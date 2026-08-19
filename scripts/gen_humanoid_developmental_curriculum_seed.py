#!/usr/bin/env python3
"""Generate the humanoid bridge into general embodied development."""
from __future__ import annotations

import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.gen_humanoid_adaptation_seed import (  # noqa: E402
    A,
    AO,
    And,
    Argmin,
    Count,
    Eq,
    Exists,
    Filter,
    Gt,
    If,
    IDiv,
    L,
    Lt,
    Max,
    Minus,
    Neg,
    Neighbours,
    Not,
    Or,
    Pick,
    PI0,
    Plus,
    Sum,
    Times,
    T,
    V,
)


P0 = PI0


def integer_node_attr(node, key):
    return Plus(AO(node, key), L(0))


def developmental_action_model(phase_candidate="candidate"):
    return Pick(Neighbours(
        phase_candidate, "generalizes_humanoid_action_model"
    ))


def developmental_orientation_escape_score(phase_candidate="candidate"):
    model = developmental_action_model(phase_candidate)
    return Plus(
        integer_node_attr(model, "development_orientation_escape_units"),
        Neg(integer_node_attr(
            model, "development_orientation_return_units"
        )),
    )


def developmental_evidence_rank(
    phase_candidate="candidate", query="query"
):
    # Selection follows requested observable evidence, not a named skill.
    # This lets the same learned consequence model serve unfamiliar curricula
    # and body plans without an adapter-side vocabulary of rolls or poses.
    return If(
        Gt(integer_node_attr(
            developmental_action_model(phase_candidate),
            "development_receipt_count",
        ), L(0)),
        P0(phase_candidate, "inverse_kinematic_cost_units"),
        Neg(physics_evidence_units("capability", phase_candidate)),
    )


