#!/usr/bin/env python3
"""Paired fresh-process scheduler work-trace instrumentation overhead panel."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = os.environ.get("SUBSTRATE_NATIVE_PACKAGE")
if not PACKAGE:
    raise SystemExit("set SUBSTRATE_NATIVE_PACKAGE to the extracted substrate_rs package directory")
sys.path[:0] = [str(Path(PACKAGE).resolve().parent), str(ROOT), str(ROOT / "runners/dsl/python")]
from substrate_rs import _native  # noqa: E402
from domains.engine_provenance import rust_source_fingerprint  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_LIVE_SCHEDULER_TRACE_OVERHEAD_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/live_scheduler_trace_overhead_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/live_scheduler_trace_overhead_v1_20260928.json"
ANALYZER = ROOT / "scripts/analyze_substrate_live_scheduler_trace_overhead_v1.py"
SOURCES = (
    "runners/dsl/Cargo.toml", "runners/dsl/src/access_trace.rs", "runners/dsl/src/scale_audit.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/python/substrate_rs/__init__.py", "substrate/world_adapter.py", "substrate/boot_all.py",
    "domains/conversation_action.py", "domains/engine_provenance.py",
    "scripts/substrate_live_scheduler_trace_overhead_v1.py", str(PROTOCOL.relative_to(ROOT)),
    str(ANALYZER.relative_to(ROOT)),
)
EXPECTED = "I see the grey thing stays, the yellow counter, and the blue thing moves."
ARMS = ("baseline", "counters", "counters_work_trace")
ORDERS = (ARMS, ("counters", "counters_work_trace", "baseline"),
          ("counters_work_trace", "baseline", "counters"))
SCHEDULER_KEYS = {
    "scheduler_passes", "scheduler_external_poll_slots", "scheduler_fixedpoint_probe_slots",
    "scheduler_dirty_vector_slots", "scheduler_selected_rules",
}


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


def worker(arm: str, replicate: int, order_index: int) -> dict:
    if arm not in ARMS:
        raise ValueError(arm)
    before = fingerprint()
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from domains.conversation_action import attach_scene

    boot_t0 = time.perf_counter_ns()
    adapter = WorldAdapter(seeds=())
    load_all_seeds(adapter)
    attach_scene(adapter, [
        {"kind": "static", "colour": "grey"},
        {"kind": "meter", "colour": "yellow"},
        {"kind": "mover", "colour": "blue", "responds_to_my_action": False},
    ])
    boot_ns = time.perf_counter_ns() - boot_t0
    adapter.inner.scale_audit_reset()
    adapter.inner.scale_audit_per_rule_reset()
    adapter.inner.runtime_access_trace_reset()
    instrumented = arm != "baseline"
    work_enabled = arm == "counters_work_trace"
    adapter.inner.scale_audit_set_enabled(instrumented)
    adapter.inner.scale_audit_set_per_rule_enabled(instrumented)
    _native.Substrate.runtime_work_trace_set_all_scopes_enabled(work_enabled)
    try:
        t0 = time.perf_counter_ns()
        reply = str(adapter.converse("describe what you see", speech_act="instruction", speaker="alice"))
        converse_ns = time.perf_counter_ns() - t0
    finally:
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
        adapter.inner.scale_audit_set_per_rule_enabled(False)
        adapter.inner.scale_audit_set_enabled(False)
    work_rows, work_dropped = adapter.inner.runtime_work_trace_snapshot()
    all_work_rows, all_work_dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
    scale = {str(k): int(v) for k, v in dict(adapter.inner.scale_audit_snapshot()).items()}
    scoped_scale = {str(k): int(v) for k, v in adapter.inner.scale_audit_scoped_work_snapshot()}
    all_scoped_scale = _native.Substrate.scale_audit_scoped_work_snapshot_all()
    graph = adapter.s.graph_to_dict()
    nodes = []
    for node in graph.get("nodes", []):
        attrs = dict(node.get("attrs", {}))
        if node.get("type") == "SystemModel":
            attrs.pop("ts", None)
            attrs.pop("runtime_s", None)
        nodes.append({"id": node["id"], "type": node["type"], "attrs": attrs})
    semantic = {"nodes": nodes, "edges": graph.get("edges", [])}
    after = fingerprint()
    record = {
        "arm": arm, "replicate": replicate, "order_index": order_index, "pid": os.getpid(),
        "before": before, "after": after, "boot_ns": boot_ns, "converse_ns": converse_ns,
        "rss_peak_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "reply": reply,
        "semantic_graph_sha256": hashlib.sha256(json.dumps(semantic, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest(),
        "node_count": len(graph.get("nodes", [])), "edge_count": len(graph.get("edges", [])),
        "scale_counters": scale, "scoped_scale_counters": scoped_scale,
        "work_rows": [list(row) for row in work_rows], "work_dropped": int(work_dropped),
        "all_scope_work_rows": [list(row) for row in all_work_rows],
        "all_scope_work_dropped": int(all_work_dropped),
        "all_scope_scale_counters": [list(row) for row in all_scoped_scale],
    }
    adapter.close()
    return record


def main() -> None:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), int(sys.argv[4])), sort_keys=True, default=str))
        return
    if sys.argv[1:2] == ["--lock"]:
        lock = fingerprint()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    locked = fingerprint()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("missing or stale source/native lock; capture a lock first")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs = []
    for replicate, order in enumerate(ORDERS):
        for order_index, arm in enumerate(order):
            cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", arm,
                                 str(replicate), str(order_index)], cwd=ROOT, env=env,
                                text=True, capture_output=True, check=True)
            runs.append(json.loads(cp.stdout))
            print(f"replicate={replicate} arm={arm} converse_ns={runs[-1]['converse_ns']}", flush=True)
    after = fingerprint()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({
        "schema_version": 1, "run_id": "live-scheduler-trace-overhead-v1-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(), "locked_inputs": locked,
        "post_run_inputs": after, "arm_order": [list(x) for x in ORDERS], "runs": runs,
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": after == locked,
                      "raw": str(RAW.relative_to(ROOT))}, indent=2))
    if after != locked or len({r["pid"] for r in runs}) != len(runs):
        raise SystemExit("worker uniqueness or source stability gate failed")


if __name__ == "__main__":
    main()
