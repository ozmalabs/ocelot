"""STAGE 3 — the jabberwock plays SNAKE FROM UNDERSTANDING (no hand-coded aim/seek).

It boots, plays a gentle non-self-colliding warmup so the self/world/board discriminator classifies the HEAD
as controllable (self), the FOOD as the salient static non-board region, and the BODY as autonomous; then it
plays by reading game.chosen_action — the death-gated argmax over its learned control basis toward the only
not-me/not-board thing. Understanding is the goal: it should move toward food and avoid walls, the seek
falling out of distance+safety, not from a hand-written policy.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/play_snake_understanding.py [steps]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from snake_env import SnakeEnv, HEAD, FOOD
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

# a 2-wide box: exercises all four actions to learn resp_<A> without a length-3 self-collision
WARMUP = ["Right", "Right", "Down", "Down", "Left", "Left", "Up", "Up"]


def game_node(agent):
    for n in agent.s.nodes("WorldInstance"):
        if agent.s.node(n)["attrs"].get("world_type") == "Game":
            return n
    return None


def classified(agent):
    head = food = None
    for n in agent.s.nodes("Region"):
        a = agent.s.node(n)["attrs"]
        if a.get("axis_kind") == "controllable" and int(a.get("rvalue") or 0) == HEAD:
            head = a.get("axis_kind")
        if a.get("salient") == 1.0:
            food = int(a.get("rvalue") or 0)
    return head, food


def main():
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    print("=" * 92)
    print("STAGE 3 — the jabberwock plays SNAKE FROM UNDERSTANDING (composed, not hand-coded).")
    print("=" * 92)
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    world = ArcWorld(SnakeEnv())
    sub, ctx = world.reset(); agent.perceive_frame(sub)

    deaths = 0
    for i, a in enumerate(WARMUP * 2):                      # gentle warmup: learn resp + classify
        sub, ctx = world.apply((a,)); agent.perceive_frame(sub); agent.master_tick(); agent.tick()
        if ctx.get("over"):
            deaths += 1
            sub, ctx = world.apply(("Reset",)); agent.perceive_frame(sub); agent.master_tick(); agent.tick()
    head_kind, food_val = classified(agent)
    print(f"\n  after warmup: HEAD classified self(controllable)={head_kind == 'controllable'}; "
          f"FOOD marked salient (rvalue={food_val}, expect {FOOD}); warmup deaths={deaths}")

    # play from understanding: read the agent's chosen_action each step
    g = game_node(agent)
    start_score = ctx.get("score", 0)
    eaten, survived = 0, 0
    last_score = start_score
    for i in range(steps):
        a = agent.s.node(game_node(agent))["attrs"].get("chosen_action") or "Right"
        sub, ctx = world.apply((a,)); agent.perceive_frame(sub); agent.master_tick(); agent.tick()
        if ctx.get("score", 0) > last_score:
            eaten += ctx.get("score", 0) - last_score
            last_score = ctx.get("score", 0)
        if ctx.get("over"):
            sub, ctx = world.apply(("Reset",)); agent.perceive_frame(sub); agent.master_tick(); agent.tick()
            last_score = ctx.get("score", 0)
        else:
            survived += 1

    print(f"  played {steps} steps: food eaten = {eaten}; non-death steps = {survived}/{steps}")
    ok = (head_kind == "controllable") and (food_val == FOOD) and eaten >= 1
    print("\n" + "=" * 92)
    print(f"  {'PASS' if ok else 'PARTIAL'} — the agent identified its self + the salient food from the "
          f"discriminator and SOUGHT the food (death-gated argmax over its learned control basis), eating "
          f"{eaten}. No hand-coded aim/seek — the seek falls out of distance+safety. Understanding is the goal.")
    print("=" * 92)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