def physics_evidence_units(capability="capability", phase_candidate="candidate"):
    """Predict the requested evidence from a receipt-learned opaque command.

    This is an adapter from the developmental evidence vocabulary into the
    general physics-proposal contract.  It contains no capability names, joint
    names, poses, or action tokens.
    """
    model = developmental_action_model(phase_candidate)
    kind = A(capability, "evidence_kind")
    orientation = Max(
        L(0), developmental_orientation_escape_score(phase_candidate)
    )
    return If(
        is_orientation_evidence(capability),
        orientation,
        If(
            Eq(kind, L("support_gain")),
            integer_node_attr(model, "development_support_evidence_units"),
            If(
                Eq(kind, L("configuration_reversal")),
                integer_node_attr(
                    model, "development_reversal_evidence_count"
                ),
                If(
                    Eq(kind, L("support_topology_change")),
                    integer_node_attr(
                        model,
                        "development_support_transition_evidence_count",
                    ),
                    If(
                        Eq(kind, L("stable_partial_motion")),
                        integer_node_attr(
                            model, "development_stable_evidence_count"
                        ),
                        If(
                            is_translation_evidence(capability),
                            integer_node_attr(
                                model,
                                "development_translation_evidence_units",
                            ),
                            If(
                                is_elevation_evidence(capability),
                                Max(L(0), integer_node_attr(
                                    model,
                                    "development_elevation_sum_units",
                                )),
                                L(0),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def is_translation_evidence(capability="capability"):
    return Or(*[
        Eq(A(capability, "evidence_kind"), L(kind))
        for kind in (
            "supported_translation",
            "translated_support_cycle",
            "reduced_support_cycle",
            "novel_locomotor_phenotype",
            "locomotor_cycle",
        )
    ])


def is_elevation_evidence(capability="capability"):
    return Or(*[
        Eq(A(capability, "evidence_kind"), L(kind))
        for kind in ("supported_elevation", "support_reducing_elevation")
    ])


def is_orientation_evidence(capability="capability"):
    return Or(*[
        Eq(A(capability, "evidence_kind"), L(kind))
        for kind in (
            "supported_orientation_change",
            "supported_quarter_turn",
            "supported_half_turn",
        )
    ])


def inverse_queries(development="development", capability="capability"):
    return Filter(
        Neighbours(development, "has_active_embodied_inverse_kinematic_query"),
        "known_inverse_query",
        And(
            Eq(A("known_inverse_query", "status"), L("active")),
            Exists(
                Neighbours(
                    "known_inverse_query", "targets_learning_capability"
                ),
                "known_inverse_capability",
                Eq(V("known_inverse_capability"), V(capability)),
            ),
        ),
    )


def expected_action_units(candidate, key):
    model = developmental_action_model(candidate)
    return IDiv(
        integer_node_attr(model, key),
        Max(L(1), integer_node_attr(model, "development_receipt_count")),
    )


def squared_residual(target, predicted):
    residual = Minus(target, predicted)
    return Times(residual, residual)


def inverse_kinematic_rank(query="query", candidate="candidate"):
    """Residual after one learned local forward consequence.

    This is discrete, local inverse kinematics by analysis-by-synthesis.  The
    query supplies task-space residuals; opaque actions supply receipt-learned
    forward consequences. No joint labels, Jacobian or float policy enters.
    """
    directed = expected_action_units(
        candidate, "development_directed_sum_units"
    )
    lateral = expected_action_units(
        candidate, "development_lateral_sum_units"
    )
    elevation = expected_action_units(
        candidate, "development_elevation_sum_units"
    )
    orientation_sum = integer_node_attr(
        developmental_action_model(candidate),
        "development_orientation_escape_sum_units",
    )
    orientation = If(
        Eq(orientation_sum, L(0)),
        IDiv(
            developmental_orientation_escape_score(candidate),
            Max(L(1), integer_node_attr(
                developmental_action_model(candidate),
                "development_receipt_count",
            )),
        ),
        expected_action_units(
            candidate, "development_orientation_escape_sum_units"
        ),
    )
    return If(
        Eq(A(query, "mode"), L("translation")),
        Plus(
            squared_residual(P0(query, "target_directed_units"), directed),
            Times(lateral, lateral),
            Times(elevation, elevation),
        ),
        If(
            Eq(A(query, "mode"), L("elevation")),
            Plus(
                squared_residual(
                    P0(query, "target_elevation_units"), elevation
                ),
                Times(lateral, lateral),
            ),
            If(
                Eq(A(query, "mode"), L("orientation")),
                squared_residual(
                    P0(query, "target_orientation_units"), orientation
                ),
                Neg(physics_evidence_units("capability", candidate)),
            ),
        ),
    )


def open_inverse_kinematic_query_rule():
    residual = Max(
        L(1),
        Minus(
            P0("development", "development_evidence_window"),
            P0("capability", "success_count"),
        ),
    )
    mode = If(
        is_translation_evidence(), L("translation"),
        If(
            is_elevation_evidence(), L("elevation"),
            If(is_orientation_evidence(), L("orientation"), L("affordance")),
        ),
    )
    return {
        "name": "hdc_open_goal_relative_inverse_kinematic_bootstrap",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -121,
        "batch": False,
        "comment": "Turn the active generic developmental goal into an "
        "integer task-space residual. This is an output-null query over "
        "learned forward consequences, never an authored pose or solver.",
        "match": [
            ["agent", "knows_embodied_inverse_kinematics", "principle"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
        ],
        "where": Eq(Count(inverse_queries()), L(0)),
        "effects": [
            ["add_node", "query", "EmbodiedInverseKinematicQuery", {
                "status": "active",
                "mode": T(mode),
                "target_directed_units": T(If(
                    is_translation_evidence(), residual, L(0)
                )),
                "target_elevation_units": T(If(
                    is_elevation_evidence(), residual, L(0)
                )),
                "target_orientation_units": T(If(
                    is_orientation_evidence(), Max(
                        residual, P0("capability", "desired_orientation_units")
                    ), L(0)
                )),
                "success_baseline_units": T(P0(
                    "capability", "success_count"
                )),
                "generation": T(Plus(
                    P0("development", "inverse_kinematic_generation"), L(1)
                )),
                "inverse_by_forward_model": 1,
                "requires_local_verification": 1,
                "integer_native": 1,
                "output_authority": 0,
            }],
            ["add_edge", "development", "has_embodied_inverse_kinematic_query", "query"],
            ["add_edge", "development", "has_active_embodied_inverse_kinematic_query", "query"],
            ["add_edge", "query", "targets_learning_capability", "capability"],
            ["add_edge", "query", "instantiates_inverse_kinematic_principle", "principle"],
            ["set_attr", "development", "inverse_kinematic_generation", T(
                Plus(P0("development", "inverse_kinematic_generation"), L(1))
            )],
        ],
    }


def bind_inverse_query_to_generic_goal_rule():
    return {
        "name": "hdc_bind_inverse_kinematic_query_to_existing_goal",
        "area": "general_cognition",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["query", "targets_learning_capability", "capability"],
            ["goal", "grounds_learning_capability", "capability"],
        ],
        "where": Not(Exists(
            Neighbours("query", "pursues_goal"), "known_goal",
            Eq(V("known_goal"), V("goal")),
        )),
        "effects": [["add_edge", "query", "pursues_goal", "goal"]],
    }


def refresh_inverse_kinematic_query_rule():
    residual = Max(
        L(1), Minus(
            P0("development", "development_evidence_window"),
            P0("capability", "success_count"),
        )
    )
    return {
        "name": "hdc_refresh_inverse_kinematic_residual_from_goal_progress",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -120,
        "batch": False,
        "match": [
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["development", "has_active_embodied_inverse_kinematic_query", "query"],
            ["query", "targets_learning_capability", "capability"],
        ],
        "where": Not(Eq(
            P0("query", "success_baseline_units"),
            P0("capability", "success_count"),
        )),
        "effects": [
            ["set_attr", "query", "success_baseline_units", T(P0(
                "capability", "success_count"
            ))],
            ["set_attr", "query", "generation", T(Plus(
                P0("development", "inverse_kinematic_generation"), L(1)
            ))],
            ["set_attr", "development", "inverse_kinematic_generation", T(
                Plus(P0("development", "inverse_kinematic_generation"), L(1))
            )],
            ["set_attr", "query", "target_directed_units", T(If(
                is_translation_evidence(), residual, L(0)
            ))],
            ["set_attr", "query", "target_elevation_units", T(If(
                is_elevation_evidence(), residual, L(0)
            ))],
            ["set_attr", "query", "target_orientation_units", T(If(
                is_orientation_evidence(), Max(
                    residual, P0("capability", "desired_orientation_units")
                ), L(0)
            ))],
        ],
    }


def score_inverse_kinematic_forward_models_rule():
    return {
        "name": "hdc_score_local_forward_models_against_inverse_residual",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -119,
        "batch": True,
        "comment": "Materialize one residual-after-action cost per opaque "
        "local forward model. Later parallel program searches read this "
        "integer result instead of re-expanding the inverse expression.",
        "match": [
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["development", "has_active_embodied_inverse_kinematic_query", "query"],
            ["query", "targets_learning_capability", "capability"],
            ["episode", "has_humanoid_phase_action_model", "candidate"],
            ["candidate", "generalizes_humanoid_action_model", "action_model"],
        ],
        "where": And(
            Gt(P0("action_model", "development_receipt_count"), L(0)),
            Or(
                Not(Eq(
                    P0("candidate", "inverse_kinematic_generation"),
                    P0("query", "generation"),
                )),
                Not(Eq(
                    P0("candidate", "inverse_scored_receipt_count"),
                    P0("action_model", "development_receipt_count"),
                )),
            ),
        ),
        "effects": [
            ["set_attr", "candidate", "inverse_kinematic_cost_units", T(
                inverse_kinematic_rank("query", "candidate")
            )],
            ["set_attr", "candidate", "inverse_kinematic_generation", T(P0(
                "query", "generation"
            ))],
            ["set_attr", "candidate", "inverse_scored_receipt_count", T(P0(
                "action_model", "development_receipt_count"
            ))],
        ],
    }


def archive_stale_inverse_kinematic_query_rule():
    return {
        "name": "hdc_archive_inverse_kinematic_query_at_goal_boundary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -122,
        "batch": True,
        "match": [
            ["development", "has_active_embodied_developmental_capability", "current"],
            ["development", "has_active_embodied_inverse_kinematic_query", "query"],
            ["query", "targets_learning_capability", "previous"],
        ],
        "where": Not(Eq(V("current"), V("previous"))),
        "effects": [
            ["del_edge", "development", "has_active_embodied_inverse_kinematic_query", "query"],
            ["set_attr", "query", "status", "archived"],
        ],
    }
def physics_counterfactual_candidates(
    capability="capability",
    var_name="physics_candidate",
):
    return Filter(
        Neighbours("episode", "has_humanoid_phase_action_model"),
        var_name,
        And(
            Eq(
                P0(var_name, "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Gt(
                integer_node_attr(
                    developmental_action_model(var_name),
                    "development_receipt_count",
                ),
                L(0),
            ),
            Gt(physics_evidence_units(capability, var_name), L(0)),
        ),
    )


def intentional_locomotor_goal(capability="capability"):
    """Any developmental capability intentionally exploring locomotion."""
    return Eq(A(capability, "goal"), L("locomotion"))


def floor_development(capability="capability"):
    """A low pose is the task context here, not a recovery error."""
    return Eq(A(capability, "developmental_ecology"), L("floor"))


def material_viability_reflex_active():
    """Existing hard-sheet evidence that recovery still has authority."""
    return Or(
        Eq(P0("episode", "sensorimotor_interrupt_required"), L(1)),
        Eq(P0("episode", "reset_requested"), L(1)),
    )


def situated_developmental_release_gate(capability="capability"):
    """Separate intended floor/locomotor exploration from an interrupt."""
    return And(
        Eq(P0("episode", "developmental_curriculum_active"), L(1)),
        Eq(A("episode", "phase"), L("locomotion")),
        Or(
            floor_development(capability),
            And(
                intentional_locomotor_goal(capability),
                Eq(P0("episode", "locomotion_drive_active"), L(1)),
            ),
        ),
        Not(material_viability_reflex_active()),
    )


def release_stale_recovery_action_ready():
    recovery_action = Or(
        Eq(A("episode", "decision_kind"), L("get_up_exploit")),
        Eq(A("episode", "decision_kind"), L("get_up_program")),
        Eq(A("episode", "decision_kind"), L("get_up_reanchor")),
    )
    return If(
        recovery_action,
        L(0),
        P0("episode", "action_ready"),
    )


def apply_capability_goal_rule():
    return {
        "name": "hdc_apply_general_developmental_capability_goal",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "The general capability frontier supplies only a goal. "
        "The humanoid motor graph still synthesizes and verifies the action.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
        ],
        "where": And(
            Eq(P0("episode", "developmental_curriculum_active"), L(1)),
            Eq(A("episode", "phase"), L("locomotion")),
            Or(
                Not(Eq(
                    A("episode", "developmental_goal"),
                    A("capability", "goal"),
                )),
                Not(Eq(
                    A("episode", "active_developmental_capability"),
                    A("capability", "name"),
                )),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "developmental_goal", T(A("capability", "goal"))],
            ["set_attr", "episode", "active_developmental_capability", T(A("capability", "name"))],
            ["set_attr", "episode", "developmental_stage_ordinal", T(
                P0("development", "embodied_developmental_mastery_count")
            )],
            ["set_attr", "episode", "locomotion_drive_active", T(If(
                Eq(A("capability", "goal"), L("locomotion")),
                L(1),
                L(0),
            ))],
            ["set_attr", "episode", "recovery_mode", T(If(
                Or(
                    floor_development(),
                    Eq(A("capability", "goal"), L("locomotion")),
                ),
                If(
                    material_viability_reflex_active(),
                    L(1),
                    L(0),
                ),
                L(1),
            ))],
            ["set_attr", "episode", "motor_primary_ready", 0],
            ["set_attr", "episode", "motor_recovery_primary_ready", 0],
        ],
    }


def hold_pre_locomotor_residual_rule():
    return {
        "name": "hdc_hold_capability_residual_until_mastery",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
        ],
        "where": And(
            Eq(P0("episode", "developmental_curriculum_active"), L(1)),
            Eq(A("episode", "phase"), L("locomotion")),
            Not(Eq(A("capability", "goal"), L("locomotion"))),
            Not(floor_development()),
            Eq(P0("episode", "action_ready"), L(0)),
            Not(And(
                Eq(P0("episode", "recovery_mode"), L(1)),
                Eq(P0("episode", "locomotion_drive_active"), L(0)),
            )),
        ),
        "effects": [
            ["set_attr", "episode", "recovery_mode", 1],
            ["set_attr", "episode", "locomotion_drive_active", 0],
            ["set_attr", "episode", "motor_primary_ready", 0],
            ["set_attr", "episode", "motor_recovery_primary_ready", 0],
        ],
    }


def release_stale_recovery_program_rule():
    return {
        "name": "hdc_release_stale_postural_recovery_program_for_intentional_locomotion",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Intentional locomotor development may "
        "inherit an output-potent postural program from the preceding "
        "developmental stage. Release only that transient authority after "
        "the locomotor drive is active and recovery is inactive. A shared "
        "sensorimotor interrupt or reset request keeps material viability "
        "authority intact; the learned program remains retained graph data.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            [
                "development",
                "has_active_embodied_developmental_capability",
                "capability",
            ],
            [
                "episode",
                "has_active_humanoid_recovery_program",
                "program",
            ],
        ],
        "where": situated_developmental_release_gate(),
        "effects": [
            [
                "del_edge",
                "episode",
                "has_active_humanoid_recovery_program",
                "program",
            ],
            ["set_attr", "program", "status", "retained"],
            [
                "set_attr",
                "program",
                "release_reason",
                "intentional_developmental_locomotion",
            ],
            ["set_attr", "episode", "selected_motor_weight_a", 1],
            ["set_attr", "episode", "selected_motor_weight_b", 1],
            ["set_attr", "episode", "recovery_mode", 0],
            ["set_attr", "episode", "action_ready", T(
                release_stale_recovery_action_ready()
            )],
            ["set_attr", "episode", "motor_recovery_primary_ready", 0],
            ["set_attr", "episode", "recovery_entry_open", 0],
            ["set_attr", "episode", "developmental_recovery_program_release_count", T(
                Plus(
                    P0("episode", "developmental_recovery_program_release_count"),
                    L(1),
                )
            )],
        ],
    }


def release_stale_recovery_basin_rule():
    active_programs = Neighbours(
        "episode", "has_active_humanoid_recovery_program"
    )
    return {
        "name": "hdc_release_stale_postural_recovery_basin_for_intentional_locomotion",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "After transient postural program authority is gone, "
        "release the current-basin pointer so phenotype discovery can treat "
        "the present configuration as a candidate locomotor basin. Stored "
        "basins and their learned actions are retained, and material "
        "interrupts prevent this rule from firing.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            [
                "development",
                "has_active_embodied_developmental_capability",
                "capability",
            ],
            [
                "episode",
                "has_current_humanoid_recovery_basin",
                "basin",
            ],
        ],
        "where": And(
            situated_developmental_release_gate(),
            Eq(Count(active_programs), L(0)),
        ),
        "effects": [
            [
                "del_edge",
                "episode",
                "has_current_humanoid_recovery_basin",
                "basin",
            ],
            ["set_attr", "basin", "status", "retained"],
            [
                "set_attr",
                "basin",
                "release_reason",
                "intentional_developmental_locomotion",
            ],
            ["set_attr", "episode", "get_up_exploitation_start_attempt", 0],
            ["set_attr", "episode", "recovery_basin_start_attempt", 0],
            ["set_attr", "episode", "recovery_mode", 0],
            ["set_attr", "episode", "action_ready", T(
                release_stale_recovery_action_ready()
            )],
            ["set_attr", "episode", "motor_recovery_primary_ready", 0],
            ["set_attr", "episode", "developmental_recovery_basin_release_count", T(
                Plus(
                    P0("episode", "developmental_recovery_basin_release_count"),
                    L(1),
                )
            )],
        ],
    }


def mirror_mastery_count_rule():
    return {
        "name": "hdc_mirror_general_capability_mastery_for_reporting",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
        ],
        "where": Not(Eq(
            P0("episode", "developmental_stage_transition_count"),
            P0("development", "embodied_developmental_mastery_count"),
        )),
        "effects": [
            ["set_attr", "episode", "developmental_stage_transition_count", T(
                P0("development", "embodied_developmental_mastery_count")
            )],
            ["set_attr", "episode", "developmental_stage_ordinal", T(
                P0("development", "embodied_developmental_mastery_count")
            )],
        ],
    }


def learn_integer_developmental_action_affordance_rule():
    return {
        "name": "hdc_learn_integer_developmental_action_affordance",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 88,
        "batch": False,
        "comment": "Retain receipt-derived integer consequences on the opaque "
        "action model so later waves can recruit commands by developmental "
        "affordance without a pose target, scalar reward, or float policy.",
        "match": [
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "uses_humanoid_action_model", "action_model"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "development_receipt_closed"), L(1)),
            Eq(Count(Neighbours(
                "trial", "updates_humanoid_developmental_affordance"
            )), L(0)),
        ),
        "effects": [
            ["set_attr", "action_model", "experience_retained", 1],
            ["set_attr", "action_model", "development_receipt_count", T(Plus(
                P0("action_model", "development_receipt_count"), L(1)
            ))],
            ["set_attr", "action_model", "development_reversal_evidence_count", T(
                Plus(
                    P0("action_model", "development_reversal_evidence_count"),
                    P0("outcome", "development_reversal"),
                )
            )],
            ["set_attr", "action_model", "development_orientation_evidence_units", T(
                Plus(
                    P0("action_model", "development_orientation_evidence_units"),
                    P0("outcome", "development_orientation_units"),
                )
            )],
            ["set_attr", "action_model", "development_orientation_escape_units", T(
                Plus(
                    P0("action_model", "development_orientation_escape_units"),
                    Max(
                        L(0),
                        P0("outcome", "development_orientation_escape_units"),
                    ),
                )
            )],
            ["set_attr", "action_model", "development_orientation_return_units", T(
                Plus(
                    P0("action_model", "development_orientation_return_units"),
                    Max(
                        L(0),
                        Neg(P0(
                            "outcome", "development_orientation_escape_units"
                        )),
                    ),
                )
            )],
            ["set_attr", "action_model", "development_support_evidence_units", T(
                Plus(
                    P0("action_model", "development_support_evidence_units"),
                    Plus(
                        Max(L(0), P0("outcome", "development_support_gain")),
                        P0("outcome", "development_support_extent_gain"),
                    ),
                )
            )],
            ["set_attr", "action_model", "development_support_transition_evidence_count", T(
                Plus(
                    P0(
                        "action_model",
                        "development_support_transition_evidence_count",
                    ),
                    P0("outcome", "development_support_topology_changed"),
                )
            )],
            ["set_attr", "action_model", "development_stable_evidence_count", T(
                Plus(
                    P0("action_model", "development_stable_evidence_count"),
                    P0("outcome", "development_motion_nonamplifying"),
                )
            )],
            ["set_attr", "action_model", "development_translation_evidence_units", T(
                Plus(
                    P0("action_model", "development_translation_evidence_units"),
                    P0("outcome", "development_translation_units"),
                )
            )],
            ["set_attr", "action_model", "development_directed_sum_units", T(
                Plus(
                    P0("action_model", "development_directed_sum_units"),
                    P0("outcome", "development_directed_units"),
                )
            )],
            ["set_attr", "action_model", "development_lateral_sum_units", T(
                Plus(
                    P0("action_model", "development_lateral_sum_units"),
                    P0("outcome", "development_lateral_units"),
                )
            )],
            ["set_attr", "action_model", "development_elevation_sum_units", T(
                Plus(
                    P0("action_model", "development_elevation_sum_units"),
                    P0("outcome", "development_elevation_units"),
                )
            )],
            ["set_attr", "action_model", "development_orientation_escape_sum_units", T(
                Plus(
                    P0(
                        "action_model",
                        "development_orientation_escape_sum_units",
                    ),
                    P0("outcome", "development_orientation_escape_units"),
                )
            )],
            ["set_attr", "action_model", "development_latest_energy_units", T(
                P0("outcome", "development_energy_units")
            )],
            ["set_attr", "action_model", "development_latest_peak_load_units", T(
                P0("outcome", "development_peak_load_units")
            )],
            ["set_attr", "action_model", "development_latest_recoverability_units", T(
                P0("outcome", "development_recoverability_units")
            )],
            [
                "add_edge", "trial",
                "updates_humanoid_developmental_affordance", "action_model",
            ],
        ],
    }


