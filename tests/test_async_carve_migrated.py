"""ASYNC COMMON-FATE CARVE — the gate (`VISION_ASYNC_CARVE_PREREG.md`).

Rung 3 of the photon-eye migration. The photon eye declares `VisionPolygon` but
never produced one (`"polygons": []`). This rung CARVES objects from the
ASYNCHRONOUS onset-event stream (`RetinalOnsetEvent` nodes, Rung 1) by COMMON
FATE: contiguous retinal columns whose events share ONE coherent motion group
into ONE `VisionPolygon` azimuth span; columns carrying a DIFFERENT common-fate
motion form a DIFFERENT polygon; a static/incoherent field carves nothing. The
carve reads the SAME async event stream Rung 2 reads (`RetinalOnsetEvent`
column+own-epoch), NOT the coarse `retinal_field` raster and NOT
`native.segment` / `native.segment_motion` (the raster carves).

HONEST SCOPE: the photon eye is a 1-D AZIMUTH STRIP, so this carve is 1-D
(contiguous azimuth spans). A true 2-D carve (azimuth×elevation objects) needs
the retina extended to elevation columns first — a named follow-on, not this rung.

What this guards:
  1. THE PRIMITIVE, called directly (CognitiveTask round-trip): two objects of
     DIFFERENT common fate → exactly 2 group starts, spans + signs correct;
     one uniform motion → 1; a scrambled-epoch set → 0 coherent runs.
  2. TWO objects → EXACTLY 2 `VisionPolygon`s through the REAL mint rule, each
     span covering its object and each direction sign matching its object.
  3. ONE uniform motion → 1 `VisionPolygon`.
  4. STATIC (dark) → no events → 0 polygons.
  5. SCRAMBLED → 0 polygons through the REAL mint rule (the velocity-consistency
     segmentation fragments below `min_events` / decorrelates below
     `min_coherence`, so the rule declines).
  6. DEFAULT OFF: flag off ⇒ no carve params, no carve task, no polygon, plain
     kind; existing paths byte-identical.
  7. MERGE-BLOCK SOURCE AUDIT: `settle_carve` reads ONLY the event stream
     (`RetinalOnsetEvent` attrs), never the raster / a frame diff.
  8. §10 PROVENANCE: the engine is a build of this tree's Rust.
"""
from __future__ import annotations

import inspect
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import substrate_rs as srs  # noqa: E402
from domains.photon_eye import GraphEye, _add_edge  # noqa: E402
from domains.engine_provenance import engine_provenance  # noqa: E402

SEED = 163000
BRIGHT = 2000
WARMUP = 8  # dark frames so each column's floor adapts before the sweep
MIN_COHERENCE = 0.5  # the adapter's default RetinaCarveParams.min_coherence
MIN_EVENTS = 2.5     # the adapter's default RetinaCarveParams.min_events
STRIDE = 7           # the kernel's per-column output block


# --- 1. the Rust DECISION primitive, called directly ----------------------

def _run_kernel(s, payload):
    t = s.add_node("CognitiveTask", {
        "status": "requested", "kind": "retinal_common_fate_carve",
        "payload": [float(v) for v in payload],
        "input_epoch": 1, "logical_time": 0, "area": "global"})
    s._inner.run_cognitive_tasks(1)
    return list(s.node(t)["attrs"]["output"])


def _pack(n_az, events, max_gap=1.0, vel_tol=0.35):
    """Serialise (column, epoch) events into the carve kernel payload."""
    payload = [float(n_az), float(max_gap), float(vel_tol), float(len(events))]
    for c, e in events:
        payload.extend([float(c), float(e)])
    return payload


def _starts(out, n_az):
    return [c for c in range(n_az) if out[c * STRIDE] == 1.0]


