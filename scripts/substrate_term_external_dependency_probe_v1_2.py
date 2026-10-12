#!/usr/bin/env python3
"""Predicate/nesting/multi-rule UseTool dependency probe v1.2."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_2_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_term_external_dependency_probe_v1_2.py"
LOCK = ROOT / "evaluation/substrate_capability/term_external_dependency_probe_v1_2_lock_20260928.json"
OUT = ROOT / "evaluation/reports/term_external_dependency_probe_v1_2_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/tools.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_term_external_dependency_probe_v1_2.py",
    "scripts/analyze_term_external_dependency_probe_v1_2.py",
    "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_2_PREREG_20260928.md",
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


def one_case(name: str, where_factory, rule_count: int = 1, stateful: bool = False) -> dict:
    from substrate_rs import Lit, Substrate, Term, _native

    _native.clear_tool_handlers()
    callback_log: list[dict] = []

    def handler(arg):
        result = len(callback_log) == 0 if stateful else True
        callback_log.append({"arg": str(arg), "return": result})
        return result

    _native.register_tool_handler("probe", handler)
    substrate = Substrate()
    inner = substrate._inner
    x = inner.add_node("PredicateProbe", {})
    y = inner.add_node("PredicateProbe", {})
    inner.add_edge_unchecked(x, "trigger", y, {})
    rules = []
    for i in range(rule_count):
        rule_idx = inner.add_rule({
            "name": f"external_predicate_{name}_{i}",
            "match": [["x", "trigger", "y"]],
            "where": where_factory(Term, Lit),
            "effects": [["set_attr", "y", f"marker_{i}", 1]],
        })
        rules.append({
            "rule_idx": rule_idx,
            "rule_uid": int(inner.rule_metadata(rule_idx)["rule_uid"]),
            "static_access": {
                "reads": sorted(map(str, inner.rule_access_sets()[rule_idx][3])),
                "reads_any": bool(inner.rule_access_sets()[rule_idx][6]),
            },
        })
    fire_before = int(_native.tool_fire_count())
    inner.runtime_access_trace_set_enabled(False)
    inner.runtime_access_trace_reset()
    inner.runtime_access_trace_set_enabled(True)
    progress = int(inner.run_rules(100))
    inner.runtime_access_trace_set_enabled(False)
    trace_rows, dropped = inner.runtime_access_trace_snapshot()
    graph = inner.graph_to_dict()
    fire_after = int(_native.tool_fire_count())
    _native.clear_tool_handlers()
    return {
        "name": name,
        "rules": rules,
        "progress": progress,
        "graph": graph,
        "callback_log": callback_log,
        "callback_invocations": len(callback_log),
        "native_fire_delta": fire_after - fire_before,
        "trace_rows": [list(row) for row in trace_rows],
        "trace_dropped": int(dropped),
    }


def worker(worker_id: int) -> dict:
    from substrate_rs import Lit, Term

    started_inputs = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text())["locked_inputs"] != started_inputs:
        raise RuntimeError("source/native inputs differ from v1.2 lock")

    def direct(term, lit):
        return Term("UseTool", tool="probe", args=[lit("payload")]).to_dict()

    def before_false(term, lit):
        call = Term("UseTool", tool="probe", args=[lit("payload")])
        return Term("And", items=[lit(False), call]).to_dict()

    def after_false(term, lit):
        call = Term("UseTool", tool="probe", args=[lit("payload")])
        return Term("And", items=[call, lit(False)]).to_dict()

    cells = [
        one_case("direct_true", direct),
        one_case("short_circuit_before", before_false),
        one_case("short_circuit_after", after_false),
        one_case("two_rules", direct, rule_count=2),
        one_case("stateful_predicate", direct, stateful=True),
    ]
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
        LOCK.write_text(json.dumps({"lock_id": "term_external_dependency_probe_v1_2_20260928", "locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(str(LOCK.relative_to(ROOT)))
        return
    if "--worker" in sys.argv:
        print(json.dumps(worker(int(sys.argv[sys.argv.index("--worker") + 1])), sort_keys=True))
        return
    locked = json.loads(LOCK.read_text())
    if lock_inputs() != locked["locked_inputs"]:
        raise SystemExit("source/native inputs differ from v1.2 lock")
    runs = []
    for worker_id in range(1, 4):
        argv = [sys.executable, str(Path(__file__).resolve()), "--worker", str(worker_id)]
        proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True)
        if proc.returncode:
            raise SystemExit(f"worker {worker_id} failed ({proc.returncode}): {proc.stderr[-2000:]}")
        run = json.loads(proc.stdout.strip().splitlines()[-1])
        run["child_process"] = {
            "argv": argv, "return_code": proc.returncode,
            "stdout_sha256": hashlib.sha256(proc.stdout.encode()).hexdigest(),
            "stderr_sha256": hashlib.sha256(proc.stderr.encode()).hexdigest(),
        }
        runs.append(run)
    report = {
        "schema_version": 1,
        "run_id": "term_external_dependency_probe_v1_2_20260928",
        "protocol_sha256": sha(PROTOCOL), "lock_sha256": sha(LOCK),
        "locked_inputs": locked["locked_inputs"],
        "environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(), "cpu_count": os.cpu_count()},
        "runs": runs,
        "claim_boundary": "Three fresh workers × five synthetic predicate/nesting/multiple-rule cells. Measures local callback invocations, native fire counts, trace counts and graph state; no general side-effect-safety or complexity claim.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "cells_per_worker": len(runs[0]["cells"]), "output": str(OUT.relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__":
    main()
