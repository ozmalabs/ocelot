#!/usr/bin/env python3
"""Analyze the source-locked foreign-snapshot variation diagnostic."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "evaluation/reports/foreign_snapshot_variation_v1_20261006/capture.json.gz"
LOCK = ROOT / "evaluation/substrate_capability/foreign_snapshot_variation_v1_20261006_lock.json"
OUT = ROOT / "evaluation/reports/foreign_snapshot_variation_v1_analysis_20261006.json"
ANALYZER = Path(__file__).resolve()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stable(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


raw = CAPTURE.read_bytes()
capture = json.loads(gzip.decompress(raw))
runs = capture["runs"]
checks = {
    "three_global_workers": len(runs) == 3 and all(r["arm"] == "global" for r in runs),
    "three_distinct_processes": len({r["pid"] for r in runs}) == 3,
    "source_lock_matches": json.loads(LOCK.read_text()) == capture["locked_inputs"],
    "source_stable": capture["post_run_inputs"] == capture["locked_inputs"] and
        all(r["worker_source_stable"] for r in runs),
    "hash_seed_zero": capture["environment"].get("PYTHONHASHSEED") == "0" and all(
        r["diagnostic_worker_environment"].get("PYTHONHASHSEED") == "0" for r in runs),
    "seven_turns_each": all(len(r["turns"]) == 7 for r in runs),
}

turn_summaries = []
for turn_index in range(7):
    rows = [r["turns"][turn_index] for r in runs]
    calls = [row.get("foreign_snapshot_diagnostics", []) for row in rows]
    count_match = len({len(row) for row in calls}) == 1
    checks[f"call_count_repeat__{turn_index}"] = count_match
    call_rows = []
    if count_match:
        for call_index in range(len(calls[0])):
            group = [worker_calls[call_index] for worker_calls in calls]
            input_hashes = [call["input_graph_sha256"] for call in group]
            enum_labels = [call["reconstructed_foreign_enumeration_labels"] for call in group]
            enum_ids = [call["reconstructed_foreign_enumeration_ids"] for call in group]
            outputs = [stable(call["result"]) for call in group]
            checks[f"input_repeat__{turn_index}__{call_index}"] = len(set(input_hashes)) == 1
            checks[f"enumeration_labels_repeat__{turn_index}__{call_index}"] = len(
                {stable(value) for value in enum_labels}) == 1
            checks[f"enumeration_ids_repeat__{turn_index}__{call_index}"] = len(
                {stable(value) for value in enum_ids}) == 1
            checks[f"model_result_repeat__{turn_index}__{call_index}"] = len(set(outputs)) == 1
            call_rows.append({
                "call_index": call_index,
                "input_sha256_by_worker": input_hashes,
                "input_node_counts": [call["input_node_count"] for call in group],
                "input_edge_counts": [call["input_edge_count"] for call in group],
                "enumeration_ids_by_worker": enum_ids,
                "enumeration_labels_repeat": len({stable(value) for value in enum_labels}) == 1,
                "model_results_by_worker": [call["result"] for call in group],
            })
    replies = [row["reply"] for row in rows]
    counts = [(row["settlement_parity"]["node_count"], row["settlement_parity"]["edge_count"])
              for row in rows]
    checks[f"reply_repeat__{turn_index}"] = len(set(replies)) == 1
    checks[f"graph_count_repeat__{turn_index}"] = len(set(counts)) == 1
    turn_summaries.append({"turn_index": turn_index,
        "prompt": rows[0].get("prompt"), "foreign_call_count": len(calls[0]),
        "input_calls": call_rows, "replies_repeat": len(set(replies)) == 1,
        "graph_counts_by_worker": counts})

failed = [name for name, value in checks.items() if not value]
analysis = {
    "schema_version": 1,
    "capture_path": str(CAPTURE.relative_to(ROOT)),
    "capture_sha256": hashlib.sha256(raw).hexdigest(),
    "capture_bytes_gzip": CAPTURE.stat().st_size,
    "lock_sha256": sha(LOCK),
    "analyzer_sha256": sha(ANALYZER),
    "checks": checks,
    "all_checks_pass": not failed,
    "failed_checks": failed,
    "turns": turn_summaries,
    "interpretation": (
        "A passing input/enumeration/result comparison under PYTHONHASHSEED=0 supports repeatability "
        "of the observed foreign-snapshot path on this workload. It does not establish graph parity "
        "for other seeds, tasks, or scheduler arms."
    ),
}
OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "all_checks_pass": analysis["all_checks_pass"],
                  "failed_checks": failed, "capture_bytes_gzip": CAPTURE.stat().st_size}, indent=2))
