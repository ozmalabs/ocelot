"""THE LEARNED X-VECTOR SPEAKER MODEL — x-vector architecture, trained by PREDICTIVE CODING (no backprop).

The whole arc converged here: a learned non-linear speaker-invariant embedding at scale. But gradient
descent is forbidden as un-cognitive, so this is the x-vector RECIPE (frame features -> statistics
pooling [mean;std] -> a discriminative embedding, recognised open-set by nearest-embedding) trained by
the cortical local rule (predictive coding, control-validated 100%, NO backprop). Trained at SCALE on
the big diverse 5-show corpus over MANY words (so the embedding learns general speaker-invariant
structure), then the embedding is transferred OPEN-SET to the held-out CONTENT words and they are
recognised by nearest-embedding. The test: does a learned embedding at scale finally clear the ~21%
wall every hand-built method (invariant shape, key contraction, keyspace prior, navigation) plateaued
against on this diversity?

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_xvector_pc [trainK] [contentK]
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
from scripts.jabberwock_shape_pc_paired import content_words
from scripts.jabberwock_enacts_xvector import frame_feats
from scripts.jabberwock_pc_embedding import PredictiveCoder, control


def pool(seg):
    """x-vector statistics pooling: mean+std of frame features (cochleagram + delta) over time."""
    F = frame_feats(seg)
    return np.concatenate([F.mean(0), F.std(0)])


def _l2(X):
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)


def ncm(Etr, ytr, Ete, yte):
    classes = sorted(set(ytr))
    Etr, Ete = _l2(Etr), _l2(Ete)
    M = _l2(np.stack([Etr[np.asarray(ytr) == c].mean(0) for c in classes]))
    pred = [classes[int(np.argmax(M @ q))] for q in Ete]
    return float(np.mean([p == w for p, w in zip(pred, yte)]))


def main():
    trainK = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    contentK = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    print("=" * 98)
    print("LEARNED X-VECTOR SPEAKER MODEL — x-vector architecture, predictive coding (no backprop), at scale.")
    print("=" * 98)
    print(f"  predictive-coding self-check: {control()*100:.0f}%\n")
    train, test = multi_extract()
    freq = Counter(w for (w, _g) in train)

    # the EMBEDDING is trained on the trainK most frequent words (scale: many classes, many speakers).
    emb_words = [w for w, n in freq.most_common() if len(w) >= 2 and n >= 15][:trainK]
    ew = {w: i for i, w in enumerate(emb_words)}
    Xtr, ytr = [], []
    for (w, g) in train:
        if w in ew and ytr.count(w) < 60:
            Xtr.append(pool(g)); ytr.append(w)
    Xtr = np.stack(Xtr)
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xn = np.tanh((Xtr - mu) / sd)
    Y = np.eye(len(emb_words))[[ew[w] for w in ytr]]
    print(f"  training the embedding on {len(emb_words)} words, {len(Xtr)} utterances (predictive coding)...",
          flush=True)
    pc = PredictiveCoder(Xn.shape[1], 256, len(emb_words))
    pc.train(Xn, Y, epochs=120, T=18, lr_v=0.2, lr_w=0.04, bs=128)

    def embed(segs):
        X = np.tanh((np.stack([pool(g) for g in segs]) - mu) / sd)
        return pc.predict(X)[0]                      # the penultimate embedding (open-set transferable)

    # OPEN-SET test on the held-out CONTENT words (mostly NOT among the training words).
    cwords = content_words(train, contentK, min_ex=12)
    wi = set(cwords)
    allex = {}
    for (w, g) in train + test:
        if w in wi:
            allex.setdefault(w, []).append(g)
    by, te = {}, []
    for w in cwords:
        ex = allex[w]; nho = max(2, len(ex) // 5)
        by[w] = ex[:-nho]; te += [(w, g) for g in ex[-nho:]]
    overlap = len(set(cwords) & set(emb_words))
    print(f"  enrol/test on {len(cwords)} CONTENT words ({len(te)} held-out, chance {100/len(cwords):.0f}%; "
          f"{overlap}/{len(cwords)} were in the embedding's training set — mostly OPEN-SET)\n")

    enroll = [(w, g) for w in cwords for g in by[w]]
    yE = [w for (w, _g) in enroll]
    Een = embed([g for (_w, g) in enroll])
    yT = [w for (w, _g) in te]
    Ete = embed([g for (_w, g) in te])
    # baselines in the same pooled space (no learning)
    Rtr = np.stack([pool(g) for (_w, g) in enroll]); Rte = np.stack([pool(g) for (_w, g) in te])

    raw = ncm(Rtr, yE, Rte, yT)
    learned = ncm(Een, yE, Ete, yT)
    print(f"  {'raw pooled features (no learning)':<46} {raw*100:>5.0f}%")
    print(f"  {'LEARNED x-vector embedding (predictive coding)':<46} {learned*100:>5.0f}%")

    print("\n" + "=" * 98)
    if learned > max(raw, 0.21) + 0.03:
        print(f"  IT CLEARS THE WALL: the learned embedding at scale {learned*100:.0f}% beats raw {raw*100:.0f}% and the")
        print("  ~21% hand-built ceiling — a non-linear speaker-invariant representation, learned the cortical way")
        print("  (predictive coding, no backprop), is the lever the arc pointed at. Scale + a learned model wins.")
    elif learned > raw + 0.03:
        print(f"  the learned embedding helps ({learned*100:.0f}% > raw {raw*100:.0f}%) but does not clear the ~21%")
        print("  invariant ceiling: at THIS scale (minutes, 256 hidden units, local learning) the embedding is real")
        print("  but small. The x-vector wins at its true scale — thousands of hours, large capacity — which this is not.")
    else:
        print(f"  learned {learned*100:.0f}% ~ raw {raw*100:.0f}%: predictive coding at this scale did not yet extract a")
        print("  speaker-invariant embedding stronger than the raw pooling on this diversity — capacity/data bound,")
        print("  the honest endpoint: the learned model needs the scale biology spends, which we cannot reach here.")
    print("=" * 98)


if __name__ == "__main__":
    main()
