"""PER-AREA RESIDUAL SALIENCE ON THE EVENT STREAM — the gate
(`VISION_RESIDUAL_SALIENCE_EVENT_PREREG.md`, block 164000).

Rung 4 of the photon-eye migration. Salience is computed EVENT-NATIVELY as the
RESIDUAL of the async onset-event stream (`RetinalOnsetEvent`, Rung 1) AFTER the
coherent structure is explained: the salient column is the SURPRISING one, whose
onset motion is NOT accounted for by the DOMINANT common-fate motion. This
re-expresses the RGB residual-salience result (157000: the residual after
egomotion cancellation ranks the independent mover ABOVE the egomotion-swung
background, where RAW salience fails) onto the EVENT STREAM — egomotion ⟷ the
dominant common-fate velocity `v_dom`; a column's cancelled residual ⟷
`|v_run − v_dom|`. It reads the SAME async event stream Rung 2/3 read
(`RetinalOnsetEvent` column + own epoch), NOT the coarse `retinal_field` raster
and NOT the raster `shape_salience` / `order_n_shape_salience`.

HONEST SCOPE: the photon eye is a 1-D AZIMUTH STRIP, so this is a per-column
salience field over that strip (a per-AREA salience). A true 2-D salience map
needs the retina extended to elevation columns — a named follow-on.

What this guards:
  1. THE PRIMITIVE, called directly (CognitiveTask round-trip): a fast coherent
     background + a slow independent mover → RESIDUAL ranks the mover TOP-1
     (mover-vs-bg AUC = 1.0) where RAW (own-speed) ranks the fast background
     ABOVE the mover (AUC = 0.0). The headline inversion, event-native.
  2. SILENCE: a fully-coherent field → residual ~0 everywhere (max residual
     salience below a floor) — the compute-∝-surprise silence; RAW is NOT silent.
  3. NO-DOMINANT-MOTION identity: no coherent run (`v_dom = 0`) → residual == raw.
  4. THROUGH THE REAL MINT RULE: a coherent background + an opposite mover →
     `RetinalSalience` nodes minted, the mover column TOP-1 by residual salience,
     residual AUC(mover>bg) = 1.0 while RAW AUC ≤ 0.6.
  5. STATIC (dark) → no onset events → NO `RetinalSalience` node.
  6. DEFAULT OFF: flag off ⇒ no salience params, no salience task, no node, plain
     kind; existing paths byte-identical.
  7. MERGE-BLOCK SOURCE AUDIT: `settle_salience` reads ONLY the event stream
     (`RetinalOnsetEvent` attrs), never the raster / a frame diff / raster salience.
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

SEED = 164000
BRIGHT = 2000
WARMUP = 8            # dark frames so each column's floor adapts before the sweep
STRIDE = 3           # the kernel's per-column output block: [fired, raw, residual]


def _auc(fg, bg):
    """Mann–Whitney AUC: P(fg_score > bg_score), ties counted as 0.5. 1.0 means
    every foreground score outranks every background score; 0.0 the reverse."""
    fg = list(fg); bg = list(bg)
    if not fg or not bg:
        return None
    wins = 0.0
    for a in fg:
        for b in bg:
            wins += 1.0 if a > b else (0.5 if a == b else 0.0)
    return wins / (len(fg) * len(bg))


# --- 1. the Rust DECISION primitive, called directly ----------------------

def _run_kernel(s, payload):
    t = s.add_node("CognitiveTask", {
        "status": "requested", "kind": "retinal_residual_salience",
        "payload": [float(v) for v in payload],
        "input_epoch": 1, "logical_time": 0, "area": "global"})
    s._inner.run_cognitive_tasks(1)
    return list(s.node(t)["attrs"]["output"])


def _pack(n_az, events, max_gap=1.0, vel_tol=0.35):
    """Serialise (column, epoch) events into the salience kernel payload."""
    payload = [float(n_az), float(max_gap), float(vel_tol), float(len(events))]
    for c, e in events:
        payload.extend([float(c), float(e)])
    return payload


def _fired(out, n_az):
    return [c for c in range(n_az) if out[c * STRIDE] == 1.0]


def test_kernel_residual_isolates_mover_where_raw_ranks_the_fast_background():
    """HEADLINE (kernel). A fast coherent background (cols 0..9, v=3) + a slow
    independent mover (cols 12..14, v=−1). RESIDUAL (departure from the dominant
    v_dom=3) ranks the mover TOP-1; RAW (own speed) ranks the fast background
    ABOVE the mover. Able to fail: a broken cancellation would not invert them."""
    s = srs.Substrate()
    n_az = 16
    bg = [(c, c / 3.0) for c in range(0, 10)]       # v = 3 (fast sweep)
    mover = [(c, 100.0 - c) for c in range(12, 15)]  # v = −1 (slow, opposite)
    out = _run_kernel(s, _pack(n_az, bg + mover))

    bg_cols = list(range(0, 10)); mv_cols = list(range(12, 15))
    raw = {c: out[c * STRIDE + 1] for c in _fired(out, n_az)}
    res = {c: out[c * STRIDE + 2] for c in _fired(out, n_az)}
    # dominant motion is the background → its residual is ~0, raw = own speed 3
    assert all(res[c] < 1e-9 for c in bg_cols), res
    assert all(abs(raw[c] - 3.0) < 1e-9 for c in bg_cols), raw
    # the mover departs from v_dom → residual = |−1 − 3| = 4; raw = own speed 1
    assert all(abs(res[c] - 4.0) < 1e-9 for c in mv_cols), res
    assert all(abs(raw[c] - 1.0) < 1e-9 for c in mv_cols), raw

    auc_res = _auc([res[c] for c in mv_cols], [res[c] for c in bg_cols])
    auc_raw = _auc([raw[c] for c in mv_cols], [raw[c] for c in bg_cols])
    order = sorted(res, key=lambda c: -res[c])
    mover_rank = min(order.index(c) for c in mv_cols) + 1
    print(f"\nSALIENCE KERNEL: residual AUC(mover>bg)={auc_res} "
          f"raw AUC(mover>bg)={auc_raw} mover_rank_residual={mover_rank}")
    # THE PRE-REGISTERED HEADLINE + interval
    assert 0.95 <= auc_res <= 1.0, auc_res            # residual isolates the mover
    assert auc_raw <= 0.6, auc_raw                    # raw FAILS (fast bg on top)
    assert mover_rank == 1, mover_rank                # mover top-1 by residual


def test_kernel_is_silent_on_a_fully_coherent_field():
    """SILENCE control. One diagonal covering the whole strip → every column
    shares v_dom → every residual ~0 (the compute-∝-surprise silence). RAW is
    NOT silent (it reports the coherent sweep's speed)."""
    s = srs.Substrate()
    n_az = 12
    coherent = [(c, float(c)) for c in range(n_az)]   # epoch = column → v=1 all
    out = _run_kernel(s, _pack(n_az, coherent))
    fired = _fired(out, n_az)
    max_res = max(out[c * STRIDE + 2] for c in fired)
    max_raw = max(out[c * STRIDE + 1] for c in fired)
    print(f"\nSALIENCE SILENCE: max_residual={max_res} max_raw={max_raw}")
    assert max_res < 1e-9, "a fully coherent field is silent (residual ~0)"
    assert max_raw > 0.5, "but RAW reports the coherent sweep's speed everywhere"


def test_kernel_no_dominant_motion_makes_residual_equal_raw():
    """NO-DOMINANT identity control. A field with no coherent run (isolated
    single-column flashes, spatially non-contiguous) → v_dom=0 → residual == raw
    for every firing column (nothing to cancel; 157000's no-egomotion control)."""
    s = srs.Substrate()
    n_az = 16
    # isolated flashes 3 columns apart — every run is a singleton (v_run=0).
    flashes = [(0, 5.0), (4, 9.0), (8, 2.0), (12, 7.0)]
    out = _run_kernel(s, _pack(n_az, flashes))
    for c in _fired(out, n_az):
        assert abs(out[c * STRIDE + 1] - out[c * STRIDE + 2]) < 1e-9, (
            f"v_dom=0 ⇒ residual == raw at column {c}")


def test_kernel_static_empty_stream_produces_no_salience():
    s = srs.Substrate()
    n_az = 8
    out = _run_kernel(s, _pack(n_az, []))
    assert _fired(out, n_az) == [], "no events ⇒ no fired column"
    assert all(v == 0.0 for v in out), "an empty event stream is all-zero"


# --- the synchronous world harness ----------------------------------------

def _eye(n_az=16, salience=True):
    ctx = {"synchronous": True, "worker_capacity": 1}
    if salience:
        ctx["visual_salience"] = True
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
    eye.settle_salience(since_epoch=since_epoch)
    eye.substrate._inner.run_cognitive_tasks(1)
    eye.substrate._inner.run_rules()
    return eye.salience_percepts()


# --- 4. through the REAL mint rule (the headline, embodied) ----------------

def test_residual_salience_minted_ranks_mover_above_background():
    """A coherent background sweep (cols 0..9, L→R, v=+1, the dominant motion) +
    an independent mover (cols 15..13, R→L, v=−1) driven through the REAL mint
    rule. The `RetinalSalience` nodes carry residual salience; the mover column
    is TOP-1 by residual, residual AUC(mover>bg)=1.0, while RAW (equal own-speed)
    does NOT separate (AUC ≤ 0.6)."""
    rng = np.random.default_rng(SEED)
    n_az = 16
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    _sweep(eye, list(range(0, 10)), rng)          # background: cols 0..9 L→R
    _sweep(eye, [15, 14, 13], rng)                # mover: cols 15..13 R→L
    sal = _settle_and_mint(eye, since_epoch=lo)
    by_col = {s["column_index"]: s for s in sal}
    print(f"\nSALIENCE EYE: "
          f"{[(s['column_index'], round(s['raw_salience'],2), round(s['residual_salience'],2)) for s in sal]}")
    bg_cols = [c for c in range(0, 10) if c in by_col]
    mv_cols = [c for c in (13, 14, 15) if c in by_col]
    assert len(bg_cols) >= 6 and len(mv_cols) >= 2, (bg_cols, mv_cols)
    res = {c: by_col[c]["residual_salience"] for c in by_col}
    raw = {c: by_col[c]["raw_salience"] for c in by_col}
    auc_res = _auc([res[c] for c in mv_cols], [res[c] for c in bg_cols])
    auc_raw = _auc([raw[c] for c in mv_cols], [raw[c] for c in bg_cols])
    order = sorted(res, key=lambda c: -res[c])
    mover_rank = min(order.index(c) for c in mv_cols) + 1
    print(f"  residual AUC(mover>bg)={auc_res} raw AUC={auc_raw} "
          f"mover_rank={mover_rank}")
    assert 0.95 <= auc_res <= 1.0, (auc_res, res)     # residual isolates mover
    assert auc_raw <= 0.6, (auc_raw, raw)             # raw does not separate
    assert mover_rank == 1, (mover_rank, res)         # mover top-1 by residual
    # the background IS the dominant motion → its residual is ~0
    assert all(res[c] < 1e-6 for c in bg_cols), res
    eye.stop()


# --- 5. static (dark) → no events → no salience node -----------------------

def test_static_dark_field_mints_no_salience():
    n_az = 16
    eye = _eye(n_az=n_az)
    for _ in range(WARMUP):
        _frame(eye, [])
    lo = eye._epoch + 1
    for _ in range(8):
        _frame(eye, [])                            # dark: no onset events
    sal = _settle_and_mint(eye, since_epoch=lo)
    print(f"\nSALIENCE static: nodes={len(sal)}")
    assert sal == [], f"a dark scene mints no salience, got {sal}"
    eye.stop()


# --- 6. default OFF / byte-identity ----------------------------------------

def test_salience_path_is_off_by_default():
    eye = _eye(n_az=8, salience=False)
    assert eye._salience_enabled is False
    assert eye._onset_kind == "photon_transduce", "flag off ⇒ plain kind"
    assert eye.substrate.nodes("RetinaSalienceParams") == [], "no params node when off"
    assert eye.settle_salience() is None, "settle_salience is a no-op when off"
    rng = np.random.default_rng(SEED)
    for c in range(8):
        _frame(eye, _bright([c], rng))
    assert eye.substrate.nodes("RetinalSalience") == [], (
        "no salience node may be minted with the salience path off")
    assert eye.salience_percepts() == []
    eye.stop()


# --- 7. merge-block source audit: salience reads ONLY the event stream ------

def test_salience_is_derived_from_the_event_stream_not_a_raster_or_frame_diff():
    src = inspect.getsource(GraphEye.settle_salience)
    assert "RetinalOnsetEvent" in src, "salience must read the onset EVENT STREAM"
    assert "column_index" in src and "epoch" in src, (
        "salience reads each event's column + own epoch")
    for forbidden in ("retinal_field", "vector_field", "retinal_flow_depth",
                      "_previous_field", "PhotonExposure",
                      "native.segment", "segment_motion", "segment_and_track",
                      "shape_salience", "order_n_shape_salience"):
        assert forbidden not in src, (
            f"MERGE-BLOCK: settle_salience must not touch {forbidden!r} — the "
            "salience is the residual of the async event stream, never a raster / "
            "frame diff / raster shape_salience")


# --- 8. provenance ---------------------------------------------------------

def test_engine_is_a_build_of_this_tree():
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), (
        f"engine source verdict {p['source_match']!r} — see "
        "test_engine_provenance_migrated.py")
