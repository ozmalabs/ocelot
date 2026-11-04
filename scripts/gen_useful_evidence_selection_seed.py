#!/usr/bin/env python3
"""Generate P26's opt-in native useful-evidence selector."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Eq, Exists, Filter, Gt, L, Lt, N, Not, Or, Plus,
    StringConcat, Sum, T, ToJsonString,
)

SEED_ID = "useful_evidence_selection"
AREA = "useful_evidence_selection"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"


def _native_signal(signal, opportunity):
    same_context = And(
        Eq(A(signal, "status"), L("verified")),
        Eq(A(signal, "split"), L("training")),
        Eq(A(signal, "source_epoch"), A(opportunity, "source_epoch")),
        Eq(A(signal, "model_epoch"), A(opportunity, "model_epoch")),
        Eq(A(signal, "frame_epoch"), A(opportunity, "frame_epoch")),
    )
    prediction_disagreement = And(
        Eq(A(signal, "signal_kind"), L("prediction_disagreement")),
        Exists(N(signal, "derived_from_prediction"), "prediction", And(
            Eq(A("prediction", "status"), L("predicted")),
            Exists(N("prediction", "predicts_for_query"), "query", And(
                Eq(A("query", "split"), L("training")),
                Eq(A("query", "source_epoch"), A(opportunity, "source_epoch")),
                Eq(A("query", "model_epoch"), A(opportunity, "model_epoch")),
                Eq(A("query", "frame_epoch"), A(opportunity, "frame_epoch")),
            )),
        )),
        Exists(N(signal, "derived_from_counterexample"), "counterexample", And(
            Eq(A("counterexample", "status"), L("observed")),
            Exists(N("counterexample", "counterexample_transition"), "transition", And(
                Eq(A("transition", "split"), L("training")),
                Eq(A("transition", "status"), L("observed")),
                Eq(A("transition", "source_epoch"), A(opportunity, "source_epoch")),
                Eq(A("transition", "model_epoch"), A(opportunity, "model_epoch")),
                Eq(A("transition", "frame_epoch"), A(opportunity, "frame_epoch")),
                Eq(A("transition", "action_kind"), A(opportunity, "action_kind")),
                Eq(A("transition", "object_type"), A(opportunity, "object_type")),
                Eq(A("transition", "feature_key"), A(opportunity, "feature_key")),
                Eq(A("transition", "before_value"), A(opportunity, "before_value")),
                Not(Eq(A("prediction", "expected_after_value"),
                       A("transition", "after_value"))),
            )),
        )),
    )
    recurring_residual = And(
        Eq(A(signal, "signal_kind"), L("recurring_residual")),
        Exists(N(signal, "derived_from_counterexample"), "residual", And(
            Eq(A("residual", "status"), L("observed")),
            Exists(N("residual", "counterexample_transition"), "transition", And(
                Eq(A("transition", "split"), L("training")),
                Eq(A("transition", "status"), L("observed")),
                Eq(A("transition", "source_epoch"), A(opportunity, "source_epoch")),
                Eq(A("transition", "model_epoch"), A(opportunity, "model_epoch")),
                Eq(A("transition", "frame_epoch"), A(opportunity, "frame_epoch")),
                Eq(A("transition", "action_kind"), A(opportunity, "action_kind")),
                Eq(A("transition", "object_type"), A(opportunity, "object_type")),
                Eq(A("transition", "feature_key"), A(opportunity, "feature_key")),
                Eq(A("transition", "before_value"), A(opportunity, "before_value")),
                Exists(N(opportunity, "has_selection_signal"), "other_signal", And(
                    Eq(A("other_signal", "signal_kind"), L("recurring_residual")),
                    Eq(A("other_signal", "status"), L("verified")),
                    Eq(A("other_signal", "split"), L("training")),
                    Eq(A("other_signal", "source_epoch"), A(opportunity, "source_epoch")),
                    Eq(A("other_signal", "model_epoch"), A(opportunity, "model_epoch")),
                    Eq(A("other_signal", "frame_epoch"), A(opportunity, "frame_epoch")),
                    Not(Eq(A("other_signal", "signal_key"), A(signal, "signal_key"))),
                    Exists(N("other_signal", "derived_from_counterexample"),
                        "other_residual", And(
                            Eq(A("other_residual", "status"), L("observed")),
                            Not(Eq(A("other_residual", "event_id"),
                                   A("residual", "event_id"))),
                            Exists(N("other_residual", "counterexample_transition"),
                                "other_transition",
                                _opportunity_matches_transition(opportunity,
                                                                "other_transition")),
                        )),
                )),
            )),
        )),
    )
    verified_progress = And(
        Eq(A(signal, "signal_kind"), L("verified_learning_progress")),
        Exists(N(signal, "derived_from_learning_outcome"), "outcome", And(
            Eq(A("outcome", "status"), L("observed")),
            Eq(A("outcome", "source_epoch"), A(signal, "source_epoch")),
            Eq(A("outcome", "model_epoch"), A(signal, "model_epoch")),
            Eq(A("outcome", "frame_epoch"), A(signal, "frame_epoch")),
            Eq(A("outcome", "learned_state_changed"), L(True)),
            Eq(A("outcome", "behavior_changed"), L(True)),
            Not(Eq(A("outcome", "before_state_digest"),
                   A("outcome", "after_state_digest"))),
            Not(Eq(A("outcome", "before_behavior_digest"),
                   A("outcome", "after_behavior_digest"))),
            Exists(N("outcome", "based_on_target_evidence"), "receipt", And(
                Eq(A("receipt", "status"), L("observed")),
                Eq(A("receipt", "split"), L("training")),
                Eq(A("receipt", "action_authorized"), L(True)),
                Eq(A("receipt", "action_occurred"), L(True)),
                Eq(A("receipt", "event_id"), A("outcome", "event_id")),
                Eq(A("receipt", "source_epoch"), A(opportunity, "source_epoch")),
                Eq(A("receipt", "model_epoch"), A(opportunity, "model_epoch")),
                Eq(A("receipt", "frame_epoch"), A(opportunity, "frame_epoch")),
                Eq(A("receipt", "action_kind"), A(opportunity, "action_kind")),
                Eq(A("receipt", "object_type"), A(opportunity, "object_type")),
                Eq(A("receipt", "feature_key"), A(opportunity, "feature_key")),
                Eq(A("receipt", "before_value"), A(opportunity, "before_value")),
            )),
        )),
    )
    return And(same_context, Or(prediction_disagreement, recurring_residual,
                                verified_progress))


def _signals(opportunity):
    return Filter(N(opportunity, "has_selection_signal"), "signal",
                  _native_signal("signal", opportunity))


def _residual_score(opportunity):
    signal_weight = {
        "type": "IfThenElse",
        "cond": Eq(A("signal", "signal_kind"), L("prediction_disagreement")),
        "then": L(4.0),
        "other": {
            "type": "IfThenElse",
            "cond": Eq(A("signal", "signal_kind"), L("recurring_residual")),
            "then": L(2.0), "other": L(1.0),
        },
    }
    return Sum(_signals(opportunity), "signal", signal_weight)


def _already_selected(opportunity):
    return Exists(N("agent", "has_useful_evidence_selection"), "old_selection",
        And(Eq(A("old_selection", "opportunity_key"),
               A(opportunity, "opportunity_key")),
            Eq(A("old_selection", "source_epoch"),
               A(opportunity, "source_epoch"))))


def _already_signaled(opportunity, signal_key):
    return Exists(N(opportunity, "has_selection_signal"), "old_signal",
                  Eq(A("old_signal", "signal_key"), signal_key))


def _opportunity_matches_transition(opportunity, transition):
    return And(
        Eq(A(opportunity, "split"), L("training")),
        Eq(A(transition, "split"), L("training")),
        Eq(A(transition, "status"), L("observed")),
        Eq(A(opportunity, "source_epoch"), A(transition, "source_epoch")),
        Eq(A(opportunity, "model_epoch"), A(transition, "model_epoch")),
        Eq(A(opportunity, "frame_epoch"), A(transition, "frame_epoch")),
        Eq(A(opportunity, "action_kind"), A(transition, "action_kind")),
        Eq(A(opportunity, "object_type"), A(transition, "object_type")),
        Eq(A(opportunity, "feature_key"), A(transition, "feature_key")),
        Eq(A(opportunity, "before_value"), A(transition, "before_value")),
    )


def _eligible(opportunity):
    return And(
        Eq(A(opportunity, "status"), L("eligible")),
        Eq(A(opportunity, "split"), L("training")),
        Eq(A(opportunity, "expected_outcome"), L("unknown")),
        Eq(A(opportunity, "answer_fields_absent"), L(True)),
        Eq(A(opportunity, "sealed_labels_present"), L(False)),
        Not(_already_selected(opportunity)),
    )


def _ranked_before(prior, opportunity):
    residual_before = Or(
        Gt(_residual_score(prior), _residual_score(opportunity)),
        And(Eq(_residual_score(prior), _residual_score(opportunity)),
            Lt(A(prior, "opportunity_key"), A(opportunity, "opportunity_key"))),
    )
    fixed_before = Or(
        Lt(A(prior, "fixed_rank"), A(opportunity, "fixed_rank")),
        And(Eq(A(prior, "fixed_rank"), A(opportunity, "fixed_rank")),
            Lt(A(prior, "opportunity_key"), A(opportunity, "opportunity_key"))),
    )
    random_before = Or(
        Lt(A(prior, "random_rank"), A(opportunity, "random_rank")),
        And(Eq(A(prior, "random_rank"), A(opportunity, "random_rank")),
            Lt(A(prior, "opportunity_key"), A(opportunity, "opportunity_key"))),
    )
    return Or(
        And(Eq(A("policy", "selector_mode"), L("residual")), residual_before),
        And(Eq(A("policy", "selector_mode"), L("fixed")), fixed_before),
        And(Eq(A("policy", "selector_mode"), L("random")), random_before),
    )


def build_seed():
    relations = [
        ("Agent", "has_useful_evidence_selection_policy", "UsefulEvidenceSelectionPolicy"),
        ("Agent", "has_useful_evidence_opportunity", "UsefulEvidenceOpportunity"),
        ("Agent", "has_useful_evidence_selection", "UsefulEvidenceSelection"),
        ("UsefulEvidenceOpportunity", "has_selection_signal", "UsefulEvidenceSignal"),
        ("UsefulEvidenceSignal", "derived_from_prediction", "ProcessPrediction"),
        ("UsefulEvidenceSignal", "derived_from_counterexample", "ProcessCounterexample"),
        ("UsefulEvidenceSignal", "derived_from_learning_outcome", "UsefulEvidenceLearningOutcome"),
        ("Agent", "has_process_prediction_query", "ProcessPredictionQuery"),
        ("Agent", "has_process_prediction", "ProcessPrediction"),
        ("ProcessPrediction", "predicts_for_query", "ProcessPredictionQuery"),
        ("ProcessPrediction", "based_on_hypothesis", "ProcessInductionHypothesis"),
        ("ProcessInductionHypothesis", "has_counterexample", "ProcessCounterexample"),
        ("Agent", "has_transition_observation", "TransitionObservation"),
        ("ProcessCounterexample", "counterexample_transition", "TransitionObservation"),
        ("UsefulEvidenceSelection", "selected_opportunity", "UsefulEvidenceOpportunity"),
        ("UsefulEvidenceOpportunity", "has_selection", "UsefulEvidenceSelection"),
        ("UsefulEvidenceSelection", "has_budget_request", "ThinkingBudgetRequest"),
        ("UsefulEvidenceSelection", "has_outcome", "UsefulEvidenceLearningOutcome"),
        ("UsefulEvidenceLearningOutcome", "outcome_for_selection", "UsefulEvidenceSelection"),
        ("UsefulEvidenceLearningOutcome", "based_on_target_evidence", "CommonTargetEvidence"),
        ("Agent", "has_useful_evidence_learning_outcome", "UsefulEvidenceLearningOutcome"),
    ]
    productions = [{
        "provenance": f"seed:{SEED_ID}:{edge}:{src}:{tgt}",
        "src": {"type": src, "var": "src"}, "edge_type": edge,
        "tgt": {"type": tgt, "var": "tgt"},
    } for src, edge, tgt in relations]
    policy = ["agent", "has_useful_evidence_selection_policy", "policy"]
    budget = ["agent", "has_thinking_budget", "budget"]
    mode = ["agent", "has_network_mode_state", "mode"]
    prior = ["agent", "has_useful_evidence_opportunity", "prior"]
    pending_selection = Exists(N("agent", "has_useful_evidence_selection"),
        "pending", Eq(A("pending", "status"), L("awaiting_receipt")))
    earlier = Exists(N("agent", "has_useful_evidence_opportunity"), "prior",
        And(Eq(A("prior", "pool_id"), A("opportunity", "pool_id")),
            _eligible("prior"), _ranked_before("prior", "opportunity")))

    task_fields = ("object_id", "object_type", "action_kind", "feature_key",
                   "before_value", "source_epoch", "model_epoch", "frame_epoch")
    selection_attrs = {field: T(A("opportunity", field)) for field in task_fields}
    selection_attrs.update({
        "opportunity_key": T(A("opportunity", "opportunity_key")),
        "pool_id": T(A("opportunity", "pool_id")),
        "selector_mode": T(A("policy", "selector_mode")),
        "split": "training", "expected_outcome": "unknown",
        "answer_fields_absent": True, "status": "awaiting_budget",
        "residual_signal_score": T(_residual_score("opportunity")),
    })
    rules = [
        {
            "name": "ues_capture_native_prediction_disagreement",
            "area": AREA, "order": 5, "latency_class": "background", "batch": False,
            "comment": "Create an epoch-bound selector signal only when a native prediction is contradicted by an observed training counterexample.",
            "match": [policy, ["agent", "has_useful_evidence_opportunity", "opportunity"],
                ["agent", "has_process_prediction", "prediction"],
                ["prediction", "predicts_for_query", "query"],
                ["prediction", "based_on_hypothesis", "hypothesis"],
                ["hypothesis", "has_counterexample", "counterexample"],
                ["counterexample", "counterexample_transition", "transition"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                Eq(A("opportunity", "status"), L("eligible")),
                Eq(A("opportunity", "expected_outcome"), L("unknown")),
                Eq(A("opportunity", "answer_fields_absent"), L(True)),
                Eq(A("opportunity", "sealed_labels_present"), L(False)),
                _opportunity_matches_transition("opportunity", "transition"),
                Eq(A("query", "status"), L("predicted")),
                Eq(A("query", "split"), L("training")),
                Eq(A("query", "source_epoch"), A("opportunity", "source_epoch")),
                Eq(A("query", "model_epoch"), A("opportunity", "model_epoch")),
                Eq(A("query", "frame_epoch"), A("opportunity", "frame_epoch")),
                Eq(A("query", "action_kind"), A("opportunity", "action_kind")),
                Eq(A("query", "object_type"), A("opportunity", "object_type")),
                Eq(A("query", "feature_key"), A("opportunity", "feature_key")),
                Eq(A("query", "before_value"), A("opportunity", "before_value")),
                Eq(A("hypothesis", "status"), L("disputed")),
                Eq(A("hypothesis", "source_epoch"), A("opportunity", "source_epoch")),
                Eq(A("hypothesis", "model_epoch"), A("opportunity", "model_epoch")),
                Eq(A("hypothesis", "frame_epoch"), A("opportunity", "frame_epoch")),
                Eq(A("counterexample", "status"), L("observed")),
                Not(Eq(A("prediction", "expected_after_value"),
                       A("transition", "after_value"))),
                Not(_already_signaled("opportunity", StringConcat(
                    L("prediction-disagreement:"), A("opportunity", "opportunity_key"),
                    L(":"), ToJsonString(A("counterexample", "event_id")))))),
            "effects": [
                ["add_node", "signal", "UsefulEvidenceSignal", {
                    "signal_kind": "prediction_disagreement", "status": "verified",
                    "split": "training", "source_epoch": T(A("opportunity", "source_epoch")),
                    "model_epoch": T(A("opportunity", "model_epoch")),
                    "frame_epoch": T(A("opportunity", "frame_epoch")),
                    "signal_key": T(StringConcat(L("prediction-disagreement:"),
                        A("opportunity", "opportunity_key"), L(":"),
                        ToJsonString(A("counterexample", "event_id")))),
                }],
                ["add_edge", "opportunity", "has_selection_signal", "signal", {}],
                ["add_edge", "signal", "derived_from_prediction", "prediction", {}],
                ["add_edge", "signal", "derived_from_counterexample", "counterexample", {}],
            ],
        },
        {
            "name": "ues_capture_recurring_native_residuals",
            "area": AREA, "order": 6, "latency_class": "background", "batch": False,
            "comment": "Recurring-residual signals require two distinct observed counterexamples in the same source/model/frame context.",
            "match": [policy, ["agent", "has_useful_evidence_opportunity", "opportunity"],
                ["agent", "has_process_induction_hypothesis", "hypothesis"],
                ["hypothesis", "has_counterexample", "counterexample"],
                ["counterexample", "counterexample_transition", "transition"],
                ["hypothesis", "has_counterexample", "other_counterexample"],
                ["other_counterexample", "counterexample_transition", "other_transition"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                Eq(A("opportunity", "status"), L("eligible")),
                Eq(A("hypothesis", "status"), L("disputed")),
                Eq(A("counterexample", "status"), L("observed")),
                Eq(A("other_counterexample", "status"), L("observed")),
                Not(Eq(A("counterexample", "event_id"),
                       A("other_counterexample", "event_id"))),
                _opportunity_matches_transition("opportunity", "transition"),
                _opportunity_matches_transition("opportunity", "other_transition"),
                Not(_already_signaled("opportunity", StringConcat(
                    L("recurring-residual:"), A("opportunity", "opportunity_key"),
                    L(":"), ToJsonString(A("counterexample", "event_id")))))),
            "effects": [
                ["add_node", "signal", "UsefulEvidenceSignal", {
                    "signal_kind": "recurring_residual", "status": "verified",
                    "split": "training", "source_epoch": T(A("opportunity", "source_epoch")),
                    "model_epoch": T(A("opportunity", "model_epoch")),
                    "frame_epoch": T(A("opportunity", "frame_epoch")),
                    "signal_key": T(StringConcat(L("recurring-residual:"),
                        A("opportunity", "opportunity_key"), L(":"),
                        ToJsonString(A("counterexample", "event_id")))),
                }],
                ["add_edge", "opportunity", "has_selection_signal", "signal", {}],
                ["add_edge", "signal", "derived_from_counterexample", "counterexample", {}],
            ],
        },
        {
            "name": "ues_capture_verified_progress_for_related_training_opportunity",
            "area": AREA, "order": 7, "latency_class": "background", "batch": False,
            "comment": "Carry only receipt-backed native-state and later-behavior changes into a same-epoch evidence opportunity.",
            "match": [policy, ["agent", "has_useful_evidence_opportunity", "opportunity"],
                ["agent", "has_useful_evidence_learning_outcome", "outcome"],
                ["outcome", "based_on_target_evidence", "receipt"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                Eq(A("opportunity", "status"), L("eligible")),
                Eq(A("outcome", "status"), L("observed")),
                Eq(A("outcome", "assessment"), L("useful_progress")),
                Eq(A("outcome", "split"), L("training")),
                Eq(A("outcome", "learned_state_changed"), L(True)),
                Eq(A("outcome", "behavior_changed"), L(True)),
                Not(Eq(A("outcome", "before_state_digest"), A("outcome", "after_state_digest"))),
                Not(Eq(A("outcome", "before_behavior_digest"), A("outcome", "after_behavior_digest"))),
                Eq(A("receipt", "status"), L("observed")),
                Eq(A("receipt", "split"), L("training")),
                Eq(A("receipt", "action_authorized"), L(True)),
                Eq(A("receipt", "action_occurred"), L(True)),
                Eq(A("receipt", "event_id"), A("outcome", "event_id")),
                Eq(A("outcome", "source_epoch"), A("opportunity", "source_epoch")),
                Eq(A("outcome", "model_epoch"), A("opportunity", "model_epoch")),
                Eq(A("outcome", "frame_epoch"), A("opportunity", "frame_epoch")),
                Eq(A("receipt", "action_kind"), A("opportunity", "action_kind")),
                Eq(A("receipt", "object_type"), A("opportunity", "object_type")),
                Eq(A("receipt", "feature_key"), A("opportunity", "feature_key")),
                Eq(A("receipt", "before_value"), A("opportunity", "before_value")),
                Not(_already_signaled("opportunity", StringConcat(
                    L("verified-progress:"), A("opportunity", "opportunity_key"),
                    L(":"), ToJsonString(A("outcome", "event_id")))))),
            "effects": [
                ["add_node", "signal", "UsefulEvidenceSignal", {
                    "signal_kind": "verified_learning_progress", "status": "verified",
                    "split": "training", "source_epoch": T(A("opportunity", "source_epoch")),
                    "model_epoch": T(A("opportunity", "model_epoch")),
                    "frame_epoch": T(A("opportunity", "frame_epoch")),
                    "signal_key": T(StringConcat(L("verified-progress:"),
                        A("opportunity", "opportunity_key"), L(":"),
                        ToJsonString(A("outcome", "event_id")))),
                }],
                ["add_edge", "opportunity", "has_selection_signal", "signal", {}],
                ["add_edge", "signal", "derived_from_learning_outcome", "outcome", {}],
            ],
        },
        {
            "name": "ues_reopen_opportunity_after_native_epoch_change",
            "area": AREA, "order": 1, "latency_class": "background", "batch": False,
            "comment": "A terminal evidence key is reconsidered only after its source, model, or frame epoch changes.",
            "match": [policy, ["agent", "has_useful_evidence_opportunity", "opportunity"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                Or(Eq(A("opportunity", "status"), L("terminal_no_progress")),
                   Eq(A("opportunity", "status"), L("resolved"))),
                Or(Not(Eq(A("opportunity", "source_epoch"),
                          A("opportunity", "terminal_source_epoch"))),
                   Not(Eq(A("opportunity", "model_epoch"),
                          A("opportunity", "terminal_model_epoch"))),
                   Not(Eq(A("opportunity", "frame_epoch"),
                          A("opportunity", "terminal_frame_epoch"))))),
            "effects": [["set_attr", "opportunity", "status", "eligible"]],
        },
        {
            "name": "ues_request_shared_budget_for_top_training_opportunity",
            "area": AREA, "order": 10, "latency_class": "background", "batch": False,
            "comment": "Select one answer-free opportunity natively and fund selection work from the common ThinkingBudget.",
            "match": [policy, mode, budget,
                ["agent", "has_useful_evidence_opportunity", "opportunity"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                Or(Eq(A("policy", "selector_mode"), L("residual")),
                   Eq(A("policy", "selector_mode"), L("fixed")),
                   Eq(A("policy", "selector_mode"), L("random"))),
                Eq(A("policy", "scheduler_status"), L("ready")),
                Eq(A("budget", "enabled"), L(1.0)),
                Eq(A("opportunity", "pool_id"), A("policy", "pool_id")),
                _eligible("opportunity"), Not(earlier), Not(pending_selection),
                Lt(Count(N("agent", "has_useful_evidence_selection")),
                   A("policy", "max_selections"))),
            "effects": [
                ["add_node", "selection", "UsefulEvidenceSelection", selection_attrs],
                ["add_edge", "agent", "has_useful_evidence_selection", "selection", {}],
                ["add_edge", "selection", "selected_opportunity", "opportunity", {}],
                ["add_edge", "opportunity", "has_selection", "selection", {}],
                ["add_node", "request", "ThinkingBudgetRequest", {
                    "requester_kind": "useful_evidence_selection",
                    "requester_key": T(A("opportunity", "opportunity_key")),
                    "source_key": T(A("opportunity", "opportunity_key")),
                    "source_epoch": T(A("opportunity", "source_epoch")),
                    "requested_epoch": T(A("mode", "epoch")),
                    "deadline_epoch": T(Plus(A("mode", "epoch"), L(1.0))),
                    "cost": T(A("policy", "selection_cost")), "status": "pending",
                }],
                ["add_edge", "agent", "has_thinking_budget_request", "request", {}],
                ["add_edge", "request", "draws_on_thinking_budget", "budget", {}],
                ["add_edge", "selection", "has_budget_request", "request", {}],
                ["set_attr", "policy", "scheduler_status", "funding_pending"],
            ],
        },
        {
            "name": "ues_emit_selected_opportunity_after_budget_approval",
            "area": AREA, "order": 20, "latency_class": "background", "batch": False,
            "comment": "Only a budget-approved selection is exposed to the mechanical training-world adapter.",
            "match": [policy,
                ["agent", "has_useful_evidence_selection", "selection"],
                ["selection", "selected_opportunity", "opportunity"],
                ["selection", "has_budget_request", "request"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                Eq(A("policy", "scheduler_status"), L("funding_pending")),
                Eq(A("selection", "status"), L("awaiting_budget")),
                Eq(A("request", "status"), L("approved"))),
            "effects": [["set_attr", "selection", "status", "awaiting_receipt"],
                ["set_attr", "opportunity", "status", "selected"],
                ["set_attr", "policy", "scheduler_status", "awaiting_outcome"]],
        },
        {
            "name": "ues_suppress_denied_opportunity_without_retry",
            "area": AREA, "order": 21, "latency_class": "background", "batch": False,
            "comment": "A budget-denied opportunity remains visible but is not retried at the same evidence epoch.",
            "match": [policy,
                ["agent", "has_useful_evidence_selection", "selection"],
                ["selection", "selected_opportunity", "opportunity"],
                ["selection", "has_budget_request", "request"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                Eq(A("policy", "scheduler_status"), L("funding_pending")),
                Eq(A("selection", "status"), L("awaiting_budget")),
                Eq(A("request", "status"), L("denied"))),
            "effects": [["set_attr", "selection", "status", "denied"],
                ["set_attr", "opportunity", "status", "terminal_no_budget"],
                ["set_attr", "policy", "scheduler_status", "ready"]],
        },
    ]
    for progressed, outcome_status, opp_status, selection_status in (
        (True, "useful_progress", "resolved", "completed_with_progress"),
        (False, "no_progress", "terminal_no_progress", "terminal_no_progress"),
    ):
        condition = And(
            Eq(A("outcome", "status"), L("observed")),
            (And(Eq(A("outcome", "learned_state_changed"), L(True)),
                 Eq(A("outcome", "behavior_changed"), L(True)))
             if progressed else Not(And(
                 Eq(A("outcome", "learned_state_changed"), L(True)),
                 Eq(A("outcome", "behavior_changed"), L(True))))),
        )
        rules.append({
            "name": f"ues_close_selection_{outcome_status}_from_receipt_and_behavior",
            "area": AREA, "order": 30 if progressed else 31,
            "latency_class": "background", "batch": False,
            "comment": "Close an evidence attempt only from a same-epoch actual target receipt and measured learner/behavior outcomes.",
            "match": [policy,
                ["agent", "has_useful_evidence_selection", "selection"],
                ["selection", "selected_opportunity", "opportunity"],
                ["selection", "has_outcome", "outcome"],
                ["outcome", "based_on_target_evidence", "receipt"]],
            "where": And(Eq(A("policy", "enabled"), L(1.0)),
                Eq(A("policy", "scheduler_status"), L("awaiting_outcome")),
                Eq(A("selection", "status"), L("awaiting_receipt")),
                Eq(A("receipt", "status"), L("observed")),
                Eq(A("receipt", "split"), L("training")),
                Eq(A("receipt", "action_authorized"), L(True)),
                Eq(A("receipt", "action_occurred"), L(True)),
                Eq(A("receipt", "event_id"), A("outcome", "event_id")),
                Eq(A("receipt", "object_id"), A("selection", "object_id")),
                Eq(A("receipt", "object_type"), A("selection", "object_type")),
                Eq(A("receipt", "action_kind"), A("selection", "action_kind")),
                Eq(A("receipt", "feature_key"), A("selection", "feature_key")),
                Eq(A("receipt", "before_value"), A("selection", "before_value")),
                Eq(A("outcome", "source_epoch"), A("selection", "source_epoch")),
                Eq(A("outcome", "model_epoch"), A("selection", "model_epoch")),
                Eq(A("outcome", "frame_epoch"), A("selection", "frame_epoch")),
                Eq(A("opportunity", "source_epoch"), A("selection", "source_epoch")),
                Eq(A("opportunity", "model_epoch"), A("selection", "model_epoch")),
                Eq(A("opportunity", "frame_epoch"), A("selection", "frame_epoch")),
                condition,
                Eq(A("outcome", "assessment"), L(outcome_status)),
                *([Not(Eq(A("outcome", "before_state_digest"),
                          A("outcome", "after_state_digest"))),
                Not(Eq(A("outcome", "before_behavior_digest"),
                       A("outcome", "after_behavior_digest")))] if progressed else [])),
            "effects": [["set_attr", "selection", "status", selection_status],
                ["set_attr", "opportunity", "status", opp_status],
                ["set_attr", "opportunity", "terminal_source_epoch", T(A("selection", "source_epoch"))],
                ["set_attr", "opportunity", "terminal_model_epoch", T(A("selection", "model_epoch"))],
                ["set_attr", "opportunity", "terminal_frame_epoch", T(A("selection", "frame_epoch"))],
                ["set_attr", "policy", "scheduler_status", "ready"]],
        })
    return {
        "id": SEED_ID, "version": "1.0.0",
        "depends_on": ["thinking_budget", "process_induction", "target_learning",
                       "common_target_evidence", "learning_memory_budget"],
        "self_load_only": True, "area": AREA,
        "description": "P26 opt-in native ranking and budgeted delivery of shared-pool training evidence.",
        "microtheory": {"name": AREA,
            "description": "Rank only epoch-valid native learning signals, issue one budgeted answer-free training opportunity, and close it from actual receipt plus later behavior."},
        "nodes": [{"local_id": 0, "type": "UsefulEvidenceSelectionPolicy", "attrs": {
            "name": "useful_evidence_selection_policy", "enabled": 0.0,
            "selector_mode": "residual", "scheduler_status": "ready",
            "pool_id": "", "selection_cost": 1.0, "max_selections": 256.0,
        }}],
        "edges": [{"src": {"role": "agent_root"},
            "type": "has_useful_evidence_selection_policy", "tgt": {"local": 0},
            "attrs": {}}],
        "productions": productions, "rules": rules,
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(OUT)
