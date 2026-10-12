//! `space_quantize` — N-dimensional, body-conditional, foveated quantization
//! over an observation belief.
//!
//! Per the design (FLOOD_DESIGN.md, Part A): "flood does not occur per
//! pixel, it occurs at quanta, and if there's a remainder it goes to more
//! detail." This module is the DEQUANTIZATION primitive: it reads the
//! agent's persistent belief (Cell/WorldInstance nodes carrying `row`/`col`
//! — or an N-dim `pose` list — plus `value`, linked to a game/space node
//! via `has_cell` edges — exactly what `worlds/arc.py` and
//! `domains/maze_world.py` already emit, unchanged), erodes it by a body
//! shape (config-space admissibility), decomposes the admissible region
//! into maximal axis-aligned N-dim boxes (`SpaceQuantum` nodes), mints
//! `portal` edges between face-adjacent quanta, and mints thin `frontier`
//! quanta where a passable quantum borders UNKNOWN poses. Everything is
//! scoped to a `focus` box (foveation) and incremental: quanta from a
//! prior call that are still valid (not stale, still within the current
//! focus) are REUSED in place rather than rebuilt; quanta marked `stale`
//! (by a Rule, in response to an action-outcome surprise) are replaced,
//! splitting ONLY along the failing dimension when `stale_dim`/
//! `stale_pose` are given.
//!
//! Kept out of `py.rs` per CLAUDE.md ("primitive in Rust, composition in
//! graph" / thin one-line PyO3 handoff) — `py.rs`'s `space_quantize`
//! method only converts Python args to `QuantizeParams`, calls
//! [`space_quantize`], and renders the returned [`QuantizeSummary`] as a
//! dict. `slide_flood` (py.rs:2172) inlined its whole BFS in the binding
//! layer; this module is the fix for that pattern, not a repeat of it.
//!
//! ## Graph vocabulary written
//!
//! - `SpaceQuantum` node: `lo`/`hi` (Tuple\<Int\>, per-dim inclusive box
//!   bounds), `ndim` (Int), `kind` (Str: `"passable"` | `"frontier"`),
//!   `body_key` (Str), `epoch` (Int, stamped every decode that confirms or
//!   creates the quantum), `stale` (Int 0/1, INPUT — read, not written, by
//!   this primitive; a Rule sets it), `visited` (Int 0/1, default 0, a
//!   Rule owns it), `qdist` (Float, -1.0 = unset, a flood Rule owns it).
//! - `portal` edge (quantum -> quantum): `dim` (Int, crossing-dimension
//!   index), `dir` (Int +1/-1, the direction of travel along `dim` from
//!   src to tgt), `span_lo`/`span_hi` (Tuple\<Int\>, the shared boundary
//!   window — meaningful for dims != `dim`), `cost` (Int, always 1 in
//!   this phase — scale-free per the design; a flood Rule multiplies by a
//!   per-dim `scale` attr it owns), `oneway_ok` (Int 0/1, default 1).
//! - `in_space` edge (quantum -> game/space node): the space linkage.
//!
//! Bypasses Γ admissibility for these writes (`graph.insert_node` /
//! `graph.insert_edge` directly), matching the existing `slide_flood`
//! (`neighbour`/`reached`) and `segment` (`within`/`has_region`)
//! precedent — these are host/primitive-owned bookkeeping edges, not
//! domain claims a Production need govern.
//!
//! ## `stale_dim` / `stale_pose` — the input side of the residual→refine
//! loop
//!
//! A Part-B Rule (`qf_stale_on_block`, not built in this phase) is
//! expected to set `stale=1` (+ `stale_dim`, the failing dimension) on a
//! `SpaceQuantum` in response to an action-outcome surprise or a belief
//! change. This primitive reads `stale`/`stale_dim` as INPUT (never
//! writes them onto a survivor — new quanta always start `stale=0`).
//! `stale_pose` (the specific failing index) is part of that Rule-facing
//! contract but this primitive does NOT need to trust it literally: it
//! re-derives exactly which indices along `stale_dim` are still
//! admissible by re-scanning the current belief (see
//! `split_along_dim`), which is strictly more robust than trusting one
//! recorded index (covers the case where more than one slice changed).

use std::sync::Arc;

use rustc_hash::{FxHashMap, FxHashSet};
use smallvec::SmallVec;

use crate::graph::{NodeID, TypedGraph};
use crate::substrate::Substrate;
use crate::sym::{Interner, Sym};
use crate::value::Value;

/// A body's shape, config-space style. `Extents` is the rigid axis-
/// aligned box case (generalises `slide_flood`'s `fp_h`x`fp_w`): the body
/// occupies `[0, extent_d)` per dim, offset from its anchor (the anchor is
/// the box's lowest corner, matching `slide_flood`'s "top-left corner"
/// convention). `Offsets` is the general case (shape-sorter pieces, RTS
/// units with an odd footprint): an explicit list of N-dim offset
/// vectors relative to the anchor (should include the zero vector unless
/// the anchor cell itself is deliberately excluded from the body).
#[derive(Clone, Debug)]
pub enum BodySpec {
    Extents(Vec<i64>),
    Offsets(Vec<Vec<i64>>),
}

/// Inputs to one [`space_quantize`] call. See `py.rs`'s `space_quantize`
/// method for the Python-visible argument names this is built from.
pub struct QuantizeParams {
    pub game: NodeID,
    pub ndim: usize,
    pub body_key: String,
    pub body: BodySpec,
    pub passable_values: Vec<i64>,
    pub focus_lo: Vec<i64>,
    pub focus_hi: Vec<i64>,
    pub epoch: i64,
    /// Per-dim coarse growth step (a performance knob only — the greedy
    /// grower tries this stride first, then falls back to 1-at-a-time to
    /// find the exact maximal boundary, so the RESULT is identical to a
    /// naive unit-stepped grower; it just does fewer admissibility scans
    /// in wide-open regions). `1` per dim = plain unit growth.
    pub min_extent: Vec<i64>,
}

/// Returned to Python as a plain dict — the decode's headline counts.
#[derive(Default, Debug, Clone, Copy)]
pub struct QuantizeSummary {
    pub quanta: usize,
    pub portals: usize,
    pub frontiers: usize,
    pub reused: usize,
    pub split: usize,
}

