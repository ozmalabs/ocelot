from __future__ import annotations

import inspect
from itertools import combinations

import pytest

from scripts.jabberwock_humanoid_adaptation import (
    _edge,
    _one_node,
    _resume_graph_motor_synthesis,
)
from substrate.world_adapter import WorldAdapter


def _inverse_control_fixture() -> tuple[WorldAdapter, object]:
    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    policy = _one_node(agent, "HumanoidPolicy")
    for key, value in {
        "gravity_acceleration": 1.0,
        "target_froude_speed": 1.0,
        "minimum_upright_height_fraction": 0.5,
        "support_phase_prior_strength": 1.0,
        "gait_surprise_confirmation_receipts": 2.0,
        "maximum_lateral_drift_metres": 1.0,
    }.items():
        agent.inner.set_attr(policy, key, value)

    episode = agent.s.add_node("HumanoidEpisode", {
        "phase": "locomotion",
        "mode": "directed_walk",
        "recovery_mode": 0.0,
        "action_ready": 0.0,
        "motor_primary_ready": 1.0,
        "selected_primary_token": "motor_a",
        "current_support_phase": 0.0,
        "evaluation_active": 1.0,
        "decision_count": 10.0,
        "last_compound_decision_count": 0.0,
        "compound_response_interval": 1.0,
        "tilt_magnitude": 0.0,
        "upright": 1.0,
        "learned_gait_mean_tilt": 1.0,
        "learned_gait_tilt_envelope": 1.0,
        "learned_gait_prediction_error_envelope": 1.0,
        "response_frames": 10.0,
        "request_seq": 1.0,
        "last_trial_request_seq": 0.0,
        "standing_reference_z": 1.0,
        "heading_x": 1.0,
        "state_z": 1.0,
        "state_qx": 0.0,
        "state_qy": 0.0,
        "state_qz": 0.0,
        "state_qw": 1.0,
        "state_wx": 0.0,
        "state_wy": 0.0,
        "state_vx": 0.0,
        "state_vy": 0.0,
        "online_phase_learning": 0.0,
        "support_sensor_count": 2.0,
        "active_support_count": 2.0,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)

    phase_models = []
    for ordinal, token in enumerate(("motor_a", "motor_b", "motor_c")):
        model = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": token,
            "ordinal": float(ordinal),
            "actuator_group": float(ordinal),
            "support_phase": 0.0,
            "initialized": 1.0,
            "experience_count": 1.0,
            "mean_dzx": 0.0,
            "mean_dzy": 0.0,
            "mean_dwx": 0.0,
            "mean_dwy": 0.0,
            "mean_dvx": 0.4,
            "mean_dvy": 0.0,
            "last_update_request_seq": 0.0,
        })
        _edge(
            agent,
            episode,
            "has_humanoid_phase_action_model",
            model,
        )
        phase_models.append(model)
        for inactive_phase in (1.0, 2.0):
            decoy = agent.s.add_node("HumanoidPhaseActionModel", {
                **agent.s.node(model)["attrs"],
                "support_phase": inactive_phase,
            })
            _edge(
                agent,
                episode,
                "has_humanoid_phase_action_model",
                decoy,
            )

    for phase_model in phase_models:
        phase_attrs = agent.s.node(phase_model)["attrs"]
        base = agent.s.add_node("HumanoidActionModel", {
            "token": phase_attrs["token"],
            "ordinal": phase_attrs["ordinal"],
            "actuator_group": phase_attrs["actuator_group"],
            "tonic_default": 0.0,
            "experience_count": 1.0,
        })
        _edge(agent, episode, "has_humanoid_action_model", base)
        _edge(
            agent,
            phase_model,
            "generalizes_humanoid_action_model",
            base,
        )

    for ordinal, (left, right) in enumerate(combinations(phase_models, 2)):
        left_attrs = agent.s.node(left)["attrs"]
        right_attrs = agent.s.node(right)["attrs"]
        synergy = agent.s.add_node("HumanoidSynergyModel", {
            "ordinal": float(ordinal),
            "token_a": left_attrs["token"],
            "token_b": right_attrs["token"],
            "initialized": 1.0,
            "probed": 1.0,
            "approved": 1.0,
            "rejected": 0.0,
            "residual_dzx": 0.0,
            "residual_dzy": 0.0,
            "residual_dwx": 0.0,
            "residual_dwy": 0.0,
            "residual_dvx": 0.1,
            "residual_dvy": 0.0,
        })
        _edge(agent, episode, "has_humanoid_synergy_model", synergy)

    return agent, episode


def test_competing_decision_retires_unfinished_program_before_next_request():
    agent, episode = _inverse_control_fixture()
    program = agent.s.add_node("HumanoidMotorProgram", {
        "status": "building",
        "request_seq": 1.0,
        "member_count": 2.0,
        "synthesis_yield_required": 1.0,
    })
    _edge(agent, episode, "has_humanoid_motor_program", program)
    _edge(agent, episode, "has_active_humanoid_motor_program", program)
    _edge(agent, episode, "resumes_humanoid_motor_program", program)

    # Another synthesis channel supplied request 1.  On request 2 this losing
    # plan must not be resumed against a different sensed state.
    agent.inner.set_attr(episode, "request_seq", 2.0)
    agent.inner.set_attr(episode, "action_ready", 1.0)
    agent.tick()

    attrs = agent.s.node(program)["attrs"]
    assert attrs["status"] == "superseded"
    assert attrs["supersession_reason"] == (
        "competing_program_committed_for_request"
    )
    assert attrs["superseded_at_request_seq"] == 2.0
    assert program not in agent.inner.neighbours(
        episode, "has_active_humanoid_motor_program"
    )
    assert program not in agent.inner.neighbours(
        episode, "resumes_humanoid_motor_program"
    )


def test_humanoid_future_manifold_gate_rejects_unsafe_candidate_but_off_is_legacy():
    """Whole-body fallback is multi-frame only when explicitly enabled."""
    agent, episode = _inverse_control_fixture()
    policy = _one_node(agent, "HumanoidPolicy")
    candidate = next(
        model
        for model in agent.inner.neighbours(
            episode, "has_humanoid_phase_action_model"
        )
        if agent.s.node(model)["attrs"]["token"] == "motor_a"
        and agent.s.node(model)["attrs"]["support_phase"] == 0.0
    )

    # The legacy composer accepts the selected support-local primitive.
    term = {
        "type": "MotorCompose",
        "episode": {"type": "Var", "name": "ep"},
        "policy": {"type": "Var", "name": "po"},
        "candidate": {"type": "Var", "name": "candidate"},
    }
    bindings = {"ep": episode, "po": policy, "candidate": candidate}
    assert agent.inner.evaluate(term, bindings)

    # Supply complete learned anchors/bounds, then make the selected primitive
    # leave the manifold before the final foveated frame.  The opt-in path
    # must reject it rather than silently falling back to the legacy choice.
    for key in (
        "manifold_bound_dzx", "manifold_bound_dzy", "manifold_bound_dwx",
        "manifold_bound_dwy", "manifold_bound_dvx", "manifold_bound_dvy",
        "manifold_bound_dvz",
    ):
        agent.inner.set_attr(episode, key, 1.0)
    agent.inner.set_attr(episode, "manifold_bounds_ready", 1.0)
    for key in (
        "anchor_z_x", "anchor_z_y", "anchor_wx", "anchor_wy",
        "anchor_vx", "anchor_vy", "anchor_vz", "anchor_lateral_offset",
    ):
        agent.inner.set_attr(candidate, key, 0.0)
    # It stays inside the bound at the sparse intermediate frame 8/10 and
    # escapes only at the final frame, so a one-frame check would accept it.
    agent.inner.set_attr(candidate, "mean_dzx", 1.1)
    agent.inner.set_attr(policy, "future_manifold_enabled", 1.0)
    agent.inner.set_attr(policy, "future_manifold_temporal_anchors_enabled", 1.0)
    assert not agent.inner.evaluate(term, bindings)


def _enable_recovery_measurements(agent, episode) -> None:
    for key, value in {
        "response_horizon_initialized": 1.0,
        "body_mass": 1.0,
        "gravity_acceleration": 1.0,
        "physics_time_step": 0.1,
        "state_vz": 0.0,
        "state_joint_count": 3.0,
        "state_joint_velocity_energy": 0.0,
        "state_contact_count_raw": 2.0,
    }.items():
        agent.inner.set_attr(episode, key, value)


def _verified_outcome(
    agent,
    trial,
    *,
    post_vx: float = 0.8,
    post_x: float = 0.1,
    post_z: float = 1.0,
    pre_support_force: float = 0.0,
    post_support_force: float = 0.0,
    pre_contact_count: float = 0.0,
    post_contact_count: float = 0.0,
    pre_configuration_shape=None,
    post_configuration_shape=None,
    recovery_basin_considered: float = 0.0,
    peak_power_watts: float = 0.0,
):
    outcome = agent.s.add_node("HumanoidTransition", {
        "receipt_verified": 1.0,
        "processed": 0.0,
        "prediction_error_measured": 0.0,
        "pre_z": 1.0,
        "post_z": post_z,
        "pre_qx": 0.0,
        "pre_qy": 0.0,
        "pre_qz": 0.0,
        "pre_qw": 1.0,
        "post_qx": 0.0,
        "post_qy": 0.0,
        "post_qz": 0.0,
        "post_qw": 1.0,
        "pre_wx": 0.0,
        "pre_wy": 0.0,
        "pre_x": 0.0,
        "post_x": post_x,
        "post_wx": 0.0,
        "post_wy": 0.0,
        "pre_vx": 0.0,
        "pre_vy": 0.0,
        "post_vx": post_vx,
        "post_vy": 0.0,
        "pre_vz": 0.0,
        "post_vz": 0.1,
        "pre_support_0_force": pre_support_force,
        "pre_support_1_force": pre_support_force,
        "post_support_0_force": post_support_force,
        "post_support_1_force": post_support_force,
        "pre_contact_count": pre_contact_count,
        "contact_count": post_contact_count,
        "pre_motor_configuration_shape": pre_configuration_shape,
        "post_motor_configuration_shape": post_configuration_shape,
        "input_energy_joules": 1.0,
        "peak_contact_force_newtons": 1.0,
        "peak_power_watts": peak_power_watts,
        "recovery_basin_considered": recovery_basin_considered,
    })
    _edge(agent, trial, "has_humanoid_transition", outcome)
    agent.tick()
    return outcome


def _ground_singleton_program(agent, episode):
    agent.inner.set_attr(episode, "compound_response_interval", 100.0)
    agent.inner.set_attr(episode, "last_compound_decision_count", 10.0)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    assert agent.s.node(program)["attrs"]["member_count"] == 1.0
    trial = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )[0]
    _verified_outcome(agent, trial)
    assert agent.s.node(program)["attrs"]["memory_eligible"] == 1.0
    return program


