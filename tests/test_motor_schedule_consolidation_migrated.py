"""Biological-timescale gates for the shared embodied motor loop."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from substrate.world_adapter import WorldAdapter


ROOT = Path(__file__).resolve().parents[1]


def _load_generator(name: str):
    path = ROOT / "scripts" / f"gen_{name}_seed.py"
    spec = importlib.util.spec_from_file_location(f"gen_{name}_seed", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _rules(name: str) -> dict[str, dict]:
    seed = json.loads((ROOT / "seeds" / f"{name}.json").read_text())
    return {rule["name"]: rule for rule in seed["rules"]}


def test_generated_schedules_are_checked_in_exactly():
    for name in ("humanoid_adaptation", "embodied_motor_priors"):
        generated = _load_generator(name).manifest()
        checked_in = json.loads(
            (ROOT / "seeds" / f"{name}.json").read_text()
        )
        assert generated == checked_in


def test_humanoid_release_and_interrupt_stay_hard_realtime():
    rules = _rules("humanoid_adaptation")
    for name in (
        "ha_measure_raw_humanoid_balance",
        "ha_choose_learned_balance_twitch",
        "ha_choose_gait_interruption_balance_twitch",
        "ha_measure_gait_prediction_error_and_interrupt",
        "ha_open_receipt_backed_motor_trial",
        "ha_withdraw_unsafe_program_from_body_shape_library",
        "ha_request_primitive_motor_learning",
        "ha_request_motor_sequence_consolidation",
    ):
        assert rules[name]["latency_class"] == "hard_realtime"
        assert rules[name]["area"] == "humanoid_sensorimotor_adaptation"


def test_humanoid_plasticity_reuses_receipt_recruited_adaptive_sheet():
    rules = _rules("humanoid_adaptation")
    for name in (
        "ha_learn_opaque_joint_consequence",
        "ha_learn_compound_interaction_residual",
        "ha_learn_support_phase_consequence_online",
        "ha_tune_response_horizon_from_prediction_receipt",
        "ha_learn_whole_body_get_up_consequence",
    ):
        assert rules[name]["latency_class"] == "soft_realtime"
        assert rules[name]["area"] == "adaptive_learning"


def test_humanoid_library_work_uses_shared_consolidation_sheet():
    rules = _rules("humanoid_adaptation")
    for name in (
        "ha_store_grounded_program_by_body_shape",
        "ha_consolidate_equivalent_motor_program",
        "ha_consolidate_motor_sequence_transition",
        "ha_expose_motor_decision_option",
    ):
        assert rules[name]["latency_class"] == "background"
        assert rules[name]["area"] == "embodied_sensorimotor"


def test_shared_priors_keep_bookkeeping_fast_and_learning_interruptible():
    seed = json.loads(
        (ROOT / "seeds" / "embodied_motor_priors.json").read_text()
    )
    assert "motor_decision_collapse" in seed["depends_on"]
    rules = _rules("embodied_motor_priors")
    assert rules["emp_recognize_humanoid_motor_receipt"]["latency_class"] == (
        "hard_realtime"
    )
    for name in (
        "emp_measure_locomotor_continuity_from_receipts",
        "emp_measure_thermodynamic_motor_economy",
        "emp_learn_opaque_effector_causal_capability",
    ):
        assert rules[name]["latency_class"] == "soft_realtime"
        assert rules[name]["area"] == "adaptive_learning"


def test_shared_core_already_recruits_every_non_hard_motor_area():
    core = json.loads(
        (ROOT / "seeds" / "embodied_sensorimotor_core.json").read_text()
    )
    task_areas = {
        node["attrs"]["area"]
        for node in core["nodes"]
        if node["type"] == "SystemTwoTaskSet"
    }
    assert {"adaptive_learning", "embodied_sensorimotor"} <= task_areas
    rules = {rule["name"]: rule for rule in core["rules"]}
    plant_learning = rules["esm_learn_actuator_plant_envelope"]
    assert plant_learning["area"] == "adaptive_learning"
    assert plant_learning["latency_class"] == "soft_realtime"
    assert rules["esm_update_event_timed_local_control"]["latency_class"] == (
        "hard_realtime"
    )


def test_every_body_plan_exposes_common_option_values_for_scoped_bridge():
    rule_names = {
        "embodied_adaptation": "ea_expose_motor_decision_option",
        "aerial_adaptation": "aa_expose_motor_decision_option",
        "humanoid_adaptation": "ha_expose_motor_decision_option",
        "helicopter_autorotation": "ha_expose_motor_decision_option",
    }
    for seed_name, rule_name in rule_names.items():
        seed = json.loads(
            (ROOT / "seeds" / f"{seed_name}.json").read_text()
        )
        assert "motor_decision_collapse" in seed["depends_on"]
        rule = next(
            rule for rule in seed["rules"] if rule["name"] == rule_name
        )
        serialized = json.dumps(rule)
        for attr in (
            "available",
            "ordinal",
            "default_value",
            "learned_value",
            "grounded_value",
        ):
            assert attr in serialized


def test_ground_release_authority_is_the_shared_collapse():
    seed = json.loads(
        (ROOT / "seeds" / "embodied_adaptation.json").read_text()
    )
    policy = next(
        node["attrs"]
        for node in seed["nodes"]
        if node["type"] == "EmbodiedPolicy"
    )
    rules = {rule["name"]: rule for rule in seed["rules"]}
    assert policy["shared_motor_collapse_enabled"] == 1.0
    assert {
        "ea_prepare_shared_motor_collapse_values",
        "ea_arm_shared_motor_collapse",
        "ea_release_shared_motor_collapse",
    } <= rules.keys()
    direct = json.dumps(rules["ea_choose_model_action"])
    assert "shared_motor_collapse_enabled" in direct
    assert '"value": 0.0' in direct
    grounded = json.dumps(
        rules["ea_prepare_shared_motor_collapse_values"]
    )
    assert "grounded_existing_forward_planning_cost" in grounded
    assert "predicted_score" not in grounded  # expanded Term, not a host call


def test_every_learned_body_selector_releases_from_shared_collapse():
    cases = {
        "aerial_adaptation": {
            "policy_type": "AerialPolicy",
            "direct": "aa_choose_learned_flight_action",
            "shared": {
                "aa_prepare_shared_motor_collapse_values",
                "aa_arm_shared_motor_collapse",
                "aa_release_shared_motor_collapse",
            },
            "provenance": "grounded_existing_flight_control_cost",
        },
        "helicopter_autorotation": {
            "policy_type": "HelicopterEnergyPolicy",
            "direct": "ha_choose_energy_viability_action",
            "shared": {
                "ha_prepare_shared_memory_options",
                "ha_arm_shared_memory_collapse",
                "ha_release_shared_memory_collapse",
                "ha_prepare_shared_compact_options",
                "ha_arm_shared_compact_collapse",
                "ha_release_shared_compact_collapse",
            },
            "provenance": "grounded_contextual_energy_viability_cost",
        },
        "humanoid_adaptation": {
            "policy_type": "HumanoidPolicy",
            "direct": "ha_select_learned_walking_primary",
            "shared": {
                "ha_prepare_shared_walking_primary",
                "ha_arm_shared_walking_primary",
                "ha_release_shared_walking_primary",
            },
            "provenance": (
                "grounded_support_conditioned_whole_body_walking_cost"
            ),
        },
    }
    for seed_name, case in cases.items():
        seed = json.loads(
            (ROOT / "seeds" / f"{seed_name}.json").read_text()
        )
        policy = next(
            node["attrs"]
            for node in seed["nodes"]
            if node["type"] == case["policy_type"]
        )
        rules = {rule["name"]: rule for rule in seed["rules"]}
        assert policy["shared_motor_collapse_enabled"] == 1.0
        assert case["shared"] <= rules.keys()

        direct = json.dumps(rules[case["direct"]])
        assert "shared_motor_collapse_enabled" in direct
        assert '"value": 0.0' in direct

        shared_rules = json.dumps(
            [rules[name] for name in sorted(case["shared"])]
        )
        assert case["provenance"] in shared_rules
        assert "has_motor_decision_option" in shared_rules
        assert "decision_request_epoch" in shared_rules
        assert "selected_option_ref" in shared_rules


def test_shared_collapse_publishes_exact_graph_option_identity():
    rules = _rules("motor_decision_collapse")
    proposal = json.dumps(rules["mdc_fast_propose"])
    shallow = json.dumps(rules["mdc_shallow_settle"])
    deep = json.dumps(rules["mdc_residual_authorized_deepen"])
    publication = json.dumps(rules["mdc_episode_publish_once"])

    assert "proposed_option_ref" in proposal
    assert "chosen_option_ref" in shallow
    assert "chosen_option_ref" in deep
    assert "selected_option_ref" in publication


def test_humanoid_walking_primary_actually_traverses_shared_collapse():
    agent = WorldAdapter(seeds=("humanoid_adaptation",))
    episode = agent.s.add_node("HumanoidEpisode", {
        "phase": "locomotion",
        "mode": "directed_walk",
        "recovery_mode": 0.0,
        "action_ready": 0.0,
        "motor_primary_ready": 0.0,
        "request_seq": 1.0,
        "decision_seq": 0.0,
        "current_support_phase": 0.0,
        "standing_reference_z": 1.0,
        "body_mass": 1.0,
        "heading_x": 1.0,
        "lateral_offset": 0.0,
        "state_qx": 0.0,
        "state_qy": 0.0,
        "state_qz": 0.0,
        "state_qw": 1.0,
        "state_wx": 0.0,
        "state_wy": 0.0,
        "state_vx": 0.0,
        "state_vy": 0.0,
        "response_frames": 2.0,
        "decision_count": 0.0,
        "compound_response_interval": 100.0,
        "last_compound_decision_count": 0.0,
    })
    agent.s.add_edge(
        agent.agent,
        "has_humanoid_episode",
        episode,
    )
    options = []
    for ordinal, (token, predicted_dvx) in enumerate((
        ("grounded_loser", -0.4),
        ("grounded_winner", 0.06),
    )):
        option = agent.s.add_node("HumanoidPhaseActionModel", {
            "token": token,
            "ordinal": float(ordinal),
            "actuator_group": float(ordinal),
            "support_phase": 0.0,
            "context_id": 0.0,
            "initialized": 1.0,
            "experience_count": 1.0,
            "mean_dzx": 0.0,
            "mean_dzy": 0.0,
            "mean_dwx": 0.0,
            "mean_dwy": 0.0,
            "mean_dvx": predicted_dvx,
            "mean_dvy": 0.0,
            "mean_input_energy_joules": 0.0,
            "support_loss_ema": 0.0,
        })
        agent.s.add_edge(
            episode,
            "has_humanoid_phase_action_model",
            option,
        )
        options.append(option)

    agent.tick()

    attrs = agent.s.node(episode)["attrs"]
    assert attrs["decision_status"] == "published"
    assert attrs["selected_option_ref"] == options[1]
    assert attrs["selected_primary_token"] == "grounded_winner"
    assert attrs["selected_via"] == "orderN"
    assert agent.s.node(options[1])["attrs"][
        "decision_experience_count"
    ] == 1.0
