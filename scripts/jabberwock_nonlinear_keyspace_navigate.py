"""NON-LINEAR KEYSPACE PRIOR + NAVIGATION — the whole arc as one algorithm.

The diverse corpus collapsed because the non-linear key-fit (warp+channel+reverb) over-searched into
wrong attractors: the search was UNCONSTRAINED. The fix the arc converges on: LEARN the prior over the
non-linear keys real speakers use, and let it CONSTRAIN the navigation — a MAP key-fit that pays a
Mahalanobis price for leaving the learned keyspace, started from the prior mean and stepped toward the
voice. The prior is the map; AbS passes are the steps; the Mahalanobis price is reachability (a key far
outside the learned distribution is expensive, so distant voices are unreachable unless the prior is
wide). Unifies: air's stamp (the key), the cipher (recover it), contraction (don't need it exact),
keyspace prior (a few coords in a learned distribution), navigation (step there, stay reachable).

  learn:  fit the non-linear key (VTL shift, spectral tilt, curvature, reverb) for every training
          utterance against its word's canonical template; the distribution of fitted keys = the prior.
  recognise: shape shortlists; for each candidate word, MAP-fit its key (DTW + lambda * Mahalanobis to
          the prior), navigating from the prior mean; pick the word whose best reachable key explains
          the observation, anchored by the invariant shape.

Compared: shape bootstrap, UNCONSTRAINED key-fit (lambda=0, the over-searching one), and the
PRIOR-CONSTRAINED navigation, on the diverse 5-show corpus.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_nonlinear_keyspace_navigate [topK]
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


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print("=" * 98)
    print("NON-LINEAR KEYSPACE PRIOR + NAVIGATION — learn the keys speakers use, navigate within reach.")
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
          f"{sum(len(v) for v in by.values())} train / {len(te)} held-out)\n")
    if len(words) < 6 or len(te) < 25:
        print("  too few."); return

    Tc = {w: np.mean([coch_mc(g) for g in by[w][:25]], axis=0) for w in words}   # canonical reference
    Ts = {w: np.mean([relational_shape(coch(g)) for g in by[w][:25]], axis=0) for w in words}
    b = next(iter(Tc.values())).shape[1]
    sigma = float(np.mean([t.std() for t in Tc.values()]))
    r1 = (np.arange(b) - (b - 1) / 2.0) / (b / 2.0)
    ramp1 = sigma * r1; ramp2 = sigma * (r1 ** 2 - (r1 ** 2).mean())

    def synth(T, k):
        return reverb_smear(shift_bands(T, k[0]) + k[1] * ramp1 + k[2] * ramp2, k[3])

    def fit_key(obs, T, mu, inv, lam):
        """Coordinate descent MAP fit: min dtw(synth(T,k),obs) + lam * Mahalanobis(k, prior)."""
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

    # LEARN the non-linear keyspace prior: fit each training utterance's key to its word's canonical.
    print("  learning the keyspace prior (fitting the non-linear key for every training utterance)...",
          flush=True)
    fitted = []
    flat_mu = [0.0, 0.0, 0.0, 0.0]; flat_inv = [1e-3, 1e-3, 1e-3, 1e-3]   # weak start for the fit
    for w in words:
        for g in by[w]:
            _, k = fit_key(coch_mc(g), Tc[w], flat_mu, flat_inv, 0.0)
            fitted.append(k)
    K = np.array(fitted)
    mu = K.mean(0)
    var = K.var(0) + 1e-6
    inv = 1.0 / var
    print(f"  keyspace prior: mean key {np.round(mu, 2)}, per-dim std {np.round(np.sqrt(var), 2)} "
          f"(VTL, tilt, curv, reverb)\n")

    def rec_shape(S):
        return min(words, key=lambda w: dtw(S, Ts[w]))

    def rec_key(M, S, lam):
        sh = {w: dtw(S, Ts[w]) for w in words}
        cands = sorted(words, key=lambda w: sh[w])[:KCAND]
        res = {w: fit_key(M, Tc[w], mu, inv, lam)[0] for w in cands}
        zsh = _zc(sh, cands); zr = _zc(res, cands)
        return min(cands, key=lambda w: zsh[w] + zr[w])

    LAM = float(np.median([dtw(synth(Tc[words[0]], mu), coch_mc(by[words[0]][0]))])) * 0.0 + 0.5
    n = len(te)
    shp = unc = con = 0
    for (w, g) in te:
        M = coch_mc(g); S = relational_shape(coch(g))
        shp += int(rec_shape(S) == w)
        unc += int(rec_key(M, S, 0.0) == w)        # unconstrained key-fit (over-searches)
        con += int(rec_key(M, S, LAM) == w)        # prior-constrained navigation
    print(f"  {'shape single-pass (bootstrap)':<48} {shp/n*100:>5.0f}%")
    print(f"  {'key-fit UNCONSTRAINED (over-searches)':<48} {unc/n*100:>5.0f}%")
    print(f"  {'PRIOR-CONSTRAINED navigation (learned keyspace)':<48} {con/n*100:>5.0f}%")

    print("\n" + "=" * 98)
    sp, up, cp = shp / n, unc / n, con / n
    if cp > max(sp, up) + 0.02:
        print(f"  THE PRIOR FIXES IT: constraining the non-linear key to the learned keyspace lifts recognition")
        print(f"  to {cp*100:.0f}% — above the bootstrap {sp*100:.0f}% and the unconstrained {up*100:.0f}% that over-searched")
        print("  into wrong attractors. The keyspace prior is the map; navigation stays within reach. The arc, closed.")
    elif cp > up + 0.02:
        print(f"  the prior HELPS vs unconstrained ({cp*100:.0f}% > {up*100:.0f}%) — it does curb the over-search — but")
        print(f"  does not clear the bootstrap {sp*100:.0f}%: the learned prior is still too NARROW for this 5-show")
        print("  diversity (documentary + puppet exceed it). A wider prior = more speakers, the scale lever.")
    else:
        print(f"  prior-constrained {cp*100:.0f}% vs bootstrap {sp*100:.0f}% / unconstrained {up*100:.0f}%: on this")
        print("  diversity the diagonal-Gaussian non-linear prior is not enough — the keyspace is wider and more")
        print("  structured than 4 independent dims; the honest frontier is a richer learned keyspace at scale.")
    print("=" * 98)


if __name__ == "__main__":
    main()