def test_raw_fallen_state_recruits_recovery_without_phase_receipt():
    agent, episode = _inverse_control_fixture()
    agent.inner.set_attr(episode, "state_seq", 1.0)
    agent.inner.set_attr(episode, "measured_state_seq", 0.0)
    agent.inner.set_attr(episode, "state_z", 0.1)
    agent.inner.set_attr(episode, "recovery_mode", 0.0)

    agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["upright"] == 0.0
    assert attrs["recovery_mode"] == 1.0


def test_analysis_by_synthesis_authors_arbitrary_three_motor_program():
    agent, episode = _inverse_control_fixture()

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)

    programs = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )
    assert len(programs) == 1
    program = programs[0]
    attrs = agent.s.node(program)["attrs"]
    members = agent.inner.neighbours(
        program,
        "includes_humanoid_phase_action_model",
    )
    tokens = {
        agent.s.node(member)["attrs"]["token"]
        for member in members
    }

    assert attrs["status"] == "ready"
    assert attrs["member_count"] == 3.0
    assert tokens == {"motor_a", "motor_b", "motor_c"}
    assert {
        agent.s.node(member)["attrs"]["support_phase"]
        for member in members
    } == {0.0}
    assert attrs["response_frames"] == 5.0

    trials = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )
    assert len(trials) == 1
    assert agent.s.node(trials[0])["attrs"]["bundle_member_count"] == 3.0
    assert agent.inner.neighbours(
        trials[0],
        "enacts_humanoid_motor_program",
    ) == [program]


def _persistent_singleton_surprise_fixture(*, surprise_streak: int):
    agent, episode = _inverse_control_fixture()
    policy = _one_node(agent, "HumanoidPolicy")
    for key, value in {
        "native_humanoid_composition_enabled": 0,
        "persistent_task_residual_authority": 1,
        "gait_surprise_confirmation_receipts": 2,
    }.items():
        agent.inner.set_attr(policy, key, value)
    for key, value in {
        "locomotion_residual_m": 3,
        "locomotion_drive_active": 1,
        "gait_surprise_streak": surprise_streak,
        "sensorimotor_interrupt_required": 0,
        "reset_requested": 0,
        "target_directed_progress_m": 3,
        "lifetime_completed_progress": 0,
        "directed_progress": 0,
        "physics_time_step": 1,
        "state_vz": 0,
        "developmental_curriculum_active": 1,
        "developmental_goal": "compound_curiosity_fixture",
    }.items():
        agent.inner.set_attr(episode, key, value)

    for model in agent.inner.neighbours(
        episode,
        "has_humanoid_phase_action_model",
    ):
        attrs = agent.s.node(model)["attrs"]
        for key in ("dzx", "dzy", "dwx", "dwy", "dvy", "dvz"):
            agent.inner.set_attr(model, f"mean_{key}", 0)
        agent.inner.set_attr(
            model,
            "mean_dvx",
            1 if attrs["token"] == "motor_a" else -1,
        )

    for synergy in agent.inner.neighbours(
        episode,
        "has_humanoid_synergy_model",
    ):
        attrs = agent.s.node(synergy)["attrs"]
        pair = {attrs["token_a"], attrs["token_b"]}
        for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"):
            agent.inner.set_attr(synergy, f"residual_{key}", 0)
        agent.inner.set_attr(
            synergy,
            "experience_count",
            1 if pair == {"motor_a", "motor_b"} else 3,
        )
        agent.inner.set_attr(
            synergy,
            "last_program_update_request_seq",
            0,
        )
    return agent, episode


@pytest.mark.parametrize("native_composition", [0, 1])
def test_persistent_surprise_explores_additively_worse_exact_pair(
    native_composition,
):
    quiet_agent, quiet_episode = _persistent_singleton_surprise_fixture(
        surprise_streak=0,
    )
    quiet_agent.inner.set_attr(
        _one_node(quiet_agent, "HumanoidPolicy"),
        "native_humanoid_composition_enabled",
        native_composition,
    )
    quiet_agent.tick()
    _resume_graph_motor_synthesis(quiet_agent, quiet_episode)
    quiet_program = quiet_agent.inner.neighbours(
        quiet_episode,
        "has_humanoid_motor_program",
    )[0]
    assert quiet_agent.s.node(quiet_program)["attrs"]["member_count"] == 1

    agent, episode = _persistent_singleton_surprise_fixture(
        surprise_streak=2,
    )
    agent.inner.set_attr(
        _one_node(agent, "HumanoidPolicy"),
        "native_humanoid_composition_enabled",
        native_composition,
    )
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    attrs = agent.s.node(program)["attrs"]
    tokens = {
        agent.s.node(member)["attrs"]["token"]
        for member in agent.inner.neighbours(
            program,
            "includes_humanoid_phase_action_model",
        )
    }

    assert attrs["member_count"] == 2
    assert attrs["compound_selection_kind"] == (
        "persistent_residual_surprise_curiosity"
    )
    assert attrs["compound_curiosity_pair_experience"] == 1
    assert tokens == {"motor_a", "motor_b"}


def test_curiosity_compound_receipt_grounds_exact_program_and_pair():
    agent, episode = _persistent_singleton_surprise_fixture(
        surprise_streak=2,
    )
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    trial = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )[0]
    pair_memory = next(
        synergy
        for synergy in agent.inner.neighbours(
            episode,
            "has_humanoid_synergy_model",
        )
        if {
            agent.s.node(synergy)["attrs"]["token_a"],
            agent.s.node(synergy)["attrs"]["token_b"],
        } == {"motor_a", "motor_b"}
    )
    context = agent.s.add_node("HumanoidSituatedLocomotionContext", {
        "status": "active",
        "developmental_goal": "compound_curiosity_fixture",
    })
    _edge(
        agent,
        episode,
        "has_current_humanoid_situated_locomotion_context",
        context,
    )

    _verified_outcome(agent, trial, post_vx=0, post_z=0.1)

    attrs = agent.s.node(program)["attrs"]
    assert attrs["status"] == "grounded"
    assert attrs["receipt_learned"] == 1
    assert attrs["member_count"] == 2
    assert {
        agent.s.node(member)["attrs"]["token"]
        for member in agent.inner.neighbours(
            program,
            "includes_humanoid_phase_action_model",
        )
    } == {"motor_a", "motor_b"}
    assert agent.s.node(pair_memory)["attrs"]["experience_count"] == 2
    assert attrs["memory_eligible"] == 1


def test_curiosity_treats_unprobed_pair_as_evidence_gap_not_fault():
    agent, episode = _persistent_singleton_surprise_fixture(
        surprise_streak=2,
    )
    for synergy in agent.inner.neighbours(
        episode,
        "has_humanoid_synergy_model",
    ):
        attrs = agent.s.node(synergy)["attrs"]
        if {attrs["token_a"], attrs["token_b"]} == {
            "motor_a", "motor_c",
        }:
            agent.inner.set_attr(synergy, "approved", 0)
            agent.inner.set_attr(synergy, "rejected", 0)
            agent.inner.set_attr(synergy, "experience_count", 0)

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    tokens = {
        agent.s.node(member)["attrs"]["token"]
        for member in agent.inner.neighbours(
            program,
            "includes_humanoid_phase_action_model",
        )
    }
    assert tokens == {"motor_a", "motor_c"}
    assert agent.s.node(program)["attrs"][
        "compound_curiosity_pair_experience"
    ] == 0


def test_failed_windows_bound_takeoff_analysis_without_forcing_width():
    agent, episode = _persistent_singleton_surprise_fixture(
        surprise_streak=0,
    )
    agent.inner.set_attr(episode, "self_takeoff_drive_active", 1)
    agent.inner.set_attr(
        _one_node(agent, "HumanoidPolicy"),
        "native_humanoid_composition_enabled",
        1,
    )
    agent.inner.set_attr(episode, "self_takeoff_target_velocity_scale", 1)
    development = agent.s.add_node("EmbodiedDevelopmentEpisode", {
        "development_evidence_window": 4,
    })
    capability = agent.s.add_node(
        "EmbodiedSituatedDevelopmentalCapability", {
            "evidence_kind": "support_reducing_elevation",
            "success_count": 0,
            # Four failed evidence windows imply order 1 + sqrt(4) = 3.
            "failure_count": 16,
        },
    )
    _edge(agent, episode, "projects_embodied_development", development)
    _edge(
        agent,
        development,
        "has_active_embodied_developmental_capability",
        capability,
    )

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    attrs = agent.s.node(program)["attrs"]
    assert attrs["motor_task_context"] == "self_takeoff"
    # Failed evidence sets analysis depth, not actuator authority.  This
    # fixture has no terminally improving higher-order effect, so it remains
    # at the normal admissible program instead of forcing width three.
    assert attrs["member_count"] == 1
    assert attrs.get("compound_selection_kind", "none") == "none"


def test_material_interrupt_withdraws_situated_compound_memory_authority():
    agent, episode = _persistent_singleton_surprise_fixture(
        surprise_streak=2,
    )
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    trial = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )[0]
    context = agent.s.add_node("HumanoidSituatedLocomotionContext", {
        "status": "active",
        "developmental_goal": "compound_curiosity_fixture",
    })
    _edge(
        agent,
        episode,
        "has_current_humanoid_situated_locomotion_context",
        context,
    )
    agent.inner.set_attr(episode, "state_maximum_power_watts", 1)

    _verified_outcome(
        agent,
        trial,
        post_vx=0,
        post_z=0.1,
        peak_power_watts=2,
    )

    attrs = agent.s.node(program)["attrs"]
    assert attrs["status"] == "grounded"
    assert attrs["receipt_learned"] == 1
    assert attrs["memory_eligible"] == 0


def test_compound_curiosity_rules_are_integer_literal_native():
    from scripts.gen_humanoid_adaptation_seed import manifest

    selected = {
        rule["name"]: rule
        for rule in manifest()["rules"]
        if rule["name"] in {
            "ha_curiosity_selects_persistent_singleton_compound",
            "ha_curiosity_expands_exact_compound_program",
        }
    }

    def assert_integer_literals(value):
        assert not isinstance(value, float)
        if isinstance(value, dict):
            for nested in value.values():
                assert_integer_literals(nested)
        elif isinstance(value, list):
            for nested in value:
                assert_integer_literals(nested)

    assert set(selected) == {
        "ha_curiosity_selects_persistent_singleton_compound",
        "ha_curiosity_expands_exact_compound_program",
    }
    for rule in selected.values():
        assert_integer_literals(rule)


