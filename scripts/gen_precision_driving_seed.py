#!/usr/bin/env python3
"""Generate the graph-native precision-driving cortex."""
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
def Mul(*items): return {"type": "Times", "items": list(items)}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Abs(value): return {"type": "Abs", "arg": value}
def Min(*items): return {"type": "Min", "items": list(items)}
def Max(*items): return {"type": "Max", "items": list(items)}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(item): return {"type": "Not", "arg": item}
def Sin(value): return {"type": "Sin", "arg": value}
def Cos(value): return {"type": "Cos", "arg": value}
def Atan2(y, x): return {"type": "Atan2", "y": y, "x": x}
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
def Argmin(source, var, value, default):
    return {
        "type": "Argmin",
        "source": source,
        "var_name": var,
        "value": value,
        "default": default,
    }
def If(cond, then, other):
    return {
        "type": "IfThenElse",
        "cond": cond,
        "then": then,
        "other": other,
    }
def T(term): return {"__term__": term}


def Clamp(value, lower, upper):
    return Min(Max(value, lower), upper)


def _selected_manoeuvre():
    return Eq(
        P0("manoeuvre", "ordinal"),
        P0("episode", "manoeuvre_ordinal"),
    )


def _clip_ahead_phase(clip_var):
    wrapped = Atan2(
        Sin(Minus(
            P0(clip_var, "phase_rad"),
            P0("episode", "state_path_phase_rad"),
        )),
        Cos(Minus(
            P0(clip_var, "phase_rad"),
            P0("episode", "state_path_phase_rad"),
        )),
    )
    return If(
        Lt(wrapped, L(0.0)),
        Plus(wrapped, P0("policy", "full_turn_rad")),
        wrapped,
    )


def _phase_transition_rule(name, from_phase, to_phase, condition):
    return {
        "name": name,
        "area": "precision_driving_cortex",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_precision_policy", "policy"],
            ["policy", "has_precision_manoeuvre", "manoeuvre"],
            ["agent", "has_precision_episode", "episode"],
        ],
        "where": And(
            _selected_manoeuvre(),
            Eq(P0("episode", "manoeuvre_phase"), L(from_phase)),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "phase_decision_seq"),
            ),
            condition,
        ),
        "effects": [
            ["set_attr", "episode", "manoeuvre_phase", float(to_phase)],
            ["set_attr", "episode", "phase_start_time_s", T(
                P0("episode", "state_time_s")
            )],
            ["set_attr", "episode", "phase_start_angular_travel_rad", T(
                P0("episode", "state_angular_travel_rad")
            )],
            ["set_attr", "episode", "phase_decision_seq", T(
                P0("episode", "request_seq")
            )],
        ],
    }


def phase_progression_rules():
    phase_elapsed = Minus(
        P0("episode", "state_time_s"),
        P0("episode", "phase_start_time_s"),
    )
    acquired_attitude = Gt(
        Mul(
            P0("manoeuvre", "target_slip_rad"),
            P0("episode", "state_slip_angle"),
        ),
        Mul(
            Abs(P0("manoeuvre", "target_slip_rad")),
            Abs(P0("manoeuvre", "target_slip_rad")),
            P0("policy", "attitude_acquisition_fraction"),
        ),
    )
    return [
        _phase_transition_rule(
            "precision_launch_to_attitude_acquisition",
            0,
            1,
            Gt(
                P0("episode", "state_speed_m_s"),
                P0("manoeuvre", "entry_speed_m_s"),
            ),
        ),
        _phase_transition_rule(
            "precision_attitude_acquisition_to_hold",
            1,
            2,
            Or(
                acquired_attitude,
                Gt(
                    phase_elapsed,
                    P0("policy", "maximum_acquisition_time_s"),
                ),
            ),
        ),
        _phase_transition_rule(
            "precision_hold_to_exit",
            2,
            3,
            And(
                Gt(
                    phase_elapsed,
                    P0("policy", "minimum_hold_time_s"),
                ),
                Gt(
                    P0("episode", "state_angular_travel_rad"),
                    P0("manoeuvre", "target_turn_rad"),
                ),
            ),
        ),
        _phase_transition_rule(
            "precision_exit_to_complete",
            3,
            4,
            And(
                Lt(
                    Abs(P0("episode", "state_slip_angle")),
                    P0("policy", "exit_slip_tolerance_rad"),
                ),
                Lt(
                    Abs(P0("episode", "state_yaw_rate_rad_s")),
                    P0("policy", "exit_yaw_rate_tolerance_rad_s"),
                ),
                Lt(
                    P0("episode", "state_speed_m_s"),
                    P0("manoeuvre", "exit_speed_m_s"),
                ),
            ),
        ),
    ]


