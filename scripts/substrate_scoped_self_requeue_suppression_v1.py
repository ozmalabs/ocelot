#!/usr/bin/env python3
"""Measure guarded suppression of saturated scoped-owner self-requeues."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import statistics
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "evaluation/reports/substrate_scoped_notification_requeue_attribution_v1_20260926.json"
ANALYSIS = BASELINE.with_name(BASELINE.stem + "_analysis.json")
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SCOPED_SELF_REQUEUE_SUPPRESSION_PREREG_20260926.md"
OUT = ROOT / "evaluation/reports/substrate_scoped_self_requeue_suppression_v1_20260926.json"
RUNNER_PATH = ROOT / "scripts/substrate_scoped_notification_requeue_attribution_v1.py"
spec = importlib.util.spec_from_file_location("requeue_baseline", RUNNER_PATH)
base = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(base)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def owner_members(s, owner):
    if not s._inner.has_node(owner):
        return None
    try:
        if s.node(owner).get("type") != "Microtheory":
            return None
    except (KeyError, ValueError):
        return None
    return {int(owner.value), *(int(node.value) for node in
                                s.neighbours(owner, "has_concept"))}


def scoped_settle_suppressed(s, seeds, owner_labels, omit_owner=None):
    from collections import deque
    from substrate_rs import NodeID

    queue = deque(seeds)
    queued = {int(mt.value) for mt in queue}
    turns = steps = enqueues = 0
    notification_entries = duplicate_suppressions = self_requeues = omitted_notifications = 0
    suppressed_self_enqueues = 0
    max_queue_depth = len(queue)
    turns_by_owner = {}
    owner_work = {}
    turn_records = []
    affected = set()
    cap_hit = deferred = False
    start = time.perf_counter_ns()
    while queue and turns < base.CAP and steps < base.CAP:
        mt = queue.popleft(); owner_id = int(mt.value); queued.remove(owner_id); turns += 1
        owner_frame = int(owner_labels[owner_id])
        turns_by_owner[str(owner_id)] = turns_by_owner.get(str(owner_id), 0) + 1
        members_before = owner_members(s, mt)
        before = base.counters(s._inner)
        queue_before = len(queue)
        report = s._inner.run_rules_scoped_delta_report(mt, base.CAP - steps, False)
        turn_steps = int(report["progress_steps"])
        steps += turn_steps
        cap_hit |= bool(report["hit_progress_budget"]); deferred |= bool(report["deferred_effects_pending"])
        if cap_hit or deferred:
            break
        notifications = [int(raw) for raw in report["affected_microtheories"]] if turn_steps else []
        notification_entries += len(notifications)
        unique_notifications = sorted(set(notifications))
        self_count = duplicate_count = omit_count = enqueue_count = suppressed_count = 0
        members_after = owner_members(s, mt)
        ownership_stable = members_before is not None and members_before == members_after
        for owner in notifications:
            affected.add(owner)
            if owner == omit_owner:
                omitted_notifications += 1; omit_count += 1
                continue
            if owner == owner_id and ownership_stable:
                suppressed_self_enqueues += 1; suppressed_count += 1
                continue
            if owner in queued:
                duplicate_suppressions += 1; duplicate_count += 1
                continue
            queue.append(NodeID(owner)); queued.add(owner); enqueues += 1; enqueue_count += 1
            if owner == owner_id:
                self_requeues += 1; self_count += 1
        max_queue_depth = max(max_queue_depth, len(queue))
        after = base.counters(s._inner)
        delta = {key: after[key] - before[key] for key in before}
        slot = owner_work.setdefault(str(owner_frame), {"turns": 0, "progress_steps": 0, "no_progress_turns": 0,
            "candidate_tests": 0, "term_evaluations": 0, "local_rule_matches": 0,
            "mt_seeded_rule_matches": 0, "fallback_rule_matches": 0})
        slot["turns"] += 1; slot["progress_steps"] += turn_steps
        slot["no_progress_turns"] += int(turn_steps == 0)
        slot["candidate_tests"] += delta["cand_enum"]
        slot["term_evaluations"] += delta["term_evals_total"]
        slot["local_rule_matches"] += delta["scoped_local_rule_matches"]
        slot["mt_seeded_rule_matches"] += delta["scoped_mt_seeded_rule_matches"]
        slot["fallback_rule_matches"] += delta["scoped_full_fallback_rule_matches"]
        turn_records.append({"turn": turns, "owner_node": owner_id, "owner_frame_index": owner_frame,
            "progress_steps": turn_steps, "queue_depth_before_turn": queue_before,
            "queue_depth_after_turn": len(queue), "notification_entries": len(notifications),
            "notified_owners": notifications, "unique_notified_owners": unique_notifications,
            "self_requeues": self_count, "duplicate_suppressions": duplicate_count,
            "suppressed_self_enqueues": suppressed_count,
            "ownership_stable_before_after": ownership_stable,
            "omitted_notifications": omit_count, "successful_enqueues": enqueue_count,
            "counter_delta": delta})
    elapsed = time.perf_counter_ns() - start
    return {"complete": not queue and turns < base.CAP and not cap_hit and not deferred,
        "turns": turns, "progress_steps": steps, "enqueues": enqueues,
        "notification_entries": notification_entries, "duplicate_suppressions": duplicate_suppressions,
        "self_requeues": self_requeues, "suppressed_self_enqueues": suppressed_self_enqueues,
        "omitted_notifications": omitted_notifications, "max_queue_depth": max_queue_depth,
        "turns_by_owner": turns_by_owner, "owner_work": owner_work, "turn_records": turn_records,
        "affected_owners": sorted(affected), "queue_remaining": sorted(queued),
        "cap_hit": cap_hit, "deferred_pending": deferred, "wall_ns": elapsed}


def event_arm(name, n):
    s, mts, concepts, edges = base.fixture(name, n)
    s._inner.scale_audit_set_enabled(True)
    phases = []
    for state in (1, 0):
        s._inner.scale_audit_reset()
        s.set_attr(concepts[0], "state", state)
        closure = scoped_settle_suppressed(
            s, [mts[0]], {int(mt.value): i for i, mt in enumerate(mts)})
        closure["audit"] = base.counters(s._inner)
        closure["projection"] = base.projection(s, concepts)
        phases.append(closure)
    s._inner.scale_audit_set_enabled(False)
    return {"phases": phases, "edges": edges,
            "frame_ids": [int(mt.value) for mt in mts]}


def membership_change_control():
    from substrate_rs import Substrate
    from substrate_rs.ext import add_rule

    s = Substrate()
    owner = s.add_node("Microtheory", {})
    seed = s.add_node("Concept", {"trigger": True})
    newcomer = s.add_node("Concept", {"ready": True})
    s.add_edge_unchecked(owner, "has_concept", seed)
    s.add_edge_unchecked(owner, "candidate_member", newcomer)
    add_rule(s._inner, "add_member", [("mt", "has_concept", "seed"),
                                      ("mt", "candidate_member", "newcomer")],
             [["add_edge", "mt", "has_concept", "newcomer"]])
    add_rule(s._inner, "process_member", [("mt", "has_concept", "newcomer")],
             [["set_attr", "newcomer", "processed", True]])
    s._inner.scale_audit_set_enabled(True)
    event = scoped_settle_suppressed(s, [owner], {int(owner.value): 0})
    event_projection = s.node(newcomer)["attrs"].get("processed")
    full = Substrate()
    full_owner = full.add_node("Microtheory", {})
    full_seed = full.add_node("Concept", {"trigger": True})
    full_newcomer = full.add_node("Concept", {"ready": True})
    full.add_edge_unchecked(full_owner, "has_concept", full_seed)
    full.add_edge_unchecked(full_owner, "candidate_member", full_newcomer)
    add_rule(full._inner, "add_member", [("mt", "has_concept", "seed"),
                                         ("mt", "candidate_member", "newcomer")],
             [["add_edge", "mt", "has_concept", "newcomer"]])
    add_rule(full._inner, "process_member", [("mt", "has_concept", "newcomer")],
             [["set_attr", "newcomer", "processed", True]])
    full._inner.scale_audit_set_enabled(True)
    full._inner.run_rules(base.CAP)
    return {"event_complete": event["complete"], "event_processed": event_projection,
            "event_self_requeues": event["self_requeues"],
            "event_suppressed_self_enqueues": event["suppressed_self_enqueues"],
            "event_membership_changed_turns": sum(not t["ownership_stable_before_after"]
                for t in event["turn_records"] if t["notification_entries"]),
            "full_processed": full.node(full_newcomer)["attrs"].get("processed"),
            "parity": event_projection == full.node(full_newcomer)["attrs"].get("processed") is True}


def delayed_writer_control():
    from substrate_rs import And, Attr, Eq, Lit, Substrate, Var
    from substrate_rs.ext import add_rule

    def make():
        s = Substrate()
        owner_a = s.add_node("Microtheory", {})
        owner_b = s.add_node("Microtheory", {})
        a = s.add_node("Concept", {"trigger": True, "late": False})
        driver = s.add_node("Concept", {"kick": False})
        output = s.add_node("Concept", {"signal": False})
        s.add_edge_unchecked(owner_a, "has_concept", a)
        s.add_edge_unchecked(owner_b, "has_concept", driver)
        s.add_edge_unchecked(owner_b, "has_concept", output)
        s.add_edge_unchecked(a, "kick_link", driver)
        s.add_edge_unchecked(driver, "internal_link", output)
        s.add_edge_unchecked(output, "late_link", a)
        add_rule(s._inner, "kick_B", [("src", "kick_link", "dst")],
            [["set_attr", "dst", "kick", True]], where=And([
                Eq(Attr(Var("src"), "trigger"), Lit(True)),
                Eq(Attr(Var("dst"), "kick"), Lit(False))]))
        add_rule(s._inner, "B_derive", [("src", "internal_link", "dst")],
            [["set_attr", "dst", "signal", True]], where=And([
                Eq(Attr(Var("src"), "kick"), Lit(True)),
                Eq(Attr(Var("dst"), "signal"), Lit(False))]))
        add_rule(s._inner, "B_to_A", [("src", "late_link", "dst")],
            [["set_attr", "dst", "late", True]], where=And([
                Eq(Attr(Var("src"), "signal"), Lit(True)),
                Eq(Attr(Var("dst"), "late"), Lit(False))]))
        return s, owner_a, owner_b, [a, driver, output]

    def projection(s, concepts):
        return [s.node(node)["attrs"] for node in concepts]

    s_base, a_base, b_base, c_base = make()
    base_turns = base.scoped_settle(s_base, [a_base],
        {int(a_base.value): 0, int(b_base.value): 1})
    base_projection = projection(s_base, c_base)
    s_event, a_event, b_event, c_event = make()
    event_turns = scoped_settle_suppressed(s_event, [a_event],
        {int(a_event.value): 0, int(b_event.value): 1})
    event_projection = projection(s_event, c_event)
    s_full, _, _, c_full = make()
    full_report = s_full._inner.run_rules_report(base.CAP, False)
    full_projection = projection(s_full, c_full)
    sequence = [record["owner_frame_index"] for record in event_turns["turn_records"]]
    # The B turn must notify A after A has already left the queue.
    b_turn_notifies_a = any(record["owner_frame_index"] == 1 and
        any(int(owner) == int(a_event.value) for owner in record["notified_owners"])
        for record in event_turns["turn_records"])
    return {"suppressed_sequence": sequence, "baseline_sequence": [r["owner_frame_index"] for r in base_turns["turn_records"]],
        "event_complete": event_turns["complete"], "full_status": full_report["status"],
        "b_turn_notifies_a": b_turn_notifies_a, "event_projection": event_projection,
        "baseline_projection": base_projection, "full_projection": full_projection,
        "parity": event_projection == base_projection == full_projection,
        "gate": sequence == [0, 1, 0] and b_turn_notifies_a and event_turns["complete"] and
            full_report["status"] == "fixed_point" and event_projection == base_projection == full_projection}


def main():
    baseline = json.loads(BASELINE.read_text())
    assert json.loads(ANALYSIS.read_text())["all_gates_pass"]
    rows = []
    base_rows = {(row["topology"], row["frame_count"]): row
                 for row in baseline["rows"]}
    for topology in base.TOPOLOGIES:
        for n in base.SIZES:
            original = base_rows[(topology, n)]
            reps = []
            for rep, reference in enumerate(original["repetitions"]):
                start = time.perf_counter_ns()
                intervention = event_arm(topology, n)
                elapsed = time.perf_counter_ns() - start
                event_base = reference["event"]
                gates = {
                    "baseline_source_cell_valid": bool(reference["gates"]) and all(reference["gates"].values()),
                    "intervention_settles": all(phase["complete"] for phase in intervention["phases"]),
                    "full_projection_parity": all(intervention["phases"][i]["projection"] == reference["full"]["phases"][i]["projection"] for i in range(2)),
                    "owner_notifications_preserved": all(
                        [owner for owner in intervention["phases"][i]["affected_owners"]] ==
                        [owner for owner in event_base["phases"][i]["affected_owners"]] for i in range(2)),
                    "only_stable_self_enqueue_suppressed": all(
                        turn["suppressed_self_enqueues"] == int(
                            turn["owner_node"] in turn["notified_owners"] and
                            turn["ownership_stable_before_after"])
                        for phase in intervention["phases"] for turn in phase["turn_records"]),
                    "no_cap_or_deferred_effects": all(not p["cap_hit"] and not p["deferred_pending"] for p in intervention["phases"]),
                    "nonself_notification_multiset_preserved": all(
                        [x for t in intervention["phases"][i]["turn_records"] for x in t["notified_owners"] if x != t["owner_node"]] ==
                        [x for t in event_base["phases"][i]["turn_records"] for x in t["notified_owners"] if x != t["owner_node"]]
                        for i in range(2)),
                }
                reps.append({"repeat": rep, "intervention": intervention,
                    "baseline": event_base, "full": reference["full"], "elapsed_ns": elapsed,
                    "gates": gates})
            rows.append({"topology": topology, "frame_count": n, "repetitions": reps})
    controls = {"ownership_change": membership_change_control(),
                "delayed_writer": delayed_writer_control()}
    controls["ownership_change"]["gate"] = all(controls["ownership_change"][k] for k in
        ("event_complete", "parity")) and controls["ownership_change"]["event_self_requeues"] > 0 and controls["ownership_change"]["event_suppressed_self_enqueues"] == 0
    controls["delayed_writer"]["gate"] = controls["delayed_writer"]["gate"]
    payload = {"protocol_id": "SUBSTRATE_SCOPED_SELF_REQUEUE_SUPPRESSION_V1_20260926",
        "inputs": {"protocol": sha(PREREG), "runner": sha(Path(__file__)),
            "baseline_raw": sha(BASELINE), "baseline_analysis": sha(ANALYSIS),
            "runner_source": sha(RUNNER_PATH), "native": sha(base.NATIVE),
            "rust_source_fingerprint": base.rust_source_fingerprint(str(ROOT))},
        "topologies": list(base.TOPOLOGIES), "sizes": list(base.SIZES), "repeats": base.REPEATS,
        "controls": controls, "rows": rows}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    failed = [(row["topology"], row["frame_count"], rep["repeat"], gate)
        for row in rows for rep in row["repetitions"] for gate, ok in rep["gates"].items() if not ok]
    print(json.dumps({"output": str(OUT), "cells": len(rows), "repetitions": sum(len(x["repetitions"]) for x in rows),
        "all_gates_pass": not failed and all(control["gate"] for control in controls.values()), "failed": failed,
        "controls": controls}, indent=2))
    if failed or not all(control["gate"] for control in controls.values()): raise SystemExit("intervention gate failed")


if __name__ == "__main__":
    main()