def test_plan_hint_selects_an_improving_synthesis_basin_not_an_action():
    def synthesize(hint_context: str | None) -> set[str]:
        agent, episode = _inverse_control_fixture()
        policy = _one_node(agent, "HumanoidPolicy")
        agent.inner.set_attr(policy, "target_froude_speed", 4)
        active_models = []
        effects = {"motor_a": 1, "motor_b": 7, "motor_c": 7}
        for model in agent.inner.neighbours(
            episode, "has_humanoid_phase_action_model"
        ):
            attrs = agent.s.node(model)["attrs"]
            if attrs["support_phase"] == 0.0:
                active_models.append(model)
                agent.inner.set_attr(
                    model, "mean_dvx", effects[attrs["token"]]
                )
        for synergy in agent.inner.neighbours(
            episode, "has_humanoid_synergy_model"
        ):
            agent.inner.set_attr(synergy, "residual_dvx", 0.0)
        if hint_context is not None:
            basin = agent.s.add_node("HumanoidMotorProgram", {
                "status": "grounded",
                "output_authority": 0.0,
                "motor_task_context": hint_context,
            })
            preferred = next(
                model for model in active_models
                if agent.s.node(model)["attrs"]["token"] == "motor_c"
            )
            _edge(
                agent,
                basin,
                "includes_humanoid_phase_action_model",
                preferred,
            )
            _edge(
                agent,
                episode,
                "has_humanoid_motor_program_basin_seed",
                basin,
            )
        agent.tick()
        _resume_graph_motor_synthesis(agent, episode)
        program = next(
            candidate
            for candidate in agent.inner.neighbours(
                episode, "has_humanoid_motor_program"
            )
            if agent.s.node(candidate)["attrs"].get("request_seq") == 1.0
        )
        return {
            agent.s.node(model)["attrs"]["token"]
            for model in agent.inner.neighbours(
                program, "includes_humanoid_phase_action_model"
            )
        }

    assert synthesize(None) == {"motor_a", "motor_b"}
    assert synthesize("locomotion") == {"motor_a", "motor_c"}
    assert synthesize("self_takeoff") == {"motor_a", "motor_b"}


def test_observed_topology_transition_locates_equal_consequence_basin():
    def synthesize(context: str | None) -> set[str]:
        agent, episode = _inverse_control_fixture()
        policy = _one_node(agent, "HumanoidPolicy")
        agent.inner.set_attr(policy, "target_froude_speed", 4)
        agent.inner.set_attr(episode, "state_support_0_force", 1.0)
        agent.inner.set_attr(episode, "state_support_1_force", 1.0)
        active_models = []
        effects = {"motor_a": 1, "motor_b": 7, "motor_c": 7}
        for model in agent.inner.neighbours(
            episode, "has_humanoid_phase_action_model"
        ):
            attrs = agent.s.node(model)["attrs"]
            if attrs["support_phase"] == 0.0:
                active_models.append(model)
                agent.inner.set_attr(model, "mean_dvx", effects[attrs["token"]])
        for synergy in agent.inner.neighbours(
            episode, "has_humanoid_synergy_model"
        ):
            agent.inner.set_attr(synergy, "residual_dvx", 0.0)
        if context is not None:
            hint = agent.s.add_node("EmbodiedMotorPlanHint", {
                "output_authority": 0,
            })
            source = agent.s.add_node("EmbodiedMotorPlanHintStage", {
                "support_topology": "paired_lower_support",
                "output_authority": 0,
            })
            target = agent.s.add_node("EmbodiedMotorPlanHintStage", {
                "output_authority": 0,
            })
            shape = agent.s.add_node("EmbodiedMotorConsequenceRoutingShape", {})
            program = agent.s.add_node("HumanoidMotorProgram", {
                "status": "grounded",
                "output_authority": 0,
                "motor_task_context": context,
            })
            preferred = next(
                model for model in active_models
                if agent.s.node(model)["attrs"]["token"] == "motor_c"
            )
            _edge(agent, episode, "considers_humanoid_motor_plan_hint", hint)
            _edge(agent, hint, "has_embodied_motor_plan_hint_stage", source)
            _edge(
                agent, source,
                "can_transition_to_embodied_motor_plan_hint_stage", target,
            )
            _edge(
                agent, target,
                "targets_embodied_motor_consequence_shape", shape,
            )
            _edge(
                agent, program,
                "realizes_embodied_motor_consequence_shape", shape,
            )
            _edge(
                agent, program,
                "includes_humanoid_phase_action_model", preferred,
            )
        agent.tick()
        _resume_graph_motor_synthesis(agent, episode)
        program = next(
            candidate
            for candidate in agent.inner.neighbours(
                episode, "has_humanoid_motor_program"
            )
            if agent.s.node(candidate)["attrs"].get("request_seq") == 1.0
        )
        return {
            agent.s.node(model)["attrs"]["token"]
            for model in agent.inner.neighbours(
                program, "includes_humanoid_phase_action_model"
            )
        }

    assert synthesize(None) == {"motor_a", "motor_b"}
    assert synthesize("locomotion") == {"motor_a", "motor_c"}
    assert synthesize("self_takeoff") == {"motor_a", "motor_b"}


def test_takeoff_compression_prices_recruitment_without_disabling_composition():
    def composed_width(compression_authority):
        agent, episode = _inverse_control_fixture()
        policy = _one_node(agent, "HumanoidPolicy")
        for key, value in {
            "self_takeoff_drive_active": 1.0,
            "self_takeoff_target_velocity_scale": 0.8,
            "self_takeoff_compression_scale": 1.0,
            "state_vz": 0.0,
            "body_mass": 1.0,
            "motor_effector_group_count": 3.0,
        }.items():
            agent.inner.set_attr(episode, key, value)
        agent.inner.set_attr(
            policy,
            "takeoff_motor_compression_authority",
            compression_authority,
        )
        models = agent.inner.neighbours(
            episode,
            "has_humanoid_phase_action_model",
        )
        for model in models:
            attrs = agent.s.node(model)["attrs"]
            agent.inner.set_attr(
                model,
                "mean_dvz",
                0.2 if attrs["token"] == "motor_a" else 0.8,
            )
            agent.inner.set_attr(model, "mean_input_energy_joules", 0.0)
        agent.tick()
        _resume_graph_motor_synthesis(agent, episode)
        program = agent.inner.neighbours(
            episode,
            "has_humanoid_motor_program",
        )[0]
        return agent.s.node(program)["attrs"]["member_count"]

    uncompressed_width = composed_width(0.0)
    compressed_width = composed_width(1.0)
    assert uncompressed_width > 1.0
    assert 1.0 <= compressed_width < uncompressed_width


def test_supported_takeoff_focuses_response_by_discovered_motor_dimension():
    agent, episode = _inverse_control_fixture()
    agent.inner.set_attr(episode, "self_takeoff_drive_active", 1.0)
    agent.inner.set_attr(episode, "self_takeoff_target_velocity_scale", 0.8)
    agent.inner.set_attr(episode, "topology_focused_response_count", 0.0)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    attrs = agent.s.node(episode)["attrs"]
    assert attrs["selected_response_frames"] == 1.0
    assert attrs["topology_focused_response_count"] >= 1.0


def test_takeoff_focus_does_not_shorten_a_locomotion_trial():
    agent, episode = _inverse_control_fixture()
    agent.inner.set_attr(episode, "self_takeoff_drive_active", 1.0)
    agent.inner.set_attr(episode, "self_takeoff_target_velocity_scale", 0.8)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    trial = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )[0]
    agent.inner.set_attr(trial, "motor_task_context", "locomotion")
    agent.inner.set_attr(trial, "response_frames", 9.0)
    agent.inner.set_attr(episode, "selected_response_frames", 9.0)
    agent.inner.set_attr(episode, "topology_focused_response_count", 0.0)

    agent.tick()

    assert agent.s.node(trial)["attrs"]["response_frames"] == 9.0
    assert (
        agent.s.node(episode)["attrs"]["topology_focused_response_count"]
        == 0.0
    )


def test_deployment_prediction_monitor_does_not_require_learning_edge():
    agent, episode = _inverse_control_fixture()
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    trial = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )[0]
    for model in agent.inner.neighbours(
        trial,
        "uses_humanoid_phase_action_model",
    ):
        agent.s.remove_edge(
            trial,
            "uses_humanoid_phase_action_model",
            model,
        )
    outcome = _verified_outcome(agent, trial, post_vx=2.0)

    assert agent.s.node(outcome)["attrs"]["prediction_error_measured"] == 1.0
    assert agent.s.node(episode)["attrs"]["latest_gait_prediction_error"] > 0.0


def test_upright_recovery_prices_downward_momentum_from_support_models():
    agent, episode = _inverse_control_fixture()
    agent.inner.set_attr(episode, "recovery_mode", 1.0)
    agent.inner.set_attr(episode, "aerial_active", 1.0)
    agent.inner.set_attr(episode, "state_vz", -1.0)
    agent.inner.set_attr(episode, "motor_recovery_primary_ready", 0.0)
    for model in agent.inner.neighbours(
        episode,
        "has_humanoid_phase_action_model",
    ):
        attrs = agent.s.node(model)["attrs"]
        if attrs["support_phase"] != 0.0:
            continue
        agent.inner.set_attr(
            model,
            "mean_dvz",
            1.0 if attrs["token"] == "motor_b" else 0.0,
        )

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["selected_recovery_primary_token"] == "motor_b"
    trials = [
        trial
        for trial in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(trial)["attrs"]["request_seq"] == 1.0
    ]
    assert len(trials) == 1
    trial_attrs = agent.s.node(trials[0])["attrs"]
    assert trial_attrs["token"] == "motor_b"
    assert trial_attrs["decision_kind"] == "learned_walk"
    assert trial_attrs["collapse_kind"] == "compound_recovery_locomotion"
    assert trial_attrs["open_residual_count"] == 2.0
    assert trial_attrs["bundle_member_count"] > 1.0
    programs = agent.inner.neighbours(
        trials[0],
        "enacts_humanoid_motor_program",
    )
    assert len(programs) == 1
    program_attrs = agent.s.node(programs[0])["attrs"]
    assert program_attrs["motor_residual_context"] == "recovery_locomotion"

    _verified_outcome(agent, trials[0])
    for key, value in {
        "recovery_mode": 0.0,
        "aerial_active": 0.0,
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 0.0,
        "motor_primary_ready": 1.0,
        "selected_primary_token": "motor_a",
        "selected_primary_context_id": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    next_trial = next(
        trial
        for trial in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(trial)["attrs"]["request_seq"] == 2.0
    )
    next_program = agent.inner.neighbours(
        next_trial,
        "enacts_humanoid_motor_program",
    )[0]
    assert next_program != programs[0]
    assert (
        agent.s.node(next_program)["attrs"]["motor_residual_context"]
        == "locomotion"
    )


def test_support_loss_is_weighted_evidence_not_a_memory_or_recovery_veto():
    agent, episode = _inverse_control_fixture()
    for key, value in {
        "state_vz": 0.0,
        "body_mass": 1.0,
        "motor_effector_group_count": 3.0,
    }.items():
        agent.inner.set_attr(episode, key, value)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    trial = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )[0]

    _verified_outcome(
        agent,
        trial,
        pre_support_force=10.0,
        post_support_force=0.0,
    )

    attrs = agent.s.node(program)["attrs"]
    assert attrs["motor_task_context"] == "locomotion"
    assert attrs["motor_task_phase"] == "launch"
    assert attrs["memory_eligible"] == 1.0
    assert attrs["support_loss_ema"] == 1.0
    assert attrs["support_deficit_ema"] == 1.0
    assert agent.s.node(episode)["attrs"]["recovery_mode"] == 0.0


