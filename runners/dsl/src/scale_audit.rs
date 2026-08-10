//! SCALE AUDIT — split the measured scale wall into COUNTED buckets.
//!
//! # Why this exists
//!
//! `VISION_VIDEO_PROBE_RESULTS.md` (merged `40318951`) measured the wall on real
//! frames — exponent **1.887**, one 1080p frame extrapolating to **164 hours** —
//! and named the cause as *"the PyO3 boundary and then an O(N²) drive"*. That is
//! **two** causes, and there is a plausible third. They have different fixes:
//!
//! | term | what it is | the tool |
//! |---|---|---|
//! | **F** | PyO3/FFI boundary: marshalling, per-item crossings | async Rust-resident collapse |
//! | **C** | genuine pairwise comparison | a proposal net (distillation) |
//! | **R** | redundant recomputation | foveated / incremental evaluation |
//!
//! Distilling a net would be an expensive mistake if half the wall were FFI. So
//! this module counts, and the counts decide.
//!
//! # Why COUNTS and not wall-clock
//!
//! `ENGINE_WINNER_VALUE_RESULTS.md` (merged `62fadd1a`) reported cost as counted
//! operations and **refused** wall-clock, having measured two verdict-identical
//! runs differing by **85 s, 1.66×, on machine load alone**.
//! `VISION_VIDEO_PROBE_RESULTS.md` §0.1 learned the same thing the hard way: its
//! absolute timings were taken under another agent's `pytest` and are
//! contaminated. Counts are load-independent, reproducible to the integer, and
//! attributable by a rule written down before they are taken
//! (`VISION_SCALE_SPLIT_PREREG.md` §3).
//!
//! # Why process-global atomics
//!
//! The `selector_audit.rs` precedent, for the same reason: an `EvalCtx` field
//! would make coverage depend on every construction site opting in — the
//! "instrument that was never wired up" failure this project has been bitten by
//! repeatedly (VISION_PROTOCOL §12, §12.1: eleven inert instruments). A global
//! read inside the hot path itself makes coverage structural rather than
//! remembered.
//!
//! # Default
//!
//! **OFF** (VISION_PROTOCOL §9 — defaults preserve committed results). When off,
//! the entire cost is one `Relaxed` atomic load per instrumented site: no counter
//! is incremented, no epoch set is touched, no allocation occurs.

use crate::term_variants::{NUM_TERM_VARIANTS, TERM_VARIANT_NAMES};
use std::cell::Cell;
use std::sync::atomic::{AtomicBool, AtomicU64, AtomicU8, Ordering};
use std::sync::{Mutex, OnceLock};

const MODE_OFF: u8 = 0;
const MODE_ON: u8 = 1;

static MODE: AtomicU8 = AtomicU8::new(MODE_OFF);
static ENV_READ: OnceLock<()> = OnceLock::new();

// ---------------------------------------------------------------------------
// F — FFI / PyO3 BOUNDARY
//
// Charged ONLY what exists BECAUSE the call came from Python: the crossing, the
// argument unmarshalling, and the return-object construction. The underlying
// graph mutation is NOT charged here — it would happen in a Rust-resident loop
// too (see `GRAPH_WRITES`, which is deliberately outside the three-way split).
// ---------------------------------------------------------------------------

/// Entries into a `#[pymethods]` method from Python — boundary crossings.
static FFI_CALLS: AtomicU64 = AtomicU64::new(0);
/// Per-item units marshalled across: 1 for a scalar call, N for a bulk call.
static FFI_ITEMS: AtomicU64 = AtomicU64::new(0);
/// Python objects CONSTRUCTED to satisfy a return. This is the real marshalling
/// cost: `node()` materialises a full attribute dict (~10 objects) to read one
/// field, which is why the bulk accessors were added in the first place.
static FFI_PYOBJECTS: AtomicU64 = AtomicU64::new(0);

// ---------------------------------------------------------------------------
// C / R — MATCH ENUMERATION
//
// The C/R split is POSITIONAL and CONSERVATIVE (prereg §3): within one EPOCH
// (one Python→Rust call into a rule-running method) a rule's FIRST enumeration
// is charged to C, every LATER enumeration of the same rule in the same epoch to
// R. The mechanism targeted is `run_rules_opts`'s cold path, which enumerates
// EVERY binding, applies ONE, `break`s, and re-enumerates from scratch.
// ---------------------------------------------------------------------------

/// `(src, tgt)` candidate pairs produced by an `extend_each` expansion.
static CAND_ENUM: AtomicU64 = AtomicU64::new(0);
/// …of which reached via the both-unbound full scan of `edges_by_type`.
/// **Global by construction** — the hypothesis-(a) numerator.
static CAND_ENUM_SCAN: AtomicU64 = AtomicU64::new(0);
/// …of which reached by traversal from an already-bound node. **Local.**
static CAND_ENUM_LOCAL: AtomicU64 = AtomicU64::new(0);
/// …of which reached via the R10 `IndexJoinHint` probe. **Indexed.**
static CAND_ENUM_HINTED: AtomicU64 = AtomicU64::new(0);

