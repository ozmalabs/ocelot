"""P-frame benchmark using GPU motion estimation.

Same shape as bench_pframe_sequence.py (4K testsrc → 1920×1088 P
chain) but replaces the MV=(0,0) static path with: GPU full-search
or hex-search ME → motion-compensated reference → existing residual
transcoder + CABAC walker with real per-MB MVs.

Reports per-frame ME time, transcode time, CABAC time, payload size,
and total PSNR vs the MV=0 baseline.
"""
import math
import struct
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
from scripts.bench_pframe_sequence import emit_p_slice_header, gen_4k_sequence, psnr
from substrate_rs._native import Substrate


def median3(a, b, c):
    return sorted([a, b, c])[1]


def compute_mvds(mvs, mb_w, mb_h, slice_row_starts=(0,), qp_input=False):
    """H.264 §8.4.1.3 median predictor → per-MB mvd in quarter-pel.

    `slice_row_starts` lists the first MB row of each slice. For
    multi-slice encoding, MBs above a slice boundary are treated as
    UNAVAILABLE for predictor purposes (since the decoder's
    neighbour state resets at slice boundaries).

    `qp_input=False` (default): `mvs` is in INTEGER luma pixels;
    we scale by 4 to get quarter-pel. `qp_input=True`: `mvs` is
    ALREADY in quarter-pel (sub-pel refinement output)."""
    slice_set = set(slice_row_starts)
    n = mb_w * mb_h
    mvd_x = bytearray(2 * n)
    mvd_y = bytearray(2 * n)
    grid = [[None] * mb_w for _ in range(mb_h)]
    scale = 1 if qp_input else 4
    for r in range(mb_h):
        for c in range(mb_w):
            i = r * mb_w + c
            mvx_qp = mvs[i][0] * scale
            mvy_qp = mvs[i][1] * scale
            # Top neighbour unavailable if this row starts a slice.
            top_avail = (r > 0) and (r not in slice_set)
            a = grid[r][c - 1] if c > 0 else None
            b = grid[r - 1][c] if top_avail else None
            cc = (grid[r - 1][c + 1] if top_avail and c < mb_w - 1
                  else (grid[r - 1][c - 1] if top_avail and c > 0 else None))
            avail = [x for x in [a, b, cc] if x is not None]
            if not avail:
                pred = (0, 0)
            elif len(avail) == 1:
                pred = avail[0]
            else:
                ax, ay = a if a else (0, 0)
                bx, by = b if b else (0, 0)
                cx, cy = cc if cc else (0, 0)
                pred = (median3(ax, bx, cx), median3(ay, by, cy))
            struct.pack_into("<h", mvd_x, i * 2, mvx_qp - pred[0])
            struct.pack_into("<h", mvd_y, i * 2, mvy_qp - pred[1])
            grid[r][c] = (mvx_qp, mvy_qp)
    return bytes(mvd_x), bytes(mvd_y)


