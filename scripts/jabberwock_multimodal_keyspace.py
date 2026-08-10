"""MULTIMODAL KEYSPACE PRIOR — cluster speakers, navigate from the NEAREST one (its local prior).

The single global non-linear prior HURT (it averaged puppet + documentary into a meaningless centre).
The keyspace is multimodal: distinct speaker populations. The fix is exactly "navigate from the nearest
known speaker if not too far": cluster the training voices (by their speaker-dominant mean spectrum),
learn a LOCAL key prior per cluster, and at recognition find the nearest cluster and constrain the
non-linear key navigation to ITS local prior. Distant clusters are unreachable; the right local prior
is a tight, meaningful basin. Compared: shape bootstrap, GLOBAL-Gaussian prior, MULTIMODAL (local) prior.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_multimodal_keyspace [topK] [nclust]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_shape_fair import coch, relational_shape
from scripts.jabberwock_shape_pc_paired import content_words
from scripts.jabberwock_key_shape_relaxation import dtw
from scripts.jabberwock_key_channel_reverb import coch_mc, shift_bands, reverb_smear, SG, C1, C2, RV

GRID = {0: SG, 1: C1, 2: C2, 3: RV}
KCAND = 6


def _zc(d, ks):
    v = np.array([d[k] for k in ks]); m, s = v.mean(), v.std() + 1e-9
    return {k: (d[k] - m) / s for k in ks}


def kmeans(X, K, iters=15, seed=0):
    rng = np.random.default_rng(seed)
    C = X[rng.choice(len(X), K, replace=False)].copy()
    for _ in range(iters):
        a = np.argmin(((X[:, None, :] - C[None]) ** 2).sum(2), axis=1)
        for c in range(K):
            if (a == c).any():
                C[c] = X[a == c].mean(0)
    return C, np.argmin(((X[:, None, :] - C[None]) ** 2).sum(2), axis=1)


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    nclust = int(sys.argv[2]) if len(sys.argv) > 2 else 10
    print("=" * 98)
    print("MULTIMODAL KEYSPACE PRIOR — cluster speakers, navigate from the nearest one's local prior.")
    print("=" * 98)
    train, test = multi_extract()
    words = content_words(train, topK, min_ex=12)
    wi = set(words)
    allex = {}
    for (w, g) in train + test:
        if w in wi:
            allex.setdefault(w, []).append(g)
    by, te = {}, []
    for w in words:
        ex = allex[w]; nho = max(2, len(ex) // 5)
        by[w] = ex[:-nho]; te += [(w, g) for g in ex[-nho:]]
    print(f"  top-{len(words)} CONTENT words (chance {100/max(len(words),1):.0f}%, "
          f"{sum(len(v) for v in by.values())} train / {len(te)} held-out), {nclust} speaker clusters\n")
    if len(words) < 6 or len(te) < 25:
        print("  too few."); return

    Tc = {w: np.mean([coch_mc(g) for g in by[w][:25]], axis=0) for w in words}
    Ts = {w: np.mean([relational_shape(coch(g)) for g in by[w][:25]], axis=0) for w in words}
    b = next(iter(Tc.values())).shape[1]
    sigma = float(np.mean([t.std() for t in Tc.values()]))
    r1 = (np.arange(b) - (b - 1) / 2.0) / (b / 2.0)
    ramp1 = sigma * r1; ramp2 = sigma * (r1 ** 2 - (r1 ** 2).mean())

    def synth(T, k):
        return reverb_smear(shift_bands(T, k[0]) + k[1] * ramp1 + k[2] * ramp2, k[3])

    def fit_key(obs, T, mu, inv, lam):
        k = list(mu)
        def cost(kk):
            d = dtw(synth(T, kk), obs)
            if lam > 0:
                d += lam * sum(inv[i] * (kk[i] - mu[i]) ** 2 for i in range(4))
            return d
        for _ in range(2):
            for i in range(4):
                k[i] = min(GRID[i], key=lambda v: cost(k[:i] + [v] + k[i + 1:]))
        return cost(k), k

    # learn: per training utterance, its speaker-dominant mean spectrum + its fitted non-linear key.
    print("  learning keys + speaker spectra for the training set...", flush=True)
    spec, keys = [], []
    flat = ([0.0] * 4, [1e-3] * 4)
    for w in words:
        for g in by[w]:
            spec.append(coch(g).mean(0))                       # speaker/channel-dominant profile
            keys.append(fit_key(coch_mc(g), Tc[w], flat[0], flat[1], 0.0)[1])
    spec = np.array(spec); keys = np.array(keys)
    sm, ss = spec.mean(0), spec.std(0) + 1e-6
    specn = (spec - sm) / ss

    # GLOBAL prior
    g_mu = keys.mean(0); g_inv = 1.0 / (keys.var(0) + 1e-6)
    # MULTIMODAL: cluster speakers, local prior per cluster
    C, lab = kmeans(specn, nclust)
    loc_mu = np.stack([keys[lab == c].mean(0) if (lab == c).any() else g_mu for c in range(nclust)])
    loc_inv = np.stack([1.0 / (keys[lab == c].var(0) + 1e-6) if (lab == c).sum() > 2 else g_inv
                        for c in range(nclust)])
    print(f"  global prior std {np.round(np.sqrt(keys.var(0)), 2)}; "
          f"per-cluster prior std (mean) {np.round(np.sqrt(1/loc_inv).mean(0), 2)} (tighter = multimodal)\n")

    LAM = 0.5

    def rec_shape(S):
        return min(words, key=lambda w: dtw(S, Ts[w]))

    def rec_key(M, S, mu, inv):
        sh = {w: dtw(S, Ts[w]) for w in words}
        cands = sorted(words, key=lambda w: sh[w])[:KCAND]
        res = {w: fit_key(M, Tc[w], mu, inv, LAM)[0] for w in cands}
        zsh = _zc(sh, cands); zr = _zc(res, cands)
        return min(cands, key=lambda w: zsh[w] + zr[w])

    n = len(te)
    shp = glob = mm = 0
    for (w, g) in te:
        M = coch_mc(g); S = relational_shape(coch(g))
        shp += int(rec_shape(S) == w)
        glob += int(rec_key(M, S, g_mu, g_inv) == w)
        c = int(np.argmin(((C - (coch(g).mean(0) - sm) / ss) ** 2).sum(1)))   # nearest speaker cluster
        mm += int(rec_key(M, S, loc_mu[c], loc_inv[c]) == w)
    print(f"  {'shape single-pass (bootstrap)':<48} {shp/n*100:>5.0f}%")
    print(f"  {'GLOBAL Gaussian keyspace prior':<48} {glob/n*100:>5.0f}%")
    print(f"  {'MULTIMODAL (nearest-cluster) keyspace prior':<48} {mm/n*100:>5.0f}%")

    print("\n" + "=" * 98)
    sp, gp, mp = shp / n, glob / n, mm / n
    if mp > max(sp, gp) + 0.02:
        print(f"  IT WORKS: navigating from the NEAREST speaker cluster's local prior lifts recognition to {mp*100:.0f}%")
        print(f"  — above the bootstrap {sp*100:.0f}% and the global prior {gp*100:.0f}% that averaged the speakers away.")
        print("  The keyspace is multimodal; navigate from the nearest known voice, as reasoned. The arc closes.")
    elif mp > gp + 0.02:
        print(f"  multimodal {mp*100:.0f}% > global {gp*100:.0f}% (bootstrap {sp*100:.0f}%): local priors DO beat the")
        print("  averaged one — the keyspace is multimodal — but mean templates + 4 key dims still cap it under the")
        print("  invariant. Tighter per-speaker references (exemplars) + more clusters is the same scale lever.")
    else:
        print(f"  multimodal {mp*100:.0f}% vs global {gp*100:.0f}% / bootstrap {sp*100:.0f}%: clustering speakers from")
        print("  mean spectra is too coarse, and the non-linear key on blurry templates caps the gain — the honest")
        print("  endpoint is a learned speaker model at scale (the x-vector the whole arc keeps pointing at).")
    print("=" * 98)


if __name__ == "__main__":
    main()
