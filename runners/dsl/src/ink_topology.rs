//! INK TOPOLOGY — enclosed regions ("counters") of a pen trajectory.
//!
//! The ventral grounding (`VISION_VENTRAL_GROUNDING.md`, 2026-07-18) names ENCLOSURE as the
//! consequence of the mid-level proto-object stage (border-ownership → figure-ground →
//! grouping/closure), and claims topology is among the most writer-INVARIANT features that
//! exists — "an 'A' has one counter whoever writes it". The handwriting pipeline
//! (`domains/ink_decode.py`, `stroke_codebook.py`, `character_compose.py`, `abs_read.py`)
//! carries turn/length quanta, pose bins, arrangement relations and continuous point-set
//! metrics — and NO topological feature of any kind. This module is that missing primitive.
//!
//! It is a PRIMITIVE, in Rust, per the architecture rule: rasterization + flood fill cannot be
//! expressed in the DSL. Nothing here decides anything — it returns a mechanical numerical fact
//! about a point set, exactly like `pointset_dist` or `smooth_deform_dist`. Every DECISION that
//! reads it (an admissibility gate, a distance, a winner) is a held Term composed in graph data.
//!
//! ── THE ONE CONSTANT THAT COULD BE MAGIC, AND WHY IT IS NOT (§13) ───────────────────────────
//!
//! The raster RESOLUTION is the only number a hole-counter needs, and it is NOT chosen here.
//! It falls out of the ink's own sampling:
//!
//!     cell = (total within-stroke arc length) / (total number of inter-sample steps)
//!
//! i.e. the MEAN INTER-SAMPLE ARC STEP — the resolution at which the pen was actually recorded.
//! This is the frame/continuum invariant's own identifiability guard applied verbatim (CLAUDE.md
//! 2026-07-08): *never encode precision the steps cannot support*. A gap narrower than one
//! sample step is BELOW THE DATUM'S OWN RESOLUTION and is therefore closed; a gap wider than one
//! is open. There is no threshold, no dilation radius, no tuned grid size, and no free parameter
//! anywhere in this file.
//!
//! ── DIGITAL TOPOLOGY, DECLARED ──────────────────────────────────────────────────────────────
//!
//! Strokes are rasterized as Bresenham polylines, which are 8-CONNECTED. The background is
//! flooded 4-CONNECTED from the raster border. 8-connected foreground with 4-connected
//! background is the standard consistent pairing (the mismatched pairing produces the classical
//! connectivity paradox, where a digital Jordan curve fails to separate its interior). Remaining
//! unflooded background components are the ENCLOSED REGIONS. Declared, not tuned.
//!
//! ── THE ONE HONEST GUARD ────────────────────────────────────────────────────────────────────
//!
//! Grid dimensions are clamped to `MAX_SIDE` per side purely to bound memory on a pathological
//! input (a figure whose bbox is enormous relative to its sample spacing). The returned `clamped`
//! field REPORTS whether the clamp bound. A caller that measures a non-zero clamp rate has lost
//! the §13 derivation for those figures and must say so — which is why the fact is returned as
//! data rather than swallowed.

use crate::value::{SurfaceKind, Value};

/// Memory guard only — NOT a resolution choice. See the module doc's "ONE HONEST GUARD".
const MAX_SIDE: usize = 4096;

fn surf(s: &str) -> Value {
    Value::Surface(SurfaceKind::Text, std::sync::Arc::from(s.as_bytes()))
}

/// Parse a `Value` shaped as a list of strokes, each a list of `[x, y]`, into polylines.
/// Points with fewer than two coordinates read as `0.0` (the same tolerant convention
/// `deform_metric::pts` / `term::pointset_dist` already use) — never a fabricated point.
fn strokes_of(v: &Value) -> Vec<Vec<[f64; 2]>> {
    v.iter()
        .map(|st| {
            st.iter()
                .map(|p| {
                    let mut it = p.iter();
                    let x = it.next().map(|c| c.as_f64()).unwrap_or(0.0);
                    let y = it.next().map(|c| c.as_f64()).unwrap_or(0.0);
                    [x, y]
                })
                .collect()
        })
        .collect()
}

