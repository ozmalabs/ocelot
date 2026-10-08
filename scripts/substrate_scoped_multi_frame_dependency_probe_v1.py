#!/usr/bin/env python3
"""Three-frame notification probe for birth/deletion with two dependencies."""
from __future__ import annotations

import hashlib
import json
import sys
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
from domains.engine_provenance import rust_source_fingerprint
from substrate_rs import And, Attr, Count, Eq, InNeighbours, Lit, NodeID, Not, Substrate, Var
from substrate_rs.ext import add_rule

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_MULTI_FRAME_DEPENDENCY_PREREG_20260926.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_MULTI_FRAME_DEPENDENCY_V1_1_AMENDMENT_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_scoped_multi_frame_dependency_probe_v1_20260926.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture():
    s = Substrate()
    a, b, c = [s.add_node("Microtheory", {"role": role}) for role in ("A", "B", "C")]
    ca = s.add_node("Concept", {"trigger": True, "emitted": False})
    cb = s.add_node("Concept", {"state": 0})
    cc = s.add_node("Concept", {"state": 0})
    for mt, concept in ((a, ca), (b, cb), (c, cc)):
        s.add_edge_unchecked(mt, "has_concept", concept)
    add_rule(s._inner, "mint_two_frame_bridge", [("ma", "has_concept", "x"), ("mb", "has_concept", "y"), ("mc", "has_concept", "z")], [
        ["add_node", "bridge", "Concept", {"delete_request": False}],
        ["add_edge", "ma", "has_concept", "bridge", {}],
        ["add_edge", "bridge", "causal_influence", "y", {}],
        ["add_edge", "bridge", "causal_influence", "z", {}],
        ["set_attr", "x", "emitted", True],
    ], where=And([Eq(Attr(Var("x"), "trigger"), Lit(True)), Eq(Attr(Var("x"), "emitted"), Lit(False)),
                  Eq(Attr(Var("ma"), "role"), Lit("A")), Eq(Attr(Var("mb"), "role"), Lit("B")),
                  Eq(Attr(Var("mc"), "role"), Lit("C"))]))
    add_rule(s._inner, "consume_influence", [("mt", "has_concept", "target")], [["set_attr", "target", "state", 1]],
             where=And([Eq(Attr(Var("target"), "state"), Lit(0)), Not(Eq(Count(InNeighbours(Var("target"), "causal_influence")), Lit(0)))]))
    add_rule(s._inner, "retract_influence", [("mt", "has_concept", "target")], [["set_attr", "target", "state", 0]],
             where=And([Eq(Attr(Var("target"), "state"), Lit(1)), Eq(Count(InNeighbours(Var("target"), "causal_influence")), Lit(0))]))
    add_rule(s._inner, "delete_bridge", [("ma", "has_concept", "bridge"), ("mb", "has_concept", "target"), ("bridge", "causal_influence", "target")], [["del_node", "bridge"]],
             where=And([Eq(Attr(Var("bridge"), "delete_request"), Lit(True)), Eq(Attr(Var("mb"), "role"), Lit("B"))]))
    return s, (a, b, c), (ca, cb, cc)


def projection(s, mts, concepts):
    a, b, c = mts
    ca, cb, cc = concepts
    bridges = [n for n in s.nodes("Concept") if s.node(n)["attrs"].get("delete_request") is not None]
    bridge = bridges[0] if bridges else None
    return {
        "emitted": s.node(ca)["attrs"].get("emitted"),
        "states": [s.node(cb)["attrs"].get("state"), s.node(cc)["attrs"].get("state")],
        "concept_count": len(s.nodes("Concept")),
        "bridge_id": int(bridge.value) if bridge else None,
        "bridge_owned": bool(bridge and s.has_edge(a, "has_concept", bridge)),
        "dependency_edges": [bool(bridge and s.has_edge(bridge, "causal_influence", target)) for target in (cb, cc)],
        "owners": [int(mt.value) for mt in mts],
    }


