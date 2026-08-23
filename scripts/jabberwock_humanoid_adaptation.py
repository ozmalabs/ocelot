"""Test graph-native opaque-joint balance learning on a full humanoid."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import sys
from typing import Any


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
from domains.pybullet_humanoid_world import (  # noqa: E402
    HUMANOID_ASSET,
    HumanoidBodyConfiguration,
    PyBulletHumanoidWorld,
)
from domains.humanoid_kinematics_study import (  # noqa: E402
    add_kinematic_receipt_points,
    update_kinematic_coordinates,
)
from domains.sensorimotor_transducer import (  # noqa: E402
    sensed_vector,
    sensor_receipt_attrs,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402


DEFAULT_PROTOCOL = ROOT / "protocols" / "humanoid_balance_adaptation_v1.json"


def _gravity_relative_up_axis(
    orientation_xyzw: tuple[float, ...],
) -> tuple[float, float, float]:
    """Transduce the body's local up axis against world gravity."""
    x, y, z, w = orientation_xyzw
    return (
        2.0 * (x * z + w * y),
        2.0 * (y * z - w * x),
        1.0 - 2.0 * (x * x + y * y),
    )


def _gravity_relative_orientation_class(
    local_up_in_world: tuple[float, float, float],
) -> int:
    axis = max(range(3), key=lambda index: abs(local_up_in_world[index]))
    return (axis + 1) * (1 if local_up_in_world[axis] >= 0.0 else -1)


def _write_state(
    agent: WorldAdapter,
    episode,
    observation: dict[str, Any],
    *,
    state_seq: int,
    state_is_receipt: bool = False,
) -> None:
    angular = sensed_vector(observation, "angular_velocity")
    linear = sensed_vector(observation, "linear_velocity")
    centre_of_mass = observation.get(
        "whole_body_centre_of_mass",
        sensed_vector(observation, "position"),
    )
    linear_momentum = observation.get(
        "whole_body_linear_momentum",
        (0.0, 0.0, 0.0),
    )
    angular_momentum = observation.get(
        "whole_body_angular_momentum",
        (0.0, 0.0, 0.0),
    )
    support = observation["support_contact_forces"]
    whole_body_support = observation.get(
        "whole_body_support_contacts",
        support,
    )
    whole_body_positions = tuple(
        tuple(float(value) for value in row["world_position"])
        for row in whole_body_support
    )
    support_extent_squared = max(
        (
            sum((a - b) * (a - b) for a, b in zip(left, right))
            for index, left in enumerate(whole_body_positions)
            for right in whole_body_positions[index + 1:]
        ),
        default=0.0,
    )
    joint_configuration = tuple(
        float(joint["position"])
        for joint in observation.get("joints", ())
    )
    joint_velocities = tuple(
        float(joint["velocity"])
        for joint in observation.get("joints", ())
    )
    if len(support) != 2:
        raise RuntimeError(
            f"expected two load-bearing support links, found {len(support)}"
        )
    orientation = tuple(
        float(value) for value in observation["base_orientation_xyzw"]
    )
    gravity_relative_orientation_class = (
        _gravity_relative_orientation_class(
            _gravity_relative_up_axis(orientation)
        )
    )
    attrs = {
        **basic_sensor_state_attrs(observation, state_seq=state_seq),
        "state_wx": float(angular[0]),
        "state_wy": float(angular[1]),
        "state_wz": float(angular[2]),
        "state_vx": float(linear[0]),
        "state_vy": float(linear[1]),
        "state_vz": float(linear[2]),
        "state_com_x": float(centre_of_mass[0]),
        "state_com_y": float(centre_of_mass[1]),
        "state_com_z": float(centre_of_mass[2]),
        "state_linear_momentum_x": float(linear_momentum[0]),
        "state_linear_momentum_y": float(linear_momentum[1]),
        "state_linear_momentum_z": float(linear_momentum[2]),
        "state_angular_momentum_x": float(angular_momentum[0]),
        "state_angular_momentum_y": float(angular_momentum[1]),
        "state_angular_momentum_z": float(angular_momentum[2]),
        "state_peak_contact_force_newtons": float(
            observation.get("peak_contact_force_newtons", 0.0)
        ),
        "state_contact_force_newtons": float(
            observation.get("contact_force_newtons", 0.0)
        ),
        "state_contact_normal_impulse_newton_seconds": float(
            observation.get(
                "contact_normal_impulse_newton_seconds",
                0.0,
            )
        ),
        "state_contact_count_raw": float(len(observation.get("contacts", ()))),
        "state_whole_body_support_count": float(len(whole_body_support)),
        "state_whole_body_support_extent_squared": support_extent_squared,
        "state_body_length_scale": float(
            observation.get("body_length_scale", 0.0)
        ),
        "state_support_0_force": float(support[0]["normal_force"]),
        "state_support_1_force": float(support[1]["normal_force"]),
        "state_joint_configuration": joint_configuration,
        "state_motor_configuration_shape": tuple(
            observation.get("motor_configuration_shape", ())
        ),
        "state_joint_count": float(len(joint_configuration)),
        "state_joint_velocity_energy": sum(
            velocity * velocity for velocity in joint_velocities
        ),
        "state_gravity_relative_orientation_class": float(
            gravity_relative_orientation_class
        ),
        "state_motor_reference_kind": observation.get(
            "motor_reference_kind",
            "current_sensed_configuration",
        ),
        "state_motor_reference_positions": tuple(
            observation.get("motor_reference_positions", ())
        ),
        "state_motor_target_positions": tuple(
            observation.get("motor_target_positions", ())
        ),
        "state_motor_command_displacements": tuple(
            observation.get("motor_command_displacements", ())
        ),
    }
    for support_ordinal, row in enumerate(support):
        position = row["world_position"]
        for axis_ordinal, axis in enumerate(("x", "y", "z")):
            attrs[f"state_support_{support_ordinal}_{axis}"] = float(
                position[axis_ordinal]
            )
    attrs.update({
        "active_distal_support_count": float(sum(
            float(row["normal_force"]) > 0.0
            for row in support
        )),
        "active_support_count": float(len(whole_body_support)),
        "state_is_receipt": float(state_is_receipt),
    })
    stamp_attrs(agent, episode, attrs)
    update_kinematic_coordinates(
        agent,
        episode,
        observation,
        state_seq=state_seq,
    )


def _body_axis_tilt(observation: dict[str, Any]) -> float:
    qx, qy, qz, qw = (
        float(value) for value in observation["base_orientation_xyzw"]
    )
    z_x = 2.0 * (qx * qz + qy * qw)
    z_y = 2.0 * (qy * qz - qx * qw)
    return math.sqrt(z_x * z_x + z_y * z_y)


def _issued_trial(agent: WorldAdapter, episode, request_seq: int):
    try:
        return unique_neighbour(
            agent,
            episode,
            "has_humanoid_motor_trial",
            attrs={"request_seq": request_seq, "status": "issued"},
            description=f"trials for request {request_seq}",
        )
    except GraphBoundaryCardinalityError as exc:
        matches = [
            trial
            for trial in agent.inner.neighbours(
                episode, "has_humanoid_motor_trial"
            )
            if agent.s.node(trial)["attrs"].get("request_seq") == request_seq
            and agent.s.node(trial)["attrs"].get("status") == "issued"
        ]
        diagnostics = []
        for trial in matches:
            attrs = agent.s.node(trial)["attrs"]
            diagnostics.append({
                "id": str(trial),
                "decision_kind": attrs.get("decision_kind"),
                "collapse_kind": attrs.get("collapse_kind"),
                "token": attrs.get("token"),
                "enacted_program_count": len(agent.inner.neighbours(
                    trial, "enacts_humanoid_motor_program"
                )),
                "synthesized_program_count": len(agent.inner.neighbours(
                    trial, "synthesized_humanoid_motor_program"
                )),
                "recalled_transition_count": len(agent.inner.neighbours(
                    trial, "enacts_humanoid_motor_transition"
                )),
            })
        raise RuntimeError(f"{exc}; diagnostics={diagnostics!r}") from exc