/// Candidates enumerated on a rule's FIRST enumeration this epoch (→ C).
static CAND_ENUM_FIRST: AtomicU64 = AtomicU64::new(0);
/// Candidates enumerated on a REPEAT enumeration this epoch (→ R).
static CAND_ENUM_REPEAT: AtomicU64 = AtomicU64::new(0);

/// Candidate pairs actually tested in the `extend_each` loop.
static CAND_TESTED: AtomicU64 = AtomicU64::new(0);
/// Candidates discarded by the bound-src/bound-tgt equality filter — enumerated
/// and then thrown away without any substantive test.
static CAND_REJECT_BOUND: AtomicU64 = AtomicU64::new(0);

/// Where-clause evaluations at the leaf (the substantive per-candidate test).
static WHERE_EVALS: AtomicU64 = AtomicU64::new(0);
/// …on a first enumeration (→ C).
static WHERE_EVALS_FIRST: AtomicU64 = AtomicU64::new(0);
/// …on a repeat enumeration (→ R).
static WHERE_EVALS_REPEAT: AtomicU64 = AtomicU64::new(0);
/// Where-clause evaluations that returned false.
static WHERE_REJECTS: AtomicU64 = AtomicU64::new(0);
/// Predicate-pushdown conjunct evaluations (prune before expanding).
static PUSHDOWN_EVALS: AtomicU64 = AtomicU64::new(0);
/// …that pruned the subtree.
static PUSHDOWN_PRUNES: AtomicU64 = AtomicU64::new(0);

/// Bindings that survived every filter and reached `visit` — the SURVIVORS.
/// `LEAF_VISITS / CAND_ENUM` is the selectivity that decides hypothesis (a).
static LEAF_VISITS: AtomicU64 = AtomicU64::new(0);
/// Bindings dropped because two vars collided on one node.
static VAR_COLLISIONS: AtomicU64 = AtomicU64::new(0);

/// `Binding` clones pushed into `run_rules_opts`'s collect-all vector — an
/// allocation count, reported under R.
static BINDINGS_CLONED: AtomicU64 = AtomicU64::new(0);
/// `apply_rule_full(record_undo = true)` applications that did NOT progress and
/// were rolled back — probe-then-rollback waste.
static APPLY_PROBE_ROLLBACKS: AtomicU64 = AtomicU64::new(0);
/// Rule enumerations begun (one per `match_rule_each` from the fixpoint).
static RULE_ENUMERATIONS: AtomicU64 = AtomicU64::new(0);
/// …of which were a REPEAT of a rule already enumerated this epoch.
static RULE_ENUMERATIONS_REPEAT: AtomicU64 = AtomicU64::new(0);

// ---------------------------------------------------------------------------
// OUTSIDE THE SPLIT — the irreducible substrate cost.
//
// Declared in the prereg as charged to NOTHING: a Rust-resident loop would
// perform these too, so folding them into any bucket would flatter that bucket.
// ---------------------------------------------------------------------------

/// Graph attribute writes performed via the Python boundary.
static GRAPH_WRITES: AtomicU64 = AtomicU64::new(0);

// ---------------------------------------------------------------------------
// T — TERM EVALUATION  (VISION_TERM_EVAL_COUNTER_PREREG.md §2)
//
// THE FOURTH TERM, AND THE REASON THIS MODULE WAS BLIND.
//
// Everything above counts GRAPH-LEVEL rule matching. `VISION_VIDEO_PROBE_RERUN_
// RESULTS.md` §3.1 measured what that misses: **a signature is an ATTRIBUTE, not
// a subgraph**, so on the sd/identity workload the matched graph is CONSTANT in
// N, every counter above is byte-identical across an 11.8x range of N, and
// wall-clock grows 13x anyway. The cost is inside Term evaluation. All four of
// that arm's pre-declared gates passed and the answer was still wrong.
//
// TWO FAMILIES, and the split is the whole point:
//
//   term_eval:<Variant>  INVOCATIONS. Charged at term.rs::evaluate's single
//                        dispatch point, so coverage is structural for all 175
//                        variants rather than dependent on per-variant opt-in.
//
//   term_unit:<Variant>  INTERIOR COMPARISON UNITS. Charged by the interior
//                        loops of variants that loop, attributed to the
//                        INNERMOST variant currently evaluating.
//
// Why both: for a leaf (`Plus`, `Attr`) interior work is O(1), so invocations
// ARE the cost and `term_unit` is legitimately zero. For an aggregate
// (`ShapeDecode`) ONE invocation performs O(N*K) work, so an invocation count is
// ITSELF insensitive to N — it would reproduce the exact disease this instrument
// treats, one level finer. The prereg predicts (P1) that `term_eval:ShapeDecode`
// FAILS G5 on the sd axis, and that prediction is part of the design rather than
// a defect discovered afterwards.
// ---------------------------------------------------------------------------

