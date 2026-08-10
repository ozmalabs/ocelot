from __future__ import annotations

import importlib.util
import inspect
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocols" / "humanoid_walking_v1.json"
RUNNER = ROOT / "scripts" / "jabberwock_humanoid_walk.py"
GENERATOR = ROOT / "scripts" / "gen_humanoid_adaptation_seed.py"
SEED = ROOT / "seeds" / "humanoid_adaptation.json"


def _rule(seed: dict, name: str) -> dict:
    return next(rule for rule in seed["rules"] if rule["name"] == name)


def test_post_sweep_pareto_choice_focuses_one_context_dimension():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    policy = next(
        node for node in seed["nodes"] if node["type"] == "HumanoidPolicy"
    )["attrs"]
    chooser = json.dumps(
        _rule(seed, "ha_select_pareto_persistent_residual_regime")
    )
    assert "without scalarizing" in chooser
    assert "mean_directed_step" in chooser
    assert "mean_abs_lateral_step" in chooser
    assert "mean_tilt" in chooser
    assert "mean_normalized_energy" in chooser
    assert not any("preference" in key for key in policy)


def test_recovery_is_a_first_class_pareto_process_not_a_scalar_score():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    learner = json.dumps(
        _rule(seed, "ha_learn_situated_recovery_basin_action")
    )
    promoter = json.dumps(
        _rule(seed, "ha_promote_receipt_confirmed_recovery_basin")
    )
    combined = learner + promoter
    for dimension in (
        "mean_height_gain",
        "mean_alignment_gain",
        "mean_support_gain",
        "mean_contact_gain",
        "mean_motion_reduction",
        "mean_normalized_energy",
        "mean_normalized_peak_load",
    ):
        assert dimension in combined
    assert "non-dominated" in promoter
    assert "state_score" not in json.dumps(seed)
    assert "get_up_score" not in json.dumps(seed)

    runner = RUNNER.read_text(encoding="utf-8")
    assert 'context="humanoid_recovery_basin"' in runner
    assert 'attrs["pareto_frontier"]' in runner
    assert 'attrs["dominated_by"]' in runner


def test_warm_repertoire_cannot_buy_authority_with_a_fall():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    storage = json.dumps(
        _rule(seed, "ha_store_grounded_program_by_body_shape")
    )
    assert "walking_minimum_height" in storage
    assert "minimum_upright_height_fraction" in storage
    assert "best_directed_progress" in storage


def test_walking_objective_and_measurement_are_graph_native():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    chooser = json.dumps(
        _rule(seed, "ha_choose_learned_walking_twitch")
    )
    synthesizer = json.dumps(
        _rule(seed, "ha_abs_expand_motor_program")
    )
    native_synthesizer = json.dumps(
        _rule(seed, "ha_native_expand_motor_program")
    )
    program_trial = json.dumps(
        _rule(seed, "ha_open_synthesized_motor_program_trial")
    )
    program_learner = json.dumps(
        _rule(seed, "ha_ground_synthesized_motor_program_from_receipt")
    )
    pair_program_learner = json.dumps(
        _rule(seed, "ha_learn_identifiable_pair_program_residual")
    )
    memory_recaller = json.dumps(
        _rule(seed, "ha_reassociate_grounded_motor_memory")
    )
    memory_release = json.dumps(
        _rule(seed, "ha_release_prepared_motor_memory")
    )
    memory_trial = json.dumps(
        _rule(seed, "ha_open_reassociated_motor_memory_trial")
    )
    memory_learner = json.dumps(
        _rule(seed, "ha_update_reassociated_motor_memory")
    )
    sequence_recaller = json.dumps(
        _rule(seed, "ha_advance_grounded_motor_sequence")
    )
    sequence_release = json.dumps(
        _rule(seed, "ha_release_prepared_motor_sequence")
    )
    sequence_trial = json.dumps(
        _rule(seed, "ha_open_receipt_advanced_motor_sequence_trial")
    )
    sequence_learner = json.dumps(
        _rule(seed, "ha_consolidate_motor_sequence_transition")
    )
    sequence_updater = json.dumps(
        _rule(seed, "ha_update_grounded_motor_sequence_transition")
    )
    sequence_invalidator = json.dumps(
        _rule(seed, "ha_invalidate_unsafe_motor_sequence_transition")
    )
    primary_chooser = json.dumps(
        _rule(seed, "ha_select_learned_walking_primary")
    )
    horizon_initializer = json.dumps(
        _rule(seed, "ha_initialize_body_scaled_response_horizon")
    )
    horizon_tuner = json.dumps(
        _rule(seed, "ha_tune_response_horizon_from_prediction_receipt")
    )
    topology_horizon = json.dumps(
        _rule(seed, "ha_focus_topology_sensitive_response_horizon")
    )
    compound_tuner = json.dumps(
        _rule(seed, "ha_tune_compound_movement_interval")
    )
    measurement = json.dumps(
        _rule(seed, "ha_measure_directed_locomotion_and_support")
    )
    phase_initializer = json.dumps(
        _rule(seed, "ha_initialize_support_phase_action_model")
    )
    phase_learner = json.dumps(
        _rule(seed, "ha_learn_support_phase_consequence_online")
    )
    phase_closer = json.dumps(
        _rule(seed, "ha_close_phase_adaptation_after_alphabet_quiet")
    )
    prediction_error = json.dumps(
        _rule(seed, "ha_measure_gait_prediction_error_and_interrupt")
    )
    recovery = json.dumps(
        _rule(seed, "ha_select_gait_recovery_primary")
    )
    recovery_entry = json.dumps(
        _rule(seed, "ha_account_recovery_mode_entry")
    )
    recovery_exit = json.dumps(
        _rule(seed, "ha_exit_gait_recovery_inside_learned_envelope")
    )

    assert '"type": "Argmin"' in primary_chooser
    assert "target_froude_speed" in primary_chooser
    assert "mean_dvx" in primary_chooser
    assert "standing_reference_z" in primary_chooser
    assert '"type": "Sqrt"' in primary_chooser
    assert "HumanoidMotorProgram" in chooser
    assert "has_active_humanoid_motor_program" in chooser
    assert "compound_response_interval" in chooser
    assert '"type": "Argmin"' in synthesizer
    assert "actuator_group" in synthesizer
    assert "includes_humanoid_phase_action_model" in synthesizer
    assert "resumes_humanoid_motor_program" in synthesizer
    assert "lateral_offset" in synthesizer
    assert "standing_reference_z" in synthesizer
    assert "gravity_acceleration" in synthesizer
    assert '"type": "MotorCompose"' in native_synthesizer
    assert "takeoff_motor_compression_authority" in json.dumps(seed)
    assert "mean_input_energy_joules" in GENERATOR.read_text(encoding="utf-8")
    assert "native_humanoid_composition_enabled" in native_synthesizer
    assert _rule(seed, "ha_native_expand_motor_program")["batch"] is True
    assert any(
        node["attrs"].get("native_humanoid_composition_enabled") == 1.0
        for node in seed["nodes"]
        if node["type"] == "HumanoidPolicy"
    )
    assert "enacts_humanoid_motor_program" in program_trial
    assert "bundle_member_count" in program_trial
    assert "residual_dvy" in program_learner
    assert "member_count" in pair_program_learner
    assert "experience_count" in pair_program_learner
    assert "last_program_update_request_seq" in pair_program_learner
    assert '"type": "Argmin"' in memory_recaller
    assert "memory_eligible" in memory_recaller
    assert "HumanoidMotorPreparation" in memory_recaller
    assert "indirect_path_cost" in memory_recaller
    assert "mean_prediction_error_energy" in memory_recaller
    assert "mean_lateral_prediction_error_energy" in memory_recaller
    assert "mean_rate_dvx" in memory_recaller
    assert "recalls_humanoid_motor_program" in memory_release
    assert "output_potent" in memory_release
    assert "mean_dvx" in memory_recaller
    assert "lateral_offset" in memory_recaller
    assert "motor_memory_recalled" in memory_trial
    assert "enacts_humanoid_motor_program" in memory_trial
    assert "experience_count" in memory_learner
    assert "last_memory_update_request_seq" in memory_learner
    assert '"type": "Argmin"' in sequence_recaller
    assert "last_verified_humanoid_motor_program" in sequence_recaller
    assert "prepares_humanoid_motor_transition" in sequence_recaller
    assert "recalls_humanoid_motor_transition" in sequence_release
    assert "motor_sequence_recall_count" in sequence_release
    assert "indirect_path_cost" in sequence_recaller
    assert "motor_sequence_recalled" in sequence_trial
    assert "enacts_humanoid_motor_transition" in sequence_trial
    assert "continues_with_humanoid_motor_program" in sequence_learner
    assert "last_motor_sequence_receipt_seq" in sequence_learner
    assert "experience_count" in sequence_updater
    assert "last_update_request_seq" in sequence_updater
    assert "mean_prediction_error_energy" in sequence_updater
    assert "mean_lateral_prediction_error_energy" in sequence_updater
    assert "mean_rate_dvx" in sequence_updater
    assert "response_frames" in sequence_updater
    assert "memory_eligible" in sequence_invalidator
    assert "last_verified_humanoid_motor_program" in (
        sequence_invalidator
    )
    assert "physics_time_step" in horizon_initializer
    assert "self_takeoff_drive_active" in topology_horizon
    assert "selected_predicted_dvz" in topology_horizon
    assert "topology_focused_response_count" in topology_horizon
    assert "nominal_response_frames" in horizon_initializer
    assert '"type": "IDiv"' in horizon_initializer
    assert "response_frames" in horizon_tuner
    assert "prediction_error_measured" in horizon_tuner
    assert "compound_interval_tuned" in compound_tuner
    assert "learned_gait_prediction_error_envelope" in compound_tuner
    assert "support_alternations" in measurement
    assert "aerial_samples" in measurement
    assert "maximum_directed_progress" in measurement
    assert "maximum_lateral_excursion" in measurement
    assert '"type": "Not"' in measurement
    assert "support_phase_prior_strength" in phase_initializer
    assert "mean_dvy" in phase_learner
    assert '"type": "Lt"' in phase_learner
    assert "last_update_request_seq" in phase_learner
    assert "has_humanoid_phase_action_model" in phase_closer
    assert '"type": "Count"' in phase_closer
    assert "learned_gait_prediction_error_envelope" in phase_closer
    assert "learned_gait_mean_tilt" in phase_closer
    assert "has_humanoid_transition" in prediction_error
    assert "predicted_dvz" in prediction_error
    assert "gait_surprise_confirmation_receipts" in prediction_error
    assert "learned_gait_tilt_envelope" in prediction_error
    assert "learned_gait_mean_tilt" in prediction_error
    assert '"type": "Sqrt"' in prediction_error
    assert "mean_dwx" in primary_chooser
    assert "selected_primary_token" in recovery
    assert "motor_primary_ready" in recovery
    assert "compound_recovery_locomotion" in chooser
    assert "open_residual_count" in chooser
    assert "recovery_mode_entries" in recovery_entry
    assert "recovery_entry_open" in recovery_entry
    assert "learned_gait_tilt_envelope" in recovery_exit
    assert "state_vz" in recovery_exit
    assert "recovery_mode_exits" in recovery_exit


