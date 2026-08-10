//! H.265 intra-prediction mode primitive — H.264 9-mode → H.265 35-mode remap.
//!
//! Executes stage 2 of the H.264→H.265 transcoder design surfaced from
//! the substrate's vocabulary (commit 486f65e):
//!
//!   STAGE: intra_prediction_mode
//!     transform-stage rewrite:  h264_intra_pred_9modes → h265_intra_pred_35modes
//!     compute pattern:          set_intersection_for_lookup
//!     hardware:                 AVX-512 VP2INTERSECT (or LUT in L1d)
//!     topology:                 pre_computed_lookup_table, replicated per-core
//!     bottleneck class:         negligible (4-cycle L1d lookups, pipelined)
//!
//! For this primitive the LUT path is faster than VP2INTERSECT setup
//! because the source set has only 9 elements and the LUT is a static
//! 9-byte array. Stays in L1d trivially; one indirect load per call.
//!
//! Mapping (H.264 4x4 intra modes → H.265 35-mode index):
//!
//!   H.264 mode  Name                    H.265 mode  Name
//!   ──────────  ──────────────────────  ──────────  ──────────────
//!        0      Vertical                    26      INTRA_ANGULAR_26  (vertical)
//!        1      Horizontal                  10      INTRA_ANGULAR_10  (horizontal)
//!        2      DC                           1      INTRA_DC
//!        3      Diagonal_Down_Left          22      INTRA_ANGULAR_22
//!        4      Diagonal_Down_Right         14      INTRA_ANGULAR_14
//!        5      Vertical_Right              28      INTRA_ANGULAR_28
//!        6      Horizontal_Down              8      INTRA_ANGULAR_8
//!        7      Vertical_Left               24      INTRA_ANGULAR_24
//!        8      Horizontal_Up                6      INTRA_ANGULAR_6
//!
//! Source: H.265 / HEVC standard angular mode numbering (modes 2..34
//! are angles -135°..+135°; mode 0 = planar, mode 1 = DC, mode 10 =
//! horizontal, mode 26 = vertical). Each H.264 mode picks the nearest
//! H.265 angular index.

/// H.264 intra-4x4 prediction mode index (0..8).
pub type H264IntraMode = u8;
/// H.265 intra prediction mode index (0..34).
pub type H265IntraMode = u8;

/// The 9-entry remap table. `LUT[h264_mode] = h265_mode`.
///
/// This is the `pre_computed_lookup_table` the substrate's
/// `set_intersection_uses_lookup_table` rule names.
const H264_TO_H265_INTRA_LUT: [H265IntraMode; 9] = [
    26, // Vertical
    10, // Horizontal
     1, // DC
    22, // Diagonal_Down_Left
    14, // Diagonal_Down_Right
    28, // Vertical_Right
     8, // Horizontal_Down
    24, // Vertical_Left
     6, // Horizontal_Up
];

/// Remap an H.264 intra-prediction mode to its closest H.265 angular
/// counterpart. Out-of-range inputs return `None`.
///
/// Per the substrate's `set_intersection_throughput_set_by_lookup_latency`
/// rule: ~4 cycle L1d latency, pipelines to ~1 lookup/cycle under OoO.
#[inline]
pub fn h264_to_h265_intra(mode: H264IntraMode) -> Option<H265IntraMode> {
    if (mode as usize) < H264_TO_H265_INTRA_LUT.len() {
        Some(H264_TO_H265_INTRA_LUT[mode as usize])
    } else {
        None
    }
}

/// Batch remap of an H.264 mode slice. Caller-allocated output of
/// equal length. Returns the count actually remapped (skips invalid).
pub fn h264_to_h265_intra_batch(modes: &[H264IntraMode],
                                  out: &mut [H265IntraMode]) -> usize {
    assert_eq!(modes.len(), out.len());
    let mut n = 0;
    for (i, &m) in modes.iter().enumerate() {
        if let Some(h265) = h264_to_h265_intra(m) {
            out[i] = h265;
            n += 1;
        } else {
            out[i] = 0;
        }
    }
    n
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn vertical_maps_to_h265_vertical() {
        // H.264 mode 0 = Vertical → H.265 mode 26 = INTRA_ANGULAR_26
        assert_eq!(h264_to_h265_intra(0), Some(26));
    }

    #[test]
    fn horizontal_maps_to_h265_horizontal() {
        // H.264 mode 1 = Horizontal → H.265 mode 10
        assert_eq!(h264_to_h265_intra(1), Some(10));
    }

    #[test]
    fn dc_maps_to_h265_dc() {
        // H.264 mode 2 = DC → H.265 mode 1 = INTRA_DC
        assert_eq!(h264_to_h265_intra(2), Some(1));
    }

    #[test]
    fn all_nine_modes_in_range() {
        for m in 0..9u8 {
            let h265 = h264_to_h265_intra(m).expect("valid mode");
            assert!(h265 <= 34, "H.265 mode index must be 0..34; got {}", h265);
        }
    }

    #[test]
    fn out_of_range_returns_none() {
        assert_eq!(h264_to_h265_intra(9), None);
        assert_eq!(h264_to_h265_intra(255), None);
    }

    #[test]
    fn no_two_h264_modes_map_to_same_h265_index() {
        // Different H.264 directional modes should map to different
        // H.265 angles (the remap preserves distinguishability).
        let mut seen = [false; 35];
        for m in 0..9u8 {
            let h265 = h264_to_h265_intra(m).unwrap() as usize;
            assert!(!seen[h265],
                    "H.264 mode {} maps to already-used H.265 mode {}",
                    m, h265);
            seen[h265] = true;
        }
    }

    #[test]
    fn batch_remap_preserves_length() {
        let input = [0u8, 1, 2, 3, 4, 5, 6, 7, 8];
        let mut output = [0u8; 9];
        let n = h264_to_h265_intra_batch(&input, &mut output);
        assert_eq!(n, 9);
        assert_eq!(&output, &H264_TO_H265_INTRA_LUT);
    }

    #[test]
    fn batch_handles_invalid_modes() {
        let input = [0u8, 9, 2, 255];
        let mut output = [0u8; 4];
        let n = h264_to_h265_intra_batch(&input, &mut output);
        assert_eq!(n, 2);  // 0 and 2 are valid
        assert_eq!(output[0], 26);
        assert_eq!(output[2], 1);
    }
}
