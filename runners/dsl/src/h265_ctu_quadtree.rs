//! H.265 CTU quadtree — stage 1 of the H.264→H.265 transcoder.
//!
//!   STAGE: block_structure
//!     rewrite:      macroblock → coding_tree_unit
//!     pattern:      tree_walk_with_merge_decisions
//!     hardware:     branch_prediction + BMI2 pdep/pext (substrate-named)
//!     topology:     cache_resident_working_set (L1d, per-CTU walks)
//!     bottleneck:   latency_bound (branch mispredict)
//!
//! ## The transcoder's load-bearing rewrite
//!
//! Per the substrate's rule `larger_partitions_save_overhead`:
//! "main reason H.265 outperforms H.264 at 4K — CTUs up to 64×64 vs
//! MBs fixed at 16×16."  This module names the actual graph rewrite:
//! H.264 macroblock decisions → H.265 CTU/CU quadtree.
//!
//! ## The merge heuristic
//!
//! When four adjacent H.264 MBs share the same prediction mode + similar
//! residual energy, they can merge into one larger H.265 CU. This saves
//! 4 × 16x16 syntax overhead → 1 × 32x32 syntax overhead. The substrate's
//! design names this as a per-CTU tree walk with merge decisions.
//!
//! ## Implementation
//!
//! Scalar Rust; no BMI2 intrinsics in v1. The substrate's
//! `tree_walk_throughput_set_by_branch_predictor` rule says throughput
//! is gated by branch prediction, not by SIMD. Modern Zen 5 hits >95%
//! prediction on shallow quadtree walks once warm.

use std::fmt;

/// Prediction mode of a CU. For the transcoder we only need to know
/// whether two CUs are "same mode" — equality on this enum drives the
/// merge decision.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PredMode {
    /// Intra mode with the H.265 mode index 0..34.
    Intra(u8),
    /// Inter mode with a motion-vector identifier (the transcoder's
    /// upstream stage assigns one ID per distinct MV pair).
    Inter(u32),
    /// Skip mode — no residual, MV from neighbour.
    Skip,
}

/// Coding-tree node. Either a leaf CU (with a prediction mode + log2
/// size) or an internal quad split (4 children, NW, NE, SW, SE order).
#[derive(Debug, Clone)]
pub enum CuNode {
    Leaf {
        mode: PredMode,
        log2_size: u8,
    },
    Quad {
        log2_size: u8,
        children: Box<[CuNode; 4]>,
    },
}

impl CuNode {
    /// log2 of this node's side length (so an 8×8 CU = 3; CTU 64×64 = 6).
    pub fn log2_size(&self) -> u8 {
        match self {
            CuNode::Leaf { log2_size, .. } => *log2_size,
            CuNode::Quad { log2_size, .. } => *log2_size,
        }
    }
    pub fn side(&self) -> u32 {
        1u32 << self.log2_size()
    }

    /// Count leaf CUs in the subtree.
    pub fn leaf_count(&self) -> usize {
        match self {
            CuNode::Leaf { .. } => 1,
            CuNode::Quad { children, .. } => children.iter().map(|c| c.leaf_count()).sum(),
        }
    }

    /// Maximum depth from root to any leaf.
    pub fn max_depth(&self) -> u8 {
        match self {
            CuNode::Leaf { .. } => 0,
            CuNode::Quad { children, .. } => {
                1 + children.iter().map(|c| c.max_depth()).max().unwrap_or(0)
            }
        }
    }
}

impl fmt::Display for CuNode {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            CuNode::Leaf { mode, log2_size } => write!(
                f,
                "Leaf({:?}, {}x{})",
                mode,
                1u32 << log2_size,
                1u32 << log2_size
            ),
            CuNode::Quad {
                log2_size,
                children,
            } => {
                write!(f, "Quad({}x{})[", 1u32 << log2_size, 1u32 << log2_size)?;
                for (i, c) in children.iter().enumerate() {
                    if i > 0 {
                        write!(f, ", ")?;
                    }
                    c.fmt(f)?;
                }
                write!(f, "]")
            }
        }
    }
}

/// Build a CTU from four adjacent H.264 macroblock decisions.
///
/// Layout of `mbs`: row-major within the CTU. For a 32×32 CTU built
/// from 4 MBs: index 0 = NW, 1 = NE, 2 = SW, 3 = SE.
///
/// Merge heuristic: if all 4 children share the same mode, emit a
/// single leaf at the parent size. Otherwise emit a Quad with 4
/// leaf children.
pub fn build_cu_from_4_mbs(mbs: &[PredMode; 4], parent_log2_size: u8) -> CuNode {
    debug_assert!(parent_log2_size >= 1);
    // Same-mode merge: a key transcoder win.
    if mbs[0] == mbs[1] && mbs[1] == mbs[2] && mbs[2] == mbs[3] {
        return CuNode::Leaf {
            mode: mbs[0],
            log2_size: parent_log2_size,
        };
    }
    let leaf = |m: PredMode| CuNode::Leaf {
        mode: m,
        log2_size: parent_log2_size - 1,
    };
    CuNode::Quad {
        log2_size: parent_log2_size,
        children: Box::new([leaf(mbs[0]), leaf(mbs[1]), leaf(mbs[2]), leaf(mbs[3])]),
    }
}

