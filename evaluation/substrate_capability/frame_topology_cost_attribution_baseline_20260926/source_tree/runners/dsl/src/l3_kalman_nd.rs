//! Multi-dimensional Kalman filter — addresses Bench 3 (commit
//! fe93761) which measured the trivial 1D case rather than the
//! ≤64-dim prediction Jabberwock's design actually made.
//!
//! ## State model
//!
//! ```text
//!   x[k+1] = A x[k] + B u[k] + w[k]   where  w ~ N(0, Q)   (process)
//!   y[k]   = C x[k]         + v[k]   where  v ~ N(0, R)   (measurement)
//! ```
//!
//! ## Filter
//!
//! Predict:
//!   x_hat = A x_hat + B u
//!   P     = A P A^T + Q
//!
//! Update (given measurement `y`):
//!   innovation = y - C x_hat
//!   S          = C P C^T + R          (innovation covariance)
//!   K          = P C^T S^-1           (Kalman gain)
//!   x_hat     += K · innovation
//!   P          = (I - K C) · P
//!
//! ## Matrix support
//!
//! Reuses `Mat` from `l3_lqr.rs` (rolled in-crate, no nalgebra dep).
//! For dimensions ≤ 64 this is sufficient; larger dimensions would
//! benefit from BLAS via blis-rs or ndarray.

use crate::l3_lqr::{Bf16PackedB, LqrError, Mat};

/// Multi-dimensional Kalman filter state + parameters.
pub struct KalmanFilterND {
    /// State estimate. Column vector represented as Mat n×1.
    pub x_hat: Mat,
    /// Estimate covariance. n×n.
    pub p: Mat,
    /// State transition. n×n.
    pub a: Mat,
    /// Input gain. n×p (p = control dim; 0 columns means no control).
    pub b: Option<Mat>,
    /// Observation matrix. m×n.
    pub c: Mat,
    /// Process noise covariance. n×n.
    pub q: Mat,
    /// Measurement noise covariance. m×m.
    pub r: Mat,
    /// Cached BF16 pre-pack of C. Built lazily; valid for the
    /// substrate's typical use where C is constant.
    c_packed_bf16: Option<Bf16PackedB>,
    /// Cached BF16 pre-pack of C^T.
    ct_packed_bf16: Option<Bf16PackedB>,
}

/// Outcome of an update step.
#[derive(Debug, Clone)]
pub struct InnovationND {
    /// y - C x_hat (pre-update). m×1.
    pub innovation: Mat,
    /// Kalman gain at this step. n×m.
    pub kalman_gain: Mat,
}

#[derive(Debug, Clone, PartialEq)]
pub enum KalmanError {
    DimensionMismatch { what: String },
    SingularInnovationCovariance,
}

impl From<LqrError> for KalmanError {
    fn from(e: LqrError) -> Self {
        match e {
            LqrError::SingularRplusBPB => KalmanError::SingularInnovationCovariance,
            other => KalmanError::DimensionMismatch {
                what: format!("{:?}", other),
            },
        }
    }
}

impl KalmanFilterND {
    /// State dimension.
    pub fn state_dim(&self) -> usize {
        self.a.rows()
    }
    /// Measurement dimension.
    pub fn measurement_dim(&self) -> usize {
        self.c.rows()
    }

