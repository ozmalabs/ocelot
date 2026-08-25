from __future__ import annotations

from dataclasses import replace
import importlib.util
import json
from pathlib import Path

import pytest

from scripts.gen_embodied_development_seed import CAPABILITIES


ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "seeds" / "humanoid_developmental_curriculum.json"
GENERAL_SEED = ROOT / "seeds" / "embodied_development.json"
PROTOCOL = ROOT / "protocols" / "humanoid_developmental_curriculum_v1.json"


def _contains_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def test_humanoid_seed_is_an_integer_output_null_bridge():
    from scripts.gen_humanoid_developmental_curriculum_seed import manifest

    generated = manifest()
    assert json.loads(SEED.read_text(encoding="utf-8")) == generated
    assert not _contains_float(generated)
    assert generated["nodes"] == []
    assert generated["depends_on"] == [
        "humanoid_adaptation",
        "somatomotor_waves",
        "hierarchical_effector_control",
    ]
    text = json.dumps(generated).lower()
    assert "has_active_embodied_developmental_capability" in text
    assert "developmental_goal" in text
    assert "learn_integer_developmental_action_affordance" in text
    assert "hold_best_orientation_program_open_until_boundary" in text
    assert "arbitrary_width_orientation_escape_bundle" in text
    assert "best_escape_command_per_effector_group" in text
    assert "request_generic_order_n_program_trajectory" in text
    assert "trajectory_minimum_selection_depth" in text
    assert "projects_future_manifold_in_episode" in text
    assert "uses_future_manifold_policy" in text
    assert "hdc_project_completed_development_to_deployment_goal" in text
    assert "publish_verified_motor_transition_to_generic_trajectory" in text
    assert "mint_receipt_grounded_developmental_program_transition" in text
    assert "bind_developmental_command_to_addressed_body_subsection" in text
    assert "credit_verified_receipt_to_each_unrolled_assignment" in text
    assert "open_verified_subsection_program_pair_experiments" in text
    assert "request_subsection_composition_pareto_escalation" in text
    assert "learn_subsection_composition_interaction_from_receipt" in text
    from scripts.gen_humanoid_adaptation_seed import manifest as motor_manifest

    assert "release_selected_developmental_order_n_trajectory" in json.dumps(
        motor_manifest()
    )
    assert "reject_selected_trajectory_in_current_manifold_context" in text
    assert "archive_selected_trajectory_after_capability_mastery" in text
    assert "park_inactive_program_trajectory_off_hot_frontier" in text
    assert "restore_reactivated_program_trajectory_to_hot_frontier" in text
    assert "clear_selected_trajectory_without_current_state_source" in text
    assert "hdc_replay_selected_order_n_program_path" in text
    assert "hdc_bind_retained_trajectory_to_deployment_receipt" in text
    assert "hdc_recruit_retained_trajectory_deployment_tasks" in text
    assert "hdc_refresh_retained_trajectory_after_deployment_receipt" in text
    assert "hdc_complete_retained_trajectory_replay_from_receipt" in text
    assert "hdc_refute_retained_trajectory_forecast_from_receipt" in text
    assert "hdc_open_post_curriculum_locomotion_rehearsal" in text
    assert "hdc_bind_first_post_curriculum_rehearsal_program" in text
    assert "hdc_record_post_curriculum_rehearsal_transition" in text
    assert "hdc_reify_post_curriculum_rehearsal_trial_program" in text
    assert "hdc_bind_post_curriculum_rehearsal_secondary_member" in text
    assert "hdc_replay_retained_order_n_program_path" in text
    assert "hdc_reject_retained_order_n_program_path" in text
    assert "hdc_audit_retained_order_n_program_path_manifold" in text
    assert "has_humanoid_library_motor_member" in text
    assert "has_issued_embodied_program_path" in text
    assert "has_issued_embodied_program_transition" in text
    assert "futuremanifoldprojection" in text
    assert "effort_supported" in text
    assert "effort_authorized" in text
    assert "open_goal_relative_inverse_kinematic_bootstrap" in text
    assert "knows_embodied_inverse_kinematics" in text
    assert "home" not in text


def test_completed_safe_curriculum_records_consecutive_rehearsal_receipts():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "phase": "locomotion",
        "request_seq": 7,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_learning_active": 1,
        "developmental_deployment_mode": 0,
    })
    plan = agent.s.add_node("SelfDirectedLearningPlan", {})
    step = agent.s.add_node("SelfDirectedLearningPlanStep", {
        "status": "completed",
    })
    first_model = agent.s.add_node("HumanoidActionModel", {
        "token": "first",
    })
    first_trial = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": 7,
        "response_frames": 2,
        "token": "first",
        "secondary_token": "first",
        "bundle_member_count": 1,
        "motor_task_context": "locomotion",
    })
    first_outcome = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(agent, development, "has_self_directed_learning_plan", plan)
    _edge(agent, plan, "has_learning_plan_step", step)
    _edge(agent, episode, "has_humanoid_action_model", first_model)
    _edge(agent, episode, "has_humanoid_motor_trial", first_trial)
    _edge(agent, first_trial, "uses_humanoid_action_model", first_model)
    _edge(agent, first_trial, "has_humanoid_transition", first_outcome)

    agent.tick()

    owners = agent.inner.neighbours(
        episode, "has_embodied_deployment_program_owner"
    )
    assert len(owners) == 1
    owner = owners[0]
    assert agent.s.node(owner)["attrs"]["output_authority"] == 0
    episode_attrs = agent.s.node(episode)["attrs"]
    assert episode_attrs["developmental_goal"] == "locomotion"
    assert episode_attrs["active_developmental_capability"] == "rehearsal"
    assert episode_attrs["locomotion_drive_active"] == 1
    assert agent.s.node(development)["attrs"][
        "developmental_deployment_mode"
    ] == 0
    first_programs = agent.inner.neighbours(
        first_trial, "enacts_humanoid_motor_program"
    )
    assert len(first_programs) == 1
    first = first_programs[0]
    assert agent.s.node(first)["attrs"]["receipt_reified"] == 1
    assert agent.inner.neighbours(
        owner, "has_current_embodied_program"
    ) == [first]
    assert not agent.inner.neighbours(
        owner, "has_embodied_program_transition"
    )

    second_model = agent.s.add_node("HumanoidActionModel", {
        "token": "second",
    })
    second_trial = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": 8,
        "response_frames": 3,
        "token": "second",
        "secondary_token": "second",
        "bundle_member_count": 1,
        "motor_task_context": "locomotion",
    })
    second_outcome = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
        "development_pre_orientation_class": 1,
        "development_post_orientation_class": 1,
        "development_pre_gravity_axis_x_units": 10,
        "development_post_gravity_axis_x_units": 12,
        "development_directed_units": 2,
        "development_energy_units": 4,
        "development_peak_load_units": 3,
    })
    agent.inner.set_attr(episode, "request_seq", 8)
    _edge(agent, episode, "has_humanoid_action_model", second_model)
    _edge(agent, episode, "has_humanoid_motor_trial", second_trial)
    _edge(agent, second_trial, "uses_humanoid_action_model", second_model)
    _edge(agent, second_trial, "has_humanoid_transition", second_outcome)

    agent.tick()

    transitions = agent.inner.neighbours(
        owner, "has_embodied_program_transition"
    )
    assert len(transitions) == 1
    second_programs = agent.inner.neighbours(
        second_trial, "enacts_humanoid_motor_program"
    )
    assert len(second_programs) == 1
    second = second_programs[0]
    transition = transitions[0]
    assert agent.inner.neighbours(
        transition, "starts_from_embodied_program"
    ) == [first]
    assert agent.inner.neighbours(
        transition, "continues_with_embodied_program"
    ) == [second]
    assert agent.inner.neighbours(
        owner, "has_current_embodied_program"
    ) == [second]
    attrs = agent.s.node(transition)["attrs"]
    assert attrs["task_progress_units"] == 2
    assert attrs["energy_units"] == 4
    assert attrs["output_authority"] == 0


def test_completed_deployment_plan_projects_normal_locomotion_goal():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_goal": "spontaneous_variation",
        "active_developmental_capability": "stale",
        "developmental_deployment_active": 0,
        "locomotion_drive_active": 0,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "developmental_deployment_mode": 1,
    })
    plan = agent.s.add_node("SelfDirectedLearningPlan", {
        "status": "completed",
    })
    stale = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability",
        {
            "name": "stale",
            "goal": "spontaneous_variation",
            "status": "mastered",
        },
    )
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(agent, development, "has_self_directed_learning_plan", plan)
    _edge(
        agent,
        development,
        "has_active_embodied_developmental_capability",
        stale,
    )

    steps = agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["developmental_goal"] == "locomotion"
    assert attrs["active_developmental_capability"] == "deployment"
    assert attrs["developmental_deployment_active"] == 1
    assert attrs["locomotion_drive_active"] == 1
    assert agent.inner.neighbours(
        development, "has_active_embodied_developmental_capability"
    ) == []
    assert steps < 100_000
    assert agent.tick() < 100