/// Build a full 64×64 CTU from 16 H.264 macroblock decisions in
/// row-major order. Recursively merges adjacent uniform groups.
///
/// `mbs` layout: 4 rows × 4 cols of 16×16 MBs, mbs[row*4 + col].
pub fn build_ctu_from_16_mbs(mbs: &[PredMode; 16]) -> CuNode {
    // Build 4 32×32 quadrants from their 4 MBs each.
    // 4×4 layout, 2×2 quadrants:
    //
    //   mb[ 0] mb[ 1] | mb[ 2] mb[ 3]
    //   mb[ 4] mb[ 5] | mb[ 6] mb[ 7]
    //   ─────────────┼─────────────
    //   mb[ 8] mb[ 9] | mb[10] mb[11]
    //   mb[12] mb[13] | mb[14] mb[15]
    //
    let nw = build_cu_from_4_mbs(&[mbs[0], mbs[1], mbs[4], mbs[5]], 5);
    let ne = build_cu_from_4_mbs(&[mbs[2], mbs[3], mbs[6], mbs[7]], 5);
    let sw = build_cu_from_4_mbs(&[mbs[8], mbs[9], mbs[12], mbs[13]], 5);
    let se = build_cu_from_4_mbs(&[mbs[10], mbs[11], mbs[14], mbs[15]], 5);

    // Top-level merge: if all four 32×32 quadrants are uniform leaves
    // with the same mode, emit a single 64×64 leaf.
    if let (
        CuNode::Leaf { mode: a, .. },
        CuNode::Leaf { mode: b, .. },
        CuNode::Leaf { mode: c, .. },
        CuNode::Leaf { mode: d, .. },
    ) = (&nw, &ne, &sw, &se)
    {
        if a == b && b == c && c == d {
            return CuNode::Leaf {
                mode: *a,
                log2_size: 6,
            };
        }
    }
    CuNode::Quad {
        log2_size: 6,
        children: Box::new([nw, ne, sw, se]),
    }
}

/// Pre-order walk emitting each leaf's (log2_size, mode) for downstream
/// consumption (entropy coder, transform stage scheduling).
pub fn walk_leaves<F: FnMut(u8, PredMode)>(node: &CuNode, mut visit: F) {
    fn rec<F: FnMut(u8, PredMode)>(n: &CuNode, v: &mut F) {
        match n {
            CuNode::Leaf { mode, log2_size } => v(*log2_size, *mode),
            CuNode::Quad { children, .. } => {
                for c in children.iter() {
                    rec(c, v);
                }
            }
        }
    }
    rec(node, &mut visit);
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn uniform_mbs_merge_to_one_ctu_leaf() {
        // 16 MBs all in the same intra mode → one 64×64 leaf.
        let mode = PredMode::Intra(26); // vertical
        let mbs = [mode; 16];
        let ctu = build_ctu_from_16_mbs(&mbs);
        assert_eq!(
            ctu.leaf_count(),
            1,
            "uniform MBs should merge to a single leaf; got {} leaves",
            ctu.leaf_count()
        );
        assert_eq!(ctu.log2_size(), 6); // 64×64
    }

    #[test]
    fn one_distinct_mb_breaks_top_level_merge_only() {
        // 15 MBs intra, one inter → CTU splits into 4 32×32 quadrants,
        // 3 of which are uniform leaves; the 4th splits into 4 leaves.
        let mut mbs = [PredMode::Intra(1); 16];
        mbs[5] = PredMode::Inter(0); // NW quadrant, second row, first col
        let ctu = build_ctu_from_16_mbs(&mbs);
        // Total leaves: 3 (uniform quadrants) + 4 (NW split) = 7.
        assert_eq!(ctu.leaf_count(), 7);
        assert_eq!(ctu.max_depth(), 2); // CTU → quadrant → leaf
    }

    #[test]
    fn all_distinct_mbs_no_merges() {
        let mbs: [PredMode; 16] = std::array::from_fn(|i| PredMode::Inter(i as u32));
        let ctu = build_ctu_from_16_mbs(&mbs);
        assert_eq!(ctu.leaf_count(), 16); // no merging anywhere
        assert_eq!(ctu.max_depth(), 2);
    }

    #[test]
    fn quad_uniform_within_quadrant_merges_quadrant() {
        // 4 NW MBs uniform → NW quadrant merges to 32×32 leaf.
        // Other quadrants distinct.
        let mut mbs = [PredMode::Inter(0); 16];
        // NW = mbs[0, 1, 4, 5] all 0 (already)
        for i in [2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15] {
            mbs[i] = PredMode::Inter(i as u32);
        }
        let ctu = build_ctu_from_16_mbs(&mbs);
        // NW: 1 leaf (merged); NE, SW, SE: 4 leaves each = 13 total.
        assert_eq!(ctu.leaf_count(), 13);
    }

    #[test]
    fn walk_leaves_visits_all_in_pre_order() {
        let mbs = [PredMode::Intra(0); 16];
        let ctu = build_ctu_from_16_mbs(&mbs); // single 64×64 leaf
        let mut visited = Vec::new();
        walk_leaves(&ctu, |sz, m| visited.push((sz, m)));
        assert_eq!(visited.len(), 1);
        assert_eq!(visited[0], (6, PredMode::Intra(0)));
    }

    #[test]
    fn walk_leaves_split_ctu() {
        let mbs: [PredMode; 16] = std::array::from_fn(|i| PredMode::Intra(i as u8));
        let ctu = build_ctu_from_16_mbs(&mbs);
        let mut visited = Vec::new();
        walk_leaves(&ctu, |sz, m| visited.push((sz, m)));
        assert_eq!(visited.len(), 16);
        for (sz, _) in &visited {
            assert_eq!(*sz, 4, "all leaves should be 16×16 when no merges");
        }
    }

    #[test]
    fn cu_size_and_depth_invariants() {
        let mbs = [PredMode::Skip; 16];
        let ctu = build_ctu_from_16_mbs(&mbs);
        assert_eq!(ctu.side(), 64);
        assert_eq!(ctu.max_depth(), 0);
    }
}
