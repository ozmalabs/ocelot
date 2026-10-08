#!/usr/bin/env python3
"""Independent checks for the paired default-filing runtime capture."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) != 3:
    raise SystemExit("usage: analyze_substrate_metashape_default_filing_runtime_v1.py RAW_A RAW_B")

paths = [Path(x) for x in sys.argv[1:]]
raw = [json.loads(p.read_text()) for p in paths]
checks = {
    "paired_outputs_exact": raw[0] == raw[1],
    "persistence_disabled": all(r["seed_persist_disabled"] for r in raw),
    "seed_tree_unchanged": all(r["seed_tree_unchanged"] for r in raw),
    "same_seed_snapshot": raw[0]["seed_tree_sha256_before"] == raw[1]["seed_tree_sha256_before"],
    "helpers_completed_in_order": all(r["helpers_completed"] == [
        "seed_epistemic_codebook", "seed_class_baseline_codebook",
        "seed_legal_hedging_codebook"] for r in raw),
    "zero_shapes_reported": all(r["loaded_metashape_count"] == 0 for r in raw),
    "record_count_matches": all(r["categorise_by_shape_calls"] == len(r["observations"]) for r in raw),
    "all_returns_none": all(x["result"] is None for r in raw for x in r["observations"]),
    "source_and_native_identity": raw[0]["source_sha256"] == raw[1]["source_sha256"]
        and raw[0]["native_artifact"] == raw[1]["native_artifact"],
}
expected_counts = {
    "seed_epistemic_codebook": 9,
    "seed_class_baseline_codebook": 4,
    "seed_legal_hedging_codebook": 6,
}
actual_counts = {
    helper: sum(x["helper"] == helper for x in raw[0]["observations"])
    for helper in expected_counts
}
checks["locked_per_helper_counts"] = actual_counts == expected_counts
result = {
    "schema": "substrate_metashape_default_filing_runtime_analysis_v1",
    "raw_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    "checks": checks,
    "all_checks_pass": all(checks.values()),
    "capture_count": len(raw[0]["observations"]),
    "calls_per_helper": actual_counts,
    "distinct_results": sorted({str(x["result"]) for x in raw[0]["observations"]}),
    "loaded_metashape_count": raw[0]["loaded_metashape_count"],
    "claim_boundary": "Three codebook helpers on a default WorldAdapter only; no filing accuracy or production frequency claim.",
}
print(json.dumps(result, sort_keys=True, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
