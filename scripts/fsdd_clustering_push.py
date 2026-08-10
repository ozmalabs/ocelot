"""Drive the agent's #1 frontier (cross-speaker clustering) further. We removed the
SPEAKER (between-speaker scatter, +7.4%). Hypothesis: the whitened-EM that NULLED on raw
features (clusters speaker-contaminated, ce9a449d) should now WORK ON THE NUISANCE-
CONDITIONED base — with the speaker gone, the pseudo-labels are clean enough that the
within-CLUSTER scatter is genuinely within-WORD, so whitening it sharpens the words.

Stages, all on the agent's native matrix primitives (BetweenScatter, WithinScatter,
WhitenMany) + its composed clusterer; LABEL-FREE for the target (speaker observed):
  raw                cluster the cochlear features.
  NC                 whiten by the between-SPEAKER scatter (remove the speaker), cluster.
  NC + whitened-EM   on the NC features, iterate: within-CLUSTER scatter -> whiten ->
                     recluster (the discriminant refinement, now on a clean base).

Run: python scripts/fsdd_clustering_push.py [n_per] [em_iters]
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
from substrate_rs.speech import _audio
from domains.cross_speaker_clustering import cluster
from scripts.speech_analysis_by_synthesis import load_wav, feat, DATA, FN, N_BANDS


def _vec(xs):
    return srs.Vec(items=[srs.Lit(float(v)) for v in xs])


def _mat(M):
    return srs.Vec(items=[_vec(r) for r in M])._json


def purity(assign, truth):
    return sum(Counter([truth[i] for i in range(len(assign)) if assign[i] == c]
                       ).most_common(1)[0][1] for c in set(assign)) / len(truth)


def scatter(s, kind, M, labels):
    Sv = s._inner.evaluate({"type": kind, "a": _mat(M),
                            "b": _vec([float(a) for a in labels])._json}, {})
    return np.array([[float(v) for v in row] for row in Sv])


def whiten_by(s, W, M, ridge):
    d = M.shape[1]
    Wr = W + ridge * (np.trace(W) / d) * np.eye(d)
    out = s._inner.evaluate({"type": "WhitenMany", "a": _mat(Wr), "b": _mat(M)}, {})
    return np.array([[float(v) for v in row] for row in out])


def pur3(M, k, truth):
    return float(np.mean([purity(cluster(M, k, seed=sd), truth) for sd in range(3)]))


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    em_iters = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    M, word, spk, sid = [], [], [], {}
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            M.append(feat(s, bank, load_wav(os.path.join(DATA, fn))[0], 8000)
                     .flatten().astype(np.float64))
            word.append(int(m.group(1)))
            spk.append(sid.setdefault(m.group(2), len(sid)))
    M = np.asarray(M); k = len(set(word))
    print("=" * 70)
    print(f"DRIVE CLUSTERING — {len(M)} tokens, {len(sid)} speakers, k={k}")
    print("=" * 70)
    print(f"  raw                          : {pur3(M, k, word):.3f}")

    # NC: remove the observed speaker (between-speaker scatter), label-free.
    Sb = scatter(s, "BetweenScatter", M, spk)
    Mnc = whiten_by(s, Sb, M, 0.2)
    nc = pur3(Mnc, k, word)
    print(f"  nuisance-conditioned (NC)    : {nc:.3f}")

    # NC + whitened-EM: within-CLUSTER refinement on the clean (speaker-removed) base.
    assign = cluster(Mnc, k, seed=0)
    Mw = Mnc
    best = nc
    for it in range(em_iters):
        Wc = scatter(s, "WithinScatter", Mw, assign)   # within-cluster (now within-word)
        Mw = whiten_by(s, Wc, Mnc, 0.0)                # whiten the NC features by it
        assign = cluster(Mw, k, seed=0)
        p = pur3(Mw, k, word)
        best = max(best, p)
        print(f"    NC + whitened-EM iter {it+1}    : {p:.3f}")
    print("-" * 70)
    print(f"  best                         : {best:.3f}   (raw +{best - pur3(M,k,word):.3f})")
    print("=" * 70)


if __name__ == "__main__":
    main()
