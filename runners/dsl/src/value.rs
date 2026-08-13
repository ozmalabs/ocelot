//! Runtime Value enum — what every `Term::evaluate` returns.
//!
//! Mirrors the Python DSL's value space: scalars (None / Bool / Int / Float
//! / Str), NodeID, and the collection types the DSL constructs
//! (Tuple from `Vec`, Set/FrozenSet from `Filter`/`SetT`/`Neighbours`,
//! Dict from attr maps / dict literals). Strings are stored as Sym so
//! `TypeOf(...) == Lit("AliveCell")` is a `Sym == Sym` u32 compare on the
//! hot path.
//!
//! The Surface variant carries rendered surfaces — text or bytes — for
//! the Cat/Join/Bytes/U*LE/Render Term family. This avoids the Python
//! version's "is it a dict with kind/payload or just a string?" runtime
//! branch in every render call.
//!
//! Equality and hashing are derived so frozenset/dict semantics work
//! naturally: a Set is a sorted-on-insert deduped list (the FrozenSet
//! evaluator wraps it). Ordering of contained values uses a stable
//! total order (`cmp_value`) so two equal frozensets hash to the same
//! bucket regardless of construction order.

use crate::sym::Sym;
use crate::graph::NodeID;
use smallvec::SmallVec;
use std::cmp::Ordering;
use std::sync::Arc;

/// Surface kind — text or raw bytes. Kept narrow so `Surface` doesn't
/// inflate the Value enum's size on the stack.
///
/// `PartialOrd`/`Ord` are derived (declaration order: `Text` < `Bytes`)
/// solely so `cmp_value`'s `(Surface, Surface)` arm can order the kind
/// tag before the payload. Two surfaces with identical bytes but
/// different kinds are `!=` under `PartialEq`, so they must not be
/// `Equal` under the total order either — see `cmp_value`.
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum SurfaceKind {
    Text,
    Bytes,
}

/// Runtime Value. Boxed collections (`Arc<[...]>`) so cloning a Value is
/// cheap — the substrate's evaluator clones Values constantly when
/// passing them through nested envs. Arc beats Vec because the same
/// frozenset is often shared across cache entries.
#[derive(Clone, Debug)]
pub enum Value {
    /// Python's None — also the default for missing attrs.
    None,
    Bool(bool),
    /// 64-bit signed; matches Python int's typical range, big-int is rare
    /// in substrate workloads and would force every Value to heap-allocate.
    Int(i64),
    Float(f64),
    /// Exact rational — the PROGRAM value domain's in-frame numeric type
    /// (PROGRAM_SYNTHESIS_ARC5_RATIONAL.md; CLAUDE.md's frame/continuum
    /// invariant: in-frame is integer/rational, never a float). INVARIANT,
    /// enforced by every constructor (`make_rational`/`rational_*`): the
    /// denominator is always > 0 and the fraction is always fully reduced
    /// (`gcd(|numerator|, denominator) == 1`) — a rational whose reduced
    /// denominator is 1 collapses to `Value::Int` instead (there is no
    /// second representation of a whole number). This means a genuine
    /// `Rational(n, d)` can never structurally equal an `Int`/`Bool` (a
    /// reduced fraction with `d > 1` is never a whole number) — `PartialEq`
    /// relies on this. Cross-frame comparison against a `Float` (the
    /// legitimate map boundary) still applies (see `PartialEq`/`cmp_value`).
    Rational(i64, i64),
    /// String values are interned; lookup goes through the substrate's
    /// interner. Lit("x") evaluated stays as Str(sym_of_x), which makes
    /// Eq comparisons u32 equality.
    Str(Sym),
    /// NodeID handle — what `Var("x")` typically evaluates to when bound
    /// to a Production pattern's src/tgt var.
    Node(NodeID),
    /// Heterogeneous tuple — output of `Vec(...)` and tuple-shaped attrs.
    Tuple(Arc<SmallVec<[Value; 4]>>),
    /// Python `list` — a SEQUENCE with the same payload as `Tuple` and
    /// the same accessors, kept as a separate tag for exactly the reason
    /// `Set`/`FrozenSet` are two tags: so the Python-side distinction
    /// survives the round trip. The difference from that precedent is
    /// that here EQUALITY DISTINGUISHES THEM, because Python's does
    /// (`[1,2] == (1,2)` is False) — see `PartialEq` below.
    ///
    /// PROGRAM_SYNTHESIS_ARC6_VALUELAYER.md. Produced at exactly three
    /// boundaries: `py.rs::py_to_value` (a `PyList`), `persist.rs`'s
    /// `__list__` tag, and `prog_eval.rs`'s list-typed operations
    /// (display `kind=="list"`, comprehensions, `sorted`, `list()`,
    /// `str.split`, and the kind-preserving slice/concat/repeat/
    /// item-assign paths). A BARE JSON array still decodes as `Tuple`
    /// so seed-resident `Lit` array literals are byte-unchanged.
    List(Arc<SmallVec<[Value; 4]>>),
    /// Hashable set, deduped on insert. Output of Filter / SetT /
    /// Neighbours. Stored as a sorted Arc<[Value]> so set equality and
    /// hashing are deterministic regardless of construction order.
    Set(Arc<[Value]>),
    /// Python frozenset equivalent — semantically the same as Set here,
    /// kept as a separate tag so persistence/round-trip preserve the
    /// Python-side distinction (Set => set, FrozenSet => frozenset).
    FrozenSet(Arc<[Value]>),
    /// Dict — Arc<[(Value, Value)]> sorted by key for deterministic
    /// iteration. Keys are arbitrary Values (matches Python's dict).
    Dict(Arc<[(Value, Value)]>),
    /// Rendered surface (Cat/Join/Bytes/U*LE family). Kind keeps text
    /// and bytes from accidentally concatenating without a type error.
    Surface(SurfaceKind, Arc<[u8]>),
}

impl Value {
    /// True iff `truthy` under Python rules: 0, 0.0, "", empty
    /// collections, None, False are falsy; everything else truthy.
    /// `IfThenElse` and `And`/`Or` use this on their condition values.
    pub fn truthy(&self) -> bool {
        match self {
            Value::None => false,
            Value::Bool(b) => *b,
            Value::Int(n) => *n != 0,
            Value::Float(f) => *f != 0.0 && !f.is_nan(),
            // Always-reduced: numerator 0 <=> the whole value is 0.
            Value::Rational(n, _) => *n != 0,
            Value::Str(s) => s.0 != 0, // Sym(0) is ""
            Value::Node(_) => true,
            Value::Tuple(t) | Value::List(t) => !t.is_empty(),
            Value::Set(s) | Value::FrozenSet(s) => !s.is_empty(),
            Value::Dict(d) => !d.is_empty(),
            Value::Surface(_, b) => !b.is_empty(),
        }
    }