def _trial_motor_tokens(
    agent: WorldAdapter,
    trial,
) -> tuple[str, ...]:
    """Mechanically read graph-authored motor-program membership."""
    programs = agent.inner.neighbours(
        trial,
        "enacts_humanoid_motor_program",
    )
    if len(programs) > 1:
        raise RuntimeError("trial enacts more than one motor program")
    if programs:
        members = agent.inner.neighbours(
            programs[0],
            "includes_humanoid_phase_action_model",
        )
        ordered = sorted(
            members,
            key=lambda member: (
                float(
                    agent.s.node(member)["attrs"].get("ordinal", 0.0)
                ),
                str(agent.s.node(member)["attrs"].get("token", "")),
            ),
        )
        tokens = tuple(dict.fromkeys(
            agent.s.node(member)["attrs"].get("token")
            for member in ordered
        ))
        if not tokens or not all(isinstance(token, str) for token in tokens):
            raise RuntimeError("graph motor program has invalid membership")
        return tokens

    trial_attrs = agent.s.node(trial)["attrs"]
    return tuple(dict.fromkeys((
        trial_attrs.get("token"),
        trial_attrs.get("secondary_token"),
    )))


def _resume_graph_motor_synthesis(
    agent: WorldAdapter,
    episode,
) -> dict[str, Any]:
    """Mechanically resume graph-authored asynchronous synthesis yields."""
    previous_width = 0.0
    previous_resume_steps: int | None = None
    resume_edge_was_present: bool | None = None
    while True:
        attrs = dict(agent.s.node(episode)["attrs"])
        if attrs.get("action_ready") == 1.0:
            return attrs
        active = agent.inner.neighbours(
            episode,
            "has_active_humanoid_motor_program",
        )
        if len(active) != 1:
            return attrs
        program = active[0]
        program_attrs = agent.s.node(program)["attrs"]
        if program_attrs.get("synthesis_yield_required") != 1.0:
            return attrs
        width = float(program_attrs.get("member_count", 0.0))
        if width <= previous_width:
            members = agent.inner.neighbours(
                program, "includes_humanoid_phase_action_model"
            )
            member_rows = [
                {
                    key: agent.s.node(member)["attrs"].get(key)
                    for key in (
                        "token",
                        "ordinal",
                        "actuator_group",
                        "support_phase",
                        "context_id",
                    )
                }
                for member in members
            ]
            frontiers = [
                dict(agent.s.node(frontier)["attrs"])
                for frontier in agent.inner.neighbours(
                    program, "has_humanoid_motor_program_frontier"
                )
            ]
            raise RuntimeError(
                "graph motor synthesis yielded without adding a member: "
                f"previous_width={previous_width}, width={width}, "
                f"program={program_attrs!r}, members={member_rows!r}, "
                f"frontiers={frontiers!r}, resume_edge_present="
                f"{program in agent.inner.neighbours(episode, 'resumes_humanoid_motor_program')}, "
                f"resume_edge_was_present={resume_edge_was_present}, "
                f"previous_resume_steps={previous_resume_steps}, "
                f"episode_request_seq={attrs.get('request_seq')!r}"
            )
        previous_width = width
        resume_edge_was_present = program in agent.inner.neighbours(
            episode, "resumes_humanoid_motor_program"
        )
        agent.s.add_edge(
            episode,
            "resumes_humanoid_motor_program",
            program,
        )
        previous_resume_steps = agent.tick()
        if previous_resume_steps >= 100_000:
            raise RuntimeError(
                "graph motor synthesis resume did not reach a fixpoint: "
                f"steps={previous_resume_steps}, request_seq="
                f"{attrs.get('request_seq')}, program={program_attrs!r}"
            )


