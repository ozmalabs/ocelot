#!/usr/bin/env python3
"""Locked fresh-process probe for ReadFile and UseTool rule dependencies."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_PREREG_20260928.md"
ANALYZER = ROOT / "scripts/analyze_term_external_dependency_probe_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/term_external_dependency_probe_v1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/term_external_dependency_probe_v1_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs",
    "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/tools.rs",
    "runners/dsl/src/prog_eval.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_term_external_dependency_probe_v1.py",
    "scripts/analyze_term_external_dependency_probe_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_PREREG_20260928.md",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lock_inputs() -> dict:
    from substrate_rs import _native
    ext = Path(_native.__file__).resolve()
    manifest = ROOT / "runners/dsl/python/substrate_rs/_native.build.json"
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
        "native_extension_path": str(ext),
        "native_extension_sha256": sha(ext),
        "native_build_manifest_sha256": sha(manifest),
    }


def one_case(term, *, trace: bool, handler_mode: str, name: str) -> dict:
    from substrate_rs import Substrate, _native

    _native.clear_tool_handlers()
    callback_calls: list[str] = []
    if handler_mode == "fixed":
        def handler(arg):
            callback_calls.append(str(arg))
            return "fixed-result"
        _native.register_tool_handler("probe", handler)

    substrate = Substrate()
    inner = substrate._inner
    x = inner.add_node("BoundaryProbe", {})
    y = inner.add_node("BoundaryProbe", {})
    inner.add_edge_unchecked(x, "trigger", y, {})
    rule_idx = inner.add_rule({
        "name": f"external_dependency_{name}",
        "match": [["x", "trigger", "y"]],
        "where": None,
        "effects": [["set_attr", "y", "result", {"__term__": term.to_dict()}]],
    })
    access_row = inner.rule_access_sets()[rule_idx]
    rule_uid = int(inner.rule_metadata(rule_idx)["rule_uid"])
    fire_before = int(_native.tool_fire_count())
    inner.runtime_access_trace_set_enabled(False)
    inner.runtime_access_trace_reset()
    inner.runtime_access_trace_set_enabled(trace)
    progress = int(inner.run_rules(20))
    inner.runtime_access_trace_set_enabled(False)
    trace_rows, dropped = inner.runtime_access_trace_snapshot()
    graph = inner.graph_to_dict()
    fire_after = int(_native.tool_fire_count())
    _native.clear_tool_handlers()
    return {
        "name": name,
        "trace_enabled": trace,
        "handler_mode": handler_mode,
        "rule_uid": rule_uid,
        "progress": progress,
        "graph": graph,
        "static_access": {
            "reads": sorted(map(str, access_row[3])),
            "term_edge_reads": sorted(map(str, access_row[4])),
            "writes": sorted(map(str, access_row[5])),
            "reads_any": bool(access_row[6]),
            "writes_any": bool(access_row[7]),
        },
        "callback_invocations": len(callback_calls),
        "callback_arguments": callback_calls,
        "native_fire_delta": fire_after - fire_before,
        "trace_rows": [list(row) for row in trace_rows],
        "trace_dropped": int(dropped),
    }


def worker(worker_id: int) -> dict:
    from substrate_rs import Lit, ReadFile, Term

    started_inputs = lock_inputs()
    if not LOCK.exists() or json.loads(LOCK.read_text())["locked_inputs"] != started_inputs:
        raise RuntimeError("source/native inputs differ from preregistered lock")
    cells = []
    with tempfile.TemporaryDirectory(prefix="term-external-probe-") as td:
        path = Path(td) / "input.txt"
        for value, name in (("alpha", "file_alpha"), ("beta", "file_beta")):
            path.write_text(value, encoding="utf-8")
            cells.append(one_case(ReadFile(Lit(str(path))), trace=True, handler_mode="none", name=name))
        path.unlink()
        cells.append(one_case(ReadFile(Lit(str(path))), trace=True, handler_mode="none", name="file_missing"))
    tool = Term("UseTool", tool="probe", args=[Lit("payload")])
    cells.append(one_case(tool, trace=True, handler_mode="fixed", name="tool_traced"))
    cells.append(one_case(tool, trace=False, handler_mode="fixed", name="tool_untraced"))
    cells.append(one_case(tool, trace=True, handler_mode="none", name="tool_missing"))
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
        LOCK.write_text(json.dumps({"lock_id": "term_external_dependency_probe_v1_20260928", "locked_inputs": lock_inputs()}, indent=2, sort_keys=True) + "\n")
        print(str(LOCK.relative_to(ROOT)))
        return
    if "--worker" in sys.argv:
        worker_id = int(sys.argv[sys.argv.index("--worker") + 1])
        print(json.dumps(worker(worker_id), sort_keys=True))
        return
    locked = json.loads(LOCK.read_text())
    if lock_inputs() != locked["locked_inputs"]:
        raise SystemExit("source/native inputs differ from preregistered lock")
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
        "run_id": "term_external_dependency_probe_v1_20260928",
        "protocol_sha256": sha(PROTOCOL),
        "lock_sha256": sha(LOCK),
        "locked_inputs": locked["locked_inputs"],
        "environment": {"python": sys.version, "platform": platform.platform(), "machine": platform.machine(), "cpu_count": os.cpu_count()},
        "runs": runs,
        "claim_boundary": "Three fresh-process synthetic rule fixtures. Measures selected RuleKey declarations, trace events, graph results, and callback repetition for ReadFile/UseTool. Does not establish safety, containment, natural workload frequency, general trace completeness, or a callback invocation bound beyond this fixture.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(runs), "cells_per_worker": len(runs[0]["cells"]), "output": str(OUT.relative_to(ROOT))}, sort_keys=True))


if __name__ == "__main__":
    main()