def test_deliberate_takeoff_owns_controller_over_generic_capability_hold():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "action_ready": 0,
        "self_takeoff_drive_active": 1,
        "active_support_count": 1,
        "sensorimotor_interrupt_required": 0,
        "upright": 1,
        "recovery_mode": 1,
        "recovery_entry_open": 1,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "name": "fixture_jump",
            "goal": "support_reducing_elevation",
            "developmental_ecology": "upright",
            "motor_task_context": "self_takeoff",
            "motor_task_target_scale": 1,
        },
    )
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent,
        development,
        "has_active_embodied_developmental_capability",
        capability,
    )
    # Let curriculum projection initialize, then reproduce the conflicting
    # situated controller state at an ordinary decision boundary.
    agent.tick()
    agent.inner.set_attr(episode, "self_takeoff_drive_active", 1)
    agent.inner.set_attr(episode, "upright", 1)
    agent.inner.set_attr(episode, "recovery_mode", 1)
    agent.inner.set_attr(episode, "recovery_entry_open", 1)

    steps = agent.tick()

    assert steps < 100_000
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["recovery_mode"] == 0
    assert attrs["recovery_entry_open"] == 0


def test_inverse_kinematic_query_inverts_learned_integer_forward_model():
    from scripts.gen_humanoid_developmental_curriculum_seed import (
        inverse_kinematic_rank,
    )
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {})
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 4,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "evidence_kind": "supported_translation",
            "success_count": 0,
            "desired_orientation_units": 0,
        },
    )
    goal = agent.s.add_node("Goal", {"progress_units": 0})
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    _edge(agent, goal, "grounds_learning_capability", capability)
    agent.tick()

    query = agent.inner.neighbours(
        development, "has_active_embodied_inverse_kinematic_query"
    )[0]
    query_attrs = agent.s.node(query)["attrs"]
    assert query_attrs["mode"] == "translation"
    assert query_attrs["target_directed_units"] == 4
    assert query_attrs["output_authority"] == 0
    assert agent.inner.neighbours(query, "pursues_goal") == [goal]

    costs = []
    phases = []
    for ordinal, directed_sum in enumerate((8, -8)):
        model = agent.s.add_node("HumanoidActionModel", {
            "development_receipt_count": 2,
            "development_directed_sum_units": directed_sum,
            "development_lateral_sum_units": 0,
            "development_elevation_sum_units": 0,
            "development_orientation_escape_sum_units": 0,
        })
        phase = agent.s.add_node("HumanoidPhaseActionModel", {
            "ordinal": ordinal,
        })
        _edge(agent, episode, "has_humanoid_phase_action_model", phase)
        _edge(agent, phase, "generalizes_humanoid_action_model", model)
        phases.append(phase)
        costs.append(agent.inner.evaluate(
            inverse_kinematic_rank("query", "candidate"),
            {"query": query, "candidate": phase, "capability": capability},
        ))
    assert costs == [0, 64]
    agent.tick()
    assert [
        agent.s.node(phase)["attrs"]["inverse_kinematic_cost_units"]
        for phase in phases
    ] == costs

    agent.inner.set_attr(capability, "success_count", 2)
    agent.tick()
    assert agent.s.node(query)["attrs"]["target_directed_units"] == 2
    assert [
        agent.s.node(phase)["attrs"]["inverse_kinematic_cost_units"]
        for phase in phases
    ] == [4, 36]


def test_orientation_inverse_uses_current_surface_and_explores_unseen_actions():
    from scripts.gen_humanoid_developmental_curriculum_seed import (
        developmental_evidence_rank,
        inverse_kinematic_rank,
    )
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "state_gravity_relative_orientation_class": -2,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "evidence_kind": "supported_half_turn",
        },
    )
    query = agent.s.add_node("EmbodiedInverseKinematicQuery", {
        "mode": "orientation",
        "target_orientation_units": 4,
    })
    model = agent.s.add_node("HumanoidActionModel", {
        "development_receipt_count": 10,
        "development_orientation_escape_units": 100,
        "development_orientation_return_units": 0,
    })
    phase = agent.s.add_node("HumanoidPhaseActionModel", {
        "inverse_kinematic_cost_units": 9,
    })
    evidence = agent.s.add_node(
        "HumanoidSituatedOrientationActionEvidence", {
            "orientation_class": -2,
            "receipt_count": 2,
            "escape_units": 2,
            "return_units": 0,
        },
    )
    _edge(agent, phase, "generalizes_humanoid_action_model", model)
    _edge(agent, model, "has_situated_orientation_action_evidence", evidence)

    bindings = {
        "episode": episode,
        "capability": capability,
        "query": query,
        "candidate": phase,
    }
    assert agent.inner.evaluate(
        inverse_kinematic_rank("query", "candidate"), bindings
    ) == 9
    assert agent.inner.evaluate(
        developmental_evidence_rank("candidate"), bindings
    ) == 9

    unseen_model = agent.s.add_node("HumanoidActionModel", {
        "development_receipt_count": 10,
    })
    unseen_phase = agent.s.add_node("HumanoidPhaseActionModel", {
        "inverse_kinematic_cost_units": 0,
    })
    _edge(
        agent, unseen_phase,
        "generalizes_humanoid_action_model", unseen_model,
    )
    bindings["candidate"] = unseen_phase
    assert agent.inner.evaluate(
        developmental_evidence_rank("candidate"), bindings
    ) == -1


def test_normal_receipts_teach_integer_task_space_forward_consequences():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {})
    trial = agent.s.add_node("HumanoidMotorTrial", {"request_seq": 1})
    model = agent.s.add_node("HumanoidActionModel", {})
    outcome = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
        "development_directed_units": 3,
        "development_lateral_units": 1,
        "development_elevation_units": 2,
        "development_orientation_escape_units": 4,
        "development_pre_orientation_class": -2,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "uses_humanoid_action_model", model)
    _edge(agent, trial, "has_humanoid_transition", outcome)
    agent.tick()

    attrs = agent.s.node(model)["attrs"]
    assert attrs["development_receipt_count"] == 1
    assert attrs["development_directed_sum_units"] == 3
    assert attrs["development_lateral_sum_units"] == 1
    assert attrs["development_elevation_sum_units"] == 2
    assert attrs["development_orientation_escape_sum_units"] == 4
    assert not any(isinstance(value, float) for value in attrs.values())
    situated = agent.inner.neighbours(
        model, "has_situated_orientation_action_evidence"
    )
    assert len(situated) == 1
    assert agent.s.node(situated[0])["attrs"] == {
        "orientation_class": -2,
        "receipt_count": 1,
        "escape_units": 4,
        "return_units": 0,
        "last_request_seq": 1,
        "integer_native": 1,
        "output_authority": 0,
    }


