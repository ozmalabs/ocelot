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
        "humanoid_adaptation", "somatomotor_waves"
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
    assert "publish_verified_motor_transition_to_generic_trajectory" in text
    assert "mint_receipt_grounded_developmental_program_transition" in text
    from scripts.gen_humanoid_adaptation_seed import manifest as motor_manifest

    assert "release_selected_developmental_order_n_trajectory" in json.dumps(
        motor_manifest()
    )
    assert "reject_selected_trajectory_in_current_manifold_context" in text
    assert "archive_selected_trajectory_after_capability_mastery" in text
    assert "park_inactive_program_trajectory_off_hot_frontier" in text
    assert "restore_reactivated_program_trajectory_to_hot_frontier" in text
    assert "clear_selected_trajectory_without_current_state_source" in text
    assert "futuremanifoldprojection" in text
    assert "effort_supported" in text
    assert "effort_authorized" in text
    assert "open_goal_relative_inverse_kinematic_bootstrap" in text
    assert "knows_embodied_inverse_kinematics" in text
    assert "home" not in text


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


def test_generic_order_n_path_releases_only_its_next_compound_program():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_developmental_curriculum",))
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
    })
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 2,
        "trajectory_horizon": 2,
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
        })
        _edge(
            agent, program,
            "includes_humanoid_phase_action_model", phase_model,
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
    ) == [programs[1]]
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["action_ready"] == 1
    assert attrs["selected_token"] == "next"
    assert attrs["selected_collapse_kind"] == (
        "developmental_order_n_trajectory"
    )
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