def learn_integer_developmental_program_affordance_rule():
    return {
        "name": "hdc_learn_integer_compound_program_developmental_affordance",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 89,
        "batch": False,
        "comment": "A compound program is judged by its actual whole-body "
        "receipt, preserving nonlinear analysis-by-synthesis consequences that "
        "cannot be inferred by adding its individual command models.",
        "match": [
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "plan"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "development_receipt_closed"), L(1)),
            Eq(Count(Neighbours(
                "trial", "updates_humanoid_developmental_program_affordance"
            )), L(0)),
        ),
        "effects": [
            ["set_attr", "plan", "experience_retained", 1],
            ["set_attr", "plan", "development_receipt_count", T(Plus(
                P0("plan", "development_receipt_count"), L(1)
            ))],
            ["set_attr", "plan", "development_orientation_evidence_units", T(
                Plus(
                    P0("plan", "development_orientation_evidence_units"),
                    P0("outcome", "development_orientation_units"),
                )
            )],
            ["set_attr", "plan", "development_orientation_escape_units", T(
                Plus(
                    P0("plan", "development_orientation_escape_units"),
                    Max(
                        L(0),
                        P0("outcome", "development_orientation_escape_units"),
                    ),
                )
            )],
            ["set_attr", "plan", "development_orientation_return_units", T(
                Plus(
                    P0("plan", "development_orientation_return_units"),
                    Max(
                        L(0),
                        Neg(P0(
                            "outcome", "development_orientation_escape_units"
                        )),
                    ),
                )
            )],
            ["set_attr", "plan", "development_latest_orientation_escape_units", T(
                P0("outcome", "development_orientation_escape_units")
            )],
            ["set_attr", "plan", "development_support_evidence_units", T(
                Plus(
                    P0("plan", "development_support_evidence_units"),
                    Plus(
                        Max(L(0), P0("outcome", "development_support_gain")),
                        P0("outcome", "development_support_extent_gain"),
                    ),
                )
            )],
            ["set_attr", "plan", "development_translation_evidence_units", T(
                Plus(
                    P0("plan", "development_translation_evidence_units"),
                    P0("outcome", "development_translation_units"),
                )
            )],
            ["set_attr", "plan", "development_reversal_evidence_count", T(
                Plus(
                    P0("plan", "development_reversal_evidence_count"),
                    P0("outcome", "development_reversal"),
                )
            )],
            [
                "add_edge", "trial",
                "updates_humanoid_developmental_program_affordance", "plan",
            ],
        ],
    }


def positive_orientation_phase_candidates():
    return Filter(
        Neighbours("episode", "has_humanoid_phase_action_model"),
        "positive_orientation_phase_candidate",
        And(
            Eq(
                P0("positive_orientation_phase_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Gt(developmental_orientation_escape_score(
                "positive_orientation_phase_candidate"
            ), L(0)),
        ),
    )


def orientation_composition_authorized(capability="capability"):
    """A prior shape or a learned excess verdict may open composition."""
    return Or(
        Gt(Count(A(capability, "desired_body_state_signature")), L(0)),
        And(
            Eq(P0(capability, "classifier_effort_excess"), L(1)),
            Or(
                Eq(A(capability, "evidence_kind"), L(
                    "supported_orientation_change"
                )),
                Eq(A(capability, "evidence_kind"), L(
                    "supported_quarter_turn"
                )),
                Eq(A(capability, "evidence_kind"), L(
                    "supported_half_turn"
                )),
            ),
        ),
    )


def open_physics_counterfactual_compound_rule():
    candidates = physics_counterfactual_candidates()
    independent_pair = Exists(
        candidates,
        "physics_source",
        Exists(
            candidates,
            "physics_peer",
            Not(Eq(
                P0("physics_source", "actuator_group"),
                P0("physics_peer", "actuator_group"),
            )),
        ),
    )
    existing = Neighbours("question", "has_counterfactual_motor_program")
    return {
        "name": "hdc_open_unseen_physics_counterfactual_compound",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -106,
        "batch": False,
        "comment": "A physics residual recruits receipt-learned opaque "
        "commands from at least two independent effector groups. The result "
        "is an output-null counterfactual, not an action or a replay.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["question", "targets_learning_capability", "capability"],
        ],
        "where": And(
            Eq(A("question", "status"), L("open")),
            Eq(Count(existing), L(0)),
            independent_pair,
        ),
        "effects": [
            ["add_node", "plan", "HumanoidMotorProgram", {
                "status": "physics_counterfactual_building",
                "request_seq": T(P0("episode", "request_seq")),
                "member_count": 0,
                "primary_token": "",
                "response_frames": T(Max(
                    L(1), P0("episode", "response_frames")
                )),
                "collapse_kind": "physics_counterfactual_compound",
                "decision_kind": "developmental_metaprogram",
                "counterfactual_unseen": 1,
                "development_receipt_count": 0,
                "requires_release_envelope_guard": 1,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "episode", "has_humanoid_motor_program", "plan"],
            ["add_edge", "question", "has_counterfactual_motor_program", "plan"],
        ],
    }


def bind_physics_counterfactual_members_rule():
    candidates = physics_counterfactual_candidates()
    same_group = Filter(
        candidates,
        "physics_group_peer",
        Eq(
            P0("physics_group_peer", "actuator_group"),
            P0("candidate", "actuator_group"),
        ),
    )
    winner = Argmin(
        same_group,
        "physics_group_option",
        P0("physics_group_option", "inverse_kinematic_cost_units"),
        V("candidate"),
    )
    return {
        "name": "hdc_bind_receipt_learned_component_per_effector_group",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -105,
        "batch": True,
        "comment": "One locally learned command represents each independent "
        "group. Group count and compound width fall out of the sensed body.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["development", "has_active_embodied_inverse_kinematic_query", "query"],
            ["query", "targets_learning_capability", "capability"],
            ["question", "targets_learning_capability", "capability"],
            ["question", "has_counterfactual_motor_program", "plan"],
            ["episode", "has_humanoid_phase_action_model", "candidate"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("physics_counterfactual_building")),
            Eq(V("candidate"), winner),
            Eq(Count(Filter(
                Neighbours("plan", "includes_humanoid_phase_action_model"),
                "known_group_member",
                Eq(
                    P0("known_group_member", "actuator_group"),
                    P0("candidate", "actuator_group"),
                ),
            )), L(0)),
        ),
        "effects": [
            ["add_edge", "plan",
             "includes_humanoid_phase_action_model", "candidate"],
            ["add_edge", "plan",
             "uses_embodied_inverse_kinematic_query", "query"],
        ],
    }


def close_physics_counterfactual_compound_rule():
    members = Neighbours("plan", "includes_humanoid_phase_action_model")
    candidates = physics_counterfactual_candidates()
    represented_groups = Filter(
        candidates,
        "represented_candidate",
        Exists(
            members,
            "represented_member",
            Eq(
                P0("represented_member", "actuator_group"),
                P0("represented_candidate", "actuator_group"),
            ),
        ),
    )
    primary = Argmin(
        members, "physics_primary", P0("physics_primary", "ordinal"), V("plan")
    )
    secondary = Argmin(
        Filter(
            members,
            "physics_secondary_option",
            Not(Eq(V("physics_secondary_option"), primary)),
        ),
        "physics_secondary",
        P0("physics_secondary", "ordinal"),
        primary,
    )
    predicted_evidence = Sum(
        members,
        "physics_member",
        physics_evidence_units("capability", "physics_member"),
    )
    predicted_energy = Sum(
        members,
        "physics_member",
        integer_node_attr(
            developmental_action_model("physics_member"),
            "development_latest_energy_units",
        ),
    )
    # Concurrent contact loads may align. Summing is deliberately
    # conservative until a whole-compound receipt teaches the interaction.
    predicted_peak_load = Sum(
        members,
        "physics_member",
        integer_node_attr(
            developmental_action_model("physics_member"),
            "development_latest_peak_load_units",
        ),
    )
    predicted_recoverability = Sum(
        members,
        "physics_member",
        integer_node_attr(
            developmental_action_model("physics_member"),
            "development_latest_recoverability_units",
        ),
    )
    return {
        "name": "hdc_forward_project_unseen_compound_consequences",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -104,
        "batch": False,
        "comment": "Forward-project the unseen simultaneous program using "
        "only integer consequences learned from its components. Nonlinear "
        "interaction remains explicit uncertainty until the physical receipt.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["question", "targets_learning_capability", "capability"],
            ["question", "has_counterfactual_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("physics_counterfactual_building")),
            Gt(Count(members), L(1)),
            Eq(Count(represented_groups), Count(candidates)),
        ),
        "effects": [
            ["set_attr", "plan", "status", "counterfactual_predicted"],
            ["set_attr", "plan", "member_count", T(Count(members))],
            ["set_attr", "plan", "primary_token", T(AO(primary, "token"))],
            ["set_attr", "plan", "secondary_token", T(AO(secondary, "token"))],
            ["set_attr", "plan", "predicted_evidence_units", T(predicted_evidence)],
            ["set_attr", "plan", "predicted_energy_units", T(predicted_energy)],
            ["set_attr", "plan", "predicted_peak_load_units", T(predicted_peak_load)],
            ["set_attr", "plan", "predicted_recoverability_units", T(
                predicted_recoverability
            )],
            ["set_attr", "plan", "interaction_uncertainty_units", T(
                Count(members)
            )],
        ],
    }