    /// Construct with named matrices. `b` may be `None` for filters
    /// with no control input.
    pub fn new(
        x0: Mat,
        p0: Mat,
        a: Mat,
        b: Option<Mat>,
        c: Mat,
        q: Mat,
        r: Mat,
    ) -> Result<Self, KalmanError> {
        let n = a.rows();
        if a.cols() != n {
            return Err(KalmanError::DimensionMismatch {
                what: "A must be square".to_string(),
            });
        }
        if x0.rows() != n || x0.cols() != 1 {
            return Err(KalmanError::DimensionMismatch {
                what: format!("x0 must be {}x1; got {}x{}", n, x0.rows(), x0.cols()),
            });
        }
        if p0.rows() != n || p0.cols() != n {
            return Err(KalmanError::DimensionMismatch {
                what: format!("P0 must be {}x{}; got {}x{}", n, n, p0.rows(), p0.cols()),
            });
        }
        if let Some(bb) = &b {
            if bb.rows() != n {
                return Err(KalmanError::DimensionMismatch {
                    what: format!("B rows must equal state dim {}; got {}", n, bb.rows()),
                });
            }
        }
        let m = c.rows();
        if c.cols() != n {
            return Err(KalmanError::DimensionMismatch {
                what: format!("C cols must equal state dim {}; got {}", n, c.cols()),
            });
        }
        if q.rows() != n || q.cols() != n {
            return Err(KalmanError::DimensionMismatch {
                what: format!("Q must be {}x{}; got {}x{}", n, n, q.rows(), q.cols()),
            });
        }
        if r.rows() != m || r.cols() != m {
            return Err(KalmanError::DimensionMismatch {
                what: format!("R must be {}x{}; got {}x{}", m, m, r.rows(), r.cols()),
            });
        }
        Ok(Self {
            x_hat: x0,
            p: p0,
            a,
            b,
            c,
            q,
            r,
            c_packed_bf16: None,
            ct_packed_bf16: None,
        })
    }

    /// Build the BF16 caches for the constant observation matrices
    /// C and C^T. Call once after construction if planning to use
    /// `update_bf16_cached`. No-op if dimensions don't qualify
    /// (smaller than 16, or not aligned) — caches stay None and
    /// callers fall back to the uncached path.
    pub fn build_bf16_caches(&mut self) {
        self.c_packed_bf16 = self.c.pack_for_bf16_b();
        self.ct_packed_bf16 = self.c.transpose().pack_for_bf16_b();
    }

    /// Predict step: x_hat ← A x_hat + B u; P ← A P A^T + Q.
    pub fn predict(&mut self, u: Option<&Mat>) -> Result<(), KalmanError> {
        // x_hat = A x_hat + B u
        let mut new_x = self.a.mul(&self.x_hat);
        if let (Some(bb), Some(uu)) = (&self.b, u) {
            if uu.rows() != bb.cols() || uu.cols() != 1 {
                return Err(KalmanError::DimensionMismatch {
                    what: format!("u must be {}x1", bb.cols()),
                });
            }
            let bu = bb.mul(uu);
            new_x = new_x.add(&bu);
        }
        // P = A P A^T + Q
        let ap = self.a.mul(&self.p);
        let at = self.a.transpose();
        let apat = ap.mul(&at);
        self.p = apat.add(&self.q);
        self.x_hat = new_x;
        Ok(())
    }

    /// Update step: incorporate measurement `y`. Returns Innovation.
    pub fn update(&mut self, y: &Mat) -> Result<InnovationND, KalmanError> {
        let m = self.c.rows();
        if y.rows() != m || y.cols() != 1 {
            return Err(KalmanError::DimensionMismatch {
                what: format!("y must be {}x1; got {}x{}", m, y.rows(), y.cols()),
            });
        }
        // innovation = y - C x_hat
        let cx = self.c.mul(&self.x_hat);
        let innovation = y.sub(&cx);
        // S = C P C^T + R
        let cp = self.c.mul(&self.p);
        let ct = self.c.transpose();
        let cpct = cp.mul(&ct);
        let s = cpct.add(&self.r);
        // K = P C^T S^-1
        let s_inv = s
            .inverse()
            .ok_or(KalmanError::SingularInnovationCovariance)?;
        let pct = self.p.mul(&ct);
        let k = pct.mul(&s_inv);
        // x_hat = x_hat + K innovation
        let k_innov = k.mul(&innovation);
        self.x_hat = self.x_hat.add(&k_innov);
        // P = (I - K C) P
        let kc = k.mul(&self.c);
        let i = Mat::identity(self.state_dim());
        let i_minus_kc = i.sub(&kc);
        self.p = i_minus_kc.mul(&self.p);
        Ok(InnovationND {
            innovation,
            kalman_gain: k,
        })
    }

