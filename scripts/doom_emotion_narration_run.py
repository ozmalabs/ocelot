"""doom_emotion_narration_run — block 208000: the 205000 curiosity explorer plays
real E1M1, and at each tick its live play OBSERVABLES feed the 207000 drive
system, the modulators shift, a 207000 region fires an EMOTION, and the agent
NARRATES it. MECHANICAL I/O + MEASUREMENT only (CLAUDE.md): reveal, tick, read
chosen_action, move, measure raw observables, run the emotion graph, read the
graph's emotion, format the template. No Python decides direction OR emotion.

Reuses 205000 verbatim (scripts.doom_active_explore_run helpers) so the play
trajectory is byte-identical to the 205000 curiosity arm; the emotion layer is an
orthogonal, default-OFF consumer of the same play signals.

    PYTHONPATH=runners/dsl/python:. python3 scripts/doom_emotion_narration_run.py --budget 300
"""
from __future__ import annotations

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from domains.engine_provenance import engine_preamble  # noqa: E402
engine_preamble(strict=False)

OUTDIR = os.path.join(ROOT, "results", "doom_emotion_narration")
SEED = 205000  # same play seed as the 205000 curiosity arm


def run_episode(budget=300, view_radius=5):
    import numpy as np
    import domains.doom_explore_world as dw
    import scripts.doom_active_explore_run as R
    import domains.doom_emotion_narration_ingest as EN

    rng = np.random.default_rng(SEED)
    occ = dw.extract_e1m1_occupancy(use_cache=True)
    world = dw.DoomExploreWorld(occ, view_radius=view_radius)
    total = len(occ["walkable"])

    wa = R._boot()
    S, I = wa.s, wa.inner
    game = S.add_node("WorldInstance", {"world_type": "Game", "map_mode": "doom",
                                        "body_w": 1.0, "flood_epoch": 0.0})
    R._setup(wa, game, active_explore=True, commit=True)   # 205000 curiosity arm
    hub, ms, drive = EN.install_emotion(wa, game)          # 208000 emotion layer
    idx = EN._narration_index(wa)

    R._reveal(wa, game, world, 1, curiosity=True)
    prev_free, _ = R._coverage(wa, game)
    gp_prev = None
    MILESTONE = 50                 # a coverage-achievement grain (cells)
    milestone_prev = prev_free // MILESTONE

    trace = []          # per-tick record
    transcript = []     # narrated lines (non-neutral ticks)
    for t in range(1, budget + 1):
        # --- 205000 play: the graph chooses + we move (205000 curiosity arm) ---
        act = R._flood_and_choose(wa, game, world, t)
        gp_now, _ = R._committed_goal_pose(wa, game)      # the pursued frontier this tick
        committed = EN.committed_flag(wa, game)
        if act:
            world.apply(act)
        R._reveal(wa, game, world, t + 1, curiosity=True)  # reveal the RESULT of the move
        free, _ = R._coverage(wa, game)
        novel = free - prev_free                           # coverage delta (205000 accounting)

        # --- RAW observables (mechanical measurement; no emotion words) ---
        # `arrived` = a coverage-ACHIEVEMENT milestone was crossed this tick (the
        # agent's own coverage paid off past a new MILESTONE grain) -- REINFORCE.
        milestone_now = free // MILESTONE
        arrived = 1 if milestone_now > milestone_prev else 0
        switched = 1 if (gp_now is not None and gp_prev is not None
                         and tuple(gp_now) != tuple(gp_prev)) else 0
        # a committed frontier that vanished with no reachable successor + no
        # payoff -- an un-re-groundable goal (DISENGAGE). On a fully-connected
        # E1M1 with an idealised motor this is essentially never true; reported.
        unreach = 1 if (gp_prev is not None and gp_now is None and novel == 0) else 0

        # --- the graph produces the emotion FROM the observables ---
        code, n_fired = EN.feed_and_settle(
            wa, ms, drive, novel=novel, arrived=arrived, switched=switched,
            committed=committed, unreach=unreach)
        nar = EN.narrate(idx, code, t, free)
        da = S.node(drive)["attrs"]
        ma = S.node(ms)["attrs"]
        cfg = int(da.get("dem_cfg", 0))

        rec = dict(t=t, coverage=free, novel=novel, arrived=arrived,
                   switched=switched, committed=committed, unreach=unreach,
                   emotion_code=code, n_fired=n_fired, dem_cfg=cfg,
                   valence=int(ma.get("valence", 0)), arousal=int(ma.get("arousal", 0)),
                   arousal_band=int(ma.get("arousal_band", 0)),
                   emotion=(nar[0] if nar else "neutral"),
                   tendency=(nar[1] if nar else "-"),
                   narration=(nar[2] if nar else None))
        trace.append(rec)
        if nar:
            transcript.append(nar[2])
        prev_free = free
        gp_prev = gp_now
        milestone_prev = milestone_now

    return dict(total_walkable=total, budget=budget, view_radius=view_radius,
                final_coverage=trace[-1]["coverage"], trace=trace,
                transcript=transcript)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=300)
    ap.add_argument("--view-radius", type=int, default=5)
    args = ap.parse_args()
    os.makedirs(OUTDIR, exist_ok=True)
    res = run_episode(budget=args.budget, view_radius=args.view_radius)
    with open(os.path.join(OUTDIR, "episode.json"), "w") as f:
        json.dump(res, f)
    print("final_coverage=%d / %d walkable" % (res["final_coverage"], res["total_walkable"]))
    from collections import Counter
    c = Counter(r["emotion"] for r in res["trace"])
    print("emotion distribution:", dict(c))
    print("narrated ticks:", len(res["transcript"]))
    print("wrote", os.path.join(OUTDIR, "episode.json"))


if __name__ == "__main__":
    main()
