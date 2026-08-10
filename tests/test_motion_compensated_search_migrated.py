"""GATE — motion-compensated (predictive-center) block search (block 148000-148999).

Every order-N verdict is read FROM THE GRAPH (the minted LatentDimension coeffs),
and every assertion is able to fail. The claim: MC-search recovers a free-fall's
acceleration where the FIXED-aperture sensor floors, by decoupling the aperture
from the velocity — and it is DEFAULT OFF / byte-identical when disengaged.

Success is judged by the COEFFICIENT (nonzero, ∝-correct acceleration read from
the graph), NOT the status flip (block 147000's lesson).
"""
import os
import sys

import numpy as np
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from domains.motion_group_world import vector_field                       # noqa: E402
import scripts.motion_compensated_measure as M                           # noqa: E402


# ── shared, deterministic H1 + controls, computed once ────────────────────────

@pytest.fixture(scope="module")
def h1():
    return M.part_h1()


@pytest.fixture(scope="module")
def controls():
    return M.part_controls()


# ── §9 DEFAULT-OFF / BYTE-IDENTITY ────────────────────────────────────────────

def test_predict_none_is_byte_identical_to_plain():
    """DEFAULT OFF: predict=None runs only the plain search — byte-identical."""
    rng = np.random.default_rng(148000)
    block = 4
    total = mism = 0
    for _ in range(6):
        a = rng.integers(0, 4, (80, 48)).astype(float)
        b = rng.integers(0, 4, (80, 48)).astype(float)
        v_plain = vector_field(a, b, block)
        v_none = vector_field(a, b, block, predict=None)
        mism += int(np.sum(v_plain != v_none))
        total += v_plain.size
    assert total > 0
    assert mism == 0, f"predict=None diverged from plain in {mism}/{total} components"