    /// Accessor for state estimate as a scalar (1D case).
    pub fn x_hat_scalar(&self) -> f64 {
        self.x_hat.get(0, 0)
    }

    // ===================================================================
    // BF16-accelerated variants — use Mat::mul_bf16 for the heavy
    // covariance updates. Matrix inverse stays FP64 for precision.
    //
    // For dimensions ≥ 16 with K%2==0 and N%16==0 these use AVX-512
    // BF16 dot product (VDPBF16PS), 2× FP64 throughput. For smaller
    // dimensions mul_bf16 falls back to mul (FP64), so calling the
    // _bf16 variants is always safe.
    // ===================================================================

    /// Predict step using BF16 matmul for the heavy A·P·A^T update.
    /// The small A·x_hat and B·u products use the normal FP64 mul.
    #[cfg(target_arch = "x86_64")]
    pub fn predict_bf16(&mut self, u: Option<&Mat>) -> Result<(), KalmanError> {
        // x_hat = A x_hat + B u  (small matmuls; FP64).
        let mut new_x = self.a.mul(&self.x_hat);
        if let (Some(bb), Some(uu)) = (&self.b, u) {
            if uu.rows() != bb.cols() || uu.cols() != 1 {
                return Err(KalmanError::DimensionMismatch {
                    what: format!("u must be {}x1", bb.cols()),
                });
            }
            let bu = bb.mul(uu);
            new_x = new_x.add(&bu);
        }
        // P = A P A^T + Q  (heavy n×n matmuls; BF16).
        let ap = self.a.mul_bf16(&self.p);
        let at = self.a.transpose();
        let apat = ap.mul_bf16(&at);
        self.p = apat.add(&self.q);
        self.x_hat = new_x;
        Ok(())
    }

    /// Update step using cached BF16 pre-packs of C, C^T + one-shot
    /// pre-pack of P. Closes the BF16 conversion overhead identified
    /// in commit 02b38ae — amortises 5 of 6 heavy matmul conversion
    /// costs across one update.
    ///
    /// Requires `build_bf16_caches` to have been called previously.
    /// If caches aren't built or P doesn't qualify for packing,
    /// falls back to `update_bf16` (which itself falls back to
    /// scalar at small dimensions).
    #[cfg(target_arch = "x86_64")]
    pub fn update_bf16_cached(&mut self, y: &Mat) -> Result<InnovationND, KalmanError> {
        // Require the C caches to exist; if not, fall back to the
        // un-cached BF16 path.
        let (c_pkd, ct_pkd) = match (&self.c_packed_bf16, &self.ct_packed_bf16) {
            (Some(a), Some(b)) => (a.clone(), b.clone()),
            _ => return self.update_bf16(y),
        };
        // Pre-pack P once for this update — used 2× below.
        let p_pkd = match self.p.pack_for_bf16_b() {
            Some(p) => p,
            None => return self.update_bf16(y),
        };
        let m = self.c.rows();
        if y.rows() != m || y.cols() != 1 {
            return Err(KalmanError::DimensionMismatch {
                what: format!("y must be {}x1; got {}x{}", m, y.rows(), y.cols()),
            });
        }
        // innovation = y - C x_hat
        let cx = self.c.mul(&self.x_hat);
        let innovation = y.sub(&cx);
        // S = C P C^T + R
        let cp = self.c.mul_bf16_pre_b(&p_pkd); // C·P (P cached)
        let cpct = cp.mul_bf16_pre_b(&ct_pkd); // CP·C^T (C^T cached)
        let s = cpct.add(&self.r);
        let s_inv = s
            .inverse()
            .ok_or(KalmanError::SingularInnovationCovariance)?;
        // K = P C^T S^-1
        let pct = self.p.mul_bf16_pre_b(&ct_pkd); // P·C^T (C^T cached)
                                                  // S^-1 changes per update; pack it once here for the next mul.
        let s_inv_pkd = s_inv.pack_for_bf16_b();
        let k = match &s_inv_pkd {
            Some(pkd) => pct.mul_bf16_pre_b(pkd),
            None => pct.mul_bf16(&s_inv),
        };
        // x_hat += K · innovation  (small)
        let k_innov = k.mul(&innovation);
        self.x_hat = self.x_hat.add(&k_innov);
        // P = (I - K C) P  — K·C uses C cache, then ·P uses P cache.
        let kc = k.mul_bf16_pre_b(&c_pkd); // K·C (C cached)
        let i = Mat::identity(self.state_dim());
        let i_minus_kc = i.sub(&kc);
        self.p = i_minus_kc.mul_bf16_pre_b(&p_pkd); // (I-KC)·P (P cached)
        Ok(InnovationND {
            innovation,
            kalman_gain: k,
        })
    }

