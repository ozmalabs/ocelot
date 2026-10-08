//! FALLBACK TRACE — the engine's record of when it operated on ABSENCE.
//!
//! # Why this exists
//!
//! `VISION_REDUNDANCY_RESULTS.md` Arm 4 measured observability **0/2** and
//! found the marker inventory EMPTY in all 26 probe runs *including baseline*:
//!
//! > "the finding is not 'the markers didn't fire', it is 'there are none to
//! > fire'."
//!
//! Ablating `vision_lateral` drives `channels_on` 51.976 -> 0.000 and every
//! learned gain to exactly 0.0, leaving **no trace in graph state**. The system
//! returns a confident, well-formed, numerically clean zero.
//!
//! The mechanism is right here in the evaluator. `term.rs`'s `Attr` arm ends
//!
//! ```text
//! .get(key).cloned().unwrap_or(Value::None)
//! ```
//!
//! which is `.get('Name','')` — the disease PROTOCOL §1.1 and §12 name — in the
//! engine core. A rule reading an attribute **no rule ever wrote** receives a
//! silent `Value::None`, indistinguishable from a real absent value.
//!
//! # What is recorded
//!
//! Two tallies, keyed by the rule that was running, for the two hypotheses the
//! rung pre-registered head-to-head:
//!
//! * **H1 `DEFAULTED`** — an `Attr` evaluation on a **live node** whose **key
//!   was absent**. "This rule computed on a value nobody wrote."
//! * **H2 `ABSENCE`** — a `Not(Exists(..))` guard that passed because its
//!   source was **empty**. "This rule fired on its absence-branch."
//!
//! # Cost
//!
//! The `DEFAULTED` tally occupies a branch **that is already taken**: the
//! existing code already distinguishes `Some(v)` from `None` via `unwrap_or`.
//! The hit path therefore pays nothing. Only a miss pays, and the reported
//! overhead statistic is the miss FRACTION (`defaulted / attr_total`) — see
//! `VISION_FALLBACK_VOCAB_PREREG.md` §5. No threshold for "too expensive" is
//! set here (§13); the number is measured and reported.
//!
//! `attr_total` (the denominator) IS a hit-path cost, so it is gated behind
//! `set_count_totals`, **off by default**, and switched on only for the
//! overhead measurement itself.
//!
//! # Why this cannot move a verdict (§9)
//!
//! Nothing in this module is ever read by a `Term`. The tallies are
//! write-only from the evaluator's perspective and are drained by an explicit
//! report call. There is no path from a counter back into `evaluate`, so the
//! instrument is incapable of changing any rule's match, any effect, or any
//! value. Byte-identity is structural, not merely tested — and it is tested
//! anyway (bench 200/0, orbit law unmoved).

use crate::sym::Sym;
use rustc_hash::FxHashMap;
use std::cell::{Cell, RefCell};
use std::sync::atomic::{AtomicBool, Ordering};

/// Gate for the hit-path denominator only. OFF by default: counting every
/// `Attr` evaluation is the one part of this instrument that costs anything
/// on the healthy path, and it is needed only to compute the overhead
/// fraction.
static COUNT_TOTALS: AtomicBool = AtomicBool::new(false);

thread_local! {
    /// The rule currently being attempted by `run_rules`, by NAME.
    ///
    /// Name, not index: the redundancy audit established that a seed's rule
    /// INDEX shifts under ablation (withheld rules are never parsed and never
    /// occupy a `RuleIdx`), so an index-keyed tally is not comparable across
    /// ablation arms. `None` outside the rule loop — reflex, production and
    /// bare `substrate.evaluate()` calls are deliberately NOT attributed to
    /// whichever rule happened to run last.
    static CURRENT_RULE: Cell<Option<Sym>> = const { Cell::new(None) };

    /// H1: (rule, attribute-key) -> times that rule read that key off a live
    /// node that did not have it.
    static DEFAULTED: RefCell<FxHashMap<(Sym, Sym), u64>> =
        RefCell::new(FxHashMap::default());

    /// H2: rule -> times a `Not(Exists(..))` guard passed on an EMPTY source.
    static ABSENCE: RefCell<FxHashMap<Sym, u64>> =
        RefCell::new(FxHashMap::default());

    /// Set by every `Exists` evaluation: was the source snapshot empty?
    /// Read by the enclosing `Not` so that "passed because absent" is
    /// distinguished from "passed because the predicate never matched".
    static LAST_EXISTS_EMPTY: Cell<bool> = const { Cell::new(false) };

    /// Overhead denominator / numerator. `ATTR_TOTAL` only moves when
    /// `COUNT_TOTALS` is on; `ATTR_DEFAULT` is always-on and free.
    static ATTR_TOTAL: Cell<u64> = const { Cell::new(0) };
    static ATTR_DEFAULT: Cell<u64> = const { Cell::new(0) };
}

