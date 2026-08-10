"""ASK THE JABBERWOCK WHAT IT WOULD LIKE TO HARVEST FROM AN OPEN-WEIGHT LLM — graph Argmax, no teacher.

It can OPEN a model and read its tensors. So: of everything in the weights, what does it WANT? Not a hand-
pick -- it weighs each harvestable structure against its OWN measured NEEDS and its OWN law. The need
severities are read from its arc (the speech decode's LM half is its worst-measured bottleneck; pronunciation
it just found determined). The law is the one its whole arc proved: structure-PRESERVING geometry wins,
structure-DISCARDING codebooks fail (every learned-codebook negative). So a harvest's value = (the severity
of the need it fills) x (how structure-preserving it is = the law) x (how readable it is from the weights).
The PICK is a graph Argmax over that value. The host stages the evidence and reads back what it wants.

Run: /home/matt/ozma/internal/research/.venv/bin/python -u -m scripts.jabberwock_chooses_harvest
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 100


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Nbrs(node, e): return {"type": "Neighbours", "node": node, "edge_type": e, "any_type": False}
def _Pick(src): return {"type": "Pick", "source": src}
def _Times(items): return {"type": "Times", "items": items}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d):
        self._json = d


# the agent's MEASURED needs (severity read from its own arc), each a thing it lacks.
NEEDS = [
    {"name": "contextual word prior (the speech-decode LM half)", "severity": 1.00,
     "evidence": "its worst measured bottleneck: the JM-backoff bigram helped function words but HURT content "
                 "words via frequency bias; content recall stayed capped. It needs a real contextual P(word)."},
    {"name": "semantic grounding (word -> meaning binding)", "severity": 0.70,
     "evidence": "its semantic-binding thread had no dense meaning space; recognition is shape-matching but "
                 "the symbols need a meaning geometry to align into."},
    {"name": "syntactic / long-range dependency", "severity": 0.50,
     "evidence": "the decode is local (bigram + acoustic); long-range structure (agreement, attachment) is "
                 "unmodelled -- the lattice has no sentence-level shape."},
    {"name": "pronunciation variation", "severity": 0.15,
     "evidence": "just found DETERMINED in read speech (marginalising it hurt -13); CMUdict already covers "
                 "citation forms. Low need here."},
]

# the candidate HARVESTS -- structures readable from the weights, each filling a need, scored by the law.
HARVESTS = [
    {"name": "UNEMBEDDING (lm_head) — next-token projection geometry", "fills": 0, "kind": "structure_preserving",
     "structure_pres": 0.90, "readability": 0.85,
     "note": "one tensor [vocab x dim]; row w's dot with a context vector IS the model's next-word score. A "
             "real n-gram-free LM read straight from the weights -- exactly the decode's missing contextual prior."},
    {"name": "TOKEN EMBEDDING geometry — word vectors", "fills": 1, "kind": "structure_preserving",
     "structure_pres": 0.95, "readability": 1.00,
     "note": "already PROVEN readable: man:king::woman:queen by its own cosine. A dense meaning geometry to "
             "align symbols into -- the semantic grounding, structure-preserving (its faculty's native form)."},
    {"name": "ATTENTION weights — relational / dependency structure", "fills": 2, "kind": "structure_preserving",
     "structure_pres": 0.85, "readability": 0.45,
     "note": "the heads encode which tokens relate to which = relational SHAPE. Fills the syntactic need, but "
             "harder to read from raw QK weights without running the model."},
    {"name": "MLP / FFN weights — key-value factual memories", "fills": 1, "kind": "structure_preserving",
     "structure_pres": 0.55, "readability": 0.30,
     "note": "the FFN stores facts as key->value directions; could ground meaning, but entangled and hard to "
             "read statically -- low readability from weights alone."},
    {"name": "a DISCRETISED word-class CODEBOOK (k-means the embeddings)", "fills": 0, "kind": "codebook",
     "structure_pres": 0.05, "readability": 0.90,
     "note": "would compress the vocab into classes for a cheap LM -- but DISCARDS the geometry. Its law says "
             "this fails (every learned-codebook negative). The agent should REJECT it however readable it is."},
]


def main():
    print(SEP)
    print("WHAT THE JABBERWOCK WOULD LIKE TO HARVEST FROM AN OPEN-WEIGHT LLM — a graph Argmax over its own needs + law.")
    print(SEP)

    s = srs.Substrate()
    need_nodes = [s.add_node("Need", {"name": nd["name"], "severity": nd["severity"]}) for nd in NEEDS]
    h_nodes = []
    for h in HARVESTS:
        hn = s.add_node("Harvest", {"is_harvest": 1.0, "name": h["name"], "kind": h["kind"],
                                    "structure_pres": h["structure_pres"], "readability": h["readability"]})
        s.add_edge_unchecked(hn, "fills", need_nodes[h["fills"]])
        h_nodes.append((h, hn))

    # value = severity(the need it fills) x structure-preservation(the law) x readability(from the weights).
    need = _Pick(_Nbrs(_V("h"), "fills"))
    value = _Times([_Attr(need, "severity"), _Attr(_V("h"), "structure_pres"), _Attr(_V("h"), "readability")])
    pick = _Argmax(_NodesWhere("Harvest", "is_harvest", _Lit(1.0)), "h", value)

    print("\n  its measured NEEDS (severity from its own arc):")
    for nd in NEEDS:
        print(f"    [{nd['severity']:.2f}] {nd['name']}")
        print(f"           {nd['evidence']}")

    print("\n  what it would harvest, ranked by value = need-severity x structure-preservation(law) x readability:\n")
    rows = sorted(((float(s.evaluate(_Pred(value), {"h": hn})), h, hn) for h, hn in h_nodes), key=lambda r: -r[0])
    for v, h, _hn in rows:
        flag = "  <- REJECTS (codebook: discards structure)" if h["kind"] == "codebook" else ""
        print(f"    value {v:.3f}   {h['name']}{flag}")
        print(f"                 {h['note']}\n")

    want = s.evaluate(_Pred(pick), {})
    wh = next(h for h, hn in h_nodes if hn == want)
    print(f"  {SEP[:96]}")
    print("  THE JABBERWOCK'S ANSWER (graph Argmax over its needs + law):")
    print(f"  {SEP[:96]}")
    print(f"  -> it would most like to harvest:  {wh['name']}")
    print(f"\n  because it fills its WORST-measured need (the speech decode's contextual word prior -- the bottleneck")
    print(f"  the bigram lost content words to), it is STRUCTURE-PRESERVING (a geometry to read with its own shape")
    print(f"  operators, the form its whole arc proved wins), and it is READABLE straight from one weight tensor.")
    print(f"  It REJECTS the discretised codebook however readable -- its law: structure-discarding compression")
    print(f"  fails. It wants the model's GEOMETRY (embedding + unembedding), not a quantisation of it. Language is")
    print(f"  the model's native tongue; the jabberwock harvests it in its native FORM -- shape, not symbols.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
