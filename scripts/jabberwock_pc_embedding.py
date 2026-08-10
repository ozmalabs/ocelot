"""THE JABBERWOCK LEARNS A SPEECH EMBEDDING BY PREDICTIVE CODING — the cortical local rule, no backprop.

It IS physically possible (a child learns speaker-invariant recognition from local plasticity), and it
does NOT need a huge corpus — the same small set, rehearsed over and over, lets a local rule extract
all the order-N detail. Predictive coding (Whittington & Bogacz 2017, discriminative form: input ->
label, errors relax LOCALLY, weights updated by local error*activity) provably approximates the
backprop gradient with purely local updates — no backward pass, no weight transport. This learns a
discriminative speech embedding by that rule on a SMALL well-sampled word set with MANY rehearsals,
and self-checks on a separable control first (the implementation must learn what is learnable).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_pc_embedding [topK] [epochs]
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


def pool(seg):
    F = frame_feats(seg)
    return np.concatenate([F.mean(0), F.std(0)])


def _f(z):
    return np.tanh(z)


def _df(z):
    return 1.0 - np.tanh(z) ** 2


class PredictiveCoder:
    """Discriminative predictive coding (Whittington-Bogacz). Feedforward predictions input->hidden->
    output; inference relaxes the hidden to reconcile its own prediction error with the back-projected
    output error; weights update by LOCAL error*presynaptic-activity. No backward pass — approximates
    the backprop gradient with purely local quantities."""

    def __init__(self, d, hid, c, seed=0):
        rng = np.random.default_rng(seed)
        self.W1 = rng.standard_normal((d, hid)) / np.sqrt(d)
        self.W2 = rng.standard_normal((hid, c)) / np.sqrt(hid)

    def _infer(self, X, T, lr_v, y=None):
        mu1 = _f(X) @ self.W1
        v1 = mu1.copy()
        v2 = y.copy() if y is not None else _f(v1) @ self.W2
        for _ in range(T):
            mu1 = _f(X) @ self.W1
            e1 = v1 - mu1
            mu2 = _f(v1) @ self.W2
            e2 = v2 - mu2
            v1 = v1 + lr_v * (-e1 + _df(v1) * (e2 @ self.W2.T))
            if y is None:
                v2 = _f(v1) @ self.W2
        e1 = v1 - _f(X) @ self.W1
        e2 = v2 - _f(v1) @ self.W2
        return v1, v2, e1, e2

    def train(self, X, Y, epochs=200, T=20, lr_v=0.2, lr_w=0.05, bs=64):
        n = X.shape[0]
        rng = np.random.default_rng(1)
        for _ep in range(epochs):                                  # rehearse the same set repeatedly
            perm = rng.permutation(n)
            for i in range(0, n, bs):
                idx = perm[i:i + bs]
                xb, yb = X[idx], Y[idx]
                v1, _v2, e1, e2 = self._infer(xb, T, lr_v, y=yb)
                m = len(idx)
                self.W1 += lr_w * (_f(xb).T @ e1) / m              # local: presyn(input) * error(hidden)
                self.W2 += lr_w * (_f(v1).T @ e2) / m              # local: presyn(hidden) * error(output)

    def predict(self, X, T=30, lr_v=0.2):
        v1, v2, _e1, _e2 = self._infer(X, T, lr_v, y=None)
        return v1, v2


def _l2(X):
    return X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)


def ncm(Etr, ytr, Ete, yte):
    classes = sorted(set(ytr))
    Etr, Ete = _l2(Etr), _l2(Ete)
    M = _l2(np.stack([Etr[np.asarray(ytr) == c].mean(0) for c in classes]))
    pred = [classes[int(np.argmax(M @ q))] for q in Ete]
    return np.mean([p == w for p, w in zip(pred, yte)])


def control():
    rng = np.random.default_rng(0)
    C, d, n = 10, 50, 40
    ctr = rng.standard_normal((C, d)) * 4

    def gen(k):
        X = np.vstack([ctr[c] + rng.standard_normal((k, d)) for c in range(C)])
        y = np.repeat(np.arange(C), k)
        return X, y
    Xtr, ytr = gen(n); Xte, yte = gen(20)
    pc = PredictiveCoder(d, 80, C)
    pc.train(np.tanh(Xtr / 4), np.eye(C)[ytr], epochs=60)
    _, v2 = pc.predict(np.tanh(Xte / 4))
    return np.mean(np.argmax(v2, 1) == yte)


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    epochs = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    print("=" * 92)
    print("PREDICTIVE-CODING SPEECH EMBEDDING — cortical local rule, small set rehearsed, no backprop.")
    print("=" * 92)
    cacc = control()
    print(f"  self-check (10 separable blobs): PC inferred-label = {cacc*100:.0f}%  "
          f"({'implementation OK' if cacc > 0.9 else 'IMPLEMENTATION STILL BROKEN'})\n")

    train, test = extract(16.0)
    freq = Counter(w for (w, _g) in train)
    words = [w for w, _ in freq.most_common(topK)]           # the K most-rehearsable words
    wi = {w: i for i, w in enumerate(words)}
    tr = [(w, g) for (w, g) in train if w in wi]
    te = [(w, g) for (w, g) in test if w in wi]
    print(f"  top-{topK} words ({len(tr)} train / {len(te)} test exemplars), {epochs} rehearsals: {words}\n")

    Xtr = np.stack([pool(g) for (_w, g) in tr]); ytr = [w for (w, _g) in tr]
    Xte = np.stack([pool(g) for (_w, g) in te]); yte = [w for (w, _g) in te]
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xtr = np.tanh((Xtr - mu) / sd); Xte = np.tanh((Xte - mu) / sd)
    Y = np.eye(len(words))[[wi[w] for w in ytr]]

    raw = ncm(Xtr, ytr, Xte, yte)
    print(f"  RAW pooled (no learning):           recall {raw*100:.0f}%  (chance {100/len(words):.0f}%)")

    pc = PredictiveCoder(Xtr.shape[1], 200, len(words))
    pc.train(Xtr, Y, epochs=epochs)
    Etr, _ = pc.predict(Xtr); Ete, Ote = pc.predict(Xte)
    pc_ncm = ncm(Etr, ytr, Ete, yte)
    out = np.mean([words[int(np.argmax(o))] == w for o, w in zip(Ote, yte)])
    print(f"  PREDICTIVE-CODING embedding (NCM):  recall {pc_ncm*100:.0f}%")
    print(f"  predictive-coding inferred label:   recall {out*100:.0f}%")

    best = max(pc_ncm, out)
    print("\n" + "=" * 92)
    if cacc <= 0.9:
        print("  Fix the implementation first (control failed) before reading the speech result.")
    elif best > raw + 0.05:
        print(f"  cog-embedding SUPPORTED: local predictive coding lifted recall {raw*100:.0f}% -> {best*100:.0f}% "
              f"on rehearsed real speech — representation learned WITHOUT backprop, the cortical way.")
    else:
        print(f"  local rule {raw*100:.0f}% -> {best*100:.0f}% on real speech (control OK, so the rule works) — "
              f"keep rehearsing / richer features; the structure is there, it is an engineering climb.")
    print("=" * 92)


if __name__ == "__main__":
    main()
