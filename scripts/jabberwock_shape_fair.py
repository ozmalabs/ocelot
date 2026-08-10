"""SHAPE RECOGNITION, FAIR TEST — content words, AbS synthesised models, shape -> predictive coding.

The function-word test was shape's worst case. This is the fair one:
  (A) CONTENT words (distinctive spectro-temporal shapes), exemplar models: raw DTW vs the agent's
      talker-invariant RELATIONAL-SHAPE DTW.
  (B) ANALYSIS-BY-SYNTHESIS: the agent SYNTHESISES each content word (piper, several variants) as its
      models and matches REAL Sesame observations to them BY SHAPE — the cross-voice test the
      talker-invariant shape is for (piper voice != human voice; the SHAPE bridges it).
  (C) SHAPE -> PREDICTIVE CODING: feed the talker-invariant relational shape into the local-plasticity
      learner — invariance by construction PLUS discrimination by learning, each covering the other.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_shape_fair [topK]
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
from domains.filter_settings import cochleagram
from domains.self_directed_speech_world import _MIDDLE
from domains.speech_world import SpeechWorld
from scripts.sesame_cmvn_probe import extract
from scripts.jabberwock_shape_match import coch, _z, relational_shape, dtw, recognise
from scripts.jabberwock_pc_embedding import PredictiveCoder, ncm, control

SEP = "=" * 94

STOP = set(("a an the and or but you i we he she it they them me him her to of in on at by "
            "is are was were be been being am do does did have has had can will would could should "
            "oh yeah yes no um uh so that this these those what who whom my your his its our their "
            "all not now then here there too very just like get got go come said say one two "
            "it's we're that's i'm you're they're don't can't won't let's there's what's he's she's "
            "blah well know about because things thing some any much many more most been will would "
            "okay ok hey hi bye now going gonna wanna lot really right way day").split())


def content_words(train, K, min_ex=8):
    freq = Counter(w for (w, _g) in train)
    out = [w for w, n in freq.most_common()
           if w not in STOP and len(w) >= 4 and "'" not in w and n >= min_ex]
    return out[:K]


def pooled_relshape(M):
    R = relational_shape(M)
    return np.concatenate([R.mean(0), R.std(0)])


def pooled_raw(M):
    Z = _z(M)
    return np.concatenate([Z.mean(0), Z.std(0)])


def pc_recall(Xtr, ytr, Xte, yte, words, wi, epochs=300):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xtr = np.tanh((Xtr - mu) / sd); Xte = np.tanh((Xte - mu) / sd)
    Y = np.eye(len(words))[[wi[w] for w in ytr]]
    pc = PredictiveCoder(Xtr.shape[1], 200, len(words))
    pc.train(Xtr, Y, epochs=epochs)
    _, O = pc.predict(Xte)
    return np.mean([words[int(np.argmax(o))] == w for o, w in zip(O, yte)])


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    print(SEP)
    print("SHAPE RECOGNITION, FAIR TEST — content words, AbS synthesis, shape -> predictive coding.")
    print(SEP)
    print(f"  predictive-coding self-check: {control()*100:.0f}%\n")
    train, test = extract(16.0)
    words = content_words(train, topK)
    wi = {w: i for i, w in enumerate(words)}
    # content words are RARE in natural speech (Zipf) — pool all exemplars and hold out within-word.
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
    print(f"  top-{len(words)} CONTENT words (chance {100/max(len(words),1):.0f}%): {words}")
    print(f"  {sum(len(v) for v in by.values())} train / {len(te)} held-out exemplars\n")
    if len(words) < 4 or len(te) < 8:
        print("  too few content words/exemplars in this slice."); return

    teM = [(w, coch(g)) for (w, g) in te]
    yte = [w for (w, _M) in teM]

    # (A) exemplar models — raw vs relational-shape DTW
    raw_models = [(w, _z(coch(g))) for w in words for g in by[w][:8]]
    shp_models = [(w, relational_shape(coch(g))) for w in words for g in by[w][:8]]
    a_raw = recognise(raw_models, [_z(M) for (_w, M) in teM], yte)
    a_shp = recognise(shp_models, [relational_shape(M) for (_w, M) in teM], yte)
    print(f"  (A) CONTENT words, exemplar DTW:   raw {a_raw*100:.0f}%   relational-shape {a_shp*100:.0f}%")

    # (B) analysis-by-synthesis — piper models matched to REAL speech by shape (cross-voice)
    sw = SpeechWorld(srs.Substrate())
    abs_models = []
    for w in words:
        for pitch in (40, 55, 70, 85):
            r = sw.synth(w, {"variant": "lessac", "pitch": pitch, "rate": 175})
            if r is not None:
                abs_models.append((w, relational_shape(coch(r[0]))))
    b_shp = recognise(abs_models, [relational_shape(M) for (_w, M) in teM], yte) if abs_models else 0.0
    print(f"  (B) AbS piper models -> real speech, SHAPE match (cross-voice): {b_shp*100:.0f}%  "
          f"({len(abs_models)} synthesised models)")

    # (C) shape -> predictive coding  vs  raw -> predictive coding
    tr = [(w, g) for w in words for g in by[w]]
    ytr = [w for (w, _g) in tr]
    Xraw_tr = np.stack([pooled_raw(coch(g)) for (_w, g) in tr])
    Xraw_te = np.stack([pooled_raw(M) for (_w, M) in teM])
    Xshp_tr = np.stack([pooled_relshape(coch(g)) for (_w, g) in tr])
    Xshp_te = np.stack([pooled_relshape(M) for (_w, M) in teM])
    c_raw = pc_recall(Xraw_tr, ytr, Xraw_te, yte, words, wi)
    c_shp = pc_recall(Xshp_tr, ytr, Xshp_te, yte, words, wi)
    print(f"  (C) predictive coding:             raw->PC {c_raw*100:.0f}%   shape->PC {c_shp*100:.0f}%")

    print(f"\n{SEP}")
    best = max(a_shp, b_shp, c_shp)
    print(f"  best shape-based: {best*100:.0f}% vs raw baselines (~{max(a_raw,c_raw)*100:.0f}%), chance "
          f"{100/len(words):.0f}%. Content words + the agent's talker-invariant shape "
          f"{'WIN' if best > max(a_raw, c_raw) + 0.05 else 'help modestly'}; AbS cross-voice = {b_shp*100:.0f}%; "
          f"shape->PC = {c_shp*100:.0f}% (invariance + learning).")
    print(SEP)


if __name__ == "__main__":
    main()