def test_aerial_topology_does_not_remove_compound_action_authority():
    agent, episode = _inverse_control_fixture()
    for key, value in {
        "active_support_count": 0.0,
        "current_support_phase": 2.0,
        "body_mass": 1.0,
        "motor_effector_group_count": 3.0,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)

    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    attrs = agent.s.node(program)["attrs"]
    assert attrs["allow_expansion"] == 1.0
    assert attrs["member_count"] > 1.0


def test_intentional_takeoff_owns_gait_surprise_until_a_body_limit_fails():
    agent, episode = _inverse_control_fixture()
    for key, value in {
        "self_takeoff_drive_active": 1.0,
        "self_takeoff_target_velocity_scale": 0.8,
        "state_vz": 0.0,
        "body_mass": 1.0,
        "motor_effector_group_count": 3.0,
    }.items():
        agent.inner.set_attr(episode, key, value)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    trial = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )[0]
    assert agent.s.node(trial)["attrs"]["motor_task_context"] == "self_takeoff"
    agent.inner.set_attr(episode, "self_takeoff_drive_active", 0.0)
    agent.inner.set_attr(episode, "tilt_magnitude", 2.0)

    _verified_outcome(agent, trial)

    assert agent.s.node(episode)["attrs"]["upright"] == 1.0
    assert agent.s.node(episode)["attrs"]["recovery_mode"] == 0.0


def test_upright_deliberate_task_reclaims_controller_before_selection():
    agent, episode = _inverse_control_fixture()
    agent.inner.set_attr(episode, "self_takeoff_drive_active", 1.0)
    agent.inner.set_attr(episode, "recovery_mode", 1.0)
    agent.inner.set_attr(episode, "recovery_entry_open", 1.0)

    agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["recovery_mode"] == 0.0
    assert attrs["recovery_entry_open"] == 0.0


def test_host_resume_boundary_delivers_only_a_structural_event():
    source = inspect.getsource(_resume_graph_motor_synthesis)

    assert "agent.s.add_edge" in source
    assert '"resumes_humanoid_motor_program"' in source
    assert "set_attr" not in source


def test_grounded_population_program_is_reassociated_before_resynthesis():
    agent, episode = _inverse_control_fixture()

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    for key, value in {
        "status": "grounded",
        "receipt_learned": 1.0,
        "memory_eligible": 1.0,
        "experience_count": 1.0,
        "response_frames": 5.0,
        "mean_dzx": 0.0,
        "mean_dzy": 0.0,
        "mean_dwx": 0.0,
        "mean_dwy": 0.0,
        "mean_dvx": 1.0,
        "mean_dvy": 0.0,
        "mean_rate_dzx": 0.0,
        "mean_rate_dzy": 0.0,
        "mean_rate_dwx": 0.0,
        "mean_rate_dwy": 0.0,
        "mean_rate_dvx": 0.2,
        "mean_rate_dvy": 0.0,
    }.items():
        agent.inner.set_attr(program, key, value)

    agent.inner.set_attr(episode, "request_seq", 2.0)
    agent.inner.set_attr(episode, "last_trial_request_seq", 1.0)
    agent.inner.set_attr(episode, "action_ready", 0.0)
    agent.inner.set_attr(episode, "motor_primary_ready", 1.0)
    agent.inner.set_attr(episode, "selected_primary_token", "motor_a")
    agent.inner.set_attr(episode, "motor_memory_recall_count", 0.0)
    agent.inner.set_attr(episode, "last_compound_decision_count", 10.0)
    agent.tick()

    programs = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )
    trials = [
        trial
        for trial in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(trial)["attrs"]["request_seq"] == 2.0
    ]

    assert programs == [program]
    assert len(trials) == 1
    assert agent.s.node(trials[0])["attrs"]["motor_memory_recalled"] == 1.0
    preparations = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_preparation",
    )
    assert len(preparations) == 1
    assert agent.s.node(preparations[0])["attrs"][
        "preparation_kind"
    ] == "memory"
    assert agent.s.node(preparations[0])["attrs"][
        "status"
    ] == "output_potent"
    assert agent.inner.neighbours(
        trials[0],
        "released_from_humanoid_motor_preparation",
    ) == preparations
    assert agent.inner.neighbours(
        trials[0],
        "enacts_humanoid_motor_program",
    ) == [program]
    assert agent.s.node(episode)["attrs"]["motor_memory_recall_count"] == 1.0
    assert agent.s.node(program)["attrs"]["recall_count"] == 1.0
    assert agent.s.node(episode)["attrs"][
        "last_compound_decision_count"
    ] == agent.s.node(episode)["attrs"]["decision_count"]

    _verified_outcome(agent, trials[0])

    memory = agent.s.node(program)["attrs"]
    assert memory["experience_count"] == 2.0
    assert memory["mean_dvx"] == pytest.approx(0.9)
    assert memory["memory_eligible"] == 1.0
    assert memory["mean_prediction_error_energy"] > 0.0
    assert memory["response_frames"] == 4.0


def test_shape_warm_singleton_verifies_then_runs_as_system_one_default():
    agent, episode = _inverse_control_fixture()
    memory = _ground_singleton_program(agent, episode)
    for key, value in {
        "source": "shape_warm_start",
        "warm_start_requires_verification": 1.0,
        "warm_start_verified": 0.0,
        "experience_count": 10.0,
        "mean_prediction_error_energy": 0.0,
        "mean_lateral_prediction_error_energy": 0.0,
        "mean_dzx": 0.0,
        "mean_dzy": 0.0,
        "mean_dwx": 0.0,
        "mean_dwy": 0.0,
        "mean_dvx": 1.0,
        "mean_dvy": 0.0,
        "mean_rate_dzx": 0.0,
        "mean_rate_dzy": 0.0,
        "mean_rate_dwx": 0.0,
        "mean_rate_dwy": 0.0,
        "mean_rate_dvx": 0.2,
        "mean_rate_dvy": 0.0,
    }.items():
        agent.inner.set_attr(memory, key, value)

    def request(sequence: int):
        decision_count = agent.s.node(episode)["attrs"]["decision_count"]
        agent.inner.set_attr(episode, "request_seq", float(sequence))
        agent.inner.set_attr(
            episode,
            "last_trial_request_seq",
            float(sequence - 1),
        )
        agent.inner.set_attr(episode, "action_ready", 0.0)
        agent.inner.set_attr(episode, "motor_primary_ready", 1.0)
        agent.inner.set_attr(episode, "last_directed_step", 1)
        agent.inner.set_attr(
            episode,
            "last_compound_decision_count",
            decision_count,
        )
        agent.tick()
        _resume_graph_motor_synthesis(agent, episode)
        return [
            trial
            for trial in agent.inner.neighbours(
                episode,
                "has_humanoid_motor_trial",
            )
            if agent.s.node(trial)["attrs"]["request_seq"]
            == float(sequence)
        ][0]

    verification_trial = request(2)
    assert agent.s.node(verification_trial)["attrs"].get(
        "motor_memory_recalled",
        0.0,
    ) == 0.0
    assert agent.s.node(verification_trial)["attrs"][
        "motor_memory_structurally_reused"
    ] == 1.0
    assert agent.inner.neighbours(
        verification_trial,
        "enacts_humanoid_motor_program",
    ) == [memory]
    verified_response_frames = agent.s.node(verification_trial)["attrs"][
        "response_frames"
    ]
    _verified_outcome(agent, verification_trial)
    assert agent.s.node(memory)["attrs"]["warm_start_verified"] == 1.0
    assert agent.s.node(memory)["attrs"][
        "response_frames"
    ] == verified_response_frames

    for phase_model in agent.inner.neighbours(
        episode,
        "has_humanoid_phase_action_model",
    ):
        if agent.s.node(phase_model)["attrs"]["support_phase"] == 0.0:
            agent.inner.set_attr(phase_model, "mean_dvx", -10)
    agent.inner.set_attr(episode, "evaluation_active", 0.0)
    adaptation_trial = request(3)
    assert agent.s.node(adaptation_trial)["attrs"].get(
        "motor_memory_recalled",
        0.0,
    ) == 0.0
    _verified_outcome(agent, adaptation_trial)

    agent.inner.set_attr(episode, "evaluation_active", 1.0)
    recalled_trial = request(4)
    assert agent.s.node(recalled_trial)["attrs"][
        "motor_memory_recalled"
    ] == 1.0
    assert agent.inner.neighbours(
        recalled_trial,
        "enacts_humanoid_motor_program",
    ) == [memory]
    assert agent.s.node(episode)["attrs"][
        "last_compound_decision_count"
    ] < agent.s.node(episode)["attrs"]["decision_count"]
    assert agent.s.node(episode)["attrs"][
        "warm_start_memory_recall_count"
    ] == 1.0
    _verified_outcome(agent, recalled_trial, post_vx=-0.2, post_x=-0.1)
    assert agent.s.node(memory)["attrs"]["memory_eligible"] == 0.0


def test_identical_token_in_a_distinct_body_context_gets_its_own_memory():
    agent, episode = _inverse_control_fixture()
    agent.inner.set_attr(
        _one_node(agent, "HumanoidPolicy"),
        "shared_motor_collapse_enabled",
        0,
    )
    first_memory = _ground_singleton_program(agent, episode)
    first_primary = agent.inner.neighbours(
        first_memory,
        "includes_humanoid_phase_action_model",
    )[0]
    second_primary = agent.s.add_node("HumanoidPhaseActionModel", {
        **agent.s.node(first_primary)["attrs"],
        "context_id": 1.0,
        "anchor_vx": 1,
        "configuration_shape": ("distinct_context",),
    })
    _edge(
        agent,
        episode,
        "has_humanoid_phase_action_model",
        second_primary,
    )
    _edge(
        agent,
        second_primary,
        "generalizes_humanoid_action_model",
        agent.inner.neighbours(
            first_primary,
            "generalizes_humanoid_action_model",
        )[0],
    )

    agent.inner.set_attr(episode, "request_seq", 2.0)
    agent.inner.set_attr(episode, "last_trial_request_seq", 1.0)
    agent.inner.set_attr(episode, "action_ready", 0.0)
    agent.inner.set_attr(episode, "motor_primary_ready", 1.0)
    agent.inner.set_attr(episode, "selected_primary_token", "motor_a")
    agent.inner.set_attr(episode, "selected_primary_context_id", 1.0)
    agent.inner.set_attr(episode, "state_vx", 1)
    agent.inner.set_attr(
        episode,
        "state_motor_configuration_shape",
        ("distinct_context",),
    )
    agent.inner.set_attr(episode, "last_directed_step", 1)
    agent.inner.set_attr(episode, "last_compound_decision_count", 10.0)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)

    trial = [
        candidate
        for candidate in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(candidate)["attrs"]["request_seq"] == 2.0
    ][0]
    enacted = agent.inner.neighbours(
        trial,
        "enacts_humanoid_motor_program",
    )[0]
    assert enacted != first_memory
    assert agent.s.node(enacted)["attrs"]["primary_context_id"] == 1.0
    assert agent.s.node(trial)["attrs"].get(
        "motor_memory_structurally_reused",
        0.0,
    ) == 0.0


