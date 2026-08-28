//! L3 MPC — Model Predictive Control with box-constrained QP solver.
//!
//! Realises the `mpc_constrained_lookahead` component of the
//! `drives_estimation_control` Mt (commit 1b9a7e0). Completes L3's
//! runtime-component coverage at 10/12 (the remaining two —
//! variety_matching at L6 and Lyapunov as design-time — aren't
//! runtime components).
//!
//! ## What MPC adds over LQR
//!
//! - **Constraint handling.** LQR's optimal solution can exceed
//!   actuator bounds; MPC respects `[u_min, u_max]` exactly.
//! - **Finite horizon.** MPC plans N steps ahead, applies the first,
//!   replans next tick (receding horizon). Lets the controller react
//!   to time-varying setpoints + handle imminent constraints.
//! - **Per-tick cost.** Each tick solves a QP (O(N²) work for
//!   projected gradient). LQR is O(1) per tick after the offline
//!   DARE solve.
//!
//! ## Problem formulation
//!
//! For scalar dynamics in error coordinates: `y_{k+1} = a·y_k + b·u_k`
//! (where `y = setpoint - state`, so MPC drives y to 0):
//!
//! ```text
//!   minimise  J = Σ_{k=1..N-1} q·y_k²  +  Σ_{k=0..N-1} r·u_k²  +  p_f·y_N²
//!   subject to  u_min ≤ u_k ≤ u_max
//! ```
//!
//! This is a strictly convex QP in `u = (u_0, …, u_{N-1})` when
//! `r > 0`. The Hessian is implicit; gradient via Pontryagin
//! adjoints (O(N) per evaluation).
//!
//! ## QP solver: projected gradient with backtracking line search
//!
//! Variants considered:
//! - **Active-set** — fast for few active constraints; complex to
//!   maintain working sets.
//! - **Interior-point** — robust; needs barrier setup + Newton steps.
//! - **ADMM (OSQP)** — battle-tested; substantial implementation
//!   work for v1.
//! - **Projected gradient** — simplest; convergence-guaranteed for
//!   convex QP with box constraints; O(N²) per QP for the substrate's
//!   typical horizons (≤ 50). Picked for v1.
//!
//! Step size selected adaptively: increase on cost decrease, halve on
//! cost increase. Terminates when ‖projected gradient‖ < tolerance
//! or step size drops below numerical floor.
//!
//! ## Mt rule: mpc_must_have_fallback_when_infeasible
//!
//! Box constraints (the only constraint type here) are always
//! feasible for unconstrained `u_min < u_max`. If the QP solver
//! fails to converge, `solve` returns an `Err`; the `Controller`
//! impl returns 0.0 as the fallback action (substrate continues
//! operating, no control signal applied — same as PID's "do nothing
//! on unknown error" mode). Honours the Mt rule.

use crate::l3_drives::Controller;

#[derive(Debug, Clone, PartialEq)]
pub enum MpcError {
    /// QP solver hit max_iter without reaching tolerance.
    QpDidNotConverge { iterations: usize, grad_norm: f64 },
    /// Box constraints are inverted (u_max < u_min). Caller error.
    InvertedBounds,
    /// Invalid parameter (e.g. non-positive r making QP ill-posed).
    InvalidParameter { what: String },
}

#[derive(Debug, Clone)]
pub struct MpcSolution {
    /// Planned control trajectory u_0, u_1, …, u_{N-1}.
    pub trajectory: Vec<f64>,
    /// Iterations the QP solver took to converge.
    pub iterations: usize,
    /// Final gradient norm (diagnostic).
    pub final_grad_norm: f64,
}

impl MpcSolution {
    /// First action — what to apply this tick (receding horizon).
    pub fn first_action(&self) -> f64 {
        *self.trajectory.first().unwrap_or(&0.0)
    }
}

