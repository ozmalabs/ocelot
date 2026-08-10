//! `StrokeQuantize` — deterministic stroke-geometry quantizer.
//!
//! The handwriting instance of "shape matching IS dequantization; a
//! transform IS a quantum delta on ONE dimension"
//! (`HANDWRITING_DESIGN.md`, R1). A raw pen stroke (a polyline of
//! `[x, y]` points) is quantized into a `ShapeSignature`-compatible
//! relation-system — `["seg", i, turn_q, len_q]` per arc-length-
//! resampled segment (rotation/translation/scale-INVARIANT by
//! construction) plus, unless `invariant_only`, four separate arity-2
//! pose relations (`pose_x`/`pose_y`/`pose_o`/`pose_s`) — so the
//! EXISTING `ShapeDecode`/`TransformDecode`/`DimInfer` Terms and the
//! `sd_*` seed-rule loop (`shape_decode.rs`) apply UNCHANGED to ink.
//! This module is pure geometry: no graph reads, no rule engine, no
//! decisions — see `eval_stroke_quantize`.
//!
//! Kept as its own module (not folded into `shape_decode.rs`) per the
//! design doc's working-tree isolation note: `shape_decode.rs` is
//! untouched by this change, so this module's edits never collide with
//! unrelated concurrent work in that file.
//!
//! ## Why the predicate strings are pre-interned Term fields
//!
//! `EvalCtx::interner` is `&Interner` — evaluation never mutates the
//! interner (see `shape_decode.rs`'s module doc for the full rationale).
//! A relation's predicate slot must be a REAL `Value::Str(Sym)` so it
//! compares equal to the same predicate name arriving from a codebook
//! node's stored signature — so `"seg"`/`"pose_x"`/`"pose_y"`/
//! `"pose_o"`/`"pose_s"` are interned ONCE when the `StrokeQuantize`
//! Term is constructed (JSON parse / reflect reconstruct / direct Rust
//! construction) and carried as `Sym` fields, exactly like `AntiUnify`'s
//! `wild` sentinel — never re-interned inside `eval_stroke_quantize`.

use std::sync::Arc;

use smallvec::SmallVec;

use crate::sym::{Interner, Sym};
use crate::term::{evaluate, Env, EvalCtx, TermArena, TermIdx};
use crate::value::{SurfaceKind, Value};

// --- tiny output helpers ---
//
// Deliberately duplicated (not imported) from `shape_decode.rs`'s
// private `surf`/`select_field`/`finish` — a few lines, kept local so
// this module's diff never touches `shape_decode.rs` (working-tree
// isolation; see module doc).

fn surf(s: &str) -> Value {
    Value::Surface(SurfaceKind::Text, Arc::from(s.as_bytes()))
}

fn select_field(dict: &Value, field_name: &str) -> Value {
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

fn finish(result: Value, field: Sym, interner: &Interner) -> Value {
    if field == Sym::default() {
        return result;
    }
    select_field(&result, interner.resolve(field))
}

// --- geometry primitives ---

fn dist(a: (f64, f64), b: (f64, f64)) -> f64 {
    ((a.0 - b.0).powi(2) + (a.1 - b.1).powi(2)).sqrt()
}

fn heading_deg(v: (f64, f64)) -> f64 {
    v.1.atan2(v.0) * 180.0 / std::f64::consts::PI
}

/// Round half away from zero (vs Rust's `f64::round`, which already IS
/// round-half-away-from-zero for positive halves but this makes the
/// convention explicit and symmetric for negative halves too) — the
/// stable tie-break this module documents for angle quantization.
fn round_half_away_from_zero(x: f64) -> f64 {
    if x >= 0.0 {
        (x + 0.5).floor()
    } else {
        (x - 0.5).ceil()
    }
}

/// Wrap a degree value into `(-180, 180]`.
fn wrap180(deg: f64) -> f64 {
    let mut d = deg % 360.0;
    if d <= -180.0 {
        d += 360.0;
    }
    if d > 180.0 {
        d -= 360.0;
    }
    d
}

/// Quantize a signed angle (degrees) into an integer bin spanning
/// `(-180°, 180°]`, `bins` buckets total (e.g. `bins=16` → 22.5°/bin).
/// Round-half-away-from-zero; a documented limitation is that an input
/// exactly ON a bin boundary can flip by one bin under floating-point
/// error — callers (and this module's tests) keep fixture angles safely
/// inside a bin.
fn quantize_signed_angle(deg: f64, bins: i64) -> i64 {
    let bins = bins.max(1);
    let bin_width = 360.0 / bins as f64;
    let wrapped = wrap180(deg);
    let raw = round_half_away_from_zero(wrapped / bin_width) as i64;
    let half = bins / 2;
    let mut q = raw;
    while q > half {
        q -= bins;
    }
    while q < -half {
        q += bins;
    }
    q
}

/// Bucket `v` into `[0, bins-1]` over `[lo, hi)` — floor-based
/// digitization ("which cell contains the value"). A degenerate
/// zero-extent range (`hi <= lo`) always returns `0`.
fn quantize_bucket(v: f64, lo: f64, hi: f64, bins: i64) -> i64 {
    let bins = bins.max(1);
    if !(hi > lo) {
        return 0;
    }
    let frac = (v - lo) / (hi - lo);
    let idx = (frac * bins as f64).floor() as i64;
    idx.clamp(0, bins - 1)
}

/// The point-set's own axis-aligned bbox — the fallback pose frame when
/// no external `bounds` Term is given (see `TermNode::StrokeQuantize`'s
/// doc for the documented limitation this implies).
fn point_bbox(points: &[(f64, f64)]) -> (f64, f64, f64, f64) {
    let mut x0 = f64::INFINITY;
    let mut x1 = f64::NEG_INFINITY;
    let mut y0 = f64::INFINITY;
    let mut y1 = f64::NEG_INFINITY;
    for &(x, y) in points {
        if x < x0 {
            x0 = x;
        }
        if x > x1 {
            x1 = x;
        }
        if y < y0 {
            y0 = y;
        }
        if y > y1 {
            y1 = y;
        }
    }
    if !x0.is_finite() {
        (0.0, 0.0, 0.0, 0.0)
    } else {
        (x0, y0, x1, y1)
    }
}

/// Resample `points` BY ARC LENGTH into `segments` equal-length pieces,
/// returning `segments+1` resample knots (endpoints preserved exactly)
/// plus the total arc length. `None` on a degenerate input — fewer than
/// 2 distinct points (consecutive near-duplicates, distance `< 1e-9`,
/// are dropped first) or a total length `< 1e-9` — the caller falls
/// back to a minimal graceful Dict, never panics.
fn resample_by_arclength(points: &[(f64, f64)], segments: i64) -> Option<(Vec<(f64, f64)>, f64)> {
    let n_out = segments.max(1) as usize;

    let mut pts: Vec<(f64, f64)> = Vec::with_capacity(points.len());
    for &p in points {
        if let Some(&last) = pts.last() {
            if dist(p, last) < 1e-9 {
                continue;
            }
        }
        pts.push(p);
    }
    if pts.len() < 2 {
        return None;
    }

    let mut cum = vec![0.0f64; pts.len()];
    for i in 1..pts.len() {
        cum[i] = cum[i - 1] + dist(pts[i], pts[i - 1]);
    }
    let total = *cum.last().unwrap();
    if total < 1e-9 {
        return None;
    }

    let mut resampled = Vec::with_capacity(n_out + 1);
    let mut j = 0usize;
    for k in 0..=n_out {
        let target = total * (k as f64) / (n_out as f64);
        while j + 2 < pts.len() && cum[j + 1] < target {
            j += 1;
        }
        let seg_span = cum[j + 1] - cum[j];
        let f = if seg_span > 1e-12 {
            ((target - cum[j]) / seg_span).clamp(0.0, 1.0)
        } else {
            0.0
        };
        let x = pts[j].0 + (pts[j + 1].0 - pts[j].0) * f;
        let y = pts[j].1 + (pts[j + 1].1 - pts[j].1) * f;
        resampled.push((x, y));
    }
    Some((resampled, total))
}

/// Read `points`'s evaluated Value as a `Vec<(f64,f64)>` — a Tuple of
/// `[x, y]` frames; malformed entries (wrong shape, non-numeric) are
/// skipped rather than erroring, matching the rest of the DSL's
/// graceful-degrade posture for observation-shaped input.
fn read_points(v: &Value) -> Vec<(f64, f64)> {
    let mut out = Vec::new();
    if let (Value::Tuple(items) | Value::List(items)) = v {
        for it in items.iter() {
            if let (Value::Tuple(pair) | Value::List(pair)) = it {
                if pair.len() >= 2 {
                    out.push((pair[0].as_f64(), pair[1].as_f64()));
                }
            }
        }
    }
    out
}

/// Read an optional `bounds` Value as `(x0, y0, x1, y1)`; any other
/// shape is treated as absent (caller falls back to the point-set bbox).
fn read_bounds(v: &Value) -> Option<(f64, f64, f64, f64)> {
    if let (Value::Tuple(items) | Value::List(items)) = v {
        if items.len() >= 4 {
            return Some((items[0].as_f64(), items[1].as_f64(), items[2].as_f64(), items[3].as_f64()));
        }
    }
    None
}

/// Evaluate `StrokeQuantize`. See `TermNode::StrokeQuantize`'s doc
/// (`term.rs`) for the full field-by-field semantics.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_stroke_quantize(
    arena: &TermArena,
    points_idx: TermIdx,
    segments: i64,
    turn_bins: i64,
    len_bins: i64,
    grid: i64,
    scale_bins: i64,
    invariant_only: bool,
    canonical_pose: bool,
    turn_edges_idx: Option<TermIdx>,
    len_edges_idx: Option<TermIdx>,
    emit_residual: bool,
    bounds_idx: Option<TermIdx>,
    field: Sym,
    seg_sym: Sym,
    pose_x_sym: Sym,
    pose_y_sym: Sym,
    pose_o_sym: Sym,
    pose_s_sym: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let points_val = evaluate(arena, points_idx, env, ctx);
    let points = read_points(&points_val);
    let n_points = points.len() as i64;

    let bounds = bounds_idx.and_then(|idx| read_bounds(&evaluate(arena, idx, env, ctx)));
    let (bx0, by0, bx1, by1) = bounds.unwrap_or_else(|| point_bbox(&points));

    let turn_bins = turn_bins.max(1);
    let len_bins = len_bins.max(1);
    let grid = grid.max(1);
    let scale_bins = scale_bins.max(1);

    // RUN 32 -- ADAPTIVE EDGES: resolved ONCE, up front. `turn_edges`/`len_edges` is
    // `Some` only when a real (>=2-entry) array was supplied -- absent/malformed input
    // falls straight through to the uniform path, byte-identical to pre-RUN-32.
    let turn_edges: Option<Vec<f64>> =
        turn_edges_idx.and_then(|idx| read_edges(&evaluate(arena, idx, env, ctx)));
    let len_edges: Option<Vec<f64>> =
        len_edges_idx.and_then(|idx| read_edges(&evaluate(arena, idx, env, ctx)));
    let quantize_turn = |deg: f64| -> i64 {
        match &turn_edges {
            Some(e) => quantize_edges(wrap180(deg), e),
            None => quantize_signed_angle(deg, turn_bins),
        }
    };
    let turn_center = |q: i64| -> f64 {
        match &turn_edges {
            Some(e) => edge_bin_center(q, e),
            None => angle_bin_center(q, turn_bins),
        }
    };
    let quantize_len = |frac: f64| -> i64 {
        match &len_edges {
            Some(e) => quantize_edges(frac, e),
            None => quantize_bucket(frac, 0.0, 1.0, len_bins),
        }
    };
    let len_center = |q: i64| -> f64 {
        match &len_edges {
            Some(e) => edge_bin_center(q, e),
            None => bucket_center(q, 0.0, 1.0, len_bins),
        }
    };

    let Some((resampled, total)) = resample_by_arclength(&points, segments) else {
        // Degenerate: <2 distinct points, or zero total arc length.
        // Graceful minimal Dict — no panic.
        let p0 = points.first().copied().unwrap_or((0.0, 0.0));
        let x_q = quantize_bucket(p0.0, bx0, bx1, grid);
        let y_q = quantize_bucket(p0.1, by0, by1, grid);
        let scale_q = quantize_bucket(-4.0, -4.0, 4.0, scale_bins);
        let pose = Value::Dict(Arc::from(vec![
            (surf("x_q"), Value::Int(x_q)),
            (surf("y_q"), Value::Int(y_q)),
            (surf("orient_q"), Value::Int(0)),
            (surf("scale_q"), Value::Int(scale_q)),
        ]));
        let result = Value::Dict(Arc::from(vec![
            (surf("signature"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("pose"), pose),
            (surf("arc_len"), Value::Float(0.0)),
            (surf("n_points"), Value::Int(n_points)),
        ]));
        return finish(result, field, ctx.interner);
    };

    let n = resampled.len() - 1;
    let mut headings: Vec<f64> = Vec::with_capacity(n);
    let mut lengths: Vec<f64> = Vec::with_capacity(n);
    for i in 0..n {
        let v = (resampled[i + 1].0 - resampled[i].0, resampled[i + 1].1 - resampled[i].1);
        headings.push(heading_deg(v));
        lengths.push(dist(resampled[i + 1], resampled[i]));
    }

    let mut relations: SmallVec<[Value; 4]> = SmallVec::new();
    // RUN 32 -- SUB-BIN RESIDUAL (opt-in, `emit_residual`): `[i, turn_residual,
    // len_residual]` per segment, parallel to `relations`'s own `seg` entries — "the
    // remainder goes to more detail," applied WITHIN a bin rather than across a coarser/
    // finer bin split. Populated regardless of which quantize path (uniform or adaptive-
    // edge) actually produced `turn_q`/`len_q`, since both `turn_center`/`len_center`
    // closures already dispatch on that same choice — a residual is well-defined either
    // way, only ever OMITTED from the output entirely when `emit_residual` is false.
    let mut residuals: SmallVec<[Value; 4]> = SmallVec::new();
    for i in 0..n {
        // Segment 0 has no PREVIOUS heading to take a relative turn
        // against — defined as turn_q = 0 (a stable, documented choice;
        // see TermNode::StrokeQuantize's doc).
        let (turn_q, turn_residual) = if i == 0 {
            (0, 0.0)
        } else {
            let wrapped = wrap180(headings[i] - headings[i - 1]);
            let q = quantize_turn(headings[i] - headings[i - 1]);
            (q, wrapped - turn_center(q))
        };
        let len_frac = if total > 1e-12 { lengths[i] / total } else { 0.0 };
        let len_q = quantize_len(len_frac);
        let len_residual = len_frac - len_center(len_q);
        relations.push(Value::Tuple(Arc::new(smallvec::smallvec![
            Value::Str(seg_sym),
            Value::Int(i as i64),
            Value::Int(turn_q),
            Value::Int(len_q),
        ])));
        if emit_residual {
            residuals.push(Value::Tuple(Arc::new(smallvec::smallvec![
                Value::Int(i as i64),
                Value::Float(turn_residual),
                Value::Float(len_residual),
            ])));
        }
    }

    let orient_q = quantize_turn(headings[0]);
    let x_q = quantize_bucket(resampled[0].0, bx0, bx1, grid);
    let y_q = quantize_bucket(resampled[0].1, by0, by1, grid);
    let log_scale = total.max(1e-9).log2().clamp(-4.0, 4.0);
    let scale_q = quantize_bucket(log_scale, -4.0, 4.0, scale_bins);

    if !invariant_only {
        // `canonical_pose` is the CODEBOOK-ENTRY form (see the Term doc):
        // pose relations at the canonical bins — bounds-origin position
        // (0, 0), heading bin 0, and the scale bin containing
        // log2(arc_len) = 0 (arc length 1 after normalization; bin
        // `scale_bins/2` for the fixed symmetric [-4, 4] log2 range —
        // bin 4 at the default scale_bins = 8). Relation counts then
        // match a full observed signature, so an observed stroke's pose
        // deltas against the canonical entry ARE the rung-1 similarity
        // transform. The measured pose still goes in the informational
        // `pose` Dict below, unconditionally.
        let (sx, sy, so, ss) = if canonical_pose {
            (0, 0, 0, quantize_bucket(0.0, -4.0, 4.0, scale_bins))
        } else {
            (x_q, y_q, orient_q, scale_q)
        };
        relations.push(Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(pose_x_sym), Value::Int(sx)])));
        relations.push(Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(pose_y_sym), Value::Int(sy)])));
        relations.push(Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(pose_o_sym), Value::Int(so)])));
        relations.push(Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(pose_s_sym), Value::Int(ss)])));
    }

    let pose = Value::Dict(Arc::from(vec![
        (surf("x_q"), Value::Int(x_q)),
        (surf("y_q"), Value::Int(y_q)),
        (surf("orient_q"), Value::Int(orient_q)),
        (surf("scale_q"), Value::Int(scale_q)),
    ]));

    let mut result_fields = vec![
        (surf("signature"), Value::Tuple(Arc::new(relations))),
        (surf("pose"), pose),
        (surf("arc_len"), Value::Float(total)),
        (surf("n_points"), Value::Int(n_points)),
    ];
    if emit_residual {
        result_fields.push((surf("residuals"), Value::Tuple(Arc::new(residuals))));
    }
    let result = Value::Dict(Arc::from(result_fields));
    finish(result, field, ctx.interner)
}