/// Per-variant Term-evaluation invocation counts. Length is the enum's own
/// arity (`term_variants.rs`, generated) — not a chosen constant.
static TERM_EVALS: [AtomicU64; NUM_TERM_VARIANTS] =
    [const { AtomicU64::new(0) }; NUM_TERM_VARIANTS];
/// Per-variant interior comparison units.
static TERM_UNITS: [AtomicU64; NUM_TERM_VARIANTS] =
    [const { AtomicU64::new(0) }; NUM_TERM_VARIANTS];

/// Sentinel for "no Term variant is currently evaluating" — a unit charged with
/// this on the stack has no innermost variant to attribute to and is counted in
/// `term_units_unattributed` rather than silently dropped or misfiled.
const NO_VARIANT: u16 = u16::MAX;

/// Units charged while no Term evaluation was in progress. Should be 0; a
/// non-zero value means an interior loop is reached from outside `evaluate` and
/// the attribution model needs revisiting. Reported, never hidden.
static TERM_UNITS_UNATTRIBUTED: AtomicU64 = AtomicU64::new(0);

thread_local! {
    /// The innermost `TermNode` variant currently being evaluated on THIS
    /// thread. Thread-local rather than atomic: it is a per-evaluation-stack
    /// fact, and the engine evaluates under the GIL, so an atomic would buy
    /// nothing and cost a contended write on the hottest path in the engine.
    static CURRENT_VARIANT: Cell<u16> = const { Cell::new(NO_VARIANT) };
}

/// RAII guard restoring the enclosing variant. A guard rather than a manual
/// restore because `evaluate` has early `return`s inside its match arms — a
/// hand-placed restore would be correct today and silently wrong the first time
/// somebody adds another one.
pub struct VariantGuard(u16);

impl Drop for VariantGuard {
    #[inline]
    fn drop(&mut self) {
        CURRENT_VARIANT.with(|c| c.set(self.0));
    }
}

/// Charge one Term-evaluation invocation to `variant`, and make it the innermost
/// variant for the duration of the returned guard. Returns `None` when the audit
/// is off, so the disabled cost is one relaxed load and no thread-local touch.
#[inline]
pub fn term_eval(variant: u16) -> Option<VariantGuard> {
    if !enabled() {
        return None;
    }
    let i = variant as usize;
    if i < NUM_TERM_VARIANTS {
        bump(&TERM_EVALS[i], 1);
    }
    let prev = CURRENT_VARIANT.with(|c| {
        let p = c.get();
        c.set(variant);
        p
    });
    Some(VariantGuard(prev))
}

/// Charge `n` interior comparison units to the innermost variant currently
/// evaluating. Call from inside an interior loop, ONCE per loop with the count,
/// not once per iteration — an atomic per iteration would dominate the very work
/// it is measuring.
#[inline]
pub fn term_units(n: u64) {
    if !enabled() || n == 0 {
        return;
    }
    let v = CURRENT_VARIANT.with(|c| c.get());
    if v == NO_VARIANT {
        bump(&TERM_UNITS_UNATTRIBUTED, n);
        return;
    }
    let i = v as usize;
    if i < NUM_TERM_VARIANTS {
        bump(&TERM_UNITS[i], n);
    }
}

// ---------------------------------------------------------------------------
// D — DISTINCT `DimInfer` ARGUMENTS  (VISION_DIM_INFER_ARGS_PREREG.md §2)
//
// THE QUESTION THIS ANSWERS. `VISION_IDENTITY_COST_ANATOMY_RESULTS.md` §5.4
// closed with the identity coefficient's one unexplained factor: `I` = 17
// invocations of `DimInfer` per recognising fixpoint, measured INVARIANT across
// 11.8x of N and 16x of K, and 2 on the novel path. Because the recognising
// path spends 8.5x more invocations than the failing one, `I` is what holds
// compute-proportional-to-surprise down to a magnitude of 1.33 even though the
// codebook fix corrected its SIGN. It is either 17 real decodes (irreducible)
// or 16 re-derivations (removable) and no existing counter can tell them apart:
// `term_eval:DimInfer` counts invocations, and every invocation counts the same
// whether or not it recomputes a value already computed.
//
// WHY A SET AND NOT A HASH. The specified test said "a hash of (residual,
// codebook, epoch)". A hash can COLLIDE, and a collision UNDER-counts distinct,
// which biases the measurement toward the re-derivation answer -- the more
// interesting one. This stores the EXACT canonical encoding, so under-counting
// is impossible by construction. The audit is off by default and the tuples are
// tens of KB, so the memory is irrelevant.
//
// WHY TWO SETS. Attempt ORDER genuinely affects `eval_dim_infer`'s answer
// (`best` is selected by `<`, first-seen wins on equality), so the ordered
// encoding is the complete determinant set. But codebook LOAD order is a
// graph-iteration fact that could churn with no semantic change, and encoding
// that churn would OVER-count -- biasing toward "irreducible". The unordered
// form (parts and generators canonically sorted) is therefore a LOWER BOUND,
// and both are reported. Neither is chosen after the fact.
//
// WHAT IS DELIBERATELY NOT IN THE TUPLE: `codebook_epoch`. It does not enter
// `eval_dim_infer` -- it is read by the RULES' `where` guards to decide whether
// to fire, never by the decode. Two invocations with identical decode arguments
// and different epochs return the SAME VALUE, so the second is redundant work
// regardless. Including it would inflate `distinct` for a reason unrelated to
// redundancy. This exclusion makes the "irreducible" verdict HARDER to reach,
// not easier.
// ---------------------------------------------------------------------------

