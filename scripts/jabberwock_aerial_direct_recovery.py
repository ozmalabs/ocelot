"""Recover complete propeller loss with graph-authored direct motor control."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.gym_pybullet_drone_world import (  # noqa: E402
    PHYSICS_FREQUENCY_HZ,
    AerialPropellerCondition,
    GymPyBulletDroneWorld,
    SIMULATOR_COMMIT,
    SIMULATOR_NAME,
)
from scripts.jabberwock_aerial_adaptation import (  # noqa: E402
    _edge,
    _one_node,
    _write_state,
    run_flight,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


DEFAULT_PROTOCOL = (
    ROOT / "protocols" / "aerial_three_rotor_direct_recovery_v1.json"
)


def _norm(values) -> float:
    return math.sqrt(sum(float(value) ** 2 for value in values))


def _recovery_episode(agent: WorldAdapter):
    episode = agent.s.add_node("AerialEpisode", {
        "direct_authority_enabled": 1.0,
        "emergency_active": 0.0,
        "failed_motor_ordinal": -1.0,
        "state_seq": 0.0,
        "measured_state_seq": -1.0,
        "direct_command_state_seq": -1.0,
        "direct_command_count": 0.0,
        "direct_motor_command_ready": 0.0,
        "goal_distance": 0.0,
        "previous_goal_distance": 0.0,
        "goal_progress": 0.0,
        "goal_reached": 0.0,
        "takeoff_origin_z": 0.25,
        "peak_altitude_gain": 0.0,
        "flight_achieved": 0.0,
    })
    _edge(agent, agent.agent, "has_aerial_episode", episode)
    return episode


def run_direct_recovery(
    protocol_path: Path = DEFAULT_PROTOCOL,
    *,
    observer: Callable[[Any, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run normal graph flight, total prop loss, then graph direct control."""
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    damage = protocol["damage"]
    onset = int(damage["onset_action"])
    goal = tuple(float(value) for value in protocol["goal"])
    normal_duration = float(protocol["normal_action_duration_seconds"])
    common = {
        "goal": goal,
        "seed": int(protocol["seed"]),
        "babble_samples": int(protocol["babble_samples_per_actuator"]),
        "action_duration_seconds": normal_duration,
        "enable_yaw_actuators": bool(protocol["enable_yaw_actuators"]),
        "enable_direct_motor_actuators": bool(
            protocol["enable_direct_motor_actuators"]
        ),
        "angular_stability_weight": float(
            protocol["angular_stability_weight"]
        ),
    }
    reference = run_flight(
        steps=onset + 1,
        observer=observer,
        **common,
    )
    prefix = [
        row["selected_token"]
        for row in reference["trace"][:onset]
    ]
    failing_token = reference["trace"][onset]["selected_token"]
    condition = AerialPropellerCondition(
        onset_action=onset,
        thrust_retention=tuple(
            float(value) for value in damage["thrust_retention"]
        ),
        torque_retention=tuple(
            float(value) for value in damage["torque_retention"]
        ),
    )

    agent = WorldAdapter(seeds=("aerial_adaptation",))
    policy = _one_node(agent, "AerialPolicy")
    episode = _recovery_episode(agent)
    recovery_ticks = round(
        float(protocol["recovery_observation_seconds"])
        * PHYSICS_FREQUENCY_HZ
    )

    with GymPyBulletDroneWorld(
        seed=int(protocol["seed"]),
        goal=goal,
        propeller_condition=condition,
        action_duration_seconds=normal_duration,
        enable_yaw_actuators=bool(protocol["enable_yaw_actuators"]),
        enable_direct_motor_actuators=bool(
            protocol["enable_direct_motor_actuators"]
        ),
    ) as world:
        replay_identical = True
        observation = world.observe()
        for epoch, token in enumerate(prefix):
            observation = world.step(token)
            replay_identical = replay_identical and (
                list(observation["base_position"])
                == reference["trace"][epoch]["position_after"]
            )

        before_failure = observation
        world.set_control_frequency(PHYSICS_FREQUENCY_HZ)
        for key, value in world.body_parameters().items():
            agent.inner.set_attr(policy, key, value)

        first_failed_tick = None
        attrs = {}
        detection_ticks = 0
        for detection_tick in range(PHYSICS_FREQUENCY_HZ):
            observation = world.step_control_tick(failing_token)
            if observer is not None:
                observer(world, {
                    "phase": "failure_detection",
                    "action": detection_tick,
                    "observation": observation,
                    "event": (
                        "damage_onset" if detection_tick == 0 else None
                    ),
                    "decision_kind": "graph_failure_inference",
                })
            if first_failed_tick is None:
                first_failed_tick = observation
            detection_ticks = detection_tick + 1
            _write_state(
                agent,
                episode,
                observation,
                state_seq=detection_ticks,
            )
            agent.inner.set_attr(
                episode,
                "direct_motor_command_ready",
                0.0,
            )
            agent.tick()
            attrs = dict(agent.s.node(episode)["attrs"])
            if float(attrs.get("direct_motor_command_ready", 0.0)) == 1.0:
                break
        else:
            raise RuntimeError(
                "graph emitted no direct motor command within one second"
            )
        detection_observation = observation

        trace = []
        for tick in range(recovery_ticks):
            if tick:
                _write_state(
                    agent,
                    episode,
                    observation,
                    state_seq=detection_ticks + tick,
                )
                agent.inner.set_attr(
                    episode,
                    "direct_motor_command_ready",
                    0.0,
                )
                agent.tick()
                attrs = dict(agent.s.node(episode)["attrs"])
            if float(attrs.get("direct_motor_command_ready", 0.0)) != 1.0:
                raise RuntimeError(
                    f"graph emitted no direct motor command at tick {tick}"
                )
            rpm = [
                float(attrs[f"direct_rpm_{motor}"])
                for motor in range(4)
            ]
            next_observation = world.step_motor_rpm(
                rpm,
                command_token="graph_three_rotor_direct",
            )
            if observer is not None:
                observer(world, {
                    "phase": "direct_recovery",
                    "action": tick,
                    "observation": next_observation,
                    "event": (
                        "direct_control"
                        if tick == 0
                        else None
                    ),
                    "decision_kind": attrs["control_mode"],
                })
            trace.append({
                "tick": tick,
                "sim_time": next_observation["sim_time"],
                "position_before": list(observation["base_position"]),
                "position_after": list(next_observation["base_position"]),
                "linear_velocity_after": list(
                    next_observation["base_linear_velocity"]
                ),
                "angular_velocity_after": list(
                    next_observation["base_angular_velocity"]
                ),
                "rpm": rpm,
                "contact_count": next_observation["contact_count"],
                "failed_motor_ordinal_graph": attrs[
                    "failed_motor_ordinal"
                ],
                "control_mode": attrs["control_mode"],
            })
            observation = next_observation

        agent.inner.set_attr(episode, "direct_authority_enabled", 0.0)
        _write_state(
            agent,
            episode,
            observation,
            state_seq=detection_ticks + recovery_ticks,
        )
        agent.tick()
        final = agent.s.node(episode)["attrs"]

    hold_target = (
        float(final["emergency_target_x"]),
        float(final["emergency_target_y"]),
        float(final["emergency_target_z"]),
    )
    final_position = tuple(
        float(value) for value in observation["base_position"]
    )
    return {
        "experiment": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "simulator": SIMULATOR_NAME,
        "simulator_commit": SIMULATOR_COMMIT,
        "policy_owner": "rust_graph",
        "normal_preflight_policy_owner": "rust_graph",
        "pre_failure_replay_identical": replay_identical,
        "damage_onset_action": onset,
        "failing_normal_token": failing_token,
        "state_before_failure": {
            "position": list(before_failure["base_position"]),
            "angular_velocity": list(
                before_failure["base_angular_velocity"]
            ),
        },
        "state_after_first_failure_tick": {
            "position": list(first_failed_tick["base_position"]),
            "angular_velocity": list(
                first_failed_tick["base_angular_velocity"]
            ),
        },
        "state_at_detection": {
            "position": list(detection_observation["base_position"]),
            "angular_velocity": list(
                detection_observation["base_angular_velocity"]
            ),
        },
        "detection_ticks": detection_ticks,
        "detection_latency_seconds": (
            detection_ticks / PHYSICS_FREQUENCY_HZ
        ),
        "failed_motor_ordinal_graph": final["failed_motor_ordinal"],
        "control_mode": final["control_mode"],
        "recovery_control_hz": PHYSICS_FREQUENCY_HZ,
        "recovery_ticks": recovery_ticks,
        "recovery_duration_seconds": (
            recovery_ticks / PHYSICS_FREQUENCY_HZ
        ),
        "direct_command_count": final["direct_command_count"],
        "hold_target": hold_target,
        "final_position": final_position,
        "hold_position_error": _norm(
            final_position[index] - hold_target[index]
            for index in range(3)
        ),
        "final_goal_distance_graph_assessment": final["goal_distance"],
        "contact_ticks": sum(
            int(row["contact_count"]) > 0 for row in trace
        ),
        "peak_angular_speed": max(
            _norm(row["angular_velocity_after"]) for row in trace
        ),
        "minimum_altitude": min(
            float(row["position_after"][2]) for row in trace
        ),
        "maximum_altitude": max(
            float(row["position_after"][2]) for row in trace
        ),
        "normal_failure_baseline": protocol[
            "normal_failure_baseline"
        ],
        "preflight": reference,
        "trace": trace,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_direct_recovery(args.protocol)
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