// --- StrokeRender: StrokeQuantize's exact generative inverse ---
//
// "ABS AS DEFAULT" (`HANDWRITING_DESIGN.md`): "the generation and reading
// model is the same ... it just runs the same engine in reverse." Where
// `eval_stroke_quantize` SAMPLES a polyline into a relation-system,
// `eval_stroke_render` DEQUANTIZES a relation-system back into a
// polyline — same conventions, same bin math, run backwards.

/// Inverse of `quantize_bucket`: the CENTER of bucket `idx` over `[lo,
/// hi)`. A degenerate zero-extent range (`hi <= lo`) always returns `lo`
/// (mirrors `quantize_bucket`'s `hi <= lo` fallback of always returning
/// bucket `0`, whose "center" degenerates to the range's single point).
fn bucket_center(idx: i64, lo: f64, hi: f64, bins: i64) -> f64 {
    let bins = bins.max(1);
    if !(hi > lo) {
        return lo;
    }
    let bin_width = (hi - lo) / bins as f64;
    lo + (idx as f64 + 0.5) * bin_width
}

/// Inverse of `quantize_signed_angle`: the CENTER angle (degrees,
/// wrapped to `(-180, 180]`) of signed-angle bin `q` over `bins` buckets
/// spanning a full turn. `quantize_signed_angle` rounds half-away-from-
/// zero onto multiples of `360/bins`, so bin `q`'s center is exactly
/// `q * (360/bins)`.
fn angle_bin_center(q: i64, bins: i64) -> f64 {
    let bins = bins.max(1);
    let bin_width = 360.0 / bins as f64;
    wrap180(q as f64 * bin_width)
}

// --- RUN 32 -- ADAPTIVE (DATA-PLACED) BIN EDGES -------------------------------------------
//
// `quantize_edges`/`edge_bin_center` are the explicit-boundary-array analogs of
// `quantize_bucket`/`bucket_center` (uniform), used ONLY when a caller supplies a
// `turn_edges`/`len_edges` array (`StrokeQuantize`/`StrokeRender`'s new optional fields —
// see `term.rs`'s doc for the full rationale: OPTION R, "attack the bin grain," the
// 10,230/10,231-LEARN-spans-in-one-family calibration finding). `edges` is an ascending
// array of `n_bins+1` interval boundaries (e.g. quantile/equal-mass splits of an observed
// distribution, computed by a Python world-adapter/seed-builder over the LEARN population
// and handed in as plain graph/held data — never computed here; this module stays pure
// geometry). LEFT-EDGE-INCLUSIVE floor digitization (the SAME convention `quantize_bucket`
// already uses for position/length/scale) applies uniformly to BOTH the turn and length
// dimensions under this path -- a deliberate, documented departure from
// `quantize_signed_angle`'s own round-to-nearest-bin-center convention for the UNIFORM turn
// path (kept byte-identical, untouched): quantile-derived boundaries ARE floor-digitizable
// edges, not centers, so one convention serves both dimensions here.

/// Bucket `v` into `[0, edges.len()-2]` via left-edge-inclusive interval membership over an
/// arbitrary (not necessarily uniform) ascending boundary array. `v` outside
/// `[edges[0], edges[last]]` clamps to the nearest end bin (the same graceful-saturation
/// posture `quantize_bucket` already has). `edges.len() < 2` degenerates to bin 0.
fn quantize_edges(v: f64, edges: &[f64]) -> i64 {
    let n_bins = edges.len().saturating_sub(1);
    if n_bins == 0 {
        return 0;
    }
    if v <= edges[0] {
        return 0;
    }
    if v >= edges[n_bins] {
        return (n_bins - 1) as i64;
    }
    for i in 0..n_bins {
        if v < edges[i + 1] {
            return i as i64;
        }
    }
    (n_bins - 1) as i64
}