def _request_action(
    agent: WorldAdapter,
    episode,
    observation: dict[str, Any],
    *,
    request_seq: int,
    allow_no_action: bool = False,
):
    episode_attrs = agent.s.node(episode)["attrs"]
    active_phase = episode_attrs.get("phase")
    agent.inner.set_attr(
        episode,
        "phase",
        "motor_perception_settlement",
    )
    _write_state(
        agent,
        episode,
        observation,
        state_seq=request_seq * 2 - 1,
    )
    agent.tick()
    agent.inner.set_attr(episode, "phase", active_phase)
    agent.inner.set_attr(episode, "request_seq", float(request_seq))
    if "regime_clock_seq" in agent.s.node(episode)["attrs"]:
        agent.inner.set_attr(
            episode,
            "regime_clock_seq",
            float(request_seq),
        )
    for regime in agent.inner.neighbours(
        episode,
        "has_humanoid_control_regime",
    ):
        agent.inner.set_attr(
            regime,
            "regime_clock_seq",
            float(request_seq),
        )
    agent.inner.set_attr(episode, "action_ready", 0.0)
    # Clear the previous ecology intervention request mechanically. The graph
    # must re-authorize caregiver support for this situated action.
    agent.inner.set_attr(
        episode, "caregiver_protective_support_requested", 0
    )
    agent.inner.set_attr(episode, "caregiver_support_scale", 0.0)
    agent.tick()
    # A later-installed developmental rule may publish a ready arbitrary-order
    # program after the ordinary motor trial openers have already passed in
    # this graph cycle.  Settle that graph authority once more before crossing
    # the mechanical boundary.  This is the same sensed request (not a world
    # prediction or simulator fork); it merely lets the existing exact-trial
    # machinery consume an output-potent program produced later in rule order.
    current_trials = [
        trial for trial in agent.inner.neighbours(
            episode, "has_humanoid_motor_trial"
        )
        if int(agent.s.node(trial)["attrs"].get("request_seq", -1))
        == request_seq
    ]
    current_ready_programs = [
        program for program in agent.inner.neighbours(
            episode, "has_ready_humanoid_motor_program"
        )
        if int(agent.s.node(program)["attrs"].get("request_seq", -1))
        == request_seq
    ]
    if current_ready_programs and not current_trials:
        agent.tick()
    attrs = _resume_graph_motor_synthesis(agent, episode)
    token = attrs.get("selected_token")
    if not isinstance(token, str) or attrs.get("action_ready") != 1.0:
        if allow_no_action:
            return None
        programs = []
        for program in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_program",
        ):
            program_attrs = agent.s.node(program)["attrs"]
            if int(program_attrs.get("request_seq", -1)) != request_seq:
                continue
            members = agent.inner.neighbours(
                program,
                "includes_humanoid_phase_action_model",
            )
            frontiers = [
                dict(agent.s.node(frontier)["attrs"])
                for frontier in agent.inner.neighbours(
                    program,
                    "has_humanoid_motor_program_frontier",
                )
            ]
            synthesis_debug = {}
            try:
                from scripts.gen_humanoid_adaptation_seed import (
                    Argmin,
                    Count,
                    P0,
                    V,
                    available_bundle_candidates,
                    bundle_synthesis_cost,
                )

                policy = _one_node(agent, "HumanoidPolicy")
                bindings = {
                    "episode": episode,
                    "plan": program,
                    "policy": policy,
                }
                available = available_bundle_candidates()
                best = Argmin(
                    available,
                    "candidate_option",
                    bundle_synthesis_cost(
                        "plan",
                        "candidate_option",
                    ),
                    V("plan"),
                )
                winner = agent.inner.evaluate(best, bindings)
                synthesis_debug = {
                    "available_count": agent.inner.evaluate(
                        Count(available),
                        bindings,
                    ),
                    "winner": (
                        dict(agent.s.node(winner)["attrs"])
                        if winner != program
                        else "plan-default"
                    ),
                    "current_cost": agent.inner.evaluate(
                        bundle_synthesis_cost("plan"),
                        bindings,
                    ),
                    "winner_cost": agent.inner.evaluate(
                        bundle_synthesis_cost("plan", best),
                        bindings,
                    ),
                }
            except Exception as exc:
                synthesis_debug = {"diagnostic_error": repr(exc)}
            programs.append({
                "status": program_attrs.get("status"),
                "member_count": program_attrs.get("member_count"),
                "allow_expansion": program_attrs.get("allow_expansion"),
                "tokens": [
                    agent.s.node(member)["attrs"].get("token")
                    for member in members
                ],
                "frontiers": frontiers,
                "synthesis": synthesis_debug,
            })
        selected_primary = []
        current_support_models = []
        for phase_model in agent.inner.neighbours(
            episode, "has_humanoid_phase_action_model"
        ):
            phase_attrs = dict(agent.s.node(phase_model)["attrs"])
            if phase_attrs.get("support_phase") == attrs.get(
                "current_support_phase"
            ):
                current_support_models.append({
                    key: phase_attrs.get(key)
                    for key in (
                        "token", "context_id", "initialized",
                        "experience_count", "motor_decision_value_epoch",
                    )
                })
            if phase_attrs.get("token") == attrs.get("selected_primary_token"):
                selected_primary.append({
                    "token": phase_attrs.get("token"),
                    "context_id": phase_attrs.get("context_id"),
                    "support_phase": phase_attrs.get("support_phase"),
                    "initialized": phase_attrs.get("initialized"),
                })
        wave_programs = []
        for field in agent.inner.neighbours(
            episode, "has_somatomotor_wave_field"
        ):
            for wave_program in agent.inner.neighbours(
                field, "has_somatomotor_wave_program"
            ):
                wave_programs.append(dict(
                    agent.s.node(wave_program)["attrs"]
                ))
        authority_programs = []
        for edge_type in (
            "has_active_humanoid_motor_program",
            "has_ready_humanoid_motor_program",
        ):
            for authority_program in agent.inner.neighbours(
                episode, edge_type
            ):
                authority_attrs = dict(
                    agent.s.node(authority_program)["attrs"]
                )
                authority_programs.append({
                    "edge_type": edge_type,
                    **{
                        key: authority_attrs.get(key)
                        for key in (
                            "status", "request_seq", "collapse_kind",
                            "decision_kind", "developmental_orientation_bundle",
                            "orientation_exploration_exhausted",
                        )
                    },
                })
        policy_rows = [
            {
                key: agent.s.node(policy)["attrs"].get(key)
                for key in (
                    "shared_motor_collapse_enabled",
                    "persistent_task_residual_authority",
                )
            }
            for policy in agent.inner.neighbours(
                agent.agent, "has_humanoid_policy"
            )
        ]
        raise RuntimeError(
            f"graph emitted no action for request {request_seq}: "
            f"phase={attrs.get('phase')!r}, "
            f"mode={attrs.get('mode')!r}, "
            f"recovery_mode={attrs.get('recovery_mode')!r}, "
            f"support_phase={attrs.get('current_support_phase')!r}, "
            f"developmental_goal={attrs.get('developmental_goal')!r}, "
            f"active_capability="
            f"{attrs.get('active_developmental_capability')!r}, "
            f"locomotion_drive_active="
            f"{attrs.get('locomotion_drive_active')!r}, "
            f"motor_primary_ready={attrs.get('motor_primary_ready')!r}, "
            f"recovery_primary_ready="
            f"{attrs.get('motor_recovery_primary_ready')!r}, "
            f"selected_primary_token={attrs.get('selected_primary_token')!r}, "
            f"selected_primary_context_id="
            f"{attrs.get('selected_primary_context_id')!r}, "
            f"selected_primary_models={selected_primary!r}, "
            f"current_support_model_count={len(current_support_models)!r}, "
            f"current_support_models={current_support_models[:4]!r}, "
            f"policy_rows={policy_rows!r}, "
            f"authority_programs={authority_programs!r}, "
            f"wave_programs={wave_programs!r}, "
            f"programs={programs!r}"
        )
    if int(attrs.get("motor_reference_request_seq", -1)) != request_seq:
        # The graph's fast action collapse may yield as soon as a motor choice
        # exists. Resume once so the independently graph-authored situated
        # reference is settled before the mechanical boundary can enact it.
        agent.tick()
        attrs = dict(agent.s.node(episode)["attrs"])
    if int(attrs.get("motor_reference_request_seq", -1)) != request_seq:
        raise RuntimeError(
            f"graph emitted no situated motor reference for request {request_seq}"
        )
    trial = _issued_trial(agent, episode, request_seq)
    # The issued trial is the graph's committed single motor outcome.  The
    # episode's reusable decision substrate may already be settling another
    # option while the independently authored situated reference catches up;
    # that mutable cache must not retroactively rewrite the committed trial.
    token = agent.s.node(trial)["attrs"].get("token")
    if not isinstance(token, str):
        raise RuntimeError(
            f"graph emitted an invalid committed trial for request {request_seq}"
        )
    trial_attrs = agent.s.node(trial)["attrs"]
    # The issued trial is the committed graph outcome. Settlement may already
    # mutate the episode's reusable selection cache for a future request, but
    # it cannot retroactively rewrite this action's secondary member or hold.
    secondary_token = trial_attrs.get("secondary_token")
    response_frames = trial_attrs.get("response_frames")
    if not isinstance(secondary_token, str):
        raise RuntimeError("graph emitted no secondary motor selection")
    if (
        isinstance(response_frames, bool)
        or not isinstance(response_frames, (int, float))
        or int(response_frames) != response_frames
        or response_frames < 1
    ):
        raise RuntimeError("graph emitted an invalid motor response horizon")
    attrs["selected_token"] = token
    attrs["selected_secondary_token"] = secondary_token
    attrs["selected_response_frames"] = response_frames
    attrs["selected_motor_tokens"] = _trial_motor_tokens(agent, trial)
    attrs["selected_motor_weights"] = {
        attrs.get("selected_token"): float(
            attrs.get("selected_motor_weight_a", 1.0)
        ),
        attrs.get("selected_secondary_token"): float(
            attrs.get("selected_motor_weight_b", 1.0)
        ),
    }
    if token not in attrs["selected_motor_tokens"]:
        raise RuntimeError("primary token is absent from graph motor program")
    return token, trial, attrs


