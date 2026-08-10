"""arc_ls20_planning_measure — RUNG 218000: ls20 PLANNING/EXECUTION.

Closes the ls20 loop see -> understand -> DO on offline ls20-shaped scenarios,
driven by the salience -> investigate -> act planner (graph rules,
domains/ls20_planning_seed.py). Measures, behind protected controls:

  G-solve            the curiosity-first planner SOLVES the scenario — routes the
                     CORRECTLY-TRANSFORMED symbol to the goal — at success >= T.
  G-vs-goal-blind    a GOAL-BLIND baseline (rushes the un-transformed symbol
                     straight to the goal) FAILS where curiosity-first SUCCEEDS,
                     CI-separated. THE load-bearing claim: goal blindness loses.
  G-investigation    a BLIND-DETOUR baseline (detours to a station without
                     recognising WHICH transform is needed) also loses on
                     multi-station scenarios -> INVESTIGATION, not mere detour,
                     is the lever. Plus the investigation TRACE for one exemplar.

Ground truth is by construction (the required transform, hence the winning
delivered shape, is known). HONEST SCOPE (standing rule — synthetic-proven !=
benchmark value, report both): these are ls20-SHAPED scenarios on the real ls20
palette, SEEN through the 216000 pixel eye; the recogniser is the GENERAL 217000
sd-loop. LIVE ls20 needs ARC_API_KEY (absent — the named frontier).

Run:  PYTHONPATH=runners/dsl/python:. python3 scripts/arc_ls20_planning_measure.py
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
for _p in (str(_ROOT), str(_ROOT / "scripts"), str(_ROOT / "runners" / "dsl" / "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from worlds.arc_ls20_scenario import make_scenario, run_episode  # noqa: E402
from domains.ls20_planning_seed import RULES  # noqa: E402

ARMS = ("curious", "blind", "detour")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - h) / d, (c + h) / d)


def measure_config(n, n_stations, seed):
    rng = np.random.default_rng(seed)
    wins = {a: 0 for a in ARMS}
    reasons = {a: {} for a in ARMS}
    for _ in range(n):
        scn = make_scenario(rng, n_stations=n_stations)
        for a in ARMS:
            res = run_episode(scn, a)
            wins[a] += int(res["win"])
            reasons[a][res["reason"]] = reasons[a].get(res["reason"], 0) + 1
    return {"n": n, "n_stations": n_stations,
            "wins": wins,
            "success": {a: wilson(wins[a], n) for a in ARMS},
            "reasons": reasons}


def investigation_trace(seed, n_stations=3):
    """One exemplar's salience -> investigate -> act trace (the curious arm)."""
    rng = np.random.default_rng(seed)
    scn = make_scenario(rng, n_stations=n_stations)
    res = run_episode(scn, "curious", trace=True)
    steps = res["trace"]
    orient = next((t for t in steps if t["affect"] == "surprise_orient"), None)
    used_station = next((t for i, t in enumerate(steps)
                         if i > 0 and steps[i - 1]["waypoint"] == "station"
                         and not steps[i - 1]["matches"] and t["matches"]), None)
    return {
        "scenario": {"symbol": scn["name"], "required_transform": scn["req_key"],
                     "station_keys": [s["key"] for s in scn["stations"]],
                     "avatar": scn["avatar_rc"], "goal": scn["goal_rc"]},
        "salience": ("mismatch symbol!=goal -> affect=surprise_orient at step "
                     f"{orient['step']}" if orient else "none"),
        "investigate": (f"recognised required transform = {res['req_key']} (217000 "
                        "sd-loop); sought the station whose key matches"),
        "discovered": (f"the matching station (key {res['req_key']}); applied it -> "
                       f"carried now matches the goal at step {used_station['step']}"
                       if used_station else "n/a"),
        "act": f"routed to the goal and delivered -> {'WIN' if res['win'] else 'LOSE'}",
        "won": res["win"], "steps": res["steps"],
    }


