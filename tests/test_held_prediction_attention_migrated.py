"""Held-prediction residuals become behaviorally load-bearing graph attention."""
from __future__ import annotations

import json
import math
import time

import numpy as np
import pytest

pytest.importorskip("substrate_rs")

from domains import doom_photon_world as dpw  # mechanical packet conversion
from domains import reflective_faculty as rf
from substrate.boot_core import boot_core
from substrate.seed_loader import manifest_for
from substrate.world_adapter import WorldAdapter


ATTENTION_SEEDS = (
    "fovea_salience_bridge",
    "retinal_attention_graph",
    "held_prediction_attention",
)


def _boot(epoch=4, my_angle=0.0):
    substrate, agent = boot_core(seeds=())
    native = rf._native_eval2(substrate)
    for seed in ATTENTION_SEEDS:
        native.load_seed_manifest(manifest_for(seed), agent)
    native.set_attr(agent, "vision_settled_epoch", epoch)
    native.set_attr(agent, "my_angle", my_angle)
    return substrate, agent, native


def _held(
    substrate,
    agent,
    *,
    epoch,
    col,
    row,
    residual,
    gaze_az=0.0,
    gaze_el=0.0,
):
    node = substrate.add_node(
        "HeldPredictionResidual",
        {
            "column_index": col,
            "row_index": row,
            "cell_index": row * 20 + col,
            "n_az": 20,
            "n_el": 15,
            "gaze_az": gaze_az,
            "gaze_el": gaze_el,
            "sensor_epoch": epoch,
            "prediction_epoch": epoch,
            "prediction_residual_quanta": residual,
            "observed_quanta": 30.5,
            "held_value_quanta": 27.25,
            "freshness_scale2": 512,
            "needs_attention": 0,
            "residual_unit": "photon_count_quanta",
        },
    )
    substrate.add_edge(agent, "perceives_prediction_residual", node)
    return node


def _motion(substrate, agent, *, epoch, col, row, residual, gaze_az):
    node = substrate.add_node(
        "RetinalSalience",
        {
            "column_index": col,
            "row_index": row,
            "n_az": 20,
            "n_el": 15,
            "gaze_az": gaze_az,
            "gaze_el": 0.0,
            "sensor_epoch": epoch,
            "raw_salience": residual,
            "residual_salience": residual,
        },
    )
    substrate.add_edge(agent, "perceives_salience", node)
    return node


def test_unique_held_residual_drives_motor_attention_after_motion_refuses():
    substrate, agent, native = _boot(epoch=4, my_angle=90.0)
    for col, residual in ((2, 0), (7, 2), (16, 20)):
        _held(
            substrate,
            agent,
            epoch=4,
            col=col,
            row=7,
            residual=residual,
            gaze_az=math.radians(col - 10),
        )

    native.run_rules()

    attrs = substrate.node(agent)["attrs"]
    assert attrs["held_attention_refused"] == 0.0
    assert attrs["attention_refused"] == 0.0
    assert attrs["attention_evidence_kind"] == "held_prediction_residual"
    assert attrs["attention_prediction_residual_quanta"] == 20
    assert attrs["attention_salience"] == pytest.approx(20.0 / (22.0 / 3.0))
    assert attrs["attention_column_index"] == 16
    heading = math.radians(90.0) + math.radians(6.0)
    assert attrs["attention_x"] == pytest.approx(math.cos(heading))
    assert attrs["attention_y"] == pytest.approx(math.sin(heading))
    assert all(
        substrate.node(node)["attrs"]["attention_candidate_epoch"] == 4
        for node in substrate.neighbours(agent, "perceives_prediction_residual")
    )


def test_unique_motion_winner_has_precedence_over_held_prediction_route():
    substrate, agent, native = _boot(epoch=8, my_angle=0.0)
    _motion(
        substrate,
        agent,
        epoch=8,
        col=3,
        row=5,
        residual=4.0,
        gaze_az=math.radians(-25.0),
    )
    _held(
        substrate,
        agent,
        epoch=8,
        col=17,
        row=9,
        residual=100,
        gaze_az=math.radians(30.0),
    )

    native.run_rules()

    attrs = substrate.node(agent)["attrs"]
    assert attrs["held_attention_refused"] == 0.0  # held route resolved
    assert attrs["attention_refused"] == 0.0
    assert attrs["attention_column_index"] == 3
    assert attrs["attention_az"] == pytest.approx(math.radians(-25.0))
    assert "attention_prediction_residual_quanta" not in attrs