def test_retained_motor_history_is_not_a_pairwise_join_tax():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    linker = _rule(seed, "ha_link_compound_trial_to_synergy_model")
    pair_learner = _rule(seed, "ha_learn_identifiable_pair_program_residual")

    assert linker["index_hints"] == [{
        "for_var": "synergy",
        "via_var": "trial",
        "via_key": "token",
        "node_type": "HumanoidSynergyModel",
        "this_key": "token_a",
    }]
    assert pair_learner["index_hints"] == [{
        "for_var": "synergy",
        "via_var": "first",
        "via_key": "token",
        "node_type": "HumanoidSynergyModel",
        "this_key": "token_a",
    }]
    linker_guard = json.dumps(linker["where"])
    assert '"key": "status"' in linker_guard
    assert '"value": "issued"' in linker_guard


def test_motor_library_reuses_existing_shape_decode_machinery():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    recognition = json.dumps(
        _rule(seed, "ha_recognize_held_body_shape")
    )
    novelty = json.dumps(_rule(seed, "ha_mint_novel_body_shape"))
    activation = json.dumps(
        _rule(seed, "ha_activate_shape_matched_motor_program")
    )
    binding = json.dumps(
        _rule(seed, "ha_bind_warm_motor_program_member")
    )
    withdrawal = json.dumps(
        _rule(seed, "ha_withdraw_unsafe_program_from_body_shape_library")
    )
    program_identity = json.dumps(
        _rule(seed, "ha_shape_decode_duplicate_library_motor_program")
    )

    assert '"type": "ShapeDecode"' in recognition
    assert '"type": "ShapeDecode"' in program_identity
    assert '"codebook_type": "HumanoidMotorProgram"' in program_identity
    assert "stores_duplicate_humanoid_motor_program" in program_identity
    assert '"codebook_type": "HumanoidBodyShapeSignature"' in recognition
    assert '"type": "SetT"' in recognition
    assert "body_shape_signature" in recognition
    assert "body_shape_signature" in novelty
    assert "includes_humanoid_phase_action_model" in binding
    assert "has_humanoid_motor_program" in activation
    assert "memory_eligible" in activation
    assert "warm_start_requires_verification" in activation
    assert "stores_humanoid_motor_program" in withdrawal
    assert '"del_edge"' in withdrawal


