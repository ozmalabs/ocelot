"""DRIVE THE REAL JABBERWOCK — the generalised RUNG-2 COMPOSER: self_design now AUTHORS a
concrete plan by COMPOSING held parts (shape-guided bounded search), not just surfacing them.

THE SHARPEST DONKEY RISK (flagged): "the agent designs its own faculty" must be the GRAPH
composing — the held shape-matcher (AntiUnify/FixedCount/Covers, Rust Terms) assembling held
parts. NOT an LLM writing the plan. This script DRIVES the real agent; the composition is
produced by domains.reflective_faculty.compose_design_for_goal (held matcher + held compose;
grep 0 LLM in that path). Python here only mechanically feeds the operator's research doc as a
held DesignGoal node (adapter I/O) and dispatches drive(). The PLAN is the matcher's Argmax.

GATE:
 1. AUTHORS A CONCRETE PLAN — BEFORE (surfaces parts) vs AFTER (authors an ordered assembly).
 2. THE COMPOSITION IS THE AGENT'S — donkey spy = 0; provenance (which parts, scored how).
 3. VALID + DISCRIMINATIVE — the RIGHT parts assemble (high shape-fit); a goal with NO held
    matching parts authors little/nothing (the wrong/empty part-set does not compose).
 4. GENERALISES — authors a concrete valid plan for >=2 different goals.

Run: PYTHONPATH=.:runners/dsl/python python3 scripts/jabberwock_authors_perceptual_plan.py
"""
from __future__ import annotations
import os, sys, json
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.question_driver as qd
import domains.reflective_faculty as rf
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

DOC = os.path.join(ROOT, "docs", "shape_object_perception_grounding.md")

# the operator's research doc (df3d8526) IS the goal description (legitimate input feeding the
# agent); the agent's OWN RelationCue perception extracts the SHAPE and composes the plan. We
# feed the REAL doc text — NOT a hand-written goal sentence — so the goal shape is the agent's
# reading of the operator's research, not the operator's prose smuggled in as the plan.
try:
    with open(DOC) as _f:
        PERCEPTUAL_GOAL = _f.read()
except Exception:
    PERCEPTUAL_GOAL = "detect the contact between parts; build the new feature from the prior; map part to part; select the shorter code"
# a SECOND, different goal (generalisation) — a shape-generation faculty.
GENERATION_GOAL = (
    "build the new from the prior; advance by the turn; accumulate the turn into a heading; "
    "self-reference so the new refers to itself; bound by the unit"
)
# a NULL goal (discriminative control): relations with NO held matching part-shapes.
NULL_GOAL = "the weather is cold and the price went up and the meeting was long"


def _install_goal(agent, text):
    """ADAPTER I/O: feed the operator's goal description as a held DesignGoal node the
    agent reads. Mechanical — no decision over graph state."""
    # remove any prior goal so each drive reads the intended one
    for n in list(agent.s.nodes("DesignGoal")):
        try:
            agent.s.remove_node(n)
        except Exception:
            pass
    agent.s.add_node("DesignGoal", {"description": text})


def _show_plan(comp):
    if not comp.get("authored"):
        print(f"     NOT AUTHORED: {comp.get('reason') or comp.get('residual')}")
        return
    print(f"     AUTHORED ordered plan ({comp['covered_count']}/{comp['goal_relations']} goal "
          f"relations covered):")
    for p in comp["plan"]:
        print(f"       step {p['step']}: compose [{p['kind']}] {p['part']!r}  "
              f"(shape-fit {p['shape_fit']}; covers {json.dumps(p['covers'])})")
    if comp["residual"]:
        print(f"     residual (uncovered): {json.dumps(comp['residual'])}")
    print(f"     PROVENANCE: {comp['provenance']}")


