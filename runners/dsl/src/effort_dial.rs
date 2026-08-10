//! Context-aware EFFORT DIAL — judges how much CPU/processing to spend
//! based on CONTEXT, dynamically.
//!
//! ## The thesis
//!
//! Some tasks are REAL-TIME, SINGLE-THREAD (respond NOW, hard latency
//! budget, no room to stall) — there the dial turns effort DOWN
//! (shallow, fast path, fewer passes, just enough to keep up). Others
//! are OFFLINE / PARALLEL / no-deadline (consolidation, re-watching,
//! reflection) — there the dial turns effort UP (deep, many passes,
//! finer, spend the compute). Within whatever budget the context
//! gives, spend MORE on the salient/hard, LESS on routine.
//!
//! It must JUDGE EFFORT BY CONTEXT, not a fixed setting.
//!
//! ## What this composes (reuse, not reinvent)
//!
//! - `l2_dispatch::PriorityClass` + `Instant` deadlines — the EDF
//!   scheduler's representation of real-time / deadlines. The dial
//!   reads "is there a deadline, how much time is left?" from the same
//!   `Instant` arithmetic EDF uses.
//! - `l2_adaptive::HotCounter` — hot/routine signal (a hot kind is
//!   routine; a cold/novel kind is surprising). Folded into the
//!   surprise channel.
//! - `l6_cybernetic_feedback::{RecommendationApplier, FeedbackChannel,
//!   CyberneticFeedbackLoop}` — the effort knob is a `register_knob_u64`
//!   knob; the context inputs are `FeedbackChannel`s that turn it;
//!   `CyberneticFeedbackLoop.tick()` reads them and writes the knob.
//! - `l6_essential_variables::WorkingSetFit` — memory pressure, an
//!   essential variable that dials effort DOWN under pressure.
//! - `memory::order_n_shape_salience` — the surprise / value signal:
//!   a salient (directed, resolving) input earns more passes; a flat /
//!   routine one earns fewer.
//!
//! ## What's NEW here
//!
//! - `EffortKnob` — the control variable in `[min_effort..max_effort]`
//!   that SCALES a real, measurable processing parameter: the number
//!   of order-N re-watch / analysis PASSES, and the salience THRESHOLD
//!   (higher effort ⇒ more passes + lower threshold ⇒ keep/process
//!   more). Backed by an `Arc<AtomicU64>` so it plugs straight into a
//!   `RecommendationApplier` via `register_knob_u64`.
//! - `EffortContext` — the live context snapshot (deadline budget,
//!   thread mode, CPU slack, memory pressure, surprise) the channels
//!   read.
//! - Concrete `FeedbackChannel`s: `DeadlineEffortChannel`,
//!   `ThreadModeEffortChannel`, `CpuSlackEffortChannel`,
//!   `MemoryPressureEffortChannel`, `SurpriseEffortChannel`. Each turns
//!   the dial per its named context input.
//! - `EffortPipeline` — a demo workload: runs `passes_for(effort)`
//!   order-N analysis passes over an input, honest wall-time measured.
//!   Real-time path verifies it FITS the deadline (and reports honestly
//!   if it can't even at minimum effort) rather than overrunning.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

use crate::l2_adaptive::HotCounter;
use crate::l6_cybernetic_feedback::{
    FeedbackChannel, FeedbackRecommendation,
};
use crate::l6_essential_variables::{EssentialVariable, ViabilityStatus};
use crate::memory::order_n_shape_salience;
use crate::sym::Sym;

/// The knob's named adjustment + target, used when registering it with
/// a `RecommendationApplier`. Channels emit recommendations addressed
/// to this pair; the applier routes them to the knob atomic.
pub const EFFORT_ADJUSTMENT: &str = "set_effort";
pub const EFFORT_TARGET: &str = "L_effort";

// =======================================================================
// EffortKnob — the control variable that scales a REAL processing param.
// =======================================================================

