//! H.265 in-loop filter — stage 5 of the H.264→H.265 transcoder.
//!
//!   STAGE: in_loop_filter
//!     rewrite:      h264_deblocking_strength → h265_deblocking_strength + SAO
//!     pattern:      stride_sequential_pixel_access
//!     hardware:     AVX512BW byte-wide SIMD (substrate-named)
//!     topology:     data_parallel_sharding (horizontal strips per core)
//!     bottleneck:   memory_bandwidth_bound (L2 bandwidth)
//!
//! Two filters: deblocking (smooths block boundaries) + SAO (corrects
//! ringing artefacts). Both run as a second pass over the reconstructed
//! plane after all CUs in a slice are decoded.
//!
//! ## Implementation choice
//!
//! Scalar Rust v1 — substrate's bottleneck is `memory_bandwidth_bound`,
//! so AVX512BW byte SIMD only matters when the working set is L2-resident.
//! For correctness verification first; SIMD acceleration is mechanical
//! once the algorithm is locked.
//!
//! Reference: ITU-T H.265 (08/2024) clauses 8.7.2 (deblocking filter)
//! and 8.7.3 (SAO).

use std::cmp::{max, min};

/// Boundary strength bS for H.265 deblocking. Per clause 8.7.2.4:
///   2 — at least one side is intra-coded
///   1 — at least one side has non-zero transform coefficients,
///       or different motion vectors / reference frames
///   0 — otherwise (no filtering)
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BoundaryStrength {
    None = 0,
    Weak = 1,
    Strong = 2,
}

/// Per-side information needed to compute bS for a boundary.
#[derive(Debug, Clone, Copy)]
pub struct SideInfo {
    pub is_intra: bool,
    pub has_nonzero_coeffs: bool,
    pub mv_x: i16,
    pub mv_y: i16,
    pub ref_pic_id: u8,
}

/// Decide bS for a boundary between two CUs. Implementation of clause
/// 8.7.2.4 derivation of bS.
pub fn boundary_strength(p: SideInfo, q: SideInfo) -> BoundaryStrength {
    if p.is_intra || q.is_intra {
        return BoundaryStrength::Strong;
    }
    if p.has_nonzero_coeffs || q.has_nonzero_coeffs {
        return BoundaryStrength::Weak;
    }
    if p.ref_pic_id != q.ref_pic_id {
        return BoundaryStrength::Weak;
    }
    let dx = (p.mv_x - q.mv_x).abs();
    let dy = (p.mv_y - q.mv_y).abs();
    // H.265 uses a 4-pel threshold for the "different motion" test.
    if dx >= 4 || dy >= 4 {
        return BoundaryStrength::Weak;
    }
    BoundaryStrength::None
}

/// Clip a value into `[lo, hi]`. Hot-path helper used by both
/// deblocking + SAO. Compiler will optimise to CMOV.
#[inline]
fn clip(v: i32, lo: i32, hi: i32) -> i32 {
    if v < lo {
        lo
    } else if v > hi {
        hi
    } else {
        v
    }
}

/// Apply a 4-pixel deblocking filter perpendicular to a vertical
/// boundary. `p3 p2 p1 p0 | q0 q1 q2 q3` are the eight samples crossing
/// the boundary (indices 3..0 on the p side, 0..3 on the q side).
///
/// Returns the four modified samples on each side: (p0', p1', p2', q0', q1', q2').
/// Simplified strong/normal split per clause 8.7.2.5. Beta/tc clipping
/// is applied per H.265 normalisation; this is the educational version.
pub fn deblock_4_samples_vertical(
    p3: i32,
    p2: i32,
    p1: i32,
    p0: i32,
    q0: i32,
    q1: i32,
    q2: i32,
    q3: i32,
    bs: BoundaryStrength,
    tc: i32,
) -> (i32, i32, i32, i32, i32, i32) {
    match bs {
        BoundaryStrength::None => (p2, p1, p0, q0, q1, q2),
        BoundaryStrength::Weak => {
            // Weak filter: clip(p0 - 1, p0' < p0 + tc); same for q0.
            let delta = clip((9 * (q0 - p0) - 3 * (q1 - p1) + 8) >> 4, -tc, tc);
            let new_p0 = clip(p0 + delta, 0, 255);
            let new_q0 = clip(q0 - delta, 0, 255);
            (p2, p1, new_p0, new_q0, q1, q2)
        }
        BoundaryStrength::Strong => {
            // Strong filter: 3-tap modifications on each side.
            let new_p0 = clip(
                (p2 + 2 * p1 + 2 * p0 + 2 * q0 + q1 + 4) >> 3,
                p0 - 2 * tc,
                p0 + 2 * tc,
            );
            let new_p1 = clip((p2 + p1 + p0 + q0 + 2) >> 2, p1 - 2 * tc, p1 + 2 * tc);
            let new_p2 = clip(
                (2 * p3 + 3 * p2 + p1 + p0 + q0 + 4) >> 3,
                p2 - 2 * tc,
                p2 + 2 * tc,
            );
            let new_q0 = clip(
                (p1 + 2 * p0 + 2 * q0 + 2 * q1 + q2 + 4) >> 3,
                q0 - 2 * tc,
                q0 + 2 * tc,
            );
            let new_q1 = clip((p0 + q0 + q1 + q2 + 2) >> 2, q1 - 2 * tc, q1 + 2 * tc);
            let new_q2 = clip(
                (p0 + q0 + q1 + 3 * q2 + 2 * q3 + 4) >> 3,
                q2 - 2 * tc,
                q2 + 2 * tc,
            );
            (new_p2, new_p1, new_p0, new_q0, new_q1, new_q2)
        }
    }
}