/// The DERIVED cell size: the mean inter-sample arc step over every within-stroke step.
/// Returns `None` when there is no step at all to measure (no stroke has ≥2 points, or the
/// whole figure has zero arc length) — an honest miss, never a fabricated resolution.
fn derived_cell(strokes: &[Vec<[f64; 2]>]) -> Option<(f64, usize)> {
    let mut total_len = 0.0f64;
    let mut n_steps = 0usize;
    for st in strokes {
        for w in st.windows(2) {
            let dx = w[1][0] - w[0][0];
            let dy = w[1][1] - w[0][1];
            total_len += (dx * dx + dy * dy).sqrt();
            n_steps += 1;
        }
    }
    if n_steps == 0 || !(total_len > 0.0) {
        return None;
    }
    Some((total_len / n_steps as f64, n_steps))
}

/// Bresenham line into a boolean occupancy grid (8-connected by construction).
fn draw_line(grid: &mut [bool], w: usize, h: usize, x0: i64, y0: i64, x1: i64, y1: i64) {
    let dx = (x1 - x0).abs();
    let sx: i64 = if x0 < x1 { 1 } else { -1 };
    let dy = -(y1 - y0).abs();
    let sy: i64 = if y0 < y1 { 1 } else { -1 };
    let mut err = dx + dy;
    let (mut x, mut y) = (x0, y0);
    loop {
        if x >= 0 && y >= 0 && (x as usize) < w && (y as usize) < h {
            grid[y as usize * w + x as usize] = true;
        }
        if x == x1 && y == y1 {
            break;
        }
        let e2 = 2 * err;
        if e2 >= dy {
            err += dy;
            x += sx;
        }
        if e2 <= dx {
            err += dx;
            y += sy;
        }
    }
}

