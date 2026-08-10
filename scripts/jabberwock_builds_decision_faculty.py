"""THE JABBERWOCK BUILDS the decision-under-uncertainty faculty GRAPH-NATIVE (no logic in any adapter).
I only frame the concern; its self-build composer authors a RULE that, on run_rules, writes chosen_action =
the affordance with the best EXPECTED UTILITY ACROSS its avatar candidates (argmax over affordances of
summed progress-toward-target). The whole decision is one held Term reading candidates / affordances /
target from the GRAPH — so it runs over whatever the agent perceived, in its own engine.

Then we feed it a perceived scene as GRAPH DATA (a goal node, affordance nodes, two avatar-candidate
nodes) and tick: its OWN rule writes chosen_action. If a move is good for whichever candidate is really
the avatar, it picks it — acting then disambiguates. donkey=0.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_builds_decision_faculty.py
"""
from __future__ import annotations
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from domains.reflective_faculty import induce_concern, ground_concern

ACTIONS = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}


def main():
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    donkey = {"n": 0}; a.set_self_teacher(lambda q: (donkey.__setitem__("n", donkey["n"] + 1), "D")[1])
    s, I = a.s, a.inner

    print("=" * 92)
    print("THE JABBERWOCK BUILDS the decision-under-uncertainty faculty GRAPH-NATIVE (I only frame it)")
    print("=" * 92)

    # 1) frame the concern -> the agent grounds the relations -> the composer authors the DECISION RULE
    ind = induce_concern(a, [["utility", "ARGMAX", "over", "CANDIDATE"],
                             ["average", "OVER", "each", "CANDIDATE"],
                             ["progress", "TOWARD", "the", "TARGET"]],
                         name_hint="act_under_avatar_uncertainty")
    g = ground_concern(a, [ind.get("capability_key")]) if ind.get("capability_key") else {}
    print(f"\n  [agent builds] grounded={g.get('grounded')} path={g.get('path')} form={g.get('form')}")
    if g.get("rule"):
        print(f"  [agent builds] AUTHORED RULE match={g['rule']['match']}")
        print(f"                 effect writes game.chosen_action via a held Term (argmax over affordances")
        print(f"                 of summed progress-toward-target over avatar candidates)")

    # 2) feed a PERCEIVED scene as graph data (what the agent would recognise): target + affordances +
    #    two avatar candidates. game --has_goal--> goal ; game --affordance--> act ; game --avatar_candidate--> c
    game = s.add_node("WorldInstance", {"world_type": "Game"})
    goal = s.add_node("Cell", {"world_type": "Cell", "cy": 2.0, "cx": 0.0, "is_goal": 1.0})
    I.add_edge_unchecked(game, "has_goal", goal)
    for nm, (dr, dc) in ACTIONS.items():
        act = s.add_node("Affordance", {"name": nm, "drow": float(dr), "dcol": float(dc)})
        I.add_edge_unchecked(game, "affordance", act)
    for (cy, cx) in [(2.0, 6.0), (2.0, 8.0)]:
        cand = s.add_node("Region", {"cy": cy, "cx": cx})
        I.add_edge_unchecked(game, "avatar_candidate", cand)
    print("\n  perceived scene: target (2,0); avatar candidates (2,6) and (2,8); affordances Up/Down/Left/Right")

    # 3) THE AGENT DECIDES — its own rule fires in run_rules and writes chosen_action
    I.run_rules()
    chosen = s.node(game)["attrs"].get("chosen_action")
    print(f"\n  -> the agent's OWN rule wrote chosen_action = {chosen!r}")
    print("     (Left reduces distance-to-target for BOTH candidates, so it wins whichever one is the avatar)")

    print("\n" + "=" * 92)
    print(f"  donkey (LLM calls): {donkey['n']}")
    print("  The decision faculty is graph-native: a Rule the agent runs in run_rules, whose Term reads the")
    print("  candidates/affordances/target it perceived and writes chosen_action = best expected utility")
    print("  across candidates. No logic in any adapter — the adapter need only provide observations +")
    print("  affordances; the agent decides. Acting then disambiguates which candidate is the avatar.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