/// SAO mode per CTU.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SaoMode {
    /// SAO disabled for this CTU.
    Off,
    /// Band offset: signal 4 consecutive bands' offsets in [0, 32).
    BandOffset { band_start: u8, offsets: [i8; 4] },
    /// Edge offset: classify each pixel by its position on an edge in
    /// the chosen direction; offset by per-category amount.
    EdgeOffset {
        direction: SaoEdgeDir,
        offsets: [i8; 4],
    },
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SaoEdgeDir {
    Horizontal,
    Vertical,
    Diag45,
    Diag135,
}

impl SaoEdgeDir {
    /// Get the (dx, dy) neighbour offset pair for this direction.
    pub fn neighbours(self) -> ((i32, i32), (i32, i32)) {
        match self {
            SaoEdgeDir::Horizontal => ((-1, 0), (1, 0)),
            SaoEdgeDir::Vertical => ((0, -1), (0, 1)),
            SaoEdgeDir::Diag45 => ((1, -1), (-1, 1)),
            SaoEdgeDir::Diag135 => ((-1, -1), (1, 1)),
        }
    }
}

/// SAO edge category per clause 8.7.3.2. Returns 0..4; 0 means no offset.
fn sao_edge_category(centre: i32, a: i32, b: i32) -> usize {
    let s1 = (centre - a).signum();
    let s2 = (centre - b).signum();
    // Category 1: both neighbours strictly greater   (centre < a, b)
    // Category 2: one strictly greater, other equal  (centre < a, == b)
    // Category 3: one strictly less, other equal     (centre > a, == b)
    // Category 4: both strictly less                 (centre > a, b)
    // Category 0: otherwise.
    match (s1, s2) {
        (-1, -1) => 1,
        (-1, 0) | (0, -1) => 2,
        (1, 0) | (0, 1) => 3,
        (1, 1) => 4,
        _ => 0,
    }
}

/// Apply SAO band-offset to a plane in-place. Substrate-named pattern:
/// `stride_sequential_pixel_access` — outer-loop rows, inner-loop cols,
/// prefetcher streams pixels.
pub fn apply_sao_band_offset(
    plane: &mut [u8],
    width: usize,
    height: usize,
    stride: usize,
    band_start: u8,
    offsets: [i8; 4],
) {
    for y in 0..height {
        for x in 0..width {
            let p = plane[y * stride + x] as i32;
            let band = (p >> 3) as u8; // 256 levels → 32 bands of 8 each
            let band_idx = band.wrapping_sub(band_start);
            if band_idx < 4 {
                let new_p = p + offsets[band_idx as usize] as i32;
                plane[y * stride + x] = clip(new_p, 0, 255) as u8;
            }
        }
    }
}