/// Every interned Sym this module touches, resolved ONCE up front so the
/// rest of the algorithm never needs `&mut Interner` (avoids borrow
/// conflicts with the `&Substrate`/`&TypedGraph` reads that dominate the
/// hot loops).
struct QSyms {
    quantum: Sym,
    in_space: Sym,
    portal: Sym,
    has_cell: Sym,
    row: Sym,
    col: Sym,
    pose: Sym,
    value: Sym,
    lo: Sym,
    hi: Sym,
    ndim: Sym,
    kind: Sym,
    body_key: Sym,
    epoch: Sym,
    stale: Sym,
    stale_dim: Sym,
    visited: Sym,
    qdist: Sym,
    dim: Sym,
    dir: Sym,
    span_lo: Sym,
    span_hi: Sym,
    cost: Sym,
    oneway_ok: Sym,
}

impl QSyms {
    fn new(interner: &mut Interner) -> Self {
        QSyms {
            quantum: interner.intern("SpaceQuantum"),
            in_space: interner.intern("in_space"),
            portal: interner.intern("portal"),
            has_cell: interner.intern("has_cell"),
            row: interner.intern("row"),
            col: interner.intern("col"),
            pose: interner.intern("pose"),
            value: interner.intern("value"),
            lo: interner.intern("lo"),
            hi: interner.intern("hi"),
            ndim: interner.intern("ndim"),
            kind: interner.intern("kind"),
            body_key: interner.intern("body_key"),
            epoch: interner.intern("epoch"),
            stale: interner.intern("stale"),
            stale_dim: interner.intern("stale_dim"),
            visited: interner.intern("visited"),
            qdist: interner.intern("qdist"),
            dim: interner.intern("dim"),
            dir: interner.intern("dir"),
            span_lo: interner.intern("span_lo"),
            span_hi: interner.intern("span_hi"),
            cost: interner.intern("cost"),
            oneway_ok: interner.intern("oneway_ok"),
        }
    }
}

// --- small numeric / Value helpers -----------------------------------

fn read_num(v: Option<&Value>) -> Option<i64> {
    match v {
        Some(Value::Int(i)) => Some(*i),
        Some(Value::Float(f)) => Some(*f as i64),
        _ => None,
    }
}

fn read_str(graph: &TypedGraph, interner: &Interner, nid: NodeID, key: Sym) -> Option<String> {
    match graph.node(nid).attrs.get(&key) {
        Some(Value::Str(sym)) => Some(interner.resolve(*sym).to_string()),
        _ => None,
    }
}

fn read_i64_list(graph: &TypedGraph, nid: NodeID, key: Sym) -> Option<Vec<i64>> {
    match graph.node(nid).attrs.get(&key) {
        Some(Value::Tuple(items) | Value::List(items)) => {
            let mut out = Vec::with_capacity(items.len());
            for it in items.iter() {
                match it {
                    Value::Int(i) => out.push(*i),
                    Value::Float(f) => out.push(*f as i64),
                    _ => return None,
                }
            }
            Some(out)
        }
        _ => None,
    }
}

fn int_tuple(xs: &[i64]) -> Value {
    let v: SmallVec<[Value; 4]> = xs.iter().map(|&x| Value::Int(x)).collect();
    Value::Tuple(Arc::new(v))
}

// --- N-dim lattice iteration ------------------------------------------

/// Enumerate every integer lattice point in the inclusive box `[lo, hi]`,
/// last dim fastest-varying (row-major; matches the existing 2D
/// convention where col is the fast-varying index). No-op if any dim is
/// empty (`hi[d] < lo[d]`).
fn for_each_pose<F: FnMut(&[i64])>(lo: &[i64], hi: &[i64], mut f: F) {
    let ndim = lo.len();
    if ndim == 0 {
        return;
    }
    let mut total: i64 = 1;
    for d in 0..ndim {
        if hi[d] < lo[d] {
            return;
        }
        total = total.saturating_mul(hi[d] - lo[d] + 1);
    }
    let mut cur = lo.to_vec();
    for _ in 0..total {
        f(&cur);
        for d in (0..ndim).rev() {
            cur[d] += 1;
            if cur[d] <= hi[d] {
                break;
            }
            cur[d] = lo[d];
        }
    }
}

/// True iff every pose in `[lo, hi]` is present in `set`.
fn box_fully_in(lo: &[i64], hi: &[i64], set: &FxHashSet<Vec<i64>>) -> bool {
    let mut ok = true;
    for_each_pose(lo, hi, |p| {
        if ok && !set.contains(p) {
            ok = false;
        }
    });
    ok
}

// --- belief + body erosion ---------------------------------------------

/// Belief point -> (raw value, passable-per-`passable_values`). Only
/// poses within `[focus_lo, focus_hi]` are read — foveation: cells the
/// agent has observed OUTSIDE the current focus stay raw/undecoded for
/// this call.
fn read_belief(
    graph: &TypedGraph,
    syms: &QSyms,
    game: NodeID,
    ndim: usize,
    focus_lo: &[i64],
    focus_hi: &[i64],
    passable: &FxHashSet<i64>,
) -> FxHashMap<Vec<i64>, (i64, bool)> {
    let mut map: FxHashMap<Vec<i64>, (i64, bool)> = FxHashMap::default();
    for cell in graph.neighbours(game, Some(syms.has_cell)) {
        if !graph.has_node(cell) {
            continue;
        }
        let attrs = &graph.node(cell).attrs;
        let pose: Option<Vec<i64>> = match attrs.get(&syms.pose) {
            Some(Value::Tuple(items) | Value::List(items)) if items.len() == ndim => {
                let mut v = Vec::with_capacity(items.len());
                let mut ok = true;
                for it in items.iter() {
                    match it {
                        Value::Int(i) => v.push(*i),
                        Value::Float(f) => v.push(*f as i64),
                        _ => {
                            ok = false;
                            break;
                        }
                    }
                }
                if ok {
                    Some(v)
                } else {
                    None
                }
            }
            _ if ndim == 2 => {
                match (
                    read_num(attrs.get(&syms.row)),
                    read_num(attrs.get(&syms.col)),
                ) {
                    (Some(r), Some(c)) => Some(vec![r, c]),
                    _ => None,
                }
            }
            _ => None,
        };
        let Some(pose) = pose else { continue };
        if pose.len() != ndim {
            continue;
        }
        let mut in_focus = true;
        for d in 0..ndim {
            if pose[d] < focus_lo[d] || pose[d] > focus_hi[d] {
                in_focus = false;
                break;
            }
        }
        if !in_focus {
            continue;
        }
        let Some(v) = read_num(attrs.get(&syms.value)) else {
            continue;
        };
        let is_passable = passable.contains(&v);
        map.insert(pose, (v, is_passable));
    }
    map
}

