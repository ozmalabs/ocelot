"""CURATE the best channel subset (greedy forward selection) and report it to be LOCKED IN.

The repertoire findings: the lever is CURATION + the rank product, not channel-count + gating. So select the
best subset by GREEDY FORWARD SELECTION over all candidate channels -- 17 FrontEnd cosine cues + absolute /
relational / dynamic DTW -- under the RANK product, maximising mean top-6 recall across BOTH conditions
(cross-speaker AND same-speaker). A channel that earns its place must help in both; that cross-condition
agreement is the guard against in-sample overfit. Each channel's per-token rank-likelihoods are cached once,
so the subset search is just summing cached evidence.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_curate_channels
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
from domains.many_settings_recognizer import likelihood_from_distances
from scripts.jabberwock_key_shape_relaxation import dtw
from scripts.jabberwock_orthogonal_shape import representations, spectral_centroid
from scripts.jabberwock_full_repertoire_combine import full_frontend, cos_dist
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_function_word_context import FUNCTION

FS = 8000
KREC = 6
ENROL_CAP = 6
MAX_KEEP = 8


def main():
    print("=" * 98)
    print("CURATE the best channel subset (greedy forward selection, rank product, both conditions).")
    print("=" * 98)
    s = full_frontend()
    cue_names = [a.get("name") for _c, a in FE.active_cues(s)]
    channels = list(cue_names) + ["~absolute", "~relational", "~dynamic"]   # ~ = DTW trajectory channel
    print(f"  {len(channels)} candidate channels ({len(cue_names)} cosine cues + 3 DTW)\n", flush=True)

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
    print(f"  {len(cands)}-way (chance {100/len(cands):.0f}%); extracting features...", flush=True)

    def feats(g):
        fe = SDW.feature_channels(s, np.asarray(g, dtype=np.float64), FS)
        rp = representations(g)
        return fe, rp["absolute"], rp["relational"], rp["dynamic"]

    allf = {w: [feats(g) for g in by[w]] for w in cands}
    cents = {w: [spectral_centroid(g) for g in by[w]] for w in cands}
    NC = len(allf[cands[0]][0][0])

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

    def cache_likelihoods(en, te):
        """per test token -> per channel -> rank-likelihood dict over candidates (computed ONCE)."""
        Xc = [np.stack([rec[0][ci] for w in cands for rec in en[w]]) for ci in range(NC)]
        wof = np.array([w for w in cands for _r in en[w]])
        relb = {w: [r[2] for r in en[w]] for w in cands}
        dynb = {w: [r[3] for r in en[w]] for w in cands}
        absb = {w: [r[1] for r in en[w]] for w in cands}
        traj = {"~absolute": absb, "~relational": relb, "~dynamic": dynb}
        trajq = {"~absolute": 1, "~relational": 2, "~dynamic": 3}
        out = []
        for (w, rec) in te:
            liks = {}
            for ci in range(NC):
                d = cos_dist(rec[0][ci], Xc[ci], wof, cands)
                liks[channels[ci]] = likelihood_from_distances(d)
            for nm, bank in traj.items():
                q = rec[trajq[nm]]
                d = {c: min((dtw(q, b) for b in bank[c]), default=np.inf) for c in cands}
                liks[nm] = likelihood_from_distances(d)
            out.append((w, liks))
        return out

    cache = {"cross": cache_likelihoods(*split_cross()), "same": cache_likelihoods(*split_mixed())}

    def score(subset, cond):
        t1 = tk = 0
        for (w, liks) in cache[cond]:
            logp = {c: 0.0 for c in cands}
            for ch in subset:
                lk = liks[ch]
                for c in cands:
                    logp[c] += np.log(lk[c] + 1e-12)
            order = sorted(cands, key=lambda c: -logp[c])
            t1 += int(order[0] == w); tk += int(w in order[:KREC])
        n = len(cache[cond])
        return t1 / n, tk / n

    def objective(subset):
        _t1c, t6c = score(subset, "cross"); _t1s, t6s = score(subset, "same")
        return 0.5 * (t6c + t6s)

    # GREEDY FORWARD SELECTION on mean top-6 recall.
    selected, remaining = [], list(channels)
    best = 0.0
    print("  greedy forward selection (mean top-6 recall, both conditions):")
    while remaining and len(selected) < MAX_KEEP:
        scored = [(objective(selected + [ch]), ch) for ch in remaining]
        scored.sort(reverse=True)
        gain, ch = scored[0]
        if gain <= best + 0.003:
            break
        selected.append(ch); remaining.remove(ch); best = gain
        t1c, t6c = score(selected, "cross"); t1s, t6s = score(selected, "same")
        print(f"    + {ch:<22} -> mean top-6 {best*100:>4.0f}%   (cross {t6c*100:.0f}/{t1c*100:.0f}  same {t6s*100:.0f}/{t1s*100:.0f})")

    t1c, t6c = score(selected, "cross"); t1s, t6s = score(selected, "same")
    fa1c, fa6c = score(channels, "cross"); fa1s, fa6s = score(channels, "same")
    print(f"\n  CURATED SUBSET ({len(selected)}): {', '.join(selected)}")
    print(f"    {'':<26}{'cross top-1/6':>16}{'same top-1/6':>16}")
    print(f"    {'curated':<26}{f'{t1c*100:.0f}% / {t6c*100:.0f}%':>16}{f'{t1s*100:.0f}% / {t6s*100:.0f}%':>16}")
    print(f"    {'full repertoire (all 20)':<26}{f'{fa1c*100:.0f}% / {fa6c*100:.0f}%':>16}{f'{fa1s*100:.0f}% / {fa6s*100:.0f}%':>16}")
    print("\n  LOCK IN  ->  CURATED_CHANNELS = [")
    for ch in selected:
        print(f"      {ch!r},")
    print("  ]")
    print("=" * 98)


if __name__ == "__main__":
    main()
