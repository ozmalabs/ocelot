//! `SynthEnumerate` — the bottom-up enumerative synthesizer as a pure
//! Rust Term (PROGRAM_SYNTHESIS_PLAN.md §4-P4: "Migrate generator.py's
//! enumerative search into a Rust `SynthEnumerate` Term (MDL-ordered,
//! observational-equivalence pruning, budgeted) callable from
//! `ps_propose`'s fallback rung").
//!
//! FAITHFUL PORT of `domains/generator.py::synthesize` (the unguided
//! path), following the module-per-engine precedent (`shape_decode.rs`,
//! `prog_eval.rs`): the engine lives here, `term.rs` has a one-line
//! dispatch arm, the output is a Dict with a `field` selector.
//!
//! ## Contract
//!
//! `SynthEnumerate{examples, ops, consts, exclude, max_size,
//! max_candidates, saturate_k, field}` →
//! `Dict{found, term, term_str, size, tested, distinct, pruned_equiv,
//! inadmissible, saturated, halt_reason}`.
//!
//! - **examples** evaluates to a list (Tuple) of rows, each a
//!   `Dict{inputs: Dict{var: value}, output: value}` — the SPEC. A
//!   malformed spec → `found:false, halt_reason:"invalid_examples"`,
//!   never a panic. **Q1 widening:** the OUTPUT is no longer numeric-
//!   only — str/bool/float/None/Dict/Tuple/Set outputs are all valid
//!   spec targets now (generator.py's own int/float-only floor is
//!   superseded here; see `SigVal`/`canon` below). Only the row SHAPE
//!   is still validated.
//! - **ops** (optional) evaluates to a list of op-name strings — THE
//!   OP-INVENTORY CONTRACT: the caller says which primitives may
//!   compose (the held-Terms discipline). The kernel table is
//!   generator.py's arithmetic set (Plus, Times, Minus, Div, Min, Max,
//!   Abs, Neg, Gt, Lt, Gte, Lte, Eq, And, Or, Not, IfThenElse) PLUS two
//!   Q1 string-composition ops (Concat → `StringConcat`, CaseFold →
//!   Python `str.lower()`) reusing EXISTING DSL string Terms — same
//!   kernel-table discipline, not a new mechanism. Names outside the
//!   table are IGNORED (generator.py's `if name in table` — parity,
//!   not silent failure: the counters expose an empty effective set as
//!   instant saturation). Absent/None → a TYPED default: a spec whose
//!   every variable value AND output is string-shaped uses
//!   `DEFAULT_STR_OPS` (Concat, CaseFold, Eq, IfThenElse); every other
//!   spec uses generator.py's own `DEFAULT_OPS` (Plus, Times, Minus,
//!   Div, Min, Max, Abs, Neg, Gt, Lt, Eq, IfThenElse) — enumeration
//!   order is part of the port either way. An explicit `ops` always
//!   overrides the typed default.
//! - **consts** (optional) evaluates to a list of literal leaves;
//!   absent → generator.py's `(0, 1, 2, -1)`. As in the source,
//!   integer-valued spec outputs are appended (so `x*x + 1` can find
//!   the `1`), deduplicated, order preserved. **Q1 addition:** every
//!   whole string value observed in the spec (any row's inputs or
//!   output) PLUS every distinct character in any of them is also
//!   appended — spec-derived only, never a global alphabet, bounded
//!   naturally by the spec's own content (no separate cap).
//! - **exclude** (optional, Q1 — the P7-B repair lever) evaluates to a
//!   list of Term-JSON strings: candidates a caller has already
//!   REFUTED (e.g. failed a held-out row in a prior round). Each
//!   excluded term's signature over THESE examples is pre-seeded into
//!   the equivalence-pruning set before search begins, so no later
//!   candidate with the same behaviour — even a syntactically
//!   different one, even an auto-appended constant that would
//!   otherwise resurrect it — can be proposed again. Parsed by a
//!   minimal LOCAL reader (`parse_excluded_term`, scoped to this
//!   module's own Var/Lit/OP_TABLE grammar — see its doc comment for
//!   why `jsonio::term_from_json` isn't reused); a malformed entry is
//!   skipped, never fatal.
//! - **Budgets are COUNTS, never a wall clock** (the in-frame integer
//!   discipline). `max_size` (≤0 → 9) bounds term size exactly as in
//!   generator.py; `max_candidates` (≤0 → 200_000) REPLACES
//!   generator.py's `timeout_s`: it bounds the number of candidate
//!   terms *evaluated* (`tested`); exhaustion → `found:false,
//!   halt_reason:"budget"` with honest counters. `saturate_k` (≤0 → 3)
//!   is the saturation window.
//! - **Pure.** No substrate mutation, no I/O. Candidates are built in
//!   a scratch arena and evaluated through the standard `evaluate()`
//!   with ONLY the example bindings in scope — DSL semantics govern
//!   (Div-by-zero → 0.0 etc.), identically on both engines, which is
//!   what makes the generator.py parity gate exact.
//!
//! ## The algorithm (generator.py, line for line where it matters)
//!
//! - SEARCH over the production space = enumerate Term-trees from the
//!   op inventory, by increasing SIZE (MDL/Occam: the shortest program
//!   fitting the spec is returned first). Size = 1 (the node) + sum of
//!   child sizes; leaves (Var/Lit) are size 1.
//! - OBSERVATIONAL-EQUIVALENCE pruning: a term's signature is its
//!   tuple of outputs on the spec inputs, type-aware exactly as
//!   generator.py's `_canon` (bool ≠ 1; 1 == 1.0; NaN folded to a
//!   token) PLUS Q1's widened cases (exact string equality; a stable
//!   recursive repr for None/Dict/Tuple/Set/Node). One term per
//!   distinct behaviour is kept as a building block.
//! - TARGET match is checked FIRST on a new signature (numeric,
//!   type-agnostic, 1e-9 tolerance) — generator.py's register order.
//! - SATURATION halt: if the distinct-behaviour count has not grown
//!   over the last `saturate_k` sizes, no new behaviours are reachable
//!   → halt honestly.
//!
//! Registration is interleaved with production here (generator.py
//! collects `produced_this_size` first, then registers). The orders
//! are IDENTICAL: production at size s reads only `by_size[< s]`, and
//! registration appends only to `by_size[s]` — no candidate can see a
//! sibling of its own size in either version. Interleaving is what
//! lets `max_candidates` bind promptly.
//!
//! ## Deliberate divergences from generator.py (documented, registered)
//!
//! - `timeout_s` → `max_candidates` (count, not clock — see above).
//! - `guide` / `guide_select` / `guide_beam` / `exclude` /
//!   `return_trace` are NOT ported: they are Python callables (host
//!   hooks), not graph data. This Term is the unguided core;
//!   generator.py's default (`guide=None, exclude=None`) "reproduces
//!   the unguided behaviour EXACTLY" — that unguided behaviour is what
//!   lives here. `beam` (the legacy arbitrary width cap) is likewise
//!   dropped: it is dead weight the guided path superseded.
//! - generator.py's "bc" (commutative) op kind generated BOTH (a,b)
//!   and (b,a) anyway (its same-size dedup was an explicit `pass` —
//!   the collapse was always left to signature pruning). The port
//!   therefore has one Binary kind; behaviour is identical.
//! - generator.py raises on a non-numeric spec output; this port
//!   WIDENS the domain instead (Q1) rather than reproducing the raise
//!   — str/bool/float/None/Dict/Tuple/Set are all valid targets now.
//!   A candidate ERROR (Python exception) still has no Rust twin — the
//!   plain DSL `evaluate()` this engine drives has no error channel
//!   distinct from an ordinary Value, so `inadmissible` (generator.py's
//!   bucket for both errors and non-scalar leakage) is now structurally
//!   unreachable; kept in the output Dict for wire back-compat only.
//!
//! ## Arc4-S4 widening: list/iteration composition (search reach)
//!
//! S0-B's measurement (`PROGRAM_SYNTHESIS_ARC4_S0B_NOTES.md` §4) found the
//! DOMINANT `gapped:enumerate_failed` sub-population (85/139 = 61.2%) was
//! not a missing-emitter-lever problem at all: `emit_prog_ir` already
//! returns `ok:true` for these tasks, but `SynthEnumerate`'s own search
//! could never REACH a solution because its op inventory was flat scalar/
//! string arithmetic with no way to iterate, reduce, filter or map a
//! list-valued variable. This section closes that gap by reusing EXISTING
//! DSL Terms (`Count`, `Sum`, `MaxOver`, `MinOver`, `IndexAt`, `Last`,
//! `Fold`, `FilterList`, `MapList` — all already pure, already usable over
//! an arbitrary `Value` with no graph dependency) as ELEVEN new composable
//! op names:
//!
//! - **ListUnary reductions** (`Len`, `SumList`, `MaxList`, `MinList`,
//!   `MaxLenOver`, `MinLenOver`, `First`, `LastElem`, `JoinList`): one
//!   fixed Term shape each, drawing their `source` ONLY from a NEW
//!   type-tracked index (`Search::list_by_size`, populated purely
//!   additively alongside the existing `by_size` — see `register`) so a
//!   scalar-only spec never wastes budget enumerating `Count` over a
//!   number. A reduction's SCALAR output is ALSO stored in the ordinary
//!   `by_size` pool, so it composes further with the pre-existing
//!   arithmetic ops for free (e.g. `MaxList(xs) - MinList(xs)` for a
//!   "max absolute difference" spec).
//! - **ListHigherOrder** (`FilterList`, `MapList`): source drawn from
//!   `list_by_size`, composed against a small, BOUNDED, precomputed
//!   template pool (`filter_templates_by_size` / `map_templates_by_size`)
//!   over ONE locally-fabricated bound variable (`__item`, the
//!   `local_sym` precedent) — comparisons/arithmetic against every
//!   spec-derived numeric const and every scalar spec variable, plus a
//!   `Count`/`CaseFold`/`IndexAt` handful of per-element transforms. This
//!   is the "bounded inner-expression grammar" the arc-4 plan names as a
//!   candidate widening, not a full recursive sub-search — templates are
//!   built ONCE per call (never counted toward `tested`/budget, same
//!   discipline as `exclude` preseeding) and reused as shared subtrees
//!   across every source candidate, exactly like existing binary-op
//!   children sharing.
//!
//! These op names are ONLY ever present in `op_list` when (a) the caller
//! explicitly requests them, or (b) the spec is LIST-SHAPED (any variable
//! or the output is list-valued across every row) AND the caller supplied
//! no explicit `ops` — a third typed default alongside `DEFAULT_OPS`/
//! `DEFAULT_STR_OPS`. Every existing scalar/string spec's `op_list` is
//! therefore BYTE-IDENTICAL to before this widening — the parity gate.
//!
//! ## Arc6 tier-0 widening: THE GAP IS PROPOSAL, NOT EXECUTION
//!
//! `PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md` §2 measured the fact this
//! section acts on: `ProgEval` — the evaluator every accepted program is
//! actually run on — ALREADY executes `sorted`, `split`, `replace`, `join`,
//! `capitalize`, `count`, `enumerate`, `reversed`, `round`, `str`, `int`,
//! strided/negative slicing, string subscripting, comprehensions and
//! `dict.items()`, while this module's 30 op names contained NONE of them.
//! The pipeline could already RUN most of the residual; it could not
//! PROPOSE it. That is an op-table gap, not an engine gap.
//!
//! Tier 0 is the cheapest cut of that gap and is the arc-4 S4 shape
//! exactly — **eight units, ZERO new `TermNode` variants** (§4.1/§9):
//!
//! - `op:TupleOf` — the shipped `Vec` Term as a binary op.
//! - `op:ProdList` — the shipped `Prod` Term; the `SumList` twin.
//! - `op:ConcatList` — LIST concat as `Fold`+`Append`, built exactly the
//!   way `JoinList` builds STRING concat (`Cat` is string concat and emits
//!   Rust debug reprs on lists — measured, so it is not the route).
//! - `op:ArgMaxLenOver` — the ARG-twin of the shipped `MaxLenOver`.
//! - `tmpl:item_in_listvar` — `item (not) in <list var>`, over the shipped
//!   `In` Term.
//! - `tmpl:len_item_vs_var` — the missing cell of the pool's own 2x2:
//!   `len(item)` against a VARIABLE, not only a constant.
//! - `tmpl:nested_reduction` — a quantifier over the bound item inside a
//!   predicate (S4 §4.4's named seam), with the inner body drawn from the
//!   SAME per-element grammar the MapList pool already uses.
//! - `fix:StringAsSequence` — not here but in `term.rs`: `Count`/`IndexAt`/
//!   `Last`/`In` accept a string. Four shipped Terms with the right names
//!   and no string type coverage (`Count("abc") -> 0` etc., all measured).
//!
//! All four new op names are APPENDED to `LIST_EXTRA_OPS`, never
//! interleaved, and every one of them sources from `list_by_size`
//! (`TupleOf` excepted — it is an ordinary Binary over the general pool).
//! A scalar-only or string-only spec's `op_list` is therefore BYTE-
//! IDENTICAL to before this widening, exactly as it was after S4.
//!
//! ## Output `term`
//!
//! The winning candidate is emitted as a Term-JSON string
//! (`Surface(Text)`) in exactly the wire form `jsonio::term_from_json`
//! parses — directly usable by the Python side (`json.loads` →
//! `substrate.evaluate(dict, env)` / `add_term_subgraph` / render).
//! Serialization is LOCAL (never through `Interner::resolve`): variable
//! names are carried in this module's own Sym→String table, so a
//! Surface-keyed input var (locally fabricated Sym, the shape_decode.rs
//! precedent) can never panic the interner.

use std::sync::Arc;

use rustc_hash::{FxHashMap, FxHashSet};
use smallvec::SmallVec;

use crate::sym::{Interner, Sym};
use crate::term::{evaluate, Env, EvalCtx, TermArena, TermIdx, TermNode};
use crate::value::{cmp_value, SurfaceKind, Value};

const DEFAULT_MAX_SIZE: i64 = 9;
const DEFAULT_MAX_CANDIDATES: i64 = 200_000;
const DEFAULT_SATURATE_K: i64 = 3;

/// generator.py's DEFAULT_OPS, in order (enumeration order is part of
/// the port).
const DEFAULT_OPS: &[&str] = &[
    "Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg",
    "Gt", "Lt", "Eq", "IfThenElse",
];

fn surf(s: &str) -> Value {
    Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes()))
}

fn surf_string(s: String) -> Value {
    Value::Surface(SurfaceKind::Text, Arc::from(s.into_bytes().into_boxed_slice()))
}

// ---------------------------------------------------------------------------
// Op table — generator.py's `_op_table`, arity only (see module docs on
// why "bc" collapses into Binary).
// ---------------------------------------------------------------------------

