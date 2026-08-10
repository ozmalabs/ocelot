"""GATE — THE PER-AREA DIRTY-INDEX: per-tick cost O(SURPRISE), not O(cells)
(block 185000).

Pins the four things the rung claims, on the COMMITTED real `defend_the_line`
fixture (`tests/fixtures/doom_carve_scale/`, VizDoom-free) through the SAME
measure core the headline numbers come from (`scripts/dirty_index_measure.py`):

  A. BRANCH A is BYTE-IDENTICAL — dirty-index ON ≡ 184000 full-sweep accel ≡ the
     graph/`run_rules` path, on polygons, the onset stream and the FULL per-cell
     rod state (adaptation / activation / prev_activation / caught_quanta /
     input_epoch) — and the WRONG (naive "skip quiet cells") predicate BREAKS it,
     so the check is provably non-vacuous.
  B. The EXACT predicate fires exactly where the float arithmetic says it must:
     never before the EMA reaches its float64 fixed point (t* ≈ 71 at
     adapt_rate 0.4), and for the whole sheet shortly after.
  C. Cost tracks the DIRTY COUNT, not the total cell count — asserted at the
     MECHANISM grain (how many cells are actually processed) and, loosely, in
     wall time.
  D. NO FREE LUNCH: when every cell genuinely changes, nothing is skipped.
  E. BRANCH B (bounded shedding) is OFF BY DEFAULT and is never claimed
     byte-identical — its divergence is real, measured, and bounded.
"""
import os
import sys
import time

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

FIX = os.path.join(ROOT, "tests", "fixtures", "doom_carve_scale",
                   "frames_160x120.npz")
pytestmark = pytest.mark.skipif(
    not os.path.exists(FIX), reason="committed doom_carve_scale fixture absent")

D = pytest.importorskip("scripts.dirty_index_measure")
dpw = pytest.importorskip("domains.doom_photon_world")


@pytest.fixture(scope="module")
def lumas():
    lum, _lab, _names = D.EA._load_fixture()
    return list(lum)


# ----------------------------------------------------------------- A ----------
def test_exact_dirty_index_is_byte_identical_to_full_sweep_and_graph(lumas):
    """dirty-ON ≡ 184000 accel ≡ graph path — polygons, onsets, ALL rod state."""
    n_el, n_az = 15, 20
    on = D.hold_carve_run(lumas[:5], None, None, n_el, n_az, arm="dirty")
    off = D.hold_carve_run(lumas[:5], None, None, n_el, n_az, arm="accel")
    gr = D.hold_carve_run(lumas[:5], None, None, n_el, n_az, arm="graph")

    assert D.poly_key(on["polygons"]) == D.poly_key(off["polygons"])
    assert D.poly_key(on["polygons"]) == D.poly_key(gr["polygons"])
    assert on["onset_stream"] == off["onset_stream"] == gr["onset_stream"]
    for key in ("adaptation", "activation", "prev_activation", "caught_quanta",
                "input_epoch"):
        assert on["rod"][key] == off["rod"][key], f"{key} differs vs full sweep"
        assert on["rod"][key] == gr["rod"][key], f"{key} differs vs graph path"
    # NON-VACUOUS: the identity must not be bought by never skipping anything.
    assert on["skipped"][-1] >= 0.9 * n_el * n_az
    assert sum(on["skipped"]) > 0


def test_byte_identity_holds_on_a_FIRING_carve(lumas):
    """The same identity where the eye actually carves something: 80x60, real
    motion, polygons + a firing onset stream (the 20x15 gate above is cheap but
    thin)."""
    n_el, n_az = 60, 80
    on = D.hold_carve_run(lumas, None, None, n_el, n_az, arm="dirty")
    off = D.hold_carve_run(lumas, None, None, n_el, n_az, arm="accel")
    assert len(on["onset_stream"]) > 10, "vacuous: nothing fired"
    assert len(on["polygons"]) > 0, "vacuous: nothing carved"
    assert D.poly_key(on["polygons"]) == D.poly_key(off["polygons"])
    assert on["onset_stream"] == off["onset_stream"]
    for key in ("adaptation", "activation", "prev_activation", "caught_quanta",
                "input_epoch"):
        assert on["rod"][key] == off["rod"][key], key
    assert on["skipped"][-1] >= 0.9 * n_el * n_az


def test_naive_skip_predicate_breaks_the_identity(lumas):
    """The naive 'skip quiet cells' design — skipping on input-unchanged ALONE,
    ignoring the still-moving EMA floor — MUST diverge. This is the bug the
    exact predicate exists to prevent; if it did not break, the gate above would
    be vacuous."""
    n_el, n_az = 15, 20
    off = D.hold_carve_run(lumas[:5], None, None, n_el, n_az, arm="accel")
    naive = D.hold_carve_run(lumas[:5], None, None, n_el, n_az, arm="dirty",
                             naive=True)
    assert naive["rod"]["adaptation"] != off["rod"]["adaptation"]
    assert not D.state_equal(naive, off)
    # ... and it skips MORE than the exact predicate does (it is skipping work
    # that was not a no-op).
    exact = D.hold_carve_run(lumas[:5], None, None, n_el, n_az, arm="dirty")
    assert sum(naive["skipped"]) > sum(exact["skipped"])


