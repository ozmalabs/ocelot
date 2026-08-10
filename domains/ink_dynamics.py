"""ink_dynamics — RUN 33: "are we missing something simple and stupid like the conservation of
momentum? YES, literally." `domains/omniglot_world.py`'s motor files carry a third column
(millisecond pen-sample timestamp, monotone) that every existing loader/consumer in this arc
silently drops (`load_points`/`load_strokes` read `parts[0], parts[1]` only) — all 32 prior runs
of the Omniglot arc ran on the STATIC trace with dynamics discarded at the loader, and every
downstream resampling step (`glyph_motor_world.to_trajectory`, `stroke_codebook`'s
`StrokeQuantize` `segments`-way equal-ARC-LENGTH split) is CONSTANT-SPEED NORMALIZATION —
run 32's own first-class finding ("len = 1/segments EXACTLY, dimension information-free by
construction") is the flattened velocity profile, read back out.

NAMING NOTE: this file is named `ink_dynamics.py`, NOT `dynamics_features.py` — that name is
already an unrelated, actively-imported SPEECH module (`domains/dynamics_features.py`, movement/
formant-transition Term-tree composition for the acoustic pipeline; referenced by
`order_n_concepts.py`, `hint_grounding.py`, `acoustic_resolution.py`, `grown_representation.py`,
`scripts/develop.py`, `scripts/cutover_test.py`). Overwriting it would have deleted live speech
machinery outside this run's scope; `tests/test_ink_dynamics_migrated.py` is this module's own
test file (not `test_dynamics_features_migrated.py`, for the same collision reason).

THE PHYSICS BEING IMPORTED (each maps to a measured open wound in this arc's own commit log):
  - VELOCITY MINIMA are physically real segment boundaries. Ballistic submovement theory (the
    "two-thirds power law", Viviani & Terzuolo 1982 / Lacquaniti-Terzuolo-Viviani 1983: tangential
    speed ~ curvature^(-1/3) for a smooth curved trajectory) says the pen SLOWS where it turns
    sharply — a corner is a place the writer's own motor program plans a submovement boundary,
    independent of how densely a downstream resampler happens to sample that arc-length span.
    Cuts at fixed-count ARC-LENGTH knots (the pre-existing `ink_decode._knots` candidate set)
    are PARAMETERIZATION-dependent: the same physical corner lands at a different knot index
    depending on how the rest of the stroke's geometry consumes the fixed knot budget. Velocity
    minima, anchored to the writer's OWN kinematics rather than an arc-length grid, are the
    candidate boundary set predicted to be MORE STABLE across different instances (drawers) of
    the same character — this is `arclength_corner_knots` vs `velocity_minima_knots`'s own,
    falsifiable, Gate-0 comparison (`scripts/jabberwock_omniglot_run33_dynamics.py`).
  - CLASS-GRAIN IDENTITY: a character's writers share a MOTOR PROGRAM (a submovement
    sequence), not a static trace — dynamics-grounded per-segment features (duration share,
    peak-speed ratio, the two-thirds-law residual) are class-grain candidates in a way a purely
    geometric quantized signature is not (run 32's own finding: identity from geometry alone
    fragments across drawers, INSTANCE- not CLASS-grain).
  - Writer tempo is a writer-frame axis, the ink twin of the speech VTL (vocal-tract-length)
    nuisance dimension already established for speech.

ARCHITECTURE (CLAUDE.md): this module is a WORLD-ADAPTER-class feature EXTRACTOR — mechanical
translation of raw (x, y, t) pen samples into numeric candidate-boundary positions / per-segment
scalars, exactly the same class of thing `glyph_motor_world._resample_arclen` (arc-length
geometry) and `domains/adaptive_bins.py` (descriptive statistics over an already-gathered
population) already are. Every function here is a FIXED FORMULA over already-collected numbers
— no conditional over graph state, no rule engine, no agent decision. WHICH candidate knot the
segmentation lattice actually CHOOSES as a boundary stays exactly where it always was: the held
`ShapeDecode`/Viterbi machinery in `domains/ink_decode.py` — this module only changes the
CANDIDATE SET fed to that unchanged decoder (per the run-33 brief: "you will CHANGE THE KNOT
PROPOSAL SET, not the decoder").
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np

from domains import glyph_motor_world as gmw

# --------------------------------------------------------------------------- #
#  DEFAULTS (documented, pre-registered before any Gate-0 number is computed).
# --------------------------------------------------------------------------- #
# Smoothing window for the speed profile, in MILLISECONDS (time-based, not sample-based -- a
# fixed sample-count window would over-smooth a fast stretch and under-smooth a slow one).
# 60ms sits inside the ~40-120ms range widely used for tangential-velocity smoothing in the
# handwriting/submovement literature (short enough to preserve genuine submovement minima,
# long enough to reject the single-sample digitizer jitter this dataset's own '~1% per-stroke
# clock glitch' audit found -- see domains/omniglot_world.py's load_strokes_t docstring).
DEFAULT_SMOOTH_MS = 60.0
# A candidate minimum must dip below this fraction of the STROKE'S OWN smoothed-speed max to
# count as a "real" slowdown (a relative, per-stroke threshold -- absolute speed varies hugely
# writer-to-writer and stroke-to-stroke, only the RELATIVE dip is physically meaningful).
DEFAULT_REL_THRESHOLD = 0.55
# The turning-angle-maxima threshold for the competing ARC-LENGTH (geometry-only, no time)
# corner detector -- same relative-threshold shape, applied to |turning angle| instead of speed.
DEFAULT_TURN_REL_THRESHOLD = 0.35
DEFAULT_ARCLEN_KNOTS = 24          # matches ink_decode.DEFAULT_MAX_KNOTS
EPS = 1e-9


# --------------------------------------------------------------------------- #
#  Shared small geometry helpers (arc-length parameterization; no Rust primitive does this
#  projection and it mirrors glyph_motor_world._resample_arclen's own cumulative-distance
#  computation exactly, reused not reimplemented).
# --------------------------------------------------------------------------- #
def _cum_arclen(xy: np.ndarray) -> np.ndarray:
    """Cumulative arc length at each sample, xy[0] -> 0.0."""
    if xy.shape[0] < 2:
        return np.zeros(xy.shape[0])
    d = np.sqrt(((np.diff(xy, axis=0)) ** 2).sum(axis=1))
    return np.concatenate([[0.0], np.cumsum(d)])


def _normalize_positions(cum: np.ndarray) -> np.ndarray:
    total = cum[-1] if cum.size else 0.0
    if total <= EPS:
        return np.zeros_like(cum)
    return cum / total


def _turning_angles(xy: np.ndarray) -> np.ndarray:
    """Signed turning angle (radians) at each INTERIOR point (0.0 at the two endpoints) --
    the angle between the incoming and outgoing segment vectors."""
    n = xy.shape[0]
    out = np.zeros(n)
    if n < 3:
        return out
    v_in = xy[1:-1] - xy[:-2]
    v_out = xy[2:] - xy[1:-1]
    n_in = np.linalg.norm(v_in, axis=1)
    n_out = np.linalg.norm(v_out, axis=1)
    denom = np.maximum(n_in * n_out, EPS)
    cos_t = np.clip((v_in * v_out).sum(axis=1) / denom, -1.0, 1.0)
    cross = v_in[:, 0] * v_out[:, 1] - v_in[:, 1] * v_out[:, 0]
    ang = np.sign(cross) * np.arccos(cos_t)
    out[1:-1] = ang
    return out


def _local_minima_indices(v: np.ndarray) -> list[int]:
    idx = []
    for i in range(1, len(v) - 1):
        if v[i] <= v[i - 1] and v[i] <= v[i + 1] and (v[i] < v[i - 1] or v[i] < v[i + 1]):
            idx.append(i)
    return idx


def _local_maxima_indices(v: np.ndarray) -> list[int]:
    idx = []
    for i in range(1, len(v) - 1):
        if v[i] >= v[i - 1] and v[i] >= v[i + 1] and (v[i] > v[i - 1] or v[i] > v[i + 1]):
            idx.append(i)
    return idx


# --------------------------------------------------------------------------- #
#  SPEED PROFILE -- time-based smoothing (DEFAULT_SMOOTH_MS), central-difference velocity.
# --------------------------------------------------------------------------- #
def speed_profile(xyt: np.ndarray, smooth_ms: float = DEFAULT_SMOOTH_MS) -> np.ndarray:
    """Raw (x, y, t) samples of ONE stroke -> smoothed instantaneous speed at every sample
    (units: distance / time-unit, whatever `t`'s own unit is -- ms in the real Omniglot data).
    Central-difference velocity at interior points (forward/backward at the two endpoints),
    then a TIME-windowed box average (`smooth_ms`, documented above): sample i's smoothed value
    averages every RAW velocity sample j with |t[j] - t[i]| <= smooth_ms / 2 -- a window defined
    in TIME, so a fast stretch (many samples per ms) and a slow stretch (few) are smoothed over
    the SAME physical duration, not the same sample count."""
    xy, t = xyt[:, :2], xyt[:, 2]
    n = xy.shape[0]
    if n < 2:
        return np.zeros(n)
    v_raw = np.zeros(n)
    for i in range(n):
        lo, hi = max(0, i - 1), min(n - 1, i + 1)
        dt = t[hi] - t[lo]
        dist = float(np.linalg.norm(xy[hi] - xy[lo]))
        v_raw[i] = dist / dt if dt > EPS else 0.0
    half = smooth_ms / 2.0
    v_smooth = np.zeros(n)
    for i in range(n):
        mask = np.abs(t - t[i]) <= half
        if not np.any(mask):
            mask = np.zeros(n, dtype=bool)
            mask[i] = True
        v_smooth[i] = float(v_raw[mask].mean())
    return v_smooth


def velocity_minima_knots(xyt: np.ndarray, *, smooth_ms: float = DEFAULT_SMOOTH_MS,
                          rel_threshold: float = DEFAULT_REL_THRESHOLD) -> np.ndarray:
    """The PHYSICAL-boundary candidate set: local minima of the smoothed speed profile whose
    value sits below `rel_threshold` of the stroke's OWN peak smoothed speed (relative, per-
    stroke -- absolute speed is not comparable writer-to-writer). Always includes the stroke's
    start/end (arc-length position 0.0 / 1.0, the SAME boundary convention the arc-length knot
    set uses) so the two candidate sets are directly comparable. Returns sorted, deduped
    NORMALIZED ARC-LENGTH positions (in [0, 1])."""
    xy = xyt[:, :2]
    n = xy.shape[0]
    if n < 3:
        return np.array([0.0, 1.0])
    v = speed_profile(xyt, smooth_ms=smooth_ms)
    vmax = float(v.max()) if v.size else 0.0
    cum = _cum_arclen(xy)
    pos = _normalize_positions(cum)
    knots = {0.0, 1.0}
    if vmax > EPS:
        thresh = rel_threshold * vmax
        for i in _local_minima_indices(v):
            if v[i] <= thresh:
                knots.add(float(pos[i]))
    return np.array(sorted(knots))


# --------------------------------------------------------------------------- #
#  ARC-LENGTH (GEOMETRY-ONLY, NO TIME) CORNER DETECTOR -- the competing, "physically arbitrary"
#  baseline: turning-angle maxima on a FIXED-COUNT arc-length resampling grid. This is the
#  Gate-0 falsifier's control arm, not a replacement for the existing `ink_decode._knots`
#  candidate set (that stays untouched; this function exists to give the physical-boundary
#  hypothesis a fair, comparably-constructed opponent -- geometry alone, same relative-
#  threshold shape as `velocity_minima_knots`, evaluated at the SAME fixed knot budget the
#  pre-existing lattice uses).
# --------------------------------------------------------------------------- #
def arclength_corner_knots(xy: np.ndarray, *, n_knots: int = DEFAULT_ARCLEN_KNOTS,
                           rel_threshold: float = DEFAULT_TURN_REL_THRESHOLD) -> np.ndarray:
    """Resample `xy` to `n_knots` points uniform in arc length (reuses
    `glyph_motor_world._resample_arclen`, the SAME geometry `ink_decode._knots` already
    performs), then take local maxima of |turning angle| above `rel_threshold` of that stroke's
    own peak turning angle. Always includes 0.0 / 1.0. This is 'physically arbitrary' in the
    sense the run-33 brief names: a corner's turning-angle PEAK still gets found, but its
    INDEX (and hence its normalized arc-length position after resampling) depends on how the
    fixed `n_knots` budget happens to fall across the rest of the stroke's geometry -- shifted
    by exactly the amount a differently-proportioned instance of the 'same' character shifts
    it, which is the instability this run measures."""
    n = max(2, min(n_knots, xy.shape[0]))
    knots_xy = gmw._resample_arclen(xy, n) if xy.shape[0] >= 2 else xy
    ang = np.abs(_turning_angles(knots_xy))
    amax = float(ang.max()) if ang.size else 0.0
    pos = np.linspace(0.0, 1.0, n)
    knots = {0.0, 1.0}
    if amax > EPS:
        thresh = rel_threshold * amax
        for i in _local_maxima_indices(ang):
            if ang[i] >= thresh:
                knots.add(float(pos[i]))
    return np.array(sorted(knots))


# --------------------------------------------------------------------------- #
#  KNOT-CANDIDATE UNION -- stage 2's "keep arc-length knots as a UNION option, armed
#  separately": merge two normalized-arc-length knot sets, deduping positions within `tol` of
#  each other (keeps the LOWER of a colliding pair, arbitrary-but-deterministic tie-break --
#  the two positions are within tolerance of "the same" candidate by construction).
# --------------------------------------------------------------------------- #
def union_knots(knots_a: np.ndarray, knots_b: np.ndarray, *, tol: float = 0.02) -> np.ndarray:
    merged = sorted(float(v) for v in list(knots_a) + list(knots_b))
    out: list[float] = []
    for v in merged:
        if not out or v - out[-1] > tol:
            out.append(v)
    return np.array(out)


# --------------------------------------------------------------------------- #
#  CROSS-DRAWER BOUNDARY AGREEMENT -- Gate 0's own metric. Symmetric nearest-neighbour match
#  rate in NORMALIZED ARC LENGTH, within a documented tolerance band, EXCLUDING the trivial
#  shared endpoints (0.0/1.0 are always present in both candidate sets by construction and
#  would equally inflate every arm's score, contributing no discriminating information).
# --------------------------------------------------------------------------- #
DEFAULT_AGREEMENT_TOL = 0.08        # 8% of normalized arc length.


def _interior(knots: np.ndarray, edge_eps: float = 1e-6) -> np.ndarray:
    return np.array([k for k in knots if edge_eps < k < 1.0 - edge_eps])


def _match_rate(x: np.ndarray, y: np.ndarray, tol: float) -> float:
    """Vectorized: fraction of `x` with a `y` element within `tol` (all-pairs |x_i - y_j|,
    min per row) -- same semantics as the original per-point python loop, just fast enough to
    run thousands of times for `count_matched_null_agreement`'s Monte Carlo baseline."""
    if len(x) == 0:
        return 0.0
    diffs = np.abs(x[:, None] - y[None, :])
    return float((diffs.min(axis=1) <= tol).mean())