/// Invocations reaching the `DimInfer` argument-recording site. MUST equal
/// `term_eval:DimInfer` (prereg §3.1) — if it does not, the site is not on the
/// path the invocation counter counts and the comparison to `I` is meaningless.
static DIM_INFER_ARG_CALLS: AtomicU64 = AtomicU64::new(0);

/// The distinct ORDERED argument encodings seen. Primary statistic.
static DIM_INFER_ARGS_ORDERED: Mutex<Vec<Vec<u8>>> = Mutex::new(Vec::new());
/// The distinct UNORDERED (canonically sorted) encodings. Lower bound.
static DIM_INFER_ARGS_UNORDERED: Mutex<Vec<Vec<u8>>> = Mutex::new(Vec::new());

/// Record one `DimInfer` invocation's exact argument encoding, in both forms.
///
/// A `Vec<Vec<u8>>` with a linear membership test rather than a `HashSet`: `I`
/// is 17, the sets never exceed a few dozen entries in any measured workload,
/// and a linear scan over a handful of byte vectors keeps the structure exact
/// and trivially auditable. Should a workload ever push this to thousands of
/// distinct tuples, that fact is ITSELF the answer to the reducibility question
/// and the cost of finding it out is irrelevant.
pub fn dim_infer_args(ordered: Vec<u8>, unordered: Vec<u8>) {
    if !enabled() {
        return;
    }
    bump(&DIM_INFER_ARG_CALLS, 1);
    if let Ok(mut s) = DIM_INFER_ARGS_ORDERED.lock() {
        let idx = match s.iter().position(|e| *e == ordered) {
            Some(i) => i,
            None => {
                s.push(ordered);
                s.len() - 1
            }
        };
        if let Ok(mut t) = DIM_INFER_ARG_TRACE.lock() {
            t.push(idx as u32);
        }
    }
    if let Ok(mut s) = DIM_INFER_ARGS_UNORDERED.lock() {
        if !s.iter().any(|e| *e == unordered) {
            s.push(unordered);
        }
    }
}

/// DIAGNOSTIC, NOT A STATISTIC. Which distinct tuple each successive call
/// carried, in call order — so `[0,0,1,2,2,…]` says calls 1–2 shared a tuple,
/// call 3 introduced a second, and so on.
///
/// Added AFTER the headline (`distinct` = 10 against `I` = 17) was measured
/// and committed, so it can explain that number but cannot have shaped it.
/// It exists to answer the "name the mechanism" half of the brief: a
/// redundancy fraction with no account of WHICH invocations repeat is a number
/// nobody can act on.
static DIM_INFER_ARG_TRACE: Mutex<Vec<u32>> = Mutex::new(Vec::new());

/// The call-order trace of distinct-tuple indices.
pub fn dim_infer_arg_trace() -> Vec<u32> {
    DIM_INFER_ARG_TRACE.lock().map(|t| t.clone()).unwrap_or_default()
}

/// The distinct ORDERED encodings themselves, so a diagnostic can diff them
/// and report WHICH determinant moved.
pub fn dim_infer_arg_encodings() -> Vec<Vec<u8>> {
    DIM_INFER_ARGS_ORDERED.lock().map(|s| s.clone()).unwrap_or_default()
}

// ---------------------------------------------------------------------------
// EPOCHS
// ---------------------------------------------------------------------------

