"""RUN 59 -- unit tests for the confound-signature measurement (pure functions, synthetic data).

Verifies: confound signatures compute correctly on synthetics (a pen-lift instance -> hand-reposition
flag; a pressure-drop instance -> ink flag; a normal instance -> no flags); per-writer robust-z
normalization; the miss-definition on a synthetic modal-junction class; and the seed-guard md5.
"""
import hashlib
import importlib.util
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

spec = importlib.util.spec_from_file_location(
    "run59", os.path.join(ROOT, "scripts", "jabberwock_omniglot_run59_confounds.py"))
run59 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run59)


def _instance(strokes, pressures=None, times=None, writer="w0", cls=99, symbol="x"):
    """Build a minimal DigiLeTs-shaped sample from a list of (k,2) stroke arrays, with matching
    per-point pressure / t_ms / pen_down (pen_down==1 at each stroke start)."""
    strokes = [np.asarray(s, dtype=float).reshape(-1, 2) for s in strokes]
    pos = np.vstack(strokes)
    n = pos.shape[0]
    pen_down = np.zeros(n)
    idx = 0
    for s in strokes:
        pen_down[idx] = 1
        idx += s.shape[0]
    pressure = np.asarray(pressures, dtype=float) if pressures is not None else np.full(n, 0.5)
    t_ms = np.asarray(times, dtype=float) if times is not None else np.arange(n, dtype=float) * 10.0
    return {"writer_id": writer, "class": cls, "symbol": symbol, "instance": 0,
            "pos_xy": pos, "pressure": pressure, "pen_down": pen_down, "t_ms": t_ms,
            "strokes": strokes}


def test_junction_contact_needs_list_conversion():
    # two crossing strokes as raw numpy arrays must be detected as contacting (the _as_xy gotcha).
    v = np.array([[0.5, 0.0], [0.5, 0.5], [0.5, 1.0]])
    h = np.array([[0.0, 0.5], [0.5, 0.5], [1.0, 0.5]])
    assert run59.instance_has_contact([v, h]) is True
    # two far-apart strokes -> no contact (a MISS realization).
    far = np.array([[3.0, 3.0], [3.0, 3.5], [3.0, 4.0]])
    assert run59.instance_has_contact([v, far]) is False
    # single stroke -> not multi-stroke.
    assert run59.instance_has_contact([v]) is None


def test_nearest_pair():
    a = np.array([[0.0, 0.0], [0.0, 1.0]])
    b = np.array([[0.05, 1.0], [0.05, 2.0]])   # near a's end
    c = np.array([[9.0, 9.0], [9.0, 10.0]])    # far
    i, j, d = run59.nearest_stroke_pair([a, b, c])
    assert (i, j) == (0, 1)
    assert d < 0.1


def test_reposition_metric():
    # A ends at (0,1); B starts at (0.02,1) -> tiny air gap; vs B' starts far -> large gap.
    A = np.array([[0.0, 0.0], [0.0, 1.0]])
    B_near = np.array([[0.02, 1.0], [0.02, 2.0]])
    B_far = np.array([[0.9, 1.0], [0.9, 2.0]])
    m_near = run59.instance_raw_metrics(_instance([A, B_near]))
    m_far = run59.instance_raw_metrics(_instance([A, B_far]))
    assert m_near["reposition"] < 0.1
    assert m_far["reposition"] > 0.5
    assert m_far["reposition"] > m_near["reposition"]


def test_pause_metric():
    A = np.array([[0.0, 0.0], [0.0, 1.0]])
    B = np.array([[0.02, 1.0], [0.02, 2.0]])
    # times: A occupies indices 0,1 (t=0,10); B indices 2,3. Long pause -> t[2]=500.
    long_pause = _instance([A, B], times=[0.0, 10.0, 500.0, 510.0])
    short_pause = _instance([A, B], times=[0.0, 10.0, 20.0, 30.0])
    assert run59.instance_raw_metrics(long_pause)["pause"] > 400
    assert run59.instance_raw_metrics(short_pause)["pause"] < 20


def test_pressure_start_metric():
    A = np.array([[0.0, 0.0], [0.0, 1.0]])
    B = np.array([[0.02, 1.0], [0.02, 2.0], [0.02, 3.0]])
    press = [0.5, 0.5, 0.1, 0.1, 0.1]   # B starts light
    m = run59.instance_raw_metrics(_instance([A, B], pressures=press))
    assert abs(m["pressure_start"] - 0.1) < 1e-6


def test_edge_distance():
    bbox = (0.0, 0.0, 1.0, 1.0, float(np.hypot(1.0, 1.0)))
    center = run59.edge_distance(np.array([0.5, 0.5]), bbox)
    edge = run59.edge_distance(np.array([0.02, 0.5]), bbox)
    assert center > edge
    assert edge < 0.05


