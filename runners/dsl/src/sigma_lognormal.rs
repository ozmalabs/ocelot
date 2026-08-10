//! `SigmaLognormalGenerate` — Plamondon's Kinematic Theory of rapid human
//! movements: handwriting velocity is the vector superimposition of a
//! small number of LOGNORMAL movement primitives, each with a constant
//! aim direction, summed in velocity space and integrated to a
//! trajectory ("The lognormal handwriter", Plamondon et al., PMC3867641;
//! `RESEARCH_CURSIVE.md` C4). This is the CONTINUOUS motor-PLANNING
//! generator — contrast `strokes.rs`'s `StrokeQuantize`/`StrokeRender`,
//! a DISCRETIZED shape codebook (12 segments × 16 turn bins, run 71's
//! floor: self-consistent but too lossy to discriminate real ink of the
//! same class). A motor plan here is a handful of primitives (typically
//! 2-6), each `(t0, mu, sigma, D, theta)` — LOW-DIMENSIONAL by
//! construction, exactly Plamondon's claim that this is the tractable
//! inverse-generative description of a stroke.
//!
//! `FIT` (extracting a motor plan from a real trajectory's velocity
//! profile — peak detection + nonlinear least-squares) is Python-side
//! signal processing (mirrors `domains/motor_plan.py`'s own
//! "world-adapter-class feature extractor" precedent: mechanical
//! translation of raw ink into graph-resident data, not a graph
//! decision) — a CLOSED-FORM kinematic curve fit, not a trained net
//! (donkey=0-compatible). This module only ever GENERATES, given an
//! already-fit (or hand-authored) motor plan: pure geometry, no graph
//! reads, no rule engine, no decisions — the exact same posture
//! `strokes.rs` documents for itself.
//!
//! Kept as its own module (not folded into `strokes.rs` or
//! `shape_decode.rs`) so this addition's diff never collides with
//! unrelated concurrent work in those files — the same working-tree
//! isolation rationale `strokes.rs`'s own module doc states for itself.

use std::sync::Arc;

use smallvec::SmallVec;

use crate::sym::{Interner, Sym};
use crate::term::{evaluate, Env, EvalCtx, TermArena, TermIdx};
use crate::value::{SurfaceKind, Value};

// --- tiny output helpers — deliberately duplicated from strokes.rs's
// private surf/select_field/finish (not imported), per that module's own
// working-tree-isolation precedent. ---

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

/// Read an evaluated `primitives` Value as `Vec<(t0, mu, sigma, D, theta)>`
/// — a Tuple of Tuple-of-≥5-floats (`[t0, mu, sigma, D, theta]`, trailing
/// slots ignored). Malformed entries are skipped, not errors — the same
/// graceful-degrade posture `strokes.rs::read_points` has for observation-
/// shaped input.
fn read_primitives(v: &Value) -> Vec<(f64, f64, f64, f64, f64)> {
    let mut out = Vec::new();
    if let (Value::Tuple(items) | Value::List(items)) = v {
        for it in items.iter() {
            if let (Value::Tuple(p) | Value::List(p)) = it {
                if p.len() >= 5 {
                    out.push((
                        p[0].as_f64(),
                        p[1].as_f64(),
                        p[2].as_f64(),
                        p[3].as_f64(),
                        p[4].as_f64(),
                    ));
                }
            }
        }
    }
    out
}

/// Read an evaluated `start` Value as `(x0, y0)`; any other shape
/// defaults to the origin (documented graceful fallback).
fn read_point(v: &Value) -> (f64, f64) {
    if let (Value::Tuple(p) | Value::List(p)) = v {
        if p.len() >= 2 {
            return (p[0].as_f64(), p[1].as_f64());
        }
    }
    (0.0, 0.0)
}

