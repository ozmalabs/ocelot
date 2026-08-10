"""Focused gate for reusable held prediction on the 2-D photon sheet.

The opt-in apparatus is only mechanical graph construction.  The existing
``staleness_decay`` seed performs prediction, residual measurement, freshness
decay, attention marking, and blending as graph rules.
"""
from __future__ import annotations

import numpy as np

from domains.photon_eye import GraphEye
from substrate.seed_loader import manifest_for


N_AZ = 3
N_EL = 2
N = N_AZ * N_EL
DEFAULT_PARAMS = {
    "enabled": 1.0,
    "lr_min": 0.15,
    "hl_scale": 32.0,
    "hl_min": 1.0,
    "c0": 1024.0,
    "refresh_thresh": 15.0,
    "attn_thresh": 768.0,
    "uniform": 0.0,
    "uniform_hl": 256.0,
    "pin_freshness": 0.0,
}


def _eye(extra=None):
    context = {
        "retina_2d": True,
        "synchronous": True,
        "worker_capacity": 1,
        "onset_threshold_db": 6.0,
        "onset_refractory_epochs": 0.0,
    }
    context.update(extra or {})
    return GraphEye(
        n_az=N_AZ, n_el=N_EL, adapt_rate=0.15, context=context).build()


def _packets(counts):
    return [
        {
            "col": col,
            "row": row,
            "wavelength_nm": 498.0,
            "count": int(counts[row, col]),
        }
        for row in range(N_EL)
        for col in range(N_AZ)
        if counts[row, col] > 0
    ]


def _tick(eye, packets):
    eye.submit_photons_2d(packets)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _held_attrs(eye):
    return [
        dict(eye.substrate.node(nid)["attrs"])
        for nid in eye.substrate.nodes("HeldSurfaceCell")
    ]


def _node_records(eye):
    records = []
    for node in (eye.substrate.node(nid) for nid in eye.substrate.nodes()):
        attrs = dict(node["attrs"])
        # Scheduler telemetry is deliberately wall-clock-valued and outside
        # the eye's byte-observable semantic manifold.
        attrs.pop("service_wall_micros", None)
        attrs.pop("wall_micros", None)
        records.append((node["type"], attrs))
    return records


def _legacy_decay_eye():
    """The exact pre-reuse measure-adapter construction."""
    eye = _eye()
    inner = eye.substrate._inner
    inner.load_seed_manifest(manifest_for("staleness_decay"), eye._agent)
    params = eye.substrate.add_node("HeldDecayParams", dict(DEFAULT_PARAMS))
    inner.add_edge_unchecked(
        eye._retina, "has_held_decay_params", params)
    for row in range(N_EL):
        for col in range(N_AZ):
            flat = row * N_AZ + col
            held = eye.substrate.add_node("HeldSurfaceCell", {
                "value": 0.0,
                "obs": 0.0,
                "row": row,
                "col": col,
                "cell_index": flat,
                "epoch": 0.0,
                "residual": 0.0,
                "last_refresh_epoch": 0.0,
                "half_life": DEFAULT_PARAMS["hl_scale"],
                "freshness": DEFAULT_PARAMS["c0"],
                "needs_attention": 0.0,
            })
            inner.add_edge_unchecked(
                eye._cells[flat], "has_held_surface_cell", held)
    return eye


