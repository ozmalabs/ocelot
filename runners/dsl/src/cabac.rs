//! CABAC engine primitive — Context-Adaptive Binary Arithmetic Coding
//! per ITU-T H.264 §9.3.
//!
//! This module implements the CABAC arithmetic engine — three
//! operations: `decode_bin` (context-aware), `decode_bypass` (1/2
//! probability), `decode_terminate` (end-of-slice flag). The
//! H.264 context MODEL (~460 contexts, each with specific
//! initialization rules based on slice_type + slice_qp) lives in a
//! higher layer and isn't bundled here — the engine is what's
//! universal across all CABAC-based codecs (H.264, also AV1 uses a
//! similar arithmetic engine).
//!
//! The encoder and decoder are mirror operations on the same state
//! tables, so round-trip is provable.
//!
//! Reference: ITU-T H.264 §9.3.3 (decoder) and §9.3.4 (encoder).
//! Tables: rangeTabLPS / transIdxLPS / transIdxMPS from §9.3.3.2.1.1
//! / §9.3.3.2.4 / §9.3.3.2.4.

/// Range table for LPS (least probable symbol) per §9.3.3.2.1.1
/// Table 9-44. Indexed by pStateIdx (0..63) × qCodIRangeIdx (0..3).
#[rustfmt::skip]
const RANGE_TAB_LPS: [[u16; 4]; 64] = [
    [128, 176, 208, 240], [128, 167, 197, 227], [128, 158, 187, 216], [123, 150, 178, 205],
    [116, 142, 169, 195], [111, 135, 160, 185], [105, 128, 152, 175], [100, 122, 144, 166],
    [95, 116, 137, 158],  [90, 110, 130, 150],  [85, 104, 123, 142],  [81, 99, 117, 135],
    [77, 94, 111, 128],   [73, 89, 105, 122],   [69, 85, 100, 116],   [66, 80, 95, 110],
    [62, 76, 90, 104],    [59, 72, 86, 99],     [56, 69, 81, 94],     [53, 65, 77, 89],
    [51, 62, 73, 85],     [48, 59, 69, 80],     [46, 56, 66, 76],     [43, 53, 63, 72],
    [41, 50, 59, 69],     [39, 48, 56, 65],     [37, 45, 54, 62],     [35, 43, 51, 59],
    [33, 41, 48, 56],     [32, 39, 46, 53],     [30, 37, 43, 50],     [29, 35, 41, 48],
    [27, 33, 39, 45],     [26, 31, 37, 43],     [24, 30, 35, 41],     [23, 28, 33, 39],
    [22, 27, 32, 37],     [21, 26, 30, 35],     [20, 24, 29, 33],     [19, 23, 27, 31],
    [18, 22, 26, 30],     [17, 21, 25, 28],     [16, 20, 23, 27],     [15, 19, 22, 25],
    [14, 18, 21, 24],     [14, 17, 20, 23],     [13, 16, 19, 22],     [12, 15, 18, 21],
    [12, 14, 17, 20],     [11, 14, 16, 19],     [11, 13, 15, 18],     [10, 12, 15, 17],
    [10, 12, 14, 16],     [9, 11, 13, 15],      [9, 11, 12, 14],      [8, 10, 12, 14],
    [8, 9, 11, 13],       [7, 9, 11, 12],       [7, 9, 10, 12],       [7, 8, 10, 11],
    [6, 8, 9, 11],        [6, 7, 9, 10],        [6, 7, 8, 9],         [2, 2, 2, 2],
];

/// State transition for MPS (most probable symbol) outcome — §9.3.3.2.4
/// Table 9-45.
const TRANS_IDX_MPS: [u8; 64] = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
    27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50,
    51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 62, 63,
];

/// State transition for LPS outcome — §9.3.3.2.4 Table 9-45.
const TRANS_IDX_LPS: [u8; 64] = [
    0, 0, 1, 2, 2, 4, 4, 5, 6, 7, 8, 9, 9, 11, 11, 12, 13, 13, 15, 15, 16, 16, 18, 18, 19, 19, 21,
    21, 22, 22, 23, 24, 24, 25, 26, 26, 27, 27, 28, 29, 29, 30, 30, 30, 31, 32, 32, 33, 33, 33, 34,
    34, 35, 35, 35, 36, 36, 36, 37, 37, 37, 38, 38, 63,
];

// Per-context initialisation tables — 1024 contexts × 2 (m, n)
// parameters each, for I-slice + 3 P/B variants by cabac_init_idc.
// Extracted from FFmpeg's libavcodec/h264_cabac.c. ITU-T H.264
// §9.3.1.1 init formula:
//
//   preCtxState = Clip3(0, 127, ((m * SliceQPY) >> 4) + n)
//   if preCtxState <= 63:  pStateIdx = 63 - preCtxState; val_mps = 0
//   else:                  pStateIdx = preCtxState - 64; val_mps = 1
include!("cabac_init_tables.rs");

/// Slice type for context initialisation. (I/SI use one table;
/// P/SP/B share three tables indexed by cabac_init_idc.)
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum CabacSliceType {
    I,
    P,
    B,
}

/// One CABAC context: probability state (0..63) + MPS bit value (0/1).
#[derive(Copy, Clone, Debug, Default, PartialEq, Eq)]
pub struct CabacCtx {
    pub p_state_idx: u8, // 0..63
    pub val_mps: u8,     // 0 or 1
}

impl CabacCtx {
    /// Initialise one context from (m, n) per §9.3.1.1.1:
    ///   preCtxState = Clip3(1, 126,
    ///                       ((m * Clip3(0, 51, SliceQPY)) >> 4) + n)
    /// Then split into (p_state_idx, val_mps).
    pub fn init_from_mn(m: i8, n: i8, slice_qp: i32) -> Self {
        let qpy_clipped = slice_qp.max(0).min(51);
        let pre_raw = ((m as i32 * qpy_clipped) >> 4) + n as i32;
        // Spec: Clip3(1, 126, …). NOT 0..127 — extreme QPs +
        // contexts with n at the rails would otherwise produce
        // preCtxState=0/127, which encode/decode round-trips
        // within our own engine but diverges from any spec-
        // conformant decoder (e.g. libavcodec).
        let pre = pre_raw.max(1).min(126) as u8;
        if pre <= 63 {
            CabacCtx {
                p_state_idx: 63 - pre,
                val_mps: 0,
            }
        } else {
            CabacCtx {
                p_state_idx: pre - 64,
                val_mps: 1,
            }
        }
    }
}

// --- H.264 syntax element: mb_skip_flag ----------------------------
//
// First syntax element decoded per macroblock in P/SP/B slices.
// Per ITU-T §9.3.3.1.1.1, ctxIdxInc is the count of available
// neighbours whose own mb_skip_flag was 0 — i.e., neighbours that
// were NOT skipped. ctxIdxOffset depends on slice type.

/// ctxIdxOffset for mb_skip_flag per slice type (§9.3.3.1.1.1
/// + Table 9-34). I/SI slices don't use mb_skip_flag at all.
pub fn mb_skip_flag_ctx_offset(slice_type: CabacSliceType) -> Option<usize> {
    match slice_type {
        CabacSliceType::P => Some(11),
        CabacSliceType::B => Some(24),
        CabacSliceType::I => None,
    }
}

/// ctxIdxInc for mb_skip_flag — counts available neighbours that
/// were NOT skipped. Per §9.3.3.1.1.1:
///   condTermFlagA = 1 iff neighbour A is available AND its skip was 0
///   condTermFlagB = 1 iff neighbour B is available AND its skip was 0
///   ctxIdxInc     = condTermFlagA + condTermFlagB     (∈ 0..2)
pub fn mb_skip_flag_ctx_idx_inc(
    left_neighbour_skip: Option<u8>,
    top_neighbour_skip: Option<u8>,
) -> usize {
    let a = match left_neighbour_skip {
        Some(0) => 1,
        _ => 0,
    };
    let b = match top_neighbour_skip {
        Some(0) => 1,
        _ => 0,
    };
    a + b
}

/// Full ctxIdx for mb_skip_flag in one helper.
pub fn mb_skip_flag_ctx_idx(
    slice_type: CabacSliceType,
    left: Option<u8>,
    top: Option<u8>,
) -> Option<usize> {
    let off = mb_skip_flag_ctx_offset(slice_type)?;
    Some(off + mb_skip_flag_ctx_idx_inc(left, top))
}

// --- H.264 syntax element: mb_type (P-slice) -----------------------
//
// Per ITU-T §9.3.3.1.1.5 + Table 9-37 (binarisation) + Table 9-39
// (context offsets). The four P-slice mb_types:
//
//   value  name              bin string
//   -----  ----------------  ----------
//     0    P_L0_16x16        "0"
//     1    P_L0_L0_16x8      "1 0 0"
//     2    P_L0_L0_8x16      "1 0 1"
//     3    P_8x8             "1 1"
//
// (P_Skip is not encoded here — it's signalled by mb_skip_flag.
//  Intra-in-P modes append the I-slice mb_type binarisation; out of
//  scope for this prototype.)
//
// Bin-position → context offset (Table 9-39 for P/SP slice):
//   bin 0: ctxIdxOffset + 0  (ctxIdx 14)
//   bin 1: ctxIdxOffset + 1  (ctxIdx 15)
//   bin 2: ctxIdxOffset + 2  (ctxIdx 16)

pub const P_MB_TYPE_CTX_OFFSET: usize = 14;
pub const B_MB_TYPE_CTX_OFFSET: usize = 27;

/// Encode a P-slice mb_type value (0..3) as a bin sequence under
/// the right contexts. Mutates the relevant context entries in
/// `contexts`. Returns the number of bins emitted.
pub fn encode_p_mb_type(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    mb_type: u8,
) -> usize {
    match mb_type {
        0 => {
            // "0"
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET], 0);
            1
        }
        1 => {
            // "1 0 0"
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET], 1);
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 1], 0);
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 2], 0);
            3
        }
        2 => {
            // "1 0 1"
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET], 1);
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 1], 0);
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 2], 1);
            3
        }
        3 => {
            // "1 1"
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET], 1);
            encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 1], 1);
            2
        }
        _ => panic!("P-slice mb_type must be 0..3; got {}", mb_type),
    }
}

/// Decode one P-slice mb_type by walking the binarisation tree.
/// Returns (mb_type, bins_consumed).
pub fn decode_p_mb_type(decoder: &mut CabacDecoder, contexts: &mut [CabacCtx]) -> (u8, usize) {
    let b0 = decoder.decode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET]);
    if b0 == 0 {
        // P_L0_16x16
        return (0, 1);
    }
    let b1 = decoder.decode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 1]);
    if b1 == 1 {
        // P_8x8
        return (3, 2);
    }
    let b2 = decoder.decode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 2]);
    if b2 == 0 {
        (1, 3) // P_L0_L0_16x8
    } else {
        (2, 3) // P_L0_L0_8x16
    }
}

// --- H.264 syntax element: mb_qp_delta -----------------------------
//
// Per ITU-T §9.3.3.1.1.5 + Tables 9-37 (binarisation) + 9-39
// (context offsets). The macroblock-level QP modifier — the
// per-MB knob a real transrate operation mutates to push QP up
// (coarser quantization, smaller output).
//
// Encoding pipeline:
//   1. Signed delta → unsigned via §9.1.1:
//        k = 2*d - 1 if d > 0
//        k = -2*d    if d ≤ 0
//   2. Emit k consecutive '1' bins + one terminating '0' bin (unary
//      binarisation per §9.3.2.5; cMax = 51 for 8-bit, but we
//      decode/encode any length here — overflow is the caller's
//      responsibility).
//   3. Each bin's context (per Table 9-39):
//        bin 0:   ctx 60 if PREVIOUS MB's delta was 0
//                 ctx 61 if PREVIOUS MB's delta was non-zero
//        bin 1:   ctx 62
//        bin 2+:  ctx 63

pub const MB_QP_DELTA_CTX_OFFSET: usize = 60;

/// Map signed delta (typical range -26..+25) to the unsigned value
/// fed into the unary coder.
pub fn mb_qp_delta_signed_to_unsigned(delta: i32) -> u32 {
    if delta > 0 {
        (2 * delta - 1) as u32
    } else {
        (-2 * delta) as u32
    }
}

/// Inverse mapping — what the decoder applies after reading the
/// unsigned k off the bin stream.
pub fn mb_qp_delta_unsigned_to_signed(k: u32) -> i32 {
    if k & 1 == 1 {
        ((k + 1) / 2) as i32
    } else {
        -((k / 2) as i32)
    }
}

/// Pick the ctxIdx for `bin_idx` given `prev_mb_qp_delta_was_zero`.
pub fn mb_qp_delta_ctx_idx(bin_idx: usize, prev_was_zero: bool) -> usize {
    match bin_idx {
        0 => MB_QP_DELTA_CTX_OFFSET + if prev_was_zero { 0 } else { 1 },
        1 => MB_QP_DELTA_CTX_OFFSET + 2,
        _ => MB_QP_DELTA_CTX_OFFSET + 3,
    }
}

/// Encode mb_qp_delta under the right contexts. `prev_was_zero` is
/// the state carried from the previous MB in this slice; the
/// caller is responsible for tracking it.
pub fn encode_mb_qp_delta(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    delta: i32,
    prev_was_zero: bool,
) -> usize {
    let k = mb_qp_delta_signed_to_unsigned(delta);
    let mut bin_idx = 0;
    // Emit k '1' bins.
    for _ in 0..k {
        let ctx = mb_qp_delta_ctx_idx(bin_idx, prev_was_zero);
        encoder.encode_bin(&mut contexts[ctx], 1);
        bin_idx += 1;
    }
    // Terminating '0' bin.
    let ctx = mb_qp_delta_ctx_idx(bin_idx, prev_was_zero);
    encoder.encode_bin(&mut contexts[ctx], 0);
    bin_idx + 1
}

/// Decode one mb_qp_delta. Returns (signed_delta, bins_consumed).
pub fn decode_mb_qp_delta(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    prev_was_zero: bool,
) -> (i32, usize) {
    let mut k: u32 = 0;
    let mut bin_idx = 0;
    loop {
        let ctx = mb_qp_delta_ctx_idx(bin_idx, prev_was_zero);
        let bin = decoder.decode_bin(&mut contexts[ctx]);
        bin_idx += 1;
        if bin == 0 {
            break;
        }
        k += 1;
        // Sanity cap — H.264 allows mb_qp_delta in [-26, 25], so
        // k ≤ 51 for 8-bit. Bail out if the stream is malformed.
        if k > 100 {
            break;
        }
    }
    (mb_qp_delta_unsigned_to_signed(k), bin_idx)
}

// --- H.264 syntax element: coded_block_pattern ---------------------
//
// Per ITU-T §9.3.3.1.1.4 + Tables 9-37/9-39. Two-part field:
//
//   coded_block_pattern_luma:   4 bins (one per 8x8 luma block in
//                                the MB), neighbour-aware contexts.
//                                ctxIdxOffset = 73; ctxIdxInc =
//                                condTermFlagA + 2*condTermFlagB.
//
//   coded_block_pattern_chroma: 0-2 bins encoding value 0/1/2.
//                                Only present for YUV420/422/444.
//                                ctxIdxOffset = 77; bin 0 says
//                                "chroma has any coded blocks";
//                                bin 1 (only if bin 0 = 1) says
//                                "AC coeffs present too".
//
// Within an MB, the four luma 8x8 blocks form a 2x2 grid:
//
//     [block 0][block 1]
//     [block 2][block 3]
//
// Each block's neighbours for CBP context:
//
//   block 0:  left = left_mb.block_1,  top = top_mb.block_2
//   block 1:  left = this_mb.block_0,  top = top_mb.block_3
//   block 2:  left = left_mb.block_3,  top = this_mb.block_0
//   block 3:  left = this_mb.block_2,  top = this_mb.block_1
//
// Where left_mb / top_mb are the neighbour macroblock's CBP-luma
// nibbles (or 0 if the neighbour is unavailable / intra-coded).

pub const CBP_LUMA_CTX_OFFSET: usize = 73;
pub const CBP_CHROMA_CTX_OFFSET: usize = 77;

/// Per-block (left, top) neighbour mapping. Returns the bit index
/// to read from each of (left_mb_cbp, top_mb_cbp, this_mb_cbp_so_far)
/// in the order (which_source, bit_index).
fn cbp_luma_neighbour_bit(
    block_idx: usize,
    this_cbp_so_far: u8,
    left_mb_cbp: u8,
    top_mb_cbp: u8,
) -> (u8, u8) {
    // Returns (left_condTermFlag, top_condTermFlag), each 0/1.
    let bit = |cbp: u8, b: usize| (cbp >> b) & 1;
    match block_idx {
        0 => (bit(left_mb_cbp, 1), bit(top_mb_cbp, 2)),
        1 => (bit(this_cbp_so_far, 0), bit(top_mb_cbp, 3)),
        2 => (bit(left_mb_cbp, 3), bit(this_cbp_so_far, 0)),
        3 => (bit(this_cbp_so_far, 2), bit(this_cbp_so_far, 1)),
        _ => panic!("luma 8x8 block_idx must be 0..3, got {}", block_idx),
    }
}

/// ctxIdxInc for coded_block_pattern_luma per Table 9-39:
///   ctxIdxInc = condTermFlagA + 2 * condTermFlagB
fn cbp_luma_ctx_idx_inc(left_term: u8, top_term: u8) -> usize {
    // Per §9.3.3.1.1.4, condTermFlagN = 1 when the neighbour's
    // CBP bit is 0 (no coded coefs there) and N is available; we
    // invert the raw neighbour bit before summing.
    let a = if left_term == 0 { 1usize } else { 0 };
    let b = if top_term == 0 { 1usize } else { 0 };
    a + 2 * b
}

/// Encode coded_block_pattern_luma (low 4 bits of cbp). Returns
/// bins emitted (always 4).
pub fn encode_cbp_luma(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    cbp_luma: u8,
    left_mb_cbp: u8,
    top_mb_cbp: u8,
) -> usize {
    let mut this_so_far: u8 = 0;
    for i in 0..4 {
        let (a, b) = cbp_luma_neighbour_bit(i, this_so_far, left_mb_cbp, top_mb_cbp);
        let inc = cbp_luma_ctx_idx_inc(a, b);
        let bit = (cbp_luma >> i) & 1;
        encoder.encode_bin(&mut contexts[CBP_LUMA_CTX_OFFSET + inc], bit);
        this_so_far |= bit << i;
    }
    4
}

/// Decode coded_block_pattern_luma. Returns (cbp_luma, bins_consumed).
pub fn decode_cbp_luma(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    left_mb_cbp: u8,
    top_mb_cbp: u8,
) -> (u8, usize) {
    let mut this_so_far: u8 = 0;
    for i in 0..4 {
        let (a, b) = cbp_luma_neighbour_bit(i, this_so_far, left_mb_cbp, top_mb_cbp);
        let inc = cbp_luma_ctx_idx_inc(a, b);
        let bit = decoder.decode_bin(&mut contexts[CBP_LUMA_CTX_OFFSET + inc]);
        this_so_far |= bit << i;
    }
    (this_so_far, 4)
}

/// ctxIdxInc for coded_block_pattern_chroma bin 0 per Table 9-39:
///   condTermFlagA = 1 if left_mb.cbp_chroma != 0
///   condTermFlagB = 1 if top_mb.cbp_chroma  != 0
///   ctxIdxInc     = condTermFlagA + 2 * condTermFlagB
fn cbp_chroma_bin0_ctx_idx_inc(left_chroma_cbp: u8, top_chroma_cbp: u8) -> usize {
    let a = if left_chroma_cbp != 0 { 1 } else { 0 };
    let b = if top_chroma_cbp != 0 { 1 } else { 0 };
    a + 2 * b
}

/// ctxIdxInc for coded_block_pattern_chroma bin 1 — gated on
/// (left.cbp_chroma == 2 / top.cbp_chroma == 2).
fn cbp_chroma_bin1_ctx_idx_inc(left_chroma_cbp: u8, top_chroma_cbp: u8) -> usize {
    let a = if left_chroma_cbp == 2 { 1 } else { 0 };
    let b = if top_chroma_cbp == 2 { 1 } else { 0 };
    a + 2 * b
}

/// Encode coded_block_pattern_chroma (value 0/1/2).
///   value 0: emit "0"
///   value 1: emit "1 0"
///   value 2: emit "1 1"
pub fn encode_cbp_chroma(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    cbp_chroma: u8,
    left_chroma_cbp: u8,
    top_chroma_cbp: u8,
) -> usize {
    let inc0 = cbp_chroma_bin0_ctx_idx_inc(left_chroma_cbp, top_chroma_cbp);
    if cbp_chroma == 0 {
        encoder.encode_bin(&mut contexts[CBP_CHROMA_CTX_OFFSET + inc0], 0);
        return 1;
    }
    encoder.encode_bin(&mut contexts[CBP_CHROMA_CTX_OFFSET + inc0], 1);
    let inc1 = cbp_chroma_bin1_ctx_idx_inc(left_chroma_cbp, top_chroma_cbp);
    // Bin 1 uses ctxIdxOffset+4 onwards (per Table 9-39 row layout).
    encoder.encode_bin(
        &mut contexts[CBP_CHROMA_CTX_OFFSET + 4 + inc1],
        if cbp_chroma == 2 { 1 } else { 0 },
    );
    2
}

/// Decode coded_block_pattern_chroma. Returns (value 0/1/2,
/// bins_consumed).
pub fn decode_cbp_chroma(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    left_chroma_cbp: u8,
    top_chroma_cbp: u8,
) -> (u8, usize) {
    let inc0 = cbp_chroma_bin0_ctx_idx_inc(left_chroma_cbp, top_chroma_cbp);
    let b0 = decoder.decode_bin(&mut contexts[CBP_CHROMA_CTX_OFFSET + inc0]);
    if b0 == 0 {
        return (0, 1);
    }
    let inc1 = cbp_chroma_bin1_ctx_idx_inc(left_chroma_cbp, top_chroma_cbp);
    let b1 = decoder.decode_bin(&mut contexts[CBP_CHROMA_CTX_OFFSET + 4 + inc1]);
    (if b1 == 1 { 2 } else { 1 }, 2)
}

