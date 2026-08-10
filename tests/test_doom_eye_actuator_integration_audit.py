"""Integration guardrails for graph-issued Doom eye actuation.

This file deliberately treats the world/runner/adapter seam as an apparatus:
the Agent is authoritative about the command, the world retains enacted
physical gaze, and WorldAdapter may rewrite receptor geometry only when that
geometry changes.
"""
from __future__ import annotations

import copy
import inspect
import math
import os
import sys
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

pytest.importorskip("substrate_rs")

import doom_world as dw  # noqa: E402
import jabberwock_plays_doom as runner  # noqa: E402
from domains import doom_photon_world as dpw  # noqa: E402
from domains.photon_eye import (  # noqa: E402
    receptor_layout_from_calibration,
)
from substrate.world_adapter import WorldAdapter  # noqa: E402
from tests.test_interactive_doom_migrated import FakeGame  # noqa: E402


def _active_command(*, az=15.0, el=-4.0, epoch=7):
    return {
        "eye_motor_active": 1.0,
        "eye_motor_source_epoch": epoch,
        "eye_motor_target_column": 11,
        "eye_motor_target_row": 5,
        "eye_motor_target_az_deg": az,
        "eye_motor_target_el_deg": el,
        "eye_motor_fixation_epoch": epoch,
        "eye_motor_duration_tics": 1,
        "eye_motor_status": "emitted",
    }


def test_enacted_gaze_persists_across_inactive_one_tic_pulses(monkeypatch):
    """Inactive means no new command; it must not recenter the physical eye."""
    games = []

    def make_game():
        game = FakeGame()
        games.append(game)
        return game

    monkeypatch.setattr(dw.vzd, "DoomGame", make_game)
    world = dw.DoomWorld(
        realtime=False,
        photon_sheet=True,
        photon_poisson=False,
        photon_n_az=5,
        photon_n_el=4,
        photon_eye_context={
            "retinal_layout": "foveated",
            "fovea_width": 3,
            "fovea_height": 2,
            "peripheral_rings": 2,
            "peripheral_spokes": 4,
        },
    )
    try:
        world.apply_eye_motor_command(_active_command())
        first, ctx = world.reset()
        assert first.vision_calibration["gaze_az_deg"] == 15.0
        assert first.vision_calibration["gaze_el_deg"] == -4.0
        assert first.vision_calibration["eye_motor_active"] == 1.0

        inactive = dict(
            _active_command(az=0.0, el=0.0, epoch=8),
            eye_motor_active=0.0,
            eye_motor_status="fixation_confirmed",
        )
        world.apply_eye_motor_command(inactive)
        second, _ = world.apply_action(first, ctx, ("noop",))
        assert second.vision_calibration["eye_motor_active"] == 0.0
        assert second.vision_calibration["gaze_az_deg"] == 15.0
        assert second.vision_calibration["gaze_el_deg"] == -4.0
    finally:
        world.close()


def test_runner_copies_only_the_authoritative_agent_command_attrs():
    """The host must not inspect candidates, commands, attention, or salience."""
    expected = _active_command(az=22.5, el=3.25, epoch=19)

    class RootOnlySubstrate:
        def node(self, node):
            assert node == "agent-root"
            return {"attrs": dict(expected)}

        def nodes(self, *_args, **_kwargs):
            raise AssertionError("host searched command/candidate nodes")

        def neighbours(self, *_args, **_kwargs):
            raise AssertionError("host searched graph structure")

    agent = SimpleNamespace(s=RootOnlySubstrate(), agent="agent-root")
    copied = runner._eye_motor_command(agent)
    assert copied == expected
    expected["eye_motor_target_az_deg"] = -99.0
    assert copied["eye_motor_target_az_deg"] == 22.5

    source = inspect.getsource(runner._eye_motor_command).lower()
    assert "sort" not in source and "argmax" not in source
    assert "attention" not in source and "salience" not in source


def _foveated_calibration():
    return {
        "retina_2d": True,
        "retina_n_az": 5,
        "retina_n_el": 4,
        "synchronous": True,
        "retina_accel": True,
        "event_native": True,
        "visual_motion": False,
        "visual_salience": False,
        "retinal_layout": "foveated",
        "fovea_width": 3,
        "fovea_height": 2,
        "peripheral_rings": 2,
        "peripheral_spokes": 4,
        "source_width": 32,
        "source_height": 24,
        "fov_h_deg": 90.0,
        "fov_v_deg": 60.0,
        "gaze_az_deg": 0.0,
        "gaze_el_deg": 0.0,
    }


