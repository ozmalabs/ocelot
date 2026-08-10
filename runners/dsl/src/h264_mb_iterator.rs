//! H.264 macroblock iterator.
//!
//! Walks the entropy-coded MB data inside an H.264 slice + produces
//! `H264MbDescriptor` records the H.265 transcoder driver
//! (`h265_transcode_driver`) consumes. Closes the input-side gap
//! named at the end of commit df75e14.
//!
//! ## What this builds on
//!
//! Uses the substrate's existing H.264 CABAC primitives in `cabac.rs`:
//!   · `CabacDecoder` — arithmetic-decoder state + bit reader
//!   · `CabacCtx` — per-syntax-element probability context
//!   · `decode_p_mb_type` / `decode_i_mb_type_is_i_nxn` — MB type
//!   · `decode_prev_intra4x4_flag` + `decode_rem_intra4x4` — intra mode
//!   · `decode_cbp_luma` / `decode_cbp_chroma` — coded block pattern
//!   · `decode_mb_qp_delta` — QP adjustment
//!
//! These functions handle every CABAC arithmetic detail; the iterator
//! just sequences them per H.264 clause 7.3.4.
//!
//! ## Scope (v1)
//!
//! Covers:
//!   · I slices with I_NxN macroblocks (the common intra case)
//!   · P slices with mb_skip_flag + p_mb_type detection
//!   · Per-MB intra prediction mode for the first 4×4 block (the field
//!     the driver's intra-mode stage 2 consumes)
//!   · CBP-derived has_nonzero_residual
//!
//! Skips (for now):
//!   · Motion-vector parsing (MV defaults to 0 for inter MBs)
//!   · Per-MB residual coefficient decode (residual_4x4 = zeros;
//!     has_nonzero_residual still reflects CBP truthfully)
//!   · I_16x16 / I_PCM / I_BL paths
//!   · B-slice MB types
//!
//! Each of these is a clean follow-up: the encode side has matching
//! functions in `cabac.rs` already; the iterator's structure just
//! needs additional decode calls.
//!
//! ## CABAC context indices (subset used here)
//!
//! From the substrate's `cabac.rs` constants + H.264 standard Table 9-34.

use crate::cabac::{
    CabacCtx, CabacDecoder, CabacSliceType, CtxBlockCat,
    mb_skip_flag_ctx_offset, mb_skip_flag_ctx_idx,
    decode_p_mb_type, decode_i_mb_type_is_i_nxn,
    decode_prev_intra4x4_flag, decode_rem_intra4x4,
    decode_cbp_luma, decode_cbp_chroma,
    decode_mb_qp_delta, decode_coded_block_flag,
    decode_residual_block, res_block_spec,
    decode_mvd, MVD_L0_X_CTX_OFFSET, MVD_L0_Y_CTX_OFFSET,
};
#[cfg(test)]
use crate::cabac::{
    CabacEncoder, encode_i_mb_type_i_nxn, encode_prev_intra4x4_flag,
    encode_rem_intra4x4, encode_cbp_luma, encode_cbp_chroma,
    encode_mb_qp_delta, encode_coded_block_flag, encode_residual_block,
    encode_p_mb_type, encode_mvd,
};
use crate::h265_transcode_driver::H264MbDescriptor;

/// Number of CABAC contexts the iterator allocates. H.264 needs ~460
/// for a full decoder; v1 uses only the prefixes for the syntax
/// elements it decodes. Allocating the full set keeps array indexing
/// safe across the existing helper functions in `cabac.rs`.
const N_CONTEXTS: usize = 460;

/// State the iterator maintains across MBs in the slice.
pub struct H264MbIterator {
    pub decoder: CabacDecoder,
    pub contexts: Vec<CabacCtx>,
    pub slice_type: CabacSliceType,
    pub slice_qp: i32,
    /// Total MBs the slice claims (from slice header `num_mbs_in_slice`).
    pub mb_count: usize,
    /// How many MBs already returned.
    pub mbs_decoded: usize,
    /// Picture width in MBs. Used for the MV-prediction grid + row
    /// wrap-around. Pass from the SPS (pic_width_in_mbs_minus1 + 1).
    /// When 0, the iterator treats the slice as a single row with no
    /// top neighbours.
    pub pic_width_in_mbs: u32,
    /// Whether the previous MB had a non-zero QP delta — used as
    /// neighbour info by `decode_mb_qp_delta`.
    pub prev_mb_qp_delta_nonzero: bool,
    /// Whether the left neighbour MB was I_NxN — used as ctx-inc
    /// input for I_NxN type decoding.
    pub left_is_i_nxn: Option<bool>,
    /// Whether the top neighbour MB was I_NxN — same purpose.
    pub top_is_i_nxn: Option<bool>,
    /// mb_skip_flag of left neighbour (for ctx-inc).
    pub left_mb_skip: bool,
    pub top_mb_skip: bool,
    /// MV grid (one row's worth). Within row y, entries 0..mb_x hold
    /// the CURRENT row's absolute MVs (left-neighbour material);
    /// entries mb_x..pic_width hold the PREVIOUS row's (top/top-right
    /// neighbour material). Per clause 8.4.1.3 derivation of mvpLX,
    /// intra-coded MBs contribute (0, 0) (treated as unavailable for
    /// MV prediction).
    mv_grid: Vec<(i16, i16)>,
}

