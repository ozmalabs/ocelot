//! `SmoothDeformComponents` — RUN 44 PHASE 2 (the human-gap plan's "background-learned
//! deformation metric"): DECOMPOSES `SmoothDeformDist`'s own free-form-deformation field into
//! an AFFINE part (rotation / shear / log-scale / translation, closed-form least-squares fit)
//! and the NON-AFFINE residual ("bending") — additively, alongside the byte-identical fused
//! scalar (`total`) for a cross-check. `term.rs`'s `smooth_deform_dist` is NOT touched; this
//! module DUPLICATES its multi-level FFD fitting loop verbatim (same magic constants: control-
//! grid half-extent, step size, grid schedule, ridge regularisation, iteration count) — the
//! established "working-tree isolation" precedent this codebase already uses for a new Term
//! that shares math with an existing one (`strokes.rs`'s own module doc: "kept local so this
//! module's edits never collide with unrelated concurrent work", mirrored here so this file's
//! diff never touches `term.rs`'s existing `smooth_deform_dist`/`pointset_resid` bodies).
//!
//! WHY: nine prior verdict-reweighting attempts (RUN 25's six nulls, RUN 34b, RUN 39b, RUN 43)
//! all changed the EVIDENCE the comparator sees or how it's weighted; none changed the DISTANCE
//! FUNCTION with background discriminative information. The standing GUARD verdict
//! (`domains.abs_read.parse_marginal_verdict` -> `recognition_graph.predict_smooth_marginal_sc_
//! term`) fuses `smoothdeform_error_term` (whole-figure `SmoothDeformDist`, THIS module's
//! target) + `part_w * marginal_part_error_term` (per-part `PointSetDist`, no deformation at
//! all — out of this mechanism's scope) + `sc_w * shapecontext_error_term` (whole-figure
//! `ShapeContextDist`, also out of scope — a descriptor match, not a deformation cost).
//! `smooth_deform_dist`'s own distortion-cost term (`residual + 1.5 * dc`, `dc` = mean squared
//! TOTAL per-point displacement) prices EVERY direction of displacement identically — a
//! writer-typical global rotation/shear costs exactly as much per unit displacement as a
//! genuine non-affine bending distortion. `TpsDeformDist` (a DIFFERENT term, not in the
//! standing fused verdict) already treats the affine part as entirely FREE ("only genuine
//! bending costs") — a coarser, binary version of the same idea. This module goes one step
//! further: instead of a binary free/costly split, the affine DOF (rotation, shear) are priced
//! MAHALANOBIS-style against their own BACKGROUND within-class variance (how much does this
//! amount of rotation/shear typically differ between two same-class glyphs from different
//! writers) — a TYPICAL amount of writer rotation/shear costs little, an ATYPICAL amount still
//! costs something (unlike TpsDeformDist's unconditional free pass), and the leftover NON-AFFINE
//! bending is priced by a separately-calibrated weight (`w_bend`). The Python side
//! (`domains/deform_metric.py`) builds the held `DictGet`-based reweighted Term; NO decision
//! lives in Rust or Python — this module only computes the DECOMPOSITION, a mechanical
//! numerical fact about two point sets, exactly like `smooth_deform_dist` itself.
//!
//! AAFFINE DECOMPOSITION (2D, standard Graphics-Gems / CSS-Working-Group QR-style
//! decomposition of a 2x2 linear map into rotation * shear * scale): fit `A` (2x2) + `t` (2,)
//! minimizing `sum_i |A p0_i + t - target_i|^2` (`target_i = p0_i + acc_i`, `acc_i` = the SAME
//! accumulated FFD displacement `smooth_deform_dist` computes) via closed-form least squares
//! (3x3 normal-equations solve, shared design matrix for both output dimensions); decompose `A`
//! into `(rotation, shear, scaleX, scaleY)`; `bending` = the mean squared NON-affine residual
//! displacement (`target_i - (A p0_i + t)`) — the part of the FFD's own displacement field the
//! affine fit does NOT explain. Degenerate input (<3 points, or a singular design matrix) falls
//! back to an honest all-zero affine (bending = dc, the SAME total displacement now attributed
//! entirely to bending) — never a fabricated decomposition.

use crate::value::{SurfaceKind, Value};

fn surf(s: &str) -> Value {
    Value::Surface(SurfaceKind::Text, std::sync::Arc::from(s.as_bytes()))
}

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

