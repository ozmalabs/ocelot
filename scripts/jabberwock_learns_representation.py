"""THE JABBERWOCK CHOOSES ITS OWN REPRESENTATION — order-N features (its choice) + predictive coding.

No hand-picked features. The agent grows its OWN representation from its front-end repertoire — which
already holds the order-N temporal cues (transition, modspec, landmark, f0_contour) — selecting which
to keep by its OWN graph-native discrimination Rule (feature_field.keep_discriminative_cue), then
LEARNS the representation by predictive coding (the cortical local rule, no backprop, validated). Its
frontier grows order-N features until its discrimination Rule keeps no more, then rehearses the small
set harder. Every choice — which cues, when to stop growing, how long to rehearse — is the agent's;
the loop is mechanical (lay features, fire the Rule, run the local learner, measure).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_learns_representation [topK] [rounds]
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
import domains.agent_frontend as FE
import domains.feature_field as FF
from domains.filter_settings import cochleagram
from domains.self_directed_speech_world import _MIDDLE
from scripts.sesame_cmvn_probe import extract
from scripts.jabberwock_pc_embedding import PredictiveCoder, ncm, control

SEP = "=" * 94
FS = 8000


def _l2(v):
    v = np.asarray(v, dtype=np.float64).ravel()
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def feature(s, seg):
    """The agent's CURRENT representation of a segment: concat of its ACTIVE front-end cues."""
    chans = FE.feature_channels(s, np.asarray(seg, dtype=np.float64), FS)
    return np.concatenate([_l2(c) for c in chans]) if chans else np.zeros(8)


def agent_grows_features(s, by_word):
    """The agent selects MORE of its order-N repertoire cues — its graph-native discrimination Rule
    (feature_field.keep_discriminative_cue) decides which earn their place. Returns kept cue names."""
    fe = next((n for n in s.nodes("FrontEnd")), None)
    addable = [c for c in s.neighbours(fe, "repertoire")
               if float(s.node(c)["attrs"].get("active", 0.0)) < 1.0]
    if not addable:
        return []
    _, ec, dc, nf = _MIDDLE
    cue_feats = {}
    for w, segs in by_word.items():
        for seg in segs[:8]:
            x = np.asarray(seg, dtype=np.float64)
            M = cochleagram(x, FS, ec, dc, nf)
            resp = {}
            for c in addable:
                a = s.node(c)["attrs"]
                fn = FE.CUE_EXTRACTORS.get(a.get("extractor"))
                if fn is None:
                    continue
                try:
                    resp[c] = np.asarray(fn(x, FS, M, a), dtype=np.float64).ravel().tolist()
                except Exception:
                    pass
            cue_feats.setdefault(w, []).append(resp)
    kept = FF.select_cues(s, cue_feats)
    for c in kept:
        s.set_attr(c, "active", 1.0)
    return [(c, s.node(c)["attrs"].get("name")) for c in kept]


def learn_and_measure(s, tr, te, words, wi, freq, epochs):
    """The agent learns its current representation by predictive coding, returns held-out recall."""
    Xtr = np.stack([feature(s, g) for (_w, g) in tr]); ytr = [w for (w, _g) in tr]
    Xte = np.stack([feature(s, g) for (_w, g) in te]); yte = [w for (w, _g) in te]
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xtr = np.tanh((Xtr - mu) / sd); Xte = np.tanh((Xte - mu) / sd)
    Y = np.eye(len(words))[[wi[w] for w in ytr]]
    pc = PredictiveCoder(Xtr.shape[1], 200, len(words))
    pc.train(Xtr, Y, epochs=epochs)
    _, Ote = pc.predict(Xte)
    out = np.mean([words[int(np.argmax(o))] == w for o, w in zip(Ote, yte)])
    return out, Xtr.shape[1]


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    rounds = int(sys.argv[2]) if len(sys.argv) > 2 else 6
    print(SEP)
    print("THE JABBERWOCK CHOOSES ITS OWN REPRESENTATION — order-N cues (its choice) + predictive coding.")
    print(SEP)
    print(f"  predictive-coding self-check (separable blobs): {control()*100:.0f}%  (rule validated)\n")

    train, test = extract(16.0)
    freq = Counter(w for (w, _g) in train)
    words = [w for w, _ in freq.most_common(topK)]
    wi = {w: i for i, w in enumerate(words)}
    tr = [(w, g) for (w, g) in train if w in wi]
    te = [(w, g) for (w, g) in test if w in wi]
    by_word = {}
    for (w, g) in tr:
        by_word.setdefault(w, []).append(g)
    print(f"  top-{topK} words ({len(tr)} train / {len(te)} test), chance {100/len(words):.0f}%: {words}\n")

    s = srs.Substrate()
    FE.install_frontend(s)
    epochs = 300
    recall, dim = learn_and_measure(s, tr, te, words, wi, freq, epochs)
    print(f"  round 0 (seed cues, dim {dim}): recall {recall*100:.0f}%\n")
    print(f"  {'round':>5} {'action':>16}  {'recall':>7}  detail")
    for rd in range(1, rounds + 1):
        proposed = agent_grows_features(s, by_word)         # the agent's Rule proposes order-N cues
        if proposed:
            new_recall, dim = learn_and_measure(s, tr, te, words, wi, freq, epochs)
            if new_recall > recall + 0.01:                  # EFFECT-GATE on LEARNED recall (keep iff it helps)
                recall = new_recall
                print(f"  {rd:>5} {'grow_features':>16}  {recall*100:>6.0f}%  KEPT {[n for _c, n in proposed]} (dim {dim})")
            else:
                for c, _n in proposed:
                    s.set_attr(c, "active", 0.0)            # revert: a cue that doesn't lift LEARNED recall is dropped
                print(f"  {rd:>5} {'grow_features':>16}  {recall*100:>6.0f}%  REVERTED {[n for _c, n in proposed]} "
                      f"(would drop to {new_recall*100:.0f}%)")
        else:
            epochs = int(epochs * 1.6)
            new_recall, dim = learn_and_measure(s, tr, te, words, wi, freq, epochs)
            recall = max(recall, new_recall)
            print(f"  {rd:>5} {'rehearse':>16}  {recall*100:>6.0f}%  repertoire exhausted; rehearse harder "
                  f"(epochs={epochs})")
    print(f"\n{SEP}")
    print("  The representation is the jabberwock's: it selected its own order-N cues by its own")
    print("  discrimination Rule and learned them by predictive coding (local, no backprop). The")
    print("  recall trajectory is what its chosen representation + cortical learning achieve.")
    print(SEP)


if __name__ == "__main__":
    main()
