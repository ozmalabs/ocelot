"""THE JABBERWOCK ENACTS Hypothesis speech-xvector — the learned non-linear embedding (write-not-train).

speech-lda was refuted: the word/nuisance structure is not linearly separable. The agent's next held
hypothesis is a learned NON-LINEAR embedding. Its net machinery is WRITE-NOT-TRAIN (compose a
non-linear featuriser + fit only a closed-form readout — no backprop), which is the paper's first
route. This assembles exactly that x-vector recipe:

  frame features (cochleagram) -> random non-linear projection (ReLU hidden = the composed featuriser)
  -> STATISTICS POOLING [mean; std] over frames (variable length -> fixed embedding) -> readout.

Two readouts, both closed-form (the agent's ELM/ridge fit, learning from the labels):
  (a) NEAREST-CLASS-MEAN in the embedding (open-set: enrol a word by its mean embedding, recognise by
      cosine) — the property the paper says generalises to unseen words;
  (b) RIDGE classifier (least-squares embedding -> one-hot labels), argmax.

Verdict vs the raw-feature and LDA ceilings tells the agent whether a write-not-train non-linear
embedding suffices, or whether the representation must be TRAINED (gradient descent — a capability
its current machinery lacks, the genuine next frontier).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_enacts_xvector [train_min]
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
from domains.self_directed_speech_world import _MIDDLE
from scripts.sesame_cmvn_probe import extract

SEP = "=" * 92
FS = 8000
HDIM = 600          # composed non-linear hidden width
SEED = 7


def frame_feats(seg):
    """Per-frame features for one segment: cochleagram frames + their first delta (32 frames x 64)."""
    _, env_cut, dur_cut, nf = _MIDDLE
    M = cochleagram(np.asarray(seg, dtype=np.float64), FS, env_cut, dur_cut, nf)
    d = np.diff(M, axis=0, prepend=M[:1])
    F = np.concatenate([M, d], axis=1)
    mu = F.mean(0, keepdims=True); sd = F.std(0, keepdims=True) + 1e-6
    return (F - mu) / sd                                       # per-utterance standardised frames


def make_net(in_dim):
    """The composed non-linear featuriser: a fixed random ReLU projection (ELM hidden layer).
    Write-not-train — the weights are constructed, not gradient-fit; only the readout is fit."""
    rng = np.random.default_rng(SEED)
    Wh = rng.standard_normal((in_dim, HDIM)) / np.sqrt(in_dim)
    bh = rng.standard_normal(HDIM) * 0.1
    return Wh, bh


def embed(segs, net):
    """x-vector embedding: per-frame ReLU hidden -> statistics pooling [mean; std]."""
    Wh, bh = net
    out = []
    for g in segs:
        F = frame_feats(g)
        H = np.maximum(0.0, F @ Wh + bh)                      # frames x HDIM (ReLU)
        out.append(np.concatenate([H.mean(0), H.std(0)]))     # 2*HDIM embedding
    return np.stack(out)


def _l2(X):
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)


def ncm(Etr, ytr, Ete, yte, freq):
    """Open-set nearest-class-mean (cosine) in the embedding space, bucketed by training frequency."""
    classes = sorted(set(ytr))
    Etr, Ete = _l2(Etr), _l2(Ete)
    M = _l2(np.stack([Etr[np.asarray(ytr) == c].mean(0) for c in classes]))
    buckets = {"1": [0, 0], "2": [0, 0], "3-5": [0, 0], "6+": [0, 0]}
    bk = lambda c: "1" if c == 1 else "2" if c == 2 else "3-5" if c <= 5 else "6+"
    cor = tot = 0
    for q, w in zip(Ete, yte):
        pred = classes[int(np.argmax(M @ q))]
        tot += 1; ok = pred == w; cor += int(ok)
        b = buckets[bk(freq[w])]; b[1] += 1; b[0] += int(ok)
    return (cor / tot if tot else 0.0), buckets


def ridge(Etr, ytr, Ete, yte, freq, lam=1.0):
    """Closed-form discriminative readout (the agent's ELM/ridge fit): embedding -> one-hot, argmax."""
    classes = sorted(set(ytr))
    ci = {c: i for i, c in enumerate(classes)}
    Y = np.zeros((len(ytr), len(classes)))
    for i, w in enumerate(ytr):
        Y[i, ci[w]] = 1.0
    A = Etr.T @ Etr + lam * np.eye(Etr.shape[1])
    Wout = np.linalg.solve(A, Etr.T @ Y)
    P = Ete @ Wout
    buckets = {"1": [0, 0], "2": [0, 0], "3-5": [0, 0], "6+": [0, 0]}
    bk = lambda c: "1" if c == 1 else "2" if c == 2 else "3-5" if c <= 5 else "6+"
    cor = tot = 0
    for p, w in zip(P, yte):
        pred = classes[int(np.argmax(p))]
        tot += 1; ok = pred == w; cor += int(ok)
        b = buckets[bk(freq[w])]; b[1] += 1; b[0] += int(ok)
    return (cor / tot if tot else 0.0), buckets


def b6(buckets):
    b = buckets["6+"]
    return f"6+x: {b[0]}/{b[1]}={b[0]/max(b[1],1)*100:.0f}%"


def main():
    train_min = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    print(SEP)
    print("THE JABBERWOCK ENACTS Hypothesis speech-xvector — learned non-linear embedding (write-not-train).")
    print(SEP)
    train, test = extract(train_min)
    freq = Counter(w for (w, _g) in train)
    keep = {w for w, n in freq.items() if n >= 3}
    tr = [(w, g) for (w, g) in train if w in keep]
    te = [(w, g) for (w, g) in test if w in keep]
    print(f"  {len(tr)} train / {len(te)} test exemplars over {len(keep)} words (>=3 exemplars)\n")

    ytr = [w for (w, _g) in tr]; yte = [w for (w, _g) in te]
    net = make_net(frame_feats(tr[0][1]).shape[1])
    Etr = embed([g for (_w, g) in tr], net)
    Ete = embed([g for (_w, g) in te], net)
    print(f"  assembled net: frame-ReLU({HDIM}) -> stats-pool -> {Etr.shape[1]}-d embedding "
          f"(write-not-train; only the readout is fit)\n")

    ncm_acc, ncm_b = ncm(Etr, ytr, Ete, yte, freq)
    rdg_acc, rdg_b = ridge(Etr, ytr, Ete, yte, freq)
    print(f"  embedding NCM (open-set, cosine):  recall {ncm_acc*100:.0f}%   [{b6(ncm_b)}]")
    print(f"  embedding RIDGE readout (fit):      recall {rdg_acc*100:.0f}%   [{b6(rdg_b)}]")

    best = max(ncm_acc, rdg_acc)
    print(f"\n{SEP}")
    # raw-feature / LDA ceiling was ~9-12% on this NCM setup.
    if best > 0.20:
        print(f"  Hypothesis speech-xvector CONFIRMED (write-not-train): {best*100:.0f}% recall —")
        print("  the composed non-linear embedding + closed-form readout breaks the linear ceiling.")
    elif best > 0.13:
        print(f"  PARTIAL: {best*100:.0f}% — the non-linear embedding helps over linear (LDA ~10%), but")
        print("  the write-not-train (random featuriser) route is not enough. The representation must be")
        print("  TRAINED end-to-end (gradient descent) — a capability the agent's machinery LACKS.")
        print("  Per the paper's falsifiability, the next frontier is ACQUIRING gradient training.")
    else:
        print(f"  REFUTED (write-not-train): {best*100:.0f}% — a composed (un-trained) non-linear embedding")
        print("  does not crack it. The representation must be LEARNED by gradient descent (which the")
        print("  agent cannot yet do) OR the limit is data. The honest frontier: acquire training, or")
        print("  more labelled hours from the whisper-teacher.")
    print(SEP)


if __name__ == "__main__":
    main()