/// Build the explicit Hessian H (N×N) and linear term g (N) for the
/// scalar MPC problem in error coordinates:
///
///   J(u) = (G u + F y_0)^T D (G u + F y_0) + u^T R u
///        = u^T (G^T D G + R) u + 2 y_0 F^T D G u + const
///
/// So H = 2(G^T D G + R)  and  g = 2 y_0 G^T D F  (vectors).
///
/// G is the N×N lower-triangular dynamics matrix:
///   G[k][i] = a^{k-i-1} · b   for i ≤ k-1 (1-indexed k, 0-indexed i)
/// F = (a, a², …, a^N)^T
/// D = diag(q, q, …, q, p_f)  (running cost on y_1..y_{N-1}, terminal on y_N)
fn build_hessian_and_linear(
    y_0: f64,
    a: f64,
    b: f64,
    q: f64,
    r: f64,
    p_f: f64,
    horizon: usize,
) -> (Vec<Vec<f64>>, Vec<f64>) {
    let n = horizon;
    // G: row k (1-indexed → row index k-1) and col i (0-indexed).
    // G[k-1][i] = a^{k-i-1} * b for i in 0..k.
    let mut g_mat = vec![vec![0.0_f64; n]; n];
    for k in 1..=n {
        for i in 0..k {
            g_mat[k - 1][i] = a.powi((k as i32) - (i as i32) - 1) * b;
        }
    }
    // F[k-1] = a^k for k=1..N.
    let f_vec: Vec<f64> = (1..=n).map(|k| a.powi(k as i32)).collect();
    // D[k-1] = q for k=1..N-1; p_f for k=N.
    let d_vec: Vec<f64> = (1..=n).map(|k| if k == n { p_f } else { q }).collect();
    // H[i][j] = 2 * (r·δ_ij + Σ_k g[k][i] · d[k] · g[k][j])
    let mut h = vec![vec![0.0_f64; n]; n];
    for i in 0..n {
        for j in 0..n {
            let mut s = if i == j { r } else { 0.0 };
            for k in 0..n {
                s += g_mat[k][i] * d_vec[k] * g_mat[k][j];
            }
            h[i][j] = 2.0 * s;
        }
    }
    // For the Controller-trait convention (u positive when error
    // positive — matches PID + LQR), MPC's internal dynamics treat
    // positive u as "removes error": y_{k+1} = a y_k - b u_k. This
    // negates G (which negates G^T D F → flips linear's sign).
    // H = 2(G^T D G + R) is unchanged since G appears quadratically.
    //
    // linear[i] = -2 y_0 · Σ_k g[k][i] · d[k] · f[k]
    let mut linear = vec![0.0_f64; n];
    for i in 0..n {
        let mut s = 0.0;
        for k in 0..n {
            s += g_mat[k][i] * d_vec[k] * f_vec[k];
        }
        linear[i] = -2.0 * y_0 * s;
    }
    (h, linear)
}

/// Estimate the largest eigenvalue of H via power iteration. Used
/// to set a Lipschitz-safe step size α = 1/L for projected gradient.
/// 30 iterations is typically more than enough for the small
/// (horizon ≤ ~50) Hessians substrate's MPC produces.
fn estimate_max_eigenvalue(h: &[Vec<f64>], iters: usize) -> f64 {
    let n = h.len();
    if n == 0 {
        return 1.0;
    }
    let mut v = vec![1.0_f64 / (n as f64).sqrt(); n];
    let mut lambda = 0.0_f64;
    for _ in 0..iters {
        let hv = matvec(h, &v);
        let norm: f64 = hv.iter().map(|x| x * x).sum::<f64>().sqrt();
        if norm < 1e-15 {
            return 1.0;
        }
        for i in 0..n {
            v[i] = hv[i] / norm;
        }
        let hv2 = matvec(h, &v);
        lambda = v.iter().zip(hv2.iter()).map(|(a, b)| a * b).sum();
    }
    lambda
}