/// Inverse of `quantize_edges`: the MIDPOINT of bin `idx`'s own interval
/// `[edges[idx], edges[idx+1])`. Documented choice (RUN 32): EDGE MIDPOINTS, not per-bin
/// mass centers — the inverse stays a pure function of the edges array alone (no extra
/// stored per-bin statistic needed to render), and is exact-inverse-safe by the same
/// construction `bucket_center` already relies on, provided the midpoint itself does not
/// land exactly on a (different) boundary — the same bin-center-safety caveat every
/// existing quantize/center pair in this module already documents.
fn edge_bin_center(idx: i64, edges: &[f64]) -> f64 {
    let n_bins = edges.len().saturating_sub(1);
    if n_bins == 0 {
        return 0.0;
    }
    let i = idx.clamp(0, (n_bins - 1) as i64) as usize;
    (edges[i] + edges[i + 1]) / 2.0
}

/// Read an evaluated Term's Value as a flat `Vec<f64>` (a Tuple of numeric scalars) — the
/// shape a `turn_edges`/`len_edges` `Lit` literal takes. Fewer than 2 usable entries (no real
/// edge array) is reported back to the caller as `None` so it can fall through to the
/// uniform path exactly as if the field were absent — the SAME graceful-degrade posture
/// `read_bounds` already has for a malformed `bounds` Value.
fn read_edges(v: &Value) -> Option<Vec<f64>> {
    if let (Value::Tuple(items) | Value::List(items)) = v {
        let out: Vec<f64> = items.iter().map(|x| x.as_f64()).collect();
        if out.len() >= 2 {
            return Some(out);
        }
    }
    None
}

/// Read a `StrokeRender` `signature` Term's evaluated Value as a flat
/// relation list `(predicate, numeric args)` — the render-side twin of
/// `shape_decode.rs`'s `json_to_value_scoped` dual parsing (native
/// `Value::Tuple` relation-system OR a JSON-string blob — the same
/// duality every `ShapeSignature` codebook node's `signature` attr
/// already uses) but DELIBERATELY NOT SHARED with it: that helper (and
/// `load_parts`, which calls it) is private to `shape_decode.rs`, and
/// per this module's doc, `strokes.rs`'s edits stay self-contained so
/// they never collide with unrelated concurrent work in that file.
///
/// The re-derivation is also simpler than `json_to_value_scoped`, not
/// just isolated: `StrokeRender` never emits a relation predicate back
/// into the graph (it only ever outputs numeric points), so it never
/// needs `json_to_value_scoped`'s placeholder-Sym fabrication — a
/// predicate is read as a plain `&str` and compared against the fixed
/// literals `"seg"`/`"pose_x"`/`"pose_y"`/`"pose_o"`/`"pose_s"` directly.
/// A native `Value::Str(Sym)` predicate is resolved via
/// `Interner::resolve` (a read op — always safe here since every Sym
/// arriving through `evaluate()` is already really interned); a JSON
/// string is parsed with `serde_json` straight into `&str` predicates,
/// no `Interner` involved at all on that path. Malformed entries (wrong
/// shape, non-array elements, unparseable JSON) are skipped rather than
/// erroring, matching this module's graceful-degrade posture.
fn read_relations(v: &Value, interner: &Interner) -> Vec<(String, Vec<f64>)> {
    fn from_tuple(items: &[Value], interner: &Interner) -> Vec<(String, Vec<f64>)> {
        let mut out = Vec::with_capacity(items.len());
        for it in items {
            let (Value::Tuple(rel) | Value::List(rel)) = it else { continue };
            if rel.is_empty() {
                continue;
            }
            let pred = match &rel[0] {
                Value::Str(sym) => interner.resolve(*sym).to_string(),
                Value::Surface(SurfaceKind::Text, bytes) => String::from_utf8_lossy(bytes).to_string(),
                _ => continue,
            };
            let args: Vec<f64> = rel[1..].iter().map(|x| x.as_f64()).collect();
            out.push((pred, args));
        }
        out
    }
    fn from_json(text: &str) -> Vec<(String, Vec<f64>)> {
        let Ok(serde_json::Value::Array(items)) = serde_json::from_str::<serde_json::Value>(text) else {
            return Vec::new();
        };
        let mut out = Vec::with_capacity(items.len());
        for it in &items {
            let serde_json::Value::Array(rel) = it else { continue };
            if rel.is_empty() {
                continue;
            }
            let Some(pred) = rel[0].as_str() else { continue };
            let args: Vec<f64> = rel[1..].iter().filter_map(|x| x.as_f64()).collect();
            out.push((pred.to_string(), args));
        }
        out
    }

    match v {
        Value::Tuple(items) | Value::List(items) => from_tuple(items, interner),
        Value::Str(sym) => from_json(interner.resolve(*sym)),
        Value::Surface(SurfaceKind::Text, bytes) => from_json(&String::from_utf8_lossy(bytes)),
        _ => Vec::new(),
    }
}

