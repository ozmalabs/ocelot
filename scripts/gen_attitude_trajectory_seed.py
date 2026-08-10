#!/usr/bin/env python3
"""Generate graph-native attitude/trajectory decomposition rules."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(var, key): return {"type": "Attr", "node": V(var), "key": key}
def P0(var, key): return Plus(A(var, key), L(0.0))
def Plus(*items): return {"type": "Plus", "items": list(items)}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Mul(*items): return {"type": "Times", "items": list(items)}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Min(*items): return {"type": "Min", "items": list(items)}
def Max(*items): return {"type": "Max", "items": list(items)}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Sin(value): return {"type": "Sin", "arg": value}
def Cos(value): return {"type": "Cos", "arg": value}
def If(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}
def T(term): return {"__term__": term}


def Clamp(value, lower, upper):
    return Min(Max(value, lower), upper)


def control_rule():
    elapsed = Minus(
        P0("episode", "state_time_s"),
        P0("policy", "spin_start_time_s"),
    )
    spin_fraction = Clamp(
        Div(elapsed, P0("policy", "spin_duration_s")),
        L(0.0),
        L(1.0),
    )
    spinning = And(Gt(spin_fraction, L(0.0)), Lt(spin_fraction, L(1.0)))
    target_yaw = Mul(P0("policy", "full_turn_rad"), spin_fraction)
    target_yaw_rate = If(
        spinning,
        Div(
            P0("policy", "full_turn_rad"),
            P0("policy", "spin_duration_s"),
        ),
        L(0.0),
    )
    yaw_error = Minus(target_yaw, P0("episode", "state_unwrapped_yaw_rad"))
    yaw_rate_error = Minus(
        target_yaw_rate,
        P0("episode", "state_yaw_rate_rad_s"),
    )
    desired_acceleration_x = Plus(
        P0("policy", "axial_drag_trim_m_s2"),
        Mul(
            P0("policy", "velocity_gain_per_s"),
            Minus(
                P0("policy", "target_vx_m_s"),
                P0("episode", "state_vx_m_s"),
            ),
        ),
    )
    desired_acceleration_y = Mul(
        P0("policy", "velocity_gain_per_s"),
        Minus(
            P0("policy", "target_vy_m_s"),
            P0("episode", "state_vy_m_s"),
        ),
    )
    cosine = Cos(P0("episode", "state_unwrapped_yaw_rad"))
    sine = Sin(P0("episode", "state_unwrapped_yaw_rad"))
    body_acceleration_x = Plus(
        Mul(cosine, desired_acceleration_x),
        Mul(sine, desired_acceleration_y),
    )
    body_acceleration_y = Plus(
        Mul(L(-1.0), sine, desired_acceleration_x),
        Mul(cosine, desired_acceleration_y),
    )
    throttle = Clamp(
        Mul(P0("policy", "axial_acceleration_to_command"), body_acceleration_x),
        L(0.0),
        L(1.0),
    )
    lateral_vector = Clamp(
        Mul(
            P0("policy", "lateral_acceleration_to_command"),
            body_acceleration_y,
        ),
        L(-1.0),
        L(1.0),
    )
    yaw_vector = Clamp(
        Plus(
            Mul(P0("policy", "yaw_angle_gain"), yaw_error),
            Mul(P0("policy", "yaw_rate_gain"), yaw_rate_error),
        ),
        L(-1.0),
        L(1.0),
    )
    phase = If(
        Lt(spin_fraction, L(1.0)),
        If(Gt(spin_fraction, L(0.0)), L(1.0), L(0.0)),
        L(2.0),
    )
    return {
        "name": "attitude_trajectory_system1_vectoring_control",
        "area": "attitude_trajectory_cortex",
        "latency_class": "hard_realtime",
        "batch": False,
        "match": [
            ["agent", "has_attitude_trajectory_policy", "policy"],
            ["agent", "has_attitude_trajectory_episode", "episode"],
        ],
        "where": And(
            Gt(
                P0("episode", "request_seq"),
                P0("episode", "decision_seq"),
            ),
            Lt(P0("episode", "action_ready"), L(1.0)),
        ),
        "effects": [
            ["set_attr", "episode", "manoeuvre_phase", T(phase)],
            ["set_attr", "episode", "target_unwrapped_yaw_rad", T(target_yaw)],
            ["set_attr", "episode", "target_yaw_rate_rad_s", T(target_yaw_rate)],
            ["set_attr", "episode", "trajectory_error_vx_m_s", T(
                Minus(
                    P0("policy", "target_vx_m_s"),
                    P0("episode", "state_vx_m_s"),
                )
            )],
            ["set_attr", "episode", "trajectory_error_vy_m_s", T(
                Minus(
                    P0("policy", "target_vy_m_s"),
                    P0("episode", "state_vy_m_s"),
                )
            )],
            ["set_attr", "episode", "attitude_error_rad", T(yaw_error)],
            ["set_attr", "episode", "command_throttle", T(throttle)],
            ["set_attr", "episode", "command_lateral_vector", T(
                lateral_vector
            )],
            ["set_attr", "episode", "command_yaw_vector", T(yaw_vector)],
            ["set_attr", "episode", "decision_seq", T(
                P0("episode", "request_seq")
            )],
            ["set_attr", "episode", "action_ready", 1.0],
        ],
    }


def manifest():
    return {
        "id": "attitude_trajectory",
        "version": "1.0.0",
        "depends_on": [],
        "area": "attitude_trajectory_cortex",
        "latency_class": "hard_realtime",
        "nodes": [{
            "local_id": 1,
            "type": "AttitudeTrajectoryPolicy",
            "attrs": {
                "full_turn_rad": 6.283185307179586,
                "spin_start_time_s": 1.0,
                "spin_duration_s": 3.0,
                "target_vx_m_s": 80.0,
                "target_vy_m_s": 0.0,
                "velocity_gain_per_s": 0.65,
                "axial_drag_trim_m_s2": 3.8,
                "axial_acceleration_to_command": 0.041666666666666664,
                "lateral_acceleration_to_command": 0.03,
                "yaw_angle_gain": 1.25,
                "yaw_rate_gain": 0.32,
            },
        }],
        "edges": [{
            "src": {"role": "agent_root"},
            "type": "has_attitude_trajectory_policy",
            "tgt": {"local": 1},
            "attrs": {},
        }],
        "productions": [],
        "rules": [control_rule()],
    }


def main() -> int:
    output = ROOT / "seeds" / "attitude_trajectory.json"
    output.write_text(
        json.dumps(manifest(), indent=1) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
