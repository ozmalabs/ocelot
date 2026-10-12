#!/usr/bin/env python3
"""Independent parity analysis for ShapeDecode name semantic controls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/shapedecode_name_aperture_semantics_v1_20261005.json"
LOCK = ROOT / "evaluation/substrate_capability/shapedecode_name_aperture_semantics_v1_lock_20261005.json"
OUT = ROOT / "evaluation/reports/shapedecode_name_aperture_semantics_v1_analysis_20261005.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    cap, lock = json.loads(CAPTURE.read_text()), json.loads(LOCK.read_text())
    rows = cap.get("rows", [])
    expected = {case["id"] for case in lock["cases"]}
    by_id = {row.get("case", {}).get("id"): row for row in rows}
    pairs = {}
    for control in ("unique", "case_varied", "exact_duplicate", "casefold_duplicate",
                    "scope_none_value", "scope_empty", "scope_order"):
        scan, cached = by_id.get(f"{control}_scan"), by_id.get(f"{control}_cached")
        pairs[control] = {"scan": None if scan is None else scan.get("result"),
                          "cached": None if cached is None else cached.get("result"),
                          "equal": bool(scan and cached and scan.get("result") == cached.get("result"))}
    checks = {
        "locked_case_set": len(rows) == len(expected) and set(by_id) == expected,
        "fresh_process_per_case": len({row.get("pid") for row in rows}) == len(expected),
        "worker_sources_stable": all(row.get("source_stable") and
            row.get("source_before") == lock["manifest"] == row.get("source_after") for row in rows),
        "no_process_or_worker_failures": not cap.get("process_failures") and
            all("worker_error" not in row for row in rows),
        "all_paired_results_equal": all(pair["equal"] for pair in pairs.values()),
        "explicit_empty_scope_has_no_parts": pairs["scope_empty"]["scan"] is None,
        "none_scope_value_is_unrestricted": pairs["scope_none_value"]["scan"] !=
            None,
        "exact_duplicate_uses_later_value": pairs["exact_duplicate"]["scan"] == 12,
        "casefold_duplicate_includes_both_variants": pairs["casefold_duplicate"]["scan"] == 36,
        "case_varied_name_resolves": pairs["case_varied"]["scan"] == 36,
        "reversed_name_aperture_preserves_insertion_order": pairs["scope_order"]["scan"] == ["r00"],
        "capture_lock_hash_matches": cap.get("lock_sha256") == sha(LOCK),
    }
    result = {"schema": "ShapeDecodeNameApertureSemanticsV1Analysis",
              "run_id": "shapedecode-name-aperture-semantics-v1-analysis-20261005",
              "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK),
              "checks": checks, "passed": all(checks.values()), "pairs": pairs,
              "interpretation": "Semantic parity for selected authored name-aperture controls only; no Surface(Text), malformed-record, exclusion, lifecycle, or natural-task claim."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "passed": result["passed"],
                      "checks": sum(checks.values()), "check_count": len(checks)}, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
