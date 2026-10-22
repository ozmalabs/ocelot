#!/usr/bin/env python3
"""Generate guarded P20 source-prior confirmation rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "target_learning.json"
AREA = "target_learning"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(v): return {"__term__": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Exists(source, name, predicate):
    return {"type": "Exists", "source": source, "var_name": name, "predicate": predicate}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}


def build_seed():
    relations = [
        ("Agent", "has_target_learning_policy", "TargetLearningPolicy"),
        ("Agent", "has_target_source_prior", "TargetProcessPrior"),
        ("TargetProcessPrior", "has_source_target_map", "RepresentationMap"),
        ("TargetProcessPrior", "has_source_prior_receipt", "TargetSourcePriorReceipt"),
        ("TargetProcessPrior", "supported_by_target_transition", "TransitionObservation"),
        ("TargetProcessPrior", "verified_by_target_receipt", "TargetSourcePriorReceipt"),
        ("TargetSourcePriorReceipt", "verifies_source_prior", "TargetProcessPrior"),
        ("TargetSourcePriorReceipt", "verifies_target_transition", "TransitionObservation"),
        ("ProcessInductionHypothesis", "supported_by_source_prior", "TargetProcessPrior"),
    ]
    rule = {
        "name": "tl_confirm_mapped_source_prior_with_target_receipt",
        "area": AREA, "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [
            ["ag", "has_target_learning_policy", "pol"],
            ["ag", "has_target_source_prior", "prior"],
            ["prior", "has_source_target_map", "map"],
            ["prior", "has_source_prior_receipt", "receipt"],
            ["prior", "has_source_prior_receipt", "map_receipt"],
            ["ag", "has_transition_observation", "obs"],
            ["obs", "has_action_receipt", "action_receipt"],
            ["obs", "has_outcome_receipt", "outcome_receipt"],
        ],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("prior", "status"), L("candidate")),
            Eq(A("prior", "owner_id"), A("obs", "owner_id")),
            Eq(A("prior", "action_kind"), A("obs", "action_kind")),
            Eq(A("prior", "object_type"), A("obs", "object_type")),
            Eq(A("prior", "feature_key"), A("obs", "feature_key")),
            Eq(A("prior", "before_value"), A("obs", "before_value")),
            Eq(A("prior", "after_value"), A("obs", "after_value")),
            Eq(A("prior", "source_epoch"), A("obs", "source_epoch")),
            Eq(A("prior", "model_epoch"), A("obs", "model_epoch")),
            Eq(A("map", "status"), L("verified")),
            Eq(A("map", "mapping_kind"), L("exact_categorical_effect")),
            Eq(A("map", "target_frame_epoch"), A("obs", "frame_epoch")),
            Eq(A("receipt", "status"), L("verified")),
            Eq(A("receipt", "exact_effect_match"), L(True)),
            Eq(A("receipt", "source_prior_id"), A("prior", "prior_id")),
            Eq(A("receipt", "target_event_id"), A("obs", "event_id")),
            Eq(A("map_receipt", "receipt_kind"), L("source_target_map")),
            Eq(A("map_receipt", "status"), L("verified")),
            Eq(A("map_receipt", "map_id"), A("map", "map_id")),
            Eq(A("obs", "status"), L("observed")),
            Eq(A("action_receipt", "status"), L("observed")),
            Eq(A("outcome_receipt", "status"), L("observed")),
            Eq(A("obs", "owner_id"), A("action_receipt", "owner_id")),
            Eq(A("obs", "owner_id"), A("outcome_receipt", "owner_id")),
            Eq(A("obs", "event_id"), A("action_receipt", "event_id")),
            Eq(A("obs", "event_id"), A("outcome_receipt", "event_id")),
            Eq(A("obs", "model_epoch"), A("action_receipt", "model_epoch")),
            Eq(A("obs", "model_epoch"), A("outcome_receipt", "model_epoch")),
            Not(Exists(N("ag", "has_process_induction_hypothesis"), "old",
                       Eq(A("old", "source_prior_id"), A("prior", "prior_id")))),
        ),
        "effects": [
            ["add_node", "hyp", "ProcessInductionHypothesis", {
                "hypothesis_key": T(Concat(L("source-confirmed:"), A("prior", "prior_id"))),
                "owner_id": T(A("obs", "owner_id")),
                "action_kind": T(A("obs", "action_kind")),
                "object_type": T(A("obs", "object_type")),
                "feature_key": T(A("obs", "feature_key")),
                "before_value": T(A("obs", "before_value")),
                "after_value": T(A("obs", "after_value")),
                "source_epoch": T(A("obs", "source_epoch")),
                "model_epoch": T(A("obs", "model_epoch")),
                "frame_epoch": T(A("obs", "frame_epoch")),
                "status": "candidate", "law_kind": "mapped_source_prior_confirmed",
                "support_count": 1.0, "target_support_count": 1.0,
                "evidence_count": 2.0, "counterexample_count": 0.0,
                "source_prior_id": T(A("prior", "prior_id")),
                "target_confirmation_event_id": T(A("obs", "event_id")),
                "effect_evaluation": "exact_source_map_and_target_receipt"}],
            ["add_edge", "ag", "has_process_induction_hypothesis", "hyp", {}],
            ["add_edge", "hyp", "supported_by_transition", "obs", {}],
            ["add_edge", "hyp", "supported_by_source_prior", "prior", {}],
            ["add_edge", "prior", "supported_by_target_transition", "obs", {}],
            ["add_edge", "prior", "verified_by_target_receipt", "receipt", {}],
            ["add_edge", "receipt", "verifies_source_prior", "prior", {}],
            ["add_edge", "receipt", "verifies_target_transition", "obs", {}],
        ],
    }
    return {
        "id": "target_learning", "version": "1.0.0",
        "depends_on": ["process_induction"], "self_load_only": True,
        "area": AREA,
        "description": "P20 exact mapped source priors require independent target-transition receipt before native prediction.",
        "microtheory": {"name": AREA,
                        "description": "Source priors are proposals; only exact maps plus current target receipts create a usable hypothesis."},
        "nodes": [{"local_id": 0, "type": "TargetLearningPolicy", "attrs": {
            "name": "target_learning_policy", "enabled": 0.0,
            "max_source_priors": 32.0}}],
        "edges": [{"src": {"role": "agent_root"},
                   "type": "has_target_learning_policy", "tgt": {"local": 0},
                   "attrs": {}}],
        "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                         "src": {"type": src, "var": "src"},
                         "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"}}
                        for src, edge, tgt in relations],
        "rules": [rule],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(OUT)
