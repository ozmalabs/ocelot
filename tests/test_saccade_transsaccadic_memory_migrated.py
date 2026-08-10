"""Focused gates for graph-native saccades and transsaccadic feature memory."""
from __future__ import annotations

import json
import math

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for


def _load(*seeds):
    substrate, agent = boot_core(seeds=())
    native = substrate._inner
    for seed in seeds:
        native.load_seed_manifest(manifest_for(seed), agent)
    return substrate, agent, native


def _node_of_type(substrate, node_type):
    nodes = list(substrate.nodes(node_type))
    assert len(nodes) == 1
    return nodes[0]


def _enable(native, substrate, node_type):
    node = _node_of_type(substrate, node_type)
    native.set_attr(node, "enabled", 1.0)
    return node


def _attention(native, agent, *, epoch=7, col=6, row=1,
               salience=9.0, az_deg=30.0, el_deg=-10.0):
    for key, value in {
        "vision_settled_epoch": epoch,
        "attention_sensor_epoch": epoch,
        "attention_refused": 0.0,
        "attention_salience": salience,
        "attention_column_index": col,
        "attention_row_index": row,
        "attention_az": math.radians(az_deg),
        "attention_el": math.radians(el_deg),
    }.items():
        native.set_attr(agent, key, value)


def _load_saccade():
    return _load("retinal_focus_control", "saccade_motor_control")


def test_saccade_slice_is_default_off_and_byte_inert():
    substrate, agent, native = _load_saccade()
    _attention(native, agent)
    native.run_rules()
    assert list(substrate.nodes("PresaccadicCandidate")) == []
    assert list(substrate.nodes("EyeMotorCommand")) == []
    assert list(substrate.nodes("SaccadeEfferenceCopy")) == []
    assert list(substrate.nodes("Fixation")) == []
    assert "eye_motor_active" not in substrate.node(agent)["attrs"]


def test_unique_attention_emits_authoritative_degree_command_and_efference():
    substrate, agent, native = _load_saccade()
    controller = _enable(native, substrate, "SaccadeController")
    _attention(native, agent)
    native.run_rules()

    commands = list(substrate.nodes("EyeMotorCommand"))
    copies = list(substrate.nodes("SaccadeEfferenceCopy"))
    fixations = list(substrate.nodes("Fixation"))
    assert len(commands) == len(copies) == len(fixations) == 1
    command = substrate.node(commands[0])["attrs"]
    copy = substrate.node(copies[0])["attrs"]
    fixation = substrate.node(fixations[0])["attrs"]
    assert command["status"] == "emitted"
    assert command["target_az_deg"] == pytest.approx(30.0)
    assert command["target_el_deg"] == pytest.approx(-10.0)
    assert copy["delta_column"] == 6
    assert copy["delta_row"] == 1
    assert fixation["status"] == "presaccadic"
    assert fixation["confirmed"] == 0

    attrs = substrate.node(agent)["attrs"]
    assert attrs["eye_motor_active"] == 1
    assert attrs["eye_motor_source_epoch"] == 7
    assert attrs["eye_motor_target_column"] == 6
    assert attrs["eye_motor_target_row"] == 1
    assert attrs["eye_motor_target_az_deg"] == pytest.approx(30.0)
    assert attrs["eye_motor_target_el_deg"] == pytest.approx(-10.0)
    assert attrs["eye_motor_fixation_epoch"] == 7
    assert attrs["eye_motor_duration_tics"] == 1
    assert attrs["eye_motor_status"] == "emitted"
    assert substrate.node(controller)["attrs"]["current_column"] == 0


def test_exact_priority_tie_refuses_without_host_tiebreak():
    substrate, agent, native = _load_saccade()
    controller = _enable(native, substrate, "SaccadeController")
    native.set_attr(agent, "vision_settled_epoch", 7)
    for col in (2, 6):
        candidate = substrate.add_node("PresaccadicCandidate", {
            "source_epoch": 7, "target_column": col, "target_row": 3,
            "gaze_az": 0.0, "gaze_el": 0.0,
            "priority": 5.0, "valid": 1.0,
        })
        substrate.add_edge(
            controller, "has_presaccadic_candidate", candidate)
    native.run_rules()

    assert list(substrate.nodes("EyeMotorCommand")) == []
    assert substrate.node(controller)["attrs"]["decision_epoch"] == 7
    attrs = substrate.node(agent)["attrs"]
    assert attrs["eye_motor_active"] == 0
    assert attrs["eye_motor_source_epoch"] == 7
    assert attrs["eye_motor_status"] == "refused"