/// Enable/disable the hit-path `Attr` total. Off by default.
pub fn set_count_totals(on: bool) {
    COUNT_TOTALS.store(on, Ordering::Relaxed);
}

pub fn count_totals_enabled() -> bool {
    COUNT_TOTALS.load(Ordering::Relaxed)
}

/// Bind the running rule for attribution. `run_rules` sets this around each
/// rule attempt and clears it afterwards.
#[inline]
pub fn set_current_rule(rule: Option<Sym>) {
    CURRENT_RULE.with(|c| c.set(rule));
}

/// Read the caller thread's attribution so immutable worker phases can carry
/// the same diagnostic context onto their worker threads.
#[inline]
pub fn current_rule() -> Option<Sym> {
    CURRENT_RULE.with(|c| c.get())
}

/// Record an `Attr` read that hit a live node but missed its key.
///
/// Called ONLY from the miss arm of `term.rs`'s `Attr` evaluator, i.e. from a
/// branch the engine already took.
#[inline]
pub fn note_defaulted_read(key: Sym) {
    ATTR_DEFAULT.with(|c| c.set(c.get() + 1));
    let rule = CURRENT_RULE.with(|c| c.get());
    // Unattributed reads (reflexes, productions, bare evaluate) are counted in
    // the totals but not filed against any rule — attributing them to whichever
    // rule ran last would be a fabricated provenance.
    if let Some(r) = rule {
        DEFAULTED.with(|m| *m.borrow_mut().entry((r, key)).or_insert(0) += 1);
    }
}

/// Record an `Attr` evaluation that resolved a live node (hit or miss).
/// No-op unless `COUNT_TOTALS` is on — this is the only hit-path cost.
#[inline]
pub fn note_attr_eval() {
    if COUNT_TOTALS.load(Ordering::Relaxed) {
        ATTR_TOTAL.with(|c| c.set(c.get() + 1));
    }
}

/// Set by `Exists` on every evaluation; consumed by the enclosing `Not`.
#[inline]
pub fn set_last_exists_empty(empty: bool) {
    LAST_EXISTS_EMPTY.with(|c| c.set(empty));
}

#[inline]
pub fn last_exists_empty() -> bool {
    LAST_EXISTS_EMPTY.with(|c| c.get())
}

/// Record a `Not(Exists(..))` that passed because the source was EMPTY.
#[inline]
pub fn note_absence_branch() {
    if let Some(r) = CURRENT_RULE.with(|c| c.get()) {
        ABSENCE.with(|m| *m.borrow_mut().entry(r).or_insert(0) += 1);
    }
}

/// Drain nothing; read the H1 tally as raw `(rule_sym, key_sym, count)`.
pub fn defaulted_raw() -> Vec<(Sym, Sym, u64)> {
    DEFAULTED.with(|m| m.borrow().iter().map(|((r, k), n)| (*r, *k, *n)).collect())
}

/// Read the H2 tally as raw `(rule_sym, count)`.
pub fn absence_raw() -> Vec<(Sym, u64)> {
    ABSENCE.with(|m| m.borrow().iter().map(|(r, n)| (*r, *n)).collect())
}

/// `(attr_total, attr_defaulted)`. `attr_total` is 0 unless `COUNT_TOTALS`
/// was on for the whole run — a 0 denominator means "not measured", never
/// "no reads", and the reader must not divide by it.
pub fn attr_totals() -> (u64, u64) {
    (ATTR_TOTAL.with(|c| c.get()), ATTR_DEFAULT.with(|c| c.get()))
}

/// One worker thread's diagnostics, moved rather than copied so a caller can
/// fold them into its own substrate-local report after immutable parallel
/// evaluation.  Keeping the storage thread-local avoids conflating `Sym`
/// identities from independent substrates sharing the same process.
pub(crate) struct LocalCounts {
    defaulted: FxHashMap<(Sym, Sym), u64>,
    absence: FxHashMap<Sym, u64>,
    attr_total: u64,
    attr_default: u64,
}

pub(crate) fn take_local_counts() -> LocalCounts {
    let defaulted = DEFAULTED.with(|rows| std::mem::take(&mut *rows.borrow_mut()));
    let absence = ABSENCE.with(|rows| std::mem::take(&mut *rows.borrow_mut()));
    let attr_total = ATTR_TOTAL.with(|count| count.replace(0));
    let attr_default = ATTR_DEFAULT.with(|count| count.replace(0));
    LAST_EXISTS_EMPTY.with(|empty| empty.set(false));
    CURRENT_RULE.with(|rule| rule.set(None));
    LocalCounts {
        defaulted,
        absence,
        attr_total,
        attr_default,
    }
}

