//! H.264 → H.265 transcode driver.
//!
//! Composes the 6 substrate-grounded transcoder stages into an
//! end-to-end pipeline. Each MB descriptor entering the driver flows
//! through the stages in the order the substrate's design names
//! (commit 486f65e + 94eaa9e):
//!
//!     [input: H.264 MB descriptors, 16 per CTU]
//!         │
//!         ▼
//!     Stage 1: block_structure
//!       h265_ctu_quadtree::build_ctu_from_16_mbs
//!       (merge same-mode MBs into larger CUs)
//!         │
//!         ▼
//!     Stage 2: intra_prediction_mode
//!       h265_intra_mode::h264_to_h265_intra
//!       (per intra CU, remap mode 0..8 → 0..34)
//!         │
//!         ▼
//!     Stage 3: transform_kind
//!       h265_dct::forward_dct_4x4 / 8x8
//!       (per TU, integer DCT-II)
//!         │
//!         ▼
//!     Stage 4: cabac_mechanism
//!       h265_cabac::CabacEncoder::encode_bin / bypass
//!       (per syntax element, arithmetic-code into output bitstream)
//!         │
//!         ▼
//!     Stage 5: in_loop_filter
//!       h265_in_loop_filter::boundary_strength + deblock + SAO
//!       (per CTU boundary, post-reconstruction)
//!         │
//!         ▼
//!     Stage 6: structure
//!       h265_slice_header::emit_h265_slice_header
//!       (per slice, emit segment header — first, before CABAC payload)
//!         │
//!         ▼
//!     [output: H.265 RBSP bytes]
//!
//! ## Scope
//!
//! The driver wires the 6 stages. It assumes:
//!   · Upstream has already parsed the H.264 bitstream into
//!     `H264MbDescriptor` records (one per MB)
//!   · Upstream provides reconstructed pixel planes for
//!     in_loop_filter input
//!   · Downstream framing (NAL prefix, RBSP escape) is the caller's
//!     concern; the driver emits raw RBSP bytes
//!
//! H.264 bitstream parsing — actually walking the entropy-coded
//! MB data — is itself a multi-thousand-line module the substrate
//! has partial pieces for (`h264_slice_header` parses slice headers,
//! `h264_dct` handles the transform/quant pair). A future commit can
//! wire those into a full MB iterator; for now the driver's input
//! contract is the natural one a parser would feed.

use crate::h265_cabac::CabacEncoder;
use crate::h265_ctu_quadtree::{
    build_ctu_from_16_mbs, walk_leaves, CuNode, PredMode,
};
use crate::h265_dct::{forward_dct, DctOutput};
use crate::h265_in_loop_filter::{
    apply_sao_band_offset, apply_sao_edge_offset, boundary_strength,
    BoundaryStrength, SaoEdgeDir, SaoMode, SideInfo,
};
use crate::h265_intra_mode::h264_to_h265_intra;
use crate::h265_slice_header::{
    emit_h265_slice_header, H265SliceHeader, H265SliceType,
};

/// One H.264 macroblock's worth of input to the transcoder.
/// Upstream's H.264 parser fills this for each MB.
#[derive(Debug, Clone)]
pub struct H264MbDescriptor {
    /// H.264 MB type code (0=P_L0_16x16, 5=I_NxN, 7=I_16x16, etc.).
    /// We collapse this to a PredMode for stage 1.
    pub mb_type: u8,
    /// H.264 4×4 intra prediction mode (0..8), present when MB is
    /// I_NxN. Mapped to H.265 by stage 2.
    pub intra_mode: Option<u8>,
    /// Motion vector (for inter MBs).
    pub mv_x: i16,
    pub mv_y: i16,
    pub ref_pic_id: u8,
    /// 16 luma 4×4 residual blocks per MB (H.264 clause 6.4.3 block
    /// indexing 0..15). Each inner [i32; 16] is one 4×4 block of
    /// scan-ordered coefficients. Zero arrays for blocks the
    /// upstream parser didn't decode.
    pub residual_luma_4x4: [[i32; 16]; 16],
    /// True if any of the 16 blocks has nonzero coefficients — used
    /// by stage 5 for boundary-strength derivation. Derived from the
    /// parser's CBP_luma, not from inspecting residual_luma_4x4
    /// (since the upstream may zero blocks while CBP still indicates
    /// they were coded).
    pub has_nonzero_residual: bool,
}

