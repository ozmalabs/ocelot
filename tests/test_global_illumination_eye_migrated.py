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
        adapter.s, adapter.agent, ["global_illumination_eye"])
    (params,) = adapter.s.nodes("GlobalIlluminationParams")
    adapter.inner.set_attr(params, "enabled", 1.0)
    return adapter


def _evidence(adapter, epoch, foveal_mean, global_mean, *, with_global=True):
    exposure = adapter.s.add_node("VisualIlluminationExposure", {
        "source_epoch": epoch,
        "status": "raw",
        "unit": "photon_count_quanta",
        "provenance_kind": "observed",
    })
    foveal = adapter.s.add_node("FovealLuminanceEvidence", {
        "source_epoch": epoch,
        "mean_quanta": float(foveal_mean),
        "confidence": 0.95,
        "sample_count": 64,
        "pathway": "dense_high_acuity_fovea",
        "field_scope": "fixated_aperture",
        "unit": "photon_count_quanta",
        "provenance_kind": "observed",
    })
    adapter.inner.add_edge_unchecked(
        adapter.agent, "has_visual_illumination_exposure", exposure)
    adapter.inner.add_edge_unchecked(
        exposure, "has_foveal_luminance_evidence", foveal)
    global_evidence = None
    if with_global:
        global_evidence = adapter.s.add_node("GlobalLuminanceEvidence", {
            "source_epoch": epoch,
            "mean_quanta": float(global_mean),
            "confidence": 0.8,
            "sample_count": 24,
            "pathway": "sparse_broad_field_scout",
            "field_scope": "whole_visual_field",
            "unit": "photon_count_quanta",
            "provenance_kind": "observed",
        })
        adapter.inner.add_edge_unchecked(
            exposure, "has_global_luminance_evidence", global_evidence)
    return exposure, foveal, global_evidence


def test_foveal_lead_waits_for_global_evidence_then_reconditions_whole_field():
    adapter = _adapter()
    try:
        cells = []
        for index, value in enumerate((40.0, 70.0, 110.0)):
            cell = adapter.s.add_node("AllocentricWorldViewCell", {
                "world_x": float(index * 64),
                "world_y": 128.0,
                "surface_value": value,
                "surface_value_epoch": 1,
                "surface_value_status": "supported",
                "surface_value_source": "unique_current_held_photometry",
                "surface_value_unit": "photon_count_quanta",
                "confidence": 0.9,
            })
            adapter.inner.add_edge_unchecked(
                adapter.agent, "holds_world_view_cell", cell)
            cells.append(cell)

        _evidence(adapter, 1, 50.0, 40.0)
        adapter.inner.run_rules()
        baseline_values = [
            dict(adapter.s.node(cell)["attrs"]) for cell in cells]
        assert all(
            attrs["surface_illumination_level"] == 1.0
            for attrs in baseline_values)

        exposure, _, _ = _evidence(
            adapter, 2, 100.0, 80.0, with_global=False)
        adapter.inner.run_rules()

        (provisional,) = adapter.inner.neighbours(
            exposure, "has_provisional_illumination_hypothesis")
        assert adapter.s.node(provisional)["attrs"]["phase"] == (
            "provisional_foveal")
        assert adapter.s.node(adapter.agent)["attrs"][
            "illumination_hypothesis_epoch"] == 1
        assert all(
            "illumination_conditioned_value"
            not in adapter.s.node(cell)["attrs"]
            for cell in cells)

        global_evidence = adapter.s.add_node("GlobalLuminanceEvidence", {
            "source_epoch": 2,
            "mean_quanta": 80.0,
            "confidence": 0.8,
            "sample_count": 24,
            "pathway": "sparse_broad_field_scout",
            "field_scope": "whole_visual_field",
            "unit": "photon_count_quanta",
            "provenance_kind": "observed",
        })
        adapter.inner.add_edge_unchecked(
            exposure, "has_global_luminance_evidence", global_evidence)
        adapter.inner.run_rules()

        hypothesis = adapter.s.node(provisional)["attrs"]
        assert hypothesis["phase"] == "global_confirmed"
        assert hypothesis["gain_estimate"] == pytest.approx(2.0)
        assert hypothesis["provenance_kind"] == "predicted"
        for before, cell in zip(baseline_values, cells):
            after = adapter.s.node(cell)["attrs"]
            assert after["illumination_conditioned_value"] == pytest.approx(
                before["surface_value"] * 2.0)
            assert after["illumination_prediction_provenance"] == (
                "predicted_from_global_illumination_prior")
            assert adapter.inner.has_edge(
                cell, "appearance_predicted_by", provisional)
            # Bottom-up photometry and its provenance remain facts, not
            # rewritten guesses.
            assert after["surface_value"] == before["surface_value"]
            assert after["surface_value_source"] == before[
                "surface_value_source"]
            assert after["surface_value_epoch"] == before[
                "surface_value_epoch"]
            assert after["surface_value_unit"] == before["surface_value_unit"]
    finally:
        adapter.close()


