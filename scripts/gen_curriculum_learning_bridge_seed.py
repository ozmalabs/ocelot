#!/usr/bin/env python3
"""Generate native requests from P15 curriculum tasks for real P20 learning."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from track_i_seed_lib import A, And, Count, Eq, L, Lt, N, Not, T  # noqa: E402

SEED_ID = "curriculum_learning_bridge"
AREA = "curriculum_learning_bridge"


def build():
    relations = [
        ("Agent", "has_curriculum_learning_bridge_policy", "CurriculumLearningBridgePolicy"),
        ("Agent", "has_process_curriculum_task", "ProcessCurriculumTask"),
        ("Agent", "has_curriculum_training_request", "CurriculumTrainingRequest"),
        ("ProcessCurriculumTask", "has_training_request", "CurriculumTrainingRequest"),
        ("CurriculumTrainingRequest", "for_curriculum_task", "ProcessCurriculumTask"),
        ("CurriculumTrainingRequest", "has_training_receipt", "TransitionObservation"),
        ("Agent", "has_transition_observation", "TransitionObservation"),
        ("Agent", "has_process_induction_hypothesis", "ProcessInductionHypothesis"),
        ("Agent", "has_process_curriculum_task", "ProcessCurriculumTask"),
        ("ProcessCurriculumTask", "has_outcome", "ProcessCurriculumOutcome"),
        ("ProcessCurriculumOutcome", "outcome_for", "ProcessCurriculumTask"),
    ]
    productions = [
        {"provenance": f"seed:{SEED_ID}:{edge}:{source}:{target}",
         "src": {"type": source, "var": "src"}, "edge_type": edge,
         "tgt": {"type": target, "var": "tgt"}}
        for source, edge, target in relations
    ]
    policy = ["agent", "has_curriculum_learning_bridge_policy", "policy"]
    rules = [
        {
            "name": "clb_issue_training_world_request_from_native_task",
            "area": AREA, "order": 1, "latency_class": "background", "batch": False,
            "comment": "Deliver an answer-free native training task to the mechanical world adapter.",
            "match": [policy, ["agent", "has_process_curriculum_task", "task"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                         Eq(A("task", "status"), L("awaiting_experience")),
                         Eq(A("task", "split"), L("training")),
                         Eq(A("task", "expected_outcome"), L("unknown")),
                         Eq(A("task", "answer_fields_absent"), L(True)),
                         Eq(Count(N("task", "has_training_request")), L(0))),
            "effects": [
                ["add_node", "request", "CurriculumTrainingRequest", {
                    "task_key": T(A("task", "task_key")),
                    "task_kind": T(A("task", "task_kind")),
                    "action_kind": T(A("task", "action_kind")),
                    "object_type": T(A("task", "object_type")),
                    "feature_key": T(A("task", "feature_key")),
                    "before_value": T(A("task", "before_value")),
                    "source_epoch": T(A("task", "source_epoch")),
                    "model_epoch": T(A("task", "model_epoch")),
                    "frame_epoch": T(A("task", "frame_epoch")),
                    "split": "training", "expected_outcome": "unknown",
                    "status": "authorized",
                }],
                ["add_edge", "agent", "has_curriculum_training_request", "request", {}],
                ["add_edge", "task", "has_training_request", "request", {}],
                ["add_edge", "request", "for_curriculum_task", "task", {}],
                ["set_attr", "task", "deadline_epoch",
                 T(A("policy", "request_deadline_epoch"))],
            ],
        },
        {
            "name": "clb_record_observed_training_outcome_after_native_learning",
            "area": AREA, "order": 2, "latency_class": "background", "batch": False,
            "comment": "Close a curriculum task only from actual receipts and a native learned hypothesis.",
            "match": [policy, ["agent", "has_process_curriculum_task", "task"],
                      ["task", "has_training_request", "request"],
                      ["request", "has_training_receipt", "first"],
                      ["request", "has_training_receipt", "second"],
                      ["agent", "has_process_induction_hypothesis", "hyp"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                         Eq(A("task", "status"), L("awaiting_experience")),
                         Eq(Count(N("task", "has_outcome")), L(0)),
                         Eq(A("request", "status"), L("executed")),
                         Eq(A("request", "split"), L("training")),
                         Eq(A("first", "status"), L("observed")),
                         Eq(A("second", "status"), L("observed")),
                         Lt(A("first", "event_id"), A("second", "event_id")),
                         Eq(A("first", "action_kind"), A("task", "action_kind")),
                         Eq(A("second", "action_kind"), A("task", "action_kind")),
                         Eq(A("hyp", "action_kind"), A("task", "action_kind")),
                         Eq(A("hyp", "object_type"), A("task", "object_type")),
                         Eq(A("hyp", "feature_key"), A("task", "feature_key")),
                         Eq(A("hyp", "status"), L("candidate"))),
            "effects": [
                ["add_node", "outcome", "ProcessCurriculumOutcome", {
                    "status": "observed", "evidence_status": "observed",
                    "assessment": "tractable_progress", "source_epoch": T(A("task", "source_epoch")),
                    "model_epoch": T(A("task", "model_epoch")),
                    "frame_epoch": T(A("task", "frame_epoch")),
                    "receipt_count": L(2), "native_hypothesis_key": T(A("hyp", "hypothesis_key")),
                    "split": "training",
                }],
                ["add_edge", "task", "has_outcome", "outcome", {}],
                ["add_edge", "outcome", "outcome_for", "task", {}],
                ["set_attr", "request", "status", "completed"],
            ],
        },
    ]
    return {
        "id": SEED_ID, "version": "1.0.0",
        "depends_on": ["process_curriculum", "target_learning", "process_induction"],
        "self_load_only": True, "area": AREA,
        "description": "P21 bridge from answer-free native training tasks to actual world receipts and P20 target learning.",
        "microtheory": {"name": AREA, "description": "Authorize training tasks and record outcomes only after native learning from observed receipts."},
        "nodes": [{"local_id": 0, "type": "CurriculumLearningBridgePolicy", "attrs": {
            "name": "curriculum_learning_bridge_policy", "enabled": 0.0,
            "request_deadline_epoch": 32.0,
        }}],
        "edges": [{"src": {"role": "agent_root"},
                    "type": "has_curriculum_learning_bridge_policy",
                    "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions, "rules": rules,
    }


if __name__ == "__main__":
    (ROOT / "seeds" / f"{SEED_ID}.json").write_text(
        json.dumps(build(), indent=2, sort_keys=False) + "\n", encoding="utf-8")