def test_structurally_identical_synthesis_consolidates_into_one_memory():
    agent, episode = _inverse_control_fixture()

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    canonical = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    first_trial = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_trial",
    )[0]
    _verified_outcome(agent, first_trial)
    assert agent.s.node(canonical)["attrs"]["status"] == "grounded"
    assert agent.s.node(canonical)["attrs"]["experience_count"] == 1.0
    agent.inner.set_attr(
        canonical,
        "mean_prediction_error_energy",
        100.0,
    )

    agent.inner.set_attr(episode, "request_seq", 2.0)
    agent.inner.set_attr(episode, "last_trial_request_seq", 1.0)
    agent.inner.set_attr(episode, "action_ready", 0.0)
    agent.inner.set_attr(episode, "motor_primary_ready", 1.0)
    agent.inner.set_attr(episode, "selected_primary_token", "motor_a")
    agent.inner.set_attr(episode, "last_compound_decision_count", 0.0)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    second_trial = [
        trial
        for trial in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(trial)["attrs"]["request_seq"] == 2.0
    ][0]
    synthesized = agent.inner.neighbours(
        second_trial,
        "synthesized_humanoid_motor_program",
    )[0]
    assert synthesized != canonical
    assert agent.inner.neighbours(
        second_trial,
        "enacts_humanoid_motor_program",
    ) == [canonical]

    _verified_outcome(agent, second_trial)

    assert agent.inner.neighbours(
        second_trial,
        "enacts_humanoid_motor_program",
    ) == [canonical]
    assert agent.inner.neighbours(
        second_trial,
        "synthesized_humanoid_motor_program",
    ) == [synthesized]
    assert agent.s.node(synthesized)["attrs"][
        "status"
    ] == "reassociated_duplicate"
    assert agent.s.node(canonical)["attrs"]["experience_count"] == 2.0
    assert agent.s.node(canonical)["attrs"]["consolidation_count"] == 1.0
    assert agent.s.node(canonical)["attrs"]["memory_eligible"] == 1.0


def test_prediction_uncertainty_keeps_an_unreliable_memory_output_null():
    agent, episode = _inverse_control_fixture()

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    unreliable = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    for key, value in {
        "status": "grounded",
        "receipt_learned": 1.0,
        "memory_eligible": 1.0,
        "experience_count": 1.0,
        "mean_prediction_error_energy": 1.0,
        "response_frames": 5.0,
        "mean_dzx": 0.0,
        "mean_dzy": 0.0,
        "mean_dwx": 0.0,
        "mean_dwy": 0.0,
        "mean_dvx": 1.0,
        "mean_dvy": 0.0,
        "mean_rate_dzx": 0.0,
        "mean_rate_dzy": 0.0,
        "mean_rate_dwx": 0.0,
        "mean_rate_dwy": 0.0,
        "mean_rate_dvx": 0.2,
        "mean_rate_dvy": 0.0,
    }.items():
        agent.inner.set_attr(unreliable, key, value)

    agent.inner.set_attr(episode, "request_seq", 2.0)
    agent.inner.set_attr(episode, "last_trial_request_seq", 1.0)
    agent.inner.set_attr(episode, "action_ready", 0.0)
    agent.inner.set_attr(episode, "motor_primary_ready", 1.0)
    agent.inner.set_attr(episode, "selected_primary_token", "motor_a")
    agent.inner.set_attr(episode, "last_compound_decision_count", 10.0)
    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)

    trial = [
        trial
        for trial in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(trial)["attrs"]["request_seq"] == 2.0
    ][0]
    assert agent.s.node(trial)["attrs"].get(
        "motor_memory_recalled",
        0.0,
    ) == 0.0
    assert agent.s.node(trial)["attrs"][
        "motor_memory_structurally_reused"
    ] == 1.0
    assert agent.inner.neighbours(
        episode,
        "has_humanoid_motor_preparation",
    ) == []


def test_fallen_body_explores_whole_actuator_alphabet_before_reset():
    agent, episode = _inverse_control_fixture()
    _enable_recovery_measurements(agent, episode)
    get_up_models = []
    for action in agent.inner.neighbours(
        episode,
        "has_humanoid_action_model",
    ):
        attrs = agent.s.node(action)["attrs"]
        model = agent.s.add_node("HumanoidGetUpActionModel", {
            "token": attrs["token"],
            "ordinal": attrs["ordinal"],
            "actuator_group": attrs["ordinal"],
            "experience_count": 0.0,
            "mean_height_gain": 0.0,
            "mean_alignment_gain": 0.0,
            "last_update_request_seq": 0.0,
        })
        _edge(
            agent,
            episode,
            "has_humanoid_get_up_action_model",
            model,
        )
        _edge(
            agent,
            model,
            "generalizes_humanoid_action_model",
            action,
        )
        get_up_models.append(model)

    for key, value in {
        "recovery_mode": 1.0,
        "upright": 0.0,
        "nominal_response_frames": 8.0,
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 0.0,
        "reset_requested": 0.0,
        "get_up_attempt_count": 0.0,
        "get_up_last_improvement_attempt": 0.0,
        "get_up_success_count": 0.0,
        "get_up_reset_count": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()
    trial = [
        candidate
        for candidate in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(candidate)["attrs"]["request_seq"] == 2.0
    ][0]
    assert agent.s.node(trial)["attrs"]["decision_kind"] == "get_up_explore"
    assert agent.s.node(trial)["attrs"]["token"] == "motor_a"
    assert agent.s.node(trial)["attrs"]["response_frames"] == 8.0

    _verified_outcome(agent, trial, post_z=1.1)
    assert agent.s.node(get_up_models[0])["attrs"][
        "experience_count"
    ] == 1.0
    assert agent.s.node(get_up_models[0])["attrs"][
        "mean_height_gain"
    ] > 0.0
    basins = agent.inner.neighbours(
        episode,
        "has_humanoid_recovery_basin",
    )
    assert len(basins) == 1
    basin_actions = agent.inner.neighbours(
        basins[0],
        "has_humanoid_recovery_basin_action",
    )
    assert len(basin_actions) == 1
    assert agent.s.node(basin_actions[0])["attrs"]["primary_token"] == (
        "motor_a"
    )
    assert agent.s.node(basin_actions[0])["attrs"][
        "mean_normalized_energy"
    ] == 1.0

    for model in get_up_models:
        agent.inner.set_attr(model, "experience_count", 1.0)
    agent.inner.set_attr(
        episode,
        "get_up_attempt_count",
        float(len(get_up_models) + 1),
    )
    agent.inner.set_attr(episode, "action_ready", 0.0)
    agent.tick()

    assert agent.s.node(episode)["attrs"]["reset_requested"] == 1.0
    assert agent.s.node(episode)["attrs"]["get_up_reset_count"] == 1.0


def test_recovery_basin_composes_compatible_effectors_and_sweeps_hold():
    agent, episode = _inverse_control_fixture()
    _enable_recovery_measurements(agent, episode)
    get_up_models = []
    for action in agent.inner.neighbours(
        episode,
        "has_humanoid_action_model",
    ):
        attrs = agent.s.node(action)["attrs"]
        model = agent.s.add_node("HumanoidGetUpActionModel", {
            "token": attrs["token"],
            "ordinal": attrs["ordinal"],
            "actuator_group": attrs["ordinal"],
            "experience_count": 1.0,
            "mean_height_gain": 0.0,
            "mean_alignment_gain": 0.0,
            "last_update_request_seq": 0.0,
        })
        _edge(
            agent,
            episode,
            "has_humanoid_get_up_action_model",
            model,
        )
        get_up_models.append(model)

    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 1.0,
        "status": "situated",
        "normalized_height": 0.1,
        "vertical_alignment": 0.0,
    })
    _edge(agent, episode, "has_humanoid_recovery_basin", basin)
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    gains = (0.1, 0.3, 0.2)
    for model, gain in zip(get_up_models, gains, strict=True):
        attrs = agent.s.node(model)["attrs"]
        action = agent.s.add_node("HumanoidRecoveryBasinAction", {
            "primary_token": attrs["token"],
            "secondary_token": attrs["token"],
            "primary_actuator_group": attrs["actuator_group"],
            "secondary_actuator_group": attrs["actuator_group"],
            "member_count": 1.0,
            "experience_count": 1.0,
            "mean_height_gain": gain,
            "mean_alignment_gain": 0.0,
            "response_frames": 8.0,
            "last_update_request_seq": 0.0,
        })
        _edge(
            agent,
            basin,
            "has_humanoid_recovery_basin_action",
            action,
        )

    model_count = float(len(get_up_models))
    for key, value in {
        "recovery_mode": 1.0,
        "upright": 0.0,
        "nominal_response_frames": 8.0,
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 0.0,
        "reset_requested": 0.0,
        "state_z": 0.1,
        "state_qx": 0.0,
        "state_qy": 0.0,
        "state_qw": 1.0,
        "state_contact_count_raw": 1.0,
        "get_up_attempt_count": model_count,
        "get_up_last_improvement_attempt": model_count,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()

    trial = next(
        candidate
        for candidate in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(candidate)["attrs"]["request_seq"] == 2.0
    )
    attrs = agent.s.node(trial)["attrs"]
    assert attrs["decision_kind"] == "get_up_exploit"
    assert attrs["token"] == "motor_b"
    assert attrs["secondary_token"] in {"motor_a", "motor_c"}
    assert attrs["secondary_token"] != attrs["token"]
    assert attrs["bundle_member_count"] == 2.0
    assert attrs["response_frames"] == 8.0
    assert agent.inner.neighbours(
        trial,
        "starts_from_humanoid_recovery_basin",
    ) == [basin]
    programs = agent.inner.neighbours(
        episode,
        "has_active_humanoid_recovery_program",
    )
    assert len(programs) == 1
    assert agent.s.node(programs[0])["attrs"]["status"] == "armed"


def test_situated_recovery_exploration_excludes_whole_body_fallback():
    agent, episode = _inverse_control_fixture()
    _enable_recovery_measurements(agent, episode)
    models = []
    for action in agent.inner.neighbours(
        episode,
        "has_humanoid_action_model",
    ):
        attrs = agent.s.node(action)["attrs"]
        model = agent.s.add_node("HumanoidGetUpActionModel", {
            "token": attrs["token"],
            "ordinal": attrs["ordinal"],
            "actuator_group": attrs["ordinal"],
            "experience_count": 0.0,
            "mean_height_gain": 0.0,
            "mean_alignment_gain": 0.0,
            "last_update_request_seq": 0.0,
        })
        _edge(agent, episode, "has_humanoid_get_up_action_model", model)
        models.append(model)

    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 1.0,
        "status": "situated",
        "normalized_height": 0.1,
        "vertical_alignment": 0.0,
    })
    _edge(agent, episode, "has_humanoid_recovery_basin", basin)
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    first = agent.s.node(models[0])["attrs"]
    tried = agent.s.add_node("HumanoidRecoveryBasinAction", {
        "primary_token": first["token"],
        "secondary_token": first["token"],
        "primary_actuator_group": first["actuator_group"],
        "secondary_actuator_group": first["actuator_group"],
        "member_count": 1.0,
        "experience_count": 1.0,
        "mean_height_gain": 0.0,
        "mean_alignment_gain": 0.0,
        "response_frames": 8.0,
        "last_update_request_seq": 1.0,
    })
    _edge(agent, basin, "has_humanoid_recovery_basin_action", tried)
    for key, value in {
        "recovery_mode": 1.0,
        "upright": 0.0,
        "nominal_response_frames": 8.0,
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 0.0,
        "reset_requested": 0.0,
        "state_z": 0.1,
        "state_qx": 0.0,
        "state_qy": 0.0,
        "state_qw": 1.0,
        "state_contact_count_raw": 1.0,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()

    trial = next(
        candidate
        for candidate in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(candidate)["attrs"]["request_seq"] == 2.0
    )
    attrs = agent.s.node(trial)["attrs"]
    assert attrs["decision_kind"] == "get_up_explore"
    assert attrs["token"] == "motor_b"
    assert attrs["secondary_token"] == "motor_b"
    assert attrs["bundle_member_count"] == 1.0
    assert agent.s.node(episode)["attrs"].get(
        "motor_recovery_primary_ready", 0.0
    ) == 0.0
    assert agent.inner.neighbours(
        episode,
        "has_active_humanoid_motor_program",
    ) == []


def test_trial_commit_collapses_conflicting_opaque_actuator_groups():
    agent, episode = _inverse_control_fixture()
    actions = {
        agent.s.node(action)["attrs"]["token"]: action
        for action in agent.inner.neighbours(
            episode,
            "has_humanoid_action_model",
        )
    }
    agent.inner.set_attr(actions["motor_b"], "actuator_group", 0.0)
    for key, value in {
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 1.0,
        "selected_token": "motor_a",
        "selected_secondary_token": "motor_b",
        "selected_response_frames": 8.0,
        "decision_kind": "get_up_explore",
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()

    trial = next(
        candidate
        for candidate in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(candidate)["attrs"]["request_seq"] == 2.0
    )
    attrs = agent.s.node(trial)["attrs"]
    assert attrs["token"] == "motor_a"
    assert attrs["secondary_token"] == "motor_a"
    assert attrs["bundle_member_count"] == 1.0


def test_compound_general_contact_mints_a_changed_successor_basin():
    agent, episode = _inverse_control_fixture()
    _enable_recovery_measurements(agent, episode)
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 1.0,
        "status": "situated",
        "configuration_shape": [0, 0],
        "normalized_height": 0.2,
        "vertical_alignment": 0.0,
    })
    _edge(agent, episode, "has_humanoid_recovery_basin", basin)
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    locally_better_action = agent.s.add_node(
        "HumanoidRecoveryBasinAction",
        {
            "primary_token": "motor_c",
            "secondary_token": "motor_c",
            "member_count": 1.0,
            "mean_height_gain": 1.0,
            "mean_alignment_gain": 1.0,
            "mean_support_gain": 1.0,
            "mean_contact_gain": 1.0,
            "mean_motion_reduction": 1.0,
            "mean_normalized_energy": 0.0,
            "mean_normalized_peak_load": 0.0,
        },
    )
    _edge(
        agent,
        basin,
        "has_humanoid_recovery_basin_action",
        locally_better_action,
    )
    trial = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": 2.0,
        "token": "motor_a",
        "secondary_token": "motor_b",
        "bundle_member_count": 2.0,
        "decision_kind": "get_up_exploit",
        "response_frames": 8.0,
    })
    _edge(agent, episode, "has_humanoid_motor_trial", trial)
    _edge(agent, trial, "starts_from_humanoid_recovery_basin", basin)
    program = agent.s.add_node("HumanoidRecoveryProgram", {
        "status": "active",
        "primary_token": "motor_a",
        "secondary_token": "motor_b",
        "response_frames": 8.0,
        "motor_weight_a": 3.0,
        "motor_weight_b": 3.0,
        "last_request_seq": 2.0,
        "launch_configuration_shape": [0, 0],
        "launch_normalized_height": 0.2,
        "launch_vertical_alignment": 0.0,
        "launch_support_count": 0.0,
        "launch_contact_count": 1.0,
        "launch_motion_energy": 0.1,
    })
    _edge(agent, basin, "has_humanoid_recovery_program", program)
    for key, value in {
        "recovery_mode": 1.0,
        "upright": 0.0,
        "state_vx": 1.0,
        "request_seq": 2.0,
        "recovery_basin_count": 1.0,
        "recovery_basin_transition_count": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)

    _verified_outcome(
        agent,
        trial,
        post_vx=1.0,
        pre_contact_count=1.0,
        post_contact_count=2.0,
        pre_configuration_shape=[0, 0],
        post_configuration_shape=[0, 1],
    )

    current = agent.inner.neighbours(
        episode,
        "has_current_humanoid_recovery_basin",
    )
    assert len(current) == 1
    assert current != [basin]
    assert agent.inner.neighbours(
        basin,
        "continues_to_humanoid_recovery_basin",
    ) == current
    assert agent.s.node(current[0])["attrs"]["contact_count"] == 2.0
    successor_attrs = agent.s.node(current[0])["attrs"]
    assert list(successor_attrs["incoming_configuration_shape"]) == [0, 0]
    assert successor_attrs["incoming_contact_count"] == 1.0
    assert successor_attrs["incoming_motor_weight_a"] == 3.0