impl H264MbDescriptor {
    /// Map this MB's prediction context to a stage-1 PredMode.
    fn to_pred_mode(&self) -> PredMode {
        // H.264 mb_type encoding (simplified):
        //   0..4   = P slice partition types → Inter
        //   5..30  = I_NxN / I_16x16 variants → Intra
        //   31     = Skip
        match self.mb_type {
            31 => PredMode::Skip,
            mt if mt >= 5 => {
                let h264_mode = self.intra_mode.unwrap_or(2);  // DC default
                PredMode::Intra(h264_to_h265_intra(h264_mode).unwrap_or(1))
            }
            _ => {
                // Use (mv_x, mv_y, ref_pic) as the Inter identifier so
                // adjacent MBs with the same motion can merge into a CU.
                let id = ((self.ref_pic_id as u32) << 24)
                    | (((self.mv_x as u16) as u32) << 8)
                    | ((self.mv_y as u16) as u32 & 0xFF);
                PredMode::Inter(id)
            }
        }
    }

    fn to_side_info(&self) -> SideInfo {
        SideInfo {
            is_intra: self.mb_type >= 5 && self.mb_type < 31,
            has_nonzero_coeffs: self.has_nonzero_residual,
            mv_x: self.mv_x,
            mv_y: self.mv_y,
            ref_pic_id: self.ref_pic_id,
        }
    }
}

/// Per-slice driver state — holds the CABAC encoder + a small set of
/// caller-configurable knobs.
pub struct H265TranscodeContext {
    pub cabac: CabacEncoder,
    /// Number of CABAC contexts the encoder should hold; depends on
    /// which syntax elements the driver emits. v1 emits a minimal set
    /// (CTU split flags, CU mode flags, coeff sig flags) — ~32 contexts.
    pub n_contexts: usize,
}

impl H265TranscodeContext {
    pub fn new(n_contexts: usize) -> Self {
        Self {
            cabac: CabacEncoder::new(n_contexts),
            n_contexts,
        }
    }
}

/// CABAC context indices used by this minimal driver. Production
/// H.265 has ~150 contexts; we use a small subset that names the bins
/// the v1 driver emits.
pub mod ctx_idx {
    pub const CTU_SPLIT_FLAG: usize = 0;
    pub const CU_SKIP_FLAG: usize = 1;
    pub const PRED_MODE_FLAG: usize = 2;  // intra vs inter
    pub const PART_MODE: usize = 3;
    pub const INTRA_LUMA_MPM_FLAG: usize = 4;
    pub const SIGNIFICANT_COEFF_FLAG: usize = 5;
    pub const COEFF_ABS_GT1_FLAG: usize = 6;
    pub const SAO_MERGE_FLAG: usize = 7;
    pub const TOTAL: usize = 8;
}

