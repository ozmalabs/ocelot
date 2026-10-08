#!/usr/bin/env python3
"""Evaluate a candidate polar-conflict guard in isolated CoW graph branches."""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]

from domains.engine_provenance import build_is_stale, rust_source_fingerprint
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter
from substrate_rs import _native
from substrate_rs.ext import run_rules as native_run_rules

LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_polar_conflict_guard_v1_lock_20261003.json"
OUT = ROOT / "evaluation/reports/thoughtexperiment_polar_conflict_guard_v1_raw_20261003.json"
REPEATS = 3
CASES = (
    {"id": "unique_affirmed", "claims": [("affirmed", "accepted", "gate")], "expected": ["yes"], "baseline_expected": ["yes"], "conflict": False},
    {"id": "unique_negated", "claims": [("negated", "accepted", "gate")], "expected": ["no"], "baseline_expected": ["no"], "conflict": False},
    {"id": "conflict_affirmed_first", "claims": [("affirmed", "accepted", "gate"), ("negated", "accepted", "gate")], "expected": [], "baseline_expected": ["yes"], "conflict": True},
    {"id": "conflict_negated_first", "claims": [("negated", "accepted", "gate"), ("affirmed", "accepted", "gate")], "expected": [], "baseline_expected": ["yes"], "conflict": True},
    {"id": "retracted_conflict", "claims": [("affirmed", "accepted", "gate"), ("negated", "retracted", "gate")], "expected": ["yes"], "baseline_expected": ["yes"], "conflict": False},
    {"id": "proposed_conflict", "claims": [("affirmed", "accepted", "gate"), ("negated", "proposed", "gate")], "expected": ["yes"], "baseline_expected": ["yes"], "conflict": False},
    {"id": "different_subject", "claims": [("affirmed", "accepted", "gate"), ("negated", "accepted", "door")], "expected": ["yes"], "baseline_expected": ["yes"], "conflict": False},
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return {row["path"]: sha(ROOT / row["path"])
            for row in lock["locked_inputs"]}


def lock_errors(actual: dict[str, str]) -> list[str]:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    return [f"source hash mismatch: {row['path']}"
            for row in lock["locked_inputs"]
            if actual.get(row["path"]) != row["sha256"]]


def digest(value) -> str:
    return hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str
    ).encode()).hexdigest()


