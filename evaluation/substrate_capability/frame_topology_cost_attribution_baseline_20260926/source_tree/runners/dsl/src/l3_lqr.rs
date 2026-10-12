//! L3 LQR — Linear Quadratic Regulator with iterative DARE solver.
//!
//! Realises the `lqr_optimal_when_linear_quadratic` component of the
//! `drives_estimation_control` Mt (commit 1b9a7e0).
//!
//! ## What LQR solves
//!
//! For a discrete-time linear system:
//!   x[k+1] = A x[k] + B u[k]
//! and quadratic cost:
//!   J = Σ (x^T Q x + u^T R u)
//!
//! the optimal infinite-horizon state-feedback control law is:
//!   u[k] = -K x[k]
//! where K = (R + B^T P B)^-1 B^T P A
//! and P solves the Discrete Algebraic Riccati Equation (DARE):
//!   P = A^T P A - A^T P B (R + B^T P B)^-1 B^T P A + Q
//!
//! LQR is inherently multi-input multi-output (matrix-valued). For
//! single-state substrate drives, the matrices are 1×1 and the math
//! collapses to scalars; we still go through the full matrix path
//! for correctness + future multi-dim drives.
//!
//! ## DARE solver
//!
//! Iterative substitution: P_0 = Q; iterate the DARE equation until
//! ||P_{k+1} - P_k||_F < tol. Convergence is guaranteed when (A, B)
//! is stabilisable and (A, Q^{1/2}) is detectable — the conditions
//! the substrate's drive systems satisfy by construction (drives
//! whose dynamics aren't stabilisable shouldn't be drives).
//!
//! Iterative substitution is simple, has no external dependencies,
//! and converges in O(20-100) iterations for the small dimensions
//! (≤ 8) the substrate cares about. For larger systems, Newton or
//! Schur-based methods would be faster — substrate doesn't need
//! that complexity at L3 v1.
//!
//! ## Matrix support
//!
//! Rolled inline rather than depending on `nalgebra` or `ndarray`.
//! Substrate's drive matrices are small (1-8 dimensions); a
//! Vec-backed `Mat` with Gauss-Jordan inversion is sufficient.
//! Adding 2-3 MB of nalgebra to the binary for LQR isn't justified.

use crate::l3_drives::Controller;

// =======================================================================
// Mat — small dense f64 matrix, row-major.
// =======================================================================

/// FP64 → BF16 conversion with round-to-nearest-even. Used by the
/// BF16 matmul path. BF16 = upper 16 bits of FP32 representation.
#[inline]
fn fp64_to_bf16(v: f64) -> u16 {
    let f = v as f32;
    let bits = f.to_bits();
    // Round-to-nearest-even: add bias depending on the bit being
    // truncated + the sticky bit.
    let bias = 0x7FFF + ((bits >> 16) & 1);
    let rounded = bits.wrapping_add(bias);
    (rounded >> 16) as u16
}

/// BF16 → FP64 conversion: shift bits to upper 16 of FP32, then
/// widen. Lossy beyond BF16 precision.
#[inline]
fn bf16_to_fp64(bf: u16) -> f64 {
    let bits = (bf as u32) << 16;
    f32::from_bits(bits) as f64
}

impl Bf16PackedB {
    /// Reconstruct the FP64 matrix this was packed from (lossy due to
    /// BF16 precision). Used for the rare non-AVX-512 fallback path.
    pub fn to_f64_mat(&self) -> Mat {
        let mut m = Mat::zeros(self.k_rows, self.n_cols);
        let kp = self.k_rows / 2;
        for kkp in 0..kp {
            for j in 0..self.n_cols {
                let pair = self.paired[kkp * self.n_cols + j];
                let lo = (pair & 0xFFFF) as u16;
                let hi = ((pair >> 16) & 0xFFFF) as u16;
                m.set(2 * kkp, j, bf16_to_fp64(lo));
                m.set(2 * kkp + 1, j, bf16_to_fp64(hi));
            }
        }
        m
    }
}

/// Pre-packed BF16 right-operand for `Mat::mul_bf16_pre_b`. Amortises
/// the pair-row conversion cost across many matmuls against the same
/// B matrix (e.g. caching C and P in Kalman update steps).
///
/// Layout: `paired[kp * n_cols + j]` is a u32 whose low 16 bits are
/// `bf16(B[2*kp][j])` and high 16 bits are `bf16(B[2*kp+1][j])` — the
/// interleaved form VDPBF16PS expects.
#[derive(Debug, Clone)]
pub struct Bf16PackedB {
    paired: Vec<u32>,
    /// K (rows of source); must be even.
    pub k_rows: usize,
    /// N (cols of source); must be multiple of 16.
    pub n_cols: usize,
}

/// Small dense matrix, row-major f64. Intended for LQR with state
/// dimension ≤ ~8; for larger problems, a proper linear algebra
/// crate would be the right move.
#[derive(Debug, Clone)]
pub struct Mat {
    rows: usize,
    cols: usize,
    /// Row-major: `data[i * cols + j] = (i,j)`.
    data: Vec<f64>,
}

impl Mat {
    pub fn zeros(rows: usize, cols: usize) -> Self {
        Self {
            rows,
            cols,
            data: vec![0.0; rows * cols],
        }
    }

    pub fn identity(n: usize) -> Self {
        let mut m = Self::zeros(n, n);
        for i in 0..n {
            m.set(i, i, 1.0);
        }
        m
    }

