#!/usr/bin/env python3
"""Fail-closed analyzer for the residual-adoption v1 capture."""
from __future__ import annotations

import json, statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/thoughtexperiment_residual_adoption_v1.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_residual_adoption_v1_analysis.json"

def main() -> int:
    capture = json.loads(RAW.read_text())
    rows = capture["workers"]
    checks = {
        "worker_count": len(rows) == 15,
        "unique_worker_processes": len({row["worker_pid"] for row in rows}) == 15,
        "size_repeats": all(sum(row["size"] == size for row in rows) == 5 for size in (0, 10000, 50000)),
        "nonempty_full_receipts": all(
            all(row["arms"]["adopt"]["receipt_counts"].get(key, 0) > 0 for key in
                ("nodes_added", "nodes_removed", "nodes_changed", "edges_added", "edges_removed"))
            for row in rows),
        "branch_isolation": all(row["arms"]["adopt"]["primary_unchanged_before_apply"] for row in rows),
        "exact_adoption": all(row["arms"]["adopt"]["full_primary_parity"] for row in rows),
        "stale_rejected": all(
            "stale experiment revision" in (row["arms"]["stale_reject"]["error"] or "")
            and row["arms"]["stale_reject"]["unchanged_at_rejection"] for row in rows),
        "conflict_rejected": all(
            "before-image" in (row["arms"]["conflict_reject"]["error"] or "")
            and row["arms"]["conflict_reject"]["unchanged_at_rejection"] for row in rows),
        "source_hashes_present": bool(capture.get("source_sha256")) and bool(capture.get("binary", {}).get("sha256")),
    }
    by_size = {}
    for size in (0, 10000, 50000):
        subset = [row for row in rows if row["size"] == size]
        by_size[str(size)] = {
            "adoption_ms_median": statistics.median(row["arms"]["adopt"]["apply_ms"] for row in subset),
            "stale_reject_ms_median": statistics.median(row["arms"]["stale_reject"]["reject_ms"] for row in subset),
            "conflict_reject_ms_median": statistics.median(row["arms"]["conflict_reject"]["reject_ms"] for row in subset),
        }
    analysis = {"schema": "ThoughtexperimentResidualAdoptionAnalysisV1", "checks": checks,
                "passed": sum(checks.values()), "total": len(checks), "by_size": by_size,
                "interpretation": "One authored productive graph-diff family; timings are descriptive, not asymptotic evidence.",
                "capture": str(RAW.relative_to(ROOT))}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(f"residual adoption gates: {analysis['passed']}/{analysis['total']}")
    for key, value in checks.items():
        print(f"  {'PASS' if value else 'FAIL'} {key}")
    for size, value in by_size.items():
        print(f"  N={size}: adopt={value['adoption_ms_median']:.3f} ms; "
              f"stale={value['stale_reject_ms_median']:.3f} ms; "
              f"conflict={value['conflict_reject_ms_median']:.3f} ms")
    return 0 if all(checks.values()) else 1

if __name__ == "__main__":
    raise SystemExit(main())