/// Python→Rust entries into a rule-running method (`tick` / `run_rules` /
/// `apply_rule_once`). One epoch = one such call.
static EPOCHS: AtomicU64 = AtomicU64::new(0);
/// …of which were `apply_rule_once` — the adapter's `_drive_phase` loop.
static EPOCHS_APPLY_ONCE: AtomicU64 = AtomicU64::new(0);
/// Candidates enumerated inside an `apply_rule_once` epoch. THE CROSS-EPOCH
/// REDUNDANCY MADE EXACT: `_drive_phase` runs `while apply_rule_once(idx): pass`,
/// so it makes ~M calls to apply M bindings and EVERY call re-derives the set
/// from scratch. The prereg keeps this OUT of R (so R stays a lower bound) and
/// requires it be reported SEPARATELY — this counter is that report, measured
/// rather than inferred.
static CAND_ENUM_APPLY_ONCE: AtomicU64 = AtomicU64::new(0);
/// Whether the epoch now open is an `apply_rule_once` epoch.
static IN_APPLY_ONCE: AtomicBool = AtomicBool::new(false);

/// Rules already enumerated in the CURRENT epoch. Touched only when enabled.
static EPOCH_RULES: Mutex<Vec<u32>> = Mutex::new(Vec::new());
/// Whether the enumeration now running is a REPEAT. Set by
/// `begin_rule_enumeration`, read by `extend_each`.
static CURRENT_IS_REPEAT: AtomicBool = AtomicBool::new(false);

fn init_from_env() {
    ENV_READ.get_or_init(|| {
        if let Ok(v) = std::env::var("OZMA_SCALE_AUDIT") {
            let m = match v.trim().to_ascii_lowercase().as_str() {
                "1" | "on" | "true" | "warn" => MODE_ON,
                _ => MODE_OFF,
            };
            MODE.store(m, Ordering::Relaxed);
        }
    });
}

/// The one hot-path read. `false` by default, so the disabled cost is a single
/// relaxed load per instrumented site.
#[inline(always)]
pub fn enabled() -> bool {
    init_from_env();
    MODE.load(Ordering::Relaxed) != MODE_OFF
}

/// Test-facing setter (the harness's §6.1 zero-when-off gate flips this rather
/// than relying on process env, so ON and OFF are measurable in one process).
pub fn set_enabled(on: bool) {
    init_from_env();
    MODE.store(if on { MODE_ON } else { MODE_OFF }, Ordering::Relaxed);
}

#[inline(always)]
fn bump(c: &AtomicU64, n: u64) {
    c.fetch_add(n, Ordering::Relaxed);
}

// --- F ---------------------------------------------------------------------

/// One PyO3 boundary crossing carrying `items` marshalled units and
/// constructing `pyobjects` Python objects for the return.
#[inline]
pub fn ffi(items: u64, pyobjects: u64) {
    if !enabled() {
        return;
    }
    bump(&FFI_CALLS, 1);
    bump(&FFI_ITEMS, items);
    bump(&FFI_PYOBJECTS, pyobjects);
}

/// Graph writes performed under a boundary call — counted, but OUTSIDE the split.
#[inline]
pub fn graph_writes(n: u64) {
    if enabled() {
        bump(&GRAPH_WRITES, n);
    }
}

// --- epochs ----------------------------------------------------------------

/// Open a new epoch: a Python→Rust call into a rule-running method.
pub fn begin_epoch() {
    begin_epoch_kind(false)
}

/// Open a new epoch, recording whether it is an `apply_rule_once` entry.
pub fn begin_epoch_kind(apply_once: bool) {
    if !enabled() {
        return;
    }
    bump(&EPOCHS, 1);
    IN_APPLY_ONCE.store(apply_once, Ordering::Relaxed);
    if apply_once {
        bump(&EPOCHS_APPLY_ONCE, 1);
    }
    if let Ok(mut s) = EPOCH_RULES.lock() {
        s.clear();
    }
    CURRENT_IS_REPEAT.store(false, Ordering::Relaxed);
}

/// Declare that `rule_i`'s bindings are about to be enumerated. Decides whether
/// the enumeration that follows is charged to C (first this epoch) or R (repeat).
pub fn begin_rule_enumeration(rule_i: u32) {
    if !enabled() {
        return;
    }
    bump(&RULE_ENUMERATIONS, 1);
    let repeat = match EPOCH_RULES.lock() {
        Ok(mut s) => {
            if s.contains(&rule_i) {
                true
            } else {
                s.push(rule_i);
                false
            }
        }
        // A poisoned lock must not silently re-classify work. Treat as FIRST —
        // the conservative direction, which understates R (prereg §3).
        Err(_) => false,
    };
    if repeat {
        bump(&RULE_ENUMERATIONS_REPEAT, 1);
    }
    CURRENT_IS_REPEAT.store(repeat, Ordering::Relaxed);
}

#[inline(always)]
fn is_repeat() -> bool {
    CURRENT_IS_REPEAT.load(Ordering::Relaxed)
}

// --- C / R -----------------------------------------------------------------

/// How an `extend_each` expansion reached its candidate set.
pub enum CandPath {
    /// Traversal from an already-bound node (`neighbours` / `in_neighbours`).
    Local,
    /// The R10 `IndexJoinHint` probe.
    Hinted,
    /// The both-unbound full scan of `edges_by_type` — global by construction.
    Scan,
}