def test_foveal_only_brightness_change_is_explicitly_refused():
    adapter = _adapter()
    try:
        cell = adapter.s.add_node("AllocentricWorldViewCell", {
            "world_x": 0.0,
            "world_y": 64.0,
            "surface_value": 60.0,
            "surface_value_epoch": 1,
            "surface_value_status": "supported",
            "surface_value_source": "unique_current_held_photometry",
            "surface_value_unit": "photon_count_quanta",
            "confidence": 0.9,
        })
        adapter.inner.add_edge_unchecked(
            adapter.agent, "holds_world_view_cell", cell)
        _evidence(adapter, 1, 50.0, 50.0)
        adapter.inner.run_rules()
        exposure, _, _ = _evidence(adapter, 2, 100.0, 50.0)
        adapter.inner.run_rules()

        (hypothesis,) = adapter.inner.neighbours(
            exposure, "has_provisional_illumination_hypothesis")
        attrs = adapter.s.node(hypothesis)["attrs"]
        assert attrs["phase"] == "refused_nonuniform_change"
        assert attrs["field_scope"] == "refused_not_global"
        assert "illumination_conditioned_value" not in adapter.s.node(
            cell)["attrs"]
    finally:
        adapter.close()


@_requires_optional('cv2')
def test_split_eye_publishes_bounded_observed_evidence_only_when_enabled():
    adapter = _adapter()
    calibration = {
        "retina_2d": True,
        "retina_n_az": 8,
        "retina_n_el": 9,
        "synchronous": True,
        "retina_accel": True,
        "retinal_layout": "foveated",
        "event_pathway": "periphery",
        "split_foveated_pathways": True,
        "fovea_width": 8,
        "fovea_height": 8,
        "peripheral_rings": 1,
        "peripheral_spokes": 8,
        "source_width": 32,
        "source_height": 32,
    }
    try:
        for epoch, level in ((1, 30), (2, 60)):
            counts = np.full((9, 8), level, dtype=np.int64)
            adapter.update_vision(
                calibration=calibration,
                photon_packets=dpw.packets_from_counts(counts),
                photon_counts=counts,
                photon_epoch=epoch,
            )
            adapter.inner.run_rules()

        assert len(adapter.s.nodes("VisualIlluminationExposure")) == 1
        assert len(adapter.s.nodes("FovealLuminanceEvidence")) == 1
        assert len(adapter.s.nodes("GlobalLuminanceEvidence")) == 1
        (foveal,) = adapter.s.nodes("FovealLuminanceEvidence")
        (global_evidence,) = adapter.s.nodes("GlobalLuminanceEvidence")
        assert adapter.s.node(foveal)["attrs"]["mean_quanta"] == 60.0
        assert adapter.s.node(global_evidence)["attrs"]["mean_quanta"] == 60.0
        assert adapter.s.node(foveal)["attrs"]["provenance_kind"] == "observed"
        assert adapter.s.node(global_evidence)["attrs"][
            "provenance_kind"] == "observed"
    finally:
        adapter.close()


def test_whole_field_reconditioning_has_bounded_fixpoint_depth():
    adapter = _adapter()
    try:
        cells = []
        for index in range(1000):
            cell = adapter.s.add_node("AllocentricWorldViewCell", {
                "world_x": float(index),
                "world_y": 0.0,
                "surface_value": 50.0,
                "surface_value_epoch": 1,
                "surface_value_status": "supported",
                "surface_value_source": "measured_test_surface",
                "surface_value_unit": "photon_count_quanta",
                "confidence": 1.0,
            })
            adapter.inner.add_edge_unchecked(
                adapter.agent, "holds_world_view_cell", cell)
            cells.append(cell)

        _evidence(adapter, 1, 50.0, 50.0)
        baseline_steps = adapter.inner.run_rules()
        _evidence(adapter, 2, 100.0, 100.0)
        change_steps = adapter.inner.run_rules()

        assert baseline_steps <= 8
        assert change_steps <= 8
        assert sum(
            adapter.s.node(cell)["attrs"].get(
                "illumination_prediction_epoch") == 2
            for cell in cells) == 1000
        assert len(adapter.s.nodes("GlobalIlluminationHypothesis")) == 1
    finally:
        adapter.close()