def _motor_library_fixture(signature):
    from scripts.jabberwock_humanoid_adaptation import _edge
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "body_shape_signature": signature,
        "body_shape_name": "current_shape",
        "body_shape_initialized": 0.0,
        "warm_start_shape_recognized": 0.0,
        "warm_start_program_count": 0.0,
        "physics_time_step": 0.01,
        "gravity_acceleration": 9.81,
        "joint_twitch_radians": 0.1,
        "maximum_joint_force": 1.0,
        "position_gain": 0.2,
        "velocity_gain": 0.3,
        "standing_reference_z": 1.0,
    })
    _edge(agent, agent.agent, "has_humanoid_episode", episode)
    for ordinal, token in enumerate(("opaque_a", "opaque_b")):
        action_model = agent.s.add_node(
            "HumanoidActionModel",
            {"token": token},
        )
        phase_model = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": token,
            "ordinal": float(ordinal),
            "support_phase": 0.0,
        })
        _edge(
            agent,
            episode,
            "has_humanoid_action_model",
            action_model,
        )
        _edge(
            agent,
            episode,
            "has_humanoid_phase_action_model",
            phase_model,
        )
        _edge(
            agent,
            phase_model,
            "generalizes_humanoid_action_model",
            action_model,
        )
    return agent, episode


def _held_motor_library(signature):
    return {
        "version": 3,
        "body_shapes": [{
            "attrs": {
                "name": "held_shape",
                "signature": signature,
                "physics_time_step": 0.01,
                "gravity_acceleration": 9.81,
                "joint_twitch_radians": 0.1,
                "maximum_joint_force": 1.0,
                "position_gain": 0.2,
                "velocity_gain": 0.3,
            },
            "programs": [{
                "attrs": {
                    "ordinal": 5.0,
                    "status": "grounded",
                    "memory_eligible": 1.0,
                    "member_count": 2.0,
                    "primary_token": "opaque_a",
                    "primary_context_id": 0.0,
                    "support_phase": 0.0,
                    "experience_count": 4.0,
                    "mean_directed_advance": 0.1,
                    "last_memory_update_request_seq": 100.0,
                    "last_recall_request_seq": 100.0,
                    "library_consolidation_seq": 1.0,
                },
                "members": [
                    {
                        "token": "opaque_a",
                        "ordinal": 0.0,
                        "support_phase": 0.0,
                    },
                    {
                        "token": "opaque_b",
                        "ordinal": 1.0,
                        "support_phase": 0.0,
                    },
                ],
            }],
        }],
    }


def test_shape_library_persists_gait_sweep_between_lifetimes():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    rules = {rule["name"] for rule in seed["rules"]}
    assert {
        "ha_restore_shape_indexed_residual_regime_memory",
        "ha_mint_shape_indexed_residual_regime_memory",
        "ha_update_shape_indexed_residual_regime_memory",
    } <= rules
    production_edges = {
        production["edge_type"] for production in seed["productions"]
    }
    assert "stores_humanoid_residual_regime_memory" in production_edges

    runner = RUNNER.read_text(encoding="utf-8")
    assert "MOTOR_LIBRARY_VERSION = 12" in runner
    assert 'shape_row.get("residual_regimes", [])' in runner
    assert '"residual_regimes": residual_regimes' in runner


def test_shape_library_round_trips_receipt_positive_recovery_basins():
    from scripts.jabberwock_humanoid_adaptation import _edge
    from scripts.jabberwock_humanoid_walk import (
        _motor_library_snapshot,
        _request_motor_library_consolidation,
        _restore_motor_library,
    )

    signature = (
        ("body", 3, 2, 1),
        ("joint", 0, -1, 1, 0, 0),
        ("support", 0, 1),
    )
    agent, episode = _motor_library_fixture(signature)
    agent.tick()
    basin = agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 1.0,
        "status": "situated",
        "normalized_height": 0.4,
        "vertical_alignment": 0.2,
    })
    action = agent.s.add_node("HumanoidRecoveryBasinAction", {
        "primary_token": "opaque_a",
        "secondary_token": "opaque_b",
        "primary_actuator_group": 0.0,
        "secondary_actuator_group": 1.0,
        "member_count": 2.0,
        "experience_count": 2.0,
        "mean_height_gain": 0.2,
        "mean_alignment_gain": 0.1,
        "mean_support_gain": 0.0,
        "mean_contact_gain": 0.0,
        "mean_motion_reduction": 0.0,
        "mean_normalized_energy": 0.1,
        "mean_normalized_peak_load": 0.1,
        "response_frames": 8.0,
    })
    successor = agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 2.0,
        "status": "situated",
        "normalized_height": 0.7,
        "vertical_alignment": 0.5,
    })
    successor_action = agent.s.add_node("HumanoidRecoveryBasinAction", {
        "primary_token": "opaque_b",
        "secondary_token": "opaque_b",
        "primary_actuator_group": 1.0,
        "secondary_actuator_group": 1.0,
        "member_count": 1.0,
        "experience_count": 1.0,
        "mean_height_gain": 0.1,
        "mean_alignment_gain": 0.0,
        "mean_support_gain": 1.0,
        "mean_contact_gain": 0.0,
        "mean_motion_reduction": 0.0,
        "mean_normalized_energy": 0.1,
        "mean_normalized_peak_load": 0.1,
        "response_frames": 8.0,
    })
    _edge(agent, episode, "has_humanoid_recovery_basin", basin)
    _edge(agent, episode, "has_humanoid_recovery_basin", successor)
    _edge(
        agent,
        basin,
        "has_humanoid_recovery_basin_action",
        action,
    )
    _edge(
        agent,
        successor,
        "has_humanoid_recovery_basin_action",
        successor_action,
    )
    _edge(
        agent,
        basin,
        "continues_to_humanoid_recovery_basin",
        successor,
    )

    _request_motor_library_consolidation(agent, episode)
    snapshot = _motor_library_snapshot(agent)
    saved = snapshot["body_shapes"][0]["recovery_basins"]
    assert len(saved) == 2
    assert saved[0]["actions"][0]["primary_token"] == "opaque_a"
    assert saved[0]["successor_slots"] == [1]
    assert saved[1]["successor_slots"] == []

    restored_agent, restored_episode = _motor_library_fixture(signature)
    restored = _restore_motor_library(restored_agent, snapshot)
    assert restored["recovery_basin_count"] == 2
    assert restored["recovery_basin_action_count"] == 2
    shape = restored_agent.inner.neighbours(
        restored_agent.agent,
        "has_humanoid_body_shape_library",
    )[0]
    restored_basins = restored_agent.inner.neighbours(
        shape,
        "stores_humanoid_recovery_basin",
    )
    assert len(restored_basins) == 2
    restored_basins.sort(
        key=lambda node: restored_agent.s.node(node)["attrs"]["ordinal"]
    )
    assert len(restored_agent.inner.neighbours(
        restored_basins[0],
        "has_humanoid_recovery_basin_action",
    )) == 1
    assert restored_agent.inner.neighbours(
        restored_basins[0],
        "continues_to_humanoid_recovery_basin",
    ) == [restored_basins[1]]

    live_duplicates = []
    for restored_basin in restored_basins:
        duplicate = restored_agent.s.add_node(
            "HumanoidRecoveryBasin",
            {
                **restored_agent.s.node(restored_basin)["attrs"],
                "source": "experience",
            },
        )
        _edge(
            restored_agent,
            shape,
            "stores_humanoid_recovery_basin",
            duplicate,
        )
        for restored_action in restored_agent.inner.neighbours(
            restored_basin,
            "has_humanoid_recovery_basin_action",
        ):
            duplicate_action = restored_agent.s.add_node(
                "HumanoidRecoveryBasinAction",
                dict(restored_agent.s.node(restored_action)["attrs"]),
            )
            _edge(
                restored_agent,
                duplicate,
                "has_humanoid_recovery_basin_action",
                duplicate_action,
            )
        live_duplicates.append(duplicate)
    _edge(
        restored_agent,
        live_duplicates[0],
        "continues_to_humanoid_recovery_basin",
        live_duplicates[1],
    )
    deduplicated = _motor_library_snapshot(restored_agent)
    deduplicated_basins = deduplicated["body_shapes"][0]["recovery_basins"]
    assert len(deduplicated_basins) == 2
    assert deduplicated_basins[0]["successor_slots"] == [1]

    restored_agent.tick()
    current = restored_agent.s.add_node("HumanoidRecoveryBasin", {
        "ordinal": 1.0,
        "status": "situated",
        "warm_start_tested": 1.0,
    })
    _edge(
        restored_agent,
        restored_episode,
        "has_humanoid_recovery_basin",
        current,
    )
    _edge(
        restored_agent,
        restored_episode,
        "has_current_humanoid_recovery_basin",
        current,
    )
    for key, value in {
        "phase": "locomotion",
        "recovery_mode": 1.0,
        "upright": 0.0,
        "state_z": 0.42,
        "state_qx": 0.0,
        "state_qy": 0.0,
        "state_qz": 0.0,
        "state_qw": 1.0,
        "state_wx": 0.0,
        "state_wy": 0.0,
        "state_vx": 0.0,
        "state_vy": 0.0,
        "active_support_count": 1.0,
        "request_seq": 1.0,
        "last_trial_request_seq": 0.0,
        "action_ready": 0.0,
        "reset_requested": 0.0,
        "get_up_attempt_count": 0.0,
        "get_up_last_improvement_attempt": 0.0,
        "get_up_exploitation_start_attempt": 0.0,
        "recovery_basin_start_attempt": 0.0,
        "recovery_action_count": 0.0,
        "recovery_warm_start_count": 0.0,
    }.items():
        restored_agent.inner.set_attr(restored_episode, key, value)
    restored_agent.tick()
    inherited = restored_agent.inner.neighbours(
        current,
        "inherits_humanoid_recovery_actions_from",
    )
    assert len(inherited) == 1
    assert inherited[0] in restored_basins
    assert restored_agent.s.node(restored_episode)["attrs"][
        "recovery_warm_start_count"
    ] == 1.0