def test_unique_presaccadic_candidate_is_selected_in_graph():
    substrate, agent, native = _load_saccade()
    controller = _enable(native, substrate, "SaccadeController")
    native.set_attr(agent, "vision_settled_epoch", 7)
    candidate = substrate.add_node("PresaccadicCandidate", {
        "source_epoch": 7, "target_column": 2, "target_row": 3,
        "gaze_az": 0.1, "gaze_el": 0.2,
        "priority": 5.0, "valid": 1.0,
    })
    substrate.add_edge(
        controller, "has_presaccadic_candidate", candidate)
    native.run_rules()

    (command,) = list(substrate.nodes("EyeMotorCommand"))
    assert substrate.neighbours(command, "selected_from") == [candidate]
    attrs = substrate.node(command)["attrs"]
    assert attrs["status"] == "requested"
    assert attrs["source_epoch"] == 7
    assert attrs["target_column"] == 2


def test_stale_requested_command_is_rejected_and_never_becomes_fixation():
    substrate, agent, native = _load_saccade()
    controller = _enable(native, substrate, "SaccadeController")
    native.set_attr(agent, "vision_settled_epoch", 7)
    command = substrate.add_node("EyeMotorCommand", {
        "source_epoch": 6, "target_column": 4, "target_row": 2,
        "status": "requested", "kind": "saccade",
    })
    substrate.add_edge(controller, "has_eye_motor_command", command)
    native.run_rules()
    assert substrate.node(command)["attrs"]["status"] == "rejected"
    assert substrate.node(command)["attrs"]["reason"] == "stale_source_epoch"
    assert list(substrate.nodes("Fixation")) == []
    assert substrate.node(agent)["attrs"]["eye_motor_active"] == 0


def test_presaccadic_fixation_confirms_only_after_later_sensor_settlement():
    substrate, agent, native = _load_saccade()
    controller = _enable(native, substrate, "SaccadeController")
    _attention(native, agent, epoch=7, col=5, row=4)
    native.run_rules()
    (fixation,) = list(substrate.nodes("Fixation"))
    assert substrate.node(fixation)["attrs"]["confirmed"] == 0

    native.set_attr(agent, "vision_settled_epoch", 8)
    native.run_rules()
    attrs = substrate.node(fixation)["attrs"]
    assert attrs["confirmed"] == 1
    assert attrs["confirmed_epoch"] == 8
    assert attrs["status"] == "confirmed"
    assert substrate.node(controller)["attrs"]["current_column"] == 5
    assert substrate.node(controller)["attrs"]["current_row"] == 4
    agent_attrs = substrate.node(agent)["attrs"]
    assert agent_attrs["eye_motor_active"] == 0
    assert agent_attrs["eye_motor_status"] == "fixation_confirmed"


def _load_memory():
    return _load(
        "retinal_focus_control",
        "optic_flow_spatial_grounding",
        "saccade_motor_control",
        "transsaccadic_feature_memory",
    )


def _confirmed_fixation(substrate, agent, *, epoch, col=5, row=4):
    fixation = substrate.add_node("Fixation", {
        "source_epoch": epoch - 1, "confirmed_epoch": epoch,
        "target_column": col, "target_row": row,
        "status": "confirmed", "confirmed": 1.0,
    })
    substrate.add_edge(agent, "has_fixation", fixation)
    return fixation


def _range_evidence(substrate, agent, *, epoch, sigma=2.0,
                    x=120.0, y=50.0, col=5, row=4, confidence=0.9):
    evidence = substrate.add_node("OpticRangeEvidence", {
        "sensor_epoch": epoch, "column_index": col, "row_index": row,
        "x_world": x, "y_world": y,
        "range_sigma_world": sigma, "confidence": confidence,
        "occupancy_commit": 0.0,
    })
    substrate.add_edge(agent, "holds_spatial_evidence", evidence)
    return evidence


def _assessment_for(substrate, agent, fixation):
    for assessment in substrate.neighbours(
            agent, "assesses_transsaccadic_memory"):
        if fixation in substrate.neighbours(
                assessment, "based_on_fixation"):
            return substrate.node(assessment)["attrs"]
    raise AssertionError("no assessment for fixation")


