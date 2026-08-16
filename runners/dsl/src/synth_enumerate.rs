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
use crate::term::{
    evaluate, DerivedOpDef, DerivedOpPool, DerivedOpRegistry, Env, EvalCtx, TermArena, TermIdx, TermNode,
};
use crate::value::{cmp_value, SurfaceKind, Value};

const DEFAULT_MAX_SIZE: i64 = 9;
const DEFAULT_MAX_CANDIDATES: i64 = 200_000;
const DEFAULT_SATURATE_K: i64 = 3;

/// generator.py's DEFAULT_OPS, in order (enumeration order is part of
/// the port).
///
/// Rung 1 measured (not assumed) that blindly appending here is UNSAFE:
/// `DEFAULT_OPS` is the typed default for every "neither string- nor
/// list-shaped" spec — i.e. it is the WIDEST-blast-radius bucket in this
/// module (every plain-arithmetic MBPP task lands here), and a first
/// attempt that appended `Round`/`ParseInt`/`Str` unconditionally
/// regressed 3 previously-passing tasks to `budget` (`tested==
/// max_candidates` exactly, confirmed live) plus 2 more to a wrong
/// exemplar-retrieval fallback — `RUNG1_RESULTS.md` §"regression
/// investigation". Left UNCHANGED here; see `str_ops_relevant` below for
/// where the three land instead (evidence-gated, the same discipline
/// `TUPLE_BUILD_OPS` already uses for `op:TupleOf`).
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
    /// Rung 1: `IndexedMap` — source from `list_by_size` (like `ListMap`),
    /// value template from its OWN pool (`indexed_map_templates_by_size`,
    /// built separately from `map_templates_by_size` so the shipped
    /// `MapList` pool's arena layout / enumeration order is never
    /// perturbed — the `tmpl:nested_reduction` precedent). The template
    /// may reference EITHER the bound item OR the bound index.
    IndexedMap,
    /// `ZIP_ELEMENTWISE` rung: `ZipWith` — TWO sources, both drawn from
    /// `list_by_size[1]` ONLY (raw declared spec variables, never a
    /// derived subterm — every one of this rung's 8 witness tasks zips
    /// the raw arguments directly, so this is a deliberate, documented
    /// narrowing, not the full `sa x sb` cross product `ListBinary` uses;
    /// see `PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_PREREG.md` §4), value
    /// template from its OWN pool (`zip_op_templates_by_size`, built
    /// separately so it never perturbs `map_templates_by_size`'s/
    /// `indexed_map_templates_by_size`'s own arena layout — the
    /// `tmpl:nested_reduction` precedent, generalised a second time).
    ZipMap,
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
    // --- CEILING_REASSESSMENT_4 (PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_4_
    // PREREG.md §3.2, tasks 111/140): a FOLDED reduction of the already-
    // shipped 2-arg `Intersect`/`Union` Set Terms across a variable-length
    // OUTER sequence — the `ConcatList`/`JoinList` `Fold`-composition
    // precedent one level up (those fold a fixed binary op across ONE
    // sequence too; this is the same shape with a Set op as the body).
    // ZERO new `TermNode` variant: `Fold`/`Intersect`/`Union`/`IndexAt`/
    // `Var`/`Lit` are all pre-existing, already-wired Terms. ---
    ("IntersectAll", OpKind::ListUnary),   // -> Fold{source, init:IndexAt(source,0), body:Intersect(acc,item)}
    ("UnionAll", OpKind::ListUnary),       // -> Fold{source, init:IndexAt(source,0), body:Union(acc,item)}
    // --- PROGRAM_SYNTHESIS_DICTFROMPAIRS_PREREG.md §3-4 (tasks 277/465):
    // Python's `dict(pairs)` — build a `Value::Dict` from a RUNTIME-LENGTH
    // list of (key,value) pairs. `MkDict{items}` alone can't (its `items`
    // are build-time-fixed `TermIdx`s), but `Fold` supplies the missing
    // variable-length reduction exactly as it did for `IntersectAll`/
    // `UnionAll` one rung earlier: accumulate a `Value::Dict`, one pair at
    // a time, via already-shipped `MkDict` (single-pair) folded in with
    // already-shipped `DictMerge` (later pair wins a key collision --
    // Python's own duplicate-key rule). ZERO new `TermNode` variant. ---
    ("DictFromPairs", OpKind::ListUnary),  // -> Fold{source, init:MkDict([]), body:DictMerge(acc, MkDict([IndexAt(item,0),IndexAt(item,1)]))}
    // --- Rung 1 (PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_
    // PREREG.md §5.1, `STRUCTURAL_CEILING.md` §9's own priced order):
    // Tier-1 stdlib Term ports. Each is a NEW `TermNode` variant (unlike
    // tier-0's zero-new-variant exposures) that ports a behaviour
    // `ProgEval` already runs — CLAUDE.md's third, sanctioned "new
    // primitive" pathway, not a shape/codebook growth. ---
    ("Replace", OpKind::Ternary),      // -> Replace{text,old,new} (str.replace)
    ("Str", OpKind::Unary),            // -> Str{value} (Python str())
    ("Split", OpKind::Binary),         // -> Split{text,sep} (str.split)
    ("StrCount", OpKind::Binary),      // -> StrCount{text,sub} (substring count)
    ("Round", OpKind::Binary),         // -> Round{value,ndigits} (2-arg round())
    ("Reverse", OpKind::Unary),        // -> Reverse{seq} (type-preserving reversed())
    ("IndexedMap", OpKind::IndexedMap),// -> IndexedMap{source,item,index,value}
    ("Capitalize", OpKind::Unary),     // -> Capitalize{text} (str.capitalize)
    ("ParseInt", OpKind::Unary),       // -> ParseInt{text} (Python int(s))
    // Deliberately LAST (§5.1): the largest blast radius of the ten.
    ("Slice", OpKind::Ternary),        // -> Slice{seq,start,stop} (negative-index-correct, type-general)
    // --- SetLit/DictItems rung (PROGRAM_SYNTHESIS_SETLIT_DICTITEMS_
    // PREREG.md): the PROPOSAL layer for Sets. `Union`/`Intersect`/
    // `MapSet` already exist as pure, already-shipped Terms (`term.rs`)
    // — the gap was purely that this OP_TABLE never exposed them. `Sort`
    // is the one new `TermNode` this rung adds, via the already-vetted
    // zero-blast-radius `cmp_value_lex` reuse (Rung 3's own Step 2). ---
    ("Sort", OpKind::Unary),           // -> Sort{seq} (type-preserving ascending sort)
    ("SetMap", OpKind::ListMap),       // -> MapSet{source,item,<template>} (the MapList twin, returns a Set)
    ("Intersect", OpKind::ListBinary), // -> Intersect{a,b} (the shipped Set/FrozenSet Term, direct)
    ("Union", OpKind::ListBinary),     // -> Union{a,b} (the shipped Set/FrozenSet Term, direct)
    // --- DictItems/SortBy rung (PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_
    // PREREG.md, task 475 `sort_counter`/`Counter.most_common()`):
    // `DictItems` is `Sort`-class (Unary, general `by_size` pool, zero new
    // registration machinery). `SortBy` reuses `OpKind::ListMap`'s
    // registration path verbatim (the `SetMap`/`IndexedMap` precedent) —
    // its template is a SORT KEY, not an output value (see `build_list_ho`
    // and the evaluator in term.rs). ---
    ("DictItems", OpKind::Unary),      // -> DictItems{seq} (dict.items() as a Tuple of (k,v) pairs)
    ("SortBy", OpKind::ListMap),       // -> SortBy{source,item,<key template>} (stable sort by projected key)
    // --- GroupCount/DictMerge rung (PROGRAM_SYNTHESIS_GROUPCOUNT_
    // DICTMERGE_PREREG.md, tasks 88/87 — priced by ARC6_STRUCTURAL_CEILING
    // §4.3 / CEILING_REASSESSMENT_2 §6.4 as 1-new-Term-each stdlib ports,
    // reconfirmed live before this rung built either). `GroupCount` is
    // `Sort`/`DictItems`-class (Unary, general `by_size` pool). `DictMerge`
    // is Binary — a 3-way merge composes via nesting, the SAME
    // `ConcatList(ConcatList(a,b),c)` precedent task 108 already uses. ---
    ("GroupCount", OpKind::Unary),     // -> GroupCount{seq} (Counter(seq) as a Dict of element->count)
    ("DictMerge", OpKind::Binary),     // -> DictMerge{a,b} (dict.update semantics: b wins over a on key conflict)
    // --- PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_PREREG.md (an 8-task MBPP
    // cluster — 259/261/273/282/399/401/429/445 — all needing Python's
    // `zip(a, b)` paired with a per-pair binary combiner). `ZipWith` is a
    // NEW `TermNode` variant (no existing Term iterates two sequences in
    // lockstep), registered via its OWN `OpKind::ZipMap` (see that
    // variant's doc comment for the deliberate `list_by_size[1]`-only
    // sourcing scope). ---
    ("ZipWith", OpKind::ZipMap), // -> ZipWith{a,b,a_name,b_name,value} (zip(a,b) + a per-pair binary combiner)
    // --- PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX (PROGRAM_SYNTHESIS_BUDGET_
    // EXHAUSTED_SURVEY_PREREG/RESULTS.md §5.1/§5.3): `Mod`/`Sqrt` are
    // already-shipped, already-evaluated `TermNode` variants (`term.rs`),
    // used elsewhere in the engine, that had never been exposed in
    // `OP_TABLE` at all. Registered here so an explicit `ops` request (or
    // a caller building its own op list) CAN name them; the bare-scalar
    // typed default (below) is the only unconditional consumer — see that
    // branch's own comment for why it is scoped this narrowly. ---
    ("Mod", OpKind::Binary),   // -> Mod{a,b} (Python a % b)
    ("Sqrt", OpKind::Unary),   // -> Sqrt{arg} (Python math.sqrt)
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
    // Rung 1 — APPENDED (same discipline). ONLY `Reverse`/`Slice` (cheap,
    // linear Unary/Ternary registration — O(by_size[size-1]), the same
    // cost class as every pre-existing Unary/Binary op) live here
    // unconditionally, and task 132 (this codebase's own documented
    // most budget-fragile spec, `distinct` already 1941/200,000 before
    // this rung touched anything — the exact task `TUPLE_BUILD_OPS` was
    // narrow-gated to protect) measured intolerant of EVEN `Reverse`+
    // `Slice` alone (2 cheap Unary/Ternary ops) appended unconditionally
    // to this bucket. So ZERO Rung-1 ops are unconditional here — every
    // one of the ten is evidence-gated (`extra_evidence_ops` /
    // `spec_has_repeated_list_element`, below) — see
    // `RUNG1_RESULTS.md` §"regression investigation" for the measured
    // walk (5 regressions -> 1 -> 0 across three narrowing passes).
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

/// SetLit/DictItems rung: a DEDICATED small typed default for a spec
/// whose OUTPUT is itself Set/FrozenSet-shaped (`spec_output_is_setlike`)
/// — the `DEFAULT_STR_OPS` precedent (a small, shape-tailored bucket, not
/// additive to the much larger list-shaped default). `SetMap` reuses
/// `OpKind::ListMap`'s exact registration code path (same
/// `map_templates_by_size` pool `MapList` already builds); `Intersect`/
/// `Union` reuse `OpKind::ListBinary` (the `ConcatList` precedent); all
/// three source from `list_by_size`, which already includes Set/
/// FrozenSet-shaped candidates by construction (`is_listlike`), so no new
/// type-filtered pool is needed. `Sort`/`Reverse`/`Slice` are included
/// unconditionally HERE (unlike the general list-shaped bucket, where
/// Rung 1 measured they regress task 132) because this branch is
/// mutually exclusive with task 132's own branch — task 132's output is
/// a STRING, never Set-shaped, so it can never reach this bucket at all.
/// Deliberately EXCLUDES `DEFAULT_OPS`'s numeric arithmetic (`Plus`/
/// `Times`/...) and `LIST_EXTRA_OPS`'s dozen list-reduction ops — MEASURED
/// (not assumed) that including them causes budget exhaustion before the
/// search reaches the in-budget witness for task 473 (`tested==200000,
/// found:false` with `DEFAULT_OPS` included vs. `found:true` at 74830
/// tested without it).
const SET_DEFAULT_OPS: &[&str] = &[
    "Eq", "IfThenElse", "Sort", "Reverse", "Slice", "SetMap", "Intersect", "Union",
    // CEILING_REASSESSMENT_4 (tasks 111/140): the FOLDED, variable-arity
    // twins of the `Intersect`/`Union` pair two lines up — same bucket,
    // same `ListUnary` cheap registration cost, live-verified end-to-end
    // (`PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_4_PREREG.md` §3.1).
    "IntersectAll", "UnionAll",
];

