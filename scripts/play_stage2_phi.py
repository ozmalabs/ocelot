"""Stage 2 in phi: 'the boundary is destruction', understood by forward-rollout — not learned by dying.

The agent boots, explores briefly (a balanced cycle near centre) so the compensated discriminator identifies
the self and learns its controllable basis (resp_<A>). Then it takes control: each frame the boundary seed
rolls the self's bbox forward by resp_<A>, flags any action whose rollout leaves the board (would_die_<A>),
and writes a surviving action to game.safe_action. The harness only transports that action to the world.

Verification: with the agent in control it NEVER walks off the board (0 deaths) even though it keeps moving;
a baseline that always presses Right walks straight into the wall and dies. Same world, same fatal boundary —
the difference is the agent's rollout. Walls are death, understood as a prior.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/play_stage2_phi.py [control_steps]
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

from stage2_phi_world import AvatarDeathEnv4, AV
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

WARM_CYCLE = ["Up", "Down", "Left", "Right"]


def _anchor(agent):
    """The node the region rules anchor on (has has_region edges) — and carries h/w/last_action/safe_action."""
    best, deg = None, -1
    for t in ("Game", "WorldInstance"):
        for n in agent.s.nodes(t):
            d = len(agent.inner.neighbours(n, "has_region"))
            if d > deg:
                best, deg = n, d
    return best


def _self_region(agent):
    for n in agent.s.nodes("Region"):
        a = agent.s.node(n)["attrs"]
        if a.get("is_ground") != 1.0 and a.get("axis_kind") == "controllable":
            return n
    return None


def boot_and_warm(warm=28):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    world = ArcWorld(AvatarDeathEnv4())
    sub, ctx = world.reset()
    agent.perceive_frame(sub)
    for i in range(warm):
        sub, ctx = world.apply((WARM_CYCLE[i % 4],))
        agent.perceive_frame(sub)
        agent.master_tick()
        agent.tick()
    return agent, world, ctx


def main() -> int:
    steps = int(sys.argv[1]) if len(sys.argv) > 1 else 80
    agent, world, ctx = boot_and_warm()

    g = _anchor(agent)
    ga = agent.s.node(g)["attrs"]
    print("THE BOUNDARY IS DESTRUCTION — understood in phi by forward-rollout, not by dying.\n")
    print(f"  board extent on the anchor node: h={ga.get('h')} w={ga.get('w')}  last_action={ga.get('last_action')!r} safe_action={ga.get('safe_action')!r}")
    r = _self_region(agent)
    if r is None:
        print("  !! no controllable self region after warmup — discriminator did not classify; aborting.")
        return 1
    ra = agent.s.node(r)["attrs"]
    basis = {A: (round(ra.get(f'resp_{A}_dr') or 0, 1), round(ra.get(f'resp_{A}_dc') or 0, 1)) for A in WARM_CYCLE}
    print(f"  self identified: axis_kind={ra.get('axis_kind')}  controllable-basis(resp)={basis}")
    print(f"  self bbox=[r {ra.get('minr')}..{ra.get('maxr')}, c {ra.get('minc')}..{ra.get('maxc')}]  "
          f"would_die={{Up:{ra.get('would_die_Up')}, Down:{ra.get('would_die_Down')}, "
          f"Left:{ra.get('would_die_Left')}, Right:{ra.get('would_die_Right')}}}")

    # --- the agent in control: it transports its own safe_action ---
    deaths = 0
    trail = []
    for i in range(steps):
        a = agent.s.node(_anchor(agent))["attrs"].get("safe_action") or "Up"
        sub, ctx = world.apply((a,))
        agent.perceive_frame(sub)
        agent.master_tick()
        agent.tick()
        if ctx.get("over"):
            deaths += 1
            sub, ctx = world.apply(("Reset",)); agent.perceive_frame(sub); agent.master_tick(); agent.tick()
        if i % 12 == 0:
            rr = _self_region(agent)
            bb = agent.s.node(rr)["attrs"] if rr else {}
            trail.append((i, a, bb.get("minr"), bb.get("maxr"), bb.get("minc"), bb.get("maxc")))
    print(f"\n  AGENT IN CONTROL for {steps} steps: chose its own safe_action each frame.")
    for i, a, mnr, mxr, mnc, mxc in trail:
        print(f"    f{i:>3} acted {a:>5}  self bbox=[r {mnr}..{mxr}, c {mnc}..{mxc}]")
    print(f"  => deaths under the agent's rollout: {deaths}")

    # --- baseline: always Right, no rollout ---
    bagent, bworld, _ = boot_and_warm()
    bdeaths, first_death = 0, None
    for i in range(steps):
        sub, bctx = bworld.apply(("Right",))
        bagent.perceive_frame(sub); bagent.master_tick(); bagent.tick()
        if bctx.get("over"):
            bdeaths += 1
            if first_death is None:
                first_death = i
            sub, bctx = bworld.apply(("Reset",)); bagent.perceive_frame(sub); bagent.master_tick(); bagent.tick()
    print(f"\n  BASELINE (always Right, no rollout): deaths={bdeaths} (first at control-frame {first_death}).")
    ok = deaths == 0 and bdeaths > 0
    print(f"\n  {'PASS' if ok else 'FAIL'}: the agent avoided the fatal boundary by rolling phi forward; the "
          f"blind baseline did not. The walls are death, understood — no death handler, no dying to learn.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