/// Evaluate `StrokeRender`. See `TermNode::StrokeRender`'s doc
/// (`term.rs`) for the full field-by-field semantics — the exact
/// generative inverse of `eval_stroke_quantize`.
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_stroke_render(
    arena: &TermArena,
    signature_idx: TermIdx,
    n_points: i64,
    apply_pose: bool,
    turn_bins: i64,
    len_bins: i64,
    grid: i64,
    scale_bins: i64,
    turn_edges_idx: Option<TermIdx>,
    len_edges_idx: Option<TermIdx>,
    bounds_idx: Option<TermIdx>,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let sig_val = evaluate(arena, signature_idx, env, ctx);
    let relations = read_relations(&sig_val, ctx.interner);

    let turn_bins = turn_bins.max(1);
    let len_bins = len_bins.max(1);
    let grid = grid.max(1);
    let scale_bins = scale_bins.max(1);
    let n_points = n_points.max(1);

    // RUN 32 -- ADAPTIVE EDGES, the render-side twin of `eval_stroke_quantize`'s own
    // resolution (see that function's doc): a caller round-tripping an adaptively-
    // quantized signature must pass the SAME edges here.
    let turn_edges: Option<Vec<f64>> =
        turn_edges_idx.and_then(|idx| read_edges(&evaluate(arena, idx, env, ctx)));
    let len_edges: Option<Vec<f64>> =
        len_edges_idx.and_then(|idx| read_edges(&evaluate(arena, idx, env, ctx)));
    let turn_center = |q: i64| -> f64 {
        match &turn_edges {
            Some(e) => edge_bin_center(q, e),
            None => angle_bin_center(q, turn_bins),
        }
    };
    let len_center = |q: i64| -> f64 {
        match &len_edges {
            Some(e) => edge_bin_center(q, e),
            None => bucket_center(q, 0.0, 1.0, len_bins),
        }
    };

    // Collect `seg` relations (ordinal, turn_q, len_q — trailing slots,
    // e.g. the design doc's arity-5 padding, are ignored) and the four
    // pose scalars, by predicate name.
    let mut segs: Vec<(i64, i64, i64)> = Vec::new();
    let mut pose_x_q: Option<i64> = None;
    let mut pose_y_q: Option<i64> = None;
    let mut pose_o_q: Option<i64> = None;
    let mut pose_s_q: Option<i64> = None;
    for (pred, args) in &relations {
        match (pred.as_str(), args.as_slice()) {
            ("seg", [i, turn_q, len_q, ..]) => {
                segs.push((i.round() as i64, turn_q.round() as i64, len_q.round() as i64));
            }
            ("pose_x", [x, ..]) => pose_x_q = Some(x.round() as i64),
            ("pose_y", [y, ..]) => pose_y_q = Some(y.round() as i64),
            ("pose_o", [o, ..]) => pose_o_q = Some(o.round() as i64),
            ("pose_s", [s, ..]) => pose_s_q = Some(s.round() as i64),
            _ => {}
        }
    }
    segs.sort_by_key(|&(i, _, _)| i);
    let n = segs.len();

    if n == 0 {
        // Degenerate: no seg relations at all — graceful empty Dict,
        // never a panic (mirrors eval_stroke_quantize's degenerate arm).
        let result = Value::Dict(Arc::from(vec![
            (surf("points"), Value::Tuple(Arc::new(SmallVec::new()))),
            (surf("n_strokes"), Value::Int(1)),
            (surf("arc_len"), Value::Float(0.0)),
        ]));
        return finish(result, field, ctx.interner);
    }

    let have_pose = pose_x_q.is_some() && pose_y_q.is_some() && pose_o_q.is_some() && pose_s_q.is_some();
    let use_pose = apply_pose && have_pose;

    let (start_x, start_y, heading0, arc_len) = if use_pose {
        let bounds = bounds_idx.and_then(|idx| read_bounds(&evaluate(arena, idx, env, ctx)));
        // Documented limitation (mirrors StrokeQuantize's self-bbox
        // note): there is no point set yet at RENDER time to derive a
        // bbox from, so an absent `bounds` falls back to a canonical
        // [0, grid) unit frame rather than an unrecoverable self-bbox.
        // A caller that cares about posed position must pass the SAME
        // `bounds` to both StrokeQuantize and StrokeRender.
        let (bx0, by0, bx1, by1) = bounds.unwrap_or((0.0, 0.0, grid as f64, grid as f64));
        let sx = bucket_center(pose_x_q.unwrap(), bx0, bx1, grid);
        let sy = bucket_center(pose_y_q.unwrap(), by0, by1, grid);
        let h0 = turn_center(pose_o_q.unwrap());
        let log_scale = bucket_center(pose_s_q.unwrap(), -4.0, 4.0, scale_bins);
        (sx, sy, h0, 2f64.powf(log_scale))
    } else {
        // Canonical pose: start origin, initial heading 0, arc length 1
        // — StrokeQuantize's own `canonical_pose` codebook-entry
        // convention.
        (0.0, 0.0, 0.0, 1.0)
    };

    // Integrate headings: segment 0 starts at heading0 (its own turn_q
    // is, BY StrokeQuantize's definition, always 0 and carries no
    // information); each subsequent segment adds its turn_q's bin-
    // center angle to the running heading (no wrapping needed for the
    // running total — only the per-step delta is a wrapped bin center;
    // cos/sin are periodic so an unwrapped cumulative sum is exact).
    let mut headings = vec![0.0f64; n];
    headings[0] = heading0;
    for i in 1..n {
        headings[i] = headings[i - 1] + turn_center(segs[i].1);
    }
    let mut lengths = vec![0.0f64; n];
    for (i, len) in lengths.iter_mut().enumerate() {
        *len = len_center(segs[i].2) * arc_len;
    }

    // Exact geometric knots (n+1 points) from the integrated headings +
    // lengths — StrokeQuantize's resample-by-arclength "sample" step,
    // run in reverse ("generate" instead of "measure").
    let mut knots: Vec<(f64, f64)> = Vec::with_capacity(n + 1);
    knots.push((start_x, start_y));
    for i in 0..n {
        let rad = headings[i].to_radians();
        let &(px, py) = knots.last().unwrap();
        knots.push((px + lengths[i] * rad.cos(), py + lengths[i] * rad.sin()));
    }

    // "integrate headings to a polyline of n_points via arc-length
    // stepping" — reuse the SAME resample_by_arclength StrokeQuantize
    // uses forward, so a caller controlling both `n_points` and
    // `segments` can make this step introduce zero corner-cutting (see
    // the round-trip gate test for the exact reasoning). Degenerate
    // fallback (e.g. a canonical zero-length knot set) returns the raw
    // knots rather than panicking.
    let out_points = resample_by_arclength(&knots, (n_points - 1).max(1))
        .map(|(pts, _)| pts)
        .unwrap_or(knots);

    let points_val: SmallVec<[Value; 4]> = out_points
        .iter()
        .map(|&(x, y)| Value::Tuple(Arc::new(smallvec::smallvec![Value::Float(x), Value::Float(y)])))
        .collect();

    let result = Value::Dict(Arc::from(vec![
        (surf("points"), Value::Tuple(Arc::new(points_val))),
        (surf("n_strokes"), Value::Int(1)),
        (surf("arc_len"), Value::Float(arc_len)),
    ]));
    finish(result, field, ctx.interner)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::{NodeID, TypedGraph};
    use crate::term::TermNode;
    use rustc_hash::FxHashMap;

    // --- test-only construction helpers ---

    fn pt(x: f64, y: f64) -> Value {
        Value::Tuple(Arc::new(smallvec::smallvec![Value::Float(x), Value::Float(y)]))
    }

    fn points_value(pts: &[(f64, f64)]) -> Value {
        let v: SmallVec<[Value; 4]> = pts.iter().map(|&(x, y)| pt(x, y)).collect();
        Value::Tuple(Arc::new(v))
    }

    /// The five fixed predicate sentinels a `StrokeQuantize` Term needs
    /// interned at construction time (mirrors `AntiUnify`'s `wild` —
    /// see this module's doc).
    struct Syms {
        seg: Sym,
        px: Sym,
        py: Sym,
        po: Sym,
        ps: Sym,
    }

    fn syms(ir: &mut Interner) -> Syms {
        Syms {
            seg: ir.intern("seg"),
            px: ir.intern("pose_x"),
            py: ir.intern("pose_y"),
            po: ir.intern("pose_o"),
            ps: ir.intern("pose_s"),
        }
    }

    #[allow(clippy::too_many_arguments)]
    fn build_term_modes(
        a: &mut TermArena,
        ir: &mut Interner,
        s: &Syms,
        points: &[(f64, f64)],
        segments: i64,
        turn_bins: i64,
        len_bins: i64,
        grid: i64,
        scale_bins: i64,
        invariant_only: bool,
        canonical_pose: bool,
        bounds: Option<(f64, f64, f64, f64)>,
        field: &str,
    ) -> TermIdx {
        let points_t = a.add(TermNode::Lit { value: points_value(points) });
        let bounds_t = bounds.map(|(x0, y0, x1, y1)| {
            let v = Value::Tuple(Arc::new(smallvec::smallvec![
                Value::Float(x0),
                Value::Float(y0),
                Value::Float(x1),
                Value::Float(y1)
            ]));
            a.add(TermNode::Lit { value: v })
        });
        let field_sym = if field.is_empty() { Sym::default() } else { ir.intern(field) };
        a.add(TermNode::StrokeQuantize {
            points: points_t,
            segments,
            turn_bins,
            len_bins,
            grid,
            scale_bins,
            invariant_only,
            canonical_pose,
            turn_edges: None,
            len_edges: None,
            emit_residual: false,
            bounds: bounds_t,
            field: field_sym,
            seg_sym: s.seg,
            pose_x_sym: s.px,
            pose_y_sym: s.py,
            pose_o_sym: s.po,
            pose_s_sym: s.ps,
        })
    }

    /// `build_term_modes` with `canonical_pose: false` — the shape the
    /// pre-`canonical_pose` tests were written against.
    #[allow(clippy::too_many_arguments)]
    fn build_term(
        a: &mut TermArena,
        ir: &mut Interner,
        s: &Syms,
        points: &[(f64, f64)],
        segments: i64,
        turn_bins: i64,
        len_bins: i64,
        grid: i64,
        scale_bins: i64,
        invariant_only: bool,
        bounds: Option<(f64, f64, f64, f64)>,
        field: &str,
    ) -> TermIdx {
        build_term_modes(a, ir, s, points, segments, turn_bins, len_bins, grid, scale_bins,
                         invariant_only, false, bounds, field)
    }

    fn run(a: &TermArena, idx: TermIdx, g: &TypedGraph, ir: &Interner) -> Value {
        let mut env: Env = Env::new();
        let mut ctx = EvalCtx::new(g, ir);
        evaluate(a, idx, &mut env, &mut ctx)
    }

    fn rotate(pts: &[(f64, f64)], deg: f64, about: (f64, f64)) -> Vec<(f64, f64)> {
        let r = deg.to_radians();
        let (c, si) = (r.cos(), r.sin());
        pts.iter()
            .map(|&(x, y)| {
                let (dx, dy) = (x - about.0, y - about.1);
                (about.0 + dx * c - dy * si, about.1 + dx * si + dy * c)
            })
            .collect()
    }

    fn translate(pts: &[(f64, f64)], dx: f64, dy: f64) -> Vec<(f64, f64)> {
        pts.iter().map(|&(x, y)| (x + dx, y + dy)).collect()
    }

    fn scale(pts: &[(f64, f64)], k: f64, about: (f64, f64)) -> Vec<(f64, f64)> {
        pts.iter().map(|&(x, y)| (about.0 + (x - about.0) * k, about.1 + (y - about.1) * k)).collect()
    }

    /// An "L": right then up, 2 segments, headings 0° then 90° (a clean
    /// +90° relative turn, safely inside any bin width we use in these
    /// tests).
    fn l_stroke() -> Vec<(f64, f64)> {
        vec![(0.0, 0.0), (1.0, 0.0), (1.0, 1.0)]
    }

    /// A quarter-circle arc (densely sampled) — same start/end bbox
    /// footprint scale as the L, but a smooth curving turn profile
    /// instead of one sharp corner.
    fn curved_stroke() -> Vec<(f64, f64)> {
        let n = 24;
        (0..=n)
            .map(|i| {
                let t = (i as f64) / (n as f64) * std::f64::consts::FRAC_PI_2;
                (t.sin(), 1.0 - t.cos())
            })
            .collect()
    }

    fn dict_get(v: &Value, key: &str) -> Value {
        select_field(v, key)
    }

    fn sig_len(v: &Value) -> usize {
        match v {
            Value::Tuple(t) | Value::List(t) => t.len(),
            _ => 0,
        }
    }

    // --- (1) invariance ---

    /// An L-stroke rotated 37°, scaled ×2.3, then translated — the
    /// INVARIANT (`invariant_only`) seg relations must be IDENTICAL to
    /// the untransformed stroke's. The FULL signature's `pose_o` must
    /// differ (the rotation is visible there); `pose_x`/`pose_y`/
    /// `pose_s` are also free to differ here because no external
    /// `bounds` is given — position/scale are read relative to the
    /// point-set's OWN bbox, which itself rotates/scales/translates
    /// with the stroke (the documented self-bbox limitation).
    #[test]
    fn invariance_under_rotation_translation_scale() {
        let mut ir = Interner::new();
        let s = syms(&mut ir);
        let base = l_stroke();
        let transformed = {
            let r = rotate(&base, 37.0, (0.0, 0.0));
            let sc = scale(&r, 2.3, (0.0, 0.0));
            translate(&sc, 5.0, -3.0)
        };
        let g = TypedGraph::new();

        let mut a1 = TermArena::new();
        let t1 = build_term(&mut a1, &mut ir, &s, &base, 2, 16, 8, 8, 8, true, None, "signature");
        let sig1 = run(&a1, t1, &g, &ir);

        let mut a2 = TermArena::new();
        let t2 = build_term(&mut a2, &mut ir, &s, &transformed, 2, 16, 8, 8, 8, true, None, "signature");
        let sig2 = run(&a2, t2, &g, &ir);

        assert_eq!(sig1, sig2, "invariant seg relations must be IDENTICAL under rotate+scale+translate");

        let mut a3 = TermArena::new();
        let t3 = build_term(&mut a3, &mut ir, &s, &base, 2, 16, 8, 8, 8, false, None, "pose");
        let pose1 = run(&a3, t3, &g, &ir);
        let mut a4 = TermArena::new();
        let t4 = build_term(&mut a4, &mut ir, &s, &transformed, 2, 16, 8, 8, 8, false, None, "pose");
        let pose2 = run(&a4, t4, &g, &ir);
        assert_ne!(
            dict_get(&pose1, "orient_q"),
            dict_get(&pose2, "orient_q"),
            "rotation must change orient_q"
        );
    }

    // --- (2) invariant_only omits pose relations ---

    #[test]
    fn invariant_only_omits_pose_relations() {
        let mut ir = Interner::new();
        let s = syms(&mut ir);
        let g = TypedGraph::new();
        let pts = l_stroke();

        let mut a1 = TermArena::new();
        let t1 = build_term(&mut a1, &mut ir, &s, &pts, 2, 16, 8, 8, 8, true, None, "signature");
        let sig_inv = run(&a1, t1, &g, &ir);
        assert_eq!(sig_len(&sig_inv), 2, "2 segments, zero pose relations");

        let mut a2 = TermArena::new();
        let t2 = build_term(&mut a2, &mut ir, &s, &pts, 2, 16, 8, 8, 8, false, None, "signature");
        let sig_full = run(&a2, t2, &g, &ir);
        assert_eq!(sig_len(&sig_full), 6, "2 seg + 4 pose relations");
    }

    // --- (3) determinism / round-trip via jsonio ---

    /// The exact JSON invocation shape a seed rule would author, parsed
    /// via `jsonio::term_from_json` then evaluated — proves the schema
    /// documented in `HANDWRITING_DESIGN.md` parses cleanly and produces
    /// the SAME result as the directly-built Term (determinism: same
    /// input, same output, both construction paths agree).
    #[test]
    fn json_round_trip_parses_and_evaluates_deterministically() {
        let mut ir = Interner::new();
        let s = syms(&mut ir);
        let g = TypedGraph::new();
        let pts = l_stroke();

        let mut direct_arena = TermArena::new();
        let direct_term = build_term(&mut direct_arena, &mut ir, &s, &pts, 2, 16, 8, 8, 8, false, None, "");
        let direct_result = run(&direct_arena, direct_term, &g, &ir);

        let term_json = serde_json::json!({
            "type": "StrokeQuantize",
            "points": {"type": "Lit", "value": [[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]]},
            "segments": 2,
            "turn_bins": 16,
            "len_bins": 8,
            "grid": 8,
            "scale_bins": 8,
            "invariant_only": false
        });
        let mut json_arena = TermArena::new();
        let json_term = crate::jsonio::term_from_json(&term_json, &mut json_arena, &mut ir)
            .expect("StrokeQuantize JSON schema must parse");
        let json_result = run(&json_arena, json_term, &g, &ir);

        assert_eq!(direct_result, json_result, "direct construction and JSON parse must agree");

        // Re-running the SAME JSON term a second time (fresh arena/
        // interner) must produce byte-identical output — determinism.
        let mut ir2 = Interner::new();
        let mut json_arena2 = TermArena::new();
        let json_term2 = crate::jsonio::term_from_json(&term_json, &mut json_arena2, &mut ir2).unwrap();
        let g2 = TypedGraph::new();
        let json_result2 = run(&json_arena2, json_term2, &g2, &ir2);
        // Compare via re-encoding through each term's own interner
        // (Syms differ numerically across separate Interner instances,
        // so compare the human-readable JSON forms instead of the raw
        // Values).
        let enc1 = crate::persist::encode_value(&json_result, &ir);
        let enc2 = crate::persist::encode_value(&json_result2, &ir2);
        assert_eq!(enc1, enc2, "re-parsing the same JSON must be fully deterministic");
    }

    // --- (4) curved vs straight turn profile ---

    #[test]
    fn curved_stroke_has_different_turn_profile_than_straight() {
        let mut ir = Interner::new();
        let s = syms(&mut ir);
        let g = TypedGraph::new();

        let mut a1 = TermArena::new();
        let t1 = build_term(&mut a1, &mut ir, &s, &l_stroke(), 6, 16, 8, 8, 8, true, None, "signature");
        let sig_l = run(&a1, t1, &g, &ir);

        let mut a2 = TermArena::new();
        let t2 = build_term(&mut a2, &mut ir, &s, &curved_stroke(), 6, 16, 8, 8, 8, true, None, "signature");
        let sig_curve = run(&a2, t2, &g, &ir);

        assert_ne!(sig_l, sig_curve, "a sharp-corner L and a smooth arc must quantize to different turn profiles");
    }

    // --- (5) segments/turn_bins params honored ---

    #[test]
    fn segment_and_bin_params_change_output_shape() {
        let mut ir = Interner::new();
        let s = syms(&mut ir);
        let g = TypedGraph::new();
        let pts = curved_stroke();

        let mut a4 = TermArena::new();
        let t4 = build_term(&mut a4, &mut ir, &s, &pts, 4, 16, 8, 8, 8, true, None, "signature");
        let sig4 = run(&a4, t4, &g, &ir);
        assert_eq!(sig_len(&sig4), 4);

        let mut a10 = TermArena::new();
        let t10 = build_term(&mut a10, &mut ir, &s, &pts, 10, 16, 8, 8, 8, true, None, "signature");
        let sig10 = run(&a10, t10, &g, &ir);
        assert_eq!(sig_len(&sig10), 10, "different `segments` -> different relation COUNT");

        // Different `turn_bins` on the SAME curved stroke changes the
        // quantized turn values (coarser bins collapse distinctions a
        // fine grid preserves) — assert the two signatures differ.
        let mut a_coarse = TermArena::new();
        let t_coarse = build_term(&mut a_coarse, &mut ir, &s, &pts, 6, 4, 8, 8, 8, true, None, "signature");
        let sig_coarse = run(&a_coarse, t_coarse, &g, &ir);
        let mut a_fine = TermArena::new();
        let t_fine = build_term(&mut a_fine, &mut ir, &s, &pts, 6, 32, 8, 8, 8, true, None, "signature");
        let sig_fine = run(&a_fine, t_fine, &g, &ir);
        assert_ne!(sig_coarse, sig_fine, "different `turn_bins` must change the quantized turn values");
    }

    // --- (6) degenerate inputs ---

    #[test]
    fn degenerate_inputs_are_graceful_not_panics() {
        let g = TypedGraph::new();

        // Zero points.
        {
            let mut ir = Interner::new();
            let s = syms(&mut ir);
            let mut a = TermArena::new();
            let t = build_term(&mut a, &mut ir, &s, &[], 4, 16, 8, 8, 8, false, None, "");
            let result = run(&a, t, &g, &ir);
            assert_eq!(dict_get(&result, "n_points"), Value::Int(0));
            assert_eq!(sig_len(&dict_get(&result, "signature")), 0);
            assert_eq!(dict_get(&result, "arc_len"), Value::Float(0.0));
        }
        // One point.
        {
            let mut ir = Interner::new();
            let s = syms(&mut ir);
            let mut a = TermArena::new();
            let t = build_term(&mut a, &mut ir, &s, &[(1.0, 1.0)], 4, 16, 8, 8, 8, false, None, "");
            let result = run(&a, t, &g, &ir);
            assert_eq!(dict_get(&result, "n_points"), Value::Int(1));
            assert_eq!(sig_len(&dict_get(&result, "signature")), 0);
        }
        // Zero-length stroke: every point identical.
        {
            let mut ir = Interner::new();
            let s = syms(&mut ir);
            let mut a = TermArena::new();
            let pts = [(2.0, 2.0), (2.0, 2.0), (2.0, 2.0)];
            let t = build_term(&mut a, &mut ir, &s, &pts, 4, 16, 8, 8, 8, false, None, "");
            let result = run(&a, t, &g, &ir);
            assert_eq!(dict_get(&result, "n_points"), Value::Int(3));
            assert_eq!(sig_len(&dict_get(&result, "signature")), 0);
            assert_eq!(dict_get(&result, "arc_len"), Value::Float(0.0));
        }
    }
    // --- (7) THE LADDER HANDOFF ---
    //
    // Proves the design's central claim: a stroke quantized into the
    // ladder's own relation-system format lets `TransformDecode` read a
    // similarity transform back as per-dimension deltas, with ZERO
    // bespoke stroke-matching code.
    //
    // HISTORY (kept because the walls taught the conventions): the first
    // run of these gates, against the ORIGINAL raw-slot-uniform
    // `TransformDecode`, found two structural walls — (7a) an
    // invariant-only held signature can never be a candidate against a
    // full goal (relation-COUNT mismatch), and (7b/7c, since FIXED) the
    // old consistency check pooled every relation's slot-1 into ONE
    // dimension, so `seg`'s untouched ordinal slot vetoed `pose_o`'s
    // rotation delta. The fixes, in order: `canonical_pose` (the
    // codebook-entry form — full signature, pose at canonical zero, so
    // counts match and pose deltas ARE the transform) closed 7a's wall;
    // `build_candidate`'s two-tier (predicate, slot) pooling closed
    // 7b/7c's. Gate 7e is the headline: both fixes together, end to end.
    //
    // Fixed EXTERNAL `bounds` are used for the pose-carrying quantize
    // calls (a page/canvas frame) so translation is legible in
    // `pose_x`/`pose_y` (the self-bbox mode would make translation
    // invisible — see `TermNode::StrokeQuantize`'s doc).
    mod ladder_handoff {
        use super::*;

        fn add_stroke_part(g: &mut TypedGraph, ir: &mut Interner, t: Sym, name: &str, sig_json: &str) -> NodeID {
            let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
            attrs.insert(ir.intern("name"), Value::Str(ir.intern(name)));
            attrs.insert(ir.intern("kind"), Value::Str(ir.intern("stroke")));
            attrs.insert(ir.intern("signature"), Value::Str(ir.intern(sig_json)));
            g.insert_node(t, attrs)
        }

        /// Plain-array JSON encoder for a relation-system Value — NOT
        /// `persist::encode_value` (which tags Tuples as `{"__tuple__":
        /// ...}`; `shape_decode::json_to_value_scoped` only understands
        /// bare nested arrays for relation-systems, matching what a
        /// Python `json.dumps([[...], ...])` builder emits). Test-only.
        fn value_to_plain_json(v: &Value, ir: &Interner) -> serde_json::Value {
            use serde_json::Value as J;
            match v {
                Value::None => J::Null,
                Value::Bool(b) => J::Bool(*b),
                Value::Int(n) => J::Number((*n).into()),
                Value::Float(f) => serde_json::Number::from_f64(*f).map(J::Number).unwrap_or(J::Null),
                Value::Str(sym) => J::String(ir.resolve(*sym).to_string()),
                Value::Tuple(items) | Value::List(items) => J::Array(items.iter().map(|it| value_to_plain_json(it, ir)).collect()),
                _ => J::Null,
            }
        }

        fn dims_as_ints(result: &Value) -> Vec<i64> {
            match dict_get(result, "dims") {
                Value::Tuple(t) | Value::List(t) => t.iter().filter_map(|v| match v {
                    Value::Int(i) => Some(*i),
                    _ => None,
                }).collect(),
                _ => Vec::new(),
            }
        }

        /// Collect `(pred_text_or_empty, dim, delta)` triples off a
        /// result's `transforms` — `pred` resolved through the interner
        /// (always a real Sym: it is taken from the OBSERVED relation's
        /// slot 0).
        fn transforms_summary(result: &Value, ir: &Interner) -> Vec<(String, i64, i64)> {
            let (Value::Tuple(ts) | Value::List(ts)) = dict_get(result, "transforms") else { return Vec::new() };
            ts.iter().map(|t| {
                let pred = match dict_get(t, "pred") {
                    Value::Str(s) => ir.resolve(s).to_string(),
                    _ => String::new(),
                };
                let dim = match dict_get(t, "dim") { Value::Int(i) => i, _ => -1 };
                let delta = match dict_get(t, "delta") { Value::Int(i) => i, _ => i64::MIN };
                (pred, dim, delta)
            }).collect()
        }

        const BOUNDS: (f64, f64, f64, f64) = (0.0, 0.0, 4.0, 4.0);
        const GRID: i64 = 8;
        const TURN_BINS: i64 = 16;

        /// An arc-length-1 "L" (right then up, 0.5 + 0.5): its
        /// `log2(arc_len) = 0`, i.e. the MEASURED `pose_s` bin equals
        /// the CANONICAL scale bin, so a rigid (non-scaling) transform
        /// leaves `pose_s` delta at exactly 0 — the fixture that keeps
        /// gate 7e's transform confined to `pose_o` + `pose_x` alone.
        fn unit_l_stroke() -> Vec<(f64, f64)> {
            vec![(0.0, 0.0), (0.5, 0.0), (0.5, 0.5)]
        }

        /// (7a) The count-mismatch wall, still real and still the honest
        /// result for THIS invocation shape: held = stroke A's
        /// INVARIANT-ONLY signature (no pose relations); goal = stroke
        /// A's FULL signature. `build_candidate` requires an exact
        /// relation-COUNT match (`segments` vs `segments + 4` never
        /// matches), so this is `explained: false` by construction — a
        /// structural mismatch, not a near-miss. `invariant_only` is the
        /// INVARIANT-COMPARISON form; the codebook-ENTRY form is
        /// `canonical_pose` (gate 7e), which is what closes this wall.
        #[test]
        fn gate7a_literal_invariant_held_vs_full_goal() {
            let mut ir = Interner::new();
            let s = syms(&mut ir);
            let stroke_a = l_stroke();

            let mut inv_arena = TermArena::new();
            let g0 = TypedGraph::new();
            let inv_term = build_term(&mut inv_arena, &mut ir, &s, &stroke_a, 2, TURN_BINS, 8, GRID, 8, true, Some(BOUNDS), "signature");
            let inv_sig = run(&inv_arena, inv_term, &g0, &ir);
            let inv_json = serde_json::to_string(&value_to_plain_json(&inv_sig, &ir)).unwrap();

            let mut g = TypedGraph::new();
            let t_type = ir.intern("ShapeSignature");
            add_stroke_part(&mut g, &mut ir, t_type, "StrokeA", &inv_json);

            let bin_deg = 360.0 / TURN_BINS as f64;
            let cell_w = (BOUNDS.2 - BOUNDS.0) / GRID as f64;
            let rotated = rotate(&stroke_a, bin_deg, stroke_a[0]);
            let transformed = translate(&rotated, cell_w, 0.0);

            let mut goal_arena = TermArena::new();
            let goal_term = build_term(&mut goal_arena, &mut ir, &s, &transformed, 2, TURN_BINS, 8, GRID, 8, false, Some(BOUNDS), "signature");

            let td = goal_arena.add(TermNode::TransformDecode {
                goal: goal_term,
                codebook_type: t_type,
                exclude: None,
                max_dims: 4,
                field: Sym::default(),
            });
            let result = run(&goal_arena, td, &g, &ir);

            assert_eq!(dict_get(&result, "explained"), Value::Bool(false),
                "count-mismatched held (invariant-only) vs full goal is NOT a TransformDecode candidate at all");
            assert_eq!(dict_get(&result, "checked"), Value::Int(1));
        }

        /// (7b) Matched relation counts, FULL measured pose held: held =
        /// stroke A's full signature (measured pose, untransformed);
        /// goal = the same stroke rotated one turn_bin quantum (about
        /// its own start) + translated one grid cell.
        ///
        /// ORIGINALLY (raw-slot-uniform `TransformDecode`) this FAILED:
        /// every arity-2 pose relation's payload and `seg`'s ordinal
        /// slot all pooled into one global slot-1 dimension, and `seg`'s
        /// zero delta vetoed `pose_o`/`pose_x`'s +1. The two-tier
        /// (predicate, slot) pooling fix makes the zero-delta groups
        /// (`seg`, `pose_y`, `pose_s`) budget-free non-transforms, and
        /// the two nonzero groups each their own `pred`-keyed dimension
        /// — explained, seg relations untransformed.
        #[test]
        fn gate7b_matched_counts_explained_via_predicate_pooling() {
            let mut ir = Interner::new();
            let s = syms(&mut ir);
            let stroke_a = l_stroke();

            let mut full_arena = TermArena::new();
            let g0 = TypedGraph::new();
            let full_term = build_term(&mut full_arena, &mut ir, &s, &stroke_a, 2, TURN_BINS, 8, GRID, 8, false, Some(BOUNDS), "signature");
            let full_sig = run(&full_arena, full_term, &g0, &ir);
            let full_json = serde_json::to_string(&value_to_plain_json(&full_sig, &ir)).unwrap();

            let mut g = TypedGraph::new();
            let t_type = ir.intern("ShapeSignature");
            add_stroke_part(&mut g, &mut ir, t_type, "StrokeA", &full_json);

            let bin_deg = 360.0 / TURN_BINS as f64;
            let cell_w = (BOUNDS.2 - BOUNDS.0) / GRID as f64;
            let rotated = rotate(&stroke_a, bin_deg, stroke_a[0]);
            let transformed = translate(&rotated, cell_w, 0.0);

            let mut goal_arena = TermArena::new();
            let goal_term = build_term(&mut goal_arena, &mut ir, &s, &transformed, 2, TURN_BINS, 8, GRID, 8, false, Some(BOUNDS), "signature");
            let td = goal_arena.add(TermNode::TransformDecode {
                goal: goal_term,
                codebook_type: t_type,
                exclude: None,
                max_dims: 4,
                field: Sym::default(),
            });
            let result = run(&goal_arena, td, &g, &ir);

            assert_eq!(dict_get(&result, "explained"), Value::Bool(true),
                "predicate-aware pooling: seg's zero-delta slot-1 group no longer vetoes pose_o/pose_x");
            assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("StrokeA")));
            assert_eq!(dims_as_ints(&result), vec![1, 1], "two split dimensions sharing local slot index 1");
            let summary = transforms_summary(&result, &ir);
            assert_eq!(summary, vec![
                ("pose_x".to_string(), 1, 1),
                ("pose_o".to_string(), 1, 1),
            ], "exactly the pose_x (+1 cell) and pose_o (+1 bin) pred-keyed deltas, in canonical sort order");
        }

        /// (7c) Pose relations alone (no `seg`), `pose_o` + `pose_x`
        /// shifting while `pose_y`/`pose_s` stay put. Originally failed
        /// for the same cross-relation slot-1 collision as 7b (the
        /// zero-delta `pose_y`/`pose_s` groups vetoed); now explained
        /// with two `pred`-keyed dimensions.
        #[test]
        fn gate7c_pose_only_explained_via_predicate_pooling() {
            let mut ir = Interner::new();
            let px = ir.intern("pose_x");
            let py = ir.intern("pose_y");
            let po = ir.intern("pose_o");
            let ps = ir.intern("pose_s");
            let rel = |p: Sym, v: i64| Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(p), Value::Int(v)]));

            let held = Value::Tuple(Arc::new(smallvec::smallvec![
                rel(px, 0), rel(py, 0), rel(po, 0), rel(ps, 3),
            ]));
            let goal = Value::Tuple(Arc::new(smallvec::smallvec![
                rel(px, 1), rel(py, 0), rel(po, 1), rel(ps, 3),
            ]));

            let mut g = TypedGraph::new();
            let t_type = ir.intern("ShapeSignature");
            let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
            attrs.insert(ir.intern("name"), Value::Str(ir.intern("PoseOnly")));
            attrs.insert(ir.intern("kind"), Value::Str(ir.intern("stroke")));
            attrs.insert(ir.intern("signature"), held);
            g.insert_node(t_type, attrs);

            let mut a = TermArena::new();
            let goal_t = a.add(TermNode::Lit { value: goal });
            let td = a.add(TermNode::TransformDecode {
                goal: goal_t,
                codebook_type: t_type,
                exclude: None,
                max_dims: 4,
                field: Sym::default(),
            });
            let result = run(&a, td, &g, &ir);

            assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
            assert_eq!(dims_as_ints(&result), vec![1, 1]);
            let summary = transforms_summary(&result, &ir);
            assert_eq!(summary, vec![
                ("pose_x".to_string(), 1, 1),
                ("pose_o".to_string(), 1, 1),
            ]);
        }

        /// (7d) Single relation type only: tier-1 global uniformity
        /// holds, so the entry stays the committed un-keyed
        /// `{dim,kind,delta}` shape — no `pred` key (output
        /// compatibility: the split machinery engages ONLY when the
        /// global check fails).
        #[test]
        fn gate7d_single_relation_type_stays_unkeyed_tier1() {
            let mut ir = Interner::new();
            let po = ir.intern("pose_o");
            let rel = |p: Sym, v: i64| Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(p), Value::Int(v)]));

            let held = Value::Tuple(Arc::new(smallvec::smallvec![rel(po, 0)]));
            let goal = Value::Tuple(Arc::new(smallvec::smallvec![rel(po, 1)]));

            let mut g = TypedGraph::new();
            let t_type = ir.intern("ShapeSignature");
            let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
            attrs.insert(ir.intern("name"), Value::Str(ir.intern("OrientOnly")));
            attrs.insert(ir.intern("kind"), Value::Str(ir.intern("stroke")));
            attrs.insert(ir.intern("signature"), held);
            g.insert_node(t_type, attrs);

            let mut a = TermArena::new();
            let goal_t = a.add(TermNode::Lit { value: goal });
            let td = a.add(TermNode::TransformDecode {
                goal: goal_t,
                codebook_type: t_type,
                exclude: None,
                max_dims: 4,
                field: Sym::default(),
            });
            let result = run(&a, td, &g, &ir);

            assert_eq!(dict_get(&result, "explained"), Value::Bool(true));
            assert_eq!(dims_as_ints(&result), vec![1]);
            let summary = transforms_summary(&result, &ir);
            assert_eq!(summary, vec![(String::new(), 1, 1)], "tier-1 entry carries NO pred key");
        }

        /// (7e) THE HEADLINE GATE — the design's central claim, end to
        /// end with the codebook convention: held = `canonical_pose`
        /// signature of stroke A (full relation count, pose at canonical
        /// zero — `pose_x 0 / pose_y 0 / pose_o 0 / pose_s 4`, the bin
        /// containing log2(arc_len)=0), stored as a JSON string on a
        /// ShapeSignature/"stroke" node; goal = FULL measured signature
        /// of stroke A rotated one turn_bin quantum about its start +
        /// translated one grid cell in x. The fixture stroke has arc
        /// length exactly 1 (`unit_l_stroke`) so the rigid transform
        /// leaves the measured `pose_s` at the canonical bin (delta 0),
        /// and starts at the bounds origin so the canonical position
        /// bins are also the measured pre-transform ones.
        ///
        /// Expected — and CONFIRMED: `explained: true`; `transforms` =
        /// exactly the `pose_x` (+1 cell) and `pose_o` (+1 bin)
        /// `pred`-keyed deltas; every `seg` relation untransformed (no
        /// entry touches dims 2/3, no seg pred appears); zero residual.
        /// An observed stroke's pose deltas against the canonical
        /// codebook entry ARE the rung-1 transform.
        #[test]
        fn gate7e_canonical_codebook_entry_reads_transform_as_pose_deltas() {
            let mut ir = Interner::new();
            let s = syms(&mut ir);
            let stroke_a = unit_l_stroke();

            // Held: canonical-pose signature (codebook-entry form).
            let mut canon_arena = TermArena::new();
            let g0 = TypedGraph::new();
            let canon_term = build_term_modes(&mut canon_arena, &mut ir, &s, &stroke_a, 2, TURN_BINS, 8, GRID, 8,
                                              false, true, Some(BOUNDS), "signature");
            let canon_sig = run(&canon_arena, canon_term, &g0, &ir);
            let canon_json = serde_json::to_string(&value_to_plain_json(&canon_sig, &ir)).unwrap();
            // Pin the canonical convention itself: pose_s at bin 4 (=
            // scale_bins/2, the bin containing log2 arc_len = 0).
            assert!(canon_json.contains("[\"pose_s\",4]"), "canonical scale bin must be 4 for scale_bins=8, got {canon_json}");
            assert!(canon_json.contains("[\"pose_x\",0]") && canon_json.contains("[\"pose_y\",0]") && canon_json.contains("[\"pose_o\",0]"));

            let mut g = TypedGraph::new();
            let t_type = ir.intern("ShapeSignature");
            add_stroke_part(&mut g, &mut ir, t_type, "StrokeA", &canon_json);

            // Goal: rotate ONE turn-bin quantum about the start point
            // (start unchanged -> pose_x/pose_y see only the
            // translation), then translate ONE grid cell in x.
            let bin_deg = 360.0 / TURN_BINS as f64;                  // 22.5 deg
            let cell_w = (BOUNDS.2 - BOUNDS.0) / GRID as f64;        // 0.5
            let rotated = rotate(&stroke_a, bin_deg, stroke_a[0]);
            let transformed = translate(&rotated, cell_w, 0.0);

            let mut goal_arena = TermArena::new();
            let goal_term = build_term(&mut goal_arena, &mut ir, &s, &transformed, 2, TURN_BINS, 8, GRID, 8,
                                       false, Some(BOUNDS), "signature");
            let td = goal_arena.add(TermNode::TransformDecode {
                goal: goal_term,
                codebook_type: t_type,
                exclude: None,
                max_dims: 4,
                field: Sym::default(),
            });
            let result = run(&goal_arena, td, &g, &ir);

            assert_eq!(dict_get(&result, "explained"), Value::Bool(true),
                "the central claim: a similarity transform IS rung-1 pose-dimension deltas");
            assert_eq!(dict_get(&result, "base"), Value::Str(ir.intern("StrokeA")));
            assert_eq!(dict_get(&result, "identity"), Value::Bool(false));
            assert_eq!(dict_get(&result, "residual_unexplained"), Value::Tuple(Arc::new(SmallVec::new())));
            assert_eq!(dims_as_ints(&result), vec![1, 1]);
            let summary = transforms_summary(&result, &ir);
            assert_eq!(summary, vec![
                ("pose_x".to_string(), 1, 1),
                ("pose_o".to_string(), 1, 1),
            ], "exactly pose_x (+1 grid cell) and pose_o (+1 turn bin), pred-keyed; seg untransformed");
        }

        /// (7f) Negative control on the new convention: the UNROTATED,
        /// UNTRANSLATED unit stroke decodes against its own canonical
        /// entry as IDENTITY (measured pose == canonical pose at the
        /// origin fixture) — not a transform, `identity: true`, the
        /// `sd_recognize` case.
        #[test]
        fn gate7f_untransformed_stroke_is_identity_against_canonical_entry() {
            let mut ir = Interner::new();
            let s = syms(&mut ir);
            let stroke_a = unit_l_stroke();

            let mut canon_arena = TermArena::new();
            let g0 = TypedGraph::new();
            let canon_term = build_term_modes(&mut canon_arena, &mut ir, &s, &stroke_a, 2, TURN_BINS, 8, GRID, 8,
                                              false, true, Some(BOUNDS), "signature");
            let canon_sig = run(&canon_arena, canon_term, &g0, &ir);
            let canon_json = serde_json::to_string(&value_to_plain_json(&canon_sig, &ir)).unwrap();

            let mut g = TypedGraph::new();
            let t_type = ir.intern("ShapeSignature");
            add_stroke_part(&mut g, &mut ir, t_type, "StrokeA", &canon_json);

            let mut goal_arena = TermArena::new();
            let goal_term = build_term(&mut goal_arena, &mut ir, &s, &stroke_a, 2, TURN_BINS, 8, GRID, 8,
                                       false, Some(BOUNDS), "signature");
            let td = goal_arena.add(TermNode::TransformDecode {
                goal: goal_term,
                codebook_type: t_type,
                exclude: None,
                max_dims: 4,
                field: Sym::default(),
            });
            let result = run(&goal_arena, td, &g, &ir);

            assert_eq!(dict_get(&result, "explained"), Value::Bool(false), "identity is sd_recognize's case, not a transform");
            assert_eq!(dict_get(&result, "identity"), Value::Bool(true));
        }
    }

    // --- (8) StrokeRender: StrokeQuantize's exact generative inverse ---
    //
    // "ABS AS DEFAULT" (`HANDWRITING_DESIGN.md`, 2026-07-03): "the
    // generation and reading model is the same ... it just runs the
    // same engine in reverse." Gate 8a is the headline, made checkable:
    // `StrokeQuantize(StrokeRender(sig)) == sig` EXACTLY.
    mod stroke_render {
        use super::*;

        const TURN_BINS: i64 = 16;
        const LEN_BINS: i64 = 8;
        const GRID: i64 = 8;
        const SCALE_BINS: i64 = 8;
        const BOUNDS: (f64, f64, f64, f64) = (0.0, 0.0, 8.0, 8.0);

        fn lit(a: &mut TermArena, v: Value) -> TermIdx {
            a.add(TermNode::Lit { value: v })
        }

        fn rel2(ir: &mut Interner, pred: &str, v: i64) -> Value {
            Value::Tuple(Arc::new(smallvec::smallvec![Value::Str(ir.intern(pred)), Value::Int(v)]))
        }

        fn seg_rel(ir: &mut Interner, i: i64, turn_q: i64, len_q: i64) -> Value {
            Value::Tuple(Arc::new(smallvec::smallvec![
                Value::Str(ir.intern("seg")), Value::Int(i), Value::Int(turn_q), Value::Int(len_q),
            ]))
        }

        /// A hand-built, bin-center-EXACT 2-segment signature: seg0
        /// (turn_q ignored by definition, len_q=3 -> fraction 0.4375),
        /// seg1 (turn_q=4 -> +90 deg, len_q=4 -> fraction 0.5625) — the
        /// two length fractions sum to EXACTLY 1.0, the constraint a
        /// uniform-arc-length re-chop needs for a byte-exact round trip
        /// (`StrokeQuantize`'s own resample is ALWAYS an equal-arc-
        /// length partition; feeding it a curve whose true total length
        /// doesn't match the fractions used to render it would recover
        /// DIFFERENT `len_q` values on the way back — see the round-trip
        /// gate's doc for the full derivation). Pose is caller-supplied
        /// so the same fixture serves both the strict round-trip gate
        /// (needs self-consistent, bin-center-exact pose) and the
        /// looser canonical-vs-posed transform gate (needs a NON-
        /// trivial rotation to actually exercise the rotation term).
        fn build_fixture_sig(ir: &mut Interner, x_q: i64, y_q: i64, o_q: i64, s_q: i64) -> Value {
            Value::Tuple(Arc::new(smallvec::smallvec![
                seg_rel(ir, 0, 0, 3),
                seg_rel(ir, 1, 4, 4),
                rel2(ir, "pose_x", x_q),
                rel2(ir, "pose_y", y_q),
                rel2(ir, "pose_o", o_q),
                rel2(ir, "pose_s", s_q),
            ]))
        }

        #[allow(clippy::too_many_arguments)]
        fn render_term(
            a: &mut TermArena,
            sig: TermIdx,
            n_points: i64,
            apply_pose: bool,
            turn_bins: i64,
            len_bins: i64,
            grid: i64,
            scale_bins: i64,
            bounds: Option<(f64, f64, f64, f64)>,
            field: &str,
            ir: &mut Interner,
        ) -> TermIdx {
            let bounds_t = bounds.map(|(x0, y0, x1, y1)| {
                lit(a, Value::Tuple(Arc::new(smallvec::smallvec![
                    Value::Float(x0), Value::Float(y0), Value::Float(x1), Value::Float(y1),
                ])))
            });
            let field_sym = if field.is_empty() { Sym::default() } else { ir.intern(field) };
            a.add(TermNode::StrokeRender {
                signature: sig, n_points, apply_pose, turn_bins, len_bins, grid, scale_bins,
                turn_edges: None, len_edges: None,
                bounds: bounds_t, field: field_sym,
            })
        }

        fn points_of(v: &Value) -> Vec<(f64, f64)> {
            match v {
                Value::Tuple(items) | Value::List(items) => items.iter().filter_map(|it| match it {
                    Value::Tuple(p) | Value::List(p) if p.len() >= 2 => Some((p[0].as_f64(), p[1].as_f64())),
                    _ => None,
                }).collect(),
                _ => Vec::new(),
            }
        }

        fn value_to_plain_json(v: &Value, ir: &Interner) -> serde_json::Value {
            use serde_json::Value as J;
            match v {
                Value::None => J::Null,
                Value::Bool(b) => J::Bool(*b),
                Value::Int(n) => J::Number((*n).into()),
                Value::Float(f) => serde_json::Number::from_f64(*f).map(J::Number).unwrap_or(J::Null),
                Value::Str(sym) => J::String(ir.resolve(*sym).to_string()),
                Value::Tuple(items) | Value::List(items) => J::Array(items.iter().map(|it| value_to_plain_json(it, ir)).collect()),
                _ => J::Null,
            }
        }

        /// (8a) THE ROUND-TRIP GATE — the design's central claim, made
        /// checkable: `StrokeQuantize(StrokeRender(sig)) == sig` EXACTLY
        /// for a bin-center-safe fixture, with `n_points = segments + 1`
        /// — the choice that makes the intermediate arc-length resample
        /// introduce ZERO corner-cutting.
        ///
        /// Getting this exact needs TWO fixture properties, not just
        /// one: the length fractions must sum to exactly 1.0 (so the
        /// rendered polyline's TRUE total arc length equals the nominal
        /// `arc_len` used to scale it) AND be EQUAL across segments (so
        /// `StrokeQuantize`'s own re-chop — ALWAYS an equal-arc-length
        /// partition, e.g. bisecting a 2-segment curve exactly at half
        /// its total length — lands its breakpoints back at the SAME
        /// knots `StrokeRender` generated, not part-way along a
        /// different segment). A first draft of this fixture used
        /// UNEQUAL fractions (0.4375/0.5625, still summing to 1) and
        /// failed non-obviously: the intermediate `n_points` resample's
        /// midpoint fell inside the SECOND segment (since the first
        /// segment's length was under half the total), silently
        /// relocating the rendered "corner" and recovering the wrong
        /// `turn_q`/`pose_o` — corner-cutting on an internal resample
        /// step, not a boundary/rounding issue. `len_bins=3`/`len_q=1`
        /// gives an EXACT `0.5` bin center ((1+0.5)/3), satisfying both
        /// properties for 2 equal segments.
        #[test]
        fn gate8a_round_trip_seg_and_pose_exact() {
            let mut ir = Interner::new();
            let s = syms(&mut ir);
            let len_bins = 3; // (1+0.5)/3 == 0.5 exactly -- see doc above.
            let sig = Value::Tuple(Arc::new(smallvec::smallvec![
                seg_rel(&mut ir, 0, 0, 1), // turn_q ignored; len fraction 0.5
                seg_rel(&mut ir, 1, 4, 1), // +90 deg; len fraction 0.5
                rel2(&mut ir, "pose_x", 2),
                rel2(&mut ir, "pose_y", 2),
                rel2(&mut ir, "pose_o", 0),
                rel2(&mut ir, "pose_s", 4),
            ]));
            let g = TypedGraph::new();

            let mut a1 = TermArena::new();
            let sig_t = lit(&mut a1, sig.clone());
            let render_t = render_term(&mut a1, sig_t, 3, true, TURN_BINS, len_bins, GRID, SCALE_BINS, Some(BOUNDS), "points", &mut ir);
            let rendered = run(&a1, render_t, &g, &ir);
            let pts = points_of(&rendered);
            assert_eq!(pts.len(), 3, "n_points = segments(2) + 1");

            let mut a2 = TermArena::new();
            let requant_t = build_term(&mut a2, &mut ir, &s, &pts, 2, TURN_BINS, len_bins, GRID, SCALE_BINS, false, Some(BOUNDS), "signature");
            let sig2 = run(&a2, requant_t, &g, &ir);

            assert_eq!(sig2, sig, "StrokeQuantize(StrokeRender(sig)) must recover sig EXACTLY at matching, bin-center-safe params");
        }

        /// (8b) Canonical vs posed render of the SAME signature differ
        /// by EXACTLY the pose similarity transform (rotate by the
        /// posed heading, scale by the posed arc length, translate to
        /// the posed start) — arc-length resampling commutes with a
        /// similarity transform, so this holds point-for-point. Uses a
        /// NON-trivial `pose_o` (45 deg) so the rotation term is
        /// actually exercised, unlike gate 8a's zero-rotation fixture.
        #[test]
        fn gate8b_canonical_vs_posed_differ_by_pose_transform() {
            let mut ir = Interner::new();
            let g = TypedGraph::new();

            let mut a1 = TermArena::new();
            let sig1 = build_fixture_sig(&mut ir, 3, 1, 2, 5);
            let sig_t1 = lit(&mut a1, sig1.clone());
            let canon_t = render_term(&mut a1, sig_t1, 6, false, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "", &mut ir);
            let canon = run(&a1, canon_t, &g, &ir);
            let canon_pts = points_of(&dict_get(&canon, "points"));
            assert_eq!(dict_get(&canon, "arc_len"), Value::Float(1.0), "canonical arc_len is always 1");

            let mut a2 = TermArena::new();
            let sig_t2 = lit(&mut a2, sig1);
            let posed_t = render_term(&mut a2, sig_t2, 6, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "", &mut ir);
            let posed = run(&a2, posed_t, &g, &ir);
            let posed_pts = points_of(&dict_get(&posed, "points"));
            let posed_arc_len = match dict_get(&posed, "arc_len") { Value::Float(f) => f, other => panic!("expected Float, got {other:?}") };

            // Expected transform, re-derived the SAME way eval_stroke_render
            // does (bucket_center / angle_bin_center) — duplicated here
            // deliberately, matching this file's existing gates (e.g.
            // `bin_deg`/`cell_w` in gate7e/7f).
            let cell_w = (BOUNDS.2 - BOUNDS.0) / GRID as f64;
            let start_x = BOUNDS.0 + (3.0 + 0.5) * cell_w;
            let start_y = BOUNDS.1 + (1.0 + 0.5) * cell_w;
            let heading0_deg = 2.0 * (360.0 / TURN_BINS as f64); // pose_o q=2 -> 45 deg
            let log_scale = -4.0 + (5.0 + 0.5) * (8.0 / SCALE_BINS as f64);
            let arc_len = 2f64.powf(log_scale);
            assert!((posed_arc_len - arc_len).abs() < 1e-9, "posed arc_len must match the pose_s bin center");

            assert_eq!(canon_pts.len(), posed_pts.len());
            let rad = heading0_deg.to_radians();
            for (c, p) in canon_pts.iter().zip(posed_pts.iter()) {
                let ex = start_x + arc_len * (c.0 * rad.cos() - c.1 * rad.sin());
                let ey = start_y + arc_len * (c.0 * rad.sin() + c.1 * rad.cos());
                assert!((p.0 - ex).abs() < 1e-9, "posed x mismatch: got {:?}, expected ({ex},{ey})", p);
                assert!((p.1 - ey).abs() < 1e-9, "posed y mismatch: got {:?}, expected ({ex},{ey})", p);
            }
        }

        /// (8c) Degenerate signatures render gracefully — never a panic.
        #[test]
        fn gate8c_degenerate_signatures_are_graceful() {
            let mut ir = Interner::new();
            let g = TypedGraph::new();

            // Zero seg relations at all -> empty points, arc_len 0.
            {
                let mut a = TermArena::new();
                let empty_sig = lit(&mut a, Value::Tuple(Arc::new(SmallVec::new())));
                let t = render_term(&mut a, empty_sig, 24, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "", &mut ir);
                let result = run(&a, t, &g, &ir);
                assert_eq!(dict_get(&result, "n_strokes"), Value::Int(1));
                assert_eq!(dict_get(&result, "arc_len"), Value::Float(0.0));
                assert_eq!(points_of(&dict_get(&result, "points")).len(), 0);
            }
            // One seg relation, no pose -> non-empty canonical render.
            {
                let mut a = TermArena::new();
                let sig = Value::Tuple(Arc::new(smallvec::smallvec![seg_rel(&mut ir, 0, 0, 4)]));
                let sig_t = lit(&mut a, sig);
                let t = render_term(&mut a, sig_t, 5, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "", &mut ir);
                let result = run(&a, t, &g, &ir);
                assert_eq!(dict_get(&result, "n_strokes"), Value::Int(1));
                assert_eq!(dict_get(&result, "arc_len"), Value::Float(1.0), "no pose relations present -> canonical arc_len 1");
                assert_eq!(points_of(&dict_get(&result, "points")).len(), 5);
            }
        }

        /// (8d) A `signature` Term evaluating to a `Value::Str` holding
        /// the relation-system as a JSON array-of-arrays string (the
        /// convention every `ShapeSignature` codebook node's `signature`
        /// attr already uses) must render IDENTICALLY to the native-
        /// Tuple encoding — the dual-parsing this Term's doc promises.
        #[test]
        fn gate8d_json_string_signature_parses_same_as_native() {
            let mut ir = Interner::new();
            let sig = build_fixture_sig(&mut ir, 2, 2, 0, 4);
            let g = TypedGraph::new();

            let mut a1 = TermArena::new();
            let sig_t = lit(&mut a1, sig.clone());
            let t1 = render_term(&mut a1, sig_t, 6, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "", &mut ir);
            let native_result = run(&a1, t1, &g, &ir);

            let json_text = serde_json::to_string(&value_to_plain_json(&sig, &ir)).unwrap();
            let mut a2 = TermArena::new();
            let sig_str_t = lit(&mut a2, Value::Str(ir.intern(&json_text)));
            let t2 = render_term(&mut a2, sig_str_t, 6, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "", &mut ir);
            let json_result = run(&a2, t2, &g, &ir);

            assert_eq!(native_result, json_result, "native-Tuple and JSON-string signature encodings must render identically");
        }

        /// (8e) Determinism across independent JSON-Term parses. Unlike
        /// `StrokeQuantize`, `StrokeRender`'s output carries no `Sym`-
        /// bearing values at all (points are Floats, `n_strokes` an Int,
        /// dict keys are interner-free `Value::Surface` text) — so two
        /// completely separate `Interner`/`TermArena` instances parsing
        /// the SAME JSON term must produce a literally `assert_eq!`-
        /// identical `Value`, no `persist::encode_value` re-encoding
        /// needed (contrast `strokes.rs`'s `StrokeQuantize` determinism
        /// test, which DOES need it).
        #[test]
        fn gate8e_json_term_deterministic_across_interners() {
            let term_json = serde_json::json!({
                "type": "StrokeRender",
                "signature": {"type": "Lit", "value": [["seg", 0, 0, 3], ["seg", 1, 4, 4],
                                                         ["pose_x", 2], ["pose_y", 2], ["pose_o", 0], ["pose_s", 4]]},
                "n_points": 5,
                "apply_pose": true,
                "turn_bins": 16,
                "len_bins": 8,
                "grid": 8,
                "scale_bins": 8,
                "bounds": {"type": "Lit", "value": [0.0, 0.0, 8.0, 8.0]}
            });

            let mut ir1 = Interner::new();
            let mut a1 = TermArena::new();
            let t1 = crate::jsonio::term_from_json(&term_json, &mut a1, &mut ir1)
                .expect("StrokeRender JSON schema must parse");
            let g1 = TypedGraph::new();
            let r1 = run(&a1, t1, &g1, &ir1);

            let mut ir2 = Interner::new();
            let mut a2 = TermArena::new();
            let t2 = crate::jsonio::term_from_json(&term_json, &mut a2, &mut ir2).unwrap();
            let g2 = TypedGraph::new();
            let r2 = run(&a2, t2, &g2, &ir2);

            assert_eq!(r1, r2, "re-parsing the same StrokeRender JSON must be fully deterministic");
        }

        /// (8f) `field` selects one output key, exactly like
        /// `StrokeQuantize`'s selector.
        #[test]
        fn gate8f_field_selector() {
            let mut ir = Interner::new();
            let g = TypedGraph::new();

            let mut a = TermArena::new();
            let sig_t = lit(&mut a, build_fixture_sig(&mut ir, 2, 2, 0, 4));
            let full_t = render_term(&mut a, sig_t, 5, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "", &mut ir);
            let full = run(&a, full_t, &g, &ir);

            let mut a2 = TermArena::new();
            let sig_t2 = lit(&mut a2, build_fixture_sig(&mut ir, 2, 2, 0, 4));
            let points_t = render_term(&mut a2, sig_t2, 5, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "points", &mut ir);
            let points_only = run(&a2, points_t, &g, &ir);
            assert_eq!(points_only, dict_get(&full, "points"));

            let mut a3 = TermArena::new();
            let sig_t3 = lit(&mut a3, build_fixture_sig(&mut ir, 2, 2, 0, 4));
            let arc_len_t = render_term(&mut a3, sig_t3, 5, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "arc_len", &mut ir);
            let arc_len_only = run(&a3, arc_len_t, &g, &ir);
            assert_eq!(arc_len_only, dict_get(&full, "arc_len"));

            let mut a4 = TermArena::new();
            let sig_t4 = lit(&mut a4, build_fixture_sig(&mut ir, 2, 2, 0, 4));
            let n_strokes_t = render_term(&mut a4, sig_t4, 5, true, TURN_BINS, LEN_BINS, GRID, SCALE_BINS, Some(BOUNDS), "n_strokes", &mut ir);
            let n_strokes_only = run(&a4, n_strokes_t, &g, &ir);
            assert_eq!(n_strokes_only, Value::Int(1));
        }
    }
}