def test_world_adapter_rewrites_layout_only_when_geometry_changes():
    adapter = WorldAdapter(seeds=())
    counts = np.zeros((4, 5), dtype=np.int64)
    calibration = _foveated_calibration()
    try:
        adapter.update_vision(
            calibration=calibration,
            photon_packets=[],
            photon_counts=counts,
            photon_epoch=1,
        )
        calls = []
        original = adapter._eye.update_receptor_layout_2d

        def counted(*args, **kwargs):
            calls.append(dict(kwargs.get("calibration") or {}))
            return original(*args, **kwargs)

        adapter._eye.update_receptor_layout_2d = counted
        # Sensor epoch and photometry change, optical geometry does not.
        adapter.update_vision(
            calibration=dict(calibration, photon_gain=2.0),
            photon_packets=[],
            photon_counts=counts,
            photon_epoch=2,
        )
        assert calls == []

        moved = dict(calibration, gaze_az_deg=12.0)
        adapter.update_vision(
            calibration=moved,
            photon_packets=[],
            photon_counts=counts,
            photon_epoch=3,
        )
        assert len(calls) == 1
        assert calls[0]["gaze_az_deg"] == 12.0
        assert adapter._eye._receptor_layout[0]["gaze_az"] != 0.0
    finally:
        adapter.close()


def test_layout_signature_tracks_explicit_and_peripheral_geometry_changes():
    """Every input used by receptor_layout_from_calibration belongs in cache."""
    base = _foveated_calibration()
    moved_periphery = dict(base, periphery_gaze_az_deg=8.0)
    assert (
        receptor_layout_from_calibration(base, 5, 4)
        != receptor_layout_from_calibration(moved_periphery, 5, 4)
    )
    assert (
        WorldAdapter._receptor_layout_signature(base)
        != WorldAdapter._receptor_layout_signature(moved_periphery)
    )

    explicit = dict(base)
    explicit.pop("retinal_layout")
    explicit["receptor_layout"] = receptor_layout_from_calibration(base, 5, 4)
    changed = copy.deepcopy(explicit)
    changed["receptor_layout"][0]["gaze_az"] += math.radians(1.0)
    assert (
        WorldAdapter._receptor_layout_signature(explicit)
        != WorldAdapter._receptor_layout_signature(changed)
    )


def test_default_and_explicit_uniform_doom_sampling_match_legacy_exactly():
    rng = np.random.default_rng(220000)
    screen = rng.integers(0, 256, size=(24, 32, 3), dtype=np.uint8)
    base = {
        "photon_sheet": True,
        "retina_2d": True,
        "retina_n_az": 8,
        "retina_n_el": 6,
        "photon_gain": 1.0,
        "photon_poisson": False,
    }
    expected = dpw.photon_counts(
        dpw.luma_grid(screen, 6, 8), rng=None, gain=1.0)

    absent = SimpleNamespace()
    explicit = SimpleNamespace()
    dw._publish_photon_sheet(
        absent, screen, base, epoch=1, packetize=False)
    dw._publish_photon_sheet(
        explicit, screen, dict(base, retinal_layout="uniform"),
        epoch=1, packetize=False)

    assert np.array_equal(absent.vision_photon_counts, expected)
    assert np.array_equal(explicit.vision_photon_counts, expected)
    assert absent.vision_photon_packets is None
    assert explicit.vision_photon_packets is None


def test_split_path_keeps_dense_fovea_as_one_tensor_and_graphs_only_scout():
    adapter = WorldAdapter(seeds=())
    cal = {
        "retina_2d": True,
        "retina_n_az": 8,
        "retina_n_el": 6,
        "retinal_layout": "foveated",
        "split_foveated_pathways": True,
        "fovea_width": 8,
        "fovea_height": 4,
        "peripheral_rings": 2,
        "peripheral_spokes": 8,
        "source_width": 32,
        "source_height": 24,
        "fov_h_deg": 90.0,
        "fov_v_deg": 60.0,
    }
    counts = np.arange(48, dtype=np.int64).reshape(6, 8)
    try:
        packets, scout, eye_cal, n_az, n_el = (
            adapter._split_foveated_photon_sheet(counts, cal, 3))
        assert (n_az, n_el) == (8, 2)
        assert scout.shape == (2, 8)
        assert np.array_equal(scout.reshape(-1), np.arange(32, 48))
        assert len(packets) == 16
        assert len(eye_cal["receptor_layout"]) == 16
        assert all(
            record["pathway"] == "log_polar_periphery"
            for record in eye_cal["receptor_layout"])

        nodes = adapter.s.nodes("FovealExposure")
        assert len(nodes) == 1
        attrs = adapter.s.node(nodes[0])["attrs"]
        assert attrs["width"] == 8 and attrs["height"] == 4
        assert attrs["values"] == tuple(range(32))
        assert attrs["native_pixel_sampling"] == 1.0

        cached_layout = adapter._vision_peripheral_layout
        adapter._split_foveated_photon_sheet(
            counts, dict(cal, gaze_az_deg=15.0), 4)
        assert adapter._vision_peripheral_layout is cached_layout
        assert len(adapter.s.nodes("FovealExposure")) == 1
        latest = adapter.s.node(adapter.s.nodes("FovealExposure")[0])["attrs"]
        assert latest["gaze_az_deg"] == 15.0
    finally:
        adapter.close()
