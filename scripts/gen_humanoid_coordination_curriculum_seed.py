"""Generate the graph-native humanoid challenge-point curriculum."""
from __future__ import annotations

import json
import math
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
    Max,
    Min,
    Minus,
    Neg,
    Neighbours,
    N0,
    Not,
    Or,
    P0,
    Plus,
    Sqrt,
    T,
    Times,
    V,
    body_z_x,
    body_z_y,
    core_curiosity_score,
)


def challenges():
    return Neighbours("policy", "has_humanoid_coordination_challenge")


def challenge_memories():
    return Neighbours("shape", "stores_humanoid_challenge_memory")


def verified_takeoff_schemas():
    return Filter(
        Neighbours("episode", "has_humanoid_motor_program"),
        "schema_stage",
        And(
            Eq(
                A("schema_stage", "motor_task_context"),
                L("self_takeoff"),
            ),
            Eq(
                P0("schema_stage", "trajectory_verified"),
                L(1.0),
            ),
        ),
    )


def matching_challenge_memories():
    return Filter(
        challenge_memories(),
        "held_memory",
        Eq(
            P0("held_memory", "ordinal"),
            P0("challenge", "ordinal"),
        ),
    )


def challenge_frontier_unresolved(challenge):
    safe_floor = N0(challenge, "largest_safe_scale")
    unsafe_ceiling = N0(challenge, "smallest_unsafe_scale")
    resolution = Div(
        Max(L(1.0), safe_floor),
        P0("policy", "support_phase_prior_strength"),
    )
    return Or(
        Eq(safe_floor, L(0.0)),
        Eq(unsafe_ceiling, L(0.0)),
        Gt(Minus(unsafe_ceiling, safe_floor), resolution),
    )


def restore_shape_challenge_memory_rule():
    safe_floor = P0("memory", "largest_safe_scale")
    unsafe_ceiling = P0("memory", "smallest_unsafe_scale")
    resolution = Div(
        Max(L(1.0), safe_floor),
        P0("policy", "support_phase_prior_strength"),
    )
    return {
        "name": "hcc_restore_shape_indexed_challenge_frontier",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Warm-start the challenge frontier only from a memory "
        "attached to the graph-recognized body shape. Previously unsafe "
        "levels return contracted and eligible for new evidence.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
            [
                "shape",
                "stores_humanoid_challenge_memory",
                "memory",
            ],
        ],
        "where": And(
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(A("memory", "source"), L("library")),
            Eq(P0("challenge", "warm_start_restored"), L(0.0)),
            Eq(
                P0("challenge", "ordinal"),
                P0("memory", "ordinal"),
            ),
        ),
        "effects": [
            ["set_attr", "challenge", "difficulty_scale", T(
                P0("memory", "difficulty_scale")
            )],
            ["set_attr", "challenge", "largest_safe_scale", T(
                P0("memory", "largest_safe_scale")
            )],
            ["set_attr", "challenge", "smallest_unsafe_scale", T(
                P0("memory", "smallest_unsafe_scale")
            )],
            ["set_attr", "challenge", "sample_count", T(
                P0("memory", "sample_count")
            )],
            ["set_attr", "challenge", "success_count", T(
                P0("memory", "success_count")
            )],
            ["set_attr", "challenge", "takeoff_efficiency_probe_count", T(
                P0("memory", "takeoff_efficiency_probe_count")
            )],
            ["set_attr", "challenge", "takeoff_schema_refinement_initialized", T(
                P0("memory", "takeoff_schema_refinement_initialized")
            )],
            ["set_attr", "challenge", "takeoff_compression_safe_scale", T(
                P0("memory", "takeoff_compression_safe_scale")
            )],
            ["set_attr", "challenge", "takeoff_compression_unsafe_scale", T(
                P0("memory", "takeoff_compression_unsafe_scale")
            )],
            ["set_attr", "challenge", "prior_unsafe_count", T(
                P0("memory", "cumulative_unsafe_count")
            )],
            ["set_attr", "challenge", "unsafe_receipt_count", 0.0],
            ["set_attr", "challenge", "mean_performance_cost", T(
                P0("memory", "mean_performance_cost")
            )],
            ["set_attr", "challenge", "fast_prediction_residual", T(
                P0("memory", "fast_prediction_residual")
            )],
            ["set_attr", "challenge", "slow_prediction_residual", T(
                P0("memory", "slow_prediction_residual")
            )],
            ["set_attr", "challenge", "q", T(P0("memory", "q"))],
            ["set_attr", "challenge", "mean_recovery_cycle_gain", T(
                P0("memory", "mean_recovery_cycle_gain")
            )],
            ["set_attr", "challenge", "mean_recovery_progress_gain", T(
                P0("memory", "mean_recovery_progress_gain")
            )],
            ["set_attr", "challenge", "novelty", T(
                P0("memory", "learning_progress")
            )],
            ["set_attr", "challenge", "asym_count", T(
                If(
                    Or(
                        Eq(safe_floor, L(0.0)),
                        Eq(unsafe_ceiling, L(0.0)),
                    ),
                    P0("policy", "support_phase_prior_strength"),
                    Div(
                        Max(
                            L(0.0),
                            Minus(unsafe_ceiling, safe_floor),
                        ),
                        resolution,
                    ),
                )
            )],
            ["set_attr", "challenge", "initialized", 1.0],
            ["set_attr", "challenge", "warm_start_restored", 1.0],
            ["set_attr", "episode", "curriculum_warm_memory_count", T(
                Plus(
                    P0("episode", "curriculum_warm_memory_count"),
                    L(1.0),
                )
            )],
        ],
    }


def initialize_takeoff_schema_refinement_rule():
    return {
        "name": "hcc_initialize_verified_takeoff_schema_refinement",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "When a complete takeoff schema first becomes reusable, "
        "discard pre-schema phase-compression counts. Those trials acquired the "
        "movement and are not evidence about how much of a verified movement "
        "can be pruned.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(A("challenge", "family"), L("self_takeoff")),
            Gt(Count(verified_takeoff_schemas()), L(0.0)),
            Eq(
                P0("challenge", "takeoff_schema_refinement_initialized"),
                L(0.0),
            ),
        ),
        "effects": [
            ["set_attr", "challenge", "takeoff_efficiency_probe_count", 0.0],
            ["set_attr", "challenge", "takeoff_compression_safe_scale", 0.0],
            ["set_attr", "challenge", "takeoff_compression_unsafe_scale", 0.0],
            [
                "set_attr",
                "challenge",
                "takeoff_schema_refinement_initialized",
                1.0,
            ],
        ],
    }


