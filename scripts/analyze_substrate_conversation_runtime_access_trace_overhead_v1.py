#!/usr/bin/env python3
"""Recompute paired conversation trace-overhead summaries from raw arms."""
from __future__ import annotations

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "evaluation/reports/substrate_conversation_runtime_access_trace_overhead_v1_20260925.json"
OUTPUT = ROOT / "evaluation/reports/substrate_conversation_runtime_access_trace_overhead_v1_analysis_20260925.json"
ARMS = ("plain", "scale_only", "trace_only", "both")


def main() -> None:
    raw = json.loads(SOURCE.read_text())
    checks = {"12_cells_48_runs": len(raw["cells"]) == 12,
              "runner_checks_all_pass": all(raw["checks"].values()),
              "paired_semantics_and_fixed_point": True,
              "instrumentation_arm_isolation": True,
              "timing_summary_recomputed": True}
    for cell in raw["cells"]:
        checks["paired_semantics_and_fixed_point"] &= cell["outcome_parity"]
        checks["instrumentation_arm_isolation"] &= (
            cell["arms"]["plain"]["event_total"] == 0
            and cell["arms"]["scale_only"]["event_total"] == 0
            and cell["arms"]["trace_only"]["event_total"] > 0
            and cell["arms"]["both"]["event_total"] > 0
            and not cell["arms"]["plain"]["scale_audit"]
            and bool(cell["arms"]["scale_only"]["scale_audit"])
            and not cell["arms"]["trace_only"]["scale_audit"]
            and bool(cell["arms"]["both"]["scale_audit"]))
    summaries = []
    for size in (1, 2):
        group = [c for c in raw["cells"] if c["size"] == size]
        arms = {}
        for arm in ARMS:
            wall = [c["arms"][arm]["wall_time_ns"] for c in group]
            cpu = [c["arms"][arm]["cpu_time_ns"] for c in group]
            recorded = raw_summary = next(s for s in raw["summaries"] if s["size"] == size)["arms"][arm]
            if int(statistics.median(wall)) != recorded["wall_median_ns"] or int(statistics.median(cpu)) != recorded["cpu_median_ns"]:
                checks["timing_summary_recomputed"] = False
            arms[arm] = {"wall_median_ns": int(statistics.median(wall)),
                         "wall_range_ns": [min(wall), max(wall)],
                         "cpu_median_ns": int(statistics.median(cpu)), "cpu_range_ns": [min(cpu), max(cpu)]}
        ratios = {}
        for num, den in (("trace_only", "plain"), ("scale_only", "plain"),
                         ("both", "scale_only"), ("both", "trace_only")):
            wr = [c["arms"][num]["wall_time_ns"] / max(1, c["arms"][den]["wall_time_ns"]) for c in group]
            cr = [c["arms"][num]["cpu_time_ns"] / max(1, c["arms"][den]["cpu_time_ns"]) for c in group]
            ratios[f"{num}_over_{den}"] = {"wall_paired_ratio_median": statistics.median(wr),
                                             "wall_paired_ratio_range": [min(wr), max(wr)],
                                             "cpu_paired_ratio_median": statistics.median(cr),
                                             "cpu_paired_ratio_range": [min(cr), max(cr)]}
        summaries.append({"size": size, "replicates": len(group), "arms": arms, "contrasts": ratios})
    result = {"schema_version": 1, "source": str(SOURCE.relative_to(ROOT)), "checks": checks,
              "all_checks_pass": all(checks.values()), "summaries": summaries,
              "claim_boundary": "Independent recomputation of a small one-host timing capture; descriptive only."}
    OUTPUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
