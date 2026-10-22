//! PROCESS ALGEBRA PRIMITIVES (Track I, I1.2).
//!
//! Pure functions behind the `ProcessCompose`, `ProcessInverse`,
//! `ProcessApply`, `EffectSupport`, `EffectFingerprint`, `PermParity` and
//! `MatDet` Terms. They compute; they never decide. Which processes are
//! composed, which inventions are kept and which wall is broken are all
//! graph rules (`seeds/process_schema.json`, `seeds/invention_round.json`,
//! `seeds/invariant_miner.json`, `seeds/process_solving.json`).
//!
//! A PROCESS VALUE is one of (dispatch is on the value's shape):
//!
//! * **Permutation** — a flat sequence of distinct `Int`s `0..n`. Convention
//!   (the probe's, `drafts/process_algebra/process_algebra_probe.py`): the
//!   content at position `i` moves to position `p[i]`, so
//!   `apply(p, s)[p[i]] = s[i]`. `compose(a, b)` is "a then b":
//!   `c[i] = b[a[i]]`. `inverse(p)[p[i]] = i`.
//! * **Integer matrix** — a sequence of `n` sequences of `n` `Int`s. Applied
//!   to an integer column vector: `apply(M, v) = M·v`. `compose(a, b) = B·A`.
//!   The inverse exists exactly when `det = ±1` (unimodular).
//! * **Delta** — `["add", [d0, d1, ...]]`: adds a constant integer vector to
//!   a vector state (a lifted transition effect, I4.1). Inverse negates it.
//! * **Generator step** — `["gen", kind, coord_dims, modulus, matrix,
//!   offset, k]`: one of the shape-decode `DimensionGenerator` kinds applied
//!   `k` times to a signature (a list of relations) through
//!   `shape_decode::apply_generator_k_with_coefficients`, the same code the
//!   decode loop uses. The output relation list is sorted, because a shape
//!   is a set of relations.
//! * **Sequence** — `["seq", p1, p2, ...]`: apply `p1`, then `p2`, ...
//!   Composition of mismatched kinds yields a sequence. `["seq"]` is the
//!   identity.
//!
//! Anything else evaluates to `Value::None` (absent): transition tables,
//! capability and motor programs have no exact effect evaluator here, and
//! the view rules record that honestly. Program-backed ProcessSchema views
//! are dispatched separately by the Term evaluator to the existing fueled,
//! pure `ProgEval` interpreter; this algebra module never interprets programs.

use crate::sym::Interner;
use crate::value::{cmp_value, SurfaceKind, Value};
use smallvec::SmallVec;
use smallvec::smallvec;
use std::sync::Arc;

#[derive(Clone, Debug)]
enum Proc {
    Perm(Vec<usize>),
    Mat(Vec<Vec<i64>>),
    Delta(Vec<i64>),
    Gen(GenStep),
    Seq(Vec<Proc>),
}

#[derive(Clone, Debug)]
struct GenStep {
    kind_val: Value,
    kind: String,
    coord_dims: Vec<i64>,
    modulus: i64,
    matrix: Vec<i64>,
    offset: Vec<i64>,
    k: i64,
}

fn text_of(v: &Value, interner: &Interner) -> Option<String> {
    match v {
        Value::Str(s) => Some(interner.resolve(*s).to_string()),
        Value::Surface(SurfaceKind::Text, b) => std::str::from_utf8(b).ok().map(str::to_string),
        _ => None,
    }
}

/// A string Value: the interned `Str` when the text is already interned
/// (evaluation holds an immutable interner), else a `Surface(Text)`.
fn tag_value(interner: &Interner, s: &str) -> Value {
    match interner.lookup(s) {
        Some(sym) => Value::Str(sym),
        None => Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes())),
    }
}

fn seq_items(v: &Value) -> Option<Arc<[Value]>> {
    match v {
        Value::Tuple(_) | Value::List(_) => Some(v.snapshot()),
        _ => None,
    }
}

fn int_list(v: &Value) -> Option<Vec<i64>> {
    let items = seq_items(v)?;
    items
        .iter()
        .map(|x| match x {
            Value::Int(i) => Some(*i),
            Value::Bool(b) => Some(*b as i64),
            Value::Float(f) if f.fract() == 0.0 && f.is_finite() => Some(*f as i64),
            _ => None,
        })
        .collect()
}

fn int_list_or_empty(v: &Value) -> Vec<i64> {
    match v {
        Value::None => Vec::new(),
        other => int_list(other).unwrap_or_default(),
    }
}

fn as_int(v: &Value) -> Option<i64> {
    match v {
        Value::Int(i) => Some(*i),
        Value::Float(f) if f.fract() == 0.0 && f.is_finite() => Some(*f as i64),
        Value::None => Some(0),
        _ => None,
    }
}

