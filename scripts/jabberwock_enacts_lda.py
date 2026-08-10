"""THE JABBERWOCK ENACTS Hypothesis speech-lda — does its held theory crack the real-speech ceiling?

The agent holds (from the seeded literature) Theorem LDA and Hypothesis speech-lda: a supervised
linear transform fit on LABELLED exemplars — suppress within-word (speaker/coarticulation) scatter,
amplify between-word scatter — should lift recognition above the raw-feature ceiling that
normalisation and cue-growth could not move. This script ENACTS that held theory on real Sesame
words and reports the verdict (confirm / refute), which — per the paper's own falsifiability — tells
the agent whether the structure is LINEAR (LDA wins) or NON-LINEAR (reach for the learned embedding).

The LDA fit is mechanical linear algebra (scatter matrices + a generalised eigenproblem, exactly the
closed form in Theorem LDA — no backprop); the agent's contribution is HOLDING the method and
choosing to test it. Recognition is nearest-class-mean in the projected space.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_enacts_lda [train_min]
"""
from __future__ import annotations

import os
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scipy.linalg import eigh
import substrate_rs as srs
import domains.self_directed_speech_world as SDW
from domains.speech_world import FS
from scripts.sesame_cmvn_probe import extract
from scripts.seed_speech_literature import fresh_substrate, PAPERS
from domains.paper_reader import install_paper_as_theory
from pathlib import Path

SEP = "=" * 90


def feats(s, segs):
    return np.stack([np.concatenate([np.asarray(c, dtype=np.float64).ravel()
                                     for c in SDW.feature_channels(s, np.asarray(g, dtype=np.float64), FS)])
                     for g in segs])


def fit_lda(X, y, n_pca=120, eps=1e-2):
    """Theorem LDA, closed form: PCA-whiten for stability (S_W is rank-deficient with few exemplars),
    then solve the generalised eigenproblem S_B w = lambda S_W w. Returns a projector x -> y-space."""
    mu = X.mean(0)
    Xc = X - mu
    U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
    k = min(n_pca, (S > 1e-9).sum())
    P = Vt[:k].T / (S[:k] + 1e-9)                      # PCA whitening
    Z = Xc @ P
    classes = sorted(set(y))
    gmu = Z.mean(0)
    Sw = np.zeros((k, k)); Sb = np.zeros((k, k))
    for c in classes:
        Zc = Z[np.asarray(y) == c]
        cmu = Zc.mean(0)
        d = Zc - cmu
        Sw += d.T @ d
        dm = (cmu - gmu)[:, None]
        Sb += len(Zc) * (dm @ dm.T)
    Sw += eps * np.eye(k)                              # shrinkage (regularised LDA)
    evals, evecs = eigh(Sb, Sw)
    ncomp = min(len(classes) - 1, k)
    W = evecs[:, -ncomp:]                              # top discriminant directions
    proj = P @ W
    return lambda Xq: (Xq - mu) @ proj


def ncm(train_feat, y, test_feat, ty, freq):
    """Nearest-class-mean recognition, bucketed by training frequency."""
    classes = sorted(set(y))
    means = {c: train_feat[np.asarray(y) == c].mean(0) for c in classes}
    M = np.stack([means[c] for c in classes])
    buckets = {"1": [0, 0], "2": [0, 0], "3-5": [0, 0], "6+": [0, 0]}

    def bk(c):
        return "1" if c == 1 else "2" if c == 2 else "3-5" if c <= 5 else "6+"
    c = t = 0
    for q, w in zip(test_feat, ty):
        d = ((M - q) ** 2).sum(1)
        pred = classes[int(np.argmin(d))]
        t += 1; ok = pred == w; c += int(ok)
        b = buckets[bk(freq[w])]; b[1] += 1; b[0] += int(ok)
    return (c / t if t else 0.0), buckets


def main():
    train_min = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    print(SEP)
    print("THE JABBERWOCK ENACTS Hypothesis speech-lda — testing its held theory on real speech.")
    print(SEP)
    # the agent reads/holds the theory, then states the claim it is about to test.
    sg = fresh_substrate()
    for pid, rel in PAPERS:
        install_paper_as_theory(sg, Path(os.path.join(ROOT, rel)), pid)
    h = next((n for n in sg.nodes("PaperHypothesis")
              if "speech-lda" in str(sg.node(n)["attrs"].get("label", ""))), None)
    if h:
        print(f"  HELD THEORY (testing): {sg.node(h)['attrs'].get('text','')[:180]}...\n")

    train, test = extract(train_min)
    s = srs.Substrate()
    # keep only words with enough exemplars to estimate within-class scatter (LDA needs them).
    freq = Counter(w for (w, _g) in train)
    keep = {w for w, n in freq.items() if n >= 3}
    tr = [(w, g) for (w, g) in train if w in keep]
    te = [(w, g) for (w, g) in test if w in keep]
    print(f"  {len(tr)} train / {len(te)} test exemplars over {len(keep)} words (>=3 exemplars)\n")

    Xtr = feats(s, [g for (_w, g) in tr]); ytr = [w for (w, _g) in tr]
    Xte = feats(s, [g for (_w, g) in te]); yte = [w for (w, _g) in te]

    base_acc, base_b = ncm(Xtr, ytr, Xte, yte, freq)
    print(f"  RAW features (NCM):  recall {base_acc*100:.0f}%   "
          f"[6+x: {base_b['6+'][0]}/{base_b['6+'][1]}={base_b['6+'][0]/max(base_b['6+'][1],1)*100:.0f}%]")

    proj = fit_lda(Xtr, ytr)
    Ztr, Zte = proj(Xtr), proj(Xte)
    lda_acc, lda_b = ncm(Ztr, ytr, Zte, yte, freq)
    print(f"  LDA  features (NCM):  recall {lda_acc*100:.0f}%   "
          f"[6+x: {lda_b['6+'][0]}/{lda_b['6+'][1]}={lda_b['6+'][0]/max(lda_b['6+'][1],1)*100:.0f}%]")

    print(f"\n{SEP}")
    delta = (lda_acc - base_acc) * 100
    if delta > 3:
        print(f"  Hypothesis speech-lda CONFIRMED: LDA {base_acc*100:.0f}% -> {lda_acc*100:.0f}% "
              f"({delta:+.0f}pt). The word/nuisance structure is partly LINEAR — the discriminative")
        print("  transform helps. Residual error motivates the learned non-linear embedding (speech-xvector).")
    else:
        print(f"  Hypothesis speech-lda REFUTED: LDA {base_acc*100:.0f}% -> {lda_acc*100:.0f}% "
              f"({delta:+.0f}pt). The structure is NOT linearly separable — per the paper's own")
        print("  falsifiability, the evidence points to the learned non-linear embedding (speech-xvector),")
        print("  the agent's next held hypothesis. The linear-transform family is exhausted.")
    print(SEP)


if __name__ == "__main__":
    main()