    /// Construct from a slice-of-slices. All inner slices must have
    /// the same length.
    pub fn from_rows(rows: &[&[f64]]) -> Self {
        let n_rows = rows.len();
        if n_rows == 0 {
            return Self::zeros(0, 0);
        }
        let n_cols = rows[0].len();
        let mut data = Vec::with_capacity(n_rows * n_cols);
        for r in rows {
            assert_eq!(r.len(), n_cols, "inconsistent row lengths");
            data.extend_from_slice(r);
        }
        Self {
            rows: n_rows,
            cols: n_cols,
            data,
        }
    }

    pub fn rows(&self) -> usize {
        self.rows
    }
    pub fn cols(&self) -> usize {
        self.cols
    }

    #[inline]
    pub fn get(&self, i: usize, j: usize) -> f64 {
        self.data[i * self.cols + j]
    }

    #[inline]
    pub fn set(&mut self, i: usize, j: usize, v: f64) {
        self.data[i * self.cols + j] = v;
    }

    /// C = A + B (dimensions must match).
    pub fn add(&self, other: &Mat) -> Mat {
        assert_eq!(self.rows, other.rows);
        assert_eq!(self.cols, other.cols);
        let mut out = Self::zeros(self.rows, self.cols);
        for i in 0..self.data.len() {
            out.data[i] = self.data[i] + other.data[i];
        }
        out
    }

    /// C = A - B.
    pub fn sub(&self, other: &Mat) -> Mat {
        assert_eq!(self.rows, other.rows);
        assert_eq!(self.cols, other.cols);
        let mut out = Self::zeros(self.rows, self.cols);
        for i in 0..self.data.len() {
            out.data[i] = self.data[i] - other.data[i];
        }
        out
    }

    /// C = A · B. Inner dims must match (A.cols == B.rows).
    pub fn mul(&self, other: &Mat) -> Mat {
        assert_eq!(
            self.cols, other.rows,
            "inner dims mismatch: {}x{} * {}x{}",
            self.rows, self.cols, other.rows, other.cols
        );
        // Dispatch to AVX-512 path when:
        //   · built with the `avx512` Cargo feature (default OFF — the
        //     intrinsics `mul_avx512` uses are unstable on this crate's
        //     baseline toolchain, see AVX512_PORTABILITY_FIX_RESULTS.md)
        //   · target is x86_64 with AVX-512F at runtime
        //   · inner-row width (other.cols) ≥ 8 (one SIMD lane)
        // Smaller widths, or a default (`avx512` feature off) build,
        // fall through to the scalar path.
        #[cfg(all(target_arch = "x86_64", feature = "avx512"))]
        {
            if other.cols >= 8 && is_x86_feature_detected!("avx512f") {
                return unsafe { self.mul_avx512(other) };
            }
        }
        self.mul_scalar(other)
    }

    /// Scalar reference impl — also the fallback when AVX-512 isn't
    /// available. The (i, k, j) loop order keeps `other`'s row reads
    /// sequential, which is cache-friendlier than (i, j, k).
    fn mul_scalar(&self, other: &Mat) -> Mat {
        let mut out = Self::zeros(self.rows, other.cols);
        for i in 0..self.rows {
            for k in 0..self.cols {
                let aik = self.get(i, k);
                if aik == 0.0 {
                    continue;
                }
                for j in 0..other.cols {
                    let cur = out.get(i, j);
                    out.set(i, j, cur + aik * other.get(k, j));
                }
            }
        }
        out
    }

    /// AVX-512 BF16 matrix multiplication via VDPBF16PS. SAFETY:
    /// caller must ensure the runtime supports `avx512f` AND
    /// `avx512bf16`.
    ///
    /// Strategy: outer-product-pair. For each output element
    /// `c[i][j]`, accumulate over k in pairs (k, k+1):
    ///   c[i][j] += a[i][k]·b[k][j] + a[i][k+1]·b[k+1][j]
    /// using `VDPBF16PS` which does this exact 2-element BF16 dot
    /// product into FP32 accumulators, 16 lanes at a time.
    ///
    /// Precision: BF16 has ~7 mantissa bits (vs 52 for FP64). For
    /// Kalman covariance updates this is usually acceptable (the
    /// covariance is itself an approximation); for the matrix
    /// inverse step, callers should keep FP64.
    ///
    /// Throughput: Zen 5 dispatches 2 VDPBF16PS/cycle; each does
    /// 32 BF16 multiplies + 16 FP32 adds = 96 FP-ops/cycle/unit
    /// = ~960 GFLOPs single-core (BF16-effective) at ~5 GHz.
    ///
    /// Falls back to `mul` when dimensions aren't compatible
    /// (requires `k % 2 == 0`, `n % 16 == 0`, both ≥ minimum), when the
    /// runtime lacks AVX-512F/BF16, or when this crate was built
    /// without the `avx512` Cargo feature (default OFF — the
    /// intrinsics `mul_bf16_inner` uses are unstable on this crate's
    /// baseline toolchain, see AVX512_PORTABILITY_FIX_RESULTS.md; the
    /// fallback is exact FP64 `mul`, which is strictly more precise
    /// than the BF16 path it replaces).
    #[cfg(target_arch = "x86_64")]
    pub fn mul_bf16(&self, other: &Mat) -> Mat {
        assert_eq!(
            self.cols, other.rows,
            "inner dims mismatch: {}x{} * {}x{}",
            self.rows, self.cols, other.rows, other.cols
        );
        #[cfg(feature = "avx512")]
        {
            let k = self.cols;
            let n = other.cols;
            // Require K even (pair-reduction) and N a multiple of 16
            // (SIMD lane width). Otherwise scalar path.
            if k >= 2
                && n >= 16
                && k % 2 == 0
                && n % 16 == 0
                && is_x86_feature_detected!("avx512f")
                && is_x86_feature_detected!("avx512bf16")
            {
                return unsafe { self.mul_bf16_inner(other) };
            }
        }
        self.mul(other)
    }

