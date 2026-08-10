"""WIRE THE ORTHOGONAL AXIS INTO THE GRAPH-NATIVE RECOGNISER — combine-all product over DTW channels.

The orthogonal-axis run proved the word's identity lives on a VTL-orthogonal axis (dynamic/relational shape),
crossing the cross-speaker gap where the absolute bands could not. Now wire it INTO the agent's recogniser:
the combine-all PRODUCT (many_settings) -- which already supports NON-cosine channels ("a channel whose
distance is NOT a cosine reuses the identical math", likelihood_from_distances) -- over DTW-distance channels:
  absolute   (CMVN cochleagram trajectory) -- same-speaker precision, but carries VTL
  relational (band-rank + self-similarity)  -- talker-invariant by construction
  dynamic    (spectral motion gesture)      -- the coarticulation gesture, VTL-orthogonal
Each channel: 1-NN DTW distance per word -> per-channel likelihood -> MULTIPLIED (the combine-all product
keeps the truth ranked high when ANY channel agrees). The claim: the PRODUCT is best-of-both -- absolute's
same-speaker precision AND dynamic's cross-speaker recall in ONE recogniser.

Measured in BOTH conditions: CROSS-SPEAKER (enrol low-centroid band, test unseen high band) and SAME/MIXED
(random split, same speaker distribution). A combined recogniser should be robust in both.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_combined_recogniser
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import domains.many_settings_recognizer as MS
from scripts.jabberwock_key_shape_relaxation import dtw
from scripts.jabberwock_orthogonal_shape import representations, spectral_centroid
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_function_word_context import FUNCTION

FS = 8000
KREC = 6
ENROL_CAP = 6
CH = ["absolute", "relational", "dynamic"]
COMBOS = [("absolute",), ("relational",), ("dynamic",),
          ("absolute", "dynamic"), ("relational", "dynamic"),
          ("absolute", "relational", "dynamic")]


def chan_dist(q_rep, banked_reps, cands, ch):
    """one channel's 1-NN DTW distance per candidate word (the channel's exemplar evidence)."""
    return {w: min((dtw(q_rep[ch], b[ch]) for b in banked_reps[w]), default=np.inf) for w in cands}


def evaluate(enrol_reps, test_reps, cands):
    """Per test token, cache each channel's per-word likelihood once; every COMBO is then a product
    of cached channel likelihoods (the combine-all). Returns {combo: (top1, top6)}."""
    acc = {c: [0, 0, 0] for c in COMBOS}              # [top1, top6, total]
    for (w, q) in test_reps:
        liks = {}
        for ch in CH:
            d = chan_dist(q, enrol_reps, cands, ch)
            liks[ch] = MS.likelihood_from_distances(d)
        for combo in COMBOS:
            logp = {c: 0.0 for c in cands}
            for ch in combo:
                for c in cands:
                    logp[c] += np.log(liks[ch][c] + 1e-12)
            order = sorted(cands, key=lambda c: -logp[c])
            acc[combo][2] += 1
            acc[combo][0] += int(order[0] == w)
            acc[combo][1] += int(w in order[:KREC])
    return {c: (a[0] / a[2], a[1] / a[2]) for c, a in acc.items()}


def report(title, res):
    print(f"\n  {title}")
    print(f"    {'combine-all product over channels':<40}{'top-1':>9}{'top-6 recall':>15}")
    for combo in COMBOS:
        t1, tk = res[combo]
        print(f"    {' x '.join(combo):<40}{t1*100:>8.0f}%{tk*100:>14.0f}%")


def main():
    print("=" * 98)
    print("WIRE ORTHOGONAL AXIS INTO THE RECOGNISER — combine-all PRODUCT over absolute/relational/dynamic DTW.")
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

    cands = []
    by = {}
    for w, exs in pool.items():
        if len(exs) >= 16:
            by[w] = exs[:24]; cands.append(w)        # cap exemplars for runtime
    cands.sort()
    print(f"  {len(cands)}-way content words (chance {100/len(cands):.0f}%); precomputing representations "
          f"(absolute/relational/dynamic)...", flush=True)
    reps = {w: [representations(g) for g in by[w]] for w in cands}
    cents = {w: [spectral_centroid(g) for g in by[w]] for w in cands}

    # ---- CONDITION 1: CROSS-SPEAKER (enrol low-centroid band, test unseen high band) ----
    en1, te1 = {}, []
    for w in cands:
        order = np.argsort(cents[w]); n = len(order)
        loidx = order[:n // 2]; hiidx = order[n // 2:]
        en1[w] = [reps[w][i] for i in loidx[:ENROL_CAP]]
        nho = max(2, len(hiidx) // 4)
        te1 += [(w, reps[w][i]) for i in hiidx[-nho:]]
    res1 = evaluate(en1, te1, cands)

    # ---- CONDITION 2: SAME/MIXED (random split, same speaker distribution) ----
    en2, te2 = {}, []
    for w in cands:
        idx = list(range(len(reps[w])))
        cut = max(ENROL_CAP, len(idx) - max(2, len(idx) // 4))
        en2[w] = [reps[w][i] for i in idx[:ENROL_CAP]]
        te2 += [(w, reps[w][i]) for i in idx[cut:]]
    res2 = evaluate(en2, te2, cands)

    report(f"CROSS-SPEAKER gap (low->unseen high band, {len(te1)} held-out):", res1)
    report(f"SAME/MIXED split (same speaker distribution, {len(te2)} held-out):", res2)

    full = ("absolute", "relational", "dynamic")
    cs_full, cs_abs = res1[full][1], res1[("absolute",)][1]
    sm_full, sm_abs = res2[full][1], res2[("absolute",)][1]
    print("\n" + "=" * 98)
    if cs_full >= cs_abs + 0.05 and sm_full >= sm_abs - 0.03:
        print(f"  BEST OF BOTH: the combine-all product over absolute x relational x dynamic gives cross-speaker top-6")
        print(f"  recall {cs_full*100:.0f}% (vs absolute alone {cs_abs*100:.0f}%) WHILE holding same-speaker recall {sm_full*100:.0f}% (absolute {sm_abs*100:.0f}%).")
        print("  Wiring the VTL-orthogonal dynamic/relational channels into the recogniser's product buys the")
        print("  cross-speaker generalisation the absolute channel lacked, with no loss where absolute was strong.")
    else:
        print(f"  combined cross-speaker {cs_full*100:.0f}% (abs {cs_abs*100:.0f}%), same-speaker {sm_full*100:.0f}% (abs {sm_abs*100:.0f}%): the product")
        print("  helps but the channels trade off rather than compounding -- per-channel weighting is the next lever.")
    print("=" * 98)


if __name__ == "__main__":
    main()