/// The topology read. Returns `(holes, grid_w, grid_h, cell, n_samples, clamped, sizes)`,
/// where `sizes` is each enclosed region's area IN RASTER CELLS.
///
/// `sizes` is DIAGNOSTIC ONLY and no verdict in this arc reads it. It exists because a hole
/// counted at the ink's own sampling resolution can be either a PERCEPTUAL COUNTER (the thing
/// the ventral claim is about) or a ONE-CELL PEN-JITTER MICRO-LOOP (a self-intersection of the
/// trajectory), and a bare count cannot tell them apart. Reporting the size distribution is how
/// a null gets DIAGNOSED rather than shrugged at. `holes == 0` with `grid_w == 0` marks a
/// degenerate input (nothing measurable).
pub fn enclosed_count(v: &Value) -> (usize, usize, usize, f64, usize, bool, Vec<usize>) {
    let strokes = strokes_of(v);
    let (cell, n_steps) = match derived_cell(&strokes) {
        Some(c) => c,
        None => return (0, 0, 0, 0.0, 0, false, Vec::new()),
    };

    let (mut minx, mut miny) = (f64::INFINITY, f64::INFINITY);
    let (mut maxx, mut maxy) = (f64::NEG_INFINITY, f64::NEG_INFINITY);
    let mut n_pts = 0usize;
    for st in &strokes {
        for p in st {
            minx = minx.min(p[0]);
            maxx = maxx.max(p[0]);
            miny = miny.min(p[1]);
            maxy = maxy.max(p[1]);
            n_pts += 1;
        }
    }
    if !minx.is_finite() || !miny.is_finite() {
        return (0, 0, 0, cell, n_pts, false, Vec::new());
    }

    // One cell of padding on every side, so the background always touches the border and the
    // flood always has a seed. `+3` = ceil-slack (1) + the two padding cells.
    let raw_w = ((maxx - minx) / cell).ceil() as i64 + 3;
    let raw_h = ((maxy - miny) / cell).ceil() as i64 + 3;
    let mut clamped = false;
    let mut w = raw_w.max(3) as usize;
    let mut h = raw_h.max(3) as usize;
    if w > MAX_SIDE {
        w = MAX_SIDE;
        clamped = true;
    }
    if h > MAX_SIDE {
        h = MAX_SIDE;
        clamped = true;
    }
    // When clamped, the effective cell grows so the figure still fits — reported via `clamped`.
    let cx = if w > 3 { (maxx - minx) / (w - 3) as f64 } else { cell };
    let cy = if h > 3 { (maxy - miny) / (h - 3) as f64 } else { cell };
    let sx = if cx > 0.0 { cx } else { cell };
    let sy = if cy > 0.0 { cy } else { cell };

    let mut grid = vec![false; w * h];
    let to_ix = |p: &[f64; 2]| -> (i64, i64) {
        (
            ((p[0] - minx) / sx).round() as i64 + 1,
            ((p[1] - miny) / sy).round() as i64 + 1,
        )
    };
    for st in &strokes {
        if st.len() == 1 {
            let (x, y) = to_ix(&st[0]);
            if x >= 0 && y >= 0 && (x as usize) < w && (y as usize) < h {
                grid[y as usize * w + x as usize] = true;
            }
            continue;
        }
        for seg in st.windows(2) {
            let (x0, y0) = to_ix(&seg[0]);
            let (x1, y1) = to_ix(&seg[1]);
            draw_line(&mut grid, w, h, x0, y0, x1, y1);
        }
    }

    // Flood the background 4-connected from every border cell.
    let mut seen = vec![false; w * h];
    let mut stack: Vec<usize> = Vec::new();
    let mut push = |i: usize, seen: &mut Vec<bool>, stack: &mut Vec<usize>| {
        if !grid[i] && !seen[i] {
            seen[i] = true;
            stack.push(i);
        }
    };
    for x in 0..w {
        push(x, &mut seen, &mut stack);
        push((h - 1) * w + x, &mut seen, &mut stack);
    }
    for y in 0..h {
        push(y * w, &mut seen, &mut stack);
        push(y * w + (w - 1), &mut seen, &mut stack);
    }
    while let Some(i) = stack.pop() {
        let (x, y) = (i % w, i / w);
        if x > 0 {
            push(i - 1, &mut seen, &mut stack);
        }
        if x + 1 < w {
            push(i + 1, &mut seen, &mut stack);
        }
        if y > 0 {
            push(i - w, &mut seen, &mut stack);
        }
        if y + 1 < h {
            push(i + w, &mut seen, &mut stack);
        }
    }

    // Every remaining un-flooded background component is an enclosed region.
    let mut holes = 0usize;
    let mut sizes: Vec<usize> = Vec::new();
    let mut comp = vec![false; w * h];
    for start in 0..(w * h) {
        if grid[start] || seen[start] || comp[start] {
            continue;
        }
        holes += 1;
        let mut size = 0usize;
        comp[start] = true;
        stack.push(start);
        while let Some(i) = stack.pop() {
            size += 1;
            let (x, y) = (i % w, i / w);
            let mut visit = |j: usize, stack: &mut Vec<usize>| {
                if !grid[j] && !seen[j] && !comp[j] {
                    comp[j] = true;
                    stack.push(j);
                }
            };
            if x > 0 {
                visit(i - 1, &mut stack);
            }
            if x + 1 < w {
                visit(i + 1, &mut stack);
            }
            if y > 0 {
                visit(i - w, &mut stack);
            }
            if y + 1 < h {
                visit(i + w, &mut stack);
            }
        }
        sizes.push(size);
    }

    let _ = n_steps;
    (holes, w, h, cell, n_pts, clamped, sizes)
}

