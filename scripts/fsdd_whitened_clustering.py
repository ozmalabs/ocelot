"""The agent's #1 frontier (cross-speaker CLUSTERING, payoff 83) meets the matrix
primitives it just authored. The clustering mechanism works but its invariance is
bounded by the front-end (cross_speaker_clustering_probe: CMVN doesn't beat raw). The
fix, UNSUPERVISED: whitened-EM — cluster, estimate the within-CLUSTER scatter from the
PSEUDO-labels (native WithinScatter), whiten it out (native Whiten), re-cluster; repeat.
The same discriminant whitening the agent derived + wired for the SUPERVISED case, now
driven by its own cluster assignments — no true labels anywhere in the loop.

LABEL-FREE: true digit labels are read ONLY to score cluster purity at the end. Uses the
agent's composed clusterer (domains.cross_speaker_clustering.cluster) + its two native
primitives (WithinScatter, Whiten). Compares raw clustering vs whitened-EM on the SAME
features — the delta is the primitives' contribution to the picked frontier.

Run: python scripts/fsdd_whitened_clustering.py [n_per] [em_iters]
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


def purity(assign, truth):
    tot = len(truth)
    hit = 0
    for c in set(assign):
        labs = [truth[i] for i in range(len(assign)) if assign[i] == c]
        if labs:
            hit += Counter(labs).most_common(1)[0][1]
    return hit / tot


def native_within_scatter(s, M, assign):
    data = srs.Vec(items=[_vec(r) for r in M])._json
    labs = _vec([float(a) for a in assign])._json
    Wval = s._inner.evaluate({"type": "WithinScatter", "a": data, "b": labs}, {})
    return srs.Vec(items=[_vec([float(v) for v in row]) for row in Wval])._json


def native_whiten_all(s, Wmat, M):
    out = np.empty_like(M)
    for i, x in enumerate(M):
        r = s._inner.evaluate({"type": "Whiten", "a": Wmat, "b": _vec(x)._json}, {})
        out[i] = [float(v) for v in r]
    return out


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    em_iters = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    M, truth = [], []
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            M.append(feat(s, bank, load_wav(os.path.join(DATA, fn))[0], 8000)
                     .flatten().astype(np.float64))
            truth.append(int(m.group(1)))
    M = np.asarray(M); k = len(set(truth))
    print("=" * 72)
    print(f"WHITENED-EM cross-speaker clustering (the agent's #1 frontier + its primitives)")
    print(f"  {len(M)} tokens pooled LABEL-FREE, k={k}, EM iters={em_iters}")
    print("=" * 72)

    floor = purity([np.random.RandomState(s_).randint(0, k)
                    for s_ in range(len(M))], truth)
    base = np.mean([purity(cluster(M, k, seed=sd), truth) for sd in range(3)])
    print(f"  random floor                : {floor:.3f}")
    print(f"  raw clustering (agent k-means): {base:.3f}")

    # WHITENED-EM: pseudo-labels -> native within-cluster scatter -> native whiten -> recluster
    assign = cluster(M, k, seed=0)
    Mw = M
    for it in range(em_iters):
        W = native_within_scatter(s, Mw, assign)   # within-CLUSTER scatter (pseudo-labels)
        Mw = native_whiten_all(s, W, M)            # whiten the ORIGINAL features by it
        assign = cluster(Mw, k, seed=0)
        print(f"    EM iter {it+1}: purity {purity(assign, truth):.3f}")
    final = np.mean([purity(cluster(Mw, k, seed=sd), truth) for sd in range(3)])
    print(f"\n  whitened-EM clustering       : {final:.3f}   "
          f"(delta {final-base:+.3f} vs raw)")
    print(f"\n  the agent's native whitening primitives {'HELP' if final > base else 'do NOT help'} "
          f"its picked clustering frontier, UNSUPERVISED.")
    print("=" * 72)


if __name__ == "__main__":
    main()