/// `n` candidates enumerated by one expansion, via `path`.
#[inline]
pub fn candidates(n: u64, path: CandPath) {
    if !enabled() || n == 0 {
        return;
    }
    bump(&CAND_ENUM, n);
    match path {
        CandPath::Local => bump(&CAND_ENUM_LOCAL, n),
        CandPath::Hinted => bump(&CAND_ENUM_HINTED, n),
        CandPath::Scan => bump(&CAND_ENUM_SCAN, n),
    }
    if is_repeat() {
        bump(&CAND_ENUM_REPEAT, n);
    } else {
        bump(&CAND_ENUM_FIRST, n);
    }
    if IN_APPLY_ONCE.load(Ordering::Relaxed) {
        bump(&CAND_ENUM_APPLY_ONCE, n);
    }
}

#[inline]
pub fn cand_tested() {
    if enabled() {
        bump(&CAND_TESTED, 1);
    }
}

#[inline]
pub fn cand_reject_bound() {
    if enabled() {
        bump(&CAND_REJECT_BOUND, 1);
    }
}

#[inline]
pub fn where_eval(passed: bool) {
    if !enabled() {
        return;
    }
    bump(&WHERE_EVALS, 1);
    if is_repeat() {
        bump(&WHERE_EVALS_REPEAT, 1);
    } else {
        bump(&WHERE_EVALS_FIRST, 1);
    }
    if !passed {
        bump(&WHERE_REJECTS, 1);
    }
}

#[inline]
pub fn pushdown_eval(pruned: bool) {
    if !enabled() {
        return;
    }
    bump(&PUSHDOWN_EVALS, 1);
    if pruned {
        bump(&PUSHDOWN_PRUNES, 1);
    }
}

#[inline]
pub fn leaf_visit() {
    if enabled() {
        bump(&LEAF_VISITS, 1);
    }
}

#[inline]
pub fn var_collision() {
    if enabled() {
        bump(&VAR_COLLISIONS, 1);
    }
}

#[inline]
pub fn binding_cloned() {
    if enabled() {
        bump(&BINDINGS_CLONED, 1);
    }
}

#[inline]
pub fn apply_probe_rollback() {
    if enabled() {
        bump(&APPLY_PROBE_ROLLBACKS, 1);
    }
}

// --- readout ---------------------------------------------------------------

macro_rules! all_counters {
    ($f:ident) => {
        $f! {
            ffi_calls => FFI_CALLS,
            ffi_items => FFI_ITEMS,
            ffi_pyobjects => FFI_PYOBJECTS,
            cand_enum => CAND_ENUM,
            cand_enum_scan => CAND_ENUM_SCAN,
            cand_enum_local => CAND_ENUM_LOCAL,
            cand_enum_hinted => CAND_ENUM_HINTED,
            cand_enum_first => CAND_ENUM_FIRST,
            cand_enum_repeat => CAND_ENUM_REPEAT,
            cand_tested => CAND_TESTED,
            cand_reject_bound => CAND_REJECT_BOUND,
            where_evals => WHERE_EVALS,
            where_evals_first => WHERE_EVALS_FIRST,
            where_evals_repeat => WHERE_EVALS_REPEAT,
            where_rejects => WHERE_REJECTS,
            pushdown_evals => PUSHDOWN_EVALS,
            pushdown_prunes => PUSHDOWN_PRUNES,
            leaf_visits => LEAF_VISITS,
            var_collisions => VAR_COLLISIONS,
            bindings_cloned => BINDINGS_CLONED,
            apply_probe_rollbacks => APPLY_PROBE_ROLLBACKS,
            rule_enumerations => RULE_ENUMERATIONS,
            rule_enumerations_repeat => RULE_ENUMERATIONS_REPEAT,
            graph_writes => GRAPH_WRITES,
            epochs => EPOCHS,
            epochs_apply_once => EPOCHS_APPLY_ONCE,
            cand_enum_apply_once => CAND_ENUM_APPLY_ONCE,
            term_units_unattributed => TERM_UNITS_UNATTRIBUTED,
            dim_infer_arg_calls => DIM_INFER_ARG_CALLS,
        }
    };
}

/// The two distinct-argument cardinalities. Emitted UNCONDITIONALLY (unlike the
/// per-variant rows, which suppress zeros): "the site was never reached" and
/// "the family is missing" must stay distinguishable, and a distinctness gate
/// that silently omits its own row when it reads zero is the inert-instrument
/// failure in a new costume.
fn dim_infer_arg_rows(out: &mut Vec<(String, u64)>) {
    let o = DIM_INFER_ARGS_ORDERED.lock().map(|s| s.len()).unwrap_or(0) as u64;
    let u = DIM_INFER_ARGS_UNORDERED.lock().map(|s| s.len()).unwrap_or(0) as u64;
    out.push(("dim_infer_arg_distinct_ordered".to_string(), o));
    out.push(("dim_infer_arg_distinct_unordered".to_string(), u));
}

