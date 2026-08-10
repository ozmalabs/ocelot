"""Generate graph-native whole-body kinematics learning study rules."""
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
    Abs,
    And,
    Argmin,
    Count,
    Div,
    Eq,
    Exists,
    Filter,
    Gt,
    IDiv,
    If,
    L,
    Lt,
    Minus,
    Max,
    Neighbours,
    Neg,
    Not,
    Or,
    P0,
    Plus,
    Sqrt,
    Sum,
    T,
    Times,
    V,
)


def terminal_link_rule():
    return {
        "name": "hks_infer_terminal_points_from_opaque_topology",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Infer distal kinematic points from graph topology alone. "
        "The mechanical boundary supplies parent relations, never anatomical "
        "labels or a privileged endpoint list.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_kinematic_link", "link"],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("link", "terminal"), L(0.0)),
            Eq(
                Count(Neighbours(
                    "link",
                    "has_humanoid_kinematic_child",
                )),
                L(0.0),
            ),
        ),
        "effects": [
            ["set_attr", "link", "terminal", 1.0],
        ],
    }


def global_models_for_action():
    return Neighbours("action_model", "has_humanoid_global_kinematic_model")


def phase_models_for_action():
    return Neighbours("phase_model", "has_humanoid_phase_kinematic_model")


def matching_point_models(source, point_var="point"):
    return Filter(
        source,
        "held_model",
        Eq(
            P0("held_model", "point_ordinal"),
            P0(point_var, "ordinal"),
        ),
    )


def mint_global_model_rule():
    existing = matching_point_models(global_models_for_action(), "link")
    return {
        "name": "hks_mint_global_action_point_model",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Mint one name-free endpoint displacement model for each "
        "opaque action and graph-inferred terminal point.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_action_model", "action_model"],
            ["episode", "has_humanoid_kinematic_link", "link"],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("link", "terminal"), L(1.0)),
            Eq(Count(existing), L(0.0)),
        ),
        "effects": [
            ["add_node", "model", "HumanoidGlobalKinematicModel", {
                "token": T(A("action_model", "token")),
                "action_ordinal": T(P0("action_model", "ordinal")),
                "actuator_group": T(P0("action_model", "actuator_group")),
                "point_ordinal": T(P0("link", "ordinal")),
                "experience_count": 0.0,
                "mean_rate_dx": 0.0,
                "mean_rate_dy": 0.0,
                "mean_rate_dz": 0.0,
                "coordinate_anchor_initialized": 0.0,
                "mean_pre_coordinate": 0.0,
                "mean_post_coordinate": 0.0,
                "context_experience_count": 0.0,
                "mean_context_residual_dx": 0.0,
                "mean_context_residual_dy": 0.0,
                "mean_context_residual_dz": 0.0,
                "mean_momentum_gain_dx": 0.0,
                "mean_momentum_gain_dy": 0.0,
                "mean_momentum_gain_dz": 0.0,
                "reach_basis_scored": 0.0,
                "reach_basis_projection": 0.0,
                "reach_basis_predicted_dx": 0.0,
                "reach_basis_predicted_dy": 0.0,
                "reach_basis_predicted_dz": 0.0,
                "last_update_request_seq": 0.0,
            }],
            [
                "add_edge",
                "action_model",
                "has_humanoid_global_kinematic_model",
                "model",
            ],
            [
                "add_edge",
                "model",
                "predicts_humanoid_kinematic_link",
                "link",
            ],
            [
                "add_edge",
                "episode",
                "has_humanoid_global_kinematic_model",
                "model",
            ],
        ],
    }


def mint_phase_model_rule():
    existing = matching_point_models(phase_models_for_action(), "link")
    return {
        "name": "hks_mint_support_conditioned_action_point_model",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Mint the hierarchical support-conditioned alternative "
        "over the same action and terminal-point inventory.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "phase_model",
            ],
            ["episode", "has_humanoid_kinematic_link", "link"],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("link", "terminal"), L(1.0)),
            Eq(Count(existing), L(0.0)),
        ),
        "effects": [
            ["add_node", "model", "HumanoidPhaseKinematicModel", {
                "token": T(A("phase_model", "token")),
                "action_ordinal": T(P0("phase_model", "ordinal")),
                "actuator_group": T(P0("phase_model", "actuator_group")),
                "point_ordinal": T(P0("link", "ordinal")),
                "support_phase": T(P0("phase_model", "support_phase")),
                "initialized": 0.0,
                "experience_count": 0.0,
                "mean_rate_dx": 0.0,
                "mean_rate_dy": 0.0,
                "mean_rate_dz": 0.0,
                "coordinate_anchor_initialized": 0.0,
                "mean_pre_coordinate": 0.0,
                "mean_post_coordinate": 0.0,
                "context_experience_count": 0.0,
                "mean_context_residual_dx": 0.0,
                "mean_context_residual_dy": 0.0,
                "mean_context_residual_dz": 0.0,
                "mean_momentum_gain_dx": 0.0,
                "mean_momentum_gain_dy": 0.0,
                "mean_momentum_gain_dz": 0.0,
                "reach_failure_goal_id": -1.0,
                "reach_outcome_request_seq": 0.0,
                "last_update_request_seq": 0.0,
            }],
            [
                "add_edge",
                "phase_model",
                "has_humanoid_phase_kinematic_model",
                "model",
            ],
            [
                "add_edge",
                "model",
                "predicts_humanoid_kinematic_link",
                "link",
            ],
            [
                "add_edge",
                "episode",
                "has_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
    }


def initialize_phase_model_rule():
    return {
        "name": "hks_initialize_phase_model_from_global_prior",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Initialize each support sheet from the learned global "
        "action-point relation with morphology-derived prior strength.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "phase_action",
            ],
            [
                "phase_action",
                "generalizes_humanoid_action_model",
                "action_model",
            ],
            [
                "phase_action",
                "has_humanoid_phase_kinematic_model",
                "phase_model",
            ],
            [
                "action_model",
                "has_humanoid_global_kinematic_model",
                "global_model",
            ],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(
                P0("phase_model", "point_ordinal"),
                P0("global_model", "point_ordinal"),
            ),
            Eq(P0("phase_model", "initialized"), L(0.0)),
            Gt(P0("global_model", "experience_count"), L(0.0)),
        ),
        "effects": [
            *[
                ["set_attr", "phase_model", key, T(P0("global_model", key))]
                for key in (
                    "mean_rate_dx",
                    "mean_rate_dy",
                    "mean_rate_dz",
                    "coordinate_anchor_initialized",
                    "mean_pre_coordinate",
                    "mean_post_coordinate",
                    "context_experience_count",
                    "mean_context_residual_dx",
                    "mean_context_residual_dy",
                    "mean_context_residual_dz",
                )
            ],
            [
                "set_attr",
                "phase_model",
                "experience_count",
                T(P0("policy", "support_phase_prior_strength")),
            ],
            ["set_attr", "phase_model", "initialized", 1.0],
        ],
    }


def synergy_models_for_action():
    return Neighbours(
        "synergy",
        "has_humanoid_synergy_kinematic_model",
    )


def kinematic_reprobe_candidates():
    return Filter(
        Neighbours("episode", "has_humanoid_synergy_model"),
        "candidate",
        Exists(
            Neighbours(
                "candidate",
                "has_humanoid_synergy_kinematic_model",
            ),
            "point_model",
            Lt(
                P0("point_model", "experience_count"),
                P0("episode", "support_sensor_count"),
            ),
        ),
    )


def synergy_kinematic_residual_energy(var_name):
    return Sum(
        Neighbours(
            var_name,
            "has_humanoid_synergy_kinematic_model",
        ),
        "point_model",
        Plus(*[
            Times(
                P0("point_model", f"mean_residual_rate_d{axis}"),
                P0("point_model", f"mean_residual_rate_d{axis}"),
            )
            for axis in ("x", "y", "z")
        ]),
    )