def _close_action(
    agent: WorldAdapter,
    episode,
    trial,
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    request_seq: int,
    external_event_frames: int = 0,
) -> dict[str, Any]:
    trial_attrs = agent.s.node(trial)["attrs"]
    # Mechanical projection into the body-plan-independent compound-action
    # receipt contract. Some mature programs already carry an expected
    # directed advance; exploratory programs honestly begin at a zero prior.
    # The graph, not this boundary, learns whether coactivation adds value.
    if "predicted_task_progress" not in trial_attrs:
        agent.inner.set_attr(
            trial,
            "predicted_task_progress",
            float(trial_attrs.get("expected_directed_advance", 0.0)),
        )
        trial_attrs = agent.s.node(trial)["attrs"]
    expected_tokens = _trial_motor_tokens(agent, trial)
    pre_position = sensed_vector(before, "position")
    post_position = sensed_vector(after, "position")
    pre_angular = sensed_vector(before, "angular_velocity")
    post_angular = sensed_vector(after, "angular_velocity")
    pre_linear = sensed_vector(before, "linear_velocity")
    post_linear = sensed_vector(after, "linear_velocity")
    receipt_verified = (
        after["last_actuator_tokens"] == expected_tokens
        and after["step_index"] - before["step_index"]
        == trial_attrs.get("response_frames")
    )
    pre_joint_configuration = tuple(
        float(joint["position"])
        for joint in before.get("joints", ())
    )
    post_joint_configuration = tuple(
        float(joint["position"])
        for joint in after.get("joints", ())
    )
    motor_reference_positions = tuple(
        float(value)
        for value in after.get("motor_reference_positions", ())
    )
    motor_target_positions = tuple(
        float(value)
        for value in after.get("motor_target_positions", ())
    )
    motor_command_displacements = tuple(
        float(value)
        for value in after.get("motor_command_displacements", ())
    )
    body_scale = float(after.get("body_length_scale", 0.0))
    joint_count = len(post_joint_configuration)
    # Spatial acuity grows with the number of independently observable
    # relations, rather than using a fixed world-unit threshold.  Squaring the
    # body-derived joint count lets repeated small, supported displacements be
    # visible without teaching the graph a preferred stride length.
    developmental_resolution = max(1, joint_count * joint_count)
    displacement_x = float(post_position[0] - pre_position[0])
    displacement_y = float(post_position[1] - pre_position[1])
    translation = math.sqrt(
        displacement_x * displacement_x
        + displacement_y * displacement_y
    )
    def support_extent_squared(observation: dict[str, Any]) -> float:
        positions = tuple(
            tuple(float(value) for value in row["world_position"])
            for row in observation.get("whole_body_support_contacts", ())
        )
        return max(
            (
                sum((a - b) * (a - b) for a, b in zip(left, right))
                for index, left in enumerate(positions)
                for right in positions[index + 1:]
            ),
            default=0.0,
        )

    pre_support_links = tuple(sorted(
        int(row["link_index"])
        for row in before.get("whole_body_support_contacts", ())
    ))
    post_support_links = tuple(sorted(
        int(row["link_index"])
        for row in after.get("whole_body_support_contacts", ())
    ))
    if body_scale > 0.0:
        development_translation_units = round(
            translation * developmental_resolution / body_scale
        )
        development_elevation_units = round(
            float(post_position[2] - pre_position[2])
            * developmental_resolution
            / body_scale
        )
    else:
        development_translation_units = 0
        development_elevation_units = 0
    before_orientation = tuple(
        float(value) for value in before["base_orientation_xyzw"]
    )
    after_orientation = tuple(
        float(value) for value in after["base_orientation_xyzw"]
    )

    pre_gravity_axis = _gravity_relative_up_axis(
        before_orientation
    )
    post_gravity_axis = _gravity_relative_up_axis(
        after_orientation
    )
    development_pre_orientation_class = _gravity_relative_orientation_class(
        pre_gravity_axis
    )
    development_post_orientation_class = _gravity_relative_orientation_class(
        post_gravity_axis
    )
    pre_dominant_axis = abs(development_pre_orientation_class) - 1
    development_orientation_escape_units = round(
        (
            abs(pre_gravity_axis[pre_dominant_axis])
            - abs(post_gravity_axis[pre_dominant_axis])
        )
        * developmental_resolution
    )
    orientation_change = sum(
        abs(after_value - before_value)
        for before_value, after_value in zip(
            before_orientation,
            after_orientation,
        )
    )
    development_orientation_units = round(
        orientation_change * developmental_resolution
    )
    episode_attrs = agent.s.node(episode)["attrs"]
    development_directed_units = round(
        float(episode_attrs.get("heading_x", 0.0))
        * displacement_x
        * developmental_resolution
        / body_scale
    ) if body_scale > 0.0 else 0
    development_lateral_units = round(
        abs(displacement_y) * developmental_resolution / body_scale
    ) if body_scale > 0.0 else 0
    pre_motor_configuration_shape = tuple(
        int(value) for value in before.get("motor_configuration_shape", ())
    )
    post_motor_configuration_shape = tuple(
        int(value) for value in after.get("motor_configuration_shape", ())
    )

    def proprioceptive_region(shape: tuple[int, ...]) -> tuple[int, ...]:
        """Quantize a situated configuration basin without defining home."""
        return tuple((value > 0) - (value < 0) for value in shape)
    energetic_scale = (
        float(after.get("body_mass", 0.0))
        * float(after.get("gravity_acceleration", 0.0))
        * body_scale
    )
    development_energy_units = round(
        abs(float(after.get("supplied_energy_joules", 0.0)))
        * developmental_resolution
        / energetic_scale
    ) if energetic_scale > 0.0 else 0
    body_weight = (
        float(after.get("body_mass", 0.0))
        * float(after.get("gravity_acceleration", 0.0))
    )
    development_peak_load_units = round(
        abs(float(after.get("peak_contact_force_newtons", 0.0)))
        * developmental_resolution
        / body_weight
    ) if body_weight > 0.0 else 0
    pre_distal_support_code = sum(
        (index + 1)
        for index, row in enumerate(before["support_contact_forces"])
        if float(row["normal_force"]) > 0.0
    )
    post_distal_support_code = sum(
        (index + 1)
        for index, row in enumerate(after["support_contact_forces"])
        if float(row["normal_force"]) > 0.0
    )

    def sign(value: int) -> int:
        return 0 if value == 0 else (1 if value > 0 else -1)
    post_joint_velocity_energy = sum(
        float(joint["velocity"]) ** 2
        for joint in after.get("joints", ())
    )
    pre_joint_velocity_energy = sum(
        float(joint["velocity"]) ** 2
        for joint in before.get("joints", ())
    )
    one_tick_velocity = (
        float(after.get("gravity_acceleration", 0.0))
        * float(after.get("actuator_activation_seconds", 0.0))
    )
    development_quiet = int(
        post_joint_velocity_energy
        <= joint_count * one_tick_velocity * one_tick_velocity
    )
    development_context_signature = (
        ("configuration", *tuple(
            int(value)
            for value in after.get("motor_configuration_shape", ())
        )),
        ("support_count", len(post_support_links)),
        ("support_topology", *post_support_links),
        ("gravity_relative_orientation", development_post_orientation_class),
    )
    policy = _one_node(agent, "HumanoidPolicy")
    upright_height = (
        float(agent.s.node(policy)["attrs"].get(
            "minimum_upright_height_fraction", 0.0
        ))
        * float(agent.s.node(episode)["attrs"].get(
            "standing_reference_z", 0.0
        ))
    )
    reference_error_energy = sum(
        (reference - sensed) ** 2
        for reference, sensed in zip(
            motor_reference_positions,
            pre_joint_configuration,
        )
    )
    # A manifold shape is meaningful only relative to the future the action
    # was establishing.  Recovery, exploration, and directed locomotion can
    # produce the same contact geometry while pursuing different futures, so
    # retain the graph-authored action intent as the coarsest coordinate.
    development_action_intent = str(
        trial_attrs.get("decision_kind", "unspecified")
    )
    development_capability = str(
        episode_attrs.get("active_developmental_capability", "unspecified")
    )
    development_motor_program_key = json.dumps(
        expected_tokens, separators=(",", ":"), ensure_ascii=True
    )
    locomotor_phenotype_signature = (
        ("action_intent", development_action_intent),
        ("developmental_capability", development_capability),
        ("motor_program", development_motor_program_key),
        ("pre_distal_support_code", pre_distal_support_code),
        ("pre_whole_body_support_count", len(pre_support_links)),
        ("distal_support_code", post_distal_support_code),
        ("distal_support_transition", int(
            pre_distal_support_code != post_distal_support_code
        )),
        ("whole_body_support_count", len(post_support_links)),
        ("aerial", int(len(post_support_links) == 0)),
        ("pre_orientation_class", development_pre_orientation_class),
        ("post_orientation_class", development_post_orientation_class),
        ("vertical_impulse_sign", sign(
            development_elevation_units
        )),
        ("motion_nonamplifying", int(
            post_joint_velocity_energy <= pre_joint_velocity_energy
        )),
    )
    # Order-0 basin geometry excludes the two dynamic refinement dimensions.
    # Receipts retain the full signature below, so verification can accumulate
    # on the stable support shape without discarding impulse/amplification
    # residuals needed for later Pareto discrimination.
    # Order 0 preserves the projected state shape. Exact enacted program and
    # dynamic response remain on the leaf, available for local escalation only
    # when the parent's residual cannot be resolved at this coarser order.
    locomotor_phenotype_family_signature = (
        *locomotor_phenotype_signature[:2],
        *locomotor_phenotype_signature[5:11],
    )
    outcome_attrs = {
        **_pose(before, "pre"),
        **_pose(after, "post"),
        "pre_x": float(pre_position[0]),
        "post_x": float(post_position[0]),
        "pre_wx": float(pre_angular[0]),
        "pre_wy": float(pre_angular[1]),
        "post_wx": float(post_angular[0]),
        "post_wy": float(post_angular[1]),
        "pre_vx": float(pre_linear[0]),
        "pre_vy": float(pre_linear[1]),
        "post_vx": float(post_linear[0]),
        "post_vy": float(post_linear[1]),
        "pre_vz": float(pre_linear[2]),
        "post_vz": float(post_linear[2]),
        "pre_contact_count": float(before["sensed_contact_count"]),
        "contact_count": float(after["sensed_contact_count"]),
        "pre_contact_force_newtons": float(
            before.get("contact_force_newtons", 0.0)
        ),
        "contact_force_newtons": float(
            after.get("contact_force_newtons", 0.0)
        ),
        "pre_whole_body_support_count": float(len(
            before.get("whole_body_support_contacts", ())
        )),
        "post_whole_body_support_count": float(len(
            after.get("whole_body_support_contacts", ())
        )),
        "peak_contact_force_newtons": float(
            after.get("peak_contact_force_newtons", 0.0)
        ),
        "contact_normal_impulse_newton_seconds": float(
            after.get("contact_normal_impulse_newton_seconds", 0.0)
        ),
        "pre_angular_momentum_x": float(
            before.get("whole_body_angular_momentum", (0.0, 0.0, 0.0))[0]
        ),
        "pre_angular_momentum_y": float(
            before.get("whole_body_angular_momentum", (0.0, 0.0, 0.0))[1]
        ),
        "pre_angular_momentum_z": float(
            before.get("whole_body_angular_momentum", (0.0, 0.0, 0.0))[2]
        ),
        "post_angular_momentum_x": float(
            after.get("whole_body_angular_momentum", (0.0, 0.0, 0.0))[0]
        ),
        "post_angular_momentum_y": float(
            after.get("whole_body_angular_momentum", (0.0, 0.0, 0.0))[1]
        ),
        "post_angular_momentum_z": float(
            after.get("whole_body_angular_momentum", (0.0, 0.0, 0.0))[2]
        ),
        "input_energy_joules": float(after["supplied_energy_joules"]),
        "absorbed_energy_joules": float(after["absorbed_energy_joules"]),
        "recovered_energy_joules": 0.0,
        "peak_power_watts": float(after["peak_actuator_power_watts"]),
        "action_duration_seconds": float(
            after["sim_time"] - before["sim_time"]
        ),
        "world_step_index": float(after["step_index"]),
        "has_motor_epoch": 1.0,
        "motor_epoch": float(request_seq),
        "energetic_window_seq": float(
            agent.s.node(episode)["attrs"].get(
                "locomotor_prior_reset_seq",
                0.0,
            )
        ),
        "pre_support_0_force": float(
            before["support_contact_forces"][0]["normal_force"]
        ),
        "pre_support_1_force": float(
            before["support_contact_forces"][1]["normal_force"]
        ),
        "post_support_0_force": float(
            after["support_contact_forces"][0]["normal_force"]
        ),
        "post_support_1_force": float(
            after["support_contact_forces"][1]["normal_force"]
        ),
        "prediction_error_measured": 0.0,
        "context_specialized": 0.0,
        "response_horizon_tuned": 0.0,
        "compound_interval_tuned": 0.0,
        "receipt_verified": float(receipt_verified),
        # Closure is execution fidelity, not success and not safety. Graph
        # cognition separately decides retention and contextual release.
        "causal_receipt_closed": int(receipt_verified),
        "development_receipt_closed": int(receipt_verified),
        "development_experience_retained": 0,
        # A simulator or hardware boundary may report that the commanded
        # transition ended the current embodiment.  This remains a normal,
        # causally closed receipt; graph cognition decides whether to request
        # re-instantiation only after retaining it.
        "embodiment_destroyed": int(after.get("embodiment_destroyed", 0)),
        "embodiment_terminal_recorded": 0,
        "embodied_reset_requested": 0,
        "caregiver_protective_support_applied": int(after.get(
            "caregiver_protective_support_applied", 0
        )),
        "caregiver_protection_exafferent": int(after.get(
            "caregiver_protective_support_applied", 0
        )),
        "caregiver_protection_efference_copy_present": 0,
        "development_recoverability_units": int(after.get(
            "caregiver_protective_support_applied", 0
        )),
        "development_unbuffered_exposure_units": (
            1 - int(after.get("caregiver_protective_support_applied", 0))
        ),
        # Integer developmental evidence is mechanically quantized at the
        # simulator boundary.  Graph cognition never receives a float policy
        # constant for capability acquisition or transfer.
        "development_verified": int(receipt_verified),
        "development_receipt_seq": int(request_seq),
        "development_reversal": 0,
        "development_configuration_changed": int(
            pre_motor_configuration_shape != post_motor_configuration_shape
        ),
        "development_pre_configuration_region": proprioceptive_region(
            pre_motor_configuration_shape
        ),
        "development_post_configuration_region": proprioceptive_region(
            post_motor_configuration_shape
        ),
        "development_orientation_units": development_orientation_units,
        "development_orientation_escape_units": (
            development_orientation_escape_units
        ),
        "development_pre_gravity_axis_units": tuple(
            round(value * developmental_resolution)
            for value in pre_gravity_axis
        ),
        "development_post_gravity_axis_units": tuple(
            round(value * developmental_resolution)
            for value in post_gravity_axis
        ),
        # Scalar projections of the same integer vestibular transduction let
        # graph-native trajectory Rules compose arbitrary-order paths without
        # introducing tuple indexing or host-side planning.
        **{
            f"development_pre_gravity_axis_{axis}_units": round(
                pre_gravity_axis[index] * developmental_resolution
            )
            for index, axis in enumerate(("x", "y", "z"))
        },
        **{
            f"development_post_gravity_axis_{axis}_units": round(
                post_gravity_axis[index] * developmental_resolution
            )
            for index, axis in enumerate(("x", "y", "z"))
        },
        "development_pre_orientation_class": development_pre_orientation_class,
        "development_post_orientation_class": development_post_orientation_class,
        "development_quarter_turn_transition": int(
            abs(development_pre_orientation_class)
            != abs(development_post_orientation_class)
        ),
        "development_half_turn_transition": int(
            development_pre_orientation_class
            == -development_post_orientation_class
        ),
        "development_pre_support_count": len(pre_support_links),
        "development_post_support_count": len(post_support_links),
        "development_support_gain": (
            len(post_support_links) - len(pre_support_links)
        ),
        "development_support_extent_gain": int(
            support_extent_squared(after) > support_extent_squared(before)
        ),
        "development_support_topology_changed": int(
            pre_support_links != post_support_links
        ),
        "development_translation_units": development_translation_units,
        "development_directed_units": development_directed_units,
        "development_lateral_units": development_lateral_units,
        "development_elevation_units": development_elevation_units,
        "development_energy_units": development_energy_units,
        "development_peak_load_units": development_peak_load_units,
        "development_pre_distal_support_code": pre_distal_support_code,
        "development_post_distal_support_code": post_distal_support_code,
        "development_distal_support_transition": int(
            pre_distal_support_code != post_distal_support_code
        ),
        "development_upright": int(
            float(post_position[2]) > upright_height
        ),
        "development_quiet": development_quiet,
        "development_motion_nonamplifying": int(
            post_joint_velocity_energy <= pre_joint_velocity_energy
        ),
        "development_locomotor_cycle_evidence": int(
            development_translation_units > 0
            and pre_support_links != post_support_links
        ),
        "development_action_intent": development_action_intent,
        "developmental_capability": development_capability,
        "development_motor_program_key": development_motor_program_key,
        "development_primary_token": str(trial_attrs.get("token", "")),
        "development_secondary_token": str(
            trial_attrs.get("secondary_token", "")
        ),
        "development_locomotor_phenotype_signature": (
            locomotor_phenotype_signature
        ),
        "development_locomotor_phenotype_key": json.dumps(
            locomotor_phenotype_signature,
            separators=(",", ":"),
            ensure_ascii=True,
        ),
        "development_locomotor_phenotype_family_signature": (
            locomotor_phenotype_family_signature
        ),
        "development_locomotor_phenotype_family_key": json.dumps(
            locomotor_phenotype_family_signature,
            separators=(",", ":"),
            ensure_ascii=True,
        ),
        "development_locomotor_phenotype_novel": 0,
        "development_external_event": int(external_event_frames > 0),
        "development_context_signature": development_context_signature,
        "development_processed": 0,
        "external_event_frames": float(external_event_frames),
        "external_event_receipt_verified": float(
            external_event_frames > 0
            and after["last_actuator_tokens"] == expected_tokens
            and after["step_index"] - before["step_index"]
            == trial_attrs.get("response_frames") + external_event_frames
        ),
        "pre_joint_configuration": pre_joint_configuration,
        "post_joint_configuration": post_joint_configuration,
        "pre_motor_configuration_shape": pre_motor_configuration_shape,
        "post_motor_configuration_shape": post_motor_configuration_shape,
        "motor_reference_kind": after.get(
            "motor_reference_kind",
            "current_sensed_configuration",
        ),
        "motor_reference_positions": motor_reference_positions,
        "motor_target_positions": motor_target_positions,
        "motor_command_displacements": motor_command_displacements,
        "motor_command_displacement_energy": sum(
            displacement * displacement
            for displacement in motor_command_displacements
        ),
        "motor_reference_error_energy": reference_error_energy,
        "processed": 0.0,
        "task_progress": float(
            sensed_vector(after, "position")[0]
            - sensed_vector(before, "position")[0]
        ),
        **sensor_receipt_attrs(before, after),
    }
    outcome = agent.s.add_node("HumanoidTransition", outcome_attrs)
    _edge(agent, trial, "has_humanoid_transition", outcome)
    if receipt_verified:
        exercised_tokens = set(expected_tokens)
        for affordance in agent.s.nodes(
            "EmbodiedOpaqueActuatorAffordance"
        ):
            if agent.s.node(affordance)["attrs"].get(
                "opaque_token"
            ) in exercised_tokens:
                _edge(
                    agent,
                    outcome,
                    "exercises_opaque_embodied_actuator_affordance",
                    affordance,
                )
    development_contexts = agent.inner.neighbours(
        episode,
        "projects_embodied_development",
    )
    if development_contexts:
        if len(development_contexts) != 1:
            raise RuntimeError(
                "humanoid episode projects multiple developmental contexts"
            )
        _edge(
            agent,
            development_contexts[0],
            "has_embodied_development_receipt",
            outcome,
        )
        agent.inner.set_attr(
            development_contexts[0],
            "latest_development_receipt_seq",
            int(request_seq),
        )
    add_kinematic_receipt_points(
        agent,
        episode,
        trial,
        before,
        after,
        request_seq=request_seq,
        receipt_verified=receipt_verified,
        external_event_frames=external_event_frames,
    )
    _write_state(
        agent,
        episode,
        after,
        state_seq=request_seq * 2,
        state_is_receipt=True,
    )
    if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
        print(
            f"humanoid_close_phase request={request_seq} hard_tick_start",
            flush=True,
        )
    diagnostic_tick_budget = int(os.environ.get(
        "HUMANOID_RECEIPT_TICK_BUDGET", "100000"
    ))
    if "HUMANOID_RECEIPT_TICK_BUDGET" in os.environ:
        agent.s._inner.reset_rule_costs()
    receipt_tick_steps = agent.tick(max_steps=diagnostic_tick_budget)
    if (
        "HUMANOID_RECEIPT_TICK_BUDGET" in os.environ
        and receipt_tick_steps >= diagnostic_tick_budget
    ):
        hot_rules = sorted(
            agent.s._inner.rule_costs(),
            key=lambda row: row[1],
            reverse=True,
        )[:20]
        raise RuntimeError(
            "humanoid receipt hard tick reached diagnostic step budget: "
            f"request_seq={request_seq}, steps={receipt_tick_steps}, "
            f"hot_rules={hot_rules!r}"
        )
    if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
        print(
            f"humanoid_close_phase request={request_seq} hard_tick_done",
            flush=True,
        )
    if development_contexts:
        # A complete receipt is the scheduling boundary for the soft sheet.
        # This call supplies no condition, ranking, or action from Python: the
        # graph decides whether trajectory expansion/Pareto work exists, while
        # the next hard-real-time tick alone can release one motor outcome.
        if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
            print(
                f"humanoid_close_phase request={request_seq} soft_tick_start",
                flush=True,
            )
        agent.dual_process_tick()
        if os.environ.get("HUMANOID_ACTION_PROGRESS") == "1":
            print(
                f"humanoid_close_phase request={request_seq} soft_tick_done",
                flush=True,
            )
    closed_trial = dict(agent.s.node(trial)["attrs"])
    # Host-local observability for the exact enacted action. These keys are
    # returned to the runner only; they are never written into graph state or
    # consulted by a decision rule.
    closed_trial["_development_directed_units"] = int(
        outcome_attrs["development_directed_units"]
    )
    closed_trial["_development_translation_units"] = int(
        outcome_attrs["development_translation_units"]
    )
    closed_trial["_development_directed_consistency"] = int(
        outcome_attrs["development_directed_units"] > 0
    )
    return closed_trial