#[inline]
fn matvec(h: &[Vec<f64>], v: &[f64]) -> Vec<f64> {
    let n = v.len();
    let mut out = vec![0.0_f64; n];
    for i in 0..n {
        let mut s = 0.0;
        for j in 0..n {
            s += h[i][j] * v[j];
        }
        out[i] = s;
    }
    out
}

/// Solve the box-constrained QP via projected gradient with
/// exact step size: α = ‖g_p‖² / (g_p^T H g_p). For an unconstrained
/// quadratic this is the steepest-descent optimum; under projection
/// it's bounded by it. Strongly convex H guarantees convergence;
/// the explicit Hessian + exact step gives much faster convergence
/// than naive adaptive alpha for ill-conditioned QPs (long horizons,
/// unstable plants).
fn solve_qp(
    y_0: f64,
    a: f64,
    b: f64,
    q: f64,
    r: f64,
    p_f: f64,
    horizon: usize,
    u_min: f64,
    u_max: f64,
    max_iter: usize,
    tolerance: f64,
) -> Result<MpcSolution, MpcError> {
    if u_max < u_min {
        return Err(MpcError::InvertedBounds);
    }
    if r <= 0.0 {
        return Err(MpcError::InvalidParameter {
            what: "r must be > 0 for strict convexity".to_string(),
        });
    }
    let n = horizon;
    let (h_mat, lin) = build_hessian_and_linear(y_0, a, b, q, r, p_f, n);

    let mut u = vec![0.0_f64; n];
    for ui in &mut u {
        *ui = ui.clamp(u_min, u_max);
    }

    // Helper: compute cost J(u) = (1/2) u^T H u + lin^T u.
    let cost_of = |u: &[f64]| -> f64 {
        let hu = matvec(&h_mat, u);
        let mut c = 0.0_f64;
        for i in 0..n {
            c += 0.5 * u[i] * hu[i] + lin[i] * u[i];
        }
        c
    };

    // Initial step from Lipschitz estimate; halve on cost increase,
    // grow on success. Power iteration may underestimate L, so
    // backtracking guards against α being too aggressive.
    let l_est = estimate_max_eigenvalue(&h_mat, 50);
    let mut alpha = if l_est > 0.0 { 1.0 / l_est } else { 1.0 };
    let mut cost = cost_of(&u);
    let mut last_norm = f64::INFINITY;

    for iter in 0..max_iter {
        // ∇J(u) = H u + lin
        let hu = matvec(&h_mat, &u);
        let mut grad = vec![0.0_f64; n];
        for i in 0..n {
            grad[i] = hu[i] + lin[i];
        }
        // Projected gradient (natural residual).
        let mut proj_g = vec![0.0_f64; n];
        for i in 0..n {
            let at_lo = u[i] <= u_min + 1e-15;
            let at_hi = u[i] >= u_max - 1e-15;
            let g = grad[i];
            if (at_lo && g > 0.0) || (at_hi && g < 0.0) {
                proj_g[i] = 0.0;
            } else {
                proj_g[i] = g;
            }
        }
        let pg_norm: f64 = proj_g.iter().map(|x| x * x).sum::<f64>().sqrt();
        last_norm = pg_norm;
        if pg_norm < tolerance {
            return Ok(MpcSolution {
                trajectory: u,
                iterations: iter,
                final_grad_norm: pg_norm,
            });
        }
        // Backtracking line search: shrink α until cost decreases.
        // Bounded by a numerical floor to avoid infinite loop on a
        // local minimum.
        let mut backtracks = 0;
        loop {
            let u_trial: Vec<f64> = u
                .iter()
                .zip(grad.iter())
                .map(|(uk, gk)| (uk - alpha * gk).clamp(u_min, u_max))
                .collect();
            let c_trial = cost_of(&u_trial);
            if c_trial < cost - 1e-18 {
                u = u_trial;
                cost = c_trial;
                // Grow α slightly on success (try larger next time).
                alpha *= 1.3;
                break;
            }
            backtracks += 1;
            alpha *= 0.5;
            if alpha < 1e-20 || backtracks > 60 {
                // Numerical floor reached — accept current u.
                return Ok(MpcSolution {
                    trajectory: u,
                    iterations: iter,
                    final_grad_norm: pg_norm,
                });
            }
        }
    }
    Err(MpcError::QpDidNotConverge {
        iterations: max_iter,
        grad_norm: last_norm,
    })
}

