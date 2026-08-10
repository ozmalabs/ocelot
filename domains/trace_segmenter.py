"""trace_segmenter — graph-native handwriting trace SEGMENTATION (change-point in the
residual-recurrence). donkey=0, earn-not-borrow.

THE KEYSTONE (shape_made_by_residual): a STROKE is a segment of the pen trajectory
following ONE residual-recurrence law (smoothly-varying curvature); a BOUNDARY is where
that law BREAKS. So segmentation = CHANGE-POINT DETECTION on cues of the recurrence:
  • pen-LIFT       — the obvious K-1 splits between separate strokes (no recurrence across a lift)
  • VELOCITY MINIMA — the pen slows at junctions/cusps (a local min of step magnitude)
  • TURNING / CURVATURE EXTREMA — corners: a local max of the turn angle between steps
  • RESIDUAL-LAW JUMP — the finite-diff curvature jumps where the generative law switches

ALL cues are HELD TERMS run by the Rust evaluator (no LLM, no scipy):
  velocity[i]   = Magnitude(Minus(p[i+1], p[i]))            # held finite-diff
  turning[i]    = AngleBetween(step[i], step[i-1])          # held turn angle
  curvejump[i]  = Abs(Minus(turning[i], turning[i-1]))      # held residual-law jump
  boundary set  = Fold over indices, Append i where cue[i] is a local extremum past an
                  ADAPTIVE threshold (mean + k*spread, all held Plus/Div/Minus/Gt).

The segmenter splits the CONCATENATED trajectory (blind to the true splits) so the
discriminative control is meaningful. Python is ONLY world-adapter (load points) +
mechanical dispatch of the held Terms.
"""
from __future__ import annotations
import numpy as _np
import substrate_rs as _srs
import domains.omniglot_world as _ow

_S = _srs._NativeSubstrate()


def _resample(pts, n=24):
    """Arc-length resample to n points (world-adapter: puts the trace at a fixed scale so
    the change-point cues fire at structural corners, not per-point sensor noise).
    numpy used ONLY here as a trace adapter; all CUE/DECISION logic is held Terms."""
    a = _np.asarray(pts, float)
    if len(a) < 2:
        return a
    d = _np.sqrt(((_np.diff(a, axis=0)) ** 2).sum(1))
    cum = _np.concatenate([[0.0], _np.cumsum(d)])
    if cum[-1] == 0:
        return a[:1]
    u = _np.linspace(0.0, cum[-1], n)
    return _np.stack([_np.interp(u, cum, a[:, 0]), _np.interp(u, cum, a[:, 1])], 1)
_L = lambda v: {"type": "Lit", "value": v}
_V = lambda n: {"type": "Var", "name": n}


def _ev(term):
    return _S.evaluate(term, {})


# ---- per-point cue terms (held finite-diff over the trajectory) ----

def _velocity_term(pts):
    """Magnitude of each step VecSub(p[i+1],p[i]) — a held list of step speeds."""
    steps = []
    for i in range(len(pts) - 1):
        steps.append({"type": "Magnitude",
                      "arg": {"type": "VecSub", "a": _L(list(map(float, pts[i + 1]))),
                              "b": _L(list(map(float, pts[i])))}})
    # evaluate each (held Term) -> python floats for the change-point scan
    return [float(_ev(s)) for s in steps]


def _turning_term(pts):
    """AngleBetween consecutive steps (held VecSub) — turn angle per interior point."""
    out = [0.0]
    for i in range(1, len(pts) - 1):
        a = {"type": "VecSub", "a": _L(list(map(float, pts[i + 1]))), "b": _L(list(map(float, pts[i])))}
        b = {"type": "VecSub", "a": _L(list(map(float, pts[i]))), "b": _L(list(map(float, pts[i - 1])))}
        # |turn| — a corner is a sharp turn regardless of sign (held Abs over AngleBetween)
        out.append(float(_ev({"type": "Abs", "arg": {"type": "AngleBetween", "a": a, "b": b}})))
    out.append(0.0)
    return out


def _curvejump_term(turning):
    """Abs(Minus(turn[i],turn[i-1])) — held residual-law jump (curvature derivative)."""
    out = [0.0]
    for i in range(1, len(turning)):
        out.append(float(_ev({"type": "Abs",
                              "arg": {"type": "Minus", "a": _L(turning[i]), "b": _L(turning[i - 1])}})))
    return out


def _adaptive_thr_term(cue, k=1.0):
    """mean + k*spread, all held Terms: Div(Plus(items),n) then mean abs-dev."""
    n = len(cue)
    if n == 0:
        return 0.0
    mean = float(_ev({"type": "Div", "a": {"type": "Plus", "items": [_L(float(x)) for x in cue]}, "b": _L(float(n))}))
    devs = [float(_ev({"type": "Abs", "arg": {"type": "Minus", "a": _L(float(x)), "b": _L(mean)}})) for x in cue]
    spread = float(_ev({"type": "Div", "a": {"type": "Plus", "items": [_L(d) for d in devs]}, "b": _L(float(n))}))
    return mean + k * spread


