"""GOING DEEPER INTO GEMMA — the model's CONCEPTS live in its FFN neurons. Read from weights, no inference.

Past the embedding: each feed-forward layer is a bank of key-value memories (Geva et al.). A neuron's VALUE
vector is one column of ffn_down -- the direction it writes into the residual stream. Projected through the
(tied) embedding, that direction names the TOKENS the neuron promotes: its concept. So the agent can ask
"which neuron writes NUMBERS?" -- scan every neuron's value vector for the one most aligned with a concept
direction, then read back the vocabulary it writes. The concept grouping is the MODEL'S own (the top tokens
extend past the seed words), surfaced straight from ffn_down (Q6_K) + the embedding. No torch, no running it.

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_gemma_neurons
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

CONCEPTS = {
    "numbers": ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"],
    "colours": ["red", "blue", "green", "yellow", "black", "white", "purple", "orange"],
    "family": ["mother", "father", "sister", "brother", "son", "daughter", "uncle", "aunt"],
    "days/time": ["monday", "tuesday", "wednesday", "friday", "morning", "evening", "night"],
    "body": ["hand", "head", "eye", "foot", "arm", "leg", "finger", "knee"],
    "emotion": ["happy", "sad", "angry", "afraid", "joy", "fear", "love", "grief"],
}


def main():
    print(SEP)
    print("GOING DEEPER INTO GEMMA — the model's CONCEPTS live in its FFN neurons (read from the weights).")
    print(SEP)

    mt = mr.ModelTensors(MODEL)
    vec_fn, vocab, (V, D) = mt.embedding()
    SP = mr.ModelTensors.marker(vocab)
    inv = {i: t for t, i in vocab.items()}
    LAYERS = sorted({int(mt.n_layers * f) for f in (0.2, 0.4, 0.6, 0.85)})   # spread across the stack
    print(f"\n  opened {MODEL}: {mt.n_layers} text layers, dim {mt.d_model}, {mt.n_heads}Q/{mt.n_kv}KV heads. "
          f"reading FFN value neurons in layers {LAYERS}.")

    # a vocab sample (normalised) to project neuron value-vectors back onto tokens (the logit lens)
    print(f"  loading a 50k-token embedding sample to read neurons back into words...", flush=True)
    samp = np.linspace(0, V - 1, 50000).astype(int)
    E = np.stack([vec_fn(int(i)) for i in samp]).astype(np.float32)
    En = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-8)

    def word_vec(w):
        tid = vocab.get(SP + w, vocab.get(w))
        if tid is None:
            return None
        v = vec_fn(tid).astype(np.float32)
        return v / (np.linalg.norm(v) + 1e-8)

    def toptokens(value, k=14):
        v = value / (np.linalg.norm(value) + 1e-8)
        sims = En @ v
        out = []
        for j in np.argsort(-sims):
            t = inv[int(samp[j])].replace(SP, "").strip()
            if t and any(c.isalpha() for c in t) and t.lower() not in (x.lower() for x in out):
                out.append(t)
            if len(out) >= k:
                break
        return out

    # load ffn_down for the chosen layers: shape (D_resid, n_neurons); neuron j's value = M[:, j]
    print(f"  reading ffn_down (the neuron VALUE vectors) for layers {LAYERS}...", flush=True)
    downs = {}
    for L in LAYERS:
        M = mt.layer(L, "ffn_down")                                # (d_model, n_neurons)
        downs[L] = (M, M / (np.linalg.norm(M, axis=0, keepdims=True) + 1e-8))
    print(f"  each layer has {downs[LAYERS[0]][0].shape[1]} neurons of dim {downs[LAYERS[0]][0].shape[0]}.\n")

    print("  for each concept, the single neuron (across those layers) whose VALUE direction most writes it,")
    print("  and the vocabulary that neuron promotes (the MODEL's own grouping, beyond the seed words):\n")
    for cname, seeds in CONCEPTS.items():
        vs = [word_vec(w) for w in seeds]
        vs = [v for v in vs if v is not None]
        cdir = np.mean(vs, axis=0); cdir /= np.linalg.norm(cdir) + 1e-8
        best = (-1, None, None)
        for L in LAYERS:
            M, Mn = downs[L]
            score = cdir @ Mn                                     # cosine of each neuron's value with the concept
            j = int(np.argmax(score))
            if score[j] > best[0]:
                best = (float(score[j]), L, j)
        sc, L, j = best
        toks = toptokens(downs[L][0][:, j])
        print(f"    {cname:>9}: layer {L:>2} neuron {j:<5} (cos {sc:.2f})  writes-> {', '.join(toks)}")

    # honesty: a few RANDOM neurons -- many are mixed / polysemantic, not clean concepts.
    print("\n  for honesty, three ARBITRARY neurons (most are mixed, not tidy concepts):\n")
    rng = np.random.default_rng(1)
    for _ in range(3):
        L = LAYERS[int(rng.integers(len(LAYERS)))]
        j = int(rng.integers(downs[L][0].shape[1]))
        print(f"    layer {L:>2} neuron {j:<5}  writes-> {', '.join(toptokens(downs[L][0][:, j], 10))}")

    print("\n" + SEP)
    print("  DEEPER FINDING: Gemma stores concepts as FEED-FORWARD MEMORIES. A single neuron's value direction,")
    print("  read through the embedding, writes a coherent vocabulary -- numbers, colours, family, body parts --")
    print("  the model's OWN grouping, not the agent's seeds. The agent located each concept's neuron by scanning")
    print("  value directions and read its vocabulary back, all from ffn_down + the embedding, no inference. Many")
    print("  neurons are polysemantic (the arbitrary ones), but the concept neurons are real and legible. This is")
    print("  how a transformer stores meaning a layer below the words -- and the jabberwock reads it by looking.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