pub(crate) fn merge_local_counts(counts: LocalCounts) {
    DEFAULTED.with(|rows| {
        let mut rows = rows.borrow_mut();
        for (key, count) in counts.defaulted {
            *rows.entry(key).or_insert(0) += count;
        }
    });
    ABSENCE.with(|rows| {
        let mut rows = rows.borrow_mut();
        for (rule, count) in counts.absence {
            *rows.entry(rule).or_insert(0) += count;
        }
    });
    ATTR_TOTAL.with(|count| count.set(count.get() + counts.attr_total));
    ATTR_DEFAULT.with(|count| count.set(count.get() + counts.attr_default));
}

/// Zero every tally. Used between probe arms so each run is independent.
pub fn reset() {
    DEFAULTED.with(|m| m.borrow_mut().clear());
    ABSENCE.with(|m| m.borrow_mut().clear());
    ATTR_TOTAL.with(|c| c.set(0));
    ATTR_DEFAULT.with(|c| c.set(0));
    LAST_EXISTS_EMPTY.with(|c| c.set(false));
    CURRENT_RULE.with(|c| c.set(None));
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::sym::Interner;

    /// The instrument attributes to the RUNNING RULE, and refuses to attribute
    /// when no rule is running. An unattributed read is counted in the totals
    /// but filed against nobody — inventing a provenance would be worse than
    /// having none.
    #[test]
    fn unattributed_reads_are_counted_but_not_filed() {
        reset();
        let mut it = Interner::default();
        let key = it.intern("h1");

        // No rule bound — a bare evaluate / reflex / production read.
        set_current_rule(None);
        note_defaulted_read(key);
        assert!(defaulted_raw().is_empty(), "must not fabricate a rule");
        assert_eq!(attr_totals().1, 1, "but it IS counted in the totals");

        // Now inside a rule.
        let rule = it.intern("lat_pool");
        set_current_rule(Some(rule));
        note_defaulted_read(key);
        let raw = defaulted_raw();
        assert_eq!(raw.len(), 1);
        assert_eq!(raw[0], (rule, key, 1));
        assert_eq!(attr_totals().1, 2);
        reset();
    }

    /// The H1 tally is per (rule, key), so one rule reading two absent keys is
    /// two distinct witnesses — which is what makes the reader able to name
    /// WHICH attribute nobody wrote.
    #[test]
    fn defaulted_is_keyed_by_rule_and_key() {
        reset();
        let mut it = Interner::default();
        let rule = it.intern("lat_pool");
        let (h1, h2) = (it.intern("h1"), it.intern("h2"));
        set_current_rule(Some(rule));
        note_defaulted_read(h1);
        note_defaulted_read(h1);
        note_defaulted_read(h2);
        let mut raw = defaulted_raw();
        raw.sort();
        assert_eq!(raw.len(), 2);
        let total: u64 = raw.iter().map(|(_, _, n)| n).sum();
        assert_eq!(total, 3);
        reset();
    }

    /// The hit-path denominator is OFF by default. A 0 denominator means "not
    /// measured" and the reader must never divide by it.
    #[test]
    fn totals_are_off_by_default() {
        reset();
        set_count_totals(false);
        note_attr_eval();
        note_attr_eval();
        assert_eq!(attr_totals().0, 0, "hit path must cost nothing by default");
        set_count_totals(true);
        note_attr_eval();
        assert_eq!(attr_totals().0, 1);
        set_count_totals(false);
        reset();
    }

    /// H2's discriminator: a `Not(Exists)` that passes because the source was
    /// EMPTY is a different event from one that passes because the predicate
    /// never matched. Only the first is an absence-branch.
    #[test]
    fn absence_branch_requires_an_empty_source() {
        reset();
        let mut it = Interner::default();
        let rule = it.intern("bh_sum_weights");
        set_current_rule(Some(rule));

        set_last_exists_empty(false);
        assert!(!last_exists_empty());
        // caller would NOT note here

        set_last_exists_empty(true);
        assert!(last_exists_empty());
        note_absence_branch();

        let raw = absence_raw();
        assert_eq!(raw.len(), 1);
        assert_eq!(raw[0], (rule, 1));
        reset();
    }

    /// `reset` genuinely isolates arms — a probe run must not inherit the
    /// previous arm's tally.
    #[test]
    fn reset_isolates_arms() {
        reset();
        let mut it = Interner::default();
        let rule = it.intern("r");
        set_current_rule(Some(rule));
        note_defaulted_read(it.intern("k"));
        note_absence_branch();
        assert!(!defaulted_raw().is_empty());
        reset();
        assert!(defaulted_raw().is_empty());
        assert!(absence_raw().is_empty());
        assert_eq!(attr_totals(), (0, 0));
    }
}
