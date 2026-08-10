"""Fold quality gate — PSNR of our DCT-domain 2:1 downscale vs
ffmpeg's pixel-domain reference.

Purpose: BEFORE investing in bitstream-level plumbing (slice walker,
MB writer, container muxing), prove that the fold math itself
produces visually reasonable output. If our pixel-domain output
through forward-DCT → fold → IDCT achieves a useful PSNR vs
ffmpeg's bicubic/bilinear/lanczos downscale, the rest of the
pipeline is plumbing. If not, the fold needs more work first.

Pipeline (no bitstream involved):
  1. Generate a 4K test image (lavfi testsrc, well-behaved)
  2. Decode to raw YUV via ffmpeg → 4K luma plane
  3. Forward-DCT each 4×4 luma block via our h264_dct.forward_4x4
  4. Apply fold (4 input blocks → 1 output block) via fold_many
  5. Inverse-DCT each output 4×4 → 1080p luma reconstruction
  6. ffmpeg-downscale the same 4K to 1080p as the REFERENCE
     (bilinear, bicubic, lanczos)
  7. Compute PSNR(our_1080p, ffmpeg_reference) for each scaler

Numbers we care about:
  - PSNR ≥ 30 dB → our fold is competitive with bilinear quality
  - PSNR ≥ 35 dB → competitive with bicubic
  - PSNR ≥ 40 dB → competitive with lanczos
  - PSNR < 25 dB → something is wrong with the fold; debug first
"""
import math
import subprocess
import sys
from pathlib import Path

from substrate_rs._native import Substrate