def slice_row_starts(mb_h, n_slices):
    """Compute first-MB-row of each slice, matching the Rust
    encoder's row-aligned partition."""
    rows_per_slice = (mb_h + n_slices - 1) // n_slices
    return [r for r in range(0, mb_h, rows_per_slice)][:n_slices]


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["full", "hex"], default="hex")
    ap.add_argument("--search-radius", type=int, default=16)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--input", type=str, default=None,
                    help="Real video source (any ffmpeg-readable). If "
                         "omitted, generates testsrc as before. The "
                         "first N_FRAMES luma frames are scaled to 4K "
                         "and used as the encoder input.")
    ap.add_argument("--start", type=float, default=0.0,
                    help="Start time in seconds for --input")
    ap.add_argument("--n-slices", type=int, default=1,
                    help="Encode each P-frame as N row-aligned slices in "
                         "parallel. Slice boundaries break the CABAC chain "
                         "(each slice has independent context state) so "
                         "more slices = more parallelism, < 0.2 %% size "
                         "overhead. 8 saturates an 8-core CPU.")
    ap.add_argument("--subpel", action="store_true",
                    help="After GPU integer-pel ME, run a two-phase "
                         "half-pel→quarter-pel diamond refinement so the "
                         "MC step picks sub-pel MVs (§8.4.2.2.1 6-tap "
                         "FIR via the vendored OxideAV kernel). Smaller "
                         "P-frame residuals at the same QP.")
    ap.add_argument("--subpel-mode", choices=["diamond", "full"],
                    default="diamond",
                    help="Sub-pel refinement search mode. "
                         "`diamond` (default): 2-phase half-pel→quarter-pel "
                         "diamond, 17 SAD evals/MB. "
                         "`full`: exhaustive 5×5 QMV sweep around the "
                         "integer-pel best, 25 SAD evals/MB. ~45 %% more "
                         "compute but guaranteed minimum within ±half-pel.")
    ap.add_argument("--async-me", action="store_true",
                    help="Pipeline GPU ME with the CABAC of the previous "
                         "frame. Submit ME for frame i+1 right after "
                         "transcoding frame i; the GPU computes it while "
                         "the CPU does CABAC for frame i.")
    args = ap.parse_args()

    out_dir = Path("/tmp/pframe_gpu_me")
    out_dir.mkdir(exist_ok=True)
    N_FRAMES = args.frames

    src_yuv = out_dir / "src_seq.yuv"
    if args.input:
        print(f"Loading {N_FRAMES} frames from {args.input} (start={args.start}s)...")
        subprocess.run([
            "ffmpeg", "-y", "-loglevel", "error",
            "-ss", str(args.start), "-i", args.input,
            "-vf", "scale=3840:2160:flags=lanczos",
            "-frames:v", str(N_FRAMES),
            "-f", "rawvideo", "-pix_fmt", "yuv420p",
            str(src_yuv),
        ], check=True)
    else:
        print(f"Generating {N_FRAMES}-frame 4K testsrc sequence...")
        gen_4k_sequence(src_yuv, N_FRAMES)
    src = src_yuv.read_bytes()
    luma_per_frame = 3840 * 2160
    yuv_per_frame = int(luma_per_frame * 1.5)
    frames_luma = [src[i * yuv_per_frame: i * yuv_per_frame + luma_per_frame]
                   for i in range(N_FRAMES)]
    frames_padded = [f + b"\x00" * (3840 * 16) for f in frames_luma]

    s = Substrate()
    OUT_W, OUT_H = 1920, 1088
    MB_W, MB_H = 120, 68
    n_mbs = MB_W * MB_H
    QP = 0

    # Frame 0: IDR
    # Use the WITH_RECON variant: returns both mb_luma AND the encoder-
    # side reconstructed plane (bit-exact with what the decoder produces
    # from this IDR's coefficients). The old `h264_area_average_2to1`
    # path used the un-encoded source plane as the IDR reference, which
    # diverged from the decoder's reconstruction by ~0.21 mean-abs per
    # sample (the DCT round-trip rounding at QP=0). Sub-pel MC then
    # amplified that offset via its 6-tap FIR, compounding through the
    # P-frame chain as visible PSNR drift.
    print("\n=== Frame 0: IDR ===")
    t0 = time.perf_counter()
    mb_luma_idr, idr_recon = s.h264_transcode_2to1_luma_with_recon(
        frames_padded[0], 3840, 2176, MB_W, MB_H, QP,
    )
    idr_transcode_ms = (time.perf_counter() - t0) * 1000
    t0 = time.perf_counter()
    idr_cabac = s.h264_encode_i_slice_luma_bytes(
        MB_W, MB_H, 0, QP, mb_luma_idr, [0xF] * n_mbs,
    )
    idr_cabac_ms = (time.perf_counter() - t0) * 1000
    print(f"  transcode: {idr_transcode_ms:.1f} ms")
    print(f"  CABAC:     {idr_cabac_ms:.1f} ms")
    print(f"  payload:   {len(idr_cabac):,} bytes")

    # Warm GPU once before the timing loop so the first P-frame
    # doesn't carry the ~30 ms wgpu init cost.
    _ = s.h264_estimate_motion_gpu(
        idr_recon, idr_recon, OUT_W, OUT_H, MB_W, MB_H,
        args.search_radius, args.mode,
    )

    total_me_ms = 0.0
    total_subpel_ms = 0.0
    total_mc_ms = 0.0
    total_p_transcode_ms = 0.0
    total_p_cabac_ms = 0.0
    total_p_bytes = 0
    p_payloads = []
    nonzero_mv_counts = []
    nonzero_subpel_counts = []
    ref_plane = idr_recon

    print(f"\n=== Frames 1..{N_FRAMES - 1}: P-frames (ME mode={args.mode}, "
          f"radius={args.search_radius}"
          f"{', sub-pel(' + args.subpel_mode + ')' if args.subpel else ''}"
          f"{', async-pipelined' if args.async_me else ''}) ===")

    # Pre-compute area-averaged target planes for all frames so we
    # don't time that work inside the per-frame loop (it's mechanical
    # downsampling, not part of the codec pipeline).
    target_planes = [None] + [
        s.h264_area_average_2to1(frames_padded[i], 3840, 2176)
        for i in range(1, N_FRAMES)
    ]

    # If async-pipelined: kick off ME for frame 1 BEFORE the loop so
    # iter 1's wait() is the only blocking ME (subsequent iters get
    # their ME work submitted at the END of the prior iter, overlapping
    # with CABAC).
    pending_me = None
    if args.async_me:
        pending_me = s.h264_submit_motion_gpu(
            target_planes[1], ref_plane, OUT_W, OUT_H, MB_W, MB_H,
            args.search_radius, args.mode,
        )

    for i in range(1, N_FRAMES):
        target_plane = target_planes[i]

        # 1. GPU motion estimation
        t0 = time.perf_counter()
        if args.async_me:
            mv_buf = pending_me.wait()
        else:
            mv_buf = s.h264_estimate_motion_gpu(
                target_plane, ref_plane, OUT_W, OUT_H, MB_W, MB_H,
                args.search_radius, args.mode,
            )
        me_ms = (time.perf_counter() - t0) * 1000
        total_me_ms += me_ms
        int_mvs = [struct.unpack_from("<iii", mv_buf, j * 12) for j in range(n_mbs)]
        n_nonzero_mv = sum(
            1 for m in int_mvs if (m[0], m[1]) != (0, 0)
        )
        nonzero_mv_counts.append(n_nonzero_mv)

        # 1b. sub-pel refinement — diamond half-pel + quarter-pel
        #     diamond around each integer-pel best. Returns quarter-pel
        #     MVs in the same (qmv_x, qmv_y, sad) triple layout.
        if args.subpel:
            t0 = time.perf_counter()
            mv_buf = s.h264_refine_motion_subpel(
                target_plane, ref_plane, mv_buf,
                OUT_W, OUT_H, MB_W, MB_H,
                mode=args.subpel_mode,
            )
            subpel_ms = (time.perf_counter() - t0) * 1000
            total_subpel_ms += subpel_ms
            mvs = [struct.unpack_from("<iii", mv_buf, j * 12) for j in range(n_mbs)]
            n_nonzero_subpel = sum(
                1 for j in range(n_mbs)
                if (mvs[j][0] % 4 != 0 or mvs[j][1] % 4 != 0)
            )
            nonzero_subpel_counts.append(n_nonzero_subpel)
        else:
            mvs = int_mvs

        # 2 + 3. Motion compensation + transcode.
        # --subpel: fused path — prediction stays in i32 end-to-end
        #   and clips ONLY at the final recon (§8.5.14 spec-correct).
        #   Skips the intermediate u8 mc_ref buffer.
        # default:  two-step — build u8 mc_ref via integer-pel MC,
        #   then transcode against it. Integer-pel never overshoots
        #   [0, 255] so the clip-then-add ordering is equivalent.
        if args.subpel:
            t0 = time.perf_counter()
            mb_luma, cbp, _skip_from_xcoder, recon = \
                s.h264_transcode_p_frame_2to1_subpel(
                    target_plane, ref_plane, mv_buf,
                    OUT_W, OUT_H, MB_W, MB_H, QP,
                )
            mc_ms = 0.0  # fused — no separate MC timing
            p_trans_ms = (time.perf_counter() - t0) * 1000
            total_p_transcode_ms += p_trans_ms
        else:
            t0 = time.perf_counter()
            mc_ref = s.h264_apply_motion_compensation(
                ref_plane, mv_buf, OUT_W, OUT_H, MB_W, MB_H,
            )
            mc_ms = (time.perf_counter() - t0) * 1000
            total_mc_ms += mc_ms

            t0 = time.perf_counter()
            mb_luma, cbp, _skip_from_xcoder, recon = \
                s.h264_transcode_p_frame_2to1(
                    target_plane, mc_ref, OUT_W, OUT_H, MB_W, MB_H, QP,
                )
            p_trans_ms = (time.perf_counter() - t0) * 1000
            total_p_transcode_ms += p_trans_ms

        # --- Async pipeline pivot: submit ME for frame i+1 NOW, against
        #     the freshly-computed `recon` (which becomes its ref_plane).
        #     The GPU then runs ME(i+1) while the CPU does CABAC(i).
        if args.async_me and i + 1 < N_FRAMES:
            pending_me = s.h264_submit_motion_gpu(
                target_planes[i + 1], bytes(recon),
                OUT_W, OUT_H, MB_W, MB_H,
                args.search_radius, args.mode,
            )

        # Spec-safe skip: cbp==0 AND MV==(0,0) AND the spatial
        # predictor for this MB is also (0,0). Without the predictor
        # check, the decoder derives the MV from neighbour MVs (which
        # may be non-zero); decoded P-Skip then reads a SHIFTED ref
        # → not target → chain drift. Compute the predictor inline
        # with the same logic compute_mvds uses below.
        skip = bytearray(n_mbs)
        grid_check = [[None] * MB_W for _ in range(MB_H)]
        mv_scale = 1 if args.subpel else 4
        for r in range(MB_H):
            for c in range(MB_W):
                j = r * MB_W + c
                mv_qp = (mvs[j][0] * mv_scale, mvs[j][1] * mv_scale)
                a = grid_check[r][c - 1] if c > 0 else None
                b = grid_check[r - 1][c] if r > 0 else None
                cc = (grid_check[r - 1][c + 1] if r > 0 and c < MB_W - 1
                      else (grid_check[r - 1][c - 1] if r > 0 and c > 0 else None))
                avail = [x for x in [a, b, cc] if x is not None]
                if not avail:
                    pred = (0, 0)
                elif len(avail) == 1:
                    pred = avail[0]
                else:
                    ax, ay = a if a else (0, 0)
                    bx, by = b if b else (0, 0)
                    cx, cy = cc if cc else (0, 0)
                    pred = (median3(ax, bx, cx), median3(ay, by, cy))
                # Strict skip: residual is zero AND the predictor agrees
                # with our chosen MV (so the decoder's derived MV matches).
                if cbp[j] == 0 and mv_qp == (0, 0) and pred == (0, 0):
                    skip[j] = 1
                grid_check[r][c] = mv_qp
        n_skip = sum(skip)

        # 4. mvd computation — slice-aware predictor so multi-slice
        #    decoding reproduces the same MVs we encoded.
        starts = slice_row_starts(MB_H, args.n_slices)
        mvd_x, mvd_y = compute_mvds(
            mvs, MB_W, MB_H, starts, qp_input=args.subpel,
        )

        # 5. CABAC encode — single or parallel per --n-slices
        t0 = time.perf_counter()
        if args.n_slices > 1:
            sls = s.h264_encode_p_slice_multi_bytes(
                MB_W, MB_H, 0, QP, args.n_slices,
                mb_luma, cbp, bytes(skip),
                mvd_x_bytes=mvd_x, mvd_y_bytes=mvd_y,
            )
            # sls = [(first_mb_in_slice, payload), ...]
            p_payloads.append((i, sls))
            p_total = sum(len(p) for _, p in sls)
        else:
            payload = s.h264_encode_p_slice_luma_bytes(
                MB_W, MB_H, 0, QP, mb_luma, cbp, bytes(skip),
                mvd_x_bytes=mvd_x, mvd_y_bytes=mvd_y,
            )
            p_payloads.append((i, [(0, payload)]))
            p_total = len(payload)
        p_cabac_ms = (time.perf_counter() - t0) * 1000
        total_p_cabac_ms += p_cabac_ms
        total_p_bytes += p_total
        if args.subpel:
            print(
                f"  P{i}: ME {me_ms:5.1f}ms  sub {subpel_ms:5.1f}ms  "
                f"MC {mc_ms:5.1f}ms  "
                f"transcode {p_trans_ms:5.1f}ms  CABAC {p_cabac_ms:5.1f}ms  "
                f"payload {p_total:>7,}B  "
                f"non-0 int {n_nonzero_mv:>5,} sub {n_nonzero_subpel:>5,}/{n_mbs:,} "
                f"skip {n_skip:>5,}"
            )
        else:
            print(
                f"  P{i}: ME {me_ms:5.1f}ms  MC {mc_ms:5.1f}ms  "
                f"transcode {p_trans_ms:5.1f}ms  CABAC {p_cabac_ms:5.1f}ms  "
                f"payload {p_total:>7,}B  "
                f"non-0 MVs {n_nonzero_mv:>5,}/{n_mbs:,} "
                f"skipped {n_skip:>5,}"
            )
        ref_plane = bytes(recon)

    print(f"\n=== Totals ===")
    print(f"  IDR transcode + CABAC:     {idr_transcode_ms + idr_cabac_ms:.1f} ms")
    print(f"  P-frames GPU ME:            {total_me_ms:.1f} ms")
    if args.subpel:
        print(f"  P-frames sub-pel refine:    {total_subpel_ms:.1f} ms")
    print(f"  P-frames MC:                {total_mc_ms:.1f} ms")
    print(f"  P-frames transcode:         {total_p_transcode_ms:.1f} ms")
    print(f"  P-frames CABAC:             {total_p_cabac_ms:.1f} ms")
    print(f"  P-frames payload total:     {total_p_bytes:,} bytes")
    print(f"  IDR alone:                  {len(idr_cabac):,} bytes")
    if total_p_bytes > 0:
        ratio = total_p_bytes / ((N_FRAMES - 1) * len(idr_cabac))
        print(f"  P/I size ratio:             {ratio*100:.1f}% (vs all-IDR)")
    avg_nz = sum(nonzero_mv_counts) / len(nonzero_mv_counts) if nonzero_mv_counts else 0
    print(f"  Avg non-zero int MVs per P: "
          f"{avg_nz:.0f} / {n_mbs} ({avg_nz/n_mbs*100:.1f}%)")
    if args.subpel and nonzero_subpel_counts:
        avg_sp = sum(nonzero_subpel_counts) / len(nonzero_subpel_counts)
        print(f"  Avg sub-pel MVs per P:      "
              f"{avg_sp:.0f} / {n_mbs} ({avg_sp/n_mbs*100:.1f}%)")

    # Build H.264 stream
    sps = SpsConfig(
        pic_width_in_mbs_minus1=MB_W - 1,
        pic_height_in_map_units_minus1=MB_H - 1,
        frame_crop_bottom_offset=4,
        num_ref_frames=1,
    )
    body = bytearray()
    body.extend(wrap_nal(emit_sps_rbsp(sps), 7, 3))
    body.extend(wrap_nal(emit_pps_rbsp(PpsConfig()), 8, 3))
    idr_hdr = emit_slice_header_with_cabac_alignment(SliceHeaderConfig())
    body.extend(wrap_nal(build_idr_nal_rbsp(idr_hdr, idr_cabac), 5, 3))
    for (frame_num, slice_list) in p_payloads:
        # slice_list = [(first_mb_in_slice, payload), ...] — one
        # NAL per slice within the frame.
        for first_mb, payload in slice_list:
            body.extend(wrap_nal(
                emit_p_slice_header(first_mb=first_mb, frame_num=frame_num)
                + payload,
                1, 2,
            ))
    stream_path = out_dir / "seq.h264"
    stream_path.write_bytes(bytes(body))
    print(f"\nFinal H.264 file: {stream_path} ({len(body):,} bytes)")
    r = subprocess.run([
        "ffmpeg", "-y", "-loglevel", "warning",
        "-i", str(stream_path),
        "-f", "rawvideo", "-pix_fmt", "yuv420p",
        str(out_dir / "decoded.yuv"),
    ], capture_output=True, text=True)
    # ffmpeg prints harmless warnings on -loglevel warning (e.g. probesize
    # for short streams). Treat as failure only when no decoded output
    # was actually produced or fatal error keywords appear.
    decoded_path = out_dir / "decoded.yuv"
    fatal = any(
        k in r.stderr for k in ("Invalid", "error", "Error", "corrupt", "fail")
    )
    if fatal or not decoded_path.exists() or decoded_path.stat().st_size == 0:
        print(f"\n!! ffmpeg decode errors:\n{r.stderr[:1000]}")
        return
    if r.stderr.strip():
        print(f"\n(ffmpeg notices, not fatal):\n  {r.stderr.strip()[:300]}\n")
    decoded = decoded_path.read_bytes()
    dec_w, dec_h = 1920, 1080
    yuv_size = int(dec_w * dec_h * 1.5)
    n_decoded = len(decoded) // yuv_size
    print(f"ffmpeg decoded {n_decoded} frame(s) cleanly")

    print("\n=== PSNR (decoded ffmpeg output vs target plane) ===")
    for i in range(n_decoded):
        dec_luma = decoded[i * yuv_size: i * yuv_size + dec_w * dec_h]
        tgt_full = s.h264_area_average_2to1(frames_padded[i], 3840, 2176)
        tgt_luma = bytes(tgt_full[:dec_w * dec_h])
        p = psnr(dec_luma, tgt_luma)
        tag = "IDR" if i == 0 else f"P{i}"
        print(f"  {tag}: {p:.2f} dB" + ("  (lossless)" if p == float('inf') else ""))


if __name__ == "__main__":
    main()
