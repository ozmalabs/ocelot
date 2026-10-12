#!/usr/bin/env python3
"""Compare the seed-zero baseline with the three-seed foreign-snapshot replay."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evaluation/reports/foreign_snapshot_variation_v1_1_20261006/capture.json.gz"
FIXED_CAPTURE = ROOT / "evaluation/reports/foreign_snapshot_variation_v1_20261006/capture.json.gz"
LOCK = ROOT / "evaluation/substrate_capability/foreign_snapshot_variation_v1_1_20261006_lock.json"
OUT = ROOT / "evaluation/reports/foreign_snapshot_variation_v1_1_analysis_20261006.json"
ANALYZER = Path(__file__).resolve()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


raw = CAPTURE.read_bytes()
capture = json.loads(gzip.decompress(raw))
fixed = json.loads(gzip.decompress(FIXED_CAPTURE.read_bytes()))
runs = capture["runs"]
fixed_run = fixed["runs"][0]
checks = {
    "three_distinct_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
    "source_lock_matches": json.loads(LOCK.read_text()) == capture["locked_inputs"],
    "source_stable": capture["post_run_inputs"] == capture["locked_inputs"] and
        all(r["worker_source_stable"] for r in runs),
    "assigned_seeds_1_2_3": sorted(int(r["diagnostic_worker_environment"]["PYTHONHASHSEED"])
                                    for r in runs) == [1, 2, 3],
    "seven_turns_each": all(len(r["turns"]) == 7 for r in runs),
}

turns = []
for ti in range(7):
    rows = [r["turns"][ti] for r in runs]
    fixed_calls = fixed_run["turns"][ti].get("foreign_snapshot_diagnostics", [])
    call_groups = [r.get("foreign_snapshot_diagnostics", []) for r in rows]
    counts = [len(x) for x in call_groups]
    checks[f"call_count_matches_seed_zero__{ti}"] = len(set(counts + [len(fixed_calls)])) == 1
    call_summary = []
    if len(set(counts + [len(fixed_calls)])) == 1:
        for ci in range(counts[0]):
            group = [x[ci] for x in call_groups]
            baseline = fixed_calls[ci]
            input_hashes = [x["input_graph_sha256"] for x in group]
            labels = [stable(x["reconstructed_foreign_enumeration_labels"]) for x in group]
            ids = [stable(x["reconstructed_foreign_enumeration_ids"]) for x in group]
            results = [stable(x["result"]) for x in group]
            row = {
                "call_index": ci,
                "seed_values": [int(r["diagnostic_worker_environment"]["PYTHONHASHSEED"]) for r in runs],
                "input_graph_sha256_by_seed": input_hashes,
                "input_equal_across_seeds": len(set(input_hashes)) == 1,
                "input_equal_to_seed_zero": all(x["input_graph_sha256"] == baseline["input_graph_sha256"] for x in group),
                "input_sizes_by_seed": [[x["input_node_count"], x["input_edge_count"]] for x in group],
                "enumeration_ids_equal_across_seeds": len(set(ids)) == 1,
                "enumeration_labels_equal_across_seeds": len(set(labels)) == 1,
                "enumeration_labels_equal_to_seed_zero": all(
                    stable(x["reconstructed_foreign_enumeration_labels"]) ==
                    stable(baseline["reconstructed_foreign_enumeration_labels"]) for x in group),
                "model_results_equal_across_seeds": len(set(results)) == 1,
                "model_results_equal_to_seed_zero": all(stable(x["result"]) == stable(baseline["result"]) for x in group),
                "result_node_counts": [x["result"].get("node_count") for x in group],
            }
            call_summary.append(row)
    turns.append({"turn_index": ti, "prompt": rows[0].get("prompt"),
                  "foreign_call_count": counts[0] if counts else None,
                  "calls": call_summary})

failed = [k for k, v in checks.items() if not v]
analysis = {
    "schema_version": 1,
    "capture_sha256": hashlib.sha256(raw).hexdigest(),
    "capture_bytes_gzip": CAPTURE.stat().st_size,
    "fixed_seed_capture_sha256": sha(FIXED_CAPTURE),
    "lock_sha256": sha(LOCK),
    "analyzer_sha256": sha(ANALYZER),
    "checks": checks,
    "capture_integrity_pass": all(checks.values()),
    "failed_integrity_checks": failed,
    "turns": turns,
    "interpretation": (
        "Cross-seed equality is descriptive. Compare exact inputs, semantic enumeration labels, "
        "and model results in sequence; numeric ID differences alone do not establish semantic variation."
    ),
}
OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
print(json.dumps({"analysis": str(OUT.relative_to(ROOT)),
                  "capture_integrity_pass": analysis["capture_integrity_pass"],
                  "failed_integrity_checks": failed}, indent=2))
