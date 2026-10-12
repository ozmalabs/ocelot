#!/usr/bin/env python3
"""Source-locked scheduler/deferred operation-work trace fixture."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import tempfile
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

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCHEDULER_WORK_TRACE_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/scheduler_work_trace_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_scheduler_work_trace_v1_20260928.json"
ANALYSIS = ROOT / "evaluation/reports/substrate_scheduler_work_trace_v1_analysis_20260928.json"
SOURCES = (
    "runners/dsl/Cargo.toml",
    "runners/dsl/src/access_trace.rs",
    "runners/dsl/src/scale_audit.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/py.rs",
    "scripts/substrate_scheduler_work_trace_v1.py",
    "scripts/analyze_substrate_scheduler_work_trace_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_SCHEDULER_WORK_TRACE_V1_PREREG_20260928.md",
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
        "native_path": str(native),
        "native_sha256": sha(native),
        "wheel_path": str(Path(wheel).resolve()) if wheel else None,
        "wheel_sha256": sha(Path(wheel).resolve()) if wheel else None,
        "python": sys.version,
        "platform": platform.platform(),
    }


def write_frame(path: Path) -> None:
    width = height = 4
    stride = width * 4
    data = bytearray(64 + width * height * 4)
    data[:4] = (0x4A425746).to_bytes(4, "little")
    data[4:8] = (1).to_bytes(4, "little")
    data[8:12] = width.to_bytes(4, "little")
    data[12:16] = height.to_bytes(4, "little")
    data[16:20] = stride.to_bytes(4, "little")
    data[20:24] = (1).to_bytes(4, "little")
    data[24:32] = (1).to_bytes(8, "little")
    for offset in range(64, len(data), 4):
        data[offset:offset + 4] = bytes((20, 40, 60, 255))
    path.write_bytes(data)


def worker(replicate: int) -> dict:
    before = fingerprint()
    shm_path = Path(f"/dev/shm/ocelot_work_trace_{os.getpid()}_{replicate}")
    write_frame(shm_path)
    try:
        sub = _native.Substrate()
        inner = sub
        fb_id = inner.fb_attach("/" + shm_path.name)
        owner = inner.add_node("Microtheory", {"name": "work_trace_probe"})
        anchor = inner.add_node("QueueAnchor", {})
        target = inner.add_node("QueueTarget", {})
        game = inner.add_node("WorldInstance", {"world_type": "Game", "frame": 0.0, "last_looked_seq": -1.0})
        inner.add_edge_unchecked(owner, "has_concept", anchor)
        inner.add_edge_unchecked(anchor, "trigger", target)
        inner.add_edge_unchecked(anchor, "has_game", game)
        inner.add_edge_unchecked(target, "wants", game)
        inner.add_rule({
            "name": "queue_target",
            "match": [["x", "wants", "g"]],
            "where": {"type": "Lit", "value": False},
            "effects": [["add_edge", "x", "seen", "g", {}]],
        })
        inner.add_rule({
            "name": "queue_writer",
            "match": [["c", "has_concept", "a"], ["a", "trigger", "b"], ["a", "has_game", "g"]],
            "effects": [
                ["set_rule_clause", "queue_target", "where", {"type": "Lit", "value": True}],
                ["fb_sample", fb_id, "g", 2, 2],
                ["del_edge", "a", "trigger", "b"],
            ],
        })

        _native.Substrate.scale_audit_set_enabled(False)
        _native.Substrate.scale_audit_set_per_rule_enabled(False)
        _native.Substrate.scale_audit_reset()
        _native.Substrate.scale_audit_per_rule_reset()
        _native.Substrate.runtime_access_trace_reset()
        _native.Substrate.scale_audit_set_per_rule_enabled(True)
        _native.Substrate.scale_audit_set_enabled(True)
        inner.runtime_access_trace_set_enabled(True)
        started = time.perf_counter_ns()
        report = inner.run_rules_report(10_000, False)
        elapsed_ns = time.perf_counter_ns() - started
        work_rows, work_dropped = inner.runtime_work_trace_snapshot()
        access_rows, access_dropped = inner.runtime_access_trace_snapshot()
        counters = dict(_native.Substrate.scale_audit_snapshot())
        per_rule = [list(row) for row in _native.Substrate.scale_audit_per_rule_snapshot()]
        inner.runtime_access_trace_set_enabled(False)
        _native.Substrate.scale_audit_set_enabled(False)
        _native.Substrate.scale_audit_set_per_rule_enabled(False)

        graph = inner.graph_to_dict()
        edges = graph["edges"]
        grid_cells = sum(node["type"] == "WorldInstance" and "row" in node.get("attrs", {}) for node in graph["nodes"])
        seen_edges = sum(edge["type"] == "seen" for edge in edges)
        after = fingerprint()
        return {
            "replicate": replicate,
            "pid": os.getpid(),
            "before": before,
            "after": after,
            "report": report,
            "elapsed_ns": elapsed_ns,
            "graph_sha256": hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
            "node_count": len(graph["nodes"]),
            "edge_count": len(edges),
            "seen_edges": seen_edges,
            "grid_cells": grid_cells,
            "scale_counters": counters,
            "per_rule_counters": per_rule,
            "work_rows": [list(row) for row in work_rows],
            "work_dropped": work_dropped,
            "access_trace_weighted_events": sum(int(row[5]) for row in access_rows),
            "access_trace_distinct_rows": len(access_rows),
            "access_trace_dropped": access_dropped,
        }
    finally:
        shm_path.unlink(missing_ok=True)


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
    schedule = [0, 1, 2]
    random.Random(20260928).shuffle(schedule)
    env = dict(os.environ)
    runs = []
    for replicate in schedule:
        cp = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", str(replicate)],
            cwd=ROOT, env=env, text=True, capture_output=True, check=True,
        )
        runs.append(json.loads(cp.stdout))
    after = fingerprint()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({
        "schema_version": 1,
        "run_id": "substrate-scheduler-work-trace-v1-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "locked_inputs": locked,
        "post_run_inputs": after,
        "schedule": schedule,
        "runs": runs,
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": after == locked, "raw": str(RAW.relative_to(ROOT))}, indent=2))


if __name__ == "__main__":
    main()