def test_confirmed_fixation_mints_world_tile_with_uncertainty_and_feature():
    substrate, agent, native = _load_memory()
    _enable(native, substrate, "TranssaccadicMemoryParams")
    native.set_attr(agent, "vision_settled_epoch", 8)
    fixation = _confirmed_fixation(substrate, agent, epoch=8)
    evidence = _range_evidence(substrate, agent, epoch=8)
    held = substrate.add_node("HeldPredictionResidual", {
        "sensor_epoch": 8, "prediction_residual_quanta": 7,
        "observed_quanta": 30.0,
    })
    substrate.add_edge(evidence, "supported_by_photometry", held)
    native.run_rules()

    (tile,) = list(substrate.nodes("VisualTile"))
    attrs = substrate.node(tile)["attrs"]
    assert attrs["world_x"] == 120.0 and attrs["world_y"] == 50.0
    assert attrs["world_relative"] == 1
    assert attrs["occupancy_commit"] == 0
    assert attrs["registration_uncertainty_world"] == 2.0
    assert attrs["freshness"] == pytest.approx(1 / 3)
    assert attrs["observation_count"] == 1
    assert attrs["prediction_residual_quanta"] == 7
    assert attrs["feature_unit"] == "photon_count_quanta"
    assert _assessment_for(
        substrate, agent, fixation)["status"] == "updated"


def test_revisit_updates_same_tile_then_freshness_decays_and_stales():
    substrate, agent, native = _load_memory()
    params = _enable(native, substrate, "TranssaccadicMemoryParams")
    native.set_attr(params, "max_tile_age_epochs", 3)
    native.set_attr(agent, "vision_settled_epoch", 8)
    _confirmed_fixation(substrate, agent, epoch=8)
    _range_evidence(substrate, agent, epoch=8, sigma=4.0)
    native.run_rules()
    (tile,) = list(substrate.nodes("VisualTile"))

    native.set_attr(agent, "vision_settled_epoch", 9)
    fixation2 = _confirmed_fixation(substrate, agent, epoch=9)
    _range_evidence(substrate, agent, epoch=9, sigma=2.0)
    native.run_rules()
    assert list(substrate.nodes("VisualTile")) == [tile]
    attrs = substrate.node(tile)["attrs"]
    assert attrs["last_observed_epoch"] == 9
    assert attrs["observation_count"] == 2
    assert attrs["registration_uncertainty_world"] == 2.0
    assert attrs["freshness"] == pytest.approx(1 / 3)
    assert _assessment_for(
        substrate, agent, fixation2)["status"] == "updated"

    native.set_attr(agent, "vision_settled_epoch", 13)
    native.run_rules()
    attrs = substrate.node(tile)["attrs"]
    assert attrs["freshness"] == pytest.approx(1 / 7)
    assert attrs["status"] == "stale"


@pytest.mark.parametrize(
    ("evidence_epoch", "sigma", "reason"),
    [
        # optic_flow_spatial_grounding retires stale evidence before this
        # consumer can bind it, so absence is the honest downstream refusal.
        (7, 2.0, "no_current_world_evidence"),
        (8, 100.0, "uncertain_world_registration"),
    ],
)
def test_stale_or_uncertain_registration_refuses_visual_tile(
        evidence_epoch, sigma, reason):
    substrate, agent, native = _load_memory()
    _enable(native, substrate, "TranssaccadicMemoryParams")
    native.set_attr(agent, "vision_settled_epoch", 8)
    fixation = _confirmed_fixation(substrate, agent, epoch=8)
    _range_evidence(substrate, agent, epoch=evidence_epoch, sigma=sigma)
    native.run_rules()
    assert list(substrate.nodes("VisualTile")) == []
    assessment = _assessment_for(substrate, agent, fixation)
    assert assessment["status"] == "refused"
    assert assessment["reason"] == reason


def test_memory_slice_default_off_and_source_audit():
    substrate, agent, native = _load_memory()
    native.set_attr(agent, "vision_settled_epoch", 8)
    _confirmed_fixation(substrate, agent, epoch=8)
    _range_evidence(substrate, agent, epoch=8)
    native.run_rules()
    assert list(substrate.nodes("VisualTile")) == []
    assert list(substrate.nodes("TranssaccadicMemoryAssessment")) == []

    for seed in ("saccade_motor_control", "transsaccadic_feature_memory"):
        manifest = manifest_for(seed)
        text = json.dumps(manifest).lower()
        assert manifest["nodes"][0]["attrs"]["enabled"] == 0.0
        assert "doom" not in text
        assert "depth_buffer" not in text and "labels_buffer" not in text
        assert "screen_buffer" not in text and "raw_pixel" not in text
        assert "python" not in text