def test_kernel_groups_two_motions_one_motion_and_declines_scrambled():
    s = srs.Substrate()
    n_az = 16
    # Object A: cols 0..5 sweep L→R (epoch=col, slope +1). Object B: cols 10..15
    # sweep R→L in a later window (epoch=40−col, slope −1); a static gap 6..9.
    a = [(c, c) for c in range(0, 6)]
    b = [(c, 40 - c) for c in range(10, 16)]
    out = _run_kernel(s, _pack(n_az, a + b))
    st = _starts(out, n_az)
    assert st == [0, 10], f"two common-fate runs anchored at 0 and 10, got {st}"
    # A: span 0..5, +1, coherence 1
    assert out[0 * STRIDE + 1] == 0.0 and out[0 * STRIDE + 2] == 5.0
    assert out[0 * STRIDE + 3] == 1.0, "A is L→R (+1)"
    assert abs(out[0 * STRIDE + 5] - 1.0) < 1e-9 and out[0 * STRIDE + 6] == 6.0
    # B: span 10..15, −1, coherence 1
    assert out[10 * STRIDE + 1] == 10.0 and out[10 * STRIDE + 2] == 15.0
    assert out[10 * STRIDE + 3] == -1.0, "B is R→L (−1)"
    assert abs(out[10 * STRIDE + 5] - 1.0) < 1e-9

    # ONE uniform motion: the whole 16-col strip L→R → a single run.
    uni = [(c, c) for c in range(16)]
    out1 = _run_kernel(s, _pack(n_az, uni))
    assert _starts(out1, n_az) == [0], "one uniform motion is one group"
    assert out1[3] == 1.0 and out1[6] == 16.0

    # SCRAMBLED CONTROL: the SAME columns, epochs shuffled — the space-time
    # structure is destroyed, the velocity-consistency segmentation fragments.
    rng = np.random.default_rng(SEED)
    cols = [c for c, _e in uni]
    eps = [e for _c, e in uni]
    rng.shuffle(eps)
    scrambled = sorted(zip(cols, eps), key=lambda ce: (ce[0], ce[1]))
    outs = _run_kernel(s, _pack(n_az, scrambled))
    coherent = [c for c in _starts(outs, n_az)
                if outs[c * STRIDE + 5] > MIN_COHERENCE
                and outs[c * STRIDE + 6] > MIN_EVENTS]
    print(f"\nCARVE KERNEL: two→{st} one→{_starts(out1, n_az)} "
          f"scrambled_coherent_runs={len(coherent)}")
    assert coherent == [], (
        "a scrambled span mints no coherent multi-column run — the shared "
        "velocity is the common fate, and it is gone")


# --- the synchronous world harness ----------------------------------------

def _eye(n_az=16, carve=True):
    ctx = {"synchronous": True, "worker_capacity": 1}
    if carve:
        ctx["visual_carve"] = True
    return GraphEye(n_az=n_az, context=ctx).build()


def _frame(eye, packets):
    eye.submit_photons(packets)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _bright(cols, rng):
    return [{"column": int(c), "wavelength_nm": 500.0,
             "count": int(rng.poisson(BRIGHT))} for c in cols]


def _sweep(eye, columns, rng):
    for c in columns:
        _frame(eye, _bright([c], rng))


def _settle_and_mint(eye, since_epoch):
    eye.settle_carve(since_epoch=since_epoch)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    return eye.carve_polygons()


# --- 2. two objects → EXACTLY two polygons (the headline) ------------------

def test_two_common_fate_objects_carve_as_two_polygons():
    """PRE-REGISTERED HEADLINE: two objects of DIFFERENT common fate carve into
    EXACTLY 2 `VisionPolygon`s; each span covers its object and each direction
    sign matches its object (A → +1 L→R, B → −1 R→L)."""
    rng = np.random.default_rng(SEED)
    n_az = 16
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    _sweep(eye, list(range(0, 6)), rng)          # A: cols 0..5 L→R
    _sweep(eye, list(range(15, 9, -1)), rng)     # B: cols 15..10 R→L
    polys = _settle_and_mint(eye, since_epoch=lo)
    print(f"\nCARVE EYE two-object: "
          f"{[(p['col_min'], p['col_max'], p['direction']) for p in polys]}")
    assert len(polys) == 2, f"exactly two polygons expected, got {len(polys)}"
    a, b = polys[0], polys[1]                      # carve_polygons sorts by col_min
    assert (a["col_min"], a["col_max"]) == (0, 5), f"object A span, got {a}"
    assert a["direction"] == 1.0, f"object A is L→R (+1), got {a}"
    assert (b["col_min"], b["col_max"]) == (10, 15), f"object B span, got {b}"
    assert b["direction"] == -1.0, f"object B is R→L (−1), got {b}"
    assert a["coherence"] > MIN_COHERENCE and b["coherence"] > MIN_COHERENCE
    eye.stop()


# --- 3. one uniform motion → one polygon -----------------------------------

