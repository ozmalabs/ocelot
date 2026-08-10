"""Run the graph-native racing cortex against the full deterministic plant.

Python is restricted to simulator I/O, exact graph transduction, termination,
and reporting.  It does not calculate a target speed, racing line, recovery,
traffic response, actuator command, or adaptation update.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.embodied_graph_transducer import (  # noqa: E402
    add_unchecked_edge as _edge,
    stamp_attrs,
)
from domains.full_racing_world import (  # noqa: E402
    FullRacingWorld,
    RacingDamage,
    RacingPlantConfig,
)
from domains.embodied_pareto import (  # noqa: E402
    evaluate_pareto_profile,
    install_pareto_profile,
    pareto_frontier,
    publish_pareto_candidate,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _sensed_attrs(observation: dict[str, Any]) -> dict[str, float]:
    """Mechanically rename raw plant telemetry for graph ingestion."""
    return {
        "state_time_s": float(observation["time_s"]),
        "state_speed_m_s": float(observation["speed_m_s"]),
        "state_body_vx_m_s": float(observation["body_vx_m_s"]),
        "state_body_vy_m_s": float(observation["body_vy_m_s"]),
        "state_yaw_rate_rad_s": float(observation["yaw_rate_rad_s"]),
        "state_slip_angle": float(observation["slip_angle_rad"]),
        "state_longitudinal_accel_m_s2": float(
            observation["longitudinal_accel_m_s2"]
        ),
        "state_lateral_accel_m_s2": float(
            observation["lateral_accel_m_s2"]
        ),
        "state_differential_yaw_moment_nm": float(
            observation.get("differential_yaw_moment_nm", 0.0)
        ),
        "state_track_lateral_m": float(observation["track_lateral_m"]),
        "state_track_half_width_m": float(
            observation["track_half_width_m"]
        ),
        "state_heading_error_rad": float(
            observation["track_heading_error_rad"]
        ),
        "state_curvature_now": float(
            observation["track_curvature_now_inv_m"]
        ),
        "state_curvature_near": float(
            observation["track_curvature_near_inv_m"]
        ),
        "state_curvature_middle": float(
            observation["track_curvature_middle_inv_m"]
        ),
        "state_curvature_far": float(
            observation["track_curvature_far_inv_m"]
        ),
        "state_curvature_envelope_near": float(
            observation["track_curvature_envelope_near_inv_m"]
        ),
        "state_curvature_envelope_middle": float(
            observation["track_curvature_envelope_middle_inv_m"]
        ),
        "state_curvature_envelope_far": float(
            observation["track_curvature_envelope_far_inv_m"]
        ),
        "state_surface_grip": float(observation["surface_grip"]),
        "state_surface_wet": float(observation["surface_wet"]),
        "state_front_slip": float(observation["front_slip_rad"]),
        "state_rear_slip": float(observation["rear_slip_rad"]),
        "state_tyre_temperature_c": float(
            observation["tyre_temperature_mean_c"]
        ),
        "state_tyre_condition": float(
            observation["tyre_condition_mean"]
        ),
        "state_brake_temperature_c": float(
            observation["brake_temperature_mean_c"]
        ),
        "state_fuel_l": float(observation["fuel_l"]),
        "state_total_distance_m": float(
            observation["race_total_distance_m"]
        ),
        "state_remaining_distance_m": float(
            observation["race_remaining_distance_m"]
        ),
        "state_damage": float(observation["damage"]),
        "state_opponent_gap_m": float(
            observation["nearest_opponent_ahead_m"]
        ),
        "state_opponent_lateral_m": float(
            observation["nearest_opponent_lateral_m"]
        ),
        "state_opponent_speed_m_s": float(
            observation["nearest_opponent_speed_m_s"]
        ),
        "state_opponent_closing_m_s": float(
            observation["nearest_opponent_closing_m_s"]
        ),
        "state_engine_rpm": float(observation["engine_rpm"]),
        "state_gear": float(observation["gear"]),
    }


def _graph_action(agent: WorldAdapter, episode: Any) -> dict[str, float | int]:
    """Read the single already-collapsed graph command without interpretation."""
    attrs = agent.s.node(episode)["attrs"]
    if float(attrs.get("action_ready", 0.0)) != 1.0:
        raise RuntimeError("racing graph did not publish an action")
    return {
        "steering": float(attrs["command_steering"]),
        "throttle": float(attrs["command_throttle"]),
        "brake": float(attrs["command_brake"]),
        "drive_front_left": float(attrs["command_drive_front_left"]),
        "drive_front_right": float(attrs["command_drive_front_right"]),
        "drive_rear_left": float(attrs["command_drive_rear_left"]),
        "drive_rear_right": float(attrs["command_drive_rear_right"]),
        "brake_front_left": float(attrs["command_brake_front_left"]),
        "brake_front_right": float(attrs["command_brake_front_right"]),
        "brake_rear_left": float(attrs["command_brake_rear_left"]),
        "brake_rear_right": float(attrs["command_brake_rear_right"]),
        "front_wing": float(attrs["command_front_wing"]),
        "rear_wing": float(attrs["command_rear_wing"]),
        "gear": int(round(float(attrs["command_gear"]))),
        "pit_request": int(round(float(attrs["command_pit"]))),
    }


def run_race(
    *,
    duration_s: float = 60.0,
    seed: int = 0,
    opponent_count: int = 3,
    damage: RacingDamage | None = None,
    trace_hz: float = 2.0,
    world_config: RacingPlantConfig | None = None,
    world: Any | None = None,
    control_architecture: str = "standard",
) -> dict[str, Any]:
    if duration_s <= 0.0:
        raise ValueError("duration_s must be positive")
    if trace_hz <= 0.0:
        raise ValueError("trace_hz must be positive")
    if control_architecture not in {"standard", "differential"}:
        raise ValueError(
            "control_architecture must be 'standard' or 'differential'"
        )

    agent = WorldAdapter(seeds=("racing_cognition",))
    if world is None:
        world = FullRacingWorld(
            seed=seed,
            config=world_config,
            damage=damage,
            opponent_count=opponent_count,
        )
    observation = world.reset()
    initial_fuel_l = float(observation["fuel_l"])
    initial_unwrapped_progress_m = (
        int(observation["laps"]) * world.track_length_m
        + float(observation["track_progress_m"])
    )
    episode = agent.s.add_node("RacingEpisode", {
        "request_seq": 0.0,
        "decision_seq": 0.0,
        "action_ready": 0.0,
        "receipt_pending": 0.0,
        "learned_grip": float(observation["surface_grip"]),
        "learned_steering_response": 0.18,
        "model_surprise": 0.0,
        "target_speed_m_s": 0.0,
        "command_steering": 0.0,
        "command_throttle": 0.0,
        "command_brake": 0.0,
        "command_differential_yaw_request": 0.0,
        "command_drive_front_left": 0.0,
        "command_drive_front_right": 0.0,
        "command_drive_rear_left": 0.0,
        "command_drive_rear_right": 0.0,
        "command_brake_front_left": 0.0,
        "command_brake_front_right": 0.0,
        "command_brake_rear_left": 0.0,
        "command_brake_rear_right": 0.0,
        "command_front_wing": 0.0,
        "command_rear_wing": 0.0,
        "command_gear": 1.0,
        "command_pit": 0.0,
        "strategy_decision_seq": 0.0,
        "strategy_ordinal": 3.0,
        "strategy_pace_fraction": 0.97,
        "strategy_fuel_cost": 0.78,
        "strategy_tyre_cost": 0.72,
        "strategy_contact_risk": 0.52,
        "strategy_aggression": 0.58,
        "strategy_pit_threshold": 0.96,
        "fuel_pressure": 0.0,
        "tyre_pressure": 0.0,
        "risk_pressure": 0.0,
        "pit_pressure": 0.0,
        "pace_aspiration": 0.97,
        "fuel_cost_aspiration": 1.0,
        "tyre_cost_aspiration": 1.0,
        "risk_aspiration": 0.52,
        "pit_commit": 0.0,
        "learned_fuel_l_per_m": 0.00035,
        "learned_tyre_wear_per_m": 0.0000002,
        "resource_receipt_seq": 0.0,
        "differential_authority": float(
            control_architecture == "differential"
        ),
        "last_resource_receipt_seq": 0.0,
        "receipt_distance_delta_m": 0.0,
        "receipt_fuel_used_l": 0.0,
        "receipt_tyre_wear": 0.0,
        "receipt_steering_command": 0.0,
        "receipt_yaw_rate_delta": 0.0,
        "receipt_lateral_accel_m_s2": 0.0,
        **_sensed_attrs(observation),
    })
    _edge(agent, agent.agent, "has_racing_episode", episode)

    control_hz = world.config.control_hz
    step_count = int(round(duration_s * control_hz))
    trace_interval = max(1, int(round(control_hz / trace_hz)))
    trace: list[dict[str, Any]] = []
    graph_latencies_us: list[float] = []
    previous_yaw_rate = float(observation["yaw_rate_rad_s"])
    previous_action = {
        "steering": 0.0,
        "throttle": 0.0,
        "brake": 0.0,
        "drive_front_left": 0.0,
        "drive_front_right": 0.0,
        "drive_rear_left": 0.0,
        "drive_rear_right": 0.0,
        "brake_front_left": 0.0,
        "brake_front_right": 0.0,
        "brake_rear_left": 0.0,
        "brake_rear_right": 0.0,
        "front_wing": 0.0,
        "rear_wing": 0.0,
        "gear": 1,
        "pit_request": 0,
    }
    previous_observation = observation

    for request_seq in range(1, step_count + 1):
        stamp_attrs(agent, episode, {
            **_sensed_attrs(observation),
            "request_seq": float(request_seq),
            "action_ready": 0.0,
            "receipt_pending": float(request_seq > 1),
            "receipt_steering_command": float(previous_action["steering"]),
            "receipt_yaw_rate_delta": (
                float(observation["yaw_rate_rad_s"]) - previous_yaw_rate
            ),
            "receipt_lateral_accel_m_s2": float(
                observation["lateral_accel_m_s2"]
            ),
            "resource_receipt_seq": float(request_seq - 1),
            "receipt_distance_delta_m": max(
                0.0,
                (
                    int(observation["laps"])
                    - int(previous_observation["laps"])
                ) * world.track_length_m
                + float(observation["track_progress_m"])
                - float(previous_observation["track_progress_m"]),
            ),
            "receipt_fuel_used_l": max(
                0.0,
                float(previous_observation["fuel_l"])
                - float(observation["fuel_l"]),
            ),
            "receipt_tyre_wear": max(
                0.0,
                float(previous_observation["tyre_condition_mean"])
                - float(observation["tyre_condition_mean"]),
            ),
        })
        tick_start_ns = time.perf_counter_ns()
        agent.tick()
        graph_latencies_us.append(
            (time.perf_counter_ns() - tick_start_ns) / 1000.0
        )
        action = _graph_action(agent, episode)
        previous_yaw_rate = float(observation["yaw_rate_rad_s"])
        previous_action = action
        previous_observation = observation
        observation = world.step(action)

        if request_seq % trace_interval == 0 or request_seq == step_count:
            attrs = agent.s.node(episode)["attrs"]
            trace.append({
                "time_s": float(observation["time_s"]),
                "laps": int(observation["laps"]),
                "progress_m": float(observation["track_progress_m"]),
                "speed_m_s": float(observation["speed_m_s"]),
                "target_speed_m_s": float(attrs["target_speed_m_s"]),
                "lateral_m": float(observation["track_lateral_m"]),
                "heading_error_rad": float(
                    observation["track_heading_error_rad"]
                ),
                "slip_angle_rad": float(observation["slip_angle_rad"]),
                "surface_wet": bool(observation["surface_wet"]),
                "opponent_gap_m": float(
                    observation["nearest_opponent_ahead_m"]
                ),
                "offtrack_time_s": float(observation["offtrack_time_s"]),
                "collisions": int(observation["collisions"]),
                "damage": float(observation["damage"]),
                "damage_active": bool(observation["damage_active"]),
                "tyre_condition": float(
                    observation["tyre_condition_mean"]
                ),
                "fuel_l": float(observation["fuel_l"]),
                "learned_grip": float(attrs["learned_grip"]),
                "learned_steering_response": float(
                    attrs["learned_steering_response"]
                ),
                "model_surprise": float(attrs["model_surprise"]),
                "strategy_ordinal": int(attrs["strategy_ordinal"]),
                "strategy_pace_fraction": float(
                    attrs["strategy_pace_fraction"]
                ),
                "strategy_fuel_cost": float(attrs["strategy_fuel_cost"]),
                "strategy_tyre_cost": float(attrs["strategy_tyre_cost"]),
                "strategy_contact_risk": float(
                    attrs["strategy_contact_risk"]
                ),
                "strategy_aggression": float(
                    attrs["strategy_aggression"]
                ),
                "strategy_pit_threshold": float(
                    attrs["strategy_pit_threshold"]
                ),
                "fuel_pressure": float(attrs["fuel_pressure"]),
                "tyre_pressure": float(attrs["tyre_pressure"]),
                "risk_pressure": float(attrs["risk_pressure"]),
                "pit_pressure": float(attrs["pit_pressure"]),
                "differential_yaw_request": float(
                    attrs["command_differential_yaw_request"]
                ),
                "differential_yaw_moment_nm": float(
                    observation.get("differential_yaw_moment_nm", 0.0)
                ),
                "learned_fuel_l_per_m": float(
                    attrs["learned_fuel_l_per_m"]
                ),
                "learned_tyre_wear_per_m": float(
                    attrs["learned_tyre_wear_per_m"]
                ),
                "pit_commit": bool(attrs["pit_commit"]),
                "pit_stops": int(observation["pit_stops"]),
                "action": dict(action),
            })

    sorted_latency = sorted(graph_latencies_us)
    percentile_index = min(
        len(sorted_latency) - 1,
        int(0.99 * len(sorted_latency)),
    )
    final_unwrapped_progress_m = (
        int(observation["laps"]) * world.track_length_m
        + float(observation["track_progress_m"])
    )
    total_progress = max(
        0.0,
        final_unwrapped_progress_m - initial_unwrapped_progress_m,
    )
    policies = agent.inner.neighbours(agent.agent, "has_racing_policy")
    if len(policies) != 1:
        raise RuntimeError("expected exactly one graph racing policy")
    strategy_profile = install_pareto_profile(agent, episode, (
        {"name": "pace", "ordinal": 0, "direction": "maximize"},
        {"name": "fuel_cost", "ordinal": 1, "direction": "minimize"},
        {"name": "tyre_cost", "ordinal": 2, "direction": "minimize"},
        {"name": "contact_risk", "ordinal": 3, "direction": "minimize"},
    ), context="racing_strategy")
    strategy_candidates = {}
    for strategy in agent.inner.neighbours(
        policies[0], "has_racing_strategy_candidate"
    ):
        attrs = agent.s.node(strategy)["attrs"]
        identity = f"racing_strategy:{int(float(attrs['ordinal']))}"
        strategy_candidates[identity] = publish_pareto_candidate(
            agent,
            strategy_profile,
            {
                "pace": float(attrs["pace_fraction"]),
                "fuel_cost": float(attrs["fuel_cost"]),
                "tyre_cost": float(attrs["tyre_cost"]),
                "contact_risk": float(attrs["contact_risk"]),
            },
            identity=identity,
        )
    strategy_profile_report = evaluate_pareto_profile(agent, strategy_profile)
    strategy_frontier = {
        agent.s.node(candidate)["attrs"]["identity"]
        for candidate in pareto_frontier(agent, strategy_profile)
    }
    result = {
        "backend": getattr(
            world,
            "backend",
            "deterministic_full_racing_plant",
        ),
        "control_architecture": control_architecture,
        "seed": seed,
        "duration_s": duration_s,
        "control_hz": control_hz,
        "physics_hz": world.config.physics_hz,
        "opponent_count": opponent_count,
        "damage": (
            None if damage is None else {
                "onset_s": damage.onset_s,
                "steering_retention": damage.steering_retention,
                "power_retention": damage.power_retention,
                "front_brake_retention": damage.front_brake_retention,
                "rear_brake_retention": damage.rear_brake_retention,
                "aero_retention": damage.aero_retention,
                "yaw_bias_nm": damage.yaw_bias_nm,
            }
        ),
        "track_length_m": world.track_length_m,
        "laps": int(observation["laps"]),
        "total_progress_m": total_progress,
        "mean_speed_m_s": total_progress / duration_s,
        "final_speed_m_s": float(observation["speed_m_s"]),
        "offtrack_time_s": float(observation["offtrack_time_s"]),
        "collisions": int(observation["collisions"]),
        "pit_stops": int(observation["pit_stops"]),
        "plant_damage": float(observation["damage"]),
        "fuel_used_l": (
            initial_fuel_l - float(observation["fuel_l"])
        ),
        "final_tyre_condition": float(
            observation["tyre_condition_mean"]
        ),
        "strategy_pareto_profile": {
            "scalarized": False,
            "dimensions": ["pace", "fuel_cost", "tyre_cost", "contact_risk"],
            "frontier": sorted(strategy_frontier),
            "system_two_steps": strategy_profile_report["system_two_steps"],
            "candidates": [
                {
                    "identity": identity,
                    "frontier": identity in strategy_frontier,
                    "dominated_by": sorted(
                        agent.s.node(other)["attrs"]["identity"]
                        for other in agent.inner.neighbours(
                            candidate,
                            "is_dominated_by_embodied_candidate",
                        )
                    ),
                }
                for identity, candidate in sorted(strategy_candidates.items())
            ],
        },
        "graph_tick_latency_us": {
            "median": sorted_latency[len(sorted_latency) // 2],
            "p99": sorted_latency[percentile_index],
            "maximum": max(sorted_latency),
        },
        "trace": trace,
    }
    if hasattr(world, "close"):
        world.close()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration-s", type=float, default=60.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--opponents", type=int, default=3)
    parser.add_argument("--damage-onset-s", type=float)
    parser.add_argument("--steering-retention", type=float, default=1.0)
    parser.add_argument("--power-retention", type=float, default=1.0)
    parser.add_argument("--front-brake-retention", type=float, default=1.0)
    parser.add_argument("--rear-brake-retention", type=float, default=1.0)
    parser.add_argument("--aero-retention", type=float, default=1.0)
    parser.add_argument("--yaw-bias-nm", type=float, default=0.0)
    parser.add_argument("--trace-hz", type=float, default=2.0)
    parser.add_argument(
        "--control-architecture",
        choices=("standard", "differential"),
        default="standard",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--speed-dreams-app-run", type=Path)
    parser.add_argument("--speed-dreams-local-directory", type=Path)
    args = parser.parse_args(argv)
    damage = (
        None if args.damage_onset_s is None else RacingDamage(
            onset_s=args.damage_onset_s,
            steering_retention=args.steering_retention,
            power_retention=args.power_retention,
            front_brake_retention=args.front_brake_retention,
            rear_brake_retention=args.rear_brake_retention,
            aero_retention=args.aero_retention,
            yaw_bias_nm=args.yaw_bias_nm,
        )
    )
    external_world = None
    if args.speed_dreams_app_run is not None:
        if args.speed_dreams_local_directory is None:
            parser.error(
                "--speed-dreams-local-directory is required with "
                "--speed-dreams-app-run"
            )
        from domains.speed_dreams_racing_world import SpeedDreamsRacingWorld
        external_world = SpeedDreamsRacingWorld(
            app_run=args.speed_dreams_app_run,
            local_directory=args.speed_dreams_local_directory,
        )
    result = run_race(
        duration_s=args.duration_s,
        seed=args.seed,
        opponent_count=args.opponents,
        damage=damage,
        trace_hz=args.trace_hz,
        world=external_world,
        control_architecture=args.control_architecture,
    )
    payload = json.dumps(result, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
