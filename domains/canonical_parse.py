"""canonical_parse — the agent's INFERRED canonical stroke parse (writer-invariant re-segmentation).

The part-nested recogniser underperformed on RAW writer strokes because Omniglot's stroke
segmentation is writer-inconsistent (one writer draws a shape in 1 pen-stroke, another in 2). The
fix the agent's own measurement located is BPL's: don't trust the writer's strokes — infer a
CANONICAL parse, the same way for every writer, so parts become comparable.

The canonical parse is geometric and training-free: re-segment the ink at STRUCTURAL CORNERS (points
of high direction change / curvature maxima). A corner is writer-invariant — a shape drawn in one
pen-stroke and the same shape drawn in two pen-strokes split at the SAME corners, so both yield the
same canonical parts. This mirrors the agent's speech self-segmentation (it cut at sonority valleys
with a threshold it TUNED by outcome); here it cuts at corners with an angle threshold it tunes by
recognition accuracy. Mechanical perception geometry (a world-adapter transform); the THRESHOLD is
the agent's parameter, tuned by its own measured payoff, and the recognition DECISION stays the
graph part-nested Term over these canonical parts.
"""
from __future__ import annotations

import numpy as np

from domains.glyph_motor_world import _resample_arclen, _normalize


def _turning_angles(pts: np.ndarray, win: int) -> np.ndarray:
    """Per-point turning angle in degrees over a +/-win window (0 = straight, 180 = reversal).
    The direction BEFORE (p_i - p_{i-win}) vs AFTER (p_{i+win} - p_i)."""
    n = len(pts)
    ang = np.zeros(n)
    for i in range(win, n - win):
        a = pts[i] - pts[i - win]
        b = pts[i + win] - pts[i]
        na = float(np.hypot(*a)); nb = float(np.hypot(*b))
        if na < 1e-9 or nb < 1e-9:
            continue
        cos = float(np.clip(np.dot(a, b) / (na * nb), -1.0, 1.0))
        ang[i] = np.degrees(np.arccos(cos))
    return ang


def corner_split(pts: np.ndarray, theta_deg: float, *, resample_to: int = 36,
                 win: int = 3, min_sep: int = 4) -> list[np.ndarray]:
    """Split ONE pen-stroke at its internal corners (turning angle >= theta, kept as local maxima
    with a minimum separation). Resampled to a consistent density first so the angle window is
    scale/density invariant. Returns the list of sub-stroke point arrays (>=2 points each)."""
    pts = np.asarray(pts, dtype=float)[:, :2]
    if len(pts) < max(6, 2 * win + 1):
        return [pts] if len(pts) >= 2 else []
    pts = _resample_arclen(pts, resample_to)
    ang = _turning_angles(pts, win)
    cuts = []
    i = win
    while i < len(pts) - win:
        if ang[i] >= theta_deg:
            lo = max(win, i - min_sep); hi = min(len(pts) - win, i + min_sep + 1)
            if ang[i] >= ang[lo:hi].max() - 1e-9:        # local maximum of turning
                cuts.append(i); i += min_sep; continue
        i += 1
    bounds = [0] + cuts + [len(pts) - 1]
    segs = []
    for k in range(len(bounds) - 1):
        seg = pts[bounds[k]:bounds[k + 1] + 1]           # overlap by 1 so the corner is shared
        if len(seg) >= 2:
            segs.append(seg)
    return segs if segs else [pts]


def canonical_parts(strokes, theta_deg: float, *, per_part: int = 12) -> list[np.ndarray]:
    """Re-parse a drawing (its raw writer strokes) into CANONICAL parts: corner-split every writer
    stroke, then JOINTLY normalise (one centroid + RMS over all sub-points, so stroke LAYOUT /
    relations are preserved) and resample each canonical sub-stroke to `per_part` points. The
    writer's pen-lift boundaries AND the internal corners both become part boundaries, so the parse
    no longer depends on how the writer chunked the character."""
    subs: list[np.ndarray] = []
    for st in strokes:
        st = np.asarray(st, dtype=float)
        if st.shape[0] >= 1:
            subs.extend(corner_split(st, theta_deg))
    if not subs:
        return []
    allp = np.concatenate(subs, axis=0)
    c = allp.mean(axis=0, keepdims=True)
    rms = float(np.sqrt(((allp - c) ** 2).sum(axis=1).mean())) or 1.0
    out = []
    for s in subs:
        s = (s - c) / rms
        s = _resample_arclen(s, per_part) if s.shape[0] >= 2 else np.repeat(s, per_part, axis=0)
        out.append(s)
    return out


def _part_turning(p: np.ndarray) -> float:
    """Total absolute turning along a part (radians). A simple part (line / smooth arc) ~ small; a
    part that still contains an un-cut corner ~ large. The 'complexity' of representing it as one part."""
    p = np.asarray(p, dtype=float)
    if p.shape[0] < 3:
        return 0.0
    d = np.diff(p, axis=0)
    ang = np.arctan2(d[:, 1], d[:, 0])
    da = (np.diff(ang) + np.pi) % (2 * np.pi) - np.pi
    return float(np.abs(da).sum())


def infer_parse(strokes, thetas=(40.0, 55.0, 70.0, 85.0), lam: float = 1.2,
                per_part: int = 12) -> list[np.ndarray]:
    """INFER the generative PARSE per character (the generative-program faculty's first piece): rather
    than one global corner-threshold, choose — per character — the parse that best EXPLAINS it under a
    description-length prior, cost = (number of parts) + lam * (mean within-part turning). Few parts is
    cheap, but a part holding an un-cut corner pays in turning; the optimum cuts a corner iff it
    simplifies the parts more than the extra part costs. This is BPL's 'infer the program', minimal
    form: marginalise over parse granularities and keep the most parsimonious explanation. Returns the
    canonical parts at the inferred threshold (writer-invariant per-character parse)."""
    best, best_cost = None, float("inf")
    for th in thetas:
        parts = canonical_parts(strokes, th, per_part=per_part)
        if not parts:
            continue
        comp = sum(_part_turning(p) for p in parts) / max(len(parts), 1)
        cost = len(parts) + lam * comp
        if cost < best_cost:
            best_cost, best = cost, parts
    return best if best is not None else canonical_parts(strokes, 70.0, per_part=per_part)


def whole_from_parts(parts) -> np.ndarray:
    """The whole-figure trajectory rebuilt from canonical parts (concatenated, re-normalised) — the
    holistic cue over the SAME canonical parse, for cue fusion."""
    if not parts:
        return np.zeros((1, 2))
    return _normalize(np.concatenate(parts, axis=0))


__all__ = ["corner_split", "canonical_parts", "infer_parse", "whole_from_parts"]
