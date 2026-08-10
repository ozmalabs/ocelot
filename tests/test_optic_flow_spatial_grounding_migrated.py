"""Oracle-free graph-native optic-flow spatial grounding.

The faculty is deliberately evidence-only: it estimates range-bearing surface
support from rigid retinal flow plus efference copy, carries uncertainty, and
refuses static, rotation-confounded, and non-rigid cases.  It never writes an
occupancy cell.
"""
from __future__ import annotations

import inspect
import json
import math
import os
import sys

import pytest

pytest.importorskip("substrate_rs")

from substrate.world_adapter import WorldAdapter  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEED = os.path.join(ROOT, "seeds", "optic_flow_spatial_grounding.json")
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)


def _boot(*, epoch=7, translation=4.0, rotation=0.0,
          pose=(100.0, 50.0, 0.0), focal=10.0, source_delta=1):
    wa = WorldAdapter(seeds=())
    wa.inner.load_seed_manifest(json.load(open(SEED)), wa.agent)
    attrs = {
        "vision_settled_epoch": epoch,
        "optic_source_epoch_delta": source_delta,
        "optic_translation_world": translation * source_delta,
        "optic_translation_world_per_source_epoch": translation,
        "optic_rotation_deg": rotation * source_delta,
        "optic_rotation_deg_per_source_epoch": rotation,
        "optic_pose_x_world": pose[0],
        "optic_pose_y_world": pose[1],
        "optic_pose_angle_deg": pose[2],
        "optic_focal_cells": focal,
    }
    for key, value in attrs.items():
        wa.inner.set_attr(wa.agent, key, value)
    return wa


def _motion(wa, *, epoch=7, coherence=0.9, speed=2.0):
    node = wa.s.add_node("RetinalMotionPercept", {
        "sensor_epoch": epoch, "coherence": coherence, "speed": speed,
        "v_az": speed, "v_el": 0.0,
    })
    wa.inner.add_edge_unchecked(wa.agent, "perceives_motion", node)
    return node


def _salience(wa, *, epoch=7, col=5, row=3, gaze=0.0,
              raw=2.0, residual=0.0):
    node = wa.s.add_node("RetinalSalience", {
        "sensor_epoch": epoch, "column_index": col, "row_index": row,
        "gaze_az": gaze, "raw_salience": raw,
        "residual_salience": residual,
    })
    wa.inner.add_edge_unchecked(wa.agent, "perceives_salience", node)
    return node


def _assessment(wa):
    nodes = wa.inner.neighbours(wa.agent, "assesses_optic_flow")
    assert len(nodes) == 1
    return wa.s.node(nodes[0])["attrs"]


def _evidence(wa):
    return [
        wa.s.node(node)["attrs"]
        for node in wa.inner.neighbours(wa.agent, "holds_spatial_evidence")
    ]


def test_translation_mints_uncertain_world_registered_surface_evidence():
    wa = _boot(source_delta=3, translation=4.0, focal=10.0)
    try:
        _motion(wa, coherence=0.9)
        salience = _salience(wa, raw=2.0, residual=0.0)
        held = wa.s.add_node("HeldPredictionResidual", {
            "sensor_epoch": 7, "column_index": 5, "row_index": 3,
            "prediction_residual_quanta": 9, "observed_quanta": 30.0,
        })
        wa.inner.add_edge_unchecked(
            wa.agent, "perceives_prediction_residual", held)
        wa.inner.run_rules()

        (evidence,) = _evidence(wa)
        # (4 world/source-epoch * 10 focal cells) / 2 cells/source-epoch.
        assert evidence["range_world"] == pytest.approx(20.0)
        assert evidence["x_world"] == pytest.approx(120.0)
        assert evidence["y_world"] == pytest.approx(50.0)
        assert evidence["range_sigma_world"] == pytest.approx(2.0)
        assert evidence["confidence"] == pytest.approx(0.9)
        assert evidence["confidence_kind"] == "rigid_flow_fit_conditional"
        assert evidence["source_epoch_delta"] == 3
        assert evidence["flow_unit"] == "retinal_cells_per_source_epoch"
        assert evidence["range_unit"] == "world_units"
        assert evidence["range_sigma_kind"] == "flow_fit_lower_bound"
        assert evidence["topology_kind"] == "visible_surface_support"
        assert evidence["occupancy_commit"] == 0
        assert evidence["rigidity_scope"] == "dominant_field_assumption"
        assert evidence["dominant_motion_ambiguity"] == 1
        assert evidence["prediction_residual_quanta"] == 9
        assert evidence["photometry_unit"] == "photon_count_quanta"
        assert wa.inner.neighbours(
            wa.inner.neighbours(wa.agent, "holds_spatial_evidence")[0],
            "based_on_salience") == [salience]
        assert _assessment(wa)["status"] == "supported"
    finally:
        wa.close()


