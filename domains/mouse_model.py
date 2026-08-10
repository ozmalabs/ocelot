"""mouse_model — RUN 34: "this isn't handwriting. This is mousewriting" (creator, 2026-07-05).

Omniglot's online strokes are NOT a pen digitizer trace — they are BROWSER/MOUSE traces
recorded from MTurk workers dragging a cursor. Pre-measured, orchestrator-verified facts on a
40-file background sample (re-verified at scale in this run's own Gate 0):
  - 59% of sample-to-sample coordinate DELTAS are EXACT integers (the browser event's
    `clientX`/`clientY` are CSS pixels — an integer lattice).
  - 56% of raw per-sample TURNING ANGLES are EXACTLY 0 degrees ("staircase runs": a diagonal
    mouse motion samples as a run of horizontal/vertical single-pixel steps before the next
    diagonal run, an artifact of the OS/browser mouse-move event coalescing onto the pixel
    grid, not a corner the writer's hand actually turned at).
  - median inter-sample dt ~= 15ms (~60Hz mouse-move event rate — a browser polling artifact,
    not a property of the hand).

Run 32 (commit 13ebc282) found "structure only in [-40,+32] degrees, point-mass at 0" in the
turning-angle distribution and read it as a PROPERTY OF WRITING (short straight segments).
That point-mass is the PIXEL LATTICE, not the hand: a smoothly-curving true pen path, sampled
onto an integer grid at a fixed low event rate, MUST alias into runs of exact-0-degree steps
between the rare samples that land on a still-diagonal grid step — this is a discretization
artifact of the SENSOR, not a discretization of the WRITER's motor program. All six of this
arc's verdict-layer nulls (runs 16/19/20/21/22/25, the ~80.5% full-dwell ceiling) were measured
DOWNSTREAM of a comparator that consumes these raw, sensor-quantized points directly.

AbS DOCTRINE (the reframe this module executes): model the TRUE production process. A writer's
hand moves along a smooth, LATENT intent path; the browser OBSERVES it through two independent,
well-understood, INVERTIBLE distortions:
  1. spatial quantization to the integer CSS-pixel grid (round-to-nearest);
  2. temporal quantization to a fixed ~60Hz mouse-move event clock (the browser only samples
     the cursor position at fixed intervals, not continuously).

Neither distortion is a property of the WRITER. Both are known, simple, and invertible enough
to be worth removing before any verdict or proposal layer ever sees the points — this module is
that removal (`denoise_path`, the INVERSE / reconstruction direction) and its exact FORWARD
twin (`mouse_render`, quantize a synthesized/rendered polyline down to corpus-like input, so a
round-trip render-vs-corpus comparison is apples-to-apples for the first time — run 31's
render-side null made renders SMOOTHER, i.e. moved AWAY from the corpus's own sensor artifact,
exactly backwards).

ARCHITECTURE (CLAUDE.md): this is a WORLD-ADAPTER-class feature transform — a FIXED, documented,
deterministic numpy formula over already-collected raw points, exactly the same class of thing
`glyph_motor_world._resample_arclen` (arc-length geometry) and `ink_dynamics.speed_profile`
(time-windowed box average) already are. No conditional over graph state, no rule engine, no
agent decision — every branch here is a mechanical presence/threshold check on already-computed
numbers (grid-presence fraction, band membership), the same class CLAUDE.md's "thin I/O-boundary
classifier" allowance already covers for this arc's other feature extractors. WHICH shape a span
resolves to, whether a verdict accepts a candidate, etc. all stay exactly where they always were
(the held ShapeDecode/SC+TPS/parse-marginal Terms) — this module only changes the INPUT those
terms are fed, mirroring `domains/ink_dynamics.py`'s own "changes the candidate set, not the
decoder" discipline.

DEFAULTS (documented, pre-registered before any Gate-0 number in this run is computed):
  DEFAULT_GRID_PX = 1.0        the CSS-pixel lattice spacing (background-sample fact: deltas
                                cluster on exact integers at step 1.0).
  DEFAULT_BAND_PX = 0.5        half a quantization cell — round-to-nearest onto a 1.0px grid
                                can move a true point by at most 0.5px in each axis; the
                                reconstructed latent path is constrained to stay within this
                                band of every observed sample (the task's own pre-registered
                                invertibility contract).
  MIN_BAND_FRAC = 0.15         a stroke with NO measurable grid structure (grid_presence_
                                fraction ~0, e.g. a genuinely continuous synthetic curve, or a
                                stroke recorded on a HiDPI/sub-pixel-aware surface) still gets
                                SOME smoothing tolerance, scaled down by its own measured grid
                                fraction — never zero, and never the full 0.5px band either
                                (that would over-smooth genuine sub-pixel detail on a stroke
                                this module's own diagnostic says is NOT on the lattice).
  DEFAULT_DENOISE_ITERS = 2    fixed iteration count for the projected-smoothing reconstruction
                                (see `denoise_path`) — deterministic, no convergence tolerance
                                loop (CLAUDE.md: mechanical, not a search).
                                AMENDMENT (run 34's own Gate 0(ii), pre-registered BEFORE this
                                default was corrected): the original pre-registration used 25
                                iterations, reasoned as "more averaging = more denoising". Gate
                                0(ii)'s own invertibility check on a higher-curvature synthetic
                                (a 2x/3x-frequency Lissajous curve) FALSIFIED that reasoning —
                                RMS-to-truth was MINIMIZED at 1-2 iterations (~0.25-0.26px, well
                                under the 0.35px bound and a real improvement over the ~0.40px
                                raw-quantized error) and got MONOTONICALLY WORSE with every
                                additional iteration (0.5477px at 25, WORSE than doing nothing).
                                MECHANISM: a 3-tap box filter's effective smoothing bandwidth
                                grows with iteration count (a discrete-diffusion process, reach
                                ~sqrt(iters) samples); the browser's spatial quantization noise
                                is a SINGLE-SAMPLE-SCALE artifact (uncorrelated between adjacent
                                samples), but genuine pen curvature lives at the SAME
                                multi-sample scale extra iterations start reaching into — so
                                more iterations don't remove more sensor noise, they progressively
                                erase real shape. The corrected default targets ONLY the
                                single-sample scale the sensor model actually claims to be
                                noisy at, never re-tuned against any downstream accuracy number
                                (the correction is justified by the Gate-0(ii) MECHANISM check
                                alone, the same discipline run 32's own bin-edge amendment used).
  DEFAULT_EVENT_DT_MS = 15.0   background-sample fact: median inter-sample dt ~= 15ms (~60Hz).
  DEFAULT_PX_PER_EVENT = 1.0   background-sample fact (this run's own 60-file re-check, `Gate
                                0(i)`): median per-event displacement ~= 1.0px — a mouse drag
                                typically advances about one pixel per polled event at normal
                                writing speed. Used only by `mouse_render`'s OPTIONAL event-rate
                                resampling to give a rendered polyline a corpus-like SAMPLE
                                DENSITY (not real physical timing — a rendered polyline carries
                                no ground-truth duration).
"""
from __future__ import annotations