def fast_control_rule():
    matching_clips = Filter(
        Neighbours("policy", "has_precision_clip_zone"),
        "candidate_clip",
        Eq(
            P0("candidate_clip", "manoeuvre_ordinal"),
            P0("manoeuvre", "ordinal"),
        ),
    )
    selected_clip = Argmin(
        matching_clips,
        "candidate_clip",
        _clip_ahead_phase("candidate_clip"),
        V("episode"),
    )
    phase = P0("episode", "manoeuvre_phase")
    geometry_native = Eq(P0("manoeuvre", "geometry_native"), L(1.0))
    path_curvature = P0("episode", "state_path_curvature_middle_inv_m")
    direction = If(
        geometry_native,
        If(
            Gt(path_curvature, L(0.0)),
            L(1.0),
            If(Lt(path_curvature, L(0.0)), L(-1.0), L(0.0)),
        ),
        P0("manoeuvre", "direction"),
    )
    active_attitude = Or(Eq(phase, L(1.0)), Eq(phase, L(2.0)))
    target_slip = If(
        active_attitude,
        If(
            geometry_native,
            Clamp(
                Mul(
                    L(-1.0),
                    P0("manoeuvre", "curvature_slip_gain_m"),
                    path_curvature,
                ),
                Mul(L(-1.0), P0("manoeuvre", "maximum_slip_rad")),
                P0("manoeuvre", "maximum_slip_rad"),
            ),
            P0("manoeuvre", "target_slip_rad"),
        ),
        L(0.0),
    )
    target_yaw_rate = If(
        Lt(phase, L(3.0)),
        If(
            geometry_native,
            Mul(P0("episode", "state_speed_m_s"), path_curvature),
            Mul(
                direction,
                Div(
                    P0("episode", "state_speed_m_s"),
                    Max(
                        P0("manoeuvre", "radius_m"),
                        P0("policy", "distance_floor_m"),
                    ),
                ),
            ),
        ),
        L(0.0),
    )
    geometry_speed = Div(
        P0("manoeuvre", "maximum_geometry_speed_m_s"),
        Plus(
            L(1.0),
            Mul(
                P0("manoeuvre", "curvature_speed_gain_m"),
                P0("episode", "state_path_curvature_envelope_inv_m"),
            ),
        ),
    )
    hold_speed = If(
        geometry_native,
        Max(geometry_speed, P0("manoeuvre", "minimum_geometry_speed_m_s")),
        P0("manoeuvre", "hold_speed_m_s"),
    )
    target_speed = If(
        Eq(phase, L(0.0)),
        P0("manoeuvre", "entry_speed_m_s"),
        If(
            Or(Eq(phase, L(1.0)), Eq(phase, L(2.0))),
            hold_speed,
            If(
                Eq(phase, L(3.0)),
                P0("manoeuvre", "exit_speed_m_s"),
                L(0.0),
            ),
        ),
    )
    path_error = If(
        geometry_native,
        P0("episode", "state_path_lateral_error_m"),
        P0("episode", "state_radial_error_m"),
    )
    clip_ahead_distance = If(
        geometry_native,
        Mul(
            _clip_ahead_phase("clip"),
            Div(
                P0("episode", "state_path_length_m"),
                P0("policy", "full_turn_rad"),
            ),
        ),
        Mul(
            _clip_ahead_phase("clip"),
            P0("manoeuvre", "radius_m"),
        ),
    )
    clip_commitment = Mul(
        P0("episode", "preview_authority"),
        Clamp(
            Minus(
                L(1.0),
                Div(
                    clip_ahead_distance,
                    P0("clip", "commitment_distance_m"),
                ),
            ),
            L(0.0),
            L(1.0),
        ),
    )
    clip_path_target = Mul(
        clip_commitment,
        P0("clip", "radial_offset_m"),
    )
    effective_path_error = Minus(path_error, clip_path_target)
    radial_command = If(
        geometry_native,
        Mul(
            L(-1.0),
            P0("policy", "radial_position_gain"),
            P0("manoeuvre", "geometry_path_gain"),
            effective_path_error,
        ),
        Mul(
            direction,
            P0("policy", "radial_position_gain"),
            effective_path_error,
        ),
    )
    clip_command = If(
        geometry_native,
        Mul(
            L(-1.0),
            P0("manoeuvre", "clip_gain"),
            clip_commitment,
            P0("policy", "clip_steering_gain"),
            Minus(path_error, P0("clip", "radial_offset_m")),
        ),
        Mul(
            direction,
            P0("manoeuvre", "clip_gain"),
            clip_commitment,
            P0("policy", "clip_steering_gain"),
            Minus(path_error, P0("clip", "radial_offset_m")),
        ),
    )
    slip_error = Minus(
        target_slip,
        P0("episode", "state_slip_angle"),
    )
    yaw_error = Minus(
        target_yaw_rate,
        P0("episode", "state_yaw_rate_rad_s"),
    )
    preview_command = Mul(
        P0("episode", "preview_authority"),
        P0("manoeuvre", "preview_gain"),
        Plus(
            Mul(
                P0("policy", "preview_near_bearing_gain"),
                P0("episode", "state_preview_near_bearing_rad"),
            ),
            Mul(
                P0("policy", "preview_middle_bearing_gain"),
                P0("episode", "state_preview_middle_bearing_rad"),
            ),
            Mul(
                P0("policy", "preview_far_bearing_gain"),
                P0("episode", "state_preview_far_bearing_rad"),
            ),
            Mul(
                P0("policy", "preview_far_heading_gain"),
                P0("episode", "state_preview_far_heading_error_rad"),
            ),
        ),
    )
    adaptive_hold_path_weight = Clamp(
        Plus(
            P0("policy", "minimum_hold_path_weight"),
            Mul(
                P0("policy", "hold_path_pressure_gain"),
                Div(
                    Abs(effective_path_error),
                    P0("policy", "hold_path_pressure_distance_m"),
                ),
            ),
        ),
        P0("policy", "minimum_hold_path_weight"),
        P0("policy", "maximum_hold_path_weight"),
    )
    path_weight = If(
        geometry_native,
        L(1.0),
        If(
            Eq(phase, L(2.0)),
            adaptive_hold_path_weight,
            If(
                Eq(phase, L(3.0)),
                P0("policy", "exit_path_weight"),
                L(1.0),
            ),
        ),
    )
    acquisition_steer = If(
        And(Eq(phase, L(1.0)), Not(geometry_native)),
        Mul(P0("policy", "acquisition_steer_bias"), direction),
        L(0.0),
    )
    steering = Clamp(
        Plus(
            acquisition_steer,
            Mul(P0("policy", "attitude_steering_gain"), slip_error),
            Mul(
                P0("policy", "yaw_steering_gain"),
                yaw_error,
            ),
            Mul(
                path_weight,
                P0("policy", "tangent_heading_gain"),
                P0("episode", "state_tangent_heading_error_rad"),
            ),
            Mul(path_weight, radial_command),
            Mul(path_weight, preview_command),
            clip_command,
        ),
        L(-1.0),
        L(1.0),
    )
    yaw_request = Clamp(
        Plus(
            Mul(
                L(-1.0),
                P0("policy", "vectoring_attitude_gain"),
                slip_error,
            ),
            Mul(P0("policy", "vectoring_yaw_gain"), yaw_error),
            Mul(
                P0("policy", "vectoring_path_gain"),
                If(
                    Eq(phase, L(2.0)),
                    Mul(
                        adaptive_hold_path_weight,
                        P0("policy", "hold_vectoring_path_ratio"),
                    ),
                    L(1.0),
                ),
                radial_command,
            ),
            Mul(P0("policy", "clip_vectoring_gain"), clip_command),
        ),
        L(-1.0),
        L(1.0),
    )
    speed_error = Minus(
        target_speed,
        P0("episode", "state_speed_m_s"),
    )
    speed_drive = Clamp(
        Mul(P0("policy", "speed_drive_gain"), Max(speed_error, L(0.0))),
        L(0.0),
        L(1.0),
    )
    attitude_drive = If(
        active_attitude,
        Clamp(
            Minus(
                Plus(
                    P0("manoeuvre", "attitude_drive"),
                    Mul(P0("policy", "attitude_speed_gain"), speed_error),
                ),
                Mul(
                    P0("policy", "attitude_drive_excess_penalty"),
                    Max(
                        Minus(
                            Abs(P0("episode", "state_slip_angle")),
                            Abs(target_slip),
                        ),
                        L(0.0),
                    ),
                ),
            ),
            L(0.0),
            L(1.0),
        ),
        L(0.0),
    )
    drive = If(active_attitude, attitude_drive, speed_drive)
    exit_brake = If(
        Or(Eq(phase, L(3.0)), Eq(phase, L(4.0))),
        Clamp(
            Mul(
                P0("policy", "exit_brake_gain"),
                Max(Minus(L(0.0), speed_error), L(0.0)),
            ),
            L(0.0),
            L(1.0),
        ),
        L(0.0),
    )
    geometry_speed_brake = If(
        And(geometry_native, active_attitude),
        Clamp(
            Mul(
                P0("manoeuvre", "geometry_speed_brake_gain"),
                Max(Minus(L(0.0), speed_error), L(0.0)),
            ),
            L(0.0),
            P0("manoeuvre", "maximum_geometry_brake"),
        ),
        L(0.0),
    )
    brake = Max(exit_brake, geometry_speed_brake)
    exclusive_drive = If(Gt(brake, L(0.0)), L(0.0), drive)
    attitude_front_brake = If(
        active_attitude,
        If(
            geometry_native,
            L(0.0),
            Clamp(
                Plus(
                    P0("policy", "attitude_front_brake"),
                    Mul(
                        P0("policy", "attitude_front_brake_speed_gain"),
                        Minus(L(0.0), speed_error),
                    ),
                ),
                L(0.0),
                P0("policy", "maximum_attitude_front_brake"),
            ),
        ),
        L(0.0),
    )
    attitude_front_drive = Clamp(
        Mul(
            P0("policy", "attitude_front_drive_speed_gain"),
            Max(speed_error, L(0.0)),
        ),
        L(0.0),
        P0("policy", "maximum_attitude_front_drive"),
    )
    front_drive = If(
        active_attitude,
        If(
            Gt(Max(attitude_front_brake, brake), L(0.0)),
            L(0.0),
            attitude_front_drive,
        ),
        exclusive_drive,
    )
    rear_vector_delta = Mul(
        P0("policy", "rear_vectoring_gain"),
        yaw_request,
    )
    rear_left_drive = Clamp(
        Minus(exclusive_drive, rear_vector_delta),
        L(0.0),
        L(1.0),
    )
    rear_right_drive = Clamp(
        Plus(exclusive_drive, rear_vector_delta),
        L(0.0),
        L(1.0),
    )
    left_rotation_brake = If(
        And(active_attitude, Gt(yaw_request, L(0.0))),
        Mul(P0("policy", "rotation_brake_gain"), yaw_request),
        L(0.0),
    )
    right_rotation_brake = If(
        And(active_attitude, Lt(yaw_request, L(0.0))),
        Mul(
            P0("policy", "rotation_brake_gain"),
            Abs(yaw_request),
        ),
        L(0.0),
    )
    rear_left_brake = Max(brake, left_rotation_brake)
    rear_right_brake = Max(brake, right_rotation_brake)
    safe_rear_left_drive = If(
        Gt(rear_left_brake, L(0.0)),
        L(0.0),
        rear_left_drive,
    )
    safe_rear_right_drive = If(
        Gt(rear_right_brake, L(0.0)),
        L(0.0),
        rear_right_drive,
    )
    return {
        "name": "precision_system1_attitude_path_energy_tradeoff",
        "area": "precision_driving_cortex",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_precision_policy", "policy"],
            ["policy", "has_precision_manoeuvre", "manoeuvre"],
            ["policy", "has_precision_clip_zone", "clip"],
            ["agent", "has_precision_episode", "episode"],
        ],
        "where": And(
            _selected_manoeuvre(),
            Eq(
                P0("clip", "ordinal"),
                AttrOf(selected_clip, "ordinal"),
            ),
            Eq(P0("episode", "action_ready"), L(0.0)),
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "decision_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "target_slip_rad", T(target_slip)],
            ["set_attr", "episode", "target_yaw_rate_rad_s", T(target_yaw_rate)],
            ["set_attr", "episode", "target_speed_m_s", T(target_speed)],
            ["set_attr", "episode", "attitude_cost", T(Abs(slip_error))],
            ["set_attr", "episode", "yaw_cost", T(Abs(yaw_error))],
            ["set_attr", "episode", "path_cost", T(
                Abs(effective_path_error)
            )],
            ["set_attr", "episode", "path_tradeoff_weight", T(path_weight)],
            ["set_attr", "episode", "selected_clip_ordinal", T(
                P0("clip", "ordinal")
            )],
            ["set_attr", "episode", "clip_ahead_distance_m", T(
                clip_ahead_distance
            )],
            ["set_attr", "episode", "clip_commitment", T(clip_commitment)],
            ["set_attr", "episode", "clip_target_radial_offset_m", T(
                P0("clip", "radial_offset_m")
            )],
            ["set_attr", "episode", "clip_path_command", T(clip_command)],
            ["set_attr", "episode", "preview_path_command", T(
                preview_command
            )],
            ["set_attr", "episode", "energy_cost", T(Plus(
                exclusive_drive,
                brake,
                attitude_front_brake,
                left_rotation_brake,
                right_rotation_brake,
            ))],
            ["set_attr", "episode", "command_steering", T(steering)],
            ["set_attr", "episode", "command_throttle", T(exclusive_drive)],
            ["set_attr", "episode", "command_brake", T(brake)],
            ["set_attr", "episode", "command_differential_yaw_request", T(
                yaw_request
            )],
            ["set_attr", "episode", "command_drive_front_left", T(front_drive)],
            ["set_attr", "episode", "command_drive_front_right", T(front_drive)],
            ["set_attr", "episode", "command_drive_rear_left", T(
                safe_rear_left_drive
            )],
            ["set_attr", "episode", "command_drive_rear_right", T(
                safe_rear_right_drive
            )],
            ["set_attr", "episode", "command_brake_front_left", T(
                Max(brake, attitude_front_brake)
            )],
            ["set_attr", "episode", "command_brake_front_right", T(
                Max(brake, attitude_front_brake)
            )],
            ["set_attr", "episode", "command_brake_rear_left", T(
                rear_left_brake
            )],
            ["set_attr", "episode", "command_brake_rear_right", T(
                rear_right_brake
            )],
            ["set_attr", "episode", "command_front_wing", 0.0],
            ["set_attr", "episode", "command_rear_wing", 0.0],
            ["set_attr", "episode", "command_gear", T(
                P0("manoeuvre", "gear")
            )],
            ["set_attr", "episode", "command_pit", 0.0],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "action_ready", 1.0],
        ],
    }


