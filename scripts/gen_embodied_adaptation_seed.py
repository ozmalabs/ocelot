"""Generate the graph-native, morphology-agnostic embodied adaptation seed.

The simulator adapter gives the graph opaque actuator tokens and raw state
transitions.  Every choice, forward-model update, and goal-directed prediction
below is a Rust-evaluated Term tree.  The generator is an authoring tool only.
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


def Mod(a, b):
    return {"type": "Mod", "a": a, "b": b}


def Sqrt(arg):
    return {"type": "Sqrt", "arg": arg}


def Abs(arg):
    return {"type": "Abs", "arg": arg}


def Sin(arg):
    return {"type": "Sin", "arg": arg}


def Cos(arg):
    return {"type": "Cos", "arg": arg}


def Atan2(y, x):
    return {"type": "Atan2", "y": y, "x": x}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Not(arg):
    return {"type": "Not", "arg": arg}


def Ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def Let(name, value, body):
    return {"type": "Let", "name": name, "value": value, "body": body}


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


def Argmax(source, var_name, value, default):
    return {
        "type": "Argmax",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


def T(term):
    return {"__term__": term}


def yaw(var, prefix):
    """Z yaw directly from the raw xyzw quaternion stored on ``var``."""
    qx = P0(var, f"{prefix}_qx")
    qy = P0(var, f"{prefix}_qy")
    qz = P0(var, f"{prefix}_qz")
    qw = P0(var, f"{prefix}_qw")
    return Atan2(
        Times(L(2.0), Plus(Times(qw, qz), Times(qx, qy))),
        Minus(L(1.0), Times(L(2.0), Plus(Times(qy, qy), Times(qz, qz)))),
    )


def body_transition(obs):
    """Observed world displacement expressed in the pre-action body frame."""
    angle = yaw(obs, "pre")
    dx = Minus(P0(obs, "post_x"), P0(obs, "pre_x"))
    dy = Minus(P0(obs, "post_y"), P0(obs, "pre_y"))
    forward = Plus(Times(Cos(angle), dx), Times(Sin(angle), dy))
    lateral = Plus(Times(L(-1.0), Sin(angle), dx), Times(Cos(angle), dy))
    post_angle = yaw(obs, "post")
    turn = Atan2(Sin(Minus(post_angle, angle)), Cos(Minus(post_angle, angle)))
    return forward, lateral, turn


def history_context(episode):
    """Read the graph-held prior transition already rotated for this body frame."""
    return (
        P0(episode, "history_context_forward"),
        P0(episode, "history_context_lateral"),
        P0(episode, "history_context_turn"),
    )


def contextual_prediction(var, episode, axis, context=None):
    if context is None:
        contexts = dict(
            zip(("forward", "lateral", "turn"), history_context(episode))
        )
        context = contexts[axis]
    return Plus(
        P0(var, f"mean_{axis}"),
        Times(P0(var, f"context_gain_{axis}"), context),
    )


def contextual_prediction_of(node, episode, axis):
    contexts = dict(
        zip(("forward", "lateral", "turn"), history_context(episode))
    )
    return Plus(
        AttrOf(node, f"mean_{axis}"),
        Times(AttrOf(node, f"context_gain_{axis}"), contexts[axis]),
    )


def candidate_prediction(var, episode, axis):
    contexts = dict(
        zip(("forward", "lateral", "turn"), history_context(episode))
    )
    return Ite(
        Gt(P0(var, "candidate_active"), L(0.5)),
        Plus(
            P0(var, f"candidate_mean_{axis}"),
            Times(P0(var, f"candidate_context_gain_{axis}"), contexts[axis]),
        ),
        contextual_prediction(var, episode, axis),
    )


def strongest_translation_model(fallback):
    """Return the empirically strongest displacement affordance."""
    return Argmax(
        MODELS,
        "propulsion",
        Plus(
            Times(
                P0("propulsion", "mean_forward"),
                P0("propulsion", "mean_forward"),
            ),
            Times(
                P0("propulsion", "mean_lateral"),
                P0("propulsion", "mean_lateral"),
            ),
        ),
        fallback,
    )


def weakest_translation_model(fallback):
    """Return the empirically closest learned consequence to bodily rest."""
    return Argmin(
        MODELS,
        "rest",
        Plus(
            Times(
                P0("rest", "mean_forward"),
                P0("rest", "mean_forward"),
            ),
            Times(
                P0("rest", "mean_lateral"),
                P0("rest", "mean_lateral"),
            ),
        ),
        fallback,
    )


def strongest_turn_model(fallback):
    """Return the largest learned one-action change of body heading."""
    return Argmax(
        MODELS,
        "turner",
        Abs(P0("turner", "mean_turn")),
        fallback,
    )


def translation_magnitude(node):
    return Sqrt(
        Plus(
            Times(
                AttrOf(node, "mean_forward"),
                AttrOf(node, "mean_forward"),
            ),
            Times(
                AttrOf(node, "mean_lateral"),
                AttrOf(node, "mean_lateral"),
            ),
        )
    )


def heading_escape_active(episode, policy):
    """Recruit orientation from learned affordances and receipt-backed failure."""
    rest = weakest_translation_model(V(episode))
    propulsion = strongest_translation_model(V(episode))
    turner = strongest_turn_model(V(episode))
    return And(
        Gt(P0(policy, "heading_escape_enabled"), L(0.5)),
        Gt(P0(episode, "goal_distance"), P0(policy, "goal_radius")),
        Eq(A(episode, "last_action_decision_kind"), L("forward_model")),
        Gt(P0(episode, "heading_escape_viable"), L(0.5)),
        Gt(translation_magnitude(propulsion), L(0.0)),
        Gt(Abs(AttrOf(turner, "mean_turn")), L(0.0)),
        # Stop once the remaining bearing error fits inside one empirically
        # learned turn quantum. No morphology-specific angle is imported.
        Gt(
            P0(episode, "goal_heading_error"),
            Abs(AttrOf(turner, "mean_turn")),
        ),
        # A goal-directed action that makes less progress than the learned
        # near-rest consequence has entered a local minimum.
        Lt(
            P0(episode, "last_action_goal_progress"),
            translation_magnitude(rest),
        ),
    )


def heading_improvement(trial, episode):
    """Actual reduction in egocentric goal bearing across one motor trial."""
    return Minus(
        P0(trial, "goal_heading_error_before"),
        P0(episode, "goal_heading_error"),
    )


def heading_escape_viability_after(trial, episode):
    """Continue an orientation bout only while its latest receipt supports it."""
    was_goal_directed = Eq(A(trial, "decision_kind"), L("forward_model"))
    was_orientation = And(
        was_goal_directed,
        Eq(A(trial, "control_regime"), L("heading_escape")),
    )
    return Ite(
        was_orientation,
        Ite(
            Gt(heading_improvement(trial, episode), L(0.0)),
            L(1.0),
            L(0.0),
        ),
        # An ordinary goal-directed action begins a fresh control bout. Other
        # probes leave the current sensorimotor evidence untouched.
        Ite(
            was_goal_directed,
            L(1.0),
            P0(episode, "heading_escape_viable"),
        ),
    )


MODELS = Neighbours("episode", "has_action_model")
UNSAMPLED = Filter(
    MODELS,
    "candidate",
    Lt(P0("candidate", "experience_count"), P0("policy", "babble_samples")),
)


def phased_navigation_calibration():
    """Matched pre-change identification shared by adaptive and frozen arms."""
    return And(
        Or(
            Eq(A("episode", "mode"), L("adaptive_damage_navigation")),
            Eq(A("episode", "mode"), L("frozen_damage_navigation")),
        ),
        Lt(P0("episode", "epoch"), P0("policy", "plasticity_stop_epoch")),
    )


def phased_navigation_active():
    """Post-calibration navigation begins at the hidden change boundary."""
    return And(
        Or(
            Eq(A("episode", "mode"), L("adaptive_damage_navigation")),
            Eq(A("episode", "mode"), L("frozen_damage_navigation")),
        ),
        Gt(
            P0("episode", "epoch"),
            Minus(P0("policy", "plasticity_stop_epoch"), L(0.5)),
        ),
    )


def closed_loop_plasticity_active():
    return Or(
        Eq(A("episode", "mode"), L("adaptive_relearning")),
        And(
            Eq(A("episode", "mode"), L("adaptive_damage_navigation")),
            Gt(
                P0("episode", "epoch"),
                Minus(P0("policy", "plasticity_stop_epoch"), L(0.5)),
            ),
        ),
        And(
            Eq(A("episode", "mode"), L("frozen_model_control")),
            Lt(
                P0("episode", "epoch"),
                P0("policy", "plasticity_stop_epoch"),
            ),
        ),
    )


def adaptive_plasticity_active():
    return Or(
        closed_loop_plasticity_active(),
        phased_navigation_calibration(),
        Eq(A("episode", "mode"), L("adaptive_probe")),
        And(
            Eq(A("episode", "mode"), L("frozen_probe_control")),
            Lt(
                P0("episode", "epoch"),
                P0("policy", "plasticity_stop_epoch"),
            ),
        ),
    )


def choose_babble_rule():
    best = Argmin(
        UNSAMPLED,
        "candidate",
        Plus(
            Times(P0("candidate", "experience_count"), L(10000.0)),
            P0("candidate", "ordinal"),
        ),
        V("episode"),
    )
    return {
        "name": "ea_choose_babble_action",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Motor babble is chosen in graph space: least-sampled opaque "
        "actuator first, with external enumeration ordinal only as a stable tie break.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": And(
            Or(
                Eq(A("episode", "mode"), L("learning")),
                Eq(A("episode", "mode"), L("adaptive_relearning")),
                Eq(A("episode", "mode"), L("frozen_model_control")),
                Eq(A("episode", "mode"), L("adaptive_probe")),
                Eq(A("episode", "mode"), L("frozen_probe_control")),
                Eq(A("episode", "mode"), L("adaptive_damage_navigation")),
                Eq(A("episode", "mode"), L("frozen_damage_navigation")),
                Eq(A("episode", "mode"), L("shuffled_model_control")),
            ),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Gt(Count(UNSAMPLED), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "predicted_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "predicted_forward", T(
                contextual_prediction_of(best, "episode", "forward")
            )],
            ["set_attr", "episode", "predicted_lateral", T(
                contextual_prediction_of(best, "episode", "lateral")
            )],
            ["set_attr", "episode", "predicted_turn", T(
                contextual_prediction_of(best, "episode", "turn")
            )],
            ["set_attr", "episode", "decision_kind", "motor_babble"],
            ["set_attr", "episode", "control_regime", "motor_babble"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(P0("episode", "decision_count"), L(1.0)))],
        ],
    }


def predicted_score(model, episode, policy):
    """Switch from distance descent to receipt-supported orientation."""
    angle = yaw(episode, "state")
    gx = Minus(P0(episode, "goal_x"), P0(episode, "state_x"))
    gy = Minus(P0(episode, "goal_y"), P0(episode, "state_y"))
    goal_forward_value = Plus(
        Times(Cos(angle), gx),
        Times(Sin(angle), gy),
    )
    goal_lateral_value = Plus(
        Times(L(-1.0), Sin(angle), gx),
        Times(Cos(angle), gy),
    )
    first_forward_value = contextual_prediction(model, episode, "forward")
    first_lateral_value = contextual_prediction(model, episode, "lateral")
    first_turn_value = contextual_prediction(model, episode, "turn")
    # The most translational learned action is an empirical capability, not a
    # named "forward" primitive.
    propulsion_value = strongest_translation_model(V(model))
    turner_value = strongest_turn_model(V(model))
    goal_forward = V("_plan_goal_forward")
    goal_lateral = V("_plan_goal_lateral")
    first_forward = V("_plan_first_forward")
    first_lateral = V("_plan_first_lateral")
    first_turn = V("_plan_first_turn")
    propulsion = V("_plan_propulsion")
    turner = V("_plan_turner")
    first_residual_forward = Minus(goal_forward, first_forward)
    first_residual_lateral = Minus(goal_lateral, first_lateral)
    one_step_distance = Sqrt(
        Plus(
            Times(first_residual_forward, first_residual_forward),
            Times(first_residual_lateral, first_residual_lateral),
        )
    )
    # A nonholonomic body may have to spend an action changing heading before
    # Euclidean distance can fall. The recruited regime compares the remaining
    # translation and bearing work in learned action quanta.
    next_goal_forward = Plus(
        Times(Cos(first_turn), first_residual_forward),
        Times(Sin(first_turn), first_residual_lateral),
    )
    next_goal_lateral = Plus(
        Times(L(-1.0), Sin(first_turn), first_residual_forward),
        Times(Cos(first_turn), first_residual_lateral),
    )
    heading_error = Abs(Atan2(next_goal_lateral, next_goal_forward))
    # Express both residuals in empirically learned one-action quanta. Their
    # sum estimates remaining motor work without a hand-tuned cross-unit weight.
    orientation_work = Plus(
        Div(one_step_distance, translation_magnitude(propulsion)),
        Div(heading_error, Abs(AttrOf(turner, "mean_turn"))),
    )
    propulsion_forward = Plus(
        Times(Cos(first_turn), AttrOf(propulsion, "mean_forward")),
        Times(
            L(-1.0),
            Sin(first_turn),
            AttrOf(propulsion, "mean_lateral"),
        ),
    )
    propulsion_lateral = Plus(
        Times(Sin(first_turn), AttrOf(propulsion, "mean_forward")),
        Times(Cos(first_turn), AttrOf(propulsion, "mean_lateral")),
    )
    two_step_residual_forward = Minus(
        goal_forward,
        Plus(first_forward, propulsion_forward),
    )
    two_step_residual_lateral = Minus(
        goal_lateral,
        Plus(first_lateral, propulsion_lateral),
    )
    two_step_distance = Sqrt(
        Plus(
            Times(
                two_step_residual_forward,
                two_step_residual_forward,
            ),
            Times(
                two_step_residual_lateral,
                two_step_residual_lateral,
            ),
        )
    )
    score = Plus(
        Ite(
            heading_escape_active(episode, policy),
            orientation_work,
            two_step_distance,
        ),
        Times(P0(policy, "contact_weight"), P0(model, "contact_ema")),
        Times(P0(policy, "effort_weight"), P0(model, "effort_ema")),
        # Stable, negligible tie break. It conveys no actuator semantics.
        Times(P0(model, "ordinal"), L(0.000000001)),
    )
    return Let(
        "_plan_goal_forward",
        goal_forward_value,
        Let(
            "_plan_goal_lateral",
            goal_lateral_value,
            Let(
                "_plan_first_forward",
                first_forward_value,
                Let(
                    "_plan_first_lateral",
                    first_lateral_value,
                    Let(
                        "_plan_first_turn",
                        first_turn_value,
                        Let(
                            "_plan_propulsion",
                            propulsion_value,
                            Let(
                                "_plan_turner",
                                turner_value,
                                score,
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def choose_model_rule():
    escape_active = heading_escape_active("episode", "policy")
    best = Argmin(
        MODELS,
        "candidate",
        predicted_score("candidate", "episode", "policy"),
        V("episode"),
    )
    return {
        "name": "ea_choose_model_action",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "After every opaque actuator has been sampled, choose the one "
        "whose learned body-frame consequence best serves the active control regime. "
        "Ordinary two-step distance descent remains the default; a graph-held lack "
        "of measured progress recruits orientation for nonholonomic local minima. "
        "Receipt-backed bearing improvement, learned rest, and learned turn quantum "
        "replace any fixed escape horizon. No morphology, forward-axis, or actuator "
        "label is visible.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(0.0)),
            Or(
                Eq(A("episode", "mode"), L("learning")),
                And(
                    closed_loop_plasticity_active(),
                    Lt(P0("episode", "recalibration_remaining"), L(0.5)),
                ),
                And(
                    Eq(A("episode", "mode"), L("frozen_model_control")),
                    Gt(
                        P0("episode", "epoch"),
                        Minus(P0("policy", "plasticity_stop_epoch"), L(0.5)),
                    ),
                ),
                And(
                    phased_navigation_active(),
                    Or(
                        Eq(
                            A("episode", "mode"),
                            L("frozen_damage_navigation"),
                        ),
                        Lt(
                            P0("episode", "recalibration_remaining"),
                            L(0.5),
                        ),
                    ),
                ),
            ),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MODELS), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "predicted_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "predicted_forward", T(
                contextual_prediction_of(best, "episode", "forward")
            )],
            ["set_attr", "episode", "predicted_lateral", T(
                contextual_prediction_of(best, "episode", "lateral")
            )],
            ["set_attr", "episode", "predicted_turn", T(
                contextual_prediction_of(best, "episode", "turn")
            )],
            ["set_attr", "episode", "decision_kind", "forward_model"],
            ["set_attr", "episode", "control_regime", T(
                Ite(
                    escape_active,
                    L("heading_escape"),
                    L("two_step_distance"),
                )
            )],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(P0("episode", "decision_count"), L(1.0)))],
        ],
    }


def prepare_shared_motor_values_rule():
    return {
        "name": "ea_prepare_shared_motor_collapse_values",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "batch": True,
        "comment": "Map the existing body-specific planning cost onto each "
        "episode-scoped option; the shared core owns the actual collapse.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
            ["episode", "has_action_model", "model"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Or(
                Eq(A("episode", "mode"), L("learning")),
                And(
                    closed_loop_plasticity_active(),
                    Lt(P0("episode", "recalibration_remaining"), L(0.5)),
                ),
                And(
                    Eq(A("episode", "mode"), L("frozen_model_control")),
                    Gt(
                        P0("episode", "epoch"),
                        Minus(P0("policy", "plasticity_stop_epoch"), L(0.5)),
                    ),
                ),
                And(
                    phased_navigation_active(),
                    Or(
                        Eq(
                            A("episode", "mode"),
                            L("frozen_damage_navigation"),
                        ),
                        Lt(
                            P0("episode", "recalibration_remaining"),
                            L(0.5),
                        ),
                    ),
                ),
            ),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MODELS), L(0.0)),
            Not(Eq(
                P0("model", "motor_decision_value_epoch"),
                P0("episode", "request_seq"),
            )),
        ),
        "effects": [
            [
                "add_edge",
                "episode",
                "has_motor_decision_option",
                "model",
            ],
            ["set_attr", "model", "available", 1.0],
            ["set_attr", "model", "grounded_value", T(Minus(
                L(0.0),
                predicted_score("model", "episode", "policy"),
            ))],
            ["set_attr", "model", "motor_decision_value_epoch", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "model", "motor_option_schema_ready", 1.0],
            [
                "set_attr",
                "model",
                "motor_option_value_provenance",
                "grounded_existing_forward_planning_cost",
            ],
        ],
    }


def arm_shared_motor_collapse_rule():
    prepared = Filter(
        MODELS,
        "candidate",
        Eq(
            P0("candidate", "motor_decision_value_epoch"),
            P0("episode", "request_seq"),
        ),
    )
    return {
        "name": "ea_arm_shared_motor_collapse",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": And(
            Eq(P0("policy", "shared_motor_collapse_enabled"), L(1.0)),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
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
            ["set_attr", "episode", "decision_status", "armed"],
        ],
    }


def release_shared_motor_collapse_rule():
    escape_active = heading_escape_active("episode", "policy")
    return {
        "name": "ea_release_shared_motor_collapse",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
            ["episode", "has_action_model", "model"],
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
            ["set_attr", "episode", "predicted_token", T(A("model", "token"))],
            ["set_attr", "episode", "predicted_forward", T(
                contextual_prediction_of(V("model"), "episode", "forward")
            )],
            ["set_attr", "episode", "predicted_lateral", T(
                contextual_prediction_of(V("model"), "episode", "lateral")
            )],
            ["set_attr", "episode", "predicted_turn", T(
                contextual_prediction_of(V("model"), "episode", "turn")
            )],
            ["set_attr", "episode", "decision_kind", "shared_forward_model"],
            ["set_attr", "episode", "control_regime", T(Ite(
                escape_active,
                L("heading_escape"),
                L("two_step_distance"),
            ))],
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


def choose_recalibration_rule():
    """Probe stale models after graph-detected sensorimotor surprise."""
    best = Argmin(
        MODELS,
        "candidate",
        Plus(
            Times(P0("candidate", "last_update_epoch"), L(100.0)),
            P0("candidate", "ordinal"),
        ),
        V("episode"),
    )
    return {
        "name": "ea_choose_change_recalibration",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Prediction surprise opens a finite graph-held re-probing "
        "window. Choose the least recently observed opaque actuator; neither "
        "the fault schedule nor actuator anatomy is available.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": And(
            closed_loop_plasticity_active(),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(P0("episode", "recalibration_remaining"), L(0.5)),
            Gt(Count(MODELS), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "predicted_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "predicted_forward", T(
                contextual_prediction_of(best, "episode", "forward")
            )],
            ["set_attr", "episode", "predicted_lateral", T(
                contextual_prediction_of(best, "episode", "lateral")
            )],
            ["set_attr", "episode", "predicted_turn", T(
                contextual_prediction_of(best, "episode", "turn")
            )],
            ["set_attr", "episode", "decision_kind", "change_recalibration"],
            ["set_attr", "episode", "control_regime", "change_recalibration"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
        ],
    }


def choose_probe_rule():
    target_ordinal = Mod(P0("episode", "epoch"), Count(MODELS))
    best = Argmin(
        MODELS,
        "candidate",
        Abs(Minus(P0("candidate", "ordinal"), target_ordinal)),
        V("episode"),
    )
    return {
        "name": "ea_choose_adaptation_probe",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Graph-native system-identification arm: apply the same "
        "round-robin opaque interventions in adaptive and frozen-plasticity "
        "graphs so prediction recovery is not confounded by action choice.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": And(
            Or(
                Eq(A("episode", "mode"), L("adaptive_probe")),
                Eq(A("episode", "mode"), L("frozen_probe_control")),
                phased_navigation_calibration(),
            ),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MODELS), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "predicted_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "predicted_forward", T(
                contextual_prediction_of(best, "episode", "forward")
            )],
            ["set_attr", "episode", "predicted_lateral", T(
                contextual_prediction_of(best, "episode", "lateral")
            )],
            ["set_attr", "episode", "predicted_turn", T(
                contextual_prediction_of(best, "episode", "turn")
            )],
            ["set_attr", "episode", "decision_kind", "adaptation_probe"],
            ["set_attr", "episode", "control_regime", "adaptation_probe"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(
                Plus(P0("episode", "decision_count"), L(1.0))
            )],
        ],
    }


def choose_control_rule():
    # Reproducible open-loop control with complete action coverage.  The
    # ordering operation and actuator lookup both remain graph-native.
    target_ordinal = Mod(P0("episode", "epoch"), Count(MODELS))
    score = Abs(Minus(P0("candidate", "ordinal"), target_ordinal))
    best = Argmin(MODELS, "candidate", score, V("episode"))
    return {
        "name": "ea_choose_no_learning_control",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "No-learning control: graph-native deterministic round-robin "
        "choice over opaque actuators. Python neither chooses nor learns.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "mode"), L("no_learning_control")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Gt(Count(MODELS), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "predicted_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "predicted_forward", T(
                contextual_prediction_of(best, "episode", "forward")
            )],
            ["set_attr", "episode", "predicted_lateral", T(
                contextual_prediction_of(best, "episode", "lateral")
            )],
            ["set_attr", "episode", "predicted_turn", T(
                contextual_prediction_of(best, "episode", "turn")
            )],
            ["set_attr", "episode", "decision_kind", "no_learning_control"],
            ["set_attr", "episode", "control_regime", "no_learning_control"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(P0("episode", "decision_count"), L(1.0)))],
        ],
    }


def choose_random_control_rule():
    # Deterministic chaos gives a reproducible random-like control.  The seed is
    # graph-held and the graph selects the minimum hash over opaque models.
    phase = Times(
        Plus(P0("episode", "epoch"), P0("policy", "control_seed"), L(1.0)),
        Plus(P0("candidate", "ordinal"), L(1.0)),
        L(12.9898),
    )
    score = Times(Abs(Sin(phase)), L(43758.5453))
    best = Argmin(MODELS, "candidate", score, V("episode"))
    return {
        "name": "ea_choose_random_control",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Random-like no-learning control: a graph-held deterministic "
        "hash selects over opaque actuator models. No host choice or model update.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "mode"), L("random_control")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Gt(Count(MODELS), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "predicted_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "selected_token", T(AttrOf(best, "token"))],
            ["set_attr", "episode", "predicted_forward", T(
                contextual_prediction_of(best, "episode", "forward")
            )],
            ["set_attr", "episode", "predicted_lateral", T(
                contextual_prediction_of(best, "episode", "lateral")
            )],
            ["set_attr", "episode", "predicted_turn", T(
                contextual_prediction_of(best, "episode", "turn")
            )],
            ["set_attr", "episode", "decision_kind", "random_control"],
            ["set_attr", "episode", "control_regime", "random_control"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(P0("episode", "decision_count"), L(1.0)))],
        ],
    }


def choose_shuffled_model_rule():
    predicted = Argmin(
        MODELS,
        "candidate",
        predicted_score("candidate", "episode", "policy"),
        V("episode"),
    )
    shifted_ordinal = Mod(
        Plus(AttrOf(predicted, "ordinal"), L(1.0)),
        Count(MODELS),
    )
    enacted = Argmin(
        MODELS,
        "candidate",
        Abs(Minus(P0("candidate", "ordinal"), shifted_ordinal)),
        V("episode"),
    )
    return {
        "name": "ea_choose_shuffled_model_control",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Ablation after babbling: retain the learned model table and "
        "graph planner but circularly permute the model-to-opaque-token association. "
        "This isolates whether the learned causal mapping, rather than generic motion, "
        "drives navigation.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "mode"), L("shuffled_model_control")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(P0("episode", "request_seq"), P0("episode", "decision_seq")),
            Eq(Count(UNSAMPLED), L(0.0)),
            Gt(Count(MODELS), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "predicted_token", T(AttrOf(predicted, "token"))],
            ["set_attr", "episode", "selected_token", T(AttrOf(enacted, "token"))],
            ["set_attr", "episode", "predicted_forward", T(
                contextual_prediction_of(predicted, "episode", "forward")
            )],
            ["set_attr", "episode", "predicted_lateral", T(
                contextual_prediction_of(predicted, "episode", "lateral")
            )],
            ["set_attr", "episode", "predicted_turn", T(
                contextual_prediction_of(predicted, "episode", "turn")
            )],
            ["set_attr", "episode", "decision_kind", "shuffled_model_control"],
            ["set_attr", "episode", "control_regime", "shuffled_model_control"],
            ["set_attr", "episode", "action_ready", 1.0],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "decision_count", T(Plus(P0("episode", "decision_count"), L(1.0)))],
        ],
    }


def open_trial_rule():
    return {
        "name": "ea_open_motor_trial",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Materialise the chosen opaque actuator and its current "
        "prediction as a graph trial before the world is touched.",
        "match": [
            ["agent", "has_embodied_episode", "episode"],
            ["episode", "has_action_model", "model"],
        ],
        "where": And(
            Eq(P0("episode", "action_ready"), L(1.0)),
            Eq(A("episode", "selected_token"), A("model", "token")),
            Lt(P0("episode", "last_trial_epoch"), P0("episode", "epoch")),
        ),
        "effects": [
            ["add_node", "trial", "MotorTrial", {
                "epoch": T(P0("episode", "epoch")),
                "token": T(A("model", "token")),
                "predicted_token": T(A("episode", "predicted_token")),
                "decision_kind": T(A("episode", "decision_kind")),
                "control_regime": T(A("episode", "control_regime")),
                "goal_heading_error_before": T(
                    P0("episode", "goal_heading_error")
                ),
                "status": "issued",
                "predicted_forward": T(P0("episode", "predicted_forward")),
                "predicted_lateral": T(P0("episode", "predicted_lateral")),
                "predicted_turn": T(P0("episode", "predicted_turn")),
                "candidate_predicted_forward": T(
                    candidate_prediction("model", "episode", "forward")
                ),
                "candidate_predicted_lateral": T(
                    candidate_prediction("model", "episode", "lateral")
                ),
                "candidate_predicted_turn": T(
                    candidate_prediction("model", "episode", "turn")
                ),
                "prediction_provenance": "graph_forward_model",
            }],
            ["add_edge", "episode", "has_motor_trial", "trial"],
            ["add_edge", "trial", "uses_action_model", "model"],
            ["set_attr", "episode", "last_trial_epoch", T(P0("episode", "epoch"))],
        ],
    }


def learn_rule():
    observed_forward, observed_lateral, observed_turn = body_transition("outcome")
    context_forward, context_lateral, context_turn = history_context("episode")
    next_context_forward = Plus(
        Times(Cos(observed_turn), observed_forward),
        Times(Sin(observed_turn), observed_lateral),
    )
    next_context_lateral = Plus(
        Times(L(-1.0), Sin(observed_turn), observed_forward),
        Times(Cos(observed_turn), observed_lateral),
    )
    residual_forward = Minus(
        observed_forward,
        P0("trial", "predicted_forward"),
    )
    residual_lateral = Minus(
        observed_lateral,
        P0("trial", "predicted_lateral"),
    )
    residual_turn = Minus(
        observed_turn,
        P0("trial", "predicted_turn"),
    )
    candidate_residual_forward = Minus(
        observed_forward,
        P0("trial", "candidate_predicted_forward"),
    )
    candidate_residual_lateral = Minus(
        observed_lateral,
        P0("trial", "candidate_predicted_lateral"),
    )
    candidate_residual_turn = Minus(
        observed_turn,
        P0("trial", "candidate_predicted_turn"),
    )
    consolidated_squared_error = Plus(
        Times(residual_forward, residual_forward),
        Times(residual_lateral, residual_lateral),
        Times(residual_turn, residual_turn),
    )
    candidate_squared_error = Plus(
        Times(candidate_residual_forward, candidate_residual_forward),
        Times(candidate_residual_lateral, candidate_residual_lateral),
        Times(candidate_residual_turn, candidate_residual_turn),
    )
    count = Plus(P0("model", "experience_count"), L(1.0))
    prediction_error = Sqrt(consolidated_squared_error)
    calibrated = Gt(
        P0("model", "experience_count"),
        Minus(P0("policy", "babble_samples"), L(0.5)),
    )
    adaptive = adaptive_plasticity_active()
    surprising = And(
        adaptive,
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
    damage_navigation = Or(
        Eq(A("episode", "mode"), L("adaptive_damage_navigation")),
        Eq(A("episode", "mode"), L("frozen_damage_navigation")),
    )
    candidate_guarded_adaptation = And(
        Eq(A("episode", "mode"), L("adaptive_damage_navigation")),
        Gt(
            P0("episode", "epoch"),
            Minus(P0("policy", "plasticity_stop_epoch"), L(0.5)),
        ),
    )
    adaptation_rate = Ite(
        surprising,
        Ite(
            damage_navigation,
            P0("policy", "navigation_fast_adaptation_rate"),
            P0("policy", "fast_adaptation_rate"),
        ),
        Ite(
            damage_navigation,
            P0("policy", "navigation_slow_adaptation_rate"),
            P0("policy", "slow_adaptation_rate"),
        ),
    )
    use_recency = And(adaptive, calibrated)

    def sample_mean(key, observation):
        return Plus(P0("model", key), Div(Minus(observation, P0("model", key)), count))

    def adaptive_mean(key, observation):
        return Ite(
            use_recency,
            Plus(
                P0("model", key),
                Times(
                    P0("outcome", "adaptation_rate"),
                    Minus(observation, P0("model", key)),
                ),
            ),
            sample_mean(key, observation),
        )

    def adaptive_axis_mean(key, observation, residual):
        return Ite(
            use_recency,
            Plus(
                P0("model", key),
                Times(P0("outcome", "adaptation_rate"), residual),
            ),
            sample_mean(key, observation),
        )

    def adaptive_context_gain(key, residual, context):
        normalized_context = Div(
            context,
            Plus(
                P0("policy", "context_regularizer"),
                Times(context, context),
            ),
        )
        return Ite(
            use_recency,
            Plus(
                P0("model", key),
                Times(
                    P0("policy", "context_learning_rate"),
                    P0("outcome", "adaptation_rate"),
                    residual,
                    normalized_context,
                ),
            ),
            P0("model", key),
        )

    candidate_was_active = Gt(P0("model", "candidate_active"), L(0.5))

    def proposed_candidate_mean(axis, _residual):
        return Ite(
            candidate_was_active,
            P0("model", f"candidate_mean_{axis}"),
            P0("model", f"mean_{axis}"),
        )

    def proposed_candidate_gain(axis, _residual, _context):
        return Ite(
            candidate_was_active,
            P0("model", f"candidate_context_gain_{axis}"),
            P0("model", f"context_gain_{axis}"),
        )

    stored_error = P0("outcome", "prediction_error")
    stored_surprising = Eq(P0("outcome", "surprise"), L(1.0))
    should_open_candidate = And(
        candidate_guarded_adaptation,
        stored_surprising,
        Lt(P0("model", "candidate_active"), L(0.5)),
        Lt(P0("model", "candidate_attempted"), L(0.5)),
    )
    candidate_opened = Eq(P0("outcome", "candidate_opened"), L(1.0))
    candidate_validation_count = Plus(
        P0("model", "candidate_validation_count"),
        L(1.0),
    )
    candidate_error_total = Plus(
        P0("model", "candidate_error_sum"),
        candidate_squared_error,
    )
    consolidated_error_total = Plus(
        P0("model", "candidate_consolidated_error_sum"),
        consolidated_squared_error,
    )
    should_promote_candidate = And(
        candidate_guarded_adaptation,
        candidate_was_active,
        Gt(
            candidate_validation_count,
            Minus(
                P0("policy", "candidate_min_validation_observations"),
                L(0.5),
            ),
        ),
        Lt(
            candidate_error_total,
            Times(
                consolidated_error_total,
                Minus(L(1.0), P0("policy", "candidate_promotion_margin")),
            ),
        ),
    )
    candidate_promoted = Eq(P0("outcome", "candidate_promoted"), L(1.0))
    should_validate_candidate_change = And(
        candidate_guarded_adaptation,
        candidate_was_active,
        Gt(
            candidate_validation_count,
            Minus(
                P0("policy", "candidate_min_validation_observations"),
                L(0.5),
            ),
        ),
        Lt(
            consolidated_error_total,
            Times(
                candidate_error_total,
                Minus(L(1.0), P0("policy", "candidate_promotion_margin")),
            ),
        ),
    )
    candidate_change_validated = Eq(
        P0("outcome", "candidate_change_validated"),
        L(1.0),
    )
    candidate_resolved = Or(candidate_promoted, candidate_change_validated)
    candidate_engaged = Or(candidate_opened, candidate_was_active)
    proposal_residual_forward = Ite(
        candidate_was_active, candidate_residual_forward, residual_forward
    )
    proposal_residual_lateral = Ite(
        candidate_was_active, candidate_residual_lateral, residual_lateral
    )
    proposal_residual_turn = Ite(
        candidate_was_active, candidate_residual_turn, residual_turn
    )
    candidate_mean_forward = proposed_candidate_mean(
        "forward", proposal_residual_forward
    )
    candidate_mean_lateral = proposed_candidate_mean(
        "lateral", proposal_residual_lateral
    )
    candidate_mean_turn = proposed_candidate_mean(
        "turn", proposal_residual_turn
    )
    candidate_gain_forward = proposed_candidate_gain(
        "forward", proposal_residual_forward, context_forward
    )
    candidate_gain_lateral = proposed_candidate_gain(
        "lateral", proposal_residual_lateral, context_lateral
    )
    candidate_gain_turn = proposed_candidate_gain(
        "turn", proposal_residual_turn, context_turn
    )
    error_ema = Ite(
        use_recency,
        Plus(
            P0("model", "error_ema"),
            Times(
                P0("policy", "error_adaptation_rate"),
                Minus(stored_error, P0("model", "error_ema")),
            ),
        ),
        Plus(
            P0("model", "error_ema"),
            Div(Minus(stored_error, P0("model", "error_ema")), count),
        ),
    )
    surprise_trace = Ite(
        stored_surprising,
        Plus(Times(P0("model", "surprise_trace"), L(0.5)), L(1.0)),
        Times(P0("model", "surprise_trace"), L(0.8)),
    )
    volatility_observation = Abs(
        Minus(stored_error, P0("model", "last_prediction_error"))
    )
    volatility_ema = Plus(
        P0("model", "volatility_ema"),
        Times(
            P0("policy", "volatility_adaptation_rate"),
            Minus(volatility_observation, P0("model", "volatility_ema")),
        ),
    )
    should_open_recalibration = And(
        closed_loop_plasticity_active(),
        stored_surprising,
        Gt(P0("model", "surprise_trace"), L(0.9)),
        Lt(P0("episode", "recalibration_remaining"), L(0.5)),
        Lt(
            P0("episode", "recalibration_cycles"),
            P0("policy", "max_recalibration_cycles"),
        ),
    )
    opened_recalibration = Eq(
        P0("outcome", "opened_recalibration"),
        L(1.0),
    )
    recalibration_remaining = Ite(
        opened_recalibration,
        Count(MODELS),
        Ite(
            Gt(P0("episode", "recalibration_remaining"), L(0.5)),
            Minus(P0("episode", "recalibration_remaining"), L(1.0)),
            L(0.0),
        ),
    )
    # Keep contact evidence graded.  Ordinary support contacts become the
    # model's baseline; additional collision contacts can then raise the same
    # learned channel without the adapter labelling either kind.
    contact_observation = P0("outcome", "contact_count")

    def guarded_consolidated(axis, ordinary_update):
        return Ite(
            candidate_promoted,
            P0("outcome", f"proposed_candidate_{axis}"),
            ordinary_update,
        )

    return {
        "name": "ea_learn_forward_model",
        "area": "adaptive_learning",
        "latency_class": "soft_realtime",
        "comment": "Receipt-backed transition updates the selected ActionModel "
        "in graph space. Initial exact sample means establish a slow prior; the "
        "adaptive mode then uses recency-weighted updates, prediction-error "
        "surprise, and a faster plasticity rate when consequences change.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
            ["episode", "has_motor_trial", "trial"],
            ["trial", "uses_action_model", "model"],
            ["trial", "has_transition_outcome", "outcome"],
        ],
        "where": And(
            Or(
                Eq(A("episode", "mode"), L("learning")),
                adaptive,
                Eq(A("trial", "decision_kind"), L("motor_babble")),
            ),
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "outcome", "observed_forward", T(observed_forward)],
            ["set_attr", "outcome", "observed_lateral", T(observed_lateral)],
            ["set_attr", "outcome", "observed_turn", T(observed_turn)],
            ["set_attr", "outcome", "history_context_forward", T(context_forward)],
            ["set_attr", "outcome", "history_context_lateral", T(context_lateral)],
            ["set_attr", "outcome", "history_context_turn", T(context_turn)],
            ["set_attr", "outcome", "prediction_error", T(prediction_error)],
            ["set_attr", "outcome", "surprise", T(Ite(surprising, L(1.0), L(0.0)))],
            ["set_attr", "outcome", "candidate_opened", T(
                Ite(should_open_candidate, L(1.0), L(0.0))
            )],
            ["set_attr", "outcome", "candidate_promoted", T(
                Ite(should_promote_candidate, L(1.0), L(0.0))
            )],
            ["set_attr", "outcome", "candidate_change_validated", T(
                Ite(should_validate_candidate_change, L(1.0), L(0.0))
            )],
            ["set_attr", "outcome", "candidate_squared_error", T(
                candidate_squared_error
            )],
            ["set_attr", "outcome", "consolidated_squared_error", T(
                consolidated_squared_error
            )],
            ["set_attr", "outcome", "proposed_candidate_mean_forward", T(
                candidate_mean_forward
            )],
            ["set_attr", "outcome", "proposed_candidate_mean_lateral", T(
                candidate_mean_lateral
            )],
            ["set_attr", "outcome", "proposed_candidate_mean_turn", T(
                candidate_mean_turn
            )],
            ["set_attr", "outcome", "proposed_candidate_context_gain_forward", T(
                candidate_gain_forward
            )],
            ["set_attr", "outcome", "proposed_candidate_context_gain_lateral", T(
                candidate_gain_lateral
            )],
            ["set_attr", "outcome", "proposed_candidate_context_gain_turn", T(
                candidate_gain_turn
            )],
            ["set_attr", "outcome", "opened_recalibration", T(
                Ite(should_open_recalibration, L(1.0), L(0.0))
            )],
            ["set_attr", "outcome", "adaptation_rate", T(adaptation_rate)],
            ["set_attr", "model", "mean_forward", T(
                guarded_consolidated(
                    "mean_forward",
                    adaptive_axis_mean(
                        "mean_forward", observed_forward, residual_forward
                    ),
                )
            )],
            ["set_attr", "model", "mean_lateral", T(
                guarded_consolidated(
                    "mean_lateral",
                    adaptive_axis_mean(
                        "mean_lateral", observed_lateral, residual_lateral
                    ),
                )
            )],
            ["set_attr", "model", "mean_turn", T(
                guarded_consolidated(
                    "mean_turn",
                    adaptive_axis_mean(
                        "mean_turn", observed_turn, residual_turn
                    ),
                )
            )],
            ["set_attr", "model", "context_gain_forward", T(
                guarded_consolidated(
                    "context_gain_forward",
                    adaptive_context_gain(
                        "context_gain_forward",
                        residual_forward,
                        context_forward,
                    ),
                )
            )],
            ["set_attr", "model", "context_gain_lateral", T(
                guarded_consolidated(
                    "context_gain_lateral",
                    adaptive_context_gain(
                        "context_gain_lateral",
                        residual_lateral,
                        context_lateral,
                    ),
                )
            )],
            ["set_attr", "model", "context_gain_turn", T(
                guarded_consolidated(
                    "context_gain_turn",
                    adaptive_context_gain(
                        "context_gain_turn", residual_turn, context_turn
                    ),
                )
            )],
            ["set_attr", "model", "contact_ema", T(
                adaptive_mean("contact_ema", contact_observation)
            )],
            ["set_attr", "model", "effort_ema", T(
                adaptive_mean("effort_ema", P0("outcome", "effort"))
            )],
            ["set_attr", "model", "energy_ema_joules", T(
                adaptive_mean(
                    "energy_ema_joules",
                    P0("outcome", "input_energy_joules"),
                )
            )],
            ["set_attr", "model", "candidate_mean_forward", T(
                Ite(
                    candidate_engaged,
                    P0("outcome", "proposed_candidate_mean_forward"),
                    P0("model", "candidate_mean_forward"),
                )
            )],
            ["set_attr", "model", "candidate_mean_lateral", T(
                Ite(
                    candidate_engaged,
                    P0("outcome", "proposed_candidate_mean_lateral"),
                    P0("model", "candidate_mean_lateral"),
                )
            )],
            ["set_attr", "model", "candidate_mean_turn", T(
                Ite(
                    candidate_engaged,
                    P0("outcome", "proposed_candidate_mean_turn"),
                    P0("model", "candidate_mean_turn"),
                )
            )],
            ["set_attr", "model", "candidate_context_gain_forward", T(
                Ite(
                    candidate_engaged,
                    P0(
                        "outcome",
                        "proposed_candidate_context_gain_forward",
                    ),
                    P0("model", "candidate_context_gain_forward"),
                )
            )],
            ["set_attr", "model", "candidate_context_gain_lateral", T(
                Ite(
                    candidate_engaged,
                    P0(
                        "outcome",
                        "proposed_candidate_context_gain_lateral",
                    ),
                    P0("model", "candidate_context_gain_lateral"),
                )
            )],
            ["set_attr", "model", "candidate_context_gain_turn", T(
                Ite(
                    candidate_engaged,
                    P0("outcome", "proposed_candidate_context_gain_turn"),
                    P0("model", "candidate_context_gain_turn"),
                )
            )],
            ["set_attr", "model", "candidate_validation_count", T(
                Ite(
                    candidate_resolved,
                    L(0.0),
                    Ite(
                        candidate_was_active,
                        candidate_validation_count,
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "model", "candidate_error_sum", T(
                Ite(
                    candidate_resolved,
                    L(0.0),
                    Ite(
                        candidate_was_active,
                        candidate_error_total,
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "model", "candidate_consolidated_error_sum", T(
                Ite(
                    candidate_resolved,
                    L(0.0),
                    Ite(
                        candidate_was_active,
                        consolidated_error_total,
                        L(0.0),
                    ),
                )
            )],
            ["set_attr", "model", "candidate_promotion_count", T(
                Plus(
                    P0("model", "candidate_promotion_count"),
                    P0("outcome", "candidate_promoted"),
                )
            )],
            ["set_attr", "model", "candidate_validation_success_count", T(
                Plus(
                    P0("model", "candidate_validation_success_count"),
                    P0("outcome", "candidate_change_validated"),
                )
            )],
            ["set_attr", "model", "last_candidate_promotion_epoch", T(
                Ite(
                    candidate_promoted,
                    P0("episode", "epoch"),
                    P0("model", "last_candidate_promotion_epoch"),
                )
            )],
            ["set_attr", "model", "candidate_attempted", T(
                Ite(
                    candidate_opened,
                    L(1.0),
                    P0("model", "candidate_attempted"),
                )
            )],
            ["set_attr", "model", "candidate_active", T(
                Ite(
                    candidate_resolved,
                    L(0.0),
                    Ite(
                        candidate_opened,
                        L(1.0),
                        P0("model", "candidate_active"),
                    ),
                )
            )],
            ["set_attr", "model", "error_ema", T(error_ema)],
            ["set_attr", "model", "volatility_ema", T(volatility_ema)],
            ["set_attr", "model", "surprise_trace", T(surprise_trace)],
            ["set_attr", "model", "adaptation_state", T(
                Ite(Gt(surprise_trace, L(0.75)), L(1.0), L(0.0))
            )],
            ["set_attr", "model", "surprise_count", T(
                Plus(
                    P0("model", "surprise_count"),
                    P0("outcome", "surprise"),
                )
            )],
            ["set_attr", "model", "last_surprise_epoch", T(
                Ite(
                    stored_surprising,
                    P0("episode", "epoch"),
                    P0("model", "last_surprise_epoch"),
                )
            )],
            ["set_attr", "model", "last_adaptation_rate", T(adaptation_rate)],
            ["set_attr", "model", "last_prediction_error", T(stored_error)],
            ["set_attr", "model", "experience_count", T(count)],
            ["set_attr", "model", "last_update_epoch", T(P0("episode", "epoch"))],
            ["set_attr", "episode", "recalibration_remaining", T(
                recalibration_remaining
            )],
            ["set_attr", "episode", "recalibration_cycles", T(
                Plus(
                    P0("episode", "recalibration_cycles"),
                    Ite(opened_recalibration, L(1.0), L(0.0)),
                )
            )],
            ["set_attr", "episode", "last_action_goal_progress", T(
                P0("episode", "goal_progress")
            )],
            ["set_attr", "episode", "last_action_decision_kind", T(
                A("trial", "decision_kind")
            )],
            ["set_attr", "episode", "last_heading_improvement", T(
                heading_improvement("trial", "episode")
            )],
            ["set_attr", "episode", "heading_escape_viable", T(
                heading_escape_viability_after("trial", "episode")
            )],
            ["set_attr", "episode", "last_observed_forward", T(observed_forward)],
            ["set_attr", "episode", "last_observed_lateral", T(observed_lateral)],
            ["set_attr", "episode", "last_observed_turn", T(observed_turn)],
            ["set_attr", "episode", "history_context_forward", T(
                next_context_forward
            )],
            ["set_attr", "episode", "history_context_lateral", T(
                next_context_lateral
            )],
            ["set_attr", "episode", "history_context_turn", T(observed_turn)],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "learned"],
        ],
    }


def close_control_trial_rule():
    observed_forward, observed_lateral, observed_turn = body_transition("outcome")
    next_context_forward = Plus(
        Times(Cos(observed_turn), observed_forward),
        Times(Sin(observed_turn), observed_lateral),
    )
    next_context_lateral = Plus(
        Times(L(-1.0), Sin(observed_turn), observed_forward),
        Times(Cos(observed_turn), observed_lateral),
    )
    squared_error = Plus(
        Times(
            Minus(observed_forward, P0("trial", "predicted_forward")),
            Minus(observed_forward, P0("trial", "predicted_forward")),
        ),
        Times(
            Minus(observed_lateral, P0("trial", "predicted_lateral")),
            Minus(observed_lateral, P0("trial", "predicted_lateral")),
        ),
        Times(
            Minus(observed_turn, P0("trial", "predicted_turn")),
            Minus(observed_turn, P0("trial", "predicted_turn")),
        ),
    )
    return {
        "name": "ea_close_no_learning_trial",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Receipt closes a control trial but changes no ActionModel.",
        "match": [
            ["agent", "has_embodied_episode", "episode"],
            ["episode", "has_motor_trial", "trial"],
            ["trial", "has_transition_outcome", "outcome"],
        ],
        "where": And(
            Not(Eq(A("trial", "decision_kind"), L("motor_babble"))),
            Or(
                Eq(A("episode", "mode"), L("no_learning_control")),
                Eq(A("episode", "mode"), L("random_control")),
                Eq(A("episode", "mode"), L("shuffled_model_control")),
                And(
                    Or(
                        Eq(A("episode", "mode"), L("frozen_model_control")),
                        Eq(A("episode", "mode"), L("frozen_probe_control")),
                        Eq(
                            A("episode", "mode"),
                            L("frozen_damage_navigation"),
                        ),
                    ),
                    Gt(
                        P0("episode", "epoch"),
                        Minus(P0("policy", "plasticity_stop_epoch"), L(0.5)),
                    ),
                ),
            ),
            Eq(A("trial", "status"), L("issued")),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "outcome", "observed_forward", T(observed_forward)],
            ["set_attr", "outcome", "observed_lateral", T(observed_lateral)],
            ["set_attr", "outcome", "observed_turn", T(observed_turn)],
            ["set_attr", "outcome", "prediction_error", T(Sqrt(squared_error))],
            ["set_attr", "episode", "last_observed_forward", T(observed_forward)],
            ["set_attr", "episode", "last_observed_lateral", T(observed_lateral)],
            ["set_attr", "episode", "last_observed_turn", T(observed_turn)],
            ["set_attr", "episode", "last_action_goal_progress", T(
                P0("episode", "goal_progress")
            )],
            ["set_attr", "episode", "last_action_decision_kind", T(
                A("trial", "decision_kind")
            )],
            ["set_attr", "episode", "last_heading_improvement", T(
                heading_improvement("trial", "episode")
            )],
            ["set_attr", "episode", "heading_escape_viable", T(
                heading_escape_viability_after("trial", "episode")
            )],
            ["set_attr", "episode", "history_context_forward", T(
                next_context_forward
            )],
            ["set_attr", "episode", "history_context_lateral", T(
                next_context_lateral
            )],
            ["set_attr", "episode", "history_context_turn", T(observed_turn)],
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "observed_no_learning"],
        ],
    }


def measure_goal_rule():
    angle = yaw("episode", "state")
    dx = Minus(P0("episode", "goal_x"), P0("episode", "state_x"))
    dy = Minus(P0("episode", "goal_y"), P0("episode", "state_y"))
    distance = Sqrt(Plus(Times(dx, dx), Times(dy, dy)))
    goal_forward = Plus(
        Times(Cos(angle), dx),
        Times(Sin(angle), dy),
    )
    goal_lateral = Plus(
        Times(L(-1.0), Sin(angle), dx),
        Times(Cos(angle), dy),
    )
    heading_error = Abs(Atan2(goal_lateral, goal_forward))
    return {
        "name": "ea_measure_goal_state",
        "area": "sensorimotor_adaptation",
        "latency_class": "hard_realtime",
        "comment": "Distance, progress, egocentric goal bearing, and threshold "
        "crossing are graph-held assessments. The runner records them but never "
        "judges success.",
        "match": [
            ["agent", "has_embodied_policy", "policy"],
            ["agent", "has_embodied_episode", "episode"],
        ],
        "where": Lt(P0("episode", "measured_state_seq"), P0("episode", "state_seq")),
        "effects": [
            ["set_attr", "episode", "previous_goal_distance", T(P0("episode", "goal_distance"))],
            ["set_attr", "episode", "goal_progress",
             T(Minus(P0("episode", "goal_distance"), distance))],
            ["set_attr", "episode", "goal_distance", T(distance)],
            ["set_attr", "episode", "previous_goal_heading_error", T(
                P0("episode", "goal_heading_error")
            )],
            ["set_attr", "episode", "goal_heading_error", T(heading_error)],
            ["set_attr", "episode", "goal_reached",
             T(Ite(Lt(distance, P0("policy", "goal_radius")), L(1.0), L(0.0)))],
            ["set_attr", "episode", "measured_state_seq", T(P0("episode", "state_seq"))],
        ],
    }


def expose_motor_decision_option_rule():
    """Initialize shared-collapse fields before local costs are projected."""
    return {
        "name": "ea_expose_motor_decision_option",
        "area": "embodied_sensorimotor",
        "latency_class": "background",
        "comment": "Initialize each opaque ActionModel in the shared collapse "
        "vocabulary. The hard preparation rule projects the existing local "
        "forward-planning cost at each decision epoch.",
        "match": [
            ["agent", "has_embodied_episode", "episode"],
            ["episode", "has_action_model", "model"],
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
                "neutral_schema_ready_for_shared_ground_collapse",
            ],
        ],
    }


def manifest():
    return {
        "id": "embodied_adaptation",
        "version": "1.7.0",
        "depends_on": [
            "embodied_motor_priors",
            "motor_decision_collapse",
        ],
        "area": "sensorimotor_adaptation",
        "latency_class": "soft_realtime",
        "description": "Morphology-agnostic from-scratch sensorimotor adaptation. "
        "A fresh graph receives opaque actuator tokens and raw pose/contact/effort "
        "receipts, performs motor babble, learns graph-resident body-frame forward "
        "models, detects changed consequences through prediction error, adapts "
        "at fast and slow timescales, and predicts the next action toward a "
        "graph-held goal. Matched frozen-plasticity and no-learning controls "
        "are also graph-native.",
        "microtheory": {
            "name": "embodied_adaptation",
            "description": "Learn what an unnamed body can do from intervention, "
            "track damage or wear as changed consequences without a fault label, "
            "then choose by forward prediction rather than imported kinematics.",
        },
        "nodes": [
            {
                "local_id": 1,
                "type": "EmbodiedPolicy",
                "attrs": {
                    "name": "morphology_agnostic_forward_control",
                    "babble_samples": 3.0,
                    "goal_radius": 0.65,
                    "contact_weight": 0.01,
                    "effort_weight": 0.00002,
                    "heading_escape_enabled": 1.0,
                    "control_seed": 17.0,
                    "slow_adaptation_rate": 0.18,
                    "fast_adaptation_rate": 0.68,
                    "navigation_slow_adaptation_rate": 0.02,
                    "navigation_fast_adaptation_rate": 0.4,
                    "context_learning_rate": 0.5,
                    "context_regularizer": 0.002,
                    "candidate_min_validation_observations": 2.0,
                    "candidate_promotion_margin": 0.05,
                    "error_adaptation_rate": 0.2,
                    "volatility_adaptation_rate": 0.2,
                    "surprise_factor": 1.25,
                    "surprise_floor": 0.005,
                    "plasticity_stop_epoch": 18.0,
                    "max_recalibration_cycles": 1.0,
                    "model_provenance": "learned_from_receipt_backed_intervention",
                    "shared_motor_collapse_enabled": 1.0,
                },
            }
        ],
        "edges": [
            {
                "src": {"role": "agent_root"},
                "type": "has_embodied_policy",
                "tgt": {"local": 1},
                "attrs": {},
            }
        ],
        "productions": [
            {
                "provenance": "embodied_adaptation:agent_policy",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_policy",
                "tgt": {"type": "EmbodiedPolicy", "var": "policy"},
            },
            {
                "provenance": "embodied_adaptation:agent_episode",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_episode",
                "tgt": {"type": "EmbodiedEpisode", "var": "episode"},
            },
            {
                "provenance": "embodied_adaptation:episode_model",
                "src": {"type": "EmbodiedEpisode", "var": "episode"},
                "edge_type": "has_action_model",
                "tgt": {"type": "ActionModel", "var": "model"},
            },
            {
                "provenance": "embodied_adaptation:model_actuator",
                "src": {"type": "ActionModel", "var": "model"},
                "edge_type": "models_actuator",
                "tgt": {"type": "OpaqueActuator", "var": "actuator"},
            },
            {
                "provenance": "embodied_adaptation:episode_trial",
                "src": {"type": "EmbodiedEpisode", "var": "episode"},
                "edge_type": "has_motor_trial",
                "tgt": {"type": "MotorTrial", "var": "trial"},
            },
            {
                "provenance": "embodied_adaptation:trial_outcome",
                "src": {"type": "MotorTrial", "var": "trial"},
                "edge_type": "has_transition_outcome",
                "tgt": {"type": "TransitionObservation", "var": "outcome"},
            },
        ],
        "rules": [
            measure_goal_rule(),
            choose_babble_rule(),
            choose_recalibration_rule(),
            choose_model_rule(),
            prepare_shared_motor_values_rule(),
            arm_shared_motor_collapse_rule(),
            release_shared_motor_collapse_rule(),
            choose_probe_rule(),
            choose_control_rule(),
            choose_random_control_rule(),
            choose_shuffled_model_rule(),
            open_trial_rule(),
            learn_rule(),
            close_control_trial_rule(),
            expose_motor_decision_option_rule(),
        ],
    }


def main():
    out = os.path.join(ROOT, "seeds", "embodied_adaptation.json")
    payload = manifest()
    with open(out, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1)
        handle.write("\n")
    with open(out, encoding="utf-8") as handle:
        json.load(handle)
    print(f"wrote {os.path.relpath(out, ROOT)} ({len(payload['rules'])} rules)")


if __name__ == "__main__":
    main()