def eligible_challenges():
    return Filter(
        challenges(),
        "c",
        And(
            Eq(P0("c", "authorized"), L(1.0)),
            Eq(P0("c", "unsafe_receipt_count"), L(0.0)),
            Or(
                challenge_frontier_unresolved("c"),
                And(
                    Eq(A("c", "family"), L("self_takeoff")),
                    Gt(P0("c", "largest_safe_scale"), L(0.0)),
                    Or(
                        Eq(Count(verified_takeoff_schemas()), L(0.0)),
                        Lt(
                            P0("c", "takeoff_efficiency_probe_count"),
                            P0("policy", "support_phase_prior_strength"),
                        ),
                    ),
                ),
            ),
        ),
    )


def initialize_challenge_frontier_rule():
    return {
        "name": "hcc_initialize_challenge_uncertainty_from_body",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Ground initial unresolved structure in the body's "
        "support-derived evidence window instead of a host-authored sample "
        "count or a fixed curriculum threshold.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(P0("challenge", "initialized"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "challenge", "asym_count", T(
                P0("policy", "support_phase_prior_strength")
            )],
            ["set_attr", "challenge", "q", 0.0],
            ["set_attr", "challenge", "novelty", 0.0],
            ["set_attr", "challenge", "initialized", 1.0],
        ],
    }


def unlock_ballistic_landing_stage_rule():
    return {
        "name": "hcc_unlock_ballistic_landing_from_mastered_prior",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Unlock a ballistic challenge only after its graph-held "
        "prerequisite has recovered safely once per sensed support. Transfer "
        "the measured safe impulse rather than restarting from an authored "
        "jump magnitude.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "prerequisite",
            ],
        ],
        "where": And(
            Or(
                Eq(A("challenge", "family"), L("ballistic_landing")),
                Eq(A("challenge", "family"), L("self_takeoff")),
            ),
            Eq(P0("challenge", "authorized"), L(0.0)),
            Eq(
                A("challenge", "prerequisite_name"),
                A("prerequisite", "name"),
            ),
            Gt(P0("prerequisite", "largest_safe_scale"), L(0.0)),
            Not(Lt(
                P0("prerequisite", "success_count"),
                P0("episode", "support_sensor_count"),
            )),
        ),
        "effects": [
            ["set_attr", "challenge", "difficulty_scale", T(
                If(
                    Eq(P0("challenge", "warm_start_restored"), L(1.0)),
                    P0("challenge", "difficulty_scale"),
                    P0("prerequisite", "largest_safe_scale"),
                )
            )],
            ["set_attr", "challenge", "authorized", 1.0],
            ["set_attr", "episode", "curriculum_stage_ordinal", T(
                Max(
                    P0("episode", "curriculum_stage_ordinal"),
                    P0("challenge", "stage_ordinal"),
                )
            )],
        ],
    }


def issue_challenge_rule():
    eligible = eligible_challenges()
    bootstrap_need = Eq(P0("episode", "locomotor_cycle_count"), L(0.0))
    selected = Argmin(
        eligible,
        "c",
        Neg(Plus(
            core_curiosity_score(),
            If(
                bootstrap_need,
                Times(
                    P0("policy", "support_phase_prior_strength"),
                    Plus(
                        P0("c", "mean_recovery_cycle_gain"),
                        Max(
                            L(0.0),
                            P0("c", "mean_recovery_progress_gain"),
                        ),
                    ),
                ),
                L(0.0),
            ),
        )),
        V("policy"),
    )
    interval_elapsed = Not(Lt(
        Minus(
            P0("episode", "request_seq"),
            P0("episode", "curriculum_last_request_seq"),
        ),
        P0("policy", "support_phase_prior_strength"),
    ))
    force_frames = Max(
        L(1.0),
        IDiv(
            P0("episode", "response_frames"),
            P0("episode", "support_sensor_count"),
        ),
    )
    active_difficulty = If(
        And(
            bootstrap_need,
            Gt(AO(selected, "largest_safe_scale"), L(0.0)),
        ),
        AO(selected, "largest_safe_scale"),
        AO(selected, "difficulty_scale"),
    )
    bootstrap_replay = And(
        bootstrap_need,
        Gt(AO(selected, "largest_safe_scale"), L(0.0)),
    )
    takeoff_efficiency_probe = And(
        Eq(AO(selected, "family"), L("self_takeoff")),
        Gt(Count(verified_takeoff_schemas()), L(0.0)),
        Not(challenge_frontier_unresolved(selected)),
        Gt(AO(selected, "largest_safe_scale"), L(0.0)),
    )
    takeoff_compression_scale = If(
        Gt(
            AO(selected, "takeoff_compression_unsafe_scale"),
            AO(selected, "takeoff_compression_safe_scale"),
        ),
        Div(
            Plus(
                AO(selected, "takeoff_compression_safe_scale"),
                AO(selected, "takeoff_compression_unsafe_scale"),
            ),
            L(2.0),
        ),
        Div(
            Plus(
                AO(selected, "takeoff_efficiency_probe_count"),
                L(1.0),
            ),
            P0("policy", "support_phase_prior_strength"),
        ),
    )
    # Froude-scaled target delta-v, converted to body weights over the
    # graph-selected pulse duration:
    #   force/(m*g) = target_Froude*sqrt(g*h)/(g*dt)
    #               = target_Froude*sqrt(h/g)/dt
    force_scale = Div(
        Times(
            P0("policy", "target_froude_speed"),
            active_difficulty,
            Sqrt(Div(
                P0("episode", "standing_reference_z"),
                P0("policy", "gravity_acceleration"),
            )),
        ),
        Times(
            force_frames,
            P0("episode", "physics_time_step"),
        ),
    )
    takeoff_target_height_gain = Div(
        Times(
            active_difficulty,
            active_difficulty,
            P0("episode", "standing_reference_z"),
        ),
        Times(
            P0("episode", "support_sensor_count"),
            P0("policy", "support_phase_prior_strength"),
            P0("policy", "support_phase_prior_strength"),
        ),
    )
    return {
        "name": "hcc_curiosity_requests_challenge_point",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "At a body-derived recovery interval, decision_core ranks "
        "the still-safe challenge frontier. The graph specifies a normalized "
        "environmental impulse; the host only converts body weights to force.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(A("episode", "phase"), L("locomotion")),
            Eq(A("episode", "mode"), L("directed_walk")),
            Eq(P0("episode", "evaluation_active"), L(1.0)),
            Eq(P0("episode", "state_is_receipt"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            Eq(P0("episode", "upright"), L(1.0)),
            Gt(P0("episode", "active_support_count"), L(0.0)),
            Eq(P0("episode", "curriculum_recovery_pending"), L(0.0)),
            Eq(
                P0("episode", "curriculum_challenge_request_seq"),
                P0("episode", "curriculum_challenge_applied_seq"),
            ),
            interval_elapsed,
            Gt(Count(eligible), L(0.0)),
            Eq(P0("challenge", "ordinal"), AO(selected, "ordinal")),
        ),
        "effects": [
            [
                "set_attr",
                "episode",
                "curriculum_active_challenge_ordinal",
                T(P0("challenge", "ordinal")),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_force_x_body_weights",
                T(Times(force_scale, P0("challenge", "direction_x"))),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_force_y_body_weights",
                T(Times(force_scale, P0("challenge", "direction_y"))),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_force_z_body_weights",
                T(Times(force_scale, P0("challenge", "direction_z"))),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_force_frames",
                T(force_frames),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_external_impulse_authority",
                T(P0("challenge", "external_impulse_authority")),
            ],
            ["set_attr", "episode", "self_takeoff_drive_active", T(If(
                Eq(A("challenge", "family"), L("self_takeoff")),
                L(1.0),
                L(0.0),
            ))],
            ["set_attr", "episode", "self_takeoff_compression_scale", T(If(
                takeoff_efficiency_probe,
                takeoff_compression_scale,
                L(0.0),
            ))],
            [
                "set_attr",
                "episode",
                "self_takeoff_target_velocity_scale",
                T(If(
                    Eq(A("challenge", "family"), L("self_takeoff")),
                    active_difficulty,
                    L(0.0),
                )),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_challenge_request_seq",
                T(Plus(P0("episode", "request_seq"), L(1.0))),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_last_request_seq",
                T(P0("episode", "request_seq")),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_last_challenge_cycle_count",
                T(P0("episode", "locomotor_cycle_count")),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_pending_baseline_directed_progress",
                T(P0("episode", "directed_progress")),
            ],
            [
                "set_attr",
                "episode",
                "curriculum_pending_baseline_cycle_count",
                T(P0("episode", "locomotor_cycle_count")),
            ],
            [
                "set_attr",
                "challenge",
                "active_request_seq",
                T(Plus(P0("episode", "request_seq"), L(1.0))),
            ],
            [
                "set_attr",
                "challenge",
                "active_difficulty_scale",
                T(active_difficulty),
            ],
            [
                "set_attr",
                "challenge",
                "active_bootstrap_replay",
                T(If(bootstrap_replay, L(1.0), L(0.0))),
            ],
            [
                "set_attr",
                "challenge",
                "request_count",
                T(Plus(P0("challenge", "request_count"), L(1.0))),
            ],
            ["set_attr", "challenge", "airborne_observed", 0.0],
            ["set_attr", "challenge", "touchdown_observed", 0.0],
            ["set_attr", "challenge", "takeoff_baseline_z", T(
                P0("episode", "state_com_z")
            )],
            ["set_attr", "challenge", "takeoff_target_height_gain", T(
                If(
                    Eq(A("challenge", "family"), L("self_takeoff")),
                    takeoff_target_height_gain,
                    L(0.0),
                )
            )],
            ["set_attr", "challenge", "takeoff_peak_height_gain", 0.0],
            ["set_attr", "challenge", "takeoff_aerial_receipt_count", 0.0],
            ["set_attr", "challenge", "takeoff_last_observed_state_seq", T(
                P0("episode", "state_seq")
            )],
        ],
    }


def bind_issued_takeoff_trial_context_rule():
    return {
        "name": "hcc_bind_issued_takeoff_trial_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A self-generated challenge selected in the motor-decision "
        "tick adopts that same request's trial as its preparation action. "
        "This preserves causal task identity without host-side re-selection.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(A("challenge", "family"), L("self_takeoff")),
            Eq(
                P0("challenge", "ordinal"),
                P0("episode", "curriculum_active_challenge_ordinal"),
            ),
            Eq(
                P0("trial", "request_seq"),
                P0("episode", "curriculum_challenge_request_seq"),
            ),
        ),
        "effects": [[
            "set_attr",
            "trial",
            "motor_task_context",
            "self_takeoff",
        ]],
    }


