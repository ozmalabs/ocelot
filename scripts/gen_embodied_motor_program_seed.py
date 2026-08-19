"""Generate shared graph-native, factorized embodied motor programs.

The seed owns analysis-by-synthesis over independent opaque effector groups.
It contains no morphology, joint, wheel, wing, or rotor vocabulary. A domain
supplies receipt-learned primitive consequences and a desired consequence;
the graph constructs an arbitrary-width simultaneous program, passes that
program through the shared motor collapse, and publishes its exact members.
"""
from __future__ import annotations

import json
from pathlib import Path

try:
    from scripts.gen_embodied_structural_limits_seed import STRUCTURAL_LOADS
except ModuleNotFoundError:  # Direct ``python scripts/...`` execution.
    from gen_embodied_structural_limits_seed import STRUCTURAL_LOADS


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = (
    "forward",
    "lateral",
    "vertical",
    "roll",
    "pitch",
    "turn",
    "normal_load",
)
FLOW_FEATURES = (
    "flow_forward",
    "flow_lateral",
    "flow_vertical",
    "power_state",
)
CONTEXT_DELTAS = FLOW_FEATURES
# A deliberately finite unroll keeps the graph contract bounded.  It is not a
# physical horizon: each slice is an A-B-S projection of receipt-learned
# context deltas, and the audit reports when this support is exhausted.
FUTURE_MANIFOLD_PROJECTION_BUDGET = 16
FUTURE_MANIFOLD_PATH_FIXED_POINT_RUN = 1
FUTURE_MANIFOLD_PHYSICAL_HORIZON = 256
# Temporal foveation is opt-in.  The runtime treats these as graph-owned
# policy data (not a host schedule): dense anchors cover 1,2,3,4,8,16, then
# log-log-far anchors then grow by four; ambiguous intervals may be locally
# refined under the same budget.
FUTURE_MANIFOLD_TEMPORAL_ANCHORS_ENABLED = 0
FUTURE_MANIFOLD_ANCHOR_GROWTH = 2
FUTURE_MANIFOLD_MAX_SHAPE_ORDER = 1
FUTURE_MANIFOLD_MAX_REFINEMENTS = 16
FUTURE_MANIFOLD_ENCLOSURE_WIDTH_FLOOR = 0
ALL_CONSEQUENCES = tuple(dict.fromkeys(
    (*COMPONENTS, "drag", "energy", *STRUCTURAL_LOADS)
))


def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(var, key):
    return {"type": "Attr", "node": V(var), "key": key}


def AO(node, key):
    return {"type": "Attr", "node": node, "key": key}


def P0(var, key):
    return {"type": "Plus", "items": [A(var, key), L(0.0)]}


def Plus(*items):
    return {"type": "Plus", "items": list(items)}


def Minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Times(*items):
    return {"type": "Times", "items": list(items)}


def Div(a, b):
    return {"type": "Div", "a": a, "b": b}


def Abs(arg):
    return {"type": "Abs", "arg": arg}


def Max(*items):
    return {"type": "Max", "items": list(items)}


def MinOver(source, var_name, value, default):
    """The minimum of `value` over `source`, or `default` when empty.

    The seed defines the MinOver Term type without exporting a helper; the
    F-16 consumer builds the same dict for the same reason.
    """
    return {
        "type": "MinOver",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


def Min(*items):
    return {"type": "Min", "items": list(items)}


def MaxOver(source, var_name, value, default):
    """Maximum value over a graph collection (the graph-native twin of MinOver)."""
    return {
        "type": "MaxOver",
        "source": source,
        "var_name": var_name,
        "value": value,
        "default": default,
    }


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


def Log(arg):
    return {"type": "Log", "arg": arg}


def Exp(arg):
    return {"type": "Exp", "arg": arg}


def Neg(arg):
    return {"type": "Neg", "arg": arg}


def And(*items):
    return {"type": "And", "items": list(items)}


def Or(*items):
    return {"type": "Or", "items": list(items)}


def Not(arg):
    return {"type": "Not", "arg": arg}


def If(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def Clamp(value, lower, upper):
    """Bound a scalar using graph-native comparisons."""
    return If(
        Lt(value, lower),
        lower,
        If(Gt(value, upper), upper, value),
    )


def Neighbours(var, edge_type):
    return {"type": "Neighbours", "node": V(var), "edge_type": edge_type}


def Filter(source, var_name, predicate):
    return {
        "type": "Filter",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Count(source):
    return {"type": "Count", "source": source}


def Exists(source, var_name, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var_name,
        "predicate": predicate,
    }


def Sum(source, var_name, value):
    return {
        "type": "Sum",
        "source": source,
        "var_name": var_name,
        "value": value,
    }


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


def MapList(source, var_name, value):
    return {
        "type": "MapList",
        "source": source,
        "var_name": var_name,
        "value": value,
    }


def Vec(*items):
    return {"type": "Vec", "items": list(items)}


def SetT(*items):
    return {"type": "SetT", "items": list(items)}


def StringConcat(*parts):
    return {"type": "StringConcat", "parts": list(parts)}


def ToJsonString(value):
    return {"type": "ToJsonString", "value": value}


def IDiv(a, b):
    return {"type": "IDiv", "a": a, "b": b}


def T(term):
    return {"__term__": term}


MODELS = Neighbours("episode", "has_embodied_effector_model")


def yaw(var, prefix):
    qx = P0(var, f"{prefix}_qx")
    qy = P0(var, f"{prefix}_qy")
    qz = P0(var, f"{prefix}_qz")
    qw = P0(var, f"{prefix}_qw")
    return Atan2(
        Times(L(2.0), Plus(Times(qw, qz), Times(qx, qy))),
        Minus(
            L(1.0),
            Times(L(2.0), Plus(Times(qy, qy), Times(qz, qz))),
        ),
    )


def pre_flow_speed_squared(var="outcome"):
    return Plus(
        Times(P0(var, "pre_vx"), P0(var, "pre_vx")),
        Times(P0(var, "pre_vy"), P0(var, "pre_vy")),
        Times(P0(var, "pre_vz"), P0(var, "pre_vz")),
    )


def six_axis_receipts():
    return Eq(P0("episode", "six_axis_receipts"), L(1.0))


def pre_flow_feature(key, var="outcome"):
    return P0(var, f"pre_{key}")


def outcome_observation(key, var="outcome"):
    dx = Minus(P0(var, "post_x"), P0(var, "pre_x"))
    dy = Minus(P0(var, "post_y"), P0(var, "pre_y"))
    heading = yaw(var, "pre")
    if key == "forward":
        return If(
            six_axis_receipts(),
            Minus(P0(var, "post_body_vx"), P0(var, "pre_body_vx")),
            Plus(Times(Cos(heading), dx), Times(Sin(heading), dy)),
        )
    if key == "lateral":
        return If(
            six_axis_receipts(),
            Minus(P0(var, "post_body_vy"), P0(var, "pre_body_vy")),
            Plus(
                Times(Minus(L(0.0), Sin(heading)), dx),
                Times(Cos(heading), dy),
            ),
        )
    if key == "vertical":
        return If(
            six_axis_receipts(),
            Minus(P0(var, "post_body_vz"), P0(var, "pre_body_vz")),
            L(0.0),
        )
    if key == "roll":
        return If(
            six_axis_receipts(),
            Minus(P0(var, "post_body_wx"), P0(var, "pre_body_wx")),
            L(0.0),
        )
    if key == "pitch":
        return If(
            six_axis_receipts(),
            Minus(P0(var, "post_body_wy"), P0(var, "pre_body_wy")),
            L(0.0),
        )
    if key == "turn":
        delta = Minus(yaw(var, "post"), heading)
        return If(
            six_axis_receipts(),
            Minus(P0(var, "post_body_wz"), P0(var, "pre_body_wz")),
            Atan2(Sin(delta), Cos(delta)),
        )
    if key == "normal_load":
        return If(
            six_axis_receipts(),
            P0(var, "normal_load_factor"),
            Div(
                P0(var, "external_normal_force_newtons"),
                P0(var, "body_weight_newtons"),
            ),
        )
    if key == "drag":
        return P0(var, "aerodynamic_dissipation_joules")
    if key == "energy":
        return P0(var, "input_energy_joules")
    if key in STRUCTURAL_LOADS:
        return P0(var, f"observed_{key}")
    raise ValueError(f"unknown motor consequence {key!r}")


def outcome_context_delta(feature, var="outcome"):
    return P0(var, f"observed_context_delta_{feature}")


def _projected_position(var, steps):
    position = P0(var, "state_effector_position")
    for _ in range(max(0, int(steps))):
        error = Minus(P0(var, "specified_command_level"), position)
        maximum = P0(var, "specified_maximum_position_change_per_action")
        change = If(
            Gt(Abs(error), maximum),
            If(Gt(error, L(0.0)), maximum, Times(L(-1.0), maximum)),
            error,
        )
        position = Plus(position, change)
    return position


def _model_prediction(var, key, context=None, projection_step=0):
    """Receipt-learned local prediction over vector flow and power state."""
    context = context or {}
    def context_value(feature):
        return context.get(feature, P0("episode", f"state_{feature}"))

    learned_prediction = Plus(
        P0(var, f"mean_{key}"),
        If(
            Gt(
                P0("policy", "contextual_effector_prediction_enabled"),
                L(0.5),
            ),
            Plus(
                Times(
                    P0(var, f"flow_gain_{key}"),
                    Minus(
                        context.get("flow_speed_squared", P0("episode", "state_flow_speed_squared")),
                        P0(var, "mean_flow_speed_squared"),
                    ),
                ),
                *(
                    Times(
                        P0(var, f"{feature}_gain_{key}"),
                        Minus(
                            context_value(feature),
                            P0(var, f"mean_{feature}"),
                        ),
                    )
                    for feature in FLOW_FEATURES
                ),
            ),
            L(0.0),
        ),
    )
    projected_position = context.get("state_effector_position", _projected_position(var, projection_step))
    position_error = Minus(
        P0(var, "specified_command_level"),
        P0(var, "state_effector_position"),
    )
    maximum_position_change = P0(
        var, "specified_maximum_position_change_per_action"
    )
    bounded_position_change = If(
        Gt(Abs(position_error), maximum_position_change),
        If(
            Gt(position_error, L(0.0)),
            maximum_position_change,
            Times(L(-1.0), maximum_position_change),
        ),
        position_error,
    )
    predicted_position = (
        projected_position if projection_step > 0
        else Plus(projected_position, bounded_position_change)
    )
    specification_prediction = Plus(
        P0(var, f"specified_passive_mean_{key}"),
        Times(
            P0(var, f"specified_position_gain_{key}"),
            predicted_position,
        ),
    )
    return If(
        And(
            Gt(P0(var, "specified_actuator_dynamics_enabled"), L(0.5)),
            Gt(P0(var, "specified_effect_prior_confidence"), L(0.5)),
            Gt(maximum_position_change, L(0.0)),
        ),
        specification_prediction,
        learned_prediction,
    )


def model_prediction(var, key):
    return _model_prediction(var, key)


def model_prediction_at_context(var, key, context, projection_step=0):
    """Predict from a synthetic context made only from learned receipts."""
    return _model_prediction(var, key, context, projection_step)


def context_delta_prediction(var, feature, context):
    """One learned context transition; no plant/model-oracle access."""
    value = P0(var, f"mean_context_delta_{feature}")
    for conditioning in FLOW_FEATURES:
        value = Plus(value, Times(
            P0(var, f"context_delta_gain_{feature}_{conditioning}"),
            Minus(
                context.get(conditioning, P0("episode", f"state_{conditioning}")),
                P0(var, f"mean_{conditioning}"),
            ),
        ))
    return value


def group_context_transition_peers(var="model"):
    """Receipt-grounded peers sharing an actuator group with ``var``.

    This is a generic bootstrap for a cold command-level model.  It shares
    only transition evidence already learned from ordinary singleton
    receipts; it never manufactures a transition for a group with no such
    receipt.
    """
    return Filter(
        MODELS,
        "peer",
        And(
            Eq(P0("peer", "actuator_group"), P0(var, "actuator_group")),
            Gt(P0("peer", "context_delta_experience_count"), L(0.0)),
        ),
    )


def share_group_context_transition_rule():
    """Bootstrap cold siblings from deterministic group-level receipt evidence."""
    peers = group_context_transition_peers()
    peer_count = Count(peers)
    effects = [
        ["set_attr", "model", "context_delta_experience_count", T(peer_count)],
    ]
    # Average the learned transition model over same-group peers.  The
    # aggregation is deterministic because graph collection order is not used
    # as a tie-break and all members contribute symmetrically.
    for feature in CONTEXT_DELTAS:
        effects.append(["set_attr", "model", f"mean_context_delta_{feature}", T(
            Div(Sum(peers, "peer", P0("peer", f"mean_context_delta_{feature}")), peer_count)
        )])
        for conditioning in FLOW_FEATURES:
            effects.append(["set_attr", "model", f"context_delta_gain_{feature}_{conditioning}", T(
                Div(Sum(peers, "peer", P0("peer", f"context_delta_gain_{feature}_{conditioning}")), peer_count)
            )])
    for feature in FLOW_FEATURES:
        effects.append(["set_attr", "model", f"mean_{feature}", T(
            Div(Sum(peers, "peer", P0("peer", f"mean_{feature}")), peer_count)
        )])
    return {
        "name": "emp_share_group_context_transition_evidence",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": True,
        "comment": (
            "A cold command-level model may use averaged same-group transition "
            "evidence from ordinary receipts; an unevidenced group remains unsupported."
        ),
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "model"],
        ],
        "where": And(
            Eq(P0("model", "context_delta_experience_count"), L(0.0)),
            Gt(peer_count, L(0.0)),
        ),
        "effects": effects,
    }


def baseline_context_delta_at_context(feature, context):
    references = Filter(
        MODELS, "reference",
        And(Lt(P0("reference", "activation_magnitude"), L(0.5)),
            Gt(P0("reference", "context_delta_experience_count"), L(0.0))),
    )
    return If(
        Gt(Count(references), L(0.0)),
        Div(Sum(references, "reference", context_delta_prediction("reference", feature, context)), Count(references)),
        L(0.0),
    )


def composed_context_delta(source, feature, context, addition=None):
    baseline = baseline_context_delta_at_context(feature, context)
    value = Plus(
        baseline,
        Sum(members(source), "member", Minus(context_delta_prediction("member", feature, context), baseline)),
    )
    if addition is not None:
        value = Plus(value, Minus(context_delta_prediction(addition, feature, context), baseline))
    return value


def structural_model_prediction(var, key):
    return If(
        Gt(P0(var, "structural_certified_default"), L(0.5)),
        Abs(P0(var, f"specified_{key}")),
        If(
            Gt(P0(var, "experience_count"), L(0.0)),
            Max(
                Abs(model_prediction(var, key)),
                Abs(P0(var, f"specified_{key}")),
            ),
            Abs(P0(var, f"specified_{key}")),
        ),
    )


def structural_limits_enabled():
    return Gt(P0("episode", "structural_limits_enabled"), L(0.5))


def structural_current_load(key):
    return Abs(P0("episode", f"state_current_{key}"))


def structural_increment_is_zero(var):
    return And(*(
        Not(Gt(structural_model_prediction(var, key), L(0.0)))
        for key in STRUCTURAL_LOADS
    ))


def structural_model_admissible(var):
    return Or(
        Not(structural_limits_enabled()),
        Or(
            And(*(
                And(
                    Gt(P0("episode", f"state_safe_{key}"), L(0.0)),
                    Not(Gt(
                        Plus(
                            structural_current_load(key),
                            structural_model_prediction(var, key),
                        ),
                        P0("episode", f"state_safe_{key}"),
                    )),
                )
                for key in STRUCTURAL_LOADS
            )),
            And(
                Gt(P0("episode", "structural_interrupt_required"), L(0.5)),
                structural_increment_is_zero(var),
            ),
        ),
    )


def members(plan="plan"):
    return Neighbours(plan, "includes_embodied_effector_model")


def baseline_prediction_at_context(key, context=None):
    references = Filter(
        MODELS,
        "reference",
        And(
            Lt(P0("reference", "activation_magnitude"), L(0.5)),
            Gt(P0("reference", "experience_count"), L(0.5)),
        ),
    )
    return If(
        Gt(Count(references), L(0.0)),
        Div(
            Sum(
                references,
                "reference",
                model_prediction_at_context("reference", key, context or {}),
            ),
            Count(references),
        ),
        L(0.0),
    )


def baseline_prediction(key):
    return baseline_prediction_at_context(key)


def prediction(source, key, addition=None):
    baseline = baseline_prediction(key)
    value = Plus(
        baseline,
        Sum(
            members(source),
            "member",
            Minus(model_prediction("member", key), baseline),
        ),
    )
    if addition is not None:
        value = Plus(
            value,
            Minus(model_prediction(addition, key), baseline),
        )
    return value


def prediction_at_context(source, key, context, addition=None, projection_step=0):
    baseline = baseline_prediction_at_context(key, context)
    value = Plus(
        baseline,
        Sum(
            members(source),
            "member",
            Minus(model_prediction_at_context("member", key, context, projection_step), baseline),
        ),
    )
    if addition is not None:
        value = Plus(
            value,
            Minus(model_prediction_at_context(addition, key, context, projection_step), baseline),
        )
    return value


def _synthetic_context(source, step, addition=None):
    """Unroll receipt-learned context transitions for one bounded slice."""
    context = {feature: P0("episode", f"state_{feature}") for feature in FLOW_FEATURES}
    for _ in range(step):
        next_context = {}
        for feature in FLOW_FEATURES:
            delta = composed_context_delta(source, feature, context, addition)
            next_context[feature] = Plus(context[feature], delta)
        # This is a derived coordinate of the learned context, not a plant
        # query or a physical forward model.
        next_context["flow_speed_squared"] = Plus(*(
            Times(next_context[feature], next_context[feature])
            for feature in FLOW_FEATURES[:3]
        ))
        context = next_context
    if "flow_speed_squared" not in context:
        context["flow_speed_squared"] = Plus(*(
            Times(context[feature], context[feature])
            for feature in FLOW_FEATURES[:3]
        ))
    return context


def _projection_supported(source, addition=None):
    specified_transition_prior = And(
        Gt(P0("member", "specified_actuator_dynamics_enabled"), L(0.5)),
        Gt(P0("member", "specified_effect_prior_confidence"), L(0.5)),
        Gt(P0("member", "specified_maximum_position_change_per_action"), L(0.0)),
    )
    checks = [Gt(P0("member", "experience_count"), L(0.0))]
    # Every transition is receipt-derived; no delta evidence means unresolved.
    checks.append(Or(
        Gt(P0("member", "context_delta_experience_count"), L(0.0)),
        specified_transition_prior,
    ))
    support = And(*checks)
    supported = Not(Exists(members(source), "member", Not(support)))
    if addition is not None:
        supported = And(
            supported,
            Gt(P0(addition, "experience_count"), L(0.0)),
            Or(
                Gt(P0(addition, "context_delta_experience_count"), L(0.0)),
                And(
                    Gt(P0(addition, "specified_actuator_dynamics_enabled"), L(0.5)),
                    Gt(P0(addition, "specified_effect_prior_confidence"), L(0.5)),
                    Gt(P0(addition, "specified_maximum_position_change_per_action"), L(0.0)),
                ),
            ),
        )
    return supported


def manifold_projection_loss(source="plan", step=1, addition=None):
    context = _synthetic_context(source, step, addition)
    terms = []
    for key in COMPONENTS:
        residual = Abs(Minus(
            P0("episode", f"target_{key}"),
            prediction_at_context(source, key, context, addition, step),
        ))
        terms.append(If(And(
            Gt(P0("policy", f"{key}_weight"), L(0.0)),
            Gt(residual, P0("episode", f"manifold_bound_{key}")),
        ), L(1.0), L(0.0)))
    return Plus(*terms)


def manifold_projection_horizon(source="plan", addition=None):
    return native_future_projection(source, addition, "horizon")


def manifold_projection_horizon_legacy(source="plan", addition=None):
    """Earliest supported loss; all-retained paths stop unresolved at budget."""
    horizon = L(float(FUTURE_MANIFOLD_PROJECTION_BUDGET))
    for step in reversed(range(1, FUTURE_MANIFOLD_PROJECTION_BUDGET + 1)):
        current = _synthetic_context(source, step, addition)
        previous = _synthetic_context(source, step - 1, addition)
        no_progress = And(
            *(Eq(current[feature], previous[feature]) for feature in FLOW_FEATURES),
            Not(Exists(members(source), "member", Not(Eq(
                _projected_position("member", step),
                _projected_position("member", step - 1),
            )))),
            Eq(_projected_position(addition, step), _projected_position(addition, step - 1)) if addition is not None else Eq(L(0.0), L(0.0)),
        )
        horizon = If(
            Or(Gt(manifold_projection_loss(source, step, addition), L(0.0)), no_progress),
            L(float(step)), horizon,
        )
    return horizon


def manifold_projection_axis_lost(source, key, addition=None):
    return Not(Gt(native_future_projection(source, addition, f"retained_{key}"), L(0.5)))


def manifold_projection_axis_lost_legacy(source, key, addition=None):
    horizon = manifold_projection_horizon(source, addition)
    values = []
    for step in range(1, FUTURE_MANIFOLD_PROJECTION_BUDGET + 1):
        context = _synthetic_context(source, step, addition)
        residual = Abs(Minus(P0("episode", f"target_{key}"), prediction_at_context(source, key, context, addition, step)))
        values.append(If(Eq(horizon, L(float(step))), Gt(residual, P0("episode", f"manifold_bound_{key}")), L(False)))
    return Or(*values)


def manifold_projection_loss_at_decision(source="plan", addition=None):
    horizon = manifold_projection_horizon(source, addition)
    terms = [If(Eq(horizon, L(float(step))), manifold_projection_loss(source, step, addition), L(0.0)) for step in range(1, FUTURE_MANIFOLD_PROJECTION_BUDGET + 1)]
    return Plus(*terms)


def structural_program_admissible(source, addition=None):
    def predicted(key):
        value = Plus(
            structural_current_load(key),
            Sum(
                members(source),
                "structural_member",
                structural_model_prediction("structural_member", key),
            ),
        )
        if addition is not None:
            value = Plus(
                value,
                structural_model_prediction(addition, key),
            )
        return value

    return Or(
        Not(structural_limits_enabled()),
        # Envelope limits are soft during an authority-escape state.  The
        # world adapter raises this flag only when preserving flight requires
        # accepting a bounded risk excursion.
        Gt(P0("episode", "authority_escape_mode"), L(0.5)),
        And(*(
            And(
                Gt(P0("episode", f"state_safe_{key}"), L(0.0)),
                Not(Gt(
                    predicted(key),
                    P0("episode", f"state_safe_{key}"),
                )),
            )
            for key in STRUCTURAL_LOADS
        )),
    )


def program_cost(source, addition=None):
    terms = []
    for key in COMPONENTS:
        residual = Minus(
            P0("episode", f"target_{key}"),
            prediction(source, key, addition),
        )
        terms.append(
            Times(
                P0("policy", f"{key}_weight"),
                residual,
                residual,
            )
        )
    for key in ("drag", "energy"):
        amount = prediction(source, key, addition)
        terms.append(Times(P0("policy", f"{key}_weight"), amount))
    activation = Sum(
        members(source),
        "member",
        P0("member", "activation_magnitude"),
    )
    if addition is not None:
        activation = Plus(
            activation,
            P0(addition, "activation_magnitude"),
        )
    terms.append(Times(P0("policy", "activation_weight"), activation))
    terms.append(
        Times(
            P0("policy", "activation_weight"),
            Sum(members(source), "member", Neg(P0("member", "log_authority"))),
        )
    )
    if addition is not None:
        terms.append(
            Times(
                P0("policy", "activation_weight"),
                Neg(P0(addition, "log_authority")),
            )
        )
    return Plus(*terms)


def singleton_cost(candidate):
    terms = []
    for key in COMPONENTS:
        residual = Minus(
            P0("episode", f"target_{key}"),
            model_prediction(candidate, key),
        )
        terms.append(
            Times(P0("policy", f"{key}_weight"), residual, residual)
        )
    for key in ("drag", "energy"):
        terms.append(
            Times(
                P0("policy", f"{key}_weight"),
                model_prediction(candidate, key),
            )
        )
    terms.append(
        Times(
            P0("policy", "activation_weight"),
            P0(candidate, "activation_magnitude"),
        )
    )
    terms.append(
        Times(
            P0("policy", "activation_weight"),
            Neg(P0(candidate, "log_authority")),
        )
    )
    return Plus(*terms)


def available_models(plan="plan"):
    return Filter(
        MODELS,
        "candidate",
        And(
            Gt(P0("candidate", "experience_count"), L(0.5)),
            Gt(P0("candidate", "available"), L(0.5)),
            structural_program_admissible(plan, "candidate"),
            Not(Exists(
                members(plan),
                "existing",
                Eq(
                    P0("existing", "actuator_group"),
                    P0("candidate", "actuator_group"),
                ),
            )),
        ),
    )


def composition_width_available(source="plan"):
    """Whether one more member may be added under the declared width cap."""
    return Or(
        Not(Gt(P0("episode", "maximum_program_width"), L(0.0))),
        Lt(P0(source, "member_count"), P0("episode", "maximum_program_width")),
    )


def retire_old_options_rule():
    return {
        "name": "emp_retire_previous_program_options",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_motor_decision_option", "program"],
        ],
        "where": And(
            Gt(
                P0("episode", "program_request_seq"),
                P0("program", "request_seq"),
            ),
            Eq(P0("program", "available"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "program", "available", 0.0],
            [
                "del_edge",
                "episode",
                "has_motor_decision_option",
                "program",
            ],
        ],
    }


_RESIDUAL_CONSEQUENCES = (
    ("forward", "pre_body_vx", "post_body_vx"),
    ("lateral", "pre_body_vy", "post_body_vy"),
    ("vertical", "pre_body_vz", "post_body_vz"),
    ("roll", "pre_body_wx", "post_body_wx"),
    ("pitch", "pre_body_wy", "post_body_wy"),
    ("turn", "pre_body_wz", "post_body_wz"),
)


def share_slope_across_command_levels_rule():
    """THE LEVELS OF ONE EFFECTOR ARE ONE LINE, NOT NINE FACTS.

    Measured (block CI part 2): within an actuator group the primary consequence
    is EXACTLY linear in command level -- aileron `mean_roll` is `0.5 x level`
    across all nine levels, rudder `mean_turn` is `-0.01 x level`, to the digit.
    The nine models per group are nine samples of one line, and the tree holds
    222 attributes to express what four slopes describe.

    Holding them separately costs three measured things: identifiability reads
    as 37 unknowns when it is 4 slopes (BV measured 0% identifiable during a
    departure); coverage is bounded by admissibility because the aggressive end
    of the envelope can never be safely commanded (CG measured 6 of 37 tokens
    reached); and each model crawls toward its own point at 1/n when one estimate
    should move all nine (CA measured samples producing no understanding).

    So when one level learns, its siblings learn WITH it, by the ratio of their
    command levels -- which is the transform rung of the sd loop applied to the
    command axis, and the same statement `scale2` makes about a base being a
    dimension. A safe exercise at 0.25 now fixes the response at 1.0 without
    ever commanding it, which is the only way the end of the envelope that
    matters in a departure can be characterised at all.

    Absent `command_level_slope_sharing` (0) the rule never fires, so every
    consumer that does not declare it is byte-identical. The zero-level sibling
    is excluded as a source: a line through the origin cannot be fixed from the
    origin.
    """
    source_level = P0("source", "specified_command_level")
    target_level = P0("target", "specified_command_level")
    ratio = Div(target_level, source_level)
    return {
        "name": "emp_share_slope_across_command_levels",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "order": -43,
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "source"],
            ["episode", "has_embodied_effector_model", "target"],
        ],
        "where": And(
            Gt(P0("episode", "command_level_slope_sharing"), L(0.5)),
            Not(Eq(V("source"), V("target"))),
            Eq(
                P0("source", "actuator_group"),
                P0("target", "actuator_group"),
            ),
            # WITHIN ONE RANGE OF THE RATIO.  A slope holds over a range of the
            # command axis, not over the whole of it; absent any split every
            # model reads 0 and the group is one range, which is the behaviour
            # measured at damaged_wing 2/3 -> 0/3.
            Eq(
                P0("source", "slope_range_ordinal"),
                P0("target", "slope_range_ordinal"),
            ),
            # a line through the origin cannot be fixed from the origin
            Gt(Abs(source_level), L(0.000001)),
            # the source has learned since the target last took its slope
            Gt(
                P0("source", "last_learning_seq"),
                P0("target", "last_slope_share_seq"),
            ),
        ),
        "effects": [
            *[
                ["set_attr", "target", f"mean_{key}", T(Times(
                    P0("source", f"mean_{key}"), ratio
                ))]
                for key in ALL_CONSEQUENCES
            ],
            ["set_attr", "target", "last_slope_share_seq", T(
                P0("source", "last_learning_seq")
            )],
        ],
    }