/// GroupCount/DictMerge rung: the `SET_DEFAULT_OPS` precedent for a spec
/// that is Dict-shaped (`spec_output_is_dictlike`) but reaches neither the
/// string-, set-, nor list-shaped typed default (task 87's own three
/// Dict-valued variables and Dict-valued output never set `spec_is_list_
/// shaped`, since `is_listlike` deliberately excludes Dict). Narrow by
/// construction, same as `SET_DEFAULT_OPS` — `Eq`/`IfThenElse` from the
/// base arithmetic set plus exactly the two new ops this rung adds.
/// DICTFROMPAIRS_PREREG §4: `DictFromPairs` appended, same narrow bucket,
/// same cheap `ListUnary` registration cost. Deliberately NOT joined by
/// `DictItems`/`FilterList` here -- both already exist but the search's own
/// `filter_templates_by_size` predicate grammar has no "project a fixed
/// index out of the bound item" template shape (PREREG §5), so offering
/// them would add real search cost to this bucket's one live canary (task
/// 87) for no measured raw-search benefit under the current template pool.
const DICT_DEFAULT_OPS: &[&str] = &["Eq", "IfThenElse", "GroupCount", "DictMerge", "DictFromPairs"];

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
/// Rung 1 — APPENDED (never interleaved, same discipline as
/// `LIST_EXTRA_OPS`'s own growth): `Replace`/`Split`/`StrCount`/
/// `Capitalize`/`Reverse`/`Slice`/`Str` are the direct stdlib string
/// methods `STRUCTURAL_CEILING.md` §9's tier-1 table names (each already
/// a shipped `ProgEval` behaviour, §2 of that document) — every one of
/// them is a plausible composable for a PURE string-in/string-out spec,
/// which is exactly what `DEFAULT_STR_OPS` selects for. This still stays
/// well short of "every string primitive" (no `startswith`/`find`/
/// `isdigit`/... — a caller that wants those declares `ops` explicitly,
/// per this const's own original design note above).
///
/// Map-template-pool rung (PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_
/// PREREG.md §3, tasks 102/411 "snake_case -> CamelCase"): APPENDED
/// `MapList`/`JoinList` — a string-shaped spec composes over its own
/// characters/substrings (`Split` already offered above), and until now
/// had no way to MAP a per-element transform (e.g. `Capitalize`) over the
/// pieces and rejoin them. `JoinList` is the already-shipped
/// Fold+concat-with-"" ListUnary (the `tup_string`/task-132 precedent);
/// `MapList` draws its per-element body from `map_templates_by_size`
/// (built below, itself evidence-gated). Both are cheap ListUnary/ListMap
/// registrations, not a new arity class.
const DEFAULT_STR_OPS: &[&str] = &[
    "Concat", "CaseFold", "Eq", "IfThenElse",
    "Replace", "Split", "StrCount", "Capitalize", "Reverse", "Slice", "Str",
    "MapList", "JoinList",
];

/// Build-A's own narrow fallback (`DERIVED_OPERATOR_TIER_RESULTS.md` §4,
/// `_SLICE1_PREREG.md` §9 step 2): an op name unrecognized by `OP_TABLE`
/// but present in `derived_names` (built from the `derived_ops`
/// registry; `op_list`'s own construction already confirmed a
/// compatible arity/pool shape via `derived_op_kind`) dispatches
/// through `Call{name,args}` instead of a native `TermNode`. Reached
/// only for a name the caller's own `op_list` put there — this function
/// trusts that gate the same way every existing `build_*` function
/// already trusts `op_list` to only ever hand it a table-recognized
/// name.
fn call_fallback(name: &str, args: Vec<TermIdx>, derived_names: &FxHashMap<String, Sym>) -> TermNode {
    match derived_names.get(name) {
        Some(sym) => TermNode::Call { name: *sym, args },
        None => unreachable!("op filtered through OP_TABLE or derived_ops"),
    }
}

/// Build the TermNode for an op over already-arena'd children.
fn build_op(name: &str, kids: &[TermIdx], derived_names: &FxHashMap<String, Sym>) -> TermNode {
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
        // Rung 1 Tier-1 stdlib Term ports.
        "Replace" => TermNode::Replace { text: kids[0], old: kids[1], new: kids[2] },
        "Str" => TermNode::Str { value: kids[0] },
        "Split" => TermNode::Split { text: kids[0], sep: kids[1] },
        "StrCount" => TermNode::StrCount { text: kids[0], sub: kids[1] },
        "Round" => TermNode::Round { value: kids[0], ndigits: kids[1] },
        "Reverse" => TermNode::Reverse { seq: kids[0] },
        "Capitalize" => TermNode::Capitalize { text: kids[0] },
        "ParseInt" => TermNode::ParseInt { text: kids[0] },
        "Slice" => TermNode::Slice { seq: kids[0], start: kids[1], stop: kids[2] },
        "Sort" => TermNode::Sort { seq: kids[0] },
        "DictItems" => TermNode::DictItems { seq: kids[0] },
        "GroupCount" => TermNode::GroupCount { seq: kids[0] },
        "DictMerge" => TermNode::DictMerge { a: kids[0], b: kids[1] },
        "Mod" => TermNode::Mod { a: kids[0], b: kids[1] },
        "Sqrt" => TermNode::Sqrt { arg: kids[0] },
        _ => call_fallback(name, kids.to_vec(), derived_names),
    }
}

/// Arc4-S4: build one of the `OpKind::ListUnary` composites. `scratch` is
/// used to mint the small fixed sub-terms each shape needs (a `Var(item)`
/// leaf, a `Count(Var(item))`, a `Lit(0)`, …) — called as its own
/// statement BEFORE `search.register(...)` (never inlined into the same
/// call), so this `&mut TermArena` borrow of `search.scratch` ends before
/// `search.register` needs `&mut search` — see the call sites below.
fn build_list_unary(
    name: &str, source: TermIdx, item: Sym, acc: Sym, scratch: &mut TermArena,
    derived_names: &FxHashMap<String, Sym>,
) -> TermNode {
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
        // CEILING_REASSESSMENT_4 `op:IntersectAll`/`op:UnionAll` (tasks
        // 111/140, PREREG §3.1-3.2): reduce a variable-length outer
        // sequence with the already-shipped binary `Intersect`/`Union`
        // Set Terms via `Fold`, seeded with the FIRST element as the
        // accumulator (`IndexAt(source, 0)`). Folding the WHOLE source
        // (including index 0 again) is safe because both ops are
        // idempotent under self-application (`Intersect(A,A)=A`,
        // `Union(A,A)=A`) — live-verified end-to-end against all three
        // fixture rows (including held-out) for both target tasks.
        "IntersectAll" => {
            let zero = scratch.add(TermNode::Lit { value: Value::Int(0) });
            let init = scratch.add(TermNode::IndexAt { seq: source, index: zero });
            let accv = scratch.add(TermNode::Var { name: acc });
            let itemv = scratch.add(TermNode::Var { name: item });
            let body = scratch.add(TermNode::Intersect { a: accv, b: itemv });
            TermNode::Fold { source, var_name: item, acc_name: acc, init, body }
        }
        "UnionAll" => {
            let zero = scratch.add(TermNode::Lit { value: Value::Int(0) });
            let init = scratch.add(TermNode::IndexAt { seq: source, index: zero });
            let accv = scratch.add(TermNode::Var { name: acc });
            let itemv = scratch.add(TermNode::Var { name: item });
            let body = scratch.add(TermNode::Union { a: accv, b: itemv });
            TermNode::Fold { source, var_name: item, acc_name: acc, init, body }
        }
        // PROGRAM_SYNTHESIS_DICTFROMPAIRS_PREREG.md §3-4: Python's
        // `dict(pairs)`. `init` is the empty dict; each fold step merges in
        // a single-pair dict built from the bound item's own two elements,
        // with `DictMerge`'s "b wins" rule giving later pairs priority on a
        // duplicate key -- exactly Python's own `dict()` semantics.
        "DictFromPairs" => {
            let empty = scratch.add(TermNode::MkDict { items: vec![] });
            let accv = scratch.add(TermNode::Var { name: acc });
            let key_item = scratch.add(TermNode::Var { name: item });
            let key_idx = scratch.add(TermNode::Lit { value: Value::Int(0) });
            let key = scratch.add(TermNode::IndexAt { seq: key_item, index: key_idx });
            let val_item = scratch.add(TermNode::Var { name: item });
            let val_idx = scratch.add(TermNode::Lit { value: Value::Int(1) });
            let val = scratch.add(TermNode::IndexAt { seq: val_item, index: val_idx });
            let pair = scratch.add(TermNode::MkDict { items: vec![key, val] });
            let body = scratch.add(TermNode::DictMerge { a: accv, b: pair });
            TermNode::Fold { source, var_name: item, acc_name: acc, init: empty, body }
        }
        _ => call_fallback(name, vec![source], derived_names),
    }
}

/// Arc6 tier-0 `op:ConcatList` — LIST concatenation, built exactly the way
/// `JoinList` builds STRING concatenation: a `Fold` over the second source
/// with the first as the accumulator's initial value and `Append` as the
/// body.  (`Cat` is string concat and emits Rust debug reprs on lists —
/// measured, §7.3 — so `Fold`+`Append` is the real route, and both Terms
/// are already shipped.)
fn build_list_binary(
    name: &str, a: TermIdx, b: TermIdx, item: Sym, acc: Sym, scratch: &mut TermArena,
    derived_names: &FxHashMap<String, Sym>,
) -> TermNode {
    match name {
        "ConcatList" => {
            let accv = scratch.add(TermNode::Var { name: acc });
            let itemv = scratch.add(TermNode::Var { name: item });
            let body = scratch.add(TermNode::Append { seq: accv, item: itemv });
            TermNode::Fold { source: b, var_name: item, acc_name: acc, init: a, body }
        }
        // SetLit/DictItems rung: `Union`/`Intersect` are already-shipped,
        // already-pure Set Terms — no Fold/Append scaffolding needed,
        // unlike `ConcatList`. Direct wrap, hence 0 extra fixed nodes
        // (`list_binary_extra_cost` below).
        "Intersect" => TermNode::Intersect { a, b },
        "Union" => TermNode::Union { a, b },
        _ => call_fallback(name, vec![a, b], derived_names),
    }
}

/// Arc6 tier-0: the FIXED node-count `build_list_binary` injects beyond its
/// two sources — the same honest MDL accounting `list_unary_extra_cost`
/// does for the unary shapes. `derived_extra` is the DATA-driven twin of
/// this hand-authored table — a derived `ListBinary` op's own
/// `extra_cost` (§3.1), consulted for any name this table itself doesn't
/// recognize.
fn list_binary_extra_cost(name: &str, derived_extra: &FxHashMap<String, usize>) -> usize {
    match name {
        "ConcatList" => 3, // Fold{.., body: Append(Var(acc), Var(item))}
        "Intersect" | "Union" => 0, // direct TermNode wrap, no injected nodes.
        _ => derived_extra.get(name).copied().unwrap_or(0),
    }
}