def test_shape_matched_library_warm_starts_without_host_actuator_mapping():
    from scripts.jabberwock_humanoid_walk import (
        _motor_library_snapshot,
        _request_motor_library_consolidation,
        _restore_motor_library,
    )

    signature = (
        ("body", 3, 2, 1),
        ("joint", 0, -1, 1, 0, 0),
        ("joint", 1, 0, 0, 1, 0),
        ("support", 0, 1),
    )
    agent, episode = _motor_library_fixture(signature)
    restored = _restore_motor_library(
        agent,
        _held_motor_library(signature),
    )
    agent.tick()

    episode_attrs = agent.s.node(episode)["attrs"]
    programs = agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )
    assert restored == {"shape_count": 1, "program_count": 1}
    assert episode_attrs["warm_start_shape_recognized"] == 1.0
    assert episode_attrs["warm_start_program_count"] == 1.0
    assert len(programs) == 1
    assert agent.s.node(programs[0])["attrs"][
        "last_memory_update_request_seq"
    ] == 0.0
    assert agent.s.node(programs[0])["attrs"][
        "last_recall_request_seq"
    ] == 0.0
    assert agent.s.node(programs[0])["attrs"][
        "library_consolidation_seq"
    ] == 0.0
    assert len(agent.inner.neighbours(
        programs[0],
        "includes_humanoid_phase_action_model",
    )) == 2
    agent.inner.set_attr(programs[0], "experience_count", 9.0)
    _request_motor_library_consolidation(agent, episode)
    assert agent.s.node(programs[0])["attrs"]["experience_count"] == 4.0
    snapshot = _motor_library_snapshot(agent)
    assert len(snapshot["body_shapes"]) == 1
    assert len(snapshot["body_shapes"][0]["programs"]) == 1


def test_shape_mismatch_mints_new_shape_and_withholds_warm_program():
    from scripts.jabberwock_humanoid_walk import _restore_motor_library

    held_signature = (("body", 3, 2, 1),)
    novel_signature = (("body", 4, 3, 1),)
    agent, episode = _motor_library_fixture(novel_signature)
    _restore_motor_library(
        agent,
        _held_motor_library(held_signature),
    )
    agent.tick()

    episode_attrs = agent.s.node(episode)["attrs"]
    recognized = agent.inner.neighbours(
        episode,
        "recognizes_humanoid_body_shape",
    )
    assert episode_attrs["warm_start_shape_recognized"] == 0.0
    assert episode_attrs["warm_start_program_count"] == 0.0
    assert not agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )
    assert len(recognized) == 1
    assert agent.s.node(recognized[0])["attrs"]["signature"] == (
        novel_signature
    )


def test_shape_library_persists_safe_coordinated_programs_not_singletons():
    from scripts.jabberwock_humanoid_adaptation import _edge
    from scripts.jabberwock_humanoid_walk import (
        _motor_library_snapshot,
        _request_motor_library_consolidation,
    )

    signature = (
        ("body", 3, 2, 1),
        ("joint", 0, -1, 1, 0, 0),
        ("support", 0, 1),
    )
    agent, episode = _motor_library_fixture(signature)
    agent.tick()
    shape = agent.inner.neighbours(
        episode,
        "recognizes_humanoid_body_shape",
    )[0]
    phase_models = agent.inner.neighbours(
        episode,
        "has_humanoid_phase_action_model",
    )
    program = agent.s.add_node("HumanoidMotorProgram", {
        "ordinal": 1.0,
        "status": "grounded",
        "memory_eligible": 1.0,
        "member_count": 2.0,
        "primary_token": "opaque_a",
        "support_phase": 0.0,
        "experience_count": 8.0,
        "recall_count": 1.0,
        "lifetime_recall_count": 1.0,
        "mean_directed_advance": 0.1,
        "receipt_learned": 1.0,
    })
    _edge(
        agent,
        episode,
        "has_humanoid_motor_program",
        program,
    )
    _edge(
        agent,
        program,
        "includes_humanoid_phase_action_model",
        phase_models[0],
    )
    _edge(
        agent,
        program,
        "includes_humanoid_phase_action_model",
        phase_models[1],
    )

    agent.tick()

    assert agent.inner.neighbours(
        shape,
        "stores_humanoid_motor_program",
    ) == [program]

    snapshot = _motor_library_snapshot(agent)
    assert snapshot["body_shapes"][0]["programs"][0]["attrs"][
        "member_count"
    ] == 2.0

    singleton = agent.s.add_node("HumanoidMotorProgram", {
        **agent.s.node(program)["attrs"],
        "ordinal": 2.0,
        "member_count": 1.0,
        "primary_token": "opaque_b",
    })
    _edge(
        agent,
        episode,
        "has_humanoid_motor_program",
        singleton,
    )
    _edge(
        agent,
        singleton,
        "includes_humanoid_phase_action_model",
        phase_models[1],
    )
    agent.tick()
    assert agent.inner.neighbours(
        shape,
        "stores_humanoid_motor_program",
    ) == [program]

    _request_motor_library_consolidation(agent, episode)
    assert agent.s.node(program)["attrs"][
        "warm_start_requires_verification"
    ] == 1.0

    agent.inner.set_attr(episode, "warm_start_shape_recognized", 1.0)
    de_novo = agent.s.add_node("HumanoidMotorProgram", {
        **agent.s.node(program)["attrs"],
        "ordinal": 3.0,
        "warm_start_requires_verification": 0.0,
    })
    _edge(
        agent,
        episode,
        "has_humanoid_motor_program",
        de_novo,
    )
    _edge(
        agent,
        de_novo,
        "includes_humanoid_phase_action_model",
        phase_models[0],
    )
    _edge(
        agent,
        de_novo,
        "includes_humanoid_phase_action_model",
        phase_models[1],
    )
    agent.tick()
    assert agent.inner.neighbours(
        shape,
        "stores_humanoid_motor_program",
    ) == [program]