def test_dropped_source_epochs_do_not_compress_range_units():
    """Equal translation/source-epoch and flow/source-epoch give equal range,
    whether observations are consecutive or three source epochs apart."""
    ranges = []
    for source_delta, total_translation in ((1, 4.0), (3, 12.0)):
        wa = _boot(source_delta=source_delta,
                   translation=total_translation / source_delta)
        try:
            _motion(wa)
            _salience(wa)
            wa.inner.run_rules()
            ranges.append(_evidence(wa)[0]["range_world"])
        finally:
            wa.close()
    assert ranges == pytest.approx([20.0, 20.0])


def test_static_view_refuses_range_instead_of_inventing_topology():
    wa = _boot(translation=0.0)
    try:
        wa.inner.run_rules()
        assert _evidence(wa) == []
        assessment = _assessment(wa)
        assert assessment["status"] == "refused"
        assert assessment["reason"] == "no_translation"
        assert wa.s.nodes("Cell") == []
        assert wa.s.nodes("ObsCell") == []
        assert wa.s.nodes("AlloCell") == []
    finally:
        wa.close()


def test_self_rotation_refuses_uncompensated_flow():
    wa = _boot(translation=4.0, rotation=7.0)
    try:
        _motion(wa)
        _salience(wa, residual=0.0)
        wa.inner.run_rules()
        assert _evidence(wa) == []
        assert _assessment(wa)["reason"] == "rotation_confounded"
    finally:
        wa.close()


def test_adversarial_independent_mover_is_not_promoted_to_range():
    wa = _boot(translation=4.0, rotation=0.0)
    try:
        _motion(wa, coherence=0.99)
        _salience(wa, raw=3.0, residual=1.0)
        wa.inner.run_rules()
        assert _evidence(wa) == []
        assessment = _assessment(wa)
        assert assessment["status"] == "refused"
        assert assessment["reason"] == "nonrigid_motion"
        assert assessment["has_nonrigid_motion"] == 1
    finally:
        wa.close()


def test_bearing_uses_real_pose_angle_plus_retinal_radians():
    wa = _boot(pose=(10.0, 20.0, 90.0), focal=8.0)
    try:
        _motion(wa)
        _salience(wa, gaze=math.radians(30), raw=2.0)
        wa.inner.run_rules()
        evidence = _evidence(wa)[0]
        assert evidence["bearing_rad"] == pytest.approx(math.radians(120))
        assert evidence["x_world"] == pytest.approx(10.0 - 8.0)
        assert evidence["y_world"] == pytest.approx(
            20.0 + 16.0 * math.sin(math.radians(120)))
    finally:
        wa.close()


def test_packet_ingress_calibrates_focal_length_and_source_gap_mechanically():
    import doom_world as dw

    base = {
        "tic": 1, "ctx": {}, "screen": None,
        "vision_calibration": {
            "photon_sheet": True, "retina_2d": True,
            "retina_n_az": 20, "retina_n_el": 10,
            "fov_h_deg": 60.0, "photon_poisson": False,
            "oracle_buffers": False,
        },
        "vision_photon_counts": [[0] * 20 for _ in range(10)],
    }
    first = dict(base)
    first.update({
        "vision_photon_epoch": 1,
        "body": {"x": 0.0, "y": 0.0, "z": 0.0,
                 "x_bin": 0, "y_bin": 0, "z_bin": 0, "angle": 350.0},
    })
    _sub1, cell, pose = dw.substrate_from_packet(first)
    second = dict(base)
    second.update({
        "tic": 4, "vision_photon_epoch": 4,
        "body": {"x": 12.0, "y": 0.0, "z": 0.0,
                 "x_bin": 0, "y_bin": 0, "z_bin": 0, "angle": 10.0},
    })
    sub2, _cell2, pose2 = dw.substrate_from_packet(
        second, prev_cell=cell, prev_pose=pose)
    cal = sub2.vision_calibration
    assert pose2[-1] == 4
    assert cal["source_epoch_delta"] == 3
    assert cal["efference_translation"] == pytest.approx(12.0)
    assert cal["efference_translation_per_source_epoch"] == pytest.approx(4.0)
    assert cal["efference_rotation_deg"] == pytest.approx(20.0)
    assert cal["efference_rotation_deg_per_source_epoch"] == pytest.approx(
        20.0 / 3.0)
    assert cal["retina_focal_cells"] == pytest.approx(
        10.0 / math.tan(math.radians(30)))


def test_source_audit_has_no_oracle_or_python_spatial_decision():
    manifest = open(SEED).read()
    lowered = manifest.lower()
    for forbidden in (
            "depth_buffer", "labels_buffer", "doomplayer", "zombieman",
            '"add_node", "cell"', '"add_node", "obscell"',
            '"add_node", "allocell"'):
        assert forbidden not in lowered
    assert '"occupancy_commit": 0.0' in manifest
    assert '"oracle_free": 1.0' in manifest

    projection = inspect.getsource(
        WorldAdapter._update_vision_photon_sheet)
    assert "optic_translation_world_per_source_epoch" in projection
    assert "optic_rotation_deg_per_source_epoch" in projection
    assert "optic_focal_cells" in projection
    assert "holds_spatial_evidence" not in projection
    assert "OpticRangeEvidence" not in projection
