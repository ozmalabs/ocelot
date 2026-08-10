"""Run the graph-native autorotation controller on a 6-DoF Bullet plant."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.pybullet_helicopter_world import (  # noqa: E402
    HelicopterDisturbance,
    PyBulletHelicopterWorld,
    SIMULATOR_NAME,
)
from domains.embodied_graph_transducer import stamp_attrs  # noqa: E402
from domains.traditional_helicopter_world import (  # noqa: E402
    EngineFailureCondition,
    HelicopterParameters,
)
from scripts.jabberwock_helicopter_autorotation import (  # noqa: E402
    AutorotationRunError,
    _action_models,
    _edge,
    _issued_trial,
    _one_node,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


def _write_state(
    agent: WorldAdapter,
    episode,
    observation: dict[str, Any],
    *,
    state_seq: int,
) -> None:
    position = observation["base_position"]
    velocity = observation["base_linear_velocity"]
    orientation = observation["base_orientation_rpy"]
    angular_velocity = observation["base_angular_velocity"]
    touchdown_velocity = observation["touchdown_velocity"] or (0.0, 0.0, 0.0)
    touchdown_rpy = observation["touchdown_rpy"] or (0.0, 0.0, 0.0)
    attrs = {
        "state_x": float(position[0]),
        "state_y": float(position[1]),
        "state_z": float(position[2]),
        "state_vx": float(velocity[0]),
        "state_vy": float(velocity[1]),
        "state_vz": float(velocity[2]),
        "state_roll": float(orientation[0]),
        "state_pitch": float(orientation[1]),
        "state_yaw": float(orientation[2]),
        "state_roll_rate": float(angular_velocity[0]),
        "state_pitch_rate": float(angular_velocity[1]),
        "state_yaw_rate": float(angular_velocity[2]),
        "state_rotor_fraction": float(observation["rotor_speed_fraction"]),
        "state_rotor_energy_joules": float(
            observation["rotor_kinetic_energy_joules"]
        ),
        "state_potential_energy_joules": float(
            observation["potential_energy_joules"]
        ),
        "state_translational_energy_joules": float(
            observation["translational_energy_joules"]
        ),
        "state_contact": float(observation["contact_count"] > 0),
        "state_touchdown_vx": float(touchdown_velocity[0]),
        "state_touchdown_vy": float(touchdown_velocity[1]),
        "state_touchdown_vz": float(touchdown_velocity[2]),
        "state_touchdown_roll": float(touchdown_rpy[0]),
        "state_touchdown_pitch": float(touchdown_rpy[1]),
        "state_abs_touchdown_vx": abs(float(touchdown_velocity[0])),
        "state_abs_touchdown_vy": abs(float(touchdown_velocity[1])),
        "state_abs_touchdown_vz": abs(float(touchdown_velocity[2])),
        "state_abs_touchdown_roll": abs(float(touchdown_rpy[0])),
        "state_abs_touchdown_pitch": abs(float(touchdown_rpy[1])),
        "state_seq": float(state_seq),
    }
    stamp_attrs(agent, episode, attrs)


def _outcome_attrs(
    agent: WorldAdapter,
    episode,
    observation: dict[str, Any],
    next_observation: dict[str, Any],
    token: str,
    *,
    bounded_intervention: bool,
) -> dict[str, Any]:
    pre_velocity = observation["base_linear_velocity"]
    post_velocity = next_observation["base_linear_velocity"]
    pre_rates = observation["base_angular_velocity"]
    post_rates = next_observation["base_angular_velocity"]
    pre_rpy = observation["base_orientation_rpy"]
    return {
        "pre_vx": float(pre_velocity[0]),
        "pre_vy": float(pre_velocity[1]),
        "pre_vz": float(pre_velocity[2]),
        "pre_roll_rate": float(pre_rates[0]),
        "pre_pitch_rate": float(pre_rates[1]),
        "pre_yaw_rate": float(pre_rates[2]),
        "pre_roll": float(pre_rpy[0]),
        "pre_pitch": float(pre_rpy[1]),
        "pre_yaw": float(pre_rpy[2]),
        "pre_rotor_fraction": float(observation["rotor_speed_fraction"]),
        "pre_time_to_contact_seconds": float(
            agent.s.node(episode)["attrs"].get(
                "time_to_contact_seconds", 0.0
            )
        ),
        "post_vx": float(post_velocity[0]),
        "post_vy": float(post_velocity[1]),
        "post_vz": float(post_velocity[2]),
        "post_roll_rate": float(post_rates[0]),
        "post_pitch_rate": float(post_rates[1]),
        "post_yaw_rate": float(post_rates[2]),
        "post_rotor_fraction": float(
            next_observation["rotor_speed_fraction"]
        ),
        "supplied_energy_joules": float(
            next_observation["supplied_energy_joules"]
        ),
        "recovered_energy_joules": float(
            next_observation["recovered_energy_joules"]
        ),
        "receipt_verified": float(
            next_observation["last_actuator_token"] == token
        ),
        "processed": 0.0,
        "bounded_intervention": float(bounded_intervention),
        "memory_recorded": 0.0,
        "provenance": (
            "reset_bounded_3d_physical_intervention_receipt"
            if bounded_intervention
            else "physical_3d_helicopter_transition_receipt"
        ),
    }


def _calibrate_policy_from_body(
    agent: WorldAdapter,
    policy,
    parameters: dict[str, float],
) -> None:
    values = {
        "minimum_viable_rotor_fraction": (
            parameters["minimum_rotor_speed"]
            / parameters["nominal_rotor_speed"]
        ),
        "maximum_touchdown_vertical_speed": (
            parameters["maximum_safe_touchdown_vertical_speed"]
        ),
        "maximum_touchdown_horizontal_speed": (
            parameters["maximum_safe_touchdown_horizontal_speed"]
        ),
        "maximum_touchdown_lateral_speed": (
            parameters["maximum_safe_touchdown_lateral_speed"]
        ),
        "maximum_touchdown_attitude": min(
            parameters["maximum_safe_touchdown_pitch"],
            parameters["maximum_safe_touchdown_roll"],
        ),
    }
    for key, value in values.items():
        agent.inner.set_attr(policy, key, float(value))


def run_autorotation_3d_experiment(
    *,
    episodes: int = 4,
    maximum_actions_per_episode: int = 500,
    initial_altitudes: Iterable[float] = (80.0, 120.0),
    initial_forward_speeds: Iterable[float] = (14.0, 20.0),
    wind_velocities: Iterable[Iterable[float]] = ((0.0, 0.0, 0.0),),
    failure_onset_seconds: float = 1.0,
    action_duration_seconds: float = 0.1,
    calibration_repeats: int = 1,
    disturbance: HelicopterDisturbance | None = None,
    parameters: HelicopterParameters | None = None,
) -> dict[str, Any]:
    if episodes < 1:
        raise ValueError("episodes must be positive")
    if maximum_actions_per_episode < 1:
        raise ValueError("maximum_actions_per_episode must be positive")
    if calibration_repeats < 0:
        raise ValueError("calibration_repeats must be non-negative")
    altitudes = tuple(float(value) for value in initial_altitudes)
    speeds = tuple(float(value) for value in initial_forward_speeds)
    winds = tuple(
        tuple(float(component) for component in wind)
        for wind in wind_velocities
    )
    if not altitudes or not all(
        math.isfinite(value) and value > 0.0 for value in altitudes
    ):
        raise ValueError("initial altitudes must be finite and positive")
    if not speeds or not all(
        math.isfinite(value) and value >= 0.0 for value in speeds
    ):
        raise ValueError("initial speeds must be finite and non-negative")
    if not winds or not all(
        len(wind) == 3 and all(math.isfinite(value) for value in wind)
        for wind in winds
    ):
        raise ValueError("wind velocities must be finite triples")

    agent = WorldAdapter(seeds=("helicopter_autorotation",))
    policy = _one_node(agent, "HelicopterEnergyPolicy")
    agent.inner.set_attr(
        policy, "action_duration_seconds", float(action_duration_seconds)
    )
    episode = agent.s.add_node("HelicopterEnergyEpisode", {
        "action_ready": 0.0,
        "request_seq": 0.0,
        "decision_seq": 0.0,
        "last_trial_seq": -1.0,
        "state_seq": 0.0,
        "measured_state_seq": -1.0,
        "episode_index": 0.0,
        "impact_cost": 0.0,
        "viable_contact": 0.0,
        "authority_change_count": 0.0,
        "contact_horizon_context": 0.0,
    })
    _edge(agent, agent.agent, "has_helicopter_episode", episode)

    world = PyBulletHelicopterWorld(
        parameters=parameters,
        failure=EngineFailureCondition(
            onset_seconds=0.0,
            retained_power_fraction=0.0,
        ),
        initial_position=(0.0, 0.0, 100.0),
        initial_velocity=(18.0, 0.0, -3.0),
        action_duration_seconds=action_duration_seconds,
    )
    options = world.actuator_options()
    _calibrate_policy_from_body(agent, policy, world.body_parameters())
    for context in range(3):
        for ordinal, option in enumerate(options):
            model = agent.s.add_node("HelicopterEnergyActionModel", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "contact_horizon_context": float(context),
                "semantics": "unknown",
                "experience_count": 0.0,
                "mean_dvx": 0.0,
                "mean_dvy": 0.0,
                "mean_dvz": 0.0,
                "mean_droll_rate": 0.0,
                "mean_dpitch_rate": 0.0,
                "mean_dyaw_rate": 0.0,
                "mean_drotor_fraction": 0.0,
                "mean_supplied_energy_joules": 0.0,
                "mean_recovered_energy_joules": 0.0,
                "prediction_error_ema": 0.0,
                "surprise_count": 0.0,
                "provenance": "fresh_contextual_opaque_3d_action_model",
            })
            _edge(agent, episode, "has_energy_action_model", model)

    request_seq = 0
    state_seq = 0
    calibration_conditions = (
        (100.0, -3.0),
        (7.0, -3.0),
        (2.0, -3.0),
    )
    for altitude, vertical_speed in calibration_conditions:
        for _ in range(len(options) * calibration_repeats):
            observation = world.reset(
                initial_position=(0.0, 0.0, altitude),
                initial_velocity=(18.0, 0.0, vertical_speed),
                initial_orientation_rpy=(0.0, 0.0, 0.0),
                initial_angular_velocity=(0.0, 0.0, 0.0),
            )
            request_seq += 1
            state_seq += 1
            _write_state(agent, episode, observation, state_seq=state_seq)
            agent.inner.set_attr(episode, "request_seq", float(request_seq))
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()
            attrs = dict(agent.s.node(episode)["attrs"])
            token = attrs.get("selected_token")
            if not isinstance(token, str):
                raise AutorotationRunError(
                    "graph did not issue a 3-D calibration intervention"
                )
            trial = _issued_trial(agent, episode, request_seq)
            next_observation = world.step(token)
            outcome = agent.s.add_node(
                "HelicopterEnergyOutcome",
                _outcome_attrs(
                    agent,
                    episode,
                    observation,
                    next_observation,
                    token,
                    bounded_intervention=True,
                ),
            )
            _edge(agent, trial, "has_helicopter_energy_outcome", outcome)
            state_seq += 1
            _write_state(
                agent, episode, next_observation, state_seq=state_seq
            )
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()

    episode_results = []
    trace = []
    for episode_index in range(episodes):
        altitude = altitudes[episode_index % len(altitudes)]
        speed = speeds[episode_index % len(speeds)]
        wind = winds[episode_index % len(winds)]
        world.close()
        world = PyBulletHelicopterWorld(
            parameters=parameters,
            failure=EngineFailureCondition(
                onset_seconds=failure_onset_seconds,
                retained_power_fraction=0.0,
            ),
            initial_position=(0.0, 0.0, altitude),
            initial_velocity=(speed, 0.0, 0.0),
            wind_velocity=wind,
            disturbance=disturbance,
            action_duration_seconds=action_duration_seconds,
        )
        observation = world.observe()
        agent.inner.set_attr(episode, "episode_index", float(episode_index))
        agent.inner.set_attr(episode, "viable_contact", 0.0)
        actions_taken = 0
        for _ in range(maximum_actions_per_episode):
            if observation["landed"]:
                break
            request_seq += 1
            state_seq += 1
            _write_state(agent, episode, observation, state_seq=state_seq)
            agent.inner.set_attr(episode, "request_seq", float(request_seq))
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()
            before = dict(agent.s.node(episode)["attrs"])
            token = before.get("selected_token")
            if not isinstance(token, str):
                raise AutorotationRunError(
                    f"graph did not issue a 3-D action at {request_seq}"
                )
            trial = _issued_trial(agent, episode, request_seq)
            next_observation = world.step(token)
            outcome = agent.s.add_node(
                "HelicopterEnergyOutcome",
                _outcome_attrs(
                    agent,
                    episode,
                    observation,
                    next_observation,
                    token,
                    bounded_intervention=False,
                ),
            )
            _edge(agent, trial, "has_helicopter_energy_outcome", outcome)
            state_seq += 1
            _write_state(
                agent, episode, next_observation, state_seq=state_seq
            )
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()
            learned = dict(agent.s.node(outcome)["attrs"])
            trace.append({
                "episode": episode_index,
                "sim_time": next_observation["sim_time"],
                "position": list(next_observation["base_position"]),
                "velocity": list(next_observation["base_linear_velocity"]),
                "orientation_rpy": list(
                    next_observation["base_orientation_rpy"]
                ),
                "angular_velocity": list(
                    next_observation["base_angular_velocity"]
                ),
                "rotor_fraction": next_observation["rotor_speed_fraction"],
                "selected_token": token,
                "decision_kind": before.get("decision_kind"),
                "prediction_error": learned.get("prediction_error"),
                "surprise": learned.get("surprise"),
            })
            observation = next_observation
            actions_taken += 1

        final = dict(agent.s.node(episode)["attrs"])
        touchdown_velocity = observation["touchdown_velocity"]
        touchdown_rpy = observation["touchdown_rpy"]
        episode_results.append({
            "episode": episode_index,
            "initial_altitude": altitude,
            "initial_forward_speed": speed,
            "wind_velocity": list(wind),
            "actions": actions_taken,
            "landed": observation["landed"],
            "safe_touchdown_world_assessment": observation["safe_touchdown"],
            "viable_contact_graph_assessment": bool(
                final.get("viable_contact", 0.0)
            ),
            "touchdown_velocity": (
                None
                if touchdown_velocity is None
                else list(touchdown_velocity)
            ),
            "touchdown_rpy": (
                None if touchdown_rpy is None else list(touchdown_rpy)
            ),
            "touchdown_rotor_fraction": observation[
                "touchdown_rotor_fraction"
            ],
            "authority_change_count": final.get(
                "authority_change_count", 0.0
            ),
        })
    world.close()

    safe_count = sum(
        bool(row["safe_touchdown_world_assessment"])
        for row in episode_results
    )
    graph_safe_count = sum(
        bool(row["viable_contact_graph_assessment"])
        for row in episode_results
    )
    return {
        "experiment": "graph_native_hidden_failure_autorotation_3d",
        "simulator": SIMULATOR_NAME,
        "policy_owner": "rust_graph",
        "failure_observation_exposed": False,
        "action_semantics_exposed_to_graph": False,
        "fresh_substrate": True,
        "episodes": episodes,
        "safe_touchdowns": safe_count,
        "graph_assessed_safe_touchdowns": graph_safe_count,
        "success_rate": safe_count / episodes,
        "calibration_repeats": calibration_repeats,
        "calibration_interventions": (
            len(calibration_conditions) * len(options) * calibration_repeats
        ),
        "action_count": len(options),
        "episode_results": episode_results,
        "action_models": _action_models(agent, episode),
        "trace": trace,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=4)
    parser.add_argument("--maximum-actions", type=int, default=500)
    parser.add_argument("--altitudes", type=float, nargs="+", default=[80, 120])
    parser.add_argument("--speeds", type=float, nargs="+", default=[14, 20])
    parser.add_argument("--failure-onset", type=float, default=1.0)
    parser.add_argument("--action-duration", type=float, default=0.1)
    parser.add_argument("--calibration-repeats", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_autorotation_3d_experiment(
        episodes=args.episodes,
        maximum_actions_per_episode=args.maximum_actions,
        initial_altitudes=args.altitudes,
        initial_forward_speeds=args.speeds,
        failure_onset_seconds=args.failure_onset,
        action_duration_seconds=args.action_duration,
        calibration_repeats=args.calibration_repeats,
    )
    payload = json.dumps(result, indent=2)
    if args.output is None:
        print(payload)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
        print(args.output)


if __name__ == "__main__":
    main()
