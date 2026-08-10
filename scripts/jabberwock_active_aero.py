"""Run graph-native active aerodynamics on a factorized wheeled body.

Python owns only simulator I/O and exact receipt transduction. The graph
selects calibration interventions, excites flow when an effector needs it,
constructs simultaneous motor programs, detects changed compound consequences,
and reopens calibration after hidden aerodynamic damage.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.embodied_graph_transducer import (  # noqa: E402
    add_unchecked_edge as _edge,
    pose_attrs,
    stamp_attrs,
    unique_neighbour,
    unique_node,
)
from domains.pybullet_robot_world import (  # noqa: E402
    AERODYNAMIC_SURFACE_COUNT,
    AerodynamicCondition,
    PyBulletRobotWorld,
)
from domains.sensorimotor_transducer import sensed_vector  # noqa: E402
from scripts.gen_embodied_motor_program_seed import FLOW_FEATURES  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


CONSEQUENCES = (
    "forward",
    "lateral",
    "vertical",
    "roll",
    "pitch",
    "turn",
    "normal_load",
    "drag",
    "energy",
)


def _state_attrs(observation: dict[str, Any]) -> dict[str, float]:
    velocity = sensed_vector(observation, "linear_velocity")
    return {
        "state_vx": float(velocity[0]),
        "state_vy": float(velocity[1]),
        "state_vz": float(velocity[2]),
        "state_flow_speed_squared": float(sum(value * value for value in velocity)),
        **{f"state_{feature}": 0.0 for feature in FLOW_FEATURES},
    }


def _model_attrs(option: dict[str, Any], ordinal: int) -> dict[str, Any]:
    attrs: dict[str, Any] = {
        "token": option["token"],
        "ordinal": float(ordinal),
        "actuator_group": float(option["group_ordinal"]),
        "activation_magnitude": float(option["activation_magnitude"]),
        "available": 1.0,
        "experience_count": 0.0,
        "last_learning_seq": 0.0,
        "recalibration_required": 0.0,
        "mean_flow_speed_squared": 0.0,
        "flow_variance_sum": 0.0,
        "semantics": "unknown",
    }
    for key in CONSEQUENCES:
        attrs[f"mean_{key}"] = 0.0
        attrs[f"flow_gain_{key}"] = 0.0
        attrs[f"flow_covariance_{key}"] = 0.0
        for feature in FLOW_FEATURES:
            attrs[f"{feature}_gain_{key}"] = 0.0
            attrs[f"{feature}_covariance_{key}"] = 0.0
    for feature in FLOW_FEATURES:
        attrs[f"mean_{feature}"] = 0.0
        attrs[f"{feature}_variance_sum"] = 0.0
    return attrs


def _issued_trial(agent: WorldAdapter, episode: Any, request_seq: int) -> Any:
    return unique_neighbour(
        agent,
        episode,
        "has_embodied_motor_program_trial",
        attrs={"status": "issued", "request_seq": float(request_seq)},
        description=f"active-aero motor trial for request {request_seq}",
    )


def _trial_tokens(agent: WorldAdapter, trial: Any) -> tuple[str, ...]:
    members = list(
        agent.inner.neighbours(trial, "commands_embodied_effector_model")
    )
    # A program operates FROM the body, so a never-commanded contributor is a
    # member of the trial like any other -- it is simply not something a
    # command can be issued to.  Membership and commandability are different
    # questions and conflating them produced "trial contains 4 members;
    # expected 5".  Absence reads as commandable, so a body plan that declares
    # no such contributor is unaffected.
    models = [
        model for model in members
        if float(agent.s.node(model)["attrs"].get("never_commanded", 0.0)) <= 0.5
    ]
    models.sort(
        key=lambda model: float(agent.s.node(model)["attrs"]["ordinal"])
    )
    tokens = tuple(
        str(agent.s.node(model)["attrs"]["token"])
        for model in models
    )
    expected = int(agent.s.node(trial)["attrs"]["expected_member_count"]) - (
        len(members) - len(models)
    )
    if len(tokens) != expected:
        raise RuntimeError(
            f"graph trial contains {len(tokens)} members; expected {expected}"
        )
    groups = {
        float(agent.s.node(model)["attrs"]["actuator_group"])
        for model in models
    }
    if len(groups) != len(models):
        raise RuntimeError("graph program commands one effector group more than once")
    return tokens


def _outcome_attrs(
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    request_seq: int,
) -> dict[str, Any]:
    pre_velocity = sensed_vector(before, "linear_velocity")
    post_velocity = sensed_vector(after, "linear_velocity")
    attrs: dict[str, Any] = {
        **pose_attrs(before, "pre"),
        **pose_attrs(after, "post"),
        **{
            f"pre_v{axis}": float(value)
            for axis, value in zip(("x", "y", "z"), pre_velocity)
        },
        **{
            f"post_v{axis}": float(value)
            for axis, value in zip(("x", "y", "z"), post_velocity)
        },
        "body_weight_newtons": float(after["body_mass"])
        * float(after["gravity_acceleration"]),
        "aerodynamic_dissipation_joules": float(
            after["aerodynamic_dissipation_joules"]
        ),
        "external_normal_force_newtons": float(
            after["external_normal_force_newtons"]
        ),
        "input_energy_joules": float(after["supplied_energy_joules"]),
        "request_seq": float(request_seq),
        "receipt_verified": 1.0,
        "processed": 0.0,
        "surprise_processed": 0.0,
        "provenance_kind": "raw_factorized_simulator_receipt",
    }
    for index, value in enumerate(before["wheel_normal_loads"]):
        attrs[f"pre_load_{index}"] = float(value)
    for index, value in enumerate(after["wheel_normal_loads"]):
        attrs[f"post_load_{index}"] = float(value)
    return attrs


def _settle_graph_request(
    agent: WorldAdapter,
    episode: Any,
    request_seq: int,
) -> None:
    """Advance authored asynchronous sheets until this request publishes."""
    seen: set[tuple[Any, ...]] = set()
    while True:
        attrs = agent.s.node(episode)["attrs"]
        if (
            float(attrs.get("action_ready", 0.0)) == 1.0
            and float(attrs.get("selected_decision_epoch", 0.0))
            == float(request_seq)
        ):
            return
        active = list(agent.inner.neighbours(
            episode,
            "has_active_embodied_motor_program",
        ))
        if len(active) == 1:
            plan = active[0]
            plan_attrs = agent.s.node(plan)["attrs"]
            if (
                float(plan_attrs.get("synthesis_yield_required", 0.0)) == 1.0
                and plan not in agent.inner.neighbours(
                    episode,
                    "resumes_embodied_motor_program",
                )
            ):
                agent.s.add_edge(
                    episode,
                    "resumes_embodied_motor_program",
                    plan,
                )
        signature = (
            attrs.get("program_mode"),
            attrs.get("program_decision_seq"),
            attrs.get("decision_status"),
            attrs.get("selected_decision_epoch"),
            attrs.get("last_program_trial_epoch"),
            tuple(
                (
                    agent.s.node(plan)["attrs"].get("member_count"),
                    agent.s.node(plan)["attrs"].get(
                        "synthesis_yield_required"
                    ),
                )
                for plan in active
            ),
            len(agent.inner.neighbours(
                episode,
                "has_embodied_motor_program_trial",
            )),
        )
        if signature in seen:
            raise RuntimeError(
                f"graph request {request_seq} reached a non-progressing "
                f"asynchronous state: {signature!r}"
            )
        seen.add(signature)
        agent.tick()


def run_active_aero(
    *,
    steps: int = 90,
    seed: int = 0,
    damage_onset: int | None = None,
    broken_surface: int = 2,
) -> dict[str, Any]:
    if steps < 1:
        raise ValueError("steps must be positive")
    if broken_surface not in range(AERODYNAMIC_SURFACE_COUNT):
        raise ValueError(
            "broken_surface must identify one declared aerodynamic surface"
        )

    agent = WorldAdapter(seeds=("embodied_motor_program",))
    policy = unique_node(agent, "EmbodiedMotorProgramPolicy")
    stamp_attrs(agent, policy, {
        "forward_weight": 20.0,
        "turn_weight": 50.0,
        "normal_load_weight": 4.0,
        "lateral_weight": 2.0,
        "drag_weight": 0.01,
        "energy_weight": 0.001,
    })
    damage = None
    if damage_onset is not None:
        retention = [1.0] * AERODYNAMIC_SURFACE_COUNT
        retention[broken_surface] = 0.0
        damage = AerodynamicCondition(
            onset_action=damage_onset,
            abrupt_retention=tuple(retention),
        )

    with PyBulletRobotWorld(
        "racecar_active_aero",
        seed=seed,
        aerodynamic_condition=damage,
    ) as world:
        observation = world.reset()
        episode = agent.s.add_node("EmbodiedMotorProgramEpisode", {
            "program_mode": "calibration",
            "program_request_seq": 0.0,
            "program_decision_seq": 0.0,
            "action_ready": 0.0,
            "calibration_complete": 0.0,
            "recalibration_count": 0.0,
            "decision_armed": 0.0,
            "decision_request_epoch": 0.0,
            "last_opened_decision_epoch": 0.0,
            "last_published_decision_epoch": 0.0,
            "last_program_trial_epoch": 0.0,
            "receipt_boundary_seq": 0.0,
            "target_forward": 0.12,
            "target_lateral": 0.0,
            "target_turn": 0.04,
            "target_normal_load": 0.25,
            **_state_attrs(observation),
        })
        _edge(agent, agent.agent, "has_embodied_motor_program_episode", episode)
        _edge(agent, agent.agent, "has_embodied_motor_episode", episode)
        for ordinal, option in enumerate(world.actuator_options()):
            model = agent.s.add_node(
                "EmbodiedEffectorModel",
                _model_attrs(option, ordinal),
            )
            _edge(agent, episode, "has_embodied_effector_model", model)

        trace: list[dict[str, Any]] = []
        for request_seq in range(1, steps + 1):
            stamp_attrs(agent, episode, {
                **_state_attrs(observation),
                "program_request_seq": float(request_seq),
                "action_ready": 0.0,
            })
            _settle_graph_request(agent, episode, request_seq)
            if float(agent.s.node(episode)["attrs"].get("action_ready", 0.0)) != 1.0:
                attrs = dict(agent.s.node(episode)["attrs"])
                trials = [
                    {
                        **dict(agent.s.node(candidate)["attrs"]),
                        "copied_members": len(agent.inner.neighbours(
                            candidate,
                            "commands_embodied_effector_model",
                        )),
                    }
                    for candidate in agent.inner.neighbours(
                        episode,
                        "has_embodied_motor_program_trial",
                    )
                    if agent.s.node(candidate)["attrs"].get("request_seq")
                    == float(request_seq)
                ]
                selected = attrs.get("selected_option_ref")
                selected_attrs = (
                    dict(agent.s.node(selected)["attrs"])
                    if selected is not None
                    else None
                )
                raise RuntimeError(
                    f"graph emitted no active-aero program for request "
                    f"{request_seq}: mode={attrs.get('program_mode')!r}, "
                    f"program_decision_seq={attrs.get('program_decision_seq')!r}, "
                    f"decision_status={attrs.get('decision_status')!r}, "
                    f"selected={selected_attrs!r}, trials={trials!r}"
                )
            trial = _issued_trial(agent, episode, request_seq)
            tokens = _trial_tokens(agent, trial)
            before = observation
            observation = world.step_program(tokens)
            if tuple(observation["last_motor_program_tokens"]) != tokens:
                raise RuntimeError("simulator program receipt does not match graph trial")
            outcome = agent.s.add_node(
                "EmbodiedMotorProgramOutcome",
                _outcome_attrs(before, observation, request_seq=request_seq),
            )
            _edge(agent, trial, "has_embodied_motor_program_outcome", outcome)
            agent.inner.set_attr(episode, "action_ready", 0.0)
            agent.tick()
            # A monotonic physical-receipt boundary wakes rules whose
            # neighbourhood predicates depend on the just-updated model set.
            # It carries no policy or completion verdict.
            agent.inner.set_attr(
                episode,
                "receipt_boundary_seq",
                float(request_seq),
            )
            agent.tick()

            trial_program = agent.inner.neighbours(
                trial,
                "enacts_embodied_motor_program",
            )[0]
            program_attrs = agent.s.node(trial_program)["attrs"]
            episode_attrs = agent.s.node(episode)["attrs"]
            trace.append({
                "request_seq": request_seq,
                "program_mode": episode_attrs["program_mode"],
                "program_source": program_attrs["source"],
                "tokens": list(tokens),
                "member_count": len(tokens),
                "flow_speed": math.sqrt(
                    max(0.0, float(episode_attrs["state_flow_speed_squared"]))
                ),
                "prediction_error_energy": float(
                    program_attrs.get("prediction_error_energy", 0.0)
                ),
                "recalibration_count": float(
                    episode_attrs["recalibration_count"]
                ),
                "damage_active": bool(
                    damage_onset is not None
                    and request_seq - 1 >= damage_onset
                ),
                "wheel_normal_loads": list(
                    observation["wheel_normal_loads"]
                ),
                "aerodynamic_dissipation_joules": float(
                    observation["aerodynamic_dissipation_joules"]
                ),
            })

        models = []
        for model in agent.inner.neighbours(
            episode,
            "has_embodied_effector_model",
        ):
            attrs = agent.s.node(model)["attrs"]
            models.append({
                key: attrs.get(key)
                for key in (
                    "token",
                    "ordinal",
                    "actuator_group",
                    "experience_count",
                    "mean_forward",
                    "mean_turn",
                    "mean_normal_load",
                    "flow_gain_normal_load",
                    "recalibration_required",
                )
            })
        models.sort(key=lambda row: float(row["ordinal"]))
        compound = [row for row in trace if row["member_count"] > 1]
        return {
            "morphology": "opaque_factorized_wheeled_body",
            "steps": steps,
            "damage_onset": damage_onset,
            "broken_surface": broken_surface if damage_onset is not None else None,
            "compound_program_count": len(compound),
            "maximum_program_width": max(
                (row["member_count"] for row in trace),
                default=0,
            ),
            "recalibration_count": float(
                agent.s.node(episode)["attrs"]["recalibration_count"]
            ),
            "final_program_mode": agent.s.node(episode)["attrs"]["program_mode"],
            "models": models,
            "trace": trace,
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=90)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--damage-onset", type=int)
    parser.add_argument("--broken-surface", type=int, default=2)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_active_aero(
        steps=args.steps,
        seed=args.seed,
        damage_onset=args.damage_onset,
        broken_surface=args.broken_surface,
    )
    payload = json.dumps(result, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
