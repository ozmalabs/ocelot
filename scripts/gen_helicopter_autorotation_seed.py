"""Generate graph-native energy/viability control for an unknown airframe.

The seed does not name collective, cyclic, engine failure, flare, or
autorotation.  It learns the local consequences of opaque actions and chooses
among them by predicted preservation of internal energy and reduction of
contact-relative kinetic energy.
"""
from __future__ import annotations

import json
import os


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def AttrOf(node, key):
    return {"type": "Attr", "node": node, "key": key}


def P0(var, key):
    return Plus(A(var, key), L(0.0))


def P(node, key):
    return (
        P0(node, key)
        if isinstance(node, str)
        else Plus(AttrOf(node, key), L(0.0))
    )


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Times(*items):
    return {"type": "Times", "items": list(items)}


def Div(a, b):
    return {"type": "Div", "a": a, "b": b}


def Sqrt(arg):
    return {"type": "Sqrt", "arg": arg}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Min(*items):
    return {"type": "Min", "items": list(items)}


def Max(*items):
    return {"type": "Max", "items": list(items)}


def And(*items):
    return {"type": "And", "items": list(items)}


def Ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def Neighbours(var, edge_type):
    return {
        "type": "Neighbours",
        "node": V(var),
        "edge_type": edge_type,
        "any_type": False,
    }


