"""Have Jabberwock learn opaque three-dimensional commands and fly.

Python is a mechanical experiment boundary: it mirrors raw simulator state,
enacts the graph-authored token, attaches the receipt, and records graph-held
assessments. Action selection, learning, takeoff judgment, and goal judgment
are Rust-evaluated graph rules from ``aerial_adaptation``.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.embodied_graph_transducer import (  # noqa: E402
    GraphBoundaryCardinalityError,
    add_unchecked_edge as _edge,
    basic_sensor_state_attrs,
    neighbour_rows,
    pose_attrs as _pose,
    stamp_attrs,
    unique_neighbour,
    unique_node as _one_node,
)
from domains.gym_pybullet_drone_world import (  # noqa: E402
    AerialMechanicalCondition,
    AerialPropellerCondition,
    GymPyBulletDroneWorld,
    SIMULATOR_COMMIT,
    SIMULATOR_NAME,
)
from domains.sensorimotor_transducer import (  # noqa: E402
    SensorimotorSensorConfiguration,
    sensed_vector,
    sensor_receipt_attrs,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402
from domains.embodied_effector_topology import (  # noqa: E402
    bind_effector_models,
    install_name_free_effector_topology,
)


class AerialRunError(RuntimeError):
    """Flight experiment failure with an action epoch."""

    def __init__(self, message: str, *, epoch: int | None = None) -> None:
        super().__init__(message)
        self.epoch = epoch


def _write_state(
    agent: WorldAdapter,
    episode,
    observation: dict[str, Any],
    *,
    state_seq: int,
) -> None:
    velocity = sensed_vector(observation, "linear_velocity")
    angular_velocity = sensed_vector(observation, "angular_velocity")
    goal = observation["goal_position"]
    stamp_attrs(agent, episode, {
        **basic_sensor_state_attrs(observation, state_seq=state_seq),
        "state_vx": float(velocity[0]),
        "state_vy": float(velocity[1]),
        "state_vz": float(velocity[2]),
        "state_wx": float(angular_velocity[0]),
        "state_wy": float(angular_velocity[1]),
        "state_wz": float(angular_velocity[2]),
        "goal_x": float(goal[0]),
        "goal_y": float(goal[1]),
        "goal_z": float(goal[2]),
    })


def _issued_trial(agent: WorldAdapter, episode, epoch: int):
    try:
        return unique_neighbour(
            agent,
            episode,
            "has_aerial_motor_trial",
            attrs={"status": "issued", "epoch": epoch},
            description="issued flight trials",
        )
    except GraphBoundaryCardinalityError as exc:
        raise AerialRunError(
            str(exc),
            epoch=epoch,
        ) from exc


def _model_rows(agent: WorldAdapter, episode) -> list[dict[str, Any]]:
    return neighbour_rows(
        agent,
        episode,
        "has_aerial_action_model",
        fields=(
                "token",
                "ordinal",
                "experience_count",
                "mean_dx",
                "mean_dy",
                "mean_dz",
                "mean_post_vx",
                "mean_post_vy",
                "mean_post_vz",
                "mean_dwx",
                "mean_dwy",
                "mean_dwz",
                "error_ema",
                "surprise_count",
                "last_prediction_error",
                "last_update_epoch",
                "energy_ema_joules",
        ),
    )


def run_flight(
    *,
    steps: int = 80,
    goal: Iterable[float] = (0.75, 0.75, 1.0),
    seed: int = 0,
    babble_samples: int = 2,
    mode: str = "adaptive_flight",
    mechanical_condition: AerialMechanicalCondition | None = None,
    propeller_condition: AerialPropellerCondition | None = None,
    sensor_configuration: SensorimotorSensorConfiguration | None = None,
    action_duration_seconds: float = 0.5,
    adaptation_rate: float | None = None,
    surprise_adaptation_rate: float | None = None,
    plasticity_stop_epoch: int | None = None,
    enable_yaw_actuators: bool = False,
    enable_direct_motor_actuators: bool = False,
    angular_stability_weight: float = 0.0,
    observer: Callable[[Any, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run a fresh graph and a fresh official Crazyflie simulation."""
    if steps < 1:
        raise ValueError("steps must be positive")
    if babble_samples < 1:
        raise ValueError("babble_samples must be positive")
    if mode not in {"adaptive_flight", "frozen_flight"}:
        raise ValueError("mode must be adaptive_flight or frozen_flight")
    if plasticity_stop_epoch is not None and plasticity_stop_epoch < 0:
        raise ValueError("plasticity_stop_epoch must be non-negative")
    if (
        not math.isfinite(angular_stability_weight)
        or angular_stability_weight < 0.0
    ):
        raise ValueError("angular_stability_weight must be finite and non-negative")
    for name, rate in (
        ("adaptation_rate", adaptation_rate),
        ("surprise_adaptation_rate", surprise_adaptation_rate),
    ):
        if rate is not None and (
            not math.isfinite(rate) or not 0.0 < rate <= 1.0
        ):
            raise ValueError(f"{name} must be greater than zero and at most one")
    goal = tuple(float(value) for value in goal)

    agent = WorldAdapter(seeds=("aerial_adaptation",))
    policy = _one_node(agent, "AerialPolicy")
    agent.inner.set_attr(policy, "babble_samples", float(babble_samples))
    agent.inner.set_attr(
        policy,
        "action_duration_seconds",
        float(action_duration_seconds),
    )
    agent.inner.set_attr(
        policy,
        "angular_stability_weight",
        float(angular_stability_weight),
    )
    if adaptation_rate is not None:
        agent.inner.set_attr(policy, "adaptation_rate", float(adaptation_rate))
    if surprise_adaptation_rate is not None:
        agent.inner.set_attr(
            policy,
            "surprise_adaptation_rate",
            float(surprise_adaptation_rate),
        )

    with GymPyBulletDroneWorld(
        seed=seed,
        goal=goal,
        mechanical_condition=mechanical_condition,
        propeller_condition=propeller_condition,
        sensor_configuration=sensor_configuration,
        action_duration_seconds=action_duration_seconds,
        enable_yaw_actuators=enable_yaw_actuators,
        enable_direct_motor_actuators=enable_direct_motor_actuators,
    ) as world:
        observation = world.observe()
        body_parameters = world.body_parameters()
        initial_position = tuple(
            float(value) for value in observation["base_position"]
        )
        episode = agent.s.add_node("AerialEpisode", {
            "mode": mode,
            "action_ready": 0.0,
            "epoch": 0.0,
            "request_seq": 0.0,
            "decision_seq": 0.0,
            "decision_count": 0.0,
            "last_trial_epoch": -1.0,
            "state_seq": 0.0,
            "measured_state_seq": -1.0,
            "takeoff_origin_z": initial_position[2],
            "peak_altitude_gain": 0.0,
            "flight_achieved": 0.0,
            "goal_distance": 0.0,
            "previous_goal_distance": 0.0,
            "goal_progress": 0.0,
            "goal_reached": 0.0,
            "last_observed_dx": 0.0,
            "last_observed_dy": 0.0,
            "last_observed_dz": 0.0,
            "body_mass": body_parameters["body_mass"],
            "gravity_acceleration": body_parameters["gravity_acceleration"],
        })
        _edge(agent, agent.agent, "has_aerial_episode", episode)

        options = world.actuator_options()
        effector_topology = install_name_free_effector_topology(
            agent, episode, options
        )
        calibration_actions = len(options) * babble_samples
        if observer is not None:
            observer(world, {
                "phase": "cold_start",
                "action": -1,
                "observation": observation,
                "event": "fresh_graph",
            })
        agent.inner.set_attr(
            policy,
            "plasticity_stop_epoch",
            float(
                calibration_actions
                if plasticity_stop_epoch is None
                else plasticity_stop_epoch
            ),
        )
        action_models = {}
        for ordinal, option in enumerate(options):
            model = agent.s.add_node("AerialActionModel", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "experience_count": 0.0,
                "mean_dx": 0.0,
                "mean_dy": 0.0,
                "mean_dz": 0.0,
                "mean_post_vx": 0.0,
                "mean_post_vy": 0.0,
                "mean_post_vz": 0.0,
                "mean_dwx": 0.0,
                "mean_dwy": 0.0,
                "mean_dwz": 0.0,
                "error_ema": 0.0,
                "surprise_count": 0.0,
                "last_prediction_error": 0.0,
                "last_update_epoch": -1.0,
                "energy_ema_joules": 0.0,
                "provenance_kind": "untrained_fresh_aerial_action_model",
            })
            actuator = agent.s.add_node("OpaqueAerialActuator", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "semantics": "unknown",
            })
            _edge(agent, episode, "has_aerial_action_model", model)
            _edge(agent, model, "models_aerial_actuator", actuator)
            action_models[option["token"]] = model
        bind_effector_models(agent, effector_topology, action_models)

        trace = []
        initial_goal_distance = None
        for epoch in range(steps):
            _write_state(agent, episode, observation, state_seq=epoch * 2 + 1)
            agent.inner.set_attr(episode, "epoch", float(epoch))
            agent.inner.set_attr(episode, "request_seq", float(epoch + 1))
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()

            episode_before = dict(agent.s.node(episode)["attrs"])
            if initial_goal_distance is None:
                initial_goal_distance = float(episode_before["goal_distance"])
            token = episode_before.get("selected_token")
            if (
                not isinstance(token, str)
                or float(episode_before.get("action_ready", 0.0)) != 1.0
            ):
                raise AerialRunError(
                    "graph did not issue a flight action",
                    epoch=epoch,
                )
            trial = _issued_trial(agent, episode, epoch)
            trial_before = dict(agent.s.node(trial)["attrs"])
            if trial_before.get("token") != token:
                raise AerialRunError(
                    "episode and flight trial selected different tokens",
                    epoch=epoch,
                )
            models = list(
                agent.inner.neighbours(trial, "uses_aerial_action_model")
            )
            if len(models) != 1:
                raise AerialRunError(
                    f"flight trial has {len(models)} action models",
                    epoch=epoch,
                )
            model = models[0]
            model_before = dict(agent.s.node(model)["attrs"])
            experience_before = float(model_before.get("experience_count", 0.0))

            next_observation = world.step(token)
            condition = (
                propeller_condition
                if propeller_condition is not None
                else mechanical_condition
            )
            if observer is not None:
                observer(world, {
                    "phase": (
                        "motor_babble"
                        if epoch < calibration_actions
                        else "goal_flight"
                    ),
                    "action": epoch,
                    "observation": next_observation,
                    "event": (
                        "damage_onset"
                        if condition is not None
                        and epoch == condition.onset_action
                        else None
                    ),
                    "decision_kind": episode_before["decision_kind"],
                })
            receipt_verified = float(
                next_observation["last_actuator_token"] == token
            )
            trial_attrs = agent.s.node(trial)["attrs"]
            agent.inner.set_attr(
                trial,
                "predicted_task_progress",
                float(trial_attrs.get("predicted_task_progress", 0.0)),
            )
            outcome = agent.s.add_node("AerialTransitionObservation", {
                **_pose(observation, "pre"),
                **_pose(next_observation, "post"),
                **{
                    f"pre_v{axis}": float(value)
                    for axis, value in zip(
                        ("x", "y", "z"),
                        sensed_vector(observation, "linear_velocity"),
                    )
                },
                **{
                    f"post_v{axis}": float(value)
                    for axis, value in zip(
                        ("x", "y", "z"),
                        sensed_vector(next_observation, "linear_velocity"),
                    )
                },
                **{
                    f"pre_w{axis}": float(value)
                    for axis, value in zip(
                        ("x", "y", "z"),
                        sensed_vector(observation, "angular_velocity"),
                    )
                },
                **{
                    f"post_w{axis}": float(value)
                    for axis, value in zip(
                        ("x", "y", "z"),
                        sensed_vector(next_observation, "angular_velocity"),
                    )
                },
                "pre_contact_count": float(
                    observation["sensed_contact_count"]
                ),
                "contact_count": float(
                    next_observation["sensed_contact_count"]
                ),
                "pre_contact_force_newtons": float(
                    observation["contact_force_newtons"]
                ),
                "contact_force_newtons": float(
                    next_observation["contact_force_newtons"]
                ),
                "input_energy_joules": float(
                    next_observation["supplied_energy_joules"]
                ),
                "absorbed_energy_joules": float(
                    next_observation["absorbed_energy_joules"]
                ),
                "recovered_energy_joules": 0.0,
                "peak_power_watts": float(
                    next_observation["peak_actuator_power_watts"]
                ),
                "action_duration_seconds": float(
                    next_observation["sim_time"] - observation["sim_time"]
                ),
                "world_step_index": float(next_observation["step_index"]),
                "has_motor_epoch": 1.0,
                "motor_epoch": float(epoch),
                "energetic_window_seq": 0.0,
                "receipt_verified": receipt_verified,
                "processed": 0.0,
                "provenance_kind": "raw_drone_simulator_receipt",
                "task_progress": float(
                    math.dist(
                        sensed_vector(observation, "position"),
                        observation["goal_position"],
                    )
                    - math.dist(
                        sensed_vector(next_observation, "position"),
                        next_observation["goal_position"],
                    )
                ),
                **sensor_receipt_attrs(observation, next_observation),
            })
            _edge(agent, trial, "has_aerial_transition_outcome", outcome)
            agent.inner.set_attr(episode, "action_ready", 0.0)
            _write_state(
                agent,
                episode,
                next_observation,
                state_seq=epoch * 2 + 2,
            )
            agent.tick()

            episode_after = dict(agent.s.node(episode)["attrs"])
            outcome_after = agent.s.node(outcome)["attrs"]
            model_after = agent.s.node(model)["attrs"]
            trace.append({
                "epoch": epoch,
                "selected_token": token,
                "decision_kind": episode_before["decision_kind"],
                "trial_status": agent.s.node(trial)["attrs"]["status"],
                "position_before": list(observation["base_position"]),
                "position_after": list(next_observation["base_position"]),
                "velocity_after": list(next_observation["base_linear_velocity"]),
                "angular_velocity_after": list(
                    next_observation["base_angular_velocity"]
                ),
                "predicted_displacement": [
                    trial_before["predicted_dx"],
                    trial_before["predicted_dy"],
                    trial_before["predicted_dz"],
                ],
                "observed_displacement": [
                    outcome_after.get("observed_dx"),
                    outcome_after.get("observed_dy"),
                    outcome_after.get("observed_dz"),
                ],
                "predicted_angular_velocity_change": [
                    trial_before["predicted_dwx"],
                    trial_before["predicted_dwy"],
                    trial_before["predicted_dwz"],
                ],
                "observed_angular_velocity_change": [
                    outcome_after.get("observed_dwx"),
                    outcome_after.get("observed_dwy"),
                    outcome_after.get("observed_dwz"),
                ],
                "prediction_error": outcome_after.get("prediction_error"),
                "surprise": outcome_after.get("surprise"),
                "adaptation_rate": outcome_after.get("adaptation_rate"),
                "experience_count_before": experience_before,
                "experience_count_after": model_after["experience_count"],
                "model_displacement_before": [
                    model_before["mean_dx"],
                    model_before["mean_dy"],
                    model_before["mean_dz"],
                ],
                "model_displacement_after": [
                    model_after["mean_dx"],
                    model_after["mean_dy"],
                    model_after["mean_dz"],
                ],
                "model_surprise_count_before": model_before["surprise_count"],
                "model_surprise_count_after": model_after["surprise_count"],
                "goal_distance_before": episode_before["goal_distance"],
                "goal_distance_after": episode_after["goal_distance"],
                "goal_reached": episode_after["goal_reached"],
                "flight_achieved": episode_after["flight_achieved"],
                "peak_altitude_gain": episode_after["peak_altitude_gain"],
                "input_energy_joules": outcome_after.get(
                    "input_energy_joules"
                ),
                "motor_net_energy_joules": episode_after.get(
                    "motor_net_energy_joules"
                ),
                "contact_count": next_observation["contact_count"],
                "sim_time": next_observation["sim_time"],
            })
            observation = next_observation

        final = agent.s.node(episode)["attrs"]
        return {
            "experiment": "graph_native_aerial_adaptation",
            "simulator": SIMULATOR_NAME,
            "simulator_commit": SIMULATOR_COMMIT,
            "fresh_substrate": True,
            "policy_owner": "rust_graph",
            "seed": seed,
            "mode": mode,
            "steps": steps,
            "babble_samples": babble_samples,
            "action_duration_seconds": action_duration_seconds,
            "adaptation_rate": agent.s.node(policy)["attrs"]["adaptation_rate"],
            "surprise_adaptation_rate": (
                agent.s.node(policy)["attrs"]["surprise_adaptation_rate"]
            ),
            "calibration_actions": calibration_actions,
            "plasticity_stop_epoch": agent.s.node(policy)["attrs"][
                "plasticity_stop_epoch"
            ],
            "yaw_actuators_enabled": enable_yaw_actuators,
            "direct_motor_actuators_enabled": enable_direct_motor_actuators,
            "angular_stability_weight": angular_stability_weight,
            "mechanical_condition": (
                None
                if mechanical_condition is None
                else {
                    "onset_action": mechanical_condition.onset_action,
                    "motor_rpm_retention": list(
                        mechanical_condition.motor_rpm_retention
                    ),
                }
            ),
            "propeller_condition": (
                None
                if propeller_condition is None
                else {
                    "onset_action": propeller_condition.onset_action,
                    "thrust_retention": list(
                        propeller_condition.thrust_retention
                    ),
                    "torque_retention": list(
                        propeller_condition.torque_retention
                    ),
                }
            ),
            "action_alphabet": [row["token"] for row in options],
            "initial_position": initial_position,
            "goal_position": tuple(float(value) for value in goal),
            "final_position": tuple(
                float(value) for value in observation["base_position"]
            ),
            "initial_goal_distance": initial_goal_distance,
            "final_goal_distance": final["goal_distance"],
            "flight_achieved_graph_assessment": final["flight_achieved"],
            "goal_reached_graph_assessment": final["goal_reached"],
            "peak_altitude_gain_graph_assessment": final["peak_altitude_gain"],
            "motor_input_energy_joules_graph_assessment": final.get(
                "motor_input_energy_joules",
                0.0,
            ),
            "motor_net_energy_joules_graph_assessment": final.get(
                "motor_net_energy_joules",
                0.0,
            ),
            "motor_peak_power_watts_graph_assessment": final.get(
                "motor_peak_power_watts",
                0.0,
            ),
            "decision_count": final["decision_count"],
            "models": _model_rows(agent, episode),
            "trace": trace,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--steps", type=int, default=80)
    parser.add_argument(
        "--goal",
        nargs=3,
        type=float,
        default=(0.75, 0.75, 1.0),
    )
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--babble-samples", type=int, default=2)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    result = run_flight(
        steps=args.steps,
        goal=args.goal,
        seed=args.seed,
        babble_samples=args.babble_samples,
    )
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
