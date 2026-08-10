"""Gate tests for RUNG 218000 — ls20 PLANNING/EXECUTION (salience->investigate->act).

The loop closes see->understand->DO: the curiosity-first planner recognises the
required transform (217000 sd-loop) and routes the correctly-transformed symbol to
the goal; goal-blind loses. All planning DECISIONS are graph rules
(domains/ls20_planning_seed.py); the adapter is mechanical.
"""
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_scenario import make_scenario, run_episode, Planner  # noqa: E402
from scripts.arc_ls20_planning_measure import (  # noqa: E402
    measure_config, investigation_trace, source_audit, wilson,
)
from domains.ls20_planning_seed import RULES  # noqa: E402

N = 24


def test_g_solve_curious_solves():
    """G-solve: the curiosity-first planner routes the correctly-transformed symbol
    to the goal on nearly every scenario (single + multi station)."""
    r1 = measure_config(N, 1, 218000)
    r3 = measure_config(N, 3, 218001)
    assert r1["success"]["curious"][0] >= 0.90, r1["success"]
    assert r3["success"]["curious"][0] >= 0.90, r3["success"]


def test_g_vs_goal_blind_loses():
    """G-vs-goal-blind (THE control): goal-blind FAILS where curiosity-first
    SUCCEEDS — CI-separated. Goal blindness is how you lose."""
    for nst, sd in ((1, 218000), (3, 218001)):
        r = measure_config(N, nst, sd)
        cur, blind = r["success"]["curious"], r["success"]["blind"]
        assert r["wins"]["blind"] == 0, r["reasons"]["blind"]
        assert cur[1] > blind[2], (nst, cur, blind)  # curious lower bound > blind upper bound


def test_g_investigation_not_mere_detour():
    """G-investigation: on multi-station scenarios a blind-detour (detours without
    recognising WHICH transform) loses where curiosity-first wins — investigation,
    not mere detour, is the lever."""
    r3 = measure_config(N, 3, 218001)
    cur, det = r3["success"]["curious"], r3["success"]["detour"]
    assert cur[1] > det[2], (cur, det)


def test_g_graph_native_rules_no_transform_token():
    """G-graph-native: the planning rules name no specific transform family and no
    ls20 constant — the decision is generic over req_key / symbol_matches_goal."""
    audit = source_audit()
    assert audit["clean"], audit
    assert audit["rule_count"] == len(RULES)


def test_loop_closes_investigation_trace():
    """G-curiosity-first: the plan is DISCOVERED by investigation — salience
    (surprise->orient) -> investigate (recognise the transform) -> discover the
    matching station -> act (deliver)."""
    tr = investigation_trace(218007)
    assert tr["won"] is True
    assert "surprise_orient" in tr["salience"]
    assert "recognised required transform" in tr["investigate"]
    assert tr["scenario"]["required_transform"] in tr["scenario"]["station_keys"]


def test_default_off_byte_identical():
    """G-discipline: with plan_on unset the rules never fire (no waypoint written)
    — the seed is default-OFF and inert on any graph that does not opt in."""
    scn = make_scenario(np.random.default_rng(218000), n_stations=1)
    pl = Planner("curious", scn["stations"], scn["goal_rc"])
    pl.n.set_attr(pl.g, "plan_on", 0.0)          # opt OUT
    pl.n.run_rules()
    assert (pl.s.node(pl.g)["attrs"].get("waypoint") or "") == ""


def test_goal_blind_delivers_wrong_not_no_route():
    """The goal-blind failure is specifically 'delivered_wrong' (it reaches the goal
    but with the un-transformed symbol) — it is not merely failing to route."""
    r = measure_config(N, 1, 218000)
    assert r["reasons"]["blind"].get("delivered_wrong", 0) == N, r["reasons"]["blind"]