def pairwise_agreement(knots_a: np.ndarray, knots_b: np.ndarray,
                       tol: float = DEFAULT_AGREEMENT_TOL) -> Optional[float]:
    """Symmetric match rate between two INTERIOR knot sets (endpoints excluded per above): the
    average of (fraction of A's knots with a B-knot within `tol`) and (fraction of B's knots
    with an A-knot within `tol`). `None` when BOTH sets are empty (no interior candidates on
    either side -- undefined, not zero, so callers can exclude it from the mean rather than
    silently scoring it as perfect disagreement).

    WARNING (found during the run-33 Gate-0 robustness check, BEFORE any verdict was reported):
    this raw match rate rises MECHANICALLY with candidate COUNT alone, independent of any
    physical alignment -- a denser point set covers [0,1] more finely, so a nearest-neighbour
    search is more likely to land within `tol` purely by chance (verified: uniform-random knots
    at ~3 points/set already score ~0.40 by chance; at ~12 points/set, ~0.86). A caller comparing
    two knot-proposal METHODS THAT PRODUCE DIFFERENT COUNTS (this run's own arc-length vs
    velocity-minima arms) must NOT compare raw `pairwise_agreement`/`mean_pairwise_agreement`
    scores directly -- use `count_matched_null_agreement` to get the count-controlled baseline
    each arm's raw score should be compared against (`excess = raw - null`)."""
    a, b = _interior(knots_a), _interior(knots_b)
    if a.size == 0 and b.size == 0:
        return None
    if a.size == 0 or b.size == 0:
        return 0.0
    return float((_match_rate(a, b, tol) + _match_rate(b, a, tol)) / 2.0)


