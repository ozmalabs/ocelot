//! `ProgEval` — the ONE pure fueled interpreter over the Program IR
//! (PROGRAM_SYNTHESIS_PLAN.md §3.2; PROGRAM_SYNTHESIS_PREREG.md §3).
//!
//! Follows the module-per-engine precedent (`shape_decode.rs`,
//! `strokes.rs`): the engine lives here, `term.rs` has a one-line
//! dispatch arm, the output is a Dict with a `field` selector.
//!
//! ## Contract
//!
//! `ProgEval{prog, env, oracles, fuel, field}` →
//! `Dict{result, env_out, steps, halted, trap}`.
//!
//! - **Pure.** Dict in → Dict out. NO substrate mutation, no I/O. The
//!   graph is read only for the subgraph-rooted `prog` form
//!   (`reflect::term_from_subgraph`, the EvalSubgraph convention).
//! - **Fueled.** `fuel` bounds the count of executed statements plus
//!   loop/comprehension ITERATIONS (`ProgSeq` containers are free; an
//!   `If` header, an assignment, a bare-expression statement each cost
//!   1; each For/While/comprehension iteration costs 1). Exhaustion →
//!   `halted:false, trap:"fuel", steps == fuel`, honest PARTIAL
//!   `env_out`, NEVER a value. `fuel <= 0` selects the documented
//!   default (10_000). Fuel is the in-frame integer axis — there is no
//!   wall clock anywhere in this module.
//! - **Trap model.** A trap is a `String` reason carried on the
//!   interpreter's control flow (`Flow::Trap`): `raise:<s>` (ProgRaise),
//!   `extern:<name>` (undeclared extern), `extern:unimplemented:<name>`
//!   (declared but outside the native oracle set), `name:<n>` (unbound
//!   variable), `attr:<a>` / `key:<k>` / `index:oob` (miss),
//!   `unpack:arity`, `is_op:unsupported`, `iter:<kind>`,
//!   `lvalue:unsupported`, `loopctl:outside_loop`,
//!   `expr:unsupported_over_prog`, `prog:invalid`, `param:<name>`;
//!   Q1 adds `slice:zero_step` / `slice:type:<kind>` (ProgSlice),
//!   `extern:<name>:arity` / `extern:<name>:argtype` / `extern:<name>:
//!   type:<kind>` (type-mismatch honesty per new oracle family),
//!   `extern:<name>:domain` (e.g. `math.sqrt` of a negative), and
//!   `extern:<name>:zero` (divmod by zero).
//!   `ProgTryOr` catches ANY trap raised in its body. It NEVER catches
//!   fuel exhaustion (`Flow::Fuel` is a distinct variant, not a trap —
//!   a catchable fuel-out would let a program forge `halted`). An
//!   uncaught trap → `halted:false`, `trap:<reason>`, partial env_out.
//! - **Env bridge.** Program variables live in this interpreter's own
//!   ordered binding list. Expressions inside statements are ordinary
//!   DSL Terms: a Prog-free subtree is delegated WHOLE to the standard
//!   `evaluate()` with the program bindings pushed as Var bindings on
//!   top of the caller's env (outer rule-match vars stay readable;
//!   program vars shadow). A subtree that MIXES Prog expression nodes
//!   under DSL operators is handled for a documented compositional
//!   core (arithmetic / comparison / logic / collection constructors)
//!   by rebuilding the operator over `Lit` children in a scratch arena
//!   and delegating — so DSL semantics govern arithmetic everywhere
//!   (including its documented divergences from CPython: `Div`-by-zero
//!   → 0.0, `Mod`-by-zero → 0, no ZeroDivisionError). And/Or/Not/
//!   IfThenElse are interpreted natively so short-circuit holds over
//!   Prog subexpressions (a subscript in the unreached branch must not
//!   trap). Any OTHER DSL operator over a Prog subexpression traps
//!   `expr:unsupported_over_prog` honestly.
//! - **Value realisation.** list/tuple displays both realise as
//!   `Value::Tuple` (the IR keeps `kind` for rendering); records
//!   (`obj.attr`) are Dict values; strings are `Str`/`Surface(Text)`
//!   interchangeably (`str_like_owned`). Assignment through
//!   subscript/attr lvalues REBUILDS the immutable value along a
//!   Var-rooted path — no aliasing (documented divergence from CPython
//!   reference semantics; fixtures avoid aliasing).
//! - **CallExtern.** Evaluated ONLY against the declared `oracles`
//!   Dict (extern name → any declaration value). The native oracle
//!   set (P1 + Q1 widening, PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md): the
//!   P1 core (len/abs/min/max/range/sum/str/int/float/bool/sorted);
//!   `math_native` (round/pow/divmod/ord/chr/math.sqrt/math.floor/
//!   math.ceil/math.pow/math.trunc); `container_ctor`
//!   (list/tuple/set/frozenset/dict); `general_builtins`
//!   (all/any/isinstance/enumerate/zip/reversed — map/next/iter are
//!   REFUSED, not approximated: they need a first-class callable or a
//!   lazy iterator, neither of which exists in this value model);
//!   `string_methods` and read-only `dict_methods` as RECV-form calls
//!   (`call_recv_oracle`) — upper/lower/capitalize/strip/lstrip/
//!   rstrip/split/join/replace/startswith/endswith/find/count/
//!   isdigit/isalpha/isupper/islower on strings, items/keys/values/get
//!   on dicts. Mutating members (`list.append`, `dict.setdefault`, …)
//!   are NOT landed — `ProgCallExtern` is a pure expression call with
//!   no lvalue write-back path (a residual, not a silent gap).
//!   `range` materialises eagerly; a range longer than 1_000_000 traps
//!   `extern:range:too_large` (an HONEST trap, not a silent cap). NO
//!   shelling out, ever — an extern's semantics is a knowledge gap
//!   that heals via the teacher chain, not a reason to run code.

use std::sync::Arc;

use smallvec::SmallVec;

use crate::sym::{Interner, Sym};
use crate::term::{children, evaluate, str_like_owned, Env, EvalCtx, TermArena, TermIdx, TermNode};
use crate::value::{
    cmp_value, make_rational, rational_add, rational_div, rational_parts, rational_pow_int,
    SurfaceKind, Value,
};

const DEFAULT_FUEL: i64 = 10_000;
const RANGE_CAP: i64 = 1_000_000;

fn surf(s: &str) -> Value {
    Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes()))
}

fn surf_string(s: String) -> Value {
    Value::Surface(
        SurfaceKind::Text,
        Arc::from(s.into_bytes().into_boxed_slice()),
    )
}

/// Non-value control flow escaping a statement/expression.
enum Flow {
    Break,
    Continue,
    Return(Value),
    Trap(String),
    Fuel,
}

type StepResult = Result<(), Flow>;
type ExprResult = Result<Value, Flow>;

struct Machine {
    /// Ordered program bindings (insertion order preserved for honesty
    /// of partial env_out; rebinding updates in place).
    vars: Vec<(Sym, Value)>,
    /// Incoming env pairs whose keys had no interned Sym — unreferencable
    /// by any parsed IR, passed through to env_out untouched.
    passthrough: Vec<(Value, Value)>,
    /// The declared extern oracles (Dict) or None.
    oracles: Value,
    steps: i64,
    fuel: i64,
}

impl Machine {
    fn charge(&mut self) -> StepResult {
        if self.steps >= self.fuel {
            return Err(Flow::Fuel);
        }
        self.steps += 1;
        Ok(())
    }

    fn get_var(&self, name: Sym) -> Option<&Value> {
        self.vars
            .iter()
            .rev()
            .find(|(k, _)| *k == name)
            .map(|(_, v)| v)
    }

    fn set_var(&mut self, name: Sym, value: Value) {
        if let Some(slot) = self.vars.iter_mut().find(|(k, _)| *k == name) {
            slot.1 = value;
        } else {
            self.vars.push((name, value));
        }
    }
}

fn is_prog_stmt(node: &TermNode) -> bool {
    matches!(
        node,
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
    )
}

fn is_prog_expr(node: &TermNode) -> bool {
    matches!(
        node,
        TermNode::ProgCallExtern { .. }
            | TermNode::ProgAttrGet { .. }
            | TermNode::ProgSubscript { .. }
            | TermNode::ProgSlice { .. }
            | TermNode::ProgContainerLit { .. }
            | TermNode::ProgComprehensionList { .. }
            | TermNode::ProgComprehensionGen { .. }
            | TermNode::ProgIsOp { .. }
            | TermNode::ProgFString { .. }
    )
}

fn is_prog(node: &TermNode) -> bool {
    is_prog_stmt(node) || is_prog_expr(node)
}

/// Does the subtree rooted at `idx` contain ANY Prog* node (itself
/// included)? Drives the delegate-whole vs rebuild-per-child decision.
fn contains_prog(arena: &TermArena, idx: TermIdx) -> bool {
    let node = arena.get(idx);
    if is_prog(node) || matches!(node, TermNode::ProgEval { .. }) {
        return true;
    }
    children(node).into_iter().any(|c| contains_prog(arena, c))
}

/// The documented compositional core (PROGRAM_SYNTHESIS_ARC2_Q1_NOTES.md
/// §"mixed tree"): arithmetic / compare / set-algebra / collection-
/// constructor Terms whose operands `eval_expr` evaluates itself (via
/// `eval_expr` recursion, so a Prog-expression operand — e.g. `a[i]` —
/// is handled correctly) before rebuilding a single-level node over
/// `Lit` children and delegating to the standard `evaluate()`. Kept as
/// its own predicate (rather than inline in `eval_expr`'s match) so it
/// can be checked UNCONDITIONALLY — see the call site's doc comment for
/// why that widening (arc-5 rational rung) is safe.
fn is_compositional_op(node: &TermNode) -> bool {
    matches!(
        node,
        TermNode::Plus { .. }
            | TermNode::Times { .. }
            | TermNode::Min { .. }
            | TermNode::Max { .. }
            | TermNode::Vec_ { .. }
            | TermNode::StringConcat { .. }
            | TermNode::Minus { .. }
            | TermNode::Div { .. }
            | TermNode::Mod { .. }
            | TermNode::Pow { .. }
            | TermNode::IDiv { .. }
            | TermNode::IRem { .. }
            | TermNode::BitAnd { .. }
            | TermNode::BitOr { .. }
            | TermNode::BitXor { .. }
            | TermNode::Shl { .. }
            | TermNode::Lshr { .. }
            | TermNode::Ashr { .. }
            | TermNode::Eq { .. }
            | TermNode::Lt { .. }
            | TermNode::Lte { .. }
            | TermNode::Gt { .. }
            | TermNode::Gte { .. }
            | TermNode::In { .. }
            | TermNode::Union { .. }
            | TermNode::Intersect { .. }
            | TermNode::Difference { .. }
            | TermNode::IndexAt { .. }
            | TermNode::Append { .. }
            | TermNode::Neg { .. }
            | TermNode::Abs { .. }
            | TermNode::Count { .. }
            | TermNode::Last { .. }
    )
}

/// Python `str()` spelling for the scalar Values the FString/`str`
/// oracle paths meet. Containers render list-style (`[1, 2]`) — the
/// documented choice for the collapsed list/tuple realisation.
/// CPython's `str(float)` spelling — factored out so the Rational arm
/// below (the boundary: a Rational renders as the SAME string a real
/// Python `float` produced by `/` would) shares it exactly.
fn py_float_str(f: f64) -> String {
    if f.is_nan() {
        "nan".to_string()
    } else if f.is_infinite() {
        if f > 0.0 {
            "inf".to_string()
        } else {
            "-inf".to_string()
        }
    } else if f == f.trunc() && f.abs() < 1e16 {
        format!("{:.1}", f)
    } else {
        format!("{}", f)
    }
}

/// Rung 1 (`PROGRAM_SYNTHESIS_STRUCTURAL_CEILING_REASSESSMENT_PREREG.md`):
/// `pub(crate)` so `term.rs`'s new `Str`/`Round`/`Slice` Term evaluators
/// can reuse these EXACT helpers rather than re-deriving a second, driftable
/// copy of Python's `str()`/`round()`/slice-index semantics. Visibility-only
/// change; no behaviour here is touched.
pub(crate) fn py_str(v: &Value, interner: &Interner) -> String {
    match v {
        Value::None => "None".to_string(),
        Value::Bool(b) => if *b { "True" } else { "False" }.to_string(),
        Value::Int(n) => n.to_string(),
        Value::Float(f) => py_float_str(*f),
        // THE boundary: `str()`/f-string rendering of an exact rational
        // spells it the way CPython would spell the `/` result it
        // stands in for (a real float) — never Rust's `Rational(n, d)`
        // Debug form the generic `other` fallback below would produce.
        Value::Rational(n, d) => py_float_str(*n as f64 / *d as f64),
        Value::Str(s) => interner.resolve(*s).to_string(),
        Value::Surface(SurfaceKind::Text, b) => String::from_utf8_lossy(b).into_owned(),
        // CPython spelling, now that the two are distinguishable: a list
        // renders `[a, b]`, a tuple `(a, b)` (and `(a,)` for a 1-tuple).
        // Before this change EVERY sequence rendered with the list
        // spelling, which was right for lists and wrong for tuples.
        Value::List(items) => {
            let inner: Vec<String> = items.iter().map(|i| py_repr_ish(i, interner)).collect();
            format!("[{}]", inner.join(", "))
        }
        Value::Tuple(items) => {
            let inner: Vec<String> = items.iter().map(|i| py_repr_ish(i, interner)).collect();
            if inner.len() == 1 {
                format!("({},)", inner[0])
            } else {
                format!("({})", inner.join(", "))
            }
        }
        Value::Dict(pairs) => {
            let inner: Vec<String> = pairs
                .iter()
                .map(|(k, v)| format!("{}: {}", py_repr_ish(k, interner), py_repr_ish(v, interner)))
                .collect();
            format!("{{{}}}", inner.join(", "))
        }
        other => format!("{:?}", other),
    }
}

/// repr-ish spelling for container ELEMENTS (strings quoted).
fn py_repr_ish(v: &Value, interner: &Interner) -> String {
    match v {
        Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
            format!("'{}'", py_str(v, interner))
        }
        _ => py_str(v, interner),
    }
}

/// String-like equality between a Dict key Value and a &str.
fn key_matches(k: &Value, s: &str, interner: &Interner) -> bool {
    match k {
        Value::Str(sym) => interner.resolve(*sym) == s,
        Value::Surface(SurfaceKind::Text, b) => b.as_ref() == s.as_bytes(),
        _ => false,
    }
}

