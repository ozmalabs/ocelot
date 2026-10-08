#!/usr/bin/env python3
"""Validate paired eager/streaming generator probe and summarize cost."""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STEM = "substrate_generator_streaming_probe_v1_20261001"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
OUT = ROOT / f"evaluation/reports/{STEM}_analysis.json"


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def median(rows, arm, field):
    return statistics.median(row["arms"][arm][field] for row in rows)


def main() -> None:
    capture = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    current = {name: digest(ROOT / name) for name in lock["sources"]}
    native = Path(lock["native_extension"]["path"])
    source_gate = current == lock["sources"] and digest(native) == lock["native_extension"]["sha256"]
    rows = capture["comparisons"]
    schedule = [tuple(item) for item in capture["schedule"]]
    observed = [(row["task"], row["max_size"], row["probe_count"], row["replicate"]) for row in rows]
    coverage_gate = len(rows) == 120 and sorted(observed) == sorted(schedule) and len(set(observed)) == 120
    comparisons = []
    for row in rows:
        eager, stream = row["arms"]["eager"], row["arms"]["streaming"]
        same = all(eager[key] == stream[key] for key in (
            "halt_reason", "pool_size", "terms_explored", "distinct_signatures",
            "signatures", "target_support_count"))
        comparisons.append({**{key: row[key] for key in ("task", "max_size", "probe_count", "replicate")},
                            "semantic_parity": same,
                            "wall_ratio_eager_over_streaming": eager["wall_s"] / stream["wall_s"] if stream["wall_s"] else None,
                            "python_peak_ratio_eager_over_streaming": eager["python_peak_bytes"] / stream["python_peak_bytes"] if stream["python_peak_bytes"] else None})
    parity_gate = all(item["semantic_parity"] for item in comparisons)
    summaries = []
    for task in ("triangular", "square", "euler"):
        for size in sorted({row["max_size"] for row in rows if row["task"] == task}):
            subset = [row for row in rows if row["task"] == task and row["max_size"] == size]
            summaries.append({"task": task, "max_size": size,
                              "cells": len(subset),
                              "parity_count": sum(item["semantic_parity"] for item in comparisons
                                                   if item["task"] == task and item["max_size"] == size),
                              "median_eager_wall_s": median(subset, "eager", "wall_s"),
                              "median_streaming_wall_s": median(subset, "streaming", "wall_s"),
                              "median_wall_ratio_eager_over_streaming": statistics.median(
                                  item["wall_ratio_eager_over_streaming"] for item in comparisons
                                  if item["task"] == task and item["max_size"] == size),
                              "median_eager_python_peak_bytes": median(subset, "eager", "python_peak_bytes"),
                              "median_streaming_python_peak_bytes": median(subset, "streaming", "python_peak_bytes")})
    result = {"all_checks_pass": source_gate and coverage_gate and parity_gate,
              "gates": {"sources_current": source_gate, "paired_schedule_coverage": coverage_gate,
                        "exact_pool_semantic_parity": parity_gate},
              "cell_count": len(rows), "parity_failures": [item for item in comparisons if not item["semantic_parity"]],
              "summaries": summaries, "paired_cells": comparisons,
              "capture_sha256": digest(RAW)}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
                      "all_checks_pass": result["all_checks_pass"],
                      "gates": result["gates"], "parity_failures": len(result["parity_failures"])}, indent=2))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