fn parse(v: &Value, interner: &Interner) -> Option<Proc> {
    let items = seq_items(v)?;
    // Graph rules build an ordered collection of process terms with MapList.
    // Its result is a list nested inside the explicit `seq` constructor. Accept
    // that shape only when every member is itself explicitly tagged `seq`;
    // this keeps matrices and ordinary lists unambiguous.
    if !items.is_empty() {
        let tagged_sequences = items.iter().all(|item| {
            seq_items(item)
                .and_then(|parts| parts.first().cloned())
                .and_then(|tag| text_of(&tag, interner))
                .as_deref() == Some("seq")
        });
        if tagged_sequences {
            let mut steps = Vec::new();
            for item in items.iter() {
                match parse(item, interner)? {
                    Proc::Seq(inner) => steps.extend(inner),
                    process => steps.push(process),
                }
            }
            return Some(Proc::Seq(steps));
        }
    }
    if let Some(first) = items.first() {
        if let Some(tag) = text_of(first, interner) {
            return match tag.as_str() {
                "seq" => {
                    let mut steps = Vec::with_capacity(items.len() - 1);
                    for it in items.iter().skip(1) {
                        match parse(it, interner)? {
                            Proc::Seq(inner) => steps.extend(inner),
                            p => steps.push(p),
                        }
                    }
                    Some(Proc::Seq(steps))
                }
                "add" => Some(Proc::Delta(int_list(items.get(1)?)?)),
                "gen" => {
                    let kind_val = items.get(1)?.clone();
                    let kind = text_of(&kind_val, interner)?;
                    Some(Proc::Gen(GenStep {
                        kind_val,
                        kind,
                        coord_dims: int_list_or_empty(items.get(2).unwrap_or(&Value::None)),
                        modulus: as_int(items.get(3).unwrap_or(&Value::None))?,
                        matrix: int_list_or_empty(items.get(4).unwrap_or(&Value::None)),
                        offset: int_list_or_empty(items.get(5).unwrap_or(&Value::None)),
                        k: as_int(items.get(6).unwrap_or(&Value::Int(1)))?,
                    }))
                }
                _ => None,
            };
        }
    }
    // Permutation: every element an Int, forming exactly 0..n.
    if items.iter().all(|x| matches!(x, Value::Int(_))) {
        let p: Vec<i64> = int_list(v)?;
        let n = p.len();
        let mut seen = vec![false; n];
        let mut out = Vec::with_capacity(n);
        for x in p {
            if x < 0 || x as usize >= n || seen[x as usize] {
                return None;
            }
            seen[x as usize] = true;
            out.push(x as usize);
        }
        return Some(Proc::Perm(out));
    }
    // Square integer matrix.
    let n = items.len();
    let mut rows = Vec::with_capacity(n);
    for row in items.iter() {
        let r = int_list(row)?;
        if r.len() != n {
            return None;
        }
        rows.push(r);
    }
    Some(Proc::Mat(rows))
}

fn ints_value(xs: impl IntoIterator<Item = i64>, as_list: bool) -> Value {
    let out: SmallVec<[Value; 4]> = xs.into_iter().map(Value::Int).collect();
    if as_list {
        Value::List(Arc::new(out))
    } else {
        Value::Tuple(Arc::new(out))
    }
}

fn encode(p: &Proc, interner: &Interner, as_list: bool) -> Value {
    match p {
        Proc::Perm(xs) => ints_value(xs.iter().map(|x| *x as i64), as_list),
        Proc::Mat(rows) => {
            let out: SmallVec<[Value; 4]> = rows
                .iter()
                .map(|r| ints_value(r.iter().copied(), as_list))
                .collect();
            if as_list {
                Value::List(Arc::new(out))
            } else {
                Value::Tuple(Arc::new(out))
            }
        }
        Proc::Delta(d) => Value::Tuple(Arc::new(smallvec::smallvec![
            tag_value(interner, "add"),
            ints_value(d.iter().copied(), as_list)
        ])),
        Proc::Gen(g) => Value::Tuple(Arc::new(smallvec::smallvec![
            tag_value(interner, "gen"),
            g.kind_val.clone(),
            ints_value(g.coord_dims.iter().copied(), as_list),
            Value::Int(g.modulus),
            ints_value(g.matrix.iter().copied(), as_list),
            ints_value(g.offset.iter().copied(), as_list),
            Value::Int(g.k)
        ])),
        Proc::Seq(steps) => {
            let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(steps.len() + 1);
            out.push(tag_value(interner, "seq"));
            for s in steps {
                out.push(encode(s, interner, as_list));
            }
            Value::Tuple(Arc::new(out))
        }
    }
}

fn is_list(v: &Value) -> bool {
    matches!(v, Value::List(_))
}

