"""arc_ls20_mapnav_measure — RUNG 220000: wire the REAL 2D-map machinery into the
ls20 planner's ROUTING.

Corrects the 218000 open-grid triviality: 218000 solved on an OPEN 16x16 grid with
greedy Manhattan and used NONE of the existing map/fog machinery. This rung stamps a
`has_cell` occupancy belief and swaps the executor to the shared `quanta_flood_step`
(space_quantize + qf_* Bellman/portal flood) — the SAME nav machinery the maze/Doom
use. The 218000 DECISION rules are UNTOUCHED; only EXECUTION (the router) changes.
Measures, behind protected controls:

  G-walled        the quanta router BEATS greedy on WALLED layouts (greedy stalls on
                  structure; quanta routes around), CI-separated, both configs.
  G-open-parity   on OPEN layouts quanta is route-EQUIVALENT to greedy (same win AND
                  same step count every episode) — no regression on the case 218000 won.
  G-fog-retained  a COMPLETE belief mints 0 frontier quanta; a PARTIAL belief mints
                  >0, ZERO rule changes — fog is retained by construction.
  G-graph-native  the routing decision is the qf_* rules; the adapter is mechanical.

HONEST SCOPE: offline ls20-shaped scenarios; live ls20 needs ARC_API_KEY (absent —
the named frontier). Synthetic-proven mechanism != benchmark value; both reported.

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_ls20_mapnav_measure.py
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_scenario import make_scenario, run_episode, Planner  # noqa: E402

ROUTERS = ("greedy", "quanta")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def measure_walled(n, n_stations, seed):
    """Both routers on the SAME walled scenarios (same decisions, different executor)."""
    rng = np.random.default_rng(seed)
    wins = {r: 0 for r in ROUTERS}
    reasons = {r: {} for r in ROUTERS}
    for _ in range(n):
        scn = make_scenario(rng, n_stations=n_stations, walls=True)
        for r in ROUTERS:
            res = run_episode(scn, "curious", router=r)
            wins[r] += int(res["win"])
            reasons[r][res["reason"]] = reasons[r].get(res["reason"], 0) + 1
    return {"n": n, "n_stations": n_stations,
            "wins": wins,
            "success": {r: wilson(wins[r], n) for r in ROUTERS},
            "reasons": reasons}


def measure_open_parity(n, seed):
    """OPEN layouts: quanta must be route-equivalent to greedy (same win AND steps)."""
    rng = np.random.default_rng(seed)
    same_win = same_steps = 0
    gwins = qwins = 0
    for _ in range(n):
        scn = make_scenario(rng, n_stations=1, walls=False)
        rg = run_episode(scn, "curious", router="greedy")
        rq = run_episode(scn, "curious", router="quanta")
        gwins += int(rg["win"]); qwins += int(rq["win"])
        same_win += int(rg["win"] == rq["win"])
        same_steps += int(rg["steps"] == rq["steps"])
    return {"n": n, "greedy_wins": gwins, "quanta_wins": qwins,
            "same_win": same_win, "same_steps": same_steps,
            "route_equivalent": (same_win == n and same_steps == n)}


def _build_belief_and_count_frontiers(grid, avatar, goal, passable=(1,)):
    """Fire the EXACT space_quantize path on a belief and count frontier quanta.
    grid[r][c]: '#'=wall(value 4), '.'=known floor(value 1), '?'=UNKNOWN (absent from
    belief — fog). Complete belief (no '?') => 0 frontiers; partial => >0 — SAME rules."""
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    from substrate.seed_loader import engine_rules_only, SEED_DIR
    from domains.spatial_sense import quanta_flood_step
    H, W = len(grid), len(grid[0])
    s, ag = boot_core(); n = rf._native_eval2(s)
    for sid in ("navigation_modes", "affordance_basis", "quanta_navigation"):
        d = json.load(open(os.path.join(str(SEED_DIR), f"{sid}.json")))
        n.load_seed_manifest(engine_rules_only(d), ag)

    class Ag:  # the mechanical shim quanta_flood_step reads (agent.s/.inner/.agent)
        pass
    a = Ag(); a.s = s; a.inner = n; a.agent = ag
    game = s.add_node("Game", {"world_type": "Game", "frame": 0.0})
    n.set_attr(game, "nav_repr", "quanta"); n.set_attr(game, "slide", 1.0); n.set_attr(game, "ground", 4.0)
    for r in range(H):
        for c in range(W):
            g = grid[r][c]
            if g == "?":
                continue        # unknown = absence (fog), first-class
            v = 4.0 if g == "#" else 1.0
            cid = s.add_node("WorldInstance", {"world_type": "Cell", "row": float(r),
                                               "col": float(c), "value": v})
            n.add_edge_unchecked(game, "has_cell", cid)
    sr = s.add_node("Region", {"is_self": 1.0}); n.add_edge_unchecked(game, "has_region", sr)
    for nm, (dr, dc) in {"Up": (-1, 0), "Down": (1, 0), "Left": (0, -1), "Right": (0, 1)}.items():
        cr = s.add_node("ControlResponse", {"dr": float(dr), "dc": float(dc), "dz": 0.0, "cname": nm})
        n.add_edge_unchecked(sr, "responds_via", cr)
    gg = s.add_node("Goal", {"pose": [goal[0], goal[1]], "committed": 1.0, "world": 1.0})
    n.add_edge_unchecked(game, "committed_goal", gg)
    quanta_flood_step(a, game, avatar, (1, 1), list(passable), 1, (H, W), focus=([0, 0], [H - 1, W - 1]))
    return sum(1 for q in s.nodes("SpaceQuantum") if s.node(q)["attrs"].get("kind") == "frontier")


def measure_fog_retained():
    """Same code, two beliefs: complete -> 0 frontiers; partial -> >0 frontiers."""
    complete = [["." for _ in range(5)] for _ in range(5)]
    partial = [[("." if (r < 3 and c < 3) else "?") for c in range(5)] for r in range(5)]
    f_complete = _build_belief_and_count_frontiers(complete, (0, 0), (4, 4))
    f_partial = _build_belief_and_count_frontiers(partial, (0, 0), (2, 2))
    return {"complete_belief_frontiers": f_complete, "partial_belief_frontiers": f_partial,
            "retained": (f_complete == 0 and f_partial > 0)}


def source_audit():
    """G-graph-native: the ls20 scenario's routing code selects NO move in Python. The
    quanta router reads `chosen_action` (a qf_* rule verdict); the greedy control is a
    geometric step; `_reachable` is generator-side world VALIDATION (BFS over the wall
    layout), never the agent's routing. Flag any Python path-search over graph state."""
    src = (_ROOT / "worlds" / "arc_ls20_scenario.py").read_text()
    # the routing verdict must come from the graph, not a Python search:
    reads_chosen = "chosen_action" in src and "quanta_flood_step" in src
    # forbidden: a Python routing search that picks the move from graph nav state.
    banned = ["dijkstra", "a_star", "astar", "heapq", "priority_queue",
              "def _bfs_route", "def _route(", "networkx"]
    hits = [b for b in banned if b in src.lower()]
    return {"router_reads_graph_chosen_action": reads_chosen,
            "banned_python_pathsearch_found": hits, "clean": reads_chosen and not hits}