def learn_uncommanded_contributor_rule():
    """Learn a NEVER-COMMANDED contributor from what it does while others act.

    Such a contributor is never sampled, so the calibration path can teach it
    nothing -- commanding is how that path learns, and it is excluded from the
    frontier for exactly that reason.  But it acts every action, and what it
    does is what the commanded members do NOT account for:

        residual = observed change - sum of the commanded members' predictions

    Averaged incrementally, that gives it the same `mean_*` columns every other
    effector carries, learned from ordinary flight rather than from exercise.
    Once populated, the probe, authority and containment machinery reads this
    contributor exactly as it reads a surface -- none of them change.

    This is the attribution a body plan makes possible: with no node the same
    residual is unattributable and can only be reported as "the plant moved";
    with one it is a column in a model.

    Domain-free -- body-frame rates and velocities, no effector, axis or
    vehicle named.
    """
    count = Plus(P0("model", "experience_count"), L(1.0))
    effects = [
        ["set_attr", "model", "experience_count", T(count)],
        ["set_attr", "model", "last_learning_seq", T(
            P0("outcome", "request_seq")
        )],
    ]
    for name, pre, post in _RESIDUAL_CONSEQUENCES:
        observed = Minus(P0("outcome", post), P0("outcome", pre))
        predicted = Sum(
            Filter(
                Neighbours("trial", "commands_embodied_effector_model"),
                "peer",
                Not(Gt(P0("peer", "never_commanded"), L(0.5))),
            ),
            "peer",
            P0("peer", f"mean_{name}"),
        )
        residual = Minus(observed, predicted)
        mean = P0("model", f"mean_{name}")
        effects.append([
            "set_attr", "model", f"mean_{name}",
            T(Plus(mean, Div(Minus(residual, mean), count))),
        ])
    return {
        "name": "emp_learn_uncommanded_contributor_from_residual",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "order": -44,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
            ["trial", "commands_embodied_effector_model", "model"],
        ],
        "where": And(
            Gt(P0("model", "never_commanded"), L(0.5)),
            Eq(P0("outcome", "processed"), L(1.0)),
            Gt(P0("outcome", "request_seq"),
               P0("model", "last_learning_seq")),
        ),
        "effects": effects,
    }


# Consequence names paired with the outcome columns whose change measures
# them.  Body-frame rates and velocities -- no domain vocabulary.
_RESIDUAL_CONSEQUENCES = (
    ("forward", "pre_body_vx", "post_body_vx"),
    ("lateral", "pre_body_vy", "post_body_vy"),
    ("vertical", "pre_body_vz", "post_body_vz"),
    ("roll", "pre_body_wx", "post_body_wx"),
    ("pitch", "pre_body_wy", "post_body_wy"),
    ("turn", "pre_body_wz", "post_body_wz"),
)


def _cannot_be_moved(var):
    """An effector whose command cannot change its position.

    This is the generic form of "you cannot command it": zero authority by
    construction rather than by a declared flag.  The body itself is the
    standing example -- an airframe is commanded once, at build time, and no
    command in flight moves it -- and a consumer says so simply by declaring a
    maximum position change of zero, which it must do anyway.

    Absence reads as zero, so any model that omits the declaration is treated
    as unmovable; every existing consumer declares it, so nothing changes.
    """
    return Not(Gt(
        P0(var, "specified_maximum_position_change_per_action"), L(0.0)
    ))


def learn_unmovable_contributor_rule():
    """Learn an unmovable contributor from what it does while the others act.

    Such an effector is selected and commanded like any other, so the ordinary
    learning path does reach it -- but only when it is SELECTED, which is an
    Argmin it rarely wins: measured, experience reached 1, 3 and 7 over a
    thousand actions (§70).  Its contribution, though, is present in EVERY
    action, and it is exactly what the movable members do not account for:

        residual = observed change - sum of the movable members' predictions

    Averaged incrementally, that fills the same `mean_*` columns from ordinary
    flight instead of from the rare selection.  It is the negative space
    between the effectors, computed rather than waited for.
    """
    count = Plus(P0("model", "experience_count"), L(1.0))
    effects = [
        ["set_attr", "model", "experience_count", T(count)],
        ["set_attr", "model", "last_learning_seq", T(
            P0("outcome", "request_seq")
        )],
    ]
    for name, pre, post in _RESIDUAL_CONSEQUENCES:
        observed = Minus(P0("outcome", post), P0("outcome", pre))
        predicted = Sum(
            Filter(
                Neighbours("trial", "commands_embodied_effector_model"),
                "peer",
                Gt(P0("peer", "specified_maximum_position_change_per_action"),
                   L(0.0)),
            ),
            "peer",
            P0("peer", f"mean_{name}"),
        )
        mean = P0("model", f"mean_{name}")
        effects.append([
            "set_attr", "model", f"mean_{name}",
            T(Plus(mean, Div(Minus(Minus(observed, predicted), mean), count))),
        ])
    return {
        "name": "emp_learn_unmovable_contributor_from_residual",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "order": -44,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
            ["episode", "has_embodied_effector_model", "model"],
        ],
        "where": And(
            _cannot_be_moved("model"),
            Eq(P0("outcome", "processed"), L(1.0)),
            Gt(P0("outcome", "request_seq"),
               P0("model", "last_learning_seq")),
        ),
        "effects": effects,
    }


def calibration_frontier():
    """Models still owed calibration samples.

    `never_commanded` contributors are excluded, and the reason is the second
    half of the effector contract: calibration samples a model BY COMMANDING
    IT, so a contributor that is never commanded can never be sampled, never
    accumulates experience, and never leaves this frontier -- which stalls the
    pass permanently.  Measured: adding a plant contributor without this
    exclusion deadlocked the loop on its first request with a non-progressing
    calibration state.

    Such a contributor is still LEARNED, from what it does while the commanded
    effectors act; it is simply never the thing being exercised.
    """
    unsampled = Filter(
        MODELS,
        "candidate",
        And(
            Not(Gt(P0("candidate", "never_commanded"), L(0.5))),
            Or(
                Lt(
                    P0("candidate", "experience_count"),
                    P0("policy", "calibration_samples"),
                ),
                Gt(P0("candidate", "recalibration_required"), L(0.5)),
                # UNATTRIBUTABLE IS ALSO OWED A SAMPLE.
                #
                # A model commanded only inside compound programs accumulates no
                # attributable experience: the receipt teaches the PROGRAM, and
                # the residual has as many owners as the program has members.
                # Measured on a departing wing -- 450 actions, 37 member tokens,
                # ZERO windows in which the members are identifiable from
                # composition variation alone -- while the models the loop was
                # steering with were last calibrated in level flight.
                #
                # Being well sampled is not the same as being KNOWN NOW.  A model
                # unseen alone for longer than the operator's declared interval
                # rejoins the frontier, and `least_sampled` prefers it on the same
                # terms as an uncalibrated one.
                #
                # Absent `attribution_refresh_actions` (0) this clause is never
                # true, so a consumer that does not declare it is unchanged.  It
                # buys no new authority and no new information spend: the measured
                # singleton rate already exceeds what attribution needs (9.1%
                # against 6.0% at W=50); this only redirects which model those
                # exercises land on -- currently 18 of 41 go to one effector while
                # two members of the flown program are never exercised at all.
                And(
                    Gt(P0("policy", "attribution_refresh_actions"), L(0.0)),
                    Gt(
                        Minus(
                            P0("episode", "program_request_seq"),
                            P0("candidate", "last_singleton_exercise_seq"),
                        ),
                        P0("policy", "attribution_refresh_actions"),
                    ),
                ),
            ),
            structural_model_admissible("candidate"),
        ),
    )
    least_sampled = Argmin(
        unsampled,
        "candidate",
        P0("candidate", "experience_count"),
        V("episode"),
    )
    return Filter(
        unsampled,
        "candidate",
        Eq(
            P0("candidate", "experience_count"),
            AO(least_sampled, "experience_count"),
        ),
    )


def calibration_target():
    return Argmin(
        calibration_frontier(),
        "candidate",
        P0("candidate", "ordinal"),
        V("episode"),
    )


def calibration_program_effects(primary, source):
    return [
        ["add_node", "program", "EmbodiedMotorProgram", {
            "request_seq": T(P0("episode", "program_request_seq")),
            "ordinal": T(P0("episode", "program_request_seq")),
            "token": T(A(primary, "token")),
            "status": "ready",
            "source": source,
            "member_count": 1.0,
            "available": 1.0,
            "grounded_value": 0.0,
            "default_value": 0.0,
            "learned_value": 0.0,
            "decision_experience_count": 0.0,
            "internalized_epoch": -1.0,
            "experience_count": 0.0,
            **{f"mean_{key}": 0.0 for key in ALL_CONSEQUENCES},
            **{f"flow_gain_{key}": 0.0 for key in ALL_CONSEQUENCES},
            **{f"mean_context_delta_{feature}": 0.0 for feature in CONTEXT_DELTAS},
            **{f"context_delta_gain_{feature}_{conditioning}": 0.0 for feature in CONTEXT_DELTAS for conditioning in FLOW_FEATURES},
            "context_delta_experience_count": 0.0,
            "mean_flow_speed_squared": 0.0,
            **{f"mean_{feature}": 0.0 for feature in FLOW_FEATURES},
            "last_learning_seq": 0.0,
        }],
        [
            "add_edge",
            "episode",
            "has_embodied_motor_program",
            "program",
        ],
        [
            "add_edge",
            "program",
            "includes_embodied_effector_model",
            primary,
        ],
        *future_manifold_audit_effects("program"),
        [
            "add_edge",
            "episode",
            "has_motor_decision_option",
            "program",
        ],
        ["set_attr", "episode", "program_decision_seq", T(
            P0("episode", "program_request_seq")
        )],
        ["set_attr", "episode", "decision_request_epoch", T(
            P0("episode", "program_request_seq")
        )],
        ["set_attr", "episode", "decision_armed", 1.0],
    ]


def open_flow_excitation_program_rule():
    target = calibration_target()
    learned = Filter(
        MODELS,
        "candidate",
        Gt(P0("candidate", "experience_count"), L(0.5)),
    )
    accelerator = Argmax(
        learned,
        "candidate",
        model_prediction("candidate", "forward"),
        V("episode"),
    )
    return {
        "name": "emp_open_flow_excitation_program",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "primary"],
        ],
        "where": And(
            Eq(A("episode", "program_mode"), L("calibration")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "program_decision_seq"),
            ),
            Gt(Count(calibration_frontier()), L(0.0)),
            Gt(AO(target, "experience_count"), L(0.5)),
            Lt(
                P0("episode", "state_flow_speed_squared"),
                P0("policy", "minimum_calibration_flow_speed_squared"),
            ),
            Gt(AO(accelerator, "mean_forward"), L(0.0)),
            Eq(P0("primary", "ordinal"), AO(accelerator, "ordinal")),
        ),
        "effects": calibration_program_effects(
            "primary",
            "graph_requested_flow_excitation",
        ),
    }


def open_calibration_program_rule():
    target = calibration_target()
    return {
        "name": "emp_open_factorized_calibration_program",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "primary"],
        ],
        "where": And(
            Eq(A("episode", "program_mode"), L("calibration")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "program_decision_seq"),
            ),
            Gt(Count(calibration_frontier()), L(0.0)),
            Or(
                Eq(AO(target, "experience_count"), L(0.0)),
                Gt(
                    P0("episode", "state_flow_speed_squared"),
                    P0("policy", "minimum_calibration_flow_speed_squared"),
                ),
                Not(Gt(
                    AO(Argmax(
                        Filter(
                            MODELS,
                            "learned",
                            Gt(P0("learned", "experience_count"), L(0.5)),
                        ),
                        "learned",
                        model_prediction("learned", "forward"),
                        V("episode"),
                    ), "mean_forward"),
                    L(0.0),
                )),
            ),
            Eq(P0("primary", "ordinal"), AO(target, "ordinal")),
        ),
        "effects": calibration_program_effects(
            "primary",
            "factorized_calibration",
        ),
    }


def complete_calibration_rule():
    return {
        "name": "emp_complete_receipt_grounded_effector_calibration",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("episode", "program_mode"), L("calibration")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(P0("outcome", "processed"), L(1.0)),
            Eq(
                P0("outcome", "request_seq"),
                P0("episode", "program_request_seq"),
            ),
            Eq(
                P0("episode", "receipt_boundary_seq"),
                P0("outcome", "request_seq"),
            ),
            Eq(Count(calibration_frontier()), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "program_mode", "synthesis"],
            ["set_attr", "episode", "calibration_complete", 1.0],
        ],
    }


def complete_specification_prior_initialization_rule():
    """Enter synthesis when trusted body specifications cover every effector."""
    return {
        "name": "emp_complete_specification_grounded_prior_initialization",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "order": -45,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
        ],
        "where": And(
            Eq(A("episode", "program_mode"), L("calibration")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Eq(Count(calibration_frontier()), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "program_mode", "synthesis"],
            ["set_attr", "episode", "calibration_complete", 1.0],
        ],
    }


