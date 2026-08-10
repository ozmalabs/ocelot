"""Head-to-head: our pipeline vs libx264 on the same source.

Fairness constraints:
  - Same input plane: 1920×1088 luma, derived from 4K via area-average
  - Same frame structure: 1 IDR + N P-frames, no B-frames, 1 reference
  - QP=0 throughout
  - libx264 across its preset range (ultrafast → medium)
  - Both produce ffmpeg-decodable bitstreams; PSNR via ffmpeg decode
    + per-frame comparison to the same source plane

CAVEAT: This is a from-scratch-encode benchmark; libx264 dominates
on every metric (it's 20+ years of hand-optimised SIMD with full
spec coverage — B-frames, sub-pel MV, CABAC adaptive contexts,
RD optimisation, deblocking, transform_bypass for true QP=0
lossless). Our encoder's positioning isn't "beat libx264 at
encoding" — it's "operate on the bitstream in coefficient domain
without going back to pixels", e.g. ABR ladder generation,
transrating, family format-hop. This bench establishes the
baseline cost of from-scratch encoding so the wins from
coefficient-domain operations can be measured against it.
"""
import argparse
import math
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from substrate_rs._native import Substrate
from scripts.h264_nal_writer import (
    SpsConfig, PpsConfig, SliceHeaderConfig,
    emit_sps_rbsp, emit_pps_rbsp,
    emit_slice_header_with_cabac_alignment,
    build_idr_nal_rbsp, wrap_nal,
)
from scripts.bench_pframe_sequence import emit_p_slice_header, psnr
from scripts.bench_pframe_gpu_me import (
    compute_mvds, slice_row_starts, median3,
)


def gen_input(src_path, out_yuv, start_sec, n_frames):
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-ss", str(start_sec), "-i", src_path,
        "-vf", "scale=3840:2160:flags=lanczos",
        "-frames:v", str(n_frames),
        "-f", "rawvideo", "-pix_fmt", "yuv420p", str(out_yuv),
    ], check=True)


def downsample_to_1920x1088(frames_yuv_4k, n_frames, out_yuv, out_dir):
    s = Substrate()
    out_data = bytearray()
    luma_4k = 3840 * 2160
    yuv_per_frame_4k = int(luma_4k * 1.5)
    luma_1080 = 1920 * 1080
    chroma_size = 960 * 540  # per-component 4:2:0 at 1920x1080
    for i in range(n_frames):
        # Take 4K luma, area-avg to 1920×1088, crop to 1920×1080.
        frame4k = frames_yuv_4k[i * yuv_per_frame_4k:
                                i * yuv_per_frame_4k + luma_4k]
        # Pad to 3840×2176 for the area_avg function.
        padded = frame4k + b"\x00" * (3840 * 16)
        avg1088 = bytes(s.h264_area_average_2to1(padded, 3840, 2176))
        avg1080 = avg1088[:luma_1080]
        out_data.extend(avg1080)
        # Pad with gray chroma so output is valid YUV420p (libx264 needs
        # chroma even if our pipeline encodes luma only).
        out_data.extend(b"\x80" * chroma_size)  # U = 128
        out_data.extend(b"\x80" * chroma_size)  # V = 128
    out_yuv.write_bytes(bytes(out_data))


