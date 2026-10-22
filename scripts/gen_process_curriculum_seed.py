#!/usr/bin/env python3
"""Generate P15 graph rules that turn verified residuals into funded training tasks."""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from track_i_seed_lib import (  # noqa: E402
    A, And, Count, Eq, Exists, Filter, Gt, L, Lt, N, NodesWhere, Not, Or, Plus,
    StringConcat, T, V,
)

SEED_ID = "process_curriculum"
OUT = ROOT / "seeds" / f"{SEED_ID}.json"
AREA = "process_curriculum"


def _prior(key):
    return Exists(N("agent", "has_process_curriculum_evidence"), "old",
                 Eq(A("old", "evidence_key"), key))


def _evidence_attrs(key, kind, source, task_kind, source_epoch, model_epoch, frame_epoch,
                    task_fields):
    return {
        "evidence_key": T(key), "source_kind": kind,
        "source_id": T(source), "task_kind": task_kind,
        "source_epoch": T(source_epoch), "model_epoch": T(model_epoch),
        "frame_epoch": T(frame_epoch), "status": "eligible",
        "split": "training", "expected_outcome": "unknown",
        "sealed_labels_present": False,
        "fixed_rank": task_fields.get("fixed_rank", 0.0),
        "random_rank": task_fields.get("random_rank", 0.0),
        **task_fields,
    }


