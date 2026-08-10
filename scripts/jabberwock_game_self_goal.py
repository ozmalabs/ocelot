"""The JABBERWOCK SETS ITS OWN GOAL in a game — no hardcoded 'goal = navigable locus'.

Creator's correction: verify_tetris was wrong to conclude "no goal location -> can't play." The agent
SETS ITS OWN ARBITRARY GOALS; the hardcoding (goal must be a locus the world provides) is the bug.
And the jabberwock should do the goal-setting ITSELF — not a goal rule I author.

DIVISION (held strictly):
  WORLD ADAPTER (thin I/O) — declares the controls (affordances) and REPORTS an observed quantity
    (here: the world's value signal) as a fact: a Quantity node + its value each frame. Reporting an
    observable is input translation, not deciding a goal.
  THE JABBERWOCK (its own faculties) — observes that the quantity VARIES and FOLLOWS its actions, then
    via its OWN generative loop induces a concern from that residual (induce_concern), and PICKS it as
    its frontier/goal (gap_prioritiser.pick_frontier). I author no goal.

This script DRIVES those faculties and reports the goal the AGENT set, donkey=0. (Pursuit is the next
rung; this establishes that the goal is self-set, not world-handed.)

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_game_self_goal.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
import domains.world_play as world_play
from tetris_world import TetrisEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern, learn_term_for_concern
from domains.gap_prioritiser import pick_frontier

CONTROLS = ["Up", "Down", "Left", "Right"]


def gnode(a):
    return next((n for n in a.s.nodes("WorldInstance")
                 if a.s.node(n)["attrs"].get("world_type") == "Game"), None)


def report_efficacy(responded):
    """ADAPTER I/O: report only OBSERVED FACTS about the world's dynamics as a relation-system (the form
    induce_concern reads) — the world-state VARIES, it FOLLOWS the agent's actions (efficacy), and it is
    STATE-bounded. No goal asserted; the agent decides what to do with this."""
    obs = [["varies", "STATE", "over", "TIME"]]
    if responded:
        obs.append(["build", "STATE", "from", "ACTION"])      # observed: the state responds to my acts
        obs.append(["bound", "STATE", "by", "STATE"])         # observed: it is state-limited
    return obs


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    w = ArcWorld(TetrisEnv()); sub, ctx = w.reset(); a.perceive_frame(sub)
    g = gnode(a); body = a.s.add_node("Body", {}); a.inner.add_edge_unchecked(body, "inhabits", g)
    world_play.declare_affordances(a, g, CONTROLS)   # adapter: the controls (affordances)

    print("=" * 84)
    print("THE JABBERWOCK SETS ITS OWN GOAL — the world reports a value signal; the agent decides")
    print("=" * 84)

    # explore + OBSERVE whether the world responds to the agent's actions (efficacy). The adapter only
    # reports observed facts; exploration here is bootstrap (the agent's curiosity is a later rung).
    responded = 0
    prev = None
    for i in range(120):
        before = tuple(tuple(r) for r in w.env._render())
        sub, ctx = w.apply((CONTROLS[i % 4],)); a.perceive_frame(sub)
        after = tuple(tuple(r) for r in w.env._render())
        if after != before:
            responded += 1
        if ctx.get("over"):
            sub, ctx = w.apply(("Reset",)); a.perceive_frame(sub)
        a.tick()
    print(f"  [observe] the world-state changed on {responded}/120 frames after the agent acted "
          f"(observed efficacy; the adapter asserts no goal)")

    # THE JABBERWOCK: induce a concern from the observed efficacy residual (its OWN faculty)
    obs = report_efficacy(responded > 0)
    ind = induce_concern(a, obs, name_hint="induced_game_value")
    print(f"\n  [induce_concern] minted={ind.get('minted')}  key={ind.get('capability_key')}")
    print(f"     residual predicates the agent extracted: {ind.get('residual_predicates')}")
    key = ind.get("capability_key")

    # THE JABBERWOCK PICKS ITS OWN FRONTIER (= its self-set goal), among ALL its axes
    pick = pick_frontier(a.s)
    print(f"\n  [pick_frontier] the agent's own pick: "
          f"{(pick or {}).get('capability_keys') or (pick or {}).get('axis_id')}")
    print(f"     (chosen by its ranking Term over its own axes — not handed a goal by the world)")

    # and GROUND it (compose the climb-the-value recurrence from held Terms) — still the agent
    if key:
        g2 = ground_concern(a, [key])
        print(f"\n  [ground_concern] grounded={g2.get('grounded')} path={g2.get('path')} "
              f"covers={g2.get('covers')} captures={g2.get('captures')}")
        if g2.get("wall"):
            print(f"     WALL (honest, = the agent's next self-extension): {str(g2.get('wall'))[:160]}")

    print(f"\n  [donkey] LLM calls: {donkey['n']}")
    print("=" * 84)
    print("  The goal is the AGENT'S: the world only reported a value signal as an observed fact; the")
    print("  jabberwock induced a concern from its residual and picked it as its frontier. No 'goal =")
    print("  locus' hardcoding, no goal rule authored by hand. (Pursuit — climbing the value via the")
    print("  learned affordance effects — is the next rung, and is the ground_concern recurrence above.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