    #[cfg(all(target_arch = "x86_64", feature = "avx512"))]
    #[target_feature(enable = "avx512f,avx512bf16")]
    unsafe fn mul_bf16_inner(&self, other: &Mat) -> Mat {
        use std::arch::x86_64::*;
        let m = self.rows;
        let k = self.cols;
        let n = other.cols;

        // VDPBF16PS layout requirement: for output lane j, the
        // accumulator gets x[2j]*y[2j] + x[2j+1]*y[2j+1] — i.e.
        // x and y must be INTERLEAVED so consecutive BF16 indices
        // (2j, 2j+1) belong to the K-pair (k_idx, k_idx+1).
        //
        // Pre-pack B into "pair-row" layout: b_paired[kp][j] is a
        // u32 whose low 16 bits are bf16(B[2*kp][j]) and high 16
        // bits are bf16(B[2*kp+1][j]). Loading 16 u32s as __m512bh
        // gives exactly the interleaved layout DPBF16PS expects.

        let a_bf16: Vec<u16> = self.data.iter().map(|v| fp64_to_bf16(*v)).collect();

        let kp = k / 2;
        let mut b_paired: Vec<u32> = Vec::with_capacity(kp * n);
        for kkp in 0..kp {
            for j in 0..n {
                let lo = fp64_to_bf16(other.data[(2 * kkp) * n + j]) as u32;
                let hi = fp64_to_bf16(other.data[(2 * kkp + 1) * n + j]) as u32;
                b_paired.push(lo | (hi << 16));
            }
        }

        let mut out = Self::zeros(m, n);
        let c_ptr = out.data.as_mut_ptr();
        let n_blocks = n / 16;

        for i in 0..m {
            for jb in 0..n_blocks {
                let mut c_v = _mm512_setzero_ps();
                for kkp in 0..kp {
                    // Pack A pair (bf16(a[i][2*kkp]), bf16(a[i][2*kkp+1]))
                    // as a single u32; broadcast to all 16 lanes.
                    let a_lo = a_bf16[i * k + 2 * kkp] as u32;
                    let a_hi = a_bf16[i * k + 2 * kkp + 1] as u32;
                    let a_pair_bits = a_lo | (a_hi << 16);
                    let a_v_si = _mm512_set1_epi32(a_pair_bits as i32);
                    let a_v_bh: __m512bh = std::mem::transmute(a_v_si);

                    // Load 16 pre-packed B pair u32s = 16 BF16 pairs.
                    let b_ptr = b_paired.as_ptr().add(kkp * n + jb * 16);
                    let b_v_si = _mm512_loadu_si512(b_ptr as *const _);
                    let b_v_bh: __m512bh = std::mem::transmute(b_v_si);

                    // c[i][j..j+16] += a_pair · b_pair (FP32 acc)
                    c_v = _mm512_dpbf16_ps(c_v, a_v_bh, b_v_bh);
                }
                // Store 16 FP32 results → FP64 output.
                let mut c_arr = [0.0_f32; 16];
                _mm512_storeu_ps(c_arr.as_mut_ptr(), c_v);
                for jj in 0..16 {
                    *c_ptr.add(i * n + jb * 16 + jj) = c_arr[jj] as f64;
                }
            }
        }
        out
    }

    /// Pre-pack this matrix as a BF16 right-operand. Returns `None`
    /// if dimensions don't qualify (`k_rows % 2 != 0` or
    /// `n_cols % 16 != 0`). The packed representation can be reused
    /// across many `mul_bf16_pre_b` calls — the substrate's Kalman
    /// path caches its constant matrices (C, C^T) and re-packs P
    /// once per update, amortising conversion overhead.
    pub fn pack_for_bf16_b(&self) -> Option<Bf16PackedB> {
        let k = self.rows;
        let n = self.cols;
        if k < 2 || n < 16 || k % 2 != 0 || n % 16 != 0 {
            return None;
        }
        let kp = k / 2;
        let mut paired = Vec::with_capacity(kp * n);
        for kkp in 0..kp {
            for j in 0..n {
                let lo = fp64_to_bf16(self.data[(2 * kkp) * n + j]) as u32;
                let hi = fp64_to_bf16(self.data[(2 * kkp + 1) * n + j]) as u32;
                paired.push(lo | (hi << 16));
            }
        }
        Some(Bf16PackedB {
            paired,
            k_rows: k,
            n_cols: n,
        })
    }

