//! G5 — THE RESPONSIVENESS GATE.
//!
//! # The failure this catches, and why nothing else does
//!
//! `VISION_VIDEO_PROBE_RERUN_RESULTS.md` §3.1: arm A8's pre-registered
//! counted-operation statistic was **byte-identical across an 11.8x range of N
//! while wall-clock grew 13x**, and **all four of its pre-declared gates
//! passed** — zero-when-off, liveness, determinism, and N-varies. Read
//! literally, the pre-registered rule returned *"the sd/identity layer is not
//! the binding term; the wall fell"*: a fluent, gated, entirely wrong answer.
//!
//! This arc has caught eleven inert instruments. **All eleven were DEAD** — a
//! counter reading zero, a hook on the wrong store, a path that never ran.
//! A8's was **ALIVE, DETERMINISTIC, CONSERVED — AND INSENSITIVE.** Every
//! existing gate is jointly satisfied by an instrument measuring something else
//! entirely, because every existing gate asks *"is it non-zero?"* and none asks
//! *"does it MOVE WITH the thing being varied?"*
//!
//! # The criterion, and where it FALLS OUT (PROTOCOL §13)
//!
//! No threshold is chosen. The bar a counter must clear is **measured**, from a
//! control run in the same process on the same machine:
//!
//! - **sweep** — the counter read at `m` points as its claimed axis varies;
//! - **control** — the counter read at `m` points with the axis held FIXED at
//!   the sweep's first value.
//!
//! `span(S) = max(S) - min(S)`, and:
//!
//! | verdict | condition |
//! |---|---|
//! | **Inert** | `max(sweep) == 0` — never exercised; this workload cannot rule |
//! | **Responsive** | `span(sweep) > span(control)` |
//! | **Blind** | otherwise |
//!
//! The control span is the counter's own noise under exactly the sweep's
//! conditions. G3 (determinism) predicts it is **exactly zero** for these
//! integer counters, in which case G5 reduces to *"did it move at all"* — which
//! is what the rerun results named as the missing gate. Writing the criterion
//! against the **measured** control rather than the assumed zero costs nothing
//! and keeps the gate correct if any counter ever becomes non-deterministic.
//!
//! **`Inert` is NOT a pass.** It is an explicit statement that the counter
//! remains unvalidated, pre-registered as a distinct verdict precisely so that
//! "it was never exercised" cannot be argued afterwards as though it were a
//! pass.
//!
//! # ρ is REPORTED, NEVER GATED
//!
//! `rho` is the log-log slope of counter against axis across the sweep: ~0 means
//! blind, ~1 means proportional. **It decides nothing.** Gating on ρ would
//! require choosing a number, which is the §13 violation this design exists to
//! avoid. It is reported so the next rung knows how strongly each counter tracks
//! its axis.
//!
//! # One implementation, two callers
//!
//! The verdict is a pure function here, unit-tested below on synthetic series
//! (constant ⇒ Blind, monotone ⇒ Responsive, all-zero ⇒ Inert), and exposed to
//! the Python harness through `py.rs`. The harness does NOT reimplement it: a
//! second copy in Python is a copy that drifts, and a gate that drifts from the
//! gate it was tested as is not a gate.

/// The three-way G5 verdict. Pre-registered before any measurement.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum G5Verdict {
    /// `span(sweep) > span(control)` — the counter moves with its axis.
    Responsive,
    /// Exercised, but does not move more than its own measured noise.
    Blind,
    /// Identically zero across the sweep — not exercised, cannot rule.
    Inert,
}

impl G5Verdict {
    pub fn as_str(self) -> &'static str {
        match self {
            G5Verdict::Responsive => "RESPONSIVE",
            G5Verdict::Blind => "BLIND",
            G5Verdict::Inert => "INERT",
        }
    }
}

fn span(s: &[u64]) -> u64 {
    match (s.iter().min(), s.iter().max()) {
        (Some(lo), Some(hi)) => hi - lo,
        _ => 0,
    }
}

/// The G5 decision. `sweep` is the counter across the varying axis; `control` is
/// the same counter across the axis held fixed.
///
/// An EMPTY sweep is `Inert`, not `Responsive`: a gate must never return its
/// pass verdict for the absence of data.
pub fn verdict(sweep: &[u64], control: &[u64]) -> G5Verdict {
    if sweep.is_empty() || sweep.iter().all(|&v| v == 0) {
        return G5Verdict::Inert;
    }
    if span(sweep) > span(control) {
        G5Verdict::Responsive
    } else {
        G5Verdict::Blind
    }
}

