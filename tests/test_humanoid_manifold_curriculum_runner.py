from __future__ import annotations

import json

import pytest

from scripts import run_humanoid_manifold_curriculum_paired as runner


PROTOCOL = runner.ROOT / "protocols" / "humanoid_developmental_curriculum_v1.json"


def _raw_run(*, treatment: bool, ready: bool = True) -> dict:
    trace = [{
        "action": 7,
        "manifold_bounds_ready": 1,
        "motor_bundle_width": 1,
    }] if ready else []
    return {
        "trace": trace,
        "directed_progress": 0.2,
        "first_fall_action": None,
        "minimum_height": 0.1,
        "lateral_offset": 0.0,
        "support_alternations": 2,
        "compound_action_count": 1,
        "maximum_synthesized_motor_program_width": 2,
        "calibration_trace": [{"request_seq": 1}],
        "pre_locomotion_state": {"position": [0, 0, 0.1]},
        "body_shape_name": "shape:test",
        "actuator_count": 21,
        "motor_library_loaded_shape_count": 1,
        "motor_library_loaded_developmental_capability_count": 15,
        "future_manifold": {
            "enabled": float(treatment),
            "temporal_anchors_enabled": float(treatment),
            "bounds_ready": float(treatment and ready),
            "bounds_provenance": (
                "receipt_grounded_phase_action_envelope"
                if treatment and ready else "unavailable"
            ),
            "learning_safety_active": 1 if treatment else 0,
        },
        "curriculum": {
            "developmental": True,
            "stage_ordinal": 13,
            "developmental_stage_transition_count": 13,
            "mastery_count": 13,
            "goal": "locomotion",
            "developmental_goal": "locomotion",
            "active_capability_diagnostics": {"status": "active"},
            "developmental_frontier": ["next"],
            "developmental_unresolved_prerequisites": ["prior"],
            "self_learning_plan": {"selected_step": "step"},
        },
        "cognitive_supervision": {
            "experiment_halted_by_checkin": 0,
            "replan_count": 0,
            "continuation_authority_at_end": 1,
        },
    }


def test_metrics_keep_legacy_defaults_and_extract_gate_trace():
    metrics = runner._metrics(_raw_run(treatment=True))

    assert metrics["actions_executed"] == 1
    assert metrics["curriculum"]["stage_ordinal"] == 13
    assert metrics["future_manifold_gate_onset_action"] == 7
    assert metrics["post_gate_action_count"] == 1
    assert metrics["maximum_post_gate_program_width"] == 1
    assert metrics["body_reset_count"] == 0
    assert metrics["body_reset_scenarios"] == []
    assert metrics["gate_onset_evidence_present"] is True
    assert metrics["motor_library_loaded_developmental_capability_count"] == 15
    assert metrics["curriculum"]["active_capability_diagnostics"] == {
        "status": "active"
    }
    assert metrics["curriculum"]["developmental_frontier"] == ["next"]
    assert metrics["curriculum"]["developmental_unresolved_prerequisites"] == [
        "prior"
    ]
    assert metrics["curriculum"]["self_learning_plan"] == {
        "selected_step": "step"
    }

    legacy = runner._metrics({"trace": []})
    assert legacy["actions_executed"] == 0
    assert legacy["curriculum"]["stage_ordinal"] == 0
    assert legacy["future_manifold"] == {}


def test_library_metadata_rejects_old_artifact_and_checks_exact_contract():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    metadata = runner._library_metadata(
        {"version": 6, "body_shapes": [], "developmental_capabilities": [{}]},
        protocol,
    )

    assert metadata["semantic_type"] == (
        runner.CAPABILITY_LIBRARY_SEMANTIC_TYPE
    )
    assert metadata["semantic_type_source"] == "inferred"
    assert metadata["curriculum_contract_present"] is False
    assert metadata["curriculum_contract_matches"] is False

    mismatch = runner._library_metadata(
        {
            "semantic_type": "wrong",
            "developmental_curriculum_contract": {
                "schema_version": 1,
                "capability_names": [],
                "ontology_sha256": "wrong",
            },
        },
        protocol,
    )
    assert mismatch["semantic_type"] == "wrong"
    assert mismatch["curriculum_contract_matches"] is False