def test_familiar_shape_retains_whole_trajectory_verified_takeoff_endpoint():
    from scripts.jabberwock_humanoid_adaptation import _edge

    signature = (
        ("body", 3, 2, 1),
        ("joint", 0, -1, 1, 0, 0),
        ("support", 0, 1),
    )
    agent, episode = _motor_library_fixture(signature)
    agent.tick()
    shape = agent.inner.neighbours(
        episode,
        "recognizes_humanoid_body_shape",
    )[0]
    agent.inner.set_attr(episode, "warm_start_shape_recognized", 1.0)
    endpoint = agent.s.add_node("HumanoidMotorProgram", {
        "ordinal": 4.0,
        "status": "grounded",
        "memory_eligible": 1.0,
        "member_count": 1.0,
        "receipt_learned": 1.0,
        "primary_token": "opaque_takeoff_endpoint",
        "motor_task_context": "self_takeoff",
        "trajectory_verified": 1.0,
        "jump_schema_id": 20.0,
        "library_slot": 1.0,
        "warm_start_requires_verification": 0.0,
    })
    _edge(agent, episode, "has_humanoid_motor_program", endpoint)

    agent.tick()

    assert agent.inner.neighbours(
        shape,
        "stores_humanoid_motor_program",
    ) == [endpoint]

    duplicate = agent.s.add_node("HumanoidMotorProgram", {
        **agent.s.node(endpoint)["attrs"],
        "primary_token": "duplicate_endpoint",
    })
    _edge(agent, episode, "has_humanoid_motor_program", duplicate)
    agent.tick()
    assert agent.inner.neighbours(
        shape,
        "stores_humanoid_motor_program",
    ) == [endpoint]


def test_verified_singleton_takeoff_endpoint_rebinds_on_familiar_shape():
    from scripts.jabberwock_humanoid_adaptation import _edge

    signature = (
        ("body", 3, 2, 1),
        ("joint", 0, -1, 1, 0, 0),
        ("support", 0, 1),
    )
    agent, episode = _motor_library_fixture(signature)
    agent.tick()
    shape = agent.inner.neighbours(
        episode,
        "recognizes_humanoid_body_shape",
    )[0]
    phase_model = agent.inner.neighbours(
        episode,
        "has_humanoid_phase_action_model",
    )[0]
    model_attrs = agent.s.node(phase_model)["attrs"]
    endpoint = agent.s.add_node("HumanoidMotorProgram", {
        "ordinal": 4.0,
        "status": "library",
        "memory_eligible": 1.0,
        "member_count": 1.0,
        "motor_task_context": "self_takeoff",
        "trajectory_verified": 1.0,
        "jump_schema_id": 20.0,
        "library_slot": 1.0,
    })
    member = agent.s.add_node("HumanoidLibraryMotorMember", {
        "token": model_attrs["token"],
        "ordinal": model_attrs["ordinal"],
        "support_phase": model_attrs["support_phase"],
    })
    duplicate_endpoint = agent.s.add_node("HumanoidMotorProgram", {
        **agent.s.node(endpoint)["attrs"],
        "library_slot": 2.0,
    })
    duplicate_member = agent.s.add_node("HumanoidLibraryMotorMember", {
        **agent.s.node(member)["attrs"],
    })
    _edge(agent, shape, "stores_humanoid_motor_program", endpoint)
    _edge(agent, endpoint, "has_humanoid_library_motor_member", member)
    _edge(agent, shape, "stores_humanoid_motor_program", duplicate_endpoint)
    _edge(
        agent,
        duplicate_endpoint,
        "has_humanoid_library_motor_member",
        duplicate_member,
    )

    agent.tick()

    active_endpoints = [
        node
        for node in agent.inner.neighbours(
            episode,
            "has_humanoid_motor_program",
        )
        if agent.s.node(node)["attrs"].get("jump_schema_id") == 20.0
    ]
    assert len(active_endpoints) == 1
    assert agent.s.node(active_endpoints[0])["attrs"]["status"] == "grounded"
    assert endpoint in agent.inner.neighbours(
        episode,
        "has_humanoid_motor_program",
    )


def test_restored_transition_selects_one_schema_identical_endpoint():
    from scripts.jabberwock_humanoid_adaptation import _edge

    signature = (
        ("body", 3, 2, 1),
        ("joint", 0, -1, 1, 0, 0),
        ("support", 0, 1),
    )
    agent, episode = _motor_library_fixture(signature)
    agent.tick()
    shape = agent.inner.neighbours(
        episode,
        "recognizes_humanoid_body_shape",
    )[0]
    previous = agent.s.add_node("HumanoidMotorProgram", {
        "ordinal": 1.0,
        "status": "grounded",
        "member_count": 2.0,
        "motor_task_context": "self_takeoff",
        "jump_schema_id": 20.0,
    })
    memory = agent.s.add_node("HumanoidMotorProgram", {
        "ordinal": 2.0,
        "status": "grounded",
        "member_count": 1.0,
        "motor_task_context": "self_takeoff",
        "jump_schema_id": 20.0,
    })
    duplicate_memory = agent.s.add_node("HumanoidMotorProgram", {
        **agent.s.node(memory)["attrs"],
    })
    for program in (previous, memory, duplicate_memory):
        _edge(agent, episode, "has_humanoid_motor_program", program)
    transition = agent.s.add_node("HumanoidMotorTransition", {
        "ordinal": 1.0,
        "status": "library",
        "motor_task_context": "self_takeoff",
        "trajectory_verified": 1.0,
        "jump_schema_id": 20.0,
        "from_program_ordinal": 1.0,
        "next_program_ordinal": 2.0,
    })
    _edge(agent, shape, "stores_humanoid_motor_transition", transition)

    agent.tick()

    assert agent.inner.neighbours(
        episode,
        "has_humanoid_motor_transition",
    ) == [transition]
    assert len(agent.inner.neighbours(
        transition,
        "continues_with_humanoid_motor_program",
    )) == 1