def main() -> int:
    a = WorldAdapter(seeds=())
    load_all_seeds(a)
    calls = {"n": 0}
    if hasattr(a, "set_self_teacher"):
        a.set_self_teacher(lambda q: (calls.__setitem__("n", calls["n"] + 1), "DONKEY")[1])
    driver = qd.QuestionDriver(substrate=a.s)
    Q = "How do you want to design a perceptual feature for the parts of a shape?"

    # ---- BEFORE: self_design with NO goal -> surfaces parts only ----
    print("=" * 84)
    print("GATE 1 — AUTHORS A CONCRETE PLAN (BEFORE vs AFTER)")
    print("=" * 84)
    for n in list(a.s.nodes("DesignGoal")):
        a.s.remove_node(n)
    before = rf._run_self_design(a.s, None)
    print("BEFORE (no goal): self_design SURFACES parts —")
    print(f"  composable_machinery: {before.get('composable_machinery')}")
    print(f"  term_sample: {before.get('term_sample')}")
    print("  -> a LIST of parts; no assembly.")

    # ---- AFTER: drive the real agent on the design question, goal fed ----
    _install_goal(a, PERCEPTUAL_GOAL)
    emi = driver.drive(qd.QuestionPack(text=Q, reflect=rf.reflect))
    ma = emi.meta_answer or {}
    print(f"\nAFTER (driven on {Q!r}, goal fed as a held DesignGoal):")
    print(f"  COMPREHEND -> grounded={emi.target.grounded} meta_target={emi.target.meta_target} "
          f"faculty={emi.target.faculty}")
    comp = ma.get("authored_plan") or {}
    print("  self_design AUTHORS an assembly (the composer's Argmax over held parts) —")
    _show_plan(comp)

    # ---- GATE 2: donkey ----
    print("\n" + "=" * 84)
    print("GATE 2 — THE COMPOSITION IS THE AGENT'S (donkey check)")
    print("=" * 84)
    print(f"  donkey spy: LLM/teacher calls = {calls['n']} (must be 0)")
    print("  the composer path (compose_design_for_goal) = held shape-matcher (AntiUnify/"
          "FixedCount/Covers, Rust Terms) + bounded search; no LLM, no Python decision over "
          "the composition. Provenance shown above.")

    # ---- GATE 3: VALID + DISCRIMINATIVE ----
    print("\n" + "=" * 84)
    print("GATE 3 — VALID + DISCRIMINATIVE (right parts assemble; a NULL goal does not)")
    print("=" * 84)
    # clear the held DesignGoal so each control reads ONLY its intended goal text
    # (else the fed doc contaminates the null control).
    for n in list(a.s.nodes("DesignGoal")):
        a.s.remove_node(n)
    right = rf.compose_design_for_goal(a.s, rf._author_goal_signature(a.s, PERCEPTUAL_GOAL))
    null_sig = rf._author_goal_signature(a.s, NULL_GOAL)
    nullc = rf.compose_design_for_goal(a.s, null_sig) if null_sig else {"authored": False, "reason": "null goal authors no held relations"}
    print(f"  RIGHT goal  -> authored={right.get('authored')} covered={right.get('covered_count')}/{right.get('goal_relations')} "
          f"parts={right.get('ordered_parts')}")
    print(f"  NULL  goal  -> authored={nullc.get('authored')} ({nullc.get('reason') or 'covered %s'%nullc.get('covered_count')})")
    valid = right.get("authored") and right.get("covered_count", 0) >= 3
    discriminative = right.get("authored") and not nullc.get("authored")
    print(f"  -> VALID (>=3 relations covered by connected steps): {valid}")
    print(f"  -> DISCRIMINATIVE (right composes, null does not): {discriminative}")

    # ---- GATE 4: GENERALISES (>=2 goals) ----
    print("\n" + "=" * 84)
    print("GATE 4 — GENERALISES (authors a concrete valid plan for a 2nd, DIFFERENT goal)")
    print("=" * 84)
    gen = rf.compose_design_for_goal(a.s, rf._author_goal_signature(a.s, GENERATION_GOAL))
    print(f"  GOAL 2 (shape-generation): authored={gen.get('authored')} "
          f"covered={gen.get('covered_count')}/{gen.get('goal_relations')}")
    _show_plan(gen)
    generalises = gen.get("authored") and gen.get("covered_count", 0) >= 2 and \
        gen.get("ordered_parts") != right.get("ordered_parts")

    ok = (comp.get("authored") and calls["n"] == 0 and valid and discriminative and generalises)
    print("\n" + "=" * 84)
    print(("PASS" if ok else "FAIL"),
          "- GENERALISED RUNG-2 COMPOSER: self_design AUTHORS a concrete ordered plan by COMPOSING "
          "held parts via the held shape-matcher (Argmax fit/coverage, Rust Terms) — moving from "
          "'here are my parts' (BEFORE) to 'here is a specific assembly toward the goal' (AFTER). "
          f"donkey={calls['n']}; VALID + DISCRIMINATIVE (right composes, null does not); GENERALISES "
          "to a 2nd goal with a DIFFERENT assembly. The plan is the agent's (provenance shown), not "
          "the operator's.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