impl H264MbIterator {
    /// Construct an iterator over a slice. `rbsp` is the slice's
    /// raw byte stream starting at the byte aligned position after
    /// the slice header. `bit_pos` is the bit offset into `rbsp`
    /// where the CABAC payload begins (per clause 9.3.1.2 this is
    /// the byte boundary after the slice-header RBSP trailing bits).
    ///
    /// Defaults `pic_width_in_mbs = mb_count` — single row, no top
    /// neighbours. For multi-row slices the caller should use
    /// `with_pic_width` to pass the real picture width.
    pub fn new(
        rbsp: Vec<u8>, bit_pos: u64,
        slice_type: CabacSliceType, slice_qp: i32,
        mb_count: usize,
    ) -> Self {
        Self::with_pic_width(rbsp, bit_pos, slice_type, slice_qp,
                              mb_count, mb_count as u32)
    }

    /// Construct with explicit picture-width-in-MBs from the SPS. The
    /// iterator uses this to maintain the MV-prediction grid + apply
    /// neighbour-aware MV prediction.
    pub fn with_pic_width(
        rbsp: Vec<u8>, bit_pos: u64,
        slice_type: CabacSliceType, slice_qp: i32,
        mb_count: usize, pic_width_in_mbs: u32,
    ) -> Self {
        // v1: all contexts equiprobable. Production transcoder seeds
        // via the standard's per-(initType, slice_qp) tables.
        let width = pic_width_in_mbs.max(1) as usize;
        Self {
            decoder: CabacDecoder::new(rbsp, bit_pos),
            contexts: vec![CabacCtx::default(); N_CONTEXTS],
            slice_type, slice_qp, mb_count,
            mbs_decoded: 0,
            pic_width_in_mbs,
            prev_mb_qp_delta_nonzero: false,
            left_is_i_nxn: None,
            top_is_i_nxn: None,
            left_mb_skip: false,
            top_mb_skip: false,
            mv_grid: vec![(0, 0); width],
        }
    }

    /// Decode one macroblock + return its descriptor. Returns `None`
    /// when the slice's MB count is exhausted.
    pub fn next_mb(&mut self) -> Option<H264MbDescriptor> {
        if self.mbs_decoded >= self.mb_count {
            return None;
        }
        let mb = self.decode_one_mb();
        self.mbs_decoded += 1;
        Some(mb)
    }

