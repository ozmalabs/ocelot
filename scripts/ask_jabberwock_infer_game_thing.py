"""ASK THE JABBERWOCK how it infers what a thing is in a game FROM ITS KNOWLEDGE, BY CONTEXT (not keywords).

It HAS game knowledge (gaming / arc3_game / agency / game_mechanics microtheories) AND a contextual
inference faculty (feature_identity classifies kind=mover/meter/static from OBSERVED BEHAVIOUR; agency:
controlled iff it responds to a PROPER SUBSET of my actions). This script poses the question through the
agent's OWN ask interface (QuestionDriver.drive -> reflect) and reports its answer, then surfaces the game
knowledge + the contextual discriminators it would answer FROM. Pure I/O: ask + read. donkey-counted.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/ask_jabberwock_infer_game_thing.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains import reflective_faculty as rf
from domains import question_driver as qd
from domains import comprehend_question as cq

QUESTIONS = [
    "How do you tell what a thing is in a game from what it does?",
    "How do you describe a new thing using what you already know about games?",
    "What is a thing that responds only to some of my actions?",
]
GAME_MTS = {"gaming", "arc3_game", "arc3_navigation", "agency", "control_kinds",
            "affordance_basis", "game_mechanics", "maze_world", "grid_navigation"}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s = a.s

    print("=" * 94)
    print("ASKED THE JABBERWOCK: how do you infer what a thing is in a game, from your knowledge, by context?")
    print("=" * 94)

    # (1) Pose each question through its OWN ask interface; report comprehension routing + answer/wall.
    try:
        driver = qd.QuestionDriver(substrate=s)
    except Exception as e:
        driver = None
        print(f"  [could not build QuestionDriver over the full agent: {type(e).__name__}: {e}]")
    print("\n[1] WHAT IT ANSWERS (its universal ask interface):")
    for q in QUESTIONS:
        try:
            spec = cq.comprehend(q)
            route = f"kind={spec.kind} meta_target={getattr(spec,'meta_target',None)}"
        except Exception as e:
            route = f"comprehend failed: {type(e).__name__}: {e}"
        ans = ""
        if driver is not None:
            try:
                emi = driver.drive(qd.QuestionPack(text=q, reflect=rf.reflect))
                if getattr(emi, "is_wall", False):
                    ans = f"WALL: {getattr(emi,'wall_reason',None)}"
                else:
                    ans = f"answer={getattr(emi,'answer',None)} meta={emi.meta_answer or {}}"
            except Exception as e:
                ans = f"drive failed: {type(e).__name__}: {e}"
        print(f"  Q: {q}")
        print(f"     comprehend -> {route}")
        print(f"     -> {ans}")

    # (2) The KNOWLEDGE it would answer FROM: its game microtheories + their concepts (its own terms).
    print("\n[2] THE GAME KNOWLEDGE IT HOLDS (the microtheories it would infer from):")
    for m in s.nodes("Microtheory"):
        nm = s.node(m)["attrs"].get("name")
        if nm in GAME_MTS:
            cs = [s.node(c)["attrs"].get("name") for c in a.inner.neighbours(m, "has_concept")]
            if cs:
                print(f"    · {nm}: {', '.join(cs[:8])}")

    # (3) The CONTEXTUAL DISCRIMINATORS it holds (behaviour -> what a thing IS), in its own definitions.
    print("\n[3] THE CONTEXTUAL DISCRIMINATORS IT HOLDS (how behaviour names a thing):")
    want = {"avatar", "wall", "opening", "door", "goal_cell", "ControlledElement",
            "the_thing_i_control", "a_thing_that_moves_itself", "a_thing_that_stays_put", "a_counter"}
    for c in s.nodes("Concept"):
        at = s.node(c)["attrs"]
        if at.get("name") in want and at.get("definition"):
            print(f"    · {at['name']}: {at['definition'][:120]}")

    print("\n" + "=" * 94)
    print(f"donkey (LLM calls): {donkey['n']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
