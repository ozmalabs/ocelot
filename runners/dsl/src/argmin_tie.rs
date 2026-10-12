//! ARGMIN TIE AUDIT — *a comparison can be false, a selection cannot.*
//!
//! # Why this exists
//!
//! `VISION_REFUSAL_CAPACITY_RESULTS.md` §7 measured, by construction:
//!
//! > **`Argmin` returned a winner from FIVE IDENTICAL CANDIDATES** — a set in
//! > which nothing is better than anything else — on all 200 draws. Its null is
//! > reachable only on an EMPTY source.
//!
//! and named the fix in §9.1:
//!
//! > **an `ArgminUnique` sibling: return the null when the extremum is not
//! > unique.** The pattern EXISTS (`PickUnique`); uniqueness is exact equality,
//! > so there is **no constant and nowhere to put one**.
//!
//! `PickUnique` was bound to **185 CONFIGURATION reads and ZERO VERDICT reads**:
//! the seed layer's config hard-fails on ambiguity while its percepts soft-fail.
//!
//! # Two artifacts, deliberately different in scope
//!
//! * **`TermNode::ArgminUnique`** (in `term.rs`) is THE MECHANISM. It is opt-in
//!   by not existing at any site — no seed uses it, so §9 holds trivially.
//! * **This module is THE INSTRUMENT**, and it is broader on purpose: it can
//!   make EVERY existing `Argmin` (and, in `refuse_all`, every `Argmax`) behave
//!   as `ArgminUnique` process-wide, which is the only way to ask *how many
//!   LANDED NUMBERS has an arbitrary tie-break been producing* without
//!   rebinding 117 sites one at a time.
//!
//! # Why process-global atomics, not an `EvalCtx` field
//!
//! Same reason as `selector_audit` (whose shape this follows): an `EvalCtx`
//! field makes coverage depend on every construction site opting in, which is
//! the "instrument that was never wired up" failure mode this tree has been
//! bitten by repeatedly (PROTOCOL §12, §12.1). A global read inside the fold
//! itself is covered by construction.
//!
//! # THE COUNTERS EXIST TO SEPARATE TWO NULLS THAT LOOK IDENTICAL
//!
//! *A dead reader and a perfect refuser produce byte-identical output.*
//! `Argmin` already returns `Value::None` on an EMPTY source. A tie-refusal
//! returns `Value::None` too. **Downstream they are the same bytes**, so the
//! instrument counts them SEPARATELY (`TIES` vs `EMPTIES`) and the positive
//! control asserts both directions: a tie bumps `TIES` and not `EMPTIES`, an
//! empty source bumps `EMPTIES` and not `TIES`, and a UNIQUE extremum bumps
//! neither and returns a real element.
//!
//! # §13
//!
//! Uniqueness is `cmp_value(v, best) == Equal` — EXACT equality. There is no
//! epsilon here and nowhere to put one. If a site ever needs a tolerance on
//! "identical", that is a finding to report, not a number to pick.
//!
//! # Default
//!
//! **OFF** (PROTOCOL §9). When off the entire cost is one `Relaxed` load per
//! selector firing; no counting, no behaviour change, and the refusal branch is
//! unreachable.

use std::collections::BTreeMap;
use std::sync::atomic::{AtomicU64, AtomicU8, Ordering};
use std::sync::{Mutex, OnceLock};

/// `off` — the default. Behaviour byte-identical to the pre-rung engine.
pub const MODE_OFF: u8 = 0;
/// `count` — count firings / ties / empties. **Behaviour UNCHANGED**: a tie
/// still returns the first-encountered extremum, exactly as before. This is the
/// census mode, and it is the one that must reproduce the committed bench.
pub const MODE_COUNT: u8 = 1;
/// `refuse_min` — every `Argmin` behaves as `ArgminUnique`.
pub const MODE_REFUSE_MIN: u8 = 2;
/// `refuse_all` — every `Argmin` AND every `Argmax` refuses a non-unique
/// extremum. Reported separately from `refuse_min`; never conflated.
pub const MODE_REFUSE_ALL: u8 = 3;

static MODE: AtomicU8 = AtomicU8::new(MODE_OFF);
static ENV_READ: OnceLock<()> = OnceLock::new();

