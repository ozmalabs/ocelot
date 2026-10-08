#!/usr/bin/env python3
"""Preregistered two-frame node birth/deletion notification diagnostic."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
from domains.engine_provenance import rust_source_fingerprint
from substrate_rs import Attr, Eq, Lit, NodeID, Not, Substrate, Var
from substrate_rs.ext import add_rule

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_NODE_LIFECYCLE_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_scoped_node_lifecycle_probe_v1_20260926.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture():
    s = Substrate()
    a = s.add_node("Microtheory", {})
    b = s.add_node("Microtheory", {})
    ca = s.add_node("Concept", {"trigger": True, "emitted": False})
    cb = s.add_node("Concept", {"state": 0})
    s.add_edge_unchecked(a, "has_concept", ca)
    s.add_edge_unchecked(b, "has_concept", cb)
    add_rule(s._inner, "mint_bridge", [("ma", "has_concept", "x"), ("mb", "has_concept", "y")], [
        ["add_node", "z", "Concept", {"delete_request": False}],
        ["add_edge", "ma", "has_concept", "z", {}],
        ["add_edge", "z", "causal_influence", "y", {}],
        ["set_attr", "x", "emitted", True],
    ], where=And([Eq(Attr(Var("x"), "trigger"), Lit(True)), Eq(Attr(Var("x"), "emitted"), Lit(False))]))
    add_rule(s._inner, "consume_bridge", [("mb", "has_concept", "y")], [["set_attr", "y", "state", 1]],
             where=And([Eq(Attr(Var("y"), "state"), Lit(0)), Not(Eq(Count(InNeighbours(Var("y"), "causal_influence")), Lit(0)))]))
    add_rule(s._inner, "retract_bridge", [("mb", "has_concept", "y")], [["set_attr", "y", "state", 0]],
             where=And([Eq(Attr(Var("y"), "state"), Lit(1)), Eq(Count(InNeighbours(Var("y"), "causal_influence")), Lit(0))]))
    add_rule(s._inner, "delete_bridge", [("ma", "has_concept", "z"), ("z", "causal_influence", "y")], [["del_node", "z"]],
             where=Eq(Attr(Var("z"), "delete_request"), Lit(True)))
    return s, a, b, ca, cb


def add_terms_imports():
    global And, Count, InNeighbours
    from substrate_rs import And, Count, InNeighbours


def projection(s, a, b, ca, cb):
    nodes = s.nodes("Concept")
    node_rows = [s._inner.node(n) for n in nodes]
    bridge_rows = [r for r in node_rows if r["attrs"].get("delete_request") is not None]
    bridge = bridge_rows[0]["id"] if bridge_rows else None
    return {
        "emitted": s._inner.node(ca)["attrs"].get("emitted"),
        "b_state": s._inner.node(cb)["attrs"].get("state"),
        "concept_count": len(nodes),
        "bridge_id": int(bridge.value) if bridge is not None else None,
        "bridge_owned": bool(bridge is not None and s._inner.has_edge(a, "has_concept", bridge)),
        "causal_edge": bool(bridge is not None and s._inner.has_edge(bridge, "causal_influence", cb)),
        "owners": [int(a.value), int(b.value)],
    }


def full(s):
    return s._inner.run_rules_report(1000, False)


def settle(s, seeds):
    queue = deque(seeds)
    queued = {int(mt.value) for mt in queue}
    reports = []
    notified = set()
    while queue and len(reports) < 100:
        mt = queue.popleft(); queued.remove(int(mt.value))
        r = s._inner.run_rules_scoped_delta_report(mt, 1000, False)
        reports.append(r)
        if r["hit_progress_budget"] or r["deferred_effects_pending"]:
            break
        if r["progress_steps"]:
            for owner in r["affected_microtheories"]:
                owner = int(owner); notified.add(owner)
                if owner not in queued:
                    queue.append(NodeID(owner)); queued.add(owner)
    return {"complete": not queue and len(reports) < 100 and all(not r["hit_progress_budget"] and not r["deferred_effects_pending"] for r in reports),
            "reports": reports, "notified": sorted(notified), "queue_remaining": sorted(queued)}


def run_event(seed=True):
    s, a, b, ca, cb = fixture()
    birth = settle(s, [a] if seed else [])
    born = projection(s, a, b, ca, cb)
    bridge_id = born["bridge_id"]
    if bridge_id is not None:
        s.set_attr(NodeID(bridge_id), "delete_request", True)
    deletion = settle(s, [a]) if bridge_id is not None else {"complete": False, "reports": [], "notified": [], "queue_remaining": []}
    ended = projection(s, a, b, ca, cb)
    return {"birth": birth, "born": born, "deletion": deletion, "ended": ended}


def run_full():
    s, a, b, ca, cb = fixture()
    birth = full(s); born = projection(s, a, b, ca, cb)
    bridge_id = born["bridge_id"]
    if bridge_id is not None:
        s.set_attr(NodeID(bridge_id), "delete_request", True)
    deletion = full(s) if bridge_id is not None else {"status": "no_bridge"}
    return {"birth": birth, "born": born, "deletion": deletion, "ended": projection(s, a, b, ca, cb)}


def main():
    add_terms_imports()
    event = run_event(True); omitted = run_event(False); oracle = run_full()
    def owner_set(stage):
        reports = stage["reports"]
        return sorted({int(m) for r in reports for m in r["affected_microtheories"]})
    gates = {
        "birth_owner_notifications_exact": owner_set(event["birth"]) == [*event["born"]["owners"]],
        "deletion_owner_notifications_exact": owner_set(event["deletion"]) == [*event["ended"]["owners"]],
        "birth_settles": event["birth"]["complete"],
        "deletion_settles": event["deletion"]["complete"],
        "event_matches_full_birth": event["born"] == oracle["born"],
        "event_matches_full_end": event["ended"] == oracle["ended"],
        "full_reference_fixed_points": oracle["birth"]["status"] == oracle["deletion"]["status"] == "fixed_point",
        "omitted_seed_is_detectably_stale": omitted["born"] != oracle["born"],
        "omitted_seed_does_not_mint": omitted["born"]["bridge_id"] is None,
    }
    inputs = {
        "preregistration": sha(PREREG), "runner": sha(Path(__file__)),
        "graph_rs": sha(ROOT / "runners/dsl/src/graph.rs"),
        "substrate_rs": sha(ROOT / "runners/dsl/src/substrate.rs"),
        "rewrite_rs": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "py_rs": sha(ROOT / "runners/dsl/src/py.rs"),
        "native": sha(NATIVE), "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
    }
    payload = {"protocol": "SUBSTRATE_SCOPED_NODE_LIFECYCLE_PREREG_20260926", "inputs": inputs,
               "gates": gates, "event": event, "omitted_seed_control": omitted, "full_oracle": oracle}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "gates": gates}, indent=2))
    if not all(gates.values()):
        raise SystemExit("one or more preregistered gates failed")


if __name__ == "__main__":
    main()
