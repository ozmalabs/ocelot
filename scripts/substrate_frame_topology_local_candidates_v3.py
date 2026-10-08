#!/usr/bin/env python3
"""Matched topology comparison for scoped event scheduling vs full closure."""
from __future__ import annotations

import hashlib
import json
import statistics
import sys
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
from domains.engine_provenance import rust_source_fingerprint
from substrate_rs import And, Attr, Eq, Lit, NodeID, Not, Substrate, Var
from substrate_rs.ext import add_rule

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_LOCAL_CANDIDATE_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_frame_topology_local_candidates_v3_20260926.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
TOPOLOGIES = ("chain", "binary_tree", "star")
SIZES = (8, 16, 32, 64)
REPEATS = 5
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def topology_edges(name: str, n: int):
    if name == "chain":
        return [(i, i + 1) for i in range(n - 1)]
    if name == "binary_tree":
        return [((i - 1) // 2, i) for i in range(1, n)]
    if name == "star":
        return [(0, i) for i in range(1, n)]
    raise ValueError(name)


def fixture(name: str, n: int):
    s = Substrate()
    mts, concepts = [], []
    for i in range(n):
        mt = s.add_node("Microtheory", {"role": "root" if i == 0 else f"frame_{i}", "frame_index": i})
        concept = s.add_node("Concept", {"state": 0, "observed": False, "frame_index": i})
        s.add_edge_unchecked(mt, "has_concept", concept)
        mts.append(mt); concepts.append(concept)
    edges = topology_edges(name, n)
    for src, dst in edges:
        s.add_edge_unchecked(concepts[src], "causal_influence", concepts[dst])
    add_rule(s._inner, "propagate_on", [("src", "causal_influence", "dst")], [["set_attr", "dst", "state", 1]],
             where=And([Eq(Attr(Var("src"), "state"), Lit(1)), Eq(Attr(Var("dst"), "state"), Lit(0))]))
    add_rule(s._inner, "propagate_off", [("src", "causal_influence", "dst")], [["set_attr", "dst", "state", 0]],
             where=And([Eq(Attr(Var("src"), "state"), Lit(0)), Eq(Attr(Var("dst"), "state"), Lit(1))]))
    add_rule(s._inner, "observe_on", [("owner", "has_concept", "target")], [["set_attr", "target", "observed", True]],
             where=And([Eq(Attr(Var("target"), "state"), Lit(1)), Eq(Attr(Var("target"), "observed"), Lit(False))]))
    add_rule(s._inner, "observe_off", [("owner", "has_concept", "target")], [["set_attr", "target", "observed", False]],
             where=And([Eq(Attr(Var("target"), "state"), Lit(0)), Eq(Attr(Var("target"), "observed"), Lit(True))]))
    return s, mts, concepts, edges


def projection(s, concepts):
    return {"states": [s.node(n)["attrs"].get("state") for n in concepts],
            "observed": [s.node(n)["attrs"].get("observed") for n in concepts]}


def counters(inner):
    data = dict(inner.scale_audit_snapshot())
    return {key: int(data.get(key, 0)) for key in ("cand_enum", "term_evals_total", "term_units_total",
        "scoped_local_rule_matches", "scoped_mt_seeded_rule_matches", "scoped_full_fallback_rule_matches")}


def focused_control(kind, scoped):
    s = Substrate()
    mt = s.add_node("Microtheory", {"fixed": True})
    concept = s.add_node("Concept", {"selected": None, "visited": False})
    s.add_edge_unchecked(mt, "has_concept", concept)
    if kind == "order_sensitive":
        first = s.add_node("Source", {"label": "first"})
        second = s.add_node("Source", {"label": "second"})
        s.add_edge_unchecked(first, "choice_edge", concept)
        s.add_edge_unchecked(second, "choice_edge", concept)
        add_rule(s._inner, "order_choice", [("src", "choice_edge", "dst")],
                 [["set_attr", "dst", "selected", {"__term__": Attr(Var("src"), "label").to_dict()}]])
    elif kind == "deleted_type_reuse":
        source = s.add_node("Source", {"label": "only"})
        spare = s.add_node("Spare", {})
        s.add_edge_unchecked(source, "temporary_edge", spare)
        deleted = bool(s._inner.remove_edge_unchecked(source, "temporary_edge", spare))
        s.add_edge_unchecked(source, "choice_edge", concept)
        add_rule(s._inner, "after_reuse", [("src", "choice_edge", "dst")],
                 [["set_attr", "dst", "visited", True]])
    elif kind == "multi_edge_fallback":
        source = s.add_node("Source", {})
        middle = s.add_node("Middle", {})
        s.add_edge_unchecked(source, "first_link", middle)
        s.add_edge_unchecked(middle, "second_link", concept)
        add_rule(s._inner, "two_edge", [("src", "first_link", "mid"), ("mid", "second_link", "dst")],
                 [["set_attr", "dst", "visited", True]])
    else:
        raise ValueError(kind)
    s._inner.scale_audit_set_enabled(True); s._inner.scale_audit_reset()
    if scoped:
        steps = int(s._inner.run_rules_scoped(1 if kind == "order_sensitive" else CAP, False, mt))
    else:
        steps = int(s._inner.run_rules(1 if kind == "order_sensitive" else CAP))
    audit = counters(s._inner); s._inner.scale_audit_set_enabled(False)
    return {"steps": steps, "concept": s.node(concept)["attrs"], "deleted_edge": deleted if kind == "deleted_type_reuse" else None,
            "edge_reinserted": s.has_edge(source, "choice_edge", concept) if kind == "deleted_type_reuse" else None,
            "path_counters": audit}


def focused_controls():
    return {kind: {arm: focused_control(kind, arm == "scoped") for arm in ("full", "scoped")}
            for kind in ("order_sensitive", "deleted_type_reuse", "multi_edge_fallback")}


def scoped_settle(s, seeds, omit_owner=None):
    queue = deque(seeds)
    queued = {int(mt.value) for mt in queue}
    turns = steps = enqueues = 0
    affected = set()
    cap_hit = deferred = False
    start = time.perf_counter_ns()
    while queue and turns < CAP and steps < CAP:
        mt = queue.popleft(); queued.remove(int(mt.value)); turns += 1
        report = s._inner.run_rules_scoped_delta_report(mt, CAP - steps, False)
        steps += int(report["progress_steps"])
        cap_hit |= bool(report["hit_progress_budget"]); deferred |= bool(report["deferred_effects_pending"])
        if cap_hit or deferred:
            break
        if report["progress_steps"]:
            for raw in report["affected_microtheories"]:
                owner = int(raw); affected.add(owner)
                if owner == omit_owner or owner in queued:
                    continue
                queue.append(NodeID(owner)); queued.add(owner); enqueues += 1
    elapsed = time.perf_counter_ns() - start
    return {"complete": not queue and turns < CAP and not cap_hit and not deferred,
            "turns": turns, "progress_steps": steps, "enqueues": enqueues,
            "affected_owners": sorted(affected), "queue_remaining": sorted(queued),
            "cap_hit": cap_hit, "deferred_pending": deferred, "wall_ns": elapsed}


def event_arm(name, n, omission=False):
    s, mts, concepts, edges = fixture(name, n)
    s._inner.scale_audit_set_enabled(True)
    omitted_owner = int(mts[-1].value) if omission else None
    phases = []
    for state in (1, 0):
        s._inner.scale_audit_reset()
        if state == 1:
            s.set_attr(concepts[0], "state", 1)
        else:
            s.set_attr(concepts[0], "state", 0)
        closure = scoped_settle(s, [mts[0]], omitted_owner if state == 1 else None)
        closure["audit"] = counters(s._inner)
        closure["projection"] = projection(s, concepts)
        phases.append(closure)
    s._inner.scale_audit_set_enabled(False)
    return {"phases": phases, "edges": edges, "frame_ids": [int(mt.value) for mt in mts]}


def full_arm(name, n):
    s, mts, concepts, edges = fixture(name, n)
    s._inner.scale_audit_set_enabled(True)
    phases = []
    for state in (1, 0):
        s._inner.scale_audit_reset()
        s.set_attr(concepts[0], "state", state)
        start = time.perf_counter_ns()
        report = s._inner.run_rules_report(CAP, False)
        elapsed = time.perf_counter_ns() - start
        phases.append({"status": report["status"], "progress_steps": int(report["progress_steps"]),
                       "budget_overshoot": int(report.get("budget_overshoot", 0)),
                       "wall_ns": elapsed, "audit": counters(s._inner),
                       "projection": projection(s, concepts)})
    s._inner.scale_audit_set_enabled(False)
    return {"phases": phases, "edges": edges, "frame_ids": [int(mt.value) for mt in mts]}


def main():
    rows = []
    for topology in TOPOLOGIES:
        for n in SIZES:
            reps = []
            for rep in range(REPEATS):
                if rep % 2:
                    event, full = event_arm(topology, n), full_arm(topology, n)
                else:
                    full, event = full_arm(topology, n), event_arm(topology, n)
                omission = event_arm(topology, n, omission=True)
                expected_owners = event["frame_ids"]
                gates = {
                    "matched_graph_cardinality": len(event["edges"]) == n - 1 and len(full["edges"]) == n - 1 and event["edges"] == full["edges"],
                    "full_arms_fixed_point": all(p["status"] == "fixed_point" for p in full["phases"]),
                    "event_settles_both_phases": all(p["complete"] for p in event["phases"]),
                    "event_full_projection_parity": all(event["phases"][i]["projection"] == full["phases"][i]["projection"] for i in range(2)),
                    "notifications_cover_every_frame": all(p["affected_owners"] == expected_owners for p in event["phases"]),
                    "omitted_leaf_observation_stale": omission["phases"][0]["projection"]["states"][-1] == 1 and omission["phases"][0]["projection"]["observed"][-1] is False and omission["phases"][0]["projection"] != full["phases"][0]["projection"],
                    "audit_counters_present": all(all(k in p["audit"] for k in ("cand_enum", "term_evals_total", "term_units_total", "scoped_local_rule_matches", "scoped_mt_seeded_rule_matches", "scoped_full_fallback_rule_matches")) for arm in (event, full) for p in arm["phases"]),
                    "event_path_selection_exact": all(p["audit"]["scoped_local_rule_matches"] > 0 and p["audit"]["scoped_mt_seeded_rule_matches"] > 0 and p["audit"]["scoped_full_fallback_rule_matches"] == 0 for p in event["phases"]),
                    "full_path_selection_zero": all(p["audit"]["scoped_local_rule_matches"] == 0 and p["audit"]["scoped_mt_seeded_rule_matches"] == 0 and p["audit"]["scoped_full_fallback_rule_matches"] == 0 for p in full["phases"]),
                    "event_has_no_cap_or_deferred": all(not p["cap_hit"] and not p["deferred_pending"] for p in event["phases"]),
                }
                reps.append({"repeat": rep, "event": event, "full": full, "omission": omission, "gates": gates})
            rows.append({"topology": topology, "frame_count": n, "node_count": 2 * n,
                         "dependency_edge_count": n - 1, "rule_count": 4, "repetitions": reps})
    inputs = {"protocol": sha(PREREG), "runner": sha(Path(__file__)),
              "graph_rs": sha(ROOT / "runners/dsl/src/graph.rs"),
              "substrate_rs": sha(ROOT / "runners/dsl/src/substrate.rs"),
              "rewrite_rs": sha(ROOT / "runners/dsl/src/rewrite.rs"),
              "py_rs": sha(ROOT / "runners/dsl/src/py.rs"), "scale_audit_rs": sha(ROOT / "runners/dsl/src/scale_audit.rs"),
              "native": sha(NATIVE), "rust_source_fingerprint": rust_source_fingerprint(str(ROOT))}
    controls = focused_controls()
    focused_gates = {
        "order_sensitive_state_and_progress": controls["order_sensitive"]["full"]["concept"] == controls["order_sensitive"]["scoped"]["concept"]
            and controls["order_sensitive"]["full"]["concept"]["selected"] is not None
            and controls["order_sensitive"]["scoped"]["concept"]["selected"] is not None
            and controls["order_sensitive"]["full"]["steps"] == controls["order_sensitive"]["scoped"]["steps"] == 1,
        "order_case_uses_local_path": controls["order_sensitive"]["scoped"]["path_counters"]["scoped_local_rule_matches"] > 0
            and controls["order_sensitive"]["scoped"]["path_counters"]["scoped_full_fallback_rule_matches"] == 0,
        "deleted_edge_reuse_falls_back": controls["deleted_type_reuse"]["scoped"]["deleted_edge"]
            and controls["deleted_type_reuse"]["scoped"]["edge_reinserted"]
            and controls["deleted_type_reuse"]["full"]["concept"] == controls["deleted_type_reuse"]["scoped"]["concept"]
            and controls["deleted_type_reuse"]["scoped"]["path_counters"]["scoped_full_fallback_rule_matches"] > 0
            and controls["deleted_type_reuse"]["scoped"]["path_counters"]["scoped_local_rule_matches"] == 0,
        "multi_edge_rule_falls_back": controls["multi_edge_fallback"]["full"]["concept"] == controls["multi_edge_fallback"]["scoped"]["concept"]
            and controls["multi_edge_fallback"]["scoped"]["path_counters"]["scoped_full_fallback_rule_matches"] > 0
            and controls["multi_edge_fallback"]["scoped"]["path_counters"]["scoped_local_rule_matches"] == 0,
    }
    payload = {"protocol_id": "SUBSTRATE_SCOPED_LOCAL_CANDIDATE_20260926",
               "topologies": list(TOPOLOGIES), "sizes": list(SIZES), "repeats": REPEATS,
               "inputs": inputs, "rows": rows, "focused_controls": controls, "focused_control_gates": focused_gates}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    gates = [v for row in rows for rep in row["repetitions"] for v in rep["gates"].values()]
    print(json.dumps({"output": str(OUT), "instances": len(gates) // 10,
                      "passed": sum(gates) + sum(focused_gates.values()), "total": len(gates) + len(focused_gates),
                      "focused_control_gates": focused_gates}, indent=2))
    if not all(gates) or not all(focused_gates.values()):
        raise SystemExit("one or more preregistered topology gates failed")


if __name__ == "__main__":
    main()
