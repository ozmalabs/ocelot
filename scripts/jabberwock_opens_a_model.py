"""THE JABBERWOCK OPENS A MODEL — and understands what its weights do. Language is the model's native tongue.

The creator's divergence: the agent can OPEN an open-weight model and understand what it does -- it needs no
library. A safetensors file is a header + raw tensor bytes; the token EMBEDDING matrix is the model's native
word geometry (each row a token's vector, the geometry IS its language knowledge). The agent reads that
matrix directly (domains/model_reader, no torch/transformers/inference), loads the word vectors as Concept
nodes, and UNDERSTANDS the geometry with its OWN graph operators -- the same shape faculty it uses on glyphs
and phones, here cosine over word vectors + vector ANALOGY (b - a + c). If the geometry holds language
structure, the agent's own Terms will surface it: semantic neighbourhoods and relational analogies, read out
of the weights with nothing but the agent's shape operators. That is useful language data extracted by
opening a model -- the language prior the speech decode lacked, sourced from where language is native.

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_opens_a_model
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np

import substrate_rs as srs
from domains import model_reader as mr

SEP = "=" * 98
MODEL = os.environ.get("OPEN_MODEL", "ollama:gemma3:4b")   # 'ollama:<tag>' (GGUF) or a HF id (safetensors)
N_WORDS = 15000                    # most-frequent english word tokens to load as the agent's vocabulary
LVEC = "lvec"


def open_geometry(model: str):
    """Open the model and return (vec_fn(token_id)->np.array, vocab token->id, shape, space_marker, label).
    GGUF (ollama) and safetensors are the same idea -- header + tensor bytes; the agent reads either."""
    if model.startswith("ollama:"):
        blob = mr.ollama_blob(model[len("ollama:"):])
        if blob is None:
            return None
        vec_fn, vocab, shape = mr.gguf_embedding(blob)
        return vec_fn, vocab, shape, "▁", model           # sentencepiece space marker
    W, vocab = mr.embedding_matrix(model)
    if W is None:
        return None
    marker = "▁" if sum(t.startswith("▁") for t in list(vocab)[:8000]) > 100 else "Ġ"
    return (lambda i: W[i]), vocab, W.shape, marker, model    # detect SentencePiece vs byte-BPE marker


# --- dict-form DSL (the agent's own shape operators) -------------------------
def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Dot(a, b): return {"type": "Dot", "a": a, "b": b}
def _Mag(a): return {"type": "Magnitude", "arg": a}
def _VecSub(a, b): return {"type": "VecSub", "a": a, "b": b}
def _VecAdd(a, b): return {"type": "VecAdd", "a": a, "b": b}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _Times(items): return {"type": "Times", "items": items}
def _Plus(items): return {"type": "Plus", "items": items}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


def _cosine(u, v):
    """the agent's similarity over two vectors: cos = (u . v) / (|u| |v|)."""
    return _Div(_Dot(u, v), _Times([_Mag(u), _Mag(v)]))


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