from typing import Optional

import numpy as np

EPS = 1e-9

DEFAULT_GRID_PX = 1.0
DEFAULT_BAND_PX = 0.5
MIN_BAND_FRAC = 0.15
DEFAULT_DENOISE_ITERS = 2
DEFAULT_EVENT_DT_MS = 15.0
DEFAULT_PX_PER_EVENT = 1.0
GLOBAL_MAX_ITERS = 300        # RUN 34b: projected-Gauss-Seidel sweep cap (see denoise_path_global).
GLOBAL_CONVERGE_TOL = 1e-4    # px: a sweep whose largest single-point move is under this stops early.


# --------------------------------------------------------------------------- #
#  GRID DIAGNOSTICS — mechanical measurement, no decision. Shared by Gate 0's re-verification
#  and by the denoiser's own per-stroke band-scaling.
# --------------------------------------------------------------------------- #
def integer_delta_fraction(points, *, eps: float = 1e-6) -> float:
    """Fraction of consecutive-sample coordinate DELTAS (dx and dy pooled together) that are
    (near-)exact integers — the grid-presence diagnostic this run's Gate 0(i) re-verifies at
    scale (background sample fact: ~59%). `points`: (m, >=2) array-like, only the first two
    columns are used. Returns 0.0 for a degenerate (<2-point) stroke (no deltas to measure —
    an honest floor, not a fabricated value)."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 2:
        return 0.0
    d = np.diff(pts[:, :2], axis=0).flatten()
    if d.size == 0:
        return 0.0
    return float(np.mean(np.abs(d - np.round(d)) < eps))


def exact_zero_turn_fraction(points, *, eps: float = 1e-9) -> float:
    """Fraction of INTERIOR turning angles that are EXACTLY zero (the "staircase run" fact —
    background sample: ~56%). Reuses `ink_dynamics._turning_angles`'s own signed-angle
    geometry (no reimplementation) rather than a fresh trig pass. Interior-only (matches that
    function's own zero-at-endpoints convention; a <3-point stroke has no interior samples and
    returns 0.0, honestly — no turning is DEFINED, not measured-and-found-straight)."""
    from domains.ink_dynamics import _turning_angles
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 3:
        return 0.0
    ang = _turning_angles(pts[:, :2])
    interior = ang[1:-1]
    if interior.size == 0:
        return 0.0
    return float(np.mean(np.abs(interior) < eps))


def sample_dt_ms(xyt) -> np.ndarray:
    """Consecutive-sample time deltas (ms) from an (m, 3) xyt array (third column = timestamp,
    `omniglot_world.load_strokes_t`'s own convention) — only strictly-positive deltas (a
    non-monotone/duplicate-timestamp glitch contributes nothing, matching this arc's own
    `~1% clock glitch` tolerance elsewhere). Returns an empty array for a degenerate stroke."""
    xyt = np.asarray(xyt, dtype=float)
    if xyt.ndim != 2 or xyt.shape[0] < 2 or xyt.shape[1] < 3:
        return np.zeros(0)
    dt = np.diff(xyt[:, 2])
    return dt[dt > 0.0]


def grid_presence_fraction(points, *, eps: float = 1e-6) -> float:
    """Alias of `integer_delta_fraction` under the name the denoiser's own band-scaling reads
    (kept as a separate, stable name so a future per-stroke diagnostic swap — e.g. combining
    delta-integrality with the zero-turn fraction — only has to change this one function)."""
    return integer_delta_fraction(points, eps=eps)


def adaptive_tolerance(points, *, base_tol: float = DEFAULT_BAND_PX,
                        min_band_frac: float = MIN_BAND_FRAC) -> float:
    """DENOISER BAND-SCALING (build item 1(a)'s "handle the non-integer-delta files
    gracefully" requirement): a stroke with strong grid structure (`grid_presence_fraction`
    near 1.0) gets the FULL `base_tol` (0.5px) reconstruction band; a stroke with little/no
    measurable grid structure gets a band scaled DOWN to `min_band_frac * base_tol` at worst —
    never zero (some smoothing tolerance is always applied — a genuinely noise-free stroke is
    unharmed by a tiny band; see `denoise_path`'s own convergence note) and never claiming the
    full half-pixel band the diagnostic itself says isn't warranted."""
    frac = grid_presence_fraction(points)
    scale = max(float(frac), float(min_band_frac))
    return float(base_tol) * scale


# --------------------------------------------------------------------------- #
#  INVERSE MODEL — denoise / latent-path reconstruction (build item 1(a)).
# --------------------------------------------------------------------------- #
def denoise_path(points, *, tol: Optional[float] = None, iters: int = DEFAULT_DENOISE_ITERS,
                  base_tol: float = DEFAULT_BAND_PX,
                  min_band_frac: float = MIN_BAND_FRAC, mode: str = "local") -> np.ndarray:
    """Reconstruct the smooth LATENT intent path consistent with integer-pixel quantization:
    iterated local averaging (a 3-tap [0.25, 0.5, 0.25] box filter along the path, endpoints
    held fixed — the same "no Rust primitive, mechanical geometry" class as
    `ink_dynamics.speed_profile`'s own time-windowed average) with a PROJECTION back into a
    tolerance band of each original observed sample after every averaging pass — the
    reconstructed path can never drift more than `tol` (Chebyshev, per axis) from what was
    actually observed at that sample index, which is exactly the pre-registered invertibility
    contract ("the reconstructed path stays within ~0.5px of observations").

    `tol=None` (the default) auto-scales via `adaptive_tolerance` (build item 1(a)'s per-stroke
    grid-detection requirement) — a strongly-gridded stroke gets the full `base_tol` band, a
    gridless stroke a scaled-down one. An explicit `tol` overrides the auto-scale (used by
    Gate 0(ii)'s own synthetic invertibility check, which needs a FIXED, known band to
    pre-register a bound against).

    DETERMINISTIC: fixed iteration count, no data-dependent stopping rule — the method is
    mechanical (CLAUDE.md's own "iteration is not a decision" idiom: repeated application of a
    fixed formula, the same discipline `run_rules`'s own fixed-point loop already follows at
    the graph level, just performed here in plain numpy since no graph state is involved).
    `<3`-point strokes have no interior point to average and are returned unchanged (nothing
    to reconstruct — a straight 1- or 2-point segment IS its own latent path).

    `mode="local"` (the default — BYTE-IDENTICAL to every pre-34b call site, so every existing
    caller/test is unaffected) runs the method above. `mode="global"` (RUN 34b) delegates
    entirely to `denoise_path_global` — the GLOBAL constrained smoother named as this local
    method's principled successor once 34a's own Gate-0(iii) showed a local filter cannot see
    past an exactly-collinear Bresenham run to the curvature underneath it. `iters` is
    LOCAL-method-only and ignored under `mode="global"` (the global method's own stopping rule
    is `max_iters`/`converge_tol` — call `denoise_path_global` directly for non-default control
    over those). Every existing `denoise=True` wiring point (`glyph_motor_world.to_trajectory`
    [`_strokes`], `ink_decode.ingest_ink`, `abs_read.stage_parse_char`, …) already forwards its
    `denoise_kwargs` dict verbatim into this function, so passing `denoise_kwargs={"mode":
    "global"}` selects the global smoother at every one of those call sites with NO wiring
    changes anywhere else — exactly the "one parameter, no new plumbing" requirement."""
    if mode == "global":
        return denoise_path_global(points, tol=tol, base_tol=base_tol, min_band_frac=min_band_frac)
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 3:
        return pts.copy()
    xy = pts[:, :2].copy()
    band = float(tol) if tol is not None else adaptive_tolerance(
        xy, base_tol=base_tol, min_band_frac=min_band_frac)
    lo, hi = xy - band, xy + band
    cur = xy.copy()
    for _ in range(max(0, int(iters))):
        sm = cur.copy()
        sm[1:-1] = 0.25 * cur[:-2] + 0.5 * cur[1:-1] + 0.25 * cur[2:]
        cur = np.clip(sm, lo, hi)
    if pts.shape[1] > 2:
        return np.concatenate([cur, pts[:, 2:]], axis=1)
    return cur


# --------------------------------------------------------------------------- #
#  GLOBAL INVERSE MODEL (RUN 34b) — the PRINCIPLED successor to the local iterated filter
#  above, named by 34a's own Gate-0(iii) failure: a Bresenham staircase run is locally EXACTLY
#  collinear over >=3 samples, so a 3-tap local average (however it's clipped) cannot see past
#  a whole straight run to the curvature underneath it — widening the local kernel to see past
#  it reopens the invertibility bound (34a's own falsified iters=25 attempt). The correct
#  inverse for KNOWN, BOUNDED quantization noise is a GLOBAL constrained smoother: the latent
#  path minimizes whole-stroke curvature subject to staying within each sample's own tolerance
#  band — a collinear pixel run is a +/-0.5px TUBE the latent path may bow through using
#  information from OUTSIDE the run (the run's own two ends connect to samples that are NOT
#  collinear with it), which no local filter can access by construction.
# --------------------------------------------------------------------------- #
def _pentadiagonal_bands(m: int):
    """Band coefficients of M = D2^T D2, the (m, m) normal-equations matrix for the whole-path
    curvature objective ||D2 x||^2, where `(D2 x)_i = x_{i-1} - 2 x_i + x_{i+1}` for the `m-2`
    valid interior rows (i = 0 .. m-3 over 0-indexed points). M is the standard discrete-
    biharmonic PENTADIAGONAL stencil ([1, -4, 6, -4, 1] in its far-interior rows, tapering near
    each end where fewer D2 rows touch a column) — derived ONCE per stroke length (not per
    Gauss-Seidel sweep) and reused by every sweep, so building it is O(m) and every sweep
    thereafter is also O(m): no (m, m) matrix is ever materialised.

    `d0` = main diagonal M[k,k]; `d1[k]` = M[k,k+1] (first off-diagonal, valid for k<m-1);
    `d2[k]` = M[k,k+2] (second off-diagonal, valid for k<m-2). M is symmetric, so a caller
    reads `M[k,k-1]` as `d1[k-1]` and `M[k,k-2]` as `d2[k-2]`.

    Derivation (row r of D2, r = 0..m-3, touches columns r, r+1, r+2 with coefficients
    1, -2, 1): column k receives a squared-coefficient contribution from row k (coeff 1, valid
    iff `0<=k<=m-3`), row k-1 (coeff -2, contributes 4, valid iff `0<=k-1<=m-3`), and row k-2
    (coeff 1, valid iff `0<=k-2<=m-3`) — giving `d0[k] = [k valid] + 4*[k-1 valid] + [k-2
    valid]`. The two off-diagonals follow the same row-overlap counting (see this run's commit
    message / build notes for the full derivation); both reduce correctly at every boundary
    (m=3, m=4, m>=5) without any special-cased branch, which is exactly why a boundary point is
    handled as "just another row of the same linear system" rather than a separate code path —
    the pre-registered "endpoints constrained like interior points" requirement falls out of
    this for free."""
    r = np.arange(m, dtype=float)

    def _valid(x):
        return (x >= 0) & (x <= m - 3)

    d0 = _valid(r).astype(float) + 4.0 * _valid(r - 1).astype(float) + _valid(r - 2).astype(float)
    d1 = -2.0 * (_valid(r - 1).astype(float) + _valid(r).astype(float))
    d2 = _valid(r).astype(float)
    return d0, d1, d2


def _gs_smooth_axis(obs: np.ndarray, band: np.ndarray, d0: np.ndarray, d1: np.ndarray,
                     d2: np.ndarray, *, max_iters: int, converge_tol: float) -> np.ndarray:
    """Projected Gauss-Seidel on ONE coordinate axis — x and y are solved INDEPENDENTLY (the
    curvature operator D2 acts along the path index only, never mixing axes; the box
    constraint is likewise per-axis). Each sweep visits every point once, updating it to the
    EXACT conditional curvature-minimizer given its (already-partially-updated, Gauss-Seidel
    style) neighbours — `x_k <- -(sum of M[k,j]*x_j over j!=k) / M[k,k]` from the pentadiagonal
    bands above — then PROJECTS the new value back into `[obs_k - band_k, obs_k + band_k]`
    (the invertibility contract, identical band semantics to `denoise_path`). A forward sweep
    is immediately followed by a backward sweep (symmetric Gauss-Seidel — propagates
    information both directions per outer iteration instead of only one, halving the sweep
    count needed for a given accuracy). CONVERGENCE: an outer iteration whose largest single
    per-point move is below `converge_tol` (px) stops the loop early; `max_iters` is a hard
    cap regardless (both mechanical, fixed scalar checks — never a data-dependent search).
    O(m) per sweep (only the five nonzero band coefficients participate per point), O(m *
    iters) total."""
    m = int(obs.shape[0])
    x = obs.copy()
    lo, hi = obs - band, obs + band

    def _sweep(order) -> float:
        max_move = 0.0
        for k in order:
            if d0[k] <= 0.0:
                continue    # m<3 degenerate rows only -- never reached from denoise_path_global.
            s = 0.0
            if k - 2 >= 0:
                s += d2[k - 2] * x[k - 2]
            if k - 1 >= 0:
                s += d1[k - 1] * x[k - 1]
            if k + 1 < m:
                s += d1[k] * x[k + 1]
            if k + 2 < m:
                s += d2[k] * x[k + 2]
            new_k = -s / d0[k]
            if new_k < lo[k]:
                new_k = lo[k]
            elif new_k > hi[k]:
                new_k = hi[k]
            move = abs(new_k - x[k])
            if move > max_move:
                max_move = move
            x[k] = new_k
        return max_move

    fwd = range(m)
    bwd = range(m - 1, -1, -1)
    for _ in range(max(0, int(max_iters))):
        move = _sweep(fwd)
        move = max(move, _sweep(bwd))
        if move < converge_tol:
            break
    return x


def denoise_path_global(points, *, tol: Optional[float] = None, base_tol: float = DEFAULT_BAND_PX,
                         min_band_frac: float = MIN_BAND_FRAC, max_iters: int = GLOBAL_MAX_ITERS,
                         converge_tol: float = GLOBAL_CONVERGE_TOL) -> np.ndarray:
    """RUN 34b — THE GLOBAL CONSTRAINED SMOOTHER (build item: 34a's named next lever).
    PRE-REGISTERED METHOD: minimize `sum ||D2 x||^2` (whole-stroke curvature — the discrete
    second difference along the path, NOT along time or arc length) over the ENTIRE stroke at
    once, subject to per-point box constraints `|x_i - obs_i| <= tol_i` (Chebyshev, per axis) —
    `tol_i` from the SAME `adaptive_tolerance` / grid-presence machinery `denoise_path` already
    uses (a stroke with strong grid structure gets the full `base_tol` band; a gridless stroke
    gets a scaled-down one; never zero). ENDPOINTS PARTICIPATE AS FREE, BOX-CONSTRAINED
    VARIABLES, not fixed anchors — the pen-down/pen-up sample is itself a quantized
    observation, exactly like every interior sample, per the pre-registered brief; this is the
    one documented difference in convention from `denoise_path` (whose local 3-tap filter
    structurally never touches its own first/last index).

    SOLVER: `D2^T D2` is PENTADIAGONAL (a discrete-biharmonic stencil, `_pentadiagonal_bands`);
    minimizing the resulting convex quadratic under box constraints is solved by PROJECTED
    GAUSS-SEIDEL (`_gs_smooth_axis`) — a standard scheme for a convex QP with box constraints:
    each unprojected Gauss-Seidel step is non-increasing in the unconstrained objective (exact
    per-coordinate minimization holding all others fixed), and projection only pulls a point
    BACK toward its own observation band, never away from it. x and y are solved as two
    INDEPENDENT 1-D problems (the curvature operator never mixes axes). NUMPY-ONLY,
    DETERMINISTIC (no RNG, no scipy) — O(m) per sweep, O(m * iters) total, `max_iters=300` /
    `converge_tol=1e-4px` pre-registered stopping rule (see `_gs_smooth_axis`).

    `<3`-point strokes have no curvature to define (matches `denoise_path`'s own convention —
    nothing to reconstruct, returned unchanged)."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] < 3:
        return pts.copy()
    xy = pts[:, :2].copy()
    m = xy.shape[0]
    band_scalar = float(tol) if tol is not None else adaptive_tolerance(
        xy, base_tol=base_tol, min_band_frac=min_band_frac)
    band = np.full(m, band_scalar, dtype=float)
    d0, d1, d2 = _pentadiagonal_bands(m)
    x_out = _gs_smooth_axis(xy[:, 0], band, d0, d1, d2, max_iters=max_iters,
                             converge_tol=converge_tol)
    y_out = _gs_smooth_axis(xy[:, 1], band, d0, d1, d2, max_iters=max_iters,
                             converge_tol=converge_tol)
    out = np.stack([x_out, y_out], axis=1)
    if pts.shape[1] > 2:
        return np.concatenate([out, pts[:, 2:]], axis=1)
    return out


def denoise_strokes(strokes: list, **kwargs) -> list:
    """`denoise_path` applied per-stroke to a LIST of (m_i, >=2) point arrays — the shape
    `omniglot_world.load_strokes`/`load_strokes_t` already return. Mechanical map, no cross-
    stroke coupling (each stroke is its own independent pen-down segment; the browser's mouse-
    move sampling artifact is per-drag, not per-figure)."""
    return [denoise_path(s, **kwargs) for s in strokes]


# --------------------------------------------------------------------------- #
#  FORWARD MODEL — quantize a synthesized/rendered polyline down to corpus-like (build item
#  1(b)). Deterministic, no RNG in the default path (the task's own explicit requirement — a
#  rendered comparator must be REPRODUCIBLE, not a fresh noisy draw per call).
# --------------------------------------------------------------------------- #
def quantize_to_grid(points, *, grid: float = DEFAULT_GRID_PX) -> np.ndarray:
    """Round xy (only) to the nearest multiple of `grid` — the spatial half of the forward
    observation model. `grid<=0` is treated as "no spatial quantization" (returns the input
    unchanged) — an honest degenerate case, never a divide-by-zero."""
    pts = np.asarray(points, dtype=float)
    if pts.ndim != 2 or pts.shape[0] == 0:
        return pts.copy()
    if grid <= 0:
        return pts.copy()
    out = pts.copy()
    out[:, :2] = np.round(pts[:, :2] / grid) * grid
    return out


def resample_event_rate(points, *, px_per_event: float = DEFAULT_PX_PER_EVENT) -> np.ndarray:
    """Resample a polyline (ARBITRARY point count/parameterization — a rendered curve, not a
    real mouse trace) onto a corpus-like SAMPLE DENSITY: constant-ARC-LENGTH-speed traversal
    (the same convention `omniglot_world._synthetic_arclen_time`'s pre-existing fallback clock
    already uses) at roughly `px_per_event` pixels advanced per output sample — the temporal
    half of the forward observation model, expressed as a SPACING (since a rendered polyline
    carries no ground-truth duration to resample against a true ms clock). A degenerate
    (<2-point or zero-length) input is returned unchanged — nothing to resample."""
    pts = np.asarray(points, dtype=float)
    xy = pts[:, :2] if pts.ndim == 2 else pts
    if xy.ndim != 2 or xy.shape[0] < 2 or px_per_event <= 0:
        return pts.copy()
    d = np.sqrt(((np.diff(xy, axis=0)) ** 2).sum(axis=1))
    cum = np.concatenate([[0.0], np.cumsum(d)])
    total = float(cum[-1])
    if total <= EPS:
        return pts.copy()
    n_events = max(2, int(round(total / px_per_event)) + 1)
    u = np.linspace(0.0, total, n_events)
    return np.stack([np.interp(u, cum, xy[:, 0]), np.interp(u, cum, xy[:, 1])], axis=1)


def mouse_render(points, *, grid: float = DEFAULT_GRID_PX, resample: bool = False,
                  px_per_event: float = DEFAULT_PX_PER_EVENT) -> np.ndarray:
    """THE FORWARD OBSERVATION MODEL: given a rendered/synthesized polyline, produce corpus-
    like input — resample to a mouse-event-like sample density (`resample=True`, OFF by
    default: the primary corpus-matching statistic this run measures is the spatial pixel
    lattice, not sample density, and event-rate resampling changes point COUNT which most
    existing comparators assume is fixed/resampled downstream anyway) THEN quantize to the
    integer pixel grid (always applied — the headline forward-model step). Order matters:
    resampling BEFORE quantizing means the final points sit exactly on corpus-like coarse
    knots snapped to the lattice, matching how a real mouse trace is produced (the hand moves
    continuously, the BROWSER samples then rounds — not the reverse)."""
    pts = np.asarray(points, dtype=float)
    if resample:
        pts = resample_event_rate(pts, px_per_event=px_per_event)
    return quantize_to_grid(pts, grid=grid)


__all__ = [
    "DEFAULT_GRID_PX", "DEFAULT_BAND_PX", "MIN_BAND_FRAC", "DEFAULT_DENOISE_ITERS",
    "DEFAULT_EVENT_DT_MS", "DEFAULT_PX_PER_EVENT", "GLOBAL_MAX_ITERS", "GLOBAL_CONVERGE_TOL",
    "integer_delta_fraction", "exact_zero_turn_fraction", "sample_dt_ms",
    "grid_presence_fraction", "adaptive_tolerance",
    "denoise_path", "denoise_path_global", "denoise_strokes",
    "quantize_to_grid", "resample_event_rate", "mouse_render",
]
