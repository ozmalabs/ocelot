"""ASK THE JABBERWOCK why its navigation isn't firing under the THIN adapter. It HAS the nav faculty; this
inspects the prerequisite CHAIN its nav rules need, frame by frame (observe -> tick), to see where it breaks:
  avatar latched?  <- AvatarMotion present?   committed goal?   distance field (_dist/_adist) on cells?
  -> chosen_action
Plus its own needed_input reflection. No nav logic here — only perceive, tick, and READ the graph.

  ulimit -v 12000000
  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_diagnose.py [--game ls20-9607627b] [--actions 8]
"""
from __future__ import annotations
import argparse, sys
from pathlib import Path
_HERE = Path(__file__).resolve().parent; _ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)
from _arc3_load_key import load_arc_api_key
from arc3_live_env import Arc3LiveEnv
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
import domains.world_play as world_play
from domains.reflective_faculty import reflect

CONTROLS = ["Up", "Down", "Left", "Right"]


def _game(a):
    return next((n for n in a.s.nodes("WorldInstance")
                 if a.s.node(n)["attrs"].get("world_type") == "Game"), None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default="ls20-9607627b"); ap.add_argument("--actions", type=int, default=8)
    args = ap.parse_args()
    if not load_arc_api_key():
        print("no key"); return 1
    a = WorldAdapter(seeds=()); load_all_seeds(a)
    S, I = a.s, a.inner

    # which nav rules does it HOLD? (the faculty)
    navnames = []
    for r in S.nodes("Rule"):
        nm = (S.node(r)["attrs"].get("id") or S.node(r)["attrs"].get("name") or "")
        if any(k in str(nm).lower() for k in ("hop", "gradient", "seek", "goal", "nav", "flood", "avatar",
                                              "frontier", "route", "reach", "descend", "explore")):
            navnames.append(str(nm))
    print("nav-ish rules it holds:", sorted(set(navnames))[:30], flush=True)

    env = Arc3LiveEnv(args.game); world = ArcWorld(env)
    sub, ctx = world.reset(); a.perceive_frame(sub)
    g = _game(a)
    if g is not None:
        world_play.declare_affordances(a, g, CONTROLS)

    def chain():
        cells = [c for c in S.nodes("WorldInstance") if S.node(c)["attrs"].get("world_type") == "Cell"]
        av = list(S.nodes("AvatarCandidate"))
        latched = [n for n in av if S.node(n)["attrs"].get("is_avatar")]
        mot = list(S.nodes("AvatarMotion"))
        gg = _game(a)
        goal = list(I.neighbours(gg, "committed_goal")) if gg is not None else []
        dist = [c for c in cells if S.node(c)["attrs"].get("_dist") is not None]
        adist = [c for c in cells if S.node(c)["attrs"].get("_adist") is not None]
        ca = ((S.node(gg)["attrs"].get("chosen_action") if gg is not None else "") or
              S.node(a.agent)["attrs"].get("chosen_action") or "")
        return (len(av), len(latched), len(mot), len(goal), len(dist), len(adist), ca)

    for i in range(args.actions):
        gg = _game(a)
        if gg is not None:
            I.set_attr(gg, "frame", float(i)); world_play.declare_affordances(a, gg, CONTROLS)
        a.tick(); I.run_rules()
        nav, lat, mot, goal, dist, adist, ca = chain()
        print(f"  f{i}: avatarcand={nav} latched={lat} AvatarMotion={mot} committed_goal={goal} "
              f"adist_cells={adist} dist_cells={dist} -> chosen_action={ca!r}", flush=True)
        act = ca or CONTROLS[i % 4]
        sub, ctx = world.apply((act,)); a.perceive_frame(sub)
        I.set_attr(a.agent, "chosen_action", "")

    # ASK IT directly
    try:
        ni = reflect("needed_input", "route the avatar to the goal cell", S)
        print("\n  [reflect needed_input] ->", str(ni)[:400], flush=True)
    except Exception as e:
        print("  [reflect needed_input] err:", type(e).__name__, e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