def choose_kinematic_reprobe_rule():
    candidates = kinematic_reprobe_candidates()
    best = Argmin(
        candidates,
        "candidate",
        Neg(synergy_kinematic_residual_energy("candidate")),
        V("episode"),
    )
    probe_frames = Max(
        L(1.0),
        IDiv(
            P0("episode", "response_frames"),
            P0("episode", "support_sensor_count"),
        ),
    )
    return {
        "name": "hks_curiosity_reprobes_uncertain_kinematic_interaction",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Before locomotion, re-sample each observed interaction "
        "until it has one receipt per sensed support channel, prioritizing "
        "the largest unresolved endpoint residual. The evidence target and "
        "pulse horizon are body-derived.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematics_reprobe")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "kinematics_reprobe_complete"), L(0.0)),
            Gt(Count(candidates), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(
                AO(best, "token_a")
            )],
            ["set_attr", "episode", "selected_secondary_token", T(
                AO(best, "token_b")
            )],
            ["set_attr", "episode", "selected_response_frames", T(
                probe_frames
            )],
            *[
                [
                    "set_attr",
                    "episode",
                    f"selected_predicted_{key}",
                    0.0,
                ]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy")
            ],
            ["set_attr", "episode", "decision_kind", "synergy_probe"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
        ],
    }


def close_kinematic_reprobe_rule():
    return {
        "name": "hks_close_body_derived_kinematic_reprobe",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematics_reprobe")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("episode", "kinematics_reprobe_complete"), L(0.0)),
            Eq(Count(kinematic_reprobe_candidates()), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "kinematics_reprobe_complete", 1.0],
        ],
    }


def reach_phase_models(*, active_point: bool):
    conditions = [
        Eq(
            P0("candidate", "support_phase"),
            P0("episode", "current_support_phase"),
        ),
        Gt(P0("candidate", "experience_count"), L(0.0)),
        Exists(
            Neighbours(
                "candidate",
                "predicts_humanoid_kinematic_link",
            ),
            "candidate_point",
            And(
                Eq(P0("candidate_point", "terminal"), L(1.0)),
                Eq(P0("candidate_point", "support_sensor"), L(0.0)),
            ),
        ),
    ]
    if active_point:
        conditions.append(Eq(
            P0("candidate", "point_ordinal"),
            P0("episode", "kinematic_reach_point_ordinal"),
        ))
        conditions.append(Not(Eq(
            P0("candidate", "reach_failure_goal_id"),
            P0("episode", "kinematic_reach_goal_id"),
        )))
    return Filter(
        Neighbours(
            "episode",
            "has_humanoid_phase_kinematic_model",
        ),
        "candidate",
        And(*conditions),
    )


def approved_synergy_for_point_model(var_name):
    return Exists(
        Neighbours("episode", "has_humanoid_synergy_model"),
        "candidate_synergy",
        And(
            Eq(
                A("candidate_synergy", "token_a"),
                A(var_name, "token_a"),
            ),
            Eq(
                A("candidate_synergy", "token_b"),
                A(var_name, "token_b"),
            ),
            Eq(P0("candidate_synergy", "approved"), L(1.0)),
        ),
    )


def reach_synergy_models(*, active_point: bool):
    conditions = [
        Gt(P0("candidate", "experience_count"), L(0.0)),
        approved_synergy_for_point_model("candidate"),
        Exists(
            Neighbours(
                "candidate",
                "predicts_humanoid_kinematic_link",
            ),
            "candidate_point",
            And(
                Eq(P0("candidate_point", "terminal"), L(1.0)),
                Eq(P0("candidate_point", "support_sensor"), L(0.0)),
            ),
        ),
    ]
    if active_point:
        conditions.append(Eq(
            P0("candidate", "point_ordinal"),
            P0("episode", "kinematic_reach_point_ordinal"),
        ))
    return Filter(
        Neighbours(
            "episode",
            "has_humanoid_synergy_kinematic_model",
        ),
        "candidate",
        And(*conditions),
    )


def reach_number(subject, key):
    return P0(subject, key) if isinstance(subject, str) else AO(subject, key)


def reach_text(subject, key):
    return A(subject, key) if isinstance(subject, str) else AO(subject, key)


def reach_coordinates(subject):
    return Filter(
        Neighbours(
            "episode",
            "has_humanoid_kinematic_coordinate",
        ),
        "coordinate",
        Eq(
            P0("coordinate", "ordinal"),
            reach_number(subject, "actuator_group"),
        ),
    )


def reach_coordinate_scale(subject):
    """Approximate remaining servo consequence from learned joint anchors."""
    anchor_delta = Minus(
        reach_number(subject, "mean_post_coordinate"),
        reach_number(subject, "mean_pre_coordinate"),
    )
    current_coordinate = Sum(
        reach_coordinates(subject),
        "coordinate",
        P0("coordinate", "position"),
    )
    raw_scale = If(
        Eq(anchor_delta, L(0.0)),
        L(1.0),
        Div(
            Minus(
                reach_number(subject, "mean_post_coordinate"),
                current_coordinate,
            ),
            anchor_delta,
        ),
    )
    morphology_bound = P0("episode", "support_sensor_count")
    normalized_upper_bound = Div(
        morphology_bound,
        morphology_bound,
    )
    bounded_scale = If(
        Gt(raw_scale, normalized_upper_bound),
        normalized_upper_bound,
        If(
            Lt(raw_scale, L(0.0)),
            L(0.0),
            raw_scale,
        ),
    )
    return If(
        And(
            Eq(
                reach_number(subject, "coordinate_anchor_initialized"),
                L(1.0),
            ),
            Eq(Count(reach_coordinates(subject)), L(1.0)),
            Gt(Abs(anchor_delta), L(0.0)),
        ),
        bounded_scale,
        L(1.0),
    )


def reach_single_prediction(var_name, axis):
    context_authority = Div(
        reach_number(var_name, "context_experience_count"),
        Plus(
            reach_number(var_name, "context_experience_count"),
            P0("policy", "support_phase_prior_strength"),
        ),
    )
    return Plus(
        Times(
            P0("episode", "response_frames"),
            reach_number(var_name, f"mean_rate_d{axis}"),
            reach_coordinate_scale(var_name),
        ),
        Times(
            context_authority,
            reach_number(var_name, f"mean_context_residual_d{axis}"),
            reach_coordinate_scale(var_name),
        ),
    )


def reach_base_prediction(var_name, axis):
    """Pre-context endpoint estimate used by incremental learners.

    Keeping the learner's target expression independent of the live residual
    fields prevents a recursive expression expansion in the graph evaluator.
    """
    return Times(
        P0("episode", "response_frames"),
        reach_number(var_name, f"mean_rate_d{axis}"),
        reach_coordinate_scale(var_name),
    )


def reach_momentum_prediction(var_name, axis):
    authority = Div(
        reach_number(var_name, "context_experience_count"),
        Plus(
            reach_number(var_name, "context_experience_count"),
            Times(L(2.0), P0("policy", "support_phase_prior_strength")),
        ),
    )
    return Plus(
        reach_single_prediction(var_name, axis),
        Times(
            authority,
            reach_number(var_name, f"mean_momentum_gain_d{axis}"),
            P0("episode", f"state_linear_momentum_{axis}"),
            reach_coordinate_scale(var_name),
        ),
    )


