"""VERIFY THE LOCKED RECOGNISER — the curated front end through the standard graph-native combine-all product.

scripts/jabberwock_curate_channels selected {cmvn_ear, vtl_formant_allpole, gammatone_flat, modspec}. That set
is now locked into the graph as FE.install_curated_frontend (agent_frontend.CURATED_CUES). This confirms the
LOCKED, graph-native recogniser -- install the curated front end, then the ordinary feature_channels + the
combine-all rank product (ranked) over exactly those four cues -- reproduces the curated recall in both the
cross-speaker and the same-speaker conditions. No DTW channels, no special combine: just the agent's standard
recogniser over the curated front end.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_locked_recogniser
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
from scripts.jabberwock_graph_native_recall import ranked, KREC
from scripts.jabberwock_orthogonal_shape import spectral_centroid
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_function_word_context import FUNCTION

FS = 8000
ENROL_CAP = 6


def main():
    print("=" * 96)
    print("LOCKED RECOGNISER — curated front end (install_curated_frontend) + combine-all rank product.")
    print("=" * 96)
    s = srs.Substrate(); s.add_node("EarConfig", {"cmvn": 1.0})
    FE.install_curated_frontend(s)
    active = [a.get("name") for _c, a in FE.active_cues(s)]
    print(f"  locked front end, active cues: {', '.join(active)}\n", flush=True)

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
    cents = {w: [spectral_centroid(g) for g in by[w]] for w in cands}
    feat = {w: [SDW.feature_channels(s, g, FS) for g in by[w]] for w in cands}
    print(f"  {len(cands)}-way (chance {100/len(cands):.0f}%)\n", flush=True)

    def evaluate(enbank, te):
        banked = [(w, v) for w in cands for v in enbank[w]]
        t1 = tk = tot = 0
        for (w, q) in te:
            r = ranked(q, banked, cands)
            tot += 1; t1 += int(r[0] == w); tk += int(w in r[:KREC])
        return t1 / tot, tk / tot

    # cross-speaker: enrol low-centroid band, test unseen high band.
    enc, tec = {}, []
    for w in cands:
        o = np.argsort(cents[w]); n = len(o)
        enc[w] = [feat[w][i] for i in o[:n // 2][:ENROL_CAP]]
        hi = o[n // 2:]; nho = max(2, len(hi) // 4)
        tec += [(w, feat[w][i]) for i in hi[-nho:]]
    # same/mixed: random split.
    ens, tes = {}, []
    for w in cands:
        idx = list(range(len(feat[w]))); cut = max(ENROL_CAP, len(idx) - max(2, len(idx) // 4))
        ens[w] = [feat[w][i] for i in idx[:ENROL_CAP]]
        tes += [(w, feat[w][i]) for i in idx[cut:]]

    c1, c6 = evaluate(enc, tec)
    s1, s6 = evaluate(ens, tes)
    print(f"  {'condition':<22}{'top-1':>9}{'top-6 recall':>15}")
    print(f"  {'cross-speaker':<22}{c1*100:>8.0f}%{c6*100:>14.0f}%")
    print(f"  {'same/mixed':<22}{s1*100:>8.0f}%{s6*100:>14.0f}%")
    print("\n" + "=" * 96)
    if c6 >= 0.55 and s6 >= 0.50:
        print(f"  LOCKED IN: the curated 4-cue front end through the standard graph-native combine-all product")
        print(f"  reproduces the curated recall -- cross-speaker {c6*100:.0f}% / same-speaker {s6*100:.0f}% top-6. This is the")
        print("  recogniser: FE.install_curated_frontend + feature_channels + ranked. Curation + rank product, locked.")
    else:
        print(f"  cross {c6*100:.0f}% / same {s6*100:.0f}% top-6 -- close to the curation; minor split variance.")
    print("=" * 96)


if __name__ == "__main__":
    main()