def test_latest_receipt_reanchors_trajectory_by_categorical_body_state():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {})
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "latest_development_receipt_seq": 5,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {}
    )
    transition = agent.s.add_node("EmbodiedProgramTransition", {
        "verified": 1,
        "pre_orientation_class": 2,
    })
    memory = agent.s.add_node("HumanoidMotorProgram", {})
    trial = agent.s.add_node("HumanoidMotorTrial", {"request_seq": 5})
    outcome = agent.s.add_node("HumanoidTransition", {
        "development_post_orientation_class": 2,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    _edge(
        agent, capability, "has_embodied_program_transition", transition
    )
    _edge(
        agent, transition, "continues_with_embodied_program", memory
    )
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "has_humanoid_transition", outcome)
    agent.tick()
    assert agent.inner.neighbours(
        capability, "has_current_embodied_program_transition_source"
    ) == [transition]


def test_order_n_release_projects_the_selected_path_not_only_its_next_program():
    from scripts.gen_humanoid_adaptation_seed import manifest

    rules = {rule["name"]: rule for rule in manifest()["rules"]}
    rule = rules["ha_release_selected_developmental_order_n_trajectory"]
    sources = []

    def visit(value):
        if isinstance(value, dict):
            if value.get("type") == "FutureManifoldProjection":
                sources.append(value["source"])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(rule)
    assert sources
    assert all(source == {"type": "Var", "name": "path"} for source in sources)
    encoded = json.dumps(rule)
    assert "selected_path_projection_request_seq" in encoded
    assert "selected_path_narrativium_retained_dvz" in encoded


@pytest.mark.parametrize(("terminal_dvx", "released"), (
    (-0.25, True),
    (0.5, False),
))
def test_generic_order_n_path_releases_only_its_next_compound_program(
    terminal_dvx,
    released,
):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    policy = agent.inner.neighbours(
        agent.agent, "has_humanoid_policy"
    )[0]
    for key, value in {
        "future_manifold_enabled": 1.0,
        "future_manifold_temporal_anchors_enabled": 1.0,
        "future_manifold_projection_budget": 16.0,
        "gravity_acceleration": 9.81,
    }.items():
        agent.inner.set_attr(policy, key, value)
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "developmental_goal": "orientation_change",
        "request_seq": 2,
        "decision_seq": 1,
        "decision_count": 0,
        "action_ready": 0,
        "selected_response_frames": 1,
        "response_frames": 1,
        "current_support_phase": 0,
        "manifold_bounds_ready": 1,
        "motor_task_context": "locomotion",
        **{f"manifold_bound_{key}": 0.5 for key in (
            "dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz",
        )},
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 4,
        "trajectory_horizon": 0,
        "latest_development_receipt_seq": 0,
    })
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "name": "fixture_orientation",
        "goal": "orientation_change",
        "desired_body_state_signature": (
            ("orientation_change", "quarter_turn"),
        ),
        "developmental_ecology": "floor",
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    programs = []
    for ordinal, token in enumerate(("origin", "next", "terminal")):
        program = agent.s.add_node("HumanoidMotorProgram", {
            "ordinal": ordinal,
            "status": "grounded",
            "memory_eligible": 1,
            "member_count": 2,
            "primary_token": token,
            "response_frames": 1,
            "request_seq": 0,
            "collapse_kind": "fixture",
            "open_residual_count": 1,
        })
        phase_model = agent.s.add_node("HumanoidPhaseActionModel", {
            "ordinal": ordinal,
            "token": token,
            "actuator_group": ordinal,
            "support_phase": 0,
            "context_id": 0,
            "initialized": 1,
            "mean_dvx": (
                0.25 if ordinal == 1 else terminal_dvx if ordinal == 2 else 0.0
            ),
            **{f"mean_{key}": 0.0 for key in (
                "dzx", "dzy", "dwx", "dwy", "dvy", "dvz",
            )},
            **{f"anchor_{key}": 0.0 for key in (
                "z_x", "z_y", "wx", "wy", "vx", "vy", "vz",
            )},
            "anchor_lateral_offset": 0.0,
        })
        _edge(
            agent, program,
            "includes_humanoid_phase_action_model", phase_model,
        )
        _edge(
            agent, episode,
            "has_humanoid_phase_action_model", phase_model,
        )
        programs.append(program)

    _edge(
        agent, episode,
        "last_verified_humanoid_motor_program", programs[0],
    )
    _edge(
        agent, capability,
        "has_current_embodied_program", programs[0],
    )
    agent.tick()
    assert agent.s.node(development)["attrs"]["trajectory_horizon"] == 4
    agent.dual_process_tick()
    trajectory = agent.inner.neighbours(
        capability, "has_embodied_program_trajectory"
    )[0]

    transitions = []
    for ordinal, (source, target, pre_x, post_x, boundary) in enumerate((
        (0, 1, 0, 60, 0),
        (1, 2, 60, 100, 1),
    )):
        transition = agent.s.add_node("HumanoidMotorTransition", {
            "ordinal": ordinal,
            "verified": 1,
            "pre_orientation_class": 1,
            "post_orientation_class": 2 if boundary else 1,
            "pre_state_axis_x_units": pre_x,
            "pre_state_axis_y_units": 0,
            "pre_state_axis_z_units": 0,
            "post_state_axis_x_units": post_x,
            "post_state_axis_y_units": 0,
            "post_state_axis_z_units": 0,
            "boundary_transition_count": boundary,
            "energy_units": 1,
            "peak_load_units": 1,
            "response_frames": 1,
        })
        transitions.append(transition)
        _edge(
            agent, capability,
            "has_embodied_program_transition", transition,
        )
        _edge(
            agent, transition,
            "starts_from_embodied_program", programs[source],
        )
        _edge(
            agent, transition,
            "continues_with_embodied_program", programs[target],
        )

    _edge(
        agent, capability,
        "has_current_embodied_program_transition_source", transitions[0],
    )

    task_set = agent.s.add_node("SystemTwoTaskSet", {
        "area": "embodied_program_trajectory", "enabled": 1,
    })
    pareto_task_set = agent.s.add_node("SystemTwoTaskSet", {
        "area": "cognitive_pareto", "enabled": 1,
    })
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "fixture_trajectory_update",
        "epoch": 2,
    })
    _edge(agent, escalation, "about_context", capability)
    _edge(agent, escalation, "recruits_task_set", task_set)
    _edge(agent, escalation, "recruits_task_set", pareto_task_set)
    agent.tick()
    agent.dual_process_tick()
    agent.tick()

    selected = agent.inner.neighbours(
        capability, "has_selected_embodied_program_path"
    )
    assert len(selected) == 1
    assert agent.s.node(selected[0])["attrs"]["depth"] == 2
    assert agent.inner.neighbours(
        episode, "has_ready_humanoid_motor_program"
    ) == ([programs[1]] if released else [])
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["action_ready"] == int(released)
    if released:
        assert attrs["selected_token"] == "next"
        assert attrs["selected_collapse_kind"] == (
            "developmental_order_n_trajectory"
        )
        memory_attrs = agent.s.node(programs[1])["attrs"]
        assert memory_attrs["selected_path_projection_request_seq"] == 2
        assert memory_attrs["selected_path_projection_depth"] == 2
        assert memory_attrs["selected_path_narrativium_retained_dvz"] == 1
    assert agent.s.node(capability)["attrs"].get(
        "trajectory_replay_count", 0
    ) == 0


def test_physics_question_synthesizes_unseen_arbitrary_width_compound_before_release():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "request_seq": 1,
        "decision_seq": 1,
        "decision_count": 0,
        "action_ready": 0,
        "response_frames": 1,
        "current_support_phase": 0,
        "sensorimotor_interrupt_required": 0,
        "reset_requested": 0,
        "structural_interrupt_required": 0,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 2,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "name": "fixture_unseen_roll",
            "goal": "deliberately_not_a_routing_label",
            "evidence_kind": "supported_half_turn",
            "developmental_ecology": "floor",
            "desired_body_state_signature": (
                ("support_topology_change", "required"),
                ("orientation_change", "half_turn"),
            ),
            "success_count": 0,
            "failure_count": 0,
        },
    )
    question = agent.s.add_node("EmbodiedPhysicsQuestion", {
        "status": "open",
        "desired_body_state_signature": (
            ("support_topology_change", "required"),
            ("orientation_change", "half_turn"),
        ),
        "proposal_count": 0,
        "selection_count": 0,
        "output_authority": 0,
        "integer_native": 1,
    })
    profile = agent.s.add_node("ParetoProfile", {
        "kind": "motor_learning_proposal",
        "dimension_count": 6,
        "scalarized": 0,
        "integer_native": 1,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    _edge(agent, question, "targets_learning_capability", capability)
    _edge(agent, question, "has_motor_learning_pareto_profile", profile)

    tokens = ("opaque_a", "opaque_b", "opaque_c")
    for ordinal, token in enumerate(tokens):
        learned = agent.s.add_node("HumanoidActionModel", {
            "development_receipt_count": 1,
            "development_orientation_escape_units": ordinal + 1,
            "development_orientation_return_units": 0,
            "development_latest_energy_units": 1,
            "development_latest_peak_load_units": 2,
            "development_latest_recoverability_units": 1,
        })
        candidate = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": token,
            "ordinal": ordinal,
            "actuator_group": ordinal,
            "support_phase": 0,
        })
        _edge(agent, episode, "has_humanoid_action_model", learned)
        _edge(agent, episode, "has_humanoid_phase_action_model", candidate)
        _edge(agent, candidate, "generalizes_humanoid_action_model", learned)
    physics_tasks = agent.s.add_node("SystemTwoTaskSet", {
        "area": "embodied_physics_proposal", "enabled": 1,
    })
    pareto_tasks = agent.s.add_node("SystemTwoTaskSet", {
        "area": "cognitive_pareto", "enabled": 1,
    })
    escalation = agent.s.add_node("SystemTwoEscalation", {
        "status": "requested", "reason": "fixture_physics_question",
    })
    _edge(agent, escalation, "recruits_task_set", physics_tasks)
    _edge(agent, escalation, "recruits_task_set", pareto_tasks)

    agent.tick()
    programs = agent.inner.neighbours(
        question, "has_counterfactual_motor_program"
    )
    assert len(programs) == 1
    program = programs[0]
    attrs = agent.s.node(program)["attrs"]
    assert attrs["status"] == "counterfactual_predicted"
    assert attrs["member_count"] == 3
    assert attrs["predicted_evidence_units"] == 6
    assert attrs["predicted_energy_units"] == 3
    assert attrs["predicted_peak_load_units"] == 6
    assert attrs["interaction_uncertainty_units"] == 3
    assert agent.s.node(episode)["attrs"]["action_ready"] == 0

    agent.dual_process_tick()
    agent.tick()
    selected = agent.inner.neighbours(
        question, "has_selected_motor_learning_proposal"
    )
    assert len(selected) == 1
    assert agent.s.node(selected[0])["attrs"]["physical_verified"] == 0
    assert agent.s.node(episode)["attrs"]["action_ready"] == 0

    agent.inner.set_attr(episode, "request_seq", 2)
    agent.tick()
    episode_attrs = agent.s.node(episode)["attrs"]
    assert episode_attrs["action_ready"] == 1
    assert episode_attrs["selected_collapse_kind"] == (
        "physics_counterfactual_compound"
    )
    members = agent.inner.neighbours(
        program, "includes_humanoid_phase_action_model"
    )
    assert {
        agent.s.node(member)["attrs"]["token"] for member in members
    } == set(tokens)


