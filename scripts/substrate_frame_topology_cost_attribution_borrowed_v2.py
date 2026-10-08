#!/usr/bin/env python3
"""Per-rule counter attribution on the matched N=64 topology fixtures."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(ROOT)]
from domains.engine_provenance import rust_source_fingerprint
from substrate_rs import And, Attr, Eq, Lit, NodeID, Not, Var
from substrate_rs.ext import add_rule

BASE = ROOT / "scripts/substrate_frame_topology_matched_scale_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_BORROWED_SCOPED_RULES_CONFIRMATION_PREREG_20260926.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_FRAME_TOPOLOGY_COST_ATTRIBUTION_V1_1_AMENDMENT_20260926.md"
BASE_PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_FRAME_TOPOLOGY_MATCHED_SCALE_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_frame_topology_cost_attribution_borrowed_v2_20260926.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
N = 64
REPEATS = 10
CAP = 100_000

spec = importlib.util.spec_from_file_location("topology_base", BASE)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rule_names(inner):
    return {int(row[0]): str(row[1]) for row in inner.rule_access_sets()}


def capture_per_rule(inner, names):
    return [{"rule_index": int(idx), "rule_name": names.get(int(idx), f"rule_{idx}"),
             "metric": str(metric), "count": int(count)}
            for idx, metric, count in inner.scale_audit_per_rule_snapshot()]


def insert_inactive_rule_gap(s):
    """Move propagate_off out of slot 1, leaving an inactive index gap."""
    inner = s._inner
    if not inner.remove_rule(1):
        raise RuntimeError("failed to tombstone the preregistered rule slot")
    add_rule(inner, "propagate_off", [("src", "causal_influence", "dst")],
             [["set_attr", "dst", "state", 0]],
             where=And([Eq(Attr(Var("src"), "state"), Lit(0)),
                        Eq(Attr(Var("dst"), "state"), Lit(1))]))


def execute_event(topology):
    s, mts, concepts, edges = base.fixture(topology, N)
    insert_inactive_rule_gap(s)
    inner = s._inner
    inner.scale_audit_set_enabled(True); inner.scale_audit_set_per_rule_enabled(True)
    names = rule_names(inner)
    phases = []
    for value in (1, 0):
        inner.scale_audit_reset(); inner.scale_audit_per_rule_reset()
        inner.set_attr(concepts[0], "state", value)
        start = time.perf_counter_ns()
        settle = base.scoped_settle(s, [mts[0]])
        elapsed = time.perf_counter_ns() - start
        phases.append({"settlement": settle, "projection": base.projection(s, concepts),
                       "global": dict(inner.scale_audit_snapshot()),
                       "per_rule": capture_per_rule(inner, names), "wall_ns": elapsed})
    inner.scale_audit_set_per_rule_enabled(False); inner.scale_audit_set_enabled(False)
    return {"phases": phases, "edges": edges, "frame_ids": [int(mt.value) for mt in mts]}


def execute_full(topology):
    s, mts, concepts, edges = base.fixture(topology, N)
    insert_inactive_rule_gap(s)
    inner = s._inner
    inner.scale_audit_set_enabled(True); inner.scale_audit_set_per_rule_enabled(True)
    names = rule_names(inner)
    phases = []
    for value in (1, 0):
        inner.scale_audit_reset(); inner.scale_audit_per_rule_reset()
        inner.set_attr(concepts[0], "state", value)
        start = time.perf_counter_ns()
        report = inner.run_rules_report(CAP, False)
        elapsed = time.perf_counter_ns() - start
        phases.append({"status": report["status"], "progress_steps": int(report["progress_steps"]),
                       "projection": base.projection(s, concepts), "global": dict(inner.scale_audit_snapshot()),
                       "per_rule": capture_per_rule(inner, names), "wall_ns": elapsed})
    inner.scale_audit_set_per_rule_enabled(False); inner.scale_audit_set_enabled(False)
    return {"phases": phases, "edges": edges, "frame_ids": [int(mt.value) for mt in mts]}


def main():
    rows = []
    for topology in base.TOPOLOGIES:
        pairs = []
        for rep in range(REPEATS):
            event, full = (execute_event(topology), execute_full(topology)) if rep % 2 else (execute_full(topology), execute_event(topology))
            # The alternating assignment above is normalized by detecting each arm's fields.
            if "phases" not in event or "settlement" not in event["phases"][0]:
                event, full = full, event
            gates = {
                "matched_fixture": len(event["edges"]) == len(full["edges"]) == N - 1 and event["edges"] == full["edges"],
                "event_full_projection_parity": all(event["phases"][i]["projection"] == full["phases"][i]["projection"] for i in (0, 1)),
                "event_settles_both_phases": all(p["settlement"]["complete"] for p in event["phases"]),
                "full_fixed_points_both_phases": all(p["status"] == "fixed_point" for p in full["phases"]),
                "event_owner_coverage": all(p["settlement"]["affected_owners"] == event["frame_ids"] for p in event["phases"]),
                "per_rule_original_indices_and_names": all(
                    {int(r["rule_index"]) for r in phase["per_rule"] if r["metric"] == "rule_enumerations"} == {0, 2, 3, 4}
                    and {int(r["rule_index"]): r["rule_name"] for r in phase["per_rule"] if r["metric"] == "rule_enumerations"}
                    == {0: "propagate_on", 2: "observe_on", 3: "observe_off", 4: "propagate_off"}
                    for arm in (event, full) for phase in arm["phases"]),
            }
            pairs.append({"repeat": rep, "event": event, "full": full, "gates": gates})
        rows.append({"topology": topology, "frame_count": N, "concept_count": N,
                     "dependency_edge_count": N - 1, "active_rule_count": 4, "pairs": pairs})
    inputs = {"protocol": sha(PREREG), "amendment": sha(AMENDMENT), "base_protocol": sha(BASE_PREREG), "runner": sha(Path(__file__)),
              "base_runner": sha(BASE), "graph_rs": sha(ROOT / "runners/dsl/src/graph.rs"),
              "substrate_rs": sha(ROOT / "runners/dsl/src/substrate.rs"),
              "rewrite_rs": sha(ROOT / "runners/dsl/src/rewrite.rs"),
              "py_rs": sha(ROOT / "runners/dsl/src/py.rs"), "scale_audit_rs": sha(ROOT / "runners/dsl/src/scale_audit.rs"),
              "native": sha(NATIVE), "rust_source_fingerprint": rust_source_fingerprint(str(ROOT))}
    payload = {"protocol_id": "SUBSTRATE_BORROWED_SCOPED_RULES_CONFIRMATION_20260926_PER_RULE",
               "frame_count": N, "repeats": REPEATS, "inputs": inputs, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    gates = [v for row in rows for pair in row["pairs"] for v in pair["gates"].values()]
    print(json.dumps({"output": str(OUT), "pairs": len(gates) // 6, "passed": sum(gates), "total": len(gates)}, indent=2))
    if not all(gates):
        raise SystemExit("one or more preregistered attribution gates failed")


if __name__ == "__main__":
    main()
