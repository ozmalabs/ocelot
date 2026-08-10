"""bigville block 292000 -- ATTR-TRIGGERED FRONTIER-INCREMENTAL MATCHING gates.

The nav flood (`mv_relax`, a Bellman-Ford relaxation to fixpoint) is driven by
RULE-EFFECT `gdist` attr writes. This block seeds the predicate-retraction
frontier from those effect writes, so the flood re-evaluates only the cells
incident to a changed cell instead of clearing every cursor -- BYTE-IDENTICALLY.

Gates mirror BIGVILLE_FRONTIER_PREREG.md. The deciding metrics are DETERMINISTIC
byte-identity hashes + the non-vacuous falsifier, NOT wall-clock.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_move_world import BigvilleMoveWorld            # noqa: E402

# walkable cells (the 245 scaffold grid); goal is far from start so the flood
# actually relaxes across the whole map.
START, GOAL = (0, 2), (27, 9)
SCEN = [
    ("villager_1", (0, 2), (7, 5)),
    ("villager_2", (16, 10), (2, 10)),
    ("villager_3", (4, 3), (4, 8)),
]


def _field_hash(w):
    fld = sorted((str(nid), round(float(w.eng.node(nid)["attrs"]["gdist"]), 6))
                 for nid in w._cell_at.values())
    return hashlib.sha256(json.dumps(fld, default=str).encode()).hexdigest()


def _one_flood_field(use_pred_retract, *, unsound=False):
    w = BigvilleMoveWorld()
    w._use_pred_retract = use_pred_retract
    w._use_field_cache = False                       # force a fresh flood
    if unsound:
        w.eng.set_predicate_retraction(True)
        w.eng.set_predicate_retraction_unsound(True)
    w.add_mover("m", START, GOAL, energy=1e12, energy_cost=0.0)
    w._flood_and_budget("m", w._movers["m"])
    h = _field_hash(w)
    w.close()
    return h


# ------------------------------------------------------ G-field-byteid
def test_flood_field_is_byte_identical_off_vs_on():
    """G-field-byteid: the full gdist field after a flood is BIT-IDENTICAL with
    the frontier OFF (blanket cursor-clear) vs ON (attr-frontier re-eval)."""
    off = _one_flood_field(False)
    on = _one_flood_field(True)
    assert off == on, ("flood field diverged frontier off vs on\n"
                       f"  off={off[:16]}  on={on[:16]}")


# ------------------------------------------------------ G-falsifier
def test_unsound_falsifier_diverges_the_flood():
    """G-falsifier: dropping one frontier node (predicate_retraction_unsound)
    MUST diverge from the sound flood -- the gate is non-vacuous (the frontier is
    genuinely exercised, not equal to full-scan by accident)."""
    sound = _one_flood_field(False)
    unsound = _one_flood_field(True, unsound=True)
    assert unsound != sound, ("the unsound falsifier did NOT diverge -- the "
                              "frontier gate is VACUOUS (not actually engaged)")


# ------------------------------------------------------ G-traj-byteid
def test_full_trajectory_is_byte_identical_off_vs_on():
    """G-traj-byteid: the full multi-mover trajectory + finals over a 14-tick run
    is BIT-IDENTICAL frontier off vs on. This exercises the SCOPING: the flood
    runs frontier-on, the hop loop (mv_pick_hop, kicked by a has_next write it
    does not read) runs frontier-off under the blanket dirtier."""
    def run(use_pr):
        w = BigvilleMoveWorld()
        w._use_pred_retract = use_pr
        for name, start, goal in SCEN:
            w.add_mover(name, start, goal, energy=1000.0, energy_cost=1.0)
        trajs = {s[0]: [] for s in SCEN}
        for _ in range(14):
            w.step()
            for name, *_ in SCEN:
                trajs[name].append(tuple(w.pos[name]))
        w.close()
        return hashlib.sha256(json.dumps({k: trajs[k] for k in sorted(trajs)},
                                         sort_keys=True, default=str).encode()).hexdigest()
    off, on = run(False), run(True)
    assert off == on, f"trajectory diverged off vs on: {off[:16]} != {on[:16]}"


# ------------------------------------------------------ G-pickhop-excluded
def test_all_movers_reach_goal_under_frontier():
    """G-pickhop-excluded (behavioural): with the frontier ON, every mover still
    REACHES its goal. If mv_pick_hop were wrongly frontier-driven it would either
    freeze (never fire) or diverge; the guard makes it full-scan, so movement is
    unchanged."""
    w = BigvilleMoveWorld()
    w._use_pred_retract = True
    for name, start, goal in SCEN:
        w.add_mover(name, start, goal, energy=1000.0, energy_cost=1.0)
    for _ in range(20):
        w.step()
    finals = {name: tuple(w.pos[name]) for name, *_ in SCEN}
    goals = {name: goal for name, _, goal in SCEN}
    w.close()
    for name in goals:
        assert finals[name] == goals[name], (
            f"{name} did not reach its goal under the frontier: "
            f"at {finals[name]}, goal {goals[name]}")
