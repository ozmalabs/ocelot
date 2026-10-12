#!/usr/bin/env python3
"""Paired source-locked work-trace overhead pilot on live describe_scene."""
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
NATIVE_PACKAGE = os.environ.get("SUBSTRATE_NATIVE_PACKAGE")
if not NATIVE_PACKAGE:
    raise SystemExit("set SUBSTRATE_NATIVE_PACKAGE to the extracted substrate_rs wheel package directory")
sys.path[:0] = [str(Path(NATIVE_PACKAGE).resolve().parent), str(ROOT), str(ROOT / "runners/dsl/python")]

from substrate_rs import _native  # noqa: E402
from domains.engine_provenance import rust_source_fingerprint  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_WORK_TRACE_OVERHEAD_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/work_trace_overhead_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/work_trace_overhead_v1_20260928.json"
SOURCES = (
    "runners/dsl/Cargo.toml", "runners/dsl/src/access_trace.rs", "runners/dsl/src/scale_audit.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py", "substrate/world_adapter.py", "substrate/boot_all.py",
    "domains/conversation_action.py", "domains/engine_provenance.py",
    "scripts/substrate_work_trace_overhead_v1.py", "scripts/analyze_work_trace_overhead_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_WORK_TRACE_OVERHEAD_V1_PREREG_20260928.md",
)
EXPECTED = "I see the grey thing stays, the yellow counter, and the blue thing moves."


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    wheel = os.environ.get("SUBSTRATE_NATIVE_WHEEL")
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {name: sha(ROOT / name) for name in SOURCES},
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "native_path": str(native), "native_sha256": sha(native),
        "wheel_path": str(Path(wheel).resolve()) if wheel else None,
        "wheel_sha256": sha(Path(wheel).resolve()) if wheel else None,
        "python": sys.version, "platform": platform.platform(),
    }


def execute_arm(replicate: int, arm: str, position: int) -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene

    adapter = WorldAdapter(seeds=())
    load_all_seeds(adapter)
    attach_scene(adapter, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False},
    ])
    adapter.inner.scale_audit_reset()
    adapter.inner.scale_audit_per_rule_reset()
    adapter.inner.runtime_access_trace_reset()
    adapter.inner.scale_audit_set_enabled(True)
    adapter.inner.scale_audit_set_per_rule_enabled(True)
    tracing = arm == "trace_on"
    _native.Substrate.runtime_work_trace_set_all_scopes_enabled(tracing)
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    try:
        reply = str(adapter.converse("describe what you see", speech_act="instruction", speaker="alice"))
    finally:
        wall_ns = time.perf_counter_ns() - wall_start
        cpu_ns = time.process_time_ns() - cpu_start
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
        adapter.inner.scale_audit_set_per_rule_enabled(False)
        adapter.inner.scale_audit_set_enabled(False)
    counters = {str(k): int(v) for k, v in dict(adapter.inner.scale_audit_snapshot()).items()}
    work_rows, dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
    inbound = getattr(adapter, "_last_turn_inbound", None)
    inbound_attrs = dict(adapter.s.node(inbound)["attrs"]) if inbound is not None else {}
    graph = adapter.s.graph_to_dict()
    outbound = []
    if inbound is not None:
        for message in adapter.s.nodes("Message"):
            attrs = dict(adapter.s.node(message)["attrs"])
            if attrs.get("from") in ("agent", "adapter") and inbound in adapter.inner.neighbours(message, "responds_to"):
                if not attrs.get("turn_reply_suppressed"):
                    outbound.append(attrs.get("text"))
    goals = [goal for goal in adapter.s.nodes("Goal")]
    return {
        "replicate": replicate, "arm": arm, "position": position,
        "reply": reply, "route": inbound_attrs.get("communication_route"),
        "graph_node_count": len(graph.get("nodes", [])), "graph_edge_count": len(graph.get("edges", [])),
        "goal_count": len(goals), "outbound_texts": outbound,
        "request_wall_ns": wall_ns, "request_process_cpu_ns": cpu_ns,
        "scale_counters": counters,
        "work_row_count": len(work_rows), "work_dropped": int(dropped),
        "work_units": sum(int(row[5]) for row in work_rows),
        "work_operation_ids": sorted({int(row[1]) for row in work_rows}),
    }


def worker(replicate: int) -> dict:
    before = fingerprint()
    order = ("trace_off", "trace_on") if replicate in (0, 2) else ("trace_on", "trace_off")
    arms = [execute_arm(replicate, arm, pos) for pos, arm in enumerate(order)]
    after = fingerprint()
    return {"replicate": replicate, "pid": os.getpid(), "before": before, "after": after, "arm_order": list(order), "arms": arms}


def main() -> None:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    if sys.argv[1:2] == ["--lock"]:
        lock = fingerprint()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    locked = fingerprint()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("missing or stale source/native lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs = []
    for replicate in (0, 1, 2):
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(replicate)], cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(cp.stdout))
    after = fingerprint()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({
        "schema_version": 1, "run_id": "work-trace-overhead-v1-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(), "locked_inputs": locked,
        "post_run_inputs": after, "runs": runs,
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": after == locked, "raw": str(RAW.relative_to(ROOT))}, indent=2))
    if after != locked or len({r["pid"] for r in runs}) != 3:
        raise SystemExit("worker or source stability gate failed")


if __name__ == "__main__":
    main()