// --- H.264 syntax element: coded_block_flag ------------------------
//
// Per ITU-T §9.3.3.1.1.9 + Table 9-42. Single bin per 4×4 (or
// 4-coef chroma DC, or 8×8) block, signalling whether the block has
// any significant coefficients. Required to make residual_block
// round-trippable on all-zero blocks (without CBF, decoder can't
// tell an all-zero block from a missing block).
//
// ctxIdxOffset = 85; per-category modifier:
//   Intra16x16Dc: +0   → ctxIdx 85..88
//   Intra16x16Ac: +4   → ctxIdx 89..92
//   Luma4x4:      +8   → ctxIdx 93..96
//   ChromaDc:     +12  → ctxIdx 97..100
//   ChromaAc:     +16  → ctxIdx 101..104
//   Luma8x8:      separate range starting at 1012 (out of scope here)
//
// ctxIdxInc derivation (§9.3.3.1.1.9 Table 9-43) uses the same-
// category CBF of left + top neighbour blocks. For our walker we
// keep that derivation simple by passing pre-computed condTermFlags.

pub const CBF_CTX_OFFSET: usize = 85;

fn cbf_cat_offset(cat: CtxBlockCat) -> usize {
    match cat {
        CtxBlockCat::Intra16x16Dc => 0,
        CtxBlockCat::Intra16x16Ac => 4,
        CtxBlockCat::Luma4x4 => 8,
        CtxBlockCat::ChromaDc => 12,
        CtxBlockCat::ChromaAc => 16,
        CtxBlockCat::Luma8x8 => {
            panic!("Luma8x8 CBF uses ctxIdxOffset 1012; out of scope here");
        }
    }
}

/// Encode coded_block_flag (CBF) for the given block category.
/// `left_cbf` and `top_cbf` are the same-category CBFs of the
/// left and top neighbour blocks (None = unavailable).
pub fn encode_coded_block_flag(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    cat: CtxBlockCat,
    cbf: bool,
    left_cbf: Option<bool>,
    top_cbf: Option<bool>,
) -> usize {
    let a = match left_cbf {
        Some(true) => 1,
        _ => 0,
    };
    let b = match top_cbf {
        Some(true) => 1,
        _ => 0,
    };
    let inc = a + 2 * b;
    let ctx = CBF_CTX_OFFSET + cbf_cat_offset(cat) + inc;
    encoder.encode_bin(&mut contexts[ctx], if cbf { 1 } else { 0 });
    1
}

/// Decode coded_block_flag for the given block category.
pub fn decode_coded_block_flag(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    cat: CtxBlockCat,
    left_cbf: Option<bool>,
    top_cbf: Option<bool>,
) -> (bool, usize) {
    let a = match left_cbf {
        Some(true) => 1,
        _ => 0,
    };
    let b = match top_cbf {
        Some(true) => 1,
        _ => 0,
    };
    let inc = a + 2 * b;
    let ctx = CBF_CTX_OFFSET + cbf_cat_offset(cat) + inc;
    let b = decoder.decode_bin(&mut contexts[ctx]);
    (b == 1, 1)
}

// --- H.264 syntax element: mb_type (I-slice) -----------------------
//
// Per ITU-T §9.3.3.1.1.5 + Tables 9-36/9-39. I-slice mb_type values:
//
//   value  name           binarisation
//   -----  -------------  ----------------------------------------
//     0    I_NxN          "0"
//     1    I_16x16_0_0_0  "1 0 0 0 0 0"
//     ...                  (24 I_16x16_X_Y_Z variants)
//    25    I_PCM          "1 1"   (bin 1 via TERMINATE)
//
// For the I-only downscale MVP we only emit/parse I_NxN. The full
// binarisation tree (rows 1-24) is added when the input stream
// actually contains I_16x16-coded MBs.
//
// ctxIdxOffset = 3 for I slice; +1 for SI bin 0 only.
// Bin 0 ctxIdxInc per §9.3.3.1.1.3:
//   condTermFlagN = 0 if N unavailable or N's mb_type is I_NxN
//   condTermFlagN = 1 otherwise (I_16x16_* / I_PCM in I slice)
//   ctxIdxInc     = condTermA + condTermB

pub const I_MB_TYPE_CTX_OFFSET: usize = 3;

fn i_mb_type_cond_term(neighbour_is_i_nxn: Option<bool>) -> u8 {
    match neighbour_is_i_nxn {
        None => 0,
        Some(true) => 0,
        Some(false) => 1,
    }
}

/// Public wrapper for the real-bitstream MB decoder in
/// `h264_cabac_mb.rs` — same condTerm rule, exposed across the module
/// boundary.
pub fn i_mb_type_cond_term_pub(neighbour_is_i_nxn: Option<bool>) -> u8 {
    i_mb_type_cond_term(neighbour_is_i_nxn)
}

/// Encode I-slice mb_type == I_NxN (the I_NxN-only path used by the
/// downscale emitter). Returns bins emitted (= 1).
pub fn encode_i_mb_type_i_nxn(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    left_neighbour_is_i_nxn: Option<bool>,
    top_neighbour_is_i_nxn: Option<bool>,
) -> usize {
    let inc =
        i_mb_type_cond_term(left_neighbour_is_i_nxn) + i_mb_type_cond_term(top_neighbour_is_i_nxn);
    let ctx = I_MB_TYPE_CTX_OFFSET + inc as usize;
    encoder.encode_bin(&mut contexts[ctx], 0); // I_NxN → bin "0"
    1
}

/// Decode I-slice mb_type bin 0 — tells us whether the MB is
/// I_NxN (returns true) or some other intra type (returns false,
/// caller must parse the rest of the binarisation tree).
///
/// Returns (is_i_nxn, bins_consumed=1).
pub fn decode_i_mb_type_is_i_nxn(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    left_neighbour_is_i_nxn: Option<bool>,
    top_neighbour_is_i_nxn: Option<bool>,
) -> (bool, usize) {
    let inc =
        i_mb_type_cond_term(left_neighbour_is_i_nxn) + i_mb_type_cond_term(top_neighbour_is_i_nxn);
    let ctx = I_MB_TYPE_CTX_OFFSET + inc as usize;
    let b = decoder.decode_bin(&mut contexts[ctx]);
    (b == 0, 1)
}

// --- H.264 syntax element: intra prediction modes ------------------
//
// Per ITU-T §9.3.3.1.1 + Tables 9-37 / 9-39. Three sub-elements,
// emitted inside an I-slice (and intra-coded MBs in P/B slices):
//
//   prev_intra4x4_pred_mode_flag  — per 4×4 luma sub-block. 1 bin.
//                                    Bit says "use the spec's
//                                    predicted mode from neighbours
//                                    (1) or override (0)".
//                                    ctxIdxOffset = 68
//                                    ctxIdxInc = 0   (one ctx)
//
//   rem_intra4x4_pred_mode        — only when the flag is 0. 3 bins,
//                                    fixed-length binarisation of a
//                                    3-bit value (the "remainder"
//                                    mode index in [0..7]).
//                                    ctxIdxOffset = 69
//                                    ctxIdxInc = 0   (all bins same ctx)
//
//   intra_chroma_pred_mode        — once per MB. Truncated unary with
//                                    cMax = 3 → up to 3 bins.
//                                    ctxIdxOffset = 64
//                                    ctxIdxInc on bin 0 is neighbour-
//                                    aware (condTermFlagA+B), bin 1
//                                    and bin 2 use fixed +3 / +3.
//
// Per-4×4-block intra mode count: an MB has 16 luma 4×4 sub-blocks,
// so the prev_flag+rem pair is emitted 16 times per I_NxN MB.

pub const INTRA_CHROMA_CTX_OFFSET: usize = 64;
pub const PREV_INTRA4X4_FLAG_CTX_OFFSET: usize = 68;
pub const REM_INTRA4X4_CTX_OFFSET: usize = 69;

/// Encode `prev_intra4x4_pred_mode_flag`: a single bin with
/// ctxIdxOffset=68. Returns bins emitted (always 1).
pub fn encode_prev_intra4x4_flag(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    flag: bool,
) -> usize {
    encoder.encode_bin(
        &mut contexts[PREV_INTRA4X4_FLAG_CTX_OFFSET],
        if flag { 1 } else { 0 },
    );
    1
}

/// Decode `prev_intra4x4_pred_mode_flag`. Returns (flag, bins_consumed).
pub fn decode_prev_intra4x4_flag(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
) -> (bool, usize) {
    let b = decoder.decode_bin(&mut contexts[PREV_INTRA4X4_FLAG_CTX_OFFSET]);
    (b == 1, 1)
}

/// Encode `rem_intra4x4_pred_mode` (value 0..7) as 3 FL bins, all
/// using ctxIdxOffset=69 / ctxIdxInc=0. Bit order: MSB first per
/// §9.3.2.6 fixed-length binarisation.
pub fn encode_rem_intra4x4(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    rem: u8,
) -> usize {
    debug_assert!(rem < 8, "rem_intra4x4 must be in 0..7, got {}", rem);
    let ctx = REM_INTRA4X4_CTX_OFFSET;
    // FL binarisation, LSB-first (bin0 = bit0). Mirrors the decoder
    // and libavcodec.
    for shift in 0..3 {
        encoder.encode_bin(&mut contexts[ctx], (rem >> shift) & 1);
    }
    3
}

/// Decode `rem_intra4x4_pred_mode`. Returns (value, bins_consumed=3).
///
/// FL binarisation, cMax=7, ctxIdxOffset=69, all 3 bins share the same
/// context. Per the H.264 FL bin string the FIRST bin is bit 0 (the
/// LEAST significant bit) — see libavcodec
/// decode_cabac_mb_intra4x4_pred_mode (mode += 1*b0 + 2*b1 + 4*b2).
/// The previous code read MSB-first, which silently produced the wrong
/// mode for any rem with an asymmetric bit pattern (no CABAC desync,
/// since the bin COUNT is identical — which is why chroma stayed
/// bit-exact while luma intra modes were corrupted).
pub fn decode_rem_intra4x4(decoder: &mut CabacDecoder, contexts: &mut [CabacCtx]) -> (u8, usize) {
    let ctx = REM_INTRA4X4_CTX_OFFSET;
    let mut v: u8 = 0;
    for i in 0..3 {
        let b = decoder.decode_bin(&mut contexts[ctx]);
        v |= b << i;
    }
    (v, 3)
}

/// Neighbour state needed for `intra_chroma_pred_mode` bin 0 context:
/// the chroma pred mode of the left + top neighbour MBs. For each
/// neighbour, the contribution to ctxIdxInc is:
///   condTermFlag = 0  if neighbour unavailable
///                  0  if neighbour is intra coded AND its chroma
///                      pred mode == 0 (DC)
///                  1  otherwise
///
/// This is the H.264 spec's exact derivation per §9.3.3.1.1.8. Our
/// caller supplies (`avail`, `mode`) for each of left and top; we
/// return (left_term, top_term) for ctxIdxInc = left + top.
fn intra_chroma_cond_term(neighbour: Option<u8>) -> u8 {
    match neighbour {
        None => 0,
        Some(0) => 0,
        Some(_) => 1,
    }
}

/// Encode `intra_chroma_pred_mode` value 0..3 as a truncated unary
/// string with cMax=3 (so values 0,1,2 emit 1,2,2 bins and value 3
/// emits 3 bins — the same as plain unary for values < cMax). Bin
/// 0 uses ctxIdxOffset+ctxIdxInc, bins 1+2 use ctxIdxOffset+3.
pub fn encode_intra_chroma_pred_mode(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    mode: u8,
    left_neighbour_mode: Option<u8>,
    top_neighbour_mode: Option<u8>,
) -> usize {
    debug_assert!(mode < 4, "intra_chroma must be 0..3, got {}", mode);
    let inc0 =
        intra_chroma_cond_term(left_neighbour_mode) + intra_chroma_cond_term(top_neighbour_mode);
    let ctx0 = INTRA_CHROMA_CTX_OFFSET + inc0 as usize;
    let ctx_rest = INTRA_CHROMA_CTX_OFFSET + 3;
    let mut bins = 0;
    // Emit `mode` consecutive 1-bins…
    for i in 0..mode {
        let ctx = if i == 0 { ctx0 } else { ctx_rest };
        encoder.encode_bin(&mut contexts[ctx], 1);
        bins += 1;
    }
    // …then a terminating 0-bin if we haven't hit cMax.
    if mode < 3 {
        let ctx = if mode == 0 { ctx0 } else { ctx_rest };
        encoder.encode_bin(&mut contexts[ctx], 0);
        bins += 1;
    }
    bins
}

/// Decode `intra_chroma_pred_mode`. Returns (mode, bins_consumed).
pub fn decode_intra_chroma_pred_mode(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    left_neighbour_mode: Option<u8>,
    top_neighbour_mode: Option<u8>,
) -> (u8, usize) {
    let inc0 =
        intra_chroma_cond_term(left_neighbour_mode) + intra_chroma_cond_term(top_neighbour_mode);
    let ctx0 = INTRA_CHROMA_CTX_OFFSET + inc0 as usize;
    let ctx_rest = INTRA_CHROMA_CTX_OFFSET + 3;
    let mut mode: u8 = 0;
    let mut bins = 0;
    loop {
        let ctx = if mode == 0 { ctx0 } else { ctx_rest };
        let b = decoder.decode_bin(&mut contexts[ctx]);
        bins += 1;
        if b == 0 {
            return (mode, bins);
        }
        mode += 1;
        if mode == 3 {
            // cMax reached — value is exactly 3, no terminating bit.
            return (3, bins);
        }
    }
}

// --- H.264 syntax element: sub_mb_type (P-slice) -------------------
//
// Per ITU-T §9.3.3.1.1.2 + Tables 9-37/9-39. Emitted inside a
// P_8x8 macroblock to describe how the 8x8 partition further
// splits. Four values, multi-bin tree dispatch:
//
//   value  name              bin string   contexts
//   -----  ----------------  ----------   --------------
//     0    P_L0_8x8          "1"          21
//     1    P_L0_8x4          "00"         21, 22
//     2    P_L0_4x8          "01 1"       21, 22, 23
//     3    P_L0_4x4          "01 0"       21, 22, 23

pub const P_SUB_MB_TYPE_CTX_OFFSET: usize = 21;

/// Encode a P-slice sub_mb_type value (0..3). Returns bins emitted.
pub fn encode_p_sub_mb_type(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    sub_mb_type: u8,
) -> usize {
    match sub_mb_type {
        0 => {
            // "1"
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET], 1);
            1
        }
        1 => {
            // "00"
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET], 0);
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET + 1], 0);
            2
        }
        2 => {
            // "01 1"
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET], 0);
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET + 1], 1);
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET + 2], 1);
            3
        }
        3 => {
            // "01 0"
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET], 0);
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET + 1], 1);
            encoder.encode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET + 2], 0);
            3
        }
        _ => panic!("P sub_mb_type must be 0..3; got {}", sub_mb_type),
    }
}

/// Decode P-slice sub_mb_type. Returns (value, bins).
pub fn decode_p_sub_mb_type(decoder: &mut CabacDecoder, contexts: &mut [CabacCtx]) -> (u8, usize) {
    let b0 = decoder.decode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET]);
    if b0 == 1 {
        return (0, 1);
    }
    let b1 = decoder.decode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET + 1]);
    if b1 == 0 {
        return (1, 2);
    }
    let b2 = decoder.decode_bin(&mut contexts[P_SUB_MB_TYPE_CTX_OFFSET + 2]);
    if b2 == 1 {
        (2, 3)
    } else {
        (3, 3)
    }
}

// --- H.264 syntax element: ref_idx_l0 -------------------------------
//
// Per ITU-T §9.3.3.1.1.7 + Tables 9-37/9-39. Reference picture
// index — one of `num_ref_idx_l0_active_minus1 + 1` values, encoded
// as truncated unary.
//
// ctxIdxOffset = 54 (for l0) / 54+something for l1 — caller passes
// offset. Per Table 9-39:
//   Bin 0: ctxIdxInc = condTermFlagA + 2 * condTermFlagB  (∈ 0..3)
//     where condTermFlagN = 1 iff neighbour N is available, not
//     intra, AND its ref_idx > 0
//   Bin 1: ctxIdxInc = 4
//   Bin 2+: ctxIdxInc = 5
//
// We expose neighbour state via the bin-0 ctxIdxInc parameter so
// the caller can thread (left_ref, top_ref) state through a row
// of MBs.

pub const REF_IDX_L0_CTX_OFFSET: usize = 54;

/// Compute ctxIdxInc for bin 0 of ref_idx_l0 given neighbour state.
/// Each `*_ref_idx` is None if the neighbour is unavailable.
pub fn ref_idx_bin0_ctx_inc(left_ref_idx: Option<u8>, top_ref_idx: Option<u8>) -> usize {
    let a = match left_ref_idx {
        Some(r) if r > 0 => 1,
        _ => 0,
    };
    let b = match top_ref_idx {
        Some(r) if r > 0 => 1,
        _ => 0,
    };
    a + 2 * b
}

/// Encode ref_idx_l0 as truncated unary. Returns bins emitted.
pub fn encode_ref_idx_l0(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    ref_idx: u8,
    bin0_ctx_inc: usize,
    num_ref_idx_active_minus1: u8,
) -> usize {
    let cmax = num_ref_idx_active_minus1;
    let mut bins_emitted = 0;
    for i in 0..ref_idx {
        let ctx_inc = match i {
            0 => bin0_ctx_inc,
            1 => 4,
            _ => 5,
        };
        encoder.encode_bin(&mut contexts[REF_IDX_L0_CTX_OFFSET + ctx_inc], 1);
        bins_emitted += 1;
    }
    if ref_idx < cmax {
        let ctx_inc = match ref_idx {
            0 => bin0_ctx_inc,
            1 => 4,
            _ => 5,
        };
        encoder.encode_bin(&mut contexts[REF_IDX_L0_CTX_OFFSET + ctx_inc], 0);
        bins_emitted += 1;
    }
    bins_emitted
}

/// Decode ref_idx_l0. Returns (value, bins_consumed).
pub fn decode_ref_idx_l0(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    bin0_ctx_inc: usize,
    num_ref_idx_active_minus1: u8,
) -> (u8, usize) {
    let cmax = num_ref_idx_active_minus1;
    let mut count = 0u8;
    let mut bins_consumed = 0;
    loop {
        let ctx_inc = match count {
            0 => bin0_ctx_inc,
            1 => 4,
            _ => 5,
        };
        let bit = decoder.decode_bin(&mut contexts[REF_IDX_L0_CTX_OFFSET + ctx_inc]);
        bins_consumed += 1;
        if bit == 0 {
            return (count, bins_consumed);
        }
        count += 1;
        if count == cmax {
            // Truncated unary: at cmax ones, value is cmax (no
            // terminating zero).
            return (count, bins_consumed);
        }
    }
}

// --- H.264 syntax element: residual_block_cabac (luma 4x4 inter) ---
//
// Per ITU-T §9.3.3.1.1.9. This is the LARGEST CABAC syntax element
// — where the DCT residual coefficients of a macroblock live.
// Five sub-elements interleaved over a block:
//
//   1. coded_block_flag         — "any non-zero coefs?" (1 bin)
//                                  Caller provides; full neighbour-
//                                  CBF context logic out of scope.
//   2. significant_coeff_flag   — per-position "is this non-zero?"
//                                  ctxIdxOffset = 105 for luma 4x4
//                                  ctxIdxInc    = position in block
//   3. last_significant_coeff_  — per non-zero position "is this the
//      flag                       last?"  ctxIdxOffset = 166
//   4. coeff_abs_level_minus1   — magnitude-1, UEG0 binarisation
//                                  ctxIdxOffset = 227 (luma 4x4)
//                                  Up to 14 unary bins context-
//                                  coded; suffix bypass-coded
//                                  Exp-Golomb order 0.
//   5. coeff_sign_flag          — sign bit, bypass.
//
// This implementation handles ONE block type — luma 4x4 inter
// (ctxBlockCat = 2, 16 coefs). Other block types (luma 8x8, chroma
// DC/AC, I16x16 DC/AC) follow the same template with different
// ctxIdxOffsets per Table 9-42.

// ctxIdxOffset table per H.264 Table 9-42, one tuple per ctxBlockCat:
//   (sig_coeff_flag, last_significant_coeff_flag, coeff_abs_level_minus1, n_coefs)
//
//   cat   block type                     n_coefs   sig   last  abs_level
//   0   Intra16x16DCLevel                  16     105    166    227
//   1   Intra16x16ACLevel                  15     120    181    237
//   2   LumaLevel4x4                       16     134    195    247
//   3   ChromaDCLevel (YUV420)              4     149    210    257
//   4   ChromaACLevel                      15     152    213    266
//   5   LumaLevel8x8                       64     402    417    426
//
// (The luma 8x8 offsets sit in a separate range because 8x8 needs
// 63 sig contexts where 4x4/AC only need 14.)

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum CtxBlockCat {
    Intra16x16Dc,
    Intra16x16Ac,
    Luma4x4,
    ChromaDc,
    ChromaAc,
    Luma8x8,
}

#[derive(Copy, Clone)]
pub struct ResBlockSpec {
    pub n_coefs: usize,
    pub sig_off: usize,
    pub last_off: usize,
    pub abs_off: usize,
}

pub const RES_BLOCK_SPEC_INTRA16X16_DC: ResBlockSpec = ResBlockSpec {
    n_coefs: 16,
    sig_off: 105,
    last_off: 166,
    abs_off: 227,
};
pub const RES_BLOCK_SPEC_INTRA16X16_AC: ResBlockSpec = ResBlockSpec {
    n_coefs: 15,
    sig_off: 120,
    last_off: 181,
    abs_off: 237,
};
pub const RES_BLOCK_SPEC_LUMA_4X4: ResBlockSpec = ResBlockSpec {
    n_coefs: 16,
    sig_off: 134,
    last_off: 195,
    abs_off: 247,
};
pub const RES_BLOCK_SPEC_CHROMA_DC: ResBlockSpec = ResBlockSpec {
    n_coefs: 4,
    sig_off: 149,
    last_off: 210,
    abs_off: 257,
};
pub const RES_BLOCK_SPEC_CHROMA_AC: ResBlockSpec = ResBlockSpec {
    n_coefs: 15,
    sig_off: 152,
    last_off: 213,
    abs_off: 266,
};
pub const RES_BLOCK_SPEC_LUMA_8X8: ResBlockSpec = ResBlockSpec {
    n_coefs: 64,
    sig_off: 402,
    last_off: 417,
    abs_off: 426,
};

pub fn res_block_spec(cat: CtxBlockCat) -> ResBlockSpec {
    match cat {
        CtxBlockCat::Intra16x16Dc => RES_BLOCK_SPEC_INTRA16X16_DC,
        CtxBlockCat::Intra16x16Ac => RES_BLOCK_SPEC_INTRA16X16_AC,
        CtxBlockCat::Luma4x4 => RES_BLOCK_SPEC_LUMA_4X4,
        CtxBlockCat::ChromaDc => RES_BLOCK_SPEC_CHROMA_DC,
        CtxBlockCat::ChromaAc => RES_BLOCK_SPEC_CHROMA_AC,
        CtxBlockCat::Luma8x8 => RES_BLOCK_SPEC_LUMA_8X8,
    }
}