fn dict_lookup_str<'v>(
    pairs: &'v [(Value, Value)],
    key_text: &str,
    interner: &Interner,
) -> Option<&'v Value> {
    pairs
        .iter()
        .find(|(k, _)| key_matches(k, key_text, interner))
        .map(|(_, v)| v)
}

/// Realise an iterable Value into a concrete item vector (For /
/// comprehensions / min/max/sum/sorted oracles).
fn iter_items(v: &Value, interner: &Interner) -> Result<Vec<Value>, Flow> {
    match v {
        Value::Tuple(items) | Value::List(items) => Ok(items.iter().cloned().collect()),
        Value::Set(items) | Value::FrozenSet(items) => Ok(items.iter().cloned().collect()),
        Value::Dict(pairs) => Ok(pairs.iter().map(|(k, _)| k.clone()).collect()),
        Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
            let s = str_like_owned(v, interner).unwrap_or_default();
            Ok(s.chars().map(|c| surf_string(c.to_string())).collect())
        }
        other => Err(Flow::Trap(format!("iter:{}", value_kind(other)))),
    }
}

fn value_kind(v: &Value) -> &'static str {
    match v {
        Value::None => "none",
        Value::Bool(_) => "bool",
        Value::Int(_) => "int",
        Value::Float(_) => "float",
        // Distinct debug label from "float" (this is an internal, exact
        // representation) — the Python-FACING type identity (isinstance,
        // str()/float() boundary rendering) is handled separately, at
        // each of those specific call sites, not here.
        Value::Rational(_, _) => "rational",
        Value::Str(_) => "str",
        Value::Node(_) => "node",
        Value::Tuple(_) => "tuple",
        Value::List(_) => "list",
        Value::Set(_) => "set",
        Value::FrozenSet(_) => "frozenset",
        Value::Dict(_) => "dict",
        Value::Surface(SurfaceKind::Text, _) => "str",
        Value::Surface(SurfaceKind::Bytes, _) => "bytes",
    }
}

// ---------------------------------------------------------------------------
// Q1 value-domain helpers (slicing, floor division, string methods).
// ---------------------------------------------------------------------------

/// CPython's `PySlice_AdjustIndices` algorithm: realise `[start:stop:step]`
/// over a sequence of length `len` into the concrete list of indices to
/// read, honestly (never OOB — Python slicing clamps, it never raises).
pub(crate) fn slice_indices(
    len: i64,
    start: Option<i64>,
    stop: Option<i64>,
    step: i64,
) -> Vec<i64> {
    let (lower, upper) = if step > 0 { (0, len) } else { (-1, len - 1) };
    let clamp = |v: i64| v.clamp(lower, upper);
    let norm = |v: Option<i64>, default: i64| -> i64 {
        match v {
            None => default,
            Some(mut x) => {
                if x < 0 {
                    x += len;
                }
                clamp(x)
            }
        }
    };
    let default_start = if step < 0 { upper } else { lower };
    let default_stop = if step < 0 { lower } else { upper };
    let s = norm(start, default_start);
    let e = norm(stop, default_stop);
    let mut out = Vec::new();
    if step > 0 {
        let mut i = s;
        while i < e {
            out.push(i);
            i += step;
        }
    } else {
        let mut i = s;
        while i > e {
            out.push(i);
            i += step;
        }
    }
    out
}

/// Python floor division on integers: `//` rounds toward negative
/// infinity, NOT toward zero (Rust's `/` truncates toward zero) —
/// this is `divmod`'s OWN semantics, computed locally so the global
/// DSL `IDiv`/`IRem` Terms (used pervasively outside program synthesis,
/// truncating by design/registered divergence) are never touched.
fn floor_div_i64(a: i64, b: i64) -> i64 {
    let q = a.wrapping_div(b);
    let r = a.wrapping_rem(b);
    if r != 0 && (r < 0) != (b < 0) {
        q - 1
    } else {
        q
    }
}

fn floor_mod_i64(a: i64, b: i64) -> i64 {
    let r = a.wrapping_rem(b);
    if r != 0 && (r < 0) != (b < 0) {
        r + b
    } else {
        r
    }
}

fn floor_div_f64(a: f64, b: f64) -> f64 {
    (a / b).floor()
}

/// Python's `round()`: round-half-to-EVEN (banker's rounding), not
/// Rust's `f64::round` (half-away-from-zero). Approximate at f64
/// precision — exact for the small integers/decimals MBPP-scale specs
/// exercise; documented, not claimed IEEE-754-exhaustive.
fn round_half_even(x: f64) -> f64 {
    let floor = x.floor();
    let diff = x - floor;
    if diff < 0.5 {
        floor
    } else if diff > 0.5 {
        floor + 1.0
    } else if (floor as i64).rem_euclid(2) == 0 {
        floor
    } else {
        floor + 1.0
    }
}

pub(crate) fn round_half_even_digits(x: f64, ndigits: i32) -> f64 {
    let mult = 10f64.powi(ndigits);
    round_half_even(x * mult) / mult
}

/// Python's default `str.strip()` whitespace set (ASCII subset — a
/// documented, narrower-than-CPython's-full-Unicode scope).
fn py_is_space(c: char) -> bool {
    matches!(c, ' ' | '\t' | '\n' | '\r' | '\x0b' | '\x0c')
}

fn strip_chars(s: &str, chars: Option<&str>, left: bool, right: bool) -> String {
    let is_strip = |c: char| match chars {
        Some(set) => set.contains(c),
        None => py_is_space(c),
    };
    let mut start = 0usize;
    let mut end = s.chars().count();
    let cs: Vec<char> = s.chars().collect();
    if left {
        while start < end && is_strip(cs[start]) {
            start += 1;
        }
    }
    if right {
        while end > start && is_strip(cs[end - 1]) {
            end -= 1;
        }
    }
    cs[start..end].iter().collect()
}

/// Byte index → char index (both haystack scans are over the SAME
/// string, so this is exact — `find`/`count` report CHAR positions,
/// consistent with `ProgSubscript`'s char-based indexing).
fn byte_to_char_idx(s: &str, byte_idx: usize) -> i64 {
    s[..byte_idx].chars().count() as i64
}

// ---------------------------------------------------------------------------
// Statement execution
// ---------------------------------------------------------------------------