    /// BF16 matmul using a pre-packed B. Caller must have ensured the
    /// runtime supports AVX-512 BF16 by previously calling
    /// `pack_for_bf16_b` (which only returns Some when dimensions
    /// qualify); this method asserts internal dims + checks features.
    /// Falls back to scalar conversion-from-packed when SIMD isn't
    /// available (rare; for portability) OR when this crate was built
    /// without the `avx512` Cargo feature (default OFF — see
    /// AVX512_PORTABILITY_FIX_RESULTS.md).
    #[cfg(target_arch = "x86_64")]
    pub fn mul_bf16_pre_b(&self, packed: &Bf16PackedB) -> Mat {
        assert_eq!(
            self.cols, packed.k_rows,
            "inner dims mismatch: {}x{} * (packed K={})",
            self.rows, self.cols, packed.k_rows
        );
        #[cfg(feature = "avx512")]
        {
            if is_x86_feature_detected!("avx512f") && is_x86_feature_detected!("avx512bf16") {
                return unsafe { self.mul_bf16_pre_b_inner(packed) };
            }
        }
        // Scalar fallback: reconstruct B from packed (lossy due to
        // BF16 → FP64) + multiply. Used on non-AVX-512 hosts and on
        // any build without the `avx512` feature.
        let b = packed.to_f64_mat();
        self.mul_scalar(&b)
    }

    #[cfg(all(target_arch = "x86_64", feature = "avx512"))]
    #[target_feature(enable = "avx512f,avx512bf16")]
    unsafe fn mul_bf16_pre_b_inner(&self, packed: &Bf16PackedB) -> Mat {
        use std::arch::x86_64::*;
        let m = self.rows;
        let k = self.cols;
        let n = packed.n_cols;
        // A is converted to BF16 row-major u16 on the fly. Conversion
        // is O(m*k) — cheap for typical Kalman dimensions.
        let a_bf16: Vec<u16> = self.data.iter().map(|v| fp64_to_bf16(*v)).collect();

        let mut out = Self::zeros(m, n);
        let c_ptr = out.data.as_mut_ptr();
        let n_blocks = n / 16;
        let kp = k / 2;

        for i in 0..m {
            for jb in 0..n_blocks {
                let mut c_v = _mm512_setzero_ps();
                for kkp in 0..kp {
                    let a_lo = a_bf16[i * k + 2 * kkp] as u32;
                    let a_hi = a_bf16[i * k + 2 * kkp + 1] as u32;
                    let a_pair_bits = a_lo | (a_hi << 16);
                    let a_v_si = _mm512_set1_epi32(a_pair_bits as i32);
                    let a_v_bh: __m512bh = std::mem::transmute(a_v_si);

                    let b_ptr = packed.paired.as_ptr().add(kkp * n + jb * 16);
                    let b_v_si = _mm512_loadu_si512(b_ptr as *const _);
                    let b_v_bh: __m512bh = std::mem::transmute(b_v_si);

                    c_v = _mm512_dpbf16_ps(c_v, a_v_bh, b_v_bh);
                }
                let mut c_arr = [0.0_f32; 16];
                _mm512_storeu_ps(c_arr.as_mut_ptr(), c_v);
                for jj in 0..16 {
                    *c_ptr.add(i * n + jb * 16 + jj) = c_arr[jj] as f64;
                }
            }
        }
        out
    }

    /// AVX-512 FP64 matrix multiplication. SAFETY: caller must
    /// ensure the runtime supports `avx512f` (checked by the public
    /// `mul` dispatcher).
    ///
    /// Strategy: same (i, k, j) loop order as scalar, but the j-loop
    /// is vectorised — for each (i, k), broadcast `aik` to a 512-bit
    /// register + FMA against 8 consecutive elements of B's row.
    /// 8 wide × FP64 = 64 bits × 8 = one AVX-512 vector.
    ///
    /// On Zen 5 with 2 FMA units at ~5 GHz, peak ~160 GFLOPs FP64.
    /// A 64×64×64 matmul = 524288 FLOPs ≈ 3.3 µs at peak.
    ///
    /// Closes the Bench 3c 64-dim Kalman gap from commit b0a7954.
    ///
    /// Gated behind the `avx512` Cargo feature (default OFF — see
    /// AVX512_PORTABILITY_FIX_RESULTS.md).
    #[cfg(all(target_arch = "x86_64", feature = "avx512"))]
    #[target_feature(enable = "avx512f")]
    unsafe fn mul_avx512(&self, other: &Mat) -> Mat {
        use std::arch::x86_64::*;
        let m = self.rows;
        let k_dim = self.cols;
        let n = other.cols;
        let mut out = Self::zeros(m, n);
        let a_ptr = self.data.as_ptr();
        let b_ptr = other.data.as_ptr();
        let c_ptr = out.data.as_mut_ptr();
        let n_simd = n - (n % 8);
        for i in 0..m {
            for k in 0..k_dim {
                let aik = *a_ptr.add(i * k_dim + k);
                if aik == 0.0 {
                    continue;
                }
                let aik_v = _mm512_set1_pd(aik);
                let b_row = b_ptr.add(k * n);
                let c_row = c_ptr.add(i * n);
                let mut j = 0;
                while j < n_simd {
                    let b_v = _mm512_loadu_pd(b_row.add(j));
                    let c_v = _mm512_loadu_pd(c_row.add(j));
                    let new_c = _mm512_fmadd_pd(aik_v, b_v, c_v);
                    _mm512_storeu_pd(c_row.add(j), new_c);
                    j += 8;
                }
                // Scalar tail for trailing < 8 columns.
                while j < n {
                    *c_row.add(j) += aik * *b_row.add(j);
                    j += 1;
                }
            }
        }
        out
    }

    /// A^T. Returns a new matrix.
    pub fn transpose(&self) -> Mat {
        let mut out = Self::zeros(self.cols, self.rows);
        for i in 0..self.rows {
            for j in 0..self.cols {
                out.set(j, i, self.get(i, j));
            }
        }
        out
    }

