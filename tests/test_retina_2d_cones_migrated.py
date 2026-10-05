"""Mary's Room stage 4.1: the 2-D GraphEye colour sheet (`retina_2d_cones`).

The flag is additive and OFF by default. With it ON each 2-D cell carries
rod + L + M + S Photoreceptors and a RetinalPercept, and the UNCHANGED 1-D
opponent rule `photon_column_synthesizes_retinal_percept` fires per cell. The
2-D sheet is driven synchronously (submit_photons_2d -> run_cognitive_tasks(1)
-> run_rules), as in the other 2-D suites; processed_count() does not advance
in 2-D.

The reference is `domains.spectral_forward.eye_capture_model` (frozen), the
documented replica of the eye's capture: caught = dark + sum count*gauss,
activation = caught / (caught + half_sat + adaptation_before), and the
documented adaptation recursion a' = a + adapt_rate * (caught - a).
"""
from __future__ import annotations

import json

import numpy as np
import pytest

from domains import spectral_forward as sf
from domains.photon_eye import GraphEye, _RECEPTORS

N_AZ = 6
N_EL = 4
N = N_AZ * N_EL
ADAPT_RATE = 0.12          # GraphEye default; the documented recursion rate
TOL = 1e-12
CLASSES = ("l", "m", "s", "rod")


def _ctx(extra=None):
    ctx = {"retina_2d": True, "synchronous": True, "worker_capacity": 1}
    ctx.update(extra or {})
    return ctx


def _eye(extra=None, n_az=N_AZ, n_el=N_EL):
    return GraphEye(n_az=n_az, n_el=n_el, context=_ctx(extra)).build()


def _tick(eye, packets):
    eye.submit_photons_2d(packets)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _node_records(eye):
    # Same export as the held-prediction byte-identity gate: every node's
    # (type, attrs), wall-clock scheduler telemetry removed.
    records = []
    for node in (eye.substrate.node(nid) for nid in eye.substrate.nodes()):
        attrs = dict(node["attrs"])
        attrs.pop("service_wall_micros", None)
        attrs.pop("wall_micros", None)
        records.append((node["type"], attrs))
    return records


def _strip_wall(obj):
    if isinstance(obj, dict):
        return {k: _strip_wall(v) for k, v in obj.items()
                if k not in ("service_wall_micros", "wall_micros")}
    if isinstance(obj, list):
        return [_strip_wall(v) for v in obj]
    return obj


def _graph_export(eye):
    """Whole-graph export (nodes, edges, next_id) via the substrate's own
    graph_to_dict, wall-clock telemetry removed, canonically serialised."""
    return json.dumps(_strip_wall(eye.substrate.graph_to_dict()),
                      sort_keys=True, default=repr)


def _white_packets():
    spd = sf.scale_to_td(sf.illuminant("D65"), sf.REFERENCE_WHITE_TD)
    return [{"wavelength_nm": p["wavelength_nm"], "count": p["count"]}
            for p in sf.quantize(spd)]


def _scene(kinds):
    """kinds: per-flat-cell stimulus label -> (per-cell packets, eye packets)."""
    white = _white_packets()
    per_cell = []
    for kind in kinds:
        if kind == "610":
            per_cell.append([{"wavelength_nm": 610.0, "count": 800}])
        elif kind == "530":
            per_cell.append([{"wavelength_nm": 530.0, "count": 800}])
        elif kind == "white":
            per_cell.append(list(white))
        else:
            per_cell.append([])
    packets = []
    for flat, cell_packets in enumerate(per_cell):
        row, col = divmod(flat, N_AZ)
        packets.extend({"col": col, "row": row, **p} for p in cell_packets)
    return per_cell, packets


def _mixed_kinds():
    # Columns 0-1: 610 nm, 2-3: 530 nm, 4: D65 white, 5: dark.
    return [("610", "610", "530", "530", "white", "dark")[flat % N_AZ]
            for flat in range(N)]


def _assert_matches_model(percepts, per_cell, adaptation):
    for flat, rec in enumerate(percepts):
        expected = sf.eye_capture_model(per_cell[flat], adaptation[flat])
        assert abs(rec["red_green"] - expected["red_green"]) <= TOL, flat
        assert abs(rec["blue_yellow"] - expected["blue_yellow"]) <= TOL, flat
        for cls in CLASSES:
            got = rec["receptors"][cls]
            assert abs(got["caught_quanta"] - expected[cls]["caught"]) <= 1e-9
            assert abs(got["activation"] - expected[cls]["activation"]) <= TOL