    /// Update step using BF16 matmul for the heavy covariance + gain
    /// computations. Innovation, matrix inverse, and small vector
    /// products stay FP64 for precision.
    #[cfg(target_arch = "x86_64")]
    pub fn update_bf16(&mut self, y: &Mat) -> Result<InnovationND, KalmanError> {
        let m = self.c.rows();
        if y.rows() != m || y.cols() != 1 {
            return Err(KalmanError::DimensionMismatch {
                what: format!("y must be {}x1; got {}x{}", m, y.rows(), y.cols()),
            });
        }
        // innovation = y - C x_hat  (small; FP64)
        let cx = self.c.mul(&self.x_hat);
        let innovation = y.sub(&cx);
        // S = C P C^T + R  (heavy; BF16 for the two matmuls)
        let cp = self.c.mul_bf16(&self.p);
        let ct = self.c.transpose();
        let cpct = cp.mul_bf16(&ct);
        let s = cpct.add(&self.r);
        // K = P C^T S^-1  (S^-1 stays FP64 — precision-critical;
        //                   the matmuls go through BF16).
        let s_inv = s
            .inverse()
            .ok_or(KalmanError::SingularInnovationCovariance)?;
        let pct = self.p.mul_bf16(&ct);
        let k = pct.mul_bf16(&s_inv);
        // x_hat = x_hat + K innovation  (small)
        let k_innov = k.mul(&innovation);
        self.x_hat = self.x_hat.add(&k_innov);
        // P = (I - K C) P  (heavy; BF16)
        let kc = k.mul_bf16(&self.c);
        let i = Mat::identity(self.state_dim());
        let i_minus_kc = i.sub(&kc);
        self.p = i_minus_kc.mul_bf16(&self.p);
        Ok(InnovationND {
            innovation,
            kalman_gain: k,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// 1D KF matches `KalmanFilter1D` behaviour: converges to the
    /// mean of a constant-mean process.
    #[test]
    fn one_dim_converges_to_constant_mean() {
        let x0 = Mat::from_rows(&[&[0.0]]);
        let p0 = Mat::from_rows(&[&[100.0]]);
        let a = Mat::from_rows(&[&[1.0]]);
        let c = Mat::from_rows(&[&[1.0]]);
        let q = Mat::from_rows(&[&[0.0]]);
        let r = Mat::from_rows(&[&[1.0]]);
        let mut kf = KalmanFilterND::new(x0, p0, a, None, c, q, r).unwrap();
        for i in 0..200 {
            let m = if i % 2 == 0 { 7.5 } else { 6.5 };
            kf.predict(None).unwrap();
            kf.update(&Mat::from_rows(&[&[m]])).unwrap();
        }
        assert!(
            (kf.x_hat_scalar() - 7.0).abs() < 0.1,
            "1D KF should converge near 7.0; got {}",
            kf.x_hat_scalar()
        );
    }

    /// 2D constant-position tracking: state = (x, y), measurement
    /// observes both. KF estimate converges to the true mean.
    #[test]
    fn two_dim_constant_position_converges() {
        let x0 = Mat::from_rows(&[&[0.0], &[0.0]]);
        let p0 = Mat::from_rows(&[&[100.0, 0.0], &[0.0, 100.0]]);
        let a = Mat::identity(2);
        let c = Mat::identity(2);
        let q = Mat::from_rows(&[&[0.01, 0.0], &[0.0, 0.01]]);
        let r = Mat::from_rows(&[&[1.0, 0.0], &[0.0, 1.0]]);
        let mut kf = KalmanFilterND::new(x0, p0, a, None, c, q, r).unwrap();

        // True state (5, 3); measurements perturbed by ±0.5 alternating.
        for i in 0..200 {
            let s = if i % 2 == 0 { 0.5 } else { -0.5 };
            let m = Mat::from_rows(&[&[5.0 + s], &[3.0 - s]]);
            kf.predict(None).unwrap();
            kf.update(&m).unwrap();
        }
        assert!(
            (kf.x_hat.get(0, 0) - 5.0).abs() < 0.2,
            "x_hat[0] should approach 5.0; got {}",
            kf.x_hat.get(0, 0)
        );
        assert!(
            (kf.x_hat.get(1, 0) - 3.0).abs() < 0.2,
            "x_hat[1] should approach 3.0; got {}",
            kf.x_hat.get(1, 0)
        );
    }

    /// 4D constant-velocity tracking: state = (x, y, vx, vy);
    /// measurement observes (x, y). KF tracks position + estimates
    /// velocity from the position derivatives.
    #[test]
    fn four_dim_constant_velocity_estimates_velocity() {
        let dt = 1.0_f64;
        let x0 = Mat::from_rows(&[&[0.0], &[0.0], &[0.0], &[0.0]]);
        let p0 = {
            let mut p = Mat::identity(4);
            for i in 0..4 {
                p.set(i, i, 100.0);
            }
            p
        };
        // A = [[1, 0, dt, 0],
        //      [0, 1, 0, dt],
        //      [0, 0, 1,  0],
        //      [0, 0, 0,  1]]
        let a = Mat::from_rows(&[
            &[1.0, 0.0, dt, 0.0],
            &[0.0, 1.0, 0.0, dt],
            &[0.0, 0.0, 1.0, 0.0],
            &[0.0, 0.0, 0.0, 1.0],
        ]);
        let c = Mat::from_rows(&[&[1.0, 0.0, 0.0, 0.0], &[0.0, 1.0, 0.0, 0.0]]);
        let q = {
            let mut q = Mat::zeros(4, 4);
            for i in 0..4 {
                q.set(i, i, 0.01);
            }
            q
        };
        let r = Mat::from_rows(&[&[0.5, 0.0], &[0.0, 0.5]]);
        let mut kf = KalmanFilterND::new(x0, p0, a, None, c, q, r).unwrap();
        // True velocity: (2, 1). Position at t=k is (2k, k).
        for k in 1..100_i64 {
            let pos_x = 2.0 * k as f64;
            let pos_y = 1.0 * k as f64;
            let m = Mat::from_rows(&[&[pos_x], &[pos_y]]);
            kf.predict(None).unwrap();
            kf.update(&m).unwrap();
        }
        // After 100 steps, velocity estimate should be near (2, 1).
        let vx_est = kf.x_hat.get(2, 0);
        let vy_est = kf.x_hat.get(3, 0);
        assert!(
            (vx_est - 2.0).abs() < 0.1,
            "vx_est should be near 2.0; got {}",
            vx_est
        );
        assert!(
            (vy_est - 1.0).abs() < 0.1,
            "vy_est should be near 1.0; got {}",
            vy_est
        );
    }

    /// Dimension mismatch produces an error rather than panic.
    #[test]
    fn dimension_mismatch_returns_error() {
        let x0 = Mat::from_rows(&[&[0.0], &[0.0]]); // 2x1
        let p0 = Mat::identity(2);
        let a = Mat::identity(2);
        let c = Mat::from_rows(&[&[1.0]]); // 1x1 — wrong cols
        let q = Mat::identity(2);
        let r = Mat::from_rows(&[&[1.0]]);
        let result = KalmanFilterND::new(x0, p0, a, None, c, q, r);
        assert!(matches!(result, Err(KalmanError::DimensionMismatch { .. })));
    }
}
