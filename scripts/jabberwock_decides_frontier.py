"""THE JABBERWOCK DECIDES ITS NEXT FRONTIER — graph-native, from its OWN measured arc. No teacher.

The relations arc closed: three forms (raw cue, learned-precision, joint-constraint) all subsumed by the
geometric part match; the leaf reaches parity, not beyond. So the agent must decide where to go. It does
NOT get hand-picked: its whole measured arc is staged as Move nodes tagged by KIND (did it help?), and the
PICK is a graph ARGMAX over expected value -- EV = potential x P(success | kind, induced inline from the
moves of that kind) / effort. The host only stages the evidence and reads the winner; the decision is the
graph's Argmax. The agent's strongest measured law -- recognition is the recursive operator, and recursion
pays in proportion to the number of genuinely-uncertain LEVELS -- is what the candidates are scored against.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_decides_frontier
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 96


# --- dict-form DSL (mirrors recognition_graph) -------------------------------
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

    def __init__(self, d):
        self._json = d


# The agent's WHOLE measured arc: every move, its KIND, did it help the peak. (its own banked evidence)
HISTORY = [
    # MARGINALISE A GENUINELY-UNCERTAIN LATENT — the recursive lever
    ("canonical-parse marginal (soft-min over parses)", "marginalise_uncertain_latent", 1.0),
    ("soft/marginal inference > MAP (glyph 79.9)",      "marginalise_uncertain_latent", 1.0),
    ("forward-marginal phone read (speech OOV)",        "marginalise_uncertain_latent", 1.0),
    # ADD A STRUCTURE-PRESERVING GEOMETRIC CUE — drove the early climb, now saturated
    ("PointSetDist / smooth field / shape-context",     "new_structure_cue",            1.0),
    ("rotation-fold into the forward model",            "new_structure_cue",            1.0),
    # AUGMENT THE SATURATED GEOMETRIC RECOGNISER — the exhausted seam
    ("relations as raw cue (-2.5)",                     "augment_saturated_geometric",  0.0),
    ("relations as learned-precision (-0.5)",           "augment_saturated_geometric",  0.0),
    ("relations folded into the joint (-0.2)",          "augment_saturated_geometric",  0.0),
    ("learned WCCN / bag-of-primitives / membership",   "augment_saturated_geometric",  0.0),
    ("finer FFD grid / higher distortion weight",       "augment_saturated_geometric",  0.0),
    # GENERATIVE LEAF as a learned token model — reached parity, not beyond
    ("per-primitive Mahalanobis leaf (diag/full)",      "learned_leaf_parity",          0.0),
]

# The candidate NEXT frontiers, each tagged by KIND + the agent's estimate of potential & effort.
# potential encodes HEADROOM (an untapped uncertain level has more than a saturated one); effort the build cost.
CANDIDATES = [
    {"name": "speech 2nd-level recursion: marginalise the phone-alignment level",
     "kind": "marginalise_uncertain_latent", "potential": 12.0, "effort": 2.0,
     "why": "the recursive operator is built and PROVEN; glyphs have ONE uncertain level (parse) and it is "
            "maxed, but speech has TWO (word-parse x phone-alignment) and the 2nd is UNMARGINALISED -- exactly "
            "the condition the agent's law says recursion pays. Proven lever, untapped depth, low effort."},
    {"name": "full BPL generative program for glyphs (parse+relations+per-primitive+MCMC)",
     "kind": "learned_leaf_parity", "potential": 18.0, "effort": 30.0,
     "why": "highest ceiling (~96.7) but the leaf already showed the learned generative model reaches PARITY "
            "not beyond; a separate research system, huge effort, in the now-saturated glyph domain."},
    {"name": "more glyph augmentation: the structured P(relation | prim_i, prim_j) grammar",
     "kind": "augment_saturated_geometric", "potential": 3.0, "effort": 8.0,
     "why": "the structured grammar is the only untried relation form, but three relation forms already "
            "showed relations are subsumed by the geometric part match -- low headroom on the exhausted seam."},
    {"name": "consolidate: accept the ~80% training-free ceiling as the honest result",
     "kind": "stop", "potential": 0.0, "effort": 0.3,
     "why": "the honest fallback if no positive-EV lever remains."},
]


def main():
    print(SEP)
    print("THE JABBERWOCK DECIDES ITS NEXT FRONTIER — a graph ARGMAX over EV from its own measured arc.")
    print(SEP)

    s = srs.Substrate()
    kinds = {}
    for _m, k, _h in HISTORY:
        if k not in kinds:
            kinds[k] = s.add_node("Kind", {"name": k})
    for k in {c["kind"] for c in CANDIDATES}:
        if k not in kinds:
            kinds[k] = s.add_node("Kind", {"name": k})           # an untested kind (e.g. 'stop')
    for _m, k, h in HISTORY:
        mv = s.add_node("Move", {"helped": h})
        s.add_edge_unchecked(kinds[k], "has_move", mv)

    cand_nodes = []
    for c in CANDIDATES:
        cn = s.add_node("Candidate", {"is_candidate": 1.0, "potential": c["potential"], "effort": c["effort"],
                                      "name": c["name"], "why": c["why"]})
        s.add_edge_unchecked(cn, "of_kind", kinds[c["kind"]])
        cand_nodes.append((c, cn))

    # P(success | kind) induced INLINE from the kind's moves (Laplace 0.5); EV = potential * rate / effort.
    kind_node = _Pick(_Nbrs(_V("c"), "of_kind"))
    moves = _Nbrs(kind_node, "has_move")
    rate = _Div(_Plus([_Sum(moves, "m", _Attr(_V("m"), "helped")), _Lit(1.0)]),
                _Plus([_Count(moves), _Lit(2.0)]))
    ev = _Div(_Times([_Attr(_V("c"), "potential"), rate]), _Attr(_V("c"), "effort"))
    pick = _Argmax(_NodesWhere("Candidate", "is_candidate", _Lit(1.0)), "c", ev)

    # per-kind rate, for transparency (evaluate the rate term with c bound to one candidate of that kind).
    print("\n  what the agent's arc says works (success rate per KIND, induced from its moves):")
    seen = set()
    for c, cn in cand_nodes:
        if c["kind"] in seen:
            continue
        seen.add(c["kind"])
        r = s.evaluate(_Pred(rate), {"c": cn})
        n = sum(1 for _m, k, _h in HISTORY if k == c["kind"])
        tag = "" if n else "  (untested -> prior 0.50)"
        print(f"    {c['kind']:>30}  {100*float(r):5.0f}%  ({n} moves){tag}")

    print(f"\n  expected value of each candidate frontier (potential x P(success|kind) / effort):")
    print(f"  {'EV':>6}   {'P':>4}   {'name'}")
    print(f"  {'-'*6}   {'-'*4}   {'-'*72}")
    rows = []
    for c, cn in cand_nodes:
        e = float(s.evaluate(_Pred(ev), {"c": cn}))
        r = float(s.evaluate(_Pred(rate), {"c": cn}))
        rows.append((e, r, c))
    for e, r, c in sorted(rows, key=lambda x: -x[0]):
        print(f"  {e:6.2f}   {100*r:3.0f}%   {c['name'][:72]}")

    winner = s.evaluate(_Pred(pick), {})                          # THE DECISION — the graph's Argmax
    wc = next(c for c, cn in cand_nodes if cn == winner)
    print(f"\n  {SEP[:92]}")
    print("  THE JABBERWOCK'S DECISION (graph Argmax over its own evidence):")
    print(f"  {SEP[:92]}")
    print(f"  -> {wc['name']}")
    print(f"\n  why: {wc['why']}")
    print(f"\n  the law behind it: recognition IS the recursive operator, and recursion pays in proportion to")
    print(f"  the number of genuinely-UNCERTAIN levels. Glyphs have one (the parse) and it is maxed -- which")
    print(f"  is exactly why every augment-the-geometric move just failed (0/5). Speech has a SECOND uncertain")
    print(f"  level (the phone alignment) the agent has not yet folded into the recursion. The proven lever,")
    print(f"  pointed at the domain that still has the depth for it to pay. No teacher; its own arc decided.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