    fn decode_one_mb(&mut self) -> H264MbDescriptor {
        // 1. mb_skip_flag (P/B slices only).
        let is_skip = if mb_skip_flag_ctx_offset(self.slice_type).is_some() {
            if let Some(ctx_idx) = mb_skip_flag_ctx_idx(
                self.slice_type,
                Some(self.left_mb_skip as u8),
                Some(self.top_mb_skip as u8))
            {
                let bin = self.decoder.decode_bin(
                    &mut self.contexts[ctx_idx]);
                self.left_mb_skip = bin == 1;
                bin == 1
            } else {
                false
            }
        } else {
            false
        };

        if is_skip {
            return H264MbDescriptor {
                mb_type: 31,  // Skip
                intra_mode: None,
                mv_x: 0, mv_y: 0, ref_pic_id: 0,
                residual_luma_4x4: [[0; 16]; 16],
                has_nonzero_residual: false,
            };
        }

        // 2. mb_type — branches by slice type.
        let (mb_type, intra_mode) = match self.slice_type {
            CabacSliceType::I => self.decode_i_slice_mb(),
            CabacSliceType::P => self.decode_p_slice_mb(),
            CabacSliceType::B => {
                // v1: B slice falls through to a P-style decode +
                // returns it as inter. Real B parsing is its own
                // commit.
                (0u8, None)
            }
        };

        // 2b. Motion vector decode for P_L0_16x16. The substrate's
        // design names CABAC MV decode as part of stage 4
        // (cabac_mechanism) — sequential per-stream.
        //
        // Neighbour-aware predictor per clause 8.4.1.3:
        //   absolute_MV = decoded_MVD + predicted_MV
        // where predicted_MV is the median of three neighbours
        // (left A, top B, top-right C). The decoder requires the
        // ABSOLUTE MV — not the raw MVD — for any downstream
        // stage that compares motion across MBs (substrate's
        // stage 1 merge decision in particular).
        //
        // Position within the slice:
        let mb_idx_in_slice = self.mbs_decoded as u32;
        let width = self.pic_width_in_mbs.max(1);
        let mb_x = (mb_idx_in_slice % width) as usize;
        let mb_y = (mb_idx_in_slice / width) as usize;
        let row_width = self.mv_grid.len();

        let (mut mv_x, mut mv_y) = (0i16, 0i16);
        if matches!(self.slice_type, CabacSliceType::P)
            && mb_type == 0  // P_L0_16x16
        {
            let (mvd_x, _) = decode_mvd(
                &mut self.decoder, &mut self.contexts,
                MVD_L0_X_CTX_OFFSET);
            let (mvd_y, _) = decode_mvd(
                &mut self.decoder, &mut self.contexts,
                MVD_L0_Y_CTX_OFFSET);
            // Neighbour predictor. Within row y, mv_grid[0..mb_x] is
            // the CURRENT row (left-neighbour material); mv_grid[mb_x..]
            // is the PREVIOUS row (top/top-right neighbour material).
            let a = if mb_x > 0 { self.mv_grid[mb_x - 1] } else { (0, 0) };
            let b = if mb_y > 0 { self.mv_grid[mb_x] } else { (0, 0) };
            let c = if mb_y > 0 && mb_x + 1 < row_width {
                self.mv_grid[mb_x + 1]
            } else {
                // C unavailable. Per clause 8.4.1.3 spec, D
                // substitutes; v1 simplification: use (0, 0). For
                // the bulk of MB positions C IS available; D-fallback
                // only matters at the right edge of multi-row slices.
                (0, 0)
            };
            // Special predictor cases (clause 8.4.1.3.1):
            //   When only one of {A, B, C} is available, predictor =
            //   that one. Otherwise: median3.
            let n_left = if mb_x > 0 { 1 } else { 0 };
            let n_top = if mb_y > 0 { 1 } else { 0 };
            let n_top_right = if mb_y > 0 && mb_x + 1 < row_width { 1 } else { 0 };
            let n_avail = n_left + n_top + n_top_right;
            let (pred_x, pred_y) = if n_avail == 1 {
                if n_left == 1 { a }
                else if n_top == 1 { b }
                else { c }
            } else {
                (median3(a.0, b.0, c.0), median3(a.1, b.1, c.1))
            };
            // Absolute MV = MVD + predicted.
            let abs_x = (mvd_x as i32) + (pred_x as i32);
            let abs_y = (mvd_y as i32) + (pred_y as i32);
            mv_x = abs_x.clamp(i16::MIN as i32, i16::MAX as i32) as i16;
            mv_y = abs_y.clamp(i16::MIN as i32, i16::MAX as i32) as i16;
        }
        // Update the MV grid at this position with the absolute MV.
        // Intra / Skip MBs contribute (0, 0) as required by clause
        // 8.4.1.3 (intra MBs are unavailable for MV prediction).
        if mb_x < row_width {
            self.mv_grid[mb_x] = (mv_x, mv_y);
        }

        // 3. Coded block pattern. v1 passes 0 for neighbour CBPs.
        let (cbp_luma, _) = decode_cbp_luma(
            &mut self.decoder, &mut self.contexts, 0, 0);
        let (_cbp_chroma, _) = decode_cbp_chroma(
            &mut self.decoder, &mut self.contexts, 0, 0);

        // 4. mb_qp_delta — only when at least one block is coded.
        let qp_delta_nonzero;
        if cbp_luma != 0 {
            let (delta, _) = decode_mb_qp_delta(
                &mut self.decoder, &mut self.contexts,
                self.prev_mb_qp_delta_nonzero);
            qp_delta_nonzero = delta != 0;
        } else {
            qp_delta_nonzero = false;
        }
        self.prev_mb_qp_delta_nonzero = qp_delta_nonzero;

        // 5. Residual coefficients. cbp_luma has 4 bits, one per
        // 8×8 region; each region holds four 4×4 luma blocks. The
        // iterator decodes every block whose 8×8 region's cbp bit is
        // set, captures each block's 16 coefficients into the
        // descriptor's residual_luma_4x4[block_idx] slot. Blocks
        // whose region's cbp bit is 0 stay zero. Block ordering
        // matches H.264 clause 6.4.3 (block_idx 0..15).
        let mut residual_luma_4x4 = [[0i32; 16]; 16];
        if cbp_luma != 0 {
            for block_idx in 0..16 {
                let region_8x8 = block_idx / 4;
                if (cbp_luma >> region_8x8) & 1 == 0 {
                    continue;
                }
                let (cbf, _) = decode_coded_block_flag(
                    &mut self.decoder, &mut self.contexts,
                    CtxBlockCat::Luma4x4,
                    None, None,
                );
                if !cbf {
                    continue;
                }
                let spec = res_block_spec(CtxBlockCat::Luma4x4);
                let (coefs, _) = decode_residual_block(
                    &mut self.decoder, &mut self.contexts, spec);
                for (i, c) in coefs.iter().take(16).enumerate() {
                    residual_luma_4x4[block_idx][i] = *c;
                }
            }
        }

        H264MbDescriptor {
            mb_type,
            intra_mode,
            mv_x, mv_y, ref_pic_id: 0,
            residual_luma_4x4,
            has_nonzero_residual: cbp_luma != 0,
        }
    }