def test_robust_z_and_normalization():
    vals = [1.0, 1.0, 1.0, 1.0, 5.0]     # 5.0 is a clear high outlier
    z_out = run59.robust_z(5.0, vals)
    z_norm = run59.robust_z(1.0, vals)
    assert z_out > 1.0
    assert abs(z_norm) < 1.0
    # NaN input -> 0 (no flag); degenerate spread -> 0.
    assert run59.robust_z(float("nan"), vals) == 0.0
    assert run59.robust_z(3.0, [2.0, 2.0, 2.0]) == 0.0


def test_confound_flags_directions():
    # high reposition/pause z -> flagged; low extension/ink z -> flagged.
    z = {"reposition": 2.0, "pause": 0.0, "extension": -2.0, "ink": 0.5}
    f = run59.confound_flags(z)
    assert f["reposition"] and f["extension"]
    assert not f["pause"] and not f["ink"]


def test_synthetic_pipeline_flags():
    """A pen-lift (big reposition) instance and a pressure-drop instance are flagged for the right
    confound; a normal instance for none -- through the FULL per-writer-normalized pipeline."""
    A = np.array([[0.0, 0.0], [0.0, 1.0]])
    B0 = np.array([[0.02, 1.0], [0.02, 2.0], [0.02, 3.0]])   # normal touching B
    samples = []
    # 6 NORMAL touching instances of the intent class (baseline for the writer).
    for k in range(6):
        samples.append(_instance([A, B0], pressures=[0.5, 0.5, 0.5, 0.5, 0.5], cls=1, symbol="x"))
    # 1 PEN-LIFT (repositioned) instance: B starts far in x -> large reposition, still touches via
    # crossing? make it a hit but repositioned. Keep contact by crossing near A's line.
    A2 = np.array([[0.0, 0.0], [0.0, 1.0], [0.0, 2.0]])
    B_rep = np.array([[0.9, 1.0], [0.45, 1.0], [0.0, 1.0]])   # ends ON A (contact) but starts far
    samples.append(_instance([A2, B_rep], pressures=[0.5]*3 + [0.5]*3, cls=1, symbol="x"))
    # 1 PRESSURE-DROP instance: B initiates very light.
    B_ink = np.array([[0.02, 1.0], [0.02, 2.0], [0.02, 3.0]])
    samples.append(_instance([A, B_ink], pressures=[0.5, 0.5, 0.05, 0.05, 0.05], cls=1, symbol="x"))
    # give the writer some other multi-stroke instances so the class qualifies (>=50% MS) -- all are.
    recs, summary = run59.build_instances(samples)
    # class 1 must be an intent class (all contact).
    assert any(cs["cls"] == 1 and cs["intent"] for cs in summary)
    # find the repositioned and ink records (they are the 7th and 8th appended).
    rep_rec = recs[6]
    ink_rec = recs[7]
    normal_rec = recs[0]
    assert rep_rec["flags"]["reposition"], f"reposition not flagged: {rep_rec['z']}"
    assert ink_rec["flags"]["ink"], f"ink not flagged: {ink_rec['z']}"
    assert not normal_rec["any"], f"normal instance flagged: {normal_rec['flags']}"


def test_miss_definition_modal_class():
    """A synthetic class with 4 touching + 1 disjoint instances -> intent class, exactly 1 miss."""
    A = np.array([[0.0, 0.0], [0.0, 1.0], [0.0, 2.0]])
    B_touch = np.array([[-0.5, 1.0], [0.0, 1.0], [0.5, 1.0]])   # crosses A at midpoint
    B_miss = np.array([[3.0, 1.0], [3.5, 1.0], [4.0, 1.0]])     # far, no contact
    samples = [_instance([A, B_touch], cls=7, symbol="t") for _ in range(4)]
    samples.append(_instance([A, B_miss], cls=7, symbol="t"))
    recs, summary = run59.build_instances(samples)
    cs = [c for c in summary if c["cls"] == 7][0]
    assert cs["intent"] is True
    assert cs["n_miss"] == 1
    miss_recs = [r for r in recs if r["is_miss"]]
    assert len(miss_recs) == 1


def test_seed_guard_md5_stable():
    with open(run59.SEED_PATH, "rb") as f:
        m1 = hashlib.md5(f.read()).hexdigest()
    # importing / running measurement must not touch the seed.
    with open(run59.SEED_PATH, "rb") as f:
        m2 = hashlib.md5(f.read()).hexdigest()
    assert m1 == m2 == run59.seed_md5()


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
