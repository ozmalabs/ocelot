"""CLOSING THE 2-D LOOP — the gate (`VISION_2D_MOTION_SALIENCE_PREREG.md`).

The 2-D expansion (block 166000) made the RETINA, the ONSET events, and the
CARVE 2-D (az×el), but left the MOTION and SALIENCE kernels 1-D — they read
azimuth (`column_index`) only. This rung generalizes both so the whole
event-native pipeline (onset → motion → carve → salience) is 2-D, via two NEW
Rust `CognitiveTask` kinds (NO new DSL Term enum variant; the 1-D kinds
byte-untouched, exactly as 166000 added `retinal_common_fate_carve_2d`).

HEADLINE (falsifiable, same shape as the 2-D carve's same-az/diff-el):
  PURE-ELEVATION motion is INVISIBLE to the 1-D motion kernel (azimuth-only →
  it reports speed 0 / coherence 0) but the 2-D kernel RECOVERS it (correct
  `v_el`, sign, coherence ≈ 1); and the 2-D residual salience RANKS a vertical
  mover the 1-D salience MISSES. 1-D blind, 2-D sees.

What this guards:
  1. THE HEADLINE, both motion kernels on the SAME event set: pure-elevation →
     1-D (speed 0, coh 0), 2-D (v_el=+1, v_az≈0, coh≈1). Sign flips on reversal.
  2. Motion controls: pure-azimuth → BOTH see (2-D keeps the 1-D case, v_el≈0);
     diagonal → 2-D recovers BOTH; static → 0; scrambled → low coherence.
  3. THE SALIENCE HEADLINE, both kernels on the SAME event set: a pure-elevation
     mover against an azimuth background → 1-D max residual ≈ 0 (blind), 2-D max
     residual at exactly the mover cells (≈ |(v_az,v_el)|).
  4. End-to-end through the REAL 2-D mint rules off the 2-D eye build.
  5. DEFAULT OFF: without `visual_motion`/`visual_salience` the 2-D-carve build
     has no motion/salience params, `settle_*_2d` no-ops; the carve path works.
  6. MERGE-BLOCK SOURCE AUDIT: `settle_motion_2d`/`settle_salience_2d` read ONLY
     the event stream.
  7. §10 PROVENANCE: the engine is a build of this tree's Rust.
"""
from __future__ import annotations

import inspect
import math
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

import substrate_rs as srs  # noqa: E402
from domains.photon_eye import GraphEye  # noqa: E402
from domains.engine_provenance import engine_provenance  # noqa: E402

SEED = 170000
N_AZ, N_EL = 16, 12
BRIGHT = 2000
WARMUP = 8
MIN_COHERENCE = 0.5
MIN_EVENTS = 2.5
SM = 3   # 2-D salience per-cell stride


# --- kernel harness --------------------------------------------------------

def _run_kernel(kind, payload):
    s = srs.Substrate()
    t = s.add_node("CognitiveTask", {
        "status": "requested", "kind": kind,
        "payload": [float(v) for v in payload],
        "input_epoch": 1, "logical_time": 0, "area": "global"})
    s._inner.run_cognitive_tasks(1)
    return list(s.node(t)["attrs"]["output"])


def _motion2(events):
    p = [float(len(events))]
    for c, r, e in events:
        p.extend([float(c), float(r), float(e)])
    return _run_kernel("retinal_event_motion_2d", p)


def _motion1(events):
    """1-D motion on the SAME events, elevation COLLAPSED to (col, epoch)."""
    p = [float(len(events))]
    for c, r, e in events:
        p.extend([float(c), float(e)])
    return _run_kernel("retinal_event_motion", p)


def _sal2(events, n_az=N_AZ, n_el=N_EL, mg=1.0, vt=0.35):
    p = [float(n_az), float(n_el), float(mg), float(vt), float(len(events))]
    for c, r, e in events:
        p.extend([float(c), float(r), float(e)])
    return _run_kernel("retinal_residual_salience_2d", p)


def _sal1(events, n_az=N_AZ, mg=1.0, vt=0.35):
    p = [float(n_az), float(mg), float(vt), float(len(events))]
    for c, r, e in events:
        p.extend([float(c), float(e)])          # collapse elevation
    return _run_kernel("retinal_residual_salience", p)


# ===========================================================================
# 1. THE MOTION HEADLINE — pure elevation: 1-D BLIND, 2-D SEES
# ===========================================================================