fn mat_mul(a: &[Vec<i64>], b: &[Vec<i64>]) -> Option<Vec<Vec<i64>>> {
    let n = a.len();
    if b.len() != n {
        return None;
    }
    let mut out = vec![vec![0i64; n]; n];
    for i in 0..n {
        for j in 0..n {
            let mut acc: i64 = 0;
            for k in 0..n {
                acc = acc.checked_add(a[i][k].checked_mul(b[k][j])?)?;
            }
            out[i][j] = acc;
        }
    }
    Some(out)
}

/// Exact integer determinant (Bareiss fraction-free elimination over i128).
fn det(m: &[Vec<i64>]) -> Option<i64> {
    let n = m.len();
    if n == 0 {
        return Some(1);
    }
    let mut a: Vec<Vec<i128>> = m
        .iter()
        .map(|r| r.iter().map(|x| *x as i128).collect())
        .collect();
    let mut sign: i128 = 1;
    let mut prev: i128 = 1;
    for k in 0..n.saturating_sub(1) {
        if a[k][k] == 0 {
            let swap = (k + 1..n).find(|&r| a[r][k] != 0);
            match swap {
                Some(r) => {
                    a.swap(k, r);
                    sign = -sign;
                }
                None => return Some(0),
            }
        }
        for i in k + 1..n {
            for j in k + 1..n {
                a[i][j] = (a[i][j] * a[k][k] - a[i][k] * a[k][j]) / prev;
            }
        }
        prev = a[k][k];
    }
    let d = sign * a[n - 1][n - 1];
    i64::try_from(d).ok()
}

/// Integer inverse of a unimodular matrix via the adjugate; `None` unless
/// `det = ±1`.
fn mat_inverse(m: &[Vec<i64>]) -> Option<Vec<Vec<i64>>> {
    let n = m.len();
    let d = det(m)?;
    if d != 1 && d != -1 {
        return None;
    }
    if n == 1 {
        return Some(vec![vec![d]]);
    }
    let mut inv = vec![vec![0i64; n]; n];
    for i in 0..n {
        for j in 0..n {
            let minor: Vec<Vec<i64>> = m
                .iter()
                .enumerate()
                .filter(|(r, _)| *r != i)
                .map(|(_, row)| {
                    row.iter()
                        .enumerate()
                        .filter(|(c, _)| *c != j)
                        .map(|(_, x)| *x)
                        .collect()
                })
                .collect();
            let cof = det(&minor)? * if (i + j) % 2 == 0 { 1 } else { -1 };
            // adjugate is the transpose of the cofactor matrix; divide by det.
            inv[j][i] = cof * d;
        }
    }
    Some(inv)
}

fn compose_proc(a: &Proc, b: &Proc) -> Proc {
    match (a, b) {
        (Proc::Perm(x), Proc::Perm(y)) if x.len() == y.len() => {
            Proc::Perm(x.iter().map(|&i| y[i]).collect())
        }
        (Proc::Mat(x), Proc::Mat(y)) if x.len() == y.len() => match mat_mul(y, x) {
            Some(m) => Proc::Mat(m),
            None => Proc::Seq(vec![a.clone(), b.clone()]),
        },
        (Proc::Delta(x), Proc::Delta(y)) if x.len() == y.len() => {
            Proc::Delta(x.iter().zip(y).map(|(p, q)| p + q).collect())
        }
        _ => {
            let mut steps = Vec::new();
            for p in [a, b] {
                match p {
                    Proc::Seq(inner) => steps.extend(inner.iter().cloned()),
                    other => steps.push(other.clone()),
                }
            }
            Proc::Seq(steps)
        }
    }
}

fn inverse_proc(p: &Proc) -> Option<Proc> {
    match p {
        Proc::Perm(x) => {
            let mut inv = vec![0usize; x.len()];
            for (i, &j) in x.iter().enumerate() {
                inv[j] = i;
            }
            Some(Proc::Perm(inv))
        }
        Proc::Mat(m) => mat_inverse(m).map(Proc::Mat),
        Proc::Delta(d) => Some(Proc::Delta(d.iter().map(|x| -x).collect())),
        Proc::Gen(g) => {
            let k = g.k.max(0);
            let mut out = g.clone();
            match g.kind.as_str() {
                "rotation90" => {
                    out.k = (4 - k % 4) % 4;
                }
                "reflection_r" | "reflection_c" => {
                    out.k = k % 2;
                }
                "modular" if g.modulus > 0 => {
                    out.k = (g.modulus - k % g.modulus) % g.modulus;
                }
                "linear" => {
                    let n = g.coord_dims.len();
                    if n == 0 || g.matrix.len() != n * n {
                        return None;
                    }
                    let m: Vec<Vec<i64>> = g.matrix.chunks(n).map(|r| r.to_vec()).collect();
                    let inv = mat_inverse(&m)?;
                    out.matrix = inv.into_iter().flatten().collect();
                }
                "translate" => {
                    out.offset = g.offset.iter().map(|x| -x).collect();
                }
                _ => return None,
            }
            if out.k == 0 {
                return Some(Proc::Seq(Vec::new()));
            }
            Some(Proc::Gen(out))
        }
        Proc::Seq(steps) => {
            let mut out = Vec::with_capacity(steps.len());
            for s in steps.iter().rev() {
                out.push(inverse_proc(s)?);
            }
            Some(Proc::Seq(out))
        }
    }
}