def build():
    rels = [
        ("Agent", "has_process_curriculum_policy", "ProcessCurriculumPolicy"),
        ("Agent", "has_process_curriculum_evidence", "ProcessCurriculumEvidence"),
        ("Agent", "has_process_curriculum_request", "ThinkingBudgetRequest"),
        ("Agent", "has_process_curriculum_task", "ProcessCurriculumTask"),
        ("Agent", "has_process_induction_hypothesis", "ProcessInductionHypothesis"),
        ("ProcessInductionHypothesis", "has_counterexample", "ProcessCounterexample"),
        ("ProcessCounterexample", "counterexample_transition", "TransitionObservation"),
        ("Agent", "has_representation_search_request", "RepresentationSearchRequest"),
        ("RepresentationSearchRequest", "has_candidate_proposal", "RepresentationProposal"),
        ("RepresentationProposal", "has_development_validation", "RepresentationDevelopmentValidation"),
        ("Agent", "has_qualia_axis_candidate", "QualiaAxisCandidate"),
        ("QualiaAxisCandidate", "has_acquisition_validation", "QualiaAcquisitionValidation"),
        ("Agent", "has_strategy_library_entry", "StrategyLibraryEntry"),
        ("StrategyLibraryEntry", "about_domain", "ProcessDomain"),
        ("Agent", "has_solve_task", "SolveTask"),
        ("SolveTask", "about_domain", "ProcessDomain"),
        ("ProcessCurriculumEvidence", "derived_from_counterexample", "ProcessCounterexample"),
        ("ProcessCurriculumEvidence", "derived_from_representation", "RepresentationProposal"),
        ("ProcessCurriculumEvidence", "derived_from_qualia_candidate", "QualiaAxisCandidate"),
        ("ProcessCurriculumEvidence", "derived_from_stale_strategy", "StrategyLibraryEntry"),
        ("ProcessCurriculumEvidence", "for_fresh_solve_task", "SolveTask"),
        ("ProcessCurriculumEvidence", "funded_by", "ThinkingBudgetRequest"),
        ("ProcessCurriculumTask", "from_evidence", "ProcessCurriculumEvidence"),
        ("ProcessCurriculumTask", "has_outcome", "ProcessCurriculumOutcome"),
        ("ProcessCurriculumOutcome", "outcome_for", "ProcessCurriculumTask"),
    ]
    productions = [
        {"provenance": f"seed:{SEED_ID}:{edge}:{src}:{dst}",
         "src": {"type": src, "var": "src"}, "edge_type": edge,
         "tgt": {"type": dst, "var": "tgt"}}
        for src, edge, dst in rels
    ]
    policy = ["agent", "has_process_curriculum_policy", "policy"]
    mode = ["agent", "has_network_mode_state", "mode"]
    budget = ["agent", "has_thinking_budget", "budget"]
    rules = []

    counterexample_sources = Filter(
        N("agent", "has_process_induction_hypothesis"), "candidate_hyp",
        And(Eq(A("candidate_hyp", "status"), L("disputed")),
            Eq(A("candidate_hyp", "owner_id"), A("hyp", "owner_id")),
            Eq(A("candidate_hyp", "source_epoch"), A("hyp", "source_epoch"))),
    )
    first_counterexample = {
        "type": "ArgminUnique", "source": counterexample_sources,
        "var_name": "candidate_hyp", "value": A("candidate_hyp", "source_epoch"),
        "default": None,
    }

    # Verified process counterexamples propose a fresh discrimination task,
    # without copying the observed answer into the agent-visible curriculum.
    key = StringConcat(L("counterexample:"), A("ce", "event_id"), L(":"), A("hyp", "source_epoch"))
    rules.append({
        "name": "pc_capture_observed_process_counterexample_residual", "area": AREA,
        "order": 1, "latency_class": "background", "batch": False,
        "comment": "A source- and epoch-bound observed counterexample creates a training task with the answer withheld.",
        "match": [policy, ["agent", "has_process_induction_hypothesis", "hyp"],
                  ["hyp", "has_counterexample", "ce"], ["ce", "counterexample_transition", "obs"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("hyp", "status"), L("disputed")),
                     Eq(A("ce", "status"), L("observed")),
                     Eq(A("obs", "split"), L("training")),
                     Eq(A("hyp", "owner_id"), A("obs", "owner_id")),
                     Eq(A("hyp", "source_epoch"), A("obs", "source_epoch")),
                     Eq(A("hyp", "model_epoch"), A("obs", "model_epoch")),
                     Eq(A("hyp", "frame_epoch"), A("obs", "frame_epoch")),
                     Eq(V("hyp"), first_counterexample),
                     Lt(Count(N("agent", "has_process_curriculum_evidence")), A("policy", "max_evidence")),
                     Not(_prior(key))),
        "effects": [
            ["add_node", "evidence", "ProcessCurriculumEvidence", _evidence_attrs(
                key, "verified_counterexample", A("ce", "event_id"),
                "counterexample_discrimination", A("obs", "source_epoch"),
                A("obs", "model_epoch"), A("obs", "frame_epoch"), {
                    "owner_id": T(A("obs", "owner_id")),
                    "action_kind": T(A("obs", "action_kind")),
                    "object_type": T(A("obs", "object_type")),
                    "feature_key": T(A("obs", "feature_key")),
                    "before_value": T(A("obs", "before_value")),
                    "observed_after_value": None,
                })],
            ["add_edge", "agent", "has_process_curriculum_evidence", "evidence", {}],
            ["add_edge", "evidence", "derived_from_counterexample", "ce", {}],
            ["set_attr", "ce", "status", "curriculum_captured"],
        ],
    })

    key = StringConcat(L("representation:"), A("proposal", "candidate_id"), L(":"),
                       A("validation", "training_split_id"))
    rules.append({
        "name": "pc_capture_frozen_training_representation_residual", "area": AREA,
        "order": 2, "latency_class": "background", "batch": False,
        "comment": "Only verified frozen-training residual bits can seed representation curriculum; held-out outcomes are not copied.",
        "match": [policy, ["agent", "has_representation_search_request", "request"],
                  ["request", "has_candidate_proposal", "proposal"],
                  ["proposal", "has_development_validation", "validation"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("proposal", "status"), L("verified_candidate")),
                     Eq(A("validation", "status"), L("scored_frozen_training")),
                     Eq(A("validation", "candidate_id"), A("proposal", "candidate_id")),
                     Eq(A("validation", "heldout_used"), L(False)),
                     Gt(A("validation", "residual_bits"), L(0.0)),
                     Lt(Count(N("agent", "has_process_curriculum_evidence")), A("policy", "max_evidence")),
                     Not(_prior(key))),
        "effects": [
            ["add_node", "evidence", "ProcessCurriculumEvidence", _evidence_attrs(
                key, "verified_training_residual", A("proposal", "candidate_id"),
                "representation_residual", A("proposal", "source_epoch"),
                A("proposal", "model_epoch"), A("proposal", "frame_epoch"), {
                    "candidate_id": T(A("proposal", "candidate_id")),
                    "source_frame_id": T(A("proposal", "source_frame_id")),
                    "target_frame_id": T(A("proposal", "target_frame_id")),
                    "residual_bits": T(A("validation", "residual_bits")),
                    "training_split_id": T(A("validation", "training_split_id")),
                })],
            ["add_edge", "agent", "has_process_curriculum_evidence", "evidence", {}],
            ["add_edge", "evidence", "derived_from_representation", "proposal", {}],
        ],
    })

    key = StringConcat(L("qualia:"), A("candidate", "candidate_key"), L(":"),
                       A("candidate", "model_epoch"), L(":"), A("candidate", "frame_epoch"))
    rules.append({
        "name": "pc_capture_contested_acquired_distinction", "area": AREA,
        "order": 3, "latency_class": "background", "batch": False,
        "comment": "Contested acquired dimensions generate fresh evidence tasks scoped to the exact owner and model/frame epochs.",
        "match": [policy, ["agent", "has_qualia_axis_candidate", "candidate"],
                  ["candidate", "has_acquisition_validation", "validation"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("candidate", "status"), L("contested")),
                     Eq(A("validation", "result"), L("negative")),
                     Eq(A("validation", "revision_round"), A("candidate", "revision_count")),
                     Lt(Count(N("agent", "has_process_curriculum_evidence")), A("policy", "max_evidence")),
                     Not(_prior(key))),
        "effects": [
            ["add_node", "evidence", "ProcessCurriculumEvidence", _evidence_attrs(
                key, "contested_acquired_distinction", A("candidate", "candidate_key"),
                "qualia_reacquisition", A("validation", "source_epoch"),
                A("candidate", "model_epoch"), A("candidate", "frame_epoch"), {
                    "owner_id": T(A("candidate", "owner_id")),
                    "feature_key": T(A("candidate", "feature_key")),
                    "feature_family": T(A("candidate", "feature_family")),
                })],
            ["add_edge", "agent", "has_process_curriculum_evidence", "evidence", {}],
            ["add_edge", "evidence", "derived_from_qualia_candidate", "candidate", {}],
        ],
    })

    key = StringConcat(L("stale-strategy:"), A("entry", "source_task"), L(":"), A("task", "task_id"))
    rules.append({
        "name": "pc_schedule_stale_strategy_on_fresh_matching_task", "area": AREA,
        "order": 4, "latency_class": "background", "batch": False,
        "comment": "Recheck an old success only on a new active task with matching structure and the current domain epochs.",
        "match": [policy, ["agent", "has_strategy_library_entry", "entry"],
                  ["entry", "about_domain", "domain"], ["agent", "has_solve_task", "task"],
                  ["task", "about_domain", "domain"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("entry", "status"), L("stale")),
                     Or(Eq(A("task", "status"), L("active")),
                        And(Eq(A("task", "status"), L("stuck")),
                            Eq(A("task", "steps"), L(0)))),
                     Eq(A("task", "split"), L("training")),
                     Eq(A("entry", "kind"), A("domain", "kind")),
                     Eq(A("entry", "state_size"), Count(A("task", "initial_state"))),
                     Eq(A("entry", "goal_size"), Count(A("task", "goal"))),
                     Eq(A("task", "source_epoch"), A("domain", "source_epoch")),
                     Eq(A("task", "model_epoch"), A("domain", "model_epoch")),
                     Eq(A("task", "frame_epoch"), A("domain", "frame_epoch")),
                     Lt(Count(N("agent", "has_process_curriculum_evidence")), A("policy", "max_evidence")),
                     Not(_prior(key))),
        "effects": [
            ["add_node", "evidence", "ProcessCurriculumEvidence", _evidence_attrs(
                key, "stale_strategy_success", A("entry", "source_task"),
                "stale_strategy_recheck", A("domain", "source_epoch"),
                A("domain", "model_epoch"), A("domain", "frame_epoch"), {
                    "domain": T(A("domain", "name")),
                    "initial_state": T(A("task", "initial_state")),
                    "goal": T(A("task", "goal")),
                    "strategy_source_task": T(A("entry", "source_task")),
                })],
            ["add_edge", "agent", "has_process_curriculum_evidence", "evidence", {}],
            ["add_edge", "evidence", "derived_from_stale_strategy", "entry", {}],
            ["add_edge", "evidence", "for_fresh_solve_task", "task", {}],
        ],
    })

    # One active funding token serializes curriculum admission. Work remains
    # graph-owned; outcomes only arrive through typed experience records.
    residual_before = Lt(A("prior", "evidence_key"), A("evidence", "evidence_key"))
    fixed_before = Or(
        Lt(A("prior", "fixed_rank"), A("evidence", "fixed_rank")),
        And(Eq(A("prior", "fixed_rank"), A("evidence", "fixed_rank")), residual_before),
    )
    random_before = Or(
        Lt(A("prior", "random_rank"), A("evidence", "random_rank")),
        And(Eq(A("prior", "random_rank"), A("evidence", "random_rank")), residual_before),
    )
    selected_before = Or(
        And(Eq(A("policy", "selector_mode"), L("residual")), residual_before),
        And(Eq(A("policy", "selector_mode"), L("fixed")), fixed_before),
        And(Eq(A("policy", "selector_mode"), L("random")), random_before),
    )
    earlier = Exists(N("agent", "has_process_curriculum_evidence"), "prior",
                     And(Eq(A("prior", "status"), L("eligible")), selected_before))
    rules.append({
        "name": "pc_fund_one_ranked_training_residual", "area": AREA,
        "order": 10, "latency_class": "background", "batch": False,
        "comment": "Fund one verified training residual at a time using the configured native selector and shared ThinkingBudget.",
        "match": [policy, mode, budget, ["agent", "has_process_curriculum_evidence", "evidence"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Or(Eq(A("policy", "selector_mode"), L("residual")),
                        Eq(A("policy", "selector_mode"), L("fixed")),
                        Eq(A("policy", "selector_mode"), L("random"))),
                     Eq(A("policy", "scheduler_status"), L("ready")),
                     Eq(A("budget", "enabled"), L(1.0)),
                     Eq(A("evidence", "status"), L("eligible")),
                     Lt(Count(N("agent", "has_process_curriculum_task")), A("policy", "max_tasks")),
                     Not(earlier)),
        "effects": [
            ["add_node", "request", "ThinkingBudgetRequest", {
                "requester_kind": "process_curriculum",
                "requester_key": T(A("evidence", "evidence_key")),
                "source_key": T(A("evidence", "evidence_key")),
                "source_epoch": T(A("evidence", "source_epoch")),
                "requested_epoch": T(A("mode", "epoch")),
                "deadline_epoch": T(Plus(A("mode", "epoch"), L(1))),
                "cost": T(A("policy", "task_cost")), "status": "pending",
            }],
            ["add_edge", "agent", "has_process_curriculum_request", "request", {}],
            ["add_edge", "evidence", "funded_by", "request", {}],
            ["add_edge", "request", "draws_on_thinking_budget", "budget", {}],
            ["set_attr", "evidence", "status", "funding_pending"],
            ["set_attr", "policy", "scheduler_status", "funding_pending"],
        ],
    })
    rules.append({
        "name": "pc_emit_training_task_only_after_budget_approval", "area": AREA,
        "order": 20, "latency_class": "background", "batch": False,
        "comment": "Emit only a training-split task after approval and omit answers, held-out identifiers and labels.",
        "match": [policy, mode, ["agent", "has_process_curriculum_evidence", "evidence"],
                  ["evidence", "funded_by", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("policy", "scheduler_status"), L("funding_pending")),
                     Eq(A("evidence", "status"), L("funding_pending")),
                     Eq(A("request", "status"), L("approved")),
                     Lt(Count(N("agent", "has_process_curriculum_task")), A("policy", "max_tasks"))),
        "effects": [
            ["add_node", "task", "ProcessCurriculumTask", {
                "task_key": T(A("evidence", "evidence_key")),
                "task_kind": T(A("evidence", "task_kind")),
                "source_kind": T(A("evidence", "source_kind")),
                "source_id": T(A("evidence", "source_id")),
                "action_kind": T(A("evidence", "action_kind")),
                "object_type": T(A("evidence", "object_type")),
                "feature_key": T(A("evidence", "feature_key")),
                "before_value": T(A("evidence", "before_value")),
                "candidate_id": T(A("evidence", "candidate_id")),
                "source_frame_id": T(A("evidence", "source_frame_id")),
                "target_frame_id": T(A("evidence", "target_frame_id")),
                "training_residual_bits": T(A("evidence", "residual_bits")),
                "feature_family": T(A("evidence", "feature_family")),
                "domain": T(A("evidence", "domain")),
                "initial_state": T(A("evidence", "initial_state")),
                "goal": T(A("evidence", "goal")),
                "strategy_source_task": T(A("evidence", "strategy_source_task")),
                "owner_id": T(A("evidence", "owner_id")),
                "source_epoch": T(A("evidence", "source_epoch")),
                "model_epoch": T(A("evidence", "model_epoch")),
                "frame_epoch": T(A("evidence", "frame_epoch")),
                "deadline_epoch": T(A("request", "deadline_epoch")),
                "split": "training", "expected_outcome": "unknown",
                "status": "awaiting_experience", "attempt_count": 1,
                "cost": T(A("policy", "task_cost")),
                "answer_fields_absent": True,
            }],
            ["add_edge", "agent", "has_process_curriculum_task", "task", {}],
            ["add_edge", "task", "from_evidence", "evidence", {}],
            ["set_attr", "evidence", "status", "scheduled"],
            ["set_attr", "policy", "scheduler_status", "active"],
        ],
    })
    rules.append({
        "name": "pc_close_curriculum_task_on_observed_progress", "area": AREA,
        "order": 30, "latency_class": "background", "batch": False,
        "comment": "Only a same-epoch observed experience outcome closes a curriculum task as completed.",
        "match": [policy, ["agent", "has_process_curriculum_task", "task"],
                  ["task", "has_outcome", "outcome"], ["task", "from_evidence", "evidence"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("policy", "scheduler_status"), L("active")),
                     Eq(A("task", "status"), L("awaiting_experience")),
                     Eq(A("outcome", "status"), L("observed")),
                     Eq(A("outcome", "evidence_status"), L("observed")),
                     Eq(A("outcome", "assessment"), L("tractable_progress")),
                     Eq(A("outcome", "source_epoch"), A("task", "source_epoch")),
                     Eq(A("outcome", "model_epoch"), A("task", "model_epoch")),
                     Eq(A("outcome", "frame_epoch"), A("task", "frame_epoch"))),
        "effects": [["set_attr", "task", "status", "completed"],
                    ["set_attr", "evidence", "status", "resolved"],
                    ["set_attr", "policy", "scheduler_status", "ready"]],
    })
    rules.append({
        "name": "pc_retire_unlearnable_task_without_repetition", "area": AREA,
        "order": 31, "latency_class": "background", "batch": False,
        "comment": "An observed unlearnable assessment is terminal for this exact residual key; later epochs need new evidence keys.",
        "match": [policy, ["agent", "has_process_curriculum_task", "task"],
                  ["task", "has_outcome", "outcome"], ["task", "from_evidence", "evidence"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("policy", "scheduler_status"), L("active")),
                     Eq(A("task", "status"), L("awaiting_experience")),
                     Eq(A("outcome", "status"), L("observed")),
                     Eq(A("outcome", "evidence_status"), L("observed")),
                     Eq(A("outcome", "assessment"), L("unlearnable")),
                     Eq(A("outcome", "source_epoch"), A("task", "source_epoch"))),
        "effects": [["set_attr", "task", "status", "retired_unlearnable"],
                    ["set_attr", "evidence", "status", "suppressed"],
                    ["set_attr", "policy", "scheduler_status", "ready"]],
    })
    rules.append({
        "name": "pc_mark_expired_residual_stale_without_retry", "area": AREA,
        "order": 32, "latency_class": "background", "batch": False,
        "comment": "Epoch mismatch or expired task ends this attempt; it cannot be mistaken for progress or retried from stale evidence.",
        "match": [policy, mode, ["agent", "has_process_curriculum_task", "task"],
                  ["task", "from_evidence", "evidence"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("policy", "scheduler_status"), L("active")),
                     Eq(A("task", "status"), L("awaiting_experience")),
                     Or(Not(Eq(A("task", "source_epoch"), A("evidence", "source_epoch"))),
                        Not(Eq(A("task", "model_epoch"), A("evidence", "model_epoch"))),
                        Not(Eq(A("task", "frame_epoch"), A("evidence", "frame_epoch"))),
                        Gt(A("mode", "epoch"), A("task", "deadline_epoch")))),
        "effects": [["set_attr", "task", "status", "stale"],
                    ["set_attr", "evidence", "status", "stale"],
                    ["set_attr", "policy", "scheduler_status", "ready"]],
    })
    rules.append({
        "name": "pc_close_denied_curriculum_request_without_retry", "area": AREA,
        "order": 33, "latency_class": "background", "batch": False,
        "comment": "Denied funding suppresses this evidence key and never creates an unfunded training task.",
        "match": [policy, ["agent", "has_process_curriculum_evidence", "evidence"],
                  ["evidence", "funded_by", "request"]],
        "where": And(Eq(A("policy", "enabled"), L(1.0)),
                     Eq(A("policy", "scheduler_status"), L("funding_pending")),
                     Eq(A("evidence", "status"), L("funding_pending")),
                     Eq(A("request", "status"), L("denied"))),
        "effects": [["set_attr", "evidence", "status", "suppressed"],
                    ["set_attr", "policy", "scheduler_status", "ready"]],
    })

    return {
        "id": SEED_ID, "version": "1.0.0",
        "depends_on": ["process_induction", "representation_search", "qualia_acquisition",
                       "strategy_library", "thinking_budget"],
        "self_load_only": True, "area": AREA,
        "description": "P15.03: disabled graph-authored curriculum from verified counterexamples, frozen training residuals, contested acquired distinctions and fresh-task stale-strategy rechecks.",
        "microtheory": {"name": AREA,
                        "description": "Fund at most one bounded training task at a time from source- and epoch-bound residual evidence."},
        "nodes": [{"local_id": 0, "type": "ProcessCurriculumPolicy", "attrs": {
            "name": "process_curriculum_policy", "enabled": 0.0,
            "scheduler_status": "ready", "selector_mode": "residual",
            "last_evidence_epoch": -1,
            "max_evidence": 512.0, "max_tasks": 256.0,
            "max_active_tasks": 1.0, "max_attempts_per_evidence": 1.0,
            "task_cost": 1.0,
        }}],
        "edges": [{"src": {"role": "agent_root"},
                   "type": "has_process_curriculum_policy", "tgt": {"local": 0}, "attrs": {}}],
        "productions": productions, "rules": rules,
    }


def main():
    OUT.write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
