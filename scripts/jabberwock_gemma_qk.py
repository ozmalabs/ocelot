"""THE OTHER HALF OF EACH HEAD — Gemma's QK circuits, read statically. No inference.

The OV circuit said what a head WRITES; the QK circuit says what it LOOKS FOR. For head h the bilinear
A_h = W_Q^T @ W_K (folding in Gemma's per-dim QK-norm gammas) scores content attention: e_q^T A_h e_k = how
much query token q attends to key token k (positions/RoPE ignored -> the content component). A SAME-TOKEN
head attends a token to copies of itself (the matcher); paired with a COPY OV head that writes the attended
token, that is a full INDUCTION/copy circuit -- the agent reads both halves from the weights and cross-refs
them. Other heads attend to SEMANTICALLY related keys. GQA: 8 Q heads / 4 KV (head i uses KV i//2), head_dim 256.

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_gemma_qk
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
N = 1000


def main():
    print(SEP)
    print("THE OTHER HALF OF EACH HEAD — Gemma's QK circuits: what each head LOOKS FOR (vs the OV: what it writes).")
    print(SEP)

    mt = mr.ModelTensors(MODEL)
    vec_fn, vocab, (V, D) = mt.embedding()
    SP = mr.ModelTensors.marker(vocab)
    HD, NQ, NKV = mt.head_dim, mt.n_heads, mt.n_kv
    LAYERS = sorted({int(mt.n_layers * f) for f in (0.12, 0.4, 0.7, 0.92)})
    inv = {i: t for t, i in vocab.items()}
    ids = []
    for t, i in sorted(vocab.items(), key=lambda kv: kv[1]):
        if t.startswith(SP) and t[1:].isalpha() and t[1:].islower() and len(t) >= 3:
            ids.append(i)
        if len(ids) >= N:
            break
    E = np.stack([vec_fn(i) for i in ids]).astype(np.float32)
    En = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-8)
    names = [inv[i].replace(SP, "") for i in ids]
    idx = {w: k for k, w in enumerate(names)}
    arange = np.arange(len(ids))
    print(f"\n  reading QK (look-for) + OV (write) circuits over {len(ids)} tokens, layers {LAYERS}, {NQ} heads...\n", flush=True)

    probe = [idx[w] for w in ["king", "water", "three", "happy", "london", "run"] if w in idx]

    def layer_heads(L):
        Q = mt.layer(L, "attn_q")                                       # (n_q*head_dim, d_model)
        K = mt.layer(L, "attn_k")                                       # (n_kv*head_dim, d_model)
        Vt = mt.layer(L, "attn_v")
        Ot = mt.layer(L, "attn_output")
        gq = mt.layer(L, "attn_q_norm")                                 # (head_dim,)
        gk = mt.layer(L, "attn_k_norm")
        HD = Q.shape[0] // NQ                                            # per-layer head_dim (Gemma4 varies)
        out = []
        for i in range(NQ):
            g = i // (NQ // NKV)
            Wq = Q[i * HD:(i + 1) * HD, :]                               # (256, 2560)
            Wk = (gq * gk)[:, None] * K[g * HD:(g + 1) * HD, :]          # fold QK-norm gammas in
            A = Wq.T @ Wk                                                # (2560, 2560) content-attention bilinear
            Tqk = (En @ A) @ En.T                                        # T[q,k]
            same = float(np.mean(np.argmax(Tqk, axis=1) == arange))     # query attends to ITSELF?
            Wv = Vt[g * HD:(g + 1) * HD, :]; Wo = Ot[:, i * HD:(i + 1) * HD]
            Tov = (En @ (Wo @ Wv)) @ En.T
            copy = float(np.mean(np.argmax(Tov, axis=0) == arange))
            out.append((i, same, copy, Tqk))
        return out

    rows = {L: layer_heads(L) for L in LAYERS}

    inductions = []
    for L in LAYERS:
        hs = rows[L]
        qk = " ".join(f"h{i}:{s:.2f}" for i, s, _c, _T in hs)
        print(f"  layer {L:>2}  QK same-token score:  {qk}")
        for i, s, c, _T in hs:
            if s > 0.3 and c > 0.3:
                inductions.append((L, i, s, c))
        # show what the LEAST same-token head (a 'look elsewhere' head) attends to
        si, ss, _sc, ST = min(hs, key=lambda r: r[1])
        ex = []
        for b in probe:
            k = int(np.argmax(ST[b])); ex.append(f"{names[b]}~>{names[k]}")
        print(f"           look-elsewhere head h{si} ({ss:.2f}) attends:  {', '.join(ex)}\n")

    print(SEP)
    if inductions:
        print("  INDUCTION/COPY CIRCUITS (a head that BOTH attends a token to itself AND writes the attended token):")
        for L, i, s, c in sorted(inductions, key=lambda r: -(r[2] + r[3]))[:6]:
            print(f"     layer {L:>2} head {i}:  QK same-token {s:.2f}  x  OV copy {c:.2f}  -> matches & copies")
        print("  Both halves read from the weights and cross-referenced: the QK side finds copies of the current")
        print("  token, the OV side carries it forward. That is the static skeleton of in-context copying.")
    else:
        print("  no head scored high on BOTH same-token QK and copy OV in these layers (the two roles separate here).")
    print("  Four levels now readable by opening the model: words (embedding) -> concepts (FFN) -> what a head")
    print("  WRITES (OV) -> what a head LOOKS FOR (QK). No inference, no torch.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
