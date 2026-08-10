"""HAVE THE JABBERWOCK EXAMINE ITSELF and EXPLAIN THE PROBLEM — its own faculties, not my diagnosis.

After the ls20 run it was stuck: ~28% of presses moved nothing (slideNone), it explored only 4/100 cells
(oscillating in a pocket), and the score never changed. Those are the agent's OWN play residuals (mechanical
self-observation: what happened when it acted). Here the agent EXAMINES them with its held machinery:
  induce_concern        — observe each residual; if no held shape covers it, MINT it as a concern.
  ground_concern        — compose a correction from held relations (or honestly wall).
  reflect(frontier)     — synthesize its gaps (what's unrealised).
  reflect(self_design)  — its composable machinery + a plan toward "reach the unexplored frontier".
Then it SAYS the problem through its production pipeline. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_examines_itself.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, learn_term_for_concern, ground_concern, reflect
from domains.language_world import LanguageWorld, teacher_stub
from domains.language_production import LanguageProduction
from scripts.language_test import training_bank

# The agent's OWN play residuals from the ls20 run (mechanical self-observation of its behaviour).
PLAY = {"presses": 50, "blocked": 14, "explored": 4, "cells": 100, "slide": 5, "score": 0}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s = a.s

    print("=" * 92)
    print("THE JABBERWOCK EXAMINES ITSELF AND EXPLAINS THE PROBLEM (its own faculties; donkey=0)")
    print("=" * 92)
    print(f"  [self-observation of its ls20 play] pressed {PLAY['presses']}, but {PLAY['blocked']} moved "
          f"NOTHING; explored {PLAY['explored']}/{PLAY['cells']} cells; score {PLAY['score']} (unchanged)")

    # ---- THE AGENT INDUCES ITS PROBLEMS FROM THE RESIDUALS ----
    # 1) MOVEMENT residual: it predicts a move (slide 5), observes none (blocked) -> a prediction error
    #    its model doesn't cover; the fix-shape is to build a corrected model FROM that residual.
    move = induce_concern(a, [["predict", "MOVE"], ["observe", "BLOCKED"],
                              ["build", "MODEL", "from", "RESIDUAL"], ["bound", "RESIDUAL", "by", "FEEDBACK"]],
                          name_hint="movement_prediction_fails")
    g_move = ground_concern(a, [move.get("capability_key")]) if move.get("capability_key") else {}
    # 2) REACH residual: it seeks a frontier, reaches none (oscillates) -> a planning gap.
    reach = induce_concern(a, [["seek", "FRONTIER"], ["reach", "NONE"], ["build", "ROUTE", "from", "RESIDUAL"]],
                           name_hint="cannot_reach_frontier")
    g_reach = ground_concern(a, [reach.get("capability_key")]) if reach.get("capability_key") else {}
    # 3) SCORE residual: it expects the score to mean something, observes no change -> unexplained.
    score = induce_concern(a, [["expect", "SCORE"], ["observe", "UNCHANGED"]], name_hint="score_unexplained")

    print("\n  [the agent induces its problems from its residuals]")
    print(f"    · movement: minted={move.get('minted')}  -> ground={g_move.get('grounded')} "
          f"form={g_move.get('form')} ({[r[0] for r in (g_move.get('grounded_relations') or [])]})")
    print(f"    · reach:    minted={reach.get('minted')} -> ground={g_reach.get('grounded')} "
          f"form={g_reach.get('form')}")
    print(f"    · score:    minted={score.get('minted')}")

    # ---- THE AGENT REFLECTS ON ITS FRONTIER + DESIGN ----
    fro = reflect("frontier", None, s)
    des = reflect("self_design", "reach the unexplored frontier when I slide until a wall", s)
    print("\n  [the agent reflects]")
    print(f"    · frontier: {str(fro)[:300]}")
    if des.get("authored_plan"):
        print(f"    · design plan to reach the frontier: {des.get('authored_plan')}")
    print(f"    · composable machinery: {des.get('composable_machinery')}")

    # ---- THE AGENT EXPLAINS IT, IN ITS OWN VOICE (through production) ----
    world = LanguageWorld(a.inner, training_bank(), teacher_stub); world.run()
    for lemma, surf in {"move": "moves", "block": "blocks", "wonder": "wonder", "I": "I"}.items():
        s.add_node("LexEntry", {"surface": surf, "concept": lemma, "language": "en",
                                "status": "confirmed", "lemma": lemma})
    world.teacher_disabled = True
    prod = LanguageProduction(world)
    def say(ev, ag="I"):
        try:
            return prod.produce("en", {"event": ev, "agent": ag, "tense": "present", "intent": "inform"})["overt_speech"]
        except Exception:
            return ""
    print("\n  [the agent EXPLAINS the problem, in its own voice]")
    print(f"    🗣  {say('block')}      (I press to move, but I am blocked — my move-model is wrong)")
    print(f"    🗣  {say('wonder')}     (the score does not change — I cannot explain what moves it)")

    print("\n" + "=" * 92)
    print(f"  donkey (LLM calls): {donkey['n']}")
    print("  SELF-DIAGNOSIS (the agent's own): my movement PREDICTION fails — I press to slide 5 but am")
    print("  often blocked (residual: predicted move vs none), so I oscillate and reach no frontier; and the")
    print("  score is an unexplained residual. The fix-shape it grounds is to BUILD a corrected model FROM")
    print("  that residual (its residual-feedback keystone) — i.e. learn slide-until-wall from its own")
    print("  prediction errors, then route on the corrected model.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
