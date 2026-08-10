"""Run Jabberwock against a hidden in-flight engine failure.

Python schedules episodes, mirrors instruments into graph nodes, enacts the
opaque token authored by the graph, and attaches physical receipts.  All action
selection, adaptation, energy management, and viability judgment are
Rust-evaluated rules from the ``helicopter_autorotation`` seed.
"""
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

from domains.embodied_graph_transducer import (  # noqa: E402
    GraphBoundaryCardinalityError,
    add_unchecked_edge as _edge,
    neighbour_rows,
    stamp_attrs,
    unique_neighbour,
    unique_node as _one_node,
)
from domains.traditional_helicopter_world import (  # noqa: E402
    EngineFailureCondition,
    HelicopterParameters,
    SIMULATOR_NAME,
    TraditionalHelicopterWorld,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


class AutorotationRunError(RuntimeError):
    """Experiment-boundary failure with a graph request sequence."""


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
    touchdown_vz = observation["touchdown_vertical_speed"]
    touchdown_vx = observation["touchdown_horizontal_speed"]
    touchdown_pitch = observation["touchdown_pitch_radians"]
    attrs = {
        "state_x": float(position[0]),
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
        "state_touchdown_vz": float(touchdown_vz or 0.0),
        "state_touchdown_vx": float(touchdown_vx or 0.0),
        "state_touchdown_vy": 0.0,
        "state_touchdown_roll": 0.0,
        "state_touchdown_pitch": float(touchdown_pitch or 0.0),
        "state_abs_touchdown_vz": abs(float(touchdown_vz or 0.0)),
        "state_abs_touchdown_vx": abs(float(touchdown_vx or 0.0)),
        "state_abs_touchdown_vy": 0.0,
        "state_abs_touchdown_roll": 0.0,
        "state_abs_touchdown_pitch": abs(float(touchdown_pitch or 0.0)),
        "state_seq": float(state_seq),
    }
    stamp_attrs(agent, episode, attrs)


def _issued_trial(agent: WorldAdapter, episode, request_seq: int):
    try:
        return unique_neighbour(
            agent,
            episode,
            "has_helicopter_energy_trial",
            attrs={"status": "issued", "request_seq": request_seq},
            description=f"trials at request {request_seq}",
        )
    except GraphBoundaryCardinalityError as exc:
        raise AutorotationRunError(str(exc)) from exc


def _action_models(agent: WorldAdapter, episode) -> list[dict[str, Any]]:
    return neighbour_rows(
        agent,
        episode,
        "has_energy_action_model",
        fields=(
                "token",
                "ordinal",
                "contact_horizon_context",
                "experience_count",
                "mean_dvx",
                "mean_dvy",
                "mean_dvz",
                "mean_droll_rate",
                "mean_dpitch_rate",
                "mean_dyaw_rate",
                "mean_drotor_fraction",
                "mean_supplied_energy_joules",
                "mean_recovered_energy_joules",
                "prediction_error_ema",
                "surprise_count",
        ),
    )


def run_autorotation_experiment(
    *,
    episodes: int = 12,
    maximum_actions_per_episode: int = 300,
    initial_altitudes: Iterable[float] = (140.0,),
    initial_forward_speeds: Iterable[float] = (18.0,),
    failure_onset_seconds: float = 1.0,
    action_duration_seconds: float = 0.1,
    calibration_repeats: int = 1,
    parameters: HelicopterParameters | None = None,
) -> dict[str, Any]:
    """Learn on repeated hidden failures while retaining only graph memory."""
    if episodes < 1:
        raise ValueError("episodes must be positive")
    if maximum_actions_per_episode < 1:
        raise ValueError("maximum_actions_per_episode must be positive")
    if calibration_repeats < 0:
        raise ValueError("calibration_repeats must be non-negative")
    altitudes = tuple(float(value) for value in initial_altitudes)
    speeds = tuple(float(value) for value in initial_forward_speeds)
    if not altitudes or not speeds:
        raise ValueError("initial condition collections must not be empty")
    if not all(math.isfinite(value) and value > 0.0 for value in altitudes):
        raise ValueError("initial altitudes must be finite and positive")
    if not all(math.isfinite(value) and value >= 0.0 for value in speeds):
        raise ValueError("initial forward speeds must be finite and non-negative")

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

    probe_world = TraditionalHelicopterWorld(
        parameters=parameters,
        failure=EngineFailureCondition(
            onset_seconds=failure_onset_seconds,
            retained_power_fraction=0.0,
        ),
        initial_position=(0.0, altitudes[0]),
        initial_velocity=(speeds[0], 0.0),
        action_duration_seconds=action_duration_seconds,
    )
    options = probe_world.actuator_options()
    body_parameters = probe_world.body_parameters()
    probe_world.close()
    agent.inner.set_attr(
        policy,
        "minimum_viable_rotor_fraction",
        body_parameters["minimum_rotor_speed"]
        / body_parameters["nominal_rotor_speed"],
    )
    agent.inner.set_attr(
        policy,
        "maximum_touchdown_vertical_speed",
        body_parameters["maximum_safe_touchdown_vertical_speed"],
    )
    agent.inner.set_attr(
        policy,
        "maximum_touchdown_horizontal_speed",
        body_parameters["maximum_safe_touchdown_horizontal_speed"],
    )
    agent.inner.set_attr(
        policy,
        "maximum_touchdown_lateral_speed",
        body_parameters["maximum_safe_touchdown_horizontal_speed"],
    )
    agent.inner.set_attr(
        policy,
        "maximum_touchdown_attitude",
        body_parameters["maximum_safe_touchdown_pitch"],
    )
    contact_horizon_contexts = range(3)
    for context in contact_horizon_contexts:
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
                "provenance": "fresh_contextual_opaque_action_model",
            })
            _edge(agent, episode, "has_energy_action_model", model)

    request_seq = 0
    state_seq = 0

    # Safe reset-based motor babbling supplies local, engine-off consequences
    # at three generic contact horizons.  Reset selection is experiment
    # scheduling; the graph still chooses every intervention and owns every
    # update.  No action vector or helicopter label crosses this boundary.
    calibration_conditions = (
        (140.0, -6.0),
        (12.0, -6.0),
        (4.0, -6.0),
    )
    for calibration_altitude, calibration_vz in calibration_conditions:
        for _ in range(len(options) * calibration_repeats):
            world = TraditionalHelicopterWorld(
                parameters=parameters,
                failure=EngineFailureCondition(
                    onset_seconds=0.0,
                    retained_power_fraction=0.0,
                ),
                initial_position=(0.0, calibration_altitude),
                initial_velocity=(18.0, calibration_vz),
                action_duration_seconds=action_duration_seconds,
            )
            observation = world.observe()
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
                    "graph did not issue a calibration intervention"
                )
            trial = _issued_trial(agent, episode, request_seq)
            next_observation = world.step(token)
            outcome = agent.s.add_node("HelicopterEnergyOutcome", {
                "pre_vx": float(observation["base_linear_velocity"][0]),
                "pre_vy": 0.0,
                "pre_vz": float(observation["base_linear_velocity"][2]),
                "pre_roll_rate": 0.0,
                "pre_pitch_rate": float(
                    observation["base_angular_velocity"][1]
                ),
                "pre_yaw_rate": 0.0,
                "pre_roll": 0.0,
                "pre_pitch": float(observation["base_orientation_rpy"][1]),
                "pre_yaw": 0.0,
                "pre_rotor_fraction": float(
                    observation["rotor_speed_fraction"]
                ),
                "pre_time_to_contact_seconds": float(
                    agent.s.node(episode)["attrs"].get(
                        "time_to_contact_seconds", 0.0
                    )
                ),
                "post_vx": float(next_observation["base_linear_velocity"][0]),
                "post_vy": 0.0,
                "post_vz": float(next_observation["base_linear_velocity"][2]),
                "post_roll_rate": 0.0,
                "post_pitch_rate": float(
                    next_observation["base_angular_velocity"][1]
                ),
                "post_yaw_rate": 0.0,
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
                "bounded_intervention": 1.0,
                "memory_recorded": 0.0,
                "provenance": "reset_bounded_physical_intervention_receipt",
            })
            _edge(agent, trial, "has_helicopter_energy_outcome", outcome)
            state_seq += 1
            _write_state(
                agent, episode, next_observation, state_seq=state_seq
            )
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()
            world.close()

    episode_results = []
    trace = []
    for episode_index in range(episodes):
        altitude = altitudes[episode_index % len(altitudes)]
        speed = speeds[episode_index % len(speeds)]
        world = TraditionalHelicopterWorld(
            parameters=parameters,
            failure=EngineFailureCondition(
                onset_seconds=failure_onset_seconds,
                retained_power_fraction=0.0,
            ),
            initial_position=(0.0, altitude),
            initial_velocity=(speed, 0.0),
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
            if (
                not isinstance(token, str)
                or float(before.get("action_ready", 0.0)) != 1.0
            ):
                raise AutorotationRunError(
                    f"graph did not issue action at request {request_seq}"
                )
            trial = _issued_trial(agent, episode, request_seq)
            linked_models = list(
                agent.inner.neighbours(trial, "uses_energy_action_model")
            )
            if len(linked_models) != 1:
                raise AutorotationRunError(
                    f"trial at request {request_seq} has "
                    f"{len(linked_models)} models"
                )
            next_observation = world.step(token)
            outcome = agent.s.add_node("HelicopterEnergyOutcome", {
                "pre_vx": float(observation["base_linear_velocity"][0]),
                "pre_vy": 0.0,
                "pre_vz": float(observation["base_linear_velocity"][2]),
                "pre_roll_rate": 0.0,
                "pre_pitch_rate": float(
                    observation["base_angular_velocity"][1]
                ),
                "pre_yaw_rate": 0.0,
                "pre_roll": 0.0,
                "pre_pitch": float(observation["base_orientation_rpy"][1]),
                "pre_yaw": 0.0,
                "pre_rotor_fraction": float(
                    observation["rotor_speed_fraction"]
                ),
                "pre_time_to_contact_seconds": float(
                    agent.s.node(episode)["attrs"].get(
                        "time_to_contact_seconds", 0.0
                    )
                ),
                "post_vx": float(next_observation["base_linear_velocity"][0]),
                "post_vy": 0.0,
                "post_vz": float(next_observation["base_linear_velocity"][2]),
                "post_roll_rate": 0.0,
                "post_pitch_rate": float(
                    next_observation["base_angular_velocity"][1]
                ),
                "post_yaw_rate": 0.0,
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
                "bounded_intervention": 0.0,
                "memory_recorded": 0.0,
                "provenance": "physical_helicopter_transition_receipt",
            })
            _edge(agent, trial, "has_helicopter_energy_outcome", outcome)
            state_seq += 1
            _write_state(
                agent, episode, next_observation, state_seq=state_seq
            )
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()
            learned_outcome = dict(agent.s.node(outcome)["attrs"])
            trace.append({
                "episode": episode_index,
                "request_seq": request_seq,
                "sim_time": next_observation["sim_time"],
                "altitude": next_observation["base_position"][2],
                "forward_speed": next_observation["base_linear_velocity"][0],
                "vertical_speed": next_observation["base_linear_velocity"][2],
                "pitch": next_observation["base_orientation_rpy"][1],
                "rotor_fraction": next_observation["rotor_speed_fraction"],
                "selected_token": token,
                "decision_kind": before.get("decision_kind"),
                "prediction_error": learned_outcome.get("prediction_error"),
                "surprise": learned_outcome.get("surprise"),
                "recovered_energy_joules": next_observation[
                    "recovered_energy_joules"
                ],
            })
            observation = next_observation
            actions_taken += 1

        final_attrs = dict(agent.s.node(episode)["attrs"])
        episode_results.append({
            "episode": episode_index,
            "initial_altitude": altitude,
            "initial_forward_speed": speed,
            "actions": actions_taken,
            "landed": observation["landed"],
            "safe_touchdown_world_assessment": observation["safe_touchdown"],
            "viable_contact_graph_assessment": bool(
                final_attrs.get("viable_contact", 0.0)
            ),
            "touchdown_vertical_speed": observation[
                "touchdown_vertical_speed"
            ],
            "touchdown_horizontal_speed": observation[
                "touchdown_horizontal_speed"
            ],
            "touchdown_pitch_radians": observation[
                "touchdown_pitch_radians"
            ],
            "touchdown_rotor_fraction": observation["rotor_speed_fraction"],
            "authority_change_count": final_attrs.get(
                "authority_change_count", 0.0
            ),
            "impact_cost_graph_assessment": final_attrs.get(
                "impact_cost", 0.0
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
        "experiment": "graph_native_hidden_failure_autorotation",
        "simulator": SIMULATOR_NAME,
        "policy_owner": "rust_graph",
        "failure_observation_exposed": False,
        "action_semantics_exposed_to_graph": False,
        "fresh_substrate": True,
        "episodes": episodes,
        "calibration_repeats": calibration_repeats,
        "calibration_interventions": (
            len(calibration_conditions) * len(options) * calibration_repeats
        ),
        "safe_touchdowns": safe_count,
        "graph_assessed_safe_touchdowns": graph_safe_count,
        "success_rate": safe_count / episodes,
        "first_half_success_rate": (
            sum(
                bool(row["safe_touchdown_world_assessment"])
                for row in episode_results[: max(1, episodes // 2)]
            )
            / max(1, episodes // 2)
        ),
        "second_half_success_rate": (
            sum(
                bool(row["safe_touchdown_world_assessment"])
                for row in episode_results[episodes // 2 :]
            )
            / max(1, len(episode_results[episodes // 2 :]))
        ),
        "action_alphabet": [option["token"] for option in options],
        "episode_results": episode_results,
        "action_models": _action_models(agent, episode),
        "trace": trace,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episodes", type=int, default=12)
    parser.add_argument("--maximum-actions", type=int, default=300)
    parser.add_argument("--altitudes", type=float, nargs="+", default=[140.0])
    parser.add_argument("--speeds", type=float, nargs="+", default=[18.0])
    parser.add_argument("--failure-onset", type=float, default=1.0)
    parser.add_argument("--action-duration", type=float, default=0.1)
    parser.add_argument("--calibration-repeats", type=int, default=1)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_autorotation_experiment(
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