/// Selector firings seen while the audit was on (`Argmin` + `Argmax`).
static FIRINGS: AtomicU64 = AtomicU64::new(0);
/// Firings whose extremum was NOT unique (≥2 candidates tied at the extremum).
static TIES: AtomicU64 = AtomicU64::new(0);
/// Firings over an EMPTY source — the null `Argmin` could ALREADY produce.
static EMPTIES: AtomicU64 = AtomicU64::new(0);
/// Firings that actually REFUSED (returned the default/None because of a tie).
/// Distinct from `TIES`: in `count` mode ties are observed but not refused, and
/// in `refuse_min` an `Argmax` tie is observed but not refused. The gap between
/// `TIES` and `REFUSALS` is therefore a MEASURED quantity, never an assumed one.
static REFUSALS: AtomicU64 = AtomicU64::new(0);
/// Firings of the explicit `ArgminUnique` Term itself (never of a coerced
/// `Argmin`), so the Term's own use is separable from the instrument's reach.
static UNIQUE_TERM_FIRINGS: AtomicU64 = AtomicU64::new(0);

/// PER-SITE ATTRIBUTION. Keyed by the selector's own `value` Term rendered to
/// JSON — the one identifier that is stable across arenas and that can be
/// matched back to the exact `seeds/*.json` rule that authored it. Recorded
/// ONLY on a tie (a few hundred events on the whole bench), so the rendering
/// cost is paid on the rare path and never on the fold.
///
/// **This is the answer to "a claim about what code SELECTS is not established
/// by counting the tokens that select it" (§12.1) — the site is read off the
/// firing, not grepped.**
static SITES: Mutex<Option<BTreeMap<String, (u64, u64)>>> = Mutex::new(None);

/// `(selector, value_term_json)` -> `(firings, ties)`.
pub fn note_site(selector: &str, key: &str, tie: bool) {
    let mut g = SITES.lock().unwrap_or_else(|e| e.into_inner());
    let m = g.get_or_insert_with(BTreeMap::new);
    let e = m.entry(format!("{selector}\u{1}{key}")).or_insert((0, 0));
    e.0 += 1;
    if tie {
        e.1 += 1;
    }
}

/// Flattened `(key, firings, ties)` rows.
pub fn sites() -> Vec<(String, u64, u64)> {
    let g = SITES.lock().unwrap_or_else(|e| e.into_inner());
    match &*g {
        None => Vec::new(),
        Some(m) => m.iter().map(|(k, (f, t))| (k.clone(), *f, *t)).collect(),
    }
}

fn init_from_env() {
    ENV_READ.get_or_init(|| {
        if let Ok(v) = std::env::var("OZMA_ARGMIN_UNIQUE") {
            let m = match v.trim().to_ascii_lowercase().as_str() {
                "count" | "1" => MODE_COUNT,
                "refuse_min" | "2" => MODE_REFUSE_MIN,
                "refuse_all" | "3" => MODE_REFUSE_ALL,
                _ => MODE_OFF,
            };
            MODE.store(m, Ordering::Relaxed);
        }
    });
}

/// The one hot-path read. `false` when off — the default.
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

/// Does the instrument coerce THIS fold into refusing? `want_min` selects which
/// selector is being asked about, so `refuse_min` never touches `Argmax`.
#[inline]
pub fn coerces_refusal(want_min: bool) -> bool {
    match mode() {
        MODE_REFUSE_ALL => true,
        MODE_REFUSE_MIN => want_min,
        _ => false,
    }
}

#[inline]
pub fn note_firing() {
    FIRINGS.fetch_add(1, Ordering::Relaxed);
}

#[inline]
pub fn note_tie() {
    TIES.fetch_add(1, Ordering::Relaxed);
}

#[inline]
pub fn note_empty() {
    EMPTIES.fetch_add(1, Ordering::Relaxed);
}

#[inline]
pub fn note_refusal() {
    REFUSALS.fetch_add(1, Ordering::Relaxed);
}

#[inline]
pub fn note_unique_term_firing() {
    UNIQUE_TERM_FIRINGS.fetch_add(1, Ordering::Relaxed);
}

