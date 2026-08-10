"""Minimal H.264 Annex B writer — emits SPS / PPS / IDR slice
NAL units around a caller-provided CABAC payload.

Per ITU-T H.264 §7.3 and §B.1 (Annex B byte-stream format).
Bit-field layout follows the spec tables; chosen field values
are the minimal viable set for a 1920×1088 (crop=1080) IDR I-slice
in baseline+CABAC profile (Main).

What this lets you do: take a CABAC-encoded slice payload from
the walker (`encode_i_slice_luma_only`) and wrap it into a stream
that ffmpeg / libavcodec will recognise as H.264.

What this is NOT: a full encoder. It does NOT handle:
  - Quantisation of coefficients (caller's responsibility; the
    walker takes coefs and writes them verbatim into the
    bitstream, where they'll be dequantised by the decoder)
  - Multiple slices per picture
  - P/B frames, reference frame management
  - VUI parameters, HRD, scaling lists
  - Inter-coded NALs
"""
from __future__ import annotations

from dataclasses import dataclass


class BitWriter:
    """Bit-level writer with byte buffer. MSB-first within each
    byte, matching H.264's standard convention."""

    def __init__(self) -> None:
        self.buf = bytearray()
        self.cur_byte = 0
        self.bit_pos = 0  # 0..7, where 0 = next write is the MSB

    def write_bits(self, value: int, n: int) -> None:
        """Write `n` bits of `value`, MSB-first."""
        assert n >= 1 and n <= 32
        assert value >= 0
        assert value < (1 << n), (
            f"value {value} doesn't fit in {n} bits"
        )
        for i in range(n - 1, -1, -1):
            bit = (value >> i) & 1
            self.cur_byte |= bit << (7 - self.bit_pos)
            self.bit_pos += 1
            if self.bit_pos == 8:
                self.buf.append(self.cur_byte)
                self.cur_byte = 0
                self.bit_pos = 0

    def write_u(self, value: int, n: int) -> None:
        """u(n): unsigned n-bit fixed-length."""
        self.write_bits(value, n)

    def write_ue(self, value: int) -> None:
        """ue(v): unsigned exp-Golomb. Per §9.1."""
        assert value >= 0
        # codeNum = value
        # codeword = m leading zeros + '1' + m bits, where
        # m = floor(log2(value + 1))
        v = value + 1
        m = v.bit_length() - 1
        # m leading zeros
        for _ in range(m):
            self.write_bits(0, 1)
        # the "info" part is v (= 1 followed by m more bits).
        self.write_bits(v, m + 1)

    def write_se(self, value: int) -> None:
        """se(v): signed exp-Golomb. Per §9.1.1."""
        if value <= 0:
            code_num = -2 * value
        else:
            code_num = 2 * value - 1
        self.write_ue(code_num)

    def rbsp_trailing_bits(self) -> None:
        """Per §7.3.2.11: write a 1-bit, then 0-bits to byte-align."""
        self.write_bits(1, 1)
        while self.bit_pos != 0:
            self.write_bits(0, 1)

    def byte_align(self) -> None:
        """Flush partial byte by padding with zeros up to byte boundary."""
        if self.bit_pos != 0:
            self.buf.append(self.cur_byte)
            self.cur_byte = 0
            self.bit_pos = 0

    def bytes_out(self) -> bytes:
        """Return the buffer as bytes. Requires byte-aligned writer."""
        assert self.bit_pos == 0, (
            f"BitWriter not byte-aligned (bit_pos={self.bit_pos})"
        )
        return bytes(self.buf)


# Rust fast path. Falls back to the Python implementation if the
# native module isn't loaded (e.g. running this file standalone).
try:
    from substrate_rs._native import Substrate as _SubstrateForEbsp
    _ebsp_substrate = _SubstrateForEbsp()
    _has_rust_ebsp = hasattr(_ebsp_substrate, "h264_rbsp_to_ebsp")
except ImportError:
    _has_rust_ebsp = False


def rbsp_to_ebsp(rbsp: bytes) -> bytes:
    """Insert emulation prevention bytes (§7.4.1.1) — running-state
    version. Tracks the count of consecutive zero bytes in the
    OUTPUT and inserts 0x03 whenever a byte ≤ 0x03 follows two
    zeros. The 3-byte sliding-window version misses cases like
    `00 00 00 00 01` where escaping the first triplet still leaves
    an unescaped `00 00 01` in the output.
    """
    if _has_rust_ebsp:
        return _ebsp_substrate.h264_rbsp_to_ebsp(rbsp)
    out = bytearray()
    zero_count = 0
    for b in rbsp:
        if zero_count >= 2 and b <= 0x03:
            out.append(0x03)
            zero_count = 0
        out.append(b)
        if b == 0:
            zero_count += 1
        else:
            zero_count = 0
    return bytes(out)


