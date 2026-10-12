#!/usr/bin/env python3
"""Independent scoring for the ls20 current-source scale panel v1.2."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import statistics
from collections import deque
from pathlib import Path

from scipy.stats import binomtest

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/ls20_mapnav_current_source_scale_v1_2/capture.json"
LOCK = ROOT / "evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_2_lock_20260928.json"
RUNNER_PATH = ROOT / "evaluation/substrate_capability/ls20_mapnav_current_source_scale_v1_2.py"
OUT = ROOT / "evaluation/reports/ls20_mapnav_current_source_scale_v1_2_independent_analysis.json"


def normalized(cells):
    rows = [int(x[0]) for x in cells]; cols = [int(x[1]) for x in cells]
    if not cells:
        return frozenset()
    mr, mc = min(rows), min(cols)
    return frozenset((int(r) - mr, int(c) - mc, int(v)) for r, c, v in cells)


def transform(cells, family, param):
    out = [(int(r), int(c), int(v)) for r, c, v in cells]
    if family == "rotate":
        for _ in range(int(param)):
            out = [(c, -r, v) for r, c, v in out]
    elif family == "reflect":
        out = [(r, -c if param == "c" else c, v) if param == "c" else (-r, c, v) for r, c, v in out]
    elif family == "recolour":
        cmap = {int(k): int(v) for k, v in param.items()}
        out = [(r, c, cmap.get(v, v)) for r, c, v in out]
    else:
        raise ValueError(f"unknown transform family: {family}")
    return normalized(out)


def transform_key(family, param):
    if family == "rotate":
        return f"rot90:{int(param)}"
    if family == "reflect":
        return f"refl:{param}"
    pairs = sorted(f"v{int(a)}>v{int(b)}" for a, b in param.items() if int(a) != int(b))
    return "recolour:" + ",".join(pairs)


def shortest_distance(start, goal, h, w, walls):
    start, goal = tuple(start), tuple(goal)
    if start == goal:
        return 0
    q = deque([(start, 0)]); seen = {start}
    while q:
        (r, c), d = q.popleft()
        for nxt in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if not (0 <= nxt[0] < h and 0 <= nxt[1] < w) or nxt in walls or nxt in seen:
                continue
            if nxt == goal:
                return d + 1
            seen.add(nxt); q.append((nxt, d + 1))
    return None


def wilson(k, n, z=1.959963984540054):
    p = k / n; d = 1 + z*z/n
    center = (p + z*z/(2*n)) / d
    half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return [center - half, center + half]


def quantile_range(values):
    vals = sorted(float(x) for x in values)
    return {"median": statistics.median(vals), "min": vals[0], "max": vals[-1]}


def main():
    capture = json.loads(CAPTURE.read_text()); locked = json.loads(LOCK.read_text())
    spec = importlib.util.spec_from_file_location("mapnav_runner_v1_2", RUNNER_PATH)
    if not spec or not spec.loader:
        raise RuntimeError("cannot import lock verifier")
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    live_lock = runner.input_lock()
    lock_stable = locked == capture.get("locked_inputs") == capture.get("post_run_inputs") == live_lock
    cells_out = {}; all_rows = 0; oracle_failures = []; key_mismatch = []
    all_scenario_hashes = []
    open_parity_n = open_parity_pass = 0
    gates = {"capture_complete": capture.get("capture_status") == "complete",
             "source_build_lock_stable": lock_stable,
             "native_extension_fresh": not locked.get("native_build_stale_reasons"),
             "all_150_world_oracles_pass": True,
             "all_route_targets_reachable": True,
             "open_win_and_step_parity": True}
    for cell in capture.get("cells", []):
        params = cell["parameters"]; records = cell["records"]; n = len(records)
        agg = {r: {"correct": 0, "wins": [], "steps": [], "wall": [], "cpu": [], "reasons": {}} for r in ("greedy", "quanta")}
        fixed = broken = 0; oracle_ok = route_ok = True; qkey_ok = 0
        for row in records:
            scenario = row["scenario"]; all_rows += 1
            digest = hashlib.sha256(json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            all_scenario_hashes.append(digest)
            req = transform_key(scenario["family"], scenario["param"])
            matching = [s for s in scenario["stations"] if s["key"] == req]
            shape_ok = transform(scenario["symbol_cells"], scenario["family"], scenario["param"]) == normalized(scenario["goal_cells"])
            station_ok = len(matching) == 1 and matching[0]["family"] == scenario["family"] and matching[0]["param"] == scenario["param"]
            if not (shape_ok and station_ok):
                oracle_ok = False; oracle_failures.append({"cell": params["name"], "episode": row["episode_index"], "shape_ok": shape_ok, "station_ok": station_ok})
            h, w = int(params["h"]), int(params["w"]); walls = {tuple(x) for x in scenario.get("walls", [])}
            targets = [tuple(scenario["goal_rc"])] + [(int(s["r"]), int(s["c"])) for s in scenario["stations"]]
            distances = [shortest_distance(scenario["avatar_rc"], t, h, w, walls) for t in targets]
            if any(d is None for d in distances):
                route_ok = False
            pair = row["pair"]["outcomes"]
            for router in ("greedy", "quanta"):
                item = pair[router]; result = item["result"]
                win = bool(result["win"]); consistent = win == (result["reason"] == "delivered")
                if not consistent:
                    oracle_ok = False
                if router == "quanta" and result.get("req_key") == req:
                    qkey_ok += 1
                agg[router]["correct"] += int(win); agg[router]["wins"].append(win)
                agg[router]["steps"].append(int(result["steps"]))
                agg[router]["wall"].append(item["wall_seconds"]); agg[router]["cpu"].append(item["cpu_seconds"])
                agg[router]["reasons"][result["reason"]] = agg[router]["reasons"].get(result["reason"], 0) + 1
            g = pair["greedy"]["result"]; q = pair["quanta"]["result"]
            fixed += int(bool(q["win"]) and not bool(g["win"]))
            broken += int(bool(g["win"]) and not bool(q["win"]))
            if params["name"] == "open_16_1":
                open_parity_n += 1
                same = bool(g["win"]) == bool(q["win"]) and int(g["steps"]) == int(q["steps"])
                open_parity_pass += int(same)
                gates["open_win_and_step_parity"] = gates["open_win_and_step_parity"] and same
        gates["all_150_world_oracles_pass"] = gates["all_150_world_oracles_pass"] and oracle_ok
        gates["all_route_targets_reachable"] = gates["all_route_targets_reachable"] and route_ok
        exact_p = float(binomtest(fixed, fixed + broken, p=0.5, alternative="two-sided").pvalue) if fixed + broken else 1.0
        stats = {}
        for router in ("greedy", "quanta"):
            a = agg[router]
            stats[router] = {"successes": a["correct"], "accuracy": a["correct"] / n,
                             "wilson_95": wilson(a["correct"], n), "reasons": a["reasons"],
                             "steps_median": statistics.median(a["steps"]),
                             "wall_seconds": quantile_range(a["wall"]), "cpu_seconds": quantile_range(a["cpu"])}
        cell_gate = True
        if params["walls"]:
            cell_gate = (agg["quanta"]["correct"] >= 27 and
                         wilson(agg["quanta"]["correct"], n)[0] > wilson(agg["greedy"]["correct"], n)[1])
        cells_out[params["name"]] = {"parameters": params, "n": n, "quanta_recognized_key": {"correct": qkey_ok, "total": n},
                                      "shortest_route_distances": {"goal_and_stations": "independently BFS-recomputed per episode", "all_reachable": route_ok,
                                                                   "median_to_goal": statistics.median([shortest_distance(r["scenario"]["avatar_rc"], r["scenario"]["goal_rc"], int(params["h"]), int(params["w"]), {tuple(x) for x in r["scenario"].get("walls", [])}) for r in records])},
                                      "arms": stats, "paired": {"quanta_fixed": fixed, "quanta_broken": broken, "exact_mcnemar_two_sided_p": exact_p},
                                      "walled_cell_gate": cell_gate if params["walls"] else None,
                                      "oracle_valid": oracle_ok}
    gates["all_150_world_oracles_pass"] = gates["all_150_world_oracles_pass"] and all_rows == 150 and len(set(all_scenario_hashes)) == 150
    gates["open_win_and_step_parity"] = gates["open_win_and_step_parity"] and open_parity_n == 30 and open_parity_pass == 30
    walled_gates = [v["walled_cell_gate"] for v in cells_out.values() if v["walled_cell_gate"] is not None]
    gates["all_four_walled_cell_gates"] = len(walled_gates) == 4 and all(walled_gates)
    gates["all_confirmatory_gates_pass"] = all(gates.values())
    process = capture.get("process", {})
    report = {"schema_version": 1, "run_id": capture.get("run_id"),
              "analysis_method": "independent transform/station reconstruction, grid BFS, paired row scoring, Wilson intervals, exact binomial McNemar; benchmark aggregate reporter not called",
              "n_scenarios": all_rows, "unique_scenario_sha256": len(set(all_scenario_hashes)),
              "cells": cells_out, "open_control": {"n": open_parity_n, "same_win_and_steps": open_parity_pass},
              "integrity_gates": gates,
              "process": process, "max_rss_kib": process.get("max_rss_kib"),
              "exploratory_scale_ratios": {
                  "quanta_wall_32x16_1station": cells_out["walled_32_1"]["arms"]["quanta"]["wall_seconds"]["median"] / cells_out["walled_16_1"]["arms"]["quanta"]["wall_seconds"]["median"],
                  "quanta_wall_32x16_3station": cells_out["walled_32_3"]["arms"]["quanta"]["wall_seconds"]["median"] / cells_out["walled_16_3"]["arms"]["quanta"]["wall_seconds"]["median"],
              },
              "oracle_failures": oracle_failures,
              "capture_limitation": "Canonical scenario digests are independently derived from the fully recorded worlds during analysis; the runner did not persist per-scenario digests at execution time.",
              "claim_boundary": capture.get("claim_boundary")}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "gates": gates,
                      "cells": {k: {"greedy": v["arms"]["greedy"]["successes"], "quanta": v["arms"]["quanta"]["successes"],
                                    "paired": v["paired"], "quanta_wall_median": v["arms"]["quanta"]["wall_seconds"]["median"]} for k,v in cells_out.items()},
                      "process_max_rss_kib": report["max_rss_kib"]}, indent=2))
    if not gates["all_confirmatory_gates_pass"]:
        raise SystemExit("independent confirmatory gate failure")


if __name__ == "__main__":
    main()