/// Per-variant rows for the snapshot: `term_eval:<Variant>` /
/// `term_unit:<Variant>`.
///
/// **Only NON-ZERO cells are emitted.** 175 variants x 2 families is 350 rows,
/// of which a typical workload touches a couple of dozen; emitting the zeros
/// would bury the signal and make every readout O(350) to scan. The totals below
/// are emitted unconditionally, so "the family is present but everything is
/// zero" remains distinguishable from "the family is missing".
fn term_rows(out: &mut Vec<(String, u64)>) {
    let mut evals_total = 0u64;
    let mut units_total = 0u64;
    for i in 0..NUM_TERM_VARIANTS {
        let e = TERM_EVALS[i].load(Ordering::Relaxed);
        let u = TERM_UNITS[i].load(Ordering::Relaxed);
        evals_total += e;
        units_total += u;
        if e != 0 {
            out.push((format!("term_eval:{}", TERM_VARIANT_NAMES[i]), e));
        }
        if u != 0 {
            out.push((format!("term_unit:{}", TERM_VARIANT_NAMES[i]), u));
        }
    }
    out.push(("term_evals_total".to_string(), evals_total));
    out.push(("term_units_total".to_string(), units_total));
}

/// Every counter as `(name, value)`, sorted by name. The harness asserts the
/// prereg §6.4 conservation identities over this.
pub fn snapshot() -> Vec<(String, u64)> {
    macro_rules! collect {
        ($($name:ident => $st:ident,)*) => {{
            let mut v: Vec<(String, u64)> = vec![
                $((stringify!($name).to_string(), $st.load(Ordering::Relaxed)),)*
            ];
            term_rows(&mut v);
            dim_infer_arg_rows(&mut v);
            v.sort_by(|a, b| a.0.cmp(&b.0));
            v
        }};
    }
    all_counters!(collect)
}

