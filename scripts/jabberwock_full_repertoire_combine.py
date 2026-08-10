"""SCALE TO THE FULL CUE REPERTOIRE with the VECTOR combine — where admissibility earns its keep.

The 3-channel test showed the bare RANK product beats admissibility when every channel is well-behaved. The
predicted regime where the VECTOR no-collapse combine (Prod exclude * Sum rank) wins is MANY heterogeneous
cues, some CONFIDENTLY WRONG in a given context -- the exclude gate suppresses their noisy positive votes while
the rank sum still orders the survivors. So scale to the agent's WHOLE front end: every active FrontEnd cue
(gammatone, fft, allpole, the sharp ears, cmvn, the VTL formants, cs_ear, formant_relation, manner_voicing,
f0, modspec, landmark, transition, correlogram) as a cosine channel, PLUS the orthogonal relational + dynamic
DTW channels. Cross-speaker, the VTL-carrying cues are confidently wrong -- exactly what admissibility is for.

Compare RANK (product), EXCLUDE (admissibility), VECTOR (exclude x rank) over the FULL repertoire, both
conditions. The claim from the previous run's rule: at repertoire scale, VECTOR >= RANK (the gate now bites).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_full_repertoire_combine
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
import domains.agent_frontend as FE
from domains.many_settings_recognizer import (likelihood_from_distances,
                                              exclusion_likelihood_from_distances)
from scripts.jabberwock_key_shape_relaxation import dtw
from scripts.jabberwock_orthogonal_shape import representations, spectral_centroid
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_function_word_context import FUNCTION

FS = 8000
KREC = 6
ENROL_CAP = 6
MODES = ["RANK (product)", "EXCLUDE (admissibility)", "VECTOR (exclude x rank)"]


def full_frontend():
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    fe = FE.install_frontend(s)
    for et in ("has_cue", "repertoire"):
        for c in s.neighbours(fe, et):
            s.set_attr(c, "active", 1.0)
    try:
        FE.activate_correlogram_ear(s)
    except Exception:
        pass
    return s


def cos_dist(q, Xc, words_arr, cands):
    qn = q / (np.linalg.norm(q) + 1e-9)
    Xn = Xc / (np.linalg.norm(Xc, axis=1, keepdims=True) + 1e-9)
    d = 1.0 - Xn @ qn
    return {w: float(d[words_arr == w].min()) if (words_arr == w).any() else np.inf for w in cands}


def dtw_dist(q_traj, banked_trajs, cands):
    return {w: min((dtw(q_traj, b) for b in banked_trajs[w]), default=np.inf) for w in cands}


def main():
    print("=" * 98)
    print("FULL CUE REPERTOIRE + VECTOR combine — does admissibility win once cues are many + heterogeneous?")
    print("=" * 98)
    s = full_frontend()
    cue_names = [a.get("name") for _c, a in FE.active_cues(s)]
    print(f"  {len(cue_names)} active FrontEnd cosine cues + relational + dynamic DTW = {len(cue_names)+2} channels")
    print(f"  cues: {', '.join(cue_names)}\n", flush=True)

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
            by[w] = exs[:22]; cands.append(w)
    cands.sort()
    print(f"  {len(cands)}-way (chance {100/len(cands):.0f}%); extracting full-repertoire features...", flush=True)

    def feats(g):
        fe = SDW.feature_channels(s, np.asarray(g, dtype=np.float64), FS)   # list of cue vectors
        rp = representations(g)
        return fe, rp["relational"], rp["dynamic"]

    allf = {w: [feats(g) for g in by[w]] for w in cands}
    cents = {w: [spectral_centroid(g) for g in by[w]] for w in cands}
    NC = len(allf[cands[0]][0][0])                       # number of cosine cue channels

    def split_cross():
        en, te = {}, []
        for w in cands:
            o = np.argsort(cents[w]); n = len(o)
            en[w] = [allf[w][i] for i in o[:n // 2][:ENROL_CAP]]
            hi = o[n // 2:]; nho = max(2, len(hi) // 4)
            te += [(w, allf[w][i]) for i in hi[-nho:]]
        return en, te

    def split_mixed():
        en, te = {}, []
        for w in cands:
            idx = list(range(len(allf[w]))); cut = max(ENROL_CAP, len(idx) - max(2, len(idx) // 4))
            en[w] = [allf[w][i] for i in idx[:ENROL_CAP]]
            te += [(w, allf[w][i]) for i in idx[cut:]]
        return en, te

    def evaluate(en, te):
        # pre-stack banked cosine cue vectors per channel + per-word trajectory lists.
        Xc = [np.stack([rec[0][ci] for w in cands for rec in en[w]]) for ci in range(NC)]
        wofc = np.array([w for w in cands for _rec in en[w]])
        rel_bank = {w: [rec[1] for rec in en[w]] for w in cands}
        dyn_bank = {w: [rec[2] for rec in en[w]] for w in cands}
        acc = {m: [0, 0, 0] for m in MODES}
        for (w, rec) in te:
            fe, rel, dyn = rec
            dist_dicts = [cos_dist(fe[ci], Xc[ci], wofc, cands) for ci in range(NC)]
            dist_dicts.append(dtw_dist(rel, rel_bank, cands))
            dist_dicts.append(dtw_dist(dyn, dyn_bank, cands))
            excl_prod = {c: 1.0 for c in cands}; rank_sum = {c: 0.0 for c in cands}
            rank_logp = {c: 0.0 for c in cands}
            for d in dist_dicts:
                ex = exclusion_likelihood_from_distances(d); rk = likelihood_from_distances(d)
                for c in cands:
                    excl_prod[c] *= ex[c]; rank_sum[c] += rk[c]; rank_logp[c] += np.log(rk[c] + 1e-12)
            scores = {
                "RANK (product)": rank_logp,
                "EXCLUDE (admissibility)": {c: np.log(excl_prod[c] + 1e-12) for c in cands},
                "VECTOR (exclude x rank)": {c: np.log(excl_prod[c] * rank_sum[c] + 1e-12) for c in cands},
            }
            for m in MODES:
                order = sorted(cands, key=lambda c: -scores[m][c])
                acc[m][2] += 1; acc[m][0] += int(order[0] == w); acc[m][1] += int(w in order[:KREC])
        return {m: (a[0] / a[2], a[1] / a[2]) for m, a in acc.items()}

    res_cs = evaluate(*split_cross())
    res_sm = evaluate(*split_mixed())

    for title, res in ((f"CROSS-SPEAKER gap", res_cs), (f"SAME/MIXED split", res_sm)):
        print(f"\n  {title} ({len(cue_names)+2} channels)")
        print(f"    {'combine mode':<30}{'top-1':>9}{'top-6 recall':>15}")
        for m in MODES:
            t1, tk = res[m]
            print(f"    {m:<30}{t1*100:>8.0f}%{tk*100:>14.0f}%")

    print("\n" + "=" * 98)
    rk = res_cs["RANK (product)"]; vc = res_cs["VECTOR (exclude x rank)"]; ex = res_cs["EXCLUDE (admissibility)"]
    if vc[1] > rk[1] + 0.02 or vc[0] > rk[0] + 0.02:
        print(f"  AT REPERTOIRE SCALE THE GATE BITES: VECTOR {vc[0]*100:.0f}%/{vc[1]*100:.0f}% beats RANK {rk[0]*100:.0f}%/{rk[1]*100:.0f}% cross-speaker")
        print("  (top-1/top-6). With many cues, the VTL-carrying ones are confidently WRONG cross-speaker and the")
        print("  bare product propagates their noisy votes; the exclude gate abstains them while the rank sum orders")
        print("  survivors. The agent's exclusion-calibrated vector combine is the RIGHT combine at scale -- as designed.")
    else:
        print(f"  VECTOR {vc[0]*100:.0f}/{vc[1]*100:.0f} vs RANK {rk[0]*100:.0f}/{rk[1]*100:.0f} vs EXCLUDE {ex[0]*100:.0f}/{ex[1]*100:.0f} (top-1/top-6 cross-speaker): even")
        print("  at repertoire scale the gate did not overtake the product for recall -- the wrong cues here are")
        print("  diffusely wrong (low separability) so they already abstain under rank softmax; the product holds.")
    print("=" * 98)


if __name__ == "__main__":
    main()