def _enact_graph_command(
    world: PyBulletHumanoidWorld,
    primary_token: str,
    decision: dict[str, Any],
) -> dict[str, Any]:
    """Mechanically enact the graph's bundle and integer hold horizon."""
    return world.step(
        tuple(decision["selected_motor_tokens"]),
        frames=int(decision["selected_response_frames"]),
        weights=decision.get("selected_motor_weights"),
        reference_positions=decision.get(
            "selected_motor_reference_positions"
        ),
        caregiver_protective_support=bool(
            int(decision.get("caregiver_protective_support_requested", 0))
        ),
        caregiver_support_scale=float(decision.get(
            "caregiver_support_scale", 0.0
        )),
    )


def _model_rows(agent: WorldAdapter, episode) -> list[dict[str, Any]]:
    return neighbour_rows(
        agent,
        episode,
        "has_humanoid_action_model",
        fields=(
                "token",
                "ordinal",
                "tonic_default",
                "experience_count",
                "mean_dzx",
                "mean_dzy",
                "mean_dwx",
                "mean_dwy",
                "mean_dvx",
                "mean_dvy",
                "mean_input_energy_joules",
                "support_loss_ema",
        ),
    )


def _configuration(protocol: dict[str, Any]) -> HumanoidBodyConfiguration:
    body = protocol["body"]
    return HumanoidBodyConfiguration(
        time_step=float(body["time_step_seconds"]),
        gravity_acceleration=float(body["gravity_acceleration"]),
        action_frames=int(body["action_frames"]),
        settling_frames=int(body["initial_settling_frames"]),
        joint_twitch_radians=float(body["joint_twitch_radians"]),
        maximum_joint_force=float(body["maximum_joint_force"]),
        position_gain=float(body["position_gain"]),
        velocity_gain=float(body["velocity_gain"]),
        initial_base_quarter_turns=tuple(
            int(value)
            for value in body.get("initial_base_quarter_turns", (0, 0, 0))
        ),
    )