def wrap_nal(rbsp: bytes, nal_unit_type: int, nal_ref_idc: int) -> bytes:
    """Wrap an RBSP into a NAL unit with the 1-byte header and
    Annex B start code prefix (00 00 00 01)."""
    assert 0 <= nal_unit_type < 32
    assert 0 <= nal_ref_idc < 4
    hdr = (nal_ref_idc << 5) | nal_unit_type  # forbidden_zero=0
    ebsp = rbsp_to_ebsp(rbsp)
    return b"\x00\x00\x00\x01" + bytes([hdr]) + ebsp


# --- SPS emission per §7.3.2.1 -------------------------------------

@dataclass
class SpsConfig:
    """Minimal SPS for a 1920×1088 (crop=1080) IDR-only Main-profile
    stream with no POC tracking and no VUI.

    Field choices match what ffmpeg/libx264 emits for this profile,
    verified by trace_headers on a real x264-encoded reference.
    """
    profile_idc: int = 77  # Main — supports CABAC
    # constraint_set1_flag = 1 (Main profile compatibility); rest 0.
    constraint_set: int = 0b01000000
    level_idc: int = 40  # adequate for 1080p
    seq_parameter_set_id: int = 0
    log2_max_frame_num_minus4: int = 0  # 4-bit frame_num
    pic_order_cnt_type: int = 2  # no POC field
    num_ref_frames: int = 0  # I-only, no reference frames kept
    pic_width_in_mbs_minus1: int = 119  # 120 MBs → 1920 px
    pic_height_in_map_units_minus1: int = 67  # 68 MBs → 1088 rows
    frame_mbs_only_flag: int = 1
    direct_8x8_inference_flag: int = 1  # match x264 default
    # Crop the bottom 8 rows so output is 1080. For YUV420 with
    # frame_mbs_only_flag=1, ChromaArrayType=1, the crop is in
    # vertical chroma samples = pixel rows / 2.
    frame_crop_bottom_offset: int = 4


def emit_sps_rbsp(cfg: SpsConfig) -> bytes:
    bw = BitWriter()
    bw.write_u(cfg.profile_idc, 8)
    bw.write_u(cfg.constraint_set, 8)
    bw.write_u(cfg.level_idc, 8)
    bw.write_ue(cfg.seq_parameter_set_id)
    # profile_idc != 100/110/122/244/44/83/86/118/128/138 → skip the
    # chroma_format_idc, etc. block.
    bw.write_ue(cfg.log2_max_frame_num_minus4)
    bw.write_ue(cfg.pic_order_cnt_type)
    # pic_order_cnt_type == 2 → no further POC fields.
    bw.write_ue(cfg.num_ref_frames)
    bw.write_u(0, 1)  # gaps_in_frame_num_value_allowed_flag = 0
    bw.write_ue(cfg.pic_width_in_mbs_minus1)
    bw.write_ue(cfg.pic_height_in_map_units_minus1)
    bw.write_u(cfg.frame_mbs_only_flag, 1)
    # frame_mbs_only_flag == 1 → no mb_adaptive_frame_field_flag.
    bw.write_u(cfg.direct_8x8_inference_flag, 1)
    # frame_cropping
    if cfg.frame_crop_bottom_offset != 0:
        bw.write_u(1, 1)  # frame_cropping_flag = 1
        bw.write_ue(0)  # crop_left
        bw.write_ue(0)  # crop_right
        bw.write_ue(0)  # crop_top
        bw.write_ue(cfg.frame_crop_bottom_offset)
    else:
        bw.write_u(0, 1)
    bw.write_u(0, 1)  # vui_parameters_present_flag = 0
    bw.rbsp_trailing_bits()
    return bw.bytes_out()


# --- PPS emission per §7.3.2.2 -------------------------------------

@dataclass
class PpsConfig:
    pic_parameter_set_id: int = 0
    seq_parameter_set_id: int = 0
    entropy_coding_mode_flag: int = 1  # 1 = CABAC
    bottom_field_pic_order_in_frame_present_flag: int = 0
    num_slice_groups_minus1: int = 0
    num_ref_idx_l0_default_active_minus1: int = 0
    num_ref_idx_l1_default_active_minus1: int = 0
    weighted_pred_flag: int = 0
    weighted_bipred_idc: int = 0
    pic_init_qp_minus26: int = -26  # → slice QP = 0 (lowest quant)
    pic_init_qs_minus26: int = 0
    chroma_qp_index_offset: int = 0
    deblocking_filter_control_present_flag: int = 0
    # constrained_intra_pred_flag=0 matches x264; with =1, decoders
    # reject our DC-mode I_NxN at MB(0,0) when no INTRA neighbour
    # is available, despite spec saying DC falls back to 128.
    constrained_intra_pred_flag: int = 0
    redundant_pic_cnt_present_flag: int = 0