def derive_active_rate_stabilization_targets_rule():
    """Turn vestibular body rates into a per-request damping objective."""
    action_duration = P0("episode", "control_action_duration_seconds")
    damping_fraction = Div(
        action_duration,
        P0("episode", "rate_damping_time_constant_seconds"),
    )

    def attitude_correction(axis):
        target_angle = P0("episode", f"target_{axis}_angle")
        if axis == "pitch":
            # During aerodynamic departure recovery, holding the ordinary
            # attitude target (usually level body pitch) while separately
            # lowering alpha commands a persistent nose-down flight path.
            # A generic recovery target is instead an alpha-aligned pitch:
            # with no outer-loop flight-path reference, this preserves the
            # current zero-flight-path objective while the alpha loop exits
            # the departure.  The condition is entirely capability/episode
            # driven and applies to any plant exposing these state channels;
            # it is not an F-16 command or surface rule.
            target_angle = If(
                And(
                    Gt(
                        P0(
                            "episode",
                            "active_angle_of_attack_recovery",
                        ),
                        L(0.5),
                    ),
                ),
                P0("episode", "target_recovery_alpha_radians"),
                target_angle,
            )
        difference = Minus(
            target_angle,
            P0("episode", f"state_{axis}_angle"),
        )
        angular_error = (
            difference
            if axis == "pitch"
            else Atan2(Sin(difference), Cos(difference))
        )
        return If(
            And(
                Gt(P0("episode", "active_attitude_stabilization"), L(0.5)),
                Or(
                    Not(Gt(
                        P0(
                            "episode",
                            "attitude_axis_gating_enabled",
                        ),
                        L(0.5),
                    )),
                    Gt(
                        P0(
                            "episode",
                            f"active_{axis}_attitude_stabilization",
                        ),
                        L(0.5),
                    ),
                ),
                Gt(
                    P0("episode", "attitude_time_constant_seconds"),
                    L(0.0),
                ),
            ),
            Times(
                angular_error,
                action_duration,
                Div(
                    L(1.0),
                    Times(
                        P0(
                            "episode",
                            "attitude_time_constant_seconds",
                        ),
                        P0(
                            "episode",
                            "rate_damping_time_constant_seconds",
                        ),
                    ),
                ),
            ),
            L(0.0),
        )

    angle_of_attack_correction = If(
        And(
            Gt(
                P0("episode", "active_angle_of_attack_recovery"),
                L(0.5),
            ),
            Gt(
                P0("episode", "aerodynamic_departure_active"),
                L(0.5),
            ),
            Gt(
                P0("episode", "angle_of_attack_time_constant_seconds"),
                L(0.0),
            ),
        ),
        Times(
            Minus(
                P0("episode", "target_recovery_alpha_radians"),
                P0("episode", "state_angle_of_attack"),
            ),
            action_duration,
            Div(
                L(1.0),
                Times(
                    P0(
                        "episode",
                        "angle_of_attack_time_constant_seconds",
                    ),
                    P0(
                        "episode",
                        "rate_damping_time_constant_seconds",
                    ),
                ),
            ),
        ),
        L(0.0),
    )

    return {
        "name": "emp_derive_active_rate_stabilization_targets",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -50,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
        ],
        "where": And(
            Gt(P0("episode", "active_rate_stabilization"), L(0.5)),
            Gt(P0("episode", "control_action_duration_seconds"), L(0.0)),
            Gt(P0("episode", "rate_damping_time_constant_seconds"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "rate_target_request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "target_roll", T(Plus(
                Times(
                    L(-1.0),
                    P0("episode", "state_body_wx"),
                    damping_fraction,
                ),
                attitude_correction("roll"),
            ))],
            ["set_attr", "episode", "target_pitch", T(Plus(
                Times(
                    L(-1.0),
                    P0("episode", "state_body_wy"),
                    damping_fraction,
                ),
                attitude_correction("pitch"),
                angle_of_attack_correction,
            ))],
            ["set_attr", "episode", "target_turn", T(Plus(
                Times(
                    L(-1.0),
                    P0("episode", "state_body_wz"),
                    damping_fraction,
                ),
                attitude_correction("yaw"),
            ))],
            ["set_attr", "episode", "rate_target_request_seq", T(
                P0("episode", "program_request_seq")
            )],
        ],
    }


def derive_flight_path_control_targets_rule():
    """Map altitude, heading and true-airspeed references into motor goals.

    This is the graph-resident outer loop used by the F-16 paper replication.
    The world adapter supplies only measured state and externally scheduled
    references.  The graph derives bank/pitch targets and four-axis consequence
    requests before the existing rate-stabilisation and motor-collapse rules
    run.
    """
    action_duration = P0("episode", "control_action_duration_seconds")
    altitude_error = Minus(
        P0("episode", "reference_altitude_m"),
        P0("episode", "state_altitude_m"),
    )
    heading_difference = Minus(
        P0("episode", "reference_heading_rad"),
        P0("episode", "state_yaw_angle"),
    )
    heading_error = Atan2(Sin(heading_difference), Cos(heading_difference))
    airspeed_error = Minus(
        P0("episode", "reference_true_airspeed_m_s"),
        P0("episode", "state_true_airspeed_m_s"),
    )
    desired_vertical_speed = Clamp(
        Div(altitude_error, P0("episode", "altitude_time_constant_seconds")),
        Times(L(-1.0), P0("episode", "maximum_vertical_speed_m_s")),
        P0("episode", "maximum_vertical_speed_m_s"),
    )
    vertical_speed_error = Minus(
        desired_vertical_speed,
        P0("episode", "state_vz"),
    )
    desired_flight_path_angle = Clamp(
        Atan2(
            vertical_speed_error,
            Max(Abs(P0("episode", "state_true_airspeed_m_s")), L(1.0)),
        ),
        Times(L(-1.0), P0("episode", "maximum_flight_path_angle_rad")),
        P0("episode", "maximum_flight_path_angle_rad"),
    )
    desired_heading_rate = Clamp(
        Div(heading_error, P0("episode", "heading_time_constant_seconds")),
        Times(L(-1.0), P0("episode", "maximum_heading_rate_rad_s")),
        P0("episode", "maximum_heading_rate_rad_s"),
    )
    desired_bank_angle = Clamp(
        Atan2(
            Times(
                P0("episode", "state_true_airspeed_m_s"),
                desired_heading_rate,
            ),
            P0("episode", "gravity_m_s2"),
        ),
        Times(L(-1.0), P0("episode", "maximum_bank_angle_rad")),
        P0("episode", "maximum_bank_angle_rad"),
    )
    desired_pitch_angle = Clamp(
        Plus(
            desired_flight_path_angle,
            P0("episode", "state_angle_of_attack"),
        ),
        Times(L(-1.0), P0("episode", "maximum_pitch_angle_rad")),
        P0("episode", "maximum_pitch_angle_rad"),
    )
    forward_delta = Clamp(
        Times(
            airspeed_error,
            Div(
                action_duration,
                P0("episode", "airspeed_time_constant_seconds"),
            ),
        ),
        Times(L(-1.0), P0("episode", "maximum_forward_delta_m_s")),
        P0("episode", "maximum_forward_delta_m_s"),
    )
    lateral_delta = Times(
        L(-1.0),
        P0("episode", "state_body_vy"),
        Div(
            action_duration,
            P0("episode", "sideslip_time_constant_seconds"),
        ),
    )
    return {
        "name": "emp_derive_flight_path_control_targets",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -60,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
        ],
        "where": And(
            Gt(P0("episode", "active_flight_path_control"), L(0.5)),
            Gt(P0("episode", "control_action_duration_seconds"), L(0.0)),
            Gt(P0("episode", "altitude_time_constant_seconds"), L(0.0)),
            Gt(P0("episode", "heading_time_constant_seconds"), L(0.0)),
            Gt(P0("episode", "airspeed_time_constant_seconds"), L(0.0)),
            Gt(P0("episode", "sideslip_time_constant_seconds"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "flight_path_target_request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "target_roll_angle", T(
                desired_bank_angle
            )],
            ["set_attr", "episode", "target_pitch_angle", T(
                desired_pitch_angle
            )],
            ["set_attr", "episode", "target_yaw_angle", T(
                P0("episode", "reference_heading_rad")
            )],
            ["set_attr", "episode", "target_forward", T(forward_delta)],
            ["set_attr", "episode", "target_lateral", T(lateral_delta)],
            ["set_attr", "episode", "target_vertical", 0.0],
            ["set_attr", "episode", "target_normal_load", 0.0],
            ["set_attr", "episode", "flight_path_altitude_error_m", T(
                altitude_error
            )],
            ["set_attr", "episode", "flight_path_heading_error_rad", T(
                heading_error
            )],
            ["set_attr", "episode", "flight_path_airspeed_error_m_s", T(
                airspeed_error
            )],
            ["set_attr", "episode", "flight_path_target_request_seq", T(
                P0("episode", "program_request_seq")
            )],
        ],
    }


def gate_distal_goals_during_aerodynamic_departure_rule():
    currently_active = Gt(
        P0("episode", "aerodynamic_departure_active"),
        L(0.5),
    )
    entry_condition = Or(
        Gt(
            Abs(P0("episode", "state_angle_of_attack")),
            P0("episode", "departure_entry_alpha_radians"),
        ),
        Gt(
            Abs(P0("episode", "state_body_wz")),
            P0("episode", "departure_entry_yaw_rate_rad_s"),
        ),
    )
    remain_condition = Or(
        Gt(
            Abs(P0("episode", "state_angle_of_attack")),
            P0("episode", "departure_exit_alpha_radians"),
        ),
        Gt(
            Abs(P0("episode", "state_body_wz")),
            P0("episode", "departure_exit_yaw_rate_rad_s"),
        ),
    )
    next_active = If(
        currently_active,
        If(remain_condition, L(1.0), L(0.0)),
        If(entry_condition, L(1.0), L(0.0)),
    )
    distal_goal_enabled = Minus(L(1.0), next_active)
    return {
        "name": "emp_gate_distal_goals_during_aerodynamic_departure",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -55,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
        ],
        "where": And(
            Gt(
                P0("episode", "aerodynamic_departure_gating_enabled"),
                L(0.5),
            ),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "departure_gate_request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "aerodynamic_departure_active", T(
                next_active
            )],
            ["set_attr", "episode", "active_roll_attitude_stabilization", T(
                distal_goal_enabled
            )],
            ["set_attr", "episode", "active_yaw_attitude_stabilization", T(
                distal_goal_enabled
            )],
            ["set_attr", "episode", "active_pitch_attitude_stabilization", 1.0],
            ["set_attr", "episode", "departure_gate_request_seq", T(
                P0("episode", "program_request_seq")
            )],
        ],
    }


def reuse_internalized_program_rule():
    return {
        "name": "emp_release_internalized_program_default",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            [
                "episode",
                "has_default_embodied_motor_program",
                "program",
            ],
        ],
        "where": And(
            Eq(A("episode", "program_mode"), L("synthesis")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "program_decision_seq"),
            ),
            Lt(
                P0("episode", "default_program_reuse_count"),
                P0("policy", "maximum_default_program_reuse_cycles"),
            ),
            Gt(P0("program", "experience_count"), L(0.0)),
            structural_program_admissible("program"),
            manifold_reuse_allowed("program"),
        ),
        "effects": [
            ["set_attr", "program", "request_seq", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "program", "available", 1.0],
            [
                "del_edge",
                "episode",
                "has_archived_embodied_motor_program",
                "program",
            ],
            [
                "add_edge",
                "episode",
                "has_embodied_motor_program",
                "program",
            ],
            [
                "add_edge",
                "episode",
                "has_motor_decision_option",
                "program",
            ],
            ["set_attr", "episode", "program_decision_seq", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "episode", "decision_request_epoch", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "episode", "decision_armed", 1.0],
            ["set_attr", "episode", "default_program_reuse_count", T(
                Plus(P0("episode", "default_program_reuse_count"), L(1.0))
            )],
        ],
    }


def async_synthesis_enabled():
    """Opt-in flag for asynchronous System-2 publication (item 2 of the
    F-16 improvement order): System 1 serves the action at rate from the
    trusted default while System 2 builds across requests and publishes a
    replacement by atomic default swap."""
    return Gt(P0("policy", "asynchronous_synthesis_enabled"), L(0.5))


def async_release_trusted_default_rule():
    """System 1 at rate: re-arm the trusted default regardless of reuse caps.

    Trust is epoch-gated (async_trust_epoch, consumer-set): a default
    internalized before a declared plant change (e.g. the F-16 fault onset)
    is NOT trusted, so the first post-change build still runs synchronously.
    Ordered before the synchronous open rule so a trusted default preempts a
    blocking build.  Inactive whenever the render-first proposer is active —
    a 27 ms fresh-target render beats serving a stale program.
    """
    return {
        "name": "emp_async_release_trusted_default",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -5,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            [
                "episode",
                "has_default_embodied_motor_program",
                "program",
            ],
        ],
        "where": And(
            async_synthesis_enabled(),
            Not(render_first_enabled()),
            Eq(A("episode", "program_mode"), L("synthesis")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "program_decision_seq"),
            ),
            # Receipt-verified, OR freshly published by the async close —
            # an async-published program is served unverified exactly the
            # way a synchronously built one is trialed unverified.
            Or(
                Gt(P0("program", "experience_count"), L(0.0)),
                Gt(P0("program", "async_published"), L(0.5)),
            ),
            Not(Lt(
                P0("program", "internalized_epoch"),
                P0("episode", "async_trust_epoch"),
            )),
            structural_program_admissible("program"),
            manifold_reuse_allowed("program"),
        ),
        "effects": [
            ["set_attr", "program", "request_seq", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "program", "available", 1.0],
            [
                "del_edge",
                "episode",
                "has_archived_embodied_motor_program",
                "program",
            ],
            [
                "add_edge",
                "episode",
                "has_embodied_motor_program",
                "program",
            ],
            [
                "add_edge",
                "episode",
                "has_motor_decision_option",
                "program",
            ],
            ["set_attr", "episode", "program_decision_seq", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "episode", "decision_request_epoch", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "episode", "decision_armed", 1.0],
            ["set_attr", "episode", "default_program_reuse_count", T(
                Plus(P0("episode", "default_program_reuse_count"), L(1.0))
            )],
        ],
    }


def async_close_background_plan_rule():
    """Atomic publication: a background build that completes becomes the new
    default (superseding the old one) without arming a decision — the action
    for this request was already served by System 1.  The program earns
    receipts the first time the release rule serves it; internalized_epoch
    is stamped now so the trust gate and the internalize rule both see it.
    """
    available = available_models()
    return {
        "name": "emp_async_close_background_plan",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": 3,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_active_embodied_motor_program", "plan"],
            ["episode", "resumes_embodied_motor_program", "plan"],
        ],
        "where": And(
            async_synthesis_enabled(),
            Eq(A("plan", "status"), L("building")),
            Eq(P0("plan", "synthesis_yield_required"), L(0.0)),
            # The action was already served this request; publish quietly.
            Eq(
                P0("episode", "program_decision_seq"),
                P0("episode", "program_request_seq"),
            ),
            Not(Exists(
                available,
                "candidate",
                Lt(
                    Plus(
                        program_cost("plan", "candidate"),
                        P0("policy", "minimum_composition_improvement"),
                    ),
                    program_cost("plan"),
                ),
            )),
        ),
        "effects": [
            ["set_attr", "plan", "status", "ready"],
            ["set_attr", "plan", "available", 0.0],
            ["set_attr", "plan", "async_published", 1.0],
            ["set_attr", "plan", "grounded_value", T(
                Minus(L(0.0), program_cost("plan"))
            )],
            ["set_attr", "plan", "default_value", T(
                Minus(L(0.0), program_cost("plan"))
            )],
            ["set_attr", "plan", "learned_value", T(
                Minus(L(0.0), program_cost("plan"))
            )],
            ["set_attr", "plan", "internalized_epoch", T(
                P0("episode", "program_request_seq")
            )],
            [
                "del_edge",
                "episode",
                "has_active_embodied_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "episode",
                "resumes_embodied_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "episode",
                "has_default_embodied_motor_program",
                "plan",
            ],
            ["set_attr", "episode", "default_program_reuse_count", 0.0],
        ],
    }


# ---------------------------------------------------------------------------
# THE MOTOR PROGRAM INDEX — BY TYPE AND SHAPE
#
# A motor program is a program, and everything else in this tree is indexed by
# type and shape: a ShapeSignature codebook, `sd_decode`/`sd_recognize`/
# `TransformDecode`/`sd_mint_quantum`, re-armed by `codebook_epoch`.  The motor
# path was the faculty that did not use it.  Its program was graph EDGES
# (`program -includes_embodied_effector_model-> model`) produced by an opaque
# search, so it could not be recognised, transformed or minted — the sd loop
# had nothing to hold.
#
# What a motor program's SHAPE is, here: one relation per member, whose
# PREDICATE is the member's actuator GROUP and whose single argument is the
# member's integer command ordinal.
#
#     [["actuator_group_2", 17], ["actuator_group_4", 33], ...]
#
# The predicate is the TYPE and the relation set is the SHAPE, which is what
# makes the index scope naturally: a program that touches one group is a
# one-relation shape (a program FOR a limb), and a program over several groups
# has those one-group shapes as sub-structure (a program WITH a limb in it).
# Nothing about this is F-16-specific — `actuator_group` is the morphology-
# neutral vocabulary this seed already owns.
#
# The command ordinal is coerced to a genuine integer (`IDiv(x, 1)`) because
# the frame invariant this tree runs on is "in-frame is INTEGER": a coordinate
# slot that stays a Float makes `coord_ints` return None and rung 2/3
# (TransformDecode / DimInfer) silently skip the part.  As an integer, "the
# same program one command step along" is the rung-1 delta the ladder already
# reads for free.
#
# WHERE THIS RUNS.  Behind the action, never in it.  Indexing is a
# `soft_realtime` plasticity rule over a program that has ALREADY flown and
# earned receipts; the epoch bump is the re-arm signal, exactly as
# `vq_grow_quantum` does it for vision and `grow_part_library` does it for
# shapes.  It costs the hard-realtime composer nothing and gates no action.
# ---------------------------------------------------------------------------

MOTOR_PROGRAM_CODEBOOK_TYPE = "EmbodiedMotorProgramShape"


def motor_program_member_relation(member="sig_member"):
    """One relation of a motor program's shape: (actuator group, command).

    `IDiv(x, 1)` is the integer coercion, not a division: attrs arrive as
    Floats and a Float coordinate is invisible to the transform ladder.
    """
    return Vec(
        StringConcat(
            L("actuator_group_"),
            ToJsonString(IDiv(P0(member, "actuator_group"), L(1))),
        ),
        IDiv(P0(member, "ordinal"), L(1)),
    )


def motor_program_signature(program="program"):
    """The program's relation system — the thing the codebook is indexed by."""
    return MapList(
        Neighbours(program, "includes_embodied_effector_model"),
        "sig_member",
        motor_program_member_relation("sig_member"),
    )


def motor_program_shape_name(program="program"):
    """A MECHANICAL identity, not a judgement of novelty.

    The humanoid twin states the contract this follows: "name is only a
    mechanical identity; novelty is decided by ShapeDecode."  A name built by
    hashing the signature would make duplicate detection a host string
    comparison and put the decision back in the wrong place.
    """
    return StringConcat(
        L("emp_program_"),
        ToJsonString(IDiv(P0(program, "internalized_epoch"), L(1))),
        L("_"),
        ToJsonString(IDiv(P0(program, "member_count"), L(1))),
    )


def signature_internalized_program_rule():
    """Stamp a flown program's shape onto it, once, after it has receipts."""
    return {
        "name": "emp_signature_internalized_program",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A motor program's SHAPE is one relation per member, "
        "predicate = actuator group (the type), argument = integer command "
        "ordinal. Stamped behind the action on a program that has already "
        "flown, so the hard-realtime composer is untouched.",
        "match": [
            ["episode", "has_default_embodied_motor_program", "program"],
        ],
        "where": And(
            Not(Lt(P0("program", "internalized_epoch"), L(0.0))),
            Not(Gt(P0("program", "shape_signature_stamped"), L(0.5))),
            Gt(Count(Neighbours("program", "includes_embodied_effector_model")),
               L(0.0)),
        ),
        "effects": [
            ["set_attr", "program", "signature", T(
                motor_program_signature("program")
            )],
            ["set_attr", "program", "dim_types", T(
                Vec(L("pred"), L("coord:command"))
            )],
            ["set_attr", "program", "shape_signature_stamped", 1.0],
        ],
    }


def grow_motor_program_shape_rule():
    """Grow the motor codebook and bump its epoch — the mint, off the action.

    This is `vq_grow_quantum` for the motor path: a program that has flown and
    been stamped becomes a codebook entry, and the epoch bump is the signal
    that what was unrecognisable a moment ago may be recognisable now.  The
    epoch is deliberately its OWN (`motor_codebook_epoch`) rather than the
    shared `codebook_epoch`, so growing the motor codebook does not re-arm
    every held Observation in the agent.
    """
    return {
        "name": "emp_grow_motor_program_shape",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Mint the flown program as a codebook entry indexed by "
        "type and shape, and bump the motor codebook epoch.",
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_default_embodied_motor_program", "program"],
        ],
        "where": And(
            Gt(P0("program", "shape_signature_stamped"), L(0.5)),
            Eq(
                Count(Neighbours("program", "has_motor_program_shape")),
                L(0.0),
            ),
        ),
        "effects": [
            ["add_node", "shape", MOTOR_PROGRAM_CODEBOOK_TYPE, {
                "name": T(motor_program_shape_name("program")),
                "signature": T(motor_program_signature("program")),
                "dim_types": T(Vec(L("pred"), L("coord:command"))),
                "kind": "motor_program",
                "faculty": "embodied_motor_program",
                "library_slot": T(P0("program", "internalized_epoch")),
                "member_count": T(P0("program", "member_count")),
                "status": "library",
            }],
            [
                "add_edge", "agent",
                "has_embodied_motor_program_shape_library", "shape",
            ],
            ["add_edge", "program", "has_motor_program_shape", "shape"],
            ["set_attr", "agent", "motor_codebook_epoch", T(
                Plus(P0("agent", "motor_codebook_epoch"), L(1.0))
            )],
        ],
    }


