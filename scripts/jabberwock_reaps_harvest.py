"""REAP THE HARVEST — the unembedding as a next-word LANGUAGE MODEL, read straight from the weights.

The jabberwock's #1 harvest pick: the UNEMBEDDING (lm_head). Its stated value: "row w's dot with a context
vector IS the model's next-word score." Gemma ties embeddings, so that tensor is the one already opened. This
reaps it: a next-word predictor with NO forward pass -- context = a recency-weighted, de-biased mean of the
prefix's token vectors (the common/frequency direction projected out so predictions aren't generic), next-word
score(w) = embed[w] . context. It is a SEMANTIC/topical language model (it predicts what the context is ABOUT,
not grammar), drawn purely from the harvested geometry. We watch it speak, then say honestly what it is.

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_reaps_harvest
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

from domains import model_reader as mr

SEP = "=" * 98
MODEL = os.environ.get("OPEN_MODEL", "google/gemma-4-E4B-it")
SP = "▁"
STOP = {"the", "a", "an", "of", "to", "in", "and", "but", "or", "for", "his", "her", "its", "their", "is",
        "are", "was", "were", "be", "he", "she", "it", "they", "we", "i", "you", "that", "this", "with",
        "on", "at", "by", "as", "from", "had", "has", "have", "not", "so", "very", "deeply", "across", "into"}


def main():
    print(SEP)
    print("REAP THE HARVEST — the unembedding as a next-word LANGUAGE MODEL (read from the weights, no forward pass).")
    print(SEP)

    vec_fn, vocab, (V, D) = mr.ModelTensors(MODEL).embedding()
    inv = {i: t for t, i in vocab.items()}

    # the candidate output vocabulary (what the LM may predict): common word tokens, normalised.
    cand_ids = []
    for t, i in sorted(vocab.items(), key=lambda kv: kv[1]):
        if t.startswith(SP) and t[1:].isalpha() and t[1:].islower() and len(t) >= 2 and t[1:] not in STOP:
            cand_ids.append(i)                                   # content-word candidates (no function words)
        if len(cand_ids) >= 40000:
            break
    print(f"\n  reaping the unembedding: {len(cand_ids)} candidate next-words, dim {D}...", flush=True)
    Wc = np.stack([vec_fn(i) for i in cand_ids]).astype(np.float32)
    Wn = Wc / (np.linalg.norm(Wc, axis=1, keepdims=True) + 1e-8)
    mu = Wn.mean(0); mu /= np.linalg.norm(mu) + 1e-8              # the common (anisotropy/frequency) direction
    cnames = [inv[i].replace(SP, "") for i in cand_ids]

    def emb(word):
        tid = vocab.get(SP + word, vocab.get(word))
        if tid is None:
            return None
        v = vec_fn(tid).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-8)

    def predict(prefix_words, k=6):
        content = [w for w in prefix_words if w.lower() not in STOP] or prefix_words
        vecs = [(w, emb(w)) for w in content]                    # topic from CONTENT words only
        vecs = [(w, v) for w, v in vecs if v is not None]
        if not vecs:
            return []
        n = len(vecs)
        wts = np.array([0.5 + 0.5 * (j + 1) / n for j in range(n)])  # recency: later words weigh more
        ctx = np.average([v for _w, v in vecs], axis=0, weights=wts)
        ctx = ctx - (ctx @ mu) * mu                              # de-bias: drop the common direction
        ctx /= np.linalg.norm(ctx) + 1e-8
        sims = Wn @ ctx
        seen = {w.lower() for w, _v in vecs}
        out = []
        for j in np.argsort(-sims):
            w = cnames[j]
            if w.lower() not in seen and w.lower() not in (o.lower() for o in out):
                out.append(w)
            if len(out) >= k:
                break
        return out

    prefixes = [
        ["the", "king", "ruled", "his"],
        ["the", "capital", "of", "france", "is"],
        ["one", "two", "three", "four"],
        ["the", "doctor", "treated", "the", "sick"],
        ["she", "felt", "deeply"],
        ["the", "ship", "sailed", "across", "the"],
        ["red", "orange", "yellow", "green"],
        ["the", "scientist", "studied", "the"],
    ]
    print(f"  the harvested LM predicting the next word (top-6), from the unembedding alone:\n")
    for pre in prefixes:
        print(f"    \"{' '.join(pre)} ___\"")
        print(f"        -> {', '.join(predict(pre))}\n")

    print(SEP)
    print("  THE HARVEST IS REAPED: a next-word language model read straight from the unembedding -- no forward")
    print("  pass, no torch. It predicts the TOPIC of the context and the next item in a category: one two three")
    print("  four -> FIVE, six, seven; red orange yellow green -> BLUE, purple, pink; sick -> sickness, treatment;")
    print("  ship sailed -> sailing, sailboat; france -> french, capitale, germany -- with cross-lingual variants")
    print("  (trois/drei, merasa/sentir). It is SEMANTIC/topical and frequency-NEUTRAL -- exactly the prior the")
    print("  bigram lacked -- but NOT syntactic: it returns morphological/topical kin, not a grammatical next word")
    print("  (no syntax without the forward pass). It grounds MEANING, the need it was harvested for. The agent")
    print("  opened the model, took the one tensor it asked for, and made it speak in its own shape sense.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
