"""Generate graph-native three-dimensional sensorimotor flight rules.

The authoring script emits Rust-evaluated Term trees. At runtime Python only
copies raw simulator receipts and enacts the opaque token selected by the graph.
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


def Or(*items):
    return {"type": "Or", "items": list(items)}


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


MODELS = Neighbours("episode", "has_aerial_action_model")
UNSAMPLED = Filter(
    MODELS,
    "candidate",
    Lt(P0("candidate", "experience_count"), P0("policy", "babble_samples")),
)


def spatial_norm(x, y, z):
    return Sqrt(
        Plus(
            Times(x, x),
            Times(y, y),
            Times(z, z),
        )
    )


def predicted_goal_distance(model, episode):
    return spatial_norm(
        Minus(
            Minus(P0(episode, "goal_x"), P0(episode, "state_x")),
            Times(
                P0("policy", "action_duration_seconds"),
                L(0.5),
                Plus(
                    P0(episode, "state_vx"),
                    P0(model, "mean_post_vx"),
                ),
            ),
        ),
        Minus(
            Minus(P0(episode, "goal_y"), P0(episode, "state_y")),
            Times(
                P0("policy", "action_duration_seconds"),
                L(0.5),
                Plus(
                    P0(episode, "state_vy"),
                    P0(model, "mean_post_vy"),
                ),
            ),
        ),
        Minus(
            Minus(P0(episode, "goal_z"), P0(episode, "state_z")),
            Times(
                P0("policy", "action_duration_seconds"),
                L(0.5),
                Plus(
                    P0(episode, "state_vz"),
                    P0(model, "mean_post_vz"),
                ),
            ),
        ),
    )


def learned_motion_magnitude(model):
    return spatial_norm(
        P0(model, "mean_post_vx"),
        P0(model, "mean_post_vy"),
        P0(model, "mean_post_vz"),
    )


def predicted_angular_speed(model, episode):
    return spatial_norm(
        Plus(P0(episode, "state_wx"), P0(model, "mean_dwx")),
        Plus(P0(episode, "state_wy"), P0(model, "mean_dwy")),
        Plus(P0(episode, "state_wz"), P0(model, "mean_dwz")),
    )


def control_cost(model, episode, at_goal):
    spatial_cost = Ite(
        at_goal,
        learned_motion_magnitude(model),
        predicted_goal_distance(model, episode),
    )
    return Plus(
        spatial_cost,
        Times(
            P0("policy", "angular_stability_weight"),
            predicted_angular_speed(model, episode),
        ),
    )


def measure_goal_rule():
    dx = Minus(P0("episode", "goal_x"), P0("episode", "state_x"))
    dy = Minus(P0("episode", "goal_y"), P0("episode", "state_y"))
    dz = Minus(P0("episode", "goal_z"), P0("episode", "state_z"))
    distance = spatial_norm(dx, dy, dz)
    current_altitude_gain = Minus(
        P0("episode", "state_z"),
        P0("episode", "takeoff_origin_z"),
    )
    return {
        "name": "aa_measure_flight_state",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Three-dimensional distance, takeoff, and success are graph "
        "assessments over raw pose. The host only records the verdict.",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
        ],
        "where": Lt(
            P0("episode", "measured_state_seq"),
            P0("episode", "state_seq"),
        ),
        "effects": [
            ["set_attr", "episode", "previous_goal_distance", T(
                P0("episode", "goal_distance")
            )],
            ["set_attr", "episode", "goal_progress", T(
                Minus(P0("episode", "goal_distance"), distance)
            )],
            ["set_attr", "episode", "goal_distance", T(distance)],
            ["set_attr", "episode", "peak_altitude_gain", T(
                Ite(
                    Gt(
                        current_altitude_gain,
                        P0("episode", "peak_altitude_gain"),
                    ),
                    current_altitude_gain,
                    P0("episode", "peak_altitude_gain"),
                )
            )],
            ["set_attr", "episode", "flight_achieved", T(
                Ite(
                    Gt(
                        current_altitude_gain,
                        P0("policy", "goal_radius"),
                    ),
                    L(1.0),
                    P0("episode", "flight_achieved"),
                )
            )],
            ["set_attr", "episode", "goal_reached", T(
                Ite(
                    Lt(distance, P0("policy", "goal_radius")),
                    L(1.0),
                    L(0.0),
                )
            )],
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
        "name": "aa_choose_motor_babble",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Intervene on every opaque command before using a learned "
        "consequence. Ordering is graph-held and conveys no actuator semantics.",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Gt(Count(UNSAMPLED), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "predicted_dx", T(AttrOf(best, "mean_dx"))],
            ["set_attr", "episode", "predicted_dy", T(AttrOf(best, "mean_dy"))],
            ["set_attr", "episode", "predicted_dz", T(AttrOf(best, "mean_dz"))],
            ["set_attr", "episode", "predicted_dwx", T(
                AttrOf(best, "mean_dwx")
            )],
            ["set_attr", "episode", "predicted_dwy", T(
                AttrOf(best, "mean_dwy")
            )],
            ["set_attr", "episode", "predicted_dwz", T(
                AttrOf(best, "mean_dwz")
            )],
            ["set_attr", "episode", "decision_kind", "motor_babble"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
        ],
    }


def choose_goal_action_rule():
    best = Argmin(
        MODELS,
        "candidate",
        control_cost(
            "candidate",
            "episode",
            Gt(P0("episode", "goal_reached"), L(0.5)),
        ),
        V("episode"),
    )
    return {
        "name": "aa_choose_learned_flight_action",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Choose the opaque command whose learned three-dimensional "
        "consequence leaves the smallest goal residual. At the goal, choose the "
        "empirically quietest consequence. No command direction is imported.",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(0.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MODELS), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "predicted_dx", T(AttrOf(best, "mean_dx"))],
            ["set_attr", "episode", "predicted_dy", T(AttrOf(best, "mean_dy"))],
            ["set_attr", "episode", "predicted_dz", T(AttrOf(best, "mean_dz"))],
            ["set_attr", "episode", "predicted_dwx", T(
                AttrOf(best, "mean_dwx")
            )],
            ["set_attr", "episode", "predicted_dwy", T(
                AttrOf(best, "mean_dwy")
            )],
            ["set_attr", "episode", "predicted_dwz", T(
                AttrOf(best, "mean_dwz")
            )],
            ["set_attr", "episode", "decision_kind", "learned_flight_model"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
        ],
    }


def prepare_shared_flight_values_rule():
    return {
        "name": "aa_prepare_shared_motor_collapse_values",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
            ["episode", "has_aerial_action_model", "model"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MODELS), L(0.0)),
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
                control_cost(
                    "model",
                    "episode",
                    Gt(P0("episode", "goal_reached"), L(0.5)),
                ),
            ))],
            ["set_attr", "model", "motor_decision_value_epoch", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "model", "motor_option_schema_ready", 1.0],
            [
                "set_attr",
                "model",
                "motor_option_value_provenance",
                "grounded_existing_flight_control_cost",
            ],
        ],
    }


def arm_shared_flight_collapse_rule():
    prepared = Filter(
        MODELS,
        "candidate",
        Eq(
            P0("candidate", "motor_decision_value_epoch"),
            P0("episode", "request_seq"),
        ),
    )
    return {
        "name": "aa_arm_shared_motor_collapse",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(Count(prepared), Count(MODELS)),
            Gt(Count(MODELS), L(0.0)),
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
        ],
    }


def release_shared_flight_collapse_rule():
    return {
        "name": "aa_release_shared_motor_collapse",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
            ["episode", "has_aerial_action_model", "model"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(A("episode", "decision_status"), L("published")),
            Eq(
                P0("episode", "selected_decision_epoch"),
                P0("episode", "request_seq"),
            ),
            Eq(A("episode", "selected_option_ref"), V("model")),
            Eq(A("episode", "selected_token"), A("model", "token")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
        ),
        "effects": [
            ["set_attr", "episode", "predicted_dx", T(P0("model", "mean_dx"))],
            ["set_attr", "episode", "predicted_dy", T(P0("model", "mean_dy"))],
            ["set_attr", "episode", "predicted_dz", T(P0("model", "mean_dz"))],
            ["set_attr", "episode", "predicted_dwx", T(P0("model", "mean_dwx"))],
            ["set_attr", "episode", "predicted_dwy", T(P0("model", "mean_dwy"))],
            ["set_attr", "episode", "predicted_dwz", T(P0("model", "mean_dwz"))],
            ["set_attr", "episode", "decision_kind", "shared_flight_model"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "decision_count", T(Plus(
                P0("episode", "decision_count"),
                L(1.0),
            ))],
        ],
    }


def open_trial_rule():
    return {
        "name": "aa_open_flight_trial",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Materialise the selected opaque action and graph prediction "
        "before the simulator is touched.",
        "match": [
            ["agent", "has_aerial_episode", "episode"],
            ["episode", "has_aerial_action_model", "model"],
        ],
        "where": And(
            Eq(P0("episode", "action_ready"), L(1.0)),
            Eq(A("episode", "selected_token"), A("model", "token")),
            Lt(P0("episode", "last_trial_epoch"), P0("episode", "epoch")),
        ),
        "effects": [
            ["add_node", "trial", "AerialMotorTrial", {
                "epoch": T(P0("episode", "epoch")),
                "token": T(A("model", "token")),
                "decision_kind": T(A("episode", "decision_kind")),
                "status": "issued",
                "predicted_dx": T(P0("episode", "predicted_dx")),
                "predicted_dy": T(P0("episode", "predicted_dy")),
                "predicted_dz": T(P0("episode", "predicted_dz")),
                "predicted_dwx": T(P0("episode", "predicted_dwx")),
                "predicted_dwy": T(P0("episode", "predicted_dwy")),
                "predicted_dwz": T(P0("episode", "predicted_dwz")),
                "prediction_provenance": "graph_aerial_forward_model",
            }],
            ["add_edge", "episode", "has_aerial_motor_trial", "trial"],
            ["add_edge", "trial", "uses_aerial_action_model", "model"],
            ["set_attr", "episode", "last_trial_epoch", T(
                P0("episode", "epoch")
            )],
        ],
    }


def learn_rule():
    observed_dx = Minus(P0("outcome", "post_x"), P0("outcome", "pre_x"))
    observed_dy = Minus(P0("outcome", "post_y"), P0("outcome", "pre_y"))
    observed_dz = Minus(P0("outcome", "post_z"), P0("outcome", "pre_z"))
    observed_post_vx = P0("outcome", "post_vx")
    observed_post_vy = P0("outcome", "post_vy")
    observed_post_vz = P0("outcome", "post_vz")
    observed_dwx = Minus(P0("outcome", "post_wx"), P0("outcome", "pre_wx"))
    observed_dwy = Minus(P0("outcome", "post_wy"), P0("outcome", "pre_wy"))
    observed_dwz = Minus(P0("outcome", "post_wz"), P0("outcome", "pre_wz"))
    count = Plus(P0("model", "experience_count"), L(1.0))
    calibrated = Gt(
        P0("model", "experience_count"),
        Minus(P0("policy", "babble_samples"), L(0.5)),
    )
    spatial_prediction_error = spatial_norm(
        Minus(observed_dx, P0("trial", "predicted_dx")),
        Minus(observed_dy, P0("trial", "predicted_dy")),
        Minus(observed_dz, P0("trial", "predicted_dz")),
    )
    angular_prediction_error = spatial_norm(
        Minus(observed_dwx, P0("trial", "predicted_dwx")),
        Minus(observed_dwy, P0("trial", "predicted_dwy")),
        Minus(observed_dwz, P0("trial", "predicted_dwz")),
    )
    prediction_error = Plus(
        spatial_prediction_error,
        Times(
            P0("policy", "angular_stability_weight"),
            angular_prediction_error,
        ),
    )
    surprising = And(
        calibrated,
        Gt(
            prediction_error,
            Plus(
                P0("policy", "surprise_floor"),
                Times(
                    P0("policy", "surprise_factor"),
                    P0("model", "error_ema"),
                ),
            ),
        ),
    )
    adaptation_rate = Ite(
        calibrated,
        Ite(
            surprising,
            P0("policy", "surprise_adaptation_rate"),
            P0("policy", "adaptation_rate"),
        ),
        Div(L(1.0), count),
    )

    def adaptive_mean(key, observation):
        return Plus(
            P0("model", key),
            Times(
                adaptation_rate,
                Minus(observation, P0("model", key)),
            ),
        )

    error_ema = Plus(
        P0("model", "error_ema"),
        Times(
            P0("policy", "error_adaptation_rate"),
            Minus(prediction_error, P0("model", "error_ema")),
        ),
    )
    plasticity_active = Or(
        Eq(A("episode", "mode"), L("adaptive_flight")),
        Lt(
            P0("episode", "epoch"),
            P0("policy", "plasticity_stop_epoch"),
        ),
    )
    return {
        "name": "aa_learn_aerial_forward_model",
        "area": "adaptive_learning",
        "latency_class": "soft_realtime",
        "comment": "Update the selected opaque command's three-dimensional "
        "consequence from a verified simulator receipt, entirely in graph state.",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
            ["episode", "has_aerial_motor_trial", "trial"],
            ["trial", "uses_aerial_action_model", "model"],
            ["trial", "has_aerial_transition_outcome", "outcome"],
        ],
        "where": And(
            plasticity_active,
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "outcome", "observed_dx", T(observed_dx)],
            ["set_attr", "outcome", "observed_dy", T(observed_dy)],
            ["set_attr", "outcome", "observed_dz", T(observed_dz)],
            ["set_attr", "outcome", "observed_dwx", T(observed_dwx)],
            ["set_attr", "outcome", "observed_dwy", T(observed_dwy)],
            ["set_attr", "outcome", "observed_dwz", T(observed_dwz)],
            ["set_attr", "outcome", "prediction_error", T(prediction_error)],
            ["set_attr", "outcome", "surprise", T(
                Ite(surprising, L(1.0), L(0.0))
            )],
            ["set_attr", "outcome", "adaptation_rate", T(adaptation_rate)],
            ["set_attr", "model", "mean_dx", T(
                adaptive_mean("mean_dx", observed_dx)
            )],
            ["set_attr", "model", "mean_dy", T(
                adaptive_mean("mean_dy", observed_dy)
            )],
            ["set_attr", "model", "mean_dz", T(
                adaptive_mean("mean_dz", observed_dz)
            )],
            ["set_attr", "model", "mean_post_vx", T(
                adaptive_mean("mean_post_vx", observed_post_vx)
            )],
            ["set_attr", "model", "mean_post_vy", T(
                adaptive_mean("mean_post_vy", observed_post_vy)
            )],
            ["set_attr", "model", "mean_post_vz", T(
                adaptive_mean("mean_post_vz", observed_post_vz)
            )],
            ["set_attr", "model", "mean_dwx", T(
                adaptive_mean("mean_dwx", observed_dwx)
            )],
            ["set_attr", "model", "mean_dwy", T(
                adaptive_mean("mean_dwy", observed_dwy)
            )],
            ["set_attr", "model", "mean_dwz", T(
                adaptive_mean("mean_dwz", observed_dwz)
            )],
            ["set_attr", "model", "energy_ema_joules", T(
                adaptive_mean(
                    "energy_ema_joules",
                    P0("outcome", "input_energy_joules"),
                )
            )],
            ["set_attr", "model", "experience_count", T(count)],
            ["set_attr", "model", "error_ema", T(error_ema)],
            ["set_attr", "model", "surprise_count", T(
                Plus(
                    P0("model", "surprise_count"),
                    P0("outcome", "surprise"),
                )
            )],
            ["set_attr", "model", "last_prediction_error", T(prediction_error)],
            ["set_attr", "model", "last_update_epoch", T(
                P0("episode", "epoch")
            )],
            ["set_attr", "episode", "last_observed_dx", T(observed_dx)],
            ["set_attr", "episode", "last_observed_dy", T(observed_dy)],
            ["set_attr", "episode", "last_observed_dz", T(observed_dz)],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "learned"],
        ],
    }


def close_frozen_trial_rule():
    observed_dx = Minus(P0("outcome", "post_x"), P0("outcome", "pre_x"))
    observed_dy = Minus(P0("outcome", "post_y"), P0("outcome", "pre_y"))
    observed_dz = Minus(P0("outcome", "post_z"), P0("outcome", "pre_z"))
    observed_dwx = Minus(P0("outcome", "post_wx"), P0("outcome", "pre_wx"))
    observed_dwy = Minus(P0("outcome", "post_wy"), P0("outcome", "pre_wy"))
    observed_dwz = Minus(P0("outcome", "post_wz"), P0("outcome", "pre_wz"))
    prediction_error = Plus(
        spatial_norm(
            Minus(observed_dx, P0("trial", "predicted_dx")),
            Minus(observed_dy, P0("trial", "predicted_dy")),
            Minus(observed_dz, P0("trial", "predicted_dz")),
        ),
        Times(
            P0("policy", "angular_stability_weight"),
            spatial_norm(
                Minus(observed_dwx, P0("trial", "predicted_dwx")),
                Minus(observed_dwy, P0("trial", "predicted_dwy")),
                Minus(observed_dwz, P0("trial", "predicted_dwz")),
            ),
        ),
    )
    return {
        "name": "aa_close_frozen_flight_trial",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Close a receipt-backed trial after plasticity is frozen "
        "without changing its AerialActionModel.",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
            ["episode", "has_aerial_motor_trial", "trial"],
            ["trial", "has_aerial_transition_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("episode", "mode"), L("frozen_flight")),
            Gt(
                P0("episode", "epoch"),
                Minus(P0("policy", "plasticity_stop_epoch"), L(0.5)),
            ),
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "outcome", "observed_dx", T(observed_dx)],
            ["set_attr", "outcome", "observed_dy", T(observed_dy)],
            ["set_attr", "outcome", "observed_dz", T(observed_dz)],
            ["set_attr", "outcome", "observed_dwx", T(observed_dwx)],
            ["set_attr", "outcome", "observed_dwy", T(observed_dwy)],
            ["set_attr", "outcome", "observed_dwz", T(observed_dwz)],
            ["set_attr", "outcome", "prediction_error", T(prediction_error)],
            ["set_attr", "outcome", "surprise", 0.0],
            ["set_attr", "outcome", "adaptation_rate", 0.0],
            ["set_attr", "episode", "last_observed_dx", T(observed_dx)],
            ["set_attr", "episode", "last_observed_dy", T(observed_dy)],
            ["set_attr", "episode", "last_observed_dz", T(observed_dz)],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "observed_no_learning"],
        ],
    }


def detect_direct_control_emergency_rule():
    angular_speed = spatial_norm(
        P0("episode", "state_wx"),
        P0("episode", "state_wy"),
        P0("episode", "state_wz"),
    )
    failed_motor = Ite(
        Gt(P0("episode", "state_wx"), L(0.0)),
        Ite(
            Gt(P0("episode", "state_wy"), L(0.0)),
            L(0.0),
            L(1.0),
        ),
        Ite(
            Lt(P0("episode", "state_wy"), L(0.0)),
            L(2.0),
            L(3.0),
        ),
    )
    return {
        "name": "aa_detect_direct_control_emergency",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Infer the failed CF2X motor quadrant after angular motion "
        "exceeds the declared diagnostic evidence threshold, then latch the "
        "current position as the reduced-attitude hold target.",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "direct_authority_enabled"), L(1.0)),
            Eq(P0("episode", "emergency_active"), L(0.0)),
            Gt(
                angular_speed,
                P0("policy", "emergency_angular_speed_threshold"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "emergency_active", 1.0],
            ["set_attr", "episode", "failed_motor_ordinal", T(failed_motor)],
            ["set_attr", "episode", "emergency_target_x", T(
                P0("episode", "state_x")
            )],
            ["set_attr", "episode", "emergency_target_y", T(
                P0("episode", "state_y")
            )],
            ["set_attr", "episode", "emergency_target_z", T(
                P0("episode", "state_z")
            )],
            ["set_attr", "episode", "emergency_detection_state_seq", T(
                P0("episode", "state_seq")
            )],
        ],
    }


def direct_three_rotor_control_rule():
    qx = P0("episode", "state_qx")
    qy = P0("episode", "state_qy")
    qz = P0("episode", "state_qz")
    qw = P0("episode", "state_qw")
    r00 = Minus(L(1.0), Times(L(2.0), Plus(Times(qy, qy), Times(qz, qz))))
    r01 = Times(L(2.0), Minus(Times(qx, qy), Times(qz, qw)))
    r02 = Times(L(2.0), Plus(Times(qx, qz), Times(qy, qw)))
    r10 = Times(L(2.0), Plus(Times(qx, qy), Times(qz, qw)))
    r11 = Minus(L(1.0), Times(L(2.0), Plus(Times(qx, qx), Times(qz, qz))))
    r12 = Times(L(2.0), Minus(Times(qy, qz), Times(qx, qw)))
    r20 = Times(L(2.0), Minus(Times(qx, qz), Times(qy, qw)))
    r21 = Times(L(2.0), Plus(Times(qy, qz), Times(qx, qw)))
    r22 = Minus(L(1.0), Times(L(2.0), Plus(Times(qx, qx), Times(qy, qy))))

    ax = Minus(
        Times(
            P0("policy", "emergency_xy_position_gain"),
            Minus(
                P0("episode", "emergency_target_x"),
                P0("episode", "state_x"),
            ),
        ),
        Times(
            P0("policy", "emergency_xy_velocity_gain"),
            P0("episode", "state_vx"),
        ),
    )
    ay = Minus(
        Times(
            P0("policy", "emergency_xy_position_gain"),
            Minus(
                P0("episode", "emergency_target_y"),
                P0("episode", "state_y"),
            ),
        ),
        Times(
            P0("policy", "emergency_xy_velocity_gain"),
            P0("episode", "state_vy"),
        ),
    )
    az = Plus(
        P0("policy", "gravity_acceleration"),
        Times(
            P0("policy", "emergency_z_position_gain"),
            Minus(
                P0("episode", "emergency_target_z"),
                P0("episode", "state_z"),
            ),
        ),
        Times(
            L(-1.0),
            P0("policy", "emergency_z_velocity_gain"),
            P0("episode", "state_vz"),
        ),
    )
    acceleration_norm = spatial_norm(ax, ay, az)
    desired_bx = Div(ax, acceleration_norm)
    desired_by = Div(ay, acceleration_norm)
    desired_bz = Div(az, acceleration_norm)
    cross_x = Minus(Times(r12, desired_bz), Times(r22, desired_by))
    cross_y = Minus(Times(r22, desired_bx), Times(r02, desired_bz))
    cross_z = Minus(Times(r02, desired_by), Times(r12, desired_bx))
    error_body_x = Plus(
        Times(r00, cross_x),
        Times(r10, cross_y),
        Times(r20, cross_z),
    )
    error_body_y = Plus(
        Times(r01, cross_x),
        Times(r11, cross_y),
        Times(r21, cross_z),
    )
    omega_body_x = Plus(
        Times(r00, P0("episode", "state_wx")),
        Times(r10, P0("episode", "state_wy")),
        Times(r20, P0("episode", "state_wz")),
    )
    omega_body_y = Plus(
        Times(r01, P0("episode", "state_wx")),
        Times(r11, P0("episode", "state_wy")),
        Times(r21, P0("episode", "state_wz")),
    )
    torque_x = Minus(
        Times(P0("policy", "emergency_attitude_gain"), error_body_x),
        Times(P0("policy", "emergency_angular_gain"), omega_body_x),
    )
    torque_y = Minus(
        Times(P0("policy", "emergency_attitude_gain"), error_body_y),
        Times(P0("policy", "emergency_angular_gain"), omega_body_y),
    )
    arm_projection = Div(P0("policy", "body_arm_length"), Sqrt(L(2.0)))
    allocation_a = Div(torque_x, arm_projection)
    allocation_b = Div(torque_y, arm_projection)
    force_3 = Div(Minus(allocation_a, allocation_b), L(2.0))
    force_delta = Div(Plus(allocation_a, allocation_b), L(2.0))
    total_force = Times(P0("policy", "body_mass"), acceleration_norm)
    force_0 = Div(
        Minus(Minus(total_force, force_delta), force_3),
        L(2.0),
    )
    force_2 = Plus(force_0, force_delta)
    maximum_force = Times(
        P0("policy", "motor_thrust_coefficient"),
        P0("policy", "maximum_motor_rpm"),
        P0("policy", "maximum_motor_rpm"),
    )

    def rpm(force):
        return Sqrt(
            Div(
                Min(Max(force, L(0.0)), maximum_force),
                P0("policy", "motor_thrust_coefficient"),
            )
        )

    return {
        "name": "aa_direct_three_rotor_reduced_attitude_control",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Compose raw surviving-motor RPM in graph state at sensor "
        "rate. Yaw is deliberately relaxed; roll, pitch, position, and "
        "altitude are controlled through constrained CF2X force allocation.",
        "match": [
            ["agent", "has_aerial_policy", "policy"],
            ["agent", "has_aerial_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "direct_authority_enabled"), L(1.0)),
            Eq(P0("episode", "emergency_active"), L(1.0)),
            Eq(P0("episode", "failed_motor_ordinal"), L(1.0)),
            Gt(
                P0("episode", "state_seq"),
                P0("episode", "direct_command_state_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "direct_rpm_0", T(rpm(force_0))],
            ["set_attr", "episode", "direct_rpm_1", 0.0],
            ["set_attr", "episode", "direct_rpm_2", T(rpm(force_2))],
            ["set_attr", "episode", "direct_rpm_3", T(rpm(force_3))],
            ["set_attr", "episode", "direct_motor_command_ready", 1.0],
            ["set_attr", "episode", "direct_command_state_seq", T(
                P0("episode", "state_seq")
            )],
            ["set_attr", "episode", "direct_command_count", T(
                Plus(P0("episode", "direct_command_count"), L(1.0))
            )],
            ["set_attr", "episode", "control_mode", "three_rotor_direct"],
        ],
    }


def expose_motor_decision_option_rule():
    """Initialize shared-collapse fields before flight values are projected."""
    return {
        "name": "aa_expose_motor_decision_option",
        "area": "embodied_sensorimotor",
        "latency_class": "background",
        "comment": "Initialize each opaque AerialActionModel in the shared "
        "collapse vocabulary. The hard flight preparation rule projects the "
        "existing three-dimensional cost at each decision epoch.",
        "match": [
            ["agent", "has_aerial_episode", "episode"],
            ["episode", "has_aerial_action_model", "model"],
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
                "neutral_schema_ready_for_shared_flight_collapse",
            ],
        ],
    }


def manifest():
    return {
        "id": "aerial_adaptation",
        "version": "1.4.0",
        "depends_on": [
            "embodied_motor_priors",
            "motor_decision_collapse",
        ],
        "area": "sensorimotor_adaptation",
        "latency_class": "soft_realtime",
        "description": "From-scratch graph-native learning and control of an "
        "aerial body through opaque stabilized actuator commands and raw "
        "three-dimensional pose receipts.",
        "microtheory": {
            "name": "aerial_adaptation",
            "description": "Discover a three-dimensional action model by "
            "intervention, then fly toward a graph-held spatial goal.",
        },
        "nodes": [
            {
                "local_id": 1,
                "type": "AerialPolicy",
                "attrs": {
                    "name": "opaque_three_dimensional_forward_control",
                    "babble_samples": 2.0,
                    "goal_radius": 0.2,
                    "angular_stability_weight": 0.1,
                    "action_duration_seconds": 0.5,
                    "adaptation_rate": 0.05,
                    "surprise_adaptation_rate": 0.1,
                    "error_adaptation_rate": 0.2,
                    "surprise_factor": 1.5,
                    "surprise_floor": 0.01,
                    "plasticity_stop_epoch": 14.0,
                    "emergency_angular_speed_threshold": 2.0,
                    "emergency_xy_position_gain": 1.2,
                    "emergency_xy_velocity_gain": 1.1,
                    "emergency_z_position_gain": 2.5,
                    "emergency_z_velocity_gain": 1.8,
                    "emergency_attitude_gain": 0.02,
                    "emergency_angular_gain": 0.002,
                    "gravity_acceleration": 9.81,
                    "body_mass": 0.027,
                    "body_arm_length": 0.0397,
                    "motor_thrust_coefficient": 3.16e-10,
                    "maximum_motor_rpm": 21702.0,
                    "model_provenance": (
                        "learned_from_receipt_backed_flight_intervention"
                    ),
                    "shared_motor_collapse_enabled": 1.0,
                },
            }
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_aerial_policy",
                "tgt": {"local": 1},
                "attrs": {},
            }
        ],
        "productions": [
            {
                "provenance": "aerial_adaptation:agent_policy",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_aerial_policy",
                "tgt": {"type": "AerialPolicy", "var": "policy"},
            },
            {
                "provenance": "aerial_adaptation:agent_episode",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_aerial_episode",
                "tgt": {"type": "AerialEpisode", "var": "episode"},
            },
            {
                "provenance": "aerial_adaptation:episode_model",
                "src": {"type": "AerialEpisode", "var": "episode"},
                "edge_type": "has_aerial_action_model",
                "tgt": {"type": "AerialActionModel", "var": "model"},
            },
            {
                "provenance": "aerial_adaptation:model_actuator",
                "src": {"type": "AerialActionModel", "var": "model"},
                "edge_type": "models_aerial_actuator",
                "tgt": {"type": "OpaqueAerialActuator", "var": "actuator"},
            },
            {
                "provenance": "aerial_adaptation:episode_trial",
                "src": {"type": "AerialEpisode", "var": "episode"},
                "edge_type": "has_aerial_motor_trial",
                "tgt": {"type": "AerialMotorTrial", "var": "trial"},
            },
            {
                "provenance": "aerial_adaptation:trial_outcome",
                "src": {"type": "AerialMotorTrial", "var": "trial"},
                "edge_type": "has_aerial_transition_outcome",
                "tgt": {"type": "AerialTransitionObservation", "var": "outcome"},
            },
        ],
        "rules": [
            measure_goal_rule(),
            choose_babble_rule(),
            choose_goal_action_rule(),
            prepare_shared_flight_values_rule(),
            arm_shared_flight_collapse_rule(),
            release_shared_flight_collapse_rule(),
            open_trial_rule(),
            learn_rule(),
            close_frozen_trial_rule(),
            detect_direct_control_emergency_rule(),
            direct_three_rotor_control_rule(),
            expose_motor_decision_option_rule(),
        ],
    }


def main():
    output = os.path.join(ROOT, "seeds", "aerial_adaptation.json")
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(manifest(), handle, indent=1)
        handle.write("\n")
    print(f"wrote {output} ({len(manifest()['rules'])} rules)")


if __name__ == "__main__":
    main()