# ---------------------------------------------------------------------------
# CONDENSATION: the order-1 -> order-0 collapse.
#
# Training is the existence proof that order-0 content is overwhelmingly
# LEARNED.  An author-only reflex codebook is therefore the wrong shape, in
# exactly the way an author-only motor codebook was until `emp_grow_motor_
# program_shape` began minting shapes from flight.  `motor_reflex_buy_time` is
# the seeded prior -- the small innate set.  These four rules are how the rest
# of the reflex index GROWS, and how it DECAYS.
#
# WHAT IS INDEXED.  Not the observation and not the program: the SHAPE OF THE
# RESIDUAL.  A reflex is `surprise -> motor program`, and the surprise is what
# prediction failed to cover, quantised.  `relative_normal_load_error` is a
# ratio (cross-frame, correctly a Float); `IDiv` against a declared quantum is
# the in-frame integer coordinate that makes it a SHAPE rather than a number.
# This is the join between CM/CP's residual channel and CT's motor codebook.
#
# THE MEASURABLE FORM, exactly as specified: a surprise shape whose response
# has not varied over N encounters is a candidate for condensation; a condensed
# reflex whose outcome starts varying is a candidate for release.  Both are
# ratios over the codebook's OWN history -- `stable_run` counts consecutive
# encounters that produced the same response, and nothing else is stored.  No
# history buffer, no window, no per-encounter record.
#
# WHY RELEASE IS NOT OPTIONAL.  A trained reflex that is no longer right has to
# be untrainable, or the agent is welded to its own history.  A condensed
# reflex is a COLLAPSE, and collapses stay open -- the same activation /
# deactivation asymmetry as the latches.  Release is one rule and it is
# installed with the condensation, not after it.
#
# POLARITY.  Both parameters are absent-inert: `motor_surprise_shape_quantum`
# and `motor_reflex_condensation_encounters` read 0 through `P0` when unset, and
# every rule requires them strictly positive.  An agent that declares neither
# indexes nothing and condenses nothing, which is the current behaviour.
# ---------------------------------------------------------------------------

SURPRISE_SHAPE_TYPE = "EmbodiedSurpriseShape"


def motor_program_response_shape(program="program"):
    """The response's identity for condensation: its SHAPE, not its name.

    MEASURED, and the reason this is not `motor_program_shape_name`: that name
    is `emp_program_<internalized_epoch>_<member_count>`, which is a SERIAL
    NUMBER -- a fresh program instance with an identical relation system gets a
    different one.  Comparing it made every re-encounter look like a varied
    response, so every stable run reset to 1 and nothing could ever condense
    (measured: 16 shapes, every run 1, reflex epoch 0).  The name is the right
    key for the motor CODEBOOK, where instance identity is the point; it is the
    wrong key here, where the question is whether the same THING happened again.

    So the comparison is over `motor_program_signature` -- the relation system
    itself, serialised.  Matching shapes, not numbers.

    KNOWN RESIDUAL: `MapList` preserves neighbour order, so two programs with
    the same relation system enumerated in a different order serialise
    differently and read as varied.  That makes this conservative -- it can
    miss a condensation, never invent one.
    """
    return ToJsonString(motor_program_signature(program))


def surprise_shape_ordinal(program="program", policy="policy"):
    """The residual's shape: a LOG-scale bucket, quantised to an integer.

    MEASURED, and the reason this is not a linear quantisation:
    `relative_normal_load_error` runs 0.21 to 1_591_707 over one nominal
    episode -- seven orders of magnitude, because it divides by a predicted
    load that goes through zero.  Bucketing that linearly gives one shape per
    encounter and an index that has learned nothing; it is matching a NUMBER.
    The log collapses the whole range into ~15 buckets that recur, which is
    what makes it a SHAPE.

    The invariant holds and is worth stating, because this is the case it was
    written for: the log is the CROSS-FRAME map (a base is a dimension --
    `scale2`), the ratio it consumes is correctly a Float, and the integer `k`
    it produces is the in-frame coordinate.  `+1` keeps it defined and
    non-negative at zero error.
    """
    return IDiv(
        Log(Plus(Abs(P0(program, "relative_normal_load_error")), L(1.0))),
        P0(policy, "motor_surprise_shape_quantum"),
    )


def _surprise_encounter_match():
    return [
        ["agent", "has_embodied_motor_program_policy", "policy"],
        ["agent", "has_embodied_motor_program_episode", "episode"],
        ["episode", "has_embodied_motor_program_trial", "trial"],
        ["trial", "enacts_embodied_motor_program", "program"],
        ["trial", "has_embodied_motor_program_outcome", "outcome"],
    ]


def _surprise_encounter_guard():
    """A verified receipt for THIS action, and the faculty declared on.

    The `program_request_seq` clause is what makes the encounter chain bind
    ONCE.  Without it every past trial of the episode binds, and MEASURED, that
    is not harmless: when a new residual bucket first appears, every one of
    those bindings passes the mint rule's `Not(Exists)` against the same
    pre-pass graph and the index gains three or four entries for one shape
    (seen in flight at ordinals 1, 12 and 14, and reproduced in the bench).
    Duplicates cannot be cleaned up afterwards either -- they share an ordinal,
    so the recur rules increment all of them in lockstep and no attr ever
    separates them.  The fix has to be at the mint, and this is it: outcomes
    are stamped with the episode's `program_request_seq`, so equality selects
    the current action's outcome alone.
    """
    return And(
        Eq(P0("outcome", "receipt_verified"), L(1.0)),
        Eq(P0("outcome", "request_seq"),
           P0("episode", "program_request_seq")),
        Gt(P0("policy", "motor_surprise_shape_quantum"), L(0.0)),
    )


def index_surprise_shape_rule():
    """Mint the residual's shape the first time it is seen.

    Find-or-mint by ORDINAL over the agent's own library -- O(library) from the
    encounter's side, not the O(n^2) pairwise alignment that kept
    `recognize_duplicate_motor_program_shape_rule` out of the tree.  Exact
    recognition is rung 0 of the ladder and costs no `ShapeDecode`.
    """
    known = Neighbours("agent", "has_embodied_surprise_shape_library")
    return {
        "name": "emp_index_surprise_shape",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Mint the quantised residual as a surprise shape, carrying "
        "the response it produced, the first time that shape is seen.",
        "match": _surprise_encounter_match(),
        "where": And(
            _surprise_encounter_guard(),
            Not(Exists(
                known, "seen",
                Eq(IDiv(P0("seen", "ordinal"), L(1)),
                   surprise_shape_ordinal("program", "policy")),
            )),
        ),
        "effects": [
            ["add_node", "surprise", SURPRISE_SHAPE_TYPE, {
                "ordinal": T(surprise_shape_ordinal("program", "policy")),
                "response_shape": T(motor_program_response_shape("program")),
                "stable_run": 1.0,
                "last_seen_seq": T(P0("outcome", "request_seq")),
                "order": 1.0,
                "condensed": 0.0,
                "status": "candidate",
                "kind": "surprise_shape",
                "faculty": "embodied_motor_program",
            }],
            [
                "add_edge", "agent",
                "has_embodied_surprise_shape_library", "surprise",
            ],
            # A NOVEL SHAPE IS A CHANGE IN DYNAMICS, and this stamp is how the
            # recalibration latch hears about it.  The mint already decides
            # "this residual is unlike anything held"; nothing else needs to
            # be computed, thresholded or debounced for that to be a trigger.
            ["set_attr", "episode", "surprise_shape_minted_seq", T(
                P0("outcome", "request_seq")
            )],
            # A fresh shape has a run of one, which is what makes the
            # adaptation rate 1.0 for it: nothing is known, so believe what
            # was just seen.
            ["set_attr", "episode", "current_stable_run", 1.0],
            # THE REGIME THE EPISODE IS IN.  Read by the model fork and by the
            # composer's eligibility gate; publishing it here is what makes a
            # brand-new regime forkable on the very action it appears.
            ["set_attr", "episode", "current_surprise_ordinal", T(
                surprise_shape_ordinal("program", "policy")
            )],
        ],
    }


def _surprise_recur_guard(same_response: bool):
    """A re-encounter of a held surprise shape, once per action.

    `last_seen_seq` is the same seq-guard idiom as `last_learning_seq`: the
    rule fires once per verified outcome per shape, never once per fixpoint
    pass.  Without it `stable_run` would count settle ticks, not encounters.
    """
    # `A`, NOT `P0`.  `P0` is `Plus(Attr, 0.0)` -- the first-class-absence
    # idiom for NUMBERS, and adding 0.0 to a String can never compare equal to
    # a String.  Measured: with `P0` here the recur rules bind correctly
    # (`last_seen_seq` advances every action) but ALWAYS take the vary branch,
    # even when the program is byte-identical, so `stable_run` never leaves 1.
    # Absence is still handled, and with the right polarity: an unset
    # `response_shape` is not equal to anything, so it reads as varied and
    # restarts the run rather than silently extending it.
    names_match = Eq(
        A("surprise", "response_shape"),
        motor_program_response_shape("program"),
    )
    return And(
        _surprise_encounter_guard(),
        # `IDiv(x, 1)` is the integer coercion, not a division -- the same
        # idiom `motor_program_member_relation` documents.  Attrs read back as
        # Floats, `surprise_shape_ordinal` computes an Int, and `Eq` across
        # those two types is FALSE.  Measured: without this the index mints
        # exactly one shape per run and never re-encounters it (run=1, epoch=0).
        Eq(IDiv(P0("surprise", "ordinal"), L(1)),
           surprise_shape_ordinal("program", "policy")),
        Gt(P0("outcome", "request_seq"), P0("surprise", "last_seen_seq")),
        names_match if same_response else Not(names_match),
    )


def count_stable_surprise_response_rule():
    """The response did not vary: lengthen the run.

    This is the whole of "has not varied over N encounters" -- one integer,
    incremented.  The alternative (store the last N responses and compare) is
    strictly more state for strictly the same answer.
    """
    return {
        "name": "emp_count_stable_surprise_response",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A held surprise shape produced the same response again: "
        "extend its stable run by one encounter.",
        "match": _surprise_encounter_match() + [
            ["agent", "has_embodied_surprise_shape_library", "surprise"],
        ],
        "where": _surprise_recur_guard(same_response=True),
        "effects": [
            ["set_attr", "surprise", "stable_run", T(
                Plus(P0("surprise", "stable_run"), L(1.0))
            )],
            ["set_attr", "episode", "current_stable_run", T(
                Plus(P0("surprise", "stable_run"), L(1.0))
            )],
            ["set_attr", "episode", "current_surprise_ordinal", T(
                IDiv(P0("surprise", "ordinal"), L(1))
            )],
            ["set_attr", "surprise", "last_seen_seq", T(
                P0("outcome", "request_seq")
            )],
        ],
    }


def vary_surprise_response_rule():
    """The response varied: the run is broken, and the count restarts at one.

    Restart at 1 rather than 0 because THIS encounter is the first of the new
    run.  Releasing a condensed reflex is not done here -- breaking the run is
    the observation, releasing is the decision, and they are separate rules so
    the release is visible in its own right.
    """
    return {
        "name": "emp_vary_surprise_response",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A held surprise shape produced a different response: "
        "record the new response and restart the stable run.",
        "match": _surprise_encounter_match() + [
            ["agent", "has_embodied_surprise_shape_library", "surprise"],
        ],
        "where": _surprise_recur_guard(same_response=False),
        "effects": [
            ["set_attr", "surprise", "response_shape", T(
                motor_program_response_shape("program")
            )],
            ["set_attr", "surprise", "stable_run", 1.0],
            # The response varied, so the run restarts and the rate goes back
            # to 1.0.  What used to work here no longer does.
            ["set_attr", "episode", "current_stable_run", 1.0],
            ["set_attr", "episode", "current_surprise_ordinal", T(
                IDiv(P0("surprise", "ordinal"), L(1))
            )],
            ["set_attr", "surprise", "last_seen_seq", T(
                P0("outcome", "request_seq")
            )],
        ],
    }


def condense_surprise_reflex_rule():
    """Order 1 -> order 0.  The response stopped needing to be computed.

    Nothing about the response changes: the same program, reached without
    deliberation.  That is what makes this a collapse rather than a new
    faculty -- and why a reflex has no parameters and cannot be mis-fit.
    """
    return {
        "name": "emp_condense_surprise_reflex",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A surprise shape whose response has not varied over N "
        "encounters condenses to order 0.",
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_surprise_shape_library", "surprise"],
        ],
        "where": And(
            Gt(P0("policy", "motor_reflex_condensation_encounters"), L(0.0)),
            Not(Lt(
                P0("surprise", "stable_run"),
                P0("policy", "motor_reflex_condensation_encounters"),
            )),
            Not(Gt(P0("surprise", "condensed"), L(0.5))),
        ),
        "effects": [
            ["set_attr", "surprise", "condensed", 1.0],
            ["set_attr", "surprise", "order", 0.0],
            ["set_attr", "surprise", "status", "reflex"],
            ["set_attr", "agent", "motor_reflex_epoch", T(
                Plus(P0("agent", "motor_reflex_epoch"), L(1.0))
            )],
        ],
    }


def release_condensed_reflex_rule():
    """Order 0 -> order 1.  The collapse stays open.

    A condensed reflex whose outcome has started varying goes back to being
    computed.  Without this the agent is welded to its own history: every
    reflex it ever earned would outlive the world that earned it.
    """
    return {
        "name": "emp_release_condensed_reflex",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A condensed reflex whose response has started varying is "
        "released back to order 1.",
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_surprise_shape_library", "surprise"],
        ],
        "where": And(
            Gt(P0("policy", "motor_reflex_condensation_encounters"), L(0.0)),
            Gt(P0("surprise", "condensed"), L(0.5)),
            Lt(
                P0("surprise", "stable_run"),
                P0("policy", "motor_reflex_condensation_encounters"),
            ),
        ),
        "effects": [
            ["set_attr", "surprise", "condensed", 0.0],
            ["set_attr", "surprise", "order", 1.0],
            ["set_attr", "surprise", "status", "released"],
            ["set_attr", "agent", "motor_reflex_epoch", T(
                Plus(P0("agent", "motor_reflex_epoch"), L(1.0))
            )],
        ],
    }


def arm_condensed_reflex_rule():
    """The stimulus side of order 0: a KNOWN surprise just happened.

    This is what `motor_reflex_armed` was always for.  It shipped inert
    because nothing set it -- there was no index of surprise shapes to set it
    FROM.  Now there is, and the arming condition is exactly the one the design
    calls for: the residual this action fell into a bucket the agent has
    already condensed, so the response is known without deliberating.

    Arming is a RULE, in the settle.  Firing is the ENGINE, at the top of the
    next cycle, before any rule runs.  The one-action gap between them is
    honest and is the point: the reflex acts at the START of the next action on
    what the last one told it, rather than waiting for a fixpoint it exists to
    pre-empt.
    """
    return {
        "name": "emp_arm_condensed_reflex",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A condensed surprise shape recurred this action: arm the "
        "order-0 reflex.",
        "match": _surprise_encounter_match() + [
            ["agent", "has_embodied_surprise_shape_library", "surprise"],
        ],
        "where": And(
            _surprise_encounter_guard(),
            Eq(IDiv(P0("surprise", "ordinal"), L(1)),
               surprise_shape_ordinal("program", "policy")),
            Gt(P0("surprise", "condensed"), L(0.5)),
        ),
        "effects": [
            ["set_attr", "episode", "motor_reflex_armed", 1.0],
            ["set_attr", "episode", "motor_reflex_armed_seq", T(
                P0("outcome", "request_seq")
            )],
        ],
    }


def enact_motor_reflex_buy_time_rule():
    """The response side of order 0 -- a RULE, not a host callback.

    The engine does not know what `motor_reflex_buy_time` MEANS.  It knows the
    stimulus held and stamps `fire_count`; the meaning is here, in the graph,
    where it can be measured, ablated and changed without touching the runtime.
    That is the whole reason the response had to stop being a Python callable:
    a callable is invisible to the agent, and an order-0 response that the
    agent cannot see is one it can never learn to change.

    What it does is DISARM and COUNT.  A reflex buys time; it does not solve
    the problem.  The named gap that remains is the consumer -- nothing yet
    reads `motor_reflex_held_seq` to actually defer a deliberation, because
    `program_cost` still cannot express "select because it extends the margin".
    Firing is real and measured; spending the time it buys is the next rung.
    """
    return {
        "name": "emp_enact_motor_reflex_buy_time",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "hard_realtime",
        "batch": False,
        "comment": "A fired order-0 reflex is enacted and disarmed by a rule "
        "reading the engine's own firing stamp.",
        "match": [
            ["agent", "has_reflex", "reflex"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
        ],
        "where": And(
            Eq(A("reflex", "name"), L("motor_reflex_buy_time")),
            Gt(P0("reflex", "fire_count"),
               P0("episode", "motor_reflex_handled_count")),
        ),
        "effects": [
            ["set_attr", "episode", "motor_reflex_handled_count", T(
                P0("reflex", "fire_count")
            )],
            ["set_attr", "episode", "motor_reflex_held_seq", T(
                P0("episode", "program_request_seq")
            )],
            # Disarm.  The arm rule re-arms on the next condensed recurrence,
            # so the reflex tracks the surprise rather than latching on.
            ["set_attr", "episode", "motor_reflex_armed", 0.0],
            ["set_attr", "agent", "motor_reflex_enactments", T(
                Plus(P0("agent", "motor_reflex_enactments"), L(1.0))
            )],
        ],
    }


# MEASURED, AND NOT INSTALLED: the collapse rule below is correct and far too
# expensive to run here, and the reason is architectural rather than a constant
# needing tuning.
#
# It matches library x library, so the engine enumerates O(n^2) bindings every
# fixpoint pass, and each surviving binding evaluates two `ShapeDecode`s whose
# `load_parts` walks EVERY node of the codebook type — the collapsed duplicates
# included, since they keep their type.  Measured on the three fault scenarios:
# no episode completed in 838 s against a 69 s/episode baseline, i.e. >11x, and
# still climbing.
#
# The honest reading is that "behind the action" is not yet a thing this tree
# can do for the motor path.  There is one `run_rules` fixpoint per action, so a
# `soft_realtime` plasticity rule is not off the action's critical path — it is
# on it, exactly as the async-synthesis note in `jabberwock_jsbsim_f16_paper_
# replication.py` already records ("a single-threaded rule engine runs the
# background build's passes inside the action's own settle ticks").  CS assumed
# the epoch discipline was enough; it is enough for SHAPES because
# `grow_part_library` runs from outside the fixpoint, and there is no equivalent
# outside caller here.
#
# So the alignment step stays measured OFFLINE for now (probe2/codebook.py reads
# the same collapse out of the finished graph) and the growth half — which is
# O(1) per internalization — is what ships.  Installing this needs either a
# once-per-entry check flag on the `sd_dim_check_mark` pattern AND a scoped
# `load_parts`, or a caller outside the action.  Both are a separate change.


def exact_motor_program_shape(entry, canonical, field):
    """Decode one codebook entry against exactly one other, by shape."""
    return {
        "type": "ShapeDecode",
        "goal": A(entry, "signature"),
        "codebook_type": MOTOR_PROGRAM_CODEBOOK_TYPE,
        "codebook_scope": SetT(A(canonical, "name")),
        "beam": 1,
        "max_steps": 1,
        "cand_k": 1,
        "field": field,
        "wild_objects": False,
    }


def recognize_duplicate_motor_program_shape_rule():
    """Collapse a re-composed program onto a held one BY SHAPE, not by name.

    This is the alignment step, and it is the whole point of the index: the
    composer re-derives the same program many times over a flight, and without
    a shape there is no way to notice.  `ShapeDecode` — not a host tuple
    comparison — decides that an entry is already covered by an earlier one.
    Running here, off the action, is what makes the NEXT encounter cheap; it
    gates nothing now.
    """
    return {
        "name": "emp_recognize_duplicate_motor_program_shape",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "Treat motor programs as relation systems. ShapeDecode "
        "recognizes a freshly minted program already covered by an earlier "
        "codebook entry of the same type and shape.",
        "match": [
            ["agent", "has_embodied_motor_program_shape_library", "entry"],
            ["agent", "has_embodied_motor_program_shape_library", "canonical"],
        ],
        "where": And(
            Not(Eq(V("entry"), V("canonical"))),
            Eq(A("entry", "status"), L("library")),
            Eq(A("canonical", "status"), L("library")),
            Lt(
                P0("canonical", "library_slot"),
                P0("entry", "library_slot"),
            ),
            Eq(
                Count(exact_motor_program_shape(
                    "entry", "canonical", "residual"
                )),
                L(0.0),
            ),
            Eq(
                exact_motor_program_shape(
                    "entry", "canonical", "covered_count"
                ),
                Count(A("entry", "signature")),
            ),
        ),
        "effects": [
            ["set_attr", "entry", "status", "shape_duplicate"],
            ["set_attr", "entry", "shape_duplicate", 1.0],
            [
                "del_edge", "agent",
                "has_embodied_motor_program_shape_library", "entry",
            ],
            [
                "add_edge", "agent",
                "has_duplicate_embodied_motor_program_shape", "entry",
            ],
            [
                "add_edge", "entry",
                "is_shape_duplicate_of_embodied_motor_program", "canonical",
            ],
        ],
    }


def internalize_synthesized_program_rule():
    return {
        "name": "emp_internalize_receipt_grounded_program_default",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "enacts_embodied_motor_program", "program"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("program", "source"), L("analysis_by_synthesis")),
            Eq(A("trial", "status"), L("learned")),
            Lt(P0("program", "internalized_epoch"), L(0.0)),
            Eq(
                P0("program", "last_learning_seq"),
                P0("outcome", "request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "program", "internalized_epoch", T(
                P0("outcome", "request_seq")
            )],
            [
                "add_edge",
                "episode",
                "has_default_embodied_motor_program",
                "program",
            ],
            ["set_attr", "episode", "default_program_reuse_count", 0.0],
        ],
    }