    /// Numeric coercion to f64. Bool→0/1, Int→f64, Float passthrough;
    /// everything else returns 0.0 so the arithmetic Terms (Sum/Plus/
    /// Times/Min/Max) degrade silently the way Python does (matches
    /// `Sum` over a set containing a None — Python raises, we return 0.0
    /// to keep the dev loop unblocked — flagged TODO to align).
    pub fn as_f64(&self) -> f64 {
        match self {
            Value::None => 0.0,
            Value::Bool(b) => {
                if *b {
                    1.0
                } else {
                    0.0
                }
            }
            Value::Int(n) => *n as f64,
            Value::Float(f) => *f,
            // THE boundary: rendering an exact rational to a double is
            // exactly the cross-frame map CLAUDE.md's invariant names —
            // applied here, at the point a rational meets anything that
            // needs a float (comparison against a float-valued spec row,
            // a further float-typed computation, ...).
            Value::Rational(n, d) => *n as f64 / *d as f64,
            _ => 0.0,
        }
    }

    /// Integer coercion. Float→trunc, Rational→trunc-toward-zero (Rust's
    /// `/` on i64 already truncates toward zero, matching Python's
    /// `int(fraction)`/`int(float)`). Used by Pow/Mod/U*LE encoders.
    pub fn as_i64(&self) -> i64 {
        match self {
            Value::None => 0,
            Value::Bool(b) => {
                if *b {
                    1
                } else {
                    0
                }
            }
            Value::Int(n) => *n,
            Value::Float(f) => *f as i64,
            Value::Rational(n, d) => n / d,
            _ => 0,
        }
    }

    /// Iterate over a collection-shaped Value. Returns an iterator over
    /// borrowed Values for Tuple/Set/FrozenSet; empty for everything
    /// else (matches Python's `for x in non_iterable`-raises, but the
    /// substrate evaluator wants graceful no-ops).
    pub fn iter(&self) -> Box<dyn Iterator<Item = &Value> + '_> {
        match self {
            Value::Tuple(t) | Value::List(t) => Box::new(t.iter()),
            Value::Set(s) | Value::FrozenSet(s) => Box::new(s.iter()),
            _ => Box::new(std::iter::empty()),
        }
    }

    /// Snapshot a collection-shaped Value into a slice we own. For
    /// Set/FrozenSet this is a cheap `Arc<[Value]>` refcount bump; for
    /// Tuple it's an `Arc<[Value]>` constructed from the inline
    /// SmallVec; for non-collection variants it's an empty Arc.
    ///
    /// This exists so Sum / Prod / MinOver / MaxOver / Argmax / Argmin
    /// / Filter / Pick / etc. can walk their source without allocating
    /// a `Vec<Value>` materialisation just to release a borrow on `self`.
    /// The previous `let items: Vec<Value> = source_v.iter().cloned()
    /// .collect()` pattern was 1 alloc + N clones per call; snapshot is
    /// 1 refcount inc for Set/FrozenSet (the common case) and 1 alloc +
    /// N clones only for Tuple (rare in reductions).
    pub fn snapshot(&self) -> std::sync::Arc<[Value]> {
        match self {
            Value::Set(s) | Value::FrozenSet(s) => s.clone(),
            Value::Tuple(t) | Value::List(t) => t.iter().cloned().collect(),
            _ => std::sync::Arc::from([].as_slice()),
        }
    }

    /// Length of a collection. Used by Count.
    pub fn len(&self) -> usize {
        match self {
            Value::Tuple(t) | Value::List(t) => t.len(),
            Value::Set(s) | Value::FrozenSet(s) => s.len(),
            Value::Dict(d) => d.len(),
            Value::Surface(_, b) => b.len(),
            _ => 0,
        }
    }

    /// Membership test for `In(member, container)`. Linear over Set;
    /// equal-value matches via `PartialEq`.
    pub fn contains(&self, item: &Value) -> bool {
        match self {
            Value::Set(_) | Value::FrozenSet(_) | Value::Tuple(_) | Value::List(_) => {
                // SmallVec for Tuple, Arc<[]> for Sets — both expose .iter()
                // through Value::iter so the membership scan is uniform.
                self.iter().any(|x| x == item)
            }
            Value::Dict(d) => d.iter().any(|(k, _)| k == item),
            _ => false,
        }
    }

    /// Build a Set from a deduped, sorted-on-Ord-key Vec<Value>.
    /// Set equality is by element set, so canonicalising the storage
    /// order means PartialEq is just a slice compare.
    pub fn make_set(mut items: Vec<Value>) -> Value {
        items.sort_by(cmp_value);
        items.dedup_by(|a, b| cmp_value(a, b) == Ordering::Equal);
        Value::Set(items.into())
    }

    /// Same as `make_set` but tagged FrozenSet — preserves the Python
    /// distinction across persistence.
    pub fn make_frozenset(mut items: Vec<Value>) -> Value {
        items.sort_by(cmp_value);
        items.dedup_by(|a, b| cmp_value(a, b) == Ordering::Equal);
        Value::FrozenSet(items.into())
    }
}

impl Value {
    pub fn is_empty(&self) -> bool {
        self.len() == 0
    }

    /// Rebuild a sequence with the SAME container kind as `self`.
    ///
    /// THE INVARIANT THIS EXISTS FOR (ARC6, and it was a real bug before it
    /// did): a helper that COPIES a sequence with one slot changed must not
    /// silently retype it. `shape_decode::set_coord` destructured
    /// `Tuple | List` and always emitted a `Tuple`, so every geometry
    /// generator (translate / rotate / reflect / scale / modular, all of
    /// which funnel through it) produced tuples while the OBSERVED frames
    /// were lists — `frames_equal` then never matched, `BlinkBridge`
    /// reported `freeze` instead of the inferred generator, and 9 vision
    /// gates went red. Read-modify-write on a sequence goes through here.
    pub fn reseq(&self, items: SmallVec<[Value; 4]>) -> Value {
        match self {
            Value::List(_) => Value::List(Arc::new(items)),
            _ => Value::Tuple(Arc::new(items)),
        }
    }
}

