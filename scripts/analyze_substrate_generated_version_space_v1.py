#!/usr/bin/env python3
"""Validate and summarize the generated-version-space pilot capture."""
from __future__ import annotations

import json
import hashlib
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_generated_version_space_v1_20260930_raw.json"
OUT = ROOT / "evaluation/reports/substrate_generated_version_space_v1_20260930_analysis.json"
LOCK = ROOT / "evaluation/substrate_capability/substrate_generated_version_space_v1_20260930_lock.json"


def main() -> int:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    checks = []

    def check(name, condition, detail=None):
        checks.append({"name": name, "ok": bool(condition), "detail": detail})

    anchors = raw.get("anchors", [])
    check("five_preregistered_anchors", [a.get("anchor") for a in anchors] == [6, 7, 8, 9, 10])
    check("no_worker_failures", not raw.get("worker_failures"))
    check("capture_matches_saved_lock", raw.get("lock") == lock)
    for anchor in anchors:
        gen = anchor["generation"]
        check(f"anchor_{anchor['anchor']}_bounded_pool_complete",
              gen["bounded_pool_complete"] and gen["halt_reason"] == "max_size",
              {"halt_reason": gen["halt_reason"], "pool_size": gen["pool_size"]})
        check(f"anchor_{anchor['anchor']}_has_heldout_correct_hypothesis",
              anchor["heldout_correct_hypothesis_count"] > 0)
        policies = anchor["policies"]
        check(f"anchor_{anchor['anchor']}_policy_count", len(policies) == 13)
        for row in policies:
            check(f"anchor_{anchor['anchor']}_{row['policy']}_{row['replicate']}_one_response",
                  len(row["oracle_responses"]) == 1)
            check(f"anchor_{anchor['anchor']}_{row['policy']}_{row['replicate']}_correct_pool_survivor",
                  row["correct_survivor_count"] > 0)
            check(f"anchor_{anchor['anchor']}_{row['policy']}_{row['replicate']}_charged_calls",
                  row["oracle_calls"] == (10 if row["policy"] == "oracle_best" else 1),
                  row["oracle_calls"])

    grouped = {}
    for anchor in anchors:
        for row in anchor["policies"]:
            grouped.setdefault(row["policy"], []).append(row)
    summary = {}
    for policy, rows in sorted(grouped.items()):
        summary[policy] = {
            "n": len(rows),
            "unique_correct_identifications": sum(r["unique_correct_identification"] for r in rows),
            "mean_survivor_count": statistics.mean(r["survivor_count"] for r in rows),
            "mean_heldout_accuracy": statistics.mean(r["mean_survivor_heldout_accuracy"] for r in rows),
            "mean_oracle_calls": statistics.mean(r["oracle_calls"] for r in rows),
            "selected_queries": [r["selected_query"] for r in rows],
        }
    entropy = summary.get("entropy_ranked", {})
    fixed = summary.get("fixed_first", {})
    check("entropy_has_no_unique_identification_lift_over_fixed",
          entropy.get("unique_correct_identifications") == fixed.get("unique_correct_identifications"),
          {"entropy": entropy.get("unique_correct_identifications"),
           "fixed_first": fixed.get("unique_correct_identifications")})
    report = {
        "protocol": raw.get("protocol"),
        "raw_sha256": "sha256:" + hashlib.sha256(RAW.read_bytes()).hexdigest(),
        "analyzer_sha256": "sha256:" + hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "checks": checks, "check_count": len(checks),
        "failed_checks": [c for c in checks if not c["ok"]],
        "all_checks_pass": all(c["ok"] for c in checks),
        "generation": {
            "median_wall_s": statistics.median(a["generation"]["wall_s"] for a in anchors),
            "median_explored": statistics.median(a["generation"]["explored"] for a in anchors),
            "pool_sizes": [a["generation"]["pool_size"] for a in anchors],
            "halt_reasons": [a["generation"]["halt_reason"] for a in anchors],
        },
        "policies": summary,
        "interpretation": "All bounded pools completed, but the generated pools were small and fixed-first already isolated held-out-correct behavior. This run shows no query-selection advantage for entropy on this family.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT), "checks": len(checks),
                      "failed": len(report["failed_checks"]),
                      "all_checks_pass": report["all_checks_pass"],
                      "policies": summary}, sort_keys=True))
    return 0 if report["all_checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