def retire_superseded_program_default_rule():
    return {
        "name": "emp_retire_superseded_program_default",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": True,
        "match": [
            [
                "episode",
                "has_default_embodied_motor_program",
                "old",
            ],
            [
                "episode",
                "has_default_embodied_motor_program",
                "fresh",
            ],
        ],
        "where": And(
            Not(Eq(V("old"), V("fresh"))),
            Lt(
                P0("old", "internalized_epoch"),
                P0("fresh", "internalized_epoch"),
            ),
        ),
        "effects": [[
            "del_edge",
            "episode",
            "has_default_embodied_motor_program",
            "old",
        ]],
    }


def native_composition_enabled():
    """Opt-in flag for the native MotorCompose search (absent -> term-tree).

    The Rust term (runners/dsl/src/motor_compose.rs) IS the search
    composer's selection — same open/expand/close semantics, precomputed
    prediction matrix, native arithmetic — so unlike render-first it is
    full search fidelity and needs no regime suspension.
    """
    return Gt(P0("policy", "native_composition_enabled"), L(0.5))


def motor_compose_member(episode="episode", policy="policy",
                         candidate="candidate"):
    """The native membership term: 1 iff candidate is in the composed
    program for (episode, policy)."""
    return {
        "type": "MotorCompose",
        "episode": V(episode),
        "policy": V(policy),
        "candidate": V(candidate),
    }


def render_first_enabled():
    """Opt-in flag for the render-first System-2 path (absent -> search).

    A consumer regime can SUSPEND rendering per episode
    (render_first_suspended attr): render proposes only while its linear
    model of the plant is trusted; a fault/escalated regime falls back to
    the search composer, whose plan-aware costs handle cross-group
    coupling (measured: render-composed programs under the rudder-jam
    regime lost the v4 altitude margin — min altitude 2,025 ft -> 4 ft).
    """
    return And(
        Gt(P0("policy", "render_first_composition_enabled"), L(0.5)),
        Not(Gt(P0("episode", "render_first_suspended"), L(0.5))),
    )


def future_manifold_enabled():
    return Gt(P0("policy", "future_manifold_enabled"), L(0.5))


def future_manifold_bounds_active():
    return And(
        future_manifold_enabled(),
        Gt(P0("episode", "manifold_bounds_ready"), L(0.5)),
    )


def future_manifold_supported():
    """The treatment is ordinary interpreted search only; unsupported paths fail closed."""
    return And(
        future_manifold_bounds_active(),
        Not(native_composition_enabled()),
        Not(render_first_enabled()),
        Not(Gt(P0("policy", "parallel_factorized_composition_enabled"), L(0.5))),
    )


def future_manifold_establishing():
    return And(
        future_manifold_enabled(),
        Not(Gt(P0("episode", "manifold_bounds_ready"), L(0.5))),
        Not(Gt(P0("episode", "program_request_seq"), P0("policy", "future_manifold_establish_until_seq"))),
    )


def ordinary_composer_allowed():
    return Or(Not(future_manifold_enabled()), future_manifold_establishing(), future_manifold_supported())


def native_future_projection(source="plan", addition=None, field="loss"):
    term = {"type": "FutureManifoldProjection", "episode": V("episode"), "policy": V("policy"), "source": V(source), "field": field}
    if addition is not None:
        term["addition"] = V(addition)
    return term


def manifold_loss(source="plan", addition=None):
    return native_future_projection(source, addition, "loss")


def manifold_loss_legacy(source="plan", addition=None):
    projected = manifold_projection_loss_at_decision(source, addition)
    terms = []
    for key in COMPONENTS:
        predicted = Abs(Minus(P0("episode", f"target_{key}"), prediction(source, key, addition)))
        terms.append(If(And(Gt(P0("policy", f"{key}_weight"), L(0.0)), Gt(predicted, P0("episode", f"manifold_bound_{key}"))), L(1.0), L(0.0)))
    immediate = Plus(*terms)
    return If(And(future_manifold_supported(), _projection_supported(source, addition)), projected, immediate)


def manifold_protected_count():
    return Plus(*(If(Gt(P0("policy", f"{key}_weight"), L(0.0)), L(1.0), L(0.0)) for key in COMPONENTS))


def manifold_information_loss(source="plan", addition=None):
    return native_future_projection(source, addition, "information_loss")
    lost = manifold_loss(source, addition)
    retained = Minus(manifold_protected_count(), lost)
    # Complete topology on protected component cells: every lost cell removes
    # its incident unordered links, counted as C(n,2)-C(r,2).
    return Plus(lost, Minus(
        Div(Times(manifold_protected_count(), Minus(manifold_protected_count(), L(1.0))), L(2.0)),
        Div(Times(retained, Minus(retained, L(1.0))), L(2.0)),
    ))


def manifold_retained_width(source="plan", addition=None):
    return native_future_projection(source, addition, "retained_width")
    terms = []
    for key in COMPONENTS:
        terms.append(If(And(Gt(P0("policy", f"{key}_weight"), L(0.0)), Not(manifold_projection_axis_lost(source, key, addition))), L(1.0), L(0.0)))
    return Plus(*terms)


def manifold_filter(source, var="candidate", addition=None):
    return Or(
        Not(future_manifold_supported()),
        And(
            Gt(native_future_projection(source, addition, "support"), L(0.5)),
            Gt(native_future_projection(source, addition, "resolved"), L(0.5)),
            Eq(manifold_loss(source, addition), L(0.0)),
        ),
    )


def manifold_reuse_allowed(source="program"):
    """A held default must earn a fresh certificate in the current state.

    Establishment programs predate the learned bounds, and their old audit is
    not authority to cross the risk gate later.  Unsupported, unresolved, or
    lossy defaults fall through to fresh composition, where all complete
    alternatives can be compared and a forced minimum-loss transition can be
    recorded if necessary.
    """
    return Or(
        Not(future_manifold_bounds_active()),
        And(
            Gt(native_future_projection(source, None, "support"), L(0.5)),
            Gt(native_future_projection(source, None, "resolved"), L(0.5)),
            Eq(manifold_loss(source), L(0.0)),
        ),
    )


def manifold_min_loss(source, candidates):
    return MinOver(candidates, "candidate", manifold_loss(source, "candidate"), L(0.0))


def future_manifold_audit_effects(source):
    """Stamp the graph-only risk report on every program release path."""
    # `If` is lazy in the evaluator.  Disabled programs receive inert audit
    # defaults without invoking projection, preserving the gate-off identity
    # all the way through publication rather than only during selection.
    gated = lambda value, default=0.0: If(
        future_manifold_enabled(), value, L(default)
    )
    support = gated(native_future_projection(source, None, "support"))
    supported = Gt(support, L(0.5))
    resolved = gated(native_future_projection(source, None, "resolved"))
    loss = gated(manifold_loss(source))
    horizon = gated(manifold_projection_horizon(source))
    termination_code = gated(native_future_projection(source, None, "termination_code"))
    epistemic_probe = Or(
        Eq(A(source, "source"), L("factorized_calibration")),
        Eq(A(source, "source"), L("graph_requested_flow_excitation")),
    )
    return [
        ["set_attr", source, "manifold_retained_width", T(gated(manifold_retained_width(source)))],
        ["set_attr", source, "manifold_information_loss", T(gated(manifold_information_loss(source)))],
        ["set_attr", source, "manifold_forced_transition", T(If(Gt(loss, L(0.0)), L(1.0), L(0.0)))],
        ["set_attr", source, "manifold_horizon", T(horizon)],
        ["set_attr", source, "manifold_projection_resolved", T(resolved)],
        ["set_attr", source, "manifold_projection_termination_code", T(termination_code)],
        ["set_attr", source, "manifold_projection_reason", T(If(
            Not(future_manifold_enabled()),
            L("disabled"),
            If(
            Not(supported),
            L("support_unavailable"),
            If(
                Gt(loss, L(0.0)),
                L("earliest_decisive_loss"),
                If(
                    Eq(termination_code, L(6.0)),
                    L("certified_horizon"),
                If(
                    And(Gt(resolved, L(0.5)), epistemic_probe),
                    L("epistemic_action_boundary"),
                    If(Gt(resolved, L(0.5)), L("path_transition_fixed_point"), L("budget_exhausted_unresolved")),
                ),
                ),
            ),
            ),
        ))],
        ["set_attr", source, "manifold_projection_horizon", T(horizon)],
        ["set_attr", source, "manifold_projection_support", T(support)],
        ["set_attr", source, "manifold_projection_budget", T(gated(L(float(FUTURE_MANIFOLD_PROJECTION_BUDGET))))],
        ["set_attr", source, "manifold_physical_horizon", T(gated(P0("policy", "future_manifold_physical_horizon")))],
        ["set_attr", source, "manifold_projection_phase", T(If(future_manifold_establishing(), L("establishing"), L("post_establishment")))],
        ["set_attr", source, "manifold_phase", T(If(future_manifold_establishing(), L("establishing"), L("post_establishment")))],
        ["set_attr", source, "projection_policy", T(If(
            epistemic_probe, L("single_action_probe"), L("hold_program")
        ))],
        ["set_attr", source, "projection_target_policy", "hold_current_target"],
        ["set_attr", source, "projection_time_bound", f"adaptive_up_to_{FUTURE_MANIFOLD_PROJECTION_BUDGET}_action_slices"],
        # The fields below are an audit contract, not authority.  They remain
        # inert when the manifold gate is disabled and let runtime agents
        # report sparse anchors/refinement without host-side interpretation.
        ["set_attr", source, "manifold_anchor_schedule", T(If(
            future_manifold_enabled(),
            L("dense_1_2_3_loglog_far"),
            L("disabled"),
        ))],
        ["set_attr", source, "manifold_anchor_count", T(gated(
            native_future_projection(source, None, "anchor_count")
        ))],
        ["set_attr", source, "manifold_refinement_count", T(gated(
            native_future_projection(source, None, "refinement_count")
        ))],
        ["set_attr", source, "manifold_certified_interval_count", T(gated(
            native_future_projection(source, None, "certified_interval_count")
        ))],
        ["set_attr", source, "manifold_ambiguous_interval_count", T(gated(
            native_future_projection(source, None, "ambiguous_interval_count")
        ))],
        ["set_attr", source, "manifold_max_enclosure_width", T(gated(
            native_future_projection(source, None, "max_enclosure_width")
        ))],
        ["set_attr", source, "manifold_max_shape_order", T(gated(
            native_future_projection(source, None, "max_shape_order")
        ))],
        ["set_attr", source, "manifold_earliest_decisive_tick", T(gated(
            native_future_projection(source, None, "earliest_decisive_tick")
        ))],
        ["set_attr", source, "manifold_anchor_budget", T(gated(
            L(float(FUTURE_MANIFOLD_PROJECTION_BUDGET))
        ))],
        ["set_attr", source, "manifold_refinement_budget", T(gated(
            L(float(FUTURE_MANIFOLD_MAX_REFINEMENTS))
        ))],
        ["set_attr", source, "manifold_shape_order_budget", T(gated(
            L(float(FUTURE_MANIFOLD_MAX_SHAPE_ORDER))
        ))],
        *[["set_attr", source, f"manifold_retained_{key}", T(gated(If(And(Gt(P0("policy", f"{key}_weight"), L(0.0)), Not(manifold_projection_axis_lost(source, key))), L(1.0), L(0.0))))] for key in COMPONENTS],
    ]


def establish_future_manifold_rule():
    """Learn deterministic component bounds only from ready programs in-window."""
    return {
        "name": "emp_establish_future_manifold_from_ready_program",
        "area": "embodied_motor_program",
        "latency_class": "soft_realtime",
        "match": [["agent", "has_embodied_motor_program_policy", "policy"],
                  ["agent", "has_embodied_motor_program_episode", "episode"],
                  ["episode", "has_embodied_motor_program", "program"]],
        "where": And(
            future_manifold_enabled(),
            Eq(A("program", "status"), L("ready")),
            Eq(A("program", "source"), L("analysis_by_synthesis")),
            Not(Lt(P0("program", "request_seq"), P0("policy", "future_manifold_establish_from_seq"))),
            Not(Gt(P0("program", "request_seq"), P0("policy", "future_manifold_establish_until_seq"))),
        ),
        "effects": [
            *[["set_attr", "program", f"manifold_predicted_residual_{key}", T(Abs(Minus(P0("episode", f"target_{key}"), prediction("program", key))))] for key in COMPONENTS],
            *[["set_attr", "episode", f"manifold_bound_{key}", T(Max(P0("episode", f"manifold_bound_{key}"), Abs(Minus(P0("episode", f"target_{key}"), prediction("program", key)))))] for key in COMPONENTS],
            ["set_attr", "episode", "manifold_bounds_ready", T(If(Not(Lt(P0("program", "request_seq"), P0("policy", "future_manifold_establish_until_seq"))), L(1.0), P0("episode", "manifold_bounds_ready")))],
        ],
    }


def open_synthesized_program_rule():
    eligible = Filter(
        MODELS,
        "candidate",
        And(
            Gt(P0("candidate", "experience_count"), L(0.5)),
            Gt(P0("candidate", "available"), L(0.5)),
            structural_model_admissible("candidate"),
            ordinary_composer_allowed(),
        ),
    )
    supported_eligible = Filter(eligible, "candidate", Or(Not(future_manifold_supported()), _projection_supported("candidate", "candidate")))
    minimum_loss = MinOver(supported_eligible, "candidate", manifold_loss("candidate", "candidate"), L(0.0))
    shape_eligible = Filter(
        eligible, "candidate",
        Or(
            Not(future_manifold_supported()),
            And(
                _projection_supported("candidate"),
                And(_projection_supported("candidate", "candidate"), Eq(manifold_loss("candidate", "candidate"), minimum_loss)),
            ),
        ),
    )
    best = Argmin(
        shape_eligible,
        "candidate",
        singleton_cost("candidate"),
        V("episode"),
    )
    return {
        "name": "emp_abs_open_embodied_motor_program",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "primary"],
        ],
        "where": And(
            Not(render_first_enabled()),
            Not(native_composition_enabled()),
            Eq(A("episode", "program_mode"), L("synthesis")),
            # One plan in flight at a time (a no-op for the synchronous path,
            # load-bearing for asynchronous background builds).
            Not(Gt(
                Count(Neighbours(
                    "episode", "has_active_embodied_motor_program"
                )),
                L(0.0),
            )),
            Or(
                # Synchronous: this request still needs a program.
                And(
                    Eq(P0("episode", "action_ready"), L(0.0)),
                    Gt(
                        P0("episode", "program_request_seq"),
                        P0("episode", "program_decision_seq"),
                    ),
                ),
                # Asynchronous background: the action was already served by
                # the trusted default; start (at most) one build per request.
                And(
                    async_synthesis_enabled(),
                    Eq(
                        P0("episode", "program_decision_seq"),
                        P0("episode", "program_request_seq"),
                    ),
                    Gt(
                        P0("episode", "program_request_seq"),
                        P0("episode", "synthesis_open_seq"),
                    ),
                ),
            ),
            Gt(Count(shape_eligible), L(0.0)),
            Eq(P0("primary", "ordinal"), AO(best, "ordinal")),
        ),
        "effects": [
            ["add_node", "program", "EmbodiedMotorProgram", {
                "request_seq": T(P0("episode", "program_request_seq")),
                "ordinal": T(P0("episode", "program_request_seq")),
                "token": T(A("primary", "token")),
                "status": "building",
                "source": "analysis_by_synthesis",
                "member_count": 1.0,
                "synthesis_yield_required": 0.0,
                "available": 0.0,
                "grounded_value": 0.0,
                "default_value": 0.0,
                "learned_value": 0.0,
                "decision_experience_count": 0.0,
                "internalized_epoch": -1.0,
                "experience_count": 0.0,
                **{f"mean_{key}": 0.0 for key in ALL_CONSEQUENCES},
                **{f"flow_gain_{key}": 0.0 for key in ALL_CONSEQUENCES},
                **{f"mean_context_delta_{feature}": 0.0 for feature in CONTEXT_DELTAS},
                **{f"context_delta_gain_{feature}_{conditioning}": 0.0 for feature in CONTEXT_DELTAS for conditioning in FLOW_FEATURES},
                "context_delta_experience_count": 0.0,
                "mean_flow_speed_squared": 0.0,
                **{f"mean_{feature}": 0.0 for feature in FLOW_FEATURES},
                "last_learning_seq": 0.0,
            }],
            [
                "add_edge",
                "episode",
                "has_embodied_motor_program",
                "program",
            ],
            [
                "add_edge",
                "episode",
                "has_active_embodied_motor_program",
                "program",
            ],
            [
                "add_edge",
                "episode",
                "resumes_embodied_motor_program",
                "program",
            ],
            [
                "add_edge",
                "program",
                "includes_embodied_effector_model",
                "primary",
            ],
            ["set_attr", "episode", "program_decision_seq", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "episode", "synthesis_open_seq", T(
                P0("episode", "program_request_seq")
            )],
        ],
    }


def expand_program_rule():
    available = Filter(available_models(), "candidate", Or(
        Not(future_manifold_supported()),
        And(composition_width_available("plan"), _projection_supported("plan", "candidate"), Lt(manifold_loss("plan", "candidate"), manifold_loss("plan"))),
    ))
    best = Argmin(
        available,
        "candidate",
        program_cost("plan", "candidate"),
        V("plan"),
    )
    return {
        "name": "emp_abs_expand_embodied_motor_program",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_active_embodied_motor_program", "plan"],
            ["episode", "resumes_embodied_motor_program", "plan"],
            ["episode", "has_embodied_effector_model", "candidate"],
        ],
        "where": And(
            ordinary_composer_allowed(),
            Not(Gt(
                P0("policy", "parallel_factorized_composition_enabled"),
                L(0.5),
            )),
            Eq(A("plan", "status"), L("building")),
            Eq(P0("plan", "synthesis_yield_required"), L(0.0)),
            composition_width_available("plan"),
            Eq(P0("candidate", "ordinal"), AO(best, "ordinal")),
            Lt(
                Plus(
                    program_cost("plan", "candidate"),
                    P0("policy", "minimum_composition_improvement"),
                ),
                program_cost("plan"),
            ),
        ),
        "effects": [
            ["set_attr", "plan", "synthesis_yield_required", 1.0],
            [
                "del_edge",
                "episode",
                "resumes_embodied_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "plan",
                "includes_embodied_effector_model",
                "candidate",
            ],
            ["set_attr", "plan", "member_count", T(
                Plus(P0("plan", "member_count"), L(1.0))
            )],
        ],
    }


def expand_factorized_groups_in_parallel_rule():
    """Add each independently useful actuator-group member in one graph pass."""
    available = available_models()
    same_group = Filter(
        available,
        "peer",
        Eq(
            P0("peer", "actuator_group"),
            P0("candidate", "actuator_group"),
        ),
    )
    best_in_group = Argmin(
        same_group,
        "peer",
        program_cost("plan", "peer"),
        V("plan"),
    )
    return {
        "name": "emp_abs_expand_factorized_groups_in_parallel",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": 1,
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_active_embodied_motor_program", "plan"],
            ["episode", "resumes_embodied_motor_program", "plan"],
            ["episode", "has_embodied_effector_model", "candidate"],
        ],
        "where": And(
            Not(future_manifold_enabled()),
            Gt(
                P0("policy", "parallel_factorized_composition_enabled"),
                L(0.5),
            ),
            Eq(A("plan", "status"), L("building")),
            Eq(P0("plan", "synthesis_yield_required"), L(0.0)),
            composition_width_available("plan"),
            Gt(Count(same_group), L(0.0)),
            Eq(P0("candidate", "ordinal"), AO(best_in_group, "ordinal")),
            Lt(
                Plus(
                    program_cost("plan", "candidate"),
                    P0("policy", "minimum_composition_improvement"),
                ),
                program_cost("plan"),
            ),
        ),
        "effects": [
            ["set_attr", "plan", "synthesis_yield_required", 1.0],
            [
                "del_edge",
                "episode",
                "resumes_embodied_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "plan",
                "includes_embodied_effector_model",
                "candidate",
            ],
        ],
    }


def reconcile_program_width_rule():
    actual_width = Count(members("plan"))
    return {
        "name": "emp_reconcile_materialized_program_width",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": 2,
        "batch": False,
        "match": [
            ["episode", "has_active_embodied_motor_program", "plan"],
        ],
        "where": Not(Eq(P0("plan", "member_count"), actual_width)),
        "effects": [[
            "set_attr",
            "plan",
            "member_count",
            T(actual_width),
        ]],
    }


