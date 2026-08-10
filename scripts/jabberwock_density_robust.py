"""DENSITY ROBUSTNESS — is the 60k->498k realigned top-1 lift (13->16) REAL on ALL 222 held-out clips, or 110-clip noise?

The density sweep showed top-1 13->16 / top-3 30->35 at the full 498k, but on 110 clips (+3% ~ 1 sigma) and a non-
monotonic curve (13,11,12,16). This tightens the key contrast on ALL 222 clips (halves the noise) and ATTRIBUTES the
gain: UNIFORM-498k (density only) vs REALIGNED-498k (density + sharper boundaries) vs REALIGNED-60k (the prior win).
Same fixed 100-way candidate set throughout.

Run:
  cd experiments/gamma-substrate
  ulimit -v 24000000
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_density_robust
"""
from __future__ import annotations

import glob
import math
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

N_WAY = 100


def units_from(sample, realign):
    uni = [(ph, uniform_split(np.asarray(fr, np.float32), ph)) for (_w, fr, ph) in sample]
    u = build_units(uni)
    if not realign:
        return u
    _, _, _, mono0 = u
    re_pw = []
    for (_w, fr, ph) in sample:
        fr = np.asarray(fr, np.float32)
        subs = realign_split(fr, ph, mono0)
        re_pw.append((ph, subs if subs is not None else uniform_split(fr, ph)))
    return build_units(re_pw)


def main():
    print("=" * 100)
    print("DENSITY ROBUSTNESS — 60k vs 498k realigned (+ uniform-498k), ALL 222 held-out clips, 100-way")
    print("=" * 100)
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    perm = rng.permutation(len(words))
    vocabcount = Counter(w for (w, _f, _p) in words)
    clips = [(w, np.asarray(cf, np.float32)) for (w, cf) in clips]
    print(f"  {len(words)} words; {len(clips)} held-out clips (ALL)\n", flush=True)

    print("  building units: realigned-60k, realigned-498k, uniform-498k ...", flush=True)
    re60 = units_from([words[i] for i in perm[:60000]], realign=True)
    re498 = units_from(words, realign=True)
    uni498 = units_from(words, realign=False)

    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand_full = list(dict.fromkeys(list(targets) + distractors))
    cand = [w for w in cand_full if template(w, re60) is not None][:N_WAY]
    print(f"  {len(cand)}-way (fixed); tri-buckets re60={len(re60[0])} re498={len(re498[0])} uni498={len(uni498[0])}\n", flush=True)

    def measure(units):
        tmpl = {w: template(w, units) for w in cand}
        t1 = t3 = tot = 0
        for (w, cf) in clips:
            d = {c: dtw(cf, tmpl[c]) for c in cand if tmpl[c] is not None}
            if w not in d:
                continue
            r = sorted(d, key=d.get)
            tot += 1; t1 += int(r[0] == w); t3 += int(w in r[:3])
        return t1, t3, tot

    rows = [("realigned-60k  (prior win)", re60), ("uniform-498k   (density only)", uni498),
            ("realigned-498k (density+realign)", re498)]
    print(f"    {'units':34}{'top-1':>14}{'top-3':>14}")
    res = {}
    for name, u in rows:
        t1, t3, tot = measure(u)
        res[name] = (t1, t3, tot)
        se = 100 * math.sqrt((t1 / tot) * (1 - t1 / tot) / tot)
        print(f"    {name:34}{100*t1/tot:>7.1f}% (±{se:.1f}){100*t3/tot:>10.1f}%", flush=True)

    print("\n" + "=" * 100)
    b1, _b3, tot = res["realigned-60k  (prior win)"]
    d1, d3, _ = res["realigned-498k (density+realign)"]
    u1, _u3, _ = res["uniform-498k   (density only)"]
    base = 100 * b1 / tot; big = 100 * d1 / tot; uni = 100 * u1 / tot
    # 2-proportion z for 498k-realigned vs 60k-realigned
    p = (b1 + d1) / (2 * tot); se = math.sqrt(2 * p * (1 - p) / tot)
    z = (d1 - b1) / tot / se if se > 0 else 0.0
    print(f"  realigned 60k {base:.1f}  ->  498k {big:.1f}  (uniform-498k {uni:.1f})   |   z(498k vs 60k realigned) = {z:.2f}")
    if big >= 15 and z >= 1.64:
        print(f"  CONFIRMED — density is a REAL lever: realigned-498k {big:.1f} beats realigned-60k {base:.1f} on 222 clips,")
        print(f"  z={z:.2f} (>1.64, one-sided p<0.05). Attribution: realignment adds over uniform at full density "
              f"({big:.1f} vs {uni:.1f}). Bank it.")
    elif big >= 15:
        print(f"  POSITIVE but NOT significant on 222 clips ({base:.1f}->{big:.1f}, z={z:.2f}<1.64): cleared the pre-registered")
        print("  15 bar yet within noise. Real-leaning but soft; report honestly, don't over-claim.")
    else:
        print(f"  WASHED OUT on 222 clips ({base:.1f}->{big:.1f}): the 110-clip 16 did not hold. The density lift was noise.")
        print("  Honest negative; 60k already saturates.")
    print("=" * 100)


if __name__ == "__main__":
    main()