/// ρ — the log-log responsiveness diagnostic. `None` when it is undefined
/// (fewer than two points, a zero counter value, or a non-varying axis) rather
/// than a fabricated 0.0, which would read as "measured and blind" when the
/// truth is "not computable here".
///
/// **Never used to pass or fail anything** (see the module doc).
pub fn rho(counter: &[u64], axis: &[f64]) -> Option<f64> {
    if counter.len() < 2 || counter.len() != axis.len() {
        return None;
    }
    let cmin = *counter.iter().min()? as f64;
    let cmax = *counter.iter().max()? as f64;
    let amin = axis.iter().cloned().fold(f64::INFINITY, f64::min);
    let amax = axis.iter().cloned().fold(f64::NEG_INFINITY, f64::max);
    if cmin <= 0.0 || amin <= 0.0 || amax <= amin {
        return None;
    }
    Some((cmax / cmin).ln() / (amax / amin).ln())
}

#[cfg(test)]
mod tests {
    use super::*;

    /// THE RED CONTROL, as a pure function. A gate that has never been shown to
    /// fail has not been tested — a lesson this arc has paid for repeatedly.
    /// This is the A8 signature exactly: alive (non-zero), deterministic
    /// (control span 0), conserved, and CONSTANT across the sweep.
    #[test]
    fn a_constant_but_live_counter_is_blind() {
        let sweep = [253u64, 253, 253, 253, 253, 253, 253];
        let control = [253u64; 7];
        assert_eq!(verdict(&sweep, &control), G5Verdict::Blind);
    }

    /// THE GREEN CONTROL — a counter that tracks its axis.
    #[test]
    fn a_moving_counter_is_responsive() {
        let sweep = [10u64, 20, 40, 80, 160, 320, 640];
        let control = [10u64; 7];
        assert_eq!(verdict(&sweep, &control), G5Verdict::Responsive);
    }

    /// Never exercised ⇒ INERT, which is explicitly NOT a pass.
    #[test]
    fn an_unexercised_counter_is_inert_not_a_pass() {
        assert_eq!(verdict(&[0u64; 7], &[0u64; 7]), G5Verdict::Inert);
        assert_ne!(verdict(&[0u64; 7], &[0u64; 7]), G5Verdict::Responsive);
    }

    /// A counter that moves by exactly as much as its own noise is BLIND, not
    /// responsive: the comparison is strict, so noise alone can never pass.
    #[test]
    fn movement_equal_to_noise_does_not_pass() {
        let sweep = [10u64, 11, 10, 11, 10, 11, 10];
        let control = [10u64, 11, 11, 10, 10, 11, 10];
        assert_eq!(span(&sweep), span(&control));
        assert_eq!(verdict(&sweep, &control), G5Verdict::Blind);
    }

    /// Movement that exceeds a NON-ZERO noise floor still passes — the
    /// criterion is the measured control, not an assumed zero.
    #[test]
    fn movement_beyond_a_nonzero_noise_floor_passes() {
        let sweep = [10u64, 30, 50, 70, 90, 110, 130];
        let control = [10u64, 11, 12, 10, 11, 12, 10];
        assert_eq!(verdict(&sweep, &control), G5Verdict::Responsive);
    }

    /// An empty sweep must not read as a pass.
    #[test]
    fn no_data_is_never_a_pass() {
        assert_eq!(verdict(&[], &[]), G5Verdict::Inert);
    }

    /// ρ on an exactly-proportional series is 1; on a constant series 0; and
    /// undefined rather than 0.0 when it cannot be computed.
    #[test]
    fn rho_reads_the_slope_and_refuses_when_undefined() {
        let axis = [1.0, 2.0, 4.0, 8.0];
        assert!((rho(&[10, 20, 40, 80], &axis).unwrap() - 1.0).abs() < 1e-12);
        assert!((rho(&[10, 10, 10, 10], &axis).unwrap() - 0.0).abs() < 1e-12);
        assert!((rho(&[10, 40, 160, 640], &axis).unwrap() - 2.0).abs() < 1e-12);
        // a zero counter value ⇒ undefined, NOT a fabricated 0.0
        assert_eq!(rho(&[0, 20, 40, 80], &axis), None);
        // a non-varying axis ⇒ undefined
        assert_eq!(rho(&[10, 20, 40, 80], &[2.0, 2.0, 2.0, 2.0]), None);
    }
}