def test_warm_transition_routes_to_stored_successor_frontier():
    agent, episode = _inverse_control_fixture()
    stored_previous = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
    })
    stored_successor = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
        "configuration_shape": [0, 1],
        "support_count": 1.0,
        "contact_count": 4.0,
        "motion_energy": 0.02,
    })
    live_previous = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
    })
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
        "warm_start_tested": 0.0,
        "configuration_shape": [0, 1],
        "support_count": 1.0,
        "contact_count": 5.0,
        "motion_energy": 0.01,
    })
    _edge(
        agent,
        stored_previous,
        "continues_to_humanoid_recovery_basin",
        stored_successor,
    )
    _edge(
        agent,
        live_previous,
        "inherits_humanoid_recovery_actions_from",
        stored_previous,
    )
    _edge(
        agent,
        basin,
        "inherits_humanoid_recovery_actions_from",
        live_previous,
    )
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    agent.inner.set_attr(episode, "recovery_path_recall_count", 0.0)
    agent.inner.set_attr(episode, "recovery_mode", 1.0)
    agent.inner.set_attr(episode, "upright", 0.0)
    agent.inner.set_attr(episode, "action_ready", 1.0)

    agent.tick()

    assert agent.inner.neighbours(
        basin,
        "inherits_humanoid_recovery_actions_from",
    ) == [stored_successor]
    assert agent.s.node(episode)["attrs"][
        "recovery_path_recall_count"
    ] == 1.0


def test_pareto_distinct_warm_successor_is_not_collapsed_into_stored_basin():
    agent, episode = _inverse_control_fixture()
    stored_previous = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
    })
    stored_successor = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
        "configuration_shape": [0, 1],
        "support_count": 1.0,
        "contact_count": 6.0,
        "motion_energy": 0.01,
    })
    live_previous = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
    })
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
        "warm_start_tested": 0.0,
        "configuration_shape": [0, 1],
        "support_count": 1.0,
        "contact_count": 2.0,
        "motion_energy": 0.1,
    })
    _edge(
        agent,
        stored_previous,
        "continues_to_humanoid_recovery_basin",
        stored_successor,
    )
    _edge(
        agent,
        live_previous,
        "inherits_humanoid_recovery_actions_from",
        stored_previous,
    )
    _edge(
        agent,
        basin,
        "inherits_humanoid_recovery_actions_from",
        live_previous,
    )
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    agent.inner.set_attr(episode, "recovery_path_recall_count", 0.0)
    agent.inner.set_attr(episode, "recovery_mode", 1.0)
    agent.inner.set_attr(episode, "upright", 0.0)
    agent.inner.set_attr(episode, "action_ready", 1.0)

    agent.tick()

    assert agent.inner.neighbours(
        basin,
        "inherits_humanoid_recovery_actions_from",
    ) == [live_previous]
    assert agent.s.node(episode)["attrs"][
        "recovery_path_recall_count"
    ] == 0.0


