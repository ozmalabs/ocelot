#!/usr/bin/env python3
"""Deterministic summary/checks for the retained RatioInduce v1.2 pilot raw."""
from __future__ import annotations

import hashlib
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_ratioinduce_cost_pilot_v1_2_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_ratioinduce_cost_pilot_v1_2_analysis_20260926.json"


def percentile(values: list[int], q: float) -> int:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    raw = json.loads(RAW.read_text())
    cells = raw["cells"]
    checks = {
        "all_11_cells_present": len(cells) == 11,
        "all_cells_pass_semantics_and_checked_count": all(c["success"] for c in cells),
        "seven_wall_and_cpu_samples_each": all(len(c["wall_time_ns"]) == 7 and len(c["cpu_time_ns"]) == 7 for c in cells),
        "no_failed_cells_in_raw": not raw["failed_cells"],
    }
    summaries = []
    for cell in cells:
        wall = [int(x) for x in cell["wall_time_ns"]]
        cpu = [int(x) for x in cell["cpu_time_ns"]]
        summaries.append({
            "factor": cell["factor"], "level": cell["level"],
            "frames": cell["frames"], "relations_per_frame": cell["relations_per_frame"],
            "coord_dimensions": cell["coord_dimensions"],
            "input_relations": cell["input_relations"],
            "median_wall_time_ns": int(statistics.median(wall)),
            "p90_wall_time_ns": percentile(wall, .90),
            "median_cpu_time_ns": int(statistics.median(cpu)),
            "p90_cpu_time_ns": percentile(cpu, .90),
            "observed_checked": cell["observed_checked"],
            "success": cell["success"],
        })
    ratios = {}
    for factor in ("frames", "relations_per_frame", "coord_dimensions"):
        group = [x for x in summaries if x["factor"] == factor]
        ratios[factor] = {
            "input_relations_ratio_last_over_first": group[-1]["input_relations"] / group[0]["input_relations"],
            "median_wall_ratio_last_over_first": group[-1]["median_wall_time_ns"] / group[0]["median_wall_time_ns"],
        }
    result = {
        "analysis_version": 1,
        "run_id": raw["run_id"],
        "raw_sha256": sha(RAW),
        "checks": checks,
        "checks_pass": all(checks.values()),
        "summaries": summaries,
        "sweep_ratios": ratios,
        "interpretation": (
            "For these positive fixtures, direct-call medians grow roughly with total input relations across the frame and point sweeps. "
            "This is descriptive pilot evidence only; dimensions span only 2-4 and the family is exact/common-ratio."
        ),
        "claim_boundary": raw["claim_boundary"],
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"run_id": result["run_id"], "checks_pass": result["checks_pass"],
                      "sweep_ratios": ratios, "output": str(OUT)}, indent=2))
    return 0 if result["checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
