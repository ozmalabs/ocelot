from __future__ import annotations

import ast
import json
import os
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY = ROOT / "domains" / "humanoid_bench_world.py"
RESULT = ROOT / "results" / "humanoid_bench_h1_walk_v1.json"
SEED = ROOT / "seeds" / "humanoid_adaptation.json"


def test_humanoid_bench_boundary_is_mechanical_only():
    tree = ast.parse(BOUNDARY.read_text(encoding="utf-8"))
    public = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not node.name.startswith("_")
    }
    assert public == {
        "actuator_options",
        "apply_force_pulse",
        "body_shape_signature",
        "close",
        "hold_tonic",
        "observe",
        "reset",
        "step",
    }
    assert not {
        "choose",
        "decide",
        "learn",
        "plan",
        "predict",
        "reward",
        "score",
    } & public


def test_recorded_h1_result_preserves_the_failed_benchmark():
    result = json.loads(RESULT.read_text(encoding="utf-8"))
    walking = result["walking"]
    tonic = result["tonic_control"]

    assert result["environment_id"] == "h1-walk-v0"
    assert result["joint_count"] == 19
    assert result["opaque_actuator_count"] == 39
    assert len(result["benchmark_revision"]) == 40
    assert result["policy_owner"] == "rust_graph"
    assert result["paired_effect"]["walking_passed"] is False
    assert walking["first_fall_action"] == 65
    assert tonic["first_fall_action"] == 64
    assert walking["benchmark"]["terminated"] is True
    assert walking["nominal_response_frames"] == 10
    assert walking["minimum_response_frames"] == 5
    assert walking["synergy_probe_count"] == 38
    assert walking["approved_synergy_count"] == 38
    assert walking["rejected_synergy_count"] == 0
    assert walking["compound_action_count"] == 0
    assert walking["synthesized_motor_program_count"] > 0
    assert walking["grounded_motor_program_count"] > 0
    assert walking["maximum_synthesized_motor_program_width"] == 1
    assert tonic["maximum_motor_bundle_width"] == 1


def test_motor_program_synthesis_and_horizon_adaptation_are_graph_native():
    seed = json.loads(SEED.read_text(encoding="utf-8"))
    rules = {rule["name"]: json.dumps(rule) for rule in seed["rules"]}

    primary = rules["ha_select_gait_recovery_primary"]
    recovery = rules["ha_choose_gait_interruption_balance_twitch"]
    synthesizer = rules["ha_abs_expand_motor_program"]
    program_trial = rules["ha_open_synthesized_motor_program_trial"]
    program_learner = rules[
        "ha_ground_synthesized_motor_program_from_receipt"
    ]
    horizon = rules["ha_initialize_body_scaled_response_horizon"]
    tuner = rules["ha_tune_response_horizon_from_prediction_receipt"]
    probe = rules["ha_choose_staged_synergy_probe"]
    learner = rules["ha_learn_compound_interaction_residual"]

    assert '"type": "Argmin"' in primary
    assert "selected_recovery_primary_token" in primary
    assert "selected_secondary_token" in recovery
    assert "selected_response_frames" in recovery
    assert '"type": "Argmin"' in synthesizer
    assert "includes_humanoid_phase_action_model" in synthesizer
    assert "has_humanoid_synergy_model" in synthesizer
    assert "token_a" in synthesizer
    assert "token_b" in synthesizer
    assert "approved" in synthesizer
    assert "resumes_humanoid_motor_program" in synthesizer
    assert "enacts_humanoid_motor_program" in program_trial
    assert "residual_dvx" in program_learner
    assert "control_integration_frames" in horizon
    assert '"type": "Min"' in horizon
    assert "response_frames" in tuner
    assert "synergy_probe_anchor_ordinal" in probe
    assert "selected_secondary_token" in probe
    assert "residual_magnitude" in learner
    assert "receipt_verified" in learner
    assert "approved" in learner


def test_humanoid_future_manifold_fallback_is_opt_in_and_multi_frame():
    seed = json.loads(
        (ROOT / "seeds" / "humanoid_adaptation.json").read_text(
            encoding="utf-8"
        )
    )
    policy = next(
        node for node in seed["nodes"] if node["type"] == "HumanoidPolicy"
    )
    attrs = policy["attrs"]
    assert attrs["future_manifold_enabled"] == 0.0
    assert attrs["future_manifold_temporal_anchors_enabled"] == 0.0
    assert attrs["future_manifold_local_refinement_enabled"] == 0.0
    assert attrs["future_manifold_projection_budget"] == 16.0
    assert attrs["future_manifold_max_shape_order"] == 1.0

    rule = next(
        rule for rule in seed["rules"]
        if rule["name"] == "ha_stamp_future_manifold_audit_contract"
    )
    encoded = json.dumps(rule)
    assert "future_manifold_risk_gate" in encoded
    assert "dense_1_2_3_loglog_far" in encoded
    assert "future_manifold_physical_horizon" in encoded
    assert "multi_frame" in encoded
    assert "disabled" in encoded
    assert "future_manifold_multi_frame_risk_required" in encoded
    # The contract is audit-only; the native fallback owns candidate rejection
    # and must not turn the disabled path into a hidden alternate selector.
    assert rule["latency_class"] == "hard_realtime"


def test_live_humanoid_bench_boundary_when_configured():
    simulator = os.environ.get("HUMANOID_BENCH_ROOT")
    if simulator is None:
        pytest.skip("set HUMANOID_BENCH_ROOT for the external simulator test")

    from domains.humanoid_bench_world import HumanoidBenchWorld
    from scripts.jabberwock_humanoid_walk import _configuration

    protocol = json.loads(
        (ROOT / "protocols" / "humanoid_bench_h1_walk_v1.json").read_text(
            encoding="utf-8"
        )
    )
    with HumanoidBenchWorld(
        _configuration(protocol),
        simulator_root=Path(simulator),
        environment_id=protocol["environment_id"],
    ) as world:
        options = world.actuator_options()
        initial = world.observe()
        reference = tuple(
            joint["position"] for joint in initial["joints"]
        )
        after = world.step(
            ("humanoid_actuator_001", "humanoid_actuator_003"),
            frames=5,
            weights={
                "humanoid_actuator_001": 0.5,
                "humanoid_actuator_003": 1.0,
            },
            reference_positions=reference,
        )

    assert len(initial["joints"]) == 19
    assert len(initial["support_contact_forces"]) == 2
    assert len(options) == 39
    assert initial["control_integration_frames"] == 10
    assert after["step_index"] == 5
    assert after["last_actuator_tokens"] == (
        "humanoid_actuator_001",
        "humanoid_actuator_003",
    )
    assert after["motor_reference_kind"] == "graph_situated_fixation"
    assert after["motor_reference_positions"] == pytest.approx(reference)
    assert after["motor_command_displacements"][0] == pytest.approx(0.04)
    assert after["motor_command_displacements"][1] == pytest.approx(0.08)
    assert after["supplied_energy_joules"] >= 0.0
    assert after["sensed_contact_count"] >= 0.0
