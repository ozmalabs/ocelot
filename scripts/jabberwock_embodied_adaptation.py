"""Run graph-native, from-scratch adaptation in headless PyBullet.

Python is only the experiment and transduction boundary:

* create a fresh Rust substrate for each morphology;
* expose the world's opaque actuator tokens as graph nodes;
* copy raw pre/post sensor samples into receipt nodes;
* enact the token the graph selected; and
* record graph-held assessments and learned ActionModel rows.

It does not select an action, calculate a policy, learn a mapping, or decide
whether the goal was reached.
"""
from __future__ import annotations

import argparse
import json
import math
import os
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
    pose_attrs as _xyzq,
    stamp_attrs,
    unique_neighbour,
    unique_node as _one_node,
)
from domains.embodied_effector_topology import (  # noqa: E402
    bind_effector_models,
    install_name_free_effector_topology,
)
from domains.pybullet_robot_world import (  # noqa: E402
    MORPHOLOGIES,
    MechanicalCondition,
    MechanicalRandomization,
    PyBulletRobotWorld,
)
from domains.sensorimotor_transducer import (  # noqa: E402
    SensorimotorSensorConfiguration,
    sensed_vector,
    sensor_receipt_attrs,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


class EmbodiedRunError(RuntimeError):
    """An experiment failure with machine-readable action context."""

    def __init__(
        self,
        message: str,
        *,
        epoch: int | None = None,
        token: str | None = None,
    ) -> None:
        super().__init__(message)
        self.epoch = epoch
        self.token = token


def _write_state(
    agent: WorldAdapter,
    episode,
    observation: dict[str, Any],
    *,
    state_seq: int,
) -> None:
    """Mechanically mirror one raw body/goal sample onto the episode node."""
    goal = observation["goal_position"]
    stamp_attrs(agent, episode, {
        **basic_sensor_state_attrs(observation, state_seq=state_seq),
        "goal_x": float(goal[0]),
        "goal_y": float(goal[1]),
        "goal_z": float(goal[2]),
    })


def _mechanical_effort(observation: dict[str, Any]) -> float:
    """Reduce the raw joint torque vector to one scalar sensor channel."""
    return float(sum(abs(float(joint["applied_torque"])) for joint in observation["joints"]))


def _find_issued_trial(agent: WorldAdapter, episode, epoch: int):
    try:
        return unique_neighbour(
            agent,
            episode,
            "has_motor_trial",
            attrs={"status": "issued", "epoch": epoch},
            description=f"issued trials for epoch {epoch}",
        )
    except GraphBoundaryCardinalityError as exc:
        raise EmbodiedRunError(
            str(exc),
            epoch=epoch,
        ) from exc


def _model_rows(agent: WorldAdapter, episode) -> list[dict[str, Any]]:
    return neighbour_rows(
        agent,
        episode,
        "has_action_model",
        fields=(
                "token",
                "ordinal",
                "experience_count",
                "mean_forward",
                "mean_lateral",
                "mean_turn",
                "context_gain_forward",
                "context_gain_lateral",
                "context_gain_turn",
                "candidate_active",
                "candidate_attempted",
                "candidate_mean_forward",
                "candidate_mean_lateral",
                "candidate_mean_turn",
                "candidate_context_gain_forward",
                "candidate_context_gain_lateral",
                "candidate_context_gain_turn",
                "candidate_validation_count",
                "candidate_error_sum",
                "candidate_consolidated_error_sum",
                "candidate_promotion_count",
                "candidate_validation_success_count",
                "last_candidate_promotion_epoch",
                "contact_ema",
                "effort_ema",
                "energy_ema_joules",
                "last_prediction_error",
                "error_ema",
                "volatility_ema",
                "surprise_trace",
                "adaptation_state",
                "surprise_count",
                "last_surprise_epoch",
                "last_adaptation_rate",
        ),
    )


def run_episode(
    morphology: str,
    mode: str = "learning",
    *,
    steps: int = 120,
    goal: Iterable[float] = (2.0, 0.0, 0.0),
    seed: int = 0,
    babble_samples: int = 3,
    mechanical_condition: MechanicalCondition | None = None,
    mechanical_randomization: MechanicalRandomization | None = None,
    sensor_configuration: SensorimotorSensorConfiguration | None = None,
    post_calibration_goal: Iterable[float] | None = None,
    post_calibration_goal_offset: Iterable[float] | None = None,
    goal_change_epoch: int | None = None,
    heading_escape_enabled: bool = True,
    observer: Callable[[Any, dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """Run one fixed-length episode; all cognitive state is freshly booted."""
    valid_modes = {
        "learning",
        "adaptive_relearning",
        "frozen_model_control",
        "adaptive_probe",
        "frozen_probe_control",
        "adaptive_damage_navigation",
        "frozen_damage_navigation",
        "no_learning_control",
        "random_control",
        "shuffled_model_control",
    }
    if mode not in valid_modes:
        raise ValueError(f"mode must be one of {sorted(valid_modes)}")
    if steps < 1:
        raise ValueError("steps must be positive")
    if babble_samples < 1:
        raise ValueError("babble_samples must be positive")
    requested_goal_changes = sum(
        value is not None
        for value in (post_calibration_goal, post_calibration_goal_offset)
    )
    if requested_goal_changes > 1:
        raise ValueError(
            "supply only one of post_calibration_goal and "
            "post_calibration_goal_offset"
        )
    if (requested_goal_changes == 0) != (goal_change_epoch is None):
        raise ValueError(
            "a post-calibration goal and goal_change_epoch must be supplied together"
        )
    if goal_change_epoch is not None and not 0 <= goal_change_epoch < steps:
        raise ValueError("goal_change_epoch must be within the episode")

    agent = WorldAdapter(seeds=("embodied_adaptation",))
    policy = _one_node(agent, "EmbodiedPolicy")
    agent.inner.set_attr(policy, "babble_samples", float(babble_samples))
    # The seed is graph-held input to the random-like control hash. Physics is
    # otherwise intentionally deterministic; learning arms with the same goal
    # are exact replications, not independent stochastic samples.
    agent.inner.set_attr(policy, "control_seed", float(seed))
    agent.inner.set_attr(
        policy,
        "heading_escape_enabled",
        float(heading_escape_enabled),
    )
    plasticity_stop_epoch = (
        goal_change_epoch
        if goal_change_epoch is not None
        else (
            mechanical_condition.onset_action
            if mechanical_condition is not None
            else babble_samples * 9
        )
    )
    agent.inner.set_attr(
        policy, "plasticity_stop_epoch", float(plasticity_stop_epoch)
    )

    with PyBulletRobotWorld(
        morphology,
        seed=seed,
        goal=goal,
        mechanical_condition=mechanical_condition,
        mechanical_randomization=mechanical_randomization,
        sensor_configuration=sensor_configuration,
    ) as world:
        observation = world.reset(goal=goal)
        initial_goal = tuple(float(value) for value in observation["goal_position"])
        initial_position = tuple(float(value) for value in observation["base_position"])
        episode = agent.s.add_node("EmbodiedEpisode", {
            "mode": mode,
            "morphology_provenance": "external_body_identifier_not_used_by_rules",
            "action_ready": 0.0,
            "epoch": 0.0,
            "request_seq": 0.0,
            "decision_seq": 0.0,
            "decision_count": 0.0,
            "last_trial_epoch": -1.0,
            "state_seq": 0.0,
            "measured_state_seq": -1.0,
            "goal_distance": 0.0,
            "goal_progress": 0.0,
            "last_action_goal_progress": 0.0,
            "last_action_decision_kind": "",
            "control_regime": "",
            "goal_heading_error": 0.0,
            "previous_goal_heading_error": 0.0,
            "last_heading_improvement": 0.0,
            "heading_escape_viable": 1.0,
            "goal_reached": 0.0,
            "recalibration_remaining": 0.0,
            "recalibration_cycles": 0.0,
            "last_observed_forward": 0.0,
            "last_observed_lateral": 0.0,
            "last_observed_turn": 0.0,
            "history_context_forward": 0.0,
            "history_context_lateral": 0.0,
            "history_context_turn": 0.0,
            "body_mass": float(observation["body_mass"]),
            "gravity_acceleration": float(observation["gravity_acceleration"]),
        })
        _edge(agent, agent.agent, "has_embodied_episode", episode)

        options = world.actuator_options()
        effector_topology = install_name_free_effector_topology(
            agent, episode, options
        )
        if observer is not None:
            observer(world, {
                "phase": "cold_start",
                "action": -1,
                "observation": observation,
                "event": "fresh_graph",
            })
        action_models = {}
        for ordinal, option in enumerate(options):
            model = agent.s.add_node("ActionModel", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "experience_count": 0.0,
                "mean_forward": 0.0,
                "mean_lateral": 0.0,
                "mean_turn": 0.0,
                "context_gain_forward": 0.0,
                "context_gain_lateral": 0.0,
                "context_gain_turn": 0.0,
                "candidate_active": 0.0,
                "candidate_attempted": 0.0,
                "candidate_mean_forward": 0.0,
                "candidate_mean_lateral": 0.0,
                "candidate_mean_turn": 0.0,
                "candidate_context_gain_forward": 0.0,
                "candidate_context_gain_lateral": 0.0,
                "candidate_context_gain_turn": 0.0,
                "candidate_validation_count": 0.0,
                "candidate_error_sum": 0.0,
                "candidate_consolidated_error_sum": 0.0,
                "candidate_promotion_count": 0.0,
                "candidate_validation_success_count": 0.0,
                "last_candidate_promotion_epoch": -1.0,
                "contact_ema": 0.0,
                "effort_ema": 0.0,
                "energy_ema_joules": 0.0,
                "last_prediction_error": 0.0,
                "error_ema": 0.0,
                "volatility_ema": 0.0,
                "surprise_trace": 0.0,
                "adaptation_state": 0.0,
                "surprise_count": 0.0,
                "last_surprise_epoch": -1.0,
                "last_adaptation_rate": 0.0,
                "last_update_epoch": -1.0,
                "provenance_kind": "untrained_fresh_action_model",
            })
            actuator = agent.s.add_node("OpaqueActuator", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "semantics": "unknown",
            })
            _edge(agent, episode, "has_action_model", model)
            _edge(agent, model, "models_actuator", actuator)
            action_models[option["token"]] = model
        bind_effector_models(agent, effector_topology, action_models)

        trace: list[dict[str, Any]] = []
        initial_goal_distance = None
        enacted_post_calibration_goal = None
        for epoch in range(steps):
            if goal_change_epoch is not None and epoch == goal_change_epoch:
                if post_calibration_goal is not None:
                    enacted_post_calibration_goal = tuple(
                        float(value) for value in post_calibration_goal
                    )
                else:
                    offset = tuple(
                        float(value) for value in post_calibration_goal_offset
                    )
                    if len(offset) != 3:
                        raise ValueError(
                            "post_calibration_goal_offset must contain three values"
                        )
                    enacted_post_calibration_goal = tuple(
                        float(observation["base_position"][index]) + offset[index]
                        for index in range(3)
                    )
                observation = world.set_goal(enacted_post_calibration_goal)
            _write_state(agent, episode, observation, state_seq=epoch * 2 + 1)
            agent.inner.set_attr(episode, "epoch", float(epoch))
            agent.inner.set_attr(episode, "request_seq", float(epoch + 1))
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()

            episode_attrs = agent.s.node(episode)["attrs"]
            if initial_goal_distance is None:
                initial_goal_distance = float(episode_attrs["goal_distance"])
            token = episode_attrs.get("selected_token")
            if not isinstance(token, str) or float(episode_attrs.get("action_ready", 0.0)) != 1.0:
                raise EmbodiedRunError(
                    f"graph did not issue an action at epoch {epoch}",
                    epoch=epoch,
                )
            trial = _find_issued_trial(agent, episode, epoch)
            trial_attrs_before = dict(agent.s.node(trial)["attrs"])
            trial_token = trial_attrs_before.get("token")
            if trial_token != token:
                raise EmbodiedRunError(
                    f"graph trial token {trial_token!r} does not match selected "
                    f"token {token!r} at epoch {epoch}",
                    epoch=epoch,
                    token=token,
                )
            trial_models = list(agent.inner.neighbours(trial, "uses_action_model"))
            if len(trial_models) != 1:
                raise EmbodiedRunError(
                    f"graph attached {len(trial_models)} models to trial at epoch {epoch}",
                    epoch=epoch,
                    token=trial_token,
                )
            model = trial_models[0]
            model_count_before = float(
                agent.s.node(model)["attrs"].get("experience_count", 0.0)
            )
            model_surprise_count_before = float(
                agent.s.node(model)["attrs"].get("surprise_count", 0.0)
            )
            model_candidate_validation_count_before = float(
                agent.s.node(model)["attrs"].get(
                    "candidate_validation_count", 0.0
                )
            )
            model_candidate_error_sum_before = float(
                agent.s.node(model)["attrs"].get("candidate_error_sum", 0.0)
            )
            model_candidate_consolidated_error_sum_before = float(
                agent.s.node(model)["attrs"].get(
                    "candidate_consolidated_error_sum", 0.0
                )
            )
            goal_distance_before = float(episode_attrs["goal_distance"])

            # Enact the token on the graph-authored MotorTrial itself. The
            # episode copy was checked above; neither Python value is a
            # fallback policy.
            next_observation = world.step(trial_token)
            if observer is not None:
                observer(world, {
                    "phase": (
                        "motor_babble"
                        if epoch < babble_samples * len(options)
                        else "goal_navigation"
                    ),
                    "action": epoch,
                    "observation": next_observation,
                    "event": (
                        "damage_onset"
                        if (
                            mechanical_condition is not None
                            and epoch == mechanical_condition.onset_action
                        )
                        else (
                            "goal_changed"
                            if goal_change_epoch is not None
                            and epoch == goal_change_epoch
                            else None
                        )
                    ),
                    "decision_kind": episode_attrs["decision_kind"],
                })
            receipt_verified = float(
                next_observation.get("last_actuator_token") == trial_token
            )
            if receipt_verified != 1.0:
                raise EmbodiedRunError(
                    f"simulator receipt token "
                    f"{next_observation.get('last_actuator_token')!r} does not "
                    f"match MotorTrial token {trial_token!r} at epoch {epoch}",
                    epoch=epoch,
                    token=trial_token,
                )
            trial_attrs = agent.s.node(trial)["attrs"]
            agent.inner.set_attr(
                trial,
                "predicted_task_progress",
                float(trial_attrs.get("predicted_task_progress", 0.0)),
            )
            outcome_attrs = {
                **_xyzq(observation, "pre"),
                **_xyzq(next_observation, "post"),
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
                "pre_contact_count": float(
                    observation["sensed_contact_count"]
                ),
                "contact_count": float(
                    next_observation["sensed_contact_count"]
                ),
                "pre_contact_force_newtons": float(
                    observation.get("contact_force_newtons", 0.0)
                ),
                "contact_force_newtons": float(
                    next_observation.get("contact_force_newtons", 0.0)
                ),
                "effort": _mechanical_effort(next_observation),
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
                "provenance_kind": "raw_simulator_receipt",
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
            }
            outcome = agent.s.add_node("TransitionObservation", outcome_attrs)
            _edge(agent, trial, "has_transition_outcome", outcome)
            agent.inner.set_attr(episode, "action_ready", 0.0)
            _write_state(agent, episode, next_observation, state_seq=epoch * 2 + 2)
            agent.tick()

            final_episode_attrs = agent.s.node(episode)["attrs"]
            final_outcome_attrs = agent.s.node(outcome)["attrs"]
            final_model_attrs = agent.s.node(model)["attrs"]
            trace.append({
                "epoch": epoch,
                "trial_id": str(trial),
                "outcome_id": str(outcome),
                "model_id": str(model),
                "selected_token": token,
                "trial_token": trial_token,
                "receipt_verified": receipt_verified,
                "predicted_token": episode_attrs.get("predicted_token"),
                "decision_kind": episode_attrs["decision_kind"],
                "control_regime": episode_attrs.get("control_regime"),
                "goal_heading_error_before": trial_attrs_before.get(
                    "goal_heading_error_before"
                ),
                "trial_status": agent.s.node(trial)["attrs"]["status"],
                "pre_base_position": list(observation["base_position"]),
                "pre_base_orientation_xyzw": list(
                    observation["base_orientation_xyzw"]
                ),
                "post_base_position": list(next_observation["base_position"]),
                "post_base_orientation_xyzw": list(
                    next_observation["base_orientation_xyzw"]
                ),
                "goal_position": list(next_observation["goal_position"]),
                "predicted_forward": trial_attrs_before.get("predicted_forward"),
                "predicted_lateral": trial_attrs_before.get("predicted_lateral"),
                "predicted_turn": trial_attrs_before.get("predicted_turn"),
                "candidate_predicted_forward": trial_attrs_before.get(
                    "candidate_predicted_forward"
                ),
                "candidate_predicted_lateral": trial_attrs_before.get(
                    "candidate_predicted_lateral"
                ),
                "candidate_predicted_turn": trial_attrs_before.get(
                    "candidate_predicted_turn"
                ),
                "observed_forward": final_outcome_attrs.get("observed_forward"),
                "observed_lateral": final_outcome_attrs.get("observed_lateral"),
                "observed_turn": final_outcome_attrs.get("observed_turn"),
                "history_context_forward": final_outcome_attrs.get(
                    "history_context_forward"
                ),
                "history_context_lateral": final_outcome_attrs.get(
                    "history_context_lateral"
                ),
                "history_context_turn": final_outcome_attrs.get(
                    "history_context_turn"
                ),
                "model_experience_count_before": model_count_before,
                "model_experience_count_after": final_model_attrs.get(
                    "experience_count"
                ),
                "model_surprise_count_before": model_surprise_count_before,
                "model_surprise_count_after": final_model_attrs.get(
                    "surprise_count"
                ),
                "model_candidate_validation_count_before": (
                    model_candidate_validation_count_before
                ),
                "model_candidate_error_sum_before": (
                    model_candidate_error_sum_before
                ),
                "model_candidate_consolidated_error_sum_before": (
                    model_candidate_consolidated_error_sum_before
                ),
                "surprise": final_outcome_attrs.get("surprise", 0.0),
                "opened_recalibration": final_outcome_attrs.get(
                    "opened_recalibration", 0.0
                ),
                "candidate_opened": final_outcome_attrs.get(
                    "candidate_opened", 0.0
                ),
                "candidate_promoted": final_outcome_attrs.get(
                    "candidate_promoted", 0.0
                ),
                "candidate_change_validated": final_outcome_attrs.get(
                    "candidate_change_validated", 0.0
                ),
                "candidate_squared_error": final_outcome_attrs.get(
                    "candidate_squared_error"
                ),
                "consolidated_squared_error": final_outcome_attrs.get(
                    "consolidated_squared_error"
                ),
                "adaptation_rate": final_outcome_attrs.get(
                    "adaptation_rate", 0.0
                ),
                "model_error_ema_after": final_model_attrs.get("error_ema"),
                "model_volatility_ema_after": final_model_attrs.get(
                    "volatility_ema"
                ),
                "model_adaptation_state_after": final_model_attrs.get(
                    "adaptation_state"
                ),
                "model_context_gain_forward_after": final_model_attrs.get(
                    "context_gain_forward"
                ),
                "model_context_gain_lateral_after": final_model_attrs.get(
                    "context_gain_lateral"
                ),
                "model_context_gain_turn_after": final_model_attrs.get(
                    "context_gain_turn"
                ),
                "model_candidate_active_after": final_model_attrs.get(
                    "candidate_active"
                ),
                "model_candidate_validation_count_after": (
                    final_model_attrs.get("candidate_validation_count")
                ),
                "model_candidate_promotion_count_after": (
                    final_model_attrs.get("candidate_promotion_count")
                ),
                "model_candidate_validation_success_count_after": (
                    final_model_attrs.get(
                        "candidate_validation_success_count"
                    )
                ),
                "goal_distance_before": goal_distance_before,
                "goal_distance_after": final_episode_attrs.get("goal_distance"),
                "goal_distance": final_episode_attrs.get("goal_distance"),
                "goal_progress": final_episode_attrs.get("goal_progress"),
                "goal_heading_error_after": final_episode_attrs.get(
                    "goal_heading_error"
                ),
                "heading_improvement": final_episode_attrs.get(
                    "last_heading_improvement"
                ),
                "heading_escape_viable": final_episode_attrs.get(
                    "heading_escape_viable"
                ),
                "goal_reached": final_episode_attrs.get("goal_reached"),
                "prediction_error": final_outcome_attrs.get("prediction_error"),
                "contact_count": outcome_attrs["contact_count"],
                "effort": outcome_attrs["effort"],
                "input_energy_joules": outcome_attrs[
                    "input_energy_joules"
                ],
                "motor_net_energy_joules": final_episode_attrs.get(
                    "motor_net_energy_joules"
                ),
            })
            observation = next_observation

        final_attrs = agent.s.node(episode)["attrs"]
        return {
            "morphology": morphology,
            "mode": mode,
            "seed": seed,
            "steps": steps,
            "mechanical_condition": (
                None
                if mechanical_condition is None
                else {
                    "onset_action": mechanical_condition.onset_action,
                    "abrupt_retention": list(
                        mechanical_condition.abrupt_retention
                    ),
                    "wear_per_use": list(mechanical_condition.wear_per_use),
                    "minimum_retention": mechanical_condition.minimum_retention,
                }
            ),
            "mechanical_randomization": {
                "base_mass_scale": (
                    mechanical_randomization or MechanicalRandomization()
                ).base_mass_scale,
                "lateral_friction": (
                    mechanical_randomization or MechanicalRandomization()
                ).lateral_friction,
                "rolling_friction": (
                    mechanical_randomization or MechanicalRandomization()
                ).rolling_friction,
                "motor_force_scale": (
                    mechanical_randomization or MechanicalRandomization()
                ).motor_force_scale,
            },
            "fresh_substrate": True,
            "policy_owner": "rust_graph",
            "heading_escape_enabled": heading_escape_enabled,
            "action_alphabet": [option["token"] for option in options],
            "initial_position": initial_position,
            "initial_goal_position": initial_goal,
            "goal_change_epoch": goal_change_epoch,
            "enacted_post_calibration_goal": enacted_post_calibration_goal,
            "final_position": tuple(float(value) for value in observation["base_position"]),
            "goal_position": tuple(float(value) for value in observation["goal_position"]),
            "initial_goal_distance": initial_goal_distance,
            "final_goal_distance": final_attrs.get("goal_distance"),
            "goal_reached_graph_assessment": final_attrs.get("goal_reached"),
            "decision_count": final_attrs.get("decision_count"),
            "motor_input_energy_joules_graph_assessment": final_attrs.get(
                "motor_input_energy_joules",
                0.0,
            ),
            "motor_net_energy_joules_graph_assessment": final_attrs.get(
                "motor_net_energy_joules",
                0.0,
            ),
            "motor_peak_power_watts_graph_assessment": final_attrs.get(
                "motor_peak_power_watts",
                0.0,
            ),
            "motor_cost_of_transport_graph_assessment": final_attrs.get(
                "motor_cost_of_transport",
                0.0,
            ),
            "candidate_min_validation_observations": agent.s.node(policy)[
                "attrs"
            ].get("candidate_min_validation_observations"),
            "candidate_promotion_margin": agent.s.node(policy)["attrs"].get(
                "candidate_promotion_margin"
            ),
            "models": _model_rows(agent, episode),
            "trace": trace,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--morphologies",
        nargs="+",
        choices=MORPHOLOGIES,
        default=list(MORPHOLOGIES),
    )
    parser.add_argument(
        "--mode",
        choices=(
            "learning",
            "no_learning_control",
            "random_control",
            "shuffled_model_control",
            "adaptive_relearning",
            "frozen_model_control",
            "adaptive_probe",
            "frozen_probe_control",
            "adaptive_damage_navigation",
            "frozen_damage_navigation",
            "both",
            "all",
            "adaptation_pair",
            "probe_pair",
            "damage_navigation_pair",
        ),
        default="both",
    )
    parser.add_argument("--steps", type=int, default=120)
    parser.add_argument("--babble-samples", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--goal", nargs=3, type=float, default=(2.0, 0.0, 0.0))
    parser.add_argument(
        "--mechanical-condition",
        choices=("healthy", "damage", "wear", "combined"),
        default="healthy",
    )
    parser.add_argument("--condition-onset", type=int, default=45)
    parser.add_argument("--affected-channel", type=int, choices=(0, 1), default=0)
    parser.add_argument("--damage-retention", type=float, default=0.25)
    parser.add_argument("--wear-per-use", type=float, default=0.012)
    parser.add_argument("--minimum-retention", type=float, default=0.2)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="write --json-out without also printing the full trace",
    )
    args = parser.parse_args(argv)

    if args.mode == "both":
        modes = ("learning", "no_learning_control")
    elif args.mode == "adaptation_pair":
        modes = ("adaptive_relearning", "frozen_model_control")
    elif args.mode == "probe_pair":
        modes = ("adaptive_probe", "frozen_probe_control")
    elif args.mode == "damage_navigation_pair":
        modes = (
            "adaptive_damage_navigation",
            "frozen_damage_navigation",
        )
    elif args.mode == "all":
        modes = (
            "learning",
            "no_learning_control",
            "random_control",
            "shuffled_model_control",
        )
    else:
        modes = (args.mode,)
    mechanical_condition = None
    if args.mechanical_condition != "healthy":
        abrupt = [1.0, 1.0]
        wear = [0.0, 0.0]
        if args.mechanical_condition in {"damage", "combined"}:
            abrupt[args.affected_channel] = args.damage_retention
        if args.mechanical_condition in {"wear", "combined"}:
            wear[args.affected_channel] = args.wear_per_use
        mechanical_condition = MechanicalCondition(
            onset_action=args.condition_onset,
            abrupt_retention=tuple(abrupt),
            wear_per_use=tuple(wear),
            minimum_retention=args.minimum_retention,
        )
    results = []
    failures = []
    for morphology in args.morphologies:
        for mode in modes:
            try:
                results.append(
                    run_episode(
                        morphology,
                        mode,
                        steps=args.steps,
                        goal=args.goal,
                        seed=args.seed,
                        babble_samples=args.babble_samples,
                        mechanical_condition=mechanical_condition,
                    )
                )
            except Exception as exc:  # noqa: BLE001 - preserve every failed row
                failures.append({
                    "morphology": morphology,
                    "mode": mode,
                    "seed": args.seed,
                    "goal": list(args.goal),
                    "steps": args.steps,
                    "babble_samples": args.babble_samples,
                    "mechanical_condition": args.mechanical_condition,
                    "epoch": getattr(exc, "epoch", None),
                    "token": getattr(exc, "token", None),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                })
    payload = {
        "experiment": "graph_native_embodied_adaptation",
        "simulator": "pybullet_direct",
        "results": results,
        "failures": failures,
    }
    rendered = json.dumps(payload, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + os.linesep, encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