def release_selected_physics_counterfactual_rule():
    members = Neighbours("plan", "includes_humanoid_phase_action_model")
    primary = Filter(
        members,
        "selected_physics_primary",
        Eq(A("selected_physics_primary", "token"), A("plan", "primary_token")),
    )
    secondary = Argmin(
        Filter(
            members,
            "selected_physics_secondary_option",
            Not(Exists(
                primary,
                "known_selected_primary",
                Eq(V("known_selected_primary"), V("selected_physics_secondary_option")),
            )),
        ),
        "selected_physics_secondary",
        P0("selected_physics_secondary", "ordinal"),
        Pick(primary),
    )
    return {
        "name": "hdc_release_selected_counterfactual_through_motor_collapse",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -103,
        "batch": False,
        "comment": "Physics proposal selection grants no actuator output. "
        "This adapter exposes the chosen compound to the ordinary single "
        "motor collapse, which still owns material-envelope interruption.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["question", "targets_learning_capability", "capability"],
            ["question", "has_selected_motor_learning_proposal", "proposal"],
            ["proposal", "proposes_counterfactual_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("proposal", "status"), L("trial_requested")),
            Eq(A("plan", "status"), L("counterfactual_predicted")),
            situated_developmental_release_gate(),
            Eq(P0("episode", "structural_interrupt_required"), L(0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(P0("episode", "action_ready"), L(0)),
            Eq(Count(Neighbours(
                "episode", "has_ready_humanoid_motor_program"
            )), L(0)),
            Gt(Count(primary), L(0)),
        ),
        "effects": [
            ["set_attr", "plan", "status", "ready"],
            ["set_attr", "plan", "request_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "plan", "open_residual_count", 1],
            ["add_edge", "episode", "has_ready_humanoid_motor_program", "plan"],
            ["set_attr", "episode", "selected_token", T(A("plan", "primary_token"))],
            ["set_attr", "episode", "selected_secondary_token", T(AO(
                secondary, "token"
            ))],
            ["set_attr", "episode", "selected_response_frames", T(Max(
                L(1), P0("plan", "response_frames")
            ))],
            ["set_attr", "episode", "selected_motor_weight_a", 1],
            ["set_attr", "episode", "selected_motor_weight_b", 1],
            *[
                ["set_attr", "episode", f"selected_predicted_{key}", 0]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "episode", "decision_kind", "developmental_metaprogram"],
            ["set_attr", "episode", "selected_collapse_kind", "physics_counterfactual_compound"],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1)
            ))],
            ["set_attr", "episode", "action_ready", 1],
        ],
    }


def open_composed_orientation_escape_bundle_rule():
    prior_bundles = Filter(
        Neighbours("episode", "has_humanoid_motor_program"),
        "prior_orientation_bundle",
        And(
            Eq(P0(
                "prior_orientation_bundle", "developmental_orientation_bundle"
            ), L(1)),
            Eq(
                P0("prior_orientation_bundle", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
        ),
    )
    return {
        "name": "hdc_open_arbitrary_width_orientation_escape_bundle",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -100,
        "batch": False,
        "comment": "Compose one command per independently discovered effector "
        "group when its own receipts predict escape from the current supported "
        "surface. The bundle width is discovered from the body, never fixed.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
        ],
        "where": And(
            orientation_composition_authorized(),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(P0("episode", "action_ready"), L(0)),
            Eq(Count(prior_bundles), L(0)),
            Gt(Count(positive_orientation_phase_candidates()), L(1)),
        ),
        "effects": [
            ["add_node", "plan", "HumanoidMotorProgram", {
                "status": "developmental_orientation_building",
                "request_seq": T(P0("episode", "request_seq")),
                "member_count": 0,
                "primary_token": "",
                "response_frames": T(Max(L(1), P0("episode", "response_frames"))),
                "collapse_kind": "developmental_orientation_bundle",
                "decision_kind": "developmental_metaprogram",
                "open_residual_count": 1,
                "developmental_orientation_bundle": 1,
                "support_phase": T(P0("episode", "current_support_phase")),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "episode", "has_humanoid_motor_program", "plan"],
        ],
    }


def bind_composed_orientation_escape_bundle_rule():
    same_group = Filter(
        positive_orientation_phase_candidates(),
        "same_orientation_group_candidate",
        Eq(
            P0("same_orientation_group_candidate", "actuator_group"),
            P0("candidate", "actuator_group"),
        ),
    )
    winner = Argmin(
        same_group,
        "ranked_orientation_group_candidate",
        Neg(developmental_orientation_escape_score(
            "ranked_orientation_group_candidate"
        )),
        V("candidate"),
    )
    return {
        "name": "hdc_bind_best_escape_command_per_effector_group",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -99,
        "batch": True,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_program", "plan"],
            ["episode", "has_humanoid_phase_action_model", "candidate"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("developmental_orientation_building")),
            Gt(developmental_orientation_escape_score("candidate"), L(0)),
            Eq(V("candidate"), winner),
            Eq(Count(Filter(
                Neighbours("plan", "includes_humanoid_phase_action_model"),
                "bound_orientation_group",
                Eq(
                    P0("bound_orientation_group", "actuator_group"),
                    P0("candidate", "actuator_group"),
                ),
            )), L(0)),
        ),
        "effects": [[
            "add_edge", "plan", "includes_humanoid_phase_action_model", "candidate"
        ]],
    }


def close_composed_orientation_escape_bundle_rule():
    members = Neighbours("plan", "includes_humanoid_phase_action_model")
    primary = Argmin(
        members, "orientation_bundle_primary",
        P0("orientation_bundle_primary", "ordinal"), V("plan")
    )
    secondary_options = Filter(
        members, "orientation_bundle_secondary_option",
        Not(Eq(V("orientation_bundle_secondary_option"), primary)),
    )
    secondary = Argmin(
        secondary_options, "orientation_bundle_secondary",
        P0("orientation_bundle_secondary", "ordinal"), primary
    )
    return {
        "name": "hdc_collapse_arbitrary_width_orientation_escape_bundle",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -98,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("developmental_orientation_building")),
            Gt(Count(members), L(1)),
        ),
        "effects": [
            ["set_attr", "plan", "status", "ready"],
            ["set_attr", "plan", "member_count", T(Count(members))],
            ["set_attr", "plan", "response_frames", T(Times(
                P0("plan", "response_frames"), Count(members)
            ))],
            ["set_attr", "plan", "primary_token", T(AO(primary, "token"))],
            ["add_edge", "episode", "has_ready_humanoid_motor_program", "plan"],
            ["set_attr", "episode", "selected_token", T(AO(primary, "token"))],
            ["set_attr", "episode", "selected_secondary_token", T(AO(
                secondary, "token"
            ))],
            ["set_attr", "episode", "selected_response_frames", T(Max(
                L(1), Times(P0("plan", "response_frames"), Count(members))
            ))],
            ["set_attr", "episode", "selected_motor_weight_a", 1],
            ["set_attr", "episode", "selected_motor_weight_b", 1],
            *[
                ["set_attr", "episode", f"selected_predicted_{key}", 0]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "episode", "decision_kind", "developmental_metaprogram"],
            ["set_attr", "episode", "selected_collapse_kind", "developmental_orientation_bundle"],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1)
            ))],
            ["set_attr", "episode", "action_ready", 1],
        ],
    }


def replay_developmental_orientation_metaprogram_rule():
    channel_count = Count(Neighbours("field", "has_somatomotor_wave_cell"))
    candidates = Filter(
        Neighbours("episode", "has_humanoid_motor_program"),
        "orientation_program_candidate",
        And(
            Or(
                Eq(A("orientation_program_candidate", "status"), L("grounded")),
                Eq(A("orientation_program_candidate", "status"), L("ready")),
            ),
            Or(
                Gt(P0(
                    "orientation_program_candidate",
                    "development_latest_orientation_escape_units",
                ), L(0)),
                And(
                    Eq(P0(
                        "orientation_program_candidate",
                        "developmental_orientation_bundle",
                    ), L(1)),
                    Lt(P0(
                        "orientation_program_candidate",
                        "developmental_replay_count",
                    ), channel_count),
                ),
            ),
            Exists(
                Neighbours(
                    "orientation_program_candidate",
                    "includes_humanoid_phase_action_model",
                ),
                "situated_orientation_member",
                Eq(
                    P0("situated_orientation_member", "support_phase"),
                    P0("episode", "current_support_phase"),
                ),
            ),
        ),
    )
    selected = Argmin(
        candidates,
        "ranked_orientation_program",
        Neg(Plus(
            P0(
                "ranked_orientation_program",
                "development_latest_orientation_escape_units",
            ),
            If(
                And(
                    Eq(P0(
                        "ranked_orientation_program",
                        "developmental_orientation_bundle",
                    ), L(1)),
                    Lt(P0(
                        "ranked_orientation_program",
                        "developmental_replay_count",
                    ), channel_count),
                ),
                channel_count,
                L(0),
            ),
        )),
        V("episode"),
    )
    members = Neighbours("plan", "includes_humanoid_phase_action_model")
    primary = Filter(
        members,
        "orientation_primary_member",
        Eq(
            A("orientation_primary_member", "token"),
            A("plan", "primary_token"),
        ),
    )
    secondary = Argmin(
        Filter(
            members,
            "orientation_secondary_member",
            Not(Exists(
                primary,
                "known_orientation_primary",
                Eq(V("known_orientation_primary"), V("orientation_secondary_member")),
            )),
        ),
        "ranked_orientation_secondary",
        P0("ranked_orientation_secondary", "ordinal"),
        Pick(primary),
    )
    return {
        "name": "hdc_hold_best_orientation_program_open_until_boundary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -97,
        "batch": False,
        "comment": "Practice is a meta-program: repeatedly reissue the best "
        "receipt-grounded compound orientation program while the developmental "
        "boundary remains open. A quarter- or half-turn receipt closes it.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "has_humanoid_motor_program", "plan"],
        ],
        "where": And(
            orientation_composition_authorized(),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(P0("episode", "action_ready"), L(0)),
            Eq(Count(Neighbours(
                "episode", "has_ready_humanoid_motor_program"
            )), L(0)),
            Gt(Count(candidates), L(0)),
            Eq(V("plan"), selected),
            Gt(Count(primary), L(0)),
        ),
        "effects": [
            ["set_attr", "plan", "status", "ready"],
            ["set_attr", "plan", "request_seq", T(P0(
                "episode", "request_seq"
            ))],
            ["set_attr", "plan", "collapse_kind", "developmental_metaprogram"],
            ["set_attr", "plan", "open_residual_count", 1],
            ["set_attr", "plan", "developmental_replay_count", T(Plus(
                P0("plan", "developmental_replay_count"), L(1)
            ))],
            [
                "add_edge", "episode", "has_ready_humanoid_motor_program", "plan"
            ],
            ["set_attr", "episode", "selected_token", T(A("plan", "primary_token"))],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(secondary, "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(Max(
                L(1), P0("plan", "response_frames")
            ))],
            ["set_attr", "episode", "selected_motor_weight_a", 1],
            ["set_attr", "episode", "selected_motor_weight_b", 1],
            *[
                ["set_attr", "episode", f"selected_predicted_{key}", 0]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "episode", "decision_kind", "developmental_metaprogram"],
            ["set_attr", "episode", "selected_collapse_kind", "developmental_metaprogram"],
            ["set_attr", "episode", "decision_seq", T(P0(
                "episode", "request_seq"
            ))],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1)
            ))],
            ["set_attr", "episode", "action_ready", 1],
        ],
    }