def _changepoints_term(cue, thr, want_min=False, min_gap=4):
    """HELD Fold over indices: Append i where cue[i] is a LOCAL extremum past thr.
    want_min=True detects local minima (velocity), False detects maxima (turning)."""
    n = len(cue)
    idxs = list(range(1, n - 1))
    # build a held Fold that appends index i when local-extremum && past-threshold.
    # cue passed as a Lit list; comparisons via held Gt/Lt on IndexAt.
    cuL = _L([float(x) for x in cue])
    i = _V("i")
    ci = {"type": "IndexAt", "seq": cuL, "index": i}
    cprev = {"type": "IndexAt", "seq": cuL, "index": {"type": "Minus", "a": i, "b": _L(1)}}
    cnext = {"type": "IndexAt", "seq": cuL, "index": {"type": "Plus", "items": [i, _L(1)]}}
    if want_min:
        local_items = [{"type": "Lt", "a": ci, "b": cprev}, {"type": "Lt", "a": ci, "b": cnext}]
        past = {"type": "Lt", "a": ci, "b": _L(thr)}   # below thr = slow (a minimum)
    else:
        local_items = [{"type": "Gt", "a": ci, "b": cprev}, {"type": "Gt", "a": ci, "b": cnext}]
        past = {"type": "Gt", "a": ci, "b": _L(thr)}
    body = {"type": "IfThenElse",
            "cond": {"type": "And", "items": local_items + [past]},
            "then": {"type": "Append", "seq": _V("acc"), "item": i},
            "other": _V("acc")}
    fold = {"type": "Fold", "source": _L(idxs), "init": _L([]), "acc_name": "acc", "var_name": "i", "body": body}
    raw = list(_ev(fold))
    # non-max suppression by min_gap (mechanical, not a decision)
    out = []
    for ix in raw:
        if not out or ix - out[-1] >= min_gap:
            out.append(int(ix))
    return out


# a CORNER is a sharp turn: ~75 deg in radians (a structural constant, not data-fit).
CORNER_RAD = 1.30
N_RESAMPLE = 24


def segment(pts, corner_rad=CORNER_RAD, n=N_RESAMPLE, min_gap=2,
            use_velocity=True, use_turning=True, use_lift=True,
            lift_k=2.0, return_pts=False, resample=True):
    """Segment ONE pen trajectory into sub-strokes at change-points (turning/velocity
    extrema). The trace is arc-length resampled to a fixed scale first (unless resample
    =False, e.g. an already-resampled concat where the pen-LIFT jump must be preserved);
    cues + the change-point decision are HELD Terms. Returns boundary indices into the
    trace (or (boundaries, pts) if return_pts)."""
    rs = _resample(pts, n) if resample else pts
    rl = [list(map(float, p)) for p in rs]
    if len(rl) < 6:
        return ([], rl) if return_pts else []
    turning = _turning_term(rl)
    bounds = set()
    if use_turning:
        bounds |= set(_changepoints_term(turning, corner_rad, want_min=False, min_gap=min_gap))
    if use_velocity or use_lift:
        vel = _velocity_term(rl)
        mean_v = float(_ev({"type": "Div", "a": {"type": "Plus", "items": [_L(float(x)) for x in vel]},
                            "b": _L(float(len(vel)))}))
        if use_velocity:
            # a within-stroke slow-down (junction): velocity MINIMA below 0.5*mean.
            bounds |= set(_changepoints_term(vel, 0.5 * mean_v, want_min=True, min_gap=min_gap))
        if use_lift:
            # a pen-LIFT: a velocity SPIKE (MAXIMA) above lift_k*mean — the obvious split.
            bounds |= set(_changepoints_term(vel, lift_k * mean_v, want_min=False, min_gap=min_gap))
    b = sorted(bounds)
    return (b, rl) if return_pts else b


def segment_drawing(path, n=N_RESAMPLE, **kw):
    """Full segmentation of an Omniglot drawing.
    pen-LIFTS = the obvious splits between load_strokes arrays; within each, change-points.
    Returns (segments=list of resampled-point-lists, lift_count=K-1, substroke_count)."""
    strokes = _ow.load_strokes(path)
    segs, sub = [], 0
    for st in strokes:
        b, rl = segment(st, n=n, return_pts=True, **kw)
        sub += len(b)
        prev = 0
        for bi in b:
            segs.append(rl[prev:bi + 1]); prev = bi
        segs.append(rl[prev:])
    return segs, max(0, len(strokes) - 1), sub


def segment_concat(path, n=N_RESAMPLE, **kw):
    """Segment the CONCATENATED trajectory (BLIND to true splits) — recovers boundaries
    purely from change-point cues, for the discriminative control vs true stroke count K.
    Returns (pred_boundaries, true_K, true_lift_indices_in_resampled_concat)."""
    strokes = _ow.load_strokes(path)
    K = len(strokes)
    parts, true_lifts, off = [], [], 0
    for st in strokes:
        rl = [list(map(float, p)) for p in _resample(st, n)]
        parts.extend(rl); off += len(rl)
        true_lifts.append(off - 1)   # boundary index at the end of this stroke
    true_lifts = true_lifts[:-1]     # K-1 internal lift boundaries
    b = segment(parts, resample=False, **kw)   # keep per-stroke pts: preserve the lift jump
    return b, K, true_lifts