def bind_issued_takeoff_program_context_rule():
    return {
        "name": "hcc_bind_issued_takeoff_program_context",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Carry the newly adopted task identity onto the exact "
        "population program enacted by the preparation trial.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "enacts_humanoid_motor_program", "program"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(A("challenge", "family"), L("self_takeoff")),
            Eq(
                P0("challenge", "ordinal"),
                P0("episode", "curriculum_active_challenge_ordinal"),
            ),
            Eq(
                P0("trial", "request_seq"),
                P0("episode", "curriculum_challenge_request_seq"),
            ),
        ),
        "effects": [[
            "set_attr",
            "program",
            "motor_task_context",
            "self_takeoff",
        ]],
    }


def learn_challenge_rule():
    count = Plus(P0("challenge", "sample_count"), L(1.0))
    post_z_x = body_z_x("outcome", "post")
    post_z_y = body_z_y("outcome", "post")
    tilt = Sqrt(Plus(
        Times(post_z_x, post_z_x),
        Times(post_z_y, post_z_y),
    ))
    velocity_scale = Sqrt(Times(
        P0("policy", "gravity_acceleration"),
        P0("episode", "standing_reference_z"),
    ))
    horizontal_velocity = Sqrt(Plus(
        Times(P0("outcome", "post_vx"), P0("outcome", "post_vx")),
        Times(P0("outcome", "post_vy"), P0("outcome", "post_vy")),
    ))
    height_floor = Times(
        P0("policy", "minimum_upright_height_fraction"),
        P0("episode", "standing_reference_z"),
    )
    height_deficit = Div(
        Max(L(0.0), Minus(height_floor, P0("outcome", "post_z"))),
        P0("episode", "standing_reference_z"),
    )
    normalized_contact_load = Div(
        P0("outcome", "peak_contact_force_newtons"),
        Times(
            P0("episode", "body_mass"),
            P0("policy", "gravity_acceleration"),
        ),
    )
    performance_cost = Plus(
        tilt,
        Div(horizontal_velocity, velocity_scale),
        height_deficit,
        normalized_contact_load,
    )
    prediction_residual = Abs(Minus(
        performance_cost,
        P0("challenge", "mean_performance_cost"),
    ))
    fast_residual = Plus(
        P0("challenge", "fast_prediction_residual"),
        Div(
            Minus(
                prediction_residual,
                P0("challenge", "fast_prediction_residual"),
            ),
            P0("episode", "support_sensor_count"),
        ),
    )
    slow_residual = Plus(
        P0("challenge", "slow_prediction_residual"),
        Div(
            Minus(
                prediction_residual,
                P0("challenge", "slow_prediction_residual"),
            ),
            P0("policy", "support_phase_prior_strength"),
        ),
    )
    learning_progress = Max(L(0.0), Minus(slow_residual, fast_residual))
    return {
        "name": "hcc_learn_challenge_envelope_from_receipt",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Update competence, learning progress and the authorized "
        "challenge observation only from the exact action-time receipt. "
        "Promotion waits for delayed recovery evidence.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
            ["episode", "has_humanoid_motor_trial", "trial"],
            ["trial", "has_humanoid_transition", "outcome"],
        ],
        "where": And(
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(
                P0("trial", "request_seq"),
                P0("challenge", "active_request_seq"),
            ),
            Or(
                And(
                    Eq(
                        P0("challenge", "external_impulse_authority"),
                        L(1.0),
                    ),
                    Eq(
                        P0("outcome", "external_event_receipt_verified"),
                        L(1.0),
                    ),
                ),
                And(
                    Eq(
                        P0("challenge", "external_impulse_authority"),
                        L(0.0),
                    ),
                    Eq(P0("outcome", "receipt_verified"), L(1.0)),
                ),
            ),
            Eq(P0("outcome", "curriculum_challenge_learned"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "challenge", "q", T(prediction_residual)],
            [
                "set_attr",
                "challenge",
                "fast_prediction_residual",
                T(fast_residual),
            ],
            [
                "set_attr",
                "challenge",
                "slow_prediction_residual",
                T(slow_residual),
            ],
            ["set_attr", "challenge", "learning_progress", T(learning_progress)],
            ["set_attr", "challenge", "novelty", T(learning_progress)],
            [
                "set_attr",
                "challenge",
                "asym_count",
                T(Max(L(0.0), Minus(
                    P0("policy", "support_phase_prior_strength"),
                    count,
                ))),
            ],
            ["set_attr", "challenge", "sample_count", T(count)],
            [
                "set_attr",
                "challenge",
                "mean_performance_cost",
                T(Plus(
                    P0("challenge", "mean_performance_cost"),
                    Div(
                        Minus(
                            performance_cost,
                            P0("challenge", "mean_performance_cost"),
                        ),
                        count,
                    ),
                )),
            ],
            ["set_attr", "challenge", "pending_recovery", 1.0],
            [
                "set_attr",
                "episode",
                "curriculum_recovery_pending",
                1.0,
            ],
            [
                "set_attr",
                "episode",
                "curriculum_pending_recovery_request_seq",
                T(P0("trial", "request_seq")),
            ],
            ["set_attr", "trial", "status", "challenge_observed"],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "outcome", "curriculum_challenge_learned", 1.0],
        ],
    }


