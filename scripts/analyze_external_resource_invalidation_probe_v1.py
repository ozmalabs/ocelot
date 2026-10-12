#!/usr/bin/env python3
"""Independent integrity and behavior summary for resource invalidation probe v1."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/external_resource_invalidation_probe_v1_20260928.json"
OUT = ROOT / "evaluation/reports/external_resource_invalidation_probe_v1_analysis_20260928.json"
PHASES = ["A_false_initial", "B_resource_only_flip_true", "C_resource_false_plus_new_graph_match"]


def main() -> None:
    d = json.loads(RAW.read_text())
    runs = d["runs"]
    inputs = [r["started_inputs"] for r in runs]
    gates = {
        "three_workers": len(runs) == 3,
        "source_native_lock_stable": all(v == d["locked_inputs"] for v in inputs),
        "phase_shape_complete": all([p["phase"] for p in r["phases"]] == PHASES for r in runs),
        "resource_values_correct": all([p["resource_value"] for p in r["phases"]] == ["0", "1", "0"] for r in runs),
        "static_use_tool_wildcard": all(r["static_access"]["reads_any"] for r in runs),
    }
    normalized = []
    for r in runs:
        normalized.append([
            {k: p[k] for k in ("resource_value", "progress", "callback_log", "callback_count", "native_fire_delta", "accepted_targets")}
            for p in r["phases"]
        ])
    gates["identical_worker_behavior"] = normalized[0] == normalized[1] == normalized[2]
    gates["phase_a_reads_false"] = all(r["phases"][0]["callback_log"] and all(x["value"] == "0" for x in r["phases"][0]["callback_log"]) and r["phases"][0]["accepted_targets"] == [False] for r in runs)
    gates["phase_b_records_resource_only_response"] = all(
        r["phases"][1]["callback_log"] == [] or all(x["value"] == "1" for x in r["phases"][1]["callback_log"])
        for r in runs
    )
    gates["phase_c_new_match_reads_current_false"] = all(
        all(x["value"] == "0" for x in r["phases"][2]["callback_log"])
        and r["phases"][2]["accepted_targets"] in ([False, False], [True, False])
        for r in runs
    )
    summary = {
        "analysis": "External resource invalidation probe v1",
        "all_integrity_gates_pass": all(gates.values()), "gates": gates,
        "behavior_by_phase": [
            {"phase": name, "callback_counts": [r["phases"][i]["callback_count"] for r in runs],
             "progress": [r["phases"][i]["progress"] for r in runs],
             "accepted_targets": [r["phases"][i]["accepted_targets"] for r in runs],
             "resource_returns": [[x["value"] for x in r["phases"][i]["callback_log"]] for r in runs]}
            for i, name in enumerate(PHASES)
        ],
        "interpretation": "Phase B is the direct resource-only invalidation observation. Phase C shows current resource values for graph-triggered new matches. Previously committed graph effects are monotonic and are not expected to retract when external state changes.",
    }
    OUT.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_integrity_gates_pass": summary["all_integrity_gates_pass"], "gates": gates,
                      "behavior_by_phase": summary["behavior_by_phase"], "analysis": str(OUT.relative_to(ROOT))}, indent=2))
    if not summary["all_integrity_gates_pass"]:
        raise SystemExit("probe analysis gate failed")


if __name__ == "__main__":
    main()