fn sorted_relations(rels: Vec<Value>, as_list: bool) -> Value {
    let mut rels = rels;
    rels.sort_by(cmp_value);
    let out: SmallVec<[Value; 4]> = rels.into_iter().collect();
    if as_list {
        Value::List(Arc::new(out))
    } else {
        Value::Tuple(Arc::new(out))
    }
}

fn apply_proc(p: &Proc, state: &Value) -> Option<Value> {
    match p {
        Proc::Perm(x) => {
            let items = seq_items(state)?;
            if items.len() != x.len() {
                return None;
            }
            let mut out: Vec<Value> = vec![Value::None; x.len()];
            for (i, &j) in x.iter().enumerate() {
                out[j] = items[i].clone();
            }
            let out: SmallVec<[Value; 4]> = out.into_iter().collect();
            Some(if is_list(state) {
                Value::List(Arc::new(out))
            } else {
                Value::Tuple(Arc::new(out))
            })
        }
        Proc::Mat(m) => {
            let v = int_list(state)?;
            if v.len() != m.len() {
                return None;
            }
            let mut out = Vec::with_capacity(v.len());
            for row in m {
                let mut acc: i64 = 0;
                for (a, b) in row.iter().zip(&v) {
                    acc = acc.checked_add(a.checked_mul(*b)?)?;
                }
                out.push(acc);
            }
            Some(ints_value(out, is_list(state)))
        }
        Proc::Delta(d) => {
            let v = int_list(state)?;
            if v.len() != d.len() {
                return None;
            }
            Some(ints_value(v.iter().zip(d).map(|(a, b)| a + b), is_list(state)))
        }
        Proc::Gen(g) => {
            let items = seq_items(state)?;
            let out = crate::shape_decode::apply_generator_k_with_coefficients(
                &g.kind,
                &g.coord_dims,
                &items,
                g.modulus,
                &g.matrix,
                &[],
                &g.offset,
                g.k,
            )?;
            Some(sorted_relations(out, is_list(state)))
        }
        Proc::Seq(steps) => {
            let mut cur = state.clone();
            for s in steps {
                cur = apply_proc(s, &cur)?;
            }
            Some(cur)
        }
    }
}

/// `ProcessCompose{a, b}` — "a then b".
pub fn compose(a: &Value, b: &Value, interner: &Interner) -> Value {
    match (parse(a, interner), parse(b, interner)) {
        (Some(pa), Some(pb)) => encode(&compose_proc(&pa, &pb), interner, is_list(a)),
        _ => Value::None,
    }
}

/// `ProcessInverse{a}` — exact inverse, or `None` when the process has none.
pub fn inverse(a: &Value, interner: &Interner) -> Value {
    match parse(a, interner).as_ref().and_then(inverse_proc) {
        Some(p) => encode(&p, interner, is_list(a)),
        None => Value::None,
    }
}

/// `ProcessApply{p, state}`.
pub fn apply(p: &Value, state: &Value, interner: &Interner) -> Value {
    parse(p, interner)
        .and_then(|pp| apply_proc(&pp, state))
        .unwrap_or(Value::None)
}

/// Verify a goal-equivalent repair on every supplied fresh state. This is a
/// separate predicate from `inverse`: many-to-one processes may repair a
/// declared set of states while having no exact inverse.
pub fn verify_repair(p: &Value, fresh_states: &[Value], goals: &[Value], interner: &Interner) -> bool {
    !fresh_states.is_empty()
        && fresh_states.len() == goals.len()
        && fresh_states.iter().zip(goals).all(|(state, goal)| {
            let result = apply(p, state, interner);
            result != Value::None && cmp_value(&result, goal) == std::cmp::Ordering::Equal
        })
}

pub fn verify_repair_values(p: &Value, fresh_states: &Value, goals: &Value, interner: &Interner) -> bool {
    match (seq_items(fresh_states), seq_items(goals)) {
        (Some(states), Some(goals)) => verify_repair(p, states.as_ref(), goals.as_ref(), interner),
        _ => false,
    }
}