    fn decode_i_slice_mb(&mut self) -> (u8, Option<u8>) {
        // For I slices: decode whether mb_type is I_NxN (the path the
        // v1 iterator handles). Other I types fall to a placeholder.
        let (is_i_nxn, _) = decode_i_mb_type_is_i_nxn(
            &mut self.decoder, &mut self.contexts,
            self.left_is_i_nxn, self.top_is_i_nxn,
        );
        self.left_is_i_nxn = Some(is_i_nxn);
        if is_i_nxn {
            // Decode the first 4×4 block's intra mode.
            let (prev_flag, _) = decode_prev_intra4x4_flag(
                &mut self.decoder, &mut self.contexts);
            let intra_mode = if prev_flag {
                // Predicted (MPM). v1: assume MPM = mode 0.
                0u8
            } else {
                let (rem, _) = decode_rem_intra4x4(
                    &mut self.decoder, &mut self.contexts);
                // rem_intra4x4 is 0..7; map to mode 1..8 by skipping
                // MPM slot.
                rem.min(7) + 1
            };
            (0u8, Some(intra_mode))
        } else {
            (1u8, None)
        }
    }

    fn decode_p_slice_mb(&mut self) -> (u8, Option<u8>) {
        let (mb_type, _bins) = decode_p_mb_type(
            &mut self.decoder, &mut self.contexts);
        (mb_type, None)
    }
}

/// Median of three i16 components — H.264 mvpLX derivation.
#[inline]
fn median3(a: i16, b: i16, c: i16) -> i16 {
    let max = a.max(b).max(c);
    let min = a.min(b).min(c);
    // Use i32 to avoid overflow when (a + b + c - max - min) approaches
    // i16 limits. Result always within range since it equals the median.
    ((a as i32) + (b as i32) + (c as i32)
        - (max as i32) - (min as i32)) as i16
}

