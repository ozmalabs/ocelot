//! Term arena + all DSL variants + `evaluate`.
//!
//! 1:1 port of `substrate/dsl.py`. Every Term head is a variant of
//! [`TermNode`]; the tree lives in a [`TermArena`] (a flat
//! `Vec<TermNode>`) and children are referenced by [`TermIdx`] u32
//! indices, not Box, so the whole tree is one allocation.
//!
//! Evaluation matches Python semantics — same truthiness rules, same
//! recursion depth guard on `Holds`, same memoisation surface on
//! `Filter` and `Neighbours`. The hot-path optimisations (Sym
//! comparisons everywhere, SmallVec env, contiguous arena) come from
//! the Rust side; behaviour stays identical.

use crate::argmin_tie;
use crate::ext::Counters;
use crate::graph::{NodeID, TypedGraph};
use crate::selector_audit;
use crate::sym::{Interner, Sym};
use crate::value::{cmp_value, SurfaceKind, Value};
use rustc_hash::FxHashMap;
use smallvec::{smallvec, SmallVec};
use std::sync::Arc;

/// Arena-relative handle for a Term tree node.
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub struct TermIdx(pub u32);

/// One node of a Term tree. The variant set mirrors `substrate/dsl.py`
/// exactly; field names match where reasonable so reflection
/// (`term_to_subgraph`) can carry over without renames.
#[derive(Clone, Debug)]
pub enum TermNode {
    // --- bindings & access ---
    Var {
        name: Sym,
    },
    Lit {
        value: Value,
    },
    TypeOf {
        node: TermIdx,
    },
    Attr {
        node: TermIdx,
        key: Sym,
    },

    /// Effectful tool-dispatch boundary — the engine's first effectful
    /// boundary Term. `tool` is an interned tool name (mirrors `Attr`'s
    /// `key`); `args` are child terms evaluated to Values then handed to
    /// the registered Python handler (see `tools::call_tool`). The handler's
    /// return converts back to a Value, so a tool call COMPOSES inside an
    /// engine-evaluated Term-tree (e.g. `Plus(UseTool("gcd",[48,36]), 1)`).
    /// Missing handler / handler error degrades to a safe default
    /// (`Int(0)`) — the evaluator never panics on the tool boundary.
    UseTool {
        tool: Sym,
        args: Vec<TermIdx>,
    },

    // --- collections ---
    SetT {
        items: Vec<TermIdx>,
    },
    In {
        member: TermIdx,
        container: TermIdx,
    },

    // --- comparators ---
    Eq {
        a: TermIdx,
        b: TermIdx,
    },
    Lt {
        a: TermIdx,
        b: TermIdx,
    },
    Lte {
        a: TermIdx,
        b: TermIdx,
    },
    Gt {
        a: TermIdx,
        b: TermIdx,
    },
    Gte {
        a: TermIdx,
        b: TermIdx,
    },

    // --- graph traversal ---
    /// `edge_type` is `Sym::default()` to mean "any edge type".
    ReachableFrom {
        node: TermIdx,
        edge_type: Sym,
        any_type: bool,
    },

    Neighbours {
        node: TermIdx,
        edge_type: Sym,
        any_type: bool,
    },
    /// Slide-neighbours: from a grid cell, the up-to-4 cells exactly `slide` clear-floor steps away
    /// along the `neighbour` lattice (value==ground each step). On-demand oracle for foveated nav.
    SlideNeighbours {
        cell: TermIdx,
        slide: TermIdx,
        ground: TermIdx,
    },
    InNeighbours {
        node: TermIdx,
        edge_type: Sym,
        any_type: bool,
    },
    MapNeighbours {
        source: TermIdx,
        edge_type: Sym,
        any_type: bool,
    },

    // --- reductions ---
    Count {
        source: TermIdx,
    },
    Filter {
        source: TermIdx,
        var_name: Sym,
        predicate: TermIdx,
    },
    /// Ordered (list) twin of Filter — preserves source order + duplicates,
    /// returns a **`Value::List`** (ARC6 value layer; it returned a `Tuple`
    /// before there was a list). Its own reason for existing is to be
    /// "the faithful target for a Python LIST comprehension's `if`"
    /// (Filter returns a set), and in CPython `[x for x in t if p]` is a
    /// LIST even when `t` is a tuple. Added via the Layer-B self-extension loop.
    FilterList {
        source: TermIdx,
        var_name: Sym,
        predicate: TermIdx,
    },
    Exists {
        source: TermIdx,
        var_name: Sym,
        predicate: TermIdx,
    },
    Sum {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
    },
    Prod {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
    },
    MinOver {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
        default: Option<TermIdx>,
    },
    MaxOver {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
        default: Option<TermIdx>,
    },
    Pick {
        source: TermIdx,
    },
    /// PickUnique: Pick, but LOUD when the selection is AMBIGUOUS.
    ///
    /// `Pick` returns `iter().next()` — an arbitrary element — so a config read
    /// like `Pick(NodesOfType("EyeParams"))` silently returns ONE of N params
    /// nodes and the other N-1 are ignored without a word. That is the same
    /// disease as `.get('Name','')` and a guarded division returning 0.0: a
    /// silent wrong answer where there should be an error (VISION_PROTOCOL
    /// §1.1, §12). It is latent under exactly the mechanism a per-eye arm
    /// (monocular deprivation's `eye_open`) would depend on.
    ///
    /// 0 or 1 elements behave EXACTLY as `Pick` (None / the element), so every
    /// committed result on a well-formed graph is byte-identical; >1 panics.
    PickUnique {
        source: TermIdx,
    },

    /// Tokenize a string by whitespace; returns Value::Tuple
    /// of (start, byte_len) Int pairs. Agent-built via babble loop.
    Tokenize {
        text: TermIdx,
    },
    MorphHead {
        text: TermIdx,
    },
    MorphTail {
        text: TermIdx,
    },
    FinalToken {
        text: TermIdx,
    },
    /// Tokenize2 — same as Tokenize. Agent-built via babble loop.
    Tokenize2 {
        text: TermIdx,
    },
    /// Read a file at `path` (a Str). Returns Value::Surface(Text, ...)
    /// with the file contents on success, or Value::None on any error.
    /// Agent-built via babble loop.
    ReadFile {
        path: TermIdx,
    },
    /// Find `needle` in `haystack` (both Strs). Returns Value::Int with the
    /// byte offset, or -1 if not found / non-string inputs. Agent-built.
    StringIndexOf {
        haystack: TermIdx,
        needle: TermIdx,
    },
    /// Byte-slice `s[start..end]`. `s` is a Str; start/end are Ints.
    /// Out-of-bounds clamps to 0..len. Returns Value::Surface(Text, ...).
    /// Non-string `s` returns an empty Text surface. Agent-built.
    StringSlice {
        s: TermIdx,
        start: TermIdx,
        end: TermIdx,
    },
    /// Concatenate Str / Surface(Text) `parts` into a single Text surface.
    /// Other value types are skipped. Agent-built via babble loop.
    StringConcat {
        parts: Vec<TermIdx>,
    },

    // -----------------------------------------------------------------
    // PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md Rung 1
    // (Tier 1 stdlib Term ports, `STRUCTURAL_CEILING.md` §9 order) — each
    // is a Term-layer port of a behaviour `ProgEval` already runs
    // (`STRUCTURAL_CEILING.md` §2: the pipeline could already RUN these,
    // it could not PROPOSE them from the enumerator's own op table).
    // CLAUDE.md's THIRD, sanctioned "new primitive" pathway: "add a new
    // DSL Term" — a primitive, not a shape/codebook growth (Q1 of the
    // reassessment doc: this layer needs Rust, not sd-loop machinery).
    // -----------------------------------------------------------------
    /// `str.replace(old, new)` (Python's un-countedreplace-all form —
    /// `Rust`'s `str::replace` has identical semantics for an empty
    /// pattern, inserting between every character, so no special case is
    /// needed). Non-string-like `text`/`old`/`new` -> an empty Text
    /// surface (the `StringSlice` refusal convention).
    Replace {
        text: TermIdx,
        old: TermIdx,
        new: TermIdx,
    },
    /// Python `str(value)` — coerce ANY Value to its Python-spelled
    /// string form (`prog_eval::py_str`, reused directly so this Term's
    /// spelling can never drift from the `ProgEval` interpreter's own
    /// `str()`/f-string rendering).  S5 ("Value -> string coercion", e.g.
    /// `Join` emitting `Int(4)` for a non-string element) is this Term
    /// composed with `StringConcat`.
    Str {
        value: TermIdx,
    },
    /// `str.split(sep)` — `sep` evaluating to `Value::None` (or an
    /// empty/non-string value) falls back to Python's no-arg
    /// whitespace-split (never a trap: an enumerated candidate has no
    /// error channel, see `synth_enumerate.rs`'s module docs). Returns a
    /// `Value::List` of Surface(Text) parts, matching CPython's
    /// `str.split` list return.
    Split {
        text: TermIdx,
        sep: TermIdx,
    },
    /// Count NON-OVERLAPPING occurrences of `sub` in `text`
    /// (`str.count`, ProgEval's own semantics ported directly: an empty
    /// `sub` counts as `char_count + 1`). Distinct from the already-
    /// shipped `Count` Term (sequence LENGTH, tier-0's
    /// `fix:StringAsSequence`) — this is substring occurrence counting
    /// (`STRUCTURAL_CEILING.md` task 172).
    StrCount {
        text: TermIdx,
        sub: TermIdx,
    },
    /// Python's 2-arg `round(value, ndigits)`, round-half-to-even
    /// (`prog_eval::round_half_even_digits`, reused directly). Preserves
    /// Python's own type rule: `Int` input with `ndigits >= 0` returns
    /// the `Int` unchanged; `Int` with negative `ndigits`, or any
    /// `Float`/`Rational` input, returns a `Float`. `ndigits` coerces via
    /// `Value::as_i64` (so a Bool/Float ndigits behaves as it does
    /// everywhere else in this engine); non-numeric `value` -> the
    /// unevaluated `Value::None`.
    Round {
        value: TermIdx,
        ndigits: TermIdx,
    },
    /// `reversed(seq)`, TYPE-PRESERVING: a `Str`/`Surface(Text)` reverses
    /// to text, a `Value::List` to a `List`, a `Value::Tuple` to a
    /// `Tuple` (CPython's own `l[::-1]` vs `t[::-1]` distinction, the
    /// same list/tuple identity the ARC6 value layer made possible).
    /// Non-reversible input passes through unchanged.
    Reverse {
        seq: TermIdx,
    },
    /// `[value for index, item in enumerate(source)]` — the (index,
    /// element) BINDER `STRUCTURAL_CEILING.md`'s S8 class names as the
    /// missing primitive (position is already an in-frame integer
    /// `IndexAt` can read; nothing bound it INTO a map body alongside
    /// the element). Iterates `source`'s items in order, pushing BOTH
    /// `item_name` -> the element and `index_name` -> its 0-based
    /// position before evaluating `value`, popping both after. Modelled
    /// directly on `MapList`'s env-push/pop shape, generalised to two
    /// bound variables instead of one. Non-list-like `source` -> an
    /// empty `Value::List`.
    IndexedMap {
        source: TermIdx,
        item_name: Sym,
        index_name: Sym,
        value: TermIdx,
    },
    /// `str.capitalize()` — first character uppercased, the rest
    /// lowercased (ProgEval's `call_recv_oracle` "capitalize" arm,
    /// ported verbatim). Non-string-like `text` -> an empty Text
    /// surface.
    Capitalize {
        text: TermIdx,
    },
    /// Python `int(s)` for a string argument ONLY (the numeric-input
    /// arms of ProgEval's `"int"` extern — `Int`/`Float`/`Bool`/
    /// `Rational` truncation — are already reachable via the shipped
    /// `IDiv`/cast-free arithmetic Terms, so this Term ports exactly the
    /// missing S16 case, task 439: parsing a STRING into an int).
    /// Trimmed before parsing (CPython's own `int()` behaviour); a
    /// non-string-like or unparseable argument -> `Value::None` (never a
    /// panic — this engine's Term evaluator has no error channel).
    ParseInt {
        text: TermIdx,
    },
    /// General sequence slice `seq[start:stop]`, negative-index-correct
    /// (CPython's `PySlice_AdjustIndices` algorithm,
    /// `prog_eval::slice_indices`, reused directly — the fix for
    /// `StringSlice`'s measured refusal of a negative end,
    /// `STRUCTURAL_CEILING.md` §7.5) and TYPE-GENERAL: `Str`/
    /// `Surface(Text)`, `Value::List`, and `Value::Tuple` all slice,
    /// preserving their own container kind. Step is always 1 (no
    /// 4-operand op exists at the enumerator's grammar level — the
    /// negative-index/type-generality fix is the whole point of this
    /// unit, per `STRUCTURAL_CEILING.md` §9's own ordering, not a
    /// strided-slice widening). Deliberately the LAST Tier-1 unit
    /// landed (§5.1 of the reassessment doc): its blast radius is the
    /// largest of the ten (touches slicing semantics generally), so it
    /// lands only after the other nine validate the "one Term, byte-
    /// identical regression sweep" workflow. Unsliceable input -> an
    /// empty Text surface.
    Slice {
        seq: TermIdx,
        start: TermIdx,
        stop: TermIdx,
    },
    /// `sorted(seq)`, ascending, via the already-shipped
    /// `cmp_value_lex` (the SAME comparator `Lt`/`Gt`/`Argmax`/`MinOver`/
    /// the `sorted`/`min`/`max` `ProgEval` externs already use —
    /// `cmp_value` itself, the boot-order-dependent canonicalisation
    /// comparator, is NEVER touched by this Term, so it carries none of
    /// the cross-cutting fixture risk `STRUCTURAL_CEILING.md` §7.2 named
    /// for a naive `Sort`; see `PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_
    /// RUNG2_RUNG3_PREREG.md`'s own Step 2, which vetted exactly this
    /// reuse). TYPE-PRESERVING like `Reverse`: `Value::List` sorts to a
    /// `List`, `Value::Tuple` to a `Tuple` — a 2-element tuple sorted
    /// this way is precisely CPython's `tuple(sorted(pair))` canonical
    /// form. `Value::Set`/`Value::FrozenSet` pass through unchanged
    /// (already canonically ordered by construction). Non-sequence input
    /// passes through unchanged (the `Reverse` degrade precedent).
    Sort {
        seq: TermIdx,
    },
    /// DictItems/SortBy rung (`PROGRAM_SYNTHESIS_DICTITEMS_SORTBY_PREREG.md`,
    /// task 475 `sort_counter`/`Counter.most_common()`): Python's
    /// `dict.items()` — a `Value::Dict` becomes a `Value::Tuple` of
    /// `(key, value)` 2-tuples, in the Dict's own stored order.
    /// `OpKind::Unary`, sourced from the enumerator's general `by_size`
    /// pool exactly like `Sort`/`Reverse` (zero new registration
    /// machinery). Non-Dict input passes through unchanged (the `Sort`/
    /// `Reverse` degrade precedent).
    DictItems {
        seq: TermIdx,
    },
    /// DictItems/SortBy rung: `sorted(source, key=lambda item: key(item))`
    /// — a STABLE sort of `source`'s elements by a PROJECTED key (the
    /// `item` binder evaluates `key` per element), keeping the ORIGINAL
    /// elements (unlike `MapList`, whose template computes the OUTPUT
    /// value; here the template computes only the sort key). Ascending;
    /// compose with `Reverse` for descending (`Counter.most_common()`'s
    /// shape). Reuses `OpKind::ListMap`'s search-registration path and
    /// `map_templates_by_size` template pool verbatim (see PREREG §3) —
    /// the same binder shape as `MapList`/`MapSet`/`IndexedMap`. Uses
    /// `cmp_value_lex` for the key comparison, the same comparator
    /// `Sort` already uses. Non-listlike source passes through unchanged.
    SortBy {
        source: TermIdx,
        var_name: Sym,
        key: TermIdx,
    },
    /// GroupCount/DictMerge rung (`PROGRAM_SYNTHESIS_GROUPCOUNT_DICTMERGE_
    /// PREREG.md`, task 88 `freq_count` — Python's `Counter(seq)` /
    /// "get the frequency of all elements in a list, returned as a
    /// dictionary"): builds a `Value::Dict` mapping each DISTINCT element
    /// of `seq` to its occurrence count (`Value::Int`). `OpKind::Unary`,
    /// sourced from the enumerator's general `by_size` pool exactly like
    /// `Sort`/`DictItems` (zero new registration machinery). Grouping uses
    /// `Value`'s own structural `PartialEq` (the same equality every other
    /// Term in this file already relies on); output pairs are canonically
    /// sorted by `cmp_value`, the SAME invariant `MkDict` maintains, so a
    /// `GroupCount`-built Dict compares equal to any other dict with the
    /// same key/count pairs regardless of build path. `Value::List`/
    /// `Value::Tuple` input only (the `Sort`/`Reverse` scope); non-listlike
    /// input passes through unchanged (the same degrade precedent).
    GroupCount {
        seq: TermIdx,
    },
    /// GroupCount/DictMerge rung (task 87 `merge_dictionaries_three` —
    /// "merge three dictionaries into a single dictionary"): Python's
    /// `{**a, **b}` / `dict.update` — `b`'s entries win over `a`'s on a
    /// KEY COLLISION, `a`'s entries are kept where `b` has no matching key.
    /// `OpKind::Binary`. A 3-way merge is NOT a new arity — it composes
    /// exactly like every other binary reduction in this arc
    /// (`ConcatList(ConcatList(a,b),c)`, task 108's own witness): nesting
    /// `DictMerge(DictMerge(dict3,dict2),dict1)` gives dict1 the highest
    /// priority, matching MBPP task 87's own asserted precedence (verified
    /// against its real fixture rows in the PREREG, not assumed from the
    /// prompt text). Output pairs canonically sorted by `cmp_value`, same
    /// as `GroupCount`/`MkDict`. Non-Dict-Dict input degrades to `a`
    /// unchanged (never panics; mirrors this file's standing degrade
    /// convention for a type-mismatched operand).
    DictMerge {
        a: TermIdx,
        b: TermIdx,
    },
    /// `ZIP_ELEMENTWISE` rung (`PROGRAM_SYNTHESIS_ZIP_ELEMENTWISE_PREREG.md`,
    /// an 8-task MBPP cluster — 259/261/273/282/399/401/429/445 — all
    /// needing Python's `zip(a, b)` paired with a per-pair binary
    /// combiner, e.g. `tuple(x - y for x, y in zip(a, b))`): iterates `a`
    /// and `b` IN LOCKSTEP (Python `zip` truncation semantics — stops at
    /// `min(len(a), len(b))`), binding each pair's two elements to
    /// `a_name`/`b_name` before evaluating `value`, popping both after.
    /// Modelled directly on `IndexedMap`'s two-bound-variable-over-one-
    /// source shape, generalised to TWO sources instead of one (the same
    /// generalisation `IndexedMap`'s own doc comment already applied to
    /// `MapList`) — and on the already-shipped `vec_binary` helper
    /// (`VecAdd`/`VecSub`), which already zips two operands with a FIXED
    /// op; this Term is that same zip shape with the op made a Term
    /// argument instead of a hard-coded closure, so nested tasks (259/
    /// 401/445 — a tuple OF tuples, needing `zip` applied at BOTH the
    /// outer and inner level) compose as `ZipWith` calling `ZipWith`
    /// again in its own `value`, rather than needing a second Term.
    /// Output container kind follows `a` (`Value::reseq` — the
    /// `RewriteTreeNodes`/`ShiftThresholdLits` kind-preserving precedent),
    /// so a List-in/List-out spec (task 282) and a Tuple-in/Tuple-out
    /// spec (the other 7) both round-trip their own container kind
    /// without a separate coercion step. Non-listlike `a`/`b` -> an empty
    /// sequence of `a`'s own kind (the `MapList`/`Reverse` degrade
    /// precedent: `av.snapshot()` is empty for a non-collection `Value`,
    /// so the loop simply never runs).
    ZipWith {
        a: TermIdx,
        b: TermIdx,
        a_name: Sym,
        b_name: Sym,
        value: TermIdx,
    },
    /// Verify that `term` (evaluated under bindings from `env`) equals
    /// `expected`. `env` should evaluate to a Value::Dict of
    /// (Str, Value) pairs — each entry is pushed onto the eval env
    /// stack as a Var binding before `term` runs, then popped. Non-Dict
    /// `env` → empty bindings (term still evaluated). Returns
    /// Value::Bool(term_result == expected_result). The substrate's
    /// "does this Term-tree compute X" primitive.
    Verify {
        term: TermIdx,
        env: TermIdx,
        expected: TermIdx,
    },

    /// Build a `Value::Dict` at evaluate time from an alternating
    /// (key, value, key, value, ...) list of child Terms. Each pair
    /// (items[2i], items[2i+1]) is evaluated; the key must evaluate
    /// to `Value::Str` or `Value::Surface(Text)` (otherwise the
    /// pair is skipped); the value may be any Value. Pairs are
    /// sorted by key with `cmp_value` to match the canonical-order
    /// invariant used by `decode_value` / `Value::Dict` construction
    /// elsewhere. Odd-length items: the trailing key with no value
    /// is dropped. This is the substrate's generic Term-tree
    /// composition primitive — rule effects compose Term-JSON-shaped
    /// Dicts at fire time with match-binding values spliced in.
    MkDict {
        items: Vec<TermIdx>,
    },

    /// Serialise `value` (any evaluated Value -- Dict/Tuple/scalars,
    /// typically built by `MkDict`/`Append`) to JSON text, returned as
    /// `Value::Surface(Text, ...)` -- the same Str-vs-Surface convention
    /// `StringConcat` already uses (both are treated as string-like by
    /// `SetRuleClause`/`set_attr` consumers; see finding 4 in
    /// tests/test_rule_minting_dialect.py). This is what lets a meta-rule
    /// build a nested Term-tree (e.g. a list of rule-dicts for a
    /// `SeedDelta`'s `add_rules`) and land it in a single flat STRING
    /// attr the way `domains/experiment_dispatch.py`'s
    /// `json.loads(delta.add_rules)` requires -- `MkDict`/`Append` alone
    /// produce a graph-native `Value::Dict`/`Tuple`, which `json.loads`
    /// can't consume directly (it would raise on a non-str argument).
    /// `Value::Node` and `Value::Surface(Bytes, ...)` serialise to JSON
    /// `null` (Term-JSON trees never carry either); Dict keys that
    /// aren't string-shaped serialise via their debug form, matching
    /// `MkDict`'s own key-shape leniency.
    ToJsonString {
        value: TermIdx,
    },

    /// Inverse of `ToJsonString`: parse `text` (a Str or Surface(Text)
    /// holding JSON) into a graph-native `Value` tree -- JSON object ->
    /// `Value::Dict` (keys as `Surface(Text)` -- `evaluate()` can't
    /// intern new Syms, the same reason `StringConcat` returns Surface
    /// rather than Str), array -> `Value::Tuple`, string ->
    /// `Value::Surface(Text)`, number -> `Value::Int` (no fractional
    /// part) or `Value::Float`, true/false -> `Value::Bool`, null ->
    /// `Value::None`. Invalid JSON or a non-string-shaped `text` ->
    /// `Value::None`. Lets a meta-rule read a JSON-string provenance
    /// attr (e.g. a `RuleSummary.rule_json` mirror,
    /// `domains/reflective_faculty.py::_ensure_acting_rule_provenance`)
    /// back into Term-tree land for structural inspection/rewrite (see
    /// `ShiftThresholdLits`).
    FromJsonString {
        text: TermIdx,
    },

    /// Deep-copy `tree` (a Value tree -- typically from `FromJsonString`,
    /// or a graph-native Rule node's own `effect`/`where` attr, which are
    /// ALREADY nested Dict/Tuple Values, never JSON strings), shifting
    /// every numeric decision-threshold `Lit` it finds: a
    /// `{"type":"Lt","b":{"type":"Lit","value":N}}` node's N becomes
    /// N - `shift`; a `{"type":"Gt", ...}` node's N becomes N + `shift`.
    /// Every other Dict/Tuple node is copied unchanged, recursing so a
    /// nested Lt/Gt deeper in the tree (inside `a`, inside a compound
    /// `Plus`/`And`, etc.) is still found and shifted. Mirrors
    /// `domains/reflective_faculty.py`'s `_find_threshold_lits` +
    /// `_shift_rule_thresholds` exactly (a mechanical structural walk
    /// over a rule's exported effects -- no interpretation of what a
    /// threshold MEANS, only how many exist and where) -- the
    /// graph-native primitive that was missing for a meta-rule to do the
    /// same rewrite itself instead of calling out to a host Python
    /// helper. `shift` coerces via `Value::as_f64`.
    ShiftThresholdLits {
        tree: TermIdx,
        shift: TermIdx,
    },

    /// Read a field out of a `Value::Dict` by key -- the Dict-VALUE twin
    /// of `Attr` (which only reads graph-Node attrs: `Attr(some_dict, k)`
    /// is always `Value::None`, since `Attr`'s evaluator requires
    /// `Value::Node`). `key` evaluates to a string-like value (`Str` or
    /// `Surface(Text)` -- both, so it reads a `MkDict`-built Dict, whose
    /// keys are usually `Str`, and a `FromJsonString`-parsed Dict, whose
    /// keys are `Surface(Text)`, uniformly). The first pair whose key
    /// matches wins; `Value::None` if `dict` isn't a Dict or no pair
    /// matches. Discovered missing while wiring `ShiftThresholdLits`
    /// output back into a new rule structure (`MkDict(L("match"),
    /// DictGet(parsed, L("match")), ...)`) -- reading a parsed rule's own
    /// `match`/`where`/`effects` fields back out of the `FromJsonString`
    /// result has no other route through the existing dialect.
    DictGet {
        dict: TermIdx,
        key: TermIdx,
    },

    /// Deep-copy `tree` (a Value tree -- typically from `FromJsonString`,
    /// or a graph-native Rule node's own `effect`/`where` attr), and for
    /// every Dict node reachable inside it (recursing into children
    /// FIRST, exactly like `ShiftThresholdLits` -- so a nested match is
    /// still found and rewritten): if `type_filter` is `Some`, require
    /// the node's own `"type"` field to string-like-equal it (skip the
    /// node otherwise); then look up the node's `field` entry's CURRENT
    /// value in `value_map` (a Dict Value, e.g. `MkDict`-built, mapping
    /// old field-values -> new field-values, string-like compared the
    /// same way `DictGet` compares keys) -- if a mapping is found,
    /// replace ONLY that one field's value with the mapped value,
    /// leaving every other field (including `type` itself when `field`
    /// is something else) untouched. `type_filter == None` matches every
    /// Dict node (the flip-comparison case: the field being CHECKED --
    /// `"type"` -- is the SAME field being REWRITTEN, so a separate
    /// guard would be redundant with `value_map`'s own keys).
    ///
    /// The general conditional-tree-rewrite primitive
    /// `domains/edit_ops.py`'s two effects-only structural appliers need
    /// -- both are "walk a Value tree, where a node matches a predicate,
    /// set ONE field" with a different predicate/field pair, so ONE Term
    /// covers both rather than two narrow ones:
    ///
    ///   - `apply_flip_comparison` (Lt<->Gt, Lte<->Gte): `type_filter =
    ///     None`, `field = "type"`, `value_map = {"Lt":"Gt","Gt":"Lt",
    ///     "Lte":"Gte","Gte":"Lte"}` -- all four pairs in ONE pass (never
    ///     sequential re-application, which would double-flip a node
    ///     touched by an earlier pass).
    ///   - `apply_swap_term_leaf` (swap which attr key a decision reads):
    ///     `type_filter = "Attr"`, `field = "key"`, `value_map =
    ///     {old_key: new_key}`.
    ///
    /// `ShiftThresholdLits` stays its own narrower Term (it rewrites a
    /// NUMERIC VALUE by an arithmetic shift depending on which of two
    /// types the node is, not a same-shaped string-to-string field
    /// remap) -- not reimplemented in terms of this one.
    RewriteTreeNodes {
        tree: TermIdx,
        type_filter: Option<TermIdx>,
        field: TermIdx,
        value_map: TermIdx,
    },

    /// Collect every distinct `{"type":"Attr","key":<str>}` node's `key`
    /// value reachable inside `tree` (recursing into every Dict node's
    /// children AND Tuple items -- the SAME walk `RewriteTreeNodes`
    /// performs), tally occurrence COUNTS per distinct key, and return
    /// them as a RANKED `Value::Tuple` of `(key: Surface(Text), count:
    /// Int)` pairs, sorted by `(-count, key)` -- IDENTICAL to
    /// `domains/edit_ops.py`'s `find_attr_keys`, the Python oracle
    /// `_compose_structural_variant`'s `swap_term_leaf` branch uses to
    /// pick its SITE (the two most-referenced Attr keys in a rule's
    /// effects tree).
    ///
    /// Deliberately returns a `Value::Tuple` (an ordered sequence, the
    /// same shape `ListDrop`/`IndexAt` already operate on), NOT a
    /// `Value::Dict` -- a Dict's pairs are canonically re-sorted BY KEY
    /// (`cmp_value`, see `MkDict`'s own construction), which would
    /// destroy the frequency ranking. A caller reads the #1 (most-
    /// referenced) key via `IndexAt(IndexAt(ranking, 0), 0)` and the #2
    /// via `IndexAt(IndexAt(ranking, 1), 0)`, then builds `{#1: #2}` via
    /// `MkDict` for `RewriteTreeNodes`'s own `value_map` argument
    /// (`type_filter=Lit("Attr")`, `field=Lit("key")`) -- the SITE-
    /// COMPUTATION half `RewriteTreeNodes` alone can't provide (it only
    /// REWRITES matching nodes in place; it has no way to accumulate a
    /// frequency table across a tree walk). This is the one missing
    /// primitive `apply_swap_term_leaf`'s composition needed to go fully
    /// graph-native -- see `seeds/composer_experiment_graph.json`'s
    /// `compose_experiment_structure_graph` swap branch.
    AttrKeyRanking {
        tree: TermIdx,
    },

    /// Observe the abstract structural SHAPE of `text` (a Str or
    /// Surface(Text)). Returns a `Value::Dict` whose keys are
    /// classification labels and whose values are scalar shape
    /// features:
    ///
    /// - `delimiters`: Str — `"braces"` / `"brackets"` / `"angles"`
    ///   / `"indent"` / `"flat"` / `"unbalanced"`
    /// - `kind`: Str — `"mapping"` / `"sequence"` / `"atomic"`
    ///   / `"nested"`
    /// - `nesting_depth`: Int — max balanced-delimiter depth
    /// - `kv_pair_count`: Int — estimated top-level key-value pairs
    /// - `seq_item_count`: Int — estimated top-level sequence items
    /// - `has_quotes`: Bool
    /// - `balanced`: Bool — all delimiter pairs balance
    /// - `whitespace_kind`: Str — `"compact"` / `"multiline"`
    ///
    /// Implementation: a single stack-tracking walk of the bytes.
    /// NOT a parser — a structural fingerprint that lets the
    /// substrate cluster "similar shapes" across surface formats
    /// (JSON / YAML / TOML / XML / etc.) for cumulative learning.
    TextShape {
        text: TermIdx,
    },

    /// `FbFrameSeq` — the READ-ONLY half of the shared-memory
    /// framebuffer vision primitive (`framebuffer.rs` /
    /// `Substrate::fb_sample`) made graph-composable. `fb` evaluates
    /// to the `Int` `fb_id` a prior `fb_attach` call returned; this
    /// Term returns the framebuffer's CURRENT `frame_seq` as an `Int`
    /// (a cheap mmap-header read, no pixel copy, no segmentation) —
    /// or `Value::None` if `fb` isn't attached, or if the evaluator's
    /// `EvalCtx` wasn't given a `framebuffers` reference at all.
    ///
    /// Composable in a `where`-clause: a rule can compare this
    /// against a `last_seq` attr it stamped on its own "I looked at
    /// frame N" witness node to ask "has anything changed since I
    /// last looked" without touching the graph — the actual sampling
    /// + segmentation (which DOES mutate the graph: mints/updates
    /// Cell and Region nodes) stays behind `Substrate::fb_sample`
    /// (PyO3: `Substrate.fb_sample(fb_id, game, grid_w, grid_h)`).
    ///
    /// HONEST SCOPE NOTE: `EvalCtx::framebuffers` defaults to `None`
    /// in `EvalCtx::new`, exactly like `derivations`/`shape_cache`,
    /// and NO existing call site currently opts in — the where-clause
    /// evaluation path (`rewrite::extend_each` → `EvalCtx::new` at
    /// rewrite.rs:628) does not thread a `&Substrate.framebuffers`
    /// reference through, because doing so requires adding a new
    /// parameter to `match_rule` / `match_rule_each` /
    /// `match_rule_each_with_initial` / `extend_each` (rewrite.rs) —
    /// a widely-shared matcher pipeline called from many sites across
    /// rewrite.rs/substrate.rs/graph_rules.rs — which was judged too
    /// invasive to land safely alongside this primitive (see the
    /// PyO3 handoff task's write-up). Until that plumbing lands, a
    /// Rule's `where`-clause containing `FbFrameSeq` evaluates to
    /// `Value::None` when fired through the normal rule engine. The
    /// Term IS real and testable today via a direct `evaluate()` call
    /// with an `EvalCtx` built with `.with_framebuffers(...)` —
    /// that's the wired, working surface.
    FbFrameSeq {
        fb: TermIdx,
    },

    /// `ChangeDetect` — the spatial face of vision's change-detect
    /// primitive: a dense image cross-correlated with a kernel
    /// (contrast / center-surround / DoG / oriented-edge response
    /// depending on which kernel the agent has kept). PURE: takes
    /// resolved Value lists, NOT graph nodes — the seed rules compose
    /// it with `Attr` (`ChangeDetect(Attr(img,"vals"), Attr(k,"weights"),
    /// Tuple(h,w,kh,kw,stride))`). `image_vals` evaluates to the flat
    /// row-major image buffer, `kernel_weights` to the flat kernel,
    /// `dims` to a Tuple `[h, w, kh, kw, stride]` (all integers). On a
    /// shape mismatch (length != h*w, kernel != kh*kw, kernel larger
    /// than image, zero stride) returns `Value::None`. Returns a
    /// `Value::Tuple` of `f64` response — `((h-kh)/stride+1) ×
    /// ((w-kw)/stride+1)`, row-major, valid (non-padded)
    /// cross-correlation (no kernel flip — matches
    /// `scipy.signal.correlate2d(mode='valid')`).
    ChangeDetect {
        image_vals: TermIdx,
        kernel_weights: TermIdx,
        dims: TermIdx,
    },

    /// `TemporalDiff` — the temporal face of change-detect: an
    /// elementwise event/motion stream between two same-shaped
    /// observations (`a_vals` = prior frame, `b_vals` = current frame).
    /// `b[i] - a[i]` per element — "process deltas before pixels"
    /// (event-camera / DVS precedent). PURE: takes resolved Value
    /// lists, NOT graph nodes. On a length mismatch returns
    /// `Value::None`. Returns a `Value::Tuple` of `f64` (same length
    /// as the inputs).
    TemporalDiff {
        a_vals: TermIdx,
        b_vals: TermIdx,
    },

    /// `Foveate` — foveated (non-uniform) sampling: cortical
    /// magnification as data. `image_vals` = flat row-major image,
    /// `dims` = Tuple `[h, w]`, `geometry` = Tuple `[fovea_radius_frac,
    /// periphery_stride]` (fovea = high-res full-rate central disc,
    /// periphery = strided). PURE: takes resolved Value lists, NOT
    /// graph nodes. Returns a `Value::Tuple` of `[out_vals...,
    /// out_h_f, out_w_f]` (the sampled grid flattened row-major,
    /// followed by the output height and width as floats). On a shape
    /// mismatch returns `Value::None`.
    Foveate {
        image_vals: TermIdx,
        dims: TermIdx,
        geometry: TermIdx,
    },

    /// Return the ELEMENT of `source` for which `value` (evaluated
    /// under `var_name: element`) is maximum. Symmetric pair with
    /// `Argmin`. Differs from `MaxOver` (which returns the max value
    /// itself). Tiebreaker: first encountered in iteration order
    /// over `source`. When `source` is empty, returns `default` if
    /// given, else `Value::None`. Added in Phase 17b.3c.4 — the
    /// missing primitive for "pick the top-salience event" without
    /// the recompute-after-max workaround.
    Argmax {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
        default: Option<TermIdx>,
    },
    Argmin {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
        default: Option<TermIdx>,
    },

    /// Generic fold combinator — the kernel iteration primitive. Iterate
    /// `source`, binding each element to `var_name` and the running
    /// accumulator to `acc_name`, evaluating `body` to produce the next
    /// accumulator. Empty source → `init`. This is the linchpin enabling
    /// graph-resident definitions for Count / Sum / Prod / MinOver /
    /// MaxOver / Argmax / Argmin / BitsAtAll / BitsWriteAll / Dot / Join
    /// / LEB128 / Lines / Bytes / Difference / etc. Added in the
    /// "shrink-to-kernel" arc (KERNEL_AUDIT.md).
    Fold {
        source: TermIdx,
        var_name: Sym,
        acc_name: Sym,
        init: TermIdx,
        body: TermIdx,
    },

    // --- universal codec primitives (Phase 16b/16c) ---
    //
    // The orthogonal building blocks every entropy-coded format needs.
    // BitsAt/BitsWrite are CORE (every binary format needs them);
    // HuffmanDecodeStream/HuffmanEncodeStream are the `huffman` optional
    // feature block (ISA §3.3) — software fallback uses these primitives
    // over graph-resident HuffmanTable nodes; hardware-accelerated runners
    // can dispatch to codec silicon.
    //
    // All consume graph-resident data — HuffmanTable nodes, buffer
    // Surface(Bytes) Values. Composing these with the agent's per-codec
    // structure (Mp3Granule, H264Slice, JpegBlock, etc.) gives MP3
    // requantize, H.264 QP-bump, JPEG transcoding, Vorbis bitrate
    // change — all as graph data + Rules, not bespoke codec engineering.
    /// Read `n_bits` MSB-first from a Surface(Bytes) buffer starting at
    /// `bitpos`. Returns Int. `buffer` must evaluate to a Surface(Bytes);
    /// other types → None. `bitpos + n_bits` past end → None.
    BitsAt {
        buffer: TermIdx,
        bitpos: TermIdx,
        n_bits: TermIdx,
    },

    /// Write the low `n_bits` of `value` MSB-first into a fresh copy of
    /// `buffer` starting at `bitpos`. Returns Surface(Bytes) with the
    /// new bytes. If write extends past `buffer`'s end, the buffer is
    /// extended with zero-filled bytes. Out-of-range types → None.
    BitsWrite {
        buffer: TermIdx,
        bitpos: TermIdx,
        value: TermIdx,
        n_bits: TermIdx,
    },

    /// Vectorised BitsWrite — apply many bit-field writes to a single
    /// buffer in ONE copy. `writes` evaluates to a `Tuple` of `Tuple
    /// (bitpos_int, value_int, nbits_int)` triples. Returns the
    /// rewritten `Surface(Bytes)`. This is the form Rules naturally
    /// produce when walking a graph subtree (collect all writes, then
    /// apply); the per-call version is for ad-hoc edits.
    BitsWriteAll {
        buffer: TermIdx,
        writes: TermIdx,
    },

    /// Vectorised BitsAt — read many bit-fields from `buffer` in ONE
    /// call. `reads` evaluates to a `Tuple` of `Tuple(bitpos, nbits)`
    /// pairs. Returns a `Tuple<Int, ...>` of the same arity. Avoids
    /// per-field Python↔runner round-trips for bulk parses (codec
    /// tables, multi-field walks).
    BitsAtAll {
        buffer: TermIdx,
        reads: TermIdx,
    },

    /// Universal Huffman pair decoder. Reads `n_pairs` value pairs from
    /// `buffer` starting at `bitpos`, using the graph-resident
    /// HuffmanTable node `table` resolves to. Returns
    /// `Tuple<Tuple<Int, Int>, ...>` then `Int new_bitpos` wrapped as
    /// `Tuple(pairs_tuple, new_bitpos)`. The agent unpacks via Nth.
    /// Consumes HuffmanTable nodes minted by `seed_mp3_huffman_tables`
    /// (or any future codec's table-seed helper).
    HuffmanDecodeStream {
        buffer: TermIdx,
        bitpos: TermIdx,
        table: TermIdx,
        n_pairs: TermIdx,
    },

    /// Mirror of HuffmanDecodeStream. Writes a tuple of (x, y) pairs
    /// into a fresh buffer copy starting at `bitpos`, encoding each
    /// pair via the named HuffmanTable. Returns
    /// `Tuple(new_buffer, new_bitpos)`.
    HuffmanEncodeStream {
        buffer: TermIdx,
        bitpos: TermIdx,
        pairs: TermIdx,
        table: TermIdx,
    },

    /// Exp-Golomb decode (unsigned, ue(v) per ITU-T H.264 §9.1).
    /// Count leading zeros M; read 1-bit marker; read M more bits as
    /// suffix; return `2^M - 1 + suffix`. Universal variable-length
    /// integer used in H.264 / HEVC / VVC slice headers, macroblock
    /// types, SPS / PPS fields. Same primitive serves all of them.
    /// Returns `Tuple(value, new_bitpos)`.
    ExpGolombDecode {
        buffer: TermIdx,
        bitpos: TermIdx,
    },

    /// Exp-Golomb signed decode (se(v) per ITU-T H.264 §9.1.1).
    /// Reads ue(v) `k`, maps to signed: k=0 → 0, k=1 → 1, k=2 → -1,
    /// k=3 → 2, k=4 → -2, ... (k odd → +ceil(k/2); k even → -k/2).
    /// Returns `Tuple(value, new_bitpos)`.
    ExpGolombDecodeSigned {
        buffer: TermIdx,
        bitpos: TermIdx,
    },

    /// Exp-Golomb encode (mirror of ExpGolombDecode). Writes `value`
    /// as ue(v) into a fresh buffer copy at `bitpos`. Returns
    /// `Tuple(new_buffer, new_bitpos)`.
    ExpGolombEncode {
        buffer: TermIdx,
        bitpos: TermIdx,
        value: TermIdx,
    },

    /// Exp-Golomb signed encode. Maps signed integer to unsigned per
    /// the inverse of se(v), then writes via ue(v).
    ExpGolombEncodeSigned {
        buffer: TermIdx,
        bitpos: TermIdx,
        value: TermIdx,
    },

    // --- recursion / concept lookup ---
    Holds {
        concept: Sym,
        node: Option<TermIdx>,
        node2: Option<TermIdx>,
    },

    // --- graph-resident Term reflection (Paper Axiom 3) ---
    /// `node` evaluates to a NodeID; the runner walks that node as a
    /// Term subgraph root (per src/reflect.rs `term_from_subgraph`),
    /// re-arenas it, and evaluates the resulting Term under the
    /// CURRENT env. Lets graph-resident Terms reference other
    /// graph-resident Terms by NodeID — the substrate's "evaluate
    /// what this attr/edge points to" primitive. Phase 17b uses it
    /// to migrate the emotion EMA loop out of Python: a Rule's
    /// effect can EvalSubgraph(Pick(Neighbours(emo, "sample_term")))
    /// to evaluate whatever per-Emotion sample Term the agent has
    /// installed.
    EvalSubgraph {
        node: TermIdx,
    },

    // --- boolean ---
    And {
        items: Vec<TermIdx>,
    },
    Or {
        items: Vec<TermIdx>,
    },
    Not {
        arg: TermIdx,
    },

    // --- arithmetic / scalar math ---
    Abs {
        arg: TermIdx,
    },
    Neg {
        arg: TermIdx,
    },
    Plus {
        items: Vec<TermIdx>,
    },
    Minus {
        a: TermIdx,
        b: TermIdx,
    },
    Times {
        items: Vec<TermIdx>,
    },
    Div {
        a: TermIdx,
        b: TermIdx,
    },
    Mod {
        a: TermIdx,
        b: TermIdx,
    },
    Pow {
        a: TermIdx,
        b: TermIdx,
    },
    Sqrt {
        arg: TermIdx,
    },
    /// Natural logarithm of a scalar. `ln(x)` for x>0; for x<=0 returns
    /// `f64::NEG_INFINITY` (callers add their own epsilon guard on the world
    /// value, mirroring `Sqrt`'s 0.0-for-nonpositive convention). The
    /// transcendental the VTL-invariant (`log(F) - mean(log(F))`) rests on —
    /// not algebraically derivable from the existing arithmetic Terms.
    Log {
        arg: TermIdx,
    },
    /// Natural exponential of a scalar — the inverse of `Log`.
    Exp {
        arg: TermIdx,
    },
    Min {
        items: Vec<TermIdx>,
    },
    Max {
        items: Vec<TermIdx>,
    },
    ArgMax {
        items: Vec<TermIdx>,
    },
    /// Banded dynamic-time-warping distance between two feature
    /// trajectories. `a` and `b` each evaluate to a Tuple of frames,
    /// each frame a Tuple of band floats (frames x bands). Returns the
    /// length-normalised banded-DTW distance as a Float — the
    /// genuinely new primitive analysis-by-synthesis recognition needs:
    /// synthesis+compare is not expressible from the existing Terms, so
    /// the agent extends the runtime (per runtime_design). Mirrors the
    /// Python `dtw` the bottom-up baseline already uses (Sakoe-Chiba
    /// band, Euclidean per-frame). The AxS DECISION (argmax over
    /// candidate words of -DtwTo(...)) is composed in the graph; only
    /// this distance kernel is the Rust primitive.
    DtwTo {
        a: TermIdx,
        b: TermIdx,
    },

    /// EnigmaCrib — exact hard admissibility check for a graph-resident
    /// Enigma candidate. The candidate node carries the machine settings,
    /// ciphertext, crib, and offset as ordinary graph attributes; this
    /// kernel only answers whether the crib is consistent. Language scoring
    /// and candidate ranking remain graph composition above this predicate.
    EnigmaCrib {
        candidate: TermIdx,
    },

    /// EnigmaBombe — plugboard-independent hard admissibility. It asks
    /// whether any involutive steckering can satisfy the crib for the
    /// candidate rotor hypothesis, thereby rejecting whole rotor/start
    /// classes without enumerating plugboards.
    EnigmaBombe {
        candidate: TermIdx,
    },
    /// EnigmaBombeWitness — returns one crib-forced partial plugboard as
    /// text, for the mechanical completion stage after the hard filter.
    EnigmaBombeWitness {
        candidate: TermIdx,
    },

    /// ApcEncode — the CONTEXT-PREDICTIVE FRONT-END encode (see `apc.rs`).
    /// Runs the learned autoregressive-predictive-coding context RNN(s)
    /// (`model`, a flat weight tuple from `apc::train`) over the full
    /// utterance frame sequence (`seq`, a Tuple of [din] frames), then
    /// slices frames `[start,end)` and resamples to `out_len` frames.
    /// Returns the context-state trajectory (Tuple of [dh] or [2*dh]
    /// frames) — a word's speaker-robust, context-aware representation
    /// ready for `DtwTo`. `start`/`end` < 0 mean "whole sequence" (the
    /// front-end-only ablation encodes a word span in isolation; the
    /// full-context path encodes the whole utterance then slices). The
    /// TRAINING primitive is `apc::train` (a batch numeric loop invoked
    /// one-line from the world adapter); only this ENCODE is a Term.
    ApcEncode {
        model: TermIdx,
        seq: TermIdx,
        start: TermIdx,
        end: TermIdx,
        out_len: TermIdx,
    },

    /// PointSetDist — ORDER-INVARIANT shape distance: the symmetric Modified
    /// Hausdorff Distance (Dubuisson-Jain) between two point SETS (each a Tuple
    /// of [x,y] frames, like DtwTo's input). max over the two directed means of
    /// nearest-neighbour distance — max( mean_a min_b |a-b| , mean_b min_a |a-b| ).
    /// Unlike DtwTo it ignores pen ORDER, so it absorbs stroke-order / stroke-count
    /// variability across writers (the named Omniglot residual). The recognition
    /// DECISION (argmax over candidates of -PointSetDist) is composed in the graph;
    /// only this distance kernel is the Rust primitive. Binary {a,b}-shaped like DtwTo.
    PointSetDist {
        a: TermIdx,
        b: TermIdx,
    },

    /// MahalLeaf — the GENERATIVE LEAF of the recursive operator (BPL's per-primitive token model AS the
    /// base case, not an added cue). `a` = an observed leaf's points (flattened); `b` = the candidate
    /// leaf's learned PRIMITIVE MODEL, [mean (len = a) ++ inv_std (len = a)] of its nearest background
    /// primitive. Returns the diagonal MAHALANOBIS cost sum_i ( inv_std_i * (a_i - mean_i) )^2 — the neg
    /// log-likelihood of the leaf under the primitive's diagonal Gaussian; the primitive's natural
    /// deformation directions cost little. Structure-preserving (a leaf stays a leaf; only its metric is
    /// learned + generative). Replaces PointSetDist at the bottom of the recursive descent.
    MahalLeaf {
        a: TermIdx,
        b: TermIdx,
    },

    /// MahalFull — the FULL-COVARIANCE generative leaf (the BPL token model's covariance). `a` = an observed
    /// leaf's points (flattened, len d); `b` = a candidate leaf's model [mean (d) ++ precision (d*d, row-major)]
    /// — its nearest primitive's mean + full inverse-covariance. Returns the RMS Mahalanobis
    /// sqrt( (a-mean)^T P (a-mean) / d ): unlike MahalLeaf (diagonal), it scores CORRELATED deformation modes
    /// (points that move together) cheaply. The strengthened generative leaf the agent's residual called for.
    MahalFull {
        a: TermIdx,
        b: TermIdx,
    },
    DeformGenMarginal {
        a: TermIdx,
        b: TermIdx,
    },
    DeformGen {
        a: TermIdx,
        b: TermIdx,
    },

    /// DeformDist — the BPL TOKEN-MODEL match: fit the candidate's written form to the observed
    /// mark with a small AFFINE deformation (affine-ICP) and score the order-invariant residual
    /// (symmetric Modified Hausdorff) PLUS a penalty on how non-rigid the fit had to be. The
    /// generative richness over PointSetDist: deformations are ALLOWED but COST, so the true class
    /// (near-rigid, low residual) beats a wrong class (large penalised deformation, poor fit). The
    /// affine + ICP + the anisotropy penalty are the Rust primitive; the recognition DECISION
    /// (argmax over candidates of -DeformDist) is composed in the graph. Binary {a,b} like DtwTo.
    DeformDist {
        a: TermIdx,
        b: TermIdx,
    },

    /// SmoothDeformDist — the "distortable canvas" (Learning from One and Only One Shot, 2022):
    /// a SMOOTH NON-RIGID deformation FIELD (free-form deformation on a multi-level control grid,
    /// ridge-regularised) warping the candidate onto the mark, with the DISTORTION COST as the
    /// metric (residual-after-warp + the smooth field's magnitude). Replaces DeformDist's global
    /// affine: a local smooth warp the true class needs little of and a wrong class pays for. Same
    /// {a,b} shape; the smooth-field optimisation is the Rust primitive, the decision is the graph.
    SmoothDeformDist {
        a: TermIdx,
        b: TermIdx,
    },

    /// TpsDeformDist — the PRINCIPLED smooth warp (thin-plate spline, Bookstein 1989 / Shape Contexts
    /// 2002): fit a regularised TPS to ICP correspondences and return residual + BENDING ENERGY
    /// (w^T K w, the non-affine distortion). The affine part (rotation/scale/shear) is FREE — only
    /// genuine bending costs. Replaces SmoothDeformDist's heuristic FFD + magnitude cost with the
    /// closed-form spline whose bending energy IS the distortion metric. Same {a,b} shape.
    TpsDeformDist {
        a: TermIdx,
        b: TermIdx,
    },

    /// SmoothDeformComponents — RUN 44 PHASE 2 (`deform_metric.rs`): decomposes
    /// `SmoothDeformDist`'s own free-form-deformation field into an AFFINE part
    /// (rotation/shear/log-scale/translation, closed-form least-squares fit) and the NON-AFFINE
    /// residual ("bending"), additively alongside the byte-identical fused scalar (`total`).
    /// Returns a `Dict` (`total`/`residual`/`dc`/`bending`/`rotation`/`shear`/`log_scale`/
    /// `tx`/`ty`/`n`) — a caller reads one field via a held `DictGet`, never a Python decision.
    /// Same {a,b} shape as `SmoothDeformDist`/`TpsDeformDist`; `smooth_deform_dist` itself is
    /// UNCHANGED (this Term duplicates its fitting loop in its own module for working-tree
    /// isolation, see `deform_metric.rs`'s module doc).
    SmoothDeformComponents {
        a: TermIdx,
        b: TermIdx,
    },

    /// ShapeContextDist — the SHAPE CONTEXT descriptor + match (Belongie-Malik-Puzicha 2002): each
    /// point carries a LOG-POLAR histogram of the OTHER points' relative positions (a globally
    /// discriminative descriptor); the distance is the symmetric mean nearest chi-squared cost
    /// between the two shapes' point descriptors. Far richer than a holistic occupancy histogram.
    /// Same {a,b} shape; the descriptor + chi-squared match is the Rust primitive.
    ShapeContextDist {
        a: TermIdx,
        b: TermIdx,
    },

    /// EnclosedCount — the INK TOPOLOGY primitive (`ink_topology.rs`): given a list of strokes
    /// (each a list of `[x, y]` pen samples), rasterize the polylines, flood the background from
    /// the raster border, and count the remaining background components — the figure's ENCLOSED
    /// REGIONS ("counters"). The ventral grounding names enclosure as the consequence of the
    /// proto-object stage and claims topology is among the most writer-INVARIANT features there
    /// is. Returns a `Dict` (`holes`/`grid_w`/`grid_h`/`cell`/`n_samples`/`clamped`) — a caller
    /// reads one field via a held `DictGet`, never a Python decision. The raster resolution is
    /// NOT a parameter: it is the ink's OWN mean inter-sample arc step (§13 — see the module doc).
    EnclosedCount {
        arg: TermIdx,
    },

    /// ScTpsDist — the FULL Shape-Contexts distance: shape-context descriptor CORRESPONDENCES (chi-
    /// squared matching) feeding a thin-plate-spline fit, distance = SC matching cost + bending
    /// energy. The descriptor supplies the good correspondences the bare TpsDeformDist (nearest-
    /// neighbour) lacked. Same {a,b} shape; the SC+TPS pipeline is the Rust primitive.
    ScTpsDist {
        a: TermIdx,
        b: TermIdx,
    },

    /// BlendCover — the jabberwock's PORTMANTEAU kernel (it authored this).
    /// Three string children (unknown, a, b): returns in [0,1] how well the two
    /// known words `a` (head) and `b` (tail) FUSE with an OVERLAPPING seam to
    /// cover `unknown` — coverage minus seam-distortion, char shapes as a
    /// phoneme proxy. The two-word search / accept-by-margin DECISION is composed
    /// in the graph; only this fused-cover score is the Rust primitive (cf. DtwTo).
    BlendCover {
        unknown: TermIdx,
        a: TermIdx,
        b: TermIdx,
    },

    /// Whiten — within-class WHITENING (the agent's matrix-primitive frozen edge,
    /// seeded then specified): a = within-class scatter matrix W (Tuple of Tuple of
    /// Float), b = vector x (Tuple of Float). Returns L^-1 x where W = L L^T
    /// (Cholesky), so distances become the Mahalanobis metric that suppresses the
    /// within-class (speaker) scatter directions. The matrix factorisation + solve
    /// the DSL cannot express. Binary {a,b}-shaped like DtwTo.
    Whiten {
        a: TermIdx,
        b: TermIdx,
    },

    /// WhitenMany — batch Whiten (the agent's perf realisation): a = W, b = data matrix
    /// X. Factors W = L L^T ONCE then forward-solves L y = x for every row, so the
    /// Cholesky is shared across rows (O(n^3 + m·n^2) not O(m·n^3)). Same math as
    /// Whiten, amortised. Binary {a,b}-shaped like Whiten.
    WhitenMany {
        a: TermIdx,
        b: TermIdx,
    },

    /// WithinScatter — the regularized within-class scatter matrix (the agent's
    /// covariance primitive, seeded then specified): a = data (Tuple of token vectors),
    /// b = class labels (Tuple of Float). Returns W = avg over classes of
    /// (x-μ_c)(x-μ_c)ᵀ, diagonal-shrunk — the matrix Whiten whitens by, making the
    /// cross-speaker pipeline fully native. Grouped mean-subtraction + outer-product
    /// accumulation the DSL cannot express. Binary {a,b}-shaped like DtwTo.
    WithinScatter {
        a: TermIdx,
        b: TermIdx,
    },

    /// BetweenScatter — the between-class scatter Sb = (1/N) Σ_c n_c (μ_c-μ)(μ_c-μ)ᵀ
    /// (the agent's between-scatter primitive, seeded then specified): a = data (Tuple
    /// of token vectors), b = group labels. The between-OBSERVED-group (e.g. speaker)
    /// scatter the nuisance-conditioned fix whitens by — one native op instead of
    /// St-Sw in numpy. Binary {a,b}-shaped like WithinScatter.
    BetweenScatter {
        a: TermIdx,
        b: TermIdx,
    },

    /// XCorrPeak — the SNR-optimal MATCHED FILTER: peak normalised
    /// cross-correlation over a LAG SEARCH between two frames x bands
    /// trajectories. The agent's sonar transfer ('correlating a known
    /// delayed signal') as the analysis-by-synthesis recognition score —
    /// max_L Dot(a, shift(b, L)) / (|a| |b|), a scalar in [-1, 1]. Shaped
    /// exactly like DtwTo (two children -> one scalar); differs only in
    /// the kernel (peak-NCC SIMILARITY over lags, not banded-DTW DISTANCE).
    /// Authored via runtime_design (agent_specify_matched_filter +
    /// emit_primitive_rust, semantic_kind=trajectory_correlation_peak).
    XCorrPeak {
        a: TermIdx,
        b: TermIdx,
    },

    // --- bitwise / integer ---
    //
    // Bitwise primitives on i64. `And`/`Or`/`Not` (above) are BOOLEAN
    // — they evaluate truthiness; these are the bit-level integer
    // operations LLVM IR's `and`/`or`/`xor`/`shl`/`lshr`/`ashr`
    // demand. Shifts clamp out-of-range shift amounts to zero (LLVM
    // would call that poison, but the substrate's convention for
    // arithmetic edge cases is silent-zero — see Div/Mod).
    /// Bitwise AND. `BitAnd(a, b) := a & b`.
    BitAnd {
        a: TermIdx,
        b: TermIdx,
    },
    /// Bitwise OR. `BitOr(a, b) := a | b`.
    BitOr {
        a: TermIdx,
        b: TermIdx,
    },
    /// Bitwise XOR. `BitXor(a, b) := a ^ b`.
    BitXor {
        a: TermIdx,
        b: TermIdx,
    },
    /// Shift-left. `Shl(a, b) := a << b` (i64 wrapping). b ∉ [0,63] → 0.
    Shl {
        a: TermIdx,
        b: TermIdx,
    },
    /// Logical shift-right (unsigned). Fills with zeros.
    /// b ∉ [0,63] → 0.
    Lshr {
        a: TermIdx,
        b: TermIdx,
    },
    /// Arithmetic shift-right (signed). Fills with the sign bit.
    /// b ∉ [0,63] → 0 if a ≥ 0, else -1.
    Ashr {
        a: TermIdx,
        b: TermIdx,
    },

    /// Integer truncating division (signed). `IDiv(a, b) := a / b` with
    /// truncation toward zero — matches Rust's `i64::wrapping_div`
    /// (which matches C's `/` and LLVM's `sdiv`). Division by zero
    /// returns 0 (the substrate's silent-zero convention).
    IDiv {
        a: TermIdx,
        b: TermIdx,
    },
    /// Integer remainder (signed). `IRem(a, b) := a % b` matching
    /// Rust's `i64::wrapping_rem` and LLVM's `srem`. Remainder of
    /// zero divisor returns 0.
    IRem {
        a: TermIdx,
        b: TermIdx,
    },

    // --- control ---
    IfThenElse {
        cond: TermIdx,
        then: TermIdx,
        other: TermIdx,
    },

    // --- geometry / N-D vectors ---
    Vec_ {
        items: Vec<TermIdx>,
    },
    VecAdd {
        a: TermIdx,
        b: TermIdx,
    },
    VecSub {
        a: TermIdx,
        b: TermIdx,
    },
    Dot {
        a: TermIdx,
        b: TermIdx,
    },
    Magnitude {
        arg: TermIdx,
    },

    // --- rotation / angle ---
    Sin {
        arg: TermIdx,
    },
    Cos {
        arg: TermIdx,
    },
    Atan2 {
        y: TermIdx,
        x: TermIdx,
    },
    Bearing {
        arg: TermIdx,
    },
    Rotate {
        vec: TermIdx,
        angle: TermIdx,
    },
    AngleBetween {
        a: TermIdx,
        b: TermIdx,
    },

    // --- set algebra (Phase 7 ext) ---
    /// Union of two set-valued Terms — the merge of the two element
    /// sets, deduped. Closes the gap left by the Python DSL needing
    /// Filter+Exists to express union.
    Union {
        a: TermIdx,
        b: TermIdx,
    },
    /// Last element of an ordered sequence (None if empty). Added via Layer B —
    /// the last-element access an accumulator-dependent loop (collapse_runs) needs.
    Last {
        seq: TermIdx,
    },
    /// Element of `seq` at a DYNAMIC (Term-computed) index, Python-style negative
    /// indexing from the end; None if out of range. Added via Layer B — the
    /// dynamic / from-end indexing `Nth`'s static `as usize` index can't do.
    IndexAt {
        seq: TermIdx,
        index: TermIdx,
    },
    /// `seq` with `item` appended — ordered concat returning a Tuple. Added via
    /// Layer B — the ordered append an accumulator-building fold needs.
    Append {
        seq: TermIdx,
        item: TermIdx,
    },
    /// `list` with the element at `index` removed, returning a NEW Tuple
    /// (order preserved). Python-style negative indexing from the end
    /// (same convention as `IndexAt`). An `index` that is out of range
    /// AFTER that adjustment is a no-op — `list`'s elements come back
    /// unchanged, in order (the caller decides whether an out-of-range
    /// drop is "inert" for its purposes; this Term only performs the
    /// mechanical removal). The index-based twin of `FilterList`
    /// (content-predicate removal) — nothing in the dialect could drop a
    /// list element by POSITION (`FilterList`'s predicate only sees the
    /// element itself, never its index). Added for
    /// `domains/edit_ops.py::apply_drop_match_edge` (drop
    /// `rule["match"][index]`) — a genuine gap, not a narrowing of an
    /// existing Term.
    ListDrop {
        list: TermIdx,
        index: TermIdx,
    },
    /// Intersection — elements present in both.
    Intersect {
        a: TermIdx,
        b: TermIdx,
    },
    /// Difference — elements in `a` but not in `b`.
    Difference {
        a: TermIdx,
        b: TermIdx,
    },
    /// Map a set element-wise to another set under `var_name`.
    /// Sum-shaped over the resulting Values — except the reduction is
    /// "collect into a frozenset" rather than "+=", so duplicate
    /// outputs collapse.
    MapSet {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
    },
    /// Ordered (list) twin of MapSet — preserves source order + duplicates,
    /// returns a **`Value::List`** (ARC6 value layer; see `FilterList`).
    /// The faithful target for a Python LIST comprehension's transform
    /// (MapSet returns a set). Added via the Layer-B self-extension loop.
    MapList {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
    },

    // --- edge-attr DSL access (Phase 7 ext) ---
    /// Set of outgoing edge "handles" from `node`. The handle is a
    /// tuple `(src_nid, edge_type_str, tgt_nid)` — matches the
    /// canonical Python representation of an EdgeKey and lets
    /// downstream Terms (`EdgeAttr`, `Nth`, `Filter`) pick it apart.
    Edges {
        node: TermIdx,
        edge_type: Sym,
        any_type: bool,
    },
    /// Read an attr from a specific edge. `edge` evaluates to a triple
    /// `(src, edge_type, tgt)` (as Tuple Value); `key` is the attr name.
    EdgeAttr {
        edge: TermIdx,
        key: Sym,
    },

    /// Indexed attr lookup (Phase 7b). Returns the frozenset of nodes
    /// typed `node_type` whose `attr_key` attribute equals the value
    /// of `value`. Resolves in O(1+result) if the index has been
    /// declared via `Substrate::declare_attr_index`; otherwise the
    /// engine falls back to a linear scan (so the Term is always
    /// correct — declaring an index just makes it faster).
    NodesWhere {
        node_type: Sym,
        attr_key: Sym,
        value: TermIdx,
    },

    /// All nodes of a given type, as a frozenset — the unfiltered
    /// enumeration source for graph-wide aggregates (`Count`/`Filter`/
    /// `MapSet` over every node of a type). `NodesWhere` is the
    /// equality-filtered special case; this is the whole population.
    NodesOfType {
        node_type: Sym,
    },

    /// Least-general generalization (anti-unification) over a collection
    /// of structured Values — the implied-rule induction operator. Where
    /// the instances AGREE the result fixes the value; where they DIFFER
    /// it abstracts to `WILD` (the sentinel `("·?·",)`). Recurses through
    /// nested Dicts (over shared keys), Tuples (element-wise, equal len),
    /// and Sets/FrozenSets (the intersection — members always present).
    /// `wild` is the interned `"·?·"` marker, set at construction so the
    /// read-only evaluator can build the sentinel without interning.
    AntiUnify {
        values: TermIdx,
        wild: Sym,
    },

    /// The MDL specificity of an induced pattern — how many leaf positions
    /// it FIXES (the twin of `domains/implied_rule.py::_fixed_count`). WILD
    /// → 0; Dict/Tuple → sum of children; Set/FrozenSet → cardinality; a
    /// scalar leaf → 1. The rank by which competing implied rules compete
    /// (a more-fixed rule is a stronger, more-compressive claim) and the
    /// quantity the keep-gate (`fixed ≥ min_fixed`) thresholds on. `wild`
    /// is the interned `"·?·"` marker, as in `AntiUnify`.
    FixedCount {
        pattern: TermIdx,
        wild: Sym,
    },

    /// Does an induced pattern COVER an instance? — the rule-application
    /// test, dual of `AntiUnify` (twin of `implied_rule.py::covers`). WILD
    /// matches anything; a Dict pattern requires its keys present and each
    /// recursively covered (instance may carry more); a Tuple requires same
    /// length, element-wise covered; a Set/FrozenSet requires the pattern be
    /// a SUBSET of the instance; a scalar requires equality. This is how the
    /// agent decides a held `ImpliedRule` APPLIES to a fresh scenario (and,
    /// for a win-rule, whether the condition the score follows now holds).
    Covers {
        pattern: TermIdx,
        instance: TermIdx,
        wild: Sym,
    },

    /// `Covers` with the OUTER container read as a relation SET — the pattern's
    /// relations must ALL be covered by DISTINCT relations of the instance, and
    /// the instance may carry extra relations the pattern says nothing about.
    /// Element comparison is `covers_value` UNCHANGED, so a relation stays
    /// positional (`["buyer", WILD]` does not match `["alice", "buyer"]`) and
    /// WILD still matches anything.
    ///
    /// This is the subsumption question — *does this held generalisation APPLY
    /// to this item* — as distinct from `Covers`' whole-shape identity question
    /// at list grain, which requires equal arity (`term.rs`'s `covers_value`,
    /// `pt.len() == it.len()`). `Covers` is untouched and every existing caller
    /// keeps its exact semantics; see `covers_open_value` for why the split is
    /// per-LEVEL rather than per-container, and for the engine precedent
    /// (`shape_decode::covers_relation`) it restores consistency with.
    CoversOpen {
        pattern: TermIdx,
        instance: TermIdx,
        wild: Sym,
    },

    /// Anti-unification that RETAINS its WITNESSES — the lattice-MEET that also
    /// emits the DIFFERENCE. Evaluates `values` (a collection of structured
    /// Values) and returns a 2-Tuple `(template, sigmas)`: `template` is exactly
    /// the `AntiUnify` lgg, and `sigmas` is a Tuple of one Dict per instance,
    /// each mapping a position-PATH (a Tuple of step keys — Int index for
    /// Tuples, key Value for Dicts) to the subterm that filled that WILD in that
    /// instance. The residue `AntiUnify` discards, captured: the difference Y in
    /// "this is like X but with Y". `wild` is the `"·?·"` marker, as in
    /// `AntiUnify`. Additive twin of `AntiUnify` (which is left untouched).
    AntiUnifyWitness {
        values: TermIdx,
        wild: Sym,
    },

    /// Apply a witness substitution — the lattice-JOIN direction. Evaluates
    /// `template` and `sigma` (a Dict of path→value, as a `sigmas` element of
    /// `AntiUnifyWitness`) and walks the template, replacing each WILD by the
    /// value `sigma` binds at that position-PATH (unmatched WILDs stay WILD).
    /// Recurses into nested Tuples/Dicts so a higher-order template is
    /// instantiated structurally — the inverse of `AntiUnify`'s walk. This
    /// REALISES "X but with Y" (move DOWN the subsumption lattice) and inverts
    /// decompose. `wild` is the `"·?·"` marker. The constructive complement of
    /// the held matcher.
    Substitute {
        template: TermIdx,
        sigma: TermIdx,
        wild: Sym,
    },

    /// Unification — the lattice JOIN (lub), the constructive DUAL of `AntiUnify`
    /// (the MEET). Evaluates `values` (a collection of structured Values) and
    /// combines them DOWN to the most general specialisation consistent with all
    /// — the BLEND / amalgam: agreements kept (shared generic), WILD holes filled
    /// from whichever input is concrete (selective projection), Dicts unified over
    /// the union of keys + Tuples element-wise + Sets unioned (emergent structure
    /// in neither input alone), and a genuine leaf/shape CONFLICT FUSED into a
    /// frozenset {a,b,…} (the emergent fused slot that carries BOTH contributions
    /// and SURFACES the conflict — a singleton means consistent, never a silent
    /// drop). The Fauconnier-Turner blend / Ontañón-Plaza amalgam over the generic
    /// `AntiUnify` already computes. `wild` is the `"·?·"` marker, as in
    /// `AntiUnify`. Additive; existing Terms untouched.
    Unify {
        values: TermIdx,
        wild: Sym,
    },

    /// Graded STRUCTURAL similarity in [0,1] — the SOFT-leaf twin of the exact
    /// `AntiUnify`/`Covers` structural compare. Evaluates `a` and `b` (two
    /// structures) and recurses them in parallel like `AntiUnify`, but at a
    /// numeric-VECTOR leaf (a learned part-shape descriptor) returns a GRADED
    /// agreement exp(-||a-b||) instead of boolean equality, while string/atom
    /// leaves (relations, ids — the program skeleton) stay EXACT. Tuples/Dicts
    /// aggregate as mean × coverage; Sets as soft best-match overlap; WILD matches
    /// anything. So writer variation within a part-shape no longer breaks the
    /// match (the soft-vocabulary lift) while the relational program stays hard —
    /// recognition-by-generation that survives variation WITHOUT drifting to a
    /// holistic learned similarity. `wild` is the `"·?·"` marker, as in
    /// `AntiUnify`. Additive; existing Terms untouched.
    StructSim {
        a: TermIdx,
        b: TermIdx,
        wild: Sym,
    },

    /// DEQUANTIZATION — the beam-search shape composer (native twin of
    /// `domains/reflective_faculty.py::compose_design_for_goal`). Shape
    /// matching IS dequantization; order-N growth is dynamic quantization —
    /// this Term is the decode half of that loop (see CLAUDE.md / the
    /// `sd_mint_quantum` seed rule for the encode/grow half). Reads held
    /// parts off every node of type `codebook_type` (default
    /// "ShapeSignature": attrs `name`/`signature`/`kind`/`concept`|
    /// `faculty` — `signature` accepted either as a native Tuple-of-Tuples
    /// or a JSON-string attr, parsed). Assembles an ORDERED PLAN of parts
    /// covering as many of `goal`'s relations as possible via a bounded
    /// beam search over `(plan, used, residual, total_fit)` states.
    /// Per-candidate scoring reuses the held matcher exactly: `shape_fit`
    /// = `FixedCount(AntiUnify([residual[..n], part_sig[..n]]))` (n = the
    /// shorter length, position-aligned — the same score `_shared_shape`
    /// computes); `covers` = the residual relations whose predicate name +
    /// arity match some part relation AND pass `Covers(pattern=goal_rel,
    /// instance=part_rel)` (the same prefilter+check as `_covers_relation`).
    /// Candidates rank by `(relations covered DESC, fit DESC)`; the top
    /// `cand_k` expand each beam state; states prune to the top `beam` by
    /// `(coverage DESC, total_fit DESC)`, deduped on `(residual, used-set)`.
    /// Terminates on `max_steps` / no further expansion / full coverage;
    /// returns the best-seen terminal by `(coverage, total_fit)`.
    /// `beam=1, cand_k=1` reduces to the old greedy composer (the
    /// discriminative control). `exclude` (optional) evaluates to part
    /// name(s) to skip. `wild` is the `"·?·"` marker, as in
    /// `AntiUnify`/`Covers`. Output is a Dict mirroring
    /// `compose_design_for_goal`'s return shape field-for-field (minus
    /// `provenance`, which the Python shim adds) — UNLESS `field` names
    /// one of that Dict's keys (or the derived `"covered_by"` — the
    /// single covering part's name when the decode fully covers with a
    /// one-part plan, else `None` — the `induce_concern`-covered-branch
    /// convenience form), in which case just that value is returned. Lets
    /// a seed rule's `Computed` effect read one field straight off a
    /// decode without a Dict-key-extraction Term of its own. `field ==
    /// Sym::default()` (i.e. absent/empty in JSON) means "return the
    /// whole Dict".
    ///
    /// `wild_objects` (default `false`) — the SECOND coverage semantics
    /// the pre-migration Python had: `compose_design_for_goal` used
    /// literal role-token `Covers` (the default here, unchanged); but
    /// `induce_concern`'s covered-branch (`_held_coverage_patterns`)
    /// WILDCARDED every non-predicate slot of each held part's own
    /// signature relations before scoring, so an observation matching a
    /// held shape's PREDICATE SKELETON (arity + predicate name) counts
    /// as covered regardless of its literal object fillers. When `true`,
    /// each part's signature relations are transformed before both
    /// `shape_fit` and `covers_relation` run: slot 0 (the predicate) is
    /// kept, every other slot becomes the `wild` marker. This also flips
    /// the `Covers` pattern/instance roles for that check to
    /// `Covers(pattern=wildcarded_part_relation, instance=goal_relation)`
    /// — matching the pre-migration `_covers(agent, wpat, obs)` call
    /// exactly (`covers_value` only auto-matches a wild that appears on
    /// the PATTERN side, so wildcarding the part's own relation only
    /// takes effect when it is passed as the pattern). Only
    /// `seeds/shape_decode_loop.json`'s `sd_decode` rule sets this to
    /// `true`; the composer path stays literal (`false`) so
    /// `compose_design_for_goal` fixture parity is untouched.
    ShapeDecode {
        goal: TermIdx,
        codebook_type: Sym,
        exclude: Option<TermIdx>,
        /// Optional PER-NET basin scope: when present, restrict the
        /// codebook to parts whose `name` is in this set (the inclusion
        /// twin of `exclude`). `None` = unrestricted (backward compatible).
        codebook_scope: Option<TermIdx>,
        beam: i64,
        max_steps: i64,
        cand_k: i64,
        /// GAMMA_SEARCH_COMPLETENESS_FIXES.md Bug 2 — the total-expansion
        /// BUDGET (fueled-interpreter idiom, `ProgEval`'s `fuel` /
        /// `SynthEnumerate`'s `max_candidates`) that replaces `beam`'s old
        /// role as a per-step SURVIVOR-COUNT cap. `beam` is kept on the
        /// wire (backward compatible, still reported in the output Dict)
        /// but no longer TRUNCATES the frontier: every non-duplicate
        /// candidate state survives to the next step, cost-ordered
        /// (`(coverage DESC, total_fit DESC)`, cheapest/best-first) by the
        /// unchanged sort, until the total number of state EXPANSIONS
        /// across the whole search reaches `budget` — at which point the
        /// search stops honestly (`budget_exhausted: true` in the output)
        /// rather than silently returning a possibly-incomplete plan
        /// flagged identically to a certified-complete one. `<= 0` selects
        /// the documented default (see `shape_decode::DEFAULT_SD_BUDGET`).
        /// See `eval_shape_decode`'s doc for why a width cap here is label
        /// -bias-shaped: discarding a lower-ranked-but-necessary state
        /// after just one step can make an optimal, fully-covering plan
        /// unreachable even though the SAME resource budget, spent as
        /// "try more states" rather than "keep fewer states", would have
        /// found it (`scripts/probe_beam_completeness.py`, live-verified).
        budget: i64,
        field: Sym,
        wild: Sym,
        wild_objects: bool,
    },

    /// `MotorCompose` — native embodied-motor composition membership (see
    /// motor_compose.rs): Int(1) iff `candidate` is in the program the
    /// seed-rule search composer would build for (`episode`, `policy`).
    /// Pure function of graph state; the term-tree composer it mirrors is
    /// gen_embodied_motor_program_seed.py's open/expand/close cascade.
    MotorCompose {
        episode: TermIdx,
        policy: TermIdx,
        candidate: TermIdx,
    },

    /// Compact graph-native two-slice learned future-manifold projection.

    /// `TransformDecode` — the "quantum delta" twin of `ShapeDecode`:
    /// recognises an observation relation-system as ONE HELD codebook
    /// shape plus a UNIFORM per-dimension delta (numeric additive shift,
    /// or a non-identity symbolic substitution FUNCTION), rather than a
    /// composed plan of parts. See `shape_decode.rs::eval_transform_decode`
    /// and `ShapeDecode`'s doc above for the "transformation isn't
    /// transformation, it's quantum change in a specific dimension"
    /// framing: rotate/recolour/translate/speaker-shift/tense are all one
    /// mechanism — a residual confined to a sparse dimension set is
    /// explained as identity + delta BEFORE the codebook grows (protects
    /// `sd_mint_quantum` from minting on an explainable transform).
    ///
    /// Codebook read identical to `ShapeDecode` (`codebook_type` nodes,
    /// `name`/`signature`/`kind`/`concept`|`faculty`, `exclude` applies
    /// the same case-insensitive name-matching, shared via
    /// `shape_decode::apply_exclude`). Slot 0 (the predicate) is NEVER
    /// transformable — a predicate mismatch (or an arity mismatch)
    /// disqualifies a held part as a candidate entirely (a different
    /// predicate is a different shape, not a transform of one). Relations
    /// are aligned by a canonical sort of BOTH signatures (`value::
    /// cmp_value`, which compares a relation tuple by its slots in order —
    /// predicate first, then slot values); if relation COUNTS differ, no
    /// transform (no O(n!) matching search — out of scope).
    ///
    /// Per-dimension consistency is TWO-TIER, predicate-aware (see
    /// `shape_decode::build_candidate`'s block comment for the full
    /// rationale). Tier 1, the merged dimension (byte-identical to the
    /// original semantics): every aligned pair with slot k present —
    /// including non-mismatching ones, a same-value pair being a
    /// zero-delta constraint — agrees on ONE uniform numeric additive
    /// delta, or ONE symbolic held->observed substitution FUNCTION (each
    /// held value maps to exactly one observed value); identical
    /// per-predicate deltas MERGE into one un-keyed `{dim,kind,delta}`
    /// entry. Tier 2, the split (NUMERIC slots only, entered only when
    /// tier 1 fails): pairs re-pool per (predicate, slot); a group whose
    /// pairs are all equal is untransformed (not a transform, exempt
    /// from `max_dims`, no longer vetoes another predicate's delta at
    /// the same slot index — slot indices are per-relation-LOCAL
    /// coordinates, so `pose_o`'s slot 1 and `seg`'s slot 1 are
    /// different dimensions sharing a storage index); each internally-
    /// uniform NONZERO group becomes its own dimension whose entry
    /// carries an additional `pred` key (duplicate indices in `dims`
    /// allowed). A group non-uniform WITHIN one predicate is the NULL.
    /// Symbolic slots have NO tier 2 by design: substitution is value
    /// RENAMING, global by nature — the same held value mapping to two
    /// observed values under two predicates is the scrambled
    /// discriminative null that protects codebook growth (a scrambled
    /// residual must still mint). `max_dims` bounds the TRANSFORM ENTRY
    /// count. Zero mismatches at all (against some held part) is
    /// `identity` — a distinct honest marker; `explained` stays `false`
    /// (identity is `sd_recognize`'s case, not a transform, so a rule
    /// never routes an exact match here). Ranking across candidates that
    /// DO explain: fewest dims (entries), then fewest total substitution
    /// pairs, then most relations, then name (Occam).
    ///
    /// Output Dict: `explained` (bool) / `base` (the winning held part's
    /// name, or the closest non-explaining candidate's name, or `None`) /
    /// `transforms` (list of `{dim,kind:"shift"|"subst",delta}`, plus a
    /// `pred` key on tier-2 split entries ONLY — committed tier-1 outputs
    /// are byte-identical; empty unless `explained`) / `dims`
    /// (convenience: `transforms`' dim indices, parallel array,
    /// duplicates possible in split mode) / `deltas` (convenience:
    /// `transforms`' delta values, parallel array) / `checked`
    /// (candidates examined) / `residual_unexplained` (the best
    /// candidate's differing relations when NOT explained, else empty) /
    /// `identity` (bool). `field` selects one key exactly like
    /// `ShapeDecode`'s selector (reuses `shape_decode::select_field`/
    /// `finish` unchanged — `deltas` is a real Dict key here, not a
    /// derived one, so no shared-helper changes were needed).
    TransformDecode {
        goal: TermIdx,
        codebook_type: Sym,
        exclude: Option<TermIdx>,
        max_dims: i64,
        field: Sym,
    },

    /// `NetForward` — native forward pass of a graph-resident authored
    /// net (the Rust twin of `code_writing_cortex.forward`). `assemblage`
    /// evaluates to a `NetworkAssemblage` node; `inputs` to a list of
    /// numbers. Walks `-has_step->` `AssemblageStep`s in `order`,
    /// applying `ReLU(W1·x+b1)` then `W2·h+b2` per step from the step's
    /// `-has_weight->` `WeightTensor{role,data}` children, returning the
    /// final vector as a `Value::Tuple` of floats. Read-only over `G`.
    /// This is the "cheap default path" a reflex net is gated in front
    /// of: authored (write-not-train), exact, evaluable inside a Rule.
    NetForward {
        assemblage: TermIdx,
        inputs: TermIdx,
    },

    /// `DimInfer` — RUNG 2 of the transform-as-quantum-delta ladder:
    /// infers a MISSING DIMENSION before falling back to `TransformDecode`'s
    /// per-slot delta. "Sometimes you need to infer a dimension before you
    /// transform — rotating a flat 2D rectangle in the Z dimension gives you
    /// a transform in XY that can't be replicated without Z." A held part's
    /// signature can carry an optional `dim_types` attr (one entry per slot:
    /// `"pred"` / `"coord:<axis>"` / `"val"` / `"sym"`; absent — rung 2 is
    /// gracefully skipped for that part, no crash, no candidate). Separately,
    /// `generator_type`-typed nodes (default `"DimensionGenerator"`) hold
    /// `{name, kind, coord_dims, params}`: `kind` selects the built-in
    /// primitive (`"rotation90"`, `"reflection_r"`, `"reflection_c"`),
    /// `coord_dims` names which of the part's OWN slots the generator acts
    /// on (integer lattice only), `params` is the list of `k` quanta to try
    /// (e.g. rotation steps 1..3; a `k`-fold application composes the
    /// primitive with itself, self-renormalizing its bbox each step, so
    /// `k=2` for a reflection is the identity).
    ///
    /// For every held part with `dim_types` present, times every generator
    /// whose `coord_dims` are ALL typed `"coord:*"` on that part, times every
    /// `k` in the generator's `params`: apply the generator to the part's OWN
    /// signature (about the shape's own bbox, normalized to the origin so a
    /// pure rotation/reflection needs no separate translation), then run the
    /// SAME rung-1 consistency check `TransformDecode` uses (shared via
    /// `shape_decode::build_candidate` — no duplicated matcher logic) on the
    /// generator-transformed candidate vs the goal. A post-generator EXACT
    /// match (no residual dims at all) is a full explanation via the
    /// generator alone; a post-generator residual that itself resolves to a
    /// consistent per-dim delta composes (rotation + translation +
    /// recolour, all at once) — reported as the SAME `{dim,kind,delta}`
    /// shape `TransformDecode` emits, just for what's left after the
    /// generator. Exact verification only, integer lattice only — no
    /// approximate matching.
    ///
    /// COMPOSITION (length ≤ 2 — see `runners/dsl/COMPOSITION_DESIGN.md`):
    /// some transforms need TWO non-linear generators together (rotate THEN
    /// scale, reflect THEN scale, rotate THEN modular-cycle) where neither
    /// reduces to the other nor to a linear residual. So in addition to the
    /// single-generator arm above, `DimInfer` also tries every ordered pair
    /// of DISTINCT generators `(g_a k_a) then (g_b k_b)` — apply `g_a` `k_a`
    /// times, then `g_b` `k_b` times, then the SAME rung-1 check on the
    /// leftover. A self-composition `(g,g)` is just `g` at a higher `k` (its
    /// own dimension) and is skipped, so a single-generator codebook yields
    /// ZERO length-2 attempts. Both orders are tried (order matters in
    /// general; the scale×isometry pairs commute on the origin-normalised
    /// lattice, `modular`×`scale2` does not). Every step stays integer-`k`,
    /// integer-lattice; `build_candidate` is reused UNCHANGED (a composition
    /// of count-preserving remaps is still count-preserving, so its
    /// count-equality prefilter holds).
    ///
    /// Ranking (Occam, within rung 2 only — rung-1-first ordering across
    /// rungs is a seed-rule concern, not this Term's): composition LENGTH
    /// strictly first (a length-2 composite NEVER beats a length-1
    /// explanation — the analog of rung-1<rung-2), then fewest residual dims,
    /// then candidate name, then the `k` sequence (smallest first, for
    /// determinism when tied `k` values both work on a symmetric shape). Any
    /// remaining exact tie (two different generators/pairs producing the
    /// identical image at the same k) is broken by first-seen generator
    /// iteration (load) order. For length 1 this reduces byte-identically to
    /// the committed `(1 + residual_dims, base_name, k)` key and tie
    /// behaviour.
    ///
    /// Output Dict: `explained` (bool) / `base` (winning held part's name,
    /// or `None`) / `generator` (the winning sequence's FIRST generator
    /// `name`, or `None` — scalar, kept for length-1 back-compat) / `k`
    /// (the first step's quantum count, or `None`) / `length` (Int: number
    /// of generator steps, 1 or 2; 0 when unexplained) / `generators`
    /// (Tuple of the step generator names, in order) / `ks` (Tuple of the
    /// parallel step `k` values) / `latent_name` (Str: the composite label
    /// body — the single name for length 1, `"a+b"` for length 2 — which
    /// the seed prefixes with `latent:`) / `transforms` (the RESIDUAL
    /// per-dim deltas left after the WHOLE sequence, same `{dim,kind,delta}`
    /// shape as `TransformDecode`) / `dims` (convenience: `transforms`' dim
    /// indices) / `checked` (generator-sequence attempts actually tried,
    /// post `dim_types` gating — includes length-2 attempts) / `identity`
    /// (bool: `true` when the sequence alone fully explains the goal with
    /// zero residual dims). `field` selects one key exactly like
    /// `ShapeDecode`/`TransformDecode`'s selector (reuses
    /// `shape_decode::select_field`/`finish` unchanged).
    DimInfer {
        goal: TermIdx,
        codebook_type: Sym,
        exclude: Option<TermIdx>,
        generator_type: Sym,
        max_dims: i64,
        field: Sym,
    },

    /// `GenInfer` — the GENERATOR-MINTING op, the DELTA on `DimInfer` at the
    /// point the held generator codebook is exhausted WITHOUT a match. Where
    /// `DimInfer` SELECTS a transform from a finite named codebook, `GenInfer`
    /// INFERS a NEW general integer-linear generator FROM THE ORBIT (a held
    /// base shape + a goal that is an unrecognised transform of it) and
    /// reports its matrix so a rule can MINT it as graph data (a
    /// `DimensionGenerator{kind:"linear", matrix:…}`), grow the codebook, and
    /// re-decode. The inference is DimInfer-native generate-and-test but over
    /// the PARAMETERIZED FAMILY of all integer `n×n` maps within a
    /// DATA-DERIVED entry bound (not a named list), applied via the SAME
    /// `apply_linear_once` a minted generator uses and verified via the SAME
    /// rung-1 `build_candidate` check — so a success is exactly what re-decode
    /// reproduces. Integer 2-D lattice only; the identity map is excluded.
    /// See `shape_decode::eval_gen_infer`. Output Dict: `explained` /
    /// `base` / `matrix` (flattened row-major Tuple of Ints) / `coord_dims` /
    /// `ncoord` / `residual_dims` / `transforms` / `dims` / `checked`;
    /// `field` selects one key exactly like `DimInfer`.
    GenInfer {
        goal: TermIdx,
        codebook_type: Sym,
        exclude: Option<TermIdx>,
        max_dims: i64,
        field: Sym,
    },

    /// `RatioInduce` — POPULATION RATIO-INVARIANCE INDUCTION, the cross-frame,
    /// population-level sibling of `GenInfer`. Where `GenInfer` induces ONE
    /// integer generator from ONE orbit, `RatioInduce` induces, from a
    /// POPULATION of frames related by a PER-FRAME multiplicative rescaling,
    /// the INVARIANT RATIO SET — the cross-coordinate ratios that stay fixed as
    /// each frame's own scale varies (the cross-frame sibling of the audio
    /// stack's within-signal ratio cancellation, on the `scale2`/base-as-
    /// dimension ladder). `population` evaluates to a collection of frames,
    /// each a collection of `[pred, coord, coord, …, val]` relation tuples (the
    /// same Value-tuple shape `GenInfer`/`DimInfer` consume). For each frame it
    /// reads the origin-normalized extent of each coord slot through
    /// `coord_ints` (integer lattice ONLY — a `Float` coordinate is CROSS-FRAME
    /// and makes the population inapplicable, the frame/continuum invariant
    /// inherited for free), READS the reduced integer cross-coordinate ratio
    /// set from the first frame, and VERIFIES it across every frame by integer
    /// cross-multiplication (the population analogue of
    /// `infer_translate_offset`'s read-then-verify). The induced object is a
    /// RATIO — a RELATION held in `Hom`, applied on read, minted as a
    /// `DimensionGenerator`/`LatentDimension` param (`scale2`-family when the
    /// set is power-of-two, else a diagonal `kind:"linear"` matrix
    /// `apply_linear_once` already reads — ZERO new dispatch arm), NEVER a
    /// continuous coordinate stored in-frame. A population that is NOT purely
    /// multiplicative FALSIFIES the invariant (the honest MDL floor,
    /// `explained=false`). See `shape_decode::eval_ratio_infer`. Output Dict:
    /// `explained` / `coord_dims` / `ncoord` / `ref_dim` / `ratios` (flat
    /// `[slot,num,den]` triples) / `is_pow2` / `matrix` / `latent_name`
    /// (`latent:ratio` / `latent:scale2`) / `n_frames` / `checked`; `field`
    /// selects one key exactly like `GenInfer`.
    ///
    /// `resolution` is the OBSERVATION-RESOLUTION tolerance (integer, default 0
    /// = EXACT). Per CLAUDE.md a ratio is pinned only to observational
    /// resolution ("never encode precision the steps cannot support (MDL)"):
    /// `0` demands an exact integer cross-frame ratio (the clean synthetic
    /// mechanism); a non-zero `q` (the grid step the coordinates were quantized
    /// to) admits a DATA-SCALED integer residual so a ratio recovered from a
    /// REAL, quantized observation is accepted iff it holds to within the
    /// resolution the observation supports — kept fully in integer arithmetic,
    /// NO float, the invariant intact.
    RatioInduce {
        population: TermIdx,
        codebook_type: Sym,
        resolution: i64,
        field: Sym,
    },

    /// `TimeInfer` — the TEMPORAL sibling of `GenInfer`, one level up: does a
    /// SEQUENCE of frames (in tick order) form an ORBIT under ONE transition
    /// generator `G` carrying `frame(t) -> frame(t+1)` for EVERY consecutive
    /// pair? If so, that generator's exponent `k` IS the inferred TIME axis
    /// (a minted `latent:time` dimension — time lives in `Hom(frame,frame)`,
    /// never in a frame's coordinates). `G` is inferred from the first pair
    /// (affine translate preferred, else integer 2×2 linear — the same
    /// enumerate-and-test as `GenInfer`) and VERIFIED by exact equality across
    /// every remaining pair; a shuffled / varying-velocity sequence is not an
    /// orbit and grounds unexplained (the MDL floor). See
    /// `shape_decode::eval_time_infer`. Output Dict: `explained` / `kind` /
    /// `offset` / `matrix` / `coord_dims` / `window` / `predicted` (the UNSEEN
    /// `G^K(f0)`) / `checked`; `field` selects one key.
    TimeInfer {
        sequence: TermIdx,
        codebook_type: Sym,
        max_b: i64,
        field: Sym,
        /// Forward-projection horizon for the `crossing` field: the number of
        /// steps the fitted generator is walked before the projection gives
        /// up and reports the horizon itself. A caller-declared bound, never
        /// an order cap — the ORDER still falls out of compressibility.
        max_steps: i64,
        /// EXACT (default `false`) vs ROBUST/MDL witness. Exact answers the
        /// IN-FRAME question — "is there an INTEGER order-N generator carrying
        /// every pair by exact equality?" — and floors a fractional (continuous)
        /// acceleration, correctly, because a non-integer generator is not
        /// expressible in-frame (the frame/continuum invariant). Robust answers
        /// the CROSS-FRAME question — "is this the STEPPED observation of a
        /// continuous order-N parabola (constant to within its own dispersion)?"
        /// — via a description-length verdict on the same pyramid, for real
        /// (noisy-integer) perception. Opt-in so the exact consumers (mass
        /// recovery / galileo, which NEED the integer generator) are byte-
        /// identical; only a caller that explicitly asks the cross-frame
        /// question sets it.
        robust: bool,
    },

    /// `DepthInfer` — MONOCULAR STRUCTURE-FROM-MOTION, the DEPTH sibling of
    /// `TimeInfer`. It reads the RESIDUAL of `TimeInfer`'s question: a scene with
    /// real (discrete) depth translated past a moving eye produces a 2D
    /// transformation NO SINGLE flat generator can explain — near layers sweep
    /// faster than far (motion parallax). That residual — DIFFERENT regions
    /// needing DIFFERENT translate generators — IS the depth signal. Each
    /// observable SURFACE (cells sharing their non-coord slots) must be a rigid
    /// constant-velocity translate (the same rigidity test `TimeInfer` runs,
    /// per region); `>=2` DISTINCT surface velocities ⇒ mint `latent:depth`, the
    /// ordinal dimension indexing surfaces by motion (faster = nearer, `n_layers`
    /// = distinct-velocity count read from the data); `<=1` distinct velocity ⇒
    /// one generator carries the scene ⇒ NO depth (a flat scene, even a
    /// multi-colour one at a single velocity, mints nothing — the anti-forced
    /// control). Integer/in-frame only; continuous perspective is CROSS-FRAME and
    /// deferred. See `shape_decode::eval_depth_infer`. Output Dict: `explained`
    /// / `n_layers` / `velocities` / `ordering` / `layers` / `predicted` (the
    /// UNSEEN frame at tick K, each surface advanced by its own velocity) /
    /// `window` / `reason` / `checked`; `field` selects one key.
    DepthInfer {
        sequence: TermIdx,
        codebook_type: Sym,
        max_b: i64,
        field: Sym,
    },

    /// `BlinkBridge` — THE BLINK: a temporal hole bridged by grounding, the
    /// TEMPORAL TWIN of the blind spot and the COMPOSITION of the grounded-field
    /// fill with `TimeInfer`'s transition generator. Input `sequence` =
    /// `[prefix(visible), gap(EMPTY = blink), resumed(visible)]`. `G` is inferred
    /// from the pre-blink orbit (translate preferred, else integer 2×2 linear —
    /// the SAME test as `TimeInfer`) and CONTINUED through the gap: the belief at
    /// blink tick `t` is `G^t(f0)`, NOT the frozen last frame (persistence) and
    /// NOT an invented value (confabulation). `confirm_run` (confirming prefix
    /// transitions) is the TEMPORAL SUPPORT; the bridge/hold DECISION lives in the
    /// seed rule reading these fields (`gap <= confirm_run` = RELATIVE decay, no
    /// constant; `explained=false` = no consistent motion ⇒ held open). On resume
    /// the continued belief is CONFIRMED (invisible) or REVISED where the
    /// observation diverges (change blindness). Integer/in-frame only. See
    /// `shape_decode::eval_blink_bridge`. Output Dict: `explained` / `kind` /
    /// `offset` / `matrix` / `coord_dims` / `prefix_len` / `confirm_run` / `gap` /
    /// `bridged` (continued beliefs) / `frozen` (persistence baseline) /
    /// `diverged_at` / `resume_ok` / `checked`; `field` selects one key.
    BlinkBridge {
        sequence: TermIdx,
        codebook_type: Sym,
        max_b: i64,
        field: Sym,
    },

    /// `TransferDecode` — ANALOGICAL MECHANISM TRANSFER, the retrieval-side
    /// sibling of `ShapeDecode` / `TransformDecode` / `DimInfer`. Faithful
    /// port of `domains/reflective_faculty.py`'s
    /// `retrieve_and_transfer_mechanism` + `transfer_mechanism` +
    /// `_filler_after_cue` (see `shape_decode::eval_transfer_decode`).
    ///
    /// `goal` evaluates to a Tuple-of-Tuples (a list of steps, each a list of
    /// tokens); `meta_shape` evaluates to the recognised meta-shape `Str`
    /// (the caller's own `categorise_by_shape` verdict — this Term consumes
    /// it, never re-derives it). The held SHAPE→MECHANISM index
    /// (`{name, meta_shape, domain, slots, steps}`) is READ DIRECTLY FROM THE
    /// GRAPH by `shape_decode::load_mechanisms` — exactly as `ShapeDecode`
    /// reads its `codebook_type`. The codebook's node-TYPE is not a Term arg:
    /// it is DISCOVERED from the graph's `CodebookRegistry` declaration
    /// (`shape_decode::codebook_type_from_registry`), so the only well-known
    /// anchor is the registry type itself. The Python `_load_mechanisms`
    /// Lit-arg shim and the `mechanism_type` literal are both gone.
    ///
    /// RETRIEVE the mechanism(s) indexed under the recognised shape, DERIVE
    /// each abstract slot's target filler from the GOAL's own predicate/
    /// argument structure via the slot's cue, RE-INSTANTIATE the mechanism's
    /// steps with those fillers, and (on tie of held mechanisms) keep the
    /// highest `total_fit`. Output Dict mirrors the Python report:
    /// `{meta_shape, retrieved, transferred}` (with an honest-wall `note`
    /// when no shape is recognised or none is indexed under it); `transferred`
    /// carries `{plan, slot_map, total_fit, unbound_roles, mechanism,
    /// source_domain, meta_shape}`.
    TransferDecode {
        goal: TermIdx,
    },

    /// `RecogniseShape` — META-SHAPE RECOGNITION, the single shared recognition
    /// path (`shape_decode::recognise_meta_shape`) used by BOTH the agent's
    /// `categorise_by_shape` faculty (`domains/teach.py`, now a thin shim over
    /// this Term) AND `TransferDecode` (which derives its own goal shape). No
    /// duplicated scorer.
    ///
    /// `text` evaluates to a String (interned `Str` or `Surface(Text)`). It is
    /// scored against every held `MetaShape` node: a shape's score is how many
    /// of its `has_principle` neighbours (Principle nodes) carry a `keywords`
    /// entry that is a SUBSTRING of `text` (a principle counts once if ANY of
    /// its keywords matches). The winner is the argmax by `(-score, name)`
    /// (most overlap, then `name` ascending — deterministic); its `name` `Value`
    /// is returned, or `Value::None` when no shape scores > 0 (or `text` is
    /// empty / no vocabulary held). The Term does NOT lowercase — the caller
    /// supplies the final text, preserving `categorise_by_shape`'s exact bytes.
    RecogniseShape {
        text: TermIdx,
    },

    /// `MetaShapeMint` — RUNG 4 of the meta-shape grain's growth ladder, the
    /// mint `SHAPE_AUDIT.md` finding #1 reports is missing ("the sd loop's
    /// fourth rung is not wired to the faculty named 'shape'").
    ///
    /// `observation` evaluates to a `Value::Node` — a residual shape
    /// observation. The Term groups every `obs_type`-typed node whose `status`
    /// is `status_value` by its PREDICATE SET (the sorted, de-duplicated set of
    /// its signature's relation predicates — order-independent and untruncated,
    /// unlike the `CapabilityAxis` key `SHAPE_AUDIT.md` §3.1 documents), and
    /// reports whether that group has RECURRED (support >= 2) with a
    /// non-trivial anti-unified core. See `shape_decode::eval_meta_shape_mint`.
    ///
    /// Output Dict: `name` / `keys` / `signature` / `support` / `fixed` /
    /// `leader` / `mintable`; `field` selects one key, as in `TransformDecode`.
    MetaShapeMint {
        observation: TermIdx,
        obs_type: Sym,
        status_value: Sym,
        wild: Sym,
        field: Sym,
    },

    /// `StrokeQuantize` — the handwriting instance of "shape matching IS
    /// dequantization; a transform IS a quantum delta on ONE dimension"
    /// (`HANDWRITING_DESIGN.md`): quantizes raw stroke GEOMETRY into a
    /// `ShapeSignature`-compatible relation-system so `ShapeDecode` /
    /// `TransformDecode` / `DimInfer` / the `sd_*` rule loop apply
    /// UNCHANGED to ink. Pure deterministic geometry, no graph reads.
    ///
    /// `points` evaluates to a Tuple of `[x, y]` frames (Int or Float
    /// scalars; malformed entries are skipped, never panic). The
    /// polyline is RESAMPLED BY ARC LENGTH into `segments` (default 12)
    /// equal-length pieces, producing `segments+1` resample knots and
    /// `segments` directed sub-vectors.
    ///
    /// Per segment `i` (0-indexed): `["seg", i, turn_q, len_q]` —
    /// `turn_q` is the SIGNED relative turn (this segment's heading
    /// minus the PREVIOUS segment's heading, wrapped to `(-180°,180°]`)
    /// quantized to `turn_bins` (default 16) bins spanning `±180°`;
    /// segment 0 has no previous heading, so `turn_q = 0` there BY
    /// DEFINITION (a documented, stable choice — not "segments start at
    /// i=1"). `len_q` is this segment's arc-length FRACTION of the
    /// total (quantized to `len_bins`, default 8, over `[0,1)`) — near-
    /// uniform (≈`1/segments`) after an EQUAL-arc resample by
    /// construction, kept as a real per-segment value so a future
    /// non-uniform resampling strategy has somewhere to write. Both
    /// `turn_q` and `len_q` are rotation/translation/scale-INVARIANT:
    /// relative turns are unaffected by a rigid transform or uniform
    /// scale, and length fractions cancel the scale factor.
    ///
    /// Unless `invariant_only`, four SEPARATE arity-2 pose relations are
    /// appended — `["pose_x", x_q]` / `["pose_y", y_q]` / `["pose_o",
    /// orient_q]` / `["pose_s", scale_q]` — so a similarity transform
    /// reads back as a delta CONFINED to a single relation per pose
    /// dimension (`TransformDecode`'s tier-2 per-(predicate, slot)
    /// semantics), rather than one blended pose tuple that would force
    /// an (unwanted) single shared delta across position/orientation/
    /// scale at once. `invariant_only: true` (default `false`) omits all
    /// four — the invariant-comparison shape (NOTE: an invariant-only
    /// signature has fewer relations than a full one, so it can never be
    /// a `TransformDecode` candidate against a full goal — relation
    /// counts must match; use `canonical_pose` for codebook AUTHORING).
    ///
    /// `canonical_pose: true` (default `false`) is the CODEBOOK-ENTRY
    /// form: the four pose relations are emitted with every pose quantum
    /// at its CANONICAL bin instead of the measured one — position at
    /// the bounds-origin bin (`["pose_x", 0]` / `["pose_y", 0]`),
    /// initial heading at bin 0 (`["pose_o", 0]`), and scale at the bin
    /// containing `log2(arc_len) = 0` (i.e. arc length 1 after
    /// normalization: `["pose_s", scale_bins/2]` for the fixed `[-4,4]`
    /// log2 range — bin 4 at the default `scale_bins = 8`). Relation
    /// counts then MATCH a full observed signature, the seg relations
    /// align invariantly, and an observed stroke's pose deltas versus
    /// the canonical entry ARE the rung-1 similarity transform
    /// (`TransformDecode` reads rotation as the `pose_o` delta,
    /// translation as `pose_x`/`pose_y`, log-scale as `pose_s`).
    /// Ignored when `invariant_only` is set (no pose relations at all
    /// wins). The informational `pose` Dict in the output ALWAYS carries
    /// the MEASURED pose regardless of this flag — only the emitted
    /// signature relations are canonicalized.
    /// `x_q`/`y_q` bucket the FIRST resample knot (`= points[0]`, arc-
    /// length resampling preserves endpoints) on a `grid`×`grid`
    /// (default 8) lattice over `bounds` (`[x0,y0,x1,y1]`, optional
    /// Term) when given, else the point-set's OWN bbox — a DOCUMENTED
    /// LIMITATION: without external `bounds`, position is relative to
    /// the ink alone, not to a page/canvas frame, so pure translation of
    /// an otherwise-unbounded stroke can be invisible to `x_q`/`y_q`
    /// (the self-bbox translates right along with the points). `orient_q`
    /// is the FIRST segment's absolute heading, quantized the same way
    /// as `turn_q` (`turn_bins` bins over `±180°`). `scale_q` buckets
    /// `log2(total_arc_len)` (clamped to a documented fixed range
    /// `[-4,4]` — i.e. arc lengths from `1/16` to `16` in the input's
    /// own coordinate units resolve distinctly; outside that range
    /// `scale_q` saturates at an end bin) over `scale_bins` (default 8)
    /// buckets.
    ///
    /// Quantization is round-half-away-from-zero for angles (signed,
    /// symmetric about 0°) and floor-bucket digitization for position/
    /// length-fraction/log-scale (which cell contains the value). A
    /// documented limitation: a value that lands EXACTLY on a bin
    /// boundary can flip by one bin under floating-point error —
    /// callers (and this Term's own tests) keep fixture angles/positions
    /// safely inside a bin, never engineered onto an edge.
    ///
    /// Output Dict: `signature` (native Tuple of Tuples — the relation-
    /// system above, `seg` entries then, unless `invariant_only`, the
    /// four `pose_*` entries) / `pose` (a Dict `{x_q,y_q,orient_q,
    /// scale_q}` — ALWAYS present regardless of `invariant_only`, the
    /// informational read-back) / `arc_len` (Float, the total resampled
    /// arc length) / `n_points` (Int, the input point count). Degenerate
    /// input (fewer than 2 distinct points, or total arc length ≈ 0)
    /// returns a graceful minimal Dict — empty `signature`, zeroed
    /// `pose`, `arc_len: 0.0` — never panics. `field` selects one key,
    /// exactly like `ShapeDecode`/`TransformDecode`/`DimInfer`'s
    /// selector. `seg_sym`/`pose_x_sym`/`pose_y_sym`/`pose_o_sym`/
    /// `pose_s_sym` are fixed sentinels (like `AntiUnify`'s `wild`) —
    /// interned once when the Term is constructed (JSON parse / reflect
    /// reconstruct / direct Rust construction), NEVER at `evaluate()`
    /// time (`EvalCtx::interner` is `&Interner`, immutable — see
    /// `shape_decode.rs`'s module doc for why a fresh intern mid-eval is
    /// not available) — this is what lets a part's predicate slot
    /// (`Value::Str`) compare EQUAL to the same predicate arriving via a
    /// codebook node's stored signature.
    /// RUN 32 addition (`OPTION R`, "the bin grain" — `results/run28_checkpoints/
    /// calibration_report.json`'s 10,230/10,231-LEARN-spans-in-one-family finding):
    /// `turn_edges`/`len_edges` (optional Terms, each evaluating to a flat ascending
    /// `Vec<f64>` of `n_bins+1` interval BOUNDARIES) let a caller supply DATA-PLACED
    /// (e.g. quantile/equal-mass) bin edges instead of a fixed uniform COUNT — the
    /// adaptive-quantization lever. When given (`len >= 2`), `turn_edges` overrides
    /// BOTH the per-segment `turn_q` quantization AND the absolute-heading `orient_q`/
    /// `pose_o` quantization (the same angular dimension); `len_edges` overrides the
    /// per-segment `len_q` quantization only (position/scale bins are untouched — out
    /// of this lever's declared scope). ABSENT (the default, every pre-existing caller):
    /// BYTE-IDENTICAL to the pre-RUN-32 uniform `turn_bins`/`len_bins` behaviour —
    /// `turn_bins`/`len_bins` remain meaningful (and are what a caller not using edges
    /// still sets) even when this Term also carries an edges Option, since Rust cannot
    /// omit a struct field conditionally; only an edges array with `len >= 2` actually
    /// engages the adaptive path (`strokes::quantize_edges`/`edge_bin_center`). Edges
    /// use LEFT-EDGE-INCLUSIVE floor digitization (`quantize_edges`, the adaptive analog
    /// of `quantize_bucket`'s uniform digitization) for BOTH turn and length — a
    /// DELIBERATE departure from `quantize_signed_angle`'s own round-to-nearest-center
    /// convention for the uniform turn path, chosen so quantile-derived interval
    /// boundaries (which ARE floor-digitizable edges, not centers) apply uniformly to
    /// both dimensions without a second convention to keep straight.
    ///
    /// `emit_residual` (default `false`, additive): when `true`, the output Dict also
    /// carries a `residuals` key — a Tuple of `[i, turn_residual, len_residual]` entries
    /// parallel to `signature`'s `seg` entries ("the remainder goes to more detail," the
    /// creator's own standing dynamic-quantization law, applied to WITHIN-bin detail
    /// rather than a coarser/finer bin split) — `turn_residual`/`len_residual` are the
    /// SIGNED offset between the raw continuous value and the bin's own center (via
    /// whichever center function — uniform or edge-based — actually quantized it), so a
    /// residual is well-defined and comparable under EITHER path. `i == 0`'s
    /// `turn_residual` is always `0.0` (mirrors `turn_q`'s own "segment 0 has no
    /// previous heading" convention — nothing to measure a residual against). Never
    /// changes `signature`'s own relation content — purely additive.
    StrokeQuantize {
        points: TermIdx,
        segments: i64,
        turn_bins: i64,
        len_bins: i64,
        grid: i64,
        scale_bins: i64,
        invariant_only: bool,
        canonical_pose: bool,
        turn_edges: Option<TermIdx>,
        len_edges: Option<TermIdx>,
        emit_residual: bool,
        bounds: Option<TermIdx>,
        field: Sym,
        seg_sym: Sym,
        pose_x_sym: Sym,
        pose_y_sym: Sym,
        pose_o_sym: Sym,
        pose_s_sym: Sym,
    },

    /// `StrokeRender` — `StrokeQuantize`'s exact generative inverse
    /// (`HANDWRITING_DESIGN.md`, "ABS AS DEFAULT": "the generation and
    /// reading model is the same ... it just runs the same engine in
    /// reverse"). Dequantizes a `ShapeSignature`-compatible stroke
    /// relation-system BACK into a polyline: `seg`/`pose_*` relations at
    /// their BIN CENTERS drive the same heading-integration geometry
    /// `StrokeQuantize` samples FROM, in reverse.
    ///
    /// `signature` evaluates to the relation-system — a native Tuple of
    /// relation Tuples (as `StrokeQuantize`'s own output/`Lit` literals
    /// produce, real interned `Sym` predicates) OR a `Value::Str`/
    /// `Value::Surface(Text, ..)` holding the same relation-system as a
    /// JSON array-of-arrays string (the convention every `ShapeSignature`
    /// codebook node's `signature` attr already uses). Unlike
    /// `shape_decode.rs`'s `json_to_value_scoped`, the JSON-string path
    /// needs NO interner involvement at all: `StrokeRender` never emits a
    /// relation predicate back into the graph, so a predicate is only
    /// ever compared as a plain `&str` against the fixed literals `"seg"`
    /// / `"pose_x"` / `"pose_y"` / `"pose_o"` / `"pose_s"` — no
    /// pre-interned sentinel Syms are needed on this Term (contrast
    /// `StrokeQuantize`'s `seg_sym`/`pose_*_sym` fields, needed only
    /// because ITS output must compare equal to a codebook's stored
    /// predicates).
    ///
    /// `seg` relations (`["seg", i, turn_q, len_q]`, any arity ≥ 4 —
    /// trailing slots ignored, matching the design doc's arity-5 padding
    /// note) are collected and sorted by ordinal `i`; `n = ` the count.
    /// Segment `0`'s `turn_q` is IGNORED (by `StrokeQuantize`'s own
    /// convention it is always `0`, meaningless) — the initial heading
    /// comes from pose instead. For `i ≥ 1`, the heading accumulates
    /// `turn_q`'s bin-CENTER angle (`quantize_signed_angle`'s exact
    /// inverse: bin `q`'s center is `q * (360/turn_bins)`, wrapped to
    /// `(-180,180]`); each segment's length is `len_q`'s bin-center
    /// FRACTION (`(idx+0.5)/len_bins`) times the current arc length.
    ///
    /// `apply_pose` (default `true`) selects posed vs canonical
    /// rendering: when `true` AND all four `pose_x`/`pose_y`/`pose_o`/
    /// `pose_s` relations are present, the start point comes from
    /// `pose_x`/`pose_y`'s bin centers over a `grid`×`grid` lattice on
    /// `bounds` (`[x0,y0,x1,y1]`, optional Term — ABSENT bounds falls
    /// back to a canonical `[0,grid)` unit frame, a documented
    /// limitation mirroring `StrokeQuantize`'s self-bbox note: there is
    /// no point set yet at render time to derive a bbox from, so a
    /// round-trip that cares about position must pass the SAME `bounds`
    /// both ways), the initial heading from `pose_o`'s bin center, and
    /// the arc length from `pose_s`'s bin center via the same `[-4,4]`
    /// log2 mapping `StrokeQuantize` uses (`arc_len = 2^center`). When
    /// `false`, or when any pose relation is missing, rendering is
    /// CANONICAL: start `(0,0)`, initial heading `0°`, arc length `1`
    /// (exactly `StrokeQuantize`'s `canonical_pose` codebook-entry
    /// convention) — canonical and posed renders of the same signature
    /// therefore differ by EXACTLY the similarity transform
    /// (rotate by the posed heading, scale by the posed arc length,
    /// translate to the posed start) applied uniformly to every point,
    /// since arc-length resampling commutes with similarity transforms.
    ///
    /// The `n` reconstructed segment endpoints (`n+1` exact geometric
    /// knots) are then resampled BY ARC LENGTH (reusing
    /// `resample_by_arclength`, the same stepping `StrokeQuantize` uses
    /// forward) into `n_points` (default `24`) output points — "a
    /// polyline of `n_points` via arc-length stepping". A signature with
    /// zero `seg` relations renders a graceful empty `points` Tuple
    /// (`arc_len: 0.0`), never panics.
    ///
    /// Output Dict: `points` (native Tuple of `[x,y]` Tuples, length
    /// `n_points`) / `n_strokes` (`Int`, always `1` — this Term renders
    /// one stroke; multi-stroke composition is character-level, out of
    /// scope) / `arc_len` (`Float`, the rendering's OWN arc length — `1`
    /// canonical or the posed `pose_s` read-back). `field` selects one
    /// key, exactly like `StrokeQuantize`'s selector.
    ///
    /// ROUND-TRIP GATE (the design's central claim, made checkable):
    /// `StrokeQuantize(StrokeRender(sig), <matching turn_bins/len_bins/
    /// grid/scale_bins/bounds>) == sig` for a signature `StrokeQuantize`
    /// itself produced, PROVIDED the fixture is bin-center-safe (every
    /// quantized value sits clear of a bin boundary) and `n_points` is
    /// chosen so the intermediate arc-length resampling introduces no
    /// corner-cutting (e.g. `n_points = segments + 1`, or any multiple
    /// of `segments` plus one) — see `strokes.rs`'s round-trip test for
    /// the exact reasoning and a documented boundary caveat.
    /// RUN 32 addition: `turn_edges`/`len_edges`, the `StrokeQuantize`-side doc's exact
    /// generative-inverse twin — when given (`len >= 2`), overrides `seg`/`pose_o`
    /// turn-bin-center and `seg` length-bin-center reconstruction with
    /// `strokes::edge_bin_center` instead of the uniform `angle_bin_center`/
    /// `bucket_center`. A caller round-tripping an adaptively-quantized signature MUST
    /// pass the SAME edges arrays here that produced it (the exact-inverse gate's own
    /// pre-existing "matching turn_bins/len_bins/grid/scale_bins/bounds" contract,
    /// extended to cover edges too). Absent (default): byte-identical to pre-RUN-32.
    StrokeRender {
        signature: TermIdx,
        n_points: i64,
        apply_pose: bool,
        turn_bins: i64,
        len_bins: i64,
        grid: i64,
        scale_bins: i64,
        turn_edges: Option<TermIdx>,
        len_edges: Option<TermIdx>,
        bounds: Option<TermIdx>,
        field: Sym,
    },

    /// `SigmaLognormalGenerate` — Plamondon's Kinematic Theory (sigma-
    /// lognormal / delta-lognormal model): handwriting is the space-time
    /// superimposition of a small number of LOGNORMAL velocity
    /// primitives, each aimed at a virtual target with a constant
    /// direction, summed in velocity space and integrated to a
    /// trajectory (`sigma_lognormal.rs`'s module doc; `RESEARCH_CURSIVE.md`
    /// C4). This is the CONTINUOUS motor-PLANNING generator — contrast
    /// `StrokeQuantize`/`StrokeRender` above, a DISCRETIZED shape
    /// codebook (run 71's floor: self-consistent but not discriminative
    /// on real ink of the same class).
    ///
    /// `primitives` evaluates to a Tuple of `[t0, mu, sigma, D, theta]`
    /// 5-tuples (any trailing slots ignored) — the FITTED (or
    /// hand-authored) motor plan; extraction from a real trajectory's
    /// velocity profile is Python-side signal processing (peak
    /// detection + closed-form least-squares — NOT a trained net), this
    /// Term only ever GENERATES. `start` evaluates to `[x0, y0]`, the
    /// pen's own starting position. `t_start`/`t_end` bound the uniform
    /// time grid the trajectory is sampled on (`t_end <= t_start`
    /// degrades gracefully to a unit-length window); `n_points` (≥2)
    /// sets the output resolution.
    ///
    /// At each grid time `t`, the vector velocity is
    /// `V(t) = Σ_i D_i · Λ(t − t0_i; mu_i, sigma_i) · (cos θ_i, sin θ_i)`
    /// where `Λ` is the lognormal density (zero for `t <= t0_i`);
    /// position is the TRAPEZOIDAL-QUADRATURE integral of `V` from
    /// `t_start`, starting at `start` — a genuinely CONTINUOUS trajectory
    /// (no bin/grid quantization anywhere in this path).
    ///
    /// Output Dict: `points` (Tuple of `[x,y]`, length `n_points`),
    /// `velocity` (Tuple of `[vx,vy]`, the same length, the raw
    /// superposition sampled at each grid time — useful for fit
    /// diagnostics), `n_points` (Int), `n_primitives` (Int, the count of
    /// well-formed primitives actually used). `field` selects one key,
    /// exactly like `StrokeQuantize`'s selector. Zero primitives is
    /// graceful: the pen never leaves `start`.
    SigmaLognormalGenerate {
        primitives: TermIdx,
        start: TermIdx,
        t_start: f64,
        t_end: f64,
        n_points: i64,
        field: Sym,
    },

    /// Backed-up k-step lookahead value over a previewed game-tree subgraph —
    /// the agent-decision core of `_lookahead` (the world adapter expands the
    /// tree by previewing actions and stamps each candidate's immediate
    /// `score_key`; this folds it). `value(n, d) = score(n) + (d>1 ∧ n has
    /// children ? max_child value(child, d-1) : 0)`. `choose_action`'s k-step
    /// is then `Argmax` over the root's first-action candidates of this value.
    /// `depth = 1` reduces to the immediate score (greedy), matching the
    /// default. The recursion is bounded by `depth`.
    LookaheadValue {
        node: TermIdx,
        child_edge: Sym,
        score_key: Sym,
        depth: TermIdx,
    },

    /// Every scalar (type, key, value) triple across all nodes, as an ordered
    /// LIST (Tuple) preserving per-node occurrences — the attr-enumeration
    /// source for graph-wide novelty. Scalar = Bool/Int/Str. Nodes whose type
    /// starts with `skip_prefix` (e.g. `"Term."`) are skipped; empty prefix
    /// skips none. Composes the novelty channel-1 count of
    /// `_novelty_count`: `Count{FilterList{ScalarAttrTriples, t, ¬In{t, seen}}}`
    /// — a node-attr occurrence is novel iff its `(type,attr,value)` triple is
    /// not in the agent's seen-triple memory.
    ScalarAttrTriples {
        skip_prefix: Sym,
    },

    /// Dynamic attribute access: read `node`'s attr whose KEY is the string
    /// `name` evaluates to (vs `Attr`, whose key is a static `Sym`). The
    /// enabler for parameterized goals — one generic satisfaction Term reads
    /// `AttrByName{target, goal.target_attr}` so a single Term + construction
    /// Rule serves a whole family of typed goals instead of a baked factory
    /// per (attr, value). None if `node` isn't a Node, `name` isn't a Str, or
    /// the attr is absent.
    AttrByName {
        node: TermIdx,
        name: TermIdx,
    },

    // --- rendering: text + byte surfaces ---
    Surface {
        kind: SurfaceKind,
        payload: Value,
    },
    Cat {
        items: Vec<TermIdx>,
    },
    Slot {
        name: Sym,
    },
    Join {
        separator: Option<TermIdx>,
        items: Option<TermIdx>,
    },
    Bytes {
        items: Vec<TermIdx>,
    },
    U8 {
        expr: Option<TermIdx>,
    },
    U16LE {
        expr: Option<TermIdx>,
    },
    U32LE {
        expr: Option<TermIdx>,
    },
    U64LE {
        expr: Option<TermIdx>,
    },
    LEB128 {
        expr: Option<TermIdx>,
    },
    Lines {
        items: Vec<TermIdx>,
    },
    Label {
        prefix: Sym,
    },
    Let {
        name: Sym,
        value: Option<TermIdx>,
        body: Option<TermIdx>,
    },
    Nth {
        items: Option<TermIdx>,
        index: i64,
    },
    Render {
        term: Option<TermIdx>,
        lang: Option<TermIdx>,
    },
    /// CODE-3 (writing is reading reversed): a FAITHFUL Python literal
    /// representation of a scalar `value` — the type-aware quoting a
    /// bare `Slot("value")` render binding can't do (Cat's `str()`
    /// coercion leaves a string Lit unquoted and a Bool/None Lit
    /// leaking Rust's Debug format, the CODE-1/2 named render-surface
    /// residual). `value` evaluates to a scalar Value (None/Bool/Int/
    /// Float/Str, the only kinds a `Lit` node ever holds); the RenderRule
    /// template composes `LitRepr(value=Slot("value"))` in place of the
    /// bare Slot. Any non-scalar Value is an honest render gap (`None`),
    /// never approximated — see `python_repr` for the exact algorithm.
    LitRepr {
        value: Option<TermIdx>,
    },
    ArgMin {
        items: Vec<TermIdx>,
    },

    /// GRAPH LAW #6 (trans-frame identity): domain-general READ-ONLY
    /// "same-thing-across-frames" correspondence. `prev`/`cur` each
    /// evaluate to a Node collection (Set/FrozenSet/Tuple, any mix of
    /// those). Every node's `feature_key` attr is read as its position
    /// in an ARBITRARY-DIMENSION feature space (a `Value::Tuple`/`Set`
    /// of numbers -- a bare scalar attr is treated as a 1-D vector);
    /// unlike `segment_and_track` (its domain-specific pixel/centroid
    /// twin -- see `Substrate::segment_and_track` in substrate.rs,
    /// which stays untouched), the feature dimensions are never grid
    /// coordinates, so this Term serves any domain a caller can turn
    /// into numbers (conversation-turn entities matched by attribute
    /// vector, tracked objects in any sensor space, graph-state
    /// snapshots of a concept, ...).
    ///
    /// If `category_key` is `Some`, a prev/cur pair whose `category_key`
    /// attrs are unequal (`Value::PartialEq`) can never match -- the
    /// general form of `segment_and_track`'s "same `value`" gate. If
    /// `extent_key` is `Some`, each node's `extent_key` attr (a
    /// `Set`/`FrozenSet`/`Tuple`, read as a multiset) drives an
    /// OVERLAP-FIRST match pass — a candidate wins if its overlap count
    /// is at least half the smaller extent's size — exactly
    /// `segment_and_track`'s cell-overlap rule, generalised past grid
    /// cells to any extent-of-things. Whatever isn't claimed by
    /// overlap (or has no extent) falls back to a EUCLIDEAN
    /// nearest-feature-vector match, gated by `radius` (a `TermIdx`
    /// evaluating to the max matchable distance) — the general form of
    /// `segment_and_track`'s nearest-centroid-within-span fallback.
    /// Matching is greedy with no reuse: each `prev` item claims at
    /// most one `cur` item, processed in `cur`'s iteration order.
    ///
    /// Pure computation — reads `ctx.graph` but writes nothing. Returns
    /// a `Value::Dict` with three keys (`Value::Surface(Text)`, since
    /// the evaluator's interner is immutable at eval time — same
    /// convention `TextShape`'s result Dict uses): `"matched"` (a
    /// `Tuple` of `(prev_node, cur_node)` `Tuple` pairs — the SAME
    /// identity persists across the pair), `"births"` (a `Tuple` of
    /// `cur` nodes with no prev match — a new identity), `"deaths"` (a
    /// `Tuple` of `prev` nodes with no cur match — that identity ended
    /// this frame). Assigning a persistent `identity` ATTR from this
    /// correspondence is a WRITE, so it lives in the mutating twin
    /// `Effect::TrackIdentity` (queues onto `graph.pending_track_identity`,
    /// drained by `Substrate::apply_pending_track_identity` calling
    /// `Substrate::track_identity` — same read-Term/write-Effect split
    /// `FbFrameSeq`/`Effect::FbSample` already established for the
    /// perception-as-action boundary).
    TrackIdentityCorrespondence {
        prev: TermIdx,
        cur: TermIdx,
        feature_key: Sym,
        category_key: Option<Sym>,
        extent_key: Option<Sym>,
        radius: TermIdx,
    },

    /// `GapAbduce` — THE ENDPOINT-ABDUCED GENERATOR, and the ONE operator the
    /// timephi rung measured the substrate to lack. Every other temporal
    /// mechanism here (`TimeInfer`, `DepthInfer`, `BlinkBridge`) infers its
    /// generator `G` from a CONSECUTIVE VISIBLE PAIR and then EXTRAPOLATES —
    /// CONTINUATION. A phi stimulus supplies exactly ONE pre-gap sample, so
    /// there is no pair to infer from, and `BlinkBridge` correctly FREEZES.
    /// This Term does the other thing: it solves `G^(gap+1)(f_before) =
    /// f_after` for `G` **from the two ENDPOINTS ALONE** — INTERPOLATION.
    ///
    /// Input `sequence` = `[prefix..(visible), gap..(EMPTY), suffix..(visible)]`,
    /// exactly `BlinkBridge`'s shape. `f_before` is the LAST visible frame
    /// before the gap and `f_after` the FIRST after it; **nothing else in the
    /// sequence is consulted for the abduction**, which is precisely why it
    /// works at `prefix_len == 1`.
    ///
    /// **THE DIVISIBILITY TEST — NO THRESHOLD, AND NOWHERE TO PUT ONE.** The
    /// total displacement `D` is read by the UNMODIFIED `infer_translate_offset`
    /// (equal cardinality, one uniform integer coordinate shift, byte-identical
    /// non-coord slots). The abduced per-step generator is `D / steps` where
    /// `steps = gap + 1`, and it is ADMISSIBLE IFF `D[i] % steps == 0` on every
    /// coordinate slot — exact integer arithmetic, no tolerance (PROTOCOL §13
    /// satisfied BY CONSTRUCTION, not by choosing a good constant). `D == 0` is
    /// the identity and is REFUSED, matching `TimeInfer`'s exclusion of the still
    /// pattern. A `steps`-th root in the integer 2×2 LINEAR class is the
    /// fallback, enumerated within the same data-derived bound as
    /// `TimeInfer`/`GenInfer` and accepted only on EXACT equality.
    ///
    /// **THE SCOPE LIMIT, MEASURED AND NOT HIDDEN: this operator has NO
    /// DISCRIMINATIVE POWER ON THE TRANSLATE CLASS.** Any two same-shape figures
    /// ARE related by a rigid translate, so the only constraint is divisibility,
    /// and the acceptance rate on independent random endpoints is `~1/steps`,
    /// not zero. `TimeInfer` at N>=3 refuses ACCEL and SHUFFLE because a THIRD
    /// frame CONSTRAINS; two endpoints and one free generator always fit.
    /// Interpolation is cheap for exactly that reason.
    ///
    /// See `shape_decode::eval_gap_abduce`. Output Dict: `explained` / `kind`
    /// (`translate`/`linear`) / `offset` / `matrix` / `coord_dims` / `gap` /
    /// `steps` / `total` (the endpoint displacement `D`) / `divisible` /
    /// `reason` (`ok`/`identity`/`indivisible`/`not_rigid`/`no_gap_structure`) /
    /// `bridged` (the abduced intermediates `G^t(f_before)`) / `closes` (does
    /// `G^steps(f_before)` equal `f_after` EXACTLY) / `correction` (the
    /// symmetric-difference cell count at `f_after` — 0 iff it closes) /
    /// `prefix_len` / `checked`; `field` selects one key. Integer / in-frame
    /// only, exactly as `TimeInfer`.
    GapAbduce {
        sequence: TermIdx,
        codebook_type: Sym,
        max_b: i64,
        field: Sym,
    },

    /// `GapVerify` — THE ABDUCED INTERMEDIATES, CHECKED. `GapAbduce` emits its
    /// intermediates (`bridged`) and compares them to NOTHING, which is why it
    /// has NO DISCRIMINATIVE POWER on the translate class: any two same-shape
    /// figures ARE rigid translates, so divisibility is its only constraint and
    /// it accepts independent random endpoints at `~1/steps`.
    ///
    /// This Term supplies the missing constraint. Where `GapAbduce` requires the
    /// gap frames to be EMPTY, this one requires them to be **OBSERVED**: the
    /// moving figure is absent, the rest of the scene is present. Each abduced
    /// intermediate `G^t(f_before)` is then a FALSIFIABLE PREDICTION about frame
    /// `t`, and it is CHECKED.
    ///
    /// **STRICT ACCOUNTABILITY — the verification rule, and it has no number in
    /// it.** For every gap tick, each predicted cell must COINCIDE with some
    /// cell actually observed at the same integer coordinates (all coordinate
    /// slots, exact equality — an IN-FRAME comparison, which the frame/continuum
    /// invariant says must be integer; a "close enough" radius here would be a
    /// CROSS-frame quantity smuggled in-frame). `violations` counts predicted
    /// cells with nothing observed at their coordinates; `verified` iff
    /// `violations == 0`. The semantics is occlusion accountability: *a figure
    /// predicted where it would have been VISIBLE, and not observed there, is
    /// FALSIFIED.*
    ///
    /// **THE SPLIT GENERALISES `GapAbduce`'s AND REDUCES TO IT.** Cells are
    /// partitioned by `surface_key` (their non-coordinate slots — the criterion
    /// `infer_translate_offset` and `DepthInfer` already use), and a gap frame is
    /// one whose surface-key SET is a STRICT SUBSET of the banks'. An EMPTY
    /// frame's key set is `{}` — a strict subset of any non-empty set — so on a
    /// blank-gap stimulus this split is IDENTICAL to `GapAbduce`'s, and the
    /// abduction fields agree cell-for-cell.
    ///
    /// Every surface shared by the two banks must be RIGID. `MOVING` = the
    /// surfaces with non-zero displacement, of which **exactly one** is admitted
    /// (`multi_motion` otherwise — several velocities is `DepthInfer`'s
    /// question). `HIDDEN` = surfaces at both banks and absent throughout the
    /// gap; with `gap >= 1` it must EQUAL `MOVING` (`hidden_mismatch` otherwise —
    /// *what vanished must be what moved*). At `gap == 0` there are no
    /// intermediates and verification is VACUOUS **on the same code path** — no
    /// second mechanism is spliced in at one end of the ISI curve.
    ///
    /// **WHAT THIS CANNOT DO, STATED WHERE THE MECHANISM IS:** it does not infer
    /// occlusion ORDER. It asks only whether SOMETHING was observed where the
    /// figure was predicted, so a figure predicted IN FRONT of an occluder is
    /// wrongly accounted. And on a genuinely BLANK gap nothing is observed, so
    /// every prediction is violated and classic phi is REFUSED — this mechanism
    /// is MORE refusing than a human, by construction.
    ///
    /// See `shape_decode::eval_gap_verify`. Output Dict: `GapAbduce`'s keys
    /// (`explained` here means abduced AND verified) plus `abduced` (the
    /// divisibility verdict alone), `verified`, `violations`, `ticks` (gap ticks
    /// actually checked), `predicted` (cells actually compared), `covered`,
    /// `surfaces`, `hidden`; `reason` gains `unverified` / `inconsistent_gap` /
    /// `hidden_mismatch` / `multi_motion`. `field` selects one key. Integer /
    /// in-frame only, exactly as `TimeInfer`.
    GapVerify {
        sequence: TermIdx,
        codebook_type: Sym,
        max_b: i64,
        field: Sym,
    },

    /// `ArgminUnique` — **`Argmin`, BUT IT CAN SAY NO.**
    ///
    /// `VISION_REFUSAL_CAPACITY_RESULTS.md` §7 measured that `Argmin` **returned
    /// a winner from five IDENTICAL candidates** — a set in which nothing is
    /// better than anything else, so there is nothing to decide — and that its
    /// only null is an EMPTY source. §10 states the law behind it: **a
    /// comparison can be false, a selection cannot.**
    ///
    /// This variant is the fix that rung named (§9.1). Identical fold to
    /// `Argmin`, with ONE added condition: if two or more candidates tie at the
    /// extremum, return `default` (or `Value::None`) instead of an arbitrary
    /// one of them. `PickUnique` is the precedent — the same discipline was
    /// applied to **185 CONFIGURATION reads and to ZERO VERDICT reads**, which
    /// is exactly the asymmetry this closes.
    ///
    /// **Why it does not PANIC as `PickUnique` does.** An ambiguous *config*
    /// read is a malformed graph and dies loudly. An ambiguous *percept* is a
    /// normal fact about a scene (two candidates genuinely fit equally well),
    /// so the admissible response is the null, not a crash. The severity
    /// follows the kind of thing being read.
    ///
    /// **§13: uniqueness is EXACT EQUALITY** (`cmp_value == Equal`). There is no
    /// constant in this variant and nowhere to put one.
    ///
    /// **Default OFF by non-existence**: no seed binds this Term, so every
    /// committed result reproduces byte-identically (§9). Arming it at a site
    /// requires that site's caller to be able to REPRESENT the null — see
    /// `VISION_ARGMIN_UNIQUE_RESULTS.md` arm C.
    ArgminUnique {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
        default: Option<TermIdx>,
    },
    /// `SupportInfer` — `TimeInfer`'s rigidity core with the APPEARANCE SLOTS
    /// TAKEN OUT OF THE VERDICT AND REPORTED SEPARATELY. A PARTITION, NOT A
    /// TOLERANCE: there is no slack parameter and nowhere to put one. The
    /// coordinate slots must be an exact uniform integer translate carried by
    /// ONE offset across the WHOLE orbit; the `pred` slot must stay
    /// byte-identical; every OTHER slot is counted into `appearance_residual`
    /// and never compared against anything. See `shape_decode::eval_support_infer`
    /// for why it exists (the pixel-seam rung's R6 isolation), why it can still
    /// refuse (it VERIFIES a read offset — it does not SELECT a best one), and
    /// what it cannot do (translate only; DEAD on a dense bounded raster, at the
    /// IDENTITY exclusion and not at R6).
    SupportInfer {
        sequence: TermIdx,
        codebook_type: Sym,
        field: Sym,
    },
    /// `MotionEnergy` — **MOTION IS ORIENTATION IN SPACE–TIME, READ AS
    /// INTERFERENCE** (Adelson & Bergen 1985). The waveform-native alternative
    /// to the SAD block-matcher, aimed at the ISI wall: five correspondence /
    /// abduction mechanisms in this tree all peak at ISI=0, the INVERSE of human
    /// phi (which needs a temporal gap), and `GapVerify` proved no filter over an
    /// abduction can ever make ISI=0 worse. A temporal-frequency channel can.
    ///
    /// Reduce the raster to the horizontal space–time signal (collapse rows —
    /// this arc is horizontal-only), take the joint 2-D DFT over `(x, ti)`, and
    /// partition the power `|S(ωx, ωt)|²` by the SIGN of the orientation:
    /// opposite-sign quadrants are `right`, same-sign `left`, `ωt==0` is
    /// `static`, `ωx==0` is `flicker`, `(0,0)` is `dc`. The directional readout
    /// is the OPPONENT `right − left`. See `shape_decode::eval_motion_energy`.
    ///
    /// **The Fourier/wave representation is a CROSS-FRAME MAP by this project's
    /// own axioms** (the frame/continuum invariant): the spatial frame is the
    /// integer pixel lattice, the spectral frame is integer-indexed bins, and the
    /// real-valued structure (phase, energy) lives in the transform BETWEEN them.
    /// **§13: no number** — the partition is exact sign/equality on integer DFT
    /// indices; a two-frame (ISI=0) sequence has only DC+Nyquist temporal
    /// frequencies, and Nyquist is direction-ambiguous (`P(ωx,Nyq)=P(−ωx,Nyq)`
    /// for a real signal), so `opponent==0` is FORCED by the sampling limit, not
    /// chosen. **Default OFF by non-existence**: no seed binds this Term.
    MotionEnergy {
        sequence: TermIdx,
        height: i64,
        width: i64,
        field: Sym,
    },
    /// `ArgminRefusal` — **`Argmin` that returns a DISTINCT refusal token on a
    /// tie, and `None` on an empty source — the two SEPARATED.**
    ///
    /// `VISION_ARGMIN_UNIQUE_RESULTS.md` measured that `ArgminUnique` can refuse
    /// but "no caller in the seed layer can hear it": at the 16 `Eq(node, sel)`
    /// WTA sites a refusal is `Bool(false)` — byte-identical to *"you are not the
    /// winner"* AND to *"the source was empty"*; at the 85 `Attr(sel, key)` sites
    /// it is a bare `None`. And `argmin_or_argmax_over` returns `default` on BOTH
    /// the tie-path AND the empty-path (`term.rs` lines ~8195 and ~8223), so even
    /// the existing `default` cannot separate REFUSED from NOTHING.
    ///
    /// This variant makes the split the `default` cannot: on a **tie** (non-unique
    /// extremum) it returns the evaluated `refused` token (a held `RefusalMark`
    /// node, passed as data); on an **empty source** it returns `Value::None`. So
    /// a consuming rule reads THREE distinct values — a real winner (REAL), the
    /// marker node (REFUSED), and `None` (NOTHING) — plus `Bool(false)` from any
    /// comparison it makes (NO). The refusal token is thus reachable ONLY by a
    /// comparison-matched-nothing (a tie), NEVER by a selection over ordinary
    /// values: an ordinary `Argmin`/`Argmax`/`Pick` never emits it, and this Term
    /// over DISTINCT candidates returns the winner, not the token. That IS the
    /// governing law — a comparison can be false, a selection cannot.
    ///
    /// **§13:** uniqueness is exact equality (`cmp_value == Equal`). There is no
    /// constant in this variant and nowhere to put one. The distinctness is a
    /// held NODE (data), not a reserved magic string.
    ///
    /// **§9 by non-existence:** no committed seed binds this Term, and every
    /// existing selector is threaded with `refused_on_tie = None`, so every
    /// committed result reproduces byte-identically.
    ArgminRefusal {
        source: TermIdx,
        var_name: Sym,
        value: TermIdx,
        refused: Option<TermIdx>,
    },

    // ------------------------------------------------------------------
    // --- Program IR (P1, PROGRAM_SYNTHESIS_PLAN.md §3.2) ---------------
    // ------------------------------------------------------------------
    //
    // STATEMENT/EXPRESSION IR variants for the program-synthesis hub IR.
    // These are DATA, not directly-evaluated operations: the main
    // `evaluate()` returns `Value::None` (the documented INERT value) for
    // every `Prog*` variant below EXCEPT `ProgEval` itself. Execution
    // happens ONLY inside the fueled `ProgEval` interpreter
    // (`prog_eval.rs`) — the DSL stays a pure expression language; a
    // program is a Term subgraph the agent can match, decode, render and
    // repair, and `ProgEval` is the one pure Dict-in → Dict-out window
    // onto its semantics.
    //
    // NAMING / RECONCILIATION (the P0-histogram variant set + While +
    // Raise; see PROGRAM_SYNTHESIS_P1_NOTES.md for the full table):
    // every variant carries the `Prog` prefix because each one is
    // PROGRAM-domain and must not be conflated with the existing DSL
    // twin it superficially resembles:
    //   - `ProgAttrGet` reads a field of a program VALUE (record/Dict);
    //     `Attr` reads a GRAPH NODE's attr (requires `Value::Node`).
    //   - `ProgSubscript` is Python subscript semantics (negative
    //     indices, Dict keys, honest trap on miss); `IndexAt` is the
    //     DSL's list primitive (clamping/None conventions).
    //   - `ProgContainerLit{kind}` KEEPS the surface kind (list vs tuple
    //     vs set vs dict) for rendering, which `Vec_`/`SetT`/`MkDict`
    //     erase; at ProgEval runtime list/tuple both realise as
    //     `Value::Tuple` (documented collapse), set → `Set`,
    //     dict → `Dict`.
    //   - `ProgAssignVar`/`ProgSeq`/... have no DSL twin at all: the DSL
    //     is pure and has no statements.
    //
    // Field conventions: child Terms are `TermIdx` (reflect: a
    // `child.<field>` edge); ordered bodies are `Vec<TermIdx>`
    // (index-attr edges); identifier lists (`targets`, `names`) are
    // `Vec<Sym>` (reflect: ONE Tuple-of-Str scalar attr — identifiers
    // are interned at parse time, the sound naming path); optional
    // identifiers use the `Sym::default()` sentinel (the
    // ReachableFrom/TrackIdentityCorrespondence convention).
    /// Statement sequence — a block body. Executes each statement in
    /// order under ProgEval; inert (`Value::None`) under `evaluate()`.
    ProgSeq {
        stmts: Vec<TermIdx>,
    },
    /// `name = value`. The program env binds `name` (a parse-time Sym).
    ProgAssignVar {
        name: Sym,
        value: TermIdx,
    },
    /// `name OP= value`. `op` is the lowercased Python ast op name:
    /// add/sub/mult/div/floordiv/mod/pow/lshift/rshift/bitand/bitor/
    /// bitxor. Numeric combination delegates to the matching DSL
    /// arithmetic Term (Plus/Minus/Times/Div/IDiv/Mod/Pow/Shl/Ashr/
    /// BitAnd/BitOr/BitXor semantics — documented divergences from
    /// CPython, e.g. div-by-zero → 0.0, apply here too); `add` also
    /// concatenates Str/Surface(Text) and Tuple values.
    ProgAugAssign {
        name: Sym,
        op: Sym,
        value: TermIdx,
    },
    /// `a, b, c = value` — flat tuple unpack onto simple names. `value`
    /// must realise a Tuple of exactly `targets.len()` elements
    /// (trap `unpack:arity` otherwise). Nested targets are a parse
    /// residual, not representable here (honest scope cut).
    ProgTupleUnpack {
        targets: Vec<Sym>,
        value: TermIdx,
    },
    /// Statement-grain `if cond: then else: orelse`.
    ProgIfStmt {
        cond: TermIdx,
        then: TermIdx,
        orelse: Option<TermIdx>,
    },
    /// `for var in iter: body [else: orelse]` — orelse runs iff the loop
    /// was not broken (Python for-else). Each iteration charges fuel.
    ProgForEach {
        var: Sym,
        iter: TermIdx,
        body: TermIdx,
        orelse: Option<TermIdx>,
    },
    /// `while cond: body [else: orelse]`. Semantically load-bearing for
    /// ProgEval despite low corpus mass (the P0-registered
    /// deviation-with-reason). Each iteration charges fuel — the
    /// in-frame integer axis; there is no wall clock anywhere.
    ProgWhile {
        cond: TermIdx,
        body: TermIdx,
        orelse: Option<TermIdx>,
    },
    /// `break` / `continue` — `kind` is the Sym "break" or "continue".
    ProgLoopCtl {
        kind: Sym,
    },
    /// `return [value]`.
    ProgReturn {
        value: Option<TermIdx>,
    },
    /// `try: body except [as exc_var]: handler`. Catches TRAPS raised in
    /// `body` (ProgRaise, extern misses, subscript/attr misses, ...);
    /// NEVER catches fuel exhaustion (fuel is not a trap — catching it
    /// would forge `halted`). `exc_var == Sym::default()` = unnamed;
    /// absent handler = catch-and-continue (`except: pass`). No
    /// finally, no typed except clauses (documented narrower scope).
    ProgTryOr {
        body: TermIdx,
        exc_var: Sym,
        handler: Option<TermIdx>,
    },
    /// `raise [exc]` — mints a trap `raise:<str(exc)>` (or `raise`).
    /// Semantics-only P1 inclusion (P0 deviation-with-reason twin of
    /// While): honest trap surfacing needs a native thrower.
    ProgRaise {
        exc: Option<TermIdx>,
    },
    /// `import module [as alias]` / `from module import names...`.
    /// Structural surface only: executes as a NO-OP under ProgEval (the
    /// binding is extern surface; any USE of an unbound imported name
    /// traps honestly at the use site — `name:<n>` / `extern:<n>`).
    ProgImportStmt {
        module: Sym,
        alias: Sym,
        names: Vec<Sym>,
    },
    /// `obj[index] = value` — read-modify-write through an lvalue path
    /// rooted at a Var (chains of ProgSubscript/ProgAttrGet allowed;
    /// values are immutable, the path is rebuilt — NO aliasing, the
    /// documented divergence from CPython reference semantics).
    ProgSubscriptSet {
        obj: TermIdx,
        index: TermIdx,
        value: TermIdx,
    },
    /// `obj.attr = value` — record-field write, same lvalue machinery.
    /// Program records are Dict values (see ProgAttrGet).
    ProgAttrSet {
        obj: TermIdx,
        attr: Sym,
        value: TermIdx,
    },
    /// One `def` parameter with an optional default. As a ProgEval
    /// statement it BINDS `name` from the incoming env if present, else
    /// from `default` (i.e. `def f(x=3)` called without `x`), else
    /// traps `param:<name>` — the honest missing-argument.
    ProgDefFnParam {
        name: Sym,
        default: Option<TermIdx>,
    },

    // --- Program-IR expressions (evaluated only inside ProgEval) ---
    /// A call to an EXTERN callable — `name` is the callee as spelled
    /// (`len`, `math.sqrt`, `append`); `recv` is the receiver for
    /// method calls (`xs.append(1)` → recv=Var(xs), name="append").
    /// ProgEval evaluates a CallExtern ONLY against the declared
    /// `oracles` Dict (name → declaration); an undeclared name traps
    /// `extern:<name>`, a declared-but-not-natively-implemented one
    /// traps `extern:unimplemented:<name>`. NO shelling out, ever.
    /// Native oracle set: len/abs/min/max/range/sum/str/int/float/
    /// bool/sorted (the histogram's call_builtin mass).
    ProgCallExtern {
        name: Sym,
        recv: Option<TermIdx>,
        args: Vec<TermIdx>,
    },
    /// Object-field read on a program VALUE: records are Dict values,
    /// `obj.attr` reads the pair whose key string-equals `attr` (trap
    /// `attr:<name>` on miss). Distinct from `Attr` (graph-node attr).
    ProgAttrGet {
        obj: TermIdx,
        attr: Sym,
    },
    /// Python subscript read: Tuple + Int (negative from the end; OOB
    /// traps `index:oob`), Dict + key (missing traps `key:<k>`),
    /// Surface(Text)/Str + Int → one-char Surface. Distinct from
    /// `IndexAt` (DSL list primitive, clamp/None conventions).
    ProgSubscript {
        obj: TermIdx,
        index: TermIdx,
    },
    /// Python slice read: `obj[start:stop:step]` over Tuple or
    /// Str/Surface(Text) (Q1 `slicing` family; Dict traps
    /// `slice:type`). Absent bounds follow Python's own defaults
    /// (conditioned on step sign); `step` absent → 1; `step == 0`
    /// traps `slice:zero_step`. Never an OOB trap — Python slicing
    /// clamps, unlike `ProgSubscript`'s single-index read. Always
    /// realises as the SAME kind as `obj` (Tuple stays Tuple, a string
    /// stays Surface(Text)).
    ProgSlice {
        obj: TermIdx,
        start: Option<TermIdx>,
        stop: Option<TermIdx>,
        step: Option<TermIdx>,
    },
    /// Display literal: `kind` ∈ list/tuple/set/dict. For dict, `items`
    /// alternate key,value (the MkDict convention). Runtime realisation:
    /// list/tuple → Tuple (kind retained in IR for rendering), set →
    /// Set, dict → Dict (keys must be scalar; sorted by cmp_value).
    ProgContainerLit {
        kind: Sym,
        items: Vec<TermIdx>,
    },
    /// `[expr for var in source if cond]` — eager, ordered, → Tuple.
    /// Each iteration charges fuel (a comprehension IS a loop).
    ProgComprehensionList {
        var: Sym,
        source: TermIdx,
        expr: TermIdx,
        cond: Option<TermIdx>,
    },
    /// `(expr for var in source if cond)` — SAME eager semantics, →
    /// Tuple (the generator is exhausted eagerly; the IR keeps the
    /// surface kind for rendering). Consumers like `sum(...)` agree
    /// with CPython because the realised sequence is identical.
    ProgComprehensionGen {
        var: Sym,
        source: TermIdx,
        expr: TermIdx,
        cond: Option<TermIdx>,
    },
    /// `a is b` / `a is not b`. Honest scope: None-identity (either
    /// side None → identity test against None) and Node-identity;
    /// anything else traps `is_op:unsupported` rather than
    /// approximating identity with `Eq` (the P0 §4 requirement).
    ProgIsOp {
        a: TermIdx,
        b: TermIdx,
        negated: bool,
    },
    /// f-string: parts are Lit(Str) segments and expressions; each part
    /// renders via `py_str` (Python `str()` spelling for scalars) and
    /// the whole concatenates to Surface(Text).
    ProgFString {
        parts: Vec<TermIdx>,
    },

    /// `ProgEval` — THE one pure fueled interpreter over the Program IR
    /// (plan §3.2). `prog` is either an INLINE `Prog*` subtree in this
    /// arena, or a Term evaluating to a `Value::Node` rooting a
    /// reflected IR subgraph (`reflect::term_from_subgraph` — the
    /// EvalSubgraph convention). `env` evaluates to a Dict of initial
    /// bindings (keys resolved via `Interner::lookup`; keys with no
    /// interned Sym cannot be referenced by any parsed IR and pass
    /// through to `env_out` untouched). `oracles` evaluates to the
    /// extern-declaration Dict for ProgCallExtern. `fuel` bounds
    /// statement steps + loop/comprehension iterations (≤0 → the
    /// documented default 10_000); exhaustion → `halted:false`,
    /// `steps == fuel`, `trap:"fuel"`, honest PARTIAL `env_out`, never
    /// a value. Output Dict: `result` (ProgReturn's value or the value
    /// of a bare-expression prog, else None) / `env_out` (Dict) /
    /// `steps` (Int) / `halted` (Bool) / `trap` (Str|None); `field`
    /// selects one key (the ShapeDecode selector convention). PURE:
    /// Dict in → Dict out, no substrate mutation, no I/O — engine in
    /// `prog_eval.rs`, this arm is a one-line handoff.
    ProgEval {
        prog: TermIdx,
        env: Option<TermIdx>,
        oracles: Option<TermIdx>,
        fuel: i64,
        field: Sym,
    },

    // --- Naming primitives (P1 deliverable 3) ---
    //
    // `evaluate()` holds `&Interner` (immutable by design — the
    // concurrency story forbids eval-time interning), so eval-produced
    // identifiers follow the REGISTERED FALLBACK (plan §6.3):
    // Surface(Text) end-to-end. Surface(Text) is already a first-class
    // string everywhere that matters: `set_attr` effect args store it
    // as a usable string attr and RenderRule templates concatenate it
    // (the StringConcat/ToJsonString precedent; gated in
    // tests/test_prog_ir_migrated.py). Identifiers that arrive via
    // Term-JSON / seed data are interned at PARSE time (jsonio takes
    // `&mut Interner`) — that is the sound interning path.
    /// snake_case an identifier-ish string: lowercase, camel boundaries
    /// → `_`, non-alphanumeric runs → one `_`, trimmed/collapsed.
    /// Str/Surface(Text) in → Surface(Text) out; other → None (honest
    /// gap, never coerced).
    SnakeCase {
        text: TermIdx,
    },
    /// Unicode-simple lowercase fold. Str/Surface(Text) in →
    /// Surface(Text) out; other → None.
    CaseFold {
        text: TermIdx,
    },

    // --- Program synthesis (P4-A) ---
    /// `Call{name,args}` — dispatch to a registry-resident, named,
    /// parameterized Term-tree template (`DERIVED_OPERATOR_TIER_
    /// RESULTS.md` §3.2, `DERIVED_OPERATOR_TIER_SLICE1_PREREG.md`): the
    /// generic mechanism a brand-new "derived" op name dispatches
    /// through, when it has no native `TermNode` variant of its own.
    /// `name` is a `Sym` that need NOT already be interned (may be a
    /// `local_sym`-fabricated placeholder — the whole point is to avoid
    /// `DerivationRegistry`'s own `ctx.interner.lookup` requirement, see
    /// `EvalCtx::derived_ops`'s doc). Evaluation binds each `args[i]`'s
    /// evaluated Value under the registry entry's own conventional
    /// param name (`Derivation::ValueTaker`'s exact bind-then-evaluate
    /// shape, copied nearly verbatim), then evaluates the entry's own
    /// template `TermIdx` — which must already be a node in the SAME
    /// arena this `evaluate()` call is running against (the
    /// `filter_templates_by_size`/`map_templates_by_size` template-pool
    /// precedent: built once, referenced many times, never a foreign
    /// arena). No registered entry for `name` (or no registry present
    /// at all) → `Value::None`, never a panic.
    Call {
        name: Sym,
        args: Vec<TermIdx>,
    },

    /// `SynthEnumerate` — the bottom-up enumerative synthesizer
    /// (faithful port of `domains/generator.py::synthesize`, unguided
    /// path): size/MDL-ordered enumeration over a caller-declared op
    /// inventory, observational-equivalence pruning, saturation halt.
    /// `examples` evaluates to rows of `Dict{inputs: Dict, output}`;
    /// `ops`/`consts` optionally declare the primitive inventory and
    /// literal leaves. Budgets are COUNTS (in-frame integers, no wall
    /// clock): `max_size` (≤0 → 9), `max_candidates` (≤0 → 200_000 —
    /// replaces generator.py's `timeout_s`), `saturate_k` (≤0 → 3).
    /// Output `Dict{found, term (Term-JSON Surface string), term_str,
    /// size, tested, distinct, pruned_equiv, inadmissible, saturated,
    /// halt_reason}`; `field` selects one key (the ShapeDecode
    /// selector convention). PURE: no substrate mutation — engine in
    /// `synth_enumerate.rs`, this arm is a one-line handoff.
    ///
    /// `exclude` (Q1, the P7-B repair lever) evaluates to a list of
    /// Term-JSON strings — candidates already REFUTED by a caller
    /// (e.g. a repair loop's held-out check). Each excluded term's
    /// observational SIGNATURE (over these same `examples`) is
    /// pre-seeded into the equivalence-pruning set before search
    /// begins, so no later candidate with the SAME behaviour — even a
    /// syntactically different one, even an auto-appended constant
    /// that would otherwise resurrect it — can ever be proposed again.
    /// A malformed/unparseable exclude entry (references an unknown
    /// variable, uses an op outside this call's own inventory, bad
    /// JSON) is skipped, not fatal — `exclude` is a soft refutation
    /// hint, not part of the spec contract.
    ///
    /// `derived_ops` (`DERIVED_OPERATOR_TIER_RESULTS.md` §3.3(b),
    /// build-A slice) evaluates to a list of Term-JSON REGISTRY-ENTRY
    /// strings (not bare Terms) — `{"name", "params":[{"name","pool"}],
    /// "extra_cost", "template"}` — each declaring one `Call`-dispatched
    /// derived op. `ops` (above) may then name a `derived_ops` entry
    /// exactly like any native op name; unrecognized/malformed entries
    /// are skipped, never fatal — the same soft-hint discipline as
    /// `exclude`. Only entries whose params are ALL `"general"` (arity
    /// 1-3) or ALL `"list"` (arity 1-2) are usable this slice (build-A's
    /// own narrow fallback, §4) — a mixed-pool shape is silently
    /// unusable (not an error) until build (B) exists.
    SynthEnumerate {
        examples: TermIdx,
        ops: Option<TermIdx>,
        consts: Option<TermIdx>,
        exclude: Option<TermIdx>,
        derived_ops: Option<TermIdx>,
        /// PROGRAM_SYNTHESIS_MODSQRT_SCOPED_FIX: an optional list of op
        /// NAMES (evaluates like `ops`/`consts` — a `Lit` of strings, or
        /// `None`/absent) to strip from whichever `op_list` this call
        /// would otherwise use — the TYPED DEFAULT when `ops` is absent,
        /// or the caller's own explicit `ops` list when given. Applied as
        /// a post-filter at the single point both converge
        /// (`eval_synth_enumerate`'s `op_list` construction), so it is
        /// call-site-scoped rather than a second typed-default table: a
        /// caller that never sets this field is byte-unchanged (empty
        /// filter). Mirrors `exclude`'s existing "soft hint, never part
        /// of the spec contract, unrecognized names silently skipped"
        /// discipline — this is the SAME idiom for op names instead of
        /// candidate terms.
        exclude_ops: Option<TermIdx>,
        max_size: i64,
        max_candidates: i64,
        saturate_k: i64,
        field: Sym,
    },

    /// Integer-only relational Pareto comparison over graph-held value nodes.
    /// Candidate/alternative, dimension count, edge labels, and attribute
    /// labels remain graph-authored inputs; this primitive only performs the
    /// bounded vector join that a nested Filter/Exists tree otherwise repeats
    /// for every candidate pair. Returns false on incomplete, unverified, or
    /// non-integer coordinates. A dimension is shared exactly when both value
    /// nodes have no `measure_edge` and equal `dimension_key`, or their
    /// `measure_edge` neighbourhoods intersect.
    ParetoDominates {
        candidate: TermIdx,
        alternative: TermIdx,
        dimension_count: TermIdx,
        value_edge: Sym,
        measure_edge: Sym,
        dimension_key: Sym,
        verified_key: Sym,
        signed_value_key: Sym,
    },
    /// Compact graph-native learned two-slice future-manifold projection.
    FutureManifoldProjection {
        episode: TermIdx,
        policy: TermIdx,
        source: TermIdx,
        addition: Option<TermIdx>,
        field: Sym,
    },
    /// Set-valued minimum-sufficient arbitration over projected candidates.
    /// `audit_snapshot` returns counts in candidate, unestablished,
    /// infeasible, feasible, minimal, selected, withheld-minimal and tie order.
    FutureManifoldSelection {
        episode: TermIdx,
        policy: TermIdx,
        candidates: TermIdx,
        field: Sym,
        snapshot_field: Sym,
    },

    /// `LogQuantum` — the integer-observable LOG-QUANTUM EMITTER
    /// (`drafts/log_quantum/LOG_QUANTUM_PREREG.md`), the substrate's own
    /// `log_scaled_proprioception` lever (`seeds/log_graph_law.json`,
    /// "a log sensor on a log world reads linearly") made a primitive. It reads
    /// a CONTINUOUS log-domain quantity `x` (log-odds, log-weight, log-prior, or
    /// a raw linear value to be logged) and emits the INTEGER log-coordinate
    /// `q = round(log_a(x) / Δ)` — the general form of `scale_pow2_once`'s
    /// fixed base-2 case (where the additive `k` in log₂ IS the quantum), now
    /// with arbitrary base `a` and step `Δ`.
    ///
    /// WELL-FORMED BY CONSTRUCTION (the H-L1 crux). `q` is written back through
    /// `set_coord` as a `Value::Int`, so it lands on the integer lattice that
    /// `coord_ints` accepts; the frame stays integer. The base `a` and
    /// resolution `Δ` are NOT coordinates — they ride as INTENSIONAL PARAMS on
    /// this Term (rationals `a = base_num/base_den`, `Δ = delta_num/delta_den`,
    /// exactly the posture `DimensionGenerator`'s `matrix`/`offset` use), a
    /// relation held in `Hom(frame, invariant-frame)`, APPLIED ON READ, never
    /// stored in a coordinate slot. The only float is the transient cross-frame
    /// render `ln(x)/(ln(a)·Δ)` computed in the map and immediately rounded —
    /// CLAUDE.md's "continuity is intensional; the observable is the stepped
    /// integer rendering; pinned only to observational resolution (MDL)".
    ///
    /// A DIFFERENCE IS A LOG-RATIO. Quantities related by a multiplicative
    /// factor `f` emit quanta differing by the constant integer
    /// `round(log_a(f)/Δ)`, so a population differing by a per-frame
    /// multiplicative scale becomes, after emission, integer frames differing by
    /// a per-frame additive log-offset — the exact shape `RatioInduce`/`scale2`
    /// consume, feeding the ratio-induction ladder with ZERO new dispatch arm.
    ///
    /// `population` evaluates to an outer collection of frames, each an inner
    /// collection of `[pred, coord, …, val]` relation tuples. For every relation
    /// the slot `value_slot` (read via `as_f64` — `Int`/`Float`/`Rational`, the
    /// rational→float step there being the named cross-frame boundary) is
    /// REPLACED by its integer log-quantum; every other slot is untouched. When
    /// `raw` is true, `x` is a raw LINEAR value mapped through the log; when
    /// false, `x` is ALREADY a natural-log-domain quantity and the emitter only
    /// rebases + requantizes it onto the integer log axis (the `frame.py`
    /// `_log_weights` case). A non-positive `x` under `raw` floors to `ln(1e-9)`
    /// exactly as `frame.py::_log_weights` does. `base_num == 0` selects base e
    /// (natural-log sentinel); otherwise `a = base_num/base_den` with `a > 1`.
    /// A `Δ <= 0`, an out-of-range `value_slot`, or an invalid base makes the op
    /// inapplicable and returns the population UNCHANGED (a graceful skip, never
    /// a float written in-frame). Output is the population with the `value_slot`
    /// column quantized to `Int`; `field` (accepted for wiring symmetry) instead
    /// selects from a diagnostic Dict (`quantized`/`n_frames`/`n_rels`/
    /// `value_slot`/`usable`). See `shape_decode::eval_log_quantum`.
    LogQuantum {
        population: TermIdx,
        value_slot: i64,
        base_num: i64,
        base_den: i64,
        delta_num: i64,
        delta_den: i64,
        raw: bool,
        field: Sym,
    },
}

/// Arena for a Term tree. Childless to outside callers — construction
/// goes through `add`, evaluation through `evaluate`. One arena per
/// substrate is the typical pattern; multiple arenas are fine as long
/// as Sym handles aren't crossed.
pub struct TermArena {
    pub nodes: Vec<TermNode>,
}

impl TermArena {
    pub fn new() -> Self {
        Self { nodes: Vec::new() }
    }

    pub fn add(&mut self, node: TermNode) -> TermIdx {
        let idx = TermIdx(self.nodes.len() as u32);
        self.nodes.push(node);
        idx
    }

    pub fn get(&self, idx: TermIdx) -> &TermNode {
        &self.nodes[idx.0 as usize]
    }

    pub fn len(&self) -> usize {
        self.nodes.len()
    }

    pub fn is_empty(&self) -> bool {
        self.nodes.is_empty()
    }
}

impl Default for TermArena {
    fn default() -> Self {
        Self::new()
    }
}

// --- Environment: variable bindings ---

/// Variable env. SmallVec since envs are typically tiny (1–4 bindings
/// during a Filter scan); linear search from the back gives the
/// most-recent binding for free, which matches lexical-scope semantics.
pub type Env = SmallVec<[(Sym, Value); 8]>;

/// Look up the most recent binding for `name`.
pub fn env_get(env: &Env, name: Sym) -> Option<&Value> {
    env.iter().rev().find(|(k, _)| *k == name).map(|(_, v)| v)
}

// --- Evaluation context ---

/// Optional per-step cache for `Neighbours` / `InNeighbours` / `Filter`.
/// The Python version flips `_eval_cache` on the graph; we keep it
/// scoped to the EvalCtx so an evaluation that opens a cache can't
/// affect concurrent unrelated evaluations.
#[derive(Default)]
pub struct EvalCache {
    /// (node, edge_type, "in" or "out") -> set Value (FrozenSet).
    pub neighbours: FxHashMap<(NodeID, Sym, bool), Value>,
    /// (term_idx, free-var bindings) -> set Value, for Filter.
    pub filter: FxHashMap<(TermIdx, SmallVec<[(Sym, Value); 4]>), Value>,
    /// `Holds(concept, node, node2)` -> Value. Same key shape as the
    /// Holds variant; Some(node) / Some(node2) participate in the key.
    /// Cleared by the substrate on any mutation (the substrate's
    /// `any_mutation` flag was added for differential rule firing —
    /// memoization piggybacks on the same invalidation primitive).
    pub holds: FxHashMap<(Sym, Option<NodeID>, Option<NodeID>), Value>,
    /// Semantic SD-ladder memo. The key deliberately excludes the requested
    /// output field: ShapeDecode / TransformDecode / DimInfer / GenInfer each
    /// compute one report and callers commonly read several fields from it.
    /// Graph mutation clears this with the other EvalCache families.
    sd_ops: FxHashMap<SdCacheKey, Value>,
}

#[derive(Clone, Debug, Eq, Hash, PartialEq)]
struct SdCacheKey {
    tag: u8,
    values: Vec<Value>,
    scalars: Vec<i64>,
    typed_fingerprints: Vec<(Sym, u64)>,
}

impl EvalCache {
    pub fn clear_traversal(&mut self) {
        self.neighbours.clear();
        self.filter.clear();
        self.holds.clear();
    }

    pub fn clear_graph_dependent(&mut self) {
        self.clear_traversal();
        self.sd_ops.clear();
    }

    pub(crate) fn clear_sd_ops(&mut self) {
        self.sd_ops.clear();
    }
}

fn sd_cache_key(
    tag: u8,
    values: &[Value],
    scalars: &[i64],
    syms: &[Sym],
    graph: &TypedGraph,
) -> SdCacheKey {
    use std::hash::{Hash, Hasher};

    let typed_fingerprints = syms
        .iter()
        .map(|sym| {
            // SD's implicit graph dependency is precisely the typed codebook
            // read by load_parts/load_generators. Hash that projection, not
            // the whole graph: unrelated cognitive writes do not invalidate
            // sibling field projections, while any codebook mutation does.
            let mut hasher = rustc_hash::FxHasher::default();
            for nid in graph.nodes_of_type(*sym) {
                nid.hash(&mut hasher);
                let node = graph.node(nid);
                for (key, value) in &node.attrs {
                    key.hash(&mut hasher);
                    value.hash(&mut hasher);
                }
            }
            (*sym, hasher.finish())
        })
        .collect();
    SdCacheKey {
        tag,
        values: values.to_vec(),
        scalars: scalars.to_vec(),
        typed_fingerprints,
    }
}

/// Concept registry — the Holds Term looks up `concept: Sym` here for
/// its defining Term. Replaces the Python `env['_resolve_concept']`
/// callable. The agent populates this before evaluating any Term that
/// uses Holds.
pub type ConceptResolver = FxHashMap<Sym, TermIdx>;

/// Derivation registry — maps a *derivable variant kind* name (e.g.
/// "Bearing", "Magnitude", "Lte", "Sum", "Count") to its graph-resident
/// derivation. The KERNEL primitives from KERNEL_AUDIT.md (Plus, Times,
/// Lt, Atan2, etc.) are NOT entries here — they're irreducible by
/// construction. Only DERIVABLE variants (reducible compositions over
/// the kernel) get derivations.
///
/// Dynamic by design: the agent installs / replaces / removes entries
/// between evaluations the same way it manages Concepts, Microtheories,
/// and Frames. An empty registry = full native dispatch.
pub type DerivationRegistry = FxHashMap<Sym, Derivation>;

/// Two derivation shapes — the variant's *arguments* (value-takers) vs.
/// its *Term-tree fields* (body-takers) determine which.
#[derive(Clone, Debug)]
pub enum Derivation {
    /// **Value-taker**: the variant's arguments evaluate to Values. The
    /// derivation is a TermIdx (graph-resident Term-tree) that runs with
    /// those Values bound under the variant's conventional arg names
    /// (e.g. for Gt: "a" + "b"; for Bearing: "arg"). Examples: Lte, Gt,
    /// Gte, Bearing, Magnitude, Rotate, AngleBetween, In, Intersect,
    /// Difference, U16LE, U32LE, U64LE.
    ValueTaker(TermIdx),
    /// **Body-taker**: one or more of the variant's fields is a Term
    /// (not a Value) — e.g. Sum's `value` is "compute THIS Term per
    /// element". The derivation expands the variant call into a kernel
    /// Term-tree where the user's Term-fields are spliced in as
    /// subtrees. Today the splice procedure is encoded per-variant in
    /// Rust (see `expand_count`, `expand_sum`, …). The next iteration
    /// stores the expansion as a graph-resident template Term with
    /// splice-Var sentinels, so the agent can rewrite it. Examples:
    /// Count, Sum, Prod, MinOver, MaxOver, Argmax, Argmin, Exists,
    /// MapSet, Join, Bytes, Lines, LEB128, BitsAtAll, BitsWriteAll,
    /// ExpGolombDecode, ExpGolombDecodeSigned, ExpGolombEncode,
    /// ExpGolombEncodeSigned.
    BodyTaker,
}

/// Which pool a `Call`-dispatched derived op's parameter draws from
/// (`DERIVED_OPERATOR_TIER_RESULTS.md` §3.1's own closed two-pool
/// taxonomy — `General` mirrors `synth_enumerate.rs`'s `by_size`,
/// `List` mirrors its `list_by_size`). Build-A's own arity/pool →
/// `OpKind` inference (`synth_enumerate.rs`) only recognizes an entry
/// whose params are ALL `General` (arity 1-3) or ALL `List`
/// (arity 1-2) — a mixed-pool shape (`JoinListSep`'s own) is build (B)
/// territory and is correctly left unusable here, not built.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum DerivedOpPool {
    General,
    List,
}

/// One derived-operator registry entry — `DERIVED_OPERATOR_TIER_
/// RESULTS.md` §3.1/§3.2: a named, parameterized Term-tree template a
/// `Call{name,args}` node dispatches to. `params` is ordered and
/// positional — `params[i]`'s Sym is the template-local `Var` name
/// `args[i]`'s evaluated Value binds under (the pool tag travels with
/// it only for `synth_enumerate.rs`'s own `op_list`/build-A arity
/// inference; `Call`'s own evaluation never reads the pool). `body` is
/// already a node in the SAME arena the whole search/evaluation is
/// running against (never a separate/foreign arena — the
/// `filter_templates_by_size`/`map_templates_by_size` template-pool
/// precedent).
#[derive(Clone, Debug)]
pub struct DerivedOpDef {
    pub params: Vec<(Sym, DerivedOpPool)>,
    pub body: TermIdx,
    /// The DATA-driven generalization of `list_unary_extra_cost`/
    /// `list_binary_extra_cost`'s own hand-authored Rust tables — read
    /// only by a derived op reached through `OpKind::ListUnary`/
    /// `ListBinary` (the two existing shapes that already have an
    /// extra-cost concept). `OpKind::Unary`/`Binary`/`Ternary` have NO
    /// such concept upstream (every native entry there is a single-node
    /// wrap, no hidden scaffolding), so a general-pool derived op's own
    /// `extra_cost` is honestly unused/unconsulted this slice — a named,
    /// not hidden, build-A limitation.
    pub extra_cost: usize,
}

/// Registry of derived operators for ONE `SynthEnumerate` call, keyed
/// by the op's own name Sym (real-interned if the name happens to
/// already exist, else `local_sym`-fabricated — never
/// `ctx.interner.lookup`, `DerivationRegistry`'s own §2.2-documented
/// gap). Reaches `evaluate()` only via `EvalCtx::derived_ops`; only
/// ever populated by `synth_enumerate::eval_synth_enumerate`, and only
/// for the scope of its own search (see `with_derived_ops`) — never
/// touched by Python/PyO3.
pub type DerivedOpRegistry = FxHashMap<Sym, DerivedOpDef>;

/// Evaluator state passed through every recursive call. Holds the
/// Argument attribution for `DimInfer`, carried BY THE CALL rather than
/// published to a process-global side channel.
///
/// # Why this exists
///
/// The distinct-argument measurement (`VISION_DIM_INFER_ARGS_PREREG.md`) was
/// originally recorded into `scale_audit`'s process-global counters: a caller
/// flipped a global enable, ran decodes, and snapshotted globals. That reading
/// is only correct if nothing else in the process decodes during the window,
/// which is not a property any caller can guarantee — and in the test harness
/// it is routinely false, because sibling tests run decodes concurrently and
/// increment the same counters. The measurement was therefore silently
/// contaminated rather than wrong-and-loud.
///
/// A witness attached to the evaluation context cannot be contaminated: two
/// concurrent decodes hold two contexts, and each records only what its own
/// call did. This is the same shape as the provenance witness in the boundary
/// theory — attribution retained through the operation instead of in shared
/// state — and it makes the failure mode structurally impossible rather than
/// merely detectable.
#[derive(Debug, Default, Clone, PartialEq)]
pub struct DimInferWitness {
    /// Exact canonical ORDERED argument encodings, one per invocation, in
    /// invocation order. Attempt order genuinely affects the answer, so this
    /// is the complete determinant set.
    pub ordered: Vec<Vec<u8>>,
    /// The UNORDERED (canonically sorted) encodings. Codebook load order is a
    /// graph-iteration fact that can churn with no semantic change, so this is
    /// the lower bound on distinctness.
    pub unordered: Vec<Vec<u8>>,
}

impl DimInferWitness {
    /// Invocations that reached the recording site.
    pub fn calls(&self) -> usize {
        self.ordered.len()
    }

    /// Distinct ordered encodings. Exact, not hashed: a hash collision would
    /// UNDER-count distinctness and bias the reading toward "re-derivation",
    /// which is the more interesting answer and therefore the one that must
    /// not be reachable by accident.
    pub fn distinct_ordered(&self) -> usize {
        let mut seen: Vec<&Vec<u8>> = Vec::new();
        for e in &self.ordered {
            if !seen.iter().any(|s| *s == e) {
                seen.push(e);
            }
        }
        seen.len()
    }

    /// Distinct unordered encodings — the lower bound.
    pub fn distinct_unordered(&self) -> usize {
        let mut seen: Vec<&Vec<u8>> = Vec::new();
        for e in &self.unordered {
            if !seen.iter().any(|s| *s == e) {
                seen.push(e);
            }
        }
        seen.len()
    }

    pub fn record(&mut self, ordered: Vec<u8>, unordered: Vec<u8>) {
        self.ordered.push(ordered);
        self.unordered.push(unordered);
    }
}

/// graph + interner + optional cache + concept resolver + a depth
/// guard (matches Python's `_holds_depth`).
pub struct EvalCtx<'a> {
    pub graph: &'a TypedGraph,
    pub interner: &'a Interner,
    pub cache: Option<&'a mut EvalCache>,
    pub concepts: Option<&'a ConceptResolver>,
    pub holds_depth: u32,
    /// Stack of concept Syms currently being evaluated by Holds. Used
    /// for cycle detection: if a Holds(concept, _) call re-enters the
    /// same concept already on the stack, the call returns Value::None
    /// instead of recursing forever. Distinct from `holds_depth`,
    /// which is a per-call recursion budget — visited-set catches
    /// genuine cycles (Arrhenius_equation → rate_law → Arrhenius_equation,
    /// or a concept whose body Holds-references itself) precisely,
    /// even when each Holds expansion has fanout > 1 (which would
    /// otherwise blow up exponentially before the depth budget trips).
    pub holds_stack: Vec<Sym>,
    /// Phase 7 observability: optional Counters target. Every cache
    /// probe (`Neighbours` / `Filter`) tallies hit/miss when present;
    /// the substrate wires this in for the top-level eval entry.
    pub counters: Option<&'a mut Counters>,
    /// Optional registry of graph-resident derivations for derivable
    /// variants (see DerivationRegistry doc). When present, derivable
    /// variants whose kind has a registered derivation dispatch via it
    /// instead of their native match arm. Kernel (irreducible) variants
    /// ignore this field — their dispatch is fixed.
    pub derivations: Option<&'a DerivationRegistry>,
    /// `active_shape_target` from the substrate — when Some, derivation
    /// dispatch tests the registered derivation's Shape against this
    /// target. Incompatible derivations are skipped (fall back to
    /// native kernel dispatch); the counter bumps. Implements
    /// `shape_mismatch_prunes_negative_problem_space` at the
    /// derivation-dispatch layer (function_shape Mt).
    pub shape_target: Option<crate::shape::Shape>,
    /// `cached_shape_makes_classification_constant_time` — the
    /// substrate's ShapeCache, threaded through the dispatch path so
    /// the per-call assess_shape walk hits the cache instead of
    /// walking. None = uncached path (slower; safe). When threaded,
    /// the dispatch shape check is O(1) on cache hit.
    pub shape_cache: Option<&'a mut crate::shape::ShapeCache>,
    /// Read-only handle onto the substrate's attached shared-memory
    /// framebuffers (`framebuffer::FbHandle`), threaded in ONLY by
    /// callers that build an `EvalCtx` with `.with_framebuffers(...)`.
    /// Backs the `FbFrameSeq` Term — a cheap "has this framebuffer's
    /// frame_seq advanced" oracle. `None` (the default, same posture
    /// as `derivations`/`shape_cache`) means `FbFrameSeq` evaluates to
    /// `Value::None`; see `TermNode::FbFrameSeq`'s doc for exactly
    /// which call sites currently opt in (today: none of the rule-
    /// engine's `where`-clause evaluation paths do — only a caller
    /// constructing `EvalCtx` directly, e.g. a test or a future
    /// primitive, can exercise it).
    pub framebuffers: Option<&'a rustc_hash::FxHashMap<u32, crate::framebuffer::FbHandle>>,
    /// Optional per-call `DimInfer` argument attribution. `None` (the default)
    /// records nothing and costs nothing. When `Some`, the decode appends its
    /// own arguments here, so the reading belongs to this evaluation and no
    /// concurrent evaluation can contribute to it.
    pub dim_infer_witness: Option<&'a mut DimInferWitness>,
    /// Optional registry for `Call{name,args}` dispatch
    /// (`DERIVED_OPERATOR_TIER_SLICE1_PREREG.md`'s own "design decisions"
    /// section). `Arc`, NOT a borrowed `&'a DerivedOpRegistry` — a
    /// registry is built fresh, locally, inside ONE
    /// `SynthEnumerate` call and cannot satisfy `EvalCtx`'s own shared
    /// `'a` (fixed by whatever ancestor call originally constructed
    /// `ctx`, generally far outliving one search); `Arc` carries no
    /// borrowed lifetime, so this field needs no lifetime parameter of
    /// its own and every other field/caller is untouched. `None` (the
    /// default, same posture as `derivations`/`shape_cache`) means
    /// `Call` evaluates to `Value::None`. Set ONLY by
    /// `synth_enumerate::eval_synth_enumerate`, for the scope of its
    /// own search, via the `with_derived_ops` scope guard — never
    /// PyO3-exposed, never Python-settable (deliberately: see the
    /// PREREG's own §"design decisions", which rejects a
    /// Python-facing field for this exact shape).
    pub derived_ops: Option<Arc<DerivedOpRegistry>>,
}

impl<'a> EvalCtx<'a> {
    pub fn new(graph: &'a TypedGraph, interner: &'a Interner) -> Self {
        Self {
            graph,
            interner,
            cache: None,
            concepts: None,
            holds_depth: 0,
            holds_stack: Vec::new(),
            counters: None,
            derivations: None,
            shape_target: None,
            shape_cache: None,
            derived_ops: None,
            framebuffers: None,
            dim_infer_witness: None,
        }
    }

    /// Attach a `DimInferWitness` so this evaluation records its own
    /// `DimInfer` arguments instead of relying on process-global counters.
    pub fn with_dim_infer_witness(mut self, w: &'a mut DimInferWitness) -> Self {
        self.dim_infer_witness = Some(w);
        self
    }

    pub fn with_framebuffers(
        mut self,
        fbs: &'a rustc_hash::FxHashMap<u32, crate::framebuffer::FbHandle>,
    ) -> Self {
        self.framebuffers = Some(fbs);
        self
    }

    pub fn with_shape_cache(mut self, cache: &'a mut crate::shape::ShapeCache) -> Self {
        self.shape_cache = Some(cache);
        self
    }

    pub fn with_shape_target(mut self, target: crate::shape::Shape) -> Self {
        self.shape_target = Some(target);
        self
    }

    pub fn with_cache(mut self, cache: &'a mut EvalCache) -> Self {
        self.cache = Some(cache);
        self
    }

    pub fn with_concepts(mut self, concepts: &'a ConceptResolver) -> Self {
        self.concepts = Some(concepts);
        self
    }

    pub fn with_counters(mut self, counters: &'a mut Counters) -> Self {
        self.counters = Some(counters);
        self
    }

    pub fn with_derivations(mut self, derivations: &'a DerivationRegistry) -> Self {
        self.derivations = Some(derivations);
        self
    }
}

// --- Evaluator ---

/// Look up a value-taker derivation TermIdx for a derivable variant.
/// Returns `None` when no DerivationRegistry is attached, the variant
/// kind isn't interned, no entry is registered, or the entry is a
/// body-taker (which doesn't use this dispatch path). See DerivationRegistry doc.
#[inline]
fn lookup_value_taker_def(
    ctx: &mut EvalCtx,
    arena: &TermArena,
    kind_name: &str,
) -> Option<TermIdx> {
    let kind_sym = ctx.interner.lookup(kind_name)?;
    let def = match ctx.derivations?.get(&kind_sym)? {
        Derivation::ValueTaker(def) => *def,
        Derivation::BodyTaker => return None,
    };
    // shape_mismatch_prunes_negative_problem_space: if a target shape
    // is active and the registered derivation's Shape is incompatible,
    // skip the derivation; the caller falls back to native kernel
    // dispatch (semantically equivalent — derivations are kernel-
    // expansion-equivalent compositions). The counter bumps so callers
    // can measure the multiplicative savings the pruning earned.
    if let Some(target) = ctx.shape_target {
        let def_shape = match ctx.shape_cache.as_deref_mut() {
            Some(cache) => cache.assess_and_cache(def, arena),
            None => crate::shape::assess_shape(def, arena),
        };
        if !crate::shape::shapes_compatible(&def_shape, &target) {
            if let Some(c) = ctx.counters.as_deref_mut() {
                c.on_derivation_shape_pruned();
            }
            return None;
        }
    }
    Some(def)
}

/// Check whether a body-taker derivation is registered for `kind_name`.
/// If yes, the variant's eval arm hands off to its `expand_X` helper
/// which synthesises a kernel Term in a tmp arena, then evaluates it.
#[inline]
fn is_body_taker_registered(ctx: &EvalCtx, kind_name: &str) -> bool {
    let Some(kind_sym) = ctx.interner.lookup(kind_name) else {
        return false;
    };
    matches!(
        ctx.derivations.and_then(|d| d.get(&kind_sym)),
        Some(Derivation::BodyTaker)
    )
}

/// Deep-copy a Term subtree from `src` arena into `dst` arena, returning
/// the new root TermIdx. Used by body-taker expansions to splice the
/// user's source/value/body sub-terms into the synthesised kernel form.
/// Recursive but bounded by the arena's tree depth — same shape as
/// `children()` in this file, just allocates instead of inspecting.
fn copy_subtree(src: &TermArena, dst: &mut TermArena, idx: TermIdx) -> TermIdx {
    let node = src.get(idx).clone();
    let copied = match node {
        // Leaves — no children to recurse on.
        TermNode::Var { .. }
        | TermNode::Lit { .. }
        | TermNode::Slot { .. }
        | TermNode::Label { .. }
        | TermNode::Surface { .. } => node,

        // Single-child Terms.
        TermNode::TypeOf { node } => TermNode::TypeOf {
            node: copy_subtree(src, dst, node),
        },
        TermNode::Attr { node, key } => TermNode::Attr {
            node: copy_subtree(src, dst, node),
            key,
        },
        TermNode::UseTool { tool, args } => TermNode::UseTool {
            tool,
            args: args.iter().map(|a| copy_subtree(src, dst, *a)).collect(),
        },
        TermNode::ReachableFrom {
            node,
            edge_type,
            any_type,
        } => TermNode::ReachableFrom {
            node: copy_subtree(src, dst, node),
            edge_type,
            any_type,
        },

        TermNode::Neighbours {
            node,
            edge_type,
            any_type,
        } => TermNode::Neighbours {
            node: copy_subtree(src, dst, node),
            edge_type,
            any_type,
        },
        TermNode::SlideNeighbours {
            cell,
            slide,
            ground,
        } => TermNode::SlideNeighbours {
            cell: copy_subtree(src, dst, cell),
            slide: copy_subtree(src, dst, slide),
            ground: copy_subtree(src, dst, ground),
        },
        TermNode::InNeighbours {
            node,
            edge_type,
            any_type,
        } => TermNode::InNeighbours {
            node: copy_subtree(src, dst, node),
            edge_type,
            any_type,
        },
        TermNode::MapNeighbours {
            source,
            edge_type,
            any_type,
        } => TermNode::MapNeighbours {
            source: copy_subtree(src, dst, source),
            edge_type,
            any_type,
        },
        TermNode::Edges {
            node,
            edge_type,
            any_type,
        } => TermNode::Edges {
            node: copy_subtree(src, dst, node),
            edge_type,
            any_type,
        },
        TermNode::EdgeAttr { edge, key } => TermNode::EdgeAttr {
            edge: copy_subtree(src, dst, edge),
            key,
        },
        TermNode::NodesWhere {
            node_type,
            attr_key,
            value,
        } => TermNode::NodesWhere {
            node_type,
            attr_key,
            value: copy_subtree(src, dst, value),
        },
        TermNode::NodesOfType { node_type } => TermNode::NodesOfType { node_type },
        TermNode::AntiUnify { values, wild } => TermNode::AntiUnify {
            values: copy_subtree(src, dst, values),
            wild,
        },
        TermNode::FixedCount { pattern, wild } => TermNode::FixedCount {
            pattern: copy_subtree(src, dst, pattern),
            wild,
        },
        TermNode::Covers {
            pattern,
            instance,
            wild,
        } => TermNode::Covers {
            pattern: copy_subtree(src, dst, pattern),
            instance: copy_subtree(src, dst, instance),
            wild,
        },
        TermNode::CoversOpen {
            pattern,
            instance,
            wild,
        } => TermNode::CoversOpen {
            pattern: copy_subtree(src, dst, pattern),
            instance: copy_subtree(src, dst, instance),
            wild,
        },
        TermNode::AntiUnifyWitness { values, wild } => TermNode::AntiUnifyWitness {
            values: copy_subtree(src, dst, values),
            wild,
        },
        TermNode::Substitute {
            template,
            sigma,
            wild,
        } => TermNode::Substitute {
            template: copy_subtree(src, dst, template),
            sigma: copy_subtree(src, dst, sigma),
            wild,
        },
        TermNode::Unify { values, wild } => TermNode::Unify {
            values: copy_subtree(src, dst, values),
            wild,
        },
        TermNode::StructSim { a, b, wild } => TermNode::StructSim {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
            wild,
        },
        TermNode::ShapeDecode {
            goal,
            codebook_type,
            exclude,
            codebook_scope,
            beam,
            max_steps,
            cand_k,
            budget,
            field,
            wild,
            wild_objects,
        } => TermNode::ShapeDecode {
            goal: copy_subtree(src, dst, goal),
            codebook_type,
            exclude: exclude.map(|e| copy_subtree(src, dst, e)),
            codebook_scope: codebook_scope.map(|e| copy_subtree(src, dst, e)),
            beam,
            max_steps,
            cand_k,
            budget,
            field,
            wild,
            wild_objects,
        },
        TermNode::MotorCompose {
            episode,
            policy,
            candidate,
        } => TermNode::MotorCompose {
            episode: copy_subtree(src, dst, episode),
            policy: copy_subtree(src, dst, policy),
            candidate: copy_subtree(src, dst, candidate),
        },
        TermNode::FutureManifoldProjection {
            episode,
            policy,
            source,
            addition,
            field,
        } => TermNode::FutureManifoldProjection {
            episode: copy_subtree(src, dst, episode),
            policy: copy_subtree(src, dst, policy),
            source: copy_subtree(src, dst, source),
            addition: addition.map(|a| copy_subtree(src, dst, a)),
            field,
        },
        TermNode::FutureManifoldSelection {
            episode,
            policy,
            candidates,
            field,
            snapshot_field,
        } => TermNode::FutureManifoldSelection {
            episode: copy_subtree(src, dst, episode),
            policy: copy_subtree(src, dst, policy),
            candidates: copy_subtree(src, dst, candidates),
            field,
            snapshot_field,
        },
        TermNode::LogQuantum {
            population,
            value_slot,
            base_num,
            base_den,
            delta_num,
            delta_den,
            raw,
            field,
        } => TermNode::LogQuantum {
            population: copy_subtree(src, dst, population),
            value_slot,
            base_num,
            base_den,
            delta_num,
            delta_den,
            raw,
            field,
        },
        TermNode::TransformDecode {
            goal,
            codebook_type,
            exclude,
            max_dims,
            field,
        } => TermNode::TransformDecode {
            goal: copy_subtree(src, dst, goal),
            codebook_type,
            exclude: exclude.map(|e| copy_subtree(src, dst, e)),
            max_dims,
            field,
        },
        TermNode::NetForward { assemblage, inputs } => TermNode::NetForward {
            assemblage: copy_subtree(src, dst, assemblage),
            inputs: copy_subtree(src, dst, inputs),
        },
        TermNode::DimInfer {
            goal,
            codebook_type,
            exclude,
            generator_type,
            max_dims,
            field,
        } => TermNode::DimInfer {
            goal: copy_subtree(src, dst, goal),
            codebook_type,
            exclude: exclude.map(|e| copy_subtree(src, dst, e)),
            generator_type,
            max_dims,
            field,
        },
        TermNode::GenInfer {
            goal,
            codebook_type,
            exclude,
            max_dims,
            field,
        } => TermNode::GenInfer {
            goal: copy_subtree(src, dst, goal),
            codebook_type,
            exclude: exclude.map(|e| copy_subtree(src, dst, e)),
            max_dims,
            field,
        },
        TermNode::RatioInduce {
            population,
            codebook_type,
            resolution,
            field,
        } => TermNode::RatioInduce {
            population: copy_subtree(src, dst, population),
            codebook_type,
            resolution,
            field,
        },
        TermNode::DepthInfer {
            sequence,
            codebook_type,
            max_b,
            field,
        } => TermNode::DepthInfer {
            sequence: copy_subtree(src, dst, sequence),
            codebook_type,
            max_b,
            field,
        },
        TermNode::TimeInfer {
            sequence,
            codebook_type,
            max_b,
            field,
            max_steps,
            robust,
        } => TermNode::TimeInfer {
            sequence: copy_subtree(src, dst, sequence),
            codebook_type,
            max_b,
            field,
            max_steps,
            robust,
        },
        TermNode::BlinkBridge {
            sequence,
            codebook_type,
            max_b,
            field,
        } => TermNode::BlinkBridge {
            sequence: copy_subtree(src, dst, sequence),
            codebook_type,
            max_b,
            field,
        },
        TermNode::GapAbduce {
            sequence,
            codebook_type,
            max_b,
            field,
        } => TermNode::GapAbduce {
            sequence: copy_subtree(src, dst, sequence),
            codebook_type,
            max_b,
            field,
        },
        TermNode::SupportInfer {
            sequence,
            codebook_type,
            field,
        } => TermNode::SupportInfer {
            sequence: copy_subtree(src, dst, sequence),
            codebook_type,
            field,
        },
        TermNode::MotionEnergy {
            sequence,
            height,
            width,
            field,
        } => TermNode::MotionEnergy {
            sequence: copy_subtree(src, dst, sequence),
            height,
            width,
            field,
        },
        TermNode::GapVerify {
            sequence,
            codebook_type,
            max_b,
            field,
        } => TermNode::GapVerify {
            sequence: copy_subtree(src, dst, sequence),
            codebook_type,
            max_b,
            field,
        },
        TermNode::TransferDecode { goal } => TermNode::TransferDecode {
            goal: copy_subtree(src, dst, goal),
        },
        TermNode::RecogniseShape { text } => TermNode::RecogniseShape {
            text: copy_subtree(src, dst, text),
        },
        TermNode::MetaShapeMint {
            observation,
            obs_type,
            status_value,
            wild,
            field,
        } => TermNode::MetaShapeMint {
            observation: copy_subtree(src, dst, observation),
            obs_type,
            status_value,
            wild,
            field,
        },
        TermNode::StrokeQuantize {
            points,
            segments,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            invariant_only,
            canonical_pose,
            turn_edges,
            len_edges,
            emit_residual,
            bounds,
            field,
            seg_sym,
            pose_x_sym,
            pose_y_sym,
            pose_o_sym,
            pose_s_sym,
        } => TermNode::StrokeQuantize {
            points: copy_subtree(src, dst, points),
            segments,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            invariant_only,
            canonical_pose,
            turn_edges: turn_edges.map(|e| copy_subtree(src, dst, e)),
            len_edges: len_edges.map(|e| copy_subtree(src, dst, e)),
            emit_residual,
            bounds: bounds.map(|b| copy_subtree(src, dst, b)),
            field,
            seg_sym,
            pose_x_sym,
            pose_y_sym,
            pose_o_sym,
            pose_s_sym,
        },
        TermNode::StrokeRender {
            signature,
            n_points,
            apply_pose,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            turn_edges,
            len_edges,
            bounds,
            field,
        } => TermNode::StrokeRender {
            signature: copy_subtree(src, dst, signature),
            n_points,
            apply_pose,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            turn_edges: turn_edges.map(|e| copy_subtree(src, dst, e)),
            len_edges: len_edges.map(|e| copy_subtree(src, dst, e)),
            bounds: bounds.map(|b| copy_subtree(src, dst, b)),
            field,
        },
        TermNode::SigmaLognormalGenerate {
            primitives,
            start,
            t_start,
            t_end,
            n_points,
            field,
        } => TermNode::SigmaLognormalGenerate {
            primitives: copy_subtree(src, dst, primitives),
            start: copy_subtree(src, dst, start),
            t_start,
            t_end,
            n_points,
            field,
        },
        TermNode::LookaheadValue {
            node,
            child_edge,
            score_key,
            depth,
        } => TermNode::LookaheadValue {
            node: copy_subtree(src, dst, node),
            child_edge,
            score_key,
            depth: copy_subtree(src, dst, depth),
        },
        TermNode::ScalarAttrTriples { skip_prefix } => TermNode::ScalarAttrTriples { skip_prefix },
        TermNode::AttrByName { node, name } => TermNode::AttrByName {
            node: copy_subtree(src, dst, node),
            name: copy_subtree(src, dst, name),
        },
        TermNode::Count { source } => TermNode::Count {
            source: copy_subtree(src, dst, source),
        },
        TermNode::Pick { source } => TermNode::Pick {
            source: copy_subtree(src, dst, source),
        },
        TermNode::PickUnique { source } => TermNode::PickUnique {
            source: copy_subtree(src, dst, source),
        },
        TermNode::EvalSubgraph { node } => TermNode::EvalSubgraph {
            node: copy_subtree(src, dst, node),
        },
        TermNode::Not { arg } => TermNode::Not {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Abs { arg } => TermNode::Abs {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Neg { arg } => TermNode::Neg {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Sqrt { arg } => TermNode::Sqrt {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Log { arg } => TermNode::Log {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Exp { arg } => TermNode::Exp {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Magnitude { arg } => TermNode::Magnitude {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Sin { arg } => TermNode::Sin {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Cos { arg } => TermNode::Cos {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::Bearing { arg } => TermNode::Bearing {
            arg: copy_subtree(src, dst, arg),
        },

        // n-ary items.
        TermNode::SetT { items } => TermNode::SetT {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::And { items } => TermNode::And {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::Or { items } => TermNode::Or {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::Plus { items } => TermNode::Plus {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::Times { items } => TermNode::Times {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::Min { items } => TermNode::Min {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::Max { items } => TermNode::Max {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::ArgMax { items } => TermNode::ArgMax {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::ArgMin { items } => TermNode::ArgMin {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::TrackIdentityCorrespondence {
            prev,
            cur,
            feature_key,
            category_key,
            extent_key,
            radius,
        } => TermNode::TrackIdentityCorrespondence {
            prev: copy_subtree(src, dst, prev),
            cur: copy_subtree(src, dst, cur),
            feature_key,
            category_key,
            extent_key,
            radius: copy_subtree(src, dst, radius),
        },
        TermNode::Vec_ { items } => TermNode::Vec_ {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::Cat { items } => TermNode::Cat {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::Bytes { items } => TermNode::Bytes {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::Lines { items } => TermNode::Lines {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },

        // Binary.
        TermNode::In { member, container } => TermNode::In {
            member: copy_subtree(src, dst, member),
            container: copy_subtree(src, dst, container),
        },
        TermNode::Tokenize { text } => TermNode::Tokenize {
            text: copy_subtree(src, dst, text),
        },
        TermNode::MorphHead { text } => TermNode::MorphHead {
            text: copy_subtree(src, dst, text),
        },
        TermNode::MorphTail { text } => TermNode::MorphTail {
            text: copy_subtree(src, dst, text),
        },
        TermNode::FinalToken { text } => TermNode::FinalToken {
            text: copy_subtree(src, dst, text),
        },
        TermNode::Tokenize2 { text } => TermNode::Tokenize2 {
            text: copy_subtree(src, dst, text),
        },
        TermNode::ReadFile { path } => TermNode::ReadFile {
            path: copy_subtree(src, dst, path),
        },
        TermNode::StringIndexOf { haystack, needle } => TermNode::StringIndexOf {
            haystack: copy_subtree(src, dst, haystack),
            needle: copy_subtree(src, dst, needle),
        },
        TermNode::StringSlice { s, start, end } => TermNode::StringSlice {
            s: copy_subtree(src, dst, s),
            start: copy_subtree(src, dst, start),
            end: copy_subtree(src, dst, end),
        },
        TermNode::StringConcat { parts } => TermNode::StringConcat {
            parts: parts.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        // Rung 1 Tier-1 stdlib Term ports.
        TermNode::Replace { text, old, new } => TermNode::Replace {
            text: copy_subtree(src, dst, text),
            old: copy_subtree(src, dst, old),
            new: copy_subtree(src, dst, new),
        },
        TermNode::Str { value } => TermNode::Str {
            value: copy_subtree(src, dst, value),
        },
        TermNode::Split { text, sep } => TermNode::Split {
            text: copy_subtree(src, dst, text),
            sep: copy_subtree(src, dst, sep),
        },
        TermNode::StrCount { text, sub } => TermNode::StrCount {
            text: copy_subtree(src, dst, text),
            sub: copy_subtree(src, dst, sub),
        },
        TermNode::Round { value, ndigits } => TermNode::Round {
            value: copy_subtree(src, dst, value),
            ndigits: copy_subtree(src, dst, ndigits),
        },
        TermNode::Reverse { seq } => TermNode::Reverse {
            seq: copy_subtree(src, dst, seq),
        },
        TermNode::IndexedMap {
            source,
            item_name,
            index_name,
            value,
        } => TermNode::IndexedMap {
            source: copy_subtree(src, dst, source),
            item_name,
            index_name,
            value: copy_subtree(src, dst, value),
        },
        TermNode::Capitalize { text } => TermNode::Capitalize {
            text: copy_subtree(src, dst, text),
        },
        TermNode::ParseInt { text } => TermNode::ParseInt {
            text: copy_subtree(src, dst, text),
        },
        TermNode::Slice { seq, start, stop } => TermNode::Slice {
            seq: copy_subtree(src, dst, seq),
            start: copy_subtree(src, dst, start),
            stop: copy_subtree(src, dst, stop),
        },
        TermNode::Sort { seq } => TermNode::Sort {
            seq: copy_subtree(src, dst, seq),
        },
        TermNode::DictItems { seq } => TermNode::DictItems {
            seq: copy_subtree(src, dst, seq),
        },
        TermNode::SortBy {
            source,
            var_name,
            key,
        } => TermNode::SortBy {
            source: copy_subtree(src, dst, source),
            var_name,
            key: copy_subtree(src, dst, key),
        },
        TermNode::GroupCount { seq } => TermNode::GroupCount {
            seq: copy_subtree(src, dst, seq),
        },
        TermNode::DictMerge { a, b } => TermNode::DictMerge {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::ZipWith {
            a,
            b,
            a_name,
            b_name,
            value,
        } => TermNode::ZipWith {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
            a_name,
            b_name,
            value: copy_subtree(src, dst, value),
        },
        TermNode::Verify {
            term,
            env,
            expected,
        } => TermNode::Verify {
            term: copy_subtree(src, dst, term),
            env: copy_subtree(src, dst, env),
            expected: copy_subtree(src, dst, expected),
        },
        TermNode::MkDict { items } => TermNode::MkDict {
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::ToJsonString { value } => TermNode::ToJsonString {
            value: copy_subtree(src, dst, value),
        },
        TermNode::FromJsonString { text } => TermNode::FromJsonString {
            text: copy_subtree(src, dst, text),
        },
        TermNode::ShiftThresholdLits { tree, shift } => TermNode::ShiftThresholdLits {
            tree: copy_subtree(src, dst, tree),
            shift: copy_subtree(src, dst, shift),
        },
        TermNode::DictGet { dict, key } => TermNode::DictGet {
            dict: copy_subtree(src, dst, dict),
            key: copy_subtree(src, dst, key),
        },
        TermNode::RewriteTreeNodes {
            tree,
            type_filter,
            field,
            value_map,
        } => TermNode::RewriteTreeNodes {
            tree: copy_subtree(src, dst, tree),
            type_filter: type_filter.map(|t| copy_subtree(src, dst, t)),
            field: copy_subtree(src, dst, field),
            value_map: copy_subtree(src, dst, value_map),
        },
        TermNode::AttrKeyRanking { tree } => TermNode::AttrKeyRanking {
            tree: copy_subtree(src, dst, tree),
        },
        TermNode::TextShape { text } => TermNode::TextShape {
            text: copy_subtree(src, dst, text),
        },
        TermNode::FbFrameSeq { fb } => TermNode::FbFrameSeq {
            fb: copy_subtree(src, dst, fb),
        },
        TermNode::ChangeDetect {
            image_vals,
            kernel_weights,
            dims,
        } => TermNode::ChangeDetect {
            image_vals: copy_subtree(src, dst, image_vals),
            kernel_weights: copy_subtree(src, dst, kernel_weights),
            dims: copy_subtree(src, dst, dims),
        },
        TermNode::TemporalDiff { a_vals, b_vals } => TermNode::TemporalDiff {
            a_vals: copy_subtree(src, dst, a_vals),
            b_vals: copy_subtree(src, dst, b_vals),
        },
        TermNode::Foveate {
            image_vals,
            dims,
            geometry,
        } => TermNode::Foveate {
            image_vals: copy_subtree(src, dst, image_vals),
            dims: copy_subtree(src, dst, dims),
            geometry: copy_subtree(src, dst, geometry),
        },
        TermNode::Eq { a, b } => TermNode::Eq {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Lt { a, b } => TermNode::Lt {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Lte { a, b } => TermNode::Lte {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Gt { a, b } => TermNode::Gt {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Gte { a, b } => TermNode::Gte {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Minus { a, b } => TermNode::Minus {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Div { a, b } => TermNode::Div {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::DtwTo { a, b } => TermNode::DtwTo {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::EnigmaCrib { candidate } => TermNode::EnigmaCrib {
            candidate: copy_subtree(src, dst, candidate),
        },
        TermNode::EnigmaBombe { candidate } => TermNode::EnigmaBombe {
            candidate: copy_subtree(src, dst, candidate),
        },
        TermNode::EnigmaBombeWitness { candidate } => TermNode::EnigmaBombeWitness {
            candidate: copy_subtree(src, dst, candidate),
        },
        TermNode::ApcEncode {
            model,
            seq,
            start,
            end,
            out_len,
        } => TermNode::ApcEncode {
            model: copy_subtree(src, dst, model),
            seq: copy_subtree(src, dst, seq),
            start: copy_subtree(src, dst, start),
            end: copy_subtree(src, dst, end),
            out_len: copy_subtree(src, dst, out_len),
        },
        TermNode::PointSetDist { a, b } => TermNode::PointSetDist {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::MahalLeaf { a, b } => TermNode::MahalLeaf {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::MahalFull { a, b } => TermNode::MahalFull {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::DeformGenMarginal { a, b } => TermNode::DeformGenMarginal {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::DeformGen { a, b } => TermNode::DeformGen {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::DeformDist { a, b } => TermNode::DeformDist {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::SmoothDeformDist { a, b } => TermNode::SmoothDeformDist {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::TpsDeformDist { a, b } => TermNode::TpsDeformDist {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::SmoothDeformComponents { a, b } => TermNode::SmoothDeformComponents {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::ShapeContextDist { a, b } => TermNode::ShapeContextDist {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::EnclosedCount { arg } => TermNode::EnclosedCount {
            arg: copy_subtree(src, dst, arg),
        },
        TermNode::ScTpsDist { a, b } => TermNode::ScTpsDist {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::BlendCover { unknown, a, b } => TermNode::BlendCover {
            unknown: copy_subtree(src, dst, unknown),
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Whiten { a, b } => TermNode::Whiten {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::WhitenMany { a, b } => TermNode::WhitenMany {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::WithinScatter { a, b } => TermNode::WithinScatter {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::BetweenScatter { a, b } => TermNode::BetweenScatter {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::XCorrPeak { a, b } => TermNode::XCorrPeak {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Mod { a, b } => TermNode::Mod {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Pow { a, b } => TermNode::Pow {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::BitAnd { a, b } => TermNode::BitAnd {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::BitOr { a, b } => TermNode::BitOr {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::BitXor { a, b } => TermNode::BitXor {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Shl { a, b } => TermNode::Shl {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Lshr { a, b } => TermNode::Lshr {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Ashr { a, b } => TermNode::Ashr {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::IDiv { a, b } => TermNode::IDiv {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::IRem { a, b } => TermNode::IRem {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::VecAdd { a, b } => TermNode::VecAdd {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::VecSub { a, b } => TermNode::VecSub {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Dot { a, b } => TermNode::Dot {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::AngleBetween { a, b } => TermNode::AngleBetween {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Union { a, b } => TermNode::Union {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Last { seq } => TermNode::Last {
            seq: copy_subtree(src, dst, seq),
        },
        TermNode::IndexAt { seq, index } => TermNode::IndexAt {
            seq: copy_subtree(src, dst, seq),
            index: copy_subtree(src, dst, index),
        },
        TermNode::ListDrop { list, index } => TermNode::ListDrop {
            list: copy_subtree(src, dst, list),
            index: copy_subtree(src, dst, index),
        },
        TermNode::Append { seq, item } => TermNode::Append {
            seq: copy_subtree(src, dst, seq),
            item: copy_subtree(src, dst, item),
        },
        TermNode::Intersect { a, b } => TermNode::Intersect {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Difference { a, b } => TermNode::Difference {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
        },
        TermNode::Atan2 { y, x } => TermNode::Atan2 {
            y: copy_subtree(src, dst, y),
            x: copy_subtree(src, dst, x),
        },
        TermNode::Rotate { vec, angle } => TermNode::Rotate {
            vec: copy_subtree(src, dst, vec),
            angle: copy_subtree(src, dst, angle),
        },

        // Reductions with binders.
        TermNode::Filter {
            source,
            var_name,
            predicate,
        } => TermNode::Filter {
            source: copy_subtree(src, dst, source),
            var_name,
            predicate: copy_subtree(src, dst, predicate),
        },
        TermNode::FilterList {
            source,
            var_name,
            predicate,
        } => TermNode::FilterList {
            source: copy_subtree(src, dst, source),
            var_name,
            predicate: copy_subtree(src, dst, predicate),
        },
        TermNode::Exists {
            source,
            var_name,
            predicate,
        } => TermNode::Exists {
            source: copy_subtree(src, dst, source),
            var_name,
            predicate: copy_subtree(src, dst, predicate),
        },
        TermNode::Sum {
            source,
            var_name,
            value,
        } => TermNode::Sum {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
        },
        TermNode::Prod {
            source,
            var_name,
            value,
        } => TermNode::Prod {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
        },
        TermNode::MinOver {
            source,
            var_name,
            value,
            default,
        } => TermNode::MinOver {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
            default: default.map(|d| copy_subtree(src, dst, d)),
        },
        TermNode::MaxOver {
            source,
            var_name,
            value,
            default,
        } => TermNode::MaxOver {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
            default: default.map(|d| copy_subtree(src, dst, d)),
        },
        TermNode::Argmax {
            source,
            var_name,
            value,
            default,
        } => TermNode::Argmax {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
            default: default.map(|d| copy_subtree(src, dst, d)),
        },
        TermNode::Argmin {
            source,
            var_name,
            value,
            default,
        } => TermNode::Argmin {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
            default: default.map(|d| copy_subtree(src, dst, d)),
        },
        TermNode::ArgminUnique {
            source,
            var_name,
            value,
            default,
        } => TermNode::ArgminUnique {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
            default: default.map(|d| copy_subtree(src, dst, d)),
        },
        TermNode::ArgminRefusal {
            source,
            var_name,
            value,
            refused,
        } => TermNode::ArgminRefusal {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
            refused: refused.map(|d| copy_subtree(src, dst, d)),
        },
        // --- Program IR (P1) ---
        TermNode::ProgSeq { stmts } => TermNode::ProgSeq {
            stmts: stmts.iter().map(|s| copy_subtree(src, dst, *s)).collect(),
        },
        TermNode::ProgAssignVar { name, value } => TermNode::ProgAssignVar {
            name,
            value: copy_subtree(src, dst, value),
        },
        TermNode::ProgAugAssign { name, op, value } => TermNode::ProgAugAssign {
            name,
            op,
            value: copy_subtree(src, dst, value),
        },
        TermNode::ProgTupleUnpack { targets, value } => TermNode::ProgTupleUnpack {
            targets,
            value: copy_subtree(src, dst, value),
        },
        TermNode::ProgIfStmt { cond, then, orelse } => TermNode::ProgIfStmt {
            cond: copy_subtree(src, dst, cond),
            then: copy_subtree(src, dst, then),
            orelse: orelse.map(|o| copy_subtree(src, dst, o)),
        },
        TermNode::ProgForEach {
            var,
            iter,
            body,
            orelse,
        } => TermNode::ProgForEach {
            var,
            iter: copy_subtree(src, dst, iter),
            body: copy_subtree(src, dst, body),
            orelse: orelse.map(|o| copy_subtree(src, dst, o)),
        },
        TermNode::ProgWhile { cond, body, orelse } => TermNode::ProgWhile {
            cond: copy_subtree(src, dst, cond),
            body: copy_subtree(src, dst, body),
            orelse: orelse.map(|o| copy_subtree(src, dst, o)),
        },
        TermNode::ProgLoopCtl { kind } => TermNode::ProgLoopCtl { kind },
        TermNode::ProgReturn { value } => TermNode::ProgReturn {
            value: value.map(|v| copy_subtree(src, dst, v)),
        },
        TermNode::ProgTryOr {
            body,
            exc_var,
            handler,
        } => TermNode::ProgTryOr {
            body: copy_subtree(src, dst, body),
            exc_var,
            handler: handler.map(|h| copy_subtree(src, dst, h)),
        },
        TermNode::ProgRaise { exc } => TermNode::ProgRaise {
            exc: exc.map(|e| copy_subtree(src, dst, e)),
        },
        TermNode::ProgImportStmt {
            module,
            alias,
            names,
        } => TermNode::ProgImportStmt {
            module,
            alias,
            names,
        },
        TermNode::ProgSubscriptSet { obj, index, value } => TermNode::ProgSubscriptSet {
            obj: copy_subtree(src, dst, obj),
            index: copy_subtree(src, dst, index),
            value: copy_subtree(src, dst, value),
        },
        TermNode::ProgAttrSet { obj, attr, value } => TermNode::ProgAttrSet {
            obj: copy_subtree(src, dst, obj),
            attr,
            value: copy_subtree(src, dst, value),
        },
        TermNode::ProgDefFnParam { name, default } => TermNode::ProgDefFnParam {
            name,
            default: default.map(|d| copy_subtree(src, dst, d)),
        },
        TermNode::ProgCallExtern { name, recv, args } => TermNode::ProgCallExtern {
            name,
            recv: recv.map(|r| copy_subtree(src, dst, r)),
            args: args.iter().map(|a| copy_subtree(src, dst, *a)).collect(),
        },
        TermNode::ProgAttrGet { obj, attr } => TermNode::ProgAttrGet {
            obj: copy_subtree(src, dst, obj),
            attr,
        },
        TermNode::ProgSubscript { obj, index } => TermNode::ProgSubscript {
            obj: copy_subtree(src, dst, obj),
            index: copy_subtree(src, dst, index),
        },
        TermNode::ProgSlice {
            obj,
            start,
            stop,
            step,
        } => TermNode::ProgSlice {
            obj: copy_subtree(src, dst, obj),
            start: start.map(|s| copy_subtree(src, dst, s)),
            stop: stop.map(|s| copy_subtree(src, dst, s)),
            step: step.map(|s| copy_subtree(src, dst, s)),
        },
        TermNode::ProgContainerLit { kind, items } => TermNode::ProgContainerLit {
            kind,
            items: items.iter().map(|i| copy_subtree(src, dst, *i)).collect(),
        },
        TermNode::ProgComprehensionList {
            var,
            source,
            expr,
            cond,
        } => TermNode::ProgComprehensionList {
            var,
            source: copy_subtree(src, dst, source),
            expr: copy_subtree(src, dst, expr),
            cond: cond.map(|c| copy_subtree(src, dst, c)),
        },
        TermNode::ProgComprehensionGen {
            var,
            source,
            expr,
            cond,
        } => TermNode::ProgComprehensionGen {
            var,
            source: copy_subtree(src, dst, source),
            expr: copy_subtree(src, dst, expr),
            cond: cond.map(|c| copy_subtree(src, dst, c)),
        },
        TermNode::ProgIsOp { a, b, negated } => TermNode::ProgIsOp {
            a: copy_subtree(src, dst, a),
            b: copy_subtree(src, dst, b),
            negated,
        },
        TermNode::ProgFString { parts } => TermNode::ProgFString {
            parts: parts.iter().map(|p| copy_subtree(src, dst, *p)).collect(),
        },
        TermNode::ProgEval {
            prog,
            env,
            oracles,
            fuel,
            field,
        } => TermNode::ProgEval {
            prog: copy_subtree(src, dst, prog),
            env: env.map(|e| copy_subtree(src, dst, e)),
            oracles: oracles.map(|o| copy_subtree(src, dst, o)),
            fuel,
            field,
        },
        TermNode::SnakeCase { text } => TermNode::SnakeCase {
            text: copy_subtree(src, dst, text),
        },
        TermNode::CaseFold { text } => TermNode::CaseFold {
            text: copy_subtree(src, dst, text),
        },
        TermNode::Call { name, args } => TermNode::Call {
            name,
            args: args.iter().map(|a| copy_subtree(src, dst, *a)).collect(),
        },
        TermNode::SynthEnumerate {
            examples,
            ops,
            consts,
            exclude,
            derived_ops,
            exclude_ops,
            max_size,
            max_candidates,
            saturate_k,
            field,
        } => TermNode::SynthEnumerate {
            examples: copy_subtree(src, dst, examples),
            ops: ops.map(|o| copy_subtree(src, dst, o)),
            consts: consts.map(|c| copy_subtree(src, dst, c)),
            exclude: exclude.map(|e| copy_subtree(src, dst, e)),
            derived_ops: derived_ops.map(|d| copy_subtree(src, dst, d)),
            exclude_ops: exclude_ops.map(|x| copy_subtree(src, dst, x)),
            max_size,
            max_candidates,
            saturate_k,
            field,
        },
        TermNode::ParetoDominates {
            candidate,
            alternative,
            dimension_count,
            value_edge,
            measure_edge,
            dimension_key,
            verified_key,
            signed_value_key,
        } => TermNode::ParetoDominates {
            candidate: copy_subtree(src, dst, candidate),
            alternative: copy_subtree(src, dst, alternative),
            dimension_count: copy_subtree(src, dst, dimension_count),
            value_edge,
            measure_edge,
            dimension_key,
            verified_key,
            signed_value_key,
        },
        TermNode::MapSet {
            source,
            var_name,
            value,
        } => TermNode::MapSet {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
        },
        TermNode::MapList {
            source,
            var_name,
            value,
        } => TermNode::MapList {
            source: copy_subtree(src, dst, source),
            var_name,
            value: copy_subtree(src, dst, value),
        },
        TermNode::Fold {
            source,
            var_name,
            acc_name,
            init,
            body,
        } => TermNode::Fold {
            source: copy_subtree(src, dst, source),
            var_name,
            acc_name,
            init: copy_subtree(src, dst, init),
            body: copy_subtree(src, dst, body),
        },
        TermNode::Holds {
            concept,
            node,
            node2,
        } => TermNode::Holds {
            concept,
            node: node.map(|n| copy_subtree(src, dst, n)),
            node2: node2.map(|n| copy_subtree(src, dst, n)),
        },
        TermNode::IfThenElse { cond, then, other } => TermNode::IfThenElse {
            cond: copy_subtree(src, dst, cond),
            then: copy_subtree(src, dst, then),
            other: copy_subtree(src, dst, other),
        },
        TermNode::Let { name, value, body } => TermNode::Let {
            name,
            value: value.map(|v| copy_subtree(src, dst, v)),
            body: body.map(|b| copy_subtree(src, dst, b)),
        },

        // Codec stream Terms — included for completeness so copy_subtree
        // is total over TermNode (we only USE it on body-taker expansions
        // today, but a total fn is the safer shape).
        TermNode::BitsAt {
            buffer,
            bitpos,
            n_bits,
        } => TermNode::BitsAt {
            buffer: copy_subtree(src, dst, buffer),
            bitpos: copy_subtree(src, dst, bitpos),
            n_bits: copy_subtree(src, dst, n_bits),
        },
        TermNode::BitsWrite {
            buffer,
            bitpos,
            value,
            n_bits,
        } => TermNode::BitsWrite {
            buffer: copy_subtree(src, dst, buffer),
            bitpos: copy_subtree(src, dst, bitpos),
            value: copy_subtree(src, dst, value),
            n_bits: copy_subtree(src, dst, n_bits),
        },
        TermNode::BitsAtAll { buffer, reads } => TermNode::BitsAtAll {
            buffer: copy_subtree(src, dst, buffer),
            reads: copy_subtree(src, dst, reads),
        },
        TermNode::BitsWriteAll { buffer, writes } => TermNode::BitsWriteAll {
            buffer: copy_subtree(src, dst, buffer),
            writes: copy_subtree(src, dst, writes),
        },
        TermNode::HuffmanDecodeStream {
            buffer,
            bitpos,
            table,
            n_pairs,
        } => TermNode::HuffmanDecodeStream {
            buffer: copy_subtree(src, dst, buffer),
            bitpos: copy_subtree(src, dst, bitpos),
            table: copy_subtree(src, dst, table),
            n_pairs: copy_subtree(src, dst, n_pairs),
        },
        TermNode::HuffmanEncodeStream {
            buffer,
            bitpos,
            pairs,
            table,
        } => TermNode::HuffmanEncodeStream {
            buffer: copy_subtree(src, dst, buffer),
            bitpos: copy_subtree(src, dst, bitpos),
            pairs: copy_subtree(src, dst, pairs),
            table: copy_subtree(src, dst, table),
        },
        TermNode::ExpGolombDecode { buffer, bitpos } => TermNode::ExpGolombDecode {
            buffer: copy_subtree(src, dst, buffer),
            bitpos: copy_subtree(src, dst, bitpos),
        },
        TermNode::ExpGolombDecodeSigned { buffer, bitpos } => TermNode::ExpGolombDecodeSigned {
            buffer: copy_subtree(src, dst, buffer),
            bitpos: copy_subtree(src, dst, bitpos),
        },
        TermNode::ExpGolombEncode {
            buffer,
            bitpos,
            value,
        } => TermNode::ExpGolombEncode {
            buffer: copy_subtree(src, dst, buffer),
            bitpos: copy_subtree(src, dst, bitpos),
            value: copy_subtree(src, dst, value),
        },
        TermNode::ExpGolombEncodeSigned {
            buffer,
            bitpos,
            value,
        } => TermNode::ExpGolombEncodeSigned {
            buffer: copy_subtree(src, dst, buffer),
            bitpos: copy_subtree(src, dst, bitpos),
            value: copy_subtree(src, dst, value),
        },

        // Rendering Terms with optional children.
        TermNode::Join { separator, items } => TermNode::Join {
            separator: separator.map(|s| copy_subtree(src, dst, s)),
            items: items.map(|i| copy_subtree(src, dst, i)),
        },
        TermNode::U8 { expr } => TermNode::U8 {
            expr: expr.map(|e| copy_subtree(src, dst, e)),
        },
        TermNode::U16LE { expr } => TermNode::U16LE {
            expr: expr.map(|e| copy_subtree(src, dst, e)),
        },
        TermNode::U32LE { expr } => TermNode::U32LE {
            expr: expr.map(|e| copy_subtree(src, dst, e)),
        },
        TermNode::U64LE { expr } => TermNode::U64LE {
            expr: expr.map(|e| copy_subtree(src, dst, e)),
        },
        TermNode::LEB128 { expr } => TermNode::LEB128 {
            expr: expr.map(|e| copy_subtree(src, dst, e)),
        },
        TermNode::Nth { items, index } => TermNode::Nth {
            items: items.map(|i| copy_subtree(src, dst, i)),
            index,
        },
        TermNode::Render { term, lang } => TermNode::Render {
            term: term.map(|t| copy_subtree(src, dst, t)),
            lang: lang.map(|l| copy_subtree(src, dst, l)),
        },
        TermNode::LitRepr { value } => TermNode::LitRepr {
            value: value.map(|v| copy_subtree(src, dst, v)),
        },
    };
    dst.add(copied)
}

// --- Body-taker expansions ---
//
// Each expansion synthesises a kernel Term-tree equivalent for one
// derivable variant. The user's Term-fields (source/value/predicate/...)
// are deep-copied into `tmp` via `copy_subtree`; the user's Sym-fields
// (var_name) are reused as-is. The result is a TermIdx into `tmp` that
// evaluates to the same Value the native arm would produce.
//
// Today these live in Rust. The next iteration moves them to graph-
// resident template Terms with splice-Var sentinels (`Var("$source")`,
// `Var("$value")`, etc.), so `wonder_why Sum` returns a Term-tree the
// agent can inspect and modify. The interface here is stable: the
// kernel `Fold` it produces is the same; only how the template is
// authored changes.

/// `Count(source) := Fold(source, "_e", "_acc", Lit(0), Plus(Var("_acc"), Lit(1)))`
fn expand_count(src: &TermArena, tmp: &mut TermArena, ir: &Interner, source: TermIdx) -> TermIdx {
    let source_t = copy_subtree(src, tmp, source);
    let e_sym = ir.lookup("_e").unwrap_or_default();
    let acc_sym = ir.lookup("_acc").unwrap_or_default();
    let zero = tmp.add(TermNode::Lit {
        value: Value::Int(0),
    });
    let one = tmp.add(TermNode::Lit {
        value: Value::Int(1),
    });
    let acc_var = tmp.add(TermNode::Var { name: acc_sym });
    let plus = tmp.add(TermNode::Plus {
        items: vec![acc_var, one],
    });
    tmp.add(TermNode::Fold {
        source: source_t,
        var_name: e_sym,
        acc_name: acc_sym,
        init: zero,
        body: plus,
    })
}

/// `Sum(source, var, value) := Fold(source, var, "_acc", Lit(0), Plus(Var("_acc"), value))`
fn expand_sum(
    src: &TermArena,
    tmp: &mut TermArena,
    ir: &Interner,
    source: TermIdx,
    var_name: Sym,
    value: TermIdx,
) -> TermIdx {
    let source_t = copy_subtree(src, tmp, source);
    let value_t = copy_subtree(src, tmp, value);
    let acc_sym = ir.lookup("_acc").unwrap_or_default();
    let acc_var = tmp.add(TermNode::Var { name: acc_sym });
    let init = tmp.add(TermNode::Lit {
        value: Value::Int(0),
    });
    let plus = tmp.add(TermNode::Plus {
        items: vec![acc_var, value_t],
    });
    tmp.add(TermNode::Fold {
        source: source_t,
        var_name,
        acc_name: acc_sym,
        init,
        body: plus,
    })
}

/// Dispatch a derivable variant through its graph-resident derivation if
/// one is registered. Each arg is evaluated, bound under its conventional
/// name in `env`, then the derivation is evaluated. Bindings are popped
/// after. On miss, the macro emits NO `return`, so the host arm falls
/// through to its native impl. Usage:
///
/// ```ignore
/// TermNode::Gt { a, b } => {
///     try_derivation!(ctx, arena, env, "Gt", [("a", *a), ("b", *b)]);
///     cmp_bool(arena, *a, *b, env, ctx, Ordering::Greater, false)
/// }
/// ```
macro_rules! try_derivation {
    ($ctx:expr, $arena:expr, $env:expr, $kind:literal, [$(($arg_name:literal, $arg_idx:expr)),* $(,)?]) => {
        if let Some(__def) = lookup_value_taker_def($ctx, $arena, $kind) {
            let mut __n: usize = 0;
            $(
                {
                    let __v = evaluate($arena, $arg_idx, $env, $ctx);
                    let __s = $ctx.interner.lookup($arg_name).unwrap_or_default();
                    $env.push((__s, __v));
                    __n += 1;
                }
            )*
            let __r = evaluate($arena, __def, $env, $ctx);
            for _ in 0..__n { $env.pop(); }
            return __r;
        }
    };
}

/// Evaluate a Term subtree under the given env + ctx. Returns a Value
/// matching what the Python `Term.evaluate` would have produced (modulo
/// the Bool↔Int coercion noted in `value.rs`).
/// Least-general generalization over a slice of structured Values — the
/// native twin of `domains/implied_rule.py::anti_unify`. Faithful to its
/// cases: empty → WILD; all-equal → that value; all-Dict → over the shared
/// (intersected) keys, each recursively generalized; all-Tuple of equal
/// length → element-wise; all-Set/FrozenSet → the intersection (frozenset);
/// otherwise → WILD. Order-independent (LGG depends only on the instance set).
/// Is `v` the wildcard SENTINEL?
///
/// ARC6 value layer: the sentinel is a ONE-ELEMENT SEQUENCE holding the
/// interned `"·?·"` marker, and its container kind carries no meaning. A
/// sentinel that has round-tripped through the graph and Python (adapters
/// normalise with `_plain`, which yields lists) comes back as a `List`
/// while `wild_val` is built here as a `Tuple` — so a bare `==` silently
/// stopped recognising it, and an anti-unified codebook entry could no
/// longer cover the observation it was generalised from
/// (`test_near_shapes_join_not_double_mint`). Compare CONTENTS.
fn is_wild(v: &Value, wild: &Value) -> bool {
    match (v, wild) {
        (Value::Tuple(a) | Value::List(a), Value::Tuple(b) | Value::List(b)) => {
            a.as_slice() == b.as_slice()
        }
        _ => v == wild,
    }
}

pub(crate) fn anti_unify_values(vals: &[Value], wild: &Value) -> Value {
    if vals.is_empty() {
        return wild.clone();
    }
    let first = &vals[0];
    if vals[1..].iter().all(|v| v == first) {
        return first.clone();
    }
    // all dicts → generalize over the shared keys
    if vals.iter().all(|v| matches!(v, Value::Dict(_))) {
        let dicts: Vec<&Arc<[(Value, Value)]>> = vals
            .iter()
            .map(|v| match v {
                Value::Dict(d) => d,
                _ => unreachable!(),
            })
            .collect();
        let mut shared: Vec<Value> = dicts[0].iter().map(|(k, _)| k.clone()).collect();
        shared.retain(|k| dicts[1..].iter().all(|d| d.iter().any(|(dk, _)| dk == k)));
        shared.sort_by(cmp_value);
        let mut entries: Vec<(Value, Value)> = Vec::with_capacity(shared.len());
        for k in shared {
            let col: Vec<Value> = dicts
                .iter()
                .map(|d| d.iter().find(|(dk, _)| *dk == k).unwrap().1.clone())
                .collect();
            entries.push((k, anti_unify_values(&col, wild)));
        }
        return Value::Dict(Arc::from(entries));
    }
    // all tuples of equal length → element-wise
    if vals
        .iter()
        .all(|v| matches!(v, Value::Tuple(_) | Value::List(_)))
    {
        let tups: Vec<&Arc<SmallVec<[Value; 4]>>> = vals
            .iter()
            .map(|v| match v {
                Value::Tuple(t) | Value::List(t) => t,
                _ => unreachable!(),
            })
            .collect();
        let n = tups[0].len();
        if tups.iter().all(|t| t.len() == n) {
            let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(n);
            for i in 0..n {
                let col: Vec<Value> = tups.iter().map(|t| t[i].clone()).collect();
                out.push(anti_unify_values(&col, wild));
            }
            return Value::Tuple(Arc::new(out));
        }
    }
    // all sets/frozensets → the intersection (members always present)
    if vals
        .iter()
        .all(|v| matches!(v, Value::Set(_) | Value::FrozenSet(_)))
    {
        let getset = |v: &Value| -> Vec<Value> {
            match v {
                Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
                _ => vec![],
            }
        };
        let mut inter = getset(&vals[0]);
        for v in &vals[1..] {
            let s = getset(v);
            inter.retain(|x| s.iter().any(|y| y == x));
        }
        return Value::make_frozenset(inter);
    }
    wild.clone()
}

/// Anti-unification that RETAINS its witnesses — the lattice-MEET that also
/// emits the DIFFERENCE (`AntiUnifyWitness` Term). Returns `(template, sigmas)`
/// where `template` is exactly `anti_unify_values`' lgg and `sigmas` is one
/// Vec of (path, residue) per instance: each PATH is the chain of step keys
/// (Int index for Tuples, the key Value for Dicts) down to a WILD, mapped to
/// the subterm that filled it in that instance. The residue `anti_unify_values`
/// discards (`wild.clone()` where instances differ) is captured here as the
/// witness substitutions {σ₁,σ₂,…}; template+σ let `substitute_value` move DOWN
/// the subsumption lattice ("X but with Y"). Recursion mirrors
/// `anti_unify_values` exactly (Dict over shared keys, Tuple element-wise,
/// Set→intersection), threading `path`.
fn anti_unify_witness_values(vals: &[Value], wild: &Value) -> (Value, Vec<Vec<(Value, Value)>>) {
    fn go(
        vals: &[Value],
        wild: &Value,
        path: &mut Vec<Value>,
        subs: &mut [Vec<(Value, Value)>],
    ) -> Value {
        if vals.is_empty() {
            return wild.clone();
        }
        let first = &vals[0];
        if vals[1..].iter().all(|v| v == first) {
            return first.clone(); // agree → fixed, no witness
        }
        // all dicts → generalise over shared keys
        if vals.iter().all(|v| matches!(v, Value::Dict(_))) {
            let dicts: Vec<&Arc<[(Value, Value)]>> = vals
                .iter()
                .map(|v| match v {
                    Value::Dict(d) => d,
                    _ => unreachable!(),
                })
                .collect();
            let mut shared: Vec<Value> = dicts[0].iter().map(|(k, _)| k.clone()).collect();
            shared.retain(|k| dicts[1..].iter().all(|d| d.iter().any(|(dk, _)| dk == k)));
            shared.sort_by(cmp_value);
            let mut entries: Vec<(Value, Value)> = Vec::with_capacity(shared.len());
            for k in shared {
                let col: Vec<Value> = dicts
                    .iter()
                    .map(|d| d.iter().find(|(dk, _)| *dk == k).unwrap().1.clone())
                    .collect();
                path.push(k.clone());
                entries.push((k, go(&col, wild, path, subs)));
                path.pop();
            }
            return Value::Dict(Arc::from(entries));
        }
        // all tuples of equal length → element-wise
        if vals
            .iter()
            .all(|v| matches!(v, Value::Tuple(_) | Value::List(_)))
        {
            let tups: Vec<&Arc<SmallVec<[Value; 4]>>> = vals
                .iter()
                .map(|v| match v {
                    Value::Tuple(t) | Value::List(t) => t,
                    _ => unreachable!(),
                })
                .collect();
            let len = tups[0].len();
            if tups.iter().all(|t| t.len() == len) {
                let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(len);
                for i in 0..len {
                    let col: Vec<Value> = tups.iter().map(|t| t[i].clone()).collect();
                    path.push(Value::Int(i as i64));
                    out.push(go(&col, wild, path, subs));
                    path.pop();
                }
                return Value::Tuple(Arc::new(out));
            }
        }
        // all sets → the intersection; the witness per instance is the members
        // it carries beyond the shared core (a set has no positional slot, so
        // the differing members are recorded at this path as a frozenset).
        if vals
            .iter()
            .all(|v| matches!(v, Value::Set(_) | Value::FrozenSet(_)))
        {
            let getset = |v: &Value| -> Vec<Value> {
                match v {
                    Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
                    _ => vec![],
                }
            };
            let mut inter = getset(&vals[0]);
            for v in &vals[1..] {
                let s = getset(v);
                inter.retain(|x| s.iter().any(|y| y == x));
            }
            let p = Value::Tuple(Arc::new(SmallVec::from_vec(path.clone())));
            for (i, v) in vals.iter().enumerate() {
                let extra: Vec<Value> = getset(v)
                    .into_iter()
                    .filter(|x| !inter.iter().any(|y| y == x))
                    .collect();
                if !extra.is_empty() {
                    subs[i].push((p.clone(), Value::make_frozenset(extra)));
                }
            }
            return Value::make_frozenset(inter);
        }
        // leaf disagreement → WILD here; record each instance's value as witness
        let p = Value::Tuple(Arc::new(SmallVec::from_vec(path.clone())));
        for (i, v) in vals.iter().enumerate() {
            subs[i].push((p.clone(), v.clone()));
        }
        wild.clone()
    }
    let mut subs: Vec<Vec<(Value, Value)>> = vec![Vec::new(); vals.len()];
    let mut path: Vec<Value> = Vec::new();
    let template = go(vals, wild, &mut path, &mut subs);
    (template, subs)
}

/// Apply a witness substitution to a template — the lattice-JOIN direction
/// ("X but with Y": move DOWN by instantiating the WILDs). Walks `template`;
/// at each WILD it looks up the current position-PATH in `sigma` (a slice of
/// (path, value) pairs, as emitted by `anti_unify_witness_values`) and
/// substitutes that value; unmatched WILDs are left as WILD. Recurses into
/// Tuple/Dict so a nested (higher-order) template is instantiated structurally
/// — the inverse of AntiUnify's walk. Sets: a path→frozenset witness is UNIONED
/// back into the shared core. Pure structural rewrite (no flattening).
fn substitute_value(template: &Value, sigma: &[(Value, Value)], wild: &Value) -> Value {
    fn lookup<'a>(sigma: &'a [(Value, Value)], path: &Value) -> Option<&'a Value> {
        sigma.iter().find(|(k, _)| k == path).map(|(_, v)| v)
    }
    fn go(t: &Value, sigma: &[(Value, Value)], wild: &Value, path: &mut Vec<Value>) -> Value {
        if is_wild(t, wild) {
            let p = Value::Tuple(Arc::new(SmallVec::from_vec(path.clone())));
            return match lookup(sigma, &p) {
                Some(v) => v.clone(),
                None => wild.clone(),
            };
        }
        match t {
            Value::Tuple(items) | Value::List(items) => {
                let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(items.len());
                for (i, it) in items.iter().enumerate() {
                    path.push(Value::Int(i as i64));
                    out.push(go(it, sigma, wild, path));
                    path.pop();
                }
                t.reseq(out) // KIND-PRESERVING (see `Value::reseq`)
            }
            Value::Dict(entries) => {
                let mut out: Vec<(Value, Value)> = Vec::with_capacity(entries.len());
                for (k, v) in entries.iter() {
                    path.push(k.clone());
                    out.push((k.clone(), go(v, sigma, wild, path)));
                    path.pop();
                }
                Value::Dict(Arc::from(out))
            }
            Value::Set(s) | Value::FrozenSet(s) => {
                // a set carries no WILD slot; union in any path→frozenset witness
                let p = Value::Tuple(Arc::new(SmallVec::from_vec(path.clone())));
                let mut members = s.to_vec();
                if let Some(Value::Set(add) | Value::FrozenSet(add)) = lookup(sigma, &p) {
                    for x in add.iter() {
                        if !members.iter().any(|y| y == x) {
                            members.push(x.clone());
                        }
                    }
                }
                Value::make_frozenset(members)
            }
            other => other.clone(),
        }
    }
    let mut path: Vec<Value> = Vec::new();
    go(template, sigma, wild, &mut path)
}

/// Unification — the lattice JOIN (lub), the constructive DUAL of
/// `anti_unify_values` (the MEET/glb). Where AntiUnify abstracts UP to the most
/// specific COMMON generalisation (WILDing differences), Unify combines DOWN to
/// the most general SPECIALISATION consistent with all inputs — the BLEND /
/// amalgam (Fauconnier-Turner). Recursion mirrors AntiUnify exactly:
///   • all AGREE                         → that value (fixed; shared generic kept)
///   • a WILD on one side                → take the concrete side (fill the hole;
///                                          this is how the shared generic's slots
///                                          are SELECTIVELY PROJECTED from inputs)
///   • all Dicts                         → unify over the UNION of keys (a key in
///                                          only one input is projected in — emergent)
///   • all Tuples, equal len             → element-wise unify (recurse the system)
///   • all Sets/FrozenSets               → the UNION (both inputs' members)
///   • genuine leaf/shape CONFLICT       → FUSE into a frozenset {a, b, …} — the
///                                          emergent fused slot that carries BOTH
///                                          contributions (never a silent drop /
///                                          collapse). The conflict is SURFACED as
///                                          a multi-member set, detectable by the
///                                          caller (a singleton ⇒ consistent).
/// So `Unify(house, boat)` keeps (function/location/occupant) generic, fills each
/// from both → the houseboat blend with the conflict made explicit per slot.
fn unify_values(vals: &[Value], wild: &Value) -> Value {
    if vals.is_empty() {
        return wild.clone();
    }
    // drop WILDs: a hole imposes no constraint (the JOIN with TOP is the other side)
    let concrete: Vec<&Value> = vals.iter().filter(|v| !is_wild(v, wild)).collect();
    if concrete.is_empty() {
        return wild.clone();
    }
    let first = concrete[0];
    if concrete[1..].iter().all(|v| *v == first) {
        return first.clone(); // all agree → fixed
    }
    // all dicts → unify over the UNION of keys (emergent: a key in one survives)
    if concrete.iter().all(|v| matches!(v, Value::Dict(_))) {
        let dicts: Vec<&Arc<[(Value, Value)]>> = concrete
            .iter()
            .map(|v| match v {
                Value::Dict(d) => d,
                _ => unreachable!(),
            })
            .collect();
        let mut keys: Vec<Value> = Vec::new();
        for d in &dicts {
            for (k, _) in d.iter() {
                if !keys.iter().any(|x| x == k) {
                    keys.push(k.clone());
                }
            }
        }
        keys.sort_by(cmp_value);
        let mut entries: Vec<(Value, Value)> = Vec::with_capacity(keys.len());
        for k in keys {
            let col: Vec<Value> = dicts
                .iter()
                .filter_map(|d| d.iter().find(|(dk, _)| *dk == k).map(|(_, v)| v.clone()))
                .collect();
            entries.push((k.clone(), unify_values(&col, wild)));
        }
        return Value::Dict(Arc::from(entries));
    }
    // all tuples of equal length → element-wise unify
    if concrete
        .iter()
        .all(|v| matches!(v, Value::Tuple(_) | Value::List(_)))
    {
        let tups: Vec<&Arc<SmallVec<[Value; 4]>>> = concrete
            .iter()
            .map(|v| match v {
                Value::Tuple(t) | Value::List(t) => t,
                _ => unreachable!(),
            })
            .collect();
        let len = tups[0].len();
        if tups.iter().all(|t| t.len() == len) {
            let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(len);
            for i in 0..len {
                let col: Vec<Value> = tups.iter().map(|t| t[i].clone()).collect();
                out.push(unify_values(&col, wild));
            }
            return Value::Tuple(Arc::new(out));
        }
    }
    // all sets → the UNION (both inputs' members)
    if concrete
        .iter()
        .all(|v| matches!(v, Value::Set(_) | Value::FrozenSet(_)))
    {
        let mut members: Vec<Value> = Vec::new();
        for v in &concrete {
            let s = match v {
                Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
                _ => vec![],
            };
            for x in s {
                if !members.iter().any(|y| *y == x) {
                    members.push(x);
                }
            }
        }
        return Value::make_frozenset(members);
    }
    // genuine conflict (distinct leaves / incompatible shapes) → FUSE both into a
    // frozenset (the emergent fused slot; surfaces the conflict, never drops it).
    let mut fused: Vec<Value> = Vec::new();
    for v in &concrete {
        if !fused.iter().any(|y| y == *v) {
            fused.push((*v).clone());
        }
    }
    Value::make_frozenset(fused)
}

/// Graded STRUCTURAL similarity in [0,1] — the SOFT-leaf twin of the exact-match
/// structural compare. Recurses two structures in parallel exactly like
/// `anti_unify_values`, but at a leaf returns a GRADED agreement instead of a
/// boolean: a numeric-VECTOR leaf (Tuple of all-numeric = a learned part-shape
/// descriptor) scores `exp(-||a-b||)` (writer variation within a part-shape no
/// longer breaks the match — the soft-vocabulary lift); a string/atom leaf
/// (relations, ids — the structural skeleton) stays EXACT (1.0 iff equal). A
/// WILD on either side matches anything (1.0). Tuples/Dicts aggregate as the MEAN
/// of child sims over the shared positions/keys, multiplied by a coverage factor
/// (shared / max len|keys) so a length/arity mismatch is penalised. So relations
/// stay hard (the program skeleton) while part-shapes grade — the generative
/// program survives writer variation WITHOUT drifting to a holistic learned
/// similarity. The constructive complement that keeps recognition in the
/// generative-program route.
fn struct_sim_value(a: &Value, b: &Value, wild: &Value) -> f64 {
    if is_wild(a, wild) || is_wild(b, wild) {
        return 1.0;
    }
    // numeric-vector leaves (descriptors) → graded by Euclidean distance
    let as_vec = |v: &Value| -> Option<Vec<f64>> {
        match v {
            Value::Tuple(t) | Value::List(t) => {
                let mut out = Vec::with_capacity(t.len());
                for x in t.iter() {
                    match x {
                        Value::Float(f) => out.push(*f),
                        Value::Int(i) => out.push(*i as f64),
                        _ => return None,
                    }
                }
                if out.is_empty() {
                    None
                } else {
                    Some(out)
                }
            }
            _ => None,
        }
    };
    if let (Some(va), Some(vb)) = (as_vec(a), as_vec(b)) {
        if va.len() == vb.len() {
            let mut s = 0.0;
            for i in 0..va.len() {
                let d = va[i] - vb[i];
                s += d * d;
            }
            return (-s.sqrt()).exp();
        }
        return 0.0;
    }
    // dicts → mean over shared keys × coverage
    if let (Value::Dict(da), Value::Dict(db)) = (a, b) {
        let mut shared = 0usize;
        let mut acc = 0.0;
        for (k, va) in da.iter() {
            if let Some((_, vb)) = db.iter().find(|(dk, _)| dk == k) {
                acc += struct_sim_value(va, vb, wild);
                shared += 1;
            }
        }
        let denom = da.len().max(db.len());
        if denom == 0 {
            return 1.0;
        }
        if shared == 0 {
            return 0.0;
        }
        return (acc / shared as f64) * (shared as f64 / denom as f64);
    }
    // tuples → mean over shared positions × coverage
    if let (Value::Tuple(ta) | Value::List(ta), Value::Tuple(tb) | Value::List(tb)) = (a, b) {
        let n = ta.len().min(tb.len());
        let denom = ta.len().max(tb.len());
        if denom == 0 {
            return 1.0;
        }
        if n == 0 {
            return 0.0;
        }
        let mut acc = 0.0;
        for i in 0..n {
            acc += struct_sim_value(&ta[i], &tb[i], wild);
        }
        return (acc / n as f64) * (n as f64 / denom as f64);
    }
    // sets → Jaccard-style soft overlap (best-match each member, symmetric mean)
    if let (Value::Set(sa) | Value::FrozenSet(sa), Value::Set(sb) | Value::FrozenSet(sb)) = (a, b) {
        if sa.is_empty() && sb.is_empty() {
            return 1.0;
        }
        if sa.is_empty() || sb.is_empty() {
            return 0.0;
        }
        let best = |xs: &[Value], ys: &[Value]| -> f64 {
            let mut tot = 0.0;
            for x in xs {
                let mut m = 0.0;
                for y in ys {
                    let s = struct_sim_value(x, y, wild);
                    if s > m {
                        m = s;
                    }
                }
                tot += m;
            }
            tot / xs.len() as f64
        };
        return 0.5 * (best(sa, sb) + best(sb, sa));
    }
    // atoms (string/int/bool/node) → exact (the relational skeleton stays hard)
    if a == b {
        1.0
    } else {
        0.0
    }
}

/// How many leaf positions an induced pattern FIXES — the native twin of
/// `domains/implied_rule.py::_fixed_count`. The WILD check comes first (WILD
/// is itself a Tuple, so it must be matched before the Tuple arm).
/// Does `pat` cover `inst`? — native twin of `implied_rule.py::covers`. The
/// WILD check comes first (WILD matches anything).
pub(crate) fn covers_value(pat: &Value, inst: &Value, wild: &Value) -> bool {
    if is_wild(pat, wild) {
        return true;
    }
    match pat {
        Value::Dict(pd) => {
            let Value::Dict(id) = inst else { return false };
            pd.iter()
                .all(|(k, pv)| match id.iter().find(|(ik, _)| ik == k) {
                    Some((_, iv)) => covers_value(pv, iv, wild),
                    None => false,
                })
        }
        Value::Tuple(pt) | Value::List(pt) => {
            let (Value::Tuple(it) | Value::List(it)) = inst else {
                return false;
            };
            pt.len() == it.len()
                && pt
                    .iter()
                    .zip(it.iter())
                    .all(|(p, i)| covers_value(p, i, wild))
        }
        Value::Set(ps) | Value::FrozenSet(ps) => {
            let is = match inst {
                Value::Set(s) | Value::FrozenSet(s) => s,
                _ => return false,
            };
            ps.iter().all(|m| is.iter().any(|x| x == m))
        }
        _ => pat == inst,
    }
}

/// OPEN-ARITY coverage — `covers_value` with the OUTER container read as a
/// relation SET rather than a positional tuple, and every element compared by
/// `covers_value` UNCHANGED.
///
/// WHY THIS EXISTS, and why it is not a weakening of `Covers`
/// ---------------------------------------------------------
/// `SHAPE_TYPE_VOCABULARY_SPIKE.md` §3.3 states a genuine three-way trade over
/// `covers_value`'s three container arms: `Set` gives residual capture and open
/// arity but cannot carry a WILD; `Dict` gives WILD and open arity but loses
/// the residual; `Tuple`/`List` gives WILD and residual and buys them by
/// FIXING THE ARITY (`pt.len() == it.len()`, immediately above).
///
/// That trade is real **per level**, and only bites when one container is asked
/// to serve both levels at once. A shape signature in this tree is not one
/// container — it is a **SET of POSITIONAL relations**: the outer level wants
/// set semantics (a held generalisation applies to an item that carries extra,
/// unrelated relations), the inner level wants tuple semantics (`[predicate,
/// value]` is positional, and `["buyer", WILD]` must NOT match
/// `["alice", "buyer"]`). Splitting the levels gets WILD *and* residual *and*
/// open arity, without changing what any existing caller sees.
///
/// The engine already reads relation SETS this way one layer down:
/// `shape_decode.rs::covers_relation` asks whether SOME relation of a part's
/// signature covers a given goal relation, and leaves the uncovered ones as the
/// residual — it never requires the two signatures to be the same length. The
/// whole-signature `Covers` guard at the meta-shape grain was the outlier.
///
/// SEMANTICS, stated precisely
/// ---------------------------
/// * pattern WILD ⇒ true (as `covers_value`).
/// * pattern and instance both list-like ⇒ true iff there is an INJECTIVE map
///   from pattern elements to instance elements under which every pattern
///   element `covers_value`s its image. Superset-tolerant, never
///   subset-tolerant: a pattern relation with no partner fails.
/// * anything else ⇒ delegate to `covers_value` verbatim. Dict / Set / scalar
///   semantics are untouched, and so is EVERY existing `Covers` caller: this is
///   a separate function reached only from `TermNode::CoversOpen`.
///
/// The map is required to be injective (a maximum-bipartite-matching, Kuhn's
/// algorithm) rather than a per-element existential, so two pattern relations
/// can never be satisfied by ONE instance relation. At this grain a signature's
/// predicates are distinct by construction, so the two readings agree on real
/// data; the matching is here so the semantics is honest independently of that
/// contingent fact, not because a case was observed.
pub(crate) fn covers_open_value(pat: &Value, inst: &Value, wild: &Value) -> bool {
    if is_wild(pat, wild) {
        return true;
    }
    match (pat, inst) {
        (Value::Tuple(pt) | Value::List(pt), Value::Tuple(it) | Value::List(it)) => {
            if pt.len() > it.len() {
                return false;
            }
            // Adjacency: which instance elements each pattern element covers.
            // SCALE AUDIT — the O(P x I) compare core, charged like
            // `shape_decode::covers_relation` charges its own scan.
            let mut adj: Vec<Vec<usize>> = Vec::with_capacity(pt.len());
            let mut scanned: u64 = 0;
            for p in pt.iter() {
                let mut row = Vec::new();
                for (j, i) in it.iter().enumerate() {
                    scanned += 1;
                    if covers_value(p, i, wild) {
                        row.push(j);
                    }
                }
                if row.is_empty() {
                    crate::scale_audit::term_units(scanned);
                    return false;
                }
                adj.push(row);
            }
            crate::scale_audit::term_units(scanned);
            // Kuhn's augmenting-path matching: every pattern element must be
            // matched to a DISTINCT instance element.
            let mut matched: Vec<Option<usize>> = vec![None; it.len()];
            fn augment(
                u: usize,
                adj: &[Vec<usize>],
                seen: &mut [bool],
                matched: &mut [Option<usize>],
            ) -> bool {
                for &v in &adj[u] {
                    if seen[v] {
                        continue;
                    }
                    seen[v] = true;
                    let free = match matched[v] {
                        None => true,
                        Some(w) => augment(w, adj, seen, matched),
                    };
                    if free {
                        matched[v] = Some(u);
                        return true;
                    }
                }
                false
            }
            for u in 0..adj.len() {
                let mut seen = vec![false; it.len()];
                if !augment(u, &adj, &mut seen, &mut matched) {
                    return false;
                }
            }
            true
        }
        _ => covers_value(pat, inst, wild),
    }
}

/// Backed-up lookahead value over a previewed game-tree subgraph — the
/// recursive core of `_lookahead`, bounded by `depth`.
fn lookahead_value(
    graph: &TypedGraph,
    node: NodeID,
    child_edge: Sym,
    score_key: Sym,
    depth: i64,
) -> f64 {
    crate::access_trace::note(2, node.0, score_key.0, crate::access_trace::NO_ID);
    let score = graph
        .node(node)
        .attrs
        .get(&score_key)
        .map(|v| v.as_f64())
        .unwrap_or(0.0);
    if depth <= 1 {
        return score;
    }
    crate::access_trace::note_out_edges(graph, node, Some(child_edge));
    let children = graph.neighbours(node, Some(child_edge));
    if children.is_empty() {
        return score;
    }
    let best = children
        .iter()
        .map(|c| lookahead_value(graph, *c, child_edge, score_key, depth - 1))
        .fold(f64::NEG_INFINITY, f64::max);
    score + best
}

pub(crate) fn fixed_count_value(v: &Value, wild: &Value) -> i64 {
    if is_wild(v, wild) {
        return 0;
    }
    match v {
        Value::Dict(d) => d.iter().map(|(_, val)| fixed_count_value(val, wild)).sum(),
        Value::Tuple(t) | Value::List(t) => t.iter().map(|e| fixed_count_value(e, wild)).sum(),
        Value::Set(s) | Value::FrozenSet(s) => s.len() as i64,
        _ => 1,
    }
}

// --- ToJsonString / FromJsonString / ShiftThresholdLits helpers -----------
//
// Free functions (not tied to the arena/env) so they're independently
// testable and reusable. `value_to_json_for_string`/`json_to_value` are
// deliberately separate from `graph_rules::value_to_json` (which is
// scoped to Term-JSON reading and treats Surface as an error case) --
// these two are the general Value<->JSON bridge these three Terms need,
// including the Surface(Text) arm StringConcat's output already relies
// on downstream callers coercing.

/// `Value` -> `serde_json::Value`, for `ToJsonString`. `Node` and
/// `Surface(Bytes, ...)` have no Term-JSON shape and serialise to
/// `null`; every other variant round-trips through `FromJsonString`.
fn value_to_json_for_string(v: &Value, interner: &Interner) -> serde_json::Value {
    use serde_json::Value as J;
    match v {
        Value::None => J::Null,
        Value::Bool(b) => J::Bool(*b),
        Value::Int(n) => J::Number((*n).into()),
        Value::Float(f) => serde_json::Number::from_f64(*f)
            .map(J::Number)
            .unwrap_or(J::Null),
        // The boundary: `json.dumps` of a program value has no rational
        // JSON literal — it renders the same double a real Python float
        // would (e.g. `json.dumps(1/3)` -> `0.3333333333333333`).
        Value::Rational(n, d) => serde_json::Number::from_f64(*n as f64 / *d as f64)
            .map(J::Number)
            .unwrap_or(J::Null),
        Value::Str(sym) => J::String(interner.resolve(*sym).to_string()),
        Value::Surface(SurfaceKind::Text, bytes) => {
            J::String(String::from_utf8_lossy(bytes).into_owned())
        }
        Value::Surface(SurfaceKind::Bytes, _) => J::Null,
        Value::Node(_) => J::Null,
        Value::Tuple(items) | Value::List(items) => J::Array(
            items
                .iter()
                .map(|x| value_to_json_for_string(x, interner))
                .collect(),
        ),
        Value::Set(items) | Value::FrozenSet(items) => J::Array(
            items
                .iter()
                .map(|x| value_to_json_for_string(x, interner))
                .collect(),
        ),
        Value::Dict(pairs) => {
            let mut obj = serde_json::Map::new();
            for (k, val) in pairs.iter() {
                let key = match k {
                    Value::Str(s) => interner.resolve(*s).to_string(),
                    Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(b).into_owned(),
                    other => format!("{:?}", other),
                };
                obj.insert(key, value_to_json_for_string(val, interner));
            }
            J::Object(obj)
        }
    }
}

/// `serde_json::Value` -> `Value`, for `FromJsonString`. Strings and
/// object keys become `Surface(Text)` (never `Str`) -- `evaluate()` only
/// has an immutable `&Interner`, so a freshly-parsed string can't be
/// interned into a new `Sym`; this mirrors `StringConcat`'s own
/// Surface-not-Str choice. Object pairs are canonically ordered with
/// `cmp_value`, the same invariant `MkDict` maintains.
fn json_to_value(j: &serde_json::Value) -> Value {
    match j {
        serde_json::Value::Null => Value::None,
        serde_json::Value::Bool(b) => Value::Bool(*b),
        serde_json::Value::Number(n) => match n.as_i64() {
            Some(i) => Value::Int(i),
            None => Value::Float(n.as_f64().unwrap_or(0.0)),
        },
        serde_json::Value::String(s) => Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes())),
        serde_json::Value::Array(items) => Value::Tuple(Arc::new(
            items
                .iter()
                .map(json_to_value)
                .collect::<SmallVec<[Value; 4]>>(),
        )),
        serde_json::Value::Object(map) => {
            let mut pairs: Vec<(Value, Value)> = map
                .iter()
                .map(|(k, v)| {
                    (
                        Value::Surface(SurfaceKind::Text, Arc::from(k.as_bytes())),
                        json_to_value(v),
                    )
                })
                .collect();
            pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
            Value::Dict(Arc::from(pairs))
        }
    }
}

/// Read a key from a Dict's pairs, treating `Str` and `Surface(Text)`
/// keys uniformly (a tree parsed by `json_to_value` carries
/// Surface(Text) keys; a tree authored by literal `MkDict(Lit("type"),
/// ...)` calls carries `Str` keys -- both must compare equal to a plain
/// `&str` here).
fn dict_get<'a>(pairs: &'a [(Value, Value)], key: &str, interner: &Interner) -> Option<&'a Value> {
    pairs.iter().find_map(|(k, v)| {
        let matches = match k {
            Value::Str(s) => interner.resolve(*s) == key,
            Value::Surface(SurfaceKind::Text, b) => b.as_ref() == key.as_bytes(),
            _ => false,
        };
        if matches {
            Some(v)
        } else {
            None
        }
    })
}

/// Read a Dict's own `"type"` field as `&str`, string-like-coerced
/// (`Str` or `Surface(Text)`) same as `dict_get`'s keys.
fn dict_type_str<'a>(
    pairs: &'a [(Value, Value)],
    interner: &'a Interner,
) -> Option<std::borrow::Cow<'a, str>> {
    match dict_get(pairs, "type", interner)? {
        Value::Str(s) => Some(std::borrow::Cow::Borrowed(interner.resolve(*s))),
        Value::Surface(SurfaceKind::Text, b) => Some(String::from_utf8_lossy(b)),
        _ => None,
    }
}

/// String-like coercion (`Str` or `Surface(Text)`) to an owned `String`
/// -- used by `DictGet` to compare its `key` argument against a Dict's
/// pairs uniformly regardless of which of the two shapes either side is.
pub(crate) fn str_like_owned(v: &Value, interner: &Interner) -> Option<String> {
    match v {
        Value::Str(s) => Some(interner.resolve(*s).to_string()),
        Value::Surface(SurfaceKind::Text, b) => Some(String::from_utf8_lossy(b).into_owned()),
        _ => None,
    }
}

// ---------------------------------------------------------------------------
// arc6 tier-0 `fix:StringAsSequence` — A STRING IS A SEQUENCE OF CHARACTERS.
//
// PROGRAM_SYNTHESIS_ARC6_STRUCTURAL_CEILING.md §3.1 S1 measured, four ways,
// that a string was ATOMIC in this value domain: `Count("abc") -> 0`,
// `IndexAt("abc", 1) -> None`, `Last("abc") -> None`, `In("a","cat") ->
// false`.  Those four Terms are shipped and correctly NAMED; only their
// TYPE COVERAGE was missing.  This is the one tier-0 unit that is a
// SEMANTIC CHANGE to shipped Terms rather than an addition, so its blast
// radius is deliberately made as small as it can be while still being the
// named unit:
//
//   * ONLY the four arms `Count` / `IndexAt` / `Last` / `In` are touched.
//     `Value::len` / `Value::snapshot` / `Value::contains` / `Value::iter`
//     are NOT touched — a change there would make every reduction, fold,
//     filter and map silently iterate strings too, which is a different
//     (much larger) unit and is NOT in scope.
//   * Every arm added here replaces a DEGENERATE answer (`0` / `None` /
//     `false`) with the right one.  No non-degenerate shipped behaviour
//     changes.  In particular `Count(Surface(Text, ..))` already answered
//     with its BYTE length (`Value::len`) and is left exactly as it was —
//     only `Value::Str`, which answered `0`, gains the character count.
//   * A character comes back as `Surface(SurfaceKind::Text, ..)`, never an
//     interned `Value::Str`: `EvalCtx` holds `&Interner` (the documented
//     immutable-at-eval-time discipline), so minting a Sym here is not
//     available.  `str_like_owned` / `eq_with_string_coercion` /
//     `SynthEnumerate::canon` all already treat the two text forms
//     identically, so this is the same convention the engine already uses
//     for every text value it constructs.
// ---------------------------------------------------------------------------

/// The characters of a TEXT value, or `None` for every other Value — so a
/// caller's existing non-text path is reached bit-for-bit unchanged.
fn text_chars(v: &Value, interner: &Interner) -> Option<Vec<char>> {
    match v {
        Value::Str(s) => Some(interner.resolve(*s).chars().collect()),
        Value::Surface(SurfaceKind::Text, b) => Some(String::from_utf8_lossy(b).chars().collect()),
        _ => None,
    }
}

/// One character as a text Value (see the module note above on why this is
/// a `Surface(Text)` and not an interned `Str`).
fn char_value(c: char) -> Value {
    let mut buf = [0u8; 4];
    let s: &str = c.encode_utf8(&mut buf);
    Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes()))
}

/// snake_case an identifier-ish string (the `SnakeCase` Term's engine):
/// a lowercase/uppercase camel boundary inserts `_`; every run of
/// non-alphanumeric characters collapses to ONE `_`; ASCII letters
/// lowercase; leading/trailing `_` trimmed. Pure text — no interner.
pub(crate) fn snake_case_str(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 4);
    let mut prev_lower_or_digit = false;
    let mut pending_sep = false;
    for ch in s.chars() {
        if ch.is_alphanumeric() {
            if ch.is_uppercase() {
                if prev_lower_or_digit && !out.is_empty() {
                    pending_sep = true;
                }
                if pending_sep && !out.is_empty() {
                    out.push('_');
                }
                pending_sep = false;
                for lc in ch.to_lowercase() {
                    out.push(lc);
                }
                prev_lower_or_digit = false;
            } else {
                if pending_sep && !out.is_empty() {
                    out.push('_');
                }
                pending_sep = false;
                out.push(ch);
                prev_lower_or_digit = true;
            }
        } else {
            // Any separator run -> at most one underscore, never leading.
            if !out.is_empty() {
                pending_sep = true;
            }
            prev_lower_or_digit = false;
        }
    }
    out
}

/// `DictGet`'s lookup: find the first pair in `pairs` whose key matches
/// `key`, comparing string-like keys (`Str`/`Surface(Text)`) by their
/// resolved text so a `MkDict`-built (`Str`-keyed) Dict and a
/// `FromJsonString`-parsed (`Surface`-keyed) Dict both work; falls back
/// to plain `Value` equality for non-string-like keys.
fn dict_get_by_value<'a>(
    pairs: &'a [(Value, Value)],
    key: &Value,
    interner: &Interner,
) -> Option<&'a Value> {
    let key_s = str_like_owned(key, interner);
    pairs.iter().find_map(|(k, v)| {
        let matches = match (&key_s, str_like_owned(k, interner)) {
            (Some(a), Some(b)) => *a == b,
            _ => k == key,
        };
        if matches {
            Some(v)
        } else {
            None
        }
    })
}

/// The recursive walk `ShiftThresholdLits` performs -- see the
/// TermNode variant's doc comment for the exact semantics. Deep-copies
/// `v`; only `Lt`/`Gt` Dict nodes whose own `"b"` is a numeric `Lit`
/// are touched, and only that Lit's `"value"` entry changes.
pub(crate) fn shift_threshold_lits_value(v: &Value, shift: f64, interner: &Interner) -> Value {
    match v {
        Value::Dict(pairs) => {
            // Deep-copy every entry first (recurses into "a", "items",
            // nested predicates, etc. -- wherever a further Lt/Gt lives).
            let mut new_pairs: Vec<(Value, Value)> = pairs
                .iter()
                .map(|(k, val)| (k.clone(), shift_threshold_lits_value(val, shift, interner)))
                .collect();
            let ty = dict_type_str(&new_pairs, interner);
            let is_lt = ty.as_deref() == Some("Lt");
            let is_gt = ty.as_deref() == Some("Gt");
            if is_lt || is_gt {
                // The recursed "b" is still the identical Lit copy (a bare
                // Lit dict has no Lt/Gt inside it to have changed) -- read
                // it back out of new_pairs and, if it's a numeric Lit,
                // rewrite its "value" in place.
                let shifted_b = new_pairs.iter().find_map(|(k, val)| {
                    let is_b = match k {
                        Value::Str(s) => interner.resolve(*s) == "b",
                        Value::Surface(SurfaceKind::Text, b) => b.as_ref() == b"b",
                        _ => false,
                    };
                    if !is_b {
                        return None;
                    }
                    let Value::Dict(bp) = val else {
                        return None;
                    };
                    if dict_type_str(bp, interner).as_deref() != Some("Lit") {
                        return None;
                    }
                    let num = match dict_get(bp, "value", interner)? {
                        Value::Int(n) => *n as f64,
                        Value::Float(f) => *f,
                        _ => return None,
                    };
                    let new_num = if is_lt { num - shift } else { num + shift };
                    let new_bp: Vec<(Value, Value)> = bp
                        .iter()
                        .map(|(bk, bv)| {
                            let is_value_key = match bk {
                                Value::Str(s) => interner.resolve(*s) == "value",
                                Value::Surface(SurfaceKind::Text, b) => b.as_ref() == b"value",
                                _ => false,
                            };
                            if is_value_key {
                                (bk.clone(), Value::Float(new_num))
                            } else {
                                (bk.clone(), bv.clone())
                            }
                        })
                        .collect();
                    Some(Value::Dict(Arc::from(new_bp)))
                });
                if let Some(new_b) = shifted_b {
                    for (k, val) in new_pairs.iter_mut() {
                        let is_b = match k {
                            Value::Str(s) => interner.resolve(*s) == "b",
                            Value::Surface(SurfaceKind::Text, b) => b.as_ref() == b"b",
                            _ => false,
                        };
                        if is_b {
                            *val = new_b.clone();
                        }
                    }
                }
            }
            Value::Dict(Arc::from(new_pairs))
        }
        Value::Tuple(items) | Value::List(items) =>
        // KIND-PRESERVING (see `Value::reseq`)
        {
            v.reseq(
                items
                    .iter()
                    .map(|x| shift_threshold_lits_value(x, shift, interner))
                    .collect::<SmallVec<[Value; 4]>>(),
            )
        }
        other => other.clone(),
    }
}

/// The recursive walk `RewriteTreeNodes` performs -- see the TermNode
/// variant's doc comment for the exact semantics. Deep-copies `v`,
/// recursing into a Dict node's children FIRST (same order
/// `shift_threshold_lits_value` uses), then -- if `type_filter` is
/// `None` or matches the node's own (already-recursed) `"type"` field --
/// looks up its `field` entry's current value in `value_map` and, if
/// found, replaces ONLY that field's value.
pub(crate) fn rewrite_tree_nodes_value(
    v: &Value,
    type_filter: Option<&str>,
    field: &str,
    value_map: &[(Value, Value)],
    interner: &Interner,
) -> Value {
    fn key_is<'a>(k: &Value, name: &str, interner: &Interner) -> bool {
        match k {
            Value::Str(s) => interner.resolve(*s) == name,
            Value::Surface(SurfaceKind::Text, b) => b.as_ref() == name.as_bytes(),
            _ => false,
        }
    }

    match v {
        Value::Dict(pairs) => {
            let mut new_pairs: Vec<(Value, Value)> = pairs
                .iter()
                .map(|(k, val)| {
                    (
                        k.clone(),
                        rewrite_tree_nodes_value(val, type_filter, field, value_map, interner),
                    )
                })
                .collect();
            let guard_ok = match type_filter {
                Some(tf) => dict_type_str(&new_pairs, interner).as_deref() == Some(tf),
                None => true,
            };
            if guard_ok {
                let cur = new_pairs.iter().find_map(|(k, val)| {
                    if key_is(k, field, interner) {
                        Some(val.clone())
                    } else {
                        None
                    }
                });
                if let Some(cur_val) = cur {
                    if let Some(new_val) = dict_get_by_value(value_map, &cur_val, interner).cloned()
                    {
                        for (k, val) in new_pairs.iter_mut() {
                            if key_is(k, field, interner) {
                                *val = new_val.clone();
                            }
                        }
                    }
                }
            }
            Value::Dict(Arc::from(new_pairs))
        }
        Value::Tuple(items) | Value::List(items) =>
        // KIND-PRESERVING (see `Value::reseq`)
        {
            v.reseq(
                items
                    .iter()
                    .map(|x| rewrite_tree_nodes_value(x, type_filter, field, value_map, interner))
                    .collect::<SmallVec<[Value; 4]>>(),
            )
        }
        other => other.clone(),
    }
}

/// The recursive walk `AttrKeyRanking` performs -- see the TermNode
/// variant's doc comment for the exact semantics. Read-only (never
/// mutates `v`): tallies every `{"type":"Attr","key":<str>}` node's
/// `key` value via an `FxHashMap`, recursing into a Dict node's children
/// and a Tuple's items (the SAME walk `rewrite_tree_nodes_value` uses),
/// then returns the `(-count, key)`-sorted ranking as an ORDERED
/// `Value::Tuple` of `(key: Surface(Text), count: Int)` pairs --
/// IDENTICAL to `domains/edit_ops.py`'s `find_attr_keys`.
pub(crate) fn attr_key_ranking_value(v: &Value, interner: &Interner) -> Value {
    fn walk(v: &Value, counts: &mut FxHashMap<String, i64>, interner: &Interner) {
        match v {
            Value::Dict(pairs) => {
                if dict_type_str(pairs, interner).as_deref() == Some("Attr") {
                    if let Some(kv) = dict_get(pairs, "key", interner) {
                        if let Some(ks) = str_like_owned(kv, interner) {
                            *counts.entry(ks).or_insert(0) += 1;
                        }
                    }
                }
                for (_, val) in pairs.iter() {
                    walk(val, counts, interner);
                }
            }
            Value::Tuple(items) | Value::List(items) => {
                for it in items.iter() {
                    walk(it, counts, interner);
                }
            }
            _ => {}
        }
    }

    let mut counts: FxHashMap<String, i64> = FxHashMap::default();
    walk(v, &mut counts, interner);
    let mut ranked: Vec<(String, i64)> = counts.into_iter().collect();
    // Python's `sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))`:
    // descending count, ascending key as tiebreak.
    ranked.sort_by(|a, b| b.1.cmp(&a.1).then_with(|| a.0.cmp(&b.0)));
    let pairs: SmallVec<[Value; 4]> = ranked
        .into_iter()
        .map(|(k, c)| {
            Value::Tuple(Arc::new(smallvec![
                Value::Surface(SurfaceKind::Text, Arc::from(k.into_bytes())),
                Value::Int(c),
            ]))
        })
        .collect();
    Value::Tuple(Arc::new(pairs))
}

// --- GRAPH LAW #6: trans-frame identity (domain-general) -------------
//
// The pure matching core behind `TermNode::TrackIdentityCorrespondence`
// (read-only) AND `Substrate::track_identity` (its mutating twin in
// substrate.rs, which calls this then writes the `identity` attr).
// Generalises `Substrate::segment_and_track`'s cell-overlap +
// nearest-centroid cross-frame matching (substrate.rs — untouched,
// still pixel/centroid-specific) to an ARBITRARY feature space: any
// node with a `feature_key` attr readable as a number-vector can be
// tracked, not just grid regions.

/// One item's data for trans-frame identity matching, read straight off
/// a graph node's attrs.
struct TrackFeature {
    nid: NodeID,
    category: Value,
    features: Vec<f64>,
    extent: Vec<Value>,
    has_extent: bool,
}

fn read_track_feature(
    graph: &TypedGraph,
    nid: NodeID,
    feature_key: Sym,
    category_key: Option<Sym>,
    extent_key: Option<Sym>,
) -> TrackFeature {
    let attrs = &graph.node(nid).attrs;
    crate::access_trace::note(2, nid.0, feature_key.0, crate::access_trace::NO_ID);
    let features: Vec<f64> = match attrs.get(&feature_key) {
        Some(v @ (Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_))) => {
            v.iter().map(|x| x.as_f64()).collect()
        }
        Some(other) => vec![other.as_f64()],
        None => Vec::new(),
    };
    let category = category_key
        .and_then(|k| {
            crate::access_trace::note(2, nid.0, k.0, crate::access_trace::NO_ID);
            attrs.get(&k).cloned()
        })
        .unwrap_or(Value::None);
    let (extent, has_extent) = match extent_key.and_then(|k| {
        crate::access_trace::note(2, nid.0, k.0, crate::access_trace::NO_ID);
        attrs.get(&k)
    }) {
        Some(v @ (Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_))) => {
            (v.iter().cloned().collect(), true)
        }
        _ => (Vec::new(), false),
    };
    TrackFeature {
        nid,
        category,
        features,
        extent,
        has_extent,
    }
}

/// Euclidean distance over two feature vectors of possibly different
/// length (missing trailing dims treated as 0.0 — a defensive default,
/// not expected in well-formed callers).
fn feature_distance(a: &[f64], b: &[f64]) -> f64 {
    let n = a.len().max(b.len());
    let mut acc = 0.0f64;
    for i in 0..n {
        let d = a.get(i).copied().unwrap_or(0.0) - b.get(i).copied().unwrap_or(0.0);
        acc += d * d;
    }
    acc.sqrt()
}

/// Multiset intersection count between two extents. `Value` isn't
/// `Hash` (Float defeats it), so this is an O(n*m) equality scan —
/// fine at `segment_and_track`'s scale (small per-item extents), and
/// mirrors its own `HashSet::intersection` for the common no-duplicate
/// case exactly while still being correct for a true multiset.
fn extent_overlap(a: &[Value], b: &[Value]) -> usize {
    let mut used = vec![false; b.len()];
    let mut count = 0usize;
    for av in a {
        if let Some(j) = b
            .iter()
            .enumerate()
            .position(|(j, bv)| !used[j] && bv == av)
        {
            used[j] = true;
            count += 1;
        }
    }
    count
}

/// Domain-general trans-frame identity correspondence between two
/// Node collections. See `TermNode::TrackIdentityCorrespondence`'s doc
/// for the full contract (overlap-first, nearest-feature-vector
/// fallback within `radius`, greedy no-reuse, category gate). Pure —
/// takes `&TypedGraph`, writes nothing.
pub struct TrackIdentityMatch {
    pub matched: Vec<(NodeID, NodeID)>,
    pub births: Vec<NodeID>,
    pub deaths: Vec<NodeID>,
}

pub fn track_identity_correspondence(
    graph: &TypedGraph,
    prev_ids: &[NodeID],
    cur_ids: &[NodeID],
    feature_key: Sym,
    category_key: Option<Sym>,
    extent_key: Option<Sym>,
    radius: f64,
) -> TrackIdentityMatch {
    let priors: Vec<TrackFeature> = prev_ids
        .iter()
        .filter(|&&n| graph.has_node(n))
        .map(|&n| read_track_feature(graph, n, feature_key, category_key, extent_key))
        .collect();
    let curs: Vec<TrackFeature> = cur_ids
        .iter()
        .filter(|&&n| graph.has_node(n))
        .map(|&n| read_track_feature(graph, n, feature_key, category_key, extent_key))
        .collect();

    let mut used: Vec<bool> = vec![false; priors.len()];
    let mut matched: Vec<(NodeID, NodeID)> = Vec::new();
    let mut births: Vec<NodeID> = Vec::new();

    for cur in &curs {
        let mut best: Option<usize> = None;
        // Phase 1: overlap-first (only when the CURRENT item carries an
        // extent — mirrors segment_and_track's cell-overlap pass).
        if cur.has_extent {
            let mut best_ov = 0usize;
            for (pi, p) in priors.iter().enumerate() {
                if used[pi] || !p.has_extent {
                    continue;
                }
                if category_key.is_some() && p.category != cur.category {
                    continue;
                }
                let ov = extent_overlap(&cur.extent, &p.extent);
                if ov > best_ov {
                    best_ov = ov;
                    best = Some(pi);
                }
            }
            let ov_ok = best.is_some_and(|pi| {
                let m = (cur.extent.len().min(priors[pi].extent.len())) as f64;
                m > 0.0 && 2.0 * (best_ov as f64) >= m
            });
            if !ov_ok {
                best = None;
            }
        }
        // Phase 2: nearest-feature-vector fallback within `radius`.
        if best.is_none() {
            let mut bd = f64::INFINITY;
            let mut bc: Option<usize> = None;
            for (pi, p) in priors.iter().enumerate() {
                if used[pi] {
                    continue;
                }
                if category_key.is_some() && p.category != cur.category {
                    continue;
                }
                let d = feature_distance(&cur.features, &p.features);
                if d < bd {
                    bd = d;
                    bc = Some(pi);
                }
            }
            if let Some(pi) = bc {
                if bd <= radius {
                    best = Some(pi);
                }
            }
        }
        if let Some(pi) = best {
            used[pi] = true;
            matched.push((priors[pi].nid, cur.nid));
        } else {
            births.push(cur.nid);
        }
    }
    let deaths: Vec<NodeID> = priors
        .iter()
        .enumerate()
        .filter(|(pi, _)| !used[*pi])
        .map(|(_, p)| p.nid)
        .collect();

    TrackIdentityMatch {
        matched,
        births,
        deaths,
    }
}

/// `Eq` with string-like coercion: a `Value::Str` (interned symbol) and a
/// `Value::Surface(Text, ..)` (rendered bytes, e.g. from `StringConcat` or a
/// rendering Term) that carry the SAME text are EQUAL in a `where`-clause `Eq`.
/// Without this, `Eq(StringConcat(...), Attr("some string attr"))` never matches
/// (the concat yields `Surface`, the attr is `Str`), forcing rules to wrap both
/// sides in `StringConcat` to reach the `Surface==Surface` arm. The coercion
/// lives HERE, in the Eq evaluator, because `Value::PartialEq` cannot carry it:
/// the `Eq`+`Hash` contract requires equal values to hash equally, but `Str`
/// hashes its `Sym` while `Surface` hashes its bytes, and resolving `Sym`->text
/// needs the interner, which `Hash::hash` has no access to. The Eq evaluator
/// DOES hold the interner, so the coercion is exact and side-effect-free here.
fn eq_with_string_coercion(a: &Value, b: &Value, interner: &Interner) -> bool {
    if a == b {
        return true;
    }
    match (a, b) {
        (Value::Str(s), Value::Surface(SurfaceKind::Text, bytes))
        | (Value::Surface(SurfaceKind::Text, bytes), Value::Str(s)) => {
            interner.resolve(*s).as_bytes() == bytes.as_ref()
        }
        _ => false,
    }
}

/// Set/FrozenSet items, or `None` for any other Value kind — the
/// runtime-type dispatch point for the `&`/`|`/`^` set-algebra overload
/// (Q1 `bitwise_ops`, PROGRAM_SYNTHESIS_ARC2_Q0_HISTOGRAM.md §1 finding:
/// Python overloads bit ops between int and set algebra).
fn as_set_like(v: &Value) -> Option<Arc<[Value]>> {
    match v {
        Value::Set(s) => Some(s.clone()),
        Value::FrozenSet(s) => Some(s.clone()),
        _ => None,
    }
}

/// Build a deduped Set/FrozenSet result, tagged like Python's own
/// `type(a).__and__` convention: the LEFT operand's tag wins.
fn set_result_like(left: &Value, items: Vec<Value>) -> Value {
    if matches!(left, Value::FrozenSet(_)) {
        Value::make_frozenset(items)
    } else {
        Value::make_set(items)
    }
}

fn eval_pareto_dominates(
    graph: &TypedGraph,
    candidate: NodeID,
    alternative: NodeID,
    dimension_count: i64,
    value_edge: Sym,
    measure_edge: Sym,
    dimension_key: Sym,
    verified_key: Sym,
    signed_value_key: Sym,
) -> bool {
    if dimension_count <= 0 || !graph.has_node(candidate) || !graph.has_node(alternative) {
        return false;
    }
    let verified_values = |owner: NodeID| -> Vec<NodeID> {
        graph
            .neighbours(owner, Some(value_edge))
            .into_iter()
            .filter(|value| {
                match graph.node(*value).attrs.get(&verified_key) {
                    Some(Value::Int(1)) => true,
                    // A generic bridge may carry its boolean/numeric marker
                    // in the same scalar representation as its coordinates.
                    Some(Value::Float(v)) => v.is_finite() && *v == 1.0,
                    _ => false,
                }
            })
            .collect()
    };
    let candidate_values = verified_values(candidate);
    let alternative_values = verified_values(alternative);
    if candidate_values.len() != dimension_count as usize
        || alternative_values.len() != dimension_count as usize
    {
        return false;
    }
    // Integer cognition is a contract, not a coercion.  Graph-native
    // consumers sometimes publish an integral measurement through a scalar
    // (for example, a control-regime bridge whose surrounding attrs are
    // floating-point action quanta).  Admit only finite, exactly integral
    // floats at this boundary; non-integral floats remain malformed rather
    // than being silently truncated.
    let as_integer = |value: NodeID| -> Option<i64> {
        match graph.node(value).attrs.get(&signed_value_key) {
            Some(Value::Int(v)) => Some(*v),
            Some(Value::Float(v)) if v.is_finite() && v.fract() == 0.0 => {
                let n = *v as i64;
                if (n as f64) == *v {
                    Some(n)
                } else {
                    None
                }
            }
            _ => None,
        }
    };
    if candidate_values
        .iter()
        .chain(alternative_values.iter())
        .any(|value| as_integer(*value).is_none())
    {
        return false;
    }

    let mut strictly_better = false;
    for candidate_value in candidate_values {
        let candidate_measures = graph.neighbours(candidate_value, Some(measure_edge));
        let candidate_ordinal = graph.node(candidate_value).attrs.get(&dimension_key);
        let Some(candidate_signed) = as_integer(candidate_value) else {
            return false;
        };
        let mut no_worse_match = false;
        for alternative_value in alternative_values.iter().copied() {
            let alternative_measures = graph.neighbours(alternative_value, Some(measure_edge));
            let same_dimension = if candidate_measures.is_empty() && alternative_measures.is_empty()
            {
                candidate_ordinal.is_some()
                    && candidate_ordinal == graph.node(alternative_value).attrs.get(&dimension_key)
            } else {
                candidate_measures
                    .iter()
                    .any(|goal| alternative_measures.contains(goal))
            };
            if !same_dimension {
                continue;
            }
            let Some(alternative_signed) = as_integer(alternative_value) else {
                return false;
            };
            if alternative_signed >= candidate_signed {
                no_worse_match = true;
                strictly_better |= alternative_signed > candidate_signed;
            }
        }
        if !no_worse_match {
            return false;
        }
    }
    strictly_better
}

pub fn evaluate(arena: &TermArena, idx: TermIdx, env: &mut Env, ctx: &mut EvalCtx) -> Value {
    // Macro to read a SmallVec cache key for Filter. Built once per call.
    macro_rules! cache_key {
        ($env:expr, $vars:expr) => {{
            let mut key: SmallVec<[(Sym, Value); 4]> = SmallVec::new();
            for v in $vars {
                if let Some(val) = env_get($env, *v) {
                    key.push((*v, val.clone()));
                }
            }
            key.sort_by(|a, b| a.0.cmp(&b.0));
            key
        }};
    }

    let node = arena.get(idx);

    // SCALE AUDIT — TERM EVALUATION (`scale_audit.rs`, T section;
    // `VISION_TERM_EVAL_COUNTER_PREREG.md` §2.1). THE choke point: every Term
    // evaluation in the engine, of every variant, passes through this `match`,
    // and every sub-term recurses back through it. Counting here makes coverage
    // STRUCTURAL rather than remembered — the same argument that made the rest of
    // this module process-global atomics, and the direct lesson of eleven inert
    // instruments (PROTOCOL §12, §12.1).
    //
    // The guard also makes `node`'s variant the INNERMOST variant for the
    // duration of the arm, so interior comparison units charged anywhere below
    // (`shape_decode::covers_relation`, …) attribute themselves without their
    // author naming a variant. It is a guard and not a manual restore because
    // several arms below `return` early.
    //
    // DISABLED COST: one `Relaxed` load, `None`, no thread-local touch, no
    // allocation. OFF by default (PROTOCOL §9).
    let _term_audit = crate::scale_audit::term_eval(node.variant_index());

    match node {
        TermNode::Var { name } => env_get(env, *name).cloned().unwrap_or(Value::None),

        TermNode::Lit { value } => value.clone(),

        TermNode::TypeOf { node } => {
            let v = evaluate(arena, *node, env, ctx);
            match v {
                Value::Node(nid) if ctx.graph.has_node(nid) => {
                    let type_sym = ctx.graph.node(nid).type_;
                    crate::access_trace::note(3, nid.0, type_sym.0, crate::access_trace::NO_ID);
                    Value::Str(type_sym)
                }
                _ => Value::None,
            }
        }

        TermNode::Attr { node, key } => {
            let v = evaluate(arena, *node, env, ctx);
            match v {
                Value::Node(nid) if ctx.graph.has_node(nid) => {
                    crate::access_trace::note(2, nid.0, key.0, crate::access_trace::NO_ID);
                    // FALLBACK TRACE (§ VISION_FALLBACK_VOCAB_PREREG). The
                    // `unwrap_or(Value::None)` this replaces is `.get('Name','')`
                    // in the engine core: a rule reading an attribute NO RULE
                    // EVER WROTE gets a silent default, which is exactly how an
                    // ablated `vision_lateral` yields a confident 0.000 with no
                    // trace. The miss arm below is the branch the engine
                    // ALREADY took — the hit arm is unchanged and pays nothing.
                    crate::fallback_trace::note_attr_eval();
                    match ctx.graph.node(nid).attrs.get(key) {
                        Some(found) => found.clone(),
                        None => {
                            crate::fallback_trace::note_defaulted_read(*key);
                            Value::None
                        }
                    }
                }
                _ => Value::None,
            }
        }

        TermNode::UseTool { tool, args } => {
            // Evaluate each arg term to a Value, then dispatch to the
            // registered Python handler under the GIL. The boundary is
            // effectful (calls out to Python) and re-entrant (evaluate ->
            // handler -> possibly back into the substrate). Missing handler
            // / handler error degrades to a safe default inside call_tool —
            // never panics the evaluator.
            let arg_vals: Vec<Value> = args.iter().map(|a| evaluate(arena, *a, env, ctx)).collect();
            let name = ctx.interner.resolve(*tool);
            crate::tools::call_tool(name, &arg_vals, ctx.interner)
        }

        TermNode::SetT { items } => {
            let mut out = Vec::with_capacity(items.len());
            for c in items {
                out.push(evaluate(arena, *c, env, ctx));
            }
            Value::make_frozenset(out)
        }

        TermNode::In { member, container } => {
            try_derivation!(
                ctx,
                arena,
                env,
                "In",
                [("member", *member), ("container", *container)]
            );
            let m = evaluate(arena, *member, env, ctx);
            let c = evaluate(arena, *container, env, ctx);
            // arc6 tier-0 `fix:StringAsSequence` — text-in-text is Python's
            // SUBSTRING test (`"a" in "cat"`), which subsumes the character
            // case.  Only fires when BOTH sides are text; a text member in a
            // Tuple/Set/Dict container keeps the existing element scan, and a
            // non-text member in a text container stays `false` exactly as
            // before (Python raises there; the substrate no-ops).
            if let (Some(hay), Some(needle)) = (
                str_like_owned(&c, ctx.interner),
                str_like_owned(&m, ctx.interner),
            ) {
                return Value::Bool(hay.contains(&needle));
            }
            Value::Bool(c.contains(&m))
        }

        TermNode::Tokenize { text } => {
            let tv = evaluate(arena, *text, env, ctx);
            let Value::Str(sym) = tv else {
                return Value::Tuple(std::sync::Arc::new(smallvec::smallvec![]));
            };
            let s = ctx.interner.resolve(sym);
            let mut positions: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
            let base = s.as_ptr() as usize;
            for tok in s.split_whitespace() {
                let start = (tok.as_ptr() as usize) - base;
                let len = tok.len();
                positions.push(Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                    Value::Int(start as i64),
                    Value::Int(len as i64)
                ])));
            }
            Value::Tuple(std::sync::Arc::new(positions))
        }

        TermNode::FinalToken { text } => {
            let tv = evaluate(arena, *text, env, ctx);
            let Value::Str(sym) = tv else {
                return Value::Tuple(std::sync::Arc::new(smallvec::smallvec![]));
            };
            let s = ctx.interner.resolve(sym);
            let mut positions: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
            let base = s.as_ptr() as usize;
            for tok in s.split_whitespace() {
                let start = (tok.as_ptr() as usize) - base;
                let len = tok.len();
                positions.push(Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                    Value::Int(start as i64),
                    Value::Int(len as i64)
                ])));
            }
            Value::Tuple(std::sync::Arc::new(positions))
        }

        TermNode::Tokenize2 { text } => {
            let tv = evaluate(arena, *text, env, ctx);
            let Value::Str(sym) = tv else {
                return Value::Tuple(std::sync::Arc::new(smallvec::smallvec![]));
            };
            let s = ctx.interner.resolve(sym);
            let mut positions: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
            let base = s.as_ptr() as usize;
            for tok in s.split_whitespace() {
                let start = (tok.as_ptr() as usize) - base;
                let len = tok.len();
                positions.push(Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                    Value::Int(start as i64),
                    Value::Int(len as i64)
                ])));
            }
            Value::Tuple(std::sync::Arc::new(positions))
        }

        TermNode::ReadFile { path } => {
            let pv = evaluate(arena, *path, env, ctx);
            let Value::Str(sym) = pv else {
                return Value::None;
            };
            let p = ctx.interner.resolve(sym);
            match std::fs::read_to_string(p) {
                Ok(contents) => Value::Surface(
                    SurfaceKind::Text,
                    std::sync::Arc::from(contents.into_bytes()),
                ),
                Err(_) => Value::None,
            }
        }

        TermNode::StringIndexOf { haystack, needle } => {
            // Both text representations are admissible: an interned Str
            // (Python-written attrs) AND a Surface(Text) (rule-effect
            // StringConcat output). Same acceptance MorphHead/StringConcat
            // already have — string search over the runtime's two text forms.
            let hv = evaluate(arena, *haystack, env, ctx);
            let nv = evaluate(arena, *needle, env, ctx);
            let h: String = match hv {
                Value::Str(sym) => ctx.interner.resolve(sym).to_string(),
                Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(&b).into_owned(),
                _ => return Value::Int(-1),
            };
            let n: String = match nv {
                Value::Str(sym) => ctx.interner.resolve(sym).to_string(),
                Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(&b).into_owned(),
                _ => return Value::Int(-1),
            };
            match h.find(&n) {
                Some(off) => Value::Int(off as i64),
                None => Value::Int(-1),
            }
        }

        TermNode::StringSlice { s, start, end } => {
            let sv = evaluate(arena, *s, env, ctx);
            let Value::Str(sym) = sv else {
                return Value::Surface(SurfaceKind::Text, std::sync::Arc::from(&[][..]));
            };
            let bytes = ctx.interner.resolve(sym).as_bytes();
            let len = bytes.len() as i64;
            let start_v = evaluate(arena, *start, env, ctx);
            let end_v = evaluate(arena, *end, env, ctx);
            let (Value::Int(sr), Value::Int(er)) = (start_v, end_v) else {
                return Value::Surface(SurfaceKind::Text, std::sync::Arc::from(&[][..]));
            };
            let s_clamped = sr.max(0).min(len) as usize;
            let e_clamped = er.max(0).min(len) as usize;
            let (lo, hi) = if s_clamped <= e_clamped {
                (s_clamped, e_clamped)
            } else {
                (s_clamped, s_clamped)
            };
            Value::Surface(SurfaceKind::Text, std::sync::Arc::from(&bytes[lo..hi]))
        }

        TermNode::StringConcat { parts } => {
            let mut out: Vec<u8> = Vec::new();
            for c in parts {
                let v = evaluate(arena, *c, env, ctx);
                match v {
                    Value::Str(sym) => out.extend_from_slice(ctx.interner.resolve(sym).as_bytes()),
                    Value::Surface(SurfaceKind::Text, b) => out.extend_from_slice(&b),
                    _ => {}
                }
            }
            Value::Surface(SurfaceKind::Text, std::sync::Arc::from(out))
        }

        // -------------------------------------------------------------
        // Rung 1 Tier-1 stdlib Term ports (see the variant doc comments
        // above for provenance/semantics of each).
        // -------------------------------------------------------------
        TermNode::Replace { text, old, new } => {
            let tv = evaluate(arena, *text, env, ctx);
            let ov = evaluate(arena, *old, env, ctx);
            let nv = evaluate(arena, *new, env, ctx);
            let (Some(t), Some(o), Some(n)) = (
                str_like_owned(&tv, ctx.interner),
                str_like_owned(&ov, ctx.interner),
                str_like_owned(&nv, ctx.interner),
            ) else {
                return Value::Surface(SurfaceKind::Text, std::sync::Arc::from(&[][..]));
            };
            Value::Surface(
                SurfaceKind::Text,
                std::sync::Arc::from(t.replace(o.as_str(), &n).into_bytes()),
            )
        }

        TermNode::Str { value } => {
            let v = evaluate(arena, *value, env, ctx);
            Value::Surface(
                SurfaceKind::Text,
                std::sync::Arc::from(crate::prog_eval::py_str(&v, ctx.interner).into_bytes()),
            )
        }

        TermNode::Split { text, sep } => {
            let tv = evaluate(arena, *text, env, ctx);
            let Some(t) = str_like_owned(&tv, ctx.interner) else {
                return Value::List(std::sync::Arc::new(smallvec::smallvec![]));
            };
            let sv = evaluate(arena, *sep, env, ctx);
            let sep_s = str_like_owned(&sv, ctx.interner);
            let parts: Vec<String> = match sep_s {
                Some(s) if !s.is_empty() => t.split(s.as_str()).map(|p| p.to_string()).collect(),
                // No separator, or an empty one -- Python's no-arg
                // whitespace-split (an empty-string `sep` is a raise in
                // CPython; this engine has no error channel for a
                // candidate term, so it degrades to the safe default
                // rather than trapping).
                _ => t.split_whitespace().map(|p| p.to_string()).collect(),
            };
            let out: smallvec::SmallVec<[Value; 4]> = parts
                .into_iter()
                .map(|p| Value::Surface(SurfaceKind::Text, std::sync::Arc::from(p.into_bytes())))
                .collect();
            Value::List(std::sync::Arc::new(out))
        }

        TermNode::StrCount { text, sub } => {
            let tv = evaluate(arena, *text, env, ctx);
            let sv = evaluate(arena, *sub, env, ctx);
            let (Some(t), Some(s)) = (
                str_like_owned(&tv, ctx.interner),
                str_like_owned(&sv, ctx.interner),
            ) else {
                return Value::Int(0);
            };
            let n = if s.is_empty() {
                t.chars().count() as i64 + 1
            } else {
                t.matches(s.as_str()).count() as i64
            };
            Value::Int(n)
        }

        TermNode::Round { value, ndigits } => {
            let v = evaluate(arena, *value, env, ctx);
            let nd = evaluate(arena, *ndigits, env, ctx).as_i64() as i32;
            match v {
                Value::Int(n) if nd >= 0 => Value::Int(n),
                Value::Int(n) => {
                    Value::Int(crate::prog_eval::round_half_even_digits(n as f64, nd) as i64)
                }
                Value::Float(f) => Value::Float(crate::prog_eval::round_half_even_digits(f, nd)),
                Value::Bool(b) => {
                    let n = if b { 1 } else { 0 };
                    if nd >= 0 {
                        Value::Int(n)
                    } else {
                        Value::Int(crate::prog_eval::round_half_even_digits(n as f64, nd) as i64)
                    }
                }
                Value::Rational(n, d) => Value::Float(crate::prog_eval::round_half_even_digits(
                    n as f64 / d as f64,
                    nd,
                )),
                _ => Value::None,
            }
        }

        TermNode::Reverse { seq } => {
            let v = evaluate(arena, *seq, env, ctx);
            match v {
                Value::Str(sym) => {
                    let s = ctx.interner.resolve(sym);
                    let rev: String = s.chars().rev().collect();
                    Value::Surface(SurfaceKind::Text, std::sync::Arc::from(rev.into_bytes()))
                }
                Value::Surface(SurfaceKind::Text, b) => {
                    let s = String::from_utf8_lossy(&b);
                    let rev: String = s.chars().rev().collect();
                    Value::Surface(SurfaceKind::Text, std::sync::Arc::from(rev.into_bytes()))
                }
                Value::List(items) => {
                    let mut v: Vec<Value> = items.iter().cloned().collect();
                    v.reverse();
                    Value::List(std::sync::Arc::new(v.into_iter().collect()))
                }
                Value::Tuple(items) => {
                    let mut v: Vec<Value> = items.iter().cloned().collect();
                    v.reverse();
                    Value::Tuple(std::sync::Arc::new(v.into_iter().collect()))
                }
                other => other,
            }
        }

        TermNode::IndexedMap {
            source,
            item_name,
            index_name,
            value,
        } => {
            let s = evaluate(arena, *source, env, ctx);
            let snap = s.snapshot();
            let mut out: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
            for (i, it_ref) in snap.iter().enumerate() {
                env.push((*item_name, it_ref.clone()));
                env.push((*index_name, Value::Int(i as i64)));
                let v = evaluate(arena, *value, env, ctx);
                env.pop();
                env.pop();
                out.push(v);
            }
            Value::List(std::sync::Arc::new(out))
        }

        TermNode::Capitalize { text } => {
            let tv = evaluate(arena, *text, env, ctx);
            let Some(t) = str_like_owned(&tv, ctx.interner) else {
                return Value::Surface(SurfaceKind::Text, std::sync::Arc::from(&[][..]));
            };
            let mut chars = t.chars();
            let out = match chars.next() {
                Some(c) => c.to_uppercase().collect::<String>() + &chars.as_str().to_lowercase(),
                None => String::new(),
            };
            Value::Surface(SurfaceKind::Text, std::sync::Arc::from(out.into_bytes()))
        }

        TermNode::ParseInt { text } => {
            let tv = evaluate(arena, *text, env, ctx);
            let Some(t) = str_like_owned(&tv, ctx.interner) else {
                return Value::None;
            };
            match t.trim().parse::<i64>() {
                Ok(n) => Value::Int(n),
                Err(_) => Value::None,
            }
        }

        TermNode::Slice { seq, start, stop } => {
            let sv = evaluate(arena, *seq, env, ctx);
            let start_v = evaluate(arena, *start, env, ctx);
            let stop_v = evaluate(arena, *stop, env, ctx);
            let start_i = match start_v {
                Value::Int(n) => Some(n),
                Value::None => None,
                other => Some(other.as_i64()),
            };
            let stop_i = match stop_v {
                Value::Int(n) => Some(n),
                Value::None => None,
                other => Some(other.as_i64()),
            };
            match sv {
                Value::Str(sym) => {
                    let chars: Vec<char> = ctx.interner.resolve(sym).chars().collect();
                    let n = chars.len() as i64;
                    let idxs = crate::prog_eval::slice_indices(n, start_i, stop_i, 1);
                    let out: String = idxs.iter().map(|&i| chars[i as usize]).collect();
                    Value::Surface(SurfaceKind::Text, std::sync::Arc::from(out.into_bytes()))
                }
                Value::Surface(SurfaceKind::Text, b) => {
                    let s = String::from_utf8_lossy(&b);
                    let chars: Vec<char> = s.chars().collect();
                    let n = chars.len() as i64;
                    let idxs = crate::prog_eval::slice_indices(n, start_i, stop_i, 1);
                    let out: String = idxs.iter().map(|&i| chars[i as usize]).collect();
                    Value::Surface(SurfaceKind::Text, std::sync::Arc::from(out.into_bytes()))
                }
                Value::List(items) => {
                    let n = items.len() as i64;
                    let idxs = crate::prog_eval::slice_indices(n, start_i, stop_i, 1);
                    let out: smallvec::SmallVec<[Value; 4]> =
                        idxs.iter().map(|&i| items[i as usize].clone()).collect();
                    Value::List(std::sync::Arc::new(out))
                }
                Value::Tuple(items) => {
                    let n = items.len() as i64;
                    let idxs = crate::prog_eval::slice_indices(n, start_i, stop_i, 1);
                    let out: smallvec::SmallVec<[Value; 4]> =
                        idxs.iter().map(|&i| items[i as usize].clone()).collect();
                    Value::Tuple(std::sync::Arc::new(out))
                }
                _ => Value::Surface(SurfaceKind::Text, std::sync::Arc::from(&[][..])),
            }
        }

        TermNode::Sort { seq } => {
            let v = evaluate(arena, *seq, env, ctx);
            match v {
                Value::List(items) => {
                    let mut v: Vec<Value> = items.iter().cloned().collect();
                    v.sort_by(|a, b| crate::value::cmp_value_lex(a, b, ctx.interner));
                    Value::List(std::sync::Arc::new(v.into_iter().collect()))
                }
                Value::Tuple(items) => {
                    let mut v: Vec<Value> = items.iter().cloned().collect();
                    v.sort_by(|a, b| crate::value::cmp_value_lex(a, b, ctx.interner));
                    Value::Tuple(std::sync::Arc::new(v.into_iter().collect()))
                }
                other => other,
            }
        }

        TermNode::DictItems { seq } => {
            let v = evaluate(arena, *seq, env, ctx);
            match v {
                Value::Dict(pairs) => {
                    // Python's `dict.items()`/`list(d.items())`: the OUTER
                    // container is a List (matches `Counter.most_common()`'s
                    // own return type, and the `__list__`/`__tuple__` wire
                    // tags a real MBPP spec's list-of-tuples output carries
                    // through the `Lit` boundary — see PREREG/RESULTS §
                    // "container type", found live, not assumed); each
                    // (key, value) PAIR is a genuine 2-tuple.
                    let out: smallvec::SmallVec<[Value; 4]> = pairs
                        .iter()
                        .map(|(k, val)| {
                            let tup: SmallVec<[Value; 4]> = smallvec![k.clone(), val.clone()];
                            Value::Tuple(std::sync::Arc::new(tup))
                        })
                        .collect();
                    Value::List(std::sync::Arc::new(out))
                }
                other => other,
            }
        }

        TermNode::SortBy {
            source,
            var_name,
            key,
        } => {
            let s = evaluate(arena, *source, env, ctx);
            match s {
                Value::List(items) => {
                    let mut keyed: Vec<(Value, Value)> = items
                        .iter()
                        .map(|it_ref| {
                            env.push((*var_name, it_ref.clone()));
                            let k = evaluate(arena, *key, env, ctx);
                            env.pop();
                            (k, it_ref.clone())
                        })
                        .collect();
                    keyed.sort_by(|a, b| crate::value::cmp_value_lex(&a.0, &b.0, ctx.interner));
                    let out: smallvec::SmallVec<[Value; 4]> =
                        keyed.into_iter().map(|(_, v)| v).collect();
                    Value::List(std::sync::Arc::new(out))
                }
                Value::Tuple(items) => {
                    let mut keyed: Vec<(Value, Value)> = items
                        .iter()
                        .map(|it_ref| {
                            env.push((*var_name, it_ref.clone()));
                            let k = evaluate(arena, *key, env, ctx);
                            env.pop();
                            (k, it_ref.clone())
                        })
                        .collect();
                    keyed.sort_by(|a, b| crate::value::cmp_value_lex(&a.0, &b.0, ctx.interner));
                    let out: smallvec::SmallVec<[Value; 4]> =
                        keyed.into_iter().map(|(_, v)| v).collect();
                    Value::Tuple(std::sync::Arc::new(out))
                }
                other => other,
            }
        }

        TermNode::GroupCount { seq } => {
            let v = evaluate(arena, *seq, env, ctx);
            let items: Option<smallvec::SmallVec<[Value; 4]>> = match &v {
                Value::List(items) => Some(items.iter().cloned().collect()),
                Value::Tuple(items) => Some(items.iter().cloned().collect()),
                _ => None,
            };
            match items {
                Some(items) => {
                    let mut counts: Vec<(Value, i64)> = Vec::new();
                    for it in items.iter() {
                        match counts.iter_mut().find(|(k, _)| k == it) {
                            Some(entry) => entry.1 += 1,
                            None => counts.push((it.clone(), 1)),
                        }
                    }
                    let mut pairs: Vec<(Value, Value)> = counts
                        .into_iter()
                        .map(|(k, c)| (k, Value::Int(c)))
                        .collect();
                    pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
                    Value::Dict(std::sync::Arc::from(pairs))
                }
                None => v,
            }
        }

        TermNode::DictMerge { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            match (&av, &bv) {
                (Value::Dict(pa), Value::Dict(pb)) => {
                    let mut out: Vec<(Value, Value)> = pa.iter().cloned().collect();
                    for (k, v) in pb.iter() {
                        match out.iter_mut().find(|(ek, _)| ek == k) {
                            Some(entry) => entry.1 = v.clone(),
                            None => out.push((k.clone(), v.clone())),
                        }
                    }
                    out.sort_by(|x, y| cmp_value(&x.0, &y.0));
                    Value::Dict(std::sync::Arc::from(out))
                }
                _ => av,
            }
        }

        TermNode::ZipWith {
            a,
            b,
            a_name,
            b_name,
            value,
        } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            let a_snap = av.snapshot();
            let b_snap = bv.snapshot();
            let n = a_snap.len().min(b_snap.len());
            let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(n);
            for i in 0..n {
                env.push((*a_name, a_snap[i].clone()));
                env.push((*b_name, b_snap[i].clone()));
                let v = evaluate(arena, *value, env, ctx);
                env.pop();
                env.pop();
                out.push(v);
            }
            av.reseq(out)
        }

        TermNode::MorphHead { text } => {
            let v = evaluate(arena, *text, env, ctx);
            let s: String = match v {
                Value::Str(sym) => ctx.interner.resolve(sym).to_string(),
                Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(&b).into_owned(),
                _ => String::new(),
            };
            let head = match first_morph_boundary(&s) {
                Some((head_end, _)) => &s[..head_end],
                None => &s[..],
            };
            Value::Surface(SurfaceKind::Text, std::sync::Arc::from(head.as_bytes()))
        }
        TermNode::MorphTail { text } => {
            let v = evaluate(arena, *text, env, ctx);
            let s: String = match v {
                Value::Str(sym) => ctx.interner.resolve(sym).to_string(),
                Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(&b).into_owned(),
                _ => String::new(),
            };
            let tail = match first_morph_boundary(&s) {
                Some((_, tail_start)) => &s[tail_start..],
                None => "",
            };
            Value::Surface(SurfaceKind::Text, std::sync::Arc::from(tail.as_bytes()))
        }

        TermNode::Verify {
            term,
            env: env_term,
            expected,
        } => {
            let env_val = evaluate(arena, *env_term, env, ctx);
            let expected_val = evaluate(arena, *expected, env, ctx);
            // Push env bindings if env evaluated to a Dict.
            let pushed = if let Value::Dict(pairs) = &env_val {
                let mut n = 0;
                for (k, v) in pairs.iter() {
                    if let Value::Str(sym) = k {
                        env.push((*sym, v.clone()));
                        n += 1;
                    }
                }
                n
            } else {
                0
            };
            let term_val = evaluate(arena, *term, env, ctx);
            for _ in 0..pushed {
                env.pop();
            }
            Value::Bool(term_val == expected_val)
        }

        TermNode::MkDict { items } => {
            // Alternating (key, value, key, value, ...). Odd trailing
            // key with no value is dropped. Keys must evaluate to
            // Str or Surface(Text); otherwise the pair is skipped.
            let n_pairs = items.len() / 2;
            let mut pairs: Vec<(Value, Value)> = Vec::with_capacity(n_pairs);
            for i in 0..n_pairs {
                let k = evaluate(arena, items[2 * i], env, ctx);
                let v = evaluate(arena, items[2 * i + 1], env, ctx);
                match &k {
                    Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
                        pairs.push((k, v));
                    }
                    _ => { /* non-string key: skip */ }
                }
            }
            // Canonical order — match `decode_value` / Value::Dict
            // construction elsewhere (persist.rs:203 sorts by cmp_value).
            pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
            Value::Dict(std::sync::Arc::from(pairs))
        }

        TermNode::ToJsonString { value } => {
            let v = evaluate(arena, *value, env, ctx);
            let j = value_to_json_for_string(&v, ctx.interner);
            let s = serde_json::to_string(&j).unwrap_or_default();
            Value::Surface(SurfaceKind::Text, std::sync::Arc::from(s.into_bytes()))
        }

        TermNode::FromJsonString { text } => {
            let tv = evaluate(arena, *text, env, ctx);
            let s_owned: String = match &tv {
                Value::Str(sym) => ctx.interner.resolve(*sym).to_string(),
                Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(b).into_owned(),
                _ => return Value::None,
            };
            match serde_json::from_str::<serde_json::Value>(&s_owned) {
                Ok(j) => json_to_value(&j),
                Err(_) => Value::None,
            }
        }

        TermNode::ShiftThresholdLits { tree, shift } => {
            let tv = evaluate(arena, *tree, env, ctx);
            let sv = evaluate(arena, *shift, env, ctx);
            shift_threshold_lits_value(&tv, sv.as_f64(), ctx.interner)
        }

        TermNode::DictGet { dict, key } => {
            let dv = evaluate(arena, *dict, env, ctx);
            let Value::Dict(pairs) = dv else {
                return Value::None;
            };
            let kv = evaluate(arena, *key, env, ctx);
            dict_get_by_value(&pairs, &kv, ctx.interner)
                .cloned()
                .unwrap_or(Value::None)
        }

        TermNode::RewriteTreeNodes {
            tree,
            type_filter,
            field,
            value_map,
        } => {
            let tv = evaluate(arena, *tree, env, ctx);
            let tf_v = type_filter.map(|t| evaluate(arena, t, env, ctx));
            let tf_s = tf_v.as_ref().and_then(|v| str_like_owned(v, ctx.interner));
            let field_v = evaluate(arena, *field, env, ctx);
            let Some(field_s) = str_like_owned(&field_v, ctx.interner) else {
                return tv;
            };
            let vm_v = evaluate(arena, *value_map, env, ctx);
            let Value::Dict(vm_pairs) = vm_v else {
                return tv;
            };
            rewrite_tree_nodes_value(&tv, tf_s.as_deref(), &field_s, &vm_pairs, ctx.interner)
        }

        TermNode::AttrKeyRanking { tree } => {
            let tv = evaluate(arena, *tree, env, ctx);
            attr_key_ranking_value(&tv, ctx.interner)
        }

        TermNode::TextShape { text } => {
            // Evaluate text → owned String, accepting Str or Surface(Text).
            let tv = evaluate(arena, *text, env, ctx);
            let s_owned: String = match &tv {
                Value::Str(sym) => ctx.interner.resolve(*sym).to_string(),
                Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(b).into_owned(),
                _ => String::new(),
            };
            let bytes = s_owned.as_bytes();

            // Single stack-tracking walk:
            //   • track depth via balanced {} [] <>
            //   • track quote state (" and ')
            //   • record top-level kv-separator positions (`:` `=`)
            //     when at depth 0 or 1 (typical for {k:v, ...})
            //   • record top-level sequence-item separators
            //     (`,` at depth 0 or 1; or `\n-` at depth 0)
            //   • track max depth, final balance
            let mut depth: i32 = 0;
            let mut max_depth: i32 = 0;
            let mut brace_o = 0u32;
            let mut brace_c = 0u32;
            let mut brack_o = 0u32;
            let mut brack_c = 0u32;
            let mut angle_o = 0u32;
            let mut angle_c = 0u32;
            let mut in_dq = false; // inside double-quoted string
            let mut in_sq = false; // inside single-quoted string
            let mut has_quotes = false;
            let mut kv_seps: u32 = 0;
            let mut seq_seps: u32 = 0;
            let mut has_newline = false;
            let mut indent_lines = 0u32; // lines that start with spaces (indented)
            let mut total_lines = 1u32;
            let mut at_line_start = true;
            let mut prev_was_newline = false;

            let mut i = 0usize;
            while i < bytes.len() {
                let c = bytes[i];

                // Quote toggles (NOT escaped; the goal is structural,
                // not a string parser).
                if !in_sq && c == b'"' {
                    has_quotes = true;
                    in_dq = !in_dq;
                    i += 1;
                    continue;
                }
                if !in_dq && c == b'\'' {
                    has_quotes = true;
                    in_sq = !in_sq;
                    i += 1;
                    continue;
                }

                if in_dq || in_sq {
                    if c == b'\n' {
                        total_lines += 1;
                        has_newline = true;
                        at_line_start = true;
                        prev_was_newline = true;
                    } else {
                        at_line_start = false;
                        prev_was_newline = false;
                    }
                    i += 1;
                    continue;
                }

                match c {
                    b'{' => {
                        brace_o += 1;
                        depth += 1;
                        if depth > max_depth {
                            max_depth = depth;
                        }
                    }
                    b'}' => {
                        brace_c += 1;
                        depth -= 1;
                    }
                    b'[' => {
                        brack_o += 1;
                        depth += 1;
                        if depth > max_depth {
                            max_depth = depth;
                        }
                    }
                    b']' => {
                        brack_c += 1;
                        depth -= 1;
                    }
                    b'<' => {
                        // Only treat `<` as an opening angle when it
                        // looks like a tag start (next byte is letter
                        // or `/`). Otherwise it's a comparison op.
                        let nxt = bytes.get(i + 1).copied().unwrap_or(0);
                        if nxt.is_ascii_alphabetic() || nxt == b'/' || nxt == b'!' || nxt == b'?' {
                            angle_o += 1;
                            depth += 1;
                            if depth > max_depth {
                                max_depth = depth;
                            }
                        }
                    }
                    b'>' => {
                        // Close an angle only if we have an unmatched
                        // opening angle (avoids closing the wrong
                        // depth for arithmetic `>`).
                        if angle_o > angle_c {
                            angle_c += 1;
                            depth -= 1;
                        }
                    }
                    b':' | b'=' => {
                        // KV separator at top-level (depth 0) or
                        // immediately inside one container (depth 1).
                        // Skip `==`, `:=`, `<=`, `>=`, `!=` (operators).
                        let prev = if i > 0 { bytes[i - 1] } else { 0 };
                        let nxt = bytes.get(i + 1).copied().unwrap_or(0);
                        let is_op = (c == b'='
                            && (prev == b'='
                                || prev == b'!'
                                || prev == b'<'
                                || prev == b'>'
                                || nxt == b'='
                                || prev == b':'))
                            || (c == b':' && nxt == b'=');
                        if !is_op && (depth == 0 || depth == 1) {
                            kv_seps += 1;
                        }
                    }
                    b',' => {
                        if depth == 0 || depth == 1 {
                            seq_seps += 1;
                        }
                    }
                    b'\n' => {
                        has_newline = true;
                        total_lines += 1;
                        at_line_start = true;
                        prev_was_newline = true;
                        i += 1;
                        continue;
                    }
                    b'-' => {
                        // YAML-style "\n- item" sequence marker
                        // (a `-` at the start of a line, top-level).
                        if at_line_start && depth == 0 {
                            seq_seps += 1;
                        }
                    }
                    b' ' | b'\t' => {
                        // Leading whitespace on a fresh line ⇒
                        // indented (YAML-style structure hint).
                        if prev_was_newline {
                            indent_lines += 1;
                        }
                        i += 1;
                        continue;
                    }
                    _ => {}
                }
                if c != b' ' && c != b'\t' && c != b'\n' {
                    at_line_start = false;
                    prev_was_newline = false;
                }
                i += 1;
            }

            // Classify delimiters family.
            let braces_balanced = brace_o == brace_c;
            let brackets_balanced = brack_o == brack_c;
            let angles_balanced = angle_o == angle_c;
            let any_delim_open = brace_o + brack_o + angle_o;
            let any_delim_close = brace_c + brack_c + angle_c;
            let overall_balanced = braces_balanced && brackets_balanced && angles_balanced;

            let delimiters: &str = if !overall_balanced {
                "unbalanced"
            } else if brace_o >= 1 {
                "braces"
            } else if brack_o >= 1 {
                "brackets"
            } else if angle_o >= 1 {
                "angles"
            } else if any_delim_open == 0
                && any_delim_close == 0
                && has_newline
                && indent_lines >= 1
            {
                "indent"
            } else {
                "flat"
            };

            // Classify kind.
            let has_mapping = kv_seps >= 1;
            let has_sequence = seq_seps >= 1;
            let kind: &str = if has_mapping && has_sequence {
                "nested"
            } else if has_mapping {
                "mapping"
            } else if has_sequence {
                "sequence"
            } else {
                "atomic"
            };

            let whitespace_kind: &str = if has_newline && total_lines > 1 {
                "multiline"
            } else {
                "compact"
            };

            // ---- Natural-language shape features (work for all text) ----
            //
            // Cheap second pass: rough token count via whitespace runs,
            // terminator from last non-whitespace byte, punctuation /
            // case scans, plus case-insensitive ASCII substring scans
            // for negation / connective / question-word / modal,
            // with approximate word-boundary checks.
            let text_length: usize = bytes.len();

            // Token count: whitespace-split words. Count transitions
            // from whitespace (or start) to non-whitespace.
            let mut token_count: u32 = 0;
            let mut in_token = false;
            // Find first / last non-whitespace bytes while we're here.
            let mut first_nws: Option<u8> = None;
            let mut last_nws: u8 = 0;
            let mut has_punctuation = false;
            let mut has_uppercase = false;
            for &b in bytes.iter() {
                let is_ws = b == b' ' || b == b'\t' || b == b'\n' || b == b'\r';
                if !is_ws {
                    if !in_token {
                        token_count += 1;
                        in_token = true;
                    }
                    if first_nws.is_none() {
                        first_nws = Some(b);
                    }
                    last_nws = b;
                    match b {
                        b'.' | b',' | b';' | b':' | b'!' | b'?' | b'(' | b')' => {
                            has_punctuation = true;
                        }
                        _ => {}
                    }
                    if b.is_ascii_uppercase() {
                        has_uppercase = true;
                    }
                } else {
                    in_token = false;
                }
            }

            let terminator: &str = match last_nws {
                b'.' => "period",
                b'?' => "question",
                b'!' => "exclamation",
                _ => "none",
            };

            let starts_capital: bool = first_nws.map(|b| b.is_ascii_uppercase()).unwrap_or(false);

            let avg_token_length: i64 = if token_count > 0 {
                (text_length as i64) / (token_count as i64)
            } else {
                0
            };

            // ---- Case-insensitive word-boundary substring scans ----
            //
            // `lower` is the text lowercased to ASCII (non-ASCII bytes
            // pass through unchanged; safe for our marker words).
            let lower: Vec<u8> = bytes.iter().map(|b| b.to_ascii_lowercase()).collect();

            // A "word-boundary-ish" position requires:
            //   • preceded by whitespace / start / punctuation
            //   • followed by whitespace / end / punctuation
            // Punctuation here = anything that isn't alpha/digit/underscore.
            fn is_word_char(b: u8) -> bool {
                b.is_ascii_alphanumeric() || b == b'_'
            }
            fn boundary_before(buf: &[u8], i: usize) -> bool {
                if i == 0 {
                    return true;
                }
                !is_word_char(buf[i - 1])
            }
            fn boundary_after(buf: &[u8], end: usize) -> bool {
                if end >= buf.len() {
                    return true;
                }
                !is_word_char(buf[end])
            }
            // Find a needle at a word boundary (both sides).
            fn contains_word(buf: &[u8], needle: &[u8]) -> bool {
                if needle.is_empty() || needle.len() > buf.len() {
                    return false;
                }
                let mut i = 0usize;
                while i + needle.len() <= buf.len() {
                    if &buf[i..i + needle.len()] == needle
                        && boundary_before(buf, i)
                        && boundary_after(buf, i + needle.len())
                    {
                        return true;
                    }
                    i += 1;
                }
                false
            }
            // Substring match (no boundary) — used for `n't` and ` no `.
            fn contains_sub(buf: &[u8], needle: &[u8]) -> bool {
                if needle.is_empty() || needle.len() > buf.len() {
                    return false;
                }
                let mut i = 0usize;
                while i + needle.len() <= buf.len() {
                    if &buf[i..i + needle.len()] == needle {
                        return true;
                    }
                    i += 1;
                }
                false
            }

            let has_negation: bool = contains_word(&lower, b"not")
                || contains_sub(&lower, b"n't")
                || contains_sub(&lower, b" no ")
                || contains_word(&lower, b"never")
                || contains_word(&lower, b"none")
                || contains_word(&lower, b"nothing")
                || contains_word(&lower, b"nobody");

            // Connective_kind: first matching category wins. Within each
            // category, scan by earliest occurrence isn't required —
            // category-order is the spec.
            let connective_kind: &str = if contains_word(&lower, b"but")
                || contains_word(&lower, b"however")
                || contains_word(&lower, b"although")
                || contains_word(&lower, b"though")
                || contains_word(&lower, b"yet")
                || contains_word(&lower, b"despite")
            {
                "contrast"
            } else if contains_word(&lower, b"because")
                || contains_word(&lower, b"since")
                || contains_word(&lower, b"therefore")
                || contains_word(&lower, b"thus")
            {
                "causal"
            } else if contains_word(&lower, b"and")
                || contains_word(&lower, b"also")
                || contains_word(&lower, b"plus")
            {
                "conjunction"
            } else {
                "none"
            };

            let has_question_word: bool = contains_word(&lower, b"who")
                || contains_word(&lower, b"what")
                || contains_word(&lower, b"when")
                || contains_word(&lower, b"where")
                || contains_word(&lower, b"why")
                || contains_word(&lower, b"how")
                || contains_word(&lower, b"which");

            let has_modal: bool = contains_word(&lower, b"can")
                || contains_word(&lower, b"could")
                || contains_word(&lower, b"would")
                || contains_word(&lower, b"should")
                || contains_word(&lower, b"must")
                || contains_word(&lower, b"might")
                || contains_word(&lower, b"may")
                || contains_word(&lower, b"will")
                || contains_word(&lower, b"shall");

            // Compose result Dict. Use Surface(Text) for keys and
            // string values (the evaluator's interner is immutable
            // at eval time; Surface(Text) sorts after Str under
            // cmp_value, which is fine for a fresh dict).
            let mk_key = |s: &str| -> Value {
                Value::Surface(SurfaceKind::Text, std::sync::Arc::from(s.as_bytes()))
            };
            let mk_str = |s: &str| -> Value {
                Value::Surface(SurfaceKind::Text, std::sync::Arc::from(s.as_bytes()))
            };

            let mut pairs: Vec<(Value, Value)> = Vec::with_capacity(19);
            pairs.push((mk_key("delimiters"), mk_str(delimiters)));
            pairs.push((mk_key("kind"), mk_str(kind)));
            pairs.push((mk_key("nesting_depth"), Value::Int(max_depth as i64)));
            pairs.push((mk_key("kv_pair_count"), Value::Int(kv_seps as i64)));
            pairs.push((mk_key("seq_item_count"), Value::Int(seq_seps as i64)));
            pairs.push((mk_key("has_quotes"), Value::Bool(has_quotes)));
            pairs.push((mk_key("balanced"), Value::Bool(overall_balanced)));
            pairs.push((mk_key("whitespace_kind"), mk_str(whitespace_kind)));
            // Natural-language + cross-text fields.
            pairs.push((mk_key("token_count"), Value::Int(token_count as i64)));
            pairs.push((mk_key("terminator"), mk_str(terminator)));
            pairs.push((mk_key("has_punctuation"), Value::Bool(has_punctuation)));
            pairs.push((mk_key("has_uppercase"), Value::Bool(has_uppercase)));
            pairs.push((mk_key("starts_capital"), Value::Bool(starts_capital)));
            pairs.push((mk_key("has_negation"), Value::Bool(has_negation)));
            pairs.push((mk_key("connective_kind"), mk_str(connective_kind)));
            pairs.push((mk_key("has_question_word"), Value::Bool(has_question_word)));
            pairs.push((mk_key("has_modal"), Value::Bool(has_modal)));
            pairs.push((mk_key("text_length"), Value::Int(text_length as i64)));
            pairs.push((mk_key("avg_token_length"), Value::Int(avg_token_length)));
            pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
            Value::Dict(std::sync::Arc::from(pairs))
        }

        TermNode::FbFrameSeq { fb } => {
            let fbv = evaluate(arena, *fb, env, ctx);
            let fb_id: Option<u32> = match fbv {
                Value::Int(i) if i >= 0 => Some(i as u32),
                Value::Float(f) if f >= 0.0 => Some(f as u32),
                _ => None,
            };
            match (fb_id, ctx.framebuffers) {
                (Some(id), Some(fbs)) => match fbs.get(&id) {
                    Some(handle) => Value::Int(handle.current_seq() as i64),
                    None => Value::None,
                },
                _ => Value::None,
            }
        }

        TermNode::ChangeDetect {
            image_vals,
            kernel_weights,
            dims,
        } => {
            let iv = evaluate(arena, *image_vals, env, ctx);
            let kv = evaluate(arena, *kernel_weights, env, ctx);
            let dv = evaluate(arena, *dims, env, ctx);
            let img: Vec<f64> = iv.iter().map(|x| x.as_f64()).collect();
            let ker: Vec<f64> = kv.iter().map(|x| x.as_f64()).collect();
            let d: Vec<usize> = dv.iter().map(|x| x.as_f64() as usize).collect();
            // dims = [h, w, kh, kw, stride]; any missing or shape mismatch -> None.
            let shape_ok = matches!((d.get(0), d.get(1), d.get(2), d.get(3), d.get(4)),
                (Some(&h), Some(&w), Some(&kh), Some(&kw), Some(&stride))
                if stride > 0 && kh > 0 && kw > 0 && kh <= h && kw <= w
                && img.len() == h * w && ker.len() == kh * kw);
            if !shape_ok {
                Value::None
            } else {
                let (h, w, kh, kw, stride) = (d[0], d[1], d[2], d[3], d[4]);
                let resp = crate::vision_primitives::convolve(&img, h, w, &ker, kh, kw, stride);
                Value::Tuple(std::sync::Arc::new(smallvec::SmallVec::from_iter(
                    resp.into_iter().map(Value::Float),
                )))
            }
        }

        TermNode::TemporalDiff { a_vals, b_vals } => {
            let av = evaluate(arena, *a_vals, env, ctx);
            let bv = evaluate(arena, *b_vals, env, ctx);
            let a: Vec<f64> = av.iter().map(|x| x.as_f64()).collect();
            let b: Vec<f64> = bv.iter().map(|x| x.as_f64()).collect();
            if a.len() != b.len() {
                Value::None
            } else {
                let resp = crate::vision_primitives::temporal_diff(&a, &b);
                Value::Tuple(std::sync::Arc::new(smallvec::SmallVec::from_iter(
                    resp.into_iter().map(Value::Float),
                )))
            }
        }

        TermNode::Foveate {
            image_vals,
            dims,
            geometry,
        } => {
            let iv = evaluate(arena, *image_vals, env, ctx);
            let dv = evaluate(arena, *dims, env, ctx);
            let gv = evaluate(arena, *geometry, env, ctx);
            let img: Vec<f64> = iv.iter().map(|x| x.as_f64()).collect();
            let d: Vec<usize> = dv.iter().map(|x| x.as_f64() as usize).collect();
            let geom: Vec<f64> = gv.iter().map(|x| x.as_f64()).collect();
            match (d.get(0).copied(), d.get(1).copied()) {
                (Some(h), Some(w)) if img.len() == h * w && h > 0 && w > 0 => {
                    let (out, oh, ow) = crate::vision_primitives::foveate(&img, h, w, &geom);
                    let mut tup: smallvec::SmallVec<[Value; 4]> =
                        smallvec::SmallVec::with_capacity(out.len() + 2);
                    tup.extend(out.into_iter().map(Value::Float));
                    tup.push(Value::Float(oh as f64));
                    tup.push(Value::Float(ow as f64));
                    Value::Tuple(std::sync::Arc::new(tup))
                }
                _ => Value::None,
            }
        }

        TermNode::Eq { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Bool(eq_with_string_coercion(&av, &bv, ctx.interner))
        }

        TermNode::Lt { a, b } => cmp_bool(arena, *a, *b, env, ctx, std::cmp::Ordering::Less, false),
        TermNode::Lte { a, b } => {
            try_derivation!(ctx, arena, env, "Lte", [("a", *a), ("b", *b)]);
            cmp_bool(arena, *a, *b, env, ctx, std::cmp::Ordering::Less, true)
        }
        TermNode::Gt { a, b } => {
            try_derivation!(ctx, arena, env, "Gt", [("a", *a), ("b", *b)]);
            cmp_bool(arena, *a, *b, env, ctx, std::cmp::Ordering::Greater, false)
        }
        TermNode::Gte { a, b } => {
            try_derivation!(ctx, arena, env, "Gte", [("a", *a), ("b", *b)]);
            cmp_bool(arena, *a, *b, env, ctx, std::cmp::Ordering::Greater, true)
        }

        TermNode::ReachableFrom {
            node,
            edge_type,
            any_type,
        } => {
            let v = evaluate(arena, *node, env, ctx);
            let Value::Node(start) = v else {
                return Value::make_frozenset(vec![]);
            };
            let et = if *any_type { None } else { Some(*edge_type) };
            // Transitive closure: BFS to fixpoint over the SAME
            // ctx.graph.neighbours() Neighbours calls for one hop --
            // composition of the existing graph primitive; only the
            // loop (data-dependent depth) is genuinely new, since no
            // finite Term-tree can express an unbounded walk.
            let mut visited: rustc_hash::FxHashSet<NodeID> = rustc_hash::FxHashSet::default();
            let mut frontier: Vec<NodeID> = vec![start];
            let mut traversal_units = 0u64;
            visited.insert(start);
            while let Some(cur) = frontier.pop() {
                crate::access_trace::note_out_edges(ctx.graph, cur, et);
                let neighbours = ctx.graph.neighbours(cur, et);
                traversal_units = traversal_units.saturating_add(neighbours.len() as u64);
                for nb in neighbours {
                    if visited.insert(nb) {
                        frontier.push(nb);
                    }
                }
            }
            crate::scale_audit::term_units(traversal_units);
            visited.remove(&start);
            Value::make_frozenset(visited.into_iter().map(Value::Node).collect::<Vec<_>>())
        }

        TermNode::Neighbours {
            node,
            edge_type,
            any_type,
        } => {
            let v = evaluate(arena, *node, env, ctx);
            let Value::Node(nid) = v else {
                return Value::make_frozenset(vec![]);
            };
            let et = if *any_type { None } else { Some(*edge_type) };
            let result = cached_neighbours(ctx, nid, *edge_type, *any_type, false, || {
                ctx.graph
                    .neighbours(nid, et)
                    .into_iter()
                    .map(Value::Node)
                    .collect::<Vec<_>>()
            });
            crate::access_trace::note_out_edges(ctx.graph, nid, et);
            result
        }

        TermNode::SlideNeighbours {
            cell,
            slide,
            ground,
        } => {
            let Value::Node(nid) = evaluate(arena, *cell, env, ctx) else {
                return Value::make_frozenset(vec![]);
            };
            let k = match evaluate(arena, *slide, env, ctx) {
                Value::Int(i) => i,
                Value::Float(f) => f as i64,
                _ => return Value::make_frozenset(vec![]),
            };
            let g = match evaluate(arena, *ground, env, ctx) {
                Value::Int(i) => i,
                Value::Float(f) => f as i64,
                _ => return Value::make_frozenset(vec![]),
            };

            let (Some(neighbour_sym), Some(row_sym), Some(col_sym), Some(value_sym)) = (
                ctx.interner.lookup("neighbour"),
                ctx.interner.lookup("row"),
                ctx.interner.lookup("col"),
                ctx.interner.lookup("value"),
            ) else {
                return Value::make_frozenset(vec![]);
            };

            let as_i64 = |v: &Value| -> Option<i64> {
                match v {
                    Value::Int(i) => Some(*i),
                    Value::Float(f) => Some(*f as i64),
                    _ => None,
                }
            };
            let read_rc = |n| -> Option<(i64, i64)> {
                let node = ctx.graph.node(n);
                crate::access_trace::note(2, n.0, row_sym.0, crate::access_trace::NO_ID);
                let r = as_i64(node.attrs.get(&row_sym)?)?;
                crate::access_trace::note(2, n.0, col_sym.0, crate::access_trace::NO_ID);
                let c = as_i64(node.attrs.get(&col_sym)?)?;
                Some((r, c))
            };

            let result = cached_neighbours(ctx, nid, value_sym, false, false, || {
                let mut results: Vec<Value> = Vec::new();
                for (dr, dc) in [(1i64, 0i64), (-1, 0), (0, 1), (0, -1)] {
                    let mut cur = nid;
                    let mut ok = true;
                    for _ in 0..k {
                        let (cr, cc) = match read_rc(cur) {
                            Some(p) => p,
                            None => {
                                ok = false;
                                break;
                            }
                        };
                        let target = (cr + dr, cc + dc);
                        let mut next = None;
                        crate::access_trace::note_out_edges(ctx.graph, cur, Some(neighbour_sym));
                        for nb in ctx.graph.neighbours(cur, Some(neighbour_sym)) {
                            if read_rc(nb) == Some(target) {
                                next = Some(nb);
                                break;
                            }
                        }
                        let nb = match next {
                            Some(n) => n,
                            None => {
                                ok = false;
                                break;
                            }
                        };
                        crate::access_trace::note(2, nb.0, value_sym.0, crate::access_trace::NO_ID);
                        let val = match ctx
                            .graph
                            .node(nb)
                            .attrs
                            .get(&value_sym)
                            .and_then(|v| as_i64(v))
                        {
                            Some(v) => v,
                            None => {
                                ok = false;
                                break;
                            }
                        };
                        if val != g {
                            ok = false;
                            break;
                        }
                        cur = nb;
                    }
                    if ok && k > 0 {
                        results.push(Value::Node(cur));
                    }
                }
                results
            });
            result
        }

        TermNode::InNeighbours {
            node,
            edge_type,
            any_type,
        } => {
            let v = evaluate(arena, *node, env, ctx);
            let Value::Node(nid) = v else {
                return Value::make_frozenset(vec![]);
            };
            let et = if *any_type { None } else { Some(*edge_type) };
            let result = cached_neighbours(ctx, nid, *edge_type, *any_type, true, || {
                ctx.graph
                    .in_neighbours(nid, et)
                    .into_iter()
                    .map(Value::Node)
                    .collect::<Vec<_>>()
            });
            crate::access_trace::note_in_edges(ctx.graph, nid, et);
            result
        }

        TermNode::MapNeighbours {
            source,
            edge_type,
            any_type,
        } => {
            let s = evaluate(arena, *source, env, ctx);
            let et = if *any_type { None } else { Some(*edge_type) };
            let mut out = Vec::new();
            for v in s.iter() {
                if let Value::Node(nid) = v {
                    crate::access_trace::note_out_edges(ctx.graph, *nid, et);
                    for n in ctx.graph.neighbours(*nid, et) {
                        out.push(Value::Node(n));
                    }
                }
            }
            Value::make_frozenset(out)
        }

        TermNode::Count { source } => {
            if is_body_taker_registered(ctx, "Count") {
                let mut tmp = TermArena::new();
                let expanded = expand_count(arena, &mut tmp, ctx.interner, *source);
                return evaluate(&tmp, expanded, env, ctx);
            }
            let s = evaluate(arena, *source, env, ctx);
            // arc6 tier-0 `fix:StringAsSequence`: an interned string used to
            // answer 0 here (it is not a collection to `Value::len`).  A
            // `Surface(Text)` already answered with its byte length and is
            // deliberately left on that path — only the degenerate 0 moves.
            if let Value::Str(sym) = &s {
                return Value::Int(ctx.interner.resolve(*sym).chars().count() as i64);
            }
            Value::Int(s.len() as i64)
        }

        TermNode::Filter {
            source,
            var_name,
            predicate,
        } => {
            // Memoize on the same shape Python does: id of this Term +
            // bindings of ALL its free vars (excluding the binder).  The
            // source matters as much as the predicate: for
            //
            //   Filter(Neighbours(Var(ctx), "has_candidate"), option, ...)
            //
            // two bindings of `ctx` have different source sets even when the
            // predicate has no outer variables.  Keying from the predicate
            // alone aliases those sets and lets the first DecisionContext's
            // candidates leak into every later context evaluated in the same
            // fixpoint pass.  `free_vars` already understands Filter binding,
            // so asking it for the whole term includes source variables while
            // still excluding `var_name` inside the predicate.
            let fv = free_vars(arena, idx, None);
            let env_covers = fv.iter().all(|v| env_get(env, *v).is_some());
            let key = if env_covers {
                Some(cache_key!(env, &fv))
            } else {
                None
            };
            if let (Some(cache), Some(k)) = (ctx.cache.as_deref_mut(), key.as_ref()) {
                if let Some(hit) = cache.filter.get(&(idx, k.clone())) {
                    if let Some(c) = ctx.counters.as_deref_mut() {
                        c.on_cache_filter(true);
                    }
                    return hit.clone();
                }
            }
            if let Some(c) = ctx.counters.as_deref_mut() {
                c.on_cache_filter(false);
            }
            let source_v = evaluate(arena, *source, env, ctx);
            let mut out = Vec::new();
            let snap = source_v.snapshot();
            for it_ref in snap.iter() {
                env.push((*var_name, it_ref.clone()));
                let keep = evaluate(arena, *predicate, env, ctx).truthy();
                env.pop();
                if keep {
                    out.push(it_ref.clone());
                }
            }
            let result = Value::make_frozenset(out);
            if let (Some(cache), Some(k)) = (ctx.cache.as_deref_mut(), key) {
                cache.filter.insert((idx, k), result.clone());
            }
            result
        }

        // Ordered twin of Filter: keep matching elements in source order (+ duplicates),
        // returns a LIST — list-comprehension `if`. (No memo cache; the value is order-bearing.)
        TermNode::FilterList {
            source,
            var_name,
            predicate,
        } => {
            let source_v = evaluate(arena, *source, env, ctx);
            let mut out: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
            let snap = source_v.snapshot();
            for it_ref in snap.iter() {
                env.push((*var_name, it_ref.clone()));
                let keep = evaluate(arena, *predicate, env, ctx).truthy();
                env.pop();
                if keep {
                    out.push(it_ref.clone());
                }
            }
            Value::List(std::sync::Arc::new(out))
        }

        TermNode::Exists {
            source,
            var_name,
            predicate,
        } => {
            let source_v = evaluate(arena, *source, env, ctx);
            let snap = source_v.snapshot();
            // FALLBACK TRACE / H2. Record whether this Exists saw NOTHING AT
            // ALL, so an enclosing `Not` can tell "passed because the thing was
            // absent" (an absence-branch) from "passed because the predicate
            // never matched" (an ordinary negative).
            crate::fallback_trace::set_last_exists_empty(snap.is_empty());
            let mut examined = 0u64;
            for it_ref in snap.iter() {
                examined += 1;
                env.push((*var_name, it_ref.clone()));
                let ok = evaluate(arena, *predicate, env, ctx).truthy();
                env.pop();
                if ok {
                    crate::scale_audit::term_units(examined);
                    return Value::Bool(true);
                }
            }
            crate::scale_audit::term_units(examined);
            Value::Bool(false)
        }

        TermNode::Sum {
            source,
            var_name,
            value,
        } => {
            if is_body_taker_registered(ctx, "Sum") {
                let mut tmp = TermArena::new();
                let expanded =
                    expand_sum(arena, &mut tmp, ctx.interner, *source, *var_name, *value);
                return evaluate(&tmp, expanded, env, ctx);
            }
            let source_v = evaluate(arena, *source, env, ctx);
            // Avoid the temporary Vec<Value>: take the underlying Arc
            // slice (cheap refcount bump for Set/FrozenSet, single owned
            // clone for Tuple<=4 inline) and walk it by reference. The
            // old `.iter().cloned().collect()` materialised the entire
            // source set into a fresh Vec just to release the borrow.
            let mut all_int = true;
            let mut total_i: i64 = 0;
            let mut total_f: f64 = 0.0;
            let snap = source_v.snapshot();
            for it_ref in snap.iter() {
                env.push((*var_name, it_ref.clone()));
                let v = evaluate(arena, *value, env, ctx);
                env.pop();
                match v {
                    Value::Int(n) => {
                        total_i = total_i.wrapping_add(n);
                        total_f += n as f64;
                    }
                    Value::Float(f) => {
                        total_f += f;
                        all_int = false;
                    }
                    Value::Bool(b) => {
                        let n = if b { 1 } else { 0 };
                        total_i = total_i.wrapping_add(n);
                        total_f += n as f64;
                    }
                    _ => {}
                }
            }
            if all_int {
                Value::Int(total_i)
            } else {
                Value::Float(total_f)
            }
        }

        TermNode::Prod {
            source,
            var_name,
            value,
        } => {
            let source_v = evaluate(arena, *source, env, ctx);
            let snap = source_v.snapshot();
            let mut all_int = true;
            let mut total_i: i64 = 1;
            let mut total_f: f64 = 1.0;
            for it_ref in snap.iter() {
                env.push((*var_name, it_ref.clone()));
                let v = evaluate(arena, *value, env, ctx);
                env.pop();
                match v {
                    Value::Int(n) => {
                        total_i = total_i.wrapping_mul(n);
                        total_f *= n as f64;
                    }
                    Value::Float(f) => {
                        total_f *= f;
                        all_int = false;
                    }
                    Value::Bool(b) => {
                        let n = if b { 1 } else { 0 };
                        total_i = total_i.wrapping_mul(n);
                        total_f *= n as f64;
                    }
                    _ => {}
                }
            }
            if all_int {
                Value::Int(total_i)
            } else {
                Value::Float(total_f)
            }
        }

        TermNode::MinOver {
            source,
            var_name,
            value,
            default,
        } => min_or_max_over(arena, *source, *var_name, *value, *default, env, ctx, true),
        TermNode::MaxOver {
            source,
            var_name,
            value,
            default,
        } => min_or_max_over(arena, *source, *var_name, *value, *default, env, ctx, false),

        TermNode::Pick { source } => {
            let s = evaluate(arena, *source, env, ctx);
            let picked = s.iter().next().cloned().unwrap_or(Value::None);
            picked
        }

        TermNode::PickUnique { source } => {
            let s = evaluate(arena, *source, env, ctx);
            let snap = s.snapshot();
            let n = snap.iter().count();
            if n > 1 {
                panic!(
                    "PickUnique: AMBIGUOUS selection — {} candidates where exactly \
                     one was required. A config read found more than one node and \
                     `Pick` would have silently returned an arbitrary one of them, \
                     leaving the rest inert (VISION_PROTOCOL §1.1). Disambiguate by \
                     traversing from the owning hub instead of selecting globally.",
                    n
                );
            }
            snap.iter().next().cloned().unwrap_or(Value::None)
        }

        TermNode::Fold {
            source,
            var_name,
            acc_name,
            init,
            body,
        } => {
            let source_v = evaluate(arena, *source, env, ctx);
            let mut acc = evaluate(arena, *init, env, ctx);
            let snap = source_v.snapshot();
            for it_ref in snap.iter() {
                let it = it_ref.clone();
                env.push((*acc_name, acc.clone()));
                env.push((*var_name, it));
                acc = evaluate(arena, *body, env, ctx);
                env.pop();
                env.pop();
            }
            acc
        }

        TermNode::Argmax {
            source,
            var_name,
            value,
            default,
        } => argmin_or_argmax_over(
            arena, *source, *var_name, *value, *default, env, ctx, false, false, None,
        ),
        TermNode::Argmin {
            source,
            var_name,
            value,
            default,
        } => argmin_or_argmax_over(
            arena, *source, *var_name, *value, *default, env, ctx, true, false, None,
        ),
        TermNode::ArgminUnique {
            source,
            var_name,
            value,
            default,
        } => argmin_or_argmax_over(
            arena, *source, *var_name, *value, *default, env, ctx, true, true, None,
        ),
        TermNode::ArgminRefusal {
            source,
            var_name,
            value,
            refused,
        } => {
            // Tie -> the `refused` token; empty source -> `Value::None` (no
            // `default`, so a tie and an empty source return DIFFERENT values).
            argmin_or_argmax_over(
                arena, *source, *var_name, *value, None, env, ctx, true, true, *refused,
            )
        }

        // --- Program IR (P1): STRUCTURAL variants are INERT here. ---
        // The main evaluator does NOT execute statement/expression IR —
        // it returns the documented inert value (`Value::None`), exactly
        // like reading data. Execution happens ONLY inside `ProgEval`
        // (prog_eval.rs). This is the structural-honesty gate's contract
        // (tests/test_prog_ir_migrated.py).
        TermNode::ProgSeq { .. }
        | TermNode::ProgAssignVar { .. }
        | TermNode::ProgAugAssign { .. }
        | TermNode::ProgTupleUnpack { .. }
        | TermNode::ProgIfStmt { .. }
        | TermNode::ProgForEach { .. }
        | TermNode::ProgWhile { .. }
        | TermNode::ProgLoopCtl { .. }
        | TermNode::ProgReturn { .. }
        | TermNode::ProgTryOr { .. }
        | TermNode::ProgRaise { .. }
        | TermNode::ProgImportStmt { .. }
        | TermNode::ProgSubscriptSet { .. }
        | TermNode::ProgAttrSet { .. }
        | TermNode::ProgDefFnParam { .. }
        | TermNode::ProgCallExtern { .. }
        | TermNode::ProgAttrGet { .. }
        | TermNode::ProgSubscript { .. }
        | TermNode::ProgSlice { .. }
        | TermNode::ProgContainerLit { .. }
        | TermNode::ProgComprehensionList { .. }
        | TermNode::ProgComprehensionGen { .. }
        | TermNode::ProgIsOp { .. }
        | TermNode::ProgFString { .. } => Value::None,

        TermNode::ProgEval {
            prog,
            env: env_t,
            oracles,
            fuel,
            field,
        } => crate::prog_eval::eval_prog_eval(
            arena, *prog, *env_t, *oracles, *fuel, *field, env, ctx,
        ),

        // --- Derived-operator tier: registry dispatch (`Derivation::
        // ValueTaker`'s exact bind-then-evaluate shape, copied nearly
        // verbatim, generalized to a runtime name + `local_sym`-safe
        // binding — see `Call`'s own doc and `EvalCtx::derived_ops`'s). ---
        TermNode::Call { name, args } => {
            let Some(reg) = ctx.derived_ops.clone() else {
                return Value::None;
            };
            let Some(def) = reg.get(name) else {
                return Value::None;
            };
            let n = args.len().min(def.params.len());
            let mut pushed = 0usize;
            for (a, (pname, _pool)) in args.iter().zip(def.params.iter()).take(n) {
                let v = evaluate(arena, *a, env, ctx);
                env.push((*pname, v));
                pushed += 1;
            }
            let r = evaluate(arena, def.body, env, ctx);
            for _ in 0..pushed {
                env.pop();
            }
            r
        }

        // --- Program synthesis (P4-A/Q1): one-line handoff. ---
        TermNode::SynthEnumerate {
            examples,
            ops,
            consts,
            exclude,
            derived_ops,
            exclude_ops,
            max_size,
            max_candidates,
            saturate_k,
            field,
        } => crate::synth_enumerate::eval_synth_enumerate(
            arena,
            *examples,
            *ops,
            *consts,
            *exclude,
            *derived_ops,
            *exclude_ops,
            *max_size,
            *max_candidates,
            *saturate_k,
            *field,
            env,
            ctx,
        ),

        TermNode::ParetoDominates {
            candidate,
            alternative,
            dimension_count,
            value_edge,
            measure_edge,
            dimension_key,
            verified_key,
            signed_value_key,
        } => {
            let Value::Node(candidate) = evaluate(arena, *candidate, env, ctx) else {
                return Value::Bool(false);
            };
            let Value::Node(alternative) = evaluate(arena, *alternative, env, ctx) else {
                return Value::Bool(false);
            };
            let dimensions = match evaluate(arena, *dimension_count, env, ctx) {
                Value::Int(value) => value,
                // Keep the Pareto contract integer-native while accepting an
                // exactly integral scalar from generic control bridges.
                Value::Float(value) if value.is_finite() && value.fract() == 0.0 => {
                    let n = value as i64;
                    if (n as f64) == value {
                        n
                    } else {
                        return Value::Bool(false);
                    }
                }
                _ => return Value::Bool(false),
            };
            Value::Bool(eval_pareto_dominates(
                ctx.graph,
                candidate,
                alternative,
                dimensions,
                *value_edge,
                *measure_edge,
                *dimension_key,
                *verified_key,
                *signed_value_key,
            ))
        }

        // --- Naming primitives (P1): Surface(Text) end-to-end. ---
        TermNode::SnakeCase { text } => {
            let tv = evaluate(arena, *text, env, ctx);
            match str_like_owned(&tv, ctx.interner) {
                Some(s) => Value::Surface(
                    SurfaceKind::Text,
                    std::sync::Arc::from(snake_case_str(&s).into_bytes().into_boxed_slice()),
                ),
                None => Value::None,
            }
        }
        TermNode::CaseFold { text } => {
            let tv = evaluate(arena, *text, env, ctx);
            match str_like_owned(&tv, ctx.interner) {
                Some(s) => Value::Surface(
                    SurfaceKind::Text,
                    std::sync::Arc::from(s.to_lowercase().into_bytes().into_boxed_slice()),
                ),
                None => Value::None,
            }
        }

        TermNode::BitsAt {
            buffer,
            bitpos,
            n_bits,
        } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let bp_v = evaluate(arena, *bitpos, env, ctx);
            let nb_v = evaluate(arena, *n_bits, env, ctx);
            let Value::Surface(_, bytes) = buf_v else {
                return Value::None;
            };
            let Value::Int(bp) = bp_v else {
                return Value::None;
            };
            let Value::Int(nb) = nb_v else {
                return Value::None;
            };
            if bp < 0 || nb < 0 || nb > 64 {
                return Value::None;
            }
            let end = bp as u64 + nb as u64;
            if end > (bytes.len() as u64) * 8 {
                return Value::None;
            }
            let mut acc: u64 = 0;
            for i in 0..(nb as u64) {
                let abs = bp as u64 + i;
                let byte = bytes[(abs >> 3) as usize];
                let bit = (byte >> (7 - (abs & 7))) & 1;
                acc = (acc << 1) | (bit as u64);
            }
            Value::Int(acc as i64)
        }

        TermNode::BitsWrite {
            buffer,
            bitpos,
            value,
            n_bits,
        } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let bp_v = evaluate(arena, *bitpos, env, ctx);
            let val_v = evaluate(arena, *value, env, ctx);
            let nb_v = evaluate(arena, *n_bits, env, ctx);
            let Value::Surface(kind, bytes) = buf_v else {
                return Value::None;
            };
            let Value::Int(bp) = bp_v else {
                return Value::None;
            };
            let Value::Int(val) = val_v else {
                return Value::None;
            };
            let Value::Int(nb) = nb_v else {
                return Value::None;
            };
            if bp < 0 || nb < 0 || nb > 64 {
                return Value::None;
            }
            let needed_bytes = ((bp as u64 + nb as u64 + 7) / 8) as usize;
            let mut new_bytes: Vec<u8> = bytes.iter().copied().collect();
            if needed_bytes > new_bytes.len() {
                new_bytes.resize(needed_bytes, 0);
            }
            let raw_val = val as u64;
            for i in 0..(nb as u64) {
                let bit = (raw_val >> (nb as u64 - 1 - i)) & 1;
                let abs = bp as u64 + i;
                let byte_idx = (abs >> 3) as usize;
                let bit_idx = 7 - (abs & 7);
                let mask = 1u8 << bit_idx;
                if bit == 1 {
                    new_bytes[byte_idx] |= mask;
                } else {
                    new_bytes[byte_idx] &= !mask;
                }
            }
            Value::Surface(kind, std::sync::Arc::from(new_bytes.into_boxed_slice()))
        }

        TermNode::BitsAtAll { buffer, reads } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let reads_v = evaluate(arena, *reads, env, ctx);
            let Value::Surface(_, bytes) = buf_v else {
                return Value::None;
            };
            let (Value::Tuple(items) | Value::List(items)) = reads_v else {
                return Value::None;
            };
            let mut out: smallvec::SmallVec<[Value; 4]> = smallvec::SmallVec::new();
            let total_bits = (bytes.len() as u64) * 8;
            for item in items.iter() {
                let (Value::Tuple(pair) | Value::List(pair)) = item else {
                    return Value::None;
                };
                if pair.len() != 2 {
                    return Value::None;
                }
                let Value::Int(bp) = pair[0] else {
                    return Value::None;
                };
                let Value::Int(nb) = pair[1] else {
                    return Value::None;
                };
                if bp < 0 || nb < 0 || nb > 64 {
                    return Value::None;
                }
                let end = bp as u64 + nb as u64;
                if end > total_bits {
                    return Value::None;
                }
                let mut acc: u64 = 0;
                for i in 0..(nb as u64) {
                    let abs = bp as u64 + i;
                    let byte = bytes[(abs >> 3) as usize];
                    let bit = (byte >> (7 - (abs & 7))) & 1;
                    acc = (acc << 1) | (bit as u64);
                }
                out.push(Value::Int(acc as i64));
            }
            Value::Tuple(std::sync::Arc::new(out))
        }

        TermNode::BitsWriteAll { buffer, writes } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let writes_v = evaluate(arena, *writes, env, ctx);
            let Value::Surface(kind, bytes) = buf_v else {
                return Value::None;
            };
            let (Value::Tuple(items) | Value::List(items)) = writes_v else {
                return Value::None;
            };
            // First pass: validate + compute final buffer length.
            let mut max_byte: usize = bytes.len();
            let mut triples: Vec<(u64, u64, u64)> = Vec::with_capacity(items.len());
            for item in items.iter() {
                let (Value::Tuple(triple) | Value::List(triple)) = item else {
                    return Value::None;
                };
                if triple.len() != 3 {
                    return Value::None;
                }
                let Value::Int(bp) = triple[0] else {
                    return Value::None;
                };
                let Value::Int(val) = triple[1] else {
                    return Value::None;
                };
                let Value::Int(nb) = triple[2] else {
                    return Value::None;
                };
                if bp < 0 || nb < 0 || nb > 64 {
                    return Value::None;
                }
                let need = ((bp as u64 + nb as u64 + 7) / 8) as usize;
                if need > max_byte {
                    max_byte = need;
                }
                triples.push((bp as u64, val as u64, nb as u64));
            }
            let mut new_bytes: Vec<u8> = bytes.iter().copied().collect();
            if max_byte > new_bytes.len() {
                new_bytes.resize(max_byte, 0);
            }
            for (bp, val, nb) in triples.into_iter() {
                for i in 0..nb {
                    let bit = (val >> (nb - 1 - i)) & 1;
                    let abs = bp + i;
                    let byte_idx = (abs >> 3) as usize;
                    let bit_idx = 7 - (abs & 7);
                    let mask = 1u8 << bit_idx;
                    if bit == 1 {
                        new_bytes[byte_idx] |= mask;
                    } else {
                        new_bytes[byte_idx] &= !mask;
                    }
                }
            }
            Value::Surface(kind, std::sync::Arc::from(new_bytes.into_boxed_slice()))
        }

        TermNode::HuffmanDecodeStream {
            buffer,
            bitpos,
            table,
            n_pairs,
        } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let bp_v = evaluate(arena, *bitpos, env, ctx);
            let table_v = evaluate(arena, *table, env, ctx);
            let np_v = evaluate(arena, *n_pairs, env, ctx);
            let Value::Surface(_, bytes) = buf_v else {
                return Value::None;
            };
            let Value::Int(start_bp) = bp_v else {
                return Value::None;
            };
            let Value::Node(table_nid) = table_v else {
                return Value::None;
            };
            let Value::Int(n_pairs_n) = np_v else {
                return Value::None;
            };
            if start_bp < 0 || n_pairs_n < 0 {
                return Value::None;
            }
            // Pull codes, hlens, linbits, xlen from the HuffmanTable
            // node's attrs. Pure graph-data read — no per-codec
            // hardcoding.
            let node = ctx.graph.node(table_nid);
            let codes_sym = ctx.interner.lookup("codes").unwrap_or(Sym::default());
            let hlens_sym = ctx.interner.lookup("hlens").unwrap_or(Sym::default());
            let linbits_sym = ctx.interner.lookup("linbits").unwrap_or(Sym::default());
            let xlen_sym = ctx.interner.lookup("xlen").unwrap_or(Sym::default());
            crate::access_trace::note(2, table_nid.0, codes_sym.0, crate::access_trace::NO_ID);
            crate::access_trace::note(2, table_nid.0, hlens_sym.0, crate::access_trace::NO_ID);
            crate::access_trace::note(2, table_nid.0, linbits_sym.0, crate::access_trace::NO_ID);
            crate::access_trace::note(2, table_nid.0, xlen_sym.0, crate::access_trace::NO_ID);
            let Some(Value::Surface(_, codes_bytes)) = node.attrs.get(&codes_sym).cloned() else {
                return Value::None;
            };
            let Some(Value::Surface(_, hlens_bytes)) = node.attrs.get(&hlens_sym).cloned() else {
                return Value::None;
            };
            let linbits = match node.attrs.get(&linbits_sym) {
                Some(Value::Int(n)) => *n as u32,
                _ => 0,
            };
            let xlen = match node.attrs.get(&xlen_sym) {
                Some(Value::Int(n)) => *n as u32,
                _ => 0,
            };
            // codes_bytes is little-endian u16 array; hlens_bytes is u8 array.
            let n_entries = codes_bytes.len() / 2;
            if hlens_bytes.len() != n_entries {
                return Value::None;
            }
            let codes: Vec<u32> = (0..n_entries)
                .map(|i| (codes_bytes[i * 2] as u32) | ((codes_bytes[i * 2 + 1] as u32) << 8))
                .collect();
            let dim = (n_entries as f64).sqrt() as usize;
            let mut pairs: Vec<Value> = Vec::with_capacity(n_pairs_n as usize);
            let mut bp = start_bp as u64;
            let total_bits = (bytes.len() as u64) * 8;
            for _ in 0..n_pairs_n {
                // Walk bit-by-bit accumulating a code, comparing
                // against table entries at the matching length.
                let mut acc: u32 = 0;
                let mut bits_read: u8 = 0;
                let mut found: Option<(u8, u32, u32)> = None; // (len, x, y)
                while bits_read < 32 && bp < total_bits {
                    let byte = bytes[(bp >> 3) as usize];
                    let bit = (byte >> (7 - (bp & 7))) & 1;
                    acc = (acc << 1) | (bit as u32);
                    bp += 1;
                    bits_read += 1;
                    for i in 0..n_entries {
                        let ln = hlens_bytes[i];
                        if ln != bits_read {
                            continue;
                        }
                        if codes[i] != acc {
                            continue;
                        }
                        let (x, y) = if dim > 0 {
                            ((i / dim) as u32, (i % dim) as u32)
                        } else {
                            (i as u32, 0)
                        };
                        found = Some((ln, x, y));
                        break;
                    }
                    if found.is_some() {
                        break;
                    }
                }
                let Some((_, mut x, mut y)) = found else {
                    return Value::None;
                };
                // Linbits escape (for tables 16-31): x==15 means read
                // `linbits` more bits and add to x. Same for y.
                if linbits > 0 && x == 15 {
                    let mut extra: u32 = 0;
                    for _ in 0..linbits {
                        if bp >= total_bits {
                            return Value::None;
                        }
                        let byte = bytes[(bp >> 3) as usize];
                        let bit = (byte >> (7 - (bp & 7))) & 1;
                        extra = (extra << 1) | (bit as u32);
                        bp += 1;
                    }
                    x += extra;
                }
                if linbits > 0 && y == 15 {
                    let mut extra: u32 = 0;
                    for _ in 0..linbits {
                        if bp >= total_bits {
                            return Value::None;
                        }
                        let byte = bytes[(bp >> 3) as usize];
                        let bit = (byte >> (7 - (bp & 7))) & 1;
                        extra = (extra << 1) | (bit as u32);
                        bp += 1;
                    }
                    y += extra;
                }
                // Sign bits for non-zero values.
                let mut x_signed = x as i64;
                let mut y_signed = y as i64;
                if x != 0 {
                    if bp >= total_bits {
                        return Value::None;
                    }
                    let byte = bytes[(bp >> 3) as usize];
                    let bit = (byte >> (7 - (bp & 7))) & 1;
                    bp += 1;
                    if bit == 1 {
                        x_signed = -x_signed;
                    }
                }
                if y != 0 {
                    if bp >= total_bits {
                        return Value::None;
                    }
                    let byte = bytes[(bp >> 3) as usize];
                    let bit = (byte >> (7 - (bp & 7))) & 1;
                    bp += 1;
                    if bit == 1 {
                        y_signed = -y_signed;
                    }
                }
                let pair = Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                    Value::Int(x_signed),
                    Value::Int(y_signed),
                ]));
                pairs.push(pair);
            }
            // Suppress unused-warning on xlen — kept for future linbits-table dispatch.
            let _ = xlen;
            Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                Value::Tuple(std::sync::Arc::new(pairs.into_iter().collect())),
                Value::Int(bp as i64),
            ]))
        }

        TermNode::ExpGolombDecode { buffer, bitpos } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let bp_v = evaluate(arena, *bitpos, env, ctx);
            let Value::Surface(_, bytes) = buf_v else {
                return Value::None;
            };
            let Value::Int(start_bp) = bp_v else {
                return Value::None;
            };
            if start_bp < 0 {
                return Value::None;
            }
            match exp_golomb_decode(&bytes, start_bp as u64) {
                Some((val, new_bp)) => Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                    Value::Int(val as i64),
                    Value::Int(new_bp as i64)
                ])),
                None => Value::None,
            }
        }

        TermNode::ExpGolombDecodeSigned { buffer, bitpos } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let bp_v = evaluate(arena, *bitpos, env, ctx);
            let Value::Surface(_, bytes) = buf_v else {
                return Value::None;
            };
            let Value::Int(start_bp) = bp_v else {
                return Value::None;
            };
            if start_bp < 0 {
                return Value::None;
            }
            match exp_golomb_decode(&bytes, start_bp as u64) {
                Some((uval, new_bp)) => {
                    let signed: i64 = if uval & 1 == 1 {
                        ((uval + 1) / 2) as i64
                    } else {
                        -((uval / 2) as i64)
                    };
                    Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                        Value::Int(signed),
                        Value::Int(new_bp as i64)
                    ]))
                }
                None => Value::None,
            }
        }

        TermNode::ExpGolombEncode {
            buffer,
            bitpos,
            value,
        } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let bp_v = evaluate(arena, *bitpos, env, ctx);
            let val_v = evaluate(arena, *value, env, ctx);
            let Value::Surface(kind, bytes) = buf_v else {
                return Value::None;
            };
            let Value::Int(start_bp) = bp_v else {
                return Value::None;
            };
            let Value::Int(val) = val_v else {
                return Value::None;
            };
            if start_bp < 0 || val < 0 {
                return Value::None;
            }
            let mut out_bytes: Vec<u8> = bytes.iter().copied().collect();
            let new_bp = exp_golomb_encode(&mut out_bytes, start_bp as u64, val as u64);
            Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                Value::Surface(kind, std::sync::Arc::from(out_bytes.into_boxed_slice())),
                Value::Int(new_bp as i64),
            ]))
        }

        TermNode::ExpGolombEncodeSigned {
            buffer,
            bitpos,
            value,
        } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let bp_v = evaluate(arena, *bitpos, env, ctx);
            let val_v = evaluate(arena, *value, env, ctx);
            let Value::Surface(kind, bytes) = buf_v else {
                return Value::None;
            };
            let Value::Int(start_bp) = bp_v else {
                return Value::None;
            };
            let Value::Int(val) = val_v else {
                return Value::None;
            };
            if start_bp < 0 {
                return Value::None;
            }
            let uval: u64 = if val > 0 {
                (val as u64) * 2 - 1
            } else {
                ((-val) as u64) * 2
            };
            let mut out_bytes: Vec<u8> = bytes.iter().copied().collect();
            let new_bp = exp_golomb_encode(&mut out_bytes, start_bp as u64, uval);
            Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                Value::Surface(kind, std::sync::Arc::from(out_bytes.into_boxed_slice())),
                Value::Int(new_bp as i64),
            ]))
        }

        TermNode::HuffmanEncodeStream {
            buffer,
            bitpos,
            pairs,
            table,
        } => {
            let buf_v = evaluate(arena, *buffer, env, ctx);
            let bp_v = evaluate(arena, *bitpos, env, ctx);
            let pairs_v = evaluate(arena, *pairs, env, ctx);
            let table_v = evaluate(arena, *table, env, ctx);
            let Value::Surface(kind, bytes) = buf_v else {
                return Value::None;
            };
            let Value::Int(start_bp) = bp_v else {
                return Value::None;
            };
            let Value::Node(table_nid) = table_v else {
                return Value::None;
            };
            let (Value::Tuple(pairs_tup) | Value::List(pairs_tup)) = pairs_v else {
                return Value::None;
            };
            if start_bp < 0 {
                return Value::None;
            }
            let node = ctx.graph.node(table_nid);
            let codes_sym = ctx.interner.lookup("codes").unwrap_or(Sym::default());
            let hlens_sym = ctx.interner.lookup("hlens").unwrap_or(Sym::default());
            let linbits_sym = ctx.interner.lookup("linbits").unwrap_or(Sym::default());
            crate::access_trace::note(2, table_nid.0, codes_sym.0, crate::access_trace::NO_ID);
            crate::access_trace::note(2, table_nid.0, hlens_sym.0, crate::access_trace::NO_ID);
            crate::access_trace::note(2, table_nid.0, linbits_sym.0, crate::access_trace::NO_ID);
            let Some(Value::Surface(_, codes_bytes)) = node.attrs.get(&codes_sym).cloned() else {
                return Value::None;
            };
            let Some(Value::Surface(_, hlens_bytes)) = node.attrs.get(&hlens_sym).cloned() else {
                return Value::None;
            };
            let linbits = match node.attrs.get(&linbits_sym) {
                Some(Value::Int(n)) => *n as u32,
                _ => 0,
            };
            let n_entries = codes_bytes.len() / 2;
            if hlens_bytes.len() != n_entries {
                return Value::None;
            }
            let codes: Vec<u32> = (0..n_entries)
                .map(|i| (codes_bytes[i * 2] as u32) | ((codes_bytes[i * 2 + 1] as u32) << 8))
                .collect();
            let dim = (n_entries as f64).sqrt() as usize;
            let mut out_bytes: Vec<u8> = bytes.iter().copied().collect();
            let mut bp = start_bp as u64;
            // Local helper to write a value at bp into out_bytes.
            let write_bits = |bp_ref: &mut u64, out: &mut Vec<u8>, val: u64, nb: u32| {
                for i in 0..nb {
                    let bit = (val >> (nb - 1 - i)) & 1;
                    let abs = *bp_ref;
                    let byte_idx = (abs >> 3) as usize;
                    let bit_idx = 7 - (abs & 7);
                    if byte_idx >= out.len() {
                        out.resize(byte_idx + 1, 0);
                    }
                    let mask = 1u8 << bit_idx;
                    if bit == 1 {
                        out[byte_idx] |= mask;
                    } else {
                        out[byte_idx] &= !mask;
                    }
                    *bp_ref += 1;
                }
            };
            for pv in pairs_tup.iter() {
                let (Value::Tuple(p) | Value::List(p)) = pv else {
                    return Value::None;
                };
                if p.len() != 2 {
                    return Value::None;
                }
                let Value::Int(x) = p[0] else {
                    return Value::None;
                };
                let Value::Int(y) = p[1] else {
                    return Value::None;
                };
                let abs_x = x.unsigned_abs() as u32;
                let abs_y = y.unsigned_abs() as u32;
                let (huff_x, extra_x) = if linbits > 0 && abs_x >= 15 {
                    (15u32, Some(abs_x - 15))
                } else {
                    (abs_x, None)
                };
                let (huff_y, extra_y) = if linbits > 0 && abs_y >= 15 {
                    (15u32, Some(abs_y - 15))
                } else {
                    (abs_y, None)
                };
                let hx = if dim > 0 {
                    std::cmp::min(huff_x, dim as u32 - 1)
                } else {
                    huff_x
                };
                let hy = if dim > 0 {
                    std::cmp::min(huff_y, dim as u32 - 1)
                } else {
                    huff_y
                };
                let idx = if dim > 0 {
                    (hx * dim as u32 + hy) as usize
                } else {
                    hx as usize
                };
                if idx >= n_entries {
                    return Value::None;
                }
                let code = codes[idx];
                let ln = hlens_bytes[idx] as u32;
                write_bits(&mut bp, &mut out_bytes, code as u64, ln);
                if let Some(e) = extra_x {
                    write_bits(&mut bp, &mut out_bytes, e as u64, linbits);
                }
                if let Some(e) = extra_y {
                    write_bits(&mut bp, &mut out_bytes, e as u64, linbits);
                }
                if x != 0 {
                    write_bits(&mut bp, &mut out_bytes, if x < 0 { 1 } else { 0 }, 1);
                }
                if y != 0 {
                    write_bits(&mut bp, &mut out_bytes, if y < 0 { 1 } else { 0 }, 1);
                }
            }
            Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                Value::Surface(kind, std::sync::Arc::from(out_bytes.into_boxed_slice())),
                Value::Int(bp as i64),
            ]))
        }

        // --- set algebra (Phase 7 ext) ---
        TermNode::Union { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            // Pre-size: both snapshots known.
            let a_snap = av.snapshot();
            let b_snap = bv.snapshot();
            let mut items: Vec<Value> = Vec::with_capacity(a_snap.len() + b_snap.len());
            items.extend(a_snap.iter().cloned());
            items.extend(b_snap.iter().cloned());
            Value::make_frozenset(items)
        }
        TermNode::Last { seq } => {
            let s = evaluate(arena, *seq, env, ctx);
            // arc6 tier-0 `fix:StringAsSequence` — the last CHARACTER of a
            // text value (it used to be `None`, measured).
            if let Some(chars) = text_chars(&s, ctx.interner) {
                return chars.last().copied().map(char_value).unwrap_or(Value::None);
            }
            s.snapshot().iter().last().cloned().unwrap_or(Value::None)
        }
        TermNode::IndexAt { seq, index } => {
            let s = evaluate(arena, *seq, env, ctx);
            // arc6 tier-0 `fix:StringAsSequence` — the character at an
            // index, with the SAME Python-style from-end rule the sequence
            // path below already uses (it used to be `None`, measured).
            if let Some(chars) = text_chars(&s, ctx.interner) {
                let n = chars.len() as i64;
                let mut i = evaluate(arena, *index, env, ctx).as_i64();
                if i < 0 {
                    i += n;
                }
                return if i < 0 || i >= n {
                    Value::None
                } else {
                    char_value(chars[i as usize])
                };
            }
            let snap = s.snapshot();
            let n = snap.len() as i64;
            let mut i = evaluate(arena, *index, env, ctx).as_i64();
            if i < 0 {
                i += n;
            } // Python-style from-end indexing
            if i < 0 || i >= n {
                Value::None
            } else {
                snap[i as usize].clone()
            }
        }
        TermNode::Append { seq, item } => {
            let s = evaluate(arena, *seq, env, ctx);
            let iv = evaluate(arena, *item, env, ctx);
            let mut out: smallvec::SmallVec<[Value; 4]> = s.snapshot().iter().cloned().collect();
            out.push(iv);
            // KIND-PRESERVING (ARC6): byte-identical whenever the source is a
            // Tuple, which is every pre-existing caller. Appending to a list
            // gives a list, exactly as `aug_combine`'s `+` does.
            let out = std::sync::Arc::new(out);
            if matches!(s, Value::List(_)) {
                Value::List(out)
            } else {
                Value::Tuple(out)
            }
        }
        TermNode::ListDrop { list, index } => {
            let lv = evaluate(arena, *list, env, ctx);
            let snap = lv.snapshot();
            let n = snap.len() as i64;
            let mut i = evaluate(arena, *index, env, ctx).as_i64();
            if i < 0 {
                i += n;
            } // Python-style from-end indexing, same as IndexAt
              // Out-of-range (after adjustment): no-op -- return the elements
              // unchanged, in order. The caller (a meta-rule's own where-clause,
              // mirroring `apply_drop_match_edge`'s own inert check) decides
              // whether an out-of-range/too-short drop is "inert" for its
              // purposes; this Term only performs the mechanical removal.
            let out: smallvec::SmallVec<[Value; 4]> = snap
                .iter()
                .enumerate()
                .filter(|(pos, _)| i < 0 || i >= n || *pos as i64 != i)
                .map(|(_, v)| v.clone())
                .collect();
            // KIND-PRESERVING (ARC6) — see `Append`.
            let out = std::sync::Arc::new(out);
            if matches!(lv, Value::List(_)) {
                Value::List(out)
            } else {
                Value::Tuple(out)
            }
        }
        TermNode::Intersect { a, b } => {
            try_derivation!(ctx, arena, env, "Intersect", [("a", *a), ("b", *b)]);
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            let b_snap = bv.snapshot();
            let a_snap = av.snapshot();
            let out: Vec<Value> = a_snap
                .iter()
                .filter(|x| b_snap.iter().any(|y| *x == y))
                .cloned()
                .collect();
            Value::make_frozenset(out)
        }
        TermNode::Difference { a, b } => {
            try_derivation!(ctx, arena, env, "Difference", [("a", *a), ("b", *b)]);
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            let b_snap = bv.snapshot();
            let a_snap = av.snapshot();
            let out: Vec<Value> = a_snap
                .iter()
                .filter(|x| !b_snap.iter().any(|y| *x == y))
                .cloned()
                .collect();
            Value::make_frozenset(out)
        }
        TermNode::MapSet {
            source,
            var_name,
            value,
        } => {
            let s = evaluate(arena, *source, env, ctx);
            let snap = s.snapshot();
            let mut out: Vec<Value> = Vec::with_capacity(snap.len());
            for it_ref in snap.iter() {
                env.push((*var_name, it_ref.clone()));
                let v = evaluate(arena, *value, env, ctx);
                env.pop();
                out.push(v);
            }
            Value::make_frozenset(out)
        }

        // Ordered twin of MapSet: same per-element evaluation, but collect into an
        // ORDERED LIST (preserves source order + duplicates) — list-comprehension transform.
        TermNode::MapList {
            source,
            var_name,
            value,
        } => {
            let s = evaluate(arena, *source, env, ctx);
            let snap = s.snapshot();
            let mut out: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
            for it_ref in snap.iter() {
                env.push((*var_name, it_ref.clone()));
                let v = evaluate(arena, *value, env, ctx);
                env.pop();
                out.push(v);
            }
            Value::List(std::sync::Arc::new(out))
        }

        // --- edge-attr DSL access (Phase 7 ext) ---
        TermNode::Edges {
            node,
            edge_type,
            any_type,
        } => {
            let v = evaluate(arena, *node, env, ctx);
            let Value::Node(nid) = v else {
                return Value::make_frozenset(vec![]);
            };
            let et = if *any_type { None } else { Some(*edge_type) };
            // Emit each outgoing edge as a (src, edge_type_str, tgt)
            // tuple. Tuple-shaped so EdgeAttr / Nth see it as a
            // structured handle, not an opaque integer.
            let mut out: Vec<Value> = Vec::new();
            let edges = ctx.graph.out_edges_slice(nid, et);
            crate::access_trace::note_out_edges(ctx.graph, nid, et);
            crate::scale_audit::term_units(edges.len() as u64);
            for idx in edges {
                let edge = ctx.graph.edge(*idx);
                let tup: SmallVec<[Value; 4]> = smallvec![
                    Value::Node(edge.src),
                    Value::Str(edge.edge_type),
                    Value::Node(edge.tgt),
                ];
                out.push(Value::Tuple(Arc::new(tup)));
            }
            Value::make_frozenset(out)
        }
        TermNode::NodesWhere {
            node_type,
            attr_key,
            value,
        } => {
            let v = evaluate(arena, *value, env, ctx);
            crate::access_trace::note(16, crate::access_trace::NO_ID, attr_key.0, node_type.0);
            // Try the index. If declared, this is O(1+result); if not
            // declared, fall back to a linear scan so the Term is
            // always correct.
            if ctx.graph.has_attr_index(*node_type, *attr_key) {
                let nodes: Vec<Value> = ctx
                    .graph
                    .nodes_where(*node_type, *attr_key, &v)
                    .into_iter()
                    .map(Value::Node)
                    .collect();
                for value in &nodes {
                    if let Value::Node(nid) = value {
                        crate::access_trace::note(
                            3,
                            nid.0,
                            node_type.0,
                            crate::access_trace::NO_ID,
                        );
                        crate::access_trace::note(2, nid.0, attr_key.0, crate::access_trace::NO_ID);
                    }
                }
                return Value::make_frozenset(nodes);
            }
            let mut out: Vec<Value> = Vec::new();
            for nid in ctx.graph.nodes_of_type(*node_type) {
                crate::access_trace::note(3, nid.0, node_type.0, crate::access_trace::NO_ID);
                crate::access_trace::note(2, nid.0, attr_key.0, crate::access_trace::NO_ID);
                if let Some(node_attr) = ctx.graph.node(nid).attrs.get(attr_key) {
                    if *node_attr == v {
                        out.push(Value::Node(nid));
                    }
                }
            }
            Value::make_frozenset(out)
        }
        TermNode::NodesOfType { node_type } => {
            let nodes: Vec<Value> = ctx
                .graph
                .nodes_of_type(*node_type)
                .into_iter()
                .map(Value::Node)
                .collect();
            for value in &nodes {
                if let Value::Node(nid) = value {
                    crate::access_trace::note(3, nid.0, node_type.0, crate::access_trace::NO_ID);
                }
            }
            // A single NodesOfType invocation can scan and materialize an
            // arbitrarily large population. Count its interior cardinality so
            // term-evaluation totals do not hide aggregate work.
            crate::scale_audit::term_units(nodes.len() as u64);
            Value::make_frozenset(nodes)
        }
        TermNode::AntiUnify { values, wild } => {
            let v = evaluate(arena, *values, env, ctx);
            // The instances may arrive as any collection Value; iterate its
            // members. A non-collection degenerates to a single instance.
            let insts: Vec<Value> = match &v {
                Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
                Value::Tuple(t) | Value::List(t) => t.to_vec(),
                Value::None => vec![],
                other => vec![other.clone()],
            };
            let wild_val =
                Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(*wild)]));
            anti_unify_values(&insts, &wild_val)
        }
        TermNode::FixedCount { pattern, wild } => {
            let p = evaluate(arena, *pattern, env, ctx);
            let wild_val =
                Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(*wild)]));
            Value::Int(fixed_count_value(&p, &wild_val))
        }
        TermNode::Covers {
            pattern,
            instance,
            wild,
        } => {
            let p = evaluate(arena, *pattern, env, ctx);
            let i = evaluate(arena, *instance, env, ctx);
            let wild_val =
                Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(*wild)]));
            Value::Bool(covers_value(&p, &i, &wild_val))
        }
        TermNode::CoversOpen {
            pattern,
            instance,
            wild,
        } => {
            let p = evaluate(arena, *pattern, env, ctx);
            let i = evaluate(arena, *instance, env, ctx);
            let wild_val =
                Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(*wild)]));
            Value::Bool(covers_open_value(&p, &i, &wild_val))
        }
        TermNode::AntiUnifyWitness { values, wild } => {
            let v = evaluate(arena, *values, env, ctx);
            let insts: Vec<Value> = match &v {
                Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
                Value::Tuple(t) | Value::List(t) => t.to_vec(),
                Value::None => vec![],
                other => vec![other.clone()],
            };
            let wild_val =
                Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(*wild)]));
            let (template, subs) = anti_unify_witness_values(&insts, &wild_val);
            // sigmas: one Dict (path→value) per instance, wrapped in a Tuple,
            // so the agent reads (template, (σ₁, σ₂, …)) graph-natively.
            let sigmas: SmallVec<[Value; 4]> = subs
                .into_iter()
                .map(|pairs| {
                    let mut entries: Vec<(Value, Value)> = pairs;
                    entries.sort_by(|a, b| cmp_value(&a.0, &b.0));
                    Value::Dict(std::sync::Arc::from(entries))
                })
                .collect();
            Value::Tuple(std::sync::Arc::new(smallvec::smallvec![
                template,
                Value::Tuple(std::sync::Arc::new(sigmas))
            ]))
        }
        TermNode::Substitute {
            template,
            sigma,
            wild,
        } => {
            let t = evaluate(arena, *template, env, ctx);
            let sg = evaluate(arena, *sigma, env, ctx);
            let pairs: Vec<(Value, Value)> = match &sg {
                Value::Dict(d) => d.to_vec(),
                _ => vec![],
            };
            let wild_val =
                Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(*wild)]));
            substitute_value(&t, &pairs, &wild_val)
        }
        TermNode::Unify { values, wild } => {
            let v = evaluate(arena, *values, env, ctx);
            let insts: Vec<Value> = match &v {
                Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
                Value::Tuple(t) | Value::List(t) => t.to_vec(),
                Value::None => vec![],
                other => vec![other.clone()],
            };
            let wild_val =
                Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(*wild)]));
            unify_values(&insts, &wild_val)
        }
        TermNode::StructSim { a, b, wild } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            let wild_val =
                Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(*wild)]));
            Value::Float(struct_sim_value(&av, &bv, &wild_val))
        }
        TermNode::ShapeDecode {
            goal,
            codebook_type,
            exclude,
            codebook_scope,
            beam,
            max_steps,
            cand_k,
            budget,
            field,
            wild,
            wild_objects,
        } => {
            let goal_value = evaluate(arena, *goal, env, ctx);
            let exclude_value = exclude
                .map(|idx| evaluate(arena, idx, env, ctx))
                .unwrap_or(Value::None);
            let scope_value = codebook_scope
                .map(|idx| evaluate(arena, idx, env, ctx))
                .unwrap_or(Value::None);
            let key = sd_cache_key(
                1,
                &[goal_value, exclude_value, scope_value],
                &[
                    *beam,
                    *max_steps,
                    *cand_k,
                    *budget,
                    i64::from(*wild_objects),
                ],
                &[*codebook_type, *wild],
                ctx.graph,
            );
            if let Some(hit) = ctx
                .cache
                .as_deref()
                .and_then(|cache| cache.sd_ops.get(&key))
                .cloned()
            {
                return crate::shape_decode::select_cached_field(&hit, *field, ctx.interner);
            }
            let full = crate::shape_decode::eval_shape_decode(
                arena,
                *goal,
                *codebook_type,
                *exclude,
                *codebook_scope,
                *beam,
                *max_steps,
                *cand_k,
                *budget,
                Sym::default(),
                *wild,
                *wild_objects,
                env,
                ctx,
            );
            let report = crate::shape_decode::select_cached_field(&full, *field, ctx.interner);
            if let Some(cache) = ctx.cache.as_deref_mut() {
                cache.sd_ops.insert(key, full);
            }
            report
        }
        TermNode::MotorCompose {
            episode,
            policy,
            candidate,
        } => {
            let Value::Node(ep) = evaluate(arena, *episode, env, ctx) else {
                return Value::Int(0);
            };
            let Value::Node(po) = evaluate(arena, *policy, env, ctx) else {
                return Value::Int(0);
            };
            let Value::Node(ca) = evaluate(arena, *candidate, env, ctx) else {
                return Value::Int(0);
            };
            if crate::motor_compose::motor_compose_member(ctx.graph, ctx.interner, ep, po, ca) {
                Value::Int(1)
            } else {
                Value::Int(0)
            }
        }
        TermNode::FutureManifoldProjection {
            episode,
            policy,
            source,
            addition,
            field,
        } => {
            let Value::Node(ep) = evaluate(arena, *episode, env, ctx) else {
                return Value::Float(0.0);
            };
            let Value::Node(po) = evaluate(arena, *policy, env, ctx) else {
                return Value::Float(0.0);
            };
            let Value::Node(src) = evaluate(arena, *source, env, ctx) else {
                return Value::Float(0.0);
            };
            let add = addition.and_then(|a| match evaluate(arena, a, env, ctx) {
                Value::Node(n) => Some(n),
                _ => None,
            });
            if let Some(value) = crate::future_manifold::projection_field(
                ctx.graph,
                ctx.interner,
                ep,
                po,
                src,
                add,
                *field,
            ) {
                value
            } else {
                crate::motor_compose::future_manifold_projection_field(
                    ctx.graph,
                    ctx.interner,
                    ep,
                    po,
                    src,
                    add,
                    *field,
                )
            }
        }
        TermNode::FutureManifoldSelection {
            episode,
            policy,
            candidates,
            field,
            snapshot_field,
        } => {
            let Value::Node(ep) = evaluate(arena, *episode, env, ctx) else {
                return Value::None;
            };
            let Value::Node(po) = evaluate(arena, *policy, env, ctx) else {
                return Value::None;
            };
            let candidate_values = evaluate(arena, *candidates, env, ctx);
            let mut candidate_nodes: Vec<NodeID> = Vec::new();
            for value in candidate_values.iter() {
                let Value::Node(node) = value else {
                    return Value::None;
                };
                if !candidate_nodes.contains(node) {
                    candidate_nodes.push(*node);
                }
            }
            let Some(selection) = crate::future_manifold::feasible_selection_with_projector(
                ctx.graph,
                ctx.interner,
                &candidate_nodes,
                |candidate| {
                    crate::future_manifold::projection_field(
                        ctx.graph,
                        ctx.interner,
                        ep,
                        po,
                        candidate,
                        None,
                        *snapshot_field,
                    )
                    .or_else(|| {
                        Some(crate::motor_compose::future_manifold_projection_field(
                            ctx.graph,
                            ctx.interner,
                            ep,
                            po,
                            candidate,
                            None,
                            *snapshot_field,
                        ))
                    })
                },
            ) else {
                return Value::None;
            };
            let nodes = |values: &[NodeID]| {
                Value::Tuple(Arc::new(
                    values
                        .iter()
                        .map(|node| Value::Node(*node))
                        .collect::<SmallVec<[Value; 4]>>(),
                ))
            };
            match ctx.interner.resolve(*field) {
                "unestablished" => nodes(&selection.unestablished),
                "infeasible" => nodes(&selection.infeasible),
                "feasible" => nodes(&selection.feasible),
                "minimal" => nodes(&selection.minimal),
                "selected" => nodes(&selection.selected),
                "withheld_minimal" => nodes(&selection.withheld_minimal),
                "tie_breadth" => Value::Int(selection.tie_breadth as i64),
                "audit_snapshot" => Value::Tuple(Arc::new(smallvec::smallvec![
                    Value::Int(candidate_nodes.len() as i64),
                    Value::Int(selection.unestablished.len() as i64),
                    Value::Int(selection.infeasible.len() as i64),
                    Value::Int(selection.feasible.len() as i64),
                    Value::Int(selection.minimal.len() as i64),
                    Value::Int(selection.selected.len() as i64),
                    Value::Int(selection.withheld_minimal.len() as i64),
                    Value::Int(selection.tie_breadth as i64),
                ])),
                "supported" => Value::Bool(true),
                _ => Value::None,
            }
        }
        TermNode::TransformDecode {
            goal,
            codebook_type,
            exclude,
            max_dims,
            field,
        } => {
            let goal_value = evaluate(arena, *goal, env, ctx);
            let exclude_value = exclude
                .map(|idx| evaluate(arena, idx, env, ctx))
                .unwrap_or(Value::None);
            let key = sd_cache_key(
                2,
                &[goal_value, exclude_value],
                &[*max_dims],
                &[*codebook_type],
                ctx.graph,
            );
            if let Some(hit) = ctx
                .cache
                .as_deref()
                .and_then(|cache| cache.sd_ops.get(&key))
                .cloned()
            {
                return crate::shape_decode::select_cached_field(&hit, *field, ctx.interner);
            }
            let full = crate::shape_decode::eval_transform_decode(
                arena,
                *goal,
                *codebook_type,
                *exclude,
                *max_dims,
                Sym::default(),
                env,
                ctx,
            );
            let report = crate::shape_decode::select_cached_field(&full, *field, ctx.interner);
            if let Some(cache) = ctx.cache.as_deref_mut() {
                cache.sd_ops.insert(key, full);
            }
            report
        }
        TermNode::NetForward { assemblage, inputs } => {
            crate::net_forward::eval_net_forward(arena, *assemblage, *inputs, env, ctx)
        }
        TermNode::DimInfer {
            goal,
            codebook_type,
            exclude,
            generator_type,
            max_dims,
            field,
        } => {
            let goal_value = evaluate(arena, *goal, env, ctx);
            let exclude_value = exclude
                .map(|idx| evaluate(arena, idx, env, ctx))
                .unwrap_or(Value::None);
            let key = sd_cache_key(
                3,
                &[goal_value, exclude_value],
                &[*max_dims],
                &[*codebook_type, *generator_type],
                ctx.graph,
            );
            if let Some(hit) = ctx
                .cache
                .as_deref()
                .and_then(|cache| cache.sd_ops.get(&key))
                .cloned()
            {
                return crate::shape_decode::select_cached_field(&hit, *field, ctx.interner);
            }
            let full = crate::shape_decode::eval_dim_infer(
                arena,
                *goal,
                *codebook_type,
                *exclude,
                *generator_type,
                *max_dims,
                Sym::default(),
                env,
                ctx,
            );
            let report = crate::shape_decode::select_cached_field(&full, *field, ctx.interner);
            if let Some(cache) = ctx.cache.as_deref_mut() {
                cache.sd_ops.insert(key, full);
            }
            report
        }
        TermNode::GenInfer {
            goal,
            codebook_type,
            exclude,
            max_dims,
            field,
        } => {
            let goal_value = evaluate(arena, *goal, env, ctx);
            let exclude_value = exclude
                .map(|idx| evaluate(arena, idx, env, ctx))
                .unwrap_or(Value::None);
            let key = sd_cache_key(
                4,
                &[goal_value, exclude_value],
                &[*max_dims],
                &[*codebook_type],
                ctx.graph,
            );
            if let Some(hit) = ctx
                .cache
                .as_deref()
                .and_then(|cache| cache.sd_ops.get(&key))
                .cloned()
            {
                return crate::shape_decode::select_cached_field(&hit, *field, ctx.interner);
            }
            let full = crate::shape_decode::eval_gen_infer(
                arena,
                *goal,
                *codebook_type,
                *exclude,
                *max_dims,
                Sym::default(),
                env,
                ctx,
            );
            let report = crate::shape_decode::select_cached_field(&full, *field, ctx.interner);
            if let Some(cache) = ctx.cache.as_deref_mut() {
                cache.sd_ops.insert(key, full);
            }
            report
        }
        TermNode::RatioInduce {
            population,
            codebook_type,
            resolution,
            field,
        } => crate::shape_decode::eval_ratio_infer(
            arena,
            *population,
            *codebook_type,
            *resolution,
            *field,
            env,
            ctx,
        ),
        TermNode::LogQuantum {
            population,
            value_slot,
            base_num,
            base_den,
            delta_num,
            delta_den,
            raw,
            field,
        } => crate::shape_decode::eval_log_quantum(
            arena,
            *population,
            *value_slot,
            *base_num,
            *base_den,
            *delta_num,
            *delta_den,
            *raw,
            *field,
            env,
            ctx,
        ),
        TermNode::TimeInfer {
            sequence,
            codebook_type,
            max_b,
            field,
            max_steps,
            robust,
        } => crate::shape_decode::eval_time_infer(
            arena,
            *sequence,
            *codebook_type,
            *max_b,
            *field,
            *max_steps,
            *robust,
            env,
            ctx,
        ),
        TermNode::DepthInfer {
            sequence,
            codebook_type,
            max_b,
            field,
        } => crate::shape_decode::eval_depth_infer(
            arena,
            *sequence,
            *codebook_type,
            *max_b,
            *field,
            env,
            ctx,
        ),
        TermNode::BlinkBridge {
            sequence,
            codebook_type,
            max_b,
            field,
        } => crate::shape_decode::eval_blink_bridge(
            arena,
            *sequence,
            *codebook_type,
            *max_b,
            *field,
            env,
            ctx,
        ),
        TermNode::GapAbduce {
            sequence,
            codebook_type,
            max_b,
            field,
        } => crate::shape_decode::eval_gap_abduce(
            arena,
            *sequence,
            *codebook_type,
            *max_b,
            *field,
            env,
            ctx,
        ),
        TermNode::GapVerify {
            sequence,
            codebook_type,
            max_b,
            field,
        } => crate::shape_decode::eval_gap_verify(
            arena,
            *sequence,
            *codebook_type,
            *max_b,
            *field,
            env,
            ctx,
        ),
        TermNode::SupportInfer {
            sequence,
            codebook_type,
            field,
        } => crate::shape_decode::eval_support_infer(
            arena,
            *sequence,
            *codebook_type,
            *field,
            env,
            ctx,
        ),
        TermNode::MotionEnergy {
            sequence,
            height,
            width,
            field,
        } => crate::shape_decode::eval_motion_energy(
            arena, *sequence, *height, *width, *field, env, ctx,
        ),
        TermNode::TransferDecode { goal } => {
            crate::shape_decode::eval_transfer_decode(arena, *goal, env, ctx)
        }
        TermNode::RecogniseShape { text } => {
            crate::shape_decode::eval_recognise_shape(arena, *text, env, ctx)
        }
        TermNode::MetaShapeMint {
            observation,
            obs_type,
            status_value,
            wild,
            field,
        } => crate::shape_decode::eval_meta_shape_mint(
            arena,
            *observation,
            *obs_type,
            *status_value,
            *wild,
            *field,
            env,
            ctx,
        ),
        TermNode::StrokeQuantize {
            points,
            segments,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            invariant_only,
            canonical_pose,
            turn_edges,
            len_edges,
            emit_residual,
            bounds,
            field,
            seg_sym,
            pose_x_sym,
            pose_y_sym,
            pose_o_sym,
            pose_s_sym,
        } => crate::strokes::eval_stroke_quantize(
            arena,
            *points,
            *segments,
            *turn_bins,
            *len_bins,
            *grid,
            *scale_bins,
            *invariant_only,
            *canonical_pose,
            *turn_edges,
            *len_edges,
            *emit_residual,
            *bounds,
            *field,
            *seg_sym,
            *pose_x_sym,
            *pose_y_sym,
            *pose_o_sym,
            *pose_s_sym,
            env,
            ctx,
        ),
        TermNode::StrokeRender {
            signature,
            n_points,
            apply_pose,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            turn_edges,
            len_edges,
            bounds,
            field,
        } => crate::strokes::eval_stroke_render(
            arena,
            *signature,
            *n_points,
            *apply_pose,
            *turn_bins,
            *len_bins,
            *grid,
            *scale_bins,
            *turn_edges,
            *len_edges,
            *bounds,
            *field,
            env,
            ctx,
        ),
        TermNode::SigmaLognormalGenerate {
            primitives,
            start,
            t_start,
            t_end,
            n_points,
            field,
        } => crate::sigma_lognormal::eval_sigma_lognormal_generate(
            arena,
            *primitives,
            *start,
            *t_start,
            *t_end,
            *n_points,
            *field,
            env,
            ctx,
        ),
        TermNode::LookaheadValue {
            node,
            child_edge,
            score_key,
            depth,
        } => {
            let nv = evaluate(arena, *node, env, ctx);
            let Value::Node(nid) = nv else {
                return Value::None;
            };
            let d = evaluate(arena, *depth, env, ctx).as_i64();
            Value::Float(lookahead_value(ctx.graph, nid, *child_edge, *score_key, d))
        }
        TermNode::ScalarAttrTriples { skip_prefix } => {
            let prefix = ctx.interner.resolve(*skip_prefix).to_string();
            let skip = !prefix.is_empty();
            let mut out: SmallVec<[Value; 4]> = smallvec![];
            for (nid, nd) in ctx.graph.iter_nodes() {
                crate::access_trace::note(3, nid.0, nd.type_.0, crate::access_trace::NO_ID);
                if skip && ctx.interner.resolve(nd.type_).starts_with(&prefix) {
                    continue;
                }
                for (k, v) in nd.attrs.iter() {
                    crate::access_trace::note(2, nid.0, k.0, crate::access_trace::NO_ID);
                    if matches!(v, Value::Bool(_) | Value::Int(_) | Value::Str(_)) {
                        out.push(Value::Tuple(Arc::new(smallvec![
                            Value::Str(nd.type_),
                            Value::Str(*k),
                            v.clone()
                        ])));
                    }
                }
            }
            Value::Tuple(Arc::new(out))
        }
        TermNode::AttrByName { node, name } => {
            let nv = evaluate(arena, *node, env, ctx);
            let Value::Node(nid) = nv else {
                return Value::None;
            };
            if !ctx.graph.has_node(nid) {
                return Value::None;
            }
            // `name` evaluates to a Str(sym); the attr key is the same sym
            // (same interner), so look it up directly.
            match evaluate(arena, *name, env, ctx) {
                Value::Str(key_sym) => ctx
                    .graph
                    .node(nid)
                    .attrs
                    .get(&key_sym)
                    .cloned()
                    .map(|value| {
                        crate::access_trace::note(2, nid.0, key_sym.0, crate::access_trace::NO_ID);
                        value
                    })
                    .unwrap_or_else(|| {
                        crate::access_trace::note(2, nid.0, key_sym.0, crate::access_trace::NO_ID);
                        Value::None
                    }),
                _ => Value::None,
            }
        }
        TermNode::EdgeAttr { edge, key } => {
            let v = evaluate(arena, *edge, env, ctx);
            // Decompose the (src, edge_type, tgt) handle to look up the
            // edge in the graph, then read its attr.
            let (Value::Tuple(parts) | Value::List(parts)) = v else {
                return Value::None;
            };
            if parts.len() < 3 {
                return Value::None;
            }
            let Value::Node(src) = parts[0] else {
                return Value::None;
            };
            let Value::Str(et) = parts[1] else {
                return Value::None;
            };
            let Value::Node(tgt) = parts[2] else {
                return Value::None;
            };
            let Some(idx) = ctx.graph.edge_idx(src, et, tgt) else {
                return Value::None;
            };
            crate::access_trace::note(15, src.0, key.0, tgt.0);
            ctx.graph
                .edge_attrs(idx)
                .get(key)
                .cloned()
                .unwrap_or(Value::None)
        }

        TermNode::Holds {
            concept,
            node,
            node2,
        } => {
            let Some(concepts) = ctx.concepts else {
                return Value::None;
            };
            let Some(node_idx) = node else {
                return Value::None;
            };
            // Cycle guard. Two layers:
            //   1. Visited-set on `holds_stack`: if this concept is
            //      already being evaluated upstack, we've hit a true
            //      cycle (e.g. rate_law's body Holds-references rate_law
            //      directly, or Arrhenius_equation → rate_law → ...
            //      → Arrhenius_equation). Bail with None — the concept
            //      did not produce a value in this frame.
            //   2. Depth budget (32): catches the pathological case
            //      where a non-cyclic chain runs deeper than any real
            //      concept inheritance would. Real definitions don't
            //      nest concept Holds more than a handful of levels.
            // The visited-set is the precise fix; the depth budget is
            // the belt-and-braces backstop.
            if ctx.holds_stack.contains(concept) {
                return Value::None;
            }
            if ctx.holds_depth > 256 {
                return Value::None;
            }
            let Some(&def) = concepts.get(concept) else {
                return Value::None;
            };
            // shape_mismatch_prunes_negative_problem_space at the
            // concept dispatch layer: if a shape_target is active and
            // the concept's Term-tree Shape is incompatible, the
            // concept is excluded by the substrate-level filter the
            // agent set. Returns as if the concept were undefined,
            // bumps the counter.
            if let Some(target) = ctx.shape_target {
                let def_shape = match ctx.shape_cache.as_deref_mut() {
                    Some(cache) => cache.assess_and_cache(def, arena),
                    None => crate::shape::assess_shape(def, arena),
                };
                if !crate::shape::shapes_compatible(&def_shape, &target) {
                    if let Some(c) = ctx.counters.as_deref_mut() {
                        c.on_concept_shape_pruned();
                    }
                    return Value::None;
                }
            }
            let nv = evaluate(arena, *node_idx, env, ctx);
            // Memoization key: (concept, node, optional second node).
            // Only cache when the node arguments resolve to NodeIDs (the
            // common case); otherwise the concept may be using nv as a
            // non-Node Value and caching by (Sym, None, None) would
            // collapse distinct calls. Cache is invalidated by the
            // substrate's `clear_eval_cache_on_mutation` (called after
            // any mutation in `run_rules`).
            let n2v_opt = if let Some(n2) = node2 {
                Some(evaluate(arena, *n2, env, ctx))
            } else {
                None
            };
            let cache_key = match (&nv, &n2v_opt) {
                (Value::Node(n1), Some(Value::Node(n2))) => Some((*concept, Some(*n1), Some(*n2))),
                (Value::Node(n1), None) => Some((*concept, Some(*n1), None)),
                _ => None,
            };
            if let (Some(k), Some(cache)) = (cache_key.as_ref(), ctx.cache.as_deref_mut()) {
                if let Some(hit) = cache.holds.get(k) {
                    return hit.clone();
                }
            }
            let name_x = ctx.interner.lookup("x").unwrap_or(Sym::default());
            let name_boundary = ctx.interner.lookup("boundary").unwrap_or(Sym::default());
            let saved = env.len();
            env.push((name_x, nv.clone()));
            env.push((name_boundary, nv));
            if let Some(n2v) = n2v_opt {
                let name_y = ctx.interner.lookup("y").unwrap_or(Sym::default());
                env.push((name_y, n2v));
            }
            ctx.holds_depth += 1;
            ctx.holds_stack.push(*concept);
            let r = evaluate(arena, def, env, ctx);
            ctx.holds_stack.pop();
            ctx.holds_depth -= 1;
            env.truncate(saved);
            if let (Some(k), Some(cache)) = (cache_key, ctx.cache.as_deref_mut()) {
                cache.holds.insert(k, r.clone());
            }
            r
        }

        TermNode::EvalSubgraph { node } => {
            // `node` evaluates to a NodeID that roots a Term subgraph
            // (per src/reflect.rs format). Walk that subgraph into a
            // temporary arena, evaluate the resulting Term under the
            // CURRENT env, return the Value. Anything that's not a
            // Node → None. A reconstruction error → None. holds_depth
            // bound applies (same recursion budget as Holds).
            let nv = evaluate(arena, *node, env, ctx);
            let Value::Node(nid) = nv else {
                return Value::None;
            };
            // Same cap as the Holds arm — EvalSubgraph shares the
            // holds_depth budget so a cycle that bounces through a
            // subgraph reconstruction is bounded too.
            if ctx.holds_depth > 256 {
                return Value::None;
            }
            let mut tmp_arena = TermArena::new();
            let Ok(sub_idx) =
                crate::reflect::term_from_subgraph(ctx.graph, ctx.interner, nid, &mut tmp_arena)
            else {
                return Value::None;
            };
            ctx.holds_depth += 1;
            let r = evaluate(&tmp_arena, sub_idx, env, ctx);
            ctx.holds_depth -= 1;
            r
        }

        TermNode::And { items } => {
            for c in items {
                if !evaluate(arena, *c, env, ctx).truthy() {
                    return Value::Bool(false);
                }
            }
            Value::Bool(true)
        }
        TermNode::Or { items } => {
            for c in items {
                if evaluate(arena, *c, env, ctx).truthy() {
                    return Value::Bool(true);
                }
            }
            Value::Bool(false)
        }
        TermNode::Not { arg } => {
            let inner = evaluate(arena, *arg, env, ctx).truthy();
            // FALLBACK TRACE / H2 — the ABSENCE-BRANCH hypothesis offered to
            // this rung, instrumented so it can be TESTED rather than assumed.
            // A `Not(Exists(..))` that passes on an EMPTY source is the rung's
            // candidate structural signature of a fallback.
            if !inner {
                if let TermNode::Exists { .. } = arena.get(*arg) {
                    if crate::fallback_trace::last_exists_empty() {
                        crate::fallback_trace::note_absence_branch();
                    }
                }
            }
            Value::Bool(!inner)
        }

        TermNode::Abs { arg } => {
            let v = evaluate(arena, *arg, env, ctx);
            match v {
                Value::Int(n) => Value::Int(n.abs()),
                Value::Float(f) => Value::Float(f.abs()),
                // Additive: Rational never existed before this arm, so
                // every pre-existing case above/below is untouched.
                // Reduced form stays reduced under |numerator|; overflow
                // (only possible at i64::MIN) degrades to float, honestly.
                Value::Rational(n, d) => n
                    .checked_abs()
                    .map(|an| Value::Rational(an, d))
                    .unwrap_or_else(|| Value::Float(v.as_f64().abs())),
                _ => Value::Float(v.as_f64().abs()),
            }
        }
        TermNode::Neg { arg } => {
            let v = evaluate(arena, *arg, env, ctx);
            match v {
                Value::Int(n) => Value::Int(-n),
                Value::Float(f) => Value::Float(-f),
                Value::Rational(n, d) => n
                    .checked_neg()
                    .map(|nn| Value::Rational(nn, d))
                    .unwrap_or_else(|| Value::Float(-v.as_f64())),
                _ => Value::Float(-v.as_f64()),
            }
        }
        TermNode::Plus { items } => numeric_variadic(
            arena,
            items,
            env,
            ctx,
            |a, b| a + b,
            |a, b| a + b,
            0,
            0.0,
            crate::value::rational_add,
        ),
        TermNode::Times { items } => numeric_variadic(
            arena,
            items,
            env,
            ctx,
            |a, b| a.wrapping_mul(b),
            |a, b| a * b,
            1,
            1.0,
            crate::value::rational_mul,
        ),
        TermNode::Minus { a, b } => numeric_binary(
            arena,
            *a,
            *b,
            env,
            ctx,
            |x, y| x.wrapping_sub(y),
            |x, y| x - y,
            crate::value::rational_sub,
        ),
        TermNode::Div { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            // Div stays TRUE division, always float-producing, byte-
            // identical to before this feature: this Term is used
            // pervasively outside program synthesis (bigville et al.)
            // and CANNOT change its (Int,Int) result type without a
            // sweeping regression. Exact program-domain division lives
            // LOCALLY in `ProgEval` (`prog_eval.rs`'s Div interception),
            // mirroring the pre-existing `divmod`/floor-division
            // precedent ("LOCAL to the oracle, not global"). A Rational
            // operand here (reachable only via program-domain Lit
            // values flowing into this shared Term) degrades to float
            // via `as_f64()` — honest, unchanged formula.
            let bf = bv.as_f64();
            if bf == 0.0 {
                Value::Float(0.0)
            } else {
                Value::Float(av.as_f64() / bf)
            }
        }
        TermNode::Mod { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            let bi = bv.as_i64();
            if bi == 0 {
                Value::Int(0)
            } else {
                // UNREGISTERED_OPS_WITNESS_CHECK: `i64::rem_euclid` panics
                // unconditionally (not merely under `overflow-checks`) on
                // `i64::MIN % -1` -- reachable via the search once `Shl` is
                // exposed (`1i64 << 63 == i64::MIN`) composed with `Mod`
                // (already exposed, MODSQRT_SCOPED_FIX). `wrapping_rem_euclid`
                // is the same guard `IDiv`'s own `wrapping_div` already uses
                // for the identical overflow case a few lines above/below.
                Value::Int(av.as_i64().wrapping_rem_euclid(bi))
            }
        }
        TermNode::Pow { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            // Match Python semantics: int**int gives int when result fits.
            match (&av, &bv) {
                (Value::Int(x), Value::Int(y)) if *y >= 0 && *y < 64 => {
                    Value::Int((*x).wrapping_pow(*y as u32))
                }
                // Additive: a genuinely Rational base (never reachable
                // via the (Int,Int) arm above, so it is unchanged) with
                // an integer exponent stays exact. Overflow/inapplicable
                // (e.g. 0 to a negative power) degrades to float.
                (Value::Rational(n, d), Value::Int(y)) => {
                    crate::value::rational_pow_int((*n, *d), *y)
                        .unwrap_or_else(|| Value::Float(av.as_f64().powf(bv.as_f64())))
                }
                _ => Value::Float(av.as_f64().powf(bv.as_f64())),
            }
        }
        TermNode::Sqrt { arg } => {
            let v = evaluate(arena, *arg, env, ctx).as_f64();
            if v > 0.0 {
                Value::Float(v.sqrt())
            } else {
                Value::Float(0.0)
            }
        }
        TermNode::Log { arg } => {
            let v = evaluate(arena, *arg, env, ctx).as_f64();
            // ln(x) for x>0; x<=0 -> -inf (caller-side epsilon guards the world value).
            Value::Float(if v > 0.0 { v.ln() } else { f64::NEG_INFINITY })
        }
        TermNode::Exp { arg } => Value::Float(evaluate(arena, *arg, env, ctx).as_f64().exp()),
        TermNode::DtwTo { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(banded_dtw(&av, &bv, 8))
        }
        TermNode::EnigmaCrib { candidate } => match evaluate(arena, *candidate, env, ctx) {
            Value::Node(node) => Value::Bool(crate::enigma::crib_admissible(
                ctx.graph,
                node,
                ctx.interner,
            )),
            _ => Value::Bool(false),
        },
        TermNode::EnigmaBombe { candidate } => match evaluate(arena, *candidate, env, ctx) {
            Value::Node(node) => Value::Bool(crate::enigma::bombe_admissible(
                ctx.graph,
                node,
                ctx.interner,
            )),
            _ => Value::Bool(false),
        },
        TermNode::EnigmaBombeWitness { candidate } => match evaluate(arena, *candidate, env, ctx) {
            Value::Node(node) => {
                match crate::enigma::bombe_witness(ctx.graph, node, ctx.interner) {
                    Some(witness) => Value::Surface(
                        SurfaceKind::Text,
                        Arc::from(witness.into_bytes().into_boxed_slice()),
                    ),
                    None => Value::None,
                }
            }
            _ => Value::None,
        },
        TermNode::ApcEncode {
            model,
            seq,
            start,
            end,
            out_len,
        } => {
            let mv = evaluate(arena, *model, env, ctx);
            let sv = evaluate(arena, *seq, env, ctx);
            let start = evaluate(arena, *start, env, ctx).as_f64() as i64;
            let end = evaluate(arena, *end, env, ctx).as_f64() as i64;
            let out_len = (evaluate(arena, *out_len, env, ctx).as_f64() as i64).max(1) as usize;
            // model = flat Tuple of floats; seq = Tuple of [din] frames.
            let modelv: Vec<f32> = mv.iter().map(|x| x.as_f64() as f32).collect();
            let tu = sv.iter().count();
            let din = sv.iter().next().map(|f| f.iter().count()).unwrap_or(0);
            let mut seqf: Vec<f32> = Vec::with_capacity(tu * din);
            for frame in sv.iter() {
                for x in frame.iter() {
                    seqf.push(x.as_f64() as f32);
                }
            }
            let (out, rep) = crate::apc::encode(&modelv, &seqf, tu, din, start, end, out_len);
            if rep == 0 {
                Value::Tuple(Arc::new(SmallVec::new()))
            } else {
                let mut frames: SmallVec<[Value; 4]> = SmallVec::new();
                for o in 0..out_len {
                    let mut row: SmallVec<[Value; 4]> = SmallVec::new();
                    for d in 0..rep {
                        row.push(Value::Float(out[o * rep + d] as f64));
                    }
                    frames.push(Value::Tuple(Arc::new(row)));
                }
                Value::Tuple(Arc::new(frames))
            }
        }
        TermNode::PointSetDist { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(pointset_dist(&av, &bv))
        }
        TermNode::MahalLeaf { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(mahal_leaf(&av, &bv))
        }
        TermNode::MahalFull { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(mahal_full(&av, &bv))
        }
        TermNode::DeformGenMarginal { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(deform_gen_marginal(&av, &bv))
        }
        TermNode::DeformGen { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(deform_gen(&av, &bv))
        }
        TermNode::DeformDist { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(deform_dist(&av, &bv))
        }
        TermNode::SmoothDeformDist { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(smooth_deform_dist(&av, &bv))
        }
        TermNode::TpsDeformDist { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(tps_deform_dist(&av, &bv))
        }
        TermNode::SmoothDeformComponents { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            crate::deform_metric::smooth_deform_components(&av, &bv)
        }
        TermNode::ShapeContextDist { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(shape_context_dist(&av, &bv))
        }
        TermNode::EnclosedCount { arg } => {
            let v = evaluate(arena, *arg, env, ctx);
            crate::ink_topology::enclosed_count_value(&v)
        }
        TermNode::ScTpsDist { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(sc_tps_dist(&av, &bv))
        }
        TermNode::BlendCover { unknown, a, b } => {
            let uv = evaluate(arena, *unknown, env, ctx);
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            let to_s = |v: &Value| -> String {
                match v {
                    Value::Str(sym) => ctx.interner.resolve(*sym).to_string(),
                    Value::Surface(_, by) => String::from_utf8_lossy(&by[..]).into_owned(),
                    _ => String::new(),
                }
            };
            let r = blend_cover(&to_s(&uv), &to_s(&av), &to_s(&bv));
            Value::Float(r)
        }
        TermNode::XCorrPeak { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            Value::Float(xcorr_peak(&av, &bv, 8))
        }
        TermNode::Whiten { a, b } => {
            let wv = evaluate(arena, *a, env, ctx);
            let xv = evaluate(arena, *b, env, ctx);
            whiten_cholesky(&wv, &xv)
        }
        TermNode::WhitenMany { a, b } => {
            let wv = evaluate(arena, *a, env, ctx);
            let xv = evaluate(arena, *b, env, ctx);
            whiten_many(&wv, &xv)
        }
        TermNode::WithinScatter { a, b } => {
            let dv = evaluate(arena, *a, env, ctx);
            let lv = evaluate(arena, *b, env, ctx);
            within_class_scatter(&dv, &lv)
        }
        TermNode::BetweenScatter { a, b } => {
            let dv = evaluate(arena, *a, env, ctx);
            let lv = evaluate(arena, *b, env, ctx);
            between_class_scatter(&dv, &lv)
        }
        TermNode::Min { items } => numeric_minmax(arena, items, env, ctx, true),
        TermNode::Max { items } => numeric_minmax(arena, items, env, ctx, false),
        TermNode::ArgMin { items } => numeric_argmin(arena, items, env, ctx),
        TermNode::ArgMax { items } => numeric_argmax(arena, items, env, ctx),

        TermNode::TrackIdentityCorrespondence {
            prev,
            cur,
            feature_key,
            category_key,
            extent_key,
            radius,
        } => {
            let prev_v = evaluate(arena, *prev, env, ctx);
            let cur_v = evaluate(arena, *cur, env, ctx);
            let prev_ids: Vec<NodeID> = prev_v
                .iter()
                .filter_map(|v| match v {
                    Value::Node(n) => Some(*n),
                    _ => None,
                })
                .collect();
            let cur_ids: Vec<NodeID> = cur_v
                .iter()
                .filter_map(|v| match v {
                    Value::Node(n) => Some(*n),
                    _ => None,
                })
                .collect();
            let radius_v = evaluate(arena, *radius, env, ctx);
            let m = track_identity_correspondence(
                ctx.graph,
                &prev_ids,
                &cur_ids,
                *feature_key,
                *category_key,
                *extent_key,
                radius_v.as_f64(),
            );
            let mk_key =
                |s: &str| -> Value { Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes())) };
            let matched_v: SmallVec<[Value; 4]> = m
                .matched
                .into_iter()
                .map(|(p, c)| Value::Tuple(Arc::new(smallvec![Value::Node(p), Value::Node(c)])))
                .collect();
            let births_v: SmallVec<[Value; 4]> = m.births.into_iter().map(Value::Node).collect();
            let deaths_v: SmallVec<[Value; 4]> = m.deaths.into_iter().map(Value::Node).collect();
            let mut pairs: Vec<(Value, Value)> = vec![
                (mk_key("matched"), Value::Tuple(Arc::new(matched_v))),
                (mk_key("births"), Value::Tuple(Arc::new(births_v))),
                (mk_key("deaths"), Value::Tuple(Arc::new(deaths_v))),
            ];
            pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
            Value::Dict(Arc::from(pairs))
        }

        // --- bitwise (Q1: `&`/`|`/`^` are ALSO Python set algebra —
        // dispatch on the evaluated RUNTIME type, never static syntax.
        // Both operands Set/FrozenSet → intersection/union/symmetric-
        // difference, result-typed by the LEFT operand (Python's own
        // `type(a).__and__` convention); anything else → int bitwise,
        // unchanged.) ---
        TermNode::BitAnd { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            match (as_set_like(&av), as_set_like(&bv)) {
                (Some(sa), Some(sb)) => {
                    let out: Vec<Value> = sa
                        .iter()
                        .filter(|x| sb.iter().any(|y| *x == y))
                        .cloned()
                        .collect();
                    set_result_like(&av, out)
                }
                _ => Value::Int(av.as_i64() & bv.as_i64()),
            }
        }
        TermNode::BitOr { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            match (as_set_like(&av), as_set_like(&bv)) {
                (Some(sa), Some(sb)) => {
                    let mut out: Vec<Value> = sa.iter().cloned().collect();
                    out.extend(sb.iter().cloned());
                    set_result_like(&av, out)
                }
                _ => Value::Int(av.as_i64() | bv.as_i64()),
            }
        }
        TermNode::BitXor { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            match (as_set_like(&av), as_set_like(&bv)) {
                (Some(sa), Some(sb)) => {
                    let out: Vec<Value> = sa
                        .iter()
                        .filter(|x| !sb.iter().any(|y| *x == y))
                        .cloned()
                        .chain(sb.iter().filter(|y| !sa.iter().any(|x| *x == **y)).cloned())
                        .collect();
                    set_result_like(&av, out)
                }
                _ => Value::Int(av.as_i64() ^ bv.as_i64()),
            }
        }
        TermNode::Shl { a, b } => {
            let av = evaluate(arena, *a, env, ctx).as_i64();
            let bv = evaluate(arena, *b, env, ctx).as_i64();
            if !(0..64).contains(&bv) {
                Value::Int(0)
            } else {
                Value::Int(av.wrapping_shl(bv as u32))
            }
        }
        TermNode::Lshr { a, b } => {
            let av = evaluate(arena, *a, env, ctx).as_i64();
            let bv = evaluate(arena, *b, env, ctx).as_i64();
            if !(0..64).contains(&bv) {
                Value::Int(0)
            } else {
                // Logical shift via u64 cast — zero-fills the high bits.
                Value::Int(((av as u64) >> (bv as u32)) as i64)
            }
        }
        TermNode::Ashr { a, b } => {
            let av = evaluate(arena, *a, env, ctx).as_i64();
            let bv = evaluate(arena, *b, env, ctx).as_i64();
            if !(0..64).contains(&bv) {
                // Out-of-range: arithmetic shift saturates to sign-fill.
                Value::Int(if av >= 0 { 0 } else { -1 })
            } else {
                // Rust's `>>` on i64 is arithmetic — fills with sign bit.
                Value::Int(av.wrapping_shr(bv as u32))
            }
        }

        TermNode::IDiv { a, b } => {
            let av = evaluate(arena, *a, env, ctx).as_i64();
            let bv = evaluate(arena, *b, env, ctx).as_i64();
            if bv == 0 {
                Value::Int(0)
            } else {
                // wrapping_div handles the i64::MIN / -1 overflow case.
                Value::Int(av.wrapping_div(bv))
            }
        }
        TermNode::IRem { a, b } => {
            let av = evaluate(arena, *a, env, ctx).as_i64();
            let bv = evaluate(arena, *b, env, ctx).as_i64();
            if bv == 0 {
                Value::Int(0)
            } else {
                Value::Int(av.wrapping_rem(bv))
            }
        }

        TermNode::IfThenElse { cond, then, other } => {
            if evaluate(arena, *cond, env, ctx).truthy() {
                evaluate(arena, *then, env, ctx)
            } else {
                evaluate(arena, *other, env, ctx)
            }
        }

        TermNode::Vec_ { items } => {
            let mut out: SmallVec<[Value; 4]> = SmallVec::new();
            for c in items {
                out.push(evaluate(arena, *c, env, ctx));
            }
            Value::Tuple(Arc::new(out))
        }
        TermNode::VecAdd { a, b } => vec_binary(arena, *a, *b, env, ctx, |x, y| x + y),
        TermNode::VecSub { a, b } => vec_binary(arena, *a, *b, env, ctx, |x, y| x - y),
        TermNode::Dot { a, b } => {
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            let mut total = 0.0;
            for (x, y) in av.iter().zip(bv.iter()) {
                total += x.as_f64() * y.as_f64();
            }
            Value::Float(total)
        }
        TermNode::Magnitude { arg } => {
            try_derivation!(ctx, arena, env, "Magnitude", [("arg", *arg)]);
            let v = evaluate(arena, *arg, env, ctx);
            let s: f64 = v.iter().map(|x| x.as_f64().powi(2)).sum();
            Value::Float(s.sqrt())
        }

        TermNode::Sin { arg } => Value::Float(evaluate(arena, *arg, env, ctx).as_f64().sin()),
        TermNode::Cos { arg } => Value::Float(evaluate(arena, *arg, env, ctx).as_f64().cos()),
        TermNode::Atan2 { y, x } => {
            let yv = evaluate(arena, *y, env, ctx).as_f64();
            let xv = evaluate(arena, *x, env, ctx).as_f64();
            Value::Float(yv.atan2(xv))
        }
        TermNode::Bearing { arg } => {
            try_derivation!(ctx, arena, env, "Bearing", [("arg", *arg)]);
            let v = evaluate(arena, *arg, env, ctx);
            let mut it = v.iter();
            let x = it.next().map(|v| v.as_f64()).unwrap_or(0.0);
            let y = it.next().map(|v| v.as_f64()).unwrap_or(0.0);
            Value::Float(y.atan2(x))
        }
        TermNode::Rotate { vec, angle } => {
            try_derivation!(
                ctx,
                arena,
                env,
                "Rotate",
                [("vec", *vec), ("angle", *angle)]
            );
            let v = evaluate(arena, *vec, env, ctx);
            let theta = evaluate(arena, *angle, env, ctx).as_f64();
            let (c, s) = (theta.cos(), theta.sin());
            let mut it = v.iter();
            let x = it.next().map(|v| v.as_f64()).unwrap_or(0.0);
            let y = it.next().map(|v| v.as_f64()).unwrap_or(0.0);
            let out: SmallVec<[Value; 4]> =
                smallvec![Value::Float(x * c - y * s), Value::Float(x * s + y * c)];
            Value::Tuple(Arc::new(out))
        }
        TermNode::AngleBetween { a, b } => {
            try_derivation!(ctx, arena, env, "AngleBetween", [("a", *a), ("b", *b)]);
            let av = evaluate(arena, *a, env, ctx);
            let bv = evaluate(arena, *b, env, ctx);
            let mut ai = av.iter();
            let mut bi = bv.iter();
            let ax = ai.next().map(|v| v.as_f64()).unwrap_or(0.0);
            let ay = ai.next().map(|v| v.as_f64()).unwrap_or(0.0);
            let bx = bi.next().map(|v| v.as_f64()).unwrap_or(0.0);
            let by = bi.next().map(|v| v.as_f64()).unwrap_or(0.0);
            Value::Float((ax * by - ay * bx).atan2(ax * bx + ay * by))
        }

        // --- rendering Terms — leaf shapes for now (full render path
        // builds on the engine's renderer registry in Phase 6) ---
        TermNode::Surface { kind, payload } => {
            let bytes: Arc<[u8]> = match payload {
                Value::Str(_) | Value::None => match payload {
                    Value::Str(s) => Arc::from(ctx.interner.resolve(*s).as_bytes()),
                    _ => Arc::from([].as_slice()),
                },
                Value::Surface(_, b) => b.clone(),
                _ => Arc::from(format!("{:?}", payload).as_bytes()),
            };
            Value::Surface(kind.clone(), bytes)
        }
        TermNode::Slot { name } => env_get(env, *name).cloned().unwrap_or(Value::None),
        TermNode::Label { prefix } => {
            // Without a render-context label counter we just emit a
            // synthetic label tied to the prefix's Sym id. The
            // graph-resident renderer (Phase 6) supplies a real counter.
            let s = ctx.interner.resolve(*prefix);
            Value::Surface(
                SurfaceKind::Text,
                Arc::from(format!(".L{}{}", s, prefix.0).as_bytes()),
            )
        }
        TermNode::Cat { items } => cat_or_lines(arena, items, env, ctx, b""),
        TermNode::Lines { items } => cat_or_lines(arena, items, env, ctx, b"\n"),
        TermNode::Join { separator, items } => {
            let Some(sep_idx) = separator else {
                return Value::None;
            };
            let Some(items_idx) = items else {
                return Value::None;
            };
            let sep = evaluate(arena, *sep_idx, env, ctx);
            let seq = evaluate(arena, *items_idx, env, ctx);
            // Resolve the active render Language once (if any) so variadic
            // Node elements — e.g. `Join(sep, Slot("items"))` over a source
            // term's tuple children — render in the current language rather
            // than stringify as `{:?}`. Snapshot first to release the borrow
            // on `env` before we render (which mutates `env`).
            let render_lang: Option<NodeID> = ctx
                .interner
                .lookup("render_lang")
                .and_then(|s| env_get(env, s).cloned())
                .and_then(|v| match v {
                    Value::Node(n) => Some(n),
                    _ => None,
                });
            let elems: Vec<Value> = seq.iter().cloned().collect();
            let mut parts: Vec<Vec<u8>> = Vec::new();
            for v in elems {
                match v {
                    Value::Surface(_, b) => parts.push(b.to_vec()),
                    Value::Str(s) => parts.push(ctx.interner.resolve(s).as_bytes().to_vec()),
                    // A Node element renders via the active Language — this
                    // is the variadic-children render path (Join over the
                    // ordered child Nodes of a tuple-shaped source field).
                    Value::Node(n) => {
                        if let Some(lang_nid) = render_lang {
                            match render_source_node(n, lang_nid, env, ctx) {
                                Value::Surface(_, b) => parts.push(b.to_vec()),
                                Value::Str(s) => {
                                    parts.push(ctx.interner.resolve(s).as_bytes().to_vec())
                                }
                                other => parts.push(format!("{:?}", other).into_bytes()),
                            }
                        } else {
                            parts.push(format!("{:?}", Value::Node(n)).into_bytes());
                        }
                    }
                    _ => parts.push(format!("{:?}", v).into_bytes()),
                }
            }
            let sep_bytes = match &sep {
                Value::Surface(_, b) => b.to_vec(),
                Value::Str(s) => ctx.interner.resolve(*s).as_bytes().to_vec(),
                _ => Vec::new(),
            };
            let mut out: Vec<u8> = Vec::new();
            for (i, p) in parts.iter().enumerate() {
                if i > 0 {
                    out.extend_from_slice(&sep_bytes);
                }
                out.extend_from_slice(p);
            }
            Value::Surface(SurfaceKind::Text, Arc::from(out))
        }
        TermNode::Bytes { items } => {
            let mut out: Vec<u8> = Vec::new();
            for c in items {
                let v = evaluate(arena, *c, env, ctx);
                match v {
                    Value::Surface(SurfaceKind::Bytes, b) => out.extend_from_slice(&b),
                    Value::None => return Value::None,
                    _ => return Value::None,
                }
            }
            Value::Surface(SurfaceKind::Bytes, Arc::from(out))
        }
        TermNode::U8 { expr } => {
            let Some(e) = expr else { return Value::None };
            let v = evaluate(arena, *e, env, ctx).as_i64();
            Value::Surface(SurfaceKind::Bytes, Arc::from([v as u8].as_slice()))
        }
        TermNode::U16LE { expr } => {
            let Some(e) = expr else { return Value::None };
            try_derivation!(ctx, arena, env, "U16LE", [("expr", *e)]);
            let v = evaluate(arena, *e, env, ctx).as_i64() as u16;
            Value::Surface(SurfaceKind::Bytes, Arc::from(v.to_le_bytes().as_slice()))
        }
        TermNode::U32LE { expr } => {
            let Some(e) = expr else { return Value::None };
            try_derivation!(ctx, arena, env, "U32LE", [("expr", *e)]);
            let v = evaluate(arena, *e, env, ctx).as_i64() as u32;
            Value::Surface(SurfaceKind::Bytes, Arc::from(v.to_le_bytes().as_slice()))
        }
        TermNode::U64LE { expr } => {
            let Some(e) = expr else { return Value::None };
            try_derivation!(ctx, arena, env, "U64LE", [("expr", *e)]);
            let v = evaluate(arena, *e, env, ctx).as_i64() as u64;
            Value::Surface(SurfaceKind::Bytes, Arc::from(v.to_le_bytes().as_slice()))
        }
        TermNode::LEB128 { expr } => {
            let Some(e) = expr else { return Value::None };
            let mut n = evaluate(arena, *e, env, ctx).as_i64();
            let mut out = Vec::new();
            loop {
                let b = (n & 0x7F) as u8;
                n >>= 7;
                if n == 0 {
                    out.push(b);
                    break;
                }
                out.push(b | 0x80);
            }
            Value::Surface(SurfaceKind::Bytes, Arc::from(out))
        }
        TermNode::Let { name, value, body } => {
            let Some(v_idx) = value else {
                return Value::None;
            };
            let Some(body_idx) = body else {
                return Value::None;
            };
            let v = evaluate(arena, *v_idx, env, ctx);
            env.push((*name, v));
            let r = evaluate(arena, *body_idx, env, ctx);
            env.pop();
            r
        }
        TermNode::Nth { items, index } => {
            let Some(items_idx) = items else {
                return Value::None;
            };
            let seq = evaluate(arena, *items_idx, env, ctx);
            let picked = seq
                .iter()
                .nth(*index as usize)
                .cloned()
                .unwrap_or(Value::None);
            // `nth(i)` walks at most i+1 items, or the full sequence when i
            // is out of range. Count the required traversal without changing
            // the selected value or iterator path.
            let traversed = (*index as usize).saturating_add(1).min(seq.len()) as u64;
            crate::scale_audit::term_units(traversed);
            picked
        }
        TermNode::Render { term, lang } => {
            // Render a source Term (a `Term.*` subgraph node) into a Surface via
            // the named Language's RenderRules. `term` evaluates to the source
            // Node; `lang` (or env "render_lang") to the Language Node. Find the
            // RenderRule whose `head` matches the source variant, bind its
            // binding_pattern slots to the source's `child.<name>` children, and
            // evaluate the rule's `template` subgraph under that env — nested
            // Render(Slot) sub-terms recurse on the bound children. None on a
            // render gap (no matching rule). Shares the holds_depth budget.
            let Some(t) = term else {
                return Value::None;
            };
            let Value::Node(src_nid) = evaluate(arena, *t, env, ctx) else {
                return Value::None;
            };
            if !ctx.graph.has_node(src_nid) {
                return Value::None;
            }
            let lang_val = match lang {
                Some(l) => evaluate(arena, *l, env, ctx),
                None => ctx
                    .interner
                    .lookup("render_lang")
                    .and_then(|s| env_get(env, s).cloned())
                    .unwrap_or(Value::None),
            };
            let Value::Node(lang_nid) = lang_val else {
                return Value::None;
            };
            render_source_node(src_nid, lang_nid, env, ctx)
        }
        TermNode::LitRepr { value } => {
            let Some(v_idx) = value else {
                return Value::None;
            };
            let v = evaluate(arena, *v_idx, env, ctx);
            match python_repr(&v, ctx.interner) {
                Some(s) => Value::Surface(SurfaceKind::Text, Arc::from(s.into_bytes())),
                None => Value::None,
            }
        }
    }
}

/// Faithful Python `repr()` of a SCALAR Value — `None`/`Bool`/`Int`/
/// `Float`/`Str`, the only kinds a `Lit` node's value ever holds. Any
/// other Value (Node/Tuple/Set/Dict/Surface) returns `None` — an honest
/// render gap, never an approximation. Strings prefer single quotes
/// (switching to double quotes iff the text holds a `'` and no `"`),
/// escaping backslash / the chosen quote / `\n` `\r` `\t` — faithful for
/// ordinary source text; NAMED RESIDUAL: exotic control / non-ASCII
/// escaping is not byte-identical to CPython's own `repr()` (out of this
/// wave's scope, never silently mis-rendered — those characters pass
/// through literally, which still round-trips through `exec`).
fn python_repr(v: &Value, interner: &Interner) -> Option<String> {
    Some(match v {
        Value::None => "None".to_string(),
        Value::Bool(b) => {
            if *b {
                "True".to_string()
            } else {
                "False".to_string()
            }
        }
        Value::Int(n) => n.to_string(),
        Value::Float(f) => {
            if f.is_nan() {
                "float('nan')".to_string()
            } else if f.is_infinite() {
                if *f > 0.0 {
                    "float('inf')".to_string()
                } else {
                    "float('-inf')".to_string()
                }
            } else {
                let s = f.to_string();
                // Rust's f64 Display drops the trailing ".0" Python's
                // repr always keeps for a whole-number float.
                if s.contains('.') || s.contains('e') || s.contains('E') {
                    s
                } else {
                    format!("{}.0", s)
                }
            }
        }
        Value::Str(sym) => {
            let text = interner.resolve(*sym);
            let quote = if text.contains('\'') && !text.contains('"') {
                '"'
            } else {
                '\''
            };
            let mut out = String::with_capacity(text.len() + 2);
            out.push(quote);
            for ch in text.chars() {
                match ch {
                    '\\' => out.push_str("\\\\"),
                    '\n' => out.push_str("\\n"),
                    '\r' => out.push_str("\\r"),
                    '\t' => out.push_str("\\t"),
                    c if c == quote => {
                        out.push('\\');
                        out.push(c);
                    }
                    c => out.push(c),
                }
            }
            out.push(quote);
            out
        }
        _ => return None,
    })
}

/// Render one source `Term.*` node into a Surface via `lang_nid`'s
/// RenderRules. Shared by the `Render` evaluator arm and by `Join`
/// (which renders each variadic `Value::Node` element it iterates).
///
/// Finds the RenderRule whose `head` matches the source variant, binds
/// each `binding_pattern` name to the source's children, and evaluates
/// the rule's `template` subgraph under that env. A binding name resolves
/// to (in order): a tuple-shaped variadic field (multiple `child.<name>`
/// edges, or a single one carrying an `index` edge-attr) → bound to a
/// `Value::Tuple` of the child Nodes in `index` order; OR a single
/// `child.<name>` child → bound to that `Value::Node`; OR a scalar attr →
/// bound to the attr Value. Returns `Value::None` on a render gap.
fn render_source_node(
    src_nid: NodeID,
    lang_nid: NodeID,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    if ctx.holds_depth > 256 {
        return Value::None;
    }
    // head = source node type with the "Term." prefix stripped.
    let source_type = ctx.graph.node(src_nid).type_;
    crate::access_trace::note(3, src_nid.0, source_type.0, crate::access_trace::NO_ID);
    let ty_str = ctx.interner.resolve(source_type);
    let head = ty_str.strip_prefix("Term.").unwrap_or(ty_str).to_string();
    let (Some(has_rule), Some(head_key)) =
        (ctx.interner.lookup("has_rule"), ctx.interner.lookup("head"))
    else {
        return Value::None;
    };
    let mut rule_nid: Option<NodeID> = None;
    crate::access_trace::note_out_edges(ctx.graph, lang_nid, Some(has_rule));
    for r in ctx.graph.neighbours(lang_nid, Some(has_rule)) {
        crate::access_trace::note(2, r.0, head_key.0, crate::access_trace::NO_ID);
        if let Some(Value::Str(h)) = ctx.graph.node(r).attrs.get(&head_key) {
            if ctx.interner.resolve(*h) == head.as_str() {
                rule_nid = Some(r);
                break;
            }
        }
    }
    let Some(rule_nid) = rule_nid else {
        return Value::None;
    };
    // Bind binding_pattern slots to the source's child.<name> children.
    let mut pushed = 0usize;
    if let Some(bp_key) = ctx.interner.lookup("binding_pattern") {
        crate::access_trace::note(2, rule_nid.0, bp_key.0, crate::access_trace::NO_ID);
        if let Some(bp) = ctx.graph.node(rule_nid).attrs.get(&bp_key).cloned() {
            let names: Vec<Value> = match bp {
                Value::Tuple(t) | Value::List(t) => t.iter().cloned().collect(),
                Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
                _ => Vec::new(),
            };
            let index_key = ctx.interner.lookup("index");
            for nv in names {
                let Value::Str(name_sym) = nv else {
                    continue;
                };
                // Collect every `child.<name>` out-edge (target Node + its
                // optional `index` edge-attr). A tuple-shaped (variadic)
                // field has either multiple such edges or a single edge
                // carrying an `index` attr; a plain single-child field has
                // exactly one edge with no `index`. We mirror reflect.rs:
                // sort by index and bind the tuple to a Value::Tuple of the
                // child Nodes; a lone unindexed child binds to one Node.
                let edge_name = format!("child.{}", ctx.interner.resolve(name_sym));
                let bound: Option<Value> = ctx
                    .interner
                    .lookup(&edge_name)
                    .and_then(|esym| {
                        crate::access_trace::note_out_edges(ctx.graph, src_nid, Some(esym));
                        let mut children: Vec<(i64, NodeID)> = Vec::new();
                        let mut any_indexed = false;
                        for eidx in ctx.graph.out_edges_idx(src_nid, Some(esym)) {
                            let tgt = ctx.graph.edge(eidx).tgt;
                            if let Some(ik) = index_key {
                                crate::access_trace::note(15, src_nid.0, ik.0, tgt.0);
                            }
                            let idx = index_key
                                .and_then(|ik| ctx.graph.edge_attrs(eidx).get(&ik))
                                .map(|v| {
                                    any_indexed = true;
                                    v.as_i64()
                                })
                                .unwrap_or(i64::MIN);
                            children.push((idx, tgt));
                        }
                        if children.is_empty() {
                            return None;
                        }
                        if any_indexed || children.len() > 1 {
                            // Variadic / tuple-shaped field → ordered Tuple
                            // of child Nodes (index order, reflect.rs parity).
                            children.sort_by_key(|(i, _)| *i);
                            let tup: SmallVec<[Value; 4]> =
                                children.iter().map(|(_, n)| Value::Node(*n)).collect();
                            Some(Value::Tuple(Arc::new(tup)))
                        } else {
                            // Single child Term.
                            Some(Value::Node(children[0].1))
                        }
                    })
                    .or_else(|| {
                        // Scalar field: a node attr bound directly.
                        crate::access_trace::note(
                            2,
                            src_nid.0,
                            name_sym.0,
                            crate::access_trace::NO_ID,
                        );
                        ctx.graph.node(src_nid).attrs.get(&name_sym).cloned()
                    });
                if let Some(v) = bound {
                    env.push((name_sym, v));
                    pushed += 1;
                }
            }
        }
    }
    // Evaluate the template subgraph under the slot env.
    let mut result = Value::None;
    if let Some(tmpl_key) = ctx.interner.lookup("template") {
        crate::access_trace::note_out_edges(ctx.graph, rule_nid, Some(tmpl_key));
        let tmpls = ctx.graph.neighbours(rule_nid, Some(tmpl_key));
        if let Some(&tmpl_nid) = tmpls.first() {
            let mut tmp = TermArena::new();
            if let Ok(sub) =
                crate::reflect::term_from_subgraph(ctx.graph, ctx.interner, tmpl_nid, &mut tmp)
            {
                ctx.holds_depth += 1;
                result = evaluate(&tmp, sub, env, ctx);
                ctx.holds_depth -= 1;
            }
        }
    }
    for _ in 0..pushed {
        env.pop();
    }
    result
}

// --- helpers ---

fn cmp_bool(
    arena: &TermArena,
    a: TermIdx,
    b: TermIdx,
    env: &mut Env,
    ctx: &mut EvalCtx,
    target: std::cmp::Ordering,
    allow_equal: bool,
) -> Value {
    let av = evaluate(arena, a, env, ctx);
    let bv = evaluate(arena, b, env, ctx);
    // REPORTED-ORDER site (Lt/Lte/Gt/Gte): the boolean truth this returns is
    // exactly what a caller/rule observes, so string comparisons must be
    // real lexicographic order, not `cmp_value`'s boot-history Sym-id order.
    // See CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md.
    let ord = crate::value::cmp_value_lex(&av, &bv, ctx.interner);
    let ok = if allow_equal {
        ord == target || ord == std::cmp::Ordering::Equal
    } else {
        ord == target
    };
    Value::Bool(ok)
}

fn cached_neighbours(
    ctx: &mut EvalCtx,
    nid: NodeID,
    edge_type: Sym,
    any_type: bool,
    is_in: bool,
    compute: impl FnOnce() -> Vec<Value>,
) -> Value {
    // Use Sym(0) (empty string) as the "any_type" cache key marker so
    // we don't have to bloat the cache key with an Option<Sym>.
    let key = (
        nid,
        if any_type { Sym::default() } else { edge_type },
        is_in,
    );
    if let Some(cache) = ctx.cache.as_deref() {
        if let Some(hit) = cache.neighbours.get(&key) {
            if let Some(c) = ctx.counters.as_deref_mut() {
                c.on_cache_neighbours(true);
            }
            return hit.clone();
        }
    }
    if let Some(c) = ctx.counters.as_deref_mut() {
        c.on_cache_neighbours(false);
    }
    let v = Value::make_frozenset(compute());
    if let Some(cache) = ctx.cache.as_deref_mut() {
        cache.neighbours.insert(key, v.clone());
    }
    v
}

/// `exact_op` combines two (numerator, denominator) pairs exactly
/// (`rational_add`/`rational_mul`) — Plus/Times's Rational-aware sibling
/// of `int_op`/`float_op`. ADDITIVE ONLY: when no `Rational` ever
/// appears among `items` (every pre-existing caller, forever, since
/// Rational didn't exist before this feature), `all_exact` is driven
/// purely by Int/Bool contributions and this function is BYTE-IDENTICAL
/// to its pre-Rational form — the `all_int`/`acc_i`/`acc_f` bookkeeping
/// and the two return arms (`Value::Int`/`Value::Float`) are untouched.
fn numeric_variadic(
    arena: &TermArena,
    items: &[TermIdx],
    env: &mut Env,
    ctx: &mut EvalCtx,
    int_op: impl Fn(i64, i64) -> i64,
    float_op: impl Fn(f64, f64) -> f64,
    int_init: i64,
    float_init: f64,
    exact_op: impl Fn((i64, i64), (i64, i64)) -> Option<Value>,
) -> Value {
    let mut all_int = true;
    let mut acc_i = int_init;
    let mut acc_f = float_init;
    let mut acc_r: (i64, i64) = (int_init, 1);
    let mut all_exact = true;
    for c in items {
        let v = evaluate(arena, *c, env, ctx);
        match v {
            Value::Int(n) => {
                acc_i = int_op(acc_i, n);
                acc_f = float_op(acc_f, n as f64);
                if all_exact {
                    match exact_op(acc_r, (n, 1)).and_then(|rv| crate::value::rational_parts(&rv)) {
                        Some(p) => acc_r = p,
                        None => all_exact = false,
                    }
                }
            }
            Value::Float(f) => {
                acc_f = float_op(acc_f, f);
                all_int = false;
                all_exact = false;
            }
            Value::Bool(b) => {
                let n = if b { 1 } else { 0 };
                acc_i = int_op(acc_i, n);
                acc_f = float_op(acc_f, n as f64);
                if all_exact {
                    match exact_op(acc_r, (n, 1)).and_then(|rv| crate::value::rational_parts(&rv)) {
                        Some(p) => acc_r = p,
                        None => all_exact = false,
                    }
                }
            }
            // NEW variant, NEW branch: unreachable before this feature.
            Value::Rational(n, d) => {
                all_int = false;
                acc_f = float_op(acc_f, n as f64 / d as f64);
                if all_exact {
                    match exact_op(acc_r, (n, d)).and_then(|rv| crate::value::rational_parts(&rv)) {
                        Some(p) => acc_r = p,
                        None => all_exact = false,
                    }
                }
            }
            // ABSENCE — the `P0` idiom working as intended. A missing attr
            // reads Value::None, contributes the identity, and the whole
            // term yields 0. Silent, and must stay silent.
            Value::None => {}
            // PRESENT BUT NOT A NUMBER — a category error, and until
            // 2026-08-10 it was indistinguishable from the line above.
            // Value semantics are unchanged (still contributes the
            // identity, so every existing seed is byte-identical); the
            // only difference is that it is now COUNTABLE. See
            // Counters::numeric_op_non_numeric_operand for the F-16
            // measurement that found this: `P0` on a Str compares FALSE
            // forever against a real string term, which silently forced
            // the "varied" branch on a byte-identical program.
            _ => {
                if let Some(counters) = ctx.counters.as_deref_mut() {
                    counters.numeric_op_non_numeric_operand =
                        counters.numeric_op_non_numeric_operand.saturating_add(1);
                }
            }
        }
    }
    if all_int {
        Value::Int(acc_i)
    } else if all_exact {
        crate::value::make_rational(acc_r.0, acc_r.1).unwrap_or(Value::Float(acc_f))
    } else {
        Value::Float(acc_f)
    }
}

/// `exact_op` is Minus's Rational-aware sibling of `int_op`/`float_op`
/// (`rational_sub`). ADDITIVE ONLY: the `(Int, Int)` fast path and the
/// float fallback formula are BYTE-IDENTICAL to the pre-Rational form —
/// the only new branch is the middle one, reachable only once a
/// `Rational` value exists at all.
fn numeric_binary(
    arena: &TermArena,
    a: TermIdx,
    b: TermIdx,
    env: &mut Env,
    ctx: &mut EvalCtx,
    int_op: impl Fn(i64, i64) -> i64,
    float_op: impl Fn(f64, f64) -> f64,
    exact_op: impl Fn((i64, i64), (i64, i64)) -> Option<Value>,
) -> Value {
    let av = evaluate(arena, a, env, ctx);
    let bv = evaluate(arena, b, env, ctx);
    if let (Value::Int(x), Value::Int(y)) = (&av, &bv) {
        Value::Int(int_op(*x, *y))
    } else if let (Some(pa), Some(pb)) = (
        crate::value::rational_parts(&av),
        crate::value::rational_parts(&bv),
    ) {
        exact_op(pa, pb).unwrap_or_else(|| Value::Float(float_op(av.as_f64(), bv.as_f64())))
    } else {
        Value::Float(float_op(av.as_f64(), bv.as_f64()))
    }
}

fn numeric_argmin(arena: &TermArena, items: &[TermIdx], env: &mut Env, ctx: &mut EvalCtx) -> Value {
    // AUDIT (default OFF) — see `numeric_argmax` / `audit_index_selector`.
    let auditing = selector_audit::enabled();
    let mut best: Option<(usize, Value)> = None;
    for (i, c) in items.iter().enumerate() {
        let v = evaluate(arena, *c, env, ctx);
        // REPORTED-ORDER site (`ArgMin`): the winning INDEX this returns is
        // decided by this comparison — must be real lexicographic order for
        // string-valued items, not `cmp_value`'s boot-order.
        let take = match &best {
            None => true,
            Some((_, cur)) => matches!(
                crate::value::cmp_value_lex(&v, cur, ctx.interner),
                std::cmp::Ordering::Less
            ),
        };
        if take {
            best = Some((i, v));
        }
    }
    if auditing {
        return audit_index_selector(arena, "ArgMin", items, best, env, ctx);
    }
    Value::Int(best.map(|(i, _)| i as i64).unwrap_or(0))
}
fn numeric_minmax(
    arena: &TermArena,
    items: &[TermIdx],
    env: &mut Env,
    ctx: &mut EvalCtx,
    want_min: bool,
) -> Value {
    let mut best: Option<Value> = None;
    for c in items {
        let v = evaluate(arena, *c, env, ctx);
        best = Some(match best {
            None => v,
            Some(cur) => {
                // REPORTED-ORDER site (`Min`/`Max`): the returned VALUE is
                // decided here — see `numeric_argmin`.
                let take_new = match crate::value::cmp_value_lex(&v, &cur, ctx.interner) {
                    std::cmp::Ordering::Less => want_min,
                    std::cmp::Ordering::Greater => !want_min,
                    _ => false,
                };
                if take_new {
                    v
                } else {
                    cur
                }
            }
        });
    }
    best.unwrap_or(Value::Int(0))
}

fn numeric_argmax(arena: &TermArena, items: &[TermIdx], env: &mut Env, ctx: &mut EvalCtx) -> Value {
    // AUDIT (default OFF) — the index-selector arm of the same instrument.
    // `ArgMax { items }` has no binder and no `value` Term: it reduces a LIST of
    // Terms to the INDEX of the extremum. The invariant is the same one —
    // re-evaluate the item the selector actually chose and compare it to the
    // extremum the selector recorded.
    let auditing = selector_audit::enabled();
    let mut best: Option<(usize, Value)> = None;
    for (i, c) in items.iter().enumerate() {
        let v = evaluate(arena, *c, env, ctx);
        // REPORTED-ORDER site (`ArgMax`) — see `numeric_argmin`.
        let take = match &best {
            None => true,
            Some((_, cur)) => matches!(
                crate::value::cmp_value_lex(&v, cur, ctx.interner),
                std::cmp::Ordering::Greater
            ),
        };
        if take {
            best = Some((i, v));
        }
    }
    if auditing {
        return audit_index_selector(arena, "ArgMax", items, best, env, ctx);
    }
    Value::Int(best.map(|(i, _)| i as i64).unwrap_or(0))
}

/// Index-selector arm of the audit, shared by `ArgMax` / `ArgMin` over `items`.
/// Re-evaluates the item the selector actually chose and compares it to the
/// extremum the selector recorded — the same invariant as the binder selectors,
/// with the item index standing in for the bound element.
fn audit_index_selector(
    arena: &TermArena,
    selector: &str,
    items: &[TermIdx],
    best: Option<(usize, Value)>,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    selector_audit::note_candidates(items.len() as u64);
    let Some((idx, recorded)) = best else {
        selector_audit::note_empty();
        return Value::Int(0);
    };
    // POSITIVE CONTROL: return index 0 regardless (unreachable when off).
    let returned = if selector_audit::fault_inject_first() {
        0
    } else {
        idx
    };
    let chosen = items[returned];
    if value_term_is_replayable(arena, chosen) {
        let winner_value = evaluate(arena, chosen, env, ctx);
        selector_audit::note_firing();
        if cmp_value(&winner_value, &recorded) != std::cmp::Ordering::Equal {
            selector_audit::note_disagreement(
                selector,
                &format!("items[{returned}]"),
                &format!("{winner_value:?}"),
                &format!("{recorded:?}"),
                items.len(),
            );
        }
    } else {
        selector_audit::note_skipped_effectful();
    }
    Value::Int(returned as i64)
}

/// Banded (Sakoe-Chiba) dynamic-time-warping distance between two
/// feature trajectories, each a Tuple of frames (each frame a Tuple of
/// band floats). Returns the path cost normalised by reference length.
/// Mirrors the Python `dtw` the bottom-up baseline uses, so the AxS
/// score is directly comparable to instance<->instance matching. The
/// genuinely new primitive analysis-by-synthesis needs: synthesis is at
/// the I/O boundary (the adapter calls speak()), this distance kernel is
/// the Term, and the argmax decision is composed in the graph.
/// whiten_cholesky — within-class WHITENING (the agent's specified matrix primitive).
/// w = symmetric PD matrix W (Tuple of Tuple of Float), x = vector (Tuple of Float).
/// Returns y = L^-1 x where W = L L^T (Cholesky), so ||y||^2 = x^T W^-1 x is the
/// Mahalanobis metric that suppresses the within-class scatter directions.
fn whiten_cholesky(w: &Value, x: &Value) -> Value {
    let rows: Vec<Vec<f64>> = w
        .iter()
        .map(|r| r.iter().map(|v| v.as_f64()).collect())
        .collect();
    let xv: Vec<f64> = x.iter().map(|v| v.as_f64()).collect();
    let n = rows.len();
    if n == 0 || xv.len() != n || rows.iter().any(|r| r.len() != n) {
        return x.clone();
    }
    // Cholesky: W = L L^T (lower), tiny floor for PD safety.
    let mut l = vec![vec![0.0f64; n]; n];
    for i in 0..n {
        for j in 0..=i {
            let mut s = rows[i][j];
            for k in 0..j {
                s -= l[i][k] * l[j][k];
            }
            if i == j {
                l[i][j] = if s > 1e-12 { s.sqrt() } else { 1e-6 };
            } else {
                let d = if l[j][j].abs() > 1e-12 { l[j][j] } else { 1e-6 };
                l[i][j] = s / d;
            }
        }
    }
    // forward-solve L y = x
    let mut y = vec![0.0f64; n];
    for i in 0..n {
        let mut s = xv[i];
        for k in 0..i {
            s -= l[i][k] * y[k];
        }
        let d = if l[i][i].abs() > 1e-12 { l[i][i] } else { 1e-6 };
        y[i] = s / d;
    }
    let mut out: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
    for v in y {
        out.push(Value::Float(v));
    }
    Value::Tuple(std::sync::Arc::new(out))
}

/// whiten_many — batch Whiten: factor W = L L^T ONCE, forward-solve L y = x per row of
/// X. The agent's perf realisation (the Cholesky is shared across rows).
fn whiten_many(w: &Value, xs: &Value) -> Value {
    let rows: Vec<Vec<f64>> = w
        .iter()
        .map(|r| r.iter().map(|v| v.as_f64()).collect())
        .collect();
    let xrows: Vec<Vec<f64>> = xs
        .iter()
        .map(|r| r.iter().map(|v| v.as_f64()).collect())
        .collect();
    let n = rows.len();
    if n == 0 || rows.iter().any(|r| r.len() != n) {
        return xs.clone();
    }
    // Cholesky ONCE: W = L L^T (lower), tiny floor for PD safety.
    let mut l = vec![vec![0.0f64; n]; n];
    for i in 0..n {
        for j in 0..=i {
            let mut s = rows[i][j];
            for k in 0..j {
                s -= l[i][k] * l[j][k];
            }
            if i == j {
                l[i][j] = if s > 1e-12 { s.sqrt() } else { 1e-6 };
            } else {
                let d = if l[j][j].abs() > 1e-12 { l[j][j] } else { 1e-6 };
                l[i][j] = s / d;
            }
        }
    }
    // batch forward-solve L y = x per row (shares the factor).
    let mut out: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
    for x in &xrows {
        let mut inner: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
        if x.len() != n {
            for v in x {
                inner.push(Value::Float(*v));
            }
            out.push(Value::Tuple(std::sync::Arc::new(inner)));
            continue;
        }
        let mut y = vec![0.0f64; n];
        for i in 0..n {
            let mut s = x[i];
            for k in 0..i {
                s -= l[i][k] * y[k];
            }
            let d = if l[i][i].abs() > 1e-12 { l[i][i] } else { 1e-6 };
            y[i] = s / d;
        }
        for v in y {
            inner.push(Value::Float(v));
        }
        out.push(Value::Tuple(std::sync::Arc::new(inner)));
    }
    Value::Tuple(std::sync::Arc::new(out))
}

/// within_class_scatter — the agent's covariance primitive. vecs = data (Tuple of
/// token vectors), labels = class labels (Tuple of Float). Returns the regularized
/// within-class scatter W = avg over classes of (x-mu_c)(x-mu_c)^T (diagonal-shrunk).
fn within_class_scatter(vecs: &Value, labels: &Value) -> Value {
    let rows: Vec<Vec<f64>> = vecs
        .iter()
        .map(|r| r.iter().map(|v| v.as_f64()).collect())
        .collect();
    let labs: Vec<i64> = labels.iter().map(|v| v.as_f64().round() as i64).collect();
    let n = rows.len();
    let empty = || Value::Tuple(std::sync::Arc::new(smallvec::SmallVec::<[Value; 4]>::new()));
    if n == 0 || labs.len() != n {
        return empty();
    }
    let d = rows[0].len();
    if d == 0 || rows.iter().any(|r| r.len() != d) {
        return empty();
    }
    let mut classes = labs.clone();
    classes.sort_unstable();
    classes.dedup();
    let mut w = vec![vec![0.0f64; d]; d];
    for &c in &classes {
        let idx: Vec<usize> = (0..n).filter(|&i| labs[i] == c).collect();
        if idx.is_empty() {
            continue;
        }
        let m = idx.len() as f64;
        let mut mu = vec![0.0f64; d];
        for &i in &idx {
            for k in 0..d {
                mu[k] += rows[i][k];
            }
        }
        for k in 0..d {
            mu[k] /= m;
        }
        for &i in &idx {
            for a in 0..d {
                let ca = rows[i][a] - mu[a];
                for b in 0..d {
                    w[a][b] += ca * (rows[i][b] - mu[b]);
                }
            }
        }
    }
    let nn = n as f64;
    for a in 0..d {
        for b in 0..d {
            w[a][b] /= nn;
        }
    }
    // diagonal shrinkage (regularized covariance estimate)
    let s = 0.3f64;
    let mut tr = 0.0;
    for a in 0..d {
        tr += w[a][a];
    }
    let lam = s * tr / (d as f64);
    for a in 0..d {
        for b in 0..d {
            w[a][b] *= 1.0 - s;
        }
        w[a][a] += lam;
    }
    let mut outer: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
    for a in 0..d {
        let mut inner: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
        for b in 0..d {
            inner.push(Value::Float(w[a][b]));
        }
        outer.push(Value::Tuple(std::sync::Arc::new(inner)));
    }
    Value::Tuple(std::sync::Arc::new(outer))
}

/// between_class_scatter — the agent's between-scatter primitive. vecs = data, labels =
/// group labels. Returns Sb = (1/N) sum_c n_c (mu_c - mu)(mu_c - mu)^T (scatter of the
/// group means about the global mean) — the between-observed-group nuisance scatter.
fn between_class_scatter(vecs: &Value, labels: &Value) -> Value {
    let rows: Vec<Vec<f64>> = vecs
        .iter()
        .map(|r| r.iter().map(|v| v.as_f64()).collect())
        .collect();
    let labs: Vec<i64> = labels.iter().map(|v| v.as_f64().round() as i64).collect();
    let n = rows.len();
    let empty = || Value::Tuple(std::sync::Arc::new(smallvec::SmallVec::<[Value; 4]>::new()));
    if n == 0 || labs.len() != n {
        return empty();
    }
    let d = rows[0].len();
    if d == 0 || rows.iter().any(|r| r.len() != d) {
        return empty();
    }
    let mut gmu = vec![0.0f64; d];
    for i in 0..n {
        for k in 0..d {
            gmu[k] += rows[i][k];
        }
    }
    for k in 0..d {
        gmu[k] /= n as f64;
    }
    let mut classes = labs.clone();
    classes.sort_unstable();
    classes.dedup();
    let mut sb = vec![vec![0.0f64; d]; d];
    for &c in &classes {
        let idx: Vec<usize> = (0..n).filter(|&i| labs[i] == c).collect();
        if idx.is_empty() {
            continue;
        }
        let nc = idx.len() as f64;
        let mut mu = vec![0.0f64; d];
        for &i in &idx {
            for k in 0..d {
                mu[k] += rows[i][k];
            }
        }
        for k in 0..d {
            mu[k] /= nc;
        }
        let diff: Vec<f64> = (0..d).map(|k| mu[k] - gmu[k]).collect();
        for a in 0..d {
            for b in 0..d {
                sb[a][b] += nc * diff[a] * diff[b];
            }
        }
    }
    for a in 0..d {
        for b in 0..d {
            sb[a][b] /= n as f64;
        }
    }
    let mut outer: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
    for a in 0..d {
        let mut inner: smallvec::SmallVec<[Value; 4]> = smallvec::smallvec![];
        for b in 0..d {
            inner.push(Value::Float(sb[a][b]));
        }
        outer.push(Value::Tuple(std::sync::Arc::new(inner)));
    }
    Value::Tuple(std::sync::Arc::new(outer))
}

// --- the jabberwock-authored portmanteau kernel (see BlendCover Term) ---
fn blend_cover(unknown: &str, a: &str, b: &str) -> f64 {
    // Shapes are ordered character sequences (a proxy for phonemes).
    let u: Vec<u8> = unknown.as_bytes().to_vec();
    let av: Vec<u8> = a.as_bytes().to_vec();
    let bv: Vec<u8> = b.as_bytes().to_vec();
    let n = u.len();
    if n == 0 {
        return 0.0;
    }

    // Fuzzy match between a shape `x` and a target segment `seg`: a
    // length-normalised Levenshtein similarity in [0,1]. Edits model the
    // sounds dropped / shortened / shared at a seam. Empty segment covers
    // nothing, so its similarity is 0.
    fn sim(x: &[u8], seg: &[u8]) -> f64 {
        let m = x.len();
        let k = seg.len();
        if k == 0 || m == 0 {
            return 0.0;
        }
        // Standard edit-distance DP over (m+1) x (k+1), single rolling row.
        let mut prev: Vec<usize> = (0..=k).collect();
        for i in 1..=m {
            let mut cur = vec![0usize; k + 1];
            cur[0] = i;
            for j in 1..=k {
                let cost = if x[i - 1] == seg[j - 1] { 0 } else { 1 };
                cur[j] = (prev[j] + 1).min(cur[j - 1] + 1).min(prev[j - 1] + cost);
            }
            prev = cur;
        }
        let dist = prev[k] as f64;
        let denom = m.max(k) as f64;
        (1.0 - dist / denom).max(0.0)
    }

    // Search every fused configuration: `a` covers the head region [0, h),
    // `b` covers the tail region [t, n); they OVERLAP in the shared middle
    // [t, h) whenever h > t (no clean split required, t == h is a clean cut,
    // and h == n / t == n degenerates to a single-word cover — so a == b is
    // handled too). Keep the best.
    let mut best = 0.0f64;
    for h in 0..=n {
        for t in 0..=h {
            let head = &u[0..h];
            let tail = &u[t..n];
            let sa = sim(&av, head); // front/head cover
            let sb = sim(&bv, tail); // body/tail cover

            // Length-weighted cover: the shared seam region is counted by
            // both sides, so an overlap where both shapes agree stays high.
            let wa = h as f64;
            let wb = (n - t) as f64;
            let denom = wa + wb;
            if denom <= 0.0 {
                continue;
            }
            let base = (wa * sa + wb * sb) / denom;

            // Seam handling: reward a genuine OVERLAPPING fusion over a clean
            // cut, but subtract seam-distortion that grows when the overlap
            // over-claims (the two shapes fight for too much shared middle).
            let overlap = (h - t) as f64;
            let bonus = if overlap > 0.0 { 0.08 } else { 0.0 };
            let r = overlap / n as f64;
            let distortion = 0.5 * r * r;

            let score = (base + bonus - distortion).clamp(0.0, 1.0);
            if score > best {
                best = score;
            }
        }
    }
    best
}

fn banded_dtw(a: &Value, b: &Value, band: usize) -> f64 {
    // Materialise each side as rows of f64 vectors.
    fn rows(v: &Value) -> Vec<Vec<f64>> {
        v.iter()
            .map(|frame| frame.iter().map(|x| x.as_f64()).collect::<Vec<f64>>())
            .collect()
    }
    let ra = rows(a);
    let rb = rows(b);
    let na = ra.len();
    let nb = rb.len();
    if na == 0 || nb == 0 {
        return f64::INFINITY;
    }
    let frame_dist = |i: usize, j: usize| -> f64 {
        let fa = &ra[i];
        let fb = &rb[j];
        let n = fa.len().min(fb.len());
        let mut s = 0.0;
        for k in 0..n {
            let d = fa[k] - fb[k];
            s += d * d;
        }
        s.sqrt()
    };
    const INF: f64 = 1e18;
    // DP over (na+1) x (nb+1) with a Sakoe-Chiba band on |i-j|.
    let mut prev = vec![INF; nb + 1];
    prev[0] = 0.0;
    for i in 1..=na {
        let mut cur = vec![INF; nb + 1];
        // band proportional so trajectories of differing length still
        // align; matches the baseline's banded behaviour.
        let center = i * nb / na.max(1);
        let jl = center.saturating_sub(band).max(1);
        let jh = (center + band).min(nb);
        for j in jl..=jh {
            let d = frame_dist(i - 1, j - 1);
            let best = prev[j].min(cur[j - 1]).min(prev[j - 1]);
            cur[j] = d + best;
        }
        prev = cur;
    }
    if prev[nb] >= INF {
        // Band too tight for this length ratio — fall back to the
        // diagonal cost so the distance is finite and comparable.
        let n = na.min(nb);
        let mut s = 0.0;
        for k in 0..n {
            s += frame_dist(k * na / n.max(1), k * nb / n.max(1));
        }
        return s / n.max(1) as f64;
    }
    prev[nb] / na.max(1) as f64
}

fn mahal_leaf(a: &Value, b: &Value) -> f64 {
    // GENERATIVE LEAF: diagonal Mahalanobis cost of an observed leaf `a` under a learned primitive model
    // `b` = [mean ++ inv_std]. `a` is a point list (frames of [x,y]); flatten it. `b` is a flat vector of
    // length 2*len(a_flat): the first half is the primitive mean, the second the per-dim inverse std. The
    // cost = sum_i ( inv_std_i * (a_i - mean_i) )^2 — the neg log-likelihood (up to const) under the
    // primitive's diagonal Gaussian; the primitive's natural deformation directions (large std) cost less.
    let mut af: Vec<f64> = Vec::new();
    for frame in a.iter() {
        for x in frame.iter() {
            af.push(x.as_f64());
        }
    }
    let bf: Vec<f64> = b.iter().map(|x| x.as_f64()).collect();
    let n = af.len();
    if n == 0 || bf.len() < 2 * n {
        return f64::INFINITY;
    }
    let mut s = 0.0;
    for i in 0..n {
        let d = (af[i] - bf[i]) * bf[n + i];
        s += d * d;
    }
    (s / n as f64).sqrt() // RMS Mahalanobis -> same scale as PointSetDist (so the marginal's exp() is well-conditioned)
}

fn mahal_full(a: &Value, b: &Value) -> f64 {
    // FULL-COVARIANCE generative leaf: `a` = observed leaf points (flatten, len d); `b` = [mean (d) ++
    // precision (d*d, row-major)]. cost = sqrt( (a-mean)^T P (a-mean) / d ) — RMS Mahalanobis under the
    // primitive's full inverse-covariance, so CORRELATED deformation modes (points moving together) cost
    // little, unlike the diagonal MahalLeaf.
    let mut af: Vec<f64> = Vec::new();
    for frame in a.iter() {
        for x in frame.iter() {
            af.push(x.as_f64());
        }
    }
    let bf: Vec<f64> = b.iter().map(|x| x.as_f64()).collect();
    let d = af.len();
    if d == 0 || bf.len() < d + d * d {
        return f64::INFINITY;
    }
    let diff: Vec<f64> = (0..d).map(|i| af[i] - bf[i]).collect();
    let prec = &bf[d..d + d * d];
    let mut s = 0.0;
    for i in 0..d {
        let mut row = 0.0;
        for j in 0..d {
            row += prec[i * d + j] * diff[j];
        }
        s += diff[i] * row;
    }
    (s.max(0.0) / d as f64).sqrt()
}

fn pointset_dist(a: &Value, b: &Value) -> f64 {
    // ORDER-INVARIANT shape distance: symmetric Modified Hausdorff Distance
    // (Dubuisson-Jain 1994). Each side is materialised as rows of f64 (points x
    // coords), exactly like banded_dtw's `rows` — but the sequence is ignored:
    // we compare the two POINT SETS. d(A,B) = mean_{a in A} min_{b in B} ||a-b||;
    // the symmetric distance is max(d(A,B), d(B,A)). Robust to outliers (mean of
    // nearest-neighbours, not the max), so it absorbs stroke-order / stroke-count
    // differences across writers that DTW's ordered warp cannot.
    fn rows(v: &Value) -> Vec<Vec<f64>> {
        v.iter()
            .map(|frame| frame.iter().map(|x| x.as_f64()).collect::<Vec<f64>>())
            .collect()
    }
    let ra = rows(a);
    let rb = rows(b);
    if ra.is_empty() || rb.is_empty() {
        return f64::INFINITY;
    }
    let pt_dist = |p: &[f64], q: &[f64]| -> f64 {
        let n = p.len().min(q.len());
        let mut s = 0.0;
        for k in 0..n {
            let d = p[k] - q[k];
            s += d * d;
        }
        s.sqrt()
    };
    let directed = |xs: &Vec<Vec<f64>>, ys: &Vec<Vec<f64>>| -> f64 {
        let mut acc = 0.0;
        for p in xs {
            let mut best = f64::INFINITY;
            for q in ys {
                let d = pt_dist(p, q);
                if d < best {
                    best = d;
                }
            }
            acc += best;
        }
        acc / xs.len() as f64
    };
    directed(&ra, &rb).max(directed(&rb, &ra))
}

// --- helpers for the deformable (BPL token-model) match ---
fn pointset_resid(p: &[[f64; 2]], q: &[[f64; 2]]) -> f64 {
    // symmetric Modified Hausdorff over 2-D point lists (the residual after a fit).
    if p.is_empty() || q.is_empty() {
        return f64::INFINITY;
    }
    let dir = |xs: &[[f64; 2]], ys: &[[f64; 2]]| -> f64 {
        let mut acc = 0.0;
        for &a in xs {
            let mut best = f64::INFINITY;
            for &b in ys {
                let d = (a[0] - b[0]).powi(2) + (a[1] - b[1]).powi(2);
                if d < best {
                    best = d;
                }
            }
            acc += best.sqrt();
        }
        acc / xs.len() as f64
    };
    dir(p, q).max(dir(q, p))
}

fn inv3(m: &[[f64; 3]; 3]) -> Option<[[f64; 3]; 3]> {
    let (a, b, c) = (m[0][0], m[0][1], m[0][2]);
    let (d, e, f) = (m[1][0], m[1][1], m[1][2]);
    let (g, h, i) = (m[2][0], m[2][1], m[2][2]);
    let det = a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g);
    if det.abs() < 1e-12 {
        return None;
    }
    let id = 1.0 / det;
    Some([
        [
            (e * i - f * h) * id,
            (c * h - b * i) * id,
            (b * f - c * e) * id,
        ],
        [
            (f * g - d * i) * id,
            (a * i - c * g) * id,
            (c * d - a * f) * id,
        ],
        [
            (d * h - e * g) * id,
            (b * g - a * h) * id,
            (a * e - b * d) * id,
        ],
    ])
}

fn mv3(m: &[[f64; 3]; 3], v: &[f64; 3]) -> [f64; 3] {
    [
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    ]
}

fn deform_dist(a: &Value, b: &Value) -> f64 {
    // BPL-style TOKEN-level deformation match. Fit the candidate's written form to the query with
    // a small AFFINE deformation (affine-ICP, 3 iterations: nearest-neighbour correspondences ->
    // least-squares affine -> repeat) and score the ORDER-INVARIANT residual (symmetric Modified
    // Hausdorff, pen order ignored) PLUS a penalty on how non-rigid (log-anisotropy / shear) the
    // fit had to be. Deformations are allowed but COST — exactly the generative token prior: the
    // true class fits with a near-rigid transform and small residual; a wrong class needs a large,
    // penalised deformation and still fits poorly. The affine absorbs anisotropic scale / shear /
    // residual rotation that the global RMS-normalise leaves. 2-D points (xy).
    fn pts(v: &Value) -> Vec<[f64; 2]> {
        v.iter()
            .map(|f| {
                let mut it = f.iter();
                let x = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                let y = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                [x, y]
            })
            .collect()
    }
    let p = pts(a);
    let q = pts(b);
    if p.is_empty() || q.is_empty() {
        return f64::INFINITY;
    }
    // Normal-equations matrix M = Σ r rᵀ over rows r=[px,py,1] (fixed across ICP iters), reg'd.
    let mut m = [[0.0f64; 3]; 3];
    for &[px, py] in &p {
        let r = [px, py, 1.0];
        for i in 0..3 {
            for j in 0..3 {
                m[i][j] += r[i] * r[j];
            }
        }
    }
    let lam = 1e-3 * p.len() as f64;
    for i in 0..3 {
        m[i][i] += lam;
    }
    let minv = match inv3(&m) {
        Some(x) => x,
        None => return pointset_resid(&p, &q),
    };
    let mut aa = [[1.0, 0.0], [0.0, 1.0]];
    let mut tt = [0.0, 0.0];
    let apply = |aa: &[[f64; 2]; 2], tt: &[f64; 2], pt: [f64; 2]| -> [f64; 2] {
        [
            aa[0][0] * pt[0] + aa[0][1] * pt[1] + tt[0],
            aa[1][0] * pt[0] + aa[1][1] * pt[1] + tt[1],
        ]
    };
    for _ in 0..3 {
        let mut rx = [0.0; 3];
        let mut ry = [0.0; 3];
        for &pp in &p {
            let tp = apply(&aa, &tt, pp);
            let mut best = f64::INFINITY;
            let mut bq = [0.0, 0.0];
            for &qq in &q {
                let d = (tp[0] - qq[0]).powi(2) + (tp[1] - qq[1]).powi(2);
                if d < best {
                    best = d;
                    bq = qq;
                }
            }
            let r = [pp[0], pp[1], 1.0];
            for i in 0..3 {
                rx[i] += r[i] * bq[0];
                ry[i] += r[i] * bq[1];
            }
        }
        let cx = mv3(&minv, &rx);
        let cy = mv3(&minv, &ry);
        aa = [[cx[0], cx[1]], [cy[0], cy[1]]];
        tt = [cx[2], cy[2]];
    }
    let tp: Vec<[f64; 2]> = p.iter().map(|&pp| apply(&aa, &tt, pp)).collect();
    let resid = pointset_resid(&tp, &q);
    // deformation penalty: log-anisotropy of A (0 for a similarity transform), from eigenvalues
    // of AᵀA (the squared singular values). A free affine over-helps wrong classes; the penalty
    // costs the non-rigid part of the fit. (Honest: on Omniglot one-shot a GLOBAL affine still
    // under-discriminates vs the holistic match — generative richness needs PART-level structure,
    // which the graph-nested part recogniser provides; see recognition_graph.predict_partnested_term.)
    let m11 = aa[0][0] * aa[0][0] + aa[1][0] * aa[1][0];
    let m22 = aa[0][1] * aa[0][1] + aa[1][1] * aa[1][1];
    let m12 = aa[0][0] * aa[0][1] + aa[1][0] * aa[1][1];
    let tr = m11 + m22;
    let det = m11 * m22 - m12 * m12;
    let disc = (tr * tr - 4.0 * det).max(0.0).sqrt();
    let e1 = ((tr + disc) / 2.0).max(1e-12);
    let e2 = ((tr - disc) / 2.0).max(1e-12);
    let aniso = 0.5 * (e1 / e2).ln(); // ln(σ1/σ2)
    resid + 0.5 * aniso.abs()
}

fn smooth_deform_dist(a: &Value, b: &Value) -> f64 {
    // The "distortable canvas" of Yu/Mineyev/Varshney/Evans 2022 (Learning from One and Only One
    // Shot): replace the GLOBAL affine of DeformDist with a SMOOTH NON-RIGID deformation FIELD whose
    // distortion COST is the similarity. A free-form deformation on a multi-level control grid
    // (coarse 2x2 then fine 4x4 = "abstracted multi-level"), each level a few ICP-style passes:
    // pull every point toward its nearest target, splat that pull onto the control grid (bilinear),
    // ridge-regularise the grid (-> a SMOOTH, small field), and apply the interpolated field. The
    // returned distance = residual-after-warp + BETA * mean squared displacement (how much smooth
    // distortion was needed). The smoothness + the cost are what discriminate: a true class warps a
    // little and smoothly; a wrong class needs a large rough warp it pays for. 2-D points (xy).
    fn pts(v: &Value) -> Vec<[f64; 2]> {
        v.iter()
            .map(|f| {
                let mut it = f.iter();
                let x = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                let y = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                [x, y]
            })
            .collect()
    }
    let p0 = pts(a);
    let q = pts(b);
    if p0.is_empty() || q.is_empty() {
        return f64::INFINITY;
    }
    let r = 2.6_f64; // control-grid half-extent (RMS-normalised points sit within ~+/-2.5)
    let n = p0.len();
    let mut warped = p0.clone();
    let mut acc = vec![[0.0f64; 2]; n]; // total displacement applied per point (the deformation)
    let nearest = |wp: [f64; 2], q: &[[f64; 2]]| -> [f64; 2] {
        let mut best = f64::INFINITY;
        let mut bq = [0.0, 0.0];
        for &qq in q {
            let d = (wp[0] - qq[0]).powi(2) + (wp[1] - qq[1]).powi(2);
            if d < best {
                best = d;
                bq = qq;
            }
        }
        bq
    };
    // bilinear cell (4 node indices + weights) for a point on a g x g grid spanning [-r, r].
    let cell = |x: f64, y: f64, g: usize| -> ([usize; 4], [f64; 4]) {
        let gx = ((x + r) / (2.0 * r) * (g as f64 - 1.0))
            .max(0.0)
            .min(g as f64 - 1.0);
        let gy = ((y + r) / (2.0 * r) * (g as f64 - 1.0))
            .max(0.0)
            .min(g as f64 - 1.0);
        let x0 = (gx.floor() as usize).min(g - 2);
        let y0 = (gy.floor() as usize).min(g - 2);
        let fx = gx - x0 as f64;
        let fy = gy - y0 as f64;
        let idx = [
            y0 * g + x0,
            y0 * g + x0 + 1,
            (y0 + 1) * g + x0,
            (y0 + 1) * g + x0 + 1,
        ];
        let w = [
            (1.0 - fx) * (1.0 - fy),
            fx * (1.0 - fy),
            (1.0 - fx) * fy,
            fx * fy,
        ];
        (idx, w)
    };
    let step = 0.7;
    // multi-level coarse-to-fine control grids (the paper's "abstracted multi-level"). A finer 6x6
    // level over-flexes (lets wrong classes warp too well) and HURT — measured; 2x2->4x4 is best.
    for &g in &[2usize, 4usize] {
        let nnode = g * g;
        let reg = (n as f64 / nnode as f64) * 0.6 + 1.0; // ridge -> smooth + needs support
        for _it in 0..5 {
            let mut sx = vec![0.0f64; nnode];
            let mut sy = vec![0.0f64; nnode];
            let mut sw = vec![0.0f64; nnode];
            for &wp in &warped {
                let bq = nearest(wp, &q);
                let (tx, ty) = (bq[0] - wp[0], bq[1] - wp[1]);
                let (idx, w) = cell(wp[0], wp[1], g);
                for k in 0..4 {
                    sx[idx[k]] += w[k] * tx;
                    sy[idx[k]] += w[k] * ty;
                    sw[idx[k]] += w[k];
                }
            }
            let ndx: Vec<f64> = (0..nnode).map(|k| sx[k] / (sw[k] + reg)).collect();
            let ndy: Vec<f64> = (0..nnode).map(|k| sy[k] / (sw[k] + reg)).collect();
            for i in 0..n {
                let (idx, w) = cell(warped[i][0], warped[i][1], g);
                let mut dx = 0.0;
                let mut dy = 0.0;
                for k in 0..4 {
                    dx += w[k] * ndx[idx[k]];
                    dy += w[k] * ndy[idx[k]];
                }
                warped[i][0] += step * dx;
                warped[i][1] += step * dy;
                acc[i][0] += step * dx;
                acc[i][1] += step * dy;
            }
        }
    }
    let residual = pointset_resid(&warped, &q);
    let mut dc = 0.0;
    for d in &acc {
        dc += d[0] * d[0] + d[1] * d[1];
    }
    dc /= n as f64;
    // distortion cost weight: leaning all-in on the cost (beta 3.0) HURT — the post-warp residual
    // carries real signal; 1.5 balances residual-fit against how-much-warp-was-needed. (measured.)
    residual + 1.5 * dc
}

fn mat_inverse(nn: usize, a: &[f64]) -> Option<Vec<f64>> {
    // general nn x nn inverse via Gauss-Jordan with partial pivoting (the TPS system L is symmetric
    // but INDEFINITE — bottom-right zero block — so Cholesky won't do; this handles it).
    let mut m = a.to_vec();
    let mut inv = vec![0.0f64; nn * nn];
    for i in 0..nn {
        inv[i * nn + i] = 1.0;
    }
    for col in 0..nn {
        let mut piv = col;
        let mut best = m[col * nn + col].abs();
        for r in (col + 1)..nn {
            let v = m[r * nn + col].abs();
            if v > best {
                best = v;
                piv = r;
            }
        }
        if best < 1e-12 {
            return None;
        }
        if piv != col {
            for k in 0..nn {
                m.swap(col * nn + k, piv * nn + k);
                inv.swap(col * nn + k, piv * nn + k);
            }
        }
        let d = m[col * nn + col];
        for k in 0..nn {
            m[col * nn + k] /= d;
            inv[col * nn + k] /= d;
        }
        for r in 0..nn {
            if r == col {
                continue;
            }
            let f = m[r * nn + col];
            if f != 0.0 {
                for k in 0..nn {
                    m[r * nn + k] -= f * m[col * nn + k];
                    inv[r * nn + k] -= f * inv[col * nn + k];
                }
            }
        }
    }
    Some(inv)
}

fn tps_deform_dist(a: &Value, b: &Value) -> f64 {
    // THIN-PLATE SPLINE deformation (Bookstein 1989 / Shape Contexts, Belongie-Malik-Puzicha 2002):
    // the principled smooth warp. Fit a regularised TPS mapping the candidate's points to their
    // nearest targets in the mark (ICP correspondences), warp, repeat; the distance = residual-after-
    // warp + BETA * BENDING ENERGY (w^T K w), the NON-AFFINE distortion. The affine part (incl.
    // rotation/scale/shear) is FREE — only genuine non-affine bending costs, so a true class warps
    // with little bending and a wrong class pays. Replaces SmoothDeformDist's FFD + magnitude cost
    // with the closed-form spline whose bending energy IS the cost. 2-D points (xy).
    fn pts(v: &Value) -> Vec<[f64; 2]> {
        v.iter()
            .map(|f| {
                let mut it = f.iter();
                let x = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                let y = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                [x, y]
            })
            .collect()
    }
    let p = pts(a);
    let q = pts(b);
    if p.len() < 4 || q.is_empty() {
        return pointset_resid(&p, &q);
    }
    let n = p.len();
    let sz = n + 3;
    let u = |r2: f64| -> f64 {
        if r2 <= 1e-12 {
            0.0
        } else {
            r2 * r2.ln()
        } // U(r) = r^2 log(r^2)
    };
    // kernel K (n x n) and the TPS system L (sz x sz) = [K+lambda*I, P_aug; P_aug^T, 0].
    let mut kmat = vec![0.0f64; n * n];
    for i in 0..n {
        for j in 0..n {
            let dx = p[i][0] - p[j][0];
            let dy = p[i][1] - p[j][1];
            kmat[i * n + j] = u(dx * dx + dy * dy);
        }
    }
    let lambda = 5.0; // stronger regularisation: don't interpolate noisy NN correspondences exactly
    let mut l = vec![0.0f64; sz * sz];
    for i in 0..n {
        for j in 0..n {
            l[i * sz + j] = kmat[i * n + j];
        }
        l[i * sz + i] += lambda;
        l[i * sz + n] = 1.0;
        l[i * sz + n + 1] = p[i][0];
        l[i * sz + n + 2] = p[i][1];
        l[n * sz + i] = 1.0;
        l[(n + 1) * sz + i] = p[i][0];
        l[(n + 2) * sz + i] = p[i][1];
    }
    let linv = match mat_inverse(sz, &l) {
        Some(x) => x,
        None => return pointset_resid(&p, &q),
    };
    let mut warped = p.clone();
    let mut wx = vec![0.0f64; n];
    let mut wy = vec![0.0f64; n];
    for _it in 0..5 {
        let mut vx = vec![0.0f64; sz];
        let mut vy = vec![0.0f64; sz];
        for i in 0..n {
            let mut best = f64::INFINITY;
            let mut bq = [0.0, 0.0];
            for &qq in &q {
                let d = (warped[i][0] - qq[0]).powi(2) + (warped[i][1] - qq[1]).powi(2);
                if d < best {
                    best = d;
                    bq = qq;
                }
            }
            vx[i] = bq[0];
            vy[i] = bq[1];
        }
        let mut cx = vec![0.0f64; sz];
        let mut cy = vec![0.0f64; sz];
        for r in 0..sz {
            let (mut sx, mut sy) = (0.0, 0.0);
            for c in 0..sz {
                sx += linv[r * sz + c] * vx[c];
                sy += linv[r * sz + c] * vy[c];
            }
            cx[r] = sx;
            cy[r] = sy;
        }
        for i in 0..n {
            wx[i] = cx[i];
            wy[i] = cy[i];
        }
        let (ax, ay) = ([cx[n], cx[n + 1], cx[n + 2]], [cy[n], cy[n + 1], cy[n + 2]]);
        for i in 0..n {
            let mut fx = ax[0] + ax[1] * p[i][0] + ax[2] * p[i][1];
            let mut fy = ay[0] + ay[1] * p[i][0] + ay[2] * p[i][1];
            for j in 0..n {
                fx += wx[j] * kmat[i * n + j];
                fy += wy[j] * kmat[i * n + j];
            }
            warped[i] = [fx, fy];
        }
    }
    let residual = pointset_resid(&warped, &q);
    // bending energy = w^T K w over both coordinate maps (the non-affine distortion).
    let mut bend = 0.0;
    for i in 0..n {
        let (mut kix, mut kiy) = (0.0, 0.0);
        for j in 0..n {
            kix += kmat[i * n + j] * wx[j];
            kiy += kmat[i * n + j] * wy[j];
        }
        bend += wx[i] * kix + wy[i] * kiy;
    }
    residual + 0.1 * bend.max(0.0)
}

fn shape_contexts(p: &[[f64; 2]], nr: usize, na: usize) -> Vec<Vec<f64>> {
    // the SHAPE CONTEXT of each point (Belongie-Malik-Puzicha 2002): a LOG-POLAR histogram of the
    // relative positions of all the OTHER points (nr log-spaced radial x na angular bins), distance-
    // normalised by the mean pairwise distance (scale invariant), L1-normalised. A globally
    // discriminative point descriptor.
    let n = p.len();
    let mut md = 0.0;
    let mut cnt = 0.0;
    for i in 0..n {
        for j in (i + 1)..n {
            md += ((p[i][0] - p[j][0]).powi(2) + (p[i][1] - p[j][1]).powi(2)).sqrt();
            cnt += 1.0;
        }
    }
    md = if cnt > 0.0 && md > 1e-9 {
        md / cnt
    } else {
        1.0
    };
    let (r_min, r_max) = (0.125_f64, 2.0_f64);
    let (lrmin, lrmax) = (r_min.ln(), r_max.ln());
    let two_pi = 2.0 * std::f64::consts::PI;
    let nb = nr * na;
    let mut hists = Vec::with_capacity(n);
    for i in 0..n {
        let mut h = vec![0.0f64; nb];
        let mut tot = 0.0;
        for j in 0..n {
            if i == j {
                continue;
            }
            let dx = p[j][0] - p[i][0];
            let dy = p[j][1] - p[i][1];
            let r = (dx * dx + dy * dy).sqrt() / md;
            let rb = if r <= r_min {
                0
            } else if r >= r_max {
                nr - 1
            } else {
                (((r.ln() - lrmin) / (lrmax - lrmin)) * nr as f64).floor() as usize
            }
            .min(nr - 1);
            let mut ang = dy.atan2(dx);
            if ang < 0.0 {
                ang += two_pi;
            }
            let ab = ((ang / two_pi) * na as f64).floor() as usize % na;
            h[rb * na + ab] += 1.0;
            tot += 1.0;
        }
        if tot > 0.0 {
            for v in h.iter_mut() {
                *v /= tot;
            }
        }
        hists.push(h);
    }
    hists
}

fn sc_chi2(a: &[f64], b: &[f64]) -> f64 {
    // chi-squared distance between two (L1-normalised) shape-context histograms.
    let mut s = 0.0;
    for k in 0..a.len() {
        let den = a[k] + b[k];
        if den > 1e-12 {
            s += (a[k] - b[k]).powi(2) / den;
        }
    }
    0.5 * s
}

fn shape_context_dist(a: &Value, b: &Value) -> f64 {
    // ORDER-INVARIANT shape-context distance: per-point log-polar shape contexts, matched by the
    // symmetric mean of nearest chi-squared cost both ways. The descriptor each point carries is the
    // distribution of the OTHERS, so the match is far more discriminative than raw position.
    fn pts(v: &Value) -> Vec<[f64; 2]> {
        v.iter()
            .map(|f| {
                let mut it = f.iter();
                let x = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                let y = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                [x, y]
            })
            .collect()
    }
    let p = pts(a);
    let q = pts(b);
    if p.len() < 2 || q.len() < 2 {
        return pointset_resid(&p, &q);
    }
    // coarser bins (4 radial x 8 angular) than the classic 5x12 — at ~64 points 60 bins is too
    // sparse for a stable chi-squared; 32 bins keeps the histograms populated.
    let (nr, na) = (4usize, 8usize);
    let hq = shape_contexts(&q, nr, na);
    let dir = |hx: &[Vec<f64>], hy: &[Vec<f64>]| -> f64 {
        let mut acc = 0.0;
        for hi in hx {
            let mut best = f64::INFINITY;
            for hj in hy {
                let c = sc_chi2(hi, hj);
                if c < best {
                    best = c;
                }
            }
            acc += best;
        }
        acc / hx.len() as f64
    };
    // the absolute-frame shape context is rotation-variant; Omniglot writers vary rotation. Search a
    // few global rotations of P and keep the best match (the rotation-fold that worked elsewhere).
    let mut best = f64::INFINITY;
    for &deg in &[-20.0f64, 0.0, 20.0] {
        let th = deg.to_radians();
        let (c, s) = (th.cos(), th.sin());
        let pr: Vec<[f64; 2]> = p
            .iter()
            .map(|&[x, y]| [c * x - s * y, s * x + c * y])
            .collect();
        let hp = shape_contexts(&pr, nr, na);
        let d = 0.5 * (dir(&hp, &hq) + dir(&hq, &hp));
        if d < best {
            best = d;
        }
    }
    best
}

fn tps_bending(src: &[[f64; 2]], tgt: &[[f64; 2]]) -> f64 {
    // fit a regularised TPS mapping src -> tgt and return its BENDING ENERGY (w^T K w over both
    // coordinate maps) — the non-affine distortion. A single closed-form solve (no ICP; the
    // correspondences are given). Returns 0 on a degenerate system.
    let n = src.len();
    if n < 4 || tgt.len() != n {
        return 0.0;
    }
    let sz = n + 3;
    let uk = |r2: f64| -> f64 {
        if r2 <= 1e-12 {
            0.0
        } else {
            r2 * r2.ln()
        }
    };
    let mut kmat = vec![0.0f64; n * n];
    for i in 0..n {
        for j in 0..n {
            let dx = src[i][0] - src[j][0];
            let dy = src[i][1] - src[j][1];
            kmat[i * n + j] = uk(dx * dx + dy * dy);
        }
    }
    let lambda = 5.0;
    let mut l = vec![0.0f64; sz * sz];
    for i in 0..n {
        for j in 0..n {
            l[i * sz + j] = kmat[i * n + j];
        }
        l[i * sz + i] += lambda;
        l[i * sz + n] = 1.0;
        l[i * sz + n + 1] = src[i][0];
        l[i * sz + n + 2] = src[i][1];
        l[n * sz + i] = 1.0;
        l[(n + 1) * sz + i] = src[i][0];
        l[(n + 2) * sz + i] = src[i][1];
    }
    let linv = match mat_inverse(sz, &l) {
        Some(x) => x,
        None => return 0.0,
    };
    let (mut wx, mut wy) = (vec![0.0f64; n], vec![0.0f64; n]);
    for r in 0..n {
        let (mut sx, mut sy) = (0.0, 0.0);
        for c in 0..n {
            sx += linv[r * sz + c] * tgt[c][0];
            sy += linv[r * sz + c] * tgt[c][1];
        }
        wx[r] = sx;
        wy[r] = sy;
    }
    let mut bend = 0.0;
    for i in 0..n {
        let (mut kix, mut kiy) = (0.0, 0.0);
        for j in 0..n {
            kix += kmat[i * n + j] * wx[j];
            kiy += kmat[i * n + j] * wy[j];
        }
        bend += wx[i] * kix + wy[i] * kiy;
    }
    bend.max(0.0)
}

fn sc_tps_dist(a: &Value, b: &Value) -> f64 {
    // THE FULL SHAPE-CONTEXTS DISTANCE: use the shape-context descriptor to establish CORRESPONDENCES
    // (chi-squared matching, not nearest-neighbour), then fit a TPS to THOSE and return the
    // shape-context matching cost + BENDING ENERGY. This is what TpsDeformDist was starving for — the
    // descriptor supplies the good correspondences the spline needs. A small rotation search (cheap,
    // on the SC cost) picks the orientation, then one TPS solve.
    fn pts(v: &Value) -> Vec<[f64; 2]> {
        v.iter()
            .map(|f| {
                let mut it = f.iter();
                let x = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                let y = it.next().map(|x| x.as_f64()).unwrap_or(0.0);
                [x, y]
            })
            .collect()
    }
    let p = pts(a);
    let q = pts(b);
    if p.len() < 4 || q.len() < 2 {
        return pointset_resid(&p, &q);
    }
    let n = p.len();
    let (nr, na) = (4usize, 8usize);
    let hq = shape_contexts(&q, nr, na);
    let mut best_sc = f64::INFINITY;
    let mut best_pr: Vec<[f64; 2]> = p.clone();
    let mut best_tgt: Vec<[f64; 2]> = vec![[0.0; 2]; n];
    for &deg in &[-20.0f64, 0.0, 20.0] {
        let th = deg.to_radians();
        let (c, s) = (th.cos(), th.sin());
        let pr: Vec<[f64; 2]> = p
            .iter()
            .map(|&[x, y]| [c * x - s * y, s * x + c * y])
            .collect();
        let hp = shape_contexts(&pr, nr, na);
        let mut tgt = vec![[0.0f64; 2]; n];
        let mut sc = 0.0;
        for i in 0..n {
            let mut bc = f64::INFINITY;
            let mut bj = 0;
            for j in 0..q.len() {
                let cc = sc_chi2(&hp[i], &hq[j]);
                if cc < bc {
                    bc = cc;
                    bj = j;
                }
            }
            tgt[i] = q[bj];
            sc += bc;
        }
        sc /= n as f64;
        if sc < best_sc {
            best_sc = sc;
            best_pr = pr;
            best_tgt = tgt;
        }
    }
    let bend = tps_bending(&best_pr, &best_tgt);
    best_sc + 0.04 * bend
}

fn xcorr_peak(a: &Value, b: &Value, band: usize) -> f64 {
    // Materialise each side as rows of f64 (frames x bands),
    // exactly like banded_dtw's `rows`.
    fn rows(v: &Value) -> Vec<Vec<f64>> {
        v.iter()
            .map(|frame| frame.iter().map(|x| x.as_f64()).collect::<Vec<f64>>())
            .collect()
    }
    let ra = rows(a);
    let rb = rows(b);
    let na = ra.len() as isize;
    let nb = rb.len() as isize;
    if na == 0 || nb == 0 {
        return 0.0;
    }
    // Per-frame correlation: dot of the two band vectors.
    let fdot = |fa: &Vec<f64>, fb: &Vec<f64>| -> f64 {
        let n = fa.len().min(fb.len());
        let mut s = 0.0;
        for k in 0..n {
            s += fa[k] * fb[k];
        }
        s
    };
    let fnorm2 = |fa: &Vec<f64>| -> f64 { fa.iter().map(|x| x * x).sum::<f64>() };
    let mut best = f64::NEG_INFINITY;
    let bl = band as isize;
    // Sweep integer lags L of b relative to a over [-band, band];
    // frame i of a pairs with frame i - L of b (overlap only).
    for lag in -bl..=bl {
        let mut dot = 0.0;
        let mut na2 = 0.0;
        let mut nb2 = 0.0;
        for i in 0..na {
            let j = i - lag;
            if j < 0 || j >= nb {
                continue;
            }
            let fa = &ra[i as usize];
            let fb = &rb[j as usize];
            dot += fdot(fa, fb);
            na2 += fnorm2(fa);
            nb2 += fnorm2(fb);
        }
        if na2 <= 0.0 || nb2 <= 0.0 {
            continue;
        }
        let ncc = dot / (na2.sqrt() * nb2.sqrt());
        if ncc > best {
            best = ncc;
        }
    }
    if best.is_finite() {
        best
    } else {
        0.0
    }
}

/// Is this value subtree safe to RE-EVALUATE for the selector audit?
///
/// The audit re-runs a selector's own `value` Term on the winner it returned.
/// That is only admissible if the Term is replayable — re-running an EFFECTFUL
/// Term would fire its side effect twice, which is a behaviour change, which
/// VISION_PROTOCOL §9 forbids in an instrumentation rung.
///
/// Two variants are effectful / re-entrant:
///
/// - `UseTool` — dispatches to a registered Python handler under the GIL, and is
///   re-entrant back into the substrate.
/// - `ReadFile` — host I/O.
///
/// Everything else in the evaluator is pure with respect to the graph:
/// `EvalCtx::graph` is a `&TypedGraph` (shared, immutable), so no other Term can
/// mutate anything a replay would observe.
///
/// SOUNDNESS OF THE WALK: this recurses via `children()`, whose `match` is
/// EXHAUSTIVE over `TermNode` with no catch-all arm — the compiler therefore
/// enforces that a newly added variant cannot silently hide a nested `UseTool`
/// from this scan. That is the difference between this walk and
/// `collect_term_reads`, whose generic catch-all is the documented
/// under-approximation in `rewrite.rs`.
fn value_term_is_replayable(arena: &TermArena, idx: TermIdx) -> bool {
    match arena.get(idx) {
        TermNode::UseTool { .. } | TermNode::ReadFile { .. } => return false,
        _ => {}
    }
    for child in children(arena.get(idx)) {
        if !value_term_is_replayable(arena, child) {
            return false;
        }
    }
    true
}

/// THE SELECTOR AUDIT CHECK — see `selector_audit.rs` for why it exists.
///
/// Re-binds `var_name` to the element the fold RETURNED, re-evaluates the
/// selector's OWN `value` Term on it, and compares to the extremum the fold
/// RECORDED. The two numbers are produced by different things, so a mismatch is
/// a single-row contradiction requiring no replay and no statistics.
fn audit_binder_selector(
    arena: &TermArena,
    selector: &str,
    var_name: Sym,
    value: TermIdx,
    winner_elem: &Value,
    recorded: &Value,
    n_candidates: usize,
    env: &mut Env,
    ctx: &mut EvalCtx,
) {
    if !value_term_is_replayable(arena, value) {
        selector_audit::note_skipped_effectful();
        return;
    }
    env.push((var_name, winner_elem.clone()));
    let winner_value = evaluate(arena, value, env, ctx);
    env.pop();
    selector_audit::note_firing();
    if cmp_value(&winner_value, recorded) != std::cmp::Ordering::Equal {
        selector_audit::note_disagreement(
            selector,
            &format!("{winner_elem:?}"),
            &format!("{winner_value:?}"),
            &format!("{recorded:?}"),
            n_candidates,
        );
    }
}

fn min_or_max_over(
    arena: &TermArena,
    source: TermIdx,
    var_name: Sym,
    value: TermIdx,
    default: Option<TermIdx>,
    env: &mut Env,
    ctx: &mut EvalCtx,
    want_min: bool,
) -> Value {
    // AUDIT (default OFF): one relaxed atomic load. When off, nothing below
    // changes — no element is cloned and no Term is re-evaluated.
    let auditing = selector_audit::enabled();
    let s = evaluate(arena, source, env, ctx);
    let snap = s.snapshot();
    let mut best: Option<Value> = None;
    // Tracked ONLY while auditing: `MinOver`/`MaxOver` return the winning VALUE,
    // so the winning ELEMENT — the thing the audit must re-evaluate on — is not
    // otherwise retained.
    let mut best_elem: Option<Value> = None;
    let mut first_value: Option<Value> = None;
    let mut n_candidates: usize = 0;
    for it_ref in snap.iter() {
        env.push((var_name, it_ref.clone()));
        let v = evaluate(arena, value, env, ctx);
        env.pop();
        if auditing {
            n_candidates += 1;
            if first_value.is_none() {
                first_value = Some(v.clone());
            }
        }
        // REPORTED-ORDER site (`MinOver`/`MaxOver`) — see `numeric_argmin`.
        let take_new = match &best {
            None => true,
            Some(cur) => match crate::value::cmp_value_lex(&v, cur, ctx.interner) {
                std::cmp::Ordering::Less => want_min,
                std::cmp::Ordering::Greater => !want_min,
                _ => false,
            },
        };
        if take_new {
            if auditing {
                best_elem = Some(it_ref.clone());
            }
            best = Some(v);
        }
    }
    if auditing {
        selector_audit::note_candidates(n_candidates as u64);
        if let (Some(recorded), Some(elem)) = (best.clone(), best_elem.clone()) {
            // POSITIVE CONTROL (unreachable when the audit is off): corrupt the
            // fold's OUTPUT while leaving the winning element intact, so the
            // returned extremum no longer belongs to the winner. This is the
            // `MaxOver` analogue of the §4.2 signature.
            let returned = if selector_audit::fault_inject_first() {
                first_value.clone().unwrap_or(recorded.clone())
            } else {
                recorded.clone()
            };
            let selector = if want_min { "MinOver" } else { "MaxOver" };
            audit_binder_selector(
                arena,
                selector,
                var_name,
                value,
                &elem,
                &returned,
                n_candidates,
                env,
                ctx,
            );
            return returned;
        }
        selector_audit::note_empty();
    }
    match best {
        Some(v) => v,
        None => default
            .map(|d| evaluate(arena, d, env, ctx))
            .unwrap_or(Value::Int(0)),
    }
}

/// Unsigned Exp-Golomb decode helper (ITU-T H.264 §9.1).
/// Count leading zeros M; read 1-bit marker; read M-bit suffix;
/// value = 2^M - 1 + suffix. Universal across H.264 / HEVC / VVC.
fn exp_golomb_decode(bytes: &[u8], bp: u64) -> Option<(u64, u64)> {
    let total_bits = (bytes.len() as u64) * 8;
    let mut leading_zeros = 0u32;
    let mut p = bp;
    // Count leading zeros until 1-bit marker.
    loop {
        if p >= total_bits {
            return None;
        }
        let byte = bytes[(p >> 3) as usize];
        let bit = (byte >> (7 - (p & 7))) & 1;
        p += 1;
        if bit == 1 {
            break;
        }
        leading_zeros += 1;
        if leading_zeros > 32 {
            return None;
        } // sanity cap
    }
    // Read `leading_zeros` more bits as suffix.
    if p + (leading_zeros as u64) > total_bits {
        return None;
    }
    let mut suffix: u64 = 0;
    for _ in 0..leading_zeros {
        let byte = bytes[(p >> 3) as usize];
        let bit = (byte >> (7 - (p & 7))) & 1;
        suffix = (suffix << 1) | (bit as u64);
        p += 1;
    }
    let value = (1u64 << leading_zeros) - 1 + suffix;
    Some((value, p))
}

/// Unsigned Exp-Golomb encode. Writes ue(v) of `value` into `out` at
/// `bp`, extending if needed. Returns the new bitpos.
fn exp_golomb_encode(out: &mut Vec<u8>, bp: u64, value: u64) -> u64 {
    // Find M such that 2^M <= value+1 < 2^(M+1).
    let code_num = value + 1;
    let m = (63u32 - code_num.leading_zeros());
    // Total bits: M leading zeros + 1 marker + M suffix bits = 2M+1.
    let total = 2 * m + 1;
    let mut p = bp;
    // Helper inline.
    let write_bit = |out: &mut Vec<u8>, p: &mut u64, bit: u8| {
        let byte_idx = (*p >> 3) as usize;
        let bit_idx = 7 - (*p & 7);
        if byte_idx >= out.len() {
            out.resize(byte_idx + 1, 0);
        }
        let mask = 1u8 << bit_idx;
        if bit == 1 {
            out[byte_idx] |= mask;
        } else {
            out[byte_idx] &= !mask;
        }
        *p += 1;
    };
    // M leading zeros.
    for _ in 0..m {
        write_bit(out, &mut p, 0);
    }
    // Write code_num MSB-first in (M+1) bits — the marker is the
    // MSB which is 1 (since code_num >= 2^M).
    for i in 0..(m + 1) {
        let bit = ((code_num >> (m - i)) & 1) as u8;
        write_bit(out, &mut p, bit);
    }
    debug_assert_eq!(p - bp, total as u64);
    p
}

fn argmin_or_argmax_over(
    arena: &TermArena,
    source: TermIdx,
    var_name: Sym,
    value: TermIdx,
    default: Option<TermIdx>,
    env: &mut Env,
    ctx: &mut EvalCtx,
    want_min: bool,
    require_unique: bool,
    // `ArgminRefusal` supplies a DISTINCT token evaluated ONLY on the tie
    // (non-unique-extremum) path — never on the empty-source path. This is the
    // separation the shared `default` cannot make (`default` is returned on
    // BOTH). Existing callers pass `None` and are byte-identical: the tie path
    // then falls back to `default`, exactly as `ArgminUnique` did.
    refused_on_tie: Option<TermIdx>,
) -> Value {
    // Same shape as min_or_max_over, but track the ELEMENT not the
    // value. Tiebreaker: first encountered. When `source` is empty,
    // returns `default` (or Value::None if no default).
    //
    // AUDIT (default OFF): one relaxed atomic load. This is the exact selector
    // class that produced the 272 irreproducible rows of
    // ENGINE_ARGMAX_DETERMINISM_RESULTS.md — a returned winner whose own value
    // disagreed with the extremum the same fold recorded.
    let auditing = selector_audit::enabled();
    // TIE AUDIT (default OFF, one relaxed atomic load): `require_unique` is the
    // `ArgminUnique` Term asking for the refusal on its own behalf; the
    // instrument can additionally COERCE an ordinary Argmin/Argmax into the
    // same behaviour so the whole tree's exposure is measurable at once.
    // `tie_tracking` is true whenever the tie count is NEEDED — either to
    // decide, or merely to count.
    let tie_audit = argmin_tie::enabled();
    let refuse_on_tie = require_unique || argmin_tie::coerces_refusal(want_min);
    let tie_tracking = tie_audit || require_unique;
    let s = evaluate(arena, source, env, ctx);
    let snap = s.snapshot();
    let mut best: Option<(Value, Value)> = None; // (value, element)
    let mut first_elem: Option<Value> = None;
    let mut n_candidates: usize = 0;
    // Candidates tied AT THE CURRENT EXTREMUM. Reset to 1 on a strict
    // improvement, incremented on EXACT equality (`cmp_value == Equal`).
    // §13: exact equality, no epsilon, nowhere to put one.
    let mut n_at_best: usize = 0;
    for it_ref in snap.iter() {
        let it = it_ref.clone();
        env.push((var_name, it.clone()));
        let v = evaluate(arena, value, env, ctx);
        env.pop();
        if auditing {
            n_candidates += 1;
            if first_elem.is_none() {
                first_elem = Some(it.clone());
            }
        }
        // REPORTED-ORDER site (`ArgminOver`/`ArgmaxOver`/`ArgminUnique`) —
        // the tie count decides refusal and the `best` match decides the
        // returned ELEMENT; both are string-order-sensitive — see
        // `numeric_argmin`.
        if tie_tracking {
            match &best {
                None => n_at_best = 1,
                Some((cur_v, _)) => match crate::value::cmp_value_lex(&v, cur_v, ctx.interner) {
                    std::cmp::Ordering::Equal => n_at_best += 1,
                    std::cmp::Ordering::Less => {
                        if want_min {
                            n_at_best = 1;
                        }
                    }
                    std::cmp::Ordering::Greater => {
                        if !want_min {
                            n_at_best = 1;
                        }
                    }
                },
            }
        }
        best = Some(match best {
            None => (v, it),
            Some((cur_v, cur_e)) => {
                let take_new = match crate::value::cmp_value_lex(&v, &cur_v, ctx.interner) {
                    std::cmp::Ordering::Less => want_min,
                    std::cmp::Ordering::Greater => !want_min,
                    _ => false,
                };
                if take_new {
                    (v, it)
                } else {
                    (cur_v, cur_e)
                }
            }
        });
    }
    // THE TIE VERDICT, taken BEFORE the selector audit's fault-injection path
    // so the two instruments never interpret each other's output.
    //
    // The three counters below are separated ON PURPOSE. `Argmin` could ALREADY
    // return `Value::None` on an empty source, and a tie-refusal returns
    // `Value::None` too — DOWNSTREAM THEY ARE THE SAME BYTES. A dead reader and
    // a perfect refuser produce byte-identical output (the refusal-capacity
    // rung's §0), so "refused" and "produced nothing" must be distinguishable
    // AT THE INSTRUMENT or no number below means anything.
    if tie_audit {
        argmin_tie::note_firing();
        let is_tie = best.is_some() && n_at_best > 1;
        if best.is_none() {
            argmin_tie::note_empty();
        } else if is_tie {
            argmin_tie::note_tie();
        }
        // PER-SITE ATTRIBUTION, on the TIE path only. Rendering the value Term
        // identifies the exact seed rule that authored this selector; doing it
        // on every firing would be a real cost, and doing it on none would
        // leave the census unable to say WHERE (§12.1).
        if is_tie {
            let key = crate::jsonio::term_to_json(arena, value, ctx.interner).to_string();
            argmin_tie::note_site(if want_min { "Argmin" } else { "Argmax" }, &key, true);
        }
    }
    if require_unique {
        argmin_tie::note_unique_term_firing();
    }
    if refuse_on_tie && best.is_some() && n_at_best > 1 {
        if tie_audit {
            argmin_tie::note_refusal();
        }
        // A TIE = the uniqueness comparison matched nothing. `ArgminRefusal`
        // routes this to its DISTINCT token; every other caller (`refused_on_tie
        // == None`) falls back to `default`, byte-identical to `ArgminUnique`.
        // The empty-source path below NEVER reaches here, so a tie and an empty
        // source return DIFFERENT values under `ArgminRefusal`.
        if let Some(r) = refused_on_tie {
            return evaluate(arena, r, env, ctx);
        }
        return default
            .map(|d| evaluate(arena, d, env, ctx))
            .unwrap_or(Value::None);
    }
    if auditing {
        selector_audit::note_candidates(n_candidates as u64);
        if let Some((recorded, elem)) = best.clone() {
            // POSITIVE CONTROL (unreachable when the audit is off): return the
            // FIRST element encountered regardless of its value, leaving the
            // recorded extremum correct. That is EXACTLY the §4.2 signature —
            // a constant winner (`fractal`, the lowest-id candidate and so the
            // first the sorted source yields) alongside a correct extremum.
            let returned = if selector_audit::fault_inject_first() {
                first_elem.clone().unwrap_or(elem)
            } else {
                elem
            };
            let selector = if want_min { "Argmin" } else { "Argmax" };
            audit_binder_selector(
                arena,
                selector,
                var_name,
                value,
                &returned,
                &recorded,
                n_candidates,
                env,
                ctx,
            );
            return returned;
        }
        selector_audit::note_empty();
    }
    match best {
        Some((_, e)) => e,
        None => default
            .map(|d| evaluate(arena, d, env, ctx))
            .unwrap_or(Value::None),
    }
}

fn vec_binary(
    arena: &TermArena,
    a: TermIdx,
    b: TermIdx,
    env: &mut Env,
    ctx: &mut EvalCtx,
    op: impl Fn(f64, f64) -> f64,
) -> Value {
    let av = evaluate(arena, a, env, ctx);
    let bv = evaluate(arena, b, env, ctx);
    let mut out: SmallVec<[Value; 4]> = SmallVec::new();
    let mut bi = bv.iter();
    for x in av.iter() {
        let y = bi.next();
        match (x, y) {
            (Value::Int(xi), Some(Value::Int(yi))) => {
                let f = op(*xi as f64, *yi as f64);
                if f.fract() == 0.0 && f.is_finite() {
                    out.push(Value::Int(f as i64));
                } else {
                    out.push(Value::Float(f));
                }
            }
            (xv, Some(yv)) => out.push(Value::Float(op(xv.as_f64(), yv.as_f64()))),
            _ => {}
        }
    }
    Value::Tuple(Arc::new(out))
}

fn cat_or_lines(
    arena: &TermArena,
    items: &[TermIdx],
    env: &mut Env,
    ctx: &mut EvalCtx,
    sep: &[u8],
) -> Value {
    let mut parts: Vec<Vec<u8>> = Vec::new();
    let mut any_bytes = false;
    for c in items {
        let v = evaluate(arena, *c, env, ctx);
        match v {
            Value::None => return Value::None,
            Value::Surface(kind, b) => {
                if kind == SurfaceKind::Bytes {
                    any_bytes = true;
                }
                parts.push(b.to_vec());
            }
            Value::Str(s) => parts.push(ctx.interner.resolve(s).as_bytes().to_vec()),
            Value::Int(n) => parts.push(n.to_string().into_bytes()),
            Value::Float(f) => parts.push(f.to_string().into_bytes()),
            other => parts.push(format!("{:?}", other).into_bytes()),
        }
    }
    let mut out: Vec<u8> = Vec::new();
    for (i, p) in parts.iter().enumerate() {
        if i > 0 {
            out.extend_from_slice(sep);
        }
        out.extend_from_slice(p);
    }
    let kind = if any_bytes {
        SurfaceKind::Bytes
    } else {
        SurfaceKind::Text
    };
    Value::Surface(kind, Arc::from(out))
}

// --- Reflection helpers: free_vars / collect_vars ---

/// Free variables of a Term subtree — Var names not shadowed by an
/// enclosing binder (Filter/Exists/Sum/Prod/MinOver/MaxOver/Let).
/// Mirrors `dsl.free_vars`. `excluded` is the binder var the caller
/// wants to skip (used by `Filter` cache to key by external bindings).
pub fn free_vars(arena: &TermArena, idx: TermIdx, excluded: Option<Sym>) -> SmallVec<[Sym; 8]> {
    let mut out: SmallVec<[Sym; 8]> = SmallVec::new();
    collect_into(arena, idx, &mut out, excluded);
    out.sort();
    out.dedup();
    out
}

fn collect_into(
    arena: &TermArena,
    idx: TermIdx,
    out: &mut SmallVec<[Sym; 8]>,
    excluded: Option<Sym>,
) {
    match arena.get(idx) {
        TermNode::Var { name } => {
            if excluded != Some(*name) {
                out.push(*name);
            }
        }
        TermNode::Filter {
            source,
            var_name,
            predicate,
        }
        | TermNode::FilterList {
            source,
            var_name,
            predicate,
        }
        | TermNode::Exists {
            source,
            var_name,
            predicate,
        } => {
            collect_into(arena, *source, out, excluded);
            // Inside the predicate, var_name is shadowed.
            collect_into(arena, *predicate, out, Some(*var_name));
        }
        TermNode::Sum {
            source,
            var_name,
            value,
        }
        | TermNode::Prod {
            source,
            var_name,
            value,
        }
        | TermNode::MapList {
            source,
            var_name,
            value,
        }
        | TermNode::MapSet {
            source,
            var_name,
            value,
        } => {
            collect_into(arena, *source, out, excluded);
            collect_into(arena, *value, out, Some(*var_name));
        }
        TermNode::SortBy {
            source,
            var_name,
            key,
        } => {
            collect_into(arena, *source, out, excluded);
            collect_into(arena, *key, out, Some(*var_name));
        }
        TermNode::MinOver {
            source,
            var_name,
            value,
            default,
        }
        | TermNode::MaxOver {
            source,
            var_name,
            value,
            default,
        } => {
            collect_into(arena, *source, out, excluded);
            collect_into(arena, *value, out, Some(*var_name));
            if let Some(d) = default {
                collect_into(arena, *d, out, excluded);
            }
        }
        TermNode::Fold {
            source,
            var_name,
            acc_name,
            init,
            body,
        } => {
            // Fold has two binders (var_name, acc_name) — both shadow
            // inside body. init evaluates in the outer scope.
            collect_into(arena, *source, out, excluded);
            collect_into(arena, *init, out, excluded);
            // We can only exclude one name at a time via this helper;
            // call once with each binder by walking body twice would
            // double-count. Instead inline a two-name filter.
            let mut local: SmallVec<[Sym; 8]> = SmallVec::new();
            let mut sub_excluded: Option<Sym> = None;
            // Approximation: exclude the most-recent-binder semantics by
            // collecting then removing both names. Cheap and correct for
            // the free-var set (idempotent on names).
            collect_into(arena, *body, &mut local, sub_excluded);
            let _ = &mut sub_excluded; // suppress unused warning
            for s in local {
                if s != *var_name && s != *acc_name && Some(s) != excluded {
                    out.push(s);
                }
            }
        }
        TermNode::Let { name, value, body } => {
            if let Some(v) = value {
                collect_into(arena, *v, out, excluded);
            }
            if let Some(b) = body {
                collect_into(arena, *b, out, Some(*name));
            }
        }
        _ => {
            for child in children(arena.get(idx)) {
                collect_into(arena, child, out, excluded);
            }
        }
    }
}

/// Yield all child TermIdx referenced by a node — used by `free_vars`
/// for generic recursion across non-binder Terms.
pub(crate) fn children(node: &TermNode) -> SmallVec<[TermIdx; 8]> {
    let mut out: SmallVec<[TermIdx; 8]> = SmallVec::new();
    match node {
        TermNode::Var { .. }
        | TermNode::Lit { .. }
        | TermNode::Slot { .. }
        | TermNode::Label { .. }
        | TermNode::Surface { .. }
        | TermNode::NodesOfType { .. }
        | TermNode::ScalarAttrTriples { .. } => {}
        TermNode::TypeOf { node } | TermNode::Attr { node, .. } => out.push(*node),
        TermNode::SetT { items }
        | TermNode::And { items }
        | TermNode::Or { items }
        | TermNode::Plus { items }
        | TermNode::Times { items }
        | TermNode::Min { items }
        | TermNode::Max { items }
        | TermNode::ArgMax { items }
        | TermNode::ArgMin { items }
        | TermNode::Vec_ { items }
        | TermNode::Cat { items }
        | TermNode::Bytes { items }
        | TermNode::Lines { items } => out.extend(items.iter().copied()),
        TermNode::UseTool { args, .. } => out.extend(args.iter().copied()),
        TermNode::In { member, container } => {
            out.push(*member);
            out.push(*container);
        }
        TermNode::ApcEncode {
            model,
            seq,
            start,
            end,
            out_len,
        } => {
            out.push(*model);
            out.push(*seq);
            out.push(*start);
            out.push(*end);
            out.push(*out_len);
        }
        TermNode::Eq { a, b }
        | TermNode::Lt { a, b }
        | TermNode::Lte { a, b }
        | TermNode::Gt { a, b }
        | TermNode::Gte { a, b }
        | TermNode::Minus { a, b }
        | TermNode::Div { a, b }
        | TermNode::Mod { a, b }
        | TermNode::DtwTo { a, b }
        | TermNode::PointSetDist { a, b }
        | TermNode::MahalLeaf { a, b }
        | TermNode::MahalFull { a, b }
        | TermNode::DeformGenMarginal { a, b }
        | TermNode::DeformGen { a, b }
        | TermNode::DeformDist { a, b }
        | TermNode::SmoothDeformDist { a, b }
        | TermNode::TpsDeformDist { a, b }
        | TermNode::SmoothDeformComponents { a, b }
        | TermNode::ShapeContextDist { a, b }
        | TermNode::ScTpsDist { a, b }
        | TermNode::XCorrPeak { a, b }
        | TermNode::Whiten { a, b }
        | TermNode::WhitenMany { a, b }
        | TermNode::WithinScatter { a, b }
        | TermNode::BetweenScatter { a, b }
        | TermNode::Pow { a, b }
        | TermNode::VecAdd { a, b }
        | TermNode::VecSub { a, b }
        | TermNode::Dot { a, b }
        | TermNode::AngleBetween { a, b }
        | TermNode::BitAnd { a, b }
        | TermNode::BitOr { a, b }
        | TermNode::BitXor { a, b }
        | TermNode::Shl { a, b }
        | TermNode::Lshr { a, b }
        | TermNode::Ashr { a, b }
        | TermNode::IDiv { a, b }
        | TermNode::IRem { a, b } => {
            out.push(*a);
            out.push(*b);
        }
        TermNode::EnigmaCrib { candidate } => out.push(*candidate),
        TermNode::EnigmaBombe { candidate } => out.push(*candidate),
        TermNode::EnigmaBombeWitness { candidate } => out.push(*candidate),
        TermNode::Atan2 { y, x } => {
            out.push(*y);
            out.push(*x);
        }
        TermNode::Rotate { vec, angle } => {
            out.push(*vec);
            out.push(*angle);
        }
        TermNode::Neighbours { node, .. } | TermNode::InNeighbours { node, .. } => out.push(*node),
        TermNode::ReachableFrom { node, .. } => out.push(*node),

        TermNode::SlideNeighbours {
            cell,
            slide,
            ground,
        } => {
            out.push(*cell);
            out.push(*slide);
            out.push(*ground);
        }
        TermNode::MapNeighbours { source, .. } => out.push(*source),
        TermNode::Count { source }
        | TermNode::Pick { source }
        | TermNode::PickUnique { source } => out.push(*source),
        TermNode::Tokenize { text } => out.push(*text),
        TermNode::MorphHead { text } => out.push(*text),
        TermNode::MorphTail { text } => out.push(*text),
        TermNode::FinalToken { text } => out.push(*text),
        TermNode::Tokenize2 { text } => out.push(*text),
        TermNode::ReadFile { path } => out.push(*path),
        TermNode::StringIndexOf { haystack, needle } => {
            out.push(*haystack);
            out.push(*needle);
        }
        TermNode::StringSlice { s, start, end } => {
            out.push(*s);
            out.push(*start);
            out.push(*end);
        }
        TermNode::BlendCover { unknown, a, b } => {
            out.push(*unknown);
            out.push(*a);
            out.push(*b);
        }
        TermNode::StringConcat { parts } => out.extend(parts.iter().copied()),
        TermNode::Verify {
            term,
            env,
            expected,
        } => {
            out.push(*term);
            out.push(*env);
            out.push(*expected);
        }
        TermNode::MkDict { items } => out.extend(items.iter().copied()),
        TermNode::ToJsonString { value } => out.push(*value),
        TermNode::FromJsonString { text } => out.push(*text),
        TermNode::ShiftThresholdLits { tree, shift } => {
            out.push(*tree);
            out.push(*shift);
        }
        TermNode::DictGet { dict, key } => {
            out.push(*dict);
            out.push(*key);
        }
        TermNode::RewriteTreeNodes {
            tree,
            type_filter,
            field,
            value_map,
        } => {
            out.push(*tree);
            if let Some(t) = type_filter {
                out.push(*t);
            }
            out.push(*field);
            out.push(*value_map);
        }
        TermNode::AttrKeyRanking { tree } => out.push(*tree),
        TermNode::TextShape { text } => out.push(*text),
        TermNode::FbFrameSeq { fb } => out.push(*fb),
        TermNode::ChangeDetect {
            image_vals,
            kernel_weights,
            dims,
        } => {
            out.push(*image_vals);
            out.push(*kernel_weights);
            out.push(*dims);
        }
        TermNode::TemporalDiff { a_vals, b_vals } => {
            out.push(*a_vals);
            out.push(*b_vals);
        }
        TermNode::Foveate {
            image_vals,
            dims,
            geometry,
        } => {
            out.push(*image_vals);
            out.push(*dims);
            out.push(*geometry);
        }
        TermNode::Filter {
            source, predicate, ..
        }
        | TermNode::FilterList {
            source, predicate, ..
        }
        | TermNode::Exists {
            source, predicate, ..
        } => {
            out.push(*source);
            out.push(*predicate);
        }
        TermNode::Sum { source, value, .. } | TermNode::Prod { source, value, .. } => {
            out.push(*source);
            out.push(*value);
        }
        TermNode::MinOver {
            source,
            value,
            default,
            ..
        }
        | TermNode::MaxOver {
            source,
            value,
            default,
            ..
        }
        | TermNode::Argmin {
            source,
            value,
            default,
            ..
        }
        | TermNode::ArgminUnique {
            source,
            value,
            default,
            ..
        }
        | TermNode::Argmax {
            source,
            value,
            default,
            ..
        } => {
            out.push(*source);
            out.push(*value);
            if let Some(d) = default {
                out.push(*d);
            }
        }
        TermNode::ArgminRefusal {
            source,
            value,
            refused,
            ..
        } => {
            out.push(*source);
            out.push(*value);
            if let Some(r) = refused {
                out.push(*r);
            }
        }
        TermNode::Fold {
            source, init, body, ..
        } => {
            out.push(*source);
            out.push(*init);
            out.push(*body);
        }
        TermNode::Holds { node, node2, .. } => {
            if let Some(n) = node {
                out.push(*n);
            }
            if let Some(n) = node2 {
                out.push(*n);
            }
        }
        TermNode::EvalSubgraph { node } => out.push(*node),
        // --- universal codec primitives ---
        TermNode::BitsAt {
            buffer,
            bitpos,
            n_bits,
        } => {
            out.push(*buffer);
            out.push(*bitpos);
            out.push(*n_bits);
        }
        TermNode::BitsWrite {
            buffer,
            bitpos,
            value,
            n_bits,
        } => {
            out.push(*buffer);
            out.push(*bitpos);
            out.push(*value);
            out.push(*n_bits);
        }
        TermNode::BitsWriteAll { buffer, writes } => {
            out.push(*buffer);
            out.push(*writes);
        }
        TermNode::BitsAtAll { buffer, reads } => {
            out.push(*buffer);
            out.push(*reads);
        }
        TermNode::HuffmanDecodeStream {
            buffer,
            bitpos,
            table,
            n_pairs,
        } => {
            out.push(*buffer);
            out.push(*bitpos);
            out.push(*table);
            out.push(*n_pairs);
        }
        TermNode::HuffmanEncodeStream {
            buffer,
            bitpos,
            pairs,
            table,
        } => {
            out.push(*buffer);
            out.push(*bitpos);
            out.push(*pairs);
            out.push(*table);
        }
        TermNode::ExpGolombDecode { buffer, bitpos }
        | TermNode::ExpGolombDecodeSigned { buffer, bitpos } => {
            out.push(*buffer);
            out.push(*bitpos);
        }
        TermNode::ExpGolombEncode {
            buffer,
            bitpos,
            value,
        }
        | TermNode::ExpGolombEncodeSigned {
            buffer,
            bitpos,
            value,
        } => {
            out.push(*buffer);
            out.push(*bitpos);
            out.push(*value);
        }
        // --- set algebra (Phase 7 ext) ---
        TermNode::Union { a, b } | TermNode::Intersect { a, b } | TermNode::Difference { a, b } => {
            out.push(*a);
            out.push(*b);
        }
        TermNode::Last { seq } => out.push(*seq),
        TermNode::IndexAt { seq, index } => {
            out.push(*seq);
            out.push(*index);
        }
        TermNode::ListDrop { list, index } => {
            out.push(*list);
            out.push(*index);
        }
        TermNode::Append { seq, item } => {
            out.push(*seq);
            out.push(*item);
        }
        TermNode::MapSet { source, value, .. } | TermNode::MapList { source, value, .. } => {
            out.push(*source);
            out.push(*value);
        }
        // --- edge-attr DSL (Phase 7 ext) ---
        TermNode::Edges { node, .. } => out.push(*node),
        TermNode::EdgeAttr { edge, .. } => out.push(*edge),
        // --- indexed lookup (Phase 7b) ---
        TermNode::NodesWhere { value, .. } => out.push(*value),
        TermNode::AntiUnify { values, .. } => out.push(*values),
        TermNode::AttrByName { node, name } => {
            out.push(*node);
            out.push(*name);
        }
        TermNode::FixedCount { pattern, .. } => out.push(*pattern),
        TermNode::Covers {
            pattern, instance, ..
        } => {
            out.push(*pattern);
            out.push(*instance);
        }
        TermNode::CoversOpen {
            pattern, instance, ..
        } => {
            out.push(*pattern);
            out.push(*instance);
        }
        TermNode::AntiUnifyWitness { values, .. } => out.push(*values),
        TermNode::Substitute {
            template, sigma, ..
        } => {
            out.push(*template);
            out.push(*sigma);
        }
        TermNode::Unify { values, .. } => out.push(*values),
        TermNode::StructSim { a, b, .. } => {
            out.push(*a);
            out.push(*b);
        }
        TermNode::ShapeDecode {
            goal,
            exclude,
            codebook_scope,
            ..
        } => {
            out.push(*goal);
            if let Some(e) = exclude {
                out.push(*e);
            }
            if let Some(sc) = codebook_scope {
                out.push(*sc);
            }
        }
        TermNode::MotorCompose {
            episode,
            policy,
            candidate,
        } => {
            out.push(*episode);
            out.push(*policy);
            out.push(*candidate);
        }
        TermNode::FutureManifoldProjection {
            episode,
            policy,
            source,
            addition,
            ..
        } => {
            out.push(*episode);
            out.push(*policy);
            out.push(*source);
            if let Some(a) = addition {
                out.push(*a);
            }
        }
        TermNode::FutureManifoldSelection {
            episode,
            policy,
            candidates,
            ..
        } => {
            out.push(*episode);
            out.push(*policy);
            out.push(*candidates);
        }
        TermNode::TransformDecode { goal, exclude, .. } => {
            out.push(*goal);
            if let Some(e) = exclude {
                out.push(*e);
            }
        }
        TermNode::NetForward { assemblage, inputs } => {
            out.push(*assemblage);
            out.push(*inputs);
        }
        TermNode::DimInfer { goal, exclude, .. } => {
            out.push(*goal);
            if let Some(e) = exclude {
                out.push(*e);
            }
        }
        TermNode::GenInfer { goal, exclude, .. } => {
            out.push(*goal);
            if let Some(e) = exclude {
                out.push(*e);
            }
        }
        TermNode::RatioInduce { population, .. } => {
            out.push(*population);
        }
        TermNode::LogQuantum { population, .. } => {
            out.push(*population);
        }
        TermNode::TimeInfer { sequence, .. } => {
            out.push(*sequence);
        }
        TermNode::DepthInfer { sequence, .. } => {
            out.push(*sequence);
        }
        TermNode::BlinkBridge { sequence, .. } => {
            out.push(*sequence);
        }
        TermNode::GapAbduce { sequence, .. } => {
            out.push(*sequence);
        }
        TermNode::GapVerify { sequence, .. } => {
            out.push(*sequence);
        }
        TermNode::SupportInfer { sequence, .. } => {
            out.push(*sequence);
        }
        TermNode::MotionEnergy { sequence, .. } => {
            out.push(*sequence);
        }
        TermNode::TransferDecode { goal, .. } => {
            out.push(*goal);
        }
        TermNode::RecogniseShape { text, .. } => {
            out.push(*text);
        }
        TermNode::MetaShapeMint { observation, .. } => {
            out.push(*observation);
        }
        TermNode::StrokeQuantize {
            points,
            turn_edges,
            len_edges,
            bounds,
            ..
        } => {
            out.push(*points);
            if let Some(e) = turn_edges {
                out.push(*e);
            }
            if let Some(e) = len_edges {
                out.push(*e);
            }
            if let Some(b) = bounds {
                out.push(*b);
            }
        }
        TermNode::StrokeRender {
            signature,
            turn_edges,
            len_edges,
            bounds,
            ..
        } => {
            out.push(*signature);
            if let Some(e) = turn_edges {
                out.push(*e);
            }
            if let Some(e) = len_edges {
                out.push(*e);
            }
            if let Some(b) = bounds {
                out.push(*b);
            }
        }
        TermNode::SigmaLognormalGenerate {
            primitives, start, ..
        } => {
            out.push(*primitives);
            out.push(*start);
        }
        TermNode::LookaheadValue { node, depth, .. } => {
            out.push(*node);
            out.push(*depth);
        }
        TermNode::Not { arg }
        | TermNode::Abs { arg }
        | TermNode::Neg { arg }
        | TermNode::EnclosedCount { arg }
        | TermNode::Sqrt { arg }
        | TermNode::Log { arg }
        | TermNode::Exp { arg }
        | TermNode::Magnitude { arg }
        | TermNode::Sin { arg }
        | TermNode::Cos { arg }
        | TermNode::Bearing { arg } => out.push(*arg),
        TermNode::IfThenElse { cond, then, other } => {
            out.push(*cond);
            out.push(*then);
            out.push(*other);
        }
        TermNode::Join { separator, items } => {
            if let Some(s) = separator {
                out.push(*s);
            }
            if let Some(i) = items {
                out.push(*i);
            }
        }
        TermNode::U8 { expr }
        | TermNode::U16LE { expr }
        | TermNode::U32LE { expr }
        | TermNode::U64LE { expr }
        | TermNode::LEB128 { expr } => {
            if let Some(e) = expr {
                out.push(*e);
            }
        }
        TermNode::Let { value, body, .. } => {
            if let Some(v) = value {
                out.push(*v);
            }
            if let Some(b) = body {
                out.push(*b);
            }
        }
        TermNode::Nth { items, .. } => {
            if let Some(i) = items {
                out.push(*i);
            }
        }
        TermNode::Render { term, lang } => {
            if let Some(t) = term {
                out.push(*t);
            }
            if let Some(l) = lang {
                out.push(*l);
            }
        }
        TermNode::LitRepr { value } => {
            if let Some(v) = value {
                out.push(*v);
            }
        }
        TermNode::TrackIdentityCorrespondence {
            prev, cur, radius, ..
        } => {
            out.push(*prev);
            out.push(*cur);
            out.push(*radius);
        }
        // --- Program IR (P1) ---
        TermNode::ProgSeq { stmts } => out.extend(stmts.iter().copied()),
        TermNode::ProgAssignVar { value, .. }
        | TermNode::ProgAugAssign { value, .. }
        | TermNode::ProgTupleUnpack { value, .. } => out.push(*value),
        TermNode::ProgIfStmt { cond, then, orelse } => {
            out.push(*cond);
            out.push(*then);
            if let Some(o) = orelse {
                out.push(*o);
            }
        }
        TermNode::ProgForEach {
            iter, body, orelse, ..
        } => {
            out.push(*iter);
            out.push(*body);
            if let Some(o) = orelse {
                out.push(*o);
            }
        }
        TermNode::ProgWhile { cond, body, orelse } => {
            out.push(*cond);
            out.push(*body);
            if let Some(o) = orelse {
                out.push(*o);
            }
        }
        TermNode::ProgLoopCtl { .. } | TermNode::ProgImportStmt { .. } => {}
        TermNode::ProgReturn { value } => {
            if let Some(v) = value {
                out.push(*v);
            }
        }
        TermNode::ProgTryOr { body, handler, .. } => {
            out.push(*body);
            if let Some(h) = handler {
                out.push(*h);
            }
        }
        TermNode::ProgRaise { exc } => {
            if let Some(e) = exc {
                out.push(*e);
            }
        }
        TermNode::ProgSubscriptSet { obj, index, value } => {
            out.push(*obj);
            out.push(*index);
            out.push(*value);
        }
        TermNode::ProgAttrSet { obj, value, .. } => {
            out.push(*obj);
            out.push(*value);
        }
        TermNode::ProgDefFnParam { default, .. } => {
            if let Some(d) = default {
                out.push(*d);
            }
        }
        TermNode::ProgCallExtern { recv, args, .. } => {
            if let Some(r) = recv {
                out.push(*r);
            }
            out.extend(args.iter().copied());
        }
        TermNode::ProgAttrGet { obj, .. } => out.push(*obj),
        TermNode::ProgSubscript { obj, index } => {
            out.push(*obj);
            out.push(*index);
        }
        TermNode::ProgSlice {
            obj,
            start,
            stop,
            step,
        } => {
            out.push(*obj);
            if let Some(s) = start {
                out.push(*s);
            }
            if let Some(s) = stop {
                out.push(*s);
            }
            if let Some(s) = step {
                out.push(*s);
            }
        }
        TermNode::ProgContainerLit { items, .. } => out.extend(items.iter().copied()),
        TermNode::ProgComprehensionList {
            source, expr, cond, ..
        }
        | TermNode::ProgComprehensionGen {
            source, expr, cond, ..
        } => {
            out.push(*source);
            out.push(*expr);
            if let Some(c) = cond {
                out.push(*c);
            }
        }
        TermNode::ProgIsOp { a, b, .. } => {
            out.push(*a);
            out.push(*b);
        }
        TermNode::ProgFString { parts } => out.extend(parts.iter().copied()),
        TermNode::ProgEval {
            prog, env, oracles, ..
        } => {
            out.push(*prog);
            if let Some(e) = env {
                out.push(*e);
            }
            if let Some(o) = oracles {
                out.push(*o);
            }
        }
        TermNode::SnakeCase { text } | TermNode::CaseFold { text } => out.push(*text),
        TermNode::Call { args, .. } => out.extend(args.iter().copied()),
        TermNode::SynthEnumerate {
            examples,
            ops,
            consts,
            exclude,
            derived_ops,
            exclude_ops,
            ..
        } => {
            out.push(*examples);
            if let Some(o) = ops {
                out.push(*o);
            }
            if let Some(c) = consts {
                out.push(*c);
            }
            if let Some(e) = exclude {
                out.push(*e);
            }
            if let Some(d) = derived_ops {
                out.push(*d);
            }
            if let Some(x) = exclude_ops {
                out.push(*x);
            }
        }
        TermNode::ParetoDominates {
            candidate,
            alternative,
            dimension_count,
            ..
        } => {
            out.push(*candidate);
            out.push(*alternative);
            out.push(*dimension_count);
        }
        // Rung 1 Tier-1 stdlib Term ports.
        TermNode::Replace { text, old, new } => {
            out.push(*text);
            out.push(*old);
            out.push(*new);
        }
        TermNode::Str { value } => out.push(*value),
        TermNode::Split { text, sep } => {
            out.push(*text);
            out.push(*sep);
        }
        TermNode::StrCount { text, sub } => {
            out.push(*text);
            out.push(*sub);
        }
        TermNode::Round { value, ndigits } => {
            out.push(*value);
            out.push(*ndigits);
        }
        TermNode::Reverse { seq } => out.push(*seq),
        TermNode::IndexedMap { source, value, .. } => {
            out.push(*source);
            out.push(*value);
        }
        TermNode::Capitalize { text } => out.push(*text),
        TermNode::ParseInt { text } => out.push(*text),
        TermNode::Slice { seq, start, stop } => {
            out.push(*seq);
            out.push(*start);
            out.push(*stop);
        }
        TermNode::Sort { seq } => out.push(*seq),
        TermNode::DictItems { seq } => out.push(*seq),
        TermNode::SortBy { source, key, .. } => {
            out.push(*source);
            out.push(*key);
        }
        TermNode::GroupCount { seq } => out.push(*seq),
        TermNode::DictMerge { a, b } => {
            out.push(*a);
            out.push(*b);
        }
        TermNode::ZipWith { a, b, value, .. } => {
            out.push(*a);
            out.push(*b);
            out.push(*value);
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::TypedGraph;
    use crate::sym::Interner;

    #[test]
    fn arena_round_trip() {
        let mut a = TermArena::new();
        let i = a.add(TermNode::Lit {
            value: Value::Int(42),
        });
        assert!(matches!(a.get(i), TermNode::Lit { .. }));
    }

    #[test]
    fn lit_evaluates() {
        let mut a = TermArena::new();
        let i = a.add(TermNode::Lit {
            value: Value::Int(7),
        });
        let g = TypedGraph::new();
        let ir = Interner::new();
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir);
        assert_eq!(evaluate(&a, i, &mut env, &mut ctx), Value::Int(7));
    }

    // ------------------------------------------------------------------
    // `CoversOpen` / `covers_open_value` — open-arity relation-SET coverage.
    // Gates META_SHAPE_ARITY_AND_KEY_SEPARATOR_FIXES: a held k-relation
    // MetaShape must cover a (k+n)-relation observation (superset-tolerant)
    // and must NOT cover a (k-1)-relation one (never subset-tolerant), while
    // `Covers` itself keeps its exact equal-arity semantics.
    // ------------------------------------------------------------------

    /// The WILD marker, as `evaluate` builds it for every shape-math Term.
    fn co_wild(ir: &mut Interner) -> Value {
        Value::Tuple(std::sync::Arc::new(smallvec::smallvec![Value::Str(
            ir.intern("·?·")
        )]))
    }

    /// A signature: a LIST of `[predicate, value]` relations, exactly the
    /// shape `domains/meta_shape.py::item_signature` writes. `None` in the
    /// value slot is the WILD an anti-unified codebook entry carries.
    fn co_sig(ir: &mut Interner, rels: &[(&str, Option<&str>)]) -> Value {
        let wild = co_wild(ir);
        let mut out: smallvec::SmallVec<[Value; 4]> = smallvec::SmallVec::new();
        for (p, v) in rels {
            let val = match v {
                Some(s) => Value::Str(ir.intern(s)),
                None => wild.clone(),
            };
            let pv = Value::Str(ir.intern(p));
            out.push(Value::List(std::sync::Arc::new(smallvec::smallvec![
                pv, val
            ])));
        }
        Value::List(std::sync::Arc::new(out))
    }

    /// The held 4-relation pattern, exactly as `MetaShapeMint` anti-unifies it
    /// live from two `TradeRecord` observations: predicates fixed, differing
    /// values WILD.
    const CO_HELD: &[(&str, Option<&str>)] = &[
        ("buyer", None),
        ("is_a", Some("traderecord")),
        ("lot", None),
        ("seller", None),
    ];

    #[test]
    fn covers_open_accepts_a_superset_instance() {
        let mut ir = Interner::new();
        let wild = co_wild(&mut ir);
        let pattern = co_sig(&mut ir, CO_HELD);
        // The k+1 observation: the same four relations plus one extra attr.
        let inst = co_sig(
            &mut ir,
            &[
                ("buyer", Some("gary")),
                ("is_a", Some("traderecord")),
                ("lot", Some("13")),
                ("note", Some("anything")),
                ("seller", Some("hank")),
            ],
        );
        assert!(covers_open_value(&pattern, &inst, &wild));
        // ... and the SHARED primitive is unchanged: `Covers` still refuses it.
        assert!(!covers_value(&pattern, &inst, &wild));
    }

    #[test]
    fn covers_open_still_accepts_an_exact_arity_instance() {
        let mut ir = Interner::new();
        let wild = co_wild(&mut ir);
        let pattern = co_sig(&mut ir, CO_HELD);
        let inst = co_sig(
            &mut ir,
            &[
                ("buyer", Some("alice")),
                ("is_a", Some("traderecord")),
                ("lot", Some("7")),
                ("seller", Some("bob")),
            ],
        );
        assert!(covers_open_value(&pattern, &inst, &wild));
        assert!(covers_value(&pattern, &inst, &wild));
    }

    #[test]
    fn covers_open_refuses_a_subset_instance() {
        let mut ir = Interner::new();
        let wild = co_wild(&mut ir);
        let pattern = co_sig(&mut ir, CO_HELD);
        // `seller` absent — a strict SUBSET. Open arity must be
        // superset-tolerant only; this is the bar separating a fix from a
        // weakening.
        let inst = co_sig(
            &mut ir,
            &[
                ("buyer", Some("alice")),
                ("is_a", Some("traderecord")),
                ("lot", Some("7")),
            ],
        );
        assert!(!covers_open_value(&pattern, &inst, &wild));
    }

    #[test]
    fn covers_open_refuses_a_disjoint_instance() {
        let mut ir = Interner::new();
        let wild = co_wild(&mut ir);
        let pattern = co_sig(&mut ir, CO_HELD);
        let inst = co_sig(
            &mut ir,
            &[
                ("definition", Some("a held generalisation")),
                ("domain", Some("engine")),
                ("is_a", Some("concept")),
                ("name", Some("shape")),
                ("source", Some("seed")),
            ],
        );
        assert!(!covers_open_value(&pattern, &inst, &wild));
    }

    #[test]
    fn covers_open_keeps_relations_positional() {
        let mut ir = Interner::new();
        let wild = co_wild(&mut ir);
        let pattern = co_sig(&mut ir, &[("buyer", None)]);
        // Same two atoms, swapped slots. A SET reading of the inner relation
        // would accept this; the inner comparison is `covers_value`, so it
        // must not.
        let swapped = co_sig(&mut ir, &[("alice", Some("buyer"))]);
        assert!(!covers_open_value(&pattern, &swapped, &wild));
        let right_way = co_sig(&mut ir, &[("buyer", Some("alice"))]);
        assert!(covers_open_value(&pattern, &right_way, &wild));
    }

    #[test]
    fn covers_open_matching_is_injective() {
        let mut ir = Interner::new();
        let wild = co_wild(&mut ir);
        // Two IDENTICAL pattern relations against ONE matching instance
        // relation: a per-element existential would accept; an injective
        // matching refuses.
        let pattern = co_sig(
            &mut ir,
            &[("buyer", Some("alice")), ("buyer", Some("alice"))],
        );
        let one = co_sig(
            &mut ir,
            &[("buyer", Some("alice")), ("is_a", Some("traderecord"))],
        );
        assert!(!covers_open_value(&pattern, &one, &wild));
        let two = co_sig(
            &mut ir,
            &[
                ("buyer", Some("alice")),
                ("buyer", Some("alice")),
                ("is_a", Some("traderecord")),
            ],
        );
        assert!(covers_open_value(&pattern, &two, &wild));
    }

    #[test]
    fn covers_open_delegates_non_list_containers_verbatim() {
        let mut ir = Interner::new();
        let wild = co_wild(&mut ir);
        // Dict, Set and scalar arms must be byte-identical to `covers_value` —
        // this Term changes ONE arm, at ONE level.
        let k = Value::Str(ir.intern("k"));
        let extra = Value::Str(ir.intern("extra"));
        let pd = Value::Dict(std::sync::Arc::from(vec![(k.clone(), Value::Int(1))]));
        let id = Value::Dict(std::sync::Arc::from(vec![
            (extra, Value::Int(2)),
            (k, Value::Int(1)),
        ]));
        assert_eq!(
            covers_open_value(&pd, &id, &wild),
            covers_value(&pd, &id, &wild)
        );
        let ps = Value::Set(std::sync::Arc::from(vec![Value::Int(1)]));
        let is = Value::Set(std::sync::Arc::from(vec![Value::Int(1), Value::Int(2)]));
        assert_eq!(
            covers_open_value(&ps, &is, &wild),
            covers_value(&ps, &is, &wild)
        );
        assert_eq!(
            covers_open_value(&Value::Int(3), &Value::Int(4), &wild),
            covers_value(&Value::Int(3), &Value::Int(4), &wild)
        );
        // A WILD pattern still covers anything.
        assert!(covers_open_value(&wild, &is, &wild));
    }

    #[test]
    fn covers_open_term_round_trips_through_json() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let p = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let i = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let w = ir.intern("·?·");
        let t = a.add(TermNode::CoversOpen {
            pattern: p,
            instance: i,
            wild: w,
        });
        let json = crate::jsonio::term_to_json(&a, t, &ir);
        assert_eq!(json["type"], serde_json::json!("CoversOpen"));
        let mut b = TermArena::new();
        let back = crate::jsonio::term_from_json(&json, &mut b, &mut ir)
            .expect("CoversOpen must parse back from its own JSON");
        assert!(matches!(b.get(back), TermNode::CoversOpen { .. }));
    }

    // ------------------------------------------------------------------
    // ToJsonString / FromJsonString / ShiftThresholdLits -- the three
    // experiment-composer Terms (gamma-substrate composer-migration
    // follow-on). See tests/test_dialect_experiment_terms.py for the
    // Python-side proof (a graph-resident meta-rule using all three).
    // ------------------------------------------------------------------

    fn fresh_ctx<'a>(g: &'a TypedGraph, ir: &'a Interner) -> EvalCtx<'a> {
        EvalCtx::new(g, ir)
    }

    #[test]
    fn to_json_string_serialises_mkdict_output() {
        let mut a = TermArena::new();
        // MkDict("a", 1, "b", StringConcat(["x","y"])) -> ToJsonString(...)
        let g = TypedGraph::new();
        let mut ir = Interner::new();
        let sym_a = ir.intern("a");
        let sym_b = ir.intern("b");
        let ka = a.add(TermNode::Lit {
            value: Value::Str(sym_a),
        });
        let va = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let kb = a.add(TermNode::Lit {
            value: Value::Str(sym_b),
        });
        let part_x = a.add(TermNode::Lit {
            value: Value::Str(ir.intern("x")),
        });
        let part_y = a.add(TermNode::Lit {
            value: Value::Str(ir.intern("y")),
        });
        let concat = a.add(TermNode::StringConcat {
            parts: vec![part_x, part_y],
        });
        let dict = a.add(TermNode::MkDict {
            items: vec![ka, va, kb, concat],
        });
        let tojson = a.add(TermNode::ToJsonString { value: dict });

        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        let out = evaluate(&a, tojson, &mut env, &mut ctx);
        let Value::Surface(SurfaceKind::Text, bytes) = out else {
            panic!("expected Surface(Text)")
        };
        let s = String::from_utf8(bytes.to_vec()).unwrap();
        let parsed: serde_json::Value = serde_json::from_str(&s).unwrap();
        assert_eq!(parsed, serde_json::json!({"a": 1, "b": "xy"}));
    }

    #[test]
    fn from_json_string_parses_nested_structure() {
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let ir = Interner::new();
        let text = a.add(TermNode::Lit {
            value: Value::Surface(
                SurfaceKind::Text,
                Arc::from(
                    br#"{"type":"Lt","a":{"type":"Var","name":"x"},"b":{"type":"Lit","value":3}}"#
                        .as_slice(),
                ),
            ),
        });
        let parsed = a.add(TermNode::FromJsonString { text });
        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        let out = evaluate(&a, parsed, &mut env, &mut ctx);
        let Value::Dict(pairs) = out else {
            panic!("expected Dict")
        };
        let ty = dict_get(&pairs, "type", &ir).unwrap();
        assert_eq!(
            ty,
            &Value::Surface(SurfaceKind::Text, Arc::from(b"Lt".as_slice()))
        );
        let b = dict_get(&pairs, "b", &ir).unwrap();
        let Value::Dict(bp) = b else {
            panic!("expected nested Dict")
        };
        let v = dict_get(bp, "value", &ir).unwrap();
        assert_eq!(v, &Value::Int(3));
    }

    #[test]
    fn shift_threshold_lits_shifts_lt_and_gt_leaves_only() {
        // {"type":"And","items":[Lt(x, Lit(5)), Gt(y, Lit(-2)), Eq(z, Lit(9))]}
        // shift=1.5 -> Lt's Lit becomes 3.5, Gt's Lit becomes -0.5, Eq's Lit
        // (not Lt/Gt) is untouched.
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let mut ir = Interner::new();
        let mk_cmp = |a: &mut TermArena,
                      ir: &mut Interner,
                      ty: &str,
                      var: &str,
                      lit_type: &str,
                      val: Value|
         -> TermIdx {
            let type_k = a.add(TermNode::Lit {
                value: Value::Str(ir.intern("type")),
            });
            let type_v = a.add(TermNode::Lit {
                value: Value::Str(ir.intern(ty)),
            });
            let a_k = a.add(TermNode::Lit {
                value: Value::Str(ir.intern("a")),
            });
            let var_type_k = a.add(TermNode::Lit {
                value: Value::Str(ir.intern("type")),
            });
            let var_type_v = a.add(TermNode::Lit {
                value: Value::Str(ir.intern("Var")),
            });
            let var_name_k = a.add(TermNode::Lit {
                value: Value::Str(ir.intern("name")),
            });
            let var_name_v = a.add(TermNode::Lit {
                value: Value::Str(ir.intern(var)),
            });
            let a_v = a.add(TermNode::MkDict {
                items: vec![var_type_k, var_type_v, var_name_k, var_name_v],
            });
            let b_k = a.add(TermNode::Lit {
                value: Value::Str(ir.intern("b")),
            });
            let lit_type_k = a.add(TermNode::Lit {
                value: Value::Str(ir.intern("type")),
            });
            let lit_type_v = a.add(TermNode::Lit {
                value: Value::Str(ir.intern(lit_type)),
            });
            let lit_val_k = a.add(TermNode::Lit {
                value: Value::Str(ir.intern("value")),
            });
            let lit_val_v = a.add(TermNode::Lit { value: val });
            let b_v = a.add(TermNode::MkDict {
                items: vec![lit_type_k, lit_type_v, lit_val_k, lit_val_v],
            });
            a.add(TermNode::MkDict {
                items: vec![type_k, type_v, a_k, a_v, b_k, b_v],
            })
        };
        let lt_node = mk_cmp(&mut a, &mut ir, "Lt", "x", "Lit", Value::Float(5.0));
        let gt_node = mk_cmp(&mut a, &mut ir, "Gt", "y", "Lit", Value::Float(-2.0));
        let eq_node = mk_cmp(&mut a, &mut ir, "Eq", "z", "Lit", Value::Float(9.0));
        let items_type_k = a.add(TermNode::Lit {
            value: Value::Str(ir.intern("type")),
        });
        let items_type_v = a.add(TermNode::Lit {
            value: Value::Str(ir.intern("And")),
        });
        let items_k = a.add(TermNode::Lit {
            value: Value::Str(ir.intern("items")),
        });
        // "items" as an array-shaped Term value: build via nested Append
        // over an empty tuple literal (matches the composer's own AP/EMPTY_TUPLE
        // convention in tests/test_rule_minting_dialect.py).
        let empty = a.add(TermNode::Lit {
            value: Value::Tuple(Arc::new(SmallVec::new())),
        });
        let ap1 = a.add(TermNode::Append {
            seq: empty,
            item: lt_node,
        });
        let ap2 = a.add(TermNode::Append {
            seq: ap1,
            item: gt_node,
        });
        let ap3 = a.add(TermNode::Append {
            seq: ap2,
            item: eq_node,
        });
        let and_node = a.add(TermNode::MkDict {
            items: vec![items_type_k, items_type_v, items_k, ap3],
        });

        let shift_lit = a.add(TermNode::Lit {
            value: Value::Float(1.5),
        });
        let shifted = a.add(TermNode::ShiftThresholdLits {
            tree: and_node,
            shift: shift_lit,
        });

        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        let out = evaluate(&a, shifted, &mut env, &mut ctx);
        let Value::Dict(pairs) = out else {
            panic!("expected Dict")
        };
        let (Value::Tuple(items) | Value::List(items)) = dict_get(&pairs, "items", &ir).unwrap()
        else {
            panic!("expected Tuple")
        };
        assert_eq!(items.len(), 3);
        let get_b_value = |v: &Value| -> Value {
            let Value::Dict(p) = v else {
                panic!("expected Dict")
            };
            let Value::Dict(b) = dict_get(p, "b", &ir).unwrap() else {
                panic!("expected Dict")
            };
            dict_get(b, "value", &ir).unwrap().clone()
        };
        assert_eq!(get_b_value(&items[0]), Value::Float(3.5)); // Lt: 5.0 - 1.5
        assert_eq!(get_b_value(&items[1]), Value::Float(-0.5)); // Gt: -2.0 + 1.5
        assert_eq!(get_b_value(&items[2]), Value::Float(9.0)); // Eq: untouched
    }

    #[test]
    fn dict_get_reads_str_keyed_and_surface_keyed_dicts() {
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let mut ir = Interner::new();

        // Intern every needed string BEFORE building ctx (EvalCtx borrows
        // the interner immutably; `ir.intern` needs `&mut`).
        let sym_k = ir.intern("k");
        let sym_json = ir.intern(r#"{"k": 42}"#);
        let sym_nope = ir.intern("nope");

        // Str-keyed (MkDict-built): DictGet(MkDict("k", 42), "k") == 42.
        let k_lit = a.add(TermNode::Lit {
            value: Value::Str(sym_k),
        });
        let v_lit = a.add(TermNode::Lit {
            value: Value::Int(42),
        });
        let mkdict = a.add(TermNode::MkDict {
            items: vec![k_lit, v_lit],
        });
        let key_query = a.add(TermNode::Lit {
            value: Value::Str(sym_k),
        });
        let get1 = a.add(TermNode::DictGet {
            dict: mkdict,
            key: key_query,
        });

        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        assert_eq!(evaluate(&a, get1, &mut env, &mut ctx), Value::Int(42));

        // Surface-keyed (FromJsonString-parsed): DictGet(parsed, "k") == 42.
        let text = a.add(TermNode::Lit {
            value: Value::Str(sym_json),
        });
        let parsed = a.add(TermNode::FromJsonString { text });
        let key_query2 = a.add(TermNode::Lit {
            value: Value::Str(sym_k),
        });
        let get2 = a.add(TermNode::DictGet {
            dict: parsed,
            key: key_query2,
        });
        assert_eq!(evaluate(&a, get2, &mut env, &mut ctx), Value::Int(42));

        // Missing key -> None; non-Dict input -> None.
        let missing_key = a.add(TermNode::Lit {
            value: Value::Str(sym_nope),
        });
        let get3 = a.add(TermNode::DictGet {
            dict: mkdict,
            key: missing_key,
        });
        assert_eq!(evaluate(&a, get3, &mut env, &mut ctx), Value::None);
        let not_a_dict = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let get4 = a.add(TermNode::DictGet {
            dict: not_a_dict,
            key: k_lit,
        });
        assert_eq!(evaluate(&a, get4, &mut env, &mut ctx), Value::None);
    }

    #[test]
    fn rewrite_tree_nodes_flips_lt_gt_in_one_pass() {
        // {"type":"And","items":[Lt(b:1), Gt(b:2), Eq(b:3)]} rewritten via
        // field="type", value_map={"Lt":"Gt","Gt":"Lt","Lte":"Gte","Gte":"Lte"},
        // type_filter=None -- the exact `apply_flip_comparison` shape, ONE
        // pass (not sequential re-application, which would double-flip).
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let mut ir = Interner::new();
        let tree_json = ir.intern(r#"{"type":"And","items":[{"type":"Lt","b":1},{"type":"Gt","b":2},{"type":"Eq","b":3}]}"#);
        let vm_json = ir.intern(r#"{"Lt":"Gt","Gt":"Lt","Lte":"Gte","Gte":"Lte"}"#);
        let type_sym = ir.intern("type");

        let text = a.add(TermNode::Lit {
            value: Value::Str(tree_json),
        });
        let tree = a.add(TermNode::FromJsonString { text });
        let vm_text = a.add(TermNode::Lit {
            value: Value::Str(vm_json),
        });
        let value_map = a.add(TermNode::FromJsonString { text: vm_text });
        let field = a.add(TermNode::Lit {
            value: Value::Str(type_sym),
        });
        let rewrite = a.add(TermNode::RewriteTreeNodes {
            tree,
            type_filter: None,
            field,
            value_map,
        });

        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        let out = evaluate(&a, rewrite, &mut env, &mut ctx);
        let Value::Dict(pairs) = out else {
            panic!("expected Dict")
        };
        let (Value::Tuple(items) | Value::List(items)) = dict_get(&pairs, "items", &ir).unwrap()
        else {
            panic!("expected Tuple")
        };
        assert_eq!(items.len(), 3);
        let get_type = |v: &Value| -> String {
            let Value::Dict(p) = v else {
                panic!("expected Dict")
            };
            dict_type_str(p, &ir).unwrap().into_owned()
        };
        assert_eq!(get_type(&items[0]), "Gt"); // Lt -> Gt
        assert_eq!(get_type(&items[1]), "Lt"); // Gt -> Lt
        assert_eq!(get_type(&items[2]), "Eq"); // untouched (not in value_map)
    }

    #[test]
    fn rewrite_tree_nodes_swaps_attr_key_guarded_by_type_filter() {
        // The exact `apply_swap_term_leaf` shape: type_filter="Attr",
        // field="key", value_map={old_key: new_key}. A DIFFERENT node type
        // with the same "key" field is untouched -- the guard is load-bearing.
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let mut ir = Interner::new();
        let attr_json = ir.intern(r#"{"type":"Attr","key":"row"}"#);
        let other_json = ir.intern(r#"{"type":"NotAttr","key":"row"}"#);
        let vm_json = ir.intern(r#"{"row":"col"}"#);
        let key_sym = ir.intern("key");
        let attr_type_sym = ir.intern("Attr");

        let text1 = a.add(TermNode::Lit {
            value: Value::Str(attr_json),
        });
        let tree1 = a.add(TermNode::FromJsonString { text: text1 });
        let vm_text1 = a.add(TermNode::Lit {
            value: Value::Str(vm_json),
        });
        let value_map1 = a.add(TermNode::FromJsonString { text: vm_text1 });
        let field1 = a.add(TermNode::Lit {
            value: Value::Str(key_sym),
        });
        let type_filter1 = a.add(TermNode::Lit {
            value: Value::Str(attr_type_sym),
        });
        let rewrite1 = a.add(TermNode::RewriteTreeNodes {
            tree: tree1,
            type_filter: Some(type_filter1),
            field: field1,
            value_map: value_map1,
        });

        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        let out1 = evaluate(&a, rewrite1, &mut env, &mut ctx);
        let Value::Dict(p1) = out1 else {
            panic!("expected Dict")
        };
        assert_eq!(
            dict_get(&p1, "key", &ir).unwrap(),
            &Value::Surface(SurfaceKind::Text, Arc::from(b"col".as_slice()))
        );

        let text2 = a.add(TermNode::Lit {
            value: Value::Str(other_json),
        });
        let tree2 = a.add(TermNode::FromJsonString { text: text2 });
        let vm_text2 = a.add(TermNode::Lit {
            value: Value::Str(vm_json),
        });
        let value_map2 = a.add(TermNode::FromJsonString { text: vm_text2 });
        let field2 = a.add(TermNode::Lit {
            value: Value::Str(key_sym),
        });
        let type_filter2 = a.add(TermNode::Lit {
            value: Value::Str(attr_type_sym),
        });
        let rewrite2 = a.add(TermNode::RewriteTreeNodes {
            tree: tree2,
            type_filter: Some(type_filter2),
            field: field2,
            value_map: value_map2,
        });
        let out2 = evaluate(&a, rewrite2, &mut env, &mut ctx);
        let Value::Dict(p2) = out2 else {
            panic!("expected Dict")
        };
        assert_eq!(
            dict_get(&p2, "key", &ir).unwrap(),
            &Value::Surface(SurfaceKind::Text, Arc::from(b"row".as_slice())),
            "type_filter='Attr' guard: a NotAttr node's 'key' field must stay untouched"
        );
    }

    #[test]
    fn attr_key_ranking_matches_find_attr_keys_ordering() {
        // Hand-computed ranking vs domains/edit_ops.py's find_attr_keys:
        // sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])). Tree has
        // "row" referenced 3x, "col" 2x, "flood_epoch" 1x -- plus a
        // NON-Attr node with a "key" field ("NotAttr") that must NOT be
        // tallied (the type=="Attr" guard is load-bearing, same as
        // RewriteTreeNodes's type_filter).
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let mut ir = Interner::new();
        let tree_json = ir.intern(
            r#"{"type":"And","items":[
                {"type":"Lt","a":{"type":"Attr","node":{"type":"Var","name":"n"},"key":"row"},"b":1},
                {"type":"Gt","a":{"type":"Attr","node":{"type":"Var","name":"n"},"key":"row"},"b":2},
                {"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"n"},"key":"row"},
                              "b":{"type":"Attr","node":{"type":"Var","name":"n"},"key":"col"}},
                {"type":"Eq","a":{"type":"Attr","node":{"type":"Var","name":"n"},"key":"col"},
                              "b":{"type":"Attr","node":{"type":"Var","name":"n"},"key":"flood_epoch"}},
                {"type":"Eq","a":{"type":"NotAttr","key":"row"},"b":1}
            ]}"#,
        );
        let text = a.add(TermNode::Lit {
            value: Value::Str(tree_json),
        });
        let tree = a.add(TermNode::FromJsonString { text });
        let ranking = a.add(TermNode::AttrKeyRanking { tree });

        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        let out = evaluate(&a, ranking, &mut env, &mut ctx);
        let (Value::Tuple(pairs) | Value::List(pairs)) = out else {
            panic!("expected Tuple")
        };
        let decoded: Vec<(String, i64)> = pairs
            .iter()
            .map(|p| {
                let (Value::Tuple(kv) | Value::List(kv)) = p else {
                    panic!("expected pair Tuple")
                };
                let Value::Surface(SurfaceKind::Text, k) = &kv[0] else {
                    panic!("expected Surface key")
                };
                let Value::Int(c) = &kv[1] else {
                    panic!("expected Int count")
                };
                (String::from_utf8_lossy(k).into_owned(), *c)
            })
            .collect();
        assert_eq!(
            decoded,
            vec![
                ("row".to_string(), 3),
                ("col".to_string(), 2),
                ("flood_epoch".to_string(), 1),
            ],
            "ranked by (-count, key), NotAttr's 'key' field never tallied"
        );
    }

    #[test]
    fn attr_key_ranking_ties_break_ascending_by_key() {
        // Three keys tied at count=1 -- tiebreak is ascending key (Python's
        // (-count, key) sort), so IndexAt(ranking, 0)/(1) are deterministic.
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let mut ir = Interner::new();
        let tree_json = ir.intern(
            r#"{"type":"And","items":[
                {"type":"Attr","node":{"type":"Var","name":"n"},"key":"zeta"},
                {"type":"Attr","node":{"type":"Var","name":"n"},"key":"alpha"},
                {"type":"Attr","node":{"type":"Var","name":"n"},"key":"mid"}
            ]}"#,
        );
        let text = a.add(TermNode::Lit {
            value: Value::Str(tree_json),
        });
        let tree = a.add(TermNode::FromJsonString { text });
        let ranking = a.add(TermNode::AttrKeyRanking { tree });
        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        let out = evaluate(&a, ranking, &mut env, &mut ctx);
        let (Value::Tuple(pairs) | Value::List(pairs)) = out else {
            panic!("expected Tuple")
        };
        let keys: Vec<String> = pairs
            .iter()
            .map(|p| {
                let (Value::Tuple(kv) | Value::List(kv)) = p else {
                    panic!("expected pair Tuple")
                };
                let Value::Surface(SurfaceKind::Text, k) = &kv[0] else {
                    panic!("expected Surface key")
                };
                String::from_utf8_lossy(k).into_owned()
            })
            .collect();
        assert_eq!(
            keys,
            vec!["alpha".to_string(), "mid".to_string(), "zeta".to_string()]
        );
    }

    #[test]
    fn list_drop_removes_element_and_is_a_mechanical_noop_out_of_range() {
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let ir = Interner::new();
        let list = a.add(TermNode::Lit {
            value: Value::Tuple(Arc::new(smallvec![
                Value::Int(10),
                Value::Int(20),
                Value::Int(30)
            ])),
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);

        let idx1 = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let drop1 = a.add(TermNode::ListDrop { list, index: idx1 });
        assert_eq!(
            evaluate(&a, drop1, &mut env, &mut ctx),
            Value::Tuple(Arc::new(smallvec![Value::Int(10), Value::Int(30)]))
        );

        // Negative index counts from the end (same convention as IndexAt).
        let idx_neg = a.add(TermNode::Lit {
            value: Value::Int(-1),
        });
        let drop_neg = a.add(TermNode::ListDrop {
            list,
            index: idx_neg,
        });
        assert_eq!(
            evaluate(&a, drop_neg, &mut env, &mut ctx),
            Value::Tuple(Arc::new(smallvec![Value::Int(10), Value::Int(20)]))
        );

        // Out-of-range index (after adjustment) is a mechanical no-op --
        // elements come back unchanged. The "would this leave the rule with
        // <1 match edge" business rule is NOT this Term's concern (see
        // TermNode::ListDrop's doc comment) -- that's the composer's guard.
        let idx_oob = a.add(TermNode::Lit {
            value: Value::Int(99),
        });
        let drop_oob = a.add(TermNode::ListDrop {
            list,
            index: idx_oob,
        });
        assert_eq!(
            evaluate(&a, drop_oob, &mut env, &mut ctx),
            Value::Tuple(Arc::new(smallvec![
                Value::Int(10),
                Value::Int(20),
                Value::Int(30)
            ]))
        );

        // Dropping the ONLY element of a 1-tuple IS mechanically valid
        // (index 0 is in-range) -- the Term has no opinion about whether
        // that leaves a semantically sane rule.
        let single = a.add(TermNode::Lit {
            value: Value::Tuple(Arc::new(smallvec![Value::Int(7)])),
        });
        let idx0 = a.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let drop_single = a.add(TermNode::ListDrop {
            list: single,
            index: idx0,
        });
        assert_eq!(
            evaluate(&a, drop_single, &mut env, &mut ctx),
            Value::Tuple(Arc::new(SmallVec::new()))
        );
    }

    #[test]
    fn attr_on_a_dict_value_is_always_none_dictget_is_the_fix() {
        // Documents the exact wall DictGet closes: Attr only reads
        // graph-Node attrs, so Attr(<dict value>, key) is always None.
        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let mut ir = Interner::new();
        let k_lit = a.add(TermNode::Lit {
            value: Value::Str(ir.intern("k")),
        });
        let v_lit = a.add(TermNode::Lit {
            value: Value::Int(42),
        });
        let mkdict = a.add(TermNode::MkDict {
            items: vec![k_lit, v_lit],
        });
        let key_sym = ir.intern("k");
        let attr_read = a.add(TermNode::Attr {
            node: mkdict,
            key: key_sym,
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = fresh_ctx(&g, &ir);
        assert_eq!(evaluate(&a, attr_read, &mut env, &mut ctx), Value::None);
    }

    /// The Term form of the framebuffer vision primitive
    /// (`TermNode::FbFrameSeq`), evaluated DIRECTLY at the Term-eval
    /// layer (below the rule engine). `rewrite::extend_each` NOW threads
    /// a `framebuffers` reference through to `EvalCtx::with_framebuffers`
    /// (see `rewrite.rs`'s `match_rule`/`match_rule_each`/`apply_rule_full`
    /// family + `Substrate::run_rules`/`try_incremental_match`, which pass
    /// `Some(&self.framebuffers)`), so a Rule's `where`-clause containing
    /// `FbFrameSeq` DOES see live data now — that end-to-end path is
    /// covered by `rewrite::tests::fb_frame_seq_gates_where_clause` and
    /// `tests/test_rule_driven_look.py`. This test stays as the narrower,
    /// dependency-free proof that the Term itself is correct when a
    /// caller threads the reference in — no shm/mmap needed, an
    /// `FbHandle` can be built from any buffer satisfying the header
    /// contract, matching `framebuffer.rs`'s own unit tests.
    #[test]
    fn fb_frame_seq_term_reads_current_seq_when_threaded() {
        use rustc_hash::FxHashMap as FxMap;

        // Build a valid header+payload buffer (no real shm — same trick
        // framebuffer.rs's own unit tests use) and wrap it in an
        // FbHandle via the same open() path a real attach would use,
        // by hand-rolling the struct's public fields is not possible
        // (private `map`/`file`), so instead this test proves the Term
        // against `ctx.framebuffers` being ABSENT (documenting the
        // "not wired into the rule engine" half) and, for the "wired if
        // threaded" half, against a handle attached to a REAL temp file
        // under /dev/shm — the same integration path
        // `Substrate::fb_attach` uses, kept self-contained so this test
        // has no dependency on another process.
        let dir = "/dev/shm";
        let name = format!("/jbw_fb_term_test_{}", std::process::id());
        let path = format!("{dir}/{}", name.trim_start_matches('/'));
        let width: u32 = 2;
        let height: u32 = 2;
        let stride = width * 4;
        let payload_len = (height * stride) as usize;
        let total_len = crate::framebuffer::FB_HEADER_LEN + payload_len;
        {
            use std::io::Write;
            let mut f = std::fs::OpenOptions::new()
                .create(true)
                .write(true)
                .truncate(true)
                .open(&path)
                .expect("create /dev/shm test file (skip this test if /dev/shm is unavailable)");
            let mut buf = vec![0u8; total_len];
            buf[0..4].copy_from_slice(&0x4A425746u32.to_le_bytes());
            buf[4..8].copy_from_slice(&1u32.to_le_bytes());
            buf[8..12].copy_from_slice(&width.to_le_bytes());
            buf[12..16].copy_from_slice(&height.to_le_bytes());
            buf[16..20].copy_from_slice(&stride.to_le_bytes());
            buf[20..24].copy_from_slice(&1u32.to_le_bytes());
            buf[24..32].copy_from_slice(&99u64.to_le_bytes());
            f.write_all(&buf).unwrap();
        }

        let handle =
            crate::framebuffer::FbHandle::open(&name).expect("open the /dev/shm file just created");
        let mut fbs: FxMap<u32, crate::framebuffer::FbHandle> = FxMap::default();
        fbs.insert(7, handle);

        let mut a = TermArena::new();
        let g = TypedGraph::new();
        let ir = Interner::new();
        let fb_lit = a.add(TermNode::Lit {
            value: Value::Int(7),
        });
        let term = a.add(TermNode::FbFrameSeq { fb: fb_lit });
        let mut env: Env = SmallVec::new();

        // Untreaded: no framebuffers reference given -> None. This is
        // the CURRENT behaviour of every real rule-engine call site.
        let mut ctx_bare = EvalCtx::new(&g, &ir);
        assert_eq!(evaluate(&a, term, &mut env, &mut ctx_bare), Value::None);

        // Threaded: a caller that DOES build EvalCtx with
        // `.with_framebuffers(&fbs)` gets the real current frame_seq
        // (99, from the header this test wrote) back as an Int.
        let mut ctx_wired = EvalCtx::new(&g, &ir).with_framebuffers(&fbs);
        assert_eq!(evaluate(&a, term, &mut env, &mut ctx_wired), Value::Int(99));

        // Unknown fb_id -> None even when threaded.
        let missing_lit = a.add(TermNode::Lit {
            value: Value::Int(404),
        });
        let missing_term = a.add(TermNode::FbFrameSeq { fb: missing_lit });
        assert_eq!(
            evaluate(&a, missing_term, &mut env, &mut ctx_wired),
            Value::None
        );

        drop(ctx_wired);
        drop(fbs);
        let _ = std::fs::remove_file(&path);
    }

    #[test]
    fn var_lookup_finds_innermost_binding() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let v = a.add(TermNode::Var { name: x });
        let g = TypedGraph::new();
        let mut env: Env = smallvec![(x, Value::Int(1)), (x, Value::Int(2))];
        let mut ctx = EvalCtx::new(&g, &ir);
        // most-recent binding wins
        assert_eq!(evaluate(&a, v, &mut env, &mut ctx), Value::Int(2));
    }

    #[test]
    fn count_filter_over_neighbours() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let cell = ir.intern("Cell");
        let alive = ir.intern("AliveCell");
        let adj = ir.intern("adjacent_to");
        let me_var = ir.intern("me");
        let n_var = ir.intern("n");

        let me_node = g.insert_node(cell, FxHashMap::default());
        let a1 = g.insert_node(alive, FxHashMap::default());
        let a2 = g.insert_node(alive, FxHashMap::default());
        let d1 = g.insert_node(cell, FxHashMap::default());
        g.insert_edge(me_node, adj, a1, FxHashMap::default())
            .unwrap();
        g.insert_edge(me_node, adj, a2, FxHashMap::default())
            .unwrap();
        g.insert_edge(me_node, adj, d1, FxHashMap::default())
            .unwrap();

        // Count(Filter(Neighbours(Var(me), 'adjacent_to'), n, Eq(TypeOf(Var n), Lit 'AliveCell')))
        let me = a.add(TermNode::Var { name: me_var });
        let nbrs = a.add(TermNode::Neighbours {
            node: me,
            edge_type: adj,
            any_type: false,
        });
        let n_var_t = a.add(TermNode::Var { name: n_var });
        let type_n = a.add(TermNode::TypeOf { node: n_var_t });
        let lit_alive = a.add(TermNode::Lit {
            value: Value::Str(alive),
        });
        let eq = a.add(TermNode::Eq {
            a: type_n,
            b: lit_alive,
        });
        let filt = a.add(TermNode::Filter {
            source: nbrs,
            var_name: n_var,
            predicate: eq,
        });
        let count = a.add(TermNode::Count { source: filt });

        let mut env: Env = smallvec![(me_var, Value::Node(me_node))];
        let mut ctx = EvalCtx::new(&g, &ir);
        assert_eq!(evaluate(&a, count, &mut env, &mut ctx), Value::Int(2));
    }

    #[test]
    fn ifthenelse_and_arithmetic() {
        let mut a = TermArena::new();
        let ir = Interner::new();
        let g = TypedGraph::new();

        // If 3 < 5 then 1+2 else 99
        let l3 = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let l5 = a.add(TermNode::Lit {
            value: Value::Int(5),
        });
        let lt = a.add(TermNode::Lt { a: l3, b: l5 });
        let l1 = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let l2 = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let plus = a.add(TermNode::Plus {
            items: vec![l1, l2],
        });
        let l99 = a.add(TermNode::Lit {
            value: Value::Int(99),
        });
        let ite = a.add(TermNode::IfThenElse {
            cond: lt,
            then: plus,
            other: l99,
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir);
        assert_eq!(evaluate(&a, ite, &mut env, &mut ctx), Value::Int(3));
    }

    #[test]
    fn neighbour_cache_returns_stable_set() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("Cell");
        let adj = ir.intern("adjacent_to");
        let me = ir.intern("me");
        let me_node = g.insert_node(t, FxHashMap::default());
        let p = g.insert_node(t, FxHashMap::default());
        g.insert_edge(me_node, adj, p, FxHashMap::default())
            .unwrap();

        let me_t = a.add(TermNode::Var { name: me });
        let nb = a.add(TermNode::Neighbours {
            node: me_t,
            edge_type: adj,
            any_type: false,
        });

        let mut env: Env = smallvec![(me, Value::Node(me_node))];
        let mut cache = EvalCache::default();
        let mut ctx = EvalCtx::new(&g, &ir).with_cache(&mut cache);
        let r1 = evaluate(&a, nb, &mut env, &mut ctx);
        let r2 = evaluate(&a, nb, &mut env, &mut ctx);
        assert_eq!(r1, r2);
        assert_eq!(r1.len(), 1);
    }

    #[test]
    fn filter_cache_keys_free_variables_from_its_source() {
        // Regression for busy-graph selector aliasing: the predicate is
        // constant, so the only free variable distinguishing the two Filter
        // evaluations occurs in Neighbours(Var(ctx), ...), the SOURCE.
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let context_t = ir.intern("Context");
        let candidate_t = ir.intern("Candidate");
        let has_candidate = ir.intern("has_candidate");
        let ctx_var = ir.intern("ctx");
        let option_var = ir.intern("option");

        let ctx_a = g.insert_node(context_t, FxHashMap::default());
        let ctx_b = g.insert_node(context_t, FxHashMap::default());
        let cand_a = g.insert_node(candidate_t, FxHashMap::default());
        let cand_b = g.insert_node(candidate_t, FxHashMap::default());
        g.insert_edge(ctx_a, has_candidate, cand_a, FxHashMap::default())
            .unwrap();
        g.insert_edge(ctx_b, has_candidate, cand_b, FxHashMap::default())
            .unwrap();

        let ctx = a.add(TermNode::Var { name: ctx_var });
        let neighbours = a.add(TermNode::Neighbours {
            node: ctx,
            edge_type: has_candidate,
            any_type: false,
        });
        let yes = a.add(TermNode::Lit {
            value: Value::Bool(true),
        });
        let filter = a.add(TermNode::Filter {
            source: neighbours,
            var_name: option_var,
            predicate: yes,
        });

        let mut cache = EvalCache::default();
        let mut env: Env = smallvec![(ctx_var, Value::Node(ctx_a))];
        let mut eval = EvalCtx::new(&g, &ir).with_cache(&mut cache);
        let from_a = evaluate(&a, filter, &mut env, &mut eval);
        env.pop();
        env.push((ctx_var, Value::Node(ctx_b)));
        let from_b = evaluate(&a, filter, &mut env, &mut eval);

        assert_eq!(from_a, Value::make_frozenset(vec![Value::Node(cand_a)]));
        assert_eq!(from_b, Value::make_frozenset(vec![Value::Node(cand_b)]));
        assert_eq!(eval.cache.as_ref().unwrap().filter.len(), 2);
    }

    #[test]
    fn holds_recurses_to_base_case() {
        // Define concept "is_zero(x) = Eq(x, 0); is_positive(x) = if is_zero(x) then 0 else 1"
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let x = ir.intern("x");
        let is_zero = ir.intern("is_zero");
        let is_positive = ir.intern("is_positive");

        let x_var = a.add(TermNode::Var { name: x });
        let zero = a.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let eq = a.add(TermNode::Eq { a: x_var, b: zero });
        let _ = is_zero; // is_zero definition is just `eq` Term

        // is_positive: if Holds(is_zero, x) then 0 else 1
        let holds = a.add(TermNode::Holds {
            concept: is_zero,
            node: Some(x_var),
            node2: None,
        });
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let ite = a.add(TermNode::IfThenElse {
            cond: holds,
            then: zero,
            other: one,
        });
        let _ = is_positive;

        let mut concepts: ConceptResolver = FxHashMap::default();
        concepts.insert(is_zero, eq);
        concepts.insert(is_positive, ite);

        let mut env: Env = smallvec![(x, Value::Int(5))];
        let mut ctx = EvalCtx::new(&g, &ir).with_concepts(&concepts);
        // Holds(is_positive, x=5) -> if Holds(is_zero, 5) then 0 else 1 -> if false then 0 else 1 -> 1
        let outer = a.add(TermNode::Holds {
            concept: is_positive,
            node: Some(x_var),
            node2: None,
        });
        assert_eq!(evaluate(&a, outer, &mut env, &mut ctx), Value::Int(1));
    }

    #[test]
    fn holds_cache_returns_same_value_on_repeat_call() {
        // Define `marks(node) = TypeOf(node) == 'Marked'`. Cache should
        // produce the same answer twice for the same Node arg.
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let marked_t = ir.intern("Marked");
        let unmarked_t = ir.intern("Unmarked");
        let marks = ir.intern("marks");
        let n_marked = g.insert_node(marked_t, FxHashMap::default());
        let n_unmarked = g.insert_node(unmarked_t, FxHashMap::default());

        // Concept body: TypeOf(Var("x")) == Lit("Marked").
        let x = ir.intern("x");
        let x_var = a.add(TermNode::Var { name: x });
        let type_x = a.add(TermNode::TypeOf { node: x_var });
        let lit_marked = a.add(TermNode::Lit {
            value: Value::Str(marked_t),
        });
        let body = a.add(TermNode::Eq {
            a: type_x,
            b: lit_marked,
        });

        let mut concepts: ConceptResolver = FxHashMap::default();
        concepts.insert(marks, body);

        let mut cache = EvalCache::default();
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir)
            .with_concepts(&concepts)
            .with_cache(&mut cache);

        let n_marked_lit = a.add(TermNode::Lit {
            value: Value::Node(n_marked),
        });
        let n_unmarked_lit = a.add(TermNode::Lit {
            value: Value::Node(n_unmarked),
        });
        let holds_marked = a.add(TermNode::Holds {
            concept: marks,
            node: Some(n_marked_lit),
            node2: None,
        });
        let holds_unmarked = a.add(TermNode::Holds {
            concept: marks,
            node: Some(n_unmarked_lit),
            node2: None,
        });

        // First call evaluates fully; second call hits the cache.
        assert_eq!(
            evaluate(&a, holds_marked, &mut env, &mut ctx),
            Value::Bool(true)
        );
        assert_eq!(
            evaluate(&a, holds_marked, &mut env, &mut ctx),
            Value::Bool(true)
        );
        assert_eq!(
            evaluate(&a, holds_unmarked, &mut env, &mut ctx),
            Value::Bool(false)
        );
        // Cache should now hold both entries.
        assert_eq!(ctx.cache.as_ref().unwrap().holds.len(), 2);
    }

    #[test]
    fn sum_over_set() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let n = ir.intern("n");
        // Sum(SetT(1, 2, 3), n, Var(n))  → 6
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let set = a.add(TermNode::SetT {
            items: vec![one, two, three],
        });
        let n_t = a.add(TermNode::Var { name: n });
        let sum = a.add(TermNode::Sum {
            source: set,
            var_name: n,
            value: n_t,
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir);
        assert_eq!(evaluate(&a, sum, &mut env, &mut ctx), Value::Int(6));
    }

    #[test]
    fn vec_magnitude_3_4_5() {
        let mut a = TermArena::new();
        let ir = Interner::new();
        let g = TypedGraph::new();
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let four = a.add(TermNode::Lit {
            value: Value::Int(4),
        });
        let vec = a.add(TermNode::Vec_ {
            items: vec![three, four],
        });
        let mag = a.add(TermNode::Magnitude { arg: vec });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir);
        assert_eq!(evaluate(&a, mag, &mut env, &mut ctx), Value::Float(5.0));
    }

    #[test]
    fn set_algebra_terms_work() {
        let mut a = TermArena::new();
        let mut i = Interner::new();
        let g = TypedGraph::new();
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let four = a.add(TermNode::Lit {
            value: Value::Int(4),
        });
        let s1 = a.add(TermNode::SetT {
            items: vec![one, two, three],
        });
        let s2 = a.add(TermNode::SetT {
            items: vec![two, three, four],
        });
        let union = a.add(TermNode::Union { a: s1, b: s2 });
        let inter = a.add(TermNode::Intersect { a: s1, b: s2 });
        let diff = a.add(TermNode::Difference { a: s1, b: s2 });
        // Pre-intern "n" before building ctx so the borrow stays immutable.
        let n_var = i.intern("n");
        let n_t = a.add(TermNode::Var { name: n_var });
        let sq = a.add(TermNode::Times {
            items: vec![n_t, n_t],
        });
        let mapset = a.add(TermNode::MapSet {
            source: s1,
            var_name: n_var,
            value: sq,
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &i);
        assert_eq!(
            evaluate(&a, union, &mut env, &mut ctx),
            Value::make_frozenset(vec![
                Value::Int(1),
                Value::Int(2),
                Value::Int(3),
                Value::Int(4)
            ])
        );
        assert_eq!(
            evaluate(&a, inter, &mut env, &mut ctx),
            Value::make_frozenset(vec![Value::Int(2), Value::Int(3)])
        );
        assert_eq!(
            evaluate(&a, diff, &mut env, &mut ctx),
            Value::make_frozenset(vec![Value::Int(1)])
        );
        // MapSet: {1,2,3} → {n*n : n in S} = {1,4,9}
        assert_eq!(
            evaluate(&a, mapset, &mut env, &mut ctx),
            Value::make_frozenset(vec![Value::Int(1), Value::Int(4), Value::Int(9)])
        );
    }

    #[test]
    fn edges_and_edgeattr_read_edge_attrs() {
        let mut arena = TermArena::new();
        let mut interner = Interner::new();
        let mut g = TypedGraph::new();
        let cell = interner.intern("Cell");
        let connects = interner.intern("connects");
        let weight = interner.intern("weight");
        let me_var = interner.intern("me");

        let a_node = g.insert_node(cell, FxHashMap::default());
        let b_node = g.insert_node(cell, FxHashMap::default());
        let c_node = g.insert_node(cell, FxHashMap::default());
        let mut e1_attrs = FxHashMap::default();
        e1_attrs.insert(weight, Value::Float(0.7));
        g.insert_edge(a_node, connects, b_node, e1_attrs).unwrap();
        let mut e2_attrs = FxHashMap::default();
        e2_attrs.insert(weight, Value::Float(0.3));
        g.insert_edge(a_node, connects, c_node, e2_attrs).unwrap();

        // Sum over edges of (me) of EdgeAttr(e, "weight") — total 1.0
        let me = arena.add(TermNode::Var { name: me_var });
        let edges = arena.add(TermNode::Edges {
            node: me,
            edge_type: connects,
            any_type: false,
        });
        let e_var = interner.intern("e");
        let e_t = arena.add(TermNode::Var { name: e_var });
        let ea = arena.add(TermNode::EdgeAttr {
            edge: e_t,
            key: weight,
        });
        let sum = arena.add(TermNode::Sum {
            source: edges,
            var_name: e_var,
            value: ea,
        });
        let mut env: Env = smallvec![(me_var, Value::Node(a_node))];
        let mut ctx = EvalCtx::new(&g, &interner);
        let r = evaluate(&arena, sum, &mut env, &mut ctx);
        // Total of edge weights is 0.7 + 0.3 = 1.0 (in Float since
        // Sum mixed-mode promotes).
        match r {
            Value::Float(f) => assert!((f - 1.0).abs() < 1e-9, "got {}", f),
            other => panic!("expected Float, got {:?}", other),
        }
    }

    #[test]
    fn free_vars_excludes_binder() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let x = ir.intern("x");
        let n = ir.intern("n");
        let x_t = a.add(TermNode::Var { name: x });
        let n_t = a.add(TermNode::Var { name: n });
        // Filter(Var(x), n, Eq(Var(n), Var(x)))  — free vars: {x}
        let eq = a.add(TermNode::Eq { a: n_t, b: x_t });
        let filt = a.add(TermNode::Filter {
            source: x_t,
            var_name: n,
            predicate: eq,
        });
        let fv = free_vars(&a, filt, None);
        assert_eq!(fv.as_slice(), &[x]);
    }

    // --- Phase B: Fold + Primitive-Concept dispatch ---

    #[test]
    fn fold_sum_matches_native_sum() {
        // Fold(SetT(1,2,3), e, acc, init=0, body=Plus(Var(acc), Var(e)))  → 6
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let e = ir.intern("e");
        let acc = ir.intern("acc");
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let set = a.add(TermNode::SetT {
            items: vec![one, two, three],
        });
        let acc_t = a.add(TermNode::Var { name: acc });
        let e_t = a.add(TermNode::Var { name: e });
        let init = a.add(TermNode::Lit {
            value: Value::Int(0),
        });
        let body = a.add(TermNode::Plus {
            items: vec![acc_t, e_t],
        });
        let fold = a.add(TermNode::Fold {
            source: set,
            var_name: e,
            acc_name: acc,
            init,
            body,
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir);
        assert_eq!(evaluate(&a, fold, &mut env, &mut ctx), Value::Int(6));
    }

    #[test]
    fn fold_empty_source_returns_init() {
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let e = ir.intern("e");
        let acc = ir.intern("acc");
        let empty = a.add(TermNode::SetT { items: vec![] });
        let acc_t = a.add(TermNode::Var { name: acc });
        let init = a.add(TermNode::Lit {
            value: Value::Int(42),
        });
        let fold = a.add(TermNode::Fold {
            source: empty,
            var_name: e,
            acc_name: acc,
            init,
            body: acc_t,
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir);
        assert_eq!(evaluate(&a, fold, &mut env, &mut ctx), Value::Int(42));
    }

    #[test]
    fn derivation_dispatch_gt_via_lt_b_a() {
        // Register Primitive[Gt] := Lt(Var(b), Var(a)).
        // Eval Gt(Lit 5, Lit 3) — should return Bool(true) via the
        // registered def, matching the native impl.
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let gt_sym = ir.intern("Gt");
        let a_sym = ir.intern("a");
        let b_sym = ir.intern("b");

        let a_var = a.add(TermNode::Var { name: a_sym });
        let b_var = a.add(TermNode::Var { name: b_sym });
        let lt_ba = a.add(TermNode::Lt { a: b_var, b: a_var });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(gt_sym, Derivation::ValueTaker(lt_ba));

        let l5 = a.add(TermNode::Lit {
            value: Value::Int(5),
        });
        let l3 = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let gt = a.add(TermNode::Gt { a: l5, b: l3 });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        let via_def = evaluate(&a, gt, &mut env, &mut ctx);

        // Now native (no primitives registered) — must agree.
        let mut ctx_native = EvalCtx::new(&g, &ir);
        let via_native = evaluate(&a, gt, &mut env, &mut ctx_native);

        assert_eq!(via_def, via_native);
        assert_eq!(via_def, Value::Bool(true));
    }

    #[test]
    fn derivation_dispatch_lte_via_or_lt_eq() {
        // Register Primitive[Lte] := Or(Lt(Var(a), Var(b)), Eq(Var(a), Var(b))).
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let lte_sym = ir.intern("Lte");
        let a_sym = ir.intern("a");
        let b_sym = ir.intern("b");

        let a_var = a.add(TermNode::Var { name: a_sym });
        let b_var = a.add(TermNode::Var { name: b_sym });
        let lt_ab = a.add(TermNode::Lt { a: a_var, b: b_var });
        let eq_ab = a.add(TermNode::Eq { a: a_var, b: b_var });
        let or = a.add(TermNode::Or {
            items: vec![lt_ab, eq_ab],
        });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(lte_sym, Derivation::ValueTaker(or));

        // Three cases: a<b, a==b, a>b.
        for (av, bv, expected) in [(3, 5, true), (5, 5, true), (7, 5, false)] {
            let la = a.add(TermNode::Lit {
                value: Value::Int(av),
            });
            let lb = a.add(TermNode::Lit {
                value: Value::Int(bv),
            });
            let lte = a.add(TermNode::Lte { a: la, b: lb });
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
            let via_def = evaluate(&a, lte, &mut env, &mut ctx);
            let mut ctx_native = EvalCtx::new(&g, &ir);
            let via_native = evaluate(&a, lte, &mut env, &mut ctx_native);
            assert_eq!(via_def, via_native, "({av}, {bv})");
            assert_eq!(via_def, Value::Bool(expected), "({av}, {bv})");
        }
    }

    #[test]
    fn derivation_dispatch_bearing_via_atan2_of_nth() {
        // Register Primitive[Bearing] := Atan2(Nth(Var(arg), 1), Nth(Var(arg), 0)).
        // Note: existing Nth signature is { items: Option<TermIdx>, index: i64 },
        // not a binary Term-tree, so we use Nth directly with arg as items.
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let bearing_sym = ir.intern("Bearing");
        let arg_sym = ir.intern("arg");

        let arg_var = a.add(TermNode::Var { name: arg_sym });
        let nth_y = a.add(TermNode::Nth {
            items: Some(arg_var),
            index: 1,
        });
        let nth_x = a.add(TermNode::Nth {
            items: Some(arg_var),
            index: 0,
        });
        let atan = a.add(TermNode::Atan2 { y: nth_y, x: nth_x });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(bearing_sym, Derivation::ValueTaker(atan));

        // Bearing((3.0, 4.0))  — should match atan2(4.0, 3.0).
        let x = a.add(TermNode::Lit {
            value: Value::Float(3.0),
        });
        let y = a.add(TermNode::Lit {
            value: Value::Float(4.0),
        });
        let vec = a.add(TermNode::Vec_ { items: vec![x, y] });
        let bearing = a.add(TermNode::Bearing { arg: vec });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        let via_def = evaluate(&a, bearing, &mut env, &mut ctx);
        let mut ctx_native = EvalCtx::new(&g, &ir);
        let via_native = evaluate(&a, bearing, &mut env, &mut ctx_native);

        match (via_def, via_native) {
            (Value::Float(d), Value::Float(n)) => {
                assert!((d - n).abs() < 1e-12, "def={} native={}", d, n);
                assert!((d - 4.0_f64.atan2(3.0)).abs() < 1e-12);
            }
            other => panic!("expected Float pair, got {:?}", other),
        }
    }

    #[test]
    fn derivation_registry_empty_falls_through_to_native() {
        // No derivations registered → every dispatch falls through to
        // the native arm; behaviour is identical to ctx-without-derivations.
        let mut a = TermArena::new();
        let ir = Interner::new();
        let g = TypedGraph::new();
        let l5 = a.add(TermNode::Lit {
            value: Value::Int(5),
        });
        let l3 = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let gt = a.add(TermNode::Gt { a: l5, b: l3 });

        let derivs: DerivationRegistry = FxHashMap::default();
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        assert_eq!(evaluate(&a, gt, &mut env, &mut ctx), Value::Bool(true));
    }

    #[test]
    fn derivation_dispatch_in_via_exists() {
        // In(member, container) := Exists(container, "_e",
        //                                  Eq(Var("_e"), Var("member")))
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let in_sym = ir.intern("In");
        let member_sym = ir.intern("member");
        let container_sym = ir.intern("container");
        let e_sym = ir.intern("_e");

        let member_var = a.add(TermNode::Var { name: member_sym });
        let container_var = a.add(TermNode::Var {
            name: container_sym,
        });
        let e_var = a.add(TermNode::Var { name: e_sym });
        let eq = a.add(TermNode::Eq {
            a: e_var,
            b: member_var,
        });
        let exists = a.add(TermNode::Exists {
            source: container_var,
            var_name: e_sym,
            predicate: eq,
        });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(in_sym, Derivation::ValueTaker(exists));

        let l2 = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let l9 = a.add(TermNode::Lit {
            value: Value::Int(9),
        });
        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let set = a.add(TermNode::SetT {
            items: vec![one, two, three],
        });

        for (m, expected) in [(l2, true), (l9, false)] {
            let in_t = a.add(TermNode::In {
                member: m,
                container: set,
            });
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
            let via_def = evaluate(&a, in_t, &mut env, &mut ctx);
            let mut ctx_native = EvalCtx::new(&g, &ir);
            let via_native = evaluate(&a, in_t, &mut env, &mut ctx_native);
            assert_eq!(via_def, via_native);
            assert_eq!(via_def, Value::Bool(expected));
        }
    }

    #[test]
    fn derivation_dispatch_magnitude_via_sqrt_dot() {
        // Magnitude(arg) := Sqrt(Dot(Var("arg"), Var("arg")))
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let mag_sym = ir.intern("Magnitude");
        let arg_sym = ir.intern("arg");

        let arg_var = a.add(TermNode::Var { name: arg_sym });
        let dot = a.add(TermNode::Dot {
            a: arg_var,
            b: arg_var,
        });
        let sqrt = a.add(TermNode::Sqrt { arg: dot });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(mag_sym, Derivation::ValueTaker(sqrt));

        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let four = a.add(TermNode::Lit {
            value: Value::Int(4),
        });
        let vec = a.add(TermNode::Vec_ {
            items: vec![three, four],
        });
        let mag = a.add(TermNode::Magnitude { arg: vec });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        let via_def = evaluate(&a, mag, &mut env, &mut ctx);
        let mut ctx_native = EvalCtx::new(&g, &ir);
        let via_native = evaluate(&a, mag, &mut env, &mut ctx_native);

        match (via_def, via_native) {
            (Value::Float(d), Value::Float(n)) => {
                assert!((d - n).abs() < 1e-12);
                assert!((d - 5.0).abs() < 1e-12);
            }
            other => panic!("expected Float pair, got {:?}", other),
        }
    }

    #[test]
    fn derivation_dispatch_angle_between_via_atan2_cross_dot() {
        // AngleBetween(a, b) := Atan2(Minus(Times(Nth(a,0), Nth(b,1)),
        //                                   Times(Nth(a,1), Nth(b,0))),
        //                              Dot(Var("a"), Var("b")))
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let ab_sym = ir.intern("AngleBetween");
        let a_sym = ir.intern("a");
        let b_sym = ir.intern("b");

        let a_var = a.add(TermNode::Var { name: a_sym });
        let b_var = a.add(TermNode::Var { name: b_sym });
        let a0 = a.add(TermNode::Nth {
            items: Some(a_var),
            index: 0,
        });
        let a1 = a.add(TermNode::Nth {
            items: Some(a_var),
            index: 1,
        });
        let b0 = a.add(TermNode::Nth {
            items: Some(b_var),
            index: 0,
        });
        let b1 = a.add(TermNode::Nth {
            items: Some(b_var),
            index: 1,
        });
        let a0b1 = a.add(TermNode::Times {
            items: vec![a0, b1],
        });
        let a1b0 = a.add(TermNode::Times {
            items: vec![a1, b0],
        });
        let cross = a.add(TermNode::Minus { a: a0b1, b: a1b0 });
        let dot = a.add(TermNode::Dot { a: a_var, b: b_var });
        let atan = a.add(TermNode::Atan2 { y: cross, x: dot });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(ab_sym, Derivation::ValueTaker(atan));

        // a = (1, 0), b = (0, 1) → angle = π/2.
        let one = a.add(TermNode::Lit {
            value: Value::Float(1.0),
        });
        let zero = a.add(TermNode::Lit {
            value: Value::Float(0.0),
        });
        let va = a.add(TermNode::Vec_ {
            items: vec![one, zero],
        });
        let vb = a.add(TermNode::Vec_ {
            items: vec![zero, one],
        });
        let ab = a.add(TermNode::AngleBetween { a: va, b: vb });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        let via_def = evaluate(&a, ab, &mut env, &mut ctx);
        let mut ctx_native = EvalCtx::new(&g, &ir);
        let via_native = evaluate(&a, ab, &mut env, &mut ctx_native);

        match (via_def, via_native) {
            (Value::Float(d), Value::Float(n)) => {
                assert!((d - n).abs() < 1e-12, "def={} native={}", d, n);
                assert!((d - std::f64::consts::FRAC_PI_2).abs() < 1e-12);
            }
            other => panic!("expected Float pair, got {:?}", other),
        }
    }

    #[test]
    fn derivation_dispatch_intersect_via_filter_in() {
        // Intersect(a, b) := Filter(a, "_e", In(Var("_e"), Var("b")))
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let intersect_sym = ir.intern("Intersect");
        let a_sym = ir.intern("a");
        let b_sym = ir.intern("b");
        let e_sym = ir.intern("_e");

        let a_var = a.add(TermNode::Var { name: a_sym });
        let b_var = a.add(TermNode::Var { name: b_sym });
        let e_var = a.add(TermNode::Var { name: e_sym });
        let in_e = a.add(TermNode::In {
            member: e_var,
            container: b_var,
        });
        let filt = a.add(TermNode::Filter {
            source: a_var,
            var_name: e_sym,
            predicate: in_e,
        });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(intersect_sym, Derivation::ValueTaker(filt));

        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let four = a.add(TermNode::Lit {
            value: Value::Int(4),
        });
        let set_a = a.add(TermNode::SetT {
            items: vec![one, two, three],
        });
        let set_b = a.add(TermNode::SetT {
            items: vec![two, three, four],
        });
        let inter = a.add(TermNode::Intersect { a: set_a, b: set_b });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        let via_def = evaluate(&a, inter, &mut env, &mut ctx);
        let mut ctx_native = EvalCtx::new(&g, &ir);
        let via_native = evaluate(&a, inter, &mut env, &mut ctx_native);

        assert_eq!(via_def, via_native);
        // Both should be {2, 3}.
        let items: Vec<i64> = via_def
            .iter()
            .filter_map(|v| match v {
                Value::Int(n) => Some(*n),
                _ => None,
            })
            .collect();
        let mut sorted = items.clone();
        sorted.sort();
        assert_eq!(sorted, vec![2, 3]);
    }

    #[test]
    fn derivation_dispatch_difference_via_filter_not_in() {
        // Difference(a, b) := Filter(a, "_e", Not(In(Var("_e"), Var("b"))))
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let diff_sym = ir.intern("Difference");
        let a_sym = ir.intern("a");
        let b_sym = ir.intern("b");
        let e_sym = ir.intern("_e");

        let a_var = a.add(TermNode::Var { name: a_sym });
        let b_var = a.add(TermNode::Var { name: b_sym });
        let e_var = a.add(TermNode::Var { name: e_sym });
        let in_e = a.add(TermNode::In {
            member: e_var,
            container: b_var,
        });
        let not_in = a.add(TermNode::Not { arg: in_e });
        let filt = a.add(TermNode::Filter {
            source: a_var,
            var_name: e_sym,
            predicate: not_in,
        });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(diff_sym, Derivation::ValueTaker(filt));

        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let four = a.add(TermNode::Lit {
            value: Value::Int(4),
        });
        let set_a = a.add(TermNode::SetT {
            items: vec![one, two, three],
        });
        let set_b = a.add(TermNode::SetT {
            items: vec![two, three, four],
        });
        let diff = a.add(TermNode::Difference { a: set_a, b: set_b });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        let via_def = evaluate(&a, diff, &mut env, &mut ctx);
        let mut ctx_native = EvalCtx::new(&g, &ir);
        let via_native = evaluate(&a, diff, &mut env, &mut ctx_native);

        assert_eq!(via_def, via_native);
        let items: Vec<i64> = via_def
            .iter()
            .filter_map(|v| match v {
                Value::Int(n) => Some(*n),
                _ => None,
            })
            .collect();
        assert_eq!(items, vec![1]);
    }

    #[test]
    fn body_taker_count_via_expansion() {
        // Count is a body-taker (source is a Term). The evaluator runs
        // `expand_count`, producing Fold(source, "_e", "_acc", Lit(0),
        // Plus(Var("_acc"), Lit(1))). Must match native Count = len.
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let count_sym = ir.intern("Count");
        ir.intern("_e");
        ir.intern("_acc");

        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let four = a.add(TermNode::Lit {
            value: Value::Int(4),
        });
        let set = a.add(TermNode::SetT {
            items: vec![one, two, three, four],
        });
        let cnt = a.add(TermNode::Count { source: set });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(count_sym, Derivation::BodyTaker);

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        let via_expansion = evaluate(&a, cnt, &mut env, &mut ctx);
        let mut ctx_native = EvalCtx::new(&g, &ir);
        let via_native = evaluate(&a, cnt, &mut env, &mut ctx_native);

        assert_eq!(via_expansion, via_native);
        assert_eq!(via_expansion, Value::Int(4));
    }

    #[test]
    fn body_taker_sum_via_expansion_with_complex_body() {
        // Sum(SetT(1,2,3), n, Times(Var(n), Var(n))) = 1+4+9 = 14.
        // The body Term `Times(Var(n), Var(n))` gets deep-copied + spliced
        // into the Fold via expand_sum. Parity proves copy_subtree handles
        // the user's body unchanged.
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let sum_sym = ir.intern("Sum");
        let n_sym = ir.intern("n");
        ir.intern("_acc");

        let one = a.add(TermNode::Lit {
            value: Value::Int(1),
        });
        let two = a.add(TermNode::Lit {
            value: Value::Int(2),
        });
        let three = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let set = a.add(TermNode::SetT {
            items: vec![one, two, three],
        });
        let n_var = a.add(TermNode::Var { name: n_sym });
        let n_sq = a.add(TermNode::Times {
            items: vec![n_var, n_var],
        });
        let sum = a.add(TermNode::Sum {
            source: set,
            var_name: n_sym,
            value: n_sq,
        });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(sum_sym, Derivation::BodyTaker);

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
        let via_expansion = evaluate(&a, sum, &mut env, &mut ctx);
        let mut ctx_native = EvalCtx::new(&g, &ir);
        let via_native = evaluate(&a, sum, &mut env, &mut ctx_native);

        assert_eq!(via_expansion, via_native);
        assert_eq!(via_expansion, Value::Int(14));
    }

    #[test]
    fn derivations_are_dynamic_install_then_remove() {
        // Dynamic property: install an (intentionally wrong) derivation,
        // observe the def is dispatched. Remove it, observe the native
        // arm runs again. The agent installing / removing between
        // evaluations IS the whole pattern; this proves the registry
        // is not baked in at startup.
        let mut a = TermArena::new();
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let gt_sym = ir.intern("Gt");
        let a_sym = ir.intern("a");
        let b_sym = ir.intern("b");

        // Intentionally-wrong derivation: Gt := Lt(a, b). Returns the
        // OPPOSITE result vs. native; if we get the "wrong" answer the
        // dispatch went through the derivation as intended.
        let a_var = a.add(TermNode::Var { name: a_sym });
        let b_var = a.add(TermNode::Var { name: b_sym });
        let wrong = a.add(TermNode::Lt { a: a_var, b: b_var });

        let mut derivs: DerivationRegistry = FxHashMap::default();
        derivs.insert(gt_sym, Derivation::ValueTaker(wrong));

        let l5 = a.add(TermNode::Lit {
            value: Value::Int(5),
        });
        let l3 = a.add(TermNode::Lit {
            value: Value::Int(3),
        });
        let gt = a.add(TermNode::Gt { a: l5, b: l3 });

        // With derivation installed: dispatches to Lt(5,3) = false.
        {
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
            assert_eq!(evaluate(&a, gt, &mut env, &mut ctx), Value::Bool(false));
        }
        // Remove the derivation → native dispatches → Gt(5,3) = true.
        derivs.remove(&gt_sym);
        {
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&g, &ir).with_derivations(&derivs);
            assert_eq!(evaluate(&a, gt, &mut env, &mut ctx), Value::Bool(true));
        }
    }

    // ------------------------------------------------------------------
    // GRAPH LAW #6: trans-frame identity — `track_identity_correspondence`
    // (the pure matching core) + the `TrackIdentityCorrespondence` Term.
    // See tests/test_trans_frame_identity.py for the Python-side proof
    // (non-visual domain: N-dim feature-space entities, no pixels).
    // ------------------------------------------------------------------

    fn mk_node(
        g: &mut TypedGraph,
        ir: &mut Interner,
        ty: &str,
        feat: Vec<f64>,
        cat: Option<i64>,
    ) -> NodeID {
        let t = ir.intern(ty);
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        let fk = ir.intern("feat");
        let feats: SmallVec<[Value; 4]> = feat.into_iter().map(Value::Float).collect();
        attrs.insert(fk, Value::Tuple(Arc::new(feats)));
        if let Some(c) = cat {
            let ck = ir.intern("cat");
            attrs.insert(ck, Value::Int(c));
        }
        g.insert_node(t, attrs)
    }

    #[test]
    fn track_identity_matches_nearest_within_radius() {
        let mut g = TypedGraph::new();
        let mut ir = Interner::new();
        let p0 = mk_node(&mut g, &mut ir, "Entity", vec![0.0, 0.0], None);
        let p1 = mk_node(&mut g, &mut ir, "Entity", vec![10.0, 10.0], None);
        // c0 is close to p0 (dist ~0.14), c1 close to p1 (dist ~0.14).
        let c0 = mk_node(&mut g, &mut ir, "Entity", vec![0.1, 0.1], None);
        let c1 = mk_node(&mut g, &mut ir, "Entity", vec![10.1, 10.1], None);
        let feat_key = ir.intern("feat");
        let m = track_identity_correspondence(&g, &[p0, p1], &[c0, c1], feat_key, None, None, 1.0);
        assert_eq!(m.matched.len(), 2);
        assert!(m.matched.contains(&(p0, c0)));
        assert!(m.matched.contains(&(p1, c1)));
        assert!(m.births.is_empty());
        assert!(m.deaths.is_empty());
    }

    #[test]
    fn track_identity_births_when_beyond_radius() {
        let mut g = TypedGraph::new();
        let mut ir = Interner::new();
        let p0 = mk_node(&mut g, &mut ir, "Entity", vec![0.0, 0.0], None);
        // c0 is 100 units away — far beyond any reasonable radius.
        let c0 = mk_node(&mut g, &mut ir, "Entity", vec![100.0, 100.0], None);
        let feat_key = ir.intern("feat");
        let m = track_identity_correspondence(&g, &[p0], &[c0], feat_key, None, None, 1.0);
        assert!(m.matched.is_empty());
        assert_eq!(m.births, vec![c0]);
        assert_eq!(m.deaths, vec![p0]);
    }

    #[test]
    fn track_identity_death_for_unmatched_prev() {
        let mut g = TypedGraph::new();
        let mut ir = Interner::new();
        let p0 = mk_node(&mut g, &mut ir, "Entity", vec![0.0, 0.0], None);
        let p1 = mk_node(&mut g, &mut ir, "Entity", vec![5.0, 5.0], None);
        // Only ONE cur item, close to p0. p1 has no match this frame.
        let c0 = mk_node(&mut g, &mut ir, "Entity", vec![0.05, 0.05], None);
        let feat_key = ir.intern("feat");
        let m = track_identity_correspondence(&g, &[p0, p1], &[c0], feat_key, None, None, 1.0);
        assert_eq!(m.matched, vec![(p0, c0)]);
        assert!(m.births.is_empty());
        assert_eq!(m.deaths, vec![p1]);
    }

    #[test]
    fn track_identity_category_gate_forces_birth() {
        // p0 is numerically closer to c0 than any radius would exclude,
        // but a DIFFERENT category — the gate must block the match even
        // though the bare distance would otherwise accept it.
        let mut g = TypedGraph::new();
        let mut ir = Interner::new();
        let p0 = mk_node(&mut g, &mut ir, "Entity", vec![0.0, 0.0], Some(1));
        let c0 = mk_node(&mut g, &mut ir, "Entity", vec![0.01, 0.01], Some(2));
        let feat_key = ir.intern("feat");
        let cat_key = ir.intern("cat");
        let m = track_identity_correspondence(&g, &[p0], &[c0], feat_key, Some(cat_key), None, 5.0);
        assert!(m.matched.is_empty());
        assert_eq!(m.births, vec![c0]);
        assert_eq!(m.deaths, vec![p0]);
    }

    #[test]
    fn track_identity_ndim_feature_space() {
        // 5-dimensional feature vectors — proves the matching is NOT
        // hardcoded to 2D pixel centroids.
        let mut g = TypedGraph::new();
        let mut ir = Interner::new();
        let p0 = mk_node(
            &mut g,
            &mut ir,
            "Entity",
            vec![1.0, 2.0, 3.0, 4.0, 5.0],
            None,
        );
        let p1 = mk_node(
            &mut g,
            &mut ir,
            "Entity",
            vec![-1.0, -2.0, -3.0, -4.0, -5.0],
            None,
        );
        let c0 = mk_node(
            &mut g,
            &mut ir,
            "Entity",
            vec![1.1, 2.1, 3.1, 3.9, 5.1],
            None,
        );
        let feat_key = ir.intern("feat");
        let m = track_identity_correspondence(&g, &[p0, p1], &[c0], feat_key, None, None, 1.0);
        assert_eq!(m.matched, vec![(p0, c0)]);
        assert_eq!(m.deaths, vec![p1]);
    }

    #[test]
    fn track_identity_extent_overlap_wins_over_distance() {
        // c0's nearest-CENTROID prior is p1 (closer in feature space),
        // but c0 shares extent members with p0 -- the overlap-first
        // pass must pick p0, exactly mirroring segment_and_track's
        // cell-overlap-before-centroid rule.
        let mut g = TypedGraph::new();
        let mut ir = Interner::new();
        let feat_key = ir.intern("feat");
        let extent_key = ir.intern("extent");
        let ty = ir.intern("Entity");

        let mut p0_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        p0_attrs.insert(
            feat_key,
            Value::Tuple(Arc::new(smallvec![Value::Float(0.0), Value::Float(0.0)])),
        );
        p0_attrs.insert(
            extent_key,
            Value::make_frozenset(vec![Value::Int(1), Value::Int(2), Value::Int(3)]),
        );
        let p0 = g.insert_node(ty, p0_attrs);

        let mut p1_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        // p1 is numerically CLOSER to c0 than p0 is.
        p1_attrs.insert(
            feat_key,
            Value::Tuple(Arc::new(smallvec![Value::Float(0.2), Value::Float(0.2)])),
        );
        p1_attrs.insert(
            extent_key,
            Value::make_frozenset(vec![Value::Int(9), Value::Int(8)]),
        );
        let p1 = g.insert_node(ty, p1_attrs);

        let mut c0_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        c0_attrs.insert(
            feat_key,
            Value::Tuple(Arc::new(smallvec![Value::Float(5.0), Value::Float(5.0)])),
        );
        c0_attrs.insert(
            extent_key,
            Value::make_frozenset(vec![Value::Int(1), Value::Int(2)]),
        );
        let c0 = g.insert_node(ty, c0_attrs);

        // Huge radius so the distance-fallback alone would also match
        // SOMETHING — the assertion is about WHICH prior wins, not
        // whether a match happens at all.
        let m = track_identity_correspondence(
            &g,
            &[p0, p1],
            &[c0],
            feat_key,
            None,
            Some(extent_key),
            100.0,
        );
        assert_eq!(m.matched, vec![(p0, c0)]);
    }

    /// P0 ON A STRING IS A CATEGORY ERROR, AND IT IS NOW COUNTABLE.
    ///
    /// `P0(node, key)` is `Plus(Attr(node, key), 0.0)`. Two cases used to be
    /// indistinguishable, both landing in `numeric_variadic`'s `_ => {}`:
    ///
    ///   * the attr is MISSING  -> Value::None -> 0. The absence idiom. Silent.
    ///   * the attr is a STRING -> skipped     -> 0. A category error, invisible.
    ///
    /// The second one compares FALSE forever against any real string term,
    /// which is how the F-16 reflex index silently took the "varied" branch on
    /// a byte-identical program (16 shapes, every run 1, epoch 0).
    ///
    /// This asserts BOTH halves: the value is unchanged in both cases (so every
    /// existing seed stays byte-identical), and only the string bumps the
    /// counter.
    #[test]
    fn p0_on_a_string_is_counted_and_absence_is_not() {
        let mut a = TermArena::new();
        let mut g = TypedGraph::new();
        let mut ir = Interner::new();

        let ty = ir.intern("GaitAttractor");
        let name_key = ir.intern("name");
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(
            name_key,
            Value::Surface(SurfaceKind::Text, Arc::from(&b"walking"[..])),
        );
        let node = g.insert_node(ty, attrs);

        let missing_key = ir.intern("ordinal");
        let zero = a.add(TermNode::Lit {
            value: Value::Float(0.0),
        });
        let node_lit = a.add(TermNode::Lit {
            value: Value::Node(node),
        });

        // P0(node, "ordinal") -- the attr is ABSENT.
        let absent_attr = a.add(TermNode::Attr {
            node: node_lit,
            key: missing_key,
        });
        let p0_absent = a.add(TermNode::Plus {
            items: vec![absent_attr, zero],
        });

        // P0(node, "name") -- the attr is PRESENT and is a String.
        let string_attr = a.add(TermNode::Attr {
            node: node_lit,
            key: name_key,
        });
        let p0_string = a.add(TermNode::Plus {
            items: vec![string_attr, zero],
        });

        // --- absence: yields 0, counts NOTHING ---
        let mut counters = crate::ext::Counters::new();
        {
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&g, &ir).with_counters(&mut counters);
            let out = evaluate(&a, p0_absent, &mut env, &mut ctx);
            assert_eq!(out.as_f64(), 0.0, "absent attr must still read 0");
        }
        assert_eq!(
            counters.numeric_op_non_numeric_operand, 0,
            "a MISSING attr is the absence idiom working -- it must stay silent",
        );

        // --- present string: same value, but COUNTED ---
        let mut counters = crate::ext::Counters::new();
        let string_value = {
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&g, &ir).with_counters(&mut counters);
            evaluate(&a, p0_string, &mut env, &mut ctx)
        };
        assert_eq!(
            string_value.as_f64(),
            0.0,
            "value semantics UNCHANGED: a present string still contributes the \
             identity, so every existing seed is byte-identical",
        );
        assert_eq!(
            counters.numeric_op_non_numeric_operand, 1,
            "a PRESENT string read through a numeric idiom must be countable",
        );
    }

    #[test]
    fn track_identity_correspondence_term_evaluates() {
        let mut a = TermArena::new();
        let mut g = TypedGraph::new();
        let mut ir = Interner::new();
        let p0 = mk_node(&mut g, &mut ir, "Entity", vec![0.0, 0.0], None);
        let c0 = mk_node(&mut g, &mut ir, "Entity", vec![0.1, 0.1], None);
        let c1 = mk_node(&mut g, &mut ir, "Entity", vec![50.0, 50.0], None);
        let feat_key = ir.intern("feat");

        let prev = a.add(TermNode::Lit {
            value: Value::make_frozenset(vec![Value::Node(p0)]),
        });
        let cur = a.add(TermNode::Lit {
            value: Value::make_frozenset(vec![Value::Node(c0), Value::Node(c1)]),
        });
        let radius = a.add(TermNode::Lit {
            value: Value::Float(1.0),
        });
        let term = a.add(TermNode::TrackIdentityCorrespondence {
            prev,
            cur,
            feature_key: feat_key,
            category_key: None,
            extent_key: None,
            radius,
        });

        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&g, &ir);
        let out = evaluate(&a, term, &mut env, &mut ctx);
        let Value::Dict(pairs) = out else {
            panic!("expected Dict, got {:?}", out)
        };
        let get = |k: &str| -> &Value {
            let key = Value::Surface(SurfaceKind::Text, Arc::from(k.as_bytes()));
            &pairs
                .iter()
                .find(|(pk, _)| *pk == key)
                .expect("key present")
                .1
        };
        let (Value::Tuple(matched) | Value::List(matched)) = get("matched") else {
            panic!("expected Tuple")
        };
        assert_eq!(matched.len(), 1);
        let (Value::Tuple(pair) | Value::List(pair)) = &matched[0] else {
            panic!("expected pair Tuple")
        };
        assert_eq!(pair[0], Value::Node(p0));
        assert_eq!(pair[1], Value::Node(c0));
        let (Value::Tuple(births) | Value::List(births)) = get("births") else {
            panic!("expected Tuple")
        };
        assert_eq!(births.to_vec(), vec![Value::Node(c1)]);
        let (Value::Tuple(deaths) | Value::List(deaths)) = get("deaths") else {
            panic!("expected Tuple")
        };
        assert!(deaths.is_empty());

        // Read-only: evaluating the Term must not have mutated the graph
        // (no new nodes, no identity attr written anywhere).
        assert_eq!(g.node(p0).attrs.get(&feat_key).is_some(), true);
        assert!(g.node(p0).attrs.iter().all(|(k, _)| *k == feat_key));
    }
}

fn first_morph_boundary(s: &str) -> Option<(usize, usize)> {
    let mut prev: Option<char> = None;
    for (i, c) in s.char_indices() {
        if c == '-' || c == '_' {
            // Separator boundary: the separator is dropped; skip any leading
            // run of separators so the tail starts at the next real character.
            let tail_start = s[i..]
                .char_indices()
                .find(|(_, ch)| *ch != '-' && *ch != '_')
                .map(|(j, _)| i + j)
                .unwrap_or_else(|| s.len());
            return Some((i, tail_start));
        }
        if let Some(p) = prev {
            // camelCase boundary: lowercase/digit immediately followed by an
            // uppercase. The uppercase is KEPT, so head ends and tail starts
            // at the same byte (the uppercase char).
            if (p.is_lowercase() || p.is_ascii_digit()) && c.is_uppercase() {
                return Some((i, i));
            }
        }
        prev = Some(c);
    }
    None
}

fn deform_gen(a: &Value, b: &Value) -> f64 {
    let mut q: Vec<f64> = Vec::new();
    for frame in a.iter() {
        for x in frame.iter() {
            q.push(x.as_f64());
        }
    }
    let d = q.len();
    let bf: Vec<f64> = b.iter().map(|x| x.as_f64()).collect();
    if d == 0 || bf.len() <= d {
        return f64::INFINITY;
    }
    let m = (bf.len() - d) / (d + 1);
    if m == 0 || bf.len() != d + m * d + m {
        return f64::INFINITY;
    }
    let mean = &bf[0..d];
    let modes = &bf[d..d + m * d];
    let inv_var = &bf[d + m * d..d + m * d + m];
    let mut diff: Vec<f64> = Vec::with_capacity(d);
    for c in 0..d {
        diff.push(q[c] - mean[c]);
    }
    let mut aug: Vec<Vec<f64>> = vec![vec![0.0; m + 1]; m];
    for i in 0..m {
        for j in 0..m {
            let mut s = 0.0;
            for c in 0..d {
                s += modes[i * d + c] * modes[j * d + c];
            }
            if i == j {
                s += inv_var[i];
            }
            aug[i][j] = s;
        }
        let mut r = 0.0;
        for c in 0..d {
            r += modes[i * d + c] * diff[c];
        }
        aug[i][m] = r;
    }
    for col in 0..m {
        let mut pivot_row = col;
        let mut best = aug[col][col].abs();
        for r in (col + 1)..m {
            if aug[r][col].abs() > best {
                best = aug[r][col].abs();
                pivot_row = r;
            }
        }
        if aug[pivot_row][col].abs() < 1e-12 {
            return f64::INFINITY;
        }
        if pivot_row != col {
            aug.swap(pivot_row, col);
        }
        let pivot = aug[col][col];
        for j in col..=m {
            aug[col][j] /= pivot;
        }
        for r in 0..m {
            if r != col {
                let factor = aug[r][col];
                if factor != 0.0 {
                    for j in col..=m {
                        aug[r][j] -= factor * aug[col][j];
                    }
                }
            }
        }
    }
    let mut coeff: Vec<f64> = vec![0.0; m];
    for i in 0..m {
        coeff[i] = aug[i][m];
    }
    let mut residual = 0.0;
    for c in 0..d {
        let mut recon = mean[c];
        for j in 0..m {
            recon += modes[j * d + c] * coeff[j];
        }
        let e = q[c] - recon;
        residual += e * e;
    }
    for j in 0..m {
        residual += inv_var[j] * coeff[j] * coeff[j];
    }
    (residual.max(0.0) / d as f64).sqrt()
}

fn deform_gen_marginal(a: &Value, b: &Value) -> f64 {
    let mut q: Vec<f64> = Vec::new();
    for frame in a.iter() {
        for x in frame.iter() {
            q.push(x.as_f64());
        }
    }
    let d = q.len();
    let bf: Vec<f64> = b.iter().map(|x| x.as_f64()).collect();
    if d == 0 || bf.len() <= d {
        return f64::INFINITY;
    }
    let m = (bf.len() - d) / (d + 1);
    if m == 0 || bf.len() != d + m * d + m {
        return f64::INFINITY;
    }
    let mean = &bf[0..d];
    let modes = &bf[d..d + m * d];
    let inv_var = &bf[d + m * d..d + m * d + m];

    let mut mat = vec![vec![0.0f64; m]; m];
    let mut rhs = vec![0.0f64; m];
    for j in 0..m {
        for k in 0..m {
            let mut s = 0.0;
            for c in 0..d {
                s += modes[j * d + c] * modes[k * d + c];
            }
            if j == k {
                s += inv_var[j];
            }
            mat[j][k] = s;
        }
        let mut r = 0.0;
        for c in 0..d {
            r += modes[j * d + c] * (q[c] - mean[c]);
        }
        rhs[j] = r;
    }

    let mut logdet = 0.0f64;
    for i in 0..m {
        let pivot = mat[i][i];
        if pivot.abs() < 1e-12 {
            return f64::INFINITY;
        }
        logdet += pivot.ln();
        let inv = 1.0 / pivot;
        for k in 0..m {
            mat[i][k] *= inv;
        }
        rhs[i] *= inv;
        for r in 0..m {
            if r != i {
                let factor = mat[r][i];
                if factor != 0.0 {
                    for k in 0..m {
                        mat[r][k] -= factor * mat[i][k];
                    }
                    rhs[r] -= factor * rhs[i];
                }
            }
        }
    }
    let coeff = rhs;

    let mut resid = 0.0f64;
    for c in 0..d {
        let mut rc = mean[c];
        for j in 0..m {
            rc += modes[j * d + c] * coeff[j];
        }
        let diff = q[c] - rc;
        resid += diff * diff;
    }
    for j in 0..m {
        resid += inv_var[j] * coeff[j] * coeff[j];
    }

    ((resid + logdet.max(0.0)).max(0.0) / d as f64).sqrt()
}