impl PartialEq for Value {
    fn eq(&self, other: &Value) -> bool {
        match (self, other) {
            (Value::None, Value::None) => true,
            (Value::Bool(a), Value::Bool(b)) => a == b,
            (Value::Int(a), Value::Int(b)) => a == b,
            (Value::Float(a), Value::Float(b)) => a == b,
            // Bool/Int coerce in Python's == ; mirror that for Term-eval
            // (Eq(Lit(true), Lit(1)) should be True the way Python sees it).
            (Value::Bool(a), Value::Int(b)) | (Value::Int(b), Value::Bool(a)) => {
                (if *a { 1 } else { 0 }) == *b
            }
            (Value::Int(a), Value::Float(b)) | (Value::Float(b), Value::Int(a)) => (*a as f64) == *b,
            (Value::Rational(n1, d1), Value::Rational(n2, d2)) => n1 == n2 && d1 == d2,
            // Cross-frame boundary: a Rational compared against a Float
            // renders to f64 (the map), exactly like Int<->Float above.
            // NOTE: a genuine (always-reduced, d>1) Rational can never
            // structurally equal an Int/Bool — that would mean a reduced
            // fraction with denominator > 1 is a whole number — so no
            // Rational<->Int/Bool arm is needed; `_ => false` is exact,
            // not an approximation.
            (Value::Rational(n, d), Value::Float(f)) | (Value::Float(f), Value::Rational(n, d)) => {
                (*n as f64 / *d as f64) == *f
            }
            (Value::Str(a), Value::Str(b)) => a == b,
            (Value::Node(a), Value::Node(b)) => a == b,
            (Value::Tuple(a), Value::Tuple(b)) => a.as_slice() == b.as_slice(),
            // THE FIX (ARC6 value layer): a List equals a List elementwise,
            // and NEVER equals a Tuple — there is deliberately no cross-tag
            // arm here, so `_ => false` below decides it, exactly as Python
            // decides `[1,2] == (1,2)`. Contrast Set/FrozenSet directly
            // above, which DO cross-compare because Python's do.
            (Value::List(a), Value::List(b)) => a.as_slice() == b.as_slice(),
            // Set == FrozenSet across the tag boundary so Python-side
            // round-trips don't surprise the caller.
            (Value::Set(a), Value::Set(b))
            | (Value::FrozenSet(a), Value::FrozenSet(b))
            | (Value::Set(a), Value::FrozenSet(b))
            | (Value::FrozenSet(a), Value::Set(b)) => a.as_ref() == b.as_ref(),
            (Value::Dict(a), Value::Dict(b)) => a.as_ref() == b.as_ref(),
            (Value::Surface(ka, ba), Value::Surface(kb, bb)) => ka == kb && ba == bb,
            _ => false,
        }
    }
}

impl Eq for Value {}

/// Total order over Values so Set/FrozenSet can canonicalise insertion
/// order. Mixed-type compares fall back to a stable tag order so the
/// sort is total even when Python would error.
pub fn cmp_value(a: &Value, b: &Value) -> Ordering {
    fn tag(v: &Value) -> u8 {
        match v {
            Value::None => 0,
            Value::Bool(_) => 1,
            Value::Int(_) => 2,
            Value::Float(_) => 3,
            Value::Str(_) => 4,
            Value::Node(_) => 5,
            Value::Tuple(_) => 6,
            Value::Set(_) => 7,
            Value::FrozenSet(_) => 8,
            Value::Dict(_) => 9,
            Value::Surface(_, _) => 10,
            Value::Rational(_, _) => 11,
            // APPENDED, never renumbered: renumbering would change the
            // canonical order of every existing mixed-type Set.
            Value::List(_) => 12,
        }
    }
    match (a, b) {
        (Value::Int(x), Value::Int(y)) => x.cmp(y),
        (Value::Float(x), Value::Float(y)) => x.partial_cmp(y).unwrap_or(Ordering::Equal),
        // Mixed numerics compare by VALUE, not by type tag — otherwise a Float
        // would always sort above any Int (tag 3 > tag 2), so Gte(0.0, 3) wrongly
        // returns true. Attrs are often Float while seed literals are Int.
        (Value::Int(x), Value::Float(y)) => (*x as f64).partial_cmp(y).unwrap_or(Ordering::Equal),
        (Value::Float(x), Value::Int(y)) => x.partial_cmp(&(*y as f64)).unwrap_or(Ordering::Equal),
        // Rational vs Int/Rational: EXACT cross-multiplication (i128 —
        // both denominators positive so sign is preserved), never a
        // lossy float compare — strictly better than the Int/Float
        // case above, made possible because both sides are exact here.
        (Value::Rational(n1, d1), Value::Rational(n2, d2)) => {
            (*n1 as i128 * *d2 as i128).cmp(&(*n2 as i128 * *d1 as i128))
        }
        (Value::Rational(n, d), Value::Int(y)) => (*n as i128).cmp(&(*y as i128 * *d as i128)),
        (Value::Int(x), Value::Rational(n, d)) => (*x as i128 * *d as i128).cmp(&(*n as i128)),
        // Rational vs Float: the cross-frame boundary — render to f64.
        (Value::Rational(n, d), Value::Float(y)) => {
            (*n as f64 / *d as f64).partial_cmp(y).unwrap_or(Ordering::Equal)
        }
        (Value::Float(x), Value::Rational(n, d)) => {
            x.partial_cmp(&(*n as f64 / *d as f64)).unwrap_or(Ordering::Equal)
        }
        (Value::Str(x), Value::Str(y)) => x.0.cmp(&y.0),
        (Value::Node(x), Value::Node(y)) => x.cmp(y),
        (Value::Bool(x), Value::Bool(y)) => x.cmp(y),
        // Recurse into collections so two distinct tuples/sets don't
        // compare Equal under their shared tag — that would collapse
        // them when a set deduplicates.
        // LOAD-BEARING: without the List arm two distinct lists would fall
        // through to the tag compare and read Equal, which silently makes
        // `sorted` a no-op over a list of lists and collapses a Set of
        // lists to one element.
        (Value::Tuple(xa), Value::Tuple(ya)) | (Value::List(xa), Value::List(ya)) => {
            xa.len().cmp(&ya.len()).then_with(|| {
                for (x, y) in xa.iter().zip(ya.iter()) {
                    let c = cmp_value(x, y);
                    if c != Ordering::Equal {
                        return c;
                    }
                }
                Ordering::Equal
            })
        }
        (Value::Set(xa), Value::Set(ya))
        | (Value::FrozenSet(xa), Value::FrozenSet(ya))
        | (Value::Set(xa), Value::FrozenSet(ya))
        | (Value::FrozenSet(xa), Value::Set(ya)) => {
            xa.len().cmp(&ya.len()).then_with(|| {
                for (x, y) in xa.iter().zip(ya.iter()) {
                    let c = cmp_value(x, y);
                    if c != Ordering::Equal {
                        return c;
                    }
                }
                Ordering::Equal
            })
        }
        // LOAD-BEARING, and it was a real, measured data-loss bug before it
        // existed (RULE_SIGNATURE_TO_RUST_RESULTS.md §5.1 named it;
        // CMP_VALUE_SURFACE_FIX_RESULTS.md fixed it). Without this arm two
        // `Surface` values fall through to `_ => tag(a).cmp(&tag(b))` — 10
        // vs 10 — and read `Equal`, so EVERY RUNTIME-BUILT STRING COMPARES
        // EQUAL TO EVERY OTHER. `PartialEq` and `Hash` both get it right
        // (kind + payload, see above), so this was an Ord/Eq INCONSISTENCY,
        // not a missing feature: `make_set`/`make_frozenset` dedup by
        // `cmp_value(a,b) == Equal`, `Value::Dict` is a cmp-sorted pair vec
        // and `prog_eval`'s dict item-assign hits the first slot whose key
        // compares Equal — so a set of computed strings collapsed to ONE
        // element and `d[computed] = v` overwrote an unrelated key.
        // Measured before the fix: `{"a"+str(i) for i in range(3)}` →
        // `{'a0'}`; `d["a"+str(i)] = i` → `{'a0': 2}`.
        //
        // Kind first, then payload bytes: a Text and a Bytes surface with
        // identical payloads are `!=` under `PartialEq`, so they must not
        // be `Equal` here either. `[u8]`'s own `Ord` is lexicographic, so
        // for `SurfaceKind::Text` this IS byte-lexicographic string order —
        // note that `(Str, Str)` next door is NOT (it compares interner
        // symbol IDs), which is a separate, still-open defect.
        (Value::Surface(ka, ba), Value::Surface(kb, bb)) => {
            ka.cmp(kb).then_with(|| ba.as_ref().cmp(bb.as_ref()))
        }
        (Value::Dict(xa), Value::Dict(ya)) => {
            xa.len().cmp(&ya.len()).then_with(|| {
                for ((kx, vx), (ky, vy)) in xa.iter().zip(ya.iter()) {
                    let c = cmp_value(kx, ky).then_with(|| cmp_value(vx, vy));
                    if c != Ordering::Equal {
                        return c;
                    }
                }
                Ordering::Equal
            })
        }
        _ => tag(a).cmp(&tag(b)),
    }
}

