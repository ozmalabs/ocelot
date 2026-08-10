"""THE ORTHOGONAL-AXIS ROUTE — recognise the word on an axis where VTL does NOT live.

The render experiments proved speaker (VTL) and word (vowel formants) are entangled on the SAME physical axis
(formant frequency), so no frequency warp can net-separate them. The lever is not a better render -- it is to
REPRESENT THE WORD on an axis ORTHOGONAL to VTL, which the agent already owns:
  RELATIONAL shape (domains/relational_shape): the within-frame ordinal band-RANK profile + the whole-unit
    self-similarity texture -- talker-invariant BY CONSTRUCTION (ordinal ranks survive any monotone talker
    transform; self-similarity is internal to the unit).
  DYNAMIC shape: how the spectrum MOVES frame-to-frame (the coarticulation gesture) -- shared across speakers
    even when the absolute formants differ by VTL.

Clean isolation: ONE cochleagram source, ONE DTW matcher (the agent's dtw), only the REPRESENTATION differs.
Measured on the cross-speaker gap (enrol each word's LOW-centroid band, test the UNSEEN HIGH band). If the
orthogonal representations generalise across the speaker gap better than the absolute (CMVN'd) bands, the
word's identity does live on a VTL-orthogonal axis -- and THAT, not construction, is how to cross the wall.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_orthogonal_shape
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from domains.filter_settings import cochleagram
from domains.cmvn import apply_cmvn
from domains.relational_shape import relational_shape
from domains.agent_frontend import _MIDDLE
from scripts.jabberwock_key_shape_relaxation import dtw
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_function_word_context import FUNCTION

FS = 8000
KREC = 6
ENROL_CAP = 6
_NAME, _EC, _DC, _NF = _MIDDLE
REPS = ["absolute", "relational", "dynamic", "relational+dynamic"]


def spectral_centroid(x):
    X = np.abs(np.fft.rfft(np.asarray(x, dtype=np.float64) * np.hanning(len(x))))
    f = np.fft.rfftfreq(len(x), 1.0 / FS)
    e = X.sum()
    return float((f * X).sum() / e) if e > 1e-9 else 1000.0


def representations(x):
    """The four representations of one clip from a SINGLE cochleagram (frames x bands)."""
    M = np.asarray(cochleagram(np.asarray(x, dtype=np.float64), FS, _EC, _DC, _NF), dtype=np.float64)
    A = apply_cmvn(M)                                   # absolute bands, speaker-mean removed (carries VTL)
    R = relational_shape(M)                             # band-rank + self-similarity (talker-invariant)
    D = np.gradient(M, axis=0)                          # spectral MOTION (the coarticulation gesture)
    Dz = (D - D.mean(0)) / (D.std(0) + 1e-6)
    RD = np.concatenate([R, Dz], axis=1)               # relational + dynamic
    return {"absolute": A, "relational": R, "dynamic": Dz, "relational+dynamic": RD}


def main():
    print("=" * 98)
    print("ORTHOGONAL-AXIS ROUTE — recognise on the talker-invariant relational/dynamic shape vs absolute.")
    print("=" * 98)
    train, test = multi_extract()
    freq = Counter(w for (w, _g) in train)
    words = [w for w, n in freq.most_common() if n >= 30 and w.isalpha() and w not in FUNCTION][:30]
    wi = set(words)
    pool = {}
    for (w, g) in train + test:
        g = np.asarray(g, dtype=np.float64)
        if w in wi and g.size >= int(0.04 * FS):
            pool.setdefault(w, []).append(g)

    # cross-speaker gap: enrol each word's LOW-centroid band, test the UNSEEN HIGH band.
    enrol, te = {}, []
    cands = []
    for w, exs in pool.items():
        if len(exs) < 16:
            continue
        cents = np.array([spectral_centroid(g) for g in exs])
        med = np.median(cents)
        lo = [exs[i] for i in range(len(exs)) if cents[i] <= med]
        hi = [exs[i] for i in range(len(exs)) if cents[i] > med]
        if len(lo) < 4 or len(hi) < 3:
            continue
        enrol[w] = lo[:ENROL_CAP]
        nho = max(2, len(hi) // 4)
        te += [(w, g) for g in hi[-nho:]]
        cands.append(w)
    cands.sort()
    print(f"  {len(cands)}-way content words; enrol LOW band, test UNSEEN HIGH band ({len(te)} held-out, chance {100/len(cands):.0f}%)")
    print(f"  computing representations (1 cochleagram source, DTW matcher, only representation differs)...\n", flush=True)

    # precompute all representations once.
    banked = {r: {w: [] for w in cands} for r in REPS}
    for w in cands:
        for g in enrol[w]:
            rep = representations(g)
            for r in REPS:
                banked[r][w].append(rep[r])
    te_reps = [(w, representations(g)) for (w, g) in te]

    print(f"  {'representation':<26}{'top-1':>9}{'top-6 recall':>15}{'  (vs absolute)':>16}")
    base_k = None
    for r in REPS:
        t1 = tk = tot = 0
        for (w, rep) in te_reps:
            q = rep[r]
            dists = {cw: min((dtw(q, b) for b in banked[r][cw]), default=np.inf) for cw in cands}
            order = sorted(cands, key=lambda c: dists[c])
            tot += 1; t1 += int(order[0] == w); tk += int(w in order[:KREC])
        a1, ak = t1 / tot, tk / tot
        if r == "absolute":
            base_k = ak
        delta = "" if r == "absolute" else f"{(ak-base_k)*100:+.0f} pt"
        print(f"  {r:<26}{a1*100:>8.0f}%{ak*100:>14.0f}%{delta:>16}")

    print("\n" + "=" * 98)
    # re-evaluate best orthogonal vs absolute for the verdict
    def recall(r):
        tk = tot = 0
        for (w, rep) in te_reps:
            q = rep[r]
            dists = {cw: min((dtw(q, b) for b in banked[r][cw]), default=np.inf) for cw in cands}
            tot += 1; tk += int(w in sorted(cands, key=lambda c: dists[c])[:KREC])
        return tk / tot
    abs_k = recall("absolute")
    orth = {r: recall(r) for r in REPS if r != "absolute"}
    best_r = max(orth, key=orth.get); best_k = orth[best_r]
    if best_k > abs_k + 0.05:
        print(f"  THE ORTHOGONAL AXIS CROSSES THE SPEAKER GAP: '{best_r}' reaches {best_k*100:.0f}% top-6 cross-speaker recall")
        print(f"  vs absolute bands {abs_k*100:.0f}% -- the word's identity DOES live on a VTL-orthogonal axis. Where a")
        print("  frequency warp could not net-separate speaker from word (same axis), the relational/dynamic shape")
        print("  never encoded VTL to begin with, so it generalises across the unseen speaker. This is the lever.")
    elif best_k > abs_k + 0.01:
        print(f"  PARTIAL: '{best_r}' {best_k*100:.0f}% edges absolute {abs_k*100:.0f}% cross-speaker -- the orthogonal axis helps but the")
        print("  rank/motion shape also sheds word detail; combining it WITH the absolute cue (not replacing) is next.")
    else:
        print(f"  '{best_r}' {best_k*100:.0f}% vs absolute {abs_k*100:.0f}%: the relational/dynamic shape did not beat absolute bands")
        print("  cross-speaker here -- on these short tokens the ordinal/motion representation sheds as much word")
        print("  discrimination as it sheds VTL, so the net cross-speaker generalisation is no better.")
    print("=" * 98)


if __name__ == "__main__":
    main()