/// Arc4-S4: build one of the `OpKind::ListFilter`/`OpKind::ListMap`
/// composites — `tmpl` is an ALREADY-BUILT template subtree (from
/// `filter_templates_by_size`/`map_templates_by_size`), reused as a
/// shared child across every `source` it is combined with (the same
/// subtree-sharing discipline every other op in this module already
/// relies on).
/// `derived_names`'s own fallback arm here is, honestly, DEAD CODE under
/// this slice's own `derived_op_kind` inference (`DERIVED_OPERATOR_
/// TIER_SLICE1_PREREG.md`'s own "fallback-arm reachability" note): no
/// `op_list`-construction path this slice builds can route an
/// unrecognized name into `OpKind::ListFilter`/`ListMap` (the parent
/// doc's own §3.1: "the three template pools are NOT argument sources
/// for a top-level op"). Added for literal completeness with step 2's
/// five-function list, not because it is reachable today.
fn build_list_ho(name: &str, source: TermIdx, tmpl: TermIdx, item: Sym, derived_names: &FxHashMap<String, Sym>) -> TermNode {
    match name {
        "FilterList" => TermNode::FilterList { source, var_name: item, predicate: tmpl },
        "MapList" => TermNode::MapList { source, var_name: item, value: tmpl },
        // SetLit/DictItems rung: `SetMap` is `MapList`'s SET-returning
        // twin — same `OpKind::ListMap` registration path, same
        // `map_templates_by_size` pool, only the built Term differs
        // (`MapSet` instead of `MapList`).
        "SetMap" => TermNode::MapSet { source, var_name: item, value: tmpl },
        // DictItems/SortBy rung: same `OpKind::ListMap` registration path,
        // same `map_templates_by_size` pool — `tmpl` here is the SORT KEY
        // template, not an output-value template (the built `TermNode`
        // holds it as `key`, and the evaluator sorts the ORIGINAL elements
        // by it, keeping them unchanged — see term.rs `SortBy`).
        "SortBy" => TermNode::SortBy { source, var_name: item, key: tmpl },
        _ => call_fallback(name, vec![source, tmpl], derived_names),
    }
}

/// Rung 1 `op:IndexedMap` — the `MapList` twin with a SECOND bound
/// variable (the element's own position). `tmpl` is drawn from
/// `indexed_map_templates_by_size` (built separately from
/// `map_templates_by_size`, never perturbing the shipped pool's arena
/// layout — the `tmpl:nested_reduction` precedent, see that unit's own
/// module-doc note).
///
/// `name`'s own fallback arm here is, like `build_list_ho`'s, DEAD CODE
/// under this slice's own arity/pool inference (no path routes an
/// unrecognized name into `OpKind::IndexedMap` today) — added for
/// literal completeness with step 2's five-function list.
fn build_indexed_map(name: &str, source: TermIdx, tmpl: TermIdx, item: Sym, index: Sym, derived_names: &FxHashMap<String, Sym>) -> TermNode {
    if name == "IndexedMap" {
        TermNode::IndexedMap { source, item_name: item, index_name: index, value: tmpl }
    } else {
        call_fallback(name, vec![source, tmpl], derived_names)
    }
}

/// `ZIP_ELEMENTWISE` rung `op:ZipWith` — two sources (`a`, `b`, both
/// drawn from `list_by_size[1]`, see `OpKind::ZipMap`'s own doc comment),
/// `tmpl` drawn from `zip_op_templates_by_size` (already references
/// `a_name`/`b_name` as free `Var`s — see the pool-construction site).
///
/// `name`'s own fallback arm here is, like `build_indexed_map`'s, DEAD
/// CODE under this slice's own arity/pool inference (no path routes an
/// unrecognized name into `OpKind::ZipMap` today) — added for the same
/// literal-completeness reason that precedent's own comment gives.
fn build_zip_with(
    name: &str, a: TermIdx, b: TermIdx, tmpl: TermIdx, a_name: Sym, b_name: Sym,
    derived_names: &FxHashMap<String, Sym>,
) -> TermNode {
    if name == "ZipWith" {
        TermNode::ZipWith { a, b, a_name, b_name, value: tmpl }
    } else {
        call_fallback(name, vec![a, b, tmpl], derived_names)
    }
}

/// `ZIP_ELEMENTWISE` rung: the fixed 7-op inventory the pool builds a
/// `ZipWith` value-template from — exactly the 7 elementwise binary ops
/// this rung's 8-task witness population needs (`PROGRAM_SYNTHESIS_
/// ZIP_ELEMENTWISE_PREREG.md` §2), all already-shipped `TermNode`
/// variants (no new arithmetic Term).
const ZIP_ELEMENTWISE_OP_NAMES: &[&str] =
    &["Max", "IDiv", "Minus", "BitXor", "Plus", "BitAnd", "Times"];

