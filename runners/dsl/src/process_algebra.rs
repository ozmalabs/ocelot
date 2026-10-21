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
//! Anything else evaluates to `Value::None` (absent): programs, transition
//! tables, capability and motor programs have no exact effect evaluator
//! here, and the view rules record that honestly.

use crate::sym::Interner;
use crate::value::{cmp_value, SurfaceKind, Value};
use smallvec::SmallVec;
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
}