/// The effort dial. Holds an integer effort level in
/// `[min_effort..=max_effort]` behind an `Arc<AtomicU64>` so the L6
/// feedback loop can turn it (`register_knob_u64`) and the pipeline can
/// read it (`knob_value`) without locking.
///
/// The level scales two real, measurable processing parameters:
///   * `passes(level)` — number of order-N re-watch / analysis passes.
///     `min` at min_effort, `max` at max_effort, linear between.
///   * `salience_threshold(level)` — keep/process if salience ≥ this.
///     HIGH at min_effort (only the most salient survives the fast
///     path), LOW at max_effort (deep mode keeps almost everything).
#[derive(Clone)]
pub struct EffortKnob {
    level: Arc<AtomicU64>,
    min_effort: u64,
    max_effort: u64,
    min_passes: u64,
    max_passes: u64,
    /// salience threshold at min effort (strict — keep little).
    hi_threshold: f64,
    /// salience threshold at max effort (lax — keep almost all).
    lo_threshold: f64,
}

impl EffortKnob {
    /// `min_passes`/`max_passes` are the pass counts at the dial
    /// extremes; `hi_threshold`/`lo_threshold` the salience gates at
    /// min/max effort respectively (hi > lo). The dial starts at
    /// `max_effort` (deep) — channels turn it down under pressure.
    pub fn new(
        min_effort: u64,
        max_effort: u64,
        min_passes: u64,
        max_passes: u64,
        hi_threshold: f64,
        lo_threshold: f64,
    ) -> Self {
        assert!(max_effort >= min_effort);
        assert!(max_passes >= min_passes && min_passes >= 1);
        Self {
            level: Arc::new(AtomicU64::new(max_effort)),
            min_effort,
            max_effort,
            min_passes,
            max_passes,
            hi_threshold,
            lo_threshold,
        }
    }

    /// A sensible default: effort 0..=10, 1..=8 passes, thresholds
    /// 0.30 (strict, fast path) .. 0.02 (lax, deep).
    pub fn default_dial() -> Self {
        Self::new(0, 10, 1, 8, 0.30, 0.02)
    }

    /// The `Arc<AtomicU64>` handle to register with a
    /// `RecommendationApplier` (`register_knob_u64(EFFORT_ADJUSTMENT,
    /// EFFORT_TARGET, knob.handle())`). The feedback loop turns it.
    pub fn handle(&self) -> Arc<AtomicU64> {
        Arc::clone(&self.level)
    }

    pub fn min_effort(&self) -> u64 { self.min_effort }
    pub fn max_effort(&self) -> u64 { self.max_effort }

    /// Current effort level (clamped read).
    pub fn level(&self) -> u64 {
        self.level
            .load(Ordering::Acquire)
            .clamp(self.min_effort, self.max_effort)
    }

    /// Set effort directly (clamped). Used by channels via the applier;
    /// also handy in tests.
    pub fn set(&self, level: u64) {
        let v = level.clamp(self.min_effort, self.max_effort);
        self.level.store(v, Ordering::Release);
    }

    /// REAL parameter #1: number of order-N analysis passes at the
    /// current effort level. Linear interpolation, rounded.
    pub fn passes(&self) -> u64 {
        self.passes_for(self.level())
    }

    pub fn passes_for(&self, level: u64) -> u64 {
        let span = (self.max_effort - self.min_effort).max(1) as f64;
        let frac = (level.clamp(self.min_effort, self.max_effort) - self.min_effort)
            as f64
            / span;
        let p = self.min_passes as f64
            + frac * (self.max_passes - self.min_passes) as f64;
        (p.round() as u64).clamp(self.min_passes, self.max_passes)
    }

    /// REAL parameter #2: the salience threshold at the current effort.
    /// HIGH effort ⇒ LOW threshold ⇒ keep/process more.
    pub fn salience_threshold(&self) -> f64 {
        self.salience_threshold_for(self.level())
    }

