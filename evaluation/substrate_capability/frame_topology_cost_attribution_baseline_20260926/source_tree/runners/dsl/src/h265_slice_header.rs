//! H.265 slice segment header emitter — stage 6 of the
//! H.264→H.265 transcoder design from commit 486f65e.
//!
//!   STAGE: structure
//!     rewrite:      h264_slice_header_syntax → h265_slice_header_syntax
//!     pattern:      bit_packed_syntax_emission
//!     hardware:     BMI2 pdep + AVX512_VBMI vpermb (substrate-named)
//!     topology:     amdahl_serial_bottleneck (runs in stage gaps)
//!     bottleneck:   negligible (~100 bytes/slice; sub-µs)
//!
//! Implementation choice: scalar Rust, no BMI2 intrinsics. The
//! substrate's `bit_packed_emission_runs_in_amdahl_slack` rule
//! explicitly says this stage is sub-µs noise; scalar is correct.
//! BMI2 could be added if the slice count blew up by orders of
//! magnitude (it won't).
//!
//! Reference: ITU-T H.265 v9 (2024) clause 7.3.6.1 slice_segment_header.
//! This implementation covers the fields required for a basic
//! I/P/B slice transcoded from H.264 — a real H.265 encoder would
//! support more options (tiles, dependent slices, weighted prediction
//! tables, etc.).

use std::io;

/// H.265 slice type. Encoded as ue(v) per H.265 clause 7.3.6.1:
///   slice_type == 0 → B
///   slice_type == 1 → P
///   slice_type == 2 → I
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum H265SliceType {
    B = 0,
    P = 1,
    I = 2,
}

impl H265SliceType {
    pub fn to_ue(self) -> u32 {
        self as u32
    }
    pub fn from_h264(h264_type: u8) -> Option<Self> {
        // H.264 slice types: 0=P, 1=B, 2=I, 3=SP, 4=SI, 5..9=same modulo 5.
        // Take modulo 5 to handle the "all-slice-types-are-this-type" variants.
        match h264_type % 5 {
            0 => Some(H265SliceType::P),
            1 => Some(H265SliceType::B),
            2 => Some(H265SliceType::I),
            _ => None, // SP/SI not in H.265
        }
    }
}

/// Minimal H.265 slice-segment header for a transcoded frame. Fields
/// outside the basic set use safe defaults; a production transcoder
/// would expose the rest.
#[derive(Debug, Clone)]
pub struct H265SliceHeader {
    pub first_slice_segment_in_pic_flag: bool,
    pub no_output_of_prior_pics_flag: bool,
    pub slice_pic_parameter_set_id: u32,
    /// CTU-index address of this slice segment within the picture.
    /// Ignored when `first_slice_segment_in_pic_flag` is set.
    pub slice_segment_address: u32,
    /// Bit-width of `slice_segment_address`. Caller computes it as
    /// `ceil_log2(num_ctus_in_picture)`; we don't infer it.
    pub slice_segment_address_bits: u8,
    pub slice_type: H265SliceType,
    pub pic_output_flag: bool,
    /// 4 bits when the picture's log2_max_pic_order_cnt_lsb_minus4 = 0.
    /// Caller's responsibility to size it.
    pub slice_pic_order_cnt_lsb: u32,
    pub slice_pic_order_cnt_lsb_bits: u8,
    /// Index into the SPS's short-term RPS list; `None` when the slice
    /// signals an inline RPS (omitted in this minimal emitter).
    pub short_term_ref_pic_set_sps_flag: bool,
    pub short_term_ref_pic_set_idx: u32,
    pub short_term_ref_pic_set_idx_bits: u8,
    pub sao_luma_flag: bool,
    pub sao_chroma_flag: bool,
    pub num_ref_idx_l0_active_minus1: u8,
    pub num_ref_idx_l1_active_minus1: u8,
    pub qp_delta: i32,
    pub deblocking_filter_disabled_flag: bool,
}

