"""Live Doom uses the existing event-native 2-D photon eye, not the 1-D RGB shim."""
from __future__ import annotations

import inspect
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

pytest.importorskip("substrate_rs")

import doom_world as dw  # noqa: E402
from domains import doom_photon_world as dpw  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


def test_doom_photon_sheet_reuses_canonical_converter_and_roundtrips():
    screen = np.zeros((24, 32, 3), dtype=np.uint8)
    screen[:, 12:20] = (200, 100, 50)
    cal = {
        "photon_sheet": True,
        "retina_2d": True,
        "retina_n_az": 8,
        "retina_n_el": 6,
        "photon_gain": 1.0,
        "photon_poisson": False,
        "oracle_buffers": False,
    }

    from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph

    graph = TypedGraph()
    graph._insert_node("Body", {
        "id": "agent_self", "x": 64.0, "y": 128.0, "z": 0.0,
        "x_bin": 1, "y_bin": 2, "z_bin": 0, "angle": 90.0,
    })
    sub = Substrate(graph=graph, checker=ConsistencyChecker(Grammar([])))
    sub.vision_screen = screen
    sub.vision_frame = None
    sub.vision_calibration = dict(cal)
    dw._publish_photon_sheet(sub, screen, cal, epoch=7)

    expected_counts = dpw.photon_counts(
        dpw.luma_grid(screen, 6, 8), rng=None, gain=1.0)
    assert np.array_equal(sub.vision_photon_counts, expected_counts)
    assert sub.vision_photon_packets == dpw.packets_from_counts(expected_counts)

    packet = dw.observation_packet(sub, {"model_tick": 0}, 7)
    rebuilt, _cell, _pose = dw.substrate_from_packet(packet)
    assert np.array_equal(
        rebuilt.vision_photon_counts, sub.vision_photon_counts)
    assert rebuilt.vision_photon_packets == sub.vision_photon_packets
    assert rebuilt.vision_photon_epoch == 7
    assert rebuilt.vision_frame is None
    assert rebuilt.vision_calibration["oracle_buffers"] is False


def test_compact_ipc_sheet_expands_to_the_same_packets_after_roundtrip():
    screen = np.full((24, 32, 3), 96, dtype=np.uint8)
    cal = {
        "photon_sheet": True, "retina_2d": True,
        "retina_n_az": 8, "retina_n_el": 6,
        "photon_poisson": False, "oracle_buffers": False,
    }
    from substrate import ConsistencyChecker, Grammar, Substrate, TypedGraph

    graph = TypedGraph()
    graph._insert_node("Body", {
        "id": "agent_self", "x": 0.0, "y": 0.0, "z": 0.0,
        "x_bin": 0, "y_bin": 0, "z_bin": 0, "angle": 0.0,
    })
    sub = Substrate(graph=graph, checker=ConsistencyChecker(Grammar([])))
    sub.vision_screen = screen
    sub.vision_frame = None
    sub.vision_calibration = dict(cal)
    dw._publish_photon_sheet(
        sub, screen, cal, epoch=3, packetize=False)
    assert sub.vision_photon_packets is None

    packet = dw.observation_packet(sub, {}, 3)
    assert "vision_photon_packets" not in packet
    assert packet["screen"] is None
    rebuilt, _cell, _pose = dw.substrate_from_packet(packet)
    assert rebuilt.vision_screen is None
    assert rebuilt.vision_photon_packets == dpw.packets_from_counts(
        sub.vision_photon_counts)


