"""stroke_library — an EARNED stroke-identity library + identity-parse, the attempt to build a STABLE
identity-bearing sub-part PARSE for handwriting (to unblock per-stroke AbS, bfe3f4a6). graph-native,
earn-not-borrow, donkey=0.

THE GOAL: the per-stroke null (bfe3f4a6) was parse-bound — the segmenter is unstable (~40% of chars
have matching stroke COUNTS across drawers), so correspondence matches mismatched strokes. Induce a
LIBRARY of stroke-identities from the BACKGROUND set (cluster sub-stroke shape descriptors) so a char
parses into STABLE identities (an identity histogram, count-stable by construction).

HONEST (the finding this enables measuring): three parse approaches — induced identity-histogram,
fixed-K count-stable parts, and even the count-STABLE subset — were measured against coarse whole-char
AbS. numpy adapter-only (descriptors + k-means); no learned net / no LLM in recognition. The library
is induced from held background data (earned), not borrowed.

Superseded (2026-07-02) by the graph-resident stroke codebook + segmentation-by-recognition
decode for handwriting: domains/stroke_codebook.py + domains/ink_decode.py (design
scratchpad/HANDWRITING_DESIGN.md) — boundaries EMERGE from the decode instead of a separate
stable-count parse. No behavior change here; this module is unmodified otherwise.
"""
from __future__ import annotations
import numpy as _np                 # ADAPTER: descriptors + k-means + histograms
import domains.omniglot_world as _ow
import domains.per_stroke_abs as _ps


def stroke_descriptor(stroke_ps, dim=15):
    """A stroke's IDENTITY descriptor: the rotation-relative turn profile (fixed-dim shape signature).
    Style-factored (relative turns); the basis for clustering sub-strokes into identities."""
    a = _np.asarray(stroke_ps)
    if len(a) < 3:
        return None
    dv = _np.diff(a, axis=0)
    ang = _np.arctan2(dv[:, 1], dv[:, 0])
    t = _np.diff(_np.unwrap(ang))
    o = _np.zeros(dim)
    o[:min(dim, len(t))] = t[:dim]
    return o


def induce_library(n_alphabets=25, per_alpha=10, K=60, N=16, seed=0):
    """INDUCE a stroke-identity LIBRARY from the BACKGROUND set: extract all sub-stroke descriptors,
    cluster (k-means) into K identities. The held library of stroke-identities (earned from background).
    Returns the K cluster centroids."""
    subs = []
    for al in _ow.alphabets("background")[:n_alphabets]:
        for c in _ow.characters(al, split="background")[:per_alpha]:
            for s in _ps.stroke_point_sets(_ow.drawings(c)[0], N=N):
                d = stroke_descriptor(s)
                if d is not None:
                    subs.append(d)
    subs = _np.array(subs)
    rng = _np.random.RandomState(seed)
    cent = subs[rng.choice(len(subs), min(K, len(subs)), replace=False)].copy()
    for _ in range(15):
        lab = ((subs[:, None] - cent[None]) ** 2).sum(2).argmin(1)
        for k in range(len(cent)):
            m = subs[lab == k]
            if len(m):
                cent[k] = m.mean(0)
    return cent


def identity_histogram(path, library, N=16):
    """Parse a char into its stroke-IDENTITY histogram (assign each segment to its nearest library
    identity). Count-stable by construction (a fixed-K vector). The 'stable identity-bearing parse'."""
    K = len(library)
    h = _np.zeros(K)
    for s in _ps.stroke_point_sets(path, N=N):
        d = stroke_descriptor(s)
        if d is not None:
            h[int(((library - d) ** 2).sum(1).argmin())] += 1
    n = _np.linalg.norm(h)
    return h / n if n > 0 else h


def fixed_parts(path, K=4, N=16):
    """A COUNT-STABLE parse by construction: split the whole normalized trajectory into K arc-length
    sub-parts (same K for every char), each a point-set keeping geometry. Stable count, no clustering."""
    strokes = _ow.load_strokes(path)
    pts = []
    for st in strokes:
        pts.extend([list(map(float, p)) for p in st])
    a = _np.asarray(pts, float)
    if len(a) < K * 3:
        return None
    a = a - a.mean(0); a = a / (_np.abs(a).max() + 1e-9)
    d = _np.sqrt((_np.diff(a, axis=0) ** 2).sum(1))
    cum = _np.concatenate([[0.0], _np.cumsum(d)])
    if cum[-1] == 0:
        return None
    parts = []
    for k in range(K):
        u = _np.linspace(cum[-1] * k / K, cum[-1] * (k + 1) / K, N)
        parts.append(_np.stack([_np.interp(u, cum, a[:, 0]), _np.interp(u, cum, a[:, 1])], 1).tolist())
    return parts
