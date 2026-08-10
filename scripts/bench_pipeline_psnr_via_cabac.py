"""End-to-end pipeline PSNR through the CABAC walker.

Full pipeline (no ffmpeg in the loop yet — that's Phase 1e):

  4K YUV pixels (from ffmpeg-decoded test pattern)
    -> forward 4x4 H.264 DCT
    -> 2:1 fold (DCT-domain)
    -> CABAC encode via I_NxN walker (whole 1088p slice)
    -> CABAC decode via I_NxN walker (round-trip)
    -> inverse 4x4 H.264 DCT
    -> 1088p YUV pixels (crop to 1072 rows for clean 16-mul)

We then compare to ffmpeg's pixel-domain downscale (various
scalers) at the same dimensions.

Since CABAC encode/decode is LOSSLESS by spec, the resulting
PSNR should match Phase 1b's fold-only PSNR (49-81 dB band).
This test pins down that the walker preserves the fold output
through a real bitstream round-trip — first end-to-end test of
the full math + bitstream + CABAC stack.

This stops short of ffmpeg-decoding our output (which would need
SPS/PPS + slice header emission — Phase 1e). It proves the
walker side is solid before we invest in NAL packing.
"""
import math
import subprocess
import time
from pathlib import Path

from substrate_rs._native import Substrate

# Per ITU-T H.264 §6.4.3 / Figure 6-12: the 16 4×4 luma blocks
# within a macroblock are scanned in this Z-order. The map
# converts a block index (0..15) into its (row, col) position
# within the MB's 4×4 grid (each cell is one 4×4 block).
BLOCK_IDX_TO_RC = [
    (0, 0), (0, 1), (1, 0), (1, 1),
    (0, 2), (0, 3), (1, 2), (1, 3),
    (2, 0), (2, 1), (3, 0), (3, 1),
    (2, 2), (2, 3), (3, 2), (3, 3),
]


def gen_4k_yuv(out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i",
        "testsrc=size=3840x2160:rate=1:duration=1",
        "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        str(out_path),
    ], check=True)


def ffmpeg_reference(src: Path, out: Path, scaler: str,
                     w: int, h: int) -> None:
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-s", "3840x2160", "-i", str(src),
        "-vf", f"scale={w}:{h}:flags={scaler}",
        "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        str(out),
    ], check=True)


def psnr(a: list[int], b: list[int]) -> float:
    sq = 0
    for x, y in zip(a, b):
        d = x - y
        sq += d * d
    if sq == 0:
        return float("inf")
    mse = sq / len(a)
    return 10.0 * math.log10((255 * 255) / mse)


def load_luma(path: Path, w: int, h: int) -> list[int]:
    return list(path.read_bytes()[: w * h])


def fold_to_coefs(s: Substrate, plane: list[int],
                  in_w: int, in_h: int) -> list[int]:
    """4K luma plane → flat list of 4x4 DCT coefficients for the
    DOWNSCALED 1080p output, in raster order across the output."""
    blocks_x = in_w // 4    # = 960
    blocks_y = in_h // 4    # = 540
    # Forward-DCT every block.
    flat_samples: list[int] = []
    for by in range(blocks_y):
        for bx in range(blocks_x):
            base_y = by * 4
            base_x = bx * 4
            for ry in range(4):
                row_off = (base_y + ry) * in_w + base_x
                flat_samples.extend(plane[row_off: row_off + 4])
    all_in_coefs = list(s.h264_dct_forward_many(flat_samples))
    # Build fold input: 4 source blocks per output block.
    out_blocks_x = blocks_x // 2  # 480
    out_blocks_y = blocks_y // 2  # 270
    fold_input: list[int] = []
    for oby in range(out_blocks_y):
        for obx in range(out_blocks_x):
            tl_idx = (2 * oby + 0) * blocks_x + (2 * obx + 0)
            tr_idx = (2 * oby + 0) * blocks_x + (2 * obx + 1)
            bl_idx = (2 * oby + 1) * blocks_x + (2 * obx + 0)
            br_idx = (2 * oby + 1) * blocks_x + (2 * obx + 1)
            for idx in (tl_idx, tr_idx, bl_idx, br_idx):
                fold_input.extend(all_in_coefs[idx * 16: idx * 16 + 16])
    return list(s.h264_dct_fold_many(fold_input))


