#!/usr/bin/env python3
"""Binding-cardinality/effect-position extension of external dependency probe v1."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_1_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_term_external_dependency_probe_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/term_external_dependency_probe_v1_1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/term_external_dependency_probe_v1_1_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/tools.rs", "runners/dsl/src/prog_eval.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_term_external_dependency_probe_v1_1.py",
    "scripts/analyze_term_external_dependency_probe_v1_1.py",
    "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_1_PREREG_20260928.md",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    ext = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
        "native_extension_path": str(ext),
        "native_extension_sha256": sha(ext),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
    }


def run_cell(cardinality: int, position: str) -> dict:
    from substrate_rs import Lit, Substrate, Term, _native

    _native.clear_tool_handlers()
    callback_args: list[str] = []

    def handler(arg):
        callback_args.append(str(arg))
        return "fixed-result"

    _native.register_tool_handler("probe", handler)
    substrate = Substrate()
    inner = substrate._inner
    source = inner.add_node("BoundaryScaleSource", {})
    targets = [inner.add_node("BoundaryScaleTarget", {}) for _ in range(cardinality)]
    for target in targets:
        inner.add_edge_unchecked(source, "trigger", target, {})
    tool_term = {"__term__": Term("UseTool", tool="probe", args=[Lit("payload")]).to_dict()}
    tool_effect = ["set_attr", "y", "tool_result", tool_term]
    marker_effect = ["set_attr", "y", "marker", 1]
    effects = [tool_effect, marker_effect] if position == "first" else [marker_effect, tool_effect]
    rule_idx = inner.add_rule({
        "name": f"external_dependency_cardinality_{cardinality}_{position}",
        "match": [["x", "trigger", "y"]],
        "where": None,
        "effects": effects,
    })
    access = inner.rule_access_sets()[rule_idx]
    fire_before = int(_native.tool_fire_count())
    inner.runtime_access_trace_set_enabled(False)
    inner.runtime_access_trace_reset()
    inner.runtime_access_trace_set_enabled(True)
    start_ns = time.perf_counter_ns()
    progress = int(inner.run_rules(10000))
    elapsed_ns = time.perf_counter_ns() - start_ns
    inner.runtime_access_trace_set_enabled(False)
    trace_rows, dropped = inner.runtime_access_trace_snapshot()
    graph = inner.graph_to_dict()
    fire_after = int(_native.tool_fire_count())
    _native.clear_tool_handlers()
    return {
        "cardinality": cardinality,
        "effect_position": position,
        "rule_uid": int(inner.rule_metadata(rule_idx)["rule_uid"]),
        "progress": progress,
        "elapsed_ns": elapsed_ns,
        "graph": graph,
        "target_ids": [int(node.value) for node in targets],
        "static_access": {
            "reads": sorted(map(str, access[3])),
            "writes": sorted(map(str, access[5])),
            "reads_any": bool(access[6]),
            "writes_any": bool(access[7]),
        },
        "callback_invocations": len(callback_args),
        "callback_args": callback_args,
        "native_fire_delta": fire_after - fire_before,
        "trace_rows": [list(row) for row in trace_rows],
        "trace_dropped": int(dropped),
    }


def worker(worker_id: int) -> dict:
    started_inputs = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text())["locked_inputs"] != started_inputs:
        raise RuntimeError("source/native inputs differ from v1.1 lock")
    cells = [run_cell(m, position) for m in (1, 2, 4) for position in ("first", "last")]
    return {
        "worker_id": worker_id,
        "pid": os.getpid(),
        "started_inputs": started_inputs,
        "python": sys.version,
        "platform": platform.platform(),
        "cells": cells,
    }


def main() -> None:
    if "--write-lock" in sys.argv:
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps({"lock_id": "term_external_dependency_probe_v1_1_20260928", "locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(str(LOCK.relative_to(ROOT)))
        return
    if "--worker" in sys.argv:
        print(json.dumps(worker(int(sys.argv[sys.argv.index("--worker") + 1])), sort_keys=True))
        return
    locked = json.loads(LOCK.read_text())
    if lock_inputs() != locked["locked_inputs"]:
        raise SystemExit("source/native inputs differ from v1.1 lock")
    runs = []
    for worker_id in range(1, 4):
        child_argv = [sys.executable, str(Path(__file__).resolve()), "--worker", str(worker_id)]
        proc = subprocess.run(child_argv, cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(f"worker {worker_id} failed ({proc.returncode}): {proc.stderr[-2000:]}")
        run = json.loads(proc.stdout.strip().splitlines()[-1])
        run["child_process"] = {
            "argv": child_argv,
            "return_code": proc.returncode,
            "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(proc.stderr.encode()).hexdigest(),
        }
        runs.append(run)
    report = {
        "schema_version": 1,
        "run_id": "term_external_dependency_probe_v1_1_20260928",
        "protocol_sha256": sha(PROTOCOL),
        "lock_sha256": sha(LOCK),
        "locked_inputs": locked["locked_inputs"],
        "environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(), "cpu_count": os.cpu_count()},
        "runs": runs,
        "claim_boundary": "Three fresh processes × six synthetic one-rule cells. Measures callback count, trace count, graph progress/state, and descriptive elapsed time across binding cardinality/effect position; not a general callback bound, natural workload estimate, or wall-time claim.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "cells_per_worker": len(runs[0]["cells"]), "output": str(OUT.relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__":
    main()
