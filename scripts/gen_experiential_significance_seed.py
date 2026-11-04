#!/usr/bin/env python3
"""Generate outcome-witnessed context-sensitive significance rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "experiential_significance.json"
AREA = "experiential_significance"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(t): return {"__term__": t}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def If(cond, yes, no): return {"type": "IfThenElse", "cond": cond, "then": yes, "other": no}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}
def Json(x): return {"type": "ToJsonString", "value": x}


def evidence_rule():
    key = Concat(A("pred", "prediction_key"), L(":"), A("receipt", "receipt_id"))
    prior = Exists(N("ag", "has_experiential_significance_evidence"), "old",
                   Eq(A("old", "evidence_key"), key))
    category = If(Gte(A("receipt", "goal_effect"), L(0.0)), L("supportive"), L("adverse"))
    attrs = {
        "evidence_key": T(key), "owner_id": T(A("pred", "owner_id")),
        "episode_id": T(A("pred", "episode_id")), "event_id": T(A("pred", "event_id")),
        "context_id": T(A("ep", "context_id")), "feature_key": T(A("pred", "feature_key")),
        "feature_value": T(A("pred", "feature_value")),
        "dimension_id": T(A("pred", "dimension_id")),
        "prediction_id": T(A("pred", "prediction_key")),
        "predicted_consequence": T(A("pred", "predicted_consequence")),
        "observed_consequence": T(A("receipt", "consequence_value")),
        "goal_effect": T(A("receipt", "goal_effect")),
        "effect_category": T(category), "source_epoch": T(A("receipt", "source_epoch")),
        "model_epoch": T(A("receipt", "model_epoch")),
        "frame_epoch": T(A("receipt", "frame_epoch")), "status": "verified",
    }
    return {"name": "es_record_verified_consequence_evidence", "area": AREA,
            "order": 1, "latency_class": "background", "batch": False,
            "match": [["ag", "has_experiential_significance_policy", "pol"],
                      ["ag", "has_qualia_behavior_prediction", "pred"],
                      ["pred", "uses_feature_observation", "feature"],
                      ["feature", "has_outcome_receipt", "receipt"],
                      ["ag", "has_experience_episode", "ep"],
                      ["ep", "has_experience_event", "ev"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("pred", "status"), L("proposed")),
                         Eq(A("receipt", "status"), L("observed")),
                         Eq(A("receipt", "evidence_status"), L("observed")),
                         Eq(A("receipt", "owner_id"), A("pred", "owner_id")),
                         Eq(A("receipt", "episode_id"), A("pred", "episode_id")),
                         Eq(A("receipt", "event_id"), A("pred", "event_id")),
                         Eq(A("receipt", "feature_id"), A("pred", "feature_id")),
                         Eq(A("receipt", "source_epoch"), A("pred", "source_epoch")),
                         Eq(A("receipt", "model_epoch"), A("pred", "model_epoch")),
                         Eq(A("receipt", "frame_epoch"), A("pred", "frame_epoch")),
                         Eq(A("ep", "owner_id"), A("pred", "owner_id")),
                         Eq(A("ep", "episode_id"), A("pred", "episode_id")),
                         Eq(A("ev", "event_id"), A("pred", "event_id")), Not(prior)),
            "effects": [["add_node", "evidence", "ExperientialSignificanceEvidence", attrs],
                        ["add_edge", "ag", "has_experiential_significance_evidence", "evidence", {}],
                        ["add_edge", "evidence", "verifies_prediction", "pred", {}],
                        ["add_edge", "evidence", "uses_outcome_receipt", "receipt", {}],
                        ["set_attr", "pred", "status", "verified"]]}


def standing_rule():
    key = Concat(A("e1", "owner_id"), L(":"), A("e1", "feature_key"), L(":"),
                 Json(A("e1", "feature_value")), L(":"), A("e1", "context_id"), L(":"),
                 A("e1", "effect_category"))
    prior = Exists(N("ag", "has_experiential_significance"), "old",
                   Eq(A("old", "significance_key"), key))
    attrs = {"significance_key": T(key), "owner_id": T(A("e1", "owner_id")),
             "feature_key": T(A("e1", "feature_key")),
             "feature_value": T(A("e1", "feature_value")),
             "context_id": T(A("e1", "context_id")),
             "dimension_id": T(A("e1", "dimension_id")),
             "effect_category": T(A("e1", "effect_category")),
             "support_count": 2.0, "status": "standing",
             "attention_priority": T(If(Eq(A("e1", "effect_category"), L("adverse")),
                                         L("protective_review"), L("reuse_candidate")))}
    return {"name": "es_earn_contextual_significance_from_repeated_receipts", "area": AREA,
            "order": 10, "latency_class": "background", "batch": False,
            "match": [["ag", "has_experiential_significance_policy", "pol"],
                      ["ag", "has_experiential_significance_evidence", "e1"],
                      ["ag", "has_experiential_significance_evidence", "e2"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("e1", "status"), L("verified")),
                         Eq(A("e2", "status"), L("verified")),
                         Eq(A("e1", "owner_id"), A("e2", "owner_id")),
                         Eq(A("e1", "feature_key"), A("e2", "feature_key")),
                         Eq(A("e1", "feature_value"), A("e2", "feature_value")),
                         Eq(A("e1", "context_id"), A("e2", "context_id")),
                         Eq(A("e1", "dimension_id"), A("e2", "dimension_id")),
                         Eq(A("e1", "effect_category"), A("e2", "effect_category")),
                         Lt(A("e1", "episode_id"), A("e2", "episode_id")),
                         Not(Eq(A("e1", "episode_id"), A("e2", "episode_id"))), Not(prior)),
            "effects": [["add_node", "sig", "ExperientialSignificance", attrs],
                        ["add_edge", "ag", "has_experiential_significance", "sig", {}],
                        ["add_edge", "sig", "supported_by", "e1", {}],
                        ["add_edge", "sig", "supported_by", "e2", {}]]}


def priority_rule():
    return {"name": "es_project_standing_relevance_into_attention_priority", "area": AREA,
            "order": 20, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_experiential_significance_policy", "pol"],
                      ["ag", "has_qualia_behavior_prediction", "pred"],
                      ["ag", "has_experiential_significance", "sig"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("sig", "status"), L("standing")),
                         Eq(A("sig", "owner_id"), A("pred", "owner_id")),
                         Eq(A("sig", "dimension_id"), A("pred", "dimension_id")),
                         Eq(A("sig", "feature_key"), A("pred", "feature_key")),
                         Eq(A("sig", "context_id"), A("pred", "context_id")),
                         Eq(A("sig", "feature_value"), A("pred", "feature_value")),
                         Not(Eq(A("pred", "significance_key"), A("sig", "significance_key")))),
            "effects": [["set_attr", "pred", "significance_key", T(A("sig", "significance_key"))],
                        ["set_attr", "pred", "attention_priority", T(A("sig", "attention_priority"))]]}


def build_seed():
    relations = [
        ("Agent", "has_experiential_significance_policy", "ExperientialSignificancePolicy"),
        ("Agent", "has_qualia_behavior_prediction", "QualiaBehaviorPrediction"),
        ("QualiaBehaviorPrediction", "uses_feature_observation", "ExperienceFeatureObservation"),
        ("ExperienceFeatureObservation", "has_outcome_receipt", "ExperienceOutcomeReceipt"),
        ("Agent", "has_experience_episode", "ExperienceEpisode"),
        ("ExperienceEpisode", "has_experience_event", "ExperienceEvent"),
        ("Agent", "has_experiential_significance_evidence", "ExperientialSignificanceEvidence"),
        ("ExperientialSignificanceEvidence", "verifies_prediction", "QualiaBehaviorPrediction"),
        ("ExperientialSignificanceEvidence", "uses_outcome_receipt", "ExperienceOutcomeReceipt"),
        ("Agent", "has_experiential_significance", "ExperientialSignificance"),
        ("ExperientialSignificance", "supported_by", "ExperientialSignificanceEvidence"),
    ]
    return {"id": "experiential_significance", "version": "1.0.0",
            "depends_on": ["qualia_behavior"], "self_load_only": True, "area": AREA,
            "description": "P17.03 context-bound significance earned from verified consequence receipts.",
            "microtheory": {"name": AREA, "description": "Retain contextual consequence evidence and its review priority."},
            "nodes": [{"local_id": 0, "type": "ExperientialSignificancePolicy",
                       "attrs": {"name": "experiential_significance_policy", "enabled": 0.0}}],
            "edges": [{"src": {"role": "agent_root"}, "type": "has_experiential_significance_policy",
                       "tgt": {"local": 0}, "attrs": {}}],
            "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                             "src": {"type": src, "var": "src"}, "edge_type": edge,
                             "tgt": {"type": tgt, "var": "tgt"}} for src, edge, tgt in relations],
            "rules": [evidence_rule(), standing_rule(), priority_rule()]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