def reach_synergy_phase_components(var_name):
    return Filter(
        Neighbours(
            "episode",
            "has_humanoid_phase_kinematic_model",
        ),
        "component",
        And(
            Eq(
                P0("component", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Eq(
                P0("component", "point_ordinal"),
                reach_number(var_name, "point_ordinal"),
            ),
            Or(
                Eq(
                    A("component", "token"),
                    reach_text(var_name, "token_a"),
                ),
                Eq(
                    A("component", "token"),
                    reach_text(var_name, "token_b"),
                ),
            ),
        ),
    )


def reach_synergy_prediction(var_name, axis):
    residual_authority = Div(
        reach_number(var_name, "experience_count"),
        Plus(
            reach_number(var_name, "experience_count"),
            P0("policy", "support_phase_prior_strength"),
        ),
    )
    components = reach_synergy_phase_components(var_name)
    component_scale = Div(
        Sum(
            components,
            "component_model",
            reach_coordinate_scale("component_model"),
        ),
        Count(components),
    )
    return Times(
        P0("episode", "response_frames"),
        Plus(
            Sum(
                components,
                "component_model",
                Times(
                    P0("component_model", f"mean_rate_d{axis}"),
                    reach_coordinate_scale("component_model"),
                ),
            ),
            Times(
                residual_authority,
                reach_number(
                    var_name,
                    f"mean_residual_rate_d{axis}",
                ),
                component_scale,
            ),
        ),
    )


def reach_vector_energy(predictions):
    return Plus(*[
        Times(prediction, prediction) for prediction in predictions
    ])


def score_kinematic_reach_basis_rule():
    singles = reach_phase_models(active_point=False)
    predictions = tuple(
        reach_single_prediction("model", axis)
        for axis in ("x", "y", "z")
    )
    projection = Plus(*[
        Times(
            P0("episode", f"kinematic_reach_direction_d{axis}"),
            prediction,
        )
        for axis, prediction in zip(("x", "y", "z"), predictions)
    ])
    return {
        "name": "hks_score_reach_basis_affordances",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Materialize each eligible learned consequence once so "
        "subsequent graph searches compose compact stored intermediates.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(P0("episode", "kinematic_reach_initialized"), L(0.0)),
            Eq(P0("episode", "kinematic_reach_primary_initialized"), L(0.0)),
            Eq(P0("model", "reach_basis_scored"), L(0.0)),
            Exists(
                singles,
                "eligible",
                Eq(V("eligible"), V("model")),
            ),
        ),
        "effects": [
            ["set_attr", "model", "reach_basis_projection", T(projection)],
            *[
                [
                    "set_attr",
                    "model",
                    f"reach_basis_predicted_d{axis}",
                    T(prediction),
                ]
                for axis, prediction in zip(("x", "y", "z"), predictions)
            ],
            ["set_attr", "model", "reach_basis_scored", 1.0],
        ],
    }


def choose_primary_kinematic_reach_basis_rule():
    singles = reach_phase_models(active_point=False)
    scored = Filter(
        singles,
        "candidate",
        Eq(P0("candidate", "reach_basis_scored"), L(1.0)),
    )
    best_single = Argmin(
        scored,
        "candidate",
        Neg(P0("candidate", "reach_basis_projection")),
        V("episode"),
    )
    return {
        "name": "hks_choose_primary_reach_basis_affordance",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(P0("episode", "kinematic_reach_primary_initialized"), L(0.0)),
            Gt(Count(singles), L(0.0)),
            Eq(Count(scored), Count(singles)),
        ),
        "effects": [
            ["set_attr", "episode", "kinematic_reach_point_ordinal", T(
                AO(best_single, "point_ordinal")
            )],
            ["set_attr", "episode", "kinematic_reach_basis_token_a", T(
                AO(best_single, "token")
            )],
            ["set_attr", "episode", "kinematic_reach_basis_group_a", T(
                AO(best_single, "actuator_group")
            )],
            *[
                [
                    "set_attr",
                    "episode",
                    f"kinematic_reach_basis_a_d{axis}",
                    T(AO(best_single, f"reach_basis_predicted_d{axis}")),
                ]
                for axis in ("x", "y", "z")
            ],
            ["set_attr", "episode", "kinematic_reach_primary_initialized", 1.0],
        ],
    }


def choose_secondary_kinematic_reach_basis_rule():
    candidates = Filter(
        reach_phase_models(active_point=True),
        "candidate",
        And(
            Eq(P0("candidate", "reach_basis_scored"), L(1.0)),
            Not(Eq(
                P0("candidate", "actuator_group"),
                P0("episode", "kinematic_reach_basis_group_a"),
            )),
        ),
    )
    best_second = Argmin(
        candidates,
        "candidate",
        Neg(P0("candidate", "reach_basis_projection")),
        V("episode"),
    )
    return {
        "name": "hks_choose_secondary_reach_basis_affordance",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Or(
                Eq(
                    A("episode", "kinematic_reach_target_mode"),
                    L("composition_of_distinct_learned_affordances"),
                ),
                Eq(
                    A("episode", "kinematic_reach_target_mode"),
                    L("body_direction_at_learned_scale"),
                ),
            ),
            Eq(P0("episode", "kinematic_reach_primary_initialized"), L(1.0)),
            Eq(P0("episode", "kinematic_reach_secondary_initialized"), L(0.0)),
            Gt(Count(candidates), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "kinematic_reach_basis_token_b", T(
                AO(best_second, "token")
            )],
            *[
                [
                    "set_attr",
                    "episode",
                    f"kinematic_reach_basis_b_d{axis}",
                    T(AO(best_second, f"reach_basis_predicted_d{axis}")),
                ]
                for axis in ("x", "y", "z")
            ],
            [
                "set_attr",
                "episode",
                "kinematic_reach_secondary_initialized",
                1.0,
            ],
        ],
    }


def initialize_kinematic_reach_rule():
    composition_mode = Eq(
        A("episode", "kinematic_reach_target_mode"),
        L("composition_of_distinct_learned_affordances"),
    )
    compound_mode = Or(
        composition_mode,
        Eq(
            A("episode", "kinematic_reach_target_mode"),
            L("body_direction_at_learned_scale"),
        ),
    )
    direction_energy = Plus(*[
        Times(
            P0("episode", f"kinematic_reach_direction_d{axis}"),
            P0("episode", f"kinematic_reach_direction_d{axis}"),
        )
        for axis in ("x", "y", "z")
    ])
    primary_predictions = tuple(
        P0("episode", f"kinematic_reach_basis_a_d{axis}")
        for axis in ("x", "y", "z")
    )
    secondary_predictions = tuple(
        P0("episode", f"kinematic_reach_basis_b_d{axis}")
        for axis in ("x", "y", "z")
    )
    learned_scale = Sqrt(reach_vector_energy(primary_predictions))
    projected_target = tuple(
        Times(
            Div(
                P0("episode", f"kinematic_reach_direction_d{axis}"),
                Sqrt(direction_energy),
            ),
            learned_scale,
        )
        for axis in ("x", "y", "z")
    )
    composed_target = tuple(
        Plus(primary, secondary)
        for primary, secondary in zip(
            primary_predictions,
            secondary_predictions,
        )
    )
    targets = tuple(
            If(
                composition_mode,
                composed,
            If(
                Eq(
                    A("episode", "kinematic_reach_target_mode"),
                    L("body_direction_at_learned_scale"),
                ),
                projected,
                learned,
            ),
        )
        for composed, projected, learned in zip(
            composed_target,
            projected_target,
            primary_predictions,
        )
    )
    target_magnitude = Sqrt(reach_vector_energy(targets))
    primary_magnitude = Sqrt(reach_vector_energy(primary_predictions))
    secondary_magnitude = Sqrt(reach_vector_energy(secondary_predictions))
    coefficient_a = Div(
        Plus(*[
            Times(target, primary)
            for target, primary in zip(targets, primary_predictions)
        ]),
        Plus(reach_vector_energy(primary_predictions), L(0.0001)),
    )
    coefficient_b = Div(
        Plus(*[
            Times(target, secondary)
            for target, secondary in zip(targets, secondary_predictions)
        ]),
        Plus(reach_vector_energy(secondary_predictions), L(0.0001)),
    )
    tolerance_scale = If(
        compound_mode,
        If(
            Lt(primary_magnitude, secondary_magnitude),
            primary_magnitude,
            secondary_magnitude,
        ),
        target_magnitude,
    )
    attempt_stage_count = If(
        compound_mode,
        P0("episode", "support_sensor_count"),
        L(1.0),
    )
    terminal_count = Count(Filter(
        Neighbours("episode", "has_humanoid_kinematic_link"),
        "terminal_point",
        Eq(P0("terminal_point", "terminal"), L(1.0)),
    ))
    return {
        "name": "hks_derive_reachable_inverse_kinematic_goal",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Choose a non-support endpoint from learned projection. "
        "The curriculum may request an experienced consequence, an "
        "off-manifold direction, or the composition of two distinct learned "
        "affordances. All remain graph-derived without anatomical labels, "
        "analytic inverse kinematics or host-side distance control.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(P0("episode", "kinematic_reach_initialized"), L(0.0)),
            Eq(P0("episode", "kinematic_reach_primary_initialized"), L(1.0)),
            Or(
                Not(compound_mode),
                Eq(
                    P0("episode", "kinematic_reach_secondary_initialized"),
                    L(1.0),
                ),
            ),
            Gt(direction_energy, L(0.0)),
        ),
        "effects": [
            *[
                [
                    "set_attr",
                    "episode",
                    f"kinematic_reach_target_d{axis}",
                    T(target),
                ]
                for axis, target in zip(("x", "y", "z"), targets)
            ],
            ["set_attr", "episode", "kinematic_reach_coefficient_a", T(
                coefficient_a
            )],
            ["set_attr", "episode", "kinematic_reach_coefficient_b", T(
                coefficient_b
            )],
            *[
                [
                    "set_attr",
                    "episode",
                    f"kinematic_reach_residual_d{axis}",
                    T(target),
                ]
                for axis, target in zip(("x", "y", "z"), targets)
            ],
            ["set_attr", "episode", "kinematic_reach_initial_error", T(
                target_magnitude
            )],
            ["set_attr", "episode", "kinematic_reach_error", T(
                target_magnitude
            )],
            ["set_attr", "episode", "kinematic_reach_success_threshold", T(
                Div(
                    tolerance_scale,
                    P0("episode", "support_sensor_count"),
                )
            )],
            ["set_attr", "episode", "kinematic_reach_attempt_limit", T(
                Times(
                    terminal_count,
                    P0("episode", "support_sensor_count"),
                    attempt_stage_count,
                )
            )],
            ["set_attr", "episode", "kinematic_reach_goal_seq", T(
                Plus(P0("episode", "kinematic_reach_goal_seq"), L(1.0))
            )],
            ["set_attr", "episode", "kinematic_reach_goal_id", T(
                Plus(P0("episode", "kinematic_reach_goal_id"), L(1.0))
            )],
            ["set_attr", "episode", "kinematic_reach_initialized", 1.0],
        ],
    }