impl Iterator for H264MbIterator {
    type Item = H264MbDescriptor;
    fn next(&mut self) -> Option<Self::Item> { self.next_mb() }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// Encode N I_NxN MBs with optional residual blocks. When
    /// `block_coefs` is `Some`, the encoder iterates the 16 4×4
    /// blocks per MB; each block whose 8×8 region's cbp bit is set
    /// is encoded as a coded_block_flag + (when nonzero) a
    /// residual_block of its own coefficients.
    ///
    /// `block_coefs` shape: `[[i32; 16]; 16]` — one 16-coef vector
    /// per 4×4 block, indexed by H.264 block_idx 0..15.
    fn encode_i_nxn_mbs(
        modes: &[u8],
        cbp_luma_each: u8,
        block_coefs: Option<&[[i32; 16]; 16]>,
    ) -> Vec<u8> {
        use crate::cabac::CtxBlockCat;
        let mut enc = CabacEncoder::new();
        let mut contexts = vec![CabacCtx::default(); N_CONTEXTS];
        for (i, &mode) in modes.iter().enumerate() {
            encode_i_mb_type_i_nxn(
                &mut enc, &mut contexts,
                if i == 0 { None } else { Some(true) },
                None);
            encode_prev_intra4x4_flag(&mut enc, &mut contexts, false);
            let rem = if mode == 0 { 0 } else { mode - 1 };
            encode_rem_intra4x4(&mut enc, &mut contexts, rem);
            encode_cbp_luma(&mut enc, &mut contexts, cbp_luma_each, 0, 0);
            encode_cbp_chroma(&mut enc, &mut contexts, 0, 0, 0);
            if cbp_luma_each != 0 {
                encode_mb_qp_delta(&mut enc, &mut contexts, 0, false);
                if let Some(per_block) = block_coefs {
                    let spec = res_block_spec(CtxBlockCat::Luma4x4);
                    for block_idx in 0..16 {
                        let region = block_idx / 4;
                        if (cbp_luma_each >> region) & 1 == 0 { continue; }
                        let coefs = &per_block[block_idx];
                        let any_nonzero =
                            coefs.iter().any(|c| *c != 0);
                        encode_coded_block_flag(
                            &mut enc, &mut contexts,
                            CtxBlockCat::Luma4x4,
                            any_nonzero, None, None,
                        );
                        if any_nonzero {
                            encode_residual_block(
                                &mut enc, &mut contexts, spec, coefs);
                        }
                    }
                }
            }
        }
        enc.finish();
        enc.buffer
    }

