"""KEY<->SHAPE RELAXATION, FULL KEY (VTL + CHANNEL + REVERB) x MORE CONTENT — analysis-by-synthesis.

The richer key the consideration named, built GENERATIVELY (the key transforms the clean template to
predict the observation — the natural place for reverb): for a word-hypothesis template T,
  synth(T, key) = reverb_smear( shift_bands(T, s) + channel(c1,c2) , r )
  key = (s = VTL log-freq band shift, c1 = spectral tilt, c2 = spectral curvature, r = reverb decay).
Recognition is analysis-by-synthesis: each candidate word gets its OWN best key (coordinate-descent
fit, min DTW of synth to the observation); pick the word that best explains the observation under its
best key, biased by the talker-invariant SHAPE (the basin anchor). channel = smooth additive offset in
the log-spectral domain (a linear convolutional channel is additive there); reverb = forward temporal
energy smear. No backprop, no learned net — a generative key fit per hypothesis, anchored by the
invariant.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_key_channel_reverb [topK]
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

SG = np.arange(-5.0, 5.01, 1.25)                 # VTL shift
C1 = np.array([-1.5, -0.75, 0.0, 0.75, 1.5])     # spectral tilt (sigma units)
C2 = np.array([-1.0, 0.0, 1.0])                  # spectral curvature (sigma units)
RV = np.array([0.0, 2.0, 4.0, 7.0])              # reverb decay (frames)
KCAND = 6                                        # shape shortlists this many for the key fit


def coch_mc(seg):
    M = coch(seg); return M - M.mean()


def _zc(d, ks):
    v = np.array([d[k] for k in ks]); m, s = v.mean(), v.std() + 1e-9
    return {k: (d[k] - m) / s for k in ks}


def shift_bands(M, s):
    if s == 0:
        return M
    b = M.shape[1]; src = np.arange(b); tgt = src - s
    out = np.empty_like(M)
    for t in range(M.shape[0]):
        out[t] = np.interp(tgt, src, M[t], left=M[t, 0], right=M[t, -1])
    return out


def reverb_smear(M, r):
    if r <= 0:
        return M
    L = min(M.shape[0], int(5 * r) + 1)
    k = np.exp(-np.arange(L) / r); k /= k.sum()
    out = np.empty_like(M)
    for band in range(M.shape[1]):
        out[:, band] = np.convolve(M[:, band], k)[:M.shape[0]]
    return out


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    print("=" * 96)
    print("FULL KEY (VTL + channel + reverb) x more content — analysis-by-synthesis, shape-anchored.")
    print("=" * 96)
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
    print(f"  {len(train)} train / {len(test)} test tokens; top-{len(words)} CONTENT words "
          f"(chance {100/max(len(words),1):.0f}%, {len(te)} held-out): {words}\n")
    if len(words) < 6 or len(te) < 25:
        print("  too few content words/exemplars even now."); return

    # EXEMPLAR templates (clean, each in a known key — not a blurry cross-speaker mean) + the ramps.
    EXc = {w: [coch_mc(g) for g in by[w][:12]] for w in words}
    EXs = {w: [relational_shape(coch(g)) for g in by[w][:12]] for w in words}
    b = EXc[words[0]][0].shape[1]
    sigma = float(np.mean([t.std() for v in EXc.values() for t in v]))
    r1 = (np.arange(b) - (b - 1) / 2.0) / (b / 2.0)
    ramp1 = sigma * r1
    ramp2 = sigma * (r1 ** 2 - (r1 ** 2).mean())

    def synth(T, s, c1, c2, r):
        return reverb_smear(shift_bands(T, s) + c1 * ramp1 + c2 * ramp2, r)

    def fit_key(obs, T, full):
        s = c1 = c2 = r = 0.0
        for _ in range(2):                       # coordinate descent over the key
            s = min(SG, key=lambda v: dtw(synth(T, v, c1, c2, r), obs))
            c1 = min(C1, key=lambda v: dtw(synth(T, s, v, c2, r), obs))
            if full:
                c2 = min(C2, key=lambda v: dtw(synth(T, s, c1, v, r), obs))
                r = min(RV, key=lambda v: dtw(synth(T, s, c1, c2, v), obs))
        return dtw(synth(T, s, c1, c2, r), obs)

    def rec_raw(M):
        return min(words, key=lambda w: min(dtw(M, T) for T in EXc[w]))

    def rec_shape(S):
        return min(words, key=lambda w: min(dtw(S, es) for es in EXs[w]))

    def rec_key(M, S, full):
        sh = {w: min(dtw(S, es) for es in EXs[w]) for w in words}
        cands = sorted(words, key=lambda w: sh[w])[:KCAND]     # shape shortlists (the anchor)
        res = {}
        for w in cands:
            bex = min(EXc[w], key=lambda T: dtw(M, T))         # best exemplar of this hypothesis
            res[w] = fit_key(M, bex, full)                     # fit its own key, AbS residual
        zsh = _zc(sh, cands); zr = _zc(res, cands)
        return min(cands, key=lambda w: zsh[w] + zr[w])

    n = len(te)
    raw1 = shp1 = vt = full = 0
    for (w, g) in te:
        M = coch_mc(g); S = relational_shape(coch(g))
        raw1 += int(rec_raw(M) == w)
        shp1 += int(rec_shape(S) == w)
        vt += int(rec_key(M, S, full=False) == w)     # VTL + tilt key
        full += int(rec_key(M, S, full=True) == w)    # VTL + tilt + curvature + reverb key
    print(f"  {'raw single-pass (no key)':<48} {raw1/n*100:>5.0f}%")
    print(f"  {'shape single-pass (bootstrap)':<48} {shp1/n*100:>5.0f}%")
    print(f"  {'key VTL+tilt, shape-anchored':<48} {vt/n*100:>5.0f}%")
    print(f"  {'key VTL+tilt+curvature+reverb, shape-anchored':<48} {full/n*100:>5.0f}%")

    print("\n" + "=" * 96)
    rp, sp, vp, fp = raw1 / n, shp1 / n, vt / n, full / n
    best = max(vp, fp)
    if best > sp + 0.03:
        ch = fp - vp
        print(f"  PAYOFF HELD on the bigger content corpus: key contraction {best*100:.0f}% beats bootstrap "
              f"{sp*100:.0f}%, raw {rp*100:.0f}%.")
        print(f"  Channel+reverb over VTL+tilt: {ch*100:+.0f}pt ({'the medium-stamp terms cash out' if ch > 0.01 else 'no net gain here — VTL is the dominant key'}).")
    else:
        print(f"  key {best*100:.0f}% vs bootstrap {sp*100:.0f}% (raw {rp*100:.0f}%): on {len(words)} words the extra")
        print("  key dimensions widen the search faster than per-word exemplars constrain it — the basin/over-fit")
        print("  risk; the dominant recoverable key here is VTL, with channel/reverb adding little net on this data.")
    print("=" * 96)


if __name__ == "__main__":
    main()
