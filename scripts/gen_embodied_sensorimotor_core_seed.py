"""Generate the shared biological sensorimotor integration seed.

This generator authors graph data.  The resulting Rules execute in Rust; the
Python file contains no runtime controller or learning loop.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.gen_embodied_motor_priors_seed import (
        A, Abs, And, Count, Div, Eq, Exists, Filter, Gt, If, L, Lt,
        Max, Minus, Neighbours, Not, Or, P0, Plus, Sqrt, T, Times, V,
    )
except ModuleNotFoundError:
    from gen_embodied_motor_priors_seed import (  # type: ignore[no-redef]
        A, Abs, And, Count, Div, Eq, Exists, Filter, Gt, If, L, Lt,
        Max, Minus, Neighbours, Not, Or, P0, Plus, Sqrt, T, Times, V,
    )


ROOT = Path(__file__).resolve().parents[1]


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def Min(*items):
    return {"type": "Min", "items": list(items)}


def Pick(source):
    return {"type": "Pick", "source": source}


def node_attr(node, key):
    return Plus({"type": "Attr", "node": node, "key": key}, L(0.0))


def clamp01(value):
    return Max(L(0.0), Min(L(1.0), value))


def sequence(var):
    """One monotone trial/receipt clock across the three body domains."""
    return If(
        Eq(P0(var, "has_motor_epoch"), L(1.0)),
        P0(var, "motor_epoch"),
        Plus(
            P0(var, "world_step_index"),
            P0(var, "request_seq"),
            P0(var, "epoch"),
        ),
    )


def observation(var, sensed_key, raw_key):
    """Use the declared sensor sample, retaining old receipt compatibility."""
    return If(
        Eq(P0(var, "has_sensor_sample"), L(1.0)),
        P0(var, sensed_key),
        P0(var, raw_key),
    )


def normalize_trial_rule(episode_edge, trial_edge, model_edge, name):
    generic_trials = Neighbours("episode", "has_embodied_motor_trial")
    generic_models = Neighbours("trial", "uses_embodied_effector_model")
    return {
        "name": name,
        "area": "embodied_sensorimotor",
        "order": -30,
        "latency_class": "hard_realtime",
        "comment": "Normalize a graph-authored domain trial before any "
        "simulator receipt exists.",
        "match": [
            ["agent", episode_edge, "episode"],
            ["episode", trial_edge, "trial"],
            ["trial", model_edge, "model"],
        ],
        "where": Or(
            Not(Exists(
                generic_trials,
                "known_trial",
                Eq(V("known_trial"), V("trial")),
            )),
            Not(Exists(
                generic_models,
                "known_model",
                Eq(V("known_model"), V("model")),
            )),
        ),
        "effects": [
            ["add_edge", "episode", "has_embodied_motor_trial", "trial"],
            ["add_edge", "trial", "uses_embodied_effector_model", "model"],
        ],
    }


def open_body_belief_rule():
    beliefs = Neighbours("episode", "has_embodied_body_belief")
    return {
        "name": "esm_open_uncertain_body_belief",
        "area": "embodied_sensorimotor",
        "order": -20,
        "latency_class": "hard_realtime",
        "comment": "Embodied control owns an uncertain inferred body state; "
        "the simulator state is evidence, never the belief itself.",
        "match": [
            ["agent", "has_embodied_sensorimotor_policy", "policy"],
            ["agent", "has_affective_state", "affect"],
            ["agent", "has_embodied_motor_episode", "episode"],
        ],
        "where": Eq(Count(beliefs), L(0.0)),
        "effects": [
            ["add_node", "belief", "EmbodiedBodyBelief", {
                "initialized": 0.0,
                "status": "current",
                "estimate_x": 0.0,
                "estimate_y": 0.0,
                "estimate_z": 0.0,
                "estimate_vx": 0.0,
                "estimate_vy": 0.0,
                "estimate_vz": 0.0,
                "estimate_wx": 0.0,
                "estimate_wy": 0.0,
                "estimate_wz": 0.0,
                "position_variance": T(P0("policy", "initial_position_variance")),
                "velocity_variance": T(P0("policy", "initial_velocity_variance")),
                "angular_variance": T(P0("policy", "initial_angular_variance")),
                "contact_confidence": 0.0,
                "uncertainty": 1.0,
                "normalized_surprise": 0.0,
                "last_receipt_sequence": -1.0,
                "last_projected_state_seq": -1.0,
                "last_world_model_epoch": -1.0,
                "receipt_count": 0.0,
                "provenance_kind": "multimodal_inference",
                "observation_status": "inferred",
            }],
            ["add_edge", "episode", "has_embodied_body_belief", "belief"],
        ],
    }


def project_body_belief_rule():
    return {
        "name": "esm_project_current_body_belief",
        "area": "embodied_sensorimotor",
        "order": 2,
        "latency_class": "hard_realtime",
        "comment": "After the mechanical boundary publishes a new delayed "
        "sample, restore the predictive body belief onto the legacy state "
        "interface before body-specific action rules read it.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_body_belief", "belief"],
        ],
        "where": And(
            Eq(P0("belief", "initialized"), L(1.0)),
            Eq(P0("episode", "has_sensor_state"), L(1.0)),
            Eq(P0("episode", "sensor_requires_inference"), L(1.0)),
            Gt(
                P0("episode", "state_seq"),
                P0("belief", "last_projected_state_seq"),
            ),
        ),
        "effects": [
            *[
                ["set_attr", "episode", f"state_{axis}", T(
                    A("belief", f"estimate_{axis}")
                )]
                for axis in ("x", "y", "z")
            ],
            *[
                ["set_attr", "episode", f"state_v{axis}", T(
                    A("belief", f"estimate_v{axis}")
                )]
                for axis in ("x", "y", "z")
            ],
            *[
                ["set_attr", "episode", f"state_w{axis}", T(
                    A("belief", f"estimate_w{axis}")
                )]
                for axis in ("x", "y", "z")
            ],
            ["set_attr", "belief", "last_projected_state_seq", T(
                P0("episode", "state_seq")
            )],
        ],
    }


def open_local_loop_rule():
    loops = Neighbours("episode", "has_embodied_local_loop")
    return {
        "name": "esm_open_event_timed_local_loop",
        "area": "embodied_sensorimotor",
        "order": -20,
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
        ],
        "where": Eq(Count(loops), L(0.0)),
        "effects": [
            ["add_node", "loop", "EmbodiedLocalControlLoop", {
                "event_sequence": -1.0,
                "control_period_seconds": 0.0,
                "sensor_latency_seconds": 0.0,
                "actuator_activation_seconds": 0.0,
                "urgency": 0.0,
                "interrupt_required": 0.0,
                "interrupt_count": 0.0,
                "vigor": 1.0,
                "fatigue": 0.0,
                "provenance_kind": "event_timed_local_control",
            }],
            ["add_edge", "episode", "has_embodied_local_loop", "loop"],
        ],
    }


def open_actuator_envelope_rule():
    envelopes = Neighbours("model", "has_embodied_actuator_envelope")
    return {
        "name": "esm_open_opaque_actuator_envelope",
        "area": "embodied_sensorimotor",
        "order": -20,
        "latency_class": "hard_realtime",
        "comment": "The biological plant abstraction is causal rather than "
        "anatomical: latency, compliance, efficiency, stability, fatigue and "
        "thermal load apply to limbs, wheels, rotors, jets and control surfaces.",
        "match": [
            ["episode", "has_embodied_motor_trial", "trial"],
            ["trial", "uses_embodied_effector_model", "model"],
        ],
        "where": Eq(Count(envelopes), L(0.0)),
        "effects": [
            ["add_node", "envelope", "EmbodiedActuatorEnvelope", {
                "experience_count": 0.0,
                "activation_seconds": 0.0,
                "sensorimotor_latency_seconds": 0.0,
                "mechanical_efficiency": 0.0,
                "elastic_recovery_fraction": 0.0,
                "stability_authority": 0.0,
                "fatigue": 0.0,
                "thermal_fraction": 0.0,
                "peak_power_watts": 0.0,
                "confidence": 0.0,
                "last_receipt_sequence": -1.0,
                "provenance_kind": "receipt_grounded_actuator_plant",
            }],
            ["add_edge", "model", "has_embodied_actuator_envelope", "envelope"],
        ],
    }


def open_forward_model_rule():
    models = Neighbours("model", "has_embodied_forward_model")
    return {
        "name": "esm_open_embodied_forward_model",
        "area": "embodied_sensorimotor",
        "order": -20,
        "latency_class": "hard_realtime",
        "match": [
            ["trial", "uses_embodied_effector_model", "model"],
        ],
        "where": Eq(Count(models), L(0.0)),
        "effects": [
            ["add_node", "forward", "ForwardModel", {
                "predicted_consequence": 0.0,
                "confidence": 0.0,
                "expected_noise": 1.0,
                "last_calibration_epoch": -1.0,
                "provenance_kind": "embodied_receipt_grounded",
            }],
            ["add_edge", "model", "has_embodied_forward_model", "forward"],
        ],
    }


def open_controller_value_rule():
    values = Neighbours("model", "has_controller_value")
    return {
        "name": "esm_open_embodied_controller_value",
        "area": "embodied_sensorimotor",
        "order": -20,
        "latency_class": "hard_realtime",
        "comment": "Install the adaptive core's value contract before a "
        "dynamically materialized motor decision reaches that core.",
        "match": [
            ["trial", "uses_embodied_effector_model", "model"],
        ],
        "where": Eq(Count(values), L(0.0)),
        "effects": [
            ["add_node", "value", "ControllerValue", {
                "estimate": 0.0,
                "experience_count": 0.0,
                "last_update_epoch": -1.0,
                "provenance_kind": "learned_from_verified_outcomes",
            }],
            ["add_edge", "model", "has_controller_value", "value"],
        ],
    }


def bridge_adaptive_decision_rule():
    decisions = Filter(
        Neighbours("trial", "has_adaptive_decision"),
        "known_decision",
        Exists(
            Neighbours("known_decision", "selected_controller"),
            "known_controller",
            Eq(V("known_controller"), V("model")),
        ),
    )
    return {
        "name": "esm_bridge_motor_trial_to_adaptive_decision",
        "area": "embodied_sensorimotor",
        "order": -10,
        "latency_class": "hard_realtime",
        "comment": "Reuse the core efference-copy and eligibility machinery "
        "for every graph-authored embodied intervention.",
        "match": [
            ["agent", "has_embodied_attention_choice", "attention"],
            ["episode", "has_embodied_motor_trial", "trial"],
            ["episode", "has_embodied_body_belief", "belief"],
            ["trial", "uses_embodied_effector_model", "model"],
            ["model", "has_embodied_forward_model", "forward"],
            ["model", "has_controller_value", "value"],
        ],
        "where": Eq(Count(decisions), L(0.0)),
        "effects": [
            ["add_node", "command", "MotorCommand", {
                "name": T(A("model", "token")),
                "command_value": T(Max(
                    L(1.0),
                    P0("trial", "response_frames"),
                )),
                "provenance_kind": "graph_authored_motor_trial",
            }],
            ["add_node", "decision", "AdaptiveDecision", {
                "status": "committed",
                "epoch": T(sequence("trial")),
                "prediction_authored": 1,
                "trace_authored": 0,
                "sensorimotor_prediction_authored": 0,
                "reliable": 0,
                "option_evidence_used": 0,
                "provenance_kind": "embodied_motor_bridge",
            }],
            ["add_node", "outcome_prediction", "OutcomePrediction", {
                "epoch": T(sequence("trial")),
                "expected_value": T(P0("value", "estimate")),
                "provenance_kind": "predicted",
                "observation_status": "not_observed",
                "status": "open",
            }],
            ["add_node", "adaptive_outcome", "AdaptiveOutcome", {
                "status": "awaiting_receipt",
                "error_evaluated": 0,
                "epoch": T(sequence("trial")),
                "observed_value": 0.0,
                "next_value": 0.0,
                "expected_noise": 1.0,
                "volatility": 0.0,
                "model_ignorance": 1.0,
                "receipt_verified": 0,
                "provenance_kind": "embodied_adaptive_bridge",
            }],
            ["add_node", "consequence", "ObservedConsequence", {
                "epoch": T(sequence("trial")),
                "signal_value": 0.0,
                "status": "awaiting_receipt",
                "receipt_verified": 0,
                "calibration_applied": 0,
                "provenance_kind": "expected_motor_receipt",
                "observation_status": "not_observed",
            }],
            ["add_edge", "agent", "has_adaptive_decision", "decision"],
            ["add_edge", "agent", "has_adaptive_outcome", "adaptive_outcome"],
            ["add_edge", "decision", "in_adaptive_context", "episode"],
            ["add_edge", "decision", "selected_state", "belief"],
            ["add_edge", "decision", "selected_action", "command"],
            ["add_edge", "decision", "selected_controller", "model"],
            ["add_edge", "decision", "selected_attention", "attention"],
            ["add_edge", "decision", "uses_forward_model", "forward"],
            [
                "add_edge",
                "decision",
                "has_outcome_prediction",
                "outcome_prediction",
            ],
            [
                "add_edge",
                "adaptive_outcome",
                "evaluates_prediction",
                "outcome_prediction",
            ],
            ["add_edge", "adaptive_outcome", "evaluates_decision", "decision"],
            ["add_edge", "adaptive_outcome", "in_adaptive_context", "episode"],
            [
                "add_edge",
                "trial",
                "has_pending_adaptive_outcome",
                "adaptive_outcome",
            ],
            [
                "add_edge",
                "decision",
                "has_pending_observed_consequence",
                "consequence",
            ],
            ["add_edge", "consequence", "reports_decision", "decision"],
            ["add_edge", "trial", "has_adaptive_decision", "decision"],
            ["add_edge", "command", "commands_embodied_effector", "model"],
        ],
    }


def integrate_body_belief_rule():
    dt = Max(
        P0("outcome", "sensor_sample_period_seconds"),
        P0("outcome", "action_duration_seconds"),
    )
    pos_obs_var = Max(
        P0("policy", "position_variance_floor"),
        P0("outcome", "sensor_position_variance"),
    )
    vel_obs_var = Max(
        P0("policy", "velocity_variance_floor"),
        P0("outcome", "sensor_velocity_variance"),
    )
    angular_obs_var = Max(
        P0("policy", "angular_variance_floor"),
        P0("outcome", "sensor_angular_variance"),
    )
    prior_pos_var = If(
        Eq(P0("belief", "initialized"), L(1.0)),
        Plus(
            P0("belief", "position_variance"),
            Times(P0("policy", "process_noise_per_second"), dt),
        ),
        P0("policy", "initial_position_variance"),
    )
    prior_vel_var = If(
        Eq(P0("belief", "initialized"), L(1.0)),
        Plus(
            P0("belief", "velocity_variance"),
            Times(P0("policy", "process_noise_per_second"), dt),
        ),
        P0("policy", "initial_velocity_variance"),
    )
    prior_angular_var = If(
        Eq(P0("belief", "initialized"), L(1.0)),
        Plus(
            P0("belief", "angular_variance"),
            Times(P0("policy", "process_noise_per_second"), dt),
        ),
        P0("policy", "initial_angular_variance"),
    )
    pos_gain = Div(prior_pos_var, Plus(prior_pos_var, pos_obs_var))
    vel_gain = Div(prior_vel_var, Plus(prior_vel_var, vel_obs_var))
    angular_gain = Div(
        prior_angular_var,
        Plus(prior_angular_var, angular_obs_var),
    )
    initialized = Eq(P0("belief", "initialized"), L(1.0))

    def position_observation(axis):
        """Advance the delayed position sample to receipt time."""
        return Plus(
            observation("outcome", f"sensed_post_{axis}", f"post_{axis}"),
            Times(
                observation(
                    "outcome",
                    f"sensed_post_v{axis}",
                    f"post_v{axis}",
                ),
                P0("outcome", "sensor_latency_seconds"),
            ),
        )

    def predicted_position(axis):
        return If(
            initialized,
            Plus(
                P0("belief", f"estimate_{axis}"),
                Times(P0("belief", f"estimate_v{axis}"), dt),
            ),
            position_observation(axis),
        )

    def fused_position(axis):
        predicted = predicted_position(axis)
        observed = position_observation(axis)
        return Plus(predicted, Times(pos_gain, Minus(observed, predicted)))

    def fused_velocity(axis):
        prior = If(
            initialized,
            P0("belief", f"estimate_v{axis}"),
            observation(
                "outcome", f"sensed_post_v{axis}", f"post_v{axis}"
            ),
        )
        observed = observation(
            "outcome", f"sensed_post_v{axis}", f"post_v{axis}"
        )
        return Plus(prior, Times(vel_gain, Minus(observed, prior)))

    def fused_angular(axis):
        prior = If(
            initialized,
            P0("belief", f"estimate_w{axis}"),
            observation(
                "outcome", f"sensed_post_w{axis}", f"post_w{axis}"
            ),
        )
        observed = observation(
            "outcome", f"sensed_post_w{axis}", f"post_w{axis}"
        )
        return Plus(prior, Times(angular_gain, Minus(observed, prior)))

    residual_square = Plus(*[
        Times(
            Minus(
                position_observation(axis),
                predicted_position(axis),
            ),
            Minus(
                position_observation(axis),
                predicted_position(axis),
            ),
        )
        for axis in ("x", "y", "z")
    ])
    normalized_surprise = Div(
        Sqrt(residual_square),
        Sqrt(Plus(pos_obs_var, prior_pos_var)),
    )
    next_pos_var = Times(Minus(L(1.0), pos_gain), prior_pos_var)
    next_vel_var = Times(Minus(L(1.0), vel_gain), prior_vel_var)
    next_angular_var = Times(
        Minus(L(1.0), angular_gain),
        prior_angular_var,
    )
    uncertainty = clamp01(Plus(
        next_pos_var,
        next_vel_var,
        next_angular_var,
    ))
    return {
        "name": "esm_integrate_delayed_multimodal_receipt",
        "area": "embodied_sensorimotor",
        "order": 3,
        "latency_class": "hard_realtime",
        "comment": "Precision-weighted prediction and correction fuses "
        "proprioceptive, vestibular and contact evidence. The resulting belief "
        "is written back to the episode interface consumed by existing motor "
        "rules, replacing privileged state with inferred state.",
        "match": [
            ["agent", "has_embodied_sensorimotor_policy", "policy"],
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_body_belief", "belief"],
            ["episode", "has_embodied_motor_receipt", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Gt(sequence("outcome"), P0("belief", "last_receipt_sequence")),
        ),
        "effects": [
            ["add_node", "proprioception", "ProprioceptiveEvidence", {
                "epoch": T(sequence("outcome")),
                "vx": T(observation("outcome", "sensed_post_vx", "post_vx")),
                "vy": T(observation("outcome", "sensed_post_vy", "post_vy")),
                "vz": T(observation("outcome", "sensed_post_vz", "post_vz")),
                "variance": T(vel_obs_var),
                "latency_seconds": T(P0("outcome", "sensor_latency_seconds")),
                "provenance_kind": "sensor_receipt",
            }],
            ["add_node", "vestibular", "VestibularEvidence", {
                "epoch": T(sequence("outcome")),
                "wx": T(observation("outcome", "sensed_post_wx", "post_wx")),
                "wy": T(observation("outcome", "sensed_post_wy", "post_wy")),
                "wz": T(observation("outcome", "sensed_post_wz", "post_wz")),
                "variance": T(angular_obs_var),
                "latency_seconds": T(P0("outcome", "sensor_latency_seconds")),
                "provenance_kind": "sensor_receipt",
            }],
            ["add_node", "tactile", "TactileEvidence", {
                "epoch": T(sequence("outcome")),
                "pre_contact_count": T(P0("outcome", "pre_contact_count")),
                "contact_count": T(observation(
                    "outcome",
                    "sensed_contact_count",
                    "contact_count",
                )),
                "variance": T(Max(
                    P0("policy", "contact_variance_floor"),
                    P0("outcome", "sensor_contact_variance"),
                )),
                "latency_seconds": T(P0("outcome", "sensor_latency_seconds")),
                "provenance_kind": "sensor_receipt",
            }],
            ["add_edge", "belief", "supported_by_proprioception", "proprioception"],
            ["add_edge", "belief", "supported_by_vestibular", "vestibular"],
            ["add_edge", "belief", "supported_by_tactile", "tactile"],
            *[
                ["set_attr", "belief", f"estimate_{axis}", T(
                    fused_position(axis)
                )]
                for axis in ("x", "y", "z")
            ],
            *[
                ["set_attr", "belief", f"estimate_v{axis}", T(
                    fused_velocity(axis)
                )]
                for axis in ("x", "y", "z")
            ],
            *[
                ["set_attr", "belief", f"estimate_w{axis}", T(
                    fused_angular(axis)
                )]
                for axis in ("x", "y", "z")
            ],
            ["set_attr", "belief", "position_variance", T(next_pos_var)],
            ["set_attr", "belief", "velocity_variance", T(next_vel_var)],
            ["set_attr", "belief", "angular_variance", T(next_angular_var)],
            ["set_attr", "belief", "uncertainty", T(uncertainty)],
            ["set_attr", "belief", "normalized_surprise", T(
                normalized_surprise
            )],
            ["set_attr", "belief", "contact_confidence", T(
                clamp01(observation(
                    "outcome",
                    "sensed_contact_count",
                    "contact_count",
                ))
            )],
            ["set_attr", "belief", "last_receipt_sequence", T(
                sequence("outcome")
            )],
            ["set_attr", "belief", "receipt_count", T(
                Plus(P0("belief", "receipt_count"), L(1.0))
            )],
            ["set_attr", "belief", "initialized", 1.0],
            ["set_attr", "episode", "sensorimotor_uncertainty", T(
                uncertainty
            )],
            ["set_attr", "episode", "sensorimotor_surprise", T(
                normalized_surprise
            )],
            ["set_attr", "outcome", "sensorimotor_integrated", 1.0],
            ["set_attr", "outcome", "sensorimotor_uncertainty", T(
                uncertainty
            )],
            ["set_attr", "outcome", "sensorimotor_surprise", T(
                normalized_surprise
            )],
            *[
                ["set_attr", "outcome", f"fused_post_{axis}", T(
                    A("belief", f"estimate_{axis}")
                )]
                for axis in ("x", "y", "z")
            ],
        ],
    }


def update_actuator_envelope_rule():
    count = Plus(P0("envelope", "experience_count"), L(1.0))
    input_energy = Max(L(0.0), P0("outcome", "input_energy_joules"))
    recovered = Max(L(0.0), P0("outcome", "recovered_energy_joules"))
    movement = Sqrt(Plus(*[
        Times(
            Minus(P0("outcome", f"post_{axis}"), P0("outcome", f"pre_{axis}")),
            Minus(P0("outcome", f"post_{axis}"), P0("outcome", f"pre_{axis}")),
        )
        for axis in ("x", "y", "z")
    ]))
    efficiency = If(
        Gt(input_energy, L(0.0)),
        Div(movement, input_energy),
        L(0.0),
    )
    recovery_fraction = If(
        Gt(input_energy, L(0.0)),
        clamp01(Div(recovered, input_energy)),
        L(0.0),
    )
    pre_instability = Sqrt(Plus(*[
        Times(P0("outcome", f"pre_w{axis}"), P0("outcome", f"pre_w{axis}"))
        for axis in ("x", "y", "z")
    ]))
    post_instability = Sqrt(Plus(*[
        Times(P0("outcome", f"post_w{axis}"), P0("outcome", f"post_w{axis}"))
        for axis in ("x", "y", "z")
    ]))
    stability = Minus(pre_instability, post_instability)
    thermal_fraction = If(
        Gt(P0("episode", "state_thermal_capacity_joules"), L(0.0)),
        clamp01(Div(
            P0("outcome", "thermal_load_joules"),
            P0("episode", "state_thermal_capacity_joules"),
        )),
        L(0.0),
    )
    fatigue_load = If(
        Gt(P0("episode", "state_maximum_power_watts"), L(0.0)),
        clamp01(Div(
            P0("outcome", "peak_power_watts"),
            P0("episode", "state_maximum_power_watts"),
        )),
        thermal_fraction,
    )
    fatigue = clamp01(Plus(
        P0("envelope", "fatigue"),
        Times(P0("policy", "fatigue_loading_gain"), fatigue_load),
        Times(
            L(-1.0),
            P0("policy", "fatigue_recovery_per_second"),
            P0("outcome", "action_duration_seconds"),
        ),
    ))

    def mean(key, sample):
        return Plus(
            P0("envelope", key),
            Div(Minus(sample, P0("envelope", key)), count),
        )

    return {
        "name": "esm_learn_actuator_plant_envelope",
        "area": "adaptive_learning",
        "order": 4,
        "latency_class": "soft_realtime",
        "comment": "Verified receipts recruit this interruptible plant "
        "plasticity through the shared adaptive-learning task set; actuator "
        "release and local viability remain on the hard sheet.",
        "match": [
            ["agent", "has_embodied_sensorimotor_policy", "policy"],
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_motor_trial", "trial"],
            ["trial", "has_embodied_motor_receipt", "outcome"],
            ["trial", "uses_embodied_effector_model", "model"],
            ["model", "has_embodied_actuator_envelope", "envelope"],
        ],
        "where": Gt(
            sequence("outcome"),
            P0("envelope", "last_receipt_sequence"),
        ),
        "effects": [
            ["set_attr", "envelope", "activation_seconds", T(mean(
                "activation_seconds",
                P0("outcome", "actuator_activation_seconds"),
            ))],
            ["set_attr", "envelope", "sensorimotor_latency_seconds", T(mean(
                "sensorimotor_latency_seconds",
                Plus(
                    P0("outcome", "sensor_latency_seconds"),
                    P0("outcome", "actuator_activation_seconds"),
                ),
            ))],
            ["set_attr", "envelope", "mechanical_efficiency", T(mean(
                "mechanical_efficiency", efficiency
            ))],
            ["set_attr", "envelope", "elastic_recovery_fraction", T(mean(
                "elastic_recovery_fraction", recovery_fraction
            ))],
            ["set_attr", "envelope", "stability_authority", T(mean(
                "stability_authority", stability
            ))],
            ["set_attr", "envelope", "thermal_fraction", T(mean(
                "thermal_fraction", thermal_fraction
            ))],
            ["set_attr", "envelope", "fatigue", T(fatigue)],
            ["set_attr", "envelope", "peak_power_watts", T(Max(
                P0("envelope", "peak_power_watts"),
                P0("outcome", "peak_power_watts"),
            ))],
            ["set_attr", "envelope", "confidence", T(
                Div(count, Plus(count, L(1.0)))
            )],
            ["set_attr", "envelope", "experience_count", T(count)],
            ["set_attr", "envelope", "last_receipt_sequence", T(
                sequence("outcome")
            )],
        ],
    }


def close_adaptive_outcome_rule():
    return {
        "name": "esm_close_adaptive_decision_from_verified_receipt",
        "area": "embodied_sensorimotor",
        "order": 5,
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_motor_trial", "trial"],
            ["trial", "has_embodied_motor_receipt", "outcome"],
            ["trial", "has_adaptive_decision", "decision"],
            ["trial", "has_pending_adaptive_outcome", "adaptive_outcome"],
            [
                "decision",
                "has_pending_observed_consequence",
                "consequence",
            ],
            ["trial", "uses_embodied_effector_model", "model"],
            ["decision", "has_outcome_prediction", "prediction"],
            ["decision", "has_sensory_prediction", "sensory_prediction"],
            ["decision", "uses_forward_model", "forward"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(A("adaptive_outcome", "status"), L("awaiting_receipt")),
        ),
        "effects": [
            ["set_attr", "consequence", "epoch", T(sequence("outcome"))],
            ["set_attr", "consequence", "signal_value", T(
                P0("outcome", "task_progress")
            )],
            ["set_attr", "consequence", "status", "observed"],
            ["set_attr", "consequence", "receipt_verified", 1],
            ["set_attr", "consequence", "provenance_kind", "verified_motor_receipt"],
            ["set_attr", "consequence", "observation_status", "observed"],
            ["set_attr", "adaptive_outcome", "status", "verified"],
            ["set_attr", "adaptive_outcome", "epoch", T(sequence("outcome"))],
            ["set_attr", "adaptive_outcome", "observed_value", T(
                P0("outcome", "task_progress")
            )],
            ["set_attr", "adaptive_outcome", "expected_noise", T(
                P0("outcome", "sensorimotor_uncertainty")
            )],
            ["set_attr", "adaptive_outcome", "volatility", T(clamp01(Div(
                P0("outcome", "sensorimotor_surprise"),
                Plus(
                    P0("outcome", "sensorimotor_surprise"),
                    L(1.0),
                ),
            )))],
            ["set_attr", "adaptive_outcome", "model_ignorance", T(Minus(
                L(1.0),
                clamp01(P0("forward", "confidence")),
            ))],
            ["set_attr", "adaptive_outcome", "receipt_verified", 1],
            ["add_edge", "outcome", "has_adaptive_outcome", "adaptive_outcome"],
            ["add_edge", "outcome", "has_observed_consequence", "consequence"],
            ["add_edge", "consequence", "grounds_motor_receipt", "outcome"],
            ["set_attr", "decision", "status", "observed"],
        ],
    }


def request_verified_receipt_learning_rule():
    """Let a motor receipt open only the soft sheets needed to learn from it.

    Phasic sensing and the local interrupt remain on the hard-real-time sheet.
    Value assignment, generative-model integration and consolidation are
    interruptible work, so the receipt itself authors a scoped request for
    those areas instead of relying on an unrestricted host tick.
    """
    return {
        "name": "esm_request_verified_receipt_learning",
        "area": "embodied_sensorimotor",
        "order": 6,
        "latency_class": "hard_realtime",
        "comment": "A verified physical receipt is the graph-owned permission "
        "to run automatic plasticity and model integration outside the local "
        "control deadline.",
        "match": [
            ["agent", "has_embodied_sensorimotor_policy", "policy"],
            [
                "agent",
                "has_embodied_adaptive_learning_task_set",
                "adaptive_tasks",
            ],
            [
                "agent",
                "has_embodied_integration_task_set",
                "integration_tasks",
            ],
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_motor_trial", "trial"],
            ["trial", "has_embodied_motor_receipt", "outcome"],
            ["outcome", "has_adaptive_outcome", "adaptive_outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(A("adaptive_outcome", "status"), L("verified")),
            Eq(P0("outcome", "learning_escalation_requested"), L(0.0)),
        ),
        "effects": [
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "verified_embodied_receipt",
                "epoch": T(sequence("outcome")),
                "provenance_kind": "graph_authored_motor_plasticity",
            }],
            [
                "add_edge",
                "outcome",
                "has_system_two_escalation",
                "escalation",
            ],
            ["add_edge", "escalation", "about_context", "outcome"],
            [
                "add_edge",
                "escalation",
                "recruits_task_set",
                "adaptive_tasks",
            ],
            [
                "add_edge",
                "escalation",
                "recruits_task_set",
                "integration_tasks",
            ],
            ["set_attr", "outcome", "learning_escalation_requested", 1.0],
        ],
    }


def advance_adaptive_clock_rule():
    """Advance the shared adaptive epoch from verified physical receipts."""
    return {
        "name": "esm_advance_adaptive_clock_from_motor_receipt",
        "area": "embodied_sensorimotor",
        "order": 6,
        "latency_class": "hard_realtime",
        "comment": "A verified motor receipt is explicit temporal evidence. "
        "Advance the graph-held adaptive clock from its monotone receipt "
        "sequence so eligibility and transient lifetimes do not depend on "
        "host ticks.",
        "match": [
            ["agent", "has_adaptive_clock", "clock"],
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_motor_trial", "trial"],
            ["trial", "has_embodied_motor_receipt", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Gt(sequence("outcome"), P0("clock", "epoch")),
        ),
        "effects": [
            ["set_attr", "clock", "epoch", T(sequence("outcome"))],
            [
                "set_attr",
                "clock",
                "provenance_kind",
                "verified_embodied_motor_receipt",
            ],
        ],
    }


def archive_expired_eligibility_trace_rule():
    """Keep expired causal history off the active credit-assignment index."""
    return {
        "name": "esm_archive_expired_eligibility_trace",
        "area": "embodied_sensorimotor",
        "order": 13,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Once adaptive learning expires a bounded eligibility "
        "trace, move only its agent index edge to archival history. The trace, "
        "its causal links, and every learned controller value remain intact, "
        "while future credit matching stays bounded by the live horizon.",
        "match": [
            ["agent", "has_eligibility_trace", "trace"],
        ],
        "where": Eq(A("trace", "status"), L("expired")),
        "effects": [
            ["del_edge", "agent", "has_eligibility_trace", "trace"],
            ["add_edge", "agent", "has_archived_eligibility_trace", "trace"],
        ],
    }


def archive_credited_adaptive_outcome_rule():
    """Remove fully assigned outcomes from the active temporal-credit join."""
    live_traces = Filter(
        Neighbours("agent", "has_eligibility_trace"),
        "candidate_trace",
        And(
            Eq(A("candidate_trace", "status"), L("open")),
            Lt(
                P0("candidate_trace", "last_credited_epoch"),
                P0("adaptive_outcome", "epoch"),
            ),
            Exists(
                Neighbours("candidate_trace", "traces_decision"),
                "candidate_decision",
                And(
                    Exists(
                        Neighbours(
                            "candidate_decision",
                            "in_adaptive_context",
                        ),
                        "candidate_context",
                        Eq(V("candidate_context"), V("context")),
                    ),
                    Gte(
                        P0("adaptive_outcome", "epoch"),
                        P0("candidate_decision", "epoch"),
                    ),
                    Not(Gt(
                        Minus(
                            P0("adaptive_outcome", "epoch"),
                            P0("candidate_decision", "epoch"),
                        ),
                        P0("policy", "eligibility_horizon"),
                    )),
                ),
            ),
        ),
    )
    return {
        "name": "esm_archive_fully_credited_adaptive_outcome",
        "area": "embodied_sensorimotor",
        "order": 13,
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "After every still-live context-local eligibility trace "
        "has received an evaluated outcome, move that outcome off the active "
        "credit index. The receipt-owned edge and outcome node preserve the "
        "audit trail; only the quadratic historical join is collapsed.",
        "match": [
            ["agent", "has_adaptive_control_policy", "policy"],
            ["agent", "has_adaptive_outcome", "adaptive_outcome"],
            ["adaptive_outcome", "in_adaptive_context", "context"],
        ],
        "where": And(
            Eq(A("adaptive_outcome", "status"), L("evaluated")),
            Eq(Count(live_traces), L(0.0)),
        ),
        "effects": [
            [
                "del_edge",
                "agent",
                "has_adaptive_outcome",
                "adaptive_outcome",
            ],
            [
                "add_edge",
                "agent",
                "has_archived_adaptive_outcome",
                "adaptive_outcome",
            ],
            [
                "set_attr",
                "adaptive_outcome",
                "active_credit_complete",
                1.0,
            ],
        ],
    }


def update_local_loop_rule():
    sample_period = Max(
        P0("outcome", "sensor_sample_period_seconds"),
        Plus(
            P0("outcome", "sensor_latency_seconds"),
            P0("outcome", "actuator_activation_seconds"),
        ),
    )
    angular_speed = Sqrt(Plus(*[
        Times(
            observation("outcome", f"sensed_post_w{axis}", f"post_w{axis}"),
            observation("outcome", f"sensed_post_w{axis}", f"post_w{axis}"),
        )
        for axis in ("x", "y", "z")
    ]))
    contact_loss = If(
        And(
            Gt(observation(
                "outcome",
                "sensed_pre_contact_count",
                "pre_contact_count",
            ), L(0.0)),
            Eq(observation(
                "outcome",
                "sensed_contact_count",
                "contact_count",
            ), L(0.0)),
        ),
        L(1.0),
        L(0.0),
    )
    raw_urgency = clamp01(Plus(
        Times(
            P0("policy", "surprise_urgency_gain"),
            Div(
                P0("belief", "normalized_surprise"),
                Plus(P0("belief", "normalized_surprise"), L(1.0)),
            ),
        ),
        Times(P0("policy", "angular_urgency_gain"), angular_speed),
        Times(P0("policy", "contact_loss_urgency_gain"), contact_loss),
    ))
    verified_safety = Filter(
        Neighbours("episode", "has_learning_safety_context"),
        "verified_learning_safety",
        Eq(P0("verified_learning_safety", "verified"), L(1.0)),
    )
    safety = Pick(verified_safety)
    recoverability = If(
        Gt(Count(verified_safety), L(0.0)),
        Plus(
            Times(
                node_attr(safety, "protective_support_available"),
                node_attr(safety, "protective_support_effectiveness"),
            ),
            node_attr(safety, "reset_reachable"),
            Min(L(1.0), node_attr(safety, "recovery_path_count")),
        ),
        L(0.0),
    )
    urgency = Div(raw_urgency, Plus(L(1.0), recoverability))
    interrupt = If(
        Gte(urgency, P0("policy", "local_interrupt_threshold")),
        L(1.0),
        L(0.0),
    )
    return {
        "name": "esm_update_event_timed_local_control",
        "area": "embodied_sensorimotor",
        "order": 5,
        "latency_class": "hard_realtime",
        "comment": "Weight local surprise, angular motion and contact-loss "
        "urgency by graph-verified recoverability. Protective support and "
        "reachable resets widen safe exploration without changing structural "
        "power or thermal limits.",
        "match": [
            ["agent", "has_embodied_sensorimotor_policy", "policy"],
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_body_belief", "belief"],
            ["episode", "has_embodied_local_loop", "loop"],
            ["episode", "has_embodied_motor_trial", "trial"],
            ["trial", "has_embodied_motor_receipt", "outcome"],
            ["trial", "uses_embodied_effector_model", "model"],
            ["model", "has_embodied_actuator_envelope", "envelope"],
        ],
        "where": Gt(sequence("outcome"), P0("loop", "event_sequence")),
        "effects": [
            ["set_attr", "loop", "control_period_seconds", T(sample_period)],
            ["set_attr", "loop", "sensor_latency_seconds", T(
                P0("outcome", "sensor_latency_seconds")
            )],
            ["set_attr", "loop", "actuator_activation_seconds", T(
                P0("outcome", "actuator_activation_seconds")
            )],
            ["set_attr", "loop", "urgency", T(urgency)],
            ["set_attr", "loop", "interrupt_required", T(interrupt)],
            ["set_attr", "loop", "interrupt_count", T(Plus(
                P0("loop", "interrupt_count"),
                interrupt,
            ))],
            ["set_attr", "loop", "vigor", T(clamp01(Minus(
                Plus(
                    L(1.0),
                    Times(
                        P0("policy", "arousal_vigor_gain"),
                        P0("affect", "arousal"),
                    ),
                ),
                Plus(
                    P0("envelope", "fatigue"),
                    Times(
                        P0("policy", "negative_valence_caution_gain"),
                        Abs(Min(L(0.0), P0("affect", "valence"))),
                    ),
                ),
            )))],
            ["set_attr", "loop", "fatigue", T(
                P0("envelope", "fatigue")
            )],
            ["set_attr", "loop", "event_sequence", T(sequence("outcome"))],
            ["set_attr", "episode", "sensorimotor_control_period_seconds", T(
                sample_period
            )],
            ["set_attr", "episode", "sensorimotor_interrupt_required", T(
                interrupt
            )],
            ["set_attr", "episode", "sensorimotor_local_urgency", T(urgency)],
            ["set_attr", "episode", "recovery_mode", T(Max(
                P0("episode", "recovery_mode"),
                interrupt,
            ))],
        ],
    }


def forecast_allostasis_rule():
    forecasts = Neighbours("outcome", "has_interoceptive_forecast")
    energy_fraction = If(
        Gt(P0("episode", "state_available_energy_joules"), L(0.0)),
        clamp01(Div(
            P0("energy", "remaining_energy_joules"),
            P0("episode", "state_available_energy_joules"),
        )),
        L(1.0),
    )
    thermal_fraction = If(
        Gt(P0("episode", "state_thermal_capacity_joules"), L(0.0)),
        clamp01(Div(
            P0("energy", "thermal_headroom_joules"),
            P0("episode", "state_thermal_capacity_joules"),
        )),
        L(1.0),
    )
    power_fraction = If(
        Gt(P0("episode", "state_maximum_power_watts"), L(0.0)),
        clamp01(Div(
            P0("energy", "power_headroom_watts"),
            P0("episode", "state_maximum_power_watts"),
        )),
        L(1.0),
    )
    reserve = Min(energy_fraction, thermal_fraction, power_fraction)
    demand = Max(
        P0("envelope", "fatigue"),
        P0("envelope", "thermal_fraction"),
    )
    return {
        "name": "esm_forecast_motor_allostatic_reserve",
        "area": "embodied_sensorimotor",
        "order": 6,
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_sensorimotor_policy", "policy"],
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_energetic_state", "energy"],
            ["episode", "has_embodied_motor_trial", "trial"],
            ["trial", "has_embodied_motor_receipt", "outcome"],
            ["trial", "uses_embodied_effector_model", "model"],
            ["model", "has_embodied_actuator_envelope", "envelope"],
        ],
        "where": And(
            Eq(P0("outcome", "sensorimotor_integrated"), L(1.0)),
            Eq(Count(forecasts), L(0.0)),
        ),
        "effects": [
            ["add_node", "forecast", "InteroceptiveForecast", {
                "status": "raw",
                "processed": 0,
                "epoch": T(sequence("outcome")),
                "current_level": T(reserve),
                "predicted_demand": T(demand),
                "desired_reserve": T(P0("policy", "desired_motor_reserve")),
                "expected_noise": T(P0("outcome", "sensorimotor_uncertainty")),
                "model_ignorance": T(Minus(
                    L(1.0),
                    P0("envelope", "confidence"),
                )),
                "provenance_kind": "embodied_energetic_forecast",
            }],
            ["add_edge", "agent", "has_interoceptive_forecast", "forecast"],
            ["add_edge", "outcome", "has_interoceptive_forecast", "forecast"],
            ["add_edge", "forecast", "forecasts_actuator", "model"],
        ],
    }


def publish_world_model_observation_rule():
    observations = Neighbours("outcome", "has_body_world_observation")
    confidence = Minus(L(1.0), P0("belief", "uncertainty"))
    return {
        "name": "esm_publish_body_belief_to_generative_world_model",
        "area": "embodied_sensorimotor",
        "order": 7,
        "latency_class": "soft_realtime",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_body_belief", "belief"],
            ["episode", "has_embodied_motor_receipt", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "sensorimotor_integrated"), L(1.0)),
            Eq(Count(observations), L(0.0)),
        ),
        "effects": [
            ["add_node", "observation", "WorldModelObservation", {
                "belief_status": "new",
                "prediction_comparison_status": "uncompared",
                "provenance_kind": "perceived",
                "state_kind": "embodied_body_state",
                "state_summary": "multimodal inferred body state",
                "epoch": T(sequence("outcome")),
                "confidence": T(clamp01(confidence)),
                "uncertainty": T(P0("belief", "uncertainty")),
            }],
            ["add_edge", "agent", "has_world_model_observation", "observation"],
            ["add_edge", "outcome", "has_body_world_observation", "observation"],
            ["add_edge", "observation", "describes_body_belief", "belief"],
        ],
    }


def publish_network_mode_sample_rule():
    samples = Neighbours("outcome", "has_embodied_network_mode_sample")
    return {
        "name": "esm_publish_sensorimotor_network_mode_sample",
        "area": "embodied_sensorimotor",
        "order": 8,
        "latency_class": "soft_realtime",
        "comment": "Motor uncertainty and predicted internal deficit feed the "
        "existing overlapping salience/executive/default network dynamics.",
        "match": [
            ["agent", "has_embodied_motor_episode", "episode"],
            ["episode", "has_embodied_body_belief", "belief"],
            ["episode", "has_embodied_motor_receipt", "outcome"],
            ["outcome", "has_interoceptive_forecast", "forecast"],
            ["error", "forecasted_from", "forecast"],
        ],
        "where": And(
            Eq(P0("outcome", "network_mode_sample_published"), L(0.0)),
            Eq(Count(samples), L(0.0)),
        ),
        "effects": [
            ["add_node", "sample", "NetworkModeSample", {
                "epoch": T(sequence("outcome")),
                "exteroceptive_load": T(Minus(
                    L(1.0),
                    clamp01(P0("belief", "uncertainty")),
                )),
                "task_demand": 1.0,
                "interoceptive_urgency": T(clamp01(P0("error", "urgency"))),
                "uncertainty": T(clamp01(P0("belief", "uncertainty"))),
                "idle_duration": 0.0,
                "status": "raw",
                "provenance_kind": "embodied_sensorimotor_state",
            }],
            ["add_edge", "agent", "has_network_mode_sample", "sample"],
            ["add_edge", "outcome", "has_embodied_network_mode_sample", "sample"],
            ["set_attr", "outcome", "network_mode_sample_published", 1.0],
        ],
    }


def consolidate_controller_rule():
    memories = Neighbours("model", "has_procedural_motor_episode")
    return {
        "name": "esm_consolidate_reliable_controller_as_procedural_episode",
        "area": "embodied_sensorimotor",
        "order": 20,
        "latency_class": "background",
        "match": [
            ["agent", "has_embodied_sensorimotor_policy", "policy"],
            ["model", "has_controller_value", "value"],
            ["model", "has_embodied_forward_model", "forward"],
        ],
        "where": And(
            Gte(
                P0("value", "experience_count"),
                P0("policy", "procedural_consolidation_experience"),
            ),
            Gte(
                P0("forward", "confidence"),
                P0("policy", "procedural_consolidation_confidence"),
            ),
            Eq(Count(memories), L(0.0)),
        ),
        "effects": [
            ["add_node", "memory", "Episode", {
                "kind": "embodied_motor_procedure",
                "consolidated": True,
                "salience": T(clamp01(Abs(P0("value", "estimate")))),
                "replay_count": 0.0,
                "provenance_kind": "verified_motor_experience",
            }],
            ["add_edge", "agent", "recorded_episode", "memory"],
            ["add_edge", "model", "has_procedural_motor_episode", "memory"],
            ["add_edge", "memory", "consolidates_controller", "model"],
        ],
    }


def request_motor_replay_integration_rule():
    return {
        "name": "esm_request_motor_replay_integration",
        "area": "embodied_sensorimotor",
        "order": 21,
        "latency_class": "hard_realtime",
        "comment": "When the default-mode core reconstructs a procedural "
        "episode, the resulting context authors a separate interruptible "
        "request to integrate that replay into its forward controller.",
        "match": [
            [
                "agent",
                "has_embodied_integration_task_set",
                "integration_tasks",
            ],
            ["agent", "has_internally_generated_context", "context"],
            ["context", "replays_episode", "memory"],
            ["memory", "consolidates_controller", "model"],
        ],
        "where": And(
            Eq(A("context", "status"), L("active")),
            Eq(P0("context", "motor_replay_requested"), L(0.0)),
        ),
        "effects": [
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "embodied_motor_replay_integration",
                "epoch": T(P0("context", "epoch")),
                "provenance_kind": "graph_authored_default_mode_replay",
            }],
            [
                "add_edge",
                "context",
                "has_motor_replay_escalation",
                "escalation",
            ],
            ["add_edge", "escalation", "about_context", "context"],
            [
                "add_edge",
                "escalation",
                "recruits_task_set",
                "integration_tasks",
            ],
            ["set_attr", "context", "motor_replay_requested", 1.0],
        ],
    }


def integrate_motor_replay_rule():
    return {
        "name": "esm_integrate_default_mode_motor_replay",
        "area": "embodied_sensorimotor",
        "order": 21,
        "latency_class": "background",
        "match": [
            ["agent", "has_embodied_sensorimotor_policy", "policy"],
            ["context", "replays_episode", "memory"],
            ["memory", "consolidates_controller", "model"],
            ["model", "has_embodied_forward_model", "forward"],
        ],
        "where": And(
            Eq(A("context", "status"), L("active")),
            Eq(P0("context", "motor_replay_integrated"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "forward", "confidence", T(clamp01(Plus(
                P0("forward", "confidence"),
                Times(
                    P0("policy", "motor_replay_gain"),
                    Minus(L(1.0), P0("forward", "confidence")),
                ),
            )))],
            ["set_attr", "memory", "replay_count", T(
                Plus(P0("memory", "replay_count"), L(1.0))
            )],
            ["set_attr", "context", "motor_replay_integrated", 1.0],
        ],
    }


def manifest():
    nodes = [
        {
            "local_id": 1,
            "type": "EmbodiedSensorimotorPolicy",
            "attrs": {
                "name": "core_embodied_sensorimotor_policy",
                "initial_position_variance": 1.0,
                "initial_velocity_variance": 1.0,
                "initial_angular_variance": 1.0,
                "position_variance_floor": 0.0001,
                "velocity_variance_floor": 0.001,
                "angular_variance_floor": 0.001,
                "contact_variance_floor": 0.001,
                "process_noise_per_second": 0.01,
                "surprise_urgency_gain": 0.5,
                "angular_urgency_gain": 0.25,
                "contact_loss_urgency_gain": 1.0,
                "local_interrupt_threshold": 0.75,
                "fatigue_loading_gain": 0.1,
                "fatigue_recovery_per_second": 0.02,
                "arousal_vigor_gain": 0.25,
                "negative_valence_caution_gain": 0.25,
                "desired_motor_reserve": 0.25,
                "procedural_consolidation_experience": 3.0,
                "procedural_consolidation_confidence": 0.5,
                "motor_replay_gain": 0.1,
            },
        },
        {
            "local_id": 2,
            "type": "AttentionChoice",
            "attrs": {
                "name": "embodied_multimodal_state",
                "provenance_kind": "sensorimotor_attention_default",
            },
        },
        {
            "local_id": 3,
            "type": "SystemTwoTaskSet",
            "attrs": {
                "name": "embodied_adaptive_learning_task_set",
                "area": "adaptive_learning",
                "enabled": 1,
            },
        },
        {
            "local_id": 4,
            "type": "SystemTwoTaskSet",
            "attrs": {
                "name": "embodied_model_integration_task_set",
                "area": "embodied_sensorimotor",
                "enabled": 1,
            },
        },
        {
            "local_id": 5,
            "type": "AdaptiveClock",
            "attrs": {
                "epoch": -1.0,
                "provenance_kind": "embodied_receipt_clock",
            },
        },
    ]
    return {
        "id": "embodied_sensorimotor_core",
        "version": "1.4.0",
        "depends_on": [
            "adaptive_control_core",
            "default_mode_core",
            "hierarchical_effector_control",
        ],
        "area": "embodied_sensorimotor",
        "latency_class": "hard_realtime",
        "description": "Uncertain multimodal body belief, event-timed local "
        "control, receipt-grounded actuator physiology, adaptive credit, "
        "allostatic forecasting and procedural replay for arbitrary bodies, "
        "with plant plasticity admitted outside the local control deadline.",
        "nodes": nodes,
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_sensorimotor_policy",
                "tgt": {"local": 1},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_attention_choice",
                "tgt": {"local": 2},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_adaptive_learning_task_set",
                "tgt": {"local": 3},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_integration_task_set",
                "tgt": {"local": 4},
                "attrs": {},
            },
            {
                "src": {"role": "agent_root"},
                "type": "has_adaptive_clock",
                "tgt": {"local": 5},
                "attrs": {},
            },
        ],
        "productions": [
            {
                "provenance": "embodied_sensorimotor:policy",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_sensorimotor_policy",
                "tgt": {
                    "type": "EmbodiedSensorimotorPolicy",
                    "var": "policy",
                },
            },
            {
                "provenance": "embodied_sensorimotor:body_belief",
                "src": {"type": "EmbodiedMotorEpisode", "var": "episode"},
                "edge_type": "has_embodied_body_belief",
                "tgt": {"type": "EmbodiedBodyBelief", "var": "belief"},
            },
            {
                "provenance": "embodied_sensorimotor:local_loop",
                "src": {"type": "EmbodiedMotorEpisode", "var": "episode"},
                "edge_type": "has_embodied_local_loop",
                "tgt": {
                    "type": "EmbodiedLocalControlLoop",
                    "var": "loop",
                },
            },
            {
                "provenance": "embodied_sensorimotor:actuator_envelope",
                "src": {"type": "Unknown", "var": "model"},
                "edge_type": "has_embodied_actuator_envelope",
                "tgt": {
                    "type": "EmbodiedActuatorEnvelope",
                    "var": "envelope",
                },
            },
        ],
        "rules": [
            normalize_trial_rule(
                "has_humanoid_episode",
                "has_humanoid_motor_trial",
                "uses_humanoid_phase_action_model",
                "esm_normalize_humanoid_motor_trial",
            ),
            normalize_trial_rule(
                "has_humanoid_episode",
                "has_humanoid_motor_trial",
                "uses_humanoid_action_model",
                "esm_normalize_humanoid_primitive_motor_trial",
            ),
            normalize_trial_rule(
                "has_embodied_episode",
                "has_motor_trial",
                "uses_action_model",
                "esm_normalize_ground_motor_trial",
            ),
            normalize_trial_rule(
                "has_aerial_episode",
                "has_aerial_motor_trial",
                "uses_aerial_action_model",
                "esm_normalize_aerial_motor_trial",
            ),
            open_body_belief_rule(),
            project_body_belief_rule(),
            open_local_loop_rule(),
            open_actuator_envelope_rule(),
            open_forward_model_rule(),
            open_controller_value_rule(),
            bridge_adaptive_decision_rule(),
            integrate_body_belief_rule(),
            update_actuator_envelope_rule(),
            close_adaptive_outcome_rule(),
            request_verified_receipt_learning_rule(),
            advance_adaptive_clock_rule(),
            archive_expired_eligibility_trace_rule(),
            archive_credited_adaptive_outcome_rule(),
            update_local_loop_rule(),
            forecast_allostasis_rule(),
            publish_world_model_observation_rule(),
            publish_network_mode_sample_rule(),
            consolidate_controller_rule(),
            request_motor_replay_integration_rule(),
            integrate_motor_replay_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "embodied_sensorimotor_core.json"
    output.write_text(
        json.dumps(manifest(), indent=1) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
