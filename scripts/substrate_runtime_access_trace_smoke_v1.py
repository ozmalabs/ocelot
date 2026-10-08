#!/usr/bin/env python3
"""Paired native smoke measurement for the opt-in concrete access trace."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_runtime_access_trace_smoke_v1_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_arm(trace_enabled: bool) -> dict:
    from substrate_rs import Substrate, _native

    substrate = Substrate()
    inner = substrate._inner
    inner.runtime_access_trace_set_enabled(False)
    inner.runtime_access_trace_reset()
    root = inner.add_node("TraceRoot", {"watched": 5})
    target = inner.add_node("TraceTarget", {})
    inner.add_edge_unchecked(root, "trigger", target, {})
    rule_idx = inner.add_rule({
        "name": "runtime_access_trace_smoke_reader",
        "match": [["x", "trigger", "y"]],
        "where": {"type": "Gt", "a": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "watched"},
                  "b": {"type": "Lit", "value": 0}},
        "effects": [
            ["set_attr", "y", "observed", {"__term__": {"type": "Attr", "node": {"type": "Var", "name": "x"}, "key": "watched"}}],
            ["add_edge", "x", "derived", "y", {}],
        ],
    })
    rule_uid = int(inner.rule_metadata(rule_idx)["rule_uid"])
    inner.runtime_access_trace_set_enabled(trace_enabled)
    progress = int(inner.run_rules(100))
    graph = inner.graph_to_dict()
    terminal = int(inner.run_rules(1))
    events, dropped = inner.runtime_access_trace_snapshot()
    inner.runtime_access_trace_set_enabled(False)
    return {
        "trace_enabled": trace_enabled,
        "rule_uid": rule_uid,
        "progress": progress,
        "terminal_progress": terminal,
        "graph": graph,
        "events": [list(row) for row in events],
        "dropped_events": int(dropped),
    }


def main() -> None:
    from substrate_rs import _native

    traced = run_arm(True)
    untraced = run_arm(False)
    kinds = {row[1] for row in traced["events"]}
    rule_events = [row for row in traced["events"] if row[0] == traced["rule_uid"]]
    checks = {
        "enabled_and_disabled_graphs_match": traced["graph"] == untraced["graph"],
        "enabled_and_disabled_progress_match": traced["progress"] == untraced["progress"],
        "both_terminal_probes_settled": traced["terminal_progress"] == untraced["terminal_progress"] == 0,
        "events_are_attributed_to_stable_rule_uid": bool(rule_events),
        "pattern_edge_event_present": "pattern_edge" in kinds,
        "attribute_read_event_present": "term_attr_read" in kinds,
        "attribute_and_edge_write_events_present": {
            "effect_attr_write", "effect_edge_upsert"
        }.issubset(kinds),
        "no_trace_events_when_disabled": len(untraced["events"]) == 0,
        "no_events_dropped": traced["dropped_events"] == 0,
    }
    extension = Path(_native.__file__).resolve()
    report = {
        "schema_version": 1,
        "run_id": "substrate-runtime-access-trace-smoke-v1-20260925",
        "scope": "one native rule with one pattern edge, a where Attr read, an effect Attr read, SetAttr, and AddEdge",
        "claim_boundary": (
            "Instrumentation smoke and enabled/disabled parity on one graph. Not evidence of complete access coverage, "
            "low tracing overhead, natural frame locality, or CAN/conversation behavior. JIT and aggregate Terms are not covered."
        ),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(extension),
            "native_extension_sha256": sha(extension),
            "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
            "source_sha256": {
                path: sha(ROOT / path) for path in (
                    "runners/dsl/src/access_trace.rs", "runners/dsl/src/lib.rs",
                    "runners/dsl/src/rewrite.rs", "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
                    "scripts/substrate_runtime_access_trace_smoke_v1.py",
                )
            },
        },
        "checks": checks,
        "traced": traced,
        "untraced": untraced,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"checks": checks, "event_rows": len(traced["events"]), "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("runtime access trace smoke measurement failed")


if __name__ == "__main__":
    main()
