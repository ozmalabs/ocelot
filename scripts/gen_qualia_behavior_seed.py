#!/usr/bin/env python3
"""Generate native prediction/action rules over acquired qualia witnesses."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "qualia_behavior.json"
AREA = "qualia_behavior"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(t): return {"__term__": t}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def In(a, b): return {"type": "In", "member": a, "container": b}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def SortBy(src, var, key): return {"type": "SortBy", "source": src, "var_name": var, "key": key}
def IndexAt(seq, ix): return {"type": "IndexAt", "seq": seq, "index": L(ix)}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}
def Json(x): return {"type": "ToJsonString", "value": x}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}


def key():
    return Concat(A("ev", "event_id"), L(":"), A("f", "feature_id"), L(":"),
                  Json(A("f", "source_epoch")), L(":"), A("dim", "name"))


def request_rule():
    duplicate_candidate = IndexAt(SortBy(Filter(N("ag", "has_qualia_axis_candidate"), "same",
        Eq(A("same", "candidate_key"), A("candidate", "candidate_key"))), "same",
        A("same", "created_epoch")), 0)
    duplicate_dimension = IndexAt(SortBy(Filter(N("ag", "has_qualia_dimension"), "same_dim",
        Eq(A("same_dim", "name"), A("dim", "name"))), "same_dim",
        A("same_dim", "name")), 0)
    first_witness = IndexAt(SortBy(Filter(N("candidate", "has_acquisition_witness"), "same_w",
        And(Eq(A("same_w", "feature_value"), A("f", "feature_value")),
            Eq(A("same_w", "owner_id"), A("ep", "owner_id")))), "same_w",
        A("same_w", "event_id")), 0)
    return {
        "name": "qbh_request_funded_fresh_prediction", "area": AREA,
        "order": 1, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_qualia_behavior_policy", "pol"],
                  ["ag", "has_thinking_budget", "budget"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_experience_episode", "ep"],
                  ["ep", "has_experience_event", "ev"],
                  ["ev", "has_episode_feature", "f"],
                  ["ag", "has_qualia_dimension", "dim"],
                  ["ag", "has_qualia_axis_candidate", "candidate"],
                  ["candidate", "has_acquisition_witness", "w"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("budget", "enabled"), L(1.0)),
                     Eq(A("ep", "status"), L("observed")),
                     Eq(A("ev", "status"), L("observed")),
                     Eq(A("ev", "event_role"), L("fresh_task")),
                     Eq(A("f", "status"), L("observed")),
                     Eq(A("ev", "owner_id"), A("ep", "owner_id")),
                     Eq(A("f", "owner_id"), A("ep", "owner_id")),
                     Eq(A("f", "episode_id"), A("ep", "episode_id")),
                     Eq(A("f", "event_id"), A("ev", "event_id")),
                     Eq(A("f", "source_epoch"), A("ev", "source_epoch")),
                     Eq(A("f", "model_epoch"), A("ev", "model_epoch")),
                     Eq(A("f", "frame_epoch"), A("ev", "frame_epoch")),
                     Eq(A("candidate", "status"), L("validated")),
                     Eq(V("candidate"), duplicate_candidate),
                     Eq(V("dim"), duplicate_dimension),
                     Eq(V("w"), first_witness),
                     Eq(A("ev", "event_role"), L("fresh_task")),
                     Eq(A("dim", "acquired"), L(1.0)),
                     Eq(A("dim", "acquisition_status"), L("standing")),
                     Eq(A("dim", "name"), A("candidate", "dimension_id")),
                     Eq(A("dim", "owner_id"), A("ep", "owner_id")),
                     Eq(A("candidate", "owner_id"), A("ep", "owner_id")),
                     Eq(A("candidate", "feature_key"), A("f", "feature_key")),
                     Eq(A("candidate", "feature_family"), A("f", "feature_family")),
                     Eq(A("candidate", "value_kind"), A("f", "value_kind")),
                     Eq(A("candidate", "model_epoch"), A("f", "model_epoch")),
                     Eq(A("candidate", "frame_epoch"), A("f", "frame_epoch")),
                     Eq(A("ev", "owner_id"), A("ep", "owner_id")),
                     Eq(A("f", "owner_id"), A("ep", "owner_id")),
                     Eq(A("f", "episode_id"), A("ep", "episode_id")),
                     Eq(A("f", "event_id"), A("ev", "event_id")),
                     Eq(A("f", "source_epoch"), A("ev", "source_epoch")),
                     Eq(A("f", "model_epoch"), A("ev", "model_epoch")),
                     Eq(A("f", "frame_epoch"), A("ev", "frame_epoch")),
                     Eq(A("w", "owner_id"), A("ep", "owner_id")),
                     Eq(A("w", "feature_key"), A("f", "feature_key")),
                     Eq(A("w", "feature_family"), A("f", "feature_family")),
                     Eq(A("w", "value_kind"), A("f", "value_kind")),
                     Eq(A("w", "model_epoch"), A("f", "model_epoch")),
                     Eq(A("w", "frame_epoch"), A("f", "frame_epoch")),
                     Eq(A("f", "is_missing"), L(False)),
                     Not(Eq(A("f", "feature_value"), L(None))),
                     Eq(A("w", "feature_value"), A("f", "feature_value")),
                     Not(Exists(N("ag", "has_thinking_budget_request"), "old",
                                Eq(A("old", "requester_key"), key()))),
                     Not(Exists(N("ag", "has_qualia_behavior_prediction"), "oldp",
                                Eq(A("oldp", "prediction_key"), key())))),
        "effects": [["add_node", "req", "ThinkingBudgetRequest", {
            "requester_kind": "qualia_behavior_inference", "requester_key": T(key()),
            "source_key": T(A("ev", "event_id")), "source_epoch": T(A("f", "source_epoch")),
            "requested_epoch": T(A("mode", "epoch")),
            "deadline_epoch": T(Plus(A("mode", "epoch"), L(1))),
            "cost": T(A("pol", "inference_cost")), "status": "pending"}],
                    ["add_edge", "ag", "has_thinking_budget_request", "req", {}],
                    ["add_edge", "req", "draws_on_thinking_budget", "budget", {}],
                    ["add_edge", "req", "funds_qualia_prediction", "f", {}]],
    }


def prediction_rule():
    duplicate_candidate = IndexAt(SortBy(Filter(N("ag", "has_qualia_axis_candidate"), "same",
        Eq(A("same", "candidate_key"), A("candidate", "candidate_key"))), "same",
        A("same", "created_epoch")), 0)
    duplicate_dimension = IndexAt(SortBy(Filter(N("ag", "has_qualia_dimension"), "same_dim",
        Eq(A("same_dim", "name"), A("dim", "name"))), "same_dim",
        A("same_dim", "name")), 0)
    first_witness = IndexAt(SortBy(Filter(N("candidate", "has_acquisition_witness"), "same_w",
        And(Eq(A("same_w", "feature_value"), A("f", "feature_value")),
            Eq(A("same_w", "owner_id"), A("ep", "owner_id")))), "same_w",
        A("same_w", "event_id")), 0)
    return {
        "name": "qbh_emit_source_bound_prediction_and_action_proposal", "area": AREA,
        "order": 10, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_qualia_behavior_policy", "pol"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_experience_episode", "ep"],
                  ["ep", "has_experience_event", "ev"],
                  ["ev", "has_episode_feature", "f"],
                  ["ag", "has_qualia_dimension", "dim"],
                  ["ag", "has_qualia_axis_candidate", "candidate"],
                  ["candidate", "has_acquisition_witness", "w"],
                  ["ag", "has_thinking_budget_request", "req"],
                  ["req", "funds_qualia_prediction", "f"],
                  ["req", "draws_on_thinking_budget", "budget"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("candidate", "status"), L("validated")),
                     Eq(V("candidate"), duplicate_candidate),
                     Eq(V("dim"), duplicate_dimension),
                     Eq(V("w"), first_witness),
                     Eq(A("dim", "acquisition_status"), L("standing")),
                     Eq(A("dim", "acquired"), L(1.0)),
                     Eq(A("dim", "name"), A("candidate", "dimension_id")),
                     Eq(A("dim", "owner_id"), A("ep", "owner_id")),
                     Eq(A("candidate", "owner_id"), A("ep", "owner_id")),
                     Eq(A("candidate", "feature_key"), A("f", "feature_key")),
                     Eq(A("candidate", "feature_family"), A("f", "feature_family")),
                     Eq(A("candidate", "value_kind"), A("f", "value_kind")),
                     Eq(A("candidate", "model_epoch"), A("f", "model_epoch")),
                     Eq(A("candidate", "frame_epoch"), A("f", "frame_epoch")),
                     Eq(A("w", "owner_id"), A("ep", "owner_id")),
                     Eq(A("w", "feature_key"), A("f", "feature_key")),
                     Eq(A("w", "feature_family"), A("f", "feature_family")),
                     Eq(A("w", "value_kind"), A("f", "value_kind")),
                     Eq(A("w", "model_epoch"), A("f", "model_epoch")),
                     Eq(A("w", "frame_epoch"), A("f", "frame_epoch")),
                     Eq(A("w", "feature_value"), A("f", "feature_value")),
                     Eq(A("f", "is_missing"), L(False)),
                     Eq(A("req", "status"), L("approved")),
                     Eq(A("req", "debited_epoch"), A("mode", "epoch")),
                     Eq(A("req", "source_epoch"), A("f", "source_epoch")),
                     Eq(A("req", "requested_epoch"), A("mode", "epoch")),
                     Not(Exists(N("ag", "has_qualia_behavior_prediction"), "old",
                                Eq(A("old", "prediction_key"), key())))),
        "effects": [["add_node", "pred", "QualiaBehaviorPrediction", {
            "prediction_key": T(key()), "owner_id": T(A("ep", "owner_id")),
            "episode_id": T(A("ep", "episode_id")), "context_id": T(A("ep", "context_id")),
            "event_id": T(A("ev", "event_id")),
            "feature_id": T(A("f", "feature_id")),
            "feature_id": T(A("f", "feature_id")), "feature_key": T(A("f", "feature_key")),
            "feature_family": T(A("f", "feature_family")),
            "feature_value": T(A("f", "feature_value")),
            "predicted_consequence_kind": T(A("w", "consequence_kind")),
            "predicted_consequence": T(A("w", "consequence_value")),
            "proposed_action_id": T(A("w", "action_id")),
            "dimension_id": T(A("dim", "name")),
            "dimension_status": T(A("dim", "acquisition_status")),
            "source_epoch": T(A("f", "source_epoch")),
            "model_epoch": T(A("f", "model_epoch")),
            "frame_epoch": T(A("f", "frame_epoch")),
            "witness_event_id": T(A("w", "event_id")),
            "attention_priority": "ordinary", "status": "proposed"}],
                    ["add_edge", "ag", "has_qualia_behavior_prediction", "pred", {}],
                    ["add_edge", "pred", "uses_feature_observation", "f", {}],
                    ["add_edge", "pred", "uses_qualia_dimension", "dim", {}],
                    ["add_edge", "pred", "uses_acquisition_witness", "w", {}],
                    ["add_edge", "pred", "uses_budget_request", "req", {}],
                    ["set_attr", "req", "status", "consumed"]],
    }


def authorize_action_rule():
    previous = Exists(N("ag", "has_qualia_action_authorization"), "old",
                      Eq(A("old", "prediction_key"), A("pred", "prediction_key")))
    attrs = {"authorization_id": T(Concat(A("pred", "prediction_key"), L(":authorized"))),
        "prediction_key": T(A("pred", "prediction_key")),
        "owner_id": T(A("pred", "owner_id")), "event_id": T(A("pred", "event_id")),
        "action_id": T(A("pred", "proposed_action_id")),
        "dimension_id": T(A("pred", "dimension_id")),
        "world_id": T(A("ctx", "world_id")), "world_epoch": T(A("ctx", "world_epoch")),
        "source_epoch": T(A("pred", "source_epoch")),
        "budget_request_id": T(A("req", "requester_key")), "status": "authorized"}
    return {"name": "qbh_authorize_only_source_bound_legal_funded_action", "area": AREA,
        "order": 15, "latency_class": "hard_realtime", "batch": False,
        "match": [["ag", "has_qualia_behavior_policy", "pol"],
                  ["ag", "has_network_mode_state", "mode"],
                  ["ag", "has_qualia_behavior_prediction", "pred"],
                  ["pred", "uses_feature_observation", "feature"],
                  ["ag", "has_experience_episode", "ep"],
                  ["ep", "has_experience_event", "ev"],
                  ["ev", "has_episode_feature", "feature"],
                  ["pred", "uses_qualia_dimension", "dim"],
                  ["pred", "uses_budget_request", "req"],
                  ["ag", "has_qualia_action_context", "ctx"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
                     Eq(A("pred", "status"), L("proposed")),
                     Eq(A("dim", "acquisition_status"), L("standing")),
                     Eq(A("dim", "name"), A("pred", "dimension_id")),
                     Eq(A("dim", "owner_id"), A("pred", "owner_id")),
                     Eq(A("req", "status"), L("consumed")),
                     Eq(A("req", "debited_epoch"), A("mode", "epoch")),
                     Eq(A("req", "source_epoch"), A("pred", "source_epoch")),
                     Eq(A("ctx", "status"), L("active")),
                     Eq(A("ctx", "owner_id"), A("pred", "owner_id")),
                     Eq(A("ctx", "event_id"), A("pred", "event_id")),
                     Eq(A("ctx", "source_epoch"), A("pred", "source_epoch")),
                     Eq(A("ev", "event_id"), A("pred", "event_id")),
                     Eq(A("ctx", "world_epoch"), A("ev", "world_epoch")),
                     In(A("pred", "proposed_action_id"), A("ctx", "legal_actions")),
                     Not(previous)),
        "effects": [["add_node", "auth", "QualiaActionAuthorization", attrs],
                    ["add_edge", "ag", "has_qualia_action_authorization", "auth", {}],
                    ["add_edge", "pred", "has_action_authorization", "auth", {}],
                    ["add_edge", "auth", "authorizes_prediction", "pred", {}],
                    ["add_edge", "auth", "applies_to_world_context", "ctx", {}],
                    ["add_edge", "auth", "authorized_by_budget_request", "req", {}]]}


def build_seed():
    relations = [
        ("Agent", "has_qualia_behavior_policy", "QualiaBehaviorPolicy"),
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
        ("Agent", "has_network_mode_state", "NetworkModeState"),
        ("Agent", "has_experience_episode", "ExperienceEpisode"),
        ("ExperienceEpisode", "has_experience_event", "ExperienceEvent"),
        ("ExperienceEvent", "has_episode_feature", "ExperienceFeatureObservation"),
        ("Agent", "has_qualia_dimension", "QualiaDimension"),
        ("Agent", "has_qualia_axis_candidate", "QualiaAxisCandidate"),
        ("QualiaAxisCandidate", "has_acquisition_witness", "QualiaAcquisitionWitness"),
        ("Agent", "has_thinking_budget_request", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("ThinkingBudgetRequest", "funds_qualia_prediction", "ExperienceFeatureObservation"),
        ("Agent", "has_qualia_behavior_prediction", "QualiaBehaviorPrediction"),
        ("QualiaBehaviorPrediction", "uses_feature_observation", "ExperienceFeatureObservation"),
        ("QualiaBehaviorPrediction", "uses_qualia_dimension", "QualiaDimension"),
        ("QualiaBehaviorPrediction", "uses_acquisition_witness", "QualiaAcquisitionWitness"),
        ("Agent", "has_qualia_action_context", "QualiaActionContext"),
        ("Agent", "has_qualia_action_authorization", "QualiaActionAuthorization"),
        ("QualiaBehaviorPrediction", "uses_budget_request", "ThinkingBudgetRequest"),
        ("QualiaBehaviorPrediction", "has_action_authorization", "QualiaActionAuthorization"),
        ("QualiaActionAuthorization", "authorizes_prediction", "QualiaBehaviorPrediction"),
        ("QualiaActionAuthorization", "applies_to_world_context", "QualiaActionContext"),
        ("QualiaActionAuthorization", "authorized_by_budget_request", "ThinkingBudgetRequest"),
    ]
    return {"id": "qualia_behavior", "version": "1.0.0",
            "depends_on": ["qualia_acquisition", "thinking_budget"],
            "self_load_only": True, "area": AREA,
            "description": "P17.02 source-bound native predictions and action proposals from standing acquired distinctions.",
            "microtheory": {"name": AREA, "description": "Use only verified acquired axes to predict later consequences."},
            "nodes": [{"local_id": 0, "type": "QualiaBehaviorPolicy",
                       "attrs": {"name": "qualia_behavior_policy", "enabled": 0.0,
                                 "inference_cost": 1.0, "max_predictions": 2000.0}}],
            "edges": [{"src": {"role": "agent_root"}, "type": "has_qualia_behavior_policy",
                       "tgt": {"local": 0}, "attrs": {}}],
            "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                             "src": {"type": src, "var": "src"}, "edge_type": edge,
                             "tgt": {"type": tgt, "var": "tgt"}} for src, edge, tgt in relations],
            "rules": [request_rule(), prediction_rule(), authorize_action_rule()]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
