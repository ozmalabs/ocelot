from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from domains import doom_photon_world as dpw
from substrate.boot_core import load_seeds_into
from substrate.world_adapter import WorldAdapter

# OPTIONAL DEPENDENCIES (red-test triage 2026-08-12): absent 'cv2' is a SKIP with a
# named reason on the tests that need it, never a red. See tests/optional_deps.py.
from optional_deps import requires as _requires_optional  # noqa: E402



def _adapter():
    adapter = WorldAdapter(seeds=())
    load_seeds_into(
        adapter.s, adapter.agent, ["foveal_predictive_coding"])
    return adapter


def _calibration():
    return {
        "retina_2d": True,
        "retina_n_az": 8,
        "retina_n_el": 9,
        "synchronous": True,
        "retina_accel": True,
        "held_prediction": "decay",
        "retinal_layout": "foveated",
        "event_pathway": "periphery",
        "split_foveated_pathways": True,
        "fovea_width": 8,
        "fovea_height": 8,
        "peripheral_rings": 1,
        "peripheral_spokes": 8,
        "source_width": 32,
        "source_height": 32,
        "fov_h_deg": 90.0,
        "fov_v_deg": 60.0,
        "proprio_x_world": 0.0,
        "proprio_y_world": 0.0,
        "proprio_angle_deg": 0.0,
    }


def _counts():
    counts = np.zeros((9, 8), dtype=np.int64)
    counts[:8, :] = np.arange(64).reshape(8, 8) + 40
    return counts


def _expose(adapter, epoch):
    counts = _counts()
    adapter.update_vision(
        calibration=_calibration(),
        photon_packets=dpw.packets_from_counts(counts),
        photon_counts=counts,
        photon_epoch=epoch,
    )
    (exposure,) = adapter.inner.neighbours(
        adapter.agent, "has_foveal_exposure")
    return exposure


@_requires_optional('cv2')
def test_predictive_fovea_is_inert_until_graph_parameter_enables_it():
    adapter = _adapter()
    try:
        exposure = _expose(adapter, 1)

        assert adapter.inner.neighbours(
            exposure, "has_foveal_tile_assessment") == []
        attrs = adapter.s.node(exposure)["attrs"]
        assert "predicted_values" not in attrs
        assert attrs["values"] == tuple(_counts()[:8].reshape(-1))
    finally:
        adapter.close()


@_requires_optional('cv2')
def test_allocentric_latent_decoder_learns_and_reconstruction_error_falls():
    adapter = _adapter()
    try:
        (params,) = adapter.s.nodes("FovealPredictiveParams")
        adapter.inner.set_attr(params, "enabled", 1.0)
        adapter.inner.set_attr(params, "settlement_budget", 1)
        cell = adapter.s.add_node("AllocentricWorldViewCell", {
            "world_x": 128.0,
            "world_y": 0.0,
            "registration_uncertainty_world": 16.0,
            "confidence": 1.0,
        })
        adapter.inner.add_edge_unchecked(
            adapter.agent, "holds_world_view_cell", cell)

        exposure = _expose(adapter, 1)
        attrs = adapter.s.node(exposure)["attrs"]
        assert attrs["predicted_tile_count"] == 0
        assert attrs["predicted_present_tiles"] == (False,)
        assert attrs["predicted_values"] == (0.0,) * 64
        adapter.inner.run_rules()

        cell_attrs = adapter.s.node(cell)["attrs"]
        assert len(cell_attrs["foveal_latent"]) == 4
        assert cell_attrs["foveal_latent_epoch"] == 1

        residuals = []
        for epoch in range(2, 8):
            exposure = _expose(adapter, epoch)
            attrs = adapter.s.node(exposure)["attrs"]
            assert attrs["predicted_tile_count"] == 1
            assert attrs["predicted_present_tiles"] == (True,)
            (assessment,) = adapter.inner.neighbours(
                exposure, "has_foveal_tile_assessment")
            residuals.append(
                adapter.s.node(assessment)["attrs"]["predicted_residual"])
            adapter.inner.run_rules()
            assert adapter.s.node(exposure)["attrs"]["settled_count"] == 1
            assert adapter.s.node(assessment)["attrs"]["status"] == "consumed"
            assert adapter.s.node(assessment)["attrs"][
                "settlement_reason"] == "predicted_residual"

        assert residuals[-1] < residuals[0] * 0.5
    finally:
        adapter.close()


def test_exactly_tied_prediction_residuals_refuse_settlement():
    adapter = _adapter()
    try:
        (params,) = adapter.s.nodes("FovealPredictiveParams")
        adapter.inner.set_attr(params, "enabled", 1.0)
        decoder = next(
            node for node in adapter.s.nodes("ReflexNet")
            if adapter.s.node(node)["attrs"].get("name")
            == "foveal_predictive_decoder")
        exposure = adapter.s.add_node("FovealExposure", {
            "source_epoch": 9,
            "settled_count": 0,
        })
        adapter.inner.add_edge_unchecked(
            adapter.agent, "has_foveal_exposure", exposure)

        assessments = []
        for index, world_y in enumerate((-8.0, 8.0)):
            cell = adapter.s.add_node("AllocentricWorldViewCell", {
                "world_x": 128.0,
                "world_y": world_y,
                "confidence": 1.0,
            })
            adapter.inner.add_edge_unchecked(
                adapter.agent, "holds_world_view_cell", cell)
            assessment = adapter.s.add_node("FovealTileAssessment", {
                "status": "raw",
                "source_epoch": 9,
                "tile_index": index,
                "prediction_present": 1.0,
                "world_grounded": 1.0,
                "world_confidence": 1.0,
                "predicted_residual": 0.25,
                "information_mass": 0.1,
                "latent": [0.2, 0.3, 0.4, 0.5],
                "input_vec": [0.2, 0.3, 0.4, 0.5],
                "target": [0.5] * 64,
            })
            adapter.inner.add_edge_unchecked(
                exposure, "has_foveal_tile_assessment", assessment)
            adapter.inner.add_edge_unchecked(
                assessment, "grounds_in_world_view", cell)
            adapter.inner.add_edge_unchecked(
                assessment, "observes", decoder)
            assessments.append(assessment)

        adapter.inner.run_rules()

        assert adapter.s.node(exposure)["attrs"]["settled_count"] == 0
        assert {
            adapter.s.node(node)["attrs"]["status"]
            for node in assessments
        } == {"raw"}
    finally:
        adapter.close()