def recovery_window_elapsed():
    return Not(Lt(
        Minus(
            P0("episode", "request_seq"),
            P0("episode", "curriculum_pending_recovery_request_seq"),
        ),
        P0("policy", "support_phase_prior_strength"),
    ))


def task_recovery_window_elapsed():
    return Not(Lt(
        Minus(
            P0("episode", "request_seq"),
            P0("episode", "curriculum_pending_recovery_request_seq"),
        ),
        Times(
            P0("policy", "support_phase_prior_strength"),
            P0("episode", "support_sensor_count"),
        ),
    ))


def close_expired_self_takeoff_actuation_rule():
    return {
        "name": "hcc_close_expired_self_takeoff_actuation_window",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A failed ballistic synthesis remains evidence for the "
        "open curriculum challenge, but it does not retain actuator authority "
        "through the subsequent recovery. Close the deliberate vertical "
        "residual after its graph-held evidence window; ordinary balance "
        "can then recover while the graph decides whether the attempt was "
        "underpowered or unsafe. No host timeout or fixed action count is "
        "introduced.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(P0("episode", "curriculum_recovery_pending"), L(1.0)),
            Eq(P0("challenge", "pending_recovery"), L(1.0)),
            Eq(A("challenge", "family"), L("self_takeoff")),
            Eq(
                P0("challenge", "active_request_seq"),
                P0("episode", "curriculum_pending_recovery_request_seq"),
            ),
            Gt(P0("episode", "self_takeoff_drive_active"), L(0.5)),
            Eq(P0("challenge", "airborne_observed"), L(0.0)),
            recovery_window_elapsed(),
        ),
        "effects": [
            ["set_attr", "episode", "self_takeoff_drive_active", 0.0],
        ],
    }


def observe_ballistic_landing_phase_rule():
    airborne_now = And(
        Eq(P0("episode", "active_support_count"), L(0.0)),
        Or(
            Not(Eq(A("challenge", "family"), L("self_takeoff"))),
            Gt(P0("episode", "state_linear_momentum_z"), L(0.0)),
        ),
    )
    touchdown_now = And(
        Eq(P0("challenge", "airborne_observed"), L(1.0)),
        Gt(P0("episode", "active_support_count"), L(0.0)),
    )
    return {
        "name": "hcc_observe_ballistic_flight_and_touchdown",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A landing receipt is a temporal topology: zero support "
        "must be observed before restored support. Self-generated takeoff "
        "additionally requires positive whole-body vertical momentum, so a "
        "falling gait interval cannot masquerade as launch.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_policy", "policy"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "state_is_receipt"), L(1.0)),
            Eq(P0("challenge", "pending_recovery"), L(1.0)),
            Eq(P0("challenge", "requires_aerial_touchdown"), L(1.0)),
            Eq(
                P0("challenge", "active_request_seq"),
                P0("episode", "curriculum_pending_recovery_request_seq"),
            ),
            Or(
                And(
                    airborne_now,
                    Eq(P0("challenge", "airborne_observed"), L(0.0)),
                ),
                And(
                    touchdown_now,
                    Eq(P0("challenge", "touchdown_observed"), L(0.0)),
                ),
            ),
        ),
        "effects": [
            ["set_attr", "challenge", "airborne_observed", T(If(
                airborne_now,
                L(1.0),
                P0("challenge", "airborne_observed"),
            ))],
            ["set_attr", "challenge", "touchdown_observed", T(If(
                touchdown_now,
                L(1.0),
                P0("challenge", "touchdown_observed"),
            ))],
            ["set_attr", "episode", "self_takeoff_drive_active", T(If(
                airborne_now,
                L(0.0),
                P0("episode", "self_takeoff_drive_active"),
            ))],
        ],
    }