#[derive(Clone, Copy, PartialEq, Eq)]
enum OpKind {
    Unary,
    Binary,
    Ternary,
    /// Arc4-S4: source drawn from `list_by_size` only, one fixed shape
    /// per name (`Len`/`SumList`/`MaxList`/`MinList`/`MaxLenOver`/
    /// `MinLenOver`/`First`/`LastElem`/`JoinList`).
    ListUnary,
    /// Arc4-S4: `FilterList` — source from `list_by_size`, predicate from
    /// `filter_templates_by_size`.
    ListFilter,
    /// Arc4-S4: `MapList` — source from `list_by_size`, value template
    /// from `map_templates_by_size`.
    ListMap,
    /// Arc6 tier-0: BOTH children drawn from `list_by_size` (`ConcatList`).
    ListBinary,
}

const OP_TABLE: &[(&str, OpKind)] = &[
    ("Plus", OpKind::Binary),
    ("Times", OpKind::Binary),
    ("Minus", OpKind::Binary),
    ("Div", OpKind::Binary),
    ("Min", OpKind::Binary),
    ("Max", OpKind::Binary),
    ("Abs", OpKind::Unary),
    ("Neg", OpKind::Unary),
    ("Gt", OpKind::Binary),
    ("Lt", OpKind::Binary),
    ("Gte", OpKind::Binary),
    ("Lte", OpKind::Binary),
    ("Eq", OpKind::Binary),
    ("And", OpKind::Binary),
    ("Or", OpKind::Binary),
    ("Not", OpKind::Unary),
    ("IfThenElse", OpKind::Ternary),
    // --- Q1: string-shaped composition (the enumerator's own grammar
    // is a plain DSL-Term search, not a ProgEval-with-oracles search —
    // these two reuse EXISTING DSL string Terms, the same kernel-table
    // discipline as every arithmetic op above). ---
    ("Concat", OpKind::Binary),   // -> StringConcat{parts:[a,b]}
    ("CaseFold", OpKind::Unary),  // -> CaseFold{text} (Python str.lower())
    // --- Arc4-S4: list/iteration composition (search reach) — reuses
    // EXISTING pure DSL Terms (Count/Sum/MaxOver/MinOver/IndexAt/Last/
    // Fold/FilterList/MapList), never a new Term variant. See the module
    // doc section "Arc4-S4 widening" above. ---
    ("Len", OpKind::ListUnary),         // -> Count{source}
    ("SumList", OpKind::ListUnary),     // -> Sum{source, item, Var(item)}
    ("MaxList", OpKind::ListUnary),     // -> MaxOver{source, item, Var(item)}
    ("MinList", OpKind::ListUnary),     // -> MinOver{source, item, Var(item)}
    ("MaxLenOver", OpKind::ListUnary),  // -> MaxOver{source, item, Count(Var(item))}
    ("MinLenOver", OpKind::ListUnary),  // -> MinOver{source, item, Count(Var(item))}
    ("First", OpKind::ListUnary),       // -> IndexAt{seq:source, index:0}
    ("LastElem", OpKind::ListUnary),    // -> Last{seq:source}
    ("JoinList", OpKind::ListUnary),    // -> Fold{source, item, acc, "", Concat(acc,item)}
    ("FilterList", OpKind::ListFilter), // -> FilterList{source, item, <template>}
    ("MapList", OpKind::ListMap),       // -> MapList{source, item, <template>}
    // --- Arc6 tier-0 (PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md §4.1):
    // the PROPOSAL layer, not the execution layer.  Each of these four
    // exposes an ALREADY-SHIPPED, already-pure DSL Term as a composable op
    // name — ZERO new `TermNode` variants, exactly the arc-4 S4 shape. ---
    ("TupleOf", OpKind::Binary),           // -> Vec{items:[a,b]}
    ("ProdList", OpKind::ListUnary),       // -> Prod{source, item, Var(item)}  (the SumList twin)
    ("ConcatList", OpKind::ListBinary),    // -> Fold{b, acc<-a, Append(acc,item)} (the JoinList precedent)
    ("ArgMaxLenOver", OpKind::ListUnary),  // -> Argmax{source, item, Count(Var(item))} (the MaxLenOver arg-twin)
];

/// Arc4-S4: the list-op names, in `OP_TABLE` declaration order — appended
/// to `DEFAULT_OPS` to form the list-shaped typed default (see
/// `spec_is_list_shaped` below). Kept as its own slice so the default-set
/// construction reads as "arithmetic PLUS list ops", matching the module
/// doc's framing.
const LIST_EXTRA_OPS: &[&str] = &[
    "Len", "SumList", "MaxList", "MinList", "MaxLenOver", "MinLenOver",
    "First", "LastElem", "JoinList", "FilterList", "MapList",
    // Arc6 tier-0 — APPENDED, never interleaved: within one size the growth
    // loop walks `op_list` in order, so every pre-existing op still registers
    // (and so still claims its signature) ahead of these four.  A widening
    // can therefore only find a solution EARLIER or at a size where none
    // existed — never displace one.
    "ProdList", "ConcatList", "ArgMaxLenOver",
];

/// Arc6 tier-0: `op:TupleOf` is offered under a NARROWER typed default than
/// the rest of `LIST_EXTRA_OPS` — only when the spec's OUTPUT is itself
/// tuple-shaped.
///
/// This is the module's own typed-enumeration mechanism (`DEFAULT_STR_OPS`
/// / `spec_is_list_shaped`), applied to the new op by its RETURN TYPE: a
/// constructor that builds a tuple is offered when a tuple is what is
/// wanted.  It is not a per-task gate — it reads the spec's type, exactly
/// like the two typed defaults that predate it.
///
/// It is also a MEASURED cost control, and this is why it is not optional.
/// Observational-equivalence pruning is what keeps this search tractable,
/// and a tuple constructor DEFEATS it: two distinct operand pairs almost
/// never produce the same tuple, so every pair is a new signature.  On task
/// 132's own spec, adding `TupleOf` to the shipped default moved
/// `distinct` from 167 to 14709 and turned a `solved` at size 6 into
/// `halt_reason:"budget"` — i.e. it REGRESSED an already-passing task.
/// Measured, then priced; see `PROGRAM_SYNTHESIS_ARC6_TIER0.md`.
const TUPLE_BUILD_OPS: &[&str] = &["TupleOf"];

fn table_kind(name: &str) -> Option<OpKind> {
    OP_TABLE.iter().find(|(n, _)| *n == name).map(|(_, k)| *k)
}

/// Arc4-S4: is this Value list-shaped (the source type our new list ops
/// require)? Tuple/Set/FrozenSet only — Dict is deliberately excluded
/// (iterating a Dict's own `.iter()` semantics are keys-only elsewhere in
/// this engine; a dict-shaped reduction is out of this widening's scope).
fn is_listlike(v: &Value) -> bool {
    matches!(v, Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_))
}

/// generator.py's DEFAULT_OPS twin for a STRING-shaped spec (Q1 typed
/// enumeration): chosen when the caller supplies no explicit `ops` AND
/// every variable/output value in the spec is string-typed. Small by
/// design — the enumerator's job is COMPOSITION over a caller-declared
/// inventory, not a from-scratch string-algorithm search; a caller
/// that wants more (e.g. `string_methods`) declares `ops` explicitly.
const DEFAULT_STR_OPS: &[&str] = &["Concat", "CaseFold", "Eq", "IfThenElse"];

/// Build the TermNode for an op over already-arena'd children.
fn build_op(name: &str, kids: &[TermIdx]) -> TermNode {
    match name {
        "Plus" => TermNode::Plus { items: kids.to_vec() },
        "Times" => TermNode::Times { items: kids.to_vec() },
        "Minus" => TermNode::Minus { a: kids[0], b: kids[1] },
        "Div" => TermNode::Div { a: kids[0], b: kids[1] },
        "Min" => TermNode::Min { items: kids.to_vec() },
        "Max" => TermNode::Max { items: kids.to_vec() },
        "Abs" => TermNode::Abs { arg: kids[0] },
        "Neg" => TermNode::Neg { arg: kids[0] },
        "Gt" => TermNode::Gt { a: kids[0], b: kids[1] },
        "Lt" => TermNode::Lt { a: kids[0], b: kids[1] },
        "Gte" => TermNode::Gte { a: kids[0], b: kids[1] },
        "Lte" => TermNode::Lte { a: kids[0], b: kids[1] },
        "Eq" => TermNode::Eq { a: kids[0], b: kids[1] },
        "And" => TermNode::And { items: kids.to_vec() },
        "Or" => TermNode::Or { items: kids.to_vec() },
        "Not" => TermNode::Not { arg: kids[0] },
        "IfThenElse" => TermNode::IfThenElse { cond: kids[0], then: kids[1], other: kids[2] },
        "Concat" => TermNode::StringConcat { parts: kids.to_vec() },
        "CaseFold" => TermNode::CaseFold { text: kids[0] },
        // Arc6 tier-0 `op:TupleOf` — the shipped `Vec` Term, which builds a
        // Tuple.  Binary because that is the arity a fixed-shape op can
        // have here; a variable-arity tuple is NOT reachable this way and is
        // recorded as such (see the tier-0 results document).
        "TupleOf" => TermNode::Vec_ { items: kids.to_vec() },
        _ => unreachable!("op filtered through OP_TABLE"),
    }
}

/// Arc4-S4: build one of the `OpKind::ListUnary` composites. `scratch` is
/// used to mint the small fixed sub-terms each shape needs (a `Var(item)`
/// leaf, a `Count(Var(item))`, a `Lit(0)`, …) — called as its own
/// statement BEFORE `search.register(...)` (never inlined into the same
/// call), so this `&mut TermArena` borrow of `search.scratch` ends before
/// `search.register` needs `&mut search` — see the call sites below.
fn build_list_unary(name: &str, source: TermIdx, item: Sym, acc: Sym, scratch: &mut TermArena) -> TermNode {
    match name {
        "Len" => TermNode::Count { source },
        "SumList" => {
            let v = scratch.add(TermNode::Var { name: item });
            TermNode::Sum { source, var_name: item, value: v }
        }
        "MaxList" => {
            let v = scratch.add(TermNode::Var { name: item });
            TermNode::MaxOver { source, var_name: item, value: v, default: None }
        }
        "MinList" => {
            let v = scratch.add(TermNode::Var { name: item });
            TermNode::MinOver { source, var_name: item, value: v, default: None }
        }
        "MaxLenOver" => {
            let iv = scratch.add(TermNode::Var { name: item });
            let cnt = scratch.add(TermNode::Count { source: iv });
            TermNode::MaxOver { source, var_name: item, value: cnt, default: None }
        }
        "MinLenOver" => {
            let iv = scratch.add(TermNode::Var { name: item });
            let cnt = scratch.add(TermNode::Count { source: iv });
            TermNode::MinOver { source, var_name: item, value: cnt, default: None }
        }
        "First" => {
            let zero = scratch.add(TermNode::Lit { value: Value::Int(0) });
            TermNode::IndexAt { seq: source, index: zero }
        }
        "LastElem" => TermNode::Last { seq: source },
        "JoinList" => {
            let accv = scratch.add(TermNode::Var { name: acc });
            let itemv = scratch.add(TermNode::Var { name: item });
            let body = scratch.add(TermNode::StringConcat { parts: vec![accv, itemv] });
            let init = scratch.add(TermNode::Lit { value: surf("") });
            TermNode::Fold { source, var_name: item, acc_name: acc, init, body }
        }
        // Arc6 tier-0 `op:ProdList` — the `SumList` twin, over the shipped
        // `Prod` Term.
        "ProdList" => {
            let v = scratch.add(TermNode::Var { name: item });
            TermNode::Prod { source, var_name: item, value: v }
        }
        // Arc6 tier-0 `op:ArgMaxLenOver` — the ARG-twin of the shipped
        // `MaxLenOver`, over the shipped `Argmax` Term: same source, same
        // projection, the WITNESS instead of the value.
        "ArgMaxLenOver" => {
            let iv = scratch.add(TermNode::Var { name: item });
            let cnt = scratch.add(TermNode::Count { source: iv });
            TermNode::Argmax { source, var_name: item, value: cnt, default: None }
        }
        _ => unreachable!("ListUnary op filtered through OP_TABLE"),
    }
}

/// Arc6 tier-0 `op:ConcatList` — LIST concatenation, built exactly the way
/// `JoinList` builds STRING concatenation: a `Fold` over the second source
/// with the first as the accumulator's initial value and `Append` as the
/// body.  (`Cat` is string concat and emits Rust debug reprs on lists —
/// measured, §7.3 — so `Fold`+`Append` is the real route, and both Terms
/// are already shipped.)
fn build_list_binary(name: &str, a: TermIdx, b: TermIdx, item: Sym, acc: Sym, scratch: &mut TermArena) -> TermNode {
    match name {
        "ConcatList" => {
            let accv = scratch.add(TermNode::Var { name: acc });
            let itemv = scratch.add(TermNode::Var { name: item });
            let body = scratch.add(TermNode::Append { seq: accv, item: itemv });
            TermNode::Fold { source: b, var_name: item, acc_name: acc, init: a, body }
        }
        _ => unreachable!("ListBinary op filtered through OP_TABLE"),
    }
}

/// Arc6 tier-0: the FIXED node-count `build_list_binary` injects beyond its
/// two sources — the same honest MDL accounting `list_unary_extra_cost`
/// does for the unary shapes.
fn list_binary_extra_cost(name: &str) -> usize {
    match name {
        "ConcatList" => 3, // Fold{.., body: Append(Var(acc), Var(item))}
        _ => 0,
    }
}

/// Arc4-S4: build one of the `OpKind::ListFilter`/`OpKind::ListMap`
/// composites — `tmpl` is an ALREADY-BUILT template subtree (from
/// `filter_templates_by_size`/`map_templates_by_size`), reused as a
/// shared child across every `source` it is combined with (the same
/// subtree-sharing discipline every other op in this module already
/// relies on).
fn build_list_ho(name: &str, source: TermIdx, tmpl: TermIdx, item: Sym) -> TermNode {
    match name {
        "FilterList" => TermNode::FilterList { source, var_name: item, predicate: tmpl },
        "MapList" => TermNode::MapList { source, var_name: item, value: tmpl },
        _ => unreachable!("ListHigherOrder op filtered through OP_TABLE"),
    }
}

/// Arc4-S4: the FIXED node-count `build_list_unary` injects BEYOND
/// `source` for each named shape — honest MDL/Occam sizing (the module's
/// own documented rule: "size = 1 (the node) + sum of child sizes;
/// leaves are size 1") requires counting the hidden `Var(item)`/
/// `Count(Var(item))`/`Lit(0)`/`Fold`-scaffold leaves each shape mints,
/// not just the visible `source` argument. Kept as its own lookup so the
/// growth loop's size partition (`size == 1 + extra + source_size`) is
/// correct per-name rather than assuming a uniform "+1".
fn list_unary_extra_cost(name: &str) -> usize {
    match name {
        "Len" => 0,           // Count{source} — no other child
        "SumList" => 1,       // Sum{source, value:Var(item)}
        "MaxList" => 1,       // MaxOver{source, value:Var(item)}
        "MinList" => 1,       // MinOver{source, value:Var(item)}
        "MaxLenOver" => 2,    // MaxOver{source, value:Count(Var(item))}
        "MinLenOver" => 2,    // MinOver{source, value:Count(Var(item))}
        "First" => 1,         // IndexAt{seq:source, index:Lit(0)}
        "LastElem" => 0,      // Last{seq:source} — no other child
        "JoinList" => 4,      // Fold{source, init:Lit("")(1), body:Concat(acc,item)(3)}
        // Arc6 tier-0.
        "ProdList" => 1,      // Prod{source, value:Var(item)}
        "ArgMaxLenOver" => 2, // Argmax{source, value:Count(Var(item))}
        _ => 0,
    }
}

