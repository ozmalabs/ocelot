"""DAMPED iterated realignment — the loop thread's fix, in speech: an over-driven EM drifts; DAMP it to converge.

Naive iterated realignment (jabberwock_iterated_realign) doubled top-1 in one pass then DRIFTED (13->11->11) -- the
emission and the alignment co-adapt and over-commit. That is the under-damped fold: gain too high -> overshoot/ring.
The loop thread's fix is damping. So damp the realignment: each pass, move every phone boundary only PART of the way
(learning rate alpha < 1) toward the freshly-realigned boundary -- bound <- (1-a)*bound + a*realigned. alpha=1 is the
drifting undamped loop; small alpha is a conservative fold that converges. Sweep alpha; does a damped loop hold/EXCEED
the single-pass 13% where the undamped one decayed to 11%? Same 60k sample, same held-out clips, content-word
top-1/top-3 at 100-way per pass.

Run:
  cd experiments/gamma-substrate
  ulimit -v 20971520
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_damped_realign
"""
from __future__ import annotations

import glob
import os
import pickle
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.phonebank import CACHE, _meta
from scripts.jabberwock_reads_oov_from_phones import phones, dtw, STOP
from scripts.jabberwock_realign_emission import build_units, template

SAMPLE = 60000
PASSES = 4
N_WAY = 100
MAX_CLIPS = 110
ALPHAS = [1.0, 0.5, 0.3]      # 1.0 = undamped (drifts); <1 = damped


def realign_bounds(fr, ph, mono):
    """DTW the word's frames vs its monophone template; backtrack -> per-phone boundary indices [0..n]."""
    segs = [mono.get(p) for p in ph]
    if any(s is None for s in segs):
        return None
    B = np.concatenate(segs, 0)
    owner = np.concatenate([[i] * len(s) for i, s in enumerate(segs)])
    n, m, L = len(fr), len(B), len(ph)
    if n < L:
        return None
    C = 1.0 - fr @ B.T
    dp = np.full((n + 1, m + 1), 1e18); dp[0, 0] = 0.0
    for i in range(1, n + 1):
        Ci = C[i - 1]; di = dp[i]; dpm = dp[i - 1]
        for j in range(1, m + 1):
            di[j] = Ci[j - 1] + min(dpm[j], di[j - 1], dpm[j - 1])
    i, j = n, m; assign = np.zeros(n, dtype=int)
    while i > 0 and j > 0:
        assign[i - 1] = owner[j - 1]
        cands = [(dp[i - 1, j - 1], i - 1, j - 1), (dp[i - 1, j], i - 1, j), (dp[i, j - 1], i, j - 1)]
        _, i, j = min(cands)
    bounds = [0] + [int(np.searchsorted(assign, k)) for k in range(1, L)] + [n]
    for k in range(1, L + 1):
        bounds[k] = max(bounds[k], bounds[k - 1])
    return bounds


def split_at(fr, bounds):
    return [fr[bounds[k]:bounds[k + 1]] for k in range(len(bounds) - 1)]


def main():
    print("=" * 100)
    print("DAMPED iterated realignment — does damping the loop (alpha<1) BEAT the drifting undamped EM?")
    print("=" * 100)
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    sample = [(w, np.asarray(fr, dtype=np.float32), ph) for (w, fr, ph) in
              (words[i] for i in rng.permutation(len(words))[:SAMPLE])]
    vocabcount = Counter(w for (w, _f, _p) in words)
    del words
    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand_full = (list(dict.fromkeys(list(targets) + distractors)))[:N_WAY]
    clips = [(w, np.asarray(cf, dtype=np.float32)) for (w, cf) in clips[:MAX_CLIPS]]
    print(f"  {len(sample)} words; {N_WAY}-way; {len(clips)} clips; alphas {ALPHAS}\n", flush=True)

    def measure(units):
        cand = [w for w in cand_full if template(w, units) is not None]
        tmpl = {w: template(w, units) for w in cand}
        t1 = t3 = tot = 0
        for (w, cf) in clips:
            d = {c: dtw(cf, tmpl[c]) for c in cand}
            r = sorted(d, key=d.get)
            if w not in d:
                continue
            tot += 1; t1 += int(r[0] == w); t3 += int(w in r[:3])
        return 100 * t1 / max(tot, 1), 100 * t3 / max(tot, 1)

    uniform_bounds = [list(np.linspace(0, len(fr), len(ph) + 1).astype(int)) for (_w, fr, ph) in sample]
    print(f"    {'alpha':>7}" + "".join(f"{'pass'+str(p):>12}" for p in range(PASSES)))
    curves = {}
    for alpha in ALPHAS:
        bounds = [list(b) for b in uniform_bounds]
        row = []
        for p in range(PASSES):
            units = build_units([(ph, split_at(fr, bounds[k])) for k, (_w, fr, ph) in enumerate(sample)])
            t1, t3 = measure(units)
            row.append((t1, t3))
            if p < PASSES - 1:
                mono = units[3]
                for k, (_w, fr, ph) in enumerate(sample):
                    nb = realign_bounds(fr, ph, mono)
                    if nb is None or len(nb) != len(bounds[k]):
                        continue
                    ob = bounds[k]
                    db = [int(round((1 - alpha) * ob[i] + alpha * nb[i])) for i in range(len(ob))]
                    for i in range(1, len(db)):
                        db[i] = max(db[i], db[i - 1])
                    bounds[k] = db
        curves[alpha] = row
        tag = "(undamped)" if alpha == 1.0 else "(damped)  "
        print(f"    {alpha:>7.1f}{tag}" + "".join(f"{t1:>5.0f}/{t3:<3.0f}   " for (t1, t3) in row))

    print("\n" + "=" * 100)
    base = curves[1.0][0][0]                                        # flat-start top-1
    und_best = max(t1 for (t1, _t3) in curves[1.0])
    und_final = curves[1.0][-1][0]
    damped_best = max(t1 for a in ALPHAS if a < 1.0 for (t1, _t3) in curves[a])
    da, dp = max(((a, p) for a in ALPHAS if a < 1.0 for p, (t1, _t3) in enumerate(curves[a]) if t1 == damped_best))
    print(f"  flat-start top-1 {base:.0f}%; UNDAMPED (alpha=1) best {und_best:.0f}% -> final {und_final:.0f}% (drifts);")
    print(f"  DAMPED best {damped_best:.0f}% at alpha={da}, pass {dp}.")
    if damped_best >= und_best + 2 or (damped_best >= und_best - 1 and curves[da][-1][0] >= und_final + 2):
        print(f"  DAMPING THE LOOP MAKES SPEECH GOODERER: a conservative fold (alpha={da}) holds/climbs to {damped_best:.0f}% where")
        print(f"  the over-driven undamped EM drifted to {und_final:.0f}%. The loop thread's fix -- lower the gain so the")
        print("  correction converges instead of overshooting -- applied to the emission. Speech, more gooderer.")
    else:
        print(f"  Damping prevents the worst of the drift but does not exceed the single-pass peak ({und_best:.0f}%) much here.")
        print("  One realignment pass captures the gain; the residual the loop can still remove is shallow. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