/// Tiny MSB-first bit writer. Holds an output Vec<u8> + a partial
/// byte. `finish` writes the trailing 1-bit + zero padding required
/// by H.265 NAL RBSP framing.
pub struct BitWriter {
    bytes: Vec<u8>,
    cur: u8,
    bits_in_cur: u8,
}

impl Default for BitWriter {
    fn default() -> Self {
        Self::new()
    }
}

impl BitWriter {
    pub fn new() -> Self {
        Self {
            bytes: Vec::new(),
            cur: 0,
            bits_in_cur: 0,
        }
    }

    /// Write `n` bits of `value` MSB-first. `n` must be ≤ 32.
    pub fn write_u(&mut self, value: u32, n: u8) {
        assert!(n <= 32);
        for i in (0..n).rev() {
            let bit = ((value >> i) & 1) as u8;
            self.cur = (self.cur << 1) | bit;
            self.bits_in_cur += 1;
            if self.bits_in_cur == 8 {
                self.bytes.push(self.cur);
                self.cur = 0;
                self.bits_in_cur = 0;
            }
        }
    }

    /// Write a single flag bit.
    pub fn write_flag(&mut self, b: bool) {
        self.write_u(b as u32, 1);
    }

    /// Unsigned Exp-Golomb code (ue(v)). Encodes `v` as:
    ///   M = floor(log2(v+1))
    ///   write M zeros, then (v+1) in M+1 bits.
    pub fn write_ue(&mut self, v: u32) {
        let x = v as u64 + 1;
        let m = 63 - x.leading_zeros() as u8; // floor(log2(x))
                                              // M zeros + 1 bit + M info bits = (M+1) bits total carrying x.
        self.write_u(0, m);
        self.write_u(x as u32, m + 1);
    }

    /// Signed Exp-Golomb code (se(v)).
    pub fn write_se(&mut self, v: i32) {
        let coded: u32 = if v <= 0 {
            (-(v as i64) as u32) * 2
        } else {
            (v as u32) * 2 - 1
        };
        self.write_ue(coded);
    }

    /// Finalise an RBSP: emit a stop bit (1) + zero-pad to byte boundary.
    pub fn finish_rbsp(mut self) -> Vec<u8> {
        self.write_flag(true);
        if self.bits_in_cur > 0 {
            self.cur <<= 8 - self.bits_in_cur;
            self.bytes.push(self.cur);
        }
        self.bytes
    }

    /// Number of bits written so far (incl. partial byte).
    pub fn bits_written(&self) -> usize {
        self.bytes.len() * 8 + self.bits_in_cur as usize
    }
}

/// Errors that can occur during slice-header emission.
#[derive(Debug)]
pub enum EmitError {
    UnsupportedSliceType,
    InvalidFieldWidth(&'static str),
}

impl std::fmt::Display for EmitError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            EmitError::UnsupportedSliceType => write!(f, "slice type not supported"),
            EmitError::InvalidFieldWidth(field) => write!(f, "invalid field width for {}", field),
        }
    }
}
impl std::error::Error for EmitError {}
impl From<io::Error> for EmitError {
    fn from(_: io::Error) -> Self {
        EmitError::UnsupportedSliceType
    }
}