def request_generic_program_trajectory_rule():
    return {
        "name": "hdc_request_generic_order_n_program_trajectory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -110,
        "batch": False,
        "comment": "The developmental capability supplies a situated owner "
        "and the body's evidence window supplies its horizon. The generic "
        "trajectory faculty owns expansion and selection.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
        ],
        "where": And(
            Eq(A("capability", "developmental_ecology"), L("floor")),
            Gt(Count(A("capability", "desired_body_state_signature")), L(0)),
            Gt(P0("development", "development_evidence_window"), L(0)),
            Eq(Count(Neighbours(
                "capability", "requests_embodied_program_trajectory"
            )), L(0)),
        ),
        "effects": [
            ["add_node", "trajectory_tasks", "SystemTwoTaskSet", {
                "area": "embodied_program_trajectory",
                "enabled": 1,
                "provenance_kind": "program_trajectory_budget",
            }],
            ["add_node", "trajectory_pareto_tasks", "SystemTwoTaskSet", {
                "area": "cognitive_pareto",
                "enabled": 1,
                "provenance_kind": "program_trajectory_budget_pareto",
            }],
            ["add_node", "trajectory_escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "expand_situated_program_trajectory",
                "epoch": T(P0("episode", "request_seq")),
            }],
            [
                "add_edge", "trajectory_escalation",
                "about_context", "capability",
            ],
            [
                "add_edge", "trajectory_escalation",
                "recruits_task_set", "trajectory_tasks",
            ],
            [
                "add_edge", "trajectory_escalation",
                "recruits_task_set", "trajectory_pareto_tasks",
            ],
            ["set_attr", "development", "trajectory_horizon", T(
                P0("development", "development_evidence_window")
            )],
            [
                "add_edge", "capability",
                "requests_embodied_program_trajectory", "development",
            ],
        ],
    }


def clear_stale_generic_program_context_rule():
    return {
        "name": "hdc_clear_stale_generic_program_trajectory_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -109,
        "batch": True,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["episode", "last_verified_humanoid_motor_program", "current"],
            ["capability", "has_current_embodied_program", "stale"],
        ],
        "where": Not(Eq(V("current"), V("stale"))),
        "effects": [[
            "del_edge", "capability", "has_current_embodied_program", "stale"
        ]],
    }


def bind_generic_program_context_rule():
    return {
        "name": "hdc_bind_current_program_as_trajectory_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -108,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["episode", "last_verified_humanoid_motor_program", "current"],
        ],
        "where": And(
            Not(Exists(
                Neighbours("capability", "has_current_embodied_program"),
                "known_current",
                Eq(V("known_current"), V("current")),
            )),
        ),
        "effects": [
            ["add_node", "trajectory_context_tasks", "SystemTwoTaskSet", {
                "area": "embodied_program_trajectory",
                "enabled": 1,
                "provenance_kind": "program_trajectory_context_update",
            }],
            ["add_node", "trajectory_context_pareto_tasks", "SystemTwoTaskSet", {
                "area": "cognitive_pareto",
                "enabled": 1,
                "provenance_kind": "program_trajectory_context_pareto",
            }],
            ["add_node", "trajectory_context_escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "situated_program_context_changed",
                "epoch": T(P0("episode", "request_seq")),
            }],
            [
                "add_edge", "trajectory_context_escalation",
                "about_context", "current",
            ],
            [
                "add_edge", "trajectory_context_escalation",
                "recruits_task_set", "trajectory_context_tasks",
            ],
            [
                "add_edge", "trajectory_context_escalation",
                "recruits_task_set", "trajectory_context_pareto_tasks",
            ],
            [
                "add_edge", "capability",
                "has_current_embodied_program", "current",
            ],
        ],
    }


def publish_verified_transition_to_generic_trajectory_rule():
    return {
        "name": "hdc_publish_verified_motor_transition_to_generic_trajectory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 90,
        "batch": False,
        "comment": "Bridge one receipt-grounded predecessor/successor edge "
        "into body-neutral integer state coordinates. No prediction or host "
        "decision is introduced by this publication step.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["previous", "has_humanoid_motor_transition", "transition"],
            ["transition", "continues_with_humanoid_motor_program", "memory"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "development_receipt_closed"), L(1)),
            Eq(
                P0("trial", "request_seq"),
                P0("transition", "last_update_request_seq"),
            ),
            Eq(
                P0("trial", "request_seq"),
                P0("development", "latest_development_receipt_seq"),
            ),
            Not(Exists(
                Neighbours("capability", "has_embodied_program_transition"),
                "published_transition",
                Eq(V("published_transition"), V("transition")),
            )),
        ),
        "effects": [
            ["add_node", "trajectory_update_tasks", "SystemTwoTaskSet", {
                "area": "embodied_program_trajectory",
                "enabled": 1,
                "provenance_kind": "program_trajectory_receipt_update",
            }],
            ["add_node", "trajectory_update_pareto_tasks", "SystemTwoTaskSet", {
                "area": "cognitive_pareto",
                "enabled": 1,
                "provenance_kind": "program_trajectory_receipt_pareto",
            }],
            ["add_node", "trajectory_update_escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "verified_program_transition_changed_trajectory",
                "epoch": T(P0("trial", "request_seq")),
            }],
            [
                "add_edge", "trajectory_update_escalation",
                "about_context", "transition",
            ],
            [
                "add_edge", "trajectory_update_escalation",
                "recruits_task_set", "trajectory_update_tasks",
            ],
            [
                "add_edge", "trajectory_update_escalation",
                "recruits_task_set", "trajectory_update_pareto_tasks",
            ],
            ["set_attr", "transition", "verified", 1],
            ["set_attr", "transition", "experience_retained", 1],
            ["set_attr", "transition", "contextual_release_eligible", 0],
            ["set_attr", "transition", "pre_orientation_class", T(
                P0("outcome", "development_pre_orientation_class")
            )],
            ["set_attr", "transition", "post_orientation_class", T(
                P0("outcome", "development_post_orientation_class")
            )],
            ["set_attr", "transition", "pre_state_axis_x_units", T(
                A("outcome", "development_pre_gravity_axis_x_units")
            )],
            ["set_attr", "transition", "pre_state_axis_y_units", T(
                A("outcome", "development_pre_gravity_axis_y_units")
            )],
            ["set_attr", "transition", "pre_state_axis_z_units", T(
                A("outcome", "development_pre_gravity_axis_z_units")
            )],
            ["set_attr", "transition", "post_state_axis_x_units", T(
                A("outcome", "development_post_gravity_axis_x_units")
            )],
            ["set_attr", "transition", "post_state_axis_y_units", T(
                A("outcome", "development_post_gravity_axis_y_units")
            )],
            ["set_attr", "transition", "post_state_axis_z_units", T(
                A("outcome", "development_post_gravity_axis_z_units")
            )],
            ["set_attr", "transition", "boundary_transition_count", T(Plus(
                P0("outcome", "development_quarter_turn_transition"),
                P0("outcome", "development_half_turn_transition"),
            ))],
            ["set_attr", "transition", "energy_units", T(
                P0("outcome", "development_energy_units")
            )],
            ["set_attr", "transition", "peak_load_units", T(
                P0("outcome", "development_peak_load_units")
            )],
            ["set_attr", "transition", "integer_native_trajectory", 1],
            [
                "add_edge", "capability",
                "has_embodied_program_transition", "transition",
            ],
            [
                "add_edge", "transition",
                "starts_from_embodied_program", "previous",
            ],
            [
                "add_edge", "transition",
                "continues_with_embodied_program", "memory",
            ],
        ],
    }


def mint_developmental_program_transition_rule():
    matching = Filter(
        Neighbours("capability", "has_embodied_program_transition"),
        "known_transition",
        And(
            Exists(
                Neighbours(
                    "known_transition", "starts_from_embodied_program"
                ),
                "known_source",
                Eq(V("known_source"), V("previous")),
            ),
            Exists(
                Neighbours(
                    "known_transition", "continues_with_embodied_program"
                ),
                "known_target",
                Eq(V("known_target"), V("memory")),
            ),
        ),
    )
    return {
        "name": "hdc_mint_receipt_grounded_developmental_program_transition",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 91,
        "batch": False,
        "comment": "Developmental programs do not require the legacy gait "
        "task-context learner. Consecutive verified receipts directly mint "
        "one body-neutral integer edge before current context advances.",
        "match": [
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["capability", "has_current_embodied_program", "previous"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "memory"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "development_receipt_closed"), L(1)),
            Eq(
                P0("trial", "request_seq"),
                P0("development", "latest_development_receipt_seq"),
            ),
            Not(Eq(V("previous"), V("memory"))),
            Eq(Count(matching), L(0)),
        ),
        "effects": [
            ["add_node", "transition", "EmbodiedProgramTransition", {
                "verified": 1,
                "experience_retained": 1,
                "contextual_release_eligible": 0,
                "pre_orientation_class": T(P0(
                    "outcome", "development_pre_orientation_class"
                )),
                "post_orientation_class": T(P0(
                    "outcome", "development_post_orientation_class"
                )),
                **{
                    f"pre_state_axis_{axis}_units": T(A(
                        "outcome",
                        f"development_pre_gravity_axis_{axis}_units",
                    ))
                    for axis in ("x", "y", "z")
                },
                **{
                    f"post_state_axis_{axis}_units": T(A(
                        "outcome",
                        f"development_post_gravity_axis_{axis}_units",
                    ))
                    for axis in ("x", "y", "z")
                },
                "boundary_transition_count": T(Plus(
                    P0("outcome", "development_quarter_turn_transition"),
                    P0("outcome", "development_half_turn_transition"),
                )),
                "energy_units": T(P0(
                    "outcome", "development_energy_units"
                )),
                "peak_load_units": T(P0(
                    "outcome", "development_peak_load_units"
                )),
                "response_frames": T(P0("trial", "response_frames")),
                "receipt_seq": T(P0("trial", "request_seq")),
                "integer_native_trajectory": 1,
            }],
            [
                "add_edge", "capability",
                "has_embodied_program_transition", "transition",
            ],
            [
                "add_edge", "transition",
                "starts_from_embodied_program", "previous",
            ],
            [
                "add_edge", "transition",
                "continues_with_embodied_program", "memory",
            ],
        ],
    }


def clear_generic_program_context_from_latest_receipt_rule():
    return {
        "name": "hdc_clear_generic_program_context_from_latest_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 92,
        "batch": True,
        "match": [
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["capability", "has_current_embodied_program", "stale"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "current"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "development_receipt_closed"), L(1)),
            Eq(
                P0("trial", "request_seq"),
                P0("development", "latest_development_receipt_seq"),
            ),
            Not(Eq(V("stale"), V("current"))),
        ),
        "effects": [[
            "del_edge", "capability", "has_current_embodied_program", "stale"
        ]],
    }


