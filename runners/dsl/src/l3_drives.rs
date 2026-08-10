//! L3 drives — actual controllers realising the
//! `drives_estimation_control` pattern Mt (commit 1b9a7e0).
//!
//! Implements the subset of components that are concrete code rather
//! than design-forward.
//!
//! ## Realised
//!
//! - **`drive_with_setpoint`** — `Drive` struct binds (setpoint,
//!   estimator, controller, weight) per the Mt's "3-tuple" rule.
//! - **`error_signal_drive_minus_state`** — `Drive::observe` returns
//!   `setpoint - estimator.x_hat`.
//! - **`pid_drive_corrector`** — `PidController` with Kp/Ki/Kd + dt.
//! - **`anti_windup_integral`** — `PidController` clamps integral to
//!   `[integral_min, integral_max]` after each accumulation
//!   (conditional integration / back-calculation hybrid).
//! - **`kalman_state_estimator`** — `KalmanFilter1D` with predict +
//!   update steps over scalar state.
//! - **`innovation_driven_belief_update`** — update returns
//!   `Innovation { raw, gain, post_x_hat }` so callers can monitor.
//! - **`multi_drive_composition_weighted`** — `MultiDriveSystem`
//!   aggregates drive control signals weighted by `Drive::weight`.
//!
//! ## Deferred (per Mt, future commits)
//!
//! - `lqr_optimal_when_linear_quadratic` — needs Algebraic Riccati
//!   Equation solver. Future.
//! - `mpc_constrained_lookahead` — needs QP solver + finite-horizon
//!   optimisation. Future.
//! - `gain_scheduling_per_context` — needs L2 dispatcher's hot
//!   counters fed in as context.
//! - `variety_matching_principle` — system-scale check; lives at L6.
//! - `lyapunov_stability_check` — design-time tool; not runtime.
//!
//! ## Invariants verified by tests
//!
//! - **`drives_converge_to_setpoint`** — PID applied to a simple
//!   first-order integrator plant drives error → 0.
//! - **`integral_bounded_by_anti_windup`** — under saturating error,
//!   integral never exceeds `integral_max`.
//! - **`estimator_unbiased`** — over a deterministic constant-mean
//!   measurement sequence, Kalman estimate converges to the mean.

/// Trait for controller types. Method JIT-friendly — `step` is the
/// hot path; `reset` is occasional.
pub trait Controller: Send {
    /// Compute control signal `u(t)` from current error + tick step.
    /// Mutates internal controller state (integral accumulator,
    /// previous error for derivative term).
    fn step(&mut self, error: f64, dt: f64) -> f64;
    /// Reset internal state — call on guard-failure cooling, on
    /// recompile, on Γ change that invalidates the controller's
    /// assumed plant model.
    fn reset(&mut self);
}

/// PID controller with anti-windup. The canonical L3 corrector.
///
/// `u(t) = Kp·e + Ki·∫e dt + Kd·de/dt`
///
/// `integral` is clamped to `[integral_min, integral_max]` after each
/// accumulation, realising the `anti_windup_integral` component.
/// Derivative is computed from successive error samples (1-step
/// finite difference). On `step` with `dt == 0.0` the derivative
/// term is skipped (avoids div-by-zero).
#[derive(Debug, Clone)]
pub struct PidController {
    pub kp: f64,
    pub ki: f64,
    pub kd: f64,
    /// Lower bound on integral. Anti-windup.
    pub integral_min: f64,
    /// Upper bound on integral. Anti-windup.
    pub integral_max: f64,
    integral: f64,
    last_error: Option<f64>,
}

impl PidController {
    pub fn new(kp: f64, ki: f64, kd: f64) -> Self {
        Self {
            kp, ki, kd,
            integral_min: -1e6,
            integral_max:  1e6,
            integral: 0.0,
            last_error: None,
        }
    }
    pub fn with_windup_bounds(mut self, lo: f64, hi: f64) -> Self {
        self.integral_min = lo;
        self.integral_max = hi;
        self
    }
    pub fn integral_value(&self) -> f64 { self.integral }
}

impl Controller for PidController {
    fn step(&mut self, error: f64, dt: f64) -> f64 {
        // Accumulate integral with anti-windup clamp.
        self.integral += error * dt;
        if self.integral > self.integral_max {
            self.integral = self.integral_max;
        } else if self.integral < self.integral_min {
            self.integral = self.integral_min;
        }
        // Derivative — 1-step finite diff. Skip when dt == 0
        // or no prior sample.
        let derivative = match (self.last_error, dt > 0.0) {
            (Some(prev), true) => (error - prev) / dt,
            _ => 0.0,
        };
        self.last_error = Some(error);
        self.kp * error + self.ki * self.integral + self.kd * derivative
    }
    fn reset(&mut self) {
        self.integral = 0.0;
        self.last_error = None;
    }
}