def Filter(source, var_name, predicate):
    return {
        "type": "Filter",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Count(source):
    return {"type": "Count", "source": source}


def Argmin(source, var_name, value, default):
    return {
        "type": "Argmin",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


def T(term):
    return {"__term__": term}


MODELS = Neighbours("episode", "has_energy_action_model")
ACTIVE_MODELS = Filter(
    MODELS,
    "candidate",
    Eq(
        P0("candidate", "contact_horizon_context"),
        P0("episode", "contact_horizon_context"),
    ),
)
MEMORIES = Neighbours("episode", "has_energy_transition_memory")
UNSAMPLED = Filter(
    ACTIVE_MODELS,
    "candidate",
    Lt(P0("candidate", "experience_count"), P0("policy", "babble_samples")),
)


def square(value):
    return Times(value, value)


def predicted(model, episode, state_key, delta_key):
    return Plus(P(episode, state_key), P(model, delta_key))


def desired_sink_rate(episode, policy):
    stopping_speed = Sqrt(
        Times(
            L(2.0),
            P0(policy, "comfortable_vertical_acceleration"),
            Max(
                L(0.0),
                Minus(
                    P0(episode, "state_z"),
                    P0(policy, "contact_clearance"),
                ),
            ),
        )
    )
    return Times(
        L(-1.0),
        Min(P0(policy, "cruise_sink_speed"), stopping_speed),
    )


def desired_forward_speed(episode, policy):
    stopping_speed = Sqrt(
        Times(
            L(2.0),
            P0(policy, "comfortable_horizontal_acceleration"),
            Max(
                L(0.0),
                Minus(
                    P0(episode, "state_z"),
                    P0(policy, "contact_clearance"),
                ),
            ),
        )
    )
    return Min(P0(policy, "cruise_forward_speed"), stopping_speed)


def action_cost(model, episode, policy):
    projection_steps = Min(
        P0(policy, "maximum_projection_steps"),
        Max(
            L(1.0),
            Div(
                P0(episode, "time_to_contact_seconds"),
                P0(policy, "action_duration_seconds"),
            ),
        ),
    )
    predicted_vx = Plus(
        P0(episode, "state_vx"),
        Times(projection_steps, P(model, "mean_dvx")),
    )
    predicted_vy = Plus(
        P0(episode, "state_vy"),
        Times(projection_steps, P(model, "mean_dvy")),
    )
    predicted_vz = Plus(
        P0(episode, "state_vz"),
        Times(projection_steps, P(model, "mean_dvz")),
    )
    predicted_pitch_rate = predicted(
        model, episode, "state_pitch_rate", "mean_dpitch_rate"
    )
    predicted_roll_rate = predicted(
        model, episode, "state_roll_rate", "mean_droll_rate"
    )
    predicted_yaw_rate = predicted(
        model, episode, "state_yaw_rate", "mean_dyaw_rate"
    )
    predicted_rotor_fraction = Plus(
        P0(episode, "state_rotor_fraction"),
        Times(projection_steps, P(model, "mean_drotor_fraction")),
    )
    predicted_pitch = Plus(
        P0(episode, "state_pitch"),
        Times(
            P0(policy, "pitch_attitude_projection_seconds"),
            predicted_pitch_rate,
        ),
    )
    predicted_roll = Plus(
        P0(episode, "state_roll"),
        Times(
            P0(policy, "attitude_projection_seconds"),
            predicted_roll_rate,
        ),
    )
    predicted_yaw = Plus(
        P0(episode, "state_yaw"),
        Times(
            P0(policy, "attitude_projection_seconds"),
            predicted_yaw_rate,
        ),
    )
    altitude_fraction = Min(
        L(1.0),
        Div(
            P0(episode, "state_z"),
            P0(policy, "attitude_relaxation_altitude"),
        ),
    )
    contact_attitude_weight = Times(
        P0(policy, "contact_attitude_weight"),
        Minus(L(1.0), altitude_fraction),
    )
    return Plus(
        Times(
            P0(policy, "rotor_reserve_weight"),
            square(
                Minus(
                    predicted_rotor_fraction,
                    P0(policy, "preferred_rotor_fraction"),
                )
            ),
        ),
        Times(
            P0(policy, "vertical_kinetic_weight"),
            square(Minus(predicted_vz, desired_sink_rate(episode, policy))),
        ),
        Times(
            P0(policy, "horizontal_kinetic_weight"),
            square(
                Minus(
                    predicted_vx,
                    desired_forward_speed(episode, policy),
                )
            ),
        ),
        Times(
            P0(policy, "lateral_kinetic_weight"),
            square(predicted_vy),
        ),
        Times(
            P0(policy, "transverse_angular_rate_weight"),
            Plus(
                square(predicted_roll_rate),
                square(predicted_yaw_rate),
            ),
        ),
        Times(
            P0(policy, "pitch_rate_weight"),
            square(predicted_pitch_rate),
        ),
        Times(
            contact_attitude_weight,
            Plus(
                square(predicted_roll),
                square(predicted_pitch),
                Times(
                    P0(policy, "yaw_attitude_fraction"),
                    square(predicted_yaw),
                ),
            ),
        ),
        Times(
            P0(policy, "flight_roll_attitude_weight"),
            square(predicted_roll),
        ),
        Times(
            P0(policy, "flight_pitch_attitude_weight"),
            square(predicted_pitch),
        ),
        Times(
            P0(policy, "flight_yaw_attitude_weight"),
            square(predicted_yaw),
        ),
        Times(
            P0(policy, "effort_weight"),
            P(model, "mean_supplied_energy_joules"),
        ),
        Times(
            L(-1.0),
            P0(policy, "recovery_weight"),
            P(model, "mean_recovered_energy_joules"),
        ),
    )


def contextual_memory_cost(memory, episode, policy):
    consequence = action_cost(memory, episode, policy)
    context_distance = Plus(
        Times(
            P0(policy, "context_vx_weight"),
            square(Minus(P0(episode, "state_vx"), P(memory, "pre_vx"))),
        ),
        Times(
            P0(policy, "context_vz_weight"),
            square(Minus(P0(episode, "state_vz"), P(memory, "pre_vz"))),
        ),
        Times(
            P0(policy, "context_vy_weight"),
            square(Minus(P0(episode, "state_vy"), P(memory, "pre_vy"))),
        ),
        Times(
            P0(policy, "context_roll_weight"),
            square(
                Minus(P0(episode, "state_roll"), P(memory, "pre_roll"))
            ),
        ),
        Times(
            P0(policy, "context_pitch_weight"),
            square(
                Minus(P0(episode, "state_pitch"), P(memory, "pre_pitch"))
            ),
        ),
        Times(
            P0(policy, "context_pitch_rate_weight"),
            square(
                Minus(
                    P0(episode, "state_pitch_rate"),
                    P(memory, "pre_pitch_rate"),
                )
            ),
        ),
        Times(
            P0(policy, "context_roll_rate_weight"),
            square(
                Minus(
                    P0(episode, "state_roll_rate"),
                    P(memory, "pre_roll_rate"),
                )
            ),
        ),
        Times(
            P0(policy, "context_yaw_rate_weight"),
            square(
                Minus(
                    P0(episode, "state_yaw_rate"),
                    P(memory, "pre_yaw_rate"),
                )
            ),
        ),
        Times(
            P0(policy, "context_rotor_weight"),
            square(
                Minus(
                    P0(episode, "state_rotor_fraction"),
                    P(memory, "pre_rotor_fraction"),
                )
            ),
        ),
        Times(
            P0(policy, "context_contact_horizon_weight"),
            square(
                Minus(
                    P0(episode, "time_to_contact_seconds"),
                    P(memory, "pre_time_to_contact_seconds"),
                )
            ),
        ),
    )
    return Plus(
        consequence,
        Times(P0(policy, "context_distance_weight"), context_distance),
    )


def measure_rule():
    closing_speed = Max(L(0.1), Times(L(-1.0), P0("episode", "state_vz")))
    time_to_contact = Div(
        P0("episode", "state_z"),
        closing_speed,
    )
    contact_horizon_context = Ite(
        Lt(time_to_contact, P0("policy", "imminent_contact_horizon_seconds")),
        L(2.0),
        Ite(
            Lt(
                time_to_contact,
                P0("policy", "approach_contact_horizon_seconds"),
            ),
            L(1.0),
            L(0.0),
        ),
    )
    impact_cost = Plus(
        Times(
            P0("policy", "vertical_kinetic_weight"),
            square(P0("episode", "state_touchdown_vz")),
        ),
        Times(
            P0("policy", "horizontal_kinetic_weight"),
            square(P0("episode", "state_touchdown_vx")),
        ),
        Times(
            P0("policy", "lateral_kinetic_weight"),
            square(P0("episode", "state_touchdown_vy")),
        ),
        Times(
            P0("policy", "contact_attitude_weight"),
            Plus(
                square(P0("episode", "state_touchdown_roll")),
                square(P0("episode", "state_touchdown_pitch")),
            ),
        ),
    )
    return {
        "name": "ha_measure_viability",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "comment": "Assess contact viability from raw motion, attitude, and "
        "energy reserve. The graph is not told whether a manoeuvre has a name.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
        ],
        "where": Lt(
            P0("episode", "measured_state_seq"),
            P0("episode", "state_seq"),
        ),
        "effects": [
            ["set_attr", "episode", "time_to_contact_seconds", T(
                time_to_contact
            )],
            ["set_attr", "episode", "contact_horizon_context", T(
                contact_horizon_context
            )],
            ["set_attr", "episode", "impact_cost", T(impact_cost)],
            ["set_attr", "episode", "viable_contact", T(Ite(
                And(
                    Gt(P0("episode", "state_contact"), L(0.5)),
                    Lt(
                        P0("episode", "state_abs_touchdown_vz"),
                        P0("policy", "maximum_touchdown_vertical_speed"),
                    ),
                    Lt(
                        P0("episode", "state_abs_touchdown_vx"),
                        P0("policy", "maximum_touchdown_horizontal_speed"),
                    ),
                    Lt(
                        P0("episode", "state_abs_touchdown_vy"),
                        P0("policy", "maximum_touchdown_lateral_speed"),
                    ),
                    Lt(
                        P0("episode", "state_abs_touchdown_pitch"),
                        P0("policy", "maximum_touchdown_attitude"),
                    ),
                    Lt(
                        P0("episode", "state_abs_touchdown_roll"),
                        P0("policy", "maximum_touchdown_attitude"),
                    ),
                    Gt(
                        P0("episode", "state_rotor_fraction"),
                        P0("policy", "minimum_viable_rotor_fraction"),
                    ),
                ),
                L(1.0),
                L(0.0),
            ))],
            ["set_attr", "episode", "measured_state_seq", T(
                P0("episode", "state_seq")
            )],
        ],
    }


def choose_babble_rule():
    best = Argmin(
        UNSAMPLED,
        "candidate",
        P0("candidate", "ordinal"),
        V("episode"),
    )
    return {
        "name": "ha_choose_unmodelled_intervention",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "comment": "Intervene once on each opaque action. Ordinal determines "
        "coverage only and contains no control semantics.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Gt(Count(UNSAMPLED), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "decision_kind", "opaque_intervention"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def choose_learned_rule():
    best = Argmin(
        MEMORIES,
        "candidate",
        contextual_memory_cost("candidate", "episode", "policy"),
        V("episode"),
    )
    return {
        "name": "ha_choose_energy_viability_action",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "comment": "Use learned opaque consequences to preserve recoverable "
        "internal energy while reducing contact-relative kinetic energy.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MEMORIES), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "decision_kind", "energy_viability_model"],
            ["set_attr", "episode", "predicted_action_cost", T(
                contextual_memory_cost(best, "episode", "policy")
            )],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def choose_compact_model_fallback_rule():
    best = Argmin(
        ACTIVE_MODELS,
        "candidate",
        action_cost("candidate", "episode", "policy"),
        V("episode"),
    )
    return {
        "name": "ha_choose_compact_model_fallback",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "comment": "Remain viable before any bounded local exemplars exist by "
        "using the compact contextual action model learned online.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Eq(Count(MEMORIES), L(0.0)),
            Gt(Count(ACTIVE_MODELS), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(
                AttrOf(best, "token")
            )],
            ["set_attr", "episode", "decision_kind", "compact_energy_model"],
            ["set_attr", "episode", "predicted_action_cost", T(
                action_cost(best, "episode", "policy")
            )],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def open_trial_rule():
    return {
        "name": "ha_open_energy_trial",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_energy_action_model", "model"],
        ],
        "where": And(
            Eq(P0("episode", "action_ready"), L(1.0)),
            Eq(A("episode", "selected_token"), A("model", "token")),
            Eq(
                P0("episode", "contact_horizon_context"),
                P0("model", "contact_horizon_context"),
            ),
            Lt(P0("episode", "last_trial_seq"), P0("episode", "request_seq")),
        ),
        "effects": [
            ["add_node", "trial", "HelicopterEnergyTrial", {
                "request_seq": T(P0("episode", "request_seq")),
                "token": T(A("model", "token")),
                "decision_kind": T(A("episode", "decision_kind")),
                "status": "issued",
            }],
            ["add_edge", "episode", "has_helicopter_energy_trial", "trial"],
            ["add_edge", "trial", "uses_energy_action_model", "model"],
            ["set_attr", "episode", "last_trial_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def learn_rule():
    count = Plus(P0("model", "experience_count"), L(1.0))
    initial_rate = Div(L(1.0), count)

    def observed(post_key, pre_key):
        return Minus(P0("outcome", post_key), P0("outcome", pre_key))

    deltas = {
        "mean_dvx": observed("post_vx", "pre_vx"),
        "mean_dvy": observed("post_vy", "pre_vy"),
        "mean_dvz": observed("post_vz", "pre_vz"),
        "mean_droll_rate": observed(
            "post_roll_rate", "pre_roll_rate"
        ),
        "mean_dpitch_rate": observed(
            "post_pitch_rate", "pre_pitch_rate"
        ),
        "mean_dyaw_rate": observed(
            "post_yaw_rate", "pre_yaw_rate"
        ),
        "mean_drotor_fraction": observed(
            "post_rotor_fraction", "pre_rotor_fraction"
        ),
    }
    prediction_error = Sqrt(Plus(*(
        square(Minus(value, P0("model", key)))
        for key, value in deltas.items()
    )))
    surprising = Gt(
        prediction_error,
        Plus(
            P0("policy", "surprise_floor"),
            Times(
                P0("policy", "surprise_factor"),
                P0("model", "prediction_error_ema"),
            ),
        ),
    )
    rate = Ite(
        Lt(P0("model", "experience_count"), P0("policy", "babble_samples")),
        initial_rate,
        Ite(
            surprising,
            P0("policy", "surprise_adaptation_rate"),
            P0("policy", "adaptation_rate"),
        ),
    )

    def update(key, value):
        return Plus(
            P0("model", key),
            Times(rate, Minus(value, P0("model", key))),
        )

    effects = [
        ["set_attr", "outcome", "prediction_error", T(prediction_error)],
        ["set_attr", "outcome", "surprise", T(Ite(
            surprising, L(1.0), L(0.0)
        ))],
        ["set_attr", "outcome", "adaptation_rate", T(rate)],
    ]
    effects.extend(
        ["set_attr", "model", key, T(update(key, value))]
        for key, value in deltas.items()
    )
    effects.extend([
        ["set_attr", "model", "mean_supplied_energy_joules", T(update(
            "mean_supplied_energy_joules",
            P0("outcome", "supplied_energy_joules"),
        ))],
        ["set_attr", "model", "mean_recovered_energy_joules", T(update(
            "mean_recovered_energy_joules",
            P0("outcome", "recovered_energy_joules"),
        ))],
        ["set_attr", "model", "prediction_error_ema", T(update(
            "prediction_error_ema", prediction_error
        ))],
        ["set_attr", "model", "experience_count", T(count)],
        ["set_attr", "model", "surprise_count", T(Plus(
            P0("model", "surprise_count"),
            P0("outcome", "surprise"),
        ))],
        ["set_attr", "episode", "authority_change_count", T(Plus(
            P0("episode", "authority_change_count"),
            P0("outcome", "surprise"),
        ))],
        ["set_attr", "outcome", "processed", 1.0],
        ["set_attr", "trial", "status", "learned"],
    ])
    return {
        "name": "ha_learn_local_energy_dynamics",
        "area": "adaptive_learning",
        "latency_class": "soft_realtime",
        "comment": "Update local action consequences from verified physical "
        "receipts. Prediction error accelerates adaptation after an unlabelled "
        "authority change.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_helicopter_energy_trial", "trial"],
            ["trial", "uses_energy_action_model", "model"],
            ["trial", "has_helicopter_energy_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
        ),
        "effects": effects,
    }


def memorise_bounded_intervention_rule():
    observed_dvx = Minus(P0("outcome", "post_vx"), P0("outcome", "pre_vx"))
    observed_dvy = Minus(P0("outcome", "post_vy"), P0("outcome", "pre_vy"))
    observed_dvz = Minus(P0("outcome", "post_vz"), P0("outcome", "pre_vz"))
    observed_droll_rate = Minus(
        P0("outcome", "post_roll_rate"),
        P0("outcome", "pre_roll_rate"),
    )
    observed_dpitch_rate = Minus(
        P0("outcome", "post_pitch_rate"),
        P0("outcome", "pre_pitch_rate"),
    )
    observed_dyaw_rate = Minus(
        P0("outcome", "post_yaw_rate"),
        P0("outcome", "pre_yaw_rate"),
    )
    observed_drotor = Minus(
        P0("outcome", "post_rotor_fraction"),
        P0("outcome", "pre_rotor_fraction"),
    )
    return {
        "name": "ha_memorise_bounded_intervention",
        "area": "embodied_sensorimotor",
        "latency_class": "background",
        "comment": "Retain reset-bounded interventions as local causal "
        "exemplars. Ordinary flight updates compact action models without "
        "unbounded episodic growth.",
        "match": [
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_helicopter_energy_trial", "trial"],
            ["trial", "uses_energy_action_model", "model"],
            ["trial", "has_helicopter_energy_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "bounded_intervention"), L(1.0)),
            Eq(P0("outcome", "memory_recorded"), L(0.0)),
        ),
        "effects": [
            ["add_node", "memory", "HelicopterEnergyTransitionMemory", {
                "token": T(A("model", "token")),
                "contact_horizon_context": T(
                    P0("model", "contact_horizon_context")
                ),
                "pre_vx": T(P0("outcome", "pre_vx")),
                "pre_vy": T(P0("outcome", "pre_vy")),
                "pre_vz": T(P0("outcome", "pre_vz")),
                "pre_roll": T(P0("outcome", "pre_roll")),
                "pre_pitch": T(P0("outcome", "pre_pitch")),
                "pre_yaw": T(P0("outcome", "pre_yaw")),
                "pre_roll_rate": T(P0("outcome", "pre_roll_rate")),
                "pre_pitch_rate": T(P0("outcome", "pre_pitch_rate")),
                "pre_yaw_rate": T(P0("outcome", "pre_yaw_rate")),
                "pre_rotor_fraction": T(
                    P0("outcome", "pre_rotor_fraction")
                ),
                "pre_time_to_contact_seconds": T(
                    P0("outcome", "pre_time_to_contact_seconds")
                ),
                "mean_dvx": T(observed_dvx),
                "mean_dvy": T(observed_dvy),
                "mean_dvz": T(observed_dvz),
                "mean_droll_rate": T(observed_droll_rate),
                "mean_dpitch_rate": T(observed_dpitch_rate),
                "mean_dyaw_rate": T(observed_dyaw_rate),
                "mean_drotor_fraction": T(observed_drotor),
                "mean_supplied_energy_joules": T(
                    P0("outcome", "supplied_energy_joules")
                ),
                "mean_recovered_energy_joules": T(
                    P0("outcome", "recovered_energy_joules")
                ),
                "provenance": "verified_bounded_local_consequence",
            }],
            ["add_edge", "episode", "has_energy_transition_memory", "memory"],
            ["set_attr", "outcome", "memory_recorded", 1.0],
        ],
    }


def request_motor_learning_rule():
    """A verified receipt graph-authorizes its interruptible learning sheet."""
    return {
        "name": "ha_request_motor_learning",
        "area": "embodied_energy_control",
        "order": -10,
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Receipt verification is the fast causal boundary; model "
        "revision and exemplar retention run only in the recruited slower sheet.",
        "match": [
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
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_helicopter_energy_trial", "trial"],
            ["trial", "has_helicopter_energy_outcome", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(
                P0("outcome", "helicopter_learning_escalation_requested"),
                L(0.0),
            ),
        ),
        "effects": [
            ["add_node", "escalation", "SystemTwoEscalation", {
                "status": "requested",
                "reason": "verified_helicopter_motor_receipt",
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
            [
                "set_attr",
                "outcome",
                "helicopter_learning_escalation_requested",
                1.0,
            ],
        ],
    }


def expose_motor_decision_option_rule():
    """Publish a neutral common schema before an option enters a decision."""
    return {
        "name": "ha_expose_motor_decision_option",
        "area": "embodied_sensorimotor",
        "latency_class": "background",
        "comment": "Give each opaque compact action model the domain-neutral "
        "fields used by the shared collapse. Physical experience remains "
        "separate from decision-habit experience.",
        "match": [
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_energy_action_model", "model"],
        ],
        "where": Eq(P0("model", "motor_option_schema_ready"), L(0.0)),
        "effects": [
            ["set_attr", "model", "available", 1.0],
            ["set_attr", "model", "ordinal", T(P0("model", "ordinal"))],
            ["set_attr", "model", "default_value", 0.0],
            ["set_attr", "model", "learned_value", 0.0],
            ["set_attr", "model", "grounded_value", 0.0],
            ["set_attr", "model", "decision_experience_count", 0.0],
            ["set_attr", "model", "motor_option_schema_ready", 1.0],
            [
                "set_attr",
                "model",
                "motor_option_value_provenance",
                "neutral_schema_ready_for_shared_collapse",
            ],
        ],
    }


def prepare_shared_memory_options_rule():
    """Ground contextual exemplar options in recoverable-energy viability."""
    return {
        "name": "ha_prepare_shared_memory_options",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Project each verified local consequence into the existing "
        "recoverable-energy/contact cost and expose its negation as a shared "
        "collapse value. The selected node remains the exact causal exemplar.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_energy_transition_memory", "memory"],
            ["episode", "has_energy_action_model", "model"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MEMORIES), L(0.0)),
            Eq(A("memory", "token"), A("model", "token")),
            Lt(
                P0("memory", "motor_decision_value_epoch"),
                P0("episode", "request_seq"),
            ),
        ),
        "effects": [
            ["add_edge", "episode", "has_motor_decision_option", "memory"],
            ["set_attr", "memory", "available", 1.0],
            ["set_attr", "memory", "ordinal", T(P0("model", "ordinal"))],
            ["set_attr", "memory", "default_value", 0.0],
            ["set_attr", "memory", "grounded_value", T(Minus(
                L(0.0),
                contextual_memory_cost("memory", "episode", "policy"),
            ))],
            ["set_attr", "memory", "motor_decision_value_epoch", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "memory", "motor_option_schema_ready", 1.0],
            ["set_attr", "memory", "motor_option_value_provenance",
             "grounded_contextual_energy_viability_cost"],
        ],
    }


def retire_shared_compact_options_rule():
    """Remove compact options once richer contextual exemplars are available."""
    return {
        "name": "ha_retire_shared_compact_options",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "A contextual exemplar supersedes the compact fallback. "
        "Remove the old episode scope before arming the next atomic collapse.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_energy_action_model", "model"],
            ["episode", "has_motor_decision_option", "model"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Gt(Count(MEMORIES), L(0.0)),
        ),
        "effects": [
            ["del_edge", "episode", "has_motor_decision_option", "model"],
        ],
    }


def arm_shared_memory_collapse_rule():
    prepared = Filter(
        MEMORIES,
        "candidate",
        Eq(
            P0("candidate", "motor_decision_value_epoch"),
            P0("episode", "request_seq"),
        ),
    )
    return {
        "name": "ha_arm_shared_memory_collapse",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Arm only after every contextual option has a value for "
        "this request, preventing collapse over a partially updated option set.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MEMORIES), L(0.0)),
            Eq(Count(prepared), Count(MEMORIES)),
            Eq(P0("episode", "decision_armed"), L(0.0)),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "last_published_decision_epoch"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "decision_request_epoch", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_armed", 1.0],
            ["set_attr", "episode", "decision_status", "armed"],
        ],
    }


def release_shared_memory_collapse_rule():
    return {
        "name": "ha_release_shared_memory_collapse",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "Release the exact contextual graph option published by "
        "the shared collapse into the existing opaque actuator interface.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_energy_transition_memory", "memory"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(A("episode", "decision_status"), L("published")),
            Eq(
                P0("episode", "selected_decision_epoch"),
                P0("episode", "request_seq"),
            ),
            Eq(A("episode", "selected_option_ref"), V("memory")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(A("memory", "token"))],
            ["set_attr", "episode", "decision_kind",
             "shared_energy_viability_model"],
            ["set_attr", "episode", "predicted_action_cost", T(Minus(
                L(0.0),
                P0("memory", "grounded_value"),
            ))],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def prepare_shared_compact_options_rule():
    return {
        "name": "ha_prepare_shared_compact_options",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "When no local exemplar exists, expose the compact learned "
        "dynamics model through the same shared collapse.",
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_energy_action_model", "model"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Eq(Count(MEMORIES), L(0.0)),
            Eq(
                P0("model", "contact_horizon_context"),
                P0("episode", "contact_horizon_context"),
            ),
            Lt(
                P0("model", "motor_decision_value_epoch"),
                P0("episode", "request_seq"),
            ),
        ),
        "effects": [
            ["add_edge", "episode", "has_motor_decision_option", "model"],
            ["set_attr", "model", "available", 1.0],
            ["set_attr", "model", "grounded_value", T(Minus(
                L(0.0),
                action_cost("model", "episode", "policy"),
            ))],
            ["set_attr", "model", "motor_decision_value_epoch", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "model", "motor_option_value_provenance",
             "grounded_compact_energy_viability_cost"],
        ],
    }


def arm_shared_compact_collapse_rule():
    prepared = Filter(
        ACTIVE_MODELS,
        "candidate",
        Eq(
            P0("candidate", "motor_decision_value_epoch"),
            P0("episode", "request_seq"),
        ),
    )
    return {
        "name": "ha_arm_shared_compact_collapse",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Eq(Count(MEMORIES), L(0.0)),
            Gt(Count(ACTIVE_MODELS), L(0.0)),
            Eq(Count(prepared), Count(ACTIVE_MODELS)),
            Eq(P0("episode", "decision_armed"), L(0.0)),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "last_published_decision_epoch"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "decision_request_epoch", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_armed", 1.0],
            ["set_attr", "episode", "decision_status", "armed"],
        ],
    }


def release_shared_compact_collapse_rule():
    return {
        "name": "ha_release_shared_compact_collapse",
        "area": "embodied_energy_control",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_helicopter_energy_policy", "policy"],
            ["agent", "has_helicopter_episode", "episode"],
            ["episode", "has_energy_action_model", "model"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(A("episode", "decision_status"), L("published")),
            Eq(
                P0("episode", "selected_decision_epoch"),
                P0("episode", "request_seq"),
            ),
            Eq(A("episode", "selected_option_ref"), V("model")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(A("model", "token"))],
            ["set_attr", "episode", "decision_kind",
             "shared_compact_energy_model"],
            ["set_attr", "episode", "predicted_action_cost", T(Minus(
                L(0.0),
                P0("model", "grounded_value"),
            ))],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def manifest():
    return {
        "id": "helicopter_autorotation",
        "version": "1.1.0",
        "depends_on": [
            "embodied_motor_priors",
            "motor_decision_collapse",
        ],
        "area": "embodied_energy_control",
        "latency_class": "soft_realtime",
        "description": "Graph-native adaptation to an unlabelled loss of "
        "powered authority using opaque controls and energy/viability priors.",
        "microtheory": {
            "name": "recoverable_energy_control",
            "description": "Preserve useful internal energy and spend it only "
            "as contact-relative kinetic energy becomes dangerous.",
        },
        "nodes": [{
            "local_id": 1,
            "type": "HelicopterEnergyPolicy",
            "attrs": {
                "name": "generic_recoverable_energy_viability",
                "babble_samples": 1.0,
                "action_duration_seconds": 0.1,
                "attitude_projection_seconds": 0.8,
                "pitch_attitude_projection_seconds": 0.1,
                "maximum_projection_steps": 1.0,
                "adaptation_rate": 0.02,
                "surprise_adaptation_rate": 0.25,
                "surprise_factor": 1.8,
                "surprise_floor": 0.002,
                "preferred_rotor_fraction": 0.98,
                "minimum_viable_rotor_fraction": 0.78,
                "rotor_reserve_weight": 100.0,
                "vertical_kinetic_weight": 2.5,
                "horizontal_kinetic_weight": 5.0,
                "lateral_kinetic_weight": 20.0,
                "transverse_angular_rate_weight": 15.0,
                "pitch_rate_weight": 1.0,
                "contact_attitude_weight": 35.0,
                "flight_roll_attitude_weight": 300.0,
                "flight_pitch_attitude_weight": 45.0,
                "flight_yaw_attitude_weight": 6.75,
                "yaw_attitude_fraction": 0.15,
                "effort_weight": 0.000001,
                "recovery_weight": 0.00001,
                "cruise_sink_speed": 6.5,
                "cruise_forward_speed": 18.0,
                "comfortable_vertical_acceleration": 1.8,
                "comfortable_horizontal_acceleration": 2.2,
                "contact_clearance": 0.0,
                "attitude_relaxation_altitude": 12.0,
                "approach_contact_horizon_seconds": 2.5,
                "imminent_contact_horizon_seconds": 0.8,
                "maximum_touchdown_vertical_speed": 2.5,
                "maximum_touchdown_horizontal_speed": 8.0,
                "maximum_touchdown_lateral_speed": 4.0,
                "maximum_touchdown_attitude": 0.3141592653589793,
                "context_distance_weight": 1.0,
                "context_vx_weight": 0.08,
                "context_vy_weight": 0.2,
                "context_vz_weight": 0.3,
                "context_roll_weight": 35.0,
                "context_pitch_weight": 35.0,
                "context_roll_rate_weight": 8.0,
                "context_pitch_rate_weight": 8.0,
                "context_yaw_rate_weight": 4.0,
                "context_rotor_weight": 120.0,
                "context_contact_horizon_weight": 0.02,
                "shared_motor_collapse_enabled": 1.0,
                "provenance": "generic_energy_and_contact_viability_priors",
            },
        }],
        "edges": [{
            "src": {"role": "agent_root"},
            "type": "has_helicopter_energy_policy",
            "tgt": {"local": 1},
            "attrs": {},
        }],
        "productions": [
            {
                "provenance": "helicopter_autorotation:agent_policy",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_helicopter_energy_policy",
                "tgt": {"type": "HelicopterEnergyPolicy", "var": "policy"},
            },
            {
                "provenance": "helicopter_autorotation:agent_episode",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_helicopter_episode",
                "tgt": {"type": "HelicopterEnergyEpisode", "var": "episode"},
            },
            {
                "provenance": "helicopter_autorotation:episode_model",
                "src": {"type": "HelicopterEnergyEpisode", "var": "episode"},
                "edge_type": "has_energy_action_model",
                "tgt": {"type": "HelicopterEnergyActionModel", "var": "model"},
            },
            {
                "provenance": "helicopter_autorotation:episode_trial",
                "src": {"type": "HelicopterEnergyEpisode", "var": "episode"},
                "edge_type": "has_helicopter_energy_trial",
                "tgt": {"type": "HelicopterEnergyTrial", "var": "trial"},
            },
            {
                "provenance": "helicopter_autorotation:trial_model",
                "src": {"type": "HelicopterEnergyTrial", "var": "trial"},
                "edge_type": "uses_energy_action_model",
                "tgt": {"type": "HelicopterEnergyActionModel", "var": "model"},
            },
            {
                "provenance": "helicopter_autorotation:trial_outcome",
                "src": {"type": "HelicopterEnergyTrial", "var": "trial"},
                "edge_type": "has_helicopter_energy_outcome",
                "tgt": {"type": "HelicopterEnergyOutcome", "var": "outcome"},
            },
            {
                "provenance": "helicopter_autorotation:episode_memory",
                "src": {"type": "HelicopterEnergyEpisode", "var": "episode"},
                "edge_type": "has_energy_transition_memory",
                "tgt": {
                    "type": "HelicopterEnergyTransitionMemory",
                    "var": "memory",
                },
            },
        ],
        "rules": [
            measure_rule(),
            choose_babble_rule(),
            choose_learned_rule(),
            choose_compact_model_fallback_rule(),
            prepare_shared_memory_options_rule(),
            retire_shared_compact_options_rule(),
            arm_shared_memory_collapse_rule(),
            release_shared_memory_collapse_rule(),
            prepare_shared_compact_options_rule(),
            arm_shared_compact_collapse_rule(),
            release_shared_compact_collapse_rule(),
            open_trial_rule(),
            request_motor_learning_rule(),
            memorise_bounded_intervention_rule(),
            learn_rule(),
            expose_motor_decision_option_rule(),
        ],
    }


def main():
    output = os.path.join(ROOT, "seeds", "helicopter_autorotation.json")
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(manifest(), handle, indent=1)
        handle.write("\n")
    print(f"wrote {output} ({len(manifest()['rules'])} rules)")


if __name__ == "__main__":
    main()