/// Interner-aware companion to `cmp_value`, for REPORTED-ORDER call sites
/// only — `sorted`/`min`/`max`, `Lt`/`Gt`/`Lte`/`Gte`, and the native
/// `ArgMin`/`ArgMax`/`MinOver`/`MaxOver`/`ArgminOver`/`ArgmaxOver` selector
/// family (see `CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md`). `cmp_value`
/// itself is UNCHANGED — this is a SEPARATE function, not a signature
/// change, so every canonicalisation-only call site (Set/Dict construction,
/// persistence, `shape_decode`'s frame correspondence) keeps its existing,
/// boot-order-consistent behaviour byte-for-byte.
///
/// Structurally mirrors `cmp_value`'s match arm-for-arm — recursing into
/// Tuple/List/Set/FrozenSet/Dict via ITSELF, not `cmp_value`, so a nested
/// string (e.g. inside a tuple being sorted) also compares lexicographically
/// rather than only the top-level case. The ONLY behavioural difference from
/// `cmp_value` is `(Str, Str)`: instead of comparing the two `Sym`s' raw
/// `u32` ids (boot-history order — whichever string got interned first
/// sorts first), it resolves both through `interner` and compares the
/// underlying `&str` — real byte-lexicographic order, matching Rust's (and
/// Python's) default string `Ord`.
pub fn cmp_value_lex(a: &Value, b: &Value, interner: &crate::sym::Interner) -> Ordering {
    fn tag(v: &Value) -> u8 {
        match v {
            Value::None => 0,
            Value::Bool(_) => 1,
            Value::Int(_) => 2,
            Value::Float(_) => 3,
            Value::Str(_) => 4,
            Value::Node(_) => 5,
            Value::Tuple(_) => 6,
            Value::Set(_) => 7,
            Value::FrozenSet(_) => 8,
            Value::Dict(_) => 9,
            Value::Surface(_, _) => 10,
            Value::Rational(_, _) => 11,
            Value::List(_) => 12,
        }
    }
    match (a, b) {
        (Value::Int(x), Value::Int(y)) => x.cmp(y),
        (Value::Float(x), Value::Float(y)) => x.partial_cmp(y).unwrap_or(Ordering::Equal),
        (Value::Int(x), Value::Float(y)) => (*x as f64).partial_cmp(y).unwrap_or(Ordering::Equal),
        (Value::Float(x), Value::Int(y)) => x.partial_cmp(&(*y as f64)).unwrap_or(Ordering::Equal),
        (Value::Rational(n1, d1), Value::Rational(n2, d2)) => {
            (*n1 as i128 * *d2 as i128).cmp(&(*n2 as i128 * *d1 as i128))
        }
        (Value::Rational(n, d), Value::Int(y)) => (*n as i128).cmp(&(*y as i128 * *d as i128)),
        (Value::Int(x), Value::Rational(n, d)) => (*x as i128 * *d as i128).cmp(&(*n as i128)),
        (Value::Rational(n, d), Value::Float(y)) => {
            (*n as f64 / *d as f64).partial_cmp(y).unwrap_or(Ordering::Equal)
        }
        (Value::Float(x), Value::Rational(n, d)) => {
            x.partial_cmp(&(*n as f64 / *d as f64)).unwrap_or(Ordering::Equal)
        }
        // THE FIX: resolve both Syms through the interner and compare the
        // underlying bytes, instead of `cmp_value`'s `x.0.cmp(&y.0)` (Sym-id
        // / boot-order compare).
        (Value::Str(x), Value::Str(y)) => interner.resolve(*x).cmp(interner.resolve(*y)),
        (Value::Node(x), Value::Node(y)) => x.cmp(y),
        (Value::Bool(x), Value::Bool(y)) => x.cmp(y),
        (Value::Tuple(xa), Value::Tuple(ya)) | (Value::List(xa), Value::List(ya)) => {
            xa.len().cmp(&ya.len()).then_with(|| {
                for (x, y) in xa.iter().zip(ya.iter()) {
                    let c = cmp_value_lex(x, y, interner);
                    if c != Ordering::Equal {
                        return c;
                    }
                }
                Ordering::Equal
            })
        }
        (Value::Set(xa), Value::Set(ya))
        | (Value::FrozenSet(xa), Value::FrozenSet(ya))
        | (Value::Set(xa), Value::FrozenSet(ya))
        | (Value::FrozenSet(xa), Value::Set(ya)) => {
            xa.len().cmp(&ya.len()).then_with(|| {
                for (x, y) in xa.iter().zip(ya.iter()) {
                    let c = cmp_value_lex(x, y, interner);
                    if c != Ordering::Equal {
                        return c;
                    }
                }
                Ordering::Equal
            })
        }
        (Value::Surface(ka, ba), Value::Surface(kb, bb)) => {
            ka.cmp(kb).then_with(|| ba.as_ref().cmp(bb.as_ref()))
        }
        (Value::Dict(xa), Value::Dict(ya)) => {
            xa.len().cmp(&ya.len()).then_with(|| {
                for ((kx, vx), (ky, vy)) in xa.iter().zip(ya.iter()) {
                    let c = cmp_value_lex(kx, ky, interner)
                        .then_with(|| cmp_value_lex(vx, vy, interner));
                    if c != Ordering::Equal {
                        return c;
                    }
                }
                Ordering::Equal
            })
        }
        _ => tag(a).cmp(&tag(b)),
    }
}