def test_opt_in_adds_exactly_one_graph_cell_per_receptor():
    baseline = _eye()
    enabled = _eye({"held_prediction": "decay"})
    try:
        assert enabled.substrate.node_count() == baseline.substrate.node_count() + N + 1
        assert enabled.substrate.edge_count() == baseline.substrate.edge_count() + N + 1
        assert len(enabled.substrate.nodes("HeldDecayParams")) == 1
        assert len(enabled.substrate.nodes("HeldSurfaceCell")) == N

        params = enabled.substrate.node(
            enabled.substrate.nodes("HeldDecayParams")[0])["attrs"]
        assert params == DEFAULT_PARAMS
        for flat, cell in enumerate(enabled._cells):
            held = enabled.substrate.neighbours(cell, "has_held_surface_cell")
            assert len(held) == 1
            attrs = enabled.substrate.node(held[0])["attrs"]
            assert (attrs["row"], attrs["col"], attrs["cell_index"]) == (
                flat // N_AZ, flat % N_AZ, flat)
    finally:
        baseline.stop()
        enabled.stop()


def test_true_alias_and_graph_data_overrides():
    eye = _eye({
        "held_prediction": True,
        "held_prediction_params": {
            "hl_scale": 64.0,
            "refresh_thresh": 12.0,
        },
    })
    try:
        params = eye.substrate.node(
            eye.substrate.nodes("HeldDecayParams")[0])["attrs"]
        assert params["hl_scale"] == 64.0
        assert params["refresh_thresh"] == 12.0
        assert all(
            attrs["half_life"] == 64.0 for attrs in _held_attrs(eye))
    finally:
        eye.stop()


def test_reusable_path_is_byte_observable_identical_to_measure_construction():
    reusable = _eye({"held_prediction": "decay"})
    legacy = _legacy_decay_eye()
    rng = np.random.default_rng(200000)
    scenes = [
        np.full((N_EL, N_AZ), 30, dtype=int) for _ in range(8)
    ] + [
        np.array([[180, 180, 30], [180, 180, 30]], dtype=int)
        for _ in range(4)
    ]
    try:
        for scene in scenes:
            counts = rng.poisson(scene)
            packets = _packets(counts)
            _tick(reusable, packets)
            _tick(legacy, packets)
            assert _held_attrs(reusable) == _held_attrs(legacy)
    finally:
        reusable.stop()
        legacy.stop()


def test_static_input_denoises_and_large_change_is_adopted_rapidly():
    eye = _eye({"held_prediction": "decay"})
    rng = np.random.default_rng(7)
    held, observed = [], []
    try:
        for _ in range(30):
            counts = rng.poisson(np.full((N_EL, N_AZ), 50))
            _tick(eye, _packets(counts))
            attrs = _held_attrs(eye)[0]
            held.append(float(attrs["value"]))
            observed.append(float(attrs["obs"]))
        assert np.var(held[-15:]) < 0.5 * np.var(observed[-15:])

        target = 200.15
        for _ in range(3):
            _tick(eye, _packets(np.full((N_EL, N_AZ), 200)))
        assert abs(float(_held_attrs(eye)[0]["value"]) - target) < 3.0
    finally:
        eye.stop()


def test_default_off_is_graph_and_observable_identical():
    absent = _eye()
    explicit_off = _eye({"held_prediction": False})
    packets = _packets(np.array([[20, 30, 40], [50, 60, 70]]))
    try:
        assert absent.substrate.node_count() == explicit_off.substrate.node_count()
        assert absent.substrate.edge_count() == explicit_off.substrate.edge_count()
        assert _node_records(absent) == _node_records(explicit_off)
        _tick(absent, packets)
        _tick(explicit_off, packets)
        assert _node_records(absent) == _node_records(explicit_off)
        assert absent.substrate.nodes("HeldDecayParams") == []
        assert absent.substrate.nodes("HeldSurfaceCell") == []
    finally:
        absent.stop()
        explicit_off.stop()


def test_accelerator_preserves_held_surface_graph_semantics():
    graph = _eye({
        "held_prediction": "decay",
        "retina_accel": False,
    })
    accel = _eye({
        "held_prediction": "decay",
        "retina_accel": True,
    })
    scenes = [
        np.full((N_EL, N_AZ), 30, dtype=int),
        np.array([[180, 180, 30], [180, 180, 30]], dtype=int),
        np.array([[30, 180, 180], [30, 180, 180]], dtype=int),
        np.full((N_EL, N_AZ), 30, dtype=int),
    ]
    try:
        for counts in scenes:
            packets = _packets(counts)
            _tick(graph, packets)
            _tick(accel, packets)
            assert _held_attrs(accel) == _held_attrs(graph)
    finally:
        graph.stop()
        accel.stop()


def test_apparatus_introduces_no_task_specific_graph_vocabulary():
    eye = _eye({"held_prediction": True})
    try:
        types = {
            eye.substrate.node(nid)["type"] for nid in eye.substrate.nodes()
        }
        assert types.isdisjoint({"Door", "Enemy", "Weapon", "Level"})
    finally:
        eye.stop()