def bind_generic_program_context_from_latest_receipt_rule():
    return {
        "name": "hdc_bind_generic_program_context_from_latest_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 93,
        "batch": False,
        "match": [
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "current"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "development_receipt_closed"), L(1)),
            Eq(
                P0("trial", "request_seq"),
                P0("development", "latest_development_receipt_seq"),
            ),
            Not(Exists(
                Neighbours("capability", "has_current_embodied_program"),
                "known_current",
                Eq(V("known_current"), V("current")),
            )),
        ),
        "effects": [
            ["add_node", "receipt_context_tasks", "SystemTwoTaskSet", {
                "area": "embodied_program_trajectory",
                "enabled": 1,
                "provenance_kind": "program_trajectory_receipt_context",
            }],
            ["add_node", "receipt_context_pareto_tasks", "SystemTwoTaskSet", {
                "area": "cognitive_pareto",
                "enabled": 1,
                "provenance_kind": "program_trajectory_receipt_pareto",
            }],
            ["add_node", "receipt_context_escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "receipt_program_context_changed",
                "epoch": T(P0("trial", "request_seq")),
            }],
            [
                "add_edge", "receipt_context_escalation",
                "about_context", "current",
            ],
            [
                "add_edge", "receipt_context_escalation",
                "recruits_task_set", "receipt_context_tasks",
            ],
            [
                "add_edge", "receipt_context_escalation",
                "recruits_task_set", "receipt_context_pareto_tasks",
            ],
            [
                "add_edge", "capability",
                "has_current_embodied_program", "current",
            ],
        ],
    }


def replay_selected_order_n_program_path_rule():
    members = Neighbours("memory", "includes_humanoid_phase_action_model")
    primary = Filter(
        members,
        "trajectory_primary_member",
        Eq(A("trajectory_primary_member", "token"), A("memory", "primary_token")),
    )
    secondary = Argmin(
        Filter(
            members,
            "trajectory_secondary_member",
            Not(Exists(
                primary,
                "known_trajectory_primary",
                Eq(V("known_trajectory_primary"), V("trajectory_secondary_member")),
            )),
        ),
        "ranked_trajectory_secondary",
        P0("ranked_trajectory_secondary", "ordinal"),
        Pick(primary),
    )
    return {
        "name": "hdc_replay_selected_order_n_program_path",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -107,
        "batch": False,
        "comment": "System 2 selects an output-null arbitrary-order path; "
        "each hard-real-time collapse releases only its next already-grounded "
        "compound program through the existing trial and receipt machinery.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["capability", "has_selected_embodied_program_path", "path"],
            ["capability", "has_current_embodied_program", "current"],
            ["path", "contains_embodied_program_transition", "transition"],
            ["transition", "starts_from_embodied_program", "current"],
            ["transition", "continues_with_embodied_program", "memory"],
        ],
        "where": And(
            Gt(Count(A("capability", "desired_body_state_signature")), L(0)),
            Gt(P0("path", "depth"), L(1)),
            Eq(P0("transition", "verified"), L(1)),
            Or(
                Eq(A("memory", "status"), L("grounded")),
                Eq(A("memory", "status"), L("ready")),
            ),
            Or(
                Eq(P0("memory", "memory_eligible"), L(1)),
                And(
                    Eq(P0("memory", "experience_retained"), L(1)),
                    Eq(P0(
                        "episode", "caregiver_protective_support_available"
                    ), L(1)),
                ),
            ),
            Gt(Count(primary), L(0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(P0("episode", "action_ready"), L(0)),
            Eq(Count(Neighbours(
                "episode", "has_ready_humanoid_motor_program"
            )), L(0)),
        ),
        "effects": [
            ["set_attr", "memory", "status", "ready"],
            ["set_attr", "memory", "request_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "memory", "collapse_kind", "developmental_order_n_trajectory"],
            ["set_attr", "memory", "open_residual_count", 1],
            ["add_edge", "episode", "has_ready_humanoid_motor_program", "memory"],
            ["set_attr", "episode", "selected_token", T(A("memory", "primary_token"))],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(secondary, "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(Max(
                L(1), P0("transition", "response_frames")
            ))],
            ["set_attr", "episode", "selected_motor_weight_a", 1],
            ["set_attr", "episode", "selected_motor_weight_b", 1],
            *[
                ["set_attr", "episode", f"selected_predicted_{key}", 0]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz")
            ],
            ["set_attr", "episode", "decision_kind", "developmental_metaprogram"],
            ["set_attr", "episode", "selected_collapse_kind", "developmental_order_n_trajectory"],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1)
            ))],
            ["set_attr", "episode", "action_ready", 1],
        ],
    }


def complete_selected_order_n_program_path_rule():
    return {
        "name": "hdc_complete_selected_order_n_program_path_from_receipt_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 91,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["capability", "has_selected_embodied_program_path", "path"],
            ["path", "continues_with_embodied_program", "terminal"],
            ["capability", "has_current_embodied_program", "terminal"],
        ],
        "where": Gt(P0("path", "depth"), L(1)),
        "effects": [
            [
                "del_edge", "capability",
                "has_selected_embodied_program_path", "path",
            ],
            ["set_attr", "path", "replay_count", T(Plus(
                P0("path", "replay_count"), L(1)
            ))],
            ["set_attr", "capability", "trajectory_replay_count", T(Plus(
                P0("capability", "trajectory_replay_count"), L(1)
            ))],
        ],
    }


def wave_phase_candidates(cell="cell", plan="plan"):
    return Filter(
        Neighbours(cell, "indexes_humanoid_wave_local_command"),
        "wave_candidate",
        And(
            Eq(
                P0("wave_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Not(Exists(
                Neighbours(plan, "includes_humanoid_phase_action_model"),
                "wave_existing_member",
                Eq(
                    P0("wave_existing_member", "actuator_group"),
                    P0("wave_candidate", "actuator_group"),
                ),
            )),
        ),
    )


def index_humanoid_wave_local_commands_rule():
    """Materialize the stable wave-cell to local-command join once.

    Support phase and current program membership remain dynamic filters.  The
    expensive anatomy join does not: a wave cell's effector channel and an
    opaque action model's effector channel are body-topology facts.  Holding
    that join as an edge keeps later winner selection proportional to the
    commands for one cell instead of to the episode's entire action alphabet.
    """
    indexed = Neighbours("cell", "indexes_humanoid_wave_local_command")
    return {
        "name": "hdc_index_wave_cell_local_commands",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -94,
        "batch": True,
        "comment": "Cache the immutable topology join between a generic "
        "wave cell and body-local opaque commands. Receipt-derived rank, "
        "support phase, and actuator-group exclusion stay live at selection.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_cell", "cell"],
            ["cell", "represents_embodied_effector", "cell_effector"],
            ["episode", "has_humanoid_phase_action_model", "candidate"],
            [
                "candidate", "generalizes_humanoid_action_model",
                "action_model",
            ],
            ["action_model", "models_embodied_effector", "model_effector"],
        ],
        "where": And(
            Eq(P0("action_model", "tonic_default"), L(0)),
            Eq(
                P0("cell_effector", "channel_ordinal"),
                P0("model_effector", "channel_ordinal"),
            ),
            Not(Exists(
                indexed,
                "indexed_candidate",
                Eq(V("indexed_candidate"), V("candidate")),
            )),
        ),
        "effects": [[
            "add_edge", "cell", "indexes_humanoid_wave_local_command",
            "candidate",
        ]],
    }