/// Validate an explicitly finite outcome distribution and preserve its
/// omitted probability as unknown mass. Duplicate outcomes, invalid weights,
/// and total mass above one are unsupported rather than normalized away.
pub fn finite_distribution(outcomes: &[(Value, f64)]) -> Option<(Vec<(Value, f64)>, f64)> {
    let mut total = 0.0;
    for (i, (outcome, probability)) in outcomes.iter().enumerate() {
        if *outcome == Value::None || !probability.is_finite() || *probability < 0.0 || *probability > 1.0 {
            return None;
        }
        if outcomes[..i].iter().any(|(prior, _)| cmp_value(prior, outcome) == std::cmp::Ordering::Equal) {
            return None;
        }
        total += probability;
    }
    if total > 1.0 { return None; }
    Some((outcomes.to_vec(), (1.0 - total).max(0.0)))
}

/// DSL boundary for finite distributions. Input is a sequence of
/// `(outcome, probability)` pairs. Output is `(validated_support, unknown_mass)`.
pub fn finite_distribution_value(value: &Value) -> Value {
    let Some(items) = seq_items(value) else { return Value::None; };
    let mut parsed = Vec::with_capacity(items.len());
    for item in items.iter() {
        let Some(pair) = seq_items(item) else { return Value::None; };
        if pair.len() != 2 { return Value::None; }
        let probability = match &pair[1] {
            Value::Float(x) => *x,
            Value::Int(x) => *x as f64,
            _ => return Value::None,
        };
        parsed.push((pair[0].clone(), probability));
    }
    let Some((support, unknown_mass)) = finite_distribution(&parsed) else { return Value::None; };
    let encoded = support.into_iter().map(|(outcome, probability)| {
        Value::Tuple(Arc::new(smallvec![outcome, Value::Float(probability)]))
    }).collect::<Vec<_>>();
    let encoded: SmallVec<[Value; 4]> = encoded.into_iter().collect();
    Value::Tuple(Arc::new(smallvec![Value::Tuple(Arc::new(encoded)), Value::Float(unknown_mass)]))
}

/// Instantiate a witnessed parametric process tree only when every captured
/// hole is exactly the corresponding source size. This deliberately refuses
/// general anti-unification guesses: callers get a concrete native process or
/// `None`, never a partially-bound process.
pub fn instantiate_lifted_process(
    witness: &Value,
    source_sizes: &Value,
    target_size: &Value,
    interner: &Interner,
) -> Value {
    let Some(witness_items) = seq_items(witness) else { return Value::None; };
    if witness_items.len() != 2 { return Value::None; }
    let Some(sizes) = seq_items(source_sizes) else { return Value::None; };
    let Some(size) = as_int(target_size) else { return Value::None; };
    if sizes.len() != 2 || !(2..=256).contains(&size) { return Value::None; }
    let sizes: Option<Vec<i64>> = sizes.iter().map(as_int).collect();
    let Some(sizes) = sizes else { return Value::None; };
    if sizes[0] == sizes[1] || sizes.iter().any(|x| *x < 2 || *x >= size) { return Value::None; }
    let sigmas = seq_items(&witness_items[1]);
    let Some(sigmas) = sigmas else { return Value::None; };
    if sigmas.len() != sizes.len() { return Value::None; }
    let mut path = Vec::new();
    let Some(tree) = replace_size_wildcards(
        &witness_items[0], &sigmas, &sizes, size, &mut path, interner) else {
        return Value::None;
    };
    eval_lift_tree(&tree, interner).unwrap_or(Value::None)
}

fn replace_size_wildcards(
    value: &Value, sigmas: &[Value], source_sizes: &[i64], target_size: i64,
    path: &mut Vec<Value>, interner: &Interner,
) -> Option<Value> {
    let is_wild = seq_items(value).is_some_and(|items| {
        items.len() == 1 && text_of(&items[0], interner).as_deref() == Some("·?·")
    });
    if is_wild {
        let path_value = Value::Tuple(Arc::new(path.iter().cloned().collect()));
        let mut captures = Vec::with_capacity(sigmas.len());
        for sigma in sigmas {
            let Value::Dict(entries) = sigma else { return None; };
            let Some((_, captured)) = entries.iter().find(|(key, _)| {
                cmp_value(key, &path_value) == std::cmp::Ordering::Equal
            }) else { return None; };
            captures.push(as_int(captured)?);
        }
        if captures.len() != source_sizes.len()
            || captures.iter().zip(source_sizes).any(|(a,b)| a != b) {
            return None;
        }
        return Some(Value::Int(target_size));
    }
    match value {
        Value::Tuple(items) => {
            let mut out: SmallVec<[Value; 4]> = SmallVec::new();
            for (index, child) in items.iter().enumerate() {
                path.push(Value::Int(index as i64));
                let result = replace_size_wildcards(child, sigmas, source_sizes, target_size, path, interner)?;
                path.pop();
                out.push(result);
            }
            Some(Value::Tuple(Arc::new(out)))
        }
        Value::List(items) => {
            let mut out: SmallVec<[Value; 4]> = SmallVec::new();
            for (index, child) in items.iter().enumerate() {
                path.push(Value::Int(index as i64));
                let result = replace_size_wildcards(child, sigmas, source_sizes, target_size, path, interner)?;
                path.pop();
                out.push(result);
            }
            Some(Value::List(Arc::new(out)))
        }
        _ => Some(value.clone()),
    }
}