def test_established_manifold_requests_path_without_target_shape():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "manifold_bounds_ready": 1,
        "caregiver_protective_support_available": 1,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 4,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "name": "path_only_fixture",
            "developmental_ecology": "upright",
            "desired_body_state_signature": None,
        },
    )
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    policy = agent.inner.neighbours(agent.agent, "has_humanoid_policy")[0]
    agent.inner.set_attr(policy, "future_manifold_enabled", 1)
    agent.tick()

    assert agent.inner.neighbours(
        capability, "requests_embodied_program_trajectory"
    ) == [development]


def test_developmental_program_enacts_and_learns_through_body_hierarchy():
    from scripts.jabberwock_humanoid_adaptation import _trial_motor_tokens
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "request_seq": 7,
        "action_ready": 0,
        "phase": "fixture",
    })
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    plan = agent.s.add_node("HumanoidMotorProgram", {
        "status": "somatomotor_wave_building",
        "request_seq": 7,
        "member_count": 1,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "has_embodied_effector_topology", topology)
    _edge(agent, episode, "has_humanoid_motor_program", plan)

    effectors = []
    phase_models = []
    for ordinal, token in enumerate(("QUUX", "FOO", "BAR")):
        effector = agent.s.add_node("EmbodiedEffector", {
            "ordinal": ordinal,
            "channel_ordinal": ordinal,
            "mount_depth": ordinal + 1,
        })
        action_model = agent.s.add_node("HumanoidActionModel", {
            "token": token,
            "ordinal": ordinal,
        })
        phase_model = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": token,
            "ordinal": ordinal,
            "actuator_group": ordinal,
        })
        effectors.append(effector)
        phase_models.append(phase_model)
        _edge(agent, topology, "has_embodied_effector", effector)
        _edge(agent, action_model, "models_embodied_effector", effector)
        _edge(
            agent, phase_model,
            "generalizes_humanoid_action_model", action_model,
        )
    _edge(
        agent, plan,
        "includes_humanoid_phase_action_model", phase_models[0],
    )

    assert agent.tick() > 0
    hierarchies = agent.inner.neighbours(
        plan, "realizes_embodied_hierarchical_control_program"
    )
    assert len(hierarchies) == 1
    hierarchy = hierarchies[0]
    assert agent.s.node(hierarchy)["attrs"]["status"] == "collecting"
    assert not agent.inner.neighbours(
        hierarchy, "has_embodied_effector_program_assignment"
    )

    for phase_model in phase_models[1:]:
        _edge(
            agent, plan,
            "includes_humanoid_phase_action_model", phase_model,
        )
    agent.inner.set_attr(plan, "member_count", 3)
    agent.inner.set_attr(plan, "status", "ready")
    assert agent.tick() > 0
    hierarchy_attrs = agent.s.node(hierarchy)["attrs"]
    assert hierarchy_attrs["status"] == "ready"
    assert hierarchy_attrs["assignment_count"] == 3
    assert set(agent.inner.neighbours(
        hierarchy, "has_bound_embodied_child_motor_program"
    )) == set(phase_models)
    assert len(agent.inner.neighbours(
        hierarchy, "includes_embodied_program_binding"
    )) == 3
    assert agent.s.node(plan)["attrs"]["hierarchical_control_ready"] == 1

    aggregate = agent.inner.neighbours(
        hierarchy, "controls_embodied_control_subsection"
    )
    assert len(aggregate) == 1
    assert set(agent.inner.neighbours(
        aggregate[0], "addresses_embodied_effector"
    )) == set(effectors)

    trial = agent.s.add_node("HumanoidMotorTrial", {
        "status": "learned",
        "request_seq": 7,
    })
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "enacts_humanoid_motor_program", plan)
    assert agent.tick() > 0
    assert agent.inner.neighbours(
        trial, "enacts_embodied_hierarchical_control_program"
    ) == [hierarchy]
    assert _trial_motor_tokens(agent, trial) == ("QUUX", "FOO", "BAR")

    outcome = agent.s.add_node("HumanoidTransition", {
        "receipt_verified": 1,
    })
    _edge(agent, trial, "has_humanoid_transition", outcome)
    assert agent.tick() > 0
    assert agent.inner.neighbours(
        outcome, "verifies_embodied_hierarchical_control_program"
    ) == [hierarchy]
    assignments = agent.inner.neighbours(
        hierarchy, "has_embodied_effector_program_assignment"
    )
    assert set(agent.inner.neighbours(
        outcome, "verifies_embodied_effector_program_assignment"
    )) == set(assignments)
    assert all(
        agent.s.node(assignment)["attrs"]["experience_count"] == 1
        for assignment in assignments
    )


def _learned_subsection_program(
    agent, episode, ordinal, directed_units, effectors
):
    program = agent.s.add_node("HumanoidMotorProgram", {
        "status": "grounded",
        "request_seq": ordinal,
        "subsection_program_ordinal": ordinal,
        "subsection_shape_order": 1,
        "development_receipt_count": 1,
        "experience_retained": 1,
        "development_translation_evidence_units": directed_units,
        "development_directed_sum_units": directed_units,
        "development_lateral_sum_units": 0,
        "development_elevation_sum_units": 0,
        "development_energy_sum_units": 1,
        "development_peak_load_sum_units": 1,
        "development_recoverability_sum_units": 1,
        "response_frames": 1,
        "member_count": len(effectors),
        "primary_token": f"program_{ordinal}_0",
    })
    hierarchy = agent.s.add_node("EmbodiedHierarchicalControlProgram", {
        "status": "ready",
        "receipt_count": 1,
    })
    scope = agent.s.add_node("EmbodiedControlSubsection", {
        "scope_kind": "learned_program_subsection",
        "status": "ready",
        "member_count": len(effectors),
    })
    _edge(agent, episode, "has_humanoid_motor_program", program)
    _edge(
        agent, program,
        "realizes_embodied_hierarchical_control_program", hierarchy,
    )
    _edge(
        agent, hierarchy,
        "controls_embodied_control_subsection", scope,
    )
    for member_ordinal, effector in enumerate(effectors):
        phase_model = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": f"program_{ordinal}_{member_ordinal}",
            "ordinal": ordinal * 10 + member_ordinal,
            "actuator_group": agent.s.node(effector)["attrs"]["ordinal"],
        })
        action_model = agent.s.add_node("HumanoidActionModel", {
            "token": f"program_{ordinal}_{member_ordinal}",
            "ordinal": ordinal * 10 + member_ordinal,
        })
        assignment = agent.s.add_node("EmbodiedEffectorProgramAssignment", {
            "status": "experienced",
            "experience_count": 1,
            "composition_operator": "superpose",
        })
        _edge(
            agent, program,
            "includes_humanoid_phase_action_model", phase_model,
        )
        _edge(
            agent, phase_model,
            "generalizes_humanoid_action_model", action_model,
        )
        _edge(agent, action_model, "models_embodied_effector", effector)
        _edge(
            agent, hierarchy,
            "has_embodied_effector_program_assignment", assignment,
        )
        _edge(agent, assignment, "targets_embodied_effector", effector)
        _edge(
            agent, assignment,
            "invokes_embodied_child_motor_program", phase_model,
        )
        _edge(agent, scope, "addresses_embodied_effector", effector)
    return program


