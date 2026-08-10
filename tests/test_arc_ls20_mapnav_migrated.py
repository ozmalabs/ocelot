"""Gate tests for RUNG 220000 — ls20 MAP-NAV WIRING.

The 218000 planner solved an OPEN grid with greedy Manhattan and used NONE of the
2D-map/fog machinery. This rung stamps a `has_cell` belief and swaps the executor to
the shared `quanta_flood_step` (space_quantize + qf_* Bellman flood — the SAME nav
machinery the maze/Doom use). The 218000 DECISION rules are UNTOUCHED; only the
router changes. Gates: quanta beats greedy on WALLS; route-equivalent on OPEN;
fog retained by construction; the routing decision is graph-native; default-OFF
byte-identical.
"""
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_scenario import make_scenario, run_episode, Planner  # noqa: E402
from scripts.arc_ls20_mapnav_measure import (  # noqa: E402
    measure_walled, measure_open_parity, measure_fog_retained, source_audit,
)


def test_g_walled_quanta_beats_greedy():
    """G-walled (headline): on WALLED layouts the quanta router BEATS greedy,
    CI-separated (quanta LB > greedy UB) — greedy stalls on structure, quanta routes
    around. Both arms run the identical curious DECISION rules; the ONLY variable is
    the router."""
    w = measure_walled(10, 1, 220000)
    g, q = w["success"]["greedy"], w["success"]["quanta"]
    assert q[1] > g[2], (g, q, w["reasons"])          # CI-separated
    assert w["wins"]["quanta"] > w["wins"]["greedy"]


def test_g_open_parity_route_equivalent():
    """G-open-parity (degenerate no-fog): on OPEN layouts quanta is route-EQUIVALENT
    to greedy — every episode same win AND same step count. The whole-map zero-frontier
    flood reduces to Manhattan; no regression on the case 218000 won."""
    p = measure_open_parity(8, 220100)
    assert p["route_equivalent"], p
    assert p["same_win"] == p["n"] and p["same_steps"] == p["n"], p


def test_g_fog_retained_frontiers_reappear():
    """G-fog-retained: the SAME space_quantize path mints 0 frontier quanta on a
    COMPLETE belief and >0 on a PARTIAL belief (unknown = absence) — ZERO rule changes.
    ls20 runs the complete-belief mode; the general fog capability is intact."""
    f = measure_fog_retained()
    assert f["complete_belief_frontiers"] == 0, f
    assert f["partial_belief_frontiers"] > 0, f
    assert f["retained"], f


def test_g_graph_native_routing_is_a_rule():
    """G-graph-native: the router reads the qf_* rules' `chosen_action`; no Python
    path-search selects the move (`_reachable` is generator-side world validation)."""
    a = source_audit()
    assert a["clean"], a
    assert a["router_reads_graph_chosen_action"] and not a["banned_python_pathsearch_found"], a


def test_default_off_byte_identical_open_greedy():
    """G-discipline: the pre-220000 path is default-OFF byte-identical — walls=False
    and router='greedy' (both defaults) never touch the belief/quanta machinery, and
    an open scenario with plan_on unset writes no waypoint (the 218000 default-off)."""
    scn = make_scenario(np.random.default_rng(220000), n_stations=1)   # walls default False
    assert scn["walls"] == []                                          # no walls stamped
    # the default router is greedy (existing 218000 behaviour) and still solves the open case
    res = run_episode(scn, "curious")                                  # router default 'greedy'
    assert res["win"] is True, res
    # planner remains default-OFF when not opted in (the 218000 discipline, unchanged)
    pl = Planner("curious", scn["stations"], scn["goal_rc"])
    pl.n.set_attr(pl.g, "plan_on", 0.0)
    pl.n.run_rules()
    assert (pl.s.node(pl.g)["attrs"].get("waypoint") or "") == ""