def emit_pps_rbsp(cfg: PpsConfig) -> bytes:
    bw = BitWriter()
    bw.write_ue(cfg.pic_parameter_set_id)
    bw.write_ue(cfg.seq_parameter_set_id)
    bw.write_u(cfg.entropy_coding_mode_flag, 1)
    bw.write_u(cfg.bottom_field_pic_order_in_frame_present_flag, 1)
    bw.write_ue(cfg.num_slice_groups_minus1)
    # num_slice_groups_minus1 == 0 → no slice-group-map fields.
    bw.write_ue(cfg.num_ref_idx_l0_default_active_minus1)
    bw.write_ue(cfg.num_ref_idx_l1_default_active_minus1)
    bw.write_u(cfg.weighted_pred_flag, 1)
    bw.write_u(cfg.weighted_bipred_idc, 2)
    bw.write_se(cfg.pic_init_qp_minus26)
    bw.write_se(cfg.pic_init_qs_minus26)
    bw.write_se(cfg.chroma_qp_index_offset)
    bw.write_u(cfg.deblocking_filter_control_present_flag, 1)
    bw.write_u(cfg.constrained_intra_pred_flag, 1)
    bw.write_u(cfg.redundant_pic_cnt_present_flag, 1)
    bw.rbsp_trailing_bits()
    return bw.bytes_out()


# --- IDR slice header per §7.3.3 -----------------------------------

@dataclass
class SliceHeaderConfig:
    """IDR I-slice header for the simplest viable case."""
    first_mb_in_slice: int = 0
    slice_type: int = 7  # 7 = I slice, all slices in picture are I
    pic_parameter_set_id: int = 0
    frame_num: int = 0
    idr_pic_id: int = 0
    no_output_of_prior_pics_flag: int = 0
    long_term_reference_flag: int = 0
    slice_qp_delta: int = 0
    # CABAC: after slice_qp_delta we need rbsp_trailing_bits, then
    # the CABAC payload starts at the next byte boundary with
    # cabac_alignment_one_bit padding (one or more '1' bits).


def emit_slice_header_with_cabac_alignment(
    cfg: SliceHeaderConfig,
) -> bytes:
    """Emit the IDR slice header bits ending at the byte boundary
    where the CABAC payload starts. The cabac_alignment_one_bit
    pattern fills the partial byte with '1' bits — per §7.3.4.

    Returns the bytes that precede the CABAC payload in the IDR
    NAL's RBSP.
    """
    bw = BitWriter()
    bw.write_ue(cfg.first_mb_in_slice)
    bw.write_ue(cfg.slice_type)
    bw.write_ue(cfg.pic_parameter_set_id)
    # frame_num is u(v) with v = log2_max_frame_num
    # = 4 (since log2_max_frame_num_minus4 = 0).
    bw.write_u(cfg.frame_num, 4)
    # pic_order_cnt_type == 2 → no POC fields.
    # IDR slice → idr_pic_id present.
    bw.write_ue(cfg.idr_pic_id)
    # dec_ref_pic_marking for IDR (nal_ref_idc != 0):
    bw.write_u(cfg.no_output_of_prior_pics_flag, 1)
    bw.write_u(cfg.long_term_reference_flag, 1)
    bw.write_se(cfg.slice_qp_delta)
    # deblocking_filter_control_present_flag = 0 in PPS → no offset fields.
    # CABAC alignment: pad the current partial byte with '1' bits.
    while bw.bit_pos != 0:
        bw.write_bits(1, 1)
    return bw.bytes_out()


def build_idr_nal_rbsp(
    slice_header_bytes: bytes,
    cabac_payload: bytes,
) -> bytes:
    """Concatenate the slice header (already byte-aligned via
    cabac_alignment_one_bit) with the CABAC payload to form the
    IDR NAL's RBSP.

    The CABAC payload from our walker already includes the
    end-of-slice / rbsp_slice_trailing_bits via the encoder's
    finish() — so we don't add anything after it.
    """
    return slice_header_bytes + cabac_payload


# --- Top-level convenience -----------------------------------------

def build_idr_stream(
    sps_cfg: SpsConfig,
    pps_cfg: PpsConfig,
    slice_cfg: SliceHeaderConfig,
    cabac_payload: bytes,
) -> bytes:
    """Build a complete Annex B byte stream: SPS NAL + PPS NAL +
    IDR slice NAL. Caller supplies the CABAC payload (e.g. from
    `Substrate.h264_encode_i_slice_luma_only`).
    """
    sps_rbsp = emit_sps_rbsp(sps_cfg)
    pps_rbsp = emit_pps_rbsp(pps_cfg)
    slice_header_bytes = emit_slice_header_with_cabac_alignment(slice_cfg)
    idr_rbsp = build_idr_nal_rbsp(slice_header_bytes, cabac_payload)

    return (
        wrap_nal(sps_rbsp, nal_unit_type=7, nal_ref_idc=3)
        + wrap_nal(pps_rbsp, nal_unit_type=8, nal_ref_idc=3)
        + wrap_nal(idr_rbsp, nal_unit_type=5, nal_ref_idc=3)
    )
