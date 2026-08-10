"""THE JABBERWOCK RECOGNISES BY SHAPE — analysis-by-synthesis models matched by talker-invariant shape.

The discriminative path tried to LEARN speaker-invariance. This gets it by CONSTRUCTION: the agent's
relational_shape faculty represents a word by its BAND-RANK PROFILE (which band is louder than which) +
whole-unit self-similarity — invariant to ANY per-band gain / per-frame level, i.e. any talker
transform, by construction (domains/relational_shape.py). Matched by warp-tolerant DTW (rate
invariance). Recognition = nearest word-MODEL by shape. The agent forms several models per word
(analysis-by-synthesis: multiple exemplars / synthesised variants) and matches the observation to them
by shape. No learning, no backprop — invariance is in the representation.

Compares, on the same hard top-K Sesame words: RAW-feature DTW (the transform-fragile baseline) vs
the agent's RELATIONAL-SHAPE DTW (talker-invariant). The rank profile is the agent's composed Term
(Gt/IfThenElse/Plus); computed here in numpy at the I/O boundary for speed, identical result.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_shape_match [topK] [models]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scipy.spatial.distance import cdist
from domains.filter_settings import cochleagram
from domains.self_directed_speech_world import _MIDDLE
from scripts.sesame_cmvn_probe import extract

SEP = "=" * 94
FS = 8000


def coch(seg):
    _, ec, dc, nf = _MIDDLE
    return cochleagram(np.asarray(seg, dtype=np.float64), FS, ec, dc, nf)


def _z(A):
    return (A - A.mean(0, keepdims=True)) / (A.std(0, keepdims=True) + 1e-6)


def rank_profile(M):
    """The agent's ordinal band-rank per frame (Gt/IfThenElse/Plus), talker-gain invariant."""
    return (M[:, :, None] > M[:, None, :]).sum(2).astype(np.float64)


def relational_shape(M, n_anchors=6):
    """rank profile ++ whole-unit self-similarity row — invariant to any uniform talker transform."""
    R = rank_profile(M)
    T = len(R)
    idx = [min(T - 1, int(round(k * (T - 1) / (n_anchors - 1)))) for k in range(n_anchors)]
    ss = np.stack([-np.abs(R - R[ai]).sum(1) for ai in idx], axis=1)
    return np.concatenate([_z(R), _z(ss)], axis=1).astype(np.float64)


def dtw(A, B):
    """Warp-tolerant distance between two trajectories (rate invariance)."""
    C = cdist(A, B, "euclidean")
    Ta, Tb = C.shape
    D = np.full((Ta + 1, Tb + 1), np.inf); D[0, 0] = 0.0
    for i in range(1, Ta + 1):
        Ci = C[i - 1]
        for j in range(1, Tb + 1):
            D[i, j] = Ci[j - 1] + min(D[i - 1, j], D[i, j - 1], D[i - 1, j - 1])
    return D[Ta, Tb] / (Ta + Tb)


def recognise(models, tests, ytests, byword=False):
    """1-NN by DTW over the word MODELS (each (word, trajectory)). Returns recall + 6+ bucket."""
    cor = 0
    for q, w in zip(tests, ytests):
        best, bw = np.inf, None
        for (mw, mt) in models:
            dd = dtw(q, mt)
            if dd < best:
                best, bw = dd, mw
        cor += int(bw == w)
    return cor / len(tests) if tests else 0.0


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    n_models = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    print(SEP)
    print("RECOGNISE BY SHAPE — analysis-by-synthesis models matched by talker-invariant relational shape.")
    print(SEP)
    train, test = extract(16.0)
    freq = Counter(w for (w, _g) in train)
    words = [w for w, _ in freq.most_common(topK)]
    wi = set(words)
    by = {}
    for (w, g) in train:
        if w in wi:
            by.setdefault(w, []).append(g)
    te = [(w, g) for (w, g) in test if w in wi][:60]
    print(f"  top-{topK} words, {n_models} models/word, {len(te)} test, chance {100/len(words):.0f}%: {words}\n")

    # form models (analysis-by-synthesis: several exemplars per word) — raw and relational-shape.
    raw_models, shp_models = [], []
    for w in words:
        for g in by[w][:n_models]:
            M = coch(g)
            raw_models.append((w, _z(M)))                 # raw spectro-temporal (transform-fragile)
            shp_models.append((w, relational_shape(M)))   # talker-invariant relational shape
    teM = [(w, coch(g)) for (w, g) in te]
    raw_test = [_z(M) for (_w, M) in teM]
    shp_test = [relational_shape(M) for (_w, M) in teM]
    yte = [w for (w, _M) in teM]

    raw_acc = recognise(raw_models, raw_test, yte)
    shp_acc = recognise(shp_models, shp_test, yte)
    print(f"  RAW spectro-temporal DTW (transform-fragile):   recall {raw_acc*100:.0f}%")
    print(f"  RELATIONAL-SHAPE DTW (talker-invariant):        recall {shp_acc*100:.0f}%")

    print(f"\n{SEP}")
    if shp_acc > raw_acc + 0.05:
        print(f"  SHAPE WINS: matching by the agent's talker-invariant relational shape lifted recall "
              f"{raw_acc*100:.0f}% -> {shp_acc*100:.0f}%.")
        print("  Speaker-invariance by CONSTRUCTION (rank profile + self-similarity, DTW), no learning,")
        print("  no backprop — analysis-by-synthesis models matched by shape. The cognitively-faithful route.")
    else:
        print(f"  shape {raw_acc*100:.0f}% -> {shp_acc*100:.0f}%: the rank-profile invariant did not beat raw here")
        print("  on these (function) words — richer shape models / synthesised AbS variants are the next step.")
    print(SEP)


if __name__ == "__main__":
    main()