def observe_self_takeoff_envelope_rule():
    qualified_aerial = And(
        Eq(P0("challenge", "airborne_observed"), L(1.0)),
        Eq(P0("episode", "active_support_count"), L(0.0)),
    )
    height_gain = Max(
        L(0.0),
        Minus(
            P0("episode", "state_com_z"),
            P0("challenge", "takeoff_baseline_z"),
        ),
    )
    return {
        "name": "hcc_accumulate_self_takeoff_ballistic_envelope",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "After positive-momentum support loss, accumulate one "
        "receipt per new sensor state and retain peak ballistic height. The "
        "state-sequence guard prevents fixpoint iterations from inventing "
        "flight duration.",
        "match": [
            ["agent", "has_humanoid_episode", "episode"],
            ["agent", "has_humanoid_policy", "policy"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "state_is_receipt"), L(1.0)),
            Eq(A("challenge", "family"), L("self_takeoff")),
            Eq(P0("challenge", "pending_recovery"), L(1.0)),
            Eq(
                P0("challenge", "active_request_seq"),
                P0("episode", "curriculum_pending_recovery_request_seq"),
            ),
            Gt(
                P0("episode", "state_seq"),
                P0("challenge", "takeoff_last_observed_state_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "challenge", "takeoff_peak_height_gain", T(If(
                qualified_aerial,
                Max(
                    P0("challenge", "takeoff_peak_height_gain"),
                    height_gain,
                ),
                P0("challenge", "takeoff_peak_height_gain"),
            ))],
            [
                "set_attr",
                "challenge",
                "takeoff_aerial_receipt_count",
                T(Plus(
                    P0("challenge", "takeoff_aerial_receipt_count"),
                    If(qualified_aerial, L(1.0), L(0.0)),
                )),
            ],
            [
                "set_attr",
                "challenge",
                "takeoff_last_observed_state_seq",
                T(P0("episode", "state_seq")),
            ],
        ],
    }


def required_landing_evidence_observed():
    return Or(
        Eq(P0("challenge", "requires_aerial_touchdown"), L(0.0)),
        And(
            Eq(P0("challenge", "airborne_observed"), L(1.0)),
            Eq(P0("challenge", "touchdown_observed"), L(1.0)),
            Or(
                Not(Eq(A("challenge", "family"), L("self_takeoff"))),
                And(
                    Not(Lt(
                        P0("challenge", "takeoff_peak_height_gain"),
                        P0("challenge", "takeoff_target_height_gain"),
                    )),
                    Not(Lt(
                        P0("challenge", "takeoff_aerial_receipt_count"),
                        P0("episode", "support_sensor_count"),
                    )),
                ),
            ),
        ),
    )


def locomotor_task_recovered():
    return And(
        Not(Lt(
            P0("episode", "directed_progress"),
            P0(
                "episode",
                "curriculum_pending_baseline_directed_progress",
            ),
        )),
        Gt(
            P0("episode", "locomotor_cycle_count"),
            P0("episode", "curriculum_pending_baseline_cycle_count"),
        ),
    )