    /// Gauss-Jordan inverse for small square matrices. Returns None
    /// if singular (pivot below `eps`). Eps = 1e-12 default.
    pub fn inverse(&self) -> Option<Mat> {
        assert_eq!(self.rows, self.cols, "inverse requires square");
        let n = self.rows;
        // Build augmented [A | I].
        let mut aug = vec![0.0_f64; n * 2 * n];
        for i in 0..n {
            for j in 0..n {
                aug[i * 2 * n + j] = self.get(i, j);
            }
            aug[i * 2 * n + n + i] = 1.0;
        }
        let eps = 1e-12;
        for col in 0..n {
            // Find pivot — partial pivoting.
            let mut pivot_row = col;
            let mut max_abs = aug[col * 2 * n + col].abs();
            for r in (col + 1)..n {
                let v = aug[r * 2 * n + col].abs();
                if v > max_abs {
                    max_abs = v;
                    pivot_row = r;
                }
            }
            if max_abs < eps {
                return None; // singular
            }
            if pivot_row != col {
                for j in 0..(2 * n) {
                    aug.swap(col * 2 * n + j, pivot_row * 2 * n + j);
                }
            }
            // Normalise pivot row.
            let piv = aug[col * 2 * n + col];
            for j in 0..(2 * n) {
                aug[col * 2 * n + j] /= piv;
            }
            // Eliminate other rows.
            for r in 0..n {
                if r == col {
                    continue;
                }
                let factor = aug[r * 2 * n + col];
                if factor == 0.0 {
                    continue;
                }
                for j in 0..(2 * n) {
                    aug[r * 2 * n + j] -= factor * aug[col * 2 * n + j];
                }
            }
        }
        // Extract right half = A^-1.
        let mut inv = Self::zeros(n, n);
        for i in 0..n {
            for j in 0..n {
                inv.set(i, j, aug[i * 2 * n + n + j]);
            }
        }
        Some(inv)
    }

    /// ||A||_F = sqrt(Σ a_ij^2). Used for DARE convergence test.
    pub fn frobenius_norm(&self) -> f64 {
        self.data.iter().map(|x| x * x).sum::<f64>().sqrt()
    }
}

// =======================================================================
// DARE solver
// =======================================================================

#[derive(Debug, Clone, PartialEq)]
pub enum LqrError {
    /// Matrix dimensions don't form a coherent LQR system.
    DimensionMismatch { what: String },
    /// (R + B^T P B) was singular during DARE iteration. Suggests
    /// R isn't positive-definite.
    SingularRplusBPB,
    /// DARE iteration didn't reach `tolerance` within `max_iter`.
    /// Contains the achieved residual for diagnostics.
    DareDidNotConverge {
        iterations: usize,
        final_residual: f64,
    },
}

/// Solve the DARE iteratively. Returns the stabilising P.
///
/// - `a`: state transition (n×n)
/// - `b`: input gain (n×m)
/// - `q`: state cost (n×n, symmetric positive-semidefinite)
/// - `r`: input cost (m×m, symmetric positive-definite)
/// - `max_iter`: cap on iterations (suggest 500 for small systems)
/// - `tolerance`: ||P_new - P||_F < tolerance terminates (e.g. 1e-9)
pub fn solve_dare(
    a: &Mat,
    b: &Mat,
    q: &Mat,
    r: &Mat,
    max_iter: usize,
    tolerance: f64,
) -> Result<Mat, LqrError> {
    let n = a.rows();
    let m = b.cols();
    if a.cols() != n {
        return Err(LqrError::DimensionMismatch {
            what: format!("A must be square; got {}x{}", a.rows(), a.cols()),
        });
    }
    if b.rows() != n {
        return Err(LqrError::DimensionMismatch {
            what: format!("B rows ({}) must equal A rows ({})", b.rows(), n),
        });
    }
    if q.rows() != n || q.cols() != n {
        return Err(LqrError::DimensionMismatch {
            what: format!("Q must be {}x{}; got {}x{}", n, n, q.rows(), q.cols()),
        });
    }
    if r.rows() != m || r.cols() != m {
        return Err(LqrError::DimensionMismatch {
            what: format!("R must be {}x{}; got {}x{}", m, m, r.rows(), r.cols()),
        });
    }

    let a_t = a.transpose();
    let b_t = b.transpose();

    // P_0 = Q.
    let mut p = q.clone();
    for it in 0..max_iter {
        // R + B^T P B  (m × m)
        let bt_p = b_t.mul(&p);
        let bt_p_b = bt_p.mul(b);
        let r_plus = r.add(&bt_p_b);

        // (R + B^T P B)^-1
        let r_plus_inv = match r_plus.inverse() {
            Some(inv) => inv,
            None => return Err(LqrError::SingularRplusBPB),
        };

        // K terms: B^T P A; ... in DARE we'll compute A^T P B (R+...)⁻¹ B^T P A.
        let bt_p_a = bt_p.mul(a); // m × n
        let bt_p_a_t = bt_p_a.transpose(); // n × m  (== A^T P B)
        let middle = r_plus_inv.mul(&bt_p_a); // m × n
        let subtracted = bt_p_a_t.mul(&middle); // n × n

        let a_t_p = a_t.mul(&p);
        let a_t_p_a = a_t_p.mul(a);
        let p_new = a_t_p_a.sub(&subtracted).add(q);

        let residual = p_new.sub(&p).frobenius_norm();
        p = p_new;
        if residual < tolerance {
            return Ok(p);
        }
        // If iteration count exceeded, fall through to error after loop.
        let _ = it;
    }
    let final_residual = {
        // Recompute final residual against the most recent P.
        let bt_p = b_t.mul(&p);
        let bt_p_b = bt_p.mul(b);
        let r_plus = r.add(&bt_p_b);
        let r_plus_inv = r_plus.inverse().ok_or(LqrError::SingularRplusBPB)?;
        let bt_p_a = bt_p.mul(a);
        let bt_p_a_t = bt_p_a.transpose();
        let middle = r_plus_inv.mul(&bt_p_a);
        let subtracted = bt_p_a_t.mul(&middle);
        let a_t_p = a_t.mul(&p);
        let a_t_p_a = a_t_p.mul(a);
        let p_new = a_t_p_a.sub(&subtracted).add(q);
        p_new.sub(&p).frobenius_norm()
    };
    Err(LqrError::DareDidNotConverge {
        iterations: max_iter,
        final_residual,
    })
}

