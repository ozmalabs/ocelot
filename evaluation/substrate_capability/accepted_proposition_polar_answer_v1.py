#!/usr/bin/env python3
"""Measure the existing graph-native accepted-proposition polar answer rule."""
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

LOCK = ROOT / "evaluation/substrate_capability/accepted_proposition_polar_answer_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/accepted_proposition_polar_answer_v1_raw_20261003.json"
REPEATS = 3
CASES = (
    {"id": "accepted_affirmative", "status": "accepted", "polarity": "affirmed", "question_polarity": "affirmed", "predicate": "open", "subject": "gate", "evidence": True, "expected": "yes"},
    {"id": "accepted_negated_claim", "status": "accepted", "polarity": "negated", "question_polarity": "affirmed", "predicate": "open", "subject": "gate", "evidence": True, "expected": "no"},
    {"id": "accepted_negated_question", "status": "accepted", "polarity": "affirmed", "question_polarity": "negated", "predicate": "open", "subject": "gate", "evidence": True, "expected": "no"},
    {"id": "proposed", "status": "proposed", "polarity": "affirmed", "question_polarity": "affirmed", "predicate": "open", "subject": "gate", "evidence": True, "expected": None},
    {"id": "suspended", "status": "suspended", "polarity": "affirmed", "question_polarity": "affirmed", "predicate": "open", "subject": "gate", "evidence": True, "expected": None},
    {"id": "predicate_mismatch", "status": "accepted", "polarity": "affirmed", "question_polarity": "affirmed", "predicate": "closed", "subject": "gate", "evidence": True, "expected": None},
    {"id": "missing_evidence", "status": "accepted", "polarity": "affirmed", "question_polarity": "affirmed", "predicate": "open", "subject": "gate", "evidence": False, "expected": None},
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
    loaded = agent.inner.load_seed_manifest(
        manifest_for("communication_intent_arbitration"), agent.agent)
    message = agent.s.add_node("Message", {
        "text": "Is the gate open?",
        "comp_relation_focus": "polar",
        "comp_anaphor": 0.0,
        "comp_know_concept": "gate",
    })
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_force": "information_request",
        "relation_focus": "polar",
        "relation_support": "missing",
        "anaphor": 0,
        "question_polarity": case["question_polarity"],
        "parsed_relation_schema": "communication_relation_projection.v1",
        "parsed_relation_status": "selected_parse_unverified",
        "parsed_predicate_lemma": "open",
        "parsed_subject": "gate",
        "cognitive_disposition": None,
    })
    edge(agent, agent.agent, "holds_interpretation", interpretation)
    edge(agent, interpretation, "interprets", message)
    goal = agent.s.add_node("Goal", {"kind": "answer_topic", "concept": "gate"})
    edge(agent, agent.agent, "has_goal", goal)
    edge(agent, goal, "comprehends", message)

    proposition = agent.s.add_node("Proposition", {
        "schema": "structured_proposition.v1",
        "predicate": case["predicate"],
        "polarity": case["polarity"],
        "commitment_status": case["status"],
        "argument_roles": '["subject"]',
    })
    edge(agent, proposition, "is_structured_proposition", proposition)
    subject = agent.s.add_node("PropositionArgument", {
        "schema": "proposition_argument.v1", "role": "subject",
        "value": case["subject"],
    })
    edge(agent, proposition, "has_argument", subject)
    evidence = None
    if case["evidence"]:
        evidence = agent.s.add_node("PropositionEvidence", {
            "schema": "neutral_proposition_evidence.v1",
            "kind": "explicit_neutral",
            "evidence_id": f"polar-answer-{case['id']}-{replicate}",
        })
        edge(agent, proposition, "evidenced_by", evidence)

    firings = agent.inner.run_rules()
    iattrs = agent.s.node(interpretation)["attrs"]
    plans = list(agent.inner.neighbours(interpretation, "has_polar_answer_plan"))
    plan_attrs = [dict(agent.s.node(node)["attrs"]) for node in plans]
    support_nodes = list(agent.inner.in_neighbours(
        interpretation, "supports_relation"))
    support_attrs = [dict(agent.s.node(node)["attrs"]) for node in support_nodes]
    based_props = [p for node in support_nodes
                   for p in agent.inner.neighbours(node, "based_on_proposition")]
    based_evidence = [e for node in support_nodes
                      for e in agent.inner.neighbours(node, "based_on_evidence")]
    observed = plan_attrs[0].get("value") if len(plan_attrs) == 1 else None
    return {
        "case_id": case["id"], "replicate": replicate, "pid": os.getpid(),
        "rule_count": int(loaded.get("rules", 0)), "rule_firings": int(firings),
        "input_commitment_status": case["status"],
        "input_uptake_applied": None,
        "proposition_evidence_present": evidence is not None,
        "relation_support": iattrs.get("relation_support"),
        "disposition": iattrs.get("cognitive_disposition"),
        "arbitration_basis": iattrs.get("arbitration_basis"),
        "candidate_plan_count": len(plan_attrs), "plan_values": [x.get("value") for x in plan_attrs],
        "support_count": len(support_attrs),
        "support_proposition_link_count": len(based_props),
        "support_evidence_link_count": len(based_evidence),
        "expected_plan": case["expected"],
        "plan_exact": (observed == case["expected"]
                       and len(plan_attrs) == (1 if case["expected"] else 0)),
    }


def main() -> int:
    before = source_hashes()
    errors = lock_errors(before)
    rows = [run_one(case, rep) for case in CASES for rep in range(REPEATS)]
    after = source_hashes()
    if before != after:
        errors.append("locked source changed during run")
    for row in rows:
        if not row["plan_exact"]:
            errors.append(f"polar-answer gate failed: {row['case_id']}/{row['replicate']}")
        if row["expected_plan"] is not None and not (
                row["support_count"] == row["support_proposition_link_count"] ==
                row["support_evidence_link_count"] == 1):
            errors.append(f"support lineage failed: {row['case_id']}/{row['replicate']}")
    report = {
        "schema": "accepted_proposition_polar_answer_v1",
        "passed_integrity_and_behavior": not errors,
        "errors": errors,
        "case_count": len(CASES), "repeat_count_per_case": REPEATS,
        "row_count": len(rows), "locked_inputs": before,
        "post_run_inputs": after,
        "expected_plan_rows": sum(row["expected_plan"] is not None for row in rows),
        "exact_plan_rows": sum(row["plan_exact"] for row in rows),
        "positive_support_lineage_rows": sum(
            row["support_count"] == row["support_proposition_link_count"] ==
            row["support_evidence_link_count"] == 1 for row in rows
            if row["expected_plan"] is not None),
        "accepted_rows_without_uptake_applied": sum(
            row["input_commitment_status"] == "accepted"
            and row["input_uptake_applied"] is None for row in rows),
        "rows": rows,
        "interpretation": (
            "Measures only the existing native rule path from explicit proposition/query "
            "graph facts to PolarAnswerPlan. The harness supplies commitment status and "
            "does not assert that native uptake caused it. No language parsing, memory "
            "request, response rendering, or general wh-recall is measured."),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"passed": report["passed_integrity_and_behavior"],
                      "errors": errors, "rows": len(rows),
                      "exact_plan_rows": report["exact_plan_rows"],
                      "expected_plan_rows": report["expected_plan_rows"],
                      "output": str(OUT)}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
