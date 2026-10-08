//! `ShapeDecode` — the dequantization primitive.
//!
//! Rust port of `domains/reflective_faculty.py::compose_design_for_goal`
//! (the beam-search shape composer) + its helpers `_load_shape_signatures`,
//! `_shared_shape`, `_covers_relation`, `_score_part_for_residual`. The
//! algorithm here must reproduce that Python function EXACTLY — parity
//! tests in this crate and (eventually) a thin Python shim depend on it
//! field-for-field.
//!
//! Scoring reuses the crate-internal `anti_unify_values` / `covers_value` /
//! `fixed_count_value` routines (widened to `pub(crate)` in `term.rs`) —
//! the same functions that back the `AntiUnify` / `FixedCount` / `Covers`
//! Terms. No duplicated matcher logic.
//!
//! ## The interner constraint (read before touching this file)
//!
//! `EvalCtx::interner` is `&Interner` — evaluation never mutates the
//! interner. But a `ShapeSignature` node's `signature` attr may be stored
//! as a JSON-string blob (the whole text interned as ONE Sym at node
//! insertion time), and DECODING that text into a relation-system means
//! interning each embedded predicate/argument string separately — which
//! would need `&mut Interner`.
//!
//! Resolution: `goal` always evaluates through the ordinary Term
//! evaluator, so every Str leaf it produces is a REAL Sym (interned
//! properly, at Term-parse time or at whatever earlier point the node
//! attr was written) — safe to place directly in the output (`covered`/
//! `residual`/`goal_relations`). A part's JSON-string `signature`, by
//! contrast, is parsed HERE via `json_to_value_scoped`, which resolves
//! each leaf string by `Interner::lookup` first (finds the REAL Sym if
//! the string was interned anywhere else already — which it must have
//! been, for it to ever match anything in `goal`) and only fabricates a
//! LOCAL placeholder Sym (a high id, scoped to one `extra` map for the
//! whole `ShapeDecode` call) for strings truly novel to this graph. Parsed
//! part-signature content is used ONLY for internal scoring (fed into the
//! matcher routines above) and is NEVER placed in the output — so a
//! fabricated placeholder Sym never reaches `interner.resolve` (which
//! would panic on it). Output strings we construct ourselves (dict keys,
//! the `why` text) sidestep interning entirely via `Value::Surface(Text,
//! ..)`, which `value_to_py` renders straight to a Python `str` without
//! touching the interner.

use std::sync::Arc;
#[cfg(feature = "geninfer_linear_exact_prefilter")]
use std::cell::Cell;
#[cfg(feature = "geninfer_linear_exact_prefilter")]
use std::hash::{Hash, Hasher};

use rustc_hash::FxHashMap;
use smallvec::SmallVec;

use crate::sym::{Interner, Sym};
use crate::term::{
    anti_unify_values, covers_value, evaluate, fixed_count_value, Env, EvalCtx, TermArena, TermIdx,
};
use crate::value::{cmp_value, SurfaceKind, Value};

#[cfg(feature = "geninfer_linear_exact_prefilter")]
thread_local! {
    static PREFILTER_IDENTITY_VALUE_COMPARISONS: Cell<u64> = const { Cell::new(0) };
    static PREFILTER_EXACT_ARITHMETIC_CHECKS: Cell<u64> = const { Cell::new(0) };
}

#[cfg(feature = "geninfer_linear_exact_prefilter")]
#[derive(Clone)]
struct PrefilterIdentityKey(Vec<Value>);

#[cfg(feature = "geninfer_linear_exact_prefilter")]
impl PartialEq for PrefilterIdentityKey {
    fn eq(&self, other: &Self) -> bool {
        let mut equal = self.0.len() == other.0.len();
        for (left, right) in self.0.iter().zip(&other.0) {
            if crate::scale_audit::enabled() {
                PREFILTER_IDENTITY_VALUE_COMPARISONS.with(|n| n.set(n.get().saturating_add(1)));
            }
            if left != right { equal = false; break; }
        }
        equal
    }
}
#[cfg(feature = "geninfer_linear_exact_prefilter")]
impl Eq for PrefilterIdentityKey {}
#[cfg(feature = "geninfer_linear_exact_prefilter")]
impl Hash for PrefilterIdentityKey {
    fn hash<H: Hasher>(&self, state: &mut H) { self.0.hash(state); }
}

#[inline]
fn trace_scanned_node(ctx: &EvalCtx, node: crate::graph::NodeID) {
    crate::access_trace::note_node_type_and_attrs(ctx.graph, node);
}

/// Build a `Value::Surface(Text, ..)` from a `&str` — the output-key /
/// output-text constructor that needs no interner access at all.
fn surf(s: &str) -> Value {
    Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes()))
}

fn surf_string(s: String) -> Value {
    Value::Surface(
        SurfaceKind::Text,
        Arc::from(s.into_bytes().into_boxed_slice()),
    )
}

fn wild_value(wild: Sym) -> Value {
    Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(wild)]))
}

/// Resolve (or locally fabricate) a Sym for a string encountered while
/// parsing a JSON-string `signature` attr. Real strings (found via
/// `Interner::lookup`) win first — this is what lets a part's parsed
/// predicate name compare EQUAL to the same predicate name arriving via
/// `goal` (which was properly interned elsewhere). A truly novel string
/// gets a placeholder Sym, unique within `extra` (scoped to one
/// `ShapeDecode` call) — safe because parsed signatures never reach the
/// output.
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

/// Convert a parsed `serde_json::Value` into our `Value` tree, scoped to
/// one `ShapeDecode` call (see module docs). Plain JSON arrays decode as
/// `Value::Tuple` (matches `persist::decode_value`'s bare-array case —
/// relation-systems never use the `__tuple__`/`__set__`/`__dict__` tagged
/// forms, they're always plain nested arrays of strings).
fn json_to_value_scoped(
    j: &serde_json::Value,
    interner: &Interner,
    extra: &mut FxHashMap<String, Sym>,
    next_id: &mut u32,
) -> Value {
    match j {
        serde_json::Value::Null => Value::None,
        serde_json::Value::Bool(b) => Value::Bool(*b),
        serde_json::Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Value::Int(i)
            } else if let Some(f) = n.as_f64() {
                Value::Float(f)
            } else {
                Value::Float(0.0)
            }
        }
        serde_json::Value::String(s) => Value::Str(local_sym(interner, extra, next_id, s)),
        serde_json::Value::Array(items) => {
            let v: SmallVec<[Value; 4]> = items
                .iter()
                .map(|it| json_to_value_scoped(it, interner, extra, next_id))
                .collect();
            // Kept as `Tuple` (ARC6): a JSON-string signature is decoded here
            // for SCORING, and reverting it to `List` was tried and did NOT
            // change the one outstanding regression, so the change was backed
            // out rather than shipped unmotivated. See §10 of
            // PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md.
            Value::Tuple(Arc::new(v))
        }
        // Relation-systems are plain nested arrays; an object here isn't
        // part of the vocabulary this Term reads.
        serde_json::Value::Object(_) => Value::None,
    }
}

/// A single held part read off a `codebook_type` node — the Rust twin of
/// `_load_shape_signatures`'s per-entry `(kind, signature, source)`.
#[derive(Clone)]
struct Part {
    /// Dict key equivalent — used for `used`/`exclude` membership tests.
    name: String,
    /// The node's own `name` attr Value (a REAL Sym) — reused directly in
    /// the output so we never need to re-intern the part's own name.
    name_val: Value,
    /// `kind` attr, or `Value::Str(Sym::default())` (resolves to `""`,
    /// always valid regardless of interner state) when absent.
    kind_val: Value,
    /// `concept` if truthy, else `faculty`, else `Value::None` — mirrors
    /// `at.get("concept") or at.get("faculty")`.
    source_val: Value,
    /// The parsed relation-system (native Tuple attr used as-is; a
    /// JSON-string attr parsed via `json_to_value_scoped`). Internal-only
    /// — never placed in the output.
    sig: Vec<Value>,
    /// Optional `dim_types` attr — one entry per slot, `"pred"` /
    /// `"coord:<axis>"` / `"val"` / `"sym"` (see `DimInfer`'s doc in
    /// `term.rs`). `None` when the attr is absent — `DimInfer` skips rung
    /// 2 for this part entirely, gracefully (no generator ever applies
    /// without a typed coordinate slot to act on). Read the same
    /// native-Tuple-or-JSON-string way as `signature` (see
    /// `parse_string_list`) — never used by `ShapeDecode`/`TransformDecode`,
    /// only by `DimInfer`, but loaded here once so all three Terms share
    /// one codebook reader.
    dim_types: Option<Vec<String>>,
}

/// One fully validated parsed codebook plus an order-preserving index for
/// ShapeDecode's case-insensitive name aperture. It is scoped to one
/// immutable EvalCtx, so no graph mutation invalidation is needed.
pub(crate) struct LoadedCodebook {
    parts: Vec<Part>,
    extra: FxHashMap<String, Sym>,
    positions_by_folded_name: FxHashMap<String, Vec<usize>>,
}

impl LoadedCodebook {
    fn new(parts: Vec<Part>, extra: FxHashMap<String, Sym>) -> Self {
        let mut positions_by_folded_name: FxHashMap<String, Vec<usize>> = FxHashMap::default();
        for (position, part) in parts.iter().enumerate() {
            positions_by_folded_name
                .entry(part.name.to_lowercase())
                .or_default()
                .push(position);
        }
        Self {
            parts,
            extra,
            positions_by_folded_name,
        }
    }

    fn select(&self, scope: Option<&std::collections::HashSet<String>>) -> Vec<Part> {
        let Some(names) = scope else {
            return self.parts.clone();
        };
        let mut positions = Vec::new();
        for name in names {
            if let Some(found) = self.positions_by_folded_name.get(name) {
                positions.extend_from_slice(found);
            }
        }
        positions.sort_unstable();
        positions.dedup();
        positions
            .into_iter()
            .map(|i| self.parts[i].clone())
            .collect()
    }
}

/// Read a string-SHAPED attr `Value` — accepts BOTH a frozen
/// `Value::Str(Sym)` and a `Value::Surface(SurfaceKind::Text, ..)`.
///
/// **This is the contract the rest of the engine already implements** and
/// that this file's own `td_val_to_string` (below) has always had:
/// `graph_rules.rs::as_str` and `term.rs::eq_with_string_coercion` both
/// accept the pair, for exactly this bug class. `load_parts` /
/// `load_generators` were the readers that never got the arm.
///
/// The Surface arm is NOT an edge case — it is the ONLY shape a
/// rule-built string can have. `evaluate()` holds an immutable
/// `&Interner`, so a Term-constructed string can never be interned into a
/// `Sym`; `StringConcat` / `StringSlice` / `ToJsonString` /
/// `FromJsonString` therefore ALL evaluate to `Surface(Text)` by
/// construction (term.rs states this in its own words). A codebook entry
/// NAMED BY A RULE is a `Surface`, and without this arm it was silently
/// dropped from the codebook — no error, no warning, the part simply did
/// not exist and every later observation re-minted against a codebook
/// that never grew.
///
/// Returns `None` ONLY for a genuinely non-string-shaped Value. Callers
/// must treat that as an ERROR (`string_attr_or_panic`), never a skip.
fn str_shaped<'a>(v: &'a Value, interner: &'a Interner) -> Option<&'a str> {
    match v {
        Value::Str(s) => Some(interner.resolve(*s)),
        Value::Surface(SurfaceKind::Text, bytes) => std::str::from_utf8(bytes).ok(),
        _ => None,
    }
}

/// Read a codebook node's string-shaped attr, or PANIC naming the offender.
///
/// **Why a panic and not a `continue`** (VISION_PROTOCOL §1.1 / §12; the
/// `PickUnique` precedent): `continue`-on-unexpected-type is a SILENT
/// WRONG ANSWER — the same disease as `.get('Name','')` returning `''` and
/// a guarded division scoring a dead cell a flawless floor. It cost this
/// arc a near-miss FALSE PARADIGM NEGATIVE: a dropped codebook entry made
/// all four lattice orientations mint, which reads exactly like *"the core
/// loop cannot fold orientation"* — a harness artifact wearing the costume
/// of the most consequential claim in the arc. No gate caught it.
///
/// The line drawn here is between INAPPLICABLE and MALFORMED:
///   * attr ABSENT      -> caller skips (legitimate: not every node of the
///                         type is a part; the graceful skip these loaders
///                         are documented to perform).
///   * attr STRING-SHAPED -> loads (`Str` byte-identically as before;
///                         `Surface` is the fix).
///   * attr PRESENT, WRONG TYPE -> **panic**. That is not "inapplicable",
///                         it is a graph the loader cannot read, and
///                         silence there is indistinguishable from the
///                         part not existing.
///
/// So on a well-formed graph every committed result is byte-identical
/// (exactly `PickUnique`'s ≤1-candidate argument), and the malformed case
/// that used to vanish now stops the run and names itself.
fn string_attr_or_panic<'a>(
    v: &'a Value,
    interner: &'a Interner,
    attr: &str,
    node_type: &str,
) -> &'a str {
    match str_shaped(v, interner) {
        Some(s) => s,
        None => panic!(
            "load_parts/load_generators: `{}` node's `{}` attr is {:?} — not a \
             string-shaped Value (expected Value::Str or Value::Surface(Text)). \
             This reader used to `continue` here, SILENTLY dropping the entry \
             from the codebook: no error, no warning, the part simply did not \
             exist and every later observation re-minted against a codebook \
             that never grew (VISION_PROTOCOL §1.1 — an absence produced by a \
             LOOKUP is not evidence of a measurement). If this value came from \
             a Term, note that every Term-built string is Surface(Text), which \
             is now accepted; a non-string type here means the graph is \
             malformed, not that the entry is inapplicable.",
            node_type, attr, v
        ),
    }
}

/// Read every `codebook_type`-typed node into an ordered part list —
/// mirrors `_load_shape_signatures`'s dict-of-name semantics: first
/// occurrence of a name fixes its ORDER, a later duplicate name only
/// overwrites its VALUE (real Python dict `d[k]=v` semantics).
fn load_parts(
    ctx: &EvalCtx,
    codebook_type: Sym,
    extra: &mut FxHashMap<String, Sym>,
    next_id: &mut u32,
) -> Vec<Part> {
    load_parts_with_scope(ctx, codebook_type, extra, next_id, None)
}

/// Scoped variant used by GenInfer. It tests the scope attribute before
/// parsing signatures or building Parts, so unrelated frames do not enter
/// matrix candidate evaluation.
fn load_parts_with_scope(
    ctx: &EvalCtx,
    codebook_type: Sym,
    extra: &mut FxHashMap<String, Sym>,
    next_id: &mut u32,
    scope_filter: Option<&Value>,
) -> Vec<Part> {
    let mut order: Vec<String> = Vec::new();
    let mut by_name: FxHashMap<String, Part> = FxHashMap::default();
    let scope_key = scope_filter.and_then(|_| ctx.interner.lookup("scope_id"));
    if scope_filter.is_some() && scope_key.is_none() {
        return Vec::new();
    }
    let indexed_scope = scope_filter
        .zip(scope_key)
        .is_some_and(|(scope, key)| ctx.graph.has_attr_index(codebook_type, key));
    let population = if indexed_scope {
        let (Some(scope), Some(key)) = (scope_filter, scope_key) else {
            unreachable!("indexed scope requires a scope value and key")
        };
        crate::access_trace::note_helper_work(56, 1);
        let nodes = ctx.graph.nodes_where(codebook_type, key, scope);
        crate::access_trace::note_helper_work(57, nodes.len() as u64);
        nodes
    } else {
        ctx.graph.nodes_of_type(codebook_type)
    };

    for nid in population {
        if !indexed_scope {
            crate::access_trace::note_helper_work(47, 1);
        }
        let node = ctx.graph.node(nid);
        if !indexed_scope {
            if let (Some(scope), Some(key)) = (scope_filter, scope_key) {
                if node.attrs.get(&key) != Some(scope) {
                    continue;
                }
            }
        }
        crate::access_trace::note_helper_work(48, node.attrs.len() as u64);
        trace_scanned_node(ctx, nid);
        let mut name_val: Option<Value> = None;
        let mut sig_val: Option<Value> = None;
        let mut kind_val: Option<Value> = None;
        let mut concept_val: Option<Value> = None;
        let mut faculty_val: Option<Value> = None;
        let mut dim_types_val: Option<Value> = None;
        for (k, v) in node.attrs.iter() {
            match ctx.interner.resolve(*k) {
                "name" => name_val = Some(v.clone()),
                "signature" => sig_val = Some(v.clone()),
                "kind" => kind_val = Some(v.clone()),
                "concept" => concept_val = Some(v.clone()),
                "faculty" => faculty_val = Some(v.clone()),
                "dim_types" => dim_types_val = Some(v.clone()),
                _ => {}
            }
        }
        // ABSENT name/signature -> not a part; skip (unchanged, legitimate).
        let (Some(nv), Some(sv)) = (name_val, sig_val) else {
            continue;
        };
        // PRESENT name -> must be string-shaped. `Str` reads exactly as
        // before; `Surface(Text)` — a name a RULE built — now loads instead
        // of vanishing; any other type is malformed and panics.
        let name = string_attr_or_panic(
            &nv,
            ctx.interner,
            "name",
            &format!(
                "codebook part (type {}, node {:?})",
                ctx.interner.resolve(codebook_type),
                nid
            ),
        )
        .to_string();
        if name.is_empty() {
            continue;
        }
        let sig: Vec<Value> = match &sv {
            Value::Tuple(t) | Value::List(t) => t.iter().cloned().collect(),
            // A JSON-string signature, interned (`Str`) or rule-built
            // (`Surface(Text)` — e.g. from `ToJsonString`). The Surface arm
            // was the SECOND silent drop in this function: a rule that
            // composed a signature landed a part whose `sig` came back empty
            // and was skipped by the `is_empty` guard below, indistinguishable
            // from a part that was never there.
            other => {
                // NAME THE NODE. The panic is correct to be loud, but a
                // literal "codebook part" cannot be acted on: it took two
                // crashed 145-trial runs and two checkpoint scans to fail to
                // identify the offender, because the malformed node is minted
                // and panics inside the SAME fixpoint and is therefore never
                // checkpointed. The codebook type plus the node id names the
                // minting rule directly.
                let text = string_attr_or_panic(
                    other,
                    ctx.interner,
                    "signature",
                    &format!(
                        "codebook part (type {}, node {:?}, name {:?})",
                        ctx.interner.resolve(codebook_type),
                        nid,
                        name
                    ),
                );
                match serde_json::from_str::<serde_json::Value>(text) {
                    Ok(serde_json::Value::Array(items)) => items
                        .iter()
                        .map(|it| json_to_value_scoped(it, ctx.interner, extra, next_id))
                        .collect(),
                    _ => Vec::new(),
                }
            }
        };
        if sig.is_empty() {
            continue;
        }
        let kind_val = kind_val.unwrap_or(Value::Str(Sym::default()));
        let source_val = match &concept_val {
            Some(v) if v.truthy() => concept_val.unwrap(),
            _ => faculty_val.unwrap_or(Value::None),
        };
        let dim_types = dim_types_val
            .as_ref()
            .and_then(|v| parse_string_list(v, ctx.interner));
        if !by_name.contains_key(&name) {
            order.push(name.clone());
        }
        crate::access_trace::note_helper_work(49, 1);
        by_name.insert(
            name.clone(),
            Part {
                name,
                name_val: nv,
                kind_val,
                source_val,
                sig,
                dim_types,
            },
        );
    }

    order
        .into_iter()
        .filter_map(|nm| by_name.remove(&nm))
        .collect()
}

/// Parse a `dim_types`/`coord_dims`/`params`-style list attr: a native
/// `Value::Tuple` of `Str` (for `dim_types`), OR a `Value::Str` holding a
/// JSON array of strings — the same native-or-JSON-string duality
/// `load_parts` already accepts for `signature`. `None` on any other shape
/// (missing attr, wrong element types, malformed JSON) — callers treat
/// that as "not typed", not an error (rung 2 is optional, graceful-skip).
fn parse_string_list(v: &Value, interner: &Interner) -> Option<Vec<String>> {
    match v {
        // Per-ELEMENT string coercion too: a Tuple of rule-built strings is
        // all `Surface(Text)`, and the old `Value::Str`-only filter_map
        // silently returned a SHORTER list — a drop that is worse than the
        // top-level one because it leaves a plausible non-empty result.
        Value::Tuple(t) | Value::List(t) => Some(
            t.iter()
                .filter_map(|x| str_shaped(x, interner).map(|s| s.to_string()))
                .collect(),
        ),
        // A JSON-array string, interned or rule-built.
        other => {
            let text = str_shaped(other, interner)?;
            match serde_json::from_str::<serde_json::Value>(text) {
                Ok(serde_json::Value::Array(items)) => Some(
                    items
                        .iter()
                        .filter_map(|it| it.as_str().map(|s| s.to_string()))
                        .collect(),
                ),
                _ => None,
            }
        }
    }
}

/// Parse a `coord_dims`/`params`-style list attr: a native `Value::Tuple`
/// of `Int` (or `Float`, truncated), OR a `Value::Str` holding a JSON
/// array of integers. `None` on any other shape.
fn parse_int_list(v: &Value, interner: &Interner) -> Option<Vec<i64>> {
    match v {
        Value::Tuple(t) | Value::List(t) => Some(
            t.iter()
                .filter_map(|x| match x {
                    Value::Int(i) => Some(*i),
                    Value::Float(f) => Some(*f as i64),
                    _ => None,
                })
                .collect(),
        ),
        // A JSON-array string, interned (`Str`) or rule-built
        // (`Surface(Text)`). `None` stays the "not typed / inapplicable"
        // signal these two callers are documented to skip on, so the
        // graceful-skip contract is unchanged — only the SHAPE of string it
        // can read is widened.
        other => {
            let text = str_shaped(other, interner)?;
            match serde_json::from_str::<serde_json::Value>(text) {
                Ok(serde_json::Value::Array(items)) => {
                    Some(items.iter().filter_map(|it| it.as_i64()).collect())
                }
                _ => None,
            }
        }
    }
}

/// One held `DimensionGenerator` codebook node — `{name, kind, coord_dims,
/// params}` (see `DimInfer`'s doc in `term.rs`). `kind` dispatches to a
/// built-in primitive (`apply_generator_once`); `name` is the
/// human/graph-facing identifier reported in `DimInfer`'s `generator`
/// output field (defaults to `kind`'s text when the `kind` attr is
/// absent, so a minimal `{name, coord_dims, params}` node — name doubling
/// as its own dispatch key — still works).
struct Generator {
    /// The generator's resolved name string — the same text as `name_val`,
    /// kept as an owned `String` for the composition distinct-generator
    /// check and the ranking tie-break (see `eval_dim_infer`) without
    /// re-resolving the interner in a hot loop.
    name: String,
    name_val: Value,
    kind: String,
    coord_dims: Vec<i64>,
    params: Vec<i64>,
    /// The cycle length for a `kind == "modular"` (cyclic Z_n) generator —
    /// one step maps a coord slot `v -> (v + 1) mod modulus` (see
    /// `modular_step_once`). Zero for every non-modular generator (the
    /// coordinate-map primitives ignore it); a `modulus <= 0` on a
    /// `"modular"` generator means "no cycle set" and makes it
    /// inapplicable (skipped in `load_generators`, the same graceful-skip
    /// as a missing `coord_dims`/`params`).
    modulus: i64,
    /// The flattened, row-major INTEGER MATRIX for a `kind == "linear"`
    /// generator — the ONLY generator kind whose transform is DEFINED BY
    /// GRAPH DATA rather than by a hardcoded Rust dispatch (see
    /// `apply_linear_once`). `matrix.len() == n*n` where `n ==
    /// coord_dims.len()`; the map sends the coord vector `v` (origin-
    /// normalized per axis) to `M·(v - min)`, leaving any leftover
    /// translation for the rung-1 residual check exactly like the other
    /// generators. Empty for every non-`"linear"` kind (they ignore it),
    /// and a `"linear"` generator with the wrong `matrix` length is skipped
    /// in `load_generators` (the same graceful-skip as a bad
    /// `coord_dims`/`params`). This field is what makes a MINTED generator
    /// (`GenInfer` → `sd_infer_generator`) participate in decode: the
    /// inferred matrix rides in as data and `apply_linear_once` reads it —
    /// no new Rust dispatch arm per discovered map.
    matrix: Vec<i64>,
    /// Flattened output-major quadratic coefficients for `kind="quadratic2"`:
    /// two rows over `[x,y,x²,xy,y²]`. This is a separate graph-data payload;
    /// polynomial coefficients are never stored under the linear `matrix`
    /// attribute.
    coefficients: Vec<i64>,
    /// The integer OFFSET vector for a `kind == "translate"` (affine
    /// pure-translation) generator — one step maps a coord slot `v -> v +
    /// offset[j]` with NO wrap and NO origin-normalization (see
    /// `apply_translate_once`). `offset.len() == coord_dims.len()`. Composing
    /// `k` steps therefore maps `v -> v + k·offset[j]`, so the exponent `k` is
    /// a DISPLACEMENT quantum: a rigidly-translating pattern is the SAME held
    /// shape stepping by `k` along a minted `latent:translate` dimension — the
    /// affine twin of the linear generator, and the one generator kind rung 1
    /// cannot pre-empt at ORBIT grain (any two frames of a constant-velocity
    /// orbit are mutual translates, so pairwise-explainability is vacuous;
    /// only a CONSTANT offset across the whole orbit identifies the map — see
    /// `TIME_DESIGN.md`). Empty for every non-`"translate"` kind (they ignore
    /// it); a `"translate"` generator whose `offset` length ≠ `coord_dims`
    /// is skipped in `load_generators`, the same graceful skip as a bad
    /// `matrix`.
    offset: Vec<i64>,
    /// `kind == "composite"` only: the generator's FLATTENED primitive step
    /// sequence, resolved at load time from its `steps` (generator names)
    /// and `ks` attrs (RECURSIVE_SELF_IMPROVEMENT_PLAN WP5). A composite may
    /// name another composite; it is expanded into primitives, so a minted
    /// chunk becomes a single codebook entry that DimInfer composes with one
    /// more step -- the length-<=2 search then reaches arbitrary depth
    /// through growth, not through a wider search. Empty for other kinds.
    composite: Vec<PrimStep>,
    /// `retired` attr truthy: the generator still RESOLVES as a step of a
    /// composite that names it, but is not itself a decode candidate (chunk
    /// retention, tranche 2 gate 3). Absent -> false (all historical seeds).
    retired: bool,
}

/// One resolved primitive step of a `composite` generator.
#[derive(Clone)]
struct PrimStep {
    kind: String,
    coord_dims: Vec<i64>,
    modulus: i64,
    matrix: Vec<i64>,
    coefficients: Vec<i64>,
    offset: Vec<i64>,
    k: i64,
}

/// Maximum flattened primitive steps in a composite (a resource bound, not a
/// semantic one: a deeper chunk is skipped at load like any malformed entry).
const COMPOSITE_MAX_STEPS: usize = 32;

/// Apply generator `gen` `k` times; a composite applies its flattened
/// primitive sequence `k` times.
fn apply_gen_k(gen: &Generator, sig: &[Value], k: i64) -> Option<Vec<Value>> {
    if gen.kind == "composite" {
        let mut cur = sig.to_vec();
        for _ in 0..k.max(0) {
            for st in &gen.composite {
                cur = apply_generator_k_with_coefficients(
                    &st.kind, &st.coord_dims, &cur, st.modulus, &st.matrix, &st.coefficients, &st.offset, st.k,
                )?;
            }
        }
        return Some(cur);
    }
    apply_generator_k_with_coefficients(
        &gen.kind, &gen.coord_dims, sig, gen.modulus, &gen.matrix, &gen.coefficients, &gen.offset, k,
    )
}

/// Read every `generator_type`-typed node into an ordered generator list —
/// same first-occurrence-order-wins / by-name dict semantics as
/// `load_parts`. A node missing `name`, or with an empty `coord_dims` or
/// `params` list (including malformed/absent attrs — see
/// `parse_int_list`), is skipped: an inapplicable generator, not an error.
/// The optional `modulus` attr (an `Int`, defaulting to `0` when absent or
/// malformed) is the cycle length for a `"modular"` generator; a
/// `"modular"` generator with `modulus <= 0` is likewise skipped (a cyclic
/// map with no cycle is inapplicable — the same graceful skip), while a
/// non-`"modular"` generator ignores `modulus` entirely.
fn load_generators(ctx: &EvalCtx, generator_type: Sym) -> Vec<Generator> {
    let mut order: Vec<String> = Vec::new();
    let mut by_name: FxHashMap<String, Generator> = FxHashMap::default();
    let mut pending_composites: Vec<(String, Vec<String>, Vec<i64>)> = Vec::new();

    for nid in ctx.graph.nodes_of_type(generator_type) {
        crate::access_trace::note_helper_work(55, 1);
        trace_scanned_node(ctx, nid);
        let node = ctx.graph.node(nid);
        let mut name_val: Option<Value> = None;
        let mut kind_val: Option<Value> = None;
        let mut coord_dims_val: Option<Value> = None;
        let mut params_val: Option<Value> = None;
        let mut modulus_val: Option<Value> = None;
        let mut matrix_val: Option<Value> = None;
        let mut coefficients_val: Option<Value> = None;
        let mut offset_val: Option<Value> = None;
        let mut steps_val: Option<Value> = None;
        let mut ks_val: Option<Value> = None;
        let mut retired = false;
        for (k, v) in node.attrs.iter() {
            match ctx.interner.resolve(*k) {
                "name" => name_val = Some(v.clone()),
                "kind" => kind_val = Some(v.clone()),
                "coord_dims" => coord_dims_val = Some(v.clone()),
                "params" => params_val = Some(v.clone()),
                "modulus" => modulus_val = Some(v.clone()),
                "matrix" => matrix_val = Some(v.clone()),
                "coefficients" => coefficients_val = Some(v.clone()),
                "offset" => offset_val = Some(v.clone()),
                "steps" => steps_val = Some(v.clone()),
                "ks" => ks_val = Some(v.clone()),
                "retired" => retired = v.truthy(),
                _ => {}
            }
        }
        // ABSENT name -> an inapplicable generator; skip (unchanged, and
        // documented as graceful above). PRESENT but not string-shaped ->
        // malformed, and panics rather than vanishing.
        let Some(nv) = name_val else { continue };
        let name =
            string_attr_or_panic(&nv, ctx.interner, "name", "DimensionGenerator").to_string();
        if name.is_empty() {
            continue;
        }
        // `kind` defaults to `name` when ABSENT (documented). When present it
        // must be string-shaped — the `Surface` arm lets a rule name a
        // generator's kind; a wrong type here previously fell through this
        // `_` arm to the default silently, so a malformed `kind` masqueraded
        // as "kind attr absent" and dispatched on the wrong primitive.
        let kind = match &kind_val {
            Some(v) => {
                string_attr_or_panic(v, ctx.interner, "kind", "DimensionGenerator").to_string()
            }
            None => name.clone(),
        };
        if kind == "composite" {
            // Steps are resolved after every node is read (they may name
            // generators declared later, or other composites).
            let names: Option<Vec<String>> = match &steps_val {
                Some(Value::Tuple(xs) | Value::List(xs)) => xs
                    .iter()
                    .map(|x| match x {
                        Value::Str(sy) => Some(ctx.interner.resolve(*sy).to_string()),
                        Value::Surface(_, b) => std::str::from_utf8(b).ok().map(str::to_string),
                        _ => None,
                    })
                    .collect(),
                _ => None,
            };
            let ks = ks_val.as_ref().and_then(|v| parse_int_list(v, ctx.interner));
            let params = params_val
                .as_ref()
                .and_then(|v| parse_int_list(v, ctx.interner))
                .unwrap_or_else(|| vec![1]);
            if let (Some(names), Some(ks)) = (names, ks) {
                if !names.is_empty() && names.len() == ks.len() && !params.is_empty() {
                    if !by_name.contains_key(&name) {
                        order.push(name.clone());
                    }
                    pending_composites.push((name.clone(), names, ks));
                    by_name.insert(name.clone(), Generator {
                        name: name.clone(), name_val: nv, kind, coord_dims: Vec::new(), params,
                        modulus: 0, matrix: Vec::new(), coefficients: Vec::new(), offset: Vec::new(),
                        composite: Vec::new(), retired,
                    });
                }
            }
            continue;
        }
        let Some(coord_dims) = coord_dims_val
            .as_ref()
            .and_then(|v| parse_int_list(v, ctx.interner))
        else {
            continue;
        };
        let Some(params) = params_val
            .as_ref()
            .and_then(|v| parse_int_list(v, ctx.interner))
        else {
            continue;
        };
        if coord_dims.is_empty() || params.is_empty() {
            continue;
        }
        let modulus = match &modulus_val {
            Some(Value::Int(m)) => *m,
            _ => 0,
        };
        // A cyclic generator with no cycle length is inapplicable — skip it
        // gracefully rather than letting `modular_step_once` reject every
        // call downstream (same posture as a missing coord_dims/params).
        if kind == "modular" && modulus <= 0 {
            continue;
        }
        // The `matrix` attr (a flattened row-major Int list) is read only for
        // a `"linear"` generator; every other kind ignores it. A `"linear"`
        // generator whose matrix is absent or is not exactly `n*n` for
        // `n == coord_dims.len()` is inapplicable — skip it gracefully (the
        // same posture as a missing coord_dims/params).
        let matrix: Vec<i64> = matrix_val
            .as_ref()
            .and_then(|v| parse_int_list(v, ctx.interner))
            .unwrap_or_default();
        if kind == "linear" {
            let n = coord_dims.len();
            if matrix.len() != n * n {
                continue;
            }
        }
        let coefficients: Vec<i64> = coefficients_val
            .as_ref()
            .and_then(|v| parse_int_list(v, ctx.interner))
            .unwrap_or_default();
        if kind == "quadratic2"
            && (!cfg!(feature = "geninfer_quadratic_map_solver")
                || coord_dims.len() != 2
                || coefficients.len() != 10)
        {
            continue;
        }
        // The `offset` attr (a flattened Int list) is read only for a
        // `"translate"` generator; every other kind ignores it. A
        // `"translate"` generator whose offset length ≠ coord_dims is
        // inapplicable — skip gracefully (same posture as a bad matrix).
        let offset: Vec<i64> = offset_val
            .as_ref()
            .and_then(|v| parse_int_list(v, ctx.interner))
            .unwrap_or_default();
        if kind == "translate" && offset.len() != coord_dims.len() {
            continue;
        }
        if !by_name.contains_key(&name) {
            order.push(name.clone());
        }
        by_name.insert(
            name.clone(),
            Generator {
                name: name.clone(),
                name_val: nv,
                kind,
                coord_dims,
                params,
                modulus,
                matrix,
                coefficients,
                offset,
                composite: Vec::new(),
                retired,
            },
        );
    }

    // Resolve composites to flattened primitive sequences. Iterates to a
    // fixed point so a composite may name a composite; an unresolvable
    // (missing, cyclic, or over-long) composite is dropped -- inapplicable,
    // the same graceful skip as any malformed generator.
    let mut unresolved = pending_composites;
    loop {
        let before = unresolved.len();
        let mut next = Vec::new();
        for (name, steps, ks) in unresolved {
            let mut flat: Vec<PrimStep> = Vec::new();
            let mut ok = true;
            for (st, k) in steps.iter().zip(&ks) {
                match by_name.get(st) {
                    Some(g) if g.kind == "composite" && !g.composite.is_empty() => {
                        for _ in 0..(*k).max(0) { flat.extend(g.composite.iter().cloned()); }
                    }
                    Some(g) if g.kind != "composite" => flat.push(PrimStep {
                        kind: g.kind.clone(), coord_dims: g.coord_dims.clone(), modulus: g.modulus,
                        matrix: g.matrix.clone(), coefficients: g.coefficients.clone(),
                        offset: g.offset.clone(), k: *k,
                    }),
                    _ => { ok = false; break; }
                }
            }
            if ok && !flat.is_empty() && flat.len() <= COMPOSITE_MAX_STEPS {
                let mut cd: Vec<i64> = flat.iter().flat_map(|p| p.coord_dims.iter().copied()).collect();
                cd.sort_unstable();
                cd.dedup();
                if let Some(g) = by_name.get_mut(&name) {
                    g.composite = flat;
                    g.coord_dims = cd;
                }
            } else if ok {
                // over-long or empty: leave unresolved -> dropped below
            } else {
                next.push((name, steps, ks));
            }
        }
        if next.is_empty() || next.len() == before {
            break;
        }
        unresolved = next;
    }

    order
        .into_iter()
        .filter_map(|nm| by_name.remove(&nm))
        .filter(|g| g.kind != "composite" || !g.composite.is_empty())
        .filter(|g| !g.retired)
        .collect()
}

/// Does `dim_types` type EVERY one of `coord_dims` as a coordinate slot
/// (`"coord:<axis>"`, matched by prefix — the axis label itself is free
/// text, not interpreted)? A generator whose `coord_dims` reach past the
/// end of `dim_types`, or land on a non-`"coord:"` slot, is not applicable
/// to this candidate at all — the `DimInfer` gate that lets a part with no
/// (or partial) `dim_types` skip rung 2 gracefully.
fn dims_are_coord(dim_types: &[String], coord_dims: &[i64]) -> bool {
    !coord_dims.is_empty()
        && coord_dims.iter().all(|&idx| {
            usize::try_from(idx)
                .ok()
                .and_then(|i| dim_types.get(i))
                .is_some_and(|t| t.starts_with("coord:"))
        })
}

/// Read the `Int` value at slot `idx` of every relation in `sig` — `None`
/// (generator not applicable) if any relation is too short or holds a
/// non-`Int` value there (rung 2 is integer-lattice-only by design; a
/// `Float` coordinate, or a symbolic one, simply never matches a generator
/// slot).
fn coord_ints(sig: &[Value], idx: usize) -> Option<Vec<i64>> {
    let mut out = Vec::with_capacity(sig.len());
    for rel in sig {
        let (Value::Tuple(t) | Value::List(t)) = rel else {
            return None;
        };
        match t.get(idx) {
            Some(Value::Int(i)) => out.push(*i),
            _ => return None,
        }
    }
    Some(out)
}

/// Copy `rel` with slot `idx` replaced by `val` — `rel` unchanged (cloned)
/// if it isn't a `Tuple` (defensive; every relation is one in practice).
fn set_coord(rel: &Value, idx: usize, val: i64) -> Value {
    let (Value::Tuple(t) | Value::List(t)) = rel else {
        return rel.clone();
    };
    let mut nt: SmallVec<[Value; 4]> = t.iter().cloned().collect();
    if idx < nt.len() {
        nt[idx] = Value::Int(val);
    }
    // KIND-PRESERVING (`Value::reseq`): every geometry generator funnels
    // through here, and its output is compared against OBSERVED relations
    // by `frames_equal`. Emitting a Tuple for a List input made every
    // generator un-verifiable against list-shaped observations.
    rel.reseq(nt)
}

/// One 90-degree-clockwise rotation of `sig`'s `(r_idx, c_idx)` coordinate
/// pair about the shape's OWN bounding box, normalized so the result's
/// origin is `(0, 0)` (see `DimInfer`'s doc: "normalized to origin so a
/// pure rotation needs no separate translation" — any translation still
/// needed to reach the goal's actual position is left for the rung-1
/// residual check, via `build_candidate`, to find). `None` if `sig` is
/// empty or either coordinate isn't a uniform `Int` column (see
/// `coord_ints`).
fn rotate90_once(sig: &[Value], r_idx: usize, c_idx: usize) -> Option<Vec<Value>> {
    let rs = coord_ints(sig, r_idx)?;
    let cs = coord_ints(sig, c_idx)?;
    let min_r = *rs.iter().min()?;
    let min_c = *cs.iter().min()?;
    let max_r0 = rs.iter().map(|r| r - min_r).max()?;
    let mut out = Vec::with_capacity(sig.len());
    for (i, rel) in sig.iter().enumerate() {
        let r0 = rs[i] - min_r;
        let c0 = cs[i] - min_c;
        let new_r = c0;
        let new_c = max_r0 - r0;
        let rel = set_coord(rel, r_idx, new_r);
        let rel = set_coord(&rel, c_idx, new_c);
        out.push(rel);
    }
    Some(out)
}

/// Reflect `sig`'s single coordinate slot `idx` about the shape's OWN
/// bounding box on that axis, normalized to origin (`max - v`, which is
/// already zero-based — see the module's `DimInfer` design notes: this is
/// algebraically `(max - min) - (v - min)`, the min term cancels). `None`
/// under the same conditions as `rotate90_once`.
fn reflect_once(sig: &[Value], idx: usize) -> Option<Vec<Value>> {
    let vs = coord_ints(sig, idx)?;
    let max_v = *vs.iter().max()?;
    let mut out = Vec::with_capacity(sig.len());
    for (i, rel) in sig.iter().enumerate() {
        out.push(set_coord(rel, idx, max_v - vs[i]));
    }
    Some(out)
}

/// Scale `sig`'s coordinate slots `coord_dims` by a factor of 2 about each
/// axis's OWN bounding-box minimum, normalized so each scaled axis is
/// origin-based (`2 * (v - min)`). This is the MULTIPLICATIVE generator
/// whose integer step `k` is a LOG2-SCALE quantum: composing `k` steps
/// (see `apply_generator_k`) scales by `2^k`, so a doubled / quadrupled
/// shape is the SAME held shape stepping by `k = 1 / 2 / ...` along the
/// minted `latent:scale2` dimension. This is the concrete realisation of
/// "a base IS a dimension" (design 'transform-as-quantum-delta',
/// base-as-dimension): a log-scale base is not hand-set config — it is a
/// generator that `DimInfer` selects and `sd_recognize_dim` mints as a
/// `LatentDimension`, exactly like `rotation90`. A ratio (×2) thus becomes
/// the additive `k`-delta rung 1 already recognises for free, so a whole
/// scale FAMILY collapses to one held shape + one dimension instead of a
/// fresh `CapabilityAxis` per size (grows capability AND improves
/// efficiency). Any leftover translation to reach the goal's actual
/// position is left for the rung-1 residual check (`build_candidate`) to
/// find, exactly like `rotate90_once`. `None` if `sig` is empty, any
/// `coord_dims` index is out of range, or any coord slot isn't a uniform
/// `Int` column (see `coord_ints`; rung 2 is integer-lattice-only —
/// odd sizes just never match a `2^k` step).
fn scale_pow2_once(sig: &[Value], coord_dims: &[i64]) -> Option<Vec<Value>> {
    if sig.is_empty() || coord_dims.is_empty() {
        return None;
    }
    // Precompute (slot index, per-relation values, min) per coord dim from
    // the ORIGINAL signature, so the sequential per-dim rewrites below —
    // each touching a DIFFERENT slot — never read a value another dim just
    // overwrote.
    let mut per_dim: Vec<(usize, Vec<i64>, i64)> = Vec::with_capacity(coord_dims.len());
    for &d in coord_dims {
        let idx = usize::try_from(d).ok()?;
        let vs = coord_ints(sig, idx)?;
        let min_v = *vs.iter().min()?;
        per_dim.push((idx, vs, min_v));
    }
    let mut out = sig.to_vec();
    for (idx, vs, min_v) in &per_dim {
        for (i, rel) in out.iter_mut().enumerate() {
            let new_v = (vs[i] - min_v) * 2;
            let updated = set_coord(rel, *idx, new_v);
            *rel = updated;
        }
    }
    Some(out)
}

/// One step of a cyclic (Z_n) generator: increment every `coord_dims`
/// coordinate slot by ONE, MODULO `modulus`, in place — `v -> (v +
/// 1).rem_euclid(modulus)`. Composing `k` steps (see `apply_generator_k`)
/// therefore maps `v -> (v + k) mod modulus`, so this is the CATEGORICAL-
/// CYCLE generator whose integer step `k` is a phase quantum: an
/// orientation / hue / clock-face value stepping around its ring is the
/// SAME held shape stepping by `k` along a minted `latent:<name>`
/// dimension, exactly as `rotation90` is for square rotations and
/// `scale_pow2_once` is for log-scale.
///
/// The one thing that makes this generator NOT a plain rung-1 numeric
/// `shift` (`build_candidate`'s uniform-delta check) is the WRAP: with
/// `modulus == 4`, a slot at `3` steps to `0`, not `4`. When some slots
/// wrap and others do not, the held->goal delta is non-uniform and rung 1
/// cannot explain it — but this generator can, because the wrap is applied
/// consistently to the WHOLE shape before rung 1's residual check runs.
/// Any leftover translation / recolour to reach the goal is still left for
/// that residual check (`build_candidate`) to find, exactly like the other
/// generators.
///
/// Unlike `rotate90_once` / `reflect_once` / `scale_pow2_once`, a modular
/// step does NOT origin-normalize its coordinates: a cyclic axis is a
/// CATEGORICAL ring (position `0` and position `modulus - 1` are adjacent),
/// so there is no bounding box to re-base against — the value is wrapped
/// in place. `None` if `modulus <= 0` (no cycle — inapplicable), `sig` /
/// `coord_dims` is empty, or any coord slot isn't a uniform `Int` column
/// (see `coord_ints`; rung 2 is integer-lattice-only, so a `Float` phase
/// simply never matches a modular step).
fn modular_step_once(sig: &[Value], coord_dims: &[i64], modulus: i64) -> Option<Vec<Value>> {
    if modulus <= 0 || sig.is_empty() || coord_dims.is_empty() {
        return None;
    }
    // Read every coord dim's Int column from the ORIGINAL signature first
    // (each dim touches a DIFFERENT slot, so this ordering is not strictly
    // required, but it mirrors `scale_pow2_once` and stays robust if two
    // coord_dims ever alias one slot).
    let mut per_dim: Vec<(usize, Vec<i64>)> = Vec::with_capacity(coord_dims.len());
    for &d in coord_dims {
        let idx = usize::try_from(d).ok()?;
        let vs = coord_ints(sig, idx)?;
        per_dim.push((idx, vs));
    }
    let mut out = sig.to_vec();
    for (idx, vs) in &per_dim {
        for (i, rel) in out.iter_mut().enumerate() {
            let new_v = (vs[i] + 1).rem_euclid(modulus);
            *rel = set_coord(rel, *idx, new_v);
        }
    }
    Some(out)
}

/// One step of a GENERAL INTEGER LINEAR generator — the only generator
/// kind whose transform is DEFINED BY GRAPH DATA (`matrix`), not by a
/// hardcoded Rust dispatch. `matrix` is a flattened row-major `n×n` integer
/// matrix `M` (`n == coord_dims.len()`); this maps each cell's coordinate
/// vector `v` (the values at `coord_dims`, origin-normalized per axis) to
/// `M·(v − min)`. Any leftover translation to reach the goal's actual
/// position is left for the rung-1 residual check (`build_candidate`) to
/// find, exactly like `rotate90_once` / `scale_pow2_once`. This one arm
/// makes the ENTIRE integer general-linear group `GL(n, ℤ)` expressible as
/// data — rotation, reflection, shear, scale, glide-linear-part alike — so
/// a generator MINTED from an orbit (`eval_gen_infer`) participates in
/// decode with no new dispatch arm. `None` if `sig` is empty, `matrix` is
/// not exactly `n×n`, any `coord_dims` index is out of range, or any coord
/// slot isn't a uniform `Int` column (see `coord_ints`; integer lattice
/// only, matching every other generator).
fn apply_linear_once(sig: &[Value], coord_dims: &[i64], matrix: &[i64]) -> Option<Vec<Value>> {
    let n = coord_dims.len();
    if sig.is_empty() || n == 0 || matrix.len() != n * n {
        return None;
    }
    // Read every coord dim's Int column + its per-axis min from the ORIGINAL
    // signature, so the sequential per-slot rewrites below never read a value
    // another slot just overwrote (each coord_dim is a DIFFERENT slot).
    let mut idxs: Vec<usize> = Vec::with_capacity(n);
    let mut cols: Vec<Vec<i64>> = Vec::with_capacity(n);
    let mut mins: Vec<i64> = Vec::with_capacity(n);
    for &d in coord_dims {
        let idx = usize::try_from(d).ok()?;
        let vs = coord_ints(sig, idx)?;
        let min_v = *vs.iter().min()?;
        idxs.push(idx);
        cols.push(vs);
        mins.push(min_v);
    }
    let mut out = sig.to_vec();
    for (cell, rel) in out.iter_mut().enumerate() {
        // normalized input vector v = (value − min) per axis
        // output row i = Σ_j M[i][j] · v[j]
        for i in 0..n {
            let mut acc: i64 = 0;
            for j in 0..n {
                acc += matrix[i * n + j] * (cols[j][cell] - mins[j]);
            }
            *rel = set_coord(rel, idxs[i], acc);
        }
    }
    Some(out)
}

/// One step of a PURE TRANSLATION generator — the affine twin of
/// `apply_linear_once`, and the one generator kind whose transform is an
/// integer OFFSET carried as GRAPH DATA rather than a matrix. `offset` is an
/// integer vector (`offset.len() == coord_dims.len()`); this maps each cell's
/// coordinate slot `v -> v + offset[j]`, with NO wrap (unlike `modular`) and
/// NO origin-normalization (unlike every linear/rotation/scale step — a
/// translation is ABOUT position, so re-basing to the bbox would erase the
/// very thing it expresses). Composing `k` steps (`apply_generator_k`) gives
/// `v -> v + k·offset`, so the exponent `k` is a displacement quantum along a
/// minted `latent:translate` dimension. `None` if `sig`/`coord_dims`/`offset`
/// is empty or mismatched, any `coord_dims` index is out of range, or any
/// coord slot isn't a uniform `Int` column (see `coord_ints`; integer lattice
/// only, matching every other generator).
fn apply_translate_once(sig: &[Value], coord_dims: &[i64], offset: &[i64]) -> Option<Vec<Value>> {
    let n = coord_dims.len();
    if sig.is_empty() || n == 0 || offset.len() != n {
        return None;
    }
    // Read every coord dim's Int column from the ORIGINAL signature first (a
    // guard that the slot IS a uniform integer coordinate — mirrors
    // `modular_step_once`; each coord_dim is a distinct slot).
    let mut per_dim: Vec<(usize, Vec<i64>, i64)> = Vec::with_capacity(n);
    for (j, &d) in coord_dims.iter().enumerate() {
        let idx = usize::try_from(d).ok()?;
        let vs = coord_ints(sig, idx)?;
        per_dim.push((idx, vs, offset[j]));
    }
    let mut out = sig.to_vec();
    for (idx, vs, off) in &per_dim {
        for (i, rel) in out.iter_mut().enumerate() {
            *rel = set_coord(rel, *idx, vs[i] + off);
        }
    }
    Some(out)
}

/// Apply a 2-D total-degree-at-most-two map with no intercept. Coefficients
/// are flattened output-major over `[x,y,x²,xy,y²]`; a uniform translation
/// remains the shared residual check's responsibility. Checked i128
/// arithmetic and checked narrowing make overflow an inapplicable candidate.
#[cfg(feature = "geninfer_quadratic_map_solver")]
fn apply_quadratic2_once(
    sig: &[Value],
    coord_dims: &[i64],
    coefficients: &[i64],
) -> Option<Vec<Value>> {
    if sig.is_empty() || coord_dims.len() != 2 || coefficients.len() != 10 {
        return None;
    }
    let ix = usize::try_from(coord_dims[0]).ok()?;
    let iy = usize::try_from(coord_dims[1]).ok()?;
    let xs = coord_ints(sig, ix)?;
    let ys = coord_ints(sig, iy)?;
    let min_x = *xs.iter().min()?;
    let min_y = *ys.iter().min()?;
    let mut out = sig.to_vec();
    for (i, rel) in out.iter_mut().enumerate() {
        let x = (xs[i] as i128).checked_sub(min_x as i128)?;
        let y = (ys[i] as i128).checked_sub(min_y as i128)?;
        let features = [x, y, x.checked_mul(x)?, x.checked_mul(y)?, y.checked_mul(y)?];
        for axis in 0..2 {
            let mut value = 0i128;
            for j in 0..5 {
                value = value.checked_add(
                    (coefficients[axis * 5 + j] as i128).checked_mul(features[j])?,
                )?;
            }
            *rel = set_coord(rel, if axis == 0 { ix } else { iy }, i64::try_from(value).ok()?);
        }
    }
    Some(out)
}

/// Dispatch one primitive generator STEP by `kind`. `"rotation90"` needs
/// exactly a `[row_dim, col_dim]` pair; `"reflection_r"`/`"reflection_c"`
/// each need only ONE axis — `coord_dims.first()` for `"reflection_r"`,
/// `coord_dims.last()` for `"reflection_c"` (so a 1-element `coord_dims`
/// works identically for either name — `first()` and `last()` agree — and
/// a shared 2-element `[row_dim, col_dim]` also works, picking the
/// intended axis by name). `"scale2"` applies a ×2 (log2-scale) step to
/// EVERY `coord_dims` axis (any arity — the base-as-dimension warp, see
/// `scale_pow2_once`). `"modular"` steps EVERY `coord_dims` axis by one
/// MODULO `modulus` (any arity — the cyclic-phase warp, see
/// `modular_step_once`); `modulus` is ignored by every other `kind`. An
/// unrecognised `kind` is simply inapplicable (`None`), not an error — new
/// primitives are added here, never in Python (per the project's
/// Rust-primitive rule).
fn apply_generator_once(
    kind: &str,
    coord_dims: &[i64],
    sig: &[Value],
    modulus: i64,
    matrix: &[i64],
    coefficients: &[i64],
    offset: &[i64],
) -> Option<Vec<Value>> {
    match kind {
        "rotation90" => {
            if coord_dims.len() != 2 {
                return None;
            }
            rotate90_once(sig, coord_dims[0] as usize, coord_dims[1] as usize)
        }
        "reflection_r" => reflect_once(sig, *coord_dims.first()? as usize),
        "reflection_c" => reflect_once(sig, *coord_dims.last()? as usize),
        "scale2" => scale_pow2_once(sig, coord_dims),
        "modular" => modular_step_once(sig, coord_dims, modulus),
        "linear" => apply_linear_once(sig, coord_dims, matrix),
        #[cfg(feature = "geninfer_quadratic_map_solver")]
        "quadratic2" => apply_quadratic2_once(sig, coord_dims, coefficients),
        "translate" => apply_translate_once(sig, coord_dims, offset),
        _ => None,
    }
}

/// Compose `k` primitive STEPS (see `apply_generator_once`) — each step
/// re-derives its own bbox from the CURRENT signature, so this
/// self-renormalizes at every step (a rectangle's rotated bbox swaps
/// height/width; a reflected-twice axis returns to its start). `k <= 0`
/// is the identity (`Some(sig.to_vec())`) rather than a failure — callers
/// only ever pass `params` values (which should be positive), but this
/// stays honest rather than panicking on a stray `0`.
fn apply_generator_k(
    kind: &str,
    coord_dims: &[i64],
    sig: &[Value],
    modulus: i64,
    matrix: &[i64],
    offset: &[i64],
    k: i64,
) -> Option<Vec<Value>> {
    apply_generator_k_with_coefficients(kind, coord_dims, sig, modulus, matrix, &[], offset, k)
}

fn apply_generator_k_with_coefficients(
    kind: &str,
    coord_dims: &[i64],
    sig: &[Value],
    modulus: i64,
    matrix: &[i64],
    coefficients: &[i64],
    offset: &[i64],
    k: i64,
) -> Option<Vec<Value>> {
    let mut cur = sig.to_vec();
    for _ in 0..k.max(0) {
        cur = apply_generator_once(kind, coord_dims, &cur, modulus, matrix, coefficients, offset)?;
    }
    Some(cur)
}

/// Collect a set of part NAMES from an evaluated `exclude` / `codebook_scope`
/// Term value — the shared reader behind `apply_exclude` and `apply_scope`.
///
/// **Why this exists and why it is `str_shaped`, not `if let Value::Str`**
/// (ENGINE_ARGMAX_DETERMINISM_RESULTS.md §3; the `string_attr_or_panic`
/// precedent thirty lines above): both callers used to match `Value::Str`
/// ALONE, which silently dropped every `Value::Surface(SurfaceKind::Text, ..)`
/// element. `evaluate()` holds an immutable `&Interner`, so a Term-built
/// string can NEVER be a `Sym` — `StringConcat` / `StringSlice` /
/// `ToJsonString` / `FromJsonString` all evaluate to `Surface(Text)` by
/// construction. **A part named by a RULE was therefore unnameable in a scope
/// or an exclude**, and the failure was silent AND inverted in both
/// directions:
///
///   * `codebook_scope` — every element dropped ⇒ the set comes out empty ⇒
///     the `!is_empty()` guard leaves the codebook **UNRESTRICTED**. A decode
///     asking "score this ONE part" silently scored **the whole codebook's
///     maximum** instead. Measured, before this fix: scoping to `fractal`
///     (a part that cannot cover a single `cell` relation, true score **0**)
///     returned **36**, the global max.
///   * `exclude` — every element dropped ⇒ **nothing is excluded**. Measured,
///     before this fix: excluding `r00` returned **36** (r00 still in) where
///     the interned-`Str` spelling of the same exclude returned **14**.
///
/// The asymmetry that made it invisible: `load_parts` ALREADY accepts both
/// spellings (via `str_shaped`), so the part is present in the codebook and
/// scopeable by its interned name — only the rule-built spelling of that same
/// name fails, and it fails by returning a confident wrong number.
///
/// `Value::None` stays "no scope / no exclude" — that is DOCUMENTED,
/// load-bearing behaviour (`seeds/reflex_net.json`: a net with no
/// `basin_parts` decodes against the whole codebook). A present-but-not-
/// string-shaped ELEMENT is a different thing: it is malformed, and silence
/// there is exactly the disease `string_attr_or_panic` exists to end, so it
/// panics and names itself.
fn collect_part_names(
    val: &Value,
    ctx: &EvalCtx,
    which: &str,
) -> std::collections::HashSet<String> {
    let mut out: std::collections::HashSet<String> = std::collections::HashSet::new();
    let mut push = |v: &Value| match str_shaped(v, ctx.interner) {
        Some(s) => {
            out.insert(s.to_lowercase());
        }
        None => panic!(
            "ShapeDecode `{}`: element {:?} is not a string-shaped Value \
                 (expected Value::Str or Value::Surface(Text)). This reader used \
                 to DROP it silently, which does not fail closed: an all-dropped \
                 `codebook_scope` leaves the codebook UNRESTRICTED (a \
                 per-candidate score silently becomes the whole codebook's \
                 MAXIMUM) and an all-dropped `exclude` excludes NOTHING. Both \
                 are confident wrong numbers with no warning. Note that every \
                 Term-built string is Surface(Text), which is now accepted; a \
                 non-string element here means the graph or the Term is \
                 malformed, not that the entry is inapplicable.",
            which, v
        ),
    };
    match val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
            for v in val.iter() {
                push(v);
            }
        }
        // The documented "absent" case — no scope / no exclude. NOT an error.
        Value::None => {}
        other => push(other),
    }
    out
}

/// Apply an `exclude` Term (evaluates to a part name, or a collection of
/// part names) to a loaded part list — case-insensitive on the part's own
/// `name`, matching `_load_shape_signatures`'s dict-comprehension filter.
/// Shared by `ShapeDecode` and `TransformDecode` (both read the same
/// codebook shape); do not duplicate this per-caller.
fn apply_exclude(
    parts: &mut Vec<Part>,
    exclude_idx: Option<TermIdx>,
    arena: &TermArena,
    env: &mut Env,
    ctx: &mut EvalCtx,
) {
    let Some(ex_idx) = exclude_idx else { return };
    let ex_val = evaluate(arena, ex_idx, env, ctx);
    let excl = collect_part_names(&ex_val, ctx, "exclude");
    if !excl.is_empty() {
        parts.retain(|p| !excl.contains(&p.name.to_lowercase()));
    }
}

/// `apply_scope` — the inclusion twin of `apply_exclude`. RESTRICTS the
/// codebook to parts whose own `name` is in the `codebook_scope` set (a
/// Does this evaluated `codebook_scope` value DECLARE a scope?
///
/// `Value::None` does not — a scope was asked for but the attribute is absent,
/// which leaves the codebook unrestricted. That is load-bearing:
/// `seeds/reflex_net.json` passes `codebook_scope = Attr(rn, basin_parts)` while
/// no node in that seed carries a `basin_parts` attribute, so every net takes
/// this path.
///
/// EVERYTHING ELSE DOES, INCLUDING AN EMPTY COLLECTION. "This observer knows
/// nothing" is a declaration, not the absence of one, and it must restrict to
/// nothing. The previous behaviour let an empty scope fall through an
/// `!is_empty()` guard and leave the codebook UNRESTRICTED, so the
/// least-informed observer scored the whole codebook's maximum — silently, and
/// inverted. See `PER_OBSERVER_APERTURE.md`.
fn scope_is_declared(sc_val: &Value) -> bool {
    !matches!(sc_val, Value::None)
}

/// set of part names, case-insensitive), so a decode can run against a
/// PER-NET basin subset of a shared codebook (e.g. a reflex net's own
/// `basin_parts`) rather than every part of the type. An ABSENT scope, or one
/// evaluating to `Value::None`, leaves the codebook unrestricted — so a net with
/// no declared basin decodes against the whole codebook, and every existing
/// `ShapeDecode` without `codebook_scope` is unchanged.
///
/// A PRESENT-BUT-EMPTY scope restricts to NOTHING. It does not mirror
/// `apply_exclude`'s `!excl.is_empty()` guard, because scope and exclude are
/// DUALS: excluding an empty set is a no-op, scoping to an empty set is total
/// restriction.
fn apply_scope(
    parts: &mut Vec<Part>,
    scope_idx: Option<TermIdx>,
    arena: &TermArena,
    env: &mut Env,
    ctx: &mut EvalCtx,
) {
    let Some(sc_idx) = scope_idx else { return };
    let sc_val = evaluate(arena, sc_idx, env, ctx);
    // `Value::None` — a scope was ASKED FOR but the attribute is absent — stays
    // "no scope declared" and leaves the codebook unrestricted. That is the
    // load-bearing case and the only one: `seeds/reflex_net.json` passes
    // `codebook_scope = Attr(rn, basin_parts)` while NO node in that seed
    // carries a `basin_parts` attribute at all, so every net takes this path.
    if !scope_is_declared(&sc_val) {
        return;
    }
    // A PRESENT-BUT-EMPTY scope is a different statement: "this observer knows
    // nothing". It must restrict to nothing.
    //
    // This used to fall through the `!scope.is_empty()` guard below and leave
    // the codebook UNRESTRICTED, documented as "exactly mirroring
    // `apply_exclude`'s `!excl.is_empty()` guard". The mirroring was the error:
    // scope and exclude are DUALS, so their empty cases are not symmetric.
    // Excluding an empty set is correctly a no-op; scoping to an empty set is
    // TOTAL restriction. Conflating them made the least-informed observer the
    // most privileged one — measured, an agent scoped to `[]` scored the whole
    // codebook's maximum — which is the one inversion a social experiment
    // cannot tolerate, and it was silent. See PER_OBSERVER_APERTURE.md.
    let scope = collect_part_names(&sc_val, ctx, "codebook_scope");
    parts.retain(|p| scope.contains(&p.name.to_lowercase()));
}

fn load_codebook_cached(ctx: &mut EvalCtx, codebook_type: Sym) -> Arc<LoadedCodebook> {
    if let Some(cached) = ctx.shape_codebooks.get(&codebook_type) {
        crate::access_trace::note_helper_work(59, 1);
        return Arc::clone(cached);
    }
    crate::access_trace::note_helper_work(58, 1);
    let mut extra = FxHashMap::default();
    let mut next_id = u32::MAX;
    let parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    let loaded = Arc::new(LoadedCodebook::new(parts, extra));
    ctx.shape_codebooks
        .insert(codebook_type, Arc::clone(&loaded));
    loaded
}

/// Load the complete codebook before evaluating filters (preserving malformed
/// unrelated-entry behavior), then use the per-EvalCtx folded-name index to
/// select a scope without rescanning/copying every Part for each nested call.
fn scoped_parts_from_cached_codebook(
    loaded: &LoadedCodebook,
    exclude_idx: Option<TermIdx>,
    scope_idx: Option<TermIdx>,
    arena: &TermArena,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Vec<Part> {
    let excludes = exclude_idx
        .map(|idx| evaluate(arena, idx, env, ctx))
        .map(|value| collect_part_names(&value, ctx, "exclude"))
        .unwrap_or_default();
    let scope_value = scope_idx
        .map(|idx| evaluate(arena, idx, env, ctx))
        .unwrap_or(Value::None);
    let scope = if scope_is_declared(&scope_value) {
        Some(collect_part_names(&scope_value, ctx, "codebook_scope"))
    } else {
        None
    };
    let mut parts = loaded.select(scope.as_ref());
    if !excludes.is_empty() {
        parts.retain(|part| !excludes.contains(&part.name.to_lowercase()));
    }
    parts
}

/// One `plan` entry — the Rust twin of `compose_design_for_goal`'s
/// per-step dict (`step`/`part`/`kind`/`source`/`shape_fit`/`covers`/`why`).
#[derive(Clone)]
struct PlanStep {
    step: i64,
    part_val: Value,
    kind_val: Value,
    source_val: Value,
    shape_fit: i64,
    covers: Vec<Value>,
    why: String,
}

impl PlanStep {
    fn to_value(&self) -> Value {
        let covers: SmallVec<[Value; 4]> = self.covers.iter().cloned().collect();
        Value::Dict(Arc::from(vec![
            (surf("step"), Value::Int(self.step)),
            (surf("part"), self.part_val.clone()),
            (surf("kind"), self.kind_val.clone()),
            (surf("source"), self.source_val.clone()),
            (surf("shape_fit"), Value::Int(self.shape_fit)),
            (surf("covers"), Value::Tuple(Arc::new(covers))),
            (surf("why"), surf_string(self.why.clone())),
        ]))
    }
}

/// Beam state — the Rust twin of Python's `(plan, used, residual,
/// total_fit)` 4-tuple.
#[derive(Clone)]
struct BeamState {
    plan: Vec<PlanStep>,
    used: std::collections::HashSet<String>,
    residual: Vec<Value>,
    total_fit: i64,
}

/// The `RelationCue` axis index — `{relation-tuple (as owned strings) -> cue
/// name}` — the Rust twin of `domains/reflective_faculty.py::
/// _relation_cue_index`. Read once per `ShapeDecode` eval (RELATION_CUE_TOKEN_
/// COLLISION_RESULTS.md, Q1/Q4c): 52 held cues, cheap relative to the
/// O(residual x parts) search this feeds. Every consumer of the RelationCue
/// lexicon (`author_signature`'s scan, hand-authored `math_capability_shapes.json`
/// rows) emits relation tuples copied VERBATIM from a `RelationCue.relation`, so
/// this index is how `shape_fit` recognises WHICH axis a row belongs to,
/// independent of its position in whatever list it arrived in — mirrors the
/// discipline `_shared_shape` already applies at the Python layer. Empty when
/// the graph holds no `RelationCue` nodes (e.g. a minimal test graph): `shape_fit`
/// then degrades to zero shared axes for every part, never to the old
/// un-anchored positional zip.
fn load_relation_cue_index(ctx: &EvalCtx) -> FxHashMap<Vec<String>, String> {
    let mut idx = FxHashMap::default();
    let Some(cue_type) = ctx.interner.lookup("RelationCue") else {
        return idx;
    };
    for nid in ctx.graph.nodes_of_type(cue_type) {
        crate::access_trace::note_helper_work(50, 1);
        trace_scanned_node(ctx, nid);
        let node = ctx.graph.node(nid);
        let mut name: Option<String> = None;
        let mut rel: Option<Value> = None;
        for (k, v) in node.attrs.iter() {
            match ctx.interner.resolve(*k) {
                "name" => name = td_val_to_string(v, ctx.interner),
                "relation" => rel = Some(v.clone()),
                _ => {}
            }
        }
        let (Some(name), Some(rel_val)) = (name, rel) else {
            continue;
        };
        // `relation` is seeded as a JSON string (`relation_vocabulary.json`
        // stores it `json.dumps`'d); accept a native Tuple/List too, the same
        // native-or-JSON-string duality `load_parts` already accepts for
        // `signature`.
        let row: Vec<String> = match &rel_val {
            Value::Tuple(t) | Value::List(t) => t
                .iter()
                .filter_map(|v| td_val_to_string(v, ctx.interner))
                .collect(),
            other => {
                let Some(text) = td_val_to_string(other, ctx.interner) else {
                    continue;
                };
                match serde_json::from_str::<serde_json::Value>(&text) {
                    Ok(serde_json::Value::Array(items)) => items
                        .iter()
                        .filter_map(|it| it.as_str().map(|s| s.to_string()))
                        .collect(),
                    _ => continue,
                }
            }
        };
        if row.is_empty() {
            continue;
        }
        idx.insert(row, name);
    }
    idx
}

/// PANIC-SAFE string resolution for a relation-row leaf — the SAME "index out
/// of bounds" hazard `resolve_scoped_output` (below) already closes for
/// `TransformDecode`'s output path, now needed here too: a held part's parsed
/// `signature` (`json_to_value_scoped`/`local_sym`) may contain a LOCALLY
/// fabricated placeholder `Sym` for a string novel to this graph, and
/// `Interner::resolve` panics on a Sym it never issued. Check `extra_rev`
/// FIRST (the placeholder's own text), THEN fall back to a real interner
/// resolve — mirrors `resolve_scoped_output`'s own order exactly.
fn shape_decode_val_to_string(
    v: &Value,
    interner: &Interner,
    extra_rev: &FxHashMap<Sym, String>,
) -> Option<String> {
    match v {
        Value::Str(s) => match extra_rev.get(s) {
            Some(text) => Some(text.clone()),
            None => Some(interner.resolve(*s).to_string()),
        },
        Value::Surface(SurfaceKind::Text, bytes) => {
            std::str::from_utf8(bytes).ok().map(|s| s.to_string())
        }
        _ => None,
    }
}

/// A relation-row `Value` (a Tuple/List of Str/Surface leaves) as an owned
/// `Vec<String>` key, for lookup against `load_relation_cue_index`'s index.
/// `None` for a non-tuple row or a row with a non-string leaf (defensive;
/// relation-systems are always flat string tuples in practice).
fn shape_decode_row_key(
    row: &Value,
    interner: &Interner,
    extra_rev: &FxHashMap<Sym, String>,
) -> Option<Vec<String>> {
    let (Value::Tuple(t) | Value::List(t)) = row else {
        return None;
    };
    let mut out = Vec::with_capacity(t.len());
    for v in t.iter() {
        out.push(shape_decode_val_to_string(v, interner, extra_rev)?);
    }
    Some(out)
}

/// `shape_fit` — `FixedCount(AntiUnify(...))`, AXIS-ANCHORED
/// (RELATION_CUE_TOKEN_COLLISION_RESULTS.md, Q1/Q4c) WHEN the RelationCue
/// vocabulary is actually in play, positional (UNCHANGED) otherwise.
///
/// `ShapeDecode`'s codebook is a SHARED pool (`codebook_type` defaults to the
/// one node type `ShapeSignature` for every domain — the math/faculty
/// cognitive-shape pool, the ink stroke/substroke pool, and others all live in
/// it together, distinguished only by their own `kind` attr, never by node
/// type; `test_codebook_partition_migrated.py` names this explicitly). Only
/// the cognitive-shape domain's rows are ever copied verbatim from a held
/// `RelationCue.relation` (`author_signature`, `math_capability_shapes.json`);
/// a stroke/substroke signature's rows are `seg`/`pose_*` relations that were
/// NEVER meant to address the `RelationCue` lexicon at all and match NO cue,
/// ever — for that domain the OLD position-aligned comparison is not the
/// collision bug, it is the ONLY signal `shape_fit` has, and axis-anchoring
/// unconditionally would zero it out (measured regression: FIRST-FIX ATTEMPT
/// silently broke `test_substroke_arity_disjointness_is_the_only_thing_
/// separating_it_from_stroke` and 4 composer/codebook tests this way — see
/// RELATION_CUE_TOKEN_COLLISION_RESULTS.md §7 for the honest record).
///
/// The discriminator: if NEITHER side has even ONE row that maps to a held
/// `RelationCue` (`by_name_a` and `by_name_b` both empty), this pair is
/// outside the cue vocabulary entirely — fall back to the exact pre-fix
/// positional `AntiUnify([residual[..n], psig[..n]])`, byte-identical. The
/// moment EITHER side has a cue-matched row, this pair is inside the
/// cognitive-shape domain the collision bug lives in, and pairing switches to
/// cue-identity: a row from `residual` is paired with a row from `psig` only
/// when BOTH are byte-identical to the SAME held `RelationCue`'s relation
/// tuple (`cue_of`, looked up via `shape_decode_row_key`) — i.e. the same
/// NAMED cue fired for both, never merely because two rows share a list
/// index (mirrors `domains/reflective_faculty.py::_shared_shape`'s fix,
/// AUTHOR_SIGNATURE_AXIS_ANCHOR_RESULTS.md, at the Rust layer this time —
/// confirmed live via `scripts/shape_decode_shape_fit_collision_probe.py`:
/// two parts with IDENTICAL real coverage got DIFFERENT `shape_fit` scores
/// from an accidental cross-cue token collision in an uncovered, unrelated
/// row, eliminated by this fix). A row that matches no held cue even inside
/// a cue-anchored comparison (a `CapabilityAxis`-residual bare predicate, or
/// a rare hand-authored seed row that isn't an exact cue-template copy)
/// contributes no axis and is excluded, honestly — never force-aligned by
/// position.
fn shape_fit(
    residual: &[Value],
    psig: &[Value],
    wild: &Value,
    cue_of: &FxHashMap<Vec<String>, String>,
    interner: &Interner,
    extra_rev: &FxHashMap<Sym, String>,
) -> i64 {
    use std::collections::BTreeMap;
    let mut by_name_a: BTreeMap<&str, &Value> = BTreeMap::new();
    for row in residual {
        if let Some(key) = shape_decode_row_key(row, interner, extra_rev) {
            if let Some(nm) = cue_of.get(&key) {
                by_name_a.entry(nm.as_str()).or_insert(row);
            }
        }
    }
    let mut by_name_b: BTreeMap<&str, &Value> = BTreeMap::new();
    for row in psig {
        if let Some(key) = shape_decode_row_key(row, interner, extra_rev) {
            if let Some(nm) = cue_of.get(&key) {
                by_name_b.entry(nm.as_str()).or_insert(row);
            }
        }
    }
    if by_name_a.is_empty() && by_name_b.is_empty() {
        // OUTSIDE the RelationCue vocabulary entirely — the pre-fix
        // positional comparison, untouched (see doc above).
        let n = residual.len().min(psig.len());
        if n == 0 {
            return 0;
        }
        crate::scale_audit::term_units(n as u64);
        let a: SmallVec<[Value; 4]> = residual[..n].iter().cloned().collect();
        let b: SmallVec<[Value; 4]> = psig[..n].iter().cloned().collect();
        let insts = [Value::Tuple(Arc::new(a)), Value::Tuple(Arc::new(b))];
        let anti = anti_unify_values(&insts, wild);
        return fixed_count_value(&anti, wild);
    }
    let a: SmallVec<[Value; 4]> = by_name_a
        .iter()
        .filter(|(nm, _)| by_name_b.contains_key(*nm))
        .map(|(_, v)| (*v).clone())
        .collect();
    if a.is_empty() {
        return 0;
    }
    let b: SmallVec<[Value; 4]> = by_name_b
        .iter()
        .filter(|(nm, _)| by_name_a.contains_key(*nm))
        .map(|(_, v)| (*v).clone())
        .collect();
    // SCALE AUDIT — interior comparison units (`scale_audit.rs`, T section).
    // `a.len()` shared-axis rows are anti-unified. Charged ONCE with the
    // count, not per position: an atomic per iteration would dominate the
    // work it measures.
    crate::scale_audit::term_units(a.len() as u64);
    let insts = [Value::Tuple(Arc::new(a)), Value::Tuple(Arc::new(b))];
    let anti = anti_unify_values(&insts, wild);
    fixed_count_value(&anti, wild)
}

/// Does some relation in the part's OWN signature cover `goal_relation`?
/// Mirrors `_covers_relation`: same-length + same-predicate (position 0)
/// prefilter, then the held `Covers` Term decides.
///
/// Two semantics (see the `ShapeDecode::wild_objects` doc on `term.rs`):
/// literal (`wild_objects=false`, the composer's default, UNCHANGED) —
/// `Covers(pattern=goal_relation, instance=step)`, the GOAL is the
/// pattern, the part's relation is the candidate instance; a WILD in the
/// goal auto-matches. Wildcarded (`wild_objects=true`, `induce_concern`'s
/// pre-migration `_held_coverage_patterns` semantics) — `part_sig` has
/// ALREADY been transformed (non-predicate slots -> wild) by the caller,
/// and the pattern/instance roles FLIP: `Covers(pattern=step,
/// instance=goal_relation)`, because `covers_value` only auto-matches a
/// wild that appears on the PATTERN (first) side — wildcarding the
/// part's own relation only takes effect when it is passed there
/// (exactly the pre-migration `_covers(agent, wpat, obs)` call order).
fn covers_relation(
    part_sig: &[Value],
    goal_relation: &Value,
    wild: &Value,
    wild_objects: bool,
) -> bool {
    let (Value::Tuple(goal_t) | Value::List(goal_t)) = goal_relation else {
        return false;
    };
    if goal_t.is_empty() {
        return false;
    }
    // SCALE AUDIT — interior comparison units (`scale_audit.rs`, T section).
    // THIS IS THE O(N_residual x N_part) CORE OF DECODE, and the work that was
    // invisible to every graph-level counter: it happens inside ONE Term
    // evaluation, over an ATTRIBUTE, touching no node and no edge. `scanned`
    // counts steps ACTUALLY examined, so the early return on a hit is reflected
    // rather than papered over — a counter that charged `part_sig.len()`
    // regardless would over-report exactly where decode is cheapest.
    let mut scanned: u64 = 0;
    for step in part_sig {
        scanned += 1;
        let (Value::Tuple(step_t) | Value::List(step_t)) = step else {
            continue;
        };
        if step_t.len() != goal_t.len() {
            continue;
        }
        if step_t[0] != goal_t[0] {
            continue;
        }
        let ok = if wild_objects {
            covers_value(step, goal_relation, wild)
        } else {
            covers_value(goal_relation, step, wild)
        };
        if ok {
            crate::scale_audit::term_units(scanned);
            return true;
        }
    }
    crate::scale_audit::term_units(scanned);
    false
}

/// `_score_part_for_residual` twin: `(shape_fit, covered)` where `covered`
/// is the subset of `residual` this part's signature covers. `psig` is
/// the (possibly already wildcard-transformed, see `wildcard_signature`)
/// scoring signature for this part; `wild_objects` only changes the
/// `Covers` pattern/instance role inside `covers_relation` (see its doc)
/// — `shape_fit`'s `AntiUnify` is symmetric, so the pre-transformed
/// `psig` alone is enough there.
fn score_part_for_residual(
    residual: &[Value],
    psig: &[Value],
    wild: &Value,
    wild_objects: bool,
    cue_of: &FxHashMap<Vec<String>, String>,
    interner: &Interner,
    extra_rev: &FxHashMap<Sym, String>,
) -> (i64, Vec<Value>) {
    let fit = shape_fit(residual, psig, wild, cue_of, interner, extra_rev);
    let covered: Vec<Value> = residual
        .iter()
        .filter(|rel| covers_relation(psig, rel, wild, wild_objects))
        .cloned()
        .collect();
    (fit, covered)
}

/// The `wild_objects` transform: for each relation in `psig`, keep slot 0
/// (the predicate) and replace every other slot with `wild` — the
/// predicate-skeleton-only view `induce_concern`'s pre-migration
/// `_held_coverage_patterns` built before scoring. Non-tuple entries pass
/// through unchanged (defensive; relation-systems are always tuples in
/// practice).
fn wildcard_signature(psig: &[Value], wild: &Value) -> Vec<Value> {
    psig.iter()
        .map(|rel| match rel {
            Value::Tuple(t) | Value::List(t) if !t.is_empty() => {
                let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(t.len());
                out.push(t[0].clone());
                for _ in 1..t.len() {
                    out.push(wild.clone());
                }
                rel.reseq(out) // KIND-PRESERVING (see `Value::reseq`)
            }
            other => other.clone(),
        })
        .collect()
}

fn wall(reason: &str) -> Value {
    Value::Dict(Arc::from(vec![
        (surf("authored"), Value::Bool(false)),
        (surf("reason"), surf(reason)),
    ]))
}

/// Pull a single named key out of the result Dict — what a `field`
/// selection resolves to. `"covered_by"` is a DERIVED field (not a real
/// Dict key: the single covering part's name when the decode fully
/// covers with a one-part plan, else `None`), supplied by the caller;
/// every other name is looked up among the Dict's `Value::Surface(Text,
/// ..)` keys (built by `surf`) by byte-comparing against `field`'s
/// resolved text. An unknown field name (or a field requested off a
/// wall dict that doesn't carry it) is `Value::None` — honest absence,
/// not an error.
fn select_field(dict: &Value, field_name: &str, covered_by: Option<Value>) -> Value {
    if field_name == "covered_by" {
        return covered_by.unwrap_or(Value::None);
    }
    if let Value::Dict(pairs) = dict {
        for (k, v) in pairs.iter() {
            if let Value::Surface(SurfaceKind::Text, bytes) = k {
                if bytes.as_ref() == field_name.as_bytes() {
                    return v.clone();
                }
            }
        }
    }
    Value::None
}

/// Select a field from a cached full SD report. `covered_by` is the sole
/// derived ShapeDecode field, so reconstruct it from the cached plan instead
/// of rerunning the beam search.
pub(crate) fn select_cached_field(dict: &Value, field: Sym, interner: &Interner) -> Value {
    if field == Sym::default() {
        return dict.clone();
    }
    let name = interner.resolve(field);
    if name != "covered_by" {
        return select_field(dict, name, None);
    }
    let residual = select_field(dict, "residual", None);
    let plan = select_field(dict, "plan", None);
    if !residual.is_empty() || plan.len() != 1 {
        return Value::None;
    }
    let Some(first) = plan.iter().next() else {
        return Value::None;
    };
    select_field(first, "part", None)
}

/// Route a finished result through `field` selection (a no-op when
/// `field` is the empty/default Sym — "return the whole Dict").
fn finish(result: Value, field: Sym, interner: &Interner, covered_by: Option<Value>) -> Value {
    if field == Sym::default() {
        return result;
    }
    select_field(&result, interner.resolve(field), covered_by)
}

/// GAMMA_SEARCH_COMPLETENESS_FIXES.md Bug 2's default total-expansion
/// budget (the `SynthEnumerate::DEFAULT_MAX_CANDIDATES` / `ProgEval`
/// `DEFAULT_FUEL` idiom, sized for THIS search: the two production configs
/// in `seeds/*.json` are `cand_k<=1` (single-step, real-time humanoid/
/// vision/embodied callers — unaffected either way, see below) and
/// `cand_k in {2,3}, max_steps=8` (reflective_faculty's composer default
/// and `seeds/shape_decode_loop.json`/`reflex_net.json`/
/// `program_synthesis.json`/`meaning_inference.json`). The exhaustive
/// worst case for the latter (every candidate distinct, dedup never
/// collapsing anything) is `sum_{k=1..8} cand_k^k` = 510 (`cand_k=2`) or
/// 9840 (`cand_k=3`) total state expansions — 20_000 gives that
/// configuration room to run to genuine exhaustion (no budget cutoff) with
/// slack for a modestly larger `cand_k`, while still bounding a runaway
/// caller (e.g. a much larger `cand_k`/`max_steps`) to an honest
/// `budget_exhausted` result instead of an unbounded search.
pub(crate) const DEFAULT_SD_BUDGET: i64 = 20_000;

/// Evaluate `ShapeDecode` — the dequantizer. See module docs for the
/// interner constraint this respects, and `term.rs`'s `ShapeDecode`
/// variant doc for the algorithm summary. Faithful to
/// `compose_design_for_goal` field-for-field (minus `provenance`, which
/// the Python shim adds), with an optional `field` selector (see
/// `select_field`).
///
/// GAMMA_SEARCH_COMPLETENESS_FIXES.md Bug 2 — cost-ordered, BUDGETED search
/// replaces the old fixed-width beam prune. `scripts/probe_beam_completeness.py`
/// (live-verified, cited in full in the ceiling-probe doc and the fix
/// writeup) demonstrated the old shape's failure mode directly: a
/// classic greedy-set-cover adversarial construction where the top-`beam`
/// SURVIVOR state after step 1 is a locally-better-looking dead end, and
/// the states that would have reached a fully-covering plan were
/// discarded — permanently, since a discarded `BeamState` never
/// re-enters `frontier` — before they got a chance to be expanded on step
/// 2. `beam=1` returned an INCOMPLETE plan flagged `authored: true`
/// identically to a genuinely complete one; `beam>=2` found the complete
/// plan over the exact same codebook and goal.
///
/// The fix, following this repo's own `SynthEnumerate` precedent
/// (`synth_enumerate.rs`, `PROGRAM_SYNTHESIS_P4A_NOTES.md`: "`beam`
/// (legacy unguided width cap) — NO, dropped — dead weight the guided
/// path superseded"): stop discarding states by WIDTH. Every
/// non-duplicate candidate state survives to the next round — the
/// existing `(coverage DESC, total_fit DESC)` sort + `(residual,
/// used)`-keyed dedup are UNCHANGED and still order/collapse the
/// frontier, so expansion still happens cheapest/best-first (the same
/// Occam-cost-ordering the rest of the sd loop's ladder is built on) —
/// bounded instead by a single, total, whole-search expansion BUDGET
/// (`budget`/`DEFAULT_SD_BUDGET`, the fueled-interpreter idiom already
/// used by `ProgEval`/`SynthEnumerate`). When the budget is exhausted
/// before the search would have stopped on its own (frontier naturally
/// empty, or full coverage reached), the result is HONESTLY flagged
/// (`budget_exhausted: true`) rather than looking identical to a
/// genuinely-exhausted-within-`max_steps` result — a caller can now tell
/// "this is the best plan reachable in the declared cost class" from
/// "the search gave up partway, here is its best partial."
///
/// `beam` itself is kept on the wire and in the output Dict (informational
/// / back-compat only — every existing seed's `"beam": N` still parses and
/// still reports) but no longer truncates anything. This is a deliberate,
/// zero-behavioural-difference no-op for every callsite that matters most:
/// `cand_k<=1` callers (`embodied_motor_bootstrap.json`,
/// `humanoid_adaptation.json`, `vision_*.json`, `somatomotor_waves.json`,
/// `embodied_physics_proposal.json`, `embodied_development.json` — all
/// real-time/hot-loop, all `beam=1, max_steps=1, cand_k=1`) generate AT
/// MOST one candidate total regardless of pruning (`best` is updated at
/// candidate-CREATION time, before any pruning ever runs — see below), so
/// this change cannot alter their output or their cost. For the
/// `max_steps=8` callers (`reflex_net.json`, `shape_decode_loop.json`,
/// `program_synthesis.json`, `meaning_inference.json`,
/// `prog_construction_loop.json`), see `DEFAULT_SD_BUDGET`'s doc for why
/// the default keeps their exhaustive worst case well inside budget.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_shape_decode(
    arena: &TermArena,
    goal_idx: TermIdx,
    codebook_type: Sym,
    exclude_idx: Option<TermIdx>,
    scope_idx: Option<TermIdx>,
    beam: i64,
    max_steps: i64,
    cand_k: i64,
    budget: i64,
    field: Sym,
    wild: Sym,
    wild_objects: bool,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_SHAPE_DECODE);
    let wild_val = wild_value(wild);

    // Codebook: read parts, then apply `exclude` (case-insensitive on the
    // part's own name), preserving first-occurrence order throughout —
    // matches `_load_shape_signatures` + the dict-comprehension filter.
    let (parts, extra) = if scope_idx.is_some()
        && crate::access_trace::shape_codebook_cache_enabled()
    {
        let loaded = load_codebook_cached(ctx, codebook_type);
        let parts =
            scoped_parts_from_cached_codebook(&loaded, exclude_idx, scope_idx, arena, env, ctx);
        (parts, loaded.extra.clone())
    } else {
        let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
        let mut next_id: u32 = u32::MAX;
        let mut parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
        apply_exclude(&mut parts, exclude_idx, arena, env, ctx);
        apply_scope(&mut parts, scope_idx, arena, env, ctx);
        (parts, extra)
    };

    if parts.is_empty() {
        return finish(
            wall("no held parts (shape-signatures) to compose from"),
            field,
            ctx.interner,
            None,
        );
    }

    // Goal: evaluated through the ordinary Term path — every Str leaf is
    // a REAL Sym, safe to place directly in the output.
    let goal_val = evaluate(arena, goal_idx, env, ctx);
    let goal: Vec<Value> = match &goal_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
            goal_val.iter().cloned().collect()
        }
        _ => Vec::new(),
    };
    if goal.is_empty() {
        return finish(
            wall("no goal signature to compose toward"),
            field,
            ctx.interner,
            None,
        );
    }
    let n_goal = goal.len();

    // The per-part SCORING signature: `part.sig` verbatim by default
    // (composer parity, unchanged); `wild_objects=true` wildcards every
    // non-predicate slot first (see `wildcard_signature`'s doc) — this is
    // the ONLY place the scoring input differs, computed once (parts
    // don't change across beam steps).
    let scoring_sigs: Vec<Vec<Value>> = if wild_objects {
        parts
            .iter()
            .map(|p| wildcard_signature(&p.sig, &wild_val))
            .collect()
    } else {
        parts.iter().map(|p| p.sig.clone()).collect()
    };

    // RELATION_CUE_TOKEN_COLLISION_RESULTS.md Q1/Q4c: the axis-anchor index
    // `shape_fit` needs, read once (52 held cues; the graph doesn't change
    // across beam steps). Built AFTER `apply_exclude`/`apply_scope` (which need
    // `ctx` mutably) — `ctx` is only read immutably from here on.
    let cue_of = load_relation_cue_index(ctx);
    // `extra_rev`: the same "resolve a locally-fabricated placeholder Sym back
    // to its own text" map every other Term in this file builds after
    // `load_parts` (see `resolve_scoped_output`'s doc) — needed so `shape_fit`
    // can safely stringify a `psig` row's tokens (parsed via
    // `json_to_value_scoped`/`local_sym`, which may carry placeholder Syms the
    // real interner never issued) without panicking.
    let extra_rev: FxHashMap<Sym, String> = extra.iter().map(|(k, v)| (*v, k.clone())).collect();

    let cand_w = cand_k.max(0) as usize;
    // Bug 2's budget: total state EXPANSIONS across the whole search
    // (one unit per candidate state created, i.e. per (state, part) pairing
    // that survives the per-state `cand_w` cap) — see `DEFAULT_SD_BUDGET`'s
    // doc. `beam` is deliberately NOT read here any more (see
    // `eval_shape_decode`'s doc): it is preserved on the wire/output only.
    let sd_budget: u64 = if budget <= 0 {
        DEFAULT_SD_BUDGET as u64
    } else {
        budget as u64
    };
    let mut expansions: u64 = 0;
    let mut budget_exhausted = false;

    let start = BeamState {
        plan: Vec::new(),
        used: std::collections::HashSet::new(),
        residual: goal.clone(),
        total_fit: 0,
    };
    let mut frontier: Vec<BeamState> = vec![start.clone()];
    let mut best: BeamState = start;

    'search: for _ in 0..max_steps.max(0) {
        let mut nxt: Vec<BeamState> = Vec::new();
        for state in &frontier {
            if state.residual.is_empty() {
                continue;
            }
            // Score every unused part vs this state's residual; keep only
            // parts that cover something (a part covering nothing doesn't
            // advance the goal).
            let mut scored: Vec<(usize, i64, &Part, Vec<Value>)> = Vec::new();
            for (part, sig) in parts.iter().zip(scoring_sigs.iter()) {
                if state.used.contains(&part.name) {
                    continue;
                }
                crate::access_trace::note_helper_work(52, 1);
                let (fit, covered) = score_part_for_residual(
                    &state.residual,
                    sig,
                    &wild_val,
                    wild_objects,
                    &cue_of,
                    ctx.interner,
                    &extra_rev,
                );
                if covered.is_empty() {
                    continue;
                }
                scored.push((covered.len(), fit, part, covered));
            }
            // Stable sort by (-ncov, -fit) — `sort_by` is a stable sort in
            // Rust, matching Python's stable `list.sort`. This is the
            // COST-ORDERING (cheapest/best candidate first) that makes the
            // budget cutoff below spend its remaining expansions on the
            // most promising continuations first, not an arbitrary subset.
            scored.sort_by(|a, b| b.0.cmp(&a.0).then(b.1.cmp(&a.1)));

            for (ncov, fit, part, covered) in scored.into_iter().take(cand_w) {
                if expansions >= sd_budget {
                    // Honest partial result: stop generating new candidates.
                    // Every candidate already generated already had its
                    // chance to become `best` (below), so nothing already
                    // found is lost — only further exploration is foregone.
                    budget_exhausted = true;
                    break 'search;
                }
                expansions += 1;
                crate::access_trace::note_helper_work(51, 1);
                let why = format!(
                    "the held shape-matcher rated '{}' fit {} and its Covers Term accepts {} residual relation(s)",
                    part.name, fit, ncov
                );
                let mut nplan = state.plan.clone();
                nplan.push(PlanStep {
                    step: nplan.len() as i64 + 1,
                    part_val: part.name_val.clone(),
                    kind_val: part.kind_val.clone(),
                    source_val: part.source_val.clone(),
                    shape_fit: fit,
                    covers: covered.clone(),
                    why,
                });
                let nresid: Vec<Value> = state
                    .residual
                    .iter()
                    .filter(|rel| !covered.contains(rel))
                    .cloned()
                    .collect();
                let mut nused = state.used.clone();
                nused.insert(part.name.clone());
                let nstate = BeamState {
                    plan: nplan,
                    used: nused,
                    residual: nresid,
                    total_fit: state.total_fit + fit,
                };

                let cov_now = n_goal - nstate.residual.len();
                let best_cov = n_goal - best.residual.len();
                if (cov_now, nstate.total_fit) > (best_cov, best.total_fit) {
                    best = nstate.clone();
                }
                nxt.push(nstate);
            }
        }
        if nxt.is_empty() {
            break;
        }
        // Sort by (coverage DESC, total_fit DESC), dedupe on (residual,
        // used-set) — UNCHANGED. Bug 2's fix: no width truncation after
        // this. Every deduped state survives to the next round (still in
        // cost-order, so a future budget cutoff still explores best-first);
        // only the total expansion BUDGET above bounds the search now.
        nxt.sort_by(|a, b| {
            let acov = n_goal - a.residual.len();
            let bcov = n_goal - b.residual.len();
            bcov.cmp(&acov).then(b.total_fit.cmp(&a.total_fit))
        });
        let mut seen: std::collections::HashSet<(Vec<Value>, std::collections::BTreeSet<String>)> =
            std::collections::HashSet::new();
        let mut pruned: Vec<BeamState> = Vec::new();
        for st in nxt {
            let key = (st.residual.clone(), st.used.iter().cloned().collect());
            if !seen.insert(key) {
                continue;
            }
            pruned.push(st);
        }
        frontier = pruned;
        if frontier.iter().all(|st| st.residual.is_empty()) {
            break;
        }
    }

    let BeamState {
        plan,
        residual,
        total_fit,
        ..
    } = best;
    let covered: Vec<Value> = goal
        .iter()
        .filter(|rel| !residual.contains(rel))
        .cloned()
        .collect();
    // `induce_concern`'s covered-branch convenience form: the single part
    // that covered everything, only meaningful for a fully-covering
    // ONE-part plan.
    let covered_by = if residual.is_empty() && plan.len() == 1 {
        Some(plan[0].part_val.clone())
    } else {
        None
    };
    let plan_vals: SmallVec<[Value; 4]> = plan.iter().map(PlanStep::to_value).collect();
    let ordered_parts: SmallVec<[Value; 4]> = plan.iter().map(|p| p.part_val.clone()).collect();
    let covered_tuple: SmallVec<[Value; 4]> = covered.iter().cloned().collect();
    let residual_tuple: SmallVec<[Value; 4]> = residual.iter().cloned().collect();

    let result = Value::Dict(Arc::from(vec![
        (surf("authored"), Value::Bool(!plan.is_empty())),
        (surf("plan"), Value::Tuple(Arc::new(plan_vals))),
        (surf("ordered_parts"), Value::Tuple(Arc::new(ordered_parts))),
        (surf("covered"), Value::Tuple(Arc::new(covered_tuple))),
        (surf("residual"), Value::Tuple(Arc::new(residual_tuple))),
        (surf("goal_relations"), Value::Int(n_goal as i64)),
        (
            surf("covered_count"),
            Value::Int((n_goal - residual.len()) as i64),
        ),
        (surf("total_fit"), Value::Int(total_fit)),
        (surf("beam"), Value::Int(beam)),
        // GAMMA_SEARCH_COMPLETENESS_FIXES.md Bug 2 — the honesty signal:
        // true iff the total-expansion budget was exhausted before the
        // search would otherwise have stopped on its own (frontier
        // naturally empty, or full coverage already reached). `authored`
        // (above) only ever meant "produced at least one step" — it was
        // never a completeness certificate, before or after this fix — so
        // this is an ADDITIVE field, not a redefinition: a caller that
        // wants to distinguish "genuinely as-good-as-this-search-gets" from
        // "gave up partway, here is its best partial" now can.
        (surf("budget_exhausted"), Value::Bool(budget_exhausted)),
    ]));
    finish(result, field, ctx.interner, covered_by)
}

/// One dimension's transform, as computed for a single candidate held
/// part — the internal twin of the output Dict's `{dim, kind, delta}`
/// entries (see `TransformDecode`'s doc in `term.rs`). `pred` is `Some`
/// ONLY for a per-predicate SPLIT dimension (see `build_candidate`'s
/// two-tier pooling doc): a numeric shift confined to one predicate
/// family at a slot index other relation types also occupy — without
/// the `pred` key the entry would be ambiguous (which relations does
/// the slot-`dim` delta apply to?). Tier-1 (globally-uniform) entries
/// carry `pred: None` and emit EXACTLY the committed `{dim,kind,delta}`
/// Dict — byte-identical output for every case the old
/// raw-slot-uniform semantics explained.
struct DimTransform {
    dim: i64,
    kind: &'static str,
    delta: Value,
    pred: Option<Value>,
}

impl DimTransform {
    fn to_value(&self) -> Value {
        let mut pairs = vec![
            (surf("dim"), Value::Int(self.dim)),
            (surf("kind"), surf(self.kind)),
            (surf("delta"), self.delta.clone()),
        ];
        if let Some(p) = &self.pred {
            pairs.push((surf("pred"), p.clone()));
        }
        Value::Dict(Arc::from(pairs))
    }
}

/// One held part evaluated against the (already canonically-sorted)
/// observation — the internal twin of a `TransformDecode` "candidate".
/// `eligible` candidates are the only ones considered for `base`
/// selection; a predicate/arity mismatch anywhere, or a relation-count
/// mismatch, disqualifies a part before it is even added to this list
/// (see `eval_transform_decode`'s `'parts` loop).
struct Candidate {
    name: String,
    name_val: Value,
    /// On SUCCESS: the transform entries' dim list, parallel to
    /// `transforms` (duplicate slot indices possible when two predicates
    /// transform separately at the same per-relation slot — tier-2 split,
    /// see `build_candidate`). On FAILURE: the raw differing-slot list.
    /// Empty = exact match (`identity`). Either way the caller's
    /// `transforms.len() == dims_needed.len()` success check holds its
    /// contract (equal on success and identity, unequal on failure).
    dims_needed: Vec<i64>,
    /// Observation-side relations (canonical order) that differ from
    /// their aligned held relation at all — used for `residual_unexplained`
    /// and to rank the "closest" candidate when nothing explains.
    mismatches: Vec<Value>,
    /// Populated only when every needed dimension resolved to one
    /// uniform delta (numeric shift or a consistent, non-identity
    /// symbolic substitution function) within `max_dims`.
    transforms: Vec<DimTransform>,
}

/// Resolve a locally-fabricated placeholder `Sym` (see `local_sym`) back to
/// an interner-safe `Value` before it is placed in `TransformDecode`'s
/// output. A held part's parsed signature (`json_to_value_scoped`) may
/// contain such placeholders for strings novel to this graph — the module
/// doc requires that parsed-signature content NEVER reach the output
/// directly, because `interner.resolve`/`value_to_py` panics on a Sym it
/// never issued (the "index out of bounds" bug this closes). The
/// symbolic-substitution branch below is the one place a held-side value
/// (a `from` entry) is placed in the output, so it is the one place this
/// must run. Real Syms (interned elsewhere, found via `Interner::lookup`
/// inside `local_sym`) are untouched; a placeholder is rewritten to
/// `Value::Surface(Text, ..)`, the same side-channel `surf`/`surf_string`
/// already use for output text that needs no interner lookup at all.
/// Recurses through the container variants defensively — today only bare
/// `Str` leaves occur in a relation's slot value, but a compound slot
/// value must not silently leak a placeholder if one is ever introduced.
fn resolve_scoped_output(v: &Value, extra_rev: &FxHashMap<Sym, String>) -> Value {
    match v {
        Value::Str(s) => match extra_rev.get(s) {
            Some(text) => surf_string(text.clone()),
            None => v.clone(),
        },
        Value::Tuple(t) | Value::List(t) => v.reseq(
            t.iter()
                .map(|x| resolve_scoped_output(x, extra_rev))
                .collect(),
        ), // KIND-PRESERVING (see `Value::reseq`)
        Value::Set(t) => Value::Set(Arc::from(
            t.iter()
                .map(|x| resolve_scoped_output(x, extra_rev))
                .collect::<Vec<_>>(),
        )),
        Value::FrozenSet(t) => Value::FrozenSet(Arc::from(
            t.iter()
                .map(|x| resolve_scoped_output(x, extra_rev))
                .collect::<Vec<_>>(),
        )),
        Value::Dict(d) => Value::Dict(Arc::from(
            d.iter()
                .map(|(k, val)| {
                    (
                        resolve_scoped_output(k, extra_rev),
                        resolve_scoped_output(val, extra_rev),
                    )
                })
                .collect::<Vec<_>>(),
        )),
        _ => v.clone(),
    }
}

/// Build one `Candidate` for a single held signature (`sig`, UNSORTED —
/// this sorts it) against an ALREADY canonically-sorted observation
/// (`sorted_o`). Shared core the rung-1 consistency check reduces to: the
/// twin of `TransformDecode`'s own `'parts` loop body, factored out so
/// `DimInfer` (rung 2) can run the exact same check on a
/// generator-transformed candidate signature without duplicating any
/// matcher logic (see `eval_dim_infer`). Returns `None` when the candidate
/// is disqualified BEFORE any dimension analysis: a relation-count
/// mismatch, or a predicate/arity mismatch on some aligned pair (a
/// different predicate is a different shape, not a transform of one —
/// slot 0 is never transformable). A `Some` result may still be a FAILED
/// transform (`transforms.len() != dims_needed.len()`, e.g. inconsistent
/// per-dim changes or `dims_needed.len() > max_dims`) or an IDENTITY
/// (`dims_needed` empty) — callers distinguish those via the same
/// `transforms.len() == dims_needed.len()` check (true for both identity
/// `0 == 0` and a fully-consistent transform `n == n`).
fn build_candidate(
    name: String,
    name_val: Value,
    sig: &[Value],
    sorted_o: &[Value],
    max_dims: usize,
    extra_rev: &FxHashMap<Sym, String>,
    fuse_structural_slots: bool,
) -> Option<Candidate> {
    let mut sorted_h = sig.to_vec();
    sorted_h.sort_by(cmp_value);
    if sorted_h.len() != sorted_o.len() {
        // Relation-count mismatch — not a candidate at all (coverage/
        // partial matching is ShapeDecode's job, not this op's).
        return None;
    }
    // SCALE AUDIT — interior comparison units (`scale_audit.rs`, T section).
    //
    // THIS IS WHERE THE sd/identity COST ACTUALLY LIVES, and finding that out
    // cost this rung a measured failure: the first build of this instrument
    // charged units in `covers_relation` / `shape_fit` only, and G5 came back
    // **INERT** — the sd workload never touches the composer path. It runs
    // `TransformDecode` and `DimInfer`, and BOTH reduce to this function's
    // aligned-pair loops (`DimInfer` calls it on a generator-transformed
    // candidate, per this function's own doc). The gate caught the dead
    // instrument the counter was supposed to be, which is precisely its job.
    //
    // Charged: aligned pairs ACTUALLY examined, so an early structural bail is
    // reflected rather than papered over. One `term_units` call per loop, never
    // per iteration.
    let mut pairs: u64 = 0;
    // Which slots (k>=1) actually differ anywhere, and which observation
    // relations differ at all (for residual reporting).
    let mut dims_seen: std::collections::BTreeSet<i64> = std::collections::BTreeSet::new();
    let mut mismatches: Vec<Value> = Vec::new();
    let mut slot_cmps: u64 = 0;
    if fuse_structural_slots {
        // Experimental fast path: perform the same structural check and slot
        // comparisons in one traversal. Slot audit units on a structural
        // failure include work already done for preceding pairs, reflecting
        // the actual fused traversal; the baseline returns before its slot
        // traversal in that case.
        for (h, o) in sorted_h.iter().zip(sorted_o.iter()) {
            pairs += 1;
            let (Value::Tuple(ht) | Value::List(ht), Value::Tuple(ot) | Value::List(ot)) = (h, o)
            else {
                crate::scale_audit::term_units(pairs);
                crate::scale_audit::term_units(slot_cmps);
                return None;
            };
            if ht.is_empty() || ht.len() != ot.len() || ht[0] != ot[0] {
                crate::scale_audit::term_units(pairs);
                crate::scale_audit::term_units(slot_cmps);
                return None;
            }
            let mut relation_mismatched = false;
            for k in 1..ht.len() {
                slot_cmps += 1;
                if ht[k] != ot[k] {
                    relation_mismatched = true;
                    dims_seen.insert(k as i64);
                }
            }
            if relation_mismatched {
                mismatches.push(o.clone());
            }
        }
        crate::scale_audit::term_units(pairs);
        crate::scale_audit::term_units(slot_cmps);
    } else {
        // Baseline two-pass validator: reject malformed/predicate-mismatched
        // candidates before examining transformable slots.
        for (h, o) in sorted_h.iter().zip(sorted_o.iter()) {
            pairs += 1;
            let (Value::Tuple(ht) | Value::List(ht), Value::Tuple(ot) | Value::List(ot)) = (h, o)
            else {
                crate::scale_audit::term_units(pairs);
                return None;
            };
            if ht.is_empty() || ht.len() != ot.len() || ht[0] != ot[0] {
                crate::scale_audit::term_units(pairs);
                return None;
            }
        }
        crate::scale_audit::term_units(pairs);

        for (h, o) in sorted_h.iter().zip(sorted_o.iter()) {
            let (Value::Tuple(ht) | Value::List(ht), Value::Tuple(ot) | Value::List(ot)) = (h, o)
            else {
                continue;
            };
            let mut relation_mismatched = false;
            for k in 1..ht.len() {
                slot_cmps += 1;
                if ht[k] != ot[k] {
                    relation_mismatched = true;
                    dims_seen.insert(k as i64);
                }
            }
            if relation_mismatched {
                mismatches.push(o.clone());
            }
        }
        crate::scale_audit::term_units(slot_cmps);
    }
    let dims_needed: Vec<i64> = dims_seen.into_iter().collect();

    if dims_needed.is_empty() {
        // Exact match under canonical sort — `identity`, not a transform
        // (nothing changed to explain).
        return Some(Candidate {
            name,
            name_val,
            dims_needed,
            mismatches,
            transforms: Vec::new(),
        });
    }

    // --- Two-tier per-dimension consistency (predicate-aware pooling) ---
    //
    // TIER 1 (the "merged dimension", byte-identical to the committed
    // semantics): EVERY aligned pair with this slot present — not just
    // the mismatching ones — must agree on ONE uniform delta (numeric)
    // or ONE substitution function (symbolic). When tier 1 succeeds the
    // slot is a single un-keyed dimension exactly as before: identical
    // per-predicate deltas at one slot MERGE into one dimension (e.g.
    // the X→Y substitution shared across `move`/`stop` predicates stays
    // `dims:[1]` with one `transforms` entry).
    //
    // TIER 2 (the split, NUMERIC slots only): when the global numeric
    // check fails, re-pool the same pairs per (predicate, slot). A
    // group whose pairs are all EQUAL is a zero-delta group — simply
    // untransformed, NOT a transform, does not count toward `max_dims`,
    // and no longer vetoes another predicate's nonzero delta (the
    // stroke-pose fix: `seg`'s untouched ordinal slot must not veto
    // `pose_o`'s rotation delta just because both live at slot index
    // 1). Each nonzero group must be internally uniform; each becomes
    // its OWN dimension, `pred`-keyed (duplicate slot indices in `dims`
    // are allowed — two predicates transforming differently, or even
    // identically, at the same slot stay SEPARATE dimensions, because
    // slot indices are per-relation-LOCAL coordinates: `pose_o`'s slot
    // 1 and `pose_x`'s slot 1 are different dimensions of the object
    // that merely share a storage index).
    //
    // SYMBOLIC slots deliberately have NO tier 2: a substitution is a
    // value RENAMING, and renaming is global — the same held value
    // mapping to two different observed values under two predicates
    // (`move X→Y` / `stop X→Z`) is precisely the scrambled
    // discriminative null the sd loop's mint path depends on
    // (`test_scrambled_observation_is_discriminative_null_and_mints`);
    // a per-predicate symbolic split would dissolve exactly and only
    // that null (a benign cross-predicate rename with DISJOINT held
    // values already passes the tier-1 function check), so it is
    // excluded by design, not omission.
    let mut transforms: Vec<DimTransform> = Vec::new();
    let mut consistent = true;
    {
        'dims: for &k in &dims_needed {
            let kk = k as usize;
            // Aligned pairs with this slot present, tagged with the
            // OBSERVED relation's predicate (always a real Sym — the
            // held side may carry scoped placeholder Syms, see
            // `resolve_scoped_output`; the prefilter above guarantees
            // ht[0] == ot[0] so the tag is the shared predicate).
            let pairs: Vec<(Value, Value, Value)> = sorted_h
                .iter()
                .zip(sorted_o.iter())
                .filter_map(|(h, o)| match (h, o) {
                    (Value::Tuple(ht) | Value::List(ht), Value::Tuple(ot) | Value::List(ot))
                        if kk < ht.len() && kk < ot.len() =>
                    {
                        Some((ot[0].clone(), ht[kk].clone(), ot[kk].clone()))
                    }
                    _ => None,
                })
                .collect();

            let all_numeric = pairs.iter().all(|(_, h, o)| {
                matches!(h, Value::Int(_) | Value::Float(_))
                    && matches!(o, Value::Int(_) | Value::Float(_))
            });

            if all_numeric {
                let as_f64 = |v: &Value| match v {
                    Value::Int(i) => *i as f64,
                    Value::Float(f) => *f,
                    _ => 0.0,
                };
                // TIER 1: one uniform delta across every relation.
                let mut iter = pairs.iter().map(|(_, h, o)| as_f64(o) - as_f64(h));
                let first = iter.next().unwrap_or(0.0);
                if iter.all(|d| (d - first).abs() < 1e-9) {
                    let any_float = pairs.iter().any(|(_, h, o)| {
                        matches!(h, Value::Float(_)) || matches!(o, Value::Float(_))
                    });
                    let delta_val = if any_float {
                        Value::Float(first)
                    } else {
                        Value::Int(first.round() as i64)
                    };
                    transforms.push(DimTransform {
                        dim: k,
                        kind: "shift",
                        delta: delta_val,
                        pred: None,
                    });
                    continue 'dims;
                }
                // TIER 2: per-(predicate, slot) groups, in canonical
                // (sorted-relation first-occurrence) order for
                // deterministic output.
                let mut group_order: Vec<Value> = Vec::new();
                let mut groups: FxHashMap<Value, Vec<(Value, Value)>> = FxHashMap::default();
                for (pred, h, o) in &pairs {
                    if !groups.contains_key(pred) {
                        group_order.push(pred.clone());
                    }
                    groups
                        .entry(pred.clone())
                        .or_default()
                        .push((h.clone(), o.clone()));
                }
                for pred in &group_order {
                    let gp = &groups[pred];
                    let mut giter = gp.iter().map(|(h, o)| as_f64(o) - as_f64(h));
                    let gfirst = giter.next().unwrap_or(0.0);
                    if !giter.all(|d| (d - gfirst).abs() < 1e-9) {
                        // Non-uniform WITHIN one predicate family — a
                        // genuine inconsistency, not a pooling artifact.
                        consistent = false;
                        break 'dims;
                    }
                    if gfirst.abs() < 1e-9 {
                        // Zero-delta group: untransformed, not a
                        // transform, free of the max_dims budget.
                        continue;
                    }
                    let any_float = gp
                        .iter()
                        .any(|(h, o)| matches!(h, Value::Float(_)) || matches!(o, Value::Float(_)));
                    let delta_val = if any_float {
                        Value::Float(gfirst)
                    } else {
                        Value::Int(gfirst.round() as i64)
                    };
                    transforms.push(DimTransform {
                        dim: k,
                        kind: "shift",
                        delta: delta_val,
                        pred: Some(pred.clone()),
                    });
                }
            } else {
                // Symbolic slot: the held->observed mapping must be a
                // FUNCTION (each held value maps to exactly one observed
                // value, across every pair — including pairs that happen
                // to already agree, which pin that held value to itself).
                // GLOBAL only — no tier-2 split (see the block comment
                // above: renaming is object identity, cross-predicate by
                // nature; splitting here would dissolve the scrambled
                // discriminative null).
                let mut map: FxHashMap<Value, Value> = FxHashMap::default();
                let mut order: Vec<Value> = Vec::new();
                for (_, h, o) in &pairs {
                    match map.get(h) {
                        Some(existing) if existing != o => {
                            consistent = false;
                            break;
                        }
                        Some(_) => {}
                        None => {
                            map.insert(h.clone(), o.clone());
                            order.push(h.clone());
                        }
                    }
                }
                if !consistent {
                    break 'dims;
                }
                let sub_pairs: SmallVec<[Value; 4]> = order
                    .iter()
                    .filter_map(|h| {
                        let o = map.get(h).expect("just inserted");
                        if o == h {
                            None
                        } else {
                            // `h` is the held-side ("from") value — may be a
                            // scoped-local placeholder Sym (see
                            // `resolve_scoped_output`'s doc); `o` is always a
                            // real Sym (goal-side).
                            Some(Value::Tuple(Arc::new(smallvec::smallvec![
                                resolve_scoped_output(h, extra_rev),
                                o.clone()
                            ])))
                        }
                    })
                    .collect();
                transforms.push(DimTransform {
                    dim: k,
                    kind: "subst",
                    delta: Value::Tuple(Arc::new(sub_pairs)),
                    pred: None,
                });
            }
        }
    }

    // The max_dims budget counts TRANSFORM ENTRIES (tier-1 merged
    // dimensions + tier-2 split dimensions), not raw slot indices —
    // zero-delta (predicate, slot) groups were skipped above and are
    // budget-free. For every case the old raw-slot semantics explained,
    // entry count == slot count (each slot resolved at tier 1), so the
    // committed verdicts are unchanged.
    if consistent && transforms.len() > max_dims {
        consistent = false;
    }

    // On success, `dims_needed` becomes the transform entries' dim list
    // (parallel to `transforms`; duplicate slot indices possible in
    // split mode) so the caller's `transforms.len() == dims_needed.len()`
    // success check keeps its contract. On failure it stays the raw
    // differing-slot list (non-empty by construction here), which the
    // empty `transforms` can never equal — the failure signal.
    let dims_out: Vec<i64> = if consistent {
        transforms.iter().map(|t| t.dim).collect()
    } else {
        dims_needed
    };

    Some(Candidate {
        name,
        name_val,
        dims_needed: dims_out,
        mismatches,
        transforms: if consistent { transforms } else { Vec::new() },
    })
}

/// Count the total substitution PAIRS across a candidate's transforms —
/// the second Occam ranking key (fewest dims first, then fewest pairs).
fn subst_pair_count(transforms: &[DimTransform]) -> usize {
    transforms
        .iter()
        .filter(|t| t.kind == "subst")
        .map(|t| match &t.delta {
            Value::Tuple(pairs) | Value::List(pairs) => pairs.len(),
            _ => 0,
        })
        .sum()
}

/// Evaluate `TransformDecode` — the quantum-delta dequantizer. See
/// `TermNode::TransformDecode`'s doc (term.rs) for the full semantics;
/// this reuses `load_parts`/`apply_exclude` (codebook read, identical to
/// `ShapeDecode`) and `select_field`/`finish` (the `field` selector,
/// unchanged) — no duplicated matcher logic. `wild` is not needed here:
/// unlike `ShapeDecode`'s `AntiUnify`/`Covers` scoring, this Term never
/// generalises a value to a wildcard — every comparison is a direct
/// `Value` equality check (see module docs re: `goal`'s Str leaves always
/// being real Syms, and a part's JSON-string `signature` being parsed via
/// `json_to_value_scoped`, which resolves to the SAME real Sym whenever
/// the string appears anywhere else in the graph — so equality across the
/// two sides is meaningful).
pub(crate) fn eval_transform_decode(
    arena: &TermArena,
    goal_idx: TermIdx,
    codebook_type: Sym,
    exclude_idx: Option<TermIdx>,
    max_dims: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_TRANSFORM_DECODE);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let mut parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    apply_exclude(&mut parts, exclude_idx, arena, env, ctx);
    // Reverse of `extra`, built once `load_parts` is done fabricating
    // placeholders — see `resolve_scoped_output`'s doc for why this must
    // run before any held-side (`h`) value reaches the output.
    let extra_rev: FxHashMap<Sym, String> = extra.iter().map(|(k, v)| (*v, k.clone())).collect();

    let goal_val = evaluate(arena, goal_idx, env, ctx);
    let goal: Vec<Value> = match &goal_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
            goal_val.iter().cloned().collect()
        }
        _ => Vec::new(),
    };
    let max_dims = max_dims.max(0) as usize;
    let checked = parts.len() as i64;

    let mut sorted_o = goal.clone();
    sorted_o.sort_by(cmp_value);

    let candidates: Vec<Candidate> = parts
        .iter()
        .filter_map(|part| {
            crate::access_trace::note_helper_work(51, 1);
            build_candidate(
                part.name.clone(),
                part.name_val.clone(),
                &part.sig,
                &sorted_o,
                max_dims,
                &extra_rev,
                false,
            )
        })
        .collect();

    let identity = candidates.iter().any(|c| c.dims_needed.is_empty());

    // A SUCCESS candidate: at least one dimension needed (a true
    // transform, not identity), within budget, and every needed
    // dimension resolved consistently (`transforms.len() ==
    // dims_needed.len()` — `transforms` is cleared to empty whenever any
    // dimension broke consistency, so this also excludes the
    // too-many-dims / inconsistent cases without a separate flag).
    let mut best: Option<&Candidate> = None;
    for c in &candidates {
        if c.dims_needed.is_empty() || c.transforms.len() != c.dims_needed.len() {
            continue;
        }
        best = Some(match best {
            None => c,
            Some(cur) => {
                let c_key = (c.dims_needed.len(), subst_pair_count(&c.transforms));
                let cur_key = (cur.dims_needed.len(), subst_pair_count(&cur.transforms));
                // "most relations" never discriminates in practice (every
                // surviving candidate has exactly `sorted_o.len()`
                // relations, by the length-alignment prefilter above) —
                // kept as a documented no-op tie key, per the design's
                // Occam ranking; `name` (ascending) is what actually
                // breaks ties.
                if c_key < cur_key || (c_key == cur_key && c.name < cur.name) {
                    c
                } else {
                    cur
                }
            }
        });
    }

    let (explained, base_val, transforms_out, residual_out) = if let Some(winner) = best {
        let transforms_vec: SmallVec<[Value; 4]> = winner
            .transforms
            .iter()
            .map(DimTransform::to_value)
            .collect();
        (true, winner.name_val.clone(), transforms_vec, Vec::new())
    } else {
        // Nothing explains — pick the CLOSEST eligible candidate (fewest
        // differing relations, then name) so `base`/`residual_unexplained`
        // still name what almost-matched; an `identity` candidate (zero
        // mismatches) always wins this by construction.
        let mut closest: Option<&Candidate> = None;
        for c in &candidates {
            closest = Some(match closest {
                None => c,
                Some(cur) => {
                    if c.mismatches.len() < cur.mismatches.len()
                        || (c.mismatches.len() == cur.mismatches.len() && c.name < cur.name)
                    {
                        c
                    } else {
                        cur
                    }
                }
            });
        }
        match closest {
            Some(c) => (
                false,
                c.name_val.clone(),
                SmallVec::new(),
                c.mismatches.clone(),
            ),
            None => (false, Value::None, SmallVec::new(), Vec::new()),
        }
    };

    let dims_val: SmallVec<[Value; 4]> = transforms_out
        .iter()
        .map(|t| select_field(t, "dim", None))
        .collect();
    let deltas_val: SmallVec<[Value; 4]> = transforms_out
        .iter()
        .map(|t| select_field(t, "delta", None))
        .collect();
    let residual_tuple: SmallVec<[Value; 4]> = residual_out.into_iter().collect();

    let result = Value::Dict(Arc::from(vec![
        (surf("explained"), Value::Bool(explained)),
        (surf("base"), base_val),
        (surf("transforms"), Value::Tuple(Arc::new(transforms_out))),
        (surf("dims"), Value::Tuple(Arc::new(dims_val))),
        (surf("deltas"), Value::Tuple(Arc::new(deltas_val))),
        (surf("checked"), Value::Int(checked)),
        (
            surf("residual_unexplained"),
            Value::Tuple(Arc::new(residual_tuple)),
        ),
        (surf("identity"), Value::Bool(identity)),
    ]));
    finish(result, field, ctx.interner, None)
}

/// One generator STEP in a (length-1 or length-2) composition — the
/// generator's human name (for the ranking tie-break and the composite
/// `latent:` label), its graph-facing `name_val`, and the integer quantum
/// `k` applied. See `COMPOSITION_DESIGN.md` §1/§4.
struct GenStep {
    name: String,
    name_val: Value,
    k: i64,
}

/// One successful `(part, generator-sequence)` attempt — `DimInfer`'s
/// internal ranking unit. `steps` is the ordered composition (length 1 for
/// the committed single-generator arm, length 2 for a composite);
/// `residual_dims` mirrors `TransformDecode`'s `dims_needed` count AFTER
/// the whole sequence is applied (0 for a post-composition EXACT match).
struct DimAttempt {
    base_val: Value,
    base_name: String,
    steps: Vec<GenStep>,
    transforms: Vec<DimTransform>,
    residual_dims: usize,
}

/// Encode ONE held part exactly, for the `DimInfer` argument audit.
///
/// EVERY field of `Part` appears. That is deliberate and it is the property the
/// gate checks: the reducibility question is *"do two invocations receive
/// arguments that determine the same answer?"*, and an encoder that silently
/// omitted a field would answer "yes" for invocations that differ in it —
/// manufacturing the re-derivation verdict out of its own blind spot.
fn enc_part(p: &Part) -> String {
    use std::fmt::Write;
    let mut s = String::new();
    let _ = write!(
        s,
        "P|{}|{:?}|{:?}|{:?}|sig{}[",
        p.name,
        p.name_val,
        p.kind_val,
        p.source_val,
        p.sig.len()
    );
    for v in &p.sig {
        let _ = write!(s, "{:?},", v);
    }
    match &p.dim_types {
        None => {
            let _ = write!(s, "]|dt-");
        }
        Some(d) => {
            let _ = write!(s, "]|dt{}{:?}", d.len(), d);
        }
    }
    s
}

/// Encode ONE generator exactly. Same completeness contract as `enc_part`.
fn enc_generator(g: &Generator) -> String {
    use std::fmt::Write;
    let mut s = String::new();
    let _ = write!(
        s,
        "G|{}|{:?}|{}|cd{:?}|p{:?}|m{}|mx{:?}|q{:?}|of{:?}",
        g.name, g.name_val, g.kind, g.coord_dims, g.params, g.modulus, g.matrix, g.coefficients, g.offset
    );
    s
}

/// The EXACT canonical encoding of one `eval_dim_infer` invocation's arguments
/// — `VISION_DIM_INFER_ARGS_PREREG.md` §2.1, whose determinant list is read off
/// this function's own body rather than chosen.
///
/// `sorted` selects the UNORDERED form: `parts` and `generators` are each
/// canonically sorted, so codebook load-order churn (a graph-iteration fact
/// with no semantic content) cannot inflate the distinct count. The goal is
/// NOT sorted in either form — its order is observed data, not iteration
/// order. The ordered form is the complete determinant set, because attempt
/// order genuinely decides ties (`best` is selected by `<`, first-seen wins on
/// equality); the unordered form is therefore a LOWER BOUND and both are
/// reported.
fn encode_dim_infer_args(
    parts: &[Part],
    generators: &[Generator],
    goal: &[Value],
    max_dims: i64,
    field: Sym,
    sorted: bool,
) -> Vec<u8> {
    use std::fmt::Write;
    let mut ps: Vec<String> = parts.iter().map(enc_part).collect();
    let mut gs: Vec<String> = generators.iter().map(enc_generator).collect();
    if sorted {
        ps.sort();
        gs.sort();
    }
    let mut s = String::new();
    let _ = write!(s, "md{}|fd{:?}|np{}|", max_dims, field, ps.len());
    for p in &ps {
        s.push_str(p);
        s.push(';');
    }
    let _ = write!(s, "|ng{}|", gs.len());
    for g in &gs {
        s.push_str(g);
        s.push(';');
    }
    let _ = write!(s, "|goal{}[", goal.len());
    for v in goal {
        let _ = write!(s, "{:?},", v);
    }
    s.push(']');
    s.into_bytes()
}

/// Evaluate `DimInfer` — RUNG 2 of the transform-as-quantum-delta ladder.
/// See `TermNode::DimInfer`'s doc (term.rs) for the full semantics; this
/// reuses `load_parts` (now also reading each part's optional `dim_types`)
/// / `apply_exclude` / `load_generators` (the two codebook reads) and
/// `build_candidate` (the EXACT rung-1 consistency check
/// `eval_transform_decode` itself runs — no duplicated matcher logic) plus
/// `select_field`/`finish` (the `field` selector, unchanged).
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_dim_infer(
    arena: &TermArena,
    goal_idx: TermIdx,
    codebook_type: Sym,
    exclude_idx: Option<TermIdx>,
    generator_type: Sym,
    grain: i64,
    max_dims: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_DIM_INFER);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let mut parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    apply_exclude(&mut parts, exclude_idx, arena, env, ctx);
    let extra_rev: FxHashMap<Sym, String> = extra.iter().map(|(k, v)| (*v, k.clone())).collect();
    let generators = load_generators(ctx, generator_type);

    let goal_val = evaluate(arena, goal_idx, env, ctx);
    let mut goal: Vec<Value> = match &goal_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
            goal_val.iter().cloned().collect()
        }
        _ => Vec::new(),
    };
    if grain > 0 {
        let slots = |dts: &[String]| -> Vec<usize> {
            dts.iter().enumerate().filter(|(_, t)| t.starts_with("coord:")).map(|(i, _)| i).collect()
        };
        if let Some(dts) = parts.iter().find_map(|p| p.dim_types.clone()) {
            goal = requantize(&goal, &slots(&dts), grain);
            if coarse_degenerate(&goal, &slots(&dts)) {
                goal.clear(); // no coarse explanation of a degenerate collapse
            }
        }
        for part in parts.iter_mut() {
            if let Some(dts) = part.dim_types.clone() {
                part.sig = requantize(&part.sig, &slots(&dts), grain);
            }
        }
    }
    let max_dims_usize = max_dims.max(0) as usize;

    // THE ARGUMENT-RECORDING SITE (VISION_DIM_INFER_ARGS_PREREG.md). Placed
    // AFTER the two codebook reads, the exclude, and the goal evaluation —
    // i.e. once every determinant of this function's return value exists and
    // BEFORE any of the work those determinants drive. Gated on the scale
    // audit, which is OFF by default (PROTOCOL §9), so the cost on every
    // committed path is one relaxed atomic load and no allocation.
    // The witness is the sound path: attribution belongs to THIS call, so a
    // concurrent decode cannot contribute to it. The global scale_audit
    // counters remain for whole-process cost measurement, which is what they
    // are for; they are not a per-call measurement, and a caller needing one
    // attaches a witness.
    if ctx.dim_infer_witness.is_some() || crate::scale_audit::enabled() {
        let ordered = encode_dim_infer_args(&parts, &generators, &goal, max_dims, field, false);
        let unordered = encode_dim_infer_args(&parts, &generators, &goal, max_dims, field, true);
        if let Some(w) = ctx.dim_infer_witness.as_deref_mut() {
            w.record(ordered.clone(), unordered.clone());
        }
        if crate::scale_audit::enabled() {
            crate::scale_audit::dim_infer_args(ordered, unordered);
        }
    }

    let mut sorted_o = goal.clone();
    sorted_o.sort_by(cmp_value);

    // For every held part WITH dim_types, times every generator whose
    // coord_dims are ALL typed coord on that part, times every k in the
    // generator's params: apply the generator, then run the shared rung-1
    // consistency check on the transformed candidate. `checked` counts
    // every (part, generator, k) triple actually attempted post-gating
    // (a part with no/partial dim_types contributes zero — the graceful
    // skip requirement 6 tests for).
    let mut checked: i64 = 0;
    let mut successes: Vec<DimAttempt> = Vec::new();

    // A transformed candidate signature is a SUCCESS iff it is either an
    // EXACT match (dims_needed empty — the sequence alone fully explains
    // it) or a fully-consistent residual transform (transforms.len() ==
    // dims_needed.len(), which is also `0 == 0` for the exact-match case
    // — see `build_candidate`'s doc). Shared by the length-1 and length-2
    // arms so both use the IDENTICAL rung-1 consistency contract, unchanged.
    let mut try_candidate = |transformed: &[Value],
                             part: &Part,
                             steps: Vec<GenStep>,
                             successes: &mut Vec<DimAttempt>| {
        let Some(cand) = build_candidate(
            part.name.clone(),
            part.name_val.clone(),
            transformed,
            &sorted_o,
            max_dims_usize,
            &extra_rev,
            false,
        ) else {
            return;
        };
        if cand.transforms.len() == cand.dims_needed.len() {
            successes.push(DimAttempt {
                base_val: cand.name_val.clone(),
                base_name: cand.name.clone(),
                steps,
                transforms: cand.transforms,
                residual_dims: cand.dims_needed.len(),
            });
        }
    };

    // THE TWO ARMS ARE TWO PASSES OVER `parts`, NOT ONE INTERLEAVED PASS, AND
    // THAT IS THE WHOLE OF THE OCCAM SHORT-CIRCUIT BELOW.
    //
    // MEASURED MOTIVATION (`VISION_CODEBOOK_AXIS_RESULTS.md`, prereg
    // `VISION_CODEBOOK_AXIS_PREREG.md` @ `e22db8dd`): this loop is EXHAUSTIVE —
    // measured/predicted units = 1.0000 at all 7 N points and all 7 K points —
    // and the length-2 arm is `(SP)^2 - SP^2` = **134 of 147 attempts, 91.16%**,
    // for the shipped 5-generator codebook. That work was being re-derived on
    // every observation that a SINGLE generator already explains.
    //
    // WHY SKIPPING IS EXACT, NOT APPROXIMATE — the proof is the comparator's
    // own definition, one line, and it was already written down in this
    // function's committed comment ("Occam (length strict-primary, below)
    // guarantees a length-2 attempt NEVER beats a length-1 one"):
    //
    //   `key = (steps.len(), residual_dims, base_name, ks)`, compared as a
    //   TUPLE, so `steps.len()` is STRICT PRIMARY. Every length-1 attempt has
    //   `steps.len() == 1`; every length-2 attempt has `steps.len() == 2`.
    //   Therefore `key(any length-1 success) < key(any length-2 success)`
    //   UNCONDITIONALLY — no tie is possible at the primary component, so no
    //   later component is ever consulted between the two arms.
    //
    // The quantifier is GLOBAL, not per-part, which is exactly why the passes
    // are split: a length-1 success on the LAST part still forbids every
    // length-2 winner on the FIRST. Interleaving per part could not see that
    // and would have had to keep going.
    //
    // A skipped candidate is therefore PROVABLY unable to win. This changes
    // WHICH WORK HAPPENS, never WHICH ANSWER IS PRODUCED — `best` is selected
    // by `<` (first-seen wins on equality), and within each arm the attempt
    // ORDER is byte-unchanged, so the winner is identical value-for-value.
    //
    // `checked` IS PRESERVED EXACTLY, AND DELIBERATELY SO. It is a RETURNED
    // field of this op's result dict, so quietly shrinking it would be a
    // silent semantic change dressed as an optimisation — and the
    // pre-registration named it as the one hazard of this fix BEFORE the fix
    // existed. The skip is therefore placed AFTER `checked += 1` and after the
    // outer `apply_generator_k` (only `SP` = 13 calls per part, and their
    // success is what `checked`'s value depends on). What is skipped is the
    // INNER `apply_generator_k` + `build_candidate` — the `O(N x slots)` work
    // that is 100% of the measured cost. `checked` byte-identical; units down
    // by the full 91.16%.
    //
    // COST STILL TRACKS CONTENT (the property batch-apply broke while holding
    // byte-identity): when NOTHING is explained at length 1, `successes` is
    // empty, the short-circuit does not fire, and the full 147 attempts run.
    // The saving accrues to RECOGNISED observations only, so the
    // surprise-proportionality of this op is strengthened, not flattened.

    // --- PASS 1: LENGTH 1, over ALL parts (the committed single-generator
    //     arm — every attempt it makes and the order it makes them are
    //     unchanged). ---
    for part in &parts {
        let Some(dim_types) = &part.dim_types else {
            continue;
        };
        // Generators applicable to THIS part (coord_dims all typed coord).
        let eligible: Vec<&Generator> = generators
            .iter()
            .filter(|g| dims_are_coord(dim_types, &g.coord_dims))
            .collect();

        for gen in &eligible {
            for &k in &gen.params {
                checked += 1;
                crate::access_trace::note_helper_work(51, 1);
                let Some(transformed) = apply_gen_k(gen, &part.sig, k) else {
                    continue;
                };
                try_candidate(
                    &transformed,
                    part,
                    vec![GenStep {
                        name: gen.name.clone(),
                        name_val: gen.name_val.clone(),
                        k,
                    }],
                    &mut successes,
                );
            }
        }
    }

    // THE SHORT-CIRCUIT. Evaluated ONCE, between the passes, over the GLOBAL
    // success set — see the proof above.
    let explained_at_length_1 = !successes.is_empty();

    // --- PASS 2: LENGTH 2 (composition; DISTINCT generators only, both
    // orders — see COMPOSITION_DESIGN.md §1). A self-composition
    // (g,g) is just g at higher k and belongs at length 1, so it is
    // skipped; this also means a single-generator codebook produces
    // ZERO length-2 attempts, keeping committed `checked` counts
    // exact. `transformed_a` is computed once per (gen_a, k_a) and
    // reused across every second step. ---
    for part in &parts {
        let Some(dim_types) = &part.dim_types else {
            continue;
        };
        let eligible: Vec<&Generator> = generators
            .iter()
            .filter(|g| dims_are_coord(dim_types, &g.coord_dims))
            .collect();

        for gen_a in &eligible {
            for &k_a in &gen_a.params {
                let Some(transformed_a) = apply_gen_k(gen_a, &part.sig, k_a) else {
                    continue;
                };
                for gen_b in &eligible {
                    if gen_b.name == gen_a.name {
                        continue;
                    }
                    for &k_b in &gen_b.params {
                        checked += 1;
                        crate::access_trace::note_helper_work(51, 1);
                        // The skip sits HERE — after `checked`, so the returned
                        // attempt count is byte-identical, and before the
                        // `O(N x slots)` work, which is the entire saving.
                        if explained_at_length_1 {
                            continue;
                        }
                        let Some(transformed_ab) = apply_gen_k(gen_b, &transformed_a, k_b) else {
                            continue;
                        };
                        try_candidate(
                            &transformed_ab,
                            part,
                            vec![
                                GenStep {
                                    name: gen_a.name.clone(),
                                    name_val: gen_a.name_val.clone(),
                                    k: k_a,
                                },
                                GenStep {
                                    name: gen_b.name.clone(),
                                    name_val: gen_b.name_val.clone(),
                                    k: k_b,
                                },
                            ],
                            &mut successes,
                        );
                    }
                }
            }
        }
    }

    // Occam within rung 2: composition LENGTH strictly first (a length-2
    // composite can never beat a length-1 explanation — COMPOSITION_DESIGN
    // §2), then fewest residual dims, then base name, then the k sequence
    // (smallest first — a symmetric shape's tied k values report the
    // smallest). For length 1 this reduces to `(1, residual_dims,
    // base_name, [k])`, whose ordering is byte-identical to the committed
    // `(1 + residual_dims, base_name, k)` key. Any remaining EXACT tie
    // (two DIFFERENT generators/pairs producing the identical image at the
    // same k — e.g. rotation90 and reflection_c both map this tromino to
    // the same cells) is broken by FIRST-SEEN generator-iteration order
    // (load order — `<` keeps `cur` on equality), byte-identical to the
    // committed single-generator behaviour. A generator-NAME tie-break was
    // rejected here precisely because it would flip that committed
    // rotation90/reflection_c tie.
    let key = |att: &DimAttempt| -> (usize, usize, String, Vec<i64>) {
        (
            att.steps.len(),
            att.residual_dims,
            att.base_name.clone(),
            att.steps.iter().map(|s| s.k).collect(),
        )
    };
    let mut best: Option<&DimAttempt> = None;
    for att in &successes {
        best = Some(match best {
            None => att,
            Some(cur) => {
                if key(att) < key(cur) {
                    att
                } else {
                    cur
                }
            }
        });
    }

    let result = match best {
        Some(win) => {
            let transforms_out: SmallVec<[Value; 4]> =
                win.transforms.iter().map(DimTransform::to_value).collect();
            let dims_val: SmallVec<[Value; 4]> = transforms_out
                .iter()
                .map(|t| select_field(t, "dim", None))
                .collect();
            // The composite step sequence as parallel `generators` / `ks`
            // tuples, plus the `latent_name` label body (`"a+b"`, or the
            // single name for length 1) the seed prefixes with `latent:`.
            // The scalar `generator` / `k` = the FIRST step, so every
            // length-1 read and committed test is byte-identical.
            let generators_out: SmallVec<[Value; 4]> =
                win.steps.iter().map(|s| s.name_val.clone()).collect();
            let ks_out: SmallVec<[Value; 4]> = win.steps.iter().map(|s| Value::Int(s.k)).collect();
            let latent_name: String = win
                .steps
                .iter()
                .map(|s| s.name.as_str())
                .collect::<Vec<_>>()
                .join("+");
            let (gen0, k0) = match win.steps.first() {
                Some(s) => (s.name_val.clone(), Value::Int(s.k)),
                None => (Value::None, Value::None),
            };
            Value::Dict(Arc::from(vec![
                (surf("explained"), Value::Bool(true)),
                (surf("base"), win.base_val.clone()),
                (surf("generator"), gen0),
                (surf("k"), k0),
                (surf("length"), Value::Int(win.steps.len() as i64)),
                (surf("generators"), Value::Tuple(Arc::new(generators_out))),
                (surf("ks"), Value::Tuple(Arc::new(ks_out))),
                (surf("latent_name"), surf(&latent_name)),
                (surf("transforms"), Value::Tuple(Arc::new(transforms_out))),
                (surf("dims"), Value::Tuple(Arc::new(dims_val))),
                (surf("checked"), Value::Int(checked)),
                (surf("identity"), Value::Bool(win.transforms.is_empty())),
            ]))
        }
        None => Value::Dict(Arc::from(vec![
            (surf("explained"), Value::Bool(false)),
            (surf("base"), Value::None),
            (surf("generator"), Value::None),
            (surf("k"), Value::None),
            (surf("length"), Value::Int(0)),
            (surf("generators"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("ks"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("latent_name"), Value::None),
            (surf("transforms"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("dims"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("checked"), Value::Int(checked)),
            (surf("identity"), Value::Bool(false)),
        ])),
    };
    finish(result, field, ctx.interner, None)
}

/// One successful `(part, matrix)` inference — `GenInfer`'s ranking unit.
struct GenAttempt {
    base_val: Value,
    base_name: String,
    kind: String,
    coord_dims: Vec<i64>,
    matrix: Vec<i64>,
    coefficients: Vec<i64>,
    transforms: Vec<DimTransform>,
    residual_dims: usize,
    abs_sum: i64,
}

/// Recover a unique integer matrix from full-rank, identity-aligned rows.
/// This is used only by the opt-in non-2-D GenInfer path. The stable key is
/// predicate plus explicitly typed `id` slots; if those do not identify each
/// relation uniquely, the solver abstains instead of guessing an alignment.
fn infer_full_rank_integer_matrix(
    source: &[Value],
    target: &[Value],
    dim_types: &[String],
    coord_dims: &[i64],
    bound: i64,
) -> Option<Vec<i64>> {
    let mut identity_key_comparisons = 0u64;
    #[cfg(feature = "geninfer_full_rank_identity_join_work_audit")]
    let track_identity_work = crate::scale_audit::enabled();
    #[cfg(not(feature = "geninfer_full_rank_identity_join_work_audit"))]
    let track_identity_work = false;
    let result = infer_full_rank_integer_matrix_impl(
        source, target, dim_types, coord_dims, bound,
        &mut identity_key_comparisons, track_identity_work,
    );
    #[cfg(feature = "geninfer_full_rank_identity_join_work_audit")]
    if track_identity_work {
        crate::scale_audit::gen_infer_full_rank_identity_key_comparisons(identity_key_comparisons);
    }
    result
}

fn infer_full_rank_integer_matrix_impl(
    source: &[Value],
    target: &[Value],
    dim_types: &[String],
    coord_dims: &[i64],
    bound: i64,
    identity_key_comparisons: &mut u64,
    track_identity_work: bool,
) -> Option<Vec<i64>> {
    let d = coord_dims.len();
    if !matches!(d, 1 | 3) || source.len() != target.len() || source.len() <= d {
        return None;
    }
    let mut stable_slots = vec![0usize];
    stable_slots.extend(dim_types.iter().enumerate().filter_map(|(i, t)| (t == "id").then_some(i)));
    if stable_slots.len() < 2 || stable_slots.iter().any(|&i| i >= dim_types.len()) {
        return None;
    }
    let key_equal = |a: &[Value], b: &[Value], comparisons: &mut u64| -> bool {
        stable_slots.iter().all(|&i| {
            if track_identity_work { *comparisons += 1; }
            a.get(i) == b.get(i)
        })
    };
    #[cfg(feature = "geninfer_full_rank_sorted_identity_join")]
    let aligned_targets = (|| -> Option<Vec<usize>> {
        // The join comparator must be a total order over eligible keys, and
        // comparator equality must never silently broaden Value equality.
        // In particular cmp_value maps NaN comparisons to Equal and compares
        // mixed numeric variants by value. Keep the opt-in fast path to
        // primitive, totally ordered keys until compound-key semantics have
        // dedicated differential coverage.
        let safe_identity_key = |value: &Value| matches!(
            value,
            Value::None | Value::Bool(_) | Value::Int(_) | Value::Str(_) | Value::Node(_)
        );
        let mut source_keys = Vec::with_capacity(source.len());
        let mut target_keys = Vec::with_capacity(target.len());
        for (index, value) in source.iter().enumerate() {
            let row = relation_values(value)?;
            if row.len() != dim_types.len() { return None; }
            let key = stable_slots.iter().map(|&i| row.get(i).cloned()).collect::<Option<Vec<_>>>()?;
            if key.iter().any(|value| !safe_identity_key(value)) { return None; }
            source_keys.push((key, index));
        }
        for (index, value) in target.iter().enumerate() {
            let row = relation_values(value)?;
            if row.len() != dim_types.len() { return None; }
            let key = stable_slots.iter().map(|&i| row.get(i).cloned()).collect::<Option<Vec<_>>>()?;
            if key.iter().any(|value| !safe_identity_key(value)) { return None; }
            target_keys.push((key, index));
        }
        let mut key_cmp = |a: &[Value], b: &[Value]| {
            for (x, y) in a.iter().zip(b) {
                if track_identity_work { *identity_key_comparisons += 1; }
                let order = cmp_value(x, y);
                if order != std::cmp::Ordering::Equal { return order; }
            }
            a.len().cmp(&b.len())
        };
        source_keys.sort_by(|a, b| key_cmp(&a.0, &b.0));
        target_keys.sort_by(|a, b| key_cmp(&a.0, &b.0));
        if source_keys.windows(2).any(|w| key_cmp(&w[0].0, &w[1].0) == std::cmp::Ordering::Equal)
            || target_keys.windows(2).any(|w| key_cmp(&w[0].0, &w[1].0) == std::cmp::Ordering::Equal)
        { return None; }
        let mut aligned = vec![usize::MAX; source.len()];
        let (mut si, mut ti) = (0usize, 0usize);
        while si < source_keys.len() && ti < target_keys.len() {
            match key_cmp(&source_keys[si].0, &target_keys[ti].0) {
                std::cmp::Ordering::Less => return None,
                std::cmp::Ordering::Greater => ti += 1,
                std::cmp::Ordering::Equal => {
                    if source_keys[si].0 != target_keys[ti].0 { return None; }
                    aligned[source_keys[si].1] = target_keys[ti].1;
                    si += 1;
                    ti += 1;
                }
            }
        }
        if si != source_keys.len() || ti != target_keys.len() || aligned.iter().any(|&i| i == usize::MAX) {
            return None;
        }
        Some(aligned)
    })();
    let mut used = vec![false; target.len()];
    let mut pairs: Vec<(Vec<i128>, Vec<i128>)> = Vec::with_capacity(source.len());
    for (source_index, src) in source.iter().enumerate() {
        #[cfg(not(feature = "geninfer_full_rank_sorted_identity_join"))]
        let _ = source_index;
        let sr = relation_values(src)?;
        if sr.len() != dim_types.len() {
            return None;
        }
        #[cfg(feature = "geninfer_full_rank_sorted_identity_join")]
        let i = if let Some(aligned) = &aligned_targets {
            aligned[source_index]
        } else {
            // Ordering can be coarser or finer than Value equality for some
            // variants (for example Bool/Int). Preserve the baseline contract
            // by falling back to the exact nested join whenever the sorted
            // merge cannot prove an unambiguous correspondence.
            let mut found = None;
            for (i, dst) in target.iter().enumerate() {
                let dr = relation_values(dst)?;
                if dr.len() != dim_types.len() { return None; }
                if key_equal(sr, dr, identity_key_comparisons) {
                    if found.is_some() || used[i] { return None; }
                    found = Some(i);
                }
            }
            found?
        };
        #[cfg(not(feature = "geninfer_full_rank_sorted_identity_join"))]
        let i = {
            let mut found = None;
            for (i, dst) in target.iter().enumerate() {
                let dr = relation_values(dst)?;
                if dr.len() != dim_types.len() { return None; }
                if key_equal(sr, dr, identity_key_comparisons) {
                    if found.is_some() || used[i] { return None; }
                    found = Some(i);
                }
            }
            found?
        };
        if used[i] {
            return None;
        }
        used[i] = true;
        let mut sx = Vec::with_capacity(d);
        let mut ty = Vec::with_capacity(d);
        for &slot in coord_dims {
            let slot = usize::try_from(slot).ok()?;
            let Value::Int(x) = sr.get(slot)? else { return None };
            let dr = relation_values(&target[i])?;
            let Value::Int(y) = dr.get(slot)? else { return None };
            sx.push(*x as i128);
            ty.push(*y as i128);
        }
        pairs.push((sx, ty));
    }
    if used.iter().any(|v| !v) || pairs.len() <= d {
        return None;
    }

    // Build a full-rank basis of source displacements relative to one row.
    let source_origin = &pairs[0].0;
    let target_origin = &pairs[0].1;
    let mut basis: Vec<Vec<i128>> = Vec::with_capacity(d);
    let mut target_basis: Vec<Vec<i128>> = Vec::with_capacity(d);
    for (sx, ty) in pairs.iter().skip(1) {
        let vector: Vec<i128> = sx.iter().zip(source_origin).map(|(x, o)| x - o).collect();
        if vector.iter().all(|x| *x == 0) {
            continue;
        }
        let mut trial = basis.clone();
        trial.push(vector.clone());
        if !independent_displacement_rows(&trial, d)? {
            continue;
        }
        basis.push(vector);
        target_basis.push(ty.iter().zip(target_origin).map(|(y, o)| y - o).collect());
        if basis.len() == d {
            break;
        }
    }
    if basis.len() != d {
        return None;
    }
    let denominator = determinant_small(&basis)?;
    if denominator == 0 {
        return None;
    }

    // Cramer's rule on this at-most-3x3 system. Every division is exact;
    // checked i128 arithmetic makes overflow an explicit abstention.
    let mut matrix = vec![0i64; d * d];
    for output_axis in 0..d {
        for input_axis in 0..d {
            let mut replaced = basis.clone();
            for row in 0..d {
                replaced[row][input_axis] = target_basis[row][output_axis];
            }
            let numerator = determinant_small(&replaced)?;
            if numerator % denominator != 0 {
                return None;
            }
            let value = numerator / denominator;
            if value < -(bound as i128) || value > bound as i128 {
                return None;
            }
            matrix[output_axis * d + input_axis] = i64::try_from(value).ok()?;
        }
    }
    // Verify every aligned pair, not just the selected basis.
    for (sx, ty) in &pairs {
        for output_axis in 0..d {
            let mut predicted = 0i128;
            for input_axis in 0..d {
                predicted = predicted.checked_add(
                    (matrix[output_axis * d + input_axis] as i128)
                        .checked_mul(sx[input_axis] - source_origin[input_axis])?,
                )?;
            }
            if predicted != ty[output_axis] - target_origin[output_axis] {
                return None;
            }
        }
    }
    Some(matrix)
}

fn relation_values(value: &Value) -> Option<&[Value]> {
    match value {
        Value::Tuple(xs) | Value::List(xs) => Some(xs.as_slice()),
        _ => None,
    }
}

fn independent_displacement_rows(rows: &[Vec<i128>], d: usize) -> Option<bool> {
    match (d, rows.len()) {
        (1, 1) => Some(rows[0][0] != 0),
        (3, 1) => Some(rows[0].iter().any(|x| *x != 0)),
        (3, 2) => {
            let a = &rows[0];
            let b = &rows[1];
            let cross = [
                a[1].checked_mul(b[2])?.checked_sub(a[2].checked_mul(b[1])?)?,
                a[2].checked_mul(b[0])?.checked_sub(a[0].checked_mul(b[2])?)?,
                a[0].checked_mul(b[1])?.checked_sub(a[1].checked_mul(b[0])?)?,
            ];
            Some(cross.iter().any(|x| *x != 0))
        }
        (3, 3) => Some(determinant_small(rows)? != 0),
        _ => None,
    }
}

/// Exact determinant for the dimensions admitted by the feature-gated solver.
fn determinant_small(matrix: &[Vec<i128>]) -> Option<i128> {
    match matrix.len() {
        1 if matrix[0].len() == 1 => Some(matrix[0][0]),
        2 if matrix.iter().all(|r| r.len() == 2) => matrix[0][0]
            .checked_mul(matrix[1][1])?
            .checked_sub(matrix[0][1].checked_mul(matrix[1][0])?),
        3 if matrix.iter().all(|r| r.len() == 3) => {
            let a = matrix[0][0].checked_mul(
                matrix[1][1].checked_mul(matrix[2][2])?
                    .checked_sub(matrix[1][2].checked_mul(matrix[2][1])?)?,
            )?;
            let b = matrix[0][1].checked_mul(
                matrix[1][0].checked_mul(matrix[2][2])?
                    .checked_sub(matrix[1][2].checked_mul(matrix[2][0])?)?,
            )?;
            let c = matrix[0][2].checked_mul(
                matrix[1][0].checked_mul(matrix[2][1])?
                    .checked_sub(matrix[1][1].checked_mul(matrix[2][0])?)?,
            )?;
            a.checked_sub(b)?.checked_add(c)
        }
        _ => None,
    }
}

#[cfg(feature = "geninfer_quadratic_map_solver")]
#[derive(Clone, Copy)]
struct ExactRat {
    numerator: i128,
    denominator: i128,
}

#[cfg(feature = "geninfer_quadratic_map_solver")]
fn gcd_i128_checked(mut a: i128, mut b: i128) -> Option<i128> {
    a = a.checked_abs()?;
    b = b.checked_abs()?;
    while b != 0 {
        let r = a % b;
        a = b;
        b = r;
    }
    Some(a.max(1))
}

#[cfg(feature = "geninfer_quadratic_map_solver")]
impl ExactRat {
    fn new(mut numerator: i128, mut denominator: i128) -> Option<Self> {
        if denominator == 0 { return None; }
        if denominator < 0 {
            numerator = numerator.checked_neg()?;
            denominator = denominator.checked_neg()?;
        }
        let gcd = gcd_i128_checked(numerator, denominator)?;
        Some(Self { numerator: numerator / gcd, denominator: denominator / gcd })
    }
    fn integer(value: i128) -> Self { Self { numerator: value, denominator: 1 } }
    fn is_zero(self) -> bool { self.numerator == 0 }
    fn add(self, other: Self) -> Option<Self> {
        let g = gcd_i128_checked(self.denominator, other.denominator)?;
        let a = other.denominator / g;
        let b = self.denominator / g;
        Self::new(self.numerator.checked_mul(a)?.checked_add(other.numerator.checked_mul(b)?)?,
                  self.denominator.checked_mul(a)?)
    }
    fn sub(self, other: Self) -> Option<Self> {
        Self::new(other.numerator.checked_neg()?, other.denominator)?.add(self)
    }
    fn mul(self, other: Self) -> Option<Self> {
        let g1 = gcd_i128_checked(self.numerator, other.denominator)?;
        let g2 = gcd_i128_checked(other.numerator, self.denominator)?;
        Self::new((self.numerator / g1).checked_mul(other.numerator / g2)?,
                  (self.denominator / g2).checked_mul(other.denominator / g1)?)
    }
    fn div(self, other: Self) -> Option<Self> {
        if other.numerator == 0 { return None; }
        self.mul(Self::new(other.denominator, other.numerator)?)
    }
}

#[cfg(feature = "geninfer_quadratic_map_solver")]
fn infer_quadratic2_coefficients(
    source: &[Value],
    target: &[Value],
    dim_types: &[String],
    coord_dims: &[i64],
) -> Result<Vec<i64>, &'static str> {
    if coord_dims.len() != 2 || source.len() != target.len() || source.len() < 7 {
        return Err("unsupported_shape");
    }
    let mut stable_slots = vec![0usize];
    stable_slots.extend(dim_types.iter().enumerate().filter_map(|(i, t)| (t == "id").then_some(i)));
    if stable_slots.len() < 2 { return Err("identity_missing"); }
    let mut used = vec![false; target.len()];
    let mut aligned = Vec::with_capacity(source.len());
    for src in source {
        let sr = relation_values(src).ok_or("malformed_relation")?;
        if sr.len() != dim_types.len() { return Err("malformed_relation"); }
        let mut found = None;
        for (i, dst) in target.iter().enumerate() {
            let dr = relation_values(dst).ok_or("malformed_relation")?;
            if dr.len() != dim_types.len() { return Err("malformed_relation"); }
            if stable_slots.iter().all(|&slot| sr.get(slot) == dr.get(slot)) {
                if found.is_some() || used[i] { return Err("identity_ambiguous"); }
                found = Some(i);
            }
        }
        let i = found.ok_or("identity_incomplete")?;
        used[i] = true;
        aligned.push(i);
    }
    if used.iter().any(|v| !v) { return Err("identity_incomplete"); }

    let ix = usize::try_from(coord_dims[0]).map_err(|_| "malformed_relation")?;
    let iy = usize::try_from(coord_dims[1]).map_err(|_| "malformed_relation")?;
    let mut raw_x = Vec::with_capacity(source.len());
    let mut raw_y = Vec::with_capacity(source.len());
    let mut raw_u = Vec::with_capacity(source.len());
    let mut raw_v = Vec::with_capacity(source.len());
    for (si, &ti) in aligned.iter().enumerate() {
        let sr = relation_values(&source[si]).ok_or("malformed_relation")?;
        let tr = relation_values(&target[ti]).ok_or("malformed_relation")?;
        let (Some(Value::Int(x)), Some(Value::Int(y)), Some(Value::Int(u)), Some(Value::Int(v))) =
            (sr.get(ix), sr.get(iy), tr.get(ix), tr.get(iy)) else { return Err("non_integer"); };
        raw_x.push(*x); raw_y.push(*y); raw_u.push(*u); raw_v.push(*v);
    }
    let min_x = *raw_x.iter().min().ok_or("unsupported_shape")? as i128;
    let min_y = *raw_y.iter().min().ok_or("unsupported_shape")? as i128;
    let mut design: Vec<[i128; 5]> = Vec::with_capacity(source.len() - 1);
    let mut outputs: Vec<[i128; 2]> = Vec::with_capacity(source.len() - 1);
    let (x0, y0) = (raw_x[0] as i128 - min_x, raw_y[0] as i128 - min_y);
    let phi = |x: i128, y: i128| -> Option<[i128; 5]> {
        Some([x, y, x.checked_mul(x)?, x.checked_mul(y)?, y.checked_mul(y)?])
    };
    let base_phi = phi(x0, y0).ok_or("overflow")?;
    for i in 1..source.len() {
        let x = (raw_x[i] as i128).checked_sub(min_x).ok_or("overflow")?;
        let y = (raw_y[i] as i128).checked_sub(min_y).ok_or("overflow")?;
        let f = phi(x, y).ok_or("overflow")?;
        let mut row = [0i128; 5];
        for j in 0..5 { row[j] = f[j].checked_sub(base_phi[j]).ok_or("overflow")?; }
        design.push(row);
        outputs.push([
            (raw_u[i] as i128).checked_sub(raw_u[0] as i128).ok_or("overflow")?,
            (raw_v[i] as i128).checked_sub(raw_v[0] as i128).ok_or("overflow")?,
        ]);
    }

    let mut a: Vec<Vec<ExactRat>> = design.iter().zip(&outputs).map(|(row, out)| {
        row.iter().map(|v| ExactRat::integer(*v))
            .chain(out.iter().map(|v| ExactRat::integer(*v))).collect()
    }).collect();
    let mut pivot_rows = Vec::with_capacity(5);
    let mut pivot_row = 0usize;
    for col in 0..5 {
        let Some(pivot) = (pivot_row..a.len()).find(|&r| !a[r][col].is_zero()) else { continue };
        a.swap(pivot_row, pivot);
        let divisor = a[pivot_row][col];
        for c in 0..7 { a[pivot_row][c] = a[pivot_row][c].div(divisor).ok_or("overflow")?; }
        let pivot_values = a[pivot_row].clone();
        for r in 0..a.len() {
            if r == pivot_row || a[r][col].is_zero() { continue; }
            let factor = a[r][col];
            for c in 0..7 {
                a[r][c] = a[r][c].sub(factor.mul(pivot_values[c]).ok_or("overflow")?).ok_or("overflow")?;
            }
        }
        pivot_rows.push(pivot_row);
        pivot_row += 1;
    }
    if pivot_rows.len() != 5 { return Err("rank_deficient"); }
    for row in &a {
        if row[..5].iter().all(|v| v.is_zero()) && (!row[5].is_zero() || !row[6].is_zero()) {
            return Err("residual_mismatch");
        }
    }
    let mut coefficients = Vec::with_capacity(10);
    for axis in 0..2 {
        for &r in &pivot_rows {
            let value = a[r][5 + axis];
            if value.denominator != 1 { return Err("non_integral"); }
            if value.numerator < -8 || value.numerator > 8 { return Err("coefficient_bound"); }
            coefficients.push(i64::try_from(value.numerator).map_err(|_| "overflow")?);
        }
    }
    // Exact overdetermined consistency check, including every validation row.
    for i in 0..design.len() {
        for axis in 0..2 {
            let mut predicted = 0i128;
            for j in 0..5 {
                predicted = predicted.checked_add(
                    (coefficients[axis * 5 + j] as i128).checked_mul(design[i][j]).ok_or("overflow")?
                ).ok_or("overflow")?;
            }
            if predicted != outputs[i][axis] { return Err("residual_mismatch"); }
        }
    }
    Ok(coefficients)
}

/// Evaluate `GenInfer` — the GENERATOR-MINTING op, the DELTA on `DimInfer`
/// (rung 2) at the exact point the held generator codebook is exhausted
/// WITHOUT a match. Where `DimInfer` SELECTS from a finite named codebook
/// (`rotation90`/`reflection_*`/`scale2`/`modular`), `GenInfer` INFERS a
/// NEW general integer-linear generator FROM THE ORBIT and reports its
/// matrix so a rule can MINT it as graph data (a `DimensionGenerator`
/// `{kind:"linear", matrix:…}` — see `apply_linear_once`), grow the
/// codebook, and re-decode.
///
/// The inference is DimInfer-native generate-and-test, but over a
/// PARAMETERIZED FAMILY (all integer `n×n` maps within a DATA-DERIVED
/// bound) rather than a named list: for each held part with `dim_types`,
/// with `coord_dims` = its `"coord:*"` slots, enumerate every integer
/// matrix `M` whose entries lie in `[-B, B]`, where `B` is the maximum
/// absolute NORMALIZED coordinate observed across the base and the goal
/// (READ FROM THE DATA — a map that carries the base's own lattice steps
/// into the goal cannot place a coordinate outside the extent it produces,
/// so `B` is fixed by the shapes, not chosen; a map needing an entry beyond
/// that extent is not identifiable from this orbit — an honest scope
/// limit, not a tuned cutoff). Apply `M` via the SAME `apply_linear_once`
/// a minted generator will use, then run the SAME rung-1 consistency check
/// (`build_candidate`) `DimInfer` runs — so a SUCCESS here is exactly what
/// re-decode reproduces. The IDENTITY map is excluded (a genuinely new
/// generator is non-trivial; `M = I` with zero residual is an exact held
/// match, and `M = I` with a residual is rung-1's own job, already run).
///
/// Occam (deterministic): fewest residual dims, then smallest `Σ|entry|`,
/// then lexicographically-smallest matrix, then base name. `explained`
/// (bool) / `base` (winning part name) / `matrix` (Tuple of Ints, flattened
/// row-major — mint as the `matrix` attr) / `coord_dims` (Tuple of Ints —
/// mint as `coord_dims`) / `ncoord` (Int) / `residual_dims` (Int) /
/// `transforms` (leftover per-dim deltas, same shape as `DimInfer`) /
/// `dims` / `checked` (candidate matrices passed to validation). Integer
/// lattice only. The default path enumerates 2-D matrices; an opt-in exact
/// full-rank solver admits 1-D and 3-D candidates. Rank-deficient or
/// ambiguously aligned higher-dimensional parts are skipped.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_gen_infer(
    arena: &TermArena,
    goal_idx: TermIdx,
    codebook_type: Sym,
    exclude_idx: Option<TermIdx>,
    scope_value: Value,
    require_scope: bool,
    quadratic_enabled: bool,
    linear_prefilter_enabled: bool,
    grain: i64,
    mdl_enabled: bool,
    max_dims: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_GEN_INFER);
    crate::scale_audit::gen_infer_kernel_call();
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let mut parts = if scope_value == Value::None {
        if require_scope {
            Vec::new()
        } else {
            load_parts(ctx, codebook_type, &mut extra, &mut next_id)
        }
    } else {
        load_parts_with_scope(
            ctx,
            codebook_type,
            &mut extra,
            &mut next_id,
            Some(&scope_value),
        )
    };
    apply_exclude(&mut parts, exclude_idx, arena, env, ctx);
    let extra_rev: FxHashMap<Sym, String> = extra.iter().map(|(k, v)| (*v, k.clone())).collect();

    let goal_val = evaluate(arena, goal_idx, env, ctx);
    let mut goal: Vec<Value> = match &goal_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
            goal_val.iter().cloned().collect()
        }
        _ => Vec::new(),
    };
    // WP3 grain: re-quantize coordinate slots of base and goal to a coarser
    // grain before ANY search, so every exact stage (and the enumerator)
    // runs unchanged at that grain. In-frame values stay integer.
    if grain > 0 {
        let coord_slots = |dts: &[String]| -> Vec<usize> {
            dts.iter().enumerate().filter(|(_, t)| t.starts_with("coord:")).map(|(i, _)| i).collect()
        };
        if let Some(dts) = parts.iter().find_map(|p| p.dim_types.clone()) {
            goal = requantize(&goal, &coord_slots(&dts), grain);
            if coarse_degenerate(&goal, &coord_slots(&dts)) {
                goal.clear();
            }
        }
        for part in parts.iter_mut() {
            if let Some(dts) = part.dim_types.clone() {
                part.sig = requantize(&part.sig, &coord_slots(&dts), grain);
            }
        }
    }
    let max_dims_usize = max_dims.max(0) as usize;
    let mut sorted_o = goal.clone();
    sorted_o.sort_by(cmp_value);

    // Data-derived search bound B — the maximum absolute NORMALIZED
    // coordinate over the goal's coord slots (computed against the goal's
    // own per-slot min). Falls out of the observation's own extent.
    let goal_coord_slots: Vec<usize> = {
        // Use the FIRST part's dim_types to learn which slots are coords;
        // all parts in a codebook share the frame. (If none has dim_types,
        // no inference is possible anyway.)
        parts
            .iter()
            .find_map(|p| p.dim_types.as_ref())
            .map(|dts| {
                dts.iter()
                    .enumerate()
                    .filter(|(_, t)| t.starts_with("coord:"))
                    .map(|(i, _)| i)
                    .collect()
            })
            .unwrap_or_default()
    };
    let goal_bound: i64 = goal_coord_slots
        .iter()
        .filter_map(|&idx| {
            let vs = coord_ints(&goal, idx)?;
            let mn = *vs.iter().min()?;
            vs.iter().map(|v| (v - mn).abs()).max()
        })
        .max()
        .unwrap_or(0);

    let mut checked: i64 = 0;
    let mut eligible_bases: u64 = 0;
    let mut apply_rejects: u64 = 0;
    let mut candidate_rejects: u64 = 0;
    let mut residual_rejects: u64 = 0;
    let mut candidate_survivors: u64 = 0;
    let mut bases_by_bound: FxHashMap<i64, u64> = FxHashMap::default();
    let mut full_rank_bases: u64 = 0;
    let mut full_rank_refusals: u64 = 0;
    let mut full_rank_attempts: u64 = 0;
    let mut full_rank_apply_rejects: u64 = 0;
    let mut full_rank_candidate_rejects: u64 = 0;
    let mut full_rank_residual_rejects: u64 = 0;
    let mut full_rank_survivors: u64 = 0;
    let mut best: Option<GenAttempt> = None;
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    let (mut prefilter_attempts, mut prefilter_solved, mut prefilter_no_fit, mut prefilter_fallback, mut prefilter_input_relations) = (0u64, 0u64, 0u64, 0u64, 0u64);
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    let (mut prefilter_identity_comparisons, mut prefilter_arithmetic_checks) = (0u64, 0u64);
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    let (mut prefilter_no_fit_reasons, mut prefilter_fallback_reasons): (FxHashMap<&'static str,u64>, FxHashMap<&'static str,u64>) = (FxHashMap::default(), FxHashMap::default());
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    let (mut rowf_attempts, mut rowf_solved, mut rowf_no_candidate, mut rowf_fallback, mut rowf_row_evaluations) = (0u64, 0u64, 0u64, 0u64, 0u64);
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    let (mut rowf_no_candidate_reasons, mut rowf_fallback_reasons): (FxHashMap<&'static str,u64>, FxHashMap<&'static str,u64>) = (FxHashMap::default(), FxHashMap::default());
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    let (mut corr_attempts, mut corr_found, mut corr_no_candidate, mut corr_fallback, mut corr_hypotheses, mut corr_validations) = (0u64, 0u64, 0u64, 0u64, 0u64, 0u64);
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    let (mut corr_no_candidate_reasons, mut corr_fallback_reasons): (FxHashMap<&'static str,u64>, FxHashMap<&'static str,u64>) = (FxHashMap::default(), FxHashMap::default());

    for part in &parts {
        let Some(dim_types) = &part.dim_types else {
            continue;
        };
        let coord_dims: Vec<i64> = dim_types
            .iter()
            .enumerate()
            .filter(|(_, t)| t.starts_with("coord:"))
            .map(|(i, _)| i as i64)
            .collect();
        let n = coord_dims.len();
        if n != 2 {
            if cfg!(feature = "geninfer_full_rank_matrix_solver")
                && matches!(n, 1 | 3)
            {
                let base_bound: i64 = coord_dims
                    .iter()
                    .filter_map(|&d| {
                        let idx = usize::try_from(d).ok()?;
                        let vs = coord_ints(&part.sig, idx)?;
                        let mn = *vs.iter().min()?;
                        vs.iter().map(|v| (v - mn).abs()).max()
                    })
                    .max()
                    .unwrap_or(0);
                let b = goal_bound.max(base_bound);
                if b > 0 {
                    full_rank_bases += 1;
                    match infer_full_rank_integer_matrix(
                        &part.sig,
                        &goal,
                        dim_types,
                        &coord_dims,
                        b,
                    ) {
                        Some(matrix) if matrix.iter().any(|v| *v != 0) => {
                            let is_identity = (0..n).all(|r| {
                                (0..n).all(|c| matrix[r * n + c] == i64::from(r == c))
                            });
                            if is_identity {
                                full_rank_refusals += 1;
                                continue;
                            }
                            checked += 1;
                            full_rank_attempts += 1;
                            crate::access_trace::note_helper_work(51, 1);
                            let Some(transformed) =
                                apply_linear_once(&part.sig, &coord_dims, &matrix)
                            else {
                                full_rank_apply_rejects += 1;
                                continue;
                            };
                            let Some(cand) = build_candidate(
                                part.name.clone(),
                                part.name_val.clone(),
                                &transformed,
                                &sorted_o,
                                max_dims_usize,
                                &extra_rev,
                                cfg!(feature = "geninfer_fused_candidate_validation"),
                            ) else {
                                full_rank_candidate_rejects += 1;
                                continue;
                            };
                            if cand.transforms.len() != cand.dims_needed.len() {
                                full_rank_residual_rejects += 1;
                                continue;
                            }
                            full_rank_survivors += 1;
                            let abs_sum = matrix.iter().fold(0i64, |sum, v| {
                                sum.saturating_add(v.saturating_abs())
                            });
                            let att = GenAttempt {
                                base_val: cand.name_val.clone(),
                                base_name: cand.name.clone(),
                                kind: "linear".to_string(),
                                coord_dims: coord_dims.clone(),
                                matrix,
                                coefficients: Vec::new(),
                                transforms: cand.transforms,
                                residual_dims: cand.dims_needed.len(),
                                abs_sum,
                            };
                            let take = match &best {
                                None => true,
                                Some(cur) => {
                                    (att.residual_dims, att.abs_sum, &att.matrix, &att.base_name)
                                        < (cur.residual_dims, cur.abs_sum, &cur.matrix, &cur.base_name)
                                }
                            };
                            if take {
                                best = Some(att);
                            }
                        }
                        _ => full_rank_refusals += 1,
                    }
                }
            }
            // The exact-solve path is deliberately feature-gated and only
            // admits uniquely identifiable 1-D/3-D maps. Other dimensions
            // and rank-deficient inputs retain the documented refusal.
            continue;
        }
        // Base's own normalized extent contributes to the bound too — a map
        // stretching a large base needs entries no larger than the extent
        // it produces, already captured by goal_bound; but a base larger
        // than the goal (a contracting map) also bounds |entry| by the base
        // extent. Take the max of the two so the range is sound in both
        // directions and still purely data-derived.
        let base_bound: i64 = coord_dims
            .iter()
            .filter_map(|&d| {
                let idx = usize::try_from(d).ok()?;
                let vs = coord_ints(&part.sig, idx)?;
                let mn = *vs.iter().min()?;
                vs.iter().map(|v| (v - mn).abs()).max()
            })
            .max()
            .unwrap_or(0);
        let b = goal_bound.max(base_bound);
        if b <= 0 {
            continue;
        }
        eligible_bases += 1;
        *bases_by_bound.entry(b).or_insert(0) += 1;

        // With the opt-in exact prefilter, uniquely aligned full-rank data
        // determines at most one integer linear map. A proved fit is checked
        // through the ordinary candidate path; a proved non-fit skips the
        // combinatorial matrix loop. Any ambiguity or unsupported value falls
        // through to the historical exhaustive search.
        #[cfg(feature = "geninfer_linear_exact_prefilter")]
        if linear_prefilter_enabled {
            prefilter_attempts += 1;
            prefilter_input_relations = prefilter_input_relations.saturating_add((part.sig.len() + goal.len()) as u64);
            PREFILTER_IDENTITY_VALUE_COMPARISONS.with(|n| n.set(0));
            PREFILTER_EXACT_ARITHMETIC_CHECKS.with(|n| n.set(0));
            let prefilter_result = infer_exact_2d_linear_prefilter(&part.sig, &goal, dim_types, &coord_dims, b);
            PREFILTER_IDENTITY_VALUE_COMPARISONS.with(|n| prefilter_identity_comparisons = prefilter_identity_comparisons.saturating_add(n.get()));
            PREFILTER_EXACT_ARITHMETIC_CHECKS.with(|n| prefilter_arithmetic_checks = prefilter_arithmetic_checks.saturating_add(n.get()));
            match prefilter_result {
                ExactLinearPrefilter::Solved(matrix) => {
                    prefilter_solved += 1;
                    let identity = matrix == [1, 0, 0, 1];
                    if !identity {
                        checked += 1;
                        crate::access_trace::note_helper_work(51, 1);
                        if let Some(transformed) = apply_linear_once(&part.sig, &coord_dims, &matrix) {
                            if let Some(cand) = build_candidate(
                                part.name.clone(), part.name_val.clone(), &transformed,
                                &sorted_o, max_dims_usize, &extra_rev,
                                cfg!(feature = "geninfer_fused_candidate_validation"),
                            ) {
                                if cand.transforms.len() == cand.dims_needed.len() {
                                    candidate_survivors += 1;
                                    let abs_sum = matrix.iter().fold(0i64, |s, v| s.saturating_add(v.saturating_abs()));
                                    let att = GenAttempt {
                                        base_val: cand.name_val.clone(), base_name: cand.name.clone(),
                                        kind: "linear".to_string(), coord_dims: coord_dims.clone(),
                                        matrix, coefficients: Vec::new(), transforms: cand.transforms,
                                        residual_dims: cand.dims_needed.len(), abs_sum,
                                    };
                                    if best.as_ref().is_none_or(|cur| (att.residual_dims, att.abs_sum, &att.matrix, &att.base_name) < (cur.residual_dims, cur.abs_sum, &cur.matrix, &cur.base_name)) { best = Some(att); }
                                } else { residual_rejects += 1; }
                            } else { candidate_rejects += 1; }
                        } else { apply_rejects += 1; }
                    }
                    continue;
                }
                ExactLinearPrefilter::ProvenNoFit(reason) => { prefilter_no_fit += 1; *prefilter_no_fit_reasons.entry(reason).or_insert(0) += 1; continue; },
                ExactLinearPrefilter::Fallback(reason) => {
                    prefilter_fallback += 1; *prefilter_fallback_reasons.entry(reason).or_insert(0) += 1;
                    rowf_attempts += 1;
                    match infer_row_factorized_2d_linear(&part.sig, &sorted_o, &coord_dims, b, max_dims_usize, &extra_rev, &mut rowf_row_evaluations) {
                        RowFactorizedSearch::Solved(matrix, expected_dims) => {
                            checked += 1;
                            crate::access_trace::note_helper_work(51, 1);
                            let validated = apply_linear_once(&part.sig, &coord_dims, &matrix).and_then(|transformed| build_candidate(
                                part.name.clone(), part.name_val.clone(), &transformed,
                                &sorted_o, max_dims_usize, &extra_rev,
                                cfg!(feature = "geninfer_fused_candidate_validation"),
                            )).filter(|cand| cand.transforms.len() == cand.dims_needed.len() && cand.dims_needed.len() == expected_dims);
                            if let Some(cand) = validated {
                                rowf_solved += 1;
                                candidate_survivors += 1;
                                let abs_sum = matrix.iter().fold(0i64, |s, v| s.saturating_add(v.saturating_abs()));
                                let att = GenAttempt {
                                    base_val: cand.name_val.clone(), base_name: cand.name.clone(),
                                    kind: "linear".to_string(), coord_dims: coord_dims.clone(),
                                    matrix, coefficients: Vec::new(), transforms: cand.transforms,
                                    residual_dims: cand.dims_needed.len(), abs_sum,
                                };
                                if best.as_ref().is_none_or(|cur| (att.residual_dims, att.abs_sum, &att.matrix, &att.base_name) < (cur.residual_dims, cur.abs_sum, &cur.matrix, &cur.base_name)) { best = Some(att); }
                                continue;
                            }
                            // Defensive: a disagreement with the validator
                            // hands the base to the historical enumerator.
                            rowf_fallback += 1; *rowf_fallback_reasons.entry("validation_mismatch").or_insert(0) += 1;
                        }
                        RowFactorizedSearch::NoCandidate(r) => { rowf_no_candidate += 1; *rowf_no_candidate_reasons.entry(r).or_insert(0) += 1; continue; }
                        RowFactorizedSearch::Fallback(r) => { rowf_fallback += 1; *rowf_fallback_reasons.entry(r).or_insert(0) += 1; }
                    }
                    corr_attempts += 1;
                    match infer_correspondence_2d_linear(&part.name, &part.name_val, &part.sig, &sorted_o, &coord_dims, b, max_dims_usize, &extra_rev, &mut corr_hypotheses, &mut corr_validations) {
                        CorrespondenceSearch::Found(matrix, cand) => {
                            corr_found += 1;
                            candidate_survivors += 1;
                            checked += 1;
                            let abs_sum = matrix.iter().fold(0i64, |s, v| s.saturating_add(v.saturating_abs()));
                            let att = GenAttempt {
                                base_val: cand.name_val.clone(), base_name: cand.name.clone(),
                                kind: "linear".to_string(), coord_dims: coord_dims.clone(),
                                matrix, coefficients: Vec::new(), transforms: cand.transforms,
                                residual_dims: cand.dims_needed.len(), abs_sum,
                            };
                            if best.as_ref().is_none_or(|cur| (att.residual_dims, att.abs_sum, &att.matrix, &att.base_name) < (cur.residual_dims, cur.abs_sum, &cur.matrix, &cur.base_name)) { best = Some(att); }
                            continue;
                        }
                        CorrespondenceSearch::NoCandidate(r) => { corr_no_candidate += 1; *corr_no_candidate_reasons.entry(r).or_insert(0) += 1; continue; }
                        CorrespondenceSearch::Fallback(r) => { corr_fallback += 1; *corr_fallback_reasons.entry(r).or_insert(0) += 1; }
                    }
                }
            }
        }
        #[cfg(not(feature = "geninfer_linear_exact_prefilter"))]
        let _ = linear_prefilter_enabled;

        // Enumerate every integer 2×2 matrix with entries in [-b, b].
        for m00 in -b..=b {
            for m01 in -b..=b {
                for m10 in -b..=b {
                    for m11 in -b..=b {
                        // Exclude the identity (a genuinely-new generator is non-trivial;
                        // identity is rung-1's job, already run and failed).
                        if m00 == 1 && m01 == 0 && m10 == 0 && m11 == 1 {
                            continue;
                        }
                        let matrix = vec![m00, m01, m10, m11];
                        checked += 1;
                        crate::access_trace::note_helper_work(51, 1);
                        let Some(transformed) = apply_linear_once(&part.sig, &coord_dims, &matrix)
                        else {
                            apply_rejects += 1;
                            continue;
                        };
                        let Some(cand) = build_candidate(
                            part.name.clone(),
                            part.name_val.clone(),
                            &transformed,
                            &sorted_o,
                            max_dims_usize,
                            &extra_rev,
                            cfg!(feature = "geninfer_fused_candidate_validation"),
                        ) else {
                            candidate_rejects += 1;
                            continue;
                        };
                        if cand.transforms.len() != cand.dims_needed.len() {
                            residual_rejects += 1;
                            continue;
                        }
                        candidate_survivors += 1;
                        let abs_sum = m00.abs() + m01.abs() + m10.abs() + m11.abs();
                        let att = GenAttempt {
                            base_val: cand.name_val.clone(),
                            base_name: cand.name.clone(),
                            kind: "linear".to_string(),
                            coord_dims: coord_dims.clone(),
                            matrix,
                            coefficients: Vec::new(),
                            transforms: cand.transforms,
                            residual_dims: cand.dims_needed.len(),
                            abs_sum,
                        };
                        let take = match &best {
                            None => true,
                            Some(cur) => {
                                (att.residual_dims, att.abs_sum, &att.matrix, &att.base_name)
                                    < (cur.residual_dims, cur.abs_sum, &cur.matrix, &cur.base_name)
                            }
                        };
                        if take {
                            best = Some(att);
                        }
                    }
                }
            }
        }
    }

    #[cfg(feature = "geninfer_quadratic_map_solver")]
    let mut quadratic_attempts = 0u64;
    #[cfg(feature = "geninfer_quadratic_map_solver")]
    let mut quadratic_refusals: FxHashMap<&'static str, u64> = FxHashMap::default();
    #[cfg(feature = "geninfer_quadratic_map_solver")]
    let mut quadratic_validation_rejects = 0u64;
    #[cfg(feature = "geninfer_quadratic_map_solver")]
    let mut quadratic_survivors = 0u64;

    // Occam gate: the experimental fixed-size polynomial solve is reached
    // only when the historical matrix/codebook search found no exact fit,
    // the Cargo feature is present, and the caller explicitly enabled it.
    #[cfg(feature = "geninfer_quadratic_map_solver")]
    if best.is_none() && quadratic_enabled {
        for part in &parts {
            let Some(dim_types) = &part.dim_types else { continue };
            let coord_dims: Vec<i64> = dim_types.iter().enumerate()
                .filter(|(_, t)| t.starts_with("coord:"))
                .map(|(i, _)| i as i64).collect();
            if coord_dims.len() != 2 { continue; }
            quadratic_attempts += 1;
            let coefficients = match infer_quadratic2_coefficients(
                &part.sig, &goal, dim_types, &coord_dims,
            ) {
                Ok(value) => value,
                Err(reason) => {
                    *quadratic_refusals.entry(reason).or_insert(0) += 1;
                    continue;
                }
            };
            let Some(transformed) = apply_quadratic2_once(&part.sig, &coord_dims, &coefficients) else {
                *quadratic_refusals.entry("apply_overflow").or_insert(0) += 1;
                continue;
            };
            let Some(cand) = build_candidate(
                part.name.clone(), part.name_val.clone(), &transformed, &sorted_o,
                max_dims_usize, &extra_rev, false,
            ) else {
                quadratic_validation_rejects += 1;
                continue;
            };
            if cand.transforms.len() != cand.dims_needed.len() {
                quadratic_validation_rejects += 1;
                continue;
            }
            quadratic_survivors += 1;
            let abs_sum = coefficients.iter().fold(0i64, |sum, c| sum.saturating_add(c.saturating_abs()));
            let att = GenAttempt {
                base_val: cand.name_val.clone(),
                base_name: cand.name.clone(),
                kind: "quadratic2".to_string(),
                coord_dims: coord_dims.clone(),
                matrix: Vec::new(),
                coefficients,
                transforms: cand.transforms,
                residual_dims: cand.dims_needed.len(),
                abs_sum,
            };
            let take = match &best {
                None => true,
                Some(cur) => (att.residual_dims, att.abs_sum, &att.coefficients, &att.base_name)
                    < (cur.residual_dims, cur.abs_sum, &cur.coefficients, &cur.base_name),
            };
            if take { best = Some(att); }
        }
    }

    #[allow(unused_mut)]
    let mut mdl: Option<(Vec<i64>, Vec<i64>, Vec<Value>, i64, i64)> = None; // (matrix, coord_dims, outliers, bits, raw_bits)
    #[cfg(feature = "geninfer_grain_mdl")]
    if best.is_none() && mdl_enabled {
        for part in &parts {
            let Some(dim_types) = &part.dim_types else { continue };
            let coord_dims: Vec<i64> = dim_types.iter().enumerate()
                .filter(|(_, t)| t.starts_with("coord:")).map(|(i, _)| i as i64).collect();
            if coord_dims.len() != 2 { continue; }
            let base_bound: i64 = coord_dims.iter().filter_map(|&d| {
                let vs = coord_ints(&part.sig, d as usize)?; let mn = *vs.iter().min()?; vs.iter().map(|v| (v - mn).abs()).max()
            }).max().unwrap_or(0);
            let b = goal_bound.max(base_bound);
            if b <= 0 { continue; }
            if let Some((m, outl, bits, raw)) = infer_mdl_2d_linear(&part.sig, &goal, &coord_dims, b) {
                if mdl.as_ref().is_none_or(|cur| bits < cur.3) {
                    best = Some(GenAttempt {
                        base_val: part.name_val.clone(), base_name: part.name.clone(), kind: "linear".to_string(),
                        coord_dims: coord_dims.clone(), matrix: m.clone(), coefficients: Vec::new(),
                        transforms: Vec::new(), residual_dims: 0,
                        abs_sum: m.iter().map(|x| x.abs()).sum(),
                    });
                    mdl = Some((m, coord_dims.clone(), outl, bits, raw));
                }
            }
        }
    }
    #[cfg(not(feature = "geninfer_grain_mdl"))]
    let _ = mdl_enabled;
    let result = match &best {
        Some(win) => {
            let transforms_out: SmallVec<[Value; 4]> =
                win.transforms.iter().map(DimTransform::to_value).collect();
            let dims_val: SmallVec<[Value; 4]> = transforms_out
                .iter()
                .map(|t| select_field(t, "dim", None))
                .collect();
            let matrix_out: SmallVec<[Value; 4]> =
                win.matrix.iter().map(|m| Value::Int(*m)).collect();
            let coefficients_out: SmallVec<[Value; 4]> =
                win.coefficients.iter().map(|c| Value::Int(*c)).collect();
            let coord_dims_out: SmallVec<[Value; 4]> =
                win.coord_dims.iter().map(|d| Value::Int(*d)).collect();
            Value::Dict(Arc::from(vec![
                (surf("explained"), Value::Bool(true)),
                (surf("base"), win.base_val.clone()),
                (surf("kind"), surf(&win.kind)),
                (surf("matrix"), Value::Tuple(Arc::new(matrix_out))),
                (surf("coefficients"), Value::Tuple(Arc::new(coefficients_out))),
                (surf("coord_dims"), Value::Tuple(Arc::new(coord_dims_out))),
                (surf("ncoord"), Value::Int(win.coord_dims.len() as i64)),
                (surf("residual_dims"), Value::Int(win.residual_dims as i64)),
                (surf("transforms"), Value::Tuple(Arc::new(transforms_out))),
                (surf("dims"), Value::Tuple(Arc::new(dims_val))),
                (surf("checked"), Value::Int(checked)),
                (surf("grain"), Value::Int(grain)),
                (surf("witness"), surf(if mdl.is_some() { "mdl" } else { "exact" })),
                (surf("outliers"), Value::Tuple(Arc::new(mdl.as_ref().map(|m| m.2.iter().cloned().collect()).unwrap_or_default()))),
                (surf("mdl_bits"), mdl.as_ref().map(|m| Value::Int(m.3)).unwrap_or(Value::None)),
                (surf("raw_bits"), mdl.as_ref().map(|m| Value::Int(m.4)).unwrap_or(Value::None)),
            ]))
        }
        None => Value::Dict(Arc::from(vec![
            (surf("grain"), Value::Int(grain)),
            (surf("witness"), Value::None),
            (surf("outliers"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("explained"), Value::Bool(false)),
            (surf("base"), Value::None),
            (surf("kind"), Value::None),
            (surf("matrix"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("coefficients"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("coord_dims"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("ncoord"), Value::Int(0)),
            (surf("residual_dims"), Value::Int(0)),
            (surf("transforms"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("dims"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("checked"), Value::Int(checked)),
        ])),
    };
    crate::scale_audit::gen_infer_search_result(
        eligible_bases,
        checked as u64,
        apply_rejects,
        candidate_rejects,
        residual_rejects,
        candidate_survivors,
        &bases_by_bound,
    );
    crate::scale_audit::gen_infer_full_rank_result(
        full_rank_bases,
        full_rank_refusals,
        full_rank_attempts,
        full_rank_apply_rejects,
        full_rank_candidate_rejects,
        full_rank_residual_rejects,
        full_rank_survivors,
    );
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    crate::scale_audit::gen_infer_linear_prefilter_result(
        prefilter_attempts, prefilter_solved, prefilter_no_fit, prefilter_fallback,
        prefilter_input_relations, prefilter_identity_comparisons, prefilter_arithmetic_checks,
        &prefilter_no_fit_reasons, &prefilter_fallback_reasons,
    );
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    crate::scale_audit::gen_infer_row_factorized_result(
        rowf_attempts, rowf_solved, rowf_no_candidate, rowf_fallback, rowf_row_evaluations,
        &rowf_no_candidate_reasons, &rowf_fallback_reasons,
    );
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    crate::scale_audit::gen_infer_correspondence_result(
        corr_attempts, corr_found, corr_no_candidate, corr_fallback, corr_hypotheses, corr_validations,
        &corr_no_candidate_reasons, &corr_fallback_reasons,
    );
    #[cfg(feature = "geninfer_quadratic_map_solver")]
    crate::scale_audit::gen_infer_quadratic_result(
        quadratic_enabled, quadratic_attempts, &quadratic_refusals,
        quadratic_validation_rejects, quadratic_survivors,
    );
    finish(result, field, ctx.interner, None)
}

#[cfg(feature = "geninfer_linear_exact_prefilter")]
enum ExactLinearPrefilter { Solved(Vec<i64>), ProvenNoFit(&'static str), Fallback(&'static str) }

/// Prove the unique 2-D integer matrix from a complete, unique typed
/// predicate+id join and two independent source displacements.
#[cfg(feature = "geninfer_linear_exact_prefilter")]
fn infer_exact_2d_linear_prefilter(source: &[Value], target: &[Value], dim_types: &[String], dims: &[i64], bound: i64) -> ExactLinearPrefilter {
    macro_rules! checked { ($operation:expr) => {{ if crate::scale_audit::enabled() { PREFILTER_EXACT_ARITHMETIC_CHECKS.with(|n| n.set(n.get().saturating_add(1))); } $operation }} }
    if dims.len() != 2 { return ExactLinearPrefilter::Fallback("unsupported_dimensions"); }
    // `apply_linear_once` preserves relation count and `build_candidate`
    // rejects unequal counts before inspecting any relation. This is an
    // unconditional proof that every enumerated matrix would be rejected.
    if source.len() != target.len() { return ExactLinearPrefilter::ProvenNoFit("relation_count_mismatch"); }
    if source.len() < 3 { return ExactLinearPrefilter::Fallback("rank_deficient"); }
    let ids: Vec<usize> = dim_types.iter().enumerate().filter_map(|(i,t)| (t == "id").then_some(i)).collect();
    if ids.is_empty() { return ExactLinearPrefilter::Fallback("missing_identity"); }
    // v1.4 soundness guards (residual-family divergence census, 2026-10-06).
    // The historical enumerator aligns relations by canonical tuple sort and
    // accepts generator-plus-residual decompositions, including per-predicate
    // (tier-2) coordinate shifts. The identity-joined affine proof below
    // coincides with that semantics only when (a) the canonical sort order is
    // fixed by the identity key, i.e. every slot before the first coordinate
    // is `id` and no `id` slot follows a coordinate, and (b) there is exactly
    // one predicate value, so tier-2 per-predicate shifts reduce to the single
    // global shift the affine proof already allows. Anything else is handed
    // back to the enumerator unchanged.
    let first_coord = dims.iter().copied().min().unwrap_or(0).max(0) as usize;
    if first_coord <= 1 || ids.iter().any(|&i| i > first_coord) || (1..first_coord).any(|i| dim_types.get(i).map(String::as_str) != Some("id")) {
        return ExactLinearPrefilter::Fallback("identity_not_sort_prefix");
    }
    {
        let pred_of = |r: &Value| relation_values(r).and_then(|row| row.first().cloned());
        let Some(p0) = source.first().and_then(pred_of) else { return ExactLinearPrefilter::Fallback("malformed_relation") };
        for r in source.iter().chain(target.iter()) {
            match pred_of(r) {
                Some(p) if p == p0 => {}
                Some(_) => return ExactLinearPrefilter::Fallback("multiple_predicates"),
                None => return ExactLinearPrefilter::Fallback("malformed_relation"),
            }
        }
    }
    let mut slots = vec![0usize]; slots.extend(ids);
    let mut target_by_key: FxHashMap<PrefilterIdentityKey, usize> = FxHashMap::default();
    for (i, t) in target.iter().enumerate() {
        let Some(row) = relation_values(t) else { return ExactLinearPrefilter::Fallback("malformed_relation") };
        if row.len() != dim_types.len() { return ExactLinearPrefilter::Fallback("malformed_relation_width"); }
        let Some(key) = slots.iter().map(|&k| row.get(k).cloned()).collect::<Option<Vec<_>>>() else { return ExactLinearPrefilter::Fallback("missing_identity_slot") };
        if target_by_key.insert(PrefilterIdentityKey(key), i).is_some() { return ExactLinearPrefilter::Fallback("ambiguous_identity"); }
    }
    let mut aligned = Vec::with_capacity(source.len());
    let mut used = vec![false; target.len()];
    for s in source {
        let Some(sr) = relation_values(s) else { return ExactLinearPrefilter::Fallback("malformed_relation") };
        if sr.len() != dim_types.len() { return ExactLinearPrefilter::Fallback("malformed_relation_width"); }
        let Some(key) = slots.iter().map(|&k| sr.get(k).cloned()).collect::<Option<Vec<_>>>() else { return ExactLinearPrefilter::Fallback("missing_identity_slot") };
        let Some(&matches) = target_by_key.get(&PrefilterIdentityKey(key)) else { return ExactLinearPrefilter::Fallback("missing_identity_match") };
        if used[matches] { return ExactLinearPrefilter::Fallback("ambiguous_identity"); }
        let tr = relation_values(&target[matches]).unwrap();
        let source_key = slots.iter().filter_map(|&k| sr.get(k).cloned()).collect::<Vec<_>>();
        let target_key = slots.iter().filter_map(|&k| tr.get(k).cloned()).collect::<Vec<_>>();
        if PrefilterIdentityKey(source_key) != PrefilterIdentityKey(target_key) { return ExactLinearPrefilter::Fallback("identity_confirmation_mismatch"); }
        used[matches] = true;
        let exact_int = |v: Option<&Value>| match v { Some(Value::Int(n)) => Some(*n), _ => None };
        let (Some(x0), Some(x1), Some(y0), Some(y1)) = (
            exact_int(sr.get(dims[0] as usize)), exact_int(sr.get(dims[1] as usize)),
            exact_int(tr.get(dims[0] as usize)), exact_int(tr.get(dims[1] as usize))) else { return ExactLinearPrefilter::Fallback("unsupported_coordinates") };
        aligned.push(([x0 as i128,x1 as i128],[y0 as i128,y1 as i128]));
    }
    if used.iter().any(|v| !v) { return ExactLinearPrefilter::Fallback("incomplete_identity_join"); }
    let (origin_x, origin_y) = aligned[0];
    let Some(a) = (1..aligned.len()).find(|&i| aligned[i].0 != origin_x) else { return ExactLinearPrefilter::Fallback("rank_deficient"); };
    let u = [aligned[a].0[0]-origin_x[0], aligned[a].0[1]-origin_x[1]];
    let mut basis = None;
    for bidx in a+1..aligned.len() {
        let v = [aligned[bidx].0[0]-origin_x[0], aligned[bidx].0[1]-origin_x[1]];
        let Some(det) = checked!(u[0].checked_mul(v[1])).and_then(|x| checked!(u[1].checked_mul(v[0])).and_then(|y| checked!(x.checked_sub(y)))) else { return ExactLinearPrefilter::Fallback("arithmetic_overflow"); };
        if det != 0 { basis = Some((bidx, v, det)); break; }
    }
    let Some((bidx, v, det)) = basis else { return ExactLinearPrefilter::Fallback("rank_deficient"); };
    let du = [aligned[a].1[0]-origin_y[0], aligned[a].1[1]-origin_y[1]];
    let dv = [aligned[bidx].1[0]-origin_y[0], aligned[bidx].1[1]-origin_y[1]];
    let mut m = Vec::with_capacity(4);
    for row in 0..2 {
        let Some(n0) = checked!(du[row].checked_mul(v[1])).and_then(|x| checked!(u[1].checked_mul(dv[row])).and_then(|y| checked!(x.checked_sub(y)))) else { return ExactLinearPrefilter::Fallback("arithmetic_overflow"); };
        let Some(n1) = checked!(u[0].checked_mul(dv[row])).and_then(|x| checked!(du[row].checked_mul(v[0])).and_then(|y| checked!(x.checked_sub(y)))) else { return ExactLinearPrefilter::Fallback("arithmetic_overflow"); };
        let (Some(r0),Some(r1)) = (checked!(n0.checked_rem(det)),checked!(n1.checked_rem(det))) else { return ExactLinearPrefilter::Fallback("arithmetic_overflow"); };
        if r0 != 0 || r1 != 0 { return ExactLinearPrefilter::ProvenNoFit("nonintegral_coefficients"); }
        let (Some(c0),Some(c1)) = (checked!(n0.checked_div(det)),checked!(n1.checked_div(det))) else { return ExactLinearPrefilter::Fallback("arithmetic_overflow"); };
        if c0 < -(bound as i128) || c0 > bound as i128 || c1 < -(bound as i128) || c1 > bound as i128 { return ExactLinearPrefilter::ProvenNoFit("coefficient_out_of_bound"); }
        let (Ok(c0),Ok(c1)) = (checked!(i64::try_from(c0)),checked!(i64::try_from(c1))) else { return ExactLinearPrefilter::Fallback("coefficient_conversion_overflow"); };
        m.extend([c0,c1]);
    }
    for (x,y) in &aligned {
        for row in 0..2 {
            let Some(pred) = checked!((m[row*2] as i128).checked_mul(x[0])).and_then(|a| checked!((m[row*2+1] as i128).checked_mul(x[1])).and_then(|b| checked!(a.checked_add(b)))) else { return ExactLinearPrefilter::Fallback("arithmetic_overflow"); };
            let Some(got) = checked!((m[row*2] as i128).checked_mul(origin_x[0])).and_then(|a| checked!((m[row*2+1] as i128).checked_mul(origin_x[1])).and_then(|b| checked!(a.checked_add(b)))).and_then(|a| checked!((y[row]-origin_y[row]).checked_add(a))) else { return ExactLinearPrefilter::Fallback("arithmetic_overflow"); };
            if pred != got { return ExactLinearPrefilter::ProvenNoFit("row_residual"); }
        }
    }
    ExactLinearPrefilter::Solved(m)
}

#[cfg(feature = "geninfer_linear_exact_prefilter")]
enum RowFactorizedSearch { Solved(Vec<i64>, usize), NoCandidate(&'static str), Fallback(&'static str) }

/// v1.4 row-factorized exact search: the historical enumerator's selection,
/// computed in O(n·(2b+1)^2) per output row instead of O(n·(2b+1)^4).
///
/// Soundness argument (checked against the enumerator by
/// `exact_linear_prefilter_row_factorized_matches_enumerator_*` tests):
/// when every source row has the same container kind and length and the
/// prefix of slots before the first coordinate is unique under `cmp_value`,
/// the canonical sort `build_candidate` applies to a transformed base is the
/// same permutation for every matrix (transforms only rewrite coordinate
/// slots). Alignment is therefore fixed. `build_candidate` then accepts iff
/// (a) the M-independent structural check passes, (b) every slot is
/// consistent, and (c) the total transform count is within `max_dims`; the
/// per-slot decision and transform count for coordinate slot `r` depend only
/// on matrix row `r`. The Occam key `(transform count, L1, matrix)` is a sum
/// over rows plus a lexicographic order, so keeping, per row and per
/// `(count, L1)` class, the two lexicographically smallest rows is enough to
/// recover the enumerator's unique winner (two, to skip the excluded
/// identity). Unsupported inputs fall back to the enumerator unchanged.
#[cfg(feature = "geninfer_linear_exact_prefilter")]
fn infer_row_factorized_2d_linear(source: &[Value], sorted_o: &[Value], dims: &[i64], bound: i64,
    max_dims: usize, extra_rev: &FxHashMap<Sym, String>, row_evaluations: &mut u64) -> RowFactorizedSearch {
    use std::cmp::Ordering;
    if dims.len() != 2 || bound <= 0 { return RowFactorizedSearch::Fallback("unsupported_dimensions"); }
    if source.len() != sorted_o.len() || source.is_empty() { return RowFactorizedSearch::Fallback("relation_count"); }
    let (Ok(d0), Ok(d1)) = (usize::try_from(dims[0]), usize::try_from(dims[1])) else { return RowFactorizedSearch::Fallback("unsupported_dimensions") };
    let first_coord = d0.min(d1);
    if first_coord == 0 || d0 == d1 { return RowFactorizedSearch::Fallback("identity_not_sort_prefix"); }
    let rows_of = |v: &Value| match v { Value::Tuple(t) => Some((false, t.clone())), Value::List(t) => Some((true, t.clone())), _ => None };
    let Some((kind0, first)) = rows_of(&source[0]) else { return RowFactorizedSearch::Fallback("malformed_relation") };
    let width = first.len();
    if width <= d0.max(d1) { return RowFactorizedSearch::Fallback("malformed_relation_width"); }
    let mut src = Vec::with_capacity(source.len());
    for r in source {
        let Some((kind, t)) = rows_of(r) else { return RowFactorizedSearch::Fallback("malformed_relation") };
        if kind != kind0 || t.len() != width { return RowFactorizedSearch::Fallback("malformed_relation_width"); }
        let (Some(Value::Int(_)), Some(Value::Int(_))) = (t.get(d0), t.get(d1)) else { return RowFactorizedSearch::Fallback("unsupported_coordinates") };
        src.push(r.clone());
    }
    // Fixed alignment: sort the base once; with a unique prefix this is the
    // permutation every transformed base sorts to.
    src.sort_by(cmp_value);
    let prefix_cmp = |a: &Value, b: &Value| -> Ordering {
        let (Some((_, x)), Some((_, y))) = (rows_of(a), rows_of(b)) else { return Ordering::Equal };
        for k in 0..first_coord { let c = cmp_value(&x[k], &y[k]); if c != Ordering::Equal { return c; } }
        Ordering::Equal
    };
    if src.windows(2).any(|w| prefix_cmp(&w[0], &w[1]) == Ordering::Equal) {
        return RowFactorizedSearch::Fallback("non_unique_source_prefix");
    }
    // M-independent structure (build_candidate's first pass).
    let mut tgt: Vec<SmallVec<[Value; 4]>> = Vec::with_capacity(sorted_o.len());
    for (h, o) in src.iter().zip(sorted_o.iter()) {
        let (Some((_, ht)), Some((_, ot))) = (rows_of(h), rows_of(o)) else { return RowFactorizedSearch::NoCandidate("structural_mismatch") };
        if ht.is_empty() || ht.len() != ot.len() || ht[0] != ot[0] { return RowFactorizedSearch::NoCandidate("structural_mismatch"); }
        tgt.push(ot.iter().cloned().collect());
    }
    for ot in &tgt {
        for &d in &[d0, d1] {
            if !matches!(ot[d], Value::Int(_) | Value::Float(_)) { return RowFactorizedSearch::Fallback("symbolic_coordinate_target"); }
        }
    }
    // Non-coordinate slots: copy the aligned target coordinates into the base
    // so only M-independent slots can differ; prefixes are untouched so the
    // copy sorts identically.
    let pinned: Vec<Value> = src.iter().zip(tgt.iter()).map(|(h, ot)| {
        let (kind, ht) = rows_of(h).expect("checked");
        let mut v: SmallVec<[Value; 4]> = ht.iter().cloned().collect();
        v[d0] = ot[d0].clone(); v[d1] = ot[d1].clone();
        if kind { Value::List(Arc::new(v)) } else { Value::Tuple(Arc::new(v)) }
    }).collect();
    let Some(other) = build_candidate(String::new(), Value::None, &pinned, sorted_o, usize::MAX, extra_rev, false) else {
        return RowFactorizedSearch::NoCandidate("structural_mismatch");
    };
    if other.transforms.len() != other.dims_needed.len() { return RowFactorizedSearch::NoCandidate("non_coordinate_inconsistent"); }
    let t_other = other.transforms.len();
    if t_other > max_dims { return RowFactorizedSearch::NoCandidate("non_coordinate_budget"); }
    // Normalized base coordinates (apply_linear_once: v - per-axis min).
    let col = |d: usize| -> Vec<i64> { src.iter().map(|r| match rows_of(r).expect("checked").1[d] { Value::Int(i) => i, _ => 0 }).collect() };
    let (c0, c1) = (col(d0), col(d1));
    let (m0, m1) = (*c0.iter().min().unwrap(), *c1.iter().min().unwrap());
    let v0: Vec<i64> = c0.iter().map(|x| x - m0).collect();
    let v1: Vec<i64> = c1.iter().map(|x| x - m1).collect();
    let as_f64 = |v: &Value| match v { Value::Int(i) => *i as f64, Value::Float(f) => *f, _ => 0.0 };
    // Per row: (count, l1) -> two lexicographically smallest (a, c).
    let mut classes: [std::collections::BTreeMap<(usize, i64), SmallVec<[(i64, i64); 2]>>; 2] = Default::default();
    for (row, &slot) in [d0, d1].iter().enumerate() {
        let obs: Vec<&Value> = tgt.iter().map(|ot| &ot[slot]).collect();
        let preds: Vec<&Value> = tgt.iter().map(|ot| &ot[0]).collect();
        for a in -bound..=bound {
            for c in -bound..=bound {
                *row_evaluations = row_evaluations.saturating_add(1);
                let h: Vec<i64> = v0.iter().zip(&v1).map(|(x, y)| a.wrapping_mul(*x).wrapping_add(c.wrapping_mul(*y))).collect();
                let differs = h.iter().zip(&obs).any(|(hv, o)| Value::Int(*hv) != **o);
                let count = if !differs { Some(0usize) } else {
                    let deltas: Vec<f64> = h.iter().zip(&obs).map(|(hv, o)| as_f64(o) - *hv as f64).collect();
                    if deltas.iter().all(|d| (d - deltas[0]).abs() < 1e-9) { Some(1) } else {
                        // tier 2: per-predicate uniform groups; nonzero groups count.
                        let mut groups: Vec<(&Value, f64)> = Vec::new();
                        let mut ok = true;
                        for (p, d) in preds.iter().zip(&deltas) {
                            match groups.iter().find(|(q, _)| *q == *p) {
                                Some((_, g)) => if (d - g).abs() >= 1e-9 { ok = false; break; },
                                None => groups.push((*p, *d)),
                            }
                        }
                        ok.then(|| groups.iter().filter(|(_, g)| g.abs() >= 1e-9).count())
                    }
                };
                let Some(count) = count else { continue };
                if t_other + count > max_dims { continue; }
                let entry = classes[row].entry((count, a.abs() + c.abs())).or_default();
                if entry.len() < 2 { entry.push((a, c)); } // (a, c) visited in ascending lexicographic order
            }
        }
    }
    let mut best: Option<((usize, i64, [i64; 4]), Vec<i64>)> = None;
    for (&(t0, l0), r0s) in &classes[0] {
        for (&(t1, l1), r1s) in &classes[1] {
            let total = t_other + t0 + t1;
            if total > max_dims { continue; }
            for &(a0, b0) in r0s {
                let pick = r1s.iter().find(|&&(a1, b1)| [a0, b0, a1, b1] != [1, 0, 0, 1]);
                if let Some(&(a1, b1)) = pick {
                    let key = (total, l0 + l1, [a0, b0, a1, b1]);
                    if best.as_ref().is_none_or(|(k, _)| key < *k) { best = Some((key, vec![a0, b0, a1, b1])); }
                    break; // later r0 entries in this class are lexicographically larger
                }
            }
        }
    }
    match best { Some(((t, _, _), m)) => RowFactorizedSearch::Solved(m, t), None => RowFactorizedSearch::NoCandidate("no_consistent_row_pair") }
}

/// v1.4 correspondence-complete candidate generation for frames whose sort
/// alignment depends on the matrix (no unique identity prefix).
///
/// Completeness lemma: if the historical enumerator accepts `M`, every
/// aligned pair shares its predicate (structural check) and, within one
/// predicate block, every coordinate slot has one uniform delta (tier 1 or a
/// tier-2 group). Hence for any three source rows `a,b,c` of one block there
/// are target rows `i,j,k` of that block with `M(b-a) = y_j - y_i` and
/// `M(c-a) = y_k - y_i`; when `b-a`, `c-a` are independent this determines
/// `M`. Enumerating the `n_p^3` target triples of the smallest full-rank
/// block therefore yields a superset of every accepted matrix. Each distinct
/// in-bound integral hypothesis is then judged by the enumerator's own
/// validator (`apply_linear_once` + `build_candidate`) and ranked by the same
/// Occam key, so the selected winner is the enumerator's.
#[cfg(feature = "geninfer_linear_exact_prefilter")]
enum CorrespondenceSearch { Found(Vec<i64>, Candidate), NoCandidate(&'static str), Fallback(&'static str) }

#[cfg(feature = "geninfer_linear_exact_prefilter")]
#[allow(clippy::too_many_arguments)]
fn infer_correspondence_2d_linear(part_name: &str, part_val: &Value, source: &[Value], sorted_o: &[Value], dims: &[i64], bound: i64,
    max_dims: usize, extra_rev: &FxHashMap<Sym, String>, hypotheses: &mut u64, validations: &mut u64) -> CorrespondenceSearch {
    if dims.len() != 2 || bound <= 0 { return CorrespondenceSearch::Fallback("unsupported_dimensions"); }
    let (Ok(d0), Ok(d1)) = (usize::try_from(dims[0]), usize::try_from(dims[1])) else { return CorrespondenceSearch::Fallback("unsupported_dimensions") };
    let int_xy = |r: &Value| -> Option<(Value, i64, i64)> {
        let (Value::Tuple(t) | Value::List(t)) = r else { return None };
        match (t.first(), t.get(d0), t.get(d1)) { (Some(p), Some(Value::Int(x)), Some(Value::Int(y))) => Some((p.clone(), *x, *y)), _ => None }
    };
    let mut src = Vec::with_capacity(source.len());
    for r in source { let Some(v) = int_xy(r) else { return CorrespondenceSearch::Fallback("unsupported_coordinates") }; src.push(v); }
    let mut tgt = Vec::with_capacity(sorted_o.len());
    for r in sorted_o { let Some(v) = int_xy(r) else { return CorrespondenceSearch::Fallback("non_integer_target_coordinates") }; tgt.push(v); }
    // Pick the smallest predicate block (by target size) that has a full-rank source triple.
    let mut preds: Vec<Value> = Vec::new();
    for (p, _, _) in &src { if !preds.contains(p) { preds.push(p.clone()); } }
    let mut choice: Option<(usize, [(i64, i64); 3], Vec<(i64, i64)>)> = None;
    for p in &preds {
        let block: Vec<(i64, i64)> = src.iter().filter(|(q, _, _)| q == p).map(|(_, x, y)| (*x, *y)).collect();
        let targets: Vec<(i64, i64)> = tgt.iter().filter(|(q, _, _)| q == p).map(|(_, x, y)| (*x, *y)).collect();
        if targets.len() != block.len() { return CorrespondenceSearch::NoCandidate("predicate_block_count_mismatch"); }
        let a = block[0];
        let Some(&b) = block.iter().find(|q| **q != a) else { continue };
        let u = (b.0 - a.0, b.1 - a.1);
        let Some(&c) = block.iter().find(|q| { let v = (q.0 - a.0, q.1 - a.1); u.0 * v.1 - u.1 * v.0 != 0 }) else { continue };
        if choice.as_ref().is_none_or(|(n, _, _)| targets.len() < *n) { choice = Some((targets.len(), [a, b, c], targets)); }
    }
    let Some((_, [a, b, c], targets)) = choice else { return CorrespondenceSearch::Fallback("no_full_rank_predicate_block") };
    let (u, v) = ((b.0 - a.0) as i128, (b.1 - a.1) as i128);
    let (w0, w1) = ((c.0 - a.0) as i128, (c.1 - a.1) as i128);
    let det = u * w1 - v * w0; // [u w] columns: u = (u, v), w = (w0, w1)
    let bnd = bound as i128;
    let mut seen: rustc_hash::FxHashSet<[i64; 4]> = rustc_hash::FxHashSet::default();
    let mut best: Option<((usize, i64, [i64; 4]), Candidate)> = None;
    for yi in &targets {
        for yj in &targets {
            let e = ((yj.0 - yi.0) as i128, (yj.1 - yi.1) as i128);
            for yk in &targets {
                *hypotheses = hypotheses.saturating_add(1);
                let f = ((yk.0 - yi.0) as i128, (yk.1 - yi.1) as i128);
                // Row r: [m_r0 m_r1]·[u w] = [e_r f_r]  =>  m_r0 = (e_r w1 - f_r v)/det, m_r1 = (f_r u - e_r w0)/det
                let mut m = [0i64; 4];
                let mut ok = true;
                for (row, (er, fr)) in [(e.0, f.0), (e.1, f.1)].into_iter().enumerate() {
                    let n0 = er * w1 - fr * v;
                    let n1 = fr * u - er * w0;
                    if n0 % det != 0 || n1 % det != 0 { ok = false; break; }
                    let (c0, c1) = (n0 / det, n1 / det);
                    if c0.abs() > bnd || c1.abs() > bnd { ok = false; break; }
                    m[row * 2] = c0 as i64; m[row * 2 + 1] = c1 as i64;
                }
                if !ok || m == [1, 0, 0, 1] || !seen.insert(m) { continue; }
                *validations = validations.saturating_add(1);
                let Some(transformed) = apply_linear_once(source, dims, &m) else { continue };
                let Some(cand) = build_candidate(part_name.to_string(), part_val.clone(), &transformed, sorted_o, max_dims, extra_rev,
                    cfg!(feature = "geninfer_fused_candidate_validation")) else { continue };
                if cand.transforms.len() != cand.dims_needed.len() { continue; }
                let key = (cand.dims_needed.len(), m.iter().map(|x| x.abs()).sum::<i64>(), m);
                if best.as_ref().is_none_or(|(k, _)| key < *k) { best = Some((key, cand)); }
            }
        }
    }
    match best { Some(((_, _, m), cand)) => CorrespondenceSearch::Found(m.to_vec(), cand), None => CorrespondenceSearch::NoCandidate("no_validated_correspondence") }
}

/// A re-quantized signature is DEGENERATE at a coarse grain when it no longer
/// carries orientation: fewer than 3 relations, or it fills its own 2-D
/// bounding box (a solid block is fixed by every D4 map and matches any block
/// of the same size). Tranche 4: tiny novel shapes and scrambled support
/// collapse to such blocks, which made the grain ladder recognise them.
fn coarse_degenerate(sig: &[Value], slots: &[usize]) -> bool {
    if sig.len() < 3 {
        return true;
    }
    if slots.len() != 2 {
        return false;
    }
    let (Some(a), Some(b)) = (coord_ints(sig, slots[0]), coord_ints(sig, slots[1])) else { return false };
    let span = |v: &[i64]| v.iter().max().unwrap_or(&0) - v.iter().min().unwrap_or(&0) + 1;
    let cells: rustc_hash::FxHashSet<(i64, i64)> = a.iter().copied().zip(b.iter().copied()).collect();
    (cells.len() as i64) >= span(&a) * span(&b)
}

/// Re-quantize the given coordinate slots of every relation to grain `g`:
/// `floor((v - min) / 2^g)` per slot (WP3). Non-Int slots are left as-is.
/// Relations that become identical at the coarser grain collapse to one
/// (the quotient: at that grain they are literally the same relation).
fn requantize(sig: &[Value], slots: &[usize], g: i64) -> Vec<Value> {
    let step = 1i64 << g.clamp(0, 30);
    let mut out = sig.to_vec();
    for &idx in slots {
        let Some(vs) = coord_ints(sig, idx) else { continue };
        let Some(&mn) = vs.iter().min() else { continue };
        for (rel, v) in out.iter_mut().zip(vs) {
            *rel = set_coord(rel, idx, (v - mn).div_euclid(step));
        }
    }
    if g > 0 {
        out.sort_by(cmp_value);
        out.dedup_by(|a, b| cmp_value(a, b) == std::cmp::Ordering::Equal);
    }
    out
}

/// MDL witness for a 2-D integer linear map (WP3, feature `geninfer_grain_mdl`).
///
/// Exact arithmetic; the approximation is in WHICH ROWS the map explains, not
/// in any coordinate tolerance. Hypotheses come from correspondences of up to
/// four disjoint anchor triples of the base (so a single outlier cannot hide
/// the map from every anchor). For each in-bound integral hypothesis M and
/// translation t fixed by its correspondence, a relation is explained iff
/// `M·(x − min) + t` reproduces a goal relation EXACTLY (multiset match on the
/// whole tuple). Description length: matrix bits (sum of per-entry
/// `bits(|m|)+1`) + translation bits + `row_bits` per unexplained goal row.
/// Accepted iff unexplained rows < half the goal and the total beats the raw
/// cost `n·row_bits` (describing the goal without the map). Returns
/// (matrix, unexplained goal rows, bits, raw_bits).
#[cfg(feature = "geninfer_grain_mdl")]
fn infer_mdl_2d_linear(source: &[Value], target: &[Value], dims: &[i64], bound: i64) -> Option<(Vec<i64>, Vec<Value>, i64, i64)> {
    if dims.len() != 2 || source.len() < 3 || source.len() != target.len() { return None; }
    let (d0, d1) = (usize::try_from(dims[0]).ok()?, usize::try_from(dims[1]).ok()?);
    let xs0 = coord_ints(source, d0)?; let xs1 = coord_ints(source, d1)?;
    let ys0 = coord_ints(target, d0)?; let ys1 = coord_ints(target, d1)?;
    let (m0, m1) = (*xs0.iter().min()?, *xs1.iter().min()?);
    let src: Vec<(i64, i64)> = xs0.iter().zip(&xs1).map(|(a, b)| (a - m0, b - m1)).collect();
    let tgt: Vec<(i64, i64)> = ys0.iter().zip(&ys1).map(|(a, b)| (*a, *b)).collect();
    let n = target.len();
    let span = |v: &[i64]| v.iter().max().unwrap_or(&0) - v.iter().min().unwrap_or(&0);
    let bits = |x: i64| 64 - (x.unsigned_abs()).leading_zeros() as i64;
    let row_bits = bits(span(&ys0)) + bits(span(&ys1)) + 2;
    let raw = n as i64 * row_bits;
    // goal multiset keyed by full tuple
    // Keyed by element vector so Tuple/List containers compare equal, as
    // `build_candidate`'s element-wise comparison does.
    let key_of = |r: &Value| -> Option<Vec<Value>> { relation_values(r).map(|x| x.to_vec()) };
    let mut goal_count: FxHashMap<Vec<Value>, (i64, Value)> = FxHashMap::default();
    for t in target { goal_count.entry(key_of(t)?).or_insert((0, t.clone())).0 += 1; }
    // anchor triples: greedy disjoint full-rank triples
    let mut anchors: Vec<[usize; 3]> = Vec::new();
    let mut used = vec![false; src.len()];
    'outer: while anchors.len() < 4 {
        let free: Vec<usize> = (0..src.len()).filter(|&i| !used[i]).collect();
        for &a in &free { for &b in &free { if b <= a { continue; } for &c in &free { if c <= b { continue; }
            let (u, v) = ((src[b].0 - src[a].0, src[b].1 - src[a].1), (src[c].0 - src[a].0, src[c].1 - src[a].1));
            if u.0 * v.1 - u.1 * v.0 != 0 { anchors.push([a, b, c]); used[a] = true; used[b] = true; used[c] = true; continue 'outer; }
        }}}
        break;
    }
    let mut best: Option<(i64, Vec<i64>, Vec<Value>)> = None;
    let mut seen: rustc_hash::FxHashSet<([i64; 4], (i64, i64))> = rustc_hash::FxHashSet::default();
    for [a, b, c] in anchors {
        let (u, v) = ((src[b].0 - src[a].0, src[b].1 - src[a].1), (src[c].0 - src[a].0, src[c].1 - src[a].1));
        let det = u.0 * v.1 - u.1 * v.0;
        for ya in &tgt { for yb in &tgt { for yc in &tgt {
            let e = (yb.0 - ya.0, yb.1 - ya.1); let f = (yc.0 - ya.0, yc.1 - ya.1);
            let mut m = [0i64; 4]; let mut ok = true;
            for (row, (er, fr)) in [(e.0, f.0), (e.1, f.1)].into_iter().enumerate() {
                let n0 = er * v.1 - fr * u.1; let n1 = fr * u.0 - er * v.0;
                if n0 % det != 0 || n1 % det != 0 { ok = false; break; }
                let (c0, c1) = (n0 / det, n1 / det);
                if c0.abs() > bound || c1.abs() > bound { ok = false; break; }
                m[row * 2] = c0; m[row * 2 + 1] = c1;
            }
            if !ok || m == [1, 0, 0, 1] || m == [0, 0, 0, 0] { continue; }
            let t = (ya.0 - (m[0] * src[a].0 + m[1] * src[a].1), ya.1 - (m[2] * src[a].0 + m[3] * src[a].1));
            if !seen.insert((m, t)) { continue; }
            let mut remaining = goal_count.clone();
            let mut matched = 0usize;
            for (i, rel) in source.iter().enumerate() {
                let (x, y) = src[i];
                let img = set_coord(&set_coord(rel, d0, m[0] * x + m[1] * y + t.0), d1, m[2] * x + m[3] * y + t.1);
                if let Some((cnt, _)) = key_of(&img).and_then(|k| remaining.get_mut(&k)) { if *cnt > 0 { *cnt -= 1; matched += 1; } }
            }
            let outliers = n - matched;
            if 2 * outliers >= n { continue; }
            let mbits: i64 = m.iter().map(|x| bits(*x) + 1).sum::<i64>() + bits(t.0) + bits(t.1) + 2;
            let total = mbits + outliers as i64 * row_bits;
            if total >= raw { continue; }
            if best.as_ref().is_none_or(|(bt, bm, _)| (total, m.to_vec()) < (*bt, bm.clone())) {
                let mut out_rows = Vec::new();
                for (_, (cnt, rel)) in remaining { for _ in 0..cnt { out_rows.push(rel.clone()); } }
                out_rows.sort_by(cmp_value);
                best = Some((total, m.to_vec(), out_rows));
            }
        }}}
    }
    best.map(|(bits_total, m, out)| (m, out, bits_total, raw))
}

/// Greatest common divisor of two non-negative integers (Euclid). `gcd(0,0)
/// == 0`. Used ONLY to reduce an induced coordinate-extent ratio to lowest
/// terms — the ratio is a RELATION (a reduced integer pair), never a stored
/// coordinate, so the frame/continuum invariant is untouched.
fn gcd_i64(mut a: i64, mut b: i64) -> i64 {
    a = a.abs();
    b = b.abs();
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    a
}

/// `eval_ratio_infer` — POPULATION RATIO-INVARIANCE INDUCTION, the cross-frame
/// population-level sibling of `GenInfer`. Where `GenInfer` induces ONE integer
/// generator from ONE orbit (base + transformed goal), this induces, from a
/// POPULATION of frames related by a PER-FRAME multiplicative rescaling, the
/// INVARIANT RATIO SET: the cross-coordinate ratios that stay fixed as each
/// frame's own scale varies.
///
/// THE SHAPE (why it FITS the frame/continuum invariant rather than fighting
/// it). A subject / speaker / writer / carrier frame differs from another by a
/// MULTIPLICATIVE factor `s_f` (impedance / gain / pitch / size). A RATIO
/// between two coordinate extents WITHIN one frame CANCELS that common `s_f`:
/// `(s_f·a) : (s_f·b) == a : b`. So the invariant is a RATIO — a RELATION held
/// in `Hom(frame, invariant-frame)`, applied on read, integer-observable
/// (a reduced integer pair `p:q`) — NOT a continuous coordinate stored
/// in-frame. In-frame stays integer (every extent is read through `coord_ints`,
/// which refuses `Float`); the ratio is the MAP, minted as a
/// `DimensionGenerator`/`LatentDimension` param, never written back into a
/// coordinate slot. This is the exact posture the substrate already privileges
/// for `scale2` ("a ratio cancels a common scale, coherent in any base").
///
/// THE METHOD (READ-then-VERIFY-across-all, the population analogue of
/// `infer_translate_offset`). For each frame, and each coord slot `j`, compute
/// the ORIGIN-NORMALIZED EXTENT `e_j(f) = max_j(f) - min_j(f)` (the same
/// data-derived magnitude `GenInfer`'s bound uses at 3044–3053). Slot 0 is the
/// REFERENCE axis. From the FIRST usable frame READ the reduced integer ratio
/// `r_j = reduce(e_j, e_0)` for every non-reference slot `j`; then VERIFY that
/// SAME reduced ratio holds in EVERY frame by cross-multiplication
/// (`e_j · r_j.den == e_0 · r_j.num`, all integer — no division, no float).
/// A frame whose extents are NOT a common-scale multiple of the reference
/// ratio set FALSIFIES the invariant (the MDL floor: the population is not
/// purely multiplicative, reported as `explained=false`, the honest null).
///
/// THE MINT. On success the ratio set is reported as `ratios` (a flat Tuple of
/// `[slot, num, den]` triples). When the whole set is a common power-of-two
/// (each `num`/`den` a power of 2) the seed rule mints a `scale2`-family
/// `latent:scale2` generator directly (`scale_pow2_once` already handles it);
/// otherwise the diagonal integer ratio mints a `kind:"linear"` diagonal
/// `matrix` that `apply_linear_once` already reads — so this rung needs ZERO
/// new dispatch arm in `apply_generator_once`, exactly like the linear inducer.
/// `latent_name` (`"latent:ratio"`) is the body the seed prefixes to mint the
/// `LatentDimension`.
///
/// Output Dict: `explained` / `coord_dims` / `ncoord` / `ref_dim` / `ratios`
/// (flat `[slot,num,den]` triples) / `is_pow2` (whole set power-of-two ⇒
/// scale2-family) / `matrix` (diagonal integer map minted when not pow2, else
/// empty) / `latent_name` / `n_frames` / `checked`; `field` selects one key
/// exactly like `GenInfer`/`DimInfer`. Integer lattice only (a `Float`
/// coordinate is CROSS-FRAME and makes the whole population inapplicable — the
/// invariant, inherited for free through `coord_ints`).
///
/// `resolution` is the OBSERVATION RESOLUTION tolerance (an integer, default 0
/// = EXACT). Per CLAUDE.md a continuous parameter (here the ratio) is pinned
/// ONLY to observational resolution — "never encode precision the steps cannot
/// support (MDL)". With `resolution == 0` the cross-frame ratio must hold by
/// EXACT integer cross-multiplication (the clean-mechanism case, H-R1). With
/// `resolution == q` (the grid step the frame's coordinates were quantized to)
/// the per-frame residual `|e_j·den − e_ref·num|` is allowed up to a
/// DATA-SCALED integer bound `q·den·(1 + e_ref/…)` — kept fully in `i128`
/// integer arithmetic, NO float — so a ratio recovered from a REAL, quantized
/// observation (H-R3 audio) is accepted iff it holds to within the resolution
/// the observation itself supports, and rejected otherwise (the honest floor
/// is preserved: a genuinely different ratio still exceeds the bound).
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_ratio_infer(
    arena: &TermArena,
    population_idx: TermIdx,
    codebook_type: Sym,
    resolution: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_RATIO_INDUCE);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);

    // Coord slots from the FIRST part that declares dim_types — all parts in a
    // codebook share the frame (identical to GenInfer/TimeInfer).
    let coord_dims: Vec<i64> = parts
        .iter()
        .find_map(|p| p.dim_types.as_ref())
        .map(|dts| {
            dts.iter()
                .enumerate()
                .filter(|(_, t)| t.starts_with("coord:"))
                .map(|(i, _)| i as i64)
                .collect()
        })
        .unwrap_or_default();

    // Read the POPULATION: an outer collection of frames, each an inner
    // collection of relation-tuples (the exact reader `eval_time_infer` uses).
    let pop_val = evaluate(arena, population_idx, env, ctx);
    let frames: Vec<Vec<Value>> = match &pop_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => pop_val
            .iter()
            .map(|f| match f {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
                    f.iter().cloned().collect()
                }
                _ => Vec::new(),
            })
            .collect(),
        _ => Vec::new(),
    };

    let coord_idxs: Vec<usize> = coord_dims
        .iter()
        .filter_map(|&d| usize::try_from(d).ok())
        .collect();

    let mut checked: i64 = 0;

    // A reduced integer ratio p:q (p == num, q == den), q > 0 by construction.
    #[derive(Clone, Copy)]
    struct Ratio {
        num: i64,
        den: i64,
    }

    let unexplained = |checked: i64, ctx: &mut EvalCtx| -> Value {
        finish(
            Value::Dict(Arc::from(vec![
                (surf("explained"), Value::Bool(false)),
                (surf("coord_dims"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("ncoord"), Value::Int(0)),
                (surf("ref_dim"), Value::None),
                (surf("ratios"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("is_pow2"), Value::Bool(false)),
                (surf("matrix"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("latent_name"), Value::None),
                (surf("n_frames"), Value::Int(0)),
                (surf("checked"), Value::Int(checked)),
            ])),
            field,
            ctx.interner,
            None,
        )
    };

    // Need at least TWO frames (a population), at least TWO coord slots (a
    // cross-coordinate ratio needs a reference + a target), and no empty frame.
    if frames.len() < 2 || coord_idxs.len() < 2 || frames.iter().any(|f| f.is_empty()) {
        return unexplained(0, ctx);
    }

    // Per-frame origin-normalized extent for a coord slot — the data-derived
    // magnitude (max - min), read through coord_ints so a Float coordinate
    // makes the frame (and thus the whole population) inapplicable. This is the
    // integer/frame invariant, inherited for free.
    let extent = |frame: &[Value], idx: usize| -> Option<i64> {
        let vs = coord_ints(frame, idx)?;
        let mn = *vs.iter().min()?;
        let mx = *vs.iter().max()?;
        Some(mx - mn)
    };

    // Extents per frame, per coord slot. Bail (null) on any Float coordinate.
    let mut ext: Vec<Vec<i64>> = Vec::with_capacity(frames.len());
    for f in &frames {
        let mut row = Vec::with_capacity(coord_idxs.len());
        for &idx in &coord_idxs {
            match extent(f, idx) {
                Some(e) => row.push(e),
                None => return unexplained(checked, ctx),
            }
        }
        ext.push(row);
    }

    // Choose the REFERENCE axis: the FIRST slot whose extent is non-zero in
    // EVERY frame (a degenerate zero-extent reference cannot carry a ratio).
    let ref_pos: Option<usize> = (0..coord_idxs.len()).find(|&j| ext.iter().all(|r| r[j] != 0));
    let Some(ref_pos) = ref_pos else {
        return unexplained(checked, ctx);
    };
    let ref_dim = coord_dims[ref_pos];

    // READ the reduced ratio r_j = e_j : e_ref for every non-reference slot,
    // then VERIFY it across ALL frames by cross-multiplication (integer only —
    // the ratio is a relation, applied not stored). Read the ratio from the
    // frame with the LARGEST reference extent (the best-resolved observation —
    // smallest RELATIVE quantization error), so the induced pair is the most
    // faithful reduction; then verify it across the whole population. A slot
    // whose ratio is not constant across the population (beyond the observation
    // resolution) FALSIFIES the invariant (the honest MDL floor: not purely
    // multiplicative).
    let best_frame = (0..ext.len()).max_by_key(|&i| ext[i][ref_pos]).unwrap_or(0);
    let fbest = &ext[best_frame];
    let mut ratios: Vec<(i64, Ratio)> = Vec::new(); // (slot dim, ratio)
    for j in 0..coord_idxs.len() {
        if j == ref_pos {
            continue;
        }
        let num0 = fbest[j];
        let den0 = fbest[ref_pos];
        let g = gcd_i64(num0, den0).max(1);
        let r = Ratio {
            num: num0 / g,
            den: den0 / g,
        };
        // VERIFY across every frame: e_j * r.den == e_ref * r.num (EXACT when
        // resolution == 0). With a non-zero observation resolution `q`, allow a
        // DATA-SCALED integer residual: each quantized extent carries up to ±q
        // of grid error, so the cross-product residual is bounded by
        // q·(num + den) — kept in i128, NO float. A genuinely different ratio
        // still blows past this bound (the honest floor survives), while a
        // ratio true to within the resolution the observation supports passes.
        let tol: i128 = (resolution.max(0) as i128) * (r.num as i128 + r.den as i128);
        for row in &ext {
            checked += 1;
            crate::access_trace::note_helper_work(51, 1);
            let residual = row[j] as i128 * r.den as i128 - row[ref_pos] as i128 * r.num as i128;
            if residual.abs() > tol {
                return unexplained(checked, ctx);
            }
        }
        ratios.push((coord_dims[j], r));
    }

    // POWER-OF-TWO test: is every ratio's num AND den a power of two? If so the
    // whole set is a scale2-family map (mint latent:scale2 directly). A value v
    // is a power of two iff v > 0 && (v & (v-1)) == 0.
    let is_pow2 = |v: i64| v > 0 && (v & (v - 1)) == 0;
    let all_pow2 =
        !ratios.is_empty() && ratios.iter().all(|(_, r)| is_pow2(r.num) && is_pow2(r.den));

    // Build the diagonal integer MATRIX minted when the set is NOT a clean
    // power-of-two (a kind:"linear" diagonal that apply_linear_once already
    // reads — ZERO new dispatch arm). The reference axis carries 1:1 (diagonal
    // entry 1); each ratio slot carries its num on the diagonal (integer map
    // v -> num * v; the denominator lives in the ratio relation, not the
    // matrix, since apply_linear_once is integer-only — the matrix expresses
    // the EXPANSION direction, the ratio pair is the full intensional relation).
    // n == coord_dims.len(); row-major.
    let n = coord_dims.len();
    let mut matrix: Vec<i64> = vec![0; n * n];
    for i in 0..n {
        matrix[i * n + i] = 1;
    }
    if !all_pow2 {
        for (slot, r) in &ratios {
            // position of this slot within coord_dims (guaranteed present — we
            // built `ratios` from coord_dims); its diagonal entry carries the
            // expansion numerator (integer map v -> num·v).
            if let Some(pos) = coord_dims.iter().position(|&d| d == *slot) {
                matrix[pos * n + pos] = r.num.max(1);
            }
        }
    }

    let ratios_out: SmallVec<[Value; 4]> = ratios
        .iter()
        .flat_map(|(slot, r)| [Value::Int(*slot), Value::Int(r.num), Value::Int(r.den)])
        .collect();
    let coord_dims_out: SmallVec<[Value; 4]> = coord_dims.iter().map(|d| Value::Int(*d)).collect();
    let matrix_out: SmallVec<[Value; 4]> = if all_pow2 {
        SmallVec::new()
    } else {
        matrix.iter().map(|m| Value::Int(*m)).collect()
    };
    let latent_name = if all_pow2 {
        "latent:scale2"
    } else {
        "latent:ratio"
    };

    let result = Value::Dict(Arc::from(vec![
        (surf("explained"), Value::Bool(true)),
        (surf("coord_dims"), Value::Tuple(Arc::new(coord_dims_out))),
        (surf("ncoord"), Value::Int(n as i64)),
        (surf("ref_dim"), Value::Int(ref_dim)),
        (surf("ratios"), Value::Tuple(Arc::new(ratios_out))),
        (surf("is_pow2"), Value::Bool(all_pow2)),
        (surf("matrix"), Value::Tuple(Arc::new(matrix_out))),
        (surf("latent_name"), surf(latent_name)),
        (surf("n_frames"), Value::Int(frames.len() as i64)),
        (surf("checked"), Value::Int(checked)),
    ]));
    finish(result, field, ctx.interner, None)
}

/// `LogQuantum` — the integer-observable LOG-QUANTUM EMITTER
/// (`drafts/log_quantum/LOG_QUANTUM_PREREG.md`). It is the substrate's own
/// `log_scaled_proprioception` lever (`seeds/log_graph_law.json`) made a
/// primitive: read a CONTINUOUS log-domain quantity `x` (log-odds, log-weight,
/// log-prior — or a raw linear value to be logged) and emit the INTEGER
/// log-coordinate `q = round(log_a(x) / Δ)` — the general form of what
/// `scale_pow2_once` does for the fixed base-2 spatial case (there the
/// additive `k` in log₂ IS the quantum; here the base `a` and step `Δ` are
/// arbitrary, held intensionally).
///
/// WHY IT FITS THE INVARIANT BY CONSTRUCTION (the H-L1 crux). The emitted `q`
/// is an `i64` written back through `set_coord` (kind-preserving), so it lands
/// in-frame as a `Value::Int` that `coord_ints` accepts — the frame stays on
/// the integer lattice. The base `a` and resolution `Δ` are NOT coordinates:
/// they ride as INTENSIONAL PARAMS on the Term (rationals `a = base_num/base_den`,
/// `Δ = delta_num/delta_den`), the exact posture `matrix`/`offset` use on a
/// `DimensionGenerator` — a relation held in `Hom(frame, invariant-frame)`,
/// APPLIED ON READ, never stored in a coordinate slot. The one place a float
/// exists is the transient cross-frame render `ln(x)/(ln(a)·Δ)` computed HERE,
/// in the map, and immediately rounded to an integer — precisely CLAUDE.md's
/// "continuity is intensional; the observable is the stepped integer rendering;
/// pinned only to observational resolution (MDL)". A `Δ` is the identifiability
/// guard: never encode precision the source cannot support.
///
/// WHY A DIFFERENCE IS A LOG-RATIO (the H-L2/H-L3 unlock). Two quanta of
/// quantities related by a multiplicative factor `f` differ by the CONSTANT
/// integer `round(log_a(f)/Δ)`: `q_i − q_j = round(log_a(x_i/x_j)/Δ)`. So a
/// population of frames differing by a per-frame multiplicative scale becomes,
/// after emission, a population of INTEGER-coordinate frames differing by a
/// per-frame ADDITIVE log-offset — exactly the shape `RatioInduce`/`scale2`
/// consume. The emitter's output feeds the ratio-induction ladder directly, no
/// new dispatch arm.
///
/// SHAPE. `population` evaluates to an outer collection of frames, each an
/// inner collection of `[pred, coord, …, val]` relation tuples (the same
/// Value-tuple shape `RatioInduce`/`GenInfer` consume). For every relation the
/// slot `value_slot` holds the continuous quantity `x` (read via `as_f64`, which
/// accepts `Int`/`Float`/`Rational` — the rational→float step there is itself
/// the named cross-frame boundary). Each such slot is REPLACED by its integer
/// log-quantum; every other slot is untouched. When `raw` is true, `x` is a raw
/// LINEAR value first mapped through the log (`log_a(x)`); when false, `x` is
/// ALREADY a log-domain quantity and the emitter only requantizes it onto the
/// integer log axis (`q = round(x/Δ)`) — the `frame.py` `_log_weights` case,
/// where `math.log` has already been applied. A non-positive `x` under `raw`
/// (log undefined) floors to `ln(1e-9)` exactly as `frame.py::_log_weights`
/// does, so the emitter matches the reasoning site it targets.
///
/// Output: the population with the `value_slot` column quantized to `Int`,
/// returned as a Tuple of Tuples (frames of relation tuples), ready to hand to
/// `RatioInduce`. `field` is accepted for wiring symmetry; when set it selects
/// from a small diagnostic Dict (`quantized` population + `n_frames`/`n_rels`/
/// `value_slot`) instead. Base `e` is selected by `base_num == 0` (a natural-log
/// sentinel); otherwise `a = base_num/base_den` with `base_num > 1`. A `Δ <= 0`,
/// an out-of-range `value_slot`, or a `base` that is not a valid log base makes
/// the op inapplicable and returns the population UNCHANGED (a graceful skip,
/// never a float written in-frame).
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_log_quantum(
    arena: &TermArena,
    population_idx: TermIdx,
    value_slot: i64,
    base_num: i64,
    base_den: i64,
    delta_num: i64,
    delta_den: i64,
    raw: bool,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let pop_val = evaluate(arena, population_idx, env, ctx);

    // Resolve the intensional base and Δ (in Hom, applied on read). base_num==0
    // is the natural-log sentinel (ln); otherwise a = base_num/base_den must be
    // a genuine log base ( > 1 as a real; base_den > 0 ). Δ = delta_num/delta_den
    // must be strictly positive. Any violation ⇒ the op is inapplicable.
    let delta = if delta_den == 0 {
        0.0
    } else {
        delta_num as f64 / delta_den as f64
    };
    // ln(a): the denominator of the log-axis step. For base e this is 1.0.
    let ln_a: f64 = if base_num == 0 {
        1.0
    } else if base_den > 0 && base_num > 0 {
        let a = base_num as f64 / base_den as f64;
        if a > 1.0 {
            a.ln()
        } else {
            f64::NAN
        }
    } else {
        f64::NAN
    };
    let usable = delta > 0.0 && ln_a.is_finite() && ln_a != 0.0 && value_slot >= 0;

    // The intensional log-render, applied on read: q = round(log_a(x)/Δ) when
    // raw (x is linear), or round(x/Δ) when x is already log-domain. A single
    // transient float, immediately rounded to i64 — the observable is the
    // stepped integer. Non-positive x under raw floors to ln(1e-9), matching
    // frame.py::_log_weights so the emitter equals the reasoning site.
    let quantum = |x: f64| -> i64 {
        let logx = if raw {
            if x > 0.0 {
                x.ln() / ln_a
            } else {
                (1e-9f64).ln() / ln_a
            }
        } else {
            // x is already a log-domain quantity in NATURAL units (math.log);
            // rebase to log_a by dividing by ln(a) (identity for base e).
            x / ln_a
        };
        (logx / delta).round() as i64
    };

    let slot = usize::try_from(value_slot).unwrap_or(usize::MAX);

    // Quantize one relation's value_slot to Int, leaving every other slot
    // byte-identical (kind-preserving via set_coord). A relation too short to
    // hold the slot, or not a Tuple/List, is passed through untouched.
    let quantize_rel = |rel: &Value| -> Value {
        if !usable {
            return rel.clone();
        }
        let (Value::Tuple(t) | Value::List(t)) = rel else {
            return rel.clone();
        };
        match t.get(slot) {
            Some(v) => {
                let q = quantum(v.as_f64());
                set_coord(rel, slot, q)
            }
            None => rel.clone(),
        }
    };

    // Walk the outer population → inner frames → relations. Non-collection
    // frames pass through as-is (mirrors eval_ratio_infer's tolerant reader).
    let mut n_frames: i64 = 0;
    let mut n_rels: i64 = 0;
    let frames_out: SmallVec<[Value; 4]> = match &pop_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => pop_val
            .iter()
            .map(|frame| match frame {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
                    n_frames += 1;
                    let rels: SmallVec<[Value; 4]> = frame
                        .iter()
                        .map(|rel| {
                            n_rels += 1;
                            quantize_rel(rel)
                        })
                        .collect();
                    frame.reseq(rels)
                }
                other => other.clone(),
            })
            .collect(),
        _ => SmallVec::new(),
    };

    let quantized = Value::Tuple(Arc::new(frames_out));

    if field == Sym::default() {
        return quantized;
    }
    let result = Value::Dict(Arc::from(vec![
        (surf("quantized"), quantized),
        (surf("n_frames"), Value::Int(n_frames)),
        (surf("n_rels"), Value::Int(n_rels)),
        (surf("value_slot"), Value::Int(value_slot)),
        (surf("usable"), Value::Bool(usable)),
    ]));
    finish(result, field, ctx.interner, None)
}

/// Infer a PURE-TRANSLATION offset carrying `f0 -> f1`, or `None` if `f1` is
/// not a rigid uniform translate of `f0`. Both frames are sorted by
/// `cmp_value` (a uniform coordinate shift preserves that order — it adds the
/// same constant to every cell's coords, and leaves the non-coord slots
/// untouched), then paired cell-by-cell: EVERY paired cell must differ by the
/// SAME integer offset on each `coord_dims` slot AND be byte-identical on
/// every non-coord slot (predicate / colour). This is the affine twin of
/// `GenInfer`'s linear enumerate-and-test, but the offset is READ directly
/// from the coordinate difference (there is nothing to search — a translation
/// is fixed by one cell pair, then VERIFIED across the rest).
fn infer_translate_offset(f0: &[Value], f1: &[Value], coord_dims: &[i64]) -> Option<Vec<i64>> {
    if f0.len() != f1.len() || f0.is_empty() {
        return None;
    }
    let mut a = f0.to_vec();
    let mut b = f1.to_vec();
    a.sort_by(cmp_value);
    b.sort_by(cmp_value);
    let n = coord_dims.len();
    let idxs: Vec<usize> = coord_dims
        .iter()
        .filter_map(|&d| usize::try_from(d).ok())
        .collect();
    if idxs.len() != n || n == 0 {
        return None;
    }
    // Offset from the FIRST paired cell; then verify it holds for all.
    let read = |rel: &Value, idx: usize| -> Option<i64> {
        let (Value::Tuple(t) | Value::List(t)) = rel else {
            return None;
        };
        match t.get(idx) {
            Some(Value::Int(v)) => Some(*v),
            _ => None,
        }
    };
    let mut offset: Vec<i64> = Vec::with_capacity(n);
    for &idx in &idxs {
        offset.push(read(&b[0], idx)? - read(&a[0], idx)?);
    }
    for (ra, rb) in a.iter().zip(b.iter()) {
        // coord slots differ by exactly `offset`
        for (j, &idx) in idxs.iter().enumerate() {
            if read(rb, idx)? - read(ra, idx)? != offset[j] {
                return None;
            }
        }
        // non-coord slots byte-identical (same predicate, same colour, same arity)
        let (Value::Tuple(ta) | Value::List(ta), Value::Tuple(tb) | Value::List(tb)) = (ra, rb)
        else {
            return None;
        };
        if ta.len() != tb.len() {
            return None;
        }
        for k in 0..ta.len() {
            if idxs.contains(&k) {
                continue;
            }
            if cmp_value(&ta[k], &tb[k]) != std::cmp::Ordering::Equal {
                return None;
            }
        }
    }
    Some(offset)
}

/// Are two frames equal as multisets of relations (order-independent)?
fn frames_equal(a: &[Value], b: &[Value]) -> bool {
    if a.len() != b.len() {
        return false;
    }
    let mut sa = a.to_vec();
    let mut sb = b.to_vec();
    sa.sort_by(cmp_value);
    sb.sort_by(cmp_value);
    sa.iter()
        .zip(sb.iter())
        .all(|(x, y)| cmp_value(x, y) == std::cmp::Ordering::Equal)
}

// ────────────────────────────────────────────────────────────────────────
//  DIMENSION-GENERIC ORDER-N — the finite-difference recursion
//
//  Order-N is a property of ANY dimension, not a time-special patch. Along an
//  ordered sequence of frames (whatever dimension indexes them — time, a
//  spatial scan, a minted latent axis: the CALLER supplies the ordering), fit
//  a per-pair generator; if that generator's PARAMETER is not constant along
//  the sequence but is itself REGULAR (its finite differences reach a
//  witnessed constant), RECURSE on the parameter's difference-stream (order+1).
//  Velocity (order-1) → acceleration (order-2) → jerk (order-3) → ... The SAME
//  code fits every order and every dimension; the order the loop reaches is
//  wherever the residual STOPS being compressible — no hard cap, no seeded
//  predicate, no `if dimension == time`.
//
//  These helpers operate on an integer-vector STREAM (`&[Vec<i64>]`) with NO
//  notion of which dimension indexes it — that is what makes the recursion
//  dimension-agnostic. `eval_time_infer` feeds them the per-pair translate
//  offset stream; the identical function would serve any ordered parameter
//  stream. `#[cfg(test)]` `order_n_generic_tests` exercises them on a raw
//  non-temporal stream to prove the point structurally.
// ────────────────────────────────────────────────────────────────────────

/// Elementwise `b - a` for two equal-length integer vectors (a stream step's
/// finite difference). Callers guarantee equal length (all offsets share
/// `coord_dims.len()`).
fn vec_sub(b: &[i64], a: &[i64]) -> Vec<i64> {
    b.iter().zip(a.iter()).map(|(x, y)| x - y).collect()
}

/// Build the finite-difference pyramid of an integer-vector stream:
/// `levels[0] == stream`, `levels[i+1]` = consecutive differences of
/// `levels[i]`. Building STOPS at the first level that is a WITNESSED
/// constant (all elements equal AND `len >= 2` — a single confirmation, the
/// honest MDL floor: one equal pair is the minimum evidence that a level is
/// constant rather than a length-1 accident), or when a level has `< 2`
/// elements (differencing can go no further). The returned pyramid is
/// classified by `pyramid_order`: dimension-agnostic, no notion of time.
fn diff_pyramid(stream: &[Vec<i64>]) -> Vec<Vec<Vec<i64>>> {
    let mut levels: Vec<Vec<Vec<i64>>> = vec![stream.to_vec()];
    loop {
        let cur = levels.last().unwrap();
        // Witnessed constant: >= 2 samples, all equal — stop, this is the order.
        if cur.len() >= 2 && cur.iter().all(|v| v == &cur[0]) {
            break;
        }
        // Cannot difference a < 2-element level: the stream never reached a
        // witnessed constant — it is NOT regular (random → floor).
        if cur.len() < 2 {
            break;
        }
        let next: Vec<Vec<i64>> = cur.windows(2).map(|w| vec_sub(&w[1], &w[0])).collect();
        levels.push(next);
    }
    levels
}

/// The order a difference pyramid witnesses, or `None` if the stream is not
/// regular. Order = `levels.len()` (level 0 = order 1, the constant-parameter
/// case) IFF the deepest level is a witnessed constant (`>= 2` equal
/// elements). A pyramid whose deepest level is `< 2` elements and not equal
/// (differencing bottomed out without ever finding a constant) is
/// incompressible → `None`.
fn pyramid_order(levels: &[Vec<Vec<i64>>]) -> Option<usize> {
    let last = levels.last()?;
    if last.len() >= 2 && last.iter().all(|v| v == &last[0]) {
        Some(levels.len())
    } else {
        None
    }
}

/// Newton forward-difference extrapolation: the NEXT vector of the stream,
/// given its pyramid is regular (deepest level a witnessed constant). The
/// next element of the deepest (constant) level IS that constant; the next
/// element of each shallower level = its last element + the next element of
/// the level just below. Walking bottom-up yields the next stream element.
fn extrapolate_next(levels: &[Vec<Vec<i64>>]) -> Vec<i64> {
    let n = levels.len();
    // Deepest level is constant: its next element equals any of its elements.
    let mut carry = levels[n - 1][0].clone();
    for l in (0..n - 1).rev() {
        let last = levels[l].last().unwrap();
        carry = last.iter().zip(carry.iter()).map(|(a, c)| a + c).collect();
    }
    carry
}

// ────────────────────────────────────────────────────────────────────────
//  ROBUST / MDL order-N witness — "bins propose, continuous decides."
//
//  The exact `diff_pyramid`/`pyramid_order` witness above requires the deepest
//  difference level to be EXACTLY constant. That is correct and load-bearing
//  for integer-Euler physics (`d2 = [1,1,1,1]`, dispersion 0) but too brittle
//  for REAL perception: a continuous fall sampled into noisy integers has a
//  second difference that clusters around a constant yet is never all-equal
//  (quantization + tracking glitch it by ±1–2 cells, plus rare bigger
//  outliers). This witness replaces exact equality with a DESCRIPTION-LENGTH
//  decision on the SAME pyramid (proposal unchanged): order-k is witnessed iff
//  modeling difference-level k as a single constant + its residual has a
//  STRICTLY LOWER description length than the raw stream — i.e. order-k
//  genuinely COMPRESSES the trajectory given the noise.
//
//  The tolerance FALLS OUT of the integer bit-costs (`ibits`), never a picked
//  constant: a level that is constant to within small residuals encodes
//  cheaply and wins; a level whose spread rivals its magnitude (random, or
//  differencing that AMPLIFIES noise) encodes no cheaper than raw and loses,
//  so random and genuine-noise still FLOOR. Zero dispersion ⇒ zero residual
//  cost ⇒ this agrees with the exact witness (but the exact path is taken
//  first, so this only ever runs where the exact witness already floored:
//  purely additive).
//
//  The fitted constant is the per-component MEDIAN — the L1/MDL-robust centre,
//  which IGNORES the rare glitch outliers real perception produces (a mean
//  would be dragged by them and break the witness).
// ────────────────────────────────────────────────────────────────────────

/// Bit-cost of an integer in a simple sign+magnitude code: 1 sign bit plus the
/// magnitude's bit-length (`0` costs 1). Monotone in `|x|` and identical for
/// every value compared, so description-length comparisons are fair; the
/// tolerance the witness uses is exactly this code, no separate threshold.
fn ibits(x: i64) -> u64 {
    let a = x.unsigned_abs();
    (64 - a.leading_zeros() as u64) + 1
}

/// Description-length of an integer vector = summed `ibits` of its components.
fn vec_ibits(v: &[i64]) -> u64 {
    v.iter().map(|&x| ibits(x)).sum()
}

/// The (upper) median of a set of integers — the L1-minimizing, outlier-robust
/// centre used to fit a difference level as "a constant".
fn median_i64(mut xs: Vec<i64>) -> i64 {
    xs.sort_unstable();
    let n = xs.len();
    if n == 0 {
        0
    } else {
        xs[n / 2]
    }
}

/// Per-component median of a level (a slice of equal-length integer vectors) —
/// the robust constant the level is modeled by.
fn median_vec(level: &[Vec<i64>]) -> Vec<i64> {
    if level.is_empty() {
        return Vec::new();
    }
    let d = level[0].len();
    (0..d)
        .map(|j| median_i64(level.iter().map(|v| v[j]).collect()))
        .collect()
}

/// The FULL finite-difference pyramid — like `diff_pyramid` but WITHOUT the
/// exact-constant early stop: it differences all the way down until a level has
/// `< 2` elements. The robust witness evaluates a description length at every
/// depth, so it needs the whole pyramid, not the truncated exact one.
fn full_pyramid(stream: &[Vec<i64>]) -> Vec<Vec<Vec<i64>>> {
    let mut levels: Vec<Vec<Vec<i64>>> = vec![stream.to_vec()];
    while levels.last().unwrap().len() >= 2 {
        let cur = levels.last().unwrap();
        let next: Vec<Vec<i64>> = cur.windows(2).map(|w| vec_sub(&w[1], &w[0])).collect();
        levels.push(next);
    }
    levels
}

/// The ROBUST/MDL order witness. Returns `Some((order, fit_levels))` — the
/// order (≥ 2) whose difference level, modeled as a robust constant + residual,
/// gives the MINIMUM description length AND strictly beats the raw stream — or
/// `None` (floor) when no order compresses (random / genuine noise), when the
/// best order is 1 (near-constant velocity is the caller's exact path, not
/// minted here), or when there is too little evidence.
///
/// `fit_levels` is the pyramid truncated to the winning depth with its deepest
/// level DENOISED to the fitted constant, so `emit_order_n`'s
/// `extrapolate_next`/`coeffs` describe the clean generator, not the noise.
fn robust_order(stream: &[Vec<i64>]) -> Option<(usize, Vec<Vec<Vec<i64>>>)> {
    robust_order_min(stream, 2)
}

/// `robust_order` with the minimum acceptable order made an ARGUMENT rather
/// than baked in at 2.
///
/// The `min_order = 2` caller is the MINTING one: a near-constant velocity is
/// the exact witness's own byte-identical path, so the tolerant witness must
/// not mint it as a "discovery". The `min_order = 1` caller is the FORWARD
/// PROJECTION one (`project_stream`): to extrapolate a real, noisy trajectory
/// the order-1 case is exactly as legitimate as the order-2 case — a steady
/// noisy descent has no exactly-equal difference level anywhere, so refusing
/// order 1 there would refuse to project the commonest real stream there is.
/// The two callers ask different questions of the same MDL verdict; nothing
/// about the verdict itself changes.
fn robust_order_min(stream: &[Vec<i64>], min_order: usize) -> Option<(usize, Vec<Vec<Vec<i64>>>)> {
    // Order-k needs a level-(k−1) of ≥ 3 elements (≥ 3 confirmations that the
    // fitted constant is one value, not a 2-point coincidence) ⇒ stream ≥ k+2.
    if stream.len() < min_order + 2 {
        return None;
    }
    let pyr = full_pyramid(stream);

    // The null model: describe the raw stream with no structure at all.
    let dl_null: u64 = stream.iter().map(|v| vec_ibits(v)).sum();

    // Description length of "stop at depth m, model level m as a constant":
    //   leading coeffs (levels 0..m first elements) + fitted constant of m
    //   + residuals of level m about that constant. This is a LOSSLESS
    //   re-encoding of the same data (integrate m times to reconstruct), so
    //   the shortest one is the best explanation — MDL, no threshold.
    let dl = |m: usize| -> Option<u64> {
        let lvl = &pyr[m];
        if lvl.len() < 2 {
            return None;
        }
        let cst = median_vec(lvl);
        let resid: u64 = lvl.iter().map(|v| vec_ibits(&vec_sub(v, &cst))).sum();
        let lead: u64 = (0..m).map(|i| vec_ibits(&pyr[i][0])).sum::<u64>() + vec_ibits(&cst);
        Some(resid + lead)
    };

    // Global argmin over depth (smallest depth wins ties — Occam / lowest order).
    let mut best_m = 0usize;
    let mut best_dl = u64::MAX;
    for m in 0..pyr.len() {
        if let Some(d) = dl(m) {
            if d < best_dl {
                best_dl = d;
                best_m = m;
            }
        }
    }
    // Must genuinely COMPRESS the raw stream — else it is not structure (floor).
    if best_dl >= dl_null {
        return None;
    }
    let order = best_m + 1;
    if order < min_order {
        return None;
    }
    // Evidence guard: the winning level needs ≥ 3 samples to witness a constant.
    if pyr[best_m].len() < 3 {
        return None;
    }

    // Denoise the deepest (winning) level to its fitted constant for a clean
    // generator descriptor / extrapolation.
    let mut fit: Vec<Vec<Vec<i64>>> = pyr[..=best_m].to_vec();
    let cst = median_vec(&fit[best_m]);
    let len = fit[best_m].len();
    fit[best_m] = vec![cst; len];
    Some((order, fit))
}

// ────────────────────────────────────────────────────────────────────────
//  FORWARD PROJECTION AT THE MEASURED ORDER — `order_fit` / `crossing`
//
//  The one-step `predicted` frame answers "what comes next". A consumer that
//  has to DECIDE against a deadline needs the other reading of the same fit:
//  how many steps does this stream's OWN generator take to carry it to the
//  frame's ORIGIN? That is the order-N generalisation of the commonest
//  quantity in any control loop — `margin / rate` — which is nothing but a
//  FIRST-ORDER extrapolation wearing no clock: it is `crossing` with the fit
//  forced to order 1. Read at the MEASURED order it is a different number,
//  and the difference is the curvature the linear reading throws away.
//
//  Dimension-generic exactly as the recursion below it: the iteration knows
//  nothing about what indexes the stream, and nothing about what the stream
//  measures. The only thing it declares is that ZERO is the floor — which is
//  not a seeded predicate but the origin of the integer lattice the caller
//  built its coordinate on (a caller whose terminal state is elsewhere shifts
//  its own coordinate, exactly as it must to make the quantity in-frame).
// ────────────────────────────────────────────────────────────────────────

/// Fit a stream's forward generator: the EXACT pyramid where it witnesses a
/// constant, else — for a caller that opted into the cross-frame question —
/// the MDL/robust fit at any order ≥ 1. Returns `(order, levels)` with the
/// deepest level constant, ready for `extrapolate_next` / `steps_to_origin`,
/// or `None` when the stream is incompressible at every order (no structure ⇒
/// no projection ⇒ the honest floor).
fn project_stream(stream: &[Vec<i64>], robust: bool) -> Option<(usize, Vec<Vec<Vec<i64>>>)> {
    let levels = diff_pyramid(stream);
    if let Some(order) = pyramid_order(&levels) {
        return Some((order, levels));
    }
    if !robust {
        return None;
    }
    robust_order_min(stream, 1)
}

/// Iterate a fitted pyramid forward and COUNT the steps until the projected
/// stream reaches the origin (any component `<= 0`), capped at `max_steps`.
///
/// This is `extrapolate_next` run in a loop with the level-wise carries kept,
/// which is Newton forward iteration: the deepest level is the fitted
/// constant, and each shallower level's next element is its own last plus the
/// next element of the level below. No root-finding, no closed form, no order
/// cap — the same walk serves order 1, 2, 3 and beyond.
fn steps_to_origin(levels: &[Vec<Vec<i64>>], max_steps: i64) -> i64 {
    let m = levels.len();
    if m == 0 || max_steps <= 0 {
        return max_steps.max(0);
    }
    let mut cur: Vec<Vec<i64>> = match levels
        .iter()
        .map(|l| l.last().cloned())
        .collect::<Option<Vec<Vec<i64>>>>()
    {
        Some(c) => c,
        None => return max_steps,
    };
    for k in 1..=max_steps {
        let mut next = cur.clone();
        for l in (0..m.saturating_sub(1)).rev() {
            next[l] = cur[l]
                .iter()
                .zip(next[l + 1].iter())
                .map(|(a, c)| a.saturating_add(*c))
                .collect();
        }
        if next[0].iter().any(|&x| x <= 0) {
            return k;
        }
        cur = next;
    }
    max_steps
}

/// The per-frame COORDINATE VECTOR stream — one integer vector per frame,
/// read from the frame's canonically-first relation (frames are compared as
/// multisets everywhere else here, so the sort is what makes "first" mean
/// anything). For a rigid translate every cell carries the same motion, so
/// any one of them is the frame's coordinate; a single-relation frame — the
/// shape a scalar sample stream takes — is the degenerate case.
fn frame_value_stream(frames: &[Vec<Value>], coord_dims: &[i64]) -> Option<Vec<Vec<i64>>> {
    let idxs: Vec<usize> = coord_dims
        .iter()
        .filter_map(|&d| usize::try_from(d).ok())
        .collect();
    if idxs.len() != coord_dims.len() || idxs.is_empty() {
        return None;
    }
    let mut out = Vec::with_capacity(frames.len());
    for frame in frames {
        let mut f = frame.to_vec();
        f.sort_by(cmp_value);
        let first = f.first()?;
        let (Value::Tuple(t) | Value::List(t)) = first else {
            return None;
        };
        let mut row = Vec::with_capacity(idxs.len());
        for &i in &idxs {
            match t.get(i) {
                Some(Value::Int(v)) => row.push(*v),
                _ => return None,
            }
        }
        out.push(row);
    }
    Some(out)
}

/// `order_fit` + `crossing`, computed on the frame sequence's own coordinate
/// stream INDEPENDENTLY of the orbit verdict — a consumer projecting a real
/// trajectory needs the numbers whether or not the sequence is an exact orbit.
#[derive(Clone, Copy)]
struct Projection {
    /// The order the forward fit reached along the DIFFERENCE stream, in the
    /// same units as `order` (1 = constant velocity, 2 = constant
    /// acceleration, 3 = jerk, …); `0` = incompressible at every order.
    order_fit: i64,
    /// Steps until the fitted generator carries the coordinate to the origin,
    /// capped at `max_steps` (also the value when it never does, and when
    /// there is no fit at all — no measured structure is no measured
    /// deadline).
    crossing: i64,
}

fn project_frames(
    frames: &[Vec<Value>],
    coord_dims: &[i64],
    robust: bool,
    max_steps: i64,
) -> Projection {
    let floor = Projection {
        order_fit: 0,
        crossing: max_steps.max(0),
    };
    let Some(values) = frame_value_stream(frames, coord_dims) else {
        return floor;
    };
    if values.len() < 3 {
        return floor;
    }
    // Fit the DIFFERENCE stream so `order_fit` reads in the same units as
    // `order` (order 1 = velocity), then put the value stream back on top so
    // the iteration walks the coordinate itself.
    let diffs: Vec<Vec<i64>> = values.windows(2).map(|w| vec_sub(&w[1], &w[0])).collect();
    let Some((order, mut levels)) = project_stream(&diffs, robust) else {
        return floor;
    };
    levels.insert(0, values);
    Projection {
        order_fit: order as i64,
        crossing: steps_to_origin(&levels, max_steps.max(0)),
    }
}

/// DIMENSION-GENERIC order-N verdict for a frame sequence whose every
/// consecutive pair is a rigid TRANSLATE. Called ONLY when the caller's
/// order-1 exact-equality path has GIVEN UP, so it is purely additive: it
/// turns a former `time_none` floor into an order-N mint exactly where the
/// per-pair offset stream is itself regular, and returns `None` (leaving the
/// existing floor to stand) otherwise.
///
/// Requires `frames.len() >= 3` (an order-2 fit needs `>= 2` offsets to
/// difference) and that EVERY consecutive pair be a translate
/// (`infer_translate_offset`); the offset stream is then fitted by the
/// finite-difference recursion. Returns `None` when the pairs are not all
/// translates, the offset stream is not regular (random → floor), or the
/// fitted order is `< 2` (order-1 is the caller's byte-identical path — an
/// all-equal offset stream would already have been explained there, and an
/// all-zero one is the excluded identity). On success, builds the same Dict
/// schema as the explained path, plus `order` (N) and `coeffs` (the leading
/// finite differences per level — the full polynomial descriptor), and
/// predicts the UNSEEN next frame by extrapolating one more offset.
#[allow(clippy::too_many_arguments)]
fn order_n_translate_verdict(
    frames: &[Vec<Value>],
    coord_dims: &[i64],
    field: Sym,
    robust: bool,
    projection: Projection,
    ctx: &mut EvalCtx,
) -> Option<Value> {
    if frames.len() < 3 {
        return None;
    }
    // Per-pair translate offsets — any non-translate pair aborts the fit.
    let mut stream: Vec<Vec<i64>> = Vec::with_capacity(frames.len() - 1);
    for i in 0..frames.len() - 1 {
        let off = infer_translate_offset(&frames[i], &frames[i + 1], coord_dims)?;
        stream.push(off);
    }
    // TWO-TIER witness. First the UNCHANGED exact-equality pyramid — every
    // currently-minting (synthetic, integer-Euler) case takes this path
    // BYTE-IDENTICALLY; nothing below runs for it.
    let levels = diff_pyramid(&stream);
    match pyramid_order(&levels) {
        Some(order) if order >= 2 => {
            // EXACT order-N (a witnessed-constant level) — the original path.
            emit_order_n(frames, coord_dims, &levels, order, field, projection, ctx)
        }
        Some(_) => None, // order-1 is the caller's exact-equality path (byte-identical)
        None => {
            // The exact witness FLOORED (no level is EXACTLY constant). Only a
            // caller that OPTED IN to the cross-frame question (`robust`) gets
            // the tolerant/MDL verdict; the default consumers floor here exactly
            // as before (byte-identical). The robust witness asks: is some
            // difference level constant to within the trajectory's OWN
            // dispersion — i.e. does modeling it as a constant + residual
            // COMPRESS the stream below its raw description length ("bins
            // propose, continuous decides")? Tolerance falls out of the integer
            // bit-costs — no picked threshold. It is the STEPPED observation of
            // a continuous parabola (a fractional/cross-frame acceleration),
            // NOT an in-frame integer generator, which is why it is opt-in: the
            // exact witness's floor here is CORRECT for a consumer that needs
            // the integer generator (mass recovery), and this is a different
            // question.
            if !robust {
                return None;
            }
            let (order, fit_levels) = robust_order(&stream)?;
            emit_order_n(
                frames,
                coord_dims,
                &fit_levels,
                order,
                field,
                projection,
                ctx,
            )
        }
    }
}

/// Build the order-N `TimeInfer` verdict Dict from a difference pyramid whose
/// DEEPEST level is a constant (exactly all-equal on the exact path, or the
/// robust fitted constant on the MDL path). Shared by both witnesses so the
/// exact path is byte-identical: given the same `levels`/`order` it produces
/// the same value it always did.
fn emit_order_n(
    frames: &[Vec<Value>],
    coord_dims: &[i64],
    levels: &[Vec<Vec<i64>>],
    order: usize,
    field: Sym,
    projection: Projection,
    ctx: &mut EvalCtx,
) -> Option<Value> {
    // Predict the UNSEEN next frame: extrapolate one more offset, apply it to
    // the last observed frame.
    let next_off = extrapolate_next(levels);
    let last_frame = frames.last().unwrap();
    let predicted = apply_translate_once(last_frame, coord_dims, &next_off).unwrap_or_default();

    let k = frames.len() as i64;
    let base_offset = &levels[0][0]; // off_0 — the initial velocity
    let offset_out: SmallVec<[Value; 4]> = base_offset.iter().map(|x| Value::Int(*x)).collect();
    let coord_out: SmallVec<[Value; 4]> = coord_dims.iter().map(|d| Value::Int(*d)).collect();
    let predicted_out: SmallVec<[Value; 4]> = predicted.into_iter().collect();
    // coeffs: leading finite difference of each level (Newton forward
    // coefficients) — the complete order-N generator descriptor.
    let coeffs_out: SmallVec<[Value; 4]> = levels
        .iter()
        .map(|lvl| {
            let row: SmallVec<[Value; 4]> = lvl[0].iter().map(|x| Value::Int(*x)).collect();
            Value::Tuple(Arc::new(row))
        })
        .collect();

    finish(
        Value::Dict(Arc::from(vec![
            (surf("explained"), Value::Bool(true)),
            (surf("kind"), surf("translate")),
            (surf("offset"), Value::Tuple(Arc::new(offset_out))),
            (surf("matrix"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("coord_dims"), Value::Tuple(Arc::new(coord_out))),
            (surf("window"), Value::Int(k)),
            (surf("predicted"), Value::Tuple(Arc::new(predicted_out))),
            (surf("checked"), Value::Int(0)),
            (surf("order"), Value::Int(order as i64)),
            (surf("coeffs"), Value::Tuple(Arc::new(coeffs_out))),
            (surf("order_fit"), Value::Int(projection.order_fit)),
            (surf("crossing"), Value::Int(projection.crossing)),
        ])),
        field,
        ctx.interner,
        None,
    )
    .into()
}

#[cfg(test)]
mod order_n_generic_tests {
    use super::{diff_pyramid, extrapolate_next, pyramid_order, robust_order};

    // The recursion is tested here on RAW integer-vector streams with NO
    // temporal (or any dimensional) meaning — the structural proof that
    // order-N is dimension-agnostic: the same `diff_pyramid`/`pyramid_order`/
    // `extrapolate_next` that `eval_time_infer` feeds a TIME offset stream
    // work identically on a stream that could index space, a latent axis, or
    // nothing at all. No `if dimension == time` exists to test around.

    fn order(stream: &[Vec<i64>]) -> Option<usize> {
        pyramid_order(&diff_pyramid(stream))
    }

    #[test]
    fn constant_stream_is_order_1() {
        // velocity constant -> order 1 (the caller handles this exactly).
        assert_eq!(order(&[vec![3], vec![3], vec![3]]), Some(1));
    }

    #[test]
    fn arithmetic_stream_is_order_2() {
        // 1,2,3,4,5,6 : 2nd diff constant -> order 2 (acceleration).
        let s: Vec<Vec<i64>> = (1..=6).map(|v| vec![v]).collect();
        assert_eq!(order(&s), Some(2));
        // extrapolate: next offset after 6 is 7.
        assert_eq!(extrapolate_next(&diff_pyramid(&s)), vec![7]);
    }

    #[test]
    fn quadratic_stream_is_order_3() {
        // 1,2,4,7,11,16 : 3rd diff constant -> order 3 (jerk).
        let s = vec![vec![1], vec![2], vec![4], vec![7], vec![11], vec![16]];
        assert_eq!(order(&s), Some(3));
        assert_eq!(extrapolate_next(&diff_pyramid(&s)), vec![22]);
    }

    #[test]
    fn irregular_stream_floors() {
        // the Stage-0 random control's position deltas: never a witnessed
        // constant before length runs out -> not regular at any order.
        let s = vec![vec![-6], vec![5], vec![2], vec![-8], vec![8], vec![1]];
        assert_eq!(order(&s), None);
    }

    #[test]
    fn multi_dim_vector_stream_recurses_per_component() {
        // A 2-D offset stream (r accelerates, c is constant velocity): the
        // recursion is elementwise, so a mixed-order vector fits at the max
        // component order (r is order-2). Same code, vector-valued.
        let s = vec![vec![1, 5], vec![2, 5], vec![3, 5], vec![4, 5], vec![5, 5]];
        assert_eq!(order(&s), Some(2));
        assert_eq!(extrapolate_next(&diff_pyramid(&s)), vec![6, 5]);
    }

    // ── the ROBUST/MDL witness (the noise-tolerant order-N) ──────────────
    // These prove the two absolute bars at the Rust level: it accepts a
    // NOISY parabola (order-2) yet keeps genuine noise OUT (floors), and the
    // tolerance is not a magic number — it falls out of the description length.

    #[test]
    fn robust_noisy_parabola_is_order_2() {
        // A velocity (offset) stream whose acceleration is ~constant (≈3) but
        // NOT exactly so — quantization jitter ±1 and one big glitch. The exact
        // pyramid never finds an all-equal level (floors); the robust witness
        // sees level-1 (acceleration) is constant to within its dispersion and
        // compresses, so it mints order-2.
        let vel = vec![2i64, 5, 9, 12, 14, 18, 20, 24, 27, 29];
        // d(vel) = [3,4,3,2,4,2,4,3,2] — clusters at 3, never all-equal.
        let s: Vec<Vec<i64>> = vel.iter().map(|&v| vec![v]).collect();
        assert_eq!(
            diff_pyramid(&s).last().unwrap().len() < 2
                || !diff_pyramid(&s)
                    .last()
                    .unwrap()
                    .iter()
                    .all(|v| v == &diff_pyramid(&s).last().unwrap()[0]),
            true,
            "exact witness must NOT fire on the noisy stream"
        );
        let (order, _fit) =
            robust_order(&s).expect("robust witness should mint the noisy parabola");
        assert_eq!(order, 2);
    }

    #[test]
    fn robust_glitch_outlier_parabola_is_order_2() {
        // The real-perception shape: a run of exact-constant acceleration with
        // a couple of big ±glitch outliers (the ball's blob shifting on the
        // coarse grid). MEDIAN fitting ignores the outliers; MEAN would not.
        // accel d2 = [3,3,3,3,3,-11,3,9,3,3] around a clear constant 3.
        let d2 = [3i64, 3, 3, 3, 3, -11, 3, 9, 3, 3];
        let mut vel = vec![5i64];
        for d in d2 {
            vel.push(vel.last().unwrap() + d);
        }
        let s: Vec<Vec<i64>> = vel.iter().map(|&v| vec![v]).collect();
        let (order, _fit) = robust_order(&s).expect("median-robust witness mints through glitches");
        assert_eq!(order, 2);
    }

    #[test]
    fn robust_random_still_floors() {
        // The load-bearing soundness bar: several genuine-noise streams must
        // mint NOTHING — differencing amplifies their spread, so no order
        // compresses below raw. A witness loose enough to accept these is WRONG.
        let randoms: [&[i64]; 4] = [
            &[-6, 5, 2, -8, 8, 1, -3, 7],
            &[4, -9, 3, 6, -2, 10, -7, 1],
            &[0, 11, -4, 5, -6, 2, 9, -8],
            &[13, -2, 7, -11, 4, 6, -9, 3],
        ];
        for r in randoms {
            let s: Vec<Vec<i64>> = r.iter().map(|&v| vec![v]).collect();
            assert!(robust_order(&s).is_none(), "random {:?} must floor", r);
        }
    }

    #[test]
    fn robust_tolerance_falls_out_no_magic_number() {
        // §13 tolerance-falls-out: with the SAME fixed noise pattern, whether
        // order-2 is minted is decided by whether the CURVATURE (acceleration)
        // rises above the noise — the crossover falls out of the data's own
        // bit-costs, there is no threshold constant. Curvature present ->
        // order-2 compresses and mints; curvature absent (constant-velocity +
        // the same noise) -> no order-2 to find, it floors.
        let noise = [1i64, -1, 1, 0, -1, 1, 0, -1];
        // curvature present (accel ≈ 4 >> noise): compresses -> order-2.
        let curved: Vec<i64> = noise
            .iter()
            .scan(2i64, |v, &n| {
                let cur = *v;
                *v += 4 + n;
                Some(cur)
            })
            .collect();
        let s_curved: Vec<Vec<i64>> = curved.iter().map(|&v| vec![v]).collect();
        assert_eq!(
            robust_order(&s_curved).map(|(o, _)| o),
            Some(2),
            "curvature above the noise -> order-2"
        );
        // curvature absent (accel = 0, SAME noise): near-constant velocity, no
        // second-order structure -> the witness declines to mint order-2.
        let flat: Vec<i64> = noise
            .iter()
            .scan(2i64, |v, &n| {
                let cur = *v;
                *v += n;
                Some(cur)
            })
            .collect();
        let s_flat: Vec<Vec<i64>> = flat.iter().map(|&v| vec![v]).collect();
        assert!(
            robust_order(&s_flat).is_none(),
            "same noise, no curvature -> no order-2 (tolerance from the data)"
        );
    }

    // ─────────────── FORWARD PROJECTION AT THE MEASURED ORDER ───────────
    // `steps_to_origin` on raw integer-vector streams — again with no
    // dimensional meaning attached. The point of every one of these is the
    // SAME comparison: a first-order reading of a curving stream and the
    // measured-order reading of it are DIFFERENT NUMBERS, and the linear one
    // is always the optimistic one.

    use super::{project_stream, steps_to_origin};

    fn project_to_origin(values: &[i64], robust: bool, max_steps: i64) -> Option<(usize, i64)> {
        let s: Vec<Vec<i64>> = values.iter().map(|&v| vec![v]).collect();
        let diffs: Vec<Vec<i64>> = s.windows(2).map(|w| super::vec_sub(&w[1], &w[0])).collect();
        let (order, mut levels) = project_stream(&diffs, robust)?;
        levels.insert(0, s);
        Some((order, steps_to_origin(&levels, max_steps)))
    }

    #[test]
    fn order_1_crossing_is_the_linear_projection() {
        // margin 100, falling 10 per step: the schoolbook `margin / rate`.
        let v: Vec<i64> = (0..6).map(|i| 100 - 10 * i).collect(); // 100..50
        assert_eq!(
            project_to_origin(&v, false, 1000),
            Some((1, 5)),
            "50 left at 10 per step = 5 steps"
        );
    }

    #[test]
    fn order_2_crossing_is_shorter_than_the_linear_one() {
        // THE HEADLINE. A stream whose FIRST difference is mild but whose
        // SECOND difference is negative: the linear reading of the same
        // instant says far more time than the measured order-2 reading.
        // margin: 100, 99, 96, 91, 84, 75  (d1 = -1,-3,-5,-7,-9; d2 = -2)
        let v = [100i64, 99, 96, 91, 84, 75];
        let (order, crossing) = project_to_origin(&v, false, 1000).expect("regular");
        assert_eq!(order, 2, "constant second difference -> order 2");
        // The order-1 reading from the same last instant (75 left, falling 9)
        // would be 9 steps. The measured order-2 reading is far shorter.
        assert!(
            crossing < 9,
            "order-2 crossing {crossing} must beat the linear 9"
        );
        assert_eq!(crossing, 5, "75, 64, 51, 36, 19, 0 — the origin on step 5");
    }

    #[test]
    fn a_rising_stream_never_crosses_and_reports_the_horizon() {
        let v: Vec<i64> = (0..6).map(|i| 100 + 10 * i).collect();
        assert_eq!(
            project_to_origin(&v, false, 40),
            Some((1, 40)),
            "no crossing within the declared horizon -> the horizon"
        );
    }

    #[test]
    fn a_noisy_descent_projects_only_under_the_robust_witness() {
        // Real telemetry: a steady descent whose per-step difference is never
        // EXACTLY equal. The exact witness floors (correctly — there is no
        // integer generator carrying every pair); the cross-frame/robust
        // witness fits order 1 at the median rate and projects.
        let noise = [0i64, 1, -1, 0, 1, -1, 0, 1, -1, 0];
        let v: Vec<i64> = noise
            .iter()
            .scan(100i64, |a, &n| {
                let cur = *a;
                *a += -10 + n;
                Some(cur)
            })
            .collect();
        assert!(
            project_to_origin(&v, false, 1000).is_none(),
            "exact witness must floor on a noisy stream"
        );
        let (order, crossing) =
            project_to_origin(&v, true, 1000).expect("robust witness projects a noisy descent");
        assert_eq!(order, 1);
        // last value ~ 10; at ~10 per step it is about one step out.
        assert!((1..=3).contains(&crossing), "crossing {crossing}");
    }

    #[test]
    fn an_incompressible_stream_has_no_projection() {
        // No measured structure is no measured deadline — the honest floor,
        // the same one the order witness already had.
        let v = [100i64, 3, 88, 12, 70, 95, 4, 61];
        assert!(project_to_origin(&v, true, 1000).is_none());
    }

    #[test]
    fn no_order_cap_the_walk_serves_order_3() {
        // Cubic: d3 constant. The same iteration, one level deeper — nothing
        // in `steps_to_origin` knows the order it is walking.
        let v: Vec<i64> = (0..7).map(|i: i64| 200 - i * i * i).collect();
        let (order, crossing) = project_to_origin(&v, false, 1000).expect("regular");
        assert_eq!(order, 3);
        assert_eq!(crossing, 1, "200 - 7^3 = -143, already past the origin");
    }
}

/// Evaluate `TimeInfer` — the TEMPORAL sibling of `GenInfer`, one level up: it
/// asks whether a SEQUENCE of frames (presented in tick order) is an ORBIT
/// under a SINGLE transition generator `G` that carries `frame(t) -> frame(t+1)`
/// for EVERY consecutive pair — and if so, that generator's exponent `k` IS the
/// inferred TIME axis (a minted `latent:time` dimension, exactly as a spatial
/// dimension is minted from a spatial orbit; time lives in `Hom(frame,frame)`,
/// never in a frame's coordinates — this tree's frame/continuum invariant).
///
/// The transition `G` is inferred from the FIRST consecutive pair `(f0, f1)`,
/// preferring the affine translate (a rigid uniform shift — the retinal
/// drifting-pattern case, `infer_translate_offset`) and otherwise an integer
/// 2×2 linear map (the SAME enumerate-and-test as `GenInfer`,
/// `apply_linear_once`), then VERIFIED across every remaining pair by EXACT
/// equality (`frames_equal`) — no residual slack. The identity is excluded
/// (a still pattern is not a motion). A shuffled sequence is NOT an orbit
/// (no single `G` carries every PRESENTED pair — for a constant-velocity
/// translation any two frames are mutual translates PAIRWISE, but the
/// CONSTANT offset that carries every consecutive pair in order is destroyed
/// by the shuffle), so it grounds unexplained: the honest MDL floor.
///
/// `field` selects: `explained` (bool) / `kind` (`"translate"`/`"linear"`) /
/// `offset` (Tuple of Ints, translate) / `matrix` (Tuple of Ints, linear) /
/// `coord_dims` / `window` (K = frames seen) / `predicted` (the UNSEEN frame
/// `G^K(f0)` — the downstream prediction the minted axis must MOVE) / `checked`.
/// Integer lattice only; `dim_types` (which slots are coords) is read from the
/// first `codebook_type` part, exactly as `GenInfer`/`DimInfer` do.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_time_infer(
    arena: &TermArena,
    sequence_idx: TermIdx,
    codebook_type: Sym,
    max_b: i64,
    field: Sym,
    max_steps: i64,
    robust: bool,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_TIME_INFER);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    // dim_types (coord slots) from the first part that declares them.
    let coord_dims: Vec<i64> = parts
        .iter()
        .find_map(|p| p.dim_types.as_ref())
        .map(|dts| {
            dts.iter()
                .enumerate()
                .filter(|(_, t)| t.starts_with("coord:"))
                .map(|(i, _)| i as i64)
                .collect()
        })
        .unwrap_or_default();

    let seq_val = evaluate(arena, sequence_idx, env, ctx);
    let frames: Vec<Vec<Value>> = match &seq_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => seq_val
            .iter()
            .map(|f| match f {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
                    f.iter().cloned().collect()
                }
                _ => Vec::new(),
            })
            .collect(),
        _ => Vec::new(),
    };

    // The FORWARD PROJECTION reading of the same fit (`order_fit`/`crossing`).
    // Computed on the frame sequence's own coordinate stream, independently of
    // whether the sequence is an exact orbit, so a consumer projecting a real
    // trajectory gets a number on every path — including the floor, where it
    // is the honest "no measured structure ⇒ no measured deadline".
    let projection = if frames.len() >= 3 && !coord_dims.is_empty() {
        project_frames(&frames, &coord_dims, robust, max_steps)
    } else {
        Projection {
            order_fit: 0,
            crossing: max_steps.max(0),
        }
    };

    let unexplained = |checked: i64, ctx: &mut EvalCtx| -> Value {
        finish(
            Value::Dict(Arc::from(vec![
                (surf("explained"), Value::Bool(false)),
                (surf("kind"), Value::None),
                (surf("offset"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("matrix"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("coord_dims"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("window"), Value::Int(0)),
                (surf("predicted"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("checked"), Value::Int(checked)),
                // order 0 = no regular generator at any order (schema-uniform with
                // the explained paths; additive — no existing query reads `order`).
                (surf("order"), Value::Int(0)),
                (surf("coeffs"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("order_fit"), Value::Int(projection.order_fit)),
                (surf("crossing"), Value::Int(projection.crossing)),
            ])),
            field,
            ctx.interner,
            None,
        )
    };

    if frames.len() < 2 || coord_dims.is_empty() || frames.iter().any(|f| f.is_empty()) {
        return unexplained(0, ctx);
    }
    let (f0, f1) = (&frames[0], &frames[1]);

    // --- infer the transition generator from (f0, f1) ---
    // Data-derived bound B for the linear search (max abs normalized coord),
    // capped by max_b (a caller-supplied safety cap, itself data-scaled).
    let mut checked: i64 = 0;
    enum G {
        Translate(Vec<i64>),
        Linear(Vec<i64>),
    }
    let g: Option<G> = if let Some(off) = infer_translate_offset(f0, f1, &coord_dims) {
        if off.iter().all(|&x| x == 0) {
            None
        } else {
            Some(G::Translate(off))
        }
    } else if coord_dims.len() == 2 {
        // enumerate integer 2×2 M within the data bound; first EXACT carrier wins
        let bound: i64 = coord_dims
            .iter()
            .filter_map(|&d| {
                let idx = usize::try_from(d).ok()?;
                let vs = coord_ints(f0, idx)?;
                let mn = *vs.iter().min()?;
                vs.iter().map(|v| (v - mn).abs()).max()
            })
            .max()
            .unwrap_or(0)
            .max(
                coord_dims
                    .iter()
                    .filter_map(|&d| {
                        let idx = usize::try_from(d).ok()?;
                        let vs = coord_ints(f1, idx)?;
                        let mn = *vs.iter().min()?;
                        vs.iter().map(|v| (v - mn).abs()).max()
                    })
                    .max()
                    .unwrap_or(0),
            )
            .min(max_b.max(0));
        let mut found: Option<Vec<i64>> = None;
        'search: for m00 in -bound..=bound {
            for m01 in -bound..=bound {
                for m10 in -bound..=bound {
                    for m11 in -bound..=bound {
                        if m00 == 1 && m01 == 0 && m10 == 0 && m11 == 1 {
                            continue;
                        }
                        checked += 1;
                        crate::access_trace::note_helper_work(51, 1);
                        let matrix = vec![m00, m01, m10, m11];
                        if let Some(t) = apply_linear_once(f0, &coord_dims, &matrix) {
                            if frames_equal(&t, f1) {
                                found = Some(matrix);
                                break 'search;
                            }
                        }
                    }
                }
            }
        }
        found.map(G::Linear)
    } else {
        None
    };

    // Order-1 inference gave up (no first-pair generator, e.g. an identity
    // f0->f1 whose stream is order-2+). BEFORE flooring, try DIMENSION-GENERIC
    // order-N on the per-pair offset stream — additive: this fires only where
    // order-1 has already failed.
    let Some(g) = g else {
        return order_n_translate_verdict(&frames, &coord_dims, field, robust, projection, ctx)
            .unwrap_or_else(|| unexplained(checked, ctx));
    };

    // --- VERIFY G carries EVERY consecutive presented pair, exactly ---
    let step = |sig: &[Value]| -> Option<Vec<Value>> {
        match &g {
            G::Translate(off) => apply_translate_once(sig, &coord_dims, off),
            G::Linear(m) => apply_linear_once(sig, &coord_dims, m),
        }
    };
    for i in 0..frames.len() - 1 {
        // The order-1 generator fails to carry a pair. This is the FORMER
        // `time_none` floor (an accelerating stream falsifies the single G).
        // Try order-N first (velocity that is itself changing regularly =
        // acceleration/jerk/...); floor only if the stream is not regular.
        let Some(pred) = step(&frames[i]) else {
            return order_n_translate_verdict(&frames, &coord_dims, field, robust, projection, ctx)
                .unwrap_or_else(|| unexplained(checked, ctx));
        };
        if !frames_equal(&pred, &frames[i + 1]) {
            return order_n_translate_verdict(&frames, &coord_dims, field, robust, projection, ctx)
                .unwrap_or_else(|| unexplained(checked, ctx));
        }
    }

    // --- downstream: predict the UNSEEN frame at exponent K = frames.len() ---
    let k = frames.len() as i64;
    let (kind, modulus, matrix, offset): (&str, i64, Vec<i64>, Vec<i64>) = match &g {
        G::Translate(off) => ("translate", 0, Vec::new(), off.clone()),
        G::Linear(m) => ("linear", 0, m.clone(), Vec::new()),
    };
    let predicted =
        apply_generator_k(kind, &coord_dims, f0, modulus, &matrix, &offset, k).unwrap_or_default();

    let offset_out: SmallVec<[Value; 4]> = offset.iter().map(|x| Value::Int(*x)).collect();
    let matrix_out: SmallVec<[Value; 4]> = matrix.iter().map(|x| Value::Int(*x)).collect();
    let coord_out: SmallVec<[Value; 4]> = coord_dims.iter().map(|d| Value::Int(*d)).collect();
    let predicted_out: SmallVec<[Value; 4]> = predicted.into_iter().collect();
    finish(
        Value::Dict(Arc::from(vec![
            (surf("explained"), Value::Bool(true)),
            (surf("kind"), surf(kind)),
            (surf("offset"), Value::Tuple(Arc::new(offset_out))),
            (surf("matrix"), Value::Tuple(Arc::new(matrix_out))),
            (surf("coord_dims"), Value::Tuple(Arc::new(coord_out))),
            (surf("window"), Value::Int(k)),
            (surf("predicted"), Value::Tuple(Arc::new(predicted_out))),
            (surf("checked"), Value::Int(checked)),
            // The exact-equality path is order 1 by definition (a constant
            // generator). `coeffs` is empty here — the descriptor is already
            // whole in offset/matrix. Additive: no existing query reads either.
            (surf("order"), Value::Int(1)),
            (surf("coeffs"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("order_fit"), Value::Int(projection.order_fit)),
            (surf("crossing"), Value::Int(projection.crossing)),
        ])),
        field,
        ctx.interner,
        None,
    )
}

/// Split a codebook's `dim_types` into (coord, predicate, appearance) slot
/// indices. The partition is DECLARED BY THE DATA, never by a hardcoded slot
/// number: `coord:*` are the coordinate slots (as `TimeInfer`/`GenInfer`/
/// `DimInfer` already read them), a slot typed exactly `pred` is the PREDICATE,
/// and EVERYTHING ELSE is APPEARANCE.
fn partition_dims(parts: &[Part]) -> (Vec<usize>, Vec<usize>, Vec<usize>) {
    let Some(dts) = parts.iter().find_map(|p| p.dim_types.as_ref()) else {
        return (Vec::new(), Vec::new(), Vec::new());
    };
    let mut coord = Vec::new();
    let mut pred = Vec::new();
    let mut app = Vec::new();
    for (i, t) in dts.iter().enumerate() {
        if t.starts_with("coord:") {
            coord.push(i);
        } else if t == "pred" {
            pred.push(i);
        } else {
            app.push(i);
        }
    }
    (coord, pred, app)
}

/// Compare two cells by (PREDICATE slots, COORDINATE slots) — APPEARANCE
/// EXCLUDED FROM THE KEY. This is the whole reason the pairing can tolerate an
/// appearance change: `infer_translate_offset` sorts by `cmp_value` over the
/// WHOLE tuple, so a changed appearance slot SCRAMBLES the pairing before the
/// coordinates are ever compared.
fn cmp_support(
    a: &Value,
    b: &Value,
    coord_idxs: &[usize],
    pred_idxs: &[usize],
) -> std::cmp::Ordering {
    let (Value::Tuple(ta) | Value::List(ta), Value::Tuple(tb) | Value::List(tb)) = (a, b) else {
        return cmp_value(a, b);
    };
    for &i in pred_idxs {
        match (ta.get(i), tb.get(i)) {
            (Some(x), Some(y)) => {
                let o = cmp_value(x, y);
                if o != std::cmp::Ordering::Equal {
                    return o;
                }
            }
            (x, y) => return x.is_some().cmp(&y.is_some()),
        }
    }
    for &i in coord_idxs {
        match (ta.get(i), tb.get(i)) {
            (Some(x), Some(y)) => {
                let o = cmp_value(x, y);
                if o != std::cmp::Ordering::Equal {
                    return o;
                }
            }
            (x, y) => return x.is_some().cmp(&y.is_some()),
        }
    }
    std::cmp::Ordering::Equal
}

/// The APPEARANCE-TOLERANT rigidity check on ONE consecutive pair.
///
/// Returns `(offset_ok, appearance_residual, compared, reason)`. `offset` is
/// supplied by the caller for every pair after the first, so ONE offset must
/// carry the WHOLE orbit — exactly as `TimeInfer` requires, and it is what
/// makes a third frame CONSTRAIN rather than decorate.
///
/// `compared` counts the cell pairs actually examined before the verdict, so a
/// refusal is provably A FAILURE AFTER A FULL PASS and not a refusal at a
/// guard. `appearance_residual` is COUNTED AND RETURNED, never compared against
/// anything: it is the second half of the PARTITION, not a tolerance.
fn support_pair(
    f0: &[Value],
    f1: &[Value],
    coord_idxs: &[usize],
    pred_idxs: &[usize],
    app_idxs: &[usize],
    offset: &[i64],
) -> (bool, i64, i64, &'static str) {
    let mut a = f0.to_vec();
    let mut b = f1.to_vec();
    a.sort_by(|x, y| cmp_support(x, y, coord_idxs, pred_idxs));
    b.sort_by(|x, y| cmp_support(x, y, coord_idxs, pred_idxs));
    let read = |rel: &Value, idx: usize| -> Option<i64> {
        let (Value::Tuple(t) | Value::List(t)) = rel else {
            return None;
        };
        match t.get(idx) {
            Some(Value::Int(v)) => Some(*v),
            _ => None,
        }
    };
    let mut resid: i64 = 0;
    let mut compared: i64 = 0;
    for (ra, rb) in a.iter().zip(b.iter()) {
        compared += 1;
        for (j, &idx) in coord_idxs.iter().enumerate() {
            let (Some(x), Some(y)) = (read(ra, idx), read(rb, idx)) else {
                return (false, resid, compared, "non_integer_coord");
            };
            if y - x != offset[j] {
                return (false, resid, compared, "offset");
            }
        }
        let (Value::Tuple(ta) | Value::List(ta), Value::Tuple(tb) | Value::List(tb)) = (ra, rb)
        else {
            return (false, resid, compared, "not_a_cell");
        };
        if ta.len() != tb.len() {
            return (false, resid, compared, "arity");
        }
        // the PREDICATE slot is STILL required byte-identical — a predicate is
        // never transformable, the arc's standing rule.
        for &idx in pred_idxs {
            match (ta.get(idx), tb.get(idx)) {
                (Some(x), Some(y)) if cmp_value(x, y) == std::cmp::Ordering::Equal => {}
                _ => return (false, resid, compared, "predicate"),
            }
        }
        // APPEARANCE: counted, NOT compared against. No branch reads `resid`.
        for &idx in app_idxs {
            match (ta.get(idx), tb.get(idx)) {
                (Some(x), Some(y)) if cmp_value(x, y) == std::cmp::Ordering::Equal => {}
                _ => {
                    resid += 1;
                    break;
                }
            }
        }
    }
    (true, resid, compared, "ok")
}

/// Evaluate `SupportInfer` — `TimeInfer`'s rigidity core with the APPEARANCE
/// SLOTS TAKEN OUT OF THE VERDICT AND REPORTED SEPARATELY.
///
/// **WHY IT EXISTS, MEASURED NOT ASSERTED.** The pixel-seam rung (104000–104999)
/// isolated `TimeInfer`'s deficit on real photometry to ONE requirement: every
/// non-coordinate slot must be BYTE-IDENTICAL across frames (R6). Across 3 200
/// real-photometry conditions `live & explained = 0` at EVERY quantization from
/// 2 to 256 levels, while `dead & explained = 1 936` — *the seam succeeded
/// exactly where it saw nothing changing.* With a ground-truth support, every
/// one of the 600 refusals was R6 with no other requirement firing; strip the
/// appearance slot from the IDENTICAL stimuli and they explain 1 400 / 1 400,
/// including 600 / 600 live.
///
/// **THIS IS A PARTITION, NOT A TOLERANCE — and the distinction is the whole
/// design.** There is no slack parameter here and nowhere to put one: every
/// clause is exact integer equality. `dim_types` already declares which slots
/// are coordinates; this Term reads the SAME declaration for the predicate
/// (`pred`) and treats EVERYTHING ELSE as appearance. Coordinates must be an
/// exact uniform integer translate; the predicate must be byte-identical; the
/// appearance slots are COUNTED into `appearance_residual` and never compared
/// against anything. The appearance verdict is not destroyed — it is MOVED, out
/// of the rigidity verdict and into a field a rule can read as a SECOND verdict.
///
/// **IT REMAINS A COMPARISON, WHICH IS WHY IT CAN STILL REFUSE.** The standing
/// law of this tree is *a comparison can be false, a selection cannot* — every
/// mechanism here that refuses well decides by exact equality against a
/// reconstruction, and everything that cannot refuse selects a best from a set.
/// `SupportInfer` does not select an offset: the offset is READ from the first
/// paired cell and then VERIFIED across every cell of every consecutive pair, so
/// a wrong offset is a REFUSAL and not a lower-scoring winner. `GapAbduce`'s
/// disease was that two endpoints and one free generator always fit; here ONE
/// offset must carry the WHOLE orbit, so a third frame CONSTRAINS.
///
/// **WHAT IT CANNOT DO, STATED WHERE THE MECHANISM IS.** (1) TRANSLATE ONLY —
/// there is no linear-map fallback, deliberately: `TimeInfer` keeps that and
/// this Term is the appearance-partitioned twin of its translate path alone.
/// (2) It is DEAD ON A DENSE BOUNDED RASTER, and not for R6's reason: a full
/// raster's coordinate SET is translation-INVARIANT, so the offset reads
/// `(0, 0)`, and the identity exclusion below refuses it. Appearance tolerance
/// does not rescue a raster — **the support must MOVE WITH THE SCENE**, and
/// where it comes from without circularity is a different question from this
/// one. (3) An acceptance asserts only that THE SUPPORT translated rigidly; how
/// much that is worth is bounded by how much shape information the support
/// carries, which is a property of the SUPPLIER and not of this Term.
///
/// Output Dict: `explained` / `kind` (`"translate"`) / `offset` / `coord_dims` /
/// `window` (frames seen) / **`appearance_residual`** (paired cells whose
/// appearance slots differ, summed over pairs) / `appearance_identical`
/// (`residual == 0` — what R6 would have demanded) / **`compared`** (cell pairs
/// actually examined, so a refusal is provably a failure after a full pass) /
/// `reason`. Integer / in-frame only, exactly as `TimeInfer`.
pub(crate) fn eval_support_infer(
    arena: &TermArena,
    sequence_idx: TermIdx,
    codebook_type: Sym,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_SUPPORT_INFER);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    let (coord_idxs, pred_idxs, app_idxs) = partition_dims(&parts);

    let seq_val = evaluate(arena, sequence_idx, env, ctx);
    let frames: Vec<Vec<Value>> = match &seq_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => seq_val
            .iter()
            .map(|f| match f {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
                    f.iter().cloned().collect()
                }
                _ => Vec::new(),
            })
            .collect(),
        _ => Vec::new(),
    };

    let refused = |reason: &str, resid: i64, compared: i64, ctx: &mut EvalCtx| -> Value {
        finish(
            Value::Dict(Arc::from(vec![
                (surf("explained"), Value::Bool(false)),
                (surf("kind"), Value::None),
                (surf("offset"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("coord_dims"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("window"), Value::Int(0)),
                (surf("appearance_residual"), Value::Int(resid)),
                (surf("appearance_identical"), Value::Bool(resid == 0)),
                (surf("compared"), Value::Int(compared)),
                (surf("reason"), surf(reason)),
            ])),
            field,
            ctx.interner,
            None,
        )
    };

    if frames.len() < 2 {
        return refused("few_frames", 0, 0, ctx);
    }
    if coord_idxs.is_empty() {
        return refused("no_coord_dims", 0, 0, ctx);
    }
    if frames.iter().any(|f| f.is_empty()) {
        return refused("empty_frame", 0, 0, ctx);
    }
    if frames.iter().any(|f| f.len() != frames[0].len()) {
        return refused("cardinality", 0, 0, ctx);
    }

    // The offset is READ from the first paired cell of the first pair, then
    // VERIFIED — there is nothing to search, and nothing to select between.
    let mut a0 = frames[0].clone();
    let mut b0 = frames[1].clone();
    a0.sort_by(|x, y| cmp_support(x, y, &coord_idxs, &pred_idxs));
    b0.sort_by(|x, y| cmp_support(x, y, &coord_idxs, &pred_idxs));
    let read = |rel: &Value, idx: usize| -> Option<i64> {
        let (Value::Tuple(t) | Value::List(t)) = rel else {
            return None;
        };
        match t.get(idx) {
            Some(Value::Int(v)) => Some(*v),
            _ => None,
        }
    };
    let mut offset: Vec<i64> = Vec::with_capacity(coord_idxs.len());
    for &idx in &coord_idxs {
        let (Some(x), Some(y)) = (read(&a0[0], idx), read(&b0[0], idx)) else {
            return refused("non_integer_coord", 0, 0, ctx);
        };
        offset.push(y - x);
    }

    let mut resid_total: i64 = 0;
    let mut compared_total: i64 = 0;
    for i in 0..frames.len() - 1 {
        let (ok, resid, compared, reason) = support_pair(
            &frames[i],
            &frames[i + 1],
            &coord_idxs,
            &pred_idxs,
            &app_idxs,
            &offset,
        );
        resid_total += resid;
        compared_total += compared;
        if !ok {
            return refused(reason, resid_total, compared_total, ctx);
        }
    }
    // The identity is excluded — a still pattern is not a motion. This is the
    // clause a DENSE BOUNDED RASTER dies on, and it is NOT R6's clause.
    if offset.iter().all(|&x| x == 0) {
        return refused("identity", resid_total, compared_total, ctx);
    }

    let offset_out: SmallVec<[Value; 4]> = offset.iter().map(|x| Value::Int(*x)).collect();
    let coord_out: SmallVec<[Value; 4]> =
        coord_idxs.iter().map(|d| Value::Int(*d as i64)).collect();
    finish(
        Value::Dict(Arc::from(vec![
            (surf("explained"), Value::Bool(true)),
            (surf("kind"), surf("translate")),
            (surf("offset"), Value::Tuple(Arc::new(offset_out))),
            (surf("coord_dims"), Value::Tuple(Arc::new(coord_out))),
            (surf("window"), Value::Int(frames.len() as i64)),
            (surf("appearance_residual"), Value::Int(resid_total)),
            (surf("appearance_identical"), Value::Bool(resid_total == 0)),
            (surf("compared"), Value::Int(compared_total)),
            (surf("reason"), surf("ok")),
        ])),
        field,
        ctx.interner,
        None,
    )
}

/// Evaluate `BlinkBridge` — THE BLINK: a temporal hole bridged by grounding, the
/// TEMPORAL TWIN of the blind spot (`vision_ground`) and the COMPOSITION of the
/// grounded-field fill with `TimeInfer`'s transition generator.
///
/// The blind spot proved vision is a grounded FIELD: a SPATIAL hole (no data) is
/// filled from the surround's belief. A BLINK is the same hole in TIME: a run of
/// frames with NO visual input (`[..., EMPTY, EMPTY, ...]`). Its "surround" is the
/// TEMPORAL neighbourhood, and its grounding is the transition generator `G` that
/// `TimeInfer` infers from the pre-blink orbit — CONTINUED through the gap. The
/// belief during blink tick `t` is `G^t(f0)` (the generator continued from the
/// last-seen orbit), NOT the frozen last frame (persistence) and NOT an invented
/// value (confabulation). When data RESUMES, the continued belief is CONFIRMED
/// (the percept was invisible/continuous) or REVISED where reality diverges from
/// it (change blindness: a change made DURING the blink is bridged over by the
/// prediction and detected only on data return).
///
/// The input `sequence` is `[prefix..(visible), gap..(EMPTY = blink), resumed..
/// (visible)]`. `G` is inferred from the first prefix pair (translate preferred,
/// else the SAME integer 2×2 enumerate-and-test as `TimeInfer`/`GenInfer`) and
/// VERIFIED by EXACT equality across every prefix pair; `confirm_run` is the count
/// of confirming consecutive transitions in the prefix — the TEMPORAL SUPPORT, the
/// blind spot's "surround support" in time. The bridge/hold/decay DECISION lives
/// in the seed rule (`blink_bridge.json`), which reads these fields: a gap within
/// the evidence horizon (`gap <= confirm_run` — RELATIVE decay, no fixed constant)
/// under a consistent motion (`explained`) is bridged; a prefix that is NOT an
/// orbit (accelerating / shuffled — `explained=false`) grounds NOTHING (held open,
/// the anti-confabulation gate); a gap beyond the horizon is held open (the gap is
/// perceived — the temporal analog of "large spatial hole not bridged"). Integer
/// lattice / in-frame only, exactly as `TimeInfer`; continuous motion is
/// cross-frame and deferred (the frame/continuum invariant).
///
/// `field` selects: `explained` (bool — prefix is a clean orbit) / `kind`
/// (`translate`/`linear`) / `offset` / `matrix` / `coord_dims` / `prefix_len` /
/// `confirm_run` (Int — temporal support) / `gap` (Int — blink length) / `bridged`
/// (Tuple of frames — `G^t(f0)` for each blink tick, the CONTINUED belief) /
/// `frozen` (Tuple of frames — the last visible frame repeated, the PERSISTENCE
/// baseline the bridge must BEAT) / `diverged_at` (Int — the first RESUMED tick
/// whose observation != the continued belief, -1 if none) / `resume_ok` (bool —
/// resumed frames all matched the continued belief ⇒ invisible/confirmed) /
/// `checked`. `dim_types` (coord slots) read from the first `codebook_type` part.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_motion_energy(
    arena: &TermArena,
    sequence_idx: TermIdx,
    height: i64,
    width: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    // ---- read the raster sequence -----------------------------------------
    // `sequence` evaluates to a Tuple of frames; each frame is a Tuple of
    // pixel luminances, row-major, length == height*width. Consumes the RAW
    // BOUNDED RASTER directly — no figure/ground split (the abduction family
    // could not do this; it needed a supplied segmentation).
    let seq_val = evaluate(arena, sequence_idx, env, ctx);
    let frames: Vec<Vec<f64>> = match &seq_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => seq_val
            .iter()
            .map(|f| match f {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => f
                    .iter()
                    .map(|p| match p {
                        Value::Int(v) => *v as f64,
                        Value::Float(v) => *v,
                        Value::Bool(b) => {
                            if *b {
                                1.0
                            } else {
                                0.0
                            }
                        }
                        _ => 0.0,
                    })
                    .collect(),
                _ => Vec::new(),
            })
            .collect(),
        _ => Vec::new(),
    };

    let h = height.max(0) as usize;
    let w = width.max(0) as usize;
    let t = frames.len();

    let readouts = motion_energy_spectrum(&frames, h, w, t);
    let dict: Vec<(Value, Value)> = readouts
        .iter()
        .map(|(k, v)| (surf(k), Value::Float(*v)))
        .collect();
    finish(Value::Dict(Arc::from(dict)), field, ctx.interner, None)
}

/// MOTION IS ORIENTATION IN SPACE–TIME, read as spectral INTERFERENCE
/// (Adelson & Bergen 1985 motion energy). Reduce the raster to the horizontal
/// space–time signal `s(x, ti) = Σ_row frame[row, x]` (this arc is
/// horizontal-displacement-only; the vertical is collapsed — a declared scope
/// limit, NOT a tuned parameter), take the joint 2‑D DFT over `(x, ti)`, and
/// partition the power `|S(ωx, ωt)|²` by the SIGN of the spatiotemporal
/// orientation:
///
/// * a rightward pattern `f(x − v·ti)`, v>0, has energy on the line
///   `ωt = −v·ωx`, i.e. `ωx` and `ωt` of OPPOSITE sign → `right`;
/// * `left` is the same-sign quadrants;
/// * `ωt == 0` is `static` (no temporal change); `ωx == 0`, `ωt ≠ 0` is
///   `flicker` (spatially uniform temporal change); `(0,0)` is `dc`.
///
/// **§13: there is NO number in this readout.** The partition is exact sign /
/// equality tests on integer DFT indices — nowhere to put a threshold. The
/// grid is fixed entirely by `w` and `t`; the continuous structure (phase, the
/// real-valued energy) lives in the DFT, which is the CROSS-FRAME MAP (the
/// spatial frame is the integer pixel lattice, the spectral frame is
/// integer-indexed bins — the frame/continuum invariant). **Nyquist cancels by
/// itself**: at `ωt = T/2`, `−ωt ≡ ωt`, so for a real signal
/// `P(ωx, Nyq) = P(−ωx, Nyq)` — the Nyquist temporal row is symmetric in `ωx`
/// and its power falls EQUALLY into `right` and `left`, so the OPPONENT `right
/// − left` receives zero net Nyquist contribution WITHOUT any hand-exclusion.
/// A two-frame sequence (ISI=0, D=1) has only DC + Nyquist temporal frequencies
/// ⇒ its whole directional signal is at Nyquist ⇒ `opponent == 0`, forced by
/// the temporal sampling limit, not by a chosen constant. That is why a single
/// mechanism here can make ISI=0 the WORST cell rather than the best.
///
/// Default OFF by non-existence: no seed binds this Term, so every committed
/// result reproduces byte-identically (§9).
fn motion_energy_spectrum(
    frames: &[Vec<f64>],
    h: usize,
    w: usize,
    t: usize,
) -> Vec<(&'static str, f64)> {
    let zero = || {
        vec![
            ("right", 0.0),
            ("left", 0.0),
            ("static", 0.0),
            ("flicker", 0.0),
            ("dc", 0.0),
            ("total_ac", 0.0),
            ("opponent", 0.0),
            ("opp_frac", 0.0),
            ("motion_frac", 0.0),
            ("width", 0.0),
            ("frames", 0.0),
        ]
    };
    if t < 2 || w == 0 || h == 0 {
        return zero();
    }
    if frames.iter().any(|f| f.len() != h * w) {
        return zero();
    }

    // Horizontal space–time signal: sum each frame down its columns.
    // s[ti][x] = Σ_row frame[row*w + x].
    let mut s = vec![vec![0.0f64; w]; t];
    for (ti, f) in frames.iter().enumerate() {
        for row in 0..h {
            let base = row * w;
            for x in 0..w {
                s[ti][x] += f[base + x];
            }
        }
    }

    // Joint 2-D DFT over (x, ti), computed separably with a naive O(N²)
    // transform (sizes here are small; correctness over speed). First the
    // temporal DFT for every x, then the spatial DFT for every ωt.
    let pi = std::f64::consts::PI;
    // Temporal DFT: A[kt][x] = Σ_ti s[ti][x] exp(-i 2π kt ti / t).
    let mut are = vec![vec![0.0f64; w]; t];
    let mut aim = vec![vec![0.0f64; w]; t];
    for kt in 0..t {
        for ti in 0..t {
            let ang = -2.0 * pi * (kt as f64) * (ti as f64) / (t as f64);
            let (si, co) = ang.sin_cos();
            for x in 0..w {
                are[kt][x] += s[ti][x] * co;
                aim[kt][x] += s[ti][x] * si;
            }
        }
    }
    // Spatial DFT: S[kt][kx] = Σ_x A[kt][x] exp(-i 2π kx x / w).
    // Accumulate power directly per (kx, kt) bin.
    let signed = |k: usize, n: usize| -> i64 {
        // integer signed frequency: k if 2k <= n else k - n
        if 2 * k <= n {
            k as i64
        } else {
            k as i64 - n as i64
        }
    };
    let (mut right, mut left, mut stat, mut flick, mut dc) = (0.0, 0.0, 0.0, 0.0, 0.0);
    for kt in 0..t {
        let ft = signed(kt, t);
        for kx in 0..w {
            let ang0 = -2.0 * pi * (kx as f64) / (w as f64);
            let mut re = 0.0;
            let mut im = 0.0;
            for x in 0..w {
                let ang = ang0 * (x as f64);
                let (si, co) = ang.sin_cos();
                // (are + i aim) * (co + i si)
                re += are[kt][x] * co - aim[kt][x] * si;
                im += are[kt][x] * si + aim[kt][x] * co;
            }
            let p = re * re + im * im;
            let fx = signed(kx, w);
            if fx == 0 && ft == 0 {
                dc += p;
            } else if ft == 0 {
                stat += p;
            } else if fx == 0 {
                flick += p;
            } else if (fx > 0) == (ft > 0) {
                left += p;
            } else {
                right += p;
            }
        }
    }
    let total_ac = right + left + stat + flick;
    let opponent = right - left;
    let opp_frac = if total_ac > 0.0 {
        opponent / total_ac
    } else {
        0.0
    };
    let motion_frac = if total_ac > 0.0 {
        (right + left) / total_ac
    } else {
        0.0
    };
    vec![
        ("right", right),
        ("left", left),
        ("static", stat),
        ("flicker", flick),
        ("dc", dc),
        ("total_ac", total_ac),
        ("opponent", opponent),
        ("opp_frac", opp_frac),
        ("motion_frac", motion_frac),
        ("width", w as f64),
        ("frames", t as f64),
    ]
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_blink_bridge(
    arena: &TermArena,
    sequence_idx: TermIdx,
    codebook_type: Sym,
    max_b: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_BLINK_BRIDGE);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    let coord_dims: Vec<i64> = parts
        .iter()
        .find_map(|p| p.dim_types.as_ref())
        .map(|dts| {
            dts.iter()
                .enumerate()
                .filter(|(_, t)| t.starts_with("coord:"))
                .map(|(i, _)| i as i64)
                .collect()
        })
        .unwrap_or_default();

    let seq_val = evaluate(arena, sequence_idx, env, ctx);
    let frames: Vec<Vec<Value>> = match &seq_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => seq_val
            .iter()
            .map(|f| match f {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
                    f.iter().cloned().collect()
                }
                _ => Vec::new(),
            })
            .collect(),
        _ => Vec::new(),
    };

    // === CONFABULATE BY DEFAULT (the creator's correction) =====================
    // Perception FILLS a temporal hole with a best-guess; grounding only
    // CONSTRAINS that guess. There is NO "hold open" — an ungrounded blink still
    // confabulates (the seed of hallucination / sensory-deprivation filling); it
    // is merely UNCONSTRAINED and LOW-CONFIDENCE. Predictive coding: the
    // prediction stands where there is no data to compute a residual (that IS
    // change blindness), and where nothing pins it the prediction is a wild guess
    // (that IS hallucination). DISCOVERY (minting a permanent dimension,
    // `time_axis`) stays conservative; PERCEPTION (this bridge) is liberal.

    // --- structure: leading VISIBLE prefix, GAP (empty = blink), then resume ---
    let mut prefix_len = 0usize;
    while prefix_len < frames.len() && !frames[prefix_len].is_empty() {
        prefix_len += 1;
    }
    let mut gap = 0usize;
    while prefix_len + gap < frames.len() && frames[prefix_len + gap].is_empty() {
        gap += 1;
    }
    let resume_start = prefix_len + gap;

    let mut checked: i64 = 0;
    let mut explained = false;
    let mut confirm_run: i64 = 0;
    let mut kind: &str = "freeze";
    let mut offset: Vec<i64> = Vec::new();
    let mut matrix: Vec<i64> = Vec::new();

    // The FREEZE source: the last visible frame (persistence = the zero-velocity
    // best-guess). It is BOTH the persistence baseline `frozen` AND the
    // unconstrained confabulation the bridge falls back to when nothing pins it.
    let last: Option<Vec<Value>> = if prefix_len >= 1 {
        Some(frames[prefix_len - 1].clone())
    } else {
        None
    };

    // --- infer + VERIFY G from the prefix (needs >=2 visible frames + coords) ---
    if prefix_len >= 2 && !coord_dims.is_empty() {
        enum G {
            Translate(Vec<i64>),
            Linear(Vec<i64>),
        }
        let f0 = &frames[0];
        let f1 = &frames[1];
        let g: Option<G> = if let Some(off) = infer_translate_offset(f0, f1, &coord_dims) {
            if off.iter().all(|&x| x == 0) {
                None
            } else {
                Some(G::Translate(off))
            }
        } else if coord_dims.len() == 2 {
            let bound: i64 = coord_dims
                .iter()
                .filter_map(|&d| {
                    let idx = usize::try_from(d).ok()?;
                    let vs = coord_ints(f0, idx)?;
                    let mn = *vs.iter().min()?;
                    vs.iter().map(|v| (v - mn).abs()).max()
                })
                .max()
                .unwrap_or(0)
                .max(
                    coord_dims
                        .iter()
                        .filter_map(|&d| {
                            let idx = usize::try_from(d).ok()?;
                            let vs = coord_ints(f1, idx)?;
                            let mn = *vs.iter().min()?;
                            vs.iter().map(|v| (v - mn).abs()).max()
                        })
                        .max()
                        .unwrap_or(0),
                )
                .min(max_b.max(0));
            let mut found: Option<Vec<i64>> = None;
            'search: for m00 in -bound..=bound {
                for m01 in -bound..=bound {
                    for m10 in -bound..=bound {
                        for m11 in -bound..=bound {
                            if m00 == 1 && m01 == 0 && m10 == 0 && m11 == 1 {
                                continue;
                            }
                            checked += 1;
                            crate::access_trace::note_helper_work(51, 1);
                            let m = vec![m00, m01, m10, m11];
                            if let Some(t) = apply_linear_once(f0, &coord_dims, &m) {
                                if frames_equal(&t, f1) {
                                    found = Some(m);
                                    break 'search;
                                }
                            }
                        }
                    }
                }
            }
            found.map(G::Linear)
        } else {
            None
        };

        if let Some(g) = &g {
            let step = |sig: &[Value]| -> Option<Vec<Value>> {
                match g {
                    G::Translate(off) => apply_translate_once(sig, &coord_dims, off),
                    G::Linear(m) => apply_linear_once(sig, &coord_dims, m),
                }
            };
            let mut ok = true;
            for i in 0..prefix_len - 1 {
                match step(&frames[i]) {
                    Some(pred) if frames_equal(&pred, &frames[i + 1]) => confirm_run += 1,
                    _ => {
                        ok = false;
                        break;
                    }
                }
            }
            explained = ok; // a SINGLE generator carried the WHOLE prefix
            match g {
                G::Translate(off) => {
                    kind = "translate";
                    offset = off.clone();
                }
                G::Linear(m) => {
                    kind = "linear";
                    matrix = m.clone();
                }
            }
        }
    }
    // Only a generator that carried the whole prefix earns its descriptor; an
    // unconstrained guess reports the freeze.
    if !explained {
        kind = "freeze";
        offset.clear();
        matrix.clear();
    }
    let f0v: Vec<Value> = if prefix_len >= 1 {
        frames[0].clone()
    } else {
        Vec::new()
    };

    // --- the GUESS: continued generator if CONSTRAINED, else the freeze default ---
    let guess_at = |t: i64| -> Vec<Value> {
        if explained {
            apply_generator_k(kind, &coord_dims, &f0v, 0, &matrix, &offset, t).unwrap_or_default()
        } else if let Some(last) = &last {
            last.clone()
        } else {
            Vec::new()
        }
    };
    let mut bridged: SmallVec<[Value; 4]> = SmallVec::new();
    let mut frozen: SmallVec<[Value; 4]> = SmallVec::new();
    for j in 0..gap {
        let t = (prefix_len + j) as i64;
        bridged.push(Value::Tuple(Arc::new(guess_at(t).into_iter().collect())));
        if let Some(last) = &last {
            frozen.push(Value::Tuple(Arc::new(last.iter().cloned().collect())));
        }
    }

    // --- CONFIDENCE falls out of SUPPORT (§13): the fraction of the
    //     extrapolation backed by CONFIRMED evidence. support = confirm_run iff
    //     the guess is constrained, else 0 (an honest "guessing blind"). RELATIVE
    //     — no constant; it DECAYS with the gap (extrapolating further, blind). ---
    let support = if explained { confirm_run } else { 0 };
    let confidence: f64 = if gap == 0 {
        if support > 0 {
            1.0
        } else {
            0.0
        }
    } else {
        support as f64 / (support as f64 + gap as f64)
    };

    // --- RESUME: first tick whose OBSERVATION diverges from the confabulated
    //     guess (change blindness's signal); `correction` = the symmetric-diff
    //     cell count at that tick, the perceptible "jump". ---
    let mut diverged_at: i64 = -1;
    let mut correction: i64 = 0;
    let mut had_resume = false;
    for i in resume_start..frames.len() {
        if frames[i].is_empty() {
            continue;
        }
        had_resume = true;
        let guess = guess_at(i as i64);
        if !frames_equal(&guess, &frames[i]) {
            diverged_at = i as i64;
            correction = frames_symdiff(&guess, &frames[i]);
            break;
        }
    }
    let resume_ok = had_resume && diverged_at < 0;

    let offset_out: SmallVec<[Value; 4]> = offset.iter().map(|x| Value::Int(*x)).collect();
    let matrix_out: SmallVec<[Value; 4]> = matrix.iter().map(|x| Value::Int(*x)).collect();
    let coord_out: SmallVec<[Value; 4]> = coord_dims.iter().map(|d| Value::Int(*d)).collect();
    finish(
        Value::Dict(Arc::from(vec![
            (surf("explained"), Value::Bool(explained)),
            (surf("constrained"), Value::Bool(explained)),
            (surf("confidence"), Value::Float(confidence)),
            (surf("kind"), surf(kind)),
            (surf("offset"), Value::Tuple(Arc::new(offset_out))),
            (surf("matrix"), Value::Tuple(Arc::new(matrix_out))),
            (surf("coord_dims"), Value::Tuple(Arc::new(coord_out))),
            (surf("prefix_len"), Value::Int(prefix_len as i64)),
            (surf("confirm_run"), Value::Int(confirm_run)),
            (surf("gap"), Value::Int(gap as i64)),
            (surf("bridged"), Value::Tuple(Arc::new(bridged))),
            (surf("frozen"), Value::Tuple(Arc::new(frozen))),
            (surf("diverged_at"), Value::Int(diverged_at)),
            (surf("correction"), Value::Int(correction)),
            (surf("resume_ok"), Value::Bool(resume_ok)),
            (surf("checked"), Value::Int(checked)),
        ])),
        field,
        ctx.interner,
        None,
    )
}

/// Multiset symmetric-difference cell count between two frames — the magnitude of
/// the perceptible CORRECTION when a confabulated guess meets reality on resume.
fn frames_symdiff(a: &[Value], b: &[Value]) -> i64 {
    let mut sa = a.to_vec();
    let mut sb = b.to_vec();
    sa.sort_by(cmp_value);
    sb.sort_by(cmp_value);
    let (mut i, mut j, mut d) = (0usize, 0usize, 0i64);
    while i < sa.len() && j < sb.len() {
        match cmp_value(&sa[i], &sb[j]) {
            std::cmp::Ordering::Equal => {
                i += 1;
                j += 1;
            }
            std::cmp::Ordering::Less => {
                d += 1;
                i += 1;
            }
            std::cmp::Ordering::Greater => {
                d += 1;
                j += 1;
            }
        }
    }
    d + (sa.len() - i) as i64 + (sb.len() - j) as i64
}

/// Evaluate `GapAbduce` — THE ENDPOINT-ABDUCED GENERATOR.
///
/// The timephi rung measured that every temporal mechanism in this tree infers
/// its generator `G` from a CONSECUTIVE VISIBLE PAIR and then EXTRAPOLATES, and
/// that a phi stimulus supplies exactly ONE pre-gap sample — so `BlinkBridge`
/// correctly FREEZES at `prefix_len == 1` (confidence 0.00, resume correction 32
/// = the dot's 16 cells counted twice). Its registered null-reading was
/// **CONTINUATION, NEVER INTERPOLATION**, and it named the missing operator
/// exactly: solve `G^(gap+1)(f_before) = f_after` for `G`.
///
/// This is that operator. It reads **ONLY THE TWO ENDPOINTS** of the gap —
/// `f_before` = the last visible frame before it, `f_after` = the first visible
/// frame after it. Nothing between them, and nothing before `f_before`, enters
/// the abduction; that is what makes it INTERPOLATION, and why it works where
/// there is no consecutive pair to continue from.
///
/// **THE DIVISIBILITY TEST — §13 BY CONSTRUCTION.** The total displacement `D`
/// comes from the UNMODIFIED `infer_translate_offset` (the same rigidity
/// criterion `TimeInfer` uses: equal cardinality, one uniform integer shift,
/// byte-identical non-coord slots). The abduced generator is `D / steps`, and it
/// is admissible **iff `D[i] % steps == 0` on every coordinate slot**. That is
/// exact integer arithmetic — there is no tolerance in it and nowhere to put
/// one, which is the strongest form of §13 compliance available: not a number
/// that falls out, but NO NUMBER AT ALL. `D == 0` is the identity and is
/// refused, matching `TimeInfer`'s exclusion of the still pattern.
///
/// **THE SCOPE LIMIT, STATED WHERE THE MECHANISM IS.** Any two same-shape
/// figures ARE rigid translates of one another, so on the translate class the
/// ONLY constraint this operator applies is divisibility — and the acceptance
/// rate on independent random endpoints is therefore `~1/steps`, NOT zero.
/// `TimeInfer` at N>=3 refuses ACCEL and SHUFFLE 18/18 because a THIRD frame
/// CONSTRAINS the orbit. Two endpoints and one free generator always fit.
/// **Interpolation is cheap for exactly the reason continuation is safe.**
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_gap_abduce(
    arena: &TermArena,
    sequence_idx: TermIdx,
    codebook_type: Sym,
    max_b: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_GAP_ABDUCE);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    let coord_dims: Vec<i64> = parts
        .iter()
        .find_map(|p| p.dim_types.as_ref())
        .map(|dts| {
            dts.iter()
                .enumerate()
                .filter(|(_, t)| t.starts_with("coord:"))
                .map(|(i, _)| i as i64)
                .collect()
        })
        .unwrap_or_default();

    let seq_val = evaluate(arena, sequence_idx, env, ctx);
    let frames: Vec<Vec<Value>> = match &seq_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => seq_val
            .iter()
            .map(|f| match f {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
                    f.iter().cloned().collect()
                }
                _ => Vec::new(),
            })
            .collect(),
        _ => Vec::new(),
    };

    // The measured endpoint displacement is carried THROUGH a refusal: an
    // indivisible `D` is a NUMBER, not an absence, and a null that cannot say
    // WHY is a shrug. (`finish` SELECTS the requested field, so `total` must be
    // in the Dict BEFORE it is called — patching afterwards silently does
    // nothing on every call that asks for `total`, which is exactly the bug the
    // mechanism test caught here.)
    let refused = |reason: &str,
                   gap: i64,
                   steps: i64,
                   prefix_len: i64,
                   checked: i64,
                   total: &[i64],
                   ctx: &mut EvalCtx|
     -> Value {
        let total_out: SmallVec<[Value; 4]> = total.iter().map(|x| Value::Int(*x)).collect();
        finish(
            Value::Dict(Arc::from(vec![
                (surf("explained"), Value::Bool(false)),
                (surf("kind"), Value::None),
                (surf("offset"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("matrix"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("coord_dims"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("gap"), Value::Int(gap)),
                (surf("steps"), Value::Int(steps)),
                (surf("total"), Value::Tuple(Arc::new(total_out))),
                (surf("divisible"), Value::Bool(false)),
                (surf("reason"), surf(reason)),
                (surf("bridged"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("closes"), Value::Bool(false)),
                (surf("correction"), Value::Int(-1)),
                (surf("prefix_len"), Value::Int(prefix_len)),
                (surf("checked"), Value::Int(checked)),
            ])),
            field,
            ctx.interner,
            None,
        )
    };

    // --- structure: leading VISIBLE prefix, a run of EMPTY (the gap), resume ---
    // Identical to `BlinkBridge`'s split, so the two Terms consume the SAME
    // stimulus encoding and their verdicts are directly comparable.
    let mut prefix_len = 0usize;
    while prefix_len < frames.len() && !frames[prefix_len].is_empty() {
        prefix_len += 1;
    }
    let mut gap = 0usize;
    while prefix_len + gap < frames.len() && frames[prefix_len + gap].is_empty() {
        gap += 1;
    }
    let mut resume_start = prefix_len + gap;

    // `gap == 0` — an ALL-VISIBLE sequence, no EMPTY run — is ADMISSIBLE and is
    // the DEGENERATE case: the boundary falls before the LAST frame, so the
    // endpoints are the final consecutive pair and `steps == 1`. This is the
    // ISI = 0 condition of the phi stimulus, and the abduction there reduces
    // EXACTLY to the two-frame reading `TimeInfer` already explains vacuously
    // (9/9, measured by the timephi rung). Keeping it admissible is what makes
    // the ISI curve's zero point measurable on the SAME operator as the rest of
    // the curve, rather than a different mechanism spliced in at one end.
    if gap == 0 && resume_start >= frames.len() && frames.len() >= 2 {
        prefix_len = frames.len() - 1;
        resume_start = frames.len() - 1;
    }

    // Both banks must exist.
    if prefix_len == 0
        || resume_start >= frames.len()
        || frames[resume_start].is_empty()
        || coord_dims.is_empty()
    {
        return refused(
            "no_gap_structure",
            gap as i64,
            gap as i64 + 1,
            prefix_len as i64,
            0,
            &[],
            ctx,
        );
    }
    let steps = gap as i64 + 1;
    let f_before = frames[prefix_len - 1].clone();
    let f_after = frames[resume_start].clone();

    let mut checked: i64 = 0;
    enum G {
        Translate(Vec<i64>),
        Linear(Vec<i64>),
    }

    // --- THE TRANSLATE ABDUCTION: read D, then DIVIDE. No threshold. ---
    let mut total: Vec<i64> = Vec::new();
    let mut divisible = false;
    let mut reason = "not_rigid";
    let mut g: Option<G> = None;

    if let Some(d) = infer_translate_offset(&f_before, &f_after, &coord_dims) {
        total = d.clone();
        if d.iter().all(|&x| x == 0) {
            // The identity: `f_after` is `f_before`. A still figure is not a
            // motion — the same exclusion `TimeInfer` applies at source.
            reason = "identity";
        } else if d.iter().all(|&x| x % steps == 0) {
            divisible = true;
            reason = "ok";
            g = Some(G::Translate(d.iter().map(|&x| x / steps).collect()));
        } else {
            reason = "indivisible";
        }
    }

    // --- THE LINEAR FALLBACK: a `steps`-th root in the integer 2x2 class.
    //     The same enumerate-and-test as `TimeInfer`/`GenInfer`, over the same
    //     data-derived bound, accepted only on EXACT equality after `steps`
    //     applications. Tried only where the translate abduction did not land. ---
    if g.is_none() && reason != "identity" && coord_dims.len() == 2 {
        let bound: i64 = coord_dims
            .iter()
            .filter_map(|&d| {
                let idx = usize::try_from(d).ok()?;
                let vs = coord_ints(&f_before, idx)?;
                let mn = *vs.iter().min()?;
                vs.iter().map(|v| (v - mn).abs()).max()
            })
            .max()
            .unwrap_or(0)
            .max(
                coord_dims
                    .iter()
                    .filter_map(|&d| {
                        let idx = usize::try_from(d).ok()?;
                        let vs = coord_ints(&f_after, idx)?;
                        let mn = *vs.iter().min()?;
                        vs.iter().map(|v| (v - mn).abs()).max()
                    })
                    .max()
                    .unwrap_or(0),
            )
            .min(max_b.max(0));
        'search: for m00 in -bound..=bound {
            for m01 in -bound..=bound {
                for m10 in -bound..=bound {
                    for m11 in -bound..=bound {
                        if m00 == 1 && m01 == 0 && m10 == 0 && m11 == 1 {
                            continue;
                        }
                        checked += 1;
                        crate::access_trace::note_helper_work(51, 1);
                        let m = vec![m00, m01, m10, m11];
                        if let Some(t) =
                            apply_generator_k("linear", &coord_dims, &f_before, 0, &m, &[], steps)
                        {
                            if frames_equal(&t, &f_after) {
                                g = Some(G::Linear(m));
                                reason = "ok";
                                break 'search;
                            }
                        }
                    }
                }
            }
        }
    }

    let Some(g) = g else {
        return refused(
            reason,
            gap as i64,
            steps,
            prefix_len as i64,
            checked,
            &total,
            ctx,
        );
    };

    let (kind, matrix, offset): (&str, Vec<i64>, Vec<i64>) = match &g {
        G::Translate(off) => ("translate", Vec::new(), off.clone()),
        G::Linear(m) => ("linear", m.clone(), Vec::new()),
    };

    // --- the ABDUCED intermediates: G^t(f_before) for each gap tick ---
    let mut bridged: SmallVec<[Value; 4]> = SmallVec::new();
    for t in 1..=gap as i64 {
        let f = apply_generator_k(kind, &coord_dims, &f_before, 0, &matrix, &offset, t)
            .unwrap_or_default();
        bridged.push(Value::Tuple(Arc::new(f.into_iter().collect())));
    }

    // --- THE CLOSURE CHECK: does G^steps(f_before) reach f_after EXACTLY?
    //     For the translate branch this is true by construction; it is computed
    //     rather than asserted because a construction-true check that is never
    //     evaluated is exactly the inert instrument this arc keeps finding. ---
    let reached = apply_generator_k(kind, &coord_dims, &f_before, 0, &matrix, &offset, steps)
        .unwrap_or_default();
    let closes = frames_equal(&reached, &f_after);
    let correction = frames_symdiff(&reached, &f_after);

    let offset_out: SmallVec<[Value; 4]> = offset.iter().map(|x| Value::Int(*x)).collect();
    let matrix_out: SmallVec<[Value; 4]> = matrix.iter().map(|x| Value::Int(*x)).collect();
    let coord_out: SmallVec<[Value; 4]> = coord_dims.iter().map(|d| Value::Int(*d)).collect();
    let total_out: SmallVec<[Value; 4]> = total.iter().map(|x| Value::Int(*x)).collect();
    finish(
        Value::Dict(Arc::from(vec![
            (surf("explained"), Value::Bool(true)),
            (surf("kind"), surf(kind)),
            (surf("offset"), Value::Tuple(Arc::new(offset_out))),
            (surf("matrix"), Value::Tuple(Arc::new(matrix_out))),
            (surf("coord_dims"), Value::Tuple(Arc::new(coord_out))),
            (surf("gap"), Value::Int(gap as i64)),
            (surf("steps"), Value::Int(steps)),
            (surf("total"), Value::Tuple(Arc::new(total_out))),
            (surf("divisible"), Value::Bool(divisible)),
            (surf("reason"), surf(reason)),
            (surf("bridged"), Value::Tuple(Arc::new(bridged))),
            (surf("closes"), Value::Bool(closes)),
            (surf("correction"), Value::Int(correction)),
            (surf("prefix_len"), Value::Int(prefix_len as i64)),
            (surf("checked"), Value::Int(checked)),
        ])),
        field,
        ctx.interner,
        None,
    )
}

/// The COORDINATE key of a signature cell: its coordinate slots alone, in slot
/// order. Two cells are AT THE SAME PLACE iff their coordinate keys are
/// byte-identical — exact integer equality, an IN-FRAME comparison. This is the
/// whole of `GapVerify`'s coverage test, and the reason that test carries no
/// tolerance: a "close enough" radius would be a CROSS-frame quantity (a metric
/// between frames) smuggled into a single frame's coordinates.
fn coord_key(cell: &Value, coord_idxs: &[usize]) -> Option<Vec<Value>> {
    let (Value::Tuple(t) | Value::List(t)) = cell else {
        return None;
    };
    Some(
        t.iter()
            .enumerate()
            .filter(|(k, _)| coord_idxs.contains(k))
            .map(|(_, v)| v.clone())
            .collect(),
    )
}

/// Evaluate `GapVerify` — THE ABDUCED INTERMEDIATES, CHECKED.
///
/// `GapAbduce` measured its own deepest limit: it has NO DISCRIMINATIVE POWER
/// on the translate class, because ANY two same-shape figures are rigid
/// translates and divisibility is its only constraint. Its intermediates are
/// emitted and compared to NOTHING. This Term compares them: in a scene with
/// other content, `G^t(f_before)` is a FALSIFIABLE PREDICTION at every gap tick.
///
/// See the doc on `TermNode::GapVerify` for the split, the surface algebra and
/// the declared limits. The verification rule itself is one line of arithmetic
/// with no constant in it: a predicted cell is COVERED iff some observed cell of
/// the same gap frame has the identical coordinate key; `violations` is the
/// count of predicted cells that are not; `verified` iff that count is 0.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_gap_verify(
    arena: &TermArena,
    sequence_idx: TermIdx,
    codebook_type: Sym,
    max_b: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_GAP_VERIFY);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    let coord_dims: Vec<i64> = parts
        .iter()
        .find_map(|p| p.dim_types.as_ref())
        .map(|dts| {
            dts.iter()
                .enumerate()
                .filter(|(_, t)| t.starts_with("coord:"))
                .map(|(i, _)| i as i64)
                .collect()
        })
        .unwrap_or_default();
    let coord_idxs: Vec<usize> = coord_dims
        .iter()
        .filter_map(|&d| usize::try_from(d).ok())
        .collect();

    let seq_val = evaluate(arena, sequence_idx, env, ctx);
    let frames: Vec<Vec<Value>> = match &seq_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => seq_val
            .iter()
            .map(|f| match f {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
                    f.iter().cloned().collect()
                }
                _ => Vec::new(),
            })
            .collect(),
        _ => Vec::new(),
    };

    // Every field a REFUSAL reports is placed in the Dict BEFORE `finish` is
    // called, because `finish` SELECTS the requested field — a value patched in
    // afterwards silently does nothing on every call that asks for it, which is
    // exactly the defect the predecessor's `total` carried until a mechanism
    // test caught it. `ticks` and `predicted` are carried through a refusal so
    // that a FAILURE AFTER A FULL CHECK is distinguishable from a REFUSAL AT A
    // GUARD: `predicted == 0` on an `unverified` verdict would mean nothing was
    // ever compared.
    #[allow(clippy::too_many_arguments)]
    fn refused(
        reason: &str,
        gap: i64,
        steps: i64,
        prefix_len: i64,
        checked: i64,
        total: &[i64],
        ticks: i64,
        predicted: i64,
        covered: i64,
        surfaces: i64,
        hidden: i64,
        field: Sym,
        ctx: &mut EvalCtx,
    ) -> Value {
        let total_out: SmallVec<[Value; 4]> = total.iter().map(|x| Value::Int(*x)).collect();
        finish(
            Value::Dict(Arc::from(vec![
                (surf("explained"), Value::Bool(false)),
                (surf("abduced"), Value::Bool(false)),
                (surf("verified"), Value::Bool(false)),
                (surf("violations"), Value::Int(predicted - covered)),
                (surf("ticks"), Value::Int(ticks)),
                (surf("predicted"), Value::Int(predicted)),
                (surf("covered"), Value::Int(covered)),
                (surf("kind"), Value::None),
                (surf("offset"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("matrix"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("coord_dims"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("gap"), Value::Int(gap)),
                (surf("steps"), Value::Int(steps)),
                (surf("total"), Value::Tuple(Arc::new(total_out))),
                (surf("divisible"), Value::Bool(false)),
                (surf("reason"), surf(reason)),
                (surf("bridged"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("closes"), Value::Bool(false)),
                (surf("correction"), Value::Int(-1)),
                (surf("prefix_len"), Value::Int(prefix_len)),
                (surf("checked"), Value::Int(checked)),
                (surf("surfaces"), Value::Int(surfaces)),
                (surf("hidden"), Value::Int(hidden)),
            ])),
            field,
            ctx.interner,
            None,
        )
    }

    if frames.len() < 2 || coord_dims.is_empty() {
        return refused(
            "no_gap_structure",
            0,
            1,
            0,
            0,
            &[],
            0,
            0,
            0,
            0,
            0,
            field,
            ctx,
        );
    }

    // --- the SURFACE-SET split. An EMPTY frame's key set is `{}`, a strict
    //     subset of any non-empty set, so on a blank-gap stimulus this reduces
    //     EXACTLY to `GapAbduce`'s empty-run split. ---
    let keys_of = |f: &[Value]| -> Vec<Vec<Value>> {
        let mut out: Vec<Vec<Value>> = Vec::new();
        for c in f {
            if let Some(k) = surface_key(c, &coord_idxs) {
                if !out.contains(&k) {
                    out.push(k);
                }
            }
        }
        out
    };
    let full = keys_of(&frames[0]);
    if full.is_empty() {
        return refused(
            "no_gap_structure",
            0,
            1,
            0,
            0,
            &[],
            0,
            0,
            0,
            0,
            0,
            field,
            ctx,
        );
    }
    let same = |ks: &[Vec<Value>]| ks.len() == full.len() && ks.iter().all(|k| full.contains(k));
    let strict_subset =
        |ks: &[Vec<Value>]| ks.len() < full.len() && ks.iter().all(|k| full.contains(k));

    let mut prefix_len = 0usize;
    while prefix_len < frames.len() && same(&keys_of(&frames[prefix_len])) {
        prefix_len += 1;
    }
    let mut gap = 0usize;
    while prefix_len + gap < frames.len() && strict_subset(&keys_of(&frames[prefix_len + gap])) {
        gap += 1;
    }
    let mut resume_start = prefix_len + gap;

    // `gap == 0` — no vanish run at all — is the DEGENERATE case, handled on
    // THIS code path (never a second mechanism spliced in at one end of the ISI
    // curve): the boundary falls before the last frame, `steps == 1`, there are
    // no intermediates, and verification is VACUOUS rather than skipped.
    if gap == 0 && resume_start >= frames.len() && frames.len() >= 2 {
        prefix_len = frames.len() - 1;
        resume_start = frames.len() - 1;
    }
    if prefix_len == 0 || resume_start >= frames.len() || !same(&keys_of(&frames[resume_start])) {
        return refused(
            "no_gap_structure",
            gap as i64,
            gap as i64 + 1,
            prefix_len as i64,
            0,
            &[],
            0,
            0,
            0,
            full.len() as i64,
            0,
            field,
            ctx,
        );
    }
    let steps = gap as i64 + 1;
    let f_before = frames[prefix_len - 1].clone();
    let f_after = frames[resume_start].clone();
    let gap_frames: Vec<Vec<Value>> = (prefix_len..prefix_len + gap)
        .map(|i| frames[i].clone())
        .collect();

    // --- HIDDEN: present at both banks, absent in EVERY gap frame, and the SAME
    //     set at every tick (a surface that vanishes and returns mid-gap is not
    //     a gap this operator can read). ---
    let mut hidden: Vec<Vec<Value>> = Vec::new();
    if gap > 0 {
        let first = keys_of(&gap_frames[0]);
        hidden = full
            .iter()
            .filter(|k| !first.contains(k))
            .cloned()
            .collect();
        for gf in &gap_frames {
            let ks = keys_of(gf);
            let h: Vec<Vec<Value>> = full.iter().filter(|k| !ks.contains(k)).cloned().collect();
            if h != hidden {
                return refused(
                    "inconsistent_gap",
                    gap as i64,
                    steps,
                    prefix_len as i64,
                    0,
                    &[],
                    0,
                    0,
                    0,
                    full.len() as i64,
                    hidden.len() as i64,
                    field,
                    ctx,
                );
            }
        }
    }

    // --- PER-SURFACE RIGIDITY. Every surface shared by the two banks must be a
    //     rigid translate (the UNMODIFIED `infer_translate_offset`, the same
    //     criterion `TimeInfer` applies); the MOVING ones are those with a
    //     non-zero displacement, and exactly one is admitted. ---
    let cells_of = |f: &[Value], ks: &[Vec<Value>]| -> Vec<Value> {
        f.iter()
            .filter(|c| {
                surface_key(c, &coord_idxs)
                    .map(|k| ks.contains(&k))
                    .unwrap_or(false)
            })
            .cloned()
            .collect()
    };
    let mut moving: Vec<Vec<Value>> = Vec::new();
    let mut total: Vec<i64> = Vec::new();
    for k in &full {
        let one = vec![k.clone()];
        let b = cells_of(&f_before, &one);
        let a = cells_of(&f_after, &one);
        match infer_translate_offset(&b, &a, &coord_dims) {
            None => {
                return refused(
                    "not_rigid",
                    gap as i64,
                    steps,
                    prefix_len as i64,
                    0,
                    &[],
                    0,
                    0,
                    0,
                    full.len() as i64,
                    hidden.len() as i64,
                    field,
                    ctx,
                )
            }
            Some(d) => {
                if d.iter().any(|&x| x != 0) {
                    moving.push(k.clone());
                    total = d;
                }
            }
        }
    }
    if moving.is_empty() {
        return refused(
            "identity",
            gap as i64,
            steps,
            prefix_len as i64,
            0,
            &[],
            0,
            0,
            0,
            full.len() as i64,
            hidden.len() as i64,
            field,
            ctx,
        );
    }
    if moving.len() > 1 {
        return refused(
            "multi_motion",
            gap as i64,
            steps,
            prefix_len as i64,
            0,
            &[],
            0,
            0,
            0,
            full.len() as i64,
            hidden.len() as i64,
            field,
            ctx,
        );
    }
    // WHAT VANISHED MUST BE WHAT MOVED.
    if gap > 0 && !(hidden.len() == moving.len() && hidden.iter().all(|k| moving.contains(k))) {
        return refused(
            "hidden_mismatch",
            gap as i64,
            steps,
            prefix_len as i64,
            0,
            &[],
            0,
            0,
            0,
            full.len() as i64,
            hidden.len() as i64,
            field,
            ctx,
        );
    }

    let fig_before = cells_of(&f_before, &moving);
    let fig_after = cells_of(&f_after, &moving);

    // --- THE DIVISIBILITY TEST, UNCHANGED FROM `GapAbduce`: read D, then
    //     DIVIDE. Exact integer arithmetic; no tolerance and nowhere to put one. ---
    let mut checked: i64 = 0;
    enum G {
        Translate(Vec<i64>),
        Linear(Vec<i64>),
    }
    let mut divisible = false;
    let mut reason = "not_rigid";
    let mut g: Option<G> = None;
    if total.iter().all(|&x| x % steps == 0) {
        divisible = true;
        reason = "ok";
        g = Some(G::Translate(total.iter().map(|&x| x / steps).collect()));
    } else {
        reason = "indivisible";
    }

    // The same `steps`-th-root enumeration in the integer 2x2 linear class, over
    // the same data-derived bound, accepted only on EXACT equality.
    if g.is_none() && coord_dims.len() == 2 {
        let bound: i64 = coord_dims
            .iter()
            .filter_map(|&d| {
                let idx = usize::try_from(d).ok()?;
                let vs = coord_ints(&fig_before, idx)?;
                let mn = *vs.iter().min()?;
                vs.iter().map(|v| (v - mn).abs()).max()
            })
            .max()
            .unwrap_or(0)
            .max(
                coord_dims
                    .iter()
                    .filter_map(|&d| {
                        let idx = usize::try_from(d).ok()?;
                        let vs = coord_ints(&fig_after, idx)?;
                        let mn = *vs.iter().min()?;
                        vs.iter().map(|v| (v - mn).abs()).max()
                    })
                    .max()
                    .unwrap_or(0),
            )
            .min(max_b.max(0));
        'search: for m00 in -bound..=bound {
            for m01 in -bound..=bound {
                for m10 in -bound..=bound {
                    for m11 in -bound..=bound {
                        if m00 == 1 && m01 == 0 && m10 == 0 && m11 == 1 {
                            continue;
                        }
                        checked += 1;
                        crate::access_trace::note_helper_work(51, 1);
                        let m = vec![m00, m01, m10, m11];
                        if let Some(t) =
                            apply_generator_k("linear", &coord_dims, &fig_before, 0, &m, &[], steps)
                        {
                            if frames_equal(&t, &fig_after) {
                                g = Some(G::Linear(m));
                                reason = "ok";
                                break 'search;
                            }
                        }
                    }
                }
            }
        }
    }

    let Some(g) = g else {
        return refused(
            reason,
            gap as i64,
            steps,
            prefix_len as i64,
            checked,
            &total,
            0,
            0,
            0,
            full.len() as i64,
            hidden.len() as i64,
            field,
            ctx,
        );
    };

    let (kind, matrix, offset): (&str, Vec<i64>, Vec<i64>) = match &g {
        G::Translate(off) => ("translate", Vec::new(), off.clone()),
        G::Linear(m) => ("linear", m.clone(), Vec::new()),
    };

    // --- THE ABDUCED INTERMEDIATES, AND THE CHECK THAT `GapAbduce` DOES NOT DO.
    //     Each `G^t(f_before)` is compared, cell by cell, against what was
    //     ACTUALLY OBSERVED in gap frame `t`. ---
    let mut bridged: SmallVec<[Value; 4]> = SmallVec::new();
    let mut ticks: i64 = 0;
    let mut predicted: i64 = 0;
    let mut covered: i64 = 0;
    for t in 1..=gap as i64 {
        let f = apply_generator_k(kind, &coord_dims, &fig_before, 0, &matrix, &offset, t)
            .unwrap_or_default();
        let observed: Vec<Vec<Value>> = gap_frames[(t - 1) as usize]
            .iter()
            .filter_map(|c| coord_key(c, &coord_idxs))
            .collect();
        for cell in &f {
            predicted += 1;
            if let Some(ck) = coord_key(cell, &coord_idxs) {
                if observed.contains(&ck) {
                    covered += 1;
                }
            }
        }
        ticks += 1;
        bridged.push(Value::Tuple(Arc::new(f.into_iter().collect())));
    }
    let violations = predicted - covered;
    let verified = violations == 0;

    let reached = apply_generator_k(kind, &coord_dims, &fig_before, 0, &matrix, &offset, steps)
        .unwrap_or_default();
    let closes = frames_equal(&reached, &fig_after);
    let correction = frames_symdiff(&reached, &fig_after);
    let out_reason = if verified { reason } else { "unverified" };

    let offset_out: SmallVec<[Value; 4]> = offset.iter().map(|x| Value::Int(*x)).collect();
    let matrix_out: SmallVec<[Value; 4]> = matrix.iter().map(|x| Value::Int(*x)).collect();
    let coord_out: SmallVec<[Value; 4]> = coord_dims.iter().map(|d| Value::Int(*d)).collect();
    let total_out: SmallVec<[Value; 4]> = total.iter().map(|x| Value::Int(*x)).collect();
    finish(
        Value::Dict(Arc::from(vec![
            (surf("explained"), Value::Bool(verified)),
            (surf("abduced"), Value::Bool(true)),
            (surf("verified"), Value::Bool(verified)),
            (surf("violations"), Value::Int(violations)),
            (surf("ticks"), Value::Int(ticks)),
            (surf("predicted"), Value::Int(predicted)),
            (surf("covered"), Value::Int(covered)),
            (surf("kind"), surf(kind)),
            (surf("offset"), Value::Tuple(Arc::new(offset_out))),
            (surf("matrix"), Value::Tuple(Arc::new(matrix_out))),
            (surf("coord_dims"), Value::Tuple(Arc::new(coord_out))),
            (surf("gap"), Value::Int(gap as i64)),
            (surf("steps"), Value::Int(steps)),
            (surf("total"), Value::Tuple(Arc::new(total_out))),
            (surf("divisible"), Value::Bool(divisible)),
            (surf("reason"), surf(out_reason)),
            (surf("bridged"), Value::Tuple(Arc::new(bridged))),
            (surf("closes"), Value::Bool(closes)),
            (surf("correction"), Value::Int(correction)),
            (surf("prefix_len"), Value::Int(prefix_len as i64)),
            (surf("checked"), Value::Int(checked)),
            (surf("surfaces"), Value::Int(full.len() as i64)),
            (surf("hidden"), Value::Int(hidden.len() as i64)),
        ])),
        field,
        ctx.interner,
        None,
    )
}

/// The SURFACE key of a signature cell: its non-coordinate slots
/// (predicate / colour / arity), in slot order, with the coord slots removed.
/// Two cells share a surface iff their non-coord slots are byte-identical —
/// this is `infer_translate_offset`'s "same predicate, same colour" pairing
/// criterion, lifted to a GROUPING key. A "surface" is an appearance-coherent
/// region; DEPTH is NOT read off it (appearance is observable) — depth is read
/// off the surface's MOTION.
fn surface_key(cell: &Value, coord_idxs: &[usize]) -> Option<Vec<Value>> {
    let (Value::Tuple(t) | Value::List(t)) = cell else {
        return None;
    };
    Some(
        t.iter()
            .enumerate()
            .filter(|(k, _)| !coord_idxs.contains(k))
            .map(|(_, v)| v.clone())
            .collect(),
    )
}

/// Partition a frame's cells into surfaces keyed by `surface_key`, preserving
/// first-appearance order of the keys. Returns `(key, cells)` pairs.
fn partition_by_surface(frame: &[Value], coord_idxs: &[usize]) -> Vec<(Vec<Value>, Vec<Value>)> {
    let mut order: Vec<Vec<Value>> = Vec::new();
    let mut groups: Vec<Vec<Value>> = Vec::new();
    for cell in frame {
        let Some(key) = surface_key(cell, coord_idxs) else {
            continue;
        };
        match order.iter().position(|k| k == &key) {
            Some(i) => groups[i].push(cell.clone()),
            None => {
                order.push(key);
                groups.push(vec![cell.clone()]);
            }
        }
    }
    order.into_iter().zip(groups).collect()
}

/// Evaluate `DepthInfer` — MONOCULAR STRUCTURE-FROM-MOTION, the DEPTH sibling
/// of `TimeInfer`. Where `TimeInfer` asks "does ONE transition generator carry
/// the WHOLE scene?", `DepthInfer` reads the RESIDUAL of that question: a scene
/// with real (discrete) depth translated past a moving eye produces a 2D
/// transformation that NO SINGLE flat generator can explain — near layers sweep
/// faster than far ones (motion parallax). That unexplained residual — DIFFERENT
/// regions needing DIFFERENT translate generators — IS the depth signal.
///
/// The operation, on the frame/continuum invariant's IN-FRAME (integer) side:
/// each observable SURFACE (an appearance-coherent region — cells sharing their
/// non-coord slots, `surface_key`) is required to be a RIGID CONSTANT-VELOCITY
/// translate across the whole orbit (the SAME `infer_translate_offset` +
/// exact-equality verification `TimeInfer` runs, restricted to the surface).
/// Then the DECISION, which is the whole result:
///   * `distinct velocities <= 1`  ⇒ the whole scene IS carried by one
///     generator ⇒ residual ZERO ⇒ **NO `latent:depth`** (a flat scene, even a
///     multi-colour one at a single velocity, mints nothing — the decisive
///     anti-forced control: depth minted from VELOCITY VARIATION, never from the
///     mere presence of multiple regions);
///   * `distinct velocities >= 2`  ⇒ one generator cannot carry all regions ⇒
///     **MINT `latent:depth`**, the ORDINAL dimension indexing the surfaces by
///     motion (faster = nearer). `n_layers` = the count of DISTINCT velocities,
///     read from the data (never a hardcoded layer count); when surfaces share a
///     velocity, depth DEDUPS them (that is the MDL compression).
///
/// Continuous perspective (a real velocity gradient / continuous foreshortening)
/// is CROSS-FRAME (non-integer) and DEFERRED, exactly as real-angle rotation is;
/// this Term recovers only the DISCRETE, integer-velocity, in-frame core.
///
/// `field` selects: `explained` (bool — depth minted) / `n_layers` (Int) /
/// `velocities` (Tuple of offset-Tuples, near→far) / `ordering` (Tuple of
/// surface-key Tuples, near→far) / `layers` (Tuple of `(rank, velocity,
/// surface_key)` Tuples) / `predicted` (the UNSEEN frame at tick K, each surface
/// advanced by its OWN velocity — the downstream a naive single generator CANNOT
/// produce) / `window` (K) / `reason` (why nothing minted) / `checked`.
/// Integer lattice only; `dim_types` (coord slots) read from the first
/// `codebook_type` part, exactly as `TimeInfer`/`GenInfer`/`DimInfer` do.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_depth_infer(
    arena: &TermArena,
    sequence_idx: TermIdx,
    codebook_type: Sym,
    _max_b: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let _helper_work =
        crate::access_trace::enter_helper_scope(crate::access_trace::HELPER_DEPTH_INFER);
    let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
    let mut next_id: u32 = u32::MAX;
    let parts = load_parts(ctx, codebook_type, &mut extra, &mut next_id);
    let coord_dims: Vec<i64> = parts
        .iter()
        .find_map(|p| p.dim_types.as_ref())
        .map(|dts| {
            dts.iter()
                .enumerate()
                .filter(|(_, t)| t.starts_with("coord:"))
                .map(|(i, _)| i as i64)
                .collect()
        })
        .unwrap_or_default();
    let coord_idxs: Vec<usize> = coord_dims
        .iter()
        .filter_map(|&d| usize::try_from(d).ok())
        .collect();

    let seq_val = evaluate(arena, sequence_idx, env, ctx);
    let frames: Vec<Vec<Value>> = match &seq_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => seq_val
            .iter()
            .map(|f| match f {
                Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
                    f.iter().cloned().collect()
                }
                _ => Vec::new(),
            })
            .collect(),
        _ => Vec::new(),
    };

    let unexplained = |reason: &str, checked: i64, ctx: &mut EvalCtx| -> Value {
        finish(
            Value::Dict(Arc::from(vec![
                (surf("explained"), Value::Bool(false)),
                (surf("n_layers"), Value::Int(0)),
                (surf("velocities"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("ordering"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("layers"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("predicted"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("window"), Value::Int(0)),
                (surf("reason"), surf(reason)),
                (surf("checked"), Value::Int(checked)),
            ])),
            field,
            ctx.interner,
            None,
        )
    };

    if frames.len() < 2 || coord_idxs.is_empty() || frames.iter().any(|f| f.is_empty()) {
        return unexplained("insufficient_frames", 0, ctx);
    }

    // Surfaces are read from f0's appearance and must be STABLE across the orbit
    // (a surface may not appear or vanish — that would be occlusion, a separate
    // rung). The keys, in first-appearance order, are the region set.
    let surf0 = partition_by_surface(&frames[0], &coord_idxs);
    if surf0.is_empty() {
        return unexplained("no_surfaces", 0, ctx);
    }
    let keys: Vec<Vec<Value>> = surf0.iter().map(|(k, _)| k.clone()).collect();

    let mut checked: i64 = 0;
    // Per surface: infer a single constant-velocity offset and VERIFY it carries
    // every consecutive pair EXACTLY (the same rigidity test TimeInfer applies to
    // the whole scene, here per region). Any surface that is not a rigid
    // constant-velocity translate (a shuffled / accelerating / rotating region)
    // fails the whole decode to the enumeration floor.
    let mut vels: Vec<Vec<i64>> = Vec::with_capacity(keys.len());
    for key in &keys {
        // Extract this surface's cells in every frame.
        let mut sub: Vec<Vec<Value>> = Vec::with_capacity(frames.len());
        for f in &frames {
            let cells: Vec<Value> = f
                .iter()
                .filter(|c| surface_key(c, &coord_idxs).as_ref() == Some(key))
                .cloned()
                .collect();
            if cells.is_empty() {
                return unexplained("surface_vanished", checked, ctx);
            }
            sub.push(cells);
        }
        // Offset from the first pair, then verify constant across all pairs.
        let Some(off) = infer_translate_offset(&sub[0], &sub[1], &coord_dims) else {
            return unexplained("non_rigid_surface", checked, ctx);
        };
        for i in 0..sub.len() - 1 {
            checked += 1;
            crate::access_trace::note_helper_work(51, 1);
            match infer_translate_offset(&sub[i], &sub[i + 1], &coord_dims) {
                Some(o) if o == off => {}
                _ => return unexplained("non_constant_velocity", checked, ctx),
            }
        }
        vels.push(off);
    }

    // Distinct velocities = the residual measure. <=1 ⇒ one generator carries
    // the whole scene ⇒ NO depth (the flat / multi-colour-single-velocity control).
    let mut distinct: Vec<Vec<i64>> = Vec::new();
    for v in &vels {
        if !distinct.iter().any(|d| d == v) {
            distinct.push(v.clone());
        }
    }
    if distinct.len() < 2 {
        return unexplained("single_velocity", checked, ctx);
    }

    // MINT depth. Order surfaces near→far by speed (L1 norm of the offset),
    // descending; ties broken by the offset then the surface key, for a total
    // deterministic order. Depth rank = position in that order.
    let l1 = |v: &[i64]| -> i64 { v.iter().map(|x| x.abs()).sum() };
    let mut idx: Vec<usize> = (0..keys.len()).collect();
    idx.sort_by(|&a, &b| {
        l1(&vels[b])
            .cmp(&l1(&vels[a]))
            .then_with(|| vels[a].cmp(&vels[b]))
            .then_with(|| {
                keys[a]
                    .iter()
                    .zip(keys[b].iter())
                    .map(|(x, y)| cmp_value(x, y))
                    .find(|o| *o != std::cmp::Ordering::Equal)
                    .unwrap_or(std::cmp::Ordering::Equal)
            })
    });

    // Distinct velocities ordered near→far (dedup after the ordering).
    let mut vel_order: Vec<Vec<i64>> = Vec::new();
    for &i in &idx {
        if !vel_order.iter().any(|d| d == &vels[i]) {
            vel_order.push(vels[i].clone());
        }
    }
    let n_layers = vel_order.len() as i64;

    // Downstream: predict the UNSEEN frame at tick K = frames.len(), advancing
    // EACH surface by its OWN velocity K times, then merging. This is the view a
    // single (naive) generator cannot produce — the depth is what makes it
    // predictable.
    let k = frames.len() as i64;
    let mut predicted: Vec<Value> = Vec::new();
    for (si, key) in keys.iter().enumerate() {
        let cells0: Vec<Value> = frames[0]
            .iter()
            .filter(|c| surface_key(c, &coord_idxs).as_ref() == Some(key))
            .cloned()
            .collect();
        if let Some(adv) =
            apply_generator_k("translate", &coord_dims, &cells0, 0, &[], &vels[si], k)
        {
            predicted.extend(adv);
        }
    }
    predicted.sort_by(cmp_value);

    // Build the outputs, near→far.
    let mut velocities_out: SmallVec<[Value; 4]> = SmallVec::new();
    for v in &vel_order {
        let t: SmallVec<[Value; 4]> = v.iter().map(|x| Value::Int(*x)).collect();
        velocities_out.push(Value::Tuple(Arc::new(t)));
    }
    let mut ordering_out: SmallVec<[Value; 4]> = SmallVec::new();
    let mut layers_out: SmallVec<[Value; 4]> = SmallVec::new();
    for (rank, &i) in idx.iter().enumerate() {
        let key_t: SmallVec<[Value; 4]> = keys[i].iter().cloned().collect();
        let vel_t: SmallVec<[Value; 4]> = vels[i].iter().map(|x| Value::Int(*x)).collect();
        ordering_out.push(Value::Tuple(Arc::new(key_t.clone())));
        let layer: SmallVec<[Value; 4]> = smallvec::smallvec![
            Value::Int(rank as i64),
            Value::Tuple(Arc::new(vel_t)),
            Value::Tuple(Arc::new(key_t)),
        ];
        layers_out.push(Value::Tuple(Arc::new(layer)));
    }
    let predicted_out: SmallVec<[Value; 4]> = predicted.into_iter().collect();

    finish(
        Value::Dict(Arc::from(vec![
            (surf("explained"), Value::Bool(true)),
            (surf("n_layers"), Value::Int(n_layers)),
            (surf("velocities"), Value::Tuple(Arc::new(velocities_out))),
            (surf("ordering"), Value::Tuple(Arc::new(ordering_out))),
            (surf("layers"), Value::Tuple(Arc::new(layers_out))),
            (surf("predicted"), Value::Tuple(Arc::new(predicted_out))),
            (surf("window"), Value::Int(k)),
            (surf("reason"), surf("minted")),
            (surf("checked"), Value::Int(checked)),
        ])),
        field,
        ctx.interner,
        None,
    )
}

// ---------------------------------------------------------------------------
// `TransferDecode` — ANALOGICAL MECHANISM TRANSFER (the rung-2 sibling of
// `ShapeDecode` / `TransformDecode` / `DimInfer`). A faithful port of
// `domains/reflective_faculty.py`'s `retrieve_and_transfer_mechanism` +
// `transfer_mechanism` + `_filler_after_cue`, field-for-field.
//
// The recognised meta-shape is SUPPLIED by the caller (the agent's own
// `categorise_by_shape`, itself a Term) — this Term consumes it, it does not
// re-derive it. Given that shape, this Term RETRIEVES the held mechanism(s)
// indexed under it, DERIVES each abstract slot's target-domain filler from the
// GOAL's own predicate/argument structure via the slot's `cue`, and
// RE-INSTANTIATES the mechanism's abstract STEPS with those fillers — the
// output plan is the GOAL domain's, structurally isomorphic to the source:
// real transfer, not a lookup. The RETRIEVE (filter by shape + argmax on fit),
// the FILLER-DERIVATION, and the SUBSTITUTION all live here in Rust.
//
// The mechanism codebook is READ FROM THE GRAPH by `load_mechanisms` — every
// node of the codebook node-TYPE (`Mechanism`), exactly as `ShapeDecode` reads
// its `codebook_type` `ShapeSignature` nodes via `load_parts`. The node-TYPE is
// itself DISCOVERED FROM THE GRAPH via the `CodebookRegistry` declaration
// (`codebook_type_from_registry`), not a Term arg. The Python `_load_mechanisms`
// shim, its Lit-arg codebook, and the `mechanism_type` literal are all GONE.
// ---------------------------------------------------------------------------

/// The quantifier/determiner caps-tokens that are NOT domain fillers — the
/// Rust twin of Python's `_TRANSFER_NON_NOUNS`.
const TRANSFER_NON_NOUNS: &[&str] = &[
    "EVERY", "ALL", "WHOLE", "EACH", "ANY", "THIS", "THE", "THAT", "THESE", "THOSE", "SET", "ONLY",
    "CURRENT", "SOME", "NO", "A", "AN", "OF", "IN",
];

/// Python `str.isupper()`: at least one cased character, and no lowercase (or
/// titlecase) cased character. For the ASCII caps-token convention the goals
/// use, `char::is_lowercase`/`is_uppercase` capture it exactly.
fn td_is_upper(s: &str) -> bool {
    let mut has_cased = false;
    for c in s.chars() {
        if c.is_lowercase() {
            return false;
        }
        if c.is_uppercase() {
            has_cased = true;
        }
    }
    has_cased
}

/// `_is_domain_noun`: an ALL-CAPS multi-char token that is not a
/// quantifier/determiner — a goal's own structural marking of a filler.
fn td_is_domain_noun(tok: &str) -> bool {
    tok.chars().count() > 1 && td_is_upper(tok) && !TRANSFER_NON_NOUNS.contains(&tok)
}

/// Resolve a `Value` to an owned `String` (interned `Str` or `Surface(Text)`).
fn td_val_to_string(v: &Value, interner: &Interner) -> Option<String> {
    match v {
        Value::Str(s) => Some(interner.resolve(*s).to_string()),
        Value::Surface(SurfaceKind::Text, bytes) => {
            std::str::from_utf8(bytes).ok().map(|s| s.to_string())
        }
        _ => None,
    }
}

/// Look up a named key in a Dict's pair list (keys may be interned `Str`
/// from `py_to_value` or `Surface(Text)` from a Rust-built fixture).
fn td_dict_get<'a>(
    pairs: &'a [(Value, Value)],
    name: &str,
    interner: &Interner,
) -> Option<&'a Value> {
    for (k, v) in pairs.iter() {
        let hit = match k {
            Value::Str(s) => interner.resolve(*s) == name,
            Value::Surface(SurfaceKind::Text, b) => b.as_ref() == name.as_bytes(),
            _ => false,
        };
        if hit {
            return Some(v);
        }
    }
    None
}

/// A Tuple-of-tokens `Value` → `Vec<String>` (one goal step / one mechanism
/// step). Non-string tokens are dropped (every real goal is all-string).
fn td_str_list(v: &Value, interner: &Interner) -> Vec<String> {
    match v {
        Value::Tuple(items) | Value::List(items) => items
            .iter()
            .filter_map(|x| td_val_to_string(x, interner))
            .collect(),
        _ => Vec::new(),
    }
}

/// `_filler_after_cue`: DERIVE a slot's target filler from the goal's own
/// structure. Find the cue (verb only at token 0 of a step; preposition
/// anywhere), then read the FIRST maximal run of domain-nouns after it
/// (skipping leading glue), joined with `_`. `None` when the cue never occurs.
fn td_filler_after_cue(goal: &[Vec<String>], cue: &str, cue_kind: &str) -> Option<String> {
    let cue = cue.to_lowercase();
    if cue.is_empty() {
        return None;
    }
    for step in goal {
        let low: Vec<String> = step.iter().map(|t| t.to_lowercase()).collect();
        let positions: Vec<usize> = if cue_kind == "verb" {
            if !low.is_empty() && low[0] == cue {
                vec![0]
            } else {
                Vec::new()
            }
        } else {
            low.iter()
                .enumerate()
                .filter(|(_, t)| t.as_str() == cue)
                .map(|(i, _)| i)
                .collect()
        };
        for ci in positions {
            let mut run: Vec<String> = Vec::new();
            for t in &step[ci + 1..] {
                if td_is_domain_noun(t) {
                    run.push(t.clone());
                } else if !run.is_empty() {
                    break;
                }
            }
            if !run.is_empty() {
                return Some(run.join("_"));
            }
        }
    }
    None
}

/// TRANSFER one held mechanism into the goal's domain (the Rust twin of
/// `transfer_mechanism`). Returns `(total_fit, transferred_dict)`.
fn td_transfer_one(
    goal: &[Vec<String>],
    mech: &[(Value, Value)],
    interner: &Interner,
) -> (i64, Value) {
    let name = td_dict_get(mech, "name", interner).and_then(|v| td_val_to_string(v, interner));
    let domain = td_dict_get(mech, "domain", interner).and_then(|v| td_val_to_string(v, interner));
    let mshape =
        td_dict_get(mech, "meta_shape", interner).and_then(|v| td_val_to_string(v, interner));

    let slots: Vec<&[(Value, Value)]> = match td_dict_get(mech, "slots", interner) {
        Some(Value::Tuple(items) | Value::List(items)) => items
            .iter()
            .filter_map(|s| {
                if let Value::Dict(p) = s {
                    Some(p.as_ref())
                } else {
                    None
                }
            })
            .collect(),
        _ => Vec::new(),
    };
    let steps: Vec<Vec<String>> = match td_dict_get(mech, "steps", interner) {
        Some(Value::Tuple(items) | Value::List(items)) => {
            items.iter().map(|s| td_str_list(s, interner)).collect()
        }
        _ => Vec::new(),
    };

    // slot_map, insertion-ordered: (role, source, target, cue).
    let mut slot_map: Vec<(String, Option<String>, String, Option<String>)> = Vec::new();
    for slot in &slots {
        let role = td_dict_get(slot, "role", interner).and_then(|v| td_val_to_string(v, interner));
        let source =
            td_dict_get(slot, "source", interner).and_then(|v| td_val_to_string(v, interner));
        let cue = td_dict_get(slot, "cue", interner).and_then(|v| td_val_to_string(v, interner));
        let cue_kind = td_dict_get(slot, "cue_kind", interner)
            .and_then(|v| td_val_to_string(v, interner))
            .unwrap_or_else(|| "verb".to_string());
        let target = td_filler_after_cue(goal, cue.as_deref().unwrap_or(""), &cue_kind);
        if let (Some(r), Some(t)) = (role.filter(|r| !r.is_empty()), target) {
            slot_map.push((r, source, t, cue));
        }
    }

    // plan: re-instantiate each step, substituting any bound role.
    let plan: SmallVec<[Value; 4]> = steps
        .iter()
        .map(|step| {
            let toks: SmallVec<[Value; 4]> = step
                .iter()
                .map(|tok| match slot_map.iter().find(|(r, _, _, _)| r == tok) {
                    Some((_, _, target, _)) => surf_string(target.clone()),
                    None => surf_string(tok.clone()),
                })
                .collect();
            Value::Tuple(Arc::new(toks))
        })
        .collect();

    // unbound_roles: slot order; a role missing from slot_map (or None) is unbound.
    let mut unbound: SmallVec<[Value; 4]> = SmallVec::new();
    for slot in &slots {
        let role = td_dict_get(slot, "role", interner).and_then(|v| td_val_to_string(v, interner));
        let bound = match &role {
            Some(r) => slot_map.iter().any(|(sr, _, _, _)| sr == r),
            None => false,
        };
        if !bound {
            unbound.push(match role {
                Some(r) => surf_string(r),
                None => Value::None,
            });
        }
    }

    // slot_map Dict: {role -> {source, target, cue}}, orders preserved.
    let slot_map_pairs: Vec<(Value, Value)> = slot_map
        .iter()
        .map(|(role, source, target, cue)| {
            let inner = Value::Dict(Arc::from(vec![
                (
                    surf("source"),
                    source.clone().map(surf_string).unwrap_or(Value::None),
                ),
                (surf("target"), surf_string(target.clone())),
                (
                    surf("cue"),
                    cue.clone().map(surf_string).unwrap_or(Value::None),
                ),
            ]));
            (surf_string(role.clone()), inner)
        })
        .collect();

    let total_fit = slot_map.len() as i64;
    let transferred = Value::Dict(Arc::from(vec![
        (surf("plan"), Value::Tuple(Arc::new(plan))),
        (surf("slot_map"), Value::Dict(Arc::from(slot_map_pairs))),
        (surf("total_fit"), Value::Int(total_fit)),
        (surf("unbound_roles"), Value::Tuple(Arc::new(unbound))),
        (
            surf("mechanism"),
            name.map(surf_string).unwrap_or(Value::None),
        ),
        (
            surf("source_domain"),
            domain.map(surf_string).unwrap_or(Value::None),
        ),
        (
            surf("meta_shape"),
            mshape.map(surf_string).unwrap_or(Value::None),
        ),
    ]));
    (total_fit, transferred)
}

/// Read the SHAPE→MECHANISM index from the graph — every `mechanism_type`
/// node (default `Mechanism`, `seeds/mechanism_index.json`) as an owned
/// `{name, meta_shape, domain, slots, steps}` Dict. This is the graph-native
/// reader that REPLACES the thin Python `_load_mechanisms` + Lit-arg codebook:
/// it reads `ctx.graph`/`ctx.interner` exactly as `load_parts` reads its
/// `ShapeSignature` codebook. Selection + ordering mirror `_load_mechanisms`
/// field-for-field: iterate the type's nodes in insertion order, keep ONLY
/// those with a truthy `name` AND `meta_shape` AND `steps`. The `slots`
/// (`Value::Tuple`-of-`Value::Dict`) and `steps` (`Value::Tuple`-of-
/// `Value::Tuple`) attrs are carried through verbatim, so the downstream
/// `td_transfer_one`/retrieve logic sees exactly the Dict shape the Lit-arg
/// codebook used to supply (byte-identical).
fn load_mechanisms(ctx: &EvalCtx, mechanism_type: Sym) -> Vec<Value> {
    let mut out: Vec<Value> = Vec::new();
    for nid in ctx.graph.nodes_of_type(mechanism_type) {
        trace_scanned_node(ctx, nid);
        let node = ctx.graph.node(nid);
        let mut name_val: Option<Value> = None;
        let mut meta_shape_val: Option<Value> = None;
        let mut domain_val: Option<Value> = None;
        let mut slots_val: Option<Value> = None;
        let mut steps_val: Option<Value> = None;
        for (k, v) in node.attrs.iter() {
            match ctx.interner.resolve(*k) {
                "name" => name_val = Some(v.clone()),
                "meta_shape" => meta_shape_val = Some(v.clone()),
                "domain" => domain_val = Some(v.clone()),
                "slots" => slots_val = Some(v.clone()),
                "steps" => steps_val = Some(v.clone()),
                _ => {}
            }
        }
        // Selection mirrors Python `_load_mechanisms`: keep iff name AND
        // meta_shape AND steps are all truthy (non-empty).
        let keep = name_val.as_ref().is_some_and(|v| v.truthy())
            && meta_shape_val.as_ref().is_some_and(|v| v.truthy())
            && steps_val.as_ref().is_some_and(|v| v.truthy());
        if !keep {
            continue;
        }
        out.push(Value::Dict(Arc::from(vec![
            (surf("name"), name_val.unwrap()),
            (surf("meta_shape"), meta_shape_val.unwrap()),
            (surf("domain"), domain_val.unwrap_or(Value::None)),
            (
                surf("slots"),
                slots_val.unwrap_or_else(|| Value::Tuple(Arc::new(SmallVec::new()))),
            ),
            (surf("steps"), steps_val.unwrap()),
        ])));
    }
    out
}

/// The ONE irreducible well-known anchor: the graph node-TYPE under which
/// codebook-type registry declarations are held. This is the single fixed
/// point — WHICH codebook node-type serves a given role is read FROM the graph
/// (a `CodebookRegistry` node's `node_type` attr), never a Term arg or Python
/// literal. `seeds/mechanism_index.json` ships the mechanism-transfer entry.
const CODEBOOK_REGISTRY_TYPE: &str = "CodebookRegistry";
/// The `role` a mechanism-transfer codebook registry entry declares.
const MECHANISM_TRANSFER_ROLE: &str = "mechanism_transfer";

/// Discover the mechanism codebook's node-TYPE from the graph registry — the
/// replacement for the former `mechanism_type` Term arg. Iterate the fixed
/// `CodebookRegistry` anchor type's nodes, take the first whose `role` attr ==
/// "mechanism_transfer", read its `node_type` attr (a Str) and resolve it to a
/// Sym. `None` when no registry (or no mechanism-transfer entry) is held — the
/// no-op: default boot names no codebook type, so nothing transfers; a graph
/// shipping the registry names `Mechanism` and the transfer is identical.
/// Uses `lookup` (non-mutating): a type/attr only matters if it is already
/// interned by having been loaded into the graph, so an absent Sym ⇒ no nodes.
fn codebook_type_from_registry(ctx: &EvalCtx) -> Option<Sym> {
    let registry_type = ctx.interner.lookup(CODEBOOK_REGISTRY_TYPE)?;
    for nid in ctx.graph.nodes_of_type(registry_type) {
        trace_scanned_node(ctx, nid);
        let node = ctx.graph.node(nid);
        let mut role: Option<String> = None;
        let mut node_type: Option<String> = None;
        for (k, v) in node.attrs.iter() {
            match ctx.interner.resolve(*k) {
                "role" => role = td_val_to_string(v, ctx.interner),
                "node_type" => node_type = td_val_to_string(v, ctx.interner),
                _ => {}
            }
        }
        if role.as_deref() == Some(MECHANISM_TRANSFER_ROLE) {
            if let Some(nt) = node_type {
                return ctx.interner.lookup(&nt);
            }
        }
    }
    None
}

/// SHARED meta-shape recognition — the SINGLE graph-native scorer used by BOTH
/// the `RecogniseShape` Term (the agent's `categorise_by_shape` faculty) and
/// `eval_transfer_decode` (which now derives its own goal shape instead of
/// receiving a Python-supplied `meta_shape`). A faithful port of
/// `domains/teach.py::categorise_by_shape`'s SCORING DECISION: for every
/// `MetaShape` node, `score` = how many of its `has_principle` neighbours
/// (Principle nodes) have a `keywords` entry that is a SUBSTRING of `text`
/// (a principle counts once if ANY of its keywords matches — the old
/// `Exists(keywords, StringIndexOf(text, kw) >= 0)`). Keep shapes with
/// `score > 0`, argmax by `(-score, name)` (most overlap, then `name`
/// ascending — deterministic), and return the winning MetaShape's `name`
/// Value (already interned in the graph, so no interner mutation).
///
/// `text` is assumed to be in its FINAL form — this scorer does NOT lowercase.
/// The CALLER lowercases so shim byte-identity is exact: `categorise_by_shape`
/// applies Python `str.lower()`; `eval_transfer_decode` applies Rust
/// `to_lowercase()` (both over ASCII goal text ⇒ identical). Keywords are the
/// RAW graph values (never lowercased), exactly as the Python `StringIndexOf`
/// used them. Returns `None` when `text` is empty, no `MetaShape` nodes are
/// held, or no shape scores > 0 — matching `categorise_by_shape`'s
/// `if not text: return None` / empty-`scored` fallthrough.
/// ONE relation of an observation's shape signature, split into the PREDICATE
/// (element 0) and its ARGUMENTS (the rest). `predicate: None` is a bare,
/// predicate-less blob — which is exactly what the LEGACY flat-text path is,
/// expressed in the structural vocabulary, so one scorer serves both inputs.
struct MsRel {
    predicate: Option<String>,
    args: Vec<String>,
}

/// The evidence a MetaShape accumulates for one observation. THREE separate
/// counts, ranked LEXICOGRAPHICALLY (descending on each) — deliberately NOT
/// summed and NOT weighted, because a weight here would be exactly the scalar
/// SHAPE_AUDIT §6 reports and CLAUDE.md's "SHAPES, NOT NUMBERS" rule refuses.
#[derive(Default, Clone, Copy, PartialEq, Eq)]
struct MsEvidence {
    /// Distinct principles matched against a relation's PREDICATE — i.e. the
    /// item's own TYPED SLOT NAME (or its `is_a` type) names the principle.
    /// STRUCTURAL evidence, and therefore the first ranking key: an item whose
    /// slots ARE the shape beats an item that merely mentions the shape in prose.
    pred_principles: i64,
    /// Distinct principles matched anywhere (predicate OR argument). THIS IS
    /// THE LEGACY SCORE, preserved as the second key so the new ranking is a
    /// strict refinement of the old one and never a reversal of it.
    principles: i64,
    /// Distinct KEYWORDS matched anywhere. The finer evidence count that the
    /// old principle-granular score threw away — two independent keyword hits
    /// for one shape used to score identically to one.
    keywords: i64,
}

impl MsEvidence {
    #[inline]
    fn key(&self) -> (i64, i64, i64) {
        (self.pred_principles, self.principles, self.keywords)
    }
}

/// Decompose a signature `Value` into `MsRel`s. A collection of relations
/// (each itself a collection: `[predicate, arg, ...]`) decomposes structurally;
/// anything else degenerates to ONE predicate-less relation carrying the whole
/// thing as its single argument — the legacy text path, unchanged.
///
/// NOTHING is lowercased here: the caller supplies final-form text (the
/// contract `recognise_meta_shape` has always had), so `categorise_by_shape`'s
/// Python `str.lower()` and `eval_transfer_decode`'s `to_lowercase()` stay the
/// single normalisation point.
fn ms_relations(v: &Value, interner: &Interner) -> Vec<MsRel> {
    let items: Vec<Value> = match v {
        Value::Tuple(t) | Value::List(t) => t.to_vec(),
        Value::Set(s) | Value::FrozenSet(s) => s.to_vec(),
        other => {
            return match td_val_to_string(other, interner) {
                Some(s) => vec![MsRel {
                    predicate: None,
                    args: vec![s],
                }],
                None => Vec::new(),
            }
        }
    };
    let mut out: Vec<MsRel> = Vec::with_capacity(items.len());
    for it in items {
        match &it {
            Value::Tuple(parts) | Value::List(parts) => {
                let mut predicate: Option<String> = None;
                let mut args: Vec<String> = Vec::new();
                for (i, p) in parts.iter().enumerate() {
                    let s = td_val_to_string(p, interner);
                    if i == 0 {
                        predicate = s;
                    } else if let Some(s) = s {
                        args.push(s);
                    }
                }
                out.push(MsRel { predicate, args });
            }
            other => {
                if let Some(s) = td_val_to_string(other, interner) {
                    out.push(MsRel {
                        predicate: None,
                        args: vec![s],
                    });
                }
            }
        }
    }
    out
}

/// Score every held `MetaShape` against a decomposed observation. Returns
/// `(evidence, name_str, name_val)` for every shape with `principles > 0`,
/// gathered in graph insertion order (so a later stable sort keeps arrival
/// order for genuinely equal keys, exactly as the Python original did).
fn ms_score_shapes(ctx: &EvalCtx, rels: &[MsRel]) -> Vec<(MsEvidence, String, Value)> {
    let mut scored: Vec<(MsEvidence, String, Value)> = Vec::new();
    let Some(metashape_sym) = ctx.interner.lookup("MetaShape") else {
        return scored;
    };
    // If `has_principle` / `keywords` / `name` were never interned, no positive
    // score is possible (nothing to walk / read) — the honest empty.
    let (has_principle, keywords_key, name_key) = match (
        ctx.interner.lookup("has_principle"),
        ctx.interner.lookup("keywords"),
        ctx.interner.lookup("name"),
    ) {
        (Some(hp), Some(kw), Some(nm)) => (hp, kw, nm),
        _ => return scored,
    };

    for shape_id in ctx.graph.nodes_of_type(metashape_sym) {
        trace_scanned_node(ctx, shape_id);
        // A MetaShape with no truthy `name` is skipped (Python `if name:`).
        crate::access_trace::note(2, shape_id.0, name_key.0, crate::access_trace::NO_ID);
        let name_val = match ctx.graph.node(shape_id).attrs.get(&name_key) {
            Some(v) => v.clone(),
            None => continue,
        };
        let name_str = match td_val_to_string(&name_val, ctx.interner) {
            Some(s) if !s.is_empty() => s,
            _ => continue,
        };
        let mut ev = MsEvidence::default();
        let mut kw_seen: std::collections::BTreeSet<String> = Default::default();
        crate::access_trace::note_out_edges(ctx.graph, shape_id, Some(has_principle));
        for p_id in ctx.graph.neighbours(shape_id, Some(has_principle)) {
            crate::access_trace::note(2, p_id.0, keywords_key.0, crate::access_trace::NO_ID);
            let kws = match ctx.graph.node(p_id).attrs.get(&keywords_key) {
                Some(Value::Tuple(items) | Value::List(items)) => items,
                _ => continue,
            };
            let mut hit_any = false;
            let mut hit_pred = false;
            for kw in kws.iter() {
                let Some(k) = td_val_to_string(kw, ctx.interner) else {
                    continue;
                };
                if k.is_empty() {
                    continue;
                }
                let in_pred = rels
                    .iter()
                    .any(|r| r.predicate.as_deref().map_or(false, |p| p.contains(&k)));
                let in_arg = rels.iter().any(|r| r.args.iter().any(|a| a.contains(&k)));
                if in_pred {
                    hit_pred = true;
                }
                if in_pred || in_arg {
                    hit_any = true;
                    kw_seen.insert(k);
                }
            }
            if hit_pred {
                ev.pred_principles += 1;
            }
            if hit_any {
                ev.principles += 1;
            }
        }
        ev.keywords = kw_seen.len() as i64;
        if ev.principles > 0 {
            scored.push((ev, name_str, name_val));
        }
    }
    scored
}

/// Pick the winner — or REFUSE. Ranks by `MsEvidence::key()` descending and
/// returns the top shape's `name` Value.
///
/// **THE ALPHABETICAL TIEBREAK IS GONE** (`SHAPE_AUDIT.md` §2.5's third stacked
/// defect: `then_with(|| a.1.cmp(&b.1))` let `associative_recall` beat a rival
/// "for no reason but the letter `a`"). When the top two candidates share the
/// FULL evidence key the contest is genuinely undecided, and this returns
/// `None` — the honest RESIDUAL, which is what the sd loop does everywhere else
/// (`sd_mint_quantum` fires "only after BOTH rungs fail"; it does not guess).
/// A residual is a mint candidate; a fabricated winner is not.
fn ms_pick(mut scored: Vec<(MsEvidence, String, Value)>) -> Option<Value> {
    if scored.is_empty() {
        return None;
    }
    scored.sort_by(|a, b| b.0.key().cmp(&a.0.key()));
    if scored.len() > 1 && scored[0].0.key() == scored[1].0.key() {
        return None; // genuinely tied ⇒ a residual, not an answer
    }
    Some(scored[0].2.clone())
}

/// SHARED meta-shape recognition — the SINGLE graph-native scorer used by BOTH
/// the `RecogniseShape` Term (the agent's `categorise_by_shape` faculty) and
/// `eval_transfer_decode` (which derives its own goal shape).
///
/// **This is the KEYWORD PRIOR rung of the meta-shape ladder, not the whole
/// ladder.** Structural recognition proper (`ShapeDecode` / `TransformDecode` /
/// `DimInfer` pointed at `codebook_type: "MetaShape"`, which `load_parts` reads
/// grain-agnostically off any node carrying `name` + `signature`) sits ABOVE it
/// in `seeds/meta_shape_growth.json`. This rung exists because the eleven
/// SEEDED `MetaShape` nodes carry NO signature and never will until something
/// files under them — so keywords are the honest bootstrap, and they run LAST,
/// just before the mint, exactly where the weakest evidence belongs.
///
/// Fixed here, against `SHAPE_AUDIT.md` §2.5's three stacked defects:
/// 1. the item's typed structure is no longer destroyed — `rels` carries the
///    attribute KEYS as relation PREDICATES, and a keyword matching a predicate
///    is ranked ABOVE any amount of prose evidence (`pred_principles`);
/// 2. the score is no longer principle-granular only — distinct KEYWORD hits
///    are a third, finer ranking key;
/// 3. ties no longer break alphabetically — they return `None`.
///
/// `text` is assumed to be in its FINAL form — this scorer does NOT lowercase.
fn recognise_meta_shape(ctx: &EvalCtx, text: &str) -> Option<Value> {
    if text.is_empty() {
        return None;
    }
    let rels = vec![MsRel {
        predicate: None,
        args: vec![text.to_string()],
    }];
    ms_pick(ms_score_shapes(ctx, &rels))
}

/// Evaluate `RecogniseShape` — the Term wrapper over the shared scorer, now
/// INPUT-POLYMORPHIC on the evaluated value:
///
/// * a **string** (interned `Str` / `Surface(Text)`) takes the legacy flat-text
///   path — one predicate-less relation, so `pred_principles` is 0 for every
///   candidate and the ranking reduces to (legacy score, keyword count).
///   `TransferDecode` still reaches the scorer this way.
/// * a **collection** takes the STRUCTURAL path: each member is a relation
///   `[predicate, arg, ...]`, so an item's attribute KEYS and node TYPE — which
///   `domains/teach.py:93` used to discard wholesale — are scored as predicates.
///
/// The result is the winning MetaShape's `name` `Value`, or `Value::None` when
/// nothing scores or the contest is tied (the honest residual).
pub(crate) fn eval_recognise_shape(
    arena: &TermArena,
    text_idx: TermIdx,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let text_val = evaluate(arena, text_idx, env, ctx);
    match &text_val {
        Value::Tuple(_) | Value::List(_) | Value::Set(_) | Value::FrozenSet(_) => {
            let rels = ms_relations(&text_val, ctx.interner);
            if rels.is_empty() {
                return Value::None;
            }
            ms_pick(ms_score_shapes(ctx, &rels)).unwrap_or(Value::None)
        }
        _ => {
            let text = match td_val_to_string(&text_val, ctx.interner) {
                Some(s) => s,
                None => return Value::None,
            };
            recognise_meta_shape(ctx, &text).unwrap_or(Value::None)
        }
    }
}

// ---------------------------------------------------------------------------
//  META-SHAPE MINT — rung 4 of the meta-shape grain's growth ladder.
//
//  `SHAPE_AUDIT.md` finding #1: `seeds/shape_vocabulary.json` holds 11
//  `MetaShape` + 13 `ShapePrinciple` nodes and NOTHING in the tree mints one at
//  runtime — "the sd loop's fourth rung is not wired to the faculty named
//  'shape'." This Term is that fourth rung.
//
//  WHAT COUNTS AS RECURRENCE (the support discipline, registered in
//  META_SHAPE_FIRST_CLASS_PREREG.md §3.2 before this was built):
//
//  * Residual observations are grouped by their PREDICATE SET — the sorted,
//    de-duplicated set of relation predicates (the item's typed-slot skeleton).
//    SORTED and SET-valued deliberately: `SHAPE_AUDIT.md` §3.1 documents the
//    `CapabilityAxis` key as "order-dependent and truncated at three" and both
//    of its failure directions; this key is neither.
//  * Support = the group's size. A group mints at size >= 2 and not before.
//    TWO is not a swept knob — it is the smallest cardinality at which "recurs"
//    is DEFINED. A distribution-derived quantile (P7-C's precedent) needs a
//    distribution this 24-entry codebook does not have; a similarity threshold
//    is exactly the `stroke_codebook.py:82` Pattern E defect and is refused.
//  * The minted SIGNATURE is the anti-unified lgg over the whole group — so the
//    slots the group agrees on stay FIXED and the slots it disagrees on become
//    WILD. That is precisely the pattern `ShapeDecode` (rung 1) needs in order
//    to recognise the NEXT member of the family without minting again.
//  * Non-triviality is STRUCTURAL, not numeric: the key must be non-empty and
//    the lgg must fix at least one leaf (`fixed_count > 0`). Two unrelated items
//    anti-unify to all-WILD and mint nothing.
//  * `leader` designates ONE minter per group (the lowest node id) so a group of
//    N residuals mints ONCE within a single `run_rules` pass rather than N
//    times. This is a CANONICAL-REPRESENTATIVE pick, the same shape
//    `retire_duplicate_gap`'s `Argmin` uses and which `SHAPE_AUDIT.md` §2.7
//    explicitly rejects as Pattern A — not a similarity ranking.
// ---------------------------------------------------------------------------

/// The sorted, de-duplicated set of relation PREDICATES of a signature —
/// an observation's typed-slot skeleton, and the meta-shape grain's group key.
fn ms_predicate_key(sig: &Value, interner: &Interner) -> Vec<String> {
    let mut keys: std::collections::BTreeSet<String> = Default::default();
    for r in ms_relations(sig, interner) {
        if let Some(p) = r.predicate {
            if !p.is_empty() {
                keys.insert(p);
            }
        }
    }
    keys.into_iter().collect()
}

/// Evaluate `MetaShapeMint` — decides whether the residual bound to
/// `observation` has RECURRED, and if so hands the rule everything it needs to
/// mint the new codebook entry. Output Dict:
///
/// | field | meaning |
/// |---|---|
/// | `name` | the minted MetaShape's name — `ms_` + the sorted predicate key, joined. CONTENT-derived and order-independent. |
/// | `keys` | the sorted predicate key itself → the minted ShapePrinciple's `keywords`. |
/// | `signature` | the anti-unified lgg over the group → the minted MetaShape's `signature`, which rungs 1-3 then read via `load_parts`. |
/// | `support` | the group's size. |
/// | `fixed` | `fixed_count` of the lgg (0 ⇒ the group shares no leaf ⇒ nothing worth minting). |
/// | `leader` | 1 iff this observation is the group's canonical minter. |
/// | `mintable` | 1 iff `support >= 2 && !keys.is_empty() && fixed > 0 && leader`. |
///
/// `field` selects one key, exactly as `TransformDecode` / `DimInfer` do.
pub(crate) fn eval_meta_shape_mint(
    arena: &TermArena,
    obs_idx: TermIdx,
    obs_type: Sym,
    status_value: Sym,
    wild: Sym,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let obs_val = evaluate(arena, obs_idx, env, ctx);
    let empty = |ctx: &EvalCtx| -> Value {
        let d = Value::Dict(Arc::from(vec![
            (surf("name"), Value::None),
            (surf("keys"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("signature"), Value::None),
            (surf("support"), Value::Int(0)),
            (surf("fixed"), Value::Int(0)),
            (surf("leader"), Value::Int(0)),
            (surf("mintable"), Value::Int(0)),
        ]));
        ms_field(d, field, ctx.interner)
    };
    let Value::Node(obs_id) = obs_val else {
        return empty(ctx);
    };

    let (Some(sig_key), Some(status_key)) = (
        ctx.interner.lookup("signature"),
        ctx.interner.lookup("status"),
    ) else {
        return empty(ctx);
    };
    crate::access_trace::note(2, obs_id.0, sig_key.0, crate::access_trace::NO_ID);
    let Some(my_sig) = ctx.graph.node(obs_id).attrs.get(&sig_key).cloned() else {
        return empty(ctx);
    };
    let key = ms_predicate_key(&my_sig, ctx.interner);
    if key.is_empty() {
        return empty(ctx);
    }

    // THE GROUP: every observation of the same type, still `status_value`
    // (residual), whose predicate key is IDENTICAL. Order-independent by
    // construction — the key is a sorted set, never a positional prefix.
    let mut group_sigs: Vec<Value> = Vec::new();
    let mut leader = true;
    for nid in ctx.graph.nodes_of_type(obs_type) {
        trace_scanned_node(ctx, nid);
        let node = ctx.graph.node(nid);
        let ok_status = node
            .attrs
            .get(&status_key)
            .map(|v| matches!(v, Value::Str(s) if *s == status_value))
            .unwrap_or(false);
        if !ok_status {
            continue;
        }
        let Some(sig) = node.attrs.get(&sig_key) else {
            continue;
        };
        if ms_predicate_key(sig, ctx.interner) != key {
            continue;
        }
        if nid < obs_id {
            leader = false;
        }
        group_sigs.push(sig.clone());
    }

    let support = group_sigs.len() as i64;
    let wild_val = wild_value(wild);
    let core = anti_unify_values(&group_sigs, &wild_val);
    let fixed = fixed_count_value(&core, &wild_val);
    let mintable = support >= 2 && fixed > 0 && leader;

    // THE KEYWORD SET IS THE DISCRIMINATIVE PART OF THE KEY, NOT ALL OF IT.
    //
    // Measured, not anticipated: the first working mint emitted `is_a` among
    // the minted principle's `keywords`, and because EVERY observation carries
    // an `is_a` relation by construction, the minted shape then scored a
    // predicate hit on literally every subsequent item and won the keyword
    // prior against the correct answer. (Live: the `"gate the layer by policy"`
    // negative control came back as the minted trade-record shape instead of
    // `selective_gating`.)
    //
    // The fix is derived, not a name-list: a predicate present in EVERY held
    // observation carries zero discriminative information, so it is dropped
    // from the keywords. This is a boolean information test over the observed
    // population — NOT a tuned frequency threshold, and NOT a hardcoded
    // stop-list of predicate names (which would be exactly the Pattern A defect
    // this whole rung exists to remove).
    //
    // The group KEY — the shape's identity and name — still uses the FULL
    // predicate set. Only what the keyword PRIOR can see is narrowed. A shape
    // whose every predicate is universal ends up with no keywords at all, which
    // is the honest outcome: it is unreachable by the weak keyword rung and
    // still perfectly reachable by rung 1's structural `Covers`.
    let mut all_obs = 0usize;
    let mut pred_doc_count: std::collections::BTreeMap<String, usize> = Default::default();
    for nid in ctx.graph.nodes_of_type(obs_type) {
        trace_scanned_node(ctx, nid);
        let Some(sig) = ctx.graph.node(nid).attrs.get(&sig_key) else {
            continue;
        };
        all_obs += 1;
        for p in ms_predicate_key(sig, ctx.interner) {
            *pred_doc_count.entry(p).or_insert(0) += 1;
        }
    }
    let discriminative: Vec<&String> = key
        .iter()
        .filter(|k| pred_doc_count.get(*k).copied().unwrap_or(0) < all_obs)
        .collect();

    let name = format!("ms_{}", key.join("_"));
    let keys_val = Value::Tuple(Arc::new(
        discriminative
            .iter()
            .map(|k| surf(k))
            .collect::<SmallVec<[Value; 4]>>(),
    ));
    let out = Value::Dict(Arc::from(vec![
        (surf("name"), surf_string(name)),
        (surf("keys"), keys_val),
        (surf("signature"), core),
        (surf("support"), Value::Int(support)),
        (surf("fixed"), Value::Int(fixed)),
        (surf("leader"), Value::Int(if leader { 1 } else { 0 })),
        (surf("mintable"), Value::Int(if mintable { 1 } else { 0 })),
    ]));
    ms_field(out, field, ctx.interner)
}

/// `field` selection, mirroring `TransformDecode` / `DimInfer`: an empty or
/// absent `field` returns the whole Dict; otherwise the named key's value
/// (`Value::None` when the key is unknown).
fn ms_field(d: Value, field: Sym, interner: &Interner) -> Value {
    // `Sym::default()` is what `jsonio::get_optional_sym` yields for an ABSENT
    // `field` — compare the Sym, not its resolved text (the idiom
    // `select_cached_field` already uses; `resolve(Sym::default())` is not
    // guaranteed to be the empty string).
    if field == Sym::default() {
        return d;
    }
    let f = interner.resolve(field);
    if f.is_empty() {
        return d;
    }
    match &d {
        Value::Dict(pairs) => td_dict_get(pairs, f, interner)
            .cloned()
            .unwrap_or(Value::None),
        _ => Value::None,
    }
}

/// Evaluate `TransferDecode` — retrieve-and-transfer, faithful to
/// `retrieve_and_transfer_mechanism` field-for-field. `goal` is a
/// Tuple-of-Tuples (list of steps of tokens). The recognised meta-shape is now
/// DERIVED HERE from the goal's own text via the shared `recognise_meta_shape`
/// (was a Python-supplied `meta_shape` Term arg) — the exact scorer the agent's
/// `categorise_by_shape` faculty uses, so there is ONE recognition path. No
/// shape recognised ⇒ the "no shape" honest wall. The codebook node-type is
/// DISCOVERED FROM THE GRAPH via the `CodebookRegistry` anchor
/// (`codebook_type_from_registry`) — no Term arg — then its nodes are read by
/// `load_mechanisms`, exactly as `ShapeDecode` reads its `codebook_type`.
pub(crate) fn eval_transfer_decode(
    arena: &TermArena,
    goal_idx: TermIdx,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let goal_val = evaluate(arena, goal_idx, env, ctx);
    // The mechanism codebook node-TYPE is DISCOVERED FROM THE GRAPH registry
    // (was a Lit `mechanism_type` Term arg), then its nodes are READ FROM THE
    // GRAPH (was a Lit-arg Tuple-of-Dicts from the now-deleted Python
    // `_load_mechanisms`). No registry held ⇒ no type ⇒ empty ⇒ the no-op.
    let mechs_owned: Vec<Value> = match codebook_type_from_registry(ctx) {
        Some(mechanism_type) => load_mechanisms(ctx, mechanism_type),
        None => Vec::new(),
    };
    // No index held at all → `Value::None`, exactly as the old Python
    // `retrieve_and_transfer_mechanism` short-circuited (`if not mechs: return
    // None`) BEFORE the meta-shape check: nothing to transfer, mint stays the
    // fallback, and the composer's no-op guard is byte-identical.
    if mechs_owned.is_empty() {
        return Value::None;
    }

    let goal: Vec<Vec<String>> = match &goal_val {
        Value::Tuple(steps) | Value::List(steps) => {
            steps.iter().map(|s| td_str_list(s, ctx.interner)).collect()
        }
        _ => Vec::new(),
    };
    // DERIVE the goal's meta-shape via the SHARED recogniser (was the
    // Python-supplied `meta_shape` arg). Build the goal text EXACTLY as the old
    // `retrieve_and_transfer_mechanism` did — join ALL goal tokens across all
    // steps with " " (each via `td_val_to_string`) — then lowercase (the
    // `.lower()` the old `categorise_by_shape` applied to that text), and score
    // it against the held `MetaShape` vocabulary. Empty text / no shape ⇒ None.
    let goal_text = goal
        .iter()
        .flat_map(|step| step.iter().cloned())
        .collect::<Vec<String>>()
        .join(" ")
        .to_lowercase();
    let ms_val = recognise_meta_shape(ctx, &goal_text).unwrap_or(Value::None);
    let interner: &Interner = ctx.interner;
    let meta_shape: Option<String> = td_val_to_string(&ms_val, interner).filter(|s| !s.is_empty());

    // No meta-shape recognised — mint remains the honest fallback.
    let ms = match meta_shape {
        None => {
            return Value::Dict(Arc::from(vec![
                (surf("meta_shape"), Value::None),
                (surf("retrieved"), Value::Tuple(Arc::new(SmallVec::new()))),
                (surf("transferred"), Value::None),
                (
                    surf("note"),
                    surf(
                        "no meta-shape recognised for the goal — mint remains the honest fallback",
                    ),
                ),
            ]));
        }
        Some(s) => s,
    };

    // Retrieve: every mechanism indexed under the recognised shape.
    let mechs: Vec<&[(Value, Value)]> = mechs_owned
        .iter()
        .filter_map(|m| {
            if let Value::Dict(p) = m {
                Some(p.as_ref())
            } else {
                None
            }
        })
        .collect();
    let mut cands: Vec<&[(Value, Value)]> = Vec::new();
    let mut cand_names: SmallVec<[Value; 4]> = SmallVec::new();
    for m in &mechs {
        let mshape =
            td_dict_get(m, "meta_shape", interner).and_then(|v| td_val_to_string(v, interner));
        if mshape.as_deref() == Some(ms.as_str()) {
            cands.push(*m);
            cand_names.push(
                td_dict_get(m, "name", interner)
                    .and_then(|v| td_val_to_string(v, interner))
                    .map(surf_string)
                    .unwrap_or(Value::None),
            );
        }
    }

    if cands.is_empty() {
        return Value::Dict(Arc::from(vec![
            (surf("meta_shape"), surf_string(ms.clone())),
            (surf("retrieved"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("transferred"), Value::None),
            (
                surf("note"),
                surf_string(format!(
                    "recognised shape '{}' but no held mechanism is indexed under it",
                    ms
                )),
            ),
        ]));
    }

    // Transfer each candidate; keep the highest total_fit (strict, first wins).
    let mut best: Option<Value> = None;
    let mut best_fit: i64 = -1;
    for m in &cands {
        let (fit, transferred) = td_transfer_one(&goal, m, interner);
        if best.is_none() || fit > best_fit {
            best = Some(transferred);
            best_fit = fit;
        }
    }

    Value::Dict(Arc::from(vec![
        (surf("meta_shape"), surf_string(ms)),
        (surf("retrieved"), Value::Tuple(Arc::new(cand_names))),
        (surf("transferred"), best.unwrap()),
    ]))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::{NodeID, TypedGraph};
    use crate::term::TermNode;

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    fn prefilter_rows(points: &[(i64, i64)], nonlinear: bool) -> Vec<Value> {
        points.iter().enumerate().map(|(i, &(x, y))| {
            let out_y = if nonlinear { y + x * x } else { x - y };
            tuple_of(vec![Value::Int(0), Value::Int(i as i64), Value::Int(2*x+y), Value::Int(out_y)])
        }).collect()
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    fn exact_linear_prefilter_recovers_integer_map_and_refuses_nonlinear_shape() {
        let points = [(0, 0), (1, 0), (0, 1), (1, 1), (2, 1)];
        let source: Vec<Value> = points.iter().enumerate().map(|(i, &(x,y))|
            tuple_of(vec![Value::Int(0), Value::Int(i as i64), Value::Int(x), Value::Int(y)])).collect();
        let dim_types = vec!["pred".into(), "id".into(), "coord:r".into(), "coord:c".into()];
        assert!(matches!(infer_exact_2d_linear_prefilter(&source, &prefilter_rows(&points, false), &dim_types, &[2,3], 8), ExactLinearPrefilter::Solved(m) if m == vec![2,1,1,-1]));
        assert!(matches!(infer_exact_2d_linear_prefilter(&source, &prefilter_rows(&points, true), &dim_types, &[2,3], 16), ExactLinearPrefilter::ProvenNoFit(_)));
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    fn exact_linear_prefilter_work_counters_are_audit_gated() {
        let _guard = crate::scale_audit::exclusive();
        let points = [(0,0),(1,0),(0,1),(1,1)];
        let source: Vec<Value> = points.iter().enumerate().map(|(i,&(x,y))|
            tuple_of(vec![Value::Int(0),Value::Int(i as i64),Value::Int(x),Value::Int(y)])).collect();
        let target = prefilter_rows(&points, false);
        let dim_types = vec!["pred".into(),"id".into(),"coord:r".into(),"coord:c".into()];
        crate::scale_audit::set_enabled(false);
        PREFILTER_IDENTITY_VALUE_COMPARISONS.with(|n| n.set(0));
        PREFILTER_EXACT_ARITHMETIC_CHECKS.with(|n| n.set(0));
        let _ = infer_exact_2d_linear_prefilter(&source,&target,&dim_types,&[2,3],4);
        assert_eq!(PREFILTER_IDENTITY_VALUE_COMPARISONS.with(Cell::get), 0);
        assert_eq!(PREFILTER_EXACT_ARITHMETIC_CHECKS.with(Cell::get), 0);

        crate::scale_audit::set_enabled(true);
        let _ = infer_exact_2d_linear_prefilter(&source,&target,&dim_types,&[2,3],4);
        assert!(PREFILTER_IDENTITY_VALUE_COMPARISONS.with(Cell::get) > 0);
        assert!(PREFILTER_EXACT_ARITHMETIC_CHECKS.with(Cell::get) > 0);
        crate::scale_audit::set_enabled(false);
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    fn exact_linear_prefilter_falls_back_on_duplicate_keys_and_rank_deficiency() {
        let dim_types = vec!["pred".into(), "id".into(), "coord:r".into(), "coord:c".into()];
        let points = [(0,0), (1,1), (2,2), (3,3)];
        let source: Vec<Value> = points.iter().enumerate().map(|(i, &(x,y))|
            tuple_of(vec![Value::Int(0), Value::Int(i as i64), Value::Int(x), Value::Int(y)])).collect();
        assert!(matches!(infer_exact_2d_linear_prefilter(&source, &source, &dim_types, &[2,3], 4), ExactLinearPrefilter::Fallback(_)));
        let mut duplicate = source.clone();
        duplicate[3] = duplicate[2].clone();
        assert!(matches!(infer_exact_2d_linear_prefilter(&duplicate, &source, &dim_types, &[2,3], 4), ExactLinearPrefilter::Fallback(_)));
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    fn exact_linear_prefilter_proves_relation_count_mismatch_is_no_fit() {
        let dim_types = vec!["pred".into(), "id".into(), "coord:r".into(), "coord:c".into()];
        let source = vec![tuple_of(vec![Value::Int(0),Value::Int(1),Value::Int(0),Value::Int(0)])];
        let target = vec![source[0].clone(), source[0].clone()];
        assert!(matches!(infer_exact_2d_linear_prefilter(&source, &target, &dim_types, &[2,3], 1), ExactLinearPrefilter::ProvenNoFit(_)));
        let extra = FxHashMap::default();
        assert!(build_candidate("base".into(), Value::None, &source, &target, 2, &extra, false).is_none());
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    fn exact_linear_prefilter_refuses_noninteger_or_unmatched_identity_and_supports_multiple_ids() {
        let dim_types=vec!["pred".into(),"id".into(),"coord:r".into(),"coord:c".into()];
        let points=[(0,0),(1,0),(0,1),(1,1)];
        let source:Vec<Value>=points.iter().enumerate().map(|(i,&(x,y))|tuple_of(vec![Value::Int(0),Value::Int(i as i64),Value::Int(x),Value::Int(y)])).collect();
        let mut noninteger=source.clone();
        noninteger[2]=tuple_of(vec![Value::Int(0),Value::Int(2),Value::Float(0.5),Value::Int(3)]);
        assert!(matches!(infer_exact_2d_linear_prefilter(&source,&noninteger,&dim_types,&[2,3],4),ExactLinearPrefilter::Fallback(_)));
        let no_id_types=vec!["pred".into(),"coord:r".into(),"coord:c".into()];
        assert!(matches!(infer_exact_2d_linear_prefilter(&source,&source,&no_id_types,&[1,2],2),ExactLinearPrefilter::Fallback(_)));
        let mut missing=source.clone();
        missing[3]=tuple_of(vec![Value::Int(0),Value::Int(99),Value::Int(1),Value::Int(1)]);
        assert!(matches!(infer_exact_2d_linear_prefilter(&source,&missing,&dim_types,&[2,3],2),ExactLinearPrefilter::Fallback(_)));

        let multi_types=vec!["pred".into(),"id".into(),"id".into(),"coord:r".into(),"coord:c".into()];
        let multi_source:Vec<Value>=points.iter().enumerate().map(|(i,&(x,y))|tuple_of(vec![Value::Int(0),Value::Int(i as i64),Value::Int((i+20) as i64),Value::Int(x),Value::Int(y)])).collect();
        let multi_target:Vec<Value>=points.iter().enumerate().map(|(i,&(x,y))|tuple_of(vec![Value::Int(0),Value::Int(i as i64),Value::Int((i+20) as i64),Value::Int(2*x+y),Value::Int(x-y)])).collect();
        assert!(matches!(infer_exact_2d_linear_prefilter(&multi_source,&multi_target,&multi_types,&[3,4],4),ExactLinearPrefilter::Solved(m) if m==vec![2,1,1,-1]));
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    fn exact_linear_prefilter_recovers_every_matrix_in_small_exhaustive_corpus() {
        let dim_types = vec!["pred".into(), "id".into(), "coord:r".into(), "coord:c".into()];
        let point_sets: [&[(i64,i64)]; 4] = [
            &[(0,0),(1,0),(0,1)],
            &[(0,0),(1,0),(1,1)],
            &[(0,0),(0,1),(1,1)],
            &[(0,0),(1,0),(0,1),(1,1)],
        ];
        let empty_extra: FxHashMap<Sym,String> = FxHashMap::default();
        let mut oracle_hash=0xcbf29ce484222325u64;
        let mut oracle_cases=0u64;
        for (set_idx, points) in point_sets.iter().enumerate() {
            let source: Vec<Value> = points.iter().enumerate().map(|(i, &(x,y))|
                tuple_of(vec![Value::Int(0), Value::Int(i as i64), Value::Int(x), Value::Int(y)])).collect();
            for a in -2i64..=2 { for b in -2i64..=2 { for c in -2i64..=2 { for d in -2i64..=2 {
                let target: Vec<Value> = points.iter().enumerate().map(|(i, &(x,y))|
                    tuple_of(vec![Value::Int(0), Value::Int(i as i64), Value::Int(a*x+b*y), Value::Int(c*x+d*y)])).collect();
                let bound = [2usize,3usize].iter().flat_map(|&slot| {
                    let values: Vec<i64> = target.iter().filter_map(|r| Some(relation_values(r)?.get(slot)?.as_i64())).collect();
                    let min = *values.iter().min()?;
                    Some(values.iter().map(|v| (v-min).abs()).max().unwrap_or(0))
                }).max().unwrap_or(0).max(1);
                let sorted_goal = { let mut v=target.clone(); v.sort_by(cmp_value); v };
                let expected = historical_linear_enum_for_test(&source, &sorted_goal, &dim_types, bound, &empty_extra);
                let actual = match infer_exact_2d_linear_prefilter(&source, &target, &dim_types, &[2,3], bound) {
                    ExactLinearPrefilter::Solved(matrix) if matrix == [1,0,0,1] => None,
                    ExactLinearPrefilter::Solved(matrix) => selected_candidate_for_test(&source, &sorted_goal, &dim_types, matrix, &empty_extra),
                    ExactLinearPrefilter::ProvenNoFit(_) => None,
                    ExactLinearPrefilter::Fallback(_) => historical_linear_enum_for_test(&source, &sorted_goal, &dim_types, bound, &empty_extra),
                };
                assert_eq!(actual, expected, "set {set_idx}, matrix [{a},{b},{c},{d}]");
                let record=match &expected {
                    None => format!("{set_idx}:{a},{b},{c},{d}:none\n"),
                    Some((m,residual,transforms)) => {
                        let ts=transforms.iter().map(|v| match v {
                            Value::Dict(items) => format!("{:?}",items),
                            other => format!("{other:?}"),
                        }).collect::<Vec<_>>().join(";");
                        format!("{set_idx}:{a},{b},{c},{d}:{m:?}:{residual}:{ts}\n")
                    }
                };
                for byte in record.bytes() { oracle_hash=(oracle_hash ^ u64::from(byte)).wrapping_mul(0x100000001b3); }
                oracle_cases+=1;
            }}}}
        }
        println!("GENINFER_PREFILTER_ENUMERATOR_ORACLE cases={oracle_cases} fnv1a64={oracle_hash:016x}");
    }

    /// v1.4 guards: inputs whose enumerator semantics differ from the
    /// identity-joined affine proof must fall back, not be "proved". The
    /// multi-predicate case is a concrete counterexample found by the residual
    /// census: a predicate-local shift is accepted by the enumerator as a
    /// generator-plus-residual decomposition that the old prefilter rejected.
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    fn exact_linear_prefilter_v1_4_guards_fall_back_where_enumerator_semantics_differ() {
        let dim_types = vec!["pred".into(), "id".into(), "coord:r".into(), "coord:c".into()];
        let extra: FxHashMap<Sym,String> = FxHashMap::default();
        // two predicates, M = swap, predicate-1 rows shifted by +1 on r
        let pts = [(0,0,0),(0,1,0),(0,0,1),(1,1,1)];
        let source: Vec<Value> = pts.iter().enumerate().map(|(i,&(p,x,y))| tuple_of(vec![Value::Int(p),Value::Int(i as i64),Value::Int(x),Value::Int(y)])).collect();
        let target: Vec<Value> = pts.iter().enumerate().map(|(i,&(p,x,y))| tuple_of(vec![Value::Int(p),Value::Int(i as i64),Value::Int(y + i64::from(p==1)),Value::Int(x)])).collect();
        let sorted_goal = { let mut v=target.clone(); v.sort_by(cmp_value); v };
        assert!(historical_linear_enum_for_test(&source, &sorted_goal, &dim_types, 2, &extra).is_some(), "enumerator accepts a residual decomposition");
        assert!(matches!(infer_exact_2d_linear_prefilter(&source, &target, &dim_types, &[2,3], 2), ExactLinearPrefilter::Fallback("multiple_predicates")));
        // identity slot after the coordinates: canonical sort is not an identity join
        let late_id = vec!["pred".into(), "coord:r".into(), "coord:c".into(), "id".into()];
        let src: Vec<Value> = [(0,0),(1,0),(0,1)].iter().enumerate().map(|(i,&(x,y))| tuple_of(vec![Value::Int(0),Value::Int(x),Value::Int(y),Value::Int(i as i64)])).collect();
        assert!(matches!(infer_exact_2d_linear_prefilter(&src, &src, &late_id, &[1,2], 2), ExactLinearPrefilter::Fallback("identity_not_sort_prefix")));
        // relation-count mismatch remains an unconditional proof
        let short = src[..2].to_vec();
        assert!(matches!(infer_exact_2d_linear_prefilter(&src, &short, &late_id, &[1,2], 2), ExactLinearPrefilter::ProvenNoFit("relation_count_mismatch")));
    }

    /// Diagnostic differential (not part of the frozen v1.2 oracle): compare
    /// the production prefilter dispatch with the historical enumerator on
    /// targets that are NOT exact linear images — predicate-local shifts,
    /// global translations, single-row perturbations, and identity
    /// relabelings — where the enumerator may accept a generator-plus-residual
    /// decomposition. Prints per-family divergence counts; asserts nothing so
    /// the census itself can be recorded.
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    #[ignore]
    fn exact_linear_prefilter_residual_family_divergence_census() {
        let dim_types = vec!["pred".into(), "id".into(), "coord:r".into(), "coord:c".into()];
        // (pred, x, y); sets 0-2 have two predicates so tier-2 predicate-local
        // residuals exist; sets 3-4 are single-predicate controls where the
        // v1.4 guards admit the exact proof.
        let point_sets: [&[(i64,i64,i64)]; 5] = [
            &[(0,0,0),(0,1,0),(1,0,1),(1,1,1)],
            &[(0,0,0),(0,2,0),(0,0,1),(1,1,1),(1,2,2)],
            &[(0,0,0),(0,1,0),(0,0,1),(1,1,1)],
            &[(0,0,0),(0,1,0),(0,0,1),(0,1,1)],
            &[(0,0,0),(0,2,0),(0,0,1),(0,1,1),(0,2,2)],
        ];
        let empty_extra: FxHashMap<Sym,String> = FxHashMap::default();
        let families = ["exact", "global_translate", "pred1_shift_r", "pred1_shift_c", "single_row_r", "id_swap"];
        for fam in families {
            // index 0 = multi-predicate sets, 1 = single-predicate sets
            let (mut cases, mut agree, mut diverge, mut solved, mut nofit, mut fallback, mut enum_accepts) = ([0u64;2],[0u64;2],[0u64;2],[0u64;2],[0u64;2],[0u64;2],[0u64;2]);
            let mut first: [Option<String>;2] = [None, None];
            for (set_idx, points) in point_sets.iter().enumerate() {
                let k = usize::from(set_idx >= 3);
                let source: Vec<Value> = points.iter().enumerate().map(|(i,&(p,x,y))|
                    tuple_of(vec![Value::Int(p), Value::Int(i as i64), Value::Int(x), Value::Int(y)])).collect();
                for a in -2i64..=2 { for b in -2i64..=2 { for c in -2i64..=2 { for d in -2i64..=2 {
                    if a*d - b*c == 0 { continue; }
                    let mut rows: Vec<(i64,i64,i64,i64)> = points.iter().enumerate().map(|(i,&(p,x,y))| (p, i as i64, a*x+b*y, c*x+d*y)).collect();
                    // normalise to the per-axis min so only the perturbation is residual
                    let mr = rows.iter().map(|r| r.2).min().unwrap();
                    let mc = rows.iter().map(|r| r.3).min().unwrap();
                    for r in rows.iter_mut() { r.2 -= mr; r.3 -= mc; }
                    match fam {
                        "exact" => {}
                        "global_translate" => for r in rows.iter_mut() { r.2 += 3; r.3 -= 2; },
                        "pred1_shift_r" => for r in rows.iter_mut() { if r.0 == 1 { r.2 += 1; } },
                        "pred1_shift_c" => for r in rows.iter_mut() { if r.0 == 1 { r.3 += 1; } },
                        "single_row_r" => { let last = rows.len()-1; rows[last].2 += 1; },
                        "id_swap" => { let (i0, i1) = (rows[0].1, rows[1].1); rows[0].1 = i1; rows[1].1 = i0; },
                        _ => unreachable!(),
                    }
                    let target: Vec<Value> = rows.iter().map(|&(p,i,x,y)| tuple_of(vec![Value::Int(p),Value::Int(i),Value::Int(x),Value::Int(y)])).collect();
                    let extent = |sig: &[Value]| [2usize,3usize].iter().filter_map(|&slot| {
                        let vs = coord_ints(sig, slot)?; let mn = *vs.iter().min()?; vs.iter().map(|v| (v-mn).abs()).max()
                    }).max().unwrap_or(0);
                    let bound = extent(&target).max(extent(&source));
                    if bound <= 0 { continue; }
                    let sorted_goal = { let mut v=target.clone(); v.sort_by(cmp_value); v };
                    let expected = historical_linear_enum_for_test(&source, &sorted_goal, &dim_types, bound, &empty_extra);
                    if expected.is_some() { enum_accepts[k] += 1; }
                    let actual = match infer_exact_2d_linear_prefilter(&source, &target, &dim_types, &[2,3], bound) {
                        ExactLinearPrefilter::Solved(matrix) => { solved[k] += 1; if matrix == [1,0,0,1] { None } else { selected_candidate_for_test(&source, &sorted_goal, &dim_types, matrix, &empty_extra) } },
                        ExactLinearPrefilter::ProvenNoFit(_) => { nofit[k] += 1; None },
                        ExactLinearPrefilter::Fallback(_) => { fallback[k] += 1; expected.clone() },
                    };
                    cases[k] += 1;
                    let _ = set_idx;
                    if actual == expected { agree[k] += 1; } else {
                        diverge[k] += 1;
                        if first[k].is_none() { first[k] = Some(format!("set {set_idx} M=[{a},{b},{c},{d}] expected={:?} actual={:?}", expected.as_ref().map(|e| (&e.0, e.1)), actual.as_ref().map(|e| (&e.0, e.1)))); }
                    }
                }}}}
            }
            for (k, class) in ["multi_predicate", "single_predicate"].iter().enumerate() {
                println!("GENINFER_PREFILTER_RESIDUAL_CENSUS family={fam} class={class} cases={} agree={} diverge={} solved={} no_fit={} fallback={} enumerator_accepts={} first_divergence={}", cases[k], agree[k], diverge[k], solved[k], nofit[k], fallback[k], enum_accepts[k], first[k].clone().unwrap_or_else(|| "none".into()));
                if *class == "single_predicate" { assert_eq!(diverge[k], 0, "single-predicate divergence in {fam}"); }
            }
        }
    }

    /// Production dispatch order for one 2-D base: affine prefilter, then the
    /// row-factorized search, then the historical enumerator.
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    fn production_dispatch_for_test(source: &[Value], target: &[Value], dim_types: &[String], bound: i64, extra: &FxHashMap<Sym,String>, path: &mut [u64; 8]) -> Option<(Vec<i64>,usize,Vec<Value>)> {
        let sorted_goal = { let mut v=target.to_vec(); v.sort_by(cmp_value); v };
        match infer_exact_2d_linear_prefilter(source, target, dim_types, &[2,3], bound) {
            ExactLinearPrefilter::Solved(m) => { path[0] += 1; if m == [1,0,0,1] { None } else { selected_candidate_for_test(source, &sorted_goal, dim_types, m, extra) } }
            ExactLinearPrefilter::ProvenNoFit(_) => { path[1] += 1; None }
            ExactLinearPrefilter::Fallback(_) => {
                let mut work = 0u64;
                match infer_row_factorized_2d_linear(source, &sorted_goal, &[2,3], bound, 2, extra, &mut work) {
                    RowFactorizedSearch::Solved(m, t) => {
                        path[2] += 1;
                        let got = selected_candidate_for_test(source, &sorted_goal, dim_types, m, extra);
                        assert_eq!(got.as_ref().map(|g| g.1), Some(t), "row-factorized winner failed validation");
                        got
                    }
                    RowFactorizedSearch::NoCandidate(_) => { path[3] += 1; None }
                    RowFactorizedSearch::Fallback(_) => {
                        let (mut h, mut v) = (0u64, 0u64);
                        match infer_correspondence_2d_linear("base", &Value::Int(1), source, &sorted_goal, &[2,3], bound, 2, extra, &mut h, &mut v) {
                            CorrespondenceSearch::Found(m, cand) => { path[6] += 1; Some((m, cand.dims_needed.len(), cand.transforms.iter().map(DimTransform::to_value).collect())) }
                            CorrespondenceSearch::NoCandidate(_) => { path[7] += 1; None }
                            CorrespondenceSearch::Fallback(_) => { path[4] += 1; historical_linear_enum_for_test(source, &sorted_goal, dim_types, bound, extra) }
                        }
                    }
                }
            }
        }
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    fn exact_linear_prefilter_row_factorized_matches_enumerator_on_counterexamples() {
        let dim_types = vec!["pred".into(), "id".into(), "coord:r".into(), "coord:c".into()];
        let extra: FxHashMap<Sym,String> = FxHashMap::default();
        let row = |p: i64, i: i64, x: i64, y: i64| tuple_of(vec![Value::Int(p),Value::Int(i),Value::Int(x),Value::Int(y)]);
        let mut path = [0u64; 8];
        // multi-predicate shift (the v1.3 divergence), rank-deficient collinear, missing identity
        let pts = [(0,0,0),(0,1,0),(0,0,1),(1,1,1)];
        let src: Vec<Value> = pts.iter().enumerate().map(|(i,&(p,x,y))| row(p,i as i64,x,y)).collect();
        let shifted: Vec<Value> = pts.iter().enumerate().map(|(i,&(p,x,y))| row(p,i as i64,y + i64::from(p==1),x)).collect();
        let line: Vec<Value> = (0..5).map(|i| row(0,i,i,0)).collect();
        let line_img: Vec<Value> = (0..5).map(|i| row(0,i,2*i,i)).collect();
        let mut orphan = src.clone(); orphan[3] = row(1,99,1,1);
        let csq: Vec<Value> = [(0,0),(1,0),(0,1),(2,1)].iter().map(|&(x,y)| row(0,0,x,y)).collect();
        let crot: Vec<Value> = [(0,0),(1,0),(0,1),(2,1)].iter().map(|&(x,y)| row(0,0,y,2-x)).collect();
        for (s, t) in [(&src, &shifted), (&line, &line_img), (&src, &orphan), (&src, &src), (&csq, &crot), (&csq, &csq)] {
            let extent = |sig: &[Value]| [2usize,3usize].iter().filter_map(|&slot| { let vs = coord_ints(sig, slot)?; let mn = *vs.iter().min()?; vs.iter().map(|v| (v-mn).abs()).max() }).max().unwrap_or(0);
            let bound = extent(t).max(extent(s)).max(1);
            let sorted_goal = { let mut v=t.clone(); v.sort_by(cmp_value); v };
            let expected = historical_linear_enum_for_test(s, &sorted_goal, &dim_types, bound, &extra);
            let actual = production_dispatch_for_test(s, t, &dim_types, bound, &extra, &mut path);
            assert_eq!(actual, expected);
        }
        assert!(path[2] + path[3] >= 3 && path[6] + path[7] >= 2, "row-factorized and correspondence paths exercised: {path:?}");
    }

    /// Ignored census: full production dispatch versus the historical
    /// enumerator over residual families, multi-predicate, rank-deficient and
    /// identity-perturbed inputs. Every case must agree.
    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    #[test]
    #[ignore]
    fn exact_linear_prefilter_row_factorized_matches_enumerator_census() {
        let dim_types = vec!["pred".into(), "id".into(), "coord:r".into(), "coord:c".into()];
        let point_sets: [&[(i64,i64,i64)]; 6] = [
            &[(0,0,0),(0,1,0),(1,0,1),(1,1,1)],
            &[(0,0,0),(0,2,0),(0,0,1),(1,1,1),(1,2,2)],
            &[(0,0,0),(0,1,0),(0,0,1),(0,1,1)],
            &[(0,0,0),(0,1,1),(0,2,2),(0,3,3)],          // rank 1
            &[(0,0,0),(0,1,0),(1,2,0),(1,3,0)],          // rank 1, two predicates
            &[(0,0,0),(0,0,0),(0,1,0),(0,0,1)],          // repeated coordinates, unique ids
        ];
        let extra: FxHashMap<Sym,String> = FxHashMap::default();
        let families = ["exact", "global_translate", "pred1_shift_r", "single_row_r", "id_swap", "missing_id", "duplicate_id", "constant_id_exact", "constant_id_pred1_shift_r", "constant_id_single_row_r"];
        let mut total_div = 0u64;
        for fam in families {
            let (mut cases, mut diverge) = (0u64, 0u64);
            let mut path = [0u64; 8];
            let mut first: Option<String> = None;
            for (set_idx, points) in point_sets.iter().enumerate() {
                let mut source: Vec<Value> = points.iter().enumerate().map(|(i,&(p,x,y))|
                    tuple_of(vec![Value::Int(p), Value::Int(i as i64), Value::Int(x), Value::Int(y)])).collect();
                if fam.starts_with("constant_id") { for r in source.iter_mut() { let t = relation_values(r).unwrap().to_vec(); *r = tuple_of(vec![t[0].clone(), Value::Int(0), t[2].clone(), t[3].clone()]); } }
                if fam == "duplicate_id" { let last = source.len()-1; let (p,_,x,y) = (points[last].0, 0, points[last].1, points[last].2); source[last] = tuple_of(vec![Value::Int(p),Value::Int(0),Value::Int(x),Value::Int(y)]); }
                for a in -2i64..=2 { for b in -2i64..=2 { for c in -2i64..=2 { for d in -2i64..=2 {
                    let mut rows: Vec<(i64,i64,i64,i64)> = points.iter().enumerate().map(|(i,&(p,x,y))| (p, i as i64, a*x+b*y, c*x+d*y)).collect();
                    let mr = rows.iter().map(|r| r.2).min().unwrap();
                    let mc = rows.iter().map(|r| r.3).min().unwrap();
                    for r in rows.iter_mut() { r.2 -= mr; r.3 -= mc; }
                    match fam {
                        "exact" | "duplicate_id" | "constant_id_exact" => {}
                        "constant_id_pred1_shift_r" => for r in rows.iter_mut() { if r.0 == 1 { r.2 += 1; } },
                        "constant_id_single_row_r" => { let last = rows.len()-1; rows[last].2 += 1; },
                        "global_translate" => for r in rows.iter_mut() { r.2 += 3; r.3 -= 2; },
                        "pred1_shift_r" => for r in rows.iter_mut() { if r.0 == 1 { r.2 += 1; } },
                        "single_row_r" => { let last = rows.len()-1; rows[last].2 += 1; },
                        "id_swap" => { let (i0, i1) = (rows[0].1, rows[1].1); rows[0].1 = i1; rows[1].1 = i0; },
                        "missing_id" => { let last = rows.len()-1; rows[last].1 = 99; },
                        _ => unreachable!(),
                    }
                    if fam.starts_with("constant_id") { for r in rows.iter_mut() { r.1 = 0; } }
                    let target: Vec<Value> = rows.iter().map(|&(p,i,x,y)| tuple_of(vec![Value::Int(p),Value::Int(i),Value::Int(x),Value::Int(y)])).collect();
                    let extent = |sig: &[Value]| [2usize,3usize].iter().filter_map(|&slot| {
                        let vs = coord_ints(sig, slot)?; let mn = *vs.iter().min()?; vs.iter().map(|v| (v-mn).abs()).max()
                    }).max().unwrap_or(0);
                    let bound = extent(&target).max(extent(&source));
                    if bound <= 0 { continue; }
                    let sorted_goal = { let mut v=target.clone(); v.sort_by(cmp_value); v };
                    let expected = historical_linear_enum_for_test(&source, &sorted_goal, &dim_types, bound, &extra);
                    if expected.is_some() { path[5] += 1; }
                    let actual = production_dispatch_for_test(&source, &target, &dim_types, bound, &extra, &mut path);
                    cases += 1;
                    if actual != expected {
                        diverge += 1;
                        if first.is_none() { first = Some(format!("set {set_idx} M=[{a},{b},{c},{d}] expected={:?} actual={:?}", expected.as_ref().map(|e| (&e.0, e.1)), actual.as_ref().map(|e| (&e.0, e.1)))); }
                    }
                }}}}
            }
            println!("GENINFER_ROW_FACTORIZED_CENSUS family={fam} cases={cases} diverge={diverge} affine_solved={} affine_no_fit={} rowf_solved={} rowf_no_candidate={} corr_found={} corr_no_candidate={} enumerator_fallback={} enumerator_accepts={} first_divergence={}", path[0], path[1], path[2], path[3], path[6], path[7], path[4], path[5], first.unwrap_or_else(|| "none".into()));
            total_div += diverge;
        }
        assert_eq!(total_div, 0);
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    fn selected_candidate_for_test(source: &[Value], sorted_goal: &[Value], dim_types: &[String], matrix: Vec<i64>, extra: &FxHashMap<Sym,String>) -> Option<(Vec<i64>,usize,Vec<Value>)> {
        let dims = vec![2,3];
        let transformed = apply_linear_once(source, &dims, &matrix)?;
        let candidate = build_candidate("base".into(), Value::Int(1), &transformed, sorted_goal, 2, extra, false)?;
        if candidate.transforms.len() != candidate.dims_needed.len() { return None; }
        let _ = dim_types;
        Some((matrix,candidate.dims_needed.len(),candidate.transforms.iter().map(DimTransform::to_value).collect()))
    }

    #[cfg(feature = "geninfer_linear_exact_prefilter")]
    fn historical_linear_enum_for_test(source: &[Value], sorted_goal: &[Value], _dim_types: &[String], bound: i64, extra: &FxHashMap<Sym,String>) -> Option<(Vec<i64>,usize,Vec<Value>)> {
        let dims=vec![2,3];
        let mut best: Option<(Vec<i64>,usize,Vec<Value>,i64)> = None;
        for a in -bound..=bound { for b in -bound..=bound { for c in -bound..=bound { for d in -bound..=bound {
            if [a,b,c,d] == [1,0,0,1] { continue; }
            let matrix=vec![a,b,c,d];
            let Some(transformed)=apply_linear_once(source,&dims,&matrix) else { continue };
            let Some(candidate)=build_candidate("base".into(),Value::Int(1),&transformed,sorted_goal,2,extra,false) else { continue };
            if candidate.transforms.len()!=candidate.dims_needed.len() { continue; }
            let residual=candidate.dims_needed.len();
            let abs_sum=matrix.iter().map(|x|x.abs()).sum::<i64>();
            let key=(residual,abs_sum,&matrix);
            if best.as_ref().is_none_or(|(m,r,_,s)| key < (*r,*s,m)) {
                best=Some((matrix,residual,candidate.transforms.iter().map(DimTransform::to_value).collect(),abs_sum));
            }
        }}}}
        best.map(|(m,r,t,_)|(m,r,t))
    }

    /// `name`/`signature`/`kind` ShapeSignature node, mirroring
    /// `_load_shape_signatures`'s expected attr shape.
    fn add_part(g: &mut TypedGraph, ir: &mut Interner, t: Sym, name: &str, sig: Value) -> NodeID {
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("name"), Value::Str(ir.intern(name)));
        attrs.insert(ir.intern("signature"), sig);
        attrs.insert(ir.intern("kind"), Value::Str(ir.intern("faculty")));
        g.insert_node(t, attrs)
    }

    /// One relation tuple, e.g. `rel(ir, &["p", "a", "b"])` == `("p","a","b")`.
    fn rel(ir: &mut Interner, parts: &[&str]) -> Value {
        let v: SmallVec<[Value; 4]> = parts.iter().map(|s| Value::Str(ir.intern(s))).collect();
        Value::Tuple(Arc::new(v))
    }

    fn tuple_of(items: Vec<Value>) -> Value {
        let v: SmallVec<[Value; 4]> = items.into_iter().collect();
        Value::Tuple(Arc::new(v))
    }

    /// Read one key out of a `ShapeDecode` result Dict (or `Value::None`
    /// if absent) — the test-side twin of `select_field`, used to assert
    /// on individual fields without depending on Dict key ORDER (the
    /// crate's `Value::Dict` equality is a positional slice compare,
    /// which is stricter than the Python dict equality the real caller
    /// sees — asserting field-by-field sidesteps that entirely).
    fn dict_get(v: &Value, key: &str) -> Value {
        if let Value::Dict(pairs) = v {
            for (k, val) in pairs.iter() {
                if let Value::Surface(SurfaceKind::Text, bytes) = k {
                    if bytes.as_ref() == key.as_bytes() {
                        return val.clone();
                    }
                }
            }
        }
        Value::None
    }

    #[allow(clippy::too_many_arguments)]
    fn build_decode_term(
        a: &mut TermArena,
        ir: &mut Interner,
        goal: Value,
        codebook_type: Sym,
        exclude: Option<Value>,
        beam: i64,
        max_steps: i64,
        cand_k: i64,
        field: &str,
        wild_objects: bool,
    ) -> TermIdx {
        let goal_t = a.add(TermNode::Lit { value: goal });
        let exclude_t = exclude.map(|e| a.add(TermNode::Lit { value: e }));
        let field_sym = if field.is_empty() {
            Sym::default()
        } else {
            ir.intern(field)
        };
        a.add(TermNode::ShapeDecode {
            goal: goal_t,
            codebook_type,
            exclude: exclude_t,
            codebook_scope: None,
            beam,
            max_steps,
            cand_k,
            budget: 0,
            field: field_sym,
            wild: ir.intern("·?·"),
            wild_objects,
        })
    }

    /// The shared 3-part / 4-relation fixture used by several tests
    /// below (see the module's hand-trace in the PR description): goal
    /// = [R1("p","a","b"), R2("q","b","c"), R3("r","c","d"),
    /// R4("s","d","e")]; PartA/B/C cover R1/R2/R3 respectively (each a
    /// ONE-relation signature identical to the relation it covers); R4
    /// is never covered by anything. Hand-traced result (beam=3,
    /// max_steps=8, cand_k=3): plan = [A, B, C] in that order (each
    /// step's `shape_fit` = 3, the front-aligned part always matches
    /// its own relation exactly since the residual is a prefix-order
    /// filter of the goal); `total_fit` = 9; `residual` = [R4];
    /// `covered_count` = 3.
    struct Fixture {
        g: TypedGraph,
        ir: Interner,
        codebook_type: Sym,
        goal: Value,
        r1: Value,
        r2: Value,
        r3: Value,
        r4: Value,
    }

    fn build_fixture() -> Fixture {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let r1 = rel(&mut ir, &["p", "a", "b"]);
        let r2 = rel(&mut ir, &["q", "b", "c"]);
        let r3 = rel(&mut ir, &["r", "c", "d"]);
        let r4 = rel(&mut ir, &["s", "d", "e"]);
        add_part(&mut g, &mut ir, t, "PartA", tuple_of(vec![r1.clone()]));
        add_part(&mut g, &mut ir, t, "PartB", tuple_of(vec![r2.clone()]));
        add_part(&mut g, &mut ir, t, "PartC", tuple_of(vec![r3.clone()]));
        let goal = tuple_of(vec![r1.clone(), r2.clone(), r3.clone(), r4.clone()]);
        Fixture {
            g,
            ir,
            codebook_type: t,
            goal,
            r1,
            r2,
            r3,
            r4,
        }
    }

    /// (1) Parity with a hand-computed example: 3 parts, 4-relation
    /// goal, beam=3/cand_k=3. See `Fixture`'s doc for the full trace.
    #[test]
    fn parity_hand_computed_example() {
        let mut fx = build_fixture();
        let mut a = TermArena::new();
        let idx = build_decode_term(
            &mut a,
            &mut fx.ir,
            fx.goal.clone(),
            fx.codebook_type,
            None,
            3,
            8,
            3,
            "",
            false,
        );
        let mut env: Env = Env::new();
        let result = {
            let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };

        assert_eq!(dict_get(&result, "authored"), Value::Bool(true));
        assert_eq!(dict_get(&result, "goal_relations"), Value::Int(4));
        assert_eq!(dict_get(&result, "covered_count"), Value::Int(3));
        assert_eq!(dict_get(&result, "total_fit"), Value::Int(9));
        assert_eq!(dict_get(&result, "beam"), Value::Int(3));
        assert_eq!(dict_get(&result, "residual"), tuple_of(vec![fx.r4.clone()]));
        assert_eq!(
            dict_get(&result, "covered"),
            tuple_of(vec![fx.r1.clone(), fx.r2.clone(), fx.r3.clone()])
        );

        let ordered_parts = dict_get(&result, "ordered_parts");
        let expect_names = tuple_of(vec![
            Value::Str(fx.ir.intern("PartA")),
            Value::Str(fx.ir.intern("PartB")),
            Value::Str(fx.ir.intern("PartC")),
        ]);
        assert_eq!(ordered_parts, expect_names);

        let (Value::Tuple(plan) | Value::List(plan)) = dict_get(&result, "plan") else {
            panic!("plan must be a Tuple")
        };
        assert_eq!(plan.len(), 3);
        let step1 = &plan[0];
        assert_eq!(dict_get(step1, "step"), Value::Int(1));
        assert_eq!(dict_get(step1, "part"), Value::Str(fx.ir.intern("PartA")));
        assert_eq!(dict_get(step1, "shape_fit"), Value::Int(3));
        assert_eq!(dict_get(step1, "covers"), tuple_of(vec![fx.r1.clone()]));
        let Value::Surface(SurfaceKind::Text, why_bytes) = dict_get(step1, "why") else {
            panic!("why must be Surface text")
        };
        let why = std::str::from_utf8(&why_bytes).unwrap().to_string();
        assert_eq!(
            why,
            "the held shape-matcher rated 'PartA' fit 3 and its Covers Term accepts 1 residual relation(s)"
        );
    }

    /// (2) `beam=1, cand_k=1` is the discriminative greedy control — on
    /// this fixture the greedy single-choice-per-step trace happens to
    /// reach the SAME optimum as beam=3 (no backtracking was needed:
    /// each step's single best candidate is unambiguous), which is
    /// itself a useful check that the degenerate beam path is wired
    /// correctly (not merely "doesn't panic").
    #[test]
    fn greedy_degenerate_beam1_cand1_matches() {
        let mut fx = build_fixture();
        let mut a = TermArena::new();
        let idx = build_decode_term(
            &mut a,
            &mut fx.ir,
            fx.goal.clone(),
            fx.codebook_type,
            None,
            1,
            8,
            1,
            "",
            false,
        );
        let mut env: Env = Env::new();
        let result = {
            let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };
        assert_eq!(dict_get(&result, "authored"), Value::Bool(true));
        assert_eq!(dict_get(&result, "beam"), Value::Int(1));
        assert_eq!(dict_get(&result, "total_fit"), Value::Int(9));
        assert_eq!(dict_get(&result, "covered_count"), Value::Int(3));
        assert_eq!(dict_get(&result, "residual"), tuple_of(vec![fx.r4.clone()]));
        assert_eq!(
            dict_get(&result, "ordered_parts"),
            tuple_of(vec![
                Value::Str(fx.ir.intern("PartA")),
                Value::Str(fx.ir.intern("PartB")),
                Value::Str(fx.ir.intern("PartC")),
            ])
        );
    }

    /// (3) `exclude` is honored: dropping "PartB" from the pool leaves
    /// R2 (and R4) permanently uncovered — `covered_count` drops from 3
    /// to 2 and "PartB" never appears in `ordered_parts`.
    #[test]
    fn exclude_is_honored() {
        let mut fx = build_fixture();
        let mut a = TermArena::new();
        let excl = Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(
            fx.ir.intern("PartB")
        )]));
        let idx = build_decode_term(
            &mut a,
            &mut fx.ir,
            fx.goal.clone(),
            fx.codebook_type,
            Some(excl),
            3,
            8,
            3,
            "",
            false,
        );
        let mut env: Env = Env::new();
        let result = {
            let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };
        assert_eq!(dict_get(&result, "authored"), Value::Bool(true));
        assert_eq!(dict_get(&result, "covered_count"), Value::Int(2));
        assert_eq!(dict_get(&result, "total_fit"), Value::Int(3));
        assert_eq!(
            dict_get(&result, "residual"),
            tuple_of(vec![fx.r2.clone(), fx.r4.clone()])
        );
        let ordered_parts = dict_get(&result, "ordered_parts");
        let (Value::Tuple(names) | Value::List(names)) = &ordered_parts else {
            panic!("ordered_parts must be a Tuple")
        };
        let part_b = Value::Str(fx.ir.intern("PartB"));
        assert!(
            !names.iter().any(|v| *v == part_b),
            "excluded part must not appear in ordered_parts"
        );
        assert_eq!(
            ordered_parts,
            tuple_of(vec![
                Value::Str(fx.ir.intern("PartA")),
                Value::Str(fx.ir.intern("PartC"))
            ])
        );
    }

    /// (4) Empty parts / empty goal both wall honestly (`authored:
    /// false`), matching `compose_design_for_goal`'s two early-return
    /// reasons.
    #[test]
    fn empty_parts_or_empty_goal_returns_unauthored() {
        // No codebook nodes at all.
        {
            let mut ir = Interner::new();
            let g = TypedGraph::new();
            let t = ir.intern("ShapeSignature");
            let mut a = TermArena::new();
            let goal = tuple_of(vec![rel(&mut ir, &["p", "a", "b"])]);
            let idx = build_decode_term(&mut a, &mut ir, goal, t, None, 3, 8, 3, "", false);
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&g, &ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(dict_get(&result, "authored"), Value::Bool(false));
        }
        // Parts exist, but the goal is empty.
        {
            let mut fx = build_fixture();
            let mut a = TermArena::new();
            let idx = build_decode_term(
                &mut a,
                &mut fx.ir,
                tuple_of(vec![]),
                fx.codebook_type,
                None,
                3,
                8,
                3,
                "",
                false,
            );
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(dict_get(&result, "authored"), Value::Bool(false));
        }
    }

    /// (5) A `signature` attr stored as a JSON string decodes to the
    /// exact same score as one stored natively (a `Value::Tuple`) — the
    /// two codebook representations `_load_shape_signatures` accepted
    /// in Python must be equivalent here too.
    #[test]
    fn json_string_and_native_signature_both_decode() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t_json = ir.intern("SigJson");
        let t_native = ir.intern("SigNative");

        let json_text = ir.intern(r#"[["p","x","y"]]"#);
        add_part(&mut g, &mut ir, t_json, "PartJson", Value::Str(json_text));

        let native_sig = tuple_of(vec![rel(&mut ir, &["p", "x", "y"])]);
        add_part(&mut g, &mut ir, t_native, "PartNative", native_sig);

        let goal = tuple_of(vec![rel(&mut ir, &["p", "x", "y"])]);

        for (label, codebook_type) in [("json", t_json), ("native", t_native)] {
            let mut a = TermArena::new();
            let idx = build_decode_term(
                &mut a,
                &mut ir,
                goal.clone(),
                codebook_type,
                None,
                3,
                8,
                3,
                "",
                false,
            );
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&g, &ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(
                dict_get(&result, "authored"),
                Value::Bool(true),
                "{label} authored"
            );
            assert_eq!(
                dict_get(&result, "covered_count"),
                Value::Int(1),
                "{label} covered_count"
            );
            assert_eq!(
                dict_get(&result, "total_fit"),
                Value::Int(3),
                "{label} total_fit"
            );
            assert_eq!(
                dict_get(&result, "residual"),
                tuple_of(vec![]),
                "{label} residual"
            );
        }
    }

    /// (6) `field` selection: a seed rule's `Computed` effect can read
    /// one Dict key straight off a decode. Covers plain-key selection
    /// (`residual`/`covered_count`/`authored`) and the derived
    /// `covered_by` convenience field (Some for a fully-covering
    /// ONE-part plan, None otherwise — including a fully-covering
    /// MULTI-part plan).
    #[test]
    fn field_selection() {
        let mut fx = build_fixture();

        // Plain-key selection on the partial-cover fixture.
        {
            let mut a = TermArena::new();
            let idx = build_decode_term(
                &mut a,
                &mut fx.ir,
                fx.goal.clone(),
                fx.codebook_type,
                None,
                3,
                8,
                3,
                "residual",
                false,
            );
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(result, tuple_of(vec![fx.r4.clone()]));
        }
        {
            let mut a = TermArena::new();
            let idx = build_decode_term(
                &mut a,
                &mut fx.ir,
                fx.goal.clone(),
                fx.codebook_type,
                None,
                3,
                8,
                3,
                "covered_count",
                false,
            );
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(result, Value::Int(3));
        }
        // Not fully covered -> covered_by is None even though a plan exists.
        {
            let mut a = TermArena::new();
            let idx = build_decode_term(
                &mut a,
                &mut fx.ir,
                fx.goal.clone(),
                fx.codebook_type,
                None,
                3,
                8,
                3,
                "covered_by",
                false,
            );
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(result, Value::None);
        }
        // Fully covered by a MULTI-part plan (2 parts) -> covered_by is
        // still None (the convenience form is one-part-only).
        {
            let mut a = TermArena::new();
            let two_rel_goal = tuple_of(vec![fx.r1.clone(), fx.r2.clone()]);
            let idx = build_decode_term(
                &mut a,
                &mut fx.ir,
                two_rel_goal,
                fx.codebook_type,
                None,
                3,
                8,
                3,
                "covered_by",
                false,
            );
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(result, Value::None);
        }
        // Fully covered by a ONE-part plan -> covered_by is that part's name.
        {
            let mut a = TermArena::new();
            let one_rel_goal = tuple_of(vec![fx.r1.clone()]);
            let idx = build_decode_term(
                &mut a,
                &mut fx.ir,
                one_rel_goal,
                fx.codebook_type,
                None,
                3,
                8,
                3,
                "covered_by",
                false,
            );
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&fx.g, &fx.ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(result, Value::Str(fx.ir.intern("PartA")));
        }
    }

    /// `field` selection also degrades honestly on a wall result (no
    /// held parts): unknown/absent keys read as `None`, `authored`
    /// still reads `false`.
    #[test]
    fn field_selection_on_wall() {
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let mut a = TermArena::new();
        let goal = tuple_of(vec![rel(&mut ir, &["p", "a", "b"])]);
        let idx = build_decode_term(&mut a, &mut ir, goal, t, None, 3, 8, 3, "authored", false);
        let mut env: Env = Env::new();
        let result = {
            let mut ctx = EvalCtx::new(&g, &ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };
        assert_eq!(result, Value::Bool(false));
    }

    /// (7) `wild_objects` — the SECOND coverage semantics
    /// (`induce_concern`'s pre-migration `_held_coverage_patterns`): a
    /// part whose signature is `[["build","NEW","from","PRIOR"]]`
    /// COVERS an observation `[["build","X","from","Y"]]` (same
    /// predicate + arity, different literal fillers) when
    /// `wild_objects=true` (recognized: empty residual, one-part plan,
    /// `covered_by` = the part's name) but NOT when `wild_objects=false`
    /// (the composer's literal default — the residual stays non-empty,
    /// nothing recognized). This is the discriminative pair the Rust fix
    /// must produce (see `tests/fixtures/composer_driver_parity/
    /// induce_concern.json`'s `covered` case, which this mirrors: object
    /// slots differ, predicate skeleton matches).
    #[test]
    fn wild_objects_covers_predicate_skeleton_only() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let part_rel = rel(&mut ir, &["build", "NEW", "from", "PRIOR"]);
        add_part(&mut g, &mut ir, t, "part_build", tuple_of(vec![part_rel]));
        let goal_rel = rel(&mut ir, &["build", "X", "from", "Y"]);
        let goal = tuple_of(vec![goal_rel.clone()]);

        // wild_objects=true: predicate-skeleton coverage — recognized.
        {
            let mut a = TermArena::new();
            let idx = build_decode_term(&mut a, &mut ir, goal.clone(), t, None, 3, 8, 3, "", true);
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&g, &ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(dict_get(&result, "authored"), Value::Bool(true));
            assert_eq!(
                dict_get(&result, "residual"),
                tuple_of(vec![]),
                "wild_objects=true must fully cover"
            );
            assert_eq!(dict_get(&result, "covered_count"), Value::Int(1));

            // `covered_by` is a DERIVED field (see `select_field`) — only
            // materializes via an explicit `field` selector, exactly the
            // `induce_concern`-covered-branch convenience form `sd_recognize`
            // reads.
            let mut a2 = TermArena::new();
            let idx2 = build_decode_term(
                &mut a2,
                &mut ir,
                goal.clone(),
                t,
                None,
                3,
                8,
                3,
                "covered_by",
                true,
            );
            let mut env2: Env = Env::new();
            let covered_by = {
                let mut ctx = EvalCtx::new(&g, &ir);
                evaluate(&a2, idx2, &mut env2, &mut ctx)
            };
            assert_eq!(covered_by, Value::Str(ir.intern("part_build")));
        }
        // wild_objects=false (default): literal fillers differ — NOT covered.
        {
            let mut a = TermArena::new();
            let idx = build_decode_term(&mut a, &mut ir, goal.clone(), t, None, 3, 8, 3, "", false);
            let mut env: Env = Env::new();
            let result = {
                let mut ctx = EvalCtx::new(&g, &ir);
                evaluate(&a, idx, &mut env, &mut ctx)
            };
            assert_eq!(
                dict_get(&result, "residual"),
                tuple_of(vec![goal_rel.clone()]),
                "wild_objects=false must NOT cover a literal-filler mismatch"
            );
            assert_eq!(dict_get(&result, "covered_count"), Value::Int(0));

            let mut a2 = TermArena::new();
            let idx2 = build_decode_term(
                &mut a2,
                &mut ir,
                goal.clone(),
                t,
                None,
                3,
                8,
                3,
                "covered_by",
                false,
            );
            let mut env2: Env = Env::new();
            let covered_by = {
                let mut ctx = EvalCtx::new(&g, &ir);
                evaluate(&a2, idx2, &mut env2, &mut ctx)
            };
            assert_eq!(covered_by, Value::None);
        }
    }

    // --- GAMMA_SEARCH_COMPLETENESS_FIXES.md Bug 2 ------------------------
    // The discriminating fixture: `scripts/probe_beam_completeness.py`'s
    // own greedy-set-cover adversarial construction (Johnson 1974 shape),
    // transplanted verbatim as a native Rust unit test so the fix is
    // gated at the same layer as the bug. `beam=1` previously discarded
    // the OPTIMAL step-1 states permanently (never re-entering `frontier`
    // for step 2); this test proves that no longer happens.

    #[allow(clippy::too_many_arguments)]
    fn build_decode_term_budgeted(
        a: &mut TermArena,
        ir: &mut Interner,
        goal: Value,
        codebook_type: Sym,
        beam: i64,
        max_steps: i64,
        cand_k: i64,
        budget: i64,
    ) -> TermIdx {
        let goal_t = a.add(TermNode::Lit { value: goal });
        a.add(TermNode::ShapeDecode {
            goal: goal_t,
            codebook_type,
            exclude: None,
            codebook_scope: None,
            beam,
            max_steps,
            cand_k,
            budget,
            field: Sym::default(),
            wild: ir.intern("·?·"),
            wild_objects: false,
        })
    }

    /// The beam trap: `part_A={g1,g2}` + `part_B={g3,g4}` is the OPTIMAL,
    /// disjoint, fully-covering 2-part plan; `part_C={g1,g3}` TIES on
    /// coverage at step 1 (covers 2 of 4) and wins the `shape_fit`
    /// tie-break by construction (position-aligned with `goal[0:2]`), but
    /// then needs 2 MORE single-relation parts to finish — impossible
    /// within `max_steps=2`. A width-1 beam that keeps only the
    /// higher-fit `part_C` survivor after step 1 can never reach the
    /// optimal plan; a search that does not discard `part_A`/`part_B`'s
    /// states can.
    fn build_beam_trap() -> (TypedGraph, Interner, Sym, Value) {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let g1 = rel(&mut ir, &["e", "1"]);
        let g2 = rel(&mut ir, &["e", "2"]);
        let g3 = rel(&mut ir, &["e", "3"]);
        let g4 = rel(&mut ir, &["e", "4"]);
        add_part(
            &mut g,
            &mut ir,
            t,
            "part_A",
            tuple_of(vec![g1.clone(), g2.clone()]),
        );
        add_part(
            &mut g,
            &mut ir,
            t,
            "part_B",
            tuple_of(vec![g3.clone(), g4.clone()]),
        );
        add_part(
            &mut g,
            &mut ir,
            t,
            "part_C",
            tuple_of(vec![g1.clone(), g3.clone()]),
        );
        add_part(&mut g, &mut ir, t, "part_only2", tuple_of(vec![g2.clone()]));
        add_part(&mut g, &mut ir, t, "part_only4", tuple_of(vec![g4.clone()]));
        let goal = tuple_of(vec![g1, g3, g2, g4]);
        (g, ir, t, goal)
    }

    /// THE FIX, live: `beam=1` (the exact width that used to lose the
    /// optimal plan) now finds the complete, 4/4-covering plan — because
    /// `beam` no longer truncates the frontier; only the (generously
    /// default-budgeted) total expansion count can, and this fixture is
    /// nowhere near that budget.
    #[test]
    fn beam1_no_longer_loses_the_optimal_plan() {
        let (g, mut ir, t, goal) = build_beam_trap();
        let mut a = TermArena::new();
        let idx = build_decode_term_budgeted(
            &mut a, &mut ir, goal, t, /*beam*/ 1, /*max_steps*/ 2, /*cand_k*/ 5,
            /*budget*/ 0,
        );
        let mut env: Env = Env::new();
        let result = {
            let mut ctx = EvalCtx::new(&g, &ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };
        assert_eq!(dict_get(&result, "authored"), Value::Bool(true));
        assert_eq!(dict_get(&result, "goal_relations"), Value::Int(4));
        assert_eq!(
            dict_get(&result, "covered_count"),
            Value::Int(4),
            "beam=1 must now reach FULL coverage (was 3/4 before the fix — \
                    scripts/probe_beam_completeness.py's live-verified 'before' number)"
        );
        assert_eq!(dict_get(&result, "residual"), tuple_of(vec![]));
        assert_eq!(
            dict_get(&result, "budget_exhausted"),
            Value::Bool(false),
            "this tiny fixture must complete well inside the default budget"
        );
        // `beam` is still reported (back-compat) even though it no longer prunes.
        assert_eq!(dict_get(&result, "beam"), Value::Int(1));
    }

    /// Sanity twin: `beam=3` (already-complete pre-fix behaviour, per the
    /// ceiling-probe doc's live-verified table) is UNCHANGED by the fix —
    /// same fully-covering plan, same shape.
    #[test]
    fn beam3_still_finds_the_optimal_plan() {
        let (g, mut ir, t, goal) = build_beam_trap();
        let mut a = TermArena::new();
        let idx = build_decode_term_budgeted(&mut a, &mut ir, goal, t, 3, 2, 5, 0);
        let mut env: Env = Env::new();
        let result = {
            let mut ctx = EvalCtx::new(&g, &ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };
        assert_eq!(dict_get(&result, "covered_count"), Value::Int(4));
        assert_eq!(dict_get(&result, "residual"), tuple_of(vec![]));
    }

    /// THE HONESTY FLAG: an artificially starved budget (1 expansion —
    /// less than even one step's worth of children on this fixture) must
    /// still return SOME result (never panic/hang) and must flag
    /// `budget_exhausted: true` rather than reporting a partial plan
    /// identically to a genuinely-exhausted-within-`max_steps` one.
    #[test]
    fn starved_budget_is_flagged_honestly() {
        let (g, mut ir, t, goal) = build_beam_trap();
        let mut a = TermArena::new();
        let idx = build_decode_term_budgeted(&mut a, &mut ir, goal, t, 1, 2, 5, /*budget*/ 1);
        let mut env: Env = Env::new();
        let result = {
            let mut ctx = EvalCtx::new(&g, &ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };
        assert_eq!(dict_get(&result, "budget_exhausted"), Value::Bool(true));
        // Whatever plan it DID find (the single candidate the 1-expansion
        // budget allowed) is still reported, not thrown away.
        assert_eq!(dict_get(&result, "authored"), Value::Bool(true));
    }

    /// A budget generous enough for step 1 (5 candidates: part_A, part_B,
    /// part_C, each contribute; the fifth+ discarded by `cand_k` not
    /// budget) but starved before step 2 can complete the optimal plan
    /// must ALSO flag `budget_exhausted: true` — proving the flag reflects
    /// genuine exhaustion, not just "budget=1".
    #[test]
    fn mid_search_budget_exhaustion_is_flagged() {
        let (g, mut ir, t, goal) = build_beam_trap();
        let mut a = TermArena::new();
        // 3 candidates possible at step 1 (part_A, part_B, part_C each
        // cover something); budget=3 exhausts exactly after step 1, before
        // any step-2 child (including the optimal-completing one) exists.
        let idx = build_decode_term_budgeted(&mut a, &mut ir, goal, t, 1, 2, 5, 3);
        let mut env: Env = Env::new();
        let result = {
            let mut ctx = EvalCtx::new(&g, &ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };
        assert_eq!(dict_get(&result, "budget_exhausted"), Value::Bool(true));
        assert_eq!(
            dict_get(&result, "covered_count"),
            Value::Int(2),
            "budget=3 affords exactly the 3 step-1 candidates, all covering 2/4 -- \
                    none has had a chance to spawn a step-2 child yet"
        );
    }
}

/// `TransformDecode` tests — the quantum-delta twin's own fixtures. Kept
/// as a sibling module (not reusing `mod tests`' private helpers) so
/// each test is self-contained; the tiny `add_part`/`rel`/`tuple_of`/
/// `dict_get` helpers below mirror `mod tests`'s (test-only, not the
/// production codebook/signature-parsing helpers `TransformDecode`
/// itself reuses from `load_parts`/`json_to_value_scoped`).
#[cfg(test)]
mod transform_decode_tests {
    use super::*;
    use crate::graph::{NodeID, TypedGraph};
    use crate::term::TermNode;

    fn add_part(g: &mut TypedGraph, ir: &mut Interner, t: Sym, name: &str, sig: Value) -> NodeID {
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("name"), Value::Str(ir.intern(name)));
        attrs.insert(ir.intern("signature"), sig);
        attrs.insert(ir.intern("kind"), Value::Str(ir.intern("faculty")));
        g.insert_node(t, attrs)
    }

    /// A relation tuple whose predicate is a Str and whose remaining
    /// slots are given as pre-built `Value`s (so a test can mix Str and
    /// Int slots freely — the grid fixtures need both).
    fn rel_vals(ir: &mut Interner, pred: &str, rest: Vec<Value>) -> Value {
        let mut v: SmallVec<[Value; 4]> = smallvec::smallvec![Value::Str(ir.intern(pred))];
        v.extend(rest);
        Value::Tuple(Arc::new(v))
    }

    /// All-Str relation tuple — the common case for symbolic fixtures.
    fn rel(ir: &mut Interner, parts: &[&str]) -> Value {
        let v: SmallVec<[Value; 4]> = parts.iter().map(|s| Value::Str(ir.intern(s))).collect();
        Value::Tuple(Arc::new(v))
    }

    fn tuple_of(items: Vec<Value>) -> Value {
        let v: SmallVec<[Value; 4]> = items.into_iter().collect();
        Value::Tuple(Arc::new(v))
    }

    fn dict_get(v: &Value, key: &str) -> Value {
        if let Value::Dict(pairs) = v {
            for (k, val) in pairs.iter() {
                if let Value::Surface(SurfaceKind::Text, bytes) = k {
                    if bytes.as_ref() == key.as_bytes() {
                        return val.clone();
                    }
                }
            }
        }
        Value::None
    }

    fn build_transform_term(
        a: &mut TermArena,
        ir: &mut Interner,
        goal: Value,
        codebook_type: Sym,
        exclude: Option<Value>,
        max_dims: i64,
        field: &str,
    ) -> TermIdx {
        let goal_t = a.add(TermNode::Lit { value: goal });
        let exclude_t = exclude.map(|e| a.add(TermNode::Lit { value: e }));
        let field_sym = if field.is_empty() {
            Sym::default()
        } else {
            ir.intern(field)
        };
        a.add(TermNode::TransformDecode {
            goal: goal_t,
            codebook_type,
            exclude: exclude_t,
            max_dims,
            field: field_sym,
        })
    }

    /// Evaluate a `TransformDecode` built by `build_transform_term` over
    /// `(g, ir)` and return the result Dict (or the `field`-selected
    /// value, when `field` is non-empty).
    fn run(
        g: &TypedGraph,
        ir: &mut Interner,
        goal: Value,
        codebook_type: Sym,
        max_dims: i64,
        field: &str,
    ) -> Value {
        let mut a = TermArena::new();
        let idx = build_transform_term(&mut a, ir, goal, codebook_type, None, max_dims, field);
        let mut env: Env = Env::new();
        let mut ctx = EvalCtx::new(g, ir);
        evaluate(&a, idx, &mut env, &mut ctx)
    }

    /// (1) A single symbolic substitution consistent across MULTIPLE
    /// relations is explained: the held shape's colour slot (1) maps
    /// uniformly `"red" -> "blue"`, reported as one `subst` dim with a
    /// single `[from, to]` pair.
    #[test]
    fn single_symbolic_substitution_explained() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![
            rel(&mut ir, &["mark", "red", "a"]),
            rel(&mut ir, &["mark", "red", "b"]),
        ]);
        add_part(&mut g, &mut ir, t, "Base", held);
        let goal = tuple_of(vec![
            rel(&mut ir, &["mark", "blue", "a"]),
            rel(&mut ir, &["mark", "blue", "b"]),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(false));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Base")));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![Value::Int(1)]));
        assert_eq!(dict_get(&result, "residual_unexplained"), tuple_of(vec![]));

        let (Value::Tuple(transforms) | Value::List(transforms)) = dict_get(&result, "transforms")
        else {
            panic!("transforms must be a Tuple")
        };
        assert_eq!(transforms.len(), 1);
        assert_eq!(dict_get(&transforms[0], "dim"), Value::Int(1));
        assert_eq!(dict_get(&transforms[0], "kind"), surf("subst"));
        let expect_pair = Value::Tuple(Arc::new(smallvec::smallvec![
            Value::Str(ir.intern("red")),
            Value::Str(ir.intern("blue"))
        ]));
        assert_eq!(
            dict_get(&transforms[0], "delta"),
            tuple_of(vec![expect_pair])
        );
    }

    /// (2) A uniform numeric shift (translate) is explained: every
    /// relation's row slot (1) shifts by the SAME amount.
    #[test]
    fn uniform_numeric_shift_explained() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![
            rel_vals(&mut ir, "cell", vec![Value::Int(1), Value::Int(5)]),
            rel_vals(&mut ir, "cell", vec![Value::Int(2), Value::Int(5)]),
        ]);
        add_part(&mut g, &mut ir, t, "Row", held);
        let goal = tuple_of(vec![
            rel_vals(&mut ir, "cell", vec![Value::Int(4), Value::Int(5)]),
            rel_vals(&mut ir, "cell", vec![Value::Int(5), Value::Int(5)]),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Row")));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![Value::Int(1)]));
        assert_eq!(dict_get(&result, "deltas"), tuple_of(vec![Value::Int(3)]));

        let (Value::Tuple(transforms) | Value::List(transforms)) = dict_get(&result, "transforms")
        else {
            panic!("transforms must be a Tuple")
        };
        assert_eq!(transforms.len(), 1);
        assert_eq!(dict_get(&transforms[0], "kind"), surf("shift"));
        assert_eq!(dict_get(&transforms[0], "delta"), Value::Int(3));
    }

    /// (3) Numeric shift + symbolic substitution TOGETHER: explained at
    /// `max_dims=2`, REJECTED (not explained) at `max_dims=1` — the
    /// candidate needs both dims or none, no partial credit.
    #[test]
    fn combined_shift_and_substitution_gated_by_max_dims() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let red = ir.intern("red");
        let held = tuple_of(vec![
            rel_vals(&mut ir, "cell", vec![Value::Int(1), Value::Str(red)]),
            rel_vals(&mut ir, "cell", vec![Value::Int(2), Value::Str(red)]),
        ]);
        add_part(&mut g, &mut ir, t, "RedRow", held);
        let blue = ir.intern("blue");
        let goal = tuple_of(vec![
            rel_vals(&mut ir, "cell", vec![Value::Int(4), Value::Str(blue)]),
            rel_vals(&mut ir, "cell", vec![Value::Int(5), Value::Str(blue)]),
        ]);

        let result2 = run(&g, &mut ir, goal.clone(), t, 2, "");
        assert_eq!(dict_get(&result2, "explained"), Value::Bool(true));
        assert_eq!(
            dict_get(&result2, "dims"),
            tuple_of(vec![Value::Int(1), Value::Int(2)])
        );

        let result1 = run(&g, &mut ir, goal, t, 1, "");
        assert_eq!(dict_get(&result1, "explained"), Value::Bool(false));
    }

    /// (4) Inconsistent per-relation changes on the SAME slot (the same
    /// held value maps to two different observed values) must NOT be
    /// explained — the null that protects codebook growth.
    #[test]
    fn inconsistent_slot_changes_not_explained() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let red = ir.intern("red");
        let held = tuple_of(vec![
            rel_vals(&mut ir, "cell", vec![Value::Int(1), Value::Str(red)]),
            rel_vals(&mut ir, "cell", vec![Value::Int(2), Value::Str(red)]),
        ]);
        add_part(&mut g, &mut ir, t, "RedRow", held);
        // "red" maps to "blue" in one relation and "green" in the other —
        // not a function.
        let blue = ir.intern("blue");
        let green = ir.intern("green");
        let goal = tuple_of(vec![
            rel_vals(&mut ir, "cell", vec![Value::Int(1), Value::Str(blue)]),
            rel_vals(&mut ir, "cell", vec![Value::Int(2), Value::Str(green)]),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(false));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(false));
    }

    /// (5) A predicate-slot change disqualifies the candidate entirely —
    /// NOT explained (a novel predicate is a different shape, so the
    /// composer's mint-on-novel-predicate path still fires downstream).
    #[test]
    fn predicate_slot_change_not_explained() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![rel(&mut ir, &["touch", "red", "a"])]);
        add_part(&mut g, &mut ir, t, "Touch", held);
        let goal = tuple_of(vec![rel(&mut ir, &["push", "red", "a"])]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(false));
        assert_eq!(dict_get(&result, "base"), Value::None);
    }

    /// (6) Zero mismatches at all is `identity`, NOT a transform:
    /// `explained` stays `false` but the Dict carries a distinct
    /// `"identity": true` marker so a rule never routes an exact match
    /// through this op (that's `sd_recognize`'s job).
    #[test]
    fn identity_is_not_explained_but_marked() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![rel(&mut ir, &["mark", "red", "a"])]);
        add_part(&mut g, &mut ir, t, "Base", held);
        let goal = tuple_of(vec![rel(&mut ir, &["mark", "red", "a"])]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(false));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
        assert_eq!(dict_get(&result, "residual_unexplained"), tuple_of(vec![]));
    }

    /// (7) Ranking: a candidate explainable with FEWER dims beats one
    /// needing more, even when both fit within `max_dims`.
    #[test]
    fn ranking_prefers_fewest_dims() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        // Needs only the colour dim (slot 1): object ids already match.
        let one_dim = tuple_of(vec![
            rel(&mut ir, &["mark", "red", "a"]),
            rel(&mut ir, &["mark", "red", "b"]),
        ]);
        add_part(&mut g, &mut ir, t, "OneDim", one_dim);
        // Needs BOTH the colour dim (1) and the object-id dim (2).
        let two_dim = tuple_of(vec![
            rel(&mut ir, &["mark", "red", "x"]),
            rel(&mut ir, &["mark", "red", "y"]),
        ]);
        add_part(&mut g, &mut ir, t, "TwoDim", two_dim);
        let goal = tuple_of(vec![
            rel(&mut ir, &["mark", "blue", "a"]),
            rel(&mut ir, &["mark", "blue", "b"]),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("OneDim")));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![Value::Int(1)]));
    }

    /// (8) A relation-COUNT mismatch is never a transform (coverage is
    /// `ShapeDecode`'s job, not this op's) — not explained, no base.
    #[test]
    fn length_mismatch_not_explained() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![rel(&mut ir, &["mark", "red", "a"])]);
        add_part(&mut g, &mut ir, t, "Base", held);
        let goal = tuple_of(vec![
            rel(&mut ir, &["mark", "red", "a"]),
            rel(&mut ir, &["mark", "red", "b"]),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(false));
        assert_eq!(dict_get(&result, "base"), Value::None);
        assert_eq!(dict_get(&result, "checked"), Value::Int(1));
    }

    /// (9) `field` selection reads one Dict key straight off a decode —
    /// same convention as `ShapeDecode`'s selector.
    #[test]
    fn field_selection_works() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![
            rel(&mut ir, &["mark", "red", "a"]),
            rel(&mut ir, &["mark", "red", "b"]),
        ]);
        add_part(&mut g, &mut ir, t, "Base", held);
        let goal = tuple_of(vec![
            rel(&mut ir, &["mark", "blue", "a"]),
            rel(&mut ir, &["mark", "blue", "b"]),
        ]);

        assert_eq!(
            run(&g, &mut ir, goal.clone(), t, 2, "explained"),
            Value::Bool(true)
        );
        assert_eq!(
            run(&g, &mut ir, goal.clone(), t, 2, "base"),
            Value::Str(ir.intern("Base"))
        );
        assert_eq!(
            run(&g, &mut ir, goal, t, 2, "dims"),
            tuple_of(vec![Value::Int(1)])
        );
    }

    /// (10) Grid-flavoured: cells-as-relations `["cell", r, c, v]` — a
    /// translated (row +5) AND recoloured (red -> blue) 4-cell shape is
    /// explained with `dims == [1, 3]` (row, then colour; the column
    /// slot 2 never changes). This is the ARC grid-transform story in
    /// miniature.
    #[test]
    fn grid_translate_and_recolour_explained_with_row_and_colour_dims() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let cell = |ir: &mut Interner, r: i64, c: i64, v: &str| {
            let v_sym = ir.intern(v);
            rel_vals(
                ir,
                "cell",
                vec![Value::Int(r), Value::Int(c), Value::Str(v_sym)],
            )
        };
        let held = tuple_of(vec![
            cell(&mut ir, 1, 1, "red"),
            cell(&mut ir, 1, 2, "red"),
            cell(&mut ir, 2, 1, "red"),
            cell(&mut ir, 2, 2, "red"),
        ]);
        add_part(&mut g, &mut ir, t, "Block", held);
        let goal = tuple_of(vec![
            cell(&mut ir, 6, 1, "blue"),
            cell(&mut ir, 6, 2, "blue"),
            cell(&mut ir, 7, 1, "blue"),
            cell(&mut ir, 7, 2, "blue"),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Block")));
        assert_eq!(
            dict_get(&result, "dims"),
            tuple_of(vec![Value::Int(1), Value::Int(3)])
        );
        assert_eq!(
            dict_get(&result, "deltas"),
            tuple_of(vec![
                Value::Int(5),
                Value::Tuple(Arc::new(smallvec::smallvec![Value::Tuple(Arc::new(
                    smallvec::smallvec![
                        Value::Str(ir.intern("red")),
                        Value::Str(ir.intern("blue"))
                    ]
                ))])),
            ])
        );
    }

    /// A `ShapeSignature` node whose `signature` is stored the way
    /// `seeds/*.json`-loaded codebook entries actually are: a JSON-string
    /// attr, parsed at decode time via `json_to_value_scoped` (NOT the
    /// native-`Value::Tuple` shortcut `add_part` uses above, which is why
    /// tests 1-10 never exercised the scoped-placeholder path at all).
    fn add_part_json(
        g: &mut TypedGraph,
        ir: &mut Interner,
        t: Sym,
        name: &str,
        sig_json: &serde_json::Value,
    ) -> NodeID {
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("name"), Value::Str(ir.intern(name)));
        attrs.insert(
            ir.intern("signature"),
            Value::Str(ir.intern(&sig_json.to_string())),
        );
        attrs.insert(ir.intern("kind"), Value::Str(ir.intern("faculty")));
        g.insert_node(t, attrs)
    }

    /// (11) Regression: a held part read from a JSON-string `signature`
    /// (the seed-loaded shape, see `add_part_json`) whose substituted
    /// "from" value ("X") is truly novel to the graph — it never appears
    /// in `goal` or anywhere else already interned — must NOT panic and
    /// must NOT leak the internal placeholder Sym `local_sym` fabricates
    /// for it. Exact repro of the reported bug: goal
    /// `[["move","Y","by","D"],["stop","Y"]]` vs held
    /// `[["move","X","by","D"],["stop","X"]]` (JSON-string signature)
    /// used to panic in `sym.rs` with "index out of bounds: index is
    /// 4294967295" (`u32::MAX`, `local_sym`'s first fabricated id) the
    /// moment the output Dict's `transforms`/`deltas` were read back
    /// (any consumer that resolves a `Value::Str` through the interner —
    /// including `value_to_py`). Before the fix, `sub_pairs` pushed the
    /// raw held-side Sym straight into the output; now it is resolved to
    /// a `Value::Surface(Text, ..)`, which needs no interner lookup.
    #[test]
    fn scoped_local_placeholder_from_value_never_reaches_output() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held_json = serde_json::json!([["move", "X", "by", "D"], ["stop", "X"],]);
        add_part_json(&mut g, &mut ir, t, "MoveStop", &held_json);
        // "Y" stands in for "X"; "move"/"by"/"D"/"stop" are shared with
        // the held signature's JSON text so `local_sym` resolves them to
        // their REAL Syms via `Interner::lookup` — only "X" is genuinely
        // novel (it never appears here), so only "X" is fabricated.
        let goal = tuple_of(vec![
            rel(&mut ir, &["move", "Y", "by", "D"]),
            rel(&mut ir, &["stop", "Y"]),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("MoveStop")));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![Value::Int(1)]));

        let (Value::Tuple(transforms) | Value::List(transforms)) = dict_get(&result, "transforms")
        else {
            panic!("transforms must be a Tuple")
        };
        assert_eq!(transforms.len(), 1);
        assert_eq!(dict_get(&transforms[0], "kind"), surf("subst"));
        // The "from" side must be a plain Surface string ("X"), NOT a
        // Value::Str Sym the interner never issued.
        let expect_pair = Value::Tuple(Arc::new(smallvec::smallvec![
            surf("X"),
            Value::Str(ir.intern("Y"))
        ]));
        assert_eq!(
            dict_get(&transforms[0], "delta"),
            tuple_of(vec![expect_pair])
        );

        // The whole Dict must also survive an interner round-trip of
        // every Str it contains (the real-world failure mode: any caller
        // — e.g. `value_to_py` — resolving every Str leaf it sees).
        fn assert_no_placeholder_syms(v: &Value, ir: &Interner) {
            match v {
                Value::Str(s) => {
                    let _ = ir.resolve(*s); // panics on an unissued Sym
                }
                Value::Tuple(items) | Value::List(items) => {
                    for it in items.iter() {
                        assert_no_placeholder_syms(it, ir);
                    }
                }
                Value::Dict(pairs) => {
                    for (k, val) in pairs.iter() {
                        assert_no_placeholder_syms(k, ir);
                        assert_no_placeholder_syms(val, ir);
                    }
                }
                _ => {}
            }
        }
        assert_no_placeholder_syms(&result, &ir);
    }

    // --- Two-tier (predicate, slot) pooling tests (the stroke-pose fix;
    // see `build_candidate`'s block comment). Tests 1-11 above are the
    // TIER-1 output-compatibility corpus: every one of them passes
    // byte-identically because a slot the old semantics explained is
    // exactly a slot the global tier-1 check still explains. ---

    /// (12) Tier-2 split: two predicates shift DIFFERENTLY at the same
    /// per-relation slot index, a third predicate holds still. The old
    /// raw-slot pooling rejected this outright (0 vs 1 vs 2 deltas at
    /// "slot 1"); now the zero-delta group (`r`) is budget-free and
    /// untransformed, and `p`/`q` each become their own `pred`-keyed
    /// dimension — duplicate slot indices in `dims`.
    #[test]
    fn predicate_split_numeric_deltas_explained_with_pred_keys() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![
            rel_vals(&mut ir, "p", vec![Value::Int(0)]),
            rel_vals(&mut ir, "q", vec![Value::Int(0)]),
            rel_vals(&mut ir, "r", vec![Value::Int(5)]),
        ]);
        add_part(&mut g, &mut ir, t, "Mixed", held);
        let goal = tuple_of(vec![
            rel_vals(&mut ir, "p", vec![Value::Int(1)]),
            rel_vals(&mut ir, "q", vec![Value::Int(2)]),
            rel_vals(&mut ir, "r", vec![Value::Int(5)]),
        ]);

        // max_dims = 2: two split entries fit; the zero-delta `r` group
        // does NOT count toward the budget.
        let result = run(&g, &mut ir, goal.clone(), t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Mixed")));
        assert_eq!(
            dict_get(&result, "dims"),
            tuple_of(vec![Value::Int(1), Value::Int(1)])
        );
        assert_eq!(
            dict_get(&result, "deltas"),
            tuple_of(vec![Value::Int(1), Value::Int(2)])
        );
        let (Value::Tuple(transforms) | Value::List(transforms)) = dict_get(&result, "transforms")
        else {
            panic!("transforms must be a Tuple")
        };
        assert_eq!(transforms.len(), 2);
        assert_eq!(dict_get(&transforms[0], "pred"), Value::Str(ir.intern("p")));
        assert_eq!(dict_get(&transforms[0], "kind"), surf("shift"));
        assert_eq!(dict_get(&transforms[0], "delta"), Value::Int(1));
        assert_eq!(dict_get(&transforms[1], "pred"), Value::Str(ir.intern("q")));
        assert_eq!(dict_get(&transforms[1], "delta"), Value::Int(2));

        // max_dims = 1: the two REQUIRED split entries exceed the
        // budget -> not explained (transform entries are what's
        // counted, zero-delta groups are exempt but nonzero ones are
        // not).
        let result1 = run(&g, &mut ir, goal, t, 1, "");
        assert_eq!(dict_get(&result1, "explained"), Value::Bool(false));
    }

    /// (13) Tier-1 entries never grow a `pred` key: a uniform shift
    /// shared by every relation (two predicates agreeing) stays ONE
    /// merged un-keyed dimension — the output-compat contract, pinned
    /// explicitly at the Dict level (equal `{dim,kind,delta}` triple,
    /// `pred` absent).
    #[test]
    fn agreeing_predicates_merge_into_one_unkeyed_dimension() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![
            rel_vals(&mut ir, "p", vec![Value::Int(0)]),
            rel_vals(&mut ir, "q", vec![Value::Int(3)]),
        ]);
        add_part(&mut g, &mut ir, t, "Agree", held);
        let goal = tuple_of(vec![
            rel_vals(&mut ir, "p", vec![Value::Int(2)]),
            rel_vals(&mut ir, "q", vec![Value::Int(5)]),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![Value::Int(1)]));
        let (Value::Tuple(transforms) | Value::List(transforms)) = dict_get(&result, "transforms")
        else {
            panic!("transforms must be a Tuple")
        };
        assert_eq!(transforms.len(), 1);
        assert_eq!(
            dict_get(&transforms[0], "pred"),
            Value::None,
            "tier-1 merged entry carries NO pred key"
        );
        assert_eq!(dict_get(&transforms[0], "delta"), Value::Int(2));
    }

    /// (14) The cross-predicate scrambled SUBSTITUTION stays the
    /// discriminative NULL: `move X->Y` / `stop X->Z` (the same held
    /// value mapping to two observed values under two predicates) must
    /// NOT be explained — symbolic slots deliberately have no tier-2
    /// split (renaming is global; see `build_candidate`'s block
    /// comment). This pins, at the cargo level, the exact fixture
    /// `tests/test_transform_decode_migrated.py::
    /// test_scrambled_observation_is_discriminative_null_and_mints`
    /// depends on through the seeded sd loop (`max_dims: 2`).
    #[test]
    fn cross_predicate_scrambled_substitution_still_null() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![
            rel(&mut ir, &["move", "X", "by", "D"]),
            rel(&mut ir, &["stop", "X"]),
        ]);
        add_part(&mut g, &mut ir, t, "MoveStop", held);
        let goal = tuple_of(vec![
            rel(&mut ir, &["move", "Y", "by", "D"]),
            rel(&mut ir, &["stop", "Z"]),
        ]);

        let result = run(&g, &mut ir, goal, t, 2, "");
        assert_eq!(
            dict_get(&result, "explained"),
            Value::Bool(false),
            "a scrambled substitution must stay the null that lets sd_mint_quantum fire"
        );
        assert_eq!(dict_get(&result, "identity"), Value::Bool(false));
    }

    /// (15) Tier-2 split still rejects non-uniformity WITHIN one
    /// predicate family: `p` shifts +1 in one relation and +3 in
    /// another (same predicate, same slot) — a genuine inconsistency
    /// the split must not paper over, even while `q`'s clean +2 group
    /// sits beside it.
    #[test]
    fn split_rejects_nonuniform_within_predicate() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let held = tuple_of(vec![
            rel_vals(&mut ir, "p", vec![Value::Int(0), Value::Int(0)]),
            rel_vals(&mut ir, "p", vec![Value::Int(9), Value::Int(1)]),
            rel_vals(&mut ir, "q", vec![Value::Int(4), Value::Int(0)]),
        ]);
        add_part(&mut g, &mut ir, t, "BadP", held);
        let goal = tuple_of(vec![
            rel_vals(&mut ir, "p", vec![Value::Int(1), Value::Int(0)]),
            rel_vals(&mut ir, "p", vec![Value::Int(12), Value::Int(1)]),
            rel_vals(&mut ir, "q", vec![Value::Int(6), Value::Int(0)]),
        ]);

        let result = run(&g, &mut ir, goal, t, 4, "");
        assert_eq!(
            dict_get(&result, "explained"),
            Value::Bool(false),
            "+1 and +3 within the SAME predicate at the same slot is not a transform"
        );
    }
}

/// `DimInfer` tests — RUNG 2's own fixtures. Self-contained (own tiny
/// `add_part`/`add_generator`/`rel_vals`/`tuple_of`/`dict_get` helpers,
/// mirroring `transform_decode_tests`'s pattern) rather than reusing
/// private helpers from a sibling module.
#[cfg(test)]
mod dim_infer_tests {
    use super::*;
    use crate::graph::{NodeID, TypedGraph};
    use crate::term::TermNode;

    /// `name`/`signature`/`kind`/`dim_types` `ShapeSignature` node.
    /// `dim_types` is a native `Value::Tuple` of `Str` — one entry per
    /// `sig`'s relation slots, e.g. `["pred","coord:r","coord:c","val"]`
    /// for a `("cell", r, c, colour)` relation family.
    fn add_part(
        g: &mut TypedGraph,
        ir: &mut Interner,
        t: Sym,
        name: &str,
        sig: Value,
        dim_types: &[&str],
    ) -> NodeID {
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("name"), Value::Str(ir.intern(name)));
        attrs.insert(ir.intern("signature"), sig);
        attrs.insert(ir.intern("kind"), Value::Str(ir.intern("faculty")));
        let dt: SmallVec<[Value; 4]> = dim_types.iter().map(|s| Value::Str(ir.intern(s))).collect();
        attrs.insert(ir.intern("dim_types"), Value::Tuple(Arc::new(dt)));
        g.insert_node(t, attrs)
    }

    /// A `ShapeSignature` node with NO `dim_types` attr at all — the
    /// graceful-skip fixture (requirement 5: rung 2 must not crash, and
    /// must contribute zero `checked` attempts, when a candidate simply
    /// isn't dimension-typed).
    fn add_part_untyped(
        g: &mut TypedGraph,
        ir: &mut Interner,
        t: Sym,
        name: &str,
        sig: Value,
    ) -> NodeID {
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("name"), Value::Str(ir.intern(name)));
        attrs.insert(ir.intern("signature"), sig);
        attrs.insert(ir.intern("kind"), Value::Str(ir.intern("faculty")));
        g.insert_node(t, attrs)
    }

    /// A `ShapeSignature` node whose `signature` is a JSON-STRING attr
    /// (parsed via `json_to_value_scoped` at decode time, exactly like
    /// `seeds/*.json`-loaded codebook entries) — the regression class
    /// `transform_decode_tests::scoped_local_placeholder_from_value_never_reaches_output`
    /// exercises for `TransformDecode`; `dim_infer_tests` exercises the
    /// SAME class through `DimInfer`'s own `build_candidate` reuse.
    fn add_part_json(
        g: &mut TypedGraph,
        ir: &mut Interner,
        t: Sym,
        name: &str,
        sig_json: &serde_json::Value,
        dim_types: &[&str],
    ) -> NodeID {
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("name"), Value::Str(ir.intern(name)));
        attrs.insert(
            ir.intern("signature"),
            Value::Str(ir.intern(&sig_json.to_string())),
        );
        attrs.insert(ir.intern("kind"), Value::Str(ir.intern("faculty")));
        let dt: SmallVec<[Value; 4]> = dim_types.iter().map(|s| Value::Str(ir.intern(s))).collect();
        attrs.insert(ir.intern("dim_types"), Value::Tuple(Arc::new(dt)));
        g.insert_node(t, attrs)
    }

    /// `name`/`kind`/`coord_dims`/`params` `DimensionGenerator` node —
    /// `coord_dims`/`params` as native `Value::Tuple` of `Int`.
    fn add_generator(
        g: &mut TypedGraph,
        ir: &mut Interner,
        gt: Sym,
        name: &str,
        kind: &str,
        coord_dims: &[i64],
        params: &[i64],
    ) -> NodeID {
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("name"), Value::Str(ir.intern(name)));
        attrs.insert(ir.intern("kind"), Value::Str(ir.intern(kind)));
        let cd: SmallVec<[Value; 4]> = coord_dims.iter().map(|&i| Value::Int(i)).collect();
        attrs.insert(ir.intern("coord_dims"), Value::Tuple(Arc::new(cd)));
        let pr: SmallVec<[Value; 4]> = params.iter().map(|&i| Value::Int(i)).collect();
        attrs.insert(ir.intern("params"), Value::Tuple(Arc::new(pr)));
        g.insert_node(gt, attrs)
    }

    /// Like `add_generator`, plus a `modulus` `Int` attr — the cycle length
    /// a `kind == "modular"` (cyclic Z_n) generator wraps against (see
    /// `modular_step_once`). Kept separate from `add_generator` so every
    /// existing non-modular fixture stays byte-identical (no `modulus`
    /// attr, `load_generators` defaults it to `0`).
    fn add_generator_mod(
        g: &mut TypedGraph,
        ir: &mut Interner,
        gt: Sym,
        name: &str,
        kind: &str,
        coord_dims: &[i64],
        params: &[i64],
        modulus: i64,
    ) -> NodeID {
        let nid = add_generator(g, ir, gt, name, kind, coord_dims, params);
        let modulus_key = ir.intern("modulus");
        g.node_mut(nid)
            .attrs
            .insert(modulus_key, Value::Int(modulus));
        nid
    }

    /// A `("cell", r, c, colour)` relation — `rel_vals(ir, "cell", r, c,
    /// "red")`.
    fn cell(ir: &mut Interner, r: i64, c: i64, colour: &str) -> Value {
        let colour_sym = ir.intern(colour);
        Value::Tuple(Arc::new(smallvec::smallvec![
            Value::Str(ir.intern("cell")),
            Value::Int(r),
            Value::Int(c),
            Value::Str(colour_sym)
        ]))
    }

    fn tuple_of(items: Vec<Value>) -> Value {
        let v: SmallVec<[Value; 4]> = items.into_iter().collect();
        Value::Tuple(Arc::new(v))
    }

    fn dict_get(v: &Value, key: &str) -> Value {
        if let Value::Dict(pairs) = v {
            for (k, val) in pairs.iter() {
                if let Value::Surface(SurfaceKind::Text, bytes) = k {
                    if bytes.as_ref() == key.as_bytes() {
                        return val.clone();
                    }
                }
            }
        }
        Value::None
    }

    #[allow(clippy::too_many_arguments)]
    fn run(
        g: &TypedGraph,
        ir: &mut Interner,
        goal: Value,
        codebook_type: Sym,
        generator_type: Sym,
        max_dims: i64,
        field: &str,
    ) -> Value {
        let mut a = TermArena::new();
        let goal_t = a.add(TermNode::Lit { value: goal });
        let field_sym = if field.is_empty() {
            Sym::default()
        } else {
            ir.intern(field)
        };
        let idx = a.add(TermNode::DimInfer {
            goal: goal_t,
            codebook_type,
            exclude: None,
            generator_type,
            grain: None,
            max_dims,
            field: field_sym,
        });
        let mut env: Env = Env::new();
        let mut ctx = EvalCtx::new(g, ir);
        evaluate(&a, idx, &mut env, &mut ctx)
    }

    /// `run`, with this invocation's own argument attribution recorded into
    /// `w`. Touches nothing global, so it is correct under a parallel harness
    /// and needs no lock.
    #[allow(clippy::too_many_arguments)]
    fn run_witnessed(
        g: &TypedGraph,
        ir: &mut Interner,
        goal: Value,
        codebook_type: Sym,
        generator_type: Sym,
        max_dims: i64,
        field: &str,
        w: &mut crate::term::DimInferWitness,
    ) -> Value {
        let mut a = TermArena::new();
        let goal_t = a.add(TermNode::Lit { value: goal });
        let field_sym = if field.is_empty() {
            Sym::default()
        } else {
            ir.intern(field)
        };
        let idx = a.add(TermNode::DimInfer {
            goal: goal_t,
            codebook_type,
            exclude: None,
            generator_type,
            grain: None,
            max_dims,
            field: field_sym,
        });
        let mut env: Env = Env::new();
        let mut ctx = EvalCtx::new(g, ir).with_dim_infer_witness(w);
        evaluate(&a, idx, &mut env, &mut ctx)
    }

    /// Run `n` witnessed decodes and return
    /// `(calls, distinct_ordered, distinct_unordered)` from that witness.
    ///
    /// Replaces a predecessor that enabled a PROCESS-GLOBAL audit, ran the
    /// decodes, and snapshotted global counters. That is a measurement of
    /// these decodes only if nothing else in the process decodes during the
    /// window — which this harness violates routinely, because sibling tests
    /// decode in parallel and increment the same counters. Measured: 22/22
    /// serial, 19-20/22 under default threading, varying run to run on
    /// identical code. The module-local mutex gave false assurance, serialising
    /// only the six tests that took it and not the thirty-nine that decode
    /// freely.
    fn witnessed<F: FnMut(usize, &mut crate::term::DimInferWitness)>(
        n: usize,
        mut each: F,
    ) -> (u64, u64, u64) {
        let mut w = crate::term::DimInferWitness::default();
        for i in 0..n {
            each(i, &mut w);
        }
        (
            w.calls() as u64,
            w.distinct_ordered() as u64,
            w.distinct_unordered() as u64,
        )
    }

    /// The shared asymmetric-tromino fixture: an "L" of 3 red cells at
    /// `(0,0) (0,1) (1,0)`. Asymmetric under 90-degree rotation (all four
    /// of k=0..3 land on a DISTINCT cell set — hand-verified), which is
    /// exactly what makes "the correct k is reported" a meaningful
    /// assertion rather than a coincidence.
    fn tromino(ir: &mut Interner) -> Value {
        tuple_of(vec![
            cell(ir, 0, 0, "red"),
            cell(ir, 0, 1, "red"),
            cell(ir, 1, 0, "red"),
        ])
    }

    /// (1) A 90-degree-rotated (k=1) shape is recognized via `rotation90`
    /// with ZERO residual transforms — the generator alone fully explains
    /// it (no separate translate/recolour needed because both held and
    /// goal sit at the same bbox-normalized origin).
    #[test]
    fn rotated_shape_explained_zero_residual() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        // Hand-computed k=1 image of the tromino (see `rotate90_once`'s
        // doc / this module's design notes): {(0,0),(0,1),(1,1)}.
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 1, "red"),
            cell(&mut ir, 1, 1, "red"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Base")));
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("rotation90"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "transforms"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
        assert_eq!(dict_get(&result, "checked"), Value::Int(3));
    }

    /// (1b) BASE-AS-DIMENSION: a ×2-scaled shape is recognized via the
    /// `scale2` generator with ZERO residual — a LOG2-SCALE base is a
    /// DIMENSION (`k`), not hand-set config. The tromino
    /// {(0,0),(0,1),(1,0)} scaled ×2 about its origin is
    /// {(0,0),(0,2),(2,0)}; `scale2` k=1 explains it exactly (the ratio ×2
    /// became the additive delta k=1 that `sd_recognize_dim` then mints as
    /// a `latent:scale2` `LatentDimension`). Asymmetric under scaling — the
    /// scaled image occupies a DISTINCT cell set, so "the correct k is
    /// reported" is a real assertion, not a coincidence.
    #[test]
    fn scaled_shape_explained_via_scale2_generator() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(&mut g, &mut ir, gt, "scale2", "scale2", &[1, 2], &[1, 2, 3]);
        // ×2 image of the tromino about its origin: {(0,0),(0,2),(2,0)}.
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 2, "red"),
            cell(&mut ir, 2, 0, "red"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Base")));
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("scale2"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "transforms"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
        assert_eq!(dict_get(&result, "checked"), Value::Int(3));
    }

    /// (1c) The SAME shape ×4 is `scale2` k=2 — the scale FAMILY collapses
    /// to one held shape stepping along one dimension (×2 = k+1), instead
    /// of a fresh mint per size. This is the efficiency half of the claim.
    #[test]
    fn scaled_x4_shape_is_scale2_k2() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(&mut g, &mut ir, gt, "scale2", "scale2", &[1, 2], &[1, 2, 3]);
        // ×4 image of the tromino: {(0,0),(0,4),(4,0)}.
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 4, "red"),
            cell(&mut ir, 4, 0, "red"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("scale2"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(2));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
    }

    /// The two-cell wrap fixture for the `modular` (cyclic Z_n) generator:
    /// cells at row `0` and row `3`, distinct columns so the relations
    /// differ. Its row slot (index 1) is the cyclic axis. Under a modulus
    /// of 4, one modular step sends row `0 -> 1` (no wrap) and row `3 -> 0`
    /// (WRAPS across the boundary) — so the held->goal row delta is
    /// NON-uniform (`+1` for one cell, `-3` for the other), which a plain
    /// rung-1 numeric `shift` can never explain. THIS is the whole point of
    /// the modular generator: the wrap is exactly what distinguishes it
    /// from an ordinary per-dimension shift, so the fixture MUST cross the
    /// modulus boundary or the test would prove nothing (see the module's
    /// note on why symmetric fixtures don't discriminate).
    fn cycle_pair(ir: &mut Interner) -> Value {
        tuple_of(vec![cell(ir, 0, 0, "red"), cell(ir, 3, 1, "red")])
    }

    /// (1d) CYCLIC PHASE (base-as-dimension, categorical): a shape whose
    /// cyclic row slot has stepped by ONE around a Z_4 ring is recognized
    /// via the `modular` generator with ZERO residual. `cycle_pair` at
    /// rows {0,3} steps (k=1, modulus 4) to rows {1,0} — the row-3 cell
    /// WRAPS to 0, which a rung-1 shift cannot match; `modular` k=1
    /// explains it exactly (the wrap applied uniformly to the whole shape
    /// before the residual check). The image {(1,0),(0,1)} is a DISTINCT
    /// cell set from the held {(0,0),(3,1)}, so "generator modular, k=1" is
    /// a real assertion, not a coincidence.
    #[test]
    fn modular_wrap_shape_explained_via_modular_generator() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let base = cycle_pair(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            base,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator_mod(
            &mut g,
            &mut ir,
            gt,
            "cycle4",
            "modular",
            &[1],
            &[1, 2, 3],
            4,
        );
        // k=1 image of the pair under +1 mod 4 on the row slot:
        // (0,0)->(1,0), (3,1)->(0,1) (the row-3 cell WRAPS to 0).
        let goal = tuple_of(vec![cell(&mut ir, 1, 0, "red"), cell(&mut ir, 0, 1, "red")]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Base")));
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("cycle4"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "transforms"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
        assert_eq!(dict_get(&result, "checked"), Value::Int(3));
    }

    /// (1e) The SAME cyclic pair stepped TWICE (k=2, modulus 4): rows {0,3}
    /// -> {2,1} (the row-3 cell wraps: `3 + 2 = 5 ≡ 1 mod 4`). A plain
    /// shift of +2 would send row 3 to 5, not 1, so the modulus is again
    /// essential. Asymmetric under the cycle — the k=1 image {(1,0),(0,1)}
    /// is a different cell set — so "the correct k is reported" (k=2, not
    /// k=1) is meaningful. This is the phase-family collapse: every step
    /// around the ring is the SAME held shape at a different `k`.
    #[test]
    fn modular_wrap_shape_is_modular_k2() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let base = cycle_pair(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            base,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator_mod(
            &mut g,
            &mut ir,
            gt,
            "cycle4",
            "modular",
            &[1],
            &[1, 2, 3],
            4,
        );
        // k=2 image: (0,0)->(2,0), (3,1)->(1,1) (row 3 wraps: 5 mod 4 = 1).
        let goal = tuple_of(vec![cell(&mut ir, 2, 0, "red"), cell(&mut ir, 1, 1, "red")]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("cycle4"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(2));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
    }

    /// (1f) NO-CYCLE SKIP: a `modular` generator declared with `modulus <=
    /// 0` is inapplicable — `load_generators` drops it, so even a genuine
    /// wrap fixture goes unexplained (no other generator present). Mirrors
    /// the missing-coord_dims/params graceful skip, one rung up.
    #[test]
    fn modular_without_modulus_is_skipped() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let base = cycle_pair(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            base,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator_mod(
            &mut g,
            &mut ir,
            gt,
            "cycle_bad",
            "modular",
            &[1],
            &[1, 2, 3],
            0,
        );
        let goal = tuple_of(vec![cell(&mut ir, 1, 0, "red"), cell(&mut ir, 0, 1, "red")]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(false));
        // The generator was skipped entirely, so ZERO (part, gen, k)
        // triples were attempted.
        assert_eq!(dict_get(&result, "checked"), Value::Int(0));
    }

    /// (2) Rotation + translation + recolour COMPOSE: the generator
    /// explains the orientation, and the residual (row shift, column
    /// shift, colour substitution — 3 dims) is picked up by the SAME
    /// rung-1 consistency check `TransformDecode` runs, reusing
    /// `build_candidate` unchanged. Needs `max_dims=3` (3 residual dims).
    #[test]
    fn rotated_translated_recoloured_composes() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        // k=1 image {(0,0),(0,1),(1,1)}, then +5 rows, +2 cols, red->blue.
        let goal = tuple_of(vec![
            cell(&mut ir, 5, 2, "blue"),
            cell(&mut ir, 5, 3, "blue"),
            cell(&mut ir, 6, 3, "blue"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 3, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Base")));
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("rotation90"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(
            dict_get(&result, "dims"),
            tuple_of(vec![Value::Int(1), Value::Int(2), Value::Int(3)])
        );

        let (Value::Tuple(transforms) | Value::List(transforms)) = dict_get(&result, "transforms")
        else {
            panic!("transforms must be a Tuple")
        };
        assert_eq!(transforms.len(), 3);
        assert_eq!(dict_get(&transforms[0], "kind"), surf("shift"));
        assert_eq!(dict_get(&transforms[0], "delta"), Value::Int(5));
        assert_eq!(dict_get(&transforms[1], "kind"), surf("shift"));
        assert_eq!(dict_get(&transforms[1], "delta"), Value::Int(2));
        assert_eq!(dict_get(&transforms[2], "kind"), surf("subst"));
        let expect_pair = Value::Tuple(Arc::new(smallvec::smallvec![
            Value::Str(ir.intern("red")),
            Value::Str(ir.intern("blue"))
        ]));
        assert_eq!(
            dict_get(&transforms[2], "delta"),
            tuple_of(vec![expect_pair])
        );
    }

    /// (3) Scrambled: the held colour is UNIFORMLY "red", but the goal's
    /// three colours are pairwise distinct — the colour dim's held->goal
    /// mapping can never be a function (the SAME held value "red" would
    /// have to map to 3 different observed values) for ANY `k`, so no
    /// generator application explains it. Every `k` is still attempted
    /// (`checked` reflects that), but none succeeds.
    #[test]
    fn scrambled_not_explained() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "blue"),
            cell(&mut ir, 0, 1, "green"),
            cell(&mut ir, 1, 0, "yellow"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(false));
        assert_eq!(dict_get(&result, "base"), Value::None);
        assert_eq!(dict_get(&result, "generator"), Value::None);
        assert_eq!(dict_get(&result, "k"), Value::None);
        assert_eq!(dict_get(&result, "checked"), Value::Int(3));
    }

    /// (4) Reflection: `reflection_r` flips the row axis about the
    /// shape's own bbox — the tromino's row-reflected image is
    /// hand-verified `{(1,0),(1,1),(0,0)}`. `k=2` (reflect twice) would
    /// revert to the untransformed original, which does NOT match the
    /// goal, so only `k=1` succeeds.
    #[test]
    fn reflection_explained() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "reflection_r",
            "reflection_r",
            &[1, 2],
            &[1, 2],
        );
        let goal = tuple_of(vec![
            cell(&mut ir, 1, 0, "red"),
            cell(&mut ir, 1, 1, "red"),
            cell(&mut ir, 0, 0, "red"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Base")));
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("reflection_r"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(dict_get(&result, "transforms"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
    }

    /// (5) No `dim_types` on the codebook candidate: rung 2 is skipped
    /// gracefully for it (no crash, `checked=0`, `explained=false`) — the
    /// generator never gets a chance to run against an untyped part.
    #[test]
    fn no_dim_types_skipped_gracefully() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part_untyped(&mut g, &mut ir, t, "Base", tromino_sig);
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 1, "red"),
            cell(&mut ir, 1, 1, "red"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(false));
        assert_eq!(dict_get(&result, "checked"), Value::Int(0));
    }

    /// (6) Regression (the placeholder-Sym class): a held part read from
    /// a JSON-STRING `signature` whose colour ("NOVELCOLOR") is truly
    /// novel to the graph — never interned anywhere else — must not
    /// panic and must not leak `local_sym`'s internal placeholder `Sym`
    /// into the output. Exercises `DimInfer`'s reuse of `build_candidate`
    /// (and therefore `resolve_scoped_output`) through the SAME
    /// `extra`/`extra_rev` plumbing `TransformDecode` uses.
    #[test]
    fn json_string_signature_placeholder_never_leaks() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let held_json = serde_json::json!([
            ["cell", 0, 0, "NOVELCOLOR"],
            ["cell", 0, 1, "NOVELCOLOR"],
            ["cell", 1, 0, "NOVELCOLOR"],
        ]);
        add_part_json(
            &mut g,
            &mut ir,
            t,
            "Base",
            &held_json,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        // k=1 image, recoloured to a REAL (goal-interned) colour.
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "goalcolor"),
            cell(&mut ir, 0, 1, "goalcolor"),
            cell(&mut ir, 1, 1, "goalcolor"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Base")));
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![Value::Int(3)]));

        let (Value::Tuple(transforms) | Value::List(transforms)) = dict_get(&result, "transforms")
        else {
            panic!("transforms must be a Tuple")
        };
        assert_eq!(transforms.len(), 1);
        let expect_pair = Value::Tuple(Arc::new(smallvec::smallvec![
            surf("NOVELCOLOR"),
            Value::Str(ir.intern("goalcolor"))
        ]));
        assert_eq!(
            dict_get(&transforms[0], "delta"),
            tuple_of(vec![expect_pair])
        );

        fn assert_no_placeholder_syms(v: &Value, ir: &Interner) {
            match v {
                Value::Str(s) => {
                    let _ = ir.resolve(*s);
                }
                Value::Tuple(items) | Value::List(items) => {
                    for it in items.iter() {
                        assert_no_placeholder_syms(it, ir);
                    }
                }
                Value::Dict(pairs) => {
                    for (k, val) in pairs.iter() {
                        assert_no_placeholder_syms(k, ir);
                        assert_no_placeholder_syms(val, ir);
                    }
                }
                _ => {}
            }
        }
        assert_no_placeholder_syms(&result, &ir);
    }

    /// (7) Param ranking: a single point-shape is rotation-INVARIANT (a
    /// lone cell's bbox is a single point, so every `k` maps it to
    /// itself), so `k=1`, `k=2`, and `k=3` all explain a translated goal
    /// with the IDENTICAL residual (a uniform 2-dim shift) — a genuine
    /// tie. The Occam tie-break (fewest residual dims, then base name,
    /// then smallest `k`) must report the smallest, `k=1`, regardless of
    /// the generator's own `params` LIST ORDER (deliberately shuffled
    /// here to `[3,2,1]`) — "the correct k is reported, not just any".
    #[test]
    fn param_ranking_prefers_smallest_tied_k() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let point = tuple_of(vec![cell(&mut ir, 0, 0, "red")]);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Point",
            point,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[3, 2, 1],
        );
        let goal = tuple_of(vec![cell(&mut ir, 3, 2, "red")]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(
            dict_get(&result, "dims"),
            tuple_of(vec![Value::Int(1), Value::Int(2)])
        );
    }

    /// (8) `field` selection — same convention as `ShapeDecode`/
    /// `TransformDecode`'s selector.
    #[test]
    fn field_selection_works() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 1, "red"),
            cell(&mut ir, 1, 1, "red"),
        ]);

        assert_eq!(
            run(&g, &mut ir, goal.clone(), t, gt, 2, "explained"),
            Value::Bool(true)
        );
        assert_eq!(
            run(&g, &mut ir, goal.clone(), t, gt, 2, "base"),
            Value::Str(ir.intern("Base"))
        );
        assert_eq!(
            run(&g, &mut ir, goal.clone(), t, gt, 2, "generator"),
            Value::Str(ir.intern("rotation90"))
        );
        assert_eq!(run(&g, &mut ir, goal, t, gt, 2, "k"), Value::Int(1));
    }

    /// (9) COMPOSITION (length 2): a tromino ROTATED (k=1) THEN SCALED
    /// (×2, k=1) — goal {(0,0),(0,2),(2,2)} — is explained by NEITHER
    /// generator alone (scale2 alone gives {(0,0),(0,2),(2,0)}; rotation/
    /// reflection preserve extent 1, so no single generator + linear
    /// residual reaches an extent-2 spread), so `DimInfer` composes
    /// rotation90∘scale2 with ZERO leftover residual. The reported
    /// sequence is `generators=("rotation90","scale2")`, `ks=(1,1)`,
    /// `length=2`. (Uniform scale commutes with the rotation on the
    /// origin-normalised lattice, so scale2∘rotation90 ALSO reaches this
    /// image; the ranking's generator-name tie-break reports the
    /// lexicographic-first order deterministically — see
    /// COMPOSITION_DESIGN.md §1/§2.) The scalar back-compat fields carry
    /// the FIRST step (`generator`="rotation90", `k`=1).
    #[test]
    fn composed_rotate_then_scale_is_length2() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        add_generator(&mut g, &mut ir, gt, "scale2", "scale2", &[1, 2], &[1, 2, 3]);
        // rotate90 k=1 {(0,0),(0,1),(1,1)}, then scale2 k=1 -> {(0,0),(0,2),(2,2)}.
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 2, "red"),
            cell(&mut ir, 2, 2, "red"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("Base")));
        assert_eq!(dict_get(&result, "length"), Value::Int(2));
        assert_eq!(
            dict_get(&result, "generators"),
            tuple_of(vec![
                Value::Str(ir.intern("rotation90")),
                Value::Str(ir.intern("scale2"))
            ])
        );
        assert_eq!(
            dict_get(&result, "ks"),
            tuple_of(vec![Value::Int(1), Value::Int(1)])
        );
        assert_eq!(dict_get(&result, "latent_name"), surf("rotation90+scale2"));
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("rotation90"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(dict_get(&result, "dims"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "transforms"), tuple_of(vec![]));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
    }

    /// (10) COMPOSITION (length 2): a tromino REFLECTED (row, k=1) THEN
    /// SCALED (×2, k=1) — goal {(0,0),(2,0),(2,2)}. Distinct image from
    /// the rotate∘scale case above, so the inferred generator PAIR is
    /// meaningful (reflection_r, not rotation90). Reports
    /// `generators=("reflection_r","scale2")`, `ks=(1,1)`, `length=2`,
    /// zero residual.
    #[test]
    fn composed_reflect_then_scale_is_length2() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        // All three generators present — the pair inference must pick the
        // reflection, not the rotation, for THIS image.
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "reflection_r",
            "reflection_r",
            &[1, 2],
            &[1, 2],
        );
        add_generator(&mut g, &mut ir, gt, "scale2", "scale2", &[1, 2], &[1, 2, 3]);
        // reflect_r k=1 {(1,0),(1,1),(0,0)}, then scale2 k=1 -> {(0,0),(2,0),(2,2)}.
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 2, 0, "red"),
            cell(&mut ir, 2, 2, "red"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(dict_get(&result, "length"), Value::Int(2));
        assert_eq!(
            dict_get(&result, "generators"),
            tuple_of(vec![
                Value::Str(ir.intern("reflection_r")),
                Value::Str(ir.intern("scale2"))
            ])
        );
        assert_eq!(
            dict_get(&result, "ks"),
            tuple_of(vec![Value::Int(1), Value::Int(1)])
        );
        assert_eq!(
            dict_get(&result, "latent_name"),
            surf("reflection_r+scale2")
        );
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
    }

    /// (11) ALIAS-NULL / Occam: a PURE ×2-scaled tromino
    /// {(0,0),(0,2),(2,0)} is explained by `scale2` ALONE — even with
    /// rotation90 ALSO in the codebook (which enables length-2
    /// compositions), the single-generator explanation must WIN because
    /// composition LENGTH is the strict-primary ranking key. Reports
    /// `length=1`, `generator="scale2"`, `k=1` — NO spurious 2-step. This
    /// is the analog of the rung-1<rung-2 order, inside rung 2.
    #[test]
    fn single_generator_explainable_stays_length1() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let tromino_sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            tromino_sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        add_generator(&mut g, &mut ir, gt, "scale2", "scale2", &[1, 2], &[1, 2, 3]);
        // Pure ×2 image of the tromino about its origin: {(0,0),(0,2),(2,0)}.
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 2, "red"),
            cell(&mut ir, 2, 0, "red"),
        ]);

        let result = run(&g, &mut ir, goal, t, gt, 2, "");
        assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
        assert_eq!(
            dict_get(&result, "length"),
            Value::Int(1),
            "a single-generator-explainable observation must stay length 1"
        );
        assert_eq!(
            dict_get(&result, "generator"),
            Value::Str(ir.intern("scale2"))
        );
        assert_eq!(dict_get(&result, "k"), Value::Int(1));
        assert_eq!(
            dict_get(&result, "generators"),
            tuple_of(vec![Value::Str(ir.intern("scale2"))])
        );
        assert_eq!(dict_get(&result, "ks"), tuple_of(vec![Value::Int(1)]));
        assert_eq!(dict_get(&result, "latent_name"), surf("scale2"));
        assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
    }

    // ----------------------------------------------------------------- //
    // THE `DimInfer` ARGUMENT AUDIT — VISION_DIM_INFER_ARGS_PREREG.md §3.
    //
    // A DISTINCTNESS statistic has TWO OPPOSITE failure modes and each one
    // FAKES one of the rung's two hypotheses:
    //
    //   encoding carries something incidental  ⇒ distinct == calls always
    //                                          ⇒ fakes IRREDUCIBLE
    //   encoding collapses a real determinant  ⇒ distinct == 1 always
    //                                          ⇒ fakes RE-DERIVATION
    //
    // Neither is caught by any gate that asks "is it non-zero?", and neither
    // is caught by G5 on the inherited N / K / PATH axes — on all three of
    // which the honest answer is a CONSTANT, so a broken counter and a
    // correct one are indistinguishable. These controls have ground truth
    // KNOWN BY CONSTRUCTION and are the reason the measurement can rule.
    // ----------------------------------------------------------------- //

    /// THE SCALE AUDIT IS PROCESS-GLOBAL, AND `cargo test` IS PARALLEL BY
    /// DEFAULT. Without this, two audit tests interleave `set_enabled` /
    /// `reset` and each reads the other's counts — which is exactly how these
    /// tests first failed (`calls` 15 where 7 was the ground truth, and the
    /// audit-OFF test reading 10). Recorded rather than papered over: it is
    /// PROTOCOL §11's shared-mutable-state hazard inside one process, and a
    /// distinctness gate is the last place that should be reading someone
    /// else's numbers. Run these with `--test-threads=1` as well; the lock
    /// makes them correct under either invocation.
    static AUDIT_TESTS: std::sync::Mutex<()> = std::sync::Mutex::new(());

    fn audit_guard() -> std::sync::MutexGuard<'static, ()> {
        AUDIT_TESTS.lock().unwrap_or_else(|e| e.into_inner())
    }

    /// D-RED — the COLLAPSE DETECTOR. Seven evaluations of the same decode
    /// against an unchanged graph. Ground truth, declared in the prereg
    /// before this existed: **calls 7, distinct 1, EXACTLY.**
    ///
    /// A counter reading 7 here is recording something that is not an
    /// argument — an address, a call counter, a load order — and would
    /// report the identity coefficient IRREDUCIBLE no matter what the
    /// engine actually did.
    #[test]
    fn d_red_identical_arguments_collapse_to_one() {
        let _g = audit_guard();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 1, "red"),
            cell(&mut ir, 1, 1, "red"),
        ]);

        let (calls, ord, unord) = witnessed(7, |_, w| {
            run_witnessed(&g, &mut ir, goal.clone(), t, gt, 2, "", w);
        });
        assert_eq!(calls, 7, "the recording site must see every invocation");
        assert_eq!(
            ord, 1,
            "seven IDENTICAL argument sets are ONE distinct tuple"
        );
        assert_eq!(unord, 1);
    }

    /// D-GREEN — DISCRIMINATION. Seven evaluations, each with a different
    /// goal. Ground truth: **calls 7, distinct 7, EXACTLY.**
    ///
    /// A counter reading 1 here has collapsed a real determinant and would
    /// report re-derivation that is not there.
    #[test]
    fn d_green_different_goals_are_seven_distinct() {
        let _g = audit_guard();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goals: Vec<Value> = (0..7)
            .map(|i| {
                tuple_of(vec![
                    cell(&mut ir, i, 0, "red"),
                    cell(&mut ir, i, 1, "red"),
                    cell(&mut ir, i + 1, 1, "red"),
                ])
            })
            .collect();

        let (calls, ord, unord) = witnessed(7, |i, w| {
            run_witnessed(&g, &mut ir, goals[i].clone(), t, gt, 2, "", w);
        });
        assert_eq!(calls, 7);
        assert_eq!(ord, 7, "seven DIFFERENT goals are seven distinct tuples");
        assert_eq!(unord, 7);
    }

    /// D-CODEBOOK — **the control that decides whether this rung can rule at
    /// all.** Seven evaluations with the SAME goal, the codebook grown by one
    /// part between each. Ground truth: **calls 7, distinct 7, EXACTLY.**
    ///
    /// The irreducibility hypothesis's entire content is *"a decode mints
    /// graph state, so the next invocation sees something different."* An
    /// encoder that covered only the goal would pass D-RED and D-GREEN and be
    /// STRUCTURALLY BLIND to exactly that mechanism — it would return
    /// `distinct = 1` and the rung would report re-derivation, confidently
    /// and wrongly. This is the positive control for the mechanism the
    /// negative hypothesis names.
    #[test]
    fn d_codebook_growth_is_seen_by_the_encoder() {
        let _g = audit_guard();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goal = tuple_of(vec![
            cell(&mut ir, 0, 0, "red"),
            cell(&mut ir, 0, 1, "red"),
            cell(&mut ir, 1, 1, "red"),
        ]);

        // ONE witness across the seven growth steps: the codebook changes
        // between decodes, so the distinctness being asserted is a property of
        // this sequence and of nothing else in the process.
        let mut w = crate::term::DimInferWitness::default();
        for i in 0..7i64 {
            run_witnessed(&g, &mut ir, goal.clone(), t, gt, 2, "", &mut w);
            // grow the codebook by one part — the mint the sd loop performs
            let grown = tuple_of(vec![
                cell(&mut ir, i + 10, 0, "blue"),
                cell(&mut ir, i + 10, 1, "blue"),
            ]);
            let name = format!("Grown{}", i);
            add_part(
                &mut g,
                &mut ir,
                t,
                &name,
                grown,
                &["pred", "coord:r", "coord:c", "val"],
            );
        }

        assert_eq!(w.calls(), 7);
        assert_eq!(
            w.distinct_ordered(),
            7,
            "codebook growth MUST change the encoding — this is the mechanism the \
             irreducibility hypothesis rests on, and an encoder blind to it cannot rule"
        );
        assert_eq!(w.distinct_unordered(), 7);
    }

    /// D-SWEEP — the G5 series. `J` distinct-goal decodes for `J` in 1..=7
    /// must read distinct = 1,2,…,7, and the fixed-`J` control must have span
    /// zero. This is the series the Python harness feeds to `g5.rs`; asserting
    /// it here means the harness cannot be the thing that makes it pass.
    #[test]
    fn d_sweep_distinct_tracks_its_axis() {
        let _g = audit_guard();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goals: Vec<Value> = (0..7)
            .map(|i| {
                tuple_of(vec![
                    cell(&mut ir, i, 0, "red"),
                    cell(&mut ir, i, 1, "red"),
                    cell(&mut ir, i + 1, 1, "red"),
                ])
            })
            .collect();

        let mut sweep = Vec::new();
        for j in 1..=7usize {
            let (_c, ord, _u) = witnessed(j, |i, w| {
                run_witnessed(&g, &mut ir, goals[i].clone(), t, gt, 2, "", w);
            });
            sweep.push(ord);
        }
        assert_eq!(sweep, vec![1, 2, 3, 4, 5, 6, 7]);

        let mut control = Vec::new();
        for _ in 0..7 {
            let (_c, ord, _u) = witnessed(1, |i, w| {
                run_witnessed(&g, &mut ir, goals[i].clone(), t, gt, 2, "", w);
            });
            control.push(ord);
        }
        assert_eq!(
            crate::g5::verdict(&sweep, &control),
            crate::g5::G5Verdict::Responsive
        );
    }

    /// DETERMINANT COVERAGE — every field §2.1 names must move the encoding.
    /// A determinant missing from the encoder is a blind spot that
    /// manufactures the re-derivation verdict, and the only way to know the
    /// list is complete is to vary each item and watch the bytes change.
    #[test]
    fn every_declared_determinant_changes_the_encoding() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goal_a = tuple_of(vec![cell(&mut ir, 0, 0, "red"), cell(&mut ir, 0, 1, "red")]);
        let goal_b = tuple_of(vec![cell(&mut ir, 5, 0, "red"), cell(&mut ir, 0, 1, "red")]);

        let ctx = EvalCtx::new(&g, &ir);
        let mut extra: FxHashMap<String, Sym> = FxHashMap::default();
        let mut next_id: u32 = u32::MAX;
        let parts = load_parts(&ctx, t, &mut extra, &mut next_id);
        let gens = load_generators(&ctx, gt);
        let ga: Vec<Value> = goal_a.iter().cloned().collect();
        let gb: Vec<Value> = goal_b.iter().cloned().collect();
        let fld = ir.intern("k");

        let base = encode_dim_infer_args(&parts, &gens, &ga, 2, Sym::default(), false);

        // goal
        assert_ne!(
            base,
            encode_dim_infer_args(&parts, &gens, &gb, 2, Sym::default(), false)
        );
        // max_dims
        assert_ne!(
            base,
            encode_dim_infer_args(&parts, &gens, &ga, 3, Sym::default(), false)
        );
        // field
        assert_ne!(
            base,
            encode_dim_infer_args(&parts, &gens, &ga, 2, fld, false)
        );
        // parts (the codebook)
        assert_ne!(
            base,
            encode_dim_infer_args(&parts[..0], &gens, &ga, 2, Sym::default(), false)
        );
        // generators
        assert_ne!(
            base,
            encode_dim_infer_args(&parts, &gens[..0], &ga, 2, Sym::default(), false)
        );
        // and identity: the same inputs encode identically, every time
        assert_eq!(
            base,
            encode_dim_infer_args(&parts, &gens, &ga, 2, Sym::default(), false)
        );
    }

    /// §9 — the site is INERT while the audit is off. A recording site that
    /// allocated or counted on the default path would contaminate every
    /// committed result.
    #[test]
    fn the_recording_site_is_silent_while_the_audit_is_off() {
        let _g = audit_guard();
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let t = ir.intern("ShapeSignature");
        let gt = ir.intern("DimensionGenerator");
        let sig = tromino(&mut ir);
        add_part(
            &mut g,
            &mut ir,
            t,
            "Base",
            sig,
            &["pred", "coord:r", "coord:c", "val"],
        );
        add_generator(
            &mut g,
            &mut ir,
            gt,
            "rotation90",
            "rotation90",
            &[1, 2],
            &[1, 2, 3],
        );
        let goal = tuple_of(vec![cell(&mut ir, 0, 0, "red"), cell(&mut ir, 0, 1, "red")]);

        // Reads process-global counters, so it needs the instrument's
        // exclusive guard; see scale_audit::exclusive().
        let _x = crate::scale_audit::exclusive();
        crate::scale_audit::set_enabled(false);
        crate::scale_audit::reset();
        for _ in 0..5 {
            run(&g, &mut ir, goal.clone(), t, gt, 2, "");
        }
        let m: std::collections::HashMap<String, u64> =
            crate::scale_audit::snapshot().into_iter().collect();
        assert_eq!(m["dim_infer_arg_calls"], 0);
        assert_eq!(m["dim_infer_arg_distinct_ordered"], 0);
        assert_eq!(m["dim_infer_arg_distinct_unordered"], 0);
    }
}

#[cfg(test)]
mod seed_json_shape_tests {
    use crate::jsonio::term_from_json;
    use crate::sym::Interner;
    use crate::term::{TermArena, TermNode};

    /// The EXACT invocation shape `seeds/shape_decode_loop.json`'s
    /// `sd_decode` rule uses (see its three `ShapeDecode` Computed
    /// effects) must parse cleanly — this is the seed author's contract
    /// with this Term's JSON schema. `sd_decode` sets `"wild_objects":
    /// true` (the induce_concern-covered semantics); this test also
    /// checks the absent-field (defaults `false`) case for back-compat.
    #[test]
    fn seed_shape_decode_invocations_parse() {
        for field in ["", "residual", "covered_count"] {
            for wild_objects in [None, Some(true), Some(false)] {
                let mut term_json = serde_json::json!({
                    "type": "ShapeDecode",
                    "goal": {
                        "type": "Attr",
                        "node": {"type": "Var", "name": "obs"},
                        "key": "signature"
                    },
                    "beam": 3,
                    "max_steps": 8,
                    "cand_k": 3
                });
                if !field.is_empty() {
                    term_json["field"] = serde_json::json!(field);
                }
                if let Some(w) = wild_objects {
                    term_json["wild_objects"] = serde_json::json!(w);
                }
                let mut arena = TermArena::new();
                let mut ir = Interner::new();
                let idx = term_from_json(&term_json, &mut arena, &mut ir).unwrap_or_else(|e| {
                    panic!("field={field:?} wild_objects={wild_objects:?} failed to parse: {e:?}")
                });
                let TermNode::ShapeDecode {
                    wild_objects: got, ..
                } = arena.get(idx)
                else {
                    panic!("expected ShapeDecode")
                };
                assert_eq!(
                    *got,
                    wild_objects.unwrap_or(false),
                    "field={field:?} wild_objects={wild_objects:?}"
                );
            }
        }
    }
}

/// `TransferDecode` tests — ANALOGICAL MECHANISM TRANSFER. Parity with the
/// documented Python outputs of `retrieve_and_transfer_mechanism` /
/// `transfer_mechanism` (see `tests/test_mechanism_transfer_migrated.py` and
/// `scripts/jabberwock_transfers_mechanism.py`). Mechanisms are the two seed
/// entries from `seeds/mechanism_index.json`, built here as `Value`s (the shim
/// passes them in as an evaluated Tuple-of-Dicts).
#[cfg(test)]
mod transfer_decode_tests {
    use super::*;
    use crate::graph::TypedGraph;
    use crate::term::TermNode;

    // NB: `ir` is the LAST parameter throughout so that when an argument list
    // both builds a `Value` (using `ir`) and forwards `ir`, the value-building
    // borrow is released before `ir` is re-borrowed for the call.
    fn s(x: &str, ir: &mut Interner) -> Value {
        Value::Str(ir.intern(x))
    }
    fn tup(items: Vec<Value>) -> Value {
        Value::Tuple(Arc::new(items.into_iter().collect()))
    }
    fn dic(pairs: Vec<(&str, Value)>, ir: &mut Interner) -> Value {
        let p: Vec<(Value, Value)> = pairs
            .into_iter()
            .map(|(k, v)| (Value::Str(ir.intern(k)), v))
            .collect();
        Value::Dict(Arc::from(p))
    }
    fn step(toks: &[&str], ir: &mut Interner) -> Value {
        tup(toks.iter().map(|t| s(t, ir)).collect())
    }
    fn slot(role: &str, cue: &str, cue_kind: &str, source: &str, ir: &mut Interner) -> Value {
        dic(
            vec![
                ("role", s(role, ir)),
                ("cue", s(cue, ir)),
                ("cue_kind", s(cue_kind, ir)),
                ("source", s(source, ir)),
            ],
            ir,
        )
    }

    /// Insert one `Mechanism` node into the graph with `slots` (a Tuple-of-
    /// Dict) and `steps` (a Tuple-of-Tuple) attrs — mirroring one
    /// `seeds/mechanism_index.json` entry as it lands on boot. This is what the
    /// graph-native `load_mechanisms` reads (was a Lit-arg Tuple-of-Dicts).
    fn add_mech(
        g: &mut TypedGraph,
        ir: &mut Interner,
        name: &str,
        meta_shape: &str,
        domain: &str,
        slots: Value,
        steps: Value,
    ) {
        let t = ir.intern("Mechanism");
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("name"), s(name, ir));
        attrs.insert(ir.intern("meta_shape"), s(meta_shape, ir));
        attrs.insert(ir.intern("domain"), s(domain, ir));
        attrs.insert(ir.intern("slots"), slots);
        attrs.insert(ir.intern("steps"), steps);
        g.insert_node(t, attrs);
    }

    /// Insert one `MetaShape{name}` -has_principle-> `Principle{name, keywords}`
    /// into the graph — the minimal shape-vocabulary datum the SHARED
    /// `recognise_meta_shape` scorer reads. `TransferDecode` now DERIVES the
    /// goal's meta-shape from this vocabulary (was a Term arg), so every transfer
    /// test needs enough vocabulary for its goal text to score the intended
    /// shape. Keywords are matched as SUBSTRINGS of the lowercased goal text,
    /// exactly as `domains/teach.py::categorise_by_shape` does.
    fn add_shape(g: &mut TypedGraph, ir: &mut Interner, name: &str, keywords: &[&str]) {
        let kws: Value = tup(keywords.iter().map(|k| s(k, ir)).collect());
        let ms_t = ir.intern("MetaShape");
        let mut ms_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        ms_attrs.insert(ir.intern("name"), s(name, ir));
        let shape_id = g.insert_node(ms_t, ms_attrs);
        let p_t = ir.intern("Principle");
        let mut p_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        p_attrs.insert(ir.intern("name"), s(&format!("{name}_principle"), ir));
        p_attrs.insert(ir.intern("keywords"), kws);
        let p_id = g.insert_node(p_t, p_attrs);
        let hp = ir.intern("has_principle");
        g.insert_edge(shape_id, hp, p_id, FxHashMap::<Sym, Value>::default())
            .expect("has_principle edge");
    }

    /// The minimal `MetaShape` vocabulary the transfer tests need: distinct
    /// substring keywords that pick out each goal's intended shape and nothing
    /// else (`gate`→selective_gating, `feedback`→feedback_control,
    /// `broadcast`→global_message_passing — the last has NO indexed mechanism,
    /// for the honest-wall test).
    fn add_shape_vocab(g: &mut TypedGraph, ir: &mut Interner) {
        add_shape(g, ir, "selective_gating", &["gate"]);
        add_shape(g, ir, "feedback_control", &["feedback"]);
        add_shape(g, ir, "global_message_passing", &["broadcast"]);
    }

    /// Insert the seed's `CodebookRegistry` declaration — the graph datum that
    /// NAMES `Mechanism` as the mechanism-transfer codebook node-type, replacing
    /// the former `mechanism_type` Term arg. `eval_transfer_decode` discovers the
    /// type through this node; without it the read is gated off (the no-op).
    fn add_registry(g: &mut TypedGraph, ir: &mut Interner) {
        let t = ir.intern("CodebookRegistry");
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("role"), s("mechanism_transfer", ir));
        attrs.insert(ir.intern("node_type"), s("Mechanism", ir));
        g.insert_node(t, attrs);
    }

    /// The two seed `Mechanism` entries as graph nodes, WITHOUT the registry
    /// declaration (insertion order: spatial_foveation, then
    /// homeostatic_regulation — matching the seed).
    fn mech_graph_bare(ir: &mut Interner) -> TypedGraph {
        let mut g = TypedGraph::new();
        let fov_slots = tup(vec![
            slot("FIELD", "scan", "verb", "space", ir),
            slot("FOCUS", "to", "prep", "focus", ir),
            slot("UNIT", "by", "prep", "quanta", ir),
        ]);
        let fov_steps = tup(vec![
            step(&["quantize", "FIELD", "into", "UNIT"], ir),
            step(&["decode", "only", "FIELD", "in", "FOCUS"], ir),
            step(&["index", "FIELD", "by", "UNIT"], ir),
        ]);
        add_mech(
            &mut g,
            ir,
            "spatial_foveation",
            "selective_gating",
            "space",
            fov_slots,
            fov_steps,
        );
        let reg_slots = tup(vec![
            slot("MEASURED", "measure", "verb", "temperature", ir),
            slot("SETPOINT", "to", "prep", "target", ir),
            slot("ACTUATOR", "correct", "verb", "heater", ir),
        ]);
        let reg_steps = tup(vec![
            step(&["measure", "MEASURED"], ir),
            step(&["compare", "MEASURED", "to", "SETPOINT"], ir),
            step(&["correct", "ACTUATOR", "toward", "SETPOINT"], ir),
        ]);
        add_mech(
            &mut g,
            ir,
            "homeostatic_regulation",
            "feedback_control",
            "thermoregulation",
            reg_slots,
            reg_steps,
        );
        // The shape vocabulary the SHARED recogniser reads — `TransferDecode`
        // now DERIVES the goal's meta-shape from it (was a Term arg).
        add_shape_vocab(&mut g, ir);
        g
    }

    /// The full seed graph as it boots: the two `Mechanism` entries PLUS the
    /// `CodebookRegistry` declaration that names their type. This is what
    /// `eval_transfer_decode` reads on a live agent.
    fn mech_graph(ir: &mut Interner) -> TypedGraph {
        let mut g = mech_graph_bare(ir);
        add_registry(&mut g, ir);
        g
    }

    fn foveation_goal(ir: &mut Interner) -> Value {
        tup(vec![
            step(&["scan", "EVERY", "RULE", "per", "EVENT"], ir),
            step(&["match", "over", "the", "WHOLE", "FRAME", "SET"], ir),
            step(&["gate", "the", "SCAN", "to", "the", "FOCUS"], ir),
            step(&["index", "the", "RULES", "by", "EVENT", "TYPE"], ir),
            step(
                &[
                    "decode", "only", "RULES", "in", "FOCUS", "for", "this", "TYPE",
                ],
                ir,
            ),
        ])
    }
    fn regulation_goal(ir: &mut Interner) -> Value {
        tup(vec![
            step(&["measure", "the", "current", "FIRING", "RATE"], ir),
            step(&["compare", "RATE", "to", "the", "set_point", "BUDGET"], ir),
            step(
                &["regulate", "by", "FEEDBACK", "toward", "the", "BUDGET"],
                ir,
            ),
            step(
                &["correct", "the", "SCHEDULER", "toward", "the", "BUDGET"],
                ir,
            ),
        ])
    }

    /// Build a `TransferDecode` reading the mechanism codebook FROM THE GRAPH
    /// `g` (built with the SAME interner `ir`, so type/attr syms resolve). The
    /// codebook node-TYPE is DISCOVERED from `g`'s `CodebookRegistry` node, and
    /// the goal's meta-shape is DERIVED from `g`'s `MetaShape` vocabulary — no
    /// `mechanism_type` and no `meta_shape` args (both removed: the registry and
    /// the shared `recognise_meta_shape` scorer replaced them).
    fn run(ir: &mut Interner, g: &TypedGraph, goal: Value) -> Value {
        let mut a = TermArena::new();
        let goal_t = a.add(TermNode::Lit { value: goal });
        let idx = a.add(TermNode::TransferDecode { goal: goal_t });
        let mut env: Env = Env::new();
        let mut ctx = EvalCtx::new(g, ir);
        evaluate(&a, idx, &mut env, &mut ctx)
    }

    fn rd(v: &Value, key: &str) -> Value {
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
    fn as_str(v: &Value) -> Option<String> {
        match v {
            Value::Surface(SurfaceKind::Text, b) => Some(String::from_utf8_lossy(b).to_string()),
            Value::Str(_) => Some("<interned>".into()),
            _ => None,
        }
    }
    fn strvec(v: &Value) -> Vec<String> {
        match v {
            Value::Tuple(items) | Value::List(items) => items.iter().filter_map(as_str).collect(),
            _ => Vec::new(),
        }
    }
    fn plan_of(v: &Value) -> Vec<Vec<String>> {
        match v {
            Value::Tuple(items) | Value::List(items) => items.iter().map(strvec).collect(),
            _ => Vec::new(),
        }
    }

    /// (1) THE CLASS CLOSES — the foveation/rule-index concern transfers the
    /// spatial_foveation mechanism, total_fit 3, plan in the RULE domain.
    #[test]
    fn foveation_transfer_matches_python() {
        let mut ir = Interner::new();
        let g = mech_graph(&mut ir);
        let goal = foveation_goal(&mut ir);
        let r = run(&mut ir, &g, goal);

        assert_eq!(
            as_str(&rd(&r, "meta_shape")).as_deref(),
            Some("selective_gating")
        );
        assert_eq!(
            strvec(&rd(&r, "retrieved")),
            vec!["spatial_foveation".to_string()]
        );

        let t = rd(&r, "transferred");
        assert_eq!(rd(&t, "total_fit"), Value::Int(3));
        assert_eq!(
            as_str(&rd(&t, "mechanism")).as_deref(),
            Some("spatial_foveation")
        );
        assert_eq!(as_str(&rd(&t, "source_domain")).as_deref(), Some("space"));
        let plan = plan_of(&rd(&t, "plan"));
        assert_eq!(
            plan,
            vec![
                vec!["quantize", "RULE", "into", "EVENT_TYPE"],
                vec!["decode", "only", "RULE", "in", "FOCUS"],
                vec!["index", "RULE", "by", "EVENT_TYPE"],
            ]
        );
        // slot_map fillers derived from the goal, not the mechanism's source.
        let sm = rd(&t, "slot_map");
        assert_eq!(
            as_str(&rd(&rd(&sm, "FIELD"), "target")).as_deref(),
            Some("RULE")
        );
        assert_eq!(
            as_str(&rd(&rd(&sm, "FOCUS"), "target")).as_deref(),
            Some("FOCUS")
        );
        assert_eq!(
            as_str(&rd(&rd(&sm, "UNIT"), "target")).as_deref(),
            Some("EVENT_TYPE")
        );
        assert_eq!(
            as_str(&rd(&rd(&sm, "FIELD"), "cue")).as_deref(),
            Some("scan")
        );
        assert_eq!(strvec(&rd(&t, "unbound_roles")), Vec::<String>::new());
    }

    /// (2) GENERALISES — a DIFFERENT meta-shape transfers a DIFFERENT held
    /// mechanism through the same op.
    #[test]
    fn feedback_transfer_matches_python() {
        let mut ir = Interner::new();
        let g = mech_graph(&mut ir);
        let goal = regulation_goal(&mut ir);
        let r = run(&mut ir, &g, goal);

        assert_eq!(
            strvec(&rd(&r, "retrieved")),
            vec!["homeostatic_regulation".to_string()]
        );
        let t = rd(&r, "transferred");
        assert_eq!(rd(&t, "total_fit"), Value::Int(3));
        assert_eq!(
            as_str(&rd(&t, "mechanism")).as_deref(),
            Some("homeostatic_regulation")
        );
        let plan = plan_of(&rd(&t, "plan"));
        assert_eq!(
            plan,
            vec![
                vec!["measure", "FIRING_RATE"],
                vec!["compare", "FIRING_RATE", "to", "BUDGET"],
                vec!["correct", "SCHEDULER", "toward", "BUDGET"],
            ]
        );
    }

    /// (3) TRANSFER, NOT LOOKUP — a different goal of the SAME shape yields a
    /// different plan carrying the new goal's fillers; the mechanism's own
    /// source fillers (space/quanta) never appear.
    #[test]
    fn transfer_not_lookup_carries_goal_fillers() {
        let mut ir = Interner::new();
        let g = mech_graph(&mut ir);
        let other = tup(vec![
            step(&["scan", "EVERY", "PACKET", "per", "TICK"], &mut ir),
            step(&["gate", "the", "SCAN", "to", "the", "PORT"], &mut ir),
            step(&["index", "the", "PACKETS", "by", "FLOW"], &mut ir),
        ]);
        let r = run(&mut ir, &g, other);
        let t = rd(&r, "transferred");
        let toks: std::collections::HashSet<String> =
            plan_of(&rd(&t, "plan")).into_iter().flatten().collect();
        assert!(toks.contains("PACKET"));
        assert!(toks.contains("FLOW"));
        assert!(!toks.contains("space"));
        assert!(!toks.contains("quanta"));
        assert!(!toks.contains("RULE"));
    }

    /// (4) HONEST WALL — a recognised shape with no indexed mechanism returns
    /// transferred=None, retrieved=[].
    #[test]
    fn recognised_shape_with_no_mechanism_is_wall() {
        let mut ir = Interner::new();
        let g = mech_graph(&mut ir);
        // "broadcast x" derives global_message_passing (the vocab keyword), but
        // NO mechanism is indexed under that shape ⇒ the honest wall.
        let goal = tup(vec![step(&["broadcast", "X"], &mut ir)]);
        let r = run(&mut ir, &g, goal);
        assert_eq!(rd(&r, "transferred"), Value::None);
        assert_eq!(strvec(&rd(&r, "retrieved")), Vec::<String>::new());
        assert_eq!(
            as_str(&rd(&r, "meta_shape")).as_deref(),
            Some("global_message_passing")
        );
        assert!(matches!(
            rd(&r, "note"),
            Value::Surface(SurfaceKind::Text, _)
        ));
    }

    /// (5) NO SHAPE — a goal whose text matches NO shape keyword derives
    /// meta_shape=None (the shared recogniser returns None), so the Term returns
    /// transferred=None with the honest-fallback note.
    #[test]
    fn no_meta_shape_is_honest_fallback() {
        let mut ir = Interner::new();
        let g = mech_graph(&mut ir);
        // No vocabulary keyword (gate/feedback/broadcast) is a substring of
        // "qqq zzz" ⇒ no shape recognised ⇒ mint stays the honest fallback.
        let goal = tup(vec![step(&["qqq", "ZZZ"], &mut ir)]);
        let r = run(&mut ir, &g, goal);
        assert_eq!(rd(&r, "meta_shape"), Value::None);
        assert_eq!(rd(&r, "transferred"), Value::None);
        assert_eq!(strvec(&rd(&r, "retrieved")), Vec::<String>::new());
    }

    /// (6) THE REGISTRY GATES THE READ — `Mechanism` nodes present but NO
    /// `CodebookRegistry` declaration ⇒ the Term cannot discover the codebook
    /// node-type, so the codebook is empty and it returns `Value::None`, exactly
    /// the default-boot no-op. Proves the read is driven by the graph registry,
    /// not a literal: the SAME mechanisms + shape that transfer under
    /// `foveation_transfer_matches_python` produce nothing without the registry.
    #[test]
    fn no_registry_returns_none() {
        let mut ir = Interner::new();
        let g = mech_graph_bare(&mut ir);
        let goal = foveation_goal(&mut ir);
        let r = run(&mut ir, &g, goal);
        assert_eq!(r, Value::None);
    }

    /// (7) RECOGNISE_SHAPE — the shared scorer as a standalone Term. The goal
    /// text scores the intended shape (most-overlap argmax), returns None on no
    /// match, and higher overlap wins a contest (deterministic `(-score, name)`).
    #[test]
    fn recognise_shape_scores_and_argmaxes() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        add_shape_vocab(&mut g, &mut ir);
        // A shape with TWO principles (each a distinct keyword), so when a text
        // matches BOTH it outscores a single-principle shape whose keyword also
        // matches — proving the most-overlap argmax, not a first-hit lookup.
        let ms_t = ir.intern("MetaShape");
        let mut ms_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        ms_attrs.insert(ir.intern("name"), s("aa_strong", &mut ir));
        let strong_id = g.insert_node(ms_t, ms_attrs);
        let hp = ir.intern("has_principle");
        let p_t = ir.intern("Principle");
        for (pname, kw) in [("aa_p1", "gate"), ("aa_p2", "focus")] {
            let kws = tup(vec![s(kw, &mut ir)]);
            let mut p_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
            p_attrs.insert(ir.intern("name"), s(pname, &mut ir));
            p_attrs.insert(ir.intern("keywords"), kws);
            let p_id = g.insert_node(p_t, p_attrs);
            g.insert_edge(strong_id, hp, p_id, FxHashMap::<Sym, Value>::default())
                .unwrap();
        }

        let run_rec = |ir: &mut Interner, g: &TypedGraph, text: &str| -> Value {
            let mut a = TermArena::new();
            let txt = a.add(TermNode::Lit {
                value: Value::Str(ir.intern(text)),
            });
            let idx = a.add(TermNode::RecogniseShape { text: txt });
            let mut env: Env = Env::new();
            let mut ctx = EvalCtx::new(g, ir);
            evaluate(&a, idx, &mut env, &mut ctx)
        };

        // RecogniseShape returns the MetaShape's `name` (an interned Str), so
        // resolve it through the interner (`td_val_to_string`), not `as_str`
        // (which stubs interned Strs as "<interned>").
        // "feedback" only → feedback_control.
        let r1 = run_rec(&mut ir, &g, "regulate by feedback");
        assert_eq!(
            td_val_to_string(&r1, &ir).as_deref(),
            Some("feedback_control")
        );
        // "gate focus" → both selective_gating(1) and aa_strong(2) match; the
        // 2-principle aa_strong wins by overlap.
        let r2 = run_rec(&mut ir, &g, "gate the focus");
        assert_eq!(td_val_to_string(&r2, &ir).as_deref(), Some("aa_strong"));
        // no keyword substring → None.
        assert_eq!(run_rec(&mut ir, &g, "qqq zzz"), Value::None);
        // empty text → None (the `if not text` guard).
        assert_eq!(run_rec(&mut ir, &g, ""), Value::None);
    }
}

#[cfg(test)]
mod motion_energy_tests {
    //! Locks the `MotionEnergy` mechanism at the engine (PROTOCOL: verify
    //! behaviour against the engine, never a doc comment). The Python runner
    //! ALSO re-derives this independently in numpy and agrees to machine
    //! precision (8.8e-16 on C-POS); this is the Rust-native twin.
    use super::motion_energy_spectrum;

    // one HxW frame with a DOTxDOT square at column `col` (None => blank).
    fn frame(h: usize, w: usize, col: Option<usize>) -> Vec<f64> {
        let mut f = vec![0.0f64; h * w];
        if let Some(c) = col {
            for r in 2..(h.min(6)) {
                for x in c..(c + 4).min(w) {
                    f[r * w + x] = 255.0;
                }
            }
        }
        f
    }
    fn get(v: &[(&'static str, f64)], k: &str) -> f64 {
        v.iter().find(|(n, _)| *n == k).map(|(_, x)| *x).unwrap()
    }

    #[test]
    fn rightward_continuous_motion_reads_opponent_positive() {
        let (h, w) = (6usize, 24usize);
        let frames = vec![
            frame(h, w, Some(0)),
            frame(h, w, Some(4)),
            frame(h, w, Some(8)),
        ];
        let r = motion_energy_spectrum(&frames, h, w, 3);
        assert!(get(&r, "opponent") > 0.0, "rightward => opponent>0");
        assert!(get(&r, "right") > get(&r, "left"));
    }

    #[test]
    fn leftward_continuous_motion_flips_the_sign() {
        let (h, w) = (6usize, 24usize);
        let frames = vec![
            frame(h, w, Some(8)),
            frame(h, w, Some(4)),
            frame(h, w, Some(0)),
        ];
        let r = motion_energy_spectrum(&frames, h, w, 3);
        assert!(get(&r, "opponent") < 0.0, "leftward => opponent<0");
    }

    #[test]
    fn two_frame_pair_is_direction_ambiguous_forced_zero() {
        // ISI=0: only DC + Nyquist temporal freqs; Nyquist is direction-
        // ambiguous, so opponent cancels to ~0 relative to total_ac.
        let (h, w) = (6usize, 24usize);
        let frames = vec![frame(h, w, Some(0)), frame(h, w, Some(8))];
        let r = motion_energy_spectrum(&frames, h, w, 2);
        let opp = get(&r, "opponent").abs();
        let tot = get(&r, "total_ac").max(1.0);
        assert!(opp / tot < 1e-9, "opponent/total_ac = {} not ~0", opp / tot);
    }

    #[test]
    fn static_field_invents_no_directional_motion() {
        let (h, w) = (6usize, 24usize);
        let f = frame(h, w, Some(0));
        let frames = vec![f.clone(), f];
        let r = motion_energy_spectrum(&frames, h, w, 2);
        let opp = get(&r, "opponent").abs();
        let tot = get(&r, "total_ac").max(1.0);
        assert!(opp / tot < 1e-9, "static => no direction");
    }

    #[test]
    fn degenerate_inputs_are_all_zero_not_a_panic() {
        assert_eq!(get(&motion_energy_spectrum(&[], 6, 24, 0), "opponent"), 0.0);
        let one = vec![frame(6, 24, Some(0))];
        assert_eq!(
            get(&motion_energy_spectrum(&one, 6, 24, 1), "total_ac"),
            0.0
        );
    }
}

// ===========================================================================
//  META-SHAPE AS A FIRST-CLASS GRAIN — unit gates
//  (docs/research/engine_substrate/META_SHAPE_FIRST_CLASS_RESULTS.md)
// ===========================================================================
#[cfg(test)]
mod meta_shape_first_class_tests {
    use super::*;
    use crate::graph::TypedGraph;
    use crate::term::TermNode;

    fn s(x: &str, ir: &mut Interner) -> Value {
        Value::Str(ir.intern(x))
    }
    fn tup(items: Vec<Value>) -> Value {
        Value::Tuple(Arc::new(items.into_iter().collect()))
    }

    /// `MetaShape{name}` -has_principle-> `Principle{name, keywords}`.
    fn add_shape(g: &mut TypedGraph, ir: &mut Interner, name: &str, keywords: &[&str]) {
        let kws: Value = tup(keywords.iter().map(|k| s(k, ir)).collect());
        let ms_t = ir.intern("MetaShape");
        let mut ms_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        ms_attrs.insert(ir.intern("name"), s(name, ir));
        let shape_id = g.insert_node(ms_t, ms_attrs);
        let p_t = ir.intern("Principle");
        let mut p_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        p_attrs.insert(ir.intern("name"), s(&format!("{name}_principle"), ir));
        p_attrs.insert(ir.intern("keywords"), kws);
        let p_id = g.insert_node(p_t, p_attrs);
        let hp = ir.intern("has_principle");
        g.insert_edge(shape_id, hp, p_id, FxHashMap::<Sym, Value>::default())
            .expect("has_principle edge");
    }

    /// A `[predicate, value]` relation set, the shape `domains/meta_shape.py::
    /// item_signature` emits (sorted by predicate).
    fn sig(rels: &[(&str, &str)], ir: &mut Interner) -> Value {
        let mut r: Vec<(String, String)> = rels
            .iter()
            .map(|(p, v)| (p.to_string(), v.to_string()))
            .collect();
        r.sort();
        tup(r
            .iter()
            .map(|(p, v)| tup(vec![s(p, ir), s(v, ir)]))
            .collect())
    }

    fn recognise(ir: &mut Interner, g: &TypedGraph, input: Value) -> Value {
        let mut a = TermArena::new();
        let t = a.add(TermNode::Lit { value: input });
        let idx = a.add(TermNode::RecogniseShape { text: t });
        let mut env: Env = Env::new();
        let mut ctx = EvalCtx::new(g, ir);
        evaluate(&a, idx, &mut env, &mut ctx)
    }

    fn name_of(v: &Value, ir: &Interner) -> Option<String> {
        td_val_to_string(v, ir).filter(|s| !s.is_empty())
    }

    // ---------------------------------------------------------------- AR1 --

    /// THE ALPHABETICAL TIEBREAK IS GONE. Two shapes, one keyword each, both
    /// present: the old scorer returned the alphabetically-first
    /// (`aardvark_shape`). A genuine tie is now a RESIDUAL, not an answer —
    /// which is what makes it a mint candidate.
    #[test]
    fn a_genuine_tie_is_a_residual_not_the_alphabetically_first_shape() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        add_shape(&mut g, &mut ir, "aardvark_shape", &["alpha"]);
        add_shape(&mut g, &mut ir, "zebra_shape", &["omega"]);
        let text = s("alpha and omega", &mut ir);
        assert_eq!(recognise(&mut ir, &g, text), Value::None);
    }

    /// …and an UNTIED contest still resolves, exactly as before: the scorer
    /// refuses only what it genuinely cannot decide.
    #[test]
    fn an_untied_contest_still_resolves() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        add_shape(&mut g, &mut ir, "aardvark_shape", &["alpha"]);
        add_shape(&mut g, &mut ir, "zebra_shape", &["omega"]);
        let text = s("only omega here", &mut ir);
        assert_eq!(
            name_of(&recognise(&mut ir, &g, text), &ir),
            Some("zebra_shape".to_string())
        );
    }

    /// DISTINCT KEYWORD HITS BREAK WHAT USED TO BREAK ALPHABETICALLY. Both
    /// shapes score ONE principle (the old score), so the old scorer tied and
    /// took `aardvark_shape`; `zebra_shape` matched TWO of its keywords and now
    /// wins on evidence. This is the `"gate the layer by policy"` case,
    /// minimised.
    #[test]
    fn more_keyword_evidence_beats_less_at_equal_principle_count() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        add_shape(&mut g, &mut ir, "aardvark_shape", &["layer"]);
        add_shape(&mut g, &mut ir, "zebra_shape", &["gate", "policy"]);
        let text = s("gate the layer by policy", &mut ir);
        assert_eq!(
            name_of(&recognise(&mut ir, &g, text), &ir),
            Some("zebra_shape".to_string())
        );
    }

    /// A TYPED SLOT OUTRANKS PROSE. `predict` appears as a relation PREDICATE
    /// for one shape and only inside another relation's VALUE for the other.
    /// The old scorer could not see the predicate at all (`teach.py:93`
    /// discarded every attribute key), so this observation scored only the
    /// prose shape.
    #[test]
    fn a_predicate_hit_outranks_a_prose_hit() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        add_shape(&mut g, &mut ir, "prose_shape", &["frame"]);
        add_shape(&mut g, &mut ir, "slot_shape", &["predict"]);
        let obs = sig(
            &[("predict", "the next frame"), ("is_a", "belief")],
            &mut ir,
        );
        assert_eq!(
            name_of(&recognise(&mut ir, &g, obs), &ir),
            Some("slot_shape".to_string())
        );
    }

    /// The legacy FLAT-TEXT path is still reachable and still scores — the Term
    /// is input-polymorphic, not switched over. `TransferDecode` depends on it.
    #[test]
    fn the_flat_text_path_still_scores() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        add_shape(&mut g, &mut ir, "feedback_control", &["feedback"]);
        let text = s("regulate by feedback toward the budget", &mut ir);
        assert_eq!(
            name_of(&recognise(&mut ir, &g, text), &ir),
            Some("feedback_control".to_string())
        );
    }

    // ---------------------------------------------------------------- AR3 --

    fn add_obs(g: &mut TypedGraph, ir: &mut Interner, status: &str, sg: Value) {
        let t = ir.intern("ShapeObservation");
        let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        attrs.insert(ir.intern("signature"), sg);
        attrs.insert(ir.intern("status"), s(status, ir));
        g.insert_node(t, attrs);
    }

    fn mint_field(ir: &mut Interner, g: &TypedGraph, obs_idx: usize, field: &str) -> Value {
        let ids = g.nodes_of_type(ir.lookup("ShapeObservation").unwrap());
        let obs = ids[obs_idx];
        let obs_type = ir.intern("ShapeObservation");
        let status_value = ir.intern("residual");
        let wild = ir.intern("·?·");
        let f = ir.intern(field);
        let mut a = TermArena::new();
        let ot = a.add(TermNode::Lit {
            value: Value::Node(obs),
        });
        let idx = a.add(TermNode::MetaShapeMint {
            observation: ot,
            obs_type,
            status_value,
            wild,
            field: f,
        });
        let mut env: Env = Env::new();
        let mut ctx = EvalCtx::new(g, ir);
        evaluate(&a, idx, &mut env, &mut ctx)
    }

    /// ONE OCCURRENCE IS NOT RECURRENCE. Support 1 ⇒ not mintable. This is the
    /// whole support discipline: two is the smallest cardinality at which
    /// "recurs" is defined, and it is a definitional boundary, not a knob.
    #[test]
    fn a_single_observation_does_not_mint() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let a1 = sig(&[("buyer", "alice"), ("lot", "7")], &mut ir);
        add_obs(&mut g, &mut ir, "residual", a1);
        assert_eq!(mint_field(&mut ir, &g, 0, "support"), Value::Int(1));
        assert_eq!(mint_field(&mut ir, &g, 0, "mintable"), Value::Int(0));
    }

    /// RECURRENCE MINTS — and the core is the anti-unified lgg: the predicates
    /// the group agrees on stay FIXED, the values it disagrees on become WILD.
    /// That pattern is exactly what rung 1's `Covers` needs to recognise the
    /// NEXT member of the family without minting again.
    #[test]
    fn a_recurring_slot_skeleton_is_mintable_with_a_wild_bearing_core() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let a1 = sig(&[("buyer", "alice"), ("lot", "7")], &mut ir);
        let a2 = sig(&[("buyer", "carol"), ("lot", "9")], &mut ir);
        add_obs(&mut g, &mut ir, "residual", a1);
        add_obs(&mut g, &mut ir, "residual", a2);
        assert_eq!(mint_field(&mut ir, &g, 0, "support"), Value::Int(2));
        assert_eq!(mint_field(&mut ir, &g, 0, "mintable"), Value::Int(1));
        // the name is CONTENT-derived from the SORTED predicate set — never
        // positional, never truncated (contrast SHAPE_AUDIT.md §3.1).
        assert_eq!(
            td_val_to_string(&mint_field(&mut ir, &g, 0, "name"), &ir),
            Some("ms_buyer_lot".to_string())
        );
        // and the core still covers a NEVER-SEEN variant of the same skeleton.
        let core = mint_field(&mut ir, &g, 0, "signature");
        let variant = sig(&[("buyer", "erin"), ("lot", "11")], &mut ir);
        let wild = wild_value(ir.intern("·?·"));
        assert!(covers_value(&core, &variant, &wild));
    }

    /// EXACTLY ONE MINTER PER GROUP PER PASS. Both members report the same name
    /// and the same core, but only the canonical representative (lowest node
    /// id) is `mintable` — so a group of N mints once, not N times.
    #[test]
    fn only_the_group_leader_mints() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let a1 = sig(&[("buyer", "alice"), ("lot", "7")], &mut ir);
        let a2 = sig(&[("buyer", "carol"), ("lot", "9")], &mut ir);
        add_obs(&mut g, &mut ir, "residual", a1);
        add_obs(&mut g, &mut ir, "residual", a2);
        assert_eq!(mint_field(&mut ir, &g, 0, "leader"), Value::Int(1));
        assert_eq!(mint_field(&mut ir, &g, 1, "leader"), Value::Int(0));
        assert_eq!(mint_field(&mut ir, &g, 1, "mintable"), Value::Int(0));
    }

    /// TWO UNRELATED RESIDUALS ARE NOT A FAMILY. Different predicate sets ⇒
    /// different groups ⇒ support 1 each ⇒ no mint. Grouping is structural.
    #[test]
    fn unrelated_residuals_do_not_group() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let a1 = sig(&[("buyer", "alice"), ("lot", "7")], &mut ir);
        let a2 = sig(&[("marker", "however"), ("role", "contrast")], &mut ir);
        add_obs(&mut g, &mut ir, "residual", a1);
        add_obs(&mut g, &mut ir, "residual", a2);
        assert_eq!(mint_field(&mut ir, &g, 0, "support"), Value::Int(1));
        assert_eq!(mint_field(&mut ir, &g, 1, "support"), Value::Int(1));
        assert_eq!(mint_field(&mut ir, &g, 0, "mintable"), Value::Int(0));
    }

    /// A UNIVERSAL PREDICATE CARRIES NO INFORMATION AND IS DROPPED FROM THE
    /// MINTED KEYWORDS. `is_a` is in every observation by construction; left in,
    /// the minted shape scored a predicate hit on literally everything and won
    /// the keyword prior against the correct answer (measured live, §4.2). The
    /// group KEY still uses the full predicate set — only the weak keyword rung
    /// is narrowed.
    #[test]
    fn a_universal_predicate_is_dropped_from_the_minted_keywords() {
        let mut ir = Interner::new();
        let mut g = TypedGraph::new();
        let a1 = sig(
            &[("is_a", "trade"), ("buyer", "alice"), ("lot", "7")],
            &mut ir,
        );
        let a2 = sig(
            &[("is_a", "trade"), ("buyer", "carol"), ("lot", "9")],
            &mut ir,
        );
        let other = sig(&[("is_a", "note"), ("text", "unrelated")], &mut ir);
        add_obs(&mut g, &mut ir, "residual", a1);
        add_obs(&mut g, &mut ir, "residual", a2);
        add_obs(&mut g, &mut ir, "recognized", other); // outside the group
                                                       // identity keeps every predicate...
        assert_eq!(
            td_val_to_string(&mint_field(&mut ir, &g, 0, "name"), &ir),
            Some("ms_buyer_is_a_lot".to_string())
        );
        // ...the keywords keep only the discriminative ones.
        let keys = mint_field(&mut ir, &g, 0, "keys");
        let got: Vec<String> = match &keys {
            Value::Tuple(items) | Value::List(items) => items
                .iter()
                .filter_map(|v| td_val_to_string(v, &ir))
                .collect(),
            _ => Vec::new(),
        };
        assert_eq!(got, vec!["buyer".to_string(), "lot".to_string()]);
    }

    /// AN OBSERVER WHO KNOWS NOTHING MUST SEE NOTHING.
    ///
    /// A present-but-EMPTY `codebook_scope` used to fall through an
    /// `!is_empty()` guard and leave the codebook UNRESTRICTED — documented as
    /// mirroring `apply_exclude`. The mirroring was the error: scope and exclude
    /// are DUALS, so excluding an empty set is a no-op while scoping to one is
    /// TOTAL restriction. The effect was that the least-informed observer scored
    /// the whole codebook's maximum, silently — the one inversion a social
    /// simulation cannot tolerate.
    ///
    /// `Value::None` must stay unrestricted, and that half is load-bearing:
    /// `seeds/reflex_net.json` passes `Attr(rn, basin_parts)` while no node in
    /// that seed carries the attribute, so every net takes that path.
    #[test]
    fn an_empty_scope_is_a_declaration_but_a_none_scope_is_not() {
        use crate::value::Value;

        assert!(
            !scope_is_declared(&Value::None),
            "Value::None must leave the codebook unrestricted (reflex_net)"
        );

        assert!(
            scope_is_declared(&Value::List(std::sync::Arc::new(Default::default()))),
            "a PRESENT-BUT-EMPTY scope declares 'knows nothing' and must restrict"
        );

        assert!(
            scope_is_declared(&Value::List(std::sync::Arc::new(smallvec::smallvec![
                Value::Str(Sym::default())
            ]))),
            "a named scope declares a restriction"
        );
    }
}