// Back-compat aliases used by the prior commits' tests + Python
// binding. These point at the original Intra16x16DC offsets (which
// the existing 4x4-named tests were inadvertently using; they still
// round-trip because both sides use the same constants).
pub const RES_SIG_COEF_CTX_OFFSET: usize = RES_BLOCK_SPEC_INTRA16X16_DC.sig_off;
pub const RES_LAST_COEF_CTX_OFFSET: usize = RES_BLOCK_SPEC_INTRA16X16_DC.last_off;
pub const RES_ABS_LEVEL_CTX_OFFSET: usize = RES_BLOCK_SPEC_INTRA16X16_DC.abs_off;
pub const RES_COEF_NUM_LUMA_4X4: usize = 16;

/// Encode one coeff_abs_level_minus1 value under UEG0 binarisation
/// per §9.3.2.7. `num_decod_abs_level_eq1` and `_gt1` are running
/// counts the caller maintains across the block — these select the
/// per-bin context.
pub fn encode_coeff_abs_level_minus1(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    ctx_offset: usize,
    value: u32,
    num_decod_abs_level_eq1: u32,
    num_decod_abs_level_gt1: u32,
) -> usize {
    // ctxIdxInc for bin 0 (per §9.3.3.1.1.9):
    //   if any prior level > 1: 0
    //   else:                    min(4, 1 + num_decod_abs_level_eq1)
    let ctx_inc0 = if num_decod_abs_level_gt1 > 0 {
        0
    } else {
        (1 + num_decod_abs_level_eq1).min(4)
    } as usize;
    // ctxIdxInc for bins 1+: 5 + min(4, num_decod_abs_level_gt1)
    let ctx_inc_rest = 5 + num_decod_abs_level_gt1.min(4) as usize;

    // Truncated unary prefix up to 14 ones.
    let unary_max = 14u32;
    let prefix_len = value.min(unary_max);
    let mut bins_emitted = 0;
    for i in 0..prefix_len {
        let ctx_inc = if i == 0 { ctx_inc0 } else { ctx_inc_rest };
        encoder.encode_bin(&mut contexts[ctx_offset + ctx_inc], 1);
        bins_emitted += 1;
    }
    if value < unary_max {
        // Terminating 0 bin.
        let ctx_inc = if prefix_len == 0 {
            ctx_inc0
        } else {
            ctx_inc_rest
        };
        encoder.encode_bin(&mut contexts[ctx_offset + ctx_inc], 0);
        bins_emitted += 1;
    } else {
        // value >= 14 — emit suffix as Exp-Golomb-0 in bypass, per
        // §9.3.2.3 + libavcodec/h264_cabac.c read pattern.
        // For value z:
        //   p = floor(log2(z + 1))  (the number of unary ones)
        //   emit p ones, a 0 terminator, then p bits of (z + 1)
        //   with the implicit-leading-1 stripped (i.e., low p bits
        //   of z + 1).
        let z = value - unary_max;
        let z_plus_1 = z + 1;
        let p = 31 - z_plus_1.leading_zeros();
        for _ in 0..p {
            encoder.encode_bypass(1);
            bins_emitted += 1;
        }
        encoder.encode_bypass(0);
        bins_emitted += 1;
        for i in (0..p).rev() {
            encoder.encode_bypass(((z_plus_1 >> i) & 1) as u8);
            bins_emitted += 1;
        }
    }
    bins_emitted
}

/// Decode one coeff_abs_level_minus1. Returns (value, bins_consumed).
pub fn decode_coeff_abs_level_minus1(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    ctx_offset: usize,
    num_decod_abs_level_eq1: u32,
    num_decod_abs_level_gt1: u32,
) -> (u32, usize) {
    let ctx_inc0 = if num_decod_abs_level_gt1 > 0 {
        0
    } else {
        (1 + num_decod_abs_level_eq1).min(4)
    } as usize;
    let ctx_inc_rest = 5 + num_decod_abs_level_gt1.min(4) as usize;

    let unary_max = 14u32;
    let mut prefix_len = 0u32;
    let mut bins_consumed = 0;
    loop {
        let ctx_inc = if prefix_len == 0 {
            ctx_inc0
        } else {
            ctx_inc_rest
        };
        let bit = decoder.decode_bin(&mut contexts[ctx_offset + ctx_inc]);
        bins_consumed += 1;
        if bit == 0 {
            return (prefix_len, bins_consumed);
        }
        prefix_len += 1;
        if prefix_len == unary_max {
            break;
        }
    }
    // Read Exp-Golomb-0 suffix in bypass — mirror of the encoder.
    // p = count of 1 bins before the 0 terminator. Then read p
    // bits and prepend the implicit leading 1 to recover z + 1.
    let mut p = 0u32;
    loop {
        let bit = decoder.decode_bypass();
        bins_consumed += 1;
        if bit == 0 {
            break;
        }
        p += 1;
        if p > 32 {
            panic!("coeff_abs_level UEG0 suffix overflow");
        }
    }
    let mut z_plus_1: u32 = 1; // implicit MSB
    for _ in 0..p {
        z_plus_1 = (z_plus_1 << 1) | (decoder.decode_bypass() as u32);
        bins_consumed += 1;
    }
    let z = z_plus_1 - 1;
    (unary_max + z, bins_consumed)
}

/// Encode a residual block of any ctxBlockCat. Caller passes the
/// block spec (offsets + n_coefs) + the coefficient slice (which
/// must have length spec.n_coefs). Returns bins emitted.
/// H.264 zigzag scan for 4×4 luma frame coding per §6.4.12.1.
/// Maps bitstream position (0..15) to raster index (row*4+col).
/// Verified against x264's ZIGZAG4_FRAME macro in common/dct.c.
const ZIGZAG_4X4: [usize; 16] = [0, 1, 4, 8, 5, 2, 3, 6, 9, 12, 13, 10, 7, 11, 14, 15];

/// Same for 2×2 chroma DC (linear, no actual zigzag — 4 entries).
const ZIGZAG_2X2: [usize; 4] = [0, 1, 2, 3];

/// Same zigzag but for the 15-AC-coef case (Intra16x16Ac /
/// ChromaAc) — the 15 positions are scan-order AC positions
/// (skipping DC), so the array index 0..14 maps to AC scan
/// position 1..15 in the original 4×4. We pre-compute the
/// remapped scan table by subtracting 1 from ZIGZAG_4X4[1..].
const ZIGZAG_4X4_AC: [usize; 15] = {
    let mut a = [0usize; 15];
    let mut i = 0;
    while i < 15 {
        a[i] = ZIGZAG_4X4[i + 1] - 1;
        i += 1;
    }
    a
};

/// Linear (raster) fallback for sizes we haven't wired the proper
/// scan for. The Luma8x8 zigzag is its own beast and isn't used in
/// the I_NxN MVP; we keep raster scan there for now so the existing
/// 8×8 round-trip tests still hold.
const LINEAR_64: [usize; 64] = {
    let mut a = [0usize; 64];
    let mut i = 0;
    while i < 64 {
        a[i] = i;
        i += 1;
    }
    a
};

/// Pick the right scan table from a block's n_coefs.
fn scan_table_for(n_coefs: usize) -> &'static [usize] {
    match n_coefs {
        16 => &ZIGZAG_4X4,
        15 => &ZIGZAG_4X4_AC, // AC-only, indices into 0..14
        4 => &ZIGZAG_2X2,
        64 => &LINEAR_64, // Luma 8×8 — not in MVP; raster for now
        _ => panic!("no scan table for {}-coef residual", n_coefs),
    }
}

pub fn encode_residual_block(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    spec: ResBlockSpec,
    coefs: &[i32],
) -> usize {
    assert_eq!(coefs.len(), spec.n_coefs);
    let n = spec.n_coefs;
    let scan = scan_table_for(n);
    // Locate last significant coefficient — in SCAN order.
    let mut last_sig = 0usize;
    let mut any_sig = false;
    for i in 0..n {
        if coefs[scan[i]] != 0 {
            last_sig = i;
            any_sig = true;
        }
    }
    if !any_sig {
        return 0; // caller's responsibility to gate via coded_block_flag
    }
    let mut bins_emitted = 0;

    let mut sig_scan_positions: Vec<usize> = Vec::new();
    for i in 0..n - 1 {
        if i > last_sig {
            break;
        }
        let is_sig = coefs[scan[i]] != 0;
        encoder.encode_bin(&mut contexts[spec.sig_off + i], if is_sig { 1 } else { 0 });
        bins_emitted += 1;
        if is_sig {
            sig_scan_positions.push(i);
            let is_last = i == last_sig;
            encoder.encode_bin(
                &mut contexts[spec.last_off + i],
                if is_last { 1 } else { 0 },
            );
            bins_emitted += 1;
            if is_last {
                break;
            }
        }
    }
    if last_sig == n - 1 {
        sig_scan_positions.push(n - 1);
    }

    let mut num_eq1 = 0u32;
    let mut num_gt1 = 0u32;
    for &scan_pos in sig_scan_positions.iter().rev() {
        let v = coefs[scan[scan_pos]];
        let abs_minus1 = (v.abs() - 1) as u32;
        bins_emitted += encode_coeff_abs_level_minus1(
            encoder,
            contexts,
            spec.abs_off,
            abs_minus1,
            num_eq1,
            num_gt1,
        );
        encoder.encode_bypass(if v < 0 { 1 } else { 0 });
        bins_emitted += 1;
        if v.abs() == 1 {
            num_eq1 += 1;
        } else {
            num_gt1 += 1;
        }
    }
    bins_emitted
}

/// Decode a residual block of any ctxBlockCat. Returns the
/// decoded coefficient vector + bins consumed.
pub fn decode_residual_block(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    spec: ResBlockSpec,
) -> (Vec<i32>, usize) {
    let n = spec.n_coefs;
    let scan = scan_table_for(n);
    let mut coefs = vec![0i32; n];
    let mut bins_consumed = 0;

    let mut sig_scan_positions: Vec<usize> = Vec::new();
    let mut hit_last = false;
    for i in 0..n - 1 {
        let sig = decoder.decode_bin(&mut contexts[spec.sig_off + i]);
        bins_consumed += 1;
        if sig == 1 {
            sig_scan_positions.push(i);
            let is_last = decoder.decode_bin(&mut contexts[spec.last_off + i]);
            bins_consumed += 1;
            if is_last == 1 {
                hit_last = true;
                break;
            }
        }
    }
    if !hit_last {
        sig_scan_positions.push(n - 1);
    }

    let mut num_eq1 = 0u32;
    let mut num_gt1 = 0u32;
    for &scan_pos in sig_scan_positions.iter().rev() {
        let (abs_minus1, bins) =
            decode_coeff_abs_level_minus1(decoder, contexts, spec.abs_off, num_eq1, num_gt1);
        bins_consumed += bins;
        let sign = decoder.decode_bypass();
        bins_consumed += 1;
        let mag = (abs_minus1 + 1) as i32;
        coefs[scan[scan_pos]] = if sign == 1 { -mag } else { mag };
        if mag == 1 {
            num_eq1 += 1;
        } else {
            num_gt1 += 1;
        }
    }
    (coefs, bins_consumed)
}

// --- H.264 syntax element: mvd (motion vector delta) --------------
//
// Per ITU-T §9.3.3.1.1.7 + Table 9-37. Each component (x or y) of
// a motion vector is encoded as a signed integer using UEG3
// binarisation (unary prefix up to 9, then bypass-coded Exp-Golomb
// suffix order 3). For prototype simplicity, we use the SAME
// running-count contexts shape as coeff_abs_level (the spec uses a
// slightly different scheme but the bin-cost shape is similar).
//
// Context offsets per Table 9-42:
//   mvd_l0/l1 X component: 40 / 47
//   mvd_l0/l1 Y component: 47 / 47
// (Caller passes the offset for the component they're emitting.)

pub const MVD_L0_X_CTX_OFFSET: usize = 40;
pub const MVD_L0_Y_CTX_OFFSET: usize = 47;
pub const MVD_UNARY_MAX: u32 = 9;

/// Encode one motion vector delta component (-2^15..+2^15-1).
/// UEG3 binarisation: unary prefix up to 9, then bypass Exp-Golomb-3
/// suffix, then bypass sign bit.
/// Spec ctxIdxInc for mvd binIdx i (i >= 1) per libavcodec's
/// decode_cabac_mb_mvd loop and §9.3.3.1.1.7:
///   binIdx 1: +3, binIdx 2: +4, binIdx 3: +5, binIdx 4+: +6
fn mvd_bin_inc(bin_idx: u32) -> usize {
    if bin_idx == 0 {
        0
    } else {
        (bin_idx as usize + 2).min(6)
    }
}

/// Derive ctxIdxInc for mvd binIdx 0 per §9.3.3.1.1.7 from the
/// neighbour absMvd sum (|left mvd| + |top mvd|, both capped per
/// spec; we just sum the raw magnitudes here — works for the
/// classification thresholds 3 and 33).
fn mvd_bin0_neighbour_inc(abs_left: i32, abs_top: i32) -> usize {
    let s = abs_left + abs_top;
    if s < 3 {
        0
    } else if s < 33 {
        1
    } else {
        2
    }
}

pub fn encode_mvd(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    ctx_offset: usize,
    mvd: i32,
) -> usize {
    encode_mvd_with_neighbours(encoder, contexts, ctx_offset, mvd, 0, 0)
}

/// Like `encode_mvd` but accepts the neighbour absMvd magnitudes
/// (in quarter-pel units) so binIdx 0's ctxIdxInc is spec-correct.
/// Pass 0, 0 for the first MB in a slice or when neighbours don't
/// supply MVD info.
pub fn encode_mvd_with_neighbours(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    ctx_offset: usize,
    mvd: i32,
    neighbour_abs_left: i32,
    neighbour_abs_top: i32,
) -> usize {
    let abs = mvd.unsigned_abs();
    let mut bins_emitted = 0;

    // Truncated unary prefix. Per spec Table 9-39 + libavcodec's
    // decode_cabac_mb_mvd: bin 0 uses ctx_offset+neighbour_inc;
    // subsequent bins step ctxbase by +3 then +1 per bin until it
    // caps at +6.
    let bin0_inc = mvd_bin0_neighbour_inc(neighbour_abs_left, neighbour_abs_top);
    let prefix_len = abs.min(MVD_UNARY_MAX);
    for i in 0..prefix_len {
        let inc = if i == 0 { bin0_inc } else { mvd_bin_inc(i) };
        encoder.encode_bin(&mut contexts[ctx_offset + inc], 1);
        bins_emitted += 1;
    }
    if abs < MVD_UNARY_MAX {
        let inc = if prefix_len == 0 {
            bin0_inc
        } else {
            mvd_bin_inc(prefix_len)
        };
        encoder.encode_bin(&mut contexts[ctx_offset + inc], 0);
        bins_emitted += 1;
    } else {
        // Bypass Exp-Golomb-3 suffix for abs - MVD_UNARY_MAX,
        // per H.264 spec EGkSuffix(z, k=3). Track v_local
        // (remainder) and k_local (current level) together.
        let mut v_local = abs - MVD_UNARY_MAX;
        let mut k_local = 3u32;
        while v_local >= (1u32 << k_local) {
            encoder.encode_bypass(1);
            bins_emitted += 1;
            v_local -= 1u32 << k_local;
            k_local += 1;
        }
        encoder.encode_bypass(0);
        bins_emitted += 1;
        for i in (0..k_local).rev() {
            encoder.encode_bypass(((v_local >> i) & 1) as u8);
            bins_emitted += 1;
        }
    }
    // Sign bit (only if nonzero).
    if abs > 0 {
        encoder.encode_bypass(if mvd < 0 { 1 } else { 0 });
        bins_emitted += 1;
    }
    bins_emitted
}

/// Decode one motion vector delta component. Returns (value, bins).
pub fn decode_mvd(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    ctx_offset: usize,
) -> (i32, usize) {
    let mut bins_consumed = 0;
    let mut prefix_len = 0u32;
    loop {
        let inc = mvd_bin_inc(prefix_len);
        let bit = decoder.decode_bin(&mut contexts[ctx_offset + inc]);
        bins_consumed += 1;
        if bit == 0 {
            break;
        }
        prefix_len += 1;
        if prefix_len == MVD_UNARY_MAX {
            break;
        }
    }
    let abs;
    if prefix_len < MVD_UNARY_MAX {
        abs = prefix_len;
    } else {
        // Mirror of encoder: count prefix ones (incrementing k_local
        // and accumulating offset), then read k_local suffix bits.
        let mut k_local = 3u32;
        let mut offset = 0u32;
        loop {
            let bit = decoder.decode_bypass();
            bins_consumed += 1;
            if bit == 0 {
                break;
            }
            offset += 1u32 << k_local;
            k_local += 1;
            if k_local > 32 {
                panic!("mvd UEG3 suffix overflow");
            }
        }
        let mut suffix = 0u32;
        for _ in 0..k_local {
            suffix = (suffix << 1) | (decoder.decode_bypass() as u32);
            bins_consumed += 1;
        }
        abs = MVD_UNARY_MAX + offset + suffix;
    }
    let value = if abs > 0 {
        let sign = decoder.decode_bypass();
        bins_consumed += 1;
        if sign == 1 {
            -(abs as i32)
        } else {
            abs as i32
        }
    } else {
        0
    };
    (value, bins_consumed)
}

/// Encode a 16-coefficient luma 4x4 residual block. Caller asserts
/// `coded_block_flag = 1` (i.e. at least one coef is non-zero) by
/// virtue of calling this; if all coefs are zero, don't call.
/// Returns the number of bins emitted.
pub fn encode_residual_4x4_luma(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    coefs: &[i32; 16],
) -> usize {
    // Locate last significant coefficient.
    let mut last_sig = 0usize;
    for (i, &c) in coefs.iter().enumerate() {
        if c != 0 {
            last_sig = i;
        }
    }
    let mut bins_emitted = 0;

    // Significance + last-flag map for positions 0..14.
    // (Position 15 is implicit — if reached, it's the last by definition.)
    let mut sig_positions: Vec<usize> = Vec::new();
    for i in 0..RES_COEF_NUM_LUMA_4X4 - 1 {
        if i > last_sig {
            break;
        }
        let is_sig = coefs[i] != 0;
        encoder.encode_bin(
            &mut contexts[RES_SIG_COEF_CTX_OFFSET + i],
            if is_sig { 1 } else { 0 },
        );
        bins_emitted += 1;
        if is_sig {
            sig_positions.push(i);
            let is_last = i == last_sig;
            encoder.encode_bin(
                &mut contexts[RES_LAST_COEF_CTX_OFFSET + i],
                if is_last { 1 } else { 0 },
            );
            bins_emitted += 1;
            if is_last {
                break;
            }
        }
    }
    // Position 15 — implicit if we get here (we didn't break above).
    if last_sig == RES_COEF_NUM_LUMA_4X4 - 1 {
        sig_positions.push(RES_COEF_NUM_LUMA_4X4 - 1);
    }

    // Now emit magnitudes (and sign bits) in REVERSE order — per
    // §9.3.3.1.1.9 the coefficients after the last significant
    // are emitted last-to-first.
    let mut num_eq1 = 0u32;
    let mut num_gt1 = 0u32;
    for &pos in sig_positions.iter().rev() {
        let v = coefs[pos];
        let abs_minus1 = (v.abs() - 1) as u32;
        bins_emitted += encode_coeff_abs_level_minus1(
            encoder,
            contexts,
            RES_ABS_LEVEL_CTX_OFFSET,
            abs_minus1,
            num_eq1,
            num_gt1,
        );
        encoder.encode_bypass(if v < 0 { 1 } else { 0 });
        bins_emitted += 1;
        // Update running counts for subsequent coefs' contexts.
        if v.abs() == 1 {
            num_eq1 += 1;
        } else {
            num_gt1 += 1;
        }
    }
    bins_emitted
}

/// Decode a 16-coefficient luma 4x4 residual block. Returns the
/// coefficient array (zero-padded for positions with no data).
pub fn decode_residual_4x4_luma(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
) -> ([i32; 16], usize) {
    let mut coefs = [0i32; 16];
    let mut bins_consumed = 0;

    // Walk the significance map.
    let mut sig_positions: Vec<usize> = Vec::new();
    let mut last_pos = 0usize;
    for i in 0..RES_COEF_NUM_LUMA_4X4 - 1 {
        let sig = decoder.decode_bin(&mut contexts[RES_SIG_COEF_CTX_OFFSET + i]);
        bins_consumed += 1;
        if sig == 1 {
            sig_positions.push(i);
            let is_last = decoder.decode_bin(&mut contexts[RES_LAST_COEF_CTX_OFFSET + i]);
            bins_consumed += 1;
            if is_last == 1 {
                last_pos = i;
                // Don't walk past the last sig coef.
                // sig_positions already records i; break.
                break;
            }
        }
    }
    // If we made it to position 14 without a last marker, position
    // 15 is implicit-significant.
    if sig_positions.last().map(|&p| p) != Some(last_pos) || sig_positions.is_empty() {
        // The loop fell through without hitting is_last == 1 — i.e.
        // last_pos is 15. Mark it sig.
        if !sig_positions.contains(&(RES_COEF_NUM_LUMA_4X4 - 1)) {
            sig_positions.push(RES_COEF_NUM_LUMA_4X4 - 1);
        }
    }

    // Decode magnitudes + signs in REVERSE order.
    let mut num_eq1 = 0u32;
    let mut num_gt1 = 0u32;
    for &pos in sig_positions.iter().rev() {
        let (abs_minus1, bins) = decode_coeff_abs_level_minus1(
            decoder,
            contexts,
            RES_ABS_LEVEL_CTX_OFFSET,
            num_eq1,
            num_gt1,
        );
        bins_consumed += bins;
        let sign = decoder.decode_bypass();
        bins_consumed += 1;
        let mag = (abs_minus1 + 1) as i32;
        coefs[pos] = if sign == 1 { -mag } else { mag };
        if mag == 1 {
            num_eq1 += 1;
        } else {
            num_gt1 += 1;
        }
    }
    (coefs, bins_consumed)
}

/// Initialise the full 1024-context array for a slice at the given
/// QP, slice type, and cabac_init_idc (only used for P/B; ignored
/// for I). Returns the populated Vec.
/// Return the (m, n) initialisation pairs for the chosen
/// slice-type / init_idc table — used by the bin-tracer to
/// mirror our initial state without copy-pasting the 1024-entry
/// constant.
pub fn init_table_mn(slice_type: CabacSliceType, cabac_init_idc: u8) -> &'static [[i8; 2]; 1024] {
    match slice_type {
        CabacSliceType::I => &CABAC_CONTEXT_INIT_I,
        CabacSliceType::P | CabacSliceType::B => match cabac_init_idc {
            0 => &CABAC_CONTEXT_INIT_PB_0,
            1 => &CABAC_CONTEXT_INIT_PB_1,
            _ => &CABAC_CONTEXT_INIT_PB_2,
        },
    }
}