def test_verified_subsection_programs_enter_pareto_composition_and_learn_residual():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    policy = agent.inner.neighbours(agent.agent, "has_humanoid_policy")[0]
    agent.inner.set_attr(policy, "future_manifold_enabled", 0)
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "request_seq": 20,
        "decision_seq": 0,
        "decision_count": 0,
        "action_ready": 0,
        "structural_interrupt_required": 0,
        "sensorimotor_interrupt_required": 0,
        "reset_requested": 0,
        "locomotion_drive_active": 1,
        "current_support_phase": 0,
        "phase": "locomotion",
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 1,
    })
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "evidence_kind": "supported_translation",
        "goal": "locomotion",
    })
    query = agent.s.add_node("EmbodiedInverseKinematicQuery", {
        "status": "active",
        "mode": "translation",
        "target_directed_units": 5,
        "target_elevation_units": 0,
        "target_orientation_units": 0,
    })
    historical_question = agent.s.add_node("EmbodiedPhysicsQuestion", {
        "status": "resolved",
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(agent, episode, "has_embodied_effector_topology", topology)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    _edge(
        agent, development,
        "has_active_embodied_inverse_kinematic_query", query,
    )
    _edge(agent, query, "targets_learning_capability", capability)
    _edge(
        agent, historical_question,
        "targets_learning_capability", capability,
    )
    relation_aliases = [
        agent.s.add_node("MotorLearningProposal", {"status": "candidate"})
        for _ in range(19)
    ]
    for alias in relation_aliases:
        _edge(agent, alias, "targets_learning_capability", capability)

    effectors = [
        agent.s.add_node("EmbodiedEffector", {
            "ordinal": ordinal,
            "channel_ordinal": ordinal,
        })
        for ordinal in range(3)
    ]
    for effector in effectors:
        _edge(agent, topology, "has_embodied_effector", effector)
    best = _learned_subsection_program(
        agent, episode, 1, 5, [effectors[0]]
    )
    disjoint = _learned_subsection_program(
        agent, episode, 2, 2, [effectors[1]]
    )
    overlapping = _learned_subsection_program(
        agent, episode, 3, 1, [effectors[0], effectors[2]]
    )

    assert agent.tick() > 0
    active_questions = agent.inner.neighbours(
        query, "has_active_subsection_composition_question"
    )
    assert len(active_questions) == 1
    question = active_questions[0]
    assert agent.s.node(question)["attrs"]["kind"] == (
        "situated_subsection_composition"
    )
    proposals = [
        plan for plan in agent.inner.neighbours(
            question, "has_counterfactual_motor_program"
        )
        if agent.s.node(plan)["attrs"].get("subsection_composition") == 1
    ]
    # One task-space-optimal anchor paired with every other admissible
    # subsection program: linear, rather than all-pairs, proposal growth.
    assert len(proposals) == 2
    assert agent.inner.neighbours(
        historical_question, "has_counterfactual_motor_program"
    ) == []
    assert all(
        agent.inner.neighbours(alias, "has_counterfactual_motor_program") == []
        and agent.inner.neighbours(alias, "has_motor_learning_pareto_profile") == []
        for alias in relation_aliases
    )
    profiles = agent.inner.neighbours(
        question, "has_motor_learning_pareto_profile"
    )
    assert len(profiles) == 1
    assert len(agent.inner.neighbours(
        profiles[0], "has_pareto_dimension"
    )) == 6
    assert agent.inner.neighbours(
        question, "has_subsection_composition_anchor"
    ) == [best]
    assert all(
        best in agent.inner.neighbours(
            plan, "composes_developmental_subsection_program"
        )
        for plan in proposals
    )
    overlap_plan = next(
        plan for plan in proposals
        if overlapping in agent.inner.neighbours(
            plan, "composes_developmental_subsection_program"
        )
    )
    assert agent.s.node(overlap_plan)["attrs"]["subsection_overlap_count"] == 1
    assert agent.s.node(overlap_plan)["attrs"]["interaction_uncertainty_units"] == 2
    assert agent.s.node(overlap_plan)["attrs"][
        "subsection_composition_manifold_admissible"
    ] == 1

    escalations = [
        escalation for escalation in agent.s.nodes("SystemTwoEscalation")
        if agent.s.node(escalation)["attrs"].get("reason")
        == "subsection_composition_requires_pareto_collapse"
    ]
    escalation_contexts = [
        [
            agent.s.node(context)["attrs"].get("primary_token"),
            agent.s.node(context)["attrs"].get("status"),
            agent.s.node(context)["attrs"].get("request_seq"),
        ]
        for escalation in escalations
        for context in agent.inner.neighbours(escalation, "about_context")
    ]
    assert escalations, escalation_contexts
    assert any(
        agent.s.node(escalation)["attrs"]["status"] == "serviced"
        for escalation in escalations
    )
    learning_proposals = agent.inner.neighbours(
        question, "has_motor_learning_proposal"
    )
    assert len(learning_proposals) == len(proposals), [
        agent.s.node(proposal)["attrs"] for proposal in learning_proposals
    ]
    selected = agent.inner.neighbours(
        question, "has_selected_motor_learning_proposal"
    )
    assert len(selected) == 1
    selected_plan = agent.inner.neighbours(
        selected[0], "proposes_counterfactual_motor_program"
    )
    assert selected_plan == [overlap_plan]
    assert agent.s.node(overlap_plan)["attrs"]["status"] == "ready"
    assert agent.s.node(capability)["attrs"][
        "active_physical_experiment_lease_count"
    ] == 1
    assert agent.inner.neighbours(
        episode, "has_ready_humanoid_motor_program"
    ) == [overlap_plan]

    trial = agent.s.add_node("HumanoidMotorTrial", {
        "status": "learned",
        "request_seq": 20,
    })
    outcome = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
        "receipt_verified": 1,
        "development_translation_units": 2,
        "development_directed_units": 2,
    })
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "enacts_humanoid_motor_program", overlap_plan)
    _edge(agent, trial, "has_humanoid_transition", outcome)
    assert agent.tick() > 0

    assert agent.s.node(overlap_plan)["attrs"]["physical_verified"] == 1
    assert agent.s.node(capability)["attrs"][
        "active_physical_experiment_lease_count"
    ] == 0
    assert agent.s.node(overlap_plan)["attrs"]["interaction_residual_units"] == 4
    for component in (best, overlapping):
        attrs = agent.s.node(component)["attrs"]
        assert attrs["subsection_composition_receipt_count"] == 1
        assert attrs["subsection_interaction_residual_sum_units"] == 4

    # The failed additivity assumption changes the next situated anchor. The
    # individually weaker but composition-reliable program now has the lower
    # task residual after learned interaction error is included.
    assert agent.inner.neighbours(
        query, "has_active_subsection_composition_question"
    ) == []
    agent.inner.set_attr(episode, "request_seq", 21)
    assert agent.tick() > 0
    next_questions = agent.inner.neighbours(
        query, "has_active_subsection_composition_question"
    )
    assert len(next_questions) == 1
    next_question = next_questions[0]
    assert next_question != question
    assert agent.inner.neighbours(
        next_question, "has_subsection_composition_anchor"
    ) == [disjoint]


def test_unreceipted_assignment_cannot_become_subsection_component():
    from scripts.gen_humanoid_developmental_curriculum_seed import manifest

    rule = next(
        rule for rule in manifest()["rules"]
        if rule["name"] == "hdc_audit_situated_subsection_program_candidate"
    )
    text = json.dumps(rule)
    assert "unsupported_assignment" in text

    pair_rule = next(
        rule for rule in manifest()["rules"]
        if rule["name"]
        == "hdc_open_verified_subsection_program_pair_experiments"
    )
    pair_text = json.dumps(pair_rule)
    assert '"addition": {"type": "Var", "name": "second"}' in pair_text
    release_rule = next(
        rule for rule in manifest()["rules"]
        if rule["name"]
        == "hdc_release_selected_counterfactual_through_motor_collapse"
    )
    assert "subsection_composition_manifold_admissible" in json.dumps(
        release_rule
    )
    assert "experience_count" in text
    assert "FutureManifoldProjection" in text
    reassociated_learn = next(
        rule for rule in manifest()["rules"]
        if rule["name"]
        == "hdc_learn_reassociated_subsection_composition_from_receipt"
    )
    reassociated_rotate = next(
        rule for rule in manifest()["rules"]
        if rule["name"]
        == "hdc_rotate_reassociated_subsection_composition_question"
    )
    assert "synthesized_humanoid_motor_program" in json.dumps(
        reassociated_learn
    )
    assert "synthesized_humanoid_motor_program" in json.dumps(
        reassociated_rotate
    )
    cancellation = next(
        rule for rule in manifest()["rules"]
        if rule["name"]
        == "hdc_cancel_subsection_experiment_lease_outside_situated_manifold"
    )
    cancellation_text = json.dumps(cancellation)
    assert "enacts_humanoid_motor_program" in cancellation_text
    assert "synthesized_humanoid_motor_program" in cancellation_text
    assert "development_receipt_closed" in cancellation_text
    assert "physical_experiment_issued" in cancellation_text
    derivative_credit = next(
        rule for rule in manifest()["rules"]
        if rule["name"] == "hdc_credit_wide_takeoff_program_derivative"
    )
    derivative_credit_text = json.dumps(derivative_credit)
    assert "subsection_derivative_credit_complete" in derivative_credit_text
    assert "subsection_derivative_receipt_count" in derivative_credit_text
    assert "development_post_vertical_velocity_units" in derivative_credit_text
    assert "development_pre_vertical_velocity_units" in derivative_credit_text
    assert "whole_program_projection_authority" in derivative_credit_text
    assert "future_manifold_information_compression" in derivative_credit_text
    assert "interaction_uncertainty_units" in derivative_credit_text
    assert derivative_credit_text.count("partial_trajectory_evidence") >= 2
    assert "receipt_support_phase" in derivative_credit_text
    assert "receipt_orientation_class" in derivative_credit_text
    assert "receipt_response_frames" in derivative_credit_text
    assert derivative_credit_text.count('"key": "response_frames"') >= 2
    assert '"name": "trial"}, "key": "request_seq"' in derivative_credit_text
    assert '"name": "episode"}, "key": "request_seq"' in derivative_credit_text


