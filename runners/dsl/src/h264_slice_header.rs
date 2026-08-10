//! H.264 slice header walker, native in the Rust runner.
//!
//! Per ITU-T H.264 §7.3.3 the slice header has a deeply conditional
//! structure depending on SPS + PPS state. The dominant fields the
//! CABAC primitive stack needs from it are:
//!
//!   slice_type        — drives context initialisation table choice
//!   slice_qp_delta    — combined with pic_init_qp_minus26 to give SliceQPY
//!   cabac_init_idc    — drives PB table selection for P/B slices
//!
//! Two structural reasons this lives as a dedicated Rust function
//! rather than a graph FieldSpec chain:
//!
//!   1. Variable-width u(v) fields whose width derives from SPS
//!      values (`frame_num` and `pic_order_cnt_lsb`). Could be
//!      handled by parameterising the grammar at construction time,
//!      but pushes width-resolution into Python.
//!
//!   2. Loop-until-terminator sub-structures
//!      (`ref_pic_list_modification` reads ue(v) modifications until
//!      it reads `3`; `dec_ref_pic_marking` reads ops until it reads
//!      `0`). The existing loop construct expects a count-from-state,
//!      not a content-terminated loop.
//!
//! Both extensions are tractable but the slice header is enough of
//! a one-off (per-codec, with codec-specific conditionals) that a
//! dedicated walker is the simpler architectural answer.

use serde_json::{Map, Value as JsonValue};
use std::collections::HashMap;

/// Bit-reader over an RBSP byte slice. The reader API matches the
/// H.264 spec naming: u(n), ue(v), se(v).
struct BitReader<'a> {
    data: &'a [u8],
    bp: usize,
}

impl<'a> BitReader<'a> {
    fn new(data: &'a [u8]) -> Self {
        BitReader { data, bp: 0 }
    }

    fn u(&mut self, n: usize) -> u64 {
        let mut val: u64 = 0;
        for k in 0..n {
            let byte = self.data[(self.bp + k) >> 3];
            let bit = (byte >> (7 - ((self.bp + k) & 7))) & 1;
            val = (val << 1) | (bit as u64);
        }
        self.bp += n;
        val
    }

    fn ue(&mut self) -> u64 {
        let mut m = 0usize;
        while self.u(1) == 0 && m < 32 {
            m += 1;
        }
        if m == 0 { return 0; }
        let suffix = self.u(m);
        (1u64 << m) - 1 + suffix
    }

    fn se(&mut self) -> i64 {
        let u = self.ue();
        if u & 1 == 1 {
            ((u + 1) / 2) as i64
        } else {
            -((u / 2) as i64)
        }
    }
}

/// SPS+PPS state the slice header walker needs. Caller provides
/// these from a prior SPS/PPS parse.
pub struct H264SpsPpsContext {
    pub log2_max_frame_num: u32,
    pub pic_order_cnt_type: u32,
    pub log2_max_poc_lsb: u32,
    pub frame_mbs_only_flag: u32,
    pub bottom_field_pic_order_in_frame_present_flag: u32,
    pub redundant_pic_cnt_present_flag: u32,
    pub weighted_pred_flag: u32,
    pub weighted_bipred_idc: u32,
    pub entropy_coding_mode_flag: u32,
    pub deblocking_filter_control_present_flag: u32,
    pub num_ref_idx_l0_default_active_minus1: u32,
    pub num_ref_idx_l1_default_active_minus1: u32,
    pub pic_init_qp_minus26: i32,
    pub num_slice_groups_minus1: u32,
}