def reach_cost_from_attrs(var_name):
    return Plus(*[
        Times(
            Minus(
                P0("episode", f"kinematic_reach_residual_d{axis}"),
                P0(var_name, f"reach_predicted_d{axis}"),
            ),
            Minus(
                P0("episode", f"kinematic_reach_residual_d{axis}"),
                P0(var_name, f"reach_predicted_d{axis}"),
            ),
        )
        for axis in ("x", "y", "z")
    ])


def predict_single_reach_candidate_rule():
    predictions = tuple(
        reach_momentum_prediction("model", axis)
        for axis in ("x", "y", "z")
    )
    return {
        "name": "hks_predict_primitive_inverse_reach_candidate",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(P0("episode", "kinematic_reach_initialized"), L(1.0)),
            Eq(
                P0("model", "support_phase"),
                P0("episode", "current_support_phase"),
            ),
            Eq(
                P0("model", "point_ordinal"),
                P0("episode", "kinematic_reach_point_ordinal"),
            ),
            Gt(P0("model", "experience_count"), L(0.0)),
            Lt(
                P0("model", "reach_prediction_seq"),
                P0("episode", "kinematic_reach_goal_seq"),
            ),
        ),
        "effects": [
            *[
                [
                    "set_attr",
                    "model",
                    f"reach_predicted_d{axis}",
                    T(prediction),
                ]
                for axis, prediction in zip(
                    ("x", "y", "z"),
                    predictions,
                )
            ],
            ["set_attr", "model", "reach_prediction_seq", T(
                P0("episode", "kinematic_reach_goal_seq")
            )],
        ],
    }


def predict_synergy_reach_candidate_rule():
    predictions = tuple(
        reach_synergy_prediction("model", axis)
        for axis in ("x", "y", "z")
    )
    return {
        "name": "hks_predict_causal_compound_inverse_reach_candidate",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_synergy_kinematic_model",
                "model",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(P0("episode", "kinematic_reach_initialized"), L(1.0)),
            Eq(
                P0("model", "point_ordinal"),
                P0("episode", "kinematic_reach_point_ordinal"),
            ),
            Gt(P0("model", "experience_count"), L(0.0)),
            approved_synergy_for_point_model("model"),
            Lt(
                P0("model", "reach_prediction_seq"),
                P0("episode", "kinematic_reach_goal_seq"),
            ),
        ),
        "effects": [
            *[
                [
                    "set_attr",
                    "model",
                    f"reach_predicted_d{axis}",
                    T(prediction),
                ]
                for axis, prediction in zip(
                    ("x", "y", "z"),
                    predictions,
                )
            ],
            ["set_attr", "model", "reach_prediction_seq", T(
                P0("episode", "kinematic_reach_goal_seq")
            )],
        ],
    }


def score_reach_candidate_rule(*, compound: bool):
    edge_type = (
        "has_humanoid_synergy_kinematic_model"
        if compound
        else "has_humanoid_phase_kinematic_model"
    )
    class_name = "compound" if compound else "primitive"
    return {
        "name": f"hks_score_{class_name}_inverse_reach_candidate",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", edge_type, "model"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(
                P0("model", "reach_prediction_seq"),
                P0("episode", "kinematic_reach_goal_seq"),
            ),
            Lt(
                P0("model", "reach_score_seq"),
                P0("episode", "kinematic_reach_goal_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "model", "reach_candidate_cost", T(
                reach_cost_from_attrs("model")
            )],
            ["set_attr", "model", "reach_score_seq", T(
                P0("episode", "kinematic_reach_goal_seq")
            )],
        ],
    }


def scored_reach_candidates(*, compound: bool):
    edge_type = (
        "has_humanoid_synergy_kinematic_model"
        if compound
        else "has_humanoid_phase_kinematic_model"
    )
    conditions = [Eq(
        P0("candidate", "reach_score_seq"),
        P0("episode", "kinematic_reach_goal_seq"),
    )]
    if not compound:
        conditions.append(Not(Eq(
            P0("candidate", "reach_failure_goal_id"),
            P0("episode", "kinematic_reach_goal_id"),
        )))
    return Filter(
        Neighbours("episode", edge_type),
        "candidate",
        And(*conditions),
    )


def choose_kinematic_reach_rule():
    singles = scored_reach_candidates(compound=False)
    compounds = scored_reach_candidates(compound=True)
    best_single = Argmin(
        singles,
        "candidate",
        P0("candidate", "reach_candidate_cost"),
        V("episode"),
    )
    best_compound = Argmin(
        compounds,
        "candidate",
        P0("candidate", "reach_candidate_cost"),
        V("episode"),
    )
    use_compound = And(
        Gt(Count(compounds), L(0.0)),
        Or(
            Eq(
                A("episode", "kinematic_reach_target_mode"),
                L("body_direction_at_learned_scale"),
            ),
            Gt(
                AO(best_single, "reach_candidate_cost"),
                AO(best_compound, "reach_candidate_cost"),
            ),
        ),
    )
    selected_predictions = tuple(
        If(
            use_compound,
            AO(best_compound, f"reach_predicted_d{axis}"),
            AO(best_single, f"reach_predicted_d{axis}"),
        )
        for axis in ("x", "y", "z")
    )
    return {
        "name": "hks_analysis_by_synthesis_selects_inverse_reach",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Invert learned forward endpoint models by comparing the "
        "predicted residual after every eligible primitive and causally "
        "verified compound. Selection remains over opaque actuator tokens.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(P0("episode", "kinematic_reach_initialized"), L(1.0)),
            Eq(P0("episode", "kinematic_reach_complete"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(Count(singles), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(If(
                use_compound,
                AO(best_compound, "token_a"),
                AO(best_single, "token"),
            ))],
            ["set_attr", "episode", "selected_secondary_token", T(If(
                use_compound,
                AO(best_compound, "token_b"),
                AO(best_single, "token"),
            ))],
            ["set_attr", "episode", "selected_response_frames", T(
                P0("episode", "response_frames")
            )],
            *[
                [
                    "set_attr",
                    "episode",
                    f"selected_predicted_{key}",
                    0.0,
                ]
                for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy")
            ],
            *[
                [
                    "set_attr",
                    "episode",
                    f"kinematic_reach_selected_predicted_d{axis}",
                    T(prediction),
                ]
                for axis, prediction in zip(
                    ("x", "y", "z"),
                    selected_predictions,
                )
            ],
            ["set_attr", "episode", "kinematic_reach_selected_compound", T(
                If(use_compound, L(1.0), L(0.0))
            )],
            ["set_attr", "episode", "selected_motor_weight_a", T(
                If(use_compound, P0("episode", "kinematic_reach_coefficient_a"), L(1.0))
            )],
            ["set_attr", "episode", "selected_motor_weight_b", T(
                If(use_compound, P0("episode", "kinematic_reach_coefficient_b"), L(1.0))
            )],
            ["set_attr", "episode", "decision_kind", "kinematic_reach"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
        ],
    }


def bind_reach_trial_synergy_rule():
    return {
        "name": "hks_bind_inverse_reach_trial_to_causal_synergy",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_policy", "policy"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["episode", "has_humanoid_synergy_model", "synergy"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(A("trial", "decision_kind"), L("kinematic_reach")),
            Or(
                And(
                    Eq(A("trial", "token"), A("synergy", "token_a")),
                    Eq(
                        A("trial", "secondary_token"),
                        A("synergy", "token_b"),
                    ),
                ),
                And(
                    Eq(A("trial", "token"), A("synergy", "token_b")),
                    Eq(
                        A("trial", "secondary_token"),
                        A("synergy", "token_a"),
                    ),
                ),
            ),
            Eq(P0("synergy", "approved"), L(1.0)),
        ),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_synergy_model",
                "synergy",
            ],
        ],
    }


