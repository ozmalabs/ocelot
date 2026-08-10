"""Gate for the GRAPH-NATIVE EVENT PATH (seed block 191000-191999).

The photon eye's carve/motion/salience settle used to marshal every
`RetinalOnsetEvent` out of the graph one node at a time in Python. Block 191000
moves that whole sweep into ONE Rust op (`retina_event_task_batch`); the onset
event stream never leaves Rust. This gate PINS that the graph-native path
(`event_native=True`, shipped) is BYTE-IDENTICAL to the old Python loop
(`event_native=False`, the oracle), on:

  * the synthetic moving-texture scene at 20x15 / 40x30 / 80x60, all three event
    stages on (carve + motion + salience);
  * the committed real-Doom carve fixture (a crop of the 160x120 `defend_the_line`
    frames -- real ink), where the carve genuinely FIRES;

and that the mechanism is right:

  * the `perturb` falsifier (a wrong in-Rust read) BREAKS the digest -- the
    identity check is non-vacuous;
  * the graph-native settle stage is far CHEAPER than the Python loop (a coarse
    cost-shape claim at the mechanism grain, with a bulletproof margin -- the
    measured gap is ~40x);
  * no agent decision leaked into the Python adapter (source audit).

Prereg: EYE_GRAPHNATIVE_EVENT_PREREG.md. Self-contained; VizDoom-free (the crop
is a committed fixture).
"""
from __future__ import annotations

import json
import os
import statistics as stats
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from domains import doom_photon_world as dpw               # noqa: E402
from domains.photon_eye import GraphEye                     # noqa: E402
import scripts.eye_graphnative_event_measure as M           # noqa: E402

SYNTH_RES = [(20, 15), (40, 30), (80, 60)]
FIXDIR = os.path.join(ROOT, "tests", "fixtures", "doom_carve_scale")
CROP = (46, 86, 33, 120)          # r0, r1, c0, c1 -> 40 rows x 87 cols
CARVE_MIN_COH = 0.5
CARVE_MIN_EVENTS = 2.5


# ---------------------------------------------------------------------------
#  Synthetic identity (all three event stages)
# ---------------------------------------------------------------------------
def _synth_last_outputs(n_az, n_el, event_native, perturb=False,
                        warmup=2, motion=4, seed=191000):
    """Drive the eye through the full per-frame cycle and return the LAST
    frame's (polygons, motion percepts, salience) -- pruned to steady state so
    the outputs are a clean per-frame read. Deterministic scene + rng."""
    eye = M.build_eye(n_az, n_el, event_native, perturb=perturb)
    frames = M.make_scene(n_az, n_el, warmup + motion, seed=seed)
    rng = np.random.default_rng(seed + 7)
    last = ([], [], [])
    for i, luma in enumerate(frames):
        eye.submit_photons_2d(dpw.photon_packets(luma, rng))
        since = eye._epoch
        eye.settle_carve_2d(since_epoch=since)
        eye.settle_motion_2d(since_epoch=since)
        eye.settle_salience_2d(since_epoch=since)
        eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
        last = (eye.carve_polygons_2d(), eye.motion_percepts_2d(),
                eye.salience_percepts_2d())
        M._prune_results(eye)
        eye.prune_settled_tasks()
        M._prune_events(eye)
    eye.stop()
    return last


def _digest(outputs):
    """Full float-exact digest of (polys, motion, salience)."""
    return json.dumps(outputs, sort_keys=True)


@pytest.mark.parametrize("n_az,n_el", SYNTH_RES)
def test_byte_identical_outputs_synthetic(n_az, n_el):
    """The graph-native path == the Python-loop oracle, float-exact, for
    VisionPolygons AND RetinalMotionPercepts AND RetinalSalience."""
    native = _synth_last_outputs(n_az, n_el, True)
    oracle = _synth_last_outputs(n_az, n_el, False)
    assert _digest(native) == _digest(oracle), (
        f"graph-native != oracle at {n_az}x{n_el}")
    # Non-vacuity: the scene actually produces salience events.
    assert len(native[2]) > 0, "scene produced no salience -- identity vacuous"


def test_perturb_breaks_identity():
    """A WRONG in-Rust read (col+1000) must break the digest -- proof the
    byte-identity check can fail."""
    oracle = _synth_last_outputs(80, 60, False)
    perturbed = _synth_last_outputs(80, 60, True, perturb=True)
    assert _digest(perturbed) != _digest(oracle), (
        "perturbed read did NOT change the output -- the identity gate is vacuous")