def mean_pairwise_agreement(knot_sets: list[np.ndarray],
                            tol: float = DEFAULT_AGREEMENT_TOL) -> dict:
    """All-pairs mean agreement over a list of per-drawer knot sets for ONE character (the
    Gate-0 unit of measurement). Returns the mean, n_pairs actually scored (pairs where both
    sides had >=1 interior knot are scored; a pair where BOTH sides are empty is excluded, per
    `pairwise_agreement`'s own honest-undefined convention), and the raw scores."""
    scores = []
    n = len(knot_sets)
    for i in range(n):
        for j in range(i + 1, n):
            s = pairwise_agreement(knot_sets[i], knot_sets[j], tol=tol)
            if s is not None:
                scores.append(s)
    return {"mean": float(np.mean(scores)) if scores else None, "n_pairs": len(scores),
            "scores": scores}


def count_matched_null_agreement(knot_sets: list, *, tol: float = DEFAULT_AGREEMENT_TOL,
                                 n_reps: int = 100, rng: Optional[np.random.Generator] = None
                                 ) -> Optional[float]:
    """THE DENSITY-CONFOUND CORRECTION (see `pairwise_agreement`'s WARNING): the count-
    controlled NULL baseline `mean_pairwise_agreement`'s raw score must be compared against --
    replaces each drawer's REAL interior knot COUNT (unchanged) with that many UNIFORM-RANDOM
    positions, `n_reps` times, and averages `mean_pairwise_agreement` over the replicates.
    `excess = raw_agreement - count_matched_null_agreement(...)` is the fair, count-normalized
    test of whether a candidate-knot METHOD aligns knots across drawers BETTER than its own
    candidate density would produce by pure chance -- the correct form of the run-33 Gate-0
    'velocity-minima agreement must exceed arc-length agreement' pre-registration, applied
    per-arm against its OWN chance floor rather than raw-score-to-raw-score (which conflates
    the physical-alignment question with a pure density difference between the two methods)."""
    rng = rng if rng is not None else np.random.default_rng(0)
    counts = [int(_interior(np.asarray(k)).size) for k in knot_sets]
    if sum(1 for c in counts if c > 0) < 2:
        return None
    reps = []
    for _ in range(n_reps):
        rand_sets = [np.concatenate([[0.0], np.sort(rng.uniform(0.0, 1.0, size=c)), [1.0]])
                     for c in counts]
        rep = mean_pairwise_agreement(rand_sets, tol=tol)
        if rep["mean"] is not None:
            reps.append(rep["mean"])
    return float(np.mean(reps)) if reps else None