/// Arc4-S4 filter-predicate template comparator kinds — see
/// `build_filter_templates`.
#[derive(Clone, Copy)]
enum CmpKind {
    Gt,
    Lt,
    Gte,
    Lte,
    Eq,
}

fn build_cmp(k: CmpKind, a: TermIdx, b: TermIdx) -> TermNode {
    match k {
        CmpKind::Gt => TermNode::Gt { a, b },
        CmpKind::Lt => TermNode::Lt { a, b },
        CmpKind::Gte => TermNode::Gte { a, b },
        CmpKind::Lte => TermNode::Lte { a, b },
        CmpKind::Eq => TermNode::Eq { a, b },
    }
}

// ---------------------------------------------------------------------------
// Q1 `exclude` parsing — a MINIMAL, self-contained Term-JSON reader
// scoped to exactly this module's own grammar (Var / Lit / the OP_TABLE
// ops). Deliberately NOT `jsonio::term_from_json`: that function needs
// `&mut Interner` to intern identifiers on the way in, but this engine
// only ever holds `&Interner` (the documented immutable-at-eval-time
// discipline). Sidestepped rather than fought: a Var resolves against
// the SPEC's OWN already-interned names (an excluded term came from a
// prior call over the same variables — its names are never novel); a
// Lit string mints a Surface(Text), which `canon` already treats
// identically to an interned Str for signature purposes. Any node this
// parser doesn't recognise (unknown type, missing field, an op outside
// the table, a Var this spec doesn't have) returns `None` — the whole
// excluded entry is then skipped, never fatal to the rest of the call.
// ---------------------------------------------------------------------------

fn json_to_lit_value(v: &serde_json::Value) -> Option<Value> {
    match v {
        serde_json::Value::Null => Some(Value::None),
        serde_json::Value::Bool(b) => Some(Value::Bool(*b)),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Some(Value::Int(i))
            } else {
                n.as_f64().map(Value::Float)
            }
        }
        serde_json::Value::String(s) => Some(surf_string(s.clone())),
        _ => None,
    }
}

fn parse_excluded_term(
    j: &serde_json::Value,
    arena: &mut TermArena,
    var_by_name: &FxHashMap<String, Sym>,
) -> Option<TermIdx> {
    let obj = j.as_object()?;
    let ty = obj.get("type")?.as_str()?;
    match ty {
        "Var" => {
            let name = obj.get("name")?.as_str()?;
            let sym = *var_by_name.get(name)?;
            Some(arena.add(TermNode::Var { name: sym }))
        }
        "Lit" => {
            let value = json_to_lit_value(obj.get("value")?)?;
            Some(arena.add(TermNode::Lit { value }))
        }
        "Plus" | "Times" | "Min" | "Max" | "And" | "Or" => {
            let items = obj.get("items")?.as_array()?;
            let mut kids = Vec::with_capacity(items.len());
            for it in items {
                kids.push(parse_excluded_term(it, arena, var_by_name)?);
            }
            Some(arena.add(match ty {
                "Plus" => TermNode::Plus { items: kids },
                "Times" => TermNode::Times { items: kids },
                "Min" => TermNode::Min { items: kids },
                "Max" => TermNode::Max { items: kids },
                "And" => TermNode::And { items: kids },
                _ => TermNode::Or { items: kids },
            }))
        }
        "Minus" | "Div" | "Gt" | "Lt" | "Gte" | "Lte" | "Eq" => {
            let a = parse_excluded_term(obj.get("a")?, arena, var_by_name)?;
            let b = parse_excluded_term(obj.get("b")?, arena, var_by_name)?;
            Some(arena.add(match ty {
                "Minus" => TermNode::Minus { a, b },
                "Div" => TermNode::Div { a, b },
                "Gt" => TermNode::Gt { a, b },
                "Lt" => TermNode::Lt { a, b },
                "Gte" => TermNode::Gte { a, b },
                "Lte" => TermNode::Lte { a, b },
                _ => TermNode::Eq { a, b },
            }))
        }
        "Abs" | "Neg" | "Not" => {
            let arg = parse_excluded_term(obj.get("arg")?, arena, var_by_name)?;
            Some(arena.add(match ty {
                "Abs" => TermNode::Abs { arg },
                "Neg" => TermNode::Neg { arg },
                _ => TermNode::Not { arg },
            }))
        }
        "IfThenElse" => {
            let cond = parse_excluded_term(obj.get("cond")?, arena, var_by_name)?;
            let then = parse_excluded_term(obj.get("then")?, arena, var_by_name)?;
            let other = parse_excluded_term(obj.get("other")?, arena, var_by_name)?;
            Some(arena.add(TermNode::IfThenElse { cond, then, other }))
        }
        "StringConcat" => {
            let items = obj.get("parts")?.as_array()?;
            let mut kids = Vec::with_capacity(items.len());
            for it in items {
                kids.push(parse_excluded_term(it, arena, var_by_name)?);
            }
            Some(arena.add(TermNode::StringConcat { parts: kids }))
        }
        "CaseFold" => {
            let text = parse_excluded_term(obj.get("text")?, arena, var_by_name)?;
            Some(arena.add(TermNode::CaseFold { text }))
        }
        _ => None,
    }
}

// ---------------------------------------------------------------------------
// Observational-equivalence signatures — generator.py's `_canon`,
// WIDENED (Q1) past the int/float/bool floor to the Q0-picked value
// domain: bool stays distinct from number; int folds onto float
// (1 == 1.0); NaN folds to a stable token; -0.0 == 0.0 (Python float
// equality); strings compare exactly; every other Value (None, Dict,
// Tuple, Set/FrozenSet, Node) compares by a stable recursive canonical
// repr (`canon_repr`) built the same way, so two candidates with equal
// STRUCTURE (not just equal numbers) are still recognised as
// observationally identical. Nothing is inadmissible anymore under
// this widened domain — `inadmissible` is kept in the output Dict for
// wire back-compat but is now structurally unreachable (documented in
// PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md: the plain DSL `evaluate()` this
// engine drives has no error channel distinct from an ordinary Value,
// so there was never a real "some inputs error, others don't" case to
// detect here — P1's original `None`-for-non-scalar branch was the
// widening's OWN missing floor, not a genuine admissibility check).
// ---------------------------------------------------------------------------

#[derive(Clone, PartialEq, Eq, Hash)]
enum SigVal {
    Bool(bool),
    Num(u64), // f64 bits, -0.0 normalised to +0.0
    NaN,
    NoneV,
    Str(String),
    /// Stable recursive repr for anything else (Dict/Tuple/Set/
    /// FrozenSet/Node/Surface(Bytes)) — see `canon_repr`.
    Other(String),
}

fn norm_bits(f: f64) -> u64 {
    if f == 0.0 { 0.0f64.to_bits() } else { f.to_bits() }
}

/// Recursive canonical repr for container/other Values — length-
/// prefixed segments so distinct value shapes can't collide on a
/// naively-delimited string (e.g. Tuple[Str("I:5")] vs Tuple[Int(5)]).
fn canon_repr(v: &Value, interner: &Interner) -> String {
    match v {
        Value::None => "N".to_string(),
        Value::Bool(b) => format!("B{}", if *b { 1 } else { 0 }),
        Value::Int(i) => format!("I{}", norm_bits(*i as f64)),
        Value::Float(f) => {
            if f.is_nan() {
                "F:nan".to_string()
            } else {
                format!("F{}", norm_bits(*f))
            }
        }
        // Never reachable as a top-level `canon()` result (that arm
        // renders to the SAME `F<bits>` shape as Float, the boundary —
        // see below); this recursive repr only matters when a Rational
        // is nested inside a Tuple/Set/Dict being reprsented.
        Value::Rational(n, d) => format!("Q{}/{}", n, d),
        Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
            let s = value_str(v, interner).unwrap_or_default();
            format!("S{}:{}", s.len(), s)
        }
        Value::Surface(SurfaceKind::Bytes, b) => format!("Y{}:{:?}", b.len(), b),
        Value::Node(n) => format!("D{:?}", n),
        Value::Tuple(items) => {
            let parts: Vec<String> = items.iter().map(|x| canon_repr(x, interner)).collect();
            format!("T{}[{}]", parts.len(), parts.join(","))
        }
        // DISTINCT prefix from Tuple's `T`: observational-equivalence
        // pruning must not merge a list-returning candidate with a
        // tuple-returning one now that the two are not equal. (The
        // `TupleOf` precedent -- 167 -> 14,709 distinct candidates --
        // is why this is measured rather than assumed; see the results
        // doc's search-space section.)
        Value::List(items) => {
            let parts: Vec<String> = items.iter().map(|x| canon_repr(x, interner)).collect();
            format!("L{}[{}]", parts.len(), parts.join(","))
        }
        Value::Set(items) | Value::FrozenSet(items) => {
            // Already canonically sorted at construction (make_set /
            // make_frozenset) — recursion is deterministic.
            let parts: Vec<String> = items.iter().map(|x| canon_repr(x, interner)).collect();
            format!("Z{}[{}]", parts.len(), parts.join(","))
        }
        Value::Dict(pairs) => {
            // Always stored sorted-by-key at construction.
            let parts: Vec<String> = pairs
                .iter()
                .map(|(k, v)| format!("{}={}", canon_repr(k, interner), canon_repr(v, interner)))
                .collect();
            format!("M{}[{}]", parts.len(), parts.join(","))
        }
    }
}

fn canon(v: &Value, interner: &Interner) -> SigVal {
    match v {
        Value::Bool(b) => SigVal::Bool(*b),
        Value::Int(i) => SigVal::Num(norm_bits(*i as f64)),
        Value::Float(f) => {
            if f.is_nan() {
                SigVal::NaN
            } else {
                SigVal::Num(norm_bits(*f))
            }
        }
        // THE boundary (PROGRAM_SYNTHESIS_ARC5_RATIONAL.md): a candidate
        // program may compute an exact Rational where the spec's own
        // target row is a plain float (e.g. `k=4/3` against an
        // `expected: 33.51...`). Rendering to the SAME `SigVal::Num`
        // shape as Float/Int means `slot_matches`'s existing 1e-9
        // tolerance compare applies unchanged — an explicit `SigVal::
        // Other(canon_repr(..))` here would instead compare by EXACT
        // STRING against a float target and never match.
        Value::Rational(n, d) => SigVal::Num(norm_bits(*n as f64 / *d as f64)),
        Value::None => SigVal::NoneV,
        Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
            SigVal::Str(value_str(v, interner).unwrap_or_default())
        }
        other => SigVal::Other(canon_repr(other, interner)),
    }
}

type Sig = Vec<SigVal>;

/// Per-slot target match — generator.py's numeric type-agnostic rule
/// (bool ↔ number, 1e-9 tolerance, NaN never matches) EXTENDED with
/// exact equality for the newly-representable non-numeric types.
fn slot_matches(got: &SigVal, want: &SigVal) -> bool {
    match (got, want) {
        (SigVal::NaN, _) | (_, SigVal::NaN) => false,
        (SigVal::Num(a), SigVal::Num(b)) => (f64::from_bits(*a) - f64::from_bits(*b)).abs() <= 1e-9,
        (SigVal::Bool(a), SigVal::Num(b)) => {
            ((if *a { 1.0 } else { 0.0 }) - f64::from_bits(*b)).abs() <= 1e-9
        }
        (SigVal::Num(a), SigVal::Bool(b)) => {
            (f64::from_bits(*a) - (if *b { 1.0 } else { 0.0 })).abs() <= 1e-9
        }
        (SigVal::Bool(a), SigVal::Bool(b)) => a == b,
        (SigVal::NoneV, SigVal::NoneV) => true,
        (SigVal::Str(a), SigVal::Str(b)) => a == b,
        (SigVal::Other(a), SigVal::Other(b)) => a == b,
        _ => false,
    }
}

fn matches_target(sig: &[SigVal], target: &[SigVal]) -> bool {
    sig.len() == target.len() && sig.iter().zip(target.iter()).all(|(s, t)| slot_matches(s, t))
}

// ---------------------------------------------------------------------------
// Input parsing helpers.
// ---------------------------------------------------------------------------

/// Read a string out of a Str/Surface(Text) value.
fn value_str(v: &Value, interner: &Interner) -> Option<String> {
    match v {
        Value::Str(s) => Some(interner.resolve(*s).to_string()),
        Value::Surface(SurfaceKind::Text, b) => Some(String::from_utf8_lossy(b).into_owned()),
        _ => None,
    }
}

/// Dict lookup by resolved key string.
fn dict_get(pairs: &[(Value, Value)], key: &str, interner: &Interner) -> Option<Value> {
    for (k, v) in pairs {
        if let Some(s) = value_str(k, interner) {
            if s == key {
                return Some(v.clone());
            }
        }
    }
    None
}

/// Items of a Tuple/Set/FrozenSet (a "list" arriving from any wire form).
fn items_of(v: &Value) -> Option<Vec<Value>> {
    match v {
        Value::Tuple(items) | Value::List(items) => Some(items.iter().cloned().collect()),
        Value::Set(items) | Value::FrozenSet(items) => Some(items.iter().cloned().collect()),
        _ => None,
    }
}

/// Resolve (or locally fabricate) a Sym for a variable name — the
/// shape_decode.rs `local_sym` precedent. Fabricated Syms are scoped to
/// one SynthEnumerate call and NEVER reach `Interner::resolve` (the
/// output serializer reads this module's own name table instead).
fn local_sym(
    interner: &Interner,
    extra: &mut FxHashMap<String, Sym>,
    next_id: &mut u32,
    s: &str,
) -> Sym {
    if let Some(sym) = interner.lookup(s) {
        return sym;
    }
    if let Some(sym) = extra.get(s) {
        return *sym;
    }
    let sym = Sym(*next_id);
    *next_id = next_id.wrapping_sub(1);
    extra.insert(s.to_string(), sym);
    sym
}

// ---------------------------------------------------------------------------
// Output serialization — LOCAL (no interner): Term-JSON in exactly the
// wire form jsonio::term_from_json parses, and generator.py's
// `_term_str` rendering for the human-readable twin.
// ---------------------------------------------------------------------------

/// `v` is either a value that arrived through the spec (a REAL interned
/// Sym for `Value::Str`, safe to resolve) or a Surface(Text) this
/// module minted itself (no interner involved). Both are safe to
/// resolve/read here — unlike Var names, Lit VALUES never carry a
/// locally-fabricated placeholder Sym.
fn lit_json(v: &Value, interner: &Interner) -> serde_json::Value {
    match v {
        Value::Bool(b) => serde_json::Value::Bool(*b),
        Value::Int(i) => serde_json::Value::Number((*i).into()),
        Value::Float(f) => serde_json::Number::from_f64(*f)
            .map(serde_json::Value::Number)
            .unwrap_or(serde_json::Value::Null),
        Value::None => serde_json::Value::Null,
        Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
            serde_json::Value::String(value_str(v, interner).unwrap_or_default())
        }
        _ => serde_json::Value::Null,
    }
}