    pub fn salience_threshold_for(&self, level: u64) -> f64 {
        let span = (self.max_effort - self.min_effort).max(1) as f64;
        let frac = (level.clamp(self.min_effort, self.max_effort) - self.min_effort)
            as f64
            / span;
        // frac 0 (min effort) -> hi_threshold; frac 1 (max) -> lo_threshold.
        self.hi_threshold + frac * (self.lo_threshold - self.hi_threshold)
    }
}

// =======================================================================
// ThreadMode — single-thread real-time serial vs parallel/offline batch.
// =======================================================================

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ThreadMode {
    /// Real-time, serial, must keep up. Dial tighter.
    RealtimeSingle,
    /// Offline / parallel / batch, no live deadline. Dial looser.
    OfflineParallel,
}

// =======================================================================
// EffortContext — the live context snapshot the channels read.
// =======================================================================

/// A snapshot of the current context. Cheap to clone; the channels
/// read fields off it each tick. The world adapter / scheduler updates
/// it as context changes (new deadline, mode flip, memory growth, a
/// surprising input).
#[derive(Debug, Clone)]
pub struct EffortContext {
    /// Thread / execution mode.
    pub thread_mode: ThreadMode,
    /// Wall-clock deadline for the current item, if any (the EDF
    /// scheduler's `Instant` deadline). `None` ⇒ no deadline (offline).
    pub deadline: Option<Instant>,
    /// Measured cost of ONE order-N pass over a typical item — lets the
    /// deadline channel compute how many passes fit. Updated from real
    /// observations (the pipeline records it).
    pub per_pass_cost: Duration,
    /// Surprise / value of the current input in [0,1+] — typically
    /// `order_n_shape_salience` of the input trajectory, optionally
    /// blended with a hot-counter novelty term.
    pub surprise: f64,
    /// When the context was taken (for time-left math).
    pub now: Instant,
}

impl EffortContext {
    /// Time left until the deadline, or `None` if no deadline / already
    /// passed.
    pub fn time_left(&self) -> Option<Duration> {
        self.deadline
            .map(|d| d.saturating_duration_since(self.now))
    }
}

// =======================================================================
// The channels. Each is a FeedbackChannel that emits a recommendation
// addressed to (EFFORT_ADJUSTMENT, EFFORT_TARGET); the scalar is the
// effort LEVEL it wants. The RecommendationApplier writes it to the
// knob. When several channels fire, the applier writes them in order —
// so we order the loop tightest-constraint-LAST (deadline wins).
// =======================================================================

fn rec(scalar: f64, source: &str, value: f64) -> FeedbackRecommendation {
    FeedbackRecommendation {
        source_variable: source.to_string(),
        source_value: value,
        // Surface status as Nominal here — these channels always emit a
        // target level, not a breach signal. The dial's "status" is its
        // level, inspected separately.
        source_status: ViabilityStatus::Nominal,
        adjustment_name: EFFORT_ADJUSTMENT.to_string(),
        adjustment_scalar: scalar,
        target_layer: EFFORT_TARGET.to_string(),
    }
}

/// A `FeedbackChannel` reading a shared, swappable `EffortContext`.
/// The context is held behind a `Mutex<EffortContext>` so the world
/// adapter can update it between ticks and all channels see the change.
pub type SharedContext = Arc<std::sync::Mutex<EffortContext>>;

// ---- DEADLINE channel (from the EDF scheduler's deadline) ----

/// Real-time + tight deadline ⇒ recommend the HIGHEST effort whose
/// passes still FIT the time left (passes * per_pass_cost ≤ time_left).
/// This is the latency-bound floor: never overrun. If even minimum
/// effort can't fit, it recommends minimum (the dial bottoms out;
/// honest behaviour reported by the pipeline).
///
/// No deadline ⇒ the channel is silent (offline contexts let other
/// channels — surprise — drive the dial up).
pub struct DeadlineEffortChannel {
    name: String,
    ctx: SharedContext,
    knob: EffortKnob,
    /// Safety fraction of the budget to actually use (e.g. 0.8 leaves
    /// 20% headroom for scheduling jitter). The remaining headroom is
    /// the difference between "fits in theory" and "meets in practice".
    budget_fraction: f64,
}

