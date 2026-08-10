"""SHARPEN THE EMISSION — flat-start realignment of the within-word phone boundaries (the #1 named headroom).

The triphone units fixed RECALL but not top-1 PRECISION, because the phonebank splits each word's frames into
phones UNIFORMLY (np.linspace) -- phones vary 2-5x in duration, so every unit is blurred across its neighbours.
The classic ASR fix, using only the cached frames (no re-alignment from audio):
  1. FLAT START: build rough monophone medoids from the uniform splits.
  2. REALIGN: for each word, DTW its frames against the concatenation of its phones' monophone medoids, backtrack
     the path -> data-driven phone boundaries -> re-split.
  3. Rebuild triphone units from the realigned splits.
Then measure top-1/top-3 at many-way: UNIFORM units vs REALIGNED units. If realignment lifts top-1, the blur was
the precision bottleneck -- the emission sharpened, the full-stack's top-1 floor rises.

Run:
  cd experiments/gamma-substrate
  ulimit -v 20971520
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_realign_emission
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
from scripts.phonebank import CACHE, _meta, medoid, pick
from scripts.jabberwock_reads_oov_from_phones import phones, dtw, STOP

SAMPLE = 60000        # words to (re)build units from (uniform AND realigned, same sample -> fair comparison)
N_WAYS = [25, 50, 100]
MAX_CLIPS = 110


def build_units(per_word):
    """per_word: list of (phone_list, [sub_frames per phone]). Build triphone/bigram/monophone medoid units."""
    tri, rbi, lbi, mono = {}, {}, {}, {}
    for ph, subs in per_word:
        for i in range(len(ph)):
            if i >= len(subs) or subs[i] is None or len(subs[i]) < 1:
                continue
            L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
            tri.setdefault((L, ph[i], R), []).append(subs[i])
            rbi.setdefault((ph[i], R), []).append(subs[i])
            lbi.setdefault((L, ph[i]), []).append(subs[i])
            mono.setdefault(ph[i], []).append(subs[i])
    g = lambda b: {k: medoid(v) for k, v in b.items() if len(v) >= 2}
    return g(tri), g(rbi), g(lbi), g(mono)


def uniform_split(fr, ph):
    nf = len(fr); cuts = np.linspace(0, nf, len(ph) + 1).astype(int)
    return [fr[cuts[i]:cuts[i + 1]] for i in range(len(ph))]


def realign_split(fr, ph, mono):
    """DTW the word's frames against the concat of its monophone medoids; backtrack -> per-frame phone -> re-split."""
    segs = [mono.get(p) for p in ph]
    if any(s is None for s in segs):
        return None
    B = np.concatenate(segs, 0)
    owner = np.concatenate([[i] * len(s) for i, s in enumerate(segs)])
    n, m = len(fr), len(B)
    if n < len(ph):
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
    subs = [fr[assign == k] for k in range(len(ph))]
    return subs


def template(w, units):
    Tri, Rbi, Lbi, Mono = units
    ph = phones(w)
    if not ph:
        return None
    parts = []
    for i in range(len(ph)):
        L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
        m = pick(L, ph[i], R, Tri, Rbi, Lbi, Mono)[0]
        if m is None:
            return None
        parts.append(m)
    return np.concatenate(parts, axis=0)


def main():
    print("=" * 100)
    print("SHARPEN THE EMISSION — UNIFORM vs flat-start REALIGNED triphone units, top-1/top-3 vs N-way")
    print("=" * 100)
    _ts, targets, clips = _meta()
    words = []
    for c in sorted(glob.glob(os.path.join(CACHE, "*_*.pkl"))):
        words += pickle.load(open(c, "rb"))
    rng = np.random.RandomState(0)
    idx = rng.permutation(len(words))[:SAMPLE]
    sample = [words[i] for i in idx]
    vocabcount = Counter(w for (w, _f, _p) in words)
    del words
    print(f"  sampled {len(sample)} words; flat-start (uniform) units...", flush=True)

    uni_pw = [(ph, uniform_split(np.asarray(fr, dtype=np.float32), ph)) for (_w, fr, ph) in sample]
    uni = build_units(uni_pw)
    _, _, _, mono0 = uni
    print(f"  realigning {len(sample)} words against monophone models...", flush=True)
    re_pw = []
    for k, (_w, fr, ph) in enumerate(sample):
        subs = realign_split(np.asarray(fr, dtype=np.float32), ph, mono0)
        re_pw.append((ph, subs if subs is not None else uniform_split(np.asarray(fr, dtype=np.float32), ph)))
        if (k + 1) % 20000 == 0:
            print(f"    realigned {k + 1}/{len(sample)}...", flush=True)
    rea = build_units(re_pw)
    print(f"  uniform {len(uni[0])} triphone buckets | realigned {len(rea[0])}\n", flush=True)

    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in set(targets) and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand_full = list(dict.fromkeys(list(targets) + distractors))
    cand_full = [w for w in cand_full if template(w, uni) is not None and template(w, rea) is not None][:max(N_WAYS)]
    clips = clips[:MAX_CLIPS]
    print(f"  up to {len(cand_full)}-way; {len(clips)} held-out clips\n", flush=True)

    tU = {w: template(w, uni) for w in cand_full}
    tR = {w: template(w, rea) for w in cand_full}
    scored = []
    for k, (w, cf) in enumerate(clips):
        cf = np.asarray(cf, dtype=np.float32)
        ud = {c: dtw(cf, tU[c]) for c in cand_full}
        rd = {c: dtw(cf, tR[c]) for c in cand_full}
        scored.append((w, ud, rd))
        if (k + 1) % 30 == 0:
            print(f"    scored {k + 1}/{len(clips)}...", flush=True)

    def acc(key, n):
        cand = cand_full[:n]; t1 = t3 = tot = 0
        for (w, ud, rd) in scored:
            sc = ud if key == "uni" else rd
            r = sorted((c for c in cand if c in sc), key=lambda c: sc[c])
            if not r:
                continue
            tot += 1; t1 += int(r[0] == w); t3 += int(w in r[:3])
        return 100 * t1 / max(tot, 1), 100 * t3 / max(tot, 1)

    print(f"  top-1 / top-3 by N-way:")
    print(f"    {'N-way':>7}{'UNIFORM':>18}{'REALIGNED':>18}")
    last = None
    for n in N_WAYS:
        u1, u3 = acc("uni", n); r1, r3 = acc("rea", n)
        last = (n, u1, u3, r1, r3)
        print(f"    {n:>7}{u1:>11.0f}% /{u3:>4.0f}%{r1:>11.0f}% /{r3:>4.0f}%")

    n, u1, u3, r1, r3 = last
    print("\n" + "=" * 100)
    if r1 >= u1 + 3 or r3 >= u3 + 4:
        print(f"  REALIGNMENT SHARPENS THE EMISSION: at {n}-way realigned top-1/top-3 {r1:.0f}/{r3:.0f} beats uniform "
              f"{u1:.0f}/{u3:.0f}.")
        print("  The uniform-split BLUR was a precision bottleneck; data-driven phone boundaries discriminate better --")
        print("  the emission's own precision (the named headroom) improves, raising the full-stack's top-1 floor.")
    else:
        print(f"  REALIGNMENT ~= UNIFORM at {n}-way (realigned {r1:.0f}/{r3:.0f} vs uniform {u1:.0f}/{u3:.0f}). One DTW realign")
        print("  pass off blurry flat-start models didn't sharpen enough -- needs iterated realignment or a marginal")
        print("  forward over exemplars (the other named lever), not a single hard re-split. Honest.")
    print("=" * 100)


if __name__ == "__main__":
    main()