def edge(agent, src, label, dst):
    try:
        agent.inner.add_edge_unchecked(src, label, dst, {})
    except TypeError:
        agent.inner.add_edge_unchecked(src, label, dst)


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(name, key): return {"type": "Attr", "node": V(name), "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def attr_term(name, key): return {"__term__": A(name, key)}


def conflict_guard_rule() -> dict:
    """Hand-authored candidate rule; installed only in the experiment branch."""
    return {
        "name": "experiment_abstain_on_opposite_accepted_unary_claims",
        "order": -100,
        "area": "experiment_polar_conflict_guard",
        "comment": "When two evidenced accepted propositions disagree on polarity for the exact same selected unary relation, mark conflict before answer-plan rules run.",
        "match": [
            ["agent", "holds_interpretation", "i"],
            ["i", "interprets", "m"],
            ["agent", "has_goal", "g"],
            ["g", "comprehends", "m"],
            ["p1", "is_structured_proposition", "p1"],
            ["p1", "evidenced_by", "e1"],
            ["p1", "has_argument", "a1"],
            ["p2", "is_structured_proposition", "p2"],
            ["p2", "evidenced_by", "e2"],
            ["p2", "has_argument", "a2"],
        ],
        "where": And(
            Eq(A("i", "schema"), L("communication_interpretation.v1")),
            Eq(A("i", "evidence_schema"), L("communication_evidence.v1")),
            Eq(A("i", "evidence_force"), L("information_request")),
            Eq(A("i", "relation_focus"), L("polar")),
            Eq(A("i", "relation_support"), L("missing")),
            Eq(A("i", "anaphor"), L(0)),
            Eq(A("i", "parsed_relation_schema"), L("communication_relation_projection.v1")),
            Eq(A("i", "parsed_relation_status"), L("selected_parse_unverified")),
            Eq(A("p1", "schema"), L("structured_proposition.v1")),
            Eq(A("p2", "schema"), L("structured_proposition.v1")),
            Eq(A("p1", "argument_roles"), L('["subject"]')),
            Eq(A("p2", "argument_roles"), L('["subject"]')),
            Eq(A("p1", "commitment_status"), L("accepted")),
            Eq(A("p2", "commitment_status"), L("accepted")),
            Eq(A("p1", "polarity"), L("affirmed")),
            Eq(A("p2", "polarity"), L("negated")),
            Eq(A("p1", "predicate"), A("i", "parsed_predicate_lemma")),
            Eq(A("p2", "predicate"), A("i", "parsed_predicate_lemma")),
            Eq(A("a1", "schema"), L("proposition_argument.v1")),
            Eq(A("a2", "schema"), L("proposition_argument.v1")),
            Eq(A("a1", "role"), L("subject")),
            Eq(A("a2", "role"), L("subject")),
            Eq(A("a1", "value"), A("i", "parsed_subject")),
            Eq(A("a2", "value"), A("i", "parsed_subject")),
            Eq(A("a1", "value"), A("g", "concept")),
            Eq(A("a2", "value"), A("g", "concept")),
            Eq(A("e1", "schema"), L("neutral_proposition_evidence.v1")),
            Eq(A("e2", "schema"), L("neutral_proposition_evidence.v1")),
            Eq(A("e1", "kind"), L("explicit_neutral")),
            Eq(A("e2", "kind"), L("explicit_neutral")),
            Not(Eq(A("i", "experiment_polar_conflict_detected"), L(1))),
        ),
        "effects": [
            ["set_attr", "i", "experiment_polar_conflict_detected", 1],
            ["set_attr", "i", "relation_support", "conflict"],
            ["set_attr", "i", "cognitive_disposition", "repair"],
            ["set_attr", "i", "cognitive_goal", "clarify_or_defer"],
            ["set_attr", "i", "arbitration_basis", "contradictory_accepted_propositions"],
            ["add_node", "outcome", "PolarConflictOutcome", {
                "schema": "polar_conflict_outcome.v1",
                "status": "conflict",
                "predicate": attr_term("p1", "predicate"),
                "affirmed_evidence_id": attr_term("e1", "evidence_id"),
                "negated_evidence_id": attr_term("e2", "evidence_id"),
                "observation_status": "not_observed",
            }],
            ["add_edge", "outcome", "for_interpretation", "i"],
            ["add_edge", "outcome", "conflicting_proposition", "p1"],
            ["add_edge", "outcome", "conflicting_proposition", "p2"],
            ["add_edge", "outcome", "based_on_evidence", "e1"],
            ["add_edge", "outcome", "based_on_evidence", "e2"],
        ],
    }


def make_primary(case: dict, replicate: int):
    agent = WorldAdapter(seeds=())
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
    claims = []
    for index, (polarity, status, subject_value) in enumerate(case["claims"]):
        proposition = agent.s.add_node("Proposition", {
            "schema": "structured_proposition.v1", "predicate": "open",
            "polarity": polarity, "commitment_status": status,
            "argument_roles": '["subject"]',
        })
        evidence = agent.s.add_node("PropositionEvidence", {
            "schema": "neutral_proposition_evidence.v1",
            "kind": "explicit_neutral",
            "evidence_id": f"cow-polar-{case['id']}-{replicate}-{index}",
        })
        argument = agent.s.add_node("PropositionArgument", {
            "schema": "proposition_argument.v1", "role": "subject",
            "value": subject_value,
        })
        edge(agent, proposition, "is_structured_proposition", proposition)
        edge(agent, proposition, "evidenced_by", evidence)
        edge(agent, proposition, "has_argument", argument)
        claims.append((proposition, evidence, polarity, status, subject_value))
    return agent, interpretation, claims


def output_state(branch, interpretation):
    plans = list(branch.neighbours(interpretation, "has_polar_answer_plan"))
    plan_values = [branch.node(node)["attrs"].get("value") for node in plans]
    outcomes = list(branch.nodes("PolarConflictOutcome"))
    support = list(branch.in_neighbours(interpretation, "supports_relation"))
    return {
        "plan_values": plan_values,
        "conflict_outcome_count": len(outcomes),
        "conflict_outcomes": [dict(branch.node(node)["attrs"]) for node in outcomes],
        "support_count": len(support),
        "interpretation": dict(branch.node(interpretation)["attrs"]),
    }


def run_one(case: dict, replicate: int) -> dict:
    agent, interpretation, claims = make_primary(case, replicate)
    primary = agent.s
    original_manifest = manifest_for("communication_intent_arbitration")
    primary_before = primary.graph_to_dict()
    primary_digest = digest(primary_before)
    primary_rules_before = agent.inner.export_rules()
    primary_revision = list(primary.experiment_graph_rule_revision())
    snapshot = primary.snapshot()

    baseline = snapshot.fork()
    baseline.load_seed_manifest(copy.deepcopy(original_manifest), agent.agent)
    baseline_firings = native_run_rules(baseline)
    baseline_state = output_state(baseline, interpretation)

    candidate = snapshot.fork()
    candidate_manifest = copy.deepcopy(original_manifest)
    candidate_manifest["id"] = "communication_intent_arbitration_polar_conflict_experiment"
    candidate_manifest["rules"].insert(0, conflict_guard_rule())
    candidate.load_seed_manifest(candidate_manifest, agent.agent)
    candidate.begin_experiment_delta_journal()
    candidate_firings = native_run_rules(candidate)
    candidate_state = output_state(candidate, interpretation)
    residual = candidate.finish_experiment_delta_journal()
    derived = residual.get("derived_only", {})

    primary_unchanged_before_return = (
        digest(primary.graph_to_dict()) == primary_digest
        and digest(agent.inner.export_rules()) == digest(primary_rules_before)
    )
    returned = False
    return_error = None
    if case["conflict"] and candidate_state["conflict_outcome_count"] == 1:
        try:
            primary.apply_experiment_graph_delta(tuple(primary_revision), derived)
            returned = True
        except Exception as exc:  # capture the revision/adoption boundary
            return_error = f"{type(exc).__name__}: {exc}"
    primary_after = primary.graph_to_dict()
    after_nodes = {row["id"]: row for row in primary_after.get("nodes", [])}
    candidate_graph = candidate.graph_to_dict()
    candidate_nodes = {row["id"]: row for row in candidate_graph.get("nodes", [])}
    added_nodes = derived.get("nodes_added", [])
    added_node_parity = all(after_nodes.get(row["id"]) == candidate_nodes.get(row["id"])
                            for row in added_nodes) if returned else True
    returned_conflict_count = len(list(primary.nodes("PolarConflictOutcome")))
    return {
        "case_id": case["id"], "replicate": replicate, "pid": os.getpid(),
        "input_claims": [{"polarity": p, "status": s, "subject": v}
                         for _, _, p, s, v in claims],
        "primary_graph_digest_before": primary_digest,
        "primary_graph_digest_after": digest(primary_after),
        "primary_rules_before_count": len(primary_rules_before),
        "primary_rules_after_count": len(agent.inner.export_rules()),
        "primary_unchanged_before_return": primary_unchanged_before_return,
        "baseline_rule_firings": int(baseline_firings),
        "candidate_rule_firings": int(candidate_firings),
        "baseline": baseline_state,
        "candidate": candidate_state,
        "residual_digest": digest(derived),
        "residual_nodes_added": len(added_nodes),
        "residual_edges_added": len(derived.get("edges_added", [])),
        "residual_nonempty": bool(added_nodes or derived.get("edges_added")
                                  or derived.get("nodes_changed")),
        "residual_returned": returned,
        "residual_return_error": return_error,
        "returned_conflict_count": returned_conflict_count,
        "returned_node_parity": added_node_parity,
        "candidate_answer_matches_oracle": (
            candidate_state["plan_values"] == case["expected"]
            and candidate_state["conflict_outcome_count"] == int(case["conflict"])),
        "baseline_answer_matches_oracle": baseline_state["plan_values"] == case["baseline_expected"],
    }


def main() -> int:
    stale = build_is_stale(str(ROOT))
    before = source_hashes()
    errors = lock_errors(before)
    if stale:
        errors.append("native engine stale: " + "; ".join(stale))
    rows = [run_one(case, rep) for case in CASES for rep in range(REPEATS)]
    after = source_hashes()
    if before != after:
        errors.append("locked sources changed during run")
    if not all(row["primary_unchanged_before_return"] for row in rows):
        errors.append("primary changed before explicit residual return")
    if any(row["primary_rules_after_count"] != row["primary_rules_before_count"] for row in rows):
        errors.append("experiment branch rule changes leaked into primary")
    if any(not row["candidate_answer_matches_oracle"]
           or not row["baseline_answer_matches_oracle"] for row in rows):
        errors.append("candidate or baseline behavior did not match preregistered oracle")
    if any(row["residual_returned"] != bool(row["candidate"]["conflict_outcome_count"])
           for row in rows):
        errors.append("conflict residual return gate failed")
    if any(row["residual_returned"] and not row["returned_node_parity"] for row in rows):
        errors.append("returned graph delta did not match candidate branch")
    report = {
        "schema": "thoughtexperiment_polar_conflict_guard_v1",
        "integrity_passed": not errors,
        "behavior_passed": not any(not row["candidate_answer_matches_oracle"]
                                    for row in rows),
        "errors": errors,
        "case_count": len(CASES), "repeat_count_per_case": REPEATS,
        "row_count": len(rows), "locked_inputs": before,
        "post_run_inputs": after,
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "native_binary_sha256": sha(Path(_native.__file__).resolve()),
        "conflict_candidates_returned": sum(row["residual_returned"] for row in rows),
        "conflict_candidates_expected": sum(case["conflict"] for case in CASES) * REPEATS,
        "rows": rows,
        "interpretation": (
            "A hand-authored conflict guard is added only to a CoW experiment branch, "
            "before the existing polar rules. Candidate and baseline branches fork the "
            "same proposition/query graph. The candidate creates a conflict outcome and "
            "returns its graph delta to primary only for conflict conditions. This probes "
            "a repair candidate; it does not establish learned rule invention, trusted "
            "uptake/source lineage, or production safety."),
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n",
                   encoding="utf-8")
    print(json.dumps({"integrity_passed": report["integrity_passed"],
                      "behavior_passed": report["behavior_passed"],
                      "errors": errors, "rows": len(rows),
                      "conflict_residuals_returned": report[
                          "conflict_candidates_returned"],
                      "expected": report["conflict_candidates_expected"],
                      "output": str(OUT)}, sort_keys=True))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