def passively_scaffolded_phase_candidates():
    return Filter(
        Neighbours("episode", "has_humanoid_phase_action_model"),
        "scaffolded_candidate",
        And(
            Eq(
                P0("scaffolded_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Exists(
                Neighbours(
                    "scaffolded_candidate",
                    "generalizes_humanoid_action_model",
                ),
                "scaffolded_action_model",
                And(
                    Eq(P0("scaffolded_action_model", "tonic_default"), L(0)),
                    Exists(
                        Neighbours(
                            "scaffolded_action_model",
                            "models_embodied_effector",
                        ),
                        "scaffolded_effector",
                        Exists(
                            Neighbours(
                                "field", "has_somatomotor_wave_cell"
                            ),
                            "scaffolded_cell",
                            And(
                                Gt(P0(
                                    "scaffolded_cell",
                                    "passive_exposure_count",
                                ), L(0)),
                                Exists(
                                    Neighbours(
                                        "scaffolded_cell",
                                        "represents_embodied_effector",
                                    ),
                                    "represented_scaffolded_effector",
                                    Eq(
                                        P0(
                                            "represented_scaffolded_effector",
                                            "channel_ordinal",
                                        ),
                                        P0(
                                            "scaffolded_effector",
                                            "channel_ordinal",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def unscaffolded_phase_candidates():
    return Filter(
        Neighbours("episode", "has_humanoid_phase_action_model"),
        "unscaffolded_candidate",
        And(
            Eq(
                P0("unscaffolded_candidate", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Exists(
                Neighbours(
                    "unscaffolded_candidate",
                    "generalizes_humanoid_action_model",
                ),
                "unscaffolded_action_model",
                Eq(P0("unscaffolded_action_model", "tonic_default"), L(0)),
            ),
        ),
    )


def open_scaffolded_self_attempt_rule():
    candidates = passively_scaffolded_phase_candidates()
    selected = Argmin(
        candidates,
        "scaffolded_option",
        P0("scaffolded_option", "experience_count"),
        V("episode"),
    )
    return {
        "name": "hdc_handoff_passive_body_mapping_to_self_authored_attempt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -96,
        "batch": False,
        "comment": "Passive cycling supplies a situated body map but no "
        "agency credit. The next graph collapse is a fresh self-authored test.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "has_humanoid_phase_action_model", "candidate"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("calibration")),
            Eq(P0("episode", "caregiver_scaffold_enabled"), L(1)),
            Eq(P0("episode", "caregiver_scaffold_handoff_ready"), L(1)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(P0("episode", "action_ready"), L(0)),
            Eq(Count(Neighbours(
                "episode", "has_ready_humanoid_motor_program"
            )), L(0)),
            Gt(Count(candidates), L(0)),
            Eq(V("candidate"), selected),
        ),
        "effects": [
            ["add_node", "plan", "HumanoidMotorProgram", {
                "status": "ready",
                "request_seq": T(P0("episode", "request_seq")),
                "member_count": 1,
                "primary_token": T(A("candidate", "token")),
                "response_frames": T(Max(
                    L(1), P0("episode", "response_frames")
                )),
                "collapse_kind": "scaffolded_self_attempt",
                "decision_kind": "motor_babble",
                "scaffolded_origin": 1,
                "open_residual_count": 1,
                "experience_retained": 0,
                "contextual_release_eligible": 1,
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "episode", "has_humanoid_motor_program", "plan"],
            [
                "add_edge",
                "plan",
                "includes_humanoid_phase_action_model",
                "candidate",
            ],
            [
                "add_edge",
                "episode",
                "has_ready_humanoid_motor_program",
                "plan",
            ],
            ["set_attr", "episode", "selected_token", T(
                A("candidate", "token")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                A("candidate", "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(Max(
                L(1), P0("episode", "response_frames")
            ))],
            ["set_attr", "episode", "selected_motor_weight_a", 1],
            ["set_attr", "episode", "selected_motor_weight_b", 1],
            [
                "set_attr",
                "episode",
                "selected_motor_reference_positions",
                None,
            ],
            [
                "set_attr",
                "episode",
                "selected_motor_reference_shape",
                T(A("episode", "state_motor_configuration_shape")),
            ],
            [
                "set_attr",
                "episode",
                "selected_motor_reference_kind",
                "current_sensed_configuration",
            ],
            [
                "set_attr",
                "episode",
                "motor_reference_request_seq",
                T(P0("episode", "request_seq")),
            ],
            ["set_attr", "episode", "decision_kind", "motor_babble"],
            [
                "set_attr",
                "episode",
                "selected_collapse_kind",
                "scaffolded_self_attempt",
            ],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1)
            ))],
            ["set_attr", "episode", "action_ready", 1],
        ],
    }


def open_unscaffolded_self_attempt_rule():
    candidates = unscaffolded_phase_candidates()
    selected = Argmin(
        candidates,
        "unscaffolded_option",
        P0("unscaffolded_option", "experience_count"),
        V("episode"),
    )
    rule = open_scaffolded_self_attempt_rule()
    rule["name"] = "hdc_open_self_authored_attempt_without_caregiver_permission"
    rule["order"] = -97
    rule["comment"] = (
        "Caregiver evidence can warm-start the body map but is never "
        "permission to develop. When it is absent or noncontingent, select "
        "the least-experienced situated command and learn its consequence."
    )
    rule["where"] = And(
        Eq(A("episode", "phase"), L("calibration")),
        Eq(P0("episode", "caregiver_scaffold_session_active"), L(0)),
        Or(
            Eq(P0("episode", "caregiver_scaffold_enabled"), L(0)),
            Eq(P0("episode", "caregiver_scaffold_handoff_ready"), L(0)),
        ),
        Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
        Eq(P0("episode", "action_ready"), L(0)),
        Eq(Count(Neighbours(
            "episode", "has_ready_humanoid_motor_program"
        )), L(0)),
        Gt(Count(candidates), L(0)),
        Eq(V("candidate"), selected),
    )
    for effect in rule["effects"]:
        if effect[0] == "add_node" and effect[1] == "plan":
            effect[3]["collapse_kind"] = "unscaffolded_self_attempt"
            effect[3]["scaffolded_origin"] = 0
            effect[3]["experience_retained"] = 0
            effect[3]["contextual_release_eligible"] = 1
        elif effect[0] == "set_attr" and effect[2] == "selected_collapse_kind":
            effect[3] = "unscaffolded_self_attempt"
    return rule


def request_evidence_faded_caregiver_protection_rule():
    return {
        "name": "hdc_request_caregiver_protection_for_under_evidenced_attempt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -80,
        "batch": False,
        "comment": "A caregiver changes the situated consequence envelope. "
        "Protection is requested while the active capability has less direct "
        "evidence than its body-derived window, then fades without an age or "
        "milestone constant.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["episode", "has_ready_humanoid_motor_program", "plan"],
        ],
        "where": And(
            Eq(P0(
                "episode", "caregiver_protective_support_available"
            ), L(1)),
            Eq(P0(
                "episode", "caregiver_protective_support_requested"
            ), L(0)),
            Eq(P0("episode", "action_ready"), L(1)),
            Lt(
                P0("capability", "attempt_count"),
                P0("development", "development_evidence_window"),
            ),
            Not(material_viability_reflex_active()),
        ),
        "effects": [
            ["set_attr", "episode", "caregiver_protective_support_requested", 1],
            ["set_attr", "plan", "contextual_release_eligible", 1],
            ["set_attr", "plan", "caregiver_buffered_release", 1],
            [
                "add_edge", "plan",
                "released_under_caregiver_protection", "capability",
            ],
        ],
    }


def request_calibration_caregiver_protection_rule():
    return {
        "name": "hdc_request_caregiver_protection_for_unfamiliar_calibration",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -81,
        "batch": False,
        "comment": "Before the developmental capability frontier opens, "
        "caregiver protection follows unfamiliarity of the actual selected "
        "command relative to the body-derived somatomotor field size.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "has_ready_humanoid_motor_program", "plan"],
            ["plan", "includes_humanoid_phase_action_model", "phase_model"],
            ["phase_model", "generalizes_humanoid_action_model", "action_model"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("calibration")),
            Eq(P0(
                "episode", "caregiver_protective_support_available"
            ), L(1)),
            Eq(P0(
                "episode", "caregiver_protective_support_requested"
            ), L(0)),
            Eq(P0("episode", "action_ready"), L(1)),
            Lt(
                P0("action_model", "experience_count"),
                Count(Neighbours("field", "has_somatomotor_wave_cell")),
            ),
            Not(material_viability_reflex_active()),
        ),
        "effects": [
            ["set_attr", "episode", "caregiver_protective_support_requested", 1],
            ["set_attr", "plan", "contextual_release_eligible", 1],
            ["set_attr", "plan", "caregiver_buffered_release", 1],
            [
                "add_edge", "plan",
                "released_under_caregiver_protection", "action_model",
            ],
        ],
    }


def developmental_self_attempt(trial="trial"):
    return Or(
        Eq(A(trial, "collapse_kind"), L("scaffolded_self_attempt")),
        Eq(A(trial, "collapse_kind"), L("unscaffolded_self_attempt")),
    )


def close_scaffolded_self_attempt_rule():
    return {
        "name": "hdc_close_causally_verified_developmental_self_attempt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 89,
        "batch": False,
        "comment": "The active attempt earns agency only through its own "
        "receipt; the earlier passive trajectory remains exafferent.",
        "match": [
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            developmental_self_attempt(),
            Eq(A("trial", "status"), L("adapted_online")),
            Eq(P0("outcome", "receipt_verified"), L(1)),
        ),
        "effects": [
            ["set_attr", "trial", "status", "learned"],
            ["set_attr", "trial", "developmental_self_attempt_closed", 1],
        ],
    }


def issue_unfixed_scaffolded_efference_copy_rule():
    return {
        "name": "hdc_issue_current_sensed_developmental_efference_copy",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -94,
        "batch": False,
        "comment": "Agency prediction does not require a privileged fixation. "
        "Copy the self-authored command relative to the current sensed body "
        "configuration and let the later receipt confirm it.",
        "match": [
            ["episode", "has_humanoid_motor_trial", "trial"],
        ],
        "where": And(
            developmental_self_attempt(),
            Eq(A("trial", "status"), L("issued")),
            Eq(Count(Neighbours(
                "trial", "has_humanoid_motor_efference_copy"
            )), L(0)),
        ),
        "effects": [
            ["add_node", "copy", "HumanoidMotorEfferenceCopy", {
                "request_seq": T(P0("trial", "request_seq")),
                "primary_token": T(A("trial", "token")),
                "secondary_token": T(A("trial", "secondary_token")),
                "response_frames": T(P0("trial", "response_frames")),
                "reference_kind": "current_sensed_configuration",
                "status": "issued",
                "integer_native": 1,
                "output_authority": 0,
            }],
            [
                "add_edge", "trial", "has_humanoid_motor_efference_copy",
                "copy",
            ],
        ],
    }


def distinguish_active_agency_from_passive_body_model_rule():
    return {
        "name": "hdc_reverify_passive_body_model_with_confirmed_active_agency",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": 90,
        "batch": False,
        "comment": "A passive envelope predicts what can happen to the body. "
        "Only a fresh verified receipt with a confirmed efference copy earns "
        "evidence that this graph collapse caused the consequence.",
        "match": [
            ["episode", "has_somatomotor_wave_field", "field"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "uses_humanoid_action_model", "action_model"],
            ["action_model", "models_embodied_effector", "effector"],
            ["field", "has_somatomotor_wave_cell", "cell"],
            ["cell", "represents_embodied_effector", "effector"],
            ["cell", "has_somatomotor_passive_body_model", "passive_model"],
            ["trial", "has_humanoid_motor_efference_copy", "copy"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            developmental_self_attempt(),
            Gt(P0("passive_model", "exposure_count"), L(0)),
            Eq(A("copy", "status"), L("confirmed")),
            Eq(P0("outcome", "receipt_verified"), L(1)),
            Eq(Count(Neighbours(
                "trial", "reverifies_somatomotor_passive_body_model"
            )), L(0)),
        ),
        "effects": [
            ["set_attr", "passive_model", "active_reverification_count", T(
                Plus(
                    P0("passive_model", "active_reverification_count"),
                    L(1),
                )
            )],
            ["set_attr", "passive_model", "agency_disambiguated_count", T(
                Plus(
                    P0("passive_model", "agency_disambiguated_count"),
                    L(1),
                )
            )],
            [
                "add_edge", "trial",
                "reverifies_somatomotor_passive_body_model", "passive_model",
            ],
        ],
    }


def mark_scaffolded_self_attempt_as_babble_rule():
    return {
        "name": "hdc_keep_developmental_self_attempt_as_fresh_motor_babble",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -95,
        "batch": True,
        "match": [["episode", "has_humanoid_motor_trial", "trial"]],
        "where": And(
            developmental_self_attempt(),
            Not(Eq(A("trial", "decision_kind"), L("motor_babble"))),
            Eq(A("trial", "status"), L("issued")),
        ),
        "effects": [
            ["set_attr", "trial", "decision_kind", "motor_babble"],
        ],
    }


def bind_scaffolded_unfixed_reference_rule():
    return {
        "name": "hdc_bind_current_sensed_reference_without_privileged_fixation",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -89,
        "batch": False,
        "comment": "A moving or unfamiliar body need not invent a fixed "
        "reference posture. The current sensed shape supplies coordinates "
        "with or without caregiver evidence.",
        "match": [["agent", "has_humanoid_episode", "episode"]],
        "where": And(
            Eq(P0("episode", "action_ready"), L(1)),
            Eq(P0("episode", "decision_seq"), P0("episode", "request_seq")),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "motor_reference_request_seq"),
            ),
            Eq(Count(Neighbours(
                "episode", "has_current_humanoid_motor_fixation"
            )), L(0)),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "selected_motor_reference_positions",
                None,
            ],
            [
                "set_attr",
                "episode",
                "selected_motor_reference_shape",
                T(A("episode", "state_motor_configuration_shape")),
            ],
            [
                "set_attr",
                "episode",
                "selected_motor_reference_kind",
                "current_sensed_configuration",
            ],
            [
                "set_attr",
                "episode",
                "motor_reference_request_seq",
                T(P0("episode", "request_seq")),
            ],
        ],
    }


def wave_cell_is_bound(cell="cell", plan="plan"):
    return Exists(
        Neighbours(plan, "includes_humanoid_phase_action_model"),
        "wave_bound_member",
        Exists(
            Neighbours(
                "wave_bound_member", "generalizes_humanoid_action_model"
            ),
            "wave_bound_model",
            Exists(
                Neighbours("wave_bound_model", "models_embodied_effector"),
                "wave_bound_effector",
                Exists(
                    Neighbours(cell, "represents_embodied_effector"),
                    "wave_requested_effector",
                    Eq(
                        P0("wave_bound_effector", "channel_ordinal"),
                        P0("wave_requested_effector", "channel_ordinal"),
                    ),
                ),
            ),
        ),
    )


def open_humanoid_wave_program_rule():
    return {
        "name": "hdc_open_humanoid_program_from_somatomotor_wave",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -93,
        "batch": False,
        "comment": "The generic wave supplies a parallel effector field. "
        "This bridge adds no anatomy or desired pose; it only opens the normal "
        "humanoid compound-program receipt path.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_program", "wave_program"],
        ],
        "where": And(
            Eq(A("wave_program", "status"), L("ready")),
            Eq(P0("wave_program", "epoch"), P0("episode", "request_seq")),
            Eq(
                Count(Neighbours(
                    "wave_program", "realizes_humanoid_motor_program"
                )),
                L(0),
            ),
            Eq(P0("episode", "action_ready"), L(0)),
        ),
        "effects": [
            ["add_node", "plan", "HumanoidMotorProgram", {
                "status": "somatomotor_wave_building",
                "request_seq": T(P0("episode", "request_seq")),
                "member_count": 0,
                "synthesis_yield_required": 0,
                "primary_token": "",
                "response_frames": T(Max(L(1), P0("episode", "response_frames"))),
                "collapse_kind": "spontaneous_somatomotor_wave",
                "decision_kind": "somatomotor_wave",
                "open_residual_count": T(P0("wave_program", "wavefront_width")),
                "output_authority": 0,
                "integer_native": 1,
            }],
            ["add_edge", "episode", "has_humanoid_motor_program", "plan"],
            ["add_edge", "episode", "has_active_humanoid_motor_program", "plan"],
            ["add_edge", "wave_program", "realizes_humanoid_motor_program", "plan"],
        ],
    }


def resume_humanoid_wave_program_rule():
    return {
        "name": "hdc_resume_yielded_somatomotor_wave_program",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -92,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_active_humanoid_motor_program", "plan"],
            ["episode", "resumes_humanoid_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("somatomotor_wave_building")),
            Eq(P0("plan", "synthesis_yield_required"), L(1)),
            Eq(P0("plan", "request_seq"), P0("episode", "request_seq")),
        ),
        "effects": [[
            "set_attr", "plan", "synthesis_yield_required", 0,
        ]],
    }


def bind_humanoid_wave_member_rule():
    candidates = wave_phase_candidates()
    selected = Argmin(
        candidates,
        "wave_option",
        developmental_evidence_rank("wave_option"),
        V("cell"),
    )
    return {
        "name": "hdc_bind_wave_cells_to_least_experienced_local_commands",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -91,
        "batch": False,
        "comment": "Each active topology cell chooses a currently situated "
        "opaque command using only integer consequences learned from receipts. "
        "This turns babbling into goal-relative practice while preserving one "
        "coherent compound collapse.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "projects_embodied_development", "development"],
            ["development", "has_active_embodied_developmental_capability", "capability"],
            ["development", "has_active_embodied_inverse_kinematic_query", "query"],
            ["query", "targets_learning_capability", "capability"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_program", "wave_program"],
            ["wave_program", "realizes_humanoid_motor_program", "plan"],
            ["wave_program", "includes_somatomotor_wave_cell", "cell"],
            ["cell", "indexes_humanoid_wave_local_command", "candidate"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("somatomotor_wave_building")),
            Or(
                Eq(P0("plan", "member_count"), L(0)),
                And(
                    Exists(
                        Neighbours("episode", "resumes_humanoid_motor_program"),
                        "wave_resumed_plan",
                        Eq(V("wave_resumed_plan"), V("plan")),
                    ),
                    Eq(P0("plan", "synthesis_yield_required"), L(0)),
                ),
            ),
            Gt(Count(candidates), L(0)),
            Eq(V("candidate"), selected),
            Not(Exists(
                Neighbours("plan", "includes_humanoid_phase_action_model"),
                "known_member",
                Eq(V("known_member"), V("candidate")),
            )),
        ),
        "effects": [
            ["add_edge", "plan", "includes_humanoid_phase_action_model", "candidate"],
            ["add_edge", "plan", "uses_embodied_inverse_kinematic_query", "query"],
            ["set_attr", "plan", "member_count", T(Plus(
                P0("plan", "member_count"), L(1)
            ))],
            ["set_attr", "plan", "synthesis_yield_required", 1],
            ["del_edge", "episode", "resumes_humanoid_motor_program", "plan"],
        ],
    }


def close_humanoid_wave_program_rule():
    members = Neighbours("plan", "includes_humanoid_phase_action_model")
    primary = Argmin(
        members,
        "wave_primary",
        P0("wave_primary", "ordinal"),
        V("plan"),
    )
    secondary_options = Filter(
        members,
        "wave_secondary_option",
        Not(Eq(V("wave_secondary_option"), primary)),
    )
    secondary = Argmin(
        secondary_options,
        "wave_secondary",
        P0("wave_secondary", "ordinal"),
        primary,
    )
    expandable_unbound_cells = Filter(
        Neighbours("wave_program", "includes_somatomotor_wave_cell"),
        "unbound_cell",
        And(
            Not(wave_cell_is_bound("unbound_cell")),
            Gt(Count(wave_phase_candidates("unbound_cell")), L(0)),
        ),
    )
    return {
        "name": "hdc_collapse_somatomotor_wave_to_one_compound_outcome",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "order": -90,
        "batch": False,
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_somatomotor_wave_field", "field"],
            ["field", "has_somatomotor_wave_program", "wave_program"],
            ["wave_program", "realizes_humanoid_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("somatomotor_wave_building")),
            Eq(P0("plan", "request_seq"), P0("episode", "request_seq")),
            Gt(Count(members), L(0)),
            Eq(Count(expandable_unbound_cells), L(0)),
        ),
        "effects": [
            ["set_attr", "plan", "status", "ready"],
            ["set_attr", "plan", "member_count", T(Count(members))],
            ["set_attr", "plan", "synthesis_yield_required", 0],
            ["set_attr", "plan", "primary_token", T(AO(primary, "token"))],
            ["add_edge", "episode", "has_ready_humanoid_motor_program", "plan"],
            ["del_edge", "episode", "has_active_humanoid_motor_program", "plan"],
            ["del_edge", "episode", "resumes_humanoid_motor_program", "plan"],
            ["set_attr", "episode", "selected_token", T(AO(primary, "token"))],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(secondary, "token")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("plan", "response_frames")
            )],
            ["set_attr", "episode", "selected_motor_weight_a", 1],
            ["set_attr", "episode", "selected_motor_weight_b", 1],
            ["set_attr", "episode", "selected_predicted_dzx", 0],
            ["set_attr", "episode", "selected_predicted_dzy", 0],
            ["set_attr", "episode", "selected_predicted_dwx", 0],
            ["set_attr", "episode", "selected_predicted_dwy", 0],
            ["set_attr", "episode", "selected_predicted_dvx", 0],
            ["set_attr", "episode", "selected_predicted_dvy", 0],
            ["set_attr", "episode", "selected_predicted_dvz", 0],
            ["set_attr", "episode", "decision_kind", "somatomotor_wave"],
            ["set_attr", "episode", "selected_collapse_kind", "spontaneous_somatomotor_wave"],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"), L(1)
            ))],
            ["set_attr", "episode", "action_ready", 1],
        ],
    }