/// Compute the LQR gain K = (R + B^T P B)^-1 B^T P A from a solved P.
pub fn compute_lqr_gain(a: &Mat, b: &Mat, r: &Mat, p: &Mat) -> Result<Mat, LqrError> {
    let b_t = b.transpose();
    let bt_p = b_t.mul(p);
    let bt_p_b = bt_p.mul(b);
    let r_plus = r.add(&bt_p_b);
    let r_plus_inv = r_plus.inverse().ok_or(LqrError::SingularRplusBPB)?;
    let bt_p_a = bt_p.mul(a);
    Ok(r_plus_inv.mul(&bt_p_a))
}

// =======================================================================
// LqrController — full multi-dim
// =======================================================================

/// Multi-input multi-output LQR controller.
pub struct LqrController {
    pub gain: Mat,
    pub state_dim: usize,
    pub input_dim: usize,
}

impl LqrController {
    /// Solve DARE + compute gain. Default tolerance 1e-9, max_iter 500.
    pub fn from_system(a: &Mat, b: &Mat, q: &Mat, r: &Mat) -> Result<Self, LqrError> {
        Self::from_system_with(a, b, q, r, 500, 1e-9)
    }

    pub fn from_system_with(
        a: &Mat,
        b: &Mat,
        q: &Mat,
        r: &Mat,
        max_iter: usize,
        tolerance: f64,
    ) -> Result<Self, LqrError> {
        let p = solve_dare(a, b, q, r, max_iter, tolerance)?;
        let k = compute_lqr_gain(a, b, r, &p)?;
        Ok(Self {
            gain: k,
            state_dim: a.rows(),
            input_dim: b.cols(),
        })
    }

    /// Compute u = -K x for the regulation problem (drive state x to 0).
    /// For a setpoint-tracking variant, the caller should pass
    /// `x - setpoint` instead of `x`.
    pub fn control(&self, x: &[f64]) -> Vec<f64> {
        assert_eq!(x.len(), self.state_dim);
        let mut u = vec![0.0; self.input_dim];
        for i in 0..self.input_dim {
            let mut s = 0.0;
            for j in 0..self.state_dim {
                s += self.gain.get(i, j) * x[j];
            }
            u[i] = -s;
        }
        u
    }
}

// =======================================================================
// ScalarLqrController — Controller-trait wrapper for 1D drives
// =======================================================================

/// Scalar LQR controller — collapses the matrix LQR to scalar gain
/// for use with the existing 1-D `Drive` surface. Plug-replaceable
/// with `PidController` via the `Controller` trait.
pub struct ScalarLqrController {
    /// The scalar gain K (1×1 matrix's only entry).
    pub gain: f64,
}

impl ScalarLqrController {
    /// Construct from scalar system: x[k+1] = a·x + b·u; cost q·x² + r·u².
    /// Both q, r > 0 required for a well-posed problem.
    pub fn from_scalar(a: f64, b: f64, q: f64, r: f64) -> Result<Self, LqrError> {
        if q <= 0.0 || r <= 0.0 {
            return Err(LqrError::DimensionMismatch {
                what: "Q and R must be positive for scalar LQR".to_string(),
            });
        }
        let am = Mat::from_rows(&[&[a]]);
        let bm = Mat::from_rows(&[&[b]]);
        let qm = Mat::from_rows(&[&[q]]);
        let rm = Mat::from_rows(&[&[r]]);
        let lqr = LqrController::from_system(&am, &bm, &qm, &rm)?;
        Ok(Self {
            gain: lqr.gain.get(0, 0),
        })
    }
}

impl Controller for ScalarLqrController {
    /// step(error, _) = K · error. (LQR gain applied to the
    /// setpoint-tracking error; equivalent to u = -K(x - setpoint).)
    fn step(&mut self, error: f64, _dt: f64) -> f64 {
        self.gain * error
    }
    /// LQR has no integrator state; reset is a no-op.
    fn reset(&mut self) {}
}

#[cfg(test)]
mod tests {
    use super::*;

