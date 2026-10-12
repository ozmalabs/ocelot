#!/usr/bin/env python3
"""Repeated generated star-fanout scaling probe for native scoped notifications."""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
from domains.engine_provenance import rust_source_fingerprint
from substrate_rs import And, Attr, Count, Eq, InNeighbours, Lit, NodeID, Not, Substrate, Var
from substrate_rs.ext import add_rule

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_NOTIFICATION_FANOUT_SCALE_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_scoped_notification_fanout_scale_v1_20260926.json"
NATIVE = ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"
SIZES = (2, 4, 8, 16, 32, 64)
REPEATS = 5
CAP = 100_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(n: int):
    s = Substrate()
    mts, concepts = [], []
    for i in range(n):
        role = "A" if i == 0 else f"F{i}"
        mt = s.add_node("Microtheory", {"role": role})
        attrs = {"role": role}
        if i == 0:
            attrs.update(trigger=True, emitted=False)
        else:
            attrs.update(state=0, linked=False)
        concept = s.add_node("Concept", attrs)
        s.add_edge_unchecked(mt, "has_concept", concept)
        mts.append(mt); concepts.append(concept)
    add_rule(s._inner, "mint_root", [("owner", "has_concept", "trigger")], [
        ["add_node", "bridge", "Concept", {"delete_request": False}],
        ["add_edge", "owner", "has_concept", "bridge", {}],
        ["set_attr", "trigger", "emitted", True],
    ], where=And([Eq(Attr(Var("owner"), "role"), Lit("A")),
                  Eq(Attr(Var("trigger"), "trigger"), Lit(True)),
                  Eq(Attr(Var("trigger"), "emitted"), Lit(False))]))
    add_rule(s._inner, "link_all_frames", [("root", "has_concept", "bridge"), ("owner", "has_concept", "target")], [
        ["add_edge", "bridge", "causal_influence", "target", {}],
        ["set_attr", "target", "linked", True],
    ], where=And([Eq(Attr(Var("bridge"), "delete_request"), Lit(False)),
                  Not(Eq(Attr(Var("owner"), "role"), Lit("A"))),
                  Eq(Attr(Var("target"), "linked"), Lit(False))]))
    add_rule(s._inner, "consume_local", [("owner", "has_concept", "target")], [["set_attr", "target", "state", 1]],
             where=And([Not(Eq(Attr(Var("owner"), "role"), Lit("A"))),
                        Eq(Attr(Var("target"), "state"), Lit(0)),
                        Not(Eq(Count(InNeighbours(Var("target"), "causal_influence")), Lit(0)))]))
    add_rule(s._inner, "retract_local", [("owner", "has_concept", "target")], [
        ["set_attr", "target", "state", 0], ["set_attr", "target", "linked", False],
    ], where=And([Not(Eq(Attr(Var("owner"), "role"), Lit("A"))),
                  Eq(Attr(Var("target"), "state"), Lit(1)),
                  Eq(Count(InNeighbours(Var("target"), "causal_influence")), Lit(0))]))
    add_rule(s._inner, "delete_bridge", [("owner", "has_concept", "bridge")], [["del_node", "bridge"]],
             where=And([Eq(Attr(Var("owner"), "role"), Lit("A")),
                        Eq(Attr(Var("bridge"), "delete_request"), Lit(True))]))
    return s, mts, concepts


def projection(s, mts, concepts):
    bridges = [node for node in s.nodes("Concept") if s.node(node)["attrs"].get("delete_request") is not None]
    bridge = bridges[0] if bridges else None
    targets = concepts[1:]
    return {
        "frame_count": len(mts),
        "emitted": s.node(concepts[0])["attrs"].get("emitted"),
        "states": [s.node(c)["attrs"].get("state") for c in targets],
        "linked": [s.node(c)["attrs"].get("linked") for c in targets],
        "bridge_id": int(bridge.value) if bridge else None,
        "bridge_owned": bool(bridge and s.has_edge(mts[0], "has_concept", bridge)),
        "dependency_edges": [bool(bridge and s.has_edge(bridge, "causal_influence", c)) for c in targets],
        "owner_ids": [int(mt.value) for mt in mts],
    }