# --------------------------------------------------------------------------- #
#  TWO-THIRDS POWER LAW -- speed ~ curvature^(-1/3) (Viviani-Terzuolo / Lacquaniti et al.):
#  log(v) = c - (1/3) log(kappa) for a smooth curved trajectory under ballistic motor control.
#  `curvature_series` is the SAME 3-point discrete-geometry estimate `_turning_angles` already
#  computes, divided by local arc length (kappa ~= dtheta/ds); `two_thirds_fit` regresses
#  log(v) on log(kappa) (slope near -1/3 confirms the law holds on this data) and
#  `two_thirds_residual` reports the FIXED-SLOPE residual the run-33 brief names: `log(speed) +
#  (1/3) log(curvature)`, which is a CONSTANT (the writer's own preferred combination, `c`
#  above) if -1/3 is exactly the local slope -- a per-writer mean-centred deviation from that
#  constant is the per-segment dynamics feature stage 3 quantizes.
# --------------------------------------------------------------------------- #
def curvature_series(xy: np.ndarray) -> np.ndarray:
    """kappa[i] ~= |turning angle at i| / local arc-length step -- 0.0 at the two endpoints
    (no turning angle defined there, matching `_turning_angles`'s own convention)."""
    n = xy.shape[0]
    kappa = np.zeros(n)
    if n < 3:
        return kappa
    ang = np.abs(_turning_angles(xy))
    seg_in = np.linalg.norm(xy[1:-1] - xy[:-2], axis=1)
    seg_out = np.linalg.norm(xy[2:] - xy[1:-1], axis=1)
    ds = np.maximum((seg_in + seg_out) / 2.0, EPS)
    kappa[1:-1] = ang[1:-1] / ds
    return kappa