fn exec_stmt(
    m: &mut Machine,
    arena: &TermArena,
    idx: TermIdx,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> StepResult {
    match arena.get(idx) {
        TermNode::ProgSeq { stmts } => {
            // The container itself is free; each inner statement charges.
            let stmts = stmts.clone();
            for s in stmts {
                exec_stmt(m, arena, s, env, ctx)?;
            }
            Ok(())
        }
        TermNode::ProgAssignVar { name, value } => {
            m.charge()?;
            let (name, value) = (*name, *value);
            let v = eval_expr(m, arena, value, env, ctx)?;
            m.set_var(name, v);
            Ok(())
        }
        TermNode::ProgAugAssign { name, op, value } => {
            m.charge()?;
            let (name, op, value) = (*name, *op, *value);
            let cur = match m.get_var(name) {
                Some(v) => v.clone(),
                None => return Err(Flow::Trap(format!("name:{}", ctx.interner.resolve(name)))),
            };
            let rhs = eval_expr(m, arena, value, env, ctx)?;
            let combined = aug_combine(&cur, ctx.interner.resolve(op), &rhs, env, ctx)?;
            m.set_var(name, combined);
            Ok(())
        }
        TermNode::ProgTupleUnpack { targets, value } => {
            m.charge()?;
            let (targets, value) = (targets.clone(), *value);
            let v = eval_expr(m, arena, value, env, ctx)?;
            let (Value::Tuple(items) | Value::List(items)) = &v else {
                return Err(Flow::Trap("unpack:arity".to_string()));
            };
            if items.len() != targets.len() {
                return Err(Flow::Trap("unpack:arity".to_string()));
            }
            for (t, item) in targets.iter().zip(items.iter()) {
                m.set_var(*t, item.clone());
            }
            Ok(())
        }
        TermNode::ProgIfStmt { cond, then, orelse } => {
            m.charge()?;
            let (cond, then, orelse) = (*cond, *then, *orelse);
            let c = eval_expr(m, arena, cond, env, ctx)?;
            if c.truthy() {
                exec_stmt(m, arena, then, env, ctx)
            } else if let Some(o) = orelse {
                exec_stmt(m, arena, o, env, ctx)
            } else {
                Ok(())
            }
        }
        TermNode::ProgForEach {
            var,
            iter,
            body,
            orelse,
        } => {
            m.charge()?;
            let (var, iter, body, orelse) = (*var, *iter, *body, *orelse);
            let it = eval_expr(m, arena, iter, env, ctx)?;
            let items = iter_items(&it, ctx.interner)?;
            let mut broke = false;
            for item in items {
                m.charge()?;
                m.set_var(var, item);
                match exec_stmt(m, arena, body, env, ctx) {
                    Ok(()) => {}
                    Err(Flow::Break) => {
                        broke = true;
                        break;
                    }
                    Err(Flow::Continue) => continue,
                    Err(other) => return Err(other),
                }
            }
            if !broke {
                if let Some(o) = orelse {
                    exec_stmt(m, arena, o, env, ctx)?;
                }
            }
            Ok(())
        }
        TermNode::ProgWhile { cond, body, orelse } => {
            let (cond, body, orelse) = (*cond, *body, *orelse);
            let mut broke = false;
            loop {
                m.charge()?; // one charge per iteration (the cond check)
                let c = eval_expr(m, arena, cond, env, ctx)?;
                if !c.truthy() {
                    break;
                }
                match exec_stmt(m, arena, body, env, ctx) {
                    Ok(()) => {}
                    Err(Flow::Break) => {
                        broke = true;
                        break;
                    }
                    Err(Flow::Continue) => continue,
                    Err(other) => return Err(other),
                }
            }
            if !broke {
                if let Some(o) = orelse {
                    exec_stmt(m, arena, o, env, ctx)?;
                }
            }
            Ok(())
        }
        TermNode::ProgLoopCtl { kind } => {
            m.charge()?;
            let k = ctx.interner.resolve(*kind);
            match k {
                "break" => Err(Flow::Break),
                "continue" => Err(Flow::Continue),
                other => Err(Flow::Trap(format!("loopctl:{}", other))),
            }
        }
        TermNode::ProgReturn { value } => {
            m.charge()?;
            let value = *value;
            let v = match value {
                Some(v) => eval_expr(m, arena, v, env, ctx)?,
                None => Value::None,
            };
            Err(Flow::Return(v))
        }
        TermNode::ProgTryOr {
            body,
            exc_var,
            handler,
        } => {
            m.charge()?;
            let (body, exc_var, handler) = (*body, *exc_var, *handler);
            match exec_stmt(m, arena, body, env, ctx) {
                Ok(()) => Ok(()),
                Err(Flow::Trap(t)) => {
                    if exc_var != Sym::default() {
                        m.set_var(exc_var, surf_string(t));
                    }
                    if let Some(h) = handler {
                        exec_stmt(m, arena, h, env, ctx)?;
                    }
                    Ok(())
                }
                // Fuel is NOT a trap; Break/Continue/Return pass through
                // a try the way Python passes them through.
                Err(other) => Err(other),
            }
        }
        TermNode::ProgRaise { exc } => {
            m.charge()?;
            let exc = *exc;
            match exc {
                Some(e) => {
                    let v = eval_expr(m, arena, e, env, ctx)?;
                    Err(Flow::Trap(format!("raise:{}", py_str(&v, ctx.interner))))
                }
                None => Err(Flow::Trap("raise".to_string())),
            }
        }
        TermNode::ProgImportStmt { .. } => {
            // Extern surface only — a documented no-op. Any USE of an
            // unbound imported name traps honestly at the use site.
            m.charge()?;
            Ok(())
        }
        TermNode::ProgSubscriptSet { obj, index, value } => {
            m.charge()?;
            let (obj, index, value) = (*obj, *index, *value);
            let val_v = eval_expr(m, arena, value, env, ctx)?;
            let idx_v = eval_expr(m, arena, index, env, ctx)?;
            let container = eval_expr(m, arena, obj, env, ctx)?;
            let updated = container_with(&container, &idx_v, val_v, ctx.interner)?;
            set_lvalue(m, arena, obj, updated, env, ctx)
        }
        TermNode::ProgAttrSet { obj, attr, value } => {
            m.charge()?;
            let (obj, attr, value) = (*obj, *attr, *value);
            let val_v = eval_expr(m, arena, value, env, ctx)?;
            let record = eval_expr(m, arena, obj, env, ctx)?;
            let updated = record_with(&record, attr, val_v, ctx.interner)?;
            set_lvalue(m, arena, obj, updated, env, ctx)
        }
        TermNode::ProgDefFnParam { name, default } => {
            m.charge()?;
            let (name, default) = (*name, *default);
            if m.get_var(name).is_some() {
                return Ok(());
            }
            match default {
                Some(d) => {
                    let v = eval_expr(m, arena, d, env, ctx)?;
                    m.set_var(name, v);
                    Ok(())
                }
                None => Err(Flow::Trap(format!("param:{}", ctx.interner.resolve(name)))),
            }
        }
        // A bare expression in statement position: evaluate, discard.
        _ => {
            m.charge()?;
            let _ = eval_expr(m, arena, idx, env, ctx)?;
            Ok(())
        }
    }
}

/// AugAssign combining. `add` handles Str/Surface concat and Tuple
/// concat natively; everything numeric delegates to the matching DSL
/// arithmetic Term over Lit children (so DSL semantics govern — same
/// as ordinary expressions).
fn aug_combine(cur: &Value, op: &str, rhs: &Value, env: &mut Env, ctx: &mut EvalCtx) -> ExprResult {
    if op == "add" {
        match (cur, rhs) {
            (
                Value::Str(_) | Value::Surface(SurfaceKind::Text, _),
                Value::Str(_) | Value::Surface(SurfaceKind::Text, _),
            ) => {
                let a = str_like_owned(cur, ctx.interner).unwrap_or_default();
                let b = str_like_owned(rhs, ctx.interner).unwrap_or_default();
                return Ok(surf_string(a + &b));
            }
            (Value::Tuple(a) | Value::List(a), Value::Tuple(b) | Value::List(b)) => {
                let mut items: SmallVec<[Value; 4]> = a.iter().cloned().collect();
                items.extend(b.iter().cloned());
                // Kind of the LEFT operand. CPython raises on `list +
                // tuple`; keeping the left kind is never MORE restrictive
                // than the pre-change behaviour, which produced a tuple
                // for every combination.
                let out = Arc::new(items);
                return Ok(if matches!(cur, Value::List(_)) {
                    Value::List(out)
                } else {
                    Value::Tuple(out)
                });
            }
            _ => {}
        }
    }
    let mut scratch = TermArena::new();
    let a = scratch.add(TermNode::Lit { value: cur.clone() });
    let b = scratch.add(TermNode::Lit { value: rhs.clone() });
    let node = match op {
        "add" => TermNode::Plus { items: vec![a, b] },
        "sub" => TermNode::Minus { a, b },
        "mult" => TermNode::Times { items: vec![a, b] },
        "div" => TermNode::Div { a, b },
        "floordiv" => TermNode::IDiv { a, b },
        "mod" => TermNode::Mod { a, b },
        "pow" => TermNode::Pow { a, b },
        "lshift" => TermNode::Shl { a, b },
        "rshift" => TermNode::Ashr { a, b },
        "bitand" => TermNode::BitAnd { a, b },
        "bitor" => TermNode::BitOr { a, b },
        "bitxor" => TermNode::BitXor { a, b },
        other => return Err(Flow::Trap(format!("augassign:{}", other))),
    };
    let root = scratch.add(node);
    Ok(evaluate(&scratch, root, env, ctx))
}

/// Rebuild `container` with `container[key] = value` applied.
fn container_with(
    container: &Value,
    key: &Value,
    value: Value,
    interner: &Interner,
) -> Result<Value, Flow> {
    match container {
        Value::Tuple(items) | Value::List(items) => {
            let Value::Int(i) = key else {
                return Err(Flow::Trap("index:type".to_string()));
            };
            let n = items.len() as i64;
            let real = if *i < 0 { i + n } else { *i };
            if real < 0 || real >= n {
                return Err(Flow::Trap("index:oob".to_string()));
            }
            let mut out: SmallVec<[Value; 4]> = items.iter().cloned().collect();
            out[real as usize] = value;
            let out = Arc::new(out);
            Ok(if matches!(container, Value::List(_)) {
                Value::List(out)
            } else {
                Value::Tuple(out)
            })
        }
        Value::Dict(pairs) => {
            let mut out: Vec<(Value, Value)> = pairs.to_vec();
            let mut replaced = false;
            for slot in out.iter_mut() {
                let hit = cmp_value(&slot.0, key) == std::cmp::Ordering::Equal
                    || match (
                        str_like_owned(&slot.0, interner),
                        str_like_owned(key, interner),
                    ) {
                        (Some(a), Some(b)) => a == b,
                        _ => false,
                    };
                if hit {
                    slot.1 = value.clone();
                    replaced = true;
                    break;
                }
            }
            if !replaced {
                out.push((key.clone(), value));
                out.sort_by(|x, y| cmp_value(&x.0, &y.0));
            }
            Ok(Value::Dict(Arc::from(out)))
        }
        other => Err(Flow::Trap(format!("subscript_set:{}", value_kind(other)))),
    }
}

/// Rebuild `record` (a Dict) with field `attr` set.
fn record_with(
    record: &Value,
    attr: Sym,
    value: Value,
    interner: &Interner,
) -> Result<Value, Flow> {
    match record {
        Value::Dict(_) => container_with(record, &Value::Str(attr), value, interner),
        other => Err(Flow::Trap(format!("attr_set:{}", value_kind(other)))),
    }
}

/// Write `new_value` back through a Var-rooted lvalue path
/// (Var / ProgSubscript / ProgAttrGet chains).
fn set_lvalue(
    m: &mut Machine,
    arena: &TermArena,
    target: TermIdx,
    new_value: Value,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> StepResult {
    match arena.get(target) {
        TermNode::Var { name } => {
            m.set_var(*name, new_value);
            Ok(())
        }
        TermNode::ProgSubscript { obj, index } => {
            let (obj, index) = (*obj, *index);
            let idx_v = eval_expr(m, arena, index, env, ctx)?;
            let container = eval_expr(m, arena, obj, env, ctx)?;
            let updated = container_with(&container, &idx_v, new_value, ctx.interner)?;
            set_lvalue(m, arena, obj, updated, env, ctx)
        }
        TermNode::ProgAttrGet { obj, attr } => {
            let (obj, attr) = (*obj, *attr);
            let record = eval_expr(m, arena, obj, env, ctx)?;
            let updated = record_with(&record, attr, new_value, ctx.interner)?;
            set_lvalue(m, arena, obj, updated, env, ctx)
        }
        _ => Err(Flow::Trap("lvalue:unsupported".to_string())),
    }
}

// ---------------------------------------------------------------------------
// Expression evaluation
// ---------------------------------------------------------------------------

fn eval_expr(
    m: &mut Machine,
    arena: &TermArena,
    idx: TermIdx,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> ExprResult {
    match arena.get(idx) {
        TermNode::Lit { value } => Ok(value.clone()),
        TermNode::Var { name } => {
            if let Some(v) = m.get_var(*name) {
                return Ok(v.clone());
            }
            // Read-through to the caller's env (rule-match vars).
            if let Some(v) = crate::term::env_get(env, *name) {
                return Ok(v.clone());
            }
            Err(Flow::Trap(format!("name:{}", ctx.interner.resolve(*name))))
        }

        // --- native short-circuit logic (Prog-safe) ---
        TermNode::And { items } => {
            let items = items.clone();
            for c in items {
                if !eval_expr(m, arena, c, env, ctx)?.truthy() {
                    return Ok(Value::Bool(false));
                }
            }
            Ok(Value::Bool(true))
        }
        TermNode::Or { items } => {
            let items = items.clone();
            for c in items {
                if eval_expr(m, arena, c, env, ctx)?.truthy() {
                    return Ok(Value::Bool(true));
                }
            }
            Ok(Value::Bool(false))
        }
        TermNode::Not { arg } => {
            let arg = *arg;
            Ok(Value::Bool(!eval_expr(m, arena, arg, env, ctx)?.truthy()))
        }
        TermNode::IfThenElse { cond, then, other } => {
            let (cond, then, other) = (*cond, *then, *other);
            if eval_expr(m, arena, cond, env, ctx)?.truthy() {
                eval_expr(m, arena, then, env, ctx)
            } else {
                eval_expr(m, arena, other, env, ctx)
            }
        }

        // --- Program-IR expressions ---
        TermNode::ProgCallExtern { name, recv, args } => {
            let (name, recv, args) = (*name, *recv, args.clone());
            let name_str = ctx.interner.resolve(name).to_string();
            // Declared?
            let declared = match &m.oracles {
                Value::Dict(pairs) => dict_lookup_str(pairs, &name_str, ctx.interner).is_some(),
                _ => false,
            };
            if !declared {
                return Err(Flow::Trap(format!("extern:{}", name_str)));
            }
            let recv_v = match recv {
                Some(r) => Some(eval_expr(m, arena, r, env, ctx)?),
                None => None,
            };
            let mut arg_vs = Vec::with_capacity(args.len());
            for a in args {
                arg_vs.push(eval_expr(m, arena, a, env, ctx)?);
            }
            call_native_oracle(&name_str, recv_v.as_ref(), &arg_vs, ctx.interner)
        }
        TermNode::ProgAttrGet { obj, attr } => {
            let (obj, attr) = (*obj, *attr);
            let record = eval_expr(m, arena, obj, env, ctx)?;
            let attr_str = ctx.interner.resolve(attr).to_string();
            match &record {
                Value::Dict(pairs) => match dict_lookup_str(pairs, &attr_str, ctx.interner) {
                    Some(v) => Ok(v.clone()),
                    None => Err(Flow::Trap(format!("attr:{}", attr_str))),
                },
                _ => Err(Flow::Trap(format!("attr:{}", attr_str))),
            }
        }
        TermNode::ProgSubscript { obj, index } => {
            let (obj, index) = (*obj, *index);
            let container = eval_expr(m, arena, obj, env, ctx)?;
            let key = eval_expr(m, arena, index, env, ctx)?;
            match &container {
                Value::Tuple(items) | Value::List(items) => {
                    let Value::Int(i) = key else {
                        return Err(Flow::Trap("index:type".to_string()));
                    };
                    let n = items.len() as i64;
                    let real = if i < 0 { i + n } else { i };
                    if real < 0 || real >= n {
                        return Err(Flow::Trap("index:oob".to_string()));
                    }
                    Ok(items[real as usize].clone())
                }
                Value::Dict(pairs) => {
                    if let Some(v) = pairs
                        .iter()
                        .find(|(k, _)| {
                            cmp_value(k, &key) == std::cmp::Ordering::Equal
                                || match (
                                    str_like_owned(k, ctx.interner),
                                    str_like_owned(&key, ctx.interner),
                                ) {
                                    (Some(a), Some(b)) => a == b,
                                    _ => false,
                                }
                        })
                        .map(|(_, v)| v)
                    {
                        Ok(v.clone())
                    } else {
                        Err(Flow::Trap(format!("key:{}", py_str(&key, ctx.interner))))
                    }
                }
                Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
                    let s = str_like_owned(&container, ctx.interner).unwrap_or_default();
                    let chars: Vec<char> = s.chars().collect();
                    let Value::Int(i) = key else {
                        return Err(Flow::Trap("index:type".to_string()));
                    };
                    let n = chars.len() as i64;
                    let real = if i < 0 { i + n } else { i };
                    if real < 0 || real >= n {
                        return Err(Flow::Trap("index:oob".to_string()));
                    }
                    Ok(surf_string(chars[real as usize].to_string()))
                }
                other => Err(Flow::Trap(format!("subscript:{}", value_kind(other)))),
            }
        }
        TermNode::ProgSlice {
            obj,
            start,
            stop,
            step,
        } => {
            let (obj, start, stop, step) = (*obj, *start, *stop, *step);
            let container = eval_expr(m, arena, obj, env, ctx)?;
            let step_v = match step {
                Some(s) => eval_expr(m, arena, s, env, ctx)?.as_i64(),
                None => 1,
            };
            if step_v == 0 {
                return Err(Flow::Trap("slice:zero_step".to_string()));
            }
            let start_v = match start {
                Some(s) => Some(eval_expr(m, arena, s, env, ctx)?.as_i64()),
                None => None,
            };
            let stop_v = match stop {
                Some(s) => Some(eval_expr(m, arena, s, env, ctx)?.as_i64()),
                None => None,
            };
            match &container {
                Value::Tuple(items) | Value::List(items) => {
                    let n = items.len() as i64;
                    let idxs = slice_indices(n, start_v, stop_v, step_v);
                    let out: SmallVec<[Value; 4]> =
                        idxs.iter().map(|&i| items[i as usize].clone()).collect();
                    // `l[1:]` is a list, `t[1:]` is a tuple — CPython.
                    let out = Arc::new(out);
                    Ok(if matches!(&container, Value::List(_)) {
                        Value::List(out)
                    } else {
                        Value::Tuple(out)
                    })
                }
                Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
                    let s = str_like_owned(&container, ctx.interner).unwrap_or_default();
                    let chars: Vec<char> = s.chars().collect();
                    let n = chars.len() as i64;
                    let idxs = slice_indices(n, start_v, stop_v, step_v);
                    let out: String = idxs.iter().map(|&i| chars[i as usize]).collect();
                    Ok(surf_string(out))
                }
                other => Err(Flow::Trap(format!("slice:type:{}", value_kind(other)))),
            }
        }
        TermNode::ProgContainerLit { kind, items } => {
            let (kind, items) = (*kind, items.clone());
            let kind_str = ctx.interner.resolve(kind).to_string();
            match kind_str.as_str() {
                "dict" => {
                    let n_pairs = items.len() / 2;
                    let mut pairs: Vec<(Value, Value)> = Vec::with_capacity(n_pairs);
                    for i in 0..n_pairs {
                        let k = eval_expr(m, arena, items[2 * i], env, ctx)?;
                        let v = eval_expr(m, arena, items[2 * i + 1], env, ctx)?;
                        pairs.push((k, v));
                    }
                    pairs.sort_by(|x, y| cmp_value(&x.0, &y.0));
                    Ok(Value::Dict(Arc::from(pairs)))
                }
                "set" => {
                    let mut out = Vec::with_capacity(items.len());
                    for it in items {
                        out.push(eval_expr(m, arena, it, env, ctx)?);
                    }
                    Ok(Value::make_set(out))
                }
                // The IR has ALWAYS carried `kind`; it used to be discarded
                // here because `Value` had no list. It is now honoured.
                _ => {
                    let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(items.len());
                    for it in items {
                        out.push(eval_expr(m, arena, it, env, ctx)?);
                    }
                    let out = Arc::new(out);
                    Ok(if kind_str == "tuple" {
                        Value::Tuple(out)
                    } else {
                        Value::List(out)
                    })
                }
            }
        }
        TermNode::ProgComprehensionList {
            var,
            source,
            expr,
            cond,
        }
        | TermNode::ProgComprehensionGen {
            var,
            source,
            expr,
            cond,
        } => {
            let (var, source, expr, cond) = (*var, *source, *expr, *cond);
            let src = eval_expr(m, arena, source, env, ctx)?;
            let items = iter_items(&src, ctx.interner)?;
            let saved = m.get_var(var).cloned();
            let mut out: SmallVec<[Value; 4]> = SmallVec::new();
            for item in items {
                m.charge()?;
                m.set_var(var, item);
                if let Some(c) = cond {
                    if !eval_expr(m, arena, c, env, ctx)?.truthy() {
                        continue;
                    }
                }
                out.push(eval_expr(m, arena, expr, env, ctx)?);
            }
            // Restore the loop var (comprehension scope doesn't leak in
            // Python 3).
            match saved {
                Some(v) => m.set_var(var, v),
                None => m.vars.retain(|(k, _)| *k != var),
            }
            // A list comprehension IS a list in CPython. A GENERATOR
            // expression is not, but is never compared directly by an
            // MBPP assert (it is always consumed by sum/join/any/...), so
            // it takes the same realisation.
            Ok(Value::List(Arc::new(out)))
        }
        TermNode::ProgIsOp { a, b, negated } => {
            let (a, b, negated) = (*a, *b, *negated);
            let av = eval_expr(m, arena, a, env, ctx)?;
            let bv = eval_expr(m, arena, b, env, ctx)?;
            let same = match (&av, &bv) {
                (Value::None, Value::None) => true,
                (Value::None, _) | (_, Value::None) => false,
                (Value::Node(x), Value::Node(y)) => x == y,
                (Value::Bool(x), Value::Bool(y)) => x == y,
                _ => return Err(Flow::Trap("is_op:unsupported".to_string())),
            };
            Ok(Value::Bool(same != negated))
        }
        TermNode::ProgFString { parts } => {
            let parts = parts.clone();
            let mut out = String::new();
            for p in parts {
                let v = eval_expr(m, arena, p, env, ctx)?;
                out.push_str(&py_str(&v, ctx.interner));
            }
            Ok(surf_string(out))
        }

        // Statement nodes have no value in expression position.
        n if is_prog_stmt(n) => Err(Flow::Trap("expr:statement".to_string())),
        TermNode::ProgEval { .. } => Err(Flow::Trap("expr:nested_prog_eval".to_string())),

        // --- ordinary DSL subtree ---
        node => {
            if !is_compositional_op(node) {
                if !contains_prog(arena, idx) {
                    // Prog-free, non-compositional node (Filter/Sum/
                    // Neighbours/...): delegate WHOLE to the standard
                    // evaluator with program bindings pushed (they
                    // shadow outer vars). UNCHANGED from before the
                    // arc-5 rational rung.
                    let saved = env.len();
                    for (k, v) in &m.vars {
                        env.push((*k, v.clone()));
                    }
                    let v = evaluate(arena, idx, env, ctx);
                    env.truncate(saved);
                    return Ok(v);
                }
                return Err(Flow::Trap("expr:unsupported_over_prog".to_string()));
            }
            // Compositional core (arithmetic / compare / set-algebra /
            // collection constructors) — UNCONDITIONAL as of the arc-5
            // rational rung, not gated on `contains_prog` any more.
            // Reaching this per-node walk even for a PLAIN, Prog-free
            // expression (e.g. `1/3 + 1/3 + 1/3`, no Prog* node
            // anywhere) is what lets `Div`/`Pow` below intercept and
            // stay EXACT (PROGRAM_SYNTHESIS_ARC5_RATIONAL.md) — the
            // old `contains_prog`-gated fast path would otherwise
            // delegate such an expression WHOLE, straight to the
            // shared, deliberately-untouched (float-producing) global
            // `Div` Term. Every op OTHER than Div/Pow, and every case
            // of Div/Pow where the exact path doesn't apply (a Float
            // operand present, a zero divisor, a non-integer exponent,
            // or exact overflow at the non-fallible sites), rebuilds
            // Lit children in a scratch arena and delegates to
            // `evaluate()` exactly as the pre-existing "mixed tree"
            // path did — evaluating a single-level node over already-
            // computed Lit children is value-identical to evaluating
            // the whole subtree in one call, so this is a safe
            // structural widening: BYTE-IDENTICAL results for every
            // node this reaches that isn't the new exact case.
            let node = node.clone();

            if let TermNode::Div { a, b } = &node {
                let av = eval_expr(m, arena, *a, env, ctx)?;
                let bv = eval_expr(m, arena, *b, env, ctx)?;
                if let (Some(pa), Some(pb)) = (rational_parts(&av), rational_parts(&bv)) {
                    if pb.0 != 0 {
                        // Committed to the exact path: overflow here is
                        // a genuine trap, never a silent float degrade
                        // (the "documented trap, never silent wrap"
                        // discipline — this differs from term.rs's
                        // shared, non-fallible arithmetic, which has no
                        // trap channel and degrades to float instead).
                        return match rational_div(pa, pb) {
                            Some(v) => Ok(v),
                            None => Err(Flow::Trap("arith:overflow".to_string())),
                        };
                    }
                }
                // Not applicable (a Float operand, or a zero divisor):
                // rebuild + delegate — IDENTICAL to the pre-existing
                // Div-by-zero -> 0.0 / float-division behaviour.
                let mut scratch = TermArena::new();
                let la = scratch.add(TermNode::Lit { value: av });
                let lb = scratch.add(TermNode::Lit { value: bv });
                let root = scratch.add(TermNode::Div { a: la, b: lb });
                return Ok(evaluate(&scratch, root, env, ctx));
            }
            if let TermNode::Pow { a, b } = &node {
                let av = eval_expr(m, arena, *a, env, ctx)?;
                let bv = eval_expr(m, arena, *b, env, ctx)?;
                // Restricted to a GENUINE Rational base — the (Int,Int)
                // combination is untouched here (never reaches this
                // arm's exactness attempt) so term.rs's existing
                // wrapping_pow (Int,Int) fast path, byte-identical,
                // still owns that case via the rebuild-and-delegate
                // fallback below.
                if let (Value::Rational(n, d), Value::Int(y)) = (&av, &bv) {
                    return match rational_pow_int((*n, *d), *y) {
                        Some(v) => Ok(v),
                        None => Err(Flow::Trap("arith:overflow".to_string())),
                    };
                }
                let mut scratch = TermArena::new();
                let la = scratch.add(TermNode::Lit { value: av });
                let lb = scratch.add(TermNode::Lit { value: bv });
                let root = scratch.add(TermNode::Pow { a: la, b: lb });
                return Ok(evaluate(&scratch, root, env, ctx));
            }

            let mut scratch = TermArena::new();
            macro_rules! lit2 {
                ($a:expr, $b:expr) => {{
                    let av = eval_expr(m, arena, $a, env, ctx)?;
                    let bv = eval_expr(m, arena, $b, env, ctx)?;
                    (
                        scratch.add(TermNode::Lit { value: av }),
                        scratch.add(TermNode::Lit { value: bv }),
                    )
                }};
            }
            macro_rules! lit_items {
                ($items:expr) => {{
                    let mut out = Vec::with_capacity($items.len());
                    for c in $items {
                        let v = eval_expr(m, arena, c, env, ctx)?;
                        out.push(scratch.add(TermNode::Lit { value: v }));
                    }
                    out
                }};
            }
            let rebuilt = match node {
                TermNode::Plus { items } => TermNode::Plus {
                    items: lit_items!(items),
                },
                TermNode::Times { items } => TermNode::Times {
                    items: lit_items!(items),
                },
                TermNode::Min { items } => TermNode::Min {
                    items: lit_items!(items),
                },
                TermNode::Max { items } => TermNode::Max {
                    items: lit_items!(items),
                },
                TermNode::Vec_ { items } => TermNode::Vec_ {
                    items: lit_items!(items),
                },
                TermNode::StringConcat { parts } => TermNode::StringConcat {
                    parts: lit_items!(parts),
                },
                TermNode::Minus { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Minus { a, b }
                }
                // Div / Pow are handled ABOVE (exact-rational
                // interception with a rebuild-and-delegate fallback of
                // their own) and always `return` before reaching this
                // match — these two TermNode kinds are structurally
                // unreachable here; no arm needed.
                TermNode::Mod { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Mod { a, b }
                }
                TermNode::IDiv { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::IDiv { a, b }
                }
                TermNode::IRem { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::IRem { a, b }
                }
                TermNode::BitAnd { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::BitAnd { a, b }
                }
                TermNode::BitOr { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::BitOr { a, b }
                }
                TermNode::BitXor { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::BitXor { a, b }
                }
                TermNode::Shl { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Shl { a, b }
                }
                TermNode::Lshr { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Lshr { a, b }
                }
                TermNode::Ashr { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Ashr { a, b }
                }
                TermNode::Eq { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Eq { a, b }
                }
                TermNode::Lt { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Lt { a, b }
                }
                TermNode::Lte { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Lte { a, b }
                }
                TermNode::Gt { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Gt { a, b }
                }
                TermNode::Gte { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Gte { a, b }
                }
                TermNode::In { member, container } => {
                    let (member, container) = lit2!(member, container);
                    TermNode::In { member, container }
                }
                TermNode::Union { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Union { a, b }
                }
                TermNode::Intersect { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Intersect { a, b }
                }
                TermNode::Difference { a, b } => {
                    let (a, b) = lit2!(a, b);
                    TermNode::Difference { a, b }
                }
                TermNode::IndexAt { seq, index } => {
                    let (seq, index) = lit2!(seq, index);
                    TermNode::IndexAt { seq, index }
                }
                TermNode::Append { seq, item } => {
                    let (seq, item) = lit2!(seq, item);
                    TermNode::Append { seq, item }
                }
                TermNode::Neg { arg } => {
                    let v = eval_expr(m, arena, arg, env, ctx)?;
                    TermNode::Neg {
                        arg: scratch.add(TermNode::Lit { value: v }),
                    }
                }
                TermNode::Abs { arg } => {
                    let v = eval_expr(m, arena, arg, env, ctx)?;
                    TermNode::Abs {
                        arg: scratch.add(TermNode::Lit { value: v }),
                    }
                }
                TermNode::Count { source } => {
                    let v = eval_expr(m, arena, source, env, ctx)?;
                    TermNode::Count {
                        source: scratch.add(TermNode::Lit { value: v }),
                    }
                }
                TermNode::Last { seq } => {
                    let v = eval_expr(m, arena, seq, env, ctx)?;
                    TermNode::Last {
                        seq: scratch.add(TermNode::Lit { value: v }),
                    }
                }
                _ => return Err(Flow::Trap("expr:unsupported_over_prog".to_string())),
            };
            let root = scratch.add(rebuilt);
            Ok(evaluate(&scratch, root, env, ctx))
        }
    }
}

// ---------------------------------------------------------------------------
// Native oracles
// ---------------------------------------------------------------------------

fn call_native_oracle(
    name: &str,
    recv: Option<&Value>,
    args: &[Value],
    interner: &Interner,
) -> ExprResult {
    if let Some(recv_v) = recv {
        // Q1 `string_methods`/`dict_methods`: method-recv native
        // oracles (`x.upper()`, `d.items()`, ...). Anything else
        // declared-but-not-natively-implemented traps honestly — never
        // a silent no-op.
        return call_recv_oracle(name, recv_v, args, interner);
    }
    let one = |args: &[Value]| -> Result<Value, Flow> {
        if args.len() == 1 {
            Ok(args[0].clone())
        } else {
            Err(Flow::Trap(format!("extern:{}:arity", name)))
        }
    };
    match name {
        "len" => {
            let v = one(args)?;
            let n = match &v {
                Value::Tuple(items) | Value::List(items) => items.len(),
                Value::Set(items) | Value::FrozenSet(items) => items.len(),
                Value::Dict(pairs) => pairs.len(),
                Value::Str(_) | Value::Surface(SurfaceKind::Text, _) => {
                    str_like_owned(&v, interner)
                        .unwrap_or_default()
                        .chars()
                        .count()
                }
                other => return Err(Flow::Trap(format!("extern:len:{}", value_kind(other)))),
            };
            Ok(Value::Int(n as i64))
        }
        "abs" => match one(args)? {
            Value::Int(n) => Ok(Value::Int(n.abs())),
            Value::Float(f) => Ok(Value::Float(f.abs())),
            Value::Bool(b) => Ok(Value::Int(if b { 1 } else { 0 })),
            Value::Rational(n, d) => Ok(match n.checked_abs() {
                Some(an) => Value::Rational(an, d),
                None => Value::Float((n as f64 / d as f64).abs()),
            }),
            other => Err(Flow::Trap(format!("extern:abs:{}", value_kind(&other)))),
        },
        "min" | "max" => {
            let items: Vec<Value> = if args.len() == 1 {
                iter_items(&args[0], interner)?
            } else {
                args.to_vec()
            };
            if items.is_empty() {
                return Err(Flow::Trap(format!("extern:{}:empty", name)));
            }
            let mut best = items[0].clone();
            for it in &items[1..] {
                // REPORTED-ORDER site (Python `min()`/`max()`): the returned
                // VALUE is decided here, so string comparisons must be real
                // lexicographic order — see
                // CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md.
                let ord = crate::value::cmp_value_lex(it, &best, interner);
                let take = if name == "min" {
                    ord == std::cmp::Ordering::Less
                } else {
                    ord == std::cmp::Ordering::Greater
                };
                if take {
                    best = it.clone();
                }
            }
            Ok(best)
        }
        "range" => {
            let (start, stop, step) = match args.len() {
                1 => (0, args[0].as_i64(), 1),
                2 => (args[0].as_i64(), args[1].as_i64(), 1),
                3 => (args[0].as_i64(), args[1].as_i64(), args[2].as_i64()),
                _ => return Err(Flow::Trap("extern:range:arity".to_string())),
            };
            if step == 0 {
                return Err(Flow::Trap("extern:range:zero_step".to_string()));
            }
            let count = if step > 0 {
                ((stop - start).max(0) + step - 1) / step
            } else {
                ((start - stop).max(0) + (-step) - 1) / (-step)
            };
            if count > RANGE_CAP {
                // An honest trap, not a silent cap.
                return Err(Flow::Trap("extern:range:too_large".to_string()));
            }
            let mut out: SmallVec<[Value; 4]> = SmallVec::new();
            let mut x = start;
            for _ in 0..count {
                out.push(Value::Int(x));
                x += step;
            }
            Ok(Value::Tuple(Arc::new(out)))
        }
        "sum" => {
            let items = iter_items(&one(args)?, interner)?;
            let mut acc_i: i64 = 0;
            let mut acc_f: f64 = 0.0;
            let mut is_float = false;
            // Exact accumulator alongside the pre-existing int/float
            // ones — additive, same discipline as term.rs's
            // `numeric_variadic` (byte-identical when no Rational ever
            // appears: `is_float`/`acc_i`/`acc_f` and the final
            // int-vs-float choice below are untouched).
            let mut acc_r: (i64, i64) = (0, 1);
            let mut all_exact = true;
            for it in items {
                match it {
                    Value::Int(n) => {
                        acc_i += n;
                        acc_f += n as f64;
                        if all_exact {
                            match rational_add(acc_r, (n, 1)).and_then(|v| rational_parts(&v)) {
                                Some(p) => acc_r = p,
                                None => all_exact = false,
                            }
                        }
                    }
                    Value::Bool(b) => {
                        let n = if b { 1 } else { 0 };
                        acc_i += n;
                        acc_f += n as f64;
                        if all_exact {
                            match rational_add(acc_r, (n, 1)).and_then(|v| rational_parts(&v)) {
                                Some(p) => acc_r = p,
                                None => all_exact = false,
                            }
                        }
                    }
                    Value::Float(f) => {
                        is_float = true;
                        all_exact = false;
                        acc_f += f;
                    }
                    Value::Rational(n, d) => {
                        acc_f += n as f64 / d as f64;
                        if all_exact {
                            match rational_add(acc_r, (n, d)).and_then(|v| rational_parts(&v)) {
                                Some(p) => acc_r = p,
                                None => all_exact = false,
                            }
                        }
                    }
                    other => return Err(Flow::Trap(format!("extern:sum:{}", value_kind(&other)))),
                }
            }
            if is_float {
                Ok(Value::Float(acc_f))
            } else if all_exact {
                // When no Rational ever appeared, acc_r tracks the
                // SAME running sum as acc_i (both driven by the same
                // Int/Bool contributions) and reduces with denominator
                // 1 — `make_rational` collapses that to `Value::Int
                // (acc_i)`, byte-identical to the pre-existing branch.
                Ok(make_rational(acc_r.0, acc_r.1).unwrap_or(Value::Int(acc_i)))
            } else {
                Ok(Value::Int(acc_i))
            }
        }
        "str" => Ok(surf_string(py_str(&one(args)?, interner))),
        "int" => match one(args)? {
            Value::Int(n) => Ok(Value::Int(n)),
            Value::Float(f) => Ok(Value::Int(f.trunc() as i64)),
            Value::Bool(b) => Ok(Value::Int(if b { 1 } else { 0 })),
            // Truncation toward zero — same convention as `as_i64()`.
            Value::Rational(n, d) => Ok(Value::Int(n / d)),
            v @ (Value::Str(_) | Value::Surface(SurfaceKind::Text, _)) => {
                let s = str_like_owned(&v, interner).unwrap_or_default();
                s.trim()
                    .parse::<i64>()
                    .map(Value::Int)
                    .map_err(|_| Flow::Trap("extern:int:parse".to_string()))
            }
            other => Err(Flow::Trap(format!("extern:int:{}", value_kind(&other)))),
        },
        "float" => match one(args)? {
            Value::Int(n) => Ok(Value::Float(n as f64)),
            Value::Float(f) => Ok(Value::Float(f)),
            Value::Bool(b) => Ok(Value::Float(if b { 1.0 } else { 0.0 })),
            // THE boundary: Python's `float()` builtin always returns a
            // genuine float — this is precisely where a rational must
            // stop being exact and become the cross-frame double.
            Value::Rational(n, d) => Ok(Value::Float(n as f64 / d as f64)),
            v @ (Value::Str(_) | Value::Surface(SurfaceKind::Text, _)) => {
                let s = str_like_owned(&v, interner).unwrap_or_default();
                s.trim()
                    .parse::<f64>()
                    .map(Value::Float)
                    .map_err(|_| Flow::Trap("extern:float:parse".to_string()))
            }
            other => Err(Flow::Trap(format!("extern:float:{}", value_kind(&other)))),
        },
        "bool" => Ok(Value::Bool(one(args)?.truthy())),
        "sorted" => {
            let mut items = iter_items(&one(args)?, interner)?;
            // FIXED (CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md): this was
            // `cmp_value`'s (Str, Str) arm, ordering by INTERNER SYMBOL ID —
            // boot-history order, not alphabetical (the registered
            // `sorted`-on-strings defect, CMP_VALUE_SURFACE_FIX_RESULTS.md
            // §4). `sorted()`'s output IS the reported order, so it now uses
            // the interner-aware lexicographic comparator instead.
            items.sort_by(|a, b| crate::value::cmp_value_lex(a, b, interner));
            Ok(Value::List(Arc::new(items.into_iter().collect())))
        }

        // --- Q1 math_native ---
        "round" => match args.len() {
            1 => match &args[0] {
                Value::Int(n) => Ok(Value::Int(*n)),
                Value::Float(f) => Ok(Value::Int(round_half_even(*f) as i64)),
                Value::Bool(b) => Ok(Value::Int(if *b { 1 } else { 0 })),
                // `round()` always returns an int regardless of input
                // type, so this is honestly approximate (round-half-
                // even of the rendered double) the same way the
                // Float arm already is — not a new precision concern.
                Value::Rational(n, d) => {
                    Ok(Value::Int(round_half_even(*n as f64 / *d as f64) as i64))
                }
                other => Err(Flow::Trap(format!("extern:round:{}", value_kind(other)))),
            },
            2 => {
                let nd = args[1].as_i64() as i32;
                match &args[0] {
                    Value::Int(n) if nd >= 0 => Ok(Value::Int(*n)),
                    Value::Int(n) => {
                        let f = round_half_even_digits(*n as f64, nd);
                        Ok(Value::Int(f as i64))
                    }
                    Value::Float(f) => Ok(Value::Float(round_half_even_digits(*f, nd))),
                    // Python's 2-arg `round(fraction, ndigits)` on a
                    // non-int returns the same TYPE it was given
                    // (a Fraction stays a Fraction); this engine has no
                    // fraction-precision-rounding primitive, so it
                    // renders to float here (the boundary) rather than
                    // approximate a Rational round — honest, not exact.
                    Value::Rational(n, d) => Ok(Value::Float(round_half_even_digits(
                        *n as f64 / *d as f64,
                        nd,
                    ))),
                    other => Err(Flow::Trap(format!("extern:round:{}", value_kind(other)))),
                }
            }
            _ => Err(Flow::Trap("extern:round:arity".to_string())),
        },
        "pow" => match args.len() {
            2 => match (&args[0], &args[1]) {
                (Value::Int(b), Value::Int(e)) if *e >= 0 => match b.checked_pow(*e as u32) {
                    Some(v) => Ok(Value::Int(v)),
                    None => Ok(Value::Float((*b as f64).powf(*e as f64))),
                },
                (a, b) => Ok(Value::Float(a.as_f64().powf(b.as_f64()))),
            },
            // 3-arg modpow: a genuinely different algorithm, not a
            // gap that scales with the rest of this table — refused
            // honestly rather than approximated.
            3 => Err(Flow::Trap("extern:unimplemented:pow:mod".to_string())),
            _ => Err(Flow::Trap("extern:pow:arity".to_string())),
        },
        "divmod" => {
            if args.len() != 2 {
                return Err(Flow::Trap("extern:divmod:arity".to_string()));
            }
            match (&args[0], &args[1]) {
                (Value::Int(a), Value::Int(b)) => {
                    if *b == 0 {
                        return Err(Flow::Trap("extern:divmod:zero".to_string()));
                    }
                    let q = floor_div_i64(*a, *b);
                    let r = floor_mod_i64(*a, *b);
                    Ok(Value::Tuple(Arc::new(smallvec::smallvec![
                        Value::Int(q),
                        Value::Int(r)
                    ])))
                }
                (a, b) => {
                    let (af, bf) = (a.as_f64(), b.as_f64());
                    if bf == 0.0 {
                        return Err(Flow::Trap("extern:divmod:zero".to_string()));
                    }
                    let q = floor_div_f64(af, bf);
                    let r = af - q * bf;
                    Ok(Value::Tuple(Arc::new(smallvec::smallvec![
                        Value::Float(q),
                        Value::Float(r)
                    ])))
                }
            }
        }
        "ord" => {
            let s = str_like_owned(&one(args)?, interner)
                .ok_or_else(|| Flow::Trap("extern:ord:type".to_string()))?;
            let mut chars = s.chars();
            match (chars.next(), chars.next()) {
                (Some(c), None) => Ok(Value::Int(c as i64)),
                _ => Err(Flow::Trap("extern:ord:arity".to_string())),
            }
        }
        "chr" => {
            let n = one(args)?.as_i64();
            match u32::try_from(n).ok().and_then(char::from_u32) {
                Some(c) => Ok(surf_string(c.to_string())),
                None => Err(Flow::Trap("extern:chr:range".to_string())),
            }
        }
        "math.sqrt" => {
            let f = one(args)?.as_f64();
            if f < 0.0 {
                Err(Flow::Trap("extern:math.sqrt:domain".to_string()))
            } else {
                Ok(Value::Float(f.sqrt()))
            }
        }
        "math.floor" => Ok(Value::Int(one(args)?.as_f64().floor() as i64)),
        "math.ceil" => Ok(Value::Int(one(args)?.as_f64().ceil() as i64)),
        "math.pow" => {
            if args.len() != 2 {
                return Err(Flow::Trap("extern:math.pow:arity".to_string()));
            }
            Ok(Value::Float(args[0].as_f64().powf(args[1].as_f64())))
        }
        "math.trunc" => Ok(Value::Int(one(args)?.as_f64().trunc() as i64)),

        // --- Q1 container_ctor ---
        "list" | "tuple" => {
            let items = match args.len() {
                0 => Vec::new(),
                1 => iter_items(&args[0], interner)?,
                _ => return Err(Flow::Trap(format!("extern:{}:arity", name))),
            };
            let out = Arc::new(items.into_iter().collect());
            Ok(if name == "tuple" {
                Value::Tuple(out)
            } else {
                Value::List(out)
            })
        }
        "set" => {
            let items = match args.len() {
                0 => Vec::new(),
                1 => iter_items(&args[0], interner)?,
                _ => return Err(Flow::Trap("extern:set:arity".to_string())),
            };
            Ok(Value::make_set(items))
        }
        "frozenset" => {
            let items = match args.len() {
                0 => Vec::new(),
                1 => iter_items(&args[0], interner)?,
                _ => return Err(Flow::Trap("extern:frozenset:arity".to_string())),
            };
            Ok(Value::make_frozenset(items))
        }
        "dict" => {
            let pairs = match args.len() {
                0 => Vec::new(),
                1 => {
                    // dict(iterable_of_pairs) — each item a 2-Tuple.
                    let items = iter_items(&args[0], interner)?;
                    let mut out = Vec::with_capacity(items.len());
                    for it in items {
                        let (Value::Tuple(pair) | Value::List(pair)) = it else {
                            return Err(Flow::Trap("extern:dict:item".to_string()));
                        };
                        if pair.len() != 2 {
                            return Err(Flow::Trap("extern:dict:item".to_string()));
                        }
                        out.push((pair[0].clone(), pair[1].clone()));
                    }
                    out
                }
                _ => return Err(Flow::Trap("extern:dict:arity".to_string())),
            };
            let mut out = pairs;
            out.sort_by(|a, b| cmp_value(&a.0, &b.0));
            Ok(Value::Dict(Arc::from(out)))
        }

        // --- Q1 general_builtins (the subset expressible without a
        // first-class callable/lazy-iterator value; map/next/iter are
        // refused honestly rather than approximated — see module docs
        // residuals) ---
        "all" => {
            let items = iter_items(&one(args)?, interner)?;
            Ok(Value::Bool(items.iter().all(|v| v.truthy())))
        }
        "any" => {
            let items = iter_items(&one(args)?, interner)?;
            Ok(Value::Bool(items.iter().any(|v| v.truthy())))
        }
        "isinstance" => {
            if args.len() != 2 {
                return Err(Flow::Trap("extern:isinstance:arity".to_string()));
            }
            let type_name = str_like_owned(&args[1], interner)
                .ok_or_else(|| Flow::Trap("extern:isinstance:argtype".to_string()))?;
            let matches = match type_name.as_str() {
                "int" => matches!(&args[0], Value::Int(_)),
                // A Rational IS a float from Python's point of view —
                // it exists here only because the value that would
                // have been a genuine `float` (a `/` result) is
                // represented exactly internally; its Python-facing
                // TYPE IDENTITY must still read as `float`, or
                // `isinstance(a / b, float)` would wrongly flip to
                // False under this feature (a real regression).
                "float" => matches!(&args[0], Value::Float(_) | Value::Rational(_, _)),
                "str" => matches!(
                    &args[0],
                    Value::Str(_) | Value::Surface(SurfaceKind::Text, _)
                ),
                "bool" => matches!(&args[0], Value::Bool(_)),
                // The type identity MBPP's asserts turn on. Before the
                // ARC6 value layer these two were literally the same test.
                "list" => matches!(&args[0], Value::List(_)),
                "tuple" => matches!(&args[0], Value::Tuple(_)),
                "dict" => matches!(&args[0], Value::Dict(_)),
                "set" | "frozenset" => matches!(&args[0], Value::Set(_) | Value::FrozenSet(_)),
                "NoneType" | "none" => matches!(&args[0], Value::None),
                other => {
                    return Err(Flow::Trap(format!(
                        "extern:isinstance:unknown_type:{}",
                        other
                    )))
                }
            };
            Ok(Value::Bool(matches))
        }
        "enumerate" => {
            let (items, start) = match args.len() {
                1 => (iter_items(&args[0], interner)?, 0i64),
                2 => (iter_items(&args[0], interner)?, args[1].as_i64()),
                _ => return Err(Flow::Trap("extern:enumerate:arity".to_string())),
            };
            let out: SmallVec<[Value; 4]> = items
                .into_iter()
                .enumerate()
                .map(|(i, v)| {
                    Value::Tuple(Arc::new(smallvec::smallvec![
                        Value::Int(start + i as i64),
                        v
                    ]))
                })
                .collect();
            Ok(Value::Tuple(Arc::new(out)))
        }
        "zip" => {
            if args.is_empty() {
                return Ok(Value::Tuple(Arc::new(SmallVec::new())));
            }
            let mut cols: Vec<Vec<Value>> = Vec::with_capacity(args.len());
            for a in args {
                cols.push(iter_items(a, interner)?);
            }
            let n = cols.iter().map(|c| c.len()).min().unwrap_or(0);
            let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(n);
            for i in 0..n {
                let row: SmallVec<[Value; 4]> = cols.iter().map(|c| c[i].clone()).collect();
                out.push(Value::Tuple(Arc::new(row)));
            }
            Ok(Value::Tuple(Arc::new(out)))
        }
        "reversed" => {
            let mut items = iter_items(&one(args)?, interner)?;
            items.reverse();
            Ok(Value::Tuple(Arc::new(items.into_iter().collect())))
        }

        other => Err(Flow::Trap(format!("extern:unimplemented:{}", other))),
    }
}

/// Q1 `string_methods` / `dict_methods`: method-recv native oracles
/// (`x.upper()`, `d.items()`, ...). Mutating members (`list.append`,
/// `dict.setdefault`, ...) are a DIFFERENT, unaddressed class of gap —
/// `ProgCallExtern` is a pure expression call with no lvalue write-back
/// path (the same reason `collection_methods` is not landed this
/// phase); every method here is read-only / value-returning.
fn call_recv_oracle(name: &str, recv: &Value, args: &[Value], interner: &Interner) -> ExprResult {
    // --- dict_methods (read-only) ---
    if let Value::Dict(pairs) = recv {
        match name {
            "items" => {
                let out: SmallVec<[Value; 4]> = pairs
                    .iter()
                    .map(|(k, v)| Value::Tuple(Arc::new(smallvec::smallvec![k.clone(), v.clone()])))
                    .collect();
                return Ok(Value::Tuple(Arc::new(out)));
            }
            "keys" => {
                let out: SmallVec<[Value; 4]> = pairs.iter().map(|(k, _)| k.clone()).collect();
                return Ok(Value::Tuple(Arc::new(out)));
            }
            "values" => {
                let out: SmallVec<[Value; 4]> = pairs.iter().map(|(_, v)| v.clone()).collect();
                return Ok(Value::Tuple(Arc::new(out)));
            }
            "get" => {
                let key = args
                    .first()
                    .ok_or_else(|| Flow::Trap("extern:get:arity".to_string()))?;
                let found = pairs.iter().find(|(k, _)| {
                    cmp_value(k, key) == std::cmp::Ordering::Equal
                        || matches!(
                            (str_like_owned(k, interner), str_like_owned(key, interner)),
                            (Some(a), Some(b)) if a == b
                        )
                });
                return match found {
                    Some((_, v)) => Ok(v.clone()),
                    None => Ok(args.get(1).cloned().unwrap_or(Value::None)),
                };
            }
            _ => {}
        }
    }
    // --- string_methods ---
    let s = str_like_owned(recv, interner)
        .ok_or_else(|| Flow::Trap(format!("extern:unimplemented:{}", name)))?;
    match name {
        "upper" => Ok(surf_string(s.to_uppercase())),
        "lower" => Ok(surf_string(s.to_lowercase())),
        "capitalize" => {
            let mut chars = s.chars();
            let out = match chars.next() {
                Some(c) => c.to_uppercase().collect::<String>() + &chars.as_str().to_lowercase(),
                None => String::new(),
            };
            Ok(surf_string(out))
        }
        "strip" | "lstrip" | "rstrip" => {
            let chars_arg = match args.first() {
                Some(v) => Some(
                    str_like_owned(v, interner)
                        .ok_or_else(|| Flow::Trap(format!("extern:{}:argtype", name)))?,
                ),
                None => None,
            };
            let (left, right) = match name {
                "lstrip" => (true, false),
                "rstrip" => (false, true),
                _ => (true, true),
            };
            Ok(surf_string(strip_chars(
                &s,
                chars_arg.as_deref(),
                left,
                right,
            )))
        }
        "split" => {
            let sep = match args.first() {
                Some(Value::None) | None => None,
                Some(v) => Some(
                    str_like_owned(v, interner)
                        .ok_or_else(|| Flow::Trap("extern:split:argtype".to_string()))?,
                ),
            };
            let maxsplit = match args.get(1) {
                Some(v) => Some(v.as_i64()),
                None => None,
            };
            let parts: Vec<String> = match (&sep, maxsplit) {
                (None, _) => s.split_whitespace().map(|p| p.to_string()).collect(),
                (Some(sep), None) => {
                    if sep.is_empty() {
                        return Err(Flow::Trap("extern:split:empty_sep".to_string()));
                    }
                    s.split(sep.as_str()).map(|p| p.to_string()).collect()
                }
                (Some(sep), Some(n)) => {
                    if sep.is_empty() {
                        return Err(Flow::Trap("extern:split:empty_sep".to_string()));
                    }
                    let n = if n < 0 {
                        usize::MAX
                    } else {
                        (n as usize).saturating_add(1)
                    };
                    s.splitn(n, sep.as_str()).map(|p| p.to_string()).collect()
                }
            };
            // CPython's `str.split` returns a LIST.
            let out: SmallVec<[Value; 4]> = parts.into_iter().map(surf_string).collect();
            Ok(Value::List(Arc::new(out)))
        }
        "join" => {
            let iterable = args
                .first()
                .ok_or_else(|| Flow::Trap("extern:join:arity".to_string()))?;
            let items = iter_items(iterable, interner)?;
            let mut parts = Vec::with_capacity(items.len());
            for it in items {
                parts.push(
                    str_like_owned(&it, interner)
                        .ok_or_else(|| Flow::Trap("extern:join:type".to_string()))?,
                );
            }
            Ok(surf_string(parts.join(&s)))
        }
        "replace" => {
            if args.len() < 2 {
                return Err(Flow::Trap("extern:replace:arity".to_string()));
            }
            let old = str_like_owned(&args[0], interner)
                .ok_or_else(|| Flow::Trap("extern:replace:argtype".to_string()))?;
            let new = str_like_owned(&args[1], interner)
                .ok_or_else(|| Flow::Trap("extern:replace:argtype".to_string()))?;
            let out = match args.get(2) {
                Some(v) => {
                    let count = v.as_i64();
                    if count < 0 {
                        s.replace(old.as_str(), &new)
                    } else {
                        s.replacen(old.as_str(), &new, count as usize)
                    }
                }
                None => s.replace(old.as_str(), &new),
            };
            Ok(surf_string(out))
        }
        "startswith" | "endswith" => {
            let arg = args
                .first()
                .ok_or_else(|| Flow::Trap(format!("extern:{}:arity", name)))?;
            let candidates: Vec<String> = match arg {
                Value::Tuple(items) | Value::List(items) => items
                    .iter()
                    .filter_map(|v| str_like_owned(v, interner))
                    .collect(),
                other => vec![str_like_owned(other, interner)
                    .ok_or_else(|| Flow::Trap(format!("extern:{}:argtype", name)))?],
            };
            let hit = candidates.iter().any(|c| {
                if name == "startswith" {
                    s.starts_with(c.as_str())
                } else {
                    s.ends_with(c.as_str())
                }
            });
            Ok(Value::Bool(hit))
        }
        "find" => {
            let needle = args
                .first()
                .ok_or_else(|| Flow::Trap("extern:find:arity".to_string()))?;
            let needle = str_like_owned(needle, interner)
                .ok_or_else(|| Flow::Trap("extern:find:argtype".to_string()))?;
            Ok(Value::Int(match s.find(needle.as_str()) {
                Some(byte_idx) => byte_to_char_idx(&s, byte_idx),
                None => -1,
            }))
        }
        "count" => {
            let needle = args
                .first()
                .ok_or_else(|| Flow::Trap("extern:count:arity".to_string()))?;
            let needle = str_like_owned(needle, interner)
                .ok_or_else(|| Flow::Trap("extern:count:argtype".to_string()))?;
            let n = if needle.is_empty() {
                s.chars().count() as i64 + 1
            } else {
                s.matches(needle.as_str()).count() as i64
            };
            Ok(Value::Int(n))
        }
        "isdigit" => Ok(Value::Bool(
            !s.is_empty() && s.chars().all(|c| c.is_ascii_digit()),
        )),
        "isalpha" => Ok(Value::Bool(
            !s.is_empty() && s.chars().all(|c| c.is_alphabetic()),
        )),
        "isupper" => {
            let cased: Vec<char> = s.chars().filter(|c| c.is_alphabetic()).collect();
            Ok(Value::Bool(
                !cased.is_empty() && cased.iter().all(|c| c.is_uppercase()),
            ))
        }
        "islower" => {
            let cased: Vec<char> = s.chars().filter(|c| c.is_alphabetic()).collect();
            Ok(Value::Bool(
                !cased.is_empty() && cased.iter().all(|c| c.is_lowercase()),
            ))
        }
        other => Err(Flow::Trap(format!("extern:unimplemented:{}", other))),
    }
}

// ---------------------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------------------

/// The `TermNode::ProgEval` engine. See module docs for the contract.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_prog_eval(
    arena: &TermArena,
    prog: TermIdx,
    env_t: Option<TermIdx>,
    oracles_t: Option<TermIdx>,
    fuel: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let fuel = if fuel <= 0 { DEFAULT_FUEL } else { fuel };

    // Seed program bindings from the env Dict.
    let mut vars: Vec<(Sym, Value)> = Vec::new();
    let mut passthrough: Vec<(Value, Value)> = Vec::new();
    if let Some(e) = env_t {
        let ev = evaluate(arena, e, env, ctx);
        if let Value::Dict(pairs) = ev {
            for (k, v) in pairs.iter() {
                let sym = match k {
                    Value::Str(s) => Some(*s),
                    Value::Surface(SurfaceKind::Text, b) => {
                        let s = String::from_utf8_lossy(b);
                        ctx.interner.lookup(&s)
                    }
                    _ => None,
                };
                match sym {
                    Some(s) => vars.push((s, v.clone())),
                    // A key with no interned Sym can never be referenced
                    // by parsed IR — pass through untouched.
                    None => passthrough.push((k.clone(), v.clone())),
                }
            }
        }
    }
    let oracles = match oracles_t {
        Some(o) => evaluate(arena, o, env, ctx),
        None => Value::None,
    };

    let mut machine = Machine {
        vars,
        passthrough,
        oracles,
        steps: 0,
        fuel,
    };

    // Resolve the program: inline Prog* subtree, or a Node rooting a
    // reflected IR subgraph.
    let mut scratch_prog = TermArena::new();
    let (prog_arena, prog_idx): (&TermArena, TermIdx) = if is_prog(arena.get(prog)) {
        (arena, prog)
    } else {
        let pv = evaluate(arena, prog, env, ctx);
        match pv {
            Value::Node(nid) => {
                let _helper_work = crate::access_trace::enter_helper_scope(
                    crate::access_trace::HELPER_PROG_EVAL_DECODE,
                );
                match crate::reflect::term_from_subgraph(
                    ctx.graph,
                    ctx.interner,
                    nid,
                    &mut scratch_prog,
                ) {
                    Ok(sub) => {
                        if is_prog(scratch_prog.get(sub)) {
                            (&scratch_prog, sub)
                        } else {
                            return finish_result(
                                &machine,
                                Value::None,
                                false,
                                Some("prog:invalid".to_string()),
                                field,
                                ctx.interner,
                            );
                        }
                    }
                    Err(_) => {
                        return finish_result(
                            &machine,
                            Value::None,
                            false,
                            Some("prog:invalid".to_string()),
                            field,
                            ctx.interner,
                        )
                    }
                }
            }
            _ => {
                return finish_result(
                    &machine,
                    Value::None,
                    false,
                    Some("prog:invalid".to_string()),
                    field,
                    ctx.interner,
                )
            }
        }
    };

    // Run. A statement root executes; an expression root evaluates to
    // `result` (charging one step, like a bare-expression statement).
    let outcome: Result<Value, Flow> = if is_prog_stmt(prog_arena.get(prog_idx)) {
        match exec_stmt(&mut machine, prog_arena, prog_idx, env, ctx) {
            Ok(()) => Ok(Value::None),
            Err(Flow::Return(v)) => Ok(v),
            Err(other) => Err(other),
        }
    } else {
        match machine.charge() {
            Ok(()) => eval_expr(&mut machine, prog_arena, prog_idx, env, ctx),
            Err(f) => Err(f),
        }
    };

    match outcome {
        Ok(result) => finish_result(&machine, result, true, None, field, ctx.interner),
        Err(Flow::Fuel) => finish_result(
            &machine,
            Value::None,
            false,
            Some("fuel".to_string()),
            field,
            ctx.interner,
        ),
        Err(Flow::Trap(t)) => {
            finish_result(&machine, Value::None, false, Some(t), field, ctx.interner)
        }
        Err(Flow::Break) | Err(Flow::Continue) => finish_result(
            &machine,
            Value::None,
            false,
            Some("loopctl:outside_loop".to_string()),
            field,
            ctx.interner,
        ),
        Err(Flow::Return(v)) => finish_result(&machine, v, true, None, field, ctx.interner),
    }
}

