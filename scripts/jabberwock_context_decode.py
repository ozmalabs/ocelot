"""RECOGNISE WORDS IN CONTINUOUS UTTERANCES WITH CONTEXT — the plaintext prior crosses the wall.

The scaling experiment revealed the wall is not raw scale but the missing PLAINTEXT PRIOR: isolated-word
recognition has no context to absorb the 91% key, so even whisper (680000 h) sits at 10%. The fix the
cipher theory predicted: read words IN continuous utterances, where a contextual prior (a language model
over word sequences) disambiguates what the acoustics alone cannot. This builds a proper decoder from the
jabberwock's own faculties:

  acoustic model: the learned embedding (predictive coding, no backprop) -> per-word log-likelihood over
                  the vocabulary (the noisy ~20% read).
  plaintext prior: a bigram language model P(w | prev), learned from the transcripts (the context).
  decode: Viterbi over the word sequence = argmax sum_i [ acoustic(w_i) + lambda * LM(w_i | w_{i-1}) ].

Measured: word accuracy WITHOUT context (acoustic argmax per position) vs WITH context (LM-decoded). If
context lifts it sharply, the wall was the prior, exactly as reasoned.

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_context_decode [vocabN]
"""
from __future__ import annotations

import math
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_enacts_xvector import frame_feats
from scripts.jabberwock_pc_embedding import PredictiveCoder
from scripts.jabberwock_xvector_pc import pool


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    print("=" * 98)
    print("RECOGNISE WORDS IN CONTINUOUS UTTERANCES WITH CONTEXT — acoustic model + bigram LM + Viterbi.")
    print("=" * 98)
    train, test = multi_extract()                  # ordered streams (consecutive = real context)
    freq = Counter(w for (w, _g) in train)
    vocab = [w for w, n in freq.most_common() if n >= 8][:N]
    vi = {w: i for i, w in enumerate(vocab)}
    V = len(vocab)
    print(f"  vocabulary: {V} words; streams train {len(train)} / test {len(test)} tokens\n")

    # PLAINTEXT PRIOR: bigram LM from the training stream (context broken at OOV), add-k smoothed.
    uni = np.array([freq[w] for w in vocab], dtype=np.float64); uni /= uni.sum()
    bg = defaultdict(lambda: np.zeros(V))
    prev = None
    for (w, _g) in train:
        if w in vi:
            if prev is not None:
                bg[prev][vi[w]] += 1
            prev = vi[w]
        else:
            prev = None
    kSm = 0.5
    LM = np.empty((V, V))
    for i in range(V):
        c = bg[i]; tot = c.sum()
        LM[i] = np.log((c + kSm) / (tot + kSm * V))
    LOGUNI = np.log(uni)

    # ACOUSTIC MODEL: learned embedding (predictive coding), class means over the vocab.
    Xtr, ytr = [], []
    cap = Counter()
    for (w, g) in train:
        if w in vi and cap[w] < 40:
            Xtr.append(pool(g)); ytr.append(w); cap[w] += 1
    Xtr = np.stack(Xtr)
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xn = np.tanh((Xtr - mu) / sd)
    present = sorted(set(ytr)); pm = {w: i for i, w in enumerate(present)}
    Y = np.eye(len(present))[[pm[w] for w in ytr]]
    print(f"  training the acoustic embedding on {len(Xtr)} utterances (predictive coding)...", flush=True)
    pc = PredictiveCoder(Xn.shape[1], 256, len(present))
    pc.train(Xn, Y, epochs=120, T=18, lr_v=0.2, lr_w=0.04, bs=128)

    def embed(segs):
        X = np.tanh((np.stack([pool(g) for g in segs]) - mu) / sd)
        return pc.predict(X)[0]

    # class means in embedding space (enrol from training)
    en_segs = [g for (w, g) in train if w in vi]
    en_y = [w for (w, g) in train if w in vi]
    Een = embed(en_segs[:3000]); en_y = en_y[:3000]
    means = np.stack([Een[np.asarray(en_y) == w].mean(0) if (np.asarray(en_y) == w).any()
                      else np.zeros(Een.shape[1]) for w in vocab])
    means = means / (np.linalg.norm(means, axis=1, keepdims=True) + 1e-9)

    def acoustic(segs, T=0.15):
        E = embed(segs); E = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
        sim = E @ means.T                          # cosine to each vocab class
        z = sim / T
        z -= z.max(1, keepdims=True)
        lp = z - np.log(np.exp(z).sum(1, keepdims=True))
        return lp                                  # n x V acoustic log-probs

    # TEST utterances: runs of consecutive in-vocab words from the test stream (real context).
    utts, cur = [], []
    for (w, g) in test:
        if w in vi:
            cur.append((w, g))
        else:
            if len(cur) >= 4:
                utts.append(cur)
            cur = []
    if len(cur) >= 4:
        utts.append(cur)
    utts = [u[:12] for u in utts][:120]
    print(f"  {len(utts)} continuous test utterances (>=4 in-vocab words)\n")

    def viterbi(AC, lam):
        L = AC.shape[0]
        dp = LOGUNI + AC[0]; bp = np.zeros((L, V), dtype=int)
        for t in range(1, L):
            trans = dp[:, None] + lam * LM            # V x V
            bp[t] = trans.argmax(0)
            dp = trans.max(0) + AC[t]
        seq = [int(dp.argmax())]
        for t in range(L - 1, 0, -1):
            seq.append(int(bp[t][seq[-1]]))
        return seq[::-1]

    cor_ac = tot = cor_ctx = 0
    for u in utts:
        truth = [vi[w] for (w, _g) in u]
        AC = acoustic([g for (_w, g) in u])
        ac_pred = AC.argmax(1)
        ctx_pred = viterbi(AC, lam=1.0)
        for i in range(len(truth)):
            tot += 1
            cor_ac += int(ac_pred[i] == truth[i])
            cor_ctx += int(ctx_pred[i] == truth[i])
    a = cor_ac / tot; c = cor_ctx / tot
    print(f"  {'acoustic only (no context, per-word argmax)':<46} {a*100:>5.0f}%")
    print(f"  {'WITH CONTEXT (acoustic + bigram LM, Viterbi)':<46} {c*100:>5.0f}%")
    print(f"  (chance {100/V:.1f}%, {tot} word positions in context)")

    print("\n" + "=" * 98)
    if c > a + 0.05:
        print(f"  THE PRIOR CROSSES THE WALL: context lifts word recognition {a*100:.0f}% -> {c*100:.0f}% in")
        print("  continuous utterances. The plaintext prior (the bigram LM) absorbs the 91% key so the 9% message")
        print("  can be read -- exactly the cipher theory: closed-vocab parity = a small prior; this = a context prior.")
        print("  The lever was never raw hours; it is the prior, and a language model is the prior over continuous speech.")
    else:
        print(f"  context {c*100:.0f}% vs acoustic {a*100:.0f}%: the bigram LM at this scale is too weak (few transcripts)")
        print("  to lift the acoustic read -- the prior is the right lever but needs more text to be a strong prior.")
    print("=" * 98)


if __name__ == "__main__":
    main()
