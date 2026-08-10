"""ITERATED REALIGNMENT = EM = the closed loop, on the speech emission — does top-1 CLIMB each pass?

One flat-start realignment pass doubled top-1 (jabberwock_realign_emission). Iterating it is EM, which is the pulse
applied to the emission: each pass is a CORRECTION -- realign every word using the CURRENT (sharper) monophone
models, which reduces the within-word alignment residual, which makes the next models sharper -- folded across
passes (the clock). The residual decays across the loop; recognition climbs. This runs N passes (pass 0 = uniform
flat start) and measures content-word top-1/top-3 at many-way after each, on held-out clips. If it climbs then
plateaus, the closed loop sharpened the emission to convergence -- the speech version of the shortfall decaying.

Run:
  cd experiments/gamma-substrate
  ulimit -v 20971520
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_iterated_realign
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
from scripts.phonebank import CACHE, _meta, pick
from scripts.jabberwock_reads_oov_from_phones import phones, dtw, STOP
from scripts.jabberwock_realign_emission import build_units, uniform_split, realign_split, template

SAMPLE = 60000
PASSES = 4
N_WAY = 100
MAX_CLIPS = 110


def main():
    print("=" * 96)
    print("ITERATED REALIGNMENT (EM = the closed loop on the emission) — does content top-1 CLIMB each pass?")
    print("=" * 96)
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    sample = [(w, np.asarray(fr, dtype=np.float32), ph) for (w, fr, ph) in
              (words[i] for i in rng.permutation(len(words))[:SAMPLE])]
    vocabcount = Counter(w for (w, _f, _p) in words)
    del words
    print(f"  {len(sample)} words sampled; {PASSES} passes\n", flush=True)

    # candidate vocab + held-out clips (fixed across passes)
    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand_full = (list(dict.fromkeys(list(targets) + distractors)))[:N_WAY]
    clips = [(w, np.asarray(cf, dtype=np.float32)) for (w, cf) in clips[:MAX_CLIPS]]

    def measure(units, cand):
        cand = [w for w in cand if template(w, units) is not None]
        tmpl = {w: template(w, units) for w in cand}
        t1 = t3 = tot = 0
        for (w, cf) in clips:
            d = {c: dtw(cf, tmpl[c]) for c in cand}
            r = sorted(d, key=d.get)
            if w not in d:
                continue
            tot += 1; t1 += int(r[0] == w); t3 += int(w in r[:3])
        return 100 * t1 / max(tot, 1), 100 * t3 / max(tot, 1)

    # pass 0 = uniform flat start; pass k = realign with pass-(k-1) monophone models
    splits = [uniform_split(fr, ph) for (_w, fr, ph) in sample]
    results = []
    for p in range(PASSES):
        units = build_units([(ph, sp) for ((_w, _fr, ph), sp) in zip(sample, splits)])
        t1, t3 = measure(units, cand_full)
        results.append((p, t1, t3, len(units[0])))
        tag = "uniform (flat start)" if p == 0 else f"realign pass {p}"
        print(f"    pass {p}  ({tag:22}): {len(units[0])} triphone buckets | top-1 {t1:.0f}%  top-3 {t3:.0f}%", flush=True)
        if p < PASSES - 1:
            mono = units[3]                                          # current monophone models
            splits = [realign_split(fr, ph, mono) or uniform_split(fr, ph) for (_w, fr, ph) in sample]

    print("\n" + "=" * 96)
    b1, b3 = results[0][1], results[0][2]
    best = max(results, key=lambda r: r[1])
    print(f"  flat-start (pass 0): top-1 {b1:.0f}% / top-3 {b3:.0f}%  ->  best (pass {best[0]}): top-1 {best[1]:.0f}% / top-3 {best[2]:.0f}%")
    if best[1] >= b1 + 3:
        print(f"  THE LOOP SHARPENS THE EMISSION: iterated realignment (EM) climbed content top-1 +{best[1]-b1:.0f} pts across")
        print(f"  passes -- each correction (realign with sharper models) reduced the alignment residual, folded across")
        print("  passes; the residual decayed, recognition climbed. The pulse, on the speech emission. Speech: gooderer.")
    else:
        print(f"  iterated realignment plateaued fast (best +{best[1]-b1:.0f} over flat-start): one pass got most of it;")
        print("  the residual the loop can remove is shallow here (uniform flat-start is already close). Honest.")
    print("=" * 96)


if __name__ == "__main__":
    main()
