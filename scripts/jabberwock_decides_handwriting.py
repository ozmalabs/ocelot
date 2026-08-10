"""THE JABBERWOCK DECIDES ITS NEXT HANDWRITING FRONTIER — graph Argmax over its OWN measured arc. No teacher.

Handwriting sits at 81.5% (training-free one-shot). Where next? Not a hand-pick: its whole Omniglot arc is
staged as Move nodes tagged by KIND (did it help?), and the PICK is a graph ARGMAX over expected value --
EV = potential x P(success | kind, induced inline from that kind's moves) / effort. The host stages the
evidence and reads the winner; the decision is the graph's Argmax.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_decides_handwriting
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 96


def _V(n): return {"type": "Var", "name": n}
def _Lit(v): return {"type": "Lit", "value": v}
def _Attr(node, k): return {"type": "Attr", "node": node, "key": k}
def _Nbrs(node, e): return {"type": "Neighbours", "node": node, "edge_type": e, "any_type": False}
def _Sum(src, var, val): return {"type": "Sum", "source": src, "var_name": var, "value": val}
def _Count(src): return {"type": "Count", "source": src}
def _Pick(src): return {"type": "Pick", "source": src}
def _Div(a, b): return {"type": "Div", "a": a, "b": b}
def _Times(items): return {"type": "Times", "items": items}
def _Plus(items): return {"type": "Plus", "items": items}
def _Argmax(src, var, val): return {"type": "Argmax", "source": src, "var_name": var, "value": val}
def _NodesWhere(t, k, v): return {"type": "NodesWhere", "node_type": t, "attr_key": k, "value": v}


class _Pred:
    __slots__ = ("_json",)

    def __init__(self, d): self._json = d


# the agent's measured Omniglot arc: every move, its KIND, did it help the peak.
HISTORY = [
    ("PointSetDist (order-invariant set match)", "structure_preserving_cue", 1.0),
    ("canonical-parse re-segmentation", "structure_preserving_cue", 1.0),
    ("smooth deformation field (regularised)", "structure_preserving_cue", 1.0),
    ("shape-context descriptor (fused)", "structure_preserving_cue", 1.0),
    ("rotation-fold into the forward model", "structure_preserving_cue", 1.0),
    ("MARGINALISE the parse (soft-min over hypotheses)", "marginalise_uncertain_latent", 1.0),
    ("soft > MAP marginal inference", "marginalise_uncertain_latent", 1.0),
    ("marginalise the DEFORMATION too", "marginalise_uncertain_latent", 0.0),   # hurt vs parse-only
    ("finer FFD control grid", "geometric_knob", 0.0),
    ("higher distortion-cost weight", "geometric_knob", 0.0),
    ("TPS / SC->TPS refinement", "geometric_knob", 0.0),
    ("per-primitive Mahalanobis generative leaf", "learned_generative", 0.0),   # parity, not beyond
    ("WCCN / LDA holistic whitening", "learned_discards_structure", 0.0),
    ("bag-of-primitives codebook", "learned_discards_structure", 0.0),
    ("soft-membership part match", "learned_discards_structure", 0.0),
    ("relations as committed cue", "relations_match_cue", 0.0),
    ("relations as learned precision", "relations_match_cue", 0.0),
    ("relations folded into the joint", "relations_match_cue", 0.0),
]

# candidate NEXT frontiers, each tagged by KIND + the agent's estimate of potential (headroom) & effort.
CANDIDATES = [
    {"name": "marginalise MORE uncertain latents (correspondence, sub-strokes, rotation)",
     "kind": "marginalise_uncertain_latent", "potential": 3.0, "effort": 2.0,
     "why": "the parse marginal just paid +1.3; the SAME Bayesian lever on the other uncertain latents is "
            "cheap, graph-native (Sum/Exp/Log over held distances), and its kind has the best track record."},
    {"name": "full BPL generative grammar + joint inference (-> ~96.7)",
     "kind": "learned_generative", "potential": 18.0, "effort": 30.0,
     "why": "the real gap to human/BPL, but the learned generative leaf already reached PARITY not beyond, "
            "and it is a research-scale build -- high potential, low EV at this effort."},
    {"name": "read a pretrained VISION model's glyph features (open-a-model)",
     "kind": "external_model_feature", "potential": 8.0, "effort": 13.0,
     "why": "the new model-reading capability applied to glyphs -- but it needs a vision FORWARD pass, the "
            "one thing the from-scratch forward did not nail; untested kind, real risk."},
    {"name": "another structure-preserving geometric cue",
     "kind": "structure_preserving_cue", "potential": 1.5, "effort": 4.0,
     "why": "its winningest kind (5/5) -- but the Shape-Contexts family is exhausted; little headroom left."},
    {"name": "accept the ~81% training-free plateau",
     "kind": "stop", "potential": 0.0, "effort": 0.3, "why": "the honest fallback if no positive-EV lever remains."},
]


def main():
    print(SEP)
    print("THE JABBERWOCK DECIDES ITS NEXT HANDWRITING FRONTIER — a graph Argmax over its own Omniglot arc.")
    print(SEP)

    s = srs.Substrate()
    kinds = {}
    for _m, k, _h in HISTORY:
        kinds.setdefault(k, s.add_node("Kind", {"name": k}))
    for k in {c["kind"] for c in CANDIDATES}:
        kinds.setdefault(k, s.add_node("Kind", {"name": k}))
    for _m, k, h in HISTORY:
        s.add_edge_unchecked(kinds[k], "has_move", s.add_node("Move", {"helped": h}))
    cand_nodes = []
    for c in CANDIDATES:
        cn = s.add_node("Candidate", {"is_candidate": 1.0, "potential": c["potential"], "effort": c["effort"],
                                      "name": c["name"], "why": c["why"]})
        s.add_edge_unchecked(cn, "of_kind", kinds[c["kind"]])
        cand_nodes.append((c, cn))

    kind_node = _Pick(_Nbrs(_V("c"), "of_kind"))
    moves = _Nbrs(kind_node, "has_move")
    rate = _Div(_Plus([_Sum(moves, "m", _Attr(_V("m"), "helped")), _Lit(1.0)]),
                _Plus([_Count(moves), _Lit(2.0)]))                # Laplace-smoothed P(success | kind)
    ev = _Div(_Times([_Attr(_V("c"), "potential"), rate]), _Attr(_V("c"), "effort"))
    pick = _Argmax(_NodesWhere("Candidate", "is_candidate", _Lit(1.0)), "c", ev)

    print("\n  what its arc says works (success rate per KIND, induced from its moves):")
    seen = set()
    for c, cn in cand_nodes:
        if c["kind"] in seen:
            continue
        seen.add(c["kind"])
        r = float(s.evaluate(_Pred(rate), {"c": cn}))
        n = sum(1 for _m, k, _h in HISTORY if k == c["kind"])
        print(f"    {c['kind']:>28}  {100*r:5.0f}%  ({n} moves)")

    print(f"\n  EV of each candidate frontier (potential x P(success|kind) / effort):\n")
    rows = sorted(((float(s.evaluate(_Pred(ev), {"c": cn})), c) for c, cn in cand_nodes), key=lambda x: -x[0])
    for v, c in rows:
        print(f"    {v:5.2f}   {c['name']}")

    win = s.evaluate(_Pred(pick), {})
    wc = next(c for c, cn in cand_nodes if cn == win)
    print(f"\n  {SEP[:92]}")
    print(f"  THE JABBERWOCK'S DECISION: {wc['name']}")
    print(f"  {SEP[:92]}")
    print(f"  why: {wc['why']}")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