def test_motor_interval_is_owned_by_the_graph_not_a_declared_rate():
    from scripts.jabberwock_humanoid_walk import _configuration

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    body = protocol["body"]
    configuration = _configuration(protocol)

    assert "action_frames" not in body
    assert "motor_command_rate_hz" not in body
    assert "adaptation_actions" not in protocol["locomotion"]
    assert "maximum_adaptation_actions" not in protocol["locomotion"]
    assert configuration.action_frames == 1
    generator = GENERATOR.read_text(encoding="utf-8")
    assert "gravity_horizon_frames" in generator
    assert "actuator_dimension" in generator
    assert "motor_command_rate_hz" not in generator


def test_support_sensors_are_discovered_from_loaded_body():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("install requirements-robot.txt")
    from domains.pybullet_humanoid_world import PyBulletHumanoidWorld
    from scripts.jabberwock_humanoid_walk import _configuration

    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    with PyBulletHumanoidWorld(_configuration(protocol)) as world:
        observation = world.observe()
        body_shape = world.body_shape_signature()

    support = observation["support_contact_forces"]
    assert len(support) == 2
    assert tuple(row["ordinal"] for row in support) == (0, 1)
    assert support[0]["link_index"] != support[1]["link_index"]
    assert all(row["normal_force"] > 0.0 for row in support)
    assert all(len(row["world_position"]) == 3 for row in support)
    assert {relation[0] for relation in body_shape} == {
        "body",
        "link",
        "actuator",
        "support",
    }
    assert all(
        isinstance(value, (str, int)) and not isinstance(value, bool)
        for relation in body_shape
        for value in relation
    )


def test_walking_runner_only_enacts_graph_selected_tokens():
    source = RUNNER.read_text(encoding="utf-8")
    run_arm = inspect.getsource(
        __import__(
            "scripts.jabberwock_humanoid_walk",
            fromlist=["_run_arm"],
        )._run_arm
    )

    assert 'seed_names = ["humanoid_adaptation"]' in run_arm
    assert 'seed_names.append("humanoid_coordination_curriculum")' in run_arm
    assert 'seed_names.append("humanoid_kinematics_study")' in run_arm
    assert "WorldAdapter(seeds=tuple(seed_names))" in run_arm
    assert "token, trial, decision = _request_action" in run_arm
    assert "after = _enact_graph_command(world, token, decision)" in run_arm
    assert run_arm.index("token, trial, decision = _request_action") < (
        run_arm.index("world.apply_force_pulse")
    )
    assert '"semantics": "unknown"' in run_arm
    assert '"policy_owner": "rust_graph"' in run_arm
    assert "choose_action" not in source
    assert "min(models" not in source
    assert "correction_cost" not in source
    assert "walking_cost" in GENERATOR.read_text(encoding="utf-8")


def test_motor_experts_and_memories_are_situated_by_configuration_shape():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    source = GENERATOR.read_text(encoding="utf-8")
    specializer = json.dumps(
        _rule(seed, "ha_specialize_surprising_support_phase_context")
    )
    learner = json.dumps(
        _rule(seed, "ha_learn_support_phase_consequence_online")
    )
    chooser = json.dumps(
        _rule(seed, "ha_choose_learned_walking_twitch")
    )

    assert "exact_peers" in source
    assert "eligible_peers" in source
    assert "state_motor_configuration_shape" in source
    assert "pre_motor_configuration_shape" in specializer
    assert "configuration_shape" in learner
    assert "configuration_shape" in chooser
    assert "configuration_shape" in json.dumps(seed["rules"])


