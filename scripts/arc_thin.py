"""arc_thin — the THIN world adapter for ARC-AGI-3, the way the architecture says it should be:

  the WORLD provides OBSERVATIONS (the frame) and AFFORDANCES (the available actions). NO LOGIC.

Each turn the adapter does exactly four mechanical things:
  1 perceive_frame(sub)              — ingest the frame as graph observations (the agent's native eye)
  2 declare the affordances + stamp the world's numbers (score/step) — observations, no decisions
  3 tick() / run_rules()             — THE AGENT acts: perceive -> map -> route -> decide, graph-native
  4 read the agent's chosen_action   — and submit it (with its spoken reasoning, an emit)

That's the whole loop. There is NO wall heuristic, NO slide_flood orchestration, NO block dict, NO nav
modes, NO footprint, NO frontier_flux in here — all of that was the AGENT'S job (map-building + routing),
and it lives in the graph (the navigation seeds), not the adapter. The only host fallback is a bootstrap
nudge when the agent emits no action (you must act to perceive). Run it to SEE what the graph drives on
its own — and where it doesn't, that gap is the real one for the agent to close.

  ulimit -v 12000000
  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_thin.py [--game ls20-9607627b] [--actions 30]
"""
from __future__ import annotations
import argparse, sys, time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _arc3_load_key import load_arc_api_key          # noqa: E402
from arc3_live_env import Arc3LiveEnv                # noqa: E402
from worlds.arc import ArcWorld                      # noqa: E402
from substrate.world_adapter import WorldAdapter     # noqa: E402
from substrate.boot_all import load_all_seeds        # noqa: E402
import domains.world_play as world_play              # noqa: E402
import arc_run as R                                  # reuse the EMIT helpers (voice) only            # noqa: E402

CONTROLS = ["Up", "Down", "Left", "Right"]


def _game(agent):
    for n in agent.s.nodes("WorldInstance"):
        if agent.s.node(n)["attrs"].get("world_type") == "Game":
            return n
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="THIN ARC-AGI-3 adapter (observations + affordances; no logic)")
    ap.add_argument("--game", default="ls20-9607627b")
    ap.add_argument("--actions", type=int, default=30)
    args = ap.parse_args()
    if not load_arc_api_key():
        print("could not load ARC_API_KEY — aborting"); return 1

    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    prod, say_map = R._setup_speech(agent)
    print("native eye:", hasattr(agent.inner, "segment"), "| voice:", prod is not None, flush=True)

    env = Arc3LiveEnv(args.game)
    world = ArcWorld(env)
    sub, ctx = world.reset()
    agent.perceive_frame(sub)                                    # 1 observe
    g = _game(agent)
    if g is not None:
        world_play.declare_affordances(agent, g, CONTROLS)       # 2 affordances

    t0 = time.time()
    drove = 0
    for i in range(args.actions):
        g = _game(agent)
        if g is not None:                                        # 2 stamp the world's numbers (observation)
            agent.inner.set_attr(g, "frame", float(i))
            agent.inner.set_attr(g, "score", float(ctx.get("score", 0) or 0))
            world_play.declare_affordances(agent, g, CONTROLS)

        agent.tick(); agent.inner.run_rules()                    # 3 THE AGENT ACTS (graph-native)

        # 4 read the agent's chosen action off the graph
        act = ""
        if g is not None:
            act = agent.s.node(g)["attrs"].get("chosen_action") or ""
        if not act:
            act = agent.s.node(agent.agent)["attrs"].get("chosen_action") or ""
        bootstrap = not act
        if bootstrap:                                            # host fallback: act to perceive
            act = CONTROLS[i % len(CONTROLS)]
        else:
            drove += 1

        # emit: the agent's three voices (read graph + produce) -> console + reasoning field
        voices = []
        for label, fn in (("I see", lambda: R._speak_frame(agent, prod, say_map)),
                          ("salient", lambda: R._speak_salient(agent, prod)),
                          ("aim", lambda: R._speak_intent(agent, prod))):
            txt = fn()
            if txt:
                voices.append(f"{label}: {txt}")
        reasoning = ("  ||  ".join(voices)) or "(no utterance)"

        t = time.time()
        sub, ctx = world.apply((act,), reasoning=reasoning)
        agent.perceive_frame(sub)                                # 1 observe next
        agent.inner.set_attr(agent.agent, "chosen_action", "")   # derive fresh next frame

        feats = len(list(agent.s.nodes("Feature")))
        print(f"  {i+1:3} {act:6} ({(time.time()-t)*1000:4.0f}ms) "
              f"{'AGENT-CHOSE' if not bootstrap else 'bootstrap '} | features {feats}", flush=True)
        for v in voices:
            print(f"        🗣  {v}", flush=True)
        if ctx.get("over") or ctx.get("won"):
            print("  game", "WON" if ctx.get("won") else "OVER"); break

    print(f"\ntotal {time.time()-t0:.1f}s. the AGENT chose the action on {drove}/{args.actions} turns "
          f"(the rest were host bootstrap). No nav logic in the adapter — that count IS how much the "
          f"graph drives on its own.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
