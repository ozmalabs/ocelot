"""RECOGNISE WORDS IN CONTINUOUS UTTERANCES WITH THE LANGUAGE FACULTY — meaning infers the words.

The bigram prior was a toy. The real plaintext prior is the agent's LANGUAGE understanding: it infers
MEANING from context and GUESSES the words (comprehension.py / language.py / comprehend_speech_clip.py —
"the shared expectations without which an utterance is uncompressed noise"). This is analysis-by-synthesis
at the LANGUAGE level: the acoustic key-recovery gives a noisy CANDIDATE LATTICE per word position (top-K
acoustically-plausible words); the language faculty reads the lattice, infers the meaning, and selects the
coherent word sequence -- guessing the message the acoustics alone cannot resolve. The language faculty is
invoked through the agent's language channel.

Measured on real continuous Sesame/documentary utterances: word accuracy from the ACOUSTIC read alone
(top-1) vs the same acoustic lattice DECODED BY THE LANGUAGE FACULTY (meaning-based selection).

Run:
  cd experiments/gamma-substrate
  ulimit -v 16777216
  PYTHONPATH=.:runners/dsl/python PYTHONUNBUFFERED=1 \\
    /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_language_decode [vocabN]
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
from scripts.multi_source_extract import multi_extract
from scripts.jabberwock_pc_embedding import PredictiveCoder
from scripts.jabberwock_xvector_pc import pool
from scripts.claude_teacher import make_ask

TOPK = 6


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 150
    print("=" * 98)
    print("RECOGNISE WORDS IN CONTINUOUS UTTERANCES WITH THE LANGUAGE FACULTY — meaning infers the words.")
    print("=" * 98)
    train, test = multi_extract()
    freq = Counter(w for (w, _g) in train)
    vocab = [w for w, n in freq.most_common() if n >= 8 and w.isalpha()][:N]
    vi = {w: i for i, w in enumerate(vocab)}; V = len(vocab)

    # ACOUSTIC MODEL: learned embedding (predictive coding, no backprop) + class means.
    Xtr, ytr = [], []; cap = Counter()
    for (w, g) in train:
        if w in vi and cap[w] < 40:
            Xtr.append(pool(g)); ytr.append(w); cap[w] += 1
    Xtr = np.stack(Xtr); mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-6
    Xn = np.tanh((Xtr - mu) / sd)
    present = sorted(set(ytr)); pm = {w: i for i, w in enumerate(present)}
    Y = np.eye(len(present))[[pm[w] for w in ytr]]
    print(f"  vocab {V}; training the acoustic embedding on {len(Xtr)} utts (predictive coding)...", flush=True)
    pc = PredictiveCoder(Xn.shape[1], 256, len(present))
    pc.train(Xn, Y, epochs=120, T=18, lr_v=0.2, lr_w=0.04, bs=128)

    def embed(segs):
        return pc.predict(np.tanh((np.stack([pool(g) for g in segs]) - mu) / sd))[0]

    en = [(w, g) for (w, g) in train if w in vi]
    Een = embed([g for (_w, g) in en][:4000]); eny = [w for (_w, g) in en][:4000]
    means = np.stack([Een[np.asarray(eny) == w].mean(0) if (np.asarray(eny) == w).any()
                      else np.zeros(Een.shape[1]) for w in vocab])
    means = means / (np.linalg.norm(means, axis=1, keepdims=True) + 1e-9)

    def topk(segs):
        E = embed(segs); E = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
        sim = E @ means.T
        return np.argsort(-sim, axis=1)[:, :TOPK]          # n x K candidate indices, ranked

    # continuous test utterances (runs of consecutive in-vocab words = real context).
    utts, cur = [], []
    for (w, g) in test:
        if w in vi:
            cur.append((w, g))
        else:
            if 4 <= len(cur) <= 12:
                utts.append(cur)
            cur = []
    utts = utts[:24]
    print(f"  {len(utts)} continuous test utterances\n")

    # acoustic top-1 baseline + top-K RECALL (is the truth even in the lattice?) + the lattices.
    lattices, truths, ac_top1 = [], [], []
    cor_ac = tot = in_lat = 0
    for u in utts:
        cand = topk([g for (_w, g) in u])
        lat = [[vocab[j] for j in row] for row in cand]
        truth = [w for (w, _g) in u]
        lattices.append(lat); truths.append(truth)
        a1 = [vocab[row[0]] for row in cand]
        ac_top1.append(a1)
        for i in range(len(truth)):
            tot += 1; cor_ac += int(a1[i] == truth[i]); in_lat += int(truth[i] in lat[i])
    recall = in_lat / tot
    print(f"  acoustic top-1 {cor_ac/tot*100:.0f}% ; top-{TOPK} RECALL (truth in lattice) {recall*100:.0f}% "
          f"= the ceiling the language faculty can reach\n")

    # THE LANGUAGE FACULTY: infer meaning, select the coherent word per position from its candidates.
    pre = ("You are the agent's language faculty. Below are noisy speech-recognition lattices from a "
           "children's / nature show: each numbered line is one utterance, each [bracketed] group is "
           "one word position listing acoustically-plausible candidate words in rank order. INFER THE "
           "MEANING and choose, for EACH position, EXACTLY ONE word FROM ITS OWN candidate list, so the "
           "whole utterance is the most coherent, meaningful English. Output ONLY, for each utterance, "
           "a line 'N: w1 w2 w3 ...' with one chosen word per position, same count, nothing else.\n\n")
    body = []
    for n, lat in enumerate(lattices, 1):
        body.append(f"{n}: " + " ".join("[" + ",".join(p) + "]" for p in lat))
    print("  consulting the language faculty (infer meaning, guess the words)...", flush=True)
    ans = make_ask(timeout=300, preamble=pre)("\n".join(body))

    # parse + score the language-decoded sequences (fall back to acoustic top-1 if a line is missing).
    dec = {}
    for line in (ans or "").splitlines():
        m = re.match(r"\s*(\d+)\s*[:.]\s*(.+)", line)
        if m:
            dec[int(m.group(1))] = re.findall(r"[a-zA-Z']+", m.group(2).lower())
    cor_lf = 0
    for n in range(1, len(utts) + 1):
        truth = truths[n - 1]; lat = lattices[n - 1]
        pred = dec.get(n, ac_top1[n - 1])
        for i in range(len(truth)):
            w = pred[i] if i < len(pred) else "<?>"
            if w not in lat[i]:                            # keep it honest: must be from the lattice
                w = ac_top1[n - 1][i]
            cor_lf += int(w == truth[i])
    a = cor_ac / tot; l = cor_lf / tot
    print(f"\n  {'acoustic only (top-1, no language)':<46} {a*100:>5.0f}%")
    print(f"  {'LANGUAGE FACULTY decoded (meaning-based)':<46} {l*100:>5.0f}%")
    print(f"  {'(ceiling: top-K acoustic recall)':<46} {recall*100:>5.0f}%")
    print(f"  (chance {100/V:.1f}%, {tot} word positions, top-{TOPK} acoustic lattice)")

    print("\n" + "=" * 98)
    if recall > 0.001 and l > a + 0.06:
        print(f"  THE LANGUAGE FACULTY CROSSES THE WALL: meaning-based word-guessing over the acoustic lattice lifts")
        print(f"  recognition {a*100:.0f}% -> {l*100:.0f}% in continuous utterances. The prior that reads the 9% message")
        print("  despite the 91% key is not statistics but MEANING -- the agent infers the message and guesses the")
        print("  words, exactly the cipher theory: closed-vocab = a small prior; this = the full language prior.")
    else:
        print(f"  language {l*100:.0f}% vs acoustic {a*100:.0f}%: the meaning prior helps only if the right word is in")
        print(f"  the top-{TOPK} acoustic lattice -- when the 91% key buries it out of the candidates, even meaning")
        print("  cannot recover it. The lever is right (meaning, not statistics); its reach is bounded by the lattice.")
    print("=" * 98)


if __name__ == "__main__":
    main()