// ---------------------------------------------------------------------------
// NULL-CANDIDATE CENSUS (2026-10-10). Same instrument, same modes, behaviour
// UNCHANGED in every mode: these counters only observe.
//
// `cmp_value` orders `Value::None` below every number (tag 0). So when a
// selector's `value` Term evaluates to None for some candidates (a missing
// attr), Argmin silently treats that cost as -inf and picks it, and Argmax
// silently treats it as the worst. Paper 02c (finite comparison
// specification) requires that an undefined cost make the minimum undefined,
// never silently 0 or infinity. This census measures how often live
// selectors are actually in that state before any behaviour is changed.
//
// * `NULL_MIXED`  -- firings with >=1 None-valued AND >=1 non-None candidate:
//                    the only case where the None ordering decides anything.
// * `NULL_WINS`   -- mixed firings whose RETURNED element's value is None
//                    (the missing cost won).
// * `NULL_ALL`    -- non-empty firings where EVERY candidate is None (the
//                    whole comparison is undefined; the fold returns the
//                    first element).
// ---------------------------------------------------------------------------
static NULL_MIXED: AtomicU64 = AtomicU64::new(0);
static NULL_WINS: AtomicU64 = AtomicU64::new(0);
static NULL_ALL: AtomicU64 = AtomicU64::new(0);
/// `(selector, value_term_json)` -> `(mixed, wins, all_null)`. Recorded only on
/// the null paths, so the rendering cost stays off the ordinary fold.
static NULL_SITES: Mutex<Option<BTreeMap<String, (u64, u64, u64)>>> = Mutex::new(None);

/// One observation of a non-empty selector firing. `n_null` of `n` candidate
/// values were None; `winner_null` says whether the returned element's value
/// was None. Returns whether the firing was on a null path (so the caller
/// renders the site key only then).
pub fn note_nulls(n: usize, n_null: usize, winner_null: bool) -> Option<(bool, bool, bool)> {
    if n == 0 || n_null == 0 {
        return None;
    }
    if n_null == n {
        NULL_ALL.fetch_add(1, Ordering::Relaxed);
        return Some((false, false, true));
    }
    NULL_MIXED.fetch_add(1, Ordering::Relaxed);
    if winner_null {
        NULL_WINS.fetch_add(1, Ordering::Relaxed);
    }
    Some((true, winner_null, false))
}

pub fn note_null_site(selector: &str, key: &str, obs: (bool, bool, bool)) {
    let mut g = NULL_SITES.lock().unwrap_or_else(|e| e.into_inner());
    let m = g.get_or_insert_with(BTreeMap::new);
    let e = m.entry(format!("{selector}\u{1}{key}")).or_insert((0, 0, 0));
    e.0 += obs.0 as u64;
    e.1 += obs.1 as u64;
    e.2 += obs.2 as u64;
}

/// Flattened `(key, mixed, wins, all_null)` rows.
pub fn null_sites() -> Vec<(String, u64, u64, u64)> {
    let g = NULL_SITES.lock().unwrap_or_else(|e| e.into_inner());
    match &*g {
        None => Vec::new(),
        Some(m) => m.iter().map(|(k, (a, b, c))| (k.clone(), *a, *b, *c)).collect(),
    }
}

/// `(mixed, wins, all_null)`.
pub fn null_stats() -> (u64, u64, u64) {
    (
        NULL_MIXED.load(Ordering::Relaxed),
        NULL_WINS.load(Ordering::Relaxed),
        NULL_ALL.load(Ordering::Relaxed),
    )
}

pub fn reset() {
    *SITES.lock().unwrap_or_else(|e| e.into_inner()) = None;
    *NULL_SITES.lock().unwrap_or_else(|e| e.into_inner()) = None;
    NULL_MIXED.store(0, Ordering::Relaxed);
    NULL_WINS.store(0, Ordering::Relaxed);
    NULL_ALL.store(0, Ordering::Relaxed);
    FIRINGS.store(0, Ordering::Relaxed);
    TIES.store(0, Ordering::Relaxed);
    EMPTIES.store(0, Ordering::Relaxed);
    REFUSALS.store(0, Ordering::Relaxed);
    UNIQUE_TERM_FIRINGS.store(0, Ordering::Relaxed);
}

/// `(firings, ties, empties, refusals, unique_term_firings)`.
pub fn stats() -> (u64, u64, u64, u64, u64) {
    (
        FIRINGS.load(Ordering::Relaxed),
        TIES.load(Ordering::Relaxed),
        EMPTIES.load(Ordering::Relaxed),
        REFUSALS.load(Ordering::Relaxed),
        UNIQUE_TERM_FIRINGS.load(Ordering::Relaxed),
    )
}