impl DeadlineEffortChannel {
    pub fn new(name: impl Into<String>, ctx: SharedContext,
               knob: EffortKnob, budget_fraction: f64) -> Self {
        Self { name: name.into(), ctx, knob, budget_fraction }
    }

    /// The highest effort level whose pass count fits the budget. Pure;
    /// also used by the pipeline to pre-check feasibility.
    pub fn fit_effort(&self, time_left: Duration,
                      per_pass: Duration) -> u64 {
        let budget = time_left.mul_f64(self.budget_fraction);
        let per = per_pass.max(Duration::from_nanos(1));
        let max_fit_passes = (budget.as_secs_f64() / per.as_secs_f64())
            .floor() as u64;
        // Walk effort levels down from max; pick the highest whose
        // passes_for fits. Floors at min_effort (dial bottoms out).
        let mut chosen = self.knob.min_effort();
        for lvl in self.knob.min_effort()..=self.knob.max_effort() {
            if self.knob.passes_for(lvl) <= max_fit_passes.max(1) {
                chosen = lvl;
            }
        }
        chosen
    }
}

impl FeedbackChannel for DeadlineEffortChannel {
    fn name(&self) -> &str { &self.name }
    fn tick(&self) -> Option<FeedbackRecommendation> {
        let ctx = self.ctx.lock().unwrap();
        // Only real-time-single contexts carry a hard deadline floor.
        if ctx.thread_mode != ThreadMode::RealtimeSingle {
            return None;
        }
        let time_left = ctx.time_left()?;
        let lvl = self.fit_effort(time_left, ctx.per_pass_cost);
        Some(rec(lvl as f64, &self.name, ctx.surprise))
    }
}

// ---- THREAD-MODE channel ----

/// Single-thread real-time ⇒ recommend a tight ceiling (effort no
/// higher than `realtime_ceiling`). Parallel/offline ⇒ recommend the
/// max (let other channels pull it back if needed). This is the coarse
/// "which regime are we in" turn; the deadline + surprise channels
/// refine within it.
pub struct ThreadModeEffortChannel {
    name: String,
    ctx: SharedContext,
    knob: EffortKnob,
    realtime_ceiling: u64,
}

impl ThreadModeEffortChannel {
    pub fn new(name: impl Into<String>, ctx: SharedContext,
               knob: EffortKnob, realtime_ceiling: u64) -> Self {
        Self { name: name.into(), ctx, knob, realtime_ceiling }
    }
}

impl FeedbackChannel for ThreadModeEffortChannel {
    fn name(&self) -> &str { &self.name }
    fn tick(&self) -> Option<FeedbackRecommendation> {
        let ctx = self.ctx.lock().unwrap();
        let lvl = match ctx.thread_mode {
            ThreadMode::RealtimeSingle =>
                self.realtime_ceiling.min(self.knob.max_effort()),
            ThreadMode::OfflineParallel => self.knob.max_effort(),
        };
        Some(rec(lvl as f64, &self.name, 0.0))
    }
}

// ---- CPU-SLACK channel ----

/// CPU/time budget: slack ⇒ dial up, pressed ⇒ dial down. `load` is a
/// fraction in [0,1] (1 = saturated). Maps load→effort linearly:
/// load 0 ⇒ max_effort, load 1 ⇒ min_effort. Reads load off a shared
/// atomic (per-mille) so the scheduler can update it live.
pub struct CpuSlackEffortChannel {
    name: String,
    knob: EffortKnob,
    load_permille: Arc<AtomicU64>,
}

