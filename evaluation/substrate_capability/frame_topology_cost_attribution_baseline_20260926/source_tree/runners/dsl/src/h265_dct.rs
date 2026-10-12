//! H.265 forward integer DCT — stage 3 of the H.264→H.265 transcoder.
//!
//!   STAGE: transform_kind
//!     rewrite:      h264_transform_set → h265_transform_set
//!     pattern:      block_local_matmul
//!     hardware:     AVX-512 FMA / BF16 (substrate-named for fast paths)
//!     topology:     embarrassingly_parallel_distribution (by CTU/block)
//!     bottleneck:   compute_bound
//!
//! ## Why integer (not BF16) for normative path
//!
//! H.265's transform is normative — encoder and decoder must produce
//! bit-identical results. The integer-DCT matrices in clause 8.6.4.2
//! are the standard's fixed choice. BF16 is for ENCODER-SIDE FAST
//! DECISIONS (mode RDO, fast scans) where ~1% error is fine; the
//! final transform that lands in the bitstream uses these integers.
//!
//! The substrate's `block_local_matmul_serves_simd_fma_or_bf16` rule
//! correctly names BF16 as one option — for the encoder's decision
//! layer. For the bitstream transform we use the standard's integer
//! matrices.
//!
//! ## Coverage
//!
//! v1 implements 4×4 and 8×8 forward DCT. These cover the bulk of
//! residual blocks in typical content; 16×16 and 32×32 are larger
//! matrices (16² and 32² coefficients) that follow the same pattern
//! and can be added incrementally.
//!
//! Reference: ITU-T H.265 (08/2024) clause 8.6.4.2 (transformation
//! process for scaled transform coefficients).

/// H.265 4×4 forward DCT-II matrix from clause 8.6.4.2.5.
/// Rows are basis vectors; columns indexed 0..3 across input samples.
pub const TRANS_4: [[i32; 4]; 4] = [
    [64, 64, 64, 64],
    [83, 36, -36, -83],
    [64, -64, -64, 64],
    [36, -83, 83, -36],
];

/// H.265 8×8 forward DCT-II matrix from clause 8.6.4.2.5.
pub const TRANS_8: [[i32; 8]; 8] = [
    [64, 64, 64, 64, 64, 64, 64, 64],
    [89, 75, 50, 18, -18, -50, -75, -89],
    [83, 36, -36, -83, -83, -36, 36, 83],
    [75, -18, -89, -50, 50, 89, 18, -75],
    [64, -64, -64, 64, 64, -64, -64, 64],
    [50, -89, 18, 75, -75, -18, 89, -50],
    [36, -83, 83, -36, -36, 83, -83, 36],
    [18, -50, 75, -89, 89, -75, 50, -18],
];

/// Stage-1 / stage-2 shifts for the H.265 transform pipeline. From
/// clause 8.6.4.2: shift1 = log2(N) - 1 + bd - 8; shift2 = log2(N) + 6
/// for the integer DCT. For 8-bit content (bd=8):
///   4×4:   shift1 = 1, shift2 = 8
///   8×8:   shift1 = 2, shift2 = 9
///   16×16: shift1 = 3, shift2 = 10
///   32×32: shift1 = 4, shift2 = 11
fn shifts(log2_n: u32) -> (u32, u32) {
    (log2_n - 1, log2_n + 6)
}

/// Forward 4×4 integer DCT-II per H.265. Input is row-major 4×4 i32
/// residual samples; output is row-major 4×4 transform coefficients.
///
/// Two-stage pipeline (clause 8.6.4.2):
///   tmp  = (TRANS_4 · X  + round1) >> shift1
///   out  = (TRANS_4 · tmpᵀ + round2) >> shift2
pub fn forward_dct_4x4(input: &[i32; 16]) -> [i32; 16] {
    let (shift1, shift2) = shifts(2);
    let round1 = 1 << (shift1 - 1);
    let round2 = 1 << (shift2 - 1);

    // Stage 1: column transform.  tmp[i][j] = sum_k T4[i][k] * X[k][j]
    let mut tmp = [0i32; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0i32;
            for k in 0..4 {
                s += TRANS_4[i][k] * input[k * 4 + j];
            }
            tmp[i * 4 + j] = (s + round1) >> shift1;
        }
    }

    // Stage 2: row transform.  out[i][j] = sum_k tmp[i][k] * T4[j][k]
    // i.e. T4^T applied from the right, which is just T4 on the
    // index pair (j, k) since T4 is real.
    let mut out = [0i32; 16];
    for i in 0..4 {
        for j in 0..4 {
            let mut s = 0i32;
            for k in 0..4 {
                s += tmp[i * 4 + k] * TRANS_4[j][k];
            }
            out[i * 4 + j] = (s + round2) >> shift2;
        }
    }
    out
}

/// Forward 8×8 integer DCT-II per H.265. Same two-stage structure
/// as 4×4 but with the 8×8 basis matrix.
pub fn forward_dct_8x8(input: &[i32; 64]) -> [i32; 64] {
    let (shift1, shift2) = shifts(3);
    let round1 = 1 << (shift1 - 1);
    let round2 = 1 << (shift2 - 1);

    let mut tmp = [0i32; 64];
    for i in 0..8 {
        for j in 0..8 {
            let mut s = 0i32;
            for k in 0..8 {
                s += TRANS_8[i][k] * input[k * 8 + j];
            }
            tmp[i * 8 + j] = (s + round1) >> shift1;
        }
    }

    let mut out = [0i32; 64];
    for i in 0..8 {
        for j in 0..8 {
            let mut s = 0i32;
            for k in 0..8 {
                s += tmp[i * 8 + k] * TRANS_8[j][k];
            }
            out[i * 8 + j] = (s + round2) >> shift2;
        }
    }
    out
}

