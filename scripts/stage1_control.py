"""Stage 1 of the jabberwock's curriculum — learn WHAT IT CONTROLS (the action_delta map).

The agent moves its avatar and learns, for the region that responds to it, the displacement each action
causes (action_delta), folded by the closed loop. Success (its own): the learned map matches the true
action displacements, and the action-conditioned one-step error < the passive (constant-velocity) error
whenever the action changes — "I can predict where I'll be after an action."

The agent acts with variety here to gather control evidence (its design's epistemic drive; a deterministic
varied sequence stands in for it at this stage). The LEARNING is the graph faculty; the host only emits
actions and reads back the numbers.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/stage1_control.py [steps]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from avatar_world import AvatarEnv, AV
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

CYCLE = ["Up", "Right", "Down", "Left"]   # always changing direction -> passive prediction is wrong every step
TRUE = {"Up": (-1.0, 0.0), "Down": (1.0, 0.0), "Left": (0.0, -1.0), "Right": (0.0, 1.0)}


def _avatar(agent):
    for n in agent.s.nodes("Region"):
        a = agent.s.node(n)["attrs"]
        if int(a.get("rvalue") or 0) == AV and a.get("is_ground") != 1.0:
            return n
    return None


def _aff(agent, name):
    # affordances are ingested as WorldInstance nodes (world_type="Action"), reached via has_action.
    for n in agent.s.nodes("WorldInstance"):
        a = agent.s.node(n)["attrs"]
        if a.get("world_type") == "Action" and a.get("interaction") == 1.0 and a.get("name") == name:
            return n
    return None


def main() -> int:
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    world = ArcWorld(AvatarEnv())
    sub, ctx = world.reset()
    agent.perceive_frame(sub)
    print("STAGE 1 — learn what I control (action_delta). success = learned map = true displacements; "
          "action-conditioned error < passive.\n")

    prev = (0.0, 0.0)
    act_errs, pas_errs = [], []
    for i in range(steps):
        a = CYCLE[i % len(CYCLE)]
        sub, ctx = world.apply((a,))          # the adapter stamps game.last_action = a
        agent.perceive_frame(sub)
        agent.master_tick()                   # fold: commit last tick's action_delta corrections
        agent.tick()                          # learn_action_delta (controlled region + the affordance just used)
        av = _avatar(agent)
        ca = agent.s.node(av)["attrs"] if av else {}
        drow, dcol = ca.get("drow") or 0.0, ca.get("dcol") or 0.0
        aff = _aff(agent, a)
        aa = agent.s.node(aff)["attrs"] if aff else {}
        dcy, dcx = aa.get("dcy") or 0.0, aa.get("dcx") or 0.0          # the prediction (learned up to last frame)
        action_err = abs(drow - dcy) + abs(dcol - dcx)                  # action-conditioned 1-step error
        passive_err = abs(drow - prev[0]) + abs(dcol - prev[1])        # passive (predict = last motion)
        prev = (drow, dcol)
        if i >= len(CYCLE):                    # after each action has been seen at least once
            act_errs.append(action_err); pas_errs.append(passive_err)

    print("  learned action_delta map (the agent's discovered controls):")
    ok = True
    for name in CYCLE:
        aff = _aff(agent, name)
        aa = agent.s.node(aff)["attrs"] if aff else {}
        dcy, dcx = round(aa.get("dcy") or 0.0, 2), round(aa.get("dcx") or 0.0, 2)
        tdy, tdx = TRUE[name]
        match = abs(dcy - tdy) < 0.25 and abs(dcx - tdx) < 0.25
        ok = ok and match
        print(f"    {name:6} learned=({dcy:+.2f},{dcx:+.2f})  true=({tdy:+.0f},{tdx:+.0f})  {'OK' if match else 'x'}")
    if act_errs:
        aa, pa = sum(act_errs) / len(act_errs), sum(pas_errs) / len(pas_errs)
        print(f"\n  one-step error after warmup: action-conditioned={aa:.3f}  passive={pa:.3f}")
        print(f"  => the agent {'LEARNED ITS CONTROLS' if ok else 'has NOT learned the map'}; "
              f"action-conditioned prediction {'BEATS' if aa < pa else 'does NOT beat'} passive "
              f"(it can predict where it will be after an action).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