def resume_program_rule():
    return {
        "name": "emp_resume_yielded_embodied_motor_program",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "match": [
            ["episode", "has_active_embodied_motor_program", "plan"],
            ["episode", "resumes_embodied_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("building")),
            Eq(P0("plan", "synthesis_yield_required"), L(1.0)),
        ),
        "effects": [[
            "set_attr",
            "plan",
            "synthesis_yield_required",
            0.0,
        ]],
    }


def close_program_rule():
    available = Filter(available_models(), "candidate", Or(
        Not(future_manifold_supported()),
        And(composition_width_available("plan"), _projection_supported("plan", "candidate"), Lt(manifold_loss("plan", "candidate"), manifold_loss("plan"))),
    ))
    return {
        "name": "emp_abs_close_embodied_motor_program",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_active_embodied_motor_program", "plan"],
            ["episode", "resumes_embodied_motor_program", "plan"],
        ],
        "where": And(
            ordinary_composer_allowed(),
            Eq(A("plan", "status"), L("building")),
            Eq(P0("plan", "synthesis_yield_required"), L(0.0)),
            # Under asynchronous synthesis, a build completing after the
            # action was served publishes via the async close rule instead
            # of arming a (already-consumed) decision.
            Or(
                Not(async_synthesis_enabled()),
                Gt(
                    P0("episode", "program_request_seq"),
                    P0("episode", "program_decision_seq"),
                ),
            ),
            Not(Exists(
                available,
                "candidate",
                Lt(
                    Plus(
                        program_cost("plan", "candidate"),
                        P0("policy", "minimum_composition_improvement"),
                    ),
                    program_cost("plan"),
                ),
            )),
        ),
        "effects": [
            ["set_attr", "plan", "status", "ready"],
            ["set_attr", "plan", "available", 1.0],
            *future_manifold_audit_effects("plan"),
            # A build that spanned requests (async background) arms with the
            # CURRENT request stamped, else the same-tick option retirement
            # deletes it and leaves an armed decision with no options
            # (measured deadlock at request 177 of the jam probe).  A no-op
            # for single-request synchronous builds.
            ["set_attr", "plan", "request_seq", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "plan", "default_value", T(
                Minus(L(0.0), program_cost("plan"))
            )],
            ["set_attr", "plan", "learned_value", T(
                Minus(L(0.0), program_cost("plan"))
            )],
            [
                "del_edge",
                "episode",
                "has_active_embodied_motor_program",
                "plan",
            ],
            [
                "del_edge",
                "episode",
                "resumes_embodied_motor_program",
                "plan",
            ],
            [
                "add_edge",
                "episode",
                "has_motor_decision_option",
                "plan",
            ],
            ["set_attr", "episode", "decision_request_epoch", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "episode", "decision_armed", 1.0],
        ],
    }


def native_mark_composition_choice_rule():
    """Native System 2: mark every member of the natively composed program.

    One MotorCompose evaluation per (episode, candidate) binding — each is
    a full native composition (~us) — feeding the same mark -> open ->
    attach -> close assembly pipeline the render path built.
    """
    return {
        "name": "emp_native_mark_composition_choice",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -4,
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "candidate"],
        ],
        "where": And(
            native_composition_enabled(),
            Eq(A("episode", "program_mode"), L("synthesis")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "program_decision_seq"),
            ),
            Eq(motor_compose_member(), L(1)),
            Not(Eq(
                P0("candidate", "render_choice_seq"),
                P0("episode", "program_request_seq"),
            )),
        ),
        "effects": [
            ["set_attr", "candidate", "render_choice_seq", T(
                P0("episode", "program_request_seq")
            )],
        ],
    }


def render_mark_group_choice_rule():
    """Render-first System 2, step 1: per-group choice by LOCAL cost.

    The search path's latency is quadratic in the candidate alphabet: every
    (episode, candidate) binding re-evaluates a global Argmin whose
    program_cost is itself O(models) via baseline_prediction (measured:
    System-2 p99 294/82/44 ms at 8/4/2 quantization intervals).  The arc5
    exact-first move at the motor grain is to PROPOSE the program from the
    held linear effector models instead of searching compositions: each
    actuator group independently selects the command level whose own
    receipt-learned consequence best matches the target (singleton_cost is
    O(1) — no baseline sum), and the program is assembled in one fixpoint
    pass.  Selection semantics match the factorized-parallel expansion's
    one-shot greedy (cross-group coupling ignored by both); behaviour is
    gated by the fixed-wing benches, the nominal run and the jam probe, not
    assumed.
    """
    same_group = Filter(
        MODELS,
        "peer",
        And(
            Gt(P0("peer", "experience_count"), L(0.5)),
            Gt(P0("peer", "available"), L(0.5)),
            structural_model_admissible("peer"),
            Eq(
                P0("peer", "actuator_group"),
                P0("candidate", "actuator_group"),
            ),
        ),
    )
    best_in_group = Argmin(
        same_group,
        "peer",
        singleton_cost("peer"),
        V("episode"),
    )
    return {
        "name": "emp_render_mark_factorized_group_choice",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -3,
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "candidate"],
        ],
        "where": And(
            render_first_enabled(),
            Not(native_composition_enabled()),
            Eq(A("episode", "program_mode"), L("synthesis")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "program_decision_seq"),
            ),
            Gt(P0("candidate", "experience_count"), L(0.5)),
            Gt(P0("candidate", "available"), L(0.5)),
            structural_model_admissible("candidate"),
            Eq(P0("candidate", "ordinal"), AO(best_in_group, "ordinal")),
            Not(Eq(
                P0("candidate", "render_choice_seq"),
                P0("episode", "program_request_seq"),
            )),
        ),
        "effects": [
            ["set_attr", "candidate", "render_choice_seq", T(
                P0("episode", "program_request_seq")
            )],
        ],
    }


def render_open_program_rule():
    """Render-first step 2: open the composite once any group has chosen."""
    marked = Filter(
        MODELS,
        "chosen",
        Eq(
            P0("chosen", "render_choice_seq"),
            P0("episode", "program_request_seq"),
        ),
    )
    return {
        "name": "emp_render_open_embodied_motor_program",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -2,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
        ],
        "where": And(
            Or(render_first_enabled(), native_composition_enabled()),
            Eq(A("episode", "program_mode"), L("synthesis")),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "program_request_seq"),
                P0("episode", "program_decision_seq"),
            ),
            Gt(Count(marked), L(0.0)),
        ),
        "effects": [
            ["add_node", "program", "EmbodiedMotorProgram", {
                "request_seq": T(P0("episode", "program_request_seq")),
                "ordinal": T(P0("episode", "program_request_seq")),
                "token": "render_composite",
                "status": "render_building",
                "source": "analysis_by_synthesis",
                "render_first": 1.0,
                "member_count": 0.0,
                "synthesis_yield_required": 0.0,
                "available": 0.0,
                "grounded_value": 0.0,
                "default_value": 0.0,
                "learned_value": 0.0,
                "decision_experience_count": 0.0,
                "internalized_epoch": -1.0,
                "experience_count": 0.0,
                **{f"mean_{key}": 0.0 for key in ALL_CONSEQUENCES},
                **{f"flow_gain_{key}": 0.0 for key in ALL_CONSEQUENCES},
                **{f"mean_context_delta_{feature}": 0.0 for feature in CONTEXT_DELTAS},
                **{f"context_delta_gain_{feature}_{conditioning}": 0.0 for feature in CONTEXT_DELTAS for conditioning in FLOW_FEATURES},
                "context_delta_experience_count": 0.0,
                "mean_flow_speed_squared": 0.0,
                **{f"mean_{feature}": 0.0 for feature in FLOW_FEATURES},
                "last_learning_seq": 0.0,
            }],
            [
                "add_edge",
                "episode",
                "has_embodied_motor_program",
                "program",
            ],
            ["set_attr", "episode", "program_decision_seq", T(
                P0("episode", "program_request_seq")
            )],
        ],
    }


def render_attach_member_rule():
    """Render-first step 3: attach every chosen model to the open composite."""
    return {
        "name": "emp_render_attach_chosen_members",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -1,
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program", "plan"],
            ["episode", "has_embodied_effector_model", "candidate"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("render_building")),
            Eq(
                P0("plan", "request_seq"),
                P0("episode", "program_request_seq"),
            ),
            Eq(
                P0("candidate", "render_choice_seq"),
                P0("plan", "request_seq"),
            ),
            Not(Exists(
                members("plan"),
                "existing",
                Eq(
                    P0("existing", "ordinal"),
                    P0("candidate", "ordinal"),
                ),
            )),
        ),
        "effects": [
            [
                "add_edge",
                "plan",
                "includes_embodied_effector_model",
                "candidate",
            ],
        ],
    }


def render_close_program_rule():
    """Render-first step 4: arm the decision once every choice is attached."""
    marked = Filter(
        MODELS,
        "chosen",
        Eq(
            P0("chosen", "render_choice_seq"),
            P0("plan", "request_seq"),
        ),
    )
    unattached = Exists(
        marked,
        "chosen",
        Not(Exists(
            members("plan"),
            "attached",
            Eq(
                P0("attached", "ordinal"),
                P0("chosen", "ordinal"),
            ),
        )),
    )
    return {
        "name": "emp_render_close_embodied_motor_program",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": 0,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program", "plan"],
        ],
        "where": And(
            Eq(A("plan", "status"), L("render_building")),
            Eq(
                P0("plan", "request_seq"),
                P0("episode", "program_request_seq"),
            ),
            Gt(Count(members("plan")), L(0.0)),
            Not(unattached),
        ),
        "effects": [
            ["set_attr", "plan", "status", "ready"],
            ["set_attr", "plan", "available", 1.0],
            ["set_attr", "plan", "member_count", T(Count(members("plan")))],
            *future_manifold_audit_effects("plan"),
            ["set_attr", "plan", "grounded_value", T(
                Minus(L(0.0), program_cost("plan"))
            )],
            ["set_attr", "plan", "default_value", T(
                Minus(L(0.0), program_cost("plan"))
            )],
            ["set_attr", "plan", "learned_value", T(
                Minus(L(0.0), program_cost("plan"))
            )],
            [
                "add_edge",
                "episode",
                "has_motor_decision_option",
                "plan",
            ],
            ["set_attr", "episode", "decision_request_epoch", T(
                P0("episode", "program_request_seq")
            )],
            ["set_attr", "episode", "decision_armed", 1.0],
        ],
    }


def open_program_trial_rule():
    return {
        "name": "emp_open_selected_motor_program_trial",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program", "program"],
        ],
        "where": And(
            Eq(A("episode", "decision_status"), L("published")),
            Eq(A("episode", "selected_option_ref"), V("program")),
            Gt(
                P0("episode", "selected_decision_epoch"),
                P0("episode", "last_program_trial_epoch"),
            ),
        ),
        "effects": [
            ["add_node", "trial", "EmbodiedMotorProgramTrial", {
                "request_seq": T(P0("episode", "selected_decision_epoch")),
                "status": "assembling",
                "expected_member_count": T(P0("program", "member_count")),
                "receipt_verified": 0.0,
            }],
            [
                "add_edge",
                "episode",
                "has_embodied_motor_program_trial",
                "trial",
            ],
            ["add_edge", "trial", "enacts_embodied_motor_program", "program"],
            ["set_attr", "program", "available", 0.0],
            [
                "del_edge",
                "episode",
                "has_motor_decision_option",
                "program",
            ],
            ["set_attr", "episode", "last_program_trial_epoch", T(
                P0("episode", "selected_decision_epoch")
            )],
        ],
    }


def _temporal_group_models(group_var="model"):
    """All declared command levels for one opaque effector group."""
    return Filter(
        MODELS,
        "peer",
        Eq(
            P0("peer", "actuator_group"),
            P0(group_var, "actuator_group"),
        ),
    )


def _temporal_states(group_var="model"):
    """The persistent graph state for one opaque effector channel."""
    return Filter(
        Neighbours("episode", "has_temporal_command_state"),
        "state",
        Eq(
            P0("state", "actuator_group"),
            P0(group_var, "actuator_group"),
        ),
    )


def _temporal_group_representative(group_var="model"):
    return Argmin(
        _temporal_group_models(group_var),
        "peer",
        P0("peer", "ordinal"),
        V("episode"),
    )


def _temporal_request_level(var="requested"):
    """Use a declared continuous request, falling back to the model level."""
    return If(
        Gt(P0(var, "temporal_request_declared"), L(0.5)),
        P0(var, "temporal_request_level"),
        P0(var, "specified_command_level"),
    )


def temporal_command_state_rule():
    """Create one residual accumulator per declared opaque effector group.

    The rule is deliberately absent-inert.  A consumer opts in by setting
    ``temporal_command_encoding_enabled`` on its episode (or policy); no
    command alphabet, morphology, or vehicle vocabulary is introduced here.
    Choosing the ordinal-minimum model as the representative makes creation
    unique even when a group exposes many command levels.
    """
    states = _temporal_states("model")
    representative = _temporal_group_representative("model")
    return {
        "name": "emp_open_temporal_command_state",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -20,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "model"],
        ],
        "where": And(
            Or(
                Gt(P0("policy", "temporal_command_encoding_enabled"), L(0.5)),
                Gt(P0("episode", "temporal_command_encoding_enabled"), L(0.5)),
            ),
            Eq(P0("model", "ordinal"), AO(representative, "ordinal")),
            Eq(Count(states), L(0.0)),
        ),
        "effects": [
            ["add_node", "state", "EmbodiedTemporalCommandState", {
                "actuator_group": T(P0("model", "actuator_group")),
                "residual": 0.0,
                "last_request": 0.0,
                "last_command": 0.0,
                "step": 0.0,
            }],
            [
                "add_edge",
                "episode",
                "has_temporal_command_state",
                "state",
            ],
        ],
    }


def temporal_command_reset_rule():
    """Reset all graph-held accumulators when the consumer starts a replay."""
    return {
        "name": "emp_reset_temporal_command_state",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": -21,
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_temporal_command_state", "state"],
        ],
        "where": And(
            Or(
                Gt(P0("policy", "temporal_command_encoding_enabled"), L(0.5)),
                Gt(P0("episode", "temporal_command_encoding_enabled"), L(0.5)),
            ),
            Gt(P0("episode", "temporal_command_reset"), L(0.5)),
        ),
        "effects": [
            ["set_attr", "state", "residual", 0.0],
            ["set_attr", "state", "last_request", 0.0],
            ["set_attr", "state", "last_command", 0.0],
            ["set_attr", "state", "step", 0.0],
            ["set_attr", "episode", "temporal_command_reset", 0.0],
        ],
    }


def _temporal_commandable_members(trial="trial"):
    return Filter(
        Neighbours(trial, "commands_embodied_effector_model"),
        "member",
        Not(Gt(P0("member", "never_commanded"), L(0.5))),
    )


def temporal_encode_trial_member_rule():
    """Sigma-delta encode one selected continuous request in graph terms.

    The alphabet is the set of declared model command levels in the same
    actuator group.  The selected request plus the graph-held residual is
    clamped, nearest-quantised, and emitted as another model member; the new
    residual is written back to the group state.  The lower command wins exact
    ties through the second Argmin over the minimum-distance subset.
    """
    states = _temporal_states("requested")
    group_models = _temporal_group_models("requested")
    lower = MinOver(
        group_models,
        "peer",
        P0("peer", "specified_command_level"),
        L(0.0),
    )
    upper = MaxOver(
        group_models,
        "peer",
        P0("peer", "specified_command_level"),
        L(0.0),
    )
    request = Clamp(
        _temporal_request_level("requested"),
        lower,
        upper,
    )
    target = Clamp(
        Plus(request, P0("state", "residual")),
        lower,
        upper,
    )
    distance = Abs(Minus(
        P0("peer", "specified_command_level"),
        target,
    ))
    nearest_distance = MinOver(group_models, "peer", distance, L(0.0))
    nearest = Filter(
        group_models,
        "near",
        Not(Gt(
            Abs(Minus(
                P0("near", "specified_command_level"),
                target,
            )),
            nearest_distance,
        )),
    )
    emitted = Argmin(
        nearest,
        "near",
        P0("near", "specified_command_level"),
        V("requested"),
    )
    return {
        "name": "emp_temporal_encode_embodied_motor_trial_member",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": 1,
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            [
                "trial",
                "commands_embodied_effector_model",
                "requested",
            ],
            [
                "episode",
                "has_temporal_command_state",
                "state",
            ],
        ],
        "where": And(
            Or(
                Gt(P0("policy", "temporal_command_encoding_enabled"), L(0.5)),
                Gt(P0("episode", "temporal_command_encoding_enabled"), L(0.5)),
            ),
            Eq(A("trial", "status"), L("temporal_encoding")),
            Not(Gt(P0("requested", "never_commanded"), L(0.5))),
            Eq(
                P0("state", "actuator_group"),
                P0("requested", "actuator_group"),
            ),
            Not(Exists(
                Neighbours("trial", "temporal_encodes_model"),
                "encoded",
                Eq(V("encoded"), V("requested")),
            )),
        ),
        "effects": [
            # Edge endpoints are match variables in the graph effect IR, so
            # the selected alphabet member is represented by a fresh command
            # node whose token is computed from `emitted`.  This keeps the
            # decision graph-native while the host only transduces its result.
            ["add_node", "command", "EmbodiedTemporalCommand", {
                "token": T(AO(emitted, "token")),
                "actuator_group": T(AO(emitted, "actuator_group")),
                "command_level": T(AO(emitted, "specified_command_level")),
                "request_level": T(request),
            }],
            [
                "add_edge",
                "trial",
                "has_temporal_command",
                "command",
            ],
            ["add_edge", "trial", "temporal_encodes_model", "requested"],
            ["set_attr", "state", "last_request", T(request)],
            ["set_attr", "state", "last_command", T(
                AO(emitted, "specified_command_level")
            )],
            ["set_attr", "state", "residual", T(
                Minus(target, AO(emitted, "specified_command_level"))
            )],
            ["set_attr", "state", "step", T(
                Plus(P0("state", "step"), L(1.0))
            )],
        ],
    }


def close_temporal_command_trial_rule():
    """Release a temporally encoded trial only after every channel is done."""
    members = _temporal_commandable_members("trial")
    unencoded = Exists(
        members,
        "member",
        Not(Exists(
            Neighbours("trial", "temporal_encodes_model"),
            "encoded",
            Eq(V("encoded"), V("member")),
        )),
    )
    return {
        "name": "emp_close_temporal_embodied_motor_trial",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": 2,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
        ],
        "where": And(
            Or(
                Gt(P0("policy", "temporal_command_encoding_enabled"), L(0.5)),
                Gt(P0("episode", "temporal_command_encoding_enabled"), L(0.5)),
            ),
            Eq(A("trial", "status"), L("temporal_encoding")),
            Not(unencoded),
        ),
        "effects": [
            ["set_attr", "trial", "status", "issued"],
            ["set_attr", "episode", "action_ready", 1.0],
        ],
    }


def temporal_emit_neutral_for_empty_trial_rule():
    """Keep a body-only program executable without host-side token policy.

    Some generic plants include an observed, never-commanded body contributor
    as the complete selected program.  It has no command alphabet of its own;
    the graph therefore emits the stable neutral command from group zero so a
    simulator boundary never receives an empty token tuple.
    """
    members = _temporal_commandable_members("trial")
    neutral_models = Filter(
        MODELS,
        "neutral",
        And(
            Not(Gt(P0("neutral", "never_commanded"), L(0.5))),
            Eq(P0("neutral", "actuator_group"), L(0.0)),
            Not(Gt(Abs(P0("neutral", "specified_command_level")), L(1e-12))),
        ),
    )
    neutral = Argmin(
        neutral_models,
        "neutral",
        P0("neutral", "ordinal"),
        V("episode"),
    )
    return {
        "name": "emp_temporal_emit_neutral_for_empty_trial",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": 1,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
        ],
        "where": And(
            Or(
                Gt(P0("policy", "temporal_command_encoding_enabled"), L(0.5)),
                Gt(P0("episode", "temporal_command_encoding_enabled"), L(0.5)),
            ),
            Eq(A("trial", "status"), L("temporal_encoding")),
            Eq(Count(members), L(0.0)),
            Eq(Count(Neighbours("trial", "has_temporal_command")), L(0.0)),
        ),
        "effects": [
            ["add_node", "command", "EmbodiedTemporalCommand", {
                "token": T(AO(neutral, "token")),
                "actuator_group": T(AO(neutral, "actuator_group")),
                "command_level": T(AO(neutral, "specified_command_level")),
                "request_level": 0.0,
                "neutral_fallback": 1.0,
            }],
            ["add_edge", "trial", "has_temporal_command", "command"],
        ],
    }


def emit_neutral_for_empty_trial_rule():
    """Emit a graph-neutral command for any body-only motor program.

    Body contributors are valid program members but are not simulator tokens.
    A selected body-only program therefore still needs the graph's declared
    neutral command before the generic host boundary can transduce it.  This
    rule is independent of temporal encoding and keeps that invariant true
    for every opaque plant.
    """
    members = _temporal_commandable_members("trial")
    neutral_models = Filter(
        MODELS,
        "neutral",
        And(
            Not(Gt(P0("neutral", "never_commanded"), L(0.5))),
            Eq(P0("neutral", "actuator_group"), L(0.0)),
            Not(Gt(Abs(P0("neutral", "specified_command_level")), L(1e-12))),
        ),
    )
    neutral = Argmin(
        neutral_models,
        "neutral",
        P0("neutral", "ordinal"),
        V("episode"),
    )
    return {
        "name": "emp_emit_neutral_for_empty_motor_trial",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "order": 1,
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
        ],
        "where": And(
            Eq(A("trial", "status"), L("issued")),
            Eq(Count(members), L(0.0)),
            Eq(Count(Neighbours("trial", "has_embodied_motor_command")), L(0.0)),
        ),
        "effects": [
            ["add_node", "command", "EmbodiedMotorCommand", {
                "token": T(AO(neutral, "token")),
                "actuator_group": T(AO(neutral, "actuator_group")),
                "command_level": T(AO(neutral, "specified_command_level")),
                "neutral_fallback": 1.0,
            }],
            ["add_edge", "trial", "has_embodied_motor_command", "command"],
        ],
    }