def _run_arm(protocol: dict[str, Any], mode: str) -> dict[str, Any]:
    configuration = _configuration(protocol)
    calibration = protocol["calibration"]
    recovery = protocol["recovery"]
    perturbation = protocol["perturbation"]
    evaluation = protocol["evaluation"]
    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    policy = _one_node(agent, "HumanoidPolicy")
    agent.inner.set_attr(
        policy,
        "babble_samples",
        float(calibration["samples_per_non_tonic_actuator"]),
    )
    agent.inner.set_attr(
        policy,
        "minimum_upright_height_fraction",
        float(evaluation["minimum_upright_height_fraction"]),
    )
    agent.inner.set_attr(
        policy,
        "gravity_acceleration",
        configuration.gravity_acceleration,
    )

    with PyBulletHumanoidWorld(
        configuration,
        seed=int(protocol["seed"]),
    ) as world:
        observation = world.observe()
        agent.inner.set_attr(
            policy,
            "gait_surprise_confirmation_receipts",
            float(
                len(observation["base_linear_velocity"])
                * len(observation["support_contact_forces"])
            ),
        )
        standing_reference_z = float(observation["base_position"][2])
        episode = agent.s.add_node("HumanoidEpisode", {
            "mode": mode,
            "phase": "calibration",
            "action_ready": 0.0,
            "request_seq": 0.0,
            "decision_seq": 0.0,
            "decision_count": 0.0,
            "last_trial_request_seq": 0.0,
            "state_seq": 0.0,
            "measured_state_seq": -1.0,
            "standing_reference_z": standing_reference_z,
            "minimum_height_seen": standing_reference_z,
            "peak_tilt_seen": 0.0,
            "recovery_measurements_initialized": 0.0,
            "upright": 1.0,
            "aerial_active": 0.0,
            "body_mass": float(observation["body_mass"]),
            "gravity_acceleration": configuration.gravity_acceleration,
            "physics_time_step": configuration.time_step,
            "control_integration_frames": float(
                observation.get("control_integration_frames", 0.0)
            ),
            "response_horizon_initialized": 0.0,
            "nominal_response_frames": 0.0,
            "response_frames": 0.0,
            "motor_primary_ready": 0.0,
            "motor_recovery_primary_ready": 0.0,
            "compound_response_interval": 0.0,
            "last_compound_decision_count": 0.0,
            "motor_fixation_count": 0.0,
            "motor_configuration_transition_count": 0.0,
            "motor_efference_copy_count": 0.0,
            "motor_efference_confirmation_count": 0.0,
            "motor_reference_request_seq": 0.0,
            "selected_motor_reference_positions": (),
            "selected_motor_reference_shape": (),
            "selected_motor_reference_kind": "unbound",
            "motor_fixture_reset_seq": 0.0,
            "motor_fixture_reset_processed_seq": 0.0,
        })
        _edge(agent, agent.agent, "has_humanoid_episode", episode)
        options = world.actuator_options()
        for ordinal, option in enumerate(options):
            model = agent.s.add_node("HumanoidActionModel", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "tonic_default": float(option["tonic_default"]),
                "actuator_group": float(option["actuator_group"]),
                "experience_count": 0.0,
                "mean_dzx": 0.0,
                "mean_dzy": 0.0,
                "mean_dwx": 0.0,
                "mean_dwy": 0.0,
                "mean_dvx": 0.0,
                "mean_dvy": 0.0,
                "mean_input_energy_joules": 0.0,
                "support_loss_ema": 0.0,
                "support_deficit_ema": 0.0,
            })
            actuator = agent.s.add_node("OpaqueHumanoidActuator", {
                "token": option["token"],
                "ordinal": float(ordinal),
                "semantics": "unknown",
            })
            _edge(agent, episode, "has_humanoid_action_model", model)
            _edge(agent, model, "models_humanoid_actuator", actuator)

        probe_count = sum(
            float(option["tonic_default"]) < 0.5 for option in options
        )
        calibration_trace = []
        request_seq = 0
        for _ in range(
            probe_count
            * int(calibration["samples_per_non_tonic_actuator"])
        ):
            request_seq += 1
            before = observation
            token, trial, decision = _request_action(
                agent,
                episode,
                before,
                request_seq=request_seq,
            )
            after = _enact_graph_command(world, token, decision)
            trial_after = _close_action(
                agent,
                episode,
                trial,
                before,
                after,
                request_seq=request_seq,
            )
            if trial_after.get("status") != "learned":
                raise RuntimeError("graph did not learn humanoid motor receipt")
            calibration_trace.append({
                "request_seq": request_seq,
                "selected_token": token,
                "selected_secondary_token": decision[
                    "selected_secondary_token"
                ],
                "response_frames": decision["selected_response_frames"],
                "decision_kind": decision["decision_kind"],
                "position_after": list(after["base_position"]),
                "motor_fixation_count": agent.s.node(episode)["attrs"].get(
                    "motor_fixation_count",
                    0.0,
                ),
                "motor_efference_copy_count": agent.s.node(episode)["attrs"].get(
                    "motor_efference_copy_count",
                    0.0,
                ),
            })
            if calibration.get(
                "restore_stable_configuration_between_samples",
                False,
            ):
                # This is an experimental fixture supplied by the protocol,
                # not a controller target. The subsequent request mirrors the
                # newly sensed configuration into the graph as a local motor
                # fixation before it chooses another opaque limb probe.
                observation = world.reset()
            else:
                observation = world.hold_tonic(
                    int(protocol["body"]["calibration_recovery_frames"])
                )

        models = _model_rows(agent, episode)
        if not all(
            float(row["experience_count"]) >= 1.0
            for row in models
            if float(row["tonic_default"]) < 0.5
        ):
            raise RuntimeError("calibration left an opaque joint unlearned")

        pre_perturbation = observation
        agent.inner.set_attr(episode, "phase", "recovery")
        body_weight = (
            float(observation["body_mass"])
            * configuration.gravity_acceleration
        )
        resolved_force = [
            float(multiple) * body_weight
            for multiple in perturbation[
                "world_frame_force_body_weights"
            ]
        ]
        observation = world.apply_force_pulse(
            resolved_force,
            frames=int(perturbation["frames"]),
        )
        post_perturbation = observation
        recovery_trace = []
        minimum_height = float(observation["base_position"][2])
        peak_tilt = _body_axis_tilt(observation)
        tilt_integral = 0.0
        first_fall_action = None
        height_floor = (
            float(evaluation["minimum_upright_height_fraction"])
            * standing_reference_z
        )
        for action in range(int(recovery["actions"])):
            request_seq += 1
            before = observation
            token, trial, decision = _request_action(
                agent,
                episode,
                before,
                request_seq=request_seq,
            )
            after = _enact_graph_command(world, token, decision)
            trial_after = _close_action(
                agent,
                episode,
                trial,
                before,
                after,
                request_seq=request_seq,
            )
            tilt = _body_axis_tilt(after)
            height = float(after["base_position"][2])
            minimum_height = min(minimum_height, height)
            peak_tilt = max(peak_tilt, tilt)
            tilt_integral += (
                tilt
                * float(decision["selected_response_frames"])
                * configuration.time_step
            )
            if first_fall_action is None and height < height_floor:
                first_fall_action = action
            recovery_trace.append({
                "action": action,
                "selected_token": token,
                "selected_secondary_token": decision[
                    "selected_secondary_token"
                ],
                "response_frames": decision["selected_response_frames"],
                "decision_kind": decision["decision_kind"],
                "trial_status": trial_after["status"],
                "position_after": list(after["base_position"]),
                "orientation_after": list(
                    after["base_orientation_xyzw"]
                ),
                "angular_velocity_after": list(
                    after["base_angular_velocity"]
                ),
                "tilt_after": tilt,
            })
            observation = after

        _write_state(
            agent,
            episode,
            observation,
            state_seq=request_seq * 2 + 1,
        )
        agent.tick()
        final = dict(agent.s.node(episode)["attrs"])

    return {
        "mode": mode,
        "policy_owner": "rust_graph",
        "fresh_substrate": True,
        "actuator_count": len(options),
        "non_tonic_actuator_count": probe_count,
        "nominal_response_frames": final["nominal_response_frames"],
        "minimum_recovery_response_frames": min(
            row["response_frames"] for row in recovery_trace
        ),
        "maximum_recovery_response_frames": max(
            row["response_frames"] for row in recovery_trace
        ),
        "calibration_trace": calibration_trace,
        "models": models,
        "body_mass": float(observation["body_mass"]),
        "resolved_perturbation_force_newtons": resolved_force,
        "standing_reference_z": standing_reference_z,
        "pre_perturbation_state": {
            "position": list(pre_perturbation["base_position"]),
            "orientation": list(
                pre_perturbation["base_orientation_xyzw"]
            ),
        },
        "post_perturbation_state": {
            "position": list(post_perturbation["base_position"]),
            "orientation": list(
                post_perturbation["base_orientation_xyzw"]
            ),
            "angular_velocity": list(
                post_perturbation["base_angular_velocity"]
            ),
        },
        "minimum_height": minimum_height,
        "height_floor": height_floor,
        "peak_tilt": peak_tilt,
        "tilt_integral": tilt_integral,
        "first_fall_action": first_fall_action,
        "upright_at_end_graph_assessment": final["upright"],
        "minimum_height_graph_assessment": final["minimum_height_seen"],
        "peak_tilt_graph_assessment": final["peak_tilt_seen"],
        "final_position": list(observation["base_position"]),
        "final_tilt_graph_assessment": final["tilt_magnitude"],
        "recovery_action_diversity": len({
            row["selected_token"] for row in recovery_trace
        }),
        "motor_fixation_count": final.get("motor_fixation_count", 0.0),
        "motor_configuration_transition_count": final.get(
            "motor_configuration_transition_count",
            0.0,
        ),
        "motor_efference_copy_count": final.get(
            "motor_efference_copy_count",
            0.0,
        ),
        "motor_efference_confirmation_count": final.get(
            "motor_efference_confirmation_count",
            0.0,
        ),
        "recovery_trace": recovery_trace,
    }