/// Emit an H.265 slice-segment header into a fresh RBSP byte sequence.
/// Skips the NAL header byte — caller prepends it for full NAL framing.
pub fn emit_h265_slice_header(h: &H265SliceHeader) -> Result<Vec<u8>, EmitError> {
    let mut w = BitWriter::new();

    // first_slice_segment_in_pic_flag u(1)
    w.write_flag(h.first_slice_segment_in_pic_flag);

    // no_output_of_prior_pics_flag (IRAP only). For simplicity we
    // emit it whenever first_slice_segment is set; an IRAP-only
    // emitter would gate by NAL type.
    if h.first_slice_segment_in_pic_flag {
        w.write_flag(h.no_output_of_prior_pics_flag);
    }

    // slice_pic_parameter_set_id ue(v)
    w.write_ue(h.slice_pic_parameter_set_id);

    // dependent_slice_segment_flag (always 0 in this minimal emitter)
    if !h.first_slice_segment_in_pic_flag {
        if h.slice_segment_address_bits == 0 {
            return Err(EmitError::InvalidFieldWidth("slice_segment_address"));
        }
        // We don't support dependent slices: emit 0.
        // dependent_slice_segment_flag u(1)
        w.write_flag(false);
        // slice_segment_address u(v) — bit width set by caller
        w.write_u(h.slice_segment_address, h.slice_segment_address_bits);
    }

    // slice_type ue(v)
    w.write_ue(h.slice_type.to_ue());

    // pic_output_flag u(1)
    w.write_flag(h.pic_output_flag);

    // slice_pic_order_cnt_lsb u(v)
    if h.slice_pic_order_cnt_lsb_bits == 0 {
        return Err(EmitError::InvalidFieldWidth("slice_pic_order_cnt_lsb"));
    }
    w.write_u(h.slice_pic_order_cnt_lsb, h.slice_pic_order_cnt_lsb_bits);

    // short_term_ref_pic_set_sps_flag u(1)
    w.write_flag(h.short_term_ref_pic_set_sps_flag);
    if h.short_term_ref_pic_set_sps_flag {
        if h.short_term_ref_pic_set_idx_bits > 0 {
            w.write_u(
                h.short_term_ref_pic_set_idx,
                h.short_term_ref_pic_set_idx_bits,
            );
        }
        // else: 0 RPSs in SPS, no index field emitted.
    }
    // (Inline RPS path omitted in this minimal emitter.)

    // sao_luma_flag + sao_chroma_flag u(1) each — when SAO enabled
    // in PPS (we assume yes for a transcoded H.265 stream).
    w.write_flag(h.sao_luma_flag);
    w.write_flag(h.sao_chroma_flag);

    // Reference index counts for non-I slices.
    if !matches!(h.slice_type, H265SliceType::I) {
        // num_ref_idx_active_override_flag = 1 to send the counts
        w.write_flag(true);
        w.write_ue(h.num_ref_idx_l0_active_minus1 as u32);
        if matches!(h.slice_type, H265SliceType::B) {
            w.write_ue(h.num_ref_idx_l1_active_minus1 as u32);
        }
    }

    // slice_qp_delta se(v)
    w.write_se(h.qp_delta);

    // slice_deblocking_filter_disabled_flag u(1)
    w.write_flag(h.deblocking_filter_disabled_flag);

    Ok(w.finish_rbsp())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bitwriter_basic_u() {
        let mut w = BitWriter::new();
        w.write_u(0b10101100, 8);
        assert_eq!(w.finish_rbsp(), vec![0b10101100, 0b10000000]);
    }

    #[test]
    fn bitwriter_partial_byte_finalised() {
        let mut w = BitWriter::new();
        w.write_u(0b101, 3);
        let bytes = w.finish_rbsp();
        // bits: 1 0 1 (stop) 1 0 0 0 0 = 0b10110000
        assert_eq!(bytes, vec![0b10110000]);
    }

    #[test]
    fn write_ue_zero() {
        // ue(0) = "1"
        let mut w = BitWriter::new();
        w.write_ue(0);
        // After stop bit + padding: bits = "1" + "1000000" = 0b11000000
        assert_eq!(w.finish_rbsp(), vec![0b11000000]);
    }

    #[test]
    fn write_ue_one() {
        // ue(1) = "010"
        let mut w = BitWriter::new();
        w.write_ue(1);
        // "010" + stop "1" + padding "0000" → 0b01010000
        assert_eq!(w.finish_rbsp(), vec![0b01010000]);
    }

    #[test]
    fn write_ue_two() {
        // ue(2) = "011"
        let mut w = BitWriter::new();
        w.write_ue(2);
        assert_eq!(w.finish_rbsp(), vec![0b01110000]);
    }

    #[test]
    fn write_ue_four() {
        // ue(4) = "00101"
        let mut w = BitWriter::new();
        w.write_ue(4);
        // 00101 + 1 + 00 = 0b00101100
        assert_eq!(w.finish_rbsp(), vec![0b00101100]);
    }

    #[test]
    fn write_se_zero() {
        // se(0) = ue(0) = "1"
        let mut w = BitWriter::new();
        w.write_se(0);
        assert_eq!(w.finish_rbsp(), vec![0b11000000]);
    }

    #[test]
    fn write_se_one() {
        // se(1) = ue(1) = "010"
        let mut w = BitWriter::new();
        w.write_se(1);
        assert_eq!(w.finish_rbsp(), vec![0b01010000]);
    }

    #[test]
    fn write_se_minus_one() {
        // se(-1) = ue(2) = "011"
        let mut w = BitWriter::new();
        w.write_se(-1);
        assert_eq!(w.finish_rbsp(), vec![0b01110000]);
    }

    #[test]
    fn emit_simple_idr_slice_header() {
        let h = H265SliceHeader {
            first_slice_segment_in_pic_flag: true,
            no_output_of_prior_pics_flag: false,
            slice_pic_parameter_set_id: 0,
            slice_segment_address: 0,
            slice_segment_address_bits: 0,
            slice_type: H265SliceType::I,
            pic_output_flag: true,
            slice_pic_order_cnt_lsb: 0,
            slice_pic_order_cnt_lsb_bits: 4,
            short_term_ref_pic_set_sps_flag: false,
            short_term_ref_pic_set_idx: 0,
            short_term_ref_pic_set_idx_bits: 0,
            sao_luma_flag: true,
            sao_chroma_flag: true,
            num_ref_idx_l0_active_minus1: 0,
            num_ref_idx_l1_active_minus1: 0,
            qp_delta: 0,
            deblocking_filter_disabled_flag: false,
        };
        let bytes = emit_h265_slice_header(&h).expect("emit");
        // Length sanity: an I-slice header should be tiny.
        assert!(!bytes.is_empty());
        assert!(
            bytes.len() < 16,
            "I-slice header should be small; got {} bytes",
            bytes.len()
        );
    }

    #[test]
    fn emit_p_slice_header_emits_more_fields() {
        let p = H265SliceHeader {
            first_slice_segment_in_pic_flag: true,
            no_output_of_prior_pics_flag: false,
            slice_pic_parameter_set_id: 0,
            slice_segment_address: 0,
            slice_segment_address_bits: 0,
            slice_type: H265SliceType::P,
            pic_output_flag: true,
            slice_pic_order_cnt_lsb: 1,
            slice_pic_order_cnt_lsb_bits: 4,
            short_term_ref_pic_set_sps_flag: true,
            short_term_ref_pic_set_idx: 0,
            short_term_ref_pic_set_idx_bits: 0,
            sao_luma_flag: true,
            sao_chroma_flag: true,
            num_ref_idx_l0_active_minus1: 0,
            num_ref_idx_l1_active_minus1: 0,
            qp_delta: 0,
            deblocking_filter_disabled_flag: false,
        };
        let i = H265SliceHeader {
            slice_type: H265SliceType::I,
            ..p.clone()
        };
        let bytes_p = emit_h265_slice_header(&p).expect("emit P");
        let bytes_i = emit_h265_slice_header(&i).expect("emit I");
        // P-slice writes ref-idx fields; should be ≥ I-slice length.
        assert!(bytes_p.len() >= bytes_i.len());
    }

    #[test]
    fn slice_type_from_h264_correct() {
        assert_eq!(H265SliceType::from_h264(0), Some(H265SliceType::P));
        assert_eq!(H265SliceType::from_h264(1), Some(H265SliceType::B));
        assert_eq!(H265SliceType::from_h264(2), Some(H265SliceType::I));
        // H.264 codes 5..9 = same modulo 5.
        assert_eq!(H265SliceType::from_h264(5), Some(H265SliceType::P));
        assert_eq!(H265SliceType::from_h264(7), Some(H265SliceType::I));
        // SP/SI not supported.
        assert_eq!(H265SliceType::from_h264(3), None);
        assert_eq!(H265SliceType::from_h264(4), None);
    }
}