def settle(s, seeds, omit_owner=None):
    queue = deque(seeds)
    queued = {int(mt.value) for mt in queue}
    reports, owners, enqueues = [], set(), 0
    steps = 0
    while queue and len(reports) < CAP:
        mt = queue.popleft(); queued.remove(int(mt.value))
        report = s._inner.run_rules_scoped_delta_report(mt, CAP - steps, False)
        reports.append(report); steps += int(report["progress_steps"])
        if report["hit_progress_budget"] or report["deferred_effects_pending"]:
            break
        if report["progress_steps"]:
            for raw_owner in report["affected_microtheories"]:
                owner = int(raw_owner); owners.add(owner)
                if owner == omit_owner or owner in queued:
                    continue
                queue.append(NodeID(owner)); queued.add(owner); enqueues += 1
    result = {
        "complete": not queue and len(reports) < CAP and all(not r["hit_progress_budget"] and not r["deferred_effects_pending"] for r in reports),
        "reports": len(reports), "progress_steps": steps, "enqueues": enqueues,
        "notified_owners": sorted(owners), "queue_remaining": sorted(queued),
        "cap_hit": any(r["hit_progress_budget"] for r in reports),
        "deferred_pending": any(r["deferred_effects_pending"] for r in reports),
    }
    return result


def event_arm(n: int, omission=False):
    s, mts, concepts = fixture(n)
    omitted = int(mts[-1].value) if omission else None
    t0 = time.perf_counter_ns()
    birth = settle(s, [mts[0]], omitted)
    born = projection(s, mts, concepts)
    full_for_omission = None
    if not omission and born["bridge_id"] is not None:
        s.set_attr(NodeID(born["bridge_id"]), "delete_request", True)
        deletion = settle(s, [mts[0]])
    else:
        deletion = None
    elapsed = time.perf_counter_ns() - t0
    return {"birth": birth, "born": born, "deletion": deletion,
            "ended": projection(s, mts, concepts) if deletion is not None else None,
            "elapsed_ns": elapsed, "omitted_owner": omitted}


def full_arm(n: int):
    s, mts, concepts = fixture(n)
    t0 = time.perf_counter_ns()
    birth = s._inner.run_rules_report(CAP, False)
    born = projection(s, mts, concepts)
    s.set_attr(NodeID(born["bridge_id"]), "delete_request", True)
    deletion = s._inner.run_rules_report(CAP, False)
    ended = projection(s, mts, concepts)
    return {"birth": birth, "born": born, "deletion": deletion, "ended": ended,
            "elapsed_ns": time.perf_counter_ns() - t0}


def stage_owner_set(stage):
    return stage["notified_owners"]


def main():
    rows = []
    for n in SIZES:
        reps = []
        for rep in range(REPEATS):
            # Alternate order to limit systematic first-arm effects.
            if rep % 2:
                event = event_arm(n); full = full_arm(n)
            else:
                full = full_arm(n); event = event_arm(n)
            omitted = event_arm(n, omission=True)
            expected_ids = event["born"]["owner_ids"]
            reps.append({"repeat": rep, "event": event, "full": full, "omitted": omitted,
                         "gates": {
                             "birth_owner_set_exact": stage_owner_set(event["birth"]) == expected_ids,
                             "deletion_owner_set_exact": stage_owner_set(event["deletion"]) == expected_ids,
                             "event_settles": event["birth"]["complete"] and event["deletion"]["complete"],
                             "birth_matches_full": event["born"] == full["born"],
                             "deletion_matches_full": event["ended"] == full["ended"],
                             "full_fixed_points": full["birth"]["status"] == full["deletion"]["status"] == "fixed_point",
                             "omitted_target_stale": omitted["born"]["states"][-1] == 0 and omitted["born"] != full["born"],
                             "no_cap_or_deferred": not event["birth"]["cap_hit"] and not event["deletion"]["cap_hit"] and not event["birth"]["deferred_pending"] and not event["deletion"]["deferred_pending"],
                         }})
        rows.append({"frame_count": n, "repetitions": reps})
    inputs = {
        "protocol": sha(PREREG), "runner": sha(Path(__file__)),
        "graph_rs": sha(ROOT / "runners/dsl/src/graph.rs"),
        "substrate_rs": sha(ROOT / "runners/dsl/src/substrate.rs"),
        "rewrite_rs": sha(ROOT / "runners/dsl/src/rewrite.rs"),
        "py_rs": sha(ROOT / "runners/dsl/src/py.rs"), "native": sha(NATIVE),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
    }
    payload = {"protocol_id": "SUBSTRATE_SCOPED_NOTIFICATION_FANOUT_SCALE_PREREG_20260926",
               "sizes": list(SIZES), "repeats": REPEATS, "inputs": inputs, "rows": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    gates = [gate for row in rows for rep in row["repetitions"] for gate in rep["gates"].values()]
    print(json.dumps({"output": str(OUT), "instances": len(gates) // 8,
                      "gates_passed": sum(gates), "gates_total": len(gates)}, indent=2))
    if not all(gates):
        raise SystemExit("one or more preregistered scale gates failed")


if __name__ == "__main__":
    main()