def test_motion_pure_elevation_is_invisible_to_1d_and_recovered_by_2d():
    # col fixed at 8; rows 2..7 sweep DOWNWARD one step per epoch.
    ev = [(8, r, r - 2) for r in range(2, 8)]

    out1 = _motion1(ev)          # (direction, speed, residual, coherence, n)
    out2 = _motion2(ev)          # (v_az, v_el, dir_az, dir_el, speed, resid, coh, n)
    print(f"\nMOTION pure-el  1-D speed={out1[1]:.3f} coh={out1[3]:.3f} | "
          f"2-D v_az={out2[0]:.3f} v_el={out2[1]:.3f} coh={out2[6]:.3f}")

    # 1-D: all events share ONE column → zero azimuth spread → BLIND.
    assert out1[1] == 0.0, f"1-D speed must be 0 (blind), got {out1[1]}"
    assert out1[3] == 0.0, f"1-D coherence must be 0 (blind), got {out1[3]}"

    # 2-D: recovers v_el with the CORRECT SIGN and MAGNITUDE, v_az≈0, coh≈1.
    assert abs(out2[0]) < 1e-9, f"2-D v_az must be ~0, got {out2[0]}"
    assert abs(out2[1] - 1.0) < 1e-9, f"2-D v_el must be +1, got {out2[1]}"
    assert out2[3] == 1.0, f"2-D dir_el must be +1, got {out2[3]}"
    assert out2[6] > 0.99, f"2-D coherence must be ~1, got {out2[6]}"


def test_motion_elevation_sign_flips_when_the_sweep_reverses():
    down = [(8, r, r - 2) for r in range(2, 8)]        # rows increase with epoch
    up = [(8, r, 7 - r) for r in range(2, 8)]          # rows decrease with epoch
    vd = _motion2(down)[1]
    vu = _motion2(up)[1]
    print(f"\nMOTION sign  down v_el={vd:.3f}  up v_el={vu:.3f}")
    assert vd > 0.99 and vu < -0.99, f"sign must flip: down={vd}, up={vu}"


# ===========================================================================
# 2. MOTION able-to-fail controls
# ===========================================================================

def test_motion_pure_azimuth_is_seen_by_both_2d_keeps_the_1d_case():
    ev = [(c, 5, c - 3) for c in range(3, 10)]         # row fixed, cols sweep
    out1 = _motion1(ev)
    out2 = _motion2(ev)
    print(f"\nMOTION pure-az  1-D speed={out1[1]:.3f} coh={out1[3]:.3f} | "
          f"2-D v_az={out2[0]:.3f} v_el={out2[1]:.3f} coh={out2[6]:.3f}")
    # 1-D sees it.
    assert abs(out1[1] - 1.0) < 1e-9 and out1[3] > 0.99
    # 2-D does NOT lose the 1-D case: v_az=+1, v_el≈0, coh≈1.
    assert abs(out2[0] - 1.0) < 1e-9, f"2-D v_az must be +1, got {out2[0]}"
    assert abs(out2[1]) < 1e-9, f"2-D v_el must be ~0, got {out2[1]}"
    assert out2[6] > 0.99


def test_motion_diagonal_recovers_both_components():
    ev = [(c, c, c - 3) for c in range(3, 10)]         # col AND row step w/ epoch
    out2 = _motion2(ev)
    print(f"\nMOTION diagonal  v_az={out2[0]:.3f} v_el={out2[1]:.3f} "
          f"speed={out2[4]:.3f} coh={out2[6]:.3f}")
    assert abs(out2[0] - 1.0) < 1e-9 and abs(out2[1] - 1.0) < 1e-9
    assert out2[2] == 1.0 and out2[3] == 1.0            # both directions +
    assert abs(out2[4] - math.sqrt(2.0)) < 1e-9         # |(1,1)|
    assert out2[6] > 0.99


def test_motion_static_field_is_zero_in_2d():
    out2 = _motion2([])
    print(f"\nMOTION static  v_az={out2[0]} v_el={out2[1]} coh={out2[6]} n={out2[7]}")
    assert out2[0] == 0.0 and out2[1] == 0.0 and out2[6] == 0.0 and out2[7] == 0.0


def test_motion_scrambled_epochs_collapse_coherence():
    """A diagonal sweep is coherent (coh≈1); shuffling the per-event epochs
    destroys the space-time structure so coherence collapses far below the
    0.5 mint gate (a distribution control over a fixed seed sweep)."""
    ev = [(c, c, c - 3) for c in range(3, 13)]          # 10-cell diagonal
    assert _motion2(ev)[6] > 0.99                       # structured baseline
    tot = 0.0
    trials = 100
    fired = 0
    for sd in range(SEED, SEED + trials):
        rng = np.random.default_rng(sd)
        eps = np.array([e for (_c, _r, e) in ev], dtype=float)
        rng.shuffle(eps)
        evs = [(c, r, eps[i]) for i, (c, r, _e) in enumerate(ev)]
        coh = _motion2(evs)[6]
        tot += coh
        fired += 1 if coh > MIN_COHERENCE else 0
    mean = tot / trials
    print(f"\nMOTION scramble sweep({trials}): mean coh={mean:.3f} "
          f"(struct 1.0); above-gate {fired}/{trials}")
    assert mean < 0.5, f"scramble must collapse coherence, got mean {mean}"


