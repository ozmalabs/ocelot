#!/usr/bin/env python3
"""Generate P14's bounded, graph-authored invention-operator lifecycle."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from track_i_seed_lib import (A, And, Eq, Gt, Gte, L, Lte, N, Not, OFFLINE_AREA, Or,
                              ZERO, policy_on, productions, rule)  # noqa: E402

SEED_ID = "invention_operator_authorship"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def build():
    specs = [
        ("Agent", "has_invention_operator_authorship_policy", "InventionOperatorAuthorshipPolicy"),
        ("Agent", "has_operator_composition_request", "OperatorCompositionRequest"),
        ("Agent", "has_candidate_operator", "CandidateOperator"),
        ("CandidateOperator", "has_expression_root", "OperatorExpression"),
        ("OperatorExpression", "expr_child", "OperatorExpression"),
        ("Agent", "has_promotion_approval", "OperatorPromotionApproval"),
        ("Agent", "has_invention_operator", "InventionOperator"),
        ("InventionOperator", "derived_from_candidate", "CandidateOperator"),
        ("InventionOperator", "parent_operator", "InventionOperator"),
    ]
    proposal = rule(
        "ioa_build_graph_authored_operator_candidate", OFFLINE_AREA, 10,
        "Build a bounded candidate expression graph from an explicit composition request over the held algebra.",
        [["agent", "has_invention_operator_authorship_policy", "pol"],
         ["agent", "has_operator_composition_request", "req"]],
        And(policy_on(), Eq(A("req", "status"), L("draft")),
            Eq(A("req", "recipe"), L("commutator_square")),
            Eq(A("req", "left_operator"), L("commutator")),
            Eq(A("req", "right_operator"), L("commutator")),
            Eq(A("req", "candidate_name"), L("commutator_square_v1"))),
        [["add_node", "candidate", "CandidateOperator", {
            "name": "commutator_square_v1", "status": "draft",
            "grammar": "held_algebra_v1", "operator": "compose",
            "authoring": "native_graph_rule", "parent_operator_name": "commutator",
            "expression_node_cap": 7, "resource_cap": 32,
            "criteria_digest": "pmb-v1-frozen-criteria",
            "lineage": "commutator -> compose(commutator,commutator)"}],
         ["add_edge", "agent", "has_candidate_operator", "candidate", {}],
         ["add_node", "root", "OperatorExpression", {"kind": "operator", "operator": "compose"}],
         ["add_node", "left", "OperatorExpression", {"kind": "operator", "operator": "commutator"}],
         ["add_node", "right", "OperatorExpression", {"kind": "operator", "operator": "commutator"}],
         ["add_node", "arg_a0", "OperatorExpression", {"kind": "input", "name": "a"}],
         ["add_node", "arg_b0", "OperatorExpression", {"kind": "input", "name": "b"}],
         ["add_node", "arg_a1", "OperatorExpression", {"kind": "input", "name": "a"}],
         ["add_node", "arg_b1", "OperatorExpression", {"kind": "input", "name": "b"}],
         ["add_edge", "candidate", "has_expression_root", "root", {}],
         ["add_edge", "root", "expr_child", "left", {"slot": 0}],
         ["add_edge", "root", "expr_child", "right", {"slot": 1}],
         ["add_edge", "left", "expr_child", "arg_a0", {"slot": 0}],
         ["add_edge", "left", "expr_child", "arg_b0", {"slot": 1}],
         ["add_edge", "right", "expr_child", "arg_a1", {"slot": 0}],
         ["add_edge", "right", "expr_child", "arg_b1", {"slot": 1}],
         ["set_attr", "req", "status", "built"]], batch=True)
    unsafe = rule(
        "ioa_reject_unsafe_composition_request", OFFLINE_AREA, 11,
        "Reject requests outside the small held-algebra graph grammar; no source code or verifier edits are admitted.",
        [["agent", "has_invention_operator_authorship_policy", "pol"],
         ["agent", "has_operator_composition_request", "req"]],
        And(policy_on(), Eq(A("req", "status"), L("draft")),
            Or(Not(Eq(A("req", "recipe"), L("commutator_square"))),
               Not(Eq(A("req", "left_operator"), L("commutator"))),
               Not(Eq(A("req", "right_operator"), L("commutator"))))),
        [["set_attr", "req", "status", "rejected"],
         ["set_attr", "req", "rejection_reason", "operator_outside_held_algebra_template"]])
    measure_pass = rule(
        "ioa_qualify_development_measurement", OFFLINE_AREA, 20,
        "Development-only positive yield may qualify a candidate when invariant checks are preserved and actual work is within the cap.",
        [["agent", "has_invention_operator_authorship_policy", "pol"],
         ["agent", "has_candidate_operator", "c"]],
        And(policy_on(), Eq(A("c", "status"), L("measured")),
            Eq(A("c", "grammar"), L("held_algebra_v1")),
            Gt(A("c", "development_yield"), A("c", "parent_development_yield")),
            Eq(A("c", "invariant_checks"), A("c", "parent_invariant_checks")),
            Eq(A("c", "proof_failures"), L(0)),
            Gte(A("c", "candidate_work"), ZERO),
            Lte(A("c", "candidate_work"), A("pol", "max_resource_work"))),
        [["set_attr", "c", "status", "awaiting_human"],
         ["set_attr", "c", "verdict", "development_qualified"],
         ["set_attr", "c", "criteria_digest", "pmb-v1-frozen-criteria"]])
    measure_fail = rule(
        "ioa_reject_unqualified_development_measurement", OFFLINE_AREA, 21,
        "Reject candidates with nonpositive development gain, proof failures or a changed invariant-check count.",
        [["agent", "has_invention_operator_authorship_policy", "pol"],
         ["agent", "has_candidate_operator", "c"]],
        And(policy_on(), Eq(A("c", "status"), L("measured")),
            Or(Not(Gt(A("c", "development_yield"), A("c", "parent_development_yield"))),
               Not(Eq(A("c", "invariant_checks"), A("c", "parent_invariant_checks"))),
               Not(Eq(A("c", "proof_failures"), L(0))),
               Not(Gte(A("c", "candidate_work"), ZERO)),
               Not(Lte(A("c", "candidate_work"), A("pol", "max_resource_work"))))),
        [["set_attr", "c", "status", "rejected"],
         ["set_attr", "c", "verdict", "development_or_invariant_gate_failed"]])
    promote = rule(
        "ioa_promote_only_with_existing_human_gate", OFFLINE_AREA, 30,
        "Promotion requires the existing explicit human approval event and the frozen criteria digest; it retains the held parent for rollback.",
        [["agent", "has_invention_operator_authorship_policy", "pol"],
         ["agent", "has_candidate_operator", "c"],
         ["agent", "has_promotion_approval", "approval"],
         ["agent", "has_invention_operator", "parent"]],
        And(policy_on(), Eq(A("c", "status"), L("awaiting_human")),
            Eq(A("approval", "status"), L("approved")),
            Eq(A("approval", "approval_kind"), L("human")),
            Eq(A("approval", "candidate_name"), A("c", "name")),
            Eq(A("approval", "criteria_digest"), L("pmb-v1-frozen-criteria")),
            Eq(A("c", "criteria_digest"), L("pmb-v1-frozen-criteria")),
            Eq(A("parent", "name"), A("c", "parent_operator_name"))),
        [["add_node", "op", "InventionOperator", {
            "name": {"__term__": A("c", "name")}, "status": "active",
            "provenance": "agent_authored_graph_data", "candidate_digest": {"__term__": A("c", "name")},
            "parent_operator": {"__term__": A("c", "parent_operator_name")},
            "rollback_target": {"__term__": A("c", "parent_operator_name")},
            "lineage": {"__term__": A("c", "lineage")}, "approval_kind": "human"}],
         ["add_edge", "agent", "has_invention_operator", "op", {}],
         ["add_edge", "op", "parent_operator", "parent", {}],
         ["add_edge", "op", "derived_from_candidate", "c", {}],
         ["set_attr", "c", "status", "promoted"]], batch=True)
    return {
        "id": SEED_ID, "version": "1.0.0", "depends_on": ["process_proof_adoption"],
        "self_load_only": True, "area": OFFLINE_AREA,
        "description": "P14.04: proposal-only bounded graph-authored invention operators. Candidate data cannot write criteria, verifier, held-out evaluation or approval. Promotion retains an explicit human gate and rollback lineage.",
        "nodes": [{"local_id": 0, "type": "InventionOperatorAuthorshipPolicy", "attrs": {
            "name": "invention_operator_authorship_policy", "enabled": 0.0,
            "max_expression_nodes": 7, "max_resource_work": 32,
            "frozen_criteria_digest": "pmb-v1-frozen-criteria", "human_gate": 1}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_invention_operator_authorship_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions(SEED_ID, specs),
        "rules": [proposal, unsafe, measure_pass, measure_fail, promote],
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
