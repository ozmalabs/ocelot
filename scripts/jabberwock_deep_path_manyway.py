"""FIX THE DEEP PATH — does context-dependent (triphone) emission SURVIVE many-way where monophone collapses?

The whole session's wall: the OOV likelihood (read a never-banked word from phones) collapses at scale (the
monophone forward: 18%@24-way -> ~0%@80-way), so the source-prior had to be tested with an engineered-small floor.
The agent named the lever twice: the phone EMISSION, not the inference. The phonebank already holds it -- 500k
MMS_FA-aligned words -> CONTEXT-DEPENDENT triphone units with back-off (measure(): monophone top-3 26% vs CONTEXT
67% at ~25-way). This measures the SCALING: rank each held-out clip against a growing candidate set (25 -> 200 way)
with monophone vs triphone emission, and report top-1 / top-3 vs N. If triphone holds a non-trivial floor where
monophone decays to chance, the deep path is FIXED -- and the source-prior would have a real floor to amplify.

Run:
  cd experiments/gamma-substrate
  ulimit -v 20971520
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_deep_path_manyway
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
from scripts.phonebank import CACHE, _meta, _build, pick
from scripts.jabberwock_reads_oov_from_phones import phones, dtw, STOP

N_WAYS = [25, 50, 100, 200]
MAX_CLIPS = 110          # sample held-out clips (DTW cost)


def template(w, units, ctx):
    """Concatenate the word's per-phone context-unit medoids (triphone+back-off if ctx, else monophone)."""
    Tri, Rbi, Lbi, Mono = units
    ph = phones(w)
    if not ph:
        return None
    parts = []
    for i in range(len(ph)):
        L = ph[i - 1] if i > 0 else "#"; R = ph[i + 1] if i < len(ph) - 1 else "#"
        m = pick(L, ph[i], R, Tri, Rbi, Lbi, Mono)[0] if ctx else Mono.get(ph[i])
        if m is None:
            return None
        parts.append(m)
    return np.concatenate(parts, axis=0)


def main():
    print("=" * 100)
    print("FIX THE DEEP PATH — triphone vs monophone emission, top-1/top-3 vs N-way (does context SURVIVE scale?)")
    print("=" * 100)
    _ts, targets, clips = _meta()
    chunks = sorted(glob.glob(os.path.join(CACHE, "*_*.pkl")))
    words = []
    for c in chunks:
        words += pickle.load(open(c, "rb"))
    print(f"  loaded {len(words)} banked words; building context units...", flush=True)
    units = _build(words)
    vocabcount = Counter(w for (w, _fr, _ph) in words)
    del words
    tset = set(targets)
    distractors = [w for (w, _c) in vocabcount.most_common()
                   if w not in tset and w not in STOP and phones(w) and len(phones(w)) >= 3 and len(w) >= 4]
    cand_full = list(dict.fromkeys(list(targets) + distractors))[:max(N_WAYS)]
    clips = clips[:MAX_CLIPS]
    print(f"  {len(targets)} true target words + distractors -> up to {len(cand_full)}-way; {len(clips)} held-out clips\n",
          flush=True)

    # precompute each candidate's mono + triphone template ONCE
    tmpl = {"mono": {}, "ctx": {}}
    for w in cand_full:
        tmpl["mono"][w] = template(w, units, False)
        tmpl["ctx"][w] = template(w, units, True)

    # per clip, score against ALL candidates once (mono + ctx); then sweep N by subsetting
    scored = []      # (true_word, {w: mono_d}, {w: ctx_d})
    for k, (w, cf) in enumerate(clips):
        cf = np.asarray(cf, dtype=np.float32)
        md = {c: dtw(cf, tmpl["mono"][c]) for c in cand_full if tmpl["mono"][c] is not None}
        cd = {c: dtw(cf, tmpl["ctx"][c]) for c in cand_full if tmpl["ctx"][c] is not None}
        scored.append((w, md, cd))
        if (k + 1) % 30 == 0:
            print(f"    scored {k + 1}/{len(clips)} clips...", flush=True)

    def acc(scores_key, n):
        cand = cand_full[:n]
        t1 = t3 = tot = 0
        for (w, md, cd) in scored:
            sc = (md if scores_key == "mono" else cd)
            ranked = sorted((c for c in cand if c in sc), key=lambda c: sc[c])
            if not ranked:
                continue
            tot += 1
            t1 += int(ranked[0] == w)
            t3 += int(w in ranked[:3])
        return (100 * t1 / max(tot, 1), 100 * t3 / max(tot, 1))

    print(f"\n  top-1 / top-3 by N-way (chance top-1 = 100/N):")
    print(f"    {'N-way':>7}{'chance':>9}{'MONOPHONE':>20}{'TRIPHONE (context)':>24}")
    rows = []
    for n in N_WAYS:
        m1, m3 = acc("mono", n)
        c1, c3 = acc("ctx", n)
        rows.append((n, m1, m3, c1, c3))
        print(f"    {n:>7}{100.0/n:>8.1f}%{m1:>11.0f}% /{m3:>5.0f}%{c1:>15.0f}% /{c3:>5.0f}%")

    n_max = N_WAYS[-1]
    _, m1, m3, c1, c3 = rows[-1]
    print("\n" + "=" * 100)
    if c1 >= 4 * (100.0 / n_max) and c1 >= m1 + 5:
        print(f"  THE DEEP PATH SURVIVES MANY-WAY: at {n_max}-way the CONTEXT (triphone) emission holds top-1 {c1:.0f}% / "
              f"top-3 {c3:.0f}%")
        print(f"  ({c1/(100.0/n_max):.0f}x chance) while the MONOPHONE decays to {m1:.0f}% / {m3:.0f}%. The lever was the EMISSION, not")
        print("  the inference -- context-dependent units (already banked, 100% triphone reach) fix the collapse. The")
        print("  source-prior now has a REAL likelihood floor to amplify in the wild, not an engineered-small one.")
    else:
        print(f"  Triphone at {n_max}-way: top-1 {c1:.0f}% / top-3 {c3:.0f}% vs monophone {m1:.0f}%/{m3:.0f}%. Better, but not a clear")
        print("  many-way survival at this scale -- the emission helps but a stronger sequence/duration model may be needed.")
    print("=" * 100)


if __name__ == "__main__":
    main()