/// Zero every counter and close any open epoch.
pub fn reset() {
    macro_rules! zero {
        ($($name:ident => $st:ident,)*) => {{
            $($st.store(0, Ordering::Relaxed);)*
        }};
    }
    all_counters!(zero);
    for i in 0..NUM_TERM_VARIANTS {
        TERM_EVALS[i].store(0, Ordering::Relaxed);
        TERM_UNITS[i].store(0, Ordering::Relaxed);
    }
    CURRENT_VARIANT.with(|c| c.set(NO_VARIANT));
    if let Ok(mut s) = EPOCH_RULES.lock() {
        s.clear();
    }
    CURRENT_IS_REPEAT.store(false, Ordering::Relaxed);
    IN_APPLY_ONCE.store(false, Ordering::Relaxed);
    if let Ok(mut s) = DIM_INFER_ARGS_ORDERED.lock() {
        s.clear();
    }
    if let Ok(mut s) = DIM_INFER_ARGS_UNORDERED.lock() {
        s.clear();
    }
    if let Ok(mut t) = DIM_INFER_ARG_TRACE.lock() {
        t.clear();
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    /// §6.1 — every counter reads zero when the audit is off, and the sites are
    /// inert. A counter that moves while disabled would contaminate every
    /// committed result (PROTOCOL §9).
    #[test]
    fn disabled_counts_nothing() {
        set_enabled(false);
        reset();
        ffi(100, 100);
        candidates(50, CandPath::Scan);
        where_eval(true);
        leaf_visit();
        for (_, v) in snapshot() {
            assert_eq!(v, 0, "a counter moved while the audit was OFF");
        }
        set_enabled(false);
    }

    /// §6.2 — a KNOWN-COUNT workload must produce EXACTLY the known integer.
    /// A counter that has only ever been seen to move has not been tested.
    #[test]
    fn known_counts_are_exact() {
        set_enabled(true);
        reset();
        begin_epoch();
        begin_rule_enumeration(0);
        candidates(7, CandPath::Scan);
        candidates(3, CandPath::Local);
        // Same rule again in the SAME epoch ⇒ every candidate is a REPEAT.
        begin_rule_enumeration(0);
        candidates(7, CandPath::Scan);
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["cand_enum"], 17);
        assert_eq!(m["cand_enum_scan"], 14);
        assert_eq!(m["cand_enum_local"], 3);
        assert_eq!(m["cand_enum_first"], 10);
        assert_eq!(m["cand_enum_repeat"], 7);
        assert_eq!(m["rule_enumerations"], 2);
        assert_eq!(m["rule_enumerations_repeat"], 1);
        // §6.4 conservation, on both axes.
        assert_eq!(m["cand_enum_first"] + m["cand_enum_repeat"], m["cand_enum"]);
        assert_eq!(
            m["cand_enum_scan"] + m["cand_enum_local"] + m["cand_enum_hinted"],
            m["cand_enum"]
        );
        set_enabled(false);
        reset();
    }

    /// §6.1 for the TERM family: the per-variant cells and the interior-unit
    /// cells are inert when the audit is off, and the guard is `None` so no
    /// thread-local is touched either.
    #[test]
    fn term_counters_are_inert_when_disabled() {
        set_enabled(false);
        reset();
        let g = term_eval(0);
        assert!(g.is_none(), "the guard must not be constructed when disabled");
        term_units(1000);
        for (name, v) in snapshot() {
            assert_eq!(v, 0, "{name} moved while the audit was OFF");
        }
        set_enabled(false);
    }

    /// §6.2 for the TERM family: a KNOWN workload produces EXACTLY the known
    /// integers, per variant, and units attribute to the INNERMOST variant.
    #[test]
    fn term_units_attribute_to_the_innermost_variant() {
        set_enabled(true);
        reset();
        {
            let _outer = term_eval(0); // Var
            term_units(5); // -> Var
            {
                let _inner = term_eval(3); // Attr
                term_units(7); // -> Attr, NOT Var
            }
            term_units(2); // guard dropped ⇒ back to Var
        }
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["term_eval:Var"], 1);
        assert_eq!(m["term_eval:Attr"], 1);
        assert_eq!(m["term_unit:Var"], 7, "5 + 2 after the inner guard is dropped");
        assert_eq!(m["term_unit:Attr"], 7);
        assert_eq!(m["term_evals_total"], 2);
        assert_eq!(m["term_units_total"], 14);
        assert_eq!(m["term_units_unattributed"], 0);
        set_enabled(false);
        reset();
    }

    /// A unit charged with no Term evaluation in progress is REPORTED, not
    /// silently dropped and not misfiled onto whichever variant ran last.
    #[test]
    fn units_outside_any_evaluation_are_reported_not_hidden() {
        set_enabled(true);
        reset();
        term_units(9);
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["term_units_unattributed"], 9);
        assert_eq!(m["term_units_total"], 0);
        set_enabled(false);
        reset();
    }

    /// G4 TABLE INTEGRITY. `term_variants.rs` is GENERATED from the enum; if a
    /// variant is added without regenerating, `variant_index()` stops being
    /// exhaustive and this fails. The name table and the counter arrays must
    /// agree in length with the enum's own arity — which is where
    /// `NUM_TERM_VARIANTS` comes FROM (PROTOCOL §13: it falls out).
    #[test]
    fn variant_table_covers_the_enum() {
        assert_eq!(TERM_VARIANT_NAMES.len(), NUM_TERM_VARIANTS);
        assert_eq!(TERM_EVALS.len(), NUM_TERM_VARIANTS);
        assert_eq!(TERM_UNITS.len(), NUM_TERM_VARIANTS);
        // Names are unique — two variants sharing a name would silently merge
        // two cost profiles into one row.
        let uniq: std::collections::HashSet<&str> = TERM_VARIANT_NAMES.iter().cloned().collect();
        assert_eq!(uniq.len(), NUM_TERM_VARIANTS, "duplicate variant name in the table");
        // Every index in range maps to a distinct, non-empty name.
        assert!(TERM_VARIANT_NAMES.iter().all(|n| !n.is_empty()));
    }

    /// Only NON-ZERO per-variant cells are emitted, but the TOTALS are always
    /// present — so "the family is there and everything is zero" stays
    /// distinguishable from "the family is missing", which is exactly the
    /// confusion that lets a missing instrument read as a clean result.
    #[test]
    fn totals_are_always_emitted_even_when_every_cell_is_zero() {
        set_enabled(true);
        reset();
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["term_evals_total"], 0);
        assert_eq!(m["term_units_total"], 0);
        assert!(!m.contains_key("term_eval:Var"), "zero cells are not emitted");
        set_enabled(false);
        reset();
    }

    /// A NEW epoch re-arms the first/repeat classification: the same rule
    /// enumerated in a later epoch is a FIRST again, because the graph it reads
    /// may have changed between Python calls.
    #[test]
    fn epoch_rearms_first_repeat() {
        set_enabled(true);
        reset();
        begin_epoch();
        begin_rule_enumeration(4);
        candidates(5, CandPath::Scan);
        begin_epoch();
        begin_rule_enumeration(4);
        candidates(5, CandPath::Scan);
        let m: std::collections::HashMap<String, u64> = snapshot().into_iter().collect();
        assert_eq!(m["cand_enum_first"], 10, "a new epoch must re-arm FIRST");
        assert_eq!(m["cand_enum_repeat"], 0);
        assert_eq!(m["epochs"], 2);
        set_enabled(false);
        reset();
    }
}