def copy_trial_members_rule():
    """Copy a program's members onto the trial that will enact it.

    **`never_commanded` is part of the effector contract here.**  An effector
    model may be OBSERVED and LEARNED without ever being commanded: it is a
    contributor whose command was issued elsewhere, or once, and never varies.
    The body itself is the standing example — an airframe or a chassis was
    commanded at construction to have a particular response and has been
    executing that command ever since — and a deviation from it is a deviation
    from command in exactly the sense every other effector already uses.

    Without this, an effector model is commandable BY CONSTRUCTION and
    "observed but never commanded" has no representation at all. Measured: a
    plant contributor added to the graph was selected by the composer and its
    token issued to the world, which raised `unknown token: 'plant'` — the loop
    tried to fly the airframe as if it were a surface, and marking it
    unavailable did not stop it, because availability gates candidacy and not
    the command path.

    **Absence means commandable.** The flag is `never_commanded`, not
    `commandable`, precisely so that an absent attribute reads as zero and
    every body plan that has never heard of this is byte-identical. Every body
    plan has an invariant that is not actually invariant; the ones that truly
    do not simply carry a zero here and lose nothing.
    """
    copied = Neighbours("trial", "commands_embodied_effector_model")
    return {
        "name": "emp_copy_program_members_to_trial",
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "enacts_embodied_motor_program", "program"],
            ["program", "includes_embodied_effector_model", "member"],
        ],
        # NOTE: never-commanded members are NOT excluded here.  A motor
        # program operates FROM the body -- the plant is where it acts, not an
        # optional participant -- so it belongs on the trial like any other
        # member.  What must not happen is a COMMAND being issued to it, and
        # that is a property of the command path, not of membership.  The
        # earlier version gated here and produced exactly the confusion it
        # should have avoided: a trial with four tokens against five members.
        "where": Not(Exists(
            copied,
            "existing",
            Eq(V("existing"), V("member")),
        )),
        "effects": [
            [
                "add_edge",
                "trial",
                "commands_embodied_effector_model",
                "member",
            ],
            ["set_attr", "trial", "status", T(If(
                Or(
                    Gt(P0("policy", "temporal_command_encoding_enabled"), L(0.5)),
                    Gt(P0("episode", "temporal_command_encoding_enabled"), L(0.5)),
                ),
                L("temporal_encoding"),
                L("issued"),
            ))],
            ["set_attr", "episode", "action_ready", T(If(
                Or(
                    Gt(P0("policy", "temporal_command_encoding_enabled"), L(0.5)),
                    Gt(P0("episode", "temporal_command_encoding_enabled"), L(0.5)),
                ),
                L(0.0),
                L(1.0),
            ))],
        ],
    }



# ---------------------------------------------------------------------------
# SHAPES INDEX MODELS.  The fork.
#
# DF measured why the shape-derived RATE cost three ground contacts, and the
# defect was scope rather than arithmetic: `stable_run` is regime-local and the
# model it was applied to is global, so one sample in a new regime discarded
# what the model knew about every other one.
#
# The resolution is the pattern this line already uses everywhere else.  Shapes
# index programs (`EmbodiedMotorProgramShape`).  Shapes index reflexes
# (`EmbodiedSurpriseShape` -> condensed response).  So shapes should index
# MODELS: when the residual lands in a regime never seen before, the model
# FORKS -- the fork inherits everything the parent knew and then adapts on its
# OWN sample count.
#
# WHICH MAKES THE RATE PROBLEM DISSOLVE RATHER THAN GET TUNED.  A fork starts
# at `experience_count` 1, so the plain `1/n` the tree has always used gives
# 0.5 on its next sample, 0.33 on the one after, decaying honestly -- fast
# where the evidence is thin and slow where it is not.  No floor, no
# `1/stable_run`, no declared constant.  The rate was never the thing that
# needed fixing; the thing it was applied to was.
#
# The fork inherits rather than starting empty because starting empty is
# unusable: `eligible` requires `experience_count > 0.5`, so a model with no
# samples can never be selected and can therefore never GET a sample.
# Inheriting the parent's means makes the fork immediately usable and no worse
# than the parent on its first action, which is the honest prior -- what you
# knew a moment ago is the best guess for a regime you have never seen.
# ---------------------------------------------------------------------------

# `token` is NOT in this list.  It is a STRING, and `P0` is `Plus(Attr, 0.0)`
# -- the first-class-absence idiom for NUMBERS.  Adding 0.0 to a String yields
# 0.0, so copying the token through `P0` gives every fork the token `0.0`, and
# the world adapter raises `unknown X-15 token: '0.0'` the moment it tries to
# command one.  This is the THIRD time this bug has been written today (the
# reflex response signature, the condensation comparison, and here), so the
# rule is recorded beside the list rather than in a commit message: A STRING
# ATTR IS READ WITH `A`, NEVER WITH `P0`.  Both other places in this file that
# copy a token already do it correctly.
_FORK_SCALARS = (
    "actuator_group", "ordinal", "available",
    "activation_magnitude", "log_authority",
    "specified_command_level", "state_effector_position",
    "specified_maximum_position_change_per_action",
    "specified_actuator_dynamics_enabled",
    "specified_effect_prior_confidence",
    "structural_certified_default",
)


def fork_regime_local_model_rule():
    """Fork the commanded model when its regime is one it has never seen."""
    forks = Neighbours("model", "has_regime_local_model")
    ordinal = IDiv(P0("episode", "current_surprise_ordinal"), L(1))
    attrs = {
        # The fork IS an effector model -- same type, so every rule that reads
        # a model reads this one, and no consumer learns a new vocabulary.
        "shape_ordinal": T(ordinal),
        "forked_from_experience": T(P0("model", "experience_count")),
        # ONE sample of inherited belief.  Not zero (unusable, see above) and
        # not the parent's count (which is the global scope this exists to
        # escape).
        "experience_count": 1.0,
        "recalibration_required": 0.0,
        "last_learning_seq": T(P0("outcome", "request_seq")),
        "last_singleton_exercise_seq": T(P0("outcome", "request_seq")),
    }
    for key in _FORK_SCALARS:
        attrs[key] = T(P0("model", key))
    # The fork commands the SAME physical effector as its parent, so it carries
    # the same token -- read as a String.
    attrs["token"] = T(A("model", "token"))
    for key in ALL_CONSEQUENCES:
        attrs[f"mean_{key}"] = T(P0("model", f"mean_{key}"))
        attrs[f"flow_gain_{key}"] = T(P0("model", f"flow_gain_{key}"))
        attrs[f"specified_passive_mean_{key}"] = T(
            P0("model", f"specified_passive_mean_{key}"))
        attrs[f"specified_position_gain_{key}"] = T(
            P0("model", f"specified_position_gain_{key}"))
        attrs[f"specified_{key}"] = T(P0("model", f"specified_{key}"))
        for feature in FLOW_FEATURES:
            attrs[f"{feature}_gain_{key}"] = T(
                P0("model", f"{feature}_gain_{key}"))
    attrs["mean_flow_speed_squared"] = T(P0("model", "mean_flow_speed_squared"))
    attrs["flow_variance_sum"] = 0.0
    for feature in FLOW_FEATURES:
        attrs[f"mean_{feature}"] = T(P0("model", f"mean_{feature}"))
        attrs[f"{feature}_variance_sum"] = 0.0
    for feature in CONTEXT_DELTAS:
        attrs[f"mean_context_delta_{feature}"] = T(P0("model", f"mean_context_delta_{feature}"))
        for conditioning in FLOW_FEATURES:
            attrs[f"context_delta_gain_{feature}_{conditioning}"] = T(P0("model", f"context_delta_gain_{feature}_{conditioning}"))
    attrs["context_delta_experience_count"] = T(P0("model", "context_delta_experience_count"))
    return {
        "name": "emp_fork_regime_local_model",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "comment": "A residual in a regime this model has never seen forks it: "
        "the fork inherits the parent's means and restarts its own count.",
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "commands_embodied_effector_model", "model"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Gt(P0("policy", "regime_local_models_enabled"), L(0.5)),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "request_seq"),
               P0("episode", "program_request_seq")),
            Gt(P0("episode", "current_surprise_ordinal"), L(0.0)),
            # Only a model that is itself global forks; a fork never forks.
            Not(Gt(P0("model", "shape_ordinal"), L(0.0))),
            Not(Exists(
                forks, "held",
                Eq(IDiv(P0("held", "shape_ordinal"), L(1)), ordinal),
            )),
        ),
        "effects": [
            ["add_node", "fork", "EmbodiedEffectorModel", attrs],
            ["add_edge", "model", "has_regime_local_model", "fork"],
            ["add_edge", "episode", "has_embodied_effector_model", "fork"],
        ],
    }


def learn_primitive_rule():
    count = Plus(P0("model", "experience_count"), L(1.0))
    recalibrating = Gt(P0("model", "recalibration_required"), L(0.5))
    # A FLOOR UNDER THE LEARNING RATE, because 1/n asserts stationarity.
    #
    # `1/n` is the incremental mean of a process that does not change.  At
    # count 200 a new observation moves the mean by 0.5%, so a plant that
    # enters a new basin is unlearnable however many samples arrive -- measured
    # (block CA): 27 of 37 models gaining samples where 1 did, and prediction
    # error IDENTICAL TO THE DIGIT, 638.45 through the departure either way.
    # More samples were not more understanding.
    #
    # The floor caps the effective sample window: below it the model keeps
    # averaging as before, above it the oldest evidence stops outvoting the
    # present.  This is the aerial seed's shape (`aa_learn_aerial_forward_model`
    # uses 1/n only while uncalibrated and a declared rate after), reduced to
    # the part that needs no per-model surprise signal.
    #
    # Absent `model_adaptation_rate_floor` (0) this is `Max(1/n, 0)` = `1/n`, so
    # every consumer that does not declare it is byte-identical.
    # THE RATE IS A COUNT OVER THE AGENT'S OWN HISTORY, WHICH IS WHAT ENDS THE
    # REGRESS.  Block CD recorded it exactly: "1/n asserts stationarity ->
    # declare a floor -> a flat floor costs quiet regimes -> declare a surprise
    # factor -> surprise needs a reference -> an error EMA -> the EMA needs a
    # rate -> ... 1/n".  Each rate needed a rate, and two attempts at
    # surprise-gating were reverted because the reference was itself a 1/n
    # accumulator judging 1/n accumulators.
    #
    # `stable_run` is not an accumulator.  It is an INTEGER COUNT of how many
    # consecutive times the current surprise shape has produced the same
    # response, so computing it needs no rate at all, and the regress
    # terminates rather than recursing.
    #
    # What it yields is the floor the tree had to declare, EARNED instead of
    # asserted: a shape seen once adapts at 1.0 (nothing is known, believe what
    # was just seen), a shape stable for 20 encounters adapts at 0.05 -- which
    # is precisely the constant `model_adaptation_rate_floor` was set to, now
    # arrived at from the codebook's own history rather than from taste.  A
    # shape stable for 200 adapts at 0.005 and should, because nothing has
    # changed in 200 encounters.
    #
    # Polarity: `current_stable_run` absent reads 0, and the guard falls back to
    # the declared floor, so every consumer without the surprise index is
    # byte-identical.
    # MEASURED AND GATED OFF BY DEFAULT (block DF).  A clean 2x2 over three
    # faults at three episodes: rate-from-shape ON costs exactly three ground
    # contacts (1/9 -> 4/9) whether credit assignment is on or off, and credit
    # assignment is exactly neutral (1/9 vs 1/9, 4/9 vs 4/9).
    #
    # The FORM is right and the regress it ends is real: `stable_run` is a
    # count, so it needs no rate of its own.  What is wrong is the SCOPE.  At
    # `stable_run == 1` the rate is 1.0, so ONE sample replaces the model
    # entirely -- and the model is GLOBAL, holding 200+ samples across every
    # regime, while the run length is REGIME-LOCAL.  Applying a regime-local
    # rate to a global model discards what the model knows about every other
    # regime on a single observation.  It buys the departure it was aimed at
    # (damaged_wing 1/3 -> 0/3, with credit) and pays for it twice over on
    # jammed_rudder and saturated_elevator, where the novel shapes come from
    # the fault rather than from a basin change.
    #
    # The resolution is not a smaller number, it is the codebook pattern this
    # whole line already uses: shapes index programs, shapes index reflexes --
    # shapes should index MODELS.  A new shape should get a NEW model that
    # starts empty, where a rate of 1.0 is correct, instead of overwriting one
    # that is right about everywhere else.  That is a build, not a constant,
    # and it is not started here.
    #
    # Absent `model_adaptation_rate_from_shape` reads 0 and the declared floor
    # is used, which is the behaviour every consumer had before DB.
    adaptive_floor = If(
        And(
            Gt(P0("policy", "model_adaptation_rate_from_shape"), L(0.5)),
            Gt(P0("episode", "current_stable_run"), L(0.0)),
        ),
        Div(L(1.0), P0("episode", "current_stable_run")),
        P0("episode", "model_adaptation_rate_floor"),
    )
    learning_rate = If(
        recalibrating,
        L(1.0),
        Max(Div(L(1.0), count), adaptive_floor),
    )
    flow_delta = Minus(
        pre_flow_speed_squared(),
        P0("model", "mean_flow_speed_squared"),
    )
    next_flow_mean = If(
        recalibrating,
        pre_flow_speed_squared(),
        Plus(
            P0("model", "mean_flow_speed_squared"),
            Div(flow_delta, count),
        ),
    )
    next_flow_variance = If(
        recalibrating,
        L(0.0),
        Plus(
            P0("model", "flow_variance_sum"),
            Times(
                flow_delta,
                Minus(
                    pre_flow_speed_squared(),
                    next_flow_mean,
                ),
            ),
        ),
    )
    feature_updates = {}
    for feature in FLOW_FEATURES:
        feature_delta = Minus(
            pre_flow_feature(feature),
            P0("model", f"mean_{feature}"),
        )
        next_feature_mean = If(
            recalibrating,
            pre_flow_feature(feature),
            Plus(
                P0("model", f"mean_{feature}"),
                Div(feature_delta, count),
            ),
        )
        next_feature_variance = If(
            recalibrating,
            L(0.0),
            Plus(
                P0("model", f"{feature}_variance_sum"),
                Times(
                    feature_delta,
                    Minus(
                        pre_flow_feature(feature),
                        next_feature_mean,
                    ),
                ),
            ),
        )
        feature_updates[feature] = (
            feature_delta,
            next_feature_mean,
            next_feature_variance,
        )
    # HOLD THE COLLAPSE OPEN.
    #
    # The shared slope has already written its prediction into this model's
    # `mean_*`, so the residual against the collapse is simply how far this
    # receipt lands from what the model currently claims -- no sibling, no
    # pairwise sweep, ONE comparison per receipt.  Evidence arrives with
    # receipts and this is where they arrive.
    #
    # The first build re-derived the collapse every action over every pair in a
    # group (~288 x 19 terms) and blew a ten-minute budget that normally fits
    # three scenarios.  A collapse that must be re-established continuously is
    # System 2 in System 1's clothes; the collapse stands, and only its RESIDUAL
    # stays open.
    #
    # Hysteresis, because a latch needs different activation and deactivation
    # energy: split above the declared factor, rejoin below half of it.  That is
    # what lets a range coarsen again rather than fragment one way -- measured
    # need (CL): one noisy observation in a departure split a range that was
    # genuinely one ratio, and cost damaged_wing 0/3 -> 2/3.
    collapse_residual = Max(*[
        Div(
            Abs(Minus(outcome_observation(key), P0("model", f"mean_{key}"))),
            Max(Abs(P0("model", f"mean_{key}")), L(0.000001)),
        )
        for key in ALL_CONSEQUENCES
    ])
    split_factor = P0("episode", "slope_range_split_factor")
    next_disagreement = Plus(
        P0("model", "slope_disagreement_ema"),
        Times(
            Minus(collapse_residual, P0("model", "slope_disagreement_ema")),
            Max(P0("episode", "model_adaptation_rate_floor"), L(0.05)),
        ),
    )
    # THE COMPARISON IS POSITIONAL, NOT A RANK.
    #
    # CO measured heteroscedasticity as residual at HIGH deflection over residual
    # at LOW deflection -- error growing toward the extremes of the axis, which
    # separated the populations 20x (0.71-1.66 where the ratio holds, 38.02 where
    # it breaks).  The first build compared each model against the group's LEAST
    # disagreeing peer instead, which asks "am I worse than the best" rather than
    # "does error grow with deflection".  Measured (CQ2): the least peer is near
    # zero in every group because some level always agrees, so the ratio is
    # enormous for everyone and the test degenerates -- identical numbers with and
    # without an absence filter, and damaged_wing losing its 0/3.
    #
    # So the comparator is the group's CENTRE: peers nearer the origin of the
    # command axis than this model.  A model at the extreme compares against the
    # levels where the line is best established; a model near the centre finds no
    # such peer and takes its own reading, giving a ratio of 1 and splitting
    # nothing.
    group_centre_disagreement = MinOver(
        Filter(
            Neighbours("episode", "has_embodied_effector_model"),
            "peer",
            And(
                Eq(
                    P0("peer", "actuator_group"),
                    P0("model", "actuator_group"),
                ),
                Gt(P0("peer", "experience_count"), L(0.0)),
                # strictly nearer the origin than this model
                Lt(
                    Abs(P0("peer", "specified_command_level")),
                    Abs(P0("model", "specified_command_level")),
                ),
            ),
        ),
        "peer",
        P0("peer", "slope_disagreement_ema"),
        next_disagreement,
    )
    effects = [
        # Evidence accumulates unconditionally; only the DECISION is gated.
        ["set_attr", "model", "slope_disagreement_ema", T(next_disagreement)],
        # THE SHAPE TEST: is my residual DISPROPORTIONATE to my group's least?
        #
        # Not "is my error large" -- measured (CN), that cannot discriminate:
        # per-receipt residual medians are 0.95 where the ratio holds and 1.35
        # where it breaks, two populations whose quartiles overlap almost
        # entirely, so no magnitude threshold separates them.
        #
        # What separates them is HETEROSCEDASTICITY (CO): residual magnitude at
        # high deflection over low is 0.71-1.66 where the shared ratio holds and
        # 38.02 where it breaks -- a factor of ~20 between populations that a
        # median could not tell apart. A relationship that has broken does not
        # fail everywhere; it fails at the extremes, which is the shape of a
        # knee and not the shape of noise.
        #
        # So the comparison is against the group's OWN least-disagreeing model --
        # a ratio of two EMAs, unitless, needing no absolute scale. Hysteresis
        # at half the factor, so a range can coarsen again.
        ["set_attr", "model", "slope_range_ordinal", T(If(
            Not(Gt(split_factor, L(0.0))),
            P0("model", "slope_range_ordinal"),
            If(
                Gt(next_disagreement,
                   Times(split_factor, Max(group_centre_disagreement, L(0.000001)))),
                Plus(P0("model", "ordinal"), L(1.0)),
                If(
                    Lt(next_disagreement,
                       Times(Times(split_factor, L(0.5)),
                             Max(group_centre_disagreement, L(0.000001)))),
                    L(0.0),
                    P0("model", "slope_range_ordinal"),
                ),
            ),
        ))],
    ]
    for key in ALL_CONSEQUENCES:
        observation = outcome_observation(key)
        next_mean = Plus(
            P0("model", f"mean_{key}"),
            Times(
                learning_rate,
                Minus(observation, P0("model", f"mean_{key}")),
            ),
        )
        next_covariance = If(
            recalibrating,
            L(0.0),
            Plus(
                P0("model", f"flow_covariance_{key}"),
                Times(
                    flow_delta,
                    Minus(observation, next_mean),
                ),
            ),
        )
        effects.extend([
            ["set_attr", "model", f"mean_{key}", T(next_mean)],
            ["set_attr", "model", f"flow_covariance_{key}", T(next_covariance)],
            ["set_attr", "model", f"flow_gain_{key}", T(If(
                Gt(next_flow_variance, L(0.0)),
                Div(next_covariance, next_flow_variance),
                L(0.0),
            ))],
        ])
        for feature, (
            feature_delta,
            _next_feature_mean,
            next_feature_variance,
        ) in feature_updates.items():
            next_feature_covariance = If(
                recalibrating,
                L(0.0),
                Plus(
                    P0("model", f"{feature}_covariance_{key}"),
                    Times(
                        feature_delta,
                        Minus(observation, next_mean),
                    ),
                ),
            )
            effects.extend([
                [
                    "set_attr",
                    "model",
                    f"{feature}_covariance_{key}",
                    T(next_feature_covariance),
                ],
                [
                    "set_attr",
                    "model",
                    f"{feature}_gain_{key}",
                    T(If(
                        Gt(next_feature_variance, L(0.0)),
                        Div(
                            next_feature_covariance,
                            next_feature_variance,
                        ),
                        L(0.0),
                    )),
                ],
            ])
    for feature, (
        _feature_delta,
        next_feature_mean,
        next_feature_variance,
    ) in feature_updates.items():
        effects.extend([
            [
                "set_attr",
                "model",
                f"mean_{feature}",
                T(next_feature_mean),
            ],
            [
                "set_attr",
                "model",
                f"{feature}_variance_sum",
                T(next_feature_variance),
            ],
        ])
    # Context transitions are learned from the dedicated receipt fields and
    # remain distinct from consequence residuals.
    for feature in CONTEXT_DELTAS:
        observation = outcome_context_delta(feature)
        next_mean = Plus(
            P0("model", f"mean_context_delta_{feature}"),
            Times(learning_rate, Minus(observation, P0("model", f"mean_context_delta_{feature}"))),
        )
        effects.append(["set_attr", "model", f"mean_context_delta_{feature}", T(next_mean)])
        for conditioning in FLOW_FEATURES:
            covariance = Plus(
                P0("model", f"context_delta_covariance_{feature}_{conditioning}"),
                Times(
                    Minus(pre_flow_feature(conditioning), P0("model", f"mean_{conditioning}")),
                    Minus(observation, next_mean),
                ),
            )
            effects.extend([
                ["set_attr", "model", f"context_delta_covariance_{feature}_{conditioning}", T(covariance)],
                ["set_attr", "model", f"context_delta_gain_{feature}_{conditioning}", T(If(
                    Gt(P0("model", f"{conditioning}_variance_sum"), L(0.0)),
                    Div(covariance, P0("model", f"{conditioning}_variance_sum")),
                    L(0.0),
                ))],
            ])
    effects.append(["set_attr", "model", "context_delta_experience_count", T(count)])
    return {
        "name": "emp_learn_factorized_effector_from_exact_receipt",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "match": [
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "commands_embodied_effector_model", "model"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(P0("trial", "expected_member_count"), L(1.0)),
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
            Gt(
                P0("outcome", "request_seq"),
                P0("model", "last_learning_seq"),
            ),
        ),
        "effects": [
            # WHEN THIS MODEL WAS LAST SEEN ALONE.  This rule fires only for
            # single-member trials (`expected_member_count == 1`), so its own
            # firing IS the exercise and stamping here needs no new rule.
            # `calibration_frontier` reads it to tell a model whose contribution
            # is currently unattributable from one that is merely well sampled.
            ["set_attr", "model", "last_singleton_exercise_seq", T(
                P0("outcome", "request_seq")
            )],
            *effects,
            ["set_attr", "model", "mean_flow_speed_squared", T(next_flow_mean)],
            ["set_attr", "model", "flow_variance_sum", T(next_flow_variance)],
            ["set_attr", "model", "experience_count", T(count)],
            ["set_attr", "model", "recalibration_required", 0.0],
            ["set_attr", "model", "last_learning_seq", T(
                P0("outcome", "request_seq")
            )],
        ],
    }