fn eval_lift_tree(tree: &Value, interner: &Interner) -> Option<Value> {
    let items = seq_items(tree)?;
    let tag = text_of(items.first()?, interner)?;
    let int_at = |index: usize| items.get(index).and_then(as_int);
    match tag.as_str() {
        "cycle" => {
            if items.len() != 4 { return None; }
            let (n, start, len) = (int_at(1)?, int_at(2)?, int_at(3)?);
            if !(2..=256).contains(&n) || start < 0 || start >= n || len < 2 || len > n { return None; }
            let mut p: Vec<i64> = (0..n).collect();
            for offset in 0..len {
                p[((start + offset) % n) as usize] = (start + offset + 1) % n;
            }
            Some(Value::Tuple(Arc::new(p.into_iter().map(Value::Int).collect())))
        }
        "swap" => {
            if items.len() != 4 { return None; }
            let (n, i, j) = (int_at(1)?, int_at(2)?, int_at(3)?);
            if !(2..=256).contains(&n) || i < 0 || j < 0 || i >= n || j >= n || i == j { return None; }
            let mut p: Vec<i64> = (0..n).collect();
            p.swap(i as usize, j as usize);
            Some(Value::Tuple(Arc::new(p.into_iter().map(Value::Int).collect())))
        }
        "inverse" => {
            if items.len() != 2 { return None; }
            let process = eval_lift_tree(&items[1], interner)?;
            let result = inverse(&process, interner);
            (result != Value::None).then_some(result)
        }
        "compose" | "commutator" => {
            if items.len() != 3 { return None; }
            let a = eval_lift_tree(&items[1], interner)?;
            let b = eval_lift_tree(&items[2], interner)?;
            if tag == "compose" { return Some(compose(&a, &b, interner)); }
            let ai = inverse(&a, interner);
            let bi = inverse(&b, interner);
            if ai == Value::None || bi == Value::None { return None; }
            Some(compose(&compose(&compose(&a, &b, interner), &ai, interner), &bi, interner))
        }
        _ => None,
    }
}

/// `EffectSupport{p}` — how much of the world the process touches: moved
/// points for a permutation, non-identity entries for a matrix, non-zero
/// components for a delta. `None` for kinds whose support is only defined
/// relative to probes.
pub fn support(p: &Value, interner: &Interner) -> Value {
    match parse(p, interner) {
        Some(Proc::Perm(x)) => {
            Value::Int(x.iter().enumerate().filter(|(i, j)| *i != **j).count() as i64)
        }
        Some(Proc::Mat(m)) => {
            let mut n = 0i64;
            for (i, row) in m.iter().enumerate() {
                for (j, x) in row.iter().enumerate() {
                    if *x != (i == j) as i64 {
                        n += 1;
                    }
                }
            }
            Value::Int(n)
        }
        Some(Proc::Delta(d)) => Value::Int(d.iter().filter(|x| **x != 0).count() as i64),
        _ => Value::None,
    }
}

/// `EffectFingerprint{p, probes}` — the process's outputs on a fixed probe
/// battery, as a List. `None` if the process cannot be applied to every
/// probe (an unevaluable process has no fingerprint).
pub fn fingerprint(p: &Value, probes: &Value, interner: &Interner) -> Value {
    let Some(pp) = parse(p, interner) else {
        return Value::None;
    };
    let Some(items) = seq_items(probes) else {
        return Value::None;
    };
    let mut out: SmallVec<[Value; 4]> = SmallVec::with_capacity(items.len());
    for probe in items.iter() {
        match apply_proc(&pp, probe) {
            Some(v) => out.push(v),
            None => return Value::None,
        }
    }
    Value::List(Arc::new(out))
}

