#!/usr/bin/env python3
"""Generate retained-counterexample, retirement and context-split rules."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "qualia_revision.json"
AREA = "qualia_revision"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(t): return {"__term__": t}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}
def Json(x): return {"type": "ToJsonString", "value": x}


def counterexample_rule():
    key = Concat(A("pred", "prediction_key"), L(":"), A("receipt", "receipt_id"))
    duplicate = Exists(N("ag", "has_qualia_counterexample"), "old",
                       Eq(A("old", "counterexample_key"), key))
    attrs = {"counterexample_key": T(key), "owner_id": T(A("pred", "owner_id")),
             "episode_id": T(A("pred", "episode_id")), "event_id": T(A("pred", "event_id")),
             "context_id": T(A("ep", "context_id")), "feature_key": T(A("pred", "feature_key")),
             "feature_value": T(A("pred", "feature_value")),
             "dimension_id": T(A("pred", "dimension_id")),
             "predicted_consequence": T(A("pred", "predicted_consequence")),
             "observed_consequence": T(A("receipt", "consequence_value")),
             "receipt_id": T(A("receipt", "receipt_id")),
             "source_epoch": T(A("receipt", "source_epoch")),
             "model_epoch": T(A("receipt", "model_epoch")),
             "frame_epoch": T(A("receipt", "frame_epoch")), "status": "verified"}
    return {"name": "qr_retire_axis_on_verified_prediction_counterexample", "area": AREA,
            "order": 1, "latency_class": "background", "batch": False,
            "match": [["ag", "has_qualia_revision_policy", "pol"],
                      ["ag", "has_qualia_behavior_prediction", "pred"],
                      ["pred", "uses_feature_observation", "feature"],
                      ["pred", "uses_qualia_dimension", "dim"],
                      ["feature", "has_outcome_receipt", "receipt"],
                      ["ag", "has_experience_episode", "ep"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Or(Eq(A("pred", "status"), L("proposed")),
                            Eq(A("pred", "status"), L("verified"))),
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
                         Not(Eq(A("pred", "predicted_consequence"), A("receipt", "consequence_value"))),
                         Not(duplicate)),
            "effects": [["add_node", "ce", "QualiaCounterexample", attrs],
                        ["add_edge", "ag", "has_qualia_counterexample", "ce", {}],
                        ["add_edge", "ce", "contradicts_prediction", "pred", {}],
                        ["add_edge", "ce", "uses_outcome_receipt", "receipt", {}],
                        ["add_edge", "ce", "retires_dimension", "dim", {}],
                        ["set_attr", "dim", "acquisition_status", "retired"],
                        ["set_attr", "pred", "status", "contradicted"]]}


def split_rule():
    key = Concat(A("c11", "owner_id"), L(":"), A("c11", "feature_key"), L(":"),
                 Json(A("c11", "feature_value")), L(":"), A("c11", "context_id"), L(":"),
                 A("c12", "context_id"), L(":"), Json(A("c11", "observed_consequence")), L(":"),
                 Json(A("c21", "observed_consequence")))
    duplicate = Exists(N("ag", "has_qualia_context_split"), "old",
                       Eq(A("old", "split_key"), key))
    same_context = And(Eq(A("c11", "context_id"), A("c12", "context_id")),
                       Eq(A("c21", "context_id"), A("c22", "context_id")),
                       Not(Eq(A("c11", "context_id"), A("c21", "context_id"))))
    # Build explicit pair identity and within-context repeatability constraints.
    where = And(Eq(A("pol", "enabled"), L(1.0)),
                *[Eq(A("c11", k), A("c12", k)) for k in
                  ("owner_id", "feature_key", "feature_value", "observed_consequence", "dimension_id")],
                *[Eq(A("c21", k), A("c22", k)) for k in
                  ("owner_id", "feature_key", "feature_value", "observed_consequence", "dimension_id")],
                *[Eq(A("c11", k), A("c21", k)) for k in
                  ("owner_id", "feature_key", "feature_value", "dimension_id")],
                same_context, Not(Eq(A("c11", "observed_consequence"), A("c21", "observed_consequence"))),
                Lt(A("c11", "episode_id"), A("c12", "episode_id")),
                Lt(A("c21", "episode_id"), A("c22", "episode_id")),
                Lt(A("c11", "context_id"), A("c21", "context_id")),
                Not(Eq(A("c11", "episode_id"), A("c12", "episode_id"))),
                Not(Eq(A("c21", "episode_id"), A("c22", "episode_id"))),
                *[Eq(A(c, "status"), L("verified")) for c in ("c11", "c12", "c21", "c22")],
                Not(duplicate))
    attrs = {"split_key": T(key), "owner_id": T(A("c11", "owner_id")),
             "feature_key": T(A("c11", "feature_key")),
             "feature_value": T(A("c11", "feature_value")),
             "dimension_id": T(A("c11", "dimension_id")),
             "context_a": T(A("c11", "context_id")),
             "context_b": T(A("c21", "context_id")),
             "consequence_a": T(A("c11", "observed_consequence")),
             "consequence_b": T(A("c21", "observed_consequence")),
             "evidence_count": 4.0, "status": "proposed", "verified": True}
    return {"name": "qr_propose_context_split_from_repeated_verified_consequences", "area": AREA,
            "order": 10, "latency_class": "background", "batch": False,
            "match": [["ag", "has_qualia_revision_policy", "pol"],
                      ["ag", "has_qualia_counterexample", "c11"],
                      ["ag", "has_qualia_counterexample", "c12"],
                      ["ag", "has_qualia_counterexample", "c21"],
                      ["ag", "has_qualia_counterexample", "c22"]],
            "where": where,
            "effects": [["add_node", "split", "QualiaContextSplit", attrs],
                        ["add_edge", "ag", "has_qualia_context_split", "split", {}],
                        ["add_edge", "split", "supported_by", "c11", {}],
                        ["add_edge", "split", "supported_by", "c12", {}],
                        ["add_edge", "split", "supported_by", "c21", {}],
                        ["add_edge", "split", "supported_by", "c22", {}]]}


def terminal_retirement_rule():
    return {"name": "qr_reassert_terminal_retirement_after_acquisition_updates", "area": AREA,
            "order": 50, "latency_class": "hard_realtime", "batch": False,
            "match": [["ag", "has_qualia_revision_policy", "pol"],
                      ["ag", "has_qualia_axis_candidate", "candidate"],
                      ["ag", "has_qualia_dimension", "dim"],
                      ["ag", "has_qualia_counterexample", "ce"],
                      ["ce", "retires_dimension", "dim"]],
            "where": And(Eq(A("pol", "enabled"), L(1.0)),
                         Eq(A("candidate", "dimension_id"), A("dim", "name")),
                         Eq(A("ce", "dimension_id"), A("dim", "name")),
                         Not(Eq(A("dim", "acquisition_status"), L("retired"))),
                         Not(Eq(A("candidate", "status"), L("retired")))),
            "effects": [["set_attr", "candidate", "status", "retired"],
                        ["set_attr", "dim", "acquisition_status", "retired"]]}


def build_seed():
    relations = [
        ("Agent", "has_qualia_revision_policy", "QualiaRevisionPolicy"),
        ("Agent", "has_qualia_behavior_prediction", "QualiaBehaviorPrediction"),
        ("QualiaBehaviorPrediction", "uses_feature_observation", "ExperienceFeatureObservation"),
        ("QualiaBehaviorPrediction", "uses_qualia_dimension", "QualiaDimension"),
        ("ExperienceFeatureObservation", "has_outcome_receipt", "ExperienceOutcomeReceipt"),
        ("Agent", "has_experience_episode", "ExperienceEpisode"),
        ("Agent", "has_qualia_counterexample", "QualiaCounterexample"),
        ("QualiaCounterexample", "contradicts_prediction", "QualiaBehaviorPrediction"),
        ("QualiaCounterexample", "uses_outcome_receipt", "ExperienceOutcomeReceipt"),
        ("QualiaCounterexample", "retires_dimension", "QualiaDimension"),
        ("Agent", "has_qualia_context_split", "QualiaContextSplit"),
        ("QualiaContextSplit", "supported_by", "QualiaCounterexample"),
    ]
    return {"id": "qualia_revision", "version": "1.0.0",
            "depends_on": ["qualia_behavior", "experiential_significance"],
            "self_load_only": True, "area": AREA,
            "description": "P17.04 preserve counterexamples, retire contradicted influence, and propose verified context splits.",
            "microtheory": {"name": AREA, "description": "Revise acquired axes only when source-bound outcomes demand it."},
            "nodes": [{"local_id": 0, "type": "QualiaRevisionPolicy",
                       "attrs": {"name": "qualia_revision_policy", "enabled": 0.0}}],
            "edges": [{"src": {"role": "agent_root"}, "type": "has_qualia_revision_policy",
                       "tgt": {"local": 0}, "attrs": {}}],
            "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                             "src": {"type": src, "var": "src"}, "edge_type": edge,
                             "tgt": {"type": tgt, "var": "tgt"}} for src, edge, tgt in relations],
            "rules": [counterexample_rule(), split_rule(), terminal_retirement_rule()]}


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUT)


if __name__ == "__main__": main()