# ===========================================================================
# 3. THE SALIENCE HEADLINE — vertical mover: 1-D MISSES, 2-D RANKS
# ===========================================================================

def _background_plus_vertical_mover():
    """Dominant azimuth-sweeping background (rows 6-9, cols 0-15, epoch=col) +
    a spatially-separated PURE-ELEVATION mover (col 12, rows 0-2, epochs
    11,12,13 — timed so the 1-D collapse of col 12 stays consistent with the
    background run, i.e. the mover is genuinely INVISIBLE to azimuth-only
    salience). Gap rows 3-5 separates the two 2-D components."""
    bg = [(c, r, c) for r in (6, 7, 8, 9) for c in range(0, 16)]
    mv = [(12, r, 11 + r) for r in range(0, 3)]
    return bg + mv, mv


def test_salience_vertical_mover_missed_by_1d_ranked_by_2d():
    ev, mover = _background_plus_vertical_mover()
    out1 = _sal1(ev)
    out2 = _sal2(ev)

    # 1-D: max residual over all firing columns.
    max1 = max(out1[c * SM + 2] for c in range(N_AZ) if out1[c * SM] == 1.0)
    # 2-D: the cell with the largest residual, and its (col, row).
    best_flat = max(
        (f for f in range(N_AZ * N_EL) if out2[f * SM] == 1.0),
        key=lambda f: out2[f * SM + 2])
    best_res = out2[best_flat * SM + 2]
    best_cr = (best_flat % N_AZ, best_flat // N_AZ)
    print(f"\nSALIENCE  1-D max residual={max1:.4f}  |  "
          f"2-D max residual={best_res:.4f} at {best_cr}")

    # 1-D is BLIND: elevation collapsed → the mover perturbs nothing → its
    # residual map is flat at ~0 (it reads only the uniform azimuth background).
    assert max1 < 0.5, f"1-D salience must MISS the vertical mover, got {max1}"

    # 2-D SEES it: the largest residual is at a MOVER cell, value ≈ |(v_az,v_el)|.
    assert best_cr in {(c, r) for (c, r, _e) in mover}, (
        f"2-D max salience must be at a mover cell, got {best_cr}")
    assert best_res > 1.0, f"2-D mover residual must be large, got {best_res}"

    # And every high-residual (>0.5) 2-D cell is a mover cell — the background
    # (which IS the dominant motion) has residual 0.
    hot = {(f % N_AZ, f // N_AZ) for f in range(N_AZ * N_EL)
           if out2[f * SM] == 1.0 and out2[f * SM + 2] > 0.5}
    assert hot == {(c, r) for (c, r, _e) in mover}, f"hot cells must be the mover, got {hot}"


def test_salience_static_field_is_empty_in_2d():
    out2 = _sal2([])
    assert all(out2[f * SM] == 0.0 for f in range(N_AZ * N_EL))


# ===========================================================================
# 4. END-TO-END through the REAL 2-D mint rules
# ===========================================================================

def _eye2d(**ctx):
    c = {"synchronous": True, "worker_capacity": 1, "retina_2d": True}
    c.update(ctx)
    return GraphEye(n_az=N_AZ, n_el=N_EL, context=c).build()


def _frame2d(eye, packets):
    eye.submit_photons_2d(packets)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()


def _bright(col, row, rng):
    return {"col": int(col), "row": int(row), "wavelength_nm": 500.0,
            "count": int(rng.poisson(BRIGHT))}


def test_motion_2d_end_to_end_recovers_pure_elevation_through_the_real_rule():
    rng = np.random.default_rng(SEED)
    eye = _eye2d(visual_motion=True)
    for _ in range(WARMUP):
        _frame2d(eye, [])
    lo = eye._epoch + 1
    for row in range(2, 8):                    # col 8 fixed, rows sweep down
        _frame2d(eye, [_bright(8, row, rng)])
    eye.settle_motion_2d(since_epoch=lo)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    percepts = eye.motion_percepts_2d()
    print(f"\nMOTION 2-D end-to-end: {[(round(p['v_az'],3), round(p['v_el'],3), round(p['coherence'],3)) for p in percepts]}")
    assert len(percepts) == 1, f"exactly 1 motion percept, got {len(percepts)}"
    p = percepts[0]
    assert abs(p["v_az"]) < 1e-9 and abs(p["v_el"] - 1.0) < 1e-9
    assert p["direction_el"] == 1.0 and p["coherence"] > 0.99
    eye.stop()


def test_salience_2d_end_to_end_ranks_the_vertical_mover_highest():
    rng = np.random.default_rng(SEED)
    eye = _eye2d(visual_salience=True)
    for _ in range(WARMUP):
        _frame2d(eye, [])
    lo = eye._epoch + 1
    # background azimuth sweep rows 6-9, one column per frame (epoch=col-ish).
    for c in range(0, 16):
        _frame2d(eye, [_bright(c, r, rng) for r in (6, 7, 8, 9)])
    # vertical mover: col 3, rows 0-2 (separated by gap rows 3-5), own sweep.
    for row in range(0, 3):
        _frame2d(eye, [_bright(3, row, rng)])
    eye.settle_salience_2d(since_epoch=lo)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    sal = eye.salience_percepts_2d()
    top = max(sal, key=lambda s: s["residual_salience"])
    mover = {(3, 0), (3, 1), (3, 2)}
    print(f"\nSALIENCE 2-D end-to-end: {len(sal)} cells; "
          f"top residual {top['residual_salience']:.3f} at "
          f"({top['column_index']},{top['row_index']})")
    assert (top["column_index"], top["row_index"]) in mover, (
        "the most-salient 2-D cell must be the vertical mover")
    assert top["residual_salience"] > 1.0
    eye.stop()


# ===========================================================================
# 5. DEFAULT OFF / byte-identity of the 2-D-carve path
# ===========================================================================

def test_2d_motion_salience_are_off_by_default_and_carve_path_unchanged():
    # 2-D build WITHOUT the motion/salience flags: no params, settle no-ops.
    eye = _eye2d()
    assert eye._motion_enabled is False and eye._salience_enabled is False
    assert eye.substrate.nodes("RetinaMotionParams2d") == []
    assert eye.substrate.nodes("RetinaSalienceParams2d") == []
    assert eye.settle_motion_2d() is None
    assert eye.settle_salience_2d() is None

    # the 2-D CARVE path still separates same-az/diff-el into 2 polygons.
    rng = np.random.default_rng(SEED)
    for _ in range(WARMUP):
        _frame2d(eye, [])
    lo = eye._epoch + 1
    for col in range(4, 10):
        _frame2d(eye, [_bright(col, r, rng) for r in (2, 3, 8, 9)])
    eye.settle_carve_2d(since_epoch=lo)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    polys = eye.carve_polygons_2d()
    print(f"\n2-D CARVE PATH UNCHANGED: {len(polys)} polygons")
    assert len(polys) == 2, f"2-D carve path must be unchanged, got {len(polys)}"
    eye.stop()


def test_1d_motion_and_salience_paths_are_unchanged():
    """The 1-D motion/salience kinds are byte-untouched; a horizontal mover is
    still read by the 1-D pipeline exactly as before."""
    rng = np.random.default_rng(SEED)
    eye = GraphEye(n_az=16, context={
        "synchronous": True, "worker_capacity": 1,
        "visual_motion": True, "visual_salience": True}).build()
    assert eye._retina_2d is False
    for _ in range(WARMUP):
        eye.submit_photons([]); eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
    lo = eye._epoch + 1
    for c in range(0, 8):
        eye.submit_photons([{"column": int(c), "wavelength_nm": 500.0,
                             "count": int(rng.poisson(BRIGHT))}])
        eye.substrate._inner.run_cognitive_tasks(1)
        eye.substrate._inner.run_rules()
    eye.settle_motion(since_epoch=lo)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    mp = eye.motion_percepts()
    print(f"\n1-D MOTION UNCHANGED: {[(round(p['direction'],2), round(p['speed'],2)) for p in mp]}")
    assert len(mp) == 1 and mp[0]["direction"] == 1.0 and mp[0]["speed"] > 0.5
    eye.stop()


# ===========================================================================
# 6. merge-block source audit
# ===========================================================================

def test_2d_motion_salience_are_derived_from_the_event_stream_not_a_raster():
    for meth in (GraphEye.settle_motion_2d, GraphEye.settle_salience_2d):
        src = inspect.getsource(meth)
        assert "RetinalOnsetEvent" in src
        assert "column_index" in src and "row_index" in src and "epoch" in src
        for forbidden in ("retinal_field", "vector_field", "retinal_flow_depth",
                          "_previous_field", "PhotonExposure",
                          "native.segment", "segment_motion", "segment_and_track"):
            assert forbidden not in src, (
                f"{meth.__name__} must not touch {forbidden}")


# ===========================================================================
# 7. §10 provenance
# ===========================================================================

def test_engine_is_a_build_of_this_trees_rust():
    prov = engine_provenance()
    assert prov["source_match"] in ("own", "shared"), prov