/// Scalar MPC controller. Drives error to zero subject to box
/// constraints on the control input. Realises the
/// `mpc_constrained_lookahead` component of the L3 Mt.
pub struct ScalarMpcController {
    pub a: f64,
    pub b: f64,
    pub q: f64,
    pub r: f64,
    pub p_f: f64,
    pub horizon: usize,
    pub u_min: f64,
    pub u_max: f64,
    pub max_iter: usize,
    pub tolerance: f64,
    /// Last QP solve result; useful for monitoring + tests.
    pub last_iterations: usize,
}

impl ScalarMpcController {
    /// Construct with sensible defaults: max_iter 200, tolerance 1e-6.
    pub fn new(
        a: f64,
        b: f64,
        q: f64,
        r: f64,
        p_f: f64,
        horizon: usize,
        u_min: f64,
        u_max: f64,
    ) -> Self {
        Self {
            a,
            b,
            q,
            r,
            p_f,
            horizon,
            u_min,
            u_max,
            max_iter: 200,
            tolerance: 1e-6,
            last_iterations: 0,
        }
    }

    /// Solve the MPC QP for the current error. Returns the full
    /// trajectory; caller applies `trajectory[0]` this tick.
    pub fn solve(&mut self, error: f64) -> Result<MpcSolution, MpcError> {
        let sol = solve_qp(
            error,
            self.a,
            self.b,
            self.q,
            self.r,
            self.p_f,
            self.horizon,
            self.u_min,
            self.u_max,
            self.max_iter,
            self.tolerance,
        )?;
        self.last_iterations = sol.iterations;
        Ok(sol)
    }
}

impl Controller for ScalarMpcController {
    /// Solve the QP + return the first action. Falls back to 0.0
    /// on QP failure (honouring the Mt rule
    /// `mpc_must_have_fallback_when_infeasible`).
    fn step(&mut self, error: f64, _dt: f64) -> f64 {
        match self.solve(error) {
            Ok(sol) => sol.first_action(),
            Err(_) => 0.0,
        }
    }
    /// MPC has no integrator state; reset is a no-op.
    fn reset(&mut self) {}
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::l3_lqr::ScalarLqrController;

    fn approx(a: f64, b: f64, tol: f64) -> bool {
        (a - b).abs() < tol
    }

    // ---------- QP convergence ----------

    /// Single-step QP (horizon = 1) with no active bounds: the
    /// closed form is u_0 = b·p_f·a·y_0 / (r + b²·p_f). Verifies
    /// the QP solver hits the analytic minimum.
    ///
    /// With internal convention y_{k+1} = a y_k - b u_k:
    ///   J(u_0) = r u_0² + p_f (a y_0 - b u_0)²
    ///   dJ/du_0 = 2 r u_0 + 2 p_f (a y_0 - b u_0) · (-b) = 0
    ///   → u_0 (r + b² p_f) = b p_f a y_0
    ///   → u_0 = b p_f a y_0 / (r + b² p_f)
    #[test]
    fn qp_single_step_matches_analytic() {
        let y_0 = 10.0_f64;
        let (a, b) = (1.0_f64, 1.0_f64);
        let (q, r, p_f) = (1.0_f64, 1.0_f64, 5.0_f64);
        let _q = q; // unused in horizon=1 (no running state cost)
        let horizon = 1;
        let sol = solve_qp(y_0, a, b, q, r, p_f, horizon, -1e6, 1e6, 500, 1e-6).unwrap();
        let expected = b * p_f * a * y_0 / (r + b * b * p_f);
        assert!(
            approx(sol.trajectory[0], expected, 1e-4),
            "QP single step expected {}, got {}",
            expected,
            sol.trajectory[0]
        );
    }