def test_pair_validity_requires_gate_provenance_safety_and_cognitive_evidence():
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    library_metadata = runner._library_metadata(
        {
            "developmental_capabilities": [{}],
            "developmental_curriculum_contract": (
                runner.developmental_curriculum_contract()
            ),
        },
        protocol,
    )
    baseline = runner._metrics(_raw_run(treatment=False, ready=True))
    treatment = runner._metrics(_raw_run(treatment=True, ready=True))
    reasons = runner._pair_invalid_reasons(
        baseline,
        treatment,
        evaluation_actions=1,
        calibration_identical=True,
        pre_locomotion_identical=True,
        library_metadata=library_metadata,
        protocol_digest="same",
        treatment_protocol_digest="same",
    )
    assert reasons == []

    treatment["future_manifold"]["bounds_provenance"] = "unavailable"
    treatment["learning_safety_active"] = 0
    treatment["cognitive_supervision"]["replan_count"] = 1
    reasons = runner._pair_invalid_reasons(
        baseline,
        treatment,
        evaluation_actions=1,
        calibration_identical=True,
        pre_locomotion_identical=True,
        library_metadata=library_metadata,
        protocol_digest="same",
        treatment_protocol_digest="same",
    )
    assert "treatment_bounds_provenance_absent_or_mismatched" in reasons
    assert "learning_safety_not_active" in reasons
    assert "treatment_cognitive_replan_required" not in reasons


def test_fresh_training_completion_fails_closed(tmp_path):
    incomplete = runner._metrics({"trace": []})
    ok, reasons = runner._training_completion(
        incomplete, 48, library_path=tmp_path / "missing.json"
    )
    assert ok is False
    assert "fresh_training_action_budget_not_completed" in reasons
    assert "fresh_training_library_artifact_absent" in reasons

    library_path = tmp_path / "library.json"
    library_path.write_text("{}", encoding="utf-8")
    complete = runner._metrics(_raw_run(treatment=False))
    complete["actions_executed"] = 48
    complete["motor_library_saved_shape_count"] = 1
    ok, reasons = runner._training_completion(
        complete, 48, library_path=library_path
    )
    assert ok is True
    assert reasons == []


def test_checkpoint_refuses_to_claim_pair_before_locomotion():
    metrics = runner._metrics(_raw_run(treatment=False, ready=False))
    metrics["curriculum"]["stage_ordinal"] = 0
    metrics["curriculum"]["goal"] = "spontaneous_variation"
    checkpoint = runner._checkpoint(
        metrics,
        action_budget=48,
        mode="training",
        protocol_digest="digest",
    )
    assert checkpoint["milestone"] == "pre_locomotion"
    assert checkpoint["recommendation"] == "continue_to_next_checkpoint"
    assert checkpoint["gate_ready"] is False


def test_checkpoint_does_not_pair_on_manifold_readiness_before_locomotion():
    metrics = runner._metrics(_raw_run(treatment=True, ready=True))
    metrics["curriculum"]["stage_ordinal"] = 8
    metrics["curriculum"]["goal"] = "orientation_change"

    checkpoint = runner._checkpoint(
        metrics,
        action_budget=1,
        mode="probe",
        protocol_digest="digest",
    )

    assert checkpoint["gate_ready"] is True
    assert checkpoint["milestone"] == "manifold_ready_pre_locomotion"
    assert checkpoint["recommendation"] == (
        "continue_curriculum_before_pairing"
    )


def test_staged_mode_runs_one_arm_and_records_checkpoint(monkeypatch, tmp_path):
    calls = []

    def fake_run(protocol, mode, *, motor_library=None, motor_library_out=None):
        calls.append((mode, motor_library is not None, motor_library_out))
        assert protocol["locomotion"]["actions"] == 48
        if motor_library_out is not None:
            motor_library_out.write_text(
                json.dumps({"developmental_capabilities": [{}]}),
                encoding="utf-8",
            )
        result = _raw_run(treatment=False, ready=False)
        result["curriculum"]["stage_ordinal"] = 0
        result["curriculum"]["goal"] = "spontaneous_variation"
        result["curriculum"]["developmental_goal"] = "spontaneous_variation"
        result["trace"] = [{"action": n} for n in range(48)]
        result["motor_library_saved_shape_count"] = 1
        return result

    monkeypatch.setattr(runner, "_run_arm", fake_run)
    result = runner.run_staged(
        PROTOCOL,
        action_budget=48,
        mode="training",
        library_path=tmp_path / "library.json",
    )

    assert calls == [("directed_walk", False, tmp_path / "library.json")]
    assert result["training_complete"] is True
    assert result["training_invalid_reasons"] == []
    assert result["library_metadata"]["artifact_valid_json"] is True
    assert result["library_metadata"]["semantic_type_source"] == "inferred"
    assert result["staged_result_valid"] is True
    assert result["checkpoint"]["action_budget_complete"] is True
    assert result["checkpoint"]["milestone"] == "pre_locomotion"