pub fn init_contexts(
    slice_type: CabacSliceType,
    cabac_init_idc: u8,
    slice_qp: i32,
) -> Vec<CabacCtx> {
    let table: &[[i8; 2]; 1024] = match slice_type {
        CabacSliceType::I => &CABAC_CONTEXT_INIT_I,
        CabacSliceType::P | CabacSliceType::B => match cabac_init_idc {
            0 => &CABAC_CONTEXT_INIT_PB_0,
            1 => &CABAC_CONTEXT_INIT_PB_1,
            _ => &CABAC_CONTEXT_INIT_PB_2,
        },
    };
    let mut out = Vec::with_capacity(1024);
    for &[m, n] in table.iter() {
        out.push(CabacCtx::init_from_mn(m, n, slice_qp));
    }
    out
}

/// Decoder state. `code_i_range` and `code_i_offset` evolve as each
/// bin is consumed; `bit_pos` is the next stream bit to read on
/// renormalisation. The encoder state mirrors this.
#[derive(Clone, Debug)]
pub struct CabacDecoder {
    pub code_i_range: u32,
    pub code_i_offset: u32,
    pub bit_pos: u64,
    pub buffer: Vec<u8>,
}

impl CabacDecoder {
    /// Initialise from `buffer` starting at `bit_pos`. Loads the
    /// first 9 bits into code_i_offset per §9.3.1.2.
    pub fn new(buffer: Vec<u8>, bit_pos: u64) -> Self {
        let mut s = CabacDecoder {
            code_i_range: 0x1FE,
            code_i_offset: 0,
            bit_pos,
            buffer,
        };
        for _ in 0..9 {
            s.code_i_offset = (s.code_i_offset << 1) | s.read_bit() as u32;
        }
        s
    }

    #[inline(always)]
    fn read_bit(&mut self) -> u8 {
        // SAFETY-turned-checked: bit_pos can legitimately run past the
        // encoded payload's end. CABAC decode is driven by the bitstream
        // SYNTAX (cbp / coded_block_flag / ...), not by a byte-count the
        // decoder tracks independently — a caller decoding against a
        // stream that ran out of coded bits (e.g. the last renorm reads
        // of a slice, or a genuinely truncated/malformed input) is a
        // real, reachable path, not just a caller bug. Per the spec's
        // own convention (rbsp_trailing_bits / cabac_zero_word padding),
        // bits read past the end of the actual payload read as 0 rather
        // than being undefined. `get` (checked) replaces `get_unchecked`
        // here; the bounds check this reintroduces is the same one the
        // `byte_idx + 1 < len` guard below already pays for b1.
        let byte = self
            .buffer
            .get((self.bit_pos >> 3) as usize)
            .copied()
            .unwrap_or(0);
        let bit = (byte >> (7 - (self.bit_pos & 7))) & 1;
        self.bit_pos += 1;
        bit
    }

    /// Read up to 8 bits in one operation. Used by the renorm fast
    /// path — instead of looping one bit at a time, compute the
    /// shift count from `code_i_range.leading_zeros()` and pull all
    /// the bits in a single byte-spanning extract.
    #[inline(always)]
    fn read_bits_up_to_8(&mut self, n: u32) -> u32 {
        if n == 0 {
            return 0;
        }
        let bp = self.bit_pos;
        let byte_idx = (bp >> 3) as usize;
        let bit_off = (bp & 7) as u32;
        // Read two bytes; the slice up to 8 bits may span a byte
        // boundary. `byte_idx` itself can be at or past `buffer.len()`
        // (see the SAFETY-turned-checked note on `read_bit` above: a
        // decoder can legitimately renormalise past the last coded
        // bit), so both bytes fall back to 0 when out of range — same
        // treatment b1 already had, now applied uniformly.
        let b0 = self.buffer.get(byte_idx).copied().unwrap_or(0) as u32;
        let b1 = if byte_idx + 1 < self.buffer.len() {
            (unsafe { *self.buffer.get_unchecked(byte_idx + 1) }) as u32
        } else {
            0
        };
        let combined = (b0 << 8) | b1;
        // The high bit of `combined` is bit 0 of the next byte... no,
        // wait. b0 is the FIRST byte; bit 0 of b0 is the MSB. So
        // combined has b0's MSB at position 15.
        let shift = 16 - n - bit_off;
        let result = (combined >> shift) & ((1u32 << n) - 1);
        self.bit_pos += n as u64;
        result
    }

    /// Renormalise: shift `code_i_range` left until ≥ 256.
    /// BASELINE (un-tuned) version — single-bit loop. Used for
    /// measuring the hand-tune speedup; the optimised version sits
    /// below behind the `cabac_tuned` cfg flag.
    #[cfg(feature = "cabac_baseline")]
    fn renorm(&mut self) {
        while self.code_i_range < 256 {
            self.code_i_range <<= 1;
            self.code_i_offset = (self.code_i_offset << 1) | self.read_bit() as u32;
        }
    }

    /// Renormalise — hand-tuned: leading_zeros for one-shot shift,
    /// fast-path early-out for the common no-renorm case.
    #[cfg(not(feature = "cabac_baseline"))]
    #[inline(always)]
    fn renorm(&mut self) {
        if self.code_i_range >= 256 {
            return;
        }
        let k = self.code_i_range.leading_zeros() - 23;
        self.code_i_range <<= k;
        let bits = self.read_bits_up_to_8(k);
        self.code_i_offset = (self.code_i_offset << k) | bits;
    }

    /// Decode one bin under context `ctx`, mutating ctx. Returns the
    /// decoded bit (0/1). §9.3.3.2.1.
    #[inline(always)]
    pub fn decode_bin(&mut self, ctx: &mut CabacCtx) -> u8 {
        let p_state = ctx.p_state_idx as usize;
        let q_range_idx = ((self.code_i_range >> 6) & 3) as usize;
        // SAFETY: p_state_idx is guaranteed 0..63 by the spec and
        // tracked by both encoder/decoder; q_range_idx is masked to
        // 0..3 by the bitmask above.
        let range_lps = unsafe {
            *RANGE_TAB_LPS
                .get_unchecked(p_state)
                .get_unchecked(q_range_idx)
        } as u32;
        self.code_i_range -= range_lps;

        let bin_val;
        if self.code_i_offset >= self.code_i_range {
            bin_val = 1 - ctx.val_mps;
            self.code_i_offset -= self.code_i_range;
            self.code_i_range = range_lps;
            if p_state == 0 {
                ctx.val_mps = 1 - ctx.val_mps;
            }
            ctx.p_state_idx = unsafe { *TRANS_IDX_LPS.get_unchecked(p_state) };
        } else {
            bin_val = ctx.val_mps;
            ctx.p_state_idx = unsafe { *TRANS_IDX_MPS.get_unchecked(p_state) };
        }
        self.renorm();
        bin_val
    }

    /// Decode one bypass bin (1/2 probability, no context). §9.3.3.2.3.
    #[inline(always)]
    pub fn decode_bypass(&mut self) -> u8 {
        self.code_i_offset = (self.code_i_offset << 1) | self.read_bit() as u32;
        if self.code_i_offset >= self.code_i_range {
            self.code_i_offset -= self.code_i_range;
            1
        } else {
            0
        }
    }

    /// Decode the terminate flag (end-of-slice). §9.3.3.2.4.
    pub fn decode_terminate(&mut self) -> u8 {
        self.code_i_range -= 2;
        if self.code_i_offset >= self.code_i_range {
            1
        } else {
            self.renorm();
            0
        }
    }

    /// I_PCM support (§9.3.1 + §7.3.5): after the I_PCM mb_type (whose
    /// final bin is the terminate bin that returned 1), the arithmetic
    /// engine is suspended. The spec's read pointer is
    /// `byte_offset = bit_pos / 8` (the engine's `bit_pos` already sits
    /// on a byte boundary at this point because the terminate path does
    /// NOT renormalise — it leaves bit_pos where the 9-bit lookahead
    /// last loaded, which is byte-aligned after the alignment one-bit
    /// of the slice + an integral number of decode steps... NOT
    /// guaranteed in general). To be exact we explicitly drop the
    /// 7 lookahead bits: the next raw byte begins at the byte that
    /// contains `bit_pos - 7` rounded up. We expose the raw reader so
    /// the caller can pull `pcm_sample_*` bytes, then `reinit_after_pcm`
    /// restarts the engine per §9.3.1.2.
    ///
    /// Returns the byte offset where PCM samples begin.
    pub fn pcm_byte_align(&mut self) -> usize {
        // The arithmetic decoder holds 9 bits of lookahead in
        // code_i_offset; the genuine consumed position is bit_pos - 9.
        // Per §9.3.1, after a terminate==1 the read pointer is set to
        // the byte AFTER the last byte that contributed bits actually
        // used, i.e. round (bit_pos - 7) up to a byte boundary. In x264
        // streams the slice's cabac_alignment + integral MBs leave this
        // on a byte boundary; we compute it explicitly to be safe.
        let consumed = self.bit_pos.saturating_sub(7);
        let byte = ((consumed + 7) / 8) as usize;
        self.bit_pos = (byte as u64) * 8;
        byte
    }

    /// Read `n` raw bytes starting at the current byte-aligned bit_pos.
    pub fn read_pcm_bytes(&mut self, n: usize) -> Vec<u8> {
        debug_assert_eq!(self.bit_pos & 7, 0, "PCM read must be byte-aligned");
        let start = (self.bit_pos >> 3) as usize;
        let out = self.buffer[start..(start + n).min(self.buffer.len())].to_vec();
        self.bit_pos += (out.len() as u64) * 8;
        out
    }

    /// Re-initialise the arithmetic engine after an I_PCM macroblock
    /// (§9.3.1.2): reload code_i_range = 0x1FE and the 9-bit
    /// code_i_offset from the (now byte-aligned) bitstream.
    pub fn reinit_after_pcm(&mut self) {
        self.code_i_range = 0x1FE;
        self.code_i_offset = 0;
        for _ in 0..9 {
            self.code_i_offset = (self.code_i_offset << 1) | self.read_bit() as u32;
        }
    }
}

/// Encoder — mirror of CabacDecoder. Implements §9.3.4.
///
/// Bit emission uses a u64 accumulator that flushes 8 bytes at a
/// time via `extend_from_slice(&u64.to_be_bytes())`. The
/// `bits_outstanding` burst (runs of identical bits) is emitted via
/// `put_bits(b, n)` which ORs an n-bit mask in one operation rather
/// than calling put_bit n times.
#[derive(Clone, Debug)]
pub struct CabacEncoder {
    pub code_i_low: u32,
    pub code_i_range: u32,
    pub bits_outstanding: u32,
    pub first_bit_emitted: bool,
    pub buffer: Vec<u8>,
    /// MSB-first accumulator. The k-th emitted bit goes at
    /// position (63 - k). When `bit_count` reaches 64, the
    /// accumulator is flushed as 8 big-endian bytes.
    bit_buf: u64,
    bit_count: u32,
    /// Total bits emitted (for inter-encoder accounting).
    pub bit_pos: u64,
}

impl CabacEncoder {
    pub fn new() -> Self {
        // Pre-reserve a chunk of output buffer to avoid Vec growth
        // reallocs on the hot path. 256 KB covers most realistic
        // slice sizes; oversize doesn't cost (lazy commit).
        CabacEncoder {
            code_i_low: 0,
            code_i_range: 0x1FE,
            bits_outstanding: 0,
            first_bit_emitted: false,
            buffer: Vec::with_capacity(256 * 1024),
            bit_buf: 0,
            bit_count: 0,
            bit_pos: 0,
        }
    }

    /// Append a single bit MSB-first into the accumulator.
    #[inline(always)]
    fn put_bit(&mut self, bit: u8) {
        // OR the bit at position (63 - bit_count). Branch-free.
        self.bit_buf |= ((bit as u64) & 1) << (63 - self.bit_count);
        self.bit_count += 1;
        self.bit_pos += 1;
        if self.bit_count == 64 {
            self.flush_acc();
        }
    }

    /// Emit `n` consecutive identical bits in one operation. Used
    /// for the `bits_outstanding` burst path — runs can be 1-30
    /// bits long for typical content.
    #[inline(always)]
    fn put_bits(&mut self, bit: u8, mut n: u32) {
        while n > 0 {
            let space = 64 - self.bit_count;
            let take = n.min(space);
            if bit != 0 {
                let mask = (((1u64 << take) - 1).wrapping_shl(0)) << (64 - self.bit_count - take);
                self.bit_buf |= mask;
            }
            self.bit_count += take;
            self.bit_pos += take as u64;
            if self.bit_count == 64 {
                self.flush_acc();
            }
            n -= take;
        }
    }

    /// Flush the full 64-bit accumulator as 8 big-endian bytes.
    /// Called when `bit_count == 64`.
    #[inline(always)]
    fn flush_acc(&mut self) {
        self.buffer.extend_from_slice(&self.bit_buf.to_be_bytes());
        self.bit_buf = 0;
        self.bit_count = 0;
    }

    /// Emit a final bit B followed by `bits_outstanding` copies of
    /// (1-B). §9.3.4.4 PutBit().
    #[inline(always)]
    fn put_bit_with_outstanding(&mut self, b: u8) {
        if self.first_bit_emitted {
            self.put_bit(b);
        } else {
            self.first_bit_emitted = true;
        }
        if self.bits_outstanding > 0 {
            // Batch the run of (1-b) bits in a single accumulator op.
            self.put_bits(1 - b, self.bits_outstanding);
            self.bits_outstanding = 0;
        }
    }

    /// Renormalisation for the encoder per §9.3.4.4 RenormE.
    /// Hand-tuned: early-out when no renorm needed (the dominant
    /// case for MPS-stays-on bins).
    #[inline(always)]
    fn renorm_e(&mut self) {
        // Fast path: most MPS bins leave range ≥ 256 → no work.
        if self.code_i_range >= 256 {
            return;
        }
        while self.code_i_range < 256 {
            if self.code_i_low < 256 {
                self.put_bit_with_outstanding(0);
            } else if self.code_i_low >= 512 {
                self.code_i_low -= 512;
                self.put_bit_with_outstanding(1);
            } else {
                self.code_i_low -= 256;
                self.bits_outstanding += 1;
            }
            self.code_i_range <<= 1;
            self.code_i_low <<= 1;
        }
    }

    /// Encode one bin under context `ctx`. §9.3.4.2.
    #[inline(always)]
    pub fn encode_bin(&mut self, ctx: &mut CabacCtx, bin_val: u8) {
        let p_state = ctx.p_state_idx as usize;
        let q_range_idx = ((self.code_i_range >> 6) & 3) as usize;
        // SAFETY: p_state_idx ∈ 0..63 by spec; q_range_idx masked to 0..3.
        let range_lps = unsafe {
            *RANGE_TAB_LPS
                .get_unchecked(p_state)
                .get_unchecked(q_range_idx)
        } as u32;
        self.code_i_range -= range_lps;

        if bin_val != ctx.val_mps {
            self.code_i_low += self.code_i_range;
            self.code_i_range = range_lps;
            if p_state == 0 {
                ctx.val_mps = 1 - ctx.val_mps;
            }
            ctx.p_state_idx = unsafe { *TRANS_IDX_LPS.get_unchecked(p_state) };
        } else {
            ctx.p_state_idx = unsafe { *TRANS_IDX_MPS.get_unchecked(p_state) };
        }
        self.renorm_e();
    }

    /// Encode bypass bin. §9.3.4.3.
    pub fn encode_bypass(&mut self, bin_val: u8) {
        self.code_i_low <<= 1;
        if bin_val != 0 {
            self.code_i_low += self.code_i_range;
        }
        if self.code_i_low >= 1024 {
            self.put_bit_with_outstanding(1);
            self.code_i_low -= 1024;
        } else if self.code_i_low < 512 {
            self.put_bit_with_outstanding(0);
        } else {
            self.code_i_low -= 512;
            self.bits_outstanding += 1;
        }
    }

    /// Encode a binary decision before termination — §9.3.4.4.
    /// Used for end_of_slice_flag and i_pcm_flag. binVal=1 signals
    /// "terminating" (next op is flush); binVal=0 just shrinks
    /// the range by 2 and renormalises.
    pub fn encode_terminate(&mut self, bin_val: u8) {
        self.code_i_range -= 2;
        if bin_val == 1 {
            // codILow advances over the LPS region (= post-decrement
            // codIRange); codIRange shrinks to 2 for the flush. Spec
            // §9.3.4.4 says NO RenormE here — flush handles it.
            self.code_i_low += self.code_i_range;
            self.code_i_range = 2;
        } else {
            // Only the binVal=0 path renormalises (codIRange may have
            // dropped below 256 after the -=2).
            self.renorm_e();
        }
    }

    /// Flush the encoder — emit the terminate bit + drain outstanding.
    /// §9.3.4.5 EncodeFlush.
    pub fn finish(&mut self) {
        self.code_i_range = 2;
        self.renorm_e();
        // Emit two bits: the 9th most-significant of code_i_low, then
        // an alignment bit 1.
        self.put_bit_with_outstanding(((self.code_i_low >> 9) & 1) as u8);
        self.put_bit(((self.code_i_low >> 8) & 1) as u8);
        self.put_bit(1);
        // Spill any partial accumulator as whole bytes (zero-pad the
        // trailing bits to the next byte boundary). The CABAC payload
        // bit length is bit_pos; the buffer length always covers it.
        if self.bit_count > 0 {
            // Pack the held bits into bytes, MSB-first. Round up to
            // the next byte boundary.
            let byte_count = (self.bit_count + 7) / 8;
            // Top `bit_count` bits of bit_buf hold the payload. After
            // shifting right (64 - 8*byte_count), the byte_count bytes
            // sit at the LSB end; to_be_bytes gives us the bytes in
            // emission order — pick the LAST `byte_count`.
            let shifted = self.bit_buf >> (64 - 8 * byte_count);
            // shifted has byte_count bytes of payload at LSB end.
            // Emit them MSB-first.
            for i in (0..byte_count).rev() {
                self.buffer.push(((shifted >> (i * 8)) & 0xFF) as u8);
            }
            self.bit_buf = 0;
            self.bit_count = 0;
        }
    }
}

impl Default for CabacEncoder {
    fn default() -> Self {
        CabacEncoder::new()
    }
}

