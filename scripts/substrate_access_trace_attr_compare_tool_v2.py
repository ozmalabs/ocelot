#!/usr/bin/env python3
"""Paired trace probe for conditional-attribute reads and UseTool dispatch."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners/dsl/python"))

from substrate_rs import _native

from domains.engine_provenance import assert_measuring_engine
from scripts.substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture

RUN_ID = "substrate-access-trace-attr-compare-tool-v2-20260926"
OUT = ROOT / "evaluation/reports/substrate_access_trace_attr_compare_tool_v2_20260926.json"
RAW = ROOT / "evaluation/reports/substrate_access_trace_attr_compare_tool_v2_workers_raw_20260926.json"
LOCK = ROOT / "evaluation/substrate_capability/access_trace_attr_compare_tool_v2_lock_20260926.json"
PROTOCOL = "docs/research/engine_substrate/SUBSTRATE_ACCESS_TRACE_ATTR_COMPARE_AND_TOOL_DISPATCH_V2_PREREG_20260926.md"
SOURCE_FILES = (
    "runners/dsl/src/access_trace.rs", "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/term.rs", "runners/dsl/src/tools.rs", "runners/dsl/src/py.rs",
)
V = lambda name: {"type": "Var", "name": name}
L = lambda value: {"type": "Lit", "value": value}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    files = (*SOURCE_FILES, "runners/dsl/python/substrate_rs/_native.build.json",
             "scripts/substrate_access_trace_attr_compare_tool_v2.py", PROTOCOL)
    return {"files": {p: sha(ROOT / p) for p in files},
            "native_extension_sha256": sha(native),
            "native_path": str(native),
            "build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}


def execute_attr(initial: int, traced: bool) -> dict:
    sub = _native.Substrate()
    node = sub.add_node("Probe", {"target": initial})
    peer = sub.add_node("Probe", {})
    sub.add_edge_unchecked(node, "trigger", peer, {})
    sub.add_rule({"name": "conditional_attr_probe", "match": [["a", "trigger", "b"]],
                  "where": None, "effects": [["set_attr_if_different", "a", "target", 1]]})
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.runtime_access_trace_set_enabled(traced)
    outcome = sub.run_rules_report(10, False)
    events, dropped = sub.runtime_access_trace_snapshot()
    _native.Substrate.runtime_access_trace_set_enabled(False)
    rows = [list(row) for row in events]
    compare_reads = sum(row[5] for row in rows if row[1] == "effect_attr_compare_read"
                        and row[2] == node and row[3] == "target")
    writes = sum(row[5] for row in rows if row[1] == "effect_attr_write"
                 and row[2] == node and row[3] == "target")
    return {"traced": traced, "initial": initial, "final": sub.node(node)["attrs"].get("target"),
            "progress_steps": outcome["progress_steps"], "status": outcome["status"],
            "events": rows, "compare_read_events": compare_reads,
            "write_events": writes, "event_count": sum(row[5] for row in rows),
            "dropped": dropped}


def execute_tool(traced: bool) -> dict:
    sub = _native.Substrate()
    node = sub.add_node("Probe", {})
    peer = sub.add_node("Probe", {})
    sub.add_edge_unchecked(node, "trigger", peer, {})
    calls = {"count": 0}

    def handler(*_args):
        calls["count"] += 1
        return True

    tool_name = "access_trace_tool_probe"
    _native.clear_tool_handlers()
    _native.register_tool_handler(tool_name, handler)
    sub.add_rule({"name": "tool_dispatch_probe", "match": [["a", "trigger", "b"]],
                  "where": {"type": "Eq", "a": {"type": "UseTool", "tool": tool_name, "args": []},
                            "b": L(True)}, "effects": []})
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.runtime_access_trace_set_enabled(traced)
    outcome = sub.run_rules_report(10, False)
    events, dropped = sub.runtime_access_trace_snapshot()
    _native.Substrate.runtime_access_trace_set_enabled(False)
    _native.clear_tool_handlers()
    rows = [list(row) for row in events]
    dispatches = sum(row[5] for row in rows if row[1] == "term_tool_dispatch"
                     and row[3] == tool_name)
    return {"traced": traced, "handler_calls": calls["count"],
            "progress_steps": outcome["progress_steps"], "status": outcome["status"],
            "events": rows, "dispatch_events": dispatches,
            "event_count": sum(row[5] for row in rows), "dropped": dropped}


def worker(replicate: int) -> dict:
    before = fingerprint()
    attr = {}
    for label, initial in (("changed", 0), ("unchanged", 1)):
        attr[label] = {"plain": execute_attr(initial, False), "traced": execute_attr(initial, True)}
    tool = {"plain": execute_tool(False), "traced": execute_tool(True)}
    return {"replicate": replicate, "pid": os.getpid(), "before": before,
            "after": fingerprint(), "attribute_cases": attr, "tool_case": tool}


def main() -> None:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True))
        return
    assert_measuring_engine()
    if sys.argv[1:] == ["--lock"]:
        payload = {"locked_inputs": fingerprint()}
        LOCK.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"lock": str(LOCK), "inputs": payload["locked_inputs"]}, indent=2, sort_keys=True))
        return
    started = datetime.now(timezone.utc).isoformat()
    locked = fingerprint()
    if not LOCK.is_file() or json.loads(LOCK.read_text()).get("locked_inputs") != locked:
        raise SystemExit("missing or stale source/native lock; run --lock after reviewing preregistered inputs")
    log = start_console_capture(RUN_ID)
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("PYTHONPATH", os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"))))
    runs = []
    for rep in range(3):
        proc = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        runs.append(json.loads(proc.stdout))
    post = fingerprint()
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": locked,
           "post_run_inputs": post, "runs": runs}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    checks = {"three_fresh_worker_processes": len({row["pid"] for row in runs}) == 3,
              "source_native_lock_stable": post == locked and all(row["before"] == locked == row["after"] for row in runs)}
    for run in runs:
        for label, data in run["attribute_cases"].items():
            plain, traced = data["plain"], data["traced"]
            checks[f"r{run['replicate']}_{label}_semantic_parity"] = (
                (plain["final"], plain["progress_steps"], plain["status"])
                == (traced["final"], traced["progress_steps"], traced["status"]))
            checks[f"r{run['replicate']}_{label}_compare_read_observed"] = traced["compare_read_events"] == 1
            checks[f"r{run['replicate']}_{label}_write_branch_correct"] = (
                traced["write_events"] == (1 if label == "changed" else 0))
            checks[f"r{run['replicate']}_{label}_trace_isolation"] = not plain["events"] and traced["dropped"] == 0
        plain, traced = run["tool_case"]["plain"], run["tool_case"]["traced"]
        checks[f"r{run['replicate']}_tool_semantic_parity"] = (
            (plain["handler_calls"], plain["progress_steps"], plain["status"])
            == (traced["handler_calls"], traced["progress_steps"], traced["status"]))
        checks[f"r{run['replicate']}_tool_dispatch_attributed"] = (
            traced["handler_calls"] == 1 and traced["dispatch_events"] == 1)
        checks[f"r{run['replicate']}_tool_trace_isolation"] = not plain["events"] and traced["dropped"] == 0
    result = {"schema_version": 1, "run_id": RUN_ID, "started_utc": started,
              "environment": {"python": sys.version, "platform": platform.platform()},
              "locked_inputs": locked, "post_run_inputs": post, "lock_sha256": sha(LOCK),
              "raw_workers_path": str(RAW.relative_to(ROOT)), "checks": checks,
              "all_checks_pass": all(checks.values())}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    log_ref = finish_console_capture(log)
    manifest = capture_run_manifest(
        run_id=RUN_ID, runner="scripts/substrate_access_trace_attr_compare_tool_v2.py",
        protocol_files=(PROTOCOL,), source_files=SOURCE_FILES,
        data_files=(str(LOCK.relative_to(ROOT)),), started_utc=started,
        exit_status=0 if result["all_checks_pass"] else 1, stdout_stderr_capture=log_ref,
        child_processes=[{"replicate": row["replicate"], "pid": row["pid"]} for row in runs])
    result["run_manifest"] = manifest
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "all_checks_pass": result["all_checks_pass"],
                      "checks": checks}, indent=2, sort_keys=True))
    if not result["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
