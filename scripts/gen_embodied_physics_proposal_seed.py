#!/usr/bin/env python3
"""Generate graph-native physics/analogy driven motor proposal mining.

The faculty closes the seam between a metacognitive learning residual and the
existing embodied analysis-by-synthesis machinery.  It has no joint, limb,
vehicle, or morphology vocabulary.  A situated capability publishes the
categorical body-state relation shape it needs; this seed retrieves analogous
output-null plan stages, asks the generic trajectory faculty to compose known
program consequences, compares the resulting experiments as complete integer
Pareto points, and lets a physical receipt settle the prediction.

Nothing here can actuate a body.  Selection only exposes an already verified
program path to the existing motor-decision collapse.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gen_humanoid_adaptation_seed import (  # noqa: E402
    A,
    And,
    Argmin,
    Count,
    Eq,
    Exists,
    Filter,
    Gt,
    If,
    L,
    Max,
    Min,
    Minus,
    Neg,
    Neighbours,
    Not,
    Or,
    PI0,
    Plus,
    SetT,
    StringConcat,
    T,
    Times,
    ToJsonString,
    V,
)


P0 = PI0
PARETO_DIMENSIONS = (
    ("predicted_evidence", "maximize"),
    ("context_discrimination", "maximize"),
    ("novelty", "maximize"),
    ("energy", "minimize"),
    ("peak_load", "minimize"),
    ("recoverability", "maximize"),
)


def shape_decode(question: str, stage: str, field: str) -> dict:
    return {
        "type": "ShapeDecode",
        "goal": A(question, "desired_body_state_signature"),
        "codebook_type": "EmbodiedMotorPlanHintStage",
        "codebook_scope": SetT(A(stage, "name")),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def memory_shape_decode(
    goal: dict,
    memory: str,
    field: str,
    *,
    codebook_type: str = "EmbodiedMotorProposalShapeMemory",
) -> dict:
    return {
        "type": "ShapeDecode",
        "goal": goal,
        "codebook_type": codebook_type,
        "codebook_scope": SetT(A(memory, "name")),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def questions_for_residual(residual: str = "residual") -> dict:
    return Neighbours(residual, "has_embodied_physics_question")


def analogies_for_stage(question: str = "question", stage: str = "stage") -> dict:
    return Filter(
        Neighbours(question, "has_embodied_physics_analogy"),
        "known_analogy",
        Exists(
            Neighbours("known_analogy", "retrieves_embodied_motor_plan_hint_stage"),
            "known_stage",
            Eq(V("known_stage"), V(stage)),
        ),
    )


def proposals_for_path(question: str = "question", path: str = "path") -> dict:
    return Filter(
        Neighbours(question, "has_motor_learning_proposal"),
        "known_proposal",
        Exists(
            Neighbours("known_proposal", "proposes_embodied_program_path"),
            "known_path",
            Eq(V("known_path"), V(path)),
        ),
    )


def proposals_for_counterfactual(
    question: str = "question",
    program: str = "program",
) -> dict:
    return Filter(
        Neighbours(question, "has_motor_learning_proposal"),
        "known_counterfactual_proposal",
        Exists(
            Neighbours(
                "known_counterfactual_proposal",
                "proposes_counterfactual_motor_program",
            ),
            "known_program",
            Eq(V("known_program"), V(program)),
        ),
    )


def candidate_for_proposal(profile: str = "profile", proposal: str = "proposal") -> dict:
    return Filter(
        Neighbours(profile, "has_pareto_candidate"),
        "known_candidate",
        Exists(
            Neighbours("known_candidate", "represents_motor_learning_proposal"),
            "known_proposal",
            Eq(V("known_proposal"), V(proposal)),
        ),
    )


def proposal_frontier(question: str = "question") -> dict:
    return Filter(
        Neighbours(question, "has_motor_learning_proposal"),
        "frontier_proposal",
        And(
            Eq(A("frontier_proposal", "status"), L("candidate")),
            Eq(P0("frontier_proposal", "eligible"), L(1)),
            Exists(
                Neighbours("frontier_proposal", "has_motor_proposal_pareto_candidate"),
                "frontier_candidate",
                Eq(
                    Count(Neighbours(
                        "frontier_candidate", "is_dominated_by_pareto_candidate"
                    )),
                    L(0),
                ),
            ),
        ),
    )


def curiosity_selected_proposal(question: str = "question") -> dict:
    frontier = proposal_frontier(question)
    return Argmin(
        frontier,
        "curious_proposal",
        Plus(
            Times(
                P0("curious_proposal", "trial_count"),
                Plus(Count(frontier), L(1)),
            ),
            Neg(P0("curious_proposal", "context_discrimination_units")),
        ),
        V(question),
    )


def add_pareto_values(candidate: str, raw: tuple[dict, ...]) -> list[list]:
    signed = (raw[0], raw[1], raw[2], Neg(raw[3]), Neg(raw[4]), raw[5])
    effects: list[list] = []
    for ordinal, value in enumerate(signed):
        node = f"{candidate}_value_{ordinal}"
        effects.extend((
            ["add_node", node, "ParetoValue", {
                "dimension_ordinal": ordinal,
                "raw_value": T(raw[ordinal]),
                "signed_value": T(value),
                "verified": 1,
                "integer_native": 1,
            }],
            ["add_edge", candidate, "has_pareto_value", node],
        ))
    return effects


def open_physics_question_rule() -> dict:
    horizon = Max(
        L(1),
        Count(Neighbours("capability", "has_embodied_program_transition")),
        Count(Neighbours("step", "requires_learning_plan_step")),
    )
    effects: list[list] = [
        ["add_node", "question", "EmbodiedPhysicsQuestion", {
            "kind": "desired_body_state_change",
            "status": "open",
            "desired_body_state_signature": T(A(
                "capability", "desired_body_state_signature"
            )),
            "desired_orientation_units": T(P0(
                "capability", "desired_orientation_units"
            )),
            "trajectory_horizon": T(horizon),
            "analogy_count": 0,
            "proposal_count": 0,
            "selection_count": 0,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "residual", "has_embodied_physics_question", "question"],
        ["add_edge", "question", "answers_learning_plan_residual", "residual"],
        ["add_edge", "question", "targets_learning_plan_step", "step"],
        ["add_edge", "question", "targets_learning_capability", "capability"],
        ["add_edge", "capability", "requests_embodied_program_trajectory", "question"],
        ["add_node", "profile", "ParetoProfile", {
            "kind": "motor_learning_proposal",
            "status": "collecting_candidates",
            "dimension_count": len(PARETO_DIMENSIONS),
            "scalarized": 0,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "question", "has_motor_learning_pareto_profile", "profile"],
        ["add_node", "physics_tasks", "SystemTwoTaskSet", {
            "area": "embodied_physics_proposal",
            "enabled": 1,
            "integer_native": 1,
        }],
        ["add_node", "pareto_tasks", "SystemTwoTaskSet", {
            "area": "cognitive_pareto",
            "enabled": 1,
            "integer_native": 1,
        }],
        ["add_node", "trajectory_tasks", "SystemTwoTaskSet", {
            "area": "embodied_program_trajectory",
            "enabled": 1,
            "integer_native": 1,
        }],
        ["add_node", "escalation", "SystemTwoEscalation", {
            "status": "requested",
            "reason": "unresolved_embodied_physics_question",
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "escalation", "about_context", "question"],
        ["add_edge", "escalation", "recruits_task_set", "physics_tasks"],
        ["add_edge", "escalation", "recruits_task_set", "pareto_tasks"],
        ["add_edge", "escalation", "recruits_task_set", "trajectory_tasks"],
    ]
    for ordinal, (name, direction) in enumerate(PARETO_DIMENSIONS):
        dimension = f"dimension_{ordinal}"
        effects.extend((
            ["add_node", dimension, "ParetoDimension", {
                "name": name,
                "ordinal": ordinal,
                "direction": direction,
                "integer_native": 1,
            }],
            ["add_edge", "profile", "has_pareto_dimension", dimension],
        ))
    return {
        "name": "epm_open_physics_question_from_learning_residual",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A failed learning policy becomes a body-relative physics "
        "question. The horizon is derived from known transitions and relational "
        "prerequisite depth, never an authored retry count.",
        "match": [
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_residual", "residual"],
            ["residual", "about_learning_plan_step", "step"],
            ["step", "plans_learning_capability", "capability"],
        ],
        "where": And(
            Eq(A("residual", "status"), L("open")),
            Not(Eq(A("capability", "desired_body_state_signature"), L(None))),
            Gt(Count(A("capability", "desired_body_state_signature")), L(0)),
            Eq(Count(questions_for_residual()), L(0)),
        ),
        "effects": effects,
    }


def retrieve_plan_stage_analogy_rule() -> dict:
    covered = shape_decode("question", "stage", "covered_count")
    residual = shape_decode("question", "stage", "residual")
    return {
        "name": "epm_retrieve_motor_stage_by_relation_shape",
        "area": "embodied_physics_proposal",
        "latency_class": "background",
        "batch": True,
        "comment": "Plan stages are explanatory analogies only. Partial "
        "relation overlap is retained as a basin hint; it cannot actuate.",
        "match": [
            ["agent", "has_embodied_motor_plan_hint_library", "hint"],
            ["hint", "has_embodied_motor_plan_hint_stage", "stage"],
            ["residual", "has_embodied_physics_question", "question"],
        ],
        "where": And(
            Eq(P0("hint", "output_authority"), L(0)),
            Eq(P0("stage", "output_authority"), L(0)),
            Gt(covered, L(0)),
            Eq(Count(analogies_for_stage()), L(0)),
        ),
        "effects": [
            ["add_node", "analogy", "EmbodiedPhysicsAnalogy", {
                "kind": "relation_shape_motor_basin",
                "covered_relation_count": T(covered),
                "unresolved_relation_count": T(Count(residual)),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "question", "has_embodied_physics_analogy", "analogy"],
            ["add_edge", "analogy", "retrieves_embodied_motor_plan_hint", "hint"],
            ["add_edge", "analogy", "retrieves_embodied_motor_plan_hint_stage", "stage"],
            ["set_attr", "question", "analogy_count", T(Plus(
                P0("question", "analogy_count"), L(1)
            ))],
        ],
    }


def retrieve_proposal_shape_memory_rule() -> dict:
    task_covered = memory_shape_decode(
        A("question", "desired_body_state_signature"),
        "memory",
        "covered_count",
    )
    body_covered = memory_shape_decode(
        A("episode", "body_capability_signature"),
        "body_shape",
        "covered_count",
        codebook_type="EmbodiedMotorProposalBodyShapeMemory",
    )
    known = Filter(
        Neighbours("question", "has_embodied_physics_analogy"),
        "known_memory_analogy",
        Exists(
            Neighbours(
                "known_memory_analogy", "retrieves_motor_proposal_shape_memory"
            ),
            "known_memory",
            Eq(V("known_memory"), V("memory")),
        ),
    )
    return {
        "name": "epm_retrieve_verified_proposal_shape_across_similar_body",
        "area": "embodied_physics_proposal",
        "latency_class": "background",
        "batch": True,
        "comment": "A successful experiment is reusable only as an "
        "output-null basin hint. Both desired consequence topology and the "
        "currently observed body relation system must overlap; the local body "
        "must still verify it physically.",
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_self_directed_learning_plan", "plan"],
            ["plan", "has_learning_plan_residual", "residual"],
            ["residual", "has_embodied_physics_question", "question"],
            ["agent", "has_motor_proposal_shape_memory", "memory"],
            ["memory", "has_motor_proposal_body_shape_memory", "body_shape"],
        ],
        "where": And(
            Eq(A("memory", "status"), L("retained")),
            Eq(P0("memory", "output_authority"), L(0)),
            Gt(task_covered, L(0)),
            Gt(body_covered, L(0)),
            Eq(Count(known), L(0)),
        ),
        "effects": [
            ["add_node", "analogy", "EmbodiedPhysicsAnalogy", {
                "kind": "verified_cross_body_proposal_shape",
                "covered_relation_count": T(task_covered),
                "covered_body_relation_count": T(body_covered),
                "requires_local_verification": 1,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "question", "has_embodied_physics_analogy", "analogy"],
            ["add_edge", "analogy", "retrieves_motor_proposal_shape_memory", "memory"],
            ["set_attr", "question", "analogy_count", T(Plus(
                P0("question", "analogy_count"), L(1)
            ))],
        ],
    }


def mint_verified_path_proposal_rule() -> dict:
    predicted = Min(
        P0("path", "orientation_span_units"),
        Max(L(1), P0("question", "desired_orientation_units")),
    )
    discrimination = Count(Neighbours(
        "path", "contains_embodied_program_transition"
    ))
    novelty = Max(
        L(0), Minus(P0("path", "depth"), P0("path", "replay_count"))
    )
    recoverability = Max(
        L(0), Minus(
            P0("path", "depth"), P0("path", "boundary_transition_count")
        )
    )
    raw = (
        predicted,
        discrimination,
        novelty,
        P0("path", "energy_units"),
        P0("path", "peak_load_units"),
        recoverability,
    )
    effects: list[list] = [
        ["add_node", "proposal", "MotorLearningProposal", {
            "kind": "verified_program_path_experiment",
            "status": "candidate",
            "eligible": 1,
            "predicted_evidence_units": T(predicted),
            "context_discrimination_units": T(discrimination),
            "novelty_units": T(novelty),
            "energy_units": T(P0("path", "energy_units")),
            "peak_load_units": T(P0("path", "peak_load_units")),
            "recoverability_units": T(recoverability),
            "trial_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "question", "has_motor_learning_proposal", "proposal"],
        ["add_edge", "proposal", "proposes_embodied_program_path", "path"],
        ["add_edge", "proposal", "targets_learning_capability", "capability"],
        ["add_node", "candidate", "ParetoCandidate", {
            "kind": "motor_learning_proposal",
            "verified": 1,
            "dominated": 0,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "profile", "has_pareto_candidate", "candidate"],
        ["add_edge", "candidate", "represents_motor_learning_proposal", "proposal"],
        ["add_edge", "proposal", "has_motor_proposal_pareto_candidate", "candidate"],
        ["set_attr", "question", "proposal_count", T(Plus(
            P0("question", "proposal_count"), L(1)
        ))],
    ]
    effects.extend(add_pareto_values("candidate", raw))
    return {
        "name": "epm_mint_complete_integer_proposal_from_verified_path",
        "area": "embodied_physics_proposal",
        "latency_class": "soft_realtime",
        "batch": True,
        "comment": "Receipt-verified analysis-by-synthesis paths become "
        "complete six-coordinate experiments. Energy and load remain separate "
        "objectives; no reward scalar is invented.",
        "match": [
            ["question", "targets_learning_capability", "capability"],
            ["question", "has_motor_learning_pareto_profile", "profile"],
            ["capability", "has_embodied_program_trajectory", "trajectory"],
            ["trajectory", "has_pareto_candidate", "path"],
        ],
        "where": And(
            Eq(A("question", "status"), L("open")),
            Eq(A("path", "kind"), L("embodied_program_path")),
            Eq(P0("path", "verified"), L(1)),
            Gt(P0("path", "orientation_span_units"), L(0)),
            Eq(
                Count(Neighbours("path", "contains_embodied_program_transition")),
                P0("path", "depth"),
            ),
            Eq(Count(proposals_for_path()), L(0)),
        ),
        "effects": effects,
    }


def mint_counterfactual_compound_proposal_rule() -> dict:
    raw = (
        P0("program", "predicted_evidence_units"),
        P0("program", "member_count"),
        P0("program", "interaction_uncertainty_units"),
        P0("program", "predicted_energy_units"),
        P0("program", "predicted_peak_load_units"),
        P0("program", "predicted_recoverability_units"),
    )
    effects: list[list] = [
        ["add_node", "proposal", "MotorLearningProposal", {
            "kind": "unseen_counterfactual_compound_experiment",
            "status": "candidate",
            "eligible": 1,
            "predicted_evidence_units": T(raw[0]),
            "context_discrimination_units": T(raw[1]),
            "novelty_units": T(raw[2]),
            "energy_units": T(raw[3]),
            "peak_load_units": T(raw[4]),
            "recoverability_units": T(raw[5]),
            "component_count": T(P0("program", "member_count")),
            "interaction_uncertainty_units": T(P0(
                "program", "interaction_uncertainty_units"
            )),
            "requires_release_envelope_guard": 1,
            "physical_verified": 0,
            "trial_count": 0,
            "success_count": 0,
            "failure_count": 0,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "question", "has_motor_learning_proposal", "proposal"],
        ["add_edge", "proposal", "proposes_counterfactual_motor_program", "program"],
        ["add_edge", "proposal", "targets_learning_capability", "capability"],
        ["add_node", "candidate", "ParetoCandidate", {
            "kind": "motor_learning_proposal",
            "coordinate_complete": 1,
            "physical_verified": 0,
            "dominated": 0,
            "output_authority": 0,
            "integer_native": 1,
        }],
        ["add_edge", "profile", "has_pareto_candidate", "candidate"],
        ["add_edge", "candidate", "represents_motor_learning_proposal", "proposal"],
        ["add_edge", "proposal", "has_motor_proposal_pareto_candidate", "candidate"],
        ["set_attr", "question", "proposal_count", T(Plus(
            P0("question", "proposal_count"), L(1)
        ))],
    ]
    effects.extend(add_pareto_values("candidate", raw))
    return {
        "name": "epm_publish_unseen_compound_as_integer_pareto_proposal",
        "area": "embodied_physics_proposal",
        "latency_class": "soft_realtime",
        "batch": True,
        "comment": "A domain adapter may publish an output-null compound "
        "assembled from receipt-learned primitives. Its forward projection is "
        "a testable prediction, never confused with physical verification.",
        "match": [
            ["question", "targets_learning_capability", "capability"],
            ["question", "has_motor_learning_pareto_profile", "profile"],
            ["question", "has_counterfactual_motor_program", "program"],
        ],
        "where": And(
            Eq(A("question", "status"), L("open")),
            Eq(A("program", "status"), L("counterfactual_predicted")),
            Eq(P0("program", "counterfactual_unseen"), L(1)),
            Gt(P0("program", "member_count"), L(1)),
            Gt(P0("program", "predicted_evidence_units"), L(0)),
            Eq(Count(proposals_for_counterfactual()), L(0)),
        ),
        "effects": effects,
    }


def select_frontier_proposal_rule() -> dict:
    frontier = proposal_frontier()
    # Pareto decides what is refuted. Curiosity only orders the surviving
    # incomparable experiments: least tried, then most discriminating. The
    # multiplier falls out of the current frontier cardinality.
    selected = curiosity_selected_proposal()
    return {
        "name": "epm_curiosity_selects_one_pareto_motor_experiment",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "The massively parallel proposal frontier collapses to "
        "one compound experiment. This is still output-null: the existing "
        "motor collapse retains sole actuator authority.",
        "match": [
            ["question", "targets_learning_capability", "capability"],
            ["question", "has_motor_learning_proposal", "proposal"],
            ["proposal", "proposes_embodied_program_path", "path"],
        ],
        "where": And(
            Gt(Count(frontier), L(0)),
            Eq(V("proposal"), selected),
            Eq(Count(Neighbours(
                "question", "has_selected_motor_learning_proposal"
            )), L(0)),
        ),
        "effects": [
            ["add_edge", "question", "has_selected_motor_learning_proposal", "proposal"],
            ["add_edge", "capability", "has_selected_motor_learning_proposal", "proposal"],
            ["set_attr", "proposal", "status", "trial_requested"],
            ["set_attr", "proposal", "trial_count", T(Plus(
                P0("proposal", "trial_count"), L(1)
            ))],
            ["set_attr", "proposal", "success_baseline", T(P0(
                "capability", "success_count"
            ))],
            ["set_attr", "proposal", "failure_baseline", T(P0(
                "capability", "failure_count"
            ))],
            ["set_attr", "question", "selection_count", T(Plus(
                P0("question", "selection_count"), L(1)
            ))],
            ["add_edge", "capability", "has_selected_embodied_program_path", "path"],
        ],
    }


def select_counterfactual_frontier_proposal_rule() -> dict:
    frontier = proposal_frontier()
    selected = curiosity_selected_proposal()
    return {
        "name": "epm_curiosity_selects_one_unseen_compound_experiment",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Selection remains output-null. The body adapter must "
        "route the chosen compound through its ordinary motor and material "
        "envelope collapse before any effector receives authority.",
        "match": [
            ["question", "targets_learning_capability", "capability"],
            ["question", "has_motor_learning_proposal", "proposal"],
            ["proposal", "proposes_counterfactual_motor_program", "program"],
        ],
        "where": And(
            Gt(Count(frontier), L(0)),
            Eq(V("proposal"), selected),
            Eq(Count(Neighbours(
                "question", "has_selected_motor_learning_proposal"
            )), L(0)),
        ),
        "effects": [
            ["add_edge", "question", "has_selected_motor_learning_proposal", "proposal"],
            ["add_edge", "capability", "has_selected_motor_learning_proposal", "proposal"],
            ["set_attr", "proposal", "status", "trial_requested"],
            ["set_attr", "proposal", "trial_count", T(Plus(
                P0("proposal", "trial_count"), L(1)
            ))],
            ["set_attr", "proposal", "success_baseline", T(P0(
                "capability", "success_count"
            ))],
            ["set_attr", "proposal", "failure_baseline", T(P0(
                "capability", "failure_count"
            ))],
            ["set_attr", "question", "selection_count", T(Plus(
                P0("question", "selection_count"), L(1)
            ))],
        ],
    }


def promote_successful_proposal_rule() -> dict:
    return {
        "name": "epm_promote_proposal_only_after_physical_causal_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_development_receipt", "receipt"],
            ["episode", "has_active_embodied_developmental_capability", "capability"],
            ["capability", "has_selected_motor_learning_proposal", "proposal"],
            ["question", "has_selected_motor_learning_proposal", "proposal"],
            ["question", "answers_learning_plan_residual", "residual"],
        ],
        "where": And(
            Eq(A("proposal", "status"), L("trial_requested")),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Gt(P0("capability", "success_count"), P0(
                "proposal", "success_baseline"
            )),
        ),
        "effects": [
            ["set_attr", "proposal", "status", "grounded"],
            ["set_attr", "proposal", "success_count", T(Plus(
                P0("proposal", "success_count"), L(1)
            ))],
            ["set_attr", "question", "status", "grounded"],
            ["set_attr", "residual", "status", "resolved"],
            ["add_node", "memory", "EmbodiedMotorProposalShapeMemory", {
                "name": T(StringConcat(
                    L("motor_proposal_shape:"),
                    ToJsonString(A("question", "desired_body_state_signature")),
                    L(":"),
                    ToJsonString(A("episode", "body_capability_signature")),
                )),
                "signature": T(A("question", "desired_body_state_signature")),
                "body_signature": T(A(
                    "episode", "body_capability_signature"
                )),
                "predicted_evidence_units": T(P0(
                    "proposal", "predicted_evidence_units"
                )),
                "energy_units": T(P0("proposal", "energy_units")),
                "peak_load_units": T(P0("proposal", "peak_load_units")),
                "status": "retained",
                "requires_local_verification": 1,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_node", "body_shape", "EmbodiedMotorProposalBodyShapeMemory", {
                "name": T(StringConcat(
                    L("motor_proposal_body_shape:"),
                    ToJsonString(A("episode", "body_capability_signature")),
                )),
                "signature": T(A("episode", "body_capability_signature")),
                "status": "retained",
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "proposal", "stores_as_motor_proposal_shape_memory", "memory"],
            ["add_edge", "memory", "has_motor_proposal_body_shape_memory", "body_shape"],
            ["add_edge", "capability", "has_motor_proposal_shape_memory", "memory"],
            ["add_edge", "agent", "has_motor_proposal_shape_memory", "memory"],
        ],
    }


def promote_grounded_path_rule() -> dict:
    return {
        "name": "epm_mark_verified_path_promoted_after_success",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["proposal", "proposes_embodied_program_path", "path"],
        ],
        "where": And(
            Eq(A("proposal", "status"), L("grounded")),
            Eq(Count(Neighbours(
                "proposal", "promotes_embodied_program_path"
            )), L(0)),
        ),
        "effects": [[
            "add_edge", "proposal", "promotes_embodied_program_path", "path"
        ]],
    }


def settle_counterfactual_program_status_rule() -> dict:
    return {
        "name": "epm_settle_counterfactual_program_from_proposal_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["proposal", "proposes_counterfactual_motor_program", "program"],
        ],
        "where": And(
            Or(
                Eq(A("proposal", "status"), L("grounded")),
                Eq(A("proposal", "status"), L("counterexample_observed")),
            ),
            Not(Eq(A("program", "status"), A("proposal", "status"))),
        ),
        "effects": [
            ["set_attr", "program", "status", T(A("proposal", "status"))],
            ["set_attr", "program", "experience_retained", 1],
            ["set_attr", "program", "physical_verified", T(
                If(
                    Eq(A("proposal", "status"), L("grounded")),
                    L(1), L(0),
                )
            )],
        ],
    }


def reject_failed_proposal_rule() -> dict:
    return {
        "name": "epm_store_contextual_counterexample_from_failed_receipt",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_development_episode", "episode"],
            ["episode", "has_embodied_development_receipt", "receipt"],
            ["episode", "has_active_embodied_developmental_capability", "capability"],
            ["capability", "has_selected_motor_learning_proposal", "proposal"],
            ["question", "has_selected_motor_learning_proposal", "proposal"],
        ],
        "where": And(
            Eq(A("proposal", "status"), L("trial_requested")),
            Eq(P0("receipt", "development_receipt_closed"), L(1)),
            Gt(P0("capability", "failure_count"), P0(
                "proposal", "failure_baseline"
            )),
            Eq(P0("capability", "success_count"), P0(
                "proposal", "success_baseline"
            )),
        ),
        "effects": [
            ["set_attr", "proposal", "status", "counterexample_observed"],
            ["set_attr", "proposal", "eligible", 0],
            ["set_attr", "proposal", "failure_count", T(Plus(
                P0("proposal", "failure_count"), L(1)
            ))],
            ["add_node", "counterexample", "MotorProposalCounterexample", {
                "body_signature": T(A("episode", "body_capability_signature")),
                "question_signature": T(A(
                    "question", "desired_body_state_signature"
                )),
                "status": "retained",
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "proposal", "has_motor_proposal_counterexample", "counterexample"],
            ["add_edge", "agent", "has_motor_proposal_counterexample", "counterexample"],
            ["del_edge", "question", "has_selected_motor_learning_proposal", "proposal"],
            ["del_edge", "capability", "has_selected_motor_learning_proposal", "proposal"],
        ],
    }


def manifest() -> dict:
    productions = (
        ("inverse_principle", "Agent", "knows_embodied_inverse_kinematics", "EmbodiedInverseKinematicsPrinciple"),
        ("residual_question", "LearningPlanResidual", "has_embodied_physics_question", "EmbodiedPhysicsQuestion"),
        ("question_residual", "EmbodiedPhysicsQuestion", "answers_learning_plan_residual", "LearningPlanResidual"),
        ("question_step", "EmbodiedPhysicsQuestion", "targets_learning_plan_step", "LearningPlanStep"),
        ("question_capability", "EmbodiedPhysicsQuestion", "targets_learning_capability", "Node"),
        ("question_profile", "EmbodiedPhysicsQuestion", "has_motor_learning_pareto_profile", "ParetoProfile"),
        ("question_analogy", "EmbodiedPhysicsQuestion", "has_embodied_physics_analogy", "EmbodiedPhysicsAnalogy"),
        ("analogy_hint", "EmbodiedPhysicsAnalogy", "retrieves_embodied_motor_plan_hint", "EmbodiedMotorPlanHint"),
        ("analogy_stage", "EmbodiedPhysicsAnalogy", "retrieves_embodied_motor_plan_hint_stage", "EmbodiedMotorPlanHintStage"),
        ("analogy_memory", "EmbodiedPhysicsAnalogy", "retrieves_motor_proposal_shape_memory", "EmbodiedMotorProposalShapeMemory"),
        ("question_proposal", "EmbodiedPhysicsQuestion", "has_motor_learning_proposal", "MotorLearningProposal"),
        ("selected_proposal", "Node", "has_selected_motor_learning_proposal", "MotorLearningProposal"),
        ("proposal_path", "MotorLearningProposal", "proposes_embodied_program_path", "ParetoCandidate"),
        ("question_counterfactual", "EmbodiedPhysicsQuestion", "has_counterfactual_motor_program", "Node"),
        ("proposal_counterfactual", "MotorLearningProposal", "proposes_counterfactual_motor_program", "Node"),
        ("proposal_capability", "MotorLearningProposal", "targets_learning_capability", "Node"),
        ("candidate_proposal", "ParetoCandidate", "represents_motor_learning_proposal", "MotorLearningProposal"),
        ("proposal_candidate", "MotorLearningProposal", "has_motor_proposal_pareto_candidate", "ParetoCandidate"),
        ("promoted_path", "MotorLearningProposal", "promotes_embodied_program_path", "ParetoCandidate"),
        ("counterexample", "MotorLearningProposal", "has_motor_proposal_counterexample", "MotorProposalCounterexample"),
        ("proposal_memory", "MotorLearningProposal", "stores_as_motor_proposal_shape_memory", "EmbodiedMotorProposalShapeMemory"),
        ("memory_body_shape", "EmbodiedMotorProposalShapeMemory", "has_motor_proposal_body_shape_memory", "EmbodiedMotorProposalBodyShapeMemory"),
        ("capability_memory", "Node", "has_motor_proposal_shape_memory", "EmbodiedMotorProposalShapeMemory"),
        ("agent_memory", "Agent", "has_motor_proposal_shape_memory", "EmbodiedMotorProposalShapeMemory"),
        ("agent_counterexample", "Agent", "has_motor_proposal_counterexample", "MotorProposalCounterexample"),
        # Γ is deliberately nominal rather than subtype-polymorphic.  Publish
        # the concrete developmental adapter edges as well as the generic
        # Node contracts above; otherwise a Rule could describe the bridge
        # but the substrate would correctly refuse to materialize it.
        ("situated_question", "EmbodiedPhysicsQuestion", "targets_learning_capability", "EmbodiedSituatedDevelopmentalCapability"),
        ("situated_request", "EmbodiedSituatedDevelopmentalCapability", "requests_embodied_program_trajectory", "EmbodiedPhysicsQuestion"),
        ("situated_trajectory", "EmbodiedSituatedDevelopmentalCapability", "has_embodied_program_trajectory", "ParetoProfile"),
        ("situated_transition", "EmbodiedSituatedDevelopmentalCapability", "has_embodied_program_transition", "Node"),
        ("situated_selected_path", "EmbodiedSituatedDevelopmentalCapability", "has_selected_embodied_program_path", "ParetoCandidate"),
        ("question_selected_proposal", "EmbodiedPhysicsQuestion", "has_selected_motor_learning_proposal", "MotorLearningProposal"),
        ("situated_selected_proposal", "EmbodiedSituatedDevelopmentalCapability", "has_selected_motor_learning_proposal", "MotorLearningProposal"),
        ("proposal_situated_capability", "MotorLearningProposal", "targets_learning_capability", "EmbodiedSituatedDevelopmentalCapability"),
        ("situated_memory", "EmbodiedSituatedDevelopmentalCapability", "has_motor_proposal_shape_memory", "EmbodiedMotorProposalShapeMemory"),
        ("question_humanoid_counterfactual", "EmbodiedPhysicsQuestion", "has_counterfactual_motor_program", "HumanoidMotorProgram"),
        ("proposal_humanoid_counterfactual", "MotorLearningProposal", "proposes_counterfactual_motor_program", "HumanoidMotorProgram"),
    )
    return {
        "id": "embodied_physics_proposal",
        "version": "1.1.0",
        "depends_on": [
            "metacognitive_learning",
            "embodied_program_trajectory",
            "embodied_capability_bootstrap",
        ],
        "area": "general_cognition",
        "latency_class": "soft_realtime",
        "description": "Morphology-neutral residual-to-physics-question "
        "bridge: inverse-by-forward-model kinematic prior, relation-shape "
        "analogy, verified analysis-by-synthesis trajectories, six-axis "
        "integer Pareto experiments, curiosity collapse, and receipt closure.",
        "nodes": [{
            "local_id": 1,
            "type": "EmbodiedInverseKinematicsPrinciple",
            "attrs": {
                "kind": "invert_local_forward_consequence_model",
                "representation": "body_relative_task_space_residual",
                "analytic_jacobian_required": 0,
                "anatomical_labels_required": 0,
                "requires_receipt_learned_forward_model": 1,
                "requires_local_physical_verification": 1,
                "integer_native": 1,
                "output_authority": 0,
            },
        }],
        "edges": [{
            "src": {"role": "agent_root"},
            "type": "knows_embodied_inverse_kinematics",
            "tgt": {"local": 1},
            "attrs": {},
        }],
        "productions": [
            {
                "provenance": f"embodied_physics_proposal:{name}",
                "src": {"type": src, "var": "src"},
                "edge_type": edge,
                "tgt": {"type": tgt, "var": "tgt"},
            }
            for name, src, edge, tgt in productions
        ],
        "rules": [
            open_physics_question_rule(),
            retrieve_plan_stage_analogy_rule(),
            retrieve_proposal_shape_memory_rule(),
            mint_verified_path_proposal_rule(),
            mint_counterfactual_compound_proposal_rule(),
            select_frontier_proposal_rule(),
            select_counterfactual_frontier_proposal_rule(),
            promote_successful_proposal_rule(),
            promote_grounded_path_rule(),
            reject_failed_proposal_rule(),
            settle_counterfactual_program_status_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "embodied_physics_proposal.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