fn term_json(
    arena: &TermArena,
    idx: TermIdx,
    names: &FxHashMap<Sym, String>,
    interner: &Interner,
) -> serde_json::Value {
    use serde_json::json;
    match arena.get(idx) {
        TermNode::Var { name } => json!({
            "type": "Var",
            "name": names.get(name).cloned().unwrap_or_default(),
        }),
        TermNode::Lit { value } => json!({ "type": "Lit", "value": lit_json(value, interner) }),
        TermNode::Plus { items } | TermNode::Times { items } | TermNode::Min { items }
        | TermNode::Max { items } | TermNode::And { items } | TermNode::Or { items } => {
            let t = match arena.get(idx) {
                TermNode::Plus { .. } => "Plus",
                TermNode::Times { .. } => "Times",
                TermNode::Min { .. } => "Min",
                TermNode::Max { .. } => "Max",
                TermNode::And { .. } => "And",
                _ => "Or",
            };
            json!({
                "type": t,
                "items": items.iter().map(|i| term_json(arena, *i, names, interner)).collect::<Vec<_>>(),
            })
        }
        TermNode::Minus { a, b } => json!({
            "type": "Minus", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::Div { a, b } => json!({
            "type": "Div", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::Gt { a, b } => json!({
            "type": "Gt", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::Lt { a, b } => json!({
            "type": "Lt", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::Gte { a, b } => json!({
            "type": "Gte", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::Lte { a, b } => json!({
            "type": "Lte", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::Eq { a, b } => json!({
            "type": "Eq", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::Abs { arg } => json!({ "type": "Abs", "arg": term_json(arena, *arg, names, interner) }),
        TermNode::Neg { arg } => json!({ "type": "Neg", "arg": term_json(arena, *arg, names, interner) }),
        TermNode::Not { arg } => json!({ "type": "Not", "arg": term_json(arena, *arg, names, interner) }),
        TermNode::IfThenElse { cond, then, other } => json!({
            "type": "IfThenElse",
            "cond": term_json(arena, *cond, names, interner),
            "then": term_json(arena, *then, names, interner),
            "other": term_json(arena, *other, names, interner),
        }),
        TermNode::StringConcat { parts } => json!({
            "type": "StringConcat",
            "parts": parts.iter().map(|i| term_json(arena, *i, names, interner)).collect::<Vec<_>>(),
        }),
        TermNode::CaseFold { text } => json!({
            "type": "CaseFold", "text": term_json(arena, *text, names, interner)
        }),
        // --- Arc4-S4: list/iteration composites — JSON shapes match
        // `jsonio.rs`'s existing parser for these (already-general) Term
        // types exactly (field names "source"/"var_name"/"value"/
        // "default"/"seq"/"index"/"acc_name"/"init"/"body"/"predicate"),
        // so a round-trip through `json.loads` -> Python dict ->
        // `jsonio::term_from_json` (elsewhere in the pipeline) parses
        // cleanly; `var_name`/`acc_name` serialize as the STRING this
        // module's own `names` table holds for the locally-fabricated
        // `__item`/`__acc` Syms — the same convention `Var` uses above,
        // never the raw Sym value. ---
        TermNode::Count { source } => json!({
            "type": "Count", "source": term_json(arena, *source, names, interner),
        }),
        TermNode::Sum { source, var_name, value } => json!({
            "type": "Sum",
            "source": term_json(arena, *source, names, interner),
            "var_name": names.get(var_name).cloned().unwrap_or_default(),
            "value": term_json(arena, *value, names, interner),
        }),
        TermNode::MaxOver { source, var_name, value, default } => {
            let mut m = serde_json::Map::new();
            m.insert("type".to_string(), json!("MaxOver"));
            m.insert("source".to_string(), term_json(arena, *source, names, interner));
            m.insert("var_name".to_string(), json!(names.get(var_name).cloned().unwrap_or_default()));
            m.insert("value".to_string(), term_json(arena, *value, names, interner));
            if let Some(d) = default {
                m.insert("default".to_string(), term_json(arena, *d, names, interner));
            }
            serde_json::Value::Object(m)
        }
        TermNode::MinOver { source, var_name, value, default } => {
            let mut m = serde_json::Map::new();
            m.insert("type".to_string(), json!("MinOver"));
            m.insert("source".to_string(), term_json(arena, *source, names, interner));
            m.insert("var_name".to_string(), json!(names.get(var_name).cloned().unwrap_or_default()));
            m.insert("value".to_string(), term_json(arena, *value, names, interner));
            if let Some(d) = default {
                m.insert("default".to_string(), term_json(arena, *d, names, interner));
            }
            serde_json::Value::Object(m)
        }
        TermNode::FilterList { source, var_name, predicate } => json!({
            "type": "FilterList",
            "source": term_json(arena, *source, names, interner),
            "var_name": names.get(var_name).cloned().unwrap_or_default(),
            "predicate": term_json(arena, *predicate, names, interner),
        }),
        TermNode::MapList { source, var_name, value } => json!({
            "type": "MapList",
            "source": term_json(arena, *source, names, interner),
            "var_name": names.get(var_name).cloned().unwrap_or_default(),
            "value": term_json(arena, *value, names, interner),
        }),
        TermNode::IndexAt { seq, index } => json!({
            "type": "IndexAt",
            "seq": term_json(arena, *seq, names, interner),
            "index": term_json(arena, *index, names, interner),
        }),
        TermNode::Last { seq } => json!({
            "type": "Last", "seq": term_json(arena, *seq, names, interner),
        }),
        TermNode::Fold { source, var_name, acc_name, init, body } => json!({
            "type": "Fold",
            "source": term_json(arena, *source, names, interner),
            "var_name": names.get(var_name).cloned().unwrap_or_default(),
            "acc_name": names.get(acc_name).cloned().unwrap_or_default(),
            "init": term_json(arena, *init, names, interner),
            "body": term_json(arena, *body, names, interner),
        }),
        // --- Arc6 tier-0: the four newly-PROPOSABLE (long-shipped) shapes.
        // Field names match `jsonio.rs`'s existing parser for each type, so
        // the wire round-trip is unchanged in kind. ---
        TermNode::Vec_ { items } => json!({
            "type": "Vec",
            "items": items.iter().map(|i| term_json(arena, *i, names, interner)).collect::<Vec<_>>(),
        }),
        TermNode::Prod { source, var_name, value } => json!({
            "type": "Prod",
            "source": term_json(arena, *source, names, interner),
            "var_name": names.get(var_name).cloned().unwrap_or_default(),
            "value": term_json(arena, *value, names, interner),
        }),
        TermNode::Argmax { source, var_name, value, default } => {
            let mut m = serde_json::Map::new();
            m.insert("type".to_string(), json!("Argmax"));
            m.insert("source".to_string(), term_json(arena, *source, names, interner));
            m.insert("var_name".to_string(), json!(names.get(var_name).cloned().unwrap_or_default()));
            m.insert("value".to_string(), term_json(arena, *value, names, interner));
            if let Some(d) = default {
                m.insert("default".to_string(), term_json(arena, *d, names, interner));
            }
            serde_json::Value::Object(m)
        }
        TermNode::Append { seq, item } => json!({
            "type": "Append",
            "seq": term_json(arena, *seq, names, interner),
            "item": term_json(arena, *item, names, interner),
        }),
        TermNode::In { member, container } => json!({
            "type": "In",
            "member": term_json(arena, *member, names, interner),
            "container": term_json(arena, *container, names, interner),
        }),
        _ => unreachable!("candidates are built only from the op table + leaves"),
    }
}

/// Python `repr` of the Lit values this module mints (numeric/string
/// consts).
fn lit_repr(v: &Value, interner: &Interner) -> String {
    match v {
        Value::Bool(b) => (if *b { "True" } else { "False" }).to_string(),
        Value::Int(i) => i.to_string(),
        Value::Float(f) => format!("{f:?}"),
        Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
            // Python `repr()`'s single-quote convention (not Rust's
            // double-quoted Debug) — good enough for this module's
            // "readable infix-ish rendering" (never re-parsed).
            format!("'{}'", value_str(v, interner).unwrap_or_default())
        }
        Value::None => "None".to_string(),
        _ => "?".to_string(),
    }
}

/// generator.py's `_term_str` — readable infix-ish rendering.
fn term_str(arena: &TermArena, idx: TermIdx, names: &FxHashMap<Sym, String>, interner: &Interner) -> String {
    match arena.get(idx) {
        TermNode::Var { name } => names.get(name).cloned().unwrap_or_default(),
        TermNode::Lit { value } => lit_repr(value, interner),
        TermNode::Plus { items } | TermNode::Times { items } | TermNode::And { items }
        | TermNode::Or { items } => {
            let sym = match arena.get(idx) {
                TermNode::Plus { .. } => "+",
                TermNode::Times { .. } => "*",
                TermNode::And { .. } => "and",
                _ => "or",
            };
            let kids: Vec<String> = items.iter().map(|i| term_str(arena, *i, names, interner)).collect();
            format!("({})", kids.join(&format!(" {sym} ")))
        }
        TermNode::Min { items } | TermNode::Max { items } => {
            let sym = if matches!(arena.get(idx), TermNode::Min { .. }) { "min" } else { "max" };
            let kids: Vec<String> = items.iter().map(|i| term_str(arena, *i, names, interner)).collect();
            format!("{sym}({})", kids.join(", "))
        }
        TermNode::Minus { a, b } => format!("({} - {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::Div { a, b } => format!("({} / {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::Gt { a, b } => format!("({} > {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::Lt { a, b } => format!("({} < {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::Gte { a, b } => format!("({} >= {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::Lte { a, b } => format!("({} <= {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::Eq { a, b } => format!("({} == {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::Abs { arg } => format!("abs({})", term_str(arena, *arg, names, interner)),
        TermNode::Neg { arg } => format!("neg({})", term_str(arena, *arg, names, interner)),
        TermNode::Not { arg } => format!("not({})", term_str(arena, *arg, names, interner)),
        TermNode::IfThenElse { cond, then, other } => format!(
            "(if {} then {} else {})",
            term_str(arena, *cond, names, interner),
            term_str(arena, *then, names, interner),
            term_str(arena, *other, names, interner),
        ),
        TermNode::StringConcat { parts } => {
            let kids: Vec<String> = parts.iter().map(|i| term_str(arena, *i, names, interner)).collect();
            format!("({})", kids.join(" + "))
        }
        TermNode::CaseFold { text } => format!("lower({})", term_str(arena, *text, names, interner)),
        // --- Arc4-S4: readable (never re-parsed) renderings for the new
        // list/iteration composites. ---
        TermNode::Count { source } => format!("len({})", term_str(arena, *source, names, interner)),
        TermNode::Sum { source, var_name, value } => format!(
            "sum({} for {} in {})",
            term_str(arena, *value, names, interner),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
        ),
        TermNode::MaxOver { source, var_name, value, .. } => format!(
            "max({} for {} in {})",
            term_str(arena, *value, names, interner),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
        ),
        TermNode::MinOver { source, var_name, value, .. } => format!(
            "min({} for {} in {})",
            term_str(arena, *value, names, interner),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
        ),
        TermNode::FilterList { source, var_name, predicate } => format!(
            "[{} for {} in {} if {}]",
            names.get(var_name).cloned().unwrap_or_default(),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
            term_str(arena, *predicate, names, interner),
        ),
        TermNode::MapList { source, var_name, value } => format!(
            "[{} for {} in {}]",
            term_str(arena, *value, names, interner),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
        ),
        TermNode::IndexAt { seq, index } => format!(
            "{}[{}]", term_str(arena, *seq, names, interner), term_str(arena, *index, names, interner)
        ),
        TermNode::Last { seq } => format!("{}[-1]", term_str(arena, *seq, names, interner)),
        TermNode::Fold { source, var_name, acc_name, init, body } => format!(
            "fold({}, {}={}, {} -> {})",
            term_str(arena, *source, names, interner),
            names.get(acc_name).cloned().unwrap_or_default(),
            term_str(arena, *init, names, interner),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *body, names, interner),
        ),
        // --- Arc6 tier-0 renderings (readable, never re-parsed). ---
        TermNode::Vec_ { items } => {
            let kids: Vec<String> = items.iter().map(|i| term_str(arena, *i, names, interner)).collect();
            format!("({})", kids.join(", "))
        }
        TermNode::Prod { source, var_name, value } => format!(
            "prod({} for {} in {})",
            term_str(arena, *value, names, interner),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
        ),
        TermNode::Argmax { source, var_name, value, .. } => format!(
            "argmax({} for {} in {})",
            term_str(arena, *value, names, interner),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
        ),
        TermNode::Append { seq, item } => format!(
            "append({}, {})",
            term_str(arena, *seq, names, interner),
            term_str(arena, *item, names, interner),
        ),
        TermNode::In { member, container } => format!(
            "({} in {})",
            term_str(arena, *member, names, interner),
            term_str(arena, *container, names, interner),
        ),
        _ => "?".to_string(),
    }
}

// ---------------------------------------------------------------------------
// The search state.
// ---------------------------------------------------------------------------

enum Reg {
    Stored,
    Dropped,
    Solved(TermIdx),
    Budget,
}

struct Search {
    scratch: TermArena,
    /// Var name strings (real AND locally fabricated Syms) for output
    /// serialization — the interner is never consulted on the way out.
    names: FxHashMap<Sym, String>,
    /// Per-row example bindings (the ONLY bindings candidates see).
    envs: Vec<Env>,
    target: Sig,
    seen: FxHashSet<Sig>,
    by_size: Vec<Vec<TermIdx>>,
    /// Arc4-S4: PURELY ADDITIVE index alongside `by_size` — every
    /// candidate whose evaluated Value is Tuple/Set/FrozenSet on EVERY
    /// example row also lands here, so the new list ops (`build_list_unary`/
    /// `build_list_ho`) draw sources only from genuinely list-shaped
    /// building blocks. Never consulted by any pre-existing op, so it has
    /// zero effect on `tested`/`pruned_equiv`/`seen`/registration order for
    /// any spec whose `op_list` doesn't contain a list op name.
    list_by_size: Vec<Vec<TermIdx>>,
    tested: u64,
    pruned_equiv: u64,
    /// Q1: structurally unreachable now (`canon` is total over the
    /// widened Value domain — see the module-doc note by `SigVal`).
    /// Kept in the struct/output Dict for wire back-compat only.
    inadmissible: u64,
    max_candidates: u64,
}

impl Search {
    /// generator.py's `register`: count, evaluate → signature, prune by
    /// observational equivalence, check target FIRST on a new
    /// signature, store as a building block.
    fn register(&mut self, node: TermNode, size: usize, ctx: &mut EvalCtx) -> Reg {
        self.register_kind(node, size, ctx, true)
    }

    /// Arc6 tier-0: register a TERMINAL candidate — it is target-checked
    /// exactly like any other, but is NOT stored as a building block.
    ///
    /// Used only by `op:TupleOf`.  A 2-tuple built out of this inventory is
    /// an ANSWER SHAPE, not an intermediate: no op in the table consumes it
    /// usefully (`SumList(Vec(a,b))` is just `a+b`, which `Plus` already
    /// reaches at the same size), while storing it costs the search dearly —
    /// tuples do not collide under observational equivalence, so composing
    /// them multiplies the distinct pool instead of pruning it (measured:
    /// 167 -> 14709 distinct on task 132's spec).  The honest price of this
    /// bound is that a NESTED tuple (`Vec(Vec(a,b), c)`) is unreachable; that
    /// is recorded, not hidden.
    fn register_terminal(&mut self, node: TermNode, size: usize, ctx: &mut EvalCtx) -> Reg {
        self.register_kind(node, size, ctx, false)
    }

    fn register_kind(&mut self, node: TermNode, size: usize, ctx: &mut EvalCtx, compose: bool) -> Reg {
        if self.tested >= self.max_candidates {
            return Reg::Budget;
        }
        self.tested += 1;
        let idx = self.scratch.add(node);
        let mut sig: Sig = Vec::with_capacity(self.envs.len());
        // Arc4-S4: classify list-likeness ALONGSIDE the existing per-row
        // signature loop (no extra evaluation pass) — `all_list` stays
        // true only if EVERY row's value is Tuple/Set/FrozenSet, so a
        // spec with a heterogeneous-typed candidate (rare, but possible
        // under the widened Q1 value domain) is never misfiled as a list
        // source.
        let mut all_list = !self.envs.is_empty();
        for base in &self.envs {
            let mut e: Env = base.clone();
            let out = evaluate(&self.scratch, idx, &mut e, ctx);
            if !is_listlike(&out) {
                all_list = false;
            }
            sig.push(canon(&out, ctx.interner));
        }
        if self.seen.contains(&sig) {
            self.pruned_equiv += 1;
            return Reg::Dropped; // observationally equivalent to a smaller (or =) term, OR pre-excluded
        }
        let solved = matches_target(&sig, &self.target);
        self.seen.insert(sig);
        if compose {
            self.by_size[size].push(idx);
            if all_list {
                self.list_by_size[size].push(idx);
            }
        }
        if solved { Reg::Solved(idx) } else { Reg::Stored }
    }

    /// Pre-seed an EXCLUDED candidate's signature into `seen` — never
    /// counted toward `tested`/budgets, never added to `by_size` (it is
    /// a refutation record, not a reusable building block). Any later
    /// candidate with the SAME observational behaviour, however built —
    /// including an auto-appended constant that would otherwise
    /// resurrect it — is now indistinguishable from "already seen" and
    /// is silently dropped (counted as `pruned_equiv`, the P7-B fix).
    /// `idx` must already be a node in `self.scratch`.
    fn preseed_excluded_idx(&mut self, idx: TermIdx, ctx: &mut EvalCtx) {
        let mut sig: Sig = Vec::with_capacity(self.envs.len());
        for base in &self.envs {
            let mut e: Env = base.clone();
            let out = evaluate(&self.scratch, idx, &mut e, ctx);
            sig.push(canon(&out, ctx.interner));
        }
        self.seen.insert(sig);
    }
}

// ---------------------------------------------------------------------------
// Result assembly (the prog_eval.rs finish_result convention, with the
// local field selector).
// ---------------------------------------------------------------------------

#[allow(clippy::too_many_arguments)]
fn finish(
    search: Option<&Search>,
    solved: Option<(TermIdx, usize)>,
    halt_reason: &str,
    saturated: bool,
    field: Sym,
    interner: &Interner,
) -> Value {
    let (term_v, term_str_v, size_v) = match (search, solved) {
        (Some(s), Some((idx, size))) => (
            surf_string(
                serde_json::to_string(&term_json(&s.scratch, idx, &s.names, interner))
                    .unwrap_or_default(),
            ),
            surf_string(term_str(&s.scratch, idx, &s.names, interner)),
            Value::Int(size as i64),
        ),
        _ => (Value::None, Value::None, Value::None),
    };
    let (tested, distinct, pruned, inadm) = match search {
        Some(s) => (s.tested as i64, s.seen.len() as i64, s.pruned_equiv as i64, s.inadmissible as i64),
        None => (0, 0, 0, 0),
    };
    let mut pairs: Vec<(Value, Value)> = vec![
        (surf("found"), Value::Bool(solved.is_some())),
        (surf("term"), term_v),
        (surf("term_str"), term_str_v),
        (surf("size"), size_v),
        (surf("tested"), Value::Int(tested)),
        (surf("distinct"), Value::Int(distinct)),
        (surf("pruned_equiv"), Value::Int(pruned)),
        (surf("inadmissible"), Value::Int(inadm)),
        (surf("saturated"), Value::Bool(saturated)),
        (surf("halt_reason"), surf(halt_reason)),
    ];
    pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
    let dict = Value::Dict(Arc::from(pairs));
    if field == Sym::default() {
        return dict;
    }
    let want = interner.resolve(field);
    if let Value::Dict(pairs) = &dict {
        for (k, v) in pairs.iter() {
            if let Value::Surface(SurfaceKind::Text, b) = k {
                if b.as_ref() == want.as_bytes() {
                    return v.clone();
                }
            }
        }
    }
    Value::None
}

// ---------------------------------------------------------------------------
// The entry point (term.rs's one-line handoff lands here).
// ---------------------------------------------------------------------------

#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_synth_enumerate(
    arena: &TermArena,
    examples_t: TermIdx,
    ops_t: Option<TermIdx>,
    consts_t: Option<TermIdx>,
    exclude_t: Option<TermIdx>,
    max_size: i64,
    max_candidates: i64,
    saturate_k: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let max_size = (if max_size <= 0 { DEFAULT_MAX_SIZE } else { max_size }) as usize;
    let max_candidates = (if max_candidates <= 0 { DEFAULT_MAX_CANDIDATES } else { max_candidates }) as u64;
    let saturate_k = (if saturate_k <= 0 { DEFAULT_SATURATE_K } else { saturate_k }) as usize;

    // --- Parse the spec (rows of {inputs, output}) ---
    // Q1: the OUTPUT type is no longer restricted to numeric/bool — any
    // Value the widened `canon`/`matches_target` can compare is a valid
    // spec target (str/None/Dict/Tuple/Set included). Only the SHAPE
    // (a Dict row with `inputs`/`output` keys) is still validated.
    let exv = evaluate(arena, examples_t, env, ctx);
    let rows = match items_of(&exv) {
        Some(r) => r,
        None => return finish(None, None, "invalid_examples", false, field, ctx.interner),
    };
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_placeholder: u32 = u32::MAX;
    let mut names: FxHashMap<Sym, String> = FxHashMap::default();
    let mut var_order: Vec<Sym> = Vec::new(); // first-appearance order across rows
    let mut envs: Vec<Env> = Vec::new();
    let mut target: Sig = Vec::new();
    let mut outputs: Vec<Value> = Vec::new();
    for row in &rows {
        let Value::Dict(pairs) = row else {
            return finish(None, None, "invalid_examples", false, field, ctx.interner);
        };
        let Some(Value::Dict(inputs)) = dict_get(pairs, "inputs", ctx.interner) else {
            return finish(None, None, "invalid_examples", false, field, ctx.interner);
        };
        let Some(output) = dict_get(pairs, "output", ctx.interner) else {
            return finish(None, None, "invalid_examples", false, field, ctx.interner);
        };
        let mut row_env: Env = SmallVec::new();
        for (k, v) in inputs.iter() {
            let (sym, name) = match k {
                Value::Str(s) => (*s, ctx.interner.resolve(*s).to_string()),
                _ => match value_str(k, ctx.interner) {
                    Some(name) => {
                        let sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, &name);
                        (sym, name)
                    }
                    None => return finish(None, None, "invalid_examples", false, field, ctx.interner),
                },
            };
            if !names.contains_key(&sym) {
                names.insert(sym, name);
                var_order.push(sym);
            }
            row_env.push((sym, v.clone()));
        }
        envs.push(row_env);
        target.push(canon(&output, ctx.interner));
        outputs.push(output);
    }

    // Arc4-S4: mint the two locally-fabricated bound-variable Syms every
    // list-op template uses (`__item`, `__acc` — the `local_sym`
    // precedent, same as every other placeholder this module mints).
    // Registered into `names` NOW (before `names` moves into `Search`)
    // so a winning candidate that uses them serializes with a stable
    // string, exactly like every real spec variable.
    let item_sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, "__item");
    names.entry(item_sym).or_insert_with(|| "__item".to_string());
    let acc_sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, "__acc");
    names.entry(acc_sym).or_insert_with(|| "__acc".to_string());
    // Arc6 tier-0 `tmpl:nested_reduction`: the SECOND bound variable — the
    // one a quantifier over the bound item needs (`for __inner in __item`).
    // Same `local_sym` precedent; minted unconditionally and cheaply so the
    // `names` table is complete before it moves into `Search`, exactly like
    // `__item`/`__acc`.
    let inner_sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, "__inner");
    names.entry(inner_sym).or_insert_with(|| "__inner".to_string());

    // --- Typed enumeration (Q1): a spec whose every variable value AND
    // output is string-shaped, with NO caller-declared `ops`, composes
    // over the string-oriented default inventory instead of arithmetic
    // DEFAULT_OPS — "a str spec never enumerates BitAnd" (the histogram's
    // own framing). Any explicit `ops` always wins; this only fills the
    // ABSENT-ops default.
    let is_str_val = |v: &Value| matches!(v, Value::Str(_) | Value::Surface(SurfaceKind::Text, _));
    let spec_is_string_shaped = !outputs.is_empty()
        && outputs.iter().all(is_str_val)
        && envs.iter().flat_map(|e| e.iter()).all(|(_, v)| is_str_val(v));

    // Arc4-S4: a spec whose OUTPUT is list-shaped, OR whose variable
    // values are CONSISTENTLY list-shaped (same var, every row) is
    // LIST-SHAPED — the third typed default, alongside string/arithmetic.
    // A spec can be both list-shaped (has a list var) and still want
    // arithmetic ops (e.g. a ratio over a filtered count and a length),
    // so the list-shaped default is arithmetic PLUS the list ops, never
    // a replacement for it.
    let spec_is_list_shaped = (!outputs.is_empty() && outputs.iter().all(is_listlike))
        || var_order.iter().any(|sym| {
            !envs.is_empty()
                && envs.iter().all(|e| {
                    e.iter()
                        .find(|(s, _)| s == sym)
                        .map(|(_, v)| is_listlike(v))
                        .unwrap_or(false)
                })
        });

    // --- Op inventory (caller-declared, else a TYPED default; unknown
    //     names ignored — generator.py's `if name in table`) ---
    // Arc6 tier-0: the tuple CONSTRUCTOR is offered only to a spec that
    // wants a tuple back (see `TUPLE_BUILD_OPS`).
    let spec_output_is_listlike = !outputs.is_empty() && outputs.iter().all(is_listlike);
    let default_ops: Vec<&str> = if spec_is_string_shaped {
        DEFAULT_STR_OPS.to_vec()
    } else if spec_is_list_shaped {
        let mut v: Vec<&str> =
            DEFAULT_OPS.iter().chain(LIST_EXTRA_OPS.iter()).copied().collect();
        if spec_output_is_listlike {
            v.extend(TUPLE_BUILD_OPS.iter().copied());
        }
        v
    } else {
        DEFAULT_OPS.to_vec()
    };
    let op_list: Vec<(String, OpKind)> = match ops_t {
        Some(t) => {
            let ov = evaluate(arena, t, env, ctx);
            match &ov {
                Value::None => default_ops
                    .iter()
                    .map(|n| (n.to_string(), table_kind(n).unwrap()))
                    .collect(),
                _ => match items_of(&ov) {
                    Some(items) => items
                        .iter()
                        .filter_map(|v| value_str(v, ctx.interner))
                        .filter_map(|n| table_kind(&n).map(|k| (n, k)))
                        .collect(),
                    None => return finish(None, None, "invalid_examples", false, field, ctx.interner),
                },
            }
        }
        None => default_ops
            .iter()
            .map(|n| (n.to_string(), table_kind(n).unwrap()))
            .collect(),
    };

    // --- Constant set: requested (default 0,1,2,-1) + integer-valued
    //     outputs (dedup, order preserved) ---
    let mut const_set: Vec<Value> = match consts_t {
        Some(t) => {
            let cv = evaluate(arena, t, env, ctx);
            match &cv {
                Value::None => vec![Value::Int(0), Value::Int(1), Value::Int(2), Value::Int(-1)],
                _ => match items_of(&cv) {
                    Some(items) => {
                        let mut out: Vec<Value> = Vec::new();
                        for it in items {
                            if !out.iter().any(|x| x == &it) {
                                out.push(it);
                            }
                        }
                        out
                    }
                    None => return finish(None, None, "invalid_examples", false, field, ctx.interner),
                },
            }
        }
        None => vec![Value::Int(0), Value::Int(1), Value::Int(2), Value::Int(-1)],
    };
    for out_v in &outputs {
        let iv = match out_v {
            Value::Int(i) => Some(*i),
            Value::Float(f) if *f == f.trunc() && f.is_finite() => Some(*f as i64),
            _ => None, // bools excluded, exactly as generator.py
        };
        if let Some(iv) = iv {
            let lit = Value::Int(iv);
            if !const_set.iter().any(|x| x == &lit) {
                const_set.push(lit);
            }
        }
    }
    // Q1 string consts: SPEC-DERIVED ONLY (substrings/chars of the
    // example strings, never a global alphabet) — every whole string
    // value observed (input or output) plus every distinct character
    // in any of them, dedup, order preserved. Bounded naturally by the
    // spec's own content size; no separate cap, no silent truncation.
    let mut str_consts: Vec<Value> = Vec::new();
    let mut push_str_const = |v: Value| {
        if !str_consts.iter().any(|x| x == &v) {
            str_consts.push(v);
        }
    };
    for row_env in &envs {
        for (_, v) in row_env.iter() {
            if let Some(s) = value_str(v, ctx.interner) {
                push_str_const(surf_string(s.clone()));
                for c in s.chars() {
                    push_str_const(surf_string(c.to_string()));
                }
            }
        }
    }
    for out_v in &outputs {
        if let Some(s) = value_str(out_v, ctx.interner) {
            push_str_const(surf_string(s.clone()));
            for c in s.chars() {
                push_str_const(surf_string(c.to_string()));
            }
        }
    }
    const_set.extend(str_consts);

    // --- The search ---
    let mut search = Search {
        scratch: TermArena::new(),
        names,
        envs,
        target,
        seen: FxHashSet::default(),
        by_size: vec![Vec::new(); max_size + 1],
        list_by_size: vec![Vec::new(); max_size + 1],
        tested: 0,
        pruned_equiv: 0,
        inadmissible: 0,
        max_candidates,
    };

    // --- Q1 `exclude`: pre-seed refuted candidates' signatures before
    // any leaf is registered, so an auto-appended const (above) can
    // never resurrect one (the P7-B fix). A malformed entry (bad JSON,
    // an op outside THIS call's own inventory, a reference to a
    // variable this spec doesn't have) is skipped — `exclude` is a
    // soft refutation hint, not part of the spec contract.
    if let Some(t) = exclude_t {
        let var_by_name: FxHashMap<String, Sym> =
            search.names.iter().map(|(s, n)| (n.clone(), *s)).collect();
        let ev = evaluate(arena, t, env, ctx);
        if let Some(items) = items_of(&ev) {
            for it in items {
                let Some(text) = value_str(&it, ctx.interner) else { continue };
                let Ok(j) = serde_json::from_str::<serde_json::Value>(&text) else { continue };
                // Parsed directly into the search's OWN scratch arena —
                // no interner mutation needed (Var names resolve
                // against the spec's own `var_by_name`; Lit values
                // never need interning, see `parse_excluded_term`).
                if let Some(idx) = parse_excluded_term(&j, &mut search.scratch, &var_by_name) {
                    search.preseed_excluded_idx(idx, ctx);
                }
            }
        }
    }

    macro_rules! reg {
        ($node:expr, $size:expr) => {
            match search.register($node, $size, ctx) {
                Reg::Solved(idx) => {
                    return finish(Some(&search), Some((idx, $size)), "solved", false, field, ctx.interner)
                }
                Reg::Budget => {
                    return finish(Some(&search), None, "budget", false, field, ctx.interner)
                }
                _ => {}
            }
        };
    }

    // size 1: leaves — vars first (first-appearance order), then consts.
    for sym in var_order.clone() {
        reg!(TermNode::Var { name: sym }, 1);
    }
    for c in const_set.clone() {
        reg!(TermNode::Lit { value: c }, 1);
    }

    // Arc4-S4: build the FilterList/MapList template pools — ONCE, never
    // counted toward `tested`/budget (the `exclude`-preseeding discipline:
    // these are shared subtrees, not enumerated candidates in their own
    // right). Skipped entirely (zero cost) unless the caller's op
    // inventory actually contains the relevant op name, so a spec that
    // never requests `FilterList`/`MapList` pays nothing for this.
    let filter_wanted = op_list.iter().any(|(n, _)| n == "FilterList");
    let map_wanted = op_list.iter().any(|(n, _)| n == "MapList");
    let template_cap = max_size + 1;
    let mut filter_templates_by_size: Vec<Vec<TermIdx>> = vec![Vec::new(); template_cap];
    let mut map_templates_by_size: Vec<Vec<TermIdx>> = vec![Vec::new(); template_cap];
    if filter_wanted || map_wanted {
        let numeric_consts: Vec<Value> = const_set
            .iter()
            .filter(|v| matches!(v, Value::Int(_) | Value::Float(_) | Value::Rational(_, _)))
            .cloned()
            .collect();
        // Scalar spec variables (excluding the bound __item/__acc, which
        // are never in var_order) — usable as a predicate/value operand
        // alongside the item, e.g. `item > threshold`.
        let scalar_vars: Vec<Sym> = var_order
            .iter()
            .cloned()
            .filter(|s| {
                search.envs.iter().all(|e| {
                    e.iter()
                        .find(|(vs, _)| vs == s)
                        .map(|(_, v)| matches!(v, Value::Int(_) | Value::Float(_) | Value::Bool(_) | Value::Rational(_, _)))
                        .unwrap_or(false)
                })
            })
            .collect();
        // Arc6 tier-0: the LIST-valued spec variables (same "consistently
        // typed on every row" rule as `scalar_vars` above) — the operand
        // `tmpl:item_in_listvar` needs.
        let list_vars: Vec<Sym> = var_order
            .iter()
            .cloned()
            .filter(|s| {
                search.envs.iter().all(|e| {
                    e.iter()
                        .find(|(vs, _)| vs == s)
                        .map(|(_, v)| is_listlike(v))
                        .unwrap_or(false)
                })
            })
            .collect();
        let push = |pool: &mut Vec<Vec<TermIdx>>, idx: TermIdx, sz: usize| {
            if sz < pool.len() {
                pool[sz].push(idx);
            }
        };
        if filter_wanted {
            const CMPS: [CmpKind; 5] =
                [CmpKind::Gt, CmpKind::Lt, CmpKind::Gte, CmpKind::Lte, CmpKind::Eq];
            for c in &numeric_consts {
                for k in CMPS {
                    // item OP c — size 3 (cmp + Var + Lit).
                    let iv = search.scratch.add(TermNode::Var { name: item_sym });
                    let lv = search.scratch.add(TermNode::Lit { value: c.clone() });
                    let t = search.scratch.add(build_cmp(k, iv, lv));
                    push(&mut filter_templates_by_size, t, 3);
                    // len(item) OP c — size 4 (cmp + Count(Var) + Lit).
                    let iv2 = search.scratch.add(TermNode::Var { name: item_sym });
                    let cnt = search.scratch.add(TermNode::Count { source: iv2 });
                    let lv2 = search.scratch.add(TermNode::Lit { value: c.clone() });
                    let t2 = search.scratch.add(build_cmp(k, cnt, lv2));
                    push(&mut filter_templates_by_size, t2, 4);
                }
            }
            for v in &scalar_vars {
                for k in CMPS {
                    // item OP (another scalar spec variable) — size 3.
                    let iv = search.scratch.add(TermNode::Var { name: item_sym });
                    let vv = search.scratch.add(TermNode::Var { name: *v });
                    let t = search.scratch.add(build_cmp(k, iv, vv));
                    push(&mut filter_templates_by_size, t, 3);
                }
            }

            // ---- Arc6 tier-0 `tmpl:item_in_listvar` ----------------------
            // `item in <list var>` / `item not in <list var>`, over the
            // SHIPPED `In` Term.  The pool already compares the bound item
            // to a scalar variable; it had no way to ask whether the item
            // is a MEMBER of another list-valued argument — the one thing a
            // two-list spec (`drop the elements of a that appear in b`)
            // needs.  General by construction: EVERY list-shaped spec
            // variable, never a named one.
            for v in &list_vars {
                // item in v — size 3 (In + Var + Var).
                let iv = search.scratch.add(TermNode::Var { name: item_sym });
                let vv = search.scratch.add(TermNode::Var { name: *v });
                let t = search.scratch.add(TermNode::In { member: iv, container: vv });
                push(&mut filter_templates_by_size, t, 3);
                // item not in v — size 4 (Not + the above).
                let iv2 = search.scratch.add(TermNode::Var { name: item_sym });
                let vv2 = search.scratch.add(TermNode::Var { name: *v });
                let inn = search.scratch.add(TermNode::In { member: iv2, container: vv2 });
                let notn = search.scratch.add(TermNode::Not { arg: inn });
                push(&mut filter_templates_by_size, notn, 4);
            }

            // ---- Arc6 tier-0 `tmpl:len_item_vs_var` ----------------------
            // `len(item) OP <scalar var>` — size 4.  The pool could already
            // compare `len(item)` to a CONSTANT and the bare item to a
            // VARIABLE; the missing cell of that 2x2 is the length against a
            // variable, which is what a spec that passes the target length
            // as an argument needs.  Filling a hole in an existing product,
            // not a new idea.
            for v in &scalar_vars {
                for k in CMPS {
                    let iv = search.scratch.add(TermNode::Var { name: item_sym });
                    let cnt = search.scratch.add(TermNode::Count { source: iv });
                    let vv = search.scratch.add(TermNode::Var { name: *v });
                    let t = search.scratch.add(build_cmp(k, cnt, vv));
                    push(&mut filter_templates_by_size, t, 4);
                }
            }

            // ---- Arc6 tier-0 `tmpl:nested_reduction` ---------------------
            // A QUANTIFIER OVER THE BOUND ITEM, inside the predicate:
            // `max/min/sum(<inner> for __inner in item) OP <rhs>`.  This is
            // S4 §4.4's named architectural seam — it widens the template
            // grammar from flat to ONE level of nesting (never to a full
            // recursive sub-search: the inner body is drawn from a pool, it
            // is not enumerated).
            //
            // The inner grammar is DELIBERATELY the SAME per-element
            // grammar the shipped MapList template pool already uses, only
            // over a second locally-fabricated bound variable — so the unit
            // introduces no new arithmetic and stays diffable against a pool
            // written from the operator list alone.  (Consequence, recorded
            // rather than patched around: the pool has {+, -, *} and no
            // `Mod`, so a DIVISIBILITY quantifier is not reachable here.)
            //
            // It is duplicated rather than factored out of the MapList pool
            // below on purpose: that pool is shipped, its construction order
            // fixes the arena layout and hence the enumeration order of
            // every already-passing list spec, and this widening must not
            // perturb it.
            {
                const REDUCERS: [&str; 3] = ["MaxOver", "MinOver", "Sum"];
                // The inner value pool, over `__inner` — same shapes, same
                // order as the MapList pool.
                let mut inner: Vec<(TermIdx, usize)> = Vec::new();
                let idn = search.scratch.add(TermNode::Var { name: inner_sym });
                inner.push((idn, 1));
                let iv = search.scratch.add(TermNode::Var { name: inner_sym });
                let cnt = search.scratch.add(TermNode::Count { source: iv });
                inner.push((cnt, 2));
                let iv2 = search.scratch.add(TermNode::Var { name: inner_sym });
                let cf = search.scratch.add(TermNode::CaseFold { text: iv2 });
                inner.push((cf, 2));
                for c in &numeric_consts {
                    let a1 = search.scratch.add(TermNode::Var { name: inner_sym });
                    let b1 = search.scratch.add(TermNode::Lit { value: c.clone() });
                    let plus = search.scratch.add(TermNode::Plus { items: vec![a1, b1] });
                    inner.push((plus, 3));
                    let a2 = search.scratch.add(TermNode::Var { name: inner_sym });
                    let b2 = search.scratch.add(TermNode::Lit { value: c.clone() });
                    let minus = search.scratch.add(TermNode::Minus { a: a2, b: b2 });
                    inner.push((minus, 3));
                    let a3 = search.scratch.add(TermNode::Lit { value: c.clone() });
                    let b3 = search.scratch.add(TermNode::Var { name: inner_sym });
                    let rminus = search.scratch.add(TermNode::Minus { a: a3, b: b3 });
                    inner.push((rminus, 3));
                    let a4 = search.scratch.add(TermNode::Var { name: inner_sym });
                    let b4 = search.scratch.add(TermNode::Lit { value: c.clone() });
                    let times = search.scratch.add(TermNode::Times { items: vec![a4, b4] });
                    inner.push((times, 3));
                }
                for k in [0i64, -1i64] {
                    let ivk = search.scratch.add(TermNode::Var { name: inner_sym });
                    let lit = search.scratch.add(TermNode::Lit { value: Value::Int(k) });
                    let ix = search.scratch.add(TermNode::IndexAt { seq: ivk, index: lit });
                    inner.push((ix, 3));
                }
                for v in &scalar_vars {
                    let ivv = search.scratch.add(TermNode::Var { name: inner_sym });
                    let vv = search.scratch.add(TermNode::Var { name: *v });
                    let ix = search.scratch.add(TermNode::IndexAt { seq: ivv, index: vv });
                    inner.push((ix, 3));
                }
                // The right-hand sides a reduction is compared against: the
                // same const/scalar-variable operands every other filter
                // template already uses.  Size 1 each.
                let mut rhs: Vec<TermIdx> = Vec::new();
                for c in &numeric_consts {
                    rhs.push(search.scratch.add(TermNode::Lit { value: c.clone() }));
                }
                for v in &scalar_vars {
                    rhs.push(search.scratch.add(TermNode::Var { name: *v }));
                }
                for red in REDUCERS {
                    for (body, body_sz) in inner.iter().copied() {
                        // R{source: Var(item), var_name: __inner, value: body}
                        //   size = 1 (the reduction) + 1 (Var(item)) + body
                        let red_sz = 2 + body_sz;
                        if red_sz + 2 >= template_cap {
                            continue; // cmp + rhs would overrun max_size
                        }
                        let src = search.scratch.add(TermNode::Var { name: item_sym });
                        let node = match red {
                            "MaxOver" => TermNode::MaxOver {
                                source: src, var_name: inner_sym, value: body, default: None },
                            "MinOver" => TermNode::MinOver {
                                source: src, var_name: inner_sym, value: body, default: None },
                            _ => TermNode::Sum {
                                source: src, var_name: inner_sym, value: body },
                        };
                        let r = search.scratch.add(node);
                        for rv in rhs.iter().copied() {
                            for k in CMPS {
                                let t = search.scratch.add(build_cmp(k, r, rv));
                                push(&mut filter_templates_by_size, t, red_sz + 2);
                            }
                        }
                    }
                }
            }
        }
        if map_wanted {
            // identity — size 1.
            let idn = search.scratch.add(TermNode::Var { name: item_sym });
            push(&mut map_templates_by_size, idn, 1);
            // len(item) — size 2.
            let iv = search.scratch.add(TermNode::Var { name: item_sym });
            let cnt = search.scratch.add(TermNode::Count { source: iv });
            push(&mut map_templates_by_size, cnt, 2);
            // lower(item) — size 2 (no-op/harmless on a non-string item —
            // DSL semantics govern, exactly like the top-level CaseFold op).
            let iv2 = search.scratch.add(TermNode::Var { name: item_sym });
            let cf = search.scratch.add(TermNode::CaseFold { text: iv2 });
            push(&mut map_templates_by_size, cf, 2);
            for c in &numeric_consts {
                // item + c, item - c, c - item, item * c — size 3 each.
                let a1 = search.scratch.add(TermNode::Var { name: item_sym });
                let b1 = search.scratch.add(TermNode::Lit { value: c.clone() });
                let plus = search.scratch.add(TermNode::Plus { items: vec![a1, b1] });
                push(&mut map_templates_by_size, plus, 3);
                let a2 = search.scratch.add(TermNode::Var { name: item_sym });
                let b2 = search.scratch.add(TermNode::Lit { value: c.clone() });
                let minus = search.scratch.add(TermNode::Minus { a: a2, b: b2 });
                push(&mut map_templates_by_size, minus, 3);
                let a3 = search.scratch.add(TermNode::Lit { value: c.clone() });
                let b3 = search.scratch.add(TermNode::Var { name: item_sym });
                let rminus = search.scratch.add(TermNode::Minus { a: a3, b: b3 });
                push(&mut map_templates_by_size, rminus, 3);
                let a4 = search.scratch.add(TermNode::Var { name: item_sym });
                let b4 = search.scratch.add(TermNode::Lit { value: c.clone() });
                let times = search.scratch.add(TermNode::Times { items: vec![a4, b4] });
                push(&mut map_templates_by_size, times, 3);
            }
            // item[0], item[-1] — size 3 each (extract from a nested
            // list/tuple element, e.g. "first of each sublist").
            for k in [0i64, -1i64] {
                let iv = search.scratch.add(TermNode::Var { name: item_sym });
                let lit = search.scratch.add(TermNode::Lit { value: Value::Int(k) });
                let ix = search.scratch.add(TermNode::IndexAt { seq: iv, index: lit });
                push(&mut map_templates_by_size, ix, 3);
            }
            for v in &scalar_vars {
                // item[other_scalar_var] — size 3 (e.g. "nth element").
                let iv = search.scratch.add(TermNode::Var { name: item_sym });
                let vv = search.scratch.add(TermNode::Var { name: *v });
                let ix = search.scratch.add(TermNode::IndexAt { seq: iv, index: vv });
                push(&mut map_templates_by_size, ix, 3);
            }
        }
    }

    let mut distinct_history: Vec<usize> = vec![search.seen.len()];

    // grow sizes 2..=max_size (generator.py's loop, partitions in the
    // same order; registration interleaved — see module docs).
    for size in 2..=max_size {
        for (name, kind) in &op_list {
            match kind {
                OpKind::Unary => {
                    // child has size-1
                    for child in search.by_size[size - 1].clone() {
                        reg!(build_op(name, &[child]), size);
                    }
                }
                OpKind::Binary => {
                    // child sizes sum to size-1
                    let terminal = name == "TupleOf"; // arc6 tier-0, see register_terminal
                    for sa in 1..size.saturating_sub(1) {
                        let sb = (size - 1) - sa;
                        if sb < 1 {
                            continue;
                        }
                        let left = search.by_size[sa].clone();
                        let right = search.by_size[sb].clone();
                        for ca in &left {
                            for cb in &right {
                                let node = build_op(name, &[*ca, *cb]);
                                let r = if terminal {
                                    search.register_terminal(node, size, ctx)
                                } else {
                                    search.register(node, size, ctx)
                                };
                                match r {
                                    Reg::Solved(idx) => return finish(
                                        Some(&search), Some((idx, size)), "solved", false, field, ctx.interner),
                                    Reg::Budget => return finish(
                                        Some(&search), None, "budget", false, field, ctx.interner),
                                    _ => {}
                                }
                            }
                        }
                    }
                }
                OpKind::Ternary => {
                    // cond+then+other sizes sum to size-1
                    if size < 4 {
                        continue;
                    }
                    for sc in 1..size - 2 {
                        for st in 1..(size - 1 - sc) {
                            let so = (size - 1) - sc - st;
                            if so < 1 {
                                continue;
                            }
                            let conds = search.by_size[sc].clone();
                            let thens = search.by_size[st].clone();
                            let others = search.by_size[so].clone();
                            for cc in &conds {
                                for tt in &thens {
                                    for oo in &others {
                                        reg!(build_op(name, &[*cc, *tt, *oo]), size);
                                    }
                                }
                            }
                        }
                    }
                }
                // --- Arc4-S4: list/iteration composition. Source only
                // ever drawn from `list_by_size` (never the general
                // `by_size` pool), so these arms are a genuine no-op for
                // any spec that never registers a list-shaped candidate —
                // the parity guarantee for every pre-existing spec. ---
                OpKind::ListUnary => {
                    // Honest MDL sizing: `size == 1 (this node) + extra
                    // (the shape's own hidden fixed leaves) + source_size`
                    // — see `list_unary_extra_cost`.
                    let extra = list_unary_extra_cost(name);
                    if size >= 1 + extra {
                        let src_size = size - 1 - extra;
                        if src_size >= 1 {
                            for child in search.list_by_size[src_size].clone() {
                                let node = build_list_unary(name, child, item_sym, acc_sym, &mut search.scratch);
                                reg!(node, size);
                            }
                        }
                    }
                }
                OpKind::ListFilter => {
                    // source size + predicate-template size sum to size-1
                    for sa in 1..size.saturating_sub(1) {
                        let st = (size - 1) - sa;
                        if st < 1 || st >= filter_templates_by_size.len() {
                            continue;
                        }
                        let srcs = search.list_by_size[sa].clone();
                        let tmpls = filter_templates_by_size[st].clone();
                        for s_ in &srcs {
                            for t_ in &tmpls {
                                reg!(build_list_ho(name, *s_, *t_, item_sym), size);
                            }
                        }
                    }
                }
                OpKind::ListMap => {
                    // source size + value-template size sum to size-1
                    for sa in 1..size.saturating_sub(1) {
                        let st = (size - 1) - sa;
                        if st < 1 || st >= map_templates_by_size.len() {
                            continue;
                        }
                        let srcs = search.list_by_size[sa].clone();
                        let tmpls = map_templates_by_size[st].clone();
                        for s_ in &srcs {
                            for t_ in &tmpls {
                                reg!(build_list_ho(name, *s_, *t_, item_sym), size);
                            }
                        }
                    }
                }
                // --- Arc6 tier-0: BOTH children list-shaped (`ConcatList`).
                // Same `list_by_size`-only sourcing discipline as every
                // other list arm, so this is a genuine no-op for a spec that
                // never registers a list-shaped candidate. Both operand
                // ORDERS are reached by the full sa x sb cross product, the
                // same way the ordinary Binary arm reaches (a,b) and (b,a).
                OpKind::ListBinary => {
                    let extra = list_binary_extra_cost(name);
                    if size >= 2 + extra {
                        let budget = size - 1 - extra; // sa + sb
                        for sa in 1..budget {
                            let sb = budget - sa;
                            if sb < 1 {
                                continue;
                            }
                            let left = search.list_by_size[sa].clone();
                            let right = search.list_by_size[sb].clone();
                            for ca in &left {
                                for cb in &right {
                                    let node = build_list_binary(
                                        name, *ca, *cb, item_sym, acc_sym, &mut search.scratch);
                                    reg!(node, size);
                                }
                            }
                        }
                    }
                }
            }
        }

        // Saturation early-stop: distinct-behaviour count not growing.
        distinct_history.push(search.seen.len());
        if distinct_history.len() > saturate_k {
            let first = distinct_history[distinct_history.len() - 1 - saturate_k];
            let last = *distinct_history.last().unwrap();
            if first == last {
                return finish(Some(&search), None, "saturated", true, field, ctx.interner);
            }
        }
    }

    finish(Some(&search), None, "max_size", false, field, ctx.interner)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::TypedGraph;

    struct Fixture {
        arena: TermArena,
        graph: TypedGraph,
        interner: Interner,
    }

    impl Fixture {
        fn new() -> Self {
            Self {
                arena: TermArena::new(),
                graph: TypedGraph::new(),
                interner: Interner::new(),
            }
        }

        /// Build the examples Value: rows of {inputs: {var: Int}, output}.
        fn rows(&mut self, rows: &[(&[(&str, i64)], Value)]) -> Value {
            let ik = Value::Str(self.interner.intern("inputs"));
            let ok = Value::Str(self.interner.intern("output"));
            let mut out: SmallVec<[Value; 4]> = SmallVec::new();
            for (inputs, output) in rows {
                let mut in_pairs: Vec<(Value, Value)> = inputs
                    .iter()
                    .map(|(n, v)| (Value::Str(self.interner.intern(n)), Value::Int(*v)))
                    .collect();
                in_pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
                let mut pairs: Vec<(Value, Value)> = vec![
                    (ik.clone(), Value::Dict(Arc::from(in_pairs))),
                    (ok.clone(), output.clone()),
                ];
                pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
                out.push(Value::Dict(Arc::from(pairs)));
            }
            Value::Tuple(Arc::new(out))
        }

        /// Arc4-S4: like `rows`, but inputs are arbitrary `Value`s (so a
        /// list-shaped spec can pass `Value::Tuple(...)` variable values,
        /// not just `Int`).
        fn rows_val(&mut self, rows: &[(&[(&str, Value)], Value)]) -> Value {
            let ik = Value::Str(self.interner.intern("inputs"));
            let ok = Value::Str(self.interner.intern("output"));
            let mut out: SmallVec<[Value; 4]> = SmallVec::new();
            for (inputs, output) in rows {
                let mut in_pairs: Vec<(Value, Value)> = inputs
                    .iter()
                    .map(|(n, v)| (Value::Str(self.interner.intern(n)), v.clone()))
                    .collect();
                in_pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
                let mut pairs: Vec<(Value, Value)> = vec![
                    (ik.clone(), Value::Dict(Arc::from(in_pairs))),
                    (ok.clone(), output.clone()),
                ];
                pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
                out.push(Value::Dict(Arc::from(pairs)));
            }
            Value::Tuple(Arc::new(out))
        }

        fn tup(items: &[i64]) -> Value {
            let v: SmallVec<[Value; 4]> = items.iter().map(|i| Value::Int(*i)).collect();
            Value::Tuple(Arc::new(v))
        }

        fn ops(&mut self, names: &[&str]) -> Value {
            let items: SmallVec<[Value; 4]> = names
                .iter()
                .map(|n| Value::Str(self.interner.intern(n)))
                .collect();
            Value::Tuple(Arc::new(items))
        }

        fn run(
            &mut self,
            examples: Value,
            ops: Option<Value>,
            max_size: i64,
            max_candidates: i64,
        ) -> Value {
            let ex = self.arena.add(TermNode::Lit { value: examples });
            let ops_t = ops.map(|o| self.arena.add(TermNode::Lit { value: o }));
            let t = self.arena.add(TermNode::SynthEnumerate {
                examples: ex,
                ops: ops_t,
                consts: None,
                exclude: None,
                max_size,
                max_candidates,
                saturate_k: 0,
                field: Sym::default(),
            });
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&self.graph, &self.interner);
            evaluate(&self.arena, t, &mut env, &mut ctx)
        }
    }

    fn dget(v: &Value, key: &str) -> Value {
        if let Value::Dict(pairs) = v {
            for (k, val) in pairs.iter() {
                if let Value::Surface(SurfaceKind::Text, b) = k {
                    if b.as_ref() == key.as_bytes() {
                        return val.clone();
                    }
                }
            }
        }
        Value::None
    }

    fn text(v: &Value) -> String {
        match v {
            Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(b).into_owned(),
            _ => String::new(),
        }
    }

    #[test]
    fn finds_x_plus_1() {
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 0)], Value::Int(1)),
            (&[("x", 1)], Value::Int(2)),
            (&[("x", 2)], Value::Int(3)),
        ]);
        let out = f.run(ex, None, 7, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
        assert_eq!(dget(&out, "size"), Value::Int(3));
        assert_eq!(text(&dget(&out, "term_str")), "(x + 1)");
        assert_eq!(text(&dget(&out, "halt_reason")), "solved");
        // Term-JSON is the engine's own wire form: parse + evaluate it back.
        let js = text(&dget(&out, "term"));
        let parsed: serde_json::Value = serde_json::from_str(&js).unwrap();
        assert_eq!(parsed["type"], "Plus");
    }

    #[test]
    fn returned_term_json_evaluates_on_the_engine() {
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 0)], Value::Int(1)),
            (&[("x", 1)], Value::Int(2)),
            (&[("x", 2)], Value::Int(3)),
        ]);
        let out = f.run(ex, None, 7, 0);
        let js = text(&dget(&out, "term"));
        let parsed: serde_json::Value = serde_json::from_str(&js).unwrap();
        let mut arena = TermArena::new();
        let idx =
            crate::jsonio::term_from_json(&parsed, &mut arena, &mut f.interner).expect("parses");
        let x = f.interner.intern("x");
        let mut env: Env = SmallVec::new();
        env.push((x, Value::Int(41)));
        let mut ctx = EvalCtx::new(&f.graph, &f.interner);
        assert_eq!(evaluate(&arena, idx, &mut env, &mut ctx), Value::Int(42));
    }

    #[test]
    fn finds_max_via_ifthenelse() {
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("a", 1), ("b", 2)], Value::Int(2)),
            (&[("a", 5), ("b", 3)], Value::Int(5)),
            (&[("a", 0), ("b", 0)], Value::Int(0)),
            (&[("a", 7), ("b", 9)], Value::Int(9)),
            (&[("a", 4), ("b", 1)], Value::Int(4)),
            (&[("a", 2), ("b", 8)], Value::Int(8)),
        ]);
        let ops = f.ops(&["Gt", "IfThenElse"]);
        let out = f.run(ex, Some(ops), 7, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
        assert_eq!(dget(&out, "size"), Value::Int(6));
        assert_eq!(text(&dget(&out, "term_str")), "(if (a > b) then a else b)");
    }

    #[test]
    fn equivalence_pruning_is_counted() {
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 0)], Value::Int(1)),
            (&[("x", 1)], Value::Int(2)),
            (&[("x", 2)], Value::Int(3)),
        ]);
        let out = f.run(ex, None, 7, 0);
        // (x + 0) ≡ x, Abs(x) ≡ x on this spec, … — pruning must fire
        // and the ledger must add up.
        let pruned = match dget(&out, "pruned_equiv") {
            Value::Int(n) => n,
            other => panic!("pruned_equiv not an Int: {other:?}"),
        };
        assert!(pruned > 0, "expected observational-equivalence pruning");
        let (tested, distinct, inadm) = (
            match dget(&out, "tested") { Value::Int(n) => n, _ => panic!() },
            match dget(&out, "distinct") { Value::Int(n) => n, _ => panic!() },
            match dget(&out, "inadmissible") { Value::Int(n) => n, _ => panic!() },
        );
        assert_eq!(tested, distinct + pruned + inadm);
    }

    #[test]
    fn saturation_is_honest() {
        let mut f = Fixture::new();
        // target 2.5 is not integer-valued → no const gets appended;
        // Abs over non-negative leaves mints NO new behaviour → the
        // distinct count freezes → saturated, found:false.
        let ex = f.rows(&[
            (&[("x", 1)], Value::Float(2.5)),
            (&[("x", 2)], Value::Float(2.5)),
        ]);
        let ops = f.ops(&["Abs"]);
        let out = f.run(ex, Some(ops), 9, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(false));
        assert_eq!(dget(&out, "saturated"), Value::Bool(true));
        assert_eq!(text(&dget(&out, "halt_reason")), "saturated");
        assert_eq!(dget(&out, "term"), Value::None);
        assert_eq!(dget(&out, "size"), Value::None);
    }

    #[test]
    fn budget_exhaustion_is_honest() {
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 0)], Value::Int(1)),
            (&[("x", 1)], Value::Int(2)),
            (&[("x", 2)], Value::Int(3)),
        ]);
        let out = f.run(ex, None, 7, 3);
        assert_eq!(dget(&out, "found"), Value::Bool(false));
        assert_eq!(text(&dget(&out, "halt_reason")), "budget");
        assert_eq!(dget(&out, "tested"), Value::Int(3)); // never exceeds the budget
        assert_eq!(dget(&out, "saturated"), Value::Bool(false));
    }

    #[test]
    fn op_restriction_is_respected() {
        let mut f = Fixture::new();
        let spec: &[(&[(&str, i64)], Value)] = &[
            (&[("x", 1)], Value::Int(2)),
            (&[("x", 2)], Value::Int(4)),
            (&[("x", 3)], Value::Int(6)),
        ];
        // Plus-only world: the doubling has to be (x + x).
        let ex = f.rows(spec);
        let ops = f.ops(&["Plus"]);
        let out = f.run(ex, Some(ops), 7, 0);
        assert_eq!(text(&dget(&out, "term_str")), "(x + x)");
        // Times-only world: the SAME behaviour is (x * 2).
        let ex = f.rows(spec);
        let ops = f.ops(&["Times"]);
        let out = f.run(ex, Some(ops), 7, 0);
        assert_eq!(text(&dget(&out, "term_str")), "(x * 2)");
        let js = text(&dget(&out, "term"));
        assert!(js.contains("\"Times\"") && !js.contains("\"Plus\""));
    }

    #[test]
    fn deterministic_same_inputs_same_result() {
        let run_once = || {
            let mut f = Fixture::new();
            let ex = f.rows(&[
                (&[("a", 1), ("b", 2), ("c", 3)], Value::Int(5)),
                (&[("a", 2), ("b", 3), ("c", 1)], Value::Int(7)),
                (&[("a", 0), ("b", 5), ("c", 4)], Value::Int(4)),
                (&[("a", 3), ("b", 3), ("c", 0)], Value::Int(9)),
                (&[("a", 2), ("b", 2), ("c", 2)], Value::Int(6)),
                (&[("a", 4), ("b", 1), ("c", 5)], Value::Int(9)),
            ]);
            let out = f.run(ex, None, 6, 0);
            (
                text(&dget(&out, "term")),
                text(&dget(&out, "term_str")),
                dget(&out, "tested"),
                dget(&out, "distinct"),
                dget(&out, "found"),
            )
        };
        let a = run_once();
        let b = run_once();
        assert_eq!(a, b);
        assert_eq!(a.4, Value::Bool(true));
    }

    #[test]
    fn invalid_examples_are_honest_not_a_panic() {
        let mut f = Fixture::new();
        let out = f.run(Value::Int(5), None, 7, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(false));
        assert_eq!(text(&dget(&out, "halt_reason")), "invalid_examples");
        // Row without an output key is invalid too.
        let ik = Value::Str(f.interner.intern("inputs"));
        let row = Value::Dict(Arc::from(vec![(ik, Value::Dict(Arc::from(Vec::new())))]));
        let ex = Value::Tuple(Arc::new(smallvec::smallvec![row]));
        let out = f.run(ex, None, 7, 0);
        assert_eq!(text(&dget(&out, "halt_reason")), "invalid_examples");
    }

    #[test]
    fn field_selector_and_purity() {
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 0)], Value::Int(1)),
            (&[("x", 1)], Value::Int(2)),
        ]);
        let nodes_before = f.graph.node_count();
        let ex_t = f.arena.add(TermNode::Lit { value: ex });
        let field = f.interner.intern("found");
        let t = f.arena.add(TermNode::SynthEnumerate {
            examples: ex_t,
            ops: None,
            consts: None,
            exclude: None,
            max_size: 7,
            max_candidates: 0,
            saturate_k: 0,
            field,
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&f.graph, &f.interner);
        let out = evaluate(&f.arena, t, &mut env, &mut ctx);
        assert_eq!(out, Value::Bool(true)); // field selects one key
        assert_eq!(f.graph.node_count(), nodes_before); // pure: no substrate mutation
    }

    #[test]
    fn abs_of_shifted_var_is_found() {
        // generator.py demo spec 4: f(x) = |x - 2| (size 4).
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", -3)], Value::Int(5)),
            (&[("x", -1)], Value::Int(3)),
            (&[("x", 0)], Value::Int(2)),
            (&[("x", 1)], Value::Int(1)),
            (&[("x", 2)], Value::Int(0)),
            (&[("x", 3)], Value::Int(1)),
            (&[("x", 5)], Value::Int(3)),
        ]);
        let out = f.run(ex, None, 7, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
        // MDL floor: |x−2| needs Abs over a Minus — size 4. Whatever
        // size-4 equivalent the fixed order lands on, the size is the
        // claim (exact-term parity vs generator.py is the pytest gate).
        assert_eq!(dget(&out, "size"), Value::Int(4));
    }

    // ----------------------------------------------------------------- //
    // Arc4-S4: list/iteration composition (search reach).
    // ----------------------------------------------------------------- //

    #[test]
    fn list_len_is_found() {
        // "count the length of a list" — Len(xs), size 2.
        let mut f = Fixture::new();
        let ex = f.rows_val(&[
            (&[("xs", Fixture::tup(&[1, 2, 3]))], Value::Int(3)),
            (&[("xs", Fixture::tup(&[4, 5]))], Value::Int(2)),
            (&[("xs", Fixture::tup(&[]))], Value::Int(0)),
        ]);
        let ops = f.ops(&["Len"]);
        let out = f.run(ex, Some(ops), 9, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
        assert_eq!(text(&dget(&out, "term_str")), "len(xs)");
        assert_eq!(dget(&out, "size"), Value::Int(2));
    }

    #[test]
    fn list_sum_is_found() {
        // "flatten and sum" (task 65's shape, one level) — SumList(xs).
        let mut f = Fixture::new();
        let ex = f.rows_val(&[
            (&[("xs", Fixture::tup(&[1, 2, 3]))], Value::Int(6)),
            (&[("xs", Fixture::tup(&[4, 5]))], Value::Int(9)),
            (&[("xs", Fixture::tup(&[]))], Value::Int(0)),
        ]);
        let ops = f.ops(&["SumList"]);
        let out = f.run(ex, Some(ops), 9, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
        // Sum{source, value:Var(item)} — size 1 + 1(source) + 1(value) = 3.
        assert_eq!(dget(&out, "size"), Value::Int(3));
    }

    #[test]
    fn list_max_minus_min_is_found() {
        // "max abs diff" (task 145's shape) — MaxList(xs) - MinList(xs),
        // demonstrating a list-reduction's SCALAR output composing
        // further with a pre-existing arithmetic op (Minus).
        let mut f = Fixture::new();
        let ex = f.rows_val(&[
            (&[("xs", Fixture::tup(&[3, 1, 9, 2]))], Value::Int(8)),
            (&[("xs", Fixture::tup(&[5, 5]))], Value::Int(0)),
            (&[("xs", Fixture::tup(&[-2, 4, 1]))], Value::Int(6)),
        ]);
        let ops = f.ops(&["MaxList", "MinList", "Minus"]);
        let out = f.run(ex, Some(ops), 9, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
        assert_eq!(dget(&out, "size"), Value::Int(7));
    }

    #[test]
    fn list_count_positives_via_filter_and_len() {
        // "count positives" (task 66's exact shape) — Len(FilterList(xs,
        // item, item > -1)) — Count(FilterList) composing THROUGH
        // list_by_size (FilterList's Tuple output is itself list-typed).
        let mut f = Fixture::new();
        let ex = f.rows_val(&[
            (&[("xs", Fixture::tup(&[1, -2, 3, -4]))], Value::Int(2)),
            (&[("xs", Fixture::tup(&[-1, -2]))], Value::Int(0)),
            (&[("xs", Fixture::tup(&[5, 6, 7]))], Value::Int(3)),
        ]);
        let ops = f.ops(&["Len", "FilterList"]);
        let out = f.run(ex, Some(ops), 9, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
    }

    #[test]
    fn list_map_index0_extracts_first_of_each_sublist() {
        // "first element of each sublist" (task 460's shape) — MapList
        // over a list-of-lists, value template IndexAt(item, 0).
        let mut f = Fixture::new();
        fn tuple_of(items: Vec<Value>) -> Value {
            let v: SmallVec<[Value; 4]> = items.into_iter().collect();
            Value::Tuple(Arc::new(v))
        }
        fn list_of(items: Vec<Value>) -> Value {
            let v: SmallVec<[Value; 4]> = items.into_iter().collect();
            Value::List(Arc::new(v))
        }
        let a = tuple_of(vec![Fixture::tup(&[1, 2]), Fixture::tup(&[3, 4])]);
        let b = tuple_of(vec![Fixture::tup(&[9]), Fixture::tup(&[7, 8, 9])]);
        // 2026-08-02 (ARC6 value layer): `MapList` now returns a
        // `Value::List` -- its own doc always called it "the faithful
        // target for a Python LIST comprehension", and in CPython
        // `[x[0] for x in t]` is a LIST even when `t` is a tuple. The pin
        // moved in the improvement direction: a spec whose expected output
        // is a LIST is what `MapList` solves.
        let expect_a = list_of(vec![Value::Int(1), Value::Int(3)]);
        let expect_b = list_of(vec![Value::Int(9), Value::Int(7)]);
        let ex = f.rows_val(&[
            (&[("lists", a.clone())], expect_a),
            (&[("lists", b.clone())], expect_b),
        ]);
        let ops = f.ops(&["MapList"]);
        let out = f.run(ex, Some(ops), 9, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));

        // ... AND THE REFUTING DIRECTION, which is the whole point of the
        // value layer: the SAME spec with a TUPLE-typed expected output is
        // NOT solved by `MapList`, because a list comprehension does not
        // produce a tuple. Before this rung the two were indistinguishable.
        let mut f2 = Fixture::new();
        let ex_t = f2.rows_val(&[
            (&[("lists", a)], tuple_of(vec![Value::Int(1), Value::Int(3)])),
            (&[("lists", b)], tuple_of(vec![Value::Int(9), Value::Int(7)])),
        ]);
        let ops_t = f2.ops(&["MapList"]);
        let out_t = f2.run(ex_t, Some(ops_t), 9, 0);
        assert_eq!(dget(&out_t, "found"), Value::Bool(false));
    }

    #[test]
    fn typed_pruning_scalar_spec_never_touches_list_by_size() {
        // "budget honesty on the new ops" / "typed pruning" gate: a
        // plain scalar spec's op_list never contains a list op name
        // (default_ops is unchanged when the spec is not list-shaped),
        // so a list op requested EXPLICITLY over a scalar-only spec must
        // find NOTHING to draw on (list_by_size stays empty for every
        // size) and the run must halt honestly (never panic, never
        // silently "find" a spurious solution).
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 1)], Value::Int(2)),
            (&[("x", 2)], Value::Int(4)),
            (&[("x", 3)], Value::Int(6)),
        ]);
        let ops = f.ops(&["Len", "SumList", "FilterList", "MapList"]);
        let out = f.run(ex, Some(ops), 9, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(false));
        // tested stays 0: leaves (x, consts) never solve, and no list op
        // ever has a `list_by_size` entry to draw from at any size — the
        // loop bodies are true no-ops, matching a saturation halt as soon
        // as the leaf-only distinct count stops growing.
        assert!(matches!(text(&dget(&out, "halt_reason")).as_str(), "saturated" | "max_size"));
    }

    #[test]
    fn list_shaped_default_ops_include_list_ops_with_no_explicit_ops() {
        // The third typed default (`spec_is_list_shaped`): a list-valued
        // spec with `ops=None` must still be reachable via a list op —
        // parity with the string-shaped default's own established test
        // shape (`op_restriction_is_respected`), but for the DEFAULT
        // selection path instead of an explicit override.
        let mut f = Fixture::new();
        let ex = f.rows_val(&[
            (&[("xs", Fixture::tup(&[1, 2, 3]))], Value::Int(3)),
            (&[("xs", Fixture::tup(&[4, 5]))], Value::Int(2)),
            (&[("xs", Fixture::tup(&[]))], Value::Int(0)),
        ]);
        let out = f.run(ex, None, 9, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
    }

    #[test]
    fn non_list_spec_default_ops_are_byte_unchanged() {
        // Parity guarantee, stated as its own gate: a spec with no list-
        // shaped variable or output gets the EXACT same DEFAULT_OPS
        // search as before this widening — same term, same size, same
        // tested count as the pre-existing `finds_x_plus_1` fixture.
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 0)], Value::Int(1)),
            (&[("x", 1)], Value::Int(2)),
            (&[("x", 2)], Value::Int(3)),
        ]);
        let out = f.run(ex, None, 7, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
        assert_eq!(dget(&out, "size"), Value::Int(3));
        assert_eq!(text(&dget(&out, "term_str")), "(x + 1)");
    }

    #[test]
    fn list_op_json_round_trips_through_jsonio() {
        // A winning list-op candidate's Term-JSON must parse back through
        // the GENERAL `jsonio::term_from_json` parser (the same one
        // `domains.prog_synthesis.run_enumerate` relies on downstream)
        // and evaluate identically — the same discipline
        // `returned_term_json_evaluates_on_the_engine` established for
        // the arithmetic case.
        let mut f = Fixture::new();
        let ex = f.rows_val(&[
            (&[("xs", Fixture::tup(&[1, 2, 3]))], Value::Int(3)),
            (&[("xs", Fixture::tup(&[4, 5]))], Value::Int(2)),
            (&[("xs", Fixture::tup(&[]))], Value::Int(0)),
        ]);
        let ops = f.ops(&["Len"]);
        let out = f.run(ex, Some(ops), 9, 0);
        let js = text(&dget(&out, "term"));
        let parsed: serde_json::Value = serde_json::from_str(&js).unwrap();
        assert_eq!(parsed["type"], "Count");
        let mut arena = TermArena::new();
        let idx =
            crate::jsonio::term_from_json(&parsed, &mut arena, &mut f.interner).expect("parses");
        let xs = f.interner.intern("xs");
        let mut env: Env = SmallVec::new();
        env.push((xs, Fixture::tup(&[10, 20, 30, 40])));
        let mut ctx = EvalCtx::new(&f.graph, &f.interner);
        assert_eq!(evaluate(&arena, idx, &mut env, &mut ctx), Value::Int(4));
    }

    #[test]
    fn exclude_contract_is_intact_for_old_shapes() {
        // Old-shape `exclude` parsing (arithmetic-only) must be entirely
        // unaffected by this widening: excluding a REFUTED (wrong)
        // candidate's behaviour (`x - 5`, which disagrees with the
        // `x + 1` target on every row) must not disturb the search at
        // all — the real solution is still found, same term, same size,
        // exactly as the unexcluded `finds_x_plus_1` fixture.
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 0)], Value::Int(1)),
            (&[("x", 1)], Value::Int(2)),
            (&[("x", 2)], Value::Int(3)),
        ]);
        let excl_json = serde_json::json!({
            "type": "Minus",
            "a": {"type": "Var", "name": "x"},
            "b": {"type": "Lit", "value": 5},
        })
        .to_string();
        let ex_t = f.arena.add(TermNode::Lit { value: ex });
        let excl_t = f.arena.add(TermNode::Lit {
            value: Value::Tuple(Arc::new(smallvec::smallvec![surf_string(excl_json)])),
        });
        let t = f.arena.add(TermNode::SynthEnumerate {
            examples: ex_t,
            ops: None,
            consts: None,
            exclude: Some(excl_t),
            max_size: 9,
            max_candidates: 0,
            saturate_k: 0,
            field: Sym::default(),
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&f.graph, &f.interner);
        let out = evaluate(&f.arena, t, &mut env, &mut ctx);
        assert_eq!(dget(&out, "found"), Value::Bool(true));
        assert_eq!(text(&dget(&out, "term_str")), "(x + 1)");
        assert_eq!(dget(&out, "size"), Value::Int(3));
    }
}
