"""Generate the graph-native fast/slow cognition loop for full racing."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(var, key): return {"type": "Attr", "node": V(var), "key": key}
def AttrOf(node, key): return {"type": "Attr", "node": node, "key": key}
def P0(var, key): return Plus(A(var, key), L(0.0))
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Mul(a, b): return {"type": "Times", "items": [a, b]}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Abs(value): return {"type": "Abs", "arg": value}
def Sqrt(value): return {"type": "Sqrt", "arg": value}
def Min(*items): return {"type": "Min", "items": list(items)}
def Max(*items): return {"type": "Max", "items": list(items)}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def If(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}
def Neighbours(var, edge):
    return {
        "type": "Neighbours",
        "node": V(var),
        "edge_type": edge,
        "any_type": False,
    }
def Filter(source, var, predicate):
    return {
        "type": "Filter",
        "source": source,
        "var_name": var,
        "predicate": predicate,
    }
def Exists(source, var, predicate):
    return {
        "type": "Exists",
        "source": source,
        "var_name": var,
        "predicate": predicate,
    }
def Argmin(source, var, value, default):
    return {
        "type": "Argmin",
        "source": source,
        "var_name": var,
        "value": value,
        "default": default,
    }
def T(term): return {"__term__": term}


def Clamp(value, lower, upper):
    return Min(Max(value, lower), upper)


STRATEGIES = Neighbours("policy", "has_racing_strategy_candidate")


def _dominates(other: str, candidate: str):
    """True Pareto domination: no worse on every axis, better on one."""
    no_worse = And(
        Not(Lt(A(other, "pace_fraction"), A(candidate, "pace_fraction"))),
        Not(Gt(A(other, "fuel_cost"), A(candidate, "fuel_cost"))),
        Not(Gt(A(other, "tyre_cost"), A(candidate, "tyre_cost"))),
        Not(Gt(A(other, "contact_risk"), A(candidate, "contact_risk"))),
    )
    strictly_better = Or(
        Gt(A(other, "pace_fraction"), A(candidate, "pace_fraction")),
        Lt(A(other, "fuel_cost"), A(candidate, "fuel_cost")),
        Lt(A(other, "tyre_cost"), A(candidate, "tyre_cost")),
        Lt(A(other, "contact_risk"), A(candidate, "contact_risk")),
    )
    return And(
        Not(Eq(A(other, "ordinal"), A(candidate, "ordinal"))),
        no_worse,
        strictly_better,
    )


PARETO_STRATEGIES = Filter(
    STRATEGIES,
    "candidate",
    Not(Exists(
        STRATEGIES,
        "other",
        _dominates("other", "candidate"),
    )),
)


def _fuel_pressure():
    required = Mul(
        Mul(
            P0("episode", "state_remaining_distance_m"),
            P0("episode", "learned_fuel_l_per_m"),
        ),
        P0("policy", "finish_fuel_reserve_factor"),
    )
    return Clamp(
        Div(
            required,
            Max(P0("episode", "state_fuel_l"), P0("policy", "fuel_floor_l")),
        ),
        L(0.0),
        P0("policy", "maximum_resource_pressure"),
    )


def _tyre_pressure():
    projected_condition = Minus(
        P0("episode", "state_tyre_condition"),
        Mul(
            P0("episode", "state_remaining_distance_m"),
            P0("episode", "learned_tyre_wear_per_m"),
        ),
    )
    reserve_shortfall = Max(
        Minus(
            P0("policy", "finish_tyre_condition_reserve"),
            projected_condition,
        ),
        L(0.0),
    )
    thermal_excess = Max(
        Minus(
            Abs(Minus(
                P0("episode", "state_tyre_temperature_c"),
                P0("policy", "optimal_tyre_temperature_c"),
            )),
            P0("policy", "thermal_deadband_c"),
        ),
        L(0.0),
    )
    return Clamp(
        Plus(
            Mul(P0("policy", "tyre_reserve_pressure_gain"), reserve_shortfall),
            Mul(P0("policy", "tyre_thermal_pressure_gain"), thermal_excess),
        ),
        L(0.0),
        P0("policy", "maximum_resource_pressure"),
    )


def _risk_pressure():
    return Clamp(
        Plus(
            Mul(
                P0("policy", "damage_risk_pressure_gain"),
                P0("episode", "state_damage"),
            ),
            Mul(
                P0("policy", "surprise_risk_pressure_gain"),
                P0("episode", "model_surprise"),
            ),
            Mul(
                P0("policy", "slip_risk_pressure_gain"),
                Max(
                    Abs(P0("episode", "state_slip_angle")),
                    Abs(P0("episode", "state_front_slip")),
                    Abs(P0("episode", "state_rear_slip")),
                ),
            ),
        ),
        L(0.0),
        P0("policy", "maximum_resource_pressure"),
    )


def _race_urgency():
    return Clamp(
        Minus(
            L(1.0),
            Div(
                P0("episode", "state_remaining_distance_m"),
                Max(
                    P0("episode", "state_total_distance_m"),
                    P0("policy", "distance_floor_m"),
                ),
            ),
        ),
        L(0.0),
        L(1.0),
    )


def _passing_opportunity():
    return Clamp(
        Mul(
            Div(
                Max(P0("episode", "state_opponent_closing_m_s"), L(0.0)),
                Max(
                    P0("episode", "state_opponent_gap_m"),
                    P0("policy", "distance_floor_m"),
                ),
            ),
            P0("policy", "passing_opportunity_gain"),
        ),
        L(0.0),
        L(1.0),
    )


def _strategy_aspirations():
    fuel_pressure = _fuel_pressure()
    tyre_pressure = _tyre_pressure()
    risk_pressure = _risk_pressure()
    urgency = _race_urgency()
    opportunity = _passing_opportunity()
    desired_pace = Clamp(
        Plus(
            P0("policy", "base_pace_aspiration"),
            Mul(P0("policy", "finish_pace_gain"), urgency),
            Mul(P0("policy", "opportunity_pace_gain"), opportunity),
            Minus(
                L(0.0),
                Plus(
                    Mul(P0("policy", "fuel_pace_penalty"), fuel_pressure),
                    Mul(P0("policy", "tyre_pace_penalty"), tyre_pressure),
                    Mul(P0("policy", "risk_pace_penalty"), risk_pressure),
                ),
            ),
        ),
        P0("policy", "minimum_pace_aspiration"),
        P0("policy", "maximum_pace_aspiration"),
    )
    desired_fuel_cost = Clamp(
        Minus(
            L(1.0),
            Mul(P0("policy", "fuel_cost_pressure_gain"), fuel_pressure),
        ),
        P0("policy", "minimum_cost_aspiration"),
        L(1.0),
    )
    desired_tyre_cost = Clamp(
        Minus(
            L(1.0),
            Mul(P0("policy", "tyre_cost_pressure_gain"), tyre_pressure),
        ),
        P0("policy", "minimum_cost_aspiration"),
        L(1.0),
    )
    desired_risk = Clamp(
        Plus(
            P0("policy", "base_risk_aspiration"),
            Mul(P0("policy", "opportunity_risk_gain"), opportunity),
            Mul(P0("policy", "finish_risk_gain"), urgency),
            Minus(
                L(0.0),
                Mul(P0("policy", "risk_pressure_penalty"), risk_pressure),
            ),
        ),
        P0("policy", "minimum_risk_aspiration"),
        L(1.0),
    )
    return (
        desired_pace,
        desired_fuel_cost,
        desired_tyre_cost,
        desired_risk,
        fuel_pressure,
        tyre_pressure,
        risk_pressure,
    )


def _strategy_loss(candidate: str):
    (
        desired_pace,
        desired_fuel,
        desired_tyre,
        desired_risk,
        fuel_pressure,
        tyre_pressure,
        risk_pressure,
    ) = _strategy_aspirations()
    return Plus(
        Mul(
            P0("policy", "pace_objective_weight"),
            Abs(Minus(A(candidate, "pace_fraction"), desired_pace)),
        ),
        Mul(
            Plus(
                P0("policy", "base_resource_weight"),
                Mul(P0("policy", "fuel_objective_gain"), fuel_pressure),
            ),
            Abs(Minus(A(candidate, "fuel_cost"), desired_fuel)),
        ),
        Mul(
            Plus(
                P0("policy", "base_resource_weight"),
                Mul(P0("policy", "tyre_objective_gain"), tyre_pressure),
            ),
            Abs(Minus(A(candidate, "tyre_cost"), desired_tyre)),
        ),
        Mul(
            Plus(
                P0("policy", "base_risk_weight"),
                Mul(P0("policy", "risk_objective_gain"), risk_pressure),
            ),
            Abs(Minus(A(candidate, "contact_risk"), desired_risk)),
        ),
    )


def strategy_pareto_rule():
    best = Argmin(
        PARETO_STRATEGIES,
        "candidate",
        _strategy_loss("candidate"),
        V("episode"),
    )
    (
        desired_pace,
        desired_fuel,
        desired_tyre,
        desired_risk,
        fuel_pressure,
        tyre_pressure,
        risk_pressure,
    ) = _strategy_aspirations()
    fuel_required = Mul(
        Mul(
            P0("episode", "state_remaining_distance_m"),
            P0("episode", "learned_fuel_l_per_m"),
        ),
        P0("policy", "finish_fuel_reserve_factor"),
    )
    projected_tyre = Minus(
        P0("episode", "state_tyre_condition"),
        Mul(
            P0("episode", "state_remaining_distance_m"),
            P0("episode", "learned_tyre_wear_per_m"),
        ),
    )
    tyre_service_pressure = Mul(
        P0("policy", "tyre_reserve_pressure_gain"),
        Max(
            Minus(
                P0("policy", "finish_tyre_condition_reserve"),
                projected_tyre,
            ),
            L(0.0),
        ),
    )
    pit_pressure = Max(
        fuel_pressure,
        tyre_service_pressure,
        Mul(
            P0("episode", "state_damage"),
            P0("policy", "damage_service_pressure_gain"),
        ),
    )
    service_window_open = Gt(
        P0("episode", "state_remaining_distance_m"),
        Mul(
            P0("episode", "state_total_distance_m"),
            P0("policy", "minimum_service_remaining_fraction"),
        ),
    )
    pit_required = Or(
        Gt(fuel_required, P0("episode", "state_fuel_l")),
        Lt(projected_tyre, P0("policy", "pit_tyre_condition_threshold")),
        And(
            service_window_open,
            Gt(pit_pressure, P0("candidate", "pit_threshold")),
        ),
    )
    return {
        "name": "race_system2_dynamic_pareto_envelope",
        "area": "racing_strategy_cortex",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "has_racing_policy", "policy"],
            ["agent", "has_racing_episode", "episode"],
            ["policy", "has_racing_strategy_candidate", "candidate"],
        ],
        "where": And(
            Gt(
                P0("episode", "request_seq"),
                Plus(
                    P0("episode", "strategy_decision_seq"),
                    P0("policy", "strategy_interval_ticks"),
                ),
            ),
            Eq(
                P0("candidate", "ordinal"),
                AttrOf(best, "ordinal"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "strategy_ordinal", T(P0("candidate", "ordinal"))],
            ["set_attr", "episode", "strategy_pace_fraction", T(P0("candidate", "pace_fraction"))],
            ["set_attr", "episode", "strategy_fuel_cost", T(P0("candidate", "fuel_cost"))],
            ["set_attr", "episode", "strategy_tyre_cost", T(P0("candidate", "tyre_cost"))],
            ["set_attr", "episode", "strategy_contact_risk", T(P0("candidate", "contact_risk"))],
            ["set_attr", "episode", "strategy_aggression", T(P0("candidate", "aggression"))],
            ["set_attr", "episode", "strategy_pit_threshold", T(P0("candidate", "pit_threshold"))],
            ["set_attr", "episode", "fuel_pressure", T(fuel_pressure)],
            ["set_attr", "episode", "tyre_pressure", T(tyre_pressure)],
            ["set_attr", "episode", "risk_pressure", T(risk_pressure)],
            ["set_attr", "episode", "pit_pressure", T(pit_pressure)],
            ["set_attr", "episode", "pace_aspiration", T(desired_pace)],
            ["set_attr", "episode", "fuel_cost_aspiration", T(desired_fuel)],
            ["set_attr", "episode", "tyre_cost_aspiration", T(desired_tyre)],
            ["set_attr", "episode", "risk_aspiration", T(desired_risk)],
            ["set_attr", "episode", "pit_commit", T(If(pit_required, L(1.0), L(0.0)))],
            ["set_attr", "episode", "strategy_decision_seq", T(P0("episode", "request_seq"))],
        ],
    }


def _effective_grip():
    thermal_error = Abs(Minus(
        P0("episode", "state_tyre_temperature_c"),
        P0("policy", "optimal_tyre_temperature_c"),
    ))
    thermal_retention = Clamp(
        Minus(
            L(1.0),
            Mul(
                P0("policy", "thermal_grip_loss_per_c"),
                Max(
                    Minus(
                        thermal_error,
                        P0("policy", "thermal_deadband_c"),
                    ),
                    L(0.0),
                ),
            ),
        ),
        P0("policy", "minimum_thermal_retention"),
        L(1.0),
    )
    return Mul(
        Mul(
            Min(
                P0("episode", "learned_grip"),
                P0("episode", "state_surface_grip"),
            ),
            P0("episode", "state_tyre_condition"),
        ),
        thermal_retention,
    )


def _curvature_demand():
    return Max(
        Abs(P0("episode", "state_curvature_now")),
        P0("episode", "state_curvature_envelope_near"),
        Mul(
            P0("policy", "middle_curvature_weight"),
            P0("episode", "state_curvature_envelope_middle"),
        ),
        Mul(
            P0("policy", "far_curvature_weight"),
            P0("episode", "state_curvature_envelope_far"),
        ),
    )


def _geometric_speed_limit():
    return Sqrt(Div(
        Mul(
            Mul(
                Mul(_effective_grip(), P0("policy", "gravity_m_s2")),
                P0("policy", "lateral_accel_margin"),
            ),
            Plus(
                P0("policy", "minimum_tyre_utilization"),
                Mul(
                    P0("policy", "strategy_tyre_utilization_gain"),
                    P0("episode", "strategy_tyre_cost"),
                ),
            ),
        ),
        Max(
            _curvature_demand(),
            P0("policy", "curvature_floor_inv_m"),
        ),
    ))


def _traffic_speed_limit():
    overlap = Lt(
        Abs(P0("episode", "state_opponent_lateral_m")),
        P0("policy", "opponent_overlap_width_m"),
    )
    close = Lt(
        P0("episode", "state_opponent_gap_m"),
        P0("policy", "opponent_reaction_distance_m"),
    )
    following_limit = Max(
        P0("policy", "minimum_speed_m_s"),
        Minus(
            Minus(
                P0("episode", "state_opponent_speed_m_s"),
                Mul(
                    P0("policy", "closing_speed_gain"),
                    Max(
                        P0("episode", "state_opponent_closing_m_s"),
                        L(0.0),
                    ),
                ),
            ),
            Mul(
                P0("policy", "following_distance_gain"),
                Max(
                    Minus(
                        P0("policy", "opponent_reaction_distance_m"),
                        P0("episode", "state_opponent_gap_m"),
                    ),
                    L(0.0),
                ),
            ),
        ),
    )
    return If(
        And(overlap, close),
        following_limit,
        P0("policy", "maximum_speed_m_s"),
    )


def _target_speed():
    stability_limit = If(
        Gt(
            Max(
                Abs(P0("episode", "state_slip_angle")),
                Abs(P0("episode", "state_front_slip")),
                Abs(P0("episode", "state_rear_slip")),
            ),
            P0("policy", "slip_intervention_rad"),
        ),
        Mul(
            P0("episode", "state_speed_m_s"),
            P0("policy", "instability_speed_retention"),
        ),
        P0("policy", "maximum_speed_m_s"),
    )
    damage_limit = Mul(
        P0("policy", "maximum_speed_m_s"),
        Max(
            P0("policy", "minimum_damage_speed_retention"),
            Minus(
                L(1.0),
                Mul(
                    P0("policy", "damage_speed_penalty"),
                    P0("episode", "model_surprise"),
                ),
            ),
        ),
    )
    unconstrained = Max(
        P0("policy", "minimum_speed_m_s"),
        Min(
            Mul(
                _geometric_speed_limit(),
                P0("episode", "strategy_pace_fraction"),
            ),
            _traffic_speed_limit(),
            stability_limit,
            damage_limit,
            Mul(
                P0("policy", "maximum_speed_m_s"),
                P0("episode", "strategy_pace_fraction"),
            ),
        ),
    )
    return If(
        Gt(P0("episode", "pit_commit"), L(0.5)),
        Min(unconstrained, P0("policy", "pit_lane_speed_m_s")),
        unconstrained,
    )


def _desired_steering():
    normalized_lateral = Div(
        P0("episode", "state_track_lateral_m"),
        Max(
            P0("episode", "state_track_half_width_m"),
            P0("policy", "distance_floor_m"),
        ),
    )
    expected_yaw_rate = Mul(
        P0("episode", "state_speed_m_s"),
        P0("episode", "state_curvature_near"),
    )
    path_command = Plus(
        Mul(
            P0("policy", "curvature_steering_gain"),
            P0("episode", "state_curvature_near"),
        ),
        Mul(
            P0("policy", "heading_steering_gain"),
            P0("episode", "state_heading_error_rad"),
        ),
        Mul(
            P0("policy", "lateral_steering_gain"),
            Minus(L(0.0), normalized_lateral),
        ),
    )
    stability_command = Plus(
        Mul(
            P0("policy", "slip_countersteer_gain"),
            Minus(L(0.0), P0("episode", "state_slip_angle")),
        ),
        Mul(
            P0("policy", "yaw_damping_gain"),
            Minus(
                expected_yaw_rate,
                P0("episode", "state_yaw_rate_rad_s"),
            ),
        ),
    )
    traffic_bias = If(
        And(
            Lt(
                P0("episode", "state_opponent_gap_m"),
                P0("policy", "overtake_commit_distance_m"),
            ),
            Lt(
                Abs(P0("episode", "state_opponent_lateral_m")),
                P0("policy", "opponent_overlap_width_m"),
            ),
        ),
        Mul(
            Mul(
                P0("policy", "overtake_lateral_gain"),
                P0("episode", "strategy_aggression"),
            ),
            If(
                Gt(P0("episode", "state_opponent_lateral_m"), L(0.0)),
                L(-1.0),
                L(1.0),
            ),
        ),
        L(0.0),
    )
    authority_compensation = Div(
        Plus(path_command, stability_command, traffic_bias),
        Max(
            P0("episode", "learned_steering_response"),
            P0("policy", "minimum_steering_response"),
        ),
    )
    return Clamp(authority_compensation, L(-1.0), L(1.0))


def fast_control_rule():
    target_speed = _target_speed()
    steering = _desired_steering()
    speed_error = Minus(
        target_speed,
        P0("episode", "state_speed_m_s"),
    )
    instability = Max(
        Minus(
            Abs(P0("episode", "state_slip_angle")),
            P0("policy", "slip_intervention_rad"),
        ),
        L(0.0),
    )
    throttle = If(
        Gt(speed_error, L(0.0)),
        Clamp(
            Mul(
                P0("policy", "throttle_speed_gain"),
                speed_error,
            ),
            L(0.0),
            L(1.0),
        ),
        L(0.0),
    )
    stability_brake = If(
        Gt(
            P0("episode", "state_speed_m_s"),
            P0("policy", "minimum_stability_brake_speed_m_s"),
        ),
        Mul(P0("policy", "stability_brake_gain"), instability),
        L(0.0),
    )
    brake = Clamp(
        Plus(
            Mul(
                P0("policy", "brake_speed_gain"),
                Max(Minus(L(0.0), speed_error), L(0.0)),
            ),
            stability_brake,
        ),
        L(0.0),
        L(1.0),
    )
    # Brake has priority; the graph, not the host, enforces pedal exclusion.
    throttle_cap = Plus(
        P0("policy", "minimum_throttle_cap"),
        Mul(
            P0("policy", "strategy_throttle_cap_gain"),
            P0("episode", "strategy_fuel_cost"),
        ),
    )
    exclusive_throttle = If(
        Gt(brake, L(0.0)),
        L(0.0),
        Min(throttle, throttle_cap),
    )
    differential_yaw_request = Clamp(
        Mul(
            Mul(
                P0("episode", "differential_authority"),
                P0("policy", "torque_vectoring_yaw_gain"),
            ),
            steering,
        ),
        L(-1.0),
        L(1.0),
    )
    front_drive_delta = Mul(
        Mul(
            exclusive_throttle,
            P0("policy", "front_drive_vectoring_gain"),
        ),
        differential_yaw_request,
    )
    rear_drive_delta = Mul(
        Mul(
            exclusive_throttle,
            P0("policy", "rear_drive_vectoring_gain"),
        ),
        differential_yaw_request,
    )
    front_brake_delta = Mul(
        Mul(
            brake,
            P0("policy", "front_brake_vectoring_gain"),
        ),
        differential_yaw_request,
    )
    rear_brake_delta = Mul(
        Mul(
            brake,
            P0("policy", "rear_brake_vectoring_gain"),
        ),
        differential_yaw_request,
    )
    aero_demand = Clamp(
        Mul(
            P0("policy", "aero_demand_gain"),
            Mul(
                _curvature_demand(),
                Mul(
                    P0("episode", "state_speed_m_s"),
                    P0("episode", "state_speed_m_s"),
                ),
            ),
        ),
        P0("policy", "minimum_aero_command"),
        L(1.0),
    )
    front_wing = Clamp(
        Plus(
            aero_demand,
            Mul(P0("policy", "braking_front_aero_gain"), brake),
        ),
        L(0.0),
        L(1.0),
    )
    rear_wing = Clamp(
        Plus(
            aero_demand,
            Mul(P0("policy", "stability_rear_aero_gain"), instability),
        ),
        L(0.0),
        L(1.0),
    )
    selected_gear = If(
        Gt(
            P0("episode", "state_engine_rpm"),
            P0("policy", "upshift_rpm"),
        ),
        Min(
            Plus(P0("episode", "state_gear"), L(1.0)),
            P0("policy", "maximum_gear"),
        ),
        If(
            And(
                Lt(
                    P0("episode", "state_engine_rpm"),
                    P0("policy", "downshift_rpm"),
                ),
                Gt(P0("episode", "state_gear"), L(1.0)),
            ),
            Minus(P0("episode", "state_gear"), L(1.0)),
            P0("episode", "state_gear"),
        ),
    )
    return {
        "name": "race_system1_coupled_fast_control",
        "area": "racing_motor_cortex",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_racing_policy", "policy"],
            ["agent", "has_racing_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "decision_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "target_speed_m_s", T(target_speed)],
            ["set_attr", "episode", "command_steering", T(steering)],
            ["set_attr", "episode", "command_throttle", T(exclusive_throttle)],
            ["set_attr", "episode", "command_brake", T(brake)],
            ["set_attr", "episode", "command_differential_yaw_request", T(
                differential_yaw_request
            )],
            ["set_attr", "episode", "command_drive_front_left", T(
                Clamp(
                    Minus(exclusive_throttle, front_drive_delta),
                    L(0.0),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "command_drive_front_right", T(
                Clamp(
                    Plus(exclusive_throttle, front_drive_delta),
                    L(0.0),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "command_drive_rear_left", T(
                Clamp(
                    Minus(exclusive_throttle, rear_drive_delta),
                    L(0.0),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "command_drive_rear_right", T(
                Clamp(
                    Plus(exclusive_throttle, rear_drive_delta),
                    L(0.0),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "command_brake_front_left", T(
                Clamp(
                    Plus(brake, front_brake_delta),
                    L(0.0),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "command_brake_front_right", T(
                Clamp(
                    Minus(brake, front_brake_delta),
                    L(0.0),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "command_brake_rear_left", T(
                Clamp(
                    Plus(brake, rear_brake_delta),
                    L(0.0),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "command_brake_rear_right", T(
                Clamp(
                    Minus(brake, rear_brake_delta),
                    L(0.0),
                    L(1.0),
                )
            )],
            ["set_attr", "episode", "command_front_wing", T(front_wing)],
            ["set_attr", "episode", "command_rear_wing", T(rear_wing)],
            ["set_attr", "episode", "command_gear", T(selected_gear)],
            ["set_attr", "episode", "command_pit", T(P0("episode", "pit_commit"))],
            ["set_attr", "episode", "decision_seq", T(P0("episode", "request_seq"))],
            ["set_attr", "episode", "action_ready", 1.0],
        ],
    }


def learn_receipt_rule():
    action_magnitude = Abs(P0("episode", "receipt_steering_command"))
    measured_response = Div(
        Abs(P0("episode", "receipt_yaw_rate_delta")),
        Max(action_magnitude, P0("policy", "command_floor")),
    )
    expected_response = Mul(
        P0("episode", "learned_steering_response"),
        action_magnitude,
    )
    steering_surprise = Abs(Minus(
        Abs(P0("episode", "receipt_yaw_rate_delta")),
        expected_response,
    ))
    observed_grip = Clamp(
        Div(
            Abs(P0("episode", "receipt_lateral_accel_m_s2")),
            P0("policy", "gravity_m_s2"),
        ),
        P0("policy", "minimum_grip_estimate"),
        P0("policy", "maximum_grip_estimate"),
    )
    old_weight = P0("policy", "model_retention")
    new_weight = Minus(L(1.0), old_weight)
    return {
        "name": "race_learn_dynamics_from_exact_receipt",
        "area": "racing_sensorimotor_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "has_racing_policy", "policy"],
            ["agent", "has_racing_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "receipt_pending"), L(1.0)),
            Gt(action_magnitude, P0("policy", "command_floor")),
            Gt(
                Abs(P0("episode", "receipt_lateral_accel_m_s2")),
                P0("policy", "grip_learning_accel_m_s2"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "learned_steering_response", T(
                Plus(
                    Mul(old_weight, P0("episode", "learned_steering_response")),
                    Mul(new_weight, measured_response),
                )
            )],
            ["set_attr", "episode", "learned_grip", T(
                Max(P0("episode", "learned_grip"), observed_grip)
            )],
            ["set_attr", "episode", "model_surprise", T(
                Plus(
                    Mul(old_weight, P0("episode", "model_surprise")),
                    Mul(new_weight, steering_surprise),
                )
            )],
            ["set_attr", "episode", "receipt_pending", 0.0],
        ],
    }


def close_unexcited_receipt_rule():
    return {
        "name": "race_close_unexcited_receipt",
        "area": "racing_sensorimotor_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "has_racing_policy", "policy"],
            ["agent", "has_racing_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "receipt_pending"), L(1.0)),
            Lt(
                Abs(P0("episode", "receipt_steering_command")),
                P0("policy", "command_floor"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "receipt_pending", 0.0],
        ],
    }


def learn_resource_rates_rule():
    distance = P0("episode", "receipt_distance_delta_m")
    measured_fuel_rate = Div(
        Max(P0("episode", "receipt_fuel_used_l"), L(0.0)),
        Max(distance, P0("policy", "distance_floor_m")),
    )
    measured_wear_rate = Div(
        Max(P0("episode", "receipt_tyre_wear"), L(0.0)),
        Max(distance, P0("policy", "distance_floor_m")),
    )
    retention = P0("policy", "resource_model_retention")
    innovation = Minus(L(1.0), retention)
    return {
        "name": "race_learn_resource_rates_from_exact_receipt",
        "area": "racing_strategy_learning",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "has_racing_policy", "policy"],
            ["agent", "has_racing_episode", "episode"],
        ],
        "where": And(
            Gt(
                P0("episode", "resource_receipt_seq"),
                P0("episode", "last_resource_receipt_seq"),
            ),
            Gt(distance, P0("policy", "resource_learning_distance_floor_m")),
        ),
        "effects": [
            ["set_attr", "episode", "learned_fuel_l_per_m", T(
                If(
                    Gt(
                        P0("episode", "receipt_fuel_used_l"),
                        P0("policy", "fuel_learning_observation_floor_l"),
                    ),
                    Plus(
                        Mul(retention, P0("episode", "learned_fuel_l_per_m")),
                        Mul(innovation, measured_fuel_rate),
                    ),
                    P0("episode", "learned_fuel_l_per_m"),
                )
            )],
            ["set_attr", "episode", "learned_tyre_wear_per_m", T(
                If(
                    Gt(
                        P0("episode", "receipt_tyre_wear"),
                        P0("policy", "tyre_learning_observation_floor"),
                    ),
                    Plus(
                        Mul(retention, P0("episode", "learned_tyre_wear_per_m")),
                        Mul(innovation, measured_wear_rate),
                    ),
                    P0("episode", "learned_tyre_wear_per_m"),
                )
            )],
            ["set_attr", "episode", "last_resource_receipt_seq", T(
                P0("episode", "resource_receipt_seq")
            )],
        ],
    }


def manifest():
    strategy_rows = (
        # pace, fuel cost, tyre cost, contact risk, aggression, pit threshold
        (0.78, 0.46, 0.40, 0.18, 0.18, 0.48),
        (0.86, 0.56, 0.48, 0.26, 0.28, 0.62),
        (0.92, 0.66, 0.59, 0.37, 0.42, 0.78),
        (0.97, 0.78, 0.72, 0.52, 0.58, 0.96),
        (1.02, 0.88, 0.84, 0.69, 0.76, 1.18),
        (1.06, 1.00, 0.98, 0.90, 0.96, 1.42),
        # Cross-axis alternatives prevent a one-dimensional mode ladder.
        (0.91, 0.58, 0.77, 0.43, 0.48, 0.88),
        (0.93, 0.81, 0.53, 0.40, 0.46, 0.74),
    )
    strategy_nodes = [
        {
            "local_id": 2 + ordinal,
            "type": "RacingStrategyCandidate",
            "attrs": {
                "ordinal": float(ordinal),
                "pace_fraction": pace,
                "fuel_cost": fuel,
                "tyre_cost": tyre,
                "contact_risk": risk,
                "aggression": aggression,
                "pit_threshold": pit_threshold,
            },
        }
        for ordinal, (pace, fuel, tyre, risk, aggression, pit_threshold)
        in enumerate(strategy_rows)
    ]
    return {
        "id": "racing_cognition",
        "version": "1.1.0",
        "depends_on": [
            "embodied_pareto_profile",
            "motor_decision_collapse",
            "embodied_structural_limits",
        ],
        "area": "racing_motor_cortex",
        "latency_class": "hard_realtime",
        "nodes": [{
            "local_id": 1,
            "type": "RacingPolicy",
            "attrs": {
                "gravity_m_s2": 9.80665,
                "minimum_speed_m_s": 5.0,
                "maximum_speed_m_s": 78.0,
                "curvature_floor_inv_m": 0.004,
                "lateral_accel_margin": 0.72,
                "near_curvature_weight": 1.0,
                "middle_curvature_weight": 0.88,
                "far_curvature_weight": 0.7,
                "optimal_tyre_temperature_c": 92.0,
                "thermal_deadband_c": 18.0,
                "thermal_grip_loss_per_c": 0.008,
                "minimum_thermal_retention": 0.62,
                "minimum_grip_estimate": 0.45,
                "maximum_grip_estimate": 1.65,
                "slip_intervention_rad": 0.115,
                "instability_speed_retention": 0.82,
                "minimum_damage_speed_retention": 0.54,
                "damage_speed_penalty": 1.8,
                "opponent_overlap_width_m": 2.35,
                "opponent_reaction_distance_m": 46.0,
                "overtake_commit_distance_m": 24.0,
                "closing_speed_gain": 0.48,
                "following_distance_gain": 0.24,
                "overtake_lateral_gain": 0.16,
                "distance_floor_m": 0.5,
                "curvature_steering_gain": 19.0,
                "heading_steering_gain": 1.38,
                "lateral_steering_gain": 0.78,
                "slip_countersteer_gain": 1.9,
                "yaw_damping_gain": 0.34,
                "minimum_steering_response": 0.12,
                "throttle_speed_gain": 0.12,
                "brake_speed_gain": 0.105,
                "stability_brake_gain": 2.4,
                "minimum_stability_brake_speed_m_s": 8.0,
                "aero_demand_gain": 0.065,
                "minimum_aero_command": 0.04,
                "braking_front_aero_gain": 0.18,
                "stability_rear_aero_gain": 1.6,
                "upshift_rpm": 7350.0,
                "downshift_rpm": 3150.0,
                "maximum_gear": 8.0,
                "model_retention": 0.94,
                "command_floor": 0.03,
                "grip_learning_accel_m_s2": 2.0,
                "strategy_interval_ticks": 25.0,
                "finish_fuel_reserve_factor": 1.12,
                "fuel_floor_l": 0.1,
                "maximum_resource_pressure": 2.0,
                "finish_tyre_condition_reserve": 0.42,
                "pit_tyre_condition_threshold": 0.34,
                "damage_service_pressure_gain": 0.02,
                "minimum_service_remaining_fraction": 0.12,
                "tyre_reserve_pressure_gain": 3.2,
                "tyre_thermal_pressure_gain": 0.022,
                "damage_risk_pressure_gain": 0.08,
                "surprise_risk_pressure_gain": 8.0,
                "slip_risk_pressure_gain": 2.4,
                "passing_opportunity_gain": 7.5,
                "base_pace_aspiration": 0.97,
                "finish_pace_gain": 0.07,
                "opportunity_pace_gain": 0.06,
                "fuel_pace_penalty": 0.12,
                "tyre_pace_penalty": 0.1,
                "risk_pace_penalty": 0.13,
                "minimum_pace_aspiration": 0.76,
                "maximum_pace_aspiration": 1.06,
                "fuel_cost_pressure_gain": 0.52,
                "tyre_cost_pressure_gain": 0.5,
                "minimum_cost_aspiration": 0.38,
                "base_risk_aspiration": 0.52,
                "opportunity_risk_gain": 0.23,
                "finish_risk_gain": 0.12,
                "risk_pressure_penalty": 0.42,
                "minimum_risk_aspiration": 0.14,
                "pace_objective_weight": 3.0,
                "base_resource_weight": 0.45,
                "fuel_objective_gain": 2.6,
                "tyre_objective_gain": 2.5,
                "base_risk_weight": 0.65,
                "risk_objective_gain": 2.8,
                "minimum_tyre_utilization": 0.78,
                "strategy_tyre_utilization_gain": 0.22,
                "minimum_throttle_cap": 0.62,
                "strategy_throttle_cap_gain": 0.38,
                "torque_vectoring_yaw_gain": 0.72,
                "front_drive_vectoring_gain": 0.55,
                "rear_drive_vectoring_gain": 1.0,
                "front_brake_vectoring_gain": 0.7,
                "rear_brake_vectoring_gain": 1.0,
                "pit_lane_speed_m_s": 12.0,
                "resource_model_retention": 0.985,
                "resource_learning_distance_floor_m": 0.05,
                "fuel_learning_observation_floor_l": 0.0000001,
                "tyre_learning_observation_floor": 0.000000001,
            },
        }, *strategy_nodes],
        "edges": [{
            "src": {"role": "agent_root"},
            "type": "has_racing_policy",
            "tgt": {"local": 1},
            "attrs": {},
        }, *[
            {
                "src": {"local": 1},
                "type": "has_racing_strategy_candidate",
                "tgt": {"local": 2 + ordinal},
                "attrs": {},
            }
            for ordinal in range(len(strategy_rows))
        ]],
        "productions": [],
        "rules": [
            learn_receipt_rule(),
            close_unexcited_receipt_rule(),
            learn_resource_rates_rule(),
            strategy_pareto_rule(),
            fast_control_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "racing_cognition.json"
    output.write_text(
        json.dumps(manifest(), indent=1) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
