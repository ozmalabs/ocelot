#!/usr/bin/env python3
"""Measure steady no-match scope calls as the active rule list grows."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
from domains.engine_provenance import build_is_stale, rust_source_fingerprint
from substrate_rs import Substrate
from substrate_rs.ext import add_rule

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_BORROWED_SCOPED_RULES_CONFIRMATION_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_scoped_noop_setup_cost_borrowed_v2_20260926.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
RULE_COUNTS = (0, 1, 4, 16, 64, 256, 512)
REPEATS, CALLS, CAP = 7, 50, 100_000
APIS = ("scoped_basic", "scoped_report", "full_report")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(rule_count: int):
    s = Substrate()
    mt = s.add_node("Microtheory", {"fixed": True})
    concept = s.add_node("Concept", {"fixed": True})
    s.add_edge_unchecked(mt, "has_concept", concept)
    for i in range(rule_count):
        add_rule(s._inner, f"no_match_{i:04d}", [("x", f"absent_relation_{i:04d}", "y")],
                 [["set_attr", "y", f"never_written_{i:04d}", True]])
    return s, mt, concept


def projection(s, mt, concept):
    mt_data, concept_data = s.node(mt), s.node(concept)
    return {"node_count": s.node_count(), "edge_count": s.edge_count(),
            "microtheory": {"type": mt_data["type"], "attrs": mt_data["attrs"]},
            "concept": {"type": concept_data["type"], "attrs": concept_data["attrs"]},
            "ownership_edge": s.has_edge(mt, "has_concept", concept),
            "rule_count": s._inner.rule_count()}


def invoke(s, mt, api):
    if api == "scoped_basic":
        result = int(s._inner.run_rules_scoped(CAP, False, mt))
        return {"progress_steps": result, "fixed_point": result == 0}
    if api == "scoped_report":
        result = s._inner.run_rules_scoped_delta_report(mt, CAP, False)
        return {"progress_steps": int(result["progress_steps"]),
                "fixed_point": int(result["progress_steps"]) == 0 and not result["hit_progress_budget"] and not result["deferred_effects_pending"],
                "hit_progress_budget": bool(result["hit_progress_budget"]),
                "deferred_effects_pending": bool(result["deferred_effects_pending"]),
                "affected_microtheories": result["affected_microtheories"]}
    if api == "full_report":
        result = s._inner.run_rules_report(CAP, False)
        return {"progress_steps": int(result["progress_steps"]), "fixed_point": result["status"] == "fixed_point",
                "status": result["status"]}
    raise ValueError(api)


def measure_batch(rule_count: int, api: str, audit_enabled: bool, repeat: int):
    s, mt, concept = fixture(rule_count)
    inner = s._inner
    inner.scale_audit_set_per_rule_enabled(False); inner.scale_audit_per_rule_reset()
    inner.scale_audit_set_enabled(False)
    warmup = invoke(s, mt, api)
    before = projection(s, mt, concept)
    inner.scale_audit_reset(); inner.scale_audit_set_enabled(audit_enabled)
    wall0, cpu0 = time.perf_counter_ns(), time.process_time_ns()
    calls = [invoke(s, mt, api) for _ in range(CALLS)]
    wall_ns, cpu_ns = time.perf_counter_ns() - wall0, time.process_time_ns() - cpu0
    counts = dict(inner.scale_audit_snapshot())
    per_rule_rows = list(inner.scale_audit_per_rule_snapshot())
    after = projection(s, mt, concept)
    inner.scale_audit_set_enabled(False); inner.scale_audit_set_per_rule_enabled(False)
    return {"repeat": repeat, "api": api, "audit_enabled": audit_enabled,
            "warmup": warmup, "calls": len(calls), "all_calls_fixed_point": all(x["fixed_point"] and x["progress_steps"] == 0 for x in calls),
            "state_unchanged": before == after, "before": before, "after": after,
            "wall_ns": wall_ns, "cpu_ns": cpu_ns, "ns_per_call": wall_ns / CALLS,
            "global_counters": counts, "per_rule_rows": len(per_rule_rows)}


def main():
    if build_is_stale(str(ROOT)):
        raise SystemExit("refusing to measure: native build is stale")
    rows = []
    for count in RULE_COUNTS:
        reps = []
        for rep in range(REPEATS):
            runs = []
            api_order = list(APIS) if rep % 2 == 0 else list(reversed(APIS))
            audit_order = (False, True) if rep % 2 == 0 else (True, False)
            for api in api_order:
                for audit in audit_order:
                    runs.append(measure_batch(count, api, audit, rep))
            by_key = {(x["api"], x["audit_enabled"]): x for x in runs}
            expected_graph = by_key[("scoped_basic", False)]["before"]
            checks = {
                "all_arms_stable_and_zero_progress": all(x["all_calls_fixed_point"] and x["state_unchanged"] and x["before"] == expected_graph for x in runs),
                "audit_off_counters_zero": all(all(int(v) == 0 for v in x["global_counters"].values()) for x in runs if not x["audit_enabled"]),
                "audit_on_rule_attempts_observable": all(int(by_key[(api, True)]["global_counters"].get("rule_enumerations", 0)) > 0 for api in ("scoped_basic", "scoped_report") if count > 0),
                "no_candidate_or_term_work": all(int(x["global_counters"].get("cand_enum", 0)) == 0 and int(x["global_counters"].get("term_evals_total", 0)) == 0 for x in runs),
                "no_per_rule_mode_or_rows": all(x["per_rule_rows"] == 0 for x in runs),
                "expected_active_rule_count": expected_graph["rule_count"] == count,
            }
            reps.append({"repeat": rep, "arms": runs, "checks": checks})
        rows.append({"active_rule_count": count, "graph_nodes": 2, "graph_edges": 1,
                     "repetitions": reps})
    inputs = {"protocol": sha(PREREG), "runner": sha(Path(__file__)),
              "graph_rs": sha(ROOT / "runners/dsl/src/graph.rs"),
              "substrate_rs": sha(ROOT / "runners/dsl/src/substrate.rs"),
              "rewrite_rs": sha(ROOT / "runners/dsl/src/rewrite.rs"),
              "py_rs": sha(ROOT / "runners/dsl/src/py.rs"),
              "scale_audit_rs": sha(ROOT / "runners/dsl/src/scale_audit.rs"),
              "native": sha(NATIVE), "rust_source_fingerprint": rust_source_fingerprint(str(ROOT))}
    payload = {"protocol_id": "SUBSTRATE_BORROWED_SCOPED_RULES_CONFIRMATION_20260926", "rule_counts": list(RULE_COUNTS),
               "repeats": REPEATS, "calls_per_batch": CALLS, "apis": list(APIS), "inputs": inputs, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    vals = [v for row in rows for rep in row["repetitions"] for v in rep["checks"].values()]
    print(json.dumps({"output": str(OUT), "cells": len(vals) // 6, "passed": sum(vals), "total": len(vals)}, indent=2))
    if not all(vals):
        raise SystemExit("one or more no-op cost probe gates failed")


if __name__ == "__main__":
    main()
