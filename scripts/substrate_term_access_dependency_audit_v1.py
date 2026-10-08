#!/usr/bin/env python3
"""Replay rooted-frame workload and capture static/dynamic access-scope data."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_TERM_ACCESS_DEPENDENCY_AUDIT_V1_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_substrate_term_access_dependency_audit_v1.py"
BASE_RAW = ROOT / "evaluation/reports/rooted_frame_access_scope_reconciliation_v1_2_20260928.json"
BASE_LOCK = ROOT / "evaluation/substrate_capability/rooted_frame_access_scope_reconciliation_v1_2_lock_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/term_access_dependency_audit_v1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/term_access_dependency_audit_v1_20260928.json"
PROMPTS = ("report your organisation", "describe who you are")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_sha(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    from scripts import substrate_rooted_frame_proposal_panel_v1_1 as base
    current_base = base.lock_inputs()
    recorded_base = json.loads(BASE_LOCK.read_text())["locked_inputs"]
    return {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__)),
        "analyzer_sha256": sha(ANALYZER),
        "accepted_baseline_raw_sha256": sha(BASE_RAW),
        "accepted_baseline_lock_sha256": sha(BASE_LOCK),
        "accepted_baseline_locked_inputs_sha256": json_sha(recorded_base),
        "accepted_baseline_current_inputs_sha256": json_sha(current_base),
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
    }


def static_rules_for_observed(inner, trace_rows: list[dict]) -> tuple[list[dict], dict[str, dict]]:
    observed_uids = {int(row["rule_uid"]) for row in trace_rows}
    accesses = inner.rule_access_sets()
    exported = inner.export_rules()
    rules = []
    index_uid = {}
    for idx, name, active, reads, term_edges, writes, reads_any, writes_any in accesses:
        metadata = inner.rule_metadata(int(idx))
        uid = int(metadata["rule_uid"])
        index_uid[int(idx)] = uid
        if uid not in observed_uids:
            continue
        rules.append({
            "rule_uid": uid,
            "rule_idx": int(idx),
            "rule_name": str(name),
            "active_after_request": bool(active),
            "reads": sorted(set(map(str, reads))),
            "term_edge_reads": sorted(set(map(str, term_edges))),
            "writes": sorted(set(map(str, writes))),
            "reads_any": bool(reads_any),
            "writes_any": bool(writes_any),
            "match_edge_count": len(exported[int(idx)].get("match", [])),
            "match_edges": exported[int(idx)].get("match", []),
        })
    return rules, {str(index): str(uid) for index, uid in index_uid.items()}


def worker(replicate: int) -> dict:
    started = lock_inputs()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from scripts import substrate_rooted_frame_proposal_panel_v1_1 as base

    agent = WorldAdapter(seeds=())
    boot_start = time.perf_counter_ns()
    load_all_seeds(agent)
    boot_ns = time.perf_counter_ns() - boot_start
    turns = []
    for turn_index, prompt in enumerate(PROMPTS):
        inner = agent.inner
        inner.runtime_access_trace_set_enabled(False)
        inner.runtime_access_trace_reset()
        inner.scale_audit_reset()
        inner.scale_audit_per_rule_reset()
        inner.runtime_access_trace_set_enabled(True)
        inner.scale_audit_set_enabled(True)
        inner.scale_audit_set_per_rule_enabled(True)
        start = time.perf_counter_ns()
        try:
            reply = agent.converse(prompt, speech_act="instruction", speaker="alice")
        finally:
            inner.runtime_access_trace_set_enabled(False)
            inner.scale_audit_set_per_rule_enabled(False)
            inner.scale_audit_set_enabled(False)
        elapsed_ns = time.perf_counter_ns() - start
        trace_raw, dropped = inner.runtime_access_trace_snapshot()
        trace_rows = [{"rule_uid": int(uid), "kind": str(kind), "node": None if node is None else int(node),
                       "resource": None if resource is None else str(resource), "peer": None if peer is None else int(peer),
                       "count": int(count)} for uid, kind, node, resource, peer, count in trace_raw]
        static_rules, index_uid = static_rules_for_observed(inner, trace_rows)
        per_rule = {}
        for idx, metric, count in inner.scale_audit_per_rule_snapshot():
            uid = index_uid.get(str(int(idx)))
            if uid is not None:
                per_rule.setdefault(uid, {})[str(metric)] = int(count)
        aggregate = {str(key): int(value) for key, value in dict(inner.scale_audit_snapshot()).items()}
        message = agent._last_turn_inbound
        attrs = dict(agent.s.node(message)["attrs"])
        goals = [goal for goal in agent.s.nodes("Goal") if message in agent.inner.neighbours(goal, "comprehends")]
        turns.append({
            "turn": turn_index,
            "prompt": prompt,
            "route": attrs.get("communication_route"),
            "reply_nonempty": bool(reply),
            "message_id": int(message.value if hasattr(message, "value") else message),
            "goal_count": len(goals),
            "goal_statuses": [agent.s.node(goal)["attrs"].get("lifecycle_status") for goal in goals],
            "elapsed_ns_instrumented": elapsed_ns,
            "trace_rows": trace_rows,
            "trace_dropped": int(dropped),
            "weighted_trace_event_count": sum(row["count"] for row in trace_rows),
            "static_rules_for_observed_uids": static_rules,
            "observed_uid_static_resolution": sorted({str(uid) for uid in {r["rule_uid"] for r in trace_rows}} - set(index_uid.values())),
            "per_rule_scale_audit_counters": per_rule,
            "aggregate_scale_audit_counters": aggregate,
        })
    graph = agent.s.graph_to_dict()
    finished = lock_inputs()
    return {
        "replicate": replicate,
        "pid": os.getpid(),
        "boot_ns": boot_ns,
        "worker_started_inputs": started,
        "worker_finished_inputs": finished,
        "turns": turns,
        "whole_graph_semantic_sha256": base.semantic_graph_digest(graph),
        "whole_graph_node_count": len(graph.get("nodes", [])),
        "whole_graph_edge_count": len(graph.get("edges", [])),
    }


def scope_isolation_control() -> dict:
    import substrate_rs as sr
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    empty = sr.Substrate()
    target = WorldAdapter(seeds=())
    load_all_seeds(target)
    empty._inner.runtime_access_trace_reset()
    empty._inner.runtime_access_trace_set_enabled(True)
    try:
        target.converse(PROMPTS[0], speech_act="instruction", speaker="alice")
    finally:
        empty._inner.runtime_access_trace_set_enabled(False)
    rows, dropped = empty._inner.runtime_access_trace_snapshot()
    return {"foreign_rows": len(rows), "foreign_drops": int(dropped), "passed": len(rows) == 0 and int(dropped) == 0}


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    locked = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale reconciliation lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    schedule = [0, 1, 2]
    random.Random(20260928).shuffle(schedule)
    runs = []
    for replicate in schedule:
        process = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(replicate)],
                                  cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(process.stdout))
    post = lock_inputs()
    baseline = json.loads(BASE_RAW.read_text())
    base_by_replicate = {int(r["replicate"]): r for r in baseline["runs"]}
    scope_isolation_control_result = scope_isolation_control()
    baseline_parity = all(
        (b := base_by_replicate.get(int(r["replicate"]))) is not None
        and r["whole_graph_semantic_sha256"] == b["whole_graph_semantic_sha256"]
        and all(
            r["turns"][i]["reply_nonempty"] == b["turns"][i]["reply_nonempty"]
            and r["turns"][i]["route"] == b["turns"][i]["route"]
            and r["turns"][i]["goal_count"] == b["turns"][i]["goal_count"]
            for i in (0, 1)
        ) for r in runs
    )
    trace_signatures = [json_sha([t["trace_rows"] for t in r["turns"]]) for r in runs]
    trace_parity = len(set(trace_signatures)) == 1
    checks = {
        "three_fresh_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "worker_and_post_run_source_lock_stable": post == locked and all(r["worker_started_inputs"] == locked == r["worker_finished_inputs"] for r in runs),
        "zero_trace_drops_and_weighted_counts_conserve": all(t["trace_dropped"] == 0 and t["weighted_trace_event_count"] == sum(x["count"] for x in t["trace_rows"]) for r in runs for t in r["turns"]),
        "foreign_scope_isolation": scope_isolation_control_result["passed"],
        "semantic_task_parity_to_baseline": baseline_parity,
        "corrected_trace_parity_across_workers": trace_parity,
    }
    payload = {
        "schema_version": 1,
        "run_id": "term-access-dependency-audit-v1-20260928",
        "claim_boundary": "Corrected trace-isolation and selected static/dynamic access reconciliation for one authored two-prompt task pair. Trace is partial; no absence of events or dependencies is inferred.",
        "locked_inputs": locked,
        "post_run_inputs": post,
        "environment": {"python": sys.version, "platform": platform.platform()},
        "schedule": schedule,
        "checks": checks,
        "baseline_v1_2_sha256": sha(BASE_RAW),
        "scope_isolation_control": scope_isolation_control_result,
        "baseline_run_ids": sorted(int(r["replicate"]) for r in baseline["runs"]),
        "runs": runs,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "checks": checks, "replicates": len(runs)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("access-scope reconciliation capture integrity failed")


if __name__ == "__main__":
    main()