def learn_program_rule():
    count = Plus(P0("program", "experience_count"), L(1.0))
    error_terms = []
    effects = []
    for key in ALL_CONSEQUENCES:
        observation = outcome_observation(key)
        additive = prediction("program", key)
        residual = Minus(observation, additive)
        error_terms.append(Times(
            P0("policy", f"{key}_weight"),
            residual,
            residual,
        ))
        effects.extend([
            ["set_attr", "program", f"mean_{key}", T(Plus(
                P0("program", f"mean_{key}"),
                Div(
                    Minus(observation, P0("program", f"mean_{key}")),
                    count,
                ),
            ))],
            ["set_attr", "program", f"interaction_residual_{key}", T(
                residual
            )],
        ])
    predicted_normal_load = prediction("program", "normal_load")
    normal_load_residual = Minus(
        outcome_observation("normal_load"),
        predicted_normal_load,
    )
    return {
        "name": "emp_learn_compound_program_interaction_residual",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "enacts_embodied_motor_program", "program"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
            Gt(
                P0("outcome", "request_seq"),
                P0("program", "last_learning_seq"),
            ),
        ),
        "effects": [
            *effects,
            ["set_attr", "program", "prediction_error_energy", T(
                Plus(*error_terms)
            )],
            ["set_attr", "program", "predicted_normal_load", T(
                predicted_normal_load
            )],
            ["set_attr", "program", "relative_normal_load_error", T(
                Div(
                    Abs(normal_load_residual),
                    Plus(Abs(predicted_normal_load), L(0.000001)),
                )
            )],
            ["set_attr", "program", "experience_count", T(count)],
            ["set_attr", "program", "last_learning_seq", T(
                P0("outcome", "request_seq")
            )],
        ],
    }


def reopen_calibration_on_surprise_rule():
    """RESTORED (block DC), and this docstring is the reason it is restored.

    Block CZ replaced this rule's trigger with a change of surprise SHAPE and
    deleted its budget.  The argument was sound and is still sound: the old
    trigger is `prediction_error_energy > compound_surprise_threshold`, an
    unbounded multi-scale quantity against a fixed 2.0, satisfied on 93% of
    actions and survivable only because a monotone budget suppressed it.

    It measured worse and stayed worse.  Ground contact over three faults at
    three episodes: 1/9 before, 4/9 after, and still 4/9 after credit
    assignment (DA) and the adaptation rate (DB) were both added to make it
    affordable.  Both surviving regressions -- saturated_elevator and
    jammed_rudder -- entered here and neither later change touched them.

    So this is a SUBTRACTION, not a retraction of the analysis.  The scaling
    criticism of this trigger stands and is recorded in CY; what is now also
    measured is that the replacement costs three episodes and the two changes
    predicted to rescue it did not.  The shape trigger's own instrumentation
    (`surprise_shape_minted_seq`) is left stamped and unread, so re-landing it
    is one clause rather than a rebuild.
    """
    return {
        "name": "emp_reopen_factorized_calibration_on_compound_surprise",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "has_embodied_motor_program_policy", "policy"],
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "enacts_embodied_motor_program", "program"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(A("episode", "program_mode"), L("synthesis")),
            Eq(
                P0("outcome", "request_seq"),
                P0("episode", "receipt_boundary_seq"),
            ),
            Lt(
                P0("episode", "recalibration_count"),
                P0("policy", "maximum_recalibration_cycles"),
            ),
            Or(
                Not(Gt(
                    P0("policy", "maximum_default_program_reuse_cycles"),
                    L(0.0),
                )),
                Gt(P0("program", "experience_count"), L(2.0)),
            ),
            Or(
                Gt(
                    P0("program", "prediction_error_energy"),
                    P0("policy", "compound_surprise_threshold"),
                ),
                And(
                    Gt(
                        Abs(P0("program", "predicted_normal_load")),
                        P0("policy", "minimum_expected_normal_load"),
                    ),
                    Gt(
                        P0("program", "relative_normal_load_error"),
                        P0("policy", "relative_normal_load_surprise"),
                    ),
                ),
            ),
            Eq(P0("outcome", "surprise_processed"), L(0.0)),
        ),
        "effects": [
            ["set_attr", "episode", "program_mode", "recalibration_marking"],
            ["set_attr", "episode", "calibration_complete", 0.0],
            ["set_attr", "episode", "recalibration_count", T(
                Plus(P0("episode", "recalibration_count"), L(1.0))
            )],
            ["set_attr", "outcome", "surprise_processed", 1.0],
        ],
    }


def mark_models_for_recalibration_rule():
    return {
        "name": "emp_mark_factorized_models_for_recalibration",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": True,
        "match": [
            ["agent", "has_embodied_motor_program_episode", "episode"],
            ["episode", "has_embodied_effector_model", "model"],
        ],
        "where": Eq(
            A("episode", "program_mode"),
            L("recalibration_marking"),
        ),
        "effects": [
            ["set_attr", "model", "recalibration_required", 1.0],
            ["set_attr", "episode", "program_mode", "calibration"],
        ],
    }


def close_receipt_rule():
    return {
        "name": "emp_close_exact_program_receipt",
        "area": "embodied_motor_program_plasticity",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["episode", "has_embodied_motor_program_trial", "trial"],
            ["trial", "enacts_embodied_motor_program", "program"],
            ["trial", "has_embodied_motor_program_outcome", "outcome"],
        ],
        "where": And(
            Eq(P0("outcome", "receipt_verified"), L(1.0)),
            Eq(P0("outcome", "processed"), L(0.0)),
            Eq(
                P0("program", "last_learning_seq"),
                P0("outcome", "request_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "outcome", "processed", 1.0],
            ["set_attr", "trial", "status", "learned"],
            [
                "del_edge",
                "episode",
                "has_embodied_motor_program",
                "program",
            ],
            [
                "add_edge",
                "episode",
                "has_archived_embodied_motor_program",
                "program",
            ],
        ],
    }
def manifest():
    return {
        "id": "embodied_motor_program",
        "version": "1.25.0",
        "depends_on": [
            "embodied_pareto_profile",
            "motor_decision_collapse",
            "embodied_structural_limits",
        ],
        "area": "embodied_motor_program",
        "latency_class": "hard_realtime",
        "description": "Morphology-neutral analysis-by-synthesis over "
        "factorized opaque effectors. The graph constructs arbitrary-width "
        "simultaneous programs, sends the exact program through shared motor "
        "collapse, and learns six-axis consequences conditioned on "
        "body-relative vector flow and delayed power state from receipts. "
        "Specification-grounded structural limits exclude unsafe primitive "
        "calibration and compound programs before release. Flown programs are "
        "indexed BY TYPE AND SHAPE in an EmbodiedMotorProgramShape codebook "
        "(one relation per member: actuator group as predicate, integer "
        "command ordinal as coordinate), grown and collapsed behind the "
        "action and re-armed by motor_codebook_epoch. Optional graph-native "
        "temporal command encoding carries quantisation residuals per opaque "
        "effector group and is disabled unless explicitly enabled.",
        "nodes": [{
            "local_id": 1,
            "type": "EmbodiedMotorProgramPolicy",
            "attrs": {
                "calibration_samples": 2.0,
                "minimum_calibration_flow_speed_squared": 0.5,
                "maximum_recalibration_cycles": 1.0,
                "compound_surprise_threshold": 2.0,
                "minimum_expected_normal_load": 0.005,
                "relative_normal_load_surprise": 0.6,
                "maximum_default_program_reuse_cycles": 0.0,
                "contextual_effector_prediction_enabled": 1.0,
                "parallel_factorized_composition_enabled": 0.0,
                "minimum_composition_improvement": 0.000001,
                "future_manifold_enabled": 0.0,
                "future_manifold_establish_from_seq": 1.0,
                "future_manifold_establish_until_seq": 0.0,
                "future_manifold_projection_budget": float(FUTURE_MANIFOLD_PROJECTION_BUDGET),
                "future_manifold_path_fixed_point_run": float(FUTURE_MANIFOLD_PATH_FIXED_POINT_RUN),
                "future_manifold_physical_horizon": float(FUTURE_MANIFOLD_PHYSICAL_HORIZON),
                "future_manifold_temporal_anchors_enabled": float(FUTURE_MANIFOLD_TEMPORAL_ANCHORS_ENABLED),
                "future_manifold_anchor_growth": float(FUTURE_MANIFOLD_ANCHOR_GROWTH),
                "future_manifold_max_shape_order": float(FUTURE_MANIFOLD_MAX_SHAPE_ORDER),
                "future_manifold_max_refinements": float(FUTURE_MANIFOLD_MAX_REFINEMENTS),
                "future_manifold_enclosure_width_floor": float(FUTURE_MANIFOLD_ENCLOSURE_WIDTH_FLOOR),
                "forward_weight": 1.0,
                "lateral_weight": 1.0,
                "turn_weight": 1.0,
                "normal_load_weight": 0.01,
                "drag_weight": 0.01,
                "energy_weight": 0.001,
                "activation_weight": 0.02,
                "temporal_command_encoding_enabled": 0.0,
            },
        }],
        "edges": [{
            "src": {"role": "agent_root"},
            "type": "has_embodied_motor_program_policy",
            "tgt": {"local": 1},
            "attrs": {},
        }],
        "productions": [
            {
                "provenance": "embodied_motor_program:episode",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_motor_program_episode",
                "tgt": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
            },
            {
                # The surprise-shape index is MATCHED on, not merely written
                # to, so its edge type must be a declared production -- an
                # undeclared edge can be added but never binds a rule.
                "provenance": "embodied_motor_program:surprise_shape",
                "src": {"type": "Agent", "var": "agent"},
                "edge_type": "has_embodied_surprise_shape_library",
                "tgt": {"type": SURPRISE_SHAPE_TYPE, "var": "surprise"},
            },
            {
                "provenance": "embodied_motor_program:model",
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
                "edge_type": "has_embodied_effector_model",
                "tgt": {"type": "EmbodiedEffectorModel", "var": "model"},
            },
            {
                "provenance": "embodied_motor_program:program",
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
                "edge_type": "has_embodied_motor_program",
                "tgt": {"type": "EmbodiedMotorProgram", "var": "program"},
            },
            {
                "provenance": "embodied_motor_program:program_archive",
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
                "edge_type": "has_archived_embodied_motor_program",
                "tgt": {"type": "EmbodiedMotorProgram", "var": "program"},
            },
            {
                "provenance": "embodied_motor_program:program_default",
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
                "edge_type": "has_default_embodied_motor_program",
                "tgt": {"type": "EmbodiedMotorProgram", "var": "program"},
            },
            {
                "provenance": "embodied_motor_program:member",
                "src": {"type": "EmbodiedMotorProgram", "var": "program"},
                "edge_type": "includes_embodied_effector_model",
                "tgt": {"type": "EmbodiedEffectorModel", "var": "model"},
            },
            {
                "provenance": "embodied_motor_program:resume",
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
                "edge_type": "resumes_embodied_motor_program",
                "tgt": {"type": "EmbodiedMotorProgram", "var": "program"},
            },
            {
                "provenance": "embodied_motor_program:trial",
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
                "edge_type": "has_embodied_motor_program_trial",
                "tgt": {"type": "EmbodiedMotorProgramTrial", "var": "trial"},
            },
            {
                "provenance": "embodied_motor_program:temporal_state",
                "src": {"type": "EmbodiedMotorProgramEpisode", "var": "episode"},
                "edge_type": "has_temporal_command_state",
                "tgt": {"type": "EmbodiedTemporalCommandState", "var": "state"},
            },
            {
                "provenance": "embodied_motor_program:temporal_encoded_member",
                "src": {"type": "EmbodiedMotorProgramTrial", "var": "trial"},
                "edge_type": "temporal_encodes_model",
                "tgt": {"type": "EmbodiedEffectorModel", "var": "model"},
            },
            {
                "provenance": "embodied_motor_program:temporal_command",
                "src": {"type": "EmbodiedMotorProgramTrial", "var": "trial"},
                "edge_type": "has_temporal_command",
                "tgt": {"type": "EmbodiedTemporalCommand", "var": "command"},
            },
            {
                "provenance": "embodied_motor_program:neutral_command",
                "src": {"type": "EmbodiedMotorProgramTrial", "var": "trial"},
                "edge_type": "has_embodied_motor_command",
                "tgt": {"type": "EmbodiedMotorCommand", "var": "command"},
            },
            {
                "provenance": "embodied_motor_program:bridge_issued_command",
                "src": {"type": "EmbodiedMotorProgramTrial", "var": "trial"},
                "edge_type": "has_control_issued_command",
                "tgt": {"type": "ControlIssuedCompoundCommand", "var": "issued"},
            },
            {
                "provenance": "embodied_motor_program:bridge_opaque_command",
                "src": {"type": "ControlIssuedCompoundCommand", "var": "issued"},
                "edge_type": "has_control_opaque_command",
                "tgt": {"type": "ControlOpaqueCommand", "var": "command"},
            },
            {
                "provenance": "embodied_motor_program:bridge_observed_delta",
                "src": {"type": "EmbodiedMotorProgramTrial", "var": "trial"},
                "edge_type": "has_control_observed_delta",
                "tgt": {"type": "ControlObservedStateDelta", "var": "observed"},
            },
            {
                "provenance": "embodied_motor_program:bridge_axis_receipt",
                "src": {"type": "ControlObservedStateDelta", "var": "observed"},
                "edge_type": "has_control_axis_receipt",
                "tgt": {"type": "ControlAxisReceipt", "var": "axis"},
            },
        ],
        "rules": [
            temporal_command_state_rule(),
            temporal_command_reset_rule(),
            gate_distal_goals_during_aerodynamic_departure_rule(),
            derive_active_rate_stabilization_targets_rule(),
            complete_specification_prior_initialization_rule(),
            retire_old_options_rule(),
            share_group_context_transition_rule(),
            open_flow_excitation_program_rule(),
            open_calibration_program_rule(),
            complete_calibration_rule(),
            reuse_internalized_program_rule(),
            async_release_trusted_default_rule(),
            async_close_background_plan_rule(),
            open_synthesized_program_rule(),
            native_mark_composition_choice_rule(),
            render_mark_group_choice_rule(),
            render_open_program_rule(),
            render_attach_member_rule(),
            render_close_program_rule(),
            expand_factorized_groups_in_parallel_rule(),
            expand_program_rule(),
            reconcile_program_width_rule(),
            resume_program_rule(),
            close_program_rule(),
            establish_future_manifold_rule(),
            open_program_trial_rule(),
            copy_trial_members_rule(),
            emit_neutral_for_empty_trial_rule(),
            temporal_encode_trial_member_rule(),
            temporal_emit_neutral_for_empty_trial_rule(),
            close_temporal_command_trial_rule(),
            share_slope_across_command_levels_rule(),
            learn_uncommanded_contributor_rule(),
            learn_unmovable_contributor_rule(),
            learn_primitive_rule(),
            learn_program_rule(),
            reopen_calibration_on_surprise_rule(),
            mark_models_for_recalibration_rule(),
            close_receipt_rule(),
            internalize_synthesized_program_rule(),
            retire_superseded_program_default_rule(),
            signature_internalized_program_rule(),
            grow_motor_program_shape_rule(),
            index_surprise_shape_rule(),
            count_stable_surprise_response_rule(),
            vary_surprise_response_rule(),
            condense_surprise_reflex_rule(),
            release_condensed_reflex_rule(),
            fork_regime_local_model_rule(),
            arm_condensed_reflex_rule(),
            enact_motor_reflex_buy_time_rule(),
            # recognize_duplicate_motor_program_shape_rule() is deliberately
            # NOT installed -- measured >11x on the fault scenarios.  See the
            # comment above its definition.
        ],
        # THE REFLEX RUNG.  An observation -> motor program mapping that does
        # not deliberate: no decode, no selection, no composition.  Its purpose
        # is to BUY TIME for cognition to catch up, not to solve the problem --
        # you step aside and catch the arrow, and someone is still shooting
        # arrows at you, but you now have time to think about it.
        #
        # Shipped as seed data via the `"reflexes"` manifest key, the
        # `question_pursue` precedent (`seeds/question_driving.json`):
        # `load_seed_manifest` installs Reflex nodes with their stimulus_term
        # subgraphs and `fire_reflexes` discovers them.
        #
        # ARMED BY ABSENCE, so this cannot fire until a consumer asks for it:
        # `motor_reflex_armed` is unset everywhere, reads 0 through P0, and the
        # stimulus counts zero episodes.  A consumer that never declares it is
        # byte-identical.
        #
        # TWO THINGS ARE STILL MISSING and neither is in this seed:
        #   1. the response executor.  `fire_reflexes` does
        #      `reflex_responses.get(response)` and skips on None, so an
        #      unregistered name is safe -- it records as fired and does
        #      nothing.  Safe, and not yet useful.
        #   2. REFLEXES DO NOT FIRE AUTOMATICALLY, AND THAT IS THE DEFECT.
        #      `agent.tick()` is `run_cycle("default")` and nothing else;
        #      `fire_reflexes` is a SEPARATE Python method, called only from
        #      `cognitive_tick`, which this consumer never calls.
        #
        #      The fix is NOT to make the F-16 adapter call it.  A reflex is not
        #      different in kind from anything else the agent does -- it is
        #      observation -> motor program with no deliberation between -- so it
        #      belongs in the engine's own cycle, firing automatically, not in a
        #      Python method every consumer must remember to pump.  Firing IS
        #      agent behaviour, and agent behaviour does not live in the adapter
        #      (the root CLAUDE.md rule).  A consumer that has to opt in to its
        #      own reflexes does not have reflexes; it has a slow path it may
        #      choose to take, which is the opposite of the point.
        #
        # Recorded rather than hidden: the seed now HAS the rung, and what stands
        # between having it and using it is an executor and an engine that fires
        # reflexes as part of its cycle.
        "reflexes": [
            {
                "name": "motor_reflex_buy_time",
                "stimulus": {
                    "type": "Gte",
                    "a": {
                        "type": "Count",
                        "source": {
                            "type": "Filter",
                            "source": {
                                "type": "NodesOfType",
                                "node_type": "EmbodiedMotorProgramEpisode",
                            },
                            "var_name": "ep",
                            "predicate": {
                                "type": "Gt",
                                "a": {
                                    "type": "Attr",
                                    "node": {"type": "Var", "name": "ep"},
                                    "key": "motor_reflex_armed",
                                },
                                "b": {"type": "Lit", "value": 0.5},
                            },
                        },
                    },
                    "b": {"type": "Lit", "value": 1},
                },
                "response": "motor_reflex_buy_time",
                "refractory_ticks": 0,
                # ORDER 0 FIRES BY ITSELF.  `autonomous` moves this reflex off
                # the host dispatch loop and into the engine's cycle, where it
                # runs at the top of every tick before a single rule matches.
                # Its response is `emp_enact_motor_reflex_buy_time`, a rule --
                # so nothing outside the graph is involved in firing OR in
                # responding, and no adapter has to remember to call anything.
                "autonomous": 1,
            },
        ],
    }


def main() -> int:
    out = ROOT / "seeds" / "embodied_motor_program.json"
    payload = manifest()
    out.write_text(json.dumps(payload, indent=1) + "\n", encoding="utf-8")
    json.loads(out.read_text(encoding="utf-8"))
    print(f"wrote {out.relative_to(ROOT)} ({len(payload['rules'])} rules)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
