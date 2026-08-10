"""P-frame multi-frame transcode demo.

Encode a sequence of frames as 1 IDR + N P-frames. Each P-frame
uses MV=(0,0) and codes the per-MB residual against the previous
reconstructed frame. Static MBs end up as P_Skip (1 bin); MBs
with changes get full residual encoding.

This is the simplest possible P-frame encoder (no motion
estimation), but it demonstrates the compression payoff of
temporal prediction: for mostly-static content, the encoded size
collapses to a fraction of all-I-frame.
"""
import math
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.h264_nal_writer import (
    SpsConfig, PpsConfig, SliceHeaderConfig,
    emit_sps_rbsp, emit_pps_rbsp,
    emit_slice_header_with_cabac_alignment,
    build_idr_nal_rbsp, wrap_nal,
)
from substrate_rs._native import Substrate


def gen_4k_sequence(out_path: Path, n_frames: int = 8) -> None:
    """Generate N frames of testsrc — the second-hand 'arc' moves
    over time so there's real per-frame motion to test against."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i",
        f"testsrc=size=3840x2160:rate=30:duration={n_frames / 30 + 0.1}",
        "-frames:v", str(n_frames),
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        str(out_path),
    ], check=True)


def psnr(a: bytes, b: bytes) -> float:
    n = min(len(a), len(b))
    sq = sum((a[i] - b[i]) ** 2 for i in range(n))
    if sq == 0:
        return float("inf")
    return 10.0 * math.log10((255 ** 2) / (sq / n))


def emit_p_slice_header(first_mb: int = 0,
                        frame_num: int = 1) -> bytes:
    """Build a P-slice slice header. Differs from IDR's:
       - slice_type = 5 (P, all slices in picture are P)
       - frame_num = frame index (not 0)
       - num_ref_idx_active_override_flag = 0 (use PPS default)
       - no dec_ref_pic_marking IDR fields (this isn't IDR)
       - no_output_of_prior_pics_flag NOT present (only IDR)
       - adaptive_ref_pic_marking_mode_flag = 0 (sliding window)
    """
    from scripts.h264_nal_writer import BitWriter
    bw = BitWriter()
    bw.write_ue(first_mb)        # first_mb_in_slice
    bw.write_ue(5)                # slice_type = P (5)
    bw.write_ue(0)                # pic_parameter_set_id
    bw.write_u(frame_num, 4)     # frame_num (log2_max_frame_num=4)
    # pic_order_cnt_type = 2 → no POC fields
    # Non-IDR → no idr_pic_id
    # P-slice with num_ref_idx_active_override_flag = 0
    bw.write_u(0, 1)              # num_ref_idx_active_override_flag = 0
    # ref_pic_list_modification per §7.3.3.1 — REQUIRED for P/B
    # slices regardless of override flag value.
    bw.write_u(0, 1)              # ref_pic_list_modification_flag_l0 = 0
    # weighted_pred_flag = 0 in PPS → no pred_weight_table
    # dec_ref_pic_marking for non-IDR:
    #   adaptive_ref_pic_marking_mode_flag = 0 (sliding window)
    bw.write_u(0, 1)              # adaptive_ref_pic_marking_mode_flag = 0
    # cabac_init_idc: present for P/B slices with CABAC entropy
    bw.write_ue(0)                # cabac_init_idc = 0
    bw.write_se(0)                # slice_qp_delta
    # cabac_alignment_one_bit
    while bw.bit_pos != 0:
        bw.write_bits(1, 1)
    return bw.bytes_out()


def main() -> None:
    out_dir = Path("/tmp/pframe_demo")
    out_dir.mkdir(exist_ok=True)
    N_FRAMES = 8

    src_yuv = out_dir / "src_seq.yuv"
    print(f"Generating {N_FRAMES}-frame 4K sequence...")
    gen_4k_sequence(src_yuv, N_FRAMES)
    src = src_yuv.read_bytes()
    luma_per_frame = 3840 * 2160
    yuv_per_frame = int(luma_per_frame * 1.5)
    frames_luma = [src[i * yuv_per_frame: i * yuv_per_frame + luma_per_frame]
                   for i in range(N_FRAMES)]
    # Pad each frame to 3840×2176 for MB alignment after 2:1.
    frames_padded = [f + b"\x00" * (3840 * 16) for f in frames_luma]

    s = Substrate()
    # Output dims for downscale: 1920×1088 (60+8 MB rows; crop to 1080)
    OUT_W, OUT_H = 1920, 1088
    MB_W, MB_H = 120, 68
    QP = 0

    # Frame 0: IDR via existing single-resolution path.
    print("\n=== Frame 0: IDR ===")
    t0 = time.perf_counter()
    mb_luma_idr = s.h264_transcode_2to1_luma(
        frames_padded[0], 3840, 2176, MB_W, MB_H, QP,
    )
    idr_transcode_ms = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    idr_cabac = s.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, QP, mb_luma_idr, [0xF] * (MB_W * MB_H),
    )
    idr_cabac_ms = (time.perf_counter() - t0) * 1000
    print(f"  transcode: {idr_transcode_ms:.1f} ms")
    print(f"  CABAC:     {idr_cabac_ms:.1f} ms")
    print(f"  payload:   {len(idr_cabac):,} bytes")

    # We need the reconstructed plane of the IDR for the next P-frame's
    # reference. Re-derive it via area-average (lossless at QP=0 for
    # this simple path — the intra-pred reconstruction matches the
    # target plane to within rounding).
    idr_recon = s.h264_area_average_2to1(frames_padded[0], 3840, 2176)

    # Frames 1..N-1: P-frames vs previous reconstructed.
    total_p_transcode_ms = 0.0
    total_p_cabac_ms = 0.0
    total_p_bytes = 0
    p_payloads = []
    skip_counts = []
    ref_plane = idr_recon
    print(f"\n=== Frames 1..{N_FRAMES - 1}: P-frames ===")
    for i in range(1, N_FRAMES):
        # Area-average current frame to target plane.
        target_plane = s.h264_area_average_2to1(frames_padded[i], 3840, 2176)
        t0 = time.perf_counter()
        mb_luma, cbp, skip, recon = s.h264_transcode_p_frame_2to1(
            target_plane, ref_plane, OUT_W, OUT_H, MB_W, MB_H, QP,
        )
        p_trans_ms = (time.perf_counter() - t0) * 1000
        total_p_transcode_ms += p_trans_ms
        n_skipped = sum(1 for b in skip if b)
        skip_counts.append(n_skipped)

        t0 = time.perf_counter()
        cabac_payload = s.h264_encode_p_slice_luma_bytes(
            MB_W, MB_H, 0, QP, mb_luma, cbp, skip,
        )
        p_cabac_ms = (time.perf_counter() - t0) * 1000
        total_p_cabac_ms += p_cabac_ms
        total_p_bytes += len(cabac_payload)
        p_payloads.append((i, cabac_payload))
        print(f"  P{i}: transcode {p_trans_ms:5.1f} ms, "
              f"CABAC {p_cabac_ms:5.1f} ms, payload {len(cabac_payload):>6,} B, "
              f"skipped {n_skipped:>5,}/{MB_W * MB_H:,} MBs")
        ref_plane = bytes(recon)

    print(f"\n=== Totals ===")
    print(f"  IDR transcode + CABAC:    "
          f"{idr_transcode_ms + idr_cabac_ms:.1f} ms")
    print(f"  P-frames transcode:        {total_p_transcode_ms:.1f} ms")
    print(f"  P-frames CABAC:            {total_p_cabac_ms:.1f} ms")
    print(f"  P-frames payload total:    {total_p_bytes:,} bytes")
    print(f"  IDR alone:                 {len(idr_cabac):,} bytes")
    if total_p_bytes > 0:
        ratio = total_p_bytes / ((N_FRAMES - 1) * len(idr_cabac))
        print(f"  P/I size ratio:            "
              f"{ratio * 100:.1f}% (vs all-IDR)")
    avg_skip = sum(skip_counts) / len(skip_counts) if skip_counts else 0
    print(f"  Avg skipped MBs per P:     "
          f"{avg_skip:.0f} / {MB_W * MB_H} "
          f"({avg_skip / (MB_W * MB_H) * 100:.1f}%)")

    # Build a complete H.264 stream and try to verify
    sps = SpsConfig(
        pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1,
        frame_crop_bottom_offset=4,
        num_ref_frames=1,
    )
    pps = PpsConfig()
    body = bytearray()
    body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
    body.extend(wrap_nal(emit_pps_rbsp(pps), 8, 3))
    # IDR slice
    idr_hdr = emit_slice_header_with_cabac_alignment(SliceHeaderConfig())
    idr_rbsp = build_idr_nal_rbsp(idr_hdr, idr_cabac)
    body.extend(wrap_nal(idr_rbsp, 5, 3))
    # P slices
    for (frame_num, payload) in p_payloads:
        p_hdr = emit_p_slice_header(first_mb=0, frame_num=frame_num)
        p_rbsp = p_hdr + payload
        body.extend(wrap_nal(p_rbsp, 1, 2))  # non-IDR slice
    stream_path = out_dir / "seq.h264"
    stream_path.write_bytes(bytes(body))
    print(f"\nFinal H.264 file: {stream_path} ({len(body):,} bytes)")
    r = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "warning",
        "-i", str(stream_path),
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        str(out_dir / "decoded.yuv"),
    ], capture_output=True, text=True)
    if r.stderr.strip():
        print(f"\n!! ffmpeg decode errors:")
        print(r.stderr[:1000])
    else:
        decoded = (out_dir / "decoded.yuv").read_bytes()
        dec_w, dec_h = 1920, 1080
        yuv_size = int(dec_w * dec_h * 1.5)
        n_decoded = len(decoded) // yuv_size
        print(f"\nffmpeg decoded {n_decoded} frame(s) cleanly")

        # Compare decoded luma vs target luma per frame.
        print("\n=== PSNR (decoded ffmpeg output vs target plane) ===")
        for i in range(n_decoded):
            dec_luma = decoded[i * yuv_size: i * yuv_size + dec_w * dec_h]
            # Target luma is the 2:1 area-averaged plane from frames_padded[i].
            tgt_full = s.h264_area_average_2to1(frames_padded[i], 3840, 2176)
            # tgt_full is 1920x1088; crop bottom 8 rows to 1920x1080
            tgt_luma = bytes(tgt_full[:dec_w * dec_h])
            p = psnr(dec_luma, tgt_luma)
            tag = "IDR" if i == 0 else f"P{i}"
            print(f"  {tag}: {p:.2f} dB"
                  + ("  (lossless)" if p == float('inf') else ""))


if __name__ == "__main__":
    main()