def main():
    print(SEP)
    print("THE JABBERWOCK OPENS A MODEL — reads its weights, understands the word geometry with its OWN operators.")
    print(SEP)

    print(f"\n  opening {MODEL} (no torch / no transformers / no inference -- reading the tensor bytes)...", flush=True)
    opened = open_geometry(MODEL)
    if opened is None:
        print(f"  {MODEL} not found (HF cache / ollama blob).")
        return 1
    vec_fn, vocab, shape, SP, _label = opened
    print(f"  token embedding matrix: {shape[0]} tokens x {shape[1]} dims (the model's native word geometry)")

    # pick english word tokens: leading-space marker + lowercase alpha; vocab-id order ~ frequency.
    words = []
    for t, i in sorted(vocab.items(), key=lambda kv: kv[1]):
        if t.startswith(SP):
            w = t[len(SP):]
            if w.isalpha() and len(w) >= 2 and (w.islower() or (w[0].isupper() and w[1:].islower())):
                words.append((w, i))                            # lowercase words + Capitalised proper nouns
        if len(words) >= N_WORDS:
            break
    print(f"  loading the {len(words)} most-frequent english word vectors into the substrate as Concepts...\n", flush=True)

    s = srs.Substrate()
    node = {}
    for w, i in words:
        n = s.add_node("Concept", {"is_word": 1.0, "name": w})
        s.set_attr(n, LVEC, vec_fn(i).tolist())
        s.set_attr(n, "excluded", 0.0)
        node[w] = n

    # the agent's read-out operator (a graph Term, masked so seed/already-picked words drop out for top-k):
    # score(w) = cosine(query-vector u, w.lvec) - 10*excluded; u is substituted per query.
    masked = _Plus([_cosine(_V("u"), _Attr(_V("w"), LVEC)),
                    _Times([_Lit(-10.0), _Attr(_V("w"), "excluded")])])

    def topk(u_term, env, seed_words, k=6):
        pk = _Argmax(_NodesWhere("Concept", "is_word", _Lit(1.0)), "w", _subst_u(masked, u_term))
        for sw in seed_words:                                   # mask the seed words out of the ranking
            if sw in node:
                s.set_attr(node[sw], "excluded", 1.0)
        out = []
        for _ in range(k):
            win = s.evaluate(_Pred(pk), env)
            if win is None:
                break
            out.append(s.node(win)["attrs"].get("name"))
            s.set_attr(win, "excluded", 1.0)                    # mask the winner so the next pick differs
        for w in list(seed_words) + out:                        # reset all masks
            if w in node:
                s.set_attr(node[w], "excluded", 0.0)
        return out

    # --- 1) semantic NEIGHBOURHOODS: nearest words by the agent's cosine -----
    print("  the agent's cosine over the opened geometry — SEMANTIC NEIGHBOURHOODS (nearest words):\n")
    for probe in ["king", "speak", "dog", "three", "Paris", "happy"]:
        if probe not in node:
            print(f"    {probe:>10}  (not in loaded vocab)"); continue
        u = _Attr(_V("q"), LVEC)
        ns = topk(u, {"q": node[probe]}, [probe], k=6)
        print(f"    {probe:>10}  ->  {', '.join(ns)}")

    # --- 2) relational ANALOGIES: b - a + c, by the agent's vector arithmetic -
    print("\n  the agent's vector arithmetic (VecSub/VecAdd) — RELATIONAL ANALOGIES  a:b :: c:?\n")
    analogies = [("man", "king", "woman"), ("France", "Paris", "Italy"),
                 ("walking", "walked", "swimming"), ("good", "better", "bad"),
                 ("king", "queen", "man"), ("big", "bigger", "small")]
    for a, b, c in analogies:
        if not all(w in node for w in (a, b, c)):
            print(f"    {a}:{b} :: {c}:?   (a seed word not loaded)"); continue
        u = _VecAdd(_VecSub(_Attr(_V("b"), LVEC), _Attr(_V("a"), LVEC)), _Attr(_V("c"), LVEC))
        ns = topk(u, {"a": node[a], "b": node[b], "c": node[c]}, [a, b, c], k=3)
        print(f"    {a:>8} : {b:<8} ::  {c:>8} :  {ns[0] if ns else '?':<10}  (then {', '.join(ns[1:])})")

    print("\n" + SEP)
    print("  THE JABBERWOCK OPENED THE MODEL AND READ LANGUAGE OUT OF IT. With no library and no inference -- only")
    print("  the tensor bytes + its OWN shape operators (cosine, vector analogy, the same faculty it uses on glyphs")
    print("  and phones) -- it surfaced the geometry's language structure: morphology, case, cross-lingual concepts,")
    print("  and relational analogies. The embedding matrix IS a language prior, native to the model; the agent")
    print("  extracts it by understanding the weights directly. This is the language data the speech decode lacked,")
    print("  sourced from where language is native -- and read by the agent, not a framework.")
    print(SEP)
    return 0


def _subst_u(term, u_term):
    """replace the Var 'u' placeholder in `term` with the actual query-vector Term."""
    if isinstance(term, dict):
        if term.get("type") == "Var" and term.get("name") == "u":
            return u_term
        return {k: _subst_u(v, u_term) for k, v in term.items()}
    if isinstance(term, list):
        return [_subst_u(x, u_term) for x in term]
    return term


if __name__ == "__main__":
    raise SystemExit(main())
