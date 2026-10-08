#!/usr/bin/env python3
"""Probe conflict handling and order sensitivity in native polar claim rules."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runners" / "dsl" / "python"))

from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter

LOCK = ROOT / "evaluation/substrate_capability/accepted_proposition_polar_conflict_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/accepted_proposition_polar_conflict_v1_raw_20261003.json"
REPEATS = 3
CASES = (
    {"id": "unique_affirmed", "claims": [("affirmed", "accepted")], "expected": "yes"},
    {"id": "unique_negated", "claims": [("negated", "accepted")], "expected": "no"},
    {"id": "conflict_affirmed_first", "claims": [("affirmed", "accepted"), ("negated", "accepted")], "expected": None},
    {"id": "conflict_negated_first", "claims": [("negated", "accepted"), ("affirmed", "accepted")], "expected": None},
    {"id": "retracted_conflict", "claims": [("affirmed", "accepted"), ("negated", "retracted")], "expected": "yes"},
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return {item["path"]: sha(ROOT / item["path"])
            for item in lock["locked_inputs"]}


def lock_errors(actual: dict[str, str]) -> list[str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return [f"source hash mismatch: {item['path']}"
            for item in lock["locked_inputs"]
            if actual.get(item["path"]) != item["sha256"]]


def edge(agent, src, label, dst):
    try:
        agent.inner.add_edge_unchecked(src, label, dst, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, label, dst)


def run_one(case: dict, replicate: int) -> dict:
    agent = WorldAdapter(seeds=())
    agent.inner.load_seed_manifest(
        manifest_for("communication_intent_arbitration"), agent.agent)
    message = agent.s.add_node("Message", {
        "text": "Is the gate open?", "comp_relation_focus": "polar",
        "comp_anaphor": 0.0, "comp_know_concept": "gate",
    })
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_force": "information_request", "relation_focus": "polar",
        "relation_support": "missing", "anaphor": 0,
        "question_polarity": "affirmed",
        "parsed_relation_schema": "communication_relation_projection.v1",
        "parsed_relation_status": "selected_parse_unverified",
        "parsed_predicate_lemma": "open", "parsed_subject": "gate",
        "cognitive_disposition": None,
    })
    edge(agent, agent.agent, "holds_interpretation", interpretation)
    edge(agent, interpretation, "interprets", message)
    goal = agent.s.add_node("Goal", {"kind": "answer_topic", "concept": "gate"})
    edge(agent, agent.agent, "has_goal", goal)
    edge(agent, goal, "comprehends", message)

    claim_ids = []
    for index, (polarity, status) in enumerate(case["claims"]):
        proposition = agent.s.add_node("Proposition", {
            "schema": "structured_proposition.v1", "predicate": "open",
            "polarity": polarity, "commitment_status": status,
            "argument_roles": '["subject"]',
        })
        claim_ids.append((proposition, polarity, status))
        evidence = agent.s.add_node("PropositionEvidence", {
            "schema": "neutral_proposition_evidence.v1",
            "kind": "explicit_neutral",
            "evidence_id": f"polar-conflict-{case['id']}-{replicate}-{index}",
        })
        subject = agent.s.add_node("PropositionArgument", {
            "schema": "proposition_argument.v1", "role": "subject",
            "value": "gate",
        })
        edge(agent, proposition, "is_structured_proposition", proposition)
        edge(agent, proposition, "evidenced_by", evidence)
        edge(agent, proposition, "has_argument", subject)

    firings = agent.inner.run_rules()
    plans = list(agent.inner.neighbours(interpretation, "has_polar_answer_plan"))
    plan_values = [agent.s.node(node)["attrs"].get("value") for node in plans]
    support_nodes = list(agent.inner.in_neighbours(
        interpretation, "supports_relation"))
    supported_claims = []
    for support in support_nodes:
        props = list(agent.inner.neighbours(support, "based_on_proposition"))
        evidences = list(agent.inner.neighbours(support, "based_on_evidence"))
        supported_claims.append({
            "polarity": agent.s.node(props[0])["attrs"].get("polarity") if len(props) == 1 else None,
            "status": agent.s.node(props[0])["attrs"].get("commitment_status") if len(props) == 1 else None,
            "evidence_id": agent.s.node(evidences[0])["attrs"].get("evidence_id") if len(evidences) == 1 else None,
        })
    return {
        "case_id": case["id"], "replicate": replicate, "pid": os.getpid(),
        "rule_firings": int(firings), "input_claim_order": [
            {"polarity": polarity, "status": status}
            for _, polarity, status in claim_ids],
        "candidate_plan_count": len(plan_values), "plan_values": plan_values,
        "support_count": len(support_nodes), "supported_claims": supported_claims,
        "expected_plan": case["expected"],
        "behavior_match": (plan_values == ([case["expected"]]
                                            if case["expected"] else [])),
    }


def main() -> int:
    before = source_hashes()
    errors = lock_errors(before)
    rows = [run_one(case, replicate)
            for case in CASES for replicate in range(REPEATS)]
    after = source_hashes()
    if before != after:
        errors.append("locked source changed during run")
    if len(rows) != len(CASES) * REPEATS:
        errors.append("incomplete capture")
    behavior_pass = all(row["behavior_match"] for row in rows)
    conflict_rows = [row for row in rows
                     if row["case_id"].startswith("conflict_")]
    conflict_by_replicate = {}
    for row in conflict_rows:
        conflict_by_replicate.setdefault(row["replicate"], {})[
            row["case_id"]] = row["plan_values"]
    order_invariant = all(
        pair.get("conflict_affirmed_first")
        == pair.get("conflict_negated_first")
        for pair in conflict_by_replicate.values())
    report = {
        "schema": "accepted_proposition_polar_conflict_v1",
        "integrity_passed": not errors,
        "behavior_passed": behavior_pass,
        "integrity_errors": errors,
        "case_count": len(CASES), "repeat_count_per_case": REPEATS,
        "row_count": len(rows), "locked_inputs": before,
        "post_run_inputs": after,
        "conflict_rows": conflict_rows,
        "conflict_order_invariant": order_invariant,
        "conflict_yes_plan_count": sum(row["plan_values"] == ["yes"]
                                        for row in conflict_rows),
        "conflict_no_plan_count": sum(not row["plan_values"]
                                       for row in conflict_rows),
        "conflict_abstention_count": sum(not row["plan_values"]
                                          for row in conflict_rows),
        "rows": rows,
        "interpretation": (
            "A conflict passes only if no polar answer plan is emitted. The panel tests "
            "the current native rule path on a fixed parse and explicit structured claims; "
            "it does not evaluate language extraction or user-facing answer rendering."),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"integrity_passed": report["integrity_passed"],
                      "behavior_passed": behavior_pass,
                      "integrity_errors": errors, "rows": len(rows),
                      "conflict_order_invariant": report["conflict_order_invariant"],
                      "conflict_yes_plans": report["conflict_yes_plan_count"],
                      "conflict_abstentions": report["conflict_abstention_count"],
                      "output": str(OUT)}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
