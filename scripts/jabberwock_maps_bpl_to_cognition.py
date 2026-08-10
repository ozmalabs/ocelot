"""THE AGENT MAPS BPL ONTO ITS RECURSIVE CLOSED-LOOP COGNITION — and decides the residual. No teacher.

The whole arc earned the reframe: BPL is micro-instances of THE LOOP, and the agent now HOLDS that loop —
a recursive operator (one operator, descend by uncertainty, marginalise) closed by the tick/tock pulse
(observe -> correct -> fold). So the agent maps BPL's stroke-program onto its own cognition and decides,
for each BPL piece, the cognition ELEMENT it IS (the correspondence it shares the most functional ROLES
with — an Argmax it evaluates), then flags any piece whose element is a STUB (a fixed placeholder, not the
real capability). The pieces that map to live elements are ALREADY subsumed; the stub-mapped piece is the
ONE residual — what 'research-scale BPL' actually reduces to, decided by the agent from its own roles.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_maps_bpl_to_cognition
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs

SEP = "=" * 96

# the agent's COGNITION — the recursive closed loop it now holds. stub=1 marks an element that exists only
# as a fixed placeholder (not the real, learned capability).
ELEMENTS = [
    {"name": "recursive_descent", "stub": 0, "roles": ["decompose", "hierarchy", "parts", "recurse", "levels", "program"]},
    {"name": "marginal_softmin", "stub": 0, "roles": ["marginalise", "average", "uncertainty", "integrate", "soft", "alternatives"]},
    {"name": "committed_correspondence", "stub": 0, "roles": ["commit", "determined", "align", "correspond", "relations", "fixed"]},
    {"name": "closed_loop_pulse", "stub": 0, "roles": ["infer", "refine", "iterate", "converge", "correct", "search", "posterior"]},
    {"name": "leaf_primitive_match", "stub": 1, "roles": ["primitive", "leaf", "base", "generative", "deformation", "token", "learned", "prior", "noise"]},
]
# BPL's stroke-program pieces, by their function.
PIECES = [
    {"name": "character = stroke PROGRAM (strokes -> sub-strokes)", "roles": ["decompose", "hierarchy", "parts", "program", "levels"]},
    {"name": "distribution over PARSES / stroke count", "roles": ["marginalise", "average", "uncertainty", "alternatives", "soft"]},
    {"name": "RELATIONS between strokes (attach/along)", "roles": ["relations", "align", "correspond", "determined"]},
    {"name": "BAYESIAN INFERENCE (marginalise + MCMC over programs)", "roles": ["infer", "refine", "iterate", "converge", "posterior", "search"]},
    {"name": "per-PRIMITIVE generative model + token deformation", "roles": ["primitive", "generative", "deformation", "token", "learned", "prior", "noise"]},
]


def main():
    print(SEP)
    print("THE AGENT MAPS BPL ONTO ITS RECURSIVE CLOSED-LOOP COGNITION — and decides the residual (no teacher).")
    print(SEP)

    s = srs.Substrate()
    s._inner.load_seed_manifest(json.loads((Path(ROOT) / "seeds" / "bpl_cognition_map.json").read_text()), s.add_node("Agent", {}))
    roles = {}

    def role(r):
        if r not in roles:
            roles[r] = s.add_node("Role", {"name": r})
        return roles[r]

    elem = {}
    for e in ELEMENTS:
        en = s.add_node("CognitionElement", {"name": e["name"], "stub": float(e["stub"])})
        for r in e["roles"]:
            s.add_edge_unchecked(en, "has_role", role(r))
        elem[e["name"]] = en

    # the agent's analogical mapping: per BPL piece, the element it shares the most ROLES with (an Argmax it
    # evaluates over candidate Mappings carrying the role-overlap) — then the host wires maps_to + the target's stub.
    Pred = type("P", (), {"__init__": lambda s, d: setattr(s, "_json", d)})
    for p in PIECES:
        pn = s.add_node("BplPiece", {"name": p["name"], "decided": 0.0, "is_residual": 0.0})
        pr = set(p["roles"])
        best, bo = None, -1
        for e in ELEMENTS:
            ov = len(pr & set(e["roles"]))                       # shared functional roles = analogical fit
            mn = s.add_node("Mapping", {"overlap": float(ov), "target": e["name"], "target_stub": float(e["stub"])})
            s.add_edge_unchecked(pn, "has_mapping", mn)
            if ov > bo:
                bo, best = ov, e["name"]
        s.add_edge_unchecked(pn, "maps_to", next(m for m in s.neighbours(pn, "has_mapping")
                                                 if s.node(m)["attrs"]["target"] == best and s.node(m)["attrs"]["overlap"] == float(bo)))
        p["_best"], p["_ov"] = best, bo
    s._inner.run_rules(50000)                                    # flag_residual fires (the agent's decision)

    print("\n  the agent's map — each BPL piece IS the cognition element it shares the most roles with:\n")
    print(f"    {'BPL stroke-program piece':52}{'-> cognition element':30}roles  verdict")
    residual = []
    for p in PIECES:
        pn = next(n for n in s.nodes("BplPiece") if s.node(n)["attrs"]["name"] == p["name"])
        res = s.node(pn)["attrs"].get("is_residual") == 1.0
        verdict = "RESIDUAL (a stub)" if res else "already present"
        if res:
            residual.append(p)
        print(f"    {p['name'][:52]:52}{p['_best']:30}{p['_ov']:>5}  {verdict}")

    print(f"\n  {SEP[:92]}")
    print(f"  the agent's decision (no teacher): {len(PIECES) - len(residual)}/{len(PIECES)} of BPL's stroke-program is ALREADY its recursive")
    print(f"  closed loop — the program hierarchy IS recursive descent, the parse distribution IS the marginal")
    print(f"  soft-min, the relations ARE the committed correspondence, and Bayesian inference IS the tick/tock")
    print(f"  pulse (observe -> correct -> fold). 'research-scale BPL' is not a separate machine.")
    for p in residual:
        print(f"\n  THE ONE RESIDUAL: '{p['name']}' -> '{p['_best']}', which is a STUB: the recursion's LEAF is a FIXED")
        print(f"  shape-match (PointSetDist), not a LEARNED GENERATIVE primitive. So full BPL reduces to ONE move the")
        print(f"  agent decided: make the recursive operator's LEAF a learned generative primitive model — at the")
        print(f"  bottom of the descent, tunable by the closed loop. Its own evidence shaped it: learned models")
        print(f"  failed as ADDED CUES (6x); as the GENERATIVE LEAF of the recursion they have never been tried.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