def test_one_uniform_motion_carves_as_one_polygon():
    rng = np.random.default_rng(SEED)
    n_az = 16
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    _sweep(eye, list(range(0, n_az)), rng)        # whole strip L→R
    polys = _settle_and_mint(eye, since_epoch=lo)
    print(f"\nCARVE EYE one-motion: "
          f"{[(p['col_min'], p['col_max'], p['direction']) for p in polys]}")
    assert len(polys) == 1, f"one polygon expected, got {len(polys)}"
    assert polys[0]["direction"] == 1.0
    assert polys[0]["col_min"] == 0 and polys[0]["col_max"] == n_az - 1
    eye.stop()


# --- 4. static (dark) → no events → no polygon -----------------------------

def test_static_dark_field_carves_nothing():
    n_az = 16
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    for _ in range(8):
        _frame(eye, [])                            # dark: no onset events
    polys = _settle_and_mint(eye, since_epoch=lo)
    print(f"\nCARVE EYE static: polygons={len(polys)}")
    assert polys == [], f"a dark scene carves nothing, got {polys}"
    eye.stop()


# --- 5. scrambled through the REAL mint rule -------------------------------

def test_scrambled_event_times_carve_no_polygon():
    """The mint RULE (not just the kernel) declines a scrambled event set."""
    rng = np.random.default_rng(SEED + 1)
    n_az = 16
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    _sweep(eye, list(range(0, n_az)), rng)

    events = []
    for node in eye.substrate.nodes("RetinalOnsetEvent"):
        a = eye.substrate.node(node)["attrs"]
        if float(a["epoch"]) >= lo:
            events.append((float(a["column_index"]), float(a["epoch"])))
    assert len(events) >= 6
    cols = [c for c, _e in events]
    eps = [e for _c, e in events]
    rng.shuffle(eps)
    scr = sorted(zip(cols, eps), key=lambda ce: (ce[0], ce[1]))
    payload = _pack(n_az, scr)

    task = eye.substrate.add_node("CognitiveTask", {
        "status": "requested", "kind": "retinal_common_fate_carve",
        "payload": payload, "input_epoch": eye._epoch, "logical_time": 999,
        "area": "retina", "order": 3, "salience": 1.0})
    _add_edge(eye.substrate._inner, eye._retina, "has_carve_task", task)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons()
    print(f"\nCARVE SCRAMBLED (rule): polygons={len(polys)}")
    assert polys == [], (
        "the mint rule must decline a scrambled (incoherent) event set")
    eye.stop()


# --- 6. default OFF / byte-identity ----------------------------------------

def test_carve_path_is_off_by_default():
    eye = _eye(n_az=8, carve=False)
    assert eye._carve_enabled is False
    assert eye._onset_kind == "photon_transduce", "flag off ⇒ plain kind"
    assert eye.substrate.nodes("RetinaCarveParams") == [], "no params node when off"
    assert eye.settle_carve() is None, "settle_carve is a no-op when off"
    rng = np.random.default_rng(SEED)
    for c in range(8):
        _frame(eye, _bright([c], rng))
    assert eye.substrate.nodes("VisionPolygon") == [], (
        "no polygon may be minted with the carve path off")
    # _read_snapshot still reports the pre-Rung-3 empty polygons list.
    snap = eye._read_snapshot(eye._epoch)
    assert snap["polygons"] == []
    eye.stop()


# --- 7. merge-block source audit: carve reads ONLY the event stream --------

def test_carve_is_derived_from_the_event_stream_not_a_raster_or_frame_diff():
    src = inspect.getsource(GraphEye.settle_carve)
    assert "RetinalOnsetEvent" in src, "carve must read the onset EVENT STREAM"
    assert "column_index" in src and "epoch" in src, (
        "carve reads each event's column + own epoch")
    for forbidden in ("retinal_field", "vector_field", "retinal_flow_depth",
                      "_previous_field", "PhotonExposure",
                      "native.segment", "segment_motion", "segment_and_track"):
        assert forbidden not in src, (
            f"MERGE-BLOCK: settle_carve must not touch {forbidden!r} — the carve "
            "groups the async event stream, never a raster / frame diff / "
            "native.segment")


# --- 8. provenance ---------------------------------------------------------

def test_engine_is_a_build_of_this_tree():
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), (
        f"engine source verdict {p['source_match']!r} — see "
        "test_engine_provenance_migrated.py")