/// `PermParity{p}` — parity (0 even, 1 odd) of the permutation that sorts a
/// sequence of distinct values. For a permutation value this is its own
/// parity. `None` for duplicates or a non-sequence.
pub fn parity(p: &Value) -> Value {
    let Some(items) = seq_items(p) else {
        return Value::None;
    };
    let n = items.len();
    let mut idx: Vec<usize> = (0..n).collect();
    idx.sort_by(|&i, &j| cmp_value(&items[i], &items[j]));
    for w in idx.windows(2) {
        if cmp_value(&items[w[0]], &items[w[1]]) == std::cmp::Ordering::Equal {
            return Value::None;
        }
    }
    // idx[r] = original position of the r-th smallest; parity of idx.
    let mut seen = vec![false; n];
    let mut odd = 0i64;
    for s in 0..n {
        if seen[s] {
            continue;
        }
        let mut j = s;
        let mut len = 0i64;
        while !seen[j] {
            seen[j] = true;
            j = idx[j];
            len += 1;
        }
        odd ^= (len - 1) & 1;
    }
    Value::Int(odd)
}

/// `MatDet{m}` — exact integer determinant of a square integer matrix.
pub fn mat_det(m: &Value) -> Value {
    let Some(items) = seq_items(m) else {
        return Value::None;
    };
    let n = items.len();
    let mut rows = Vec::with_capacity(n);
    for r in items.iter() {
        match int_list(r) {
            Some(row) if row.len() == n => rows.push(row),
            _ => return Value::None,
        }
    }
    det(&rows).map(Value::Int).unwrap_or(Value::None)
}

#[cfg(test)]
mod tests {
    use super::*;
    use smallvec::smallvec;

    fn ints(xs: &[i64]) -> Value {
        Value::Tuple(Arc::new(xs.iter().map(|x| Value::Int(*x)).collect()))
    }

    fn row_shift(n: usize, row: usize) -> Value {
        let mut p: Vec<i64> = (0..(n * n) as i64).collect();
        for c in 0..n {
            p[row * n + c] = (row * n + (c + 1) % n) as i64;
        }
        ints(&p)
    }

    fn col_shift(n: usize, col: usize) -> Value {
        let mut p: Vec<i64> = (0..(n * n) as i64).collect();
        for r in 0..n {
            p[r * n + col] = (((r + 1) % n) * n + col) as i64;
        }
        ints(&p)
    }

    #[test]
    fn permutation_algebra_matches_the_probe() {
        let ir = Interner::new();
        let r0 = row_shift(3, 0);
        let c0 = col_shift(3, 0);
        let r0i = inverse(&r0, &ir);
        let c0i = inverse(&c0, &ir);
        // [R0, C0] = R0 · C0 · R0⁻¹ · C0⁻¹ moves exactly 3 cells.
        let comm = compose(&compose(&compose(&r0, &c0, &ir), &r0i, &ir), &c0i, &ir);
        assert_eq!(support(&comm, &ir), Value::Int(3));
        assert_eq!(parity(&comm), Value::Int(0));
        // p · p⁻¹ is the identity.
        let id = compose(&r0, &r0i, &ir);
        assert_eq!(id, ints(&(0..9).collect::<Vec<_>>()));
        // A 4-cycle row shift on 4x4 is odd.
        assert_eq!(parity(&row_shift(4, 0)), Value::Int(1));
        // apply moves content at i to p[i].
        let s = ints(&[10, 11, 12]);
        assert_eq!(apply(&ints(&[1, 2, 0]), &s, &ir), ints(&[12, 10, 11]));
    }

    #[test]
    fn graph_mapped_nested_sequence_applies_in_order() {
        let ir = Interner::new();
        let mut nested = Vec::new();
        for i in 0..5 {
            let mut p: Vec<i64> = (0..6).collect();
            p.swap(i, 5);
            nested.push(Value::Tuple(Arc::new(smallvec![
                Value::Surface(SurfaceKind::Text, Arc::from(&b"seq"[..])),
                ints(&p),
            ])));
        }
        let mapped = Value::List(Arc::new(nested.into_iter().collect()));
        let sequence = Value::Tuple(Arc::new(smallvec![
            Value::Surface(SurfaceKind::Text, Arc::from(&b"seq"[..])),
            mapped,
        ]));
        assert_eq!(apply(&sequence, &ints(&[1, 2, 3, 4, 5, 0]), &ir), ints(&[0, 1, 2, 3, 4, 5]));
    }

    #[test]
    fn matrices_compose_invert_and_have_exact_determinants() {
        let ir = Interner::new();
        let rot = Value::Tuple(Arc::new(smallvec![ints(&[0, -1]), ints(&[1, 0])]));
        let r2 = compose(&rot, &rot, &ir);
        assert_eq!(r2, Value::Tuple(Arc::new(smallvec![ints(&[-1, 0]), ints(&[0, -1])])));
        let inv = inverse(&rot, &ir);
        assert_eq!(compose(&rot, &inv, &ir), Value::Tuple(Arc::new(smallvec![ints(&[1, 0]), ints(&[0, 1])])));
        assert_eq!(mat_det(&rot), Value::Int(1));
        let sing = Value::Tuple(Arc::new(smallvec![ints(&[2, 0]), ints(&[0, 1])]));
        assert_eq!(inverse(&sing, &ir), Value::None);
        assert_eq!(apply(&rot, &ints(&[1, 0]), &ir), ints(&[0, 1]));
    }

