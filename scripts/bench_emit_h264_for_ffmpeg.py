"""Phase 1e — emit a valid H.264 stream and pipe it through
ffmpeg's decoder. Honest end-to-end demonstration.

What works:
  - 1920x1080 IDR I-slice with CBP=0 (no residuals) → ffmpeg
    decodes cleanly with no errors. Output is uniform gray
    (intra-DC prediction fallback at slice boundary = 128).
  - Single-MB 16x16 IDR stream with any CBP → ffmpeg decodes.
  - 3-MB row CBP=0 → ffmpeg decodes.

What doesn't:
  - 1920x1080 with CBP=0xF and luma residuals → ffmpeg fails at
    MB(1, 0). Cause: our CBF context derivation passes
    `None, None` for the in-MB neighbour CBFs of each 4x4 luma
    block. Spec wants in-MB and cross-MB CBF state tracking
    per §9.3.3.1.1.9. Round-trip through our own decoder masks
    this (both sides use the same wrong contexts); ffmpeg's
    spec-compliant CBF context diverges starting at the second
    4x4 block in MB(0, 0).

Spec bugs found and fixed in this commit:
  1. CabacCtx::init_from_mn — clamped preCtxState to [0, 127]
     instead of the spec's [1, 126]. Self-consistent but
     spec-wrong; libavcodec init diverges.
  2. cbp_luma_ctx_idx_inc — used the neighbour bit directly,
     spec wants the inverted condition (cond=1 when neighbour
     bit=0). Also: walker now passes 0xF (all-coded sentinel)
     for unavailable neighbours so the inversion gives 0 per
     spec ("unavailable → condTermFlag = 0").
  3. encode_terminate — missing `codILow += codIRange` for
     binVal=1 case per §9.3.4.4. Caused the encoder's terminate
     bin to compress to 0 bytes instead of the correct ~1 bit;
     payload was 11x larger than necessary AND the decoder
     could only recover via our own (mis-matching) decoder.
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.h264_nal_writer import (
    SpsConfig, PpsConfig, SliceHeaderConfig, build_idr_stream,
)
from substrate_rs._native import Substrate


def emit_and_decode(label: str, mb_w: int, mb_h: int,
                    luma: list[int], cbp: list[int]) -> None:
    s = Substrate()
    payload = s.h264_encode_i_slice_luma_only(
        mb_w, mb_h, 0, 0, luma, cbp,
    )
    sps = SpsConfig(
        pic_width_in_mbs_minus1=mb_w - 1,
        pic_height_in_map_units_minus1=mb_h - 1,
        frame_crop_bottom_offset=4 if mb_h == 68 else 0,
    )
    pps = PpsConfig()
    slice_cfg = SliceHeaderConfig()
    stream = build_idr_stream(sps, pps, slice_cfg, payload)
    out = Path(f"/tmp/phase1e_{label}.h264")
    out.write_bytes(stream)
    yuv = Path(f"/tmp/phase1e_{label}.yuv")
    r = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "warning",
         "-i", str(out),
         "-f", "rawvideo", "-pix_fmt", "yuv420p", str(yuv)],
        capture_output=True, text=True,
    )
    status = "OK" if not r.stderr.strip() else "FAIL"
    print(f"  {label:30s} {mb_w}x{mb_h} MBs, "
          f"payload={len(payload):5d}B, stream={len(stream):5d}B "
          f"→ {status}")
    if r.stderr.strip():
        print(f"     err: {r.stderr.strip()[:200]}")


def main() -> None:
    print("Phase 1e — H.264 NAL emission, end-to-end via ffmpeg")
    print("=" * 60)

    # Case 1: minimal stream — 1 MB, 16x16, no CBP.
    emit_and_decode("min_1mb_cbp0",
                    1, 1, [0] * 256, [0])

    # Case 2: 3-MB row, no CBP — tests neighbour propagation.
    emit_and_decode("3mb_row_cbp0",
                    3, 1, [0] * (3 * 256), [0, 0, 0])

    # Case 3: full 1920×1088 (crop to 1080), no CBP.
    n = 120 * 68
    emit_and_decode("1080_no_residuals",
                    120, 68, [0] * (n * 256), [0] * n)

    # Case 4: full 1920×1088, CBP=0xF, small DC per block.
    luma = [0] * (n * 256)
    for i in range(n):
        luma[i * 256 + 0] = 1
    emit_and_decode("1080_cbp_f_dc_1",
                    120, 68, luma, [0xF] * n)

    print()
    print("Note: case 4 fails because CBF context derivation uses")
    print("`None, None` for in-MB neighbours; ffmpeg's spec-compliant")
    print("derivation tracks 4x4-block CBF state and diverges. Fix is")
    print("the next increment (Phase 1f) — not signal-processing risk,")
    print("just spec-driven neighbour-state plumbing.")


if __name__ == "__main__":
    main()