def coefs_to_mb_layout(folded_coefs: list[int],
                       out_blocks_x: int, out_blocks_y: int,
                       mb_width: int, mb_height: int) -> list[int]:
    """Take a flat raster array of 4x4 DCT coefficients
    (out_blocks_x wide × out_blocks_y tall, 16 coefs each) and
    repack into the H.264 per-MB layout: 256 coefs per MB × N_MBs,
    where within each MB the 16 4x4 blocks are in Z-scan order
    per Table 6-4.

    Drops any extra block rows beyond mb_height*4 (we crop the
    1080-row fold output to 67 MB rows = 1072 rows to avoid the
    16-row alignment issue cleanly inside this benchmark).
    """
    out: list[int] = []
    for mb_r in range(mb_height):
        for mb_c in range(mb_width):
            mb_coefs = [0] * 256
            for block_idx, (br, bc) in enumerate(BLOCK_IDX_TO_RC):
                block_y = mb_r * 4 + br
                block_x = mb_c * 4 + bc
                if block_y >= out_blocks_y or block_x >= out_blocks_x:
                    continue
                src = (block_y * out_blocks_x + block_x) * 16
                mb_coefs[block_idx * 16: block_idx * 16 + 16] = \
                    folded_coefs[src: src + 16]
            out.extend(mb_coefs)
    return out


def mb_layout_to_coefs(mb_luma: list[int],
                       out_blocks_x: int, out_blocks_y: int,
                       mb_width: int, mb_height: int) -> list[int]:
    """Inverse of coefs_to_mb_layout — repack MB-ordered coefs back
    into block-raster order so the IDCT can chew through them."""
    out = [0] * (out_blocks_x * out_blocks_y * 16)
    for mb_r in range(mb_height):
        for mb_c in range(mb_width):
            mb_base = (mb_r * mb_width + mb_c) * 256
            for block_idx, (br, bc) in enumerate(BLOCK_IDX_TO_RC):
                block_y = mb_r * 4 + br
                block_x = mb_c * 4 + bc
                if block_y >= out_blocks_y or block_x >= out_blocks_x:
                    continue
                dst = (block_y * out_blocks_x + block_x) * 16
                out[dst: dst + 16] = mb_luma[
                    mb_base + block_idx * 16:
                    mb_base + block_idx * 16 + 16
                ]
    return out


def coefs_to_plane(s: Substrate, coefs: list[int],
                   blocks_x: int, blocks_y: int) -> list[int]:
    """Inverse-DCT every 4×4 block, reassemble into a raster plane."""
    pixels_flat = list(s.h264_dct_inverse_many(coefs))
    out_w = blocks_x * 4
    out_h = blocks_y * 4
    plane = bytearray(out_w * out_h)
    for by in range(blocks_y):
        for bx in range(blocks_x):
            base_y = by * 4
            base_x = bx * 4
            blk_base = (by * blocks_x + bx) * 16
            for ry in range(4):
                row_off = (base_y + ry) * out_w + base_x
                for rx in range(4):
                    v = pixels_flat[blk_base + ry * 4 + rx]
                    plane[row_off + rx] = max(0, min(255, v))
    return list(plane)


