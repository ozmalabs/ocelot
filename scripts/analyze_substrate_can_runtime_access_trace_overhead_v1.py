#!/usr/bin/env python3
"""Independent arithmetic/gate audit for CAN access-trace overhead v1.1."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_can_runtime_access_trace_overhead_v1_1_20260925.json"
OUT = ROOT / "evaluation/reports/substrate_can_runtime_access_trace_overhead_v1_1_analysis_20260925.json"
ARMS = ("plain", "scale_only", "trace_only", "both")
COMPARISONS = {
    "trace_only_over_plain": ("trace_only", "plain"),
    "scale_only_over_plain": ("scale_only", "plain"),
    "both_over_scale_only": ("both", "scale_only"),
    "both_over_trace_only": ("both", "trace_only"),
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values):
    return statistics.median(values)


def main() -> None:
    raw = json.loads(RAW.read_text())
    groups = []
    valid = all(raw["checks"].values()) and len(raw["cells"]) == 48
    for n, topology, mode in ((n, topology, mode)
                              for n in (8, 16)
                              for topology in ("path", "complete")
                              for mode in ("2state", "3state")):
        cells = [row for row in raw["cells"]
                 if (row["n"], row["topology"], row["mode"]) == (n, topology, mode)]
        if len(cells) != 6 or len({row["replicate"] for row in cells}) != 6:
            valid = False
        arm_stats = {}
        for arm in ARMS:
            for measure in ("wall_time_ns", "cpu_time_ns"):
                values = [int(row["arms"][arm][measure]) for row in cells]
                arm_stats.setdefault(arm, {})[measure] = {
                    "median": int(median(values)), "min": min(values), "max": max(values), "values": values,
                }
        comparisons = {}
        for name, (numerator, denominator) in COMPARISONS.items():
            comparisons[name] = {}
            for measure in ("wall_time_ns", "cpu_time_ns"):
                ratios = [row["arms"][numerator][measure] / max(1, row["arms"][denominator][measure])
                          for row in cells]
                differences = [row["arms"][numerator][measure] - row["arms"][denominator][measure]
                               for row in cells]
                comparisons[name][measure] = {
                    "paired_ratio_median": median(ratios), "paired_ratio_min": min(ratios),
                    "paired_ratio_max": max(ratios), "paired_ratios": ratios,
                    "paired_difference_median": int(median(differences)),
                    "paired_difference_min": min(differences), "paired_difference_max": max(differences),
                    "paired_differences": differences,
                }
        groups.append({"n": n, "topology": topology, "mode": mode,
                       "replicates": len(cells), "arms": arm_stats, "comparisons": comparisons})
    # Confirm the runner's own summary uses the preregistered median of
    # within-instance paired ratios and exact paired differences.
    summary_checks = []
    for group in groups:
        runner_summary = next(row for row in raw["summaries"] if
                              (row["n"], row["topology"], row["mode"]) ==
                              (group["n"], group["topology"], group["mode"]))
        for name in COMPARISONS:
            for measure in ("wall_time_ns", "cpu_time_ns"):
                key = "wall" if measure == "wall_time_ns" else "cpu"
                actual = group["comparisons"][name][measure]
                recorded = runner_summary["ratios"][name]
                summary_checks.append(
                    abs(actual["paired_ratio_median"] - recorded[f"{key}_paired_ratio_median"]) < 1e-12
                    and actual["paired_differences"] == recorded[f"{key}_paired_differences_ns"]
                )
    valid = valid and all(summary_checks)
    report = {
        "schema_version": 1, "raw_sha256": sha(RAW),
        "independent_checks_pass": valid,
        "check_summary": {"48_instance_rows": len(raw["cells"]) == 48,
                          "six_unique_replicates_per_cell": all(group["replicates"] == 6 for group in groups),
                          "all_registered_runner_gates_pass": all(raw["checks"].values()),
                          "paired_ratio_and_difference_arithmetic_matches_raw": all(summary_checks)},
        "groups": groups,
        "claim_boundary": raw["claim_boundary"],
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"independent_checks_pass": valid, "groups": len(groups), "output": str(OUT)}, indent=2))
    if not valid:
        raise SystemExit("overhead report audit failed")


if __name__ == "__main__":
    main()