/// Outcome of a Kalman update. Callers can monitor `raw` to detect
/// estimator bias (persistent nonzero mean → model misfit per Mt
/// rule `estimator_persistent_bias_signals_model_misfit`).
#[derive(Debug, Clone, Copy)]
pub struct Innovation {
    /// y - x_hat (pre-update).
    pub raw: f64,
    /// Kalman gain at this step. Near 1.0 = trusts measurement
    /// heavily; near 0.0 = trusts model.
    pub gain: f64,
    /// Updated state estimate after applying gain × innovation.
    pub post_x_hat: f64,
}

/// 1D Kalman filter — scalar state, scalar measurement. Sufficient
/// for a single drive's state estimate. Multi-dimensional cases
/// would use matrix Kalman (future when needed).
///
/// State model:
///   x[t+1] = x[t] + u[t]  + N(0, q)        (process)
///   y[t]   = x[t]         + N(0, r)        (measurement)
///
/// Filter:
///   predict: x_hat ← x_hat + u;  p ← p + q
///   update:  K ← p / (p + r)
///            innovation ← y - x_hat
///            x_hat ← x_hat + K · innovation
///            p ← (1 - K) · p
#[derive(Debug, Clone)]
pub struct KalmanFilter1D {
    pub x_hat: f64,
    pub p: f64,
    pub q: f64,
    pub r: f64,
}

impl KalmanFilter1D {
    pub fn new(initial_estimate: f64, initial_covariance: f64,
                process_noise: f64, measurement_noise: f64) -> Self {
        Self {
            x_hat: initial_estimate,
            p: initial_covariance,
            q: process_noise,
            r: measurement_noise,
        }
    }

    /// Predict step: x_hat ← x_hat + u; p ← p + q.
    pub fn predict(&mut self, control_input: f64) {
        self.x_hat += control_input;
        self.p += self.q;
    }

    /// Update step: incorporate measurement; return Innovation.
    pub fn update(&mut self, measurement: f64) -> Innovation {
        let raw = measurement - self.x_hat;
        let gain = self.p / (self.p + self.r);
        self.x_hat += gain * raw;
        self.p = (1.0 - gain) * self.p;
        Innovation { raw, gain, post_x_hat: self.x_hat }
    }
}

/// A single substrate drive. Binds together the (setpoint,
/// measurement, controller, weight) tuple the Mt requires.
pub struct Drive {
    pub name: String,
    pub setpoint: f64,
    pub estimator: KalmanFilter1D,
    pub controller: Box<dyn Controller>,
    /// Composition weight for multi-drive systems. Higher weight =
    /// drive's control signal contributes more to the aggregate.
    pub weight: f64,
}

impl Drive {
    pub fn new(
        name: impl Into<String>,
        setpoint: f64,
        estimator: KalmanFilter1D,
        controller: Box<dyn Controller>,
    ) -> Self {
        Self { name: name.into(), setpoint, estimator,
                controller, weight: 1.0 }
    }
    pub fn with_weight(mut self, w: f64) -> Self {
        self.weight = w;
        self
    }

    /// Current measurement-based estimate.
    pub fn estimate(&self) -> f64 { self.estimator.x_hat }

    /// Error = setpoint - estimate.
    pub fn error(&self) -> f64 { self.setpoint - self.estimator.x_hat }

    /// Observe a fresh measurement, update the estimator. Returns
    /// the innovation so callers can monitor for bias.
    pub fn observe(&mut self, measurement: f64) -> Innovation {
        self.estimator.update(measurement)
    }

    /// Advance one control step. Computes error from current
    /// estimate + setpoint, runs the controller, returns the
    /// control signal `u`. Does NOT apply `u` to anything — the
    /// substrate's actuation surface is the caller's concern.
    pub fn step(&mut self, dt: f64) -> f64 {
        let e = self.error();
        self.controller.step(e, dt)
    }

    /// Reset controller state (e.g. on cooling, recompile, plant
    /// model invalidation).
    pub fn reset_controller(&mut self) {
        self.controller.reset();
    }
}

/// Multi-drive composition. The Mt's `multi_drive_composition_
/// weighted` component — aggregate control signal is a weighted sum
/// of per-drive signals.
pub struct MultiDriveSystem {
    pub drives: Vec<Drive>,
}

impl MultiDriveSystem {
    pub fn new() -> Self { Self { drives: Vec::new() } }

