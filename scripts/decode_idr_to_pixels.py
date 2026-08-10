#!/usr/bin/env python3
"""World adapter: decode the first IDR frame of a real H.264 Annex-B
bitstream to pixels using the AGENT'S OWN CABAC MB decoder
(substrate_rs.h264_decode_i_slice_to_pixels), then compare to a
reference YUV decoded by ffmpeg (oracle ONLY — never used to decode).

This is a pure world adapter: it does NAL/SPS/PPS bit-parsing (opaque
external bitstream -> the smallest graph tokens the Rust decoder
needs), hands the slice payload to the Rust agent, and reads the YUV
planes back out. No agent decisions in Python.
"""
import os
import sys
from pathlib import Path

ROOT = Path("/home/matt/ozma/internal/research/experiments/gamma-substrate")
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

import substrate_rs as srs


# ---- Annex-B NAL splitting -------------------------------------------
def split_nals(data: bytes):
    """Yield (nal_ref_idc, nal_type, rbsp_with_eps) for each NAL.
    rbsp still contains emulation-prevention bytes."""
    nals = []
    i = 0
    n = len(data)
    starts = []
    while i < n - 3:
        if data[i] == 0 and data[i+1] == 0 and data[i+2] == 1:
            starts.append(i + 3)
            i += 3
        elif data[i] == 0 and data[i+1] == 0 and data[i+2] == 0 and data[i+3] == 1:
            starts.append(i + 4)
            i += 4
        else:
            i += 1
    for k, s in enumerate(starts):
        # The next NAL's start code is AT LEAST 3 bytes (00 00 01); it
        # may be 4 (00 00 00 01). Back up by the minimal 3, then let the
        # trailing-zero trim below absorb the optional 4th leading-zero
        # byte. Backing up a fixed 4 (the old code) dropped the final
        # NON-zero payload byte whenever the next start code was the
        # 3-byte form — which truncated the PPS by one byte and made
        # chroma_qp_index_offset (the last field, an Exp-Golomb codeword
        # that can spill into that byte) mis-parse (e.g. -2 read as +2).
        e = starts[k+1] - 3 if k + 1 < len(starts) else n
        # Trim the trailing start-code prefix bytes of the next NAL.
        while e > s and data[e-1] == 0:
            e -= 1
        payload = data[s:e]
        if not payload:
            continue
        hdr = payload[0]
        nal_ref_idc = (hdr >> 5) & 3
        nal_type = hdr & 0x1f
        nals.append((nal_ref_idc, nal_type, payload[1:]))
    return nals


def strip_eps(rbsp: bytes) -> bytes:
    """Remove emulation-prevention 0x03 bytes (00 00 03 -> 00 00)."""
    out = bytearray()
    i = 0
    n = len(rbsp)
    while i < n:
        if i + 2 < n and rbsp[i] == 0 and rbsp[i+1] == 0 and rbsp[i+2] == 3:
            out.append(0); out.append(0)
            i += 3
        else:
            out.append(rbsp[i])
            i += 1
    return bytes(out)