    /// Multi-step QP with no constraints converges and drives error
    /// toward zero. Trajectory applied via the internal model
    /// y_{k+1} = a y_k - b u_k.
    #[test]
    fn qp_multi_step_drives_error_down() {
        let y_0 = 10.0_f64;
        let (a, b) = (1.0_f64, 1.0_f64);
        let sol = solve_qp(y_0, a, b, 1.0, 1.0, 10.0, 20, -100.0, 100.0, 3000, 1e-3).unwrap();
        // Apply trajectory open-loop with the internal sign convention.
        let mut y = y_0;
        for u in &sol.trajectory {
            y = a * y - b * u;
        }
        assert!(
            y.abs() < 1.0,
            "open-loop trajectory should drive y near 0; got {}",
            y
        );
    }

    // ---------- Constraint handling ----------

    /// MPC respects upper bound when unconstrained action would
    /// exceed it. With positive y_0 (positive error), MPC drives y
    /// down via positive u (internal y' = a y - b u). Unconstrained
    /// u is huge; with u_max=1 it saturates at +1.
    #[test]
    fn mpc_respects_u_max() {
        let mut mpc = ScalarMpcController::new(1.0, 1.0, 1.0, 0.001, 100.0, 5, -1.0, 1.0);
        let sol = mpc.solve(1000.0).unwrap();
        for (i, u) in sol.trajectory.iter().enumerate() {
            assert!(
                *u >= -1.0 - 1e-9 && *u <= 1.0 + 1e-9,
                "u[{}] = {} violates bounds [-1, 1]",
                i,
                u
            );
        }
        // First action saturates positively (drive positive error down).
        assert!(
            approx(sol.first_action(), 1.0, 1e-3),
            "first action should saturate near +1.0; got {}",
            sol.first_action()
        );
    }

    /// MPC respects lower bound symmetrically. Negative y_0 →
    /// negative u (saturating at u_min = -1).
    #[test]
    fn mpc_respects_u_min() {
        let mut mpc = ScalarMpcController::new(1.0, 1.0, 1.0, 0.001, 100.0, 5, -1.0, 1.0);
        let sol = mpc.solve(-1000.0).unwrap();
        assert!(
            approx(sol.first_action(), -1.0, 1e-3),
            "first action should saturate at -1.0; got {}",
            sol.first_action()
        );
    }

    /// Inverted bounds → InvertedBounds error.
    #[test]
    fn mpc_inverted_bounds_returns_error() {
        let r = solve_qp(
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 5, 1.0, -1.0, // inverted!
            100, 1e-9,
        );
        assert!(matches!(r, Err(MpcError::InvertedBounds)));
    }

    /// r = 0 → InvalidParameter (QP not strictly convex).
    #[test]
    fn mpc_zero_input_cost_rejected() {
        let r = solve_qp(1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 5, -1.0, 1.0, 100, 1e-9);
        assert!(matches!(r, Err(MpcError::InvalidParameter { .. })));
    }

    // ---------- Controller trait ----------

    /// Positive error → positive u; negative error → negative u.
    /// Matches the Controller-trait convention shared with PID + LQR
    /// (u positive when state below setpoint to push state up).
    #[test]
    fn mpc_step_sign_convention() {
        let mut mpc = ScalarMpcController::new(1.0, 1.0, 1.0, 1.0, 5.0, 5, -10.0, 10.0);
        let u_pos_err = mpc.step(5.0, 0.1);
        let u_neg_err = mpc.step(-5.0, 0.1);
        assert!(
            u_pos_err > 0.0,
            "positive error should yield positive u; got {}",
            u_pos_err
        );
        assert!(
            u_neg_err < 0.0,
            "negative error should yield negative u; got {}",
            u_neg_err
        );
        assert!(
            approx(u_pos_err, -u_neg_err, 1e-3),
            "sign-symmetric expected; got pos={}, neg={}",
            u_pos_err,
            u_neg_err
        );
    }

