#!/usr/bin/env python3
"""Fresh paired task-derived Bigville frame/access diagnostic."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_BIGVILLE_TASK_ACCESS_CENSUS_PREREG_20260926.md"
LOCK = ROOT / "evaluation/substrate_capability/bigville_task_access_census_lock_20260926.json"
OUT = ROOT / "evaluation/reports/substrate_bigville_task_access_census_v1_20260926.json"
BASE_RUNNER = ROOT / "scripts/substrate_bigville_can_runtime_partition_replay_v3_1.py"
CAST = ROOT / "seeds/bigville_cast100.json"
SEED = ROOT / "seeds/can_native_reimplementation.json"
BUILDER = ROOT / "worlds/bigville_can_beliefs.py"
RULE = "can_native_update_3state"
# Chosen after the resident-0 no-op diagnostic showed zero rule firings. The
# existing replay reports nonzero settlement for resident 40; retain this as
# post-hoc diagnostic selection, not a confirmatory task sample.
TARGET = 40
CAP = 100_000
WRITE_KINDS = {"effect_attr_write", "effect_edge_upsert", "effect_edge_delete",
               "effect_node_mint", "effect_node_delete", "effect_replace_edge"}
READ_KINDS = {"pattern_edge", "term_attr_read", "term_type_read", "term_edge_read",
              "term_edge_attr_read", "term_index_query", "jit_attr_read", "jit_type_read"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_base():
    spec = importlib.util.spec_from_file_location("bigville_task_access_base", BASE_RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load registered Bigville replay helper")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def locked_inputs() -> dict:
    from substrate_rs import _native
    native = Path(_native.__file__).resolve()
    return {
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(Path(__file__)),
        "base_runner_sha256": sha(BASE_RUNNER),
        "cast_sha256": sha(CAST),
        "seed_sha256": sha(SEED),
        "builder_sha256": sha(BUILDER),
        "native_extension_sha256": sha(native),
        "native_extension_path": str(native),
        "rust_sources_sha256": {
            name: sha(ROOT / "runners/dsl/src" / name)
            for name in ("graph.rs", "rewrite.rs", "substrate.rs", "term.rs", "access_trace.rs", "py.rs")
        },
    }


def graph_digest(inner) -> str:
    raw = inner.graph_to_dict()
    packed = json.dumps(raw, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(packed).hexdigest()


def run_arm(base, sr, cast, seed, bigville, *, policy: str, traced: bool) -> dict:
    build_start = time.perf_counter_ns()
    (outer, inner, residents, mts, concepts, frame_nodes, node_frame, edges, cross,
     ref_by_id, node_flat) = base.build(sr, cast, seed, bigville)
    build_ns = time.perf_counter_ns() - build_start
    if len(frame_nodes) != len(cast) or set(map(len, frame_nodes)) != {5}:
        raise RuntimeError("runtime-derived Bigville ownership did not produce 100 five-Concept frames")
    if cross:
        raise RuntimeError("authored baseline unexpectedly contains cross-frame causal edges")

    # Reconstruct ownership and dependency relation from the live graph while
    # timing that operation separately from graph/rule/task construction.
    partition_start = time.perf_counter_ns()
    owner_pairs = []
    for node, frame in sorted(node_frame.items()):
        owner_pairs.append([int(node), int(frame)])
    dependency_edges = [[int(a), int(b)] for a, b in edges]
    partition_ns = time.perf_counter_ns() - partition_start

    initial = base.settle_full(inner, mts)
    if not initial["complete"]:
        raise RuntimeError("full baseline failed to settle")
    inner.runtime_access_trace_set_enabled(False)
    inner.runtime_access_trace_reset()
    target_scope = mts[TARGET]
    base.mutate(inner, concepts, residents, bigville, TARGET)

    if traced:
        inner.runtime_access_trace_set_enabled(True)
    wall_start, cpu_start = time.perf_counter_ns(), time.process_time_ns()
    if policy == "full":
        settlement = base.settle_full(inner, mts, audit=True)
    elif policy == "event":
        settlement = base.settle_event(
            inner, mts, frame_nodes, node_frame, edges, ref_by_id, {TARGET}, audit=True)
    else:
        raise ValueError(policy)
    wall_ns, cpu_ns = time.perf_counter_ns() - wall_start, time.process_time_ns() - cpu_start
    inner.runtime_access_trace_set_enabled(False)
    trace_rows, dropped = inner.runtime_access_trace_snapshot()

    state = base.states(inner, concepts)
    field_rows = base.fields(inner, concepts)
    weights = base.weights_by_id(concepts, residents, bigville, node_flat)
    residual_count = sum(base.residuals(state, field_rows, weights))
    rules = inner.rule_access_sets()
    rule_meta = []
    for index, name, active, reads, term_edges, writes, reads_any, writes_any in rules:
        if name == RULE:
            rule_meta.append({"name": name, "index": int(index), "active": bool(active),
                              "reads": sorted(set(reads) | set(term_edges)),
                              "writes": sorted(writes), "reads_any": bool(reads_any),
                              "writes_any": bool(writes_any),
                              "uid": int(inner.rule_metadata(index)["rule_uid"])})
    if len(rule_meta) != 1:
        raise RuntimeError("native loaded rule inventory lacks unique target rule")

    frames = {int(node): int(frame) for node, frame in owner_pairs}
    event_records = []
    event_frame_ids = set()
    cross_frame_events = []
    for uid, kind, node, resource_name, peer, count in trace_rows:
        node_frame_id = frames.get(int(node)) if node is not None else None
        peer_frame_id = frames.get(int(peer)) if peer is not None else None
        row = {"rule_uid": int(uid), "kind": kind, "node": node,
               "resource": resource_name, "peer": peer, "count": int(count),
               "node_frame": node_frame_id, "peer_frame": peer_frame_id}
        event_records.append(row)
        if node_frame_id is not None:
            event_frame_ids.add(node_frame_id)
        if peer_frame_id is not None:
            event_frame_ids.add(peer_frame_id)
        if node_frame_id is not None and peer_frame_id is not None and node_frame_id != peer_frame_id:
            cross_frame_events.append(row)

    return {
        "policy": policy, "traced": traced,
        "pid": os.getpid(),
        "build_plus_runtime_partition_ns": build_ns,
        "partition_map_materialization_ns": partition_ns,
        "initial_full_closure": initial,
        "settlement": settlement,
        "settlement_wall_ns": wall_ns, "settlement_cpu_ns": cpu_ns,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "graph_digest": graph_digest(inner), "independent_residual_count": residual_count,
        "frame_count": len(frame_nodes), "frame_sizes": [len(x) for x in frame_nodes],
        "runtime_node_frame": owner_pairs,
        "runtime_dependency_edges": dependency_edges,
        "cross_frame_dependency_edge_count": len(cross),
        "static_rule_access": rule_meta[0],
        "runtime_access_events": event_records,
        "runtime_event_count": sum(row[5] for row in trace_rows),
        "runtime_distinct_event_count": len(trace_rows),
        "runtime_trace_dropped": int(dropped),
        "runtime_observed_frame_ids": sorted(event_frame_ids),
        "runtime_cross_frame_events": cross_frame_events,
        "observed_reads": sum(row["count"] for row in event_records if row["kind"] in READ_KINDS),
        "observed_writes": sum(row["count"] for row in event_records if row["kind"] in WRITE_KINDS),
        "target_scope_id": int(target_scope.value if hasattr(target_scope, "value") else target_scope),
        "external_mutation_target_frame": TARGET,
    }


def main() -> None:
    if len(sys.argv) == 2 and sys.argv[1] == "--lock":
        print(json.dumps({"locked_inputs": locked_inputs()}, indent=2, sort_keys=True))
        return
    current = locked_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text()).get("locked_inputs") != current:
        raise SystemExit("missing or stale lock; inspect --lock output before execution")
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        from substrate_rs import _native  # noqa: F401
        import substrate_rs as sr
        from worlds import bigville_can_beliefs as bigville
        base = load_base()
        cast = json.loads(CAST.read_text())["residents"]
        seed = json.loads(SEED.read_text())
        if len(cast) != 100:
            raise RuntimeError("registered Bigville cast must contain 100 residents")
        policy, trace_flag = sys.argv[2].split(":", 1)
        row = run_arm(base, sr, cast, seed, bigville, policy=policy,
                      traced=(trace_flag == "trace"))
        print(json.dumps(row, sort_keys=True))
        return

    from substrate_rs import _native
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs = []
    for policy, trace_flag in (("full", "plain"), ("event", "plain"), ("event", "trace")):
        proc = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", f"{policy}:{trace_flag}"],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True,
        )
        runs.append(json.loads(proc.stdout))
    full, event_plain, event_trace = runs
    checks = {
        "runtime_derived_100_five_concept_frames": all(
            row["frame_count"] == 100 and set(row["frame_sizes"]) == {5} for row in runs),
        "fresh_process_per_arm": len({row["pid"] for row in runs}) == 3,
        "authored_partition_has_no_cross_frame_causal_edges": all(
            row["cross_frame_dependency_edge_count"] == 0 for row in runs),
        "all_settlements_complete": all(row["settlement"]["complete"] for row in runs),
        "full_and_event_graph_digest_equal": full["graph_digest"] == event_plain["graph_digest"],
        "trace_on_off_event_graph_digest_equal": event_plain["graph_digest"] == event_trace["graph_digest"],
        "event_independent_residual_zero": event_plain["independent_residual_count"] == 0,
        "trace_emits_events_without_drops": event_trace["runtime_event_count"] > 0 and event_trace["runtime_trace_dropped"] == 0,
        "event_trace_observes_target_frame": TARGET in event_trace["runtime_observed_frame_ids"],
        "event_arm_makes_progress": event_plain["settlement"]["steps"] > 0,
        "trace_arm_makes_progress": event_trace["settlement"]["steps"] > 0,
        "event_trace_has_no_cross_frame_events": len(event_trace["runtime_cross_frame_events"]) == 0,
    }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-bigville-task-access-census-v1-20260926",
        "claim_boundary": (
            "Fresh diagnostic trace of one authored Bigville resident update on its existing 100-frame workload. "
            "The dynamic access trace is partial; zero observed cross-frame events is not proof that no dependencies exist. "
            "This is not an independent task family, representative-distribution estimate, boundary-aware scheduler, or speed claim."
        ),
        "input_lock_sha256": sha(LOCK), "locked_inputs": current,
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "OZMA_NO_LLM": os.environ.get("OZMA_NO_LLM"),
                        "OZMA_SEED_PERSIST_DISABLED": os.environ.get("OZMA_SEED_PERSIST_DISABLED"),
                        "native_extension_path": str(Path(_native.__file__).resolve())},
        "checks": checks,
        "summary": {"frame_count": event_trace["frame_count"],
                    "target_frame": TARGET,
                    "dependency_edges": len(event_trace["runtime_dependency_edges"]),
                    "cross_frame_dependency_edges": event_trace["cross_frame_dependency_edge_count"],
                    "observed_runtime_events": event_trace["runtime_event_count"],
                    "distinct_runtime_events": event_trace["runtime_distinct_event_count"],
                    "observed_reads": event_trace["observed_reads"],
                    "observed_writes": event_trace["observed_writes"],
                    "observed_frames": event_trace["runtime_observed_frame_ids"],
                    "trace_arm_wall_ns": event_trace["settlement_wall_ns"],
                    "untraced_arm_wall_ns": event_plain["settlement_wall_ns"],
                    "full_arm_wall_ns": full["settlement_wall_ns"]},
        "runs": runs,
        "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                       "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
                       "native_extension_sha256": sha(Path(_native.__file__).resolve()),
                       "command": "PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_bigville_task_access_census_v1.py"},
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "checks": checks, "summary": payload["summary"]}, indent=2))
    if not all(checks.values()):
        raise SystemExit("task-derived access census checks failed; raw report preserved")


if __name__ == "__main__":
    main()
