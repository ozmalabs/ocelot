#!/usr/bin/env python3
"""Post-hoc semantic comparison of helper capture v1.4 with v1.3 baseline."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / "evaluation/reports/substrate_live_frame_rule_scope_capture_v1_3_workers_raw_20261005.json.gz"
NEW = ROOT / "evaluation/reports/substrate_live_helper_work_capture_v1_4_workers_raw_20261005.json.gz"
OUT = ROOT / "evaluation/reports/live_helper_work_capture_v1_4_baseline_parity_20261005.json"
HELPER_KINDS = {
    "dynamic_helper_invocation", "helper_codebook_population_node",
    "helper_node_attribute_examined", "helper_codebook_part_parsed",
    "helper_relation_cue_population_node", "helper_search_candidate",
    "helper_candidate_part_scored", "helper_graph_term_node_decoded",
    "helper_render_rule_candidate", "helper_auxiliary_population_node",
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def stable(value):
    """Remove process IDs, timings, and source receipts; retain outcomes."""
    if isinstance(value, dict):
        return {
            key: stable(child)
            for key, child in value.items()
            if key != "pid" and not key.endswith("_ns") and not key.startswith("turn_ns_")
            and not key.startswith("worker_started_inputs")
            and not key.startswith("worker_finished_inputs")
        }
    if isinstance(value, list):
        return [stable(child) for child in value]
    return value


def main() -> None:
    old, new = read(OLD), read(NEW)
    old_runs = {int(row["replicate"]): row["capture"] for row in old["runs"]}
    new_runs = {int(row["replicate"]): row["capture"] for row in new["runs"]}
    checks = {
        "same_replicate_ids": set(old_runs) == set(new_runs) == {0, 1, 2},
        "graph_semantics_match_by_worker": True,
        "task_outcomes_match_after_volatile_fields_removed": True,
        "request_prompt_reply_and_access_trace_match": True,
        "non_helper_work_trace_matches": True,
        "helper_events_are_additional_and_nonzero": True,
    }
    totals = {"helper_event_rows": 0, "helper_work_units": 0, "requests": 0}
    for rep in sorted(set(old_runs) & set(new_runs)):
        before, after = old_runs[rep], new_runs[rep]
        checks["graph_semantics_match_by_worker"] &= (
            before.get("graph_semantic_sha256") == after.get("graph_semantic_sha256")
        )
        checks["task_outcomes_match_after_volatile_fields_removed"] &= (
            stable(before.get("task_result")) == stable(after.get("task_result"))
        )
        checks["request_prompt_reply_and_access_trace_match"] &= len(before["requests"]) == len(after["requests"])
        for old_req, new_req in zip(before["requests"], after["requests"]):
            totals["requests"] += 1
            checks["request_prompt_reply_and_access_trace_match"] &= all(
                old_req.get(key) == new_req.get(key)
                for key in ("prompt", "reply", "access_rows")
            )
            old_work = [row for row in old_req["work_rows"] if str(row[2]) not in HELPER_KINDS]
            new_work = [row for row in new_req["work_rows"] if str(row[2]) not in HELPER_KINDS]
            checks["non_helper_work_trace_matches"] &= old_work == new_work
            helper_rows = [row for row in new_req["work_rows"] if str(row[2]) in HELPER_KINDS]
            totals["helper_event_rows"] += len(helper_rows)
            totals["helper_work_units"] += sum(int(row[4]) for row in helper_rows)
    checks["helper_events_are_additional_and_nonzero"] &= totals["helper_event_rows"] > 0 and totals["helper_work_units"] > 0
    result = {
        "schema_version": 1,
        "run_id": "live-helper-work-capture-v1.4-baseline-parity-posthoc-20261005",
        "comparison": "v1.3 baseline vs. v1.4 instrumented capture; timing, process IDs, and source receipts excluded from semantic equality",
        "inputs": {"baseline_sha256": digest(OLD), "instrumented_sha256": digest(NEW)},
        "checks": checks,
        "summary": totals,
        "claim_boundary": "This comparison supports task outcome and observed-access parity for the same selected route. It is post-hoc, does not replace an instrumented-vs-uninstrumented paired timing study, and does not establish helper locality or natural-task prevalence.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2))
    if not all(checks.values()):
        raise SystemExit("v1.4 baseline comparison failed")


if __name__ == "__main__":
    main()