def two_thirds_fit(xyt: np.ndarray, *, smooth_ms: float = DEFAULT_SMOOTH_MS,
                   min_points: int = 5) -> Optional[dict]:
    """Fit log(v) = a + b*log(kappa) over one stroke's interior samples (kappa, v both > EPS
    only -- straight sections and zero-speed samples carry no power-law information and would
    blow up the log). Returns `{slope, intercept, r2, n}`, or `None` when fewer than
    `min_points` usable samples survive the filter (an honest, non-crashing insufficient-data
    report, the `EmptyCalibrationError`-class convention this arc already uses elsewhere)."""
    xy = xyt[:, :2]
    v = speed_profile(xyt, smooth_ms=smooth_ms)
    kappa = curvature_series(xy)
    mask = (kappa[1:-1] > EPS) & (v[1:-1] > EPS)
    if int(mask.sum()) < min_points:
        return None
    x = np.log(kappa[1:-1][mask])
    y = np.log(v[1:-1][mask])
    slope, intercept = np.polyfit(x, y, 1)
    y_hat = slope * x + intercept
    ss_res = float(((y - y_hat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > EPS else (1.0 if ss_res <= EPS else 0.0)
    return {"slope": float(slope), "intercept": float(intercept), "r2": float(r2), "n": int(mask.sum())}


def pooled_two_thirds_fit(stroke_xyts: list, *, smooth_ms: float = DEFAULT_SMOOTH_MS,
                          min_points: int = 8) -> Optional[dict]:
    """`two_thirds_fit`'s POOLED twin: concatenate the (log kappa, log v) pairs from EVERY
    stroke in `stroke_xyts` (e.g. one writer's strokes across many characters) and fit ONE
    regression over the pooled population — the per-WRITER number the run-33 Gate-0 falsifier
    reports a distribution of (r² across writers), rather than per-stroke noise. Same honest
    `None` on insufficient pooled data."""
    xs, ys = [], []
    for xyt in stroke_xyts:
        xy = xyt[:, :2]
        v = speed_profile(xyt, smooth_ms=smooth_ms)
        kappa = curvature_series(xy)
        mask = (kappa[1:-1] > EPS) & (v[1:-1] > EPS)
        if not np.any(mask):
            continue
        xs.append(np.log(kappa[1:-1][mask]))
        ys.append(np.log(v[1:-1][mask]))
    if not xs:
        return None
    x = np.concatenate(xs)
    y = np.concatenate(ys)
    if x.size < min_points:
        return None
    slope, intercept = np.polyfit(x, y, 1)
    y_hat = slope * x + intercept
    ss_res = float(((y - y_hat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    r2 = 1.0 - ss_res / ss_tot if ss_tot > EPS else (1.0 if ss_res <= EPS else 0.0)
    return {"slope": float(slope), "intercept": float(intercept), "r2": float(r2),
            "n": int(x.size), "n_strokes": len(xs)}


def two_thirds_residual(xyt: np.ndarray, *, smooth_ms: float = DEFAULT_SMOOTH_MS) -> Optional[dict]:
    """The run-33 brief's FIXED-SLOPE (-1/3) residual, per interior sample: `z = log(v) +
    (1/3) log(kappa)` (constant under an exact two-thirds law); `residual = z - mean(z)` over
    this stroke's own usable samples ('deviation from the writer's own fit'). `None` under the
    same insufficient-data condition `two_thirds_fit` uses."""
    xy = xyt[:, :2]
    v = speed_profile(xyt, smooth_ms=smooth_ms)
    kappa = curvature_series(xy)
    mask = (kappa[1:-1] > EPS) & (v[1:-1] > EPS)
    if int(mask.sum()) < 3:
        return None
    z = np.log(v[1:-1][mask]) + (1.0 / 3.0) * np.log(kappa[1:-1][mask])
    c = float(z.mean())
    return {"c": c, "residual": (z - c).tolist(), "n": int(mask.sum())}


__all__ = ["DEFAULT_SMOOTH_MS", "DEFAULT_REL_THRESHOLD", "DEFAULT_TURN_REL_THRESHOLD",
           "DEFAULT_ARCLEN_KNOTS", "DEFAULT_AGREEMENT_TOL",
           "speed_profile", "velocity_minima_knots", "arclength_corner_knots",
           "union_knots", "pairwise_agreement", "mean_pairwise_agreement",
           "count_matched_null_agreement",
           "curvature_series", "two_thirds_fit", "two_thirds_residual", "pooled_two_thirds_fit"]