    #[test]
    fn round_trip_i_nxn_returns_descriptors() {
        let modes = [3u8, 5, 1, 7];
        let rbsp = encode_i_nxn_mbs(&modes, 0, None);

        let mut iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, modes.len());
        let mut got = Vec::new();
        while let Some(mb) = iter.next_mb() {
            got.push(mb);
        }
        assert_eq!(got.len(), modes.len());
        for (i, mb) in got.iter().enumerate() {
            assert_eq!(mb.mb_type, 0, "MB {} should be I_NxN", i);
            assert!(mb.intra_mode.is_some(),
                     "MB {} should have intra mode", i);
            assert!(!mb.has_nonzero_residual);
        }
    }

    #[test]
    fn cbp_drives_has_nonzero_residual() {
        let rbsp = encode_i_nxn_mbs(&[0], 0xF, None);  // all 4 blocks coded
        let mut iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 1);
        let mb = iter.next_mb().expect("one mb");
        assert!(mb.has_nonzero_residual,
                "cbp_luma=0xF should set has_nonzero_residual");
    }

    #[test]
    fn cbp_zero_yields_zero_residual_flag() {
        let rbsp = encode_i_nxn_mbs(&[0], 0, None);
        let mut iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 1);
        let mb = iter.next_mb().expect("one mb");
        assert!(!mb.has_nonzero_residual);
    }

    #[test]
    fn iterator_respects_mb_count() {
        let rbsp = encode_i_nxn_mbs(&[0; 3], 0, None);
        let mut iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 2);  // ask for only 2
        let count = (&mut iter).take(10).count();
        assert_eq!(count, 2);
        assert!(iter.next_mb().is_none());
    }

    #[test]
    fn implements_iterator_trait() {
        let rbsp = encode_i_nxn_mbs(&[0], 0, None);
        let iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 1);
        let mbs: Vec<H264MbDescriptor> = iter.collect();
        assert_eq!(mbs.len(), 1);
    }

    /// All 16 residual blocks round-trip through the iterator with
    /// distinct per-block coefficients. Verifies the iterator captures
    /// every block (not just the first) + bitstream position advances
    /// correctly across all 16 residual_block decodes.
    #[test]
    fn all_16_blocks_round_trip_with_distinct_coefs() {
        // Each block gets a distinct DC coefficient = block_idx + 1.
        let mut per_block = [[0i32; 16]; 16];
        for block_idx in 0..16 {
            per_block[block_idx][0] = (block_idx as i32) + 1;
        }
        let rbsp = encode_i_nxn_mbs(&[0], 0xF, Some(&per_block));
        let mut iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 1);
        let mb = iter.next_mb().expect("one mb");
        assert!(mb.has_nonzero_residual);
        for block_idx in 0..16 {
            assert_eq!(mb.residual_luma_4x4[block_idx][0],
                       (block_idx as i32) + 1,
                       "block {} DC coef round-trip", block_idx);
        }
    }

    /// Sparse pattern across blocks — only blocks 0, 5, 10, 15 carry
    /// coefficients (matching a typical diagonal sparse residual).
    #[test]
    fn sparse_block_pattern_round_trips() {
        let mut per_block = [[0i32; 16]; 16];
        per_block[0][0] = 7;
        per_block[5][0] = -4;
        per_block[10][0] = 3;
        per_block[15][0] = -1;
        let rbsp = encode_i_nxn_mbs(&[0], 0xF, Some(&per_block));
        let mut iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 1);
        let mb = iter.next_mb().expect("one mb");
        assert_eq!(mb.residual_luma_4x4[0][0], 7);
        assert_eq!(mb.residual_luma_4x4[5][0], -4);
        assert_eq!(mb.residual_luma_4x4[10][0], 3);
        assert_eq!(mb.residual_luma_4x4[15][0], -1);
        // Untouched blocks stay zero.
        for block_idx in [1usize, 2, 3, 4, 6, 7, 8, 9, 11, 12, 13, 14] {
            assert_eq!(mb.residual_luma_4x4[block_idx], [0; 16],
                       "block {} should be all-zero", block_idx);
        }
    }

    /// Partial CBP: only the first 8×8 region has coefficients.
    /// Verifies blocks 4..15 stay zero (their region cbp bit is 0).
    #[test]
    fn partial_cbp_decodes_only_set_regions() {
        let mut per_block = [[0i32; 16]; 16];
        for block_idx in 0..16 {
            per_block[block_idx][0] = (block_idx as i32) + 1;
        }
        let rbsp = encode_i_nxn_mbs(&[0], 0x1, Some(&per_block));  // bit 0 only
        let mut iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 1);
        let mb = iter.next_mb().expect("one mb");
        // Blocks 0..3 (region 0) decoded.
        for block_idx in 0..4 {
            assert_eq!(mb.residual_luma_4x4[block_idx][0],
                       (block_idx as i32) + 1);
        }
        // Blocks 4..15 (regions 1..3) stay zero.
        for block_idx in 4..16 {
            assert_eq!(mb.residual_luma_4x4[block_idx], [0; 16],
                       "block {} (region {}) should stay zero",
                       block_idx, block_idx / 4);
        }
    }

    /// All-zero coefficients with cbp_luma set: encoder emits 16
    /// coded_block_flag=0 → no residual_blocks → flag still true
    /// (CBP-driven) but all 16 blocks stay zero.
    #[test]
    fn cbp_set_with_zero_coefs_yields_zero_residual() {
        let per_block = [[0i32; 16]; 16];
        let rbsp = encode_i_nxn_mbs(&[0], 0xF, Some(&per_block));
        let mut iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 1);
        let mb = iter.next_mb().expect("one mb");
        for block_idx in 0..16 {
            assert_eq!(mb.residual_luma_4x4[block_idx], [0; 16]);
        }
    }

    /// Encode N P_L0_16x16 MBs with known (mvd_x, mvd_y) pairs into
    /// an RBSP buffer. v1 P-slice fixture: no residual, no chroma,
    /// no ref_idx (assumes num_ref_idx_l0_active_minus1 = 0).
    fn encode_p_l0_16x16_mbs(mvs: &[(i16, i16)]) -> Vec<u8> {
        let mut enc = CabacEncoder::new();
        let mut contexts = vec![CabacCtx::default(); N_CONTEXTS];
        for &(mvd_x, mvd_y) in mvs.iter() {
            // mb_skip_flag = 0 (not skipped). ctx_idx for first MB
            // with neighbours absent: ctx_offset + 0.
            let skip_ctx_idx = mb_skip_flag_ctx_idx(
                CabacSliceType::P, Some(0), Some(0),
            ).expect("P slice has mb_skip");
            enc.encode_bin(&mut contexts[skip_ctx_idx], 0);
            // mb_type = 0 (P_L0_16x16)
            encode_p_mb_type(&mut enc, &mut contexts, 0);
            // mvd_x, mvd_y
            encode_mvd(&mut enc, &mut contexts,
                       MVD_L0_X_CTX_OFFSET, mvd_x as i32);
            encode_mvd(&mut enc, &mut contexts,
                       MVD_L0_Y_CTX_OFFSET, mvd_y as i32);
            // cbp_luma = 0, cbp_chroma = 0 (no residual)
            encode_cbp_luma(&mut enc, &mut contexts, 0, 0, 0);
            encode_cbp_chroma(&mut enc, &mut contexts, 0, 0, 0);
        }
        enc.finish();
        enc.buffer
    }

    /// P_L0_16x16 round-trip with neighbour-aware MV prediction.
    /// pic_width = mb_count so every MB after the first uses the
    /// previous MB's absolute MV as its left predictor. The MVDs
    /// drive the absolute MVs to known accumulated values.
    ///
    /// MVDs: (3, -2), (0, 0), (-5, 7), (42, -42)
    /// Predictors: (0,0), (3,-2), (3,-2), (-2, 5)
    /// Absolutes:  (3,-2), (3,-2), (-2, 5), (40, -37)
    #[test]
    fn p_mb_motion_vector_round_trips_with_predictor() {
        let mvds = [(3i16, -2i16), (0, 0), (-5, 7), (42, -42)];
        let rbsp = encode_p_l0_16x16_mbs(&mvds);
        let mut iter = H264MbIterator::with_pic_width(
            rbsp, 0, CabacSliceType::P, 26, mvds.len(),
            mvds.len() as u32);
        let got: Vec<_> = (&mut iter).collect();
        assert_eq!(got.len(), mvds.len());
        let expected_abs = [(3i16, -2i16), (3, -2), (-2, 5), (40, -37)];
        for (i, (mb, exp)) in got.iter().zip(expected_abs.iter()).enumerate() {
            assert_eq!(mb.mb_type, 0, "MB {} should be P_L0_16x16", i);
            assert_eq!((mb.mv_x, mb.mv_y), *exp,
                       "MB {} abs MV: got ({}, {}), want {:?}",
                       i, mb.mv_x, mb.mv_y, exp);
        }
    }

    /// Median-of-3 unit test.
    #[test]
    fn median3_correct() {
        assert_eq!(median3(1, 2, 3), 2);
        assert_eq!(median3(3, 1, 2), 2);
        assert_eq!(median3(2, 3, 1), 2);
        assert_eq!(median3(-5, 0, 5), 0);
        assert_eq!(median3(7, 7, 7), 7);
        assert_eq!(median3(i16::MAX, 0, i16::MIN), 0);
    }

    /// First MB in slice: no neighbours → predictor = (0, 0) →
    /// absolute MV = decoded MVD.
    #[test]
    fn first_mb_predictor_is_zero() {
        let mvs = [(5i16, -3i16)];
        let rbsp = encode_p_l0_16x16_mbs(&mvs);
        let mut iter = H264MbIterator::with_pic_width(
            rbsp, 0, CabacSliceType::P, 26, 1, 4);
        let mb = iter.next_mb().expect("one mb");
        assert_eq!((mb.mv_x, mb.mv_y), (5, -3),
                   "first MB MV should equal the raw MVD");
    }

    /// Single-row slice: every MB after the first uses the previous
    /// MB's absolute MV as its left-neighbour predictor.
    ///
    /// Encode chain of MVDs; expect absolute MVs to accumulate.
    /// MB 0: MVD (10, 0); pred (0, 0); abs (10, 0)
    /// MB 1: MVD (3, 0);  pred A=(10, 0); abs (13, 0)
    /// MB 2: MVD (-2, 0); pred A=(13, 0); abs (11, 0)
    #[test]
    fn left_neighbour_predictor_chains_correctly() {
        let mvds = [(10i16, 0i16), (3, 0), (-2, 0)];
        let rbsp = encode_p_l0_16x16_mbs(&mvds);
        let iter = H264MbIterator::with_pic_width(
            rbsp, 0, CabacSliceType::P, 26, mvds.len(), 4);
        let got: Vec<_> = iter.collect();
        assert_eq!(got[0].mv_x, 10);
        assert_eq!(got[1].mv_x, 13, "MB 1 abs MV should be MVD + left A");
        assert_eq!(got[2].mv_x, 11, "MB 2 abs MV should be MVD + left A");
    }

    /// Multi-row slice — second row's first MB uses top neighbour B.
    ///
    /// pic_width = 2, 4 MBs total → 2 rows of 2 MBs each.
    /// MB 0 at (0, 0): MVD (5, 0);   pred (0, 0);          abs (5, 0)
    /// MB 1 at (1, 0): MVD (0, 0);   pred A=(5, 0);        abs (5, 0)
    /// MB 2 at (0, 1): MVD (0, 7);   pred B=(5, 0);        abs (5, 7)
    /// MB 3 at (1, 1): MVD (1, 1);   pred=median(A=(5,7), B=(5,0), C=0,0)
    ///                                = (median(5,5,0), median(7,0,0))
    ///                                = (5, 0);            abs (6, 1)
    #[test]
    fn top_neighbour_predictor_for_second_row() {
        let mvds = [(5i16, 0i16), (0, 0), (0, 7), (1, 1)];
        let rbsp = encode_p_l0_16x16_mbs(&mvds);
        let iter = H264MbIterator::with_pic_width(
            rbsp, 0, CabacSliceType::P, 26, mvds.len(), 2);
        let got: Vec<_> = iter.collect();
        assert_eq!((got[0].mv_x, got[0].mv_y), (5, 0));
        assert_eq!((got[1].mv_x, got[1].mv_y), (5, 0));
        assert_eq!((got[2].mv_x, got[2].mv_y), (5, 7),
                   "MB at (0, 1) should use top neighbour (5, 0) as predictor");
        assert_eq!((got[3].mv_x, got[3].mv_y), (6, 1),
                   "MB at (1, 1) should use median(A, B, C)");
    }

    /// Median-of-3 predictor for an interior MB. Set up a slice
    /// where the three neighbours produce a known median.
    ///
    /// pic_width = 3, 6 MBs total → 2 rows of 3.
    /// Top row: MVs (10, 0), (20, 0), (30, 0)
    /// MB 3 at (0, 1): predictor B=(10, 0); MVD (1, 0); abs (11, 0)
    /// MB 4 at (1, 1): predictor median(A=(11, 0), B=(20, 0), C=(30, 0))
    ///                        = (median(11, 20, 30), 0) = (20, 0)
    ///                  MVD (0, 0); abs (20, 0)
    #[test]
    fn interior_mb_uses_median_of_three() {
        let mvds = [(10i16, 0), (10, 0), (10, 0),   // row 0: (10,0), (20,0), (30,0)
                     (1, 0), (0, 0), (0, 0)];        // row 1
        // Compute expected row-0 absolutes: each accumulates by left.
        // MB 0: pred (0,0); abs (10, 0)
        // MB 1: pred A=(10,0); MVD (10,0); abs (20, 0)
        // MB 2: pred A=(20,0); MVD (10,0); abs (30, 0)
        let rbsp = encode_p_l0_16x16_mbs(&mvds);
        let iter = H264MbIterator::with_pic_width(
            rbsp, 0, CabacSliceType::P, 26, mvds.len(), 3);
        let got: Vec<_> = iter.collect();
        // Verify the row-0 setup.
        assert_eq!(got[0].mv_x, 10);
        assert_eq!(got[1].mv_x, 20);
        assert_eq!(got[2].mv_x, 30);
        // MB at (0, 1): pred = B = top neighbour (10, 0); MVD (1, 0).
        assert_eq!(got[3].mv_x, 11,
                   "MB (0,1) should use B as predictor (10) + MVD (1)");
        // MB at (1, 1): pred = median(A=(11,0), B=(20,0), C=(30,0)) = (20, 0).
        // MVD (0, 0) → abs = (20, 0).
        assert_eq!(got[4].mv_x, 20,
                   "MB (1,1) should use median(11, 20, 30) = 20 as predictor");
    }

    /// Zero-MV P MBs: common in static-scene content.
    #[test]
    fn p_mb_zero_motion_round_trips() {
        let mvs = [(0i16, 0i16); 5];
        let rbsp = encode_p_l0_16x16_mbs(&mvs);
        let iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::P, 26, mvs.len());
        let got: Vec<_> = iter.collect();
        assert_eq!(got.len(), mvs.len());
        for mb in &got {
            assert_eq!(mb.mv_x, 0);
            assert_eq!(mb.mv_y, 0);
        }
    }

    /// Multi-MB stream with residuals — verifies bitstream advances
    /// correctly between MBs after a full 16-block residual decode.
    #[test]
    fn multi_mb_full_residual_advances_bitstream() {
        let mut per_block = [[0i32; 16]; 16];
        for block_idx in 0..16 {
            per_block[block_idx][0] = 1;
        }
        let rbsp = encode_i_nxn_mbs(&[0, 1, 2], 0xF, Some(&per_block));
        let iter = H264MbIterator::new(
            rbsp, 0, CabacSliceType::I, 26, 3);
        let mbs: Vec<_> = iter.collect();
        assert_eq!(mbs.len(), 3);
        for mb in &mbs {
            assert!(mb.has_nonzero_residual);
            for block_idx in 0..16 {
                assert_eq!(mb.residual_luma_4x4[block_idx][0], 1,
                           "block {} DC should be 1 per MB", block_idx);
            }
        }
    }
}