def test_staged_training_halt_is_fail_closed_but_preserves_null_artifact(
    monkeypatch, tmp_path
):
    library_path = tmp_path / "null-library.json"

    def halted_run(protocol, mode, *, motor_library=None, motor_library_out=None):
        assert motor_library_out == library_path
        motor_library_out.write_text("null\n", encoding="utf-8")
        result = _raw_run(treatment=False, ready=False)
        result["trace"] = [{"action": n} for n in range(19)]
        result["curriculum"]["stage_ordinal"] = 0
        result["curriculum"]["goal"] = "spontaneous_variation"
        result["curriculum"]["developmental_goal"] = "spontaneous_variation"
        result["motor_library_saved_shape_count"] = 0
        result["cognitive_supervision"]["experiment_halted_by_checkin"] = 1
        return result

    monkeypatch.setattr(runner, "_run_arm", halted_run)
    result = runner.run_staged(
        PROTOCOL,
        action_budget=48,
        mode="training",
        library_path=library_path,
    )

    assert library_path.read_text(encoding="utf-8") == "null\n"
    assert result["training_complete"] is False
    assert result["staged_result_valid"] is False
    assert "fresh_training_action_budget_not_completed" in result[
        "training_invalid_reasons"
    ]
    assert "cognitive_checkin_terminal" in result["training_invalid_reasons"]
    assert "fresh_training_library_shape_evidence_absent" in result[
        "training_invalid_reasons"
    ]
    assert result["library_metadata"]["artifact_valid_json"] is False
    assert result["library_metadata"]["semantic_type"] == "unknown"
    assert result["checkpoint"]["milestone"] == "incomplete_training"
    assert result["checkpoint"]["recommendation"] == "do_not_accept_artifact"


def test_staged_continuation_loads_one_generation_and_writes_the_next(
    monkeypatch, tmp_path
):
    input_path = tmp_path / "generation-1.json"
    output_path = tmp_path / "generation-2.json"
    retained = {
        "developmental_capabilities": [{"name": "retained"}],
        "developmental_curriculum_contract": (
            runner.developmental_curriculum_contract()
        ),
    }
    input_path.write_text(json.dumps(retained), encoding="utf-8")

    def continuing_run(
        protocol, mode, *, motor_library=None, motor_library_out=None
    ):
        assert protocol["locomotion"]["future_manifold_enabled"] == 1.0
        assert motor_library == retained
        assert motor_library_out == output_path
        motor_library_out.write_text(json.dumps({
            **retained,
            "developmental_capabilities": [
                *retained["developmental_capabilities"],
                {"name": "new"},
            ],
        }), encoding="utf-8")
        result = _raw_run(treatment=True, ready=False)
        result["trace"] = [{"action": n} for n in range(48)]
        result["motor_library_saved_shape_count"] = 1
        return result

    monkeypatch.setattr(runner, "_run_arm", continuing_run)
    result = runner.run_staged(
        PROTOCOL,
        action_budget=48,
        mode="continue",
        library_path=output_path,
        library_in=input_path,
    )

    assert json.loads(input_path.read_text(encoding="utf-8")) == retained
    assert len(json.loads(output_path.read_text(
        encoding="utf-8"
    ))["developmental_capabilities"]) == 2
    assert result["staged_result_valid"] is True
    assert result["training_complete"] is True
    assert result["input_library_metadata"][
        "curriculum_contract_matches"
    ] is True
    assert result["checkpoint"]["mode"] == "continue"


def test_staged_budget_and_probe_requirements_are_deterministic(tmp_path):
    with pytest.raises(ValueError, match="one of"):
        runner.run_staged(
            PROTOCOL,
            action_budget=80,
            mode="training",
            library_path=tmp_path / "library.json",
        )
    with pytest.raises(ValueError, match="requires --library-in"):
        runner.run_staged(
            PROTOCOL,
            action_budget=48,
            mode="probe",
            library_path=tmp_path / "library.json",
        )
    with pytest.raises(ValueError, match="requires --library-in"):
        runner.run_staged(
            PROTOCOL,
            action_budget=48,
            mode="continue",
            library_path=tmp_path / "next.json",
        )
    library_path = tmp_path / "same.json"
    library_path.write_text(json.dumps({
        "developmental_curriculum_contract": (
            runner.developmental_curriculum_contract()
        ),
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="distinct input and output"):
        runner.run_staged(
            PROTOCOL,
            action_budget=48,
            mode="continue",
            library_path=library_path,
            library_in=library_path,
        )