# ---------------------------------------------------------------- 1. default off

@pytest.mark.parametrize("layout", [None, "uniform"])
def test_default_off_is_graph_and_observable_identical(layout):
    extra = {} if layout is None else {"retinal_layout": layout}
    absent = _eye(extra)
    explicit_off = _eye({**extra, "retina_2d_cones": False})
    try:
        assert absent.substrate.node_count() == explicit_off.substrate.node_count()
        assert absent.substrate.edge_count() == explicit_off.substrate.edge_count()
        assert _node_records(absent) == _node_records(explicit_off)
        assert _graph_export(absent) == _graph_export(explicit_off)
        assert absent.substrate.nodes("RetinalPercept") == []
        assert {absent.substrate.node(r)["attrs"]["receptor_class"]
                for r in absent.substrate.nodes("Photoreceptor")} == {"rod"}
        assert list(absent.kernels()) == ["rod"]
        assert absent.percepts_2d() == []
        _, packets = _scene(_mixed_kinds())
        for _ in range(2):
            _tick(absent, packets)
            _tick(explicit_off, packets)
        assert absent.substrate.node_count() == explicit_off.substrate.node_count()
        assert absent.substrate.edge_count() == explicit_off.substrate.edge_count()
        assert _node_records(absent) == _node_records(explicit_off)
        assert _graph_export(absent) == _graph_export(explicit_off)
        assert absent.percepts_2d() == explicit_off.percepts_2d() == []
    finally:
        absent.stop()
        explicit_off.stop()


# ---------------------------------------------------------------- build shape

@pytest.mark.parametrize("layout", [None, "uniform"])
def test_cones_build_adds_typed_receptors_and_percepts(layout):
    extra = {"retina_2d_cones": True}
    if layout is not None:
        extra["retinal_layout"] = layout
    eye = _eye(extra)
    try:
        kern = eye.kernels()
        assert list(kern) == list(_RECEPTORS)
        assert all(len(v) == N for v in kern.values())
        assert len(eye.substrate.nodes("RetinalPercept")) == N
        for flat in range(N):
            row, col = divmod(flat, N_AZ)
            rod = eye.substrate.node(eye._receptors[(flat, "rod")])["attrs"]
            for cls in ("l", "m", "s"):
                a = eye.substrate.node(eye._receptors[(flat, cls)])["attrs"]
                c, bw, half, dark = _RECEPTORS[cls]
                assert (a["receptor_class"], a["column"], a["row"]) == (cls, col, row)
                assert (a["sensitivity_center_nm"], a["bandwidth_nm"],
                        a["half_saturation"], a["dark_current"]) == (c, bw, half, dark)
                if layout is not None:
                    for key in ("cell_index", "eye_id", "pathway", "gaze_az",
                                "gaze_el", "angular_width", "angular_height"):
                        assert a[key] == rod[key]
                else:
                    assert "gaze_az" not in a
        recs = eye.percepts_2d()
        assert [r["cell_index"] for r in recs] == list(range(N))
        assert all(r["input_epoch"] == -1 for r in recs)
    finally:
        eye.stop()


# ---------------------------------------------------------------- 2. cones fire

def test_cones_on_percepts_fire_and_match_capture_model():
    eye = _eye({"retina_2d_cones": True})
    per_cell, packets = _scene(_mixed_kinds())
    try:
        _tick(eye, packets)
        recs = eye.percepts_2d()
        assert len(recs) == N
        assert all(r["input_epoch"] == 1 for r in recs)
        for r in recs:
            assert (r["row"], r["col"]) == divmod(r["cell_index"], N_AZ)
        _assert_matches_model(recs, per_cell, [None] * N)
        # Non-vacuity: the three stimulus kinds are chromatically distinct.
        rg = {k: recs[i]["red_green"] for i, k in ((0, "610"), (2, "530"), (4, "w"))}
        assert rg["610"] > rg["w"] > rg["530"]
    finally:
        eye.stop()


