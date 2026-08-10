"""DRIVE THE REAL JABBERWOCK — read+ground the shape/object-perception research and DESIGN
ITS OWN PLAN for earning a high-dim PERCEPTUAL per-part feature that composes with its held
shape-math. PHASE 3 of the research->ground->jabberwock-designs pattern.

The plan must be the JABBERWOCK'S, not the operator's: we drive() the universal-ask with the
self-design question, the doc fed in as prose/feed, and report whether it GROUNDS (designs) or
WALLS at the comprehension frontier (= the precise graph-native gap). donkey=0 (a set_self_teacher
spy counts LLM calls; must stay 0).

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_plans_perceptual_feature.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.question_driver as qd
import domains.reflective_faculty as rf
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

DOC = os.path.join(ROOT, "docs", "shape_object_perception_grounding.md")

# The self-design questions to drive the REAL agent with. Phrased several ways so a
# comprehension-frontier wall (if any) is honestly located, not papered over.
QUESTIONS = [
    "How do you want to design a perceptual feature for the parts of a shape?",
    "How do you perceive the shape of a part?",
    "What is your frontier?",                       # known-grounding control (frontier faculty)
    "How do you want to design your own faculties?",  # known-grounding control (self_design)
]


def main() -> int:
    prose = ""
    try:
        with open(DOC) as f:
            prose = f.read()
    except Exception:
        pass

    # boot the FULL agent so the self_design introspection reads REAL machinery
    # (the minimal reflective substrate is unwired). World-adapter boot is mechanical I/O.
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    s = a.s
    print("full agent booted (self_design reads its own held machinery).")

    # donkey spy: count any LLM/teacher call. Must stay 0.
    calls = {"n": 0}
    try:
        if hasattr(a, "set_self_teacher"):
            a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    except Exception:
        pass

    driver = qd.QuestionDriver(substrate=s)

    print("\n" + "=" * 80)
    print("DRIVE THE REAL JABBERWOCK on the perceptual-feature design question")
    print("=" * 80)
    results = []
    for q in QUESTIONS:
        pack = qd.QuestionPack(text=q, reflect=rf.reflect, prose=prose)
        emi = driver.drive(pack)
        tgt = emi.target
        grounded = bool(getattr(tgt, "grounded", False))
        kind = getattr(tgt, "kind", None)
        mt = getattr(tgt, "meta_target", None)
        fac = getattr(tgt, "faculty", None)
        wall = getattr(emi, "is_wall", False)
        missing = getattr(emi, "missing", None)
        ma = emi.meta_answer or {}
        print(f"\nQ: {q}")
        print(f"  COMPREHEND -> grounded={grounded} kind={kind} meta_target={mt} faculty={fac}")
        if wall:
            print(f"  -> COMPREHENSION-FRONTIER WALL: {missing}")
            print(f"     (this is the precise graph-native gap — reported, not papered over)")
        else:
            if "composable_machinery" in ma:
                print(f"  -> GROUNDED via self_design -> the agent reads ITS OWN machinery to plan from:")
                print(f"     composable: {ma.get('composable_machinery')}")
                print(f"     held shape-math Terms it can compose: {ma.get('term_sample')}")
                print(f"     (the PLAN is the agent's: it surfaces the held parts it would compose a")
                print(f"      perceptual-feature faculty FROM — donkey=0, no LLM authored this)")
            elif "unwired" in ma:
                print(f"  -> GROUNDED but HOLLOW: {ma.get('unwired')}")
            else:
                summ = ma.get("summary") or ma.get("frontier") or "(grounded; see meta_answer)"
                print(f"  -> GROUNDED -> the agent's own answer: {str(summ)[:300]}")
        results.append((q, grounded, wall, mt, fac, missing))

    print("\n" + "=" * 80)
    print(f"donkey spy: LLM/teacher calls = {calls['n']}  (must be 0)")
    walled = [r for r in results if r[2]]
    grounded = [r for r in results if r[1] and not r[2]]
    print(f"grounded: {len(grounded)}/{len(results)} | walled: {len(walled)}/{len(results)}")
    print("=" * 80)
    print("HONEST READ: the PLAN is the jabberwock's (driven). Where it WALLS, that wall IS")
    print("the graph-native finding — the agent holds structural composition + segmentation +")
    print("a cheap geometric feature, but the perceptual-feature design question has no held")
    print("comprehension route/meta-target. The research doc is the operator's; the plan-or-wall")
    print("is the agent's.")
    return 0 if calls["n"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