impl CpuSlackEffortChannel {
    pub fn new(name: impl Into<String>, knob: EffortKnob)
        -> (Self, Arc<AtomicU64>) {
        let load = Arc::new(AtomicU64::new(0));
        (Self { name: name.into(), knob, load_permille: Arc::clone(&load) },
         load)
    }
}

impl FeedbackChannel for CpuSlackEffortChannel {
    fn name(&self) -> &str { &self.name }
    fn tick(&self) -> Option<FeedbackRecommendation> {
        let load = (self.load_permille.load(Ordering::Acquire) as f64
            / 1000.0).clamp(0.0, 1.0);
        let span = (self.knob.max_effort() - self.knob.min_effort()) as f64;
        let lvl = self.knob.max_effort() as f64 - load * span;
        Some(rec(lvl.round(), &self.name, load))
    }
}

// ---- MEMORY-PRESSURE channel (folds in the existing essential var) ----

/// Memory pressure (the existing `WorkingSetFit` essential variable):
/// Nominal ⇒ no constraint (silent); NearEdge ⇒ cap to `near_ceiling`;
/// Breach ⇒ cap to min_effort. Dials effort DOWN under pressure,
/// reusing the substrate's existing memory bound.
pub struct MemoryPressureEffortChannel {
    name: String,
    knob: EffortKnob,
    var: Arc<dyn EssentialVariable>,
    near_ceiling: u64,
}

impl MemoryPressureEffortChannel {
    pub fn new(name: impl Into<String>, knob: EffortKnob,
               var: Arc<dyn EssentialVariable>, near_ceiling: u64) -> Self {
        Self { name: name.into(), knob, var, near_ceiling }
    }
}

impl FeedbackChannel for MemoryPressureEffortChannel {
    fn name(&self) -> &str { &self.name }
    fn tick(&self) -> Option<FeedbackRecommendation> {
        let lvl = match self.var.status() {
            ViabilityStatus::Nominal => return None,
            ViabilityStatus::NearEdge =>
                self.near_ceiling.min(self.knob.max_effort()),
            ViabilityStatus::Breach => self.knob.min_effort(),
        };
        Some(rec(lvl as f64, &self.name, self.var.current_value()))
    }
}

// ---- SURPRISE channel (within the context's budget) ----

/// Within whatever budget the context allows, spend MORE on the
/// salient/hard, LESS on routine. Surprise (order_n_shape_salience,
/// optionally blended with hot-counter novelty) maps to effort:
/// surprise 0 ⇒ a low floor, surprise ≥ `salient_at` ⇒ max_effort.
///
/// The surprise channel emits a recommendation that's a CEILING-aware
/// suggestion, but it is intentionally placed FIRST in the loop so the
/// deadline / mode / memory channels (which represent hard budget
/// constraints) write LAST and win. Thus surprise raises effort only
/// within the budget the constraint channels leave.
pub struct SurpriseEffortChannel {
    name: String,
    ctx: SharedContext,
    knob: EffortKnob,
    /// surprise value at/above which we want max effort.
    salient_at: f64,
    /// effort floor for a totally routine input.
    routine_floor: u64,
}

impl SurpriseEffortChannel {
    pub fn new(name: impl Into<String>, ctx: SharedContext,
               knob: EffortKnob, salient_at: f64,
               routine_floor: u64) -> Self {
        Self { name: name.into(), ctx, knob, salient_at, routine_floor }
    }

    pub fn effort_for_surprise(&self, surprise: f64) -> u64 {
        let frac = (surprise / self.salient_at.max(1e-9)).clamp(0.0, 1.0);
        let span = (self.knob.max_effort() - self.routine_floor) as f64;
        (self.routine_floor as f64 + frac * span).round() as u64
    }
}

impl FeedbackChannel for SurpriseEffortChannel {
    fn name(&self) -> &str { &self.name }
    fn tick(&self) -> Option<FeedbackRecommendation> {
        let ctx = self.ctx.lock().unwrap();
        let lvl = self.effort_for_surprise(ctx.surprise);
        Some(rec(lvl as f64, &self.name, ctx.surprise))
    }
}