def test_positive_takeoff_derivative_replays_exact_wide_program_without_pair_search():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    policy = agent.inner.neighbours(agent.agent, "has_humanoid_policy")[0]
    agent.inner.set_attr(policy, "future_manifold_enabled", 0)
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "request_seq": 2,
        "decision_seq": 1,
        "decision_count": 1,
        "action_ready": 0,
        "structural_interrupt_required": 0,
        "phase": "locomotion",
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 1,
    })
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "evidence_kind": "support_reducing_elevation",
        "failure_count": 1,
        "goal": "locomotion",
    })
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    effectors = [
        agent.s.add_node("EmbodiedEffector", {
            "ordinal": ordinal,
            "channel_ordinal": ordinal,
        })
        for ordinal in range(3)
    ]
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(agent, episode, "has_embodied_effector_topology", topology)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    for effector in effectors:
        _edge(agent, topology, "has_embodied_effector", effector)
    program = _learned_subsection_program(
        agent, episode, 1, 0, effectors,
    )
    agent.inner.set_attr(
        program, "development_latest_vertical_velocity_progress_units", 9,
    )
    agent.inner.set_attr(program, "subsection_derivative_receipt_count", 1)
    agent.inner.set_attr(program, "subsection_partial_replay_receipt_count", 0)

    assert agent.tick() > 0
    attrs = agent.s.node(episode)["attrs"]
    program_attrs = agent.s.node(program)["attrs"]
    assert attrs["selected_collapse_kind"] == "takeoff_derivative_recurrence"
    assert attrs["action_ready"] == 1
    assert attrs["partial_trajectory_warm_reuse_count"] == 0
    assert agent.inner.neighbours(
        episode, "has_ready_humanoid_motor_program"
    ) == [program]
    assert program_attrs["subsection_partial_replay_receipt_count"] == 1
    assert program_attrs["exclude_subsection_candidate"] == 1
    assert agent.inner.neighbours(
        episode, "has_active_subsection_composition_question"
    ) == []


def test_situated_warm_partial_takeoff_gets_one_local_verification_attempt():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    policy = agent.inner.neighbours(agent.agent, "has_humanoid_policy")[0]
    agent.inner.set_attr(policy, "future_manifold_enabled", 0)
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "request_seq": 2,
        "decision_seq": 1,
        "decision_count": 1,
        "action_ready": 0,
        "structural_interrupt_required": 0,
        "phase": "locomotion",
        "current_support_phase": 0,
        "state_gravity_relative_orientation_class": 3,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 1,
    })
    capability = agent.s.add_node("EmbodiedSituatedDevelopmentalCapability", {
        "evidence_kind": "support_reducing_elevation",
        "failure_count": 1,
    })
    topology = agent.s.add_node("EmbodiedEffectorTopology", {})
    effectors = [
        agent.s.add_node("EmbodiedEffector", {
            "ordinal": ordinal,
            "channel_ordinal": ordinal,
        })
        for ordinal in range(3)
    ]
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(agent, episode, "has_embodied_effector_topology", topology)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    for effector in effectors:
        _edge(agent, topology, "has_embodied_effector", effector)
    program = _learned_subsection_program(agent, episode, 1, 0, effectors)
    for key, value in {
        "partial_trajectory_evidence": 1,
        "development_vertical_velocity_progress_sum_units": 36,
        "development_latest_vertical_velocity_progress_units": 0,
        "warm_start_requires_verification": 1,
        "warm_start_verified": 0,
        "whole_program_projection_authority": 1,
        "receipt_support_phase": 0,
        "receipt_orientation_class": 3,
        "receipt_response_frames": 1,
        "response_frames": 1,
        "subsection_derivative_receipt_count": 5,
        "subsection_partial_replay_receipt_count": 4,
    }.items():
        agent.inner.set_attr(program, key, value)

    assert agent.tick() > 0
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["selected_collapse_kind"] == "situated_partial_warm_verification"
    assert attrs["action_ready"] == 1
    assert attrs["partial_trajectory_warm_reuse_count"] == 1
    assert agent.inner.neighbours(
        episode, "has_ready_humanoid_motor_program"
    ) == [program]


def test_learned_effort_excess_opens_body_discovered_orientation_bundle():
    """The classifier unlocks composition, but does not choose its members."""
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "request_seq": 1,
        "decision_seq": 0,
        "decision_count": 0,
        "action_ready": 0,
        "response_frames": 1,
        "current_support_phase": 0,
        "state_gravity_relative_orientation_class": -2,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "evidence_kind": "supported_quarter_turn",
            "desired_body_state_signature": None,
            "classifier_effort_excess": 1,
        },
    )
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    field = agent.s.add_node("SomatomotorWaveField", {})
    _edge(agent, episode, "has_somatomotor_wave_field", field)
    for _ in range(3):
        cell = agent.s.add_node("SomatomotorWaveCell", {})
        _edge(agent, field, "has_somatomotor_wave_cell", cell)
    for ordinal, token in enumerate(("opaque_a", "opaque_b", "opaque_c")):
        learned = agent.s.add_node("HumanoidActionModel", {
            "development_orientation_escape_units": ordinal + 1,
            "development_orientation_return_units": 0,
        })
        candidate = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": token,
            "ordinal": ordinal,
            "actuator_group": ordinal,
            "support_phase": 0,
        })
        _edge(agent, episode, "has_humanoid_action_model", learned)
        _edge(agent, episode, "has_humanoid_phase_action_model", candidate)
        _edge(agent, candidate, "generalizes_humanoid_action_model", learned)
        situated = agent.s.add_node(
            "HumanoidSituatedOrientationActionEvidence", {
                "orientation_class": -2,
                "escape_units": ordinal + 1 if ordinal < 2 else 0,
                "return_units": 0 if ordinal < 2 else 4,
            },
        )
        _edge(
            agent, learned,
            "has_situated_orientation_action_evidence", situated,
        )

    agent.tick()

    programs = [
        program for program in agent.inner.neighbours(
            episode, "has_humanoid_motor_program"
        )
        if agent.s.node(program)["attrs"].get(
            "developmental_orientation_bundle"
        ) == 1
    ]
    assert len(programs) == 1
    members = agent.inner.neighbours(
        programs[0], "includes_humanoid_phase_action_model"
    )
    assert len(members) == 2
    assert {
        agent.s.node(member)["attrs"]["actuator_group"]
        for member in members
    } == {0, 1}
    assert agent.s.node(programs[0])["attrs"][
        "developmental_orientation_origin_class"
    ] == -2
    assert agent.s.node(programs[0])["attrs"][
        "developmental_orientation_shape_order"
    ] == 2
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["action_ready"] == 1
    assert attrs["selected_collapse_kind"] == (
        "developmental_orientation_bundle"
    )

    # Issuance alone does not ground a practice program. Without an exact
    # receipt for request 1, the next request must not replay it as memory.
    agent.inner.set_attr(episode, "request_seq", 2)
    agent.inner.set_attr(episode, "action_ready", 0)
    agent.tick()
    replay_attrs = agent.s.node(episode)["attrs"]
    assert replay_attrs["action_ready"] == 0
    assert agent.s.node(programs[0])["attrs"].get(
        "developmental_replay_count", 0
    ) == 0

    # A bundle that uses its body-derived replay budget without retaining a
    # current orientation escape remains negative evidence, but must not own
    # this support phase forever. A fresh AbS bundle replaces it.
    agent.inner.set_attr(programs[0], "status", "grounded")
    agent.inner.set_attr(programs[0], "developmental_replay_count", 3)
    agent.inner.set_attr(
        programs[0], "development_latest_orientation_escape_units", 0
    )
    agent.inner.remove_edge(
        episode, "has_ready_humanoid_motor_program", programs[0]
    )
    agent.inner.set_attr(episode, "request_seq", 3)
    agent.inner.set_attr(episode, "action_ready", 0)
    agent.tick()

    old_attrs = agent.s.node(programs[0])["attrs"]
    assert old_attrs["orientation_exploration_exhausted"] == 1
    assert old_attrs["orientation_exhaustion_reason"] == (
        "replay_budget_closed_without_current_escape"
    )
    replacements = [
        candidate for candidate in agent.inner.neighbours(
            episode, "has_humanoid_motor_program"
        )
        if candidate != programs[0]
        and agent.s.node(candidate)["attrs"].get(
            "developmental_orientation_bundle"
        ) == 1
    ]
    assert len(replacements) == 1
    assert agent.s.node(replacements[0])["attrs"][
        "developmental_orientation_shape_order"
    ] == 3
    assert len(agent.inner.neighbours(
        replacements[0], "includes_humanoid_phase_action_model"
    )) == 3
    assert agent.s.node(episode)["attrs"]["selected_collapse_kind"] in (
        "developmental_orientation_bundle", "developmental_metaprogram"
    )


def test_elevation_shape_does_not_recruit_orientation_bundle():
    """A manifold signature is not by itself an orientation request."""
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "request_seq": 1,
        "decision_seq": 0,
        "decision_count": 0,
        "action_ready": 0,
        "response_frames": 1,
        "current_support_phase": 0,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "evidence_kind": "support_reducing_elevation",
            "desired_body_state_signature": (
                ("height_energy_relation", "increasing"),
                ("support_relation", "reduced"),
            ),
            "classifier_effort_excess": 1,
        },
    )
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    for ordinal in range(2):
        learned = agent.s.add_node("HumanoidActionModel", {
            "development_orientation_escape_units": ordinal + 1,
            "development_orientation_return_units": 0,
        })
        candidate = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": f"opaque_{ordinal}",
            "ordinal": ordinal,
            "actuator_group": ordinal,
            "support_phase": 0,
        })
        _edge(agent, episode, "has_humanoid_phase_action_model", candidate)
        _edge(agent, candidate, "generalizes_humanoid_action_model", learned)

    agent.tick()

    assert not any(
        agent.s.node(program)["attrs"].get(
            "developmental_orientation_bundle"
        ) == 1
        for program in agent.inner.neighbours(
            episode, "has_humanoid_motor_program"
        )
    )