/// Encode one P_L0_16x16 macroblock with motion vector (mvd_x,
/// mvd_y) per ITU-T §7.3.5.1. Assumes:
///   - num_ref_idx_l0_active_minus1 = 0 (one ref frame; ref_idx
///     not emitted)
///   - cbp_luma + cbp_chroma drive residual emission (CBF-gated
///     per block, scan-zigzag, same as I_NxN walker)
///   - mb_qp_delta = 0
/// Caller passes pre-quantised luma residual coefficients
/// in `mb.luma_4x4` (already DCT'd and quantised vs the reference).
pub fn encode_p_l0_16x16_mb(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    mb: &INxnMbInputs, // re-using the I_NxN struct shape
    mvd_x: i32,
    mvd_y: i32,
    left_was_p_skip: Option<bool>,
    top_was_p_skip: Option<bool>,
    left: Option<&MbNeighbourState>,
    top: Option<&MbNeighbourState>,
) -> (usize, [bool; 16]) {
    let mut bins = 0;

    // 1. mb_type = P_L0_16x16. Per libavcodec h264_cabac.c
    //    decode_cabac_mb_type_p_slice, P/SP-slice non-intra mb_type
    //    always emits 3 bins:
    //       bin 0 @ ctx 14:  0 = P-type (1 = intra-in-P)
    //       bin 1 @ ctx 15:  0 = 16x16 or 8x8 sub-MB
    //                        1 = 16x8 or 8x16
    //       bin 2 @ ctx 16 (when bin 1=0): 0 = 16x16, 1 = 8x8
    //       bin 2 @ ctx 17 (when bin 1=1): bin value flips meaning per
    //                                      libavcodec's "2 - bin2".
    //    For P_L0_16x16: "0 0 0" at ctx 14, 15, 16.
    let _ = (left_was_p_skip, top_was_p_skip);
    encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET], 0);
    encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 1], 0);
    encoder.encode_bin(&mut contexts[P_MB_TYPE_CTX_OFFSET + 2], 0);
    bins += 3;

    // 2. mb_pred: ref_idx not emitted (1 ref); just mvd_l0_x, mvd_l0_y.
    //    Neighbour absMvd derives bin 0 ctxIdxInc per §9.3.3.1.1.7.
    let (left_abs_x, left_abs_y) = left.map(|l| (l.abs_mvd_x, l.abs_mvd_y)).unwrap_or((0, 0));
    let (top_abs_x, top_abs_y) = top.map(|t| (t.abs_mvd_x, t.abs_mvd_y)).unwrap_or((0, 0));
    bins += encode_mvd_with_neighbours(
        encoder,
        contexts,
        MVD_L0_X_CTX_OFFSET,
        mvd_x,
        left_abs_x,
        top_abs_x,
    );
    bins += encode_mvd_with_neighbours(
        encoder,
        contexts,
        MVD_L0_Y_CTX_OFFSET,
        mvd_y,
        left_abs_y,
        top_abs_y,
    );

    // 3. CBP luma + chroma (same as I_NxN walker).
    bins += encode_cbp_luma(
        encoder,
        contexts,
        mb.cbp_luma,
        left.map(|l| l.cbp_luma).unwrap_or(0xF),
        top.map(|t| t.cbp_luma).unwrap_or(0xF),
    );
    bins += encode_cbp_chroma(
        encoder,
        contexts,
        mb.cbp_chroma,
        left.map(|l| l.cbp_chroma).unwrap_or(0),
        top.map(|t| t.cbp_chroma).unwrap_or(0),
    );

    // 4. mb_qp_delta if any CBP set
    let any_cbp = mb.cbp_luma != 0 || mb.cbp_chroma != 0;
    if any_cbp {
        let prev_was_zero = left.map(|l| l.mb_qp_delta_was_zero).unwrap_or(true);
        bins += encode_mb_qp_delta(encoder, contexts, mb.mb_qp_delta, prev_was_zero);
    }

    // 5. Luma 4×4 residual blocks — same scan + CBF gating as I_NxN.
    let luma_blocks_in_8x8: [[usize; 4]; 4] =
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]];
    let mut this_mb_cbf = [false; 16];
    for (i_8x8, sub_blocks) in luma_blocks_in_8x8.iter().enumerate() {
        if (mb.cbp_luma >> i_8x8) & 1 == 0 {
            continue;
        }
        for &block_idx in sub_blocks {
            let has_coefs = mb.luma_4x4[block_idx].iter().any(|&c| c != 0);
            let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
            // Same unavailable-as-coded convention as I_NxN. P-MBs
            // are NOT intra so the spec says unavailable → cond=0
            // (treated as uncoded). Pass false explicitly.
            let left_cbf = if bc > 0 {
                Some(this_mb_cbf[RC_TO_BLOCK_IDX[br][bc - 1]])
            } else {
                left.map(|l| l.luma_cbf[RC_TO_BLOCK_IDX[br][3]])
            };
            let top_cbf = if br > 0 {
                Some(this_mb_cbf[RC_TO_BLOCK_IDX[br - 1][bc]])
            } else {
                top.map(|t| t.luma_cbf[RC_TO_BLOCK_IDX[3][bc]])
            };
            bins += encode_coded_block_flag(
                encoder,
                contexts,
                CtxBlockCat::Luma4x4,
                has_coefs,
                left_cbf,
                top_cbf,
            );
            this_mb_cbf[block_idx] = has_coefs;
            if has_coefs {
                bins += encode_residual_block(
                    encoder,
                    contexts,
                    RES_BLOCK_SPEC_LUMA_4X4,
                    &mb.luma_4x4[block_idx],
                );
            }
        }
    }

    // 6. Chroma DC (Cb then Cr) if cbp_chroma >= 1. CBF-gated.
    //    Mirrors the I-walker's chroma section (§7.3.5.3.2 +
    //    §9.3.3.1.1.9 ctxBlockCat ChromaDc / ChromaAc).
    let mut this_chroma_dc_cbf_cb = false;
    let mut this_chroma_dc_cbf_cr = false;
    let mut this_chroma_ac_cbf_cb = [false; 4];
    let mut this_chroma_ac_cbf_cr = [false; 4];
    if mb.cbp_chroma >= 1 {
        let cb_has = mb.chroma_dc_cb.iter().any(|&c| c != 0);
        let left_cb_dc = left.map(|l| l.chroma_dc_cbf_cb);
        let top_cb_dc = top.map(|t| t.chroma_dc_cbf_cb);
        bins += encode_coded_block_flag(
            encoder,
            contexts,
            CtxBlockCat::ChromaDc,
            cb_has,
            left_cb_dc,
            top_cb_dc,
        );
        this_chroma_dc_cbf_cb = cb_has;
        if cb_has {
            bins += encode_residual_block(
                encoder,
                contexts,
                RES_BLOCK_SPEC_CHROMA_DC,
                &mb.chroma_dc_cb,
            );
        }
        let cr_has = mb.chroma_dc_cr.iter().any(|&c| c != 0);
        let left_cr_dc = left.map(|l| l.chroma_dc_cbf_cr);
        let top_cr_dc = top.map(|t| t.chroma_dc_cbf_cr);
        bins += encode_coded_block_flag(
            encoder,
            contexts,
            CtxBlockCat::ChromaDc,
            cr_has,
            left_cr_dc,
            top_cr_dc,
        );
        this_chroma_dc_cbf_cr = cr_has;
        if cr_has {
            bins += encode_residual_block(
                encoder,
                contexts,
                RES_BLOCK_SPEC_CHROMA_DC,
                &mb.chroma_dc_cr,
            );
        }
    }
    // 7. Chroma AC if cbp_chroma == 2 (4 Cb blocks + 4 Cr blocks of
    //    15 coefs each). Each 4×4 sub-block's CBF context consults
    //    same-position neighbour CBFs across MB boundaries.
    //    Chroma 4×4 grid layout per MB (block_idx 0..3):
    //       block 0 (top-left), 1 (top-right)
    //       block 2 (bottom-left), 3 (bottom-right)
    if mb.cbp_chroma == 2 {
        // Cb plane AC
        for blk_idx in 0..4 {
            let row = blk_idx / 2;
            let col = blk_idx % 2;
            let blk = &mb.chroma_ac_cb[blk_idx];
            let has = blk.iter().any(|&c| c != 0);
            // In-MB neighbours are within this_chroma_ac_cbf_cb; cross-MB
            // neighbours from `left` (right column → idx 1, 3) and `top`
            // (bottom row → idx 2, 3).
            let left_cbf = if col > 0 {
                Some(this_chroma_ac_cbf_cb[row * 2 + (col - 1)])
            } else {
                left.map(|l| l.chroma_ac_cbf_cb[row * 2 + 1])
            };
            let top_cbf = if row > 0 {
                Some(this_chroma_ac_cbf_cb[(row - 1) * 2 + col])
            } else {
                top.map(|t| t.chroma_ac_cbf_cb[2 + col])
            };
            bins += encode_coded_block_flag(
                encoder,
                contexts,
                CtxBlockCat::ChromaAc,
                has,
                left_cbf,
                top_cbf,
            );
            this_chroma_ac_cbf_cb[blk_idx] = has;
            if has {
                bins += encode_residual_block(encoder, contexts, RES_BLOCK_SPEC_CHROMA_AC, blk);
            }
        }
        // Cr plane AC — same shape
        for blk_idx in 0..4 {
            let row = blk_idx / 2;
            let col = blk_idx % 2;
            let blk = &mb.chroma_ac_cr[blk_idx];
            let has = blk.iter().any(|&c| c != 0);
            let left_cbf = if col > 0 {
                Some(this_chroma_ac_cbf_cr[row * 2 + (col - 1)])
            } else {
                left.map(|l| l.chroma_ac_cbf_cr[row * 2 + 1])
            };
            let top_cbf = if row > 0 {
                Some(this_chroma_ac_cbf_cr[(row - 1) * 2 + col])
            } else {
                top.map(|t| t.chroma_ac_cbf_cr[2 + col])
            };
            bins += encode_coded_block_flag(
                encoder,
                contexts,
                CtxBlockCat::ChromaAc,
                has,
                left_cbf,
                top_cbf,
            );
            this_chroma_ac_cbf_cr[blk_idx] = has;
            if has {
                bins += encode_residual_block(encoder, contexts, RES_BLOCK_SPEC_CHROMA_AC, blk);
            }
        }
    }
    // Capture chroma CBFs as out-params via a side-channel on
    // the MbNeighbourState built by the slice walker; the closure
    // is in encode_p_slice_from_mb_luma. Return them through a
    // local field on the implicit out-tuple — but the current
    // signature only returns luma_cbf. We attach them via a
    // module-private mutable static? No — instead, the caller can
    // recompute them from `mb` by checking nonzero-ness, since the
    // outputs we wrote ARE just the CBFs we computed above.
    let _ = (
        this_chroma_dc_cbf_cb,
        this_chroma_dc_cbf_cr,
        this_chroma_ac_cbf_cb,
        this_chroma_ac_cbf_cr,
    );

    (bins, this_mb_cbf)
}

/// Optional chroma residual coefficients for a P-slice. When
/// `cbp_chroma_list` has any nonzero entry, the corresponding
/// chroma_dc / chroma_ac arrays must be populated for that MB.
/// All arrays are LAID OUT FLAT in MB order:
///   chroma_dc_cb[i*4..i*4+4]       — 4 DC coefs for MB i, Cb plane
///   chroma_dc_cr[i*4..i*4+4]       — 4 DC coefs for MB i, Cr plane
///   chroma_ac_cb[i*60..i*60+60]    — 4×15 AC coefs for MB i, Cb plane
///                                    (4 sub-blocks × 15 AC positions)
///   chroma_ac_cr[i*60..i*60+60]    — same for Cr
pub struct PSliceChromaResiduals<'a> {
    pub cbp_chroma_list: &'a [u8],
    pub chroma_dc_cb: &'a [i32],
    pub chroma_dc_cr: &'a [i32],
    pub chroma_ac_cb: &'a [i32],
    pub chroma_ac_cr: &'a [i32],
}

/// Encode an entire P-slice from a flat mb_luma buffer + a
/// flat mb_skip mask. Each MB is either:
///   - skipped (mb_skip_flag = 1) → decoder derives MV from
///     neighbours, no residual data
///   - non-skipped P_L0_16x16 with mvd = (0, 0) (so the
///     reference at the same position is used)
///
/// `chroma` is optional; when None, every MB is encoded with
/// cbp_chroma = 0 (luma-only — backward compatible).
pub fn encode_p_slice_from_mb_luma(
    mb_luma: &[i32],
    cbp_luma_list: &[u8],
    mb_skip_list: &[bool],
    mb_width: usize,
    mb_height: usize,
    cabac_init_idc: u8,
    slice_qp: i32,
    chroma: Option<&PSliceChromaResiduals>,
    // Per-MB motion vector differences in quarter-luma-pel units
    // (mvd_x, mvd_y). When None, all MBs encode mvd = (0, 0).
    // MVDs are differences from the spec's median predictor;
    // caller must compute them appropriately.
    mvd: Option<(&[i16], &[i16])>,
) -> Vec<u8> {
    let n_mbs = mb_width * mb_height;
    assert_eq!(mb_luma.len(), n_mbs * 256);
    assert_eq!(cbp_luma_list.len(), n_mbs);
    assert_eq!(mb_skip_list.len(), n_mbs);
    if let Some(ch) = chroma {
        assert_eq!(ch.cbp_chroma_list.len(), n_mbs);
        assert_eq!(ch.chroma_dc_cb.len(), n_mbs * 4);
        assert_eq!(ch.chroma_dc_cr.len(), n_mbs * 4);
        assert_eq!(ch.chroma_ac_cb.len(), n_mbs * 60);
        assert_eq!(ch.chroma_ac_cr.len(), n_mbs * 60);
    }
    if let Some((mx, my)) = mvd {
        assert_eq!(mx.len(), n_mbs);
        assert_eq!(my.len(), n_mbs);
    }

    let mut contexts = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
    let mut enc = CabacEncoder::new();
    // Track per-MB neighbour state for skip + mb_type-is-P + CBF etc.
    #[derive(Clone, Copy)]
    struct PNeighbour {
        skipped: bool,
        is_p_l0: bool,
        ns: MbNeighbourState,
    }
    let mut grid: Vec<Vec<Option<PNeighbour>>> = vec![vec![None; mb_width]; mb_height];

    let skip_ctx_offset = mb_skip_flag_ctx_offset(CabacSliceType::P).unwrap();

    for r in 0..mb_height {
        for c in 0..mb_width {
            let i = r * mb_width + c;
            let left = if c > 0 { grid[r][c - 1] } else { None };
            let top = if r > 0 { grid[r - 1][c] } else { None };

            // mb_skip_flag bin
            let skip_inc = mb_skip_flag_ctx_idx_inc(
                left.map(|l| if l.skipped { 1 } else { 0 }),
                top.map(|t| if t.skipped { 1 } else { 0 }),
            );
            let skip_ctx = skip_ctx_offset + skip_inc;
            let mb_skip = mb_skip_list[i];
            enc.encode_bin(&mut contexts[skip_ctx], if mb_skip { 1 } else { 0 });

            let luma_cbf;
            let is_p_l0;
            let cbp_luma;
            let cbp_chroma_this;
            let this_mvd_x_emitted;
            let this_mvd_y_emitted;
            if mb_skip {
                // Skipped: no further bins for this MB. P_Skip implies
                // mvd = (0, 0) for neighbour-context purposes.
                luma_cbf = [false; 16];
                is_p_l0 = true;
                cbp_luma = 0;
                cbp_chroma_this = 0;
                this_mvd_x_emitted = 0;
                this_mvd_y_emitted = 0;
            } else {
                // Non-skipped P_L0_16x16
                let mut mb_in = INxnMbInputs::default();
                let base = i * 256;
                for blk in 0..16 {
                    for k in 0..16 {
                        mb_in.luma_4x4[blk][k] = mb_luma[base + blk * 16 + k];
                    }
                }
                mb_in.cbp_luma = cbp_luma_list[i];
                if let Some(ch) = chroma {
                    mb_in.cbp_chroma = ch.cbp_chroma_list[i];
                    if mb_in.cbp_chroma >= 1 {
                        for k in 0..4 {
                            mb_in.chroma_dc_cb[k] = ch.chroma_dc_cb[i * 4 + k];
                            mb_in.chroma_dc_cr[k] = ch.chroma_dc_cr[i * 4 + k];
                        }
                    }
                    if mb_in.cbp_chroma == 2 {
                        for b in 0..4 {
                            for k in 0..15 {
                                mb_in.chroma_ac_cb[b][k] = ch.chroma_ac_cb[i * 60 + b * 15 + k];
                                mb_in.chroma_ac_cr[b][k] = ch.chroma_ac_cr[i * 60 + b * 15 + k];
                            }
                        }
                    }
                } else {
                    mb_in.cbp_chroma = 0;
                }
                mb_in.mb_qp_delta = 0;

                let left_ns = left.map(|l| l.ns);
                let top_ns = top.map(|t| t.ns);
                let (this_mvd_x, this_mvd_y) = match mvd {
                    Some((mx, my)) => (mx[i] as i32, my[i] as i32),
                    None => (0, 0),
                };
                let (_, cbf) = encode_p_l0_16x16_mb(
                    &mut enc,
                    &mut contexts,
                    &mb_in,
                    this_mvd_x,
                    this_mvd_y,
                    left.map(|l| l.skipped),
                    top.map(|t| t.skipped),
                    left_ns.as_ref(),
                    top_ns.as_ref(),
                );
                luma_cbf = cbf;
                is_p_l0 = true;
                cbp_luma = mb_in.cbp_luma;
                cbp_chroma_this = mb_in.cbp_chroma;
                this_mvd_x_emitted = this_mvd_x;
                this_mvd_y_emitted = this_mvd_y;
            }

            // end_of_slice_flag — emitted after every MB in CABAC
            // mode, including skipped ones (per §7.3.4 slice_data
            // loop structure).
            let is_last = r == mb_height - 1 && c == mb_width - 1;
            enc.encode_terminate(if is_last { 1 } else { 0 });

            // Compute the chroma CBFs we wrote for this MB so the
            // next MB's CBF context derivation matches what we
            // encoded (and what the decoder will compute).
            let (cdc_cb, cdc_cr, cac_cb, cac_cr) = if mb_skip || cbp_chroma_this == 0 {
                (false, false, [false; 4], [false; 4])
            } else {
                let mb_in_base = i;
                let dc_cb = if let Some(ch) = chroma {
                    ch.chroma_dc_cb[mb_in_base * 4..mb_in_base * 4 + 4]
                        .iter()
                        .any(|&v| v != 0)
                } else {
                    false
                };
                let dc_cr = if let Some(ch) = chroma {
                    ch.chroma_dc_cr[mb_in_base * 4..mb_in_base * 4 + 4]
                        .iter()
                        .any(|&v| v != 0)
                } else {
                    false
                };
                let mut ac_cb = [false; 4];
                let mut ac_cr = [false; 4];
                if cbp_chroma_this == 2 {
                    if let Some(ch) = chroma {
                        for b in 0..4 {
                            ac_cb[b] = ch.chroma_ac_cb
                                [mb_in_base * 60 + b * 15..mb_in_base * 60 + (b + 1) * 15]
                                .iter()
                                .any(|&v| v != 0);
                            ac_cr[b] = ch.chroma_ac_cr
                                [mb_in_base * 60 + b * 15..mb_in_base * 60 + (b + 1) * 15]
                                .iter()
                                .any(|&v| v != 0);
                        }
                    }
                }
                (dc_cb, dc_cr, ac_cb, ac_cr)
            };
            grid[r][c] = Some(PNeighbour {
                skipped: mb_skip,
                is_p_l0,
                ns: MbNeighbourState {
                    mb_type_is_i_nxn: Some(false),
                    cbp_luma,
                    cbp_chroma: cbp_chroma_this,
                    intra_chroma_mode: None,
                    mb_qp_delta_was_zero: true,
                    luma_cbf,
                    luma_dc_cbf: false,
                    chroma_dc_cbf_cb: cdc_cb,
                    chroma_dc_cbf_cr: cdc_cr,
                    chroma_ac_cbf_cb: cac_cb,
                    chroma_ac_cbf_cr: cac_cr,
                    abs_mvd_x: this_mvd_x_emitted.abs(),
                    abs_mvd_y: this_mvd_y_emitted.abs(),
                },
            });
        }
    }
    enc.finish();
    enc.buffer
}

/// Encode a P-slice picture as N independent slices in parallel.
/// Each slice is a contiguous range of MB rows. Slice boundaries
/// break the CABAC context chain (each slice initialises contexts
/// independently per §9.3.1.2) — i.e. neighbour state inside the
/// slice is preserved, but cross-slice neighbour state is dropped.
///
/// Returns `Vec<(first_mb_in_slice, payload)>`, one entry per slice,
/// in raster (row) order. Caller emits each as its own slice NAL
/// with the appropriate slice header.
///
/// Parallelism: one std::thread per slice. With N cores ≥ N slices
/// this is a near-linear speedup over the single-slice encoder.
pub fn encode_p_slice_multi(
    mb_luma: &[i32],
    cbp_luma_list: &[u8],
    mb_skip_list: &[bool],
    mb_width: usize,
    mb_height: usize,
    cabac_init_idc: u8,
    slice_qp: i32,
    chroma: Option<&PSliceChromaResiduals>,
    mvd: Option<(&[i16], &[i16])>,
    n_slices: usize,
) -> Vec<(usize, Vec<u8>)> {
    let n_mbs = mb_width * mb_height;
    assert_eq!(mb_luma.len(), n_mbs * 256);
    assert_eq!(cbp_luma_list.len(), n_mbs);
    assert_eq!(mb_skip_list.len(), n_mbs);
    assert!(n_slices >= 1);
    assert!(
        n_slices <= mb_height,
        "can't split {} MB rows into {} slices",
        mb_height,
        n_slices
    );

    // Divide MB rows roughly evenly across N slices.
    let rows_per_slice = (mb_height + n_slices - 1) / n_slices;
    let mut ranges: Vec<(usize, usize)> = Vec::with_capacity(n_slices);
    let mut row = 0;
    while row < mb_height {
        let last = (row + rows_per_slice).min(mb_height);
        ranges.push((row, last));
        row = last;
    }

    // Pre-slice all input arrays so each thread gets a self-contained
    // sub-slice. Cheaper than per-thread index arithmetic and lets us
    // call encode_p_slice_from_mb_luma unchanged.
    struct Slice<'a> {
        first_mb: usize,
        mb_h: usize,
        mb_luma: &'a [i32],
        cbp: &'a [u8],
        skip: &'a [bool],
        chroma: Option<PSliceChromaResiduals<'a>>,
        mvd_x: Option<&'a [i16]>,
        mvd_y: Option<&'a [i16]>,
    }
    let mut slices: Vec<Slice> = Vec::with_capacity(n_slices);
    for &(first_row, last_row) in &ranges {
        let mb_h_slice = last_row - first_row;
        let mb_start = first_row * mb_width;
        let mb_end = last_row * mb_width;
        let lo_l = mb_start * 256;
        let hi_l = mb_end * 256;
        let chroma_sub = chroma.map(|ch| PSliceChromaResiduals {
            cbp_chroma_list: &ch.cbp_chroma_list[mb_start..mb_end],
            chroma_dc_cb: &ch.chroma_dc_cb[mb_start * 4..mb_end * 4],
            chroma_dc_cr: &ch.chroma_dc_cr[mb_start * 4..mb_end * 4],
            chroma_ac_cb: &ch.chroma_ac_cb[mb_start * 60..mb_end * 60],
            chroma_ac_cr: &ch.chroma_ac_cr[mb_start * 60..mb_end * 60],
        });
        let (mvd_x_sub, mvd_y_sub) = match mvd {
            Some((x, y)) => (Some(&x[mb_start..mb_end]), Some(&y[mb_start..mb_end])),
            None => (None, None),
        };
        slices.push(Slice {
            first_mb: mb_start,
            mb_h: mb_h_slice,
            mb_luma: &mb_luma[lo_l..hi_l],
            cbp: &cbp_luma_list[mb_start..mb_end],
            skip: &mb_skip_list[mb_start..mb_end],
            chroma: chroma_sub,
            mvd_x: mvd_x_sub,
            mvd_y: mvd_y_sub,
        });
    }

    std::thread::scope(|scope| {
        let handles: Vec<_> = slices
            .iter()
            .map(|sl| {
                let mw = mb_width;
                let mh = sl.mb_h;
                let mvd_pair = match (sl.mvd_x, sl.mvd_y) {
                    (Some(x), Some(y)) => Some((x, y)),
                    _ => None,
                };
                let chroma_ref = sl.chroma.as_ref();
                let first_mb = sl.first_mb;
                let payload_handle = scope.spawn(move || {
                    encode_p_slice_from_mb_luma(
                        sl.mb_luma,
                        sl.cbp,
                        sl.skip,
                        mw,
                        mh,
                        cabac_init_idc,
                        slice_qp,
                        chroma_ref,
                        mvd_pair,
                    )
                });
                (first_mb, payload_handle)
            })
            .collect();
        handles
            .into_iter()
            .map(|(first_mb, h)| (first_mb, h.join().unwrap()))
            .collect()
    })
}

/// Encode a full I-slice from a flat mb_luma buffer (16 quantised
/// coefficients per 4×4 block × 16 blocks per MB × N MBs). Used
/// both by the Python binding and by the in-process ladder
/// transcoder. Returns the raw CABAC payload (no NAL wrapping).
pub fn encode_i_slice_from_mb_luma(
    mb_luma: &[i32],
    cbp_luma_list: &[u8],
    mb_width: usize,
    mb_height: usize,
    cabac_init_idc: u8,
    slice_qp: i32,
) -> Vec<u8> {
    let n_mbs = mb_width * mb_height;
    assert_eq!(mb_luma.len(), n_mbs * 256);
    assert_eq!(cbp_luma_list.len(), n_mbs);
    let mut contexts = init_contexts(CabacSliceType::I, cabac_init_idc, slice_qp);
    let mut enc = CabacEncoder::new();
    let mut grid: Vec<Vec<Option<MbNeighbourState>>> = vec![vec![None; mb_width]; mb_height];

    for r in 0..mb_height {
        for c in 0..mb_width {
            let i = r * mb_width + c;
            let mut mb = INxnMbInputs::default();
            let base = i * 256;
            for blk in 0..16 {
                for k in 0..16 {
                    mb.luma_4x4[blk][k] = mb_luma[base + blk * 16 + k];
                }
            }
            mb.cbp_luma = cbp_luma_list[i];
            mb.cbp_chroma = 0;
            mb.intra_chroma_pred_mode = 0;
            mb.mb_qp_delta = 0;
            let left = if c > 0 { grid[r][c - 1].as_ref() } else { None };
            let top = if r > 0 { grid[r - 1][c].as_ref() } else { None };
            let (_, luma_cbf) = encode_i_nxn_mb(&mut enc, &mut contexts, &mb, left, top);
            let is_last = r == mb_height - 1 && c == mb_width - 1;
            enc.encode_terminate(if is_last { 1 } else { 0 });
            grid[r][c] = Some(MbNeighbourState {
                mb_type_is_i_nxn: Some(true),
                cbp_luma: mb.cbp_luma,
                cbp_chroma: mb.cbp_chroma,
                intra_chroma_mode: Some(mb.intra_chroma_pred_mode),
                mb_qp_delta_was_zero: mb.mb_qp_delta == 0,
                luma_cbf,
                // I-slice walker doesn't currently encode chroma
                // residuals (cbp_chroma=0), so chroma CBFs stay false.
                luma_dc_cbf: false,
                chroma_dc_cbf_cb: false,
                chroma_dc_cbf_cr: false,
                chroma_ac_cbf_cb: [false; 4],
                chroma_ac_cbf_cr: [false; 4],
                abs_mvd_x: 0,
                abs_mvd_y: 0,
            });
        }
    }
    enc.finish();
    enc.buffer
}

