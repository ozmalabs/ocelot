"""Run a matched hidden in-flight vehicle-damage adaptation trial."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from domains.gym_pybullet_drone_world import (  # noqa: E402
    AERIAL_ACTUATOR_COUNT,
    AERIAL_YAW_ACTUATOR_COUNT,
    AerialMechanicalCondition,
    AerialPropellerCondition,
    GymPyBulletDroneWorld,
)
from scripts.jabberwock_aerial_adaptation import run_flight  # noqa: E402


DEFAULT_PROTOCOL = ROOT / "protocols" / "aerial_damage_in_flight_v1.json"


def _closest_goal_distance(run: dict[str, Any], onset: int) -> float:
    return min(
        float(row["goal_distance_after"])
        for row in run["trace"]
        if int(row["epoch"]) >= onset
    )


def _post_damage_summary(run: dict[str, Any], onset: int) -> dict[str, Any]:
    post = [row for row in run["trace"] if int(row["epoch"]) >= onset]
    contacts = [row for row in post if int(row["contact_count"]) > 0]
    first_contact_action = (
        None if not contacts else int(contacts[0]["epoch"])
    )
    angular_speeds = [
        math.sqrt(
            sum(
                float(value) ** 2
                for value in row["angular_velocity_after"]
            )
        )
        for row in post
    ]
    return {
        "final_goal_distance": float(run["final_goal_distance"]),
        "closest_goal_distance": _closest_goal_distance(run, onset),
        "goal_reached_at_end": float(
            run["goal_reached_graph_assessment"]
        ),
        "learning_actions": sum(
            row["trial_status"] == "learned" for row in post
        ),
        "surprise_events": sum(float(row["surprise"] or 0.0) for row in post),
        "contact_actions": sum(int(row["contact_count"]) > 0 for row in post),
        "first_contact_action": first_contact_action,
        "contact_latency_seconds": (
            None
            if first_contact_action is None
            else (
                first_contact_action - onset + 1
            ) * float(run["action_duration_seconds"])
        ),
        "mean_angular_speed": sum(angular_speeds) / len(angular_speeds),
        "peak_angular_speed": max(angular_speeds),
    }


def _run_forced_action_controls(
    *,
    protocol: dict[str, Any],
    condition_arguments: dict[str, Any],
    prefix: list[str],
) -> list[dict[str, Any]]:
    controls = protocol.get("forced_action_controls")
    if controls is None:
        return []
    duration = float(protocol["action_duration_seconds"])
    rows = []
    for token in controls["tokens"]:
        with GymPyBulletDroneWorld(
            seed=int(protocol["seed"]),
            goal=protocol["goal"],
            action_duration_seconds=duration,
            enable_yaw_actuators=bool(
                protocol.get("enable_yaw_actuators", False)
            ),
            **condition_arguments,
        ) as world:
            for prefix_token in prefix:
                world.step(prefix_token)
            first_contact_offset = None
            peak_angular_speed = 0.0
            first_damaged_rpm = None
            final_observation = world.observe()
            for offset in range(int(controls["actions"])):
                final_observation = world.step(token)
                if first_damaged_rpm is None:
                    first_damaged_rpm = final_observation["motor_rpm"]
                angular_speed = math.sqrt(
                    sum(
                        float(value) ** 2
                        for value in final_observation[
                            "base_angular_velocity"
                        ]
                    )
                )
                peak_angular_speed = max(
                    peak_angular_speed,
                    angular_speed,
                )
                if (
                    first_contact_offset is None
                    and int(final_observation["contact_count"]) > 0
                ):
                    first_contact_offset = offset
            rows.append({
                "forced_token": token,
                "first_contact_latency_seconds": (
                    None
                    if first_contact_offset is None
                    else (first_contact_offset + 1) * duration
                ),
                "peak_angular_speed": peak_angular_speed,
                "first_damaged_action_motor_rpm": first_damaged_rpm,
                "final_altitude": float(
                    final_observation["base_position"][2]
                ),
            })
    return rows


def run_damage_trial(protocol_path: Path = DEFAULT_PROTOCOL) -> dict[str, Any]:
    """Execute adaptive and frozen graphs against the same hidden damage."""
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    babble_samples = int(protocol["babble_samples_per_actuator"])
    # The onset is derived from the intervention alphabet, not a controller
    # horizon: every opaque actuator receives the specified sample count.
    damage = protocol["damage"]
    yaw_actuators_enabled = bool(protocol.get("enable_yaw_actuators", False))
    if damage.get("onset") == "immediately_after_complete_motor_babble":
        actuator_count = AERIAL_ACTUATOR_COUNT + (
            AERIAL_YAW_ACTUATOR_COUNT if yaw_actuators_enabled else 0
        )
        onset = actuator_count * babble_samples
    else:
        onset = int(damage["onset_action"])
    damage_kind = damage["kind"]
    condition_arguments: dict[str, Any]
    if damage_kind == "motor_rpm_loss":
        condition_arguments = {
            "mechanical_condition": AerialMechanicalCondition(
                onset_action=onset,
                motor_rpm_retention=tuple(
                    float(value)
                    for value in damage["motor_rpm_retention"]
                ),
            )
        }
    elif damage_kind == "broken_propeller":
        condition_arguments = {
            "propeller_condition": AerialPropellerCondition(
                onset_action=onset,
                thrust_retention=tuple(
                    float(value) for value in damage["thrust_retention"]
                ),
                torque_retention=tuple(
                    float(value) for value in damage["torque_retention"]
                ),
            )
        }
    else:
        raise ValueError(f"unsupported aerial damage kind: {damage_kind!r}")
    common = {
        "steps": int(protocol["steps"]),
        "goal": tuple(float(value) for value in protocol["goal"]),
        "seed": int(protocol["seed"]),
        "babble_samples": babble_samples,
        **condition_arguments,
        "action_duration_seconds": float(
            protocol["action_duration_seconds"]
        ),
        "plasticity_stop_epoch": onset,
        "enable_yaw_actuators": yaw_actuators_enabled,
        "angular_stability_weight": float(
            protocol.get("angular_stability_weight", 0.0)
        ),
    }
    adaptive = run_flight(mode="adaptive_flight", **common)
    frozen = run_flight(mode="frozen_flight", **common)

    pre_damage_equal = all(
        adaptive["trace"][epoch]["selected_token"]
        == frozen["trace"][epoch]["selected_token"]
        and adaptive["trace"][epoch]["position_after"]
        == frozen["trace"][epoch]["position_after"]
        and adaptive["trace"][epoch]["model_displacement_after"]
        == frozen["trace"][epoch]["model_displacement_after"]
        for epoch in range(onset)
    )
    adaptive_summary = _post_damage_summary(adaptive, onset)
    frozen_summary = _post_damage_summary(frozen, onset)
    forced_action_controls = _run_forced_action_controls(
        protocol=protocol,
        condition_arguments=condition_arguments,
        prefix=[
            row["selected_token"]
            for row in adaptive["trace"][:onset]
        ],
    )
    return {
        "experiment": protocol["protocol"],
        "protocol_status": protocol["status"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "damage_onset_action": onset,
        "damage_kind": damage_kind,
        "state_before_damage": {
            "position": adaptive["trace"][onset - 1]["position_after"],
            "angular_velocity": adaptive["trace"][onset - 1][
                "angular_velocity_after"
            ],
        },
        "damage_is_observable_to_graph": False,
        "pre_damage_trajectories_identical": pre_damage_equal,
        "forced_action_controls": forced_action_controls,
        "adaptive": adaptive_summary,
        "frozen": frozen_summary,
        "paired_effect": {
            "final_distance_reduction": (
                frozen_summary["final_goal_distance"]
                - adaptive_summary["final_goal_distance"]
            ),
            "closest_distance_reduction": (
                frozen_summary["closest_goal_distance"]
                - adaptive_summary["closest_goal_distance"]
            ),
            "mean_angular_speed_reduction": (
                frozen_summary["mean_angular_speed"]
                - adaptive_summary["mean_angular_speed"]
            ),
        },
        "runs": {
            "adaptive": adaptive,
            "frozen": frozen,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_damage_trial(args.protocol)
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