/// The lognormal velocity-magnitude density Λ(τ; mu, sigma) for
/// τ = t − t0. Zero for τ ≤ 0 (a primitive contributes nothing before
/// its own virtual-target command fires) and for a degenerate
/// (non-positive) `sigma` — graceful, never NaN/panic.
fn lognormal(tau: f64, mu: f64, sigma: f64) -> f64 {
    if tau <= 1e-9 || sigma <= 1e-9 {
        return 0.0;
    }
    let z = (tau.ln() - mu) / sigma;
    (1.0 / (sigma * tau * (2.0 * std::f64::consts::PI).sqrt())) * (-0.5 * z * z).exp()
}

/// Evaluate `SigmaLognormalGenerate`. See `TermNode::SigmaLognormalGenerate`'s
/// doc (`term.rs`) for the full field semantics — GENERATE half of the
/// sigma-lognormal motor-planning primitive (the FIT half is Python-side).
#[allow(clippy::too_many_arguments)]
pub(crate) fn eval_sigma_lognormal_generate(
    arena: &TermArena,
    primitives_idx: TermIdx,
    start_idx: TermIdx,
    t_start: f64,
    t_end: f64,
    n_points: i64,
    field: Sym,
    env: &mut Env,
    ctx: &mut EvalCtx,
) -> Value {
    let prims = read_primitives(&evaluate(arena, primitives_idx, env, ctx));
    let (x0, y0) = read_point(&evaluate(arena, start_idx, env, ctx));

    let n = n_points.max(2) as usize;
    let (t0v, t1v) = if t_end > t_start {
        (t_start, t_end)
    } else {
        (t_start, t_start + 1.0)
    };
    let dt = (t1v - t0v) / (n as f64 - 1.0);

    // Velocity superposition: V(t) = sum_i D_i * Λ(t - t0_i; mu_i, sigma_i) *
    // (cos theta_i, sin theta_i) — the vector sum of every primitive's own
    // constant-direction lognormal-magnitude contribution at time t.
    let vel_at = |t: f64| -> (f64, f64) {
        let mut vx = 0.0f64;
        let mut vy = 0.0f64;
        for &(pt0, mu, sigma, d, theta) in &prims {
            let mag = d * lognormal(t - pt0, mu, sigma);
            vx += mag * theta.cos();
            vy += mag * theta.sin();
        }
        (vx, vy)
    };

    // Integrate via trapezoidal quadrature over a uniform time grid — a
    // CONTINUOUS trajectory (no grid/bin quantization anywhere in this
    // path, contrast StrokeQuantize's turn/len bins).
    let mut points: Vec<(f64, f64)> = Vec::with_capacity(n);
    let mut velocities: Vec<(f64, f64)> = Vec::with_capacity(n);
    let (mut x, mut y) = (x0, y0);
    points.push((x, y));
    velocities.push(vel_at(t0v));

    for k in 1..n {
        let t = t0v + dt * k as f64;
        let (vx, vy) = vel_at(t);
        let (vx_prev, vy_prev) = velocities[k - 1];
        x += 0.5 * (vx + vx_prev) * dt;
        y += 0.5 * (vy + vy_prev) * dt;
        points.push((x, y));
        velocities.push((vx, vy));
    }

    let points_val: SmallVec<[Value; 4]> = points
        .iter()
        .map(|&(px, py)| Value::Tuple(Arc::new(smallvec::smallvec![Value::Float(px), Value::Float(py)])))
        .collect();
    let velocity_val: SmallVec<[Value; 4]> = velocities
        .iter()
        .map(|&(vx, vy)| Value::Tuple(Arc::new(smallvec::smallvec![Value::Float(vx), Value::Float(vy)])))
        .collect();

    let result = Value::Dict(Arc::from(vec![
        (surf("points"), Value::Tuple(Arc::new(points_val))),
        (surf("velocity"), Value::Tuple(Arc::new(velocity_val))),
        (surf("n_points"), Value::Int(n as i64)),
        (surf("n_primitives"), Value::Int(prims.len() as i64)),
    ]));
    finish(result, field, ctx.interner)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::graph::TypedGraph;
    use crate::term::TermNode;

    fn pt(x: f64, y: f64) -> Value {
        Value::Tuple(Arc::new(smallvec::smallvec![Value::Float(x), Value::Float(y)]))
    }

    fn prims_value(prims: &[(f64, f64, f64, f64, f64)]) -> Value {
        let v: SmallVec<[Value; 4]> = prims
            .iter()
            .map(|&(t0, mu, sigma, d, theta)| {
                Value::Tuple(Arc::new(smallvec::smallvec![
                    Value::Float(t0),
                    Value::Float(mu),
                    Value::Float(sigma),
                    Value::Float(d),
                    Value::Float(theta),
                ]))
            })
            .collect();
        Value::Tuple(Arc::new(v))
    }

    fn build(
        a: &mut TermArena,
        ir: &mut Interner,
        prims: &[(f64, f64, f64, f64, f64)],
        start: (f64, f64),
        t_start: f64,
        t_end: f64,
        n_points: i64,
        field: &str,
    ) -> TermIdx {
        let p = a.add(TermNode::Lit { value: prims_value(prims) });
        let s = a.add(TermNode::Lit { value: pt(start.0, start.1) });
        let field_sym = if field.is_empty() { Sym::default() } else { ir.intern(field) };
        a.add(TermNode::SigmaLognormalGenerate {
            primitives: p,
            start: s,
            t_start,
            t_end,
            n_points,
            field: field_sym,
        })
    }

    fn run(a: &TermArena, idx: TermIdx, g: &TypedGraph, ir: &Interner) -> Value {
        let mut env: Env = Env::new();
        let mut ctx = EvalCtx::new(g, ir);
        evaluate(a, idx, &mut env, &mut ctx)
    }

    fn points_of(v: &Value) -> Vec<(f64, f64)> {
        let pts = select_field(v, "points");
        let mut out = Vec::new();
        if let (Value::Tuple(items) | Value::List(items)) = pts {
            for it in items.iter() {
                if let (Value::Tuple(p) | Value::List(p)) = it {
                    out.push((p[0].as_f64(), p[1].as_f64()));
                }
            }
        }
        out
    }

    // --- (1) single primitive: trajectory ends near start (a lognormal
    // pulse decays to ~0 velocity well before its own generous t_end, so
    // net displacement should be small relative to the primitive's own D
    // scale — mostly checks NO PANIC + sane shape, not near-zero net
    // motion, since a single directional pulse DOES move the pen). ---
    #[test]
    fn single_primitive_generates_a_smooth_directed_stroke() {
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let mut a = TermArena::new();
        // One primitive aimed along +x, peak near tau=exp(mu)=exp(-1.2)~0.30.
        let t = build(&mut a, &mut ir, &[(0.0, -1.2, 0.3, 5.0, 0.0)], (0.0, 0.0), 0.0, 3.0, 60, "");
        let out = run(&a, t, &g, &ir);
        let pts = points_of(&out);
        assert_eq!(pts.len(), 60);
        assert_eq!(pts[0], (0.0, 0.0), "must start at the given start point");
        // Movement is along +x (theta=0): final y stays ~0, final x > 0.
        let (xf, yf) = pts[pts.len() - 1];
        assert!(xf > 0.5, "a +x-aimed primitive must move the pen in +x: got {xf}");
        assert!(yf.abs() < 1e-6, "a +x-aimed primitive must not move the pen off the x-axis: got {yf}");
    }

    // --- (2) CONTINUITY: consecutive points are not restricted to any
    // small quantization grid — a direct falsifier of "this is just
    // StrokeQuantize with different bin edges." ---
    #[test]
    fn generation_is_continuous_not_grid_quantized() {
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let mut a = TermArena::new();
        let t = build(
            &mut a, &mut ir,
            &[(0.0, -1.3, 0.35, 4.0, 0.2), (0.4, -1.0, 0.25, 3.0, 1.1)],
            (0.0, 0.0), 0.0, 3.0, 50, "",
        );
        let out = run(&a, t, &g, &ir);
        let pts = points_of(&out);
        // Consecutive-step deltas should take MANY distinct values (a
        // grid-quantized generator collapses onto a small alphabet of
        // step vectors; this one should not).
        use std::collections::BTreeSet;
        let mut seen: BTreeSet<(i64, i64)> = BTreeSet::new();
        for w in pts.windows(2) {
            let (dx, dy) = (w[1].0 - w[0].0, w[1].1 - w[0].1);
            // Quantize coarsely to i64 millis just to hash-compare floats.
            seen.insert(((dx * 1e6).round() as i64, (dy * 1e6).round() as i64));
        }
        assert!(seen.len() > pts.len() / 2, "step vectors must vary continuously, not collapse onto a small grid");
    }

    // --- (3) two primitives superimpose (a 2-stroke plan is NOT the same
    // as either primitive alone). ---
    #[test]
    fn primitives_superimpose() {
        let mut ir = Interner::new();
        let g = TypedGraph::new();

        let mut a1 = TermArena::new();
        let t1 = build(&mut a1, &mut ir, &[(0.0, -1.2, 0.3, 5.0, 0.0)], (0.0, 0.0), 0.0, 3.0, 40, "");
        let out1 = run(&a1, t1, &g, &ir);
        let pts1 = points_of(&out1);

        let mut a2 = TermArena::new();
        let t2 = build(
            &mut a2, &mut ir,
            &[(0.0, -1.2, 0.3, 5.0, 0.0), (0.5, -1.2, 0.3, 5.0, std::f64::consts::FRAC_PI_2)],
            (0.0, 0.0), 0.0, 3.0, 40, "",
        );
        let out2 = run(&a2, t2, &g, &ir);
        let pts2 = points_of(&out2);

        assert_ne!(pts1.last(), pts2.last(), "adding a second primitive must change the trajectory");
        // The two-primitive plan must pick up some +y motion from the
        // second (theta=90°) primitive that the single-primitive plan lacks.
        assert!(pts2.last().unwrap().1 > pts1.last().unwrap().1 + 0.1);
    }

    // --- (4) n_primitives / n_points reported, field selector works. ---
    #[test]
    fn field_selector_and_counts() {
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let mut a = TermArena::new();
        let t = build(&mut a, &mut ir, &[(0.0, -1.2, 0.3, 5.0, 0.0), (0.3, -1.0, 0.2, 3.0, 0.5)],
                      (1.0, 2.0), 0.0, 2.0, 20, "n_primitives");
        let out = run(&a, t, &g, &ir);
        assert_eq!(out, Value::Int(2));

        let mut a2 = TermArena::new();
        let t2 = build(&mut a2, &mut ir, &[(0.0, -1.2, 0.3, 5.0, 0.0)], (1.0, 2.0), 0.0, 2.0, 20, "");
        let out2 = run(&a2, t2, &g, &ir);
        let pts = points_of(&out2);
        assert_eq!(pts[0], (1.0, 2.0), "must start at the given `start`, not the origin");
    }

    // --- (5) degenerate: zero primitives -> the pen never leaves `start`. ---
    #[test]
    fn zero_primitives_stays_at_start() {
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let mut a = TermArena::new();
        let t = build(&mut a, &mut ir, &[], (3.0, -4.0), 0.0, 2.0, 10, "");
        let out = run(&a, t, &g, &ir);
        let pts = points_of(&out);
        assert!(pts.iter().all(|&p| p == (3.0, -4.0)));
    }

    // --- (6) determinism: same plan, two evaluations, byte-identical. ---
    #[test]
    fn deterministic() {
        let mut ir = Interner::new();
        let g = TypedGraph::new();
        let prims = [(0.1, -1.4, 0.3, 4.0, 0.3), (0.5, -1.1, 0.25, 2.5, -0.4)];

        let mut a1 = TermArena::new();
        let t1 = build(&mut a1, &mut ir, &prims, (0.0, 0.0), 0.0, 2.5, 30, "");
        let out1 = run(&a1, t1, &g, &ir);

        let mut a2 = TermArena::new();
        let t2 = build(&mut a2, &mut ir, &prims, (0.0, 0.0), 0.0, 2.5, 30, "");
        let out2 = run(&a2, t2, &g, &ir);

        assert_eq!(out1, out2, "identical motor plans must generate byte-identical trajectories");
    }
}