def bind_reach_trial_secondary_phase_rule():
    return {
        "name": "hks_bind_inverse_reach_secondary_endpoint_models",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_policy", "policy"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "phase_action",
            ],
            [
                "phase_action",
                "has_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("kinematic_reach")),
            Eq(
                A("phase_action", "token"),
                A("trial", "secondary_token"),
            ),
            Eq(
                P0("phase_action", "support_phase"),
                P0("trial", "support_phase"),
            ),
        ),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
    }


def bind_reach_trial_secondary_global_rule():
    return {
        "name": "hks_bind_inverse_reach_secondary_global_models",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "episode",
                "has_humanoid_action_model",
                "action_model",
            ],
            [
                "action_model",
                "has_humanoid_global_kinematic_model",
                "model",
            ],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("kinematic_reach")),
            Eq(
                A("action_model", "token"),
                A("trial", "secondary_token"),
            ),
        ),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_global_kinematic_model",
                "model",
            ],
        ],
    }


def measure_kinematic_reach_rule():
    new_achieved = {
        axis: Plus(
            P0("episode", f"kinematic_reach_achieved_d{axis}"),
            P0("transition", f"observed_d{axis}"),
        )
        for axis in ("x", "y", "z")
    }
    new_residual = {
        axis: Minus(
            P0("episode", f"kinematic_reach_target_d{axis}"),
            new_achieved[axis],
        )
        for axis in ("x", "y", "z")
    }
    error = Sqrt(Plus(*[
        Times(residual, residual) for residual in new_residual.values()
    ]))
    attempt_count = Plus(
        P0("episode", "kinematic_reach_attempt_count"),
        L(1.0),
    )
    success = Not(Gt(
        error,
        P0("episode", "kinematic_reach_success_threshold"),
    ))
    exhausted = Not(Lt(
        attempt_count,
        P0("episode", "kinematic_reach_attempt_limit"),
    ))
    return {
        "name": "hks_close_inverse_reach_from_endpoint_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Accumulate only the selected terminal point's measured "
        "body-relative motion. Success and exhaustion are graph verdicts over "
        "the receipt, never simulator-side IK or distance control.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "has_humanoid_kinematic_transition",
                "transition",
            ],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("kinematic_reach")),
            Eq(P0("transition", "receipt_verified"), L(1.0)),
            Eq(P0("transition", "external_event_frames"), L(0.0)),
            Eq(
                P0("transition", "point_ordinal"),
                P0("episode", "kinematic_reach_point_ordinal"),
            ),
            Lt(
                P0("episode", "kinematic_reach_last_receipt_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "kinematic_reach_previous_error", T(
                P0("episode", "kinematic_reach_error")
            )],
            ["set_attr", "episode", "kinematic_reach_success", T(
                If(success, L(1.0), L(0.0))
            )],
            ["set_attr", "episode", "kinematic_reach_complete", T(
                If(Or(success, exhausted), L(1.0), L(0.0))
            )],
            ["set_attr", "episode", "kinematic_reach_error", T(error)],
            ["set_attr", "episode", "kinematic_reach_goal_seq", T(
                If(
                    Or(success, exhausted),
                    P0("episode", "kinematic_reach_goal_id"),
                    Plus(
                        P0("episode", "kinematic_reach_goal_seq"),
                        L(1.0),
                    ),
                )
            )],
            ["set_attr", "episode", "kinematic_reach_last_receipt_seq", T(
                P0("trial", "request_seq")
            )],
            ["set_attr", "trial", "status", "kinematic_reach_measured"],
            *[
                [
                    "set_attr",
                    "episode",
                    f"kinematic_reach_residual_d{axis}",
                    T(value),
                ]
                for axis, value in new_residual.items()
            ],
            *[
                [
                    "set_attr",
                    "episode",
                    f"kinematic_reach_achieved_d{axis}",
                    T(value),
                ]
                for axis, value in new_achieved.items()
            ],
            ["set_attr", "episode", "kinematic_reach_attempt_count", T(
                attempt_count
            )],
        ],
    }


def record_reach_candidate_outcome_rule():
    return {
        "name": "hks_record_reach_candidate_outcome_frontier",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Retain a receipt-backed negative outcome for the current "
        "goal so analysis by synthesis explores another learned candidate "
        "before revisiting the worsened command.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_phase_kinematic_model",
                "model",
            ],
            [
                "trial",
                "has_humanoid_kinematic_transition",
                "transition",
            ],
        ],
        "where": And(
            Eq(A("trial", "decision_kind"), L("kinematic_reach")),
            Eq(A("trial", "status"), L("kinematic_reach_measured")),
            Eq(P0("transition", "receipt_verified"), L(1.0)),
            Eq(
                P0("model", "point_ordinal"),
                P0("transition", "point_ordinal"),
            ),
            Lt(
                P0("model", "reach_outcome_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            [
                "set_attr",
                "model",
                "reach_failure_goal_id",
                T(If(
                    Gt(
                        P0("episode", "kinematic_reach_error"),
                        P0("episode", "kinematic_reach_previous_error"),
                    ),
                    P0("episode", "kinematic_reach_goal_seq"),
                    L(-1.0),
                )),
            ],
            [
                "set_attr",
                "model",
                "reach_outcome_request_seq",
                T(P0("trial", "request_seq")),
            ],
        ],
    }


def clear_exhausted_reach_candidate_frontier_rule():
    candidates = reach_phase_models(active_point=True)
    return {
        "name": "hks_clear_exhausted_reach_candidate_frontier",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(P0("episode", "kinematic_reach_complete"), L(0.0)),
            Eq(P0("model", "point_ordinal"), P0(
                "episode", "kinematic_reach_point_ordinal"
            )),
            Eq(Count(candidates), L(0.0)),
            Gt(P0("model", "experience_count"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "model", "reach_failure_goal_id", L(-1.0)],
        ],
    }


def mint_synergy_model_rule():
    existing = matching_point_models(synergy_models_for_action(), "link")
    return {
        "name": "hks_mint_observed_synergy_point_residual_model",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Only a causally probed actuator pair receives an endpoint "
        "interaction model; the graph does not materialize the combinatorial "
        "pair space in advance.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_synergy_model", "synergy"],
            ["episode", "has_humanoid_kinematic_link", "link"],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("link", "terminal"), L(1.0)),
            Gt(P0("synergy", "experience_count"), L(0.0)),
            Eq(Count(existing), L(0.0)),
        ),
        "effects": [
            ["add_node", "model", "HumanoidSynergyKinematicModel", {
                "token_a": T(A("synergy", "token_a")),
                "token_b": T(A("synergy", "token_b")),
                "point_ordinal": T(P0("link", "ordinal")),
                "experience_count": 0.0,
                "mean_residual_rate_dx": 0.0,
                "mean_residual_rate_dy": 0.0,
                "mean_residual_rate_dz": 0.0,
                "last_update_request_seq": 0.0,
            }],
            [
                "add_edge",
                "synergy",
                "has_humanoid_synergy_kinematic_model",
                "model",
            ],
            [
                "add_edge",
                "model",
                "predicts_humanoid_kinematic_link",
                "link",
            ],
            [
                "add_edge",
                "episode",
                "has_humanoid_synergy_kinematic_model",
                "model",
            ],
        ],
    }


def arbitration_models():
    return Neighbours("episode", "has_humanoid_kinematic_arbitration_model")