    fn approx_eq(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    // ---------- Mat sanity ----------

    #[test]
    fn mat_inverse_identity_is_identity() {
        let i = Mat::identity(3);
        let inv = i.inverse().unwrap();
        for r in 0..3 {
            for c in 0..3 {
                let expected = if r == c { 1.0 } else { 0.0 };
                assert!((inv.get(r, c) - expected).abs() < 1e-12);
            }
        }
    }

    #[test]
    fn mat_inverse_2x2_known() {
        // [[1, 2], [3, 4]] inverse = [[-2, 1], [1.5, -0.5]]
        let m = Mat::from_rows(&[&[1.0, 2.0], &[3.0, 4.0]]);
        let inv = m.inverse().unwrap();
        assert!((inv.get(0, 0) - (-2.0)).abs() < 1e-12);
        assert!((inv.get(0, 1) - 1.0).abs() < 1e-12);
        assert!((inv.get(1, 0) - 1.5).abs() < 1e-12);
        assert!((inv.get(1, 1) - (-0.5)).abs() < 1e-12);
    }

    #[test]
    fn mat_inverse_singular_returns_none() {
        // Singular: rows linearly dependent.
        let m = Mat::from_rows(&[&[1.0, 2.0], &[2.0, 4.0]]);
        assert!(m.inverse().is_none());
    }

    #[test]
    fn mat_multiplication_identity_is_self() {
        let m = Mat::from_rows(&[&[1.0, 2.0, 3.0], &[4.0, 5.0, 6.0]]);
        let i = Mat::identity(3);
        let p = m.mul(&i);
        for r in 0..2 {
            for c in 0..3 {
                assert!((p.get(r, c) - m.get(r, c)).abs() < 1e-12);
            }
        }
    }

    /// BF16 matmul matches scalar within precision-appropriate
    /// tolerance. BF16 has ~7 mantissa bits = ~3 decimal digits;
    /// over 64-deep summation, relative error grows but should
    /// stay < ~1%.
    #[test]
    fn bf16_matmul_within_precision_tolerance() {
        #[cfg(target_arch = "x86_64")]
        if !cfg!(feature = "avx512") || !is_x86_feature_detected!("avx512bf16") {
            eprintln!("avx512 feature not enabled or avx512bf16 not detected, skipping BF16 test");
            return;
        }
        for n in [16, 32, 64] {
            let mut a = Mat::zeros(n, n);
            let mut b = Mat::zeros(n, n);
            for i in 0..n {
                for j in 0..n {
                    a.set(i, j, ((i * 31 + j * 17) % 23) as f64 * 0.1);
                    b.set(i, j, ((i * 11 + j * 41) % 19) as f64 * 0.05);
                }
            }
            let c_scalar = a.mul_scalar(&b);
            let c_bf16 = a.mul_bf16(&b);
            let mut max_rel = 0.0_f64;
            for i in 0..n {
                for j in 0..n {
                    let s = c_scalar.get(i, j);
                    let v = c_bf16.get(i, j);
                    let rel = if s.abs() > 1e-9 {
                        (v - s).abs() / s.abs()
                    } else {
                        (v - s).abs()
                    };
                    if rel > max_rel {
                        max_rel = rel;
                    }
                }
            }
            assert!(
                max_rel < 0.02,
                "BF16 max relative error n={} = {} (must be < 2%)",
                n,
                max_rel
            );
        }
    }

    /// AVX-512 path produces identical results to the scalar path
    /// across many dimensions. Verifies the SIMD implementation is
    /// numerically equivalent to the reference.
    #[test]
    fn avx512_matches_scalar_across_dimensions() {
        // Skip if the `avx512` Cargo feature is off (default) or
        // hardware lacks AVX-512F.
        #[cfg(target_arch = "x86_64")]
        if !cfg!(feature = "avx512") || !is_x86_feature_detected!("avx512f") {
            return;
        }
        for n in [8, 9, 16, 17, 32, 64, 65] {
            // Pseudorandom but deterministic.
            let mut a = Mat::zeros(n, n);
            let mut b = Mat::zeros(n, n);
            for i in 0..n {
                for j in 0..n {
                    a.set(i, j, ((i * 31 + j * 17) % 23) as f64 * 0.1);
                    b.set(i, j, ((i * 11 + j * 41) % 19) as f64 * 0.05);
                }
            }
            let c_scalar = a.mul_scalar(&b);
            let c_avx = a.mul(&b); // dispatches to AVX
            for i in 0..n {
                for j in 0..n {
                    let s = c_scalar.get(i, j);
                    let v = c_avx.get(i, j);
                    let rel = if s.abs() > 1e-9 {
                        (v - s).abs() / s.abs()
                    } else {
                        (v - s).abs()
                    };
                    assert!(
                        rel < 1e-12,
                        "n={} c[{},{}]: scalar={}, avx={}, rel={}",
                        n,
                        i,
                        j,
                        s,
                        v,
                        rel
                    );
                }
            }
        }
    }

    // ---------- DARE convergence ----------

    /// Scalar DARE with a=1, b=1, q=1, r=1.
    ///   P_∞ satisfies: P = P - P²/(1+P) + 1
    ///                = P·r / (r + b²P) + Q  (after rearranging)
    ///                = P / (1 + P) + 1
    /// Multiplying by (1 + P): P + P² = P + 1 + P
    ///                         P² = 1 + P → P² - P - 1 = 0
    ///                         P = (1 + √5)/2 = φ ≈ 1.618 (golden ratio!)
    #[test]
    fn dare_scalar_converges_to_golden_ratio() {
        let a = Mat::from_rows(&[&[1.0]]);
        let b = Mat::from_rows(&[&[1.0]]);
        let q = Mat::from_rows(&[&[1.0]]);
        let r = Mat::from_rows(&[&[1.0]]);
        let p = solve_dare(&a, &b, &q, &r, 500, 1e-12).unwrap();
        let phi = (1.0 + 5.0_f64.sqrt()) / 2.0;
        assert!(
            approx_eq(p.get(0, 0), phi, 1e-9),
            "P should converge to φ ≈ {}; got {}",
            phi,
            p.get(0, 0)
        );
    }

    /// And the gain K = b·P/(r + b²P) = φ/(1+φ) = φ/φ² = 1/φ ≈ 0.618.
    #[test]
    fn lqr_scalar_gain_is_one_over_phi() {
        let lqr = ScalarLqrController::from_scalar(1.0, 1.0, 1.0, 1.0).unwrap();
        let inv_phi = 1.0 / ((1.0 + 5.0_f64.sqrt()) / 2.0);
        assert!(
            approx_eq(lqr.gain, inv_phi, 1e-9),
            "K should be 1/φ ≈ {}; got {}",
            inv_phi,
            lqr.gain
        );
    }

    /// Standard LQR sanity: when state grows beyond setpoint, control
    /// action is negative-feedback (subtracts from state). With scalar
    /// gain K > 0 and error = setpoint - state, u = K·error is
    /// positive when state < setpoint.
    #[test]
    fn scalar_lqr_step_negative_feedback() {
        let mut lqr = ScalarLqrController::from_scalar(1.0, 1.0, 1.0, 1.0).unwrap();
        // error positive (state below setpoint) → positive control
        assert!(lqr.step(5.0, 0.1) > 0.0);
        // error negative (state above setpoint) → negative control
        assert!(lqr.step(-5.0, 0.1) < 0.0);
    }

    /// Closed-loop stability: applying LQR feedback to the scalar
    /// plant x[k+1] = a·x + b·u, with u = -K·x, drives x→0.
    #[test]
    fn lqr_closed_loop_drives_state_to_zero() {
        let a = 1.05_f64; // mildly unstable open-loop
        let b = 1.0;
        let lqr_ctrl = ScalarLqrController::from_scalar(a, b, 1.0, 1.0).unwrap();
        let mut x: f64 = 10.0;
        for _ in 0..200 {
            // u from the controller (treating error = setpoint - x = -x
            // for setpoint 0 regulation).
            // Going via step(): step takes error, returns K·error.
            // For setpoint 0: error = 0 - x = -x; u = K·(-x) = -K·x.
            let mut c = ScalarLqrController {
                gain: lqr_ctrl.gain,
            };
            let u = c.step(-x, 0.01); // u = K·error
            x = a * x + b * u;
        }
        assert!(
            x.abs() < 0.1,
            "closed-loop state should decay to zero; got {}",
            x
        );
    }

    /// Higher r (input cost) → smaller gain (cheaper to let state
    /// drift than to spend control effort). Demonstrates the LQR
    /// tuning knob.
    #[test]
    fn lqr_gain_decreases_with_higher_input_cost() {
        let lqr1 = ScalarLqrController::from_scalar(1.0, 1.0, 1.0, 1.0).unwrap();
        let lqr2 = ScalarLqrController::from_scalar(1.0, 1.0, 1.0, 100.0).unwrap();
        assert!(
            lqr2.gain < lqr1.gain,
            "higher R should yield smaller gain; got {} vs {}",
            lqr2.gain,
            lqr1.gain
        );
    }

    /// 2D system: double-integrator-like, well-posed LQR.
    ///   [x1]     [1 1] [x1]   [0]
    ///   [x2]  =  [0 1] [x2] + [1] u
    ///   Q = I, R = [1]
    /// The DARE converges; the gain has the expected sign pattern
    /// (positive for both state components — both contribute to error).
    #[test]
    fn dare_2x2_double_integrator() {
        let a = Mat::from_rows(&[&[1.0, 1.0], &[0.0, 1.0]]);
        let b = Mat::from_rows(&[&[0.0], &[1.0]]);
        let q = Mat::identity(2);
        let r = Mat::from_rows(&[&[1.0]]);
        let lqr = LqrController::from_system(&a, &b, &q, &r).unwrap();
        assert_eq!(lqr.state_dim, 2);
        assert_eq!(lqr.input_dim, 1);
        // Gain entries should be positive (both states contribute to
        // requiring decelerating control).
        assert!(
            lqr.gain.get(0, 0) > 0.0,
            "gain[0,0] should be positive; got {}",
            lqr.gain.get(0, 0)
        );
        assert!(
            lqr.gain.get(0, 1) > 0.0,
            "gain[0,1] should be positive; got {}",
            lqr.gain.get(0, 1)
        );
    }

    /// Dimension mismatch reported.
    #[test]
    fn dare_dimension_mismatch_returns_error() {
        let a = Mat::from_rows(&[&[1.0, 1.0], &[0.0, 1.0]]); // 2x2
        let b = Mat::from_rows(&[&[1.0]]); // 1x1
        let q = Mat::identity(2);
        let r = Mat::identity(1);
        let result = solve_dare(&a, &b, &q, &r, 100, 1e-9);
        assert!(matches!(result, Err(LqrError::DimensionMismatch { .. })));
    }

    /// LQR reset is a no-op (no integrator state).
    #[test]
    fn scalar_lqr_reset_is_noop() {
        let mut lqr = ScalarLqrController::from_scalar(1.0, 1.0, 1.0, 1.0).unwrap();
        let before = lqr.step(5.0, 0.1);
        lqr.reset();
        let after = lqr.step(5.0, 0.1);
        // Same error → same output: no internal state.
        assert!(approx_eq(before, after, 1e-12));
    }
}
