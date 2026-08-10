"""KEY<->SHAPE RELAXATION, RICHER KEY x CONTENT WORDS — where the consideration said the payoff lives.

The minimal run (VTL-only key, function words) confirmed the FORM: shape-anchored relaxation beats
single-pass, discarding the shape falls into wrong attractors. The consideration said the real lift
needs (a) CONTENT words (distinctive shape, detail for key-recovery to reward) and (b) a RICHER KEY
(warp + tilt + channel, not one shift). This runs exactly that, keeping the winning shape-anchored loop:

  key = (VTL band-shift, spectral tilt) — two structured residuals the rank-profile invariant does not
        fully remove; the shape stays the basin anchor, the key recovers what the shape discarded.
  loop: seed by shape (bootstrap) -> M-step fit (shift,tilt) to the hypothesised exemplar -> E-step
        re-recognise scoring z(shape) + z(key-normalised raw) -> iterate to a fixed point.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_key_shape_content [topK]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_shape_fair import coch, _z, relational_shape
from scripts.jabberwock_shape_pc_paired import content_words
from scripts.jabberwock_key_shape_relaxation import dtw

SHIFTS = np.arange(-5.0, 5.01, 1.25)        # VTL key candidates (log-freq band shift)
TILTS = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])   # spectral-tilt key candidates (units of sigma)


def coch_mc(seg):
    M = coch(seg)
    return M - M.mean()


def _z1(v):
    v = np.asarray(v); return (v - v.mean()) / (v.std() + 1e-9)


def warp2(M, s, t, ramp):
    """Apply key (VTL shift s, spectral tilt t): shift bands by s, add t*ramp across the band axis."""
    b = M.shape[1]
    src = np.arange(b); tgt = src - s
    tramp = t * ramp
    out = np.empty_like(M)
    for ti in range(M.shape[0]):
        out[ti] = np.interp(tgt, src, M[ti], left=M[ti, 0], right=M[ti, -1]) + tramp
    return out


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 16
    print("=" * 94)
    print("KEY<->SHAPE RELAXATION — richer key (warp+tilt) x CONTENT words, shape kept as basin anchor.")
    print("=" * 94)
    train, test = multi_extract()
    words = content_words(train, topK, min_ex=10)
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
          f"{sum(len(v) for v in by.values())} train / {len(te)} held-out): {words}\n")
    if len(words) < 5 or len(te) < 20:
        print("  too few content words/exemplars."); return

    # exemplar models + the band ramp scaled to the data's spectral spread.
    EX = [(w, coch_mc(g), relational_shape(coch(g))) for w in words for g in by[w][:12]]
    EXc = [e[1] for e in EX]; EXs = [e[2] for e in EX]; EXw = [e[0] for e in EX]
    b = EXc[0].shape[1]
    sigma = float(np.mean([c.std() for c in EXc]))
    ramp = sigma * (np.arange(b) - (b - 1) / 2.0) / (b / 2.0)   # +/- ~1 sigma across the band axis

    def nearest_shape(S):
        j = int(np.argmin([dtw(S, T) for T in EXs])); return EXw[j], EXc[j]

    def nearest_raw(Mw):
        j = int(np.argmin([dtw(Mw, T) for T in EXc])); return EXw[j], EXc[j]

    def fit_key(M, T):
        best, bk = np.inf, (0.0, 0.0)
        for s in SHIFTS:
            for t in TILTS:
                d = dtw(warp2(M, s, t, ramp), T)
                if d < best:
                    best, bk = d, (s, t)
        return bk

    def loop_anchored(M, S, seed_w, seed_T, iters=6):
        zshape = _z1([dtw(S, Ts) for Ts in EXs])
        m, T = seed_w, seed_T
        for _ in range(iters):
            s, t = fit_key(M, T)
            Mw = warp2(M, s, t, ramp)
            j = int(np.argmin(zshape + _z1([dtw(Mw, Tc) for Tc in EXc])))
            if EXw[j] == m:
                break
            m, T = EXw[j], EXc[j]
        return m

    n = len(te)
    raw1 = shp1 = anc = 0
    for (w, g) in te:
        M = coch_mc(g); S = relational_shape(coch(g))
        raw1 += int(nearest_raw(M)[0] == w)
        sseed, sT = nearest_shape(S)
        shp1 += int(sseed == w)
        anc += int(loop_anchored(M, S, sseed, sT) == w)
    print(f"  {'raw single-pass (k=0)':<42} {raw1/n*100:>5.0f}%")
    print(f"  {'shape single-pass (bootstrap)':<42} {shp1/n*100:>5.0f}%")
    print(f"  {'LOOP, richer key (warp+tilt), shape-anchored':<42} {anc/n*100:>5.0f}%")

    print("\n" + "=" * 94)
    rp, sp, ap = raw1 / n, shp1 / n, anc / n
    if ap > sp + 0.03:
        print(f"  PAYOFF: on content words with a richer key, the key<->shape relaxation {ap*100:.0f}% beats the")
        print(f"  bootstrap {sp*100:.0f}% and raw {rp*100:.0f}% — key CONTRACTION recovers the detail the invariant")
        print(f"  discarded, exactly where the consideration said it would. Co-estimating message and key wins.")
    elif ap >= sp:
        print(f"  loop {ap*100:.0f}% >= bootstrap {sp*100:.0f}% (raw {rp*100:.0f}%): the richer key holds the gain "
              f"the form predicts, but content-word data is thin ({len(te)} test) — directional, not decisive.")
    else:
        print(f"  loop {ap*100:.0f}% < bootstrap {sp*100:.0f}%: the richer key over-searched into wrong attractors "
              f"on thin data — the basin/over-fit risk the consideration warned of, now from the key side.")
    print("=" * 94)


if __name__ == "__main__":
    main()
