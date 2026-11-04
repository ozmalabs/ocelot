#!/usr/bin/env python3
"""Generate native, additive source-prior proposal rules for P24."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "additive_transfer.json"
AREA = "additive_transfer"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def T(v): return {"__term__": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Exists(source, name, predicate):
    return {"type": "Exists", "source": source, "var_name": name, "predicate": predicate}
def N(n, edge): return {"type": "Neighbours", "node": V(n), "edge_type": edge, "any_type": False}


def build_seed():
    relations = [
        ("Agent", "has_additive_transfer_policy", "AdditiveTransferPolicy"),
        ("Agent", "has_source_model_proposal", "SourceModelProposal"),
        ("SourceModelProposal", "uses_verified_map", "RepresentationMap"),
        ("SourceModelProposal", "has_map_verification", "TargetSourcePriorReceipt"),
        ("SourceModelProposal", "has_target_effect_verification", "TargetSourcePriorReceipt"),
        ("Agent", "has_target_source_prior", "TargetProcessPrior"),
        ("TargetProcessPrior", "has_source_target_map", "RepresentationMap"),
        ("TargetProcessPrior", "has_source_prior_receipt", "TargetSourcePriorReceipt"),
        ("TargetMapObservation", "funded_by", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("ThinkingBudgetRequest", "funds_target_map_observation", "TargetMapObservation"),
    ]
    attrs = {key: T(A("proposal", key)) for key in (
        "prior_id", "source_id", "owner_id", "action_kind", "object_type",
        "feature_key", "before_value", "after_value", "source_epoch",
        "model_epoch", "frame_epoch")}
    attrs["status"] = "candidate"
    same_effect = And(
        Eq(A("same", "owner_id"), A("proposal", "owner_id")),
        Eq(A("same", "action_kind"), A("proposal", "action_kind")),
        Eq(A("same", "object_type"), A("proposal", "object_type")),
        Eq(A("same", "feature_key"), A("proposal", "feature_key")),
        Eq(A("same", "before_value"), A("proposal", "before_value")),
        Eq(A("same", "after_value"), A("proposal", "after_value")),
        Eq(A("same", "source_epoch"), A("proposal", "source_epoch")),
        Eq(A("same", "model_epoch"), A("proposal", "model_epoch")),
        Eq(A("same", "frame_epoch"), A("proposal", "frame_epoch")))
    rule = {
        "name": "at_import_verified_source_effect_as_additive_candidate",
        "area": AREA, "order": 1, "latency_class": "background", "batch": False,
        "match": [["ag", "has_additive_transfer_policy", "pol"],
                  ["ag", "has_source_model_proposal", "proposal"],
                  ["proposal", "uses_verified_map", "map"],
                  ["proposal", "has_map_verification", "map_receipt"],
                  ["proposal", "has_target_effect_verification", "effect_receipt"]],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("proposal", "status"), L("candidate")),
            Eq(A("map", "status"), L("verified")),
            Eq(A("map", "mapping_kind"), L("exact_categorical_effect")),
            Eq(A("map_receipt", "receipt_kind"), L("source_target_map")),
            Eq(A("map_receipt", "status"), L("verified")),
            Eq(A("map_receipt", "map_id"), A("map", "map_id")),
            Eq(A("effect_receipt", "receipt_kind"), L("target_prior_effect")),
            Eq(A("effect_receipt", "status"), L("verified")),
            Eq(A("effect_receipt", "exact_effect_match"), L(True)),
            Eq(A("effect_receipt", "source_prior_id"), A("proposal", "prior_id")),
            Eq(A("proposal", "target_event_id"), A("effect_receipt", "target_event_id")),
            Not(Exists(N("ag", "has_target_source_prior"), "old",
                       Eq(A("old", "prior_id"), A("proposal", "prior_id")))),
            Not(Exists(N("ag", "has_process_induction_hypothesis"), "same",
                       same_effect))),
        "effects": [
            ["add_node", "prior", "TargetProcessPrior", attrs],
            ["add_edge", "ag", "has_target_source_prior", "prior", {}],
            ["add_edge", "prior", "has_source_target_map", "map", {}],
            ["add_edge", "prior", "has_source_prior_receipt", "map_receipt", {}],
            ["add_edge", "prior", "has_source_prior_receipt", "effect_receipt", {}],
            ["set_attr", "proposal", "status", "imported_candidate"],
        ],
    }
    portfolio_attrs = dict(attrs)
    portfolio_attrs["status"] = "portfolio_candidate"
    portfolio_rule = {
        "name": "at_retain_redundant_source_as_portfolio_candidate",
        "area": AREA, "order": 2, "latency_class": "background", "batch": False,
        "match": [["ag", "has_additive_transfer_policy", "pol"],
                  ["ag", "has_source_model_proposal", "proposal"],
                  ["proposal", "uses_verified_map", "map"],
                  ["proposal", "has_map_verification", "map_receipt"],
                  ["proposal", "has_target_effect_verification", "effect_receipt"],
                  ["ag", "has_process_induction_hypothesis", "same"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("proposal", "status"), L("candidate")),
                      Eq(A("map", "status"), L("verified")),
                      Eq(A("map", "mapping_kind"), L("exact_categorical_effect")),
                      Eq(A("map_receipt", "receipt_kind"), L("source_target_map")),
                      Eq(A("map_receipt", "status"), L("verified")),
                      Eq(A("map_receipt", "map_id"), A("map", "map_id")),
                      Eq(A("effect_receipt", "receipt_kind"), L("target_prior_effect")),
                      Eq(A("effect_receipt", "status"), L("verified")),
                      Eq(A("effect_receipt", "exact_effect_match"), L(True)),
                      Eq(A("effect_receipt", "source_prior_id"), A("proposal", "prior_id")),
                      Eq(A("proposal", "target_event_id"), A("effect_receipt", "target_event_id")),
                      Eq(A("same", "owner_id"), A("proposal", "owner_id")),
                      Eq(A("same", "action_kind"), A("proposal", "action_kind")),
                      Eq(A("same", "object_type"), A("proposal", "object_type")),
                      Eq(A("same", "feature_key"), A("proposal", "feature_key")),
                      Eq(A("same", "before_value"), A("proposal", "before_value")),
                      Eq(A("same", "after_value"), A("proposal", "after_value")),
                      Eq(A("same", "source_epoch"), A("proposal", "source_epoch")),
                      Eq(A("same", "model_epoch"), A("proposal", "model_epoch")),
                      Eq(A("same", "frame_epoch"), A("proposal", "frame_epoch")),
                      Not(Exists(N("ag", "has_target_source_prior"), "old",
                                 Eq(A("old", "prior_id"), A("proposal", "prior_id"))))),
        "effects": [
            ["add_node", "prior", "TargetProcessPrior", portfolio_attrs],
            ["add_edge", "ag", "has_target_source_prior", "prior", {}],
            ["add_edge", "prior", "has_source_target_map", "map", {}],
            ["add_edge", "prior", "has_source_prior_receipt", "map_receipt", {}],
            ["add_edge", "prior", "has_source_prior_receipt", "effect_receipt", {}],
            ["set_attr", "proposal", "status", "imported_portfolio_candidate"],
        ],
    }
    map_rule = {
        "name": "at_authorize_typed_common_map_pair_and_charge_construction",
        "area": AREA, "order": 0, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_additive_transfer_policy", "pol"],
                  ["ag", "has_common_target_evidence", "event"],
                  ["event", "projects_to_map_pair", "pair"],
                  ["ag", "has_thinking_budget", "budget"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                      Eq(A("pair", "status"), L("map_pending")),
                      Eq(A("pair", "source_status"), L("observed")),
                      Eq(A("pair", "source_action_authorized"), L(True)),
                      Eq(A("pair", "target_action_authorized"), L(True)),
                      Not(Eq(A("pair", "source_event_id"), A("pair", "target_event_id"))),
                      Not(Exists(N("ag", "has_thinking_budget_request"), "old",
                                 Eq(A("old", "source_key"), A("pair", "pair_id"))))),
        "effects": [
            ["set_attr", "pair", "status", "observed_pair"],
            ["add_node", "req", "ThinkingBudgetRequest", {
                "requester_kind": "target_map_observation",
                "source_key": T(A("pair", "pair_id")),
                "source_epoch": T(A("pair", "source_epoch")),
                "requested_epoch": 10.0, "operation_id": T(A("pair", "pair_id")),
                "deadline_epoch": 11.0, "status": "pending", "cost": 1.0}],
            ["add_edge", "ag", "has_thinking_budget_request", "req", {}],
            ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
            ["add_edge", "req", "funds_target_map_observation", "pair", {}],
            ["add_edge", "pair", "funded_by", "req", {}],
        ],
    }
    return {
        "id": "additive_transfer", "version": "1.0.0",
        "depends_on": ["common_target_evidence", "target_learning"],
        "self_load_only": True, "area": AREA,
        "description": "P24 maps verified source structure to a candidate prior while preserving ordinary target learning.",
        "microtheory": {"name": AREA, "description": "Source structure proposes candidates; target evidence remains authoritative."},
        "nodes": [{"local_id": 0, "type": "AdditiveTransferPolicy",
                   "attrs": {"name": "additive_transfer_policy", "enabled": 0.0}}],
        "edges": [{"src": {"role": "agent_root"}, "type": "has_additive_transfer_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                         "src": {"type": src, "var": "src"},
                         "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"}}
                        for src, edge, tgt in relations],
        "rules": [map_rule, rule, portfolio_rule],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(OUT)