def source_audit():
    """G-graph-native: the planning rules name NO specific transform family and NO
    ls20 constant — the DECISION is generic over req_key / symbol_matches_goal."""
    blob = json.dumps(RULES).lower()
    banned = ["ls20", "rotation90", "reflection", "rot90", "recolour", "reflect", "rotate"]
    hits = [w for w in banned if w in blob]
    return {"rule_count": len(RULES), "banned_tokens_found": hits, "clean": not hits}


def check_gates(res1, res3, g_solve, g_sep_margin):
    """res1 = single-station config, res3 = 3-station config."""
    cur1 = res1["success"]["curious"]
    cur3 = res3["success"]["curious"]
    blind1, blind3 = res1["success"]["blind"], res3["success"]["blind"]
    det3 = res3["success"]["detour"]
    solve = min(cur1[0], cur3[0])
    # CI-separated: curious lower bound > baseline upper bound
    vs_blind = (cur1[1] > blind1[2]) and (cur3[1] > blind3[2])
    vs_detour = cur3[1] > det3[2]
    return {
        "G_solve": solve >= g_solve,
        "G_vs_goal_blind": vs_blind,
        "G_investigation_not_detour": vs_detour,
        "solve_min_success": solve,
        "curious_1station": cur1, "curious_3station": cur3,
        "blind_1station": blind1, "blind_3station": blind3, "detour_3station": det3,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=100)
    ap.add_argument("--seed", type=int, default=218000)
    ap.add_argument("--tag", default="first")
    ap.add_argument("--g-solve", type=float, default=0.0)
    ap.add_argument("--g-sep-margin", type=float, default=0.0)
    args = ap.parse_args()

    res1 = measure_config(args.n, 1, args.seed)
    res3 = measure_config(args.n, 3, args.seed + 1)
    # reproduction check (determinism): same seed -> same wins
    rep = measure_config(min(args.n, 20), 3, args.seed + 1)
    repro_ok = all(rep["wins"][a] == measure_config(min(args.n, 20), 3, args.seed + 1)["wins"][a]
                   for a in ARMS)
    trace = investigation_trace(args.seed + 7)
    audit = source_audit()
    gates = check_gates(res1, res3, args.g_solve, args.g_sep_margin)

    result = {
        "rung": 218000, "tag": args.tag, "seed": args.seed, "n": args.n,
        "commitment": "salience->investigate->act planner (graph rules) SOLVES ls20-shaped "
                      "scenarios by recognising the required transform (217000) and routing the "
                      "correctly-transformed symbol to the goal; GOAL-BLIND loses.",
        "single_station": res1, "three_station": res3,
        "reproduction_deterministic": repro_ok,
        "investigation_trace": trace,
        "source_audit": audit,
        "gates": gates,
        "note": "ls20-SHAPED offline scenarios on the real ls20 palette, SEEN through the 216000 "
                "pixel eye; recogniser = the GENERAL 217000 sd-loop; integer-native exact-equality "
                "verdict at the goal. LIVE ls20 needs ARC_API_KEY (absent — the named frontier).",
    }
    out = _ROOT / "results" / f"arc_ls20_planning_{args.tag}.json"
    out.parent.mkdir(exist_ok=True)
    out.write_text(json.dumps(result, indent=2, default=str))

    def fmt(ci):
        return f"{ci[0]:.4f} [{ci[1]:.4f}, {ci[2]:.4f}]"

    print("=== RUNG 218000 — ls20 PLANNING/EXECUTION (salience->investigate->act) ===")
    for res in (res1, res3):
        print(f"\n{res['n_stations']}-STATION  N={res['n']}")
        for a in ARMS:
            print(f"  {a:8s} success={fmt(res['success'][a])}  reasons={res['reasons'][a]}")
    print(f"\nreproduction deterministic: {repro_ok}")
    print(f"source audit (rules graph-native, no transform/ls20 token): {audit}")
    print("\nINVESTIGATION TRACE (curious exemplar):")
    for k in ("scenario", "salience", "investigate", "discovered", "act", "won"):
        print(f"  {k:12s}: {trace[k]}")
    print(f"\nGATES: {json.dumps(gates, default=str, indent=1)}")
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main()
