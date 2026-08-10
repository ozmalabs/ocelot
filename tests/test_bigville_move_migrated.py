"""bigville R1 (block 249000) -- MOVEMENT + ENERGY gates.

Graph-native movement (a Bellman flood + Argmin next-hop, both RULES) coupled to
the proven 245 social layer, plus a per-agent energy budget whose graded slow-down
is a RULE. Gates mirror BIGVILLE_MOVE_PREREG.md. No agent decision lives in Python:
every movement / energy / credibility verdict is a rule (source-audit test below).
"""
from __future__ import annotations

import json
import os
import re
import sys

import pytest

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.bigville_move_world import BigvilleMoveWorld            # noqa: E402
from worlds.bigville_sim_world import SOLID                         # noqa: E402

HL_START, HL_GOAL = (0, 2), (7, 5)
EN_START, EN_GOAL = (16, 10), (2, 10)
WALL_START, WALL_GOAL = (4, 3), (4, 8)


# ---------------------------------------------------- HEADLINE: the coupling
def test_headline_movement_changes_witnessing_and_backing():
    """G-move-changes-witnessing: a villager isolated at its seed cell witnesses
    nothing and BACKS JOHN; when it MOVES onto a line-of-sight to John's office it
    witnesses the scheme (seen_hostile 0 -> >0) and the SAME 245 credibility rule
    (bd_villager_backs) FLIPS it to BACK MARY. Movement proven by its effect on the
    already-proven social layer."""
    # STAY (movement OFF): never gains office LOS.
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", HL_START, HL_GOAL, energy=1000.0, energy_cost=1.0)
    for _ in range(11):
        w.step(move=False)
    stay = w.backs_of("villager_1")
    w.close()
    assert stay["seen_hostile"] == 0 and stay["backs"] == "John", stay

    # MOVE (movement ON): navigates into office LOS -> witnesses -> flips.
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", HL_START, HL_GOAL, energy=1000.0, energy_cost=1.0)
    trace = []
    for t in range(1, 12):
        w.step()
        trace.append(dict(tick=t, **w.backs_of("villager_1")))
    move = w.backs_of("villager_1")
    w.close()

    assert move["seen_hostile"] > 0 and move["backs"] == "Mary", move
    # The flip coincides with the FIRST tick office LOS is gained (seen_hostile > 0)
    # -- i.e. it is the WITNESSING (a function of WHERE the agent went), not a paper
    # broadcast: with seen_hostile forced to 0 the credibility rule keeps John.
    first_witness = next(r for r in trace if r["seen_hostile"] > 0)
    first_mary = next(r for r in trace if r["backs"] == "Mary")
    assert first_mary["tick"] >= first_witness["tick"]
    # witnessing is load-bearing: the paper alone (heard_claim) would NOT have
    # flipped it (heard_claim*(cw-dp) <= seen_benevolent*cw without the hostility term).
    assert move["heard_claim"] * 1 <= move["seen_benevolent"] * 1 + move["seen_hostile"], move
    assert move["seen_benevolent"] * 1 - move["seen_hostile"] < move["heard_claim"] * 1, (
        "without the witnessed hostility term the credibility inequality would not "
        "hold -- witnessing is the decisive cause", move)


# ---------------------------------------------------- ENERGY: graded slow-down
def _cells_per_tick(cost, slow_on, ticks=9):
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", EN_START, EN_GOAL, energy=100.0,
                energy_cost=cost, slow_on=slow_on)
    curve = [len(w.move_one("villager_1")) for _ in range(ticks)]
    w.close()
    return curve


def test_energy_slows_graded():
    """G-energy-slows: cells/tick DECREASES as the budget depletes (graded, from the
    rule's 3/2/1/0 step function of energy). Monotone non-increasing; a rested agent
    covers strictly more over the first few ticks than an exhausted one covers later."""
    curve = _cells_per_tick(cost=8.0, slow_on=1.0)
    assert curve[0] == 3, curve                       # rested: full budget
    assert all(curve[i] >= curve[i + 1] for i in range(len(curve) - 1)), curve  # monotone
    assert min(curve) == 0 and max(curve) == 3, curve  # spans full -> exhausted
    assert sum(curve[:2]) > sum(curve[-2:]), curve     # rested covers more than exhausted


def test_control_energy_ablated_no_slowdown():
    """Failing control: with energy-cost ablated (slow_on=0, cost=0) there is NO
    graded slow-down -- the curve is FLAT at full budget until the goal is reached
    (then 0). Cost is load-bearing for the slow-down."""
    ablated = _cells_per_tick(cost=0.0, slow_on=0.0)
    cost_on = _cells_per_tick(cost=8.0, slow_on=1.0)

    def leading(curve):     # every tick BEFORE the last non-zero (= before arrival)
        idx = max(i for i, n in enumerate(curve) if n > 0)
        return curve[:idx]
    # ablated: full budget every travelling tick -> the only sub-3 tick is arrival.
    assert leading(ablated) and all(n == 3 for n in leading(ablated)), ablated
    # cost-on: graded drops (2, then 1) appear WHILE still travelling -> slow-down.
    assert not all(n == 3 for n in leading(cost_on)), cost_on
    # over equal ticks the ablated (no-cost) agent covers strictly more ground.
    assert sum(ablated) > sum(cost_on), (ablated, cost_on)


