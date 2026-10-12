#!/usr/bin/env python3
"""Fresh held-topic capture with per-operation access and work attribution."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NATIVE_PACKAGE = os.environ.get("SUBSTRATE_NATIVE_PACKAGE")
NATIVE_PARENT = str(Path(NATIVE_PACKAGE).resolve().parent) if NATIVE_PACKAGE else None
sys.path[:0] = ([NATIVE_PARENT] if NATIVE_PARENT else []) + [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_STRUCTURAL_TRACE_CAPTURE_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_HELD_TOPIC_STRUCTURAL_TRACE_CAPTURE_V1_AMENDMENT_20260928.md"
ANALYZER = ROOT / "scripts/analyze_substrate_held_topic_structural_trace_capture_v1.py"
BASE_RUNNER = ROOT / "scripts/substrate_live_held_topic_evidence_v1_6.py"
BASE_OUT = ROOT / "evaluation/reports/substrate_live_held_topic_evidence_v1_6_20260926.json"
BASE_RAW = ROOT / "evaluation/reports/substrate_live_held_topic_evidence_v1_6_workers_raw_20260926.json"
BASE_LOCK = ROOT / "evaluation/substrate_capability/live_held_topic_evidence_v1_6_lock_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/held_topic_structural_trace_capture_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/held_topic_structural_trace_capture_v1_20260928.json"
CATEGORY_FIELDS = {"status", "outcome", "kind", "path", "route", "mode", "decision", "role", "state", "source_kind", "local_grounding_outcome"}
FAMILY_CODES = {"rule_edits": 1, "rule_patches": 2, "fb_samples": 3, "track_identity": 4, "net_collapses": 5}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    from scripts import substrate_live_held_topic_evidence_v1_6 as base
    base_lock = json.loads(BASE_LOCK.read_text())["locked_inputs"]
    current_base = base.fingerprint()
    old_closure = base_lock.get("source_closure_sha256", {})
    current_closure = current_base.get("source_closure_sha256", {})
    drift = {
        "added_paths": sorted(set(current_closure) - set(old_closure)),
        "removed_paths": sorted(set(old_closure) - set(current_closure)),
        "changed_hash_paths": sorted(path for path in set(old_closure) & set(current_closure)
                                      if old_closure[path] != current_closure[path]),
        "native_extension_changed": base_lock.get("native_extension_sha256") != current_base.get("native_extension_sha256"),
        "native_build_manifest_changed": base_lock.get("native_build_manifest_sha256") != current_base.get("native_build_manifest_sha256"),
        "base_runner_changed": base_lock.get("runner_sha256") != current_base.get("runner_sha256"),
    }
    return {
        "protocol_sha256": sha(PROTOCOL), "driver_sha256": sha(Path(__file__)),
        "amendment_sha256": sha(AMENDMENT), "analyzer_sha256": sha(ANALYZER), "base_runner_sha256": sha(BASE_RUNNER),
        "base_output_sha256": sha(BASE_OUT), "base_raw_sha256": sha(BASE_RAW),
        "base_lock_sha256": sha(BASE_LOCK), "base_current_fingerprint_sha256": hashlib.sha256(
            json.dumps(current_base, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "base_locked_fingerprint_sha256": hashlib.sha256(
            json.dumps(base_lock, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "base_fingerprint_exact_match": current_base == base_lock,
        "base_fingerprint_drift": drift,
        "native_extension_sha256": sha(Path(_native.__file__).resolve()),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "python": sys.version, "platform": platform.platform(),
    }


def task_attribute_schema(graph: dict, ids: set[int]) -> dict:
    nodes = {int(row["id"]): row for row in graph.get("nodes", [])}
    counts = Counter()
    kinds: dict[str, set[str]] = defaultdict(set)
    categorical: dict[str, set[str]] = defaultdict(set)
    node_rows = []
    for node_id in ids:
        node = nodes.get(node_id)
        if node is None:
            continue
        typ = str(node.get("type", "<missing>"))
        attrs = node.get("attrs", {})
        node_categories = {}
        for key, value in attrs.items():
            token = f"{typ}.{key}"
            counts[token] += 1
            kinds[token].add(type(value).__name__)
            if str(key) in CATEGORY_FIELDS and isinstance(value, (str, bool, int)):
                if len(categorical[token]) < 33:
                    encoded = json.dumps(value, sort_keys=True, default=str)
                    categorical[token].add(encoded)
                    node_categories[str(key)] = encoded
    rows = {}
    for key in sorted(counts):
        values = sorted(categorical.get(key, set()))
        rows[key] = {
            "node_attribute_observations": counts[key],
            "python_value_kinds": sorted(kinds[key]),
            "field_designated_categorical": key.rsplit(".", 1)[-1] in CATEGORY_FIELDS,
            "observed_categorical_value_count_lower_bound": len(values) if key.rsplit(".", 1)[-1] in CATEGORY_FIELDS else None,
            "observed_categorical_values": values if key.rsplit(".", 1)[-1] in CATEGORY_FIELDS and len(values) <= 32 else None,
            "complete_domain_known": False,
        }
    for node_id in sorted(ids):
        node = nodes.get(node_id)
        if node is None:
            continue
        attrs = node.get("attrs", {})
        node_rows.append({
            "node_id": node_id, "node_type": str(node.get("type", "<missing>")),
            "attribute_keys": sorted(map(str, attrs)),
            "attribute_value_kinds": {str(key): type(value).__name__ for key, value in sorted(attrs.items())},
            "observed_categorical_values": {str(key): json.dumps(value, sort_keys=True, default=str)
                                            for key, value in sorted(attrs.items())
                                            if str(key) in CATEGORY_FIELDS and isinstance(value, (str, bool, int))},
        })
    return {"by_type_attribute": rows, "nodes": node_rows}


def graph_digest(graph: dict) -> str:
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def instrumented_measured(agent, operation):
    """Mirror the base timer while adding independent native snapshots outside it."""
    from substrate_rs import _native
    inner = agent.inner
    inner.scale_audit_reset()
    inner.scale_audit_per_rule_reset()
    inner.runtime_access_trace_reset()
    inner.runtime_access_trace_set_enabled(True)
    inner.scale_audit_set_enabled(True)
    inner.scale_audit_set_per_rule_enabled(True)
    _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
    started = time.perf_counter_ns()
    try:
        value = operation()
        elapsed = time.perf_counter_ns() - started
    finally:
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
        inner.runtime_access_trace_set_enabled(False)
        inner.scale_audit_set_per_rule_enabled(False)
        inner.scale_audit_set_enabled(False)
    access_rows, access_dropped = inner.runtime_access_trace_snapshot()
    all_work_rows, work_dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
    per_rule = inner.scale_audit_per_rule_snapshot()
    access_sets = inner.rule_access_sets()
    index_uid = {}
    static_rules = []
    exported = inner.export_rules()
    for idx, name, active, reads, term_edges, writes, reads_any, writes_any in access_sets:
        metadata = inner.rule_metadata(int(idx))
        uid = int(metadata["rule_uid"])
        index_uid[int(idx)] = uid
        static_rules.append({
            "rule_uid": uid, "rule_idx": int(idx), "rule_name": str(name), "active_after_operation": bool(active),
            "reads": sorted(set(map(str, reads))), "term_edge_reads": sorted(set(map(str, term_edges))),
            "writes": sorted(set(map(str, writes))), "reads_any": bool(reads_any), "writes_any": bool(writes_any),
            "match_edges": exported[int(idx)].get("match", []),
        })
    per_rule_by_uid = defaultdict(dict)
    for idx, metric, count in per_rule:
        uid = index_uid.get(int(idx))
        if uid is not None:
            per_rule_by_uid[str(uid)][str(metric)] = int(count)
    scope_counters = _native.Substrate.scale_audit_scoped_work_snapshot_all()
    global_counters = {str(k): int(v) for k, v in dict(inner.scale_audit_snapshot()).items()}
    rows = [{"rule_uid": int(uid), "kind": str(kind), "node": None if node is None else int(node),
             "resource": None if resource is None else str(resource), "peer": None if peer is None else int(peer),
             "count": int(count)} for uid, kind, node, resource, peer, count in access_rows]
    return value, {
        "elapsed_ns": elapsed, "scale_counters": global_counters,
        "access_rows": rows, "access_dropped": int(access_dropped),
        "weighted_access_events": sum(row["count"] for row in rows),
        "all_scope_work_rows": [[int(s), int(op), int(uid), str(kind), None if sub is None else int(sub), int(units)]
                                 for s, op, uid, kind, sub, units in all_work_rows],
        "all_scope_work_dropped": int(work_dropped),
        "all_scope_scale_counters": [[int(s), str(metric), int(units)] for s, metric, units in scope_counters],
        "per_rule_scale_counters": dict(sorted(per_rule_by_uid.items(), key=lambda kv: int(kv[0]))),
        "static_rule_accesses": static_rules,
        "unresolved_access_rule_uids": sorted({row["rule_uid"] for row in rows} - set(index_uid.values())),
    }


def instrumented_frame_projection(agent, inbound, goals, topic, held, evidence, receipts, replies):
    from scripts import substrate_live_held_topic_evidence_v1_6 as base
    frame = base._FRAME_PROJECTION_ORIGINAL(agent, inbound, goals, topic, held, evidence, receipts, replies)
    graph = agent.s.graph_to_dict()
    members = set(map(int, frame["node_ids"]))
    external = {int(edge[2]) if int(edge[0]) in members else int(edge[0]) for edge in frame["boundary_edges"]}
    frame["member_node_type_counts"] = dict(sorted(Counter(
        str(node["type"]) for node in graph.get("nodes", []) if int(node["id"]) in members).items()))
    frame["external_node_type_counts_recomputed"] = dict(sorted(Counter(
        str(node["type"]) for node in graph.get("nodes", []) if int(node["id"]) in external).items()))
    frame["owned_task_attribute_schema"] = task_attribute_schema(graph, members)
    frame["external_boundary_attribute_schema"] = task_attribute_schema(graph, external)
    frame["graph_sha256"] = graph_digest(graph)
    return frame


def worker(replicate: int) -> dict:
    from scripts import substrate_live_held_topic_evidence_v1_6 as base
    started = lock_inputs()
    original_measured = base.measured
    original_projection = base.frame_projection
    base.measured = instrumented_measured
    base._FRAME_PROJECTION_ORIGINAL = original_projection
    base.frame_projection = instrumented_frame_projection
    try:
        result = base.worker(replicate)
    finally:
        base.measured = original_measured
        base.frame_projection = original_projection
        del base._FRAME_PROJECTION_ORIGINAL
    finished = lock_inputs()
    result["driver_started_inputs"] = started
    result["driver_finished_inputs"] = finished
    return result


def main() -> None:
    if sys.argv[1:] == ["--lock"]:
        lock = lock_inputs()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    locked = lock_inputs()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("missing or stale source/native lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs = []
    for replicate in range(3):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(replicate)],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
    post = lock_inputs()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({
        "schema_version": 1, "run_id": "held-topic-structural-trace-capture-v1-20260928",
        "locked_inputs": locked, "post_run_inputs": post,
        "environment": {"python": sys.version, "platform": platform.platform()}, "runs": runs,
    }, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": post == locked,
                      "raw": str(RAW.relative_to(ROOT))}, indent=2))
    if post != locked or len({r["pid"] for r in runs}) != 3 or any(
            r["driver_started_inputs"] != locked or r["driver_finished_inputs"] != locked for r in runs):
        raise SystemExit("capture source lock failed")


if __name__ == "__main__":
    main()