def test_predict_zero_is_byte_identical_to_plain():
    """A ZERO prediction adds a predicted pass whose candidates coincide with the
    plain candidates and can never strictly beat them -> byte-identical output."""
    rng = np.random.default_rng(148001)
    block = 4
    total = mism = 0
    for _ in range(6):
        a = rng.integers(0, 4, (80, 48)).astype(float)
        b = rng.integers(0, 4, (80, 48)).astype(float)
        nh, nw = (80 // block), (48 // block)
        v_plain = vector_field(a, b, block)
        v_zero = vector_field(a, b, block, predict=np.zeros((nh, nw, 2)))
        mism += int(np.sum(v_plain != v_zero))
        total += v_plain.size
    assert mism == 0, f"predict=0 diverged from plain in {mism}/{total} components"


def test_byte_identity_gate_can_fail():
    """POSITIVE CONTROL on the guard: a genuinely NON-zero prediction on a fast
    shift DOES change the output — so the byte-identity assertion is not vacuous."""
    a = np.zeros((60, 40)); a[10:40, 10:30] = np.arange(30 * 20).reshape(30, 20) % 4
    shift = 11
    b = np.zeros_like(a); b[shift:, :] = a[:-shift, :]
    block = 4
    nh, nw = 60 // block, 40 // block
    v_plain = vector_field(a, b, block)
    pred = np.zeros((nh, nw, 2)); pred[:, :, 0] = shift
    v_mc = vector_field(a, b, block, predict=pred)
    assert int(np.sum(v_plain != v_mc)) > 0


def test_first_frame_fallback_is_plain():
    """First frame pair has no prior field -> the carve passes predict=None ->
    byte-identical to the plain sensor on that pair."""
    rng = np.random.default_rng(148002)
    a = rng.integers(0, 4, (60, 40)).astype(float)
    b = rng.integers(0, 4, (60, 40)).astype(float)
    assert np.array_equal(vector_field(a, b, 4), vector_field(a, b, 4, predict=None))


# ── the SENSOR layer: MC decouples the aperture from the velocity ─────────────

def test_field_fidelity_mc_decouples_aperture(h1):
    """OFF saturates near the aperture; ON tracks the true (fast) displacement.
    The mechanism, at the layer the sensor actually fixes."""
    ap = h1["apparatus"]["aperture"]
    off = h1["field_fidelity_off"]
    on = h1["field_fidelity_on"]
    # a frame whose true displacement OVERRUNS the aperture must exist.
    fast = [i for i, r in enumerate(on) if r["true_disp"] > ap]
    assert fast, "apparatus does not overrun the aperture"
    for i in fast:
        # ON reads the true fast displacement; OFF cannot (bounded by the aperture).
        assert abs(on[i]["median_vy"] - on[i]["true_disp"]) <= 1.5, \
            f"MC field did not track true disp at frame {on[i]['frame']}"
        assert abs(off[i]["median_vy"]) <= ap + 0.5, \
            f"fixed aperture read {off[i]['median_vy']} > aperture {ap}"


# ── H1: fixed floors on the COEFFICIENT; MC recovers nonzero ∝-correct accel ──

def test_h1_fixed_aperture_floors(h1):
    """MC OFF (fixed aperture) recovers NO nonzero acceleration end-to-end —
    read from the graph. (Run too short / no order-2 mint / a=0 all qualify.)"""
    off = h1["mc_off_fixed_aperture"]
    assert off.get("accel_coeff") in (None, 0), \
        f"fixed aperture unexpectedly recovered accel={off.get('accel_coeff')}"


def test_h1_mc_recovers_nonzero_proportional_accel(h1):
    """MC ON mints order-2 with a NONZERO, ∝-correct (positive/downward, constant
    curvature) acceleration coefficient — read from the minted LatentDimension."""
    on = h1["mc_on"]
    ac = on.get("accel_coeff")
    assert ac is not None and ac != 0, f"MC ON did not recover a nonzero accel (got {ac})"
    # ∝-correct: same SIGN as the ideal (a downward free fall -> positive curvature),
    # and a genuine constant 2nd difference (a parabola shape, up to scale/noise).
    ideal = h1["ideal_witness"]["accel_coeff"]
    assert (ac > 0) == (ideal > 0), f"MC accel sign {ac} disagrees with ideal {ideal}"
    d2 = on.get("d2") or []
    # ROBUST constant-positive curvature: the MAJORITY of raw 2nd differences
    # equal the graph-minted coefficient and are positive. NOT exact equality
    # (`len(set(d2))==1`) — the carve's ±1 CROSS-PROCESS track jitter injects an
    # occasional glitch frame (characterized: 2/20 fresh processes give
    # d2=[3,3,39] while the minted coeff stays 3), so exact-constancy both flakes
    # on that AND contradicts the robust witness's own constant-to-dispersion
    # verdict (block 146000). The minted `ac` IS that robust median, graph-read;
    # this still fails on a true floor (no mint → ac None, caught above), on
    # noise (no positive majority), or on a sign flip.
    assert len(d2) >= 2 and ac > 0 and \
        sum(1 for x in d2 if x == ac) >= (len(d2) + 1) // 2, \
        f"MC ON 2nd difference is not a robust constant positive curvature: d2={d2} coeff={ac}"
    assert on.get("run_one_id") is True


# ── CONTROLS (MC on) ──────────────────────────────────────────────────────────

def test_control_const_velocity_is_order1_not_2(controls):
    """A constant-velocity fall (MC on) mints order-1, NOT order-2 — the predictor
    must not manufacture curvature."""
    cv = controls["const_velocity_mc_on"]
    # (a) FIELD level (noise-free, where the predictor operates): MC carries the
    #     constant velocity forward WITHOUT curvature — steady-state 2nd difference
    #     ~0, and the velocity genuinely OVERRUNS the aperture (MC engaged).
    assert cv["vel"] > cv["aperture"], "const-velocity control does not engage MC"
    assert cv["field_constant_velocity"] is True, \
        f"MC manufactured curvature in a const-velocity field: {cv['field_2nd_diff_steady']}"
    # (b) WITNESS level: no nonzero constant-positive curvature (no parabola).
    assert cv.get("accel_coeff") in (None, 0), \
        f"const-velocity confabulated accel={cv.get('accel_coeff')}"
    assert cv["no_manufactured_curvature"] is True


def test_control_static_mints_nothing(controls):
    st = controls["static_mc_on"]
    assert st.get("accel_coeff") is None
    assert not [m for m in (st.get("mints") or []) if m["order"] == 2]


def test_control_noise_floors(controls):
    """Random/noise (MC on) floors — the predictor must not hallucinate a coherent
    order-2 fall from incoherent motion."""
    nz = controls["noise_mc_on"]
    assert nz.get("accel_coeff") in (None, 0), \
        f"noise confabulated a coherent accel={nz.get('accel_coeff')}"