@pytest.mark.parametrize("residuals", [(0, 0), (12, 12)])
def test_zero_field_and_exact_tie_refuse_without_stale_direction(residuals):
    substrate, agent, native = _boot(epoch=6, my_angle=30.0)
    native.set_attr(agent, "attention_x", 99.0)
    native.set_attr(agent, "attention_salience", 99.0)
    for col, residual in zip((4, 15), residuals):
        _held(
            substrate,
            agent,
            epoch=6,
            col=col,
            row=7,
            residual=residual,
        )

    native.run_rules()

    attrs = substrate.node(agent)["attrs"]
    assert attrs["held_attention_refused"] == 1.0
    assert attrs["attention_refused"] == 1.0
    assert attrs["attention_x"] == 0.0
    assert attrs["attention_salience"] == 0.0


def test_20x15_projection_is_complete_epoch_bounded_and_behavioral():
    calibration = {
        "retina_2d": True,
        "retina_n_az": 20,
        "retina_n_el": 15,
        "synchronous": True,
        "retina_accel": True,
        "event_native": True,
        "visual_motion": False,
        "visual_salience": False,
        "held_prediction": "decay",
    }
    adapter = WorldAdapter(seeds=())
    try:
        for seed in ATTENTION_SEEDS:
            adapter.inner.load_seed_manifest(manifest_for(seed), adapter.agent)
        adapter.inner.set_attr(adapter.agent, "my_angle", 0.0)

        counts = np.full((15, 20), 30, dtype=np.int64)
        adapter.update_vision(
            calibration=calibration,
            photon_packets=dpw.packets_from_counts(counts),
            photon_counts=counts,
            photon_epoch=1,
        )
        first = set(
            adapter.inner.neighbours(
                adapter.agent, "perceives_prediction_residual"
            )
        )
        assert len(first) == 20 * 15
        assert all(
            adapter.s.node(node)["type"] == "HeldPredictionResidual"
            for node in first
        )
        assert all(
            adapter.s.node(node)["attrs"]["residual_unit"]
            == "photon_count_quanta"
            for node in first
        )
        assert all(
            isinstance(adapter.s.node(node)["attrs"]["held_value_quanta"], float)
            for node in first
        )
        adapter.inner.run_rules()
        assert adapter.s.node(adapter.agent)["attrs"]["attention_refused"] == 1.0
        first_node_count = adapter.s.node_count()
        first_edge_count = adapter.s.edge_count()

        changed = counts.copy()
        changed[7, 16] = 200
        started = time.perf_counter()
        adapter.update_vision(
            calibration=calibration,
            photon_packets=dpw.packets_from_counts(changed),
            photon_counts=changed,
            photon_epoch=2,
        )
        adapter.inner.run_rules()
        elapsed = time.perf_counter() - started

        second = set(
            adapter.inner.neighbours(
                adapter.agent, "perceives_prediction_residual"
            )
        )
        assert len(second) == 20 * 15
        assert {
            adapter.s.node(node)["attrs"]["sensor_epoch"] for node in second
        } == {2}
        # Native graph slots may reuse deleted NodeIDs, so bounded counts and
        # absence of epoch-1 projections are the lifecycle-observable contract.
        assert adapter.s.node_count() <= first_node_count + 2
        assert adapter.s.edge_count() <= first_edge_count + 2
        held_candidates = [
            node
            for node in adapter.s.nodes("FoveaCandidate")
            if adapter.s.node(node)["attrs"].get("purpose")
            == "held_prediction_attention"
        ]
        assert len(held_candidates) == 20 * 15
        assert {
            adapter.s.node(node)["attrs"]["candidate_epoch"]
            for node in held_candidates
        } == {2}

        attrs = adapter.s.node(adapter.agent)["attrs"]
        assert attrs["attention_evidence_kind"] == "held_prediction_residual"
        assert attrs["attention_column_index"] == 16
        assert attrs["attention_row_index"] == 7
        assert attrs["attention_prediction_residual_quanta"] > 0
        assert attrs["attention_salience"] > 2.0
        # Observed locally as a performance guardrail, not a hard realtime
        # contract. The semantic assertions above remain the test's gate.
        assert elapsed < 2.0
    finally:
        adapter.close()


def test_seed_is_generic_and_keeps_physical_units_distinct():
    manifest = manifest_for("held_prediction_attention")
    text = json.dumps(manifest).lower()
    assert manifest["depends_on"] == ["retinal_attention_graph"]
    assert "doom" not in text
    assert "photon_count_quanta" in text
    assert "cells/epoch" in text
    assert '"argminunique"' in text