def run_experiment(
    protocol_path: Path = DEFAULT_PROTOCOL,
) -> dict[str, Any]:
    protocol_path = protocol_path.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    modes = protocol["recovery"]["modes"]
    runs = {mode: _run_arm(protocol, mode) for mode in modes}
    adaptive = runs["adaptive_graph"]
    tonic = runs["tonic_posture_control"]
    pre_states_identical = (
        adaptive["calibration_trace"] == tonic["calibration_trace"]
        and adaptive["pre_perturbation_state"]
        == tonic["pre_perturbation_state"]
        and adaptive["post_perturbation_state"]
        == tonic["post_perturbation_state"]
    )
    return {
        "experiment": protocol["protocol"],
        "protocol_path": str(protocol_path.relative_to(ROOT)),
        "simulator": protocol["simulator"],
        "asset": HUMANOID_ASSET,
        "policy_owner": "rust_graph",
        "joint_count": adaptive["non_tonic_actuator_count"] // 2,
        "opaque_actuator_count": adaptive["actuator_count"],
        "pre_recovery_trajectories_identical": pre_states_identical,
        "perturbation": {
            **protocol["perturbation"],
            "resolved_world_frame_force_newtons": adaptive[
                "resolved_perturbation_force_newtons"
            ],
        },
        "adaptive": adaptive,
        "tonic_control": tonic,
        "paired_effect": {
            "minimum_height_advantage": (
                adaptive["minimum_height"] - tonic["minimum_height"]
            ),
            "tilt_integral_reduction": (
                tonic["tilt_integral"] - adaptive["tilt_integral"]
            ),
            "adaptive_survived": adaptive["first_fall_action"] is None,
            "tonic_control_fell": tonic["first_fall_action"] is not None,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--json-out", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)
    result = run_experiment(args.protocol)
    rendered = json.dumps(result, indent=2)
    if args.json_out is not None:
        args.json_out.write_text(rendered + "\n", encoding="utf-8")
    if not args.quiet:
        print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