def verify_recovered_jump_schema_rule():
    return {
        "name": "hcc_verify_recovered_jump_schema",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Make phase transitions reusable only after the complete "
        "takeoff, aerial interval, touchdown, and locomotor recovery succeeds. "
        "Compression probes remain analysis-by-synthesis refinements inside "
        "those phases rather than blindly replaying the old trajectory.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
            [
                "episode",
                "has_humanoid_motor_transition",
                "transition",
            ],
            ["previous", "has_humanoid_motor_transition", "transition"],
            [
                "transition",
                "continues_with_humanoid_motor_program",
                "memory",
            ],
        ],
        "where": And(
            Eq(A("challenge", "family"), L("self_takeoff")),
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(P0("episode", "curriculum_recovery_pending"), L(1.0)),
            Eq(P0("challenge", "pending_recovery"), L(1.0)),
            Eq(
                P0("challenge", "active_request_seq"),
                P0("episode", "curriculum_pending_recovery_request_seq"),
            ),
            Eq(
                P0("transition", "task_request_seq"),
                P0("challenge", "active_request_seq"),
            ),
            Eq(A("transition", "motor_task_context"), L("self_takeoff")),
            recovery_window_elapsed(),
            Eq(P0("episode", "upright"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            required_landing_evidence_observed(),
            locomotor_task_recovered(),
        ),
        "effects": [
            ["set_attr", "transition", "trajectory_verified", 1.0],
            ["set_attr", "transition", "jump_schema_id", T(
                P0("challenge", "active_request_seq")
            )],
            ["set_attr", "previous", "trajectory_verified", 1.0],
            ["set_attr", "memory", "trajectory_verified", 1.0],
            ["set_attr", "previous", "jump_schema_id", T(
                P0("challenge", "active_request_seq")
            )],
            ["set_attr", "memory", "jump_schema_id", T(
                P0("challenge", "active_request_seq")
            )],
        ],
    }


def resolve_recovered_challenge_rule():
    expansion_fraction = Div(
        L(1.0),
        P0("policy", "support_phase_prior_strength"),
    )
    safe_floor = Max(
        P0("challenge", "largest_safe_scale"),
        P0("challenge", "active_difficulty_scale"),
    )
    unsafe_ceiling = P0("challenge", "smallest_unsafe_scale")
    next_difficulty = If(
        Eq(P0("challenge", "active_bootstrap_replay"), L(1.0)),
        P0("challenge", "difficulty_scale"),
        If(
            Gt(unsafe_ceiling, safe_floor),
            Div(Plus(safe_floor, unsafe_ceiling), L(2.0)),
            Times(
                P0("challenge", "difficulty_scale"),
                Plus(L(1.0), expansion_fraction),
            ),
        ),
    )
    next_success_count = Plus(P0("challenge", "success_count"), L(1.0))
    recovery_cycle_gain = Minus(
        P0("episode", "locomotor_cycle_count"),
        P0("episode", "curriculum_pending_baseline_cycle_count"),
    )
    recovery_progress_gain = Div(
        Minus(
            P0("episode", "directed_progress"),
            P0(
                "episode",
                "curriculum_pending_baseline_directed_progress",
            ),
        ),
        P0("episode", "standing_reference_z"),
    )
    return {
        "name": "hcc_promote_challenge_after_delayed_recovery",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Promote a challenge only after the body remains upright, "
        "exits recovery, regains its pre-challenge directed progress and "
        "completes another support cycle. Safe means task recovery, not merely "
        "postural survival.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(P0("episode", "curriculum_recovery_pending"), L(1.0)),
            Eq(P0("challenge", "pending_recovery"), L(1.0)),
            Eq(
                P0("challenge", "active_request_seq"),
                P0("episode", "curriculum_pending_recovery_request_seq"),
            ),
            recovery_window_elapsed(),
            Eq(P0("episode", "upright"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            required_landing_evidence_observed(),
            locomotor_task_recovered(),
        ),
        "effects": [
            ["set_attr", "challenge", "mean_recovery_cycle_gain", T(
                Plus(
                    P0("challenge", "mean_recovery_cycle_gain"),
                    Div(
                        Minus(
                            recovery_cycle_gain,
                            P0("challenge", "mean_recovery_cycle_gain"),
                        ),
                        next_success_count,
                    ),
                )
            )],
            ["set_attr", "challenge", "mean_recovery_progress_gain", T(
                Plus(
                    P0("challenge", "mean_recovery_progress_gain"),
                    Div(
                        Minus(
                            recovery_progress_gain,
                            P0(
                                "challenge",
                                "mean_recovery_progress_gain",
                            ),
                        ),
                        next_success_count,
                    ),
                )
            )],
            ["set_attr", "challenge", "success_count", T(
                next_success_count
            )],
            ["set_attr", "challenge", "takeoff_efficiency_probe_count", T(
                Plus(
                    P0("challenge", "takeoff_efficiency_probe_count"),
                    If(
                        And(
                            Eq(A("challenge", "family"), L("self_takeoff")),
                            Gt(
                                P0(
                                    "episode",
                                    "self_takeoff_compression_scale",
                                ),
                                L(0.0),
                            ),
                        ),
                        L(1.0),
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "challenge", "takeoff_compression_safe_scale", T(If(
                And(
                    Eq(A("challenge", "family"), L("self_takeoff")),
                    Gt(P0("episode", "self_takeoff_compression_scale"), L(0.0)),
                ),
                Max(
                    P0("challenge", "takeoff_compression_safe_scale"),
                    P0("episode", "self_takeoff_compression_scale"),
                ),
                P0("challenge", "takeoff_compression_safe_scale"),
            ))],
            ["set_attr", "challenge", "largest_safe_scale", T(safe_floor)],
            ["set_attr", "challenge", "difficulty_scale", T(
                next_difficulty
            )],
            ["set_attr", "challenge", "pending_recovery", 0.0],
            ["set_attr", "episode", "curriculum_recovery_pending", 0.0],
            ["set_attr", "episode", "self_takeoff_drive_active", 0.0],
            [
                "set_attr",
                "episode",
                "curriculum_last_request_seq",
                T(P0("episode", "request_seq")),
            ],
            ["set_attr", "episode", "curriculum_completed_challenges", T(
                Plus(
                    P0("episode", "curriculum_completed_challenges"),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "curriculum_safe_challenges", T(
                Plus(
                    P0("episode", "curriculum_safe_challenges"),
                    L(1.0),
                )
            )],
        ],
    }


def advance_underpowered_ballistic_challenge_rule():
    next_difficulty = Times(
        P0("challenge", "active_difficulty_scale"),
        Plus(
            L(1.0),
            Div(
                L(1.0),
                P0("policy", "support_phase_prior_strength"),
            ),
        ),
    )
    return {
        "name": "hcc_expand_ballistic_task_after_grounded_recovery",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A stable trial which never leaves support is below the "
        "task threshold, not beyond the safety frontier. Preserve its "
        "eligibility and expand the stimulus by the graph-held evidence "
        "fraction; only an actual loss of recovery is unsafe.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(P0("episode", "curriculum_recovery_pending"), L(1.0)),
            Eq(P0("challenge", "pending_recovery"), L(1.0)),
            Or(
                And(
                    Eq(A("challenge", "family"), L("ballistic_landing")),
                    Eq(P0("challenge", "airborne_observed"), L(0.0)),
                ),
                And(
                    Eq(A("challenge", "family"), L("self_takeoff")),
                    Not(required_landing_evidence_observed()),
                ),
            ),
            Eq(
                P0("challenge", "active_request_seq"),
                P0("episode", "curriculum_pending_recovery_request_seq"),
            ),
            task_recovery_window_elapsed(),
            Eq(P0("episode", "upright"), L(1.0)),
            Eq(P0("episode", "recovery_mode"), L(0.0)),
            locomotor_task_recovered(),
        ),
        "effects": [
            ["set_attr", "challenge", "difficulty_scale", T(
                next_difficulty
            )],
            ["set_attr", "challenge", "insufficient_task_count", T(
                Plus(
                    P0("challenge", "insufficient_task_count"),
                    L(1.0),
                )
            )],
            ["set_attr", "challenge", "pending_recovery", 0.0],
            ["set_attr", "episode", "curriculum_recovery_pending", 0.0],
            ["set_attr", "episode", "self_takeoff_drive_active", 0.0],
            [
                "set_attr",
                "episode",
                "curriculum_last_request_seq",
                T(P0("episode", "request_seq")),
            ],
        ],
    }


def reject_unrecovered_challenge_rule():
    contraction_fraction = Div(
        L(1.0),
        P0("policy", "support_phase_prior_strength"),
    )
    previous_ceiling = P0("challenge", "smallest_unsafe_scale")
    unsafe_ceiling = If(
        Gt(previous_ceiling, L(0.0)),
        Min(
            previous_ceiling,
            P0("challenge", "active_difficulty_scale"),
        ),
        P0("challenge", "active_difficulty_scale"),
    )
    recorded_safe_floor = P0("challenge", "largest_safe_scale")
    safe_floor = If(
        And(
            Gt(recorded_safe_floor, L(0.0)),
            Not(Gt(unsafe_ceiling, recorded_safe_floor)),
        ),
        L(0.0),
        recorded_safe_floor,
    )
    next_difficulty = If(
        Gt(safe_floor, L(0.0)),
        Div(Plus(safe_floor, unsafe_ceiling), L(2.0)),
        Times(
            P0("challenge", "active_difficulty_scale"),
            Max(
                L(0.0),
                Minus(L(1.0), contraction_fraction),
            ),
        ),
    )
    efficiency_probe = And(
        Eq(A("challenge", "family"), L("self_takeoff")),
        Gt(P0("episode", "self_takeoff_compression_scale"), L(0.0)),
    )
    return {
        "name": "hcc_retain_unrecovered_challenge_as_boundary",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "A fall or failure to regain both posture and locomotion "
        "inside a support-topology-derived task window is an unsafe frontier "
        "observation, not success.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "curriculum_active"), L(1.0)),
            Eq(P0("episode", "curriculum_recovery_pending"), L(1.0)),
            Eq(P0("challenge", "pending_recovery"), L(1.0)),
            Eq(
                P0("challenge", "active_request_seq"),
                P0("episode", "curriculum_pending_recovery_request_seq"),
            ),
            task_recovery_window_elapsed(),
            Or(
                Eq(P0("episode", "upright"), L(0.0)),
                Eq(P0("episode", "recovery_mode"), L(1.0)),
                Not(required_landing_evidence_observed()),
                Not(locomotor_task_recovered()),
            ),
        ),
        "effects": [
            ["set_attr", "challenge", "unsafe_receipt_count", T(
                Plus(
                    P0("challenge", "unsafe_receipt_count"),
                    If(efficiency_probe, L(0.0), L(1.0)),
                )
            )],
            ["set_attr", "challenge", "takeoff_efficiency_probe_count", T(If(
                efficiency_probe,
                Plus(
                    P0("challenge", "takeoff_efficiency_probe_count"),
                    L(1.0),
                ),
                P0("challenge", "takeoff_efficiency_probe_count"),
            ))],
            ["set_attr", "challenge", "takeoff_compression_unsafe_scale", T(If(
                efficiency_probe,
                P0("episode", "self_takeoff_compression_scale"),
                P0("challenge", "takeoff_compression_unsafe_scale"),
            ))],
            [
                "set_attr",
                "challenge",
                "smallest_unsafe_scale",
                T(If(
                    efficiency_probe,
                    previous_ceiling,
                    unsafe_ceiling,
                )),
            ],
            [
                "set_attr",
                "challenge",
                "largest_safe_scale",
                T(If(
                    efficiency_probe,
                    recorded_safe_floor,
                    safe_floor,
                )),
            ],
            ["set_attr", "challenge", "difficulty_scale", T(
                If(
                    efficiency_probe,
                    P0("challenge", "difficulty_scale"),
                    next_difficulty,
                )
            )],
            ["set_attr", "challenge", "pending_recovery", 0.0],
            ["set_attr", "episode", "curriculum_recovery_pending", 0.0],
            ["set_attr", "episode", "self_takeoff_drive_active", 0.0],
            [
                "set_attr",
                "episode",
                "curriculum_last_request_seq",
                T(P0("episode", "request_seq")),
            ],
            ["set_attr", "episode", "curriculum_completed_challenges", T(
                Plus(
                    P0("episode", "curriculum_completed_challenges"),
                    L(1.0),
                )
            )],
        ],
    }


def mint_shape_challenge_memory_rule():
    memories = matching_challenge_memories()
    return {
        "name": "hcc_mint_shape_indexed_challenge_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "At an explicit lifetime boundary, mint observed challenge "
        "competence under the graph-recognized body shape.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
        ],
        "where": And(
            Eq(P0("episode", "library_consolidation_requested"), L(1.0)),
            Gt(P0("challenge", "sample_count"), L(0.0)),
            Eq(Count(memories), L(0.0)),
        ),
        "effects": [
            ["add_node", "memory", "HumanoidChallengeMemory", {
                "ordinal": T(P0("challenge", "ordinal")),
                "family": T(A("challenge", "family")),
                "name": T(A("challenge", "name")),
                "difficulty_scale": T(
                    P0("challenge", "difficulty_scale")
                ),
                "largest_safe_scale": T(
                    P0("challenge", "largest_safe_scale")
                ),
                "smallest_unsafe_scale": T(
                    P0("challenge", "smallest_unsafe_scale")
                ),
                "sample_count": T(P0("challenge", "sample_count")),
                "success_count": T(P0("challenge", "success_count")),
                "cumulative_unsafe_count": T(Plus(
                    P0("challenge", "prior_unsafe_count"),
                    P0("challenge", "unsafe_receipt_count"),
                )),
                "mean_performance_cost": T(
                    P0("challenge", "mean_performance_cost")
                ),
                "fast_prediction_residual": T(
                    P0("challenge", "fast_prediction_residual")
                ),
                "slow_prediction_residual": T(
                    P0("challenge", "slow_prediction_residual")
                ),
                "learning_progress": T(
                    P0("challenge", "learning_progress")
                ),
                "q": T(P0("challenge", "q")),
                "mean_recovery_cycle_gain": T(
                    P0("challenge", "mean_recovery_cycle_gain")
                ),
                "mean_recovery_progress_gain": T(
                    P0("challenge", "mean_recovery_progress_gain")
                ),
                "takeoff_efficiency_probe_count": T(
                    P0("challenge", "takeoff_efficiency_probe_count")
                ),
                "takeoff_schema_refinement_initialized": T(
                    P0("challenge", "takeoff_schema_refinement_initialized")
                ),
                "takeoff_compression_safe_scale": T(
                    P0("challenge", "takeoff_compression_safe_scale")
                ),
                "takeoff_compression_unsafe_scale": T(
                    P0("challenge", "takeoff_compression_unsafe_scale")
                ),
                "library_consolidation_seq": T(
                    P0("episode", "library_consolidation_seq")
                ),
                "updated_in_lifetime": 1.0,
            }],
            [
                "add_edge",
                "shape",
                "stores_humanoid_challenge_memory",
                "memory",
            ],
        ],
    }


def update_shape_challenge_memory_rule():
    return {
        "name": "hcc_update_shape_indexed_challenge_memory",
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Refresh an existing shape-indexed frontier only at a "
        "later explicit lifetime boundary.",
        "match": [
            ["agent", "has_humanoid_policy", "policy"],
            ["agent", "has_humanoid_episode", "episode"],
            ["episode", "recognizes_humanoid_body_shape", "shape"],
            [
                "policy",
                "has_humanoid_coordination_challenge",
                "challenge",
            ],
            [
                "shape",
                "stores_humanoid_challenge_memory",
                "memory",
            ],
        ],
        "where": And(
            Eq(P0("episode", "library_consolidation_requested"), L(1.0)),
            Gt(P0("challenge", "sample_count"), L(0.0)),
            Eq(
                P0("challenge", "ordinal"),
                P0("memory", "ordinal"),
            ),
            Eq(P0("memory", "updated_in_lifetime"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "memory", "difficulty_scale", T(
                P0("challenge", "difficulty_scale")
            )],
            ["set_attr", "memory", "largest_safe_scale", T(
                P0("challenge", "largest_safe_scale")
            )],
            ["set_attr", "memory", "smallest_unsafe_scale", T(
                P0("challenge", "smallest_unsafe_scale")
            )],
            ["set_attr", "memory", "sample_count", T(
                P0("challenge", "sample_count")
            )],
            ["set_attr", "memory", "success_count", T(
                P0("challenge", "success_count")
            )],
            ["set_attr", "memory", "cumulative_unsafe_count", T(
                Plus(
                    P0("challenge", "prior_unsafe_count"),
                    P0("challenge", "unsafe_receipt_count"),
                )
            )],
            ["set_attr", "memory", "mean_performance_cost", T(
                P0("challenge", "mean_performance_cost")
            )],
            ["set_attr", "memory", "fast_prediction_residual", T(
                P0("challenge", "fast_prediction_residual")
            )],
            ["set_attr", "memory", "slow_prediction_residual", T(
                P0("challenge", "slow_prediction_residual")
            )],
            ["set_attr", "memory", "learning_progress", T(
                P0("challenge", "learning_progress")
            )],
            ["set_attr", "memory", "q", T(P0("challenge", "q"))],
            ["set_attr", "memory", "mean_recovery_cycle_gain", T(
                P0("challenge", "mean_recovery_cycle_gain")
            )],
            ["set_attr", "memory", "mean_recovery_progress_gain", T(
                P0("challenge", "mean_recovery_progress_gain")
            )],
            ["set_attr", "memory", "takeoff_efficiency_probe_count", T(
                P0("challenge", "takeoff_efficiency_probe_count")
            )],
            [
                "set_attr",
                "memory",
                "takeoff_schema_refinement_initialized",
                T(P0("challenge", "takeoff_schema_refinement_initialized")),
            ],
            ["set_attr", "memory", "takeoff_compression_safe_scale", T(
                P0("challenge", "takeoff_compression_safe_scale")
            )],
            ["set_attr", "memory", "takeoff_compression_unsafe_scale", T(
                P0("challenge", "takeoff_compression_unsafe_scale")
            )],
            ["set_attr", "memory", "library_consolidation_seq", T(
                P0("episode", "library_consolidation_seq")
            )],
            ["set_attr", "memory", "updated_in_lifetime", 1.0],
        ],
    }


def manifest():
    inverse_root_two = 1.0 / math.sqrt(2.0)
    directions = (
        ("forward", 1.0, 0.0, 0.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("rearward", -1.0, 0.0, 0.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("left", 0.0, 1.0, 0.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("right", 0.0, -1.0, 0.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("forward_left", inverse_root_two, inverse_root_two, 0.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("forward_right", inverse_root_two, -inverse_root_two, 0.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("rearward_left", -inverse_root_two, inverse_root_two, 0.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("rearward_right", -inverse_root_two, -inverse_root_two, 0.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("unload", 0.0, 0.0, 1.0, "reactive_balance", 1.0, 0.0, "", 0.0),
        ("vertical_landing", 0.0, 0.0, 1.0, "ballistic_landing", 0.0, 1.0, "unload", 1.0),
        ("forward_landing", inverse_root_two, 0.0, inverse_root_two, "ballistic_landing", 0.0, 1.0, "vertical_landing", 2.0),
        ("left_landing", 0.0, inverse_root_two, inverse_root_two, "ballistic_landing", 0.0, 1.0, "vertical_landing", 2.0),
        ("right_landing", 0.0, -inverse_root_two, inverse_root_two, "ballistic_landing", 0.0, 1.0, "vertical_landing", 2.0),
        ("self_takeoff", 0.0, 0.0, 0.0, "self_takeoff", 0.0, 1.0, "vertical_landing", 3.0),
    )
    nodes = [
        {
            "local_id": ordinal + 1,
            "type": "HumanoidCoordinationChallenge",
            "attrs": {
                "ordinal": float(ordinal),
                "family": family,
                "name": name,
                "direction_x": x,
                "direction_y": y,
                "direction_z": z,
                "authorized": authorized,
                "requires_aerial_touchdown": requires_aerial_touchdown,
                "prerequisite_name": prerequisite_name,
                "stage_ordinal": stage_ordinal,
                "external_impulse_authority": float(
                    family != "self_takeoff"
                ),
                "initialized": 0.0,
                "difficulty_scale": 1.0,
                "largest_safe_scale": 0.0,
                "smallest_unsafe_scale": 0.0,
                "request_count": 0.0,
                "sample_count": 0.0,
                "success_count": 0.0,
                "unsafe_receipt_count": 0.0,
                "active_request_seq": 0.0,
                "active_difficulty_scale": 1.0,
                "active_bootstrap_replay": 0.0,
                "pending_recovery": 0.0,
                "prior_unsafe_count": 0.0,
                "warm_start_restored": 0.0,
                "mean_performance_cost": 0.0,
                "fast_prediction_residual": 0.0,
                "slow_prediction_residual": 0.0,
                "learning_progress": 0.0,
                "q": 0.0,
                "mean_recovery_cycle_gain": 0.0,
                "mean_recovery_progress_gain": 0.0,
                "asym_count": 0.0,
                "novelty": 0.0,
                "airborne_observed": 0.0,
                "touchdown_observed": 0.0,
                "insufficient_task_count": 0.0,
                "takeoff_baseline_z": 0.0,
                "takeoff_target_height_gain": 0.0,
                "takeoff_peak_height_gain": 0.0,
                "takeoff_aerial_receipt_count": 0.0,
                "takeoff_efficiency_probe_count": 0.0,
                "takeoff_schema_refinement_initialized": 0.0,
                "takeoff_compression_safe_scale": 0.0,
                "takeoff_compression_unsafe_scale": 0.0,
                "takeoff_last_observed_state_seq": 0.0,
            },
        }
        for ordinal, (
            name,
            x,
            y,
            z,
            family,
            authorized,
            requires_aerial_touchdown,
            prerequisite_name,
            stage_ordinal,
        ) in enumerate(directions)
    ]
    return {
        "id": "humanoid_coordination_curriculum",
        "version": "1.5.0",
        "depends_on": ["humanoid_adaptation"],
        "area": "humanoid_sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "description": "Curiosity-selected, receipt-gated challenge-point "
        "progression for whole-body balance and coordination.",
        "nodes": nodes,
        "edges": [
            {
                "src": {"type": "HumanoidPolicy"},
                "type": "has_humanoid_coordination_challenge",
                "tgt": {"local": ordinal + 1},
                "attrs": {},
            }
            for ordinal in range(len(nodes))
        ],
        "productions": [
            {
                "provenance": "humanoid_coordination_curriculum:challenge",
                "src": {"type": "HumanoidPolicy", "var": "policy"},
                "edge_type": "has_humanoid_coordination_challenge",
                "tgt": {
                    "type": "HumanoidCoordinationChallenge",
                    "var": "challenge",
                },
            },
            {
                "provenance": (
                    "humanoid_coordination_curriculum:shape_memory"
                ),
                "src": {
                    "type": "HumanoidBodyShapeSignature",
                    "var": "shape",
                },
                "edge_type": "stores_humanoid_challenge_memory",
                "tgt": {
                    "type": "HumanoidChallengeMemory",
                    "var": "memory",
                },
            },
        ],
        "rules": [
            restore_shape_challenge_memory_rule(),
            initialize_takeoff_schema_refinement_rule(),
            initialize_challenge_frontier_rule(),
            unlock_ballistic_landing_stage_rule(),
            issue_challenge_rule(),
            bind_issued_takeoff_trial_context_rule(),
            bind_issued_takeoff_program_context_rule(),
            learn_challenge_rule(),
            observe_ballistic_landing_phase_rule(),
            close_expired_self_takeoff_actuation_rule(),
            observe_self_takeoff_envelope_rule(),
            verify_recovered_jump_schema_rule(),
            resolve_recovered_challenge_rule(),
            advance_underpowered_ballistic_challenge_rule(),
            reject_unrecovered_challenge_rule(),
            mint_shape_challenge_memory_rule(),
            update_shape_challenge_memory_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "humanoid_coordination_curriculum.json"
    output.write_text(
        json.dumps(manifest(), indent=1) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output} ({len(manifest()['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