def test_settled_warm_basin_tests_causal_stored_transition_first():
    agent, episode = _inverse_control_fixture()
    incoming_shape = [0, 1, -1]
    stored_previous = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
    })
    stored_successor = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
        "normalized_height": 0.22,
        "vertical_alignment": 0.35,
        "support_count": 2.0,
        "contact_count": 6.0,
        "motion_energy": 0.01,
        "incoming_primary_token": "motor_b",
        "incoming_secondary_token": "motor_c",
        "incoming_response_frames": 8.0,
        "incoming_motor_weight_a": 7.5,
        "incoming_motor_weight_b": 6.5,
        "incoming_configuration_shape": incoming_shape,
        "incoming_support_count": 0.0,
        "incoming_contact_count": 4.0,
        "incoming_motion_energy": 0.04,
    })
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
        "warm_start_tested": 0.0,
    })
    _edge(
        agent,
        stored_previous,
        "continues_to_humanoid_recovery_basin",
        stored_successor,
    )
    _edge(
        agent,
        basin,
        "inherits_humanoid_recovery_actions_from",
        stored_previous,
    )
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    for key, value in {
        "recovery_mode": 1.0,
        "upright": 0.0,
        "action_ready": 0.0,
        "reset_requested": 0.0,
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "recovery_path_hint_count": 0.0,
        "recovery_warm_start_count": 0.0,
        "state_motor_configuration_shape": incoming_shape,
        "active_support_count": 0.0,
        "state_contact_count_raw": 4.0,
        "state_vx": 0.1,
        "state_vy": 0.1,
        "state_vz": 0.1,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()

    trial = next(
        candidate
        for candidate in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(candidate)["attrs"]["request_seq"] == 2.0
    )
    attrs = agent.s.node(trial)["attrs"]
    assert attrs["decision_kind"] == "get_up_exploit"
    assert attrs["token"] == "motor_b"
    assert attrs["secondary_token"] == "motor_c"
    assert attrs["bundle_member_count"] == 2.0
    assert attrs["motor_weight_a"] == 7.5
    assert attrs["motor_weight_b"] == 6.5
    assert agent.s.node(episode)["attrs"]["recovery_path_hint_count"] == 1.0
    program = agent.inner.neighbours(
        episode,
        "has_active_humanoid_recovery_program",
    )[0]
    program_attrs = agent.s.node(program)["attrs"]
    assert program_attrs["termination_kind"] == (
        "stored_successor_approach_or_pareto_loss"
    )
    assert program_attrs["target_normalized_height"] == 0.22
    assert program_attrs["target_vertical_alignment"] == 0.35
    assert program_attrs["target_support_count"] == 2.0
    assert program_attrs["target_contact_count"] == 6.0
    assert program_attrs["target_motion_energy"] == 0.01
    assert program_attrs["motor_weight_a"] == 7.5
    assert program_attrs["motor_weight_b"] == 6.5
    assert list(program_attrs["launch_configuration_shape"]) == incoming_shape


def test_recovery_probe_reanchors_to_observed_successor_before_next_probe():
    agent, episode = _inverse_control_fixture()
    _enable_recovery_measurements(agent, episode)
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "status": "situated",
        "configuration_shape": [0, 1],
        "normalized_height": 0.3,
        "vertical_alignment": 0.5,
        "support_count": 2.0,
        "contact_count": 4.0,
        "motion_energy": 0.01,
        "incoming_primary_token": "motor_b",
        "incoming_secondary_token": "motor_c",
        "incoming_response_frames": 8.0,
        "incoming_motor_weight_a": 7.0,
        "incoming_motor_weight_b": 6.0,
        "reanchor_after_request_seq": 1.0,
    })
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    model = agent.s.add_node("HumanoidGetUpActionModel", {
        "token": "motor_a",
        "ordinal": 0.0,
        "actuator_group": 0.0,
        "experience_count": 1.0,
    })
    _edge(agent, episode, "has_humanoid_get_up_action_model", model)
    remaining_model = agent.s.add_node("HumanoidGetUpActionModel", {
        "token": "motor_b",
        "ordinal": 1.0,
        "actuator_group": 1.0,
        "experience_count": 1.0,
    })
    _edge(
        agent,
        episode,
        "has_humanoid_get_up_action_model",
        remaining_model,
    )
    probe = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": 2.0,
        "token": "motor_a",
        "secondary_token": "motor_a",
        "bundle_member_count": 1.0,
        "decision_kind": "get_up_explore",
        "response_frames": 8.0,
    })
    _edge(agent, episode, "has_humanoid_motor_trial", probe)
    _edge(agent, probe, "starts_from_humanoid_recovery_basin", basin)
    agent.inner.set_attr(episode, "action_ready", 1.0)
    _verified_outcome(
        agent,
        probe,
        pre_configuration_shape=[0, 1],
        post_configuration_shape=[1, 0],
    )
    for key, value in {
        "recovery_mode": 1.0,
        "upright": 0.0,
        "request_seq": 3.0,
        "last_trial_request_seq": 2.0,
        "action_ready": 0.0,
        "reset_requested": 0.0,
        "state_motor_configuration_shape": [1, 0],
        "recovery_reanchor_count": 0.0,
        "recovery_program_count": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()

    trial = next(
        candidate
        for candidate in agent.inner.neighbours(
            episode, "has_humanoid_motor_trial"
        )
        if agent.s.node(candidate)["attrs"]["request_seq"] == 3.0
    )
    attrs = agent.s.node(trial)["attrs"]
    assert attrs["decision_kind"] == "get_up_reanchor"
    assert attrs["token"] == "motor_b"
    assert attrs["secondary_token"] == "motor_c"
    assert attrs["motor_weight_a"] == 7.0
    assert attrs["motor_weight_b"] == 6.0
    assert agent.s.node(basin)["attrs"]["reanchor_after_request_seq"] == 2.0
    assert agent.s.node(episode)["attrs"]["recovery_reanchor_count"] == 1.0


def test_recovery_basin_tests_predecessor_action_as_a_hint():
    agent, episode = _inverse_control_fixture()
    _enable_recovery_measurements(agent, episode)
    previous = agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 1.0,
        "status": "situated",
        "normalized_height": 0.1,
        "vertical_alignment": 0.0,
    })
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 2.0,
        "status": "situated",
        "normalized_height": 0.2,
        "vertical_alignment": 0.0,
        "warm_start_tested": 0.0,
    })
    hint = agent.s.add_node("HumanoidRecoveryBasinAction", {
        "primary_token": "motor_b",
        "secondary_token": "motor_c",
        "primary_actuator_group": 1.0,
        "secondary_actuator_group": 2.0,
        "member_count": 2.0,
        "experience_count": 2.0,
        "mean_height_gain": 0.2,
        "mean_alignment_gain": 0.1,
        "response_frames": 16.0,
        "last_update_request_seq": 1.0,
    })
    _edge(agent, episode, "has_humanoid_recovery_basin", previous)
    _edge(agent, episode, "has_humanoid_recovery_basin", basin)
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    _edge(
        agent,
        basin,
        "inherits_humanoid_recovery_actions_from",
        previous,
    )
    _edge(
        agent,
        previous,
        "has_humanoid_recovery_basin_action",
        hint,
    )
    for key, value in {
        "phase": "locomotion",
        "recovery_mode": 1.0,
        "upright": 0.0,
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 0.0,
        "reset_requested": 0.0,
        "get_up_attempt_count": 3.0,
        "get_up_last_improvement_attempt": 3.0,
        "get_up_exploitation_start_attempt": 3.0,
        "recovery_basin_start_attempt": 3.0,
        "recovery_action_count": 3.0,
        "recovery_warm_start_count": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()

    trial = next(
        candidate
        for candidate in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(candidate)["attrs"]["request_seq"] == 2.0
    )
    attrs = agent.s.node(trial)["attrs"]
    assert attrs["decision_kind"] == "get_up_exploit"
    assert attrs["token"] == "motor_b"
    assert attrs["secondary_token"] == "motor_c"
    assert attrs["response_frames"] == 16.0
    assert agent.inner.neighbours(
        trial,
        "starts_from_humanoid_recovery_basin",
    ) == [basin]
    assert agent.s.node(basin)["attrs"]["warm_start_tested"] == 1.0
    assert agent.s.node(episode)["attrs"]["recovery_warm_start_count"] == 1.0


def test_compound_recovery_program_repeats_until_receipt_loses_progress():
    agent, episode = _inverse_control_fixture()
    _enable_recovery_measurements(agent, episode)
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 1.0,
        "status": "candidate",
        "normalized_height": 0.4,
        "vertical_alignment": 0.1,
    })
    action = agent.s.add_node("HumanoidRecoveryBasinAction", {
        "primary_token": "motor_b",
        "secondary_token": "motor_c",
        "primary_actuator_group": 1.0,
        "secondary_actuator_group": 2.0,
        "member_count": 2.0,
        "experience_count": 1.0,
        "mean_height_gain": 0.1,
        "mean_alignment_gain": 0.0,
        "mean_support_gain": 0.0,
        "mean_contact_gain": 0.0,
        "mean_motion_reduction": 0.0,
        "mean_normalized_energy": 2.0,
        "mean_normalized_peak_load": 0.0,
        "response_frames": 8.0,
        "last_update_request_seq": 1.0,
    })
    _edge(agent, episode, "has_humanoid_recovery_basin", basin)
    _edge(agent, episode, "has_current_humanoid_recovery_basin", basin)
    _edge(agent, basin, "has_humanoid_recovery_basin_action", action)
    program = agent.s.add_node("HumanoidRecoveryProgram", {
        "status": "armed",
        "termination_kind": "basin_exit_or_pareto_loss",
        "primary_token": "motor_b",
        "secondary_token": "motor_c",
        "response_frames": 8.0,
        "last_receipt_progress": 0.0,
        "repeat_count": 0.0,
        "last_request_seq": 1.0,
    })
    _edge(agent, episode, "has_active_humanoid_recovery_program", program)
    _edge(agent, basin, "has_humanoid_recovery_program", program)
    _edge(agent, program, "starts_from_humanoid_recovery_basin", basin)
    source_trial = agent.s.add_node("HumanoidMotorTrial", {
        "request_seq": 1.0,
        "token": "motor_b",
        "secondary_token": "motor_c",
        "bundle_member_count": 2.0,
        "decision_kind": "get_up_exploit",
        "response_frames": 8.0,
    })
    _edge(agent, episode, "has_humanoid_motor_trial", source_trial)
    _edge(agent, source_trial, "starts_from_humanoid_recovery_basin", basin)
    # Keep the current situated basin alive while the receipt is integrated,
    # but defer repetition until the next explicit controller request.
    agent.inner.set_attr(episode, "recovery_mode", 1.0)
    agent.inner.set_attr(episode, "upright", 0.0)
    agent.inner.set_attr(episode, "action_ready", 1.0)
    source_outcome = _verified_outcome(
        agent,
        source_trial,
        post_z=1.1,
        post_vx=0.0,
        recovery_basin_considered=1.0,
    )
    # Promotion is independently covered below. Keep this synthetic receipt in
    # its source basin so this test isolates condition-terminated repetition.
    assert agent.s.node(source_outcome)["attrs"][
        "recovery_basin_considered"
    ] == 1.0
    for key, value in {
        "phase": "locomotion",
        "recovery_mode": 1.0,
        "upright": 0.0,
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 0.0,
        "reset_requested": 0.0,
        "get_up_attempt_count": 1.0,
        "get_up_last_improvement_attempt": 1.0,
        "get_up_exploitation_start_attempt": 1.0,
        "recovery_basin_start_attempt": 1.0,
        "recovery_action_count": 1.0,
        "recovery_program_count": 0.0,
        "recovery_program_repeat_count": 0.0,
        "recovery_program_termination_count": 0.0,
        # Keep the source basin open; this test isolates option termination
        # rather than the separate settled-basin promotion rule.
        "state_vx": 1.0,
        "state_wx": 1.0,
        "state_joint_velocity_energy": 100.0,
        "state_z": 0.4,
    }.items():
        agent.inner.set_attr(episode, key, value)

    agent.tick()

    programs = agent.inner.neighbours(
        episode,
        "has_active_humanoid_recovery_program",
    )
    assert programs == [program], {
        "program": agent.s.node(program)["attrs"],
        "current": agent.inner.neighbours(
            episode, "has_current_humanoid_recovery_basin"
        ),
    }
    repeated_trial = next(
        trial
        for trial in agent.inner.neighbours(episode, "has_humanoid_motor_trial")
        if agent.s.node(trial)["attrs"]["request_seq"] == 2.0
    )
    repeated = agent.s.node(repeated_trial)["attrs"]
    assert repeated["decision_kind"] == "get_up_program"
    assert repeated["token"] == "motor_b"
    assert repeated["secondary_token"] == "motor_c"

    _verified_outcome(
        agent,
        repeated_trial,
        post_z=0.9,
        post_vx=0.8,
    )
    agent.inner.set_attr(episode, "request_seq", 3.0)
    agent.inner.set_attr(episode, "last_trial_request_seq", 2.0)
    agent.inner.set_attr(episode, "action_ready", 0.0)
    agent.tick()

    assert not agent.inner.neighbours(
        episode,
        "has_active_humanoid_recovery_program",
    )
    assert agent.s.node(programs[0])["attrs"]["status"] == "retained"
    assert agent.s.node(episode)["attrs"][
        "recovery_program_termination_count"
    ] == 1.0