def learn_receipt_rule():
    excitation = Abs(P0("episode", "receipt_yaw_request"))
    observed_yaw_response = Div(
        Abs(P0("episode", "receipt_yaw_rate_delta")),
        Max(excitation, P0("policy", "learning_excitation_floor")),
    )
    observed_slip_response = Div(
        Abs(P0("episode", "receipt_slip_delta")),
        Max(excitation, P0("policy", "learning_excitation_floor")),
    )
    retention = P0("policy", "model_retention")
    update = Minus(L(1.0), retention)
    return {
        "name": "precision_learn_combined_attitude_response",
        "area": "precision_driving_cortex",
        "latency_class": "soft_realtime",
        "batch": False,
        "match": [
            ["agent", "has_precision_policy", "policy"],
            ["agent", "has_precision_episode", "episode"],
        ],
        "where": And(
            Eq(P0("episode", "receipt_pending"), L(1.0)),
            Lt(P0("episode", "manoeuvre_phase"), L(3.0)),
            Gt(
                P0("episode", "state_speed_m_s"),
                P0("policy", "minimum_learning_speed_m_s"),
            ),
            Lt(
                Abs(P0("episode", "receipt_slip_delta")),
                P0("policy", "maximum_learning_slip_delta_rad"),
            ),
            Gt(excitation, P0("policy", "learning_excitation_floor")),
            Gt(
                P0("episode", "receipt_seq"),
                P0("episode", "learned_receipt_seq"),
            ),
        ),
        "effects": [
            ["set_attr", "episode", "learned_yaw_response", T(Plus(
                Mul(retention, P0("episode", "learned_yaw_response")),
                Mul(update, observed_yaw_response),
            ))],
            ["set_attr", "episode", "learned_slip_response", T(Plus(
                Mul(retention, P0("episode", "learned_slip_response")),
                Mul(update, observed_slip_response),
            ))],
            ["set_attr", "episode", "learned_receipt_seq", T(
                P0("episode", "receipt_seq")
            )],
            ["set_attr", "episode", "receipt_pending", 0.0],
        ],
    }


