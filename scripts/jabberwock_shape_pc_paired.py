"""SHAPE x PREDICTIVE CODING, PAIRED — invariance by construction FED INTO discrimination by learning.

Both at once: more hours (multi-source) AND the proper pairing. The talker-invariant relational shape
gives speaker-invariance for free; predictive coding (local plasticity, no backprop) gives
discrimination. Feed the shape into the learner and they cover each other's weakness. Compared on
content words from a bigger multi-show set:
  raw-DTW, shape-DTW (matching) ; raw->PC, shape->PC (learning) ; and shape is the agent's own
  talker-invariant relational_shape (rank profile + self-similarity).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_shape_pc_paired [topK]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_shape_fair import (STOP, coch, _z, relational_shape, recognise,
                                           pooled_relshape, pooled_raw, pc_recall)
from scripts.jabberwock_pc_embedding import control

SEP = "=" * 94


def content_words(train, K, min_ex=10):
    freq = Counter(w for (w, _g) in train)
    out = [w for w, n in freq.most_common()
           if w not in STOP and len(w) >= 4 and "'" not in w and n >= min_ex]
    return out[:K]


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print(SEP)
    print("SHAPE x PREDICTIVE CODING, PAIRED — more hours + invariance-by-construction into learning.")
    print(SEP)
    print(f"  predictive-coding self-check: {control()*100:.0f}%\n")
    train, test = multi_extract()
    print(f"  multi-source corpus: {len(train)} train / {len(test)} test tokens")
    words = content_words(train, topK)
    wi = {w: i for i, w in enumerate(words)}
    allex = {}
    for (w, g) in train + test:
        if w in wi:
            allex.setdefault(w, []).append(g)
    by, te = {}, []
    for w in words:
        ex = allex[w]
        nho = max(2, len(ex) // 5)
        by[w] = ex[:-nho]
        te += [(w, g) for g in ex[-nho:]]
    print(f"  top-{len(words)} CONTENT words (chance {100/max(len(words),1):.0f}%, "
          f"{sum(len(v) for v in by.values())} train / {len(te)} held-out): {words}\n")
    if len(words) < 5 or len(te) < 20:
        print("  still too few content words/exemplars — need more hours."); return

    teM = [(w, coch(g)) for (w, g) in te]
    yte = [w for (w, _M) in teM]

    # matching (no learning): raw vs talker-invariant shape, by DTW
    raw_models = [(w, _z(coch(g))) for w in words for g in by[w][:10]]
    shp_models = [(w, relational_shape(coch(g))) for w in words for g in by[w][:10]]
    dtw_raw = recognise(raw_models, [_z(M) for (_w, M) in teM], yte)
    dtw_shp = recognise(shp_models, [relational_shape(M) for (_w, M) in teM], yte)

    # learning: raw->PC vs shape->PC
    tr = [(w, g) for w in words for g in by[w]]
    ytr = [w for (w, _g) in tr]
    Xraw_tr = np.stack([pooled_raw(coch(g)) for (_w, g) in tr])
    Xraw_te = np.stack([pooled_raw(M) for (_w, M) in teM])
    Xshp_tr = np.stack([pooled_relshape(coch(g)) for (_w, g) in tr])
    Xshp_te = np.stack([pooled_relshape(M) for (_w, M) in teM])
    pc_raw = pc_recall(Xraw_tr, ytr, Xraw_te, yte, words, wi, epochs=400)
    pc_shp = pc_recall(Xshp_tr, ytr, Xshp_te, yte, words, wi, epochs=400)
    # the pairing: shape ++ raw, both into PC (invariance + raw detail, discriminated by learning)
    Xcat_tr = np.concatenate([Xshp_tr, Xraw_tr], axis=1)
    Xcat_te = np.concatenate([Xshp_te, Xraw_te], axis=1)
    pc_both = pc_recall(Xcat_tr, ytr, Xcat_te, yte, words, wi, epochs=400)

    print(f"  {'':<22}{'DTW (no learning)':>20}{'-> predictive coding':>24}")
    print(f"  {'raw features':<22}{dtw_raw*100:>18.0f}%{pc_raw*100:>23.0f}%")
    print(f"  {'talker-invariant shape':<22}{dtw_shp*100:>18.0f}%{pc_shp*100:>23.0f}%")
    print(f"  {'shape ++ raw (paired)':<22}{'':>20}{pc_both*100:>23.0f}%")

    print(f"\n{SEP}")
    best = max(pc_raw, pc_shp, pc_both)
    chance = 100 / len(words)
    print(f"  best {best*100:.0f}% vs chance {chance:.0f}% (held-out {len(te)} on {len(words)} content words). "
          f"shape-DTW {'>' if dtw_shp > dtw_raw else '<='} raw-DTW; the paired shape++raw -> PC = {pc_both*100:.0f}% "
          f"({'best — invariance + learning compound' if pc_both >= best - 0.001 else 'no compound here'}).")
    print(SEP)


if __name__ == "__main__":
    main()