    /// Fallback on QP failure: Controller returns 0.0.
    #[test]
    fn mpc_fallback_on_invalid_bounds() {
        let mut mpc = ScalarMpcController::new(
            1.0, 1.0, 1.0, 1.0, 1.0, 5, 1.0, -1.0, // inverted → solver errors
        );
        // step() returns 0.0 fallback rather than panicking.
        let u = mpc.step(5.0, 0.1);
        assert_eq!(u, 0.0);
    }

    /// Reset is a no-op (MPC has no integrator state).
    #[test]
    fn mpc_reset_noop() {
        let mut mpc = ScalarMpcController::new(1.0, 1.0, 1.0, 1.0, 1.0, 5, -10.0, 10.0);
        let before = mpc.step(5.0, 0.1);
        mpc.reset();
        let after = mpc.step(5.0, 0.1);
        assert!(approx(before, after, 1e-6));
    }

    // ---------- Closed-loop stability ----------

    /// Closed-loop MPC stabilises a mildly unstable plant. Plant
    /// dynamics: x_{k+1} = a x_k + b u_k (a > 1 open-loop unstable).
    /// Each tick: error = setpoint - x, MPC returns u that drives
    /// state toward setpoint (positive when error > 0).
    #[test]
    fn mpc_closed_loop_stabilises_mild_instability() {
        let a = 1.05_f64; // open-loop unstable
        let b = 1.0_f64;
        let mut mpc = ScalarMpcController::new(a, b, 1.0, 1.0, 10.0, 10, -5.0, 5.0);
        // Looser tolerance acceptable for closed-loop work — the
        // receding-horizon re-solve recovers from any per-tick
        // sub-optimality.
        mpc.tolerance = 1e-3;
        mpc.max_iter = 500;
        let setpoint = 0.0_f64;
        let mut x: f64 = 10.0;
        for _ in 0..200 {
            let error = setpoint - x; // = -x; negative initially
            let u = mpc.step(error, 0.01);
            x = a * x + b * u;
        }
        assert!(
            x.abs() < 1.0,
            "MPC closed loop should stabilise plant; final x = {}",
            x
        );
    }

    // ---------- MPC vs LQR cross-validation ----------

    /// For unconstrained MPC with a long horizon, the first action
    /// should approximate LQR's gain·error. Cross-validates two
    /// independent implementations: LQR via DARE iteration, MPC via
    /// QP. Both should produce u with the same sign + magnitude
    /// converging to the LQR limit as horizon → ∞.
    ///
    /// Allow ≤ 20% relative error because finite-horizon MPC isn't
    /// exactly the infinite-horizon LQR even with terminal cost,
    /// and the projected-gradient QP has finite tolerance.
    #[test]
    fn mpc_long_horizon_matches_lqr_unconstrained() {
        let (a, b) = (1.0_f64, 1.0_f64);
        let (q, r) = (1.0_f64, 1.0_f64);
        let error = 5.0_f64;
        let lqr = ScalarLqrController::from_scalar(a, b, q, r).unwrap();
        let lqr_action = lqr.gain * error;
        let mut mpc = ScalarMpcController::new(a, b, q, r, 10.0, 30, -1e6, 1e6);
        mpc.tolerance = 1e-4;
        mpc.max_iter = 3000;
        let mpc_action = mpc.solve(error).unwrap().first_action();
        // Same sign required.
        assert!(
            mpc_action * lqr_action > 0.0,
            "MPC + LQR should have matching sign; MPC={}, LQR={}",
            mpc_action,
            lqr_action
        );
        let rel_err = (mpc_action - lqr_action).abs() / lqr_action.abs();
        assert!(
            rel_err < 0.2,
            "MPC long-horizon should approximate LQR within 20%; \
                 MPC={}, LQR={}, rel_err={}",
            mpc_action,
            lqr_action,
            rel_err
        );
    }
}
