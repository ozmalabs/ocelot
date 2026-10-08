#!/usr/bin/env python3
"""Check audited/uninstrumented semantic parity on the N=64 topology fixture."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), str(ROOT)]
from domains.engine_provenance import build_is_stale, rust_source_fingerprint

BASE = ROOT / "scripts/substrate_frame_topology_matched_scale_v1.py"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPE_AUDIT_ON_OFF_PARITY_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_scope_audit_on_off_parity_v1_20260926.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
N, REPEATS, CAP = 64, 5, 100_000

spec = importlib.util.spec_from_file_location("topology_base", BASE)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_event(topology, audit):
    s, mts, concepts, edges = base.fixture(topology, N)
    inner = s._inner
    inner.scale_audit_set_per_rule_enabled(False); inner.scale_audit_per_rule_reset()
    inner.scale_audit_set_enabled(audit)
    phases = []
    for value in (1, 0):
        inner.scale_audit_reset()
        s.set_attr(concepts[0], "state", value)
        start = time.perf_counter_ns()
        settle = base.scoped_settle(s, [mts[0]])
        elapsed = time.perf_counter_ns() - start
        phases.append({"settlement": settle, "projection": base.projection(s, concepts),
                       "audit": dict(inner.scale_audit_snapshot()), "wall_ns": elapsed})
    per_rule_rows = list(inner.scale_audit_per_rule_snapshot())
    inner.scale_audit_set_enabled(False)
    return {"phases": phases, "edges": edges, "per_rule_rows": len(per_rule_rows),
            "frame_ids": [int(mt.value) for mt in mts], "rule_count": inner.rule_count()}


def run_full(topology, audit):
    s, mts, concepts, edges = base.fixture(topology, N)
    inner = s._inner
    inner.scale_audit_set_per_rule_enabled(False); inner.scale_audit_per_rule_reset()
    inner.scale_audit_set_enabled(audit)
    phases = []
    for value in (1, 0):
        inner.scale_audit_reset()
        s.set_attr(concepts[0], "state", value)
        start = time.perf_counter_ns()
        report = inner.run_rules_report(CAP, False)
        elapsed = time.perf_counter_ns() - start
        phases.append({"status": report["status"], "progress_steps": int(report["progress_steps"]),
                       "projection": base.projection(s, concepts),
                       "audit": dict(inner.scale_audit_snapshot()), "wall_ns": elapsed})
    per_rule_rows = list(inner.scale_audit_per_rule_snapshot())
    inner.scale_audit_set_enabled(False)
    return {"phases": phases, "edges": edges, "per_rule_rows": len(per_rule_rows),
            "frame_ids": [int(mt.value) for mt in mts], "rule_count": inner.rule_count()}


def main():
    if build_is_stale(str(ROOT)):
        raise SystemExit("refusing to measure: native build is stale")
    rows = []
    for topology in base.TOPOLOGIES:
        reps = []
        for rep in range(REPEATS):
            if rep % 2:
                event_off, event_on, full_off, full_on = (run_event(topology, False), run_event(topology, True),
                                                           run_full(topology, False), run_full(topology, True))
            else:
                full_on, full_off, event_on, event_off = (run_full(topology, True), run_full(topology, False),
                                                           run_event(topology, True), run_event(topology, False))
            gates = {
                "fixture_cardinality_matches": all(x["rule_count"] == 4 and len(x["edges"]) == N - 1 for x in (event_off, event_on, full_off, full_on)),
                "event_audit_mode_projection_equal": all(event_off["phases"][i]["projection"] == event_on["phases"][i]["projection"] for i in (0, 1)),
                "full_audit_mode_projection_equal": all(full_off["phases"][i]["projection"] == full_on["phases"][i]["projection"] for i in (0, 1)),
                "event_full_parity_when_off": all(event_off["phases"][i]["projection"] == full_off["phases"][i]["projection"] for i in (0, 1)),
                "event_full_parity_when_on": all(event_on["phases"][i]["projection"] == full_on["phases"][i]["projection"] for i in (0, 1)),
                "event_settles_and_notifies_all": all(p["settlement"]["complete"] and p["settlement"]["affected_owners"] == event_off["frame_ids"] for p in event_off["phases"] + event_on["phases"]),
                "full_fixed_point_both_modes": all(p["status"] == "fixed_point" for arm in (full_off, full_on) for p in arm["phases"]),
                "audit_counter_on_off_contract": all(all(v == 0 for v in p["audit"].values()) for arm in (event_off, full_off) for p in arm["phases"]) and all(int(p["audit"].get("cand_enum", 0)) > 0 and int(p["audit"].get("term_evals_total", 0)) > 0 for arm in (event_on, full_on) for p in arm["phases"]),
                "per_rule_audit_remains_disabled": all(x["per_rule_rows"] == 0 for x in (event_off, event_on, full_off, full_on)),
            }
            reps.append({"repeat": rep, "event_off": event_off, "event_on": event_on,
                         "full_off": full_off, "full_on": full_on, "gates": gates})
        rows.append({"topology": topology, "frame_count": N, "concept_count": N,
                     "dependency_edge_count": N - 1, "rule_count": 4, "repetitions": reps})
    inputs = {"protocol": sha(PREREG), "runner": sha(Path(__file__)), "base_runner": sha(BASE),
              "graph_rs": sha(ROOT / "runners/dsl/src/graph.rs"),
              "substrate_rs": sha(ROOT / "runners/dsl/src/substrate.rs"),
              "rewrite_rs": sha(ROOT / "runners/dsl/src/rewrite.rs"),
              "py_rs": sha(ROOT / "runners/dsl/src/py.rs"),
              "scale_audit_rs": sha(ROOT / "runners/dsl/src/scale_audit.rs"),
              "native": sha(NATIVE), "rust_source_fingerprint": rust_source_fingerprint(str(ROOT))}
    payload = {"protocol_id": "SUBSTRATE_SCOPE_AUDIT_ON_OFF_PARITY_PREREG_20260926",
               "frame_count": N, "repeats": REPEATS, "inputs": inputs, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    gates = [v for row in rows for rep in row["repetitions"] for v in rep["gates"].values()]
    print(json.dumps({"output": str(OUT), "instances": len(gates) // 9,
                      "passed": sum(gates), "total": len(gates)}, indent=2))
    if not all(gates):
        raise SystemExit("one or more audit parity gates failed")


if __name__ == "__main__":
    main()