# ---------------------------------------------------------------------------
#  Real-Doom carve identity (committed fixture crop -- real ink)
# ---------------------------------------------------------------------------
def _carve_run(lumas, n_el, n_az, event_native):
    """Carve-only flow over [f0]*warmup + motion (the doom_carve_scale flow),
    with the 191000 switch. Returns the VisionPolygons."""
    eye = GraphEye(
        n_az=n_az, n_el=n_el, adapt_rate=0.4,
        context={"retina_2d": True, "synchronous": True, "worker_capacity": 1,
                 "onset_threshold_db": 6.0, "onset_refractory_epochs": 0.0,
                 "visual_carve": True, "carve_min_coherence": CARVE_MIN_COH,
                 "carve_min_events": CARVE_MIN_EVENTS,
                 "event_native": event_native}).build()
    rng = np.random.default_rng(182000)
    f0, motion = lumas[0], lumas[1:]
    for _ in range(6):
        eye.submit_photons_2d(dpw.photon_packets(f0, rng))
        eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
        eye.prune_settled_tasks()
    for nid in list(eye.substrate.nodes("RetinalOnsetEvent")):
        eye.substrate.remove_node(nid)
    since = eye._epoch + 1
    for luma in motion:
        eye.submit_photons_2d(dpw.photon_packets(luma, rng))
        eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
        eye.prune_settled_tasks()
    eye.settle_carve_2d(since_epoch=since)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    eye.stop()
    return polys


@pytest.fixture(scope="module")
def crop_lumas():
    d = np.load(os.path.join(FIXDIR, "frames_160x120.npz"))
    r0, r1, c0, c1 = CROP
    lumas = d["lumas"][:, r0:r1, c0:c1]
    return [lumas[i] for i in range(lumas.shape[0])]


def test_landed_doom_carve_byte_identical(crop_lumas):
    """On real Doom ink (the committed 160x120 crop where the carve FIRES), the
    graph-native carve is byte-identical to the Python-loop oracle."""
    n_el, n_az = crop_lumas[0].shape
    native = _carve_run(crop_lumas, n_el, n_az, True)
    oracle = _carve_run(crop_lumas, n_el, n_az, False)
    assert json.dumps(native, sort_keys=True) == json.dumps(oracle, sort_keys=True)
    assert len(native) > 0, "carve did not fire on the crop -- identity vacuous"


# ---------------------------------------------------------------------------
#  Cost shape (mechanism grain, bulletproof margin)
# ---------------------------------------------------------------------------
def _settle_ms(n_az, n_el, event_native, frames=6):
    """Median wall-ms for the three settle calls (the event path) over a few
    steady-state frames."""
    import time
    eye = M.build_eye(n_az, n_el, event_native)
    scene = M.make_scene(n_az, n_el, frames, seed=191000)
    rng = np.random.default_rng(193000)
    xs = []
    for i, luma in enumerate(scene):
        eye.submit_photons_2d(dpw.photon_packets(luma, rng))
        since = eye._epoch
        t = time.perf_counter()
        eye.settle_carve_2d(since_epoch=since)
        eye.settle_motion_2d(since_epoch=since)
        eye.settle_salience_2d(since_epoch=since)
        dt = time.perf_counter() - t
        eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
        if i >= 2:
            xs.append(dt)
        M._prune_results(eye)
        eye.prune_settled_tasks()
        M._prune_events(eye)
    eye.stop()
    return 1000 * stats.median(xs)


def test_graphnative_settle_is_cheaper():
    """COST SHAPE (robust): at 80x60 the graph-native settle is far cheaper than
    the Python loop. The measured gap is ~40x; assert a bulletproof 3x margin so
    the mechanism claim never flakes on a noisy machine."""
    native = _settle_ms(80, 60, True)
    oracle = _settle_ms(80, 60, False)
    assert native * 3 < oracle, (
        f"graph-native settle ({native:.3f}ms) not clearly cheaper than the "
        f"Python loop ({oracle:.3f}ms)")


def test_no_agent_decision_in_adapter_source():
    """The 191000 helper is mechanical I/O: it packs a payload and mints a task,
    no branch over graph state deciding what the agent does. The native branch
    must NOT iterate individual RetinalOnsetEvent nodes in Python."""
    src = open(os.path.join(ROOT, "domains", "photon_eye.py")).read()
    # The ONLY remaining event-node loop is the oracle branch inside the helper.
    assert src.count('nodes("RetinalOnsetEvent")') == 1, (
        "unexpected extra Python event-node loop -- the marshalling must live in "
        "Rust, with a single oracle loop retained")
    assert "retina_event_task_batch" in src, "graph-native op not wired in"