def encode_with_ours(yuv_1080_path, n_frames, out_h264, out_dir, subpel=False):
    """Encode using our pipeline. Uses:
      - `h264_transcode_2to1_luma_with_recon` for an encoder-side-
        reconstructed IDR reference (byte-exact with the decoder).
      - `h264_refine_motion_subpel` + `h264_transcode_p_frame_2to1_subpel`
        when `subpel=True`; otherwise the integer-pel two-step path.
    Both paths now produce ffmpeg-decodable output that's byte-exact
    against our `recon` since the row-first IDCT landed.
    """
    s = Substrate()
    src = yuv_1080_path.read_bytes()
    luma_size = 1920 * 1080
    yuv_per = int(luma_size * 1.5)
    # Extract just luma per frame, pad to 1920×1088 (encoder MB-aligned).
    frames = []
    for i in range(n_frames):
        luma = src[i * yuv_per: i * yuv_per + luma_size]
        padded = luma + b"\x00" * (1920 * 8)  # pad to 1088 rows
        frames.append(padded)

    W, H = 1920, 1088
    MB_W, MB_H = W // 16, H // 16
    n_mbs = MB_W * MB_H
    QP = 0

    t_total_start = time.perf_counter()
    # IDR: encode the 1920×1088 plane directly via the no-resize
    # intra-predict+quant. Returns mb_luma + encoder-side recon
    # (= ffmpeg's IDR after decode, since the IDCT is byte-exact).
    mb_luma_idr, idr_recon = s.h264_intra_predict_and_quantise_with_recon(
        frames[0], W, H, MB_W, MB_H, QP,
    )

    idr_cabac = s.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, QP, mb_luma_idr, [0xF] * n_mbs,
    )

    # Warm GPU
    _ = s.h264_estimate_motion_gpu(
        idr_recon, idr_recon, W, H, MB_W, MB_H, 16, "full",
    )

    p_payloads = []
    ref_plane = idr_recon
    pending = s.h264_submit_motion_gpu(
        frames[1], ref_plane, W, H, MB_W, MB_H, 16, "full",
    )

    for i in range(1, n_frames):
        target = frames[i]
        mv_buf = pending.wait()
        if subpel:
            mv_buf = s.h264_refine_motion_subpel(
                target, ref_plane, mv_buf, W, H, MB_W, MB_H,
            )
            mb_luma, cbp, _skip_x, recon = s.h264_transcode_p_frame_2to1_subpel(
                target, ref_plane, mv_buf, W, H, MB_W, MB_H, QP,
            )
        else:
            mc_ref = s.h264_apply_motion_compensation(
                ref_plane, mv_buf, W, H, MB_W, MB_H,
            )
            mb_luma, cbp, _skip_x, recon = s.h264_transcode_p_frame_2to1(
                target, mc_ref, W, H, MB_W, MB_H, QP,
            )
        if i + 1 < n_frames:
            pending = s.h264_submit_motion_gpu(
                frames[i + 1], bytes(recon), W, H, MB_W, MB_H, 16, "full",
            )

        # One-shot Rust kernel: spec-safe skip-detect + MVD computation
        # over the 8160-MB grid. Replaces a 75 ms / frame Python double-
        # loop (median predictor + slice-aware availability + MV scaling).
        starts = slice_row_starts(MB_H, 8)
        skip, mvd_x, mvd_y = s.h264_compute_skip_and_mvds(
            mv_buf, cbp, MB_W, MB_H, starts, subpel,
        )
        slices = s.h264_encode_p_slice_multi_bytes(
            MB_W, MB_H, 0, QP, 8,
            mb_luma, cbp, skip,
            mvd_x_bytes=mvd_x, mvd_y_bytes=mvd_y,
        )
        p_payloads.append((i, slices))
        ref_plane = bytes(recon)

    sps = SpsConfig(
        num_ref_frames=1, pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1, frame_crop_bottom_offset=4,
    )
    body = bytearray()
    body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
    body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
    body.extend(wrap_nal(build_idr_nal_rbsp(
        emit_slice_header_with_cabac_alignment(SliceHeaderConfig()),
        idr_cabac), 5, 3))
    for (fn, sl) in p_payloads:
        for first_mb, payload in sl:
            body.extend(wrap_nal(
                emit_p_slice_header(first_mb=first_mb, frame_num=fn) + payload,
                1, 2,
            ))
    elapsed = time.perf_counter() - t_total_start
    out_h264.write_bytes(bytes(body))
    return elapsed, len(body)


def encode_with_libx264(yuv_1080_path, n_frames, out_h264, preset):
    """Encode the same input with libx264. Match feature level to ours:
    1 reference frame, no B-frames, QP=0. The preset knob trades
    encode speed vs compression — `ultrafast` is the closest to our
    "simple integer-pel inter, no rate-distortion analysis" feature
    set; `medium` is x264's default.
    """
    t0 = time.perf_counter()
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-s", "1920x1080", "-r", "30",
        "-i", str(yuv_1080_path),
        "-c:v", "libx264", "-preset", preset,
        "-qp", "0", "-bf", "0", "-refs", "1",
        "-g", str(n_frames + 1),  # only first frame is IDR
        "-keyint_min", str(n_frames + 1),
        "-f", "h264", str(out_h264),
    ], check=True)
    elapsed = time.perf_counter() - t0
    return elapsed, out_h264.stat().st_size