def mint_arbitration_model_rule(*, compound: bool):
    bundle_class = 1.0 if compound else 0.0
    existing = Filter(
        arbitration_models(),
        "held_model",
        And(
            Eq(
                P0("held_model", "point_ordinal"),
                P0("link", "ordinal"),
            ),
            Eq(
                P0("held_model", "support_phase"),
                P0("phase_action", "support_phase"),
            ),
            Eq(P0("held_model", "bundle_class"), L(bundle_class)),
        ),
    )
    class_name = "compound" if compound else "primitive"
    return {
        "name": f"hks_mint_{class_name}_kinematic_arbitration_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Mint one approach-selection context per terminal point, "
        "support regime and composition class. No action semantics enter it.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_phase_action_model",
                "phase_action",
            ],
            ["episode", "has_humanoid_kinematic_link", "link"],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("link", "terminal"), L(1.0)),
            Eq(Count(existing), L(0.0)),
        ),
        "effects": [
            ["add_node", "model", "HumanoidKinematicArbitrationModel", {
                "point_ordinal": T(P0("link", "ordinal")),
                "support_phase": T(
                    P0("phase_action", "support_phase")
                ),
                "bundle_class": bundle_class,
                "sample_count": 0.0,
                "mean_global_error": 0.0,
                "mean_phase_error": 0.0,
                "mean_interaction_error": 0.0,
                "global_selection_count": 0.0,
                "phase_selection_count": 0.0,
                "interaction_selection_count": 0.0,
            }],
            [
                "add_edge",
                "episode",
                "has_humanoid_kinematic_arbitration_model",
                "model",
            ],
            [
                "add_edge",
                "model",
                "arbitrates_humanoid_kinematic_link",
                "link",
            ],
        ],
    }


def bind_trial_global_model_rule():
    return {
        "name": "hks_bind_trial_global_point_models",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "uses_humanoid_action_model", "action_model"],
            [
                "action_model",
                "has_humanoid_global_kinematic_model",
                "model",
            ],
        ],
        "where": Eq(P0("episode", "kinematics_study_active"), L(1.0)),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_global_kinematic_model",
                "model",
            ],
        ],
    }


def bind_program_global_model_rule():
    return {
        "name": "hks_bind_program_members_to_global_point_models",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_phase_action_model",
                "phase_action",
            ],
            [
                "phase_action",
                "generalizes_humanoid_action_model",
                "action_model",
            ],
            [
                "action_model",
                "has_humanoid_global_kinematic_model",
                "model",
            ],
        ],
        "where": Eq(P0("episode", "kinematics_study_active"), L(1.0)),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_global_kinematic_model",
                "model",
            ],
        ],
    }


def bind_trial_phase_model_rule():
    return {
        "name": "hks_bind_trial_support_conditioned_point_models",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "uses_humanoid_action_model", "action_model"],
            [
                "phase_action",
                "generalizes_humanoid_action_model",
                "action_model",
            ],
            [
                "phase_action",
                "has_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(
                P0("phase_action", "support_phase"),
                P0("trial", "support_phase"),
            ),
        ),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
    }


def bind_program_phase_model_rule():
    return {
        "name": "hks_bind_program_support_conditioned_point_models",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_phase_action_model",
                "phase_action",
            ],
            [
                "phase_action",
                "has_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
        "where": Eq(P0("episode", "kinematics_study_active"), L(1.0)),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_phase_kinematic_model",
                "model",
            ],
        ],
    }


def bind_trial_synergy_model_rule():
    return {
        "name": "hks_bind_trial_observed_synergy_point_models",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "uses_humanoid_synergy_model", "synergy"],
            [
                "synergy",
                "has_humanoid_synergy_kinematic_model",
                "model",
            ],
        ],
        "where": Eq(P0("episode", "kinematics_study_active"), L(1.0)),
        "effects": [
            [
                "add_edge",
                "trial",
                "uses_humanoid_synergy_kinematic_model",
                "model",
            ],
        ],
    }


def bind_transition_arbitration_model_rule():
    linked = Neighbours(
        "transition",
        "uses_humanoid_kinematic_arbitration_model",
    )
    return {
        "name": "hks_bind_receipt_to_exact_arbitration_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Materialize the exact point/support/composition context "
        "once so later reliability updates wake only their local receipts.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            [
                "episode",
                "has_humanoid_kinematic_arbitration_model",
                "model",
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "has_humanoid_kinematic_transition",
                "transition",
            ],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(Count(linked), L(0.0)),
            Eq(
                P0("model", "point_ordinal"),
                P0("transition", "point_ordinal"),
            ),
            Eq(
                P0("model", "support_phase"),
                P0("transition", "support_phase"),
            ),
            Eq(
                P0("model", "bundle_class"),
                If(
                    Gt(
                        P0("transition", "bundle_member_count"),
                        L(1.0),
                    ),
                    L(1.0),
                    L(0.0),
                ),
            ),
        ),
        "effects": [
            [
                "add_edge",
                "transition",
                "uses_humanoid_kinematic_arbitration_model",
                "model",
            ],
        ],
    }


def models_for_transition(edge_type):
    return Filter(
        Neighbours("trial", edge_type),
        "candidate_model",
        Eq(
            P0("candidate_model", "point_ordinal"),
            P0("transition", "point_ordinal"),
        ),
    )


def predicted_axis(models, axis):
    return Times(
        P0("transition", "response_frames"),
        Sum(
            models,
            "prediction_model",
            P0("prediction_model", f"mean_rate_d{axis}"),
        ),
    )


def interaction_predicted_axis(
    phase_models,
    synergy_models,
    axis,
):
    return Plus(
        predicted_axis(phase_models, axis),
        Times(
            P0("transition", "response_frames"),
            Sum(
                synergy_models,
                "interaction_model",
                Times(
                    Div(
                        P0("interaction_model", "experience_count"),
                        Plus(
                            P0(
                                "interaction_model",
                                "experience_count",
                            ),
                            P0(
                                "policy",
                                "support_phase_prior_strength",
                            ),
                        ),
                    ),
                    P0(
                        "interaction_model",
                        f"mean_residual_rate_d{axis}",
                    ),
                ),
            ),
        ),
    )


def prediction_error(predictions):
    return Sqrt(Plus(*[
        Times(
            Minus(
                P0("transition", f"observed_d{axis}"),
                prediction,
            ),
            Minus(
                P0("transition", f"observed_d{axis}"),
                prediction,
            ),
        )
        for axis, prediction in zip(("x", "y", "z"), predictions)
    ]))


def measure_prequential_error_rule():
    global_models = models_for_transition(
        "uses_humanoid_global_kinematic_model"
    )
    phase_models = models_for_transition(
        "uses_humanoid_phase_kinematic_model"
    )
    synergy_models = models_for_transition(
        "uses_humanoid_synergy_kinematic_model"
    )
    global_predictions = tuple(
        predicted_axis(global_models, axis) for axis in ("x", "y", "z")
    )
    phase_predictions = tuple(
        predicted_axis(phase_models, axis) for axis in ("x", "y", "z")
    )
    interaction_predictions = tuple(
        interaction_predicted_axis(
            phase_models,
            synergy_models,
            axis,
        )
        for axis in ("x", "y", "z")
    )
    return {
        "name": "hks_measure_paired_prequential_kinematic_error",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Score both approaches before either receives this exact "
        "receipt. Simulator geometry is never used as a model or selector.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "has_humanoid_kinematic_transition",
                "transition",
            ],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("transition", "receipt_verified"), L(1.0)),
            Eq(P0("transition", "external_event_frames"), L(0.0)),
            Eq(P0("transition", "prediction_measured"), L(0.0)),
            Gt(Count(global_models), L(0.0)),
            Gt(Count(phase_models), L(0.0)),
        ),
        "effects": [
            *[
                ["set_attr", "transition", f"global_predicted_d{axis}", T(
                    prediction
                )]
                for axis, prediction in zip(
                    ("x", "y", "z"),
                    global_predictions,
                )
            ],
            *[
                ["set_attr", "transition", f"phase_predicted_d{axis}", T(
                    prediction
                )]
                for axis, prediction in zip(
                    ("x", "y", "z"),
                    phase_predictions,
                )
            ],
            *[
                [
                    "set_attr",
                    "transition",
                    f"interaction_predicted_d{axis}",
                    T(prediction),
                ]
                for axis, prediction in zip(
                    ("x", "y", "z"),
                    interaction_predictions,
                )
            ],
            ["set_attr", "transition", "global_prediction_error", T(
                prediction_error(global_predictions)
            )],
            ["set_attr", "transition", "phase_prediction_error", T(
                prediction_error(phase_predictions)
            )],
            ["set_attr", "transition", "interaction_prediction_error", T(
                prediction_error(interaction_predictions)
            )],
            ["set_attr", "transition", "global_model_count", T(
                Count(global_models)
            )],
            ["set_attr", "transition", "phase_model_count", T(
                Count(phase_models)
            )],
            ["set_attr", "transition", "synergy_model_count", T(
                Count(synergy_models)
            )],
            ["set_attr", "transition", "global_experience", T(
                Sum(
                    global_models,
                    "experience_model",
                    P0("experience_model", "experience_count"),
                )
            )],
            ["set_attr", "transition", "phase_experience", T(
                Sum(
                    phase_models,
                    "experience_model",
                    P0("experience_model", "experience_count"),
                )
            )],
            ["set_attr", "transition", "synergy_experience", T(
                Sum(
                    synergy_models,
                    "experience_model",
                    P0("experience_model", "experience_count"),
                )
            )],
            ["set_attr", "transition", "prediction_measured", 1.0],
        ],
    }


