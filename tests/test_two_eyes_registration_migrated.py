"""BLOCK 176000 — TWO EYES, ESTIMATED OFFSET → SUPER-RESOLUTION.

The gate for `VISION_TWO_EYES_REGISTRATION_PREREG.md` (v1, amplitude-SAD reuse of
subcell) and `VISION_TWO_EYES_REGISTRATION_PREREG_PHASE.md` (the corrected
cross-frame-phase mechanism). Closes Rung 5's largest caveat: the sub-receptor
offset is ESTIMATED from the two eyes' OWN overlapping data, fed into the
UNCHANGED Rung-5 `multilook_superres` kernel, and the super-resolution win STILL
HOLDS. Registration is a mechanical numpy sensor; fusion is graph-native.

Pinned here:
  1. THE CORRECTED MECHANISM PASSES the pre-registered criteria — registration
     accurate (H1), super-res holds under the estimate (H2), perturbed offset
     degrades (C1), zero-offset falsifier holds (C2).
  2. THE v1 amplitude-SAD reuse FAILS registration on the aliased wall (the
     committed named constraint): the aliased target corrupts a shift metric.
  3. THE INVARIANT — the emitted offset observable is a FINER-UNIT INTEGER; the
     aliased bin is excluded by arithmetic.
  4. BYTE-IDENTITY — the Rung-5 fuser is unchanged and its OFF gate still silent;
     a default GraphEye loads no super-resolution machinery.
  5. PROVENANCE — the number came from this tree's own (or source-identical
     shared) engine; never a pinned hash.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

pytest.importorskip("substrate_rs")
np = pytest.importorskip("numpy")

from domains.engine_provenance import engine_provenance  # noqa: E402
from domains.two_eye_register import (  # noqa: E402
    clean_bins, estimate_offset_phase, estimate_offset)
from domains.two_eye_superres import SuperResFuser, sample_eye  # noqa: E402
from scripts.two_eye_registration_measure import (  # noqa: E402
    BLOCK, registration_arm, zero_offset_arm, make_texture)

_REG = registration_arm(np.random.default_rng(BLOCK), method="phase")
_SAD = registration_arm(np.random.default_rng(BLOCK), method="sad")
_ZERO = zero_offset_arm(np.random.default_rng(BLOCK + 1))


# ── H1: the offset ESTIMATED from data ≈ the true offset ─────────────────────
def test_h1_registration_accurate():
    assert _REG["reg_err"] <= 0.05, _REG


# ── H2: super-resolution HOLDS under the estimated offset ────────────────────
def test_h2_superres_holds_under_estimate():
    assert _REG["gain_est_over_single"] > 4.0, _REG
    assert _REG["k0_relerr_fused_est"] < 0.25, _REG      # k0 resolved by fusion
    assert _REG["k0_relerr_single"] > 0.60, _REG          # k0 aliases in one eye
    # the offset turns N distinct positions into 2N.
    assert _REG["single_nyquist_harmonic"] < _REG["k0"] < _REG["fused_nyquist_harmonic"]


# ── C1: a PERTURBED (wrong) offset degrades — the estimate is load-bearing ───
def test_c1_perturbed_offset_degrades():
    assert _REG["pert_hi_over_est"] >= 2.0, _REG
    assert _REG["pert_lo_over_est"] >= 2.0, _REG


# ── C2: zero true offset → estimate collapses, no gain (the Rung-5 falsifier) ─
def test_c2_zero_offset_falsifier():
    assert _ZERO["abs_delta_est"] <= 0.02, _ZERO
    assert 0.8 <= _ZERO["gain_est_over_single"] <= 1.25, _ZERO


# ── The v1 amplitude-SAD reuse FAILS on the aliased wall (named constraint) ───
def test_v1_amplitude_sad_is_corrupted_by_the_aliased_target():
    # The committed v1 result: amplitude-SAD registration cannot separate the
    # aliased supra-Nyquist target's energy from real in-band energy, so it
    # misses the offset and the fused-with-estimate is no better than one eye.
    assert _SAD["reg_err"] > 0.05, _SAD
    assert _SAD["gain_est_over_single"] < 4.0, _SAD
    # ... whereas the phase mechanism, on the SAME data, is accurate.
    assert _REG["reg_err"] < _SAD["reg_err"]


# ── The frame/continuum invariant + the aliased-bin arithmetic ───────────────
def test_offset_observable_is_a_finer_unit_integer():
    tex, _P, _a0, _ph0 = make_texture(np.random.default_rng(BLOCK), 8, 6)
    _posA, actA = sample_eye(tex, n_az=8, offset=0.0)
    _posB, actB = sample_eye(tex, n_az=8, offset=0.5)
    delta, bt, diag = estimate_offset_phase(actA, actB, S=100, N=8, k0=6)
    assert isinstance(bt, int)                            # stepped observable
    assert delta == bt / 100.0                            # cross-frame map = bt/S
    assert diag["bins"] == [1, 3]                          # aliased bin 2 excluded


def test_clean_bins_exclude_the_aliased_bin():
    # k0=6 aliases onto bin |6 mod 8| folded into [0,4] -> bin 2, excluded.
    assert clean_bins(8, 6) == [1, 3]
    # k0=5 -> alias 3 excluded; k0=6 on N=8 -> 2.
    assert 3 not in clean_bins(8, 5)


# ── Byte-identity: the Rung-5 fuser is unchanged; its OFF gate still silent ───
def test_rung5_fuser_off_gate_still_silent():
    import math
    N, P = 8, 8.0
    xa = [float(i) for i in range(N)]
    ya = [0.5 + 0.4 * math.cos(2 * math.pi * 6 * x / P) for x in xa]
    off = SuperResFuser(enabled=False)
    assert off.fuse(xa, ya, n_fine=32, period=P, ridge=1e-6, k_max=4) is None
    assert not list(off.substrate.nodes("SuperResolvedField"))


def test_default_graph_eye_loads_no_superres_machinery():
    from domains.photon_eye import GraphEye
    eye = GraphEye(n_az=8, context={"synchronous": True}).build()
    assert not list(eye.substrate.nodes("SuperresParams"))
    assert not list(eye.substrate.nodes("SuperResolvedField"))
    eye.stop()


# ── Provenance ───────────────────────────────────────────────────────────────
def test_engine_provenance_is_own_or_shared():
    p = engine_provenance()
    assert p["source_match"] in ("own", "shared"), p
