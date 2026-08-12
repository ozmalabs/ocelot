"""Live mechanical bridge from graph world-view priors back into GraphEye."""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from domains import doom_photon_world as dpw
from substrate.world_adapter import WorldAdapter

# OPTIONAL DEPENDENCY (red-test triage 2026-08-12): absent 'cv2' is a SKIP with a
# named reason, never a red. See tests/optional_deps.py.
from optional_deps import importorskip as _optional_importorskip  # noqa: E402
_optional_importorskip('cv2')



def test_agent_held_surface_prior_is_rendered_before_bottom_up_evidence():
    adapter = WorldAdapter(seeds=())
    try:
        calibration = {
            "retina_2d": True,
            "retina_n_az": 4,
            "retina_n_el": 2,
            "synchronous": True,
            "retina_accel": True,
            "held_prediction": "decay",
            "fov_h_deg": 90.0,
            "fov_v_deg": 60.0,
        }
        dark = np.zeros((2, 4), dtype=np.int64)
        adapter.update_vision(
            calibration=calibration,
            photon_packets=dpw.packets_from_counts(dark),
            photon_counts=dark,
            photon_epoch=1,
        )
        support = adapter.s.add_node("AllocentricWorldViewCell", {
            "world_x": 128.0,
            "world_y": 0.0,
            "registration_uncertainty_world": 32.0,
            "confidence": 0.75,
            "surface_value": 77.0,
            "surface_value_unit": "photon_count_quanta",
        })
        adapter.inner.add_edge_unchecked(
            adapter.agent, "holds_world_view_cell", support)

        copied = adapter.apply_allocentric_retinal_prior(
            (0.0, 0.0, 0.0, 0.0, 0.0), source_epoch=1)

        assert copied > 0
        held = [
            adapter._eye.substrate.node(node)["attrs"]
            for node in adapter._eye.substrate.nodes("HeldSurfaceCell")
        ]
        predicted = [attrs for attrs in held
                     if attrs.get("prior_source_index") == 0]
        assert predicted
        assert {attrs["prior_value"] for attrs in predicted} == {77.0}
        assert {attrs["prior_confidence"] for attrs in predicted} == {0.75}
        agent_attrs = adapter.s.node(adapter.agent)["attrs"]
        assert agent_attrs["top_down_prior_available_cells"] == 1
        assert agent_attrs["top_down_prior_projected_receptors"] == copied
    finally:
        adapter.close()


def test_unknown_world_view_does_not_invent_retinal_values():
    adapter = WorldAdapter(seeds=())
    try:
        calibration = {
            "retina_2d": True,
            "retina_n_az": 3,
            "retina_n_el": 1,
            "synchronous": True,
            "retina_accel": True,
            "held_prediction": "decay",
        }
        dark = np.zeros((1, 3), dtype=np.int64)
        adapter.update_vision(
            calibration=calibration,
            photon_packets=dpw.packets_from_counts(dark),
            photon_counts=dark,
            photon_epoch=1,
        )
        spatial_only = adapter.s.add_node("AllocentricWorldViewCell", {
            "world_x": 64.0,
            "world_y": 0.0,
            "registration_uncertainty_world": 16.0,
            "confidence": 1.0,
        })
        adapter.inner.add_edge_unchecked(
            adapter.agent, "holds_world_view_cell", spatial_only)

        assert adapter.apply_allocentric_retinal_prior(
            (0.0, 0.0, 0.0, 0.0, 0.0), source_epoch=1) == 0
        assert adapter.s.node(adapter.agent)["attrs"][
            "top_down_prior_projected_receptors"] == 0
    finally:
        adapter.close()
