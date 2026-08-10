"""Run the NEW order-N incremental perception on the LIVE ls20 game.

Boots the seed agent, connects the live ARC-AGI-3 transport (worlds/arc.ArcWorld
over scripts/arc3_live_env), and drives the agent's OWN perceive_frame on each
live frame — then reports what the perception UNDERSTANDS (regions, the avatar as
a Body that owns its component Regions, the floor map, any order-N split into
owned components). The measure is understanding, not score.

Thin harness: it only sequences reset -> perceive -> read -> act -> step. Every
figure/ground / avatar / split judgement is the agent's graph rules.

  ulimit -v 12000000
  timeout 400 env PYTHONPATH=runners/dsl/python:. python3 \
      scripts/run_ls20_ordern_perception.py --actions 12
"""
from __future__ import annotations
import argparse, os, sys, time
from pathlib import Path
_HERE = Path(__file__).resolve().parent; _ROOT = _HERE.parent
for p in (str(_ROOT), str(_HERE), str(_ROOT / "runners" / "dsl" / "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from _arc3_load_key import load_arc_api_key      # noqa: E402
from arc3_live_env import Arc3LiveEnv             # noqa: E402
from worlds.arc import ArcWorld                   # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402
from substrate.boot_all import load_all_seeds     # noqa: E402

GAME = "ls20-9607627b"


def _understanding(ag):
    """Read what the agent's perception holds — pure query, no decisions."""
    S, I = ag.s, ag.inner
    regions = list(S.nodes("Region"))
    bodies = [n for n in S.nodes("WorldInstance")
              if S.node(n)["attrs"].get("world_type") == "Body"]
    # the avatar = a Body that owns (controls) one-or-more component Regions
    avatar = None
    for b in bodies:
        comps = list(I.neighbours(b, "controls"))
        if comps:
            a = S.node(b)["attrs"]
            cells = sum(len(list(I.in_neighbours(r, "within"))) for r in comps)
            avatar = {"components": len(comps), "cells": cells,
                      "cy": a.get("cy"), "cx": a.get("cx"),
                      "drow": a.get("drow"), "dcol": a.get("dcol")}
    floor = sum(1 for n in S.nodes("WorldInstance")
                if S.node(n)["attrs"].get("world_type") == "SpatialLocation")
    # figure-sized regions (small, non-ground) + their motion/votes — to see whether
    # the avatar-candidate moves rigidly and accrues votes, or loses identity.
    figs = []
    for r in regions:
        a = S.node(r)["attrs"]; cnt = a.get("count") or 0
        if 0 < cnt <= 40:
            figs.append({"rid": a.get("rid"), "n": cnt, "v": a.get("value") or a.get("rvalue"),
                         "drow": a.get("drow"), "dcol": a.get("dcol"),
                         "votes": a.get("avatar_votes")})
    figs.sort(key=lambda d: -(d["votes"] or 0))
    return {"regions": len(regions), "avatar": avatar, "floor_cells": floor,
            "figures": figs[:6]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--actions", type=int, default=12)
    args = ap.parse_args()

    if not load_arc_api_key():
        print("could not load ARC_API_KEY from .env — aborting"); return 1
    print(f"connecting to {GAME} ...", flush=True)
    env = Arc3LiveEnv(GAME)
    ag = WorldAdapter(seeds=()); load_all_seeds(ag)
    w = ArcWorld(env)

    t0 = time.time()
    sub, ctx = w.reset()
    ag.perceive_frame(sub)
    u = _understanding(ag)
    print(f"reset ({time.time()-t0:.1f}s): score={ctx['score']} regions={u['regions']} "
          f"floor={u['floor_cells']} avatar={u['avatar']}", flush=True)

    # a fixed exploratory sequence so the figure MOVES (the avatar is whatever
    # translates as a rigid body under the agent's actions). Not play strategy —
    # just enough motion for the perception to reveal the avatar + any split/merge.
    seq = (["Up", "Down"] * 4 + ["Up"] * 4 + ["Down"] * 4)
    for i in range(args.actions):
        act = seq[i % len(seq)]
        t = time.time()
        sub, ctx = w.apply((act,))
        ag.perceive_frame(sub)
        u = _understanding(ag)
        av = u["avatar"]
        avs = (f"avatar(comp={av['components']} cells={av['cells']} "
               f"d=({av['drow']:+.1f},{av['dcol']:+.1f}))") if av else "avatar=none"
        figs = "; ".join(f"rid={f['rid']} n={f['n']} v={f['v']} "
                         f"d=({f['drow']},{f['dcol']}) votes={f['votes']}" for f in u["figures"])
        print(f"  {i+1:2} {act:5} ({time.time()-t:4.1f}s) score={ctx['score']} "
              f"regions={u['regions']} floor={u['floor_cells']} {avs}\n        figs: {figs}", flush=True)
        if ctx["over"] or ctx["won"]:
            print(f"  game {'WON' if ctx['won'] else 'OVER'}"); break

    print(f"\nfinal understanding: {_understanding(ag)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
