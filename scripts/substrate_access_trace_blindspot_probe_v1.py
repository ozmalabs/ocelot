#!/usr/bin/env python3
"""Paired diagnostic probes for unchanged attribute effects and UseTool traces."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from substrate_rs import _native
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_access_trace_blindspot_probe_v1_20260926.json"
V = lambda name: {"type": "Var", "name": name}
L = lambda value: {"type": "Lit", "value": value}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_attr(changed: bool, traced: bool) -> dict:
    sub = _native.Substrate()
    old = 0 if changed else 1
    node = sub.add_node("Probe", {"target": old})
    peer = sub.add_node("Probe", {})
    sub.add_edge_unchecked(node, "trigger", peer, {})
    sub.add_rule({"name": "sai_probe", "match": [["a", "trigger", "b"]],
                  "where": None,
                  "effects": [["set_attr_if_different", "a", "target", 1]]})
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.runtime_access_trace_set_enabled(traced)
    outcome = sub.run_rules_report(10, False)
    events, dropped = sub.runtime_access_trace_snapshot()
    _native.Substrate.runtime_access_trace_set_enabled(False)
    rows = [list(row) for row in events]
    writes = sum(row[5] for row in rows if row[1] == "effect_attr_write"
                 and row[2] == node and row[3] == "target")
    return {"trace_enabled": traced, "target_node": node, "initial": old,
            "final": sub.node(node)["attrs"].get("target"), "progress": outcome["progress_steps"],
            "status": outcome["status"], "events": rows,
            "target_write_event_count": writes, "event_count": sum(row[5] for row in rows),
            "dropped": dropped}


def run_tool(traced: bool) -> dict:
    sub = _native.Substrate()
    node = sub.add_node("Probe", {})
    peer = sub.add_node("Probe", {})
    sub.add_edge_unchecked(node, "trigger", peer, {})
    calls = {"n": 0}

    def handler(*_args):
        calls["n"] += 1
        return True

    _native.clear_tool_handlers()
    _native.register_tool_handler("trace_probe", handler)
    sub.add_rule({"name": "tool_probe", "match": [["a", "trigger", "b"]],
                  "where": {"type": "Eq", "a": {"type": "UseTool", "tool": "trace_probe", "args": []},
                            "b": L(True)}, "effects": []})
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.runtime_access_trace_set_enabled(traced)
    outcome = sub.run_rules_report(10, False)
    events, dropped = sub.runtime_access_trace_snapshot()
    _native.Substrate.runtime_access_trace_set_enabled(False)
    _native.clear_tool_handlers()
    rows = [list(row) for row in events]
    return {"trace_enabled": traced, "handler_calls": calls["n"],
            "progress": outcome["progress_steps"], "status": outcome["status"],
            "events": rows, "event_count": sum(row[5] for row in rows), "dropped": dropped}


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    log_capture = start_console_capture("substrate-access-trace-blindspot-probe-v1-20260926")
    cases = []
    for changed in (False, True):
        plain, traced = run_attr(changed, False), run_attr(changed, True)
        cases.append({"family": "set_attr_if_different", "changed": changed,
                      "plain": plain, "traced": traced,
                      "semantic_match": (plain["final"], plain["progress"], plain["status"])
                      == (traced["final"], traced["progress"], traced["status"])})
    plain, traced = run_tool(False), run_tool(True)
    cases.append({"family": "use_tool", "plain": plain, "traced": traced,
                  "semantic_match": (plain["handler_calls"], plain["progress"], plain["status"])
                  == (traced["handler_calls"], traced["progress"], traced["status"])})
    checks = {
        "attribute_semantics_match": all(c["semantic_match"] for c in cases[:2]),
        "unchanged_attribute_has_no_write_event": cases[0]["traced"]["target_write_event_count"] == 0,
        "changed_attribute_has_write_event": cases[1]["traced"]["target_write_event_count"] > 0,
        "tool_callback_independently_observed": traced["handler_calls"] > 0,
        "tool_callback_has_no_tool_event_kind": not any("tool" in str(row[1]).lower()
                                                         for row in traced["events"]),
        "tool_semantics_match": cases[2]["semantic_match"],
        "no_trace_overflow": all(c["traced"]["dropped"] == 0 for c in cases),
    }
    sources = ("runners/dsl/src/access_trace.rs", "runners/dsl/src/term.rs",
               "runners/dsl/src/rewrite.rs", "runners/dsl/src/tools.rs", "runners/dsl/src/py.rs",
               "scripts/substrate_access_trace_blindspot_probe_v1.py")
    ext = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    print("probe checks before manifest capture:", json.dumps(checks, sort_keys=True), flush=True)
    log_ref = finish_console_capture(log_capture)
    run_manifest = capture_run_manifest(
        run_id="substrate-access-trace-blindspot-probe-v1-20260926",
        runner="scripts/substrate_access_trace_blindspot_probe_v1.py",
        protocol_files=("docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md",
                        "docs/research/engine_substrate/SUBSTRATE_ACCESS_TRACE_BLINDSPOT_PROBE_V1_PREREG_20260926.md"),
        source_files=("runners/dsl/src/access_trace.rs", "runners/dsl/src/term.rs",
                      "runners/dsl/src/rewrite.rs", "runners/dsl/src/tools.rs", "runners/dsl/src/py.rs"),
        started_utc=started, exit_status=0 if all(checks.values()) else 1,
        stdout_stderr_capture=log_ref)
    report = {"schema_version": 1, "run_id": "substrate-access-trace-blindspot-probe-v1-20260926",
              "claim_boundary": "Paired mechanism probes for two known trace limits; not general recall or cost coverage.",
              "environment": {"python": sys.version, "platform": platform.platform()},
              "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                             "native_extension_sha256": sha(ext),
                             "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
                             "source_sha256": {p: sha(ROOT / p) for p in sources}},
              "run_manifest": run_manifest, "checks": checks, "cells": cases}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"checks": checks, "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("blind-spot probe failed")


if __name__ == "__main__":
    main()
