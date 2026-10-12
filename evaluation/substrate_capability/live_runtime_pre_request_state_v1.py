#!/usr/bin/env python3
"""Capture exact primary graph/rule snapshots around each fixed live request."""
from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_RUNTIME_PRE_REQUEST_STATE_V1_PREREG_20261004.md"
RUNNER = Path(__file__).resolve()
PARENT_RUNNER = ROOT / "evaluation/substrate_capability/live_runtime_closure_counters_v1_6.py"
PARENT_LOCK = ROOT / "evaluation/substrate_capability/live_runtime_closure_counters_v1_6_lock_20261004.json"
PARENT_RAW = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_20261004.json.gz"
PARENT_ANALYSIS = ROOT / "evaluation/reports/live_runtime_closure_counters_v1_6_analysis_20261004.json"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_live_runtime_pre_request_state_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/live_runtime_pre_request_state_v1_lock_20261004.json"
OUT = ROOT / "evaluation/reports/live_runtime_pre_request_state_v1_20261004.json"
CHECKPOINT_DIR = ROOT / "evaluation/reports/live_runtime_pre_request_state_v1_checkpoints"

SPEC = importlib.util.spec_from_file_location("live_runtime_counter_parent", PARENT_RUNNER)
PARENT = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(PARENT)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def task_projection(task: dict) -> list[dict]:
    return [{
        "route": turn.get("route"),
        "reply_nonempty": turn.get("reply_nonempty"),
        "goal_count": turn.get("goal_count"),
        "goal": {key: turn.get("goal", {}).get(key) for key in ("kind", "status", "transition_kinds", "transition_links_all_bound", "closed")} if isinstance(turn.get("goal"), dict) else None,
    } for turn in task.get("turns", [])]


def locked_inputs() -> dict:
    from substrate_rs import _native

    return {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "analyzer_sha256": sha(ANALYZER),
        "parent_runner_sha256": sha(PARENT_RUNNER),
        "parent_lock_sha256": sha(PARENT_LOCK),
        "parent_capture_sha256": sha(PARENT_RAW),
        "parent_analysis_sha256": sha(PARENT_ANALYSIS),
        "parent_worker_inputs": PARENT.lock_inputs(),
        "native_sha256": sha(Path(_native.__file__).resolve()),
        "cargo_lock_sha256": sha(ROOT / "runners/dsl/Cargo.lock"),
    }


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or OUT.exists() or CHECKPOINT_DIR.exists():
            raise SystemExit("refusing to overwrite existing checkpoint capture")
        LOCK.write_text(json.dumps({"schema": "LiveRuntimePreRequestStateV1Lock", "locked_inputs": locked_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if sys.argv[1:]:
        raise SystemExit("usage: live_runtime_pre_request_state_v1.py [--lock]")
    assert_measuring_engine()
    locked = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source lock")
    parent_analysis = json.loads(PARENT_ANALYSIS.read_text())
    if parent_analysis.get("passed") is not True:
        raise SystemExit("parent v1.6 analysis must pass")

    from substrate.world_adapter import WorldAdapter

    checkpoints = []
    request_rows = []
    boundary_equalities = []
    original_converse = WorldAdapter.converse

    def capture_boundaries(agent, *args, **kwargs):
        inner = agent.inner
        before_graph = inner.graph_to_dict()
        before_rules = inner.export_rules()
        before = {"graph": before_graph, "rules": before_rules}
        if not checkpoints:
            checkpoints.append({"label": "before_first_request", "state": before})
        else:
            boundary_equalities.append(checkpoints[-1]["state"] == before)
            checkpoints.append({"label": f"before_request_{len(request_rows) + 1}", "state": before})
        reply = original_converse(agent, *args, **kwargs)
        after_graph = inner.graph_to_dict()
        after_rules = inner.export_rules()
        checkpoints.append({"label": f"after_request_{len(request_rows) + 1}", "state": {"graph": after_graph, "rules": after_rules}})
        request_rows.append({"prompt": str(args[0]) if args else None, "reply": reply})
        return reply

    WorldAdapter.converse = capture_boundaries
    try:
        payload = PARENT.worker(0, "on")
    finally:
        WorldAdapter.converse = original_converse

    with gzip.open(PARENT_RAW, "rt", encoding="utf-8") as stream:
        parent_capture = json.load(stream)
    parent_runs = [row for row in parent_capture["runs"] if row.get("replicate") == 0 and row.get("audit_mode") == "on"]
    if len(parent_runs) != 1:
        raise SystemExit("parent fixed sample is not unique")
    parent_run = parent_runs[0]
    task_parity = task_projection(payload.get("task_result", {})) == task_projection(parent_run.get("task_result", {}))
    reply_parity = [row.get("reply") for row in request_rows] == [row.get("reply") for row in parent_run.get("requests", [])]
    graph_digest_parity = payload.get("graph_semantic_sha256") == parent_run.get("graph_semantic_sha256")
    boundary_parity = len(boundary_equalities) == 1 and all(boundary_equalities)

    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=False)
    checkpoint_rows = []
    for index, checkpoint in enumerate(checkpoints):
        state = checkpoint["state"]
        canonical = json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode()
        name = f"checkpoint_{index}_{checkpoint['label']}.json.gz"
        path = CHECKPOINT_DIR / name
        with gzip.open(path, "wt", encoding="utf-8") as stream:
            json.dump(state, stream, sort_keys=True, separators=(",", ":"), default=str)
        graph = state["graph"]
        checkpoint_rows.append({
            "index": index,
            "label": checkpoint["label"],
            "path": (Path("evaluation/reports/live_runtime_pre_request_state_v1_checkpoints") / name).as_posix(),
            "state_sha256": hashlib.sha256(canonical).hexdigest(),
            "graph_nodes": len(graph.get("nodes", [])),
            "graph_edges": len(graph.get("edges", [])),
            "rule_count": len(state.get("rules", [])),
        })

    compact_payload = {
        key: payload[key]
        for key in ("replicate", "task_result", "graph_semantic_sha256", "native_exported_rules", "native_counter_observations", "worker_started_inputs", "worker_finished_inputs", "source_stable", "audit_mode")
        if key in payload
    }
    compact_payload["requests"] = request_rows
    post = locked_inputs()
    result = {
        "schema": "LiveRuntimePreRequestStateV1",
        "locked_inputs": locked,
        "post_run_inputs": post,
        "source_stable": locked == post,
        "replicate": 0,
        "audit_mode": "on",
        "parent_capture_run_id": "live-runtime-closure-counters-v1.6-20261004",
        "payload": compact_payload,
        "checkpoints": checkpoint_rows,
        "request_count": len(request_rows),
        "primary_state_matches_at_request_boundary": boundary_parity,
        "parent_task_projection_matches": task_parity,
        "parent_replies_match": reply_parity,
        "parent_final_graph_digest_matches": graph_digest_parity,
        "all_checks_pass": locked == post and len(checkpoints) == 4 and len(request_rows) == 2 and boundary_parity and task_parity and reply_parity and graph_digest_parity,
    }
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"], "checkpoints": len(checkpoints), "boundary_parity": boundary_parity, "task_parity": task_parity, "reply_parity": reply_parity, "digest_parity": graph_digest_parity, "raw": OUT.relative_to(ROOT).as_posix()}))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
