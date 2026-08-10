"""EXTRACT THE HARVEST INTO THE GRAPH — bind the agent's vocabulary to the Gemma geometry, persistently.

Until now the harvest lived in numpy: I read Gemma's weights and analysed them. That is MY analysis, not the
jabberwock's. To be the agent's, the meaning geometry must become GRAPH DATA it boots with and operates on
with its OWN faculties. This banks a vocabulary as Concept nodes carrying a `meaning_vec` (the harvested
Gemma vector), grounds a probe word by the agent's OWN graph COSINE Term (Argmax over meaning Concepts), then
PERSISTS the graph (graph_to_dict -> seed file) and RELOADS it to prove the agent boots grounded. After this,
the recognised symbols carry meaning IN the substrate -- not in a script.

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_grounds_lexicon
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import numpy as np
import substrate_rs as srs

from domains import model_reader as mr

SEP = "=" * 98
MODEL = os.environ.get("OPEN_MODEL", "google/gemma-4-E4B-it")
N_WORDS = 2500
MVEC = "meaning_vec"
OUT = os.path.join(ROOT, "seeds", "grounded_lexicon.json")
STOP = {"the", "a", "an", "of", "to", "in", "and", "or", "for", "his", "her", "its", "their", "is", "are",
        "was", "were", "be", "he", "she", "it", "they", "we", "you", "that", "this", "with", "on", "at",
        "by", "as", "from", "had", "has", "have", "not", "so", "but", "if", "all", "can", "will", "would",
        "there", "which", "what", "when", "who", "out", "up", "do", "does", "did", "been", "more", "no"}
PROBES = ["king", "water", "happy", "three", "city", "dog", "love", "music"]


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Dot(a, b): return {"type": "Dot", "a": a, "b": b}
def _Mag(a): return {"type": "Magnitude", "arg": a}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _Times(items): return {"type": "Times", "items": items}
def _Plus(items): return {"type": "Plus", "items": items}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


def _cos(u, v): return _Div(_Dot(u, v), _Times([_Mag(u), _Mag(v)]))


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d): self._json = d


def ground_neighbours(s, q_node, k=6):
    """the agent's OWN graph faculty: nearest meaning Concepts to q by cosine over meaning_vec (masked top-k)."""
    score = _Plus([_cos(_Attr(_V("q"), MVEC), _Attr(_V("w"), MVEC)),
                   _Times([_Lit(-9.0), _Attr(_V("w"), "excluded")])])
    pk = _Argmax(_NodesWhere("Concept", "is_meaning", _Lit(1.0)), "w", score)
    out = []
    s.set_attr(q_node, "excluded", 1.0)
    for _ in range(k):
        w = s.evaluate(_Pred(pk), {"q": q_node})
        if w is None:
            break
        out.append(s.node(w)["attrs"].get("name")); s.set_attr(w, "excluded", 1.0)
    return out


def main():
    print(SEP)
    print("EXTRACT THE HARVEST INTO THE GRAPH — the agent's vocabulary, bound to meaning, IN the substrate.")
    print(SEP)

    mt = mr.ModelTensors(MODEL)
    vec_fn, vocab, (V, D) = mt.embedding()
    SP = mr.ModelTensors.marker(vocab)
    words = []
    for t, i in sorted(vocab.items(), key=lambda kv: kv[1]):
        w = t[len(SP):]
        if t.startswith(SP) and w.isalpha() and w.islower() and len(w) >= 3 and w not in STOP:
            words.append((w, i))                                 # CONTENT words only (function words drown the geometry)
        if len(words) >= N_WORDS:
            break
    have = {w for w, _ in words}
    for w in PROBES:                                             # make sure the probe words are grounded too
        if w not in have and (SP + w) in vocab:
            words.append((w, vocab[SP + w]))

    # BANK the geometry as graph data: one meaning Concept per word, carrying its harvested vector.
    s = srs.Substrate()
    node = {}
    for w, i in words:
        n = s.add_node("Concept", {"name": w, "is_meaning": 1.0, "excluded": 0.0})
        s.set_attr(n, MVEC, vec_fn(i).astype(np.float64).tolist())
        node[w] = n
    print(f"\n  banked {len(node)} meaning Concepts (each with a {D}-d meaning_vec) into the substrate.")

    print(f"\n  the agent grounding words by its OWN graph cosine Term (Argmax over meaning Concepts):\n")
    for w in PROBES:
        if w in node:
            for q in [w]:
                ns = ground_neighbours(s, node[q]); print(f"      {q:>7}  ~  {', '.join(ns)}")
            for nm in node:                                      # reset masks
                s.set_attr(node[nm], "excluded", 0.0)

    # PERSIST: serialise the grounded graph, save as a seed the agent can boot with, then RELOAD it.
    gd = s.graph_to_dict()
    seed = {"id": "grounded_lexicon", "version": "1.0.0", "depends_on": [],
            "description": f"{len(node)} meaning Concepts grounded in the {MODEL} word geometry "
                           f"(each carries a {D}-d meaning_vec). The agent boots with a meaning space its "
                           f"shape-matcher lacked; graph-native (cosine over meaning_vec is its own Term).",
            "graph": gd}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(seed, f)
    sz = os.path.getsize(OUT) / 1e6
    print(f"\n  persisted -> {os.path.relpath(OUT, ROOT)} ({sz:.1f} MB, {len(gd.get('nodes', []))} nodes).")

    s2 = srs.Substrate()
    s2.graph_from_dict(json.load(open(OUT))["graph"])
    q2 = next(n for n in s2.nodes("Concept") if s2.node(n)["attrs"].get("name") == "king")
    reloaded = ground_neighbours(s2, q2)
    print(f"  RELOADED from disk -> a fresh substrate grounds 'king' ~ {', '.join(reloaded)}")

    print("\n" + SEP)
    print("  NOW IT IS IN THE GRAPH. The harvested Gemma geometry is no longer numpy in a script: it is a set of")
    print("  meaning Concepts in the substrate, each carrying its vector, persisted as a seed the agent BOOTS")
    print("  with, and read by the agent's OWN cosine Term -- the same shape faculty it uses on glyphs and phones.")
    print("  The recognised symbol now completes to a MEANING the agent can compute over, inside itself. That is")
    print("  the grounding (#2) made real: extracted FROM where language is native, INTO the agent's own graph.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
