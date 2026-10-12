#!/usr/bin/env python3
"""Current-source live task graph/access capture for the frame-locality gate."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_FRAME_INTERFACE_CAPTURE_V1_PREREG_20261003.md"
LOCK = ROOT / "evaluation/substrate_capability/live_frame_interface_capture_v1_lock_20261003.json"
RAW = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_workers_raw_20261003.json"
SUMMARY = ROOT / "evaluation/reports/substrate_live_frame_interface_capture_v1_20261003.json"
BASE_SCRIPT = ROOT / "scripts/substrate_live_self_report_task_boundary_v2_1.py"
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from domains.engine_provenance import assert_measuring_engine  # noqa: E402

_SPEC = importlib.util.spec_from_file_location("self_report_boundary_base", BASE_SCRIPT)
BASE = importlib.util.module_from_spec(_SPEC)
assert _SPEC and _SPEC.loader
_SPEC.loader.exec_module(BASE)


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lock_inputs() -> dict:
    base = BASE.lock_inputs()
    base.update({
        "capture_protocol_sha256": sha(PROTOCOL),
        "capture_runner_sha256": sha(Path(__file__).resolve()),
        "base_worker_sha256": sha(BASE_SCRIPT),
    })
    return base


def graph_summary(graph: dict) -> dict:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    node_types = Counter(str(n.get("type")) for n in nodes)
    edge_types = Counter(str(e.get("type")) for e in edges)
    attrs = Counter()
    value_kinds = Counter()
    for node in nodes:
        for key, value in node.get("attrs", {}).items():
            attrs[(str(node.get("type")), str(key))] += 1
            kind = type(value).__name__
            value_kinds[(str(node.get("type")), str(key), kind)] += 1
    return {
        "node_count": len(nodes), "edge_count": len(edges),
        "node_type_counts": dict(sorted(node_types.items())),
        "edge_type_counts": dict(sorted(edge_types.items())),
        "attribute_presence_counts": [list(k) + [v] for k, v in sorted(attrs.items())],
        "attribute_value_kind_counts": [list(k) + [v] for k, v in sorted(value_kinds.items())],
    }


def boundary_stats(graph: dict, members: set[int]) -> dict:
    internal, crossing, external = 0, 0, set()
    for edge in graph.get("edges", []):
        src, tgt = int(edge["src"]), int(edge["tgt"])
        src_in, tgt_in = src in members, tgt in members
        if src_in and tgt_in:
            internal += 1
        elif src_in != tgt_in:
            crossing += 1
            external.add(tgt if src_in else src)
    node_types = {int(n["id"]): str(n.get("type")) for n in graph.get("nodes", [])}
    ext_types = Counter(node_types.get(node, "<missing>") for node in external)
    return {
        "member_count": len(members), "internal_edge_count": internal,
        "crossing_incidence_count": crossing,
        "distinct_external_node_count": len(external),
        "external_node_type_counts": dict(sorted(ext_types.items())),
        "all_members_resolve": members <= set(node_types),
        "all_external_nodes_resolve": all(node in node_types for node in external),
    }


def bfs_proposals(graph: dict, root: int, request_trace: dict) -> list[dict]:
    adjacency: dict[int, set[int]] = defaultdict(set)
    for edge in graph.get("edges", []):
        src, tgt = int(edge["src"]), int(edge["tgt"])
        adjacency[src].add(tgt)
        adjacency[tgt].add(src)
    members = {root}
    frontier = {root}
    output = []
    trace_rows = request_trace["access_rows"]
    for radius in range(4):
        started = time.perf_counter_ns()
        if radius:
            nxt = set().union(*(adjacency.get(node, set()) for node in frontier)) - members
            members.update(nxt)
            frontier = nxt
        stats = boundary_stats(graph, members)
        trace_total = sum(int(row[6]) for row in trace_rows)
        trace_touched = sum(
            int(row[6]) for row in trace_rows
            if (row[2] is not None and int(row[2]) in members)
            or (row[4] is not None and int(row[4]) in members)
        )
        rules = sorted({int(row[0]) for row in trace_rows
                        if ((row[2] is not None and int(row[2]) in members)
                            or (row[4] is not None and int(row[4]) in members))})
        discovery_ns = time.perf_counter_ns() - started
        output.append({
            "proposal": "undirected_typed_graph_bfs", "root_message_id": root,
            "radius": radius, "member_ids": sorted(members), **stats,
            "dynamic_trace_weight_total": trace_total,
            "dynamic_trace_weight_touching_member_nodes": trace_touched,
            "dynamic_trace_touch_fraction": trace_touched / trace_total if trace_total else None,
            "touched_rule_uid_count": len(rules), "touched_rule_uids": rules,
            "discovery_time_ns": discovery_ns,
        })
    return output


def instrumented_worker(rep: int) -> dict:
    assert_measuring_engine()
    started_inputs = lock_inputs()
    from substrate_rs import _native
    from substrate.world_adapter import WorldAdapter

    captured = {"graph": None, "native_rules": None, "requests": []}
    original_digest = BASE.semantic_graph_digest
    original_converse = WorldAdapter.converse

    def capture_digest(graph):
        captured["graph"] = graph
        return original_digest(graph)

    def measured_converse(agent, *args, **kwargs):
        audit = agent.inner
        if captured["native_rules"] is None:
            captured["native_rules"] = audit.export_rules()
        audit.runtime_access_trace_reset()
        # Access-trace overhead studies can disable concrete event recording
        # while retaining the same worker, graph, rule exports, and operation
        # work trace. Default-on preserves every historical capture behavior.
        capture_access = os.environ.get("OZMA_ACCESS_TRACE", "1") != "0"
        audit.runtime_access_trace_set_enabled(capture_access)
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
        started_ns = time.perf_counter_ns()
        error = None
        result = None
        try:
            result = original_converse(agent, *args, **kwargs)
        except BaseException as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            elapsed_ns = time.perf_counter_ns() - started_ns
            access_rows, access_dropped = audit.runtime_access_trace_snapshot_detailed()
            work_rows, work_dropped = audit.runtime_work_trace_snapshot()
            audit.runtime_access_trace_set_enabled(False)
            _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
        captured["requests"].append({
            "prompt": str(args[0]) if args else None,
            "reply": result,
            "error": error,
            "elapsed_ns": elapsed_ns,
            "access_rows": [list(row) for row in access_rows],
            "access_dropped_events": int(access_dropped),
            "work_rows": [list(row) for row in work_rows],
            "work_dropped_events": int(work_dropped),
        })
        if error is not None:
            raise RuntimeError(error)
        return result

    BASE.semantic_graph_digest = capture_digest
    WorldAdapter.converse = measured_converse
    try:
        run = BASE.worker(rep)
    except BaseException as exc:
        finished_inputs = lock_inputs()
        return {
            "replicate": rep, "pid": os.getpid(),
            "worker_error": f"{type(exc).__name__}: {exc}",
            "worker_started_inputs": started_inputs,
            "worker_finished_inputs": finished_inputs,
            "requests": captured["requests"],
        }
    finally:
        BASE.semantic_graph_digest = original_digest
        WorldAdapter.converse = original_converse

    graph = captured["graph"]
    if graph is None:
        raise RuntimeError("base worker did not expose its final graph to the capture hook")
    summary = graph_summary(graph)
    message_ids = [int(turn["message_id"]) for turn in run["turns"]]
    if len(message_ids) != len(captured["requests"]):
        raise RuntimeError("request trace count does not match task turn count")
    proposals = [bfs_proposals(graph, message_id, captured["requests"][index])
                 for index, message_id in enumerate(message_ids)]
    out = {
        "replicate": rep, "pid": os.getpid(), "worker_started_inputs": started_inputs,
        "worker_finished_inputs": lock_inputs(), "task_result": run,
        "requests": captured["requests"], "graph_summary": summary,
        "graph_semantic_sha256": run["whole_graph_semantic_sha256"],
        "bfs_proposals": proposals,
        "graph_rule_nodes": [n for n in graph.get("nodes", [])
                             if str(n.get("type", "")).lower() in {"rule", "rulepatch", "production"}],
    }
    if rep == 0:
        out["full_graph"] = graph
        out["native_exported_rules"] = captured["native_rules"]
    return out


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".frame-interface-", suffix=".json", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True, default=str)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    except BaseException:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def run() -> dict:
    assert_measuring_engine()
    locked = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale v1 source lock; freeze with --lock after protocol and runner are final")
    env = {**os.environ, "OZMA_NO_LLM": "1", "OZMA_SEED_PERSIST_DISABLED": "1"}
    jobs = [0, 1, 2]
    random.Random(20261003).shuffle(jobs)
    runs, process_failures = [], []
    for rep in jobs:
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True)
        try:
            payload = json.loads(proc.stdout)
        except Exception:
            payload = {"replicate": rep, "worker_error": "invalid_worker_json",
                       "returncode": proc.returncode, "stdout_tail": proc.stdout[-4000:],
                       "stderr_tail": proc.stderr[-4000:]}
        runs.append(payload)
        if proc.returncode:
            process_failures.append({"replicate": rep, "returncode": proc.returncode,
                                     "stderr_tail": proc.stderr[-4000:]})

    post_inputs = lock_inputs()
    valid_runs = [row for row in runs if "task_result" in row]
    semantic_digests = {r.get("graph_semantic_sha256") for r in valid_runs}
    summaries = {json.dumps(r.get("graph_summary"), sort_keys=True) for r in valid_runs}
    boundary_signatures = {json.dumps(r["task_result"]["task_boundaries"], sort_keys=True)
                           for r in valid_runs if "task_result" in r}
    request_trace_complete = all(
        req.get("access_dropped_events") == 0 and req.get("work_dropped_events") == 0
        for row in valid_runs for req in row.get("requests", [])
    )
    request_shape_reproduces = all(
        [req.get("prompt") for req in row.get("requests", [])] == list(BASE.PROMPTS)
        for row in valid_runs
    ) and all(len(row.get("requests", [])) == 2 for row in valid_runs)
    endpoints_resolve = all(
        proposal["all_members_resolve"] and proposal["all_external_nodes_resolve"]
        for row in valid_runs for turn in row.get("bfs_proposals", []) for proposal in turn
    )
    lifecycle_passes = all(
        row["task_result"]["turns"][0]["route"] == "self_report"
        and row["task_result"]["turns"][0]["reply_nonempty"]
        and row["task_result"]["turns"][0]["goal_count"] == 1
        and row["task_result"]["turns"][0]["goal"]["status"] == "resolved"
        and row["task_result"]["turns"][0]["goal"]["transition_kinds"] == ["selection", "execution", "action_result"]
        and row["task_result"]["turns"][0]["goal"]["transition_links_all_bound"]
        and row["task_result"]["turns"][0]["goal"]["closed"]
        and row["task_result"]["turns"][1]["route"] is None
        and row["task_result"]["turns"][1]["goal_count"] == 0
        and not row["task_result"]["turns"][1]["lifecycle_events"]
        and not row["task_result"]["turns"][1]["producer_work"]
        for row in valid_runs if len(row["task_result"].get("turns", [])) == 2
    ) and len(valid_runs) == 3
    checks = {
        "three_distinct_fresh_pids": len(valid_runs) == 3 and len({r["pid"] for r in valid_runs}) == 3,
        "all_workers_lock_stable": post_inputs == locked and all(
            r.get("worker_started_inputs") == locked == r.get("worker_finished_inputs") for r in valid_runs),
        "semantic_graph_reproduces": len(semantic_digests) == 1,
        "derived_graph_summary_reproduces": len(summaries) == 1,
        "declared_boundaries_reproduce": len(boundary_signatures) == 1,
        "captured_prompt_schedule_reproduces": bool(valid_runs) and request_shape_reproduces,
        "traces_have_no_dropped_events": bool(valid_runs) and request_trace_complete,
        "bfs_members_and_external_endpoints_resolve": bool(valid_runs) and endpoints_resolve,
        "first_prompt_lifecycle_and_second_prompt_shortfall_reproduce": lifecycle_passes,
    }
    controls = BASE.controls()
    control_checks = {
        "correct_link_selects_only_owner": controls["correct_link"]["statuses"] == ["selected", "proposed"],
        "omitted_link_selects_no_goal": controls["omitted_link"]["statuses"] == ["proposed", "proposed"],
        "swapped_link_follows_explicit_edge": controls["swapped_link"]["statuses"] == ["proposed", "selected"]
            and controls["swapped_link"]["event_goal_ids"] == [controls["swapped_link"]["goal_ids"][1]]
            and controls["swapped_link"]["declared_target"] == controls["swapped_link"]["goal_ids"][0],
        "duplicate_result_is_idempotent": controls["duplicate_result"]["status"] == "resolved"
            and controls["duplicate_result"]["transition_kinds"] == ["selection", "execution", "action_result"]
            and controls["duplicate_result"]["closed"] and not controls["duplicate_result"]["active"],
        "faculty_failure_blocks_with_identity": controls["faculty_failure"]["goal_status"] == "blocked"
            and controls["faculty_failure"]["goal_transition_kinds"] == ["selection", "execution", "action_failure"]
            and controls["faculty_failure"]["closed"] and not controls["faculty_failure"]["active"],
    }
    checks["all_semantic_controls_pass"] = all(control_checks.values())
    raw = {
        "schema_version": 1, "run_id": "substrate-live-frame-interface-capture-v1-20261003",
        "protocol": str(PROTOCOL.relative_to(ROOT)), "locked_inputs": locked,
        "post_run_inputs": post_inputs, "worker_order": jobs, "runs": runs,
        "controls": controls, "control_checks": control_checks,
        "process_failures": process_failures, "checks": checks,
        "claim_boundary": "Three fresh workers over one authored self-report prompt pair; BFS is a generic root-neighborhood proposal. No learned frame, exact task factorization, partitioned execution, scaling law, or prevalence claim.",
    }
    atomic_json(RAW, raw)
    summary = {
        "schema_version": 1, "run_id": raw["run_id"],
        "raw_path": str(RAW.relative_to(ROOT)), "raw_sha256": sha(RAW),
        "lock_path": str(LOCK.relative_to(ROOT)), "lock_sha256": sha(LOCK),
        "checks": checks, "summary": {"workers": len(valid_runs), "access_rows": sum(len(q.get("access_rows", [])) for r in valid_runs for q in r.get("requests", [])),
                                        "work_rows": sum(len(q.get("work_rows", [])) for r in valid_runs for q in r.get("requests", [])),
                                        "full_graph_nodes": next((len(r.get("full_graph", {}).get("nodes", [])) for r in valid_runs if "full_graph" in r), 0),
                                        "full_graph_edges": next((len(r.get("full_graph", {}).get("edges", [])) for r in valid_runs if "full_graph" in r), 0)},
    }
    atomic_json(SUMMARY, summary)
    print(json.dumps(summary, indent=2))
    if not all(checks.values()):
        raise SystemExit("one or more preregistered structural capture gates failed; raw capture retained")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", action="store_true", help="write a new versioned lock; does not run workers")
    parser.add_argument("--worker", type=int, choices=(0, 1, 2))
    args = parser.parse_args()
    assert_measuring_engine()
    if args.lock:
        atomic_json(LOCK, {"locked_inputs": lock_inputs()})
        print(LOCK.relative_to(ROOT))
    elif args.worker is not None:
        print(json.dumps(instrumented_worker(args.worker), sort_keys=True, default=str))
    else:
        run()


if __name__ == "__main__":
    main()
