"""PRODUCT vs ADMISSIBILITY vs VECTOR — how should the channels combine?

The combined recogniser used the RANK product (positive softmax likelihoods multiplied): every channel casts
a full positive vote, always. But the agent's recognition stance is EXCLUSION/ADMISSIBILITY
(ozma_recognition_is_exclusion) and, deeper, the VECTOR no-collapse combine (ozma_weighting_is_a_vector): a
cue's stance is a 2-vector [EXCLUDE, RANK], and collapsing to either scalar loses something. This matters here:
the ABSOLUTE channel carries VTL, so cross-speaker it casts WRONG positive votes -> under the rank product it
drags the truth down; under admissibility it can't discriminate (low separability) so it ABSTAINS, letting the
VTL-orthogonal dynamic channel do the excluding. So admissibility should help precisely where the rank product
hurts. Test all three combines over the SAME absolute/relational/dynamic DTW channels, in both conditions:

  RANK     : score = Sum_c  log rank_c        (positive vote product -- what we used)
  EXCLUDE  : score = Prod_c exclude_c          (admissibility: survive unless a cue confidently excludes)
  VECTOR   : score = (Prod_c exclude_c) * (Sum_c rank_c)   (the agent's no-collapse combine)

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_admissibility_combine
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from domains.many_settings_recognizer import (likelihood_from_distances,
                                              exclusion_likelihood_from_distances)
from scripts.jabberwock_key_shape_relaxation import dtw
from scripts.jabberwock_orthogonal_shape import representations, spectral_centroid
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_function_word_context import FUNCTION

FS = 8000
KREC = 6
ENROL_CAP = 6
CH = ["absolute", "relational", "dynamic"]
MODES = ["RANK (product)", "EXCLUDE (admissibility)", "VECTOR (exclude x rank)"]


def evaluate(enrol_reps, test_reps, cands):
    """Per test token: per-channel DTW 1-NN distance -> exclude & rank likelihoods -> the three combines."""
    acc = {m: [0, 0, 0] for m in MODES}
    for (w, q) in test_reps:
        excl_prod = {c: 1.0 for c in cands}
        rank_sum = {c: 0.0 for c in cands}
        rank_logprod = {c: 0.0 for c in cands}
        for ch in CH:
            d = {c: min((dtw(q[ch], b[ch]) for b in enrol_reps[c]), default=np.inf) for c in cands}
            ex = exclusion_likelihood_from_distances(d)
            rk = likelihood_from_distances(d)
            for c in cands:
                excl_prod[c] *= ex[c]
                rank_sum[c] += rk[c]
                rank_logprod[c] += np.log(rk[c] + 1e-12)
        scores = {
            "RANK (product)": rank_logprod,
            "EXCLUDE (admissibility)": {c: np.log(excl_prod[c] + 1e-12) for c in cands},
            "VECTOR (exclude x rank)": {c: np.log(excl_prod[c] * rank_sum[c] + 1e-12) for c in cands},
        }
        for m in MODES:
            order = sorted(cands, key=lambda c: -scores[m][c])
            acc[m][2] += 1
            acc[m][0] += int(order[0] == w)
            acc[m][1] += int(w in order[:KREC])
    return {m: (a[0] / a[2], a[1] / a[2]) for m, a in acc.items()}


def main():
    print("=" * 98)
    print("PRODUCT vs ADMISSIBILITY vs VECTOR — combine over absolute/relational/dynamic DTW channels.")
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
    cands, by = [], {}
    for w, exs in pool.items():
        if len(exs) >= 16:
            by[w] = exs[:24]; cands.append(w)
    cands.sort()
    print(f"  {len(cands)}-way (chance {100/len(cands):.0f}%); precomputing representations...", flush=True)
    reps = {w: [representations(g) for g in by[w]] for w in cands}
    cents = {w: [spectral_centroid(g) for g in by[w]] for w in cands}

    en1, te1 = {}, []
    for w in cands:
        order = np.argsort(cents[w]); n = len(order)
        en1[w] = [reps[w][i] for i in order[:n // 2][:ENROL_CAP]]
        hi = order[n // 2:]; nho = max(2, len(hi) // 4)
        te1 += [(w, reps[w][i]) for i in hi[-nho:]]
    en2, te2 = {}, []
    for w in cands:
        idx = list(range(len(reps[w]))); cut = max(ENROL_CAP, len(idx) - max(2, len(idx) // 4))
        en2[w] = [reps[w][i] for i in idx[:ENROL_CAP]]
        te2 += [(w, reps[w][i]) for i in idx[cut:]]

    res1 = evaluate(en1, te1, cands)
    res2 = evaluate(en2, te2, cands)

    for title, res in ((f"CROSS-SPEAKER gap ({len(te1)} held-out)", res1),
                       (f"SAME/MIXED split ({len(te2)} held-out)", res2)):
        print(f"\n  {title}")
        print(f"    {'combine mode':<30}{'top-1':>9}{'top-6 recall':>15}")
        for m in MODES:
            t1, tk = res[m]
            print(f"    {m:<30}{t1*100:>8.0f}%{tk*100:>14.0f}%")

    print("\n" + "=" * 98)
    rank_cs, rank_sm = res1["RANK (product)"], res2["RANK (product)"]
    vec_cs, vec_sm = res1["VECTOR (exclude x rank)"], res2["VECTOR (exclude x rank)"]
    exc_cs = res1["EXCLUDE (admissibility)"]
    if vec_cs[0] > rank_cs[0] + 0.02 or vec_cs[1] > rank_cs[1] + 0.02 or exc_cs[0] > rank_cs[0] + 0.02:
        print(f"  ADMISSIBILITY HELPS: keeping the EXCLUDE axis (a channel abstains when it can't discriminate")
        print(f"  rather than casting a wrong positive vote) beats the bare rank product -- VECTOR top-1 {vec_cs[0]*100:.0f}%/top-6")
        print(f"  {vec_cs[1]*100:.0f}% cross-speaker vs RANK {rank_cs[0]*100:.0f}%/{rank_cs[1]*100:.0f}%. The VTL-carrying absolute channel stops dragging")
        print("  the truth down cross-speaker; this is why the agent's recogniser is exclusion-calibrated, not a")
        print("  bare positive product. We were using the wrong combine -- admissibility is the right one.")
    else:
        print(f"  the combines are close here: VECTOR {vec_cs[0]*100:.0f}/{vec_cs[1]*100:.0f}, EXCLUDE {exc_cs[0]*100:.0f}/{exc_cs[1]*100:.0f}, RANK {rank_cs[0]*100:.0f}/{rank_cs[1]*100:.0f}")
        print("  (top-1/top-6 cross-speaker) -- the admissibility gate matters most when a channel is confidently")
        print("  WRONG; with DTW 1-NN channels the wrong votes are weak, so the gate's gain is modest here.")
    print("=" * 98)


if __name__ == "__main__":
    main()