# ---- minimal bit reader for SPS/PPS ----------------------------------
class BR:
    def __init__(self, data):
        self.d = data
        self.p = 0
    def u(self, n):
        v = 0
        for _ in range(n):
            idx = self.p >> 3
            bit = ((self.d[idx] >> (7 - (self.p & 7))) & 1) if idx < len(self.d) else 0
            v = (v << 1) | bit
            self.p += 1
        return v
    def ue(self):
        lz = 0
        while self.u(1) == 0:
            lz += 1
            if lz > 31:
                return 0
        v = 0
        for _ in range(lz):
            v = (v << 1) | self.u(1)
        return (1 << lz) - 1 + v
    def se(self):
        k = self.ue()
        if k & 1:
            return (k + 1) // 2
        return -(k // 2)


def parse_sps(rbsp):
    b = BR(strip_eps(rbsp))
    profile = b.u(8); b.u(8); b.u(8)  # constraint flags + level
    b.ue()  # seq_parameter_set_id
    if profile in (100, 110, 122, 244, 44, 83, 86, 118, 128, 138, 139, 134, 135):
        chroma = b.ue()
        if chroma == 3:
            b.u(1)
        b.ue(); b.ue()
        b.u(1)
        if b.u(1):  # seq_scaling_matrix_present
            for i in range(8 if chroma != 3 else 12):
                if b.u(1):
                    _scaling_list(b, 16 if i < 6 else 64)
    log2_max_frame_num = b.ue() + 4
    poc_type = b.ue()
    log2_max_poc_lsb = 0
    if poc_type == 0:
        log2_max_poc_lsb = b.ue() + 4
    elif poc_type == 1:
        b.u(1); b.se(); b.se()
        for _ in range(b.ue()):
            b.se()
    b.ue()  # max_num_ref_frames
    b.u(1)  # gaps_in_frame_num_value_allowed
    w_mbs = b.ue() + 1
    h_map = b.ue() + 1
    frame_mbs_only = b.u(1)
    if not frame_mbs_only:
        b.u(1)  # mb_adaptive_frame_field_flag
    b.u(1)  # direct_8x8_inference_flag
    # frame_cropping — for resolutions not a multiple of 16 (e.g. the
    # 854x480 BINGO frame, coded 864x480), this gives the display crop.
    crop_l = crop_r = crop_t = crop_b = 0
    if b.u(1):  # frame_cropping_flag
        crop_l = b.ue(); crop_r = b.ue(); crop_t = b.ue(); crop_b = b.ue()
    mb_w = w_mbs
    mb_h = h_map * (2 - frame_mbs_only)
    # 4:2:0 crop units: horizontal 2 luma samples, vertical 2*(2-fmo).
    crop_unit_x = 2
    crop_unit_y = 2 * (2 - frame_mbs_only)
    disp_w = mb_w * 16 - crop_unit_x * (crop_l + crop_r)
    disp_h = mb_h * 16 - crop_unit_y * (crop_t + crop_b)
    return {
        "log2_max_frame_num": log2_max_frame_num,
        "pic_order_cnt_type": poc_type,
        "log2_max_poc_lsb": log2_max_poc_lsb,
        "frame_mbs_only_flag": frame_mbs_only,
        "mb_width": mb_w,
        "mb_height": mb_h,
        "disp_width": disp_w,
        "disp_height": disp_h,
    }


def _scaling_list(b, size):
    last = 8; nxt = 8
    for _ in range(size):
        if nxt != 0:
            nxt = (last + b.se() + 256) % 256
        last = nxt if nxt != 0 else last


def parse_pps(rbsp):
    b = BR(strip_eps(rbsp))
    b.ue()  # pps_id
    b.ue()  # sps_id
    entropy = b.u(1)
    bottom = b.u(1)
    num_slice_groups_minus1 = b.ue()
    if num_slice_groups_minus1 > 0:
        # slice group map — not needed for single-slice-group streams.
        raise RuntimeError("multi slice group not supported")
    nref0 = b.ue()
    nref1 = b.ue()
    weighted_pred = b.u(1)
    weighted_bipred = b.u(2)
    pic_init_qp = b.se() + 26
    b.se()  # pic_init_qs
    chroma_qp_index_offset = b.se()
    deblock = b.u(1)
    return {
        "entropy_coding_mode_flag": entropy,
        "bottom_field_pic_order_in_frame_present_flag": bottom,
        "num_ref_idx_l0_default_active_minus1": nref0,
        "num_ref_idx_l1_default_active_minus1": nref1,
        "weighted_pred_flag": weighted_pred,
        "weighted_bipred_idc": weighted_bipred,
        "pic_init_qp": pic_init_qp,
        "chroma_qp_index_offset": chroma_qp_index_offset,
        "deblocking_filter_control_present_flag": deblock,
        "redundant_pic_cnt_present_flag": 0,
        "num_slice_groups_minus1": num_slice_groups_minus1,
    }


def main(h264_path, ref_yuv_path):
    data = Path(h264_path).read_bytes()
    nals = split_nals(data)

    sps = pps = None
    idr_nal = None
    for nal_ref_idc, nal_type, rbsp in nals:
        if nal_type == 7 and sps is None:
            sps = parse_sps(rbsp)
        elif nal_type == 8 and pps is None:
            pps = parse_pps(rbsp)
        elif nal_type == 5 and idr_nal is None:  # IDR slice
            idr_nal = (nal_ref_idc, rbsp)

    assert sps and pps and idr_nal, f"missing sps/pps/idr: {sps is not None},{pps is not None},{idr_nal is not None}"

    sps_pps = {**sps, **pps}
    mb_w = sps["mb_width"]
    mb_h = sps["mb_height"]
    print(f"SPS/PPS: mb_grid={mb_w}x{mb_h} ({mb_w*16}x{mb_h*16}px), "
          f"cabac={pps['entropy_coding_mode_flag']}, "
          f"pic_init_qp={pps['pic_init_qp']}")

    nal_ref_idc, idr_rbsp = idr_nal
    slice_rbsp = strip_eps(idr_rbsp)

    import substrate_rs._native as native
    g = native.Substrate()
    hdr = g.walk_h264_slice_header(slice_rbsp, sps_pps, nal_ref_idc, True)
    slice_qp = int(hdr["slice_qp"])
    cabac_start_bp = int(hdr["cabac_start_bp"])
    print(f"slice header: slice_type={hdr.get('slice_type')}, "
          f"slice_qp={slice_qp}, cabac_start_bit={cabac_start_bp}")

    # Deblocking parameters from the slice header (default: filter ON,
    # zero offsets). disable_idc == 1 means the slice turns it off.
    deblock = os.environ.get("DECODE_NO_DEBLOCK") is None
    disable_idc = int(hdr.get("disable_deblocking_filter_idc", 0))
    alpha_off = 2 * int(hdr.get("slice_alpha_c0_offset_div2", 0))
    beta_off = 2 * int(hdr.get("slice_beta_offset_div2", 0))

    # ---- THE AGENT'S OWN DECODE ----
    y, u, v, decoded, i16, inxn, ipcm = g.h264_decode_i_slice_to_pixels(
        slice_rbsp, cabac_start_bp, slice_qp, 0, mb_w, mb_h,
        pps.get("chroma_qp_index_offset", 0),
        deblock, disable_idc, alpha_off, beta_off,
    )
    print(f"decoded {decoded} MBs: I_16x16={i16}, I_NxN={inxn}, I_PCM={ipcm}")

    # ---- reference (ffmpeg oracle, comparison only) ----
    # The decoder emits the CODED frame (mb_w*16 x mb_h*16). ffmpeg's
    # reference YUV is the DISPLAY frame (post-crop). When the display
    # size is not a multiple of 16 (e.g. BINGO 854x480, coded 864x480),
    # the strides differ, so compare row-by-row over the cropped region
    # rather than as a flat buffer.
    ref = Path(ref_yuv_path).read_bytes()
    cW = mb_w * 16
    cH = mb_h * 16
    dW = sps.get("disp_width", cW)
    dH = sps.get("disp_height", cH)
    ny = dW * dH
    nc = (dW // 2) * (dH // 2)
    ref_y = ref[:ny]
    ref_u = ref[ny:ny+nc]
    ref_v = ref[ny+nc:ny+2*nc]

    import math

    def compare(name, dec, dec_w, ref, ref_w, h):
        sse = 0
        maxe = 0
        exact = 0
        n = 0
        for r in range(h):
            base_d = r * dec_w
            base_r = r * ref_w
            for c in range(ref_w):
                e = abs(dec[base_d + c] - ref[base_r + c])
                sse += e * e
                if e > maxe:
                    maxe = e
                if e == 0:
                    exact += 1
                n += 1
        mse = sse / n if n else 0
        psnr = 10 * math.log10((255*255) / mse) if mse > 0 else float("inf")
        print(f"  {name}: PSNR={psnr:.2f} dB  max_err={maxe}  "
              f"exact={exact}/{n} ({100*exact/n:.1f}%)")
        return psnr, maxe

    if (dW, dH) != (cW, cH):
        print(f"display crop: coded {cW}x{cH} -> display {dW}x{dH}")
    print("vs ffmpeg reference:")
    py, my = compare("Y", y, cW, ref_y, dW, dH)
    pu, mu = compare("U", u, cW // 2, ref_u, dW // 2, dH // 2)
    pv, mv = compare("V", v, cW // 2, ref_v, dW // 2, dH // 2)
    return py, my


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