def manifest() -> dict:
    return {
        "id": "humanoid_developmental_curriculum",
        "version": "3.16.0",
        "depends_on": ["humanoid_adaptation", "somatomotor_waves"],
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "description": "Thin integer humanoid transduction bridge for the "
        "general developmental graph, including goal-relative local inverse "
        "kinematics by analysis-by-synthesis over learned consequences.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": "humanoid_development:projection",
                "src": {"type": "HumanoidEpisode", "var": "episode"},
                "edge_type": "projects_embodied_development",
                "tgt": {"type": "EmbodiedDevelopmentEpisode", "var": "development"},
            },
            {
                "provenance": "humanoid_development:inverse_query",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "development"},
                "edge_type": "has_embodied_inverse_kinematic_query",
                "tgt": {"type": "EmbodiedInverseKinematicQuery", "var": "query"},
            },
            {
                "provenance": "humanoid_development:active_inverse_query",
                "src": {"type": "EmbodiedDevelopmentEpisode", "var": "development"},
                "edge_type": "has_active_embodied_inverse_kinematic_query",
                "tgt": {"type": "EmbodiedInverseKinematicQuery", "var": "query"},
            },
            {
                "provenance": "humanoid_development:inverse_query_capability",
                "src": {"type": "EmbodiedInverseKinematicQuery", "var": "query"},
                "edge_type": "targets_learning_capability",
                "tgt": {"type": "EmbodiedSituatedDevelopmentalCapability", "var": "capability"},
            },
            {
                "provenance": "humanoid_development:inverse_query_principle",
                "src": {"type": "EmbodiedInverseKinematicQuery", "var": "query"},
                "edge_type": "instantiates_inverse_kinematic_principle",
                "tgt": {"type": "EmbodiedInverseKinematicsPrinciple", "var": "principle"},
            },
            {
                "provenance": "humanoid_development:inverse_query_goal",
                "src": {"type": "EmbodiedInverseKinematicQuery", "var": "query"},
                "edge_type": "pursues_goal",
                "tgt": {"type": "Goal", "var": "goal"},
            },
            {
                "provenance": "humanoid_development:program_inverse_query",
                "src": {"type": "HumanoidMotorProgram", "var": "program"},
                "edge_type": "uses_embodied_inverse_kinematic_query",
                "tgt": {"type": "EmbodiedInverseKinematicQuery", "var": "query"},
            },
            {
                "provenance": "humanoid_development:wave_local_command_index",
                "src": {"type": "SomatomotorWaveCell", "var": "cell"},
                "edge_type": "indexes_humanoid_wave_local_command",
                "tgt": {
                    "type": "HumanoidPhaseActionModel",
                    "var": "phase_model",
                },
            },
        ],
        "rules": [
            archive_stale_inverse_kinematic_query_rule(),
            open_inverse_kinematic_query_rule(),
            bind_inverse_query_to_generic_goal_rule(),
            refresh_inverse_kinematic_query_rule(),
            score_inverse_kinematic_forward_models_rule(),
            apply_capability_goal_rule(),
            release_stale_recovery_program_rule(),
            release_stale_recovery_basin_rule(),
            hold_pre_locomotor_residual_rule(),
            request_generic_program_trajectory_rule(),
            clear_stale_generic_program_context_rule(),
            bind_generic_program_context_rule(),
            replay_selected_order_n_program_path_rule(),
            open_physics_counterfactual_compound_rule(),
            bind_physics_counterfactual_members_rule(),
            close_physics_counterfactual_compound_rule(),
            release_selected_physics_counterfactual_rule(),
            open_composed_orientation_escape_bundle_rule(),
            bind_composed_orientation_escape_bundle_rule(),
            close_composed_orientation_escape_bundle_rule(),
            replay_developmental_orientation_metaprogram_rule(),
            open_scaffolded_self_attempt_rule(),
            open_unscaffolded_self_attempt_rule(),
            request_calibration_caregiver_protection_rule(),
            request_evidence_faded_caregiver_protection_rule(),
            mark_scaffolded_self_attempt_as_babble_rule(),
            issue_unfixed_scaffolded_efference_copy_rule(),
            bind_scaffolded_unfixed_reference_rule(),
            close_scaffolded_self_attempt_rule(),
            distinguish_active_agency_from_passive_body_model_rule(),
            index_humanoid_wave_local_commands_rule(),
            open_humanoid_wave_program_rule(),
            resume_humanoid_wave_program_rule(),
            bind_humanoid_wave_member_rule(),
            close_humanoid_wave_program_rule(),
            mirror_mastery_count_rule(),
            learn_integer_developmental_action_affordance_rule(),
            learn_integer_developmental_program_affordance_rule(),
            publish_verified_transition_to_generic_trajectory_rule(),
            mint_developmental_program_transition_rule(),
            clear_generic_program_context_from_latest_receipt_rule(),
            bind_generic_program_context_from_latest_receipt_rule(),
            complete_selected_order_n_program_path_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "humanoid_developmental_curriculum.json"
    payload = manifest()
    output.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {output} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