/// The offset set a body occupies relative to its anchor.
fn body_offsets(body: &BodySpec, ndim: usize) -> Vec<Vec<i64>> {
    match body {
        BodySpec::Offsets(o) => o.clone(),
        BodySpec::Extents(ext) => {
            let mut offs: Vec<Vec<i64>> = vec![vec![0i64; ndim]];
            for d in 0..ndim {
                let e = ext.get(d).copied().unwrap_or(1).max(1);
                let mut next = Vec::with_capacity(offs.len() * e as usize);
                for o in &offs {
                    for k in 0..e {
                        let mut o2 = o.clone();
                        o2[d] = k;
                        next.push(o2);
                    }
                }
                offs = next;
            }
            offs
        }
    }
}

/// Config-space admissibility: an anchor pose `p` is admissible for the
/// body iff every offset cell `p + o` is a KNOWN, passable belief point.
fn body_admissible(
    belief: &FxHashMap<Vec<i64>, (i64, bool)>,
    offsets: &[Vec<i64>],
    anchor: &[i64],
) -> bool {
    for o in offsets {
        let mut p = anchor.to_vec();
        for d in 0..p.len() {
            p[d] += o[d];
        }
        match belief.get(&p) {
            Some((_, true)) => {}
            _ => return false,
        }
    }
    true
}

// --- greedy N-dim maximal-box decomposition -----------------------------

/// Greedy maximal-box cover: repeatedly seeds on the lexicographically
/// smallest remaining candidate, grows a box dim-by-dim (0, 1, ..,
/// ndim-1) as far as it can stay fully covered by `candidates`, then
/// removes the box's poses from `candidates` and repeats. Not globally
/// optimal (true maximal-rectangle decomposition is a harder problem),
/// but deterministic and — per the design's "flood does not occur per
/// pixel... remainder goes to more detail" — degrades to unit boxes for
/// any residue rather than failing.
fn decompose_region(
    candidates: &mut FxHashSet<Vec<i64>>,
    ndim: usize,
    min_extent: &[i64],
) -> Vec<(Vec<i64>, Vec<i64>)> {
    let mut out = Vec::new();
    while !candidates.is_empty() {
        let seed = candidates
            .iter()
            .min()
            .cloned()
            .expect("non-empty checked above");
        let lo = seed.clone();
        let mut hi = seed.clone();
        for d in 0..ndim {
            let step = min_extent.get(d).copied().unwrap_or(1).max(1);
            // Coarse strides first (perf only — see QuantizeParams::min_extent doc).
            loop {
                let mut try_hi = hi.clone();
                try_hi[d] += step;
                if box_fully_in(&lo, &try_hi, candidates) {
                    hi[d] = try_hi[d];
                } else {
                    break;
                }
            }
            // Fine 1-at-a-time correction to the exact maximal boundary.
            if step > 1 {
                loop {
                    let mut try_hi = hi.clone();
                    try_hi[d] += 1;
                    if box_fully_in(&lo, &try_hi, candidates) {
                        hi[d] = try_hi[d];
                    } else {
                        break;
                    }
                }
            }
        }
        for_each_pose(&lo, &hi, |p| {
            candidates.remove(p);
        });
        out.push((lo, hi));
    }
    out
}

/// A stale quantum with `stale_dim`/`stale_pose` set is replaced by
/// re-decomposing ONLY along `stale_dim`: scan every index along that
/// dim (holding the ORIGINAL box's extents fixed in every other dim),
/// group maximal contiguous runs of fully-admissible hyperplane slices
/// into boxes (other dims' extents thus stay byte-for-byte identical to
/// the original quantum), and — for any index whose hyperplane is only
/// PARTIALLY admissible (a genuinely interior, not full-width, block) —
/// fall back to the general greedy decomposer restricted to that thin
/// slice, so correctness holds even outside the simple "whole hyperplane
/// blocked" case (still only ever touches `stale_dim`-adjacent bounds).
fn split_along_dim(
    lo: &[i64],
    hi: &[i64],
    dim: usize,
    admissible: &FxHashSet<Vec<i64>>,
    min_extent: &[i64],
) -> Vec<(Vec<i64>, Vec<i64>)> {
    let ndim = lo.len();
    let mut out = Vec::new();
    let mut run_start: Option<i64> = None;
    let mut k = lo[dim];
    while k <= hi[dim] {
        let mut slice_lo = lo.to_vec();
        slice_lo[dim] = k;
        let mut slice_hi = hi.to_vec();
        slice_hi[dim] = k;
        if box_fully_in(&slice_lo, &slice_hi, admissible) {
            if run_start.is_none() {
                run_start = Some(k);
            }
        } else {
            if let Some(rs) = run_start.take() {
                let mut blo = lo.to_vec();
                blo[dim] = rs;
                let mut bhi = hi.to_vec();
                bhi[dim] = k - 1;
                out.push((blo, bhi));
            }
            // Partial hyperplane at k — finer decompose, restricted to
            // this one thin slice, using the real admissible set.
            let mut slice_candidates: FxHashSet<Vec<i64>> = FxHashSet::default();
            for_each_pose(&slice_lo, &slice_hi, |pose| {
                if admissible.contains(pose) {
                    slice_candidates.insert(pose.to_vec());
                }
            });
            let mut sub = decompose_region(&mut slice_candidates, ndim, min_extent);
            out.append(&mut sub);
        }
        k += 1;
    }
    if let Some(rs) = run_start.take() {
        let mut blo = lo.to_vec();
        blo[dim] = rs;
        let mut bhi = hi.to_vec();
        bhi[dim] = hi[dim];
        out.push((blo, bhi));
    }
    out
}

// --- adjacency / portals -------------------------------------------------