fn finish_result(
    m: &Machine,
    result: Value,
    halted: bool,
    trap: Option<String>,
    field: Sym,
    interner: &Interner,
) -> Value {
    // env_out: program bindings + untouched passthrough pairs.
    let mut env_pairs: Vec<(Value, Value)> = m
        .vars
        .iter()
        .map(|(k, v)| (Value::Str(*k), v.clone()))
        .collect();
    env_pairs.extend(m.passthrough.iter().cloned());
    env_pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));

    let mut pairs: Vec<(Value, Value)> = vec![
        (surf("result"), result),
        (surf("env_out"), Value::Dict(Arc::from(env_pairs))),
        (surf("steps"), Value::Int(m.steps)),
        (surf("halted"), Value::Bool(halted)),
        (
            surf("trap"),
            match trap {
                Some(t) => surf_string(t),
                None => Value::None,
            },
        ),
    ];
    pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
    let dict = Value::Dict(Arc::from(pairs));
    if field == Sym::default() {
        return dict;
    }
    // Local field selector (the strokes.rs convention).
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
        fn sym(&mut self, s: &str) -> Sym {
            self.interner.intern(s)
        }
        fn lit(&mut self, v: Value) -> TermIdx {
            self.arena.add(TermNode::Lit { value: v })
        }
        fn var(&mut self, name: &str) -> TermIdx {
            let s = self.sym(name);
            self.arena.add(TermNode::Var { name: s })
        }
        fn run(&mut self, prog: TermIdx, fuel: i64) -> Value {
            self.run_with(prog, fuel, None, None)
        }
        fn run_with(
            &mut self,
            prog: TermIdx,
            fuel: i64,
            env_t: Option<TermIdx>,
            oracles: Option<TermIdx>,
        ) -> Value {
            let pe = self.arena.add(TermNode::ProgEval {
                prog,
                env: env_t,
                oracles,
                fuel,
                field: Sym::default(),
            });
            let mut env: Env = SmallVec::new();
            let mut ctx = EvalCtx::new(&self.graph, &self.interner);
            evaluate(&self.arena, pe, &mut env, &mut ctx)
        }
        /// oracle Dict declaring the given names.
        fn oracle_decl(&mut self, names: &[&str]) -> TermIdx {
            let mut pairs: Vec<(Value, Value)> = names
                .iter()
                .map(|n| {
                    let s = self.interner.intern(n);
                    (Value::Str(s), Value::Str(self.interner.intern("builtin")))
                })
                .collect();
            pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
            self.lit(Value::Dict(Arc::from(pairs)))
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

    fn env_var(v: &Value, interner: &Interner, name: &str) -> Value {
        let env = dget(v, "env_out");
        if let Value::Dict(pairs) = env {
            for (k, val) in pairs.iter() {
                if let Value::Str(s) = k {
                    if interner.resolve(*s) == name {
                        return val.clone();
                    }
                }
            }
        }
        Value::None
    }

    #[test]
    fn arithmetic_assign_seq() {
        // a = 2; b = a * 3 + 4; c = b - a
        let mut f = Fixture::new();
        let a_s = f.sym("a");
        let b_s = f.sym("b");
        let c_s = f.sym("c");
        let two = f.lit(Value::Int(2));
        let s1 = f.arena.add(TermNode::ProgAssignVar {
            name: a_s,
            value: two,
        });
        let av = f.var("a");
        let three = f.lit(Value::Int(3));
        let mul = f.arena.add(TermNode::Times {
            items: vec![av, three],
        });
        let four = f.lit(Value::Int(4));
        let plus = f.arena.add(TermNode::Plus {
            items: vec![mul, four],
        });
        let s2 = f.arena.add(TermNode::ProgAssignVar {
            name: b_s,
            value: plus,
        });
        let bv = f.var("b");
        let av2 = f.var("a");
        let sub = f.arena.add(TermNode::Minus { a: bv, b: av2 });
        let s3 = f.arena.add(TermNode::ProgAssignVar {
            name: c_s,
            value: sub,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s1, s2, s3],
        });
        let out = f.run(seq, 100);
        assert_eq!(dget(&out, "halted"), Value::Bool(true));
        assert_eq!(dget(&out, "trap"), Value::None);
        assert_eq!(env_var(&out, &f.interner, "a"), Value::Int(2));
        assert_eq!(env_var(&out, &f.interner, "b"), Value::Int(10));
        assert_eq!(env_var(&out, &f.interner, "c"), Value::Int(8));
        assert_eq!(dget(&out, "steps"), Value::Int(3));
    }

    #[test]
    fn if_else_branches() {
        // if x > 3: y = 1 else: y = 0   (x = 5)
        let mut f = Fixture::new();
        let x_s = f.sym("x");
        let y_s = f.sym("y");
        let five = f.lit(Value::Int(5));
        let s0 = f.arena.add(TermNode::ProgAssignVar {
            name: x_s,
            value: five,
        });
        let xv = f.var("x");
        let three = f.lit(Value::Int(3));
        let cond = f.arena.add(TermNode::Gt { a: xv, b: three });
        let one = f.lit(Value::Int(1));
        let then = f.arena.add(TermNode::ProgAssignVar {
            name: y_s,
            value: one,
        });
        let zero = f.lit(Value::Int(0));
        let els = f.arena.add(TermNode::ProgAssignVar {
            name: y_s,
            value: zero,
        });
        let ifs = f.arena.add(TermNode::ProgIfStmt {
            cond,
            then,
            orelse: Some(els),
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, ifs],
        });
        let out = f.run(seq, 100);
        assert_eq!(env_var(&out, &f.interner, "y"), Value::Int(1));
        assert_eq!(dget(&out, "halted"), Value::Bool(true));
    }

    #[test]
    fn for_with_accumulator() {
        // total = 0; for i in range(5): total += i   → 10
        let mut f = Fixture::new();
        let total_s = f.sym("total");
        let i_s = f.sym("i");
        let range_s = f.sym("range");
        let add_s = f.sym("add");
        let zero = f.lit(Value::Int(0));
        let s0 = f.arena.add(TermNode::ProgAssignVar {
            name: total_s,
            value: zero,
        });
        let five = f.lit(Value::Int(5));
        let call = f.arena.add(TermNode::ProgCallExtern {
            name: range_s,
            recv: None,
            args: vec![five],
        });
        let iv = f.var("i");
        let aug = f.arena.add(TermNode::ProgAugAssign {
            name: total_s,
            op: add_s,
            value: iv,
        });
        let fore = f.arena.add(TermNode::ProgForEach {
            var: i_s,
            iter: call,
            body: aug,
            orelse: None,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, fore],
        });
        let oracles = f.oracle_decl(&["range"]);
        let out = f.run_with(seq, 100, None, Some(oracles));
        assert_eq!(dget(&out, "trap"), Value::None);
        assert_eq!(env_var(&out, &f.interner, "total"), Value::Int(10));
        assert_eq!(dget(&out, "halted"), Value::Bool(true));
    }

    #[test]
    fn while_and_fuel_exhaustion() {
        // while True: i = i + 1   with fuel 7 → halted false, steps == 7
        let mut f = Fixture::new();
        let i_s = f.sym("i");
        let zero = f.lit(Value::Int(0));
        let s0 = f.arena.add(TermNode::ProgAssignVar {
            name: i_s,
            value: zero,
        });
        let tru = f.lit(Value::Bool(true));
        let iv = f.var("i");
        let one = f.lit(Value::Int(1));
        let plus = f.arena.add(TermNode::Plus {
            items: vec![iv, one],
        });
        let body = f.arena.add(TermNode::ProgAssignVar {
            name: i_s,
            value: plus,
        });
        let wh = f.arena.add(TermNode::ProgWhile {
            cond: tru,
            body,
            orelse: None,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, wh],
        });
        let out = f.run(seq, 7);
        assert_eq!(dget(&out, "halted"), Value::Bool(false));
        assert_eq!(dget(&out, "steps"), Value::Int(7));
        assert_eq!(dget(&out, "trap"), surf("fuel"));
        assert_eq!(dget(&out, "result"), Value::None);
        // Honest PARTIAL env: i advanced some but the loop never closed.
        assert!(matches!(env_var(&out, &f.interner, "i"), Value::Int(n) if n > 0));
    }

    #[test]
    fn while_terminates_within_fuel() {
        // i = 0; s = 0; while i < 5: s += i; i += 1   → s = 10
        let mut f = Fixture::new();
        let i_s = f.sym("i");
        let s_s = f.sym("s");
        let add_s = f.sym("add");
        let zero1 = f.lit(Value::Int(0));
        let a0 = f.arena.add(TermNode::ProgAssignVar {
            name: i_s,
            value: zero1,
        });
        let zero2 = f.lit(Value::Int(0));
        let a1 = f.arena.add(TermNode::ProgAssignVar {
            name: s_s,
            value: zero2,
        });
        let iv = f.var("i");
        let five = f.lit(Value::Int(5));
        let cond = f.arena.add(TermNode::Lt { a: iv, b: five });
        let iv2 = f.var("i");
        let aug1 = f.arena.add(TermNode::ProgAugAssign {
            name: s_s,
            op: add_s,
            value: iv2,
        });
        let one = f.lit(Value::Int(1));
        let aug2 = f.arena.add(TermNode::ProgAugAssign {
            name: i_s,
            op: add_s,
            value: one,
        });
        let body = f.arena.add(TermNode::ProgSeq {
            stmts: vec![aug1, aug2],
        });
        let wh = f.arena.add(TermNode::ProgWhile {
            cond,
            body,
            orelse: None,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![a0, a1, wh],
        });
        let out = f.run(seq, 100);
        assert_eq!(dget(&out, "halted"), Value::Bool(true));
        assert_eq!(env_var(&out, &f.interner, "s"), Value::Int(10));
        assert_eq!(env_var(&out, &f.interner, "i"), Value::Int(5));
    }

    #[test]
    fn try_catches_raise_fuel_is_not_catchable() {
        // try: raise "boom" except as e: caught = 1  → caught, e bound
        let mut f = Fixture::new();
        let caught_s = f.sym("caught");
        let e_s = f.sym("e");
        let boom_sym__ = f.interner.intern("boom");
        let boom = f.lit(Value::Str(boom_sym__));
        let raise = f.arena.add(TermNode::ProgRaise { exc: Some(boom) });
        let one = f.lit(Value::Int(1));
        let handler = f.arena.add(TermNode::ProgAssignVar {
            name: caught_s,
            value: one,
        });
        let tryo = f.arena.add(TermNode::ProgTryOr {
            body: raise,
            exc_var: e_s,
            handler: Some(handler),
        });
        let out = f.run(tryo, 100);
        assert_eq!(dget(&out, "halted"), Value::Bool(true));
        assert_eq!(env_var(&out, &f.interner, "caught"), Value::Int(1));
        assert_eq!(env_var(&out, &f.interner, "e"), surf("raise:boom"));

        // Fuel exhaustion inside a try body is NOT caught.
        let mut f2 = Fixture::new();
        let tru = f2.lit(Value::Bool(true));
        let i_s = f2.sym("i");
        let one2 = f2.lit(Value::Int(1));
        let body = f2.arena.add(TermNode::ProgAssignVar {
            name: i_s,
            value: one2,
        });
        let wh = f2.arena.add(TermNode::ProgWhile {
            cond: tru,
            body,
            orelse: None,
        });
        let x_s = f2.sym("x");
        let nine = f2.lit(Value::Int(9));
        let handler2 = f2.arena.add(TermNode::ProgAssignVar {
            name: x_s,
            value: nine,
        });
        let tryo2 = f2.arena.add(TermNode::ProgTryOr {
            body: wh,
            exc_var: Sym::default(),
            handler: Some(handler2),
        });
        let out2 = f2.run(tryo2, 5);
        assert_eq!(dget(&out2, "halted"), Value::Bool(false));
        assert_eq!(dget(&out2, "trap"), surf("fuel"));
        assert_eq!(dget(&out2, "steps"), Value::Int(5));
        // The handler must NOT have run.
        assert_eq!(env_var(&out2, &f2.interner, "x"), Value::None);
    }

    #[test]
    fn uncaught_raise_traps_honestly() {
        let mut f = Fixture::new();
        let msg = f.lit(Value::Int(42));
        let raise = f.arena.add(TermNode::ProgRaise { exc: Some(msg) });
        let out = f.run(raise, 100);
        assert_eq!(dget(&out, "halted"), Value::Bool(false));
        assert_eq!(dget(&out, "trap"), surf("raise:42"));
    }

    #[test]
    fn tuple_unpack_binds_and_arity_traps() {
        let mut f = Fixture::new();
        let a_s = f.sym("a");
        let b_s = f.sym("b");
        let pair = f.lit(Value::Tuple(Arc::new(smallvec::smallvec![
            Value::Int(3),
            Value::Int(4)
        ])));
        let unp = f.arena.add(TermNode::ProgTupleUnpack {
            targets: vec![a_s, b_s],
            value: pair,
        });
        let out = f.run(unp, 100);
        assert_eq!(env_var(&out, &f.interner, "a"), Value::Int(3));
        assert_eq!(env_var(&out, &f.interner, "b"), Value::Int(4));

        let mut f2 = Fixture::new();
        let a2 = f2.sym("a");
        let b2 = f2.sym("b");
        let c2 = f2.sym("c");
        let pair2 = f2.lit(Value::Tuple(Arc::new(smallvec::smallvec![
            Value::Int(1),
            Value::Int(2)
        ])));
        let unp2 = f2.arena.add(TermNode::ProgTupleUnpack {
            targets: vec![a2, b2, c2],
            value: pair2,
        });
        let out2 = f2.run(unp2, 100);
        assert_eq!(dget(&out2, "halted"), Value::Bool(false));
        assert_eq!(dget(&out2, "trap"), surf("unpack:arity"));
    }

    #[test]
    fn comprehension_filters_and_maps() {
        // ys = [x*x for x in (1,2,3) if x > 1] → (4, 9)
        let mut f = Fixture::new();
        let x_s = f.sym("x");
        let ys_s = f.sym("ys");
        let src = f.lit(Value::Tuple(Arc::new(smallvec::smallvec![
            Value::Int(1),
            Value::Int(2),
            Value::Int(3)
        ])));
        let xv = f.var("x");
        let xv2 = f.var("x");
        let sq = f.arena.add(TermNode::Times {
            items: vec![xv, xv2],
        });
        let xv3 = f.var("x");
        let one = f.lit(Value::Int(1));
        let cond = f.arena.add(TermNode::Gt { a: xv3, b: one });
        let comp = f.arena.add(TermNode::ProgComprehensionList {
            var: x_s,
            source: src,
            expr: sq,
            cond: Some(cond),
        });
        let assign = f.arena.add(TermNode::ProgAssignVar {
            name: ys_s,
            value: comp,
        });
        let out = f.run(assign, 100);
        let ys = env_var(&out, &f.interner, "ys");
        // 2026-08-02 (ARC6 value layer): a list comprehension now realises
        // as `Value::List`, not `Value::Tuple` — the pin moved in the
        // improvement direction (CPython returns a `list` here).
        assert_eq!(
            ys,
            Value::List(Arc::new(smallvec::smallvec![Value::Int(4), Value::Int(9)]))
        );
        // Loop var does not leak (Python 3 comprehension scope).
        assert_eq!(env_var(&out, &f.interner, "x"), Value::None);
    }

    #[test]
    fn extern_oracle_declared_vs_undeclared() {
        // n = len((7,8,9)) with len declared → 3
        let mut f = Fixture::new();
        let n_s = f.sym("n");
        let len_s = f.sym("len");
        let xs = f.lit(Value::Tuple(Arc::new(smallvec::smallvec![
            Value::Int(7),
            Value::Int(8),
            Value::Int(9)
        ])));
        let call = f.arena.add(TermNode::ProgCallExtern {
            name: len_s,
            recv: None,
            args: vec![xs],
        });
        let assign = f.arena.add(TermNode::ProgAssignVar {
            name: n_s,
            value: call,
        });
        let oracles = f.oracle_decl(&["len"]);
        let out = f.run_with(assign, 100, None, Some(oracles));
        assert_eq!(env_var(&out, &f.interner, "n"), Value::Int(3));

        // y = foo(1) with nothing declared → trap extern:foo, halted:false
        let mut f2 = Fixture::new();
        let y_s = f2.sym("y");
        let foo_s = f2.sym("foo");
        let one = f2.lit(Value::Int(1));
        let call2 = f2.arena.add(TermNode::ProgCallExtern {
            name: foo_s,
            recv: None,
            args: vec![one],
        });
        let assign2 = f2.arena.add(TermNode::ProgAssignVar {
            name: y_s,
            value: call2,
        });
        let out2 = f2.run(assign2, 100);
        assert_eq!(dget(&out2, "halted"), Value::Bool(false));
        assert_eq!(dget(&out2, "trap"), surf("extern:foo"));
        assert_eq!(env_var(&out2, &f2.interner, "y"), Value::None);
    }

    #[test]
    fn nesting_loop_if_break_continue() {
        // total = 0
        // for i in range(10):
        //     if i == 3: break
        //     if i == 1: continue
        //     total += i          → 0 + 2 = 2
        let mut f = Fixture::new();
        let total_s = f.sym("total");
        let i_s = f.sym("i");
        let range_s = f.sym("range");
        let add_s = f.sym("add");
        let brk_s = f.sym("break");
        let cont_s = f.sym("continue");
        let zero = f.lit(Value::Int(0));
        let s0 = f.arena.add(TermNode::ProgAssignVar {
            name: total_s,
            value: zero,
        });
        let ten = f.lit(Value::Int(10));
        let call = f.arena.add(TermNode::ProgCallExtern {
            name: range_s,
            recv: None,
            args: vec![ten],
        });
        let iv1 = f.var("i");
        let three = f.lit(Value::Int(3));
        let is3 = f.arena.add(TermNode::Eq { a: iv1, b: three });
        let brk = f.arena.add(TermNode::ProgLoopCtl { kind: brk_s });
        let if_break = f.arena.add(TermNode::ProgIfStmt {
            cond: is3,
            then: brk,
            orelse: None,
        });
        let iv2 = f.var("i");
        let one = f.lit(Value::Int(1));
        let is1 = f.arena.add(TermNode::Eq { a: iv2, b: one });
        let cont = f.arena.add(TermNode::ProgLoopCtl { kind: cont_s });
        let if_cont = f.arena.add(TermNode::ProgIfStmt {
            cond: is1,
            then: cont,
            orelse: None,
        });
        let iv3 = f.var("i");
        let aug = f.arena.add(TermNode::ProgAugAssign {
            name: total_s,
            op: add_s,
            value: iv3,
        });
        let body = f.arena.add(TermNode::ProgSeq {
            stmts: vec![if_break, if_cont, aug],
        });
        let fore = f.arena.add(TermNode::ProgForEach {
            var: i_s,
            iter: call,
            body,
            orelse: None,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, fore],
        });
        let oracles = f.oracle_decl(&["range"]);
        let out = f.run_with(seq, 200, None, Some(oracles));
        assert_eq!(dget(&out, "trap"), Value::None);
        assert_eq!(env_var(&out, &f.interner, "total"), Value::Int(2));
    }

    #[test]
    fn return_carries_result_and_halts() {
        // x = 5; return x * 2; x = 99 (dead)
        let mut f = Fixture::new();
        let x_s = f.sym("x");
        let five = f.lit(Value::Int(5));
        let s0 = f.arena.add(TermNode::ProgAssignVar {
            name: x_s,
            value: five,
        });
        let xv = f.var("x");
        let two = f.lit(Value::Int(2));
        let mul = f.arena.add(TermNode::Times {
            items: vec![xv, two],
        });
        let ret = f.arena.add(TermNode::ProgReturn { value: Some(mul) });
        let nine9 = f.lit(Value::Int(99));
        let dead = f.arena.add(TermNode::ProgAssignVar {
            name: x_s,
            value: nine9,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, ret, dead],
        });
        let out = f.run(seq, 100);
        assert_eq!(dget(&out, "result"), Value::Int(10));
        assert_eq!(dget(&out, "halted"), Value::Bool(true));
        assert_eq!(env_var(&out, &f.interner, "x"), Value::Int(5));
    }

    #[test]
    fn subscript_and_attr_paths_read_write() {
        // d = {"k": 1}; d["k"] = 5; y = d["k"]
        let mut f = Fixture::new();
        let d_s = f.sym("d");
        let y_s = f.sym("y");
        let k_lit1_sym__ = f.interner.intern("k");
        let k_lit1 = f.lit(Value::Str(k_lit1_sym__));
        let one = f.lit(Value::Int(1));
        let dict_lit = f.arena.add(TermNode::ProgContainerLit {
            kind: f.interner.intern("dict"),
            items: vec![k_lit1, one],
        });
        let s0 = f.arena.add(TermNode::ProgAssignVar {
            name: d_s,
            value: dict_lit,
        });
        let dv = f.var("d");
        let k_lit2_sym__ = f.interner.intern("k");
        let k_lit2 = f.lit(Value::Str(k_lit2_sym__));
        let five = f.lit(Value::Int(5));
        let sset = f.arena.add(TermNode::ProgSubscriptSet {
            obj: dv,
            index: k_lit2,
            value: five,
        });
        let dv2 = f.var("d");
        let k_lit3_sym__ = f.interner.intern("k");
        let k_lit3 = f.lit(Value::Str(k_lit3_sym__));
        let sub = f.arena.add(TermNode::ProgSubscript {
            obj: dv2,
            index: k_lit3,
        });
        let s2 = f.arena.add(TermNode::ProgAssignVar {
            name: y_s,
            value: sub,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, sset, s2],
        });
        let out = f.run(seq, 100);
        assert_eq!(dget(&out, "trap"), Value::None);
        assert_eq!(env_var(&out, &f.interner, "y"), Value::Int(5));

        // r = {}; r.x = 7; z = r.x + 1
        let mut f2 = Fixture::new();
        let r_s = f2.sym("r");
        let z_s = f2.sym("z");
        let x_attr = f2.sym("x");
        let empty = f2.arena.add(TermNode::ProgContainerLit {
            kind: f2.interner.intern("dict"),
            items: vec![],
        });
        let s0 = f2.arena.add(TermNode::ProgAssignVar {
            name: r_s,
            value: empty,
        });
        let rv = f2.var("r");
        let seven = f2.lit(Value::Int(7));
        let aset = f2.arena.add(TermNode::ProgAttrSet {
            obj: rv,
            attr: x_attr,
            value: seven,
        });
        let rv2 = f2.var("r");
        let aget = f2.arena.add(TermNode::ProgAttrGet {
            obj: rv2,
            attr: x_attr,
        });
        let one2 = f2.lit(Value::Int(1));
        let plus = f2.arena.add(TermNode::Plus {
            items: vec![aget, one2],
        });
        let s2 = f2.arena.add(TermNode::ProgAssignVar {
            name: z_s,
            value: plus,
        });
        let seq2 = f2.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, aset, s2],
        });
        let out2 = f2.run(seq2, 100);
        assert_eq!(dget(&out2, "trap"), Value::None);
        assert_eq!(env_var(&out2, &f2.interner, "z"), Value::Int(8));
    }

    #[test]
    fn is_none_honest_and_unsupported_traps() {
        let mut f = Fixture::new();
        let y_s = f.sym("y");
        let none = f.lit(Value::None);
        let none2 = f.lit(Value::None);
        let is_op = f.arena.add(TermNode::ProgIsOp {
            a: none,
            b: none2,
            negated: false,
        });
        let assign = f.arena.add(TermNode::ProgAssignVar {
            name: y_s,
            value: is_op,
        });
        let out = f.run(assign, 100);
        assert_eq!(env_var(&out, &f.interner, "y"), Value::Bool(true));

        let mut f2 = Fixture::new();
        let y2 = f2.sym("y");
        let a = f2.lit(Value::Int(1));
        let b = f2.lit(Value::Int(1));
        let is_op2 = f2.arena.add(TermNode::ProgIsOp {
            a,
            b,
            negated: false,
        });
        let assign2 = f2.arena.add(TermNode::ProgAssignVar {
            name: y2,
            value: is_op2,
        });
        let out2 = f2.run(assign2, 100);
        assert_eq!(dget(&out2, "halted"), Value::Bool(false));
        assert_eq!(dget(&out2, "trap"), surf("is_op:unsupported"));
    }

    #[test]
    fn env_in_flows_through_and_fstring_renders() {
        // s = f"x={x}!"  with env {x: 7}
        let mut f = Fixture::new();
        let s_s = f.sym("s");
        let _x_s = f.sym("x");
        let seg_sym__ = f.interner.intern("x=");
        let seg = f.lit(Value::Str(seg_sym__));
        let xv = f.var("x");
        let bang_sym__ = f.interner.intern("!");
        let bang = f.lit(Value::Str(bang_sym__));
        let fs = f.arena.add(TermNode::ProgFString {
            parts: vec![seg, xv, bang],
        });
        let assign = f.arena.add(TermNode::ProgAssignVar {
            name: s_s,
            value: fs,
        });
        let mut pairs: Vec<(Value, Value)> =
            vec![(Value::Str(f.interner.intern("x")), Value::Int(7))];
        pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
        let env_t = f.lit(Value::Dict(Arc::from(pairs)));
        let out = f.run_with(assign, 100, Some(env_t), None);
        assert_eq!(env_var(&out, &f.interner, "s"), surf("x=7!"));
        // env_in var passes through to env_out too.
        assert_eq!(env_var(&out, &f.interner, "x"), Value::Int(7));
    }

    #[test]
    fn def_fn_param_default_and_missing() {
        // param n default 7; y = n + 1  (env empty → n = 7)
        let mut f = Fixture::new();
        let n_s = f.sym("n");
        let y_s = f.sym("y");
        let seven = f.lit(Value::Int(7));
        let p = f.arena.add(TermNode::ProgDefFnParam {
            name: n_s,
            default: Some(seven),
        });
        let nv = f.var("n");
        let one = f.lit(Value::Int(1));
        let plus = f.arena.add(TermNode::Plus {
            items: vec![nv, one],
        });
        let a = f.arena.add(TermNode::ProgAssignVar {
            name: y_s,
            value: plus,
        });
        let seq = f.arena.add(TermNode::ProgSeq { stmts: vec![p, a] });
        let out = f.run(seq, 100);
        assert_eq!(env_var(&out, &f.interner, "y"), Value::Int(8));

        // param q with NO default and no env → trap param:q
        let mut f2 = Fixture::new();
        let q_s = f2.sym("q");
        let p2 = f2.arena.add(TermNode::ProgDefFnParam {
            name: q_s,
            default: None,
        });
        let out2 = f2.run(p2, 100);
        assert_eq!(dget(&out2, "halted"), Value::Bool(false));
        assert_eq!(dget(&out2, "trap"), surf("param:q"));
    }

    #[test]
    fn structural_variants_are_inert_under_main_evaluate() {
        // Bare statement variants do NOT execute under evaluate().
        let mut f = Fixture::new();
        let x_s = f.sym("x");
        let one = f.lit(Value::Int(1));
        let assign = f.arena.add(TermNode::ProgAssignVar {
            name: x_s,
            value: one,
        });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&f.graph, &f.interner);
        assert_eq!(evaluate(&f.arena, assign, &mut env, &mut ctx), Value::None);
        // And nothing was bound anywhere: env untouched.
        assert!(env.is_empty());
    }

    #[test]
    fn snake_case_and_case_fold() {
        let mut f = Fixture::new();
        let t_sym__ = f.interner.intern("Total Cost (USD)");
        let t = f.lit(Value::Str(t_sym__));
        let sc = f.arena.add(TermNode::SnakeCase { text: t });
        let mut env: Env = SmallVec::new();
        let mut ctx = EvalCtx::new(&f.graph, &f.interner);
        assert_eq!(
            evaluate(&f.arena, sc, &mut env, &mut ctx),
            surf("total_cost_usd")
        );

        let t2_sym__ = f.interner.intern("camelCaseName");
        let t2 = f.lit(Value::Str(t2_sym__));
        let sc2 = f.arena.add(TermNode::SnakeCase { text: t2 });
        let mut ctx2 = EvalCtx::new(&f.graph, &f.interner);
        assert_eq!(
            evaluate(&f.arena, sc2, &mut env, &mut ctx2),
            surf("camel_case_name")
        );

        let t3_sym__ = f.interner.intern("MiXeD UP");
        let t3 = f.lit(Value::Str(t3_sym__));
        let cf = f.arena.add(TermNode::CaseFold { text: t3 });
        let mut ctx3 = EvalCtx::new(&f.graph, &f.interner);
        assert_eq!(
            evaluate(&f.arena, cf, &mut env, &mut ctx3),
            surf("mixed up")
        );

        // Non-string → honest None.
        let t4 = f.lit(Value::Int(3));
        let sc4 = f.arena.add(TermNode::SnakeCase { text: t4 });
        let mut ctx4 = EvalCtx::new(&f.graph, &f.interner);
        assert_eq!(evaluate(&f.arena, sc4, &mut env, &mut ctx4), Value::None);
    }

    #[test]
    fn prog_eval_from_reflected_subgraph() {
        // Materialise `x = 2; y = x + 3` as a Term subgraph, then run
        // ProgEval over the subgraph ROOT NODE (the EvalSubgraph form).
        let mut f = Fixture::new();
        let x_s = f.sym("x");
        let y_s = f.sym("y");
        let two = f.lit(Value::Int(2));
        let s0 = f.arena.add(TermNode::ProgAssignVar {
            name: x_s,
            value: two,
        });
        let xv = f.var("x");
        let three = f.lit(Value::Int(3));
        let plus = f.arena.add(TermNode::Plus {
            items: vec![xv, three],
        });
        let s1 = f.arena.add(TermNode::ProgAssignVar {
            name: y_s,
            value: plus,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, s1],
        });
        let root_nid =
            crate::reflect::term_to_subgraph(&f.arena, seq, &mut f.graph, &mut f.interner);
        let node_lit = f.lit(Value::Node(root_nid));
        let out = f.run(node_lit, 100);
        assert_eq!(dget(&out, "trap"), Value::None);
        assert_eq!(dget(&out, "halted"), Value::Bool(true));
        assert_eq!(env_var(&out, &f.interner, "y"), Value::Int(5));
    }

    #[test]
    fn short_circuit_protects_prog_subexpressions() {
        // y = (0 > 1) and d["missing"]  → False, NOT a key trap.
        let mut f = Fixture::new();
        let y_s = f.sym("y");
        let d_s = f.sym("d");
        let empty = f.arena.add(TermNode::ProgContainerLit {
            kind: f.interner.intern("dict"),
            items: vec![],
        });
        let s0 = f.arena.add(TermNode::ProgAssignVar {
            name: d_s,
            value: empty,
        });
        let zero = f.lit(Value::Int(0));
        let one = f.lit(Value::Int(1));
        let cmp = f.arena.add(TermNode::Gt { a: zero, b: one });
        let dv = f.var("d");
        let k_sym__ = f.interner.intern("missing");
        let k = f.lit(Value::Str(k_sym__));
        let sub = f.arena.add(TermNode::ProgSubscript { obj: dv, index: k });
        let and = f.arena.add(TermNode::And {
            items: vec![cmp, sub],
        });
        let s1 = f.arena.add(TermNode::ProgAssignVar {
            name: y_s,
            value: and,
        });
        let seq = f.arena.add(TermNode::ProgSeq {
            stmts: vec![s0, s1],
        });
        let out = f.run(seq, 100);
        assert_eq!(dget(&out, "trap"), Value::None);
        assert_eq!(env_var(&out, &f.interner, "y"), Value::Bool(false));
    }
}