/// The `Value` face read by `TermNode::EnclosedCount` — a `Dict` a caller reads one field of via
/// a held `DictGet`, never a Python branch.
pub fn enclosed_count_value(v: &Value) -> Value {
    let (holes, gw, gh, cell, n_samples, clamped, sizes) = enclosed_count(v);
    let max_cells = sizes.iter().copied().max().unwrap_or(0);
    let sum_cells: usize = sizes.iter().sum();
    // Holes of exactly ONE cell are the MINIMUM representable enclosure -- unambiguously a
    // rasterization/self-intersection artifact, and identified with NO threshold chosen.
    let one_cell = sizes.iter().filter(|&&z| z == 1).count();
    Value::Dict(std::sync::Arc::from(vec![
        (surf("holes"), Value::Float(holes as f64)),
        (surf("grid_w"), Value::Float(gw as f64)),
        (surf("grid_h"), Value::Float(gh as f64)),
        (surf("cell"), Value::Float(cell)),
        (surf("n_samples"), Value::Float(n_samples as f64)),
        (surf("clamped"), Value::Float(if clamped { 1.0 } else { 0.0 })),
        (surf("hole_cells_max"), Value::Float(max_cells as f64)),
        (surf("hole_cells_sum"), Value::Float(sum_cells as f64)),
        (surf("holes_one_cell"), Value::Float(one_cell as f64)),
        (surf("grid_cells"), Value::Float((gw * gh) as f64)),
    ]))
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::value::Value;

    fn tup(items: Vec<Value>) -> Value {
        Value::Tuple(std::sync::Arc::new(items.into_iter().collect()))
    }

    fn poly(pts: &[(f64, f64)]) -> Value {
        tup(pts
            .iter()
            .map(|&(x, y)| tup(vec![Value::Float(x), Value::Float(y)]))
            .collect::<Vec<_>>())
    }

    fn figure(strokes: Vec<Value>) -> Value {
        tup(strokes)
    }

    fn circle(cx: f64, cy: f64, r: f64, n: usize, frac: f64) -> Value {
        let pts: Vec<(f64, f64)> = (0..=n)
            .map(|i| {
                let t = frac * 2.0 * std::f64::consts::PI * (i as f64) / (n as f64);
                (cx + r * t.cos(), cy + r * t.sin())
            })
            .collect();
        poly(&pts)
    }

    #[test]
    fn closed_circle_has_one_counter() {
        let (holes, ..) = enclosed_count(&figure(vec![circle(0.0, 0.0, 10.0, 120, 1.0)]));
        assert_eq!(holes, 1);
    }

    #[test]
    fn open_arc_has_none() {
        let (holes, ..) = enclosed_count(&figure(vec![circle(0.0, 0.0, 10.0, 120, 0.75)]));
        assert_eq!(holes, 0);
    }

    #[test]
    fn nested_circles_have_two() {
        let (holes, ..) = enclosed_count(&figure(vec![
            circle(0.0, 0.0, 10.0, 120, 1.0),
            circle(0.0, 0.0, 4.0, 60, 1.0),
        ]));
        assert_eq!(holes, 2);
    }

    #[test]
    fn straight_line_and_scatter_have_none() {
        let line = figure(vec![poly(&[(0.0, 0.0), (10.0, 0.0), (20.0, 0.0)])]);
        assert_eq!(enclosed_count(&line).0, 0);
        let scatter = figure(vec![
            poly(&[(0.0, 0.0), (1.0, 0.0)]),
            poly(&[(9.0, 4.0), (10.0, 4.0)]),
            poly(&[(3.0, 9.0), (4.0, 9.0)]),
        ]);
        assert_eq!(enclosed_count(&scatter).0, 0);
    }

    #[test]
    fn degenerate_is_an_honest_zero_not_a_crash() {
        assert_eq!(enclosed_count(&figure(vec![])).0, 0);
        let one = figure(vec![poly(&[(1.0, 1.0)])]);
        assert_eq!(enclosed_count(&one).0, 0);
    }

    /// The §13 claim in code: the resolution is the ink's own mean inter-sample step, so the
    /// SAME shape sampled at a different density yields the SAME topology — the number is not
    /// a grid size anyone picked.
    #[test]
    fn resolution_is_sampling_derived_not_chosen() {
        for n in [40usize, 120, 400] {
            assert_eq!(enclosed_count(&figure(vec![circle(0.0, 0.0, 10.0, n, 1.0)])).0, 1);
        }
    }

    /// Scale invariance: a circle at radius 1 and at radius 1000 both enclose exactly one
    /// region, because the cell scales with the ink.
    #[test]
    fn scale_invariant() {
        for r in [1.0f64, 10.0, 1000.0] {
            assert_eq!(enclosed_count(&figure(vec![circle(0.0, 0.0, r, 120, 1.0)])).0, 1);
        }
    }
}