    pub fn add(&mut self, drive: Drive) -> usize {
        self.drives.push(drive);
        self.drives.len() - 1
    }

    pub fn drive(&self, idx: usize) -> &Drive { &self.drives[idx] }
    pub fn drive_mut(&mut self, idx: usize) -> &mut Drive {
        &mut self.drives[idx]
    }

    /// Run one tick: step every drive, return their weighted sum.
    /// The weight-normalisation is left to the caller — for some
    /// applications a sum is right (e.g. additive forces), for
    /// others a weighted average (e.g. blended preference).
    pub fn step_sum(&mut self, dt: f64) -> f64 {
        let mut acc = 0.0;
        for d in &mut self.drives {
            acc += d.weight * d.step(dt);
        }
        acc
    }

    /// Weighted average control signal — sum / total_weight.
    pub fn step_weighted_average(&mut self, dt: f64) -> f64 {
        let mut acc = 0.0;
        let mut total_w = 0.0;
        for d in &mut self.drives {
            acc += d.weight * d.step(dt);
            total_w += d.weight;
        }
        if total_w == 0.0 { 0.0 } else { acc / total_w }
    }
}

impl Default for MultiDriveSystem {
    fn default() -> Self { Self::new() }
}

#[cfg(test)]
mod tests {
    use super::*;

    // ---------- PID convergence (drives_converge_to_setpoint) ----------

    /// PID applied to a simple first-order integrator plant drives
    /// the state to the setpoint. Verifies the Mt's
    /// `drives_converge_to_setpoint` invariant on a tractable plant.
    ///
    /// Plant: x[t+1] = x[t] + dt × u[t].
    /// Goal: x → setpoint as t → ∞.
    #[test]
    fn pid_converges_on_first_order_integrator() {
        let mut pid = PidController::new(1.0, 0.5, 0.05);
        let setpoint = 10.0;
        let mut state = 0.0;
        let dt = 0.1;
        for _ in 0..500 {
            let error = setpoint - state;
            let u = pid.step(error, dt);
            state += u * dt;
        }
        let final_error = (setpoint - state).abs();
        assert!(final_error < 0.05,
                "PID should converge near setpoint; got |error|={}",
                final_error);
    }

    // ---------- Anti-windup (integral_bounded_by_anti_windup) ----------

    /// With saturating positive error, the integral term stays
    /// within `[integral_min, integral_max]` after each step.
    /// Verifies the Mt's `integral_bounded_by_anti_windup` invariant.
    #[test]
    fn anti_windup_clamps_integral_under_saturation() {
        let mut pid = PidController::new(1.0, 1.0, 0.0)
            .with_windup_bounds(-5.0, 5.0);
        // Apply persistent large positive error; without anti-windup,
        // integral would grow unbounded.
        for _ in 0..1000 {
            pid.step(100.0, 0.01);
        }
        let i = pid.integral_value();
        assert!(i <= 5.0 + 1e-9,
                "integral exceeded upper bound: {}", i);
        assert!(i >= -5.0 - 1e-9,
                "integral exceeded lower bound: {}", i);
        // Symmetric: persistent negative error pegs at lower bound.
        for _ in 0..1000 {
            pid.step(-100.0, 0.01);
        }
        let i = pid.integral_value();
        assert!(i >= -5.0 - 1e-9 && i <= 5.0 + 1e-9,
                "integral exceeded bounds on negative side: {}", i);
    }

    /// PID reset zeros the integral + derivative-state.
    #[test]
    fn pid_reset_clears_state() {
        let mut pid = PidController::new(1.0, 1.0, 1.0);
        pid.step(5.0, 0.1);
        pid.step(3.0, 0.1);
        assert_ne!(pid.integral_value(), 0.0);
        pid.reset();
        assert_eq!(pid.integral_value(), 0.0);
        assert!(pid.last_error.is_none());
    }

    // ---------- Kalman unbiased estimator (estimator_unbiased) -------

    /// Kalman filter fed measurements from a constant-mean process
    /// converges its estimate to that mean. Sum of innovations →
    /// 0 over time (unbiased).
    #[test]
    fn kalman_converges_to_constant_mean() {
        // Process: true state = 7.0. Measurements perturb around it.
        let mut kf = KalmanFilter1D::new(0.0, 100.0, 0.0, 1.0);
        // Deterministic alternating perturbation around true mean.
        let measurements: Vec<f64> = (0..200)
            .map(|i| 7.0 + if i % 2 == 0 { 0.5 } else { -0.5 })
            .collect();
        let mut innovation_sum = 0.0;
        for m in &measurements {
            let inn = kf.update(*m);
            innovation_sum += inn.raw;
        }
        // Estimate close to true mean.
        assert!((kf.x_hat - 7.0).abs() < 0.1,
                "Kalman should converge to 7.0; got {}", kf.x_hat);
        // Innovation sum bounded (unbiased over symmetric perturbation).
        // Early innovations are large; we just check it's reasonable.
        assert!(innovation_sum.abs() < 10.0,
                "innovation sum should be small under symmetric perturbation; got {}",
                innovation_sum);
    }