def update_model_rule(*, phase: bool):
    edge_type = (
        "uses_humanoid_phase_kinematic_model"
        if phase
        else "uses_humanoid_global_kinematic_model"
    )
    model_type = (
        "support-conditioned" if phase else "global"
    )
    count = Plus(P0("model", "experience_count"), L(1.0))
    context_count = Plus(
        P0("model", "context_experience_count"),
        L(1.0),
    )
    context_sample = Eq(
        A("trial", "decision_kind"),
        L("kinematic_reach"),
    )
    initialize_coordinate_anchor = And(
        Eq(P0("transition", "actuator_coordinate_observed"), L(1.0)),
        Eq(P0("model", "coordinate_anchor_initialized"), L(0.0)),
    )
    return {
        "name": f"hks_update_{model_type}_model_from_single_action_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Only isolated action receipts identify primitive endpoint "
        "effects. Compound receipts remain held-out composition tests.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_policy", "policy"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", edge_type, "model"],
            [
                "trial",
                "has_humanoid_kinematic_transition",
                "transition",
            ],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("transition", "prediction_measured"), L(1.0)),
            Eq(P0("transition", "bundle_member_count"), L(1.0)),
            Eq(
                P0("model", "point_ordinal"),
                P0("transition", "point_ordinal"),
            ),
            Lt(
                P0("model", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            *[
                ["set_attr", "model", f"mean_rate_d{axis}", T(
                    Plus(
                        P0("model", f"mean_rate_d{axis}"),
                        Div(
                            Minus(
                                Div(
                                    P0("transition", f"observed_d{axis}"),
                                    P0("transition", "response_frames"),
                                ),
                                P0("model", f"mean_rate_d{axis}"),
                            ),
                            count,
                        ),
                    )
                )]
                for axis in ("x", "y", "z")
            ],
            [
                "set_attr",
                "model",
                "context_experience_count",
                T(If(
                    context_sample,
                    context_count,
                    P0("model", "context_experience_count"),
                )),
            ],
            *[
                [
                    "set_attr",
                    "model",
                    f"mean_context_residual_d{axis}",
                    T(If(
                        context_sample,
                        Plus(
                            P0("model", f"mean_context_residual_d{axis}"),
                            Div(
                                Minus(
                                    P0("transition", f"observed_d{axis}"),
                                    reach_base_prediction("model", axis),
                                ),
                                context_count,
                            ),
                        ),
                        P0("model", f"mean_context_residual_d{axis}"),
                    )),
                ]
                for axis in ("x", "y", "z")
            ],
            [
                "set_attr",
                "model",
                "mean_pre_coordinate",
                T(If(
                    initialize_coordinate_anchor,
                    P0("transition", "pre_actuator_coordinate"),
                    P0("model", "mean_pre_coordinate"),
                )),
            ],
            [
                "set_attr",
                "model",
                "mean_post_coordinate",
                T(If(
                    initialize_coordinate_anchor,
                    P0("transition", "post_actuator_coordinate"),
                    P0("model", "mean_post_coordinate"),
                )),
            ],
            [
                "set_attr",
                "model",
                "coordinate_anchor_initialized",
                T(If(
                    initialize_coordinate_anchor,
                    L(1.0),
                    P0("model", "coordinate_anchor_initialized"),
                )),
            ],
            ["set_attr", "model", "experience_count", T(count)],
            ["set_attr", "model", "last_update_request_seq", T(
                P0("trial", "request_seq")
            )],
        ],
    }


def update_momentum_gain_rule(*, phase: bool):
    edge_type = (
        "uses_humanoid_phase_kinematic_model"
        if phase else "uses_humanoid_global_kinematic_model"
    )
    count = Plus(P0("model", "context_experience_count"), L(1.0))
    return {
        "name": f"hks_update_{'phase' if phase else 'global'}_momentum_gain",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Learn momentum-conditioned endpoint gain only from "
        "reach receipts; calibration remains unaffected.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", edge_type, "model"],
            ["trial", "has_humanoid_kinematic_transition", "transition"],
        ],
        "where": And(
            Eq(A("episode", "phase"), L("kinematic_reach")),
            Eq(A("trial", "decision_kind"), L("kinematic_reach")),
            Eq(P0("transition", "prediction_measured"), L(1.0)),
            Eq(P0("transition", "bundle_member_count"), L(1.0)),
            Lt(P0("model", "last_update_request_seq"),
               P0("trial", "request_seq")),
        ),
        "effects": [
            *[
                ["set_attr", "model", f"mean_momentum_gain_d{axis}", T(
                    If(
                        Gt(Abs(P0("episode", f"state_linear_momentum_{axis}")), L(0.0001)),
                        Plus(
                            P0("model", f"mean_momentum_gain_d{axis}"),
                            Div(
                                Minus(
                                    P0("transition", f"observed_d{axis}"),
                                    reach_base_prediction("model", axis),
                                ),
                                Times(
                                    count,
                                    P0("episode", f"state_linear_momentum_{axis}"),
                                ),
                            ),
                        ),
                        P0("model", f"mean_momentum_gain_d{axis}"),
                    )
                )]
                for axis in ("x", "y", "z")
            ],
            ["set_attr", "model", "last_update_request_seq", T(
                P0("trial", "request_seq")
            )],
        ],
    }


def update_synergy_model_rule():
    count = Plus(P0("model", "experience_count"), L(1.0))
    return {
        "name": "hks_update_synergy_endpoint_interaction_residual",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Learn only the endpoint residual left after the "
        "support-conditioned additive prediction. This preserves reusable "
        "primitive structure while representing measured non-additivity.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "uses_humanoid_synergy_kinematic_model",
                "model",
            ],
            [
                "trial",
                "has_humanoid_kinematic_transition",
                "transition",
            ],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("transition", "prediction_measured"), L(1.0)),
            Gt(P0("transition", "bundle_member_count"), L(1.0)),
            Eq(
                P0("model", "point_ordinal"),
                P0("transition", "point_ordinal"),
            ),
            Lt(
                P0("model", "last_update_request_seq"),
                P0("trial", "request_seq"),
            ),
        ),
        "effects": [
            *[
                [
                    "set_attr",
                    "model",
                    f"mean_residual_rate_d{axis}",
                    T(Plus(
                        P0(
                            "model",
                            f"mean_residual_rate_d{axis}",
                        ),
                        Div(
                            Minus(
                                Div(
                                    Minus(
                                        P0(
                                            "transition",
                                            f"observed_d{axis}",
                                        ),
                                        P0(
                                            "transition",
                                            f"phase_predicted_d{axis}",
                                        ),
                                    ),
                                    P0(
                                        "transition",
                                        "response_frames",
                                    ),
                                ),
                                P0(
                                    "model",
                                    f"mean_residual_rate_d{axis}",
                                ),
                            ),
                            count,
                        ),
                    )),
                ]
                for axis in ("x", "y", "z")
            ],
            ["set_attr", "model", "experience_count", T(count)],
            ["set_attr", "model", "last_update_request_seq", T(
                P0("trial", "request_seq")
            )],
        ],
    }