def main() -> None:
    out_dir = Path("/tmp/cabac_pipeline")
    out_dir.mkdir(exist_ok=True)
    src_yuv = out_dir / "src_4k.yuv"
    print("Step 1: generate 4K test pattern via ffmpeg lavfi...")
    gen_4k_yuv(src_yuv)
    src_plane = load_luma(src_yuv, 3840, 2160)
    print(f"  loaded {len(src_plane):,}-sample 4K luma plane")

    s = Substrate()

    # Output dimensions: pad-down to 1072 rows (67 MB rows) for
    # a clean 16-row alignment. Width 1920 is already 120 MBs.
    OUT_W = 1920
    OUT_H = 1072
    MB_W = OUT_W // 16  # 120
    MB_H = OUT_H // 16  # 67
    OUT_BLOCKS_X = OUT_W // 4  # 480
    OUT_BLOCKS_Y = OUT_H // 4  # 268
    N_MBS = MB_W * MB_H

    print(f"\nStep 2: forward-DCT + 2:1 fold (4K → {OUT_W}x{OUT_H})...")
    t0 = time.perf_counter()
    folded = fold_to_coefs(s, src_plane, 3840, 2160)
    t1 = time.perf_counter()
    print(f"  done in {(t1 - t0)*1000:.1f} ms — {len(folded):,} coefs")
    # NB: the fold output has 270 block rows. We'll only use 268.

    print(f"\nStep 3: pack fold output into MB layout for "
          f"{N_MBS:,} MBs ({MB_W}×{MB_H})...")
    t0 = time.perf_counter()
    mb_luma_in = coefs_to_mb_layout(
        folded, 480, 270, MB_W, MB_H,
    )
    t1 = time.perf_counter()
    print(f"  done in {(t1 - t0)*1000:.1f} ms")

    print(f"\nStep 4: CABAC encode via I_NxN walker...")
    # CBP luma = 0xF for all MBs (all 4 8×8 blocks coded).
    cbp_luma_list = [0xF] * N_MBS
    t0 = time.perf_counter()
    buf = s.h264_encode_i_slice_luma_only(
        MB_W, MB_H, 0, 26, mb_luma_in, cbp_luma_list,
    )
    t1 = time.perf_counter()
    print(f"  encoded {len(buf):,} bytes in {(t1 - t0)*1000:.1f} ms "
          f"({len(buf)/N_MBS:.2f} B/MB)")

    print(f"\nStep 5: CABAC decode via I_NxN walker (round-trip)...")
    t0 = time.perf_counter()
    luma_back, cbp_back = s.h264_decode_i_slice_luma_only(
        MB_W, MB_H, 0, 26, list(buf),
    )
    luma_back = list(luma_back)
    t1 = time.perf_counter()
    print(f"  decoded in {(t1 - t0)*1000:.1f} ms")
    mismatches = sum(1 for a, b in zip(mb_luma_in, luma_back) if a != b)
    print(f"  bitstream round-trip: {mismatches} / {len(mb_luma_in):,} "
          f"coefs mismatch")
    assert mismatches == 0, "CABAC round-trip should be lossless"

    print(f"\nStep 6: unpack MB layout → block raster, then inverse-DCT...")
    t0 = time.perf_counter()
    coefs_block_order = mb_layout_to_coefs(
        luma_back, OUT_BLOCKS_X, OUT_BLOCKS_Y, MB_W, MB_H,
    )
    our_plane = coefs_to_plane(s, coefs_block_order,
                               OUT_BLOCKS_X, OUT_BLOCKS_Y)
    t1 = time.perf_counter()
    print(f"  done in {(t1 - t0)*1000:.1f} ms — "
          f"{OUT_W}x{OUT_H} luma plane")

    print(f"\nStep 7: PSNR vs ffmpeg's pixel-domain reference.")
    print(f"  Our output is the TOP {OUT_H} rows of a 2:1 area-average")
    print(f"  from 4K. ffmpeg's 1920×1080 area scaler is the matching")
    print(f"  reference; we crop its top {OUT_H} rows for comparison.")
    print(f"  {'scaler':10s} {'PSNR':>10s}")
    for scaler in ("area", "bilinear", "bicubic", "lanczos"):
        ref_path = out_dir / f"ref_{scaler}.yuv"
        ffmpeg_reference(src_yuv, ref_path, scaler, 1920, 1080)
        ref_full = load_luma(ref_path, 1920, 1080)
        # Crop ffmpeg's 1080-row reference to our 1072 rows.
        ref_plane = ref_full[: OUT_W * OUT_H]
        p = psnr(our_plane, ref_plane)
        print(f"  {scaler:10s} {p:>10.2f} dB")

    print()
    print("=" * 60)
    print("This is the FIRST end-to-end test through the full math +")
    print("bitstream stack: pixels → DCT → fold → CABAC encode →")
    print("CABAC decode → IDCT → pixels. Result should match Phase")
    print("1b PSNR (CABAC is lossless by spec). If so: the walker")
    print("preserves the fold output bit-for-bit. Remaining work for")
    print("Phase 1e is NAL packing so ffmpeg can decode this stream.")


if __name__ == "__main__":
    main()