    /// Kalman gain decreases monotonically as covariance shrinks
    /// (each update reduces uncertainty when R > 0).
    #[test]
    fn kalman_gain_decreases_with_repeated_updates() {
        let mut kf = KalmanFilter1D::new(0.0, 100.0, 0.0, 1.0);
        let g1 = kf.update(5.0).gain;
        let g2 = kf.update(5.0).gain;
        let g3 = kf.update(5.0).gain;
        assert!(g1 > g2 && g2 > g3,
                "Kalman gain should decrease as covariance shrinks; got {} > {} > {}",
                g1, g2, g3);
    }

    // ---------- Drive composition ----------

    /// Drive observes measurement + steps controller end-to-end.
    /// Verifies the full Drive surface composes.
    #[test]
    fn drive_observes_and_steps() {
        let kf = KalmanFilter1D::new(0.0, 10.0, 0.01, 1.0);
        let pid = PidController::new(1.0, 0.0, 0.0);
        let mut d = Drive::new("test_drive", 5.0, kf, Box::new(pid));
        assert_eq!(d.setpoint, 5.0);
        d.observe(4.0);
        assert!(d.error() > 0.0);
        let u = d.step(0.1);
        // P-only controller → u proportional to current error.
        assert!(u > 0.0);
    }

    /// Multi-drive weighted-average composition: two drives with
    /// opposing setpoints + different weights produce a weighted
    /// blend.
    #[test]
    fn multi_drive_weighted_average() {
        let mut sys = MultiDriveSystem::new();
        // Drive A: setpoint 10, weight 3.
        let kf_a = KalmanFilter1D::new(0.0, 10.0, 0.01, 1.0);
        let pid_a = PidController::new(1.0, 0.0, 0.0);
        sys.add(Drive::new("a", 10.0, kf_a, Box::new(pid_a))
                .with_weight(3.0));
        // Drive B: setpoint -10, weight 1.
        let kf_b = KalmanFilter1D::new(0.0, 10.0, 0.01, 1.0);
        let pid_b = PidController::new(1.0, 0.0, 0.0);
        sys.add(Drive::new("b", -10.0, kf_b, Box::new(pid_b))
                .with_weight(1.0));
        // Both drives observe state=0 → errors are +10 and -10.
        let u = sys.step_weighted_average(0.1);
        // Weighted avg: (3·10 + 1·(-10)) / (3+1) = 20/4 = 5.
        assert!((u - 5.0).abs() < 1e-9,
                "weighted average expected 5.0, got {}", u);
    }

    /// A Drive's controller can be reset (e.g. on cooling).
    #[test]
    fn drive_reset_propagates_to_controller() {
        let kf = KalmanFilter1D::new(0.0, 10.0, 0.01, 1.0);
        let pid = PidController::new(1.0, 1.0, 0.0);
        let mut d = Drive::new("d", 5.0, kf, Box::new(pid));
        d.observe(0.0);
        d.step(0.1);
        d.step(0.1);
        // Reset.
        d.reset_controller();
        // After reset, no integral accumulation, derivative skipped.
        // Verifying via behaviour: step(0, dt) yields 0.
        let u = d.step(0.0); // dt=0 skips derivative + integral
        // Actually with dt=0 + error=5, integral += 0, derivative
        // skipped due to dt=0, so u = kp * e = 5.
        assert!((u - 5.0).abs() < 1e-9,
                "after reset, P term should dominate; got {}", u);
    }

    // ---------- Mt rule: drive_must_have_setpoint_and_measurement --

    /// Constructing a Drive without setpoint + estimator + controller
    /// is impossible — the type system enforces the Mt's rule that
    /// a drive must have all three. Verified at the type level (no
    /// runtime test needed; this comment documents the property).
    #[test]
    fn drive_construction_requires_three_tuple() {
        // The signature of Drive::new takes (name, setpoint,
        // estimator, controller) — all four required, no defaults.
        // Removing any breaks compilation. Documenting this in a
        // test so the invariant is visible.
        let _ = Drive::new(
            "stub", 0.0,
            KalmanFilter1D::new(0.0, 1.0, 0.01, 1.0),
            Box::new(PidController::new(1.0, 0.0, 0.0)),
        );
    }
}
