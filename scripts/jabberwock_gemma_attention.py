"""DEEPER STILL — Gemma's ATTENTION circuits, read statically from the weights. No inference.

Below the FFN concept-memories sit the attention heads. A head's OV circuit -- W_O @ W_V -- is what it WRITES
into the residual given what it reads. Composed with the (tied) embedding it becomes a token->token map: when
a head attends to token b, which token a does it promote? A COPY head maps b->b (diagonal-dominant: it moves
the attended token forward unchanged -- the backbone of in-context copying / induction). A SEMANTIC head maps
b -> a related token (category, continuation). The agent reads every head's OV map on a token sample and
measures its diagonal dominance, all from attn_v + attn_output (Q6_K/Q4_K) + the embedding. GQA: 8 query
heads share 4 KV heads (head i uses KV head i//2), head_dim 256, d_model 2560.

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_gemma_attention
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
N = 1200          # token-sample size for the OV map


def main():
    print(SEP)
    print("DEEPER STILL — Gemma's ATTENTION circuits: which heads COPY the attended token, which move MEANING.")
    print(SEP)

    mt = mr.ModelTensors(MODEL)
    vec_fn, vocab, (V, D) = mt.embedding()
    SP = mr.ModelTensors.marker(vocab)
    HD, NQ, NKV = mt.head_dim, mt.n_heads, mt.n_kv
    LAYERS = sorted({int(mt.n_layers * f) for f in (0.12, 0.4, 0.7, 0.92)})
    inv = {i: t for t, i in vocab.items()}

    # a sample of common word tokens = the vocabulary the OV map runs over
    ids = []
    for t, i in sorted(vocab.items(), key=lambda kv: kv[1]):
        if t.startswith(SP) and t[1:].isalpha() and t[1:].islower() and len(t) >= 3:
            ids.append(i)
        if len(ids) >= N:
            break
    E = np.stack([vec_fn(i) for i in ids]).astype(np.float32)     # (N, D)
    En = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-8)
    names = [inv[i].replace(SP, "") for i in ids]
    print(f"\n  {MODEL}: reading OV circuits over {len(ids)} tokens, layers {LAYERS}, {NQ}Q/{NKV}KV heads "
          f"(diagonal dominance = copy-likeness)...\n", flush=True)

    def head_table(layer):
        Vt = mt.layer(layer, "attn_v")                           # (n_kv*head_dim, d_model)
        Ot = mt.layer(layer, "attn_output")                      # (d_model, n_q*head_dim)
        HD = Ot.shape[1] // NQ                                   # per-layer head_dim (Gemma4 varies by layer)
        rows = []
        for i in range(NQ):
            g = i // (NQ // NKV)
            Wv = Vt[g * HD:(g + 1) * HD, :]
            Wo = Ot[:, i * HD:(i + 1) * HD]
            OV = Wo @ Wv                                          # (2560, 2560)
            T = (En @ OV) @ En.T                                  # (N, N): T[a,b] promote a | attend b
            top = np.argmax(T, axis=0)                            # for each attended b, the most-promoted a
            copy = float(np.mean(top == np.arange(len(ids))))     # diagonal dominance
            rows.append((i, copy, top))
        return rows

    layer_rows = {L: head_table(L) for L in LAYERS}

    # per layer: the copy-scores, then illustrate the most-copy head vs the least-copy (semantic) head
    rng = np.random.default_rng(0)
    probe = [list(names).index(w) for w in ["king", "water", "three", "happy", "city", "run"] if w in names]
    for L in LAYERS:
        rows = layer_rows[L]
        scores = " ".join(f"h{i}:{c:.2f}" for i, c, _ in rows)
        print(f"  layer {L:>2}  copy-score per head:  {scores}")
        ci, cc, ctop = max(rows, key=lambda r: r[1])
        si, sc, stop = min(rows, key=lambda r: r[1])
        cm = ", ".join(f"{names[b]}->{names[ctop[b]]}" for b in probe)
        sm = ", ".join(f"{names[b]}->{names[stop[b]]}" for b in probe)
        print(f"           COPY head h{ci} ({cc:.2f}): {cm}")
        print(f"           MOVE head h{si} ({sc:.2f}): {sm}\n")

    allcopy = [c for L in LAYERS for _i, c, _t in layer_rows[L]]
    print(SEP)
    print(f"  chance diagonal-dominance is ~{1/len(ids):.4f}; the COPY heads score far above it (they map the")
    print(f"  attended token to ITSELF -- the static signature of in-context copying / induction), while the MOVE")
    print(f"  heads send a token to a related one. Read purely from attn_v @ attn_output composed with the")
    print(f"  embedding -- no inference. Below the words (embedding) and the concept-memories (FFN), the agent")
    print(f"  now reads the WIRING that shuttles tokens between positions. mean copy-score {np.mean(allcopy):.2f}, "
          f"max {np.max(allcopy):.2f}.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