def test_orientation_ready_authority_closes_when_evidence_manifold_ends():
    """Retain the learned bundle, but not obsolete actuator authority."""
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "request_seq": 12,
        "decision_seq": 11,
        "action_ready": 0,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "name": "next_capability",
            "goal": "locomotion",
            "evidence_kind": "supported_translation",
        },
    )
    orientation = agent.s.add_node("HumanoidMotorProgram", {
        "status": "ready",
        "request_seq": 8,
        "developmental_orientation_bundle": 1,
    })
    ordinary = agent.s.add_node("HumanoidMotorProgram", {
        "status": "ready",
        "request_seq": 9,
        "developmental_orientation_bundle": 0,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    _edge(agent, episode, "has_humanoid_motor_program", orientation)
    _edge(agent, episode, "has_humanoid_motor_program", ordinary)
    _edge(agent, episode, "has_ready_humanoid_motor_program", orientation)
    _edge(agent, episode, "has_ready_humanoid_motor_program", ordinary)

    agent.tick()

    assert agent.inner.neighbours(
        episode, "has_ready_humanoid_motor_program"
    ) == []
    assert agent.s.node(ordinary)["attrs"]["status"] == "superseded"
    attrs = agent.s.node(orientation)["attrs"]
    assert attrs["status"] == "manifold_authority_closed"
    assert attrs["orientation_authority_closed_at_request_seq"] == 12
    assert attrs["orientation_authority_close_reason"] == (
        "active_capability_not_orientation_evidence"
    )
    assert orientation in agent.inner.neighbours(
        episode, "has_humanoid_motor_program"
    )


def test_verified_developmental_receipt_mints_body_neutral_program_edge():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "request_seq": 2,
        "decision_seq": 2,
        "action_ready": 0,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "latest_development_receipt_seq": 2,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability",
        {"goal": "orientation_change"},
    )
    previous = agent.s.add_node("HumanoidMotorProgram", {})
    memory = agent.s.add_node("HumanoidMotorProgram", {})
    trial = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": 2,
        "response_frames": 3,
    })
    outcome = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
        "development_pre_orientation_class": 1,
        "development_post_orientation_class": 2,
        "development_pre_gravity_axis_x_units": 0,
        "development_pre_gravity_axis_y_units": 0,
        "development_pre_gravity_axis_z_units": 100,
        "development_post_gravity_axis_x_units": 100,
        "development_post_gravity_axis_y_units": 0,
        "development_post_gravity_axis_z_units": 0,
        "development_quarter_turn_transition": 1,
        "development_half_turn_transition": 0,
        "development_energy_units": 7,
        "development_peak_load_units": 4,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    _edge(agent, capability, "has_current_embodied_program", previous)
    _edge(
        agent, episode,
        "last_verified_humanoid_motor_program", previous,
    )
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "enacts_humanoid_motor_program", memory)
    _edge(agent, trial, "has_humanoid_transition", outcome)

    steps = agent.tick(max_steps=2_000)

    assert steps < 2_000
    assert agent.inner.neighbours(
        capability, "has_current_embodied_program"
    ) == [memory]

    transitions = agent.inner.neighbours(
        capability, "has_embodied_program_transition"
    )
    assert len(transitions) == 1
    transition = transitions[0]
    assert agent.inner.neighbours(
        transition, "starts_from_embodied_program"
    ) == [previous]
    assert agent.inner.neighbours(
        transition, "continues_with_embodied_program"
    ) == [memory]
    attrs = agent.s.node(transition)["attrs"]
    assert attrs["boundary_transition_count"] == 1
    assert attrs["energy_units"] == 7
    assert attrs["peak_load_units"] == 4
    assert attrs["experience_retained"] == 1
    assert attrs["contextual_release_eligible"] == 0
    assert not any(isinstance(value, float) for value in attrs.values())


def test_latest_trial_preserves_all_current_equivalent_programs():
    """Multiple enacted aliases cannot clear and rebind each other forever."""
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {})
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "latest_development_receipt_seq": 5,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {}
    )
    current_a = agent.s.add_node("HumanoidMotorProgram", {})
    current_b = agent.s.add_node("HumanoidMotorProgram", {})
    stale = agent.s.add_node("HumanoidMotorProgram", {})
    trial = agent.s.add_node("HumanoidMotorTrial", {"request_seq": 5})
    outcome = agent.s.add_node("HumanoidTransition", {
        "development_receipt_closed": 1,
    })
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent, development,
        "has_active_embodied_developmental_capability", capability,
    )
    for program in (current_a, current_b, stale):
        _edge(agent, capability, "has_current_embodied_program", program)
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "enacts_humanoid_motor_program", current_a)
    _edge(agent, trial, "enacts_humanoid_motor_program", current_b)
    _edge(agent, trial, "has_humanoid_transition", outcome)

    steps = agent.tick(max_steps=2_000)

    assert steps < 2_000
    assert set(agent.inner.neighbours(
        capability, "has_current_embodied_program"
    )) == {current_a, current_b}


def test_caregiver_is_contextual_protection_not_developmental_permission():
    from scripts.gen_humanoid_developmental_curriculum_seed import manifest

    generated = manifest()
    rules = {row["name"]: row for row in generated["rules"]}
    cold = json.dumps(rules[
        "hdc_open_self_authored_attempt_without_caregiver_permission"
    ])
    protection_rule = rules[
        "hdc_request_caregiver_protection_for_under_evidenced_attempt"
    ]
    protection = json.dumps(protection_rule)
    assert "caregiver_scaffold_handoff_ready" in cold
    assert "unscaffolded_self_attempt" in cold
    assert "caregiver_protective_support_available" in protection
    assert "development_evidence_window" in protection
    assert "success_count" in protection
    assert "attempt_count" not in protection
    protection_condition = json.dumps(protection_rule["where"])
    protection_effects = json.dumps(protection_rule["effects"])
    assert "caregiver_support_scale" in protection_effects
    effect_keys = [effect[2] for effect in protection_rule["effects"][:2]]
    assert effect_keys == [
        "caregiver_support_scale",
        "caregiver_protective_support_requested",
    ]
    assert "milestone" not in protection_condition
    assert "developmental_stage_ordinal" not in protection_condition
    reference = json.dumps(rules[
        "hdc_bind_current_sensed_reference_without_privileged_fixation"
    ]["where"])
    assert "caregiver" not in reference
    assert "has_current_humanoid_motor_fixation" in reference


def _edge(agent, source, edge_type, target):
    try:
        agent.inner.add_edge_unchecked(source, edge_type, target, {})
    except TypeError:
        agent.inner.add_edge_unchecked(source, edge_type, target)


def test_detached_embodiment_freezes_its_locomotor_pareto_profile():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("embodied_development",))
    episode = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    connection = agent.s.add_node(
        "EmbodiedSimulatorConnection", {"current_attachment": 0}
    )
    profile = agent.s.add_node("ParetoProfile", {
        "context": "situated_locomotor_repertoire",
        "integer_native": 1,
    })
    _edge(agent, episode, "grounded_in_embodied_simulator_connection", connection)
    _edge(agent, episode, "has_embodied_locomotor_pareto_profile", profile)

    agent.tick(max_steps=100)

    assert agent.s.node(profile)["attrs"]["pareto_suspended"] == 1


def _stale_recovery_fixture(
    *,
    capability_name="locomotor_phenotype_discovery",
    sensorimotor_interrupt_required=0,
    reset_requested=0,
    developmental_goal="locomotion",
    recovery_mode=1,
    active_developmental_capability=None,
    capability_goal="locomotion",
    developmental_ecology="upright",
):
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "developmental_goal": developmental_goal,
        "active_developmental_capability": (
            capability_name
            if active_developmental_capability is None
            else active_developmental_capability
        ),
        "locomotion_drive_active": 1,
        "recovery_mode": recovery_mode,
        "sensorimotor_interrupt_required": sensorimotor_interrupt_required,
        "reset_requested": reset_requested,
        "selected_motor_weight_a": 4,
        "selected_motor_weight_b": 3,
        "decision_kind": "get_up_program",
        "action_ready": 1,
        "motor_recovery_primary_ready": 1,
        "recovery_entry_open": 1,
        "developmental_recovery_program_release_count": 0,
        "developmental_recovery_basin_release_count": 0,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    capability = agent.s.add_node("EmbodiedDevelopmentalCapability", {
        "name": capability_name,
        "goal": capability_goal,
        "developmental_ecology": developmental_ecology,
    })
    program = agent.s.add_node("HumanoidRecoveryProgram", {
        "status": "active",
    })
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent,
        development,
        "has_active_embodied_developmental_capability",
        capability,
    )
    _edge(
        agent,
        episode,
        "has_active_humanoid_recovery_program",
        program,
    )
    _edge(
        agent,
        episode,
        "has_current_humanoid_recovery_basin",
        basin,
    )
    _edge(agent, episode, "has_humanoid_recovery_basin", basin)
    _edge(agent, basin, "has_humanoid_recovery_program", program)
    return agent, episode, program, basin