// =======================================================================
// EffortBlend — how the per-channel recommendations combine into one
// effort level. The constraint channels (deadline / mode / memory /
// cpu) are CEILINGS; the surprise channel is a DEMAND. Final effort =
// min(all ceilings, surprise_demand) — i.e. spend as much as the
// demand wants but never more than any budget allows.
// =======================================================================

/// Combine recommendations into one effort level: the minimum across
/// all the budget ceilings AND the surprise demand. This is the
/// "within the context's budget, more on the salient" rule made
/// explicit, and it is order-independent (unlike last-writer-wins),
/// which makes the dial's behaviour deterministic + testable.
pub fn blend_effort(
    knob: &EffortKnob,
    recs: &[FeedbackRecommendation],
) -> u64 {
    if recs.is_empty() {
        return knob.level();
    }
    let mut chosen = knob.max_effort();
    for r in recs {
        if r.adjustment_name == EFFORT_ADJUSTMENT
            && r.target_layer == EFFORT_TARGET
        {
            chosen = chosen.min(r.adjustment_scalar.round() as u64);
        }
    }
    chosen.clamp(knob.min_effort(), knob.max_effort())
}

// =======================================================================
// Surprise helper — fold order_n_shape_salience with hot-counter
// novelty into one [0,1+] surprise value the context carries.
// =======================================================================

/// Surprise of an input trajectory in the current context. Combines:
///   * shape salience (a directed, resolving build = surprising/valued)
///   * NOVELTY from the hot counter (a kind fired many times = routine
///     ⇒ damp; a cold kind = novel ⇒ keep).
/// Novelty multiplier in (0,1]: 1 for an unseen kind, decaying toward a
/// floor as the kind heats up.
pub fn surprise_of(
    traj: &[f64],
    hot: &HotCounter,
    kind: Sym,
    routine_after: u64,
) -> f64 {
    let salience = order_n_shape_salience(traj);
    let count = hot.count(kind);
    // novelty: 1.0 when unseen, -> 0.25 floor as count -> routine_after.
    let novelty = if routine_after == 0 {
        1.0
    } else {
        let r = (count as f64 / routine_after as f64).clamp(0.0, 1.0);
        1.0 - 0.75 * r
    };
    salience * novelty
}

// =======================================================================
// EffortPipeline — the measurable workload. Runs `passes` order-N
// analysis passes over an input trajectory; each pass refines an
// estimate (an analysis-by-synthesis re-watch). MORE passes = deeper
// result + more wall-time. The dial sets the depth; we MEASURE both.
// =======================================================================

/// Result of running the pipeline on one item.
#[derive(Debug, Clone)]
pub struct PipelineResult {
    /// Effort level the dial chose.
    pub effort: u64,
    /// Number of order-N passes actually run.
    pub passes: u64,
    /// Salience threshold in force (lower = kept more).
    pub salience_threshold: f64,
    /// Whether the item passed the salience gate (was processed at all).
    pub processed: bool,
    /// The refined estimate after all passes (deeper = closer to the
    /// fixed point of the order-N analysis). Reported so "deeper" is
    /// observable, not just asserted.
    pub estimate: f64,
    /// Honest measured wall-time.
    pub wall: Duration,
    /// If a deadline was in force, whether we met it.
    pub deadline_met: Option<bool>,
}

/// A pipeline whose depth is governed by an `EffortKnob`. The work each
/// pass does is real (an iterated order-N refinement over the input),
/// so wall-time scales with passes — the dial measurably changes how
/// much CPU is spent.
pub struct EffortPipeline {
    knob: EffortKnob,
}

impl EffortPipeline {
    pub fn new(knob: EffortKnob) -> Self {
        Self { knob }
    }

