#!/usr/bin/env python3
"""Reanalyse the locked live describe-scene access trace for dynamic locality.

This is a derived analysis of the v2.1 capture; it does not rerun the workload.
"""
from __future__ import annotations

import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_1_workers_raw_20260926.json"
CAPTURE = ROOT / "evaluation/reports/substrate_live_describe_scene_access_trace_v2_1_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/live_describe_scene_access_trace_v2_1_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_live_conversation_dynamic_locality_v1_20260927.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def analyze() -> dict:
    raw = json.loads(RAW.read_text())
    capture = json.loads(CAPTURE.read_text())
    lock = json.loads(LOCK.read_text())
    traced = [run for run in raw["runs"] if run["trace_enabled"]]
    checks = {
        "capture_inputs_match_postrun": capture["locked_inputs"] == capture["post_run_inputs"],
        "capture_lock_matches_lockfile": capture["locked_inputs"] == lock["locked_inputs"],
        "raw_inputs_match_capture": raw["locked_inputs"] == capture["locked_inputs"],
        "three_traced_replicates": len(traced) == 3 and len({r["replicate"] for r in traced}) == 3,
        "all_traces_complete": all(r["access_trace"]["dropped"] == 0 for r in traced),
        "trace_rows_reconcile": all(
            r["access_trace"]["event_count"] == sum(x["count"] for x in r["access_trace"]["event_rows"])
            for r in traced
        ),
        "stable_task_ownership_and_trace": len({
            json.dumps({"boundaries": r["task_boundaries"], "trace": r["access_trace"]}, sort_keys=True)
            for r in traced
        }) == 1,
    }

    # These are selected native access kinds, not a complete memory-access trace.
    representative = traced[0]
    boundaries = representative["task_boundaries"]
    owned = {key: set(boundaries[key]["owned_node_ids"]) for key in ("a", "b")}
    per_request = {}
    for req, label in (("request-A", "a"), ("request-B", "b")):
        rows = [x for x in representative["access_trace"]["event_rows"] if x["request"] == req]
        unique, weighted = collections.Counter(), collections.Counter()
        kinds, weighted_kinds = collections.Counter(), collections.Counter()
        term_reads_by_rule = collections.Counter()
        external_node_ids = set()
        touched_owned_node_ids = set()
        for row in rows:
            touched = {owner for owner, ids in owned.items()
                       if row["node"] in ids or row["peer"] in ids}
            bucket = "+".join(sorted(touched)) or "neither_owned_core"
            unique[bucket] += 1
            weighted[bucket] += row["count"]
            kinds[row["kind"]] += 1
            weighted_kinds[row["kind"]] += row["count"]
            if row["kind"] == "term_attr_read":
                term_reads_by_rule[row["rule_name"]] += row["count"]
            for node in (row["node"], row["peer"]):
                if node is not None:
                    (touched_owned_node_ids if node in owned["a"] | owned["b"] else external_node_ids).add(node)
        per_request[req] = {
            "request_owned_core": label,
            "unique_event_rows": len(rows),
            "weighted_event_count": sum(x["count"] for x in rows),
            "unique_rows_by_owned_core_touch": dict(sorted(unique.items())),
            "weighted_events_by_owned_core_touch": dict(sorted(weighted.items())),
            "unique_rows_by_kind": dict(sorted(kinds.items())),
            "weighted_events_by_kind": dict(sorted(weighted_kinds.items())),
            "top_term_attr_read_rules": [
                {"rule_name": name, "weighted_reads": count}
                for name, count in term_reads_by_rule.most_common(12)
            ],
            "distinct_owned_core_nodes_touched": len(touched_owned_node_ids),
            "distinct_non_owned_nodes_touched": len(external_node_ids),
        }

    result = {
        "schema_version": 1,
        "run_id": "substrate-live-conversation-dynamic-locality-v1-20260927",
        "claim_boundary": (
            "Derived from three identical, complete selected-operation traces in a synthetic live describe-scene "
            "conversation capture. Its task projection contains request lifecycle entities but omits the attached "
            "Scene and Percept inputs, so outside-core event counts cannot distinguish scene-local from shared "
            "or unrelated work. The request interval is serialized; event rows are aggregated and selected, not "
            "a complete graph read/write trace. This is a projection diagnostic, not a complete task-frame "
            "locality, natural-task prevalence, or asymptotic result."
        ),
        "inputs": {"raw_sha256": sha(RAW), "capture_sha256": sha(CAPTURE), "lock_sha256": sha(LOCK)},
        "checks": checks,
        "replicates": len(traced),
        "trace_total_weighted_events": representative["access_trace"]["event_count"],
        "trace_distinct_aggregated_rows": representative["access_trace"]["distinct_event_rows"],
        "task_geometry": {
            "projection_scope": "request lifecycle nodes; excludes attached Scene and Percept input nodes",
        } | {
            key: {k: boundaries[key][k] for k in (
                "owned_node_count", "internal_edge_count", "boundary_incidence_count",
                "boundary_unique_external_node_count", "owned_induced_treewidth_upper_bound"
            )}
            for key in ("a", "b")
        } | {"pair": {
            "direct_cross_task_edge_count": boundaries["pair"]["direct_cross_task_edge_count"],
            "shared_external_node_count": boundaries["pair"]["shared_external_node_count"],
            "shared_external_node_type_counts": boundaries["pair"]["shared_external_node_type_counts"],
        }},
        "per_request": per_request,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    report = analyze()
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "checks": report["checks"],
                      "task_geometry": report["task_geometry"], "per_request": report["per_request"]}, indent=2))
    if not all(report["checks"].values()):
        raise SystemExit("dynamic locality analysis integrity gate failed")