// Hash by element-tag + payload. Two equal Values hash to the same
// bucket because PartialEq is by canonical contents.
impl std::hash::Hash for Value {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        match self {
            Value::None => 0u8.hash(state),
            Value::Bool(b) => {
                1u8.hash(state);
                b.hash(state);
            }
            Value::Int(n) => {
                2u8.hash(state);
                n.hash(state);
            }
            Value::Float(f) => {
                3u8.hash(state);
                f.to_bits().hash(state);
            }
            Value::Str(s) => {
                4u8.hash(state);
                s.hash(state);
            }
            Value::Node(n) => {
                5u8.hash(state);
                n.hash(state);
            }
            Value::Tuple(t) => {
                6u8.hash(state);
                t.len().hash(state);
                for v in t.iter() {
                    v.hash(state);
                }
            }
            // Set and FrozenSet hash identically so the cross-tag PartialEq
            // arm doesn't break the hash invariant.
            Value::Set(s) | Value::FrozenSet(s) => {
                7u8.hash(state);
                s.len().hash(state);
                for v in s.iter() {
                    v.hash(state);
                }
            }
            Value::Dict(d) => {
                9u8.hash(state);
                d.len().hash(state);
                for (k, v) in d.iter() {
                    k.hash(state);
                    v.hash(state);
                }
            }
            Value::Surface(k, b) => {
                10u8.hash(state);
                k.hash(state);
                b.hash(state);
            }
            // Structural hash over the always-reduced (n, d) pair —
            // consistent with Rational's own PartialEq arm. Like the
            // pre-existing Int/Float cross-equality (tag 2 vs tag 3
            // hash differently despite `Int(1) == Float(1.0)`), the
            // Rational<->Float cross-equality arm above has the SAME
            // latent Hash/Eq inconsistency; not a new class of wart.
            Value::Rational(n, d) => {
                11u8.hash(state);
                n.hash(state);
                d.hash(state);
            }
            // Distinct tag byte from Tuple's 6 — required by Hash/Eq
            // consistency now that List != Tuple.
            Value::List(t) => {
                12u8.hash(state);
                t.len().hash(state);
                for v in t.iter() {
                    v.hash(state);
                }
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Exact rational arithmetic — PROGRAM_SYNTHESIS_ARC5_RATIONAL.md. Every
// entry point here is used BOTH by the shared DSL arithmetic Terms
// (`numeric_variadic`/`numeric_binary`/`Pow`/`Neg`/`Abs` in term.rs — safe
// by construction: Rational never appeared before this feature, so these
// arms are purely additive and byte-identical for every pre-existing
// Int/Float/Bool combination) AND by `ProgEval`'s local exact-division/
// exact-power interception (`prog_eval.rs`).
//
// Overflow policy (CLAUDE.md-consistent: "a bounded denominator with an
// explicit trap on overflow, never silent wrap"): every combinator here
// computes in i128 (ample headroom over i64 for a single cross-multiply)
// and returns `None` if the REDUCED result doesn't fit back in i64. The
// two call sites differ in what they do with `None`:
//   - term.rs's shared, non-fallible `evaluate()` has no trap channel —
//     it degrades to `Value::Float` (still HONEST — a real, if imprecise,
//     value — never a silent wrap/truncation).
//   - `ProgEval` has a trap channel (`Flow::Trap`) and uses it explicitly
//     ("arith:overflow") once it has committed to the exact path.
fn gcd_i128(a: i128, b: i128) -> i128 {
    let (mut a, mut b) = (a.unsigned_abs(), b.unsigned_abs());
    while b != 0 {
        let t = b;
        b = a % b;
        a = t;
    }
    a as i128
}

/// Build a normalised `Value` from an i128 numerator/denominator (the
/// common tail of every rational combinator below): reduce by gcd, move
/// the sign onto the numerator, collapse to `Value::Int` when the
/// reduced denominator is 1. `None` on a zero denominator or on overflow
/// (the reduced numerator/denominator don't fit back in i64).
fn make_rational_i128(mut n: i128, mut d: i128) -> Option<Value> {
    if d == 0 {
        return None;
    }
    if d < 0 {
        n = -n;
        d = -d;
    }
    let g = gcd_i128(n, d).max(1);
    n /= g;
    d /= g;
    let n64 = i64::try_from(n).ok()?;
    let d64 = i64::try_from(d).ok()?;
    if d64 == 1 {
        Some(Value::Int(n64))
    } else {
        Some(Value::Rational(n64, d64))
    }
}

/// Build a normalised rational Value from i64 numerator/denominator —
/// the public entry point for a fresh (n, d) pair (e.g. a `Lit` decoded
/// off the wire). `None` on a zero denominator.
pub fn make_rational(n: i64, d: i64) -> Option<Value> {
    make_rational_i128(n as i128, d as i128)
}

/// Extract an (numerator, denominator) pair from any EXACT numeric
/// Value (Int/Bool/Rational — never Float, which is the whole point:
/// callers use this to detect "can this arithmetic stay exact?").
pub fn rational_parts(v: &Value) -> Option<(i64, i64)> {
    match v {
        Value::Int(n) => Some((*n, 1)),
        Value::Bool(b) => Some((if *b { 1 } else { 0 }, 1)),
        Value::Rational(n, d) => Some((*n, *d)),
        _ => None,
    }
}

pub fn rational_add((n1, d1): (i64, i64), (n2, d2): (i64, i64)) -> Option<Value> {
    let (n1, d1, n2, d2) = (n1 as i128, d1 as i128, n2 as i128, d2 as i128);
    make_rational_i128(n1 * d2 + n2 * d1, d1 * d2)
}

pub fn rational_sub((n1, d1): (i64, i64), (n2, d2): (i64, i64)) -> Option<Value> {
    let (n1, d1, n2, d2) = (n1 as i128, d1 as i128, n2 as i128, d2 as i128);
    make_rational_i128(n1 * d2 - n2 * d1, d1 * d2)
}

pub fn rational_mul((n1, d1): (i64, i64), (n2, d2): (i64, i64)) -> Option<Value> {
    let (n1, d1, n2, d2) = (n1 as i128, d1 as i128, n2 as i128, d2 as i128);
    make_rational_i128(n1 * n2, d1 * d2)
}

/// `None` also on division by zero (numerator of the divisor is 0) —
/// callers distinguish "not applicable" (zero divisor / a Float is
/// present) from genuine overflow themselves; `rational_parts` +
/// an explicit `pb.0 != 0` guard at the call site is the documented
/// discipline (mirrors the existing Div-by-zero-is-not-a-trap
/// convention: this function alone can't tell the two `None` causes
/// apart, so callers check zero BEFORE calling it).
pub fn rational_div((n1, d1): (i64, i64), (n2, d2): (i64, i64)) -> Option<Value> {
    if n2 == 0 {
        return None;
    }
    let (n1, d1, n2, d2) = (n1 as i128, d1 as i128, n2 as i128, d2 as i128);
    make_rational_i128(n1 * d2, d1 * n2)
}

/// Exact `(n/d) ** exp` for an INTEGER exponent (the only case that can
/// stay in-frame — a non-integer exponent is cross-frame by the
/// CLAUDE.md invariant and correctly stays float). `exp == 0` is `1`
/// regardless of base (Python convention, including `0 ** 0 == 1`).
/// A negative exponent inverts the base first; `None` if the base is
/// zero (no reciprocal) or the exponent magnitude is absurd (bounds the
/// loop, real overflow is caught by `make_rational_i128` regardless).
pub fn rational_pow_int((n, d): (i64, i64), exp: i64) -> Option<Value> {
    if exp == 0 {
        return Some(Value::Int(1));
    }
    if n == 0 && exp < 0 {
        return None;
    }
    if exp.unsigned_abs() > 63 {
        return None;
    }
    let (base_n, base_d): (i128, i128) = if exp < 0 { (d as i128, n as i128) } else { (n as i128, d as i128) };
    let e = exp.unsigned_abs() as u32;
    let mut num: i128 = 1;
    let mut den: i128 = 1;
    for _ in 0..e {
        num = num.checked_mul(base_n)?;
        den = den.checked_mul(base_d)?;
    }
    make_rational_i128(num, den)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bool_int_compare_equal() {
        assert_eq!(Value::Bool(true), Value::Int(1));
        assert_eq!(Value::Int(0), Value::Bool(false));
    }

    #[test]
    fn set_dedupes_and_sorts() {
        let s = Value::make_set(vec![Value::Int(3), Value::Int(1), Value::Int(2), Value::Int(1)]);
        let Value::Set(items) = &s else {
            panic!("expected Set")
        };
        assert_eq!(items.len(), 3);
        assert_eq!(items[0], Value::Int(1));
        assert_eq!(items[2], Value::Int(3));
    }

    #[test]
    fn set_frozenset_equal_across_tags() {
        let a = Value::make_set(vec![Value::Int(1), Value::Int(2)]);
        let b = Value::make_frozenset(vec![Value::Int(1), Value::Int(2)]);
        assert_eq!(a, b);
    }

    #[test]
    fn truthy_matches_python() {
        assert!(!Value::None.truthy());
        assert!(!Value::Int(0).truthy());
        assert!(Value::Int(1).truthy());
        assert!(!Value::make_set(vec![]).truthy());
        assert!(Value::make_set(vec![Value::Int(0)]).truthy());
    }

    #[test]
    fn count_matches_python() {
        let s = Value::make_set(vec![Value::Int(1), Value::Int(2)]);
        assert_eq!(s.len(), 2);
        assert_eq!(Value::None.len(), 0);
    }

    #[test]
    fn make_rational_reduces_and_collapses() {
        assert_eq!(make_rational(4, 6), Some(Value::Rational(2, 3)));
        assert_eq!(make_rational(6, 3), Some(Value::Int(2)));
        assert_eq!(make_rational(3, -6), Some(Value::Rational(-1, 2)));
        assert_eq!(make_rational(0, 5), Some(Value::Int(0)));
        assert_eq!(make_rational(1, 0), None);
    }

    #[test]
    fn rational_add_is_exact_where_float_is_not() {
        // The textbook float trap: 0.1 + 0.2 != 0.3 in IEEE-754.
        assert_ne!(0.1_f64 + 0.2_f64, 0.3_f64);
        // The exact rational form has no such trap: 1/3+1/3+1/3 == 1.
        let third = rational_parts(&Value::Rational(1, 3)).unwrap();
        let mut acc = rational_add(third, third).unwrap();
        acc = rational_add(rational_parts(&acc).unwrap(), third).unwrap();
        assert_eq!(acc, Value::Int(1));
    }

    #[test]
    fn rational_sub_mul_div_exact() {
        assert_eq!(rational_sub((1, 2), (1, 3)), Some(Value::Rational(1, 6)));
        assert_eq!(rational_mul((2, 3), (3, 4)), Some(Value::Rational(1, 2)));
        assert_eq!(rational_div((1, 2), (1, 4)), Some(Value::Int(2)));
        // Division by zero is "not applicable" (None) — callers guard
        // on the numerator before calling, never silently.
        assert_eq!(rational_div((1, 2), (0, 5)), None);
    }

    #[test]
    fn rational_pow_int_exact() {
        assert_eq!(rational_pow_int((1, 2), 2), Some(Value::Rational(1, 4)));
        assert_eq!(rational_pow_int((4, 3), 0), Some(Value::Int(1)));
        assert_eq!(rational_pow_int((2, 1), -1), Some(Value::Rational(1, 2)));
        assert_eq!(rational_pow_int((0, 1), -1), None);
    }

    #[test]
    fn rational_overflow_is_none_not_silent_wrap() {
        // i64::MAX * i64::MAX overflows even i128's headroom for the
        // FINAL reduced value here (denominator product blows past
        // i64::MAX), so this must report None, never wrap/truncate.
        let huge = i64::MAX;
        assert_eq!(rational_mul((huge, 1), (huge, 1)), None);
    }

    #[test]
    fn rational_cross_frame_equals_float_by_value() {
        assert_eq!(Value::Rational(1, 2), Value::Float(0.5));
        assert_eq!(Value::Float(0.5), Value::Rational(1, 2));
        assert_ne!(Value::Rational(1, 3), Value::Float(0.333));
    }

    #[test]
    fn rational_never_structurally_equals_int_or_bool() {
        // A reduced fraction with denominator > 1 is never a whole
        // number — no `_ => false` lossiness, this is exact.
        assert_ne!(Value::Rational(1, 3), Value::Int(0));
        assert_ne!(Value::Rational(1, 3), Value::Int(1));
        assert_ne!(Value::Rational(2, 3), Value::Bool(true));
    }

    // --- ARC6 value layer: list vs tuple ---------------------------------
    fn seq(items: Vec<Value>) -> Arc<SmallVec<[Value; 4]>> {
        Arc::new(SmallVec::from_vec(items))
    }

    #[test]
    fn list_never_equals_tuple_with_the_same_elements() {
        let l = Value::List(seq(vec![Value::Int(1), Value::Int(2)]));
        let t = Value::Tuple(seq(vec![Value::Int(1), Value::Int(2)]));
        assert_ne!(l, t);
        assert_ne!(t, l);
        // ... and a list still equals an equal list.
        assert_eq!(l, Value::List(seq(vec![Value::Int(1), Value::Int(2)])));
        assert_ne!(l, Value::List(seq(vec![Value::Int(1), Value::Int(3)])));
    }

    #[test]
    fn list_is_a_sequence_for_every_shared_accessor() {
        let l = Value::List(seq(vec![Value::Int(7), Value::Int(8)]));
        assert_eq!(l.len(), 2);
        assert!(l.truthy());
        assert!(!Value::List(seq(vec![])).truthy());
        assert!(l.contains(&Value::Int(8)));
        assert!(!l.contains(&Value::Int(9)));
        assert_eq!(l.iter().count(), 2);
        assert_eq!(l.snapshot().len(), 2);
    }

    #[test]
    fn cmp_value_recurses_into_lists_so_sort_and_set_still_work() {
        use std::cmp::Ordering;
        let a = Value::List(seq(vec![Value::Int(1)]));
        let b = Value::List(seq(vec![Value::Int(2)]));
        // NOT Equal -- the tag fallback would have made it Equal, which
        // silently turns `sorted` into a no-op and collapses Sets.
        assert_eq!(cmp_value(&a, &b), Ordering::Less);
        let s = Value::make_set(vec![a.clone(), b.clone(), a.clone()]);
        assert_eq!(s.len(), 2);
    }

    #[test]
    fn list_and_tuple_hash_differently() {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let h = |v: &Value| {
            let mut st = DefaultHasher::new();
            v.hash(&mut st);
            st.finish()
        };
        let l = Value::List(seq(vec![Value::Int(1)]));
        let t = Value::Tuple(seq(vec![Value::Int(1)]));
        assert_ne!(h(&l), h(&t));
    }

    #[test]
    fn rational_cmp_is_exact_cross_multiplication() {
        use std::cmp::Ordering;
        assert_eq!(cmp_value(&Value::Rational(1, 3), &Value::Rational(1, 2)), Ordering::Less);
        assert_eq!(cmp_value(&Value::Rational(2, 1), &Value::Int(2)), Ordering::Equal);
        assert_eq!(cmp_value(&Value::Int(1), &Value::Rational(1, 2)), Ordering::Greater);
    }

    // ---------------------------------------------------------------
    // (Surface, Surface) — CMP_VALUE_SURFACE_FIX_RESULTS.md AR3.
    // Every one of these was RED before the arm existed: `cmp_value`
    // read `Equal` for any two Surfaces, so a set of runtime-built
    // strings collapsed to one element.
    // ---------------------------------------------------------------
    fn text(s: &str) -> Value {
        Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes().to_vec()))
    }
    fn bytes(s: &[u8]) -> Value {
        Value::Surface(SurfaceKind::Bytes, Arc::from(s.to_vec()))
    }