/// Apply SAO edge-offset to a plane in-place. Interior pixels only
/// (boundary rows/cols left alone; that's how H.265 handles them in
/// the CTU-tile case).
pub fn apply_sao_edge_offset(
    plane: &mut [u8],
    width: usize,
    height: usize,
    stride: usize,
    direction: SaoEdgeDir,
    offsets: [i8; 4],
) {
    let ((dx_a, dy_a), (dx_b, dy_b)) = direction.neighbours();
    // Need at least 3 rows + 3 cols to have an interior cell.
    if width < 3 || height < 3 {
        return;
    }
    for y in 1..height - 1 {
        for x in 1..width - 1 {
            let centre = plane[y * stride + x] as i32;
            let xa = (x as i32 + dx_a) as usize;
            let ya = (y as i32 + dy_a) as usize;
            let xb = (x as i32 + dx_b) as usize;
            let yb = (y as i32 + dy_b) as usize;
            let a = plane[ya * stride + xa] as i32;
            let b = plane[yb * stride + xb] as i32;
            let cat = sao_edge_category(centre, a, b);
            if cat == 0 {
                continue;
            }
            let new_p = centre + offsets[cat - 1] as i32;
            plane[y * stride + x] = clip(new_p, 0, 255) as u8;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn intra() -> SideInfo {
        SideInfo {
            is_intra: true,
            has_nonzero_coeffs: false,
            mv_x: 0,
            mv_y: 0,
            ref_pic_id: 0,
        }
    }
    fn inter_zero() -> SideInfo {
        SideInfo {
            is_intra: false,
            has_nonzero_coeffs: false,
            mv_x: 0,
            mv_y: 0,
            ref_pic_id: 0,
        }
    }

    #[test]
    fn intra_boundary_is_strong() {
        assert_eq!(
            boundary_strength(intra(), inter_zero()),
            BoundaryStrength::Strong
        );
        assert_eq!(
            boundary_strength(inter_zero(), intra()),
            BoundaryStrength::Strong
        );
    }

    #[test]
    fn matching_inter_zero_boundary_is_none() {
        assert_eq!(
            boundary_strength(inter_zero(), inter_zero()),
            BoundaryStrength::None
        );
    }

    #[test]
    fn nonzero_coeffs_make_boundary_weak() {
        let mut q = inter_zero();
        q.has_nonzero_coeffs = true;
        assert_eq!(boundary_strength(inter_zero(), q), BoundaryStrength::Weak);
    }

    #[test]
    fn different_ref_pic_makes_boundary_weak() {
        let mut q = inter_zero();
        q.ref_pic_id = 1;
        assert_eq!(boundary_strength(inter_zero(), q), BoundaryStrength::Weak);
    }

    #[test]
    fn motion_difference_makes_boundary_weak() {
        let mut q = inter_zero();
        q.mv_x = 5;
        assert_eq!(boundary_strength(inter_zero(), q), BoundaryStrength::Weak);
    }

    #[test]
    fn deblock_no_strength_leaves_pixels_unchanged() {
        let result = deblock_4_samples_vertical(
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            100,
            BoundaryStrength::None,
            4,
        );
        assert_eq!(result, (100, 100, 100, 100, 100, 100));
    }

    #[test]
    fn deblock_weak_smooths_boundary() {
        // Step from 100 to 150 across the boundary.
        let (_, _, p0, q0, _, _) = deblock_4_samples_vertical(
            100,
            100,
            100,
            100,
            150,
            150,
            150,
            150,
            BoundaryStrength::Weak,
            8,
        );
        // After weak filter the boundary samples move toward each other.
        assert!(p0 > 100, "p0 should rise toward q0; got {}", p0);
        assert!(q0 < 150, "q0 should fall toward p0; got {}", q0);
    }

    #[test]
    fn deblock_strong_smooths_more_than_weak() {
        let (_, _, p0_strong, q0_strong, _, _) = deblock_4_samples_vertical(
            100,
            100,
            100,
            100,
            150,
            150,
            150,
            150,
            BoundaryStrength::Strong,
            16,
        );
        let (_, _, p0_weak, q0_weak, _, _) = deblock_4_samples_vertical(
            100,
            100,
            100,
            100,
            150,
            150,
            150,
            150,
            BoundaryStrength::Weak,
            16,
        );
        // Strong filter pulls boundary further toward midline.
        assert!(
            (p0_strong - 100).abs() >= (p0_weak - 100).abs(),
            "strong should change p0 more or equally: weak {}, strong {}",
            p0_weak,
            p0_strong
        );
        assert!(
            (q0_strong - 150).abs() >= (q0_weak - 150).abs(),
            "strong should change q0 more or equally: weak {}, strong {}",
            q0_weak,
            q0_strong
        );
    }

    #[test]
    fn sao_band_offset_shifts_target_bands_only() {
        // 8×1 plane, pixels in 4 different bands.
        let mut plane = vec![10u8, 30, 50, 70, 90, 110, 130, 150];
        // band_start=2 means we offset bands 2, 3, 4, 5 (values 16..47).
        apply_sao_band_offset(&mut plane, 8, 1, 8, 2, [5, 5, 5, 5]);
        // Only pixels whose band ∈ {2, 3, 4, 5} are shifted.
        // 30 / 8 = band 3 → shifted (+5 → 35)
        // 50 / 8 = band 6 → not shifted
        assert_eq!(plane[1], 35);
        assert_eq!(plane[2], 50);
    }

    #[test]
    fn sao_edge_category_local_minimum_is_cat1() {
        // centre < both neighbours
        assert_eq!(sao_edge_category(50, 100, 100), 1);
    }

    #[test]
    fn sao_edge_category_local_maximum_is_cat4() {
        assert_eq!(sao_edge_category(150, 100, 100), 4);
    }

    #[test]
    fn sao_edge_category_flat_is_cat0() {
        assert_eq!(sao_edge_category(100, 100, 100), 0);
    }

    #[test]
    fn sao_edge_offset_shifts_local_extrema() {
        // 3×3 plane: centre is a local minimum.
        let mut plane = vec![100, 100, 100, 100, 50, 100, 100, 100, 100];
        // Horizontal edge direction: neighbours of (1, 1) are (0, 1) and (2, 1) = 100, 100.
        // Centre 50 is local-min → category 1. Offset by +20.
        apply_sao_edge_offset(&mut plane, 3, 3, 3, SaoEdgeDir::Horizontal, [20, 0, 0, 0]);
        assert_eq!(
            plane[1 * 3 + 1],
            70,
            "local min should be raised by category-1 offset"
        );
    }
}