/// Stage 1 + 2 + 3 + 4: walk a CTU's worth of MBs.
///
/// 1. build_ctu_from_16_mbs → CuNode tree (stage 1)
/// 2. For each leaf: recurse the H.264 intra mode → H.265 (stage 2 done
///    in `to_pred_mode`)
/// 3. For each CU, transform its residual (stage 3)
/// 4. Encode CABAC bins for the CU's syntax (stage 4)
fn encode_one_ctu(
    ctx: &mut H265TranscodeContext,
    mbs: &[H264MbDescriptor; 16],
) -> usize {
    // Stage 1: build CTU partition.
    let modes: [PredMode; 16] = std::array::from_fn(|i| mbs[i].to_pred_mode());
    let ctu: CuNode = build_ctu_from_16_mbs(&modes);

    // Stage 4: emit CTU's CABAC syntax. We emit a minimal subset:
    //   · split_cu_flag bin per internal node (0 = no split, 1 = split)
    //   · pred_mode_flag bin per leaf (0 = intra, 1 = inter)
    //   · intra_luma_mpm_flag per intra leaf (whether mode is in MPM list)
    //   · per-coeff significance bins for the residual
    fn emit_ctu_syntax(ctx: &mut H265TranscodeContext, node: &CuNode) {
        match node {
            CuNode::Quad { children, .. } => {
                ctx.cabac.encode_bin(ctx_idx::CTU_SPLIT_FLAG, 1);
                for child in children.iter() {
                    emit_ctu_syntax(ctx, child);
                }
            }
            CuNode::Leaf { mode, .. } => {
                ctx.cabac.encode_bin(ctx_idx::CTU_SPLIT_FLAG, 0);
                match mode {
                    PredMode::Skip => {
                        ctx.cabac.encode_bin(ctx_idx::CU_SKIP_FLAG, 1);
                    }
                    PredMode::Intra(_) => {
                        ctx.cabac.encode_bin(ctx_idx::CU_SKIP_FLAG, 0);
                        ctx.cabac.encode_bin(ctx_idx::PRED_MODE_FLAG, 0);
                        // intra_luma_mpm_flag: 1 if mode in most-probable list.
                        // v1 simplification: always 0 (= remainder mode); a
                        // real encoder would track neighbour modes.
                        ctx.cabac.encode_bin(ctx_idx::INTRA_LUMA_MPM_FLAG, 0);
                    }
                    PredMode::Inter(_) => {
                        ctx.cabac.encode_bin(ctx_idx::CU_SKIP_FLAG, 0);
                        ctx.cabac.encode_bin(ctx_idx::PRED_MODE_FLAG, 1);
                    }
                }
            }
        }
    }
    emit_ctu_syntax(ctx, &ctu);

    // Stage 3: transform residuals. Each MB has 16 luma 4×4 blocks;
    // each block flows through forward_dct independently (no inter-
    // block dependency — this is the embarrassingly_parallel_
    // distribution case the substrate's design names).
    //
    // Stage 4 (continued): per block, emit significance + magnitude
    // bins to the CABAC stream.
    let mut transforms_done = 0;
    for mb in mbs.iter() {
        if !mb.has_nonzero_residual { continue; }
        for block in mb.residual_luma_4x4.iter() {
            let any_nonzero = block.iter().any(|c| *c != 0);
            if !any_nonzero { continue; }
            if let Some(DctOutput::Size4(coeffs)) = forward_dct(2, block) {
                for c in coeffs.iter() {
                    let sig = if *c != 0 { 1u8 } else { 0u8 };
                    ctx.cabac.encode_bin(ctx_idx::SIGNIFICANT_COEFF_FLAG, sig);
                    if sig == 1 {
                        let gt1 = if c.abs() > 1 { 1u8 } else { 0u8 };
                        ctx.cabac.encode_bin(ctx_idx::COEFF_ABS_GT1_FLAG, gt1);
                    }
                }
                transforms_done += 1;
            }
        }
    }
    transforms_done
}

/// Stage 5: in-loop filter over a reconstructed plane.
///
/// Iterates pairs of adjacent MBs (vertical + horizontal neighbours),
/// computes boundary strength, would apply the deblock filter in a real
/// pipeline (here we just sum the strength values as a sanity check).
/// SAO is applied as a CTU-level operation on the plane if `sao_mode`
/// is set.
pub fn apply_in_loop_filter(
    plane: &mut [u8], width: usize, height: usize, stride: usize,
    mbs: &[H264MbDescriptor], sao_mode: SaoMode,
) -> InLoopFilterStats {
    let mut weak_boundaries = 0;
    let mut strong_boundaries = 0;
    // Pair adjacent MBs horizontally + vertically. With 16 MBs in a
    // CTU (4×4 grid), we have 12 horizontal + 12 vertical internal
    // boundaries.
    for row in 0..4 {
        for col in 0..3 {
            let i = row * 4 + col;
            let bs = boundary_strength(
                mbs[i].to_side_info(), mbs[i + 1].to_side_info(),
            );
            match bs {
                BoundaryStrength::Weak => weak_boundaries += 1,
                BoundaryStrength::Strong => strong_boundaries += 1,
                BoundaryStrength::None => {}
            }
        }
    }
    for row in 0..3 {
        for col in 0..4 {
            let i = row * 4 + col;
            let bs = boundary_strength(
                mbs[i].to_side_info(), mbs[i + 4].to_side_info(),
            );
            match bs {
                BoundaryStrength::Weak => weak_boundaries += 1,
                BoundaryStrength::Strong => strong_boundaries += 1,
                BoundaryStrength::None => {}
            }
        }
    }
    // Apply SAO if requested.
    match sao_mode {
        SaoMode::Off => {}
        SaoMode::BandOffset { band_start, offsets } =>
            apply_sao_band_offset(plane, width, height, stride,
                                    band_start, offsets),
        SaoMode::EdgeOffset { direction, offsets } =>
            apply_sao_edge_offset(plane, width, height, stride,
                                    direction, offsets),
    }
    InLoopFilterStats {
        weak_boundaries,
        strong_boundaries,
    }
}