# ---------------------------------------------------------------- 3. multi-epoch

def test_second_exposure_updates_percepts_and_carries_adaptation():
    eye = _eye({"retina_2d_cones": True})
    first_cells, first = _scene(_mixed_kinds())
    swapped = [{"610": "530", "530": "610"}.get(k, k) for k in _mixed_kinds()]
    second_cells, second = _scene(swapped)
    try:
        _tick(eye, first)
        after_first = eye.percepts_2d()
        # Documented recursion from a fresh eye: a1 = 0 + rate*(caught1 - 0).
        adapt1 = []
        for flat in range(N):
            model = sf.eye_capture_model(first_cells[flat])
            adapt1.append({
                cls: ADAPT_RATE * model[cls]["caught"] for cls in CLASSES})
            for cls in CLASSES:
                assert abs(after_first[flat]["receptors"][cls]["adaptation"]
                           - adapt1[flat][cls]) <= 1e-9
        _tick(eye, second)
        recs = eye.percepts_2d()
        assert all(r["input_epoch"] == 2 for r in recs)
        _assert_matches_model(recs, second_cells, adapt1)
        for flat in range(N):
            model = sf.eye_capture_model(second_cells[flat], adapt1[flat])
            for cls in CLASSES:
                a1 = adapt1[flat][cls]
                expect = a1 + ADAPT_RATE * (model[cls]["caught"] - a1)
                assert abs(recs[flat]["receptors"][cls]["adaptation"]
                           - expect) <= 1e-9
        # The swap really changed the percept sign at a chromatic cell.
        assert after_first[0]["red_green"] > 0 > recs[0]["red_green"]
    finally:
        eye.stop()


# ---------------------------------------------------------------- 4. onset/carve

def _onset_records(eye):
    out = []
    for nid in eye.substrate.nodes("RetinalOnsetEvent"):
        attrs = dict(eye.substrate.node(nid)["attrs"])
        out.append(tuple(sorted((k, repr(v)) for k, v in attrs.items())))
    return sorted(out)


def test_rod_onset_and_carve_unchanged_with_cones_on():
    n_az, n_el = 12, 10
    rng_seed = 166000
    results = {}
    for cones in (False, True):
        rng = np.random.default_rng(rng_seed)
        eye = _eye({"retina_2d_cones": cones}, n_az=n_az, n_el=n_el)
        try:
            for _ in range(8):
                _tick(eye, [])
            lo = eye._epoch + 1
            for col in range(4, 10):         # luminance step sweeping L->R
                pkts = [{"col": col, "row": row, "wavelength_nm": 500.0,
                         "count": int(rng.poisson(2000))} for row in (2, 3)]
                _tick(eye, pkts)
            eye.settle_carve_2d(since_epoch=lo)
            eye.substrate._inner.run_cognitive_tasks(1)
            eye.substrate._inner.run_rules()
            rods = [dict(eye.substrate.node(eye._receptors[(f, "rod")])["attrs"])
                    for f in range(n_az * n_el)]
            results[cones] = (_onset_records(eye), eye.carve_polygons_2d(), rods)
            if cones:
                assert all(r["input_epoch"] == eye._epoch
                           for r in eye.percepts_2d())
        finally:
            eye.stop()
    off_onsets, off_polys, off_rods = results[False]
    on_onsets, on_polys, on_rods = results[True]
    assert len(off_onsets) > 0
    assert on_onsets == off_onsets
    assert len(off_polys) == 1
    assert on_polys == off_polys
    assert on_rods == off_rods


# ---------------------------------------------------------------- 5. refusals

@pytest.mark.parametrize("extra", [
    {"retina_accel": True},
    {"per_sensor_epoch": True},
    {"per_sensor_epoch_wrong": True},
    {"held_prediction": True},
    {"held_prediction": "decay"},
])
def test_unsupported_combinations_refused(extra):
    with pytest.raises(ValueError, match="retina_2d_cones is unsupported"):
        _eye({"retina_2d_cones": True, **extra})


@pytest.mark.parametrize("extra", [
    {"retina_accel": True}, {"per_sensor_epoch": True},
    {"held_prediction": True},
])
def test_refusal_only_applies_when_cones_on(extra):
    eye = _eye({"retina_2d_cones": False, **extra})
    eye.stop()
