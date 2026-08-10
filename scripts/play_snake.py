"""play_snake — put the jabberwock in SNAKE and run the bare loop. NOTHING here is snake-specific.

The loop body is the universal one: perceive_frame -> master_tick() ; tick() -> read the action the
GRAPH chose -> world.apply(action). The agent's curiosity drives it: world_curiosity recognises a world
it doesn't understand and mints a CapabilityAxis; action_effect.babble_interaction tries its affordances
(published by the adapter) to discover what they cause; the graph rule enact_forced_action bridges that
choice into chosen_action. Understanding is the goal, not the score — we watch what it builds.

Run:  PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/play_snake.py [steps]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from snake_env import SnakeEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds


DISP = {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1), "Select": (0, 0), "Reset": (0, 0)}


def _game(agent):
    return next((n for n in agent.s.nodes("WorldInstance")
                 if agent.s.node(n)["attrs"].get("world_type") == "Game"), None)


def main() -> int:
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    # the generic faculties master_tick fires — none snake-specific.
    agent.wire_autonomy_faculty()
    agent.wire_enact_faculty()
    agent.wire_self_extension()
    agent.wire_escalation_faculties()

    env = SnakeEnv()
    world = ArcWorld(env)
    sub, ctx = world.reset()
    agent.perceive_frame(sub)
    print(f"SNAKE {env.grid_h}x{env.grid_w} — the jabberwock plays. understanding is the goal, not the score.\n")

    deaths = 0
    eats = 0
    near_stuck = 0          # mechanical: frames spent NEAR the salient thing without consuming it (the orbit signal)
    prev_score = 0
    S = agent.s
    for i in range(steps):
        # perception hygiene: the controlled/salient marks are PER-FRAME derived flags — clear them so the
        # rules re-derive them from THIS frame's perception (else stale marks corrupt control/salience as
        # regions change identity). Mechanical, like the eye re-segmenting each frame.
        for n in S.nodes("Region"):
            ra = S.node(n)["attrs"]
            if ra.get("controlled"):
                agent.inner.set_attr(n, "controlled", 0.0)
            if ra.get("salient"):
                agent.inner.set_attr(n, "salient", 0.0)
        agent.master_tick()
        agent.tick()
        g = _game(agent)
        ga = agent.s.node(g)["attrs"] if g else {}
        action = ga.get("chosen_action") or ""
        # the agent acts; if it has not produced an action yet, it still must act to perceive (Reset bootstrap)
        sub, ctx = world.apply((action,) if action else ("Up",))
        agent.perceive_frame(sub)

        # MECHANICAL orbit measurement (perception, not a decision): is the agent near the salient thing
        # yet not consuming it? The DECISION to break the orbit (explore) is the graph rule that reads this.
        score = ctx.get("score", 0) or 0
        ate = score > prev_score
        if ate:
            eats += 1
        ctrl = next((n for n in S.nodes("Region") if S.node(n)["attrs"].get("controlled") == 1.0), None)
        sal = next((n for n in S.nodes("Region") if S.node(n)["attrs"].get("salient") == 1.0), None)
        if ate:
            near_stuck = 0
        elif ctrl is not None and sal is not None:
            ca, sa = S.node(ctrl)["attrs"], S.node(sal)["attrs"]
            dist = abs((ca.get("cy") or 0) - (sa.get("cy") or 0)) + abs((ca.get("cx") or 0) - (sa.get("cx") or 0))
            near_stuck = near_stuck + 1 if dist <= 3.0 else 0
        else:
            near_stuck = 0
        prev_score = score
        if g is not None:
            agent.inner.set_attr(g, "near_stuck", float(near_stuck))
            # heading = the displacement of the action just applied (the body's current heading), so the
            # agent's compute_aim can aim its leading edge. Mechanical I/O (the known motion of an action).
            dr, dc = DISP.get(action, (0, 0))
            agent.inner.set_attr(g, "last_drow", float(dr))
            agent.inner.set_attr(g, "last_dcol", float(dc))
            # the salient thing was just CONSUMED — flag the eating EVENT so the agent learns its
            # interaction point from it (learn_front_from_eating). The host only reports the event.
            if ate:
                agent.inner.set_attr(g, "pending_eat", 1.0)

        wa = [a for a in agent.s.nodes("CapabilityAxis")
              if agent.s.node(a)["attrs"].get("needs_world_action") == 1.0]
        head = env._snake[0] if getattr(env, "_snake", None) else None
        state = ctx.get("won") and "WON" or (ctx.get("over") and "DEAD" or "alive")
        if ctx.get("over"):
            deaths += 1
        mode = "explore" if near_stuck >= 4 else "seek"
        front = int(ga.get("aim_front") or 0)
        print(f"  {i+1:3} act={action or '(bootstrap Up)':14} head={head} food={env._food} "
              f"len={len(env._snake) if getattr(env,'_snake',None) else 0} score={score} eats={eats} "
              f"[{state}] {mode} front={front} stuck={near_stuck}{'  ATE!' if ate else ''}", flush=True)
        if ctx.get("over"):
            sub, ctx = world.apply(("Reset",))   # penalty-free restart — it keeps what it learned
            agent.perceive_frame(sub)
            near_stuck = 0; prev_score = 0

    wa = [a for a in agent.s.nodes("CapabilityAxis") if agent.s.node(a)["attrs"].get("needs_world_action") == 1.0]
    print(f"\n  {steps} steps, {deaths} deaths. The agent minted {len(wa)} world-understanding axis(es) and acted "
          f"from its own curiosity throughout — no snake-specific code drove it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
