"""LEARN THE WIDER KEYSPACE PRIOR ACROSS SPEAKERS — normalise out what varies by speaker, not by word.

The diverse 5-show pool broke the basin: a content word now spans puppet and documentary voices, so its
exemplars scatter across keys the hand-built invariant could not span. The fix the consideration named:
a WIDER keyspace prior, LEARNED across speakers. Here is the cognitively-faithful way to learn it
without speaker labels: across all words, the variation WITHIN a word (which is shared across words,
because every speaker stamps the same kind of key) IS the keyspace. Estimate that pooled within-word
scatter S_W and WHITEN by it — down-weighting the directions that vary by speaker and up-weighting the
directions that vary by word. This is within-class covariance normalisation, the speaker-compensation
core of x-vector/i-vector systems, and it is exactly "learn the prior over keys so every voice falls in
the basin." Recognise (nearest-class-mean) before vs after the learned normalisation.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_keyspace_prior [topK]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scipy.linalg import eigh
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_shape_pc_paired import content_words
from scripts.jabberwock_enacts_xvector import frame_feats

N_PCA = 60


def pool(seg):
    F = frame_feats(seg)
    return np.concatenate([F.mean(0), F.std(0)])


def ncm(Ztr, ytr, Zte, yte):
    classes = sorted(set(ytr))
    M = np.stack([Ztr[np.asarray(ytr) == c].mean(0) for c in classes])
    pred = [classes[int(np.argmin(((M - q) ** 2).sum(1)))] for q in Zte]
    return float(np.mean([p == w for p, w in zip(pred, yte)]))


def main():
    topK = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    print("=" * 94)
    print("LEARN THE WIDER KEYSPACE PRIOR ACROSS SPEAKERS — whiten what varies by speaker (WCCN).")
    print("=" * 94)
    train, test = multi_extract()
    words = content_words(train, topK, min_ex=12)
    wi = set(words)
    allex = {}
    for (w, g) in train + test:
        if w in wi:
            allex.setdefault(w, []).append(g)
    by, te = {}, []
    for w in words:
        ex = allex[w]; nho = max(2, len(ex) // 5)
        by[w] = ex[:-nho]; te += [(w, g) for g in ex[-nho:]]
    print(f"  {len(train)} train tokens; top-{len(words)} CONTENT words (chance {100/max(len(words),1):.0f}%, "
          f"{sum(len(v) for v in by.values())} train / {len(te)} held-out)\n")
    if len(words) < 6 or len(te) < 25:
        print("  too few content words/exemplars."); return

    tr = [(w, g) for w in words for g in by[w]]
    Xtr = np.stack([pool(g) for (_w, g) in tr]); ytr = [w for (w, _g) in tr]
    Xte = np.stack([pool(g) for (_w, g) in te]); yte = [w for (w, _g) in te]
    m0, s0 = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xtr = (Xtr - m0) / s0; Xte = (Xte - m0) / s0

    # PCA (stabilise the covariance estimates)
    mu = Xtr.mean(0)
    U, S, Vt = np.linalg.svd(Xtr - mu, full_matrices=False)
    k = min(N_PCA, (S > 1e-9).sum())
    P = Vt[:k].T
    Ztr = (Xtr - mu) @ P; Zte = (Xte - mu) @ P

    # LEARN the keyspace prior across speakers: pooled within-WORD scatter = the speaker/channel variation.
    Sw = np.zeros((k, k)); nW = 0
    for w in words:
        Zw = Ztr[np.asarray(ytr) == w]
        d = Zw - Zw.mean(0)
        Sw += d.T @ d; nW += len(Zw)
    Sw = Sw / nW + 1e-3 * np.eye(k)
    vals, vecs = eigh(Sw)
    Wh = vecs @ np.diag(1.0 / np.sqrt(vals)) @ vecs.T          # S_W^{-1/2}: whiten the keyspace

    raw = ncm(Ztr, ytr, Zte, yte)
    wccn = ncm(Ztr @ Wh, ytr, Zte @ Wh, yte)
    # how much of the variance is speaker (within-word) vs word — the keyspace's width.
    St = (Ztr - Ztr.mean(0)); St = (St.T @ St) / len(Ztr)
    spk_frac = float(np.trace(Sw - 1e-3 * np.eye(k)) / (np.trace(St) + 1e-9))
    print(f"  feature variance that is WITHIN-word (speaker/channel, the keyspace): {spk_frac*100:.0f}%\n")
    print(f"  {'NCM, raw features (no keyspace prior)':<46} {raw*100:>5.0f}%")
    print(f"  {'NCM, keyspace-normalised (learned WCCN)':<46} {wccn*100:>5.0f}%")

    print("\n" + "=" * 94)
    if wccn > raw + 0.03:
        print(f"  THE LEARNED KEYSPACE PRIOR HELPS: normalising out the cross-speaker (within-word) variation lifts")
        print(f"  recognition {raw*100:.0f}% -> {wccn*100:.0f}% on the diverse pool — a wider prior IS a wider basin,")
        print(f"  learned from speakers rather than hand-built. {spk_frac*100:.0f}% of the variance was speaker, now whitened.")
    else:
        print(f"  keyspace-normalised {wccn*100:.0f}% vs raw {raw*100:.0f}%: whitening the LINEAR within-word scatter is")
        print(f"  not enough — {spk_frac*100:.0f}% of the variance is speaker, but it is entangled non-linearly with the")
        print("  word (coarticulation; VTL is a non-linear warp), so a linear keyspace prior cannot fully separate it.")
    print("=" * 94)


if __name__ == "__main__":
    main()
