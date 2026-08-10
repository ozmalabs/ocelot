"""doom_active_explore_run — ACTIVE curiosity-driven exploration on REAL E1M1 geometry
(block 205000), controlled-motor setting.

Closes perception->DECISION->ACTION: the eye reveals what is in view (unknown =
ABSENCE), the belief map accumulates + space_quantize decodes FRONTIER boxes, and
the graph CHOOSES the next cardinal step (frontier-seeking + learning-progress
curiosity + commit-net, all rules/nets in seeds/quanta_navigation.json +
seeds/doom_active_exploration.json). This runner is MECHANICAL I/O + MEASUREMENT
only: reveal, tick, read chosen_action, move, score. No Python decides direction.

Arms (G1 baselines), same map machinery, only the ACTION SOURCE differs:
  curiosity  — the graph's chosen_action (frontier + LP + commit)
  nearest    — the graph's chosen_action (frontier, LP off, commit off; reference)
  random     — a uniform random cardinal step (rng(205000))
  passive    — no move (strict no-move floor; coverage = initial view)

    PYTHONPATH=runners/dsl/python:. python3 scripts/doom_active_explore_run.py --budget 300
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

OUTDIR = os.path.join(ROOT, "results", "doom_active_explore")
SEED = 205000

# self-region ControlResponses: pose order is [x, y]; dr<->x, dc<->y.
CONTROLS = [("Right", 1, 0), ("Left", -1, 0), ("Down", 0, 1), ("Up", 0, -1)]


def _boot():
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    wa = WorldAdapter(seeds=())
    load_all_seeds(wa)
    return wa


def _setup(wa, game, *, active_explore, commit):
    """Mechanical world wiring (DATA, once): quanta mode; the 4 cardinal actions as
    ControlResponse data on an is_self Region; the active-explore + commit flags."""
    S, I = wa.s, wa.inner
    I.set_attr(game, "nav_repr", "quanta")
    I.set_attr(game, "body_w", 1.0)
    I.set_attr(game, "active_explore", 1.0 if active_explore else 0.0)
    sr = S.add_node("Region", {"is_self": 1.0})
    I.add_edge_unchecked(game, "has_region", sr)
    for cname, dr, dc in CONTROLS:
        cr = S.add_node("ControlResponse", {"dr": float(dr), "dc": float(dc), "dz": 0.0,
                                            "cname": cname})
        I.add_edge_unchecked(sr, "responds_via", cr)
    if active_explore:
        import domains.doom_active_explore_ingest as ae
        ae.install_curiosity(wa, game, commit=commit)


def _reveal(wa, game, world, epoch, *, curiosity=False):
    """Mechanical eye: reveal walkable cells in view as belief, accumulate + quantize.
    For the curiosity arm, also maintain the pose-keyed frontier interest (lp_* input) and
    bump the commit-net clock -- all mechanical adapter I/O."""
    import domains.doom_map_ingest as dm
    free, walls = world.view_cells()
    # emit as ObsCells via the 161000 adapter's _emit (walk own cell; seen free/wall).
    obs = [(world.pos, "walk")]
    for c in free:
        if c != world.pos:
            obs.append((c, "depth_free"))
    for c in walls:
        obs.append((c, "depth_wall"))
    dm._emit(wa, game, obs)
    work = dm.accumulate(wa, game, epoch=epoch)
    if curiosity:
        import domains.doom_active_explore_ingest as ae
        ae.maintain_frontier_interest(wa, game, epoch)
        ae.bump_deliberation(wa, game)
    return work


def _flood_and_choose(wa, game, world, epoch):
    """Fire the qf_* flood to fixpoint and read the graph's chosen cardinal action.
    Two-phase closed scheduling (the quanta_flood_step precedent). Decides nothing."""
    S, I = wa.s, wa.inner
    # commit-net gate (separate pass): retire the goal while the net has not committed
    import domains.doom_active_explore_ingest as ae
    ae.retire_while_deliberating(wa, game)
    I.set_attr(game, "avatar_pose", [int(world.pos[0]), int(world.pos[1])])
    I.set_attr(game, "chosen_action", "")
    I.set_attr(game, "closed", -1.0)
    I.set_attr(game, "flood_epoch", float(epoch))
    I.run_rules()                       # phase 1: qf flood to fixpoint (+ frontier commit + hop)
    I.set_attr(game, "closed", 0.0)
    I.run_rules()                       # phase 2: closed detection on the converged field
    return S.node(game)["attrs"].get("chosen_action") or ""


def _coverage(wa, game):
    """Reconstructed passable (free) cells known so far — the map coverage."""
    import domains.doom_map_ingest as dm
    m = dm.read_map(wa, game)
    free = sum(1 for v in m["cells"].values() if v == 0.0)
    return free, m


def _committed_goal_pose(wa, game):
    S, I = wa.s, wa.inner
    for g in I.neighbours(game, "committed_goal"):
        p = S.node(g)["attrs"].get("pose")
        if p is not None:
            return tuple(int(v) for v in p), str(g)
    return None, None


def run_arm(arm, occ, *, budget, view_radius, rng):
    import domains.doom_explore_world as dw
    world = dw.DoomExploreWorld(occ, view_radius=view_radius)
    total = len(occ["walkable"])
    active_explore = (arm in ("curiosity", "nocommit"))
    commit = (arm == "curiosity")
    wa = _boot()
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom",
                                        "body_w": 1.0, "flood_epoch": 0.0})
    if arm in ("curiosity", "nearest", "nocommit"):
        _setup(wa, game, active_explore=active_explore, commit=commit)

    curve = []
    goal_trace = []          # (tick, goal_pose) for dwell/thrash measurement
    work_trace = []          # (tick, accumulate_work, novel_cells_delta)
    path = [world.pos]
    prev_free = 0
    cur = active_explore
    _reveal(wa, game, world, 1, curiosity=cur)
    free0, _ = _coverage(wa, game)
    curve.append((0, free0))
    prev_free = free0
    for t in range(1, budget + 1):
        if arm == "passive":
            act = ""
        elif arm == "random":
            act = CONTROLS[rng.integers(0, 4)][0]
        else:
            act = _flood_and_choose(wa, game, world, t)
            gp, gid = _committed_goal_pose(wa, game)
            goal_trace.append((t, gp))      # goal POSE: the substrate REUSES freed node ids, so a
            #                                 held frontier = a stable pose; thrash = pose changes.
        if act:
            world.apply(act)
        path.append(world.pos)
        import time as _time
        _t0 = _time.perf_counter()
        work = _reveal(wa, game, world, t + 1, curiosity=cur)
        dt_ms = (_time.perf_counter() - _t0) * 1000.0
        free, _ = _coverage(wa, game)
        work_trace.append((t, round(dt_ms, 2), free - prev_free))   # (tick, reveal_ms, novel_cells)
        prev_free = free
        curve.append((t, free))
    return {"arm": arm, "total_walkable": total, "curve": curve, "goal_trace": goal_trace,
            "work_trace": work_trace, "path": [list(p) for p in path],
            "final_free": curve[-1][1]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=300)
    ap.add_argument("--view-radius", type=int, default=5)
    ap.add_argument("--arms", default="curiosity,nearest,nocommit,random,passive")
    ap.add_argument("--repeats-random", type=int, default=3)
    args = ap.parse_args()
    import numpy as np
    import domains.doom_explore_world as dw

    os.makedirs(OUTDIR, exist_ok=True)
    occ = dw.extract_e1m1_occupancy(use_cache=True)
    arms = args.arms.split(",")
    results = {}
    for arm in arms:
        if arm == "random":
            reps = []
            for r in range(args.repeats_random):
                rng = np.random.default_rng(SEED + r)
                reps.append(run_arm("random", occ, budget=args.budget,
                                    view_radius=args.view_radius, rng=rng))
            results["random"] = reps
        else:
            rng = np.random.default_rng(SEED)
            results[arm] = run_arm(arm, occ, budget=args.budget,
                                   view_radius=args.view_radius, rng=rng)
        fin = (results[arm][0]["final_free"] if arm == "random" else results[arm]["final_free"])
        print(f"[{arm}] final_free={fin} / {len(occ['walkable'])}", flush=True)
    with open(os.path.join(OUTDIR, "arms.json"), "w") as f:
        json.dump({"budget": args.budget, "view_radius": args.view_radius,
                   "total_walkable": len(occ["walkable"]), "results": results}, f)
    print("wrote", os.path.join(OUTDIR, "arms.json"))


if __name__ == "__main__":
    main()
