#!/usr/bin/env python3
"""Independent integrity and outcome summary for generated-pool CEGIS comparison."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEM = "substrate_generated_pool_cegis_comparison_v1_5_20261001"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
OUT = ROOT / f"evaluation/reports/{STEM}_analysis.json"
EXPECTED_TASKS = ("triangular", "square", "euler")
EXPECTED_ARMS = ("mdl_cegis", "entropy_pool", "first_pool", "random_pool")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if not RAW.is_file():
        raise SystemExit(f"missing capture: {RAW}")
    capture = json.loads(RAW.read_text())
    checks = []
    checks.append(("schema", capture.get("schema") == "GeneratedPoolCegisComparisonV1"))
    lock = capture["lock"]
    stale = []
    for relative, expected in lock["sources"].items():
        path = ROOT / relative
        if not path.is_file() or digest(path) != expected:
            stale.append(relative)
    checks.append(("source_hashes_current", not stale))
    binary = Path(lock["native_extension"]["path"])
    checks.append(("native_binary_hash_current", binary.is_file() and digest(binary) == lock["native_extension"]["sha256"]))
    checks.append(("all_scheduled_workers_returned", capture.get("capture_complete") is True))

    rows = capture.get("comparisons", [])
    keyed = {(row.get("task"), row.get("arm"), row.get("replicate")): row for row in rows}
    expected_keys = {(task, arm, rep) for task in EXPECTED_TASKS
                      for arm in EXPECTED_ARMS for rep in range(5)}
    checks.append(("all_task_arm_rows_present", set(keyed) == expected_keys))
    summaries = []
    for task in EXPECTED_TASKS:
        for arm in EXPECTED_ARMS:
          for replicate in range(5):
            row = keyed.get((task, arm, replicate), {})
            if "worker_error" in row:
                continue
            qlog = row.get("query_log", [])
            qnames = [item["name"] for item in qlog]
            if arm != "mdl_cegis":
                checks.append((f"{task}_{arm}_queries_unique", len(qnames) == len(set(qnames))))
            checks.append((f"{task}_{arm}_query_survivor_contract",
                           all(item.get("survivors_after", 0) <= item.get("survivors_before", 0)
                               for item in qlog if "survivors_before" in item)))
            if arm == "mdl_cegis":
                heldout_ok = row.get("heldout_exact") is True
                checks.append((f"{task}_{arm}_converged", row.get("converged") is True))
                pool_complete = None
                target_supported = None
                stop_reason = row.get("stop_reason")
                survivor_count = None
            else:
                pool_complete = row.get("pool_complete") is True
                target_supported = row.get("target_supported_on_heldout") is True
                heldout_ok = row.get("heldout_exact") is True
                stop_reason = row.get("stop_reason")
                survivor_count = row.get("final_survivor_count")
                if pool_complete:
                    checks.append((f"{task}_{arm}_complete_pool_reason",
                                   row.get("pool_halt_reason") == "max_size"))
                    if target_supported:
                        checks.append((f"{task}_{arm}_supported_target_survives",
                                       row.get("heldout_exact") is True))
            counters = row.get("counters", {})
            algorithm_wall = sum(counters.get(key, 0.0) for key in
                                 ("synthesis_wall_s", "selection_wall_s", "oracle_wall_s"))
            summaries.append({
                "task": task, "arm": arm, "replicate": replicate, "stop_reason": stop_reason,
                "heldout_exact": heldout_ok, "complete_pool": pool_complete,
                "target_supported": target_supported, "pool_size": row.get("pool_size"),
                "queries": len(qlog), "oracle_calls": counters.get("oracle_calls"),
                "oracle_wall_s": counters.get("oracle_wall_s"),
                "terms_explored": counters.get("terms_explored"),
                "synthesis_wall_s": counters.get("synthesis_wall_s"),
                "selection_wall_s": counters.get("selection_wall_s"),
                "evaluation_wall_s": counters.get("evaluation_wall_s"),
                "algorithm_wall_s": algorithm_wall,
                "index_heap_estimate_bytes": row.get("index_heap_estimate_bytes"),
                "worker_wall_s": row.get("worker_wall_s"),
                "task_setup_wall_s": row.get("task_setup_wall_s"),
                "parent_subprocess_wall_s": row.get("parent_subprocess_wall_s"),
                "final_survivor_count": survivor_count,
            })
    passed = sum(ok for _, ok in checks)
    analysis = {
        "schema": "GeneratedPoolCegisComparisonAnalysisV1",
        "capture": str(RAW.relative_to(ROOT)),
        "capture_sha256": digest(RAW),
        "check_count": len(checks), "checks_passed": passed,
        "all_checks_pass": passed == len(checks),
        "failed_checks": [name for name, ok in checks if not ok],
        "stale_sources": stale,
        "rows": summaries,
        "arm_medians_by_task": {},
    }
    for task in EXPECTED_TASKS:
        analysis["arm_medians_by_task"][task] = {}
        for arm in EXPECTED_ARMS:
            group = [row for row in summaries if row["task"] == task and row["arm"] == arm]
            if not group:
                continue
            vals = [r["algorithm_wall_s"] for r in group
                    if isinstance(r.get("algorithm_wall_s"), (int, float))]
            analysis["arm_medians_by_task"][task][arm] = {
                "algorithm_wall_s": statistics.median(vals) if vals else None,
                "parent_process_wall_s": statistics.median(
                    [r["parent_subprocess_wall_s"] for r in group
                     if isinstance(r.get("parent_subprocess_wall_s"), (int, float))])
                    if any(isinstance(r.get("parent_subprocess_wall_s"), (int, float)) for r in group) else None,
                "all_heldout_exact": all(r["heldout_exact"] for r in group),
                "queries_by_replicate": [r["queries"] for r in sorted(group, key=lambda x: x["replicate"])],
                "oracle_calls_by_replicate": [r["oracle_calls"] for r in sorted(group, key=lambda x: x["replicate"])],
                "paired_mdl_to_arm_algorithm_ratios": [],
            }
    for task in EXPECTED_TASKS:
        baseline = {row["replicate"]: row["algorithm_wall_s"]
                    for row in summaries if row["task"] == task and row["arm"] == "mdl_cegis"}
        for arm in EXPECTED_ARMS:
            if arm == "mdl_cegis":
                continue
            group = [row for row in summaries if row["task"] == task and row["arm"] == arm]
            ratios = [baseline[row["replicate"]] / row["algorithm_wall_s"]
                      for row in group if row["algorithm_wall_s"] and baseline.get(row["replicate"])]
            analysis["arm_medians_by_task"][task][arm]["paired_mdl_to_arm_algorithm_ratios"] = ratios
            analysis["arm_medians_by_task"][task][arm]["median_mdl_to_arm_ratio"] = (
                statistics.median(ratios) if ratios else None)
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
                      "check_count": len(checks), "checks_passed": passed,
                      "all_checks_pass": analysis["all_checks_pass"],
                      "failed_checks": analysis["failed_checks"],
                      "arm_medians_by_task": analysis["arm_medians_by_task"]}, indent=2))
    if not analysis["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