def test_verified_receipts_build_and_advance_a_motor_sequence():
    agent, episode = _inverse_control_fixture()

    agent.tick()
    _resume_graph_motor_synthesis(agent, episode)
    program = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )[0]
    for key, value in {
        "status": "grounded",
        "receipt_learned": 1.0,
        "memory_eligible": 1.0,
        "experience_count": 1.0,
        "response_frames": 5.0,
        "mean_dzx": 0.0,
        "mean_dzy": 0.0,
        "mean_dwx": 0.0,
        "mean_dwy": 0.0,
        "mean_dvx": 1.0,
        "mean_dvy": 0.0,
        "mean_rate_dzx": 0.0,
        "mean_rate_dzy": 0.0,
        "mean_rate_dwx": 0.0,
        "mean_rate_dwy": 0.0,
        "mean_rate_dvx": 0.2,
        "mean_rate_dvy": 0.0,
    }.items():
        agent.inner.set_attr(program, key, value)

    agent.inner.set_attr(episode, "motor_memory_recall_count", 0.0)
    agent.inner.set_attr(episode, "motor_sequence_recall_count", 0.0)
    agent.inner.set_attr(episode, "motor_sequence_transition_count", 0.0)
    agent.inner.set_attr(episode, "last_motor_sequence_receipt_seq", 0.0)

    def request(sequence: int):
        decision_count = agent.s.node(episode)["attrs"]["decision_count"]
        agent.inner.set_attr(episode, "request_seq", float(sequence))
        agent.inner.set_attr(
            episode,
            "last_trial_request_seq",
            float(sequence - 1),
        )
        agent.inner.set_attr(episode, "action_ready", 0.0)
        agent.inner.set_attr(episode, "motor_primary_ready", 1.0)
        agent.inner.set_attr(
            episode,
            "last_compound_decision_count",
            decision_count - float(
                agent.s.node(episode)["attrs"][
                    "compound_response_interval"
                ]
            ),
        )
        agent.tick()
        return [
            trial
            for trial in agent.inner.neighbours(
                episode,
                "has_humanoid_motor_trial",
            )
            if agent.s.node(trial)["attrs"]["request_seq"]
            == float(sequence)
        ][0]

    first = request(2)
    _verified_outcome(agent, first)
    assert agent.inner.neighbours(
        episode,
        "last_verified_humanoid_motor_program",
    ) == [program]

    next_program = agent.s.add_node("HumanoidMotorProgram", {
        **agent.s.node(program)["attrs"],
        "request_seq": 2.0,
        "ordinal": 2.0,
        "primary_token": "motor_b",
        "mean_dvx": 1.0,
        "mean_rate_dvx": 0.2,
        "experience_count": 1.0,
        "recall_count": 0.0,
        "last_recall_request_seq": 0.0,
        "last_memory_update_request_seq": 0.0,
    })
    _edge(
        agent,
        episode,
        "has_humanoid_motor_program",
        next_program,
    )
    for member in agent.inner.neighbours(
        program,
        "includes_humanoid_phase_action_model",
    ):
        _edge(
            agent,
            next_program,
            "includes_humanoid_phase_action_model",
            member,
        )

    agent.inner.set_attr(program, "memory_eligible", 0.0)
    second = request(3)
    assert agent.inner.neighbours(
        second,
        "enacts_humanoid_motor_program",
    ) == [next_program]
    assert agent.s.node(second)["attrs"].get(
        "motor_sequence_recalled",
        0.0,
    ) == 0.0
    _verified_outcome(agent, second, post_vx=1.4)

    transitions = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_transition",
    )
    assert len(transitions) == 1
    transition = transitions[0]
    assert agent.inner.neighbours(
        program,
        "has_humanoid_motor_transition",
    ) == [transition]
    assert agent.inner.neighbours(
        transition,
        "continues_with_humanoid_motor_program",
    ) == [next_program]
    assert agent.s.node(transition)["attrs"]["experience_count"] == 1.0

    agent.inner.set_attr(program, "memory_eligible", 1.0)
    agent.inner.set_attr(next_program, "memory_eligible", 0.0)
    agent.inner.set_attr(episode, "state_vx", 0.28)
    third = request(4)
    assert agent.inner.neighbours(
        third,
        "enacts_humanoid_motor_program",
    ) == [program]
    assert agent.s.node(third)["attrs"].get(
        "motor_sequence_recalled",
        0.0,
    ) == 0.0
    _verified_outcome(agent, third)

    assert len(agent.inner.neighbours(
        episode,
        "has_humanoid_motor_transition",
    )) == 2

    # Re-observe this exact successor under an explicit intervention so the
    # transition receives an out-of-sample prediction-error measurement.
    agent.inner.set_attr(program, "memory_eligible", 0.0)
    agent.inner.set_attr(next_program, "memory_eligible", 1.0)
    agent.inner.set_attr(episode, "state_vx", 0.0)
    fourth = request(5)
    trial_attrs = agent.s.node(fourth)["attrs"]
    assert agent.inner.neighbours(
        fourth,
        "enacts_humanoid_motor_program",
    ) == [next_program]
    assert trial_attrs.get("motor_sequence_recalled", 0.0) == 0.0
    _verified_outcome(agent, fourth, post_vx=1.0)
    transition_attrs = agent.s.node(transition)["attrs"]
    assert transition_attrs["experience_count"] == 2.0
    assert transition_attrs["prediction_error_measured"] == 1.0
    assert transition_attrs["mean_dvx"] == pytest.approx(1.2)
    assert transition_attrs["mean_prediction_error_energy"] > 0.0
    assert transition_attrs["response_frames"] < 5.0

    agent.inner.set_attr(program, "memory_eligible", 1.0)
    agent.inner.set_attr(next_program, "memory_eligible", 0.0)
    agent.inner.set_attr(episode, "state_vx", 0.28)
    return_trial = request(6)
    assert agent.inner.neighbours(
        return_trial,
        "enacts_humanoid_motor_program",
    ) == [program]
    assert agent.s.node(return_trial)["attrs"].get(
        "motor_sequence_recalled",
        0.0,
    ) == 0.0
    _verified_outcome(agent, return_trial)

    agent.inner.set_attr(next_program, "memory_eligible", 1.0)
    agent.inner.set_attr(episode, "state_vx", 0.0)
    recalled = request(7)
    trial_attrs = agent.s.node(recalled)["attrs"]
    assert agent.inner.neighbours(
        recalled,
        "enacts_humanoid_motor_program",
    ) == [next_program]
    assert trial_attrs["motor_sequence_recalled"] == 1.0
    sequence_preparation = agent.inner.neighbours(
        recalled,
        "released_from_humanoid_motor_preparation",
    )
    assert len(sequence_preparation) == 1
    assert agent.s.node(sequence_preparation[0])["attrs"][
        "preparation_kind"
    ] == "sequence"
    assert agent.inner.neighbours(
        recalled,
        "enacts_humanoid_motor_transition",
    ) == [transition]
    transition_before = agent.s.node(transition)["attrs"]
    assert trial_attrs["predicted_dvx"] == pytest.approx(
        transition_before["mean_rate_dvx"]
        * trial_attrs["response_frames"]
    )
    assert agent.s.node(episode)["attrs"][
        "motor_sequence_recall_count"
    ] == 1.0
    assert agent.s.node(transition)["attrs"]["recall_count"] == 1.0

    unsafe_transition = agent.inner.neighbours(
        recalled,
        "enacts_humanoid_motor_transition",
    )[0]
    _verified_outcome(agent, recalled, post_z=0.2)

    assert agent.s.node(unsafe_transition)["attrs"][
        "memory_eligible"
    ] == 0.0
    assert agent.inner.neighbours(
        episode,
        "last_verified_humanoid_motor_program",
    ) == []


def test_verified_takeoff_stage_fires_from_support_without_token_identity():
    agent, episode = _inverse_control_fixture()
    memory = _ground_singleton_program(agent, episode)
    memory_token = agent.s.node(memory)["attrs"]["primary_token"]
    for key, value in {
        "motor_task_context": "self_takeoff",
        "trajectory_verified": 1.0,
        "warm_start_requires_verification": 1.0,
        "warm_start_verified": 1.0,
    }.items():
        agent.inner.set_attr(memory, key, value)

    for key, value in {
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 0.0,
        "motor_primary_ready": 1.0,
        "self_takeoff_drive_active": 1.0,
        "self_takeoff_compression_scale": 0.0,
        "selected_primary_token": "not_the_stage",
        "motor_memory_recall_count": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)
    agent.tick()

    preparations = [
        preparation
        for preparation in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_preparation",
        )
        if agent.s.node(preparation)["attrs"]["preparation_kind"]
        == "takeoff_stage"
    ]
    assert len(preparations) == 1
    assert agent.s.node(preparations[0])["attrs"]["status"] \
        == "output_potent"
    assert agent.s.node(episode)["attrs"]["decision_kind"] \
        == "learned_takeoff_stage"
    assert agent.s.node(episode)["attrs"]["selected_token"] == memory_token
    assert agent.s.node(episode)["attrs"]["motor_memory_recall_count"] == 1.0
    trials = [
        trial
        for trial in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(trial)["attrs"]["request_seq"] == 2.0
    ]
    assert len(trials) == 1
    assert agent.inner.neighbours(
        trials[0],
        "enacts_humanoid_motor_program",
    ) == [memory]
    assert agent.s.node(trials[0])["attrs"]["decision_kind"] \
        == "learned_takeoff_stage"


def test_takeoff_schema_root_inherits_duration_from_verified_temporal_edge():
    agent, episode = _inverse_control_fixture()
    memory = _ground_singleton_program(agent, episode)
    for key, value in {
        "motor_task_context": "self_takeoff",
        "trajectory_verified": 1.0,
        "jump_schema_id": 41.0,
        "response_frames": 0.0,
        "warm_start_requires_verification": 1.0,
        "warm_start_verified": 1.0,
    }.items():
        agent.inner.set_attr(memory, key, value)
    transition = agent.s.add_node("HumanoidMotorTransition", {
        "status": "grounded",
        "memory_eligible": 1.0,
        "trajectory_verified": 1.0,
        "jump_schema_id": 41.0,
        "response_frames": 7.0,
        "ordinal": 2.0,
    })
    _edge(agent, memory, "has_humanoid_motor_transition", transition)

    for key, value in {
        "request_seq": 2.0,
        "last_trial_request_seq": 1.0,
        "action_ready": 0.0,
        "motor_primary_ready": 1.0,
        "self_takeoff_drive_active": 1.0,
        "self_takeoff_compression_scale": 0.0,
        "selected_primary_token": "not_the_stage",
        "motor_memory_recall_count": 0.0,
    }.items():
        agent.inner.set_attr(episode, key, value)
    agent.tick()

    preparations = [
        preparation
        for preparation in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_preparation",
        )
        if agent.s.node(preparation)["attrs"]["preparation_kind"]
        == "takeoff_stage"
    ]
    assert len(preparations) == 1
    assert agent.s.node(preparations[0])["attrs"]["status"] \
        == "output_potent"
    assert agent.s.node(transition)["attrs"]["response_frames"] == 7.0
    assert agent.s.node(episode)["attrs"]["selected_response_frames"] == 1.0
    trials = [
        trial
        for trial in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_trial",
        )
        if agent.s.node(trial)["attrs"]["request_seq"] == 2.0
    ]
    assert len(trials) == 1
    assert agent.inner.neighbours(
        trials[0],
        "enacts_humanoid_motor_program",
    ) == [memory]
