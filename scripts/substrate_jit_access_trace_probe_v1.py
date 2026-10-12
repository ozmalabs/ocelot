#!/usr/bin/env python3
"""Paired direct probe of JIT Attr, TypeOf, and Count(Neighbours) trace sites."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

from substrate_rs import _native

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_jit_access_trace_probe_v1_20260925.json"
V = lambda name: {"type": "Var", "name": name}
L = lambda value: {"type": "Lit", "value": value}

CASES = {
    "jit_attr": {"type": "Not", "arg": {"type": "Attr", "node": V("a"), "key": "flag"}},
    "jit_type": {"type": "Eq", "a": {"type": "TypeOf", "node": V("b")}, "b": L("Probe")},
    "jit_neighbour_count": {"type": "Gt", "a": {"type": "Count", "source": {
        "type": "Neighbours", "node": V("a"), "edge_type": "probe_edge"}}, "b": L(0)},
}
EXPECTED_KIND = {"jit_attr": "jit_attr_read", "jit_type": "jit_type_read", "jit_neighbour_count": "term_edge_read"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(case: str, traced: bool) -> dict:
    sub = _native.Substrate()
    sub.add_rule({"name": f"{case}_rule", "match": [["a", "probe_edge", "b"]],
                  "where": CASES[case], "effects": []})
    a = sub.add_node("Probe", {"flag": 0})
    b = sub.add_node("Probe", {})
    sub.add_edge_unchecked(a, "probe_edge", b, {})
    compiled, total, _epoch = sub.jit_report()
    _native.Substrate.runtime_access_trace_reset()
    _native.Substrate.runtime_access_trace_set_enabled(traced)
    outcome = sub.run_rules_report(10, False)
    terminal = sub.run_rules(1)
    events, dropped = sub.runtime_access_trace_snapshot()
    _native.Substrate.runtime_access_trace_set_enabled(False)
    return {"trace_enabled": traced, "compiled_jit_rules": compiled, "total_rules": total,
            "progress": outcome["progress_steps"], "status": outcome["status"],
            "terminal_progress": terminal, "events": [list(row) for row in events],
            "event_count": sum(row[5] for row in events), "dropped": dropped,
            "expected_where_truth": True}


def main() -> None:
    cells = []
    for case in CASES:
        plain, traced = run(case, False), run(case, True)
        cells.append({"case": case, "expected_kind": EXPECTED_KIND[case], "plain": plain, "traced": traced,
                      "outcome_match": (plain["progress"], plain["status"], plain["terminal_progress"])
                      == (traced["progress"], traced["status"], traced["terminal_progress"])})
    checks = {
        "each_fixture_compiles_one_jit_rule": all(c["traced"]["compiled_jit_rules"] == 1 for c in cells),
        "all_pairs_settle_with_matching_outcomes": all(c["outcome_match"] and c["traced"]["status"] == "fixed_point"
                                                        and c["traced"]["terminal_progress"] == 0 for c in cells),
        "plain_arms_emit_nothing": all(c["plain"]["event_count"] == 0 for c in cells),
        "trace_arms_emit_expected_kind": all(c["traced"]["event_count"] > 0 and
                                               any(e[1] == c["expected_kind"] for e in c["traced"]["events"])
                                               for c in cells),
        "no_trace_overflow": all(c["traced"]["dropped"] == 0 for c in cells),
    }
    ext = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
    report = {"schema_version": 1, "run_id": "substrate-jit-access-trace-probe-v1-20260925",
              "scope": "three tiny paired fresh-substrate probes of JIT Attr, TypeOf, and fused Count(Neighbours)",
              "claim_boundary": "Confirms three newly instrumented JIT sites; not representative coverage, performance, or general trace completeness.",
              "environment": {"python": sys.version, "platform": platform.platform()},
              "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                             "native_extension_sha256": sha(ext),
                             "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
                             "source_sha256": {p: sha(ROOT / p) for p in (
                                 "runners/dsl/src/access_trace.rs", "runners/dsl/src/jit.rs",
                                 "scripts/substrate_jit_access_trace_probe_v1.py")}},
              "checks": checks, "cells": cells}
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "cells": len(cells), "output": str(OUT)}, indent=2))
    if not all(checks.values()):
        raise SystemExit("JIT trace probe failed")


if __name__ == "__main__":
    main()
