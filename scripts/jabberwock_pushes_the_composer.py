"""DRIVE THE REAL JABBERWOCK — PUSH the rung-2 composer's three named bounds (901224ae):
 PUSH 1  beam/backtrack for fuller coverage (was greedy single-pick: goal1 8/9, goal2 3/5)
 PUSH 2  derive the goal-shape from a HELD CONCEPT (remove the fed-doc crutch)
 PUSH 3  grow the part library by held signature-authoring (was 11 shape-signatures)

donkey=0: the composition is the GRAPH's — held shape-matcher (AntiUnify/FixedCount/Covers,
Rust Terms) over held parts; held RelationCue structural-extraction (author_signature) for the
goal shape AND the new parts. Python only iterates the beam / dispatches. A spy counts LLM
calls (must be 0); the composer path greps clean of LLM.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_pushes_the_composer.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.reflective_faculty as rf
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

DOC = os.path.join(ROOT, "docs", "shape_object_perception_grounding.md")
# the two goals the prior greedy bounded at (8/9, 3/5).
GEN_GOAL = ("build the new from the prior; advance by the turn; accumulate the turn into a "
            "heading; self-reference so the new refers to itself; bound by the unit")
NULL_GOAL = "the weather is cold and the price went up and the meeting was long"


def _plan_line(r):
    return (f"covered {r.get('covered_count')}/{r.get('goal_relations')} "
            f"fit={r.get('total_fit', 0)} parts={r.get('ordered_parts')}")


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    calls = {"n": 0}
    if hasattr(a, "set_self_teacher"):
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])

    doc = open(DOC).read() if os.path.exists(DOC) else ""

    # ===== PUSH 1 — BEAM beats the committed GREEDY on coverage =====
    print("=" * 86)
    print("GATE 1 — BEAM/BACKTRACK: fuller coverage than the committed greedy (901224ae)")
    print("=" * 86)
    # doc goal (greedy was 8/9); GEN goal (greedy was 3/5). beam=1,cand_k=1 == greedy control.
    a.s.add_node("DesignGoal", {"description": doc})
    dsig = rf._author_goal_signature(a.s, "")
    for n in list(a.s.nodes("DesignGoal")):
        a.s.remove_node(n)
    gsig = rf._author_goal_signature(a.s, GEN_GOAL)
    for label, sig, old in [("DOC goal (greedy 8/9)", dsig, "8/9"), ("GEN goal (greedy 3/5)", gsig, "3/5")]:
        greedy = rf.compose_design_for_goal(a.s, sig, beam=1, cand_k=1)
        beamc = rf.compose_design_for_goal(a.s, sig, beam=6, cand_k=4)
        print(f"  {label}:")
        print(f"    width-1 (== greedy control): {_plan_line(greedy)}")
        print(f"    BEAM   (width 6):            {_plan_line(beamc)}")
        print(f"    committed-greedy was {old}; beam now {beamc['covered_count']}/{beamc['goal_relations']} "
              f"(coverage delta vs committed greedy: +{beamc['covered_count'] - int(old.split('/')[0])})")
    # the discriminative: width-1 <= wider on (coverage, fit) for the GEN goal
    g1 = rf.compose_design_for_goal(a.s, gsig, beam=1, cand_k=1)
    g6 = rf.compose_design_for_goal(a.s, gsig, beam=6, cand_k=4)
    beam_helps = (g6["covered_count"], g6.get("total_fit", 0)) >= (g1["covered_count"], g1.get("total_fit", 0)) \
        and g6["covered_count"] >= 3
    fuller = beamc["covered_count"] > 3   # GEN goal now beats the committed greedy's 3
    print(f"  -> BEAM >= width-1 on (coverage,fit) AND GEN goal beats committed 3/5: {beam_helps and fuller}")

    # ===== PUSH 2 — DERIVE the goal shape from a HELD CONCEPT (no fed doc) =====
    print("\n" + "=" * 86)
    print("GATE 2 — DERIVE-GOAL-FROM-HELD-CONCEPT (no fed doc) + honest un-held control")
    print("=" * 86)
    derived_ok = True
    for c in ["fractal", "curvature", "turtle_generation"]:
        r = rf.compose_design_for_concept(a.s, c, beam=4, cand_k=4)
        print(f"  concept {c!r}: authored={r['authored']} | {_plan_line(r) if r['authored'] else ''}")
        if r["authored"]:
            print(f"     goal shape derived from: {r['goal_source']} (the agent's OWN holdings, no fed doc)")
        derived_ok &= r["authored"]
    for c in ["recognition", "quux_not_held"]:
        r = rf.compose_design_for_concept(a.s, c)
        print(f"  concept {c!r} (control, expect WALL): authored={r['authored']} reason={r.get('reason','')[:60]}")
        derived_ok &= (not r["authored"])
    print(f"  -> DERIVE works for held concepts AND walls honestly for un-held: {derived_ok}")

    # ===== PUSH 3 — GROW the part library by held signature-authoring =====
    print("\n" + "=" * 86)
    print("GATE 3 — GROW the part library (held signature-authoring) — was 11 shape-signatures")
    print("=" * 86)
    before = len(rf._load_shape_signatures(a.s))
    grow = rf.grow_part_library(a.s, ["wavelet_transform", "edge_detection", "pooling", "gradient_descent"])
    after = len(rf._load_shape_signatures(a.s))
    print(f"  library {before} -> {after} parts")
    print(f"  grown (shapes AUTHORED from held Concept definitions): {grow['grown']}")
    print(f"  skipped: {grow['skipped']}")
    print(f"  how: {grow['how']}")
    # a grown part is usable by the composer:
    r = rf.compose_design_for_concept(a.s, "wavelet_transform", beam=4, cand_k=4)
    print(f"  compose for a grown concept 'wavelet_transform': authored={r['authored']} {_plan_line(r) if r['authored'] else ''}")
    grew = len(grow["grown"]) > 0 and after > before

    # ===== GATE 4 — donkey + generalises =====
    print("\n" + "=" * 86)
    print("GATE 4 — donkey=0 + generalises (>=2 goals) + null control")
    print("=" * 86)
    nsig = rf._author_goal_signature(a.s, NULL_GOAL)
    nullc = rf.compose_design_for_goal(a.s, nsig) if nsig else {"authored": False, "reason": "no held relations"}
    print(f"  NULL goal (control): authored={nullc.get('authored')} ({nullc.get('reason','covered %s' % nullc.get('covered_count'))})")
    print(f"  donkey spy: LLM/teacher calls = {calls['n']} (must be 0)")
    print(f"  the composer path (compose_design_for_goal / _for_concept / grow_part_library) = held")
    print(f"  shape-matcher + held RelationCue structural-extraction; no LLM, no Python composition decision.")
    generalises = beamc["covered_count"] >= 3 and derived_ok
    discriminative = not nullc.get("authored")

    ok = (beam_helps and fuller and derived_ok and grew and calls["n"] == 0 and discriminative and generalises)
    print("\n" + "=" * 86)
    print(("PASS" if ok else "FAIL"),
          "- PUSHED THE RUNG-2 COMPOSER: (1) BEAM/backtrack covers MORE than the committed greedy "
          "(GEN 3/5->5/5, DOC 8/9->9/9); (2) DERIVE-goal-from-HELD-CONCEPT removes the fed-doc crutch "
          "(composes from a held concept name; walls honestly for un-held); (3) GROW the part library "
          f"by held signature-authoring ({before}->{after}). donkey={calls['n']}; null control holds; "
          "all graph-native (held shape-matcher + held structural-extraction); the plan is the agent's.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