# ----------------------------------------------------------------- B ----------
def test_exact_predicate_fires_only_at_the_float_fixed_point(lumas):
    """The EMA reaches an EXACT float64 fixed point after t* ≈ 71 ticks of
    bit-repeatable input at adapt_rate 0.4 — not before, and then for the whole
    sheet. Nothing may be skipped while the floor is still moving."""
    n_el, n_az = 15, 20
    g = D._grid(lumas[0], n_el, n_az)
    eye = D.build_eye(n_el, n_az, dirty=True)
    sensor = D.Sensor(0)
    frac = []
    for _ in range(95):
        sensor.submit(eye, g)
        frac.append(eye._skip_log[-1] / float(n_el * n_az))
    eye.stop()
    assert max(frac[:64]) == 0.0, "skipped a cell before the EMA settled"
    assert frac[89] > 0.99, "the settled sheet is not being skipped"


def test_poisson_shot_noise_admits_no_exact_skip(lumas):
    """A photon-COUNTING sensor's input is never bit-identical, so the exact
    predicate correctly never fires under shot noise — the honest boundary of
    Branch A, pinned so a later change cannot silently start skipping."""
    n_el, n_az = 15, 20
    g = D._grid(lumas[0], n_el, n_az)
    eye = D.build_eye(n_el, n_az, dirty=True)
    sensor = D.Sensor(0)
    rng = np.random.default_rng(D.SEED)
    for _ in range(90):
        sensor.submit(eye, g, rng)
    assert max(eye._skip_log) == 0
    eye.stop()


# ----------------------------------------------------------------- C ----------
def test_cost_tracks_dirty_count_not_total_cells(lumas):
    """Per-tick work is O(dirty), not O(cells): at the MECHANISM grain the sheet
    processes exactly the reported cells, and in wall time a 16-cell tick is a
    small fraction of a whole-sheet tick — at BOTH resolutions."""
    per_res = {}
    for (n_az, n_el) in ((20, 15), (40, 30)):
        g = D._grid(lumas[0], n_el, n_az)
        eye, sensor, _t, _s = D.settled_eye(n_el, n_az, g, stamp=False)
        n = n_az * n_el
        c16 = D.cost_at_worklist(eye, sensor, g, 16)
        # MECHANISM GRAIN: exactly n-16 cells were skipped on that tick.
        assert eye._skip_log[-1] == n - 16
        cfull = D.cost_at_worklist(eye, sensor, g, n)
        assert eye._skip_log[-1] == 0
        per_res[n] = (c16, cfull)
        eye.stop()
        assert c16 < 0.5 * cfull, (n, c16, cfull)
    # ≈FLAT in total cells at a FIXED dirty count: 4x the cells must NOT cost 4x.
    c16_small = per_res[300][0]
    c16_big = per_res[1200][0]
    assert c16_big < 2.5 * c16_small, (c16_small, c16_big)


# ----------------------------------------------------------------- D ----------
def test_full_field_change_gets_no_free_lunch(lumas):
    """The FALSIFIER. When everything genuinely changes every tick the index must
    skip NOTHING and cost about what the full sweep costs — otherwise it is
    wrongly skipping work."""
    n_el, n_az = 30, 40
    rng = np.random.default_rng(D.SEED + 1)
    frames = [rng.uniform(0, 255, size=(n_el, n_az)) for _ in range(8)]
    eye = D.build_eye(n_el, n_az, dirty=True)
    sensor = D.Sensor(0)
    t_dirty = []
    n = n_el * n_az
    for f in frames:
        dt, k = sensor.submit(eye, f)
        t_dirty.append(dt)
        # every cell reported changed (bar the handful whose rounded photon
        # count coincides between two independent uniform draws)
        assert k >= 0.99 * n, k
    assert max(eye._skip_log) <= 0.01 * n   # ... and essentially nothing skipped
    eye.stop()

    eye2 = D.build_eye(n_el, n_az, dirty=False)
    s2 = D.Sensor(0)
    t_full = [s2.submit_full(eye2, f)[0] for f in frames]
    eye2.stop()
    ratio = float(np.median(t_dirty[2:])) / float(np.median(t_full[2:]))
    assert ratio > 0.6, f"dirty-index is suspiciously fast on full-field change: {ratio}"


# ----------------------------------------------------------------- E ----------
def test_branch_b_shedding_is_off_by_default_and_never_claims_identity(lumas):
    """BRANCH B is a SEMANTIC OPTION: OFF by default, and when switched on its
    divergence is REAL (never byte-identity) and bounded by the shed threshold's
    own scale."""
    n_el, n_az = 15, 20
    probe = D.build_eye(n_el, n_az)
    assert probe._dirty_index is False
    assert probe._dirty_shed is False
    assert probe._dirty_naive is False
    probe.stop()

    exact = D.poisson_carve_run(lumas[:5], None, None, n_el, n_az, arm="dirty")
    shed = D.poisson_carve_run(lumas[:5], None, None, n_el, n_az, arm="dirty",
                               delta=8, shed=True)
    a0 = np.array([float(x) for x in exact["rod"]["adaptation"]])
    a1 = np.array([float(x) for x in shed["rod"]["adaptation"]])
    dev = np.abs(a1 - a0)
    # It DOES shed work ...
    assert sum(shed["skipped"]) > sum(exact["skipped"])
    # ... and it DOES diverge — this is declared, not hidden.
    assert dev.max() > 0.0
    # ... within the shed threshold's own scale (a dead-band, not a drift).
    assert dev.max() < 200.0, dev.max()