def manifest():
    manoeuvre_rows = (
        # name, direction, radius, entry speed, hold speed, slip, turn, exit, drive, gear
        ("drift_left", 1.0, 34.0, 13.0, 17.0, -0.14, 5.5, 3.0, 0.36, 2.0),
        ("drift_right", -1.0, 34.0, 13.0, 17.0, 0.14, 5.5, 3.0, 0.36, 2.0),
        ("donut_left", 1.0, 8.5, 8.0, 10.5, -0.25, 6.8, 2.0, 0.46, 1.0),
        ("donut_right", -1.0, 8.5, 8.0, 10.5, 0.25, 6.8, 2.0, 0.46, 1.0),
        ("gymkhana", 0.0, 20.0, 8.0, 13.0, 0.0, 100.0, 3.0, 0.38, 2.0),
    )
    manoeuvres = [
        {
            "local_id": index + 2,
            "type": "PrecisionManoeuvre",
            "attrs": {
                "name": name,
                "ordinal": float(index),
                "direction": direction,
                "radius_m": radius,
                "entry_speed_m_s": entry_speed,
                "hold_speed_m_s": hold_speed,
                "target_slip_rad": slip,
                "target_turn_rad": turn,
                "exit_speed_m_s": exit_speed,
                "attitude_drive": drive,
                "geometry_native": float(name == "gymkhana"),
                "curvature_slip_gain_m": (
                    1.2 if name == "gymkhana" else 0.0
                ),
                "maximum_slip_rad": (
                    0.14 if name == "gymkhana" else abs(slip)
                ),
                "geometry_path_gain": (
                    1.0
                ),
                "geometry_speed_brake_gain": (
                    0.22 if name == "gymkhana" else 0.0
                ),
                "maximum_geometry_brake": (
                    0.72 if name == "gymkhana" else 0.0
                ),
                "minimum_geometry_speed_m_s": (
                    7.0 if name == "gymkhana" else hold_speed
                ),
                "maximum_geometry_speed_m_s": (
                    17.0 if name == "gymkhana" else hold_speed
                ),
                "curvature_speed_gain_m": (
                    22.0 if name == "gymkhana" else 0.0
                ),
                "preview_gain": (
                    0.72 if name == "gymkhana"
                    else 1.0 if name.startswith("drift")
                    else 0.2
                ),
                "clip_gain": (
                    1.0 if name == "gymkhana"
                    else 2.3 if name.startswith("drift")
                    else 0.3
                ),
                "gear": gear,
            },
        }
        for index, (
            name,
            direction,
            radius,
            entry_speed,
            hold_speed,
            slip,
            turn,
            exit_speed,
            drive,
            gear,
        ) in enumerate(manoeuvre_rows)
    ]
    clip_rows = tuple(
        (
            manoeuvre_ordinal,
            phase_rad,
            radial_offset_m,
            commitment_distance_m,
        )
        for manoeuvre_ordinal, manoeuvre in enumerate(manoeuvre_rows)
        for phase_rad, radial_offset_m, commitment_distance_m in (
            (
                1.5707963267948966,
                -1.5 if manoeuvre[0].startswith("drift") else -1.0,
                30.0 if manoeuvre[0].startswith("drift") else 5.0,
            ),
            (
                4.71238898038469,
                -1.5 if manoeuvre[0].startswith("drift") else -1.0,
                30.0 if manoeuvre[0].startswith("drift") else 5.0,
            ),
        )
    )
    clip_start_id = 2 + len(manoeuvre_rows)
    clips = [
        {
            "local_id": clip_start_id + ordinal,
            "type": "PrecisionClipZone",
            "attrs": {
                "ordinal": float(ordinal),
                "manoeuvre_ordinal": float(manoeuvre_ordinal),
                "phase_rad": phase_rad,
                "radial_offset_m": radial_offset_m,
                "commitment_distance_m": commitment_distance_m,
            },
        }
        for ordinal, (
            manoeuvre_ordinal,
            phase_rad,
            radial_offset_m,
            commitment_distance_m,
        ) in enumerate(clip_rows)
    ]
    return {
        "id": "precision_driving",
        "version": "1.2.0",
        "depends_on": [
            "motor_decision_collapse",
            "embodied_structural_limits",
        ],
        "area": "precision_driving_cortex",
        "latency_class": "hard_realtime",
        "nodes": [{
            "local_id": 1,
            "type": "PrecisionDrivingPolicy",
            "attrs": {
                "distance_floor_m": 0.5,
                "full_turn_rad": 6.283185307179586,
                "attitude_acquisition_fraction": 0.70,
                "maximum_acquisition_time_s": 5.0,
                "minimum_hold_time_s": 5.0,
                "exit_slip_tolerance_rad": 0.06,
                "exit_yaw_rate_tolerance_rad_s": 0.16,
                "attitude_steering_gain": 6.0,
                "acquisition_steer_bias": 1.0,
                "yaw_steering_gain": 2.0,
                "tangent_heading_gain": 0.62,
                "radial_position_gain": 0.08,
                "preview_near_bearing_gain": 0.9,
                "preview_middle_bearing_gain": 0.45,
                "preview_far_bearing_gain": 0.18,
                "preview_far_heading_gain": 0.12,
                "clip_steering_gain": 0.22,
                "clip_vectoring_gain": 0.06,
                "minimum_hold_path_weight": 0.18,
                "maximum_hold_path_weight": 1.0,
                "hold_path_pressure_gain": 0.82,
                "hold_path_pressure_distance_m": 10.0,
                "exit_path_weight": 0.10,
                "vectoring_attitude_gain": 2.0,
                "vectoring_yaw_gain": 1.2,
                "vectoring_path_gain": 0.55,
                "hold_vectoring_path_ratio": 0.20,
                "speed_drive_gain": 0.18,
                "attitude_speed_gain": 0.06,
                "attitude_drive_excess_penalty": 0.5,
                "exit_brake_gain": 0.14,
                "attitude_front_brake": 0.16,
                "attitude_front_brake_speed_gain": 0.04,
                "maximum_attitude_front_brake": 0.45,
                "attitude_front_drive_speed_gain": 0.18,
                "maximum_attitude_front_drive": 1.0,
                "rear_vectoring_gain": 1.0,
                "rotation_brake_gain": 2.0,
                "learning_excitation_floor": 0.03,
                "minimum_learning_speed_m_s": 5.0,
                "maximum_learning_slip_delta_rad": 0.20,
                "model_retention": 0.97,
            },
        }, *manoeuvres, *clips],
        "edges": [{
            "src": {"role": "agent_root"},
            "type": "has_precision_policy",
            "tgt": {"local": 1},
            "attrs": {},
        }, *[
            {
                "src": {"local": 1},
                "type": "has_precision_manoeuvre",
                "tgt": {"local": index + 2},
                "attrs": {},
            }
            for index in range(len(manoeuvre_rows))
        ], *[
            {
                "src": {"local": 1},
                "type": "has_precision_clip_zone",
                "tgt": {"local": clip_start_id + ordinal},
                "attrs": {},
            }
            for ordinal in range(len(clip_rows))
        ]],
        "productions": [],
        "rules": [
            learn_receipt_rule(),
            *phase_progression_rules(),
            fast_control_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "precision_driving.json"
    output.write_text(
        json.dumps(manifest(), indent=1) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
