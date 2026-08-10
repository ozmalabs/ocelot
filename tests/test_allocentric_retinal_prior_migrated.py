import math

import pytest

import substrate_rs
from domains.photon_eye import GraphEye


def _native_projection(**overrides):
    args = {
        "surface_x": [10.0, 4.0],
        "surface_y": [0.0, 0.0],
        "surface_z": [0.0, 0.0],
        "surface_radius": [0.1, 0.1],
        "surface_value": [30.0, 90.0],
        "surface_confidence": [12.0, 55.0],
        "pose_x": 0.0,
        "pose_y": 0.0,
        "pose_z": 0.0,
        "pose_yaw": 0.0,
        "pose_pitch": 0.0,
        "receptor_az": [0.0, 1.0],
        "receptor_el": [0.0, 0.0],
        "receptor_width": [0.1, 0.1],
        "receptor_height": [0.1, 0.1],
    }
    args.update(overrides)
    return substrate_rs._native.allocentric_retinal_projection(**args)


def test_native_projection_nearest_surface_occludes_farther():
    values, confidence, present, source = _native_projection()
    assert values == [90.0, 0.0]
    assert confidence == [55.0, 0.0]
    assert present == [True, False]
    assert source == [1, -1]


def test_native_projection_applies_pose_and_keeps_unknown_absent():
    values, confidence, present, source = _native_projection(
        surface_x=[0.0],
        surface_y=[10.0],
        surface_z=[10.0],
        surface_radius=[0.01],
        surface_value=[77.0],
        surface_confidence=[8.0],
        pose_yaw=math.pi / 2,
        pose_pitch=math.pi / 4,
        receptor_az=[0.0, -1.0],
        receptor_el=[0.0, 0.0],
        receptor_width=[0.05, 0.05],
        receptor_height=[0.05, 0.05],
    )
    assert (values, confidence, present, source) == (
        [77.0, 0.0], [8.0, 0.0], [True, False], [0, -1])


def test_native_projection_rejects_mismatched_surface_vectors():
    with pytest.raises(ValueError, match="surface vectors"):
        _native_projection(surface_y=[])


def _eye(*, held=True, explicit=True):
    context = {
        "retina_2d": True,
        "synchronous": True,
        "retina_accel": True,
    }
    if held:
        context["held_prediction"] = "decay"
    if explicit:
        context["retinal_layout"] = "uniform"
    return GraphEye(n_az=3, n_el=1, context=context).build()


def test_grapheye_projection_uses_current_explicit_receptors():
    eye = _eye()
    projected = eye.project_allocentric_surfaces_2d(
        surface_x=[5.0],
        surface_y=[0.0],
        surface_z=[0.0],
        surface_radius=[0.1],
        surface_value=[123.0],
        surface_confidence=[900.0],
        pose_x=0.0,
        pose_y=0.0,
        pose_z=0.0,
        pose_yaw=0.0,
        pose_pitch=0.0,
    )
    # Three receptors span -30, 0, +30 degrees; the surface is straight ahead.
    assert projected == {
        "values": [0.0, 123.0, 0.0],
        "confidences": [0.0, 900.0, 0.0],
        "present": [False, True, False],
        "source_indices": [-1, 0, -1],
    }


def test_prior_hook_copies_only_present_state_without_policy():
    eye = _eye()
    before = [
        dict(eye.substrate.node(node)["attrs"])
        for node in eye._held_surface_cells
    ]
    copied = eye.ingest_allocentric_prior_2d(
        [0.0, 123.0, 0.0],
        [0.0, 777.0, 0.0],
        [False, True, False],
        source_epoch=0,
        source_indices=[-1, 4, -1],
    )
    assert copied == 1
    after = [
        dict(eye.substrate.node(node)["attrs"])
        for node in eye._held_surface_cells
    ]
    assert after[0] == before[0]
    assert after[2] == before[2]
    assert after[1]["value"] == 123.0
    assert after[1]["freshness"] == 777.0
    assert after[1]["prior_value"] == 123.0
    assert after[1]["prior_confidence"] == 777.0
    assert after[1]["prior_source_index"] == 4
    assert after[1]["obs"] == before[1]["obs"]
    prior = eye.substrate.nodes("AllocentricRetinalPrior")
    assert len(prior) == 1
    assert eye.substrate.node(prior[0])["attrs"]["predicted_count"] == 1
    assert eye.substrate.neighbours(
        prior[0], "predicts_held_surface") == [eye._held_surface_cells[1]]


def test_photon_evidence_meets_the_prior_in_existing_graph_rules():
    eye = _eye()
    eye.ingest_allocentric_prior_2d(
        [0.0, 100.0, 0.0], [0.0, 1024.0, 0.0],
        [False, True, False], source_epoch=0)
    eye.submit_photons_2d([
        {"col": 1, "row": 0, "wavelength_nm": 498.0, "count": 160},
    ])
    eye.substrate._inner.run_rules()
    held = eye.substrate.node(eye._held_surface_cells[1])["attrs"]
    assert held["obs"] == 160.15  # photon count plus the rod's declared dark current
    assert held["residual"] == 60
    assert held["epoch"] == 1


def test_prior_hook_is_exact_noop_without_held_prediction_apparatus():
    eye = _eye(held=False)
    nodes, edges = eye.substrate.node_count(), eye.substrate.edge_count()
    assert eye.ingest_allocentric_prior_2d(
        [1.0, 2.0, 3.0], [4.0, 5.0, 6.0],
        [True, True, True], source_epoch=0) == 0
    assert eye.substrate.node_count() == nodes
    assert eye.substrate.edge_count() == edges