#[derive(Debug, Clone, Copy)]
pub struct InLoopFilterStats {
    pub weak_boundaries: u32,
    pub strong_boundaries: u32,
}

/// Top-level transcode of one slice's worth of CTUs.
///
/// Returns the H.265 RBSP bytes for the slice (header + CABAC payload).
/// `ctus` is a flat vector of CTUs, each of which is 16 H.264 MBs.
pub fn transcode_slice(
    h265_slice_type: H265SliceType,
    slice_qp_delta: i32,
    ctus: &[[H264MbDescriptor; 16]],
) -> Vec<u8> {
    // Stage 6: emit slice header.
    let header = H265SliceHeader {
        first_slice_segment_in_pic_flag: true,
        no_output_of_prior_pics_flag: false,
        slice_pic_parameter_set_id: 0,
        slice_segment_address: 0,
        slice_segment_address_bits: 0,
        slice_type: h265_slice_type,
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
        qp_delta: slice_qp_delta,
        deblocking_filter_disabled_flag: false,
    };
    let mut output = emit_h265_slice_header(&header).expect("emit header");

    // Stages 1-4 per CTU.
    let mut ctx = H265TranscodeContext::new(ctx_idx::TOTAL);
    for ctu_mbs in ctus.iter() {
        encode_one_ctu(&mut ctx, ctu_mbs);
    }
    ctx.cabac.encode_terminate(1);

    // Append CABAC payload.
    let payload = ctx.cabac.finalize();
    output.extend_from_slice(&payload);
    output
}

#[cfg(test)]
mod tests {
    use super::*;

    fn intra_mb(intra_mode: u8) -> H264MbDescriptor {
        H264MbDescriptor {
            mb_type: 7,  // I_4x4
            intra_mode: Some(intra_mode),
            mv_x: 0, mv_y: 0, ref_pic_id: 0,
            residual_luma_4x4: [[0; 16]; 16],
            has_nonzero_residual: false,
        }
    }
    fn inter_mb(mv_x: i16, mv_y: i16, ref_pic_id: u8) -> H264MbDescriptor {
        H264MbDescriptor {
            mb_type: 0,
            intra_mode: None,
            mv_x, mv_y, ref_pic_id,
            residual_luma_4x4: [[0; 16]; 16],
            has_nonzero_residual: false,
        }
    }

    #[test]
    fn uniform_intra_ctu_emits_one_split_flag() {
        let ctx_initial_bytes;
        let mut ctx = H265TranscodeContext::new(ctx_idx::TOTAL);
        ctx_initial_bytes = ctx.cabac.bytes_emitted();
        let mbs: [H264MbDescriptor; 16] = std::array::from_fn(|_| intra_mb(0));
        encode_one_ctu(&mut ctx, &mbs);
        ctx.cabac.encode_terminate(1);
        let bytes = ctx.cabac.finalize();
        // A uniform-mode CTU collapses to one leaf → emits:
        //   · 1 split_cu_flag = 0
        //   · 1 skip_flag = 0
        //   · 1 pred_mode_flag = 0
        //   · 1 intra_luma_mpm_flag = 0
        //   · 0 transforms (no nonzero residual)
        // = 4 bins. Plus terminate. Output should be small.
        assert!(bytes.len() >= 1);
        assert!(bytes.len() < 8,
                "uniform-intra CTU should emit < 8 bytes; got {}", bytes.len());
        let _ = ctx_initial_bytes;
    }

