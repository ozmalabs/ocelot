#!/usr/bin/env python3
"""Mutation-to-fixpoint trace overhead factorial on native synthetic fixtures."""
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

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_MUTATION_CLOSURE_TRACE_OVERHEAD_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/mutation_closure_trace_overhead_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/mutation_closure_trace_overhead_v1_20260928.json"
SIZES = (8, 32, 128)
FAMILIES = ("sparse", "matcher_dense")
ARMS = ("baseline", "audit_only", "trace_only", "audit_and_trace")
REPEATS = 32
DENSE_DEGREE = 8
ORDERS = (ARMS, ("audit_and_trace", "trace_only", "audit_only", "baseline"),
          ("audit_only", "baseline", "audit_and_trace", "trace_only"))
SOURCES = (
    "runners/dsl/Cargo.toml", "runners/dsl/src/access_trace.rs", "runners/dsl/src/scale_audit.rs",
    "runners/dsl/src/substrate.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "scripts/substrate_mutation_closure_trace_overhead_v1.py",
    "scripts/analyze_substrate_mutation_closure_trace_overhead_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_MUTATION_CLOSURE_TRACE_OVERHEAD_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_MUTATION_CLOSURE_TRACE_OVERHEAD_V1_AMENDMENT_20260928.md",
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


def build_fixture(n: int, family: str):
    sub = _native.Substrate()
    if family == "sparse":
        left = sub.add_node("MutationTraceNode", {})
        right = sub.add_node("MutationTraceNode", {})
        for i in range(n):
            sub.add_rule({
                "name": f"mutation_sparse_rule_{i}",
                "match": [["x", f"sparse_trigger_{i}", "y"]],
                "effects": [["add_edge", "x", f"sparse_derived_{i}", "y", {}]],
            })
        return sub, (left, "sparse_trigger_0", right), 1

    degree = DENSE_DEGREE
    for i in range(n):
        x = sub.add_node("MutationTraceNode", {})
        ys = [sub.add_node("MutationTraceNode", {}) for _ in range(degree)]
        zs = [sub.add_node("MutationTraceNode", {}) for _ in range(degree)]
        sub.add_rule({
            "name": f"mutation_dense_rule_{i}",
            "match": [["x", f"dense_a_{i}", "y"], ["x", f"dense_b_{i}", "z"]],
            "effects": [["add_edge", "x", f"dense_derived_{i}", "z", {}]],
        })
        if i == 0:
            for y in ys[:-1]:
                sub.add_edge_unchecked(x, f"dense_a_{i}", y)
            for z in zs:
                sub.add_edge_unchecked(x, f"dense_b_{i}", z)
            missing = (x, f"dense_a_{i}", ys[-1])
    return sub, missing, degree


def digest_graph(sub) -> str:
    graph = sub.graph_to_dict()
    return hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def run_cell(n: int, family: str, arm: str, position: int, replicate: int) -> dict:
    fixtures = [build_fixture(n, family) for _ in range(REPEATS)]
    audit = arm in ("audit_only", "audit_and_trace")
    trace = arm in ("trace_only", "audit_and_trace")
    _native.Substrate.scale_audit_reset()
    _native.Substrate.scale_audit_per_rule_reset()
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.scale_audit_set_enabled(audit)
    _native.Substrate.scale_audit_set_per_rule_enabled(audit)
    _native.Substrate.runtime_work_trace_set_all_scopes_enabled(trace)
    reports, graph_digests, derived_counts = [], [], []
    wall_start = time.perf_counter_ns()
    cpu_start = time.process_time_ns()
    try:
        for sub, trigger, expected_derived in fixtures:
            sub.add_edge_unchecked(*trigger)
            report = sub.run_rules_report(100_000, False)
            reports.append({key: report[key] for key in ("status", "progress_steps", "passes_completed", "budget_overshoot")})
            graph_digests.append(digest_graph(sub))
            graph = sub.graph_to_dict()
            derived_counts.append(sum("derived_" in edge["type"] for edge in graph["edges"]))
    finally:
        wall_ns = time.perf_counter_ns() - wall_start
        cpu_ns = time.process_time_ns() - cpu_start
        _native.Substrate.runtime_work_trace_set_all_scopes_enabled(False)
        _native.Substrate.scale_audit_set_per_rule_enabled(False)
        _native.Substrate.scale_audit_set_enabled(False)
    counters = {str(k): int(v) for k, v in dict(_native.Substrate.scale_audit_snapshot()).items()}
    rows, dropped = _native.Substrate.runtime_work_trace_all_scopes_snapshot()
    return {
        "replicate": replicate, "rule_count": n, "family": family, "arm": arm, "position": position,
        "repeats": REPEATS, "dense_degree": DENSE_DEGREE if family == "matcher_dense" else None,
        "reports": reports, "graph_digests": graph_digests, "derived_counts": derived_counts,
        "request_wall_ns": wall_ns, "request_process_cpu_ns": cpu_ns,
        "scale_counters": counters, "work_rows": [list(row) for row in rows],
        "work_row_count": len(rows), "work_dropped": int(dropped),
    }


def worker(replicate: int) -> dict:
    before = fingerprint()
    runs = []
    for size_index, n in enumerate(SIZES):
        for family_index, family in enumerate(FAMILIES):
            rotation = (replicate + size_index + family_index) % len(ARMS)
            order = list(ORDERS[replicate])
            order = order[rotation:] + order[:rotation]
            for position, arm in enumerate(order):
                runs.append(run_cell(n, family, arm, position, replicate))
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
    runs = []
    for replicate in range(3):
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(replicate)],
                            cwd=ROOT, env=dict(os.environ), text=True, capture_output=True, check=True)
        runs.append(json.loads(cp.stdout))
    after = fingerprint()
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps({
        "schema_version": 1, "run_id": "mutation-closure-trace-overhead-v1-20260928",
        "started_utc": datetime.now(timezone.utc).isoformat(), "locked_inputs": locked,
        "post_run_inputs": after, "runs": runs,
    }, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "source_stable": after == locked, "raw": str(RAW.relative_to(ROOT))}, indent=2))
    if after != locked or len({row["pid"] for row in runs}) != 3 or any(row["before"] != locked or row["after"] != locked for row in runs):
        raise SystemExit("worker or source stability gate failed")


if __name__ == "__main__":
    main()