    #[test]
    fn cmp_value_distinguishes_two_computed_surfaces() {
        use std::cmp::Ordering;
        // THE HEADLINE: this read `Equal` before the arm existed.
        assert_eq!(cmp_value(&text("a0"), &text("a1")), Ordering::Less);
        assert_eq!(cmp_value(&text("a1"), &text("a0")), Ordering::Greater);
        assert_eq!(cmp_value(&text("a0"), &text("a0")), Ordering::Equal);
    }

    #[test]
    fn surface_set_does_not_collapse() {
        // `{f"a{i}" for i in range(3)}` -> ONE element before the fix.
        let s = Value::make_set(vec![text("a0"), text("a1"), text("a2")]);
        assert_eq!(s.len(), 3);
        let f = Value::make_frozenset(vec![text("a0"), text("a1"), text("a2"), text("a0")]);
        assert_eq!(f.len(), 3, "a genuine duplicate must still dedup");
    }

    #[test]
    fn surface_set_of_tuples_does_not_collapse() {
        // Nesting did not save you before the fix: the Tuple arm recurses
        // straight back into the missing Surface arm.
        let mk = |i: &str| Value::Tuple(seq(vec![Value::Str(Sym(1)), text(i)]));
        let s = Value::make_set(vec![mk("a0"), mk("a1"), mk("a2")]);
        assert_eq!(s.len(), 3);
    }