/// Decoded slice-header fields. Kept as a hash-map for ergonomic
/// JSON serialisation back to Python — the variable-presence
/// nature of these fields (conditional on slice type / IDR / SPS
/// flags) makes a struct awkward.
pub fn walk_h264_slice_header(
    rbsp: &[u8],
    sps_pps: &H264SpsPpsContext,
    nal_ref_idc: u8,
    is_idr: bool,
) -> Map<String, JsonValue> {
    let mut r = BitReader::new(rbsp);
    let mut out: Map<String, JsonValue> = Map::new();

    out.insert("first_mb_in_slice".into(), r.ue().into());
    let slice_type_raw = r.ue();
    out.insert("slice_type_raw".into(), slice_type_raw.into());
    let slice_type_mod5 = (slice_type_raw % 5) as u32;
    out.insert("slice_type_mod5".into(), slice_type_mod5.into());
    out.insert("pps_id".into(), r.ue().into());

    let frame_num = r.u(sps_pps.log2_max_frame_num as usize);
    out.insert("frame_num".into(), frame_num.into());

    let mut field_pic_flag = 0u64;
    if sps_pps.frame_mbs_only_flag == 0 {
        field_pic_flag = r.u(1);
        out.insert("field_pic_flag".into(), field_pic_flag.into());
        if field_pic_flag == 1 {
            out.insert("bottom_field_flag".into(), r.u(1).into());
        }
    }

    if is_idr {
        out.insert("idr_pic_id".into(), r.ue().into());
    }

    if sps_pps.pic_order_cnt_type == 0 {
        let poc_lsb = r.u(sps_pps.log2_max_poc_lsb as usize);
        out.insert("pic_order_cnt_lsb".into(), poc_lsb.into());
        if sps_pps.bottom_field_pic_order_in_frame_present_flag == 1
            && field_pic_flag == 0
        {
            out.insert("delta_pic_order_cnt_bottom".into(), r.se().into());
        }
    }

    if sps_pps.redundant_pic_cnt_present_flag == 1 {
        out.insert("redundant_pic_cnt".into(), r.ue().into());
    }

    let is_b = slice_type_mod5 == 1;
    if is_b {
        out.insert("direct_spatial_mv_pred_flag".into(), r.u(1).into());
    }

    // num_ref_idx for P / SP / B
    let is_pspb = slice_type_mod5 == 0 || slice_type_mod5 == 3 || is_b;
    let mut num_ref_l0 = sps_pps.num_ref_idx_l0_default_active_minus1;
    let mut num_ref_l1 = sps_pps.num_ref_idx_l1_default_active_minus1;
    if is_pspb {
        let override_flag = r.u(1);
        out.insert(
            "num_ref_idx_active_override_flag".into(),
            override_flag.into(),
        );
        if override_flag == 1 {
            num_ref_l0 = r.ue() as u32;
            out.insert(
                "num_ref_idx_l0_active_minus1".into(),
                num_ref_l0.into(),
            );
            if is_b {
                num_ref_l1 = r.ue() as u32;
                out.insert(
                    "num_ref_idx_l1_active_minus1".into(),
                    num_ref_l1.into(),
                );
            }
        }
    }

    // ref_pic_list_modification — loop-until-terminator.
    // l0 modification (P/SP/B)
    if slice_type_mod5 != 2 && slice_type_mod5 != 4 {
        let flag = r.u(1);
        if flag == 1 {
            loop {
                let idc = r.ue();
                if idc == 3 { break; }
                r.ue();  // abs_diff_pic_num_minus1 or long_term_pic_num
            }
        }
    }
    // l1 modification (B only)
    if is_b {
        let flag = r.u(1);
        if flag == 1 {
            loop {
                let idc = r.ue();
                if idc == 3 { break; }
                r.ue();
            }
        }
    }

    // pred_weight_table — present when weighted prediction is on
    // for the slice's type.
    let weighted_p = sps_pps.weighted_pred_flag == 1
        && slice_type_mod5 == 0;
    let weighted_b = sps_pps.weighted_bipred_idc == 1 && is_b;
    if weighted_p || weighted_b {
        r.ue();  // luma_log2_weight_denom
        r.ue();  // chroma_log2_weight_denom (assume ChromaArrayType > 0)
        for _ in 0..=num_ref_l0 {
            let luma_wflag = r.u(1);
            if luma_wflag == 1 {
                r.se(); r.se();
            }
            let chroma_wflag = r.u(1);
            if chroma_wflag == 1 {
                for _ in 0..2 {
                    r.se(); r.se();
                }
            }
        }
        if is_b {
            for _ in 0..=num_ref_l1 {
                let luma_wflag = r.u(1);
                if luma_wflag == 1 {
                    r.se(); r.se();
                }
                let chroma_wflag = r.u(1);
                if chroma_wflag == 1 {
                    for _ in 0..2 {
                        r.se(); r.se();
                    }
                }
            }
        }
    }

    // dec_ref_pic_marking — present when nal_ref_idc != 0.
    if nal_ref_idc != 0 {
        if is_idr {
            r.u(1);  // no_output_of_prior_pics_flag
            r.u(1);  // long_term_reference_flag
        } else {
            let adaptive = r.u(1);
            if adaptive == 1 {
                // Loop-until-terminator (op == 0).
                loop {
                    let op = r.ue();
                    if op == 0 { break; }
                    if op == 1 || op == 3 { r.ue(); }
                    if op == 2 { r.ue(); }
                    if op == 3 || op == 6 { r.ue(); }
                    if op == 4 { r.ue(); }
                    // op 5: no further fields
                }
            }
        }
    }

    // cabac_init_idc — CABAC and not I/SI slice.
    if sps_pps.entropy_coding_mode_flag == 1
        && slice_type_mod5 != 2
        && slice_type_mod5 != 4
    {
        out.insert("cabac_init_idc".into(), r.ue().into());
    }

    let qp_delta = r.se();
    out.insert("slice_qp_delta".into(), qp_delta.into());
    out.insert(
        "slice_qp".into(),
        (sps_pps.pic_init_qp_minus26 + 26 + qp_delta as i32).into(),
    );

    if sps_pps.deblocking_filter_control_present_flag == 1 {
        let deblock_idc = r.ue();
        out.insert("disable_deblocking_filter_idc".into(), deblock_idc.into());
        if deblock_idc != 1 {
            let alpha = r.se();  // slice_alpha_c0_offset_div2
            let beta = r.se();   // slice_beta_offset_div2
            out.insert("slice_alpha_c0_offset_div2".into(), alpha.into());
            out.insert("slice_beta_offset_div2".into(), beta.into());
        }
    }

    out.insert("header_end_bp".into(), r.bp.into());

    // CABAC payload starts at the next byte boundary, after
    // cabac_alignment_one_bit padding.
    if sps_pps.entropy_coding_mode_flag == 1 {
        while r.bp & 7 != 0 {
            r.u(1);
        }
    }
    out.insert("cabac_start_bp".into(), r.bp.into());

    out
}

/// Build a HashMap-keyed lookup of the same shape, used by the
/// Python binding to keep allocation count low.
pub fn walk_h264_slice_header_dict(
    rbsp: &[u8],
    sps_pps: &H264SpsPpsContext,
    nal_ref_idc: u8,
    is_idr: bool,
) -> HashMap<String, i64> {
    let m = walk_h264_slice_header(rbsp, sps_pps, nal_ref_idc, is_idr);
    let mut out: HashMap<String, i64> = HashMap::new();
    for (k, v) in m {
        if let Some(n) = v.as_i64() {
            out.insert(k, n);
        } else if let Some(n) = v.as_u64() {
            out.insert(k, n as i64);
        }
    }
    out
}