// --- H.264 MB layer walker (I-slice, I_NxN only) --------------------
//
// Per ITU-T §7.3.5.1, an intra-coded I_NxN macroblock is the
// sequence of CABAC-encoded syntax elements:
//
//   1.  mb_type                 (I_NxN, 1 bin)
//   2.  transform_8x8_mode_flag (if PPS allows + this is intra4x4 —
//                                we set 0; not coded here)
//   3.  16 × (prev_intra4x4_pred_mode_flag
//             [+ rem_intra4x4_pred_mode if flag==0])
//   4.  intra_chroma_pred_mode
//   5.  coded_block_pattern_luma + coded_block_pattern_chroma
//   6.  mb_qp_delta             (only if any CBP bit is set)
//   7.  16 × luma 4×4 residual block (only those whose CBP-luma
//                                     8×8-block bit is set)
//   8.  4 × chroma DC (Cb + Cr) if cbp_chroma >= 1
//   9.  8 × chroma AC (Cb + Cr, 4 each) if cbp_chroma == 2
//
// This walker uses I_NxN with prev_intra4x4_pred_mode_flag=1 for
// all 16 sub-blocks — the "use the spec's predicted intra mode"
// path. For an I-only output stream with all-DC neighbours (or
// unavailable neighbours), the spec-predicted mode is DC (mode 2)
// per §8.3.1.1 (`predIntra4x4PredMode = min(predN_A, predN_B)`,
// with DC as the default for unavailable neighbours), so the
// effective intra4x4 mode for all sub-blocks is DC. No
// rem_intra4x4_pred_mode bins needed.

/// Inputs needed to encode one I_NxN macroblock. All quantised
/// coefficients are in raster order within their 4×4 block;
/// `luma_blocks` is ordered per H.264 4×4 luma scan (block 0 =
/// top-left 4×4, then raster left-to-right, top-to-bottom within
/// each 8×8, and 8×8 blocks in raster order — see Table 6-4).
#[derive(Clone, Debug)]
pub struct INxnMbInputs {
    /// 16 luma 4×4 residual blocks. Zeroed entries mean "no
    /// residual" and are skipped per CBP.
    pub luma_4x4: [[i32; 16]; 16],
    /// 4-bit CBP luma per §7.4.5.1 (one bit per 8×8 luma block).
    pub cbp_luma: u8,
    /// CBP chroma value 0/1/2 per §7.4.5.1.
    pub cbp_chroma: u8,
    /// Chroma DC coefficients: 4 for Cb (2×2 grid) + 4 for Cr.
    /// Ignored if cbp_chroma == 0.
    pub chroma_dc_cb: [i32; 4],
    pub chroma_dc_cr: [i32; 4],
    /// Chroma AC: 4 blocks of 15 coefs each, Cb then Cr. Ignored
    /// unless cbp_chroma == 2.
    pub chroma_ac_cb: [[i32; 15]; 4],
    pub chroma_ac_cr: [[i32; 15]; 4],
    /// Per-MB QP modifier. 0 = "same as slice QP".
    pub mb_qp_delta: i32,
    /// intra_chroma_pred_mode: 0=DC, 1=Horizontal, 2=Vertical, 3=Plane.
    pub intra_chroma_pred_mode: u8,
}

impl Default for INxnMbInputs {
    fn default() -> Self {
        INxnMbInputs {
            luma_4x4: [[0i32; 16]; 16],
            cbp_luma: 0,
            cbp_chroma: 0,
            chroma_dc_cb: [0; 4],
            chroma_dc_cr: [0; 4],
            chroma_ac_cb: [[0i32; 15]; 4],
            chroma_ac_cr: [[0i32; 15]; 4],
            mb_qp_delta: 0,
            intra_chroma_pred_mode: 0,
        }
    }
}

/// Neighbour state required for context selection across a single
/// MB encode/decode. Caller maintains this between MBs in raster
/// scan.
#[derive(Clone, Copy, Debug, Default)]
pub struct MbNeighbourState {
    pub mb_type_is_i_nxn: Option<bool>,
    pub cbp_luma: u8,
    pub cbp_chroma: u8,
    pub intra_chroma_mode: Option<u8>,
    pub mb_qp_delta_was_zero: bool,
    /// CBF (coded_block_flag) for each of the 16 luma 4×4 blocks,
    /// indexed by block_idx (per Figure 6-12 Z-scan ordering).
    /// Needed by the NEXT MB to compute the right CBF ctxIdxInc
    /// for blocks on its top/left edge.
    pub luma_cbf: [bool; 16],
    /// I_16x16 luma DC coded_block_flag — consulted by the next
    /// I_16x16 MB's DC CBF context (§9.3.3.1.1.9, ctxBlockCat=0).
    pub luma_dc_cbf: bool,
    /// CBFs for the single chroma DC 2×2 block per component.
    /// Per §9.3.3.1.1.9 the right/below MB consults the neighbour's
    /// same-component DC CBF to derive the ctxIdxInc.
    pub chroma_dc_cbf_cb: bool,
    pub chroma_dc_cbf_cr: bool,
    /// CBFs for the four chroma AC 4×4 sub-blocks per component
    /// (indexed by chroma 4×4 raster position 0..3).
    pub chroma_ac_cbf_cb: [bool; 4],
    pub chroma_ac_cbf_cr: [bool; 4],
    /// Absolute MVD magnitudes (quarter-luma-pel units, capped at
    /// the spec's classification thresholds — predMvd uses |A|+|B|
    /// thresholded at 3 and 33 per §9.3.3.1.1.7). Used by the next
    /// MB to derive the mvd binIdx-0 ctxIdxInc.
    pub abs_mvd_x: i32,
    pub abs_mvd_y: i32,
}

/// Spec §6.4.3 / Figure 6-12: 4×4 luma block index (0..15) to its
/// (row, col) position within the 4×4 grid of an MB.
const BLOCK_IDX_TO_RC: [(usize, usize); 16] = [
    (0, 0),
    (0, 1),
    (1, 0),
    (1, 1),
    (0, 2),
    (0, 3),
    (1, 2),
    (1, 3),
    (2, 0),
    (2, 1),
    (3, 0),
    (3, 1),
    (2, 2),
    (2, 3),
    (3, 2),
    (3, 3),
];

/// Inverse mapping: (row, col) → block_idx. Built from
/// `BLOCK_IDX_TO_RC` by hand to keep the table const.
const RC_TO_BLOCK_IDX: [[usize; 4]; 4] =
    [[0, 1, 4, 5], [2, 3, 6, 7], [8, 9, 12, 13], [10, 11, 14, 15]];

/// Encode one I_NxN macroblock per §7.3.5.1. `left` and `top` are
/// the neighbour states for context derivation; if a neighbour is
/// out of slice / unavailable, pass `MbNeighbourState::default()`
/// AND set `*_avail` to false.
/// Encode one I_NxN MB. Returns (bins_emitted, luma_cbf_grid)
/// where the grid is the CBF of each of the 16 luma 4×4 sub-blocks
/// — the caller stores this on the next MB's MbNeighbourState so
/// raster-scan neighbours can read its right edge / bottom edge.
pub fn encode_i_nxn_mb(
    encoder: &mut CabacEncoder,
    contexts: &mut [CabacCtx],
    mb: &INxnMbInputs,
    left: Option<&MbNeighbourState>,
    top: Option<&MbNeighbourState>,
) -> (usize, [bool; 16]) {
    let mut bins = 0;

    // 1. mb_type = I_NxN
    bins += encode_i_mb_type_i_nxn(
        encoder,
        contexts,
        left.and_then(|l| l.mb_type_is_i_nxn),
        top.and_then(|t| t.mb_type_is_i_nxn),
    );

    // 3. Intra prediction modes: 16 × prev_intra4x4_pred_mode_flag = 1
    //    (no rem_intra4x4_pred_mode bins because the flag = 1 path).
    for _ in 0..16 {
        bins += encode_prev_intra4x4_flag(encoder, contexts, true);
    }

    // 4. intra_chroma_pred_mode
    bins += encode_intra_chroma_pred_mode(
        encoder,
        contexts,
        mb.intra_chroma_pred_mode,
        left.and_then(|l| l.intra_chroma_mode),
        top.and_then(|t| t.intra_chroma_mode),
    );

    // 5. CBP luma + chroma. For unavailable neighbours, the spec
    // wants condTermFlag = 0 (treat as "fully coded"); we encode
    // that by passing 0xF (all 4 8×8 luma bits set) so the bit-
    // inversion in ctxIdxInc yields the right thing. Chroma uses
    // a non-bit value (0/1/2) but its inc function already maps
    // 0 → condTermFlag = 0 which IS the unavailable behaviour.
    bins += encode_cbp_luma(
        encoder,
        contexts,
        mb.cbp_luma,
        left.map(|l| l.cbp_luma).unwrap_or(0xF),
        top.map(|t| t.cbp_luma).unwrap_or(0xF),
    );
    bins += encode_cbp_chroma(
        encoder,
        contexts,
        mb.cbp_chroma,
        left.map(|l| l.cbp_chroma).unwrap_or(0),
        top.map(|t| t.cbp_chroma).unwrap_or(0),
    );

    // 6. mb_qp_delta if any CBP bit set
    let any_cbp = mb.cbp_luma != 0 || mb.cbp_chroma != 0;
    if any_cbp {
        let prev_was_zero = left.map(|l| l.mb_qp_delta_was_zero).unwrap_or(true);
        bins += encode_mb_qp_delta(encoder, contexts, mb.mb_qp_delta, prev_was_zero);
    }

    // 7. Luma 4×4 residual blocks. Per H.264 Table 6-2 the 16 4×4
    //    blocks group into 4 8×8 luma blocks with this mapping:
    //      8×8 block 0 → 4×4 blocks 0, 1, 2, 3
    //      8×8 block 1 → 4×4 blocks 4, 5, 6, 7
    //      8×8 block 2 → 4×4 blocks 8, 9, 10, 11
    //      8×8 block 3 → 4×4 blocks 12, 13, 14, 15
    //    Within each 8×8 block they're scanned in their natural
    //    index order, which IS the §6.4.3 Z-scan within the MB.
    let luma_blocks_in_8x8: [[usize; 4]; 4] =
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]];
    // Track CBF for each of the 16 4×4 sub-blocks as we encode,
    // so subsequent blocks can derive their CBF ctxIdxInc from
    // in-MB neighbours per §9.3.3.1.1.9.
    let mut this_mb_cbf = [false; 16];
    for (i_8x8, sub_blocks) in luma_blocks_in_8x8.iter().enumerate() {
        if (mb.cbp_luma >> i_8x8) & 1 == 0 {
            continue;
        }
        for &block_idx in sub_blocks {
            let has_coefs = mb.luma_4x4[block_idx].iter().any(|&c| c != 0);
            let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
            // CBF left neighbour: same MB at (br, bc-1) if in-MB,
            //   else from left MB at (br, 3). When unavailable in an
            //   intra MB, spec §9.3.3.1.1.9 says condTermFlag = 1
            //   (treat as coded) — we encode this by returning
            //   Some(true). Libavcodec uses 0x7CF for unavailable
            //   intra-MB neighbour CBPs which sets bits 6-10 (the
            //   CBF region) all to 1 — same convention.
            let left_cbf = if bc > 0 {
                Some(this_mb_cbf[RC_TO_BLOCK_IDX[br][bc - 1]])
            } else {
                Some(
                    left.map(|l| l.luma_cbf[RC_TO_BLOCK_IDX[br][3]])
                        .unwrap_or(true),
                )
            };
            let top_cbf = if br > 0 {
                Some(this_mb_cbf[RC_TO_BLOCK_IDX[br - 1][bc]])
            } else {
                Some(
                    top.map(|t| t.luma_cbf[RC_TO_BLOCK_IDX[3][bc]])
                        .unwrap_or(true),
                )
            };
            bins += encode_coded_block_flag(
                encoder,
                contexts,
                CtxBlockCat::Luma4x4,
                has_coefs,
                left_cbf,
                top_cbf,
            );
            this_mb_cbf[block_idx] = has_coefs;
            if has_coefs {
                bins += encode_residual_block(
                    encoder,
                    contexts,
                    RES_BLOCK_SPEC_LUMA_4X4,
                    &mb.luma_4x4[block_idx],
                );
            }
        }
    }
    // Capture our CBF grid so the NEXT MB (right or below) can
    // use our right-edge column / bottom-edge row as its left/top
    // neighbour CBFs. Caller stores this on the returned
    // MbNeighbourState.

    // 8. Chroma DC (Cb then Cr) if cbp_chroma >= 1. CBF-gated.
    if mb.cbp_chroma >= 1 {
        let cb_has = mb.chroma_dc_cb.iter().any(|&c| c != 0);
        bins +=
            encode_coded_block_flag(encoder, contexts, CtxBlockCat::ChromaDc, cb_has, None, None);
        if cb_has {
            bins += encode_residual_block(
                encoder,
                contexts,
                RES_BLOCK_SPEC_CHROMA_DC,
                &mb.chroma_dc_cb,
            );
        }
        let cr_has = mb.chroma_dc_cr.iter().any(|&c| c != 0);
        bins +=
            encode_coded_block_flag(encoder, contexts, CtxBlockCat::ChromaDc, cr_has, None, None);
        if cr_has {
            bins += encode_residual_block(
                encoder,
                contexts,
                RES_BLOCK_SPEC_CHROMA_DC,
                &mb.chroma_dc_cr,
            );
        }
    }

    // 9. Chroma AC if cbp_chroma == 2 (8 blocks of 15 coefs each).
    if mb.cbp_chroma == 2 {
        for blk in &mb.chroma_ac_cb {
            let has = blk.iter().any(|&c| c != 0);
            bins +=
                encode_coded_block_flag(encoder, contexts, CtxBlockCat::ChromaAc, has, None, None);
            if has {
                bins += encode_residual_block(encoder, contexts, RES_BLOCK_SPEC_CHROMA_AC, blk);
            }
        }
        for blk in &mb.chroma_ac_cr {
            let has = blk.iter().any(|&c| c != 0);
            bins +=
                encode_coded_block_flag(encoder, contexts, CtxBlockCat::ChromaAc, has, None, None);
            if has {
                bins += encode_residual_block(encoder, contexts, RES_BLOCK_SPEC_CHROMA_AC, blk);
            }
        }
    }

    (bins, this_mb_cbf)
}