def check_gates(w1, w3, parity, fog, audit):
    def sep(res):  # quanta LB > greedy UB
        return res["success"]["quanta"][1] > res["success"]["greedy"][2]
    return {
        "G_walled_1station": sep(w1),
        "G_walled_3station": sep(w3),
        "G_open_parity": parity["route_equivalent"],
        "G_fog_retained": fog["retained"],
        "G_graph_native": audit["clean"],
        "walled_1_greedy": w1["success"]["greedy"], "walled_1_quanta": w1["success"]["quanta"],
        "walled_3_greedy": w3["success"]["greedy"], "walled_3_quanta": w3["success"]["quanta"],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--tag", default="first")
    args = ap.parse_args()

    w1 = measure_walled(args.n, 1, 220000)
    w3 = measure_walled(args.n, 3, 220001)
    parity = measure_open_parity(args.n, 220100)
    fog = measure_fog_retained()
    audit = source_audit()
    gates = check_gates(w1, w3, parity, fog, audit)

    result = {
        "rung": 220000, "tag": args.tag, "n": args.n,
        "commitment": "wire the real 2D-map machinery (walls + has_cell belief + quanta_flood_step) "
                      "into the ls20 planner EXECUTION; 218000 DECISION rules untouched; quanta beats "
                      "greedy on walls, route-equivalent on open, fog retained by construction.",
        "walled_1station": w1, "walled_3station": w3,
        "open_parity": parity, "fog_retained": fog,
        "source_audit": audit, "gates": gates,
        "note": "offline ls20-shaped scenarios; LIVE ls20 needs ARC_API_KEY (absent — the named "
                "frontier). Synthetic-proven mechanism != benchmark value.",
    }
    out = _ROOT / "results" / f"arc_ls20_mapnav_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))

    def fmt(ci):
        return f"{ci[0]:.4f} [{ci[1]:.4f}, {ci[2]:.4f}]"

    print("=== RUNG 220000 — ls20 MAP-NAV WIRING (quanta flood over a has_cell belief) ===")
    for res in (w1, w3):
        print(f"\nWALLED {res['n_stations']}-STATION  N={res['n']}")
        for r in ROUTERS:
            print(f"  {r:7s} success={fmt(res['success'][r])}  reasons={res['reasons'][r]}")
    print(f"\nOPEN PARITY N={parity['n']}: greedy {parity['greedy_wins']}/{parity['n']}  "
          f"quanta {parity['quanta_wins']}/{parity['n']}  same_win={parity['same_win']}  "
          f"same_steps={parity['same_steps']}  route_equivalent={parity['route_equivalent']}")
    print(f"FOG RETAINED: complete_belief_frontiers={fog['complete_belief_frontiers']}  "
          f"partial_belief_frontiers={fog['partial_belief_frontiers']}  retained={fog['retained']}")
    print(f"SOURCE AUDIT (routing is a qf_* rule verdict; no Python path-search): {audit}")
    print(f"\nGATES: {json.dumps(gates, default=str, indent=1)}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
