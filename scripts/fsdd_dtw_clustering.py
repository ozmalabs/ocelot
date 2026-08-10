"""Drive clustering past the representational bound the agent named (sequence/alignment):
the token is a TIME TRAJECTORY; the same word is the same ordered parts stretched in time,
and flattening into equal bins misaligns the parts. The agent already HOLDS the fix as a
primitive — DtwTo (banded DTW, alignment-invariant trajectory distance). Cluster the
trajectories by DTW (k-medoids on the native DtwTo distance) instead of Euclidean on
flattened bins. LABEL-FREE; labels only score purity.

Run: python scripts/fsdd_dtw_clustering.py [n_per] [n_frames]
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
from scripts.speech_analysis_by_synthesis import load_wav, DATA, FN, N_BANDS


def feat_traj(s, bank, samples, fs, n_frames):
    """(n_frames x bands) cochlear TRAJECTORY (held cochlea ops; not flattened)."""
    buf = _audio.audio_from_array(s, samples, sample_rate=fs)
    resps = _audio.a1_responses(s, buf, bank)
    T = np.zeros((n_frames, len(bank)), np.float64)
    for bi, r in enumerate(resps):
        resp = _audio.audio_to_array(s, r).astype(np.float64)
        if resp.ndim > 1:
            resp = resp.mean(axis=1)
        n = len(resp)
        if n == 0:
            continue
        wl = max(1, n // n_frames)
        for w in range(n_frames):
            seg = resp[w * wl:(w + 1) * wl]
            if len(seg):
                T[w, bi] = float(np.sqrt(np.mean(seg ** 2)))
    nrm = np.linalg.norm(T)
    return T / nrm if nrm > 1e-8 else T


def purity(assign, truth):
    return sum(Counter([truth[i] for i in range(len(assign)) if assign[i] == c]
                       ).most_common(1)[0][1] for c in set(assign)) / len(truth)


def kmedoids(D, k, seed, iters=30):
    rng = np.random.RandomState(seed)
    med = list(rng.choice(len(D), k, replace=False))
    for _ in range(iters):
        assign = np.argmin(D[:, med], axis=1)
        newmed = []
        for c in range(k):
            members = np.where(assign == c)[0]
            if len(members) == 0:
                newmed.append(med[c]); continue
            sub = D[np.ix_(members, members)].sum(axis=1)
            newmed.append(int(members[int(sub.argmin())]))
        if newmed == med:
            break
        med = newmed
    return np.argmin(D[:, med], axis=1)


def main():
    n_per = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    n_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    s = Substrate(); _audio.seed_audio_grammar(s)
    bank = _audio.cochlea(s, n_bands=N_BANDS, fs=8000)

    trajs, jsons, truth = [], [], []
    for fn in sorted(os.listdir(DATA)):
        m = FN.match(fn)
        if m and int(m.group(3)) < n_per:
            T = feat_traj(s, bank, load_wav(os.path.join(DATA, fn))[0], 8000, n_frames)
            trajs.append(T); truth.append(int(m.group(1)))
            jsons.append(srs.Vec(items=[srs.Vec(items=[srs.Lit(float(v)) for v in fr])
                                        for fr in T])._json)
    n = len(trajs); k = len(set(truth))
    print("=" * 66)
    print(f"DTW CLUSTERING — {n} tokens, k={k}, {n_frames}-frame trajectories")
    print("=" * 66)

    # Euclidean-on-flattened baseline (the bound the agent named).
    F = np.array([T.flatten() for T in trajs])
    De = np.linalg.norm(F[:, None, :] - F[None, :, :], axis=2)
    eucl = np.mean([purity(kmedoids(De, k, sd), truth) for sd in range(3)])
    print(f"  Euclidean (flattened bins)   : {eucl:.3f}")

    # DTW distance matrix via the held native DtwTo primitive (alignment-invariant).
    D = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = float(s._inner.evaluate({"type": "DtwTo", "a": jsons[i], "b": jsons[j]}, {}))
            D[i, j] = D[j, i] = d
    dtw = np.mean([purity(kmedoids(D, k, sd), truth) for sd in range(3)])
    print(f"  DTW (native DtwTo, aligned)  : {dtw:.3f}   (delta {dtw-eucl:+.3f})")
    print("=" * 66)
    print(f"  alignment-invariant comparison {'HELPS' if dtw > eucl else 'does NOT help'} "
          f"clustering ({dtw-eucl:+.3f}).")
    print("=" * 66)


if __name__ == "__main__":
    main()
