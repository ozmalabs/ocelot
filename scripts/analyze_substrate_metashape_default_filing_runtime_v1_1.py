#!/usr/bin/env python3
"""Independent checks for vocabulary-enabled MetaShape filing captures."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

if len(sys.argv) != 4:
    raise SystemExit("usage: analyze... V1_1_A V1_1_B V1_DEFAULT")

paths = [Path(x) for x in sys.argv[1:]]
enabled_a, enabled_b, baseline = [json.loads(p.read_text()) for p in paths]
identity = lambda r: [(x["helper"], x["type"], x["attrs"]) for x in r["observations"]]
checks = {
    "paired_outputs_exact": enabled_a == enabled_b,
    "persistence_disabled": enabled_a["seed_persist_disabled"] and enabled_b["seed_persist_disabled"],
    "seed_tree_unchanged": enabled_a["seed_tree_unchanged"] and enabled_b["seed_tree_unchanged"],
    "same_seed_snapshot": enabled_a["seed_tree_sha256_before"] == enabled_b["seed_tree_sha256_before"],
    "shape_vocabulary_arm": enabled_a["condition"] == "default_world_adapter_plus_shape_vocabulary",
    "vocabulary_digest_stable": enabled_a["loaded_vocabulary_manifest_sha256"] == enabled_b["loaded_vocabulary_manifest_sha256"],
    "vocabulary_loaded": enabled_a["loaded_metashape_count"] >= 1,
    "helper_inputs_match_v1": identity(enabled_a) == identity(baseline),
    "call_count_matches_records": enabled_a["categorise_by_shape_calls"] == len(enabled_a["observations"]),
    "source_native_identity": enabled_a["source_sha256"] == enabled_b["source_sha256"]
        and enabled_a["native_artifact"] == enabled_b["native_artifact"],
}
base_results = [x["result"] for x in baseline["observations"]]
enabled_results = [x["result"] for x in enabled_a["observations"]]
per_helper = {}
for helper in sorted({x["helper"] for x in enabled_a["observations"]}):
    per_helper[helper] = {
        "items": sum(x["helper"] == helper for x in enabled_a["observations"]),
        "default_non_none": sum(x["helper"] == helper and x["result"] is not None
                                 for x in baseline["observations"]),
        "vocabulary_non_none": sum(x["helper"] == helper and x["result"] is not None
                                   for x in enabled_a["observations"]),
    }
result = {
    "schema": "substrate_metashape_default_filing_runtime_analysis_v1_1",
    "raw_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    "checks": checks,
    "all_checks_pass": all(checks.values()),
    "capture_count": len(enabled_a["observations"]),
    "loaded_metashape_count": enabled_a["loaded_metashape_count"],
    "default_result_counts": dict(sorted(Counter(map(str, base_results)).items())),
    "vocabulary_result_counts": dict(sorted(Counter(map(str, enabled_results)).items())),
    "changed_result_count": sum(a != b for a, b in zip(base_results, enabled_results)),
    "per_helper": per_helper,
    "claim_boundary": "Matched outputs for the same three helper inputs with shape_vocabulary loaded; no correctness or production-frequency claim.",
}
print(json.dumps(result, sort_keys=True, indent=2))
if not result["all_checks_pass"]:
    raise SystemExit(1)
