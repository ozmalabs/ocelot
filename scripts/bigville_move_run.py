"""bigville R1 (block 249000) -- MOVEMENT + ENERGY oracle run.

Runs the pre-registered scenarios (BIGVILLE_MOVE_PREREG.md) on the graph-native
movement/energy seeds and dumps a results JSON for the RESULTS doc:

  * G-move-changes-witnessing (HEADLINE): STAY (movement OFF, isolated seed pos)
    vs MOVE (navigates into office line-of-sight). Witnessing office hostility
    (seen_hostile 0 -> >0) flips the 245 credibility rule bd_villager_backs.
  * G-energy-slows: cells/tick curve as the energy budget depletes, vs the
    energy-ablated arm (flat until goal).
  * Failing controls: no-goal idle / goal-at-cell zero / wall detour (no teleport).

No agent decision in Python -- every movement/energy/credibility verdict is a rule.
"""
from __future__ import annotations

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains.engine_provenance import provenance_line          # noqa: E402
from worlds.bigville_move_world import BigvilleMoveWorld        # noqa: E402
from worlds.bigville_sim_world import (SOLID, SIGHT_RANGE,       # noqa: E402
                                       HEAR_RANGE)

HL_START, HL_GOAL = (0, 2), (7, 5)     # isolated seed pos ; goal with office LOS, not square
EN_START, EN_GOAL = (16, 10), (2, 10)  # long straight-ish route for the energy curve
WALL_START, WALL_GOAL = (4, 3), (4, 8)  # inside office -> outside; only exit is door (8,4)


def _row(w, name):
    b = w.backs_of(name)
    return {k: b[k] for k in ("pos", "seen_hostile", "seen_benevolent",
                              "heard_claim", "backs")}


def headline():
    # STAY (movement OFF): the villager never leaves its isolated seed cell.
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", HL_START, HL_GOAL, energy=1000.0, energy_cost=1.0)
    stay_seed = _row(w, "villager_1")
    for _ in range(11):
        w.step(move=False)
    stay_final = _row(w, "villager_1")
    w.close()
    # MOVE (movement ON): navigates into office line-of-sight.
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", HL_START, HL_GOAL, energy=1000.0, energy_cost=1.0)
    move_seed = _row(w, "villager_1")
    trace = []
    for t in range(1, 12):
        w.step()
        trace.append(dict(tick=t, **_row(w, "villager_1")))
    move_final = _row(w, "villager_1")
    cost = w.cost_report()
    w.close()
    # first tick office LOS is gained == first tick seen_hostile rises == the flip
    flip = next((r for r in trace if r["seen_hostile"] > 0), None)
    return dict(start=list(HL_START), goal=list(HL_GOAL),
                stay_seed=stay_seed, stay_final=stay_final,
                move_seed=move_seed, move_final=move_final,
                move_trace=trace, flip_tick=flip["tick"] if flip else None,
                cost=cost)


def energy_curve():
    def run(cost, slow_on):
        w = BigvilleMoveWorld()
        w.add_mover("villager_1", EN_START, EN_GOAL, energy=100.0,
                    energy_cost=cost, slow_on=slow_on)
        rows = []
        for t in range(1, 10):
            e0 = w.energy_of("villager_1")
            n = len(w.move_one("villager_1"))
            rows.append(dict(tick=t, energy_before=round(e0, 1), cells_moved=n,
                             budget=w.budget_of("villager_1"),
                             energy_after=round(w.energy_of("villager_1"), 1)))
        cost_rep = w.cost_report()
        w.close()
        return rows, cost_rep
    on, on_cost = run(cost=8.0, slow_on=1.0)
    ablated, _ = run(cost=0.0, slow_on=0.0)     # energy-cost ablated -> no slow-down
    return dict(thresholds=dict(e_high=70, e_mid=40, e_low=15, budget="3/2/1/0"),
                cost_on=on, ablated=ablated, cost_report=on_cost)


def controls():
    out = {}
    # no goal -> idle
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", EN_START, goal=None, energy=1000.0)
    out["no_goal_total_moves"] = sum(len(w.move_one("villager_1")) for _ in range(5))
    out["no_goal_pos"] = list(w.pos["villager_1"])
    w.close()
    # goal at current cell -> zero moves
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", EN_START, EN_START, energy=1000.0)
    out["goal_at_cell_moves"] = sum(len(w.move_one("villager_1")) for _ in range(5))
    w.close()
    # wall on the straight line -> route AROUND, no teleport
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", WALL_START, WALL_GOAL, energy=1000.0, energy_cost=1.0)
    path = [WALL_START]
    for _ in range(40):
        path += w.move_one("villager_1")
        if w.pos["villager_1"] == WALL_GOAL:
            break
    man = abs(WALL_START[0] - WALL_GOAL[0]) + abs(WALL_START[1] - WALL_GOAL[1])
    out["wall"] = dict(
        start=list(WALL_START), goal=list(WALL_GOAL), path=[list(p) for p in path],
        reached=w.pos["villager_1"] == WALL_GOAL, path_len=len(path) - 1, manhattan=man,
        is_detour=(len(path) - 1) > man,
        all_steps_adjacent=all(abs(path[i][0] - path[i + 1][0]) +
                               abs(path[i][1] - path[i + 1][1]) == 1
                               for i in range(len(path) - 1)),
        no_wall_teleport=all(w.grid[y][x] not in SOLID for (x, y) in path),
        exits_via_door=[8, 4] in [list(p) for p in path])
    w.close()
    return out


def main():
    res = dict(block=249000, provenance=provenance_line(),
               sight_range=SIGHT_RANGE, hear_range=HEAR_RANGE,
               headline=headline(), energy=energy_curve(), controls=controls())
    outdir = os.path.join(_ROOT, "results", "bigville_move")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "r1_results.json")
    with open(path, "w") as f:
        json.dump(res, f, indent=1)
    print("wrote", path)
    h = res["headline"]
    print("HEADLINE stay_final:", h["stay_final"])
    print("HEADLINE move_final:", h["move_final"], "flip_tick", h["flip_tick"])
    print("ENERGY cost_on cells/tick:", [r["cells_moved"] for r in res["energy"]["cost_on"]])
    print("ENERGY ablated cells/tick:", [r["cells_moved"] for r in res["energy"]["ablated"]])
    print("CONTROLS:", {k: v for k, v in res["controls"].items() if k != "wall"})
    print("WALL:", {k: res["controls"]["wall"][k] for k in
                    ("reached", "path_len", "manhattan", "is_detour",
                     "all_steps_adjacent", "no_wall_teleport", "exits_via_door")})
    return res


if __name__ == "__main__":
    main()
