"""Drive the agent's #1 frontier: formant-ratio / VTL speaker normalization. The held op
_vtl_formant_allpole extracts sharp LPC formants and normalises F_i - mean(F1..F3) in
log-Hz — the vocal-tract-length shift cancels by construction (= formant RATIOS). VTL is
a log-FREQUENCY shift; the shape front-end (clustering+segmentation winner) removed log-
AMPLITUDE level, so formant-ratio is COMPLEMENTARY. Test: does explicit formant-ratio
normalization add cross-speaker invariance on top of / vs the shape front-end?

A/B on FSDD cross-speaker clustering (purity, label-free; +NC = native between-speaker
whitening): shape vs VTL-formant-ratio vs both.

Run: python scripts/fsdd_formant_ratio_norm.py [n_per]
"""
from __future__ import annotations
import os
import sys
from collections import Counter

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), os.pardir, "runners/dsl/python"))

import substrate_rs as srs
from substrate_rs import Substrate
from domains.agent_frontend import _vtl_formant_allpole
from domains.cross_speaker_clustering import cluster
from scripts.frontend_improve_xspeaker import band_matrix
from scripts.speech_analysis_by_synthesis import load_wav, DATA, FN


def shape_feat(x):
    M = band_matrix(x, 8000, n_bands=32, n_frames=12)
    L = np.log(M + 1e-6)
    return (L - L.mean(axis=1, keepdims=True)).flatten()


def zscore(F):
    return (F - F.mean(0)) / (F.std(0) + 1e-9)


def purity(a, t):
    return sum(Counter([t[i] for i in range(len(a)) if a[i] == c]).most_common(1)[0][1]
               for c in set(a)) / len(t)


def pur3(F, k, t):
    return float(np.mean([purity(cluster(F, k, seed=sd), t) for sd in range(3)]))


def _mat(s, A):
    return srs.Vec(items=[srs.Vec(items=[srs.Lit(float(v)) for v in r]) for r in A])._json


def nc(s, F, spk):
    d = F.shape[1]
    Sb = np.array([[float(v) for v in r] for r in s._inner.evaluate(
        {"type": "BetweenScatter", "a": _mat(s, F),
         "b": srs.Vec(items=[srs.Lit(float(a)) for a in spk])._json}, {})])
    Wr = Sb + 0.2 * (np.trace(Sb) / d) * np.eye(d)
    return np.array([[float(v) for v in r] for r in s._inner.evaluate(
        {"type": "WhitenMany", "a": _mat(s, Wr), "b": _mat(s, F)}, {})])


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    s = Substrate()
    shp, fmt, word, spk, sid = [], [], [], [], {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            x = load_wav(os.path.join(DATA, fn))[0]
            shp.append(shape_feat(x))
            fmt.append(np.asarray(_vtl_formant_allpole(x, 8000, None, {}), np.float64))
            word.append(int(m.group(1))); spk.append(sid.setdefault(m.group(2), len(sid)))
    SH = zscore(np.asarray(shp)); FM = zscore(np.asarray(fmt))
    BOTH = np.hstack([SH, FM])
    k = len(set(word))
    print("=" * 64)
    print(f"FORMANT-RATIO / VTL NORMALIZATION — FSDD cross-speaker clustering")
    print(f"  {len(word)} utts, k={k}, label-free; +NC = between-speaker whitening")
    print("=" * 64)
    print(f"  {'representation':28s} {'raw':>7s} {'+NC':>7s}")
    print("-" * 64)
    for name, F in [("shape front-end (level-norm)", SH),
                    ("VTL formant-ratio (freq-norm)", FM),
                    ("shape + formant-ratio", BOTH)]:
        print(f"  {name:28s} {pur3(F,k,word):7.3f} {pur3(nc(s,F,spk),k,word):7.3f}")
    print("=" * 64)


if __name__ == "__main__":
    main()