# ---------------------------------------------------- failing controls
def test_control_no_goal_is_idle():
    """No goal -> no purposeful movement (the flood never seeds; pick_hop's
    reachability guard is false). No wander."""
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", EN_START, goal=None, energy=1000.0)
    moves = sum(len(w.move_one("villager_1")) for _ in range(5))
    pos = w.pos["villager_1"]
    w.close()
    assert moves == 0 and pos == EN_START


def test_control_goal_at_current_cell_zero_moves():
    """Goal == current cell (gdist 0) -> pick_hop guard (gdist>=1) false -> 0 moves."""
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", EN_START, EN_START, energy=1000.0)
    moves = sum(len(w.move_one("villager_1")) for _ in range(5))
    w.close()
    assert moves == 0


def test_control_wall_routes_around_no_teleport():
    """A wall on the straight line -> the path routes AROUND it (through the single
    door), never teleporting: every step is orthogonally adjacent and walkable, and
    the detour is longer than the Manhattan distance."""
    w = BigvilleMoveWorld()
    w.add_mover("villager_1", WALL_START, WALL_GOAL, energy=1000.0, energy_cost=1.0)
    path = [WALL_START]
    for _ in range(40):
        path += w.move_one("villager_1")
        if w.pos["villager_1"] == WALL_GOAL:
            break
    grid = w.grid
    w.close()
    man = abs(WALL_START[0] - WALL_GOAL[0]) + abs(WALL_START[1] - WALL_GOAL[1])
    assert path[-1] == WALL_GOAL, path
    assert (len(path) - 1) > man, (len(path) - 1, man)                 # a real detour
    assert all(abs(path[i][0] - path[i + 1][0]) + abs(path[i][1] - path[i + 1][1]) == 1
               for i in range(len(path) - 1)), path                    # no teleport
    assert all(grid[y][x] not in SOLID for (x, y) in path), path       # never enters a wall


# ---------------------------------------------------- discipline / source-audit
def test_movement_decisions_are_rules_not_python():
    """Source-audit: the world adapter runs NO rule engine and holds no movement
    decision; the decisions live in the two seeds (mv_pick_hop = the hop; mv_relax =
    the flood; mv_energy_budget = the slow-down; mv_deplete = the spend)."""
    wf = open(os.path.join(_ROOT, "worlds", "bigville_move_world.py")).read()
    for forbidden in ("graph_rewrite", "gr.run", "make_rule", "gr._match", "gr._apply"):
        assert forbidden not in wf, f"world adapter calls a rule engine: {forbidden}"
    nav = json.load(open(os.path.join(_ROOT, "seeds", "bigville_move_nav.json")))
    en = json.load(open(os.path.join(_ROOT, "seeds", "bigville_move_energy.json")))
    names = {r["name"] for r in nav["rules"]} | {r["name"] for r in en["rules"]}
    assert {"mv_relax", "mv_pick_hop", "mv_seed_goal",
            "mv_energy_budget", "mv_deplete"} <= names, names
    # the hop decision is an Argmin descending the flood field (a rule, not Python)
    pick = next(r for r in nav["rules"] if r["name"] == "mv_pick_hop")
    assert "Argmin" in json.dumps(pick), "the next-hop must be an Argmin rule"


def test_no_new_rust_and_engine_invariant():
    """No new Rust primitive: both seeds compose existing DSL Terms only. And the
    engine provenance asserts the INVARIANT (source_match in {own, shared}) -- never
    a pinned md5 (lesson 7b)."""
    from domains.engine_provenance import engine_provenance
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
    # existing Terms only -- spot-check the Term vocabulary the seeds use is standard
    used = set()
    for seed in ("bigville_move_nav", "bigville_move_energy"):
        d = json.load(open(os.path.join(_ROOT, "seeds", seed + ".json")))
        used |= set(re.findall(r'"type":\s*"([A-Z][A-Za-z]+)"', json.dumps(d)))
    known = {"Attr", "Var", "Lit", "Plus", "Minus", "Times", "Max", "Lt", "Gte",
             "Eq", "Gt", "And", "IfThenElse", "Argmin", "Neighbours",
             "Sum"}  # carried-weight penalty in mv_energy_budget -- an existing Term, no new Rust
    assert used <= known, f"unexpected Term(s) -- new Rust? {used - known}"