/// Decode the same MB layout. Returns (inputs, bins_consumed,
/// luma_cbf_grid) — same CBF surface as the encoder so callers
/// can thread state between MBs.
pub fn decode_i_nxn_mb(
    decoder: &mut CabacDecoder,
    contexts: &mut [CabacCtx],
    left: Option<&MbNeighbourState>,
    top: Option<&MbNeighbourState>,
) -> (INxnMbInputs, usize, [bool; 16]) {
    let mut mb = INxnMbInputs::default();
    let mut bins = 0;

    // 1. Verify mb_type is I_NxN (caller's responsibility to call
    //    only when they've already established this).
    let (is_i_nxn, b) = decode_i_mb_type_is_i_nxn(
        decoder,
        contexts,
        left.and_then(|l| l.mb_type_is_i_nxn),
        top.and_then(|t| t.mb_type_is_i_nxn),
    );
    bins += b;
    assert!(is_i_nxn, "decode_i_nxn_mb called on non-I_NxN MB");

    // 3. 16 × prev_intra4x4_flag.
    for _ in 0..16 {
        let (flag, b) = decode_prev_intra4x4_flag(decoder, contexts);
        bins += b;
        assert!(flag, "encoder only emits flag=1; decoder saw flag=0");
        // If we ever support flag=0, decode rem here.
    }

    // 4. intra_chroma_pred_mode
    let (mode, b) = decode_intra_chroma_pred_mode(
        decoder,
        contexts,
        left.and_then(|l| l.intra_chroma_mode),
        top.and_then(|t| t.intra_chroma_mode),
    );
    bins += b;
    mb.intra_chroma_pred_mode = mode;

    // 5. CBP — unavailable neighbours pass 0xF for luma (so the
    // bit-inversion in ctxIdxInc gives condTermFlag=0 per spec).
    let (cbp_l, b) = decode_cbp_luma(
        decoder,
        contexts,
        left.map(|l| l.cbp_luma).unwrap_or(0xF),
        top.map(|t| t.cbp_luma).unwrap_or(0xF),
    );
    bins += b;
    mb.cbp_luma = cbp_l;
    let (cbp_c, b) = decode_cbp_chroma(
        decoder,
        contexts,
        left.map(|l| l.cbp_chroma).unwrap_or(0),
        top.map(|t| t.cbp_chroma).unwrap_or(0),
    );
    bins += b;
    mb.cbp_chroma = cbp_c;

    // 6. mb_qp_delta
    let any_cbp = mb.cbp_luma != 0 || mb.cbp_chroma != 0;
    if any_cbp {
        let prev_was_zero = left.map(|l| l.mb_qp_delta_was_zero).unwrap_or(true);
        let (d, b) = decode_mb_qp_delta(decoder, contexts, prev_was_zero);
        bins += b;
        mb.mb_qp_delta = d;
    }

    // 7. Luma residuals — spec ordering [0,1,2,3]/[4,5,6,7]/...
    //    with per-block CBF context from in-MB + cross-MB neighbours.
    let luma_blocks_in_8x8: [[usize; 4]; 4] =
        [[0, 1, 2, 3], [4, 5, 6, 7], [8, 9, 10, 11], [12, 13, 14, 15]];
    let mut this_mb_cbf = [false; 16];
    for (i_8x8, sub_blocks) in luma_blocks_in_8x8.iter().enumerate() {
        if (mb.cbp_luma >> i_8x8) & 1 == 0 {
            continue;
        }
        for &block_idx in sub_blocks {
            let (br, bc) = BLOCK_IDX_TO_RC[block_idx];
            // Same unavailable-as-coded convention as the encoder.
            let left_cbf = if bc > 0 {
                Some(this_mb_cbf[RC_TO_BLOCK_IDX[br][bc - 1]])
            } else {
                Some(
                    left.map(|l| l.luma_cbf[RC_TO_BLOCK_IDX[br][3]])
                        .unwrap_or(true),
                )
            };
            let top_cbf = if br > 0 {
                Some(this_mb_cbf[RC_TO_BLOCK_IDX[br - 1][bc]])
            } else {
                Some(
                    top.map(|t| t.luma_cbf[RC_TO_BLOCK_IDX[3][bc]])
                        .unwrap_or(true),
                )
            };
            let (cbf, b) =
                decode_coded_block_flag(decoder, contexts, CtxBlockCat::Luma4x4, left_cbf, top_cbf);
            bins += b;
            this_mb_cbf[block_idx] = cbf;
            if cbf {
                let (coefs, b) = decode_residual_block(decoder, contexts, RES_BLOCK_SPEC_LUMA_4X4);
                bins += b;
                for (i, &c) in coefs.iter().enumerate() {
                    mb.luma_4x4[block_idx][i] = c;
                }
            }
            // CBF=0 leaves the block all-zero (already initialised).
        }
    }

    // 8. Chroma DC (CBF-gated, Cb then Cr).
    if mb.cbp_chroma >= 1 {
        let (cb_cbf, b) =
            decode_coded_block_flag(decoder, contexts, CtxBlockCat::ChromaDc, None, None);
        bins += b;
        if cb_cbf {
            let (cb, b) = decode_residual_block(decoder, contexts, RES_BLOCK_SPEC_CHROMA_DC);
            bins += b;
            for (i, &c) in cb.iter().enumerate() {
                mb.chroma_dc_cb[i] = c;
            }
        }
        let (cr_cbf, b) =
            decode_coded_block_flag(decoder, contexts, CtxBlockCat::ChromaDc, None, None);
        bins += b;
        if cr_cbf {
            let (cr, b) = decode_residual_block(decoder, contexts, RES_BLOCK_SPEC_CHROMA_DC);
            bins += b;
            for (i, &c) in cr.iter().enumerate() {
                mb.chroma_dc_cr[i] = c;
            }
        }
    }

    // 9. Chroma AC
    if mb.cbp_chroma == 2 {
        for blk in &mut mb.chroma_ac_cb {
            let (cbf, b) =
                decode_coded_block_flag(decoder, contexts, CtxBlockCat::ChromaAc, None, None);
            bins += b;
            if cbf {
                let (coefs, b) = decode_residual_block(decoder, contexts, RES_BLOCK_SPEC_CHROMA_AC);
                bins += b;
                for (i, &c) in coefs.iter().enumerate() {
                    blk[i] = c;
                }
            }
        }
        for blk in &mut mb.chroma_ac_cr {
            let (cbf, b) =
                decode_coded_block_flag(decoder, contexts, CtxBlockCat::ChromaAc, None, None);
            bins += b;
            if cbf {
                let (coefs, b) = decode_residual_block(decoder, contexts, RES_BLOCK_SPEC_CHROMA_AC);
                bins += b;
                for (i, &c) in coefs.iter().enumerate() {
                    blk[i] = c;
                }
            }
        }
    }

    (mb, bins, this_mb_cbf)
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The simplest round-trip: ten bypass bins, alternating 0/1,
    /// encoded and then decoded should recover the same sequence.
    #[test]
    fn bypass_round_trip_alternating() {
        let bins: Vec<u8> = (0..20).map(|i| (i & 1) as u8).collect();
        let mut enc = CabacEncoder::new();
        for &b in &bins {
            enc.encode_bypass(b);
        }
        enc.finish();

        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut out = Vec::new();
        for _ in 0..bins.len() {
            out.push(dec.decode_bypass());
        }
        assert_eq!(out, bins, "bypass round-trip diverged");
    }

    /// Context bins with a fixed context — encode 32 bins, decode,
    /// expect identity. The context's p_state_idx drift on both
    /// sides must match.
    #[test]
    fn context_round_trip_static_pattern() {
        let bins: Vec<u8> = vec![
            1, 1, 0, 1, 1, 1, 0, 0, 1, 0, 1, 1, 1, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 0,
            1,
        ];
        let mut enc_ctx = CabacCtx {
            p_state_idx: 18,
            val_mps: 0,
        };
        let mut enc = CabacEncoder::new();
        for &b in &bins {
            enc.encode_bin(&mut enc_ctx, b);
        }
        enc.finish();

        let mut dec_ctx = CabacCtx {
            p_state_idx: 18,
            val_mps: 0,
        };
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut out = Vec::new();
        for _ in 0..bins.len() {
            out.push(dec.decode_bin(&mut dec_ctx));
        }
        assert_eq!(out, bins, "context-bin round-trip diverged");
        assert_eq!(
            enc_ctx, dec_ctx,
            "encoder + decoder context must agree on final state"
        );
    }

    /// Spec §9.3.1.1.1 examples: at slice_qp = 26 (the median
    /// neutral QP), pre = ((m * 26) >> 4) + n. Verify the formula
    /// against hand-computed values.
    #[test]
    fn init_formula_matches_spec_examples() {
        // (m=20, n=-15) at qp=26: pre = ((20*26)>>4) + -15 = 32 + -15 = 17
        // 17 <= 63 → p_state_idx = 63-17 = 46, val_mps = 0
        let c = CabacCtx::init_from_mn(20, -15, 26);
        assert_eq!(
            c,
            CabacCtx {
                p_state_idx: 46,
                val_mps: 0
            }
        );

        // (m=2, n=54) at qp=26: pre = ((2*26)>>4) + 54 = 3 + 54 = 57
        // 57 <= 63 → p_state_idx = 63-57 = 6, val_mps = 0
        let c = CabacCtx::init_from_mn(2, 54, 26);
        assert_eq!(
            c,
            CabacCtx {
                p_state_idx: 6,
                val_mps: 0
            }
        );

        // (m=-28, n=127) at qp=26: pre = ((-28*26)>>4) + 127 = -46 + 127 = 81
        // 81 > 63 → p_state_idx = 81-64 = 17, val_mps = 1
        let c = CabacCtx::init_from_mn(-28, 127, 26);
        assert_eq!(
            c,
            CabacCtx {
                p_state_idx: 17,
                val_mps: 1
            }
        );

        // Clip3 sanity per §9.3.1.1.1 — large negative m at high qp
        // clips to preCtxState=1 (NOT 0; spec is Clip3(1, 126, ...)).
        let c = CabacCtx::init_from_mn(-127, -127, 51);
        assert_eq!(
            c,
            CabacCtx {
                p_state_idx: 62,
                val_mps: 0
            }
        );

        // Saturation high — large positive m at high qp clips to 126.
        let c = CabacCtx::init_from_mn(127, 127, 51);
        assert_eq!(
            c,
            CabacCtx {
                p_state_idx: 62,
                val_mps: 1
            }
        );
    }

    /// 1024 contexts initialised at QP=26 for an I-slice. Cross-check
    /// a few well-known entries (the first 11 from §9.3.1.1
    /// Table 9-12 for macroblock-type contexts).
    #[test]
    fn init_full_i_slice_table_at_qp26() {
        let ctxs = init_contexts(CabacSliceType::I, 0, 26);
        assert_eq!(ctxs.len(), 1024);
        // First entry uses (20, -15) per Table 9-12 ctxIdx 0; expected
        // pre=17 above.
        assert_eq!(
            ctxs[0],
            CabacCtx {
                p_state_idx: 46,
                val_mps: 0
            }
        );
        // ctxIdx 6 uses (-28, 127): pre=81, val_mps=1.
        assert_eq!(
            ctxs[6],
            CabacCtx {
                p_state_idx: 17,
                val_mps: 1
            }
        );
    }

    /// mb_skip_flag context selection per §9.3.3.1.1.1.
    #[test]
    fn mb_skip_flag_ctx_selection() {
        // I-slice doesn't use mb_skip_flag.
        assert_eq!(mb_skip_flag_ctx_offset(CabacSliceType::I), None);

        // P-slice base offset is 11; B-slice is 24.
        assert_eq!(mb_skip_flag_ctx_offset(CabacSliceType::P), Some(11));
        assert_eq!(mb_skip_flag_ctx_offset(CabacSliceType::B), Some(24));

        // ctxIdxInc cases:
        //   no neighbours (top-left MB)               → 0
        //   one neighbour, skip=0 (not-skipped)        → 1
        //   one neighbour, skip=1 (skipped)            → 0
        //   both neighbours present, both not-skipped → 2
        //   both present, both skipped                → 0
        //   one not-skipped + one unavailable         → 1
        assert_eq!(mb_skip_flag_ctx_idx_inc(None, None), 0);
        assert_eq!(mb_skip_flag_ctx_idx_inc(Some(0), None), 1);
        assert_eq!(mb_skip_flag_ctx_idx_inc(Some(1), None), 0);
        assert_eq!(mb_skip_flag_ctx_idx_inc(Some(0), Some(0)), 2);
        assert_eq!(mb_skip_flag_ctx_idx_inc(Some(1), Some(1)), 0);
        assert_eq!(mb_skip_flag_ctx_idx_inc(Some(0), Some(1)), 1);

        // Combined helper.
        assert_eq!(
            mb_skip_flag_ctx_idx(CabacSliceType::P, None, None),
            Some(11),
        );
        assert_eq!(
            mb_skip_flag_ctx_idx(CabacSliceType::P, Some(0), Some(0)),
            Some(13),
        );
        assert_eq!(
            mb_skip_flag_ctx_idx(CabacSliceType::B, Some(0), None),
            Some(25),
        );
    }

    /// Full encode-decode round-trip of a `mb_skip_flag` sequence in
    /// a P slice. Both sides track per-row left/top neighbour state
    /// and pick the correct context per MB.
    #[test]
    fn mb_skip_flag_encode_decode_round_trip() {
        let slice_type = CabacSliceType::P;
        let qp = 26;
        let init_idc = 0;
        let mb_width = 20; // 320/16 — same as parrot
        let mb_height = 15; // 240/16
        let total = mb_width * mb_height;

        // Deterministic test pattern: every 3rd MB is skipped.
        let skips: Vec<u8> = (0..total).map(|i| ((i % 3 == 0) as u8)).collect();

        // ENCODE.
        let mut enc_ctxs = init_contexts(slice_type, init_idc, qp);
        let mut enc = CabacEncoder::new();
        // Walk MB raster-scan; track skip flags in a 2D grid for
        // neighbour lookup.
        let mut grid = vec![vec![None::<u8>; mb_width]; mb_height];
        for (i, &skip) in skips.iter().enumerate() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { grid[r][c - 1] };
            let top = if r == 0 { None } else { grid[r - 1][c] };
            let ctx_idx = mb_skip_flag_ctx_idx(slice_type, left, top).unwrap();
            enc.encode_bin(&mut enc_ctxs[ctx_idx], skip);
            grid[r][c] = Some(skip);
        }
        enc.finish();

        // DECODE.
        let mut dec_ctxs = init_contexts(slice_type, init_idc, qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut decoded_grid = vec![vec![None::<u8>; mb_width]; mb_height];
        let mut decoded = Vec::with_capacity(total);
        for i in 0..total {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { decoded_grid[r][c - 1] };
            let top = if r == 0 { None } else { decoded_grid[r - 1][c] };
            let ctx_idx = mb_skip_flag_ctx_idx(slice_type, left, top).unwrap();
            let bit = dec.decode_bin(&mut dec_ctxs[ctx_idx]);
            decoded_grid[r][c] = Some(bit);
            decoded.push(bit);
        }

        assert_eq!(decoded, skips, "mb_skip_flag round-trip diverged");
        // The three relevant contexts (ctxIdx 11/12/13 for P) on
        // both sides must end at the same adaptive state.
        for ctx in 11..=13 {
            assert_eq!(
                enc_ctxs[ctx], dec_ctxs[ctx],
                "ctx {} drifted differently between encoder/decoder",
                ctx,
            );
        }
    }

    /// Each of the 4 P-slice mb_type values round-trips through the
    /// binarisation tree. Verifies the encode/decode pair agrees
    /// on the bin sequence per Table 9-37.
    #[test]
    fn p_mb_type_each_value_round_trips() {
        for val in 0u8..=3 {
            let qp = 26;
            let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, qp);
            let mut enc = CabacEncoder::new();
            let bins_emitted = encode_p_mb_type(&mut enc, &mut enc_ctxs, val);
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, qp);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (decoded, bins_consumed) = decode_p_mb_type(&mut dec, &mut dec_ctxs);
            assert_eq!(decoded, val);
            assert_eq!(bins_consumed, bins_emitted);
        }
    }

    /// Sequence of 50 P-slice mb_types — verify the contexts adapt
    /// consistently between encoder and decoder. This exercises the
    /// case where bin counts vary across mb_types (1, 2, or 3 bins).
    #[test]
    fn p_mb_type_sequence_round_trip() {
        let seq: Vec<u8> = vec![
            0, 0, 1, 0, 3, 2, 0, 0, 3, 1, 0, 2, 3, 0, 0, 1, 0, 3, 0, 2, 0, 0, 0, 1, 3, 0, 2, 0, 1,
            0, 3, 0, 0, 2, 0, 3, 1, 0, 0, 0, 2, 0, 3, 0, 1, 0, 0, 3, 0, 0,
        ];

        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        for &mb in &seq {
            encode_p_mb_type(&mut enc, &mut enc_ctxs, mb);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        for &expected in &seq {
            let (got, _) = decode_p_mb_type(&mut dec, &mut dec_ctxs);
            assert_eq!(got, expected);
        }
        // Encoder + decoder agree on context state.
        for ctx in P_MB_TYPE_CTX_OFFSET..P_MB_TYPE_CTX_OFFSET + 3 {
            assert_eq!(enc_ctxs[ctx], dec_ctxs[ctx]);
        }
    }

    /// Signed↔unsigned mapping is bijective and matches §9.1.1.
    #[test]
    fn mb_qp_delta_signed_unsigned_mapping() {
        // From the spec:
        //   d=0  → k=0
        //   d=+1 → k=1
        //   d=-1 → k=2
        //   d=+2 → k=3
        //   d=-2 → k=4
        //   etc.
        let cases = [
            (0, 0),
            (1, 1),
            (-1, 2),
            (2, 3),
            (-2, 4),
            (3, 5),
            (-3, 6),
            (10, 19),
            (-10, 20),
            (25, 49),
            (-25, 50),
            (26, 51),
        ];
        for (d, expected_k) in cases {
            let k = mb_qp_delta_signed_to_unsigned(d);
            assert_eq!(k, expected_k, "d={} → k mismatch", d);
            let d_back = mb_qp_delta_unsigned_to_signed(k);
            assert_eq!(d_back, d, "round-trip broke at d={}", d);
        }
    }

    /// Context selection per Table 9-39.
    #[test]
    fn mb_qp_delta_ctx_selection() {
        // bin 0: ctx 60 if prev was zero, else 61
        assert_eq!(mb_qp_delta_ctx_idx(0, true), 60);
        assert_eq!(mb_qp_delta_ctx_idx(0, false), 61);
        // bin 1: ctx 62 always
        assert_eq!(mb_qp_delta_ctx_idx(1, true), 62);
        assert_eq!(mb_qp_delta_ctx_idx(1, false), 62);
        // bin 2+: ctx 63 always
        assert_eq!(mb_qp_delta_ctx_idx(2, true), 63);
        assert_eq!(mb_qp_delta_ctx_idx(5, false), 63);
    }

    /// Each plausible delta value round-trips through the unary
    /// coder + context selection.
    #[test]
    fn mb_qp_delta_each_value_round_trips() {
        for delta in -26..=25 {
            let qp = 26;
            let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, qp);
            let mut enc = CabacEncoder::new();
            encode_mb_qp_delta(&mut enc, &mut enc_ctxs, delta, /*prev_was_zero=*/ true);
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, qp);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (got, _) =
                decode_mb_qp_delta(&mut dec, &mut dec_ctxs, /*prev_was_zero=*/ true);
            assert_eq!(got, delta, "round-trip failed for delta={}", delta);
        }
    }

    /// A sequence of mb_qp_deltas with the previous-was-zero state
    /// threaded through. The encoder + decoder must agree on which
    /// context (60 vs 61) to use for each bin 0.
    #[test]
    fn mb_qp_delta_sequence_round_trip_with_carried_state() {
        let seq: Vec<i32> = vec![
            0, 1, 0, -1, 0, 0, 2, -3, 0, 5, -5, 0, 0, 10, -10, 0, 1, 1, 0, -1,
        ];
        let qp = 26;
        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, qp);
        let mut enc = CabacEncoder::new();
        let mut prev_was_zero = true; // first MB: spec says "0" prev
        for &d in &seq {
            encode_mb_qp_delta(&mut enc, &mut enc_ctxs, d, prev_was_zero);
            prev_was_zero = d == 0;
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut prev_was_zero_d = true;
        for &expected in &seq {
            let (got, _) = decode_mb_qp_delta(&mut dec, &mut dec_ctxs, prev_was_zero_d);
            assert_eq!(got, expected);
            prev_was_zero_d = got == 0;
        }
        // All four contexts (60..63) end in agreement.
        for ctx in MB_QP_DELTA_CTX_OFFSET..MB_QP_DELTA_CTX_OFFSET + 4 {
            assert_eq!(enc_ctxs[ctx], dec_ctxs[ctx], "ctx {} drift", ctx);
        }
    }

    /// Every 4-bit cbp_luma value (0..15) round-trips through the
    /// 4-bin encoder/decoder for an isolated macroblock (no
    /// neighbours).
    #[test]
    fn cbp_luma_all_16_values_round_trip() {
        for cbp_luma in 0u8..16 {
            let qp = 26;
            let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, qp);
            let mut enc = CabacEncoder::new();
            encode_cbp_luma(&mut enc, &mut enc_ctxs, cbp_luma, 0, 0);
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, qp);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (got, bins) = decode_cbp_luma(&mut dec, &mut dec_ctxs, 0, 0);
            assert_eq!(got, cbp_luma, "cbp_luma 0x{:X} round-trip", cbp_luma);
            assert_eq!(bins, 4);
        }
    }

    /// CBP chroma's three values (0, 1, 2) round-trip with their
    /// expected bin counts.
    #[test]
    fn cbp_chroma_round_trip() {
        for (chroma, expected_bins) in [(0u8, 1usize), (1, 2), (2, 2)] {
            let qp = 26;
            let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, qp);
            let mut enc = CabacEncoder::new();
            let bins = encode_cbp_chroma(&mut enc, &mut enc_ctxs, chroma, 0, 0);
            assert_eq!(bins, expected_bins);
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, qp);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (got, _) = decode_cbp_chroma(&mut dec, &mut dec_ctxs, 0, 0);
            assert_eq!(got, chroma);
        }
    }

    /// Within-MB neighbour mapping: block 0's neighbours are in
    /// OTHER MBs, while block 3's neighbours are both inside the
    /// same MB. Encoder + decoder must agree on which bit feeds
    /// which context.
    #[test]
    fn cbp_luma_neighbour_mapping_within_mb() {
        // block 0: left_mb.bit1 = 1, top_mb.bit2 = 0
        //   → (left_term, top_term) = (1, 0)
        let (a, b) = cbp_luma_neighbour_bit(0, 0, 0b0010, 0b0000);
        assert_eq!((a, b), (1, 0));

        // block 1: this_so_far has bit 0 set
        //   → (left_term=1, top_term=top_mb.bit3=0)
        let (a, b) = cbp_luma_neighbour_bit(1, 0b0001, 0, 0);
        assert_eq!((a, b), (1, 0));

        // block 2: left_mb.bit3 = 1, this_so_far.bit0 = 0
        let (a, b) = cbp_luma_neighbour_bit(2, 0, 0b1000, 0);
        assert_eq!((a, b), (1, 0));

        // block 3: this_so_far.bit2 = 1, this_so_far.bit1 = 1
        //   → (1, 1)
        let (a, b) = cbp_luma_neighbour_bit(3, 0b0110, 0, 0);
        assert_eq!((a, b), (1, 1));
    }

    /// Sequence of 30 MBs with both CBP luma + chroma. Both sides
    /// of the encoder/decoder must thread the (left, top)
    /// neighbour CBP values correctly through the sequence.
    #[test]
    fn cbp_sequence_round_trip_with_neighbour_state() {
        // 6 columns × 5 rows. Pre-built CBP values per MB.
        let mb_cbp_luma: Vec<u8> = vec![
            0x0, 0xF, 0x3, 0xC, 0xA, 0x5, 0xF, 0x0, 0x5, 0xA, 0xC, 0x3, 0x6, 0x9, 0x3, 0xC, 0x0,
            0xF, 0xA, 0x5, 0xC, 0x3, 0x9, 0x6, 0x0, 0xF, 0xC, 0x3, 0x6, 0x9,
        ];
        let mb_cbp_chroma: Vec<u8> = (0..30).map(|i| (i % 3) as u8).collect();
        let width = 6;

        let qp = 26;
        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, qp);
        let mut enc = CabacEncoder::new();
        let mut enc_luma_grid = vec![vec![0u8; width]; 5];
        let mut enc_chroma_grid = vec![vec![0u8; width]; 5];
        for (i, (&luma, &chroma)) in mb_cbp_luma.iter().zip(mb_cbp_chroma.iter()).enumerate() {
            let r = i / width;
            let c = i % width;
            let left_luma = if c == 0 { 0 } else { enc_luma_grid[r][c - 1] };
            let top_luma = if r == 0 { 0 } else { enc_luma_grid[r - 1][c] };
            let left_chroma = if c == 0 { 0 } else { enc_chroma_grid[r][c - 1] };
            let top_chroma = if r == 0 { 0 } else { enc_chroma_grid[r - 1][c] };

            encode_cbp_luma(&mut enc, &mut enc_ctxs, luma, left_luma, top_luma);
            encode_cbp_chroma(&mut enc, &mut enc_ctxs, chroma, left_chroma, top_chroma);
            enc_luma_grid[r][c] = luma;
            enc_chroma_grid[r][c] = chroma;
        }
        enc.finish();

        // Decode mirror.
        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut dec_luma_grid = vec![vec![0u8; width]; 5];
        let mut dec_chroma_grid = vec![vec![0u8; width]; 5];
        for i in 0..mb_cbp_luma.len() {
            let r = i / width;
            let c = i % width;
            let left_luma = if c == 0 { 0 } else { dec_luma_grid[r][c - 1] };
            let top_luma = if r == 0 { 0 } else { dec_luma_grid[r - 1][c] };
            let left_chroma = if c == 0 { 0 } else { dec_chroma_grid[r][c - 1] };
            let top_chroma = if r == 0 { 0 } else { dec_chroma_grid[r - 1][c] };

            let (luma, _) = decode_cbp_luma(&mut dec, &mut dec_ctxs, left_luma, top_luma);
            let (chroma, _) = decode_cbp_chroma(&mut dec, &mut dec_ctxs, left_chroma, top_chroma);
            assert_eq!(luma, mb_cbp_luma[i], "mb {} luma mismatch", i);
            assert_eq!(chroma, mb_cbp_chroma[i], "mb {} chroma mismatch", i);
            dec_luma_grid[r][c] = luma;
            dec_chroma_grid[r][c] = chroma;
        }
        // All 4 luma + 2*4 chroma contexts agree at end.
        for ctx in CBP_LUMA_CTX_OFFSET..CBP_LUMA_CTX_OFFSET + 4 {
            assert_eq!(enc_ctxs[ctx], dec_ctxs[ctx], "cbp_luma ctx {} drift", ctx);
        }
        for ctx in CBP_CHROMA_CTX_OFFSET..CBP_CHROMA_CTX_OFFSET + 8 {
            assert_eq!(enc_ctxs[ctx], dec_ctxs[ctx], "cbp_chroma ctx {} drift", ctx);
        }
    }

    /// coeff_abs_level_minus1 UEG0 binarisation round-trips for
    /// values across the truncation boundary (< 14 use only the
    /// unary prefix; ≥ 14 use unary + bypass Exp-Golomb suffix).
    #[test]
    fn coeff_abs_level_minus1_round_trip() {
        let values = [0u32, 1, 5, 13, 14, 15, 20, 50, 100, 200, 500];
        for &v in &values {
            let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
            let mut enc = CabacEncoder::new();
            encode_coeff_abs_level_minus1(
                &mut enc,
                &mut enc_ctxs,
                RES_ABS_LEVEL_CTX_OFFSET,
                v,
                0,
                0,
            );
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (got, _) = decode_coeff_abs_level_minus1(
                &mut dec,
                &mut dec_ctxs,
                RES_ABS_LEVEL_CTX_OFFSET,
                0,
                0,
            );
            assert_eq!(got, v, "coeff_abs_level v={} round-trip", v);
        }
    }

    /// A sparse 4x4 luma block — only positions 0, 3, 7 have
    /// non-zero coefs. Round-trip the full residual_block_cabac
    /// machinery.
    #[test]
    fn residual_4x4_sparse_round_trip() {
        let mut coefs = [0i32; 16];
        coefs[0] = 5;
        coefs[3] = -2;
        coefs[7] = 1;

        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        encode_residual_4x4_luma(&mut enc, &mut enc_ctxs, &coefs);
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (decoded, _) = decode_residual_4x4_luma(&mut dec, &mut dec_ctxs);
        assert_eq!(decoded, coefs);
    }

    /// A dense 4x4 block — every position non-zero, last coef at
    /// position 15 (implicit-significant in the spec).
    #[test]
    fn residual_4x4_dense_round_trip() {
        let coefs: [i32; 16] = [10, -8, 6, -4, 3, -2, 1, -1, 2, 3, 4, 5, 6, 7, 8, 9];
        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        encode_residual_4x4_luma(&mut enc, &mut enc_ctxs, &coefs);
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (decoded, _) = decode_residual_4x4_luma(&mut dec, &mut dec_ctxs);
        assert_eq!(decoded, coefs);
    }

    /// Single-non-zero block at the LAST position (15) — the
    /// implicit-last codepath. No last_significant_coeff_flag bin
    /// for position 15.
    #[test]
    fn residual_4x4_only_last_position_significant() {
        let mut coefs = [0i32; 16];
        coefs[15] = 7;

        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        encode_residual_4x4_luma(&mut enc, &mut enc_ctxs, &coefs);
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (decoded, _) = decode_residual_4x4_luma(&mut dec, &mut dec_ctxs);
        assert_eq!(decoded, coefs);
    }

    /// Large magnitudes that exercise the UEG0 suffix path (>= 14).
    #[test]
    fn residual_4x4_large_magnitudes() {
        let mut coefs = [0i32; 16];
        coefs[0] = 100;
        coefs[5] = -50;
        coefs[10] = 200;

        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        encode_residual_4x4_luma(&mut enc, &mut enc_ctxs, &coefs);
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (decoded, _) = decode_residual_4x4_luma(&mut dec, &mut dec_ctxs);
        assert_eq!(decoded, coefs);
    }

    /// Sequence of 50 4x4 blocks with varied sparsity — exercises
    /// the encoder/decoder running-count state machinery (num_eq1
    /// / num_gt1 reset per block, but contexts adapt across).
    #[test]
    fn residual_4x4_sequence_round_trip() {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};

        let mut blocks: Vec<[i32; 16]> = Vec::new();
        // Deterministic pseudo-random blocks via a hash chain.
        let mut seed: u64 = 0x42;
        for block_idx in 0..50 {
            let mut block = [0i32; 16];
            // Each block has 2-6 non-zero coefs at varying positions.
            let mut hasher = DefaultHasher::new();
            (block_idx as u64, seed).hash(&mut hasher);
            seed = hasher.finish();
            let n_nonzero = (seed % 5 + 2) as usize;
            for k in 0..n_nonzero {
                let mut h2 = DefaultHasher::new();
                (seed, k as u64).hash(&mut h2);
                let r = h2.finish();
                let pos = (r % 16) as usize;
                let sign: i32 = if (r >> 16) & 1 == 0 { 1 } else { -1 };
                let mag = ((r >> 24) % 20) as i32 + 1;
                block[pos] = sign * mag;
            }
            blocks.push(block);
        }

        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        for block in &blocks {
            encode_residual_4x4_luma(&mut enc, &mut enc_ctxs, block);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        for expected in &blocks {
            let (decoded, _) = decode_residual_4x4_luma(&mut dec, &mut dec_ctxs);
            assert_eq!(&decoded, expected, "block round-trip");
        }
        // Final adapted state agrees.
        for ctx in RES_SIG_COEF_CTX_OFFSET..RES_SIG_COEF_CTX_OFFSET + 15 {
            assert_eq!(enc_ctxs[ctx], dec_ctxs[ctx], "sig_coef ctx {} drift", ctx);
        }
    }

    /// Generic residual block — round-trip each supported ctxBlockCat.
    #[test]
    fn residual_block_all_cats_round_trip() {
        use CtxBlockCat::*;
        for cat in [
            Intra16x16Dc,
            Intra16x16Ac,
            Luma4x4,
            ChromaDc,
            ChromaAc,
            Luma8x8,
        ] {
            let spec = res_block_spec(cat);
            let mut coefs = vec![0i32; spec.n_coefs];
            // Sprinkle a few non-zero coefs at specific positions.
            for i in (0..spec.n_coefs).step_by(3) {
                coefs[i] = ((i as i32) % 5) - 2 + 1; // some nonzero pattern
            }
            // Ensure last is non-trivial.
            if spec.n_coefs >= 4 {
                coefs[spec.n_coefs / 2] = 7;
            }
            // Ensure at least one non-zero (gates the test).
            if coefs.iter().all(|&c| c == 0) {
                coefs[0] = 1;
            }

            let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
            let mut enc = CabacEncoder::new();
            encode_residual_block(&mut enc, &mut enc_ctxs, spec, &coefs);
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (got, _) = decode_residual_block(&mut dec, &mut dec_ctxs, spec);
            assert_eq!(got, coefs, "cat {:?} round-trip", cat);
        }
    }

    /// Luma 8x8 stress test — 64 coefs is the largest residual block.
    #[test]
    fn residual_luma_8x8_dense() {
        let spec = RES_BLOCK_SPEC_LUMA_8X8;
        let mut coefs = vec![0i32; 64];
        // Realistic dense low-freq block.
        for i in 0..16 {
            coefs[i] = (i as i32 + 1) * if i & 1 == 0 { 1 } else { -1 };
        }
        // Plus a couple of high-freq.
        coefs[40] = 3;
        coefs[63] = 1;

        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        encode_residual_block(&mut enc, &mut enc_ctxs, spec, &coefs);
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (got, _) = decode_residual_block(&mut dec, &mut dec_ctxs, spec);
        assert_eq!(got, coefs);
    }

    /// mvd component round-trips across the prefix/suffix boundary.
    #[test]
    fn mvd_each_magnitude_round_trips() {
        let values = [
            0i32, 1, -1, 5, -5, 8, -8, 9, -9, 10, -10, 50, -50, 100, -100, 500, -500, 1000, -1000,
        ];
        for &v in &values {
            let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
            let mut enc = CabacEncoder::new();
            encode_mvd(&mut enc, &mut enc_ctxs, MVD_L0_X_CTX_OFFSET, v);
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (got, _) = decode_mvd(&mut dec, &mut dec_ctxs, MVD_L0_X_CTX_OFFSET);
            assert_eq!(got, v, "mvd v={} round-trip", v);
        }
    }

    /// mvd sequence — 100 values, exercises context adaptation.
    #[test]
    fn mvd_sequence_round_trip() {
        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        let mut values = Vec::new();
        for i in 0..100i32 {
            let v = ((i * 13) % 41) - 20;
            values.push(v);
            encode_mvd(&mut enc, &mut enc_ctxs, MVD_L0_X_CTX_OFFSET, v);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        for &expected in &values {
            let (got, _) = decode_mvd(&mut dec, &mut dec_ctxs, MVD_L0_X_CTX_OFFSET);
            assert_eq!(got, expected);
        }
    }

    /// Every P-slice sub_mb_type value round-trips through its
    /// bin tree.
    #[test]
    fn p_sub_mb_type_each_value_round_trips() {
        for val in 0u8..=3 {
            let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
            let mut enc = CabacEncoder::new();
            encode_p_sub_mb_type(&mut enc, &mut enc_ctxs, val);
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (got, _) = decode_p_sub_mb_type(&mut dec, &mut dec_ctxs);
            assert_eq!(got, val);
        }
    }

    /// ref_idx neighbour context selection per §9.3.3.1.1.7.
    #[test]
    fn ref_idx_neighbour_context_selection() {
        // Neither neighbour set → bin0 ctxIdxInc = 0
        assert_eq!(ref_idx_bin0_ctx_inc(None, None), 0);
        // Left set, top not → 1
        assert_eq!(ref_idx_bin0_ctx_inc(Some(1), None), 1);
        // Top set, left not → 2
        assert_eq!(ref_idx_bin0_ctx_inc(None, Some(2)), 2);
        // Both set → 3
        assert_eq!(ref_idx_bin0_ctx_inc(Some(3), Some(1)), 3);
        // Left available but ref_idx == 0 → 0 contribution
        assert_eq!(ref_idx_bin0_ctx_inc(Some(0), None), 0);
        assert_eq!(ref_idx_bin0_ctx_inc(Some(0), Some(0)), 0);
    }

    /// ref_idx round-trip across the truncated-unary range.
    #[test]
    fn ref_idx_l0_round_trip() {
        for num_ref_minus1 in [0u8, 1, 2, 3, 4, 7] {
            for ref_idx in 0..=num_ref_minus1 {
                let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
                let mut enc = CabacEncoder::new();
                encode_ref_idx_l0(
                    &mut enc,
                    &mut enc_ctxs,
                    ref_idx,
                    /*bin0_inc=*/ 0,
                    num_ref_minus1,
                );
                enc.finish();

                let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
                let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
                let (got, _) = decode_ref_idx_l0(
                    &mut dec,
                    &mut dec_ctxs,
                    /*bin0_inc=*/ 0,
                    num_ref_minus1,
                );
                assert_eq!(
                    got, ref_idx,
                    "ref_idx round-trip failed: cmax={}, val={}",
                    num_ref_minus1, ref_idx
                );
            }
        }
    }

    /// Threaded neighbour-state walk: 30 macroblocks across a 6x5
    /// grid; each MB's ref_idx_l0 selected with the previous MB's
    /// values as left/top neighbours.
    #[test]
    fn ref_idx_l0_sequence_with_neighbour_state() {
        let mut enc_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut enc = CabacEncoder::new();
        let width = 6;
        let height = 5;
        let num_ref_minus1 = 3u8;
        // Generate a deterministic pattern of ref_idx values.
        let mut refs: Vec<u8> = (0..width * height).map(|i| ((i * 7) % 4) as u8).collect();
        // Ensure values are in range.
        for r in refs.iter_mut() {
            if *r > num_ref_minus1 {
                *r = num_ref_minus1;
            }
        }

        let mut grid = vec![vec![None::<u8>; width]; height];
        for (i, &val) in refs.iter().enumerate() {
            let r = i / width;
            let c = i % width;
            let left = if c == 0 { None } else { grid[r][c - 1] };
            let top = if r == 0 { None } else { grid[r - 1][c] };
            let inc = ref_idx_bin0_ctx_inc(left, top);
            encode_ref_idx_l0(&mut enc, &mut enc_ctxs, val, inc, num_ref_minus1);
            grid[r][c] = Some(val);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut dec_grid = vec![vec![None::<u8>; width]; height];
        for i in 0..refs.len() {
            let r = i / width;
            let c = i % width;
            let left = if c == 0 { None } else { dec_grid[r][c - 1] };
            let top = if r == 0 { None } else { dec_grid[r - 1][c] };
            let inc = ref_idx_bin0_ctx_inc(left, top);
            let (got, _) = decode_ref_idx_l0(&mut dec, &mut dec_ctxs, inc, num_ref_minus1);
            assert_eq!(got, refs[i]);
            dec_grid[r][c] = Some(got);
        }
    }

    /// Contexts produced for I vs P/B differ — the I table and the
    /// PB[0] table at ctxIdx 0 use different (m, n) pairs.
    #[test]
    fn init_i_vs_pb_tables_differ() {
        let i_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let p_ctxs = init_contexts(CabacSliceType::P, 0, 26);
        // Some ctxIdx must differ — pick a known one.
        // ctxIdx 11 (P_L0_16x16 vs I-only) typically differs.
        assert_ne!(i_ctxs[11], p_ctxs[11]);
    }

    // --- intra prediction mode CABAC tests --------------------

    #[test]
    fn prev_intra4x4_flag_round_trip() {
        let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut enc = CabacEncoder::new();
        // 100 alternating flags + a deterministic pattern.
        let flags: Vec<bool> = (0..100).map(|i| i % 3 != 0).collect();
        for &f in &flags {
            encode_prev_intra4x4_flag(&mut enc, &mut enc_ctxs, f);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        for (i, &expected) in flags.iter().enumerate() {
            let (got, _) = decode_prev_intra4x4_flag(&mut dec, &mut dec_ctxs);
            assert_eq!(got, expected, "prev_intra4x4_flag[{}]", i);
        }
    }

    #[test]
    fn rem_intra4x4_each_value_round_trips() {
        for v in 0..8u8 {
            let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
            let mut enc = CabacEncoder::new();
            let bins = encode_rem_intra4x4(&mut enc, &mut enc_ctxs, v);
            assert_eq!(bins, 3);
            enc.finish();

            let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
            let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
            let (got, bins_d) = decode_rem_intra4x4(&mut dec, &mut dec_ctxs);
            assert_eq!(got, v, "rem_intra4x4 v={}", v);
            assert_eq!(bins_d, 3);
        }
    }

    #[test]
    fn rem_intra4x4_sequence_round_trip() {
        // 16 sub-blocks per MB × 4 MBs worth. Widen to u32 for the
        // intermediate `i * 5 + 3` (max 63*5+3=318, overflows u8):
        // since 8 | 256, `(x % 256) % 8 == x % 8`, so this yields the
        // exact same cycling sequence a u8 wrap would have produced,
        // without the debug-mode overflow panic.
        let seq: Vec<u8> = (0..64u32).map(|i| ((i * 5 + 3) % 8) as u8).collect();
        let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut enc = CabacEncoder::new();
        for &v in &seq {
            encode_rem_intra4x4(&mut enc, &mut enc_ctxs, v);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        for (i, &expected) in seq.iter().enumerate() {
            let (got, _) = decode_rem_intra4x4(&mut dec, &mut dec_ctxs);
            assert_eq!(got, expected, "rem_intra4x4 seq[{}]", i);
        }
    }

    #[test]
    fn intra_chroma_pred_mode_each_value_round_trips() {
        for mode in 0..4u8 {
            for (la, ta) in [
                (None, None),
                (Some(0), None),
                (None, Some(0)),
                (Some(0), Some(0)),
                (Some(1), None),
                (Some(0), Some(2)),
                (Some(3), Some(1)),
            ] {
                let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
                let mut enc = CabacEncoder::new();
                encode_intra_chroma_pred_mode(&mut enc, &mut enc_ctxs, mode, la, ta);
                enc.finish();

                let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
                let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
                let (got, _) = decode_intra_chroma_pred_mode(&mut dec, &mut dec_ctxs, la, ta);
                assert_eq!(
                    got, mode,
                    "intra_chroma mode={} left={:?} top={:?}",
                    mode, la, ta
                );
            }
        }
    }

    #[test]
    fn intra_chroma_neighbour_context_sequence() {
        // Simulate a 2x2 MB neighbourhood and verify context state
        // propagates across MBs correctly through encode+decode.
        // Modes per MB in raster scan: [0, 2, 1, 3].
        let modes = [0u8, 2u8, 1u8, 3u8];
        let mb_width = 2;
        let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut enc = CabacEncoder::new();
        let mut grid: [[Option<u8>; 2]; 2] = [[None; 2]; 2];
        for (i, &m) in modes.iter().enumerate() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { grid[r][c - 1] };
            let top = if r == 0 { None } else { grid[r - 1][c] };
            encode_intra_chroma_pred_mode(&mut enc, &mut enc_ctxs, m, left, top);
            grid[r][c] = Some(m);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut decoded_grid: [[Option<u8>; 2]; 2] = [[None; 2]; 2];
        for i in 0..modes.len() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { decoded_grid[r][c - 1] };
            let top = if r == 0 { None } else { decoded_grid[r - 1][c] };
            let (got, _) = decode_intra_chroma_pred_mode(&mut dec, &mut dec_ctxs, left, top);
            assert_eq!(
                got, modes[i],
                "MB[{}] expected mode {}, got {}",
                i, modes[i], got
            );
            decoded_grid[r][c] = Some(got);
        }
    }

    // --- I-slice mb_type CABAC tests --------------------------

    #[test]
    fn i_mb_type_i_nxn_round_trip() {
        // Single MB with no neighbours.
        let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut enc = CabacEncoder::new();
        encode_i_mb_type_i_nxn(&mut enc, &mut enc_ctxs, None, None);
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (got, _) = decode_i_mb_type_is_i_nxn(&mut dec, &mut dec_ctxs, None, None);
        assert!(got, "I_NxN round-trip");
    }

    #[test]
    fn i_mb_type_i_nxn_grid_round_trip() {
        // 3x3 grid of all-I_NxN MBs — verifies neighbour state
        // propagates correctly across encode + decode.
        let mb_width = 3;
        let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut enc = CabacEncoder::new();
        let mut grid: [[Option<bool>; 3]; 3] = [[None; 3]; 3];
        for r in 0..3 {
            for c in 0..3 {
                let left = if c == 0 { None } else { grid[r][c - 1] };
                let top = if r == 0 { None } else { grid[r - 1][c] };
                encode_i_mb_type_i_nxn(&mut enc, &mut enc_ctxs, left, top);
                grid[r][c] = Some(true); // all I_NxN
            }
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut dgrid: [[Option<bool>; 3]; 3] = [[None; 3]; 3];
        for r in 0..3 {
            for c in 0..3 {
                let left = if c == 0 { None } else { dgrid[r][c - 1] };
                let top = if r == 0 { None } else { dgrid[r - 1][c] };
                let (got, _) = decode_i_mb_type_is_i_nxn(&mut dec, &mut dec_ctxs, left, top);
                assert!(got, "MB[{},{}] should be I_NxN", r, c);
                dgrid[r][c] = Some(true);
            }
            // Suppress unused-var warning for mb_width.
            let _ = mb_width;
        }
    }

    // --- I_NxN MB walker round-trip tests ---------------------

    fn make_test_mb(seed: u32) -> INxnMbInputs {
        // Realistic-shape MB: top-left luma block has DC + a few
        // low-freq AC; CBP luma covers one 8×8; no chroma.
        let mut mb = INxnMbInputs::default();
        let s = seed as i32;
        // Block 0 (top-left of MB) — DC+AC residual.
        mb.luma_4x4[0] = [100 + s, -8, 3, 0, -6, 5, 1, 0, 2, 1, 0, 0, 0, 0, 0, 0];
        mb.cbp_luma = 0b0001; // 8×8 block 0 only
        mb.cbp_chroma = 0;
        mb.intra_chroma_pred_mode = 0;
        mb.mb_qp_delta = 0;
        mb
    }

    #[test]
    fn i_nxn_mb_walker_round_trip_no_neighbours() {
        let mb = make_test_mb(0);
        let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut enc = CabacEncoder::new();
        let (bins, _) = encode_i_nxn_mb(&mut enc, &mut enc_ctxs, &mb, None, None);
        enc.finish();
        assert!(bins > 0);

        let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (decoded, _, _) = decode_i_nxn_mb(&mut dec, &mut dec_ctxs, None, None);
        assert_eq!(decoded.cbp_luma, mb.cbp_luma);
        assert_eq!(decoded.cbp_chroma, mb.cbp_chroma);
        assert_eq!(decoded.intra_chroma_pred_mode, mb.intra_chroma_pred_mode);
        assert_eq!(decoded.mb_qp_delta, mb.mb_qp_delta);
        for i in 0..16 {
            for j in 0..16 {
                assert_eq!(
                    decoded.luma_4x4[i][j], mb.luma_4x4[i][j],
                    "luma[{}][{}]",
                    i, j,
                );
            }
        }
    }

    #[test]
    fn i_nxn_mb_walker_round_trip_with_chroma() {
        let mut mb = make_test_mb(1);
        mb.cbp_chroma = 1; // DC only
        mb.chroma_dc_cb = [40, -2, 1, 0];
        mb.chroma_dc_cr = [-30, 1, 0, 0];

        let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut enc = CabacEncoder::new();
        let _ = encode_i_nxn_mb(&mut enc, &mut enc_ctxs, &mb, None, None);
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (decoded, _, _) = decode_i_nxn_mb(&mut dec, &mut dec_ctxs, None, None);
        assert_eq!(decoded.cbp_chroma, 1);
        assert_eq!(decoded.chroma_dc_cb, mb.chroma_dc_cb);
        assert_eq!(decoded.chroma_dc_cr, mb.chroma_dc_cr);
    }

    #[test]
    fn i_nxn_mb_walker_sequence_with_neighbour_state() {
        // 3 consecutive MBs in raster scan; verifies neighbour
        // state propagates correctly between MBs.
        let mbs = [make_test_mb(0), make_test_mb(7), make_test_mb(13)];

        let mut enc_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut enc = CabacEncoder::new();
        let mut prev: Option<MbNeighbourState> = None;
        for mb in &mbs {
            let (_, cbf) = encode_i_nxn_mb(
                &mut enc,
                &mut enc_ctxs,
                mb,
                prev.as_ref(),
                None, // same row, no top
            );
            prev = Some(MbNeighbourState {
                mb_type_is_i_nxn: Some(true),
                cbp_luma: mb.cbp_luma,
                cbp_chroma: mb.cbp_chroma,
                intra_chroma_mode: Some(mb.intra_chroma_pred_mode),
                mb_qp_delta_was_zero: mb.mb_qp_delta == 0,
                luma_cbf: cbf,
                luma_dc_cbf: false,
                chroma_dc_cbf_cb: false,
                chroma_dc_cbf_cr: false,
                chroma_ac_cbf_cb: [false; 4],
                chroma_ac_cbf_cr: [false; 4],
                abs_mvd_x: 0,
                abs_mvd_y: 0,
            });
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::I, 0, 26);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut prev: Option<MbNeighbourState> = None;
        for (i, expected) in mbs.iter().enumerate() {
            let (got, _, cbf) = decode_i_nxn_mb(&mut dec, &mut dec_ctxs, prev.as_ref(), None);
            assert_eq!(got.cbp_luma, expected.cbp_luma, "MB {} cbp_luma", i);
            for j in 0..16 {
                for k in 0..16 {
                    assert_eq!(
                        got.luma_4x4[j][k], expected.luma_4x4[j][k],
                        "MB {} luma[{}][{}]",
                        i, j, k,
                    );
                }
            }
            let _ = cbf; // silence-unused; the next iteration's prev uses it
            prev = Some(MbNeighbourState {
                mb_type_is_i_nxn: Some(true),
                cbp_luma: got.cbp_luma,
                cbp_chroma: got.cbp_chroma,
                intra_chroma_mode: Some(got.intra_chroma_pred_mode),
                mb_qp_delta_was_zero: got.mb_qp_delta == 0,
                luma_cbf: cbf,
                luma_dc_cbf: false,
                chroma_dc_cbf_cb: false,
                chroma_dc_cbf_cr: false,
                chroma_ac_cbf_cb: [false; 4],
                chroma_ac_cbf_cr: [false; 4],
                abs_mvd_x: 0,
                abs_mvd_y: 0,
            });
        }
    }

    /// Mixed: alternate context bins and bypass bins. Encoder state
    /// must round-trip through both modes.
    #[test]
    fn mixed_round_trip_context_and_bypass() {
        let mut ctx_a = CabacCtx {
            p_state_idx: 5,
            val_mps: 1,
        };
        let mut ctx_b = CabacCtx {
            p_state_idx: 30,
            val_mps: 0,
        };
        let mut enc = CabacEncoder::new();
        for i in 0..16 {
            enc.encode_bin(&mut ctx_a, ((i * 7) & 1) as u8);
            enc.encode_bypass((i & 1) as u8);
            enc.encode_bin(&mut ctx_b, ((i * 3) & 1) as u8);
        }
        enc.finish();

        let mut dec_a = CabacCtx {
            p_state_idx: 5,
            val_mps: 1,
        };
        let mut dec_b = CabacCtx {
            p_state_idx: 30,
            val_mps: 0,
        };
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        for i in 0..16 {
            assert_eq!(dec.decode_bin(&mut dec_a), ((i * 7) & 1) as u8);
            assert_eq!(dec.decode_bypass(), (i & 1) as u8);
            assert_eq!(dec.decode_bin(&mut dec_b), ((i * 3) & 1) as u8);
        }
    }
}