def test_world_adapter_drives_and_projects_the_real_2d_event_eye():
    cal = {
        "retina_2d": True,
        "retina_n_az": 16,
        "retina_n_el": 12,
        "synchronous": True,
        "retina_accel": True,
        "event_native": True,
        "visual_motion": True,
        "visual_salience": True,
        "event_window_epochs": 8,
        "adapt_rate": 0.4,
        "onset_threshold_db": 6.0,
        "onset_refractory_epochs": 0.0,
    }
    wa = WorldAdapter(seeds=())
    try:
        # Adapt the static field, then sweep one bright receptor across a row.
        for epoch in range(1, 5):
            counts = np.zeros((12, 16), dtype=np.int64)
            wa.update_vision(
                calibration=cal, photon_packets=[],
                photon_counts=counts, photon_epoch=epoch)
        for col in range(2, 10):
            epoch = col + 3
            counts = np.zeros((12, 16), dtype=np.int64)
            counts[5, col] = 4096
            wa.update_vision(
                calibration=cal,
                photon_packets=[{
                    "col": col, "row": 5,
                    "wavelength_nm": 498.0, "count": 4096,
                }],
                photon_counts=counts, photon_epoch=epoch)

        assert wa._eye._retina_2d is True
        assert len(wa._eye._cells) == 16 * 12
        assert set(wa.vision_kernels()) == {"rod"}
        assert len(wa.vision_kernels()["rod"]) == 16 * 12

        attrs = wa.s.node(wa.agent)["attrs"]
        assert attrs["vision_sensor_epoch"] == 12
        assert attrs["vision_settled_epoch"] == 12
        assert attrs["vision_source_epoch"] == 12

        motion_nodes = wa.inner.neighbours(wa.agent, "perceives_motion")
        assert len(motion_nodes) == attrs["vision_motion_count"] == 1
        motion = wa.s.node(motion_nodes[0])["attrs"]
        assert motion["v_az"] == 1.0
        assert motion["v_el"] == 0.0
        assert motion["coherence"] == 1.0

        shapes = wa.inner.neighbours(wa.agent, "sees_shape")
        assert len(shapes) == attrs["vision_polygon_count"] == 1
        shape = wa.s.node(shapes[0])["attrs"]
        assert (
            shape["mincol"], shape["maxcol"],
            shape["minrow"], shape["maxrow"],
        ) == (2, 9, 5, 5)
        assert all(isinstance(shape[key], int) for key in (
            "mincol", "maxcol", "minrow", "maxrow", "sensor_epoch"))
        for forbidden in ("cx_norm", "cy_norm", "bbox_norm", "area"):
            assert forbidden not in shape

        salience_nodes = wa.inner.neighbours(wa.agent, "perceives_salience")
        assert len(salience_nodes) == attrs["vision_salience_count"] == 8
        assert all(
            wa.s.node(node)["type"] == "RetinalSalience"
            for node in salience_nodes)
    finally:
        wa.close()


def test_source_epoch_gaps_advance_the_graph_native_visual_clock():
    cal = {
        "retina_2d": True,
        "retina_n_az": 4,
        "retina_n_el": 3,
        "synchronous": True,
        "retina_accel": True,
        "event_native": True,
        "held_prediction": "decay",
        "visual_motion": False,
        "visual_salience": False,
    }
    wa = WorldAdapter(seeds=())
    try:
        counts = np.full((3, 4), 30, dtype=np.int64)
        packets = dpw.packets_from_counts(counts)
        wa.update_vision(
            calibration=cal, photon_packets=packets,
            photon_counts=counts, photon_epoch=1)
        wa.update_vision(
            calibration=cal, photon_packets=packets,
            photon_counts=counts, photon_epoch=9)

        attrs = wa.s.node(wa.agent)["attrs"]
        assert wa._eye._epoch == 9
        assert attrs["vision_sensor_epoch"] == 9
        assert attrs["vision_source_epoch"] == 9
        assert {
            int(wa._eye.substrate.node(node)["attrs"]["epoch"])
            for node in wa._eye.substrate.nodes("HeldSurfaceCell")
        } == {9}
    finally:
        wa.close()


def test_2d_bridge_bypasses_the_1d_snapshot_and_rgb_compatibility_path():
    source = inspect.getsource(WorldAdapter._update_vision_photon_sheet)
    assert ".latest(" not in source
    assert "_rgb_to_photons" not in source
    assert "submit_photons_2d" in source
    assert "settle_carve_2d" in source
    assert "settle_motion_2d" in source
    assert "settle_salience_2d" in source


def test_interactive_runner_selects_measured_photon_profile():
    import jabberwock_plays_doom as runner

    profile = runner.PHOTON_EYE_PROFILE
    assert profile["retina_accel"] is True
    assert profile["event_native"] is True
    assert profile["visual_motion"] is True
    assert profile["visual_salience"] is True
    assert profile["event_window_epochs"] >= 3
    source = inspect.getsource(runner.main)
    assert '"photon_sheet":True' in source
    assert "agent._eye.latest()" not in source
    assert 'default=20' in source
    assert 'default=15' in source