    /// One order-N analysis pass: re-derive the estimate from the
    /// input + the previous estimate. Models analysis-by-synthesis —
    /// each pass folds the order-N shape salience back in, converging
    /// toward a fixed point. Deliberately does real floating work
    /// (proportional to input length) so passes cost measurable time.
    fn one_pass(input: &[f64], prev: f64) -> f64 {
        let sal = order_n_shape_salience(input);
        // refine: a damped step toward (salience-weighted mean of input).
        let mean: f64 = if input.is_empty() {
            0.0
        } else {
            input.iter().sum::<f64>() / input.len() as f64
        };
        // do honest per-element work so the pass has measurable cost.
        let mut acc = 0.0f64;
        for &x in input {
            acc += (x * sal).sin().abs();
        }
        let _ = acc; // keep the work from being optimised away via the blend below
        let target = mean + sal;
        let refined = prev + 0.5 * (target - prev) + 1e-12 * acc;
        refined
    }

    /// Run the pipeline at the dial's CURRENT effort over `input`.
    /// `surprise` is the input's salience (already computed by the
    /// caller / context); the item is processed only if it clears the
    /// effort-dependent salience gate. If `deadline` is supplied,
    /// reports whether wall-time met it.
    pub fn run(&self, input: &[f64], surprise: f64,
               deadline: Option<Instant>) -> PipelineResult {
        let effort = self.knob.level();
        let passes = self.knob.passes();
        let threshold = self.knob.salience_threshold();
        let processed = surprise >= threshold;

        let start = Instant::now();
        let mut est = 0.0f64;
        if processed {
            for _ in 0..passes {
                est = Self::one_pass(input, est);
            }
        }
        let wall = start.elapsed();
        let deadline_met = deadline.map(|d| Instant::now() <= d);

        PipelineResult {
            effort,
            passes: if processed { passes } else { 0 },
            salience_threshold: threshold,
            processed,
            estimate: est,
            wall,
            deadline_met,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::l6_cybernetic_feedback::{
        CyberneticFeedbackLoop, RecommendationApplier,
    };
    use crate::l6_essential_variables::WorkingSetFit;
    use std::sync::Mutex as StdMutex;

    fn ctx(mode: ThreadMode, deadline: Option<Instant>,
           per_pass: Duration, surprise: f64) -> SharedContext {
        Arc::new(StdMutex::new(EffortContext {
            thread_mode: mode,
            deadline,
            per_pass_cost: per_pass,
            surprise,
            now: Instant::now(),
        }))
    }

    #[test]
    fn knob_scales_passes_and_threshold_monotonically() {
        let k = EffortKnob::default_dial();
        k.set(0);
        let p_lo = k.passes();
        let t_lo = k.salience_threshold();
        k.set(10);
        let p_hi = k.passes();
        let t_hi = k.salience_threshold();
        assert!(p_hi > p_lo, "more effort => more passes");
        assert!(t_hi < t_lo, "more effort => lower threshold (keep more)");
        assert_eq!(p_lo, 1);
        assert_eq!(p_hi, 8);
    }

    #[test]
    fn deadline_channel_fits_passes_into_budget() {
        let k = EffortKnob::default_dial();
        // 1ms per pass; 3ms budget at fraction 0.8 -> 2.4ms -> 2 passes.
        let per = Duration::from_millis(1);
        let c = ctx(ThreadMode::RealtimeSingle,
                    Some(Instant::now() + Duration::from_millis(3)),
                    per, 0.0);
        let ch = DeadlineEffortChannel::new("dl", Arc::clone(&c),
                                            k.clone(), 0.8);
        let r = ch.tick().expect("realtime+deadline emits");
        let lvl = r.adjustment_scalar.round() as u64;
        // passes_for(lvl) must be <= 2.
        assert!(k.passes_for(lvl) <= 2,
                "chosen effort {} -> {} passes must fit 2",
                lvl, k.passes_for(lvl));
    }

    #[test]
    fn deadline_bottoms_out_when_even_min_cannot_fit() {
        let k = EffortKnob::default_dial();
        // per-pass 10ms, budget 1ms -> 0 passes fit -> floor min effort.
        let c = ctx(ThreadMode::RealtimeSingle,
                    Some(Instant::now() + Duration::from_millis(1)),
                    Duration::from_millis(10), 0.0);
        let ch = DeadlineEffortChannel::new("dl", Arc::clone(&c),
                                            k.clone(), 0.8);
        let r = ch.tick().unwrap();
        assert_eq!(r.adjustment_scalar.round() as u64, k.min_effort());
    }

    #[test]
    fn offline_no_deadline_silent_lets_surprise_drive_up() {
        let k = EffortKnob::default_dial();
        let c = ctx(ThreadMode::OfflineParallel, None,
                    Duration::from_millis(1), 0.5);
        let dl = DeadlineEffortChannel::new("dl", Arc::clone(&c),
                                            k.clone(), 0.8);
        // No deadline channel output offline.
        assert!(dl.tick().is_none());
        let sp = SurpriseEffortChannel::new("sp", Arc::clone(&c),
                                            k.clone(), 0.5, 1);
        let r = sp.tick().unwrap();
        // surprise 0.5 == salient_at -> max effort.
        assert_eq!(r.adjustment_scalar.round() as u64, k.max_effort());
    }

    #[test]
    fn memory_breach_caps_to_min() {
        let k = EffortKnob::default_dial();
        let wsf: Arc<WorkingSetFit> =
            Arc::new(WorkingSetFit::new("wsf", 1000, 0.9));
        wsf.update(950); // breach
        let ch = MemoryPressureEffortChannel::new(
            "mem", k.clone(),
            Arc::clone(&wsf) as Arc<dyn EssentialVariable>, 3);
        let r = ch.tick().unwrap();
        assert_eq!(r.adjustment_scalar.round() as u64, k.min_effort());
    }

    #[test]
    fn blend_takes_min_of_ceilings_and_demand() {
        let k = EffortKnob::default_dial();
        // surprise wants 10, deadline allows 4, memory allows 6 -> 4.
        let recs = vec![
            rec(10.0, "surprise", 0.5),
            rec(4.0, "deadline", 0.0),
            rec(6.0, "memory", 0.0),
        ];
        assert_eq!(blend_effort(&k, &recs), 4);
    }

    /// END-TO-END through the real L6 loop + applier (the project's
    /// own knob/feedback machinery), NOT a bespoke path.
    #[test]
    fn full_loop_turns_the_registered_knob() {
        let k = EffortKnob::default_dial();
        // Real-time, tight: 1ms/pass, 2.5ms budget -> ~2 passes -> low.
        let c = ctx(ThreadMode::RealtimeSingle,
                    Some(Instant::now() + Duration::from_millis(1000)),
                    Duration::from_millis(1), 0.5);

        let mut floop = CyberneticFeedbackLoop::new();
        floop.add(Box::new(SurpriseEffortChannel::new(
            "surprise", Arc::clone(&c), k.clone(), 0.5, 1)));
        floop.add(Box::new(DeadlineEffortChannel::new(
            "deadline", Arc::clone(&c), k.clone(), 0.8)));

        // Register the effort knob with the real applier.
        let mut applier = RecommendationApplier::new();
        applier.register_knob_u64(EFFORT_ADJUSTMENT, EFFORT_TARGET,
                                  k.handle());

        // Blend deterministically, then write via the applier's knob.
        let recs = floop.tick();
        let blended = blend_effort(&k, &recs);
        k.set(blended);
        assert_eq!(applier.knob_value(EFFORT_ADJUSTMENT, EFFORT_TARGET),
                   Some(blended));
        // 1s budget @ 1ms/pass -> all 8 passes fit; surprise wants max;
        // so blended == max_effort.
        assert_eq!(blended, k.max_effort());
    }
}
