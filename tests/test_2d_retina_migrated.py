"""THE 2-D EXPANSION — the gate (`VISION_2D_EXPANSION_PREREG.md`).

Rungs 1-4 (onset / motion / carve / salience) are 1-D because the photon eye is
a 1-D AZIMUTH STRIP (`domains/photon_eye.py`: `n_az` columns, elevation
collapsed). This rung extends the retina to a 2-D az×el RECEPTOR SHEET — each
`(col, row)` a cell with its OWN adapting rod + onset history, onset events
carrying `(col, row)` — and generalizes the common-fate CARVE from a 1-D column
to a 2-D cell grid.

HEADLINE (the falsifiable proof 2-D adds real capability): two objects at the
SAME azimuth but DIFFERENT elevation are ONE thing to the 1-D carve (elevation
collapsed → one azimuth span) and TWO things to the 2-D carve (two 8-connected
components at their correct `(az, el)`).

HONEST SCOPE: 2-D RETINA + 2-D ONSET + 2-D CARVE this rung. 2-D MOTION and 2-D
SALIENCE are NAMED FOLLOW-ONS. The 2-D carve splits objects by 2-D spatial
connectivity + a coherence/`n_events` gate; a velocity-split of spatially
touching different-motion objects is a named follow-on.

What this guards:
  1. THE PRIMITIVE, both kernels called directly on the SAME event set: the
     same-az/diff-el scene → 1-D carve 1 coherent run, 2-D carve 2 coherent
     components at the correct `(az, el)`.
  2. Controls: diff-az → 2/2 (2-D does not over-split); static → 0/0; scrambled
     epochs → the coherent count COLLAPSES toward 0 (a distribution control, see
     the note on small-sample coherence).
  3. Two objects same-az/diff-el carved end-to-end through the REAL 2-D mint rule
     off the 2-D eye build → EXACTLY 2 `VisionPolygon`s.
  4. DEFAULT OFF: `retina_2d` off ⇒ no 2-D nodes/seeds, `settle_carve_2d` a
     no-op; the 1-D carve path still works unchanged.
  5. MERGE-BLOCK SOURCE AUDIT: `settle_carve_2d` reads ONLY the event stream.
  6. §10 PROVENANCE: the engine is a build of this tree's Rust.
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

SEED = 166000
N_AZ, N_EL = 16, 12
BRIGHT = 2000
WARMUP = 8
MIN_COHERENCE = 0.5
MIN_EVENTS = 2.5
S1 = 7   # 1-D kernel per-column stride
S2 = 9   # 2-D kernel per-cell stride


# --- kernel harness --------------------------------------------------------

def _run_kernel(kind, payload):
    s = srs.Substrate()
    t = s.add_node("CognitiveTask", {
        "status": "requested", "kind": kind,
        "payload": [float(v) for v in payload],
        "input_epoch": 1, "logical_time": 0, "area": "global"})
    s._inner.run_cognitive_tasks(1)
    return list(s.node(t)["attrs"]["output"])


def _pack1(n_az, events, max_gap=1.0, vel_tol=0.35):
    p = [float(n_az), float(max_gap), float(vel_tol), float(len(events))]
    for c, e in events:
        p.extend([float(c), float(e)])
    return p


def _pack2(n_az, n_el, events, max_gap=1.0, vel_tol=0.35):
    p = [float(n_az), float(n_el), float(max_gap), float(vel_tol),
         float(len(events))]
    for c, r, e in events:
        p.extend([float(c), float(r), float(e)])
    return p


def _coherent_1d(out, n_az):
    return [c for c in range(n_az)
            if out[c * S1] == 1.0
            and out[c * S1 + 5] > MIN_COHERENCE
            and out[c * S1 + 6] > MIN_EVENTS]


def _coherent_2d(out, n_az, n_el):
    return [f for f in range(n_az * n_el)
            if out[f * S2] == 1.0
            and out[f * S2 + 7] > MIN_COHERENCE
            and out[f * S2 + 8] > MIN_EVENTS]


def _same_az_diff_el_events(cols=range(4, 10), rows_a=(2, 3), rows_b=(8, 9)):
    """Two objects at the SAME azimuth columns, one L->R common fate
    (epoch = col - cols[0]), separated ONLY in elevation."""
    c0 = list(cols)[0]
    ev = []
    for row in list(rows_a) + list(rows_b):
        for col in cols:
            ev.append((col, row, col - c0))
    return ev


# --- 1. THE HEADLINE: same primitive, 1-D conflates, 2-D separates ---------

def test_kernel_2d_separates_what_1d_conflates_at_same_azimuth():
    ev3 = _same_az_diff_el_events()
    ev2 = [(c, e) for (c, r, e) in ev3]      # collapse elevation for the 1-D carve

    out1 = _run_kernel("retinal_common_fate_carve", _pack1(N_AZ, ev2))
    out2 = _run_kernel("retinal_common_fate_carve_2d", _pack2(N_AZ, N_EL, ev3))
    c1 = _coherent_1d(out1, N_AZ)
    c2 = _coherent_2d(out2, N_AZ, N_EL)
    print(f"\nHEADLINE  1-D coherent runs={len(c1)}  2-D coherent comps={len(c2)}")

    # 1-D: elevation collapsed → the two objects are ONE azimuth span.
    assert len(c1) == 1, f"1-D carve must conflate to 1 span, got {c1}"
    assert out1[c1[0] * S1 + 1] == 4.0 and out1[c1[0] * S1 + 2] == 9.0

    # 2-D: TWO components, one per elevation band, at the correct (az, el).
    assert len(c2) == 2, f"2-D carve must separate into 2 comps, got {c2}"
    spans = sorted(
        (int(out2[f * S2 + 1]), int(out2[f * S2 + 2]),
         int(out2[f * S2 + 3]), int(out2[f * S2 + 4]),
         int(out2[f * S2 + 5]))
        for f in c2)
    assert spans[0] == (4, 9, 2, 3, 1), f"object A (col4-9,row2-3,+1), got {spans[0]}"
    assert spans[1] == (4, 9, 8, 9, 1), f"object B (col4-9,row8-9,+1), got {spans[1]}"


# --- 2. controls: diff-az (no over-split), static ---------------------------

def test_kernel_2d_does_not_oversplit_when_1d_already_separates():
    """Two objects at DIFFERENT azimuth → BOTH carves give 2 (2-D adds no split
    the 1-D carve doesn't already make)."""
    ev3 = []
    for row in (4, 5):
        for col in range(0, 4):
            ev3.append((col, row, col))
    for row in (4, 5):
        for col in range(10, 14):
            ev3.append((col, row, col))
    ev2 = [(c, e) for (c, r, e) in ev3]
    n1 = len(_coherent_1d(_run_kernel(
        "retinal_common_fate_carve", _pack1(N_AZ, ev2)), N_AZ))
    n2 = len(_coherent_2d(_run_kernel(
        "retinal_common_fate_carve_2d", _pack2(N_AZ, N_EL, ev3)), N_AZ, N_EL))
    print(f"\nDIFF-AZ  1-D={n1}  2-D={n2}")
    assert n1 == 2 and n2 == 2, f"both carves separate diff-az, got 1-D={n1} 2-D={n2}"


def test_kernel_static_field_carves_nothing_in_2d():
    n2 = len(_coherent_2d(_run_kernel(
        "retinal_common_fate_carve_2d", _pack2(N_AZ, N_EL, [])), N_AZ, N_EL))
    print(f"\nSTATIC 2-D={n2}")
    assert n2 == 0


# --- 3. scrambled epochs: the coherent count COLLAPSES toward 0 -------------

def test_scrambled_epochs_collapse_the_coherent_count():
    """The structured scene gives (1-D=1, 2-D=2). Shuffling the per-event epochs
    destroys the common-fate diagonal, so the coherent count COLLAPSES toward 0.

    A single random shuffle of a small (~12-cell) component is a SMALL-SAMPLE-
    NOISY incoherence test: ~20% of seeds leave a spurious |r|>0.5 in 2-D (~14%
    in 1-D — the EXISTING 1-D carve shares this). So the control is expressed as
    a DISTRIBUTION over a fixed 200-seed sweep: the MEAN coherent count must be
    far below the structured value (a mechanism that ignored the shuffle would
    hold at ~2). Robustifies to per-seed 0 as components grow (see results)."""
    ev3 = _same_az_diff_el_events()
    # structured baseline
    assert len(_coherent_2d(_run_kernel(
        "retinal_common_fate_carve_2d", _pack2(N_AZ, N_EL, ev3)), N_AZ, N_EL)) == 2

    tot1 = tot2 = 0
    trials = 200
    sp2 = 0
    for sd in range(SEED, SEED + trials):
        rng = np.random.default_rng(sd)
        eps = np.array([e for (_c, _r, e) in ev3], dtype=float)
        rng.shuffle(eps)
        evs = [(c, r, eps[i]) for i, (c, r, _e) in enumerate(ev3)]
        ev2s = [(c, e) for (c, r, e) in evs]
        n1 = len(_coherent_1d(_run_kernel(
            "retinal_common_fate_carve", _pack1(N_AZ, ev2s)), N_AZ))
        n2 = len(_coherent_2d(_run_kernel(
            "retinal_common_fate_carve_2d", _pack2(N_AZ, N_EL, evs)), N_AZ, N_EL))
        tot1 += n1
        tot2 += n2
        sp2 += 1 if n2 > 0 else 0
    mean1, mean2 = tot1 / trials, tot2 / trials
    print(f"\nSCRAMBLE sweep({trials}): mean 1-D={mean1:.3f} (struct 1) "
          f"mean 2-D={mean2:.3f} (struct 2)  2-D spurious {sp2}/{trials}")
    assert mean1 < 0.5, f"scramble must collapse 1-D far below 1, got {mean1}"
    assert mean2 < 0.75, f"scramble must collapse 2-D far below 2, got {mean2}"


def test_scrambled_epochs_are_deterministically_incoherent_at_scale():
    """As components grow the coherence gate sharpens to a crisp per-seed 0: a
    4x10-cell object at the committed seed 166000 → EXACTLY 0 coherent comps."""
    cols = range(3, 13)
    ev3 = _same_az_diff_el_events(cols=cols, rows_a=(2, 3, 4, 5),
                                  rows_b=(10, 11, 12, 13))
    # structured → 2
    assert len(_coherent_2d(_run_kernel("retinal_common_fate_carve_2d",
              _pack2(N_AZ, N_EL, ev3)), N_AZ, N_EL)) == 2
    rng = np.random.default_rng(SEED)
    eps = np.array([e for (_c, _r, e) in ev3], dtype=float)
    rng.shuffle(eps)
    evs = [(c, r, eps[i]) for i, (c, r, _e) in enumerate(ev3)]
    n2 = len(_coherent_2d(_run_kernel(
        "retinal_common_fate_carve_2d", _pack2(N_AZ, N_EL, evs)), N_AZ, N_EL))
    print(f"\nSCRAMBLE at scale (seed {SEED}): 2-D coherent={n2}")
    assert n2 == 0


# --- 4. end-to-end through the REAL 2-D eye + mint rule ---------------------

def _eye2d(n_az=N_AZ, n_el=N_EL):
    ctx = {"synchronous": True, "worker_capacity": 1, "retina_2d": True}
    return GraphEye(n_az=n_az, n_el=n_el, context=ctx).build()


def _frame2d(eye, packets):
    eye.submit_photons_2d(packets)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _bright_cell(col, row, rng):
    return {"col": int(col), "row": int(row), "wavelength_nm": 500.0,
            "count": int(rng.poisson(BRIGHT))}


def test_two_objects_same_az_diff_el_carve_as_two_polygons_end_to_end():
    """PRE-REGISTERED HEADLINE end-to-end: two objects at the SAME azimuth cols
    4-9, one L->R common fate, object A rows 2-3 and B rows 8-9, driven through
    the 2-D eye build and the REAL `retinal_mint_carve_2d` rule → EXACTLY 2
    VisionPolygons at the correct (az, el)."""
    rng = np.random.default_rng(SEED)
    eye = _eye2d()
    for _ in range(WARMUP):
        _frame2d(eye, [])
    lo = eye._epoch + 1
    for col in range(4, 10):                       # both objects sweep L->R
        pkts = [_bright_cell(col, row, rng) for row in (2, 3, 8, 9)]
        _frame2d(eye, pkts)
    eye.settle_carve_2d(since_epoch=lo)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    print(f"\nEND-TO-END 2-D: "
          f"{[(p['col_min'], p['col_max'], p['row_min'], p['row_max'], p['direction']) for p in polys]}")
    assert len(polys) == 2, f"exactly 2 polygons expected, got {len(polys)}"
    a, b = polys[0], polys[1]                       # sorted by (row_min, col_min)
    assert (a["col_min"], a["col_max"], a["row_min"], a["row_max"]) == (4, 9, 2, 3)
    assert (b["col_min"], b["col_max"], b["row_min"], b["row_max"]) == (4, 9, 8, 9)
    assert a["direction"] == 1.0 and b["direction"] == 1.0
    assert a["coherence"] > MIN_COHERENCE and b["coherence"] > MIN_COHERENCE
    # correct (az, el): the two share az but differ in el.
    assert abs(a["az_min"] - b["az_min"]) < 1e-9, "same azimuth"
    assert a["el_max"] < b["el_min"], "A is below B in elevation, non-overlapping"


# --- 5. default OFF / byte-identity of the 1-D path -------------------------

def test_retina_2d_is_off_by_default_and_1d_carve_still_works():
    # OFF by default: no 2-D nodes, settle_carve_2d a no-op.
    off = GraphEye(n_az=8, context={"synchronous": True}).build()
    assert off._retina_2d is False
    assert off.substrate.nodes("RetinaCarveParams2d") == []
    assert off.substrate.nodes("RetinaOnsetParams2d") == []
    assert off.settle_carve_2d() is None
    off.stop()

    # the 1-D carve path is unchanged: two diff-fate objects still → 2 polygons.
    rng = np.random.default_rng(SEED)
    eye = GraphEye(n_az=16, context={
        "synchronous": True, "worker_capacity": 1, "visual_carve": True}).build()
    assert eye._retina_2d is False
    for _ in range(WARMUP):
        eye.submit_photons([]); eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
    lo = eye._epoch + 1
    for c in list(range(0, 6)) + list(range(15, 9, -1)):
        eye.submit_photons([{"column": int(c), "wavelength_nm": 500.0,
                             "count": int(rng.poisson(BRIGHT))}])
        eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
    eye.settle_carve(since_epoch=lo)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons()
    print(f"\n1-D CARVE UNCHANGED: {len(polys)} polygons")
    assert len(polys) == 2, f"1-D carve path must be unchanged, got {len(polys)}"
    eye.stop()


# --- 6. merge-block source audit: 2-D carve reads ONLY the event stream -----

def test_2d_carve_is_derived_from_the_event_stream_not_a_raster():
    src = inspect.getsource(GraphEye.settle_carve_2d)
    assert "RetinalOnsetEvent" in src
    assert "column_index" in src and "row_index" in src and "epoch" in src
    for forbidden in ("retinal_field", "vector_field", "retinal_flow_depth",
                      "_previous_field", "PhotonExposure",
                      "native.segment", "segment_motion", "segment_and_track"):
        assert forbidden not in src, (
            f"MERGE-BLOCK: settle_carve_2d must not touch {forbidden!r}")


# --- 7. provenance ---------------------------------------------------------

def test_engine_is_a_build_of_this_tree():
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), (
        f"engine source verdict {p['source_match']!r}")
