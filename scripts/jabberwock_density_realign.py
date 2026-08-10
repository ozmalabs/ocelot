"""DENSITY x REALIGNMENT — the agent's remaining reliable lever: does realigning on the FULL 498k beat the 60k sample?

Realignment doubled content top-1 (6->13) on a 60k SAMPLE of the phonebank. "Density helps" is the most-repeated
positive in the ledger (triphone reach 100% only at 500k; context units climbed with data). The phonebank holds ~498k
words. This builds REALIGNED triphone units from a NESTED, growing prefix [60k, 150k, 300k, 498k] (true add-more-data
curve) and measures content top-1/top-3 @100-way on the SAME held-out clips, SAME fixed candidate set. Pre-registered:
  KEEP   top-1 >= 15 at the largest size (real lift over the 60k-sample 13) -> density is the lever; bank it.
  STOP   top-1 <= 13 (60k already saturates the realigned read) -> one pass at 60k got it; honest.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_density_realign
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
from scripts.jabberwock_realign_emission import build_units, realign_split, uniform_split, template

SIZES = [60000, 150000, 300000, 497863]
N_WAY = 100
MAX_CLIPS = 110


def realigned_units(sample):
    uni = [(ph, uniform_split(np.asarray(fr, np.float32), ph)) for (_w, fr, ph) in sample]
    _, _, _, mono0 = build_units(uni)
    re_pw = []
    for (_w, fr, ph) in sample:
        fr = np.asarray(fr, np.float32)
        subs = realign_split(fr, ph, mono0)
        re_pw.append((ph, subs if subs is not None else uniform_split(fr, ph)))
    return build_units(re_pw)


def main():
    print("=" * 100)
    print("DENSITY x REALIGNMENT — top-1/top-3 @100-way as realigned training data grows 60k -> 498k")
    print("=" * 100)
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    perm = rng.permutation(len(words))
    vocabcount = Counter(w for (w, _f, _p) in words)
    sizes = [s for s in SIZES if s <= len(words)]
    print(f"  {len(words)} words; nested prefixes {sizes}\n", flush=True)

    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand_full = list(dict.fromkeys(list(targets) + distractors))
    clips = [(w, np.asarray(cf, np.float32)) for (w, cf) in clips[:MAX_CLIPS]]

    # fix the candidate set on the SMALLEST size (buildable there -> buildable at all larger sizes), same 100 words throughout
    small = realigned_units([words[i] for i in perm[:sizes[0]]])
    cand = [w for w in cand_full if template(w, small) is not None][:N_WAY]
    print(f"  {len(cand)}-way (fixed across sizes); {len(clips)} held-out clips\n", flush=True)

    def measure(units):
        tmpl = {w: template(w, units) for w in cand}
        t1 = t3 = tot = 0
        for (w, cf) in clips:
            d = {c: dtw(cf, tmpl[c]) for c in cand if tmpl[c] is not None}
            r = sorted(d, key=d.get)
            if w not in d:
                continue
            tot += 1; t1 += int(r[0] == w); t3 += int(w in r[:3])
        return 100 * t1 / max(tot, 1), 100 * t3 / max(tot, 1), len(units[0])

    print(f"    {'size':>9}{'tri-buckets':>14}{'top-1':>9}{'top-3':>9}")
    curve = []
    for s in sizes:
        units = small if s == sizes[0] else realigned_units([words[i] for i in perm[:s]])
        t1, t3, nb = measure(units)
        curve.append((s, t1, t3, nb))
        print(f"    {s:>9}{nb:>14}{t1:>8.0f}%{t3:>8.0f}%", flush=True)

    print("\n" + "=" * 100)
    base = curve[0][1]; big1 = curve[-1][1]; big3 = curve[-1][2]
    print(f"  60k realigned top-1 {base:.0f}  ->  {curve[-1][0]//1000}k realigned top-1 {big1:.0f} / top-3 {big3:.0f}")
    if big1 >= 15:
        print(f"  KEEP — DENSITY IS THE LEVER: realigning on the full {curve[-1][0]//1000}k lifts content top-1 {base:.0f}->{big1:.0f}")
        print("  (>=15). More aligned data -> denser triphone coverage + sharper medoids -> better top-1. Speech: gooderer.")
    elif big1 <= 13:
        print(f"  STOP — density SATURATES: full {curve[-1][0]//1000}k top-1 {big1:.0f} ~= the 60k-sample {base:.0f}. One realignment")
        print("  pass at 60k already captured it; more data doesn't move top-1 here. Honest.")
    else:
        print(f"  WEAK — {base:.0f}->{big1:.0f} (13-15 band): a real but sub-threshold density lift; honest small.")
    print("=" * 100)


if __name__ == "__main__":
    main()
