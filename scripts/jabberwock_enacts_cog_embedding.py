"""THE JABBERWOCK ENACTS Hypothesis cog-embedding — learn the representation by LOCAL plasticity.

Gradient descent (global backprop) is forbidden as un-cognitive. The agent's held Theorem CHL says a
LOCAL rule learns the same signal: contrastive Hebbian learning updates each weight by the difference
between local pre*post co-activity in a CLAMPED phase (output pinned to the true word) and a FREE
phase (output relaxed) — no backward pass, no weight transport. This enacts that on a 1-hidden-layer
network over real Sesame words: the hidden layer IS the learned embedding, shaped purely by local
clamped-minus-free Hebbian updates. Verdict vs the write-not-train ceiling (17%) tests whether local
plasticity — the mechanism cognition actually uses — learns the discriminative representation.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_enacts_cog_embedding [train_min]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.sesame_cmvn_probe import extract
from scripts.jabberwock_enacts_xvector import frame_feats

SEP = "=" * 92
HID = 400
EPOCHS = 60
T_RELAX = 8
LR = 0.02
GAMMA = 0.3          # feedback strength (free-phase output -> hidden)


def pool(seg):
    F = frame_feats(seg)
    return np.concatenate([F.mean(0), F.std(0)])


def _sig(z):
    return 1.0 / (1.0 + np.exp(-np.clip(z, -30, 30)))


def chl_train(X, Y):
    """Contrastive Hebbian learning (Theorem CHL). Local clamped-minus-free Hebbian updates; no
    backprop, no backward pass. Returns (W1, W2) and the free-phase embedding function."""
    n, d = X.shape
    c = Y.shape[1]
    rng = np.random.default_rng(0)
    W1 = rng.standard_normal((d, HID)) * (1.0 / np.sqrt(d))
    W2 = rng.standard_normal((HID, c)) * (1.0 / np.sqrt(HID))

    def relax(xb, clamp=None):
        h = np.tanh(xb @ W1)
        o = clamp if clamp is not None else _sig(h @ W2)
        for _ in range(T_RELAX):
            h = np.tanh(xb @ W1 + GAMMA * (o @ W2.T))
            if clamp is None:
                o = _sig(h @ W2)
        return h, o

    bs = 32
    for ep in range(EPOCHS):
        perm = rng.permutation(n)
        for i in range(0, n, bs):
            idx = perm[i:i + bs]
            xb, yb = X[idx], Y[idx]
            hf, of = relax(xb, None)
            hc, _ = relax(xb, yb)
            m = len(idx)
            W1 += LR * (xb.T @ (hc - hf)) / m              # local: pre(input) * Δpost(hidden)
            W2 += LR * (hc.T @ yb - hf.T @ of) / m         # local: clamped - free co-activity
    return (lambda Xq: relax(Xq, None)[0]), (lambda Xq: relax(Xq, None)[1])


def _l2(X):
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)


def ncm(Etr, ytr, Ete, yte, freq):
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


def b6(b):
    x = b["6+"]
    return f"6+x: {x[0]}/{x[1]}={x[0]/max(x[1],1)*100:.0f}%"


def main():
    train_min = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    print(SEP)
    print("THE JABBERWOCK ENACTS Hypothesis cog-embedding — local contrastive-Hebbian learning (no backprop).")
    print(SEP)
    train, test = extract(train_min)
    freq = Counter(w for (w, _g) in train)
    keep = {w for w, n in freq.items() if n >= 3}
    tr = [(w, g) for (w, g) in train if w in keep]
    te = [(w, g) for (w, g) in test if w in keep]
    classes = sorted(keep)
    ci = {c: i for i, c in enumerate(classes)}
    print(f"  {len(tr)} train / {len(te)} test exemplars over {len(keep)} words (>=3 exemplars)\n")

    Xtr = np.stack([pool(g) for (_w, g) in tr]); ytr = [w for (w, _g) in tr]
    Xte = np.stack([pool(g) for (_w, g) in te]); yte = [w for (w, _g) in te]
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xtr = (Xtr - mu) / sd; Xte = (Xte - mu) / sd
    Y = np.zeros((len(ytr), len(classes)))
    for i, w in enumerate(ytr):
        Y[i, ci[w]] = 1.0

    # raw pooled-feature baseline (untrained representation)
    raw_acc, raw_b = ncm(Xtr, ytr, Xte, yte, freq)
    print(f"  RAW pooled features (no learning):   recall {raw_acc*100:.0f}%   [{b6(raw_b)}]")

    embed_fn, out_fn = chl_train(Xtr, Y)
    Etr, Ete = embed_fn(Xtr), embed_fn(Xte)
    cog_acc, cog_b = ncm(Etr, ytr, Ete, yte, freq)
    # classify by relaxed output too
    O = out_fn(Xte)
    cor = sum(int(classes[int(np.argmax(o))] == w) for o, w in zip(O, yte))
    out_acc = cor / len(yte)
    print(f"  CHL embedding NCM (local plasticity): recall {cog_acc*100:.0f}%   [{b6(cog_b)}]")
    print(f"  CHL relaxed-output readout:           recall {out_acc*100:.0f}%")

    best = max(cog_acc, out_acc)
    print(f"\n{SEP}")
    if best > 0.20:
        print(f"  Hypothesis cog-embedding CONFIRMED: local contrastive-Hebbian learning reached "
              f"{best*100:.0f}% recall —")
        print("  representation learning WITHOUT backprop, by the local clamped-minus-free rule cognition")
        print("  uses. The forbidden operation was never needed: local plasticity learns the representation.")
    elif best > raw_acc + 0.03:
        print(f"  PARTIAL: local plasticity lifted recall {raw_acc*100:.0f}% -> {best*100:.0f}% over the")
        print("  untrained representation (it IS learning, locally, no backprop) but not to parity. Honest")
        print("  result on local learning at this data scale; tune the rule or get more labelled hours.")
    else:
        print(f"  No lift ({raw_acc*100:.0f}% -> {best*100:.0f}%): contrastive-Hebbian did not converge usefully")
        print("  at this scale. Per the paper's falsifiability, either the local rule needs work (predictive")
        print("  coding / equilibrium propagation) or the limit is data — NOT a licence for backprop.")
    print(SEP)


if __name__ == "__main__":
    main()