def test_stale_phase_predictions_are_receipt_invalidated_and_regrounded():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    linker = json.dumps(
        _rule(seed, "ha_link_walking_trial_to_support_phase_model")
    )
    initializer = json.dumps(
        _rule(seed, "ha_initialize_support_phase_action_model")
    )
    confirmer = _rule(
        seed, "ha_confirm_local_phase_prediction_from_receipt"
    )
    invalidator = _rule(
        seed, "ha_invalidate_stale_local_phase_prediction"
    )
    regrounder = _rule(
        seed, "ha_reground_invalidated_local_phase_prediction"
    )
    selector = json.dumps(
        _rule(seed, "ha_select_learned_walking_primary")
    )
    shared_selector = json.dumps(
        _rule(seed, "ha_prepare_shared_walking_primary")
    )

    assert "evaluation_active" not in linker

    invalidator_text = json.dumps(invalidator)
    confirmer_text = json.dumps(confirmer)
    regrounder_text = json.dumps(regrounder)
    for rendered in (confirmer_text, invalidator_text):
        assert "development_directed_units" in rendered
        assert "predicted_dvx" in rendered
        assert "heading_x" in rendered
        assert "bundle_member_count" in rendered
        assert "receipt_verified" in rendered
        assert "prediction_error" not in rendered
    assert "prediction_authority" in initializer
    assert "prediction_invalidation_count" in initializer
    assert "prediction_authority" in selector
    assert "prediction_invalidation_count" in selector
    assert "prediction_authority" in shared_selector
    assert "prediction_invalidation_count" in shared_selector
    assert invalidator["latency_class"] == "hard_realtime"
    assert invalidator["area"] == "humanoid_sensorimotor_adaptation"
    assert regrounder["latency_class"] == "soft_realtime"
    assert regrounder["area"] == "adaptive_learning"

    # Invalidation has no magnitude tolerance or elapsed-time policy: all its
    # literals are categorical integers and its only epoch comparison proves
    # that this exact receipt has not already been consumed.
    def literals(value):
        if isinstance(value, dict):
            if value.get("type") == "Lit":
                yield value.get("value")
            for nested in value.values():
                yield from literals(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from literals(nested)

    numeric_literals = [
        value for value in literals(invalidator)
        if isinstance(value, (int, float)) and not isinstance(value, bool)
    ]
    assert numeric_literals
    assert all(isinstance(value, int) for value in numeric_literals)
    assert "last_prediction_receipt_seq" in invalidator_text
    assert "invalidated_receipt_seq" in invalidator_text

    # Re-grounding is bounded and in-place: all learned consequence means and
    # context anchors are replaced from the contradictory receipt before
    # authority returns. It does not mint another phase-model population.
    for key in ("dzx", "dzy", "dwx", "dwy", "dvx", "dvy", "dvz"):
        assert f"mean_{key}" in regrounder_text
    for key in ("wx", "wy", "vx", "vy", "vz"):
        assert f"anchor_{key}" in regrounder_text
    assert "last_reground_receipt_seq" in regrounder_text
    assert "prediction_reground_count" in regrounder_text
    assert "HumanoidPhaseActionModel" not in regrounder_text


def test_shared_primary_is_scoped_to_the_request_that_authored_it():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    clear = _rule(seed, "ha_clear_stale_shared_walking_primary")
    builder = _rule(seed, "ha_choose_learned_walking_twitch")
    clear_text = json.dumps(clear)
    builder_text = json.dumps(builder)

    assert "request_seq" in clear_text
    assert "motor_primary_request_seq" in clear_text
    assert "motor_primary_ready" in clear_text
    assert clear["effects"] == [[
        "set_attr", "episode", "motor_primary_ready", 0,
    ]]
    assert "selected_decision_epoch" in builder_text
    assert "selected_option_ref" in builder_text
    assert "motor_primary_request_seq" in builder_text
    assert "shared_motor_collapse_enabled" in builder_text


def test_contradictory_directed_receipt_regrounds_phase_model_once():
    from substrate.world_adapter import WorldAdapter

    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "heading_x": 1,
        "standing_reference_z": 1.0,
        "body_mass": 1.0,
        "request_seq": 1,
        "state_seq": 1,
        "phase": "test",
        "mode": "test",
    })
    agent.inner.add_edge(agent.agent, "has_humanoid_episode", episode)
    model = agent.s.add_node("HumanoidPhaseActionModel", {
        "token": "opaque_actuator",
        "initialized": 1.0,
        "mean_dvx": 0.09,
        "experience_count": 9.0,
        "prediction_authority": 1,
        "prediction_confirmation_count": 0,
        "prediction_invalidation_count": 0,
        "prediction_reground_count": 0,
        "last_prediction_receipt_seq": 0,
        "invalidated_receipt_seq": 0,
        "last_reground_receipt_seq": 0,
    })
    agent.inner.add_edge(
        episode, "has_humanoid_phase_action_model", model
    )
    trial = agent.s.add_node("HumanoidMotorTrial", {
        "decision_kind": "learned_walk",
        "status": "issued",
        "bundle_member_count": 1,
        "request_seq": 1,
        "response_frames": 1.0,
        "model_response_frames": 1.0,
        "predicted_dvx": 0.09,
        "pre_lateral_offset": 0.0,
    })
    agent.inner.add_edge(episode, "has_humanoid_motor_trial", trial)
    agent.inner.add_edge(
        trial, "uses_humanoid_phase_action_model", model
    )
    outcome = agent.s.add_node("HumanoidTransition", {
        "receipt_verified": 1,
        "context_specialized": 0,
        "development_directed_units": 0,
        "input_energy_joules": 0.0,
        "pre_motor_configuration_shape": (),
        "pre_qx": 0.0, "pre_qy": 0.0,
        "pre_qz": 0.0, "pre_qw": 1.0,
        "post_qx": 0.0, "post_qy": 0.0,
        "post_qz": 0.0, "post_qw": 1.0,
        "pre_wx": 0.0, "pre_wy": 0.0,
        "post_wx": 0.0, "post_wy": 0.0,
        "pre_vx": 0.0, "pre_vy": 0.0, "pre_vz": 0.0,
        "post_vx": 0.0, "post_vy": 0.0, "post_vz": 0.0,
        "pre_support_0_force": 0.0,
        "pre_support_1_force": 0.0,
        "post_support_0_force": 0.0,
        "post_support_1_force": 0.0,
    })
    agent.inner.add_edge(trial, "has_humanoid_transition", outcome)

    agent.tick()
    attrs = agent.s.node(model)["attrs"]
    assert attrs["prediction_invalidation_count"] == 1
    assert attrs["prediction_reground_count"] == 1
    assert attrs["invalidated_receipt_seq"] == 1
    assert attrs["last_reground_receipt_seq"] == 1
    assert attrs["prediction_authority"] == 1
    assert attrs["prediction_grounding_status"] == "receipt_regrounded"
    assert attrs["mean_dvx"] == 0.0
    assert attrs["experience_count"] == 1

    # Receipt sequence, not a timer, supplies idempotence.
    agent.tick()
    attrs = agent.s.node(model)["attrs"]
    assert attrs["prediction_invalidation_count"] == 1
    assert attrs["prediction_reground_count"] == 1


