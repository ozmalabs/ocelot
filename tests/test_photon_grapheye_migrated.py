"""The public GraphEye is photon/photoreceptor based, not pixel based."""
from __future__ import annotations

import numpy as np
import pytest
import time

pytest.importorskip("substrate_rs")

from domains.photon_eye import GraphEye
from domains.vision_graph import RGBEye


def _receptor(eye, receptor_class):
    return eye.substrate.node(eye.kernels()[receptor_class][0])["attrs"]


def _settle(eye, expected=1, timeout=2.0):
    deadline = time.perf_counter() + timeout
    snapshot = eye.latest()
    while eye.processed_count() < expected and time.perf_counter() < deadline:
        time.sleep(0.002)
        snapshot = eye.latest()
    assert eye.processed_count() >= expected
    snapshot = eye.latest()
    assert snapshot is not None
    return snapshot


def test_public_eye_and_deprecated_rgb_eye_are_distinct():
    from domains.vision_graph import GraphEye as PublicGraphEye
    assert PublicGraphEye is GraphEye
    assert RGBEye is not GraphEye
    assert RGBEye.__deprecated__ is True
    assert "fixed RGB/depth" in RGBEye.deprecation_reason


def test_photon_eye_graph_contains_receptors_not_pixels_or_sobel_kernels():
    eye = GraphEye(n_az=4).build()
    assert len(eye.substrate.nodes("Photoreceptor")) == 16
    assert len(eye.substrate.nodes("RetinalColumn")) == 4
    for forbidden in ("Image", "Patch", "Kernel", "VisionPolygon"):
        assert list(eye.substrate.nodes(forbidden)) == []
    eye.stop()


def test_spectral_sensitivity_distinguishes_red_and_blue_photons():
    red = GraphEye(n_az=1).build()
    red.submit_photons([
        {"column": 0, "wavelength_nm": 610, "count": 1000},
    ])
    _settle(red)
    assert _receptor(red, "l")["activation"] > _receptor(red, "s")["activation"]
    red.stop()

    blue = GraphEye(n_az=1).build()
    blue.submit_photons([
        {"column": 0, "wavelength_nm": 460, "count": 1000},
    ])
    _settle(blue)
    assert _receptor(blue, "s")["activation"] > _receptor(blue, "l")["activation"]
    blue.stop()


def test_repeated_exposure_adapts_receptor_response():
    eye = GraphEye(n_az=1, adapt_rate=0.25).build()
    packets = [{"column": 0, "wavelength_nm": 550, "count": 1000}]
    eye.submit_photons(packets)
    _settle(eye, 1)
    first = _receptor(eye, "m")["activation"]
    first_adaptation = _receptor(eye, "m")["adaptation"]
    eye.submit_photons(packets)
    _settle(eye, 2)
    second = _receptor(eye, "m")["activation"]
    assert _receptor(eye, "m")["adaptation"] > first_adaptation
    assert second < first
    eye.stop()


def test_rgb_is_only_converted_to_photon_counts_at_io_boundary():
    frame = np.zeros((12, 24, 3), np.uint8)
    frame[:, :12, 0] = 255
    frame[:, 12:, 2] = 255
    eye = GraphEye(n_az=2, context={"exposure_quanta": 512}).build()
    eye.submit(screen=frame)
    _settle(eye)
    exposures = eye.substrate.nodes("PhotonExposure")
    assert len(exposures) == 1
    attrs = eye.substrate.node(exposures[0])["attrs"]
    assert attrs["total_quanta"] > 0
    assert list(eye.substrate.nodes("Image")) == []
    snap = eye.latest()
    assert snap["percepts"][0]["red_green"] > snap["percepts"][1]["red_green"]
    assert snap["percepts"][1]["blue_yellow"] > snap["percepts"][0]["blue_yellow"]
    eye.stop()


def test_depth_buffer_is_not_treated_as_visual_input():
    eye = GraphEye(n_az=2).build()
    eye.submit(depth=np.full((10, 10), 255, np.uint8), screen=None)
    _settle(eye)
    assert all(p["distance"] is None for p in eye.latest()["percepts"])
    assert eye.substrate.node(eye._last_exposure)["attrs"]["total_quanta"] == 0
    eye.stop()


def test_worker_count_does_not_change_retinal_percept():
    frame = np.arange(16 * 32 * 3, dtype=np.uint8).reshape(16, 32, 3)
    outputs = []
    for workers in (1, 2, 4):
        eye = GraphEye(
            n_az=8,
            context={"worker_capacity": workers, "exposure_quanta": 256},
        ).build()
        eye.submit(screen=frame, posture_deg=12)
        outputs.append(_settle(eye))
        eye.stop()
    assert outputs[0] == outputs[1] == outputs[2]


def test_submit_is_nonblocking_and_retina_settles_on_its_own_clock():
    eye = GraphEye(
        n_az=16,
        context={"worker_capacity": 2, "retina_tick_hz": 10.0},
    ).build()
    packets = [
        {"column": i, "wavelength_nm": 550, "count": 500}
        for i in range(16)
    ]
    started = time.perf_counter()
    eye.submit_photons(packets)
    elapsed = time.perf_counter() - started
    assert elapsed < 0.05, "submission must enqueue, not run a retinal cycle"
    assert eye.processed_count() == 0
    _settle(eye, timeout=3.0)
    eye.stop()