    #[test]
    fn surface_ord_agrees_with_eq_in_both_directions() {
        use std::cmp::Ordering;
        // THE CONTRACT the missing arm broke: Ord and Eq must agree.
        let vals = [text(""), text("a"), text("a0"), text("a1"), text("b"),
                    bytes(b""), bytes(b"a"), bytes(b"a0")];
        for a in vals.iter() {
            for b in vals.iter() {
                assert_eq!(
                    cmp_value(a, b) == Ordering::Equal,
                    a == b,
                    "Ord/Eq disagree for {:?} vs {:?}", a, b);
            }
        }
    }

    #[test]
    fn surface_ord_is_antisymmetric_and_total() {
        let vals = [text(""), text("a"), text("a0"), text("ab"), bytes(b"a"), bytes(b"b")];
        for a in vals.iter() {
            for b in vals.iter() {
                assert_eq!(cmp_value(a, b), cmp_value(b, a).reverse(),
                           "antisymmetry broken for {:?} vs {:?}", a, b);
            }
        }
    }

    #[test]
    fn surface_ord_is_transitive_on_a_ladder() {
        use std::cmp::Ordering;
        let (a, b, c) = (text("a"), text("b"), text("c"));
        assert_eq!(cmp_value(&a, &b), Ordering::Less);
        assert_eq!(cmp_value(&b, &c), Ordering::Less);
        assert_eq!(cmp_value(&a, &c), Ordering::Less);
    }

    #[test]
    fn surface_kind_is_part_of_the_order() {
        use std::cmp::Ordering;
        // Same payload, different kind: `!=` under PartialEq, so it must
        // not be `Equal` under the total order either.
        assert_ne!(text("ab"), bytes(b"ab"));
        assert_ne!(cmp_value(&text("ab"), &bytes(b"ab")), Ordering::Equal);
        // Text sorts before Bytes (declaration order), and the kind tag
        // dominates the payload.
        assert_eq!(cmp_value(&text("zz"), &bytes(b"aa")), Ordering::Less);
        let s = Value::make_set(vec![text("ab"), bytes(b"ab")]);
        assert_eq!(s.len(), 2);
    }