def test_graph_walks_with_alternating_support_and_bounded_aerial_phases():
    if importlib.util.find_spec("pybullet") is None:
        pytest.skip("install requirements-robot.txt")
    from scripts.jabberwock_humanoid_walk import run_experiment

    result = run_experiment(PROTOCOL)
    walking = result["walking"]
    tonic = result["tonic_control"]

    assert result["joint_count"] == 21
    assert result["opaque_actuator_count"] == 43
    assert result["policy_owner"] == "rust_graph"
    assert result["pre_locomotion_trajectories_identical"] is True
    assert result["paired_effect"]["walking_passed"] is False
    assert result["evaluation_profile"]["dimensions"] == {
            "upright": True,
            "directed_progress": False,
            "support_alternation": True,
            "bounded_aerial_occupancy": True,
        "bounded_lateral_drift": True,
    }
    assert walking["familiarization_complete"] == 1.0
    assert walking["adaptation_actions"] > 0
    assert walking["adaptation_learning_events"] > 20
    assert walking["deployment_learning_events"] > 0
    assert walking["adaptation_first_fall_action"] is None
    assert walking["first_fall_action"] is None
    assert walking["perturbation"]["onset_action"] == 300
    assert walking["perturbation"][
        "world_frame_force_body_weights"
    ] == [2.0, 0.0, 0.0]
    assert walking["perturbation"][
        "resolved_world_frame_force_newtons"
    ][0] > 800.0
    assert sum(
        row["perturbation_applied"] for row in walking["trace"]
    ) == 1
    assert walking["minimum_height"] > walking["height_floor"]
    assert walking["upright_at_end_graph_assessment"] == 1.0
    assert walking["directed_progress"] < 0.3
    assert result["paired_effect"]["directed_progress_advantage"] > 1.0
    assert abs(walking["lateral_offset"]) < json.loads(
        PROTOCOL.read_text(encoding="utf-8")
    )["evaluation"]["maximum_final_lateral_drift_metres"]
    assert 0 < walking["support_alternations"] < 20
    assert walking["aerial_samples_per_locomotor_cycle"] <= json.loads(
        PROTOCOL.read_text(encoding="utf-8")
    )["evaluation"]["maximum_aerial_samples_per_locomotor_cycle"]
    assert walking["motor_fixation_count"] > 1.0
    assert walking["motor_configuration_transition_count"] > 0.0
    assert walking["motor_efference_copy_count"] - walking[
        "motor_efference_confirmation_count"
    ] in (0.0, 1.0)
    assert walking["learned_gait_envelope"]["mean_tilt"] > 0.0
    assert (
        walking["learned_gait_envelope"]["mean_tilt"]
        < walking["learned_gait_envelope"]["tilt"]
    )
    assert (
        walking["learned_gait_envelope"]["horizontal_prediction_error"]
        > 0.0
    )
    assert walking["gait_surprise_confirmation_receipts"] == 6.0
    assert walking["nominal_response_frames"] == 12.0
    assert walking["minimum_response_frames"] >= 1.0
    assert walking["maximum_response_frames"] == 12.0
    assert walking["mean_realized_motor_command_rate_hz"] >= 20.0
    assert walking["synergy_probe_count"] == 42
    assert (
        walking["approved_synergy_count"]
        + walking["rejected_synergy_count"]
        == walking["synergy_probe_count"]
    )
    assert walking["approved_synergy_count"] > 0
    # Pair outcomes are Pareto evidence, not a mandatory binary fault class.
    # A body may safely admit every calibrated pair while retaining
    # non-additive residual, support and energy costs for later choice.
    assert any(
        float(row.get("residual_magnitude", 0.0)) > 0.0
        for row in walking["synergy_models"]
    )
    assert all(
        "support_loss_ema" in row
        and "support_deficit_ema" in row
        and "mean_input_energy_joules" in row
        for row in walking["synergy_models"]
    )
    assert walking["maximum_synergy_probe_bundle_width"] == 2
    assert max(
        row["experience_count"] for row in walking["synergy_models"]
    ) > 1.0
    assert any(
        row["selected_token"] != row["selected_secondary_token"]
        for row in walking["synergy_calibration_trace"]
    )
    assert walking["compound_action_count"] > 0
    assert walking["maximum_motor_bundle_width"] > 1
    assert walking["synthesized_motor_program_count"] > 0
    assert walking["grounded_motor_program_count"] > 0
    assert walking["maximum_synthesized_motor_program_width"] > 1
    assert walking["motor_memory_recall_count"] > 0
    assert walking["reusable_motor_memory_count"] > 0
    assert walking["maximum_motor_memory_experience_count"] > 1.0
    assert walking["maximum_motor_memory_uncertainty"] > 0.0
    assert walking["motor_preparation_count"] == walking[
        "motor_preparation_release_count"
    ]
    assert walking["motor_preparation_count"] == walking[
        "motor_memory_recall_count"
    ]
    assert walking["output_null_motor_preparation_count"] == 0
    assert walking["output_potent_motor_preparation_count"] == walking[
        "motor_preparation_count"
    ]
    assert all(
        row["gated_cost"] < row["primitive_cost"]
        and (
            row["lateral_cost"]
            + row["lateral_indirect_path_cost"]
            <= row["primitive_lateral_cost"]
        )
        for row in walking["motor_preparations"]
    )
    assert walking["learned_motor_transition_count"] > 0
    assert walking["reusable_motor_transition_count"] > 0
    assert walking["maximum_motor_transition_experience_count"] >= 1.0
    assert walking["minimum_learned_motor_transition_frames"] >= 1.0
    assert sum(
        row["motor_sequence_recalled"] for row in walking["trace"]
    ) == walking["motor_sequence_recall_count"]
    assert sum(
        row["motor_memory_recalled"] for row in walking["trace"]
    ) == walking["motor_memory_recall_count"]
    assert all(
        row["motor_bundle_width"] == len(row["motor_tokens"])
        for row in walking["trace"]
    )
    assert walking["recovery_mode_entries"] >= 0.0
    assert walking["recovery_mode_exits"] <= walking[
        "recovery_mode_entries"
    ]
    assert walking["recovery_action_count"] >= 0.0
    assert walking["recovery_mode_at_end"] == 0.0
    recovery_trace = [
        row
        for row in walking["trace"]
        if row["decision_kind"] == "gait_recovery"
    ]
    assert len(recovery_trace) == walking["recovery_action_count"]
    assert all(
        row["selected_token"] != "humanoid_actuator_000"
        for row in recovery_trace
    )
    assert all(
        "gait_prediction_error" in row
        and "gait_surprise_streak" in row
        and "recovery_mode_after" in row
        for row in walking["trace"]
    )
    assert walking["support_pattern_counts"]["support_0"] > 0
    assert walking["support_pattern_counts"]["support_1"] > 0
    assert walking["support_pattern_counts"]["double_support"] > 0
    assert walking["touchdown_count"] > 20
    assert walking["advancing_touchdown_count"] > 20
    assert walking["mean_directed_touchdown_advance"] > 0.0
    assert walking["locomotion_action_diversity"] > 10
    assert walking["directed_progress_graph_assessment"] == pytest.approx(
        walking["directed_progress"]
    )
    assert walking["lateral_offset_graph_assessment"] == pytest.approx(
        walking["lateral_offset"]
    )
    assert walking[
        "maximum_lateral_excursion_graph_assessment"
    ] == pytest.approx(walking["maximum_lateral_excursion"])
    assert walking["minimum_height_graph_assessment"] == pytest.approx(
        walking["minimum_height"]
    )
    assert walking["peak_tilt_graph_assessment"] == pytest.approx(
        walking["peak_tilt"]
    )
    assert walking[
        "support_alternations_graph_assessment"
    ] == pytest.approx(walking["support_alternations"])
    assert walking["aerial_samples_graph_assessment"] == pytest.approx(
        walking["aerial_samples"]
    )
    assert all(
        row["experience_count"] == 1.0
        for row in walking["models"]
        if row["tonic_default"] == 0.0
    )
    prior_counts = {
        row["experience_count"]
        for row in walking["phase_models_before_walk"]
    }
    support_phases = {
        row["support_phase"]
        for row in walking["phase_models_before_walk"]
    }
    assert support_phases == {0.0, 1.0, 2.0}
    assert len(walking["phase_models_before_walk"]) == (
        walking["non_tonic_actuator_count"] * len(support_phases)
    )
    assert prior_counts == {9.0}
    assert all(
        row["initialized"] == 1.0
        for row in walking["phase_models_before_walk"]
    )
    assert all(
        9.0 <= row["experience_count"] <= 10.0
        for row in walking["phase_models_after_walk"]
    )
    assert any(
        row["experience_count"] == 10.0
        for row in walking["phase_models_after_walk"]
    )
    assert tonic["directed_progress"] < 0.01
    assert tonic["support_alternations"] < 10
    assert tonic["support_pattern_counts"]["double_support"] > 580
    assert tonic["touchdown_count"] < 10


def test_independent_experiment_arms_submit_before_deterministic_fold(
    monkeypatch,
):
    import scripts.jabberwock_humanoid_walk as walk

    events = []

    class DeferredResult:
        def __init__(self, fn, args):
            self.fn = fn
            self.args = args

        def result(self):
            events.append(("fold", self.args[1]))
            return self.fn(*self.args)

    class RecordingPool:
        def __init__(self, *, max_workers, mp_context):
            events.append(("workers", max_workers))

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def submit(self, fn, *args):
            events.append(("submit", args[1]))
            return DeferredResult(fn, args)

    monkeypatch.setattr(walk, "ProcessPoolExecutor", RecordingPool)
    monkeypatch.setattr(
        walk.multiprocessing,
        "get_context",
        lambda method: method,
    )
    monkeypatch.setattr(
        walk,
        "_run_arm_process",
        lambda _protocol, mode, _library, _out: (mode, {"mode": mode}),
    )

    modes = ["directed_walk", "tonic_posture_control"]
    result = walk._run_independent_arms(
        {"protocol": "parallel_boundary_test"},
        modes,
        motor_library=None,
        motor_library_path=None,
    )

    assert list(result) == modes
    assert events == [
        ("workers", len(modes)),
        ("submit", modes[0]),
        ("submit", modes[1]),
        ("fold", modes[0]),
        ("fold", modes[1]),
    ]