def settle(s, seeds):
    queue = deque(seeds)
    queued = {int(mt.value) for mt in queue}
    reports, notified = [], set()
    while queue and len(reports) < 100:
        mt = queue.popleft(); queued.remove(int(mt.value))
        report = s._inner.run_rules_scoped_delta_report(mt, 1000, False)
        reports.append(report)
        if report["hit_progress_budget"] or report["deferred_effects_pending"]:
            break
        if report["progress_steps"]:
            for owner in report["affected_microtheories"]:
                owner = int(owner); notified.add(owner)
                if owner not in queued:
                    queue.append(NodeID(owner)); queued.add(owner)
    return {"complete": not queue and len(reports) < 100 and all(not r["hit_progress_budget"] and not r["deferred_effects_pending"] for r in reports),
            "reports": reports, "notified": sorted(notified), "queue_remaining": sorted(queued)}


def event_arm(seed=True):
    s, mts, concepts = fixture()
    birth = settle(s, [mts[0]] if seed else [])
    born = projection(s, mts, concepts)
    if born["bridge_id"] is not None:
        s.set_attr(NodeID(born["bridge_id"]), "delete_request", True)
        deletion = settle(s, [mts[0]])
    else:
        deletion = {"complete": False, "reports": [], "notified": [], "queue_remaining": []}
    return {"birth": birth, "born": born, "deletion": deletion, "ended": projection(s, mts, concepts)}


def full_arm():
    s, mts, concepts = fixture()
    birth = s._inner.run_rules_report(1000, False)
    born = projection(s, mts, concepts)
    if born["bridge_id"] is not None:
        s.set_attr(NodeID(born["bridge_id"]), "delete_request", True)
        deletion = s._inner.run_rules_report(1000, False)
    else:
        deletion = {"status": "no_bridge"}
    return {"birth": birth, "born": born, "deletion": deletion, "ended": projection(s, mts, concepts)}


def main():
    event, omitted, oracle = event_arm(), event_arm(False), full_arm()
    def owner_set(stage):
        return sorted({int(x) for r in stage["reports"] for x in r["affected_microtheories"]})
    gates = {
        "birth_notifies_exactly_three_owners": owner_set(event["birth"]) == event["born"]["owners"],
        "deletion_notifies_exactly_three_owners": owner_set(event["deletion"]) == event["ended"]["owners"],
        "event_queue_settles_both_stages": event["birth"]["complete"] and event["deletion"]["complete"],
        "birth_event_matches_full": event["born"] == oracle["born"],
        "deletion_event_matches_full": event["ended"] == oracle["ended"],
        "full_closure_reaches_fixed_points": oracle["birth"]["status"] == oracle["deletion"]["status"] == "fixed_point",
        "omitted_seed_stays_unminted_and_diverges": omitted["born"]["bridge_id"] is None and omitted["born"] != oracle["born"],
        "birth_has_both_cross_frame_edges": event["born"]["dependency_edges"] == [True, True],
        "deletion_removes_both_cross_frame_edges": event["ended"]["dependency_edges"] == [False, False],
    }
    inputs = {
        "preregistration": sha(PREREG), "amendment": sha(AMENDMENT), "runner": sha(Path(__file__)),
        "graph_rs": sha(ROOT / "runners/dsl/src/graph.rs"),
        "substrate_rs": sha(ROOT / "runners/dsl/src/substrate.rs"),
        "rewrite_rs": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "py_rs": sha(ROOT / "runners/dsl/src/py.rs"), "native": sha(NATIVE),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
    }
    payload = {"protocol": "SUBSTRATE_SCOPED_MULTI_FRAME_DEPENDENCY_PREREG_20260926_V1_1", "inputs": inputs,
               "gates": gates, "event": event, "omitted_seed_control": omitted, "full_oracle": oracle}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "gates": gates}, indent=2))
    if not all(gates.values()):
        raise SystemExit("one or more preregistered gates failed")


if __name__ == "__main__":
    main()