    #[test]
    fn surface_text_order_is_byte_lexicographic() {
        use std::cmp::Ordering;
        // The half of §5.2 this fix DOES deliver: Surface(Text) compares
        // by payload bytes, so it is genuinely lexicographic. `(Str, Str)`
        // next door still compares interner symbol IDs — separate defect,
        // deliberately untouched here.
        let mut v = vec![text("where"), text("source"), text("var_name"),
                         text("a_zzz"), text("b")];
        v.sort_by(cmp_value);
        let rendered: Vec<String> = v
            .iter()
            .map(|x| match x {
                Value::Surface(_, b) => String::from_utf8_lossy(b).into_owned(),
                _ => unreachable!(),
            })
            .collect();
        assert_eq!(rendered, vec!["a_zzz", "b", "source", "var_name", "where"]);
        assert_eq!(cmp_value(&text("a"), &text("ab")), Ordering::Less,
                   "prefix sorts before its extension, as CPython does");
    }

    // --- cmp_value_lex: the (Str,Str) follow-on
    // (CMP_VALUE_LEXICOGRAPHIC_FOLLOWON_RESULTS.md) ---------------------

    /// Intern strings in an order CHOSEN so boot order and alphabetical
    /// order disagree, so a test that merely happened to intern
    /// alphabetically could not pass by accident.
    fn interner_with_reverse_boot_order() -> (crate::sym::Interner, Vec<Sym>) {
        let mut interner = crate::sym::Interner::new();
        // Intern "zebra" first (gets a LOW Sym id) and "apple" last (gets a
        // HIGH Sym id) — the opposite of alphabetical.
        let names = ["zebra", "mango", "banana", "apple"];
        let syms: Vec<Sym> = names.iter().map(|n| interner.intern(n)).collect();
        (interner, syms)
    }

    #[test]
    fn cmp_value_is_still_boot_order_not_lexicographic() {
        // Pins that this rung did NOT touch `cmp_value`'s own (Str,Str)
        // arm — the regression guard the prior rung's own test named as
        // "the test to update when (Str,Str) is fixed". It is NOT fixed
        // globally here; `cmp_value` must stay exactly as it was.
        let (_interner, syms) = interner_with_reverse_boot_order();
        // Boot order: zebra(0) < mango(1) < banana(2) < apple(3) as Syms,
        // so cmp_value must say zebra < apple (wrong alphabetically).
        let zebra = Value::Str(syms[0]);
        let apple = Value::Str(syms[3]);
        assert_eq!(cmp_value(&zebra, &apple), Ordering::Less,
                   "cmp_value must remain Sym-id (boot-history) order, untouched by this rung");
    }

    #[test]
    fn cmp_value_lex_is_byte_lexicographic_regardless_of_boot_order() {
        // THE live before/after case: same interner, same two Values,
        // opposite verdicts from cmp_value vs cmp_value_lex.
        let (interner, syms) = interner_with_reverse_boot_order();
        let zebra = Value::Str(syms[0]);
        let apple = Value::Str(syms[3]);
        assert_eq!(cmp_value(&zebra, &apple), Ordering::Less, "boot order: zebra before apple");
        assert_eq!(cmp_value_lex(&zebra, &apple, &interner), Ordering::Greater,
                   "lex order: apple before zebra — cmp_value_lex inverts cmp_value's verdict here");
        // A full sort by each comparator, on the SAME four strings, gives
        // two different orders — that IS the defect and the fix, live.
        let mut boot_order: Vec<Value> = syms.iter().map(|&s| Value::Str(s)).collect();
        boot_order.sort_by(cmp_value);
        let render = |vs: &[Value]| -> Vec<&str> {
            vs.iter().map(|v| match v {
                Value::Str(s) => interner.resolve(*s),
                _ => unreachable!(),
            }).collect()
        };
        assert_eq!(render(&boot_order), vec!["zebra", "mango", "banana", "apple"],
                   "cmp_value: unchanged boot-history order");
        let mut lex_order: Vec<Value> = syms.iter().map(|&s| Value::Str(s)).collect();
        lex_order.sort_by(|a, b| cmp_value_lex(a, b, &interner));
        assert_eq!(render(&lex_order), vec!["apple", "banana", "mango", "zebra"],
                   "cmp_value_lex: real alphabetical order");
    }

    #[test]
    fn cmp_value_lex_recurses_into_tuples_so_nested_strings_are_lex_too() {
        let (interner, syms) = interner_with_reverse_boot_order();
        let zebra = Value::Str(syms[0]);
        let apple = Value::Str(syms[3]);
        let tup_a = Value::Tuple(Arc::new(SmallVec::from_vec(vec![Value::Int(1), zebra.clone()])));
        let tup_b = Value::Tuple(Arc::new(SmallVec::from_vec(vec![Value::Int(1), apple.clone()])));
        // Same length, same first slot -> decided by the nested string.
        assert_eq!(cmp_value(&tup_a, &tup_b), Ordering::Less, "cmp_value: boot order nested");
        assert_eq!(cmp_value_lex(&tup_a, &tup_b, &interner), Ordering::Greater,
                   "cmp_value_lex: lex order nested — 'apple' < 'zebra'");
    }

    #[test]
    fn cmp_value_lex_agrees_with_cmp_value_on_every_non_string_arm() {
        let interner = crate::sym::Interner::new();
        let pairs: Vec<(Value, Value)> = vec![
            (Value::Int(3), Value::Int(7)),
            (Value::Int(3), Value::Float(3.5)),
            (Value::Float(2.0), Value::Int(2)),
            (Value::Bool(true), Value::Bool(false)),
            (Value::Node(NodeID(1)), Value::Node(NodeID(2))),
            (Value::None, Value::Int(0)),
            (Value::Rational(1, 2), Value::Rational(2, 3)),
        ];
        for (a, b) in pairs {
            assert_eq!(cmp_value(&a, &b), cmp_value_lex(&a, &b, &interner),
                       "cmp_value_lex must match cmp_value outside (Str,Str): {a:?} vs {b:?}");
        }
    }

    #[test]
    fn cmp_value_lex_leaves_surface_text_byte_lexicographic_unchanged() {
        // Surface(Text) was already byte-lexicographic (the prior rung's
        // fix) — cmp_value_lex must agree with cmp_value here, not
        // reintroduce a difference.
        let interner = crate::sym::Interner::new();
        let a = text("apple");
        let b = text("zebra");
        assert_eq!(cmp_value(&a, &b), cmp_value_lex(&a, &b, &interner));
        assert_eq!(cmp_value_lex(&a, &b, &interner), Ordering::Less);
    }
}