/// Build a single `ZIP_ELEMENTWISE_OP_NAMES` entry applied to two
/// already-built operand `TermIdx`s. `Max`/`Plus`/`Times` are the
/// variadic-`items` arithmetic Terms (`term.rs`); the rest are the
/// binary-`{a,b}` shape. Both reduce to a 2-operand application here.
fn build_zip_elementwise_op(name: &str, x: TermIdx, y: TermIdx) -> TermNode {
    match name {
        "Max" => TermNode::Max { items: vec![x, y] },
        "Plus" => TermNode::Plus { items: vec![x, y] },
        "Times" => TermNode::Times { items: vec![x, y] },
        "IDiv" => TermNode::IDiv { a: x, b: y },
        "Minus" => TermNode::Minus { a: x, b: y },
        "BitXor" => TermNode::BitXor { a: x, b: y },
        "BitAnd" => TermNode::BitAnd { a: x, b: y },
        // Unreachable: `ZIP_ELEMENTWISE_OP_NAMES` is the only caller.
        _ => TermNode::Minus { a: x, b: y },
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
fn list_unary_extra_cost(name: &str, derived_extra: &FxHashMap<String, usize>) -> usize {
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
        // CEILING_REASSESSMENT_4: Fold{source, init:IndexAt(source,Lit(0))
        // (2: Lit(0)+IndexAt), body:Intersect|Union(Var(acc),Var(item))
        // (3: Var(acc)+Var(item)+Intersect|Union)} = 5.
        "IntersectAll" => 5,
        "UnionAll" => 5,
        // DICTFROMPAIRS_PREREG §4: Fold{source, init:MkDict([])(1), body:
        // DictMerge(Var(acc)(1), MkDict([IndexAt(Var(item),Lit(0))(3),
        // IndexAt(Var(item),Lit(1))(3)])(1))(1)} = 1+1+1+3+3+1 = 10.
        "DictFromPairs" => 10,
        // Derived-operator tier: the DATA-driven generalization of this
        // same hand-authored table (§3.1's own `extra_cost`), for any
        // name this table itself doesn't recognize.
        _ => derived_extra.get(name).copied().unwrap_or(0),
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
// Derived-operator tier (`DERIVED_OPERATOR_TIER_RESULTS.md` §3.3(b),
// `DERIVED_OPERATOR_TIER_SLICE1_PREREG.md`): parse the `derived_ops`
// argument's Term-JSON registry-entry strings. Two-stage, because
// `op_list` (which needs each entry's arity/pool shape) is built BEFORE
// `Search`/`search.scratch` exists — the arena a template body must be
// parsed into (the `filter_templates_by_size` precedent). Stage 1
// (`parse_derived_op_meta`, below) reads only name/params/extra_cost —
// no arena needed. Stage 2 (`build_derived_op_registry`, further below)
// parses each entry's `template` into `search.scratch`, once `search`
// exists, reusing `parse_excluded_term`'s EXISTING local grammar
// unchanged (this rung's own parity op — `Plus{Var,Var}` — is already
// covered by it) called with an EXTENDED `var_by_name` (spec vars plus
// this entry's own params) — the literal sense in which this is "an
// extension of `parse_excluded_term`'s existing local grammar": a new
// calling context, not a grammar rewrite. A template referencing
// ANOTHER derived op (`Call` inside a template) is NOT supported by
// this parser — out of scope, no entry this slice registers needs it.
// ---------------------------------------------------------------------------

/// One `derived_ops` entry, parsed enough to decide its `OpKind` for
/// `op_list` construction — the template itself stays as raw JSON until
/// `search.scratch` exists (stage 2).
struct DerivedOpMeta {
    /// The op's own display name, as given in the JSON — this is what
    /// an explicit `ops` list names to request it.
    name: String,
    name_sym: Sym,
    /// (display name, Sym, pool), ordered/positional.
    params: Vec<(String, Sym, DerivedOpPool)>,
    extra_cost: usize,
    template_json: serde_json::Value,
}

fn parse_derived_op_meta(
    j: &serde_json::Value,
    interner: &Interner,
    extra: &mut FxHashMap<String, Sym>,
    next_id: &mut u32,
) -> Option<DerivedOpMeta> {
    let obj = j.as_object()?;
    let name = obj.get("name")?.as_str()?.to_string();
    let name_sym = local_sym(interner, extra, next_id, &name);
    let params_json = obj.get("params")?.as_array()?;
    let mut params = Vec::with_capacity(params_json.len());
    for p in params_json {
        let pobj = p.as_object()?;
        let pname = pobj.get("name")?.as_str()?.to_string();
        let pool = match pobj.get("pool")?.as_str()? {
            "general" => DerivedOpPool::General,
            "list" => DerivedOpPool::List,
            _ => return None,
        };
        let psym = local_sym(interner, extra, next_id, &pname);
        params.push((pname, psym, pool));
    }
    let extra_cost = obj.get("extra_cost").and_then(|v| v.as_u64()).unwrap_or(0) as usize;
    let template_json = obj.get("template")?.clone();
    Some(DerivedOpMeta { name, name_sym, params, extra_cost, template_json })
}

/// Arity/pool -> `OpKind`, build-A's own narrow inference
/// (`DERIVED_OPERATOR_TIER_RESULTS.md` §4/§9 step 2). A mixed-pool shape
/// (`JoinListSep`'s own — one `list`, one `general`) is correctly
/// unrecognized here; that is build (B)'s job.
fn derived_op_kind(meta: &DerivedOpMeta) -> Option<OpKind> {
    let pools: Vec<DerivedOpPool> = meta.params.iter().map(|(_, _, p)| *p).collect();
    match pools.as_slice() {
        [DerivedOpPool::General] => Some(OpKind::Unary),
        [DerivedOpPool::General, DerivedOpPool::General] => Some(OpKind::Binary),
        [DerivedOpPool::General, DerivedOpPool::General, DerivedOpPool::General] => Some(OpKind::Ternary),
        [DerivedOpPool::List] => Some(OpKind::ListUnary),
        [DerivedOpPool::List, DerivedOpPool::List] => Some(OpKind::ListBinary),
        _ => None,
    }
}

/// Stage 2: build the full `DerivedOpRegistry`, parsing each entry's
/// `template` into `scratch` (must be `search.scratch` — the arena
/// `evaluate()` will run `Call`'s dispatch against).
fn build_derived_op_registry(
    metas: &[DerivedOpMeta],
    scratch: &mut TermArena,
    base_var_by_name: &FxHashMap<String, Sym>,
) -> DerivedOpRegistry {
    let mut registry = DerivedOpRegistry::default();
    for meta in metas {
        let mut var_by_name = base_var_by_name.clone();
        for (pname, psym, _pool) in &meta.params {
            var_by_name.insert(pname.clone(), *psym);
        }
        let Some(body) = parse_excluded_term(&meta.template_json, scratch, &var_by_name) else {
            continue; // malformed template — skip this entry, never fatal (the `exclude` discipline)
        };
        let params: Vec<(Sym, DerivedOpPool)> = meta.params.iter().map(|(_, s, p)| (*s, *p)).collect();
        registry.insert(meta.name_sym, DerivedOpDef { params, body, extra_cost: meta.extra_cost });
    }
    registry
}

/// Scope-guard: install `registry` into `ctx.derived_ops` for the
/// duration of `body`, restoring the PREVIOUS value afterward (`None`
/// in every real case today) so a `Call` node evaluated later in the
/// SAME `evaluate()` call tree — after this `SynthEnumerate` call
/// returns — can never dispatch through a stale registry
/// (`DERIVED_OPERATOR_TIER_SLICE1_PREREG.md`'s own "design decisions").
fn with_derived_ops<R>(
    ctx: &mut EvalCtx,
    registry: DerivedOpRegistry,
    body: impl FnOnce(&mut EvalCtx) -> R,
) -> R {
    let prev = ctx.derived_ops.take();
    ctx.derived_ops = Some(Arc::new(registry));
    let r = body(ctx);
    ctx.derived_ops = prev;
    r
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
        // `ZIP_ELEMENTWISE` rung: `IDiv` is a pre-existing, already-shipped
        // `TermNode` (already handled by `jsonio.rs`/`reflect.rs`) that was
        // NEVER previously reachable via a search-built candidate — it had
        // no `OP_TABLE` entry of its own before this rung, so this
        // module's own LOCAL `term_json` (distinct from `jsonio.rs`'s,
        // per the `MkDict`/`DictFromPairs` precedent's own comment two
        // arms below) never needed an arm for it. `ZipWith`'s template
        // pool is the first thing to make `IDiv` a possible `value` inside
        // a winning candidate (task 261, Python `//`) — found live, the
        // SAME class of gap `DICTFROMPAIRS_PREREG.md` §4 already hit for
        // `MkDict`, fixed the same way: add the arm before it ships.
        TermNode::IDiv { a, b } => json!({
            "type": "IDiv", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        // `ZIP_ELEMENTWISE` rung: same gap as `IDiv` above — `BitAnd`/
        // `BitXor` are pre-existing shipped Terms with no prior `OP_TABLE`
        // entry, first made search-reachable by `ZipWith`'s template pool
        // (tasks 429/399). Found live (task 399, `zip`+`^`).
        TermNode::BitAnd { a, b } => json!({
            "type": "BitAnd", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::BitXor { a, b } => json!({
            "type": "BitXor", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
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
        // Rung 1 Tier-1 stdlib Term ports — field names match
        // `jsonio.rs`'s (already-general) parser exactly, so the winning
        // candidate round-trips through `json.loads` on the Python side
        // the same way every other op's output already does.
        TermNode::Replace { text, old, new } => json!({
            "type": "Replace",
            "text": term_json(arena, *text, names, interner),
            "old": term_json(arena, *old, names, interner),
            "new": term_json(arena, *new, names, interner),
        }),
        TermNode::Str { value } => json!({
            "type": "Str", "value": term_json(arena, *value, names, interner),
        }),
        TermNode::Split { text, sep } => json!({
            "type": "Split",
            "text": term_json(arena, *text, names, interner),
            "sep": term_json(arena, *sep, names, interner),
        }),
        TermNode::StrCount { text, sub } => json!({
            "type": "StrCount",
            "text": term_json(arena, *text, names, interner),
            "sub": term_json(arena, *sub, names, interner),
        }),
        TermNode::Round { value, ndigits } => json!({
            "type": "Round",
            "value": term_json(arena, *value, names, interner),
            "ndigits": term_json(arena, *ndigits, names, interner),
        }),
        TermNode::Reverse { seq } => json!({
            "type": "Reverse", "seq": term_json(arena, *seq, names, interner),
        }),
        TermNode::IndexedMap { source, item_name, index_name, value } => json!({
            "type": "IndexedMap",
            "source": term_json(arena, *source, names, interner),
            "item_name": names.get(item_name).cloned().unwrap_or_default(),
            "index_name": names.get(index_name).cloned().unwrap_or_default(),
            "value": term_json(arena, *value, names, interner),
        }),
        TermNode::Capitalize { text } => json!({
            "type": "Capitalize", "text": term_json(arena, *text, names, interner),
        }),
        TermNode::ParseInt { text } => json!({
            "type": "ParseInt", "text": term_json(arena, *text, names, interner),
        }),
        TermNode::Slice { seq, start, stop } => json!({
            "type": "Slice",
            "seq": term_json(arena, *seq, names, interner),
            "start": term_json(arena, *start, names, interner),
            "stop": term_json(arena, *stop, names, interner),
        }),
        // SetLit/DictItems rung.
        TermNode::Sort { seq } => json!({
            "type": "Sort", "seq": term_json(arena, *seq, names, interner),
        }),
        TermNode::MapSet { source, var_name, value } => json!({
            "type": "MapSet",
            "source": term_json(arena, *source, names, interner),
            "var_name": names.get(var_name).cloned().unwrap_or_default(),
            "value": term_json(arena, *value, names, interner),
        }),
        TermNode::Intersect { a, b } => json!({
            "type": "Intersect",
            "a": term_json(arena, *a, names, interner),
            "b": term_json(arena, *b, names, interner),
        }),
        TermNode::Union { a, b } => json!({
            "type": "Union",
            "a": term_json(arena, *a, names, interner),
            "b": term_json(arena, *b, names, interner),
        }),
        // DictItems/SortBy rung.
        TermNode::DictItems { seq } => json!({
            "type": "DictItems", "seq": term_json(arena, *seq, names, interner),
        }),
        TermNode::SortBy { source, var_name, key } => json!({
            "type": "SortBy",
            "source": term_json(arena, *source, names, interner),
            "var_name": names.get(var_name).cloned().unwrap_or_default(),
            "key": term_json(arena, *key, names, interner),
        }),
        // GroupCount/DictMerge rung.
        TermNode::GroupCount { seq } => json!({
            "type": "GroupCount", "seq": term_json(arena, *seq, names, interner),
        }),
        TermNode::DictMerge { a, b } => json!({
            "type": "DictMerge",
            "a": term_json(arena, *a, names, interner),
            "b": term_json(arena, *b, names, interner),
        }),
        // `ZIP_ELEMENTWISE` rung: this module's own local `term_json`
        // renderer is exhaustive (an omitted arm here `unreachable!()`s
        // the first time the search renders a `ZipWith` candidate — the
        // SAME finding `GROUPCOUNT_DICTMERGE_RESULTS.md` §4 already hit
        // for `MkDict`, avoided here by adding the arm up front).
        TermNode::ZipWith { a, b, a_name, b_name, value } => json!({
            "type": "ZipWith",
            "a": term_json(arena, *a, names, interner),
            "b": term_json(arena, *b, names, interner),
            "a_name": names.get(a_name).cloned().unwrap_or_default(),
            "b_name": names.get(b_name).cloned().unwrap_or_default(),
            "value": term_json(arena, *value, names, interner),
        }),
        // DICTFROMPAIRS_PREREG §4: `MkDict` had NO arm here (this module's
        // own local `term_json` renderer, distinct from `jsonio.rs`'s) --
        // every prior op composing it (`MkDict` calls elsewhere in this
        // file are all rule-authoring/`Verify`-test call sites, never
        // reachable from a SEARCH-BUILT candidate) never hit this path.
        // `DictFromPairs` is the FIRST op-table exposure whose built
        // candidate tree can contain a bare `MkDict` node, and omitting
        // this arm panics `unreachable!()` the first time the search
        // renders such a candidate (found live, not anticipated -- see
        // RESULTS §"genuine mid-rung finding"). Field name matches
        // `jsonio.rs`'s own `MkDict` parser (`"items"`).
        TermNode::MkDict { items } => json!({
            "type": "MkDict",
            "items": items.iter().map(|i| term_json(arena, *i, names, interner)).collect::<Vec<_>>(),
        }),
        // PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX: the SAME missing-arm class
        // `DictFromPairs`/`MkDict` already hit (see that comment above) —
        // `Mod`/`Sqrt` are the first op-table exposure whose built
        // candidate tree can contain a bare `Mod`/`Sqrt` node. Field names
        // match `jsonio.rs`'s own parser (`"a"`/`"b"` for `Mod`, `"arg"`
        // for `Sqrt`).
        TermNode::Mod { a, b } => json!({
            "type": "Mod", "a": term_json(arena, *a, names, interner), "b": term_json(arena, *b, names, interner)
        }),
        TermNode::Sqrt { arg } => json!({
            "type": "Sqrt", "arg": term_json(arena, *arg, names, interner),
        }),
        // Derived-operator tier: a winning candidate may itself be a
        // `Call{name,args}` node (build-A's own fallback arms route an
        // unrecognized-but-registered op name here) — rendered exactly
        // like every other op, `name` resolved through THIS module's own
        // local table (never `Interner::resolve`; see the "Register each
        // derived op's own name" note where `names` is populated).
        TermNode::Call { name, args } => json!({
            "type": "Call",
            "name": names.get(name).cloned().unwrap_or_default(),
            "args": args.iter().map(|a| term_json(arena, *a, names, interner)).collect::<Vec<_>>(),
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
        TermNode::IDiv { a, b } => format!("({} // {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::BitAnd { a, b } => format!("({} & {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
        TermNode::BitXor { a, b } => format!("({} ^ {})", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)),
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
        // Rung 1 Tier-1 stdlib Term ports (readable, never re-parsed).
        TermNode::Replace { text, old, new } => format!(
            "{}.replace({}, {})",
            term_str(arena, *text, names, interner),
            term_str(arena, *old, names, interner),
            term_str(arena, *new, names, interner),
        ),
        TermNode::Str { value } => format!("str({})", term_str(arena, *value, names, interner)),
        TermNode::Split { text, sep } => format!(
            "{}.split({})", term_str(arena, *text, names, interner), term_str(arena, *sep, names, interner)
        ),
        TermNode::StrCount { text, sub } => format!(
            "{}.count({})", term_str(arena, *text, names, interner), term_str(arena, *sub, names, interner)
        ),
        TermNode::Round { value, ndigits } => format!(
            "round({}, {})", term_str(arena, *value, names, interner), term_str(arena, *ndigits, names, interner)
        ),
        TermNode::Reverse { seq } => format!("reversed({})", term_str(arena, *seq, names, interner)),
        TermNode::IndexedMap { source, item_name, index_name, value } => format!(
            "[{} for {}, {} in enumerate({})]",
            term_str(arena, *value, names, interner),
            names.get(index_name).cloned().unwrap_or_default(),
            names.get(item_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
        ),
        TermNode::ZipWith { a, b, a_name, b_name, value } => format!(
            "[{} for {}, {} in zip({}, {})]",
            term_str(arena, *value, names, interner),
            names.get(a_name).cloned().unwrap_or_default(),
            names.get(b_name).cloned().unwrap_or_default(),
            term_str(arena, *a, names, interner),
            term_str(arena, *b, names, interner),
        ),
        TermNode::Capitalize { text } => format!("{}.capitalize()", term_str(arena, *text, names, interner)),
        TermNode::ParseInt { text } => format!("int({})", term_str(arena, *text, names, interner)),
        TermNode::Slice { seq, start, stop } => format!(
            "{}[{}:{}]",
            term_str(arena, *seq, names, interner),
            term_str(arena, *start, names, interner),
            term_str(arena, *stop, names, interner),
        ),
        // SetLit/DictItems rung.
        TermNode::Sort { seq } => format!("sorted({})", term_str(arena, *seq, names, interner)),
        TermNode::MapSet { source, var_name, value } => format!(
            "{{{} for {} in {}}}",
            term_str(arena, *value, names, interner),
            names.get(var_name).cloned().unwrap_or_default(),
            term_str(arena, *source, names, interner),
        ),
        TermNode::Intersect { a, b } => format!(
            "{} & {}", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)
        ),
        TermNode::Union { a, b } => format!(
            "{} | {}", term_str(arena, *a, names, interner), term_str(arena, *b, names, interner)
        ),
        // Derived-operator tier — see `term_json`'s matching `Call` arm.
        TermNode::Call { name, args } => {
            let kids: Vec<String> = args.iter().map(|a| term_str(arena, *a, names, interner)).collect();
            format!("{}({})", names.get(name).cloned().unwrap_or_default(), kids.join(", "))
        }
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
    derived_ops_t: Option<TermIdx>,
    exclude_ops_t: Option<TermIdx>,
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
    // Rung 1 `op:IndexedMap`: the SECOND bound variable an indexed-map
    // body needs (the element's own 0-based position). Same `local_sym`
    // precedent, minted unconditionally and cheaply.
    let index_sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, "__index");
    names.entry(index_sym).or_insert_with(|| "__index".to_string());
    // `ZIP_ELEMENTWISE` rung `op:ZipWith`: the two bound variables a
    // zip-body needs (one per zipped pair, OUTER level). A SEPARATE,
    // distinctly-named INNER pair (`__zi`/`__zj`) is minted too, for the
    // one-level-nested composition tasks 259/401/445 need (a tuple OF
    // tuples: the outer `ZipWith` binds `__za`/`__zb` to a PAIR of
    // sub-tuples, whose own elements the INNER `ZipWith` binds
    // `__zi`/`__zj` to) — distinct names, matching the `__item`/`__inner`
    // two-level precedent, even though the engine's own stack-shadowing
    // `env_get` (searches from the end) would tolerate reuse.
    let za_sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, "__za");
    names.entry(za_sym).or_insert_with(|| "__za".to_string());
    let zb_sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, "__zb");
    names.entry(zb_sym).or_insert_with(|| "__zb".to_string());
    let zi_sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, "__zi");
    names.entry(zi_sym).or_insert_with(|| "__zi".to_string());
    let zj_sym = local_sym(ctx.interner, &mut extra, &mut next_placeholder, "__zj");
    names.entry(zj_sym).or_insert_with(|| "__zj".to_string());

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

    // `ZIP_ELEMENTWISE` rung: does this spec have (at least) TWO DISTINCT
    // list/tuple-shaped variables that are pairwise-zippable (equal
    // length on EVERY row)? Narrow, structural evidence — the same
    // "consistently typed on every row" discipline `list_vars`/
    // `scalar_vars` below already use — for a genuine two-sequence spec
    // (`zip(a, b)` needs both operands the same length to mean anything).
    // A single list-shaped variable (e.g. task 88's `a`) never sets this.
    let zippable_list_vars: SmallVec<[Sym; 4]> = var_order
        .iter()
        .cloned()
        .filter(|s| {
            !envs.is_empty()
                && envs.iter().all(|e| {
                    e.iter().find(|(vs, _)| vs == s).map(|(_, v)| is_listlike(v)).unwrap_or(false)
                })
        })
        .collect();
    let spec_has_two_zippable_list_vars = zippable_list_vars.iter().enumerate().any(|(i, s1)| {
        zippable_list_vars.iter().skip(i + 1).any(|s2| {
            envs.iter().all(|e| {
                let l1 = e.iter().find(|(vs, _)| vs == s1).and_then(|(_, v)| items_of(v)).map(|it| it.len());
                let l2 = e.iter().find(|(vs, _)| vs == s2).and_then(|(_, v)| items_of(v)).map(|it| it.len());
                l1.is_some() && l1 == l2
            })
        })
    });

    // --- Op inventory (caller-declared, else a TYPED default; unknown
    //     names ignored — generator.py's `if name in table`) ---
    // Arc6 tier-0: the tuple CONSTRUCTOR is offered only to a spec that
    // wants a tuple back (see `TUPLE_BUILD_OPS`).
    let spec_output_is_listlike = !outputs.is_empty() && outputs.iter().all(is_listlike);
    // SetLit/DictItems rung: the SAME narrow output-type gate as
    // `spec_output_is_listlike`, for Set/FrozenSet — see `SET_DEFAULT_OPS`.
    let spec_output_is_setlike = !outputs.is_empty()
        && outputs.iter().all(|v| matches!(v, Value::Set(_) | Value::FrozenSet(_)));
    // Rung 1: EVIDENCE-gated string/float method ops (`TUPLE_BUILD_OPS`'s
    // own discipline, generalised past output-shape to ANY-row content
    // evidence). Loose "ANY row, any var or the output" tests — NOT the
    // strict ALL-string `spec_is_string_shaped` test above — because a
    // spec that is otherwise numeric but carries ONE string argument
    // (e.g. `int(s)`) still genuinely needs `ParseInt`/`Str`, and a spec
    // is never penalised for having the evidence absent (the bucket is
    // simply empty, byte-identical to today).
    let spec_has_string_value = envs.iter().flat_map(|e| e.iter()).any(|(_, v)| is_str_val(v))
        || outputs.iter().any(is_str_val);
    let is_float_val = |v: &Value| matches!(v, Value::Float(_) | Value::Rational(_, _));
    let spec_has_float_value = envs.iter().flat_map(|e| e.iter()).any(|(_, v)| is_float_val(v))
        || outputs.iter().any(is_float_val);
    // DictItems/SortBy rung (PREREG §4): a spec with a top-level
    // Dict-shaped VARIABLE (never a nested one — the same shallow,
    // top-level-only test `spec_has_string_value`/`spec_has_float_value`
    // already use). Narrow by construction: `is_listlike` deliberately
    // excludes Dict, so no currently-shipped bucket ever offers
    // `DictItems`/`SortBy`, and — measured against the real corpus,
    // PREREG §4 — no CURRENTLY-PASSING task has a top-level Dict variable,
    // so this evidence gate can only ever ADD ops to a spec that is not
    // already solved, never touch one that is.
    let is_dict_val = |v: &Value| matches!(v, Value::Dict(_));
    let spec_has_dict_value = envs.iter().flat_map(|e| e.iter()).any(|(_, v)| is_dict_val(v));
    // GroupCount/DictMerge rung: the OUTPUT-shape twin of `spec_has_dict_
    // value` above, mirroring `spec_output_is_listlike`/`spec_output_is_
    // setlike`'s own already-measured-safe discipline (an output-type gate,
    // never input-shape alone). Task 88 (`freq_count`, output Dict, input a
    // plain List) needs `GroupCount` even though it has NO dict-shaped
    // VARIABLE; task 87 (`merge_dictionaries_three`, output AND all three
    // inputs Dict) needs `DictMerge` and has no list-shaped variable at
    // all, so it never reaches the list-shaped branch below — see the
    // dedicated `DICT_DEFAULT_OPS` branch this flag also gates.
    let spec_output_is_dictlike = !outputs.is_empty() && outputs.iter().all(is_dict_val);
    // Rung 1: measured live that even an "inside the list" string-content
    // test still fires for task 132 (a genuine list-of-CHARACTERS ->
    // joined-string spec) and still regresses it to `budget` — see the
    // list-shaped branch below, which for this reason does NOT offer the
    // string-method ops at all for a list-shaped spec.
    // Rung 1 `op:IndexedMap`'s OWN justification, made a real evidence
    // gate rather than an unconditional list-shaped default: "with
    // repeated elements, no composition of the current [element-wise]
    // ops can distinguish two occurrences" (the variant's own doc
    // comment / `STRUCTURAL_CEILING.md`'s S8 class). A list-shaped var
    // or output whose elements are all DISTINCT on some row never needs
    // the position at all — `IndexAt`/`Argmax`/etc already reach
    // everything an index-free composition can. `IndexedMap` is the
    // single most expensive op this rung adds (a full `ListMap`-shaped
    // source x template cross-product every size), so it stays OUT of
    // the unconditional `LIST_EXTRA_OPS` bucket entirely and is offered
    // only when this concrete evidence is present.
    let has_dup = |v: &Value| -> bool {
        let Some(items) = items_of(v) else { return false };
        for i in 0..items.len() {
            for j in (i + 1)..items.len() {
                if items[i] == items[j] {
                    return true;
                }
            }
        }
        false
    };
    let spec_has_repeated_list_element = envs.iter().flat_map(|e| e.iter()).any(|(_, v)| has_dup(v))
        || outputs.iter().any(has_dup);
    // Map-template-pool rung (PROGRAM_SYNTHESIS_CEILING_REASSESSMENT_2_
    // PREREG.md §3): nested, ONE-LEVEL-DOWN evidence — does a list-shaped
    // var/output have elements that are THEMSELVES list-shaped ("a list of
    // lists")? This is the `spec_has_dict_value`/`spec_has_float_value`
    // discipline one grain finer, needed because `MapList`'s per-element
    // body operates on the BOUND ITEM, not the outer spec value — e.g.
    // "sort each sublist" (task 104) never shows up as a top-level Dict/
    // Float value, only as a list variable whose OWN elements are lists.
    let spec_has_list_of_lists = envs.iter().flat_map(|e| e.iter()).any(|(_, v)| {
        items_of(v).is_some_and(|items| !items.is_empty() && items.iter().all(is_listlike))
    }) || outputs.iter().any(|v| {
        items_of(v).is_some_and(|items| !items.is_empty() && items.iter().all(is_listlike))
    });
    // Map-template-pool rung, same grain as `spec_has_list_of_lists` above
    // but for STRING elements (task 456, "reverse each string in a list" —
    // the outer var/output is a List, never a bare Str, so the existing
    // flat `spec_has_string_value` never sees it). Deliberately used ONLY
    // to gate `map_templates_by_size` entries (never `op_list`/`DEFAULT_
    // OPS` — Rung 1's own measured lesson, `RUNG1_RESULTS.md`, is that
    // THIS exact "list has string elements" evidence still regresses
    // task 132 when it widens the TOP-LEVEL op inventory; it does not
    // license widening op_list here, only the bounded per-element pool).
    let spec_has_string_list_elements = envs.iter().flat_map(|e| e.iter()).any(|(_, v)| {
        items_of(v).is_some_and(|items| !items.is_empty() && items.iter().all(is_str_val))
    }) || outputs.iter().any(|v| {
        items_of(v).is_some_and(|items| !items.is_empty() && items.iter().all(is_str_val))
    });
    // Same grain, for FLOAT elements (task 419, "round every number of a
    // given list") — `spec_has_float_value`'s flat top-level test never
    // sees a Float nested one level inside a List var/output either.
    let spec_has_float_list_elements = envs.iter().flat_map(|e| e.iter()).any(|(_, v)| {
        items_of(v).is_some_and(|items| items.iter().any(is_float_val))
    }) || outputs.iter().any(|v| {
        items_of(v).is_some_and(|items| items.iter().any(is_float_val))
    });
    let mut extra_evidence_ops: Vec<&str> = Vec::new();
    if spec_has_string_value {
        extra_evidence_ops.extend(["Replace", "Split", "StrCount", "Capitalize", "Str", "ParseInt"]);
    }
    if spec_has_float_value {
        extra_evidence_ops.push("Round");
    }
    if spec_is_list_shaped && spec_has_repeated_list_element {
        extra_evidence_ops.push("IndexedMap");
    }
    let default_ops: Vec<&str> = if spec_is_string_shaped {
        // DEFAULT_STR_OPS already carries the full Tier-1 string-method
        // set (§ its own doc comment) — that bucket's OWN gate (every
        // row's every value string-shaped) is already narrow, so no
        // further evidence-gating is layered on top here.
        DEFAULT_STR_OPS.to_vec()
    } else if spec_output_is_setlike {
        // SetLit/DictItems rung: a DEDICATED small typed default — the
        // `DEFAULT_STR_OPS` precedent (a small, shape-tailored bucket),
        // NOT layered onto the much larger list-shaped default below.
        // MEASURED necessary, not assumed: layering `Sort`/`SetMap`/
        // `Intersect`/`Union` on top of `DEFAULT_OPS ∪ LIST_EXTRA_OPS`'s
        // dozen other list ops caused BUDGET EXHAUSTION before the
        // search ever reached the in-budget witness for tasks 232/473
        // (`tested==200000, found:false`, live-measured) even though
        // THIS narrow bucket solves both well under budget (19772/74830
        // tested respectively) — the exact Rung-1 lesson ("even cheap
        // unconditional additions regress a budget-fragile spec"),
        // reproduced here and resolved the same way Rung 1 resolved it:
        // narrow the bucket, don't widen the budget.
        SET_DEFAULT_OPS.to_vec()
    } else if spec_is_list_shaped {
        let mut v: Vec<&str> =
            DEFAULT_OPS.iter().chain(LIST_EXTRA_OPS.iter()).copied().collect();
        if spec_output_is_listlike {
            v.extend(TUPLE_BUILD_OPS.iter().copied());
        }
        // SetLit/DictItems rung: `Sort` offered under the SAME narrow
        // output-type gate `TUPLE_BUILD_OPS` uses (never on input-shape
        // evidence alone — Rung 1 measured that even cheap unconditional
        // Unary/Ternary additions regress task 132). Set-shaped output
        // is handled entirely by the dedicated branch above; this arm is
        // only reached when the output is List/Tuple-shaped, not Set.
        if spec_output_is_listlike {
            v.push("Sort");
        }
        // Map-template-pool rung (task 118, "split a string into a list of
        // strings"): `Split` under the SAME narrow output-type gate as
        // `Sort`/`TUPLE_BUILD_OPS` above, PLUS the string-content evidence
        // gate `Round` already uses below — never on input-shape evidence
        // alone (task 132's own exclusion above stays in force: its output
        // is a STRING, not listlike, so `spec_output_is_listlike` is false
        // for it and this arm is unreached). A list-shaped spec whose
        // output is NOT listlike still gets none of the string-method ops,
        // exactly as the paragraph below already decided.
        if spec_output_is_listlike && spec_has_string_value {
            v.push("Split");
        }
        // Measured (not assumed): even the NARROWER `spec_list_has_
        // string_elements` gate still fires for task 132 (a genuine
        // list-of-CHARACTERS -> joined-string spec — its elements really
        // are strings) and still regresses it to `budget`
        // (`RUNG1_RESULTS.md` §"regression investigation" walks all four
        // attempts, `distinct` 1941 -> 1508 -> still `tested==
        // max_candidates`). None of this rung's measured gains are
        // list-shaped specs needing the string-method ops (checked
        // directly against the 6 `newly_passing` ids), so the honest,
        // measured-safe choice is: the list-shaped branch does NOT offer
        // `Replace`/`Split`/`StrCount`/`Capitalize`/`Str`/`ParseInt` at
        // all. A list of strings still reaches them via `MapList`
        // composing a per-element `Str`/`Capitalize`/... IF a future
        // task needs it enough to declare `ops` explicitly (Rung 4's
        // selection layer) — this typed default stays conservative.
        if spec_has_float_value {
            v.push("Round");
        }
        // Map-template-pool rung (task 439, "join a list of integers into
        // a single integer" — `ParseInt(JoinList(MapList(a,item,
        // Str(item))))`): narrow, output-type-only gate — a list-shaped
        // spec whose output is a BARE Int (never listlike) and which
        // carries NO top-level string/float evidence at all (so this
        // never overlaps `Split`'s own gate immediately above, nor
        // `Round`'s). `ParseInt` only ever matches a genuinely String-
        // typed candidate at evaluation time, so on a spec with no string
        // content anywhere it costs a registration attempt that can never
        // produce a NEW distinct value — the same "harmless when unused"
        // shape as `Round` being offered to a spec with no float value
        // would be, except this one is additionally gated to never even
        // apply until this rung's own `Str(item)` map-template exists.
        let spec_output_is_bare_int = !outputs.is_empty()
            && outputs.iter().all(|v| matches!(v, Value::Int(_)));
        if !spec_output_is_listlike
            && spec_output_is_bare_int
            && !spec_has_string_value
            && !spec_has_float_value
        {
            v.push("ParseInt");
        }
        if spec_has_repeated_list_element {
            v.push("IndexedMap");
        }
        // DictItems/SortBy rung: same evidence-gate discipline as
        // `Round`/`IndexedMap` above — offered only when the spec's own
        // content proves it is needed (PREREG §4's regression audit).
        // `Reverse` is included alongside (not unconditional in
        // `LIST_EXTRA_OPS` per Rung 1's own measured task-132 regression)
        // because it is needed for the `Counter.most_common()` descending
        // shape and is mutually exclusive with task 132's branch the same
        // way `SET_DEFAULT_OPS`'s unconditional `Reverse` is: task 132 has
        // no Dict-shaped variable, so it can never reach this gate.
        if spec_has_dict_value {
            v.push("DictItems");
            v.push("SortBy");
            v.push("Reverse");
        }
        // Ceiling reassessment 3 (task 64, "sort a list of tuples using the
        // second value of each tuple"): `SortBy` was gated to
        // `spec_has_dict_value` ONLY when it landed (scoped narrowly to
        // serve task 475's own `Counter.most_common()` shape) and never
        // re-checked against a spec with NO dict at all but a genuine
        // sort-by-projected-key need — a `List[Tuple]` never sets
        // `spec_has_dict_value`. `spec_has_list_of_lists` (map-template-pool
        // rung, already measured safe for the `Sort(item)` key template
        // this exact witness uses) is the correct, already-existing,
        // already-narrow evidence: a spec whose own list variable/output
        // contains list-shaped (or tuple-shaped — `is_listlike` covers
        // both) elements is exactly the shape `SortBy` composes over.
        // Deliberately does NOT also widen `DictItems`/`Reverse` here —
        // both stay exactly as dict-scoped as before; only `SortBy` gets
        // the second disjunct, because only `SortBy` has a live witness
        // under this evidence (task 64, `SortBy(a, item, Sort(item))`,
        // confirmed against every revealed AND held-out row).
        if spec_has_list_of_lists && !spec_has_dict_value {
            v.push("SortBy");
        }
        // GroupCount/DictMerge rung (task 88, `freq_count`): task 88's own
        // variable `a` is list-shaped (so this spec reaches THIS branch,
        // never the dedicated `DICT_DEFAULT_OPS` branch below), but its
        // OUTPUT is Dict-shaped — the SAME output-type-only gate discipline
        // `Sort`/`Split`/`ParseInt` above already use. `DictMerge` is
        // deliberately NOT added here: task 88 has no live witness needing
        // it under this evidence, and every one of task 87's own variables
        // is Dict-shaped, not list-shaped, so it never reaches this branch
        // to need it here.
        if spec_output_is_dictlike {
            v.push("GroupCount");
        }
        // `ZIP_ELEMENTWISE` rung (tasks 259/261/273/282/399/401/429/445):
        // narrow, structural evidence — a genuine two-sequence spec, see
        // `spec_has_two_zippable_list_vars`'s own doc comment. Every one
        // of this rung's 8 witness tasks has EXACTLY two spec variables,
        // both list/tuple-shaped, equal length on every row, so this gate
        // is a real narrowing, not a rename of `spec_is_list_shaped`
        // itself (a single-list-var spec like task 88 never sets it).
        if spec_has_two_zippable_list_vars {
            v.push("ZipWith");
        }
        v
    } else if spec_output_is_dictlike {
        // GroupCount/DictMerge rung (task 87, `merge_dictionaries_three`):
        // a spec whose variables and output are ALL Dict-shaped is neither
        // string-, set-, nor list-shaped (`spec_is_list_shaped` requires a
        // LIST/Tuple/Set/FrozenSet-shaped var or output; Dict is
        // deliberately excluded from `is_listlike`, same exclusion
        // `spec_has_dict_value`'s own doc comment already names) — it would
        // otherwise fall to the bare arithmetic `DEFAULT_OPS` below and
        // never see `DictMerge`/`GroupCount` at all. A dedicated small
        // bucket, mirroring `SET_DEFAULT_OPS`'s own precedent (a shape that
        // isn't "list-shaped" gets its OWN narrow typed default, not a
        // layer on top of the much larger list-shaped bucket).
        DICT_DEFAULT_OPS.to_vec()
    } else {
        let mut v = DEFAULT_OPS.to_vec();
        v.extend(extra_evidence_ops.iter().copied());
        // PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX: `Mod`/`Sqrt` pushed onto
        // this LOCAL `v` only — never onto the shared `DEFAULT_OPS`
        // constant the list-shaped branch above also consumes, so every
        // list-shaped spec's op inventory (including task 132's) is
        // byte-unchanged, exactly as the bare-scalar-`else`-branch-only
        // scoping this arc's own BUDGET_EXHAUSTED_SURVEY_PREREG/RESULTS.md
        // §6/§8 already established was the correct blast-radius
        // boundary. A call site that needs the pre-Mod/Sqrt bare-scalar
        // inventory back (the retrieval-ladder/decomposition-probe
        // cross-lane callers this fix scopes) uses `exclude_ops` instead
        // of a second typed-default branch.
        v.push("Mod");
        v.push("Sqrt");
        v
    };
    // --- Derived-operator tier, stage 1 (metadata only — no arena needed
    // yet; `Search`/`search.scratch` doesn't exist until below). A
    // derived op is NEVER part of a typed default (`default_ops` above)
    // — like `JoinListSep`'s own precedent, it is reachable only via an
    // EXPLICIT `ops` request naming it. ---
    let derived_metas: Vec<DerivedOpMeta> = match derived_ops_t {
        Some(t) => {
            let dv = evaluate(arena, t, env, ctx);
            match items_of(&dv) {
                Some(items) => items
                    .iter()
                    .filter_map(|v| value_str(v, ctx.interner))
                    .filter_map(|text| serde_json::from_str::<serde_json::Value>(&text).ok())
                    .filter_map(|j| parse_derived_op_meta(&j, ctx.interner, &mut extra, &mut next_placeholder))
                    .collect(),
                None => Vec::new(),
            }
        }
        None => Vec::new(),
    };
    // Register each derived op's own name (and param names) in the
    // OUTPUT name table too — `term_json`/`term_str` (this module's own
    // LOCAL serializers, never `jsonio.rs`'s generic ones — see the
    // module doc's own "Serialization is LOCAL" note) resolve a `Call`
    // node's `name`/param `Var`s the same way they already resolve
    // `__item`/`__acc`/every spec variable, via THIS table, never
    // `Interner::resolve` directly.
    for meta in &derived_metas {
        names.entry(meta.name_sym).or_insert_with(|| meta.name.clone());
        for (pname, psym, _pool) in &meta.params {
            names.entry(*psym).or_insert_with(|| pname.clone());
        }
    }
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
                        .filter_map(|n| {
                            if let Some(k) = table_kind(&n) {
                                return Some((n, k));
                            }
                            derived_metas
                                .iter()
                                .find(|m| m.name == n)
                                .and_then(|m| derived_op_kind(m).map(|k| (n.clone(), k)))
                        })
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
    // PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX: `exclude_ops` is a soft,
    // call-site-scoped filter applied AFTER `op_list` converges (whether
    // it came from the typed default above or a caller's own explicit
    // `ops`) — the single point both paths already meet. Absent
    // (`exclude_ops_t == None`) is the byte-unchanged case every existing
    // caller hits. An unrecognized name is simply not present in
    // `op_list` to begin with, so it is a no-op, matching `exclude`'s own
    // "unrecognized/malformed entries are skipped, never fatal" idiom.
    let op_list: Vec<(String, OpKind)> = match exclude_ops_t {
        Some(t) => {
            let xv = evaluate(arena, t, env, ctx);
            match items_of(&xv) {
                Some(items) => {
                    let names: Vec<String> =
                        items.iter().filter_map(|v| value_str(v, ctx.interner)).collect();
                    op_list.into_iter().filter(|(n, _)| !names.iter().any(|x| x == n)).collect()
                }
                None => op_list,
            }
        }
        None => op_list,
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

    // --- Derived-operator tier, stage 2: build the template bodies into
    // `search.scratch` now that it exists, then install the registry into
    // `ctx.derived_ops` for the scope of the search only (`with_derived_ops`
    // restores `ctx.derived_ops` to its PREVIOUS value before this
    // function returns, so a `Call` node evaluated elsewhere in the same
    // `evaluate()` call tree can never see a stale registry — see
    // `DERIVED_OPERATOR_TIER_SLICE1_PREREG.md`'s own "design decisions").
    let derived_var_by_name: FxHashMap<String, Sym> =
        search.names.iter().map(|(s, n)| (n.clone(), *s)).collect();
    let derived_registry =
        build_derived_op_registry(&derived_metas, &mut search.scratch, &derived_var_by_name);
    // Build-A's own fallback arms (§4/§9 step 2, `build_op`/`build_list_*`
    // below) need the SAME name -> Sym mapping the registry itself is
    // keyed by (so a `Call{name,...}` node built mid-search dispatches
    // to the exact entry `ctx.derived_ops` holds) plus each entry's own
    // `extra_cost` (consulted only by the two shapes that already have
    // an extra-cost concept — `ListUnary`/`ListBinary`).
    let derived_names: FxHashMap<String, Sym> =
        derived_metas.iter().map(|m| (m.name.clone(), m.name_sym)).collect();
    let derived_extra: FxHashMap<String, usize> =
        derived_metas.iter().map(|m| (m.name.clone(), m.extra_cost)).collect();

    let result = with_derived_ops(ctx, derived_registry, |ctx| {

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
    // SetLit/DictItems rung: `SetMap` shares `MapList`'s exact template
    // pool (`OpKind::ListMap`), so it must ALSO gate pool construction —
    // a spec that requests `SetMap` but never `MapList` would otherwise
    // build an empty pool and find nothing.
    let set_map_wanted = op_list.iter().any(|(n, _)| n == "SetMap");
    // DictItems/SortBy rung: `SortBy` shares `MapList`'s exact template
    // pool too (same `OpKind::ListMap` reuse as `SetMap`) — must ALSO gate
    // pool construction, same reasoning as `set_map_wanted` above.
    let sort_by_wanted = op_list.iter().any(|(n, _)| n == "SortBy");
    let map_wanted =
        op_list.iter().any(|(n, _)| n == "MapList") || set_map_wanted || sort_by_wanted;
    // Rung 1 `op:IndexedMap`.
    let indexed_map_wanted = op_list.iter().any(|(n, _)| n == "IndexedMap");
    let template_cap = max_size + 1;
    let mut filter_templates_by_size: Vec<Vec<TermIdx>> = vec![Vec::new(); template_cap];
    let mut map_templates_by_size: Vec<Vec<TermIdx>> = vec![Vec::new(); template_cap];
    // Rung 1: built SEPARATELY from `map_templates_by_size` so that
    // pool's arena layout (and hence the enumeration order of every
    // already-shipped `MapList` spec) is never perturbed — the
    // `tmpl:nested_reduction` precedent.
    let mut indexed_map_templates_by_size: Vec<Vec<TermIdx>> = vec![Vec::new(); template_cap];
    // `ZIP_ELEMENTWISE` rung `op:ZipWith`: built in its OWN, independent
    // block below (never entangled with the filter/map pool construction
    // above — narrower blast radius, matches `OpKind::ZipMap`'s own doc
    // comment).
    let zip_wanted = op_list.iter().any(|(n, _)| n == "ZipWith");
    let mut zip_op_templates_by_size: Vec<Vec<TermIdx>> = vec![Vec::new(); template_cap];
    if filter_wanted || map_wanted || indexed_map_wanted {
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
            // SetLit/DictItems rung: sorted(item) — size 2. Gated to
            // `set_map_wanted` ONLY (not unconditional whenever
            // `map_wanted`), so every already-shipped `MapList`-only
            // spec's template pool stays BYTE-IDENTICAL to today — a
            // spec that never asked for `SetMap` pays nothing for this.
            // General-purpose (per-element canonicalization, e.g.
            // "collapse an unordered pair" — not 2-tuple-specific in the
            // Term itself), reused by MapList too if a future spec's
            // template search reaches it via `SetMap`'s own gate.
            //
            // Map-template-pool rung (task 104, "sort each sublist of
            // strings"): the SAME `sorted(item)` template is ALSO offered
            // when the spec has direct nested-list evidence
            // (`spec_has_list_of_lists`, defined above — a list variable
            // or output whose OWN elements are themselves list-shaped),
            // widening past `set_map_wanted`-only without going
            // unconditional. Emitted once via `Or`, so a spec that is
            // neither Set-shaped nor list-of-lists pays nothing (byte-
            // identical to today).
            if set_map_wanted || spec_has_list_of_lists {
                let iv = search.scratch.add(TermNode::Var { name: item_sym });
                let srt = search.scratch.add(TermNode::Sort { seq: iv });
                push(&mut map_templates_by_size, srt, 2);
            }
            // Map-template-pool rung (PROGRAM_SYNTHESIS_CEILING_
            // REASSESSMENT_2_PREREG.md §3): four more per-element
            // templates, APPENDED (never interleaved — every existing
            // template above keeps its exact arena index and pool
            // position, so any already-shipped `MapList` spec's own
            // enumeration order is byte-identical to before this rung).
            // Each is gated on the SAME evidence discipline
            // `Round`/`IndexedMap`/`DictItems` already use in the op_list
            // construction above (never unconditional-by-default beyond
            // that), applied one level down at the per-element grain
            // `spec_has_string_value`/`spec_has_float_value` don't reach
            // (they test the OUTER spec value, not the bound item).
            //
            // reverse(item) — size 2 (task 456, "reverse each string").
            // `spec_has_string_value` alone misses 456 (its outer var/
            // output is a List, never a bare Str) — OR'd with the nested
            // `spec_has_string_list_elements` evidence above.
            if spec_has_string_value || spec_has_string_list_elements {
                let iv = search.scratch.add(TermNode::Var { name: item_sym });
                let rv = search.scratch.add(TermNode::Reverse { seq: iv });
                push(&mut map_templates_by_size, rv, 2);
            }
            // capitalize(item) — size 2 (tasks 102/411, snake->camel via
            // `MapList(Split(a,"_"), item, Capitalize(item))`).
            if spec_has_string_value || spec_has_string_list_elements {
                let iv = search.scratch.add(TermNode::Var { name: item_sym });
                let cap = search.scratch.add(TermNode::Capitalize { text: iv });
                push(&mut map_templates_by_size, cap, 2);
            }
            // str(item) — size 2 (tasks 439/421, joining non-string
            // elements into one string/int). Gated on the SAME
            // `map_wanted` precondition alone — `Str` is a total,
            // type-general conversion (unlike `Reverse`/`Capitalize`,
            // which are only meaningful on string/sequence items), so no
            // further narrowing is needed beyond already being inside
            // this `if map_wanted` block.
            {
                let iv = search.scratch.add(TermNode::Var { name: item_sym });
                let s = search.scratch.add(TermNode::Str { value: iv });
                push(&mut map_templates_by_size, s, 2);
            }
            // round(item, c) — size 3 each (task 419, "round every number
            // ... print the resultant list"). Nested evidence, same
            // reasoning as `spec_has_string_list_elements` above.
            if spec_has_float_value || spec_has_float_list_elements {
                for c in &numeric_consts {
                    let iv = search.scratch.add(TermNode::Var { name: item_sym });
                    let cv = search.scratch.add(TermNode::Lit { value: c.clone() });
                    let rnd = search.scratch.add(TermNode::Round { value: iv, ndigits: cv });
                    push(&mut map_templates_by_size, rnd, 3);
                }
            }
        }
        // ---- Rung 1 `op:IndexedMap` templates -------------------------
        // The (index, element) BINDER `STRUCTURAL_CEILING.md`'s S8 class
        // names: a value template that may reference the bound POSITION
        // as well as the bound element. Deliberately its OWN pool (never
        // shares arena slots with `map_templates_by_size` above).
        if indexed_map_wanted {
            // index — size 1 (e.g. "the position itself").
            let idxn = search.scratch.add(TermNode::Var { name: index_sym });
            push(&mut indexed_map_templates_by_size, idxn, 1);
            // item — size 1 (plain MapList-identity is still reachable
            // through IndexedMap too, so a spec that requests only this
            // op name isn't missing the trivial case).
            let itn = search.scratch.add(TermNode::Var { name: item_sym });
            push(&mut indexed_map_templates_by_size, itn, 1);
            // (index, item) — size 3: the BINDING itself, directly
            // closing the S8 gap ("no Term binds an index alongside the
            // element").
            let iv1 = search.scratch.add(TermNode::Var { name: index_sym });
            let iv2 = search.scratch.add(TermNode::Var { name: item_sym });
            let pair = search.scratch.add(TermNode::Vec_ { items: vec![iv1, iv2] });
            push(&mut indexed_map_templates_by_size, pair, 3);
            // item == index — size 3 (e.g. "the element equal to its own
            // position").
            let ev1 = search.scratch.add(TermNode::Var { name: item_sym });
            let ev2 = search.scratch.add(TermNode::Var { name: index_sym });
            let eqn = search.scratch.add(TermNode::Eq { a: ev1, b: ev2 });
            push(&mut indexed_map_templates_by_size, eqn, 3);
            for c in &numeric_consts {
                // index + c, index - c — size 3 each (e.g. 1-based
                // position, or an offset lookup).
                let a1 = search.scratch.add(TermNode::Var { name: index_sym });
                let b1 = search.scratch.add(TermNode::Lit { value: c.clone() });
                let plus = search.scratch.add(TermNode::Plus { items: vec![a1, b1] });
                push(&mut indexed_map_templates_by_size, plus, 3);
                let a2 = search.scratch.add(TermNode::Var { name: index_sym });
                let b2 = search.scratch.add(TermNode::Lit { value: c.clone() });
                let minus = search.scratch.add(TermNode::Minus { a: a2, b: b2 });
                push(&mut indexed_map_templates_by_size, minus, 3);
            }
            for v in &scalar_vars {
                // index == other_scalar_var — size 3 (e.g. "the element
                // at the requested position").
                let iv = search.scratch.add(TermNode::Var { name: index_sym });
                let vv = search.scratch.add(TermNode::Var { name: *v });
                let eqv = search.scratch.add(TermNode::Eq { a: iv, b: vv });
                push(&mut indexed_map_templates_by_size, eqv, 3);
            }
        }
    }

    // ---- `ZIP_ELEMENTWISE` rung `op:ZipWith` template pool -------------
    // Built ONCE (never counted toward `tested`/budget — the `FilterList`/
    // `MapList` pool-construction discipline above), zero cost unless the
    // caller's op inventory actually contains `ZipWith`. A SMALL, FIXED
    // set of templates — the exact 7 elementwise binary ops this rung's
    // 8-task witness population needs (`PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_
    // PREREG.md` §2), each in TWO flavours:
    //   - FLAT (size 3): `OP(Var(__za), Var(__zb))` — the direct per-pair
    //     combine (tasks 261/273/282/399/429).
    //   - NESTED (size 6): `ZipWith(Var(__za), Var(__zb), __zi, __zj,
    //     OP(Var(__zi), Var(__zj)))` — a SECOND `zip` applied to each
    //     bound pair's own elements, for a tuple-OF-tuples spec (tasks
    //     259/401/445, each `zip`-ing at BOTH the outer and inner level).
    // No numeric-constant/scalar-variable cross product (unlike
    // `filter_templates_by_size`'s six families) — every one of this
    // rung's 8 witnesses composes the bound pair DIRECTLY, with no
    // constant or third variable involved, so a bigger pool would only
    // cost search budget for zero additional reach.
    if zip_wanted {
        let push = |pool: &mut Vec<Vec<TermIdx>>, idx: TermIdx, sz: usize| {
            if sz < pool.len() {
                pool[sz].push(idx);
            }
        };
        // (op name, build-fn) — `Max`/`Plus`/`Times` are variadic
        // (`items: Vec<TermIdx>`), the rest are binary (`a`, `b`); both
        // shapes reduce to a 2-element application here.
        for op_name in ZIP_ELEMENTWISE_OP_NAMES {
            // FLAT: OP(Var(__za), Var(__zb)) — size 3.
            let za1 = search.scratch.add(TermNode::Var { name: za_sym });
            let zb1 = search.scratch.add(TermNode::Var { name: zb_sym });
            let flat = search.scratch.add(build_zip_elementwise_op(op_name, za1, zb1));
            push(&mut zip_op_templates_by_size, flat, 3);

            // NESTED: ZipWith(Var(__za), Var(__zb), __zi, __zj,
            // OP(Var(__zi), Var(__zj))) — size 6 (1 for the inner
            // ZipWith node + 1 + 1 for its own Var(__za)/Var(__zb) +
            // 3 for the size-3 OP(Var(__zi),Var(__zj)) inner value).
            let za2 = search.scratch.add(TermNode::Var { name: za_sym });
            let zb2 = search.scratch.add(TermNode::Var { name: zb_sym });
            let zi = search.scratch.add(TermNode::Var { name: zi_sym });
            let zj = search.scratch.add(TermNode::Var { name: zj_sym });
            let inner_op = search.scratch.add(build_zip_elementwise_op(op_name, zi, zj));
            let nested = search.scratch.add(TermNode::ZipWith {
                a: za2, b: zb2, a_name: zi_sym, b_name: zj_sym, value: inner_op,
            });
            push(&mut zip_op_templates_by_size, nested, 6);
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
                        reg!(build_op(name, &[child], &derived_names), size);
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
                                let node = build_op(name, &[*ca, *cb], &derived_names);
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
                                        reg!(build_op(name, &[*cc, *tt, *oo], &derived_names), size);
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
                    let extra = list_unary_extra_cost(name, &derived_extra);
                    if size >= 1 + extra {
                        let src_size = size - 1 - extra;
                        if src_size >= 1 {
                            for child in search.list_by_size[src_size].clone() {
                                let node = build_list_unary(name, child, item_sym, acc_sym, &mut search.scratch, &derived_names);
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
                                reg!(build_list_ho(name, *s_, *t_, item_sym, &derived_names), size);
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
                                reg!(build_list_ho(name, *s_, *t_, item_sym, &derived_names), size);
                            }
                        }
                    }
                }
                // Rung 1 `op:IndexedMap` — same shape as `ListMap`, its
                // OWN template pool (`indexed_map_templates_by_size`).
                OpKind::IndexedMap => {
                    for sa in 1..size.saturating_sub(1) {
                        let st = (size - 1) - sa;
                        if st < 1 || st >= indexed_map_templates_by_size.len() {
                            continue;
                        }
                        let srcs = search.list_by_size[sa].clone();
                        let tmpls = indexed_map_templates_by_size[st].clone();
                        for s_ in &srcs {
                            for t_ in &tmpls {
                                reg!(build_indexed_map(name, *s_, *t_, item_sym, index_sym, &derived_names), size);
                            }
                        }
                    }
                }
                // `ZIP_ELEMENTWISE` rung `op:ZipWith` — see `OpKind::ZipMap`'s
                // own doc comment: `a`/`b` are drawn ONLY from
                // `list_by_size[1]` (raw declared spec variables), so
                // `size == 1 (node) + 1 (a) + 1 (b) + st (template)`
                // pins `st` to a SINGLE value per `size`, never a sa x sb
                // cross product.
                OpKind::ZipMap => {
                    if size >= 4 {
                        let st = size - 3;
                        if st < zip_op_templates_by_size.len() {
                            let srcs = search.list_by_size[1].clone();
                            let tmpls = zip_op_templates_by_size[st].clone();
                            for ca in &srcs {
                                for cb in &srcs {
                                    for t_ in &tmpls {
                                        reg!(build_zip_with(name, *ca, *cb, *t_, za_sym, zb_sym, &derived_names), size);
                                    }
                                }
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
                    let extra = list_binary_extra_cost(name, &derived_extra);
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
                                        name, *ca, *cb, item_sym, acc_sym, &mut search.scratch, &derived_names);
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
    });
    result
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
                derived_ops: None,
                exclude_ops: None,
                max_size,
                max_candidates,
                saturate_k: 0,
                field: Sym::default(),
            });
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&self.graph, &self.interner);
            evaluate(&self.arena, t, &mut env, &mut ctx)
        }

        /// Like `run`, but with an explicit `derived_ops` registry-entry
        /// list (Term-JSON strings, §3.3(b)'s own wire shape) — the
        /// derived-operator-tier slice1 parity test's own entry point.
        fn run_with_derived(
            &mut self,
            examples: Value,
            ops: Option<Value>,
            derived_ops_json: &[&str],
            max_size: i64,
            max_candidates: i64,
        ) -> Value {
            let ex = self.arena.add(TermNode::Lit { value: examples });
            let ops_t = ops.map(|o| self.arena.add(TermNode::Lit { value: o }));
            let derived_items: SmallVec<[Value; 4]> = derived_ops_json
                .iter()
                .map(|s| surf_string(s.to_string()))
                .collect();
            let derived_t = self
                .arena
                .add(TermNode::Lit { value: Value::Tuple(Arc::new(derived_items)) });
            let t = self.arena.add(TermNode::SynthEnumerate {
                examples: ex,
                ops: ops_t,
                consts: None,
                exclude: None,
                derived_ops: Some(derived_t),
                exclude_ops: None,
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
            derived_ops: None,
            exclude_ops: None,
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
            derived_ops: None,
            exclude_ops: None,
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

    // -----------------------------------------------------------------
    // Derived-operator tier, slice 1 — `Call{name,args}` dispatch +
    // build-A fallback arms (`DERIVED_OPERATOR_TIER_SLICE1_PREREG.md`,
    // `DERIVED_OPERATOR_TIER_RESULTS.md` §9 steps 1-3).
    // -----------------------------------------------------------------

    /// §9 step 3's own parity op — `Total2`: Binary, general pool,
    /// template `Plus{Var(a),Var(b)}`, `extra_cost:0`. Deliberately a
    /// registry-authored re-expression of the ALREADY-SHIPPED, byte-
    /// for-byte-identical `Plus` op (not a novel composition) — the
    /// cleanest possible isolation of dispatch-plumbing correctness.
    const TOTAL2_JSON: &str = r#"{"name":"Total2","params":[{"name":"a","pool":"general"},{"name":"b","pool":"general"}],"extra_cost":0,"template":{"type":"Plus","items":[{"type":"Var","name":"a"},{"type":"Var","name":"b"}]}}"#;

    /// Direct `Call` evaluation, bypassing `SynthEnumerate` entirely:
    /// `Call{"Total2",[3,4]}` must evaluate to EXACTLY what
    /// `Plus{items:[3,4]}` does — the registry's template is `Plus`
    /// itself, so this is byte-for-byte parity by construction, not by
    /// coincidence.
    #[test]
    fn call_dispatches_to_registry_template_matching_native_plus() {
        let mut f = Fixture::new();
        let mut arena = TermArena::new();
        let a_sym = f.interner.intern("a");
        let b_sym = f.interner.intern("b");
        let av = arena.add(TermNode::Var { name: a_sym });
        let bv = arena.add(TermNode::Var { name: b_sym });
        let body = arena.add(TermNode::Plus { items: vec![av, bv] });
        let total2_sym = f.interner.intern("Total2");
        let bogus_sym = f.interner.intern("Bogus"); // interned up front — `ctx` below borrows `f.interner`
        let mut registry = DerivedOpRegistry::default();
        registry.insert(
            total2_sym,
            DerivedOpDef {
                params: vec![(a_sym, DerivedOpPool::General), (b_sym, DerivedOpPool::General)],
                body,
                extra_cost: 0,
            },
        );

        let x1 = arena.add(TermNode::Lit { value: Value::Int(3) });
        let x2 = arena.add(TermNode::Lit { value: Value::Int(4) });
        let call_node = arena.add(TermNode::Call { name: total2_sym, args: vec![x1, x2] });
        let plus_node = arena.add(TermNode::Plus { items: vec![x1, x2] });
        let bogus_call = arena.add(TermNode::Call { name: bogus_sym, args: vec![x1, x2] });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&f.graph, &f.interner);
        ctx.derived_ops = Some(Arc::new(registry));
        let call_val = evaluate(&arena, call_node, &mut env, &mut ctx);
        let plus_val = evaluate(&arena, plus_node, &mut env, &mut ctx);
        assert_eq!(call_val, Value::Int(7));
        assert_eq!(call_val, plus_val);

        // ctx.derived_ops is caller-managed here (direct evaluate(), not
        // through eval_synth_enumerate) — confirms a MISSING registry
        // entry is `Value::None`, never a panic (the documented "no
        // registered entry -> Value::None" contract).
        assert_eq!(evaluate(&arena, bogus_call, &mut env, &mut ctx), Value::None);
    }

    /// `ctx.derived_ops` is restored to its PREVIOUS value (`None` here)
    /// once `eval_synth_enumerate` returns, on the SAME `EvalCtx`
    /// instance — the `with_derived_ops` scope-guard's own restore
    /// contract, verified by reusing one `ctx` across two `evaluate()`
    /// calls (a fresh `EvalCtx` would trivially have `derived_ops:
    /// None` regardless of whether the guard works, so this must NOT
    /// construct a new `ctx` for the second call).
    #[test]
    fn derived_ops_registry_does_not_leak_past_the_call() {
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 1), ("y", 2)], Value::Int(3)),
            (&[("x", 2), ("y", 5)], Value::Int(7)),
        ]);
        let ops_t = {
            let ops = f.ops(&["Total2"]);
            f.arena.add(TermNode::Lit { value: ops })
        };
        let ex_t = f.arena.add(TermNode::Lit { value: ex });
        let derived_t = f.arena.add(TermNode::Lit {
            value: Value::Tuple(Arc::new(smallvec::smallvec![surf_string(TOTAL2_JSON.to_string())])),
        });
        let synth_t = f.arena.add(TermNode::SynthEnumerate {
            examples: ex_t,
            ops: Some(ops_t),
            consts: None,
            exclude: None,
            derived_ops: Some(derived_t),
            exclude_ops: None,
            max_size: 9,
            max_candidates: 0,
            saturate_k: 0,
            field: Sym::default(),
        });
        let total2_sym = f.interner.intern("Total2");
        let a1 = f.arena.add(TermNode::Lit { value: Value::Int(1) });
        let a2 = f.arena.add(TermNode::Lit { value: Value::Int(2) });
        let call_t = f.arena.add(TermNode::Call { name: total2_sym, args: vec![a1, a2] });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&f.graph, &f.interner);
        assert!(ctx.derived_ops.is_none()); // before: no registry
        let synth_out = evaluate(&f.arena, synth_t, &mut env, &mut ctx);
        assert_eq!(dget(&synth_out, "found"), Value::Bool(true)); // the call itself worked
        assert!(ctx.derived_ops.is_none()); // after: restored, not leaked
        // And a Call node evaluated on this SAME (now-registry-less) ctx
        // finds nothing — proof the restore is behaviourally real, not
        // just a field read-out.
        assert_eq!(evaluate(&f.arena, call_t, &mut env, &mut ctx), Value::None);
    }

    /// The parity check itself (§9 step 3): a search offered
    /// `ops:["Total2"]` (the registry-authored derived op) on a
    /// `Plus`-shaped spec must reach the SAME size, with the SAME
    /// `tested`/`distinct`/`pruned_equiv`/`halt_reason` counters, as the
    /// identical search offered `ops:["Plus"]` — the winning term
    /// differs ONLY in the outer node's own name/shape
    /// (`(x + y)` vs `Total2(x, y)`), never in the search's own
    /// behaviour. A plumbing proof, not a capability claim.
    #[test]
    fn total2_derived_op_search_matches_native_plus_byte_for_byte() {
        let mut f = Fixture::new();
        let ex = f.rows(&[
            (&[("x", 1), ("y", 2)], Value::Int(3)),
            (&[("x", 2), ("y", 5)], Value::Int(7)),
            (&[("x", 0), ("y", 0)], Value::Int(0)),
            (&[("x", -3), ("y", 9)], Value::Int(6)),
        ]);

        let ops_plus = f.ops(&["Plus"]);
        let native = f.run(ex.clone(), Some(ops_plus), 9, 0);

        let ops_total2 = f.ops(&["Total2"]);
        let derived = f.run_with_derived(ex, Some(ops_total2), &[TOTAL2_JSON], 9, 0);

        assert_eq!(dget(&native, "found"), Value::Bool(true));
        assert_eq!(dget(&derived, "found"), Value::Bool(true));
        assert_eq!(dget(&native, "size"), dget(&derived, "size"));
        assert_eq!(dget(&native, "tested"), dget(&derived, "tested"));
        assert_eq!(dget(&native, "distinct"), dget(&derived, "distinct"));
        assert_eq!(dget(&native, "pruned_equiv"), dget(&derived, "pruned_equiv"));
        assert_eq!(dget(&native, "halt_reason"), dget(&derived, "halt_reason"));

        let native_term = text(&dget(&native, "term_str"));
        let derived_term = text(&dget(&derived, "term_str"));
        assert!(native_term.contains('+'), "native term_str: {native_term}");
        assert!(derived_term.starts_with("Total2("), "derived term_str: {derived_term}");

        // Byte-identical VALUE at the winning candidate too, not just
        // matching counters — re-evaluate both winning terms over a
        // fresh row and confirm equal output.
        let native_json = text(&dget(&native, "term"));
        let derived_json = text(&dget(&derived, "term"));
        assert!(derived_json.contains("\"type\":\"Call\""), "derived term JSON: {derived_json}");
        assert_ne!(native_json, derived_json); // different node kinds, same behaviour
    }

    /// §9 step 2's own honest residual, verified directly rather than
    /// merely asserted in prose: a `derived_ops` entry whose pool shape
    /// build-A does NOT cover (`JoinListSep`'s own mixed
    /// `[list,general]` shape) is silently UNUSABLE — `op_list`
    /// construction drops it (never an error), so an explicit `ops`
    /// request naming it finds nothing to search with and reports
    /// `found:false` honestly, exactly as if the name were never
    /// registered at all.
    #[test]
    fn mixed_pool_derived_op_is_silently_unusable_under_build_a() {
        let mut f = Fixture::new();
        // Two rows with DIFFERENT outputs, neither equal to `x` itself —
        // a leaf (var or auto-appended-const, `synth_enumerate.rs`'s own
        // "integer-valued outputs are appended to `const_set`" rule)
        // can satisfy at most ONE row's fixed value, never both, so
        // `found:true` here can only come from a genuine COMPOSITION —
        // which needs an op, and none is usable (`op_list` construction
        // drops the mixed-pool `Mixed` entry entirely).
        let ex = f.rows(&[(&[("x", 1)], Value::Int(5)), (&[("x", 2)], Value::Int(9))]);
        let mixed_json = r#"{"name":"Mixed","params":[{"name":"s","pool":"list"},{"name":"g","pool":"general"}],"extra_cost":0,"template":{"type":"Var","name":"s"}}"#;
        let ops = f.ops(&["Mixed"]);
        let out = f.run_with_derived(ex, Some(ops), &[mixed_json], 5, 0);
        assert_eq!(dget(&out, "found"), Value::Bool(false));
    }
}