/// Dispatch a forward DCT by log2 size. `log2_n` in {2, 3} = sizes
/// {4, 8}. Returns `None` for unsupported sizes; v1 covers the
/// common cases.
pub enum DctOutput {
    Size4([i32; 16]),
    Size8([i32; 64]),
}

pub fn forward_dct(log2_n: u32, input: &[i32]) -> Option<DctOutput> {
    match log2_n {
        2 if input.len() == 16 => {
            let mut buf = [0i32; 16];
            buf.copy_from_slice(input);
            Some(DctOutput::Size4(forward_dct_4x4(&buf)))
        }
        3 if input.len() == 64 => {
            let mut buf = [0i32; 64];
            buf.copy_from_slice(input);
            Some(DctOutput::Size8(forward_dct_8x8(&buf)))
        }
        _ => None,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// DC input → only DC output coefficient.  All input samples equal
    /// to a constant should produce a single nonzero output at [0][0]
    /// (energy concentrates at DC).
    #[test]
    fn dct_4x4_dc_only() {
        let input = [10i32; 16];
        let out = forward_dct_4x4(&input);
        assert!(out[0] != 0, "DC coefficient should be nonzero");
        for k in 1..16 {
            assert_eq!(
                out[k], 0,
                "non-DC coefficient at {} should be 0 for DC input; got {}",
                k, out[k]
            );
        }
    }

    #[test]
    fn dct_8x8_dc_only() {
        let input = [10i32; 64];
        let out = forward_dct_8x8(&input);
        assert!(out[0] != 0);
        for k in 1..64 {
            assert_eq!(
                out[k], 0,
                "non-DC coefficient at {} should be 0; got {}",
                k, out[k]
            );
        }
    }

    /// Zero input → zero output.
    #[test]
    fn dct_4x4_zero() {
        let input = [0i32; 16];
        let out = forward_dct_4x4(&input);
        assert_eq!(out, [0; 16]);
    }

    /// Energy concentration: vertical edge produces vertical-frequency
    /// coefficients on the first column; horizontal-frequency
    /// coefficients should be zero by symmetry.
    #[test]
    fn dct_4x4_vertical_edge_concentrates_vertical_freq() {
        // Vertical edge: top half +N, bottom half -N.
        let input = [
            100, 100, 100, 100, 100, 100, 100, 100, -100, -100, -100, -100, -100, -100, -100, -100,
        ];
        let out = forward_dct_4x4(&input);
        // Row 0 (DC) should be zero — input is anti-symmetric vertically.
        for j in 0..4 {
            assert_eq!(
                out[0 * 4 + j],
                0,
                "DC row should be 0 for anti-symmetric input; col {} = {}",
                j,
                out[j]
            );
        }
        // First column (j=0) should have nonzero vertical-frequency
        // entries at rows 1 and 3 (the odd basis functions).
        assert!(
            out[1 * 4 + 0] != 0,
            "vertical-freq coefficient at (1,0) should be nonzero"
        );
        // Columns 1..3 should be zero (no horizontal frequency content).
        for i in 0..4 {
            for j in 1..4 {
                assert_eq!(
                    out[i * 4 + j],
                    0,
                    "horizontal-freq coefficient at ({},{}) should be 0; got {}",
                    i,
                    j,
                    out[i * 4 + j]
                );
            }
        }
    }

    /// Forward DCT preserves the parity of input rows: an input with
    /// vertical symmetry about the centre should produce zero rows at
    /// odd basis indices (rows 1, 3).
    #[test]
    fn dct_4x4_vertical_symmetric_zeros_odd_rows() {
        // Symmetric vertically.
        let input = [
            50, 50, 50, 50, 100, 100, 100, 100, 100, 100, 100, 100, 50, 50, 50, 50,
        ];
        let out = forward_dct_4x4(&input);
        for j in 0..4 {
            assert_eq!(
                out[1 * 4 + j],
                0,
                "row 1 col {} should be 0 for v-symmetric input; got {}",
                j,
                out[4 + j]
            );
            assert_eq!(
                out[3 * 4 + j],
                0,
                "row 3 col {} should be 0; got {}",
                j,
                out[12 + j]
            );
        }
    }

    /// Dispatcher returns the right variant per size.
    #[test]
    fn dispatch_4x4_returns_size4() {
        let input = vec![1i32; 16];
        let out = forward_dct(2, &input).expect("4x4 dispatch");
        match out {
            DctOutput::Size4(_) => {}
            _ => panic!("expected Size4"),
        }
    }

    #[test]
    fn dispatch_8x8_returns_size8() {
        let input = vec![1i32; 64];
        let out = forward_dct(3, &input).expect("8x8 dispatch");
        match out {
            DctOutput::Size8(_) => {}
            _ => panic!("expected Size8"),
        }
    }

    #[test]
    fn dispatch_unsupported_returns_none() {
        let input = vec![1i32; 256];
        assert!(
            forward_dct(4, &input).is_none(),
            "16x16 not in v1; should return None"
        );
    }

    #[test]
    fn dispatch_wrong_length_returns_none() {
        let input = vec![1i32; 15]; // 4×4 wants 16
        assert!(forward_dct(2, &input).is_none());
    }
}
