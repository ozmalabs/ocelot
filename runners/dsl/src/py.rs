//! PyO3 bindings for `substrate_rs`.
//!
//! Strategy: one big `Substrate` PyClass that owns the whole (G, Γ, C,
//! arena, interner, concepts) bundle. Term construction stays on the
//! Python side as dataclass-style factories — they emit JSON dicts in
//! the wire format `jsonio.rs` produces, and the substrate ingests
//! them via `term_from_json`. This avoids minting 50 PyClasses (one
//! per Term variant) while keeping `from substrate_rs import Filter`
//! drop-in compatible with `substrate/dsl.py`.
//!
//! Value bridge:
//!   Python None / bool / int / float / str    ↔ Value scalars (Str interned)
//!   Python `NodeID(value=n)` dataclass         ↔ Value::Node
//!   Python tuple / set / frozenset / dict      ↔ Value::Tuple / Set / FrozenSet / Dict
//!
//! Errors:
//!   `InadmissibleEdge` Python exception carries the Type-1 vs Type-2
//!   distinction in its message so the Python side can match on text or
//!   on `__cause__`.

use crate::checker::ConsistencyChecker;
use crate::grammar::Grammar;
use crate::graph::{EdgeKey, NodeID};
use crate::jsonio::{grammar_from_json, grammar_to_json, term_from_json, term_to_json};
use crate::persist::{decode_value, encode_value, graph_from_value, graph_to_value};
use crate::substrate::{InadmissibleEdge as InadmissibleEdgeRs, Substrate as SubstrateRs};
use crate::sym::Sym;
use crate::term::{evaluate, Env, EvalCache, EvalCtx, TermArena, TermIdx};
use crate::value::{cmp_value, SurfaceKind, Value};
use pyo3::create_exception;
use pyo3::exceptions::{PyException, PyKeyError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyFrozenSet, PyList, PySet, PyTuple};
use rustc_hash::FxHashMap;
use serde_json::Value as J;
use smallvec::SmallVec;
use std::sync::{Arc, Mutex};

create_exception!(_native, InadmissibleEdge, PyException);

/// Python handle for an in-flight GPU motion-estimation submission.
/// `.wait()` blocks if needed, then returns the LE-i32 (mv_x, mv_y,
/// sad) triples as bytes — same layout as the synchronous variant.
/// Once waited on (or dropped), the handle is consumed.
#[cfg(feature = "gpu_me")]
#[pyclass(name = "GpuMeHandle", module = "substrate_rs._native", unsendable)]
pub struct GpuMeHandle {
    inner: Option<crate::gpu_me::MeHandle>,
}

#[cfg(feature = "gpu_me")]
#[pymethods]
impl GpuMeHandle {
    /// Block until the GPU work is complete; return the MVs.
    fn wait<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let handle = self.inner.take().ok_or_else(|| {
            pyo3::exceptions::PyRuntimeError::new_err("GpuMeHandle.wait() called twice")
        })?;
        let mvs = py
            .allow_threads(|| handle.wait())
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))?;
        let mut out = Vec::with_capacity(mvs.len() * 12);
        for m in &mvs {
            out.extend_from_slice(&m.mv_x.to_le_bytes());
            out.extend_from_slice(&m.mv_y.to_le_bytes());
            out.extend_from_slice(&(m.sad as i32).to_le_bytes());
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &out))
    }
}

/// Build a motion-compensated reference plane: for each macroblock,
/// copy from the reference at the per-MB integer-luma offset. Out-
/// of-plane reads are clamp-to-border. Returns a plane the same
/// shape as the input reference; caller hands it to the existing
/// `transcode_p_frame_static_mv0` (which then computes residual =
/// target - mc_ref at MV=(0,0)).
/// `subpel = false`: MVs are in INTEGER luma pixels (legacy path —
/// what GPU ME emits today). Reads from the reference at the integer
/// offset with clamp-to-border.
///
/// `subpel = true`: MVs are in QUARTER luma pixels. Each MB's MV is
/// decomposed into an integer part (`mv >> 2`) and a fractional part
/// (`mv & 3`); the fractional part selects one of the 16 sub-pel
/// positions per §8.4.2.2.1 and we run the vendored 6-tap FIR via
/// `h264_inter_pred::interpolate_luma`. When the fractional part is
/// (0, 0) we fall through to the integer-pel fast path.
fn apply_motion_compensation_kernel(
    reference: &[u8],
    mvs: &[(i32, i32)],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    mb_h: usize,
    subpel: bool,
) -> Vec<u8> {
    assert_eq!(reference.len(), plane_w * plane_h);
    assert_eq!(mvs.len(), mb_w * mb_h);
    let mut out = vec![0u8; plane_w * plane_h];

    // For sub-pel, the vendored interpolate_luma works in i32 (so the
    // 6-tap intermediates stay representable). Convert the reference
    // plane once up-front and share read-only across worker threads.
    // Skip the conversion entirely when subpel is off — the integer-
    // pel fast path reads u8 directly.
    let ref_i32: Option<Vec<i32>> = if subpel {
        Some(reference.iter().map(|&b| b as i32).collect())
    } else {
        None
    };

    // Parallelise across MB rows — each row chunk writes to a
    // non-overlapping strip of `out` (16 luma rows wide).
    let n_threads = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4)
        .min(mb_h);
    let rows_per_chunk = (mb_h + n_threads - 1) / n_threads;
    let recon_per_row = plane_w * 16;
    let mut chunks: Vec<(usize, usize, &mut [u8])> = Vec::with_capacity(n_threads);
    let mut remaining: &mut [u8] = &mut out;
    let mut row = 0;
    while row < mb_h {
        let last = (row + rows_per_chunk).min(mb_h);
        let n_rows = last - row;
        let (chunk, rest) = remaining.split_at_mut(n_rows * recon_per_row);
        remaining = rest;
        chunks.push((row, last, chunk));
        row = last;
    }
    let ref_i32_ref: Option<&[i32]> = ref_i32.as_deref();
    std::thread::scope(|scope| {
        for (start_row, end_row, chunk) in chunks {
            scope.spawn(move || {
                apply_mc_rows(
                    reference,
                    ref_i32_ref,
                    mvs,
                    plane_w,
                    plane_h,
                    mb_w,
                    start_row,
                    end_row,
                    subpel,
                    chunk,
                );
            });
        }
    });
    out
}

fn apply_mc_rows(
    reference: &[u8],
    reference_i32: Option<&[i32]>,
    mvs: &[(i32, i32)],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    start_row: usize,
    end_row: usize,
    subpel: bool,
    out_chunk: &mut [u8],
) {
    let w = plane_w as i32;
    let h = plane_h as i32;
    // Per-MB sub-pel destination buffer (16×16 i32 samples). Reused
    // across MBs within this row chunk to avoid per-MB allocation.
    let mut subpel_dst: Vec<i32> = if subpel { vec![0i32; 256] } else { Vec::new() };
    for mb_y in start_row..end_row {
        let local_y = mb_y - start_row;
        for mb_x in 0..mb_w {
            let (dx, dy) = mvs[mb_y * mb_w + mb_x];
            // Decompose quarter-pel MV when subpel; otherwise treat
            // the MV as an integer-pel offset (legacy).
            let (int_dx, int_dy, x_frac, y_frac) = if subpel {
                // Floor-division for signed quarter-pel → integer-pel +
                // 0..=3 fractional. Rust's `/` and `%` round toward
                // zero, so use Euclidean rem for the fractional part
                // (so −5 quarter-pel decomposes as int=−2, frac=3).
                let fx = (dx.rem_euclid(4)) as u8;
                let fy = (dy.rem_euclid(4)) as u8;
                (dx.div_euclid(4), dy.div_euclid(4), fx, fy)
            } else {
                (dx, dy, 0u8, 0u8)
            };
            let int_x0 = (mb_x * 16) as i32 + int_dx;
            let int_y0 = (mb_y * 16) as i32 + int_dy;

            if !subpel || (x_frac == 0 && y_frac == 0) {
                // Integer-pel fast path — direct clamped copy.
                for yy in 0..16 {
                    let ry = (int_y0 + yy as i32).clamp(0, h - 1);
                    let local_ty = (local_y * 16 + yy) as i32;
                    for xx in 0..16 {
                        let rx = (int_x0 + xx as i32).clamp(0, w - 1);
                        out_chunk[(local_ty * w + tx_safe(mb_x, xx)) as usize] =
                            reference[(ry * w + rx) as usize];
                    }
                }
            } else {
                // Sub-pel path — call the vendored 6-tap FIR
                // interpolator. Edge replication is done inside
                // interpolate_luma per §8.4.2.2.1 eq. 8-239/240.
                let src_i32 = reference_i32.expect("subpel requires i32 ref");
                crate::h264_inter_pred::interpolate_luma(
                    src_i32,
                    plane_w,
                    plane_w,
                    plane_h,
                    int_x0,
                    int_y0,
                    x_frac,
                    y_frac,
                    16,
                    16,
                    /*bit_depth=*/ 8,
                    &mut subpel_dst,
                    16,
                )
                .expect("interpolate_luma");
                for yy in 0..16 {
                    let local_ty = (local_y * 16 + yy) as i32;
                    for xx in 0..16 {
                        out_chunk[(local_ty * w + tx_safe(mb_x, xx)) as usize] =
                            subpel_dst[yy * 16 + xx].clamp(0, 255) as u8;
                    }
                }
            }
        }
    }
}

#[inline(always)]
fn tx_safe(mb_x: usize, xx: usize) -> i32 {
    (mb_x * 16 + xx) as i32
}

/// CPU full-search SAD motion estimation. Mirrors the GPU shader's
/// semantics: for each MB in raster order, scan a (2r+1)² window of
/// candidate offsets and return (mv_x, mv_y, sad) for the best.
/// MVs in integer luma pixels. Clamp-to-border on off-plane reads.
fn estimate_motion_cpu_kernel(
    target: &[u8],
    reference: &[u8],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    mb_h: usize,
    search_radius: i32,
) -> Vec<(i32, i32, i32)> {
    let n_mbs = mb_w * mb_h;
    let mut out = Vec::with_capacity(n_mbs);
    let w = plane_w as i32;
    let h = plane_h as i32;
    for mb_y in 0..mb_h {
        for mb_x in 0..mb_w {
            let mb_px = (mb_x * 16) as i32;
            let mb_py = (mb_y * 16) as i32;
            let mut best_sad: u32 = u32::MAX;
            let mut best_dx = 0i32;
            let mut best_dy = 0i32;
            for dy in -search_radius..=search_radius {
                for dx in -search_radius..=search_radius {
                    let mut s: u32 = 0;
                    for yy in 0..16 {
                        for xx in 0..16 {
                            let tx = (mb_px + xx).clamp(0, w - 1);
                            let ty = (mb_py + yy).clamp(0, h - 1);
                            let rx = (mb_px + xx + dx).clamp(0, w - 1);
                            let ry = (mb_py + yy + dy).clamp(0, h - 1);
                            let t = target[(ty * w + tx) as usize] as i32;
                            let r = reference[(ry * w + rx) as usize] as i32;
                            s += (t - r).unsigned_abs();
                        }
                    }
                    if s < best_sad {
                        best_sad = s;
                        best_dx = dx;
                        best_dy = dy;
                    }
                }
            }
            out.push((best_dx, best_dy, best_sad as i32));
        }
    }
    out
}

// --- sub-pel refinement ---------------------------------------------------

/// Sub-pel refinement around an integer-pel ME result. For each MB,
/// starts from the integer-pel best `(dx_int, dy_int)` and runs a
/// two-phase diamond search in quarter-pel space:
///
///   Phase 1 (half-pel): test the 8 positions at QMV offsets
///     (±2, 0), (0, ±2), (±2, ±2) from the integer baseline.
///   Phase 2 (quarter-pel): test the 8 positions at QMV offset ±1
///     around the phase-1 winner.
///
/// 17 SAD evaluations per MB worst-case. Sub-pel SADs are computed
/// against the vendored 6-tap FIR (§8.4.2.2.1, see NOTICES.md).
/// Returns quarter-pel MVs: `(qmv_x, qmv_y, sad)` per MB.
///
/// The diamond is symmetric around the integer best, so motion in any
/// quadrant is reachable without bias toward the south-east half-cell
/// that a naive `xf ∈ 0..=3, yf ∈ 0..=3` sweep would have.
/// Refinement search mode: `Diamond` is the cheap 2-phase
/// (half-pel diamond → quarter-pel diamond, 17 SAD evals/MB),
/// `Full` sweeps the full 5×5 QMV grid (offsets ∈ {-2..=2}² = 25
/// SADs/MB) and finds the true minimum within ±half-pel of the
/// integer baseline. `Full` is exhaustive within its search radius
/// but ~45 % more compute. Pick `Full` when quality matters more
/// than refinement-time latency.
#[derive(Copy, Clone)]
pub enum SubpelMode {
    Diamond,
    Full,
}

fn refine_motion_subpel_kernel(
    target: &[u8],
    reference: &[u8],
    mvs_int: &[(i32, i32)],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    mb_h: usize,
    mode: SubpelMode,
) -> Vec<(i32, i32, i32)> {
    assert_eq!(target.len(), plane_w * plane_h);
    assert_eq!(reference.len(), plane_w * plane_h);
    assert_eq!(mvs_int.len(), mb_w * mb_h);

    // Sub-pel FIR needs i32 headroom for 6-tap intermediates; widen once
    // and share read-only across worker threads.
    let ref_i32: Vec<i32> = reference.iter().map(|&b| b as i32).collect();

    let mut out: Vec<(i32, i32, i32)> = vec![(0, 0, 0); mb_w * mb_h];

    let n_threads = std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(4)
        .min(mb_h);
    let rows_per_chunk = (mb_h + n_threads - 1) / n_threads;

    let mut chunks: Vec<(usize, usize, &mut [(i32, i32, i32)])> = Vec::new();
    let mut remaining: &mut [(i32, i32, i32)] = &mut out;
    let mut row = 0;
    while row < mb_h {
        let last = (row + rows_per_chunk).min(mb_h);
        let n_rows = last - row;
        let (chunk, rest) = remaining.split_at_mut(n_rows * mb_w);
        remaining = rest;
        chunks.push((row, last, chunk));
        row = last;
    }

    let ref_i32_ref: &[i32] = &ref_i32;
    std::thread::scope(|scope| {
        for (start_row, end_row, chunk) in chunks {
            scope.spawn(move || {
                refine_subpel_rows(
                    target,
                    reference,
                    ref_i32_ref,
                    mvs_int,
                    plane_w,
                    plane_h,
                    mb_w,
                    start_row,
                    end_row,
                    mode,
                    chunk,
                );
            });
        }
    });
    out
}

/// QMV offsets relative to (qmv_int_x, qmv_int_y) for phase 1
/// (half-pel) and phase 2 (quarter-pel) of the diamond search.
const HALFPEL_OFFSETS: [(i32, i32); 8] = [
    (-2, -2),
    (-2, 0),
    (-2, 2),
    (0, -2),
    (0, 2),
    (2, -2),
    (2, 0),
    (2, 2),
];
const QUARTERPEL_OFFSETS: [(i32, i32); 8] = [
    (-1, -1),
    (-1, 0),
    (-1, 1),
    (0, -1),
    (0, 1),
    (1, -1),
    (1, 0),
    (1, 1),
];

/// All 24 non-zero QMV offsets in the 5×5 grid {-2..=2}² around the
/// integer baseline. The integer-pel baseline (0, 0) is evaluated
/// separately (no FIR needed), so this array has 24 entries.
const FULL_5X5_OFFSETS: [(i32, i32); 24] = [
    (-2, -2),
    (-1, -2),
    (0, -2),
    (1, -2),
    (2, -2),
    (-2, -1),
    (-1, -1),
    (0, -1),
    (1, -1),
    (2, -1),
    (-2, 0),
    (-1, 0),
    (1, 0),
    (2, 0),
    (-2, 1),
    (-1, 1),
    (0, 1),
    (1, 1),
    (2, 1),
    (-2, 2),
    (-1, 2),
    (0, 2),
    (1, 2),
    (2, 2),
];

fn refine_subpel_rows(
    target: &[u8],
    reference: &[u8],
    reference_i32: &[i32],
    mvs_int: &[(i32, i32)],
    plane_w: usize,
    plane_h: usize,
    mb_w: usize,
    start_row: usize,
    end_row: usize,
    mode: SubpelMode,
    out_chunk: &mut [(i32, i32, i32)],
) {
    let w = plane_w as i32;
    let h = plane_h as i32;
    let mut target_block = [0u8; 256];
    let mut pred = [0i32; 256];

    for mb_y in start_row..end_row {
        let local_row = mb_y - start_row;
        for mb_x in 0..mb_w {
            let mb_idx = mb_y * mb_w + mb_x;
            let (int_dx, int_dy) = mvs_int[mb_idx];
            let mb_px = (mb_x * 16) as i32;
            let mb_py = (mb_y * 16) as i32;

            // Extract target block once with the same clamp-to-border
            // semantics the SAD path uses for the reference.
            for yy in 0..16 {
                let ty = (mb_py + yy as i32).clamp(0, h - 1);
                for xx in 0..16 {
                    let tx = (mb_px + xx as i32).clamp(0, w - 1);
                    target_block[yy * 16 + xx] = target[(ty * w + tx) as usize];
                }
            }

            // Phase 0: integer baseline. Directly read u8 reference,
            // skipping the FIR entirely so the seed cost matches the
            // upstream ME's SAD count for parity-checking.
            let int_x0 = mb_px + int_dx;
            let int_y0 = mb_py + int_dy;
            let mut best_qmv_x = int_dx * 4;
            let mut best_qmv_y = int_dy * 4;
            let mut best_sad =
                sad_integer(&target_block, reference, plane_w, plane_h, int_x0, int_y0);

            match mode {
                SubpelMode::Diamond => {
                    // Phase 1: half-pel diamond around integer baseline.
                    for (ox, oy) in HALFPEL_OFFSETS.iter().copied() {
                        let qx = int_dx * 4 + ox;
                        let qy = int_dy * 4 + oy;
                        let sad = sad_at_qmv(
                            &target_block,
                            reference,
                            reference_i32,
                            plane_w,
                            plane_h,
                            mb_px,
                            mb_py,
                            qx,
                            qy,
                            &mut pred,
                        );
                        if sad < best_sad {
                            best_sad = sad;
                            best_qmv_x = qx;
                            best_qmv_y = qy;
                        }
                    }
                    // Phase 2: quarter-pel diamond around phase-1 winner.
                    let p1_x = best_qmv_x;
                    let p1_y = best_qmv_y;
                    for (ox, oy) in QUARTERPEL_OFFSETS.iter().copied() {
                        let qx = p1_x + ox;
                        let qy = p1_y + oy;
                        let sad = sad_at_qmv(
                            &target_block,
                            reference,
                            reference_i32,
                            plane_w,
                            plane_h,
                            mb_px,
                            mb_py,
                            qx,
                            qy,
                            &mut pred,
                        );
                        if sad < best_sad {
                            best_sad = sad;
                            best_qmv_x = qx;
                            best_qmv_y = qy;
                        }
                    }
                }
                SubpelMode::Full => {
                    // 5×5 exhaustive sweep around the integer baseline.
                    // 24 sub-pel evaluations (the integer baseline is
                    // already in `best_sad`). Guaranteed to find the
                    // minimum within ±half-pel.
                    for (ox, oy) in FULL_5X5_OFFSETS.iter().copied() {
                        let qx = int_dx * 4 + ox;
                        let qy = int_dy * 4 + oy;
                        let sad = sad_at_qmv(
                            &target_block,
                            reference,
                            reference_i32,
                            plane_w,
                            plane_h,
                            mb_px,
                            mb_py,
                            qx,
                            qy,
                            &mut pred,
                        );
                        if sad < best_sad {
                            best_sad = sad;
                            best_qmv_x = qx;
                            best_qmv_y = qy;
                        }
                    }
                }
            }

            out_chunk[local_row * mb_w + mb_x] = (best_qmv_x, best_qmv_y, best_sad as i32);
        }
    }
}

#[inline]
fn sad_integer(
    target_block: &[u8; 256],
    reference: &[u8],
    plane_w: usize,
    plane_h: usize,
    int_x: i32,
    int_y: i32,
) -> u32 {
    let w = plane_w as i32;
    let h = plane_h as i32;
    let mut s: u32 = 0;
    for yy in 0..16 {
        let ry = (int_y + yy as i32).clamp(0, h - 1);
        for xx in 0..16 {
            let rx = (int_x + xx as i32).clamp(0, w - 1);
            let r = reference[(ry * w + rx) as usize] as i32;
            let t = target_block[yy * 16 + xx] as i32;
            s += (t - r).unsigned_abs();
        }
    }
    s
}

#[inline]
fn sad_at_qmv(
    target_block: &[u8; 256],
    reference: &[u8],
    reference_i32: &[i32],
    plane_w: usize,
    plane_h: usize,
    mb_px: i32,
    mb_py: i32,
    qmv_x: i32,
    qmv_y: i32,
    pred: &mut [i32; 256],
) -> u32 {
    let int_x = mb_px + qmv_x.div_euclid(4);
    let int_y = mb_py + qmv_y.div_euclid(4);
    let xf = qmv_x.rem_euclid(4) as u8;
    let yf = qmv_y.rem_euclid(4) as u8;
    if xf == 0 && yf == 0 {
        return sad_integer(target_block, reference, plane_w, plane_h, int_x, int_y);
    }
    if crate::h264_inter_pred::interpolate_luma(
        reference_i32,
        plane_w,
        plane_w,
        plane_h,
        int_x,
        int_y,
        xf,
        yf,
        16,
        16,
        /*bit_depth=*/ 8,
        pred,
        16,
    )
    .is_err()
    {
        return u32::MAX;
    }
    let mut s: u32 = 0;
    for k in 0..256 {
        let p = pred[k].clamp(0, 255);
        let t = target_block[k] as i32;
        s += (t - p).unsigned_abs();
    }
    s
}

// --- NodeID ---------------------------------------------------------------

/// Lightweight Python handle for a NodeID. Mirrors the Python
/// `substrate.graph.NodeID` dataclass shape: `.value` int, hashable,
/// equal by value, `repr(n) == '#<id>'`. Implements the Python-side
/// dataclass interface that existing tests use.
#[pyclass(name = "NodeID", module = "substrate_rs._native", frozen)]
#[derive(Copy, Clone, Debug, PartialEq, Eq, Hash)]
pub struct PyNodeID {
    #[pyo3(get)]
    pub value: u32,
}

#[pymethods]
impl PyNodeID {
    #[new]
    fn new(value: u32) -> Self {
        Self { value }
    }

    fn __repr__(&self) -> String {
        format!("#{}", self.value)
    }

    fn __eq__(&self, other: &Bound<'_, PyAny>) -> bool {
        if let Ok(o) = other.extract::<PyRef<'_, PyNodeID>>() {
            self.value == o.value
        } else if let Ok(v) = other.extract::<u32>() {
            self.value == v
        } else {
            false
        }
    }

    fn __hash__(&self) -> i64 {
        self.value as i64
    }
}

impl PyNodeID {
    fn from_node(nid: NodeID) -> Self {
        Self { value: nid.0 }
    }

    fn to_node(self) -> NodeID {
        NodeID(self.value)
    }
}

// --- Python ↔ Value bridge -----------------------------------------------

/// Convert a Python object to a substrate Value. Interns strings.
/// Recognises `NodeID` dataclass instances by attribute (so callers
/// can pass either the PyO3 `PyNodeID` or a plain Python class with a
/// `.value` int — keeps the bridge tolerant of either side).
/// Build the bundle of interned Sym keys can_ops needs.
///
/// All names are interned (created if absent) so subsequent reads via
/// can_ops resolve in O(1). Returns Some(keys) — None can't actually
/// happen since intern() always succeeds, but the call sites assume
/// Option for forward-compat.
fn build_can_keys(inner: &mut crate::substrate::Substrate) -> Option<crate::can_ops::CanKeys> {
    let state_attr = inner.interner.intern("state");
    let external_field_attr = inner.interner.intern("external_field");
    let identity_field_attr = inner.interner.intern("identity_field");
    let target_state_attr = inner.interner.intern("target_state");
    let temperature_attr = inner.interner.intern("temperature");
    let weight_attr = inner.interner.intern("weight");
    let has_concept_edge = inner.interner.intern("has_concept");
    let causal_influence_edge = inner.interner.intern("causal_influence");
    Some(crate::can_ops::CanKeys {
        state_attr,
        external_field_attr,
        identity_field_attr,
        target_state_attr,
        temperature_attr,
        weight_attr,
        has_concept_edge,
        causal_influence_edge,
    })
}

fn py_to_value(
    py: Python<'_>,
    obj: &Bound<'_, PyAny>,
    interner: &mut crate::sym::Interner,
) -> PyResult<Value> {
    if obj.is_none() {
        return Ok(Value::None);
    }
    if let Ok(b) = obj.extract::<bool>() {
        // bool BEFORE int since Python bools are ints subclasses.
        return Ok(Value::Bool(b));
    }
    if let Ok(n) = obj.extract::<i64>() {
        return Ok(Value::Int(n));
    }
    // `fractions.Fraction` BEFORE the f64 extraction below — PyO3's f64
    // FromPyObject falls back to `__float__` for arbitrary objects, and
    // Fraction implements it, so checking class name first is required
    // or every Fraction would silently lose its exactness right here.
    if let Ok(cls_name) = obj.get_type().name().map(|s| s.to_string()) {
        if cls_name == "Fraction" {
            if let (Ok(n), Ok(d)) = (
                obj.getattr("numerator").and_then(|v| v.extract::<i64>()),
                obj.getattr("denominator").and_then(|v| v.extract::<i64>()),
            ) {
                return Ok(crate::value::make_rational(n, d).unwrap_or(Value::Int(0)));
            }
        }
    }
    if let Ok(f) = obj.extract::<f64>() {
        return Ok(Value::Float(f));
    }
    if let Ok(s) = obj.extract::<String>() {
        return Ok(Value::Str(interner.intern(&s)));
    }
    // Python `bytes` → Surface(Bytes, …). The Surface variant is the
    // engine's canonical byte payload (used by render Terms) so
    // routing arbitrary blobs through it keeps the type set small.
    if let Ok(b) = obj.extract::<&[u8]>() {
        return Ok(Value::Surface(SurfaceKind::Bytes, Arc::from(b)));
    }
    if let Ok(n) = obj.extract::<PyRef<'_, PyNodeID>>() {
        return Ok(Value::Node(n.to_node()));
    }
    // Tolerate any object with a `.value` int attr labelled as NodeID
    // (matches the Python `substrate.graph.NodeID` dataclass) so users
    // mixing Python and Rust NodeIDs don't trip.
    if let Ok(cls_name) = obj.get_type().name().map(|s| s.to_string()) {
        if cls_name == "NodeID" {
            if let Ok(v) = obj.getattr("value").and_then(|v| v.extract::<u32>()) {
                return Ok(Value::Node(NodeID(v)));
            }
        }
    }
    if let Ok(t) = obj.downcast::<PyTuple>() {
        let mut items: SmallVec<[Value; 4]> = SmallVec::new();
        for x in t.iter() {
            items.push(py_to_value(py, &x, interner)?);
        }
        return Ok(Value::Tuple(Arc::new(items)));
    }
    if let Ok(fs) = obj.downcast::<PyFrozenSet>() {
        let mut items = Vec::new();
        for x in fs.iter() {
            items.push(py_to_value(py, &x, interner)?);
        }
        return Ok(Value::make_frozenset(items));
    }
    if let Ok(s) = obj.downcast::<PySet>() {
        let mut items = Vec::new();
        for x in s.iter() {
            items.push(py_to_value(py, &x, interner)?);
        }
        return Ok(Value::make_set(items));
    }
    if let Ok(l) = obj.downcast::<PyList>() {
        // Python list → `Value::List` (ARC6 value layer). This used to
        // collapse to `Value::Tuple`, which is why a row's `expected`
        // was already a tuple before any comparator saw it.
        let mut items: SmallVec<[Value; 4]> = SmallVec::new();
        for x in l.iter() {
            items.push(py_to_value(py, &x, interner)?);
        }
        return Ok(Value::List(Arc::new(items)));
    }
    if let Ok(d) = obj.downcast::<PyDict>() {
        let mut pairs: Vec<(Value, Value)> = Vec::new();
        for (k, v) in d.iter() {
            pairs.push((
                py_to_value(py, &k, interner)?,
                py_to_value(py, &v, interner)?,
            ));
        }
        pairs.sort_by(|a, b| cmp_value(&a.0, &b.0));
        return Ok(Value::Dict(pairs.into()));
    }
    Err(PyValueError::new_err(format!(
        "cannot convert Python {} to substrate Value",
        obj.get_type().name()?
    )))
}

/// Convert a substrate Value back to a Python object.
fn value_to_py<'py>(
    py: Python<'py>,
    v: &Value,
    interner: &crate::sym::Interner,
) -> PyResult<Bound<'py, PyAny>> {
    match v {
        Value::None => Ok(py.None().into_bound(py)),
        Value::Bool(b) => Ok(b.into_py(py).into_bound(py)),
        Value::Int(n) => Ok(n.into_py(py).into_bound(py)),
        Value::Float(f) => Ok(f.into_py(py).into_bound(py)),
        // The PROGRAM value domain's exact rational surfaces to Python
        // as a `fractions.Fraction` — the natural, exact Python-side
        // numeric type (arithmetic + comparisons against int/float both
        // work correctly out of the box), not a lossy float. Callers at
        // a genuine cross-frame boundary (comparing against a float
        // spec row) call `float(...)` themselves, exactly the
        // "render at the comparison boundary" discipline.
        Value::Rational(n, d) => {
            let fractions = py.import_bound("fractions")?;
            let frac_cls = fractions.getattr("Fraction")?;
            Ok(frac_cls.call1((*n, *d))?)
        }
        Value::Str(s) => {
            let s_str = interner.resolve(*s).to_string();
            Ok(s_str.into_py(py).into_bound(py))
        }
        Value::Node(nid) => {
            let n = PyNodeID::from_node(*nid);
            Ok(Py::new(py, n)?.into_bound(py).into_any())
        }
        Value::Tuple(items) => {
            let mut elems: Vec<PyObject> = Vec::with_capacity(items.len());
            for x in items.iter() {
                elems.push(value_to_py(py, x, interner)?.unbind());
            }
            Ok(PyTuple::new_bound(py, &elems).into_any())
        }
        // The other half of the ARC6 fix: a `List` surfaces to Python as
        // a genuine `list`, so `type(got) == type(expected)` is a real
        // test on the Python side too.
        Value::List(items) => {
            let mut elems: Vec<PyObject> = Vec::with_capacity(items.len());
            for x in items.iter() {
                elems.push(value_to_py(py, x, interner)?.unbind());
            }
            Ok(PyList::new_bound(py, &elems).into_any())
        }
        Value::Set(items) => {
            let s = PySet::empty_bound(py)?;
            for x in items.iter() {
                s.add(value_to_py(py, x, interner)?)?;
            }
            Ok(s.into_any())
        }
        Value::FrozenSet(items) => {
            let mut elems: Vec<PyObject> = Vec::with_capacity(items.len());
            for x in items.iter() {
                elems.push(value_to_py(py, x, interner)?.unbind());
            }
            Ok(PyFrozenSet::new_bound(py, &elems)?.into_any())
        }
        Value::Dict(pairs) => {
            let d = PyDict::new_bound(py);
            for (k, v) in pairs.iter() {
                d.set_item(value_to_py(py, k, interner)?, value_to_py(py, v, interner)?)?;
            }
            Ok(d.into_any())
        }
        Value::Surface(kind, bytes) => {
            // Unwrap to plain Python types: bytes → bytes, text → str.
            // Callers who explicitly want the (kind, payload) split
            // can route through the persistence codec which preserves
            // the tag. Round-trip for `bytes` is the load-bearing
            // case (used by Image.pixels / Kernel.weights in the
            // vision module).
            match kind {
                SurfaceKind::Bytes => Ok(pyo3::types::PyBytes::new_bound(py, bytes).into_any()),
                SurfaceKind::Text => {
                    let s = std::str::from_utf8(bytes).unwrap_or("");
                    Ok(s.to_string().into_py(py).into_bound(py))
                }
            }
        }
    }
}

// --- attr/env dict <-> FxHashMap helpers ----------------------------------

/// Decode a seed manifest's attrs object (JSON shape) into a typed
/// attrs map. Re-uses `decode_value` so dunder-tagged forms
/// (`__nid__`, `__tuple__`, `__set__`, `__dict__`, ...) round-trip
/// the same as `graph_from_value` handles them.
fn decode_attrs_object(
    attrs: Option<&J>,
    interner: &mut crate::sym::Interner,
) -> FxHashMap<Sym, Value> {
    let mut out = FxHashMap::default();
    if let Some(J::Object(m)) = attrs {
        for (k, v) in m {
            let k_sym = interner.intern(k);
            out.insert(k_sym, decode_value(v, interner));
        }
    }
    out
}

/// Resolve a node reference inside a seed manifest. Three shapes:
///
///   `{"local": <int>}`        — a node added by this seed; look up
///                                in the local→global allocation map.
///   `{"role": "agent_root"}`  — the well-known agent self-node,
///                                passed in by the world adapter.
///   `{"type": "Concept", "name": "X"}` and similar
///                              — find a pre-existing node of the
///                                given type whose attrs include
///                                every other field of the ref.
///
/// Errors if the reference can't be resolved against the current
/// graph (the typical cause is a missing dependency seed).
fn resolve_seed_ref(
    raw: Option<&J>,
    local_to_global: &FxHashMap<u64, NodeID>,
    root_node: Option<NodeID>,
    inner: &crate::substrate::Substrate,
) -> PyResult<NodeID> {
    let obj = raw
        .and_then(|v| v.as_object())
        .ok_or_else(|| PyValueError::new_err("seed ref must be an object"))?;
    if let Some(J::Number(n)) = obj.get("local") {
        if let Some(u) = n.as_u64() {
            return local_to_global.get(&u).copied().ok_or_else(|| {
                PyValueError::new_err(format!(
                    "seed ref local={} unresolved (out-of-order edge)",
                    u
                ))
            });
        }
    }
    if let Some(J::String(role)) = obj.get("role") {
        if role == "agent_root" {
            return root_node.ok_or_else(|| {
                PyValueError::new_err(
                    "seed ref names role=agent_root but loader was \
                     invoked without a root_node — pass agent.agent_root \
                     for agent seeds, or use a manifest without \
                     agent-role refs for non-agent compositions",
                )
            });
        }
        return Err(PyValueError::new_err(format!(
            "seed ref: unknown role {:?}",
            role
        )));
    }
    if let Some(J::String(kind)) = obj.get("type") {
        let Some(type_sym) = inner.interner.lookup(kind) else {
            return Err(PyValueError::new_err(format!(
                "seed cross-ref to absent type {:?}",
                kind
            )));
        };
        // Walk every node of that type, return the first whose attrs
        // match all the non-`type` fields of the ref.
        for nid in inner.graph.nodes_of_type(type_sym) {
            let n = inner.graph.node(nid);
            if seed_ref_attrs_match(obj, n, &inner.interner) {
                return Ok(nid);
            }
        }
        return Err(PyValueError::new_err(format!(
            "seed cross-ref {:?} unresolved (missing dep seed?)",
            obj
        )));
    }
    Err(PyValueError::new_err(format!(
        "seed ref: unrecognised shape {:?}",
        obj
    )))
}

/// True iff every key in `ref_obj` other than `type` matches the
/// node's attrs (string-valued, comparison via interner).
fn seed_ref_attrs_match(
    ref_obj: &serde_json::Map<String, J>,
    node: &crate::graph::NodeData,
    interner: &crate::sym::Interner,
) -> bool {
    for (k, v) in ref_obj {
        if k == "type" {
            continue;
        }
        let Some(want_str) = v.as_str() else {
            return false;
        };
        let Some(attr_sym) = interner.lookup(k) else {
            return false;
        };
        let Some(attr_val) = node.attrs.get(&attr_sym) else {
            return false;
        };
        match attr_val {
            Value::Str(s) => {
                if interner.resolve(s.clone()) != want_str {
                    return false;
                }
            }
            _ => return false,
        }
    }
    true
}

fn pydict_to_attrs(
    py: Python<'_>,
    d: Option<&Bound<'_, PyDict>>,
    interner: &mut crate::sym::Interner,
) -> PyResult<FxHashMap<Sym, Value>> {
    let mut out = FxHashMap::default();
    if let Some(d) = d {
        for (k, v) in d.iter() {
            let key = k.extract::<String>().map_err(|_| {
                PyValueError::new_err("attr keys must be strings (intern fast-path)")
            })?;
            let sym = interner.intern(&key);
            out.insert(sym, py_to_value(py, &v, interner)?);
        }
    }
    Ok(out)
}

fn pydict_to_env(
    py: Python<'_>,
    d: Option<&Bound<'_, PyDict>>,
    interner: &mut crate::sym::Interner,
) -> PyResult<Env> {
    let mut env: Env = SmallVec::new();
    if let Some(d) = d {
        for (k, v) in d.iter() {
            let key = k
                .extract::<String>()
                .map_err(|_| PyValueError::new_err("env keys must be strings (Var names)"))?;
            // Skip private keys used by the Python evaluator (_resolve_concept,
            // _holds_depth) — concept resolution goes through `define_concept`.
            if key.starts_with('_') {
                continue;
            }
            let sym = interner.intern(&key);
            env.push((sym, py_to_value(py, &v, interner)?));
        }
    }
    Ok(env)
}

fn attrs_to_pydict<'py>(
    py: Python<'py>,
    attrs: &crate::graph::Attrs,
    interner: &crate::sym::Interner,
) -> PyResult<Bound<'py, PyDict>> {
    let d = PyDict::new_bound(py);
    for (k, v) in attrs {
        d.set_item(
            interner.resolve(*k).to_string(),
            value_to_py(py, v, interner)?,
        )?;
    }
    Ok(d)
}

fn pyobj_to_json(py: Python<'_>, obj: &Bound<'_, PyAny>) -> PyResult<J> {
    // Round-trip through Python's `json.dumps` — handles None/bool/int/
    // float/str/list/dict uniformly without us reimplementing the JSON
    // serialiser. The wire form is JSON anyway, so the Python caller
    // already constructs JSON-shaped dicts.
    let json_mod = py.import_bound("json")?;
    let s: String = json_mod.call_method1("dumps", (obj,))?.extract()?;
    // serde_json's default recursion limit (128) would reject deeply-nested
    // composed Term-trees; disable it so large single-Term compositions parse.
    // Disabling the limit risks a hard stack overflow on pathological depth, so
    // parse on a dedicated 256 MiB-stack thread (the standard stack-safety guard).
    let parsed: Result<J, String> = std::thread::Builder::new()
        .stack_size(256 * 1024 * 1024)
        .spawn(move || {
            let mut de = serde_json::Deserializer::from_str(&s);
            de.disable_recursion_limit();
            let v = <J as serde::Deserialize>::deserialize(&mut de)
                .map_err(|e| format!("json parse: {}", e))?;
            de.end().map_err(|e| format!("json parse: {}", e))?;
            Ok(v)
        })
        .map_err(|e| PyValueError::new_err(format!("json parse thread: {}", e)))?
        .join()
        .map_err(|_| PyValueError::new_err("json parse thread panicked"))?;
    parsed.map_err(PyValueError::new_err)
}

// --- THE `Lit` WIRE (prereg A8) -----------------------------------------
//
// `pyobj_to_json` above round-trips through `json.dumps`, and **JSON has
// exactly one array type**. So a Python `list` and a Python `tuple` inside
// a `Lit` both reach `persist::decode_value` as a bare array, which decodes
// as `Value::Tuple`. That was harmless while `List` and `Tuple` were one
// Value; under the ARC6 value layer it silently RETYPES every Python list
// that crosses the Term wire, and it is the root cause of the A6/A7
// episode (a control comparing a list-typed spec with a tuple-typed spec
// over a bare `Lit` was comparing a spec with itself).
//
// THE FIX, AND WHAT BOUNDS ITS BLAST RADIUS.
//
// The engine already ships an exact tagged form (`__tuple__` / `__list__` /
// `__set__` / `__fset__`, `persist.rs`). `pyobj_to_json_term` below writes
// it — but ONLY for the value of a `Lit`, and ONLY on the TERM-EVALUATION
// wire (`evaluate`, `relax_to_fixpoint`, `search`, `shape_of_term`,
// `add_shape_node_for_term`, `add_term_subgraph`). Everywhere else — and in
// particular `load_seed_manifest`, `add_rule`, `import_rules`,
// `add_production`, `define_concept`, `graph_from_dict`, the `decode`
// free function — keeps calling `pyobj_to_json` unchanged.
//
// That split is load-bearing and it is NOT the split A8's prose assumed.
// A8 states "seed files never pass through `pyobj_to_json`". **They do**:
// `load_seed_manifest(json.load(open(seed)))` is exactly that path, and
// there are 68 array-valued `Lit`s in `seeds/*.json`. A blanket
// type-faithful encoder would therefore retype every one of them from
// `Tuple` to `List`, which is the thing A8's LW2 forbids. The honest
// formulation of the same constraint is by CHANNEL, not by file:
//
//   * a Term handed over for EVALUATION is Python-originated  -> faithful;
//   * a Term installed as GRAPH DATA (seed manifest, rule, production,
//     concept definition, checkpoint) is the persisted wire form, where a
//     bare array means `Tuple` -> unchanged, byte for byte.
//
// A bare JSON array therefore still decodes as `Value::Tuple` everywhere;
// what changes is that a Python `list` on the evaluation wire is no longer
// WRITTEN as a bare array.
#[derive(Clone, Copy, PartialEq)]
enum WireMode {
    /// Term structure: arrays stay arrays (they are children lists), and a
    /// `{"type": "Lit"}` dict's `value` field descends in `Value` mode.
    Structural,
    /// A `Lit`'s value: the Python container type is preserved with the
    /// shipped tag.
    Value,
    /// Already-tagged wire form: emit verbatim, tag nothing, and do not
    /// look for `Lit`s inside it.
    Verbatim,
}

/// The tags `persist::decode_value` recognises. A dict carrying any of
/// them is ALREADY in wire form (this is what `prog_synthesis._wire`
/// writes), so it is emitted verbatim rather than re-tagged.
fn is_wire_tag(k: &str) -> bool {
    matches!(
        k,
        "__tuple__"
            | "__list__"
            | "__set__"
            | "__fset__"
            | "__dict__"
            | "__nid__"
            | "__rational__"
            | "__surface__"
            | "__term__"
    )
}

/// Type-faithful Term encoder. See the block comment above.
///
/// Every leaf this walker does not handle natively is delegated to
/// `pyobj_to_json`, so the exact pre-existing behaviour (including the
/// `TypeError` on `bytes`, the `ValueError` on `NaN`/`Infinity`, and the
/// int-key stringification) is preserved verbatim for those cases.
fn pyobj_to_json_term(py: Python<'_>, obj: &Bound<'_, PyAny>, mode: WireMode) -> PyResult<J> {
    use pyo3::types::{PyBool, PyFloat, PyInt, PyString};

    // Scalars first, and `bool` BEFORE `int` (Python's bool is an int).
    if obj.is_none() {
        return Ok(J::Null);
    }
    if let Ok(b) = obj.downcast::<PyBool>() {
        return Ok(J::Bool(b.is_true()));
    }
    if obj.is_instance_of::<PyString>() {
        let s: String = obj.extract()?;
        return Ok(J::String(s));
    }
    if obj.is_instance_of::<PyInt>() {
        // A Python int wider than i64 is NOT handled here — it falls
        // through to `pyobj_to_json`, which reproduces the existing
        // "huge int becomes a float" behaviour exactly.
        if let Ok(i) = obj.extract::<i64>() {
            return Ok(J::Number(i.into()));
        }
        return pyobj_to_json(py, obj);
    }
    if obj.is_instance_of::<PyFloat>() {
        let f: f64 = obj.extract()?;
        // Non-finite floats have no JSON form; delegate so the caller
        // gets the same `ValueError` it gets today.
        return match serde_json::Number::from_f64(f) {
            Some(n) => Ok(J::Number(n)),
            None => pyobj_to_json(py, obj),
        };
    }

    // Containers.
    if let Ok(d) = obj.downcast::<PyDict>() {
        let mut pairs: Vec<(String, Bound<'_, PyAny>)> = Vec::with_capacity(d.len());
        for (k, v) in d.iter() {
            match k.downcast::<PyString>() {
                Ok(s) => pairs.push((s.extract()?, v)),
                // Non-string keys: `json.dumps` stringifies them by its
                // own rules. Do not reimplement those rules — delegate
                // the whole dict, exactly as today. (Residual: a `Lit`
                // value that is a non-string-keyed dict stays lossy.)
                Err(_) => return pyobj_to_json(py, obj),
            }
        }
        // A dict already in wire form is emitted verbatim.
        if mode == WireMode::Value && pairs.iter().any(|(k, _)| is_wire_tag(k)) {
            return pyobj_to_json_term(py, obj, WireMode::Verbatim);
        }
        let is_lit = mode == WireMode::Structural
            && d.get_item("type")?
                .and_then(|t| t.extract::<String>().ok())
                .as_deref()
                == Some("Lit");
        let mut m = serde_json::Map::with_capacity(pairs.len());
        for (k, v) in pairs.iter() {
            let child_mode = if is_lit && k == "value" {
                WireMode::Value
            } else {
                mode
            };
            m.insert(k.clone(), pyobj_to_json_term(py, v, child_mode)?);
        }
        return Ok(J::Object(m));
    }

    let seq: Option<(&'static str, Vec<Bound<'_, PyAny>>)> = if let Ok(l) = obj.downcast::<PyList>()
    {
        Some(("__list__", l.iter().collect()))
    } else if let Ok(t) = obj.downcast::<PyTuple>() {
        Some(("__tuple__", t.iter().collect()))
    } else if let Ok(s) = obj.downcast::<PyFrozenSet>() {
        Some(("__fset__", s.iter().collect()))
    } else if let Ok(s) = obj.downcast::<PySet>() {
        Some(("__set__", s.iter().collect()))
    } else {
        None
    };
    if let Some((tag, items)) = seq {
        // In Structural / Verbatim mode a `set` has no JSON form at all;
        // delegate so the caller gets today's `TypeError`.
        if mode != WireMode::Value && (tag == "__set__" || tag == "__fset__") {
            return pyobj_to_json(py, obj);
        }
        let mut arr = Vec::with_capacity(items.len());
        for it in items.iter() {
            arr.push(pyobj_to_json_term(py, it, mode)?);
        }
        if mode == WireMode::Value {
            let mut m = serde_json::Map::with_capacity(1);
            m.insert(tag.to_string(), J::Array(arr));
            return Ok(J::Object(m));
        }
        return Ok(J::Array(arr));
    }

    // Anything else (bytes, numpy scalars, custom objects, ...) goes
    // through the untouched path, so its success or its exception is
    // exactly what it was before.
    pyobj_to_json(py, obj)
}

fn json_to_pyobj<'py>(py: Python<'py>, j: &J) -> PyResult<Bound<'py, PyAny>> {
    let json_mod = py.import_bound("json")?;
    let s =
        serde_json::to_string(j).map_err(|e| PyValueError::new_err(format!("json emit: {}", e)))?;
    Ok(json_mod.call_method1("loads", (s,))?)
}

// --- graph-resident backtracking search ----------------------------------
//
// The strategy is graph-resident Term-trees (open / options / fail / accept /
// value); the engine just explores DFS with undo. This is the native form of
// the old Python `graph_rewrite.search_count` / `search_sum` — the missing
// capability behind determinants (signed product summed over permutations) and
// constraint counts (proper colourings). `assign_edge` is the decision edge the
// search adds from the chosen open item to each candidate option (then undoes).

/// Evaluate one Term against the live graph + env, returning its Value. Borrows
/// `inner` only for the duration of the eval, so the caller is free to mutate
/// the graph between calls (the backtracking add/remove edge).
fn search_eval(inner: &mut SubstrateRs, idx: TermIdx, env: &Env) -> Value {
    // Clone the (small, constant) base env per eval: `evaluate` uses env as a
    // scratch stack (pushing Filter/Exists iteration vars), so sharing one &mut
    // env across the fail/open/options evals of a level would let one eval's
    // residue corrupt the next.
    let mut env_local = env.clone();
    let mut cache = EvalCache::default();
    let SubstrateRs {
        graph,
        interner,
        concepts,
        terms,
        counters,
        ..
    } = &mut *inner;
    let mut ctx = EvalCtx::new(graph, interner)
        .with_cache(&mut cache)
        .with_counters(counters);
    if !concepts.is_empty() {
        ctx = ctx.with_concepts(concepts);
    }
    evaluate(terms, idx, &mut env_local, &mut ctx)
}

/// Extract the NodeIDs a strategy Term evaluated to (Filter / Neighbours yield a
/// Set; a bare Node is a singleton).
fn search_nodes(v: &Value) -> Vec<NodeID> {
    match v {
        // Filter / Neighbours / SetT yield a Set or FrozenSet of Nodes.
        Value::Set(items) | Value::FrozenSet(items) => items
            .iter()
            .filter_map(|x| {
                if let Value::Node(n) = x {
                    Some(*n)
                } else {
                    None
                }
            })
            .collect(),
        Value::Node(n) => vec![*n],
        _ => Vec::new(),
    }
}

/// DFS with undo. Returns the count of solutions (when `value` is None) or the
/// sum of `value` over solution leaves. `fail` prunes; `accept` gates a leaf.
#[allow(clippy::too_many_arguments)]
fn search_recurse(
    inner: &mut SubstrateRs,
    open: TermIdx,
    options: TermIdx,
    assign: Sym,
    fail: Option<TermIdx>,
    value: Option<TermIdx>,
    accept: Option<TermIdx>,
    env: &Env,
) -> f64 {
    if let Some(f) = fail {
        if search_eval(inner, f, env).truthy() {
            return 0.0; // constraint violated → prune
        }
    }
    let opens = search_nodes(&search_eval(inner, open, env));
    if opens.is_empty() {
        if let Some(a) = accept {
            if !search_eval(inner, a, env).truthy() {
                return 0.0;
            }
        }
        return match value {
            Some(v) => search_eval(inner, v, env).as_f64(),
            None => 1.0, // complete + consistent → one solution
        };
    }
    let item = *opens.iter().min().unwrap(); // deterministic choice
    let opts = search_nodes(&search_eval(inner, options, env));
    let mut total = 0.0;
    for opt in opts {
        let _ = inner
            .graph
            .insert_edge(item, assign, opt, FxHashMap::<Sym, Value>::default());
        total += search_recurse(inner, open, options, assign, fail, value, accept, env);
        if let Some(idx) = inner.graph.edge_idx(item, assign, opt) {
            inner.graph.delete_edge(idx); // backtrack
        }
    }
    total
}

// --- Substrate -----------------------------------------------------------

/// One big PyClass that owns the whole (G, Γ, C) bundle. Methods
/// mirror Python's `Substrate` (`primitives.py`) + the rest of the
/// substrate package, so the Python wrapper module can re-export them
/// directly.
///
/// Phase 7b adds:
/// - `declare_attr_index` / `nodes_where` — indexed attr lookup
/// - `register_hook` / `clear_hooks` — Python lifecycle callbacks fired
///   from the PyO3 layer (the Rust engine itself stays callback-free)
#[pyclass(name = "Substrate", module = "substrate_rs._native")]
pub struct PySubstrate {
    inner: Arc<Mutex<SubstrateRs>>,
    /// Per-event Python callback lists. Stored here (not in the Rust
    /// engine) because they're a Python-FFI concern; the engine
    /// produces hook-relevant events through its return values, the
    /// PyO3 layer fires the Python callbacks. Keys: "node_inserted",
    /// "node_deleted", "edge_inserted", "edge_deleted", "attr_set".
    hooks: FxHashMap<String, Vec<Py<PyAny>>>,
    /// Background tick thread — when Some, the agent is running.
    /// Cleared by `stop_agent`. The thread's stop signal is the
    /// `agent_stop` flag; `agent_thread` is just the join handle.
    agent_thread: Option<std::thread::JoinHandle<()>>,
    /// Stop signal for the background tick thread. Set true to ask
    /// the thread to exit at its next loop iteration.
    agent_stop: Arc<std::sync::atomic::AtomicBool>,
    /// The agent's MEMORY faculty (keep/forget/index decision in Rust,
    /// composing code_cache/HotCounter/persist tiers). Lazily created by
    /// `memory_bound`; persists across calls so the growth history + the
    /// order-N shape index accumulate.
    memory: Option<crate::memory::MemoryFaculty>,
}

#[pymethods]
impl PySubstrate {
    #[new]
    fn new() -> Self {
        Self {
            inner: Arc::new(Mutex::new(SubstrateRs::new(ConsistencyChecker::new(
                Grammar::new(),
            )))),
            hooks: FxHashMap::default(),
            agent_thread: None,
            agent_stop: Arc::new(std::sync::atomic::AtomicBool::new(false)),
            memory: None,
        }
    }

    // --- autonomous agent loop -----------------------------------------
    //
    // `start_agent` spawns a Rust thread that ticks the substrate at the
    // requested rate. The thread holds an Arc clone of `inner`; world
    // adapters keep writing to the same Arc through PySubstrate methods.
    // Lock contention is microseconds for both sides — worlds + agent
    // run asynchronously, hot-pluggable.
    //
    // PyO3 releases the GIL while the Rust thread holds the lock, so
    // Python world-adapter threads waiting for the lock don't block
    // each other on the GIL.

    #[pyo3(signature = (tick_rate_hz=10.0, n_runners=1, n_threads_per_runner=1, max_steps_per_tick=100_000))]
    fn start_agent(
        &mut self,
        tick_rate_hz: f64,
        n_runners: usize,
        n_threads_per_runner: usize,
        max_steps_per_tick: usize,
    ) -> PyResult<()> {
        if self.agent_thread.is_some() {
            return Err(PyValueError::new_err("agent already running"));
        }
        if n_runners != 1 {
            return Err(PyValueError::new_err(
                "multiple live graph writers are forbidden; use one runner \
                 with multiple pure cognitive-task workers",
            ));
        }
        let inner = Arc::clone(&self.inner);
        let stop = Arc::clone(&self.agent_stop);
        stop.store(false, std::sync::atomic::Ordering::SeqCst);
        let period_ns = (1e9 / tick_rate_hz.max(1e-9)) as u64;
        let period = std::time::Duration::from_nanos(period_ns);
        let handle = std::thread::Builder::new()
            .name("substrate-agent-tick".into())
            .spawn(move || {
                while !stop.load(std::sync::atomic::Ordering::Relaxed) {
                    let tick_start = std::time::Instant::now();
                    let (prepared, pre_steps) = {
                        let mut guard = match inner.lock() {
                            Ok(g) => g,
                            Err(p) => p.into_inner(),
                        };
                        crate::cognitive_cycle::advance_cognitive_epoch(&mut guard);
                        let steps = crate::cognitive_cycle::execute(
                            &mut guard,
                            crate::cognitive_cycle::CyclePlan::Default,
                            max_steps_per_tick,
                            false,
                            false,
                            n_threads_per_runner.max(1),
                        )
                        .steps;
                        let prepared = crate::cognitive_tasks::prepare_requested(
                            &mut guard,
                            n_threads_per_runner.max(1),
                        );
                        (prepared, steps)
                    };
                    // Pure task kernels run without the live-graph mutex.
                    let completed = crate::cognitive_tasks::execute_prepared(prepared);
                    {
                        let mut guard = match inner.lock() {
                            Ok(g) => g,
                            Err(p) => p.into_inner(),
                        };
                        let _ = crate::cognitive_tasks::fold_completed(&mut guard, completed);
                        let remaining = max_steps_per_tick.saturating_sub(pre_steps);
                        if remaining > 0 {
                            let _ = crate::cognitive_cycle::execute(
                                &mut guard,
                                crate::cognitive_cycle::CyclePlan::Default,
                                remaining,
                                false,
                                false,
                                n_threads_per_runner.max(1),
                            );
                        }
                    }
                    // Sleep until the next tick boundary; if the tick
                    // took longer than the period, fire the next one
                    // immediately.
                    let elapsed = tick_start.elapsed();
                    if let Some(remaining) = period.checked_sub(elapsed) {
                        std::thread::sleep(remaining);
                    }
                }
            })
            .map_err(|e| PyValueError::new_err(format!("spawn failed: {}", e)))?;
        self.agent_thread = Some(handle);
        Ok(())
    }

    fn stop_agent(&mut self, py: Python<'_>) -> PyResult<()> {
        let Some(handle) = self.agent_thread.take() else {
            return Ok(());
        };
        self.agent_stop
            .store(true, std::sync::atomic::Ordering::SeqCst);
        // Release the GIL while joining so the thread can finish its
        // current tick (which may want to acquire the inner mutex,
        // which doesn't need the GIL, but symmetry helps if hooks
        // ever fire from the agent thread).
        py.allow_threads(|| {
            let _ = handle.join();
        });
        Ok(())
    }

    fn agent_running(&self) -> bool {
        self.agent_thread
            .as_ref()
            .map(|h| !h.is_finished())
            .unwrap_or(false)
    }

    // --- seed loading: apply a captured manifest -----------------------
    //
    // A seed manifest is JSON: `{id, version, depends_on, nodes, edges,
    // productions}`. The agent boots by loading seed manifests for the
    // knowledge bundle the world adapter requests (chat / voice / ...).
    // CLAUDE.md "the agent is in Rust" — the loader lives here, not in
    // the Python adapter.
    //
    // Node IDs in the manifest are seed-local; the loader allocates
    // fresh global IDs and remaps. Cross-references to nodes installed
    // by dependency seeds are resolved structurally —
    // `{"role": "agent_root"}` or `{"type": "Concept", "name": "X"}`.
    // Seed edges go through `insert_edge` directly (skip the dynamic
    // admissibility check — the seed's own productions authorise the
    // edges it ships).

    #[pyo3(signature = (manifest, root_node=None))]
    fn load_seed_manifest(
        &mut self,
        py: Python<'_>,
        manifest: &Bound<'_, PyAny>,
        root_node: Option<PyRef<'_, PyNodeID>>,
    ) -> PyResult<PyObject> {
        let manifest_json = pyobj_to_json(py, manifest)?;
        let m = manifest_json
            .as_object()
            .ok_or_else(|| PyValueError::new_err("seed manifest must be a JSON object"))?;
        // `root_node` is the well-known node a manifest can name via
        // `{"role": "agent_root"}`. Agents pass `agent.agent_root`;
        // non-agent tasks (transcoding pipelines, subtitle generators
        // — any graph-resident composition that's not an agent)
        // leave it None. Resolution raises loudly if a manifest's
        // ref names a role we have no binding for.
        let root_nid = root_node.as_ref().map(|r| r.to_node());

        let mut nodes_added: usize = 0;
        let mut edges_added: usize = 0;
        let mut productions_added: usize = 0;

        // Process nodes + edges inside a single mutex hold so the local
        // → global map and the graph mutations stay consistent.
        {
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            let inner = &mut *guard;

            // 1) Nodes: allocate fresh global IDs.
            let mut local_to_global: FxHashMap<u64, NodeID> = FxHashMap::default();
            if let Some(J::Array(nodes)) = m.get("nodes") {
                for n in nodes {
                    let n_obj = n
                        .as_object()
                        .ok_or_else(|| PyValueError::new_err("seed node must be an object"))?;
                    let local_id = n_obj
                        .get("local_id")
                        .and_then(|v| v.as_u64())
                        .ok_or_else(|| PyValueError::new_err("seed node missing local_id"))?;
                    let type_str = n_obj
                        .get("type")
                        .and_then(|v| v.as_str())
                        .ok_or_else(|| PyValueError::new_err("seed node missing type"))?;
                    let type_sym = inner.interner.intern(type_str);
                    let attrs = decode_attrs_object(n_obj.get("attrs"), &mut inner.interner);
                    let new_nid = inner.add_node(type_sym, attrs);
                    local_to_global.insert(local_id, new_nid);
                    nodes_added += 1;
                }
            }

            // 2) Edges: resolve src/tgt refs, then insert unchecked.
            if let Some(J::Array(edges)) = m.get("edges") {
                for e in edges {
                    let e_obj = e
                        .as_object()
                        .ok_or_else(|| PyValueError::new_err("seed edge must be an object"))?;
                    let src =
                        resolve_seed_ref(e_obj.get("src"), &local_to_global, root_nid, inner)?;
                    let tgt =
                        resolve_seed_ref(e_obj.get("tgt"), &local_to_global, root_nid, inner)?;
                    let et_str = e_obj
                        .get("type")
                        .and_then(|v| v.as_str())
                        .ok_or_else(|| PyValueError::new_err("seed edge missing type"))?;
                    let et_sym = inner.interner.intern(et_str);
                    let attrs = decode_attrs_object(e_obj.get("attrs"), &mut inner.interner);
                    let _ = inner.graph.insert_edge(src, et_sym, tgt, attrs);
                    edges_added += 1;
                }
            }
        }

        // 3) Productions: re-use the existing add_production path. It
        // takes its own lock and handles where/weight Terms. The
        // capture tool refuses to persist non-trivial where/weight so
        // these are all simple (src_type, edge_type, tgt_type, prov).
        if let Some(J::Array(prods)) = m.get("productions") {
            for p in prods {
                let py_prod = json_to_pyobj(py, p)?;
                // Best-effort: a duplicate production is fine, swallow.
                let _ = self.add_production(py, &py_prod);
                productions_added += 1;
            }
        }

        // 4) Rules: register each RewriteRule the seed bundles (the
        // migrated agent decisions — decision→Term, construction→Rule).
        // Same parse path as `add_rule`. Rules match against the live
        // graph at tick time, so they need no local_id resolution.
        let mut rules_added: usize = 0;
        let mut rules_skipped: Vec<String> = Vec::new();
        if let Some(J::Array(rules)) = m.get("rules") {
            let patchable_rule_names: std::collections::HashSet<&str> = m
                .get("self_modification_patchable_rules")
                .and_then(|value| value.as_array())
                .into_iter()
                .flatten()
                .filter_map(|value| value.as_str())
                .collect();
            let manifest_area = m.get("area").and_then(|v| v.as_str());
            let manifest_order = m.get("order").and_then(|v| v.as_u64());
            let manifest_latency = m.get("latency_class").and_then(|v| v.as_str());
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            let inner = &mut *guard;
            for r in rules {
                // System-agnostic resilience: a single malformed rule must NOT take down the whole
                // seed's rule set. The old code `?`-propagated, and the Python boot loader then fell
                // back to loading the seed WITHOUT ANY rules — one typo (e.g. `remove_edge` for
                // `del_edge`) silently dropped all of a seed's rules and the failure was invisible.
                // Skip just the bad rule, LOUDLY, and keep every valid one.
                let mut scheduled = r.clone();
                if let Some(obj) = scheduled.as_object_mut() {
                    if !obj.contains_key("area") {
                        if let Some(area) = manifest_area {
                            obj.insert("area".into(), J::String(area.into()));
                        }
                    }
                    if !obj.contains_key("order") {
                        if let Some(order) = manifest_order {
                            obj.insert("order".into(), J::Number(order.into()));
                        }
                    }
                    if !obj.contains_key("latency_class") {
                        if let Some(latency) = manifest_latency {
                            obj.insert("latency_class".into(), J::String(latency.into()));
                        }
                    }
                }
                match parse_rule_json(&scheduled, &mut inner.terms, &mut inner.interner) {
                    Ok(mut rule) => {
                        // A loaded seed is a boot prior, not an ambient mutable
                        // target. Self-change remains additive: the agent may
                        // author a successor rule, while RulePatch is reserved
                        // for rules authored into the live substrate.
                        let rule_name = r
                            .get("name")
                            .and_then(|value| value.as_str())
                            .unwrap_or("anonymous_rule");
                        rule.mutation_protected = !patchable_rule_names.contains(rule_name);
                        inner.add_rule(rule);
                        rules_added += 1;
                    }
                    Err(e) => {
                        let nm = r
                            .get("name")
                            .and_then(|n| n.as_str())
                            .unwrap_or("<unnamed>");
                        eprintln!("[seed] WARNING: skipping malformed rule '{}': {}", nm, e);
                        rules_skipped.push(format!("{}: {}", nm, e));
                    }
                }
            }
        }

        // 5) Reflexes: the Reflex mechanism (Reflex node + stimulus_term
        // subgraph + refractory + named response), previously installed
        // only at runtime by `world_adapter.install_reflex`, now also
        // seed-loadable. Each entry's `stimulus` Term materialises as a
        // subgraph via the same path `add_term_subgraph` uses
        // (`reflect::term_to_subgraph`), then wires
        // `agent -has_reflex-> reflex -stimulus_term-> subgraph_root` —
        // mirroring `install_reflex`'s node/edge shape exactly (attrs
        // name/response/refractory_ticks/last_fired_tick/fire_count, the
        // latter two at `install_reflex`'s fresh-reflex defaults) so
        // `fire_reflexes` treats a seed-loaded reflex identically to one
        // installed at runtime. Same per-entry resilience as rules: a
        // malformed reflex is skipped, LOUDLY, never fatal to the whole
        // seed's remaining reflexes.
        let mut reflexes_added: usize = 0;
        let mut reflexes_skipped: Vec<String> = Vec::new();
        if let Some(J::Array(reflexes)) = m.get("reflexes") {
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            let inner = &mut *guard;
            for r in reflexes {
                match load_reflex_json(r, inner, root_nid) {
                    Ok(()) => reflexes_added += 1,
                    Err(e) => {
                        let nm = r
                            .get("name")
                            .and_then(|n| n.as_str())
                            .unwrap_or("<unnamed>");
                        eprintln!("[seed] WARNING: skipping malformed reflex '{}': {}", nm, e);
                        reflexes_skipped.push(format!("{}: {}", nm, e));
                    }
                }
            }
        }

        let summary = PyDict::new_bound(py);
        summary.set_item("nodes", nodes_added)?;
        summary.set_item("edges", edges_added)?;
        summary.set_item("productions", productions_added)?;
        summary.set_item("rules", rules_added)?;
        summary.set_item("rules_skipped", rules_skipped)?; // visible per-rule failures, not silent
        summary.set_item("reflexes", reflexes_added)?;
        summary.set_item("reflexes_skipped", reflexes_skipped)?;
        if let Some(J::String(seed_id)) = m.get("id") {
            summary.set_item("id", seed_id.clone())?;
        }
        Ok(summary.into())
    }

    // --- mutation surface (Π) ---

    #[pyo3(signature = (type_, attrs=None))]
    fn add_node(
        &mut self,
        py: Python<'_>,
        type_: &str,
        attrs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<PyNodeID> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let attrs_map = pydict_to_attrs(py, attrs, &mut inner.interner)?;
        let t = inner.interner.intern(type_);
        crate::scale_audit::ffi(1, 1);
        crate::scale_audit::graph_writes(1);
        let nid = inner.add_node(t, attrs_map);
        let py_nid = PyNodeID::from_node(nid);
        // Fire hooks AFTER the mutation lands so callbacks observe the
        // post-state. Snapshot the callback Py refs so we can release
        // the &mut self borrow before invoking Python.
        self.fire_hook(
            py,
            "node_inserted",
            &[
                Py::new(py, py_nid)?.into_any(),
                type_.to_string().into_py(py),
            ],
        )?;
        Ok(py_nid)
    }

    #[pyo3(signature = (src, edge_type, tgt, attrs=None))]
    fn add_edge(
        &mut self,
        py: Python<'_>,
        src: PyRef<'_, PyNodeID>,
        edge_type: &str,
        tgt: PyRef<'_, PyNodeID>,
        attrs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<()> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::graph_writes(1);
        let attrs_map = pydict_to_attrs(py, attrs, &mut inner.interner)?;
        let et = inner.interner.intern(edge_type);
        let src_node = src.to_node();
        let tgt_node = tgt.to_node();
        match inner.add_edge(src_node, et, tgt_node, attrs_map) {
            Ok(_) => {
                self.fire_hook(
                    py,
                    "edge_inserted",
                    &[
                        Py::new(py, PyNodeID::from_node(src_node))?.into_any(),
                        edge_type.to_string().into_py(py),
                        Py::new(py, PyNodeID::from_node(tgt_node))?.into_any(),
                    ],
                )?;
                Ok(())
            }
            Err(InadmissibleEdgeRs::Type1NoProduction {
                src_type,
                edge_type,
                tgt_type,
            }) => Err(InadmissibleEdge::new_err(format!(
                "Γ rejects ({}) -[{}]-> ({})",
                inner.interner.resolve(src_type),
                inner.interner.resolve(edge_type),
                inner.interner.resolve(tgt_type)
            ))),
            Err(InadmissibleEdgeRs::Type2VocabAbsent { missing }) => {
                Err(InadmissibleEdge::new_err(format!(
                    "Γ rejects: type '{}' not in vocabulary (Type-2)",
                    inner.interner.resolve(missing)
                )))
            }
        }
    }

    fn remove_edge(
        &mut self,
        py: Python<'_>,
        src: PyRef<'_, PyNodeID>,
        edge_type: &str,
        tgt: PyRef<'_, PyNodeID>,
    ) -> PyResult<bool> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let et = inner.interner.intern(edge_type);
        let src_node = src.to_node();
        let tgt_node = tgt.to_node();
        let removed = inner.remove_edge(EdgeKey {
            src: src_node,
            edge_type: et,
            tgt: tgt_node,
        });
        if removed {
            self.fire_hook(
                py,
                "edge_deleted",
                &[
                    Py::new(py, PyNodeID::from_node(src_node))?.into_any(),
                    edge_type.to_string().into_py(py),
                    Py::new(py, PyNodeID::from_node(tgt_node))?.into_any(),
                ],
            )?;
        }
        Ok(removed)
    }

    fn remove_node(&mut self, py: Python<'_>, nid: PyRef<'_, PyNodeID>) -> PyResult<bool> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let nid_node = nid.to_node();
        // Snapshot the node's type BEFORE delete so the hook can carry it.
        let type_str = if inner.graph.has_node(nid_node) {
            Some(
                inner
                    .interner
                    .resolve(inner.graph.node(nid_node).type_)
                    .to_string(),
            )
        } else {
            None
        };
        let removed = inner.remove_node(nid_node);
        if removed {
            if let Some(t) = type_str {
                self.fire_hook(
                    py,
                    "node_deleted",
                    &[
                        Py::new(py, PyNodeID::from_node(nid_node))?.into_any(),
                        t.into_py(py),
                    ],
                )?;
            }
        }
        Ok(removed)
    }

    fn set_attr(
        &mut self,
        py: Python<'_>,
        nid: PyRef<'_, PyNodeID>,
        key: &str,
        value: &Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let v = py_to_value(py, value, &mut inner.interner)?;
        let k = inner.interner.intern(key);
        let nid_node = nid.to_node();
        // Snapshot the previous attr value so the hook can show old →
        // new — handy for invariant-tracking callbacks.
        let old = if inner.graph.has_node(nid_node) {
            inner.graph.node(nid_node).attrs.get(&k).cloned()
        } else {
            None
        };
        // Two objects are built (old_py, new_py) even when no hook can observe
        // them — the cost the bulk path exists to avoid.
        crate::scale_audit::ffi(1, 2);
        crate::scale_audit::graph_writes(1);
        inner.set_attr(nid_node, k, v.clone());
        let old_py = match old {
            Some(ov) => value_to_py(py, &ov, &inner.interner)?.unbind(),
            None => py.None(),
        };
        let new_py = value_to_py(py, &v, &inner.interner)?.unbind();
        self.fire_hook(
            py,
            "attr_set",
            &[
                Py::new(py, PyNodeID::from_node(nid_node))?.into_any(),
                key.to_string().into_py(py),
                old_py,
                new_py,
            ],
        )?;
        Ok(())
    }

    fn set_type(&mut self, nid: PyRef<'_, PyNodeID>, new_type: &str) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let t = inner.interner.intern(new_type);
        inner.set_type(nid.to_node(), t);
    }

    // --- query ---

    fn node<'py>(&self, py: Python<'py>, nid: PyRef<'_, PyNodeID>) -> PyResult<Bound<'py, PyDict>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        if !inner.graph.has_node(nid.to_node()) {
            return Err(PyKeyError::new_err(format!("no node #{}", nid.value)));
        }
        let n = inner.graph.node(nid.to_node());
        // SCALE AUDIT: `node()` materialises the WHOLE attribute dict (id + type
        // + one object per attr) to satisfy a read of ONE field. That asymmetry
        // is the F bucket's whole point, so it is counted per CONSTRUCTED OBJECT,
        // not per call.
        crate::scale_audit::ffi(1, 2 + n.attrs.len() as u64);
        let d = PyDict::new_bound(py);
        let nid_obj = Py::new(py, PyNodeID::from_node(nid.to_node()))?;
        d.set_item("id", nid_obj)?;
        d.set_item("type", inner.interner.resolve(n.type_).to_string())?;
        d.set_item("attrs", attrs_to_pydict(py, &n.attrs, &inner.interner)?)?;
        Ok(d)
    }

    // --- BULK ATTRIBUTE ACCESS: ONE crossing instead of N --------------------
    //
    // *** PURE PERFORMANCE. NO NEW CAPABILITY, NO DECISION. ***
    //
    // These are exactly `[node(n)["attrs"].get(k) for n in nodes]` and
    // `[set_attr(n, k, v) for n in nodes]`, evaluated on the Rust side of the
    // boundary. A world adapter still chooses WHICH nodes and WHAT value — the
    // composition stays in Python; only the LOOP moves. Per-cell Python I/O was
    // never a decision (CLAUDE.md: "primitive in Rust, composition in graph").
    //
    // WHY (measured 2026-07-17, engine 366ce5f14eff, Ryzen 5 9600X, RELEASE):
    // the retina adapter crosses PyO3 ~4N times per tick, and `node()`
    // MATERIALISES A FULL ATTRIBUTE DICT (~10 Python objects) to read ONE
    // field. At 128^2 the Python side was 82% of the tick; the Rust rule engine
    // was 18%. A bare Python loop is 0.004us/cell, so the interpreter was never
    // the cost — THE BOUNDARY WAS.
    //
    // WHAT IS PRESERVED, EXACTLY (PROTOCOL §9 — byte-identity is absolute):
    //   * `get_attr_many` uses `lookup`, NEVER `intern`: a READ must not mint a
    //     symbol. An un-interned key can be on no node, so it yields all-None —
    //     which is precisely what `.get()` returns.
    //   * a missing node raises KeyError, matching `node()`.
    //   * `set_attr_many` interns the key ONCE and converts the value ONCE (it
    //     is uniform BY CONSTRUCTION), then does N native writes. It does NOT
    //     check node existence — because `set_attr` does not either, and the
    //     job here is to preserve behaviour, not improve it.
    //   * HOOKS: `set_attr` fires `attr_set` on every write. If ANY `attr_set`
    //     hook is registered this falls back to the per-node path, so hook
    //     semantics (and firing order) are identical. With no hook registered —
    //     every vision path — the old->new snapshot is skipped, which `set_attr`
    //     built unconditionally even when nothing could observe it.
    fn get_attr_many(
        &self,
        py: Python<'_>,
        nodes: Vec<PyRef<'_, PyNodeID>>,
        key: &str,
    ) -> PyResult<Vec<PyObject>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        // SCALE AUDIT: ONE crossing, N marshalled items, N constructed objects —
        // the bulk accessor's whole reason for existing, made countable.
        crate::scale_audit::ffi(nodes.len() as u64, nodes.len() as u64);
        let mut out: Vec<PyObject> = Vec::with_capacity(nodes.len());
        // `lookup` (not `intern`): reading must never mutate the interner.
        let Some(k) = inner.interner.lookup(key) else {
            // Never interned => carried by no node => None everywhere. Node
            // existence is still validated, so this cannot mask a bad id.
            for n in &nodes {
                if !inner.graph.has_node(NodeID(n.value)) {
                    return Err(PyKeyError::new_err(format!("no node #{}", n.value)));
                }
                out.push(py.None());
            }
            return Ok(out);
        };
        for n in &nodes {
            let nid = NodeID(n.value);
            if !inner.graph.has_node(nid) {
                return Err(PyKeyError::new_err(format!("no node #{}", n.value)));
            }
            match inner.graph.node(nid).attrs.get(&k) {
                Some(v) => out.push(value_to_py(py, v, &inner.interner)?.unbind()),
                None => out.push(py.None()),
            }
        }
        Ok(out)
    }

    fn set_attr_many(
        &mut self,
        py: Python<'_>,
        nodes: Vec<PyRef<'_, PyNodeID>>,
        key: &str,
        value: &Bound<'_, PyAny>,
    ) -> PyResult<()> {
        // Hook parity FIRST: if anything can observe these writes, take the
        // per-node path that fires them exactly as `set_attr` does.
        if self.hooks.contains_key("attr_set") {
            let ids: Vec<u32> = nodes.iter().map(|n| n.value).collect();
            drop(nodes);
            for v in ids {
                let one = Py::new(py, PyNodeID { value: v })?;
                self.set_attr(py, one.borrow(py), key, value)?;
            }
            return Ok(());
        }
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        // ONE crossing, N marshalled items, ZERO objects constructed (writes).
        crate::scale_audit::ffi(nodes.len() as u64, 0);
        crate::scale_audit::graph_writes(nodes.len() as u64);
        let v = py_to_value(py, value, &mut inner.interner)?;
        let k = inner.interner.intern(key);
        for n in &nodes {
            inner.set_attr(NodeID(n.value), k, v.clone());
        }
        Ok(())
    }

    // The per-node-VALUE complement of `set_attr_many`: writes `values[i]` onto
    // `nodes[i][key]` in ONE crossing. `set_attr_many` is uniform BY
    // CONSTRUCTION (one value, converted once); this rung's hot path — the
    // retina's per-cell luminance ingest — writes a DIFFERENT value per cell,
    // which is exactly why that loop survived the bulk conversion that batched
    // everything else. This is `[set_attr(n, key, v) for n, v in zip(nodes,
    // values)]`, evaluated on the Rust side of the boundary. NO new capability,
    // NO decision — the adapter still chooses WHICH nodes and WHAT values; only
    // the LOOP moves (CLAUDE.md: "primitive in Rust, composition in graph").
    //
    // BYTE-IDENTITY (PROTOCOL §9): the resulting graph state is bit-for-bit
    // what N `set_attr` calls produce — same interned key (interning is
    // idempotent), same per-value `py_to_value` conversion, same native writes.
    // The only thing NOT built is the transient old->new snapshot `set_attr`
    // constructs even when no hook can observe it — which changes no graph
    // state. HOOKS: if any `attr_set` hook is registered, fall back to the
    // per-node `set_attr` path so hook firing + order are identical.
    fn set_attr_each(
        &mut self,
        py: Python<'_>,
        nodes: Vec<PyRef<'_, PyNodeID>>,
        key: &str,
        values: Vec<Bound<'_, PyAny>>,
    ) -> PyResult<()> {
        if nodes.len() != values.len() {
            return Err(PyValueError::new_err(format!(
                "set_attr_each: {} nodes but {} values",
                nodes.len(),
                values.len()
            )));
        }
        // Hook parity FIRST: if anything can observe these writes, take the
        // per-node path that fires them exactly as `set_attr` does.
        if self.hooks.contains_key("attr_set") {
            let ids: Vec<u32> = nodes.iter().map(|n| n.value).collect();
            drop(nodes);
            for (v, val) in ids.into_iter().zip(values.into_iter()) {
                let one = Py::new(py, PyNodeID { value: v })?;
                self.set_attr(py, one.borrow(py), key, &val)?;
            }
            return Ok(());
        }
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        // ONE crossing, N marshalled items, N per-value conversions (the values
        // DIFFER per node), ZERO objects constructed on the write side.
        crate::scale_audit::ffi(nodes.len() as u64, 0);
        crate::scale_audit::graph_writes(nodes.len() as u64);
        let k = inner.interner.intern(key);
        for (n, val) in nodes.iter().zip(values.iter()) {
            let v = py_to_value(py, val, &mut inner.interner)?;
            inner.set_attr(NodeID(n.value), k, v);
        }
        Ok(())
    }

    fn has_node(&self, nid: PyRef<'_, PyNodeID>) -> bool {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.graph.has_node(nid.to_node())
    }

    fn has_edge(
        &self,
        src: PyRef<'_, PyNodeID>,
        edge_type: &str,
        tgt: PyRef<'_, PyNodeID>,
    ) -> bool {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let Some(et) = inner.interner.lookup(edge_type) else {
            return false;
        };
        inner.graph.has_edge(src.to_node(), et, tgt.to_node())
    }

    #[pyo3(signature = (type_=None))]
    fn nodes(&self, type_: Option<&str>) -> Vec<PyNodeID> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        match type_ {
            Some(t) => match inner.interner.lookup(t) {
                Some(sym) => inner
                    .graph
                    .nodes_of_type(sym)
                    .into_iter()
                    .map(PyNodeID::from_node)
                    .collect(),
                None => Vec::new(),
            },
            None => inner
                .graph
                .all_nodes()
                .into_iter()
                .map(PyNodeID::from_node)
                .collect(),
        }
    }

    #[pyo3(signature = (nid, edge_type=None))]
    fn neighbours(&self, nid: PyRef<'_, PyNodeID>, edge_type: Option<&str>) -> Vec<PyNodeID> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let et = edge_type.and_then(|t| inner.interner.lookup(t));
        let need_filter = edge_type.is_some() && et.is_none();
        if need_filter {
            return Vec::new();
        }
        inner
            .graph
            .neighbours(nid.to_node(), et)
            .into_iter()
            .map(PyNodeID::from_node)
            .collect()
    }

    #[pyo3(signature = (nid, edge_type=None))]
    fn in_neighbours(&self, nid: PyRef<'_, PyNodeID>, edge_type: Option<&str>) -> Vec<PyNodeID> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let et = edge_type.and_then(|t| inner.interner.lookup(t));
        let need_filter = edge_type.is_some() && et.is_none();
        if need_filter {
            return Vec::new();
        }
        inner
            .graph
            .in_neighbours(nid.to_node(), et)
            .into_iter()
            .map(PyNodeID::from_node)
            .collect()
    }

    fn node_count(&self) -> usize {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.graph.node_count()
    }

    /// Self-instrumentation: per-rule accumulated cost. Returns a list of
    /// (rule_name, micros, times_processed) so the agent (or a diagnostic) can
    /// read back which of its own rules dominates the tick — reliable, immune to
    /// the trajectory-change confound that makes neutering-and-timing lie.
    fn rule_costs(&self) -> Vec<(String, u64, u64, u64)> {
        let __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.rule_costs_report()
    }

    /// FALLBACK TRACE / H1: `(rule_name, attr_key, hits)` — this rule computed
    /// on an attribute NOBODY WROTE. See `fallback_trace`.
    fn defaulted_reads(&self) -> Vec<(String, String, u64)> {
        let __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.defaulted_reads_report()
    }

    /// FALLBACK TRACE / H2: `(rule_name, hits)` — this rule's `Not(Exists(..))`
    /// guard passed on an EMPTY source (the absence-branch hypothesis).
    fn absence_branches(&self) -> Vec<(String, u64)> {
        let __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.absence_branches_report()
    }

    /// `(attr_evals, attr_defaulted)`. The first is 0 unless
    /// `fallback_count_totals(True)` was set for the whole run — a 0 denominator
    /// means NOT MEASURED, never "no reads". Do not divide by it.
    fn fallback_attr_totals(&self) -> (u64, u64) {
        crate::fallback_trace::attr_totals()
    }

    /// Zero the fallback tallies so each probe arm is independent.
    fn fallback_trace_reset(&self) {
        crate::fallback_trace::reset()
    }

    /// Enable the hit-path `Attr` denominator. OFF by default — it is the only
    /// part of the instrument that costs anything on the healthy path, and it
    /// is needed only to compute the overhead FRACTION.
    #[staticmethod]
    fn fallback_count_totals(on: bool) {
        crate::fallback_trace::set_count_totals(on)
    }

    // --- SCALE AUDIT (`scale_audit.rs`) — the three-way wall decomposition ---
    //
    // These are the ONLY read/reset path for the counters. They take no
    // substrate lock: the counters are process-global atomics, deliberately, so
    // coverage is structural rather than dependent on every call site opting in
    // (the `selector_audit.rs` precedent, and the eleven-inert-instruments
    // lesson behind it).

    /// Every scale-audit counter as `(name, value)`, sorted by name.
    /// LOAD-INDEPENDENT INTEGERS — this exists precisely because wall-clock on
    /// this machine swings 1.66x on concurrent load alone.
    #[staticmethod]
    fn scale_audit_snapshot() -> Vec<(String, u64)> {
        crate::scale_audit::snapshot()
    }

    /// Zero every counter and close any open epoch.
    #[staticmethod]
    fn scale_audit_reset() {
        crate::scale_audit::reset()
    }

    /// Turn the audit on/off in-process. The harness's zero-when-off gate flips
    /// this rather than relying on process env, so ON and OFF are measurable in
    /// ONE process (an env-only switch would need two, and two processes are two
    /// different machine states).
    #[staticmethod]
    fn scale_audit_set_enabled(on: bool) {
        crate::scale_audit::set_enabled(on)
    }

    /// G5 RESPONSIVENESS — the verdict for one counter, as
    /// `"RESPONSIVE" | "BLIND" | "INERT"` (`g5.rs`).
    ///
    /// THE HARNESS DOES NOT REIMPLEMENT THIS. A second copy in Python is a copy
    /// that drifts, and a gate that has drifted from the gate its unit tests
    /// exercise is not a gate. One-line handoff, per the architecture rule.
    #[staticmethod]
    fn scale_audit_g5_verdict(sweep: Vec<u64>, control: Vec<u64>) -> String {
        crate::g5::verdict(&sweep, &control).as_str().to_string()
    }

    /// ρ — the log-log responsiveness diagnostic. `None` when undefined, rather
    /// than a fabricated 0.0 that would read as "measured and blind".
    /// **REPORTED, NEVER GATED** (see `g5.rs`).
    #[staticmethod]
    fn scale_audit_g5_rho(counter: Vec<u64>, axis: Vec<f64>) -> Option<f64> {
        crate::g5::rho(&counter, &axis)
    }

    /// Whether the audit is currently on.
    #[staticmethod]
    fn scale_audit_enabled() -> bool {
        crate::scale_audit::enabled()
    }

    /// DIAGNOSTIC — which distinct `DimInfer` argument-tuple each successive
    /// invocation carried, in call order. One-line handoff.
    #[staticmethod]
    fn scale_audit_dim_infer_arg_trace() -> Vec<u32> {
        crate::scale_audit::dim_infer_arg_trace()
    }

    /// DIAGNOSTIC — the distinct ordered argument encodings themselves, so a
    /// harness can diff them and report WHICH determinant moved. One-line
    /// handoff.
    #[staticmethod]
    fn scale_audit_dim_infer_arg_encodings() -> Vec<Vec<u8>> {
        crate::scale_audit::dim_infer_arg_encodings()
    }

    /// §9/§12.3 gate hook — see `Substrate::clear_pushdown_plans`. Restores the
    /// pre-pushdown matcher so a gate can compare old vs new path live.
    fn clear_pushdown_plans(&mut self) -> usize {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.clear_pushdown_plans()
    }

    /// Names of active rules carrying a pushdown plan (the positive control).
    fn pushdown_armed(&self) -> Vec<String> {
        let __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.pushdown_armed()
    }

    /// WITHIN-RUST ATTRIBUTION instrument — see `Substrate::profile_rule_match`.
    /// Read-only with respect to graph state (no-op visit, no apply), so calling
    /// it cannot move a committed number.
    #[pyo3(signature = (rule_name, reps=1))]
    fn profile_rule_match(&mut self, rule_name: &str, reps: usize) -> Vec<(String, u64, u64)> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.profile_rule_match(rule_name, reps)
    }

    fn reset_rule_costs(&mut self) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.reset_rule_costs();
    }

    fn edge_count(&self) -> usize {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.graph.edge_count()
    }

    // --- Causal Attitude Network operations ----------------------------
    //
    // grounding_theory + causal_attitude_networks + mt_target_equilibria
    // expressed as Rust ops on the typed graph. Each Concept node carries
    // attrs `state` (σ) + `external_field` (h); each Microtheory carries
    // `temperature` (β); `causal_influence` edges between Concepts carry
    // `weight` attr (J). See can_ops.rs for the surviving energy,
    // frustration, distance, target derivations. PHASE A (native-backend
    // cutover): the continuous mean-field / Ising mutation ops were
    // removed; the discrete-native graph rules are the sole dynamics.

    /// Energy H(σ) = -Σ J σσ - Σ h σ under Mt's Hamiltonian.
    /// `state` is a dict {node_id_int: float}; missing nodes default to 0.
    #[pyo3(signature = (mt, state))]
    fn mt_energy(
        &self,
        mt: PyRef<'_, PyNodeID>,
        state: std::collections::HashMap<u32, f32>,
    ) -> f32 {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let keys = match build_can_keys(inner) {
            Some(k) => k,
            None => return 0.0,
        };
        let state_map: rustc_hash::FxHashMap<crate::graph::NodeID, f32> = state
            .into_iter()
            .map(|(k, v)| (crate::graph::NodeID(k), v))
            .collect();
        crate::can_ops::mt_energy(&inner.graph, mt.to_node(), &keys, &state_map)
    }

    /// Per-concept target ⟨σ⟩* the Mt commits to (from each concept's
    /// `target_state` attr; defaults to +1.0 for has_concept members).
    fn mt_target(&self, mt: PyRef<'_, PyNodeID>) -> std::collections::HashMap<u32, f32> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let keys = match build_can_keys(inner) {
            Some(k) => k,
            None => return std::collections::HashMap::new(),
        };
        crate::can_ops::mt_target(&inner.graph, mt.to_node(), &keys)
            .into_iter()
            .map(|(n, v)| (n.0, v))
            .collect()
    }

    /// Distance from current committed state to Mt's target. Returns a
    /// dict:
    ///   "magnitude": float (L2),
    ///   "per_node": list of (node_id, deviation),
    ///   "max_dev_node": Optional[node_id],
    ///   "max_dev_value": Optional[float].
    ///
    /// PHASE A (native-backend cutover): reads each Concept's committed
    /// discrete `state` attr directly (the discrete-async mechanism's own
    /// equilibrium) rather than running a continuous mean-field
    /// relaxation. Pure read; representation-agnostic geometry.
    fn mt_distance_to_target<'py>(
        &self,
        py: Python<'py>,
        mt: PyRef<'_, PyNodeID>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let result = PyDict::new_bound(py);
        let keys = match build_can_keys(inner) {
            Some(k) => k,
            None => {
                result.set_item("magnitude", 0.0_f32)?;
                result.set_item("per_node", Vec::<(u32, f32)>::new())?;
                result.set_item("max_dev_node", py.None())?;
                result.set_item("max_dev_value", py.None())?;
                return Ok(result);
            }
        };
        // Current = committed `state` per owned Concept (native fixed
        // point); no relaxation.
        let concepts =
            crate::can_ops::mt_concepts(&inner.graph, mt.to_node(), keys.has_concept_edge);
        let mut current: rustc_hash::FxHashMap<crate::graph::NodeID, f32> =
            rustc_hash::FxHashMap::default();
        for &c in &concepts {
            current.insert(c, crate::can_ops::node_state(&inner.graph, c, &keys));
        }
        let target = crate::can_ops::mt_target(&inner.graph, mt.to_node(), &keys);
        let disp = crate::can_ops::distance_to_target(&current, &target);

        result.set_item("magnitude", disp.magnitude)?;
        let per_node: Vec<(u32, f32)> = disp.per_node.into_iter().map(|(n, d)| (n.0, d)).collect();
        result.set_item("per_node", per_node)?;
        match disp.max_dev {
            Some((n, d)) => {
                result.set_item("max_dev_node", n.0)?;
                result.set_item("max_dev_value", d)?;
            }
            None => {
                result.set_item("max_dev_node", py.None())?;
                result.set_item("max_dev_value", py.None())?;
            }
        }
        Ok(result)
    }

    /// Frustration index given an arbitrary state map. Used by
    /// predictive insight-seeking to predict ΔF on a what-if marginal.
    /// state is a dict {node_id_int: float}.
    #[pyo3(signature = (mt, state))]
    fn mt_frustration_given_state(
        &self,
        mt: PyRef<'_, PyNodeID>,
        state: std::collections::HashMap<u32, f32>,
    ) -> f32 {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let keys = match build_can_keys(inner) {
            Some(k) => k,
            None => return 0.0,
        };
        let state_map: rustc_hash::FxHashMap<crate::graph::NodeID, f32> = state
            .into_iter()
            .map(|(k, v)| (crate::graph::NodeID(k), v))
            .collect();
        crate::can_ops::mt_frustration_given_state(&inner.graph, mt.to_node(), &keys, &state_map)
    }

    /// Apply an evidence delta to a single Concept's external field.
    /// h_i ← h_i + alpha · evidence.
    #[pyo3(signature = (concept, evidence, alpha=1.0))]
    fn concept_apply_evidence(&mut self, concept: PyRef<'_, PyNodeID>, evidence: f32, alpha: f32) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let keys = match build_can_keys(inner) {
            Some(k) => k,
            None => return,
        };
        crate::can_ops::apply_evidence_h(
            &mut inner.graph,
            concept.to_node(),
            &keys,
            evidence,
            alpha,
        );
    }

    // --- Term evaluation -----------------------------------------------

    /// Relax a graph-resident Term to a fixed point over a set of cells,
    /// writing each cell's value into the `register` attr — the native
    /// iteration driver for attr-relaxation (passability-aware spatial distance
    /// is the first user). The relaxation DECISION lives wholly in `term` (graph
    /// data: what a distance is, which neighbour is passable); this primitive
    /// only sweeps it to convergence in Rust, so no Python loop drives the
    /// fixpoint and the incremental rule engine (which re-fires on matched EDGE
    /// types, not attrs read in effects, and so cannot drive an attr-relaxation
    /// rule) is bypassed. Jacobi sweeps: each sweep evaluates `term` for every
    /// cell (env binds "cell" -> the cell node) against the previous register
    /// values, then commits the changed registers; repeats until nothing
    /// changes or `max_sweeps` (0 = bound by the cell count, since no finite
    /// shortest path is longer). Returns the sweeps taken. Each cell eval uses a
    /// FRESH EvalCache so a neighbour's just-written value is seen — the
    /// staleness that froze run_rules cannot occur here.
    #[pyo3(signature = (term_json, cells, register, max_sweeps=0))]
    fn relax_to_fixpoint(
        &mut self,
        py: Python<'_>,
        term_json: &Bound<'_, PyAny>,
        cells: Vec<u32>,
        register: &str,
        max_sweeps: usize,
    ) -> PyResult<usize> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let json = pyobj_to_json_term(py, term_json, WireMode::Structural)?;
        let pre_parse = inner.terms.nodes.len();
        let idx = term_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad Term JSON: {:?}", e)))?;
        let post_parse = inner.terms.nodes.len();
        let reg = inner.interner.intern(register);
        let cell_sym = inner.interner.intern("cell");
        let cell_ids: Vec<NodeID> = cells.iter().map(|&v| NodeID(v)).collect();
        let cap = if max_sweeps == 0 {
            cell_ids.len() + 1
        } else {
            max_sweeps
        };
        let mut sweeps = 0usize;
        for _ in 0..cap {
            let mut updates: Vec<(NodeID, f64)> = Vec::new();
            for &c in &cell_ids {
                if !inner.graph.has_node(c) {
                    continue;
                }
                let mut env_v: Env = Default::default();
                env_v.push((cell_sym, Value::Node(c)));
                let mut cache = EvalCache::default();
                let nv = {
                    let SubstrateRs {
                        graph,
                        interner,
                        concepts,
                        terms,
                        counters,
                        active_shape_target,
                        shape_cache,
                        ..
                    } = &mut *inner;
                    let shape_target_copy = *active_shape_target;
                    let mut ctx = EvalCtx::new(graph, interner)
                        .with_cache(&mut cache)
                        .with_counters(counters)
                        .with_shape_cache(shape_cache);
                    if !concepts.is_empty() {
                        ctx = ctx.with_concepts(concepts);
                    }
                    if let Some(target) = shape_target_copy {
                        ctx = ctx.with_shape_target(target);
                    }
                    match evaluate(terms, idx, &mut env_v, &mut ctx) {
                        Value::Float(f) => Some(f),
                        Value::Int(i) => Some(i as f64),
                        _ => None,
                    }
                };
                inner.terms.nodes.truncate(post_parse);
                if let Some(nv) = nv {
                    let old = match inner.graph.node(c).attrs.get(&reg) {
                        Some(Value::Float(f)) => Some(*f),
                        Some(Value::Int(i)) => Some(*i as f64),
                        _ => None,
                    };
                    if old != Some(nv) {
                        updates.push((c, nv));
                    }
                }
            }
            if updates.is_empty() {
                break;
            }
            for (c, nv) in updates {
                inner.graph.set_node_attr(c, reg, Value::Float(nv));
            }
            sweeps += 1;
        }
        inner.terms.nodes.truncate(pre_parse);
        Ok(sweeps)
    }

    fn slide_flood(
        &mut self,
        seed: u32,
        slide: i64,
        fp_h: i64,
        fp_w: i64,
        walls: Vec<i64>,
        horizon: i64,
        epoch: i64,
        game: u32,
        mark_reached: bool,
        dist_attr: &str,
    ) -> PyResult<Vec<(u32, i64)>> {
        use std::collections::{HashMap, HashSet, VecDeque};
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let neighbour_sym = inner.interner.intern("neighbour");
        let row_sym = inner.interner.intern("row");
        let col_sym = inner.interner.intern("col");
        let value_sym = inner.interner.intern("value");
        // The distance attr the caller chooses: the avatar flood writes `_adist` (one-slide neighbours = 1),
        // the goal flood writes `_dist` (the gradient the hop descends). Two attrs so the hop can intersect
        // "is a true direct slide of the avatar" (_adist==1) with "minimises goal distance" (min _dist).
        let dist_sym = inner.interner.intern(dist_attr);
        let epoch_sym = inner.interner.intern("_epoch");
        // LEARNED passability: a per-cell, per-direction block the host stamps when a flood-approved press
        // produced NO movement (the world has a constraint the value-grid doesn't show -- a mover, a gate, a
        // hidden rule). The flood refuses any slide whose SOURCE cell is blocked in that direction, so the
        // agent stops proposing the dead move and routes elsewhere. This is the action-outcome correction
        // that closes the gap between the static reachability model and the real game.
        let blk_syms: [crate::sym::Sym; 4] = [
            inner.interner.intern("_blk_u"),
            inner.interner.intern("_blk_d"),
            inner.interner.intern("_blk_l"),
            inner.interner.intern("_blk_r"),
        ];
        let reached_sym = inner.interner.intern("reached");
        let game_id = NodeID(game);
        if mark_reached {
            for idx in inner.graph.out_edges_idx(game_id, Some(reached_sym)) {
                inner.graph.delete_edge(idx);
            }
        }
        let read_i64 =
            |g: &crate::graph::TypedGraph, nid: NodeID, sym: crate::sym::Sym| -> Option<i64> {
                match g.node(nid).attrs.get(&sym) {
                    Some(Value::Int(i)) => Some(*i),
                    Some(Value::Float(f)) => Some(*f as i64),
                    _ => None,
                }
            };
        let seed_id = NodeID(seed);
        if !inner.graph.has_node(seed_id) {
            return Ok(vec![]);
        }
        // RIGID-BODY slide flood. The agent is a `fp_h` x `fp_w` block whose TOP-LEFT corner is the seed
        // cell. It slides a FIXED `slide` cells per press and STOPS at a wall; a move in a direction is
        // admissible iff every cell the body sweeps into (the union of the old and new footprint) is
        // NON-WALL and on-grid. Passability is "not a wall value" (the body crosses floor, its own body,
        // and feature cells alike) -- NOT "== one ground value" -- because the world's walkable surface is
        // many-valued. The reachable set are body top-left positions, lattice-aligned to the seed, so the
        // gradient is exact (no centroid rounding, no point-vs-body mismatch). Re-flooding each frame tracks
        // a world whose obstacles move.
        // (row,col) -> NodeID index, built by BFS over the grid's `neighbour` edges from the seed.
        let mut cellidx: HashMap<(i64, i64), NodeID> = HashMap::new();
        let mut seen_cells: HashSet<NodeID> = HashSet::new();
        let mut bq: VecDeque<NodeID> = VecDeque::new();
        bq.push_back(seed_id);
        seen_cells.insert(seed_id);
        while let Some(n) = bq.pop_front() {
            if let (Some(r), Some(c)) = (
                read_i64(&inner.graph, n, row_sym),
                read_i64(&inner.graph, n, col_sym),
            ) {
                cellidx.insert((r, c), n);
            }
            for nb in inner.graph.neighbours(n, Some(neighbour_sym)) {
                if seen_cells.insert(nb) {
                    bq.push_back(nb);
                }
            }
        }
        let wallset: HashSet<i64> = walls.into_iter().collect();
        let val_at = |g: &crate::graph::TypedGraph,
                      ci: &HashMap<(i64, i64), NodeID>,
                      r: i64,
                      c: i64|
         -> Option<i64> {
            ci.get(&(r, c)).and_then(|&n| read_i64(g, n, value_sym))
        };
        let (sr, sc) = match (
            read_i64(&inner.graph, seed_id, row_sym),
            read_i64(&inner.graph, seed_id, col_sym),
        ) {
            (Some(r), Some(c)) => (r, c),
            _ => return Ok(vec![]),
        };
        let dirs: [(i64, i64); 4] = [(-1, 0), (1, 0), (0, -1), (0, 1)];
        let mut dist: HashMap<(i64, i64), i64> = HashMap::new();
        let mut queue: VecDeque<(i64, i64)> = VecDeque::new();
        dist.insert((sr, sc), 0);
        queue.push_back((sr, sc));
        inner
            .graph
            .set_node_attr(seed_id, dist_sym, Value::Float(0.0));
        inner
            .graph
            .set_node_attr(seed_id, epoch_sym, Value::Float(epoch as f64));
        if mark_reached {
            let _ = inner.graph.insert_edge(
                game_id,
                reached_sym,
                seed_id,
                FxHashMap::<Sym, Value>::default(),
            );
        }
        let mut out: Vec<(u32, i64)> = vec![(seed, 0)];
        while let Some((r, c)) = queue.pop_front() {
            let d = *dist.get(&(r, c)).unwrap_or(&0);
            if d >= horizon {
                continue;
            }
            for (di, &(dr, dc)) in dirs.iter().enumerate() {
                // refuse a move the source cell has LEARNED is dead in this direction.
                if let Some(&src) = cellidx.get(&(r, c)) {
                    if read_i64(&inner.graph, src, blk_syms[di]) == Some(1) {
                        continue;
                    }
                }
                let (nr, nc) = (r + dr * slide, c + dc * slide);
                // swept region = union of footprint at (r,c) and (nr,nc); all cells must exist & be non-wall.
                let (r0, r1) = (r.min(nr), r.max(nr) + fp_h - 1);
                let (c0, c1) = (c.min(nc), c.max(nc) + fp_w - 1);
                let mut ok = true;
                'sweep: for rr in r0..=r1 {
                    for cc in c0..=c1 {
                        match val_at(&inner.graph, &cellidx, rr, cc) {
                            Some(v) if !wallset.contains(&v) => {}
                            _ => {
                                ok = false;
                                break 'sweep;
                            }
                        }
                    }
                }
                if !ok {
                    continue;
                }
                if !dist.contains_key(&(nr, nc)) {
                    dist.insert((nr, nc), d + 1);
                    if let Some(&node) = cellidx.get(&(nr, nc)) {
                        inner
                            .graph
                            .set_node_attr(node, dist_sym, Value::Float((d + 1) as f64));
                        inner
                            .graph
                            .set_node_attr(node, epoch_sym, Value::Float(epoch as f64));
                        if mark_reached {
                            let _ = inner.graph.insert_edge(
                                game_id,
                                reached_sym,
                                node,
                                FxHashMap::<Sym, Value>::default(),
                            );
                        }
                        out.push((node.0, d + 1));
                    }
                    queue.push_back((nr, nc));
                }
            }
        }
        Ok(out)
    }

    /// PREDICTED-NEXT obstacle map — the sparse->dense bridge the jabberwock raised as an honest impasse
    /// (intrinsic-designer rung-3 to the creator): "primitive in Rust, composition in graph". Given the
    /// values the agent has LEARNED are impassable (from its KindPassability faculty — the adapter reads them,
    /// the LEARNING stays graph-resident; this primitive names no colour/wall), return the Cell node-ids that
    /// an impassable region occupies NOW or WILL occupy next frame (current cell + that kind's forward-model
    /// velocity drow/dcol, rounded). Feeding this to the HELD slide_flood/plan_passable_step routes the agent
    /// over the t+1 map: DYNAMIC (avoids where obstacles WILL be, e.g. its own advancing body), GENERIC (works
    /// in any world — impassable is whatever killed it, not a per-game constant). Cells remain graph nodes and
    /// the navigate_alive composition stays in graph; only this rasterize is the Rust primitive.
    fn principal_axes(&mut self, region: u32) -> PyResult<i64> {
        let mut __g = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__g;
        let responds_via_sym = inner.interner.intern("responds_via");
        let on_axis_sym = inner.interner.intern("on_axis");
        let axis_type = inner.interner.intern("Axis");
        let dr_sym = inner.interner.intern("dr");
        let dc_sym = inner.interner.intern("dc");
        let dz_sym = inner.interner.intern("dz");
        let dir_x_sym = inner.interner.intern("dir_x");
        let dir_y_sym = inner.interner.intern("dir_y");
        let dir_z_sym = inner.interner.intern("dir_z");
        let sign_sym = inner.interner.intern("sign");
        let ndim_sym = inner.interner.intern("ndim");
        let region_nid = NodeID(region);
        let read_f = |g: &crate::graph::TypedGraph, nid: NodeID, s: crate::sym::Sym| -> f64 {
            match g.node(nid).attrs.get(&s) {
                Some(Value::Float(f)) => *f,
                Some(Value::Int(i)) => *i as f64,
                _ => 0.0,
            }
        };
        // 2. Collect existing axes first (idempotency), dedup by NodeID.
        let mut axes: Vec<(NodeID, [f64; 3])> = Vec::new();
        let responders = inner.graph.neighbours(region_nid, Some(responds_via_sym));
        for cr in &responders {
            for ax in inner.graph.neighbours(*cr, Some(on_axis_sym)) {
                if axes.iter().any(|(a, _)| *a == ax) {
                    continue;
                }
                let d = [
                    read_f(&inner.graph, ax, dir_x_sym),
                    read_f(&inner.graph, ax, dir_y_sym),
                    read_f(&inner.graph, ax, dir_z_sym),
                ];
                axes.push((ax, d));
            }
        }
        // 3. Attach (or mint) an axis for each as-yet-unassigned control vector.
        for cr in &responders {
            if !inner.graph.neighbours(*cr, Some(on_axis_sym)).is_empty() {
                continue;
            }
            let v = [
                read_f(&inner.graph, *cr, dr_sym),
                read_f(&inner.graph, *cr, dc_sym),
                read_f(&inner.graph, *cr, dz_sym),
            ];
            let mag = (v[0] * v[0] + v[1] * v[1] + v[2] * v[2]).sqrt();
            if mag < 1e-6 {
                continue;
            }
            let mut hit: Option<(NodeID, f64)> = None;
            for (ax, d) in &axes {
                let dmag = (d[0] * d[0] + d[1] * d[1] + d[2] * d[2]).sqrt();
                if dmag < 1e-6 {
                    continue;
                }
                let dot = v[0] * d[0] + v[1] * d[1] + v[2] * d[2];
                if dot.abs() / (mag * dmag) > 0.99 {
                    hit = Some((*ax, dot));
                    break;
                }
            }
            match hit {
                Some((ax, dot)) => {
                    let _ = inner.graph.insert_edge(
                        *cr,
                        on_axis_sym,
                        ax,
                        rustc_hash::FxHashMap::default(),
                    );
                    inner.set_attr(
                        *cr,
                        sign_sym,
                        Value::Float(if dot > 0.0 { 1.0 } else { -1.0 }),
                    );
                }
                None => {
                    let ax = inner.add_node(axis_type, rustc_hash::FxHashMap::default());
                    inner.set_attr(ax, dir_x_sym, Value::Float(v[0]));
                    inner.set_attr(ax, dir_y_sym, Value::Float(v[1]));
                    inner.set_attr(ax, dir_z_sym, Value::Float(v[2]));
                    let _ = inner.graph.insert_edge(
                        *cr,
                        on_axis_sym,
                        ax,
                        rustc_hash::FxHashMap::default(),
                    );
                    inner.set_attr(*cr, sign_sym, Value::Float(1.0));
                    axes.push((ax, v));
                }
            }
        }
        // 4. Record the discovered dimensionality on the region.
        let len = axes.len();
        inner.set_attr(region_nid, ndim_sym, Value::Float(len as f64));
        Ok(len as i64)
    }

    fn predict_wall_set(
        &mut self,
        h: i64,
        w: i64,
        impassable_values: Vec<i32>,
    ) -> PyResult<Vec<u32>> {
        use std::collections::{HashMap, HashSet};
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        // cells are ingested as WorldInstance nodes carrying row/col/value (world_type=="Cell"); only the
        // grid cells have row+col+value, so the (row,col) guard below selects exactly them.
        let cell_t = inner.interner.intern("WorldInstance");
        let region_t = inner.interner.intern("Region");
        let row_sym = inner.interner.intern("row");
        let col_sym = inner.interner.intern("col");
        let value_sym = inner.interner.intern("value");
        let rvalue_sym = inner.interner.intern("rvalue");
        let drow_sym = inner.interner.intern("drow");
        let dcol_sym = inner.interner.intern("dcol");
        let ground_sym = inner.interner.intern("is_ground");
        let read_i =
            |g: &crate::graph::TypedGraph, nid: NodeID, s: crate::sym::Sym| -> Option<i64> {
                match g.node(nid).attrs.get(&s) {
                    Some(Value::Int(i)) => Some(*i),
                    Some(Value::Float(f)) => Some(*f as i64),
                    _ => None,
                }
            };
        let read_f = |g: &crate::graph::TypedGraph, nid: NodeID, s: crate::sym::Sym| -> f64 {
            match g.node(nid).attrs.get(&s) {
                Some(Value::Float(f)) => *f,
                Some(Value::Int(i)) => *i as f64,
                _ => 0.0,
            }
        };
        let imp: HashSet<i32> = impassable_values.into_iter().collect();
        // kind -> (drow,dcol): the per-kind forward-model velocity, from the impassable non-ground regions
        let mut vel: HashMap<i32, (i64, i64)> = HashMap::new();
        for nid in inner.graph.nodes_of_type(region_t) {
            if read_f(&inner.graph, nid, ground_sym) == 1.0 {
                continue;
            }
            if let Some(rv) = read_i(&inner.graph, nid, rvalue_sym) {
                if !imp.contains(&(rv as i32)) {
                    continue;
                }
                let dr = read_f(&inner.graph, nid, drow_sym).round() as i64;
                let dc = read_f(&inner.graph, nid, dcol_sym).round() as i64;
                vel.insert(rv as i32, (dr, dc));
            }
        }
        // (row,col) -> cell node id, and the currently-impassable occupied cells (actual cells, not bbox)
        let mut cellidx: HashMap<(i64, i64), u32> = HashMap::new();
        let mut occupied: Vec<(i64, i64, i32)> = Vec::new();
        for nid in inner.graph.nodes_of_type(cell_t) {
            let (r, c) = match (
                read_i(&inner.graph, nid, row_sym),
                read_i(&inner.graph, nid, col_sym),
            ) {
                (Some(r), Some(c)) => (r, c),
                _ => continue,
            };
            cellidx.insert((r, c), nid.0);
            if let Some(v) = read_i(&inner.graph, nid, value_sym) {
                if imp.contains(&(v as i32)) {
                    occupied.push((r, c, v as i32));
                }
            }
        }
        let mut walls: HashSet<u32> = HashSet::new();
        for (r, c, v) in occupied {
            if let Some(&id) = cellidx.get(&(r, c)) {
                walls.insert(id);
            } // occupied NOW
            let (dr, dc) = *vel.get(&v).unwrap_or(&(0, 0));
            let (nr, nc) = (r + dr, c + dc);
            if nr >= 0 && nr < h && nc >= 0 && nc < w {
                if let Some(&id) = cellidx.get(&(nr, nc)) {
                    walls.insert(id);
                } // occupied NEXT (t+1)
            }
        }
        Ok(walls.into_iter().collect())
    }

    #[pyo3(signature = (term_json, env=None))]
    fn evaluate<'py>(
        &mut self,
        py: Python<'py>,
        term_json: &Bound<'_, PyAny>,
        env: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let json = pyobj_to_json_term(py, term_json, WireMode::Structural)?;
        // Ingest into the substrate's arena so any concept TermIdx
        // resolved via Holds (which lives in this same arena) is in
        // bounds. The arena grows monotonically; we snapshot its len
        // and truncate back after eval so repeated evaluate() calls
        // don't leak.
        let snapshot = inner.terms.nodes.len();
        let idx = term_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad Term JSON: {:?}", e)))?;
        let mut env_v = pydict_to_env(py, env, &mut inner.interner)?;
        let mut cache = EvalCache::default();
        inner.counters.on_evaluation();
        // Split the &mut *inner borrow so we can hand mutable
        // counters AND immutable graph/interner/concepts/terms to the
        // ctx in one breath.
        let SubstrateRs {
            graph,
            interner,
            concepts,
            terms,
            counters,
            active_shape_target,
            shape_cache,
            ..
        } = &mut *inner;
        let shape_target_copy = *active_shape_target;
        let mut ctx = EvalCtx::new(graph, interner)
            .with_cache(&mut cache)
            .with_counters(counters)
            .with_shape_cache(shape_cache);
        if !concepts.is_empty() {
            ctx = ctx.with_concepts(concepts);
        }
        if let Some(target) = shape_target_copy {
            ctx = ctx.with_shape_target(target);
        }
        let v = evaluate(terms, idx, &mut env_v, &mut ctx);
        // Release the scratch Terms — concepts/productions live below
        // the snapshot so their TermIdx remain valid.
        terms.nodes.truncate(snapshot);
        value_to_py(py, &v, &inner.interner)
    }

    // --- Phase 7 observability surface ----------------------------------

    /// Snapshot the current counters as a dict — what the Python
    /// `substrate_rs.ext.counters(s)` helper unwraps for callers.
    fn counters<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let d = PyDict::new_bound(py);
        let c = &inner.counters;
        d.set_item("nodes_inserted_total", c.nodes_inserted_total)?;
        d.set_item("edges_inserted_total", c.edges_inserted_total)?;
        d.set_item("admissibility_checks_total", c.admissibility_checks_total)?;
        d.set_item("rejections_type1", c.rejections_type1)?;
        d.set_item("rejections_type2", c.rejections_type2)?;
        d.set_item("evaluations_total", c.evaluations_total)?;
        d.set_item("cache_neighbours_hits", c.cache_neighbours_hits)?;
        d.set_item("cache_neighbours_misses", c.cache_neighbours_misses)?;
        d.set_item("cache_filter_hits", c.cache_filter_hits)?;
        d.set_item("cache_filter_misses", c.cache_filter_misses)?;
        d.set_item("derivation_shape_pruned", c.derivation_shape_pruned)?;
        d.set_item("concept_shape_pruned", c.concept_shape_pruned)?;

        let by_type = PyDict::new_bound(py);
        for (sym, n) in &c.nodes_inserted_by_type {
            by_type.set_item(inner.interner.resolve(*sym), n)?;
        }
        d.set_item("nodes_inserted_by_type", by_type)?;

        let edge_by_type = PyDict::new_bound(py);
        for (sym, n) in &c.edges_inserted_by_type {
            edge_by_type.set_item(inner.interner.resolve(*sym), n)?;
        }
        d.set_item("edges_inserted_by_type", edge_by_type)?;

        let prod_admits = PyDict::new_bound(py);
        for (pi, n) in &c.production_admits {
            let prod = &inner.checker.grammar.productions[pi.0 as usize];
            let key = inner.interner.resolve(prod.provenance).to_string();
            prod_admits.set_item(key, n)?;
        }
        d.set_item("production_admits", prod_admits)?;

        let prod_rejects = PyDict::new_bound(py);
        for (pi, n) in &c.production_rejects {
            let prod = &inner.checker.grammar.productions[pi.0 as usize];
            let key = inner.interner.resolve(prod.provenance).to_string();
            prod_rejects.set_item(key, n)?;
        }
        d.set_item("production_rejects", prod_rejects)?;

        // The ρ-helper (Paper §1): live node + edge count as the
        // operational complexity proxy denominator.
        d.set_item(
            "rho_g_size",
            inner.graph.node_count() + inner.graph.edge_count(),
        )?;
        Ok(d)
    }

    fn counters_clear(&mut self) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.counters.clear();
    }

    // --- Phase 7b: attr indices ---

    /// Declare a secondary attribute index on `(node_type, attr_key)`.
    /// All existing nodes of that type with that attr are back-filled
    /// at declaration; subsequent insert/delete/set_attr/set_type
    /// maintain the index.
    fn declare_attr_index(&mut self, node_type: &str, attr_key: &str) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let t = inner.interner.intern(node_type);
        let k = inner.interner.intern(attr_key);
        inner.declare_attr_index(t, k);
    }

    /// Direct O(1)-lookup of `nodes_where`. Returns an empty list if
    /// the index isn't declared OR if no nodes match.
    fn nodes_where(
        &mut self,
        py: Python<'_>,
        node_type: &str,
        attr_key: &str,
        value: &Bound<'_, PyAny>,
    ) -> PyResult<Vec<PyNodeID>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let v = py_to_value(py, value, &mut inner.interner)?;
        let t = inner.interner.intern(node_type);
        let k = inner.interner.intern(attr_key);
        Ok(inner
            .nodes_where(t, k, &v)
            .into_iter()
            .map(PyNodeID::from_node)
            .collect())
    }

    /// Insert an edge bypassing Γ admissibility. Reserved for
    /// search-edge assignments (`substrate_rs.ext.search_*`) where the
    /// edge is a scratch annotation, not a domain claim — the caller
    /// guarantees its admissibility doesn't matter. Same return shape
    /// as `add_edge` but never raises `InadmissibleEdge`.
    ///
    /// `add_edge` is still the right path for everything that should
    /// be gated by Γ. The "unchecked" name is the only reason it's
    /// safe to expose: callers can't conflate the two paths.
    #[pyo3(signature = (src, edge_type, tgt, attrs=None))]
    fn add_edge_unchecked(
        &mut self,
        py: Python<'_>,
        src: PyRef<'_, PyNodeID>,
        edge_type: &str,
        tgt: PyRef<'_, PyNodeID>,
        attrs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<()> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let attrs_map = pydict_to_attrs(py, attrs, &mut inner.interner)?;
        let et = inner.interner.intern(edge_type);
        let _ = inner
            .graph
            .insert_edge(src.to_node(), et, tgt.to_node(), attrs_map);
        // "unchecked" refers to ADMISSIBILITY, not OBSERVABILITY — wake the rules
        // that read this edge type, exactly as the checked add_edge does. Without
        // this, a has_change-reading rule with no where-clause would never fire
        // once the all-cells set_attr storm (which currently dirties everything via
        // mark_node_mutation) is removed by the incremental-perception redesign.
        inner.mark_edge_type_dirty(et);
        // Hooks still fire — the observer doesn't care which gate the
        // edge passed through, only that it exists.
        let src_node = src.to_node();
        let tgt_node = tgt.to_node();
        self.fire_hook(
            py,
            "edge_inserted",
            &[
                Py::new(py, PyNodeID::from_node(src_node))?.into_any(),
                edge_type.to_string().into_py(py),
                Py::new(py, PyNodeID::from_node(tgt_node))?.into_any(),
            ],
        )?;
        Ok(())
    }

    /// Drop an edge by triple. Like `remove_edge` but with no Π
    /// surface implication — paired with `add_edge_unchecked` for the
    /// search-edge use case.
    fn remove_edge_unchecked(
        &mut self,
        py: Python<'_>,
        src: PyRef<'_, PyNodeID>,
        edge_type: &str,
        tgt: PyRef<'_, PyNodeID>,
    ) -> PyResult<bool> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let Some(et) = inner.interner.lookup(edge_type) else {
            return Ok(false);
        };
        let removed = if let Some(idx) = inner.graph.edge_idx(src.to_node(), et, tgt.to_node()) {
            inner.graph.delete_edge(idx).is_some()
        } else {
            false
        };
        if removed {
            self.fire_hook(
                py,
                "edge_deleted",
                &[
                    Py::new(py, PyNodeID::from_node(src.to_node()))?.into_any(),
                    edge_type.to_string().into_py(py),
                    Py::new(py, PyNodeID::from_node(tgt.to_node()))?.into_any(),
                ],
            )?;
        }
        Ok(removed)
    }

    fn has_attr_index(&self, node_type: &str, attr_key: &str) -> bool {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let Some(t) = inner.interner.lookup(node_type) else {
            return false;
        };
        let Some(k) = inner.interner.lookup(attr_key) else {
            return false;
        };
        inner.graph.has_attr_index(t, k)
    }

    // --- Phase 7c: rewrite rules ---

    /// Register a rewrite rule from its dict form. Wire shape:
    ///   {"name": str,
    ///    "match": [[src_var, edge_type, tgt_var], ...],
    ///    "where": {<term JSON>} | None,
    ///    "effects": [<effect-op>, ...]}
    ///
    /// Effect ops:
    ///   ["add_edge", src_var, edge_type, tgt_var, {attr: literal-or-term-dict}?]
    ///   ["del_edge", src_var, edge_type, tgt_var]
    ///   ["add_node", new_var, type, {attr: literal-or-term-dict}]
    ///   ["del_node", var]
    ///   ["set_attr", var, key, literal-or-term-dict]
    /// A term-dict is `{"__term__": {<term JSON>}}`; otherwise the
    /// value is a literal.
    fn add_rule(&mut self, py: Python<'_>, rule_dict: &Bound<'_, PyAny>) -> PyResult<u32> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let json = pyobj_to_json(py, rule_dict)?;
        let mut rule = parse_rule_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad rule JSON: {}", e)))?;
        // `add_rule` is the live authoring surface, not checkpoint restore:
        // copied install metadata must never make a newly-authored successor
        // immutable. `import_rules` below is the sole path that preserves it.
        rule.mutation_protected = false;
        Ok(inner.add_rule(rule).0)
    }

    /// Stable identity/CAS metadata for one dense rule slot.
    fn rule_metadata<'py>(&self, py: Python<'py>, rule_idx: u32) -> PyResult<Bound<'py, PyDict>> {
        let guard = self.inner.lock().expect("substrate mutex poisoned");
        let (uid, revision, content_hash, active) = guard
            .rule_metadata(crate::rewrite::RuleIdx(rule_idx))
            .ok_or_else(|| PyValueError::new_err("rule index out of range"))?;
        let out = PyDict::new_bound(py);
        out.set_item("rule_idx", rule_idx)?;
        out.set_item("rule_uid", uid.0)?;
        out.set_item("revision", revision)?;
        out.set_item("content_hash", content_hash)?;
        out.set_item("active", active)?;
        out.set_item(
            "mutation_protected",
            guard.rules[rule_idx as usize].mutation_protected,
        )?;
        Ok(out)
    }

    /// Mechanical binding for the same CAS transaction graph rules invoke via
    /// `ApplyRulePatch`. Agent decisions belong in RulePatch graph data; this
    /// surface exists for checkpoint tooling and focused conformance tests.
    fn apply_rule_patch<'py>(
        &mut self,
        py: Python<'py>,
        target_uid: u64,
        expected_revision: u64,
        expected_content_hash: u64,
        field: &str,
        proposed_clause: &Bound<'_, PyAny>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let j = pyobj_to_json(py, proposed_clause)?;
        let clause = decode_value(&j, &mut guard.interner);
        let receipt = guard
            .apply_rule_patch(
                crate::rewrite::RuleUid(target_uid),
                expected_revision,
                expected_content_hash,
                field,
                clause,
            )
            .map_err(|error| {
                PyValueError::new_err(format!("rule patch refused: {}", error.code()))
            })?;
        let out = PyDict::new_bound(py);
        out.set_item("target_uid", receipt.uid.0)?;
        out.set_item("previous_revision", receipt.previous_revision)?;
        out.set_item("previous_content_hash", receipt.previous_content_hash)?;
        out.set_item("revision", receipt.revision)?;
        out.set_item("content_hash", receipt.content_hash)?;
        out.set_item(
            "inverse_clause",
            value_to_py(py, &receipt.inverse_clause, &guard.interner)?,
        )?;
        Ok(out)
    }

    fn apply_rule_once(&mut self, rule_idx: u32) -> bool {
        // SCALE AUDIT: one Python->Rust entry into a rule-running method = one
        // EPOCH. Re-enumeration WITHIN an epoch is charged to R; re-enumeration
        // ACROSS epochs (the adapter's `while apply_rule_once(idx): pass` drive
        // loop) is deliberately NOT, so R stays a LOWER bound (prereg §3).
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch_kind(true);
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.apply_rule_once(crate::rewrite::RuleIdx(rule_idx))
    }

    /// `apply_rule_once` at the whole-binding-set grain for rules that set
    /// `batch`; identical to `apply_rule_once` for rules that do not.
    ///
    /// One line, handing straight off to Rust (CLAUDE.md: primitive in Rust,
    /// composition in graph). The DECISION of whether to batch is graph DATA
    /// — the rule's own `batch` attribute — never a branch in the adapter.
    fn apply_rule_batch(&mut self, rule_idx: u32) -> bool {
        // Charged exactly as `apply_rule_once` is: one Python->Rust entry into
        // a rule-running method = one EPOCH. Keeping the charge identical is
        // what makes the before/after counts comparable — the whole point of
        // the intervention is that this method is called FEWER times, and a
        // differently-charged entry would confound that with a book-keeping
        // change (`VISION_BATCH_APPLY_PREREG.md` D2).
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch_kind(true);
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.apply_rule_batch(crate::rewrite::RuleIdx(rule_idx))
    }

    #[pyo3(signature = (max_steps=100_000))]
    fn run_rules(&mut self, py: Python<'_>, max_steps: usize) -> usize {
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch();
        py.allow_threads(|| {
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            guard.run_rules(max_steps)
        })
    }

    /// PER-MT SCOPED fixpoint (CAN_MT_SCOPED_RULES_PREREG/RESULTS.md).
    /// ADDITIVE — `run_rules`/`run_rules_settle` above are unchanged.
    /// `scope_mt=None` (the default) is byte-for-byte `run_rules`: the
    /// underlying `Substrate::run_rules_scoped` calls the existing
    /// `run_rules_opts` directly on this arm, not a re-implementation.
    /// `scope_mt=Some(mt)` restricts the fixpoint to bindings that touch
    /// `mt`'s owned nodes (`mt` itself + its `has_concept` neighbours),
    /// so a caller can safely drive one Microtheory's native CAN rules
    /// (e.g. `can_native_update_3state`, `can_native_hebbian_mint`)
    /// without mutating an unrelated Microtheory's state as a side effect.
    #[pyo3(signature = (max_steps=100_000, detect_cycles=false, scope_mt=None))]
    fn run_rules_scoped(
        &mut self,
        py: Python<'_>,
        max_steps: usize,
        detect_cycles: bool,
        scope_mt: Option<PyRef<'_, PyNodeID>>,
    ) -> usize {
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch();
        let scope_node = scope_mt.as_ref().map(|r| r.to_node());
        py.allow_threads(|| {
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            guard.run_rules_scoped(max_steps, detect_cycles, scope_node)
        })
    }

    /// PER-AREA ASYNC SETTLEMENT (block 186000). **DEFAULT OFF and built
    /// ALONGSIDE the global fixpoint** — `run_rules` above is unchanged and
    /// remains both the default and the correctness oracle. Nothing in the
    /// committed tree calls this; a caller must ask for it by name.
    ///
    /// A cortex tick is a SETTLEMENT EVENT that CARRIES a residual: each area
    /// settles as much of its own accumulated surprise as `budget_per_area`
    /// affords this round, then yields, carrying the rest forward. An area
    /// with no dirty rule does NO work. `budget_per_area = 0` is UNBOUNDED —
    /// the REDUCTION arm that must reproduce the global fixpoint's final
    /// state. `drop_residual = true` is the FALSIFIER arm: it DISCARDS what
    /// the budget did not reach instead of carrying it, and must diverge.
    ///
    /// `snapshot_round = false` (default) is the ASYNC form: an area reads its
    /// own dirty set when ITS turn comes, so there is no barrier anywhere.
    /// `snapshot_round = true` is the BARRIER form: every area's dirty set is
    /// read once at round start, so a round attempts exactly the rule multiset
    /// one committed global pass would, permuted into area-major order. The
    /// difference between the two arms measures how much of the fixpoint's
    /// answer depends on the barrier.
    ///
    /// Returns the settlement ledger: per round, per area, how much was dirty,
    /// how much the budget reached, how much progressed, how much was carried.
    #[pyo3(signature = (budget_per_area=0, max_rounds=100_000,
                        drop_residual=false, snapshot_round=false))]
    fn run_rules_settle<'py>(
        &mut self,
        py: Python<'py>,
        budget_per_area: usize,
        max_rounds: usize,
        drop_residual: bool,
        snapshot_round: bool,
    ) -> PyResult<Bound<'py, PyAny>> {
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch();
        let report = {
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            guard.run_rules_settle(budget_per_area, max_rounds, drop_residual, snapshot_round)
        };
        let guard = self.inner.lock().expect("substrate mutex poisoned");
        let name = |s: Sym| -> String {
            if s == Sym::default() {
                "global".to_string()
            } else {
                guard.interner.resolve(s).to_string()
            }
        };
        let rounds: Vec<J> = report
            .rounds
            .iter()
            .map(|r| {
                let rows: Vec<J> = r
                    .rows
                    .iter()
                    .map(|row| {
                        serde_json::json!({
                            "area": name(row.area),
                            "dirty": row.dirty,
                            "attempted": row.attempted,
                            "steps": row.steps,
                            "carried": row.carried,
                        })
                    })
                    .collect();
                serde_json::json!({
                    "steps": r.steps,
                    "dirty_areas": r.dirty_areas,
                    "residual": r.residual,
                    "rows": rows,
                })
            })
            .collect();
        let areas: Vec<J> = report
            .areas
            .iter()
            .map(|a| serde_json::json!(name(*a)))
            .collect();
        json_to_pyobj(
            py,
            &serde_json::json!({
                "steps": report.steps,
                "rounds": rounds,
                "n_rounds": report.rounds.len(),
                "areas": areas,
                "hit_max_rounds": report.hit_max_rounds,
            }),
        )
    }

    /// Relabel one rule's AREA — scheduling metadata only (no committed code
    /// path reads `rule.area`; the default fixpoint iterates rule INDICES).
    /// Mechanical, so a measurement can split an existing seed's rules across
    /// areas without editing committed seed data. Returns whether it matched.
    fn set_rule_area(&mut self, rule_name: &str, area: &str) -> bool {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let n = guard.interner.intern(rule_name);
        let a = guard.interner.intern(area);
        guard.set_rule_area(n, a)
    }

    /// The AREA of each active rule, by rule name — read-only introspection so
    /// a gate can assert the partition it is measuring without guessing.
    fn rule_areas<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let guard = self.inner.lock().expect("substrate mutex poisoned");
        let rows: Vec<J> = guard
            .rules
            .iter()
            .filter(|r| r.active)
            .map(|r| {
                serde_json::json!([
                    guard.interner.resolve(r.name).to_string(),
                    if r.area == Sym::default() {
                        "global".to_string()
                    } else {
                        guard.interner.resolve(r.area).to_string()
                    },
                ])
            })
            .collect();
        json_to_pyobj(py, &serde_json::json!(rows))
    }

    // --- GAMMA_COLLAPSE_ALGORITHM spike ---

    /// **DEFAULT OFF.** Capture Type-1 `Γ` rejections as graph-resident
    /// `GammaResidual` nodes instead of discarding the rejected triple (see
    /// `Substrate::gamma_residual_capture`). Off ⇒ `add_edge`'s
    /// `Type1NoProduction` arm is byte-unchanged.
    fn set_gamma_residual_capture(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_gamma_residual_capture(on);
    }

    // --- DIRTY-PROPAGATION PRECISION (block 187000) ---

    /// **DEFAULT OFF.** Turn on the key-precise + value-level external dirty
    /// path (see `Substrate::precise_dirty`). Off ⇒ the committed blanket.
    fn set_precise_dirty(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_precise_dirty(on);
    }

    /// **DEFAULT OFF.** Maintain the dirty-mark telemetry counters. Costs the
    /// no-op-write value comparison, so the committed path never pays it.
    fn set_dirty_telemetry(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_dirty_telemetry(on);
    }

    /// **THE WRONG-PRECISION FALSIFIER.** Over-aggressive predicate that skips
    /// genuinely-dirty rules; MUST break byte-identity. Measurement use only.
    fn set_dirty_overaggressive(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_dirty_overaggressive(on);
    }

    /// BINDING PROJECTION (block 188000), **DEFAULT OFF**. Deduplicate a rule's
    /// binding set on the variables its where-clause and effects actually
    /// reference, for rules whose remaining effects are attribute writes only.
    /// A droppable, byte-identical mirror: it removes a RE-DERIVATION, never a
    /// DECISION.
    fn set_binding_projection(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_binding_projection(on);
    }

    /// **THE WRONG-PROJECTION FALSIFIER.** Projects on the EMPTY variable set,
    /// so a rule fires at most once per visit however many distinct hubs match.
    /// MUST break byte-identity. Measurement use only.
    fn set_projection_overaggressive(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_projection_overaggressive(on);
    }

    /// Read-only introspection: the rules for which binding projection is
    /// admissible, as `(rule_name, area, projected_vars)`. Mechanical.
    fn projectable_rules(&self) -> Vec<(String, String, Vec<String>)> {
        let g = self.inner.lock().expect("substrate mutex poisoned");
        g.projectable_rules()
    }

    /// EMPTY-MATCH-SET PROOF (block 189000), **DEFAULT OFF**. Skip the
    /// enumeration of a rule whose match set is PROVABLY empty under the current
    /// graph — some match edge's edge type has ZERO live edges, so no binding
    /// can exist. A droppable, byte-identical mirror: it removes an enumeration
    /// that provably yields nothing, never a DECISION.
    fn set_empty_match_proof(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_empty_match_proof(on);
    }

    /// **THE UNSOUND-PREDICATE FALSIFIER.** Claims "empty" when a match edge
    /// type has ≤ 1 live edge, i.e. treats a SINGLETON edge type as absent — a
    /// rule that binds a one-of-a-kind edge is then silently never run. MUST
    /// break byte-identity. Measurement use only.
    fn set_empty_match_proof_unsound(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_empty_match_proof_unsound(on);
    }

    /// INCREMENTAL MATCH (block 192000 — ladder rung A), DEFAULT OFF. ON ⇒
    /// semi-naive cursors are validated against PER-EDGE-TYPE delete versions,
    /// so a delete of an unrelated edge type no longer forces a full rescan;
    /// retraction stays correct (a delete of a rule's own match type invalidates
    /// it) and where-flip catching is preserved (where-rules' cursors are
    /// cleared on external node/attr writes). OFF ⇒ the committed engine,
    /// byte-identical. The eye's where-gated mint rules fall back to full rescan
    /// (rung B's target).
    fn set_incremental_match(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_incremental_match(on);
    }

    /// **THE UNSOUND-RETRACTION FALSIFIER** (block 192000). Accepts a stale
    /// cursor regardless of its edge type's delete version, so a delete of a
    /// rule's own match type is NOT retracted — the graph diverges from the full
    /// rescan on any deleting workload. MUST break byte-identity. Measurement
    /// use only.
    fn set_incremental_match_unsound(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_incremental_match_unsound(on);
    }

    /// PREDICATE RETRACTION (block 194000, ladder rung B), DEFAULT FALSE. When
    /// on, an external attr write to a node records the node against the covered
    /// where-rules that read the written key and KEEPS their cursors, instead of
    /// clearing the whole cursor and forcing an O(N) full rescan. On the rule's
    /// next attempt only the bindings that TOUCH the written node(s) are
    /// re-evaluated (node-seeded, lean-TREAT) — O(K) for a K-node attr flip on
    /// stable edges, byte-identical to the full rescan. Covers the stable-edge
    /// attr-flip shape rung A named and fell back on (fire direction, add-only
    /// effects). OFF ⇒ the committed path, byte-unchanged.
    fn set_predicate_retraction(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_predicate_retraction(on);
    }

    /// **THE UNSOUND-RETRACTION FALSIFIER** (block 194000). Drops one dirty node
    /// from the node-seeded re-evaluation set, so a binding whose predicate
    /// flipped to TRUE on it is never re-fired — the graph diverges from the
    /// full rescan (a fired / minted observable moves). MUST break byte-identity.
    /// Measurement use only.
    fn set_predicate_retraction_unsound(&mut self, on: bool) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .set_predicate_retraction_unsound(on);
    }

    /// Read-only telemetry: `(rule_name, enumerations_skipped)`. Mechanical.
    fn empty_match_skips(&self) -> Vec<(String, u64)> {
        let g = self.inner.lock().expect("substrate mutex poisoned");
        g.empty_match_skips()
    }

    fn reset_empty_match_skips(&mut self) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .reset_empty_match_skips();
    }

    /// Read-only introspection: which ACTIVE rules are provably empty RIGHT NOW,
    /// as `(rule_name, area, the zero-population edge type that proves it)`.
    /// Evaluated independently of the flag. Mechanical.
    fn provably_empty_rules(&self) -> Vec<(String, String, String)> {
        let g = self.inner.lock().expect("substrate mutex poisoned");
        g.provably_empty_rules()
    }

    /// `{writeset, edge_type, external, attr_writes, noop_attr_writes,
    /// external_events}` — dirty MARKS by the path that made them, counted at
    /// the false→true transition only.
    fn dirty_marks<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let m = self
            .inner
            .lock()
            .expect("substrate mutex poisoned")
            .dirty_marks();
        json_to_pyobj(
            py,
            &serde_json::json!({
                "writeset": m[0], "edge_type": m[1], "external": m[2],
                "attr_writes": m[3], "noop_attr_writes": m[4], "external_events": m[5],
                "writeset_transitions": m[6], "edge_type_transitions": m[7],
                "external_transitions": m[8],
            }),
        )
    }

    fn reset_dirty_marks(&mut self) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .reset_dirty_marks();
    }

    /// How many ACTIVE rules currently hold a dirty bit.
    fn dirty_rule_count(&self) -> usize {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .dirty_rule_count()
    }

    /// `(rule, area)` for every active rule currently dirty.
    fn dirty_rule_names(&self) -> Vec<(String, String)> {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .dirty_rule_names()
    }

    /// DIAGNOSTIC: mark every rule dirty + invalidate every cursor. Lets a
    /// measurement PROVE a precise-dirty run landed on a genuine fixpoint —
    /// force everything dirty, run the committed loop, expect ZERO steps.
    fn force_all_dirty(&mut self) {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .force_all_dirty();
    }

    /// `(rule, area)` for every active rule whose read-set contains `Attr(key)`.
    fn rules_reading_attr(&self, key: &str) -> Vec<(String, String)> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let k = guard.interner.intern(key);
        guard.rules_reading_attr(k)
    }

    /// The AREAS holding at least one dirty active rule, canonical order.
    fn dirty_area_names(&self) -> Vec<String> {
        self.inner
            .lock()
            .expect("substrate mutex poisoned")
            .dirty_area_names()
    }

    /// ACCELERATOR (block 184000) — droppable, byte-identical vectorized mirror
    /// of the 2-D retina's per-cell transduce+onset sheet. ONE FFI crossing does
    /// the whole sheet in O(cells): reuses the shared `photon_transduce_onset`
    /// kernel VERBATIM, mirrors `photon_apply_receptor_transduction` +
    /// `retinal_mint_onset_2d`, mints the same `RetinalOnsetEvent`s — no
    /// CognitiveTask nodes, no `run_rules` join. The adapter branches on
    /// `retina_accel`; OFF ⇒ the graph path runs as the correctness oracle.
    /// `perturb=true` injects a wrong mirror (fires every cell) so the
    /// byte-identity check is provably non-vacuous. NO new Term enum variant.
    ///
    /// DIRTY-INDEX (block 185000): `rod_ids`/`col_ids`/`payloads` are the WORK
    /// LIST (the cells that must be processed this tick), `cell_idx` maps them
    /// back to flat cell indices, `track_settled` returns the flat indices whose
    /// EXACT bitwise no-op predicate does NOT hold (so the adapter can re-present
    /// them next tick), `stamp_rod_ids` stamps `input_epoch` on the whole sheet,
    /// and `naive_skip` is the wrong-predicate falsifier. Omitting all of them is
    /// the byte-unchanged 184000 full sweep. Returns `(minted, unsettled)`.
    ///
    /// PER-SENSOR EPOCH (block 188000): `per_sensor_epoch=True` writes the rod's
    /// clock under its OWN key (`rod_epoch`) and advances it only when the rod's
    /// own state genuinely changed (the exact four-clause predicate). Default
    /// `False` ⇒ `input_epoch`, stamped unconditionally, byte-unchanged.
    #[pyo3(signature = (rod_ids, col_ids, payloads, epoch, threshold_db, refractory_epochs, perturb=false, cell_idx=None, track_settled=false, stamp_rod_ids=None, naive_skip=false, per_sensor_epoch=false))]
    #[allow(clippy::too_many_arguments)]
    fn retina_onset_batch(
        &mut self,
        py: Python<'_>,
        rod_ids: Vec<u32>,
        col_ids: Vec<u32>,
        payloads: Vec<Vec<f64>>,
        epoch: i64,
        threshold_db: f64,
        refractory_epochs: f64,
        perturb: bool,
        cell_idx: Option<Vec<u32>>,
        track_settled: bool,
        stamp_rod_ids: Option<Vec<u32>>,
        naive_skip: bool,
        per_sensor_epoch: bool,
    ) -> (usize, Vec<u32>) {
        crate::scale_audit::ffi(1, 0);
        py.allow_threads(|| {
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            crate::cognitive_tasks::retina_onset_batch(
                &mut guard,
                &rod_ids,
                &col_ids,
                payloads,
                epoch,
                threshold_db,
                refractory_epochs,
                perturb,
                cell_idx.as_deref(),
                track_settled,
                stamp_rod_ids.as_deref(),
                naive_skip,
                per_sensor_epoch,
            )
        })
    }

    /// GRAPH-NATIVE EVENT PATH (block 191000) — the event-consumer analogue of
    /// `retina_onset_batch`. ONE FFI crossing sweeps the whole `RetinalOnsetEvent`
    /// stream in Rust, builds the carve/motion/salience `CognitiveTask.payload`
    /// byte-identically to the old Python per-event loop, and mints the task node
    /// + its retina edge. The `run_rules` mint rules + kernels are UNCHANGED. This
    /// kills the O(events) per-event Python marshalling (`node(node)["attrs"]` per
    /// event, per stage, per frame). `dims` 2/3, `sort_mode` 0 spatial-first / 1
    /// epoch-first, `prefix` the per-stage payload header, `perturb` the wrong-read
    /// falsifier. NO new Term enum variant. Returns the minted task node id.
    #[pyo3(signature = (retina_id, edge_type, kind, marker_key, dims, sort_mode, prefix, input_epoch, logical_time, order, since_epoch=None, perturb=false))]
    #[allow(clippy::too_many_arguments)]
    fn retina_event_task_batch(
        &mut self,
        py: Python<'_>,
        retina_id: u32,
        edge_type: &str,
        kind: &str,
        marker_key: &str,
        dims: u8,
        sort_mode: u8,
        prefix: Vec<f64>,
        input_epoch: i64,
        logical_time: i64,
        order: i64,
        since_epoch: Option<f64>,
        perturb: bool,
    ) -> u32 {
        crate::scale_audit::ffi(1, 0);
        py.allow_threads(|| {
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            crate::cognitive_tasks::retina_event_task_batch(
                &mut guard,
                retina_id,
                edge_type,
                kind,
                marker_key,
                dims,
                sort_mode,
                &prefix,
                input_epoch,
                logical_time,
                order,
                since_epoch,
                perturb,
            )
        })
    }

    /// The clock-edge FOLD (the "tock"), graph-native — the engine's own conservative fold.
    /// The agent's correction PRODUCTION writes `next_<X>` attrs in-fixpoint (combinational:
    /// reads current, writes NEXT, never mutates its own inputs); this commits `next_<X> -> <X>`
    /// at the clock edge — the ONLY lawful home for the non-monotone down-stroke (a value going
    /// DOWN is impossible inside the monotone in-tick fixpoint; Tarski). A SEPARATE phase from
    /// `run_rules` so the next-state rule and the commit do not chase each other within one
    /// fixpoint (that interference IS the limit cycle). Opt-in: only nodes carrying `clocked == 1`
    /// are folded, so an operator self-tunes ONLY when wired to it (manually-folded proof scripts,
    /// which don't set `clocked`, are untouched). Returns the number of attrs committed.
    fn fold_clock_edge(&mut self) -> usize {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::cognitive_cycle::fold_clock_edge(inner)
    }

    /// Native EYE: segment the grid into connected-component Regions AND track identity
    /// across frames, updating persistent Region nodes in place. A faithful native port of
    /// the verified Python `WorldAdapter._perceive_regions` (the jabberwock's eye design):
    /// union-find CC per value, match each component to last frame's region by cell-overlap,
    /// inherit identity (drow/dcol/changed_frame/is_ground), ground membership conserved
    /// (add-only), figures re-point, birth/death. No per-cell Python FFI.
    /// values[r*w+c] = grid value; cell_ids[r*w+c] = that Cell node's id (.0). Row-major.
    ///
    /// THIN handoff: the algorithm itself now lives in
    /// `Substrate::segment_and_track` (moved there so `fb_sample` can
    /// reuse the exact same cross-frame identity machinery instead of
    /// duplicating it — see framebuffer.rs). This method only unlocks
    /// the mutex and forwards.
    fn segment(
        &mut self,
        game: pyo3::PyRef<'_, PyNodeID>,
        h: usize,
        w: usize,
        values: Vec<i32>,
        cell_ids: Vec<i64>,
    ) {
        let mut g = self.inner.lock().expect("substrate mutex poisoned");
        g.segment_and_track(game.to_node(), h, w, &values, &cell_ids);
    }

    /// MOTION-COMMON-FATE carve — the object-notion carve (block 144000). Thin
    /// handoff to `Substrate::segment_motion_and_track`: group the cells that
    /// MOVE TOGETHER (per-cell motion field `vy`/`vx`, one entry per grid cell
    /// row-major, computed by the caller's `vector_field` sensor) into Region
    /// components, static/dominant background as one, then track them through
    /// the SAME cross-frame identity machinery `segment` uses. ADDITIVE — the
    /// exact-value `segment` above is unchanged and remains the default.
    fn segment_motion(
        &mut self,
        game: pyo3::PyRef<'_, PyNodeID>,
        h: usize,
        w: usize,
        vy: Vec<f64>,
        vx: Vec<f64>,
        cell_ids: Vec<i64>,
    ) {
        let mut g = self.inner.lock().expect("substrate mutex poisoned");
        g.segment_motion_and_track(game.to_node(), h, w, &vy, &vx, &cell_ids);
    }

    // --- shared-memory framebuffer vision primitive --------------------
    //
    // "Live vision on shared memory": a POSIX shm object a writer thread
    // (browser CDP-screencast, built separately, out of scope here) keeps
    // fresh; the Rust runtime attaches once, then samples at its own tick
    // pace. Python's job is exactly `fb_attach` once + `fb_sample` per
    // tick — mechanical I/O, no perception decisions. See
    // `framebuffer.rs` for the wire contract and `Substrate::fb_sample`
    // for the sampling + segmentation handoff (reuses `segment_and_track`,
    // the same primitive `segment` uses).

    /// Attach a reader-only mapping to the POSIX shm object `shm_name`
    /// (e.g. `"/jbw_fb_3"`). Validates the 64-byte header (magic
    /// `0x4A425746` "JBWF", version 1, format 1=BGRA8888, stride >=
    /// width*4) and that the object is large enough for its declared
    /// payload. Raises `ValueError` with the precise validation failure
    /// on a bad/missing shm object; on success returns the `fb_id`
    /// later calls address this framebuffer by.
    fn fb_attach(&mut self, shm_name: &str) -> PyResult<u32> {
        let mut g = self.inner.lock().expect("substrate mutex poisoned");
        g.fb_attach(shm_name).map_err(PyValueError::new_err)
    }

    /// Detach the mapping for `fb_id`. Returns False if `fb_id` wasn't
    /// attached (already detached, or never valid) — mirrors
    /// dict.pop-with-default semantics rather than raising, since
    /// "detach something already gone" is a harmless no-op for a
    /// caller doing cleanup.
    fn fb_detach(&mut self, fb_id: u32) -> bool {
        let mut g = self.inner.lock().expect("substrate mutex poisoned");
        g.fb_detach(fb_id)
    }

    /// Sample the CURRENT frame of `fb_id`, quantize it to a
    /// `grid_w x grid_h` value grid, and run the SAME segmentation +
    /// cross-frame identity tracking `segment` uses for `game` —
    /// minting/reusing the grid's own Cell/`WorldInstance` nodes (a
    /// live framebuffer has no separately-ingested world graph the way
    /// ARC's ingest pipeline does, so this method mints them itself,
    /// first call; later calls at the same `grid_w`/`grid_h`/`game`
    /// reuse + update them in place).
    ///
    /// Fast-paths to `{"unchanged": True, "frame_seq": N, ...}` without
    /// re-segmenting when the framebuffer's `frame_seq` hasn't advanced
    /// since the last `fb_sample` call for this `fb_id` — the writer
    /// hasn't produced a new frame, so there's nothing new to perceive.
    /// Otherwise returns `{"unchanged": False, "frame_seq": N,
    /// "torn": bool, "grid_w": int, "grid_h": int}` — `torn` is True
    /// only if the bounded seqlock retry was exhausted while the writer
    /// kept racing ahead (the frame was still used; this is vision, not
    /// banking).
    fn fb_sample<'py>(
        &mut self,
        py: Python<'py>,
        fb_id: u32,
        game: pyo3::PyRef<'_, PyNodeID>,
        grid_w: usize,
        grid_h: usize,
    ) -> PyResult<Bound<'py, PyDict>> {
        let result = {
            let mut g = self.inner.lock().expect("substrate mutex poisoned");
            g.fb_sample(fb_id, game.to_node(), grid_w, grid_h)
                .map_err(PyValueError::new_err)?
        };
        let d = PyDict::new_bound(py);
        d.set_item("fb_id", result.fb_id)?;
        d.set_item("frame_seq", result.frame_seq)?;
        d.set_item("unchanged", result.unchanged)?;
        d.set_item("torn", result.torn)?;
        d.set_item("grid_w", result.grid_w)?;
        d.set_item("grid_h", result.grid_h)?;
        Ok(d)
    }

    // --- GRAPH LAW #6: domain-general trans-frame identity -------------
    //
    // "Same thing across frames" generalised past `segment_and_track`'s
    // pixel/centroid domain (that stays exactly as-is; it's the visual
    // eye's own dependency) — see `Substrate::track_identity` /
    // `crate::term::track_identity_correspondence` for the shared
    // matching algorithm (overlap-first, nearest-feature-vector
    // fallback within `radius`, greedy, birth/death). Any two node sets
    // carrying a `feature_key` attr readable as a number-vector can be
    // matched — not just grid regions.

    /// Match `cur_ids` against `prev_ids` by feature-vector (+ optional
    /// extent-overlap) correspondence, writing `identity_key` onto
    /// every `cur` node so it PERSISTS the matched `prev` node's
    /// identity (or mints a fresh globally-unique one on birth).
    /// `category_key` (a discrete equality gate) and `extent_key` (an
    /// overlap-first pass over a Set/Tuple attr) are optional — `None`
    /// skips that gate/pass entirely, falling straight to
    /// nearest-feature-vector-within-`radius`. Returns `{"matched":
    /// [(prev_id, cur_id), ...], "births": [cur_id, ...], "deaths":
    /// [prev_id, ...]}` as `NodeID` objects (like `wire_relation`'s
    /// return shape), so the result composes directly with `.node()`/
    /// `.set_attr()`/etc. without a caller re-wrapping ints.
    #[pyo3(signature = (prev_ids, cur_ids, feature_key, identity_key, radius, category_key=None, extent_key=None))]
    fn track_identity<'py>(
        &mut self,
        py: Python<'py>,
        prev_ids: Vec<PyRef<'_, PyNodeID>>,
        cur_ids: Vec<PyRef<'_, PyNodeID>>,
        feature_key: &str,
        identity_key: &str,
        radius: f64,
        category_key: Option<&str>,
        extent_key: Option<&str>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let prev: Vec<NodeID> = prev_ids.iter().map(|n| n.to_node()).collect();
        let cur: Vec<NodeID> = cur_ids.iter().map(|n| n.to_node()).collect();
        let result = {
            let mut g = self.inner.lock().expect("substrate mutex poisoned");
            let feature_sym = g.interner.intern(feature_key);
            let identity_sym = g.interner.intern(identity_key);
            let category_sym = category_key.map(|s| g.interner.intern(s));
            let extent_sym = extent_key.map(|s| g.interner.intern(s));
            g.track_identity(
                &prev,
                &cur,
                feature_sym,
                category_sym,
                extent_sym,
                identity_sym,
                radius,
            )
        };
        let d = PyDict::new_bound(py);
        // Returns `NodeID` objects (not bare ints) — like `wire_relation`/
        // `wire_relation_affect` — so a caller can pass a result straight
        // back into `.node()`/`.set_attr()`/etc. without re-wrapping.
        // `Py::new` (not a bare `PyNodeID`) since `PyDict::set_item` needs
        // `ToPyObject`, which a raw pyclass struct doesn't implement --
        // only its GIL-allocated `Py<T>` handle does.
        let mut matched: Vec<(Py<PyNodeID>, Py<PyNodeID>)> =
            Vec::with_capacity(result.matched.len());
        for (p, c) in &result.matched {
            matched.push((
                Py::new(py, PyNodeID::from_node(*p))?,
                Py::new(py, PyNodeID::from_node(*c))?,
            ));
        }
        let mut births: Vec<Py<PyNodeID>> = Vec::with_capacity(result.births.len());
        for n in &result.births {
            births.push(Py::new(py, PyNodeID::from_node(*n))?);
        }
        let mut deaths: Vec<Py<PyNodeID>> = Vec::with_capacity(result.deaths.len());
        for n in &result.deaths {
            deaths.push(Py::new(py, PyNodeID::from_node(*n))?);
        }
        d.set_item("matched", matched)?;
        d.set_item("births", births)?;
        d.set_item("deaths", deaths)?;
        Ok(d)
    }

    /// N-dimensional, body-conditional, foveated quantization over the
    /// observation belief (FLOOD_DESIGN.md Part A — `space_quantize.rs`).
    /// THIN handoff: this method only converts Python args into
    /// `space_quantize::QuantizeParams`, calls the core-module primitive,
    /// and renders the returned summary as a dict. The algorithm itself —
    /// belief read, body erosion, maximal-box decomposition, incremental
    /// reuse/split, portals, frontier minting — lives entirely in
    /// `space_quantize.rs`, per CLAUDE.md's "primitive in Rust, composition
    /// in graph" split (this is the fix for the `slide_flood` binding-layer
    /// violation at this file's line ~2172, not a repeat of it).
    ///
    /// Exactly one of `body_extents` (a rigid axis-aligned box, anchored at
    /// its lowest corner — generalises `slide_flood`'s `fp_h`x`fp_w`) or
    /// `body_offsets` (an explicit N-dim offset set, for non-rectangular
    /// bodies) must be given; if neither is given, defaults to a 1x1x..x1
    /// unit body. `focus_lo`/`focus_hi`/`passable_values`/`min_extent` are
    /// all length-`space_ndim`, except `passable_values` which is the set
    /// of `value` attrs the erosion treats as passable (any length).
    ///
    /// Returns `{"quanta": int, "portals": int, "frontiers": int,
    /// "reused": int, "split": int}`.
    /// Feasible-set selection over a candidate family — a one-line handoff to
    /// `future_manifold::feasible_selection`. The decision rule, the set-tie and
    /// every fail-closed condition live in Rust; this only marshals node ids and
    /// hands the record back as a dict.
    fn feasible_selection<'py>(
        &mut self,
        py: Python<'py>,
        episode: PyRef<'_, PyNodeID>,
        policy: PyRef<'_, PyNodeID>,
        candidates: Vec<PyRef<'_, PyNodeID>>,
    ) -> PyResult<Option<Bound<'py, PyDict>>> {
        let cands: Vec<NodeID> = candidates.iter().map(|c| NodeID(c.value)).collect();
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *guard;
        let Some(sel) = crate::future_manifold::feasible_selection(
            &inner.graph,
            &mut inner.interner,
            NodeID(episode.value),
            NodeID(policy.value),
            &cands,
        ) else {
            return Ok(None);
        };
        let ids = |v: &[NodeID]| -> Vec<u32> { v.iter().map(|n| n.0).collect() };
        let out = PyDict::new_bound(py);
        out.set_item("unestablished", ids(&sel.unestablished))?;
        out.set_item("infeasible", ids(&sel.infeasible))?;
        out.set_item("feasible", ids(&sel.feasible))?;
        out.set_item("minimal", ids(&sel.minimal))?;
        out.set_item("selected", ids(&sel.selected))?;
        out.set_item("withheld_minimal", ids(&sel.withheld_minimal))?;
        out.set_item("tie_breadth", sel.tie_breadth)?;
        Ok(Some(out))
    }

    #[pyo3(signature = (
        game, space_ndim, body_key, passable_values, focus_lo, focus_hi, epoch,
        body_extents=None, body_offsets=None, min_extent=None
    ))]
    fn space_quantize<'py>(
        &mut self,
        py: Python<'py>,
        game: u32,
        space_ndim: usize,
        body_key: &str,
        passable_values: Vec<i64>,
        focus_lo: Vec<i64>,
        focus_hi: Vec<i64>,
        epoch: i64,
        body_extents: Option<Vec<i64>>,
        body_offsets: Option<Vec<Vec<i64>>>,
        min_extent: Option<Vec<i64>>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let body = match (body_extents, body_offsets) {
            (Some(e), None) => crate::space_quantize::BodySpec::Extents(e),
            (None, Some(o)) => crate::space_quantize::BodySpec::Offsets(o),
            (None, None) => crate::space_quantize::BodySpec::Extents(vec![1; space_ndim]),
            (Some(_), Some(_)) => {
                return Err(PyValueError::new_err(
                    "space_quantize: pass only one of body_extents / body_offsets",
                ))
            }
        };
        let min_extent = min_extent.unwrap_or_else(|| vec![1; space_ndim]);
        let params = crate::space_quantize::QuantizeParams {
            game: NodeID(game),
            ndim: space_ndim,
            body_key: body_key.to_string(),
            body,
            passable_values,
            focus_lo,
            focus_hi,
            epoch,
            min_extent,
        };
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let summary =
            crate::space_quantize::space_quantize(inner, params).map_err(PyValueError::new_err)?;
        let d = PyDict::new_bound(py);
        d.set_item("quanta", summary.quanta)?;
        d.set_item("portals", summary.portals)?;
        d.set_item("frontiers", summary.frontiers)?;
        d.set_item("reused", summary.reused)?;
        d.set_item("split", summary.split)?;
        Ok(d)
    }

    /// FAST serve path for a reflex net — the direct native forward pass.
    /// Bypasses the generic `evaluate()` term-parse (`pyobj_to_json` +
    /// `term_from_json` + arena alloc + value marshalling) that dominates
    /// per-call cost for small nets: hand the assemblage node id + input
    /// vector straight to `net_forward::net_forward_core`. A THIN handoff
    /// (cf. `space_quantize`) — the algorithm lives entirely in
    /// `net_forward.rs`; this only locks, resolves the node id, and returns
    /// the output vector. Used by a world adapter serving reflex-net
    /// answers in a hot loop; rules still compose the `NetForward` Term.
    fn net_forward(&self, assemblage: u32, inputs: Vec<f64>) -> Vec<f64> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::net_forward::net_forward_core(
            &inner.graph,
            &inner.interner,
            NodeID(assemblage),
            inputs,
        )
    }

    /// BATCH reflex-net serve path. Graph-resident tensors are loaded once,
    /// then reused for every row in caller order. This is scalar
    /// `net_forward` semantics with one FFI crossing and one weight load.
    fn net_forward_batch(&self, assemblage: u32, inputs: Vec<Vec<f64>>) -> Vec<Vec<f64>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::net_forward::net_forward_batch_core(
            &inner.graph,
            &inner.interner,
            NodeID(assemblage),
            &inputs,
        )
    }

    /// CASCADE forward — the sum of a residual-cascade net's block
    /// `NetForward`s (an additive ensemble; depth by refinement). Read-only.
    fn cascade_forward(&self, cascade: u32, input: Vec<f64>) -> Vec<f64> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::net_forward::cascade_forward(&inner.graph, &inner.interner, NodeID(cascade), input)
    }

    /// CASCADE collapse step — the new net type trains ITSELF: each block
    /// learns (local delta rule) the SURPRISE the previous block left, the
    /// residual passed up the stack. No backprop, online, per-observation.
    /// Returns the final residual magnitude Σr² (falls as depth/training
    /// grow). Mutates the blocks' weights in place.
    fn cascade_collapse_step(
        &self,
        cascade: u32,
        input: Vec<f64>,
        target: Vec<f64>,
        eta: f64,
    ) -> f64 {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let SubstrateRs {
            graph, interner, ..
        } = &mut *inner;
        crate::net_forward::cascade_collapse_step(
            graph,
            interner,
            NodeID(cascade),
            &input,
            &target,
            eta,
        )
    }

    /// COMPOSITE forward — a net nested out of component SHAPE specialists.
    /// Routes the input to the component covering the most of its shape
    /// (`sig_keys` matched against each component's `basin_parts`), evaluates
    /// that component's `NetForward`, and returns `(output, chosen_component,
    /// residual_fraction)`. An empty output + component `-1` means NO
    /// component covers the input's shape — the composite defers to cognition.
    /// A thin handoff to `net_forward::composite_forward` (cf. `net_forward`);
    /// the routing is grounded shape-residual, never a trained gate.
    fn composite_forward(
        &self,
        composite: u32,
        input: Vec<f64>,
        sig_keys: Vec<String>,
    ) -> (Vec<f64>, i64, f64) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::net_forward::composite_forward(
            &inner.graph,
            &inner.interner,
            NodeID(composite),
            input,
            sig_keys,
        )
    }

    /// One SURPRISE-DRIVEN COLLAPSE step — the reflex net trains ITSELF.
    /// The net predicts, computes its surprise (target − prediction), and
    /// collapses its readout weights toward reducing it (local delta rule;
    /// `net_forward.rs::net_collapse_step`). Mutates the net's `WeightTensor`
    /// data in place; returns the surprise magnitude `Σ e²`, which falls
    /// toward 0 as the net learns. A world adapter feeds one observed
    /// (input, target) pair per call (mechanical — the DECISION to train is
    /// a rule); over observations the net self-trains online, no external
    /// optimizer. This is "collapse and surprise within the net."
    fn net_collapse_step(
        &self,
        assemblage: u32,
        inputs: Vec<f64>,
        target: Vec<f64>,
        eta: f64,
    ) -> f64 {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let SubstrateRs {
            graph, interner, ..
        } = &mut *inner;
        crate::net_forward::net_collapse_step(
            graph,
            interner,
            NodeID(assemblage),
            &inputs,
            &target,
            eta,
        )
    }

    /// Ordered BATCH self-training. Row i+1 sees row i's local-delta update,
    /// exactly like sequential `net_collapse_step` calls; final graph weights
    /// are published once. Inputs and targets must have one row each.
    fn net_collapse_batch_ordered(
        &self,
        assemblage: u32,
        inputs: Vec<Vec<f64>>,
        targets: Vec<Vec<f64>>,
        eta: f64,
    ) -> PyResult<Vec<f64>> {
        if inputs.len() != targets.len() {
            return Err(PyValueError::new_err(format!(
                "net_collapse_batch_ordered: {} input rows but {} target rows",
                inputs.len(),
                targets.len(),
            )));
        }
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let SubstrateRs {
            graph, interner, ..
        } = &mut *inner;
        Ok(crate::net_forward::net_collapse_batch_ordered(
            graph,
            interner,
            NodeID(assemblage),
            &inputs,
            &targets,
            eta,
        ))
    }

    /// One agent tick — apply every graph-resident Rule node to
    /// fixed point. Replaces the Python `graph_rewrite.run` driver
    /// per the unified-runtime architecture (CLAUDE.md): rule
    /// matching + effect application move into Rust; Python only
    /// constructs the Rule nodes at seed time and triggers ticks
    /// from world adapters.
    ///
    /// Walks every `Rule`-typed node, parses its `match` / `where` /
    /// `effect` attrs into native `RewriteRule` structs (using a
    /// fresh per-tick TermArena so the substrate's permanent arena
    /// doesn't accumulate duplicates), then dispatches via the
    /// existing `rewrite::run_rules` engine. Returns the number of
    /// rule applications that progressed the graph before fixed
    /// point.
    ///
    /// Per the prose-rule compiler integration: after walking Rule
    /// nodes, also fires the RewriteRule store (substrate.rules).
    /// add_rule() populates that store; without this bridge, rules
    /// added through add_rule fire only via run_rules() but not via
    /// tick() — an asymmetry that violated the docstring claim of
    /// 'every graph-resident Rule node to fixed point.'
    /// `detect_cycles` (default False) — PROTOCOL §9: OFF by default, so
    /// every committed result reproduces byte-identically and no seed that
    /// does not ask for it can move.
    ///
    /// When True, the fixpoint additionally terminates on a REPEATED GRAPH
    /// STATE. `run_rules` otherwise offers exactly one termination
    /// semantics — run to an EXACT fixed point — and exact equality is
    /// UNSATISFIABLE over float arithmetic that dithers: a contraction's
    /// fixed point is generically not representable in float64, so the
    /// iteration lands in a period-2 orbit between the two nearest floats
    /// and burns the cap forever on a sheet that has already settled to
    /// 1e-16. A period-2 orbit IS a fixed point of the 2-step map, and a
    /// repeated state under a deterministic map proves nothing new can be
    /// reached. This needs exact equality against history and NO TOLERANCE
    /// — so it introduces no epsilon and no magic number (PROTOCOL §13).
    #[pyo3(signature = (max_steps=100_000, detect_cycles=false))]
    fn tick(&mut self, max_steps: usize, detect_cycles: bool) -> usize {
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch();
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::cognitive_cycle::advance_cognitive_epoch(inner);
        crate::cognitive_cycle::execute(
            inner,
            crate::cognitive_cycle::CyclePlan::Default,
            max_steps,
            detect_cycles,
            false,
            1,
        )
        .steps
    }

    /// Execute one explicit native phase plan. This is the migration seam for
    /// the historically different tick paths; it does not silently unify them.
    #[pyo3(signature = (plan, max_steps=100_000, detect_cycles=false, trace=false, n_workers=None))]
    fn run_cycle<'py>(
        &mut self,
        py: Python<'py>,
        plan: &str,
        max_steps: usize,
        detect_cycles: bool,
        trace: bool,
        n_workers: Option<usize>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let plan = crate::cognitive_cycle::CyclePlan::parse(plan)
            .ok_or_else(|| PyValueError::new_err(format!("unknown cycle plan: {plan}")))?;
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch();
        let n_workers = crate::cognitive_tasks::resolve_worker_capacity(n_workers);
        let synchronous_system_two_tasks = matches!(
            plan,
            crate::cognitive_cycle::CyclePlan::Default
                | crate::cognitive_cycle::CyclePlan::DualProcess
        );
        let (mut report, prepared) = py.allow_threads(|| {
            let mut guard = self.inner.lock().expect("substrate mutex poisoned");
            crate::cognitive_cycle::advance_cognitive_epoch(&mut guard);
            let report = crate::cognitive_cycle::execute(
                &mut *guard,
                plan,
                max_steps,
                detect_cycles,
                trace,
                n_workers,
            );
            let prepared = synchronous_system_two_tasks.then(|| {
                crate::cognitive_tasks::prepare_requested_class(
                    &mut guard,
                    n_workers.max(1),
                    "system_two",
                )
            });
            (report, prepared)
        });
        if let Some(prepared) = prepared {
            // Preserve the explicit cycle's synchronous API while releasing
            // the live-graph mutex for graph-authored pure System-2 work.
            // Other task classes remain untouched by this compatibility seam.
            let completed = py.allow_threads(|| crate::cognitive_tasks::execute_prepared(prepared));
            let (summary, followup) = py.allow_threads(|| {
                let mut guard = self.inner.lock().expect("substrate mutex poisoned");
                let summary = crate::cognitive_tasks::fold_completed(&mut guard, completed);
                let followup = if summary.requested > 0 {
                    let remaining = max_steps.saturating_sub(report.steps);
                    if remaining > 0 {
                        Some(crate::cognitive_cycle::execute(
                            &mut guard,
                            plan,
                            remaining,
                            detect_cycles,
                            trace,
                            n_workers,
                        ))
                    } else {
                        None
                    }
                } else {
                    None
                };
                (summary, followup)
            });
            if summary.requested > 0 {
                report.task_summary = Some(summary);
                if let Some(mut followup) = followup {
                    report.steps = report.steps.saturating_add(followup.steps);
                    report.clock_commits =
                        report.clock_commits.saturating_add(followup.clock_commits);
                    report.needs_reflex_dispatch |= followup.needs_reflex_dispatch;
                    report.needs_thread_dispatch |= followup.needs_thread_dispatch;
                    report.needs_result_fold |= followup.needs_result_fold;
                    report.needs_system_two |= followup.needs_system_two;
                    report.system_one_commits = report
                        .system_one_commits
                        .saturating_add(followup.system_one_commits);
                    report.system_two_escalations = report
                        .system_two_escalations
                        .saturating_add(followup.system_two_escalations);
                    report.system_two_stale = report
                        .system_two_stale
                        .saturating_add(followup.system_two_stale);
                    report.system_two_lease_blocked = report
                        .system_two_lease_blocked
                        .saturating_add(followup.system_two_lease_blocked);
                    report.system_two_steps = report
                        .system_two_steps
                        .saturating_add(followup.system_two_steps);
                    let offset = report.trace.len();
                    for (index, event) in followup.trace.iter_mut().enumerate() {
                        event.sequence = offset + index;
                    }
                    report.trace.extend(followup.trace);
                }
            }
        }
        let out = PyDict::new_bound(py);
        out.set_item("steps", report.steps)?;
        out.set_item("clock_commits", report.clock_commits)?;
        out.set_item("needs_reflex_dispatch", report.needs_reflex_dispatch)?;
        out.set_item("reflexes_fired", report.reflexes_fired)?;
        out.set_item("needs_thread_dispatch", report.needs_thread_dispatch)?;
        out.set_item("needs_result_fold", report.needs_result_fold)?;
        out.set_item("needs_system_two", report.needs_system_two)?;
        out.set_item("system_one_commits", report.system_one_commits)?;
        out.set_item("system_two_escalations", report.system_two_escalations)?;
        out.set_item("system_two_stale", report.system_two_stale)?;
        out.set_item("system_two_lease_blocked", report.system_two_lease_blocked)?;
        out.set_item("system_two_steps", report.system_two_steps)?;
        if let Some(tasks) = &report.task_summary {
            out.set_item("tasks_requested", tasks.requested)?;
            out.set_item("tasks_completed", tasks.completed)?;
            out.set_item("tasks_failed", tasks.failed)?;
            out.set_item("tasks_stale", tasks.stale)?;
            out.set_item("task_workers_used", tasks.workers_used)?;
            out.set_item("task_wall_micros", tasks.wall_micros)?;
        }
        let events: Vec<(usize, &str, usize, Option<u64>)> = report
            .trace
            .iter()
            .map(|e| (e.sequence, e.phase, e.progressed, e.fingerprint))
            .collect();
        out.set_item("trace", events)?;
        Ok(out)
    }

    /// Read-only shadow schedule: semantic areas, dependencies and SCCs.
    /// It does not alter rule execution; area-serial parity is established
    /// before any asynchronous cutover.
    fn area_schedule<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let guard = self.inner.lock().expect("substrate mutex poisoned");
        let schedule = crate::area_scheduler::derive(&guard.rules);
        let areas: Vec<J> = schedule
            .areas
            .iter()
            .map(|a| {
                serde_json::json!({
                    "area": if a.area == Sym::default() {
                        "global"
                    } else {
                        guard.interner.resolve(a.area)
                    },
                    "rules": a.rule_indices,
                })
            })
            .collect();
        let dependencies: Vec<J> = schedule
            .dependencies
            .iter()
            .map(|(a, b)| serde_json::json!([a, b]))
            .collect();
        let components: Vec<J> = schedule
            .components
            .iter()
            .map(|c| serde_json::json!(c))
            .collect();
        json_to_pyobj(
            py,
            &serde_json::json!({
                "areas": areas,
                "dependencies": dependencies,
                "components": components,
            }),
        )
    }

    /// Execute every graph-requested pure CognitiveTask on native workers,
    /// then commit TaskResult nodes in deterministic logical order.
    #[pyo3(signature = (n_workers=None))]
    fn run_cognitive_tasks<'py>(
        &mut self,
        py: Python<'py>,
        n_workers: Option<usize>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        crate::cognitive_cycle::advance_cognitive_epoch(&mut guard);
        let summary = crate::cognitive_tasks::run_requested(
            &mut guard,
            crate::cognitive_tasks::resolve_worker_capacity(n_workers),
        );
        let out = PyDict::new_bound(py);
        out.set_item("requested", summary.requested)?;
        out.set_item("completed", summary.completed)?;
        out.set_item("failed", summary.failed)?;
        out.set_item("stale", summary.stale)?;
        out.set_item("workers_used", summary.workers_used)?;
        out.set_item("wall_micros", summary.wall_micros)?;
        Ok(out)
    }

    /// Return and stamp the next ready order-0 reflex. The caller enacts the
    /// named external response, then calls again so callback mutations remain
    /// visible to later reflex stimuli in the same logical tick.
    fn next_ready_reflex(
        &mut self,
        agent: u32,
        now: i64,
        ordered: Vec<u32>,
        excluded: Vec<u32>,
    ) -> Option<(u32, String, String)> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let ordered: Vec<NodeID> = ordered.into_iter().map(NodeID).collect();
        let excluded: rustc_hash::FxHashSet<NodeID> = excluded.into_iter().map(NodeID).collect();
        crate::reflex_runtime::next_ready(&mut guard, NodeID(agent), now, &ordered, &excluded)
            .map(|dispatch| (dispatch.node.0, dispatch.name, dispatch.response))
    }

    /// ADMISSIBLE VECTORIZED STENCIL FAST PATH (block 134000,
    /// `VISION_STENCIL_SIMD_PREREG.md`). Replaces the per-cell wave-relaxation
    /// rule matching with a single vectorized pass over the contiguous field —
    /// the EXACT VECTORIZATION scale lever 133000 named for a KNOWN local rule.
    ///
    /// Returns True iff the fast path was ADMISSIBLE and applied (⇒ the caller
    /// must NOT also call `tick`); False iff inadmissible (⇒ the caller falls
    /// back to `tick`). Admissibility is a STRUCTURAL property read from the
    /// graph: the RetinaCell dynamics must be the recognised uniform radius-1
    /// stencil (its three rules' `where`/`effect` ASTs matched — NOT by name),
    /// and no non-stencil rule may read/write the CA's outputs. A learner-laden
    /// graph (Unit/Synapse) or any altered rule set is inadmissible and left to
    /// the general per-cell path — so this COMPOSES and the committed path is
    /// byte-unchanged (PROTOCOL §9).
    ///
    /// BYTE-IDENTITY (§9, non-negotiable): the vectorized state is bit-for-bit
    /// what the rules produce (`scripts/_scratch_ca_verify.py`'s proven
    /// `ca_tick`); gated by `tests/test_stencil_simd_migrated.py` over
    /// multi-tick runs. `run_rest=True` (default, SAFE) runs every NON-wave rule
    /// exactly as `tick` would; `run_rest=False` applies only the stencil (valid
    /// for the pure wave field, where the gate certifies the rest cannot fire).
    #[pyo3(signature = (max_steps=200_000, run_rest=true))]
    fn wave_stencil_tick(&mut self, max_steps: usize, run_rest: bool) -> bool {
        crate::scale_audit::ffi(1, 0);
        crate::scale_audit::begin_epoch();
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::wave_stencil::stencil_tick(inner, max_steps, run_rest)
    }

    /// Graph-resident backtracking search (DFS with undo) — the native form of
    /// the old Python `graph_rewrite.search_count` / `search_sum`. The strategy
    /// is graph-resident Terms: `open` yields the undecided items; for the
    /// lowest-id open item the search adds `assign_edge` to each `options`
    /// candidate, recurses, then undoes. `fail` prunes a violated constraint;
    /// `accept` gates a complete leaf. With `value` None it COUNTS solutions;
    /// with `value` set it SUMS that Term over solution leaves (e.g. the signed
    /// product behind a determinant). `env` pre-binds free vars (anchors, the
    /// matrix node, …). Returns an int when the result is integral, else a float.
    #[pyo3(signature = (open, options, assign_edge, fail=None, value=None, accept=None, env=None))]
    fn search<'py>(
        &mut self,
        py: Python<'py>,
        open: &Bound<'_, PyAny>,
        options: &Bound<'_, PyAny>,
        assign_edge: &str,
        fail: Option<&Bound<'_, PyAny>>,
        value: Option<&Bound<'_, PyAny>>,
        accept: Option<&Bound<'_, PyAny>>,
        env: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let snapshot = inner.terms.nodes.len();
        let open_idx = {
            let j = pyobj_to_json_term(py, open, WireMode::Structural)?;
            term_from_json(&j, &mut inner.terms, &mut inner.interner)
                .map_err(|e| PyValueError::new_err(format!("bad open Term: {:?}", e)))?
        };
        let options_idx = {
            let j = pyobj_to_json_term(py, options, WireMode::Structural)?;
            term_from_json(&j, &mut inner.terms, &mut inner.interner)
                .map_err(|e| PyValueError::new_err(format!("bad options Term: {:?}", e)))?
        };
        let mut opt_idx =
            |t: Option<&Bound<'_, PyAny>>, label: &str| -> PyResult<Option<TermIdx>> {
                match t {
                    None => Ok(None),
                    Some(b) => {
                        let j = pyobj_to_json_term(py, b, WireMode::Structural)?;
                        Ok(Some(
                            term_from_json(&j, &mut inner.terms, &mut inner.interner).map_err(
                                |e| PyValueError::new_err(format!("bad {} Term: {:?}", label, e)),
                            )?,
                        ))
                    }
                }
            };
        let fail_idx = opt_idx(fail, "fail")?;
        let value_idx = opt_idx(value, "value")?;
        let accept_idx = opt_idx(accept, "accept")?;
        let assign_sym = inner.interner.intern(assign_edge);
        let env_v = pydict_to_env(py, env, &mut inner.interner)?;
        let result = search_recurse(
            inner,
            open_idx,
            options_idx,
            assign_sym,
            fail_idx,
            value_idx,
            accept_idx,
            &env_v,
        );
        inner.terms.nodes.truncate(snapshot);
        let v = if result.fract() == 0.0 && result.abs() < 9e15 {
            Value::Int(result as i64)
        } else {
            Value::Float(result)
        };
        value_to_py(py, &v, &inner.interner)
    }

    /// Install the universal codec field-grammar Rules (decode +
    /// encode + skip + loop machinery) on this substrate. After
    /// calling this once, any FieldSpec chain you seed (H.264 PPS,
    /// HEVC SPS, JPEG DQT, ...) is walked by the same Rule set.
    /// Returns the number of rules installed. The Rules live in the
    /// runner crate (`src/codec.rs` + `codec_field_grammar_rules
    /// .json`) so callers don't repeat the ~600-line Rule construction.
    fn install_field_grammar_rules(&mut self) -> PyResult<usize> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        crate::codec::install_field_grammar_rules(&mut *inner).map_err(PyValueError::new_err)
    }

    /// Number of rule SLOTS, i.e. the index space `add_rule` hands out
    /// (`0..rule_count()`). Includes rules retracted via `remove_rule` —
    /// those are tombstoned in place, not compacted out, so a returned
    /// `RuleIdx` always stays valid to pass back to `remove_rule` /
    /// `apply_rule_once` even after other rules are removed. This is
    /// therefore the count of installed-ever rules, not live/active ones.
    fn rule_count(&self) -> usize {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.rules.len()
    }

    /// Retract a rule installed by `add_rule`: it stops matching/firing in
    /// `apply_rule_once` / `run_rules` / `tick`. The slot is TOMBSTONED,
    /// not removed — `rule_idx` values stay stable (no reuse, no
    /// reindexing of other rules); `rule_count()` still counts it. Returns
    /// `True` iff a previously-active rule was deactivated; `False` for an
    /// out-of-range index or a rule that was already removed (safe to
    /// call twice).
    fn remove_rule(&mut self, rule_idx: u32) -> bool {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.remove_rule(crate::rewrite::RuleIdx(rule_idx))
    }

    /// Serialise every slot in the `add_rule` rule store — including
    /// tombstoned (inactive) ones — to the SAME dict dialect `add_rule`
    /// accepts, plus an `"active"` bool per entry. This is the checkpoint
    /// counterpart of `add_rule`: `graph_to_dict` / `grammar_to_json`
    /// persist the graph and the Γ grammar, but neither persists this
    /// store (rules installed via `add_rule` — including everything a
    /// seed loader or a self-authoring agent installs at runtime), which
    /// is why a save/load cycle used to come back with `rule_count() ==
    /// 0`. Order is preserved (list index `i` == `RuleIdx(i)`), so
    /// `import_rules` can reproduce identical indices by replaying
    /// `add_rule` in the same order. Every `RewriteRule` field round-trips
    /// through the existing `parse_rule_json` wire dialect (match edges,
    /// `where` via `jsonio::term_to_json` — which covers the full `TermNode`
    /// enum exhaustively, so no Term variant is silently dropped — and
    /// effects via the same array-encoding `parse_effect_json` reads), so
    /// there is currently no rule shape that fails to round-trip; if a
    /// future `Effect`/`TermNode` variant is added without a matching arm
    /// here, this is a compile error (the match is exhaustive), not a
    /// silent drop.
    fn export_rules<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let arr: Vec<J> = inner
            .rules
            .iter()
            .map(|r| rule_to_json(r, &inner.terms, &inner.interner))
            .collect();
        json_to_pyobj(py, &J::Array(arr))
    }

    /// Inverse of `export_rules`: reinstall a rule store captured by it,
    /// replaying `add_rule` in list order so `RuleIdx(i)` for entry `i`
    /// matches the exported index exactly, then calling `remove_rule` on
    /// any entry whose `"active"` was `false` so tombstoned slots come
    /// back tombstoned (indices of every OTHER rule are unaffected by a
    /// `remove_rule` call — it only flips a flag on its own slot).
    ///
    /// Requires the rule store to be empty (true of a freshly constructed
    /// `Substrate`, which is what `WorldAdapter.load` builds before calling
    /// this): reinstalling on top of existing rules would shift every
    /// `RuleIdx` a caller might already hold, silently corrupting indices
    /// rather than reproducing them — so this raises instead.
    fn import_rules(&mut self, py: Python<'_>, rules: &Bound<'_, PyAny>) -> PyResult<usize> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        if !inner.rules.is_empty() {
            return Err(PyValueError::new_err(
                "import_rules: substrate already has rules installed — the rule \
                 store must be empty so RuleIdx slots line up with the export \
                 (call this right after graph_from_dict on a fresh Substrate)",
            ));
        }
        let json = pyobj_to_json(py, rules)?;
        let arr = json
            .as_array()
            .ok_or_else(|| PyValueError::new_err("import_rules: expected a list"))?;
        for (i, rule_json) in arr.iter().enumerate() {
            let rule = parse_rule_json(rule_json, &mut inner.terms, &mut inner.interner)
                .map_err(|e| PyValueError::new_err(format!("import_rules: rule {}: {}", i, e)))?;
            let active = rule_json
                .get("active")
                .and_then(|v| v.as_bool())
                .unwrap_or(true);
            let idx = inner.add_rule(rule);
            debug_assert_eq!(
                idx.0 as usize, i,
                "import_rules: index drift from export order"
            );
            if !active {
                inner.remove_rule(idx);
            }
        }
        Ok(inner.rules.len())
    }

    // --- CABAC primitive prototype ---------------------------------
    // The H.264 entropy-coding engine, exposed as a low-level
    // operation: encode/decode one bin under either a context (with
    // adaptive probability) or in bypass mode (1/2 probability).
    // The H.264 context MODEL (~460 contexts with codec-specific
    // initialization) lives above; this primitive is the universal
    // arithmetic engine shared by H.264 and AV1's similar coder.

    /// Round-trip a bit sequence through the CABAC encoder+decoder.
    /// Each bin is `(ctx_p_state_idx, ctx_val_mps, bin_val, is_bypass)`.
    /// Returns (encoded_bytes, decoded_bin_sequence). Intended for
    /// integration smoke tests; production users would call
    /// encode_bins / decode_bins separately.
    /// Initialise the 1024 H.264 CABAC contexts for a slice with the
    /// given slice type ("I" / "P" / "B"), cabac_init_idc (0/1/2,
    /// unused for I), and slice QP. Returns a list of
    /// (p_state_idx, val_mps) tuples — one per context. Per ITU-T
    /// H.264 §9.3.1.1.
    fn cabac_init_contexts<'py>(
        &self,
        py: Python<'py>,
        slice_type: &str,
        cabac_init_idc: u8,
        slice_qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::cabac::{init_contexts, CabacSliceType};
        let st = match slice_type {
            "I" | "SI" => CabacSliceType::I,
            "P" | "SP" => CabacSliceType::P,
            "B" => CabacSliceType::B,
            other => {
                return Err(PyValueError::new_err(format!(
                    "unknown slice_type: {}",
                    other
                )))
            }
        };
        let ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let out = pyo3::types::PyList::empty_bound(py);
        for c in ctxs.iter() {
            let t = pyo3::types::PyTuple::new_bound(
                py,
                &[c.p_state_idx.into_py(py), c.val_mps.into_py(py)],
            );
            out.append(t)?;
        }
        Ok(out)
    }

    /// Round-trip a sequence of mb_skip_flag bins via real H.264
    /// context selection (§9.3.3.1.1.1). `skips` is the desired
    /// macroblock skip pattern as a flat list in raster-scan order
    /// (each entry 0 or 1); `mb_width` is the picture width in MBs.
    /// `slice_type` is "P" or "B"; `slice_qp` and `cabac_init_idc`
    /// drive context initialisation.
    ///
    /// Returns (encoded_bytes, decoded_skips, final_ctxs).
    /// final_ctxs is a list of 3 tuples for ctxIdx
    /// {offset, offset+1, offset+2} after all bins are processed —
    /// useful for asserting that adaptation tracked correctly.
    fn cabac_mb_skip_flag_round_trip<'py>(
        &self,
        py: Python<'py>,
        slice_type: &str,
        cabac_init_idc: u8,
        slice_qp: i32,
        mb_width: usize,
        skips: Vec<u8>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            init_contexts, mb_skip_flag_ctx_idx, mb_skip_flag_ctx_offset, CabacDecoder,
            CabacEncoder, CabacSliceType,
        };
        let st = match slice_type {
            "P" | "SP" => CabacSliceType::P,
            "B" => CabacSliceType::B,
            other => {
                return Err(PyValueError::new_err(format!(
                    "mb_skip_flag is only defined for P/B slices; got {}",
                    other
                )))
            }
        };
        let mb_height = (skips.len() + mb_width - 1) / mb_width;
        let mut enc_ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        let mut grid = vec![vec![None::<u8>; mb_width]; mb_height];
        for (i, &skip) in skips.iter().enumerate() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { grid[r][c - 1] };
            let top = if r == 0 { None } else { grid[r - 1][c] };
            let ctx_idx = mb_skip_flag_ctx_idx(st, left, top).unwrap();
            enc.encode_bin(&mut enc_ctxs[ctx_idx], skip);
            grid[r][c] = Some(skip);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut decoded_grid = vec![vec![None::<u8>; mb_width]; mb_height];
        let mut decoded = Vec::with_capacity(skips.len());
        for i in 0..skips.len() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { decoded_grid[r][c - 1] };
            let top = if r == 0 { None } else { decoded_grid[r - 1][c] };
            let ctx_idx = mb_skip_flag_ctx_idx(st, left, top).unwrap();
            let bit = dec.decode_bin(&mut dec_ctxs[ctx_idx]);
            decoded_grid[r][c] = Some(bit);
            decoded.push(bit);
        }

        let off = mb_skip_flag_ctx_offset(st).unwrap();
        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let dec_py = pyo3::types::PyList::new_bound(py, &decoded);
        let ctxs_py = pyo3::types::PyList::empty_bound(py);
        for ctx in &dec_ctxs[off..off + 3] {
            let t = pyo3::types::PyTuple::new_bound(
                py,
                &[ctx.p_state_idx.into_py(py), ctx.val_mps.into_py(py)],
            );
            ctxs_py.append(t)?;
        }
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[buf_py.into_any(), dec_py.into_any(), ctxs_py.into_any()],
        ))
    }

    /// Round-trip a P-slice macroblock walk: for each MB emit
    /// mb_skip_flag, then (if not skipped) the mb_type. Encoder
    /// and decoder run with neighbour-aware context selection for
    /// mb_skip_flag and the binarisation-tree dispatch for mb_type.
    ///
    /// Args:
    ///   slice_qp: QP for context initialisation
    ///   cabac_init_idc: 0/1/2 for PB tables
    ///   mb_width: picture width in macroblocks
    ///   mbs: list of (skip, mb_type) tuples. mb_type ignored when
    ///        skip == 1.
    ///
    /// Returns (encoded_bytes, [(skip, mb_type), ...], bytes_per_mb).
    fn cabac_p_slice_walk<'py>(
        &self,
        py: Python<'py>,
        slice_qp: i32,
        cabac_init_idc: u8,
        mb_width: usize,
        mbs: Vec<(u8, u8)>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_p_mb_type, encode_p_mb_type, init_contexts, mb_skip_flag_ctx_idx, CabacDecoder,
            CabacEncoder, CabacSliceType,
        };
        let st = CabacSliceType::P;
        let mb_height = (mbs.len() + mb_width - 1) / mb_width;
        let mut enc_ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        let mut enc_grid = vec![vec![None::<u8>; mb_width]; mb_height];
        for (i, &(skip, mb_type)) in mbs.iter().enumerate() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { enc_grid[r][c - 1] };
            let top = if r == 0 { None } else { enc_grid[r - 1][c] };
            let ctx_idx = mb_skip_flag_ctx_idx(st, left, top).unwrap();
            enc.encode_bin(&mut enc_ctxs[ctx_idx], skip);
            enc_grid[r][c] = Some(skip);
            if skip == 0 {
                encode_p_mb_type(&mut enc, &mut enc_ctxs, mb_type);
            }
        }
        enc.finish();

        // Decode mirror.
        let mut dec_ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut dec_grid = vec![vec![None::<u8>; mb_width]; mb_height];
        let mut decoded: Vec<(u8, u8)> = Vec::with_capacity(mbs.len());
        for i in 0..mbs.len() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { dec_grid[r][c - 1] };
            let top = if r == 0 { None } else { dec_grid[r - 1][c] };
            let ctx_idx = mb_skip_flag_ctx_idx(st, left, top).unwrap();
            let skip = dec.decode_bin(&mut dec_ctxs[ctx_idx]);
            dec_grid[r][c] = Some(skip);
            let mb_type = if skip == 0 {
                let (v, _) = decode_p_mb_type(&mut dec, &mut dec_ctxs);
                v
            } else {
                0
            };
            decoded.push((skip, mb_type));
        }

        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let dec_py = pyo3::types::PyList::empty_bound(py);
        for (s, m) in decoded.iter() {
            let t = pyo3::types::PyTuple::new_bound(py, &[s.into_py(py), m.into_py(py)]);
            dec_py.append(t)?;
        }
        let bytes_per_mb: f64 = enc.buffer.len() as f64 / mbs.len() as f64;
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                buf_py.into_any(),
                dec_py.into_any(),
                bytes_per_mb.into_py(py).into_bound(py),
            ],
        ))
    }

    /// Round-trip a sequence of mb_qp_delta values under a single
    /// P-slice's context state. Tracks the "prev_was_zero" carry
    /// across MBs for bin-0 context selection (§9.3.3.1.1.5).
    /// Returns (encoded_bytes, decoded_deltas, bytes_per_mb).
    fn cabac_mb_qp_delta_sequence<'py>(
        &self,
        py: Python<'py>,
        slice_qp: i32,
        cabac_init_idc: u8,
        deltas: Vec<i32>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_mb_qp_delta, encode_mb_qp_delta, init_contexts, CabacDecoder, CabacEncoder,
            CabacSliceType,
        };
        let st = CabacSliceType::P;
        let mut enc_ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        let mut prev_was_zero = true;
        for &d in &deltas {
            encode_mb_qp_delta(&mut enc, &mut enc_ctxs, d, prev_was_zero);
            prev_was_zero = d == 0;
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut decoded: Vec<i32> = Vec::with_capacity(deltas.len());
        let mut prev = true;
        for _ in 0..deltas.len() {
            let (d, _) = decode_mb_qp_delta(&mut dec, &mut dec_ctxs, prev);
            prev = d == 0;
            decoded.push(d);
        }

        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let dec_py = pyo3::types::PyList::new_bound(py, &decoded);
        let bpm: f64 = enc.buffer.len() as f64 / deltas.len() as f64;
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                buf_py.into_any(),
                dec_py.into_any(),
                bpm.into_py(py).into_bound(py),
            ],
        ))
    }

    /// Round-trip a P-slice walk emitting mb_skip_flag, mb_type,
    /// mb_qp_delta, cbp_luma, cbp_chroma per MB (when applicable).
    /// `mbs` is a list of (skip, mb_type, qp_delta, cbp_luma,
    /// cbp_chroma) tuples in raster order. For skipped MBs only
    /// the skip bin is emitted; for non-skipped MBs all five are.
    ///
    /// Returns (encoded_bytes, decoded_mbs, bytes_per_mb).
    fn cabac_p_slice_full_mb_walk<'py>(
        &self,
        py: Python<'py>,
        slice_qp: i32,
        cabac_init_idc: u8,
        mb_width: usize,
        mbs: Vec<(u8, u8, i32, u8, u8)>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_cbp_chroma, decode_cbp_luma, decode_mb_qp_delta, decode_p_mb_type,
            encode_cbp_chroma, encode_cbp_luma, encode_mb_qp_delta, encode_p_mb_type,
            init_contexts, mb_skip_flag_ctx_idx, CabacDecoder, CabacEncoder, CabacSliceType,
        };
        let st = CabacSliceType::P;
        let mb_height = (mbs.len() + mb_width - 1) / mb_width;
        // Encode.
        let mut enc_ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        let mut enc_skip = vec![vec![None::<u8>; mb_width]; mb_height];
        let mut enc_luma = vec![vec![0u8; mb_width]; mb_height];
        let mut enc_chroma = vec![vec![0u8; mb_width]; mb_height];
        let mut prev_qpd_zero = true;
        for (i, &(skip, mb_type, qpd, cbp_l, cbp_c)) in mbs.iter().enumerate() {
            let r = i / mb_width;
            let c = i % mb_width;
            let sleft = if c == 0 { None } else { enc_skip[r][c - 1] };
            let stop = if r == 0 { None } else { enc_skip[r - 1][c] };
            let skip_ctx = mb_skip_flag_ctx_idx(st, sleft, stop).unwrap();
            enc.encode_bin(&mut enc_ctxs[skip_ctx], skip);
            enc_skip[r][c] = Some(skip);
            if skip == 1 {
                continue;
            }

            encode_p_mb_type(&mut enc, &mut enc_ctxs, mb_type);
            encode_mb_qp_delta(&mut enc, &mut enc_ctxs, qpd, prev_qpd_zero);
            prev_qpd_zero = qpd == 0;

            let lleft = if c == 0 { 0 } else { enc_luma[r][c - 1] };
            let ltop = if r == 0 { 0 } else { enc_luma[r - 1][c] };
            let cleft = if c == 0 { 0 } else { enc_chroma[r][c - 1] };
            let ctop = if r == 0 { 0 } else { enc_chroma[r - 1][c] };
            encode_cbp_luma(&mut enc, &mut enc_ctxs, cbp_l, lleft, ltop);
            encode_cbp_chroma(&mut enc, &mut enc_ctxs, cbp_c, cleft, ctop);
            enc_luma[r][c] = cbp_l;
            enc_chroma[r][c] = cbp_c;
        }
        enc.finish();

        // Decode mirror.
        let mut dec_ctxs = init_contexts(st, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut dec_skip = vec![vec![None::<u8>; mb_width]; mb_height];
        let mut dec_luma = vec![vec![0u8; mb_width]; mb_height];
        let mut dec_chroma = vec![vec![0u8; mb_width]; mb_height];
        let mut decoded: Vec<(u8, u8, i32, u8, u8)> = Vec::with_capacity(mbs.len());
        let mut prev_zero = true;
        for i in 0..mbs.len() {
            let r = i / mb_width;
            let c = i % mb_width;
            let sleft = if c == 0 { None } else { dec_skip[r][c - 1] };
            let stop = if r == 0 { None } else { dec_skip[r - 1][c] };
            let skip_ctx = mb_skip_flag_ctx_idx(st, sleft, stop).unwrap();
            let skip = dec.decode_bin(&mut dec_ctxs[skip_ctx]);
            dec_skip[r][c] = Some(skip);
            if skip == 1 {
                decoded.push((1, 0, 0, 0, 0));
                continue;
            }
            let (mb_type, _) = decode_p_mb_type(&mut dec, &mut dec_ctxs);
            let (qpd, _) = decode_mb_qp_delta(&mut dec, &mut dec_ctxs, prev_zero);
            prev_zero = qpd == 0;

            let lleft = if c == 0 { 0 } else { dec_luma[r][c - 1] };
            let ltop = if r == 0 { 0 } else { dec_luma[r - 1][c] };
            let cleft = if c == 0 { 0 } else { dec_chroma[r][c - 1] };
            let ctop = if r == 0 { 0 } else { dec_chroma[r - 1][c] };
            let (cbp_l, _) = decode_cbp_luma(&mut dec, &mut dec_ctxs, lleft, ltop);
            let (cbp_c, _) = decode_cbp_chroma(&mut dec, &mut dec_ctxs, cleft, ctop);
            dec_luma[r][c] = cbp_l;
            dec_chroma[r][c] = cbp_c;
            decoded.push((0, mb_type, qpd, cbp_l, cbp_c));
        }

        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let dec_py = pyo3::types::PyList::empty_bound(py);
        for &(s, m, q, l, ch) in decoded.iter() {
            let t = pyo3::types::PyTuple::new_bound(
                py,
                &[
                    s.into_py(py),
                    m.into_py(py),
                    q.into_py(py),
                    l.into_py(py),
                    ch.into_py(py),
                ],
            );
            dec_py.append(t)?;
        }
        let bpm: f64 = enc.buffer.len() as f64 / mbs.len() as f64;
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                buf_py.into_any(),
                dec_py.into_any(),
                bpm.into_py(py).into_bound(py),
            ],
        ))
    }

    /// Round-trip a sequence of 4x4 luma residual blocks under
    /// real H.264 CABAC. Each block is 16 i32 coefficients;
    /// returns (encoded_bytes, decoded_blocks, bytes_per_block).
    fn cabac_residual_4x4_sequence<'py>(
        &self,
        py: Python<'py>,
        slice_qp: i32,
        cabac_init_idc: u8,
        blocks: Vec<Vec<i32>>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_residual_4x4_luma, encode_residual_4x4_luma, init_contexts, CabacDecoder,
            CabacEncoder, CabacSliceType,
        };
        let n = blocks.len();
        let mut enc_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        for block in &blocks {
            if block.len() != 16 {
                return Err(PyValueError::new_err(format!(
                    "each block must be 16 coefs; got {}",
                    block.len()
                )));
            }
            let mut arr = [0i32; 16];
            for (i, &v) in block.iter().enumerate() {
                arr[i] = v;
            }
            encode_residual_4x4_luma(&mut enc, &mut enc_ctxs, &arr);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let dec_py = pyo3::types::PyList::empty_bound(py);
        for _ in 0..n {
            let (decoded, _) = decode_residual_4x4_luma(&mut dec, &mut dec_ctxs);
            let block_py = pyo3::types::PyList::new_bound(py, &decoded);
            dec_py.append(block_py)?;
        }

        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let bpb: f64 = enc.buffer.len() as f64 / n as f64;
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                buf_py.into_any(),
                dec_py.into_any(),
                bpb.into_py(py).into_bound(py),
            ],
        ))
    }

    /// Round-trip a residual block of any supported ctxBlockCat.
    /// `cat` is one of "intra16x16_dc", "intra16x16_ac", "luma_4x4",
    /// "chroma_dc", "chroma_ac", "luma_8x8".
    fn cabac_residual_block<'py>(
        &self,
        py: Python<'py>,
        slice_qp: i32,
        cabac_init_idc: u8,
        cat: &str,
        coefs: Vec<i32>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_residual_block, encode_residual_block, init_contexts, res_block_spec,
            CabacDecoder, CabacEncoder, CabacSliceType, CtxBlockCat,
        };
        let cat_enum = match cat {
            "intra16x16_dc" => CtxBlockCat::Intra16x16Dc,
            "intra16x16_ac" => CtxBlockCat::Intra16x16Ac,
            "luma_4x4" => CtxBlockCat::Luma4x4,
            "chroma_dc" => CtxBlockCat::ChromaDc,
            "chroma_ac" => CtxBlockCat::ChromaAc,
            "luma_8x8" => CtxBlockCat::Luma8x8,
            other => {
                return Err(PyValueError::new_err(format!(
                    "unknown ctxBlockCat: {}",
                    other
                )))
            }
        };
        let spec = res_block_spec(cat_enum);
        if coefs.len() != spec.n_coefs {
            return Err(PyValueError::new_err(format!(
                "cat {} expects {} coefs; got {}",
                cat,
                spec.n_coefs,
                coefs.len()
            )));
        }
        let mut enc_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        encode_residual_block(&mut enc, &mut enc_ctxs, spec, &coefs);
        enc.finish();
        let mut dec_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let (decoded, _) = decode_residual_block(&mut dec, &mut dec_ctxs, spec);
        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let dec_py = pyo3::types::PyList::new_bound(py, &decoded);
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[buf_py.into_any(), dec_py.into_any()],
        ))
    }

    /// Round-trip a sequence of mvd values.
    fn cabac_mvd_sequence<'py>(
        &self,
        py: Python<'py>,
        slice_qp: i32,
        cabac_init_idc: u8,
        values: Vec<i32>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_mvd, encode_mvd, init_contexts, CabacDecoder, CabacEncoder, CabacSliceType,
            MVD_L0_X_CTX_OFFSET,
        };
        let mut enc_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        for &v in &values {
            encode_mvd(&mut enc, &mut enc_ctxs, MVD_L0_X_CTX_OFFSET, v);
        }
        enc.finish();
        let mut dec_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut decoded = Vec::with_capacity(values.len());
        for _ in 0..values.len() {
            let (v, _) = decode_mvd(&mut dec, &mut dec_ctxs, MVD_L0_X_CTX_OFFSET);
            decoded.push(v);
        }
        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let dec_py = pyo3::types::PyList::new_bound(py, &decoded);
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[buf_py.into_any(), dec_py.into_any()],
        ))
    }

    /// Round-trip a sequence of P-slice sub_mb_type values.
    fn cabac_p_sub_mb_type_sequence<'py>(
        &self,
        py: Python<'py>,
        slice_qp: i32,
        cabac_init_idc: u8,
        values: Vec<u8>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_p_sub_mb_type, encode_p_sub_mb_type, init_contexts, CabacDecoder, CabacEncoder,
            CabacSliceType,
        };
        let mut enc_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        for &v in &values {
            encode_p_sub_mb_type(&mut enc, &mut enc_ctxs, v);
        }
        enc.finish();
        let mut dec_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut decoded = Vec::with_capacity(values.len());
        for _ in 0..values.len() {
            let (v, _) = decode_p_sub_mb_type(&mut dec, &mut dec_ctxs);
            decoded.push(v);
        }
        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let dec_py = pyo3::types::PyList::new_bound(py, &decoded);
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[buf_py.into_any(), dec_py.into_any()],
        ))
    }

    /// Round-trip a sequence of ref_idx_l0 values with neighbour-
    /// aware bin-0 context selection over an mb_width-MB grid.
    fn cabac_ref_idx_l0_sequence<'py>(
        &self,
        py: Python<'py>,
        slice_qp: i32,
        cabac_init_idc: u8,
        mb_width: usize,
        num_ref_idx_active_minus1: u8,
        values: Vec<u8>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_ref_idx_l0, encode_ref_idx_l0, init_contexts, ref_idx_bin0_ctx_inc,
            CabacDecoder, CabacEncoder, CabacSliceType,
        };
        let height = (values.len() + mb_width - 1) / mb_width;
        let mut enc_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        let mut enc_grid = vec![vec![None::<u8>; mb_width]; height];
        for (i, &v) in values.iter().enumerate() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { enc_grid[r][c - 1] };
            let top = if r == 0 { None } else { enc_grid[r - 1][c] };
            let inc = ref_idx_bin0_ctx_inc(left, top);
            encode_ref_idx_l0(&mut enc, &mut enc_ctxs, v, inc, num_ref_idx_active_minus1);
            enc_grid[r][c] = Some(v);
        }
        enc.finish();

        let mut dec_ctxs = init_contexts(CabacSliceType::P, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(enc.buffer.clone(), 0);
        let mut dec_grid = vec![vec![None::<u8>; mb_width]; height];
        let mut decoded = Vec::with_capacity(values.len());
        for i in 0..values.len() {
            let r = i / mb_width;
            let c = i % mb_width;
            let left = if c == 0 { None } else { dec_grid[r][c - 1] };
            let top = if r == 0 { None } else { dec_grid[r - 1][c] };
            let inc = ref_idx_bin0_ctx_inc(left, top);
            let (v, _) = decode_ref_idx_l0(&mut dec, &mut dec_ctxs, inc, num_ref_idx_active_minus1);
            dec_grid[r][c] = Some(v);
            decoded.push(v);
        }
        let buf_py = pyo3::types::PyBytes::new_bound(py, &enc.buffer);
        let dec_py = pyo3::types::PyList::new_bound(py, &decoded);
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[buf_py.into_any(), dec_py.into_any()],
        ))
    }

    /// Walk an H.264 slice header per ITU-T §7.3.3. Returns a dict
    /// of decoded fields including header_end_bp + cabac_start_bp.
    /// Caller supplies the SPS+PPS state derived from a prior parse.
    fn walk_h264_slice_header<'py>(
        &self,
        py: Python<'py>,
        rbsp: &[u8],
        sps_pps_dict: &Bound<'_, pyo3::types::PyDict>,
        nal_ref_idc: u8,
        is_idr: bool,
    ) -> PyResult<Bound<'py, pyo3::types::PyDict>> {
        use crate::h264_slice_header::{walk_h264_slice_header, H264SpsPpsContext};
        let g = |k: &str| -> PyResult<i64> {
            sps_pps_dict
                .get_item(k)?
                .ok_or_else(|| PyValueError::new_err(format!("sps_pps missing key {}", k)))?
                .extract::<i64>()
        };
        let ctx = H264SpsPpsContext {
            log2_max_frame_num: g("log2_max_frame_num")? as u32,
            pic_order_cnt_type: g("pic_order_cnt_type")? as u32,
            log2_max_poc_lsb: g("log2_max_poc_lsb")? as u32,
            frame_mbs_only_flag: g("frame_mbs_only_flag")? as u32,
            bottom_field_pic_order_in_frame_present_flag: g(
                "bottom_field_pic_order_in_frame_present_flag",
            )? as u32,
            redundant_pic_cnt_present_flag: g("redundant_pic_cnt_present_flag")? as u32,
            weighted_pred_flag: g("weighted_pred_flag")? as u32,
            weighted_bipred_idc: g("weighted_bipred_idc")? as u32,
            entropy_coding_mode_flag: g("entropy_coding_mode_flag")? as u32,
            deblocking_filter_control_present_flag: g("deblocking_filter_control_present_flag")?
                as u32,
            num_ref_idx_l0_default_active_minus1: g("num_ref_idx_l0_default_active_minus1")? as u32,
            num_ref_idx_l1_default_active_minus1: g("num_ref_idx_l1_default_active_minus1")? as u32,
            pic_init_qp_minus26: (g("pic_init_qp")? as i32) - 26,
            num_slice_groups_minus1: g("num_slice_groups_minus1")? as u32,
        };
        let m = walk_h264_slice_header(rbsp, &ctx, nal_ref_idc, is_idr);
        let out = pyo3::types::PyDict::new_bound(py);
        for (k, v) in m {
            if let Some(n) = v.as_i64() {
                out.set_item(k, n)?;
            } else if let Some(n) = v.as_u64() {
                out.set_item(k, n)?;
            }
        }
        Ok(out)
    }

    /// Pure-Rust CABAC throughput benchmark — encodes `n_bins` under
    /// a single context with the given (p_state_idx, val_mps), all
    /// bins = `bin_val`. Then decodes them. Returns (wall_seconds,
    /// encoded_byte_count). Bypasses Python list-overhead so the
    /// measurement reflects engine throughput, not bridge cost.
    fn cabac_bench_single_context(
        &self,
        n_bins: usize,
        p_state_idx: u8,
        val_mps: u8,
        bin_val: u8,
    ) -> PyResult<(f64, usize)> {
        use crate::cabac::{CabacCtx, CabacDecoder, CabacEncoder};
        let start = std::time::Instant::now();
        // Encode
        let mut enc_ctx = CabacCtx {
            p_state_idx,
            val_mps,
        };
        let mut enc = CabacEncoder::new();
        for _ in 0..n_bins {
            enc.encode_bin(&mut enc_ctx, bin_val);
        }
        enc.finish();
        let buf_len = enc.buffer.len();
        // Decode
        let mut dec_ctx = CabacCtx {
            p_state_idx,
            val_mps,
        };
        let mut dec = CabacDecoder::new(enc.buffer, 0);
        let mut sink: u64 = 0;
        for _ in 0..n_bins {
            sink = sink.wrapping_add(dec.decode_bin(&mut dec_ctx) as u64);
        }
        // Sink read so optimiser doesn't elide the decode loop.
        let _ = std::hint::black_box(sink);
        let elapsed = start.elapsed().as_secs_f64();
        Ok((elapsed, buf_len))
    }

    /// Same shape but with random-ish bins (alternating low-prob).
    /// Tests the LPS path adaptation cost.
    fn cabac_bench_mixed_bins(
        &self,
        n_bins: usize,
        p_state_idx: u8,
        val_mps: u8,
        skew_one_in: usize,
    ) -> PyResult<(f64, usize)> {
        use crate::cabac::{CabacCtx, CabacDecoder, CabacEncoder};
        let start = std::time::Instant::now();
        let bins: Vec<u8> = (0..n_bins)
            .map(|i| {
                if i % skew_one_in == 0 {
                    1 - val_mps
                } else {
                    val_mps
                }
            })
            .collect();
        let mut enc_ctx = CabacCtx {
            p_state_idx,
            val_mps,
        };
        let mut enc = CabacEncoder::new();
        for &b in &bins {
            enc.encode_bin(&mut enc_ctx, b);
        }
        enc.finish();
        let buf_len = enc.buffer.len();
        let mut dec_ctx = CabacCtx {
            p_state_idx,
            val_mps,
        };
        let mut dec = CabacDecoder::new(enc.buffer, 0);
        let mut sink: u64 = 0;
        for _ in 0..n_bins {
            sink = sink.wrapping_add(dec.decode_bin(&mut dec_ctx) as u64);
        }
        let _ = std::hint::black_box(sink);
        let elapsed = start.elapsed().as_secs_f64();
        Ok((elapsed, buf_len))
    }

    /// DCT-domain 2:1 fold benchmark. `n_blocks` is the number of
    /// output 4×4 blocks to produce; each fold consumes four 4×4
    /// input blocks (= one 8×8 region of source). Returns the
    /// elapsed wall time on the Rust side.
    fn h264_dct_fold_bench(&self, n_folds: usize, use_matrix: bool) -> PyResult<f64> {
        use crate::h264_dct::{fold_4to1_via_matrix, fold_4to1_via_pixels};
        // Build a "realistic" input: low-frequency-dominated
        // coefficients (DC large, AC small, mostly zero).
        let mut tl = [0i32; 16];
        let mut tr = [0i32; 16];
        let mut bl = [0i32; 16];
        let mut br = [0i32; 16];
        tl[0] = 120;
        tl[1] = -10;
        tl[4] = -8;
        tr[0] = 122;
        tr[1] = 12;
        tr[4] = -6;
        bl[0] = 118;
        bl[1] = -7;
        bl[4] = 9;
        br[0] = 125;
        br[1] = 8;
        br[4] = 4;
        let start = std::time::Instant::now();
        let mut sink: i64 = 0;
        if use_matrix {
            for _ in 0..n_folds {
                let out = fold_4to1_via_matrix(&tl, &tr, &bl, &br);
                for v in out.iter() {
                    sink = sink.wrapping_add(*v as i64);
                }
            }
        } else {
            for _ in 0..n_folds {
                let out = fold_4to1_via_pixels(&tl, &tr, &bl, &br);
                for v in out.iter() {
                    sink = sink.wrapping_add(*v as i64);
                }
            }
        }
        let _ = std::hint::black_box(sink);
        Ok(start.elapsed().as_secs_f64())
    }

    /// Fold a flat array of input coefficients to the downscaled
    /// output coefficients. Input is `4 * 16 * n_folds` i32s in the
    /// order `[tl0..16, tr0..16, bl0..16, br0..16,  tl1..16, ...]`.
    /// Output is `16 * n_folds` i32s. Uses the matrix fast path.
    fn h264_dct_fold_many<'py>(
        &self,
        py: Python<'py>,
        coefs: Vec<i32>,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::fold_4to1_via_matrix;
        if coefs.len() % 64 != 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "coefs must be a multiple of 64 (4 blocks × 16 coefficients)",
            ));
        }
        let n = coefs.len() / 64;
        let mut out: Vec<i32> = Vec::with_capacity(16 * n);
        for i in 0..n {
            let mut tl = [0i32; 16];
            let mut tr = [0i32; 16];
            let mut bl = [0i32; 16];
            let mut br = [0i32; 16];
            tl.copy_from_slice(&coefs[i * 64..i * 64 + 16]);
            tr.copy_from_slice(&coefs[i * 64 + 16..i * 64 + 32]);
            bl.copy_from_slice(&coefs[i * 64 + 32..i * 64 + 48]);
            br.copy_from_slice(&coefs[i * 64 + 48..i * 64 + 64]);
            let folded = fold_4to1_via_matrix(&tl, &tr, &bl, &br);
            out.extend_from_slice(&folded);
        }
        let py_list = pyo3::types::PyList::new_bound(py, &out);
        Ok(py_list)
    }

    /// Forward 4×4 H.264 integer DCT applied to a flat input of
    /// `16 * n` samples. Returns `16 * n` coefficients in the same
    /// layout. Used by Python-side tests that need to construct
    /// realistic blocks from pixel data.
    fn h264_dct_forward_many<'py>(
        &self,
        py: Python<'py>,
        samples: Vec<i32>,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::forward_4x4;
        if samples.len() % 16 != 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "samples must be a multiple of 16",
            ));
        }
        let n = samples.len() / 16;
        let mut out: Vec<i32> = Vec::with_capacity(16 * n);
        for i in 0..n {
            let mut x = [0i32; 16];
            x.copy_from_slice(&samples[i * 16..(i + 1) * 16]);
            let y = forward_4x4(&x);
            out.extend_from_slice(&y);
        }
        let py_list = pyo3::types::PyList::new_bound(py, &out);
        Ok(py_list)
    }

    /// Inverse 4×4 H.264 integer DCT applied to a flat input of
    /// `16 * n` coefficients. Returns `16 * n` samples.
    fn h264_dct_inverse_many<'py>(
        &self,
        py: Python<'py>,
        coefs: Vec<i32>,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::inverse_4x4;
        if coefs.len() % 16 != 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "coefs must be a multiple of 16",
            ));
        }
        let n = coefs.len() / 16;
        let mut out: Vec<i32> = Vec::with_capacity(16 * n);
        for i in 0..n {
            let mut y = [0i32; 16];
            y.copy_from_slice(&coefs[i * 16..(i + 1) * 16]);
            let x = inverse_4x4(&y);
            out.extend_from_slice(&x);
        }
        let py_list = pyo3::types::PyList::new_bound(py, &out);
        Ok(py_list)
    }

    /// Forward-quantise a batch of 4×4 luma intra blocks per
    /// H.264 §8.5.10. `coefs` is a flat list of 16 raw DCT
    /// coefficients per block; output is the same shape with
    /// quantised values ready for CABAC encoding.
    fn h264_quantize_intra_many<'py>(
        &self,
        py: Python<'py>,
        coefs: Vec<i32>,
        qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::quantize_intra_4x4;
        if coefs.len() % 16 != 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "coefs length must be a multiple of 16",
            ));
        }
        let n = coefs.len() / 16;
        let mut out: Vec<i32> = Vec::with_capacity(n * 16);
        for i in 0..n {
            let mut y = [0i32; 16];
            y.copy_from_slice(&coefs[i * 16..(i + 1) * 16]);
            out.extend_from_slice(&quantize_intra_4x4(&y, qp));
        }
        Ok(pyo3::types::PyList::new_bound(py, &out))
    }

    /// Run the graph-resident audio pipeline attached to an
    /// AudioStream. The runtime walks Operation nodes connected
    /// via `has_pipeline_entry` + `feeds_into`, dispatches each to
    /// the matching Rust primitive (gammatone / envelope /
    /// onset_detect / broadband_coincidence), and mints terminal
    /// events (EnvelopeChannel / OnsetEvent / BroadbandOnset) on
    /// the stream. The pipeline is graph data; the agent can read
    /// or edit it and the next run picks the changes up.
    #[pyo3(signature = (audio_stream, samples, sample_rate))]
    fn run_audio_pipeline<'py>(
        &mut self,
        py: Python<'py>,
        audio_stream: PyRef<'_, PyNodeID>,
        samples: &Bound<'_, pyo3::types::PyBytes>,
        sample_rate: u32,
    ) -> PyResult<Bound<'py, PyDict>> {
        let raw = samples.as_bytes();
        if raw.len() % 4 != 0 {
            return Err(PyValueError::new_err(
                "samples PyBytes length must be a multiple of 4 (f32)",
            ));
        }
        let n_samples = raw.len() / 4;
        let mut buf = Vec::with_capacity(n_samples);
        for i in 0..n_samples {
            let off = i * 4;
            buf.push(f32::from_le_bytes([
                raw[off],
                raw[off + 1],
                raw[off + 2],
                raw[off + 3],
            ]));
        }
        let stream_nid = audio_stream.to_node();
        let summary = {
            let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
            let inner = &mut *__substrate_guard;
            // The agent OWNS the sound: store raw f32 samples + metadata
            // as an AudioBuffer node attached to the stream via
            // `has_audio`. The ear Operations (gammatone / stft / ...)
            // read their input from this node, not from a side-channel.
            // The raw PyBytes is already little-endian f32, so we store
            // the bytes directly as a Surface(Bytes) — cheap Arc clone,
            // no per-sample boxing.
            crate::pipeline_runtime::attach_audio_buffer(
                inner,
                stream_nid,
                raw,
                sample_rate,
                n_samples,
            );
            crate::pipeline_runtime::run_pipeline(inner, stream_nid, &buf, sample_rate)
        };
        let out = PyDict::new_bound(py);
        out.set_item("ops_run", summary.ops_run)?;
        out.set_item("envelopes", summary.envelopes)?;
        out.set_item("onsets", summary.onsets)?;
        out.set_item("broadband", summary.broadband)?;
        out.set_item("syllables", summary.syllables)?;
        Ok(out)
    }

    /// Synthesise audio for one AcousticSign via the source-filter
    /// voicebox primitive. The composition (which sign, which
    /// patches, which params) is decided by graph data; this just
    /// dispatches into Rust.
    ///
    /// Inputs:
    ///   trajectory       — flat list of n_patches × spp floats,
    ///                      the sign's stored trajectory.
    ///   patch_centres    — Vec<f32>, per-channel centre_hz in the
    ///                      same order as the trajectory channels
    ///                      (lexical_access sorts alphabetically by
    ///                      patch name).
    ///   patch_kinds      — Vec<String>, same order.
    ///   patch_is_sibilant — Vec<bool>, same order; true → noise.
    ///   spp              — samples per patch in the trajectory.
    ///   output_samples   — desired output length.
    ///   sample_rate      — Hz.
    ///   f0_hz            — base voicing pitch (default 120 Hz).
    ///   q_factor         — formant filter Q (default 4.0).
    ///
    /// Returns the audio as PyBytes (little-endian f32).
    #[pyo3(signature = (trajectory, patch_centres, patch_sigmas,
                          patch_kinds, patch_is_sibilant, spp,
                          output_samples, sample_rate, f0_hz=120.0,
                          q_clamp_max=6.0))]
    fn synthesize_from_trajectory<'py>(
        &mut self,
        py: Python<'py>,
        trajectory: Vec<f32>,
        patch_centres: Vec<f32>,
        patch_sigmas: Vec<f32>,
        patch_kinds: Vec<String>,
        patch_is_sibilant: Vec<bool>,
        spp: usize,
        output_samples: usize,
        sample_rate: u32,
        f0_hz: f32,
        q_clamp_max: f32,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        if patch_centres.len() != patch_kinds.len()
            || patch_centres.len() != patch_is_sibilant.len()
            || patch_centres.len() != patch_sigmas.len()
        {
            return Err(PyValueError::new_err(
                "patch_centres / patch_sigmas / patch_kinds / \
                 patch_is_sibilant must have matching lengths",
            ));
        }
        let patches: Vec<crate::audio_primitives::VoiceboxPatch> = patch_centres
            .iter()
            .zip(patch_sigmas.iter())
            .zip(patch_kinds.iter())
            .zip(patch_is_sibilant.iter())
            .map(
                |(((c, sig), k), s)| crate::audio_primitives::VoiceboxPatch {
                    centre_hz: *c,
                    freq_sigma_hz: *sig,
                    kind: k.clone(),
                    is_sibilant: *s,
                },
            )
            .collect();
        let audio = crate::audio_primitives::synthesize_from_trajectory(
            &trajectory,
            &patches,
            spp,
            output_samples,
            sample_rate,
            f0_hz,
            q_clamp_max,
        );
        let mut bytes: Vec<u8> = Vec::with_capacity(audio.len() * 4);
        for v in &audio {
            bytes.extend_from_slice(&v.to_le_bytes());
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &bytes))
    }

    /// KLATT cascade + LF glottal source synthesis (iter-40 upgraded forward
    /// model). Same trajectory/patch interface as `synthesize_from_trajectory`,
    /// plus LF source shape params (oq/am/ta_frac = voice identity) and an
    /// optional nasal antiresonance (nasal_f/nasal_bw > 0). Pure DSP, no fit.
    /// Returns the audio as PyBytes (little-endian f32).
    #[pyo3(signature = (trajectory, patch_centres, patch_sigmas,
                          patch_kinds, patch_is_sibilant, spp,
                          output_samples, sample_rate, f0_hz=120.0,
                          oq=0.6, am=0.7, ta_frac=0.01,
                          nasal_f=0.0, nasal_bw=0.0))]
    fn synthesize_klatt_lf<'py>(
        &mut self,
        py: Python<'py>,
        trajectory: Vec<f32>,
        patch_centres: Vec<f32>,
        patch_sigmas: Vec<f32>,
        patch_kinds: Vec<String>,
        patch_is_sibilant: Vec<bool>,
        spp: usize,
        output_samples: usize,
        sample_rate: u32,
        f0_hz: f32,
        oq: f32,
        am: f32,
        ta_frac: f32,
        nasal_f: f32,
        nasal_bw: f32,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        if patch_centres.len() != patch_kinds.len()
            || patch_centres.len() != patch_is_sibilant.len()
            || patch_centres.len() != patch_sigmas.len()
        {
            return Err(PyValueError::new_err(
                "patch_centres / patch_sigmas / patch_kinds / \
                 patch_is_sibilant must have matching lengths",
            ));
        }
        let patches: Vec<crate::audio_primitives::VoiceboxPatch> = patch_centres
            .iter()
            .zip(patch_sigmas.iter())
            .zip(patch_kinds.iter())
            .zip(patch_is_sibilant.iter())
            .map(
                |(((c, sig), k), s)| crate::audio_primitives::VoiceboxPatch {
                    centre_hz: *c,
                    freq_sigma_hz: *sig,
                    kind: k.clone(),
                    is_sibilant: *s,
                },
            )
            .collect();
        let audio = crate::audio_primitives::synthesize_klatt_lf(
            &trajectory,
            &patches,
            spp,
            output_samples,
            sample_rate,
            f0_hz,
            oq,
            am,
            ta_frac,
            nasal_f,
            nasal_bw,
        );
        let mut bytes: Vec<u8> = Vec::with_capacity(audio.len() * 4);
        for v in &audio {
            bytes.extend_from_slice(&v.to_le_bytes());
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &bytes))
    }

    /// Source-filter synthesis driven by per-frame FORMANT TRACKS (the agent's
    /// production forward model in faithful source-filter form: LF glottal source
    /// clock at f0 -> Klatt cascade set to the formant frequencies). The formant /
    /// bandwidth tracks come from the agent's phonetic knowledge (formant tables
    /// interpolated over a word's phoneme sequence). NO net, NO fit.
    ///
    /// `formants_flat` / `bandwidths_flat` are n_frames * n_formants, frame-major.
    /// `voiced` and `amp` are n_frames. Returns f32 PCM little-endian bytes.
    #[pyo3(signature = (formants_flat, bandwidths_flat, voiced, amp, n_formants,
                        output_samples, sample_rate, f0_hz,
                        oq=0.6, am=0.7, ta_frac=0.01))]
    #[allow(clippy::too_many_arguments)]
    fn synthesize_formant_track<'py>(
        &mut self,
        py: Python<'py>,
        formants_flat: Vec<f32>,
        bandwidths_flat: Vec<f32>,
        voiced: Vec<f32>,
        amp: Vec<f32>,
        n_formants: usize,
        output_samples: usize,
        sample_rate: u32,
        f0_hz: f32,
        oq: f32,
        am: f32,
        ta_frac: f32,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let audio = crate::audio_primitives::synthesize_formant_track(
            &formants_flat,
            &bandwidths_flat,
            &voiced,
            &amp,
            n_formants,
            output_samples,
            sample_rate,
            f0_hz,
            oq,
            am,
            ta_frac,
        );
        let mut bytes: Vec<u8> = Vec::with_capacity(audio.len() * 4);
        for v in &audio {
            bytes.extend_from_slice(&v.to_le_bytes());
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &bytes))
    }

    /// Cochlear-nucleus pass: take a raw f32 PCM buffer + a list of
    /// gammatone band centres, run the full Rust biology-aligned
    /// pipeline (gammatone filtering → hair-cell envelope → onset
    /// detection per band → cross-band coincidence) and write the
    /// resulting graph nodes into the substrate under the given
    /// AudioStream. Returns a summary dict with the counts.
    ///
    /// Samples arrive as PyBytes interpreted as little-endian f32.
    /// The caller does ``samples.astype(np.float32).tobytes()``.
    #[pyo3(signature = (audio_stream, samples, sample_rate, band_centres,
                          envelope_lp_hz=50.0, onset_threshold_db=6.0,
                          onset_refractory_ms=30.0,
                          broadband_coincidence=0.4,
                          broadband_window_ms=25.0))]
    fn cochlear_nucleus_process<'py>(
        &mut self,
        py: Python<'py>,
        audio_stream: PyRef<'_, PyNodeID>,
        samples: &Bound<'_, pyo3::types::PyBytes>,
        sample_rate: u32,
        band_centres: Vec<f32>,
        envelope_lp_hz: f32,
        onset_threshold_db: f32,
        onset_refractory_ms: f32,
        broadband_coincidence: f32,
        broadband_window_ms: f32,
    ) -> PyResult<Bound<'py, PyDict>> {
        let raw = samples.as_bytes();
        if raw.len() % 4 != 0 {
            return Err(PyValueError::new_err(
                "samples PyBytes length must be a multiple of 4 (f32)",
            ));
        }
        // Reinterpret raw bytes as f32 LE — `from_le_bytes` per
        // chunk avoids the alignment requirement of a transmute.
        let n_samples = raw.len() / 4;
        let mut buf = Vec::with_capacity(n_samples);
        for i in 0..n_samples {
            let off = i * 4;
            buf.push(f32::from_le_bytes([
                raw[off],
                raw[off + 1],
                raw[off + 2],
                raw[off + 3],
            ]));
        }
        let config = crate::cochlear_nucleus::CnConfig {
            envelope_lp_hz,
            onset_threshold_db,
            onset_refractory_ms,
            broadband_coincidence,
            broadband_window_ms,
        };
        let stream_nid = audio_stream.to_node();
        let summary = {
            let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
            let inner = &mut *__substrate_guard;
            crate::cochlear_nucleus::process_audio(
                inner,
                stream_nid,
                &buf,
                sample_rate,
                &band_centres,
                &config,
            )
        };
        let out = PyDict::new_bound(py);
        out.set_item("onsets", summary.onsets)?;
        out.set_item("envelopes", summary.envelopes)?;
        out.set_item("broadband", summary.broadband)?;
        Ok(out)
    }

    /// Inferior-colliculus pass: modulation-rate analysis above the
    /// cochlear-nucleus envelope output. For each (cochlear band,
    /// modulation rate) pair, bandpass the envelope, extract its
    /// envelope-of-envelope, peak-pick → ModulationEvent nodes; then
    /// cluster syllable-rate (4–8 Hz by default) events across bands
    /// → SyllableNucleus nodes. All output is graph data under the
    /// given AudioStream.
    #[pyo3(signature = (audio_stream, samples, sample_rate, band_centres,
                          modulation_rates_hz,
                          envelope_lp_hz=50.0, mod_q=2.0,
                          peak_threshold_db=4.0,
                          peak_refractory_ms=80.0,
                          syllable_coincidence=0.4,
                          syllable_window_ms=60.0,
                          syllable_low_hz=4.0,
                          syllable_high_hz=8.0))]
    fn inferior_colliculus_process<'py>(
        &mut self,
        py: Python<'py>,
        audio_stream: PyRef<'_, PyNodeID>,
        samples: &Bound<'_, pyo3::types::PyBytes>,
        sample_rate: u32,
        band_centres: Vec<f32>,
        modulation_rates_hz: Vec<f32>,
        envelope_lp_hz: f32,
        mod_q: f32,
        peak_threshold_db: f32,
        peak_refractory_ms: f32,
        syllable_coincidence: f32,
        syllable_window_ms: f32,
        syllable_low_hz: f32,
        syllable_high_hz: f32,
    ) -> PyResult<Bound<'py, PyDict>> {
        let raw = samples.as_bytes();
        if raw.len() % 4 != 0 {
            return Err(PyValueError::new_err(
                "samples PyBytes length must be a multiple of 4 (f32)",
            ));
        }
        let n_samples = raw.len() / 4;
        let mut buf = Vec::with_capacity(n_samples);
        for i in 0..n_samples {
            let off = i * 4;
            buf.push(f32::from_le_bytes([
                raw[off],
                raw[off + 1],
                raw[off + 2],
                raw[off + 3],
            ]));
        }
        let config = crate::inferior_colliculus::IcConfig {
            envelope_lp_hz,
            mod_q,
            peak_threshold_db,
            peak_refractory_ms,
            syllable_coincidence,
            syllable_window_ms,
            syllable_low_hz,
            syllable_high_hz,
        };
        let stream_nid = audio_stream.to_node();
        let summary = {
            let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
            let inner = &mut *__substrate_guard;
            crate::inferior_colliculus::process_audio(
                inner,
                stream_nid,
                &buf,
                sample_rate,
                &band_centres,
                &modulation_rates_hz,
                &config,
            )
        };
        let out = PyDict::new_bound(py);
        out.set_item("channels", summary.channels)?;
        out.set_item("modulation_events", summary.modulation_events)?;
        out.set_item("syllables", summary.syllables)?;
        Ok(out)
    }

    /// A1 cortex pass: evaluate every A1Patch in the graph against
    /// the cochlear-band envelopes and write A1Response + A1Event
    /// nodes per patch under the given AudioStream. The patches are
    /// installed by the auditory_cortex seed; the caller passes
    /// their NodeIDs so the loader doesn't have to query the graph
    /// for them (a future refinement could let Rust walk the patch
    /// nodes directly).
    #[pyo3(signature = (audio_stream, samples, sample_rate, band_centres,
                          patches,
                          envelope_lp_hz=50.0,
                          peak_threshold_db=4.0,
                          peak_refractory_ms=50.0))]
    fn auditory_cortex_process<'py>(
        &mut self,
        py: Python<'py>,
        audio_stream: PyRef<'_, PyNodeID>,
        samples: &Bound<'_, pyo3::types::PyBytes>,
        sample_rate: u32,
        band_centres: Vec<f32>,
        patches: &Bound<'_, pyo3::types::PyList>,
        envelope_lp_hz: f32,
        peak_threshold_db: f32,
        peak_refractory_ms: f32,
    ) -> PyResult<Bound<'py, PyDict>> {
        let raw = samples.as_bytes();
        if raw.len() % 4 != 0 {
            return Err(PyValueError::new_err(
                "samples PyBytes length must be a multiple of 4 (f32)",
            ));
        }
        let n_samples = raw.len() / 4;
        let mut buf = Vec::with_capacity(n_samples);
        for i in 0..n_samples {
            let off = i * 4;
            buf.push(f32::from_le_bytes([
                raw[off],
                raw[off + 1],
                raw[off + 2],
                raw[off + 3],
            ]));
        }

        // Parse the patch list — each item is a dict with the
        // A1Patch's attrs + its NodeID.
        let mut specs: Vec<crate::auditory_cortex::PatchSpec> = Vec::new();
        for item in patches.iter() {
            let d = item
                .downcast::<PyDict>()
                .map_err(|_| PyValueError::new_err("each patch must be a dict"))?;
            let nid: PyRef<PyNodeID> = d
                .get_item("nid")?
                .ok_or_else(|| PyValueError::new_err("patch missing 'nid'"))?
                .extract()?;
            let name: String = d
                .get_item("name")?
                .map(|v| v.extract::<String>().unwrap_or_default())
                .unwrap_or_default();
            let kind: String = d
                .get_item("kind")?
                .map(|v| v.extract::<String>().unwrap_or_default())
                .unwrap_or_default();
            let centre_hz: f32 = d
                .get_item("centre_hz")?
                .and_then(|v| v.extract::<f32>().ok())
                .unwrap_or(1000.0);
            let freq_sigma_hz: f32 = d
                .get_item("freq_sigma_hz")?
                .and_then(|v| v.extract::<f32>().ok())
                .unwrap_or(500.0);
            let duration_ms: f32 = d
                .get_item("duration_ms")?
                .and_then(|v| v.extract::<f32>().ok())
                .unwrap_or(50.0);
            let slope_hz_per_ms: f32 = d
                .get_item("slope_hz_per_ms")?
                .and_then(|v| v.extract::<f32>().ok())
                .unwrap_or(0.0);
            specs.push(crate::auditory_cortex::PatchSpec {
                nid: nid.to_node(),
                name,
                kind,
                centre_hz,
                freq_sigma_hz,
                duration_ms,
                slope_hz_per_ms,
            });
        }

        let config = crate::auditory_cortex::AcConfig {
            envelope_lp_hz,
            peak_threshold_db,
            peak_refractory_ms,
        };
        let stream_nid = audio_stream.to_node();
        let summary = {
            let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
            let inner = &mut *__substrate_guard;
            crate::auditory_cortex::process_audio(
                inner,
                stream_nid,
                &buf,
                sample_rate,
                &band_centres,
                &specs,
                &config,
            )
        };
        let out = PyDict::new_bound(py);
        out.set_item("responses", summary.responses)?;
        out.set_item("events", summary.events)?;
        Ok(out)
    }

    /// Diagnostic: just the 2:1 area-average step (no DCT, no quant).
    /// Uses the SIMD path from h264_dct when available. Takes
    /// PyBytes by reference (zero-copy view into Python's buffer).
    fn h264_area_average_2to1<'py>(
        &self,
        py: Python<'py>,
        plane: &Bound<'_, pyo3::types::PyBytes>,
        in_w: usize,
        in_h: usize,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        use crate::h264_dct::area_average_2to1_pub;
        let plane_slice = plane.as_bytes();
        let out_w = in_w / 2;
        let out_h = in_h / 2;
        let mut out = vec![0u8; out_w * out_h];
        area_average_2to1_pub(plane_slice, in_w, out_w, out_h, &mut out);
        Ok(pyo3::types::PyBytes::new_bound(py, &out))
    }

    /// Encode a P-frame: area-average current frame to 1080p, take
    /// the difference vs the previous reconstructed reference, DCT
    /// + quantise per MB, return (mb_luma_bytes, cbp_list_bytes,
    /// skip_list_bytes, reconstructed_plane). The reconstructed
    /// plane becomes the reference for the next P-frame.
    fn h264_transcode_p_frame_2to1<'py>(
        &self,
        py: Python<'py>,
        target_plane: &Bound<'_, pyo3::types::PyBytes>,
        reference_plane: &Bound<'_, pyo3::types::PyBytes>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::h264_dct::transcode_p_frame_static_mv0;
        let tgt = target_plane.as_bytes();
        let refp = reference_plane.as_bytes();
        if tgt.len() != plane_w * plane_h || refp.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "target/reference plane size mismatch",
            ));
        }
        let (mb_luma, cbp, skip, recon) = py.allow_threads(|| {
            transcode_p_frame_static_mv0(tgt, refp, plane_w, plane_h, mb_w, mb_h, qp)
        });
        // mb_luma → LE bytes
        let mut mb_luma_bytes = Vec::with_capacity(mb_luma.len() * 4);
        for v in &mb_luma {
            mb_luma_bytes.extend_from_slice(&v.to_le_bytes());
        }
        let skip_bytes: Vec<u8> = skip
            .into_iter()
            .map(|b| if b { 1u8 } else { 0u8 })
            .collect();
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &mb_luma_bytes), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &cbp), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &skip_bytes), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &recon), py),
            ],
        ))
    }

    /// Fused sub-pel P-frame transcoder. Replaces the
    /// `h264_apply_motion_compensation(subpel=True)` → `h264_transcode_p_frame_2to1`
    /// two-step pipeline with a single pass that keeps the per-MB
    /// prediction in i32 end-to-end and clips ONLY at the final
    /// recon (§8.5.14 `clip1Y(pred + idct)`, not `clip1Y(pred)` +
    /// `clip1Y(idct + clipped_pred)`).
    ///
    /// Why fused: the two-step pipeline clips the FIR output to u8
    /// before computing the residual. When the 6-tap §8.4.2.2.1 FIR
    /// overshoots `[0, 255]` (rare, happens on cross-term `j` at
    /// high-contrast edges), the encoder loses the overshoot
    /// while the decoder keeps it. Encoder/decoder diverge by the
    /// clipping delta, and the error feeds back through the
    /// recon-as-reference chain → drift.
    ///
    /// `mv_bytes` is the same 3-LE-i32-per-MB layout as
    /// `h264_estimate_motion_gpu` / `h264_refine_motion_subpel` —
    /// but in this call the MVs are QUARTER-PEL. Use
    /// `h264_refine_motion_subpel` to upgrade integer-pel ME output.
    ///
    /// Returns `(mb_luma_bytes, cbp_bytes, skip_bytes, recon_bytes)` —
    /// drop-in compatible with `h264_transcode_p_frame_2to1`'s tuple
    /// shape so the CABAC stage doesn't need to know which path
    /// produced its inputs.
    fn h264_transcode_p_frame_2to1_subpel<'py>(
        &self,
        py: Python<'py>,
        target_plane: &Bound<'_, pyo3::types::PyBytes>,
        reference_plane: &Bound<'_, pyo3::types::PyBytes>,
        mv_bytes: &Bound<'_, pyo3::types::PyBytes>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::h264_dct::transcode_p_frame_subpel_static;
        let tgt = target_plane.as_bytes();
        let refp = reference_plane.as_bytes();
        if tgt.len() != plane_w * plane_h || refp.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "target/reference plane size mismatch",
            ));
        }
        let raw = mv_bytes.as_bytes();
        let n_mbs = mb_w * mb_h;
        if raw.len() != n_mbs * 12 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "mv_bytes must be {} bytes (3 LE i32 × {})",
                n_mbs * 12,
                n_mbs
            )));
        }
        let mut mvs = Vec::with_capacity(n_mbs);
        for i in 0..n_mbs {
            let o = i * 12;
            let mx = i32::from_le_bytes([raw[o], raw[o + 1], raw[o + 2], raw[o + 3]]);
            let my = i32::from_le_bytes([raw[o + 4], raw[o + 5], raw[o + 6], raw[o + 7]]);
            mvs.push((mx, my));
        }
        let (mb_luma, cbp, skip, recon) = py.allow_threads(|| {
            transcode_p_frame_subpel_static(tgt, refp, &mvs, plane_w, plane_h, mb_w, mb_h, qp)
        });
        let mut mb_luma_bytes = Vec::with_capacity(mb_luma.len() * 4);
        for v in &mb_luma {
            mb_luma_bytes.extend_from_slice(&v.to_le_bytes());
        }
        let skip_bytes: Vec<u8> = skip
            .into_iter()
            .map(|b| if b { 1u8 } else { 0u8 })
            .collect();
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &mb_luma_bytes), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &cbp), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &skip_bytes), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &recon), py),
            ],
        ))
    }

    /// CABAC-encode a P-slice from packed mb_luma + cbp + skip
    /// byte buffers (output of h264_transcode_p_frame_2to1).
    #[pyo3(signature = (
        mb_width, mb_height, cabac_init_idc, slice_qp,
        luma_coefs_bytes, cbp_luma_bytes, mb_skip_bytes,
        chroma=None, mvd_x_bytes=None, mvd_y_bytes=None,
    ))]
    fn h264_encode_p_slice_luma_bytes<'py>(
        &self,
        py: Python<'py>,
        mb_width: usize,
        mb_height: usize,
        cabac_init_idc: u8,
        slice_qp: i32,
        luma_coefs_bytes: &Bound<'_, pyo3::types::PyBytes>,
        cbp_luma_bytes: &Bound<'_, pyo3::types::PyBytes>,
        mb_skip_bytes: &Bound<'_, pyo3::types::PyBytes>,
        chroma: Option<&Bound<'_, pyo3::types::PyDict>>,
        mvd_x_bytes: Option<&Bound<'_, pyo3::types::PyBytes>>,
        mvd_y_bytes: Option<&Bound<'_, pyo3::types::PyBytes>>,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        use crate::cabac::{encode_p_slice_from_mb_luma, PSliceChromaResiduals};
        let n_mbs = mb_width * mb_height;
        let raw = luma_coefs_bytes.as_bytes();
        if raw.len() != n_mbs * 256 * 4 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "luma_coefs_bytes must be {} bytes",
                n_mbs * 256 * 4
            )));
        }
        let cbp = cbp_luma_bytes.as_bytes();
        let skip = mb_skip_bytes.as_bytes();
        if cbp.len() != n_mbs || skip.len() != n_mbs {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "cbp/skip byte length mismatch",
            ));
        }
        // Decode mb_luma bytes → Vec<i32>
        let mut mb_luma_i32 = vec![0i32; n_mbs * 256];
        for i in 0..n_mbs * 256 {
            let off = i * 4;
            mb_luma_i32[i] =
                i32::from_le_bytes([raw[off], raw[off + 1], raw[off + 2], raw[off + 3]]);
        }
        let cbp_vec: Vec<u8> = cbp.to_vec();
        let skip_vec: Vec<bool> = skip.iter().map(|&b| b != 0).collect();

        // Optional chroma residuals. Each LE-packed i32 buffer is
        // expected at a fixed flat layout per MB count.
        let chroma_buffers: Option<(Vec<u8>, Vec<i32>, Vec<i32>, Vec<i32>, Vec<i32>)>;
        let chroma_ref: Option<PSliceChromaResiduals>;
        if let Some(d) = chroma {
            let get = |k: &str| -> PyResult<Vec<u8>> {
                let v = d.get_item(k)?.ok_or_else(|| {
                    pyo3::exceptions::PyValueError::new_err(format!("chroma dict missing '{}'", k))
                })?;
                let b: &Bound<pyo3::types::PyBytes> =
                    v.downcast::<pyo3::types::PyBytes>().map_err(|_| {
                        pyo3::exceptions::PyValueError::new_err(format!(
                            "chroma['{}'] must be bytes",
                            k
                        ))
                    })?;
                Ok(b.as_bytes().to_vec())
            };
            let cbp_c = get("cbp_chroma")?;
            if cbp_c.len() != n_mbs {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "cbp_chroma must be {} bytes",
                    n_mbs
                )));
            }
            let parse_i32 = |label: &str, expected_count: usize| -> PyResult<Vec<i32>> {
                let raw = get(label)?;
                if raw.len() != expected_count * 4 {
                    return Err(pyo3::exceptions::PyValueError::new_err(format!(
                        "{} must be {} bytes (LE i32 x {})",
                        label,
                        expected_count * 4,
                        expected_count
                    )));
                }
                let mut v = vec![0i32; expected_count];
                for i in 0..expected_count {
                    let o = i * 4;
                    v[i] = i32::from_le_bytes([raw[o], raw[o + 1], raw[o + 2], raw[o + 3]]);
                }
                Ok(v)
            };
            let dc_cb = parse_i32("chroma_dc_cb", n_mbs * 4)?;
            let dc_cr = parse_i32("chroma_dc_cr", n_mbs * 4)?;
            let ac_cb = parse_i32("chroma_ac_cb", n_mbs * 60)?;
            let ac_cr = parse_i32("chroma_ac_cr", n_mbs * 60)?;
            chroma_buffers = Some((cbp_c, dc_cb, dc_cr, ac_cb, ac_cr));
            let (cb_c, dc_cb_r, dc_cr_r, ac_cb_r, ac_cr_r) = chroma_buffers.as_ref().unwrap();
            chroma_ref = Some(PSliceChromaResiduals {
                cbp_chroma_list: cb_c,
                chroma_dc_cb: dc_cb_r,
                chroma_dc_cr: dc_cr_r,
                chroma_ac_cb: ac_cb_r,
                chroma_ac_cr: ac_cr_r,
            });
        } else {
            chroma_buffers = None;
            chroma_ref = None;
        }
        // Optional per-MB MVDs (LE-packed i16, n_mbs each). Both
        // axes must be provided together or neither.
        let mvd_buffers: Option<(Vec<i16>, Vec<i16>)>;
        let mvd_ref: Option<(&[i16], &[i16])>;
        match (mvd_x_bytes, mvd_y_bytes) {
            (Some(xb), Some(yb)) => {
                let xb_raw = xb.as_bytes();
                let yb_raw = yb.as_bytes();
                if xb_raw.len() != n_mbs * 2 || yb_raw.len() != n_mbs * 2 {
                    return Err(pyo3::exceptions::PyValueError::new_err(format!(
                        "mvd_x/y_bytes must be {} bytes (LE i16 x {})",
                        n_mbs * 2,
                        n_mbs
                    )));
                }
                let mut mx = vec![0i16; n_mbs];
                let mut my = vec![0i16; n_mbs];
                for i in 0..n_mbs {
                    mx[i] = i16::from_le_bytes([xb_raw[i * 2], xb_raw[i * 2 + 1]]);
                    my[i] = i16::from_le_bytes([yb_raw[i * 2], yb_raw[i * 2 + 1]]);
                }
                mvd_buffers = Some((mx, my));
            }
            (None, None) => {
                mvd_buffers = None;
            }
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "mvd_x_bytes and mvd_y_bytes must be provided together",
                ));
            }
        }
        mvd_ref = mvd_buffers
            .as_ref()
            .map(|(mx, my)| (mx.as_slice(), my.as_slice()));
        let payload = encode_p_slice_from_mb_luma(
            &mb_luma_i32,
            &cbp_vec,
            &skip_vec,
            mb_width,
            mb_height,
            cabac_init_idc,
            slice_qp,
            chroma_ref.as_ref(),
            mvd_ref,
        );
        let _ = chroma_buffers; // keep alive for the call
        let _ = mvd_buffers;
        Ok(pyo3::types::PyBytes::new_bound(py, &payload))
    }

    /// Multi-slice parallel P-slice encoder. Splits the picture into
    /// `n_slices` row-aligned slices and encodes each in its own
    /// thread (std::thread::scope). Slices are independent CABAC
    /// streams — no cross-slice neighbour state. Returns a list of
    /// (first_mb_in_slice, cabac_payload_bytes) per slice in raster
    /// order; caller wraps each in its own slice NAL.
    ///
    /// Same input shape as h264_encode_p_slice_luma_bytes.
    #[pyo3(signature = (
        mb_width, mb_height, cabac_init_idc, slice_qp, n_slices,
        luma_coefs_bytes, cbp_luma_bytes, mb_skip_bytes,
        chroma=None, mvd_x_bytes=None, mvd_y_bytes=None,
    ))]
    fn h264_encode_p_slice_multi_bytes<'py>(
        &self,
        py: Python<'py>,
        mb_width: usize,
        mb_height: usize,
        cabac_init_idc: u8,
        slice_qp: i32,
        n_slices: usize,
        luma_coefs_bytes: &Bound<'_, pyo3::types::PyBytes>,
        cbp_luma_bytes: &Bound<'_, pyo3::types::PyBytes>,
        mb_skip_bytes: &Bound<'_, pyo3::types::PyBytes>,
        chroma: Option<&Bound<'_, pyo3::types::PyDict>>,
        mvd_x_bytes: Option<&Bound<'_, pyo3::types::PyBytes>>,
        mvd_y_bytes: Option<&Bound<'_, pyo3::types::PyBytes>>,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::cabac::{encode_p_slice_multi, PSliceChromaResiduals};
        let n_mbs = mb_width * mb_height;
        let raw = luma_coefs_bytes.as_bytes();
        if raw.len() != n_mbs * 256 * 4 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "luma_coefs_bytes must be {} bytes",
                n_mbs * 256 * 4
            )));
        }
        let cbp = cbp_luma_bytes.as_bytes();
        let skip = mb_skip_bytes.as_bytes();
        if cbp.len() != n_mbs || skip.len() != n_mbs {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "cbp/skip byte length mismatch",
            ));
        }
        let mut mb_luma_i32 = vec![0i32; n_mbs * 256];
        for i in 0..n_mbs * 256 {
            let off = i * 4;
            mb_luma_i32[i] =
                i32::from_le_bytes([raw[off], raw[off + 1], raw[off + 2], raw[off + 3]]);
        }
        let cbp_vec: Vec<u8> = cbp.to_vec();
        let skip_vec: Vec<bool> = skip.iter().map(|&b| b != 0).collect();

        let chroma_buffers: Option<(Vec<u8>, Vec<i32>, Vec<i32>, Vec<i32>, Vec<i32>)>;
        let chroma_ref: Option<PSliceChromaResiduals>;
        if let Some(d) = chroma {
            let get = |k: &str| -> PyResult<Vec<u8>> {
                let v = d.get_item(k)?.ok_or_else(|| {
                    pyo3::exceptions::PyValueError::new_err(format!("chroma dict missing '{}'", k))
                })?;
                let b: &Bound<pyo3::types::PyBytes> =
                    v.downcast::<pyo3::types::PyBytes>().map_err(|_| {
                        pyo3::exceptions::PyValueError::new_err(format!(
                            "chroma['{}'] must be bytes",
                            k
                        ))
                    })?;
                Ok(b.as_bytes().to_vec())
            };
            let cbp_c = get("cbp_chroma")?;
            let parse_i32 = |label: &str, expected: usize| -> PyResult<Vec<i32>> {
                let raw = get(label)?;
                if raw.len() != expected * 4 {
                    return Err(pyo3::exceptions::PyValueError::new_err(format!(
                        "{} length mismatch",
                        label
                    )));
                }
                let mut v = vec![0i32; expected];
                for i in 0..expected {
                    let o = i * 4;
                    v[i] = i32::from_le_bytes([raw[o], raw[o + 1], raw[o + 2], raw[o + 3]]);
                }
                Ok(v)
            };
            let dc_cb = parse_i32("chroma_dc_cb", n_mbs * 4)?;
            let dc_cr = parse_i32("chroma_dc_cr", n_mbs * 4)?;
            let ac_cb = parse_i32("chroma_ac_cb", n_mbs * 60)?;
            let ac_cr = parse_i32("chroma_ac_cr", n_mbs * 60)?;
            chroma_buffers = Some((cbp_c, dc_cb, dc_cr, ac_cb, ac_cr));
            let (cb_c, dc_cb_r, dc_cr_r, ac_cb_r, ac_cr_r) = chroma_buffers.as_ref().unwrap();
            chroma_ref = Some(PSliceChromaResiduals {
                cbp_chroma_list: cb_c,
                chroma_dc_cb: dc_cb_r,
                chroma_dc_cr: dc_cr_r,
                chroma_ac_cb: ac_cb_r,
                chroma_ac_cr: ac_cr_r,
            });
        } else {
            chroma_buffers = None;
            chroma_ref = None;
        }

        let mvd_buffers: Option<(Vec<i16>, Vec<i16>)>;
        let mvd_ref: Option<(&[i16], &[i16])>;
        match (mvd_x_bytes, mvd_y_bytes) {
            (Some(xb), Some(yb)) => {
                let xb_raw = xb.as_bytes();
                let yb_raw = yb.as_bytes();
                if xb_raw.len() != n_mbs * 2 || yb_raw.len() != n_mbs * 2 {
                    return Err(pyo3::exceptions::PyValueError::new_err(
                        "mvd bytes length mismatch",
                    ));
                }
                let mut mx = vec![0i16; n_mbs];
                let mut my = vec![0i16; n_mbs];
                for i in 0..n_mbs {
                    mx[i] = i16::from_le_bytes([xb_raw[i * 2], xb_raw[i * 2 + 1]]);
                    my[i] = i16::from_le_bytes([yb_raw[i * 2], yb_raw[i * 2 + 1]]);
                }
                mvd_buffers = Some((mx, my));
            }
            (None, None) => mvd_buffers = None,
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(
                    "mvd_x_bytes and mvd_y_bytes must be provided together",
                ))
            }
        }
        mvd_ref = mvd_buffers
            .as_ref()
            .map(|(x, y)| (x.as_slice(), y.as_slice()));

        let slices = py.allow_threads(|| {
            encode_p_slice_multi(
                &mb_luma_i32,
                &cbp_vec,
                &skip_vec,
                mb_width,
                mb_height,
                cabac_init_idc,
                slice_qp,
                chroma_ref.as_ref(),
                mvd_ref,
                n_slices,
            )
        });
        let _ = chroma_buffers;
        let _ = mvd_buffers;
        let out = pyo3::types::PyList::empty_bound(py);
        for (first_mb, payload) in slices {
            let tup = pyo3::types::PyTuple::new_bound(
                py,
                &[
                    pyo3::IntoPy::into_py(first_mb, py),
                    pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &payload), py),
                ],
            );
            out.append(tup)?;
        }
        Ok(out)
    }

    /// GPU-accelerated motion estimation. Returns one (mv_x, mv_y,
    /// sad) triple per macroblock in raster order, with MVs in
    /// integer LUMA pixels (multiply by 4 for quarter-pel H.264 mvd).
    ///
    /// `search_radius` is in luma pixels.
    /// `mode`: "full" (exhaustive SAD, bit-exact global optimum) or
    ///         "hex"  (hex+diamond refinement, much faster).
    ///
    /// The wgpu context is initialised lazily on first call and
    /// reused for every subsequent invocation (~30 ms one-time cost).
    ///
    /// ASYNC PIPELINING: see `h264_submit_motion_gpu` for the
    /// non-blocking variant that returns a handle. Submit frame N+1
    /// before waiting on frame N's handle to hide the ~10 ms GPU
    /// dispatch + readback latency behind CPU work on frame N.
    #[cfg(feature = "gpu_me")]
    #[pyo3(signature = (
        target_plane, reference_plane, plane_w, plane_h, mb_w, mb_h,
        search_radius, mode = "full",
    ))]
    fn h264_estimate_motion_gpu<'py>(
        &self,
        py: Python<'py>,
        target_plane: &Bound<'_, pyo3::types::PyBytes>,
        reference_plane: &Bound<'_, pyo3::types::PyBytes>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        search_radius: u32,
        mode: &str,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        use crate::gpu_me::{shared, SearchMode};
        let tgt = target_plane.as_bytes();
        let refp = reference_plane.as_bytes();
        if tgt.len() != plane_w * plane_h || refp.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "plane size mismatch",
            ));
        }
        let m = match mode {
            "full" => SearchMode::Full,
            "hex" => SearchMode::Hex,
            other => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "mode must be 'full' or 'hex', got '{}'",
                    other
                )))
            }
        };
        let ctx = shared().map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!("gpu init failed: {}", e))
        })?;
        let mvs = py
            .allow_threads(|| {
                ctx.estimate_with_mode(tgt, refp, plane_w, plane_h, mb_w, mb_h, search_radius, m)
            })
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))?;
        let mut out = Vec::with_capacity(mvs.len() * 12);
        for m in &mvs {
            out.extend_from_slice(&m.mv_x.to_le_bytes());
            out.extend_from_slice(&m.mv_y.to_le_bytes());
            out.extend_from_slice(&(m.sad as i32).to_le_bytes());
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &out))
    }

    /// Submit a GPU motion-estimation job and IMMEDIATELY return a
    /// handle. The GPU compute runs in the background. Caller invokes
    /// `.wait()` on the handle to retrieve the (mv_x, mv_y, sad)
    /// LE-i32 triples per macroblock, blocking only if the GPU work
    /// isn't yet done.
    ///
    /// Pattern (hides the ~10 ms GPU dispatch behind CPU work):
    ///     h = s.h264_submit_motion_gpu(targets[1], refs[1], ...)
    ///     for i in range(1, N):
    ///         h_next = (s.h264_submit_motion_gpu(targets[i+1], ...)
    ///                   if i + 1 < N else None)
    ///         mvs = h.wait()
    ///         do_cpu_work(mvs)   # overlaps with h_next's GPU compute
    ///         h = h_next
    #[cfg(feature = "gpu_me")]
    #[pyo3(signature = (
        target_plane, reference_plane, plane_w, plane_h, mb_w, mb_h,
        search_radius, mode = "full",
    ))]
    fn h264_submit_motion_gpu(
        &self,
        target_plane: &Bound<'_, pyo3::types::PyBytes>,
        reference_plane: &Bound<'_, pyo3::types::PyBytes>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        search_radius: u32,
        mode: &str,
    ) -> PyResult<GpuMeHandle> {
        use crate::gpu_me::{shared, SearchMode};
        let tgt = target_plane.as_bytes();
        let refp = reference_plane.as_bytes();
        if tgt.len() != plane_w * plane_h || refp.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "plane size mismatch",
            ));
        }
        let m = match mode {
            "full" => SearchMode::Full,
            "hex" => SearchMode::Hex,
            other => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "mode must be 'full' or 'hex', got '{}'",
                    other
                )))
            }
        };
        let ctx = shared().map_err(|e| {
            pyo3::exceptions::PyRuntimeError::new_err(format!("gpu init failed: {}", e))
        })?;
        let handle = ctx
            .submit_async(tgt, refp, plane_w, plane_h, mb_w, mb_h, search_radius, m)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e))?;
        Ok(GpuMeHandle {
            inner: Some(handle),
        })
    }

    /// Sub-pel luma interpolation per H.264 §8.4.2.2.1 — the spec-
    /// exact 6-tap FIR + ¼-pel positions. Wraps the vendored
    /// OxideAV/oxideav-h264 `interpolate_luma` kernel (MIT, see
    /// NOTICES.md). For a block of size `(w, h)` at integer position
    /// (`int_x`, `int_y`) with fractional position (`x_frac`, `y_frac`),
    /// fills `dst_w * dst_h` bytes of output. `x_frac` and `y_frac`
    /// are 0..=3 (quarter-pel).
    ///
    /// Returns a Vec<u8> of length w*h.
    fn h264_interpolate_luma_subpel<'py>(
        &self,
        py: Python<'py>,
        reference: &Bound<'_, pyo3::types::PyBytes>,
        src_w: usize,
        src_h: usize,
        int_x: i32,
        int_y: i32,
        x_frac: u8,
        y_frac: u8,
        block_w: u32,
        block_h: u32,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        use crate::h264_inter_pred::interpolate_luma;
        let r = reference.as_bytes();
        if r.len() != src_w * src_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "reference plane size mismatch",
            ));
        }
        // The vendored kernel works in i32 to keep 6-tap intermediates
        // representable without overflow; expand the u8 plane on entry.
        let src_i32: Vec<i32> = r.iter().map(|&b| b as i32).collect();
        let bh = block_h as usize;
        let bw = block_w as usize;
        let mut dst = vec![0i32; bw * bh];
        interpolate_luma(
            &src_i32, src_w, src_w, src_h, int_x, int_y, x_frac, y_frac, block_w, block_h,
            /*bit_depth=*/ 8, &mut dst, bw,
        )
        .map_err(|e| {
            pyo3::exceptions::PyValueError::new_err(format!("interpolate_luma failed: {}", e))
        })?;
        let out: Vec<u8> = dst.iter().map(|&v| v.clamp(0, 255) as u8).collect();
        Ok(pyo3::types::PyBytes::new_bound(py, &out))
    }

    /// Build a motion-compensated reference plane by reading the
    /// supplied reference at per-MB integer-luma offsets. `mv_bytes`
    /// is the same LE i32 triples (mv_x, mv_y, sad) layout produced
    /// by h264_estimate_motion_gpu / _cpu; only the first two
    /// components are used.
    ///
    /// Returns a plane the same size as `reference`; the caller
    /// hands it to h264_transcode_p_frame_2to1 as the reference,
    /// which then computes residual = target - mc_ref at MV=(0,0).
    /// `subpel=False` (default, back-compat): MVs in `mv_bytes` are in
    /// INTEGER luma pixels (what `h264_estimate_motion_gpu` returns).
    ///
    /// `subpel=True`: MVs are QUARTER luma pixels. Each MB's MV is
    /// decomposed (`int = mv >> 2`, `frac = mv & 3`); when frac is
    /// non-zero the per-MB block is produced by the vendored
    /// `interpolate_luma` 6-tap FIR (§8.4.2.2.1, see NOTICES.md).
    #[pyo3(signature = (
        reference_plane, mv_bytes, plane_w, plane_h, mb_w, mb_h,
        subpel = false,
    ))]
    fn h264_apply_motion_compensation<'py>(
        &self,
        py: Python<'py>,
        reference_plane: &Bound<'_, pyo3::types::PyBytes>,
        mv_bytes: &Bound<'_, pyo3::types::PyBytes>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        subpel: bool,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let refp = reference_plane.as_bytes();
        if refp.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "reference plane size mismatch",
            ));
        }
        let raw = mv_bytes.as_bytes();
        let n_mbs = mb_w * mb_h;
        if raw.len() != n_mbs * 12 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "mv_bytes must be {} bytes (3 LE i32 × {})",
                n_mbs * 12,
                n_mbs
            )));
        }
        let mut mvs = Vec::with_capacity(n_mbs);
        for i in 0..n_mbs {
            let o = i * 12;
            let mx = i32::from_le_bytes([raw[o], raw[o + 1], raw[o + 2], raw[o + 3]]);
            let my = i32::from_le_bytes([raw[o + 4], raw[o + 5], raw[o + 6], raw[o + 7]]);
            mvs.push((mx, my));
        }
        let out = py.allow_threads(|| {
            apply_motion_compensation_kernel(refp, &mvs, plane_w, plane_h, mb_w, mb_h, subpel)
        });
        Ok(pyo3::types::PyBytes::new_bound(py, &out))
    }

    /// CPU reference implementation of the same SAD search — for
    /// parity testing the GPU output. Same return packing.
    fn h264_estimate_motion_cpu<'py>(
        &self,
        py: Python<'py>,
        target_plane: &Bound<'_, pyo3::types::PyBytes>,
        reference_plane: &Bound<'_, pyo3::types::PyBytes>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        search_radius: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let tgt = target_plane.as_bytes();
        let refp = reference_plane.as_bytes();
        if tgt.len() != plane_w * plane_h || refp.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "plane size mismatch",
            ));
        }
        let mvs = py.allow_threads(|| {
            estimate_motion_cpu_kernel(tgt, refp, plane_w, plane_h, mb_w, mb_h, search_radius)
        });
        let mut out = Vec::with_capacity(mvs.len() * 12);
        for m in &mvs {
            out.extend_from_slice(&m.0.to_le_bytes());
            out.extend_from_slice(&m.1.to_le_bytes());
            out.extend_from_slice(&m.2.to_le_bytes());
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &out))
    }

    /// Direct intra-predict + quant for an already-downsampled luma
    /// plane — skips the `area_average_2to1` step that
    /// `h264_transcode_2to1_luma_with_recon` does first. Use this when
    /// the caller has the 1920×1088 (or whatever MB-aligned size)
    /// luma plane already and doesn't need the 2:1 downsample applied
    /// internally. Returns the same `(mb_luma_bytes, recon_bytes)`
    /// tuple shape so callers can swap one for the other.
    fn h264_intra_predict_and_quantise_with_recon<'py>(
        &self,
        py: Python<'py>,
        plane: &Bound<'_, pyo3::types::PyBytes>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::h264_dct::intra_predict_and_quantise_slice_with_recon;
        let p = plane.as_bytes();
        if p.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "plane len {} != plane_w*plane_h ({})",
                p.len(),
                plane_w * plane_h
            )));
        }
        if mb_w * 16 != plane_w || mb_h * 16 != plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "mb_w*16 must equal plane_w and mb_h*16 must equal plane_h",
            ));
        }
        let (mb_luma, recon) = py.allow_threads(|| {
            intra_predict_and_quantise_slice_with_recon(p, plane_w, plane_h, mb_w, mb_h, qp)
        });
        let mut mb_bytes = Vec::with_capacity(mb_luma.len() * 4);
        for v in &mb_luma {
            mb_bytes.extend_from_slice(&v.to_le_bytes());
        }
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &mb_bytes), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &recon), py),
            ],
        ))
    }

    /// One-shot Rust kernel that does both skip-detection (spec-safe:
    /// cbp==0 ∧ MV==0 ∧ median-predictor==0) and MVD computation in a
    /// single MB-grid traversal. Replaces the per-bench Python double-
    /// loop that was costing ~75 ms / 8-frame run at 1920×1088
    /// (8160 MBs × O(few-list-ops) iterations is dominated by Python
    /// interpreter overhead, not the math).
    ///
    /// `mv_bytes`: same 12-byte-per-MB layout produced by
    ///   `h264_estimate_motion_gpu` / `h264_refine_motion_subpel`.
    /// `cbp_bytes`: one u8 per MB (8x8 CBP nibble in low 4 bits).
    /// `slice_row_starts`: list of first-MB-row indices for each
    ///   slice (multi-slice predictor must treat rows above a slice
    ///   boundary as unavailable).
    /// `qp_input`: false → MVs are integer-pel and get scaled ×4
    ///   internally before predictor math; true → MVs are already
    ///   quarter-pel (sub-pel refinement output).
    ///
    /// Returns `(skip_bytes, mvd_x_bytes, mvd_y_bytes)`:
    ///   skip_bytes is one u8 per MB (1 = skip).
    ///   mvd_{x,y}_bytes are 2 bytes per MB (LE i16).
    fn h264_compute_skip_and_mvds<'py>(
        &self,
        py: Python<'py>,
        mv_bytes: &Bound<'_, pyo3::types::PyBytes>,
        cbp_bytes: &Bound<'_, pyo3::types::PyBytes>,
        mb_w: usize,
        mb_h: usize,
        slice_row_starts: Vec<usize>,
        qp_input: bool,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        let raw = mv_bytes.as_bytes();
        let cbp = cbp_bytes.as_bytes();
        let n_mbs = mb_w * mb_h;
        if raw.len() != n_mbs * 12 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "mv_bytes must be {} bytes",
                n_mbs * 12
            )));
        }
        if cbp.len() != n_mbs {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "cbp_bytes must be {} bytes",
                n_mbs
            )));
        }
        let mv_scale: i32 = if qp_input { 1 } else { 4 };
        let slice_set: std::collections::HashSet<usize> =
            slice_row_starts.iter().copied().collect();

        let mut skip = vec![0u8; n_mbs];
        let mut mvd_x = vec![0u8; 2 * n_mbs];
        let mut mvd_y = vec![0u8; 2 * n_mbs];
        // Grid of post-scale per-MB MVs in QP, used for predictor lookups.
        let mut grid: Vec<Option<(i32, i32)>> = vec![None; n_mbs];

        let median3 = |a: i32, b: i32, c: i32| -> i32 {
            let mut v = [a, b, c];
            v.sort_unstable();
            v[1]
        };

        for r in 0..mb_h {
            let row_starts_slice = slice_set.contains(&r);
            for c in 0..mb_w {
                let j = r * mb_w + c;
                let o = j * 12;
                let mx = i32::from_le_bytes([raw[o], raw[o + 1], raw[o + 2], raw[o + 3]]);
                let my = i32::from_le_bytes([raw[o + 4], raw[o + 5], raw[o + 6], raw[o + 7]]);
                let mv_qp = (mx * mv_scale, my * mv_scale);
                let top_avail = r > 0 && !row_starts_slice;
                let a = if c > 0 {
                    grid[r * mb_w + (c - 1)]
                } else {
                    None
                };
                let b = if top_avail {
                    grid[(r - 1) * mb_w + c]
                } else {
                    None
                };
                let cc = if top_avail && c + 1 < mb_w {
                    grid[(r - 1) * mb_w + (c + 1)]
                } else if top_avail && c > 0 {
                    grid[(r - 1) * mb_w + (c - 1)]
                } else {
                    None
                };
                let avail_count = a.is_some() as i32 + b.is_some() as i32 + cc.is_some() as i32;
                let pred = match avail_count {
                    0 => (0, 0),
                    1 => a.or(b).or(cc).unwrap(),
                    _ => {
                        let (ax, ay) = a.unwrap_or((0, 0));
                        let (bx, by) = b.unwrap_or((0, 0));
                        let (cx, cy) = cc.unwrap_or((0, 0));
                        (median3(ax, bx, cx), median3(ay, by, cy))
                    }
                };
                if (cbp[j] & 0x0F) == 0 && mv_qp == (0, 0) && pred == (0, 0) {
                    skip[j] = 1;
                }
                let dx = (mv_qp.0 - pred.0) as i16;
                let dy = (mv_qp.1 - pred.1) as i16;
                mvd_x[j * 2] = (dx as u16 & 0xFF) as u8;
                mvd_x[j * 2 + 1] = ((dx as u16 >> 8) & 0xFF) as u8;
                mvd_y[j * 2] = (dy as u16 & 0xFF) as u8;
                mvd_y[j * 2 + 1] = ((dy as u16 >> 8) & 0xFF) as u8;
                grid[j] = Some(mv_qp);
            }
        }
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &skip), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &mvd_x), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &mvd_y), py),
            ],
        ))
    }

    /// H.264 emulation-prevention byte insertion (§7.4.1.1). Walks
    /// the RBSP and inserts a 0x03 byte whenever a byte ≤ 0x03 would
    /// otherwise follow two consecutive zeros in the output stream.
    ///
    /// Replaces the pure-Python `rbsp_to_ebsp` (which the profile shows
    /// eating ~54 % of `encode_with_ours` total wall-clock; the
    /// 8160-MB-per-frame Python `for b in rbsp` loop is the bottleneck).
    /// The Rust version walks the byte slice with a tiny state machine
    /// and pre-reserves an output Vec sized for the worst case
    /// (1 extra byte per 2 input zeros).
    fn h264_rbsp_to_ebsp<'py>(
        &self,
        py: Python<'py>,
        rbsp: &Bound<'_, pyo3::types::PyBytes>,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let bytes = rbsp.as_bytes();
        let mut out = Vec::with_capacity(bytes.len() + bytes.len() / 4);
        let mut zero_count: u32 = 0;
        for &b in bytes {
            if zero_count >= 2 && b <= 0x03 {
                out.push(0x03);
                zero_count = 0;
            }
            out.push(b);
            if b == 0 {
                zero_count += 1;
            } else {
                zero_count = 0;
            }
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &out))
    }

    /// Sub-pel refinement pass over integer-pel MVs. Given a buffer of
    /// integer-pel `(mv_x, mv_y, sad)` triples (the format
    /// `h264_estimate_motion_gpu` / `_cpu` returns), runs a two-phase
    /// half-pel→quarter-pel diamond search per MB and returns
    /// QUARTER-PEL `(qmv_x, qmv_y, sad)` triples in the same byte
    /// layout (12 bytes/MB, 3 LE i32).
    ///
    /// Worst case: 17 SAD evaluations per MB (1 integer baseline + 8
    /// half-pel + 8 quarter-pel). Sub-pel SADs are computed against
    /// the vendored 6-tap FIR (`h264_inter_pred::interpolate_luma`,
    /// §8.4.2.2.1, MIT — see `NOTICES.md`). Released without the GIL.
    ///
    /// Callers should:
    ///   1. Run `h264_estimate_motion_gpu` (or `_cpu`) to get integer
    ///      MVs.
    ///   2. Call this to upgrade them to quarter-pel.
    ///   3. Pass `subpel=True` into `h264_apply_motion_compensation`
    ///      so the MC step uses the same FIR to build the reference.
    ///   4. The QMV bytes also feed `compute_mvds` (Python) which now
    ///      receives QMVs directly instead of integer MVs × 4.
    #[pyo3(signature = (
        target_plane, reference_plane, mv_bytes,
        plane_w, plane_h, mb_w, mb_h,
        mode = "diamond",
    ))]
    fn h264_refine_motion_subpel<'py>(
        &self,
        py: Python<'py>,
        target_plane: &Bound<'_, pyo3::types::PyBytes>,
        reference_plane: &Bound<'_, pyo3::types::PyBytes>,
        mv_bytes: &Bound<'_, pyo3::types::PyBytes>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        mode: &str,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        let kernel_mode = match mode {
            "diamond" => SubpelMode::Diamond,
            "full" => SubpelMode::Full,
            other => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "subpel mode must be 'diamond' or 'full', got {:?}",
                    other
                )))
            }
        };
        let tgt = target_plane.as_bytes();
        let refp = reference_plane.as_bytes();
        if tgt.len() != plane_w * plane_h || refp.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "plane size mismatch",
            ));
        }
        let raw = mv_bytes.as_bytes();
        let n_mbs = mb_w * mb_h;
        if raw.len() != n_mbs * 12 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "mv_bytes must be {} bytes (3 LE i32 × {})",
                n_mbs * 12,
                n_mbs
            )));
        }
        let mut mvs_int = Vec::with_capacity(n_mbs);
        for i in 0..n_mbs {
            let o = i * 12;
            let mx = i32::from_le_bytes([raw[o], raw[o + 1], raw[o + 2], raw[o + 3]]);
            let my = i32::from_le_bytes([raw[o + 4], raw[o + 5], raw[o + 6], raw[o + 7]]);
            mvs_int.push((mx, my));
        }
        let refined = py.allow_threads(|| {
            refine_motion_subpel_kernel(
                tgt,
                refp,
                &mvs_int,
                plane_w,
                plane_h,
                mb_w,
                mb_h,
                kernel_mode,
            )
        });
        let mut out = Vec::with_capacity(refined.len() * 12);
        for m in &refined {
            out.extend_from_slice(&m.0.to_le_bytes());
            out.extend_from_slice(&m.1.to_le_bytes());
            out.extend_from_slice(&m.2.to_le_bytes());
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &out))
    }

    /// Multi-slice + multi-resolution parallel ABR ladder.
    /// `slices_per_level` is a list of slice counts (one per
    /// pyramid level) — splits each level into N slices for
    /// further parallelism within the level. Returns:
    ///   [(out_w, out_h, mb_w, mb_h,
    ///     [(first_mb_in_slice, cabac_payload_bytes), ...]),
    ///    ...]
    fn h264_transcode_pyramid_multislice<'py>(
        &self,
        py: Python<'py>,
        plane: &Bound<'_, pyo3::types::PyBytes>,
        in_w: usize,
        in_h: usize,
        qp: i32,
        slices_per_level: Vec<usize>,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::transcode_pyramid_multislice;
        let plane_slice = plane.as_bytes();
        if plane_slice.len() != in_w * in_h {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "plane len {} != in_w*in_h ({})",
                plane_slice.len(),
                in_w * in_h
            )));
        }
        let n_levels = slices_per_level.len();
        let levels = py.allow_threads(|| {
            transcode_pyramid_multislice(plane_slice, in_w, in_h, qp, n_levels, &slices_per_level)
        });
        let out = pyo3::types::PyList::empty_bound(py);
        for level in &levels {
            let slices_py = pyo3::types::PyList::empty_bound(py);
            for slice in &level.slices {
                let payload_py = pyo3::types::PyBytes::new_bound(py, &slice.cabac_payload);
                let slice_tup = pyo3::types::PyTuple::new_bound(
                    py,
                    &[
                        pyo3::IntoPy::into_py(slice.first_mb_in_slice, py),
                        pyo3::IntoPy::into_py(payload_py, py),
                    ],
                );
                slices_py.append(slice_tup)?;
            }
            let level_tup = pyo3::types::PyTuple::new_bound(
                py,
                &[
                    pyo3::IntoPy::into_py(level.out_w, py),
                    pyo3::IntoPy::into_py(level.out_h, py),
                    pyo3::IntoPy::into_py(level.mb_w, py),
                    pyo3::IntoPy::into_py(level.mb_h, py),
                    pyo3::IntoPy::into_py(slices_py, py),
                ],
            );
            out.append(level_tup)?;
        }
        Ok(out)
    }

    /// Full parallel ABR ladder: pyramid + intra-pred + quant +
    /// CABAC encode all done in Rust, with each level encoded in
    /// its own thread. Returns list of
    /// (out_w, out_h, mb_w, mb_h, cabac_payload_bytes).
    fn h264_transcode_pyramid_full<'py>(
        &self,
        py: Python<'py>,
        plane: &Bound<'_, pyo3::types::PyBytes>,
        in_w: usize,
        in_h: usize,
        qp: i32,
        n_levels: usize,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::transcode_pyramid_full;
        let plane_slice = plane.as_bytes();
        if plane_slice.len() != in_w * in_h {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "plane len {} != in_w*in_h ({})",
                plane_slice.len(),
                in_w * in_h
            )));
        }
        // Allow concurrency: release the GIL while Rust threads run.
        let streams =
            py.allow_threads(|| transcode_pyramid_full(plane_slice, in_w, in_h, qp, n_levels));
        let out = pyo3::types::PyList::empty_bound(py);
        for stream in &streams {
            let payload_py = pyo3::types::PyBytes::new_bound(py, &stream.cabac_payload);
            let tup = pyo3::types::PyTuple::new_bound(
                py,
                &[
                    pyo3::IntoPy::into_py(stream.out_w, py),
                    pyo3::IntoPy::into_py(stream.out_h, py),
                    pyo3::IntoPy::into_py(stream.mb_w, py),
                    pyo3::IntoPy::into_py(stream.mb_h, py),
                    pyo3::IntoPy::into_py(payload_py, py),
                ],
            );
            out.append(tup)?;
        }
        Ok(out)
    }

    /// Multi-resolution ABR ladder in a single pass. Returns a
    /// list of (out_w, out_h, mb_w, mb_h, mb_luma_bytes) tuples —
    /// one per pyramid level. Each level's mb_luma_bytes is the
    /// LE-packed i32 buffer ready for h264_encode_i_slice_luma_bytes.
    fn h264_transcode_pyramid<'py>(
        &self,
        py: Python<'py>,
        plane: &Bound<'_, pyo3::types::PyBytes>,
        in_w: usize,
        in_h: usize,
        qp: i32,
        n_levels: usize,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::transcode_pyramid_2to1;
        let plane_slice = plane.as_bytes();
        if plane_slice.len() != in_w * in_h {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "plane len {} != in_w*in_h ({})",
                plane_slice.len(),
                in_w * in_h
            )));
        }
        let levels = transcode_pyramid_2to1(plane_slice, in_w, in_h, qp, n_levels);
        let out = pyo3::types::PyList::empty_bound(py);
        for level in &levels {
            // Pack mb_luma as LE-bytes.
            let mut bytes_buf = Vec::with_capacity(level.mb_luma.len() * 4);
            for v in &level.mb_luma {
                bytes_buf.extend_from_slice(&v.to_le_bytes());
            }
            let mb_luma_py = pyo3::types::PyBytes::new_bound(py, &bytes_buf);
            let tup = pyo3::types::PyTuple::new_bound(
                py,
                &[
                    pyo3::IntoPy::into_py(level.out_w, py),
                    pyo3::IntoPy::into_py(level.out_h, py),
                    pyo3::IntoPy::into_py(level.mb_w, py),
                    pyo3::IntoPy::into_py(level.mb_h, py),
                    pyo3::IntoPy::into_py(mb_luma_py, py),
                ],
            );
            out.append(tup)?;
        }
        Ok(out)
    }

    /// Combined 4K pixels → mb_luma single-pass transcode for a
    /// 2:1 spatial downscale (e.g. 3840×2160 → 1920×1088 luma).
    /// One Rust call: fold + inverse-DCT + intra-pred + quant.
    /// Returns the flat mb_luma vector ready for the CABAC walker.
    fn h264_transcode_2to1_luma<'py>(
        &self,
        py: Python<'py>,
        plane: &Bound<'_, pyo3::types::PyBytes>,
        in_w: usize,
        in_h: usize,
        mb_w: usize,
        mb_h: usize,
        qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        use crate::h264_dct::transcode_2to1_luma_plane;
        let plane_slice = plane.as_bytes();
        if plane_slice.len() != in_w * in_h {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "plane len {} != in_w*in_h ({})",
                plane_slice.len(),
                in_w * in_h
            )));
        }
        if mb_w * 32 != in_w || mb_h * 32 != in_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "mb_w*32 must equal in_w and mb_h*32 must equal in_h",
            ));
        }
        let mb_luma = transcode_2to1_luma_plane(plane_slice, in_w, in_h, mb_w, mb_h, qp);
        // Return as bytes (4× faster than PyList<i32> for 2M values).
        // Layout: little-endian i32 sequence.
        let mut out_bytes = Vec::with_capacity(mb_luma.len() * 4);
        for v in &mb_luma {
            out_bytes.extend_from_slice(&v.to_le_bytes());
        }
        Ok(pyo3::types::PyBytes::new_bound(py, &out_bytes))
    }

    /// Same as `h264_transcode_2to1_luma` but ALSO returns the
    /// encoder-side reconstructed plane — the bit-exact luma plane
    /// the decoder will produce from this IDR's `mb_luma`. Return
    /// shape: `(mb_luma_bytes, recon_bytes)`.
    ///
    /// Use the recon plane as the IDR reference for subsequent P-frame
    /// ME / MC. Using the un-encoded source plane (or its
    /// `area_average_2to1` downsample) introduces a ~0.21 mean-abs
    /// offset per sample from our DCT round-trip rounding at QP=0,
    /// and that offset compounds through every P-frame's recon-as-
    /// reference loop. Sub-pel MC amplifies the compounding via its
    /// 6-tap FIR.
    fn h264_transcode_2to1_luma_with_recon<'py>(
        &self,
        py: Python<'py>,
        plane: &Bound<'_, pyo3::types::PyBytes>,
        in_w: usize,
        in_h: usize,
        mb_w: usize,
        mb_h: usize,
        qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::h264_dct::transcode_2to1_luma_plane_with_recon;
        let plane_slice = plane.as_bytes();
        if plane_slice.len() != in_w * in_h {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "plane len {} != in_w*in_h ({})",
                plane_slice.len(),
                in_w * in_h
            )));
        }
        if mb_w * 32 != in_w || mb_h * 32 != in_h {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "mb_w*32 must equal in_w and mb_h*32 must equal in_h",
            ));
        }
        let (mb_luma, recon) = py.allow_threads(|| {
            transcode_2to1_luma_plane_with_recon(plane_slice, in_w, in_h, mb_w, mb_h, qp)
        });
        let mut mb_bytes = Vec::with_capacity(mb_luma.len() * 4);
        for v in &mb_luma {
            mb_bytes.extend_from_slice(&v.to_le_bytes());
        }
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &mb_bytes), py),
                pyo3::IntoPy::into_py(pyo3::types::PyBytes::new_bound(py, &recon), py),
            ],
        ))
    }

    /// Single-pass DCT + 2:1 fold on a u8 luma plane. Input is a
    /// flat u8 buffer (in_w × in_h, multiples of 8). Output is the
    /// flat folded coefficients ((in_w/8) × (in_h/8) × 16 i32s)
    /// in raster order — ready for inverse-DCT to recover the
    /// downscaled pixel plane.
    fn h264_fold_luma_plane<'py>(
        &self,
        py: Python<'py>,
        plane: Vec<u8>,
        in_w: usize,
        in_h: usize,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::fold_luma_plane_to_coefs;
        if plane.len() != in_w * in_h {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "plane len {} != in_w*in_h ({})",
                plane.len(),
                in_w * in_h
            )));
        }
        if in_w & 7 != 0 || in_h & 7 != 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "in_w and in_h must be multiples of 8",
            ));
        }
        let coefs = fold_luma_plane_to_coefs(&plane, in_w, in_h);
        Ok(pyo3::types::PyList::new_bound(py, &coefs))
    }

    /// Inverse-DCT a flat coefficient array (raster of 4×4 blocks)
    /// back to a u8 luma plane. blocks_x and blocks_y give the
    /// dimensions of the block grid; output is blocks_x*4 wide and
    /// blocks_y*4 tall.
    fn h264_coefs_to_plane<'py>(
        &self,
        py: Python<'py>,
        coefs: Vec<i32>,
        blocks_x: usize,
        blocks_y: usize,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        use crate::h264_dct::coefs_to_luma_plane;
        if coefs.len() != blocks_x * blocks_y * 16 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "coefs len {} != blocks_x*blocks_y*16 ({})",
                coefs.len(),
                blocks_x * blocks_y * 16
            )));
        }
        let plane = coefs_to_luma_plane(&coefs, blocks_x, blocks_y);
        Ok(pyo3::types::PyBytes::new_bound(py, &plane))
    }

    /// Run the full I-slice luma intra-prediction + DCT + quant
    /// cascade on a target pixel plane, returning the mb_luma flat
    /// vector ready for the CABAC walker. Replaces the Python
    /// per-block loop in scripts/bench_real_downscale_via_ffmpeg.py.
    ///
    /// Inputs:
    ///   - target: u8 buffer of length plane_w*plane_h
    ///   - plane_w, plane_h: target dimensions
    ///   - mb_w, mb_h: macroblock-grid dims (must satisfy
    ///     mb_w*16==plane_w and mb_h*16==plane_h)
    ///   - qp: slice QP
    fn h264_intra_predict_and_quantise<'py>(
        &self,
        py: Python<'py>,
        target: Vec<u8>,
        plane_w: usize,
        plane_h: usize,
        mb_w: usize,
        mb_h: usize,
        qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::intra_predict_and_quantise_slice;
        if target.len() != plane_w * plane_h {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "target len {} != plane_w*plane_h ({})",
                target.len(),
                plane_w * plane_h
            )));
        }
        let mb_luma = intra_predict_and_quantise_slice(&target, plane_w, plane_h, mb_w, mb_h, qp);
        Ok(pyo3::types::PyList::new_bound(py, &mb_luma))
    }

    /// Apply H.264 spec inverse 4×4 transform + add to predictor +
    /// clip, per libavcodec ff_h264_idct_add. Input: per-block
    /// dequantised coefficients (16 i32 each) + 4×4 predictor
    /// pixels (16 u8 each). Output: 16 u8 reconstructed pixels.
    /// Inputs and output are flat arrays — n blocks of 16.
    fn h264_idct_add_many<'py>(
        &self,
        py: Python<'py>,
        coefs: Vec<i32>,
        preds: Vec<u8>,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::idct_add_4x4_h264;
        if coefs.len() % 16 != 0 || preds.len() != coefs.len() {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "coefs and preds must both be multiples of 16, same length",
            ));
        }
        let n = coefs.len() / 16;
        let mut out: Vec<u8> = Vec::with_capacity(n * 16);
        for i in 0..n {
            let mut blk = [0i32; 16];
            blk.copy_from_slice(&coefs[i * 16..(i + 1) * 16]);
            let mut p = [0u8; 16];
            p.copy_from_slice(&preds[i * 16..(i + 1) * 16]);
            out.extend_from_slice(&idct_add_4x4_h264(&blk, &p));
        }
        Ok(pyo3::types::PyList::new_bound(py, &out))
    }

    /// Inverse-dequantise (W' = Z * V << (QP/6)). Used by tests to
    /// validate the round-trip without going through ffmpeg.
    fn h264_dequantize_intra_many<'py>(
        &self,
        py: Python<'py>,
        coefs: Vec<i32>,
        qp: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::h264_dct::dequantize_intra_4x4;
        if coefs.len() % 16 != 0 {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "coefs length must be a multiple of 16",
            ));
        }
        let n = coefs.len() / 16;
        let mut out: Vec<i32> = Vec::with_capacity(n * 16);
        for i in 0..n {
            let mut z = [0i32; 16];
            z.copy_from_slice(&coefs[i * 16..(i + 1) * 16]);
            out.extend_from_slice(&dequantize_intra_4x4(&z, qp));
        }
        Ok(pyo3::types::PyList::new_bound(py, &out))
    }

    /// Return the (m, n) init pairs for the CABAC context table
    /// matching the given slice type + init_idc. Used by the
    /// independent Python reference walker to mirror the same
    /// initial state without copy-pasting the 1024-entry table.
    fn cabac_init_table<'py>(
        &self,
        py: Python<'py>,
        slice_type: &str,
        init_idc: u8,
    ) -> PyResult<Bound<'py, pyo3::types::PyList>> {
        use crate::cabac::{init_table_mn, CabacSliceType};
        let st = match slice_type {
            "I" | "SI" => CabacSliceType::I,
            "P" | "SP" => CabacSliceType::P,
            "B" => CabacSliceType::B,
            _ => {
                return Err(pyo3::exceptions::PyValueError::new_err(format!(
                    "unknown slice_type {}",
                    slice_type
                )))
            }
        };
        let table = init_table_mn(st, init_idc);
        let out: Vec<(i8, i8)> = table.iter().map(|p| (p[0], p[1])).collect();
        Ok(pyo3::types::PyList::new_bound(
            py,
            out.iter()
                .map(|(m, n)| pyo3::types::PyTuple::new_bound(py, [*m as i32, *n as i32])),
        ))
    }

    /// Like `h264_encode_i_slice_luma_only` but accepts the
    /// luma coefficients as a packed bytes buffer (4 LE bytes per
    /// i32) — the format produced by `h264_transcode_2to1_luma`.
    /// Saves the PyList-of-2M-ints conversion overhead.
    fn h264_encode_i_slice_luma_bytes<'py>(
        &self,
        py: Python<'py>,
        mb_width: usize,
        mb_height: usize,
        cabac_init_idc: u8,
        slice_qp: i32,
        luma_coefs_bytes: &Bound<'_, pyo3::types::PyBytes>,
        cbp_luma_list: Vec<u8>,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        use crate::cabac::{
            encode_i_nxn_mb, init_contexts, CabacEncoder, CabacSliceType, INxnMbInputs,
            MbNeighbourState,
        };
        let n_mbs = mb_width * mb_height;
        let raw = luma_coefs_bytes.as_bytes();
        if raw.len() != n_mbs * 256 * 4 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "luma_coefs_bytes must be {} bytes, got {}",
                n_mbs * 256 * 4,
                raw.len()
            )));
        }
        if cbp_luma_list.len() != n_mbs {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "cbp_luma_list must be {} per MB, got {}",
                n_mbs,
                cbp_luma_list.len()
            )));
        }
        // Cast the byte buffer to a slice of i32 (LE).
        let mut contexts = init_contexts(CabacSliceType::I, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        let mut grid: Vec<Vec<Option<MbNeighbourState>>> = vec![vec![None; mb_width]; mb_height];

        for r in 0..mb_height {
            for c in 0..mb_width {
                let i = r * mb_width + c;
                let mut mb = INxnMbInputs::default();
                let base = i * 256;
                for blk in 0..16 {
                    for k in 0..16 {
                        let off = (base + blk * 16 + k) * 4;
                        let v = i32::from_le_bytes([
                            raw[off],
                            raw[off + 1],
                            raw[off + 2],
                            raw[off + 3],
                        ]);
                        mb.luma_4x4[blk][k] = v;
                    }
                }
                mb.cbp_luma = cbp_luma_list[i];
                mb.cbp_chroma = 0;
                mb.intra_chroma_pred_mode = 0;
                mb.mb_qp_delta = 0;
                let left = if c > 0 { grid[r][c - 1].as_ref() } else { None };
                let top = if r > 0 { grid[r - 1][c].as_ref() } else { None };
                let (_, luma_cbf) = encode_i_nxn_mb(&mut enc, &mut contexts, &mb, left, top);
                let is_last = r == mb_height - 1 && c == mb_width - 1;
                enc.encode_terminate(if is_last { 1 } else { 0 });
                grid[r][c] = Some(MbNeighbourState {
                    mb_type_is_i_nxn: Some(true),
                    cbp_luma: mb.cbp_luma,
                    cbp_chroma: mb.cbp_chroma,
                    intra_chroma_mode: Some(mb.intra_chroma_pred_mode),
                    mb_qp_delta_was_zero: mb.mb_qp_delta == 0,
                    luma_cbf,
                    luma_dc_cbf: false,
                    chroma_dc_cbf_cb: false,
                    chroma_dc_cbf_cr: false,
                    chroma_ac_cbf_cb: [false; 4],
                    chroma_ac_cbf_cr: [false; 4],
                    abs_mvd_x: 0,
                    abs_mvd_y: 0,
                });
            }
        }
        enc.finish();
        Ok(pyo3::types::PyBytes::new_bound(py, &enc.buffer))
    }

    /// Encode an entire I-slice's worth of I_NxN macroblocks via
    /// the §7.3.5.1 walker. Inputs:
    ///   - mb_width:        slice width in macroblocks (e.g. 120 for 1080p)
    ///   - mb_height:       slice height in macroblocks (e.g. 68 for 1088 rows)
    ///   - cabac_init_idc:  I-slice value (typically 0; spec uses I table)
    ///   - slice_qp:        QP for context initialisation (e.g. 26)
    ///   - luma_coefs:      256 i32s per MB × N_mbs (luma 4×4 blocks
    ///                       in H.264 §6.4.3 raster order within each MB)
    ///   - cbp_luma_list:   one u8 per MB (4-bit CBP-luma per §7.4.5.1)
    /// All chroma is omitted from this binding for the I-only MVP
    /// (cbp_chroma = 0, no chroma DC/AC encoded).
    ///
    /// Returns the encoded byte buffer.
    fn h264_encode_i_slice_luma_only<'py>(
        &self,
        py: Python<'py>,
        mb_width: usize,
        mb_height: usize,
        cabac_init_idc: u8,
        slice_qp: i32,
        luma_coefs: Vec<i32>,
        cbp_luma_list: Vec<u8>,
    ) -> PyResult<Bound<'py, pyo3::types::PyBytes>> {
        use crate::cabac::{
            encode_i_nxn_mb, init_contexts, CabacEncoder, CabacSliceType, INxnMbInputs,
            MbNeighbourState,
        };
        let n_mbs = mb_width * mb_height;
        if luma_coefs.len() != n_mbs * 256 {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "luma_coefs must be {} = mb_width*mb_height*256, got {}",
                n_mbs * 256,
                luma_coefs.len(),
            )));
        }
        if cbp_luma_list.len() != n_mbs {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "cbp_luma_list must be {} per MB, got {}",
                n_mbs,
                cbp_luma_list.len(),
            )));
        }
        let mut contexts = init_contexts(CabacSliceType::I, cabac_init_idc, slice_qp);
        let mut enc = CabacEncoder::new();
        // Per-row neighbour-state grids (Option to model availability).
        let mut grid: Vec<Vec<Option<MbNeighbourState>>> = vec![vec![None; mb_width]; mb_height];

        for r in 0..mb_height {
            for c in 0..mb_width {
                let i = r * mb_width + c;
                let mut mb = INxnMbInputs::default();
                // Populate luma 4×4 blocks from the flat input.
                let base = i * 256;
                for blk in 0..16 {
                    for k in 0..16 {
                        mb.luma_4x4[blk][k] = luma_coefs[base + blk * 16 + k];
                    }
                }
                mb.cbp_luma = cbp_luma_list[i];
                mb.cbp_chroma = 0;
                mb.intra_chroma_pred_mode = 0;
                mb.mb_qp_delta = 0;

                let left = if c > 0 { grid[r][c - 1].as_ref() } else { None };
                let top = if r > 0 { grid[r - 1][c].as_ref() } else { None };
                let (_, luma_cbf) = encode_i_nxn_mb(&mut enc, &mut contexts, &mb, left, top);

                // Per §7.3.5: after each MB in a CABAC slice, emit
                // end_of_slice_flag — terminate bin = 1 only for the
                // very last MB in the slice; 0 otherwise.
                let is_last = r == mb_height - 1 && c == mb_width - 1;
                enc.encode_terminate(if is_last { 1 } else { 0 });

                grid[r][c] = Some(MbNeighbourState {
                    mb_type_is_i_nxn: Some(true),
                    cbp_luma: mb.cbp_luma,
                    cbp_chroma: mb.cbp_chroma,
                    intra_chroma_mode: Some(mb.intra_chroma_pred_mode),
                    mb_qp_delta_was_zero: mb.mb_qp_delta == 0,
                    luma_cbf,
                    luma_dc_cbf: false,
                    chroma_dc_cbf_cb: false,
                    chroma_dc_cbf_cr: false,
                    chroma_ac_cbf_cb: [false; 4],
                    chroma_ac_cbf_cr: [false; 4],
                    abs_mvd_x: 0,
                    abs_mvd_y: 0,
                });
            }
        }
        enc.finish();
        Ok(pyo3::types::PyBytes::new_bound(py, &enc.buffer))
    }

    /// Decode the buffer produced by `h264_encode_i_slice_luma_only`.
    /// Returns (luma_coefs, cbp_luma_list) where the layouts match
    /// the encoder's inputs.
    fn h264_decode_i_slice_luma_only<'py>(
        &self,
        py: Python<'py>,
        mb_width: usize,
        mb_height: usize,
        cabac_init_idc: u8,
        slice_qp: i32,
        buffer: Vec<u8>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{
            decode_i_nxn_mb, init_contexts, CabacDecoder, CabacSliceType, MbNeighbourState,
        };
        let n_mbs = mb_width * mb_height;
        let mut contexts = init_contexts(CabacSliceType::I, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(buffer, 0);
        let mut grid: Vec<Vec<Option<MbNeighbourState>>> = vec![vec![None; mb_width]; mb_height];

        let mut luma_out: Vec<i32> = Vec::with_capacity(n_mbs * 256);
        let mut cbp_luma_out: Vec<u8> = Vec::with_capacity(n_mbs);

        for r in 0..mb_height {
            for c in 0..mb_width {
                let left = if c > 0 { grid[r][c - 1].as_ref() } else { None };
                let top = if r > 0 { grid[r - 1][c].as_ref() } else { None };
                let (mb, _, luma_cbf) = decode_i_nxn_mb(&mut dec, &mut contexts, left, top);
                // Read end_of_slice_flag — mirror of the encoder.
                let _ = dec.decode_terminate();
                for blk in 0..16 {
                    for k in 0..16 {
                        luma_out.push(mb.luma_4x4[blk][k]);
                    }
                }
                cbp_luma_out.push(mb.cbp_luma);
                grid[r][c] = Some(MbNeighbourState {
                    mb_type_is_i_nxn: Some(true),
                    cbp_luma: mb.cbp_luma,
                    cbp_chroma: mb.cbp_chroma,
                    intra_chroma_mode: Some(mb.intra_chroma_pred_mode),
                    mb_qp_delta_was_zero: mb.mb_qp_delta == 0,
                    luma_cbf,
                    luma_dc_cbf: false,
                    chroma_dc_cbf_cb: false,
                    chroma_dc_cbf_cr: false,
                    chroma_ac_cbf_cb: [false; 4],
                    chroma_ac_cbf_cr: [false; 4],
                    abs_mvd_x: 0,
                    abs_mvd_y: 0,
                });
            }
        }
        let luma_py = pyo3::types::PyList::new_bound(py, &luma_out);
        let cbp_py = pyo3::types::PyList::new_bound(py, &cbp_luma_out);
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            [luma_py.into_any(), cbp_py.into_any()],
        ))
    }

    /// Decode a full H.264 I-slice (IDR frame) from a real bitstream
    /// all the way to YUV 4:2:0 pixels, using the agent's own CABAC MB
    /// decoder (h264_cabac_mb) + reconstruct primitives. NO ffmpeg.
    ///
    /// Inputs:
    ///   - rbsp: the slice NAL payload with emulation-prevention bytes
    ///     ALREADY REMOVED (the world adapter strips 0x03), as a byte
    ///     buffer. CABAC reads from `cabac_start_bit`.
    ///   - cabac_start_bit: bit position where the CABAC engine starts
    ///     (from walk_h264_slice_header's `cabac_start_bp`).
    ///   - slice_qp, cabac_init_idc, mb_width, mb_height: slice params.
    ///
    /// Returns (y_bytes, u_bytes, v_bytes, mbs_decoded, i16_count,
    /// inxn_count, ipcm_count). Planes are YUV 4:2:0; luma is
    /// (mb_width*16)*(mb_height*16), chroma each a quarter.
    #[pyo3(signature = (rbsp, cabac_start_bit, slice_qp, cabac_init_idc, mb_width, mb_height, chroma_qp_offset, deblock=false, deblock_disable_idc=0, deblock_alpha_off=0, deblock_beta_off=0))]
    fn h264_decode_i_slice_to_pixels<'py>(
        &self,
        py: Python<'py>,
        rbsp: Vec<u8>,
        cabac_start_bit: u64,
        slice_qp: i32,
        cabac_init_idc: u8,
        mb_width: usize,
        mb_height: usize,
        chroma_qp_offset: i32,
        deblock: bool,
        deblock_disable_idc: i32,
        deblock_alpha_off: i32,
        deblock_beta_off: i32,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{init_contexts, CabacDecoder, CabacSliceType, MbNeighbourState};
        use crate::h264_cabac_mb::{
            chroma_qp, decode_i_macroblock, reconstruct_i_macroblock, DecodedIMb, IMbType, YuvFrame,
        };
        use crate::h264_deblock::{deblock_i_frame, MbDeblockInfo};

        let w = mb_width * 16;
        let h = mb_height * 16;
        let mut frame = YuvFrame::new(w, h);

        let mut contexts = init_contexts(CabacSliceType::I, cabac_init_idc, slice_qp);
        let mut dec = CabacDecoder::new(rbsp, cabac_start_bit);

        // Neighbour-state row (left = same row prev col, top = prev row).
        let mut ns_grid: Vec<Vec<Option<MbNeighbourState>>> = vec![vec![None; mb_width]; mb_height];
        let mut mode_grid: Vec<Vec<Option<[u8; 16]>>> = vec![vec![None; mb_width]; mb_height];

        let mut cur_qp = slice_qp;
        // mb_qp_delta of the previous MB in DECODING ORDER (§9.3.3.1.1.5).
        // At slice start prevMbQpDelta is inferred 0 -> was_zero = true.
        let mut prev_qp_delta_was_zero = true;
        // Per-MB QPs for the in-loop deblocking filter.
        let mut mb_info: Vec<MbDeblockInfo> = vec![
            MbDeblockInfo {
                qp_luma: slice_qp,
                qp_chroma: slice_qp,
                is_intra: true
            };
            mb_width * mb_height
        ];
        let mut i16 = 0usize;
        let mut inxn = 0usize;
        let mut ipcm = 0usize;
        let mut decoded = 0usize;

        'outer: for mby in 0..mb_height {
            for mbx in 0..mb_width {
                let left = if mbx > 0 {
                    ns_grid[mby][mbx - 1].as_ref()
                } else {
                    None
                };
                let top = if mby > 0 {
                    ns_grid[mby - 1][mbx].as_ref()
                } else {
                    None
                };
                let left_m: Option<[u8; 16]> = if mbx > 0 {
                    mode_grid[mby][mbx - 1]
                } else {
                    None
                };
                let top_m: Option<[u8; 16]> = if mby > 0 {
                    mode_grid[mby - 1][mbx]
                } else {
                    None
                };

                let mb: DecodedIMb = decode_i_macroblock(
                    &mut dec,
                    &mut contexts,
                    left,
                    top,
                    left_m.as_ref(),
                    top_m.as_ref(),
                    prev_qp_delta_was_zero,
                );
                // Track for the next MB in decoding order. mb_qp_delta is
                // only PRESENT when the MB had coded blocks or is I_16x16;
                // when absent it is inferred 0 (was_zero stays true).
                let qp_present = mb.cbp_luma != 0
                    || mb.cbp_chroma != 0
                    || matches!(mb.mb_type, IMbType::I16x16 { .. });
                prev_qp_delta_was_zero = if qp_present {
                    mb.mb_qp_delta == 0
                } else {
                    true
                };

                if std::env::var("H264_TRACE").is_ok() {
                    let addr = mby * mb_width + mbx;
                    let coef_sum: i64 = mb
                        .luma_4x4
                        .iter()
                        .flat_map(|b| b.iter())
                        .map(|&c| c as i64)
                        .sum::<i64>()
                        + mb.luma_dc.iter().map(|&c| c as i64).sum::<i64>();
                    eprintln!(
                        "MB {:4} ({:2},{:2}) type={:?} cbp_l={:x} cbp_c={} qpd={} cmode={} coefsum={}",
                        addr, mbx, mby, mb.mb_type, mb.cbp_luma, mb.cbp_chroma,
                        mb.mb_qp_delta, mb.intra_chroma_mode, coef_sum,
                    );
                }

                // Effective QP: running accumulator + this MB's delta.
                cur_qp = (cur_qp + mb.mb_qp_delta).rem_euclid(52);
                if std::env::var("H264_TRACE").is_ok() {
                    eprintln!("    -> qp={}", cur_qp);
                }

                reconstruct_i_macroblock(&mut frame, &mb, mbx, mby, cur_qp, chroma_qp_offset);
                mb_info[mby * mb_width + mbx] = MbDeblockInfo {
                    qp_luma: cur_qp,
                    qp_chroma: chroma_qp(cur_qp + chroma_qp_offset),
                    is_intra: true,
                };

                match mb.mb_type {
                    IMbType::I16x16 { .. } => i16 += 1,
                    IMbType::INxN => inxn += 1,
                    IMbType::IPcm => ipcm += 1,
                }
                decoded += 1;

                let is_inxn = matches!(mb.mb_type, IMbType::INxN);
                ns_grid[mby][mbx] = Some(MbNeighbourState {
                    mb_type_is_i_nxn: Some(is_inxn),
                    cbp_luma: mb.cbp_luma,
                    cbp_chroma: mb.cbp_chroma,
                    intra_chroma_mode: Some(mb.intra_chroma_mode),
                    mb_qp_delta_was_zero: mb.mb_qp_delta == 0,
                    luma_cbf: mb.luma_cbf,
                    luma_dc_cbf: mb.luma_dc_cbf,
                    chroma_dc_cbf_cb: mb.chroma_dc_cbf_cb,
                    chroma_dc_cbf_cr: mb.chroma_dc_cbf_cr,
                    chroma_ac_cbf_cb: mb.chroma_ac_cbf_cb,
                    chroma_ac_cbf_cr: mb.chroma_ac_cbf_cr,
                    abs_mvd_x: 0,
                    abs_mvd_y: 0,
                });
                mode_grid[mby][mbx] = if is_inxn {
                    Some(mb.luma4x4_modes)
                } else {
                    None
                };

                // end_of_slice_flag (terminate). 1 => slice ends.
                let eos = dec.decode_terminate();
                if eos == 1 {
                    break 'outer;
                }
            }
        }

        if deblock {
            deblock_i_frame(
                &mut frame,
                &mb_info,
                mb_width,
                mb_height,
                deblock_alpha_off,
                deblock_beta_off,
                deblock_disable_idc,
            );
        }

        let y_py = pyo3::types::PyBytes::new_bound(py, &frame.y);
        let u_py = pyo3::types::PyBytes::new_bound(py, &frame.u);
        let v_py = pyo3::types::PyBytes::new_bound(py, &frame.v);
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            [
                y_py.into_any(),
                u_py.into_any(),
                v_py.into_any(),
                decoded.into_py(py).into_bound(py),
                i16.into_py(py).into_bound(py),
                inxn.into_py(py).into_bound(py),
                ipcm.into_py(py).into_bound(py),
            ],
        ))
    }

    fn cabac_round_trip<'py>(
        &mut self,
        py: Python<'py>,
        ops: &Bound<'_, pyo3::types::PyList>,
    ) -> PyResult<Bound<'py, pyo3::types::PyTuple>> {
        use crate::cabac::{CabacCtx, CabacDecoder, CabacEncoder};
        let mut enc = CabacEncoder::new();
        // Each context's state persists across ops with the same id.
        let mut enc_ctxs: std::collections::HashMap<u32, CabacCtx> =
            std::collections::HashMap::new();
        let mut bins: Vec<u8> = Vec::new();
        let mut spec: Vec<(u32, u8, bool)> = Vec::new(); // (ctx_id, bin, is_bypass)
        for item in ops.iter() {
            let t = item.downcast::<pyo3::types::PyTuple>()?;
            let ctx_id: u32 = t.get_item(0)?.extract()?;
            let p_state_idx: u8 = t.get_item(1)?.extract()?;
            let val_mps: u8 = t.get_item(2)?.extract()?;
            let bin_val: u8 = t.get_item(3)?.extract()?;
            let is_bypass: bool = t.get_item(4)?.extract()?;
            if !is_bypass {
                enc_ctxs.entry(ctx_id).or_insert(CabacCtx {
                    p_state_idx,
                    val_mps,
                });
                let ctx = enc_ctxs.get_mut(&ctx_id).unwrap();
                enc.encode_bin(ctx, bin_val);
            } else {
                enc.encode_bypass(bin_val);
            }
            spec.push((ctx_id, bin_val, is_bypass));
            bins.push(bin_val);
        }
        enc.finish();
        let buf = enc.buffer.clone();

        // Decode.
        let mut dec = CabacDecoder::new(buf.clone(), 0);
        let mut dec_ctxs: std::collections::HashMap<u32, CabacCtx> =
            std::collections::HashMap::new();
        let mut decoded = Vec::new();
        for (ctx_id, _bin_val, is_bypass) in &spec {
            if !*is_bypass {
                // Re-initialise context state same as encoder did.
                let init = enc_ctxs.get(ctx_id).map(|c| (c.p_state_idx, c.val_mps));
                // Find original p_state_idx / val_mps by searching ops.
                let (orig_p, orig_mps) = ops
                    .iter()
                    .filter_map(|i| {
                        let t = i.downcast::<pyo3::types::PyTuple>().ok()?;
                        let cid: u32 = t.get_item(0).ok()?.extract().ok()?;
                        let is_b: bool = t.get_item(4).ok()?.extract().ok()?;
                        if cid == *ctx_id && !is_b {
                            let p: u8 = t.get_item(1).ok()?.extract().ok()?;
                            let m: u8 = t.get_item(2).ok()?.extract().ok()?;
                            Some((p, m))
                        } else {
                            None
                        }
                    })
                    .next()
                    .unwrap();
                let _ = init;
                let ctx = dec_ctxs.entry(*ctx_id).or_insert(CabacCtx {
                    p_state_idx: orig_p,
                    val_mps: orig_mps,
                });
                decoded.push(dec.decode_bin(ctx));
            } else {
                decoded.push(dec.decode_bypass());
            }
        }

        let buf_py = pyo3::types::PyBytes::new_bound(py, &buf);
        let decoded_py = pyo3::types::PyList::new_bound(py, &decoded);
        Ok(pyo3::types::PyTuple::new_bound(
            py,
            &[buf_py.into_any(), decoded_py.into_any()],
        ))
    }

    // --- Phase 7b: hooks ---

    /// Register a Python callable as a lifecycle hook. `event` is one
    /// of: "node_inserted", "node_deleted", "edge_inserted",
    /// "edge_deleted", "attr_set". The callback receives positional
    /// args matching the event (see `substrate_rs.ext` docstring).
    fn register_hook(&mut self, event: &str, callback: Py<PyAny>) -> PyResult<()> {
        if !matches!(
            event,
            "node_inserted" | "node_deleted" | "edge_inserted" | "edge_deleted" | "attr_set"
        ) {
            return Err(PyValueError::new_err(format!(
                "unknown hook event: {}",
                event
            )));
        }
        self.hooks
            .entry(event.to_string())
            .or_default()
            .push(callback);
        Ok(())
    }

    fn clear_hooks(&mut self) {
        self.hooks.clear();
    }

    // --- Grammar surface -----------------------------------------------

    fn add_production(
        &mut self,
        py: Python<'_>,
        production_json: &Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        // The wire format wraps a single production in the same shape
        // grammar_from_json expects (`{"productions": [...]}`), so accept
        // either a single production dict or a productions list.
        let mut json = pyobj_to_json(py, production_json)?;
        if !json.is_object() || !json.as_object().unwrap().contains_key("productions") {
            // Wrap a single production into the grammar shape.
            json = serde_json::json!({"productions": [json]});
        }
        let parsed = grammar_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad production JSON: {:?}", e)))?;
        for p in parsed.productions {
            inner.checker.grammar.add(p);
        }
        Ok(())
    }

    /// `checker.grammar`-only variant of `add_production`: adds a production
    /// to `ConsistencyChecker.grammar` (so `check_edge` gates on it) WITHOUT
    /// writing a `GammaGrammar`/`GammaProduction` graph mirror. Structurally
    /// identical to `add_production`'s own body (this crate's Rust-inherent
    /// `Substrate::add_production` — `substrate.rs` — is the one that mints
    /// the mirror; this method deliberately never calls it).
    ///
    /// Exists for exactly one caller: `WorldAdapter.load()`'s Γ-replay-on-load
    /// step (`substrate/world_adapter.py`). `load()` restores the graph via
    /// `graph_from_dict` FIRST — which already brings back any mirror nodes a
    /// prior `save()` dumped as part of the graph — then replays
    /// `blob["grammar"]["productions"]` (a SEPARATE, `jsonio.rs`-serialised
    /// snapshot of `checker.grammar` itself, independent of the graph dump;
    /// `graph_from_dict` never touches `checker`) purely to repopulate
    /// `checker.grammar`, the plain Rust struct `check_edge` reads. If that
    /// replay went through the (possibly mirroring) general `add_production`
    /// binding, every load would mint a SECOND mirror subgraph on top of the
    /// one `graph_from_dict` just restored — unbounded, compounding growth on
    /// every save/load cycle (measured in `GAMMA_PYO3_REROUTE_RESULTS.md`
    /// §2.5: +261 nodes/cycle, no convergence across 5 cycles). Routing the
    /// replay through this mirror-free method instead makes `load()`'s
    /// behaviour independent of whatever the general `add_production`
    /// binding does — today or after any future reroute of it.
    fn add_production_no_mirror(
        &mut self,
        py: Python<'_>,
        production_json: &Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let mut json = pyobj_to_json(py, production_json)?;
        if !json.is_object() || !json.as_object().unwrap().contains_key("productions") {
            json = serde_json::json!({"productions": [json]});
        }
        let parsed = grammar_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad production JSON: {:?}", e)))?;
        for p in parsed.productions {
            inner.checker.grammar.add(p);
        }
        Ok(())
    }

    fn grammar_to_json<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let j = grammar_to_json(&inner.checker.grammar, &inner.terms, &inner.interner);
        json_to_pyobj(py, &j)
    }

    // --- admissibility probes -----------------------------------------

    #[pyo3(signature = (src, edge_type, candidate_tgt_type, candidate_tgt_attrs=None))]
    fn is_edge_admissible(
        &mut self,
        py: Python<'_>,
        src: PyRef<'_, PyNodeID>,
        edge_type: &str,
        candidate_tgt_type: &str,
        candidate_tgt_attrs: Option<&Bound<'_, PyDict>>,
    ) -> PyResult<bool> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let et = inner.interner.intern(edge_type);
        let tgt_t = inner.interner.intern(candidate_tgt_type);
        let attrs = pydict_to_attrs(py, candidate_tgt_attrs, &mut inner.interner)?;
        Ok(inner.is_edge_admissible(src.to_node(), et, tgt_t, attrs))
    }

    fn admissible_edges_from(
        &self,
        src: PyRef<'_, PyNodeID>,
        edge_type: &str,
        candidates: Vec<PyRef<'_, PyNodeID>>,
    ) -> Vec<PyNodeID> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let Some(et) = inner.interner.lookup(edge_type) else {
            return Vec::new();
        };
        let tgts: Vec<NodeID> = candidates.iter().map(|c| c.to_node()).collect();
        inner
            .admissible_edges_from(src.to_node(), et, tgts)
            .into_iter()
            .map(PyNodeID::from_node)
            .collect()
    }

    fn admissible_moves(
        &mut self,
        py: Python<'_>,
        src: PyRef<'_, PyNodeID>,
        edge_type: &str,
        candidates: Vec<(String, Option<Py<PyDict>>)>,
    ) -> PyResult<Vec<(String, Py<PyDict>, f64)>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let et = inner.interner.intern(edge_type);
        // Convert candidates Python-side first to avoid re-borrowing the
        // GIL inside the iteration.
        let mut prepared: Vec<(Sym, crate::graph::Attrs)> = Vec::with_capacity(candidates.len());
        for (t, attrs) in candidates.iter() {
            let sym = inner.interner.intern(t);
            let attrs_map: crate::graph::Attrs = match attrs {
                Some(p) => pydict_to_attrs(py, Some(p.bind(py)), &mut inner.interner)?.into(),
                None => crate::graph::Attrs::new(),
            };
            prepared.push((sym, attrs_map));
        }
        let moves = inner.admissible_moves(src.to_node(), et, prepared);
        let mut out = Vec::with_capacity(moves.len());
        for (sym, attrs, w) in moves {
            let t_str = inner.interner.resolve(sym).to_string();
            let d = attrs_to_pydict(py, &attrs, &inner.interner)?;
            out.push((t_str, d.unbind(), w));
        }
        Ok(out)
    }

    fn define_concept(
        &mut self,
        py: Python<'_>,
        name: &str,
        def_term: &Bound<'_, PyAny>,
    ) -> PyResult<()> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let name_sym = inner.interner.intern(name);
        let json = pyobj_to_json(py, def_term)?;
        let def_idx: TermIdx = term_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad concept Term JSON: {:?}", e)))?;
        inner.define_concept(name_sym, def_idx);
        Ok(())
    }

    // --- persistence ----------------------------------------------------

    fn graph_to_dict<'py>(&self, py: Python<'py>) -> PyResult<Bound<'py, PyAny>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let j = graph_to_value(&inner.graph, &inner.interner);
        json_to_pyobj(py, &j)
    }

    fn graph_from_dict(&mut self, py: Python<'_>, d: &Bound<'_, PyAny>) -> PyResult<()> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let j = pyobj_to_json(py, d)?;
        let g = graph_from_value(&j, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad graph dict: {:?}", e)))?;
        inner.graph = g;
        Ok(())
    }

    /// Diff two `graph_to_dict()`-shaped dicts. No `Substrate` instance is
    /// touched — this is pure JSON-level structural comparison (see
    /// `persist::graph_diff`'s doc comment for the full contract), so it's
    /// a `#[staticmethod]`: `substrate_rs.Substrate.graph_diff(a, b)`,
    /// callable without constructing a `Substrate` at all. Built for
    /// comparing a parent agent's pre-dispatch snapshot (`dict_a`) against
    /// a dispatched child's final graph (`dict_b`) — node identity is the
    /// node id, which `graph_from_dict` preserves across a save/load, so
    /// parent and child are id-aligned; edge identity is the structural
    /// `(src, type, tgt)` triple. O(|a| + |b|) — hash-map indexed, not a
    /// nested scan — for the 10^4-10^5 node/edge snapshots this is for.
    ///
    /// Returns:
    ///   {"nodes_added": [{id, type, attrs}, ...],
    ///    "nodes_removed": [id, ...],
    ///    "nodes_changed": [{id, attrs_before, attrs_after}, ...] (only
    ///                      the attr keys that differ; a node whose
    ///                      `type` itself changed also carries
    ///                      type_before/type_after),
    ///    "edges_added": [{src, type, tgt}, ...],
    ///    "edges_removed": [{src, type, tgt}, ...]}
    #[staticmethod]
    fn graph_diff<'py>(
        py: Python<'py>,
        dict_a: &Bound<'_, PyAny>,
        dict_b: &Bound<'_, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let ja = pyobj_to_json(py, dict_a)?;
        let jb = pyobj_to_json(py, dict_b)?;
        let d = crate::persist::graph_diff(&ja, &jb)
            .map_err(|e| PyValueError::new_err(format!("bad graph dict: {:?}", e)))?;
        json_to_pyobj(py, &d)
    }

    // --- MEMORY faculty (keep/forget/index DECISION in Rust) -----------
    //
    // CLAUDE.md: memory management is a core agent function, so it lives in
    // the Rust runtime. These hooks expose the faculty in crate::memory,
    // which composes the existing tiers (code_cache eviction shape +
    // HotCounter hot/cold + persist disk tier) with the agent's keep_value
    // / order-N-shape decision. The world adapter calls these; it makes no
    // decision itself.

    /// Configure (and lazily create) the memory faculty's bounds. The
    /// faculty persists on the substrate so growth history + the order-N
    /// shape index accumulate across calls.
    #[pyo3(signature = (budget_nodes=5000, budget_bytes=67108864, hot_window=3))]
    fn memory_bound(&mut self, budget_nodes: usize, budget_bytes: usize, hot_window: i64) {
        let fac = self
            .memory
            .get_or_insert_with(|| crate::memory::MemoryFaculty::new(budget_nodes, budget_bytes));
        fac.budget_nodes = budget_nodes;
        fac.budget_bytes = budget_bytes;
        fac.hot_window = hot_window;
    }

    /// Set only the long-term shuffle hot_window without touching the
    /// sensory byte/node budget (which MemorySelfManagement owns).
    fn memory_set_hot_window(&mut self, hot_window: i64) {
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        fac.hot_window = hot_window;
    }

    /// STREAMING forget: while over the byte/count budget, shed the type
    /// with the lowest keep_value-per-byte. Call DURING ingest so one
    /// pathological episode cannot spike the store. Returns {type: n}.
    fn memory_forget_over_budget<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        let forgot = fac.forget_over_budget(&mut guard);
        let d = PyDict::new_bound(py);
        for (t, n) in forgot {
            d.set_item(t, n)?;
        }
        Ok(d)
    }

    /// End-of-round bound (records growth, runs streaming forget, snapshots
    /// census). Returns {nodes_before, bytes_before, nodes_after,
    /// bytes_after, forgot}.
    fn memory_observe_and_bound<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        let (nb, bb, na, ba, forgot) = fac.observe_and_bound(&mut guard);
        let d = PyDict::new_bound(py);
        d.set_item("nodes_before", nb)?;
        d.set_item("bytes_before", bb)?;
        d.set_item("nodes_after", na)?;
        d.set_item("bytes_after", ba)?;
        let fd = PyDict::new_bound(py);
        for (t, n) in forgot {
            fd.set_item(t, n)?;
        }
        d.set_item("forgot", fd)?;
        Ok(d)
    }

    /// Total estimated bytes held by the graph (the real serialized
    /// footprint — the quantity the byte bound enforces).
    fn memory_total_bytes(&self) -> usize {
        let guard = self.inner.lock().expect("substrate mutex poisoned");
        crate::memory::total_bytes(&guard)
    }

    /// The agent PERCEIVING its own live native self-modification:
    /// (rule where-clauses compiled to native, total rules, Γ epoch).
    fn jit_report(&self) -> (usize, usize, u64) {
        let guard = self.inner.lock().expect("substrate mutex poisoned");
        guard.jit_stats()
    }

    /// VALUE-FOR-COMPUTE CENSUS (read-only). Per resident node type, the
    /// agent's OWN keep verdict — the quantities `forget_over_budget` ranks by.
    /// Returns a list of dicts (sorted ascending by keep_value_per_byte, i.e.
    /// the agent's forget order — head = lowest value-for-compute):
    ///   {type, count, bytes, keep_value, keep_value_per_byte,
    ///    miss_penalty, non_rebuildability, never_forget, saturating}
    fn memory_value_report<'py>(&self, py: Python<'py>) -> PyResult<Vec<Bound<'py, PyDict>>> {
        let guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .as_ref()
            .map(|f| f.value_report(&guard))
            .unwrap_or_default();
        let mut out = Vec::with_capacity(fac.len());
        for (t, count, bytes, kv, kvpb, mp, nr, never, sat, tier) in fac {
            let d = PyDict::new_bound(py);
            d.set_item("type", t)?;
            d.set_item("count", count)?;
            d.set_item("bytes", bytes)?;
            d.set_item("keep_value", kv)?;
            d.set_item("keep_value_per_byte", kvpb)?;
            d.set_item("miss_penalty", mp)?;
            d.set_item("non_rebuildability", nr)?;
            d.set_item("never_forget", never)?;
            d.set_item("saturating", sat)?;
            d.set_item("tier", tier)?;
            out.push(d);
        }
        Ok(out)
    }

    /// The memory TIER the agent assigns a node type: "keep" (consolidated),
    /// "working" (bounded RAM), or "disposable" (echoic/iconic sensory scratch
    /// — the raw firehose, dropped eagerly every tick, never consolidated).
    /// Derived from the role multipliers — the agent's standing value policy.
    #[staticmethod]
    fn value_tier(type_name: &str) -> &'static str {
        crate::memory::tier_for(type_name)
    }

    /// Forget all nodes of a named type at a CONSOLIDATION boundary, leaving a
    /// compressed MemorySummary. For retiring a spent working trace (e.g. the
    /// per-frame CortexStamp timing anchors after their binding is captured).
    fn memory_forget_type(&mut self, type_name: &str) -> usize {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        fac.forget_named(&mut guard, type_name)
    }

    /// Set the disposable circular-buffer capacity (the sensory-register span):
    /// byte bound (primary — a buffer has a size) + a node-count safety bound.
    fn memory_disposable_capacity(&mut self, bytes: usize, nodes: usize) {
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        fac.set_disposable_capacity(bytes, nodes);
    }

    /// ROLL THE SENSORY REGISTER — the disposable tier as a CIRCULAR BUFFER.
    /// Admit newly-seen disposable nodes, evict oldest-first past capacity. A
    /// fixed-capacity rolling window of recent raw input that persists a few
    /// seconds ACROSS ticks (echoic/iconic memory), not an all-or-nothing
    /// flush. Call every tick. Returns {type: n_evicted}.
    fn memory_roll_disposable<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        let evicted = fac.roll_disposable(&mut guard);
        let d = PyDict::new_bound(py);
        for (t, n) in evicted {
            d.set_item(t, n)?;
        }
        Ok(d)
    }

    /// EAGER sensory-cache flush: drop EVERY disposable-tier node NOW (the raw
    /// per-input firehose). Unconditional; clears the ring. Use for a full
    /// flush; prefer memory_roll_disposable for the rolling-window behaviour.
    fn memory_drop_disposable<'py>(&mut self, py: Python<'py>) -> PyResult<Bound<'py, PyDict>> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        let dropped = fac.drop_disposable(&mut guard);
        let d = PyDict::new_bound(py);
        for (t, n) in dropped {
            d.set_item(t, n)?;
        }
        Ok(d)
    }

    /// Consolidate a freshly-learned record to durable disk + index it into
    /// its order-N shape cluster. `cat_vec`/`leaf_vec` are the record's
    /// coarse/fine feature vectors (the shape is computed natively here).
    /// Returns the cluster id.
    fn memory_consolidate(
        &mut self,
        store_dir: &str,
        key: &str,
        nid: PyRef<'_, PyNodeID>,
        round: i64,
        cat_vec: Vec<f64>,
        leaf_vec: Vec<f64>,
    ) -> PyResult<String> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        fac.consolidate(
            &mut guard,
            store_dir,
            key,
            nid.to_node(),
            round,
            &cat_vec,
            &leaf_vec,
        )
        .map_err(|e| PyValueError::new_err(format!("consolidate failed: {}", e)))
    }

    /// Shuffle: evict cold clusters from RAM (disk copy persists). Returns
    /// the evicted cluster ids.
    fn memory_shuffle(&mut self, round: i64) -> Vec<String> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        fac.shuffle(&mut guard, round)
    }

    /// Recall by order-N shape descent: locate the cluster whose shape
    /// matches the query, page the whole drawer hot. Returns (cluster_id,
    /// n_paged_in) or None.
    fn memory_recall_by_shape(
        &mut self,
        cat_vec: Vec<f64>,
        leaf_vec: Vec<f64>,
        round: i64,
    ) -> Option<(String, usize)> {
        let mut guard = self.inner.lock().expect("substrate mutex poisoned");
        let fac = self
            .memory
            .get_or_insert_with(crate::memory::MemoryFaculty::default);
        fac.recall_by_shape(&mut guard, &cat_vec, &leaf_vec, round)
    }

    /// Number of clusters in the order-N shape index (the index footprint —
    /// a RULE bounded by #clusters, NOT a per-item map).
    fn memory_index_clusters(&self) -> usize {
        self.memory
            .as_ref()
            .map(|f| f.findable_clusters())
            .unwrap_or(0)
    }

    /// Report the L4 subsystem the memory faculty's operations belong to.
    /// The faculty registers its ops under MetaShape::DelayedPersistence
    /// (#449, "consolidation + replay"); this verifies that wiring against a
    /// fresh registry and returns the subsystem name + analogy weight.
    fn memory_subsystem(&self) -> (String, u32) {
        let mut reg = crate::l4_subsystem_boundaries::SubsystemRegistry::new();
        crate::memory::MemoryFaculty::register_subsystem(&mut reg);
        let shape = reg
            .subsystem_of("memory_consolidate")
            .unwrap_or(crate::l4_subsystem_boundaries::MetaShape::DelayedPersistence);
        (format!("{:?}", shape), shape.analogy_weight())
    }

    /// ORDER-N SHAPE SALIENCE — the agent's GENERAL salience operator over
    /// ANY trajectory's order-N shape (growth / pitch / rhythm / motion).
    /// High for a DIRECTED, RESOLVING build->peak (the "tada"); low for a
    /// FLAT or RANDOM trajectory. Composes the held order_n (velocity +
    /// curvature) and relational_shape (ordinal rank of the resolution)
    /// operators, native, no ML. This is the SAME operator memory's
    /// keep_value uses for tiering — one salience for memory AND perception.
    /// A world adapter (audio/video front-end) feeds it the trajectory it
    /// extracted; the salience itself lives here.
    #[staticmethod]
    fn shape_salience(seq: Vec<f64>) -> f64 {
        crate::memory::order_n_shape_salience(&seq)
    }

    /// THE SHAPE SIGNATURE of a trajectory — its relational-shape
    /// ordinal-rank key (gain/level-invariant). Two clips that share the
    /// order-N SHAPE but differ in every surface way get NEIGHBOURING
    /// signatures. The world adapter extracts the trajectory; the signature
    /// is the held operator. Returns a list of int ranks.
    #[staticmethod]
    fn shape_signature(seq: Vec<f64>) -> Vec<i64> {
        crate::memory::shape_signature(&seq)
    }

    /// VISION FOREGROUND — the held object-isolation operator. The named object on
    /// screen is what DEVIATES from the persistent background; foreground =
    /// elementwise |frame - background|, suppressing the constant presenter/set so
    /// the cue is the object, not the dominant scene. The held op (Rust); the world
    /// adapter holds the background buffer + marshals frames in/out.
    #[staticmethod]
    fn foreground(frame: Vec<f64>, background: Vec<f64>) -> Vec<f64> {
        frame
            .iter()
            .zip(background.iter())
            .map(|(f, b)| (f - b).abs())
            .collect()
    }

    /// EMA BACKGROUND UPDATE — the running background model: elementwise
    /// background*(1-alpha) + frame*alpha. The persistent scene accretes; a new
    /// object stands out in `foreground` until it too fades in. Held op (Rust).
    #[staticmethod]
    fn ema_blend(background: Vec<f64>, frame: Vec<f64>, alpha: f64) -> Vec<f64> {
        background
            .iter()
            .zip(frame.iter())
            .map(|(b, f)| b * (1.0 - alpha) + f * alpha)
            .collect()
    }

    /// L1 distance between two shape signatures (the shape-neighbour metric).
    #[staticmethod]
    fn shape_signature_distance(a: Vec<i64>, b: Vec<i64>) -> i64 {
        crate::memory::shape_distance(&a, &b)
    }

    /// The scale-derived shape-neighbour threshold for a signature of length
    /// n (NOT tuned to an answer — set from the rank scale).
    #[staticmethod]
    fn shape_neighbour_threshold(n: usize) -> i64 {
        crate::memory::shape_neighbour_threshold(n)
    }

    /// PER-FEATURE z-score normalisation of a population of affect vectors,
    /// returned as fixed-point milli-z integers (`z * 1000`). Makes
    /// heterogeneous-unit features comparable before L2 (the proper affect
    /// metric). Mechanical mean/std over the exact clip set, no fit/sweep.
    #[staticmethod]
    fn affect_normalize(vectors: Vec<Vec<f64>>) -> Vec<Vec<i64>> {
        crate::memory::affect_normalize(&vectors)
    }

    /// L2 (Euclidean) distance between two normalised affect signatures, in
    /// the fixed-point milli-z space. The proper affect-neighbour metric.
    #[staticmethod]
    fn l2_signature_distance(a: Vec<i64>, b: Vec<i64>) -> i64 {
        crate::memory::l2_distance(&a, &b)
    }

    /// The scale-derived affect-neighbour threshold for an n-feature vector
    /// (sqrt(n) * 1000 milli-z = ~1 std per feature). NOT tuned.
    #[staticmethod]
    fn affect_neighbour_threshold(n: usize) -> i64 {
        crate::memory::affect_neighbour_threshold(n)
    }

    /// CATEGORICAL (Hamming) distance between two bucketed role signatures —
    /// the proper function-neighbour metric (count of differing buckets).
    #[staticmethod]
    fn categorical_signature_distance(a: Vec<i64>, b: Vec<i64>) -> i64 {
        crate::memory::categorical_distance(&a, &b)
    }

    /// The function-neighbour threshold (categorical-match: Hamming <= 1, i.e.
    /// distance < 2 == same role allowing one bucket slip). NOT tuned.
    #[staticmethod]
    fn categorical_neighbour_threshold(n: usize) -> i64 {
        crate::memory::categorical_neighbour_threshold(n)
    }

    /// Declare the `shares_shape` edge type admissible in Γ
    /// ((SalientShape) -[shares_shape]-> (SalientShape)). ONE edge type
    /// added to the grammar; the existing edge types are untouched.
    fn declare_shares_shape(&mut self) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.declare_shares_shape();
    }

    /// Add a SalientShape NODE carrying a clip/event's order-N shape
    /// signature, then WIRE `shares_shape` edges to existing SalientShape
    /// nodes that are shape-NEIGHBOURS (signature distance below the
    /// scale-derived threshold). Returns `(node_id, [(neighbour_id,
    /// distance), ...])`. The salient shape as ONE relation, additive.
    fn add_salient_shape(
        &mut self,
        label: &str,
        signature: Vec<i64>,
    ) -> (PyNodeID, Vec<(PyNodeID, i64)>) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let (nid, linked) = inner.add_salient_shape(label, &signature);
        let py_linked = linked
            .into_iter()
            .map(|(n, d)| (PyNodeID::from_node(n), d))
            .collect();
        (PyNodeID::from_node(nid), py_linked)
    }

    /// SPREADING-ACTIVATION recall from a cue node. Traverses MULTIPLE edge
    /// types (shares_shape + co-occurrence + whatever the node carries) up
    /// to `max_hops`, surfacing the activated set. Returns `[(node_id,
    /// edge_type_name, hop), ...]` so shape-analogues are distinguishable
    /// from co-occurrence neighbours. NOT a single-key lookup.
    #[pyo3(signature = (cue, max_hops=2))]
    fn spread(&self, cue: PyRef<'_, PyNodeID>, max_hops: usize) -> Vec<(PyNodeID, String, usize)> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner
            .spread(cue.to_node(), max_hops)
            .into_iter()
            .map(|(n, et, hop)| {
                (
                    PyNodeID::from_node(n),
                    inner.interner.resolve(et).to_string(),
                    hop,
                )
            })
            .collect()
    }

    /// Declare ONE multi-relational edge type admissible in Γ:
    /// (SalientShape) -[edge_type]-> (SalientShape). Used for the timbre /
    /// affect / function relations — each its own edge type, added alongside
    /// shares_shape, leaving existing edge types untouched.
    fn declare_relation_edge(&mut self, edge_type: &str, provenance: &str) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.declare_relation_edge(edge_type, provenance);
    }

    /// Attach a relation SIGNATURE (stored under `sig_attr`) to an EXISTING
    /// SalientShape node, then WIRE `edge_type` edges to other SalientShape
    /// nodes whose `sig_attr` signature is within the scale-derived threshold.
    /// The SAME node can carry many relation signatures (shape, timbre,
    /// affect, function) — each under its own attr key, each its own edge.
    /// Returns `[(neighbour_id, distance), ...]`. Reuses the held ordinal-rank
    /// distance + threshold (NOT tuned).
    fn wire_relation(
        &mut self,
        node: PyRef<'_, PyNodeID>,
        edge_type: &str,
        sig_attr: &str,
        signature: Vec<i64>,
        provenance: &str,
    ) -> Vec<(PyNodeID, i64)> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner
            .wire_relation(node.to_node(), edge_type, sig_attr, &signature, provenance)
            .into_iter()
            .map(|(n, d)| (PyNodeID::from_node(n), d))
            .collect()
    }

    /// AFFECT relation wiring with the PROPER metric (per-feature normalised
    /// L2, NOT ordinal rank). Takes the RAW heterogeneous affect vectors for a
    /// set of nodes (parallel to `nodes`); normalises each feature across the
    /// population in the core, stores the normalised signature, wires pairs
    /// within the scale-derived affect threshold. Returns, per node index,
    /// `[(neighbour_id, distance), ...]`.
    fn wire_relation_affect(
        &mut self,
        nodes: Vec<PyRef<'_, PyNodeID>>,
        edge_type: &str,
        sig_attr: &str,
        raw: Vec<Vec<f64>>,
        provenance: &str,
    ) -> Vec<Vec<(PyNodeID, i64)>> {
        let node_ids: Vec<NodeID> = nodes.iter().map(|n| n.to_node()).collect();
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner
            .wire_relation_affect(&node_ids, edge_type, sig_attr, &raw, provenance)
            .into_iter()
            .map(|row| {
                row.into_iter()
                    .map(|(n, d)| (PyNodeID::from_node(n), d))
                    .collect()
            })
            .collect()
    }

    /// FUNCTION relation wiring with the PROPER metric (CATEGORICAL / Hamming
    /// match on the bucketed role vector, NOT ordinal rank). Stores the role
    /// signature, wires to other nodes whose role category matches within the
    /// categorical threshold (Hamming <= 1). Returns `[(neighbour_id, dist)]`.
    fn wire_relation_categorical(
        &mut self,
        node: PyRef<'_, PyNodeID>,
        edge_type: &str,
        sig_attr: &str,
        signature: Vec<i64>,
        provenance: &str,
    ) -> Vec<(PyNodeID, i64)> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner
            .wire_relation_categorical(node.to_node(), edge_type, sig_attr, &signature, provenance)
            .into_iter()
            .map(|(n, d)| (PyNodeID::from_node(n), d))
            .collect()
    }

    fn intern(&mut self, s: &str) -> u32 {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.interner.intern(s).0
    }

    fn resolve_sym(&self, sym: u32) -> PyResult<String> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        if (sym as usize) >= inner.interner.len() {
            return Err(PyValueError::new_err(format!("unknown sym {}", sym)));
        }
        Ok(inner.interner.resolve(Sym(sym)).to_string())
    }

    // --- Shape (function_shape Mt) PyO3 bindings ------------------------
    //
    // World adapters + tests query the Shape of a Term-tree via JSON
    // (same encoding as `evaluate`'s term_json). Returns a dict
    // {recursion, order_n, abstraction} so Python can pattern-match
    // on axes without minting a PyShape class.

    /// Return the Shape of the Term-tree given as JSON.
    /// Hits the substrate's shape_cache; second + subsequent calls on
    /// the same term are O(1) per Michie 1968 / L6 bounded latency.
    fn shape_of_term<'py>(
        &mut self,
        py: Python<'py>,
        term_json: &Bound<'_, PyAny>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let json = pyobj_to_json_term(py, term_json, WireMode::Structural)?;
        let idx = term_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad Term JSON: {:?}", e)))?;
        let shape = inner.shape_of_term(idx);
        let d = pyo3::types::PyDict::new_bound(py);
        d.set_item("recursion", shape.recursion.as_str())?;
        d.set_item("order_n", shape.order_n.0 as i64)?;
        d.set_item("abstraction", shape.abstraction.as_str())?;
        Ok(d.into_any())
    }

    /// Add a graph `Shape` node for the given Term-tree and return its
    /// NodeID. The node's attrs encode the three axes; Rules can then
    /// filter Shape nodes by axis via the substrate's standard Term
    /// dispatch (Filter / Attr).
    fn add_shape_node_for_term<'py>(
        &mut self,
        py: Python<'py>,
        term_json: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyNodeID>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let json = pyobj_to_json_term(py, term_json, WireMode::Structural)?;
        let idx = term_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad Term JSON: {:?}", e)))?;
        let shape = inner.shape_of_term(idx);
        let nid = crate::shape::add_shape_node(inner, shape);
        Py::new(py, PyNodeID { value: nid.0 })
    }

    /// Materialise a Term as a graph subgraph (typed `Term.<Variant>`
    /// nodes + `child.<field>` edges) and return its root NodeID — the
    /// inverse of `EvalSubgraph`'s read. This is how a Term becomes
    /// first-class graph DATA the agent can introspect, attach to a
    /// node (e.g. a `satisfaction_term` / `goal_weight_term` edge), and
    /// evaluate via `EvalSubgraph(root)`. It is also how a captured seed
    /// carries a decision Term: materialise it, then serialise the
    /// subgraph into the seed's nodes/edges.
    fn add_term_subgraph<'py>(
        &mut self,
        py: Python<'py>,
        term_json: &Bound<'_, PyAny>,
    ) -> PyResult<Py<PyNodeID>> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let json = pyobj_to_json_term(py, term_json, WireMode::Structural)?;
        let idx = term_from_json(&json, &mut inner.terms, &mut inner.interner)
            .map_err(|e| PyValueError::new_err(format!("bad Term JSON: {:?}", e)))?;
        let nid = crate::reflect::term_to_subgraph(
            &inner.terms,
            idx,
            &mut inner.graph,
            &mut inner.interner,
        );
        Py::new(py, PyNodeID { value: nid.0 })
    }

    /// Read a reflected Term subgraph (rooted at `node`) back into the
    /// canonical Term-JSON wire form, returned as a JSON STRING — the
    /// mechanical inverse of `add_term_subgraph`, and the read-back
    /// half of the P1 reflect round-trip gate
    /// (tests/test_prog_ir_migrated.py): Term-JSON →
    /// `add_term_subgraph` → `term_subgraph_json` → identical
    /// canonical JSON. Pure read; raises on a node that does not root
    /// a well-formed `Term.*` subgraph.
    fn term_subgraph_json(&self, node: PyRef<'_, PyNodeID>) -> PyResult<String> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        let nid = node.to_node();
        let snapshot = inner.terms.nodes.len();
        let idx = crate::reflect::term_from_subgraph(
            &inner.graph,
            &inner.interner,
            nid,
            &mut inner.terms,
        )
        .map_err(|e| PyValueError::new_err(format!("not a Term subgraph: {:?}", e)))?;
        let j = term_to_json(&inner.terms, idx, &inner.interner);
        inner.terms.nodes.truncate(snapshot);
        Ok(j.to_string())
    }

    /// Test shape compatibility: does the candidate shape's structure
    /// admit the target shape? Implements
    /// shape_mismatch_prunes_negative_problem_space.
    /// Both inputs are dict-encoded shapes
    /// `{recursion, order_n, abstraction}` (the same encoding
    /// `shape_of_term` returns).
    fn shapes_compatible(
        &self,
        candidate: &Bound<'_, PyDict>,
        target: &Bound<'_, PyDict>,
    ) -> PyResult<bool> {
        let c = shape_from_pydict(candidate)?;
        let t = shape_from_pydict(target)?;
        Ok(crate::shape::shapes_compatible(&c, &t))
    }

    /// `meta_shape_is_one_rung_up_l6_circular_causality` — climb one
    /// rung of the Smith reflective tower (Smith 1982). Returns the
    /// Shape that results from applying the order-N operator
    /// (Pearlmutter-Siskind D) to a function with the given shape:
    /// order_n + 1, abstraction becomes parametric, recursion preserved.
    #[pyo3(name = "meta_shape")]
    fn meta_shape_py<'py>(
        &self,
        py: Python<'py>,
        shape: &Bound<'_, PyDict>,
    ) -> PyResult<Bound<'py, PyAny>> {
        let s = shape_from_pydict(shape)?;
        let meta = crate::shape::meta_shape(s);
        let d = pyo3::types::PyDict::new_bound(py);
        d.set_item("recursion", meta.recursion.as_str())?;
        d.set_item("order_n", meta.order_n.0 as i64)?;
        d.set_item("abstraction", meta.abstraction.as_str())?;
        Ok(d.into_any())
    }

    /// Climb N rungs of the reflective tower. Equivalent to applying
    /// `meta_shape` N times. Caps at u8::MAX rungs (per
    /// `crate::shape::climb_tower`'s saturating arithmetic).
    fn climb_tower<'py>(
        &self,
        py: Python<'py>,
        shape: &Bound<'_, PyDict>,
        rungs: u8,
    ) -> PyResult<Bound<'py, PyAny>> {
        let s = shape_from_pydict(shape)?;
        let climbed = crate::shape::climb_tower(s, rungs);
        let d = pyo3::types::PyDict::new_bound(py);
        d.set_item("recursion", climbed.recursion.as_str())?;
        d.set_item("order_n", climbed.order_n.0 as i64)?;
        d.set_item("abstraction", climbed.abstraction.as_str())?;
        Ok(d.into_any())
    }

    /// Set the substrate's active_shape_target. Rules whose where-clause
    /// shape is incompatible with this target will be SKIPPED by
    /// `apply_rule_once` (negative_problem_space_pruning at the rule
    /// dispatch level). Pass None to clear the filter.
    fn set_shape_target(&mut self, target: Option<&Bound<'_, PyDict>>) -> PyResult<()> {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        let inner = &mut *__substrate_guard;
        inner.set_shape_target(target.map(shape_from_pydict).transpose()?);
        Ok(())
    }

    /// Returns the count of rules skipped by the shape filter since the
    /// counter was last cleared (start of run_rules). Lets callers
    /// measure the Cousot+Ashby pruning's multiplicative savings.
    fn shape_pruned_count(&self) -> u64 {
        let __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.shape_pruned_count
    }

    /// Manually reset the three Shape-pruning counters (rule-dispatch,
    /// derivation-dispatch, concept-dispatch). run_rules() does this
    /// automatically; this method is for callers that drive their own
    /// tick boundary.
    fn reset_shape_counters(&mut self) {
        let mut __substrate_guard = self.inner.lock().expect("substrate mutex poisoned");
        __substrate_guard.reset_shape_counters();
    }
}

// Helper for shapes_compatible: parse a Python dict into a Shape.
fn shape_from_pydict(d: &Bound<'_, PyDict>) -> PyResult<crate::shape::Shape> {
    let rec_str: String = d
        .get_item("recursion")?
        .ok_or_else(|| PyValueError::new_err("shape dict missing 'recursion'"))?
        .extract()?;
    let order_i: i64 = d
        .get_item("order_n")?
        .ok_or_else(|| PyValueError::new_err("shape dict missing 'order_n'"))?
        .extract()?;
    let abs_str: String = d
        .get_item("abstraction")?
        .ok_or_else(|| PyValueError::new_err("shape dict missing 'abstraction'"))?
        .extract()?;
    let recursion = crate::shape::RecursionKind::from_str(&rec_str)
        .ok_or_else(|| PyValueError::new_err(format!("unknown RecursionKind '{}'", rec_str)))?;
    let abstraction = crate::shape::AbstractionKind::from_str(&abs_str)
        .ok_or_else(|| PyValueError::new_err(format!("unknown AbstractionKind '{}'", abs_str)))?;
    let order_n = crate::shape::OrderN(
        u8::try_from(order_i)
            .map_err(|_| PyValueError::new_err(format!("order_n {} out of u8 range", order_i)))?,
    );
    Ok(crate::shape::Shape::new(recursion, order_n, abstraction))
}

// --- Rule JSON parsing (Phase 7c) ------------------------------------------

/// Parse a rule dict into a Rust [`crate::rewrite::RewriteRule`].
/// Mirrors the encoding the existing `domains/graph_rewrite.py` uses
/// for storage so a rule authored in Python is usable here without
/// reshape.
/// Public wrapper around `parse_rule_json` so other Rust modules
/// (e.g. `codec`) can parse the same JSON dialect.
pub fn parse_rule_json_pub(
    j: &serde_json::Value,
    terms: &mut TermArena,
    interner: &mut crate::sym::Interner,
) -> Result<crate::rewrite::RewriteRule, String> {
    parse_rule_json(j, terms, interner)
}

fn parse_rule_json(
    j: &J,
    terms: &mut TermArena,
    interner: &mut crate::sym::Interner,
) -> Result<crate::rewrite::RewriteRule, String> {
    let obj = j
        .as_object()
        .ok_or_else(|| "rule must be an object".to_string())?;
    let name = obj
        .get("name")
        .and_then(|v| v.as_str())
        .unwrap_or("anonymous_rule");
    let schedule_explicit =
        obj.contains_key("area") || obj.contains_key("order") || obj.contains_key("latency_class");
    let uid = obj.get("rule_uid").and_then(|v| v.as_u64()).unwrap_or(0);
    let revision = obj.get("revision").and_then(|v| v.as_u64()).unwrap_or(0);
    let mutation_protected = obj
        .get("mutation_protected")
        .and_then(|v| v.as_bool())
        .unwrap_or(false);
    // Do not intern derived defaults: interner allocation order is observable
    // in this non-confluent runtime. Legacy rules must not move one Sym.
    let area = obj
        .get("area")
        .and_then(|v| v.as_str())
        .map(|v| interner.intern(v))
        .unwrap_or_default();
    let order = obj.get("order").and_then(|v| v.as_u64()).unwrap_or(0) as u32;
    let latency_class = obj
        .get("latency_class")
        .and_then(|v| v.as_str())
        .map(|v| interner.intern(v))
        .unwrap_or_default();

    let match_arr = obj
        .get("match")
        .and_then(|v| v.as_array())
        .ok_or_else(|| "missing or non-array 'match'".to_string())?;
    let mut match_edges = Vec::with_capacity(match_arr.len());
    for me in match_arr {
        let arr = me
            .as_array()
            .ok_or_else(|| "match item must be array".to_string())?;
        if arr.len() != 3 {
            return Err(
                "match item must have 3 elements: [src_var, edge_type, tgt_var]".to_string(),
            );
        }
        let src_var = arr[0]
            .as_str()
            .ok_or_else(|| "match src_var must be str".to_string())?;
        let edge_type = arr[1]
            .as_str()
            .ok_or_else(|| "match edge_type must be str".to_string())?;
        let tgt_var = arr[2]
            .as_str()
            .ok_or_else(|| "match tgt_var must be str".to_string())?;
        match_edges.push(crate::rewrite::MatchEdge {
            src_var: interner.intern(src_var),
            edge_type: interner.intern(edge_type),
            tgt_var: interner.intern(tgt_var),
        });
    }

    let where_ = match obj.get("where") {
        Some(J::Null) | None => None,
        Some(other) => Some(
            crate::jsonio::term_from_json(other, terms, interner)
                .map_err(|e| format!("bad where Term: {:?}", e))?,
        ),
    };

    let effects_arr = obj
        .get("effects")
        .and_then(|v| v.as_array())
        .map(|a| a.as_slice())
        .unwrap_or(&[]);
    let mut effects = Vec::with_capacity(effects_arr.len());
    for ef in effects_arr {
        effects.push(parse_effect_json(ef, terms, interner)?);
    }

    let batch = obj.get("batch").and_then(|v| v.as_bool()).unwrap_or(false);
    let match_type = obj
        .get("match_type")
        .and_then(|v| v.as_str())
        .map(|s| interner.intern(s));

    // R10 (join-index wave): optional "index_hints" — a list of
    // {"for_var","via_var","via_key","node_type","this_key"} dicts. Absent
    // for every pre-existing rule (parses to the empty Vec, byte-identical
    // to before this field existed). See rewrite.rs::IndexJoinHint.
    let mut index_hints = Vec::new();
    if let Some(arr) = obj.get("index_hints").and_then(|v| v.as_array()) {
        for h in arr {
            let ho = h
                .as_object()
                .ok_or_else(|| "index_hints item must be an object".to_string())?;
            let get_str = |k: &str| -> Result<&str, String> {
                ho.get(k)
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| format!("index_hints item missing string field {k:?}"))
            };
            index_hints.push(crate::rewrite::IndexJoinHint {
                for_var: interner.intern(get_str("for_var")?),
                via_var: interner.intern(get_str("via_var")?),
                via_key: interner.intern(get_str("via_key")?),
                node_type: interner.intern(get_str("node_type")?),
                this_key: interner.intern(get_str("this_key")?),
            });
        }
    }

    Ok(crate::rewrite::RewriteRule {
        uid: crate::rewrite::RuleUid(uid),
        revision,
        mutation_protected,
        name: interner.intern(name),
        area,
        order,
        latency_class,
        schedule_explicit,
        match_edges,
        where_,
        effects,
        batch,
        match_type,
        index_hints,
        ..Default::default()
    })
}

// --- Rule JSON emission (checkpoint export) --------------------------------
//
// Exact inverse of `parse_rule_json` / `parse_effect_json` above — same wire
// dialect, so a rule captured here loads straight back through `add_rule` (or
// through `Substrate::import_rules`, which is what `export_rules` pairs
// with). Kept next to the parsers so the two directions are visibly in sync.

/// Serialise one installed rule (including its `active` tombstone flag) to
/// the `add_rule` dict dialect.
pub(crate) fn rule_to_json(
    rule: &crate::rewrite::RewriteRule,
    terms: &TermArena,
    interner: &crate::sym::Interner,
) -> J {
    let match_arr: Vec<J> = rule
        .match_edges
        .iter()
        .map(|me| {
            serde_json::json!([
                interner.resolve(me.src_var),
                interner.resolve(me.edge_type),
                interner.resolve(me.tgt_var),
            ])
        })
        .collect();
    let where_j = match rule.where_ {
        Some(idx) => term_to_json(terms, idx, interner),
        None => J::Null,
    };
    let effects_j: Vec<J> = rule
        .effects
        .iter()
        .map(|e| effect_to_json(e, terms, interner))
        .collect();
    let match_type_j = match rule.match_type {
        Some(s) => J::String(interner.resolve(s).to_string()),
        None => J::Null,
    };
    let mut out = serde_json::json!({
        "rule_uid": rule.uid.0,
        "revision": rule.revision,
        "content_hash": rule.content_hash,
        "name": interner.resolve(rule.name),
        "match": match_arr,
        "where": where_j,
        "effects": effects_j,
        "batch": rule.batch,
        "match_type": match_type_j,
        "active": rule.active,
    });
    // R10: emit "index_hints" ONLY when non-empty — every pre-existing rule
    // (no hints) round-trips byte-identically to the pre-R10 export dialect,
    // which fixture-parity gates (e.g. composer_driver_parity) compare
    // literally. A hinted rule gains the key; parse_rule_json treats an
    // absent key as the empty Vec, so the round-trip is exact both ways.
    if !rule.index_hints.is_empty() {
        let index_hints_j: Vec<J> = rule
            .index_hints
            .iter()
            .map(|h| {
                serde_json::json!({
                    "for_var": interner.resolve(h.for_var),
                    "via_var": interner.resolve(h.via_var),
                    "via_key": interner.resolve(h.via_key),
                    "node_type": interner.resolve(h.node_type),
                    "this_key": interner.resolve(h.this_key),
                })
            })
            .collect();
        out["index_hints"] = J::Array(index_hints_j);
    }
    if rule.mutation_protected {
        out["mutation_protected"] = J::Bool(true);
    }
    if rule.schedule_explicit {
        out["area"] = J::String(interner.resolve(rule.area).to_string());
        out["order"] = J::Number(serde_json::Number::from(rule.order));
        out["latency_class"] = J::String(interner.resolve(rule.latency_class).to_string());
    }
    out
}

/// Inverse of `arg_to_effect` (defined inline in `parse_effect_json`):
/// `Literal(v)` → the encoded value itself; `Computed(idx)` → `{"__term__": ...}`.
fn effect_arg_to_json(
    arg: &crate::rewrite::EffectArg,
    terms: &TermArena,
    interner: &crate::sym::Interner,
) -> J {
    match arg {
        crate::rewrite::EffectArg::Literal(v) => encode_value(v, interner),
        crate::rewrite::EffectArg::Computed(idx) => {
            serde_json::json!({ "__term__": term_to_json(terms, *idx, interner) })
        }
    }
}

/// Inverse of `attrs_dict` (defined inline in `parse_effect_json`).
fn attrs_to_json(
    attrs: &[(Sym, crate::rewrite::EffectArg)],
    terms: &TermArena,
    interner: &crate::sym::Interner,
) -> J {
    let mut m = serde_json::Map::with_capacity(attrs.len());
    for (k, v) in attrs {
        m.insert(
            interner.resolve(*k).to_string(),
            effect_arg_to_json(v, terms, interner),
        );
    }
    J::Object(m)
}

/// Inverse of `parse_effect_json` — same array-of-[kind, ...args] wire shape
/// for every `Effect` variant.
pub(crate) fn effect_to_json(
    eff: &crate::rewrite::Effect,
    terms: &TermArena,
    interner: &crate::sym::Interner,
) -> J {
    use crate::rewrite::Effect as E;
    let s = |sym: Sym| interner.resolve(sym).to_string();
    match eff {
        E::AddEdge {
            src_var,
            edge_type,
            tgt_var,
            attrs,
        } => J::Array(vec![
            J::String("add_edge".into()),
            J::String(s(*src_var)),
            J::String(s(*edge_type)),
            J::String(s(*tgt_var)),
            attrs_to_json(attrs, terms, interner),
        ]),
        E::DelEdge {
            src_var,
            edge_type,
            tgt_var,
        } => J::Array(vec![
            J::String("del_edge".into()),
            J::String(s(*src_var)),
            J::String(s(*edge_type)),
            J::String(s(*tgt_var)),
        ]),
        E::AddNode {
            new_var,
            type_,
            attrs,
        } => J::Array(vec![
            J::String("add_node".into()),
            J::String(s(*new_var)),
            J::String(s(*type_)),
            attrs_to_json(attrs, terms, interner),
        ]),
        E::AddNodeIfAbsent {
            new_var,
            type_,
            attrs,
        } => J::Array(vec![
            J::String("add_node_if_absent".into()),
            J::String(s(*new_var)),
            J::String(s(*type_)),
            attrs_to_json(attrs, terms, interner),
        ]),
        E::DelNode { var } => J::Array(vec![J::String("del_node".into()), J::String(s(*var))]),
        E::SetAttr { var, key, value } => J::Array(vec![
            J::String("set_attr".into()),
            J::String(s(*var)),
            J::String(s(*key)),
            effect_arg_to_json(value, terms, interner),
        ]),
        E::SetAttrIfDifferent { var, key, value } => J::Array(vec![
            J::String("set_attr_if_different".into()),
            J::String(s(*var)),
            J::String(s(*key)),
            effect_arg_to_json(value, terms, interner),
        ]),
        E::ReplaceValue { old_var, new_var } => J::Array(vec![
            J::String("replace_value".into()),
            J::String(s(*old_var)),
            J::String(s(*new_var)),
        ]),
        E::DefineConcept { name, term } => J::Array(vec![
            J::String("define_concept".into()),
            effect_arg_to_json(name, terms, interner),
            effect_arg_to_json(term, terms, interner),
        ]),
        E::SetRuleClause {
            rule_name,
            field,
            term,
        } => J::Array(vec![
            J::String("set_rule_clause".into()),
            effect_arg_to_json(rule_name, terms, interner),
            effect_arg_to_json(field, terms, interner),
            effect_arg_to_json(term, terms, interner),
        ]),
        E::ApplyRulePatch { patch_var } => J::Array(vec![
            J::String("apply_rule_patch".into()),
            J::String(s(*patch_var)),
        ]),
        E::FbSample {
            fb,
            game_var,
            grid_w,
            grid_h,
        } => J::Array(vec![
            J::String("fb_sample".into()),
            effect_arg_to_json(fb, terms, interner),
            J::String(s(*game_var)),
            effect_arg_to_json(grid_w, terms, interner),
            effect_arg_to_json(grid_h, terms, interner),
        ]),
        E::NetCollapse {
            reflex_net,
            input,
            target,
            eta,
        } => J::Array(vec![
            J::String("net_collapse".into()),
            J::String(s(*reflex_net)),
            effect_arg_to_json(input, terms, interner),
            effect_arg_to_json(target, terms, interner),
            effect_arg_to_json(eta, terms, interner),
        ]),
        E::TrackIdentity {
            prev,
            cur,
            feature_key,
            category_key,
            extent_key,
            identity_key,
            radius,
        } => J::Array(vec![
            J::String("track_identity".into()),
            effect_arg_to_json(prev, terms, interner),
            effect_arg_to_json(cur, terms, interner),
            J::String(s(*feature_key)),
            match category_key {
                Some(k) => J::String(s(*k)),
                None => J::Null,
            },
            match extent_key {
                Some(k) => J::String(s(*k)),
                None => J::Null,
            },
            J::String(s(*identity_key)),
            effect_arg_to_json(radius, terms, interner),
        ]),
    }
}

fn parse_effect_json(
    j: &J,
    terms: &mut TermArena,
    interner: &mut crate::sym::Interner,
) -> Result<crate::rewrite::Effect, String> {
    let arr = j
        .as_array()
        .ok_or_else(|| "effect must be an array".to_string())?;
    let kind = arr
        .first()
        .and_then(|v| v.as_str())
        .ok_or_else(|| "effect kind missing".to_string())?;
    let s = |i: usize| -> Result<String, String> {
        arr.get(i)
            .and_then(|v| v.as_str())
            .map(String::from)
            .ok_or_else(|| format!("effect arg {} must be str", i))
    };
    let arg_to_effect = |v: &J,
                         terms: &mut TermArena,
                         interner: &mut crate::sym::Interner|
     -> Result<crate::rewrite::EffectArg, String> {
        // `{"__term__": {...}}` → Computed; everything else → Literal.
        if let Some(obj) = v.as_object() {
            if let Some(inner) = obj.get("__term__") {
                let idx = crate::jsonio::term_from_json(inner, terms, interner)
                    .map_err(|e| format!("bad computed effect arg: {:?}", e))?;
                return Ok(crate::rewrite::EffectArg::Computed(idx));
            }
        }
        // Literal — decode through the same codec as graph attrs.
        Ok(crate::rewrite::EffectArg::Literal(
            crate::persist::decode_value(v, interner),
        ))
    };
    let attrs_dict = |arr_i: usize,
                      terms: &mut TermArena,
                      interner: &mut crate::sym::Interner|
     -> Result<Vec<(Sym, crate::rewrite::EffectArg)>, String> {
        let Some(raw) = arr.get(arr_i) else {
            return Ok(Vec::new());
        };
        let obj = raw
            .as_object()
            .ok_or_else(|| format!("effect attrs at {} must be object", arr_i))?;
        let mut out = Vec::with_capacity(obj.len());
        for (k, v) in obj {
            let arg = arg_to_effect(v, terms, interner)?;
            out.push((interner.intern(k), arg));
        }
        Ok(out)
    };
    match kind {
        "add_edge" => Ok(crate::rewrite::Effect::AddEdge {
            src_var: interner.intern(&s(1)?),
            edge_type: interner.intern(&s(2)?),
            tgt_var: interner.intern(&s(3)?),
            attrs: attrs_dict(4, terms, interner)?,
        }),
        "del_edge" => Ok(crate::rewrite::Effect::DelEdge {
            src_var: interner.intern(&s(1)?),
            edge_type: interner.intern(&s(2)?),
            tgt_var: interner.intern(&s(3)?),
        }),
        "add_node" => Ok(crate::rewrite::Effect::AddNode {
            new_var: interner.intern(&s(1)?),
            type_: interner.intern(&s(2)?),
            attrs: attrs_dict(3, terms, interner)?,
        }),
        // Mirror `add_node` wire shape — same args, AddNodeIfAbsent
        // dedup semantics. Wire form:
        //   ["add_node_if_absent", "<new_var>", "<NodeType>", {attrs}]
        // attrs double as the dedup key set: an existing node of the
        // given type whose attrs include every (k, v) here is reused
        // (no progress, no new NodeID), bound to `new_var` so following
        // effects in the rule still see a witness.
        "add_node_if_absent" => Ok(crate::rewrite::Effect::AddNodeIfAbsent {
            new_var: interner.intern(&s(1)?),
            type_: interner.intern(&s(2)?),
            attrs: attrs_dict(3, terms, interner)?,
        }),
        "del_node" => Ok(crate::rewrite::Effect::DelNode {
            var: interner.intern(&s(1)?),
        }),
        "set_attr" => {
            let var = interner.intern(&s(1)?);
            let key = interner.intern(&s(2)?);
            let raw = arr
                .get(3)
                .ok_or_else(|| "set_attr missing value".to_string())?;
            let value = arg_to_effect(raw, terms, interner)?;
            Ok(crate::rewrite::Effect::SetAttr { var, key, value })
        }
        // Mirror `set_attr` wire shape — same args, delta-only write.
        //   ["set_attr_if_different", "<var>", "<key>", <value-or-term>]
        // If the bound node's existing attr equals the resolved new
        // value, no write happens, no progress is recorded, no
        // UndoStep is emitted. Otherwise it behaves exactly like
        // SetAttr.
        "set_attr_if_different" => {
            let var = interner.intern(&s(1)?);
            let key = interner.intern(&s(2)?);
            let raw = arr
                .get(3)
                .ok_or_else(|| "set_attr_if_different missing value".to_string())?;
            let value = arg_to_effect(raw, terms, interner)?;
            Ok(crate::rewrite::Effect::SetAttrIfDifferent { var, key, value })
        }
        "replace_value" => Ok(crate::rewrite::Effect::ReplaceValue {
            old_var: interner.intern(&s(1)?),
            new_var: interner.intern(&s(2)?),
        }),
        "define_concept" => {
            // Shape: ["define_concept", <name>, <term-arg>]
            // `<name>` is either a bare string (literal) or a
            // `{"__term__": …}` dict (computed).
            // `<term-arg>` is also an `EffectArg`:
            //   - `{"__term__": <expr>}` → Computed: a Term that
            //     evaluates to a Dict-shaped Value (Term-JSON) at
            //     fire time, letting a rule synthesise the registered
            //     Term-tree from its match binding.
            //   - any other JSON object → Literal: parsed via
            //     `decode_value` into a `Value::Dict` mirroring the
            //     Term-JSON shape; the applier walks it back through
            //     `encode_value` + `term_from_json` at fire time. This
            //     preserves the original "registered term given at
            //     rule-construction time" behaviour with the parse
            //     deferred to apply time.
            // Both arms share the same wire shape — the applier
            // pipes whatever Value falls out through `term_from_json`,
            // so authoring stays a single `arg_to_effect` codec call.
            let name_raw = arr
                .get(1)
                .ok_or_else(|| "define_concept missing name".to_string())?;
            let name = arg_to_effect(name_raw, terms, interner)?;
            let term_raw = arr
                .get(2)
                .ok_or_else(|| "define_concept missing term".to_string())?;
            let term = arg_to_effect(term_raw, terms, interner)?;
            Ok(crate::rewrite::Effect::DefineConcept { name, term })
        }
        "set_rule_clause" => {
            // INTRINSIC SELF-REPAIR (struct-rule path). Shape:
            //   ["set_rule_clause", <rule_name>, <field>, <clause-arg>]
            // <rule_name> and <field> ("where"|"effect") are EffectArgs (literal
            // string or {"__term__": …} computed); <clause-arg> evaluates to the
            // wire JSON for the new clause (a Term for "where", an effect list for
            // "effect"). Queued + applied between passes by Substrate::run_rules.
            let rule_name = arg_to_effect(
                arr.get(1)
                    .ok_or_else(|| "set_rule_clause missing rule_name".to_string())?,
                terms,
                interner,
            )?;
            let field = arg_to_effect(
                arr.get(2)
                    .ok_or_else(|| "set_rule_clause missing field".to_string())?,
                terms,
                interner,
            )?;
            let term = arg_to_effect(
                arr.get(3)
                    .ok_or_else(|| "set_rule_clause missing clause term".to_string())?,
                terms,
                interner,
            )?;
            Ok(crate::rewrite::Effect::SetRuleClause {
                rule_name,
                field,
                term,
            })
        }
        "apply_rule_patch" => {
            // Shape: ["apply_rule_patch", "<bound_rule_patch_var>"].
            // The bound node is the complete graph-native transaction.
            Ok(crate::rewrite::Effect::ApplyRulePatch {
                patch_var: interner.intern(&s(1)?),
            })
        }
        // PERCEPTION-AS-ACTION: a rule triggers a shared-memory
        // framebuffer sample. Shape:
        //   ["fb_sample", <fb_id-or-term>, "<game_var>", <grid_w-or-term>, <grid_h-or-term>]
        // `<fb_id>` / `<grid_w>` / `<grid_h>` are EffectArgs (literal
        // number or `{"__term__": …}` computed); `<game_var>` is a bare
        // var name already bound by the rule's match/where (the
        // WorldInstance/game root `segment_and_track` mints/updates
        // Regions under) — same convention as `AddEdge`'s src_var/
        // tgt_var. Queued onto `graph.pending_fb_samples`; drained by
        // `Substrate::run_rules` between passes, which calls the same
        // `Substrate::fb_sample` the PyO3 `fb_sample` method calls.
        "fb_sample" => {
            let fb = arg_to_effect(
                arr.get(1)
                    .ok_or_else(|| "fb_sample missing fb_id".to_string())?,
                terms,
                interner,
            )?;
            let game_var = interner.intern(&s(2)?);
            let grid_w = arg_to_effect(
                arr.get(3)
                    .ok_or_else(|| "fb_sample missing grid_w".to_string())?,
                terms,
                interner,
            )?;
            let grid_h = arg_to_effect(
                arr.get(4)
                    .ok_or_else(|| "fb_sample missing grid_h".to_string())?,
                terms,
                interner,
            )?;
            Ok(crate::rewrite::Effect::FbSample {
                fb,
                game_var,
                grid_w,
                grid_h,
            })
        }
        // SELF-TRAINING: a rule fires one surprise-driven weight collapse of
        // a reflex net inside run_rules. Shape:
        //   ["net_collapse", "<reflex_net_var>", <input-term>, <target-term>, <eta-term>]
        // reflex_net_var is bound by the match; input/target/eta are
        // EffectArgs (typically Attr(obs,"input_vec"), Attr(obs,"target"),
        // Attr(rn,"eta")). Queued onto graph.pending_net_collapses; drained
        // by Substrate::run_rules via net_forward::net_collapse_step.
        "net_collapse" => {
            let reflex_net = interner.intern(&s(1)?);
            let input = arg_to_effect(
                arr.get(2)
                    .ok_or_else(|| "net_collapse missing input".to_string())?,
                terms,
                interner,
            )?;
            let target = arg_to_effect(
                arr.get(3)
                    .ok_or_else(|| "net_collapse missing target".to_string())?,
                terms,
                interner,
            )?;
            let eta = arg_to_effect(
                arr.get(4)
                    .ok_or_else(|| "net_collapse missing eta".to_string())?,
                terms,
                interner,
            )?;
            Ok(crate::rewrite::Effect::NetCollapse {
                reflex_net,
                input,
                target,
                eta,
            })
        }
        // GRAPH LAW #6: a rule triggers domain-general trans-frame
        // identity assignment. Shape:
        //   ["track_identity", <prev-term>, <cur-term>, "<feature_key>",
        //    <"category_key"|null>, <"extent_key"|null>, "<identity_key>",
        //    <radius-or-term>]
        // `<prev>`/`<cur>` are EffectArgs resolving to Node collections;
        // `<radius>` is an EffectArg resolving to a number; the four key
        // names are fixed strings (interned at parse time, same
        // convention `AddNode`'s type_ uses) — `category_key`/
        // `extent_key` are nullable. Queued onto
        // `graph.pending_track_identity`; drained by `Substrate::
        // run_rules` between passes via `Substrate::track_identity`.
        "track_identity" => {
            let prev = arg_to_effect(
                arr.get(1)
                    .ok_or_else(|| "track_identity missing prev".to_string())?,
                terms,
                interner,
            )?;
            let cur = arg_to_effect(
                arr.get(2)
                    .ok_or_else(|| "track_identity missing cur".to_string())?,
                terms,
                interner,
            )?;
            let feature_key = interner.intern(&s(3)?);
            let category_key = match arr.get(4) {
                Some(J::String(k)) => Some(interner.intern(k)),
                _ => None,
            };
            let extent_key = match arr.get(5) {
                Some(J::String(k)) => Some(interner.intern(k)),
                _ => None,
            };
            let identity_key = interner.intern(&s(6)?);
            let radius = arg_to_effect(
                arr.get(7)
                    .ok_or_else(|| "track_identity missing radius".to_string())?,
                terms,
                interner,
            )?;
            Ok(crate::rewrite::Effect::TrackIdentity {
                prev,
                cur,
                feature_key,
                category_key,
                extent_key,
                identity_key,
                radius,
            })
        }
        other => Err(format!("unknown effect kind: {}", other)),
    }
}

// --- Reflex JSON parsing (seed manifests) ----------------------------------

/// Load one `"reflexes"` manifest entry: `{name, stimulus: <Term JSON>,
/// response, refractory_ticks}`. Materialises `stimulus` as a subgraph
/// via the same path `add_term_subgraph` uses
/// (`reflect::term_to_subgraph`), creates the `Reflex` node, and wires
/// `agent_root -has_reflex-> reflex -stimulus_term-> subgraph_root` —
/// mirroring `world_adapter.install_reflex`'s shape exactly (attrs +
/// `last_fired_tick: -1_000_000_000` / `fire_count: 0`, its fresh-reflex
/// defaults) so a seed-loaded reflex is indistinguishable from a
/// runtime-installed one. `agent_root` may be `None` (a manifest loaded
/// without a root_node) — the Reflex node + its stimulus subgraph still
/// get created; only the `has_reflex` edge is skipped, since a Reflex
/// node is independently discoverable by scanning `nodes("Reflex")`.
/// Mechanical loader code — no agent decision here, purely JSON → graph
/// mutation (this is the manifest loader itself, same status as the
/// `rules` section just above).
fn load_reflex_json(
    j: &J,
    inner: &mut SubstrateRs,
    agent_root: Option<NodeID>,
) -> Result<(), String> {
    let obj = j
        .as_object()
        .ok_or_else(|| "reflex must be an object".to_string())?;
    let name = obj
        .get("name")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "missing 'name'".to_string())?;
    let response = obj
        .get("response")
        .and_then(|v| v.as_str())
        .ok_or_else(|| "missing 'response'".to_string())?;
    let refractory_ticks = obj
        .get("refractory_ticks")
        .and_then(|v| v.as_i64())
        .unwrap_or(0);
    // ORDER 0 IS INVOLUNTARY: an `autonomous` reflex fires inside the engine's
    // own cycle and is never offered to the host dispatch loop.  Absent reads
    // 0, so every reflex authored before this key keeps the host path exactly.
    let autonomous = obj
        .get("autonomous")
        .and_then(|v| v.as_i64().or_else(|| v.as_f64().map(|f| f as i64)))
        .unwrap_or(0);
    let stimulus = obj
        .get("stimulus")
        .ok_or_else(|| "missing 'stimulus'".to_string())?;

    let idx = term_from_json(stimulus, &mut inner.terms, &mut inner.interner)
        .map_err(|e| format!("bad stimulus Term: {:?}", e))?;
    let stim_root =
        crate::reflect::term_to_subgraph(&inner.terms, idx, &mut inner.graph, &mut inner.interner);

    let reflex_type = inner.interner.intern("Reflex");
    let mut attrs: FxHashMap<Sym, Value> = FxHashMap::default();
    attrs.insert(
        inner.interner.intern("name"),
        Value::Str(inner.interner.intern(name)),
    );
    attrs.insert(
        inner.interner.intern("response"),
        Value::Str(inner.interner.intern(response)),
    );
    attrs.insert(
        inner.interner.intern("refractory_ticks"),
        Value::Int(refractory_ticks),
    );
    attrs.insert(
        inner.interner.intern("last_fired_tick"),
        Value::Int(-1_000_000_000),
    );
    attrs.insert(inner.interner.intern("fire_count"), Value::Int(0));
    attrs.insert(inner.interner.intern("autonomous"), Value::Int(autonomous));
    let reflex_nid = inner.add_node(reflex_type, attrs);

    let has_reflex = inner.interner.intern("has_reflex");
    let stimulus_term = inner.interner.intern("stimulus_term");
    if let Some(agent) = agent_root {
        let _ = inner
            .graph
            .insert_edge(agent, has_reflex, reflex_nid, FxHashMap::default());
    }
    let _ = inner
        .graph
        .insert_edge(reflex_nid, stimulus_term, stim_root, FxHashMap::default());
    Ok(())
}

#[cfg(test)]
mod reflex_manifest_tests {
    use super::*;
    use crate::checker::ConsistencyChecker;
    use crate::grammar::Grammar;

    fn fresh_substrate() -> SubstrateRs {
        SubstrateRs::new(ConsistencyChecker::new(Grammar::new()))
    }

    /// A well-formed `"reflexes"` manifest entry creates a `Reflex` node
    /// (attrs name/response/refractory_ticks/last_fired_tick/fire_count
    /// at `install_reflex`'s fresh-reflex defaults), materialises its
    /// stimulus Term as a subgraph, and wires
    /// `agent -has_reflex-> reflex -stimulus_term-> subgraph_root`.
    #[test]
    fn loads_one_reflex_and_wires_agent() {
        let mut s = fresh_substrate();
        let agent_type = s.interner.intern("Agent");
        let agent = s.add_node(agent_type, FxHashMap::default());

        let entry = serde_json::json!({
            "name": "question_pursue",
            "stimulus": {"type": "Lit", "value": true},
            "response": "question_pursue",
            "refractory_ticks": 2,
        });
        load_reflex_json(&entry, &mut s, Some(agent)).expect("well-formed reflex must load");

        let reflex_type = s.interner.lookup("Reflex").expect("Reflex type interned");
        let reflexes = s.graph.nodes_of_type(reflex_type);
        assert_eq!(reflexes.len(), 1, "exactly one Reflex node created");
        let reflex_nid = reflexes[0];
        let attrs = &s.graph.node(reflex_nid).attrs;
        let name_key = s.interner.intern("name");
        let response_key = s.interner.intern("response");
        let refractory_key = s.interner.intern("refractory_ticks");
        let last_fired_key = s.interner.intern("last_fired_tick");
        let fire_count_key = s.interner.intern("fire_count");
        assert_eq!(
            attrs.get(&name_key),
            Some(&Value::Str(s.interner.lookup("question_pursue").unwrap()))
        );
        assert_eq!(
            attrs.get(&response_key),
            Some(&Value::Str(s.interner.lookup("question_pursue").unwrap()))
        );
        assert_eq!(attrs.get(&refractory_key), Some(&Value::Int(2)));
        assert_eq!(
            attrs.get(&last_fired_key),
            Some(&Value::Int(-1_000_000_000))
        );
        assert_eq!(attrs.get(&fire_count_key), Some(&Value::Int(0)));

        // agent -has_reflex-> reflex
        let has_reflex = s.interner.intern("has_reflex");
        let via_has_reflex = s.graph.neighbours(agent, Some(has_reflex));
        assert_eq!(via_has_reflex, vec![reflex_nid]);

        // reflex -stimulus_term-> a Term.Lit subgraph root
        let stimulus_term = s.interner.intern("stimulus_term");
        let stim_targets = s.graph.neighbours(reflex_nid, Some(stimulus_term));
        assert_eq!(stim_targets.len(), 1, "exactly one stimulus_term edge");
        let stim_root = stim_targets[0];
        assert_eq!(
            s.interner.resolve(s.graph.node(stim_root).type_),
            "Term.Lit"
        );
    }

    /// No `root_node`/agent: the Reflex node + its stimulus subgraph
    /// still get created (independently discoverable via
    /// `nodes("Reflex")`), only the `has_reflex` edge is skipped.
    #[test]
    fn loads_reflex_without_agent_root() {
        let mut s = fresh_substrate();
        let entry = serde_json::json!({
            "name": "no_agent_reflex",
            "stimulus": {"type": "Lit", "value": 1},
            "response": "noop",
        });
        load_reflex_json(&entry, &mut s, None).expect("reflex without agent_root must still load");
        let reflex_type = s.interner.lookup("Reflex").expect("Reflex type interned");
        assert_eq!(s.graph.nodes_of_type(reflex_type).len(), 1);
        // refractory_ticks defaults to 0 when absent.
        let reflex_nid = s.graph.nodes_of_type(reflex_type)[0];
        let refractory_key = s.interner.intern("refractory_ticks");
        assert_eq!(
            s.graph.node(reflex_nid).attrs.get(&refractory_key),
            Some(&Value::Int(0))
        );
    }

    /// Malformed entries (missing a required field) are reported as an
    /// `Err`, not a panic — the manifest loader's per-entry loop (in
    /// `load_seed_manifest`) turns this into a logged warning + skip,
    /// same resilience as the `rules` section.
    #[test]
    fn malformed_reflex_is_an_error_not_a_panic() {
        let mut s = fresh_substrate();
        let missing_response = serde_json::json!({
            "name": "bad",
            "stimulus": {"type": "Lit", "value": 1},
        });
        assert!(load_reflex_json(&missing_response, &mut s, None).is_err());

        let missing_stimulus = serde_json::json!({
            "name": "bad2",
            "response": "noop",
        });
        assert!(load_reflex_json(&missing_stimulus, &mut s, None).is_err());

        let not_an_object = serde_json::json!(["not", "an", "object"]);
        assert!(load_reflex_json(&not_an_object, &mut s, None).is_err());

        // None of the malformed attempts should have left a Reflex node behind.
        let reflex_type = s.interner.intern("Reflex");
        assert_eq!(s.graph.nodes_of_type(reflex_type).len(), 0);
    }
}

// Plain impl block for internal helpers — kept outside #[pymethods] so
// `fire_hook` isn't surfaced as a Python method.
impl PySubstrate {
    /// Invoke every callback registered for `event`. Tolerant of
    /// per-callback errors — one bad callback shouldn't tear down the
    /// substrate mutation, but the error is surfaced via the first
    /// `Err` we encounter. Callbacks happen on the same Python thread
    /// that initiated the mutation.
    fn fire_hook(&self, py: Python<'_>, event: &str, args: &[PyObject]) -> PyResult<()> {
        let Some(callbacks) = self.hooks.get(event) else {
            return Ok(());
        };
        for cb in callbacks {
            let py_args = PyTuple::new_bound(py, args);
            cb.bind(py).call1(py_args)?;
        }
        Ok(())
    }
}

// --- top-level value encode/decode (for callers that want to drive --------
//      the Python codec without owning a substrate; mirrors persistence.py)

/// The nine per-term contributions of the last humanoid plan scored on this
/// thread, as {name: value}.  OBSERVABILITY ONLY -- a mechanical read of a
/// thread-local the composer writes; nothing here decides anything, and the
/// cost sum is byte-identical with or without it.  Pays the debt registered
/// in CONTACT_WRENCH_PREREG.md ("report per-term contributions; a measure
/// with one live component has replaced one category with another").
#[pyfunction]
fn humanoid_cost_terms(py: Python<'_>) -> PyResult<Py<PyAny>> {
    let values = crate::motor_compose::last_humanoid_cost_terms();
    let out = pyo3::types::PyDict::new_bound(py);
    for (name, value) in crate::motor_compose::HUMANOID_COST_TERM_NAMES
        .iter()
        .zip(values.iter())
    {
        out.set_item(*name, *value)?;
    }
    Ok(out.into_any().unbind())
}

#[pyfunction]
fn encode<'py>(py: Python<'py>, value: &Bound<'_, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    // The Python codec works with a fresh interner; we mint one here
    // and don't keep the resulting Syms — they get resolved straight
    // back to strings by the JSON encoder.
    let mut interner = crate::sym::Interner::new();
    let v = py_to_value(py, value, &mut interner)?;
    let j = encode_value(&v, &interner);
    json_to_pyobj(py, &j)
}

#[pyfunction]
fn decode<'py>(py: Python<'py>, value: &Bound<'_, PyAny>) -> PyResult<Bound<'py, PyAny>> {
    let j = pyobj_to_json(py, value)?;
    let mut interner = crate::sym::Interner::new();
    let v = decode_value(&j, &mut interner);
    value_to_py(py, &v, &interner)
}

/// k-means clustering of `n` `d`-dim vectors (flat row-major `data`) into `k` centroids — the LEARNING
/// primitive for the agent's sub-stroke library (BPL's generative vocabulary). Deterministic init
/// (evenly-spaced samples) + Lloyd's iterations; no RNG. Returns the k*d flat centroids. A numerical
/// primitive at the I/O boundary (like `cochleagram`); the world adapter feeds background descriptors,
/// the agent holds the returned library as graph data.
#[pyfunction]
fn kmeans(data: Vec<f64>, n: usize, d: usize, k: usize, iters: usize) -> Vec<f64> {
    if n == 0 || d == 0 || k == 0 {
        return vec![0.0; k.max(1) * d.max(1)];
    }
    let kk = k.min(n);
    let mut cent = vec![0.0f64; kk * d];
    for j in 0..kk {
        let idx = (j * n) / kk;
        for c in 0..d {
            cent[j * d + c] = data[idx * d + c];
        }
    }
    let mut assign = vec![0usize; n];
    for _ in 0..iters {
        for i in 0..n {
            let mut best = f64::INFINITY;
            let mut bj = 0;
            for j in 0..kk {
                let mut s = 0.0;
                for c in 0..d {
                    let dd = data[i * d + c] - cent[j * d + c];
                    s += dd * dd;
                }
                if s < best {
                    best = s;
                    bj = j;
                }
            }
            assign[i] = bj;
        }
        let mut sum = vec![0.0f64; kk * d];
        let mut cnt = vec![0usize; kk];
        for i in 0..n {
            let j = assign[i];
            cnt[j] += 1;
            for c in 0..d {
                sum[j * d + c] += data[i * d + c];
            }
        }
        for j in 0..kk {
            if cnt[j] > 0 {
                for c in 0..d {
                    cent[j * d + c] = sum[j * d + c] / cnt[j] as f64;
                }
            }
        }
    }
    // pad to the requested k (if clamped) so the histogram dimension is stable.
    cent.resize(k * d, 0.0);
    cent
}

/// Per-primitive FULL PRECISION: for each of `k` centroids, the inverse of the (ridge-regularised) full
/// covariance of the `d`-dim parts assigned to it — the per-primitive Gaussian's precision matrix, which
/// captures CORRELATED deformation modes (e.g. a stroke bending = points moving together) a diagonal std
/// cannot. Returns `k*d*d` (row-major precision per primitive). `ridge` is added to the covariance diagonal
/// so the inverse is well-conditioned even when a cluster has few samples. The BPL token model's covariance.
#[pyfunction]
fn cluster_precision(
    data: Vec<f64>,
    n: usize,
    d: usize,
    cent: Vec<f64>,
    k: usize,
    ridge: f64,
) -> Vec<f64> {
    let mut assign = vec![0usize; n];
    for i in 0..n {
        let mut best = f64::INFINITY;
        let mut bj = 0usize;
        for j in 0..k {
            let mut s = 0.0;
            for c in 0..d {
                let dd = data[i * d + c] - cent[j * d + c];
                s += dd * dd;
            }
            if s < best {
                best = s;
                bj = j;
            }
        }
        assign[i] = bj;
    }
    let floor = if ridge > 1e-9 { ridge } else { 1e-3 };
    let mut out = vec![0.0f64; k * d * d];
    for j in 0..k {
        let pts: Vec<usize> = (0..n).filter(|&i| assign[i] == j).collect();
        let m = pts.len();
        let mut mean = vec![0.0f64; d];
        for &i in &pts {
            for c in 0..d {
                mean[c] += data[i * d + c];
            }
        }
        if m > 0 {
            for c in 0..d {
                mean[c] /= m as f64;
            }
        }
        // covariance + ridge on the diagonal
        let mut cov = vec![0.0f64; d * d];
        for &i in &pts {
            for a in 0..d {
                let da = data[i * d + a] - mean[a];
                for b in 0..d {
                    cov[a * d + b] += da * (data[i * d + b] - mean[b]);
                }
            }
        }
        let denom = (m.max(2) - 1) as f64;
        for a in 0..d {
            for b in 0..d {
                cov[a * d + b] /= denom;
            }
            cov[a * d + a] += floor;
        }
        // invert via Gauss-Jordan (general d x d); fall back to ridge*I if singular
        let mut aug = vec![0.0f64; d * 2 * d];
        for r in 0..d {
            for c in 0..d {
                aug[r * 2 * d + c] = cov[r * d + c];
            }
            aug[r * 2 * d + d + r] = 1.0;
        }
        let mut ok = true;
        for col in 0..d {
            let mut piv = col;
            for r in (col + 1)..d {
                if aug[r * 2 * d + col].abs() > aug[piv * 2 * d + col].abs() {
                    piv = r;
                }
            }
            if aug[piv * 2 * d + col].abs() < 1e-12 {
                ok = false;
                break;
            }
            if piv != col {
                for c in 0..2 * d {
                    aug.swap(col * 2 * d + c, piv * 2 * d + c);
                }
            }
            let pv = aug[col * 2 * d + col];
            for c in 0..2 * d {
                aug[col * 2 * d + c] /= pv;
            }
            for r in 0..d {
                if r == col {
                    continue;
                }
                let f = aug[r * 2 * d + col];
                if f != 0.0 {
                    for c in 0..2 * d {
                        aug[r * 2 * d + c] -= f * aug[col * 2 * d + c];
                    }
                }
            }
        }
        for a in 0..d {
            for b in 0..d {
                out[j * d * d + a * d + b] = if ok {
                    aug[a * 2 * d + d + b]
                } else if a == b {
                    1.0 / floor
                } else {
                    0.0
                };
            }
        }
    }
    out
}

/// Per-primitive DEFORMATION SPREAD: for each of `k` learned centroids, the per-dimension standard
/// deviation of the `n` `d`-dim parts assigned to it (nearest centroid). A diagonal Gaussian per
/// primitive — the learned generative deformation model BPL's per-primitive token model approximates.
/// `ridge` floors the std so a near-degenerate dimension does not blow up the whitened metric. Returns
/// `k*d` stds; whitening a part by `(x - centroid) / std` of its nearest primitive turns the per-part
/// distance into a Mahalanobis metric that costs the primitive's NATURAL deformation directions less —
/// structure-preserving (the part stays a part, only its metric is learned). Numerical primitive.
#[pyfunction]
fn cluster_deform_stats(
    data: Vec<f64>,
    n: usize,
    d: usize,
    cent: Vec<f64>,
    k: usize,
    ridge: f64,
) -> Vec<f64> {
    let mut sum = vec![0.0f64; k * d];
    let mut sq = vec![0.0f64; k * d];
    let mut cnt = vec![0usize; k];
    for i in 0..n {
        let mut best = f64::INFINITY;
        let mut bj = 0usize;
        for j in 0..k {
            let mut s = 0.0;
            for c in 0..d {
                let dd = data[i * d + c] - cent[j * d + c];
                s += dd * dd;
            }
            if s < best {
                best = s;
                bj = j;
            }
        }
        cnt[bj] += 1;
        for c in 0..d {
            let v = data[i * d + c];
            sum[bj * d + c] += v;
            sq[bj * d + c] += v * v;
        }
    }
    let floor = if ridge > 1e-9 { ridge } else { 1e-6 };
    let mut out = vec![floor; k * d];
    for j in 0..k {
        if cnt[j] > 1 {
            let m = cnt[j] as f64;
            for c in 0..d {
                let mean = sum[j * d + c] / m;
                let var = (sq[j * d + c] / m - mean * mean).max(0.0);
                out[j * d + c] = var.sqrt().max(floor);
            }
        }
    }
    out
}

fn _soft_thr(v: f64, t: f64) -> f64 {
    if v > t {
        v - t
    } else if v < -t {
        v + t
    } else {
        0.0
    }
}

fn _l2norm(v: &mut [f64]) {
    let s: f64 = v.iter().map(|x| x * x).sum::<f64>().sqrt();
    if s > 1e-9 {
        for x in v.iter_mut() {
            *x /= s;
        }
    }
}

/// ISTA sparse inference: code `a` (k) for `x` (d) under dictionary `dict` (k*d) = argmin ||x - D^T a||^2 +
/// lam|a|_1 via iterated soft-thresholded gradient steps (biologically = recurrent lateral inhibition).
fn _ista(
    x: &[f64],
    dict: &[f64],
    k: usize,
    d: usize,
    lam: f64,
    step: f64,
    iters: usize,
) -> Vec<f64> {
    let mut a = vec![0.0f64; k];
    for _ in 0..iters {
        let mut recon = vec![0.0f64; d];
        for j in 0..k {
            let aj = a[j];
            if aj != 0.0 {
                let b = j * d;
                for c in 0..d {
                    recon[c] += aj * dict[b + c];
                }
            }
        }
        for j in 0..k {
            let b = j * d;
            let mut g = 0.0;
            for c in 0..d {
                g += dict[b + c] * (x[c] - recon[c]);
            }
            a[j] = _soft_thr(a[j] + step * g, step * lam);
        }
    }
    a
}

/// SPARSE CODING (Olshausen & Field) — learn an OVERCOMPLETE dictionary of `k` atoms over `n` `d`-dim samples
/// by alternating sparse INFERENCE (ISTA) with a LOCAL HEBBIAN dictionary update (ΔD_j ∝ a_j * residual, then
/// renormalise the atom). Structure-PRESERVING (a reconstructive basis, NOT a quantiser like kmeans) and
/// biologically plausible (V1 receptive-field learning). Deterministic init (evenly-spaced samples), no RNG.
/// Returns the k*d flat dictionary — the agent's generative stroke-primitive basis, held as graph data.
#[pyfunction]
fn sparse_dict_learn(
    data: Vec<f64>,
    n: usize,
    d: usize,
    k: usize,
    lam: f64,
    epochs: usize,
    lr: f64,
    infer_iters: usize,
    step: f64,
) -> Vec<f64> {
    if n == 0 || d == 0 || k == 0 {
        return vec![0.0; k.max(1) * d.max(1)];
    }
    let mut dict = vec![0.0f64; k * d];
    for j in 0..k {
        let idx = (j * n) / k;
        for c in 0..d {
            dict[j * d + c] = data[idx * d + c];
        }
        _l2norm(&mut dict[j * d..(j + 1) * d]);
    }
    for _ep in 0..epochs {
        for i in 0..n {
            let x = &data[i * d..(i + 1) * d];
            let a = _ista(x, &dict, k, d, lam, step, infer_iters);
            let mut recon = vec![0.0f64; d];
            for j in 0..k {
                let aj = a[j];
                if aj != 0.0 {
                    let b = j * d;
                    for c in 0..d {
                        recon[c] += aj * dict[b + c];
                    }
                }
            }
            for j in 0..k {
                let aj = a[j];
                if aj != 0.0 {
                    let b = j * d;
                    for c in 0..d {
                        dict[b + c] += lr * aj * (x[c] - recon[c]);
                    }
                    _l2norm(&mut dict[b..b + d]);
                }
            }
        }
    }
    dict
}

/// Sparse-encode `m` `d`-dim vectors against a learned `k`*`d` dictionary (ISTA). Returns m*k flat codes —
/// each vector's composition over the learned generative basis (structure-preserving, sparse).
#[pyfunction]
fn sparse_encode(
    data: Vec<f64>,
    m: usize,
    d: usize,
    dict: Vec<f64>,
    k: usize,
    lam: f64,
    infer_iters: usize,
    step: f64,
) -> Vec<f64> {
    let mut out = vec![0.0f64; m * k];
    for i in 0..m {
        let a = _ista(
            &data[i * d..(i + 1) * d],
            &dict,
            k,
            d,
            lam,
            step,
            infer_iters,
        );
        for j in 0..k {
            out[i * k + j] = a[j];
        }
    }
    out
}

/// Soft BAG-OF-PRIMITIVES histogram of `n` `d`-dim descriptors over the learned `k` centroids: each
/// descriptor soft-assigned (softmax over -distance, temperature `beta`), accumulated, L2-normalised
/// (so a dot product of two histograms is their cosine). The character's composition over the learned
/// vocabulary — a writer-invariant feature. Numerical primitive; the world adapter stores the result.
#[pyfunction]
fn bow_histogram(
    data: Vec<f64>,
    n: usize,
    d: usize,
    cent: Vec<f64>,
    k: usize,
    beta: f64,
) -> Vec<f64> {
    let mut h = vec![0.0f64; k];
    if n == 0 || k == 0 {
        return h;
    }
    for i in 0..n {
        let mut dist = vec![0.0f64; k];
        let mut mn = f64::INFINITY;
        for j in 0..k {
            let mut s = 0.0;
            for c in 0..d {
                let dd = data[i * d + c] - cent[j * d + c];
                s += dd * dd;
            }
            dist[j] = s;
            if s < mn {
                mn = s;
            }
        }
        let mut z = 0.0;
        for j in 0..k {
            dist[j] = (-beta * (dist[j] - mn)).exp();
            z += dist[j];
        }
        if z > 0.0 {
            for j in 0..k {
                h[j] += dist[j] / z;
            }
        }
    }
    let nrm: f64 = h.iter().map(|x| x * x).sum::<f64>().sqrt();
    if nrm > 1e-9 {
        for v in h.iter_mut() {
            *v /= nrm;
        }
    }
    h
}

// --- temporal fine structure (Gap 1) --------------------------------------
//
// The agent's TFS primitives, exposed at the I/O boundary so a world
// adapter / front-end cue extractor can hand a gammatone band's fine
// waveform in and read the phase-locked temporal code out. These are
// thin one-line hand-offs to `audio_primitives` — no logic here.

/// One gammatone band's FINE WAVEFORM (the carrier, NOT the envelope).
/// Thin hand-off so a front-end can feed the band into `band_autocorr`
/// for the TFS / phase-lock readout. The cochlear band the place code
/// reads its envelope off and the temporal code reads its periodicity off.
#[pyfunction]
fn gammatone_band(samples: Vec<f32>, fs: u32, fc: f32, order: u32) -> Vec<f32> {
    crate::audio_primitives::gammatone_band(&samples, fs, fc, order)
}

/// The agent's gammatone cochleagram (32 log bands 80..7500 Hz) in Rust — returns the
/// (n_frames x 32) map flattened row-major (frame, band). Sensory transduction.
#[pyfunction]
fn cochleagram(x: Vec<f32>, fs: u32, env_cut: f32, dur_cut: f32, n_frames: usize) -> Vec<f32> {
    crate::audio_primitives::cochleagram(&x, fs, env_cut, dur_cut, n_frames)
}

/// Train the CONTEXT-PREDICTIVE FRONT-END (autoregressive predictive
/// coding; see `apc.rs`) — a Rust-native, label-free stand-in for
/// wav2vec2-from-scratch. `frames_flat` = all utterance sequences
/// concatenated (each frame `din` floats, row-major); `seq_lens` = each
/// utterance's frame count. Returns the flat model weights consumed by
/// the `ApcEncode` Term. The heavy numeric SGD+BPTT loop is entirely in
/// Rust — the world adapter calls this one line, no reasoning in Python.
/// `shuffle_future` is the negative control (predict a shuffled future).
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn apc_train(
    frames_flat: Vec<f32>,
    seq_lens: Vec<usize>,
    din: usize,
    dh: usize,
    k_ahead: usize,
    epochs: usize,
    lr: f32,
    bidir: bool,
    seed: u64,
    shuffle_future: bool,
) -> Vec<f32> {
    crate::apc::train(
        &frames_flat,
        &seq_lens,
        din,
        dh,
        k_ahead,
        epochs,
        lr,
        bidir,
        seed,
        shuffle_future,
    )
}

/// Train the CONTEXT-PREDICTIVE FRONT-END WITH an InfoNCE contrastive head
/// (see `apc::train_contrastive`) — same predictive objective as
/// `apc_train`, PLUS a same-word-positive / different-word-negative
/// in-batch InfoNCE loss over MEAN-POOLED word-span embeddings (the
/// MMS-bootstrap `(word, f0, f1)` spans already extracted by the world
/// adapter — `word_seq_idx`/`word_start`/`word_end`/`word_id` are their
/// flattened per-occurrence metadata, `word_id` an integer word-identity
/// id). `lambda_nce` weights the InfoNCE gradient folded into the same BPTT
/// sweep as the predictive loss; `tau` is the softmax temperature;
/// `batch_size` = utterances per mini-batch (forward-only pass for the
/// in-batch negative pool, per-utterance BPTT+update). `shuffle_word_id` is
/// the CONTROL: permute word ids within each batch, destroying the
/// same-word structure — a real gain must collapse under it. The
/// gradient/training math is entirely in Rust; this is a one-line hand-off.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn apc_train_contrastive(
    frames_flat: Vec<f32>,
    seq_lens: Vec<usize>,
    din: usize,
    dh: usize,
    k_ahead: usize,
    epochs: usize,
    lr: f32,
    bidir: bool,
    seed: u64,
    shuffle_future: bool,
    word_seq_idx: Vec<usize>,
    word_start: Vec<usize>,
    word_end: Vec<usize>,
    word_id: Vec<i64>,
    lambda_nce: f32,
    tau: f32,
    batch_size: usize,
    shuffle_word_id: bool,
) -> Vec<f32> {
    crate::apc::train_contrastive(
        &frames_flat,
        &seq_lens,
        din,
        dh,
        k_ahead,
        epochs,
        lr,
        bidir,
        seed,
        shuffle_future,
        &word_seq_idx,
        &word_start,
        &word_end,
        &word_id,
        lambda_nce,
        tau,
        batch_size,
        shuffle_word_id,
    )
}

/// Train the MASKED-FRAME CONTRASTIVE PREDICTIVE CODING front-end (Step C
/// OBJECTIVE lever; see `apc::train_masked_cpc`): mask a fraction of frames,
/// encode with bidirectional context, predict each masked frame's TRUE-frame
/// target CONTRASTIVELY (in-batch InfoNCE over frames) — the wav2vec2-style
/// objective AR-APC lacks. Label-free (no word spans). `shuffle_ctrl`
/// permutes the positive assignment = the CONTROL. Emits the SAME model
/// layout as `apc_train`, so `ApcEncode` reads it unchanged.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn apc_train_masked_cpc(
    frames_flat: Vec<f32>,
    seq_lens: Vec<usize>,
    din: usize,
    dh: usize,
    epochs: usize,
    lr: f32,
    bidir: bool,
    seed: u64,
    mask_prob: f32,
    mask_span: usize,
    dt: usize,
    tau: f32,
    batch_size: usize,
    shuffle_ctrl: bool,
) -> Vec<f32> {
    crate::apc::train_masked_cpc(
        &frames_flat,
        &seq_lens,
        din,
        dh,
        epochs,
        lr,
        bidir,
        seed,
        mask_prob,
        mask_span,
        dt,
        tau,
        batch_size,
        shuffle_ctrl,
    )
}

/// Batched cross-speaker NN-recall + d' over `n` trajectories (each `t`
/// frames x `dim`, flat row-major) — reuses the DtwTo banded-DTW kernel
/// (`apc::nn_recall_and_dprime`). Returns [recall, dprime, pos_mean,
/// neg_mean]. A fast measurement helper so the two-lever ablation can use
/// the FULL candidate pool (guaranteed-support) without per-pair Python
/// marshalling; the distance is identical to the held DtwTo Term.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn apc_recall(
    trajs: Vec<f32>,
    n: usize,
    t: usize,
    dim: usize,
    words: Vec<i64>,
    spk: Vec<i64>,
    cap_q: usize,
    n_pos: usize,
    n_neg: usize,
    seed: u64,
) -> Vec<f32> {
    crate::apc::nn_recall_and_dprime(&trajs, n, t, dim, &words, &spk, cap_q, n_pos, n_neg, seed)
}

/// DETAIL variant of `apc_recall` for BOOTSTRAP CIs: returns raw per-query
/// hit indicators + the sampled pos/neg distances (identical kernel + pool +
/// selection as `apc_recall`), flat-packed as `[n_hit, hits..., n_pos,
/// pos..., n_neg, neg...]`. See `apc::nn_recall_detail`.
#[pyfunction]
#[allow(clippy::too_many_arguments)]
fn apc_recall_detail(
    trajs: Vec<f32>,
    n: usize,
    t: usize,
    dim: usize,
    words: Vec<i64>,
    spk: Vec<i64>,
    cap_q: usize,
    n_pos: usize,
    n_neg: usize,
    seed: u64,
) -> Vec<f32> {
    crate::apc::nn_recall_detail(&trajs, n, t, dim, &words, &spk, cap_q, n_pos, n_neg, seed)
}

/// Batched multi-speaker order-1 PURITY at ~`target` clusters via greedy
/// leader clustering over the DtwTo kernel (`apc::cluster_purity`). Returns
/// [purity, n_clusters]. A fast measurement helper for gate (c).
#[pyfunction]
fn apc_purity(
    trajs: Vec<f32>,
    n: usize,
    t: usize,
    dim: usize,
    words: Vec<i64>,
    target: usize,
    seed: u64,
) -> Vec<f32> {
    crate::apc::cluster_purity(&trajs, n, t, dim, &words, target, seed)
}

/// DISCOVER the nuisance (speaker/accent) subspace from same-text
/// cross-speaker residuals (see `apc::nuisance_subspace`). `resid` = n rows
/// × dim (content-cancelled same-word-cross-speaker per-frame differences);
/// returns the top-k principal directions (k*dim) to QUOTIENT out.
#[pyfunction]
fn apc_nuisance_subspace(
    resid: Vec<f32>,
    n: usize,
    dim: usize,
    k: usize,
    iters: usize,
) -> Vec<f32> {
    crate::apc::nuisance_subspace(&resid, n, dim, k, iters)
}

/// DIMENSIONAL LIFT for cross-speaker invariance (see `apc::logfreq_lift`).
/// Lifts each log-frequency cochleagram frame into Fourier modes along the
/// bands, where the VTL/speaker warp is a per-mode ROTATION, and returns
/// the rotation-INVARIANT magnitudes `[|C_1|..|C_M|]` — cheap, exact
/// VTL-shift invariance that keeps spectral shape (discrimination).
/// `coch_flat` = (n_frames x n_bands) row-major; returns (n_frames x n_modes).
#[pyfunction]
fn apc_lift(coch_flat: Vec<f32>, n_frames: usize, n_bands: usize, n_modes: usize) -> Vec<f32> {
    crate::apc::logfreq_lift(&coch_flat, n_frames, n_bands, n_modes)
}

/// COCHLEAGRAM-BAND RENDER (see `apc::formant_bands`): project a phoneme's
/// (F1,F2,F3) formants into the 32-band cochleagram magnitude space so a
/// TEXT-recovered accent shift-vector can be applied to / quotiented from
/// REAL cochleagram audio. Returns 32 band magnitudes.
#[pyfunction]
fn apc_formant_bands(f1: f32, f2: f32, f3: f32, sigma: f32) -> Vec<f32> {
    crate::apc::formant_bands(f1, f2, f3, sigma)
}

/// The agent's CMVN (per-band cepstral mean-variance normalisation) in Rust — the
/// batched form of the composed cmvn_band_term. `m` is the (n_frames x n_bands) matrix
/// flattened row-major (frame, band); `voiced` is a per-frame 0/1 stat-frame mask.
/// Returns the normalised matrix, same flat layout. Speaker-invariant phonetic trajectory.
#[pyfunction]
fn cmvn(
    m: Vec<f32>,
    n_frames: usize,
    n_bands: usize,
    eps: f32,
    do_variance: bool,
    voiced: Vec<u8>,
) -> Vec<f32> {
    crate::audio_primitives::cmvn(&m, n_frames, n_bands, eps, do_variance, &voiced)
}

/// The recogniser's decision in Rust: score an embedding against the centroid matrix
/// (row-major n_cent x dim) by dot product and return (top-k indices, top-k scores).
/// The batched form of the held Dot Term + argmax loop over WordCentroid nodes.
#[pyfunction]
fn topk_dot(
    emb: Vec<f32>,
    cents: Vec<f32>,
    n_cent: usize,
    dim: usize,
    k: usize,
) -> (Vec<i64>, Vec<f32>) {
    crate::audio_primitives::topk_dot(&emb, &cents, n_cent, dim, k)
}

/// Duration-aware recognition (the agent's composed match Term, compiled): score =
/// Dot(emb, cent) - 0.5*((qdur - dmu)/dsig)^2 per centroid, top-k. dmu/dsig are per-unit
/// duration mean/std (frames) from data. Returns (top-k indices, scores).
#[pyfunction]
fn topk_match(
    emb: Vec<f32>,
    cents: Vec<f32>,
    dmu: Vec<f32>,
    dsig: Vec<f32>,
    n_cent: usize,
    dim: usize,
    k: usize,
    qdur: f32,
) -> (Vec<i64>, Vec<f32>) {
    crate::audio_primitives::topk_match(&emb, &cents, &dmu, &dsig, n_cent, dim, k, qdur)
}

/// The agent's TP-trough word segmenter in Rust — the batched form of
/// forward_segmentation. `seqs` are the unit (per-frame codebook id) sequences;
/// returns, per sequence, the chunk LENGTHS in units. mode: 0=median, 1=local_min,
/// 2=prominent (local_min AND below median — the grid-robust word-scale rule).
#[pyfunction]
fn segment_units(seqs: Vec<Vec<i64>>, bidirectional: bool, mode: u8) -> Vec<Vec<usize>> {
    crate::audio_primitives::segment_units(&seqs, bidirectional, mode)
}

/// The agent's FFT ear (nwin Hanning windows x nbands log bands 150..3800 Hz) in Rust.
#[pyfunction]
fn fft_ear(x: Vec<f64>, fs: u32, nbands: usize, nwin: usize, nfft: usize) -> Vec<f64> {
    crate::audio_primitives::fft_ear(&x, fs, nbands, nwin, nfft)
}

/// The agent's all-pole (LPC) ear (nwin windows x nbands log bands 150..3800 Hz) in Rust.
#[pyfunction]
fn allpole_ear(x: Vec<f64>, fs: u32, nbands: usize, nwin: usize, order: usize) -> Vec<f64> {
    crate::audio_primitives::allpole_ear(&x, fs, nbands, nwin, order)
}

/// The agent's sonority-valley word segmenter in Rust -> inter-word cut sample indices. The
/// depth_threshold is the graph-resident, self-tuned decision; this is its mechanical DSP.
#[pyfunction]
fn sonority_segment(
    x: Vec<f64>,
    fs: u32,
    smoothing_ms: f64,
    min_sep_ms: f64,
    depth_threshold: f64,
    silence_floor: f64,
    snap_center: f64,
) -> Vec<usize> {
    crate::audio_primitives::sonority_segment(
        &x,
        fs,
        smoothing_ms,
        min_sep_ms,
        depth_threshold,
        silence_floor,
        snap_center,
    )
}

/// Short-time Fourier transform MAGNITUDE — Hann-windowed, hop-strided,
/// `window_size/2` magnitude bins per frame, returned FLAT
/// (`n_frames * window_size/2`, row-major: frame-major). A front-end reshapes
/// to (n_frames, half) for spectral flux / onset density. Thin hand-off to the
/// held `audio_primitives::stft`; the RHYTHM channel of the pitch+rhythm
/// perception front-end reads onset density off this.
#[pyfunction]
fn stft(samples: Vec<f32>, window_size: usize, hop_size: usize) -> Vec<f32> {
    crate::audio_primitives::stft(&samples, window_size, hop_size)
}

/// Inner-hair-cell envelope (HWR + one-pole LPF) of a band — the
/// magnitude code that DISCARDS the sub-millisecond fine timing. Exposed
/// alongside the TFS so the "envelope-cannot / TFS-can" diagnostic can
/// contrast the two reads of the SAME band.
#[pyfunction]
fn hair_cell_envelope(band: Vec<f32>, cutoff_hz: f32, fs: u32) -> Vec<f32> {
    crate::audio_primitives::hair_cell_envelope(&band, cutoff_hz, fs)
}

/// Per-band running short-time autocorrelation of a gammatone band's
/// FINE WAVEFORM. Returns a flat `n_frames × (max_lag+1)` row-major
/// list (the within-band inter-spike-interval / phase-lock readout).
#[pyfunction]
fn band_autocorr(band: Vec<f32>, win: usize, hop: usize, max_lag: usize) -> Vec<f32> {
    crate::audio_primitives::band_autocorr(&band, win, hop, max_lag)
}

/// Summary autocorrelogram: pool per-band running autocorrelations
/// (each from `band_autocorr` with the SAME win/hop/max_lag) across
/// bands into one peak-normalised lag profile per frame. `n_lags =
/// max_lag + 1`.
#[pyfunction]
fn summary_autocorrelogram(band_acs: Vec<Vec<f32>>, n_lags: usize) -> Vec<f32> {
    let refs: Vec<&[f32]> = band_acs.iter().map(|v| v.as_slice()).collect();
    crate::audio_primitives::summary_autocorrelogram(&refs, n_lags)
}

/// Periodicity track from a summary autocorrelogram: per frame, the
/// `(periodicity_strength, period_lag)` of the strongest pooled peak
/// in `[min_lag, max_lag]`. Returns a flat list `[s0, l0, s1, l1, ...]`
/// (strength as float, lag cast to float) so it crosses the boundary
/// as a plain numeric list.
#[pyfunction]
fn periodicity_track(sacf: Vec<f32>, n_lags: usize, min_lag: usize, max_lag: usize) -> Vec<f32> {
    let pairs = crate::audio_primitives::periodicity_track(&sacf, n_lags, min_lag, max_lag);
    let mut out = Vec::with_capacity(pairs.len() * 2);
    for (s, l) in pairs {
        out.push(s);
        out.push(l as f32);
    }
    out
}

/// Autocorrelation r[0..=p] of a windowed frame. Native back-end for the
/// LPC formant chain (was `lpc_formant_representation._autocorr`).
#[pyfunction]
fn lpc_autocorr(x: Vec<f32>, p: usize) -> Vec<f64> {
    crate::audio_primitives::lpc_autocorr(&x, p)
}

/// Levinson-Durbin recursion: autocorrelation r[0..=p] -> all-pole
/// coefficients a[0..=p] (a[0]=1) of A(z) = 1 - sum_k a_k z^-k. Native
/// back-end for the LPC formant chain (was `_levinson`).
#[pyfunction]
fn levinson_durbin(r: Vec<f64>, p: usize) -> Vec<f64> {
    let (a, _gain) = crate::audio_primitives::levinson_durbin(&r, p);
    a
}

/// One raw-waveform frame -> ascending formant frequencies (Hz) from the
/// LPC pole angles. The agent's own self-specified `lpc_all_pole_formants`
/// front-end op, OWNED natively (Stage-0 / W1 / Gap 2). Thin one-line
/// hand-off; all the DSP is in `audio_primitives.rs`.
#[pyfunction]
#[pyo3(signature = (frame, fs, order, pre_emph=0.97, f_lo=150.0, f_hi=3600.0, bw_max=500.0))]
fn lpc_roots_formants(
    frame: Vec<f32>,
    fs: u32,
    order: usize,
    pre_emph: f32,
    f_lo: f32,
    f_hi: f32,
    bw_max: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_roots_formants(&frame, fs, order, pre_emph, f_lo, f_hi, bw_max)
}

/// LPC RESIDUAL of one frame — inverse-filter through the frame's own all-pole
/// A(z), leaving an estimate of the GLOTTAL SOURCE (the speaker's voice-identity
/// excitation). The KEY impressionist inversion primitive: the residual of a
/// real speaker's sample IS that speaker's source estimate. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (frame, order, pre_emph=0.97))]
fn lpc_residual(frame: Vec<f32>, order: usize, pre_emph: f32) -> Vec<f32> {
    crate::audio_primitives::lpc_residual(&frame, order, pre_emph)
}

/// Formant freqs AND bandwidths from one frame (the LPC pole freq/radius). Like
/// `lpc_roots_formants` but KEEPS the bandwidth (half the speaker's filter code).
/// Returns flat [f0,bw0, f1,bw1, ...] ascending by freq. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (frame, fs, order, pre_emph=0.97, f_lo=150.0, f_hi=3600.0, bw_max=500.0))]
fn lpc_formants_bw(
    frame: Vec<f32>,
    fs: u32,
    order: usize,
    pre_emph: f32,
    f_lo: f32,
    f_hi: f32,
    bw_max: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_formants_bw(&frame, fs, order, pre_emph, f_lo, f_hi, bw_max)
}

/// F0 (Hz) of a frame by autocorrelation peak-picking — the speaker's pitch
/// (glottal clock rate). 0.0 if unvoiced. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (frame, fs, f_lo=70.0, f_hi=400.0, voicing_thresh=0.3))]
fn f0_autocorr(frame: Vec<f32>, fs: u32, f_lo: f32, f_hi: f32, voicing_thresh: f32) -> f32 {
    crate::audio_primitives::f0_autocorr(&frame, fs, f_lo, f_hi, voicing_thresh)
}

/// GLOTTAL SOURCE shape from an LPC residual — [oq, ta_frac, tilt_db_per_oct]:
/// the speaker's open-quotient, return-phase/spectral-tilt proxy, and source
/// tilt, read pitch-synchronously from the residual the inverse way (the params
/// the forward LF source model is parametrised by). Thin hand-off.
#[pyfunction]
#[pyo3(signature = (residual, fs, f0_hz))]
fn glottal_params_from_residual(residual: Vec<f32>, fs: u32, f0_hz: f32) -> Vec<f32> {
    crate::audio_primitives::glottal_params_from_residual(&residual, fs, f0_hz)
}

/// GENUINE GLOTTAL INVERSE (IAIF + closed-phase covariance LPC + GCI) — recover
/// [oq, ta_frac, tilt_db] from a voiced frame off the recovered glottal FLOW (not
/// the over-whitened full-frame residual). Does NOT saturate at the 0.30 oq floor.
/// Thin hand-off. Operates on the RAW (radiated) speech frame, not the residual.
#[pyfunction]
#[pyo3(signature = (frame, fs, f0_hz))]
fn glottal_inverse_iaif(frame: Vec<f32>, fs: u32, f0_hz: f32) -> Vec<f32> {
    crate::audio_primitives::glottal_inverse_iaif(&frame, fs, f0_hz)
}

/// SPREAD-PRESERVING f0 — octave-robust cepstral pitch with an autocorr octave-
/// error reject. Returns f0 Hz (0 = unvoiced). Thin hand-off.
#[pyfunction]
#[pyo3(signature = (frame, fs, f_lo, f_hi, voicing_thresh))]
fn f0_cepstral(frame: Vec<f32>, fs: u32, f_lo: f32, f_hi: f32, voicing_thresh: f32) -> f32 {
    crate::audio_primitives::f0_cepstral(&frame, fs, f_lo, f_hi, voicing_thresh)
}

/// CEPSTRAL-ENVELOPE FORMANTS — excitation-robust formants by homomorphic
/// deconvolution: lifter the cepstrum to the low-quefrency spectral ENVELOPE (the
/// FILTER, with the SOURCE comb/noise removed), peak-pick formants off THAT.
/// Returns flat [f1,bw1, f2,bw2, ...] ascending, same layout as lpc_formants_bw.
/// Thin hand-off.
#[pyfunction]
#[pyo3(signature = (frame, fs, f_lo=150.0, f_hi=3800.0, n_formants=3, lifter=24))]
fn cepstral_formants(
    frame: Vec<f32>,
    fs: u32,
    f_lo: f32,
    f_hi: f32,
    n_formants: usize,
    lifter: usize,
) -> Vec<f32> {
    crate::audio_primitives::cepstral_formants(&frame, fs, f_lo, f_hi, n_formants, lifter)
}

/// HIGH-RESOLUTION f0 — YIN (cumulative-mean-normalised difference function +
/// absolute threshold + PARABOLIC INTERPOLATION). Sub-Hz period accuracy that
/// resolves closely-spaced same-register (e.g. male) voices the integer-lag
/// autocorr / broad cepstral peak collapse onto a common value. Returns f0 Hz
/// (0 = unvoiced). Thin hand-off.
#[pyfunction]
#[pyo3(signature = (frame, fs, f_lo=70.0, f_hi=400.0, voicing_thresh=0.1))]
fn f0_yin(frame: Vec<f32>, fs: u32, f_lo: f32, f_hi: f32, voicing_thresh: f32) -> f32 {
    crate::audio_primitives::f0_yin(&frame, fs, f_lo, f_hi, voicing_thresh)
}

/// WITHIN-REGISTER TRACT-SHAPE WARP — imprint a speaker's OWN per-formant tract
/// signature (formant-space offsets `freq_ratio` + per-formant bandwidths
/// `targ_bw`) onto a content LPC coefficient track, so two same-VTL / same-register
/// speakers render with their OWN distinct vocal-tract geometry. Roots each frame's
/// A(z), multiplies each of the first `n_formant` in-band formant-pole angles by
/// `freq_ratio[k]`, blends each pole radius toward the speaker's `targ_bw[k]` by
/// `alpha`, and multiplies the polynomial back out. Pure owned DSP. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (a_frames, order, fs, freq_ratio, targ_bw, n_formant=3, alpha=0.5, f_lo=200.0, f_hi=3800.0))]
#[allow(clippy::too_many_arguments)]
fn lpc_formant_warp_track(
    a_frames: Vec<f32>,
    order: usize,
    fs: u32,
    freq_ratio: Vec<f32>,
    targ_bw: Vec<f32>,
    n_formant: usize,
    alpha: f32,
    f_lo: f32,
    f_hi: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_formant_warp_track(
        &a_frames,
        order,
        fs,
        &freq_ratio,
        &targ_bw,
        n_formant,
        alpha,
        f_lo,
        f_hi,
    )
}

/// ABSOLUTE-TARGET formant warp for the analysis-by-synthesis formant-fix loop:
/// sets each of the first `n_formant` in-band formant poles to an ABSOLUTE target
/// frequency `targ_f[k]` (Hz, `<=0` leaves it), blends bandwidth toward
/// `targ_bw[k]` by `alpha`. Thin hand-off. The caller drives `targ_f` to the
/// values that make the rendered formants re-analyse to the speaker's REAL
/// formants (a deterministic inverse on the forward model). Pure owned DSP.
#[pyfunction]
#[pyo3(signature = (a_frames, order, fs, targ_f, targ_bw, n_formant=3, alpha=0.5, f_lo=200.0, f_hi=3800.0))]
#[allow(clippy::too_many_arguments)]
fn lpc_formant_set_track(
    a_frames: Vec<f32>,
    order: usize,
    fs: u32,
    targ_f: Vec<f32>,
    targ_bw: Vec<f32>,
    n_formant: usize,
    alpha: f32,
    f_lo: f32,
    f_hi: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_formant_set_track(
        &a_frames, order, fs, &targ_f, &targ_bw, n_formant, alpha, f_lo, f_hi,
    )
}

/// COPY-RESYNTHESIS — analyse the signal frame-by-frame, KEEP the true LPC
/// residual as the excitation, drive the recovered all-pole tract filter with
/// it, carrying filter state + de-emphasis across frames. The output is the
/// real signal regenerated by the real physics (near-transparent). Thin hand-off.
#[pyfunction]
#[pyo3(signature = (signal, fs, order=14, frame_len=200, pre_emph=0.97))]
fn lpc_copy_resynth(
    signal: Vec<f32>,
    fs: u32,
    order: usize,
    frame_len: usize,
    pre_emph: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_copy_resynth(&signal, fs, order, frame_len, pre_emph)
}

/// Per-frame LPC coefficient track (the SPEAKER's vocal-tract filter trajectory):
/// flat concat of per-frame `a` vectors (length order+1 each, a[0]=1), one per
/// hop. The filter half of the impression. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (signal, order=14, frame_len=200, hop=100, pre_emph=0.97))]
fn lpc_coeff_track(
    signal: Vec<f32>,
    order: usize,
    frame_len: usize,
    hop: usize,
    pre_emph: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_coeff_track(&signal, order, frame_len, hop, pre_emph)
}

/// Whole-signal LPC residual track (the TRUE recovered source over the whole
/// utterance) at the same hop/frame as lpc_coeff_track. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (signal, order=14, frame_len=200, hop=100, pre_emph=0.97))]
fn lpc_residual_track(
    signal: Vec<f32>,
    order: usize,
    frame_len: usize,
    hop: usize,
    pre_emph: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_residual_track(&signal, order, frame_len, hop, pre_emph)
}

/// CROSS-RESYNTHESIS (the impression render): drive a per-frame SPEAKER filter
/// track (`a_frames`, flat concat of length order+1 each) with an excitation
/// (`exc`) at `hop` samples/frame, state + de-emphasis carried across frames.
/// Hold the speaker, swap the content. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (a_frames, exc, order, hop, pre_emph=0.97))]
fn lpc_cross_resynth(
    a_frames: Vec<f32>,
    exc: Vec<f32>,
    order: usize,
    hop: usize,
    pre_emph: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_cross_resynth(&a_frames, &exc, order, hop, pre_emph)
}

/// SOURCE-CHARACTER TRANSPLANT (the held-voice factoring): pitch-synchronously
/// re-lay the CONTENT residual's source grains at speaker S's target f0, and
/// warp the source spectral tilt toward S's recovered colour. Holds the WORD
/// (the content's grain shape + per-hop timing) while transplanting S's source
/// CHARACTER (f0 + open-quotient grain width + tilt). Thin hand-off.
#[pyfunction]
#[pyo3(signature = (exc, f0_track, hop, fs, tgt_f0, tgt_oq, tgt_tilt_db, src_tilt_db))]
#[allow(clippy::too_many_arguments)]
fn glottal_warp_residual(
    exc: Vec<f32>,
    f0_track: Vec<f32>,
    hop: usize,
    fs: u32,
    tgt_f0: f32,
    tgt_oq: f32,
    tgt_tilt_db: f32,
    src_tilt_db: f32,
) -> Vec<f32> {
    crate::audio_primitives::glottal_warp_residual(
        &exc,
        &f0_track,
        hop,
        fs,
        tgt_f0,
        tgt_oq,
        tgt_tilt_db,
        src_tilt_db,
    )
}

/// SOURCE-IMPRINTED EXCITATION TRANSPLANT (the 48 kHz held-voice fix): instead of
/// re-laying the CONTENT donor's own residual grains (which keeps the donor's
/// pulse SHAPE so S's open-quotient/spectral-tilt never enter the excitation and
/// the all-pole filter launders them), SYNTHESIZE a fresh LF glottal-flow-
/// derivative pulse at S's recovered oq + ta_frac (return-phase = tilt) + f0, ONE
/// pulse per S-period (pitch-synchronous → no grain reuse → no high-voice ringing),
/// modulated by the content per-hop residual ENERGY ENVELOPE (the word's loudness
/// contour + voiced/unvoiced structure). Unvoiced hops copy the content residual
/// through (frication is sourceless). The source character now lives IN the
/// excitation, surviving lpc_cross_resynth. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (content_res, content_f0_track, hop, fs, tgt_f0, tgt_oq, tgt_ta_frac, am=0.7))]
#[allow(clippy::too_many_arguments)]
fn lf_excitation_transplant(
    content_res: Vec<f32>,
    content_f0_track: Vec<f32>,
    hop: usize,
    fs: u32,
    tgt_f0: f32,
    tgt_oq: f32,
    tgt_ta_frac: f32,
    am: f32,
) -> Vec<f32> {
    crate::audio_primitives::lf_excitation_transplant(
        &content_res,
        &content_f0_track,
        hop,
        fs,
        tgt_f0,
        tgt_oq,
        tgt_ta_frac,
        am,
    )
}

/// BANDWIDTH-FLOOR an LPC coefficient track (the high-voice anti-ring): scale the
/// k-th coeff of every frame by γ^k (γ = exp(-π·bw_floor_hz/fs)), pulling all poles
/// radially inward → widening each formant's bandwidth by ~bw_floor_hz while
/// leaving the formant FREQUENCY fixed, so sharp poles cannot ring between sparse
/// high-f0 pulses. bw_floor_hz=0 is identity. Thin hand-off.
#[pyfunction]
#[pyo3(signature = (a_frames, order, fs, bw_floor_hz))]
fn lpc_bw_expand_track(a_frames: Vec<f32>, order: usize, fs: u32, bw_floor_hz: f32) -> Vec<f32> {
    crate::audio_primitives::lpc_bw_expand_track(&a_frames, order, fs, bw_floor_hz)
}

/// BUGGY (historical) lpc_roots_formants — the PRE-FIX reversed-coeff /
/// sign-wrong-bandwidth-gate behaviour, surfaced ONLY for the bandwidth-bug A/B
/// measurement (how much the broken forward model throttled perception). Thin
/// hand-off. NOT for production.
#[pyfunction]
#[pyo3(signature = (frame, fs, order, pre_emph=0.97, f_lo=150.0, f_hi=3600.0, bw_max=500.0))]
fn lpc_roots_formants_buggy(
    frame: Vec<f32>,
    fs: u32,
    order: usize,
    pre_emph: f32,
    f_lo: f32,
    f_hi: f32,
    bw_max: f32,
) -> Vec<f32> {
    crate::audio_primitives::lpc_roots_formants_buggy(
        &frame, fs, order, pre_emph, f_lo, f_hi, bw_max,
    )
}

/// Sonority-valley segmentation of a total-envelope track — the native
/// `detect_sonority_valleys` (audio_primitives.rs), surfaced for the
/// Stage-2 sonority SKELETON. Picks smoothed local minima whose relative
/// drop from the lower flanking peak exceeds `depth_threshold`; the
/// valleys are the consonant-boundary landmarks, the spans between them
/// the sonorant nuclei. Returns a flat list
/// `[sample0, depth0, valley0, peak0, sample1, ...]` (sample cast to
/// float) so the segmentation crosses the boundary as a plain numeric
/// list — the agent reads the SKELETON (count + pattern of valleys),
/// not a Python object.
#[pyfunction]
#[pyo3(signature = (total_env, fs, smoothing_ms=40.0, min_separation_ms=100.0, depth_threshold=0.3))]
fn detect_sonority_valleys(
    total_env: Vec<f32>,
    fs: u32,
    smoothing_ms: f32,
    min_separation_ms: f32,
    depth_threshold: f32,
) -> Vec<f32> {
    let valleys = crate::audio_primitives::detect_sonority_valleys(
        &total_env,
        fs,
        smoothing_ms,
        min_separation_ms,
        depth_threshold,
    );
    let mut out = Vec::with_capacity(valleys.len() * 4);
    for v in valleys {
        out.push(v.sample as f32);
        out.push(v.depth);
        out.push(v.valley);
        out.push(v.peak);
    }
    out
}

// =======================================================================
// EffortDial — PyO3 bundle of the context-aware effort dial. ALL the
// decision logic (which channels fire, how they blend, how many passes
// to run) lives in Rust (`effort_dial.rs` + L6 loop); the Python side is
// a pure world adapter: it pushes context (deadline, mode, cpu, memory,
// surprise) in and reads the trace (effort, passes, wall-time, met) out.
// =======================================================================

use crate::effort_dial::{
    blend_effort, CpuSlackEffortChannel, DeadlineEffortChannel, EffortContext, EffortKnob,
    EffortPipeline, MemoryPressureEffortChannel, SurpriseEffortChannel, ThreadMode,
    ThreadModeEffortChannel, EFFORT_ADJUSTMENT, EFFORT_TARGET,
};
use crate::l6_cybernetic_feedback::{CyberneticFeedbackLoop, RecommendationApplier};
use crate::l6_essential_variables::{EssentialVariable, WorkingSetFit};
use crate::memory::order_n_shape_salience;
use std::sync::atomic::AtomicU64 as StdAtomicU64;
use std::sync::Mutex as StdMutex;
use std::time::{Duration, Instant};

#[pyclass(name = "EffortDial", module = "substrate_rs._native")]
pub struct PyEffortDial {
    knob: EffortKnob,
    ctx: Arc<StdMutex<EffortContext>>,
    floop: CyberneticFeedbackLoop,
    applier: RecommendationApplier,
    pipeline: EffortPipeline,
    cpu_load: Arc<StdAtomicU64>,
    wsf: Arc<WorkingSetFit>,
}

#[pymethods]
impl PyEffortDial {
    /// Build the dial: knob (effort 0..=`max_effort`, `min_passes`..
    /// `max_passes`, salience thresholds `hi`..`lo`), all five context
    /// channels wired into the L6 feedback loop, the effort knob
    /// registered with a real `RecommendationApplier`, and the
    /// measurable pipeline. `l3_cache_bytes` sizes the memory bound.
    #[new]
    #[pyo3(signature = (
        max_effort=10, min_passes=1, max_passes=8,
        hi_threshold=0.30, lo_threshold=0.02,
        realtime_ceiling=4, l3_cache_bytes=33_554_432,
        mem_high=0.9, budget_fraction=0.8,
        salient_at=0.5, routine_floor=1, mem_near_ceiling=3))]
    fn new(
        max_effort: u64,
        min_passes: u64,
        max_passes: u64,
        hi_threshold: f64,
        lo_threshold: f64,
        realtime_ceiling: u64,
        l3_cache_bytes: usize,
        mem_high: f64,
        budget_fraction: f64,
        salient_at: f64,
        routine_floor: u64,
        mem_near_ceiling: u64,
    ) -> Self {
        let knob = EffortKnob::new(
            0,
            max_effort,
            min_passes,
            max_passes,
            hi_threshold,
            lo_threshold,
        );
        let ctx = Arc::new(StdMutex::new(EffortContext {
            thread_mode: ThreadMode::OfflineParallel,
            deadline: None,
            per_pass_cost: Duration::from_micros(100),
            surprise: 0.0,
            now: Instant::now(),
        }));
        let wsf: Arc<WorkingSetFit> = Arc::new(WorkingSetFit::new(
            "working_set_fit",
            l3_cache_bytes,
            mem_high,
        ));

        let mut floop = CyberneticFeedbackLoop::new();
        // Surprise FIRST (a demand); constraint channels after.
        floop.add(Box::new(SurpriseEffortChannel::new(
            "surprise",
            Arc::clone(&ctx),
            knob.clone(),
            salient_at,
            routine_floor,
        )));
        floop.add(Box::new(ThreadModeEffortChannel::new(
            "thread_mode",
            Arc::clone(&ctx),
            knob.clone(),
            realtime_ceiling,
        )));
        floop.add(Box::new(DeadlineEffortChannel::new(
            "deadline",
            Arc::clone(&ctx),
            knob.clone(),
            budget_fraction,
        )));
        let (cpu_ch, cpu_load) = CpuSlackEffortChannel::new("cpu_slack", knob.clone());
        floop.add(Box::new(cpu_ch));
        floop.add(Box::new(MemoryPressureEffortChannel::new(
            "memory",
            knob.clone(),
            Arc::clone(&wsf) as Arc<dyn EssentialVariable>,
            mem_near_ceiling,
        )));

        let mut applier = RecommendationApplier::new();
        applier.register_knob_u64(EFFORT_ADJUSTMENT, EFFORT_TARGET, knob.handle());

        let pipeline = EffortPipeline::new(knob.clone());

        Self {
            knob,
            ctx,
            floop,
            applier,
            pipeline,
            cpu_load,
            wsf,
        }
    }

    /// Set the execution context. `mode` is "realtime" (single-thread,
    /// latency-bound) or "offline" (parallel/batch, no deadline).
    /// `deadline_us` is the per-item budget in microseconds from NOW
    /// (None / 0 ⇒ no deadline). `per_pass_us` is the measured cost of
    /// one analysis pass (the deadline channel uses it to fit passes).
    /// `surprise` is the input's salience. `cpu_load` in [0,1].
    /// `working_set_bytes` feeds the memory bound.
    #[pyo3(signature = (mode, deadline_us=None, per_pass_us=100,
                        surprise=0.0, cpu_load=0.0, working_set_bytes=0))]
    fn set_context(
        &self,
        mode: &str,
        deadline_us: Option<u64>,
        per_pass_us: u64,
        surprise: f64,
        cpu_load: f64,
        working_set_bytes: usize,
    ) -> PyResult<()> {
        let tm = match mode {
            "realtime" | "realtime_single" => ThreadMode::RealtimeSingle,
            "offline" | "offline_parallel" => ThreadMode::OfflineParallel,
            other => {
                return Err(PyValueError::new_err(format!(
                    "mode must be 'realtime' or 'offline', got {:?}",
                    other
                )))
            }
        };
        let now = Instant::now();
        let deadline = match deadline_us {
            Some(us) if us > 0 => Some(now + Duration::from_micros(us)),
            _ => None,
        };
        {
            let mut c = self.ctx.lock().unwrap();
            c.thread_mode = tm;
            c.deadline = deadline;
            c.per_pass_cost = Duration::from_micros(per_pass_us.max(1));
            c.surprise = surprise;
            c.now = now;
        }
        let lm = (cpu_load.clamp(0.0, 1.0) * 1000.0).round() as u64;
        self.cpu_load
            .store(lm, std::sync::atomic::Ordering::Release);
        self.wsf.update(working_set_bytes);
        Ok(())
    }

    /// Tick the L6 feedback loop: read every context channel, blend
    /// (min of all budget ceilings AND the surprise demand), and turn
    /// the registered effort knob. Returns the chosen effort level.
    fn turn_dial(&self) -> u64 {
        let recs = self.floop.tick();
        let blended = blend_effort(&self.knob, &recs);
        self.knob.set(blended);
        blended
    }

    /// Per-channel recommendations this tick: list of (name, effort)
    /// — the trace of WHICH context input asked for WHAT.
    fn channel_votes(&self) -> Vec<(String, u64)> {
        self.floop
            .tick()
            .iter()
            .map(|r| {
                (
                    r.source_variable.clone(),
                    r.adjustment_scalar.round() as u64,
                )
            })
            .collect()
    }

    /// Current effort level.
    fn effort(&self) -> u64 {
        self.knob.level()
    }
    /// Passes the dial will run at current effort.
    fn passes(&self) -> u64 {
        self.knob.passes()
    }
    /// Salience threshold at current effort (lower ⇒ keep more).
    fn salience_threshold(&self) -> f64 {
        self.knob.salience_threshold()
    }
    fn max_effort(&self) -> u64 {
        self.knob.max_effort()
    }

    /// Salience of an input trajectory (the surprise signal) — the
    /// same `order_n_shape_salience` operator memory + perception use.
    #[staticmethod]
    fn surprise_of(traj: Vec<f64>) -> f64 {
        order_n_shape_salience(&traj)
    }

    /// Run the measurable pipeline over `input` at the CURRENT effort.
    /// Returns a dict: effort, passes, salience_threshold, processed,
    /// estimate, wall_us, deadline_met. `surprise` gates processing;
    /// `deadline_us` (if set) is checked against actual wall-time.
    #[pyo3(signature = (input, surprise=0.0, deadline_us=None))]
    fn run<'py>(
        &self,
        py: Python<'py>,
        input: Vec<f64>,
        surprise: f64,
        deadline_us: Option<u64>,
    ) -> PyResult<Bound<'py, PyDict>> {
        let deadline = match deadline_us {
            Some(us) if us > 0 => Some(Instant::now() + Duration::from_micros(us)),
            _ => None,
        };
        let res = self.pipeline.run(&input, surprise, deadline);
        let d = PyDict::new_bound(py);
        d.set_item("effort", res.effort)?;
        d.set_item("passes", res.passes)?;
        d.set_item("salience_threshold", res.salience_threshold)?;
        d.set_item("processed", res.processed)?;
        d.set_item("estimate", res.estimate)?;
        d.set_item("wall_us", res.wall.as_secs_f64() * 1e6)?;
        d.set_item("deadline_met", res.deadline_met)?;
        Ok(d)
    }
}

#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

// --- selector audit (ENGINE_WINNER_VALUE_PREREG.md) ------------------------
//
// Thin one-line handoffs to `crate::selector_audit`. No logic here: the
// instrument lives in the evaluator, so coverage is structural rather than
// wired-up-per-call-site.

/// Set the selector audit mode: "off" (default), "warn", or "strict".
/// "warn" counts contradictions; "strict" panics on the first one.
#[pyfunction]
fn selector_audit_enable(mode: &str) -> PyResult<()> {
    let m = match mode.trim().to_ascii_lowercase().as_str() {
        "off" => crate::selector_audit::MODE_OFF,
        "warn" | "on" => crate::selector_audit::MODE_WARN,
        "strict" => crate::selector_audit::MODE_STRICT,
        other => {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "selector_audit_enable: unknown mode {other:?} \
                 (expected 'off', 'warn' or 'strict')"
            )))
        }
    };
    crate::selector_audit::set_mode(m);
    Ok(())
}

/// THE POSITIVE CONTROL. When on, selector folds return the FIRST candidate
/// regardless of value — the §4.2 anomaly's exact signature. Only reachable
/// while the audit is enabled; a detector that has never fired is untested.
#[pyfunction]
fn selector_audit_fault_inject(on: bool) {
    crate::selector_audit::set_fault_inject_first(on);
}

#[pyfunction]
fn selector_audit_reset() {
    crate::selector_audit::reset();
}

/// `{firings, candidates, skipped_effectful, disagreements, empty,
///   first_row, mode, fault_inject}`.
///
/// `firings / candidates` is the EXACT counted cost of the instrument on the
/// selector path — one extra value evaluation per firing, i.e. 1/N for a
/// selector over N candidates. Counted, not wall-clock: deterministic and
/// load-independent.
/// `{failed_edge_inserts, false_progress, first_row, correction_enabled}`.
///
/// `failed_edge_inserts` counts `AddEdge` effects whose `insert_edge` returned
/// `Err` and was discarded by the applier. `false_progress` is the subset that
/// ALSO credited `progressed` and pushed an undo step for a mutation that never
/// happened — the count that matters for fixpoint behaviour, since a rule that
/// always fails this way always claims progress.
#[pyfunction]
fn effect_audit_stats(py: Python<'_>) -> PyResult<PyObject> {
    let (failed, false_progress, first_row) = crate::effect_audit::stats();
    let d = PyDict::new_bound(py);
    d.set_item("failed_edge_inserts", failed)?;
    d.set_item("false_progress", false_progress)?;
    d.set_item("first_row", first_row)?;
    d.set_item(
        "correction_enabled",
        crate::effect_audit::correct_failed_effects(),
    )?;
    Ok(d.into())
}

/// Probe-exactness instrument: does the cold path's apply-then-undo restore the
/// graph exactly? Returns `(probes_checked, probes_dirty, dirty_rule_names)`.
/// The rule list is an ENUMERATION — Stage A's NO-GO condition is a semantic
/// delta that cannot be listed rule-by-rule.
#[pyfunction]
fn probe_exactness_stats(py: Python<'_>) -> PyResult<PyObject> {
    let (checked, dirty, rules) = crate::effect_audit::probe_stats();
    let d = PyDict::new_bound(py);
    d.set_item("probes_checked", checked)?;
    d.set_item("probes_dirty", dirty)?;
    d.set_item("dirty_rules", rules)?;
    d.set_item("enabled", crate::effect_audit::probe_exactness())?;
    Ok(d.into())
}

/// Arm the probe-exactness check. OFF by default: it hashes the whole graph
/// twice per rolled-back binding.
#[pyfunction]
fn probe_exactness_enable(on: bool) {
    crate::effect_audit::set_probe_exactness(on);
}

#[pyfunction]
fn probe_exactness_reset() {
    crate::effect_audit::probe_reset();
}

/// Rules that commit MORE THAN ONE binding in a single drain, so a later
/// binding evaluated against an earlier one's writes. This is the population
/// Stage A's immutable-base change would affect, and `DECISION_LAYER_PREREG.md`
/// fixes a NO-GO at more than 20 of them — so it is a LIST, not a count.
#[pyfunction]
fn same_round_visibility_stats(py: Python<'_>) -> PyResult<PyObject> {
    let (drains, rules) = crate::effect_audit::multi_binding_stats();
    let d = PyDict::new_bound(py);
    d.set_item("multi_binding_drains", drains)?;
    d.set_item("rules", rules)?;
    d.set_item(
        "rule_count",
        rules_len(&crate::effect_audit::multi_binding_stats().1),
    )?;
    Ok(d.into())
}

fn rules_len(v: &[(String, u64)]) -> usize {
    v.len()
}

#[pyfunction]
fn same_round_visibility_reset() {
    crate::effect_audit::multi_binding_reset();
}

/// Stage A: derive each drain against ONE immutable base and apply the
/// resulting proposals at a single boundary. Default OFF and byte-identical
/// when off — see `stage_a.rs` for why this landed as a mode to measure with
/// rather than as a fix.
#[pyfunction]
fn stage_a_enable(on: bool) {
    crate::stage_a::set_enabled(on);
}

#[pyfunction]
fn stage_a_stats(py: Python<'_>) -> PyResult<PyObject> {
    let (proposals, writes, excluded) = crate::stage_a::stats();
    let d = PyDict::new_bound(py);
    d.set_item("proposals", proposals)?;
    d.set_item("writes", writes)?;
    d.set_item("excluded_drains", excluded)?;
    d.set_item("conflict_fallbacks", crate::stage_a::conflict_fallbacks())?;
    d.set_item("enabled", crate::stage_a::enabled())?;
    Ok(d.into())
}

#[pyfunction]
fn stage_a_reset() {
    crate::stage_a::reset();
}

/// Stage A COMPARE mode: derive each drain both ways and record rules whose
/// write lists differ. Behaviour is unchanged (the committed result is what
/// stays); this measures the prereg's actual NO-GO quantity — rules whose
/// behaviour CHANGES — rather than the at-risk upper bound.
#[pyfunction]
fn stage_a_compare_enable(on: bool) {
    crate::stage_a::set_compare_mode(on);
}

#[pyfunction]
fn stage_a_compare_stats(py: Python<'_>) -> PyResult<PyObject> {
    let (compared, diverged, rules) = crate::stage_a::compare_stats();
    let d = PyDict::new_bound(py);
    d.set_item("compared_drains", compared)?;
    d.set_item("diverged_drains", diverged)?;
    d.set_item("diverged_rules", rules)?;
    let (unsound, unsound_rules) = crate::stage_a::unsound_stats();
    d.set_item("unsound_drains", unsound)?;
    d.set_item("unsound_rules", unsound_rules)?;
    Ok(d.into())
}

/// Worked examples of divergence, `(rule, stage_a_writes, committed_writes)`.
#[pyfunction]
fn stage_a_compare_samples() -> Vec<(String, String, String)> {
    crate::stage_a::compare_samples()
}

#[pyfunction]
fn stage_a_compare_reset() {
    crate::stage_a::compare_reset();
}

/// The engine's own canonical whole-graph hash — the same one opt-in cycle
/// detection compares against history. Exposed so a byte-identity gate can be
/// written against the engine's notion of state rather than a Python
/// re-serialisation of it (which picks up object reprs and dict order).
#[pyfunction]
fn graph_state_fingerprint(sub: &PySubstrate) -> u64 {
    let guard = sub.inner.lock().expect("substrate mutex poisoned");
    guard.graph.state_fingerprint()
}

#[pyfunction]
fn effect_audit_reset() {
    crate::effect_audit::reset();
}

/// Enable the behavioural correction: a failed insert withholds `progressed`
/// and the undo step. Default OFF — committed results are byte-identical with
/// it off (VISION_PROTOCOL §9).
#[pyfunction]
fn effect_audit_set_correction(on: bool) {
    crate::effect_audit::set_correct_failed_effects(on);
}

#[pyfunction]
fn selector_audit_stats(py: Python<'_>) -> PyResult<PyObject> {
    let (firings, candidates, skipped, disagreements, empty, first_row) =
        crate::selector_audit::stats();
    let d = PyDict::new_bound(py);
    d.set_item("firings", firings)?;
    d.set_item("candidates", candidates)?;
    d.set_item("skipped_effectful", skipped)?;
    d.set_item("disagreements", disagreements)?;
    d.set_item("empty", empty)?;
    d.set_item("first_row", first_row)?;
    d.set_item(
        "mode",
        match crate::selector_audit::mode() {
            crate::selector_audit::MODE_WARN => "warn",
            crate::selector_audit::MODE_STRICT => "strict",
            _ => "off",
        },
    )?;
    d.set_item("fault_inject", crate::selector_audit::fault_inject_first())?;
    Ok(d.into())
}

// --- argmin tie audit (VISION_ARGMIN_UNIQUE_PREREG.md) ---------------------
//
// Thin one-line handoffs to `crate::argmin_tie`. No logic here: the instrument
// lives in the selector fold itself, so coverage is structural.

/// Set the tie-audit mode: "off" (default), "count", "refuse_min",
/// "refuse_all". "count" leaves BEHAVIOUR UNCHANGED and only counts;
/// "refuse_min" coerces every `Argmin` to `ArgminUnique`; "refuse_all" does the
/// same for `Argmax`. §9: off is the default and reproduces every committed
/// number byte-identically.
#[pyfunction]
fn argmin_tie_enable(mode: &str) -> PyResult<()> {
    let m = match mode.trim().to_ascii_lowercase().as_str() {
        "off" => crate::argmin_tie::MODE_OFF,
        "count" => crate::argmin_tie::MODE_COUNT,
        "refuse_min" => crate::argmin_tie::MODE_REFUSE_MIN,
        "refuse_all" => crate::argmin_tie::MODE_REFUSE_ALL,
        other => {
            return Err(pyo3::exceptions::PyValueError::new_err(format!(
                "argmin_tie_enable: unknown mode {other:?} (expected 'off', \
                 'count', 'refuse_min' or 'refuse_all')"
            )))
        }
    };
    crate::argmin_tie::set_mode(m);
    Ok(())
}

/// `[(selector, value_term_json, firings, ties)]` for every site that TIED.
/// The site key is the selector's own `value` Term as JSON, so it matches back
/// to the exact `seeds/*.json` rule — read off the firing, never grepped.
#[pyfunction]
fn argmin_tie_sites(py: Python<'_>) -> PyResult<PyObject> {
    let rows = crate::argmin_tie::sites();
    let out = pyo3::types::PyList::empty_bound(py);
    for (key, firings, ties) in rows {
        let mut parts = key.splitn(2, '\u{1}');
        let sel = parts.next().unwrap_or("");
        let term = parts.next().unwrap_or("");
        let d = PyDict::new_bound(py);
        d.set_item("selector", sel)?;
        d.set_item("value_term", term)?;
        d.set_item("firings", firings)?;
        d.set_item("ties", ties)?;
        out.append(d)?;
    }
    Ok(out.into())
}

#[pyfunction]
fn argmin_tie_reset() {
    crate::argmin_tie::reset();
}

/// `{firings, ties, empties, refusals, unique_term_firings, mode}`.
///
/// `ties` and `empties` are SEPARATE on purpose: a tie-refusal and an
/// empty-source null are the same `Value::None` downstream, and a rung that
/// cannot tell them apart has built the instrument that dies first.
#[pyfunction]
fn argmin_tie_stats(py: Python<'_>) -> PyResult<PyObject> {
    let (firings, ties, empties, refusals, unique_term) = crate::argmin_tie::stats();
    let d = PyDict::new_bound(py);
    d.set_item("firings", firings)?;
    d.set_item("ties", ties)?;
    d.set_item("empties", empties)?;
    d.set_item("refusals", refusals)?;
    d.set_item("unique_term_firings", unique_term)?;
    d.set_item(
        "mode",
        match crate::argmin_tie::mode() {
            crate::argmin_tie::MODE_COUNT => "count",
            crate::argmin_tie::MODE_REFUSE_MIN => "refuse_min",
            crate::argmin_tie::MODE_REFUSE_ALL => "refuse_all",
            _ => "off",
        },
    )?;
    Ok(d.into())
}

/// Batch sample an explicit retinal receptor layout from one luminance frame.
/// Every receptor is processed inside this single compiled call.
#[pyfunction]
#[pyo3(signature = (
    luma, source_height, source_width, gaze_az, gaze_el,
    angular_width, angular_height, fov_h, fov_v
))]
#[allow(clippy::too_many_arguments)]
fn retinal_layout_sample(
    py: Python<'_>,
    luma: Vec<f64>,
    source_height: usize,
    source_width: usize,
    gaze_az: Vec<f64>,
    gaze_el: Vec<f64>,
    angular_width: Vec<f64>,
    angular_height: Vec<f64>,
    fov_h: f64,
    fov_v: f64,
) -> PyResult<Vec<f64>> {
    py.allow_threads(|| {
        crate::cognitive_tasks::sample_retinal_layout(
            &luma,
            source_height,
            source_width,
            &gaze_az,
            &gaze_el,
            &angular_width,
            &angular_height,
            fov_h,
            fov_v,
        )
        .map_err(PyValueError::new_err)
    })
}

/// Project allocentric surface supports into explicit retinal receptors.
/// Returns `(values, confidences, present, source_indices)` in receptor order.
#[pyfunction]
#[pyo3(signature = (
    surface_x, surface_y, surface_z, surface_radius, surface_value,
    surface_confidence, pose_x, pose_y, pose_z, pose_yaw, pose_pitch,
    receptor_az, receptor_el, receptor_width, receptor_height
))]
#[allow(clippy::too_many_arguments)]
fn allocentric_retinal_projection(
    py: Python<'_>,
    surface_x: Vec<f64>,
    surface_y: Vec<f64>,
    surface_z: Vec<f64>,
    surface_radius: Vec<f64>,
    surface_value: Vec<f64>,
    surface_confidence: Vec<f64>,
    pose_x: f64,
    pose_y: f64,
    pose_z: f64,
    pose_yaw: f64,
    pose_pitch: f64,
    receptor_az: Vec<f64>,
    receptor_el: Vec<f64>,
    receptor_width: Vec<f64>,
    receptor_height: Vec<f64>,
) -> PyResult<(Vec<f64>, Vec<f64>, Vec<bool>, Vec<i64>)> {
    py.allow_threads(|| {
        crate::cognitive_tasks::project_allocentric_retina(
            &surface_x,
            &surface_y,
            &surface_z,
            &surface_radius,
            &surface_value,
            &surface_confidence,
            pose_x,
            pose_y,
            pose_z,
            pose_yaw,
            pose_pitch,
            &receptor_az,
            &receptor_el,
            &receptor_width,
            &receptor_height,
        )
        .map_err(PyValueError::new_err)
    })
}

// --- module init ----------------------------------------------------------

pub(crate) fn register(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add(
        "InadmissibleEdge",
        m.py().get_type_bound::<InadmissibleEdge>(),
    )?;
    m.add_class::<PyNodeID>()?;
    m.add_class::<PySubstrate>()?;
    m.add_class::<PyEffortDial>()?;
    #[cfg(feature = "gpu_me")]
    m.add_class::<GpuMeHandle>()?;
    m.add_function(wrap_pyfunction!(humanoid_cost_terms, m)?)?;
    m.add_function(wrap_pyfunction!(encode, m)?)?;
    m.add_function(wrap_pyfunction!(decode, m)?)?;
    m.add_function(wrap_pyfunction!(kmeans, m)?)?;
    m.add_function(wrap_pyfunction!(cluster_deform_stats, m)?)?;
    m.add_function(wrap_pyfunction!(sparse_dict_learn, m)?)?;
    m.add_function(wrap_pyfunction!(sparse_encode, m)?)?;
    m.add_function(wrap_pyfunction!(cluster_precision, m)?)?;
    m.add_function(wrap_pyfunction!(bow_histogram, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(selector_audit_enable, m)?)?;
    m.add_function(wrap_pyfunction!(selector_audit_fault_inject, m)?)?;
    m.add_function(wrap_pyfunction!(selector_audit_reset, m)?)?;
    m.add_function(wrap_pyfunction!(selector_audit_stats, m)?)?;
    m.add_function(wrap_pyfunction!(effect_audit_stats, m)?)?;
    m.add_function(wrap_pyfunction!(probe_exactness_stats, m)?)?;
    m.add_function(wrap_pyfunction!(probe_exactness_enable, m)?)?;
    m.add_function(wrap_pyfunction!(probe_exactness_reset, m)?)?;
    m.add_function(wrap_pyfunction!(same_round_visibility_stats, m)?)?;
    m.add_function(wrap_pyfunction!(same_round_visibility_reset, m)?)?;
    m.add_function(wrap_pyfunction!(stage_a_enable, m)?)?;
    m.add_function(wrap_pyfunction!(stage_a_stats, m)?)?;
    m.add_function(wrap_pyfunction!(stage_a_reset, m)?)?;
    m.add_function(wrap_pyfunction!(stage_a_compare_enable, m)?)?;
    m.add_function(wrap_pyfunction!(stage_a_compare_stats, m)?)?;
    m.add_function(wrap_pyfunction!(stage_a_compare_reset, m)?)?;
    m.add_function(wrap_pyfunction!(stage_a_compare_samples, m)?)?;
    m.add_function(wrap_pyfunction!(graph_state_fingerprint, m)?)?;
    m.add_function(wrap_pyfunction!(effect_audit_reset, m)?)?;
    m.add_function(wrap_pyfunction!(effect_audit_set_correction, m)?)?;
    m.add_function(wrap_pyfunction!(argmin_tie_enable, m)?)?;
    m.add_function(wrap_pyfunction!(argmin_tie_reset, m)?)?;
    m.add_function(wrap_pyfunction!(argmin_tie_stats, m)?)?;
    m.add_function(wrap_pyfunction!(argmin_tie_sites, m)?)?;
    m.add_function(wrap_pyfunction!(retinal_layout_sample, m)?)?;
    m.add_function(wrap_pyfunction!(allocentric_retinal_projection, m)?)?;
    m.add_function(wrap_pyfunction!(gammatone_band, m)?)?;
    m.add_function(wrap_pyfunction!(cochleagram, m)?)?;
    m.add_function(wrap_pyfunction!(apc_train, m)?)?;
    m.add_function(wrap_pyfunction!(apc_train_contrastive, m)?)?;
    m.add_function(wrap_pyfunction!(apc_train_masked_cpc, m)?)?;
    m.add_function(wrap_pyfunction!(apc_lift, m)?)?;
    m.add_function(wrap_pyfunction!(apc_formant_bands, m)?)?;
    m.add_function(wrap_pyfunction!(apc_recall, m)?)?;
    m.add_function(wrap_pyfunction!(apc_recall_detail, m)?)?;
    m.add_function(wrap_pyfunction!(apc_purity, m)?)?;
    m.add_function(wrap_pyfunction!(apc_nuisance_subspace, m)?)?;
    m.add_function(wrap_pyfunction!(cmvn, m)?)?;
    m.add_function(wrap_pyfunction!(segment_units, m)?)?;
    m.add_function(wrap_pyfunction!(topk_dot, m)?)?;
    m.add_function(wrap_pyfunction!(topk_match, m)?)?;
    m.add_function(wrap_pyfunction!(fft_ear, m)?)?;
    m.add_function(wrap_pyfunction!(allpole_ear, m)?)?;
    m.add_function(wrap_pyfunction!(sonority_segment, m)?)?;
    m.add_function(wrap_pyfunction!(stft, m)?)?;
    m.add_function(wrap_pyfunction!(hair_cell_envelope, m)?)?;
    m.add_function(wrap_pyfunction!(band_autocorr, m)?)?;
    m.add_function(wrap_pyfunction!(summary_autocorrelogram, m)?)?;
    m.add_function(wrap_pyfunction!(periodicity_track, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_autocorr, m)?)?;
    m.add_function(wrap_pyfunction!(levinson_durbin, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_roots_formants, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_residual, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_formants_bw, m)?)?;
    m.add_function(wrap_pyfunction!(f0_autocorr, m)?)?;
    m.add_function(wrap_pyfunction!(glottal_params_from_residual, m)?)?;
    m.add_function(wrap_pyfunction!(glottal_inverse_iaif, m)?)?;
    m.add_function(wrap_pyfunction!(f0_cepstral, m)?)?;
    m.add_function(wrap_pyfunction!(cepstral_formants, m)?)?;
    m.add_function(wrap_pyfunction!(f0_yin, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_formant_warp_track, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_formant_set_track, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_copy_resynth, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_coeff_track, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_residual_track, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_cross_resynth, m)?)?;
    m.add_function(wrap_pyfunction!(glottal_warp_residual, m)?)?;
    m.add_function(wrap_pyfunction!(lf_excitation_transplant, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_bw_expand_track, m)?)?;
    m.add_function(wrap_pyfunction!(lpc_roots_formants_buggy, m)?)?;
    m.add_function(wrap_pyfunction!(detect_sonority_valleys, m)?)?;
    Ok(())
}

// --- Rule checkpoint export/import round-trip (Rust unit test) ------------

#[cfg(test)]
mod rule_checkpoint_tests {
    use super::*;
    use crate::checker::ConsistencyChecker;
    use crate::grammar::Grammar;
    use crate::rewrite::{Effect, EffectArg, MatchEdge, RewriteRule};

    fn fresh_substrate() -> SubstrateRs {
        SubstrateRs::new(ConsistencyChecker::new(Grammar::new()))
    }

    /// `export_rules`'s underlying `rule_to_json` + `import_rules`'s
    /// underlying `add_rule`/`remove_rule` replay must round-trip a rule
    /// store exactly: same slot count, same indices (export order ==
    /// import order == original `RuleIdx`), same `active`/tombstone state
    /// per slot, and — behaviourally — the imported active rule fires
    /// identically (including a literal effect attr) while the imported
    /// tombstoned rule never fires.
    #[test]
    fn export_import_round_trip_identity() {
        let mut s = fresh_substrate();
        let trigger_t = s.interner.intern("Trigger");
        let target_t = s.interner.intern("Target");
        let minted_a_t = s.interner.intern("MintedA");
        let minted_b_t = s.interner.intern("MintedB");
        let et = s.interner.intern("triggers");
        let src_var = s.interner.intern("src");
        let tgt_var = s.interner.intern("tgt");
        let new_var = s.interner.intern("m");
        let k_key = s.interner.intern("k");

        let a = s.add_node(trigger_t, FxHashMap::default());
        let b = s.add_node(target_t, FxHashMap::default());
        s.graph.insert_edge(a, et, b, FxHashMap::default()).unwrap();

        let rule_a_name = s.interner.intern("rule_A");
        let idx_a = s.add_rule(RewriteRule {
            name: rule_a_name,
            match_edges: vec![MatchEdge {
                src_var,
                edge_type: et,
                tgt_var,
            }],
            where_: None,
            effects: vec![Effect::AddNode {
                new_var,
                type_: minted_a_t,
                attrs: vec![(k_key, EffectArg::Literal(Value::Int(42)))],
            }],
            ..Default::default()
        });
        let rule_b_name = s.interner.intern("rule_B");
        let idx_b = s.add_rule(RewriteRule {
            name: rule_b_name,
            match_edges: vec![MatchEdge {
                src_var,
                edge_type: et,
                tgt_var,
            }],
            where_: None,
            effects: vec![Effect::AddNode {
                new_var,
                type_: minted_b_t,
                attrs: vec![],
            }],
            ..Default::default()
        });
        assert_eq!((idx_a.0, idx_b.0), (0, 1));
        // Tombstone rule_B before exporting — the export must capture that.
        assert!(s.remove_rule(idx_b));

        // Export (same code path as `PySubstrate::export_rules`).
        let exported: Vec<J> = s
            .rules
            .iter()
            .map(|r| rule_to_json(r, &s.terms, &s.interner))
            .collect();
        assert_eq!(exported.len(), 2);
        assert_eq!(exported[0]["active"], serde_json::json!(true));
        assert_eq!(exported[1]["active"], serde_json::json!(false));

        // Import onto a FRESH substrate with its own interner — strings are
        // the portable identity across the JSON boundary, exactly like a
        // real save/load. Recreate the same graph shape the rules match
        // against.
        let mut s2 = fresh_substrate();
        let trigger_t2 = s2.interner.intern("Trigger");
        let target_t2 = s2.interner.intern("Target");
        let et2 = s2.interner.intern("triggers");
        let a2 = s2.add_node(trigger_t2, FxHashMap::default());
        let b2 = s2.add_node(target_t2, FxHashMap::default());
        s2.graph
            .insert_edge(a2, et2, b2, FxHashMap::default())
            .unwrap();

        for (i, rj) in exported.iter().enumerate() {
            let rule = parse_rule_json(rj, &mut s2.terms, &mut s2.interner).unwrap();
            let active = rj.get("active").and_then(|v| v.as_bool()).unwrap();
            let idx = s2.add_rule(rule);
            assert_eq!(
                idx.0 as usize, i,
                "import must reproduce export order as identical indices"
            );
            if !active {
                assert!(s2.remove_rule(idx));
            }
        }

        assert_eq!(s2.rules.len(), 2);
        assert!(s2.rules[0].active, "rule_A must import active");
        assert!(!s2.rules[1].active, "rule_B must import tombstoned");

        // Behavioural check: the imported active rule fires post-import
        // exactly as the original did (including its literal attr); the
        // imported tombstoned rule never fires.
        let minted_a_t2 = s2.interner.intern("MintedA");
        let minted_b_t2 = s2.interner.intern("MintedB");
        s2.run_rules(100);
        assert_eq!(
            s2.graph.nodes_of_type(minted_a_t2).len(),
            1,
            "imported active rule must fire post-import"
        );
        assert_eq!(
            s2.graph.nodes_of_type(minted_b_t2).len(),
            0,
            "imported tombstoned rule must never fire"
        );
        let minted_node = s2.graph.nodes_of_type(minted_a_t2)[0];
        let k2 = s2.interner.intern("k");
        assert_eq!(
            s2.graph.node(minted_node).attrs.get(&k2),
            Some(&Value::Int(42))
        );
    }
}

/// PERCEPTION-AS-ACTION: `Effect::FbSample` — a RULE (not the host)
/// triggering a shared-memory framebuffer sample. Covers the two
/// bullets `Effect::FbSample`'s doc comment promises: it mints the same
/// graph state `Substrate::fb_sample` (the fn the PyO3 `fb_sample`
/// method calls) does directly, and a rule authoring it survives an
/// export/import checkpoint cycle.
#[cfg(test)]
mod fb_sample_effect_tests {
    use super::*;
    use crate::checker::ConsistencyChecker;
    use crate::grammar::Grammar;
    use crate::rewrite::{Effect, EffectArg, MatchEdge, RewriteRule};
    use crate::term::TermNode;

    fn fresh_substrate() -> SubstrateRs {
        SubstrateRs::new(ConsistencyChecker::new(Grammar::new()))
    }

    /// Write a solid-colour fb header+payload to a `/dev/shm`-backed file
    /// — the same trick `term.rs`'s and `rewrite.rs`'s `FbFrameSeq` tests
    /// use (`FbHandle`'s fields are private, so a real header-shaped file
    /// is the only way to build one outside `framebuffer.rs` itself).
    /// Real enough for `Substrate::fb_attach` to accept; no external
    /// writer process needed. Returns the bare shm name (`fb_attach`'s
    /// argument) and the on-disk path (for cleanup).
    fn write_solid_fb(
        tag: &str,
        width: u32,
        height: u32,
        seq: u64,
        fill: (u8, u8, u8, u8),
    ) -> (String, String) {
        let stride = width * 4;
        let name = format!("/jbw_fb_effect_test_{}_{}", tag, std::process::id());
        let path = format!("/dev/shm/{}", name.trim_start_matches('/'));
        use std::io::Write;
        let mut f = std::fs::OpenOptions::new()
            .create(true)
            .write(true)
            .truncate(true)
            .open(&path)
            .expect("write /dev/shm test fb (skip if /dev/shm unavailable)");
        let mut buf = vec![0u8; crate::framebuffer::FB_HEADER_LEN + (height * stride) as usize];
        buf[0..4].copy_from_slice(&crate::framebuffer::FB_MAGIC.to_le_bytes());
        buf[4..8].copy_from_slice(&crate::framebuffer::FB_VERSION.to_le_bytes());
        buf[8..12].copy_from_slice(&width.to_le_bytes());
        buf[12..16].copy_from_slice(&height.to_le_bytes());
        buf[16..20].copy_from_slice(&stride.to_le_bytes());
        buf[20..24].copy_from_slice(&crate::framebuffer::FB_FORMAT_BGRA8888.to_le_bytes());
        buf[24..32].copy_from_slice(&seq.to_le_bytes());
        let (b, g, r, a) = fill;
        for y in 0..height as usize {
            for x in 0..width as usize {
                let p = crate::framebuffer::FB_HEADER_LEN + y * stride as usize + x * 4;
                buf[p] = b;
                buf[p + 1] = g;
                buf[p + 2] = r;
                buf[p + 3] = a;
            }
        }
        f.write_all(&buf).unwrap();
        (name, path)
    }

    fn attr_num(attrs: &crate::graph::Attrs, key: Sym) -> i64 {
        match attrs.get(&key) {
            Some(Value::Float(f)) => *f as i64,
            Some(Value::Int(i)) => *i,
            _ => i64::MIN,
        }
    }

    /// `(row, col, value)` for every `WorldInstance` node, sorted — the
    /// per-cell grid `fb_sample` mints/updates.
    fn cell_grid(s: &SubstrateRs) -> Vec<(i64, i64, i64)> {
        let world_instance_t = s.interner.lookup("WorldInstance").unwrap();
        let row_k = s.interner.lookup("row").unwrap();
        let col_k = s.interner.lookup("col").unwrap();
        let value_k = s.interner.lookup("value").unwrap();
        let mut out: Vec<(i64, i64, i64)> = s
            .graph
            .nodes_of_type(world_instance_t)
            .iter()
            .map(|&nid| {
                let attrs = &s.graph.node(nid).attrs;
                (
                    attr_num(attrs, row_k),
                    attr_num(attrs, col_k),
                    attr_num(attrs, value_k),
                )
            })
            .collect();
        out.sort();
        out
    }

    /// `(rvalue, count)` for every `Region` node, sorted — the segmented
    /// connected components `fb_sample` mints via `segment_and_track`.
    fn region_summary(s: &SubstrateRs) -> Vec<(i64, i64)> {
        let Some(region_t) = s.interner.lookup("Region") else {
            return Vec::new();
        };
        let rvalue_k = s.interner.lookup("rvalue").unwrap();
        let count_k = s.interner.lookup("count").unwrap();
        let mut out: Vec<(i64, i64)> = s
            .graph
            .nodes_of_type(region_t)
            .iter()
            .map(|&nid| {
                let attrs = &s.graph.node(nid).attrs;
                (attr_num(attrs, rvalue_k), attr_num(attrs, count_k))
            })
            .collect();
        out.sort();
        out
    }

    /// Build the canonical "look rule": `?t -[wants_look]-> ?g` (a
    /// `LookTrigger` pointing at the `Game` node to perceive), gated on
    /// `FbFrameSeq(fb) > Attr(?g, "last_looked_seq")` so it fires once
    /// per genuinely new frame, with two effects — `fb_sample` (the
    /// perception-as-action mint/update) then `set_attr` advancing the
    /// watermark to the frame just sampled (closing the gate until the
    /// NEXT frame, i.e. no per-tick churn on a static/paused writer).
    fn install_look_rule(
        s: &mut SubstrateRs,
        fb_id: u32,
        grid_w: i64,
        grid_h: i64,
    ) -> (NodeID, NodeID) {
        let trigger_t = s.interner.intern("LookTrigger");
        let game_t = s.interner.intern("Game");
        let wants_look = s.interner.intern("wants_look");
        let last_seq_key = s.interner.intern("last_looked_seq");
        let trigger = s.add_node(trigger_t, FxHashMap::default());
        let mut game_attrs: FxHashMap<Sym, Value> = FxHashMap::default();
        game_attrs.insert(last_seq_key, Value::Int(-1));
        let game = s.add_node(game_t, game_attrs);
        s.graph
            .insert_edge(trigger, wants_look, game, FxHashMap::default())
            .unwrap();

        let t_var = s.interner.intern("t");
        let g_var = s.interner.intern("g");
        let g_ref = s.terms.add(TermNode::Var { name: g_var });
        let attr_term = s.terms.add(TermNode::Attr {
            node: g_ref,
            key: last_seq_key,
        });
        let fb_lit_where = s.terms.add(TermNode::Lit {
            value: Value::Int(fb_id as i64),
        });
        let fbseq = s.terms.add(TermNode::FbFrameSeq { fb: fb_lit_where });
        let where_term = s.terms.add(TermNode::Gt {
            a: fbseq,
            b: attr_term,
        });

        let fb_lit_watermark = s.terms.add(TermNode::Lit {
            value: Value::Int(fb_id as i64),
        });
        let watermark_term = s.terms.add(TermNode::FbFrameSeq {
            fb: fb_lit_watermark,
        });

        let rule = RewriteRule {
            name: s.interner.intern("look_when_frame_advances"),
            match_edges: vec![MatchEdge {
                src_var: t_var,
                edge_type: wants_look,
                tgt_var: g_var,
            }],
            where_: Some(where_term),
            effects: vec![
                Effect::FbSample {
                    fb: EffectArg::Literal(Value::Int(fb_id as i64)),
                    game_var: g_var,
                    grid_w: EffectArg::Literal(Value::Int(grid_w)),
                    grid_h: EffectArg::Literal(Value::Int(grid_h)),
                },
                Effect::SetAttr {
                    var: g_var,
                    key: last_seq_key,
                    value: EffectArg::Computed(watermark_term),
                },
            ],
            ..Default::default()
        };
        s.add_rule(rule);
        (trigger, game)
    }

    /// A rule's `Effect::FbSample` must mint/update the SAME graph state
    /// (WorldInstance grid + Region segmentation) that calling
    /// `Substrate::fb_sample` directly (the internal fn the PyO3
    /// `fb_sample` method calls) does — two independent substrates
    /// attached to byte-identical fb content, one sampled the direct way,
    /// one sampled purely by the agent's own rule firing via `run_rules`,
    /// with NO host `fb_sample` call at all on the rule side.
    #[test]
    fn fb_sample_effect_mints_same_nodes_as_pyo3_path() {
        let (name, path) = write_solid_fb("mint", 8, 8, 1, (200, 100, 50, 255));

        // --- A: the direct / PyO3-equivalent path ---
        let mut a = fresh_substrate();
        let fb_id_a = a.fb_attach(&name).expect("attach A");
        let game_t_a = a.interner.intern("Game");
        let game_a = a.add_node(game_t_a, FxHashMap::default());
        a.fb_sample(fb_id_a, game_a, 2, 2)
            .expect("direct fb_sample");

        // --- B: purely rule-driven. No host fb_sample call anywhere. ---
        let mut b = fresh_substrate();
        let fb_id_b = b.fb_attach(&name).expect("attach B");
        assert_eq!(
            fb_id_a, fb_id_b,
            "both substrates' first attach must get the same fb_id (fresh next_fb_id=1)"
        );
        install_look_rule(&mut b, fb_id_b, 2, 2);
        let steps = b.run_rules(1000);
        assert!(steps >= 1, "the look rule must have fired at least once");

        // Same downsampled grid, same segmented Region summary.
        assert_eq!(
            cell_grid(&a),
            cell_grid(&b),
            "fb_sample effect must mint the same WorldInstance grid as the direct call"
        );
        assert_eq!(
            region_summary(&a),
            region_summary(&b),
            "fb_sample effect must mint the same Region segmentation as the direct call"
        );
        // Solid fill over an 8x8 frame downsampled 2x2 -> one connected
        // Region covering all 4 cells. Sanity-check the fixture isn't
        // vacuously empty on BOTH sides (a real risk if grid mint failed
        // silently on both paths identically).
        assert_eq!(region_summary(&a).len(), 1);
        assert_eq!(
            region_summary(&a)[0].1,
            4,
            "solid fill -> one 4-cell region"
        );

        // No-churn: a second run_rules call must NOT re-fire (the
        // watermark effect closed the gate; frame_seq hasn't moved).
        let steps2 = b.run_rules(1000);
        assert_eq!(
            steps2, 0,
            "gate must stay closed once the watermark catches up (no churn)"
        );

        let _ = std::fs::remove_file(&path);
    }

    /// The look-rule's `Effect::FbSample` must survive an export/import
    /// checkpoint cycle (`rule_to_json` / `parse_rule_json` — the same
    /// codec `PySubstrate::export_rules`/`import_rules` use) both
    /// structurally (the wire JSON round-trips through the exhaustive
    /// `effect_to_json`/`parse_effect_json` match) and behaviourally (the
    /// imported rule still fires and mints the same graph state as
    /// before export).
    #[test]
    fn fb_sample_effect_round_trips_through_export_import() {
        let (name, path) = write_solid_fb("roundtrip", 8, 8, 1, (10, 20, 30, 255));

        let mut b = fresh_substrate();
        let fb_id_b = b.fb_attach(&name).expect("attach B");
        install_look_rule(&mut b, fb_id_b, 2, 2);

        // Export (same code path as `PySubstrate::export_rules`).
        let exported: Vec<J> = b
            .rules
            .iter()
            .map(|r| rule_to_json(r, &b.terms, &b.interner))
            .collect();
        assert_eq!(exported.len(), 1);
        // Structural check: the effect list round-trips to the fb_sample
        // wire shape, not silently dropped/coerced to something else.
        let effects_json = exported[0]["effects"].as_array().expect("effects list");
        assert_eq!(effects_json[0][0], serde_json::json!("fb_sample"));
        assert_eq!(effects_json[1][0], serde_json::json!("set_attr"));

        // Import onto a FRESH substrate, attaching its OWN handle to the
        // SAME shm content (own next_fb_id counter starts at 1 too, so
        // the literal fb_id baked into the exported rule still resolves).
        let mut c = fresh_substrate();
        let fb_id_c = c.fb_attach(&name).expect("attach C");
        assert_eq!(
            fb_id_c, fb_id_b,
            "fresh substrate's first attach must reproduce the same fb_id"
        );
        let game_t_c = c.interner.intern("Game");
        let trigger_t_c = c.interner.intern("LookTrigger");
        let wants_look_c = c.interner.intern("wants_look");
        let last_seq_key_c = c.interner.intern("last_looked_seq");
        let trigger_c = c.add_node(trigger_t_c, FxHashMap::default());
        let mut game_attrs_c: FxHashMap<Sym, Value> = FxHashMap::default();
        game_attrs_c.insert(last_seq_key_c, Value::Int(-1));
        let game_c = c.add_node(game_t_c, game_attrs_c);
        c.graph
            .insert_edge(trigger_c, wants_look_c, game_c, FxHashMap::default())
            .unwrap();

        for rj in &exported {
            let rule = parse_rule_json(rj, &mut c.terms, &mut c.interner).unwrap();
            c.add_rule(rule);
        }

        let steps = c.run_rules(1000);
        assert!(steps >= 1, "the imported rule must still fire");
        assert!(
            !cell_grid(&c).is_empty(),
            "the imported rule's fb_sample effect must still mint WorldInstance nodes"
        );
        assert_eq!(region_summary(&c).len(), 1);
        assert_eq!(
            region_summary(&c)[0].1,
            4,
            "imported rule mints the same 4-cell region as the pre-export original"
        );

        let _ = std::fs::remove_file(&path);
    }
}