/// If boxes `a` and `b` share a face (touch along exactly one dim, with
/// non-empty overlap in every other dim), return `(dim, dir, span_lo,
/// span_hi)` where `dir` is the direction of travel FROM `a` TO `b` along
/// `dim` (+1 if `b` sits on `a`'s + side, -1 if on its - side). `span_lo`/
/// `span_hi` carry the shared overlap window per dim (meaningful for dims
/// != `dim`; the `dim`-th entry is the boundary coordinate on each side,
/// informational only).
fn face_adjacent(
    a_lo: &[i64],
    a_hi: &[i64],
    b_lo: &[i64],
    b_hi: &[i64],
    ndim: usize,
) -> Option<(usize, i64, Vec<i64>, Vec<i64>)> {
    for d in 0..ndim {
        let mut span_lo = vec![0i64; ndim];
        let mut span_hi = vec![0i64; ndim];
        let mut others_ok = true;
        for e in 0..ndim {
            if e == d {
                continue;
            }
            let lo = a_lo[e].max(b_lo[e]);
            let hi = a_hi[e].min(b_hi[e]);
            if lo > hi {
                others_ok = false;
                break;
            }
            span_lo[e] = lo;
            span_hi[e] = hi;
        }
        if !others_ok {
            continue;
        }
        if a_hi[d] + 1 == b_lo[d] {
            span_lo[d] = a_hi[d];
            span_hi[d] = b_lo[d];
            return Some((d, 1, span_lo, span_hi));
        }
        if b_hi[d] + 1 == a_lo[d] {
            span_lo[d] = b_hi[d];
            span_hi[d] = a_lo[d];
            return Some((d, -1, span_lo, span_hi));
        }
    }
    None
}

/// Maximal boxes of UNKNOWN poses (absent from `belief`) in the thin
/// hyperplane just past quantum `[lo, hi]`'s face along `dim`/`dir`,
/// clipped to focus. Empty if the boundary itself is outside focus, or
/// if every adjacent pose is already known (no frontier needed there).
fn unknown_faces(
    belief: &FxHashMap<Vec<i64>, (i64, bool)>,
    lo: &[i64],
    hi: &[i64],
    dim: usize,
    dir: i64,
    focus_lo: &[i64],
    focus_hi: &[i64],
    ndim: usize,
    min_extent: &[i64],
) -> Vec<(Vec<i64>, Vec<i64>)> {
    let boundary = if dir > 0 { hi[dim] + 1 } else { lo[dim] - 1 };
    if boundary < focus_lo[dim] || boundary > focus_hi[dim] {
        return Vec::new();
    }
    let mut hyper_lo = lo.to_vec();
    hyper_lo[dim] = boundary;
    let mut hyper_hi = hi.to_vec();
    hyper_hi[dim] = boundary;
    let mut candidates: FxHashSet<Vec<i64>> = FxHashSet::default();
    for_each_pose(&hyper_lo, &hyper_hi, |pose| {
        if !belief.contains_key(pose) {
            candidates.insert(pose.to_vec());
        }
    });
    decompose_region(&mut candidates, ndim, min_extent)
}

// --- node/edge minting ---------------------------------------------------

fn mint_quantum(
    s: &mut Substrate,
    syms: &QSyms,
    game: NodeID,
    ndim: usize,
    lo: &[i64],
    hi: &[i64],
    kind: &str,
    body_key: &str,
    epoch: i64,
) -> NodeID {
    let kind_sym = s.interner.intern(kind);
    let body_key_sym = s.interner.intern(body_key);
    let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
    attrs.insert(syms.lo, int_tuple(lo));
    attrs.insert(syms.hi, int_tuple(hi));
    attrs.insert(syms.ndim, Value::Int(ndim as i64));
    attrs.insert(syms.kind, Value::Str(kind_sym));
    attrs.insert(syms.body_key, Value::Str(body_key_sym));
    attrs.insert(syms.epoch, Value::Int(epoch));
    attrs.insert(syms.stale, Value::Int(0));
    attrs.insert(syms.visited, Value::Int(0));
    attrs.insert(syms.qdist, Value::Float(-1.0));
    let nid = s.add_node(syms.quantum, attrs);
    let _ = s
        .graph
        .insert_edge(nid, syms.in_space, game, FxHashMap::default());
    nid
}

#[allow(clippy::too_many_arguments)]
fn insert_portal(
    s: &mut Substrate,
    syms: &QSyms,
    src: NodeID,
    tgt: NodeID,
    dim: usize,
    dir: i64,
    span_lo: &[i64],
    span_hi: &[i64],
    oneway_ok: i64,
) {
    let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
    attrs.insert(syms.dim, Value::Int(dim as i64));
    attrs.insert(syms.dir, Value::Int(dir));
    attrs.insert(syms.span_lo, int_tuple(span_lo));
    attrs.insert(syms.span_hi, int_tuple(span_hi));
    attrs.insert(syms.cost, Value::Int(1));
    attrs.insert(syms.oneway_ok, Value::Int(oneway_ok));
    let _ = s.graph.insert_edge(src, syms.portal, tgt, attrs);
}

// --- the primitive --------------------------------------------------------