def decode_psnr(h264_path, ref_yuv_path, n_frames, w=1920, h=1080):
    """Decode through ffmpeg, PSNR-compare to ref YUV (luma only)."""
    with tempfile.NamedTemporaryFile(suffix=".yuv") as tf:
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-i", str(h264_path),
            "-f", "rawvideo", "-pix_fmt", "yuv420p", tf.name,
        ], check=True)
        dec = Path(tf.name).read_bytes()
    ref = ref_yuv_path.read_bytes()
    yuv_size = int(w * h * 1.5)
    psnrs = []
    for i in range(n_frames):
        d = dec[i * yuv_size: i * yuv_size + w * h]
        r = ref[i * yuv_size: i * yuv_size + w * h]
        if len(d) != w * h or len(r) != w * h:
            psnrs.append(float("nan"))
            continue
        psnrs.append(psnr(d, r))
    return psnrs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--start", type=float, default=1.0)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--presets", default="ultrafast,superfast,fast,medium")
    ap.add_argument("--subpel", action="store_true",
                    help="Also encode with sub-pel MV refinement (extra row "
                         "in the results table). Default just runs integer-pel.")
    args = ap.parse_args()

    out_dir = Path("/tmp/bench_vs_x264")
    out_dir.mkdir(exist_ok=True)
    src_yuv_4k = out_dir / "src_4k.yuv"
    print(f"1. Extract {args.frames} frames @ 4K from {args.input}…")
    gen_input(args.input, src_yuv_4k, args.start, args.frames)
    src_4k = src_yuv_4k.read_bytes()

    print("2. Downsample 4K→1080p via area-avg → both encoders' input")
    src_yuv_1080 = out_dir / "src_1080.yuv"
    downsample_to_1920x1088(src_4k, args.frames, src_yuv_1080, out_dir)

    print("\n3. Encode with OUR pipeline (integer-pel ME)")
    ours_h264 = out_dir / "ours.h264"
    ours_t, ours_sz = encode_with_ours(
        src_yuv_1080, args.frames, ours_h264, out_dir, subpel=False,
    )
    ours_psnr = decode_psnr(ours_h264, src_yuv_1080, args.frames)
    results = [("ours", ours_t, ours_sz, ours_psnr)]

    if args.subpel:
        print("\n3b. Encode with OUR pipeline (sub-pel ME)")
        ours_sub_h264 = out_dir / "ours_subpel.h264"
        ours_sub_t, ours_sub_sz = encode_with_ours(
            src_yuv_1080, args.frames, ours_sub_h264, out_dir, subpel=True,
        )
        ours_sub_psnr = decode_psnr(ours_sub_h264, src_yuv_1080, args.frames)
        results.append(("ours+subpel", ours_sub_t, ours_sub_sz, ours_sub_psnr))

    for preset in args.presets.split(","):
        preset = preset.strip()
        print(f"\n4. Encode with libx264 preset={preset}")
        x264_h264 = out_dir / f"x264_{preset}.h264"
        try:
            t, sz = encode_with_libx264(
                src_yuv_1080, args.frames, x264_h264, preset,
            )
            psnrs = decode_psnr(x264_h264, src_yuv_1080, args.frames)
            results.append((f"x264:{preset}", t, sz, psnrs))
        except subprocess.CalledProcessError as e:
            print(f"  failed: {e}")

    print(f"\n=== Results: {args.frames} frames @ 1920×1080, QP=0, 1 ref, no B ===")
    hdr = f"{'encoder':<18}  {'time':>8}  {'fps':>6}  {'size':>10}  "\
          f"{'PSNR med':>9}  {'PSNR min':>9}"
    print(hdr)
    print("-" * len(hdr))
    for name, t, sz, p in results:
        finite = [x for x in p if x != float("inf") and not math.isnan(x)]
        med = sorted(finite)[len(finite) // 2] if finite else float("inf")
        mn = min(finite) if finite else float("inf")
        fps = args.frames / t
        print(f"{name:<18}  {t*1000:>6.1f}ms  {fps:>5.1f}  "
              f"{sz:>9,}B  {med:>7.2f}dB  {mn:>7.2f}dB")


if __name__ == "__main__":
    main()