    #[test]
    fn deltas_and_invalid_values() {
        let ir = Interner::new();
        let add = Value::Tuple(Arc::new(smallvec![
            Value::Surface(SurfaceKind::Text, Arc::from(&b"add"[..])),
            ints(&[1, 0])
        ]));
        assert_eq!(apply(&add, &ints(&[2, 3]), &ir), ints(&[3, 3]));
        let back = inverse(&add, &ir);
        assert_eq!(apply(&back, &ints(&[3, 3]), &ir), ints(&[2, 3]));
        // Not a permutation, not a matrix: absent everywhere.
        let bad = ints(&[0, 0, 1]);
        assert_eq!(support(&bad, &ir), Value::None);
        assert_eq!(fingerprint(&bad, &Value::Tuple(Arc::new(smallvec![ints(&[1, 2, 3])])), &ir), Value::None);
        assert_eq!(parity(&bad), Value::None);
    }

    #[test]
    fn repair_is_fresh_goal_verification_not_inverse() {
        let ir = Interner::new();
        let add = Value::Tuple(Arc::new(smallvec![
            Value::Surface(SurfaceKind::Text, Arc::from(&b"add"[..])), ints(&[1])
        ]));
        let starts = [ints(&[0]), ints(&[4])];
        let goals = [ints(&[1]), ints(&[5])];
        assert!(verify_repair(&add, &starts, &goals, &ir));
        assert!(!verify_repair(&add, &starts, &[ints(&[1]), ints(&[4])], &ir));
        assert!(!verify_repair(&Value::None, &starts, &goals, &ir));
    }

    #[test]
    fn finite_distribution_retains_support_and_unknown_mass() {
        let support = vec![(ints(&[0]), 0.25), (ints(&[1]), 0.5)];
        let (kept, unknown) = finite_distribution(&support).unwrap();
        assert_eq!(kept.len(), 2);
        assert!((unknown - 0.25).abs() < 1e-12);
        assert!(finite_distribution(&[(ints(&[0]), 0.7), (ints(&[1]), 0.4)]).is_none());
        assert!(finite_distribution(&[(ints(&[0]), 1.0), (ints(&[1]), f64::EPSILON)]).is_none());
        assert!(finite_distribution(&[(ints(&[0]), 0.5), (ints(&[0]), 0.5)]).is_none());
    }

    #[test]
    fn lifted_commutator_rebinds_only_consistent_size_witnesses() {
        let ir = Interner::new();
        let text = |s: &str| Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes()));
        let seq = |xs: Vec<Value>| Value::Tuple(Arc::new(xs.into_iter().collect::<SmallVec<[Value; 4]>>()));
        let path = |a, b| seq(vec![Value::Int(a), Value::Int(b)]);
        let wild = seq(vec![text("·?·")]);
        let template = seq(vec![
            text("commutator"),
            seq(vec![text("cycle"), wild.clone(), Value::Int(0), wild.clone()]),
            seq(vec![text("swap"), wild.clone(), Value::Int(0), Value::Int(1)]),
        ]);
        let sigma = |n| Value::Dict(Arc::from([
            (path(1, 1), Value::Int(n)),
            (path(1, 3), Value::Int(n)),
            (path(2, 1), Value::Int(n)),
        ]));
        let witness = seq(vec![template, seq(vec![sigma(3), sigma(5)])]);
        let got = instantiate_lifted_process(&witness, &ints(&[3, 5]), &Value::Int(6), &ir);
        assert!(matches!(parse(&got, &ir), Some(Proc::Perm(ref p)) if p.len() == 6));
        // A hole that does not track source size is not guessed into a lift.
        let bad = seq(vec![
            Value::Dict(Arc::from([(path(1, 1), Value::Int(3)),
                                   (path(1, 3), Value::Int(2)),
                                   (path(2, 1), Value::Int(3))])),
            Value::Dict(Arc::from([(path(1, 1), Value::Int(5)),
                                   (path(1, 3), Value::Int(4)),
                                   (path(2, 1), Value::Int(5))])),
        ]);
        let bad_witness = seq(vec![
            seq(vec![text("commutator"),
                seq(vec![text("cycle"), wild.clone(), Value::Int(0), wild.clone()]),
                seq(vec![text("swap"), wild, Value::Int(0), Value::Int(1)])]), bad]);
        assert_eq!(instantiate_lifted_process(&bad_witness, &ints(&[3, 5]), &Value::Int(6), &ir), Value::None);
    }
}