def gen_4k_yuv_from_lavfi(out_path: Path, source: str = "testsrc") -> None:
    """Decode a 4K test pattern to raw YUV420p."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i",
        f"{source}=size=3840x2160:rate=1:duration=1",
        "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        str(out_path),
    ], check=True)


def ffmpeg_downscale_reference(
    src_yuv: Path, out_path: Path, scaler: str
) -> None:
    """ffmpeg downscale 4K YUV → 1080p YUV via the named scaler."""
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        "-s", "3840x2160", "-i", str(src_yuv),
        "-vf", f"scale=1920:1080:flags={scaler}",
        "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        str(out_path),
    ], check=True)


def load_luma_plane(path: Path, w: int, h: int) -> list[int]:
    """Read raw YUV420p, return the luma plane only (w·h bytes)."""
    data = path.read_bytes()
    return list(data[: w * h])


def fold_luma_plane_via_dct(
    s: Substrate, plane: list[int], w: int, h: int,
) -> list[int]:
    """Take a w×h luma plane, do 4×4 forward-DCT per block, fold 2:1
    via our DCT-domain matrix, IDCT back to pixels. Returns the
    (w/2)·(h/2) downscaled luma plane.

    The plane is tiled left-to-right, top-to-bottom into 4×4 blocks.
    Block at (block_row, block_col) covers pixels
    [r=4*block_row..+4, c=4*block_col..+4].
    """
    blocks_x = w // 4    # = 960 for 4K
    blocks_y = h // 4    # = 540 for 4K
    out_blocks_x = blocks_x // 2  # 480
    out_blocks_y = blocks_y // 2  # 270

    # Phase A: forward-DCT every 4×4 block of the input plane.
    # Flatten input blocks into a single big array of `blocks_x *
    # blocks_y * 16` samples in block-major order (block 0 = top-
    # left 4×4, block 1 = next 4×4 to the right, ...).
    flat_samples: list[int] = []
    for by in range(blocks_y):
        for bx in range(blocks_x):
            base_y = by * 4
            base_x = bx * 4
            for ry in range(4):
                row_off = (base_y + ry) * w + base_x
                flat_samples.extend(plane[row_off: row_off + 4])
    # Forward-DCT the lot in one FFI call.
    all_coefs = list(s.h264_dct_forward_many(flat_samples))

    # Phase B: for each output block (2:1 down), gather its 4 source
    # blocks (TL/TR/BL/BR) into the fold's expected layout and
    # call fold_many.
    fold_input: list[int] = []
    for oby in range(out_blocks_y):
        for obx in range(out_blocks_x):
            # 4 source blocks: (2*oby, 2*obx), (2*oby, 2*obx+1),
            # (2*oby+1, 2*obx), (2*oby+1, 2*obx+1)
            tl_idx = (2 * oby + 0) * blocks_x + (2 * obx + 0)
            tr_idx = (2 * oby + 0) * blocks_x + (2 * obx + 1)
            bl_idx = (2 * oby + 1) * blocks_x + (2 * obx + 0)
            br_idx = (2 * oby + 1) * blocks_x + (2 * obx + 1)
            for idx in (tl_idx, tr_idx, bl_idx, br_idx):
                fold_input.extend(all_coefs[idx * 16: idx * 16 + 16])
    folded_coefs = list(s.h264_dct_fold_many(fold_input))

    # Phase C: inverse-DCT every output block back to pixels.
    folded_pixels = list(s.h264_dct_inverse_many(folded_coefs))

    # Reassemble into a (w/2)×(h/2) raster plane.
    out_w = w // 2
    out_h = h // 2
    out = bytearray(out_w * out_h)
    for oby in range(out_blocks_y):
        for obx in range(out_blocks_x):
            blk_idx = oby * out_blocks_x + obx
            base_y = oby * 4
            base_x = obx * 4
            for ry in range(4):
                row_off = (base_y + ry) * out_w + base_x
                for rx in range(4):
                    v = folded_pixels[blk_idx * 16 + ry * 4 + rx]
                    out[row_off + rx] = max(0, min(255, v))
    return list(out)


def psnr(a: list[int], b: list[int]) -> float:
    assert len(a) == len(b)
    if not a:
        return float("inf")
    sq = 0
    for x, y in zip(a, b):
        d = x - y
        sq += d * d
    mse = sq / len(a)
    if mse == 0:
        return float("inf")
    return 10.0 * math.log10((255 * 255) / mse)


def main() -> None:
    out_dir = Path("/tmp/fold_psnr")
    out_dir.mkdir(exist_ok=True)
    src_yuv = out_dir / "src_4k.yuv"
    print("Generating 4K test pattern via lavfi...")
    gen_4k_yuv_from_lavfi(src_yuv)

    src_plane = load_luma_plane(src_yuv, 3840, 2160)
    print(f"  loaded {len(src_plane):,}-sample 4K luma plane")

    print("\nDownscaling via our DCT-domain fold...")
    s = Substrate()
    import time
    t0 = time.perf_counter()
    our_1080p = fold_luma_plane_via_dct(s, src_plane, 3840, 2160)
    t1 = time.perf_counter()
    print(f"  done — {(t1 - t0)*1000:.1f} ms")
    assert len(our_1080p) == 1920 * 1080

    print("\nReference downscales via ffmpeg + PSNR comparison:")
    print(f"  {'scaler':10s}  {'our PSNR':>10s}")
    for scaler in ("neighbor", "bilinear", "bicubic", "lanczos", "area"):
        ref_path = out_dir / f"ref_1080p_{scaler}.yuv"
        ffmpeg_downscale_reference(src_yuv, ref_path, scaler)
        ref_plane = load_luma_plane(ref_path, 1920, 1080)
        p = psnr(our_1080p, ref_plane)
        print(f"  {scaler:10s}  {p:>10.2f} dB")

    print()
    print("Interpretation:")
    print("  ≥ 30 dB  fold is competitive with simple scalers")
    print("  ≥ 35 dB  fold approaches bicubic quality")
    print("  ≥ 40 dB  fold approaches lanczos quality")
    print("  < 25 dB  something is wrong; debug the fold math")


if __name__ == "__main__":
    main()
