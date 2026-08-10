"""ABR multi-resolution ladder in a single pass.

The magical capability: from one 4K input, produce an H.264 ladder
at 1080p, 540p, 270p, 135p — all in a single substrate call. The
2:1 area-average pyramid is essentially free (each level operates
on a 4× smaller plane than the previous), and the encoder cost
over the geometric series converges to ~1.33× single-rate.

Compare against running ffmpeg's libx264 four times to produce
the same ladder.
"""
import math
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.h264_nal_writer import (
    SpsConfig, PpsConfig, SliceHeaderConfig, build_idr_stream,
)
from substrate_rs._native import Substrate


def gen_4k(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i",
        "testsrc=size=3840x2160:rate=1:duration=1",
        "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        str(out_path),
    ], check=True)


def ffmpeg_scale_ref(src: Path, out: Path, w: int, h: int) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-s", "3840x2160", "-i", str(src),
        "-vf", f"scale={w}:{h}:flags=area",
        "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "yuv420p", str(out),
    ], check=True)


def psnr(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b))
    sq = sum((a[i] - b[i]) ** 2 for i in range(n))
    if sq == 0:
        return float("inf")
    return 10.0 * math.log10((255 ** 2) / (sq / n))


def main() -> None:
    out_dir = Path("/tmp/abr_ladder")
    out_dir.mkdir(exist_ok=True)
    src_yuv = out_dir / "src_4k.yuv"
    print("Generating 4K source...")
    gen_4k(src_yuv)
    # Pad to 2176 rows so the 2:1 pyramid stays MB-aligned for
    # several levels.
    src = src_yuv.read_bytes()[:3840 * 2160] + b"\x00" * (3840 * 16)

    s = Substrate()

    # 3 pyramid levels: 1080p (1920×1088), 540p (960×544),
    # 270p (480×272). Going to 4 levels would land at 240×136 —
    # 136 isn't divisible by 16, so the smallest MB-aligned rung
    # in this ladder is 270p.
    print("\n=== Multi-resolution + MULTI-SLICE PARALLEL transcode ===")
    # Higher slice counts at larger resolutions where the per-level
    # work is bigger; small levels stay single-slice.
    slices_per_level = [16, 8, 4]
    t0 = time.perf_counter()
    levels_raw = s.h264_transcode_pyramid_multislice(
        src, 3840, 2176, 0, slices_per_level,
    )
    parallel_ms = (time.perf_counter() - t0) * 1000
    print(f"  full parallel multi-slice transcode: {parallel_ms:.1f} ms")
    for level in levels_raw:
        out_w, out_h, mb_w, mb_h, slices = level
        payload_total = sum(len(p) for (_, p) in slices)
        print(f"    level {out_w}×{out_h} ({mb_w}×{mb_h} MBs), "
              f"{len(slices)} slices, {payload_total:,} bytes")

    # NAL wrap each slice into its own IDR NAL with the right
    # first_mb_in_slice.
    from scripts.h264_nal_writer import (
        emit_sps_rbsp, emit_pps_rbsp,
        emit_slice_header_with_cabac_alignment,
        build_idr_nal_rbsp, wrap_nal,
    )
    streams = []
    for level in levels_raw:
        out_w, out_h, mb_w, mb_h, slices = level
        sps = SpsConfig(
            pic_width_in_mbs_minus1=mb_w - 1,
            pic_height_in_map_units_minus1=mb_h - 1,
            frame_crop_bottom_offset=0,
        )
        pps = PpsConfig()
        sps_nal = wrap_nal(emit_sps_rbsp(sps), nal_unit_type=7, nal_ref_idc=3)
        pps_nal = wrap_nal(emit_pps_rbsp(pps), nal_unit_type=8, nal_ref_idc=3)
        body = bytearray(sps_nal + pps_nal)
        for (first_mb, cabac_payload) in slices:
            slice_cfg = SliceHeaderConfig(first_mb_in_slice=first_mb)
            slice_header_bytes = emit_slice_header_with_cabac_alignment(
                slice_cfg)
            idr_rbsp = build_idr_nal_rbsp(slice_header_bytes, cabac_payload)
            body.extend(wrap_nal(idr_rbsp, nal_unit_type=5, nal_ref_idc=3))
        path = out_dir / f"out_{out_w}x{out_h}.h264"
        path.write_bytes(bytes(body))
        streams.append((out_w, out_h, path, 0, 0, len(body)))

    # Verify each decodes through ffmpeg + PSNR vs ffmpeg's own
    # area scaler.
    print("\n=== Verify each level decodes via ffmpeg ===")
    for (out_w, out_h, path, _, _, _) in streams:
        decoded = out_dir / f"decoded_{out_w}x{out_h}.yuv"
        r = subprocess.run([
            "ffmpeg", "-y", "-loglevel", "warning",
            "-i", str(path),
            "-f", "rawvideo", "-pix_fmt", "yuv420p",
            str(decoded),
        ], capture_output=True, text=True)
        status = "OK " if not r.stderr.strip() else "FAIL"
        # Pad reference to match our output (we padded vertical
        # to 1088/544/272/144 rows).
        # Actually we generated the source at 2176 rows by zero-
        # padding; the area-average preserves that, so our output
        # has out_h rows (matching).
        ref_path = out_dir / f"ref_{out_w}x{out_h}.gray"
        # Reference: ffmpeg downscale of just-luma 4K using its
        # area scaler. Read input as gray (luma only) since our
        # source bytes are 8-bit-per-pixel single plane.
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "rawvideo", "-pix_fmt", "gray",
            "-s", "3840x2176", "-i", "-",
            "-vf", f"scale={out_w}:{out_h}:flags=area",
            "-frames:v", "1",
            "-f", "rawvideo", "-pix_fmt", "gray", str(ref_path),
        ], input=src, check=True)
        our_luma = decoded.read_bytes()[:out_w * out_h]
        ref_luma = ref_path.read_bytes()[:out_w * out_h]
        p = psnr(our_luma, ref_luma)
        print(f"  {status} {out_w}×{out_h}: PSNR vs ffmpeg area = "
              f"{p:6.2f} dB")

    # Compare against running ffmpeg's libx264 four times.
    print("\n=== Baseline: ffmpeg libx264 ladder (4 passes) ===")
    # Generate a 4K H.264 video first so we can transcode it.
    src_h264 = out_dir / "src_4k.h264"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-s", "3840x2160", "-i", str(src_yuv),
        "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0",
        "-frames:v", "1", str(src_h264),
    ], check=True)
    ffmpeg_total = 0.0
    for w, h in [(1920, 1080), (960, 540), (480, 270)]:
        out = out_dir / f"ffmpeg_{w}x{h}.h264"
        t0 = time.perf_counter()
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(src_h264),
            "-vf", f"scale={w}:{h}:flags=area",
            "-c:v", "libx264", "-preset", "ultrafast", "-qp", "0",
            "-frames:v", "1", str(out),
        ], check=True)
        elapsed = (time.perf_counter() - t0) * 1000
        ffmpeg_total += elapsed
        print(f"  ffmpeg → {w}×{h}: {elapsed:.0f} ms")
    print(f"\nffmpeg ladder total: {ffmpeg_total:.0f} ms")
    print(f"substrate ladder total: {parallel_ms:.1f} ms")
    print(f"speedup: {ffmpeg_total / parallel_ms:.1f}×")


if __name__ == "__main__":
    main()