// Duplicated verbatim from `term.rs::pointset_resid` (working-tree isolation, see module doc).
fn pointset_resid_local(p: &[[f64; 2]], q: &[[f64; 2]]) -> f64 {
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

// Generic 3x3 solve via Cramer's rule (small, closed-form — no need for the general Gauss-Jordan
// `mat_inverse` `term.rs` uses for the TPS system; duplicated-scope local helper, same isolation
// rationale).
fn solve3(m: &[[f64; 3]; 3], rhs: &[f64; 3]) -> Option<[f64; 3]> {
    let det3 = |a: &[[f64; 3]; 3]| -> f64 {
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
            - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
            + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    };
    let d = det3(m);
    if d.abs() < 1e-10 {
        return None;
    }
    let mut out = [0.0f64; 3];
    for col in 0..3 {
        let mut mc = *m;
        for row in 0..3 {
            mc[row][col] = rhs[row];
        }
        out[col] = det3(&mc) / d;
    }
    Some(out)
}

/// The multi-level FFD field fit — EXACT duplicate of `term.rs::smooth_deform_dist`'s own
/// warping loop (same `r`, `step`, grid schedule `[2, 4]`, ridge formula, 5 inner iterations),
/// returning `(p0, warped, acc)` instead of the fused scalar so the affine decomposition below
/// can run on the SAME field. A change to `term.rs::smooth_deform_dist`'s own constants does
/// NOT automatically update this copy — `tests/test_deform_metric_migrated.py`'s byte-compat
/// gate (comparing this module's own `total` output against a live `SmoothDeformDist` evaluate
/// on the same inputs) is what catches drift.
fn ffd_fit(a: &Value, b: &Value) -> Option<(Vec<[f64; 2]>, Vec<[f64; 2]>, Vec<[f64; 2]>)> {
    let p0 = pts(a);
    let q = pts(b);
    if p0.is_empty() || q.is_empty() {
        return None;
    }
    let r = 2.6_f64;
    let n = p0.len();
    let mut warped = p0.clone();
    let mut acc = vec![[0.0f64; 2]; n];
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
    for &g in &[2usize, 4usize] {
        let nnode = g * g;
        let reg = (n as f64 / nnode as f64) * 0.6 + 1.0;
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
    Some((p0, warped, acc))
}

/// Best-fit affine `(A, t)` (2x2 + translation) minimizing `sum |A p0_i + t - target_i|^2` via
/// closed-form least squares (shared 3x3 normal-equations design matrix, one solve per output
/// dimension). Returns `None` for a degenerate/singular fit (<3 points, or collinear input) —
/// caller falls back to an honest all-bending decomposition.
fn fit_affine(p0: &[[f64; 2]], target: &[[f64; 2]]) -> Option<([[f64; 2]; 2], [f64; 2])> {
    let n = p0.len();
    if n < 3 {
        return None;
    }
    let mut m = [[0.0f64; 3]; 3];
    let mut rhs_x = [0.0f64; 3];
    let mut rhs_y = [0.0f64; 3];
    for i in 0..n {
        let row = [p0[i][0], p0[i][1], 1.0];
        for r in 0..3 {
            for c in 0..3 {
                m[r][c] += row[r] * row[c];
            }
            rhs_x[r] += row[r] * target[i][0];
            rhs_y[r] += row[r] * target[i][1];
        }
    }
    let sx = solve3(&m, &rhs_x)?;
    let sy = solve3(&m, &rhs_y)?;
    // A = [[sx0, sx1], [sy0, sy1]], t = [sx2, sy2] — target = A * p0 + t.
    Some(([[sx[0], sx[1]], [sy[0], sy[1]]], [sx[2], sy[2]]))
}

/// 2D affine -> (rotation, shear, scaleX, scaleY) — the standard Graphics-Gems / CSS Working
/// Group QR-style decomposition (Gram-Schmidt on the matrix's own columns): `A`'s first column
/// gives `scaleX` + `rotation`; the second column's component orthogonal to the first (after
/// removing the shared rotation) gives `shear` + `scaleY`. Degenerate (near-zero column norm)
/// returns `(0.0, 0.0, 0.0, 0.0)` — an honest no-affine-signal default, never a NaN.
fn decompose_affine(a: &[[f64; 2]; 2]) -> (f64, f64, f64, f64) {
    // Column-major reading: col0 = (a[0][0], a[1][0]), col1 = (a[0][1], a[1][1]).
    let (mut m00, mut m10) = (a[0][0], a[1][0]);
    let (mut m01, mut m11) = (a[0][1], a[1][1]);
    let scale_x = (m00 * m00 + m10 * m10).sqrt();
    if scale_x < 1e-12 {
        return (0.0, 0.0, 0.0, 0.0);
    }
    m00 /= scale_x;
    m10 /= scale_x;
    let mut shear = m00 * m01 + m10 * m11;
    m01 -= m00 * shear;
    m11 -= m10 * shear;
    let scale_y = (m01 * m01 + m11 * m11).sqrt();
    if scale_y > 1e-12 {
        shear /= scale_y;
    } else {
        shear = 0.0;
    }
    let rotation = m10.atan2(m00);
    (rotation, shear, scale_x, scale_y)
}

/// THE Term primitive: `SmoothDeformComponents(a, b)` -> a `Dict` carrying `total` (byte-
/// identical to `SmoothDeformDist(a, b)`'s own fused scalar — the cross-check), `residual`
/// (post-warp point-set residual, unchanged), `dc` (mean squared TOTAL displacement, unchanged),
/// `bending` (mean squared NON-AFFINE residual displacement — the part `dc` that the best-fit
/// affine doesn't explain), `rotation` (radians), `shear` (dimensionless), `log_scale`
/// (`0.5*ln(scaleX*scaleY)`), `tx`/`ty` (translation), `n` (point count, `Int`). Degenerate
/// input (empty point sets, or a singular affine fit) returns an honest default (`total`/
/// `residual` = `+inf` for empty input mirroring `SmoothDeformDist`'s own `f64::INFINITY`
/// convention; a singular-but-nonempty fit reports `bending = dc`, every affine component 0.0 —
/// "no affine explained" rather than a fabricated decomposition).
pub(crate) fn smooth_deform_components(a: &Value, b: &Value) -> Value {
    let fit = ffd_fit(a, b);
    let (p0, warped, acc) = match fit {
        Some(x) => x,
        None => {
            return Value::Dict(std::sync::Arc::from(vec![
                (surf("total"), Value::Float(f64::INFINITY)),
                (surf("residual"), Value::Float(f64::INFINITY)),
                (surf("dc"), Value::Float(0.0)),
                (surf("bending"), Value::Float(0.0)),
                (surf("rotation"), Value::Float(0.0)),
                (surf("shear"), Value::Float(0.0)),
                (surf("log_scale"), Value::Float(0.0)),
                (surf("tx"), Value::Float(0.0)),
                (surf("ty"), Value::Float(0.0)),
                (surf("n"), Value::Int(0)),
            ]));
        }
    };
    let n = p0.len();
    let q = pts(b);
    let residual = pointset_resid_local(&warped, &q);
    let dc = acc.iter().map(|d| d[0] * d[0] + d[1] * d[1]).sum::<f64>() / n as f64;
    let total = residual + 1.5 * dc;

    let target: Vec<[f64; 2]> = (0..n)
        .map(|i| [p0[i][0] + acc[i][0], p0[i][1] + acc[i][1]])
        .collect();
    let (rotation, shear, log_scale, tx, ty, bending) = match fit_affine(&p0, &target) {
        Some((mat, t)) => {
            let (rot, shr, sx, sy) = decompose_affine(&mat);
            let log_scale = if sx > 1e-12 && sy > 1e-12 {
                0.5 * (sx * sy).ln()
            } else {
                0.0
            };
            let mut bend = 0.0;
            for i in 0..n {
                let px = mat[0][0] * p0[i][0] + mat[0][1] * p0[i][1] + t[0];
                let py = mat[1][0] * p0[i][0] + mat[1][1] * p0[i][1] + t[1];
                let (dx, dy) = (target[i][0] - px, target[i][1] - py);
                bend += dx * dx + dy * dy;
            }
            bend /= n as f64;
            (rot, shr, log_scale, t[0], t[1], bend)
        }
        None => (0.0, 0.0, 0.0, 0.0, 0.0, dc),
    };

    Value::Dict(std::sync::Arc::from(vec![
        (surf("total"), Value::Float(total)),
        (surf("residual"), Value::Float(residual)),
        (surf("dc"), Value::Float(dc)),
        (surf("bending"), Value::Float(bending)),
        (surf("rotation"), Value::Float(rotation)),
        (surf("shear"), Value::Float(shear)),
        (surf("log_scale"), Value::Float(log_scale)),
        (surf("tx"), Value::Float(tx)),
        (surf("ty"), Value::Float(ty)),
        (surf("n"), Value::Int(n as i64)),
    ]))
}