@pytest.mark.parametrize(
    "capability_name",
    (
        "cyclic_support_translation",
        "cyclic_reduced_support_translation",
        "locomotor_phenotype_discovery",
        "locomotor_pareto_repertoire",
    ),
)
def test_intentional_locomotion_releases_only_transient_postural_authority(
    capability_name,
):
    agent, episode, program, basin = _stale_recovery_fixture(
        capability_name=capability_name,
    )

    agent.tick()

    assert not agent.inner.neighbours(
        episode, "has_active_humanoid_recovery_program"
    )
    assert not agent.inner.neighbours(
        episode, "has_current_humanoid_recovery_basin"
    )
    # Learned recovery structure remains available for a future real reflex.
    assert agent.inner.neighbours(
        episode, "has_humanoid_recovery_basin"
    ) == [basin]
    assert agent.inner.neighbours(
        basin, "has_humanoid_recovery_program"
    ) == [program]
    assert agent.s.node(program)["attrs"]["status"] == "retained"
    assert agent.s.node(basin)["attrs"]["status"] == "retained"
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["developmental_recovery_program_release_count"] == 1
    assert attrs["developmental_recovery_basin_release_count"] == 1
    assert attrs["selected_motor_weight_a"] == 1
    assert attrs["selected_motor_weight_b"] == 1
    assert attrs["recovery_mode"] == 0
    assert (
        attrs["action_ready"] == 0
        or attrs["decision_kind"] not in {
            "get_up_exploit",
            "get_up_program",
            "get_up_reanchor",
        }
    )


@pytest.mark.parametrize(
    ("capability_name", "interrupt", "reset_requested"),
    (
        ("locomotor_phenotype_discovery", 1, 0),
        ("locomotor_pareto_repertoire", 0, 1),
    ),
)
def test_material_reflex_keeps_recovery_authority(
    capability_name, interrupt, reset_requested
):
    agent, episode, program, basin = _stale_recovery_fixture(
        capability_name=capability_name,
        sensorimotor_interrupt_required=interrupt,
        reset_requested=reset_requested,
    )

    agent.tick()

    assert agent.inner.neighbours(
        episode, "has_active_humanoid_recovery_program"
    ) == [program]
    assert agent.inner.neighbours(
        episode, "has_current_humanoid_recovery_basin"
    ) == [basin]
    assert agent.s.node(program)["attrs"]["status"] == "active"
    assert agent.s.node(basin)["attrs"]["status"] == "situated"
    assert agent.s.node(episode)["attrs"]["action_ready"] == 1


def test_floor_development_releases_get_up_without_muting_real_interrupts():
    agent, episode, program, basin = _stale_recovery_fixture(
        capability_name="side_lying_transition",
        capability_goal="orientation_change",
        developmental_ecology="floor",
        developmental_goal="bounded_equilibrium",
        recovery_mode=1,
    )

    agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["developmental_goal"] == "orientation_change"
    assert attrs["recovery_mode"] == 0
    assert not agent.inner.neighbours(
        episode, "has_active_humanoid_recovery_program"
    )
    assert not agent.inner.neighbours(
        episode, "has_current_humanoid_recovery_basin"
    )
    assert agent.s.node(program)["attrs"]["status"] == "retained"
    assert agent.s.node(basin)["attrs"]["status"] == "retained"


def test_new_repertoire_goal_does_not_suppress_live_material_interrupt():
    agent, episode, program, basin = _stale_recovery_fixture(
        sensorimotor_interrupt_required=1,
        developmental_goal="bounded_equilibrium",
        recovery_mode=1,
        active_developmental_capability="dynamic_equilibrium",
    )

    agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["developmental_goal"] == "locomotion"
    assert attrs["recovery_mode"] == 1
    assert agent.inner.neighbours(
        episode, "has_active_humanoid_recovery_program"
    ) == [program]
    assert agent.inner.neighbours(
        episode, "has_current_humanoid_recovery_basin"
    ) == [basin]


def test_same_goal_capability_transition_refreshes_development_context():
    agent, episode, _, _ = _stale_recovery_fixture(
        capability_name="locomotor_pareto_repertoire",
        developmental_goal="locomotion",
        active_developmental_capability="locomotor_phenotype_discovery",
    )

    agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["developmental_goal"] == "locomotion"
    assert attrs["active_developmental_capability"] == (
        "locomotor_pareto_repertoire"
    )
    assert attrs["motor_primary_ready"] == 0
    assert attrs["motor_recovery_primary_ready"] == 0


def test_general_development_is_a_capability_dag_not_an_age_clock():
    seed = json.loads(GENERAL_SEED.read_text(encoding="utf-8"))
    templates = [node for node in seed["nodes"] if node["type"] ==
                 "EmbodiedDevelopmentalCapabilityTemplate"]
    prerequisites = [edge for edge in seed["edges"] if edge["type"] ==
                     "requires_embodied_developmental_capability_template"]
    assert len(templates) == len(CAPABILITIES)
    assert len(prerequisites) > len(templates) - 1
    assert not _contains_float(seed)
    assert all(node["attrs"]["output_authority"] == 0 for node in templates)
    by_name = {node["attrs"]["name"]: node["attrs"] for node in templates}
    assert by_name["spontaneous_general_movement"]["developmental_ecology"] == "floor"
    assert by_name["independent_sitting"]["clinical_milestone"] == 1
    assert by_name["hands_knees_crawling"]["optional_route"] == 1
    assert by_name["independent_walking"]["human_analogue"] == "walking_alone"
    assert by_name["two_foot_jump"]["motor_task_context"] == "self_takeoff"
    assert by_name["two_foot_jump"]["motor_task_target_scale"] == 1


def test_developmental_task_context_opens_takeoff_only_inside_supported_manifold():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "developmental_curriculum_active": 1,
        "phase": "locomotion",
        "upright": 1,
        "recovery_mode": 0,
        "active_support_count": 2,
        "self_takeoff_drive_active": 0,
        "self_takeoff_target_velocity_scale": 0,
        "self_takeoff_compression_scale": 0,
        "motor_primary_ready": 1,
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {})
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "name": "fixture_elevation",
            "goal": "support_reducing_elevation",
            "motor_task_context": "self_takeoff",
            "motor_task_target_scale": 1,
        },
    )
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent,
        development,
        "has_active_embodied_developmental_capability",
        capability,
    )

    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["self_takeoff_drive_active"] == 1
    assert attrs["self_takeoff_target_velocity_scale"] == 1

    agent.inner.set_attr(episode, "active_support_count", 0)
    agent.tick()
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["self_takeoff_drive_active"] == 0
    assert attrs["self_takeoff_target_velocity_scale"] == 0


def test_cross_body_transfer_is_structural_output_null_and_reverified():
    seed = json.loads(GENERAL_SEED.read_text(encoding="utf-8"))
    rules = {row["name"]: row for row in seed["rules"]}
    warm = json.dumps(
        rules["ed_warm_start_capability_from_similar_body_shape"]
    )
    assert rules["ed_warm_start_capability_from_similar_body_shape"][
        "latency_class"
    ] == "hard_realtime"
    assert "ShapeDecode" in warm
    assert "covered_count" in warm and "residual" in warm
    assert "body_capability_signature" in warm
    assert "warm_start_requires_verification" in warm
    store = json.dumps(
        rules["ed_store_mastered_capability_by_structural_body_shape"]
    )
    assert '"output_authority": 0' in store


def test_protocol_declares_supine_fixture_and_graph_owned_curriculum():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["body"]["initial_base_quarter_turns"] == [1, 0, 0]
    assert protocol["curriculum"]["developmental"] is True
    assert protocol["curriculum"]["authority"] == "current_stage_goal_only"
    assert protocol["curriculum"]["initial_fixture"] == (
        "supported_supine_floor_exploration"
    )


def test_supine_fixture_exposes_name_free_body_capability_signature():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("install requirements-robot.txt")
    from scripts.jabberwock_humanoid_walk import _configuration
    from domains.pybullet_humanoid_world import PyBulletHumanoidWorld

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    with PyBulletHumanoidWorld(
        _configuration(protocol), seed=protocol["seed"]
    ) as world:
        observation = world.reset()

    assert observation["whole_body_support_contacts"]
    signature = observation["body_capability_signature"]
    assert signature and all(isinstance(row, tuple) for row in signature)
    encoded = json.dumps(signature).lower()
    for anatomical_name in ("arm", "leg", "foot", "hand", "torso", "hip"):
        assert anatomical_name not in encoded


@pytest.mark.parametrize(
    "quarter_turns", ((1.0, 0, 0), (True, 0, 0), (1, 0), "1,0,0")
)
def test_initial_fixture_requires_three_integer_quarter_turns(quarter_turns):
    from scripts.jabberwock_humanoid_walk import _configuration

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    with pytest.raises(ValueError, match="initial_base_quarter_turns"):
        replace(
            _configuration(protocol),
            initial_base_quarter_turns=quarter_turns,
        )
