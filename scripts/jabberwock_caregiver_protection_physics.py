#!/usr/bin/env python3
"""Matched physics assay for exafferent caregiver protection."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
for _path in (ROOT, ROOT / "runners" / "dsl" / "python"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from domains.pybullet_humanoid_world import (  # noqa: E402
    HumanoidBodyConfiguration,
    PyBulletHumanoidWorld,
)


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_balance_adaptation_v1.json"


def _configuration(protocol: dict[str, Any]) -> HumanoidBodyConfiguration:
    body = protocol["body"]
    return HumanoidBodyConfiguration(
        time_step=body["time_step_seconds"],
        gravity_acceleration=body["gravity_acceleration"],
        action_frames=body["action_frames"],
        settling_frames=body["initial_settling_frames"],
        joint_twitch_radians=body["joint_twitch_radians"],
        maximum_joint_force=body["maximum_joint_force"],
        position_gain=body["position_gain"],
        velocity_gain=body["velocity_gain"],
    )


def run_assay(protocol_path: Path = DEFAULT_PROTOCOL) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    configuration = _configuration(protocol)
    arms = {}
    for name, protected in (("unbuffered", False), ("caregiver_buffered", True)):
        with PyBulletHumanoidWorld(
            configuration, seed=int(protocol["seed"])
        ) as world:
            before = world.observe()
            # Both timing values are read from this body. No experiment beam,
            # age, or fixed controller horizon is authored here.
            pulse_frames = max(1, len(before["support_contact_forces"]))
            response_frames = max(1, len(before["joints"]))
            weight = (
                before["body_mass"] * before["gravity_acceleration"]
            )
            kicked = world.apply_force_pulse(
                (0.0, 0.0, -weight), frames=pulse_frames
            )
            after = world.step(
                "humanoid_actuator_000",
                frames=response_frames,
                caregiver_protective_support=protected,
            )
            arms[name] = {
                "caregiver_protective_support_applied": int(protected),
                "pulse_frames_from_support_channels": pulse_frames,
                "response_frames_from_observable_joints": response_frames,
                "pre_height": before["base_position"][2],
                "post_pulse_height": kicked["base_position"][2],
                "post_response_height": after["base_position"][2],
                "post_response_vertical_velocity": after[
                    "base_linear_velocity"
                ][2],
                "caregiver_support_impulse_newton_seconds": after[
                    "caregiver_support_impulse_newton_seconds"
                ],
            }
    arms["caregiver_buffered"]["height_advantage_over_unbuffered"] = (
        arms["caregiver_buffered"]["post_response_height"]
        - arms["unbuffered"]["post_response_height"]
    )
    return {
        "experiment": "caregiver_protection_physics_v1",
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "matched_initial_state_seed_and_disturbance": True,
        "child_motor_command_identical": True,
        "caregiver_intervention_exafferent": True,
        "arms": arms,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_assay(args.protocol)
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