def arbitrate_kinematic_approach_rule():
    unseen = Eq(P0("model", "sample_count"), L(0.0))
    global_best = And(
        Not(Gt(
            P0("model", "mean_global_error"),
            P0("model", "mean_phase_error"),
        )),
        Not(Gt(
            P0("model", "mean_global_error"),
            P0("model", "mean_interaction_error"),
        )),
    )
    phase_best = Not(Gt(
        P0("model", "mean_phase_error"),
        P0("model", "mean_interaction_error"),
    ))
    selected_ordinal = If(
        Or(unseen, global_best),
        L(0.0),
        If(phase_best, L(1.0), L(2.0)),
    )
    selected_error = If(
        Eq(selected_ordinal, L(0.0)),
        P0("transition", "global_prediction_error"),
        If(
            Eq(selected_ordinal, L(1.0)),
            P0("transition", "phase_prediction_error"),
            P0("transition", "interaction_prediction_error"),
        ),
    )
    count = Plus(P0("model", "sample_count"), L(1.0))

    def updated_mean(model_key, transition_key):
        return Plus(
            P0("model", model_key),
            Div(
                Minus(
                    P0("transition", transition_key),
                    P0("model", model_key),
                ),
                count,
            ),
        )

    return {
        "name": "hks_prequentially_arbitrate_kinematic_approach",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Choose the approach with the best prior track record in "
        "this point/support/composition context, score that choice, then learn "
        "from the new receipt. Unseen contexts conservatively use global.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "trial",
                "has_humanoid_kinematic_transition",
                "transition",
            ],
            [
                "transition",
                "uses_humanoid_kinematic_arbitration_model",
                "model",
            ],
        ],
        "where": And(
            Eq(P0("episode", "kinematics_study_active"), L(1.0)),
            Eq(P0("transition", "prediction_measured"), L(1.0)),
            Eq(P0("transition", "arbitration_measured"), L(0.0)),
            Eq(
                P0("model", "point_ordinal"),
                P0("transition", "point_ordinal"),
            ),
            Eq(
                P0("model", "support_phase"),
                P0("transition", "support_phase"),
            ),
            Eq(
                P0("model", "bundle_class"),
                If(
                    Gt(
                        P0("transition", "bundle_member_count"),
                        L(1.0),
                    ),
                    L(1.0),
                    L(0.0),
                ),
            ),
        ),
        "effects": [
            ["set_attr", "transition", "selected_approach_ordinal", T(
                selected_ordinal
            )],
            ["set_attr", "transition", "arbitrated_prediction_error", T(
                selected_error
            )],
            ["set_attr", "transition", "arbitration_prior_sample_count", T(
                P0("model", "sample_count")
            )],
            ["set_attr", "transition", "arbitration_measured", 1.0],
            [
                "del_edge",
                "transition",
                "uses_humanoid_kinematic_arbitration_model",
                "model",
            ],
            ["set_attr", "model", "global_selection_count", T(
                Plus(
                    P0("model", "global_selection_count"),
                    If(
                        Eq(selected_ordinal, L(0.0)),
                        L(1.0),
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "model", "phase_selection_count", T(
                Plus(
                    P0("model", "phase_selection_count"),
                    If(
                        Eq(selected_ordinal, L(1.0)),
                        L(1.0),
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "model", "interaction_selection_count", T(
                Plus(
                    P0("model", "interaction_selection_count"),
                    If(
                        Eq(selected_ordinal, L(2.0)),
                        L(1.0),
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "model", "mean_global_error", T(
                updated_mean(
                    "mean_global_error",
                    "global_prediction_error",
                )
            )],
            ["set_attr", "model", "mean_phase_error", T(
                updated_mean(
                    "mean_phase_error",
                    "phase_prediction_error",
                )
            )],
            ["set_attr", "model", "mean_interaction_error", T(
                updated_mean(
                    "mean_interaction_error",
                    "interaction_prediction_error",
                )
            )],
            ["set_attr", "model", "sample_count", T(count)],
        ],
    }


def manifest():
    productions = [
        (
            "HumanoidEpisode",
            "has_humanoid_kinematic_link",
            "HumanoidKinematicLink",
        ),
        (
            "HumanoidKinematicLink",
            "has_humanoid_kinematic_child",
            "HumanoidKinematicLink",
        ),
        (
            "HumanoidActionModel",
            "has_humanoid_global_kinematic_model",
            "HumanoidGlobalKinematicModel",
        ),
        (
            "HumanoidPhaseActionModel",
            "has_humanoid_phase_kinematic_model",
            "HumanoidPhaseKinematicModel",
        ),
        (
            "HumanoidGlobalKinematicModel",
            "predicts_humanoid_kinematic_link",
            "HumanoidKinematicLink",
        ),
        (
            "HumanoidPhaseKinematicModel",
            "predicts_humanoid_kinematic_link",
            "HumanoidKinematicLink",
        ),
        (
            "HumanoidSynergyModel",
            "has_humanoid_synergy_kinematic_model",
            "HumanoidSynergyKinematicModel",
        ),
        (
            "HumanoidSynergyKinematicModel",
            "predicts_humanoid_kinematic_link",
            "HumanoidKinematicLink",
        ),
        (
            "HumanoidEpisode",
            "has_humanoid_kinematic_arbitration_model",
            "HumanoidKinematicArbitrationModel",
        ),
        (
            "HumanoidKinematicArbitrationModel",
            "arbitrates_humanoid_kinematic_link",
            "HumanoidKinematicLink",
        ),
        (
            "HumanoidKinematicTransition",
            "uses_humanoid_kinematic_arbitration_model",
            "HumanoidKinematicArbitrationModel",
        ),
        (
            "HumanoidMotorTrial",
            "uses_humanoid_global_kinematic_model",
            "HumanoidGlobalKinematicModel",
        ),
        (
            "HumanoidMotorTrial",
            "uses_humanoid_phase_kinematic_model",
            "HumanoidPhaseKinematicModel",
        ),
        (
            "HumanoidMotorTrial",
            "uses_humanoid_synergy_kinematic_model",
            "HumanoidSynergyKinematicModel",
        ),
        (
            "HumanoidMotorTrial",
            "has_humanoid_kinematic_transition",
            "HumanoidKinematicTransition",
        ),
        (
            "HumanoidKinematicTransition",
            "observes_humanoid_kinematic_link",
            "HumanoidKinematicLink",
        ),
    ]
    return {
        "id": "humanoid_kinematics_study",
        "version": "1.0.0",
        "depends_on": ["humanoid_adaptation"],
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "description": "Paired prequential study of global-additive versus "
        "support-conditioned hierarchical whole-body kinematics learning.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": f"humanoid_kinematics_study:{edge_type}",
                "src": {"type": source_type, "var": "source"},
                "edge_type": edge_type,
                "tgt": {"type": target_type, "var": "target"},
            }
            for source_type, edge_type, target_type in productions
        ],
        "rules": [
            terminal_link_rule(),
            mint_global_model_rule(),
            mint_phase_model_rule(),
            initialize_phase_model_rule(),
            mint_synergy_model_rule(),
            mint_arbitration_model_rule(compound=False),
            mint_arbitration_model_rule(compound=True),
            choose_kinematic_reprobe_rule(),
            close_kinematic_reprobe_rule(),
            score_kinematic_reach_basis_rule(),
            choose_primary_kinematic_reach_basis_rule(),
            choose_secondary_kinematic_reach_basis_rule(),
            initialize_kinematic_reach_rule(),
            predict_single_reach_candidate_rule(),
            predict_synergy_reach_candidate_rule(),
            score_reach_candidate_rule(compound=False),
            score_reach_candidate_rule(compound=True),
            choose_kinematic_reach_rule(),
            bind_reach_trial_synergy_rule(),
            bind_reach_trial_secondary_phase_rule(),
            bind_reach_trial_secondary_global_rule(),
            measure_kinematic_reach_rule(),
            record_reach_candidate_outcome_rule(),
            clear_exhausted_reach_candidate_frontier_rule(),
            bind_trial_global_model_rule(),
            bind_program_global_model_rule(),
            bind_trial_phase_model_rule(),
            bind_program_phase_model_rule(),
            bind_trial_synergy_model_rule(),
            bind_transition_arbitration_model_rule(),
            measure_prequential_error_rule(),
            update_model_rule(phase=False),
            update_model_rule(phase=True),
            update_momentum_gain_rule(phase=False),
            update_momentum_gain_rule(phase=True),
            update_synergy_model_rule(),
            arbitrate_kinematic_approach_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "humanoid_kinematics_study.json"
    output.write_text(
        json.dumps(manifest(), indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output} ({len(manifest()['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
