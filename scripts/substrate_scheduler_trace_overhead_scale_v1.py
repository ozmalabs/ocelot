#!/usr/bin/env python3
"""Paired audit/work-trace overhead sweep on native positive scheduler fixtures."""
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

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCHEDULER_TRACE_OVERHEAD_SCALE_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/scheduler_trace_overhead_scale_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/scheduler_trace_overhead_scale_v1_20260928.json"
SIZES = (8, 32, 128)
ORDERS = (
    ("baseline", "audit_only", "trace_only", "audit_and_trace"),
    ("audit_and_trace", "trace_only", "audit_only", "baseline"),
    ("audit_only", "baseline", "audit_and_trace", "trace_only"),
)
SOURCES = (
    "runners/dsl/Cargo.toml", "runners/dsl/src/access_trace.rs", "runners/dsl/src/scale_audit.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "scripts/substrate_scheduler_trace_overhead_scale_v1.py",
    "scripts/analyze_substrate_scheduler_trace_overhead_scale_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_SCHEDULER_TRACE_OVERHEAD_SCALE_V1_PREREG_20260928.md",
)


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


def build_fixture(n: int):
    sub = _native.Substrate()
    left = sub.add_node("SchedulerTraceNode", {})
    right = sub.add_node("SchedulerTraceNode", {})
    for i in range(n):
        sub.add_rule({
            "name": f"scheduler_trace_rule_{i}",
            "match": [["x", f"trace_trigger_{i}", "y"]],
            "effects": [["add_edge", "x", f"trace_derived_{i}", "y", {}]],
        })
        sub.add_edge_unchecked(left, f"trace_trigger_{i}", right)
    return sub


def run_arm(n: int, arm: str, position: int, replicate: int) -> dict:
    sub = build_fixture(n)
    audit = arm in ("audit_only", "audit_and_trace")
    trace = arm in ("trace_only", "audit_and_trace")
    _native.Substrate.scale_audit_reset()
    _native.Substrate.scale_audit_per_rule_reset()
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.scale_audit_set_enabled(audit)
    _native.Substrate.scale_audit_set_per_rule_enabled(audit)
    _native.Substrate.runtime_work_trace_set_all_scopes_enabled(trace)
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    try:
        report = sub.run_rules_report(10_000, False)
    finally:
        wall_ns = time.perf_counter_ns() - wall_start
        cpu_ns = time.process_time_ns() - cpu_start
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
        _native.Substrate.scale_audit_set_per_rule_enabled(False)
        _native.Substrate.scale_audit_set_enabled(False)
    graph = sub.graph_to_dict()
    counters = {str(k): int(v) for k, v in dict(_native.Substrate.scale_audit_snapshot()).items()}
    rows, dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
    triggers = sum(edge["type"].startswith("trace_trigger_") for edge in graph["edges"])
    derived = sum(edge["type"].startswith("trace_derived_") for edge in graph["edges"])
    graph_hash = hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()
    return {
        "replicate": replicate, "rule_count": n, "arm": arm, "position": position,
        "report": {key: report[key] for key in ("status", "progress_steps", "passes_completed", "budget_overshoot")},
        "trigger_edges": triggers, "derived_edges": derived, "node_count": len(graph["nodes"]),
        "edge_count": len(graph["edges"]), "graph_sha256": graph_hash,
        "request_wall_ns": wall_ns, "request_process_cpu_ns": cpu_ns,
        "scale_counters": counters,
        "work_rows": [list(row) for row in rows], "work_row_count": len(rows),
        "work_units": sum(int(row[5]) for row in rows), "work_dropped": int(dropped),
    }


def worker(replicate: int) -> dict:
    before = fingerprint()
    runs = []
    for size_index, n in enumerate(SIZES):
        rotation = (replicate + size_index) % 3
        base = list(ORDERS[replicate])
        order = base[rotation:] + base[:rotation]
        for position, arm in enumerate(order):
            runs.append(run_arm(n, arm, position, replicate))
    after = fingerprint()
    return {"replicate": replicate, "pid": os.getpid(), "before": before, "after": after, "runs": runs}


def main() -> None:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True))
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
    runs = []
    for replicate in (0, 1, 2):
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(replicate)], cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(cp.stdout))
    after = fingerprint()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({
        "schema_version": 1, "run_id": "scheduler-trace-overhead-scale-v1-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(), "locked_inputs": locked,
        "post_run_inputs": after, "runs": runs,
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": after == locked, "raw": str(RAW.relative_to(ROOT))}, indent=2))
    if after != locked or len({row["pid"] for row in runs}) != 3 or any(row["before"] != locked or row["after"] != locked for row in runs):
        raise SystemExit("worker or source stability gate failed")


if __name__ == "__main__":
    main()
