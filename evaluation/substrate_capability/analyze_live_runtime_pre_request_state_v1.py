#!/usr/bin/env python3
"""Independently verify each compressed request-boundary checkpoint."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CAPTURE = ROOT / "evaluation/reports/live_runtime_pre_request_state_v1_20261004.json"
LOCK = ROOT / "evaluation/substrate_capability/live_runtime_pre_request_state_v1_lock_20261004.json"
PARENT = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz"
OUT = ROOT / "evaluation/reports/live_runtime_pre_request_state_v1_analysis_20261004.json"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def task_projection(task: dict) -> list[dict]:
    return [{
        "route": turn.get("route"),
        "reply_nonempty": turn.get("reply_nonempty"),
        "goal_count": turn.get("goal_count"),
        "goal": {key: turn.get("goal", {}).get(key) for key in ("kind", "status", "transition_kinds", "transition_links_all_bound", "closed")} if isinstance(turn.get("goal"), dict) else None,
    } for turn in task.get("turns", [])]


def main() -> int:
    errors: list[str] = []

    def req(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    locked = json.loads(LOCK.read_text())["locked_inputs"]
    manifest = json.loads(CAPTURE.read_text())
    req(manifest.get("locked_inputs") == locked == manifest.get("post_run_inputs"), "source lock differs or changed during run")
    req(manifest.get("source_stable") is True and manifest.get("all_checks_pass") is True, "capture integrity or parent parity gates failed")
    req(manifest.get("request_count") == 2, "expected two captured requests")
    req(manifest.get("primary_state_matches_at_request_boundary") is True, "runner observed primary boundary mismatch")
    req(manifest.get("parent_task_projection_matches") is True and manifest.get("parent_replies_match") is True and manifest.get("parent_final_graph_digest_matches") is True, "parent route parity failed")
    checkpoint_rows = manifest.get("checkpoints", [])
    req(len(checkpoint_rows) == 4, "expected four primary state checkpoints")
    checkpoint_results = []
    for expected_index, row in enumerate(checkpoint_rows):
        req(row.get("index") == expected_index, "checkpoint index/order mismatch")
        path = ROOT / str(row.get("path", ""))
        if not path.exists():
            errors.append("missing checkpoint: " + str(path))
            continue
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            state = json.load(stream)
        actual_digest = hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
        graph = state.get("graph", {})
        nodes, edges = graph.get("nodes", []), graph.get("edges", [])
        rules = state.get("rules", [])
        node_ids = [str(node.get("id")) for node in nodes]
        rule_uids = [int(rule["rule_uid"]) for rule in rules if "rule_uid" in rule]
        req(actual_digest == row.get("state_sha256"), "checkpoint state digest mismatch: " + str(row.get("label")))
        req(len(nodes) == row.get("graph_nodes") and len(edges) == row.get("graph_edges") and len(rules) == row.get("rule_count"), "checkpoint counts mismatch: " + str(row.get("label")))
        req(len(node_ids) == len(set(node_ids)), "duplicate graph node IDs: " + str(row.get("label")))
        req(len(rule_uids) == len(set(rule_uids)), "duplicate rule UIDs: " + str(row.get("label")))
        id_set = set(node_ids)
        req(all(str(edge.get("src")) in id_set and str(edge.get("tgt")) in id_set for edge in edges), "dangling graph edge: " + str(row.get("label")))
        checkpoint_results.append({"label": row.get("label"), "state_sha256": actual_digest, "graph_nodes": len(nodes), "graph_edges": len(edges), "rule_count": len(rules), "file_sha256": sha(path)})
        del state

    if len(checkpoint_results) == 4:
        req(checkpoint_results[1]["state_sha256"] == checkpoint_results[2]["state_sha256"], "after-first and before-second primary states differ")
    with gzip.open(PARENT, "rt", encoding="utf-8") as stream:
        parent = json.load(stream)
    parent_runs = [r for r in parent.get("runs", []) if r.get("replicate") == 0 and r.get("audit_mode") == "on"]
    req(parent.get("source_stable") is True and parent.get("all_checks_pass") is True and len(parent_runs) == 1, "parent v1.6 capture integrity or fixed-sample gate failed")
    payload = manifest.get("payload", {})
    if len(parent_runs) == 1:
        parent_run = parent_runs[0]
        req(task_projection(payload.get("task_result", {})) == task_projection(parent_run.get("task_result", {})), "task projection differs from parent capture")
        req(payload.get("graph_semantic_sha256") == parent_run.get("graph_semantic_sha256"), "stored graph digest differs from parent capture")
        req([r.get("reply") for r in payload.get("requests", [])] == [r.get("reply") for r in parent_run.get("requests", [])], "stored replies differ from parent capture")

    result = {
        "schema": "LiveRuntimePreRequestStateV1Analysis",
        "passed": not errors,
        "errors": errors,
        "manifest_sha256": sha(CAPTURE),
        "parent_capture_sha256": sha(PARENT),
        "checkpoint_count": len(checkpoint_results),
        "checkpoints": checkpoint_results,
        "primary_between_request_states_equal": len(checkpoint_results) == 4 and checkpoint_results[1]["state_sha256"] == checkpoint_results[2]["state_sha256"],
        "claim_boundary": "Exact primary graph/rule checkpoint equality and task/reply/final-digest parity for one authored two-request route; secondary native-store bodies remain outside capture.",
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "errors": errors, "checkpoints": result["checkpoints"]}, indent=2))
    return int(not result["passed"])


if __name__ == "__main__":
    raise SystemExit(main())
