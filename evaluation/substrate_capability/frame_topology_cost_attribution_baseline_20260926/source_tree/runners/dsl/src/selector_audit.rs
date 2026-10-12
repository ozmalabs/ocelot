//! SELECTOR AUDIT — record the WINNER'S OWN VALUE.
//!
//! # Why this exists
//!
//! `ENGINE_ARGMAX_DETERMINISM_RESULTS.md` (merged `fc95c326`) investigated 272
//! irreproducible rows in which one `Argmax` returned a single constant node for
//! an entire substrate, while — in the SAME rule application — the preceding
//! `MaxOver` and the following `Count(Filter(Eq(·, max)))` were **both correct
//! on 272/272 rows**. Six mechanisms were excluded on evidence; the fault did
//! not reproduce in 1 088 000 probes; the cause is UNESTABLISHED.
//!
//! Its §6 actionable output is this module:
//!
//! > **Record the WINNER'S OWN VALUE, not just the extremum and the tie count.**
//! > A tie count proves the selection was unambiguous *according to the
//! > selector*. It cannot detect a selector that disagrees with its own value
//! > Term, because both numbers are then computed by the thing under suspicion.
//!
//! The governing principle, which is the whole design:
//!
//! > **A DIAGNOSTIC MUST NOT BE COMPUTED BY THE COMPONENT IT CHECKS.**
//!
//! So: after a selector fold picks `(best_value, best_element)`, the EVALUATOR
//! re-binds the selector's own variable to `best_element` and re-evaluates the
//! selector's own `value` Term. `winner_value != best_value` is then a LOCAL,
//! SINGLE-ROW contradiction — no replay, no statistics, and no reliance on any
//! other quantity the same selector produced.
//!
//! # Why process-global atomics and not an `EvalCtx` field
//!
//! `EvalCtx` is constructed at many call sites. An `EvalCtx` field would make
//! coverage depend on every one of them opting in — which is precisely the
//! "instrument that was never wired up" failure mode this project has been
//! bitten by repeatedly (VISION_PROTOCOL §12, §12.1: nine inert instruments,
//! and a provenance gate green for 51 commits because its trigger never arose).
//! A global is read inside the fold helpers themselves, so EVERY firing passes
//! the check by construction and coverage is structural rather than remembered.
//!
//! Atomics (not a `Cell`/`RefCell`) because the collapse loop is intended to go
//! asynchronous, and this instrument is meant to survive that. See
//! `ENGINE_WINNER_VALUE_PREREG.md` §6.3 for the soundness caveat: the check is
//! sound under a QUIESCENT graph. Under a parallel monotone phase a value Term
//! reading a growing set could legitimately change between the fold and the
//! re-check, which would be a FALSE POSITIVE. Making this a live race detector
//! during parallel evaluation requires the re-check to be taken under the same
//! graph snapshot as the fold. That is a design constraint on the concurrency
//! work, recorded here so it is inherited rather than rediscovered.
//!
//! # Default
//!
//! **OFF** (VISION_PROTOCOL §9 — defaults preserve committed results). When off,
//! the entire cost is one `Relaxed` atomic load per selector firing: no element
//! is cloned, no Term is re-evaluated, and the fault injector below is
//! UNREACHABLE.

use std::sync::atomic::{AtomicBool, AtomicU64, AtomicU8, Ordering};
use std::sync::{Mutex, OnceLock};

/// `off` — no check (the default).
pub const MODE_OFF: u8 = 0;
/// `warn` — check, count, retain the first contradiction, keep going.
pub const MODE_WARN: u8 = 1;
/// `strict` — check, and panic on the first contradiction with the full row.
pub const MODE_STRICT: u8 = 2;

static MODE: AtomicU8 = AtomicU8::new(MODE_OFF);
static ENV_READ: OnceLock<()> = OnceLock::new();

/// Selector firings that were audited (one extra `value` evaluation each).
static FIRINGS: AtomicU64 = AtomicU64::new(0);
/// Candidate `value` evaluations performed by the folds themselves, counted
/// only while auditing. The exact cost fraction is `FIRINGS / CANDIDATES`
/// — i.e. `1/N` for a selector over `N` candidates. This is a COUNTED
/// overhead, not a wall-clock one: deterministic, load-independent, and it
/// FALLS OUT of the candidate-set sizes the seeds actually produce
/// (VISION_PROTOCOL §13 — no threshold is set here).
static CANDIDATES: AtomicU64 = AtomicU64::new(0);
/// Firings skipped because the value subtree is effectful / re-entrant
/// (`UseTool`, `ReadFile`). Re-evaluating those would DOUBLE-FIRE a side
/// effect, which is a behaviour change, which §9 forbids. Counted, never
/// silent — a coverage gap must be a number.
static SKIPPED_EFFECTFUL: AtomicU64 = AtomicU64::new(0);
/// Firings where the winner's own value DISAGREED with the recorded extremum.
static DISAGREEMENTS: AtomicU64 = AtomicU64::new(0);
/// Firings where the fold saw no candidates at all (the `default` path).
static EMPTY: AtomicU64 = AtomicU64::new(0);

static FIRST_ROW: Mutex<Option<String>> = Mutex::new(None);

