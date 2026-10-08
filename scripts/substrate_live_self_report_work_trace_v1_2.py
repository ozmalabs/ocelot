#!/usr/bin/env python3
"""All-scope scheduler-work and matcher accounting on live self-report tasks."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
from substrate_rs import _native  # noqa: E402
from domains.engine_provenance import build_is_stale, rust_source_fingerprint  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_WORK_TRACE_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_WORK_TRACE_V1_1_AMENDMENT_20260928.md"
AMENDMENT_V1_2 = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_SELF_REPORT_WORK_TRACE_V1_2_AMENDMENT_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/live_self_report_work_trace_v1_2_lock_20260928.json"
RAW = ROOT / "evaluation/reports/live_self_report_work_trace_v1_2_20260928.json"
ANALYZER = ROOT / "scripts/analyze_substrate_live_self_report_work_trace_v1_2.py"
PROMPTS = ("report your organisation", "describe who you are")
TARGETS = ("self_organisation", "self_identity")
SOURCES = (
    "runners/dsl/Cargo.toml", "runners/dsl/src/access_trace.rs", "runners/dsl/src/scale_audit.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py", "substrate/world_adapter.py", "substrate/boot_all.py",
    "domains/conversation_action.py", "domains/discourse_state.py", "domains/reflective_faculty.py",
    "domains/engine_provenance.py", "seeds/conversation_discourse_state.json",
    "scripts/substrate_live_self_report_work_trace_v1_2.py",
    "scripts/analyze_substrate_live_self_report_work_trace_v1_2.py",
    "scripts/materialize_self_report_work_trace_snapshot_v1_2.py",
    str(PROTOCOL.relative_to(ROOT)), str(AMENDMENT.relative_to(ROOT)),
    str(AMENDMENT_V1_2.relative_to(ROOT)),
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def nid(value) -> int:
    return int(value.value if hasattr(value, "value") else value)


def source_closure() -> dict[str, str]:
    paths: set[Path] = set()
    for folder in (ROOT / "domains", ROOT / "substrate", ROOT / "runners/dsl/python"):
        paths.update(p for p in folder.rglob("*.py") if "__pycache__" not in p.parts)
    seed_dir = ROOT / "seeds"
    paths.update(seed_dir.glob("*.json"))
    paths.update((seed_dir / "generated").glob("*.json"))
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}


def lock_inputs() -> dict:
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"native engine is stale relative to Rust sources: {stale[:5]}")
    native = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protocol_sha256": sha(PROTOCOL),
        "source_sha256": {p: sha(ROOT / p) for p in SOURCES},
        "source_closure_sha256": source_closure(),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "native_extension_path": str(native), "native_extension_sha256": sha(native),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "python": sys.version, "platform": platform.platform(),
    }


def semantic_digest(adapter) -> tuple[str, int, int]:
    graph = adapter.s.graph_to_dict()
    nodes = []
    for node in graph.get("nodes", []):
        attrs = dict(node.get("attrs", {}))
        if node.get("type") == "SystemModel":
            attrs.pop("ts", None)
            attrs.pop("runtime_s", None)
        nodes.append({"id": node["id"], "type": node["type"], "attrs": attrs})
    payload = {"nodes": nodes, "edges": graph.get("edges", [])}
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    return digest, len(graph.get("nodes", [])), len(graph.get("edges", []))


def worker(replicate: int) -> dict:
    started = lock_inputs()
    frozen = json.loads(LOCK.read_text())
    if started != frozen:
        raise SystemExit("worker start fingerprint differs from frozen lock; refusing capture")
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds

    adapter = WorldAdapter(seeds=())
    load_all_seeds(adapter)
    turns = []
    for turn, prompt in enumerate(PROMPTS):
        adapter.inner.scale_audit_reset()
        adapter.inner.scale_audit_per_rule_reset()
        adapter.inner.runtime_access_trace_reset()
        adapter.inner.scale_audit_set_enabled(True)
        adapter.inner.scale_audit_set_per_rule_enabled(True)
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(True)
        t0 = time.perf_counter_ns()
        try:
            reply = str(adapter.converse(prompt, speech_act="instruction", speaker="alice"))
            elapsed = time.perf_counter_ns() - t0
        finally:
            _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
            adapter.inner.scale_audit_set_per_rule_enabled(False)
            adapter.inner.scale_audit_set_enabled(False)
        scale = {str(k): int(v) for k, v in dict(adapter.inner.scale_audit_snapshot()).items()}
        per_rule = [[int(i), str(metric), int(n)] for i, metric, n in adapter.inner.scale_audit_per_rule_snapshot()]
        per_clause = [[int(i), int(pos), int(n)] for i, pos, n in adapter.inner.scale_audit_match_clause_snapshot()]
        metadata = [[int(i), int(sym), str(name), int(arity), bool(amb)]
                    for i, sym, name, arity, amb in adapter.inner.scale_audit_rule_metadata_snapshot()]
        global_work, global_dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
        scoped_work = _native.Substrate.scale_audit_scoped_work_snapshot_all()
        message = adapter._last_turn_inbound
        message_attrs = adapter.s.node(message)["attrs"]
        origin = message_attrs.get("discourse_event_id")
        state = message_attrs.get("discourse_state_id")
        goals = [g for g in adapter.s.nodes("Goal") if message in adapter.inner.neighbours(g, "comprehends")]
        goal = goals[0] if len(goals) == 1 else None
        if goal is not None:
            ga = adapter.s.node(goal)["attrs"]
            event_ids = list(adapter.inner.neighbours(goal, "transitioned_by"))
            event_ids.sort(key=lambda e: int(adapter.s.node(e)["attrs"].get("event_index", -1)))
            event_kinds = [adapter.s.node(e)["attrs"].get("kind") for e in event_ids]
            all_bound = all(goal in adapter.inner.neighbours(e, "for_goal") for e in event_ids)
            closed = any(goal in adapter.inner.neighbours(s, "has_closed_goal") for s in adapter.s.nodes("DiscourseState"))
            active = any(goal in adapter.inner.neighbours(s, "has_active_goal") for s in adapter.s.nodes("DiscourseState"))
            goal_record = {"id": nid(goal), "status": ga.get("lifecycle_status"),
                           "self_target": ga.get("self_target"), "event_kinds": event_kinds,
                           "all_transitions_bound": all_bound, "closed": closed, "active": active,
                           "origin_linked": origin in adapter.inner.neighbours(goal, "originated_in")}
        else:
            event_ids, event_kinds, goal_record = [], [], None
        digest, node_count, edge_count = semantic_digest(adapter)
        turns.append({
            "turn": turn, "prompt": prompt, "expected_self_target": TARGETS[turn],
            "elapsed_ns": elapsed, "reply": reply, "reply_nonempty": bool(reply),
            "route": message_attrs.get("communication_route"), "message_id": nid(message),
            "origin_event_id": nid(origin) if origin is not None else None,
            "goal_count": len(goals), "goal": goal_record,
            "lifecycle_event_ids": [nid(x) for x in event_ids], "lifecycle_event_kinds": event_kinds,
            "semantic_graph_sha256": digest, "node_count": node_count, "edge_count": edge_count,
            "scale_counters": scale, "per_rule": per_rule, "per_clause": per_clause,
            "rule_metadata": metadata,
            "all_scope_work_rows": [list(row) for row in global_work],
            "all_scope_work_dropped": int(global_dropped),
            "all_scope_scale_counters": [list(row) for row in scoped_work],
        })
    finished = lock_inputs()
    adapter.close()
    return {"replicate": replicate, "pid": os.getpid(), "worker_started_inputs": started,
            "worker_finished_inputs": finished, "turns": turns}


def main() -> None:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    if sys.argv[1:2] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or raw output")
        lock = lock_inputs()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    if RAW.exists():
        raise SystemExit("refusing to overwrite raw capture")
    locked = lock_inputs()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("missing or stale source/native lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs = []
    for rep in (0, 1, 2):
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
                            cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(cp.stdout))
        print(f"replicate={rep} routes={[t['route'] for t in runs[-1]['turns']]}", flush=True)
        if runs[-1]["worker_started_inputs"] != locked or runs[-1]["worker_finished_inputs"] != locked:
            post = lock_inputs()
            RAW.parent.mkdir(parents=True, exist_ok=True)
            RAW.write_text(json.dumps({"schema_version": 1, "capture_status": "censored_source_drift",
                "run_id": "live-self-report-work-trace-v1_2-20260928", "locked_inputs": locked,
                "post_run_inputs": post, "runs": runs}, indent=2, sort_keys=True, default=str) + "\n")
            raise SystemExit("source drift during worker; captured prefix preserved and later workers stopped")
    post = lock_inputs()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    status = "complete" if post == locked else "censored_source_drift"
    RAW.write_text(json.dumps({
        "schema_version": 1, "capture_status": status, "run_id": "live-self-report-work-trace-v1_2-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(), "locked_inputs": locked,
        "post_run_inputs": post, "runs": runs,
    }, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": post == locked,
                      "raw": str(RAW.relative_to(ROOT))}, indent=2))
    if status != "complete" or len({r["pid"] for r in runs}) != 3:
        raise SystemExit("fresh-process or source-stability gate failed")


if __name__ == "__main__":
    main()