/// Decode the belief within `focus` into body-conditional `SpaceQuantum`
/// boxes + `portal` edges + `frontier` quanta. See module docs for the
/// full graph vocabulary written. Incremental: existing (same
/// `game`+`body_key`) passable quanta that are not `stale` and still
/// wholly within the current focus are REUSED (kept in place, epoch
/// stamped); `stale` quanta are deleted and replaced (split along
/// `stale_dim` only, when given); quanta that fall outside the current
/// focus are dropped (foveation — the quantized layer only exists within
/// focus; the underlying Cell belief is untouched and persists). Frontier
/// quanta are always regenerated fresh (cheap to derive, not memoried).
pub fn space_quantize(s: &mut Substrate, p: QuantizeParams) -> Result<QuantizeSummary, String> {
    let ndim = p.ndim;
    if ndim == 0 {
        return Err("space_quantize: ndim must be >= 1".to_string());
    }
    if p.focus_lo.len() != ndim || p.focus_hi.len() != ndim {
        return Err("space_quantize: focus_lo/focus_hi length must equal ndim".to_string());
    }
    for d in 0..ndim {
        if p.focus_hi[d] < p.focus_lo[d] {
            return Err(format!("space_quantize: focus_hi[{d}] < focus_lo[{d}]"));
        }
    }
    if !s.graph.has_node(p.game) {
        return Err("space_quantize: game node does not exist".to_string());
    }

    let syms = QSyms::new(&mut s.interner);
    let passable: FxHashSet<i64> = p.passable_values.iter().copied().collect();
    let offsets = body_offsets(&p.body, ndim);
    let min_extent: Vec<i64> = (0..ndim)
        .map(|d| p.min_extent.get(d).copied().unwrap_or(1).max(1))
        .collect();

    // 1. Belief, within focus only (foveation).
    let belief = read_belief(
        &s.graph,
        &syms,
        p.game,
        ndim,
        &p.focus_lo,
        &p.focus_hi,
        &passable,
    );

    // 2. Body-conditional admissibility over every anchor pose in focus.
    let mut admissible: FxHashSet<Vec<i64>> = FxHashSet::default();
    for_each_pose(&p.focus_lo, &p.focus_hi, |pose| {
        if body_admissible(&belief, &offsets, pose) {
            admissible.insert(pose.to_vec());
        }
    });

    // 3. Existing quanta for this (game, body_key) lineage.
    let existing: Vec<NodeID> = s
        .graph
        .in_neighbours(p.game, Some(syms.in_space))
        .into_iter()
        .filter(|&nid| s.graph.has_node(nid) && s.graph.node(nid).type_ == syms.quantum)
        .filter(|&nid| {
            read_str(&s.graph, &s.interner, nid, syms.body_key).as_deref()
                == Some(p.body_key.as_str())
        })
        .collect();

    let mut kept: Vec<(NodeID, Vec<i64>, Vec<i64>)> = Vec::new();
    let mut to_delete: Vec<NodeID> = Vec::new();
    let mut split_boxes: Vec<(Vec<i64>, Vec<i64>)> = Vec::new();

    for nid in existing {
        let kind = read_str(&s.graph, &s.interner, nid, syms.kind);
        if kind.as_deref() == Some("frontier") {
            // Frontiers are always cheap to re-derive — never incrementally kept.
            to_delete.push(nid);
            continue;
        }
        let (lo, hi) = match (
            read_i64_list(&s.graph, nid, syms.lo),
            read_i64_list(&s.graph, nid, syms.hi),
        ) {
            (Some(lo), Some(hi)) if lo.len() == ndim && hi.len() == ndim => (lo, hi),
            _ => {
                to_delete.push(nid);
                continue;
            }
        };
        let within_focus = (0..ndim).all(|d| lo[d] >= p.focus_lo[d] && hi[d] <= p.focus_hi[d]);
        if !within_focus {
            to_delete.push(nid);
            continue;
        }
        let stale = read_num(s.graph.node(nid).attrs.get(&syms.stale)).unwrap_or(0) != 0;
        if !stale {
            kept.push((nid, lo, hi));
            continue;
        }
        to_delete.push(nid);
        let stale_dim = read_num(s.graph.node(nid).attrs.get(&syms.stale_dim));
        if let Some(d64) = stale_dim {
            if d64 >= 0 && (d64 as usize) < ndim {
                let mut boxes = split_along_dim(&lo, &hi, d64 as usize, &admissible, &min_extent);
                split_boxes.append(&mut boxes);
            }
        }
        // stale without a usable stale_dim: generic invalidation — its
        // bounds simply fall through to the general uncovered-region
        // decomposition below (nothing more to do here).
    }

    for nid in &to_delete {
        s.remove_node(*nid);
    }

    // 4. Remaining admissible-but-uncovered poses -> general decomposition.
    let mut covered: FxHashSet<Vec<i64>> = FxHashSet::default();
    for (_, lo, hi) in &kept {
        for_each_pose(lo, hi, |pose| {
            covered.insert(pose.to_vec());
        });
    }
    for (lo, hi) in &split_boxes {
        for_each_pose(lo, hi, |pose| {
            covered.insert(pose.to_vec());
        });
    }
    let mut remaining: FxHashSet<Vec<i64>> = admissible.difference(&covered).cloned().collect();
    let decomposed = decompose_region(&mut remaining, ndim, &min_extent);

    // 5. Materialise. `all_passable` carries (node, lo, hi, is_new) for the
    // portal + frontier passes below.
    let mut summary = QuantizeSummary::default();
    let mut all_passable: Vec<(NodeID, Vec<i64>, Vec<i64>, bool)> = Vec::new();

    for (nid, lo, hi) in kept {
        s.set_attr(nid, syms.epoch, Value::Int(p.epoch));
        summary.reused += 1;
        all_passable.push((nid, lo, hi, false));
    }
    for (lo, hi) in split_boxes {
        let nid = mint_quantum(
            s,
            &syms,
            p.game,
            ndim,
            &lo,
            &hi,
            "passable",
            &p.body_key,
            p.epoch,
        );
        summary.split += 1;
        all_passable.push((nid, lo, hi, true));
    }
    for (lo, hi) in decomposed {
        let nid = mint_quantum(
            s,
            &syms,
            p.game,
            ndim,
            &lo,
            &hi,
            "passable",
            &p.body_key,
            p.epoch,
        );
        all_passable.push((nid, lo, hi, true));
    }
    summary.quanta = all_passable.len();

    // 6. Portals among passable quanta — only (re)computed for pairs where
    // at least one side is new this call, so a kept<->kept portal (which
    // may carry a learned `oneway_ok=0` from a Rule) is left untouched.
    let mut portal_count = 0usize;
    for i in 0..all_passable.len() {
        for j in (i + 1)..all_passable.len() {
            let (a_nid, a_lo, a_hi, a_new) = &all_passable[i];
            let (b_nid, b_lo, b_hi, b_new) = &all_passable[j];
            if !*a_new && !*b_new {
                continue;
            }
            if let Some((dim, dir, span_lo, span_hi)) = face_adjacent(a_lo, a_hi, b_lo, b_hi, ndim)
            {
                insert_portal(s, &syms, *a_nid, *b_nid, dim, dir, &span_lo, &span_hi, 1);
                insert_portal(s, &syms, *b_nid, *a_nid, dim, -dir, &span_lo, &span_hi, 1);
                portal_count += 2;
            }
        }
    }

    // 7. Frontier quanta — thin boxes of unknown poses bordering a
    // passable quantum's face, within focus.
    let mut frontier_count = 0usize;
    for (nid, lo, hi, _) in &all_passable {
        for dim in 0..ndim {
            for dir in [-1i64, 1i64] {
                let boxes = unknown_faces(
                    &belief,
                    lo,
                    hi,
                    dim,
                    dir,
                    &p.focus_lo,
                    &p.focus_hi,
                    ndim,
                    &min_extent,
                );
                for (flo, fhi) in boxes {
                    let fnid = mint_quantum(
                        s,
                        &syms,
                        p.game,
                        ndim,
                        &flo,
                        &fhi,
                        "frontier",
                        &p.body_key,
                        p.epoch,
                    );
                    insert_portal(s, &syms, *nid, fnid, dim, dir, &flo, &fhi, 1);
                    insert_portal(s, &syms, fnid, *nid, dim, -dir, &flo, &fhi, 1);
                    frontier_count += 1;
                    portal_count += 2;
                }
            }
        }
    }
    summary.portals = portal_count;
    summary.frontiers = frontier_count;

    Ok(summary)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::checker::ConsistencyChecker;
    use crate::grammar::Grammar;
    use std::collections::VecDeque;

    fn fresh_substrate() -> Substrate {
        Substrate::new(ConsistencyChecker::new(Grammar::new()))
    }

    /// Mint a `game` node plus one Cell per `(pose, value)`, wired via
    /// `has_cell` (bypassing Γ — the same "world adapter primitive"
    /// bookkeeping edges `slide_flood`'s callers use). No `neighbour`
    /// lattice is required — `space_quantize` reads `has_cell` + pose
    /// attrs directly, not a BFS over `neighbour`.
    fn build_world(s: &mut Substrate, cells: &[(Vec<i64>, i64)]) -> NodeID {
        let game_t = s.interner.intern("Game");
        let cell_t = s.interner.intern("Cell");
        let has_cell = s.interner.intern("has_cell");
        let row_k = s.interner.intern("row");
        let col_k = s.interner.intern("col");
        let pose_k = s.interner.intern("pose");
        let value_k = s.interner.intern("value");
        let game = s.add_node(game_t, FxHashMap::default());
        for (pose, value) in cells {
            let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
            if pose.len() == 2 {
                attrs.insert(row_k, Value::Int(pose[0]));
                attrs.insert(col_k, Value::Int(pose[1]));
            } else {
                attrs.insert(pose_k, int_tuple(pose));
            }
            attrs.insert(value_k, Value::Int(*value));
            let cell = s.add_node(cell_t, attrs);
            let _ = s
                .graph
                .insert_edge(game, has_cell, cell, FxHashMap::default());
        }
        game
    }

    fn rect_2d(r0: i64, r1: i64, c0: i64, c1: i64, value: i64) -> Vec<(Vec<i64>, i64)> {
        let mut out = Vec::new();
        for r in r0..=r1 {
            for c in c0..=c1 {
                out.push((vec![r, c], value));
            }
        }
        out
    }

    fn quanta_of(s: &Substrate, syms_quantum: Sym, game: NodeID, body_key: &str) -> Vec<NodeID> {
        let in_space = s.interner.lookup("in_space").unwrap();
        let body_key_sym = s.interner.lookup("body_key").unwrap();
        s.graph
            .in_neighbours(game, Some(in_space))
            .into_iter()
            .filter(|&nid| s.graph.node(nid).type_ == syms_quantum)
            .filter(|&nid| {
                read_str(&s.graph, &s.interner, nid, body_key_sym).as_deref() == Some(body_key)
            })
            .collect()
    }

    fn kind_of(s: &Substrate, nid: NodeID) -> String {
        let kind_sym = s.interner.lookup("kind").unwrap();
        read_str(&s.graph, &s.interner, nid, kind_sym).unwrap_or_default()
    }

    fn lo_hi_of(s: &Substrate, nid: NodeID) -> (Vec<i64>, Vec<i64>) {
        let lo_sym = s.interner.lookup("lo").unwrap();
        let hi_sym = s.interner.lookup("hi").unwrap();
        (
            read_i64_list(&s.graph, nid, lo_sym).unwrap(),
            read_i64_list(&s.graph, nid, hi_sym).unwrap(),
        )
    }

    fn portal_targets(s: &Substrate, nid: NodeID) -> Vec<NodeID> {
        let portal_sym = s.interner.lookup("portal").unwrap();
        s.graph.neighbours(nid, Some(portal_sym))
    }

    /// 1x1 rigid body over a 2D belief.
    fn body1() -> BodySpec {
        BodySpec::Extents(vec![1, 1])
    }

    #[test]
    fn corridor_and_room_decompose_with_per_dim_extents_and_one_portal() {
        let mut s = fresh_substrate();
        // 5 rows x 7 cols. Walls (value 9) everywhere except:
        //   row1, cols1..5: a 1-wide corridor
        //   rows2-3, cols3-4: a 2x2 room, connected to the corridor at (2,3)/(2,4)
        let mut cells = rect_2d(0, 4, 0, 6, 9);
        let mut passable_poses: FxHashSet<Vec<i64>> = FxHashSet::default();
        for c in 1..=5 {
            passable_poses.insert(vec![1, c]);
        }
        for r in 2..=3 {
            for c in 3..=4 {
                passable_poses.insert(vec![r, c]);
            }
        }
        for (pose, value) in cells.iter_mut() {
            if passable_poses.contains(pose) {
                *value = 0;
            }
        }
        let game = build_world(&mut s, &cells);

        let params = QuantizeParams {
            game,
            ndim: 2,
            body_key: "b1".to_string(),
            body: body1(),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![4, 6],
            epoch: 1,
            min_extent: vec![1, 1],
        };
        let summary = space_quantize(&mut s, params).expect("quantize ok");
        assert_eq!(summary.quanta, 2, "corridor + room = 2 passable quanta");
        assert_eq!(
            summary.frontiers, 0,
            "fully wall-enclosed — no unknown border"
        );
        assert_eq!(summary.portals, 2, "one bidirectional portal pair");

        let quantum_t = s.interner.lookup("SpaceQuantum").unwrap();
        let quanta = quanta_of(&s, quantum_t, game, "b1");
        assert_eq!(quanta.len(), 2);
        let mut boxes: Vec<(Vec<i64>, Vec<i64>)> =
            quanta.iter().map(|&n| lo_hi_of(&s, n)).collect();
        boxes.sort();
        assert_eq!(
            boxes[0],
            (vec![1, 1], vec![1, 5]),
            "corridor: 1 row x 5 cols"
        );
        assert_eq!(boxes[1], (vec![2, 3], vec![3, 4]), "room: 2 rows x 2 cols");
    }

    #[test]
    fn three_d_lattice_wall_plane_with_hole_has_a_portal_route() {
        let mut s = fresh_substrate();
        // 4x4x4 cube, pose=[x,y,z]. z=0,2,3 all passable(0); z=1 all wall(9)
        // except one hole at (2,2,1).
        let mut cells = Vec::new();
        for x in 0..4 {
            for y in 0..4 {
                for z in 0..4 {
                    let v = if z == 1 && !(x == 2 && y == 2) { 9 } else { 0 };
                    cells.push((vec![x, y, z], v));
                }
            }
        }
        let game = build_world(&mut s, &cells);
        let params = QuantizeParams {
            game,
            ndim: 3,
            body_key: "b1".to_string(),
            body: BodySpec::Extents(vec![1, 1, 1]),
            passable_values: vec![0],
            focus_lo: vec![0, 0, 0],
            focus_hi: vec![3, 3, 3],
            epoch: 1,
            min_extent: vec![1, 1, 1],
        };
        let summary = space_quantize(&mut s, params).expect("quantize ok");
        assert!(summary.quanta >= 2, "at least the hole + one bulk region");
        // per-dim extents proof: at least one quantum has ndim==3 and a
        // non-trivial extent along some dim.
        let quantum_t = s.interner.lookup("SpaceQuantum").unwrap();
        let quanta = quanta_of(&s, quantum_t, game, "b1");
        assert!(quanta.iter().any(|&n| {
            let (lo, hi) = lo_hi_of(&s, n);
            lo.len() == 3 && (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1) > 1
        }));

        // route exists: BFS over portal edges from the quantum containing
        // (0,0,0) to the quantum containing (0,0,3).
        let find_quantum_containing =
            |s: &Substrate, quanta: &[NodeID], pose: &[i64]| -> Option<NodeID> {
                quanta.iter().copied().find(|&n| {
                    let (lo, hi) = lo_hi_of(s, n);
                    (0..3).all(|d| pose[d] >= lo[d] && pose[d] <= hi[d])
                })
            };
        let start = find_quantum_containing(&s, &quanta, &[0, 0, 0]).expect("start quantum exists");
        let goal = find_quantum_containing(&s, &quanta, &[0, 0, 3]).expect("goal quantum exists");
        let mut seen: FxHashSet<NodeID> = FxHashSet::default();
        let mut q: VecDeque<NodeID> = VecDeque::new();
        q.push_back(start);
        seen.insert(start);
        let mut reached = false;
        while let Some(n) = q.pop_front() {
            if n == goal {
                reached = true;
                break;
            }
            for t in portal_targets(&s, n) {
                if seen.insert(t) {
                    q.push_back(t);
                }
            }
        }
        assert!(
            reached,
            "z=0 layer must reach z=3 layer through the (2,2,1) hole"
        );
    }

    #[test]
    fn two_bodies_over_one_belief_give_different_quanta() {
        let mut s = fresh_substrate();
        // Two 4x4 rooms joined by a 1-wide, 3-long gap at row=1..3, col=4.
        let mut cells = rect_2d(0, 5, 0, 8, 9);
        let mut passable: FxHashSet<Vec<i64>> = FxHashSet::default();
        for r in 0..4 {
            for c in 0..4 {
                passable.insert(vec![r, c]);
            }
        }
        for r in 1..=2 {
            passable.insert(vec![r, 4]);
        }
        for r in 0..4 {
            for c in 5..9 {
                passable.insert(vec![r, c]);
            }
        }
        for (pose, value) in cells.iter_mut() {
            if passable.contains(pose) {
                *value = 0;
            }
        }
        let game = build_world(&mut s, &cells);

        let quantum_t = s.interner.intern("SpaceQuantum");

        let p1x1 = QuantizeParams {
            game,
            ndim: 2,
            body_key: "small".to_string(),
            body: BodySpec::Extents(vec![1, 1]),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![5, 8],
            epoch: 1,
            min_extent: vec![1, 1],
        };
        space_quantize(&mut s, p1x1).expect("1x1 quantize ok");
        let quanta_small = quanta_of(&s, quantum_t, game, "small");
        // the 1-wide gap admits a 1x1 body: covers cell (1,4) and/or (2,4).
        let small_covers_gap = quanta_small.iter().any(|&n| {
            let (lo, hi) = lo_hi_of(&s, n);
            (0..2).all(|d| lo[d] <= 4 && hi[d] >= 1) && lo[1] <= 4 && hi[1] >= 4
        });

        let p2x2 = QuantizeParams {
            game,
            ndim: 2,
            body_key: "big".to_string(),
            body: BodySpec::Extents(vec![2, 2]),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![5, 8],
            epoch: 1,
            min_extent: vec![1, 1],
        };
        space_quantize(&mut s, p2x2).expect("2x2 quantize ok");
        let quanta_big = quanta_of(&s, quantum_t, game, "big");
        // no 2x2-body anchor pose can straddle the 1-wide gap (anchor at
        // col 3 or 4 always needs a wall cell in its footprint).
        let big_crosses_gap = quanta_big.iter().any(|&n| {
            let (lo, hi) = lo_hi_of(&s, n);
            lo[1] <= 3 && hi[1] >= 5
        });

        assert!(small_covers_gap, "1x1 body must find the gap admissible");
        assert!(!big_crosses_gap, "2x2 body must NOT bridge a 1-wide gap");
        assert_ne!(quanta_small.len(), 0);
        assert_ne!(quanta_big.len(), 0);
    }

    #[test]
    fn interior_block_splits_along_exactly_one_dim() {
        let mut s = fresh_substrate();
        let cells = rect_2d(0, 4, 0, 4, 0); // 5x5, all passable
        let game = build_world(&mut s, &cells);
        let params = QuantizeParams {
            game,
            ndim: 2,
            body_key: "b1".to_string(),
            body: body1(),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![4, 4],
            epoch: 1,
            min_extent: vec![1, 1],
        };
        let s1 = space_quantize(&mut s, params).expect("first decode ok");
        assert_eq!(s1.quanta, 1, "one open room = one quantum");
        let quantum_t = s.interner.lookup("SpaceQuantum").unwrap();
        let quanta = quanta_of(&s, quantum_t, game, "b1");
        assert_eq!(quanta.len(), 1);
        let original = quanta[0];
        assert_eq!(lo_hi_of(&s, original), (vec![0, 0], vec![4, 4]));

        // Observation: row 2 (the whole width) became a wall. Update the
        // belief AND mark the quantum stale/stale_dim/stale_pose the way
        // a Part-B `qf_stale_on_block` Rule would (white-box: this test
        // exercises the primitive's read side of that contract directly).
        let value_k = s.interner.lookup("value").unwrap();
        // Re-derive cell nodes by walking has_cell (build_world didn't
        // hand back per-pose node ids).
        let has_cell = s.interner.lookup("has_cell").unwrap();
        let row_k = s.interner.lookup("row").unwrap();
        let col_k = s.interner.lookup("col").unwrap();
        for cell in s.graph.neighbours(game, Some(has_cell)) {
            let r = read_num(s.graph.node(cell).attrs.get(&row_k));
            if r == Some(2) {
                s.set_attr(cell, value_k, Value::Int(9));
            }
        }
        let stale_k = s.interner.lookup("stale").unwrap();
        let stale_dim_k = s.interner.lookup("stale_dim").unwrap();
        let stale_pose_k = s.interner.intern("stale_pose");
        s.set_attr(original, stale_k, Value::Int(1));
        s.set_attr(original, stale_dim_k, Value::Int(0)); // row dim
        s.set_attr(original, stale_pose_k, Value::Int(2));
        let _ = col_k;

        let params2 = QuantizeParams {
            game,
            ndim: 2,
            body_key: "b1".to_string(),
            body: body1(),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![4, 4],
            epoch: 2,
            min_extent: vec![1, 1],
        };
        let s2 = space_quantize(&mut s, params2).expect("second decode ok");
        assert_eq!(
            s2.split, 2,
            "split into exactly 2 boxes (above/below the blocked row)"
        );
        assert_eq!(s2.reused, 0, "the stale quantum itself is not reused");

        let quanta2 = quanta_of(&s, quantum_t, game, "b1");
        assert_eq!(quanta2.len(), 2);
        let mut boxes: Vec<(Vec<i64>, Vec<i64>)> =
            quanta2.iter().map(|&n| lo_hi_of(&s, n)).collect();
        boxes.sort();
        assert_eq!(
            boxes[0],
            (vec![0, 0], vec![1, 4]),
            "rows above the block, cols UNCHANGED"
        );
        assert_eq!(
            boxes[1],
            (vec![3, 0], vec![4, 4]),
            "rows below the block, cols UNCHANGED"
        );
    }

    #[test]
    fn frontier_minted_at_unknown_border() {
        let mut s = fresh_substrate();
        // Only a 3x3 known-passable block exists (cols 0-2); cols 3-4 have
        // no Cell nodes at all (genuinely unknown, not walls).
        let cells = rect_2d(0, 2, 0, 2, 0);
        let game = build_world(&mut s, &cells);
        let params = QuantizeParams {
            game,
            ndim: 2,
            body_key: "b1".to_string(),
            body: body1(),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![2, 4],
            epoch: 1,
            min_extent: vec![1, 1],
        };
        let summary = space_quantize(&mut s, params).expect("quantize ok");
        assert_eq!(
            summary.quanta, 1,
            "one passable quantum (the known 3x3 block)"
        );
        assert!(
            summary.frontiers >= 1,
            "must mint a frontier at the unknown col-3 border"
        );

        let quantum_t = s.interner.lookup("SpaceQuantum").unwrap();
        let quanta = quanta_of(&s, quantum_t, game, "b1");
        let frontier = quanta
            .iter()
            .copied()
            .find(|&n| kind_of(&s, n) == "frontier")
            .expect("a frontier quantum exists");
        let (flo, fhi) = lo_hi_of(&s, frontier);
        assert_eq!(flo[1], 3, "frontier starts just past the known block");
        assert_eq!(
            fhi[1], 3,
            "frontier is unit-depth along the adjacency dim (col)"
        );
        assert_eq!(
            (flo[0], fhi[0]),
            (0, 2),
            "frontier spans the full known block's row range"
        );

        // a portal connects the passable block to the frontier.
        let passable_q = quanta
            .iter()
            .copied()
            .find(|&n| kind_of(&s, n) == "passable")
            .unwrap();
        assert!(portal_targets(&s, passable_q).contains(&frontier));
        assert!(portal_targets(&s, frontier).contains(&passable_q));
    }

    #[test]
    fn incremental_decode_reuses_non_stale_quanta() {
        let mut s = fresh_substrate();
        let cells = rect_2d(0, 3, 0, 3, 0);
        let game = build_world(&mut s, &cells);
        let params1 = QuantizeParams {
            game,
            ndim: 2,
            body_key: "b1".to_string(),
            body: body1(),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![3, 3],
            epoch: 1,
            min_extent: vec![1, 1],
        };
        let s1 = space_quantize(&mut s, params1).expect("first decode ok");
        assert_eq!(s1.quanta, 1);
        let quantum_t = s.interner.lookup("SpaceQuantum").unwrap();
        let ids_before: Vec<NodeID> = quanta_of(&s, quantum_t, game, "b1");
        assert_eq!(ids_before.len(), 1);

        let params2 = QuantizeParams {
            game,
            ndim: 2,
            body_key: "b1".to_string(),
            body: body1(),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![3, 3],
            epoch: 2,
            min_extent: vec![1, 1],
        };
        let s2 = space_quantize(&mut s, params2).expect("second decode ok");
        assert_eq!(s2.reused, 1, "the one quantum is reused, not rebuilt");
        assert_eq!(s2.split, 0);
        assert_eq!(s2.quanta, 1);
        let ids_after: Vec<NodeID> = quanta_of(&s, quantum_t, game, "b1");
        assert_eq!(
            ids_before, ids_after,
            "identical node id — genuinely reused, not recreated"
        );

        let epoch_k = s.interner.lookup("epoch").unwrap();
        assert_eq!(
            read_num(s.graph.node(ids_after[0]).attrs.get(&epoch_k)),
            Some(2),
            "epoch stamped fresh"
        );
    }

    #[test]
    fn focus_bound_is_honored() {
        let mut s = fresh_substrate();
        let cells = rect_2d(0, 5, 0, 5, 0); // 6x6, all passable
        let game = build_world(&mut s, &cells);
        let params = QuantizeParams {
            game,
            ndim: 2,
            body_key: "b1".to_string(),
            body: body1(),
            passable_values: vec![0],
            focus_lo: vec![0, 0],
            focus_hi: vec![2, 2], // smaller than the belief
            epoch: 1,
            min_extent: vec![1, 1],
        };
        let summary = space_quantize(&mut s, params).expect("quantize ok");
        assert!(summary.quanta >= 1);
        let quantum_t = s.interner.lookup("SpaceQuantum").unwrap();
        for nid in quanta_of(&s, quantum_t, game, "b1") {
            let (lo, hi) = lo_hi_of(&s, nid);
            for d in 0..2 {
                assert!(
                    lo[d] >= 0 && hi[d] <= 2,
                    "quantum {:?}-{:?} must stay within the focus box",
                    lo,
                    hi
                );
            }
        }
    }
}