/// FAULT INJECTION — the positive control (`ENGINE_WINNER_VALUE_PREREG.md` §2.3).
///
/// When set, a selector fold returns the FIRST element it encountered regardless
/// of its value. That is EXACTLY the §4.2 anomaly's measured signature: a
/// constant winner (`fractal`, the lowest-id candidate — the first the fold sees,
/// because `make_frozenset` sorts by node id) while the neighbouring
/// compositions stayed correct.
///
/// **A detector that has never fired has not been tested.** This exists so the
/// instrument can be demonstrated red-then-green rather than argued for.
///
/// SAFETY PROPERTY: this flag is read ONLY inside the audit branch, so it is
/// unreachable when the audit is off (the default). It is not reachable from any
/// seed, Term or rule — only from the explicit test-facing setter below.
static FAULT_INJECT_FIRST: AtomicBool = AtomicBool::new(false);

fn init_from_env() {
    ENV_READ.get_or_init(|| {
        if let Ok(v) = std::env::var("OZMA_SELECTOR_AUDIT") {
            let m = match v.trim().to_ascii_lowercase().as_str() {
                "1" | "warn" | "on" | "true" => MODE_WARN,
                "2" | "strict" => MODE_STRICT,
                _ => MODE_OFF,
            };
            MODE.store(m, Ordering::Relaxed);
        }
    });
}

/// The one hot-path read. `false` when the audit is off — which is the default,
/// so the disabled cost is a single relaxed load per selector firing.
#[inline(always)]
pub fn enabled() -> bool {
    init_from_env();
    MODE.load(Ordering::Relaxed) != MODE_OFF
}

#[inline]
pub fn mode() -> u8 {
    init_from_env();
    MODE.load(Ordering::Relaxed)
}

pub fn set_mode(m: u8) {
    init_from_env();
    MODE.store(m, Ordering::Relaxed);
}

/// Enable/disable the fault injector. Only meaningful while the audit is on.
pub fn set_fault_inject_first(on: bool) {
    FAULT_INJECT_FIRST.store(on, Ordering::Relaxed);
}

#[inline]
pub fn fault_inject_first() -> bool {
    FAULT_INJECT_FIRST.load(Ordering::Relaxed)
}

#[inline]
pub fn note_candidates(n: u64) {
    CANDIDATES.fetch_add(n, Ordering::Relaxed);
}

#[inline]
pub fn note_firing() {
    FIRINGS.fetch_add(1, Ordering::Relaxed);
}

#[inline]
pub fn note_skipped_effectful() {
    SKIPPED_EFFECTFUL.fetch_add(1, Ordering::Relaxed);
}

#[inline]
pub fn note_empty() {
    EMPTY.fetch_add(1, Ordering::Relaxed);
}

/// Record a winner-value / recorded-extremum contradiction on ONE firing.
///
/// In `strict` mode this panics with the whole row, which is the point: the
/// determinism arc cost an arc-long investigation because the rows recorded the
/// winner's NAME and the maximum SCORE but never the winner's OWN score.
pub fn note_disagreement(
    selector: &str,
    winner: &str,
    winner_value: &str,
    recorded_extremum: &str,
    n_candidates: usize,
) {
    DISAGREEMENTS.fetch_add(1, Ordering::Relaxed);
    let row = format!(
        "SELECTOR/VALUE CONTRADICTION in `{selector}`: the fold returned \
         winner={winner}, but re-evaluating the selector's OWN value Term on \
         that winner gives {winner_value} while the fold recorded the extremum \
         as {recorded_extremum} (over {n_candidates} candidates). \
         These two numbers are computed by DIFFERENT things — the recorded \
         extremum by the selector under suspicion, the winner value by the \
         evaluator re-running the seed author's own Term on the returned node \
         — so this is a single-row, replay-free contradiction. See \
         ENGINE_ARGMAX_DETERMINISM_RESULTS.md §6."
    );
    {
        let mut slot = FIRST_ROW.lock().unwrap_or_else(|e| e.into_inner());
        if slot.is_none() {
            *slot = Some(row.clone());
        }
    }
    if mode() == MODE_STRICT {
        panic!("{row}");
    }
}

pub fn reset() {
    FIRINGS.store(0, Ordering::Relaxed);
    CANDIDATES.store(0, Ordering::Relaxed);
    SKIPPED_EFFECTFUL.store(0, Ordering::Relaxed);
    DISAGREEMENTS.store(0, Ordering::Relaxed);
    EMPTY.store(0, Ordering::Relaxed);
    *FIRST_ROW.lock().unwrap_or_else(|e| e.into_inner()) = None;
}

/// `(firings, candidates, skipped_effectful, disagreements, empty, first_row)`.
pub fn stats() -> (u64, u64, u64, u64, u64, Option<String>) {
    (
        FIRINGS.load(Ordering::Relaxed),
        CANDIDATES.load(Ordering::Relaxed),
        SKIPPED_EFFECTFUL.load(Ordering::Relaxed),
        DISAGREEMENTS.load(Ordering::Relaxed),
        EMPTY.load(Ordering::Relaxed),
        FIRST_ROW.lock().unwrap_or_else(|e| e.into_inner()).clone(),
    )
}