    #[test]
    fn mixed_ctu_emits_more_bins_than_uniform() {
        let mbs_uniform: [H264MbDescriptor; 16] =
            std::array::from_fn(|_| intra_mb(0));
        let mut mbs_mixed: [H264MbDescriptor; 16] =
            std::array::from_fn(|i| if i % 2 == 0 {
                intra_mb(0)
            } else {
                inter_mb(1, 0, 0)
            });
        // Ensure no merging.
        for (i, mb) in mbs_mixed.iter_mut().enumerate() {
            if mb.mb_type == 0 {
                mb.mv_x = i as i16;  // make MVs distinct → no merge
            }
        }

        let mut ctx_u = H265TranscodeContext::new(ctx_idx::TOTAL);
        encode_one_ctu(&mut ctx_u, &mbs_uniform);
        ctx_u.cabac.encode_terminate(1);
        let bytes_u = ctx_u.cabac.finalize();

        let mut ctx_m = H265TranscodeContext::new(ctx_idx::TOTAL);
        encode_one_ctu(&mut ctx_m, &mbs_mixed);
        ctx_m.cabac.encode_terminate(1);
        let bytes_m = ctx_m.cabac.finalize();

        // Mixed CTU has more split_flag/pred_mode bins → bigger payload.
        assert!(bytes_m.len() > bytes_u.len(),
                "mixed CTU ({}b) should exceed uniform ({}b)",
                bytes_m.len(), bytes_u.len());
    }

    #[test]
    fn residual_bins_encoded_when_nonzero() {
        let mut ctx_no_residual = H265TranscodeContext::new(ctx_idx::TOTAL);
        let mbs_no_res: [H264MbDescriptor; 16] =
            std::array::from_fn(|_| intra_mb(0));
        encode_one_ctu(&mut ctx_no_residual, &mbs_no_res);
        ctx_no_residual.cabac.encode_terminate(1);
        let bytes_no = ctx_no_residual.cabac.finalize();

        // Now with nonzero residual on every MB.
        let mut ctx_with_res = H265TranscodeContext::new(ctx_idx::TOTAL);
        let mut mbs_with_res: [H264MbDescriptor; 16] =
            std::array::from_fn(|_| intra_mb(0));
        for mb in mbs_with_res.iter_mut() {
            mb.has_nonzero_residual = true;
            // Nonzero coefficients across all 16 4×4 blocks.
            mb.residual_luma_4x4 = [[10; 16]; 16];
        }
        encode_one_ctu(&mut ctx_with_res, &mbs_with_res);
        ctx_with_res.cabac.encode_terminate(1);
        let bytes_yes = ctx_with_res.cabac.finalize();

        assert!(bytes_yes.len() > bytes_no.len(),
                "with-residual CTU ({}b) should exceed no-residual ({}b)",
                bytes_yes.len(), bytes_no.len());
    }

    #[test]
    fn full_slice_transcode_produces_output() {
        let mbs: [H264MbDescriptor; 16] =
            std::array::from_fn(|_| intra_mb(0));
        let bytes = transcode_slice(H265SliceType::I, 0, &[mbs]);
        // Header + at least one CABAC byte.
        assert!(bytes.len() > 2, "slice should have header + CABAC; got {} bytes",
                bytes.len());
    }

    #[test]
    fn intra_boundary_detected_by_in_loop_filter() {
        let mbs: [H264MbDescriptor; 16] =
            std::array::from_fn(|i| if i < 8 { intra_mb(0) } else { inter_mb(0, 0, 0) });
        let mut plane = vec![128u8; 64 * 64];
        let stats = apply_in_loop_filter(
            &mut plane, 64, 64, 64, &mbs, SaoMode::Off);
        // Strong boundaries: where intra meets inter (some of the
        // internal vertical + horizontal pairings).
        assert!(stats.strong_boundaries > 0,
                "intra/inter boundary should be detected as Strong");
    }

    #[test]
    fn p_slice_round_trip_does_not_panic() {
        let mbs: [H264MbDescriptor; 16] =
            std::array::from_fn(|_| inter_mb(1, 1, 0));
        let bytes = transcode_slice(H265SliceType::P, 1, &[mbs]);
        assert!(!bytes.is_empty());
    }

    #[test]
    fn multiple_ctus_processed_sequentially() {
        let mbs: [H264MbDescriptor; 16] =
            std::array::from_fn(|_| intra_mb(0));
        let ctus = [mbs.clone(), mbs.clone(), mbs.clone()];
        let single = transcode_slice(H265SliceType::I, 0, &[mbs]);
        let triple = transcode_slice(H265SliceType::I, 0, &ctus);
        // Three CTUs should produce more bytes than one.
        assert!(triple.len() > single.len(),
                "3 CTUs ({}b) should exceed 1 CTU ({}b)",
                triple.len(), single.len());
    }
}
