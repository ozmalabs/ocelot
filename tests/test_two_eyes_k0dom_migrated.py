"""BLOCK 178000 — TWO EYES, k0-DOMINANT WALL: the supervisor's Rung-5b
prediction is FALSIFIED.

The gate for `VISION_TWO_EYES_K0DOM_PREREG.md`. The prediction under test
(recorded in `VISION_TWO_EYES_REGISTRATION_RESULTS.md` §6): the cross-frame-phase
estimator reads δ only from the CLEAN non-aliased bins {1,3} and is therefore
IMMUNE to the supra-Nyquist harmonic k0's amplitude, so a k0-DOMINANT wall would
give BOTH accurate registration AND a large gain approaching the known-offset
ceiling.

MEASURED (block seed 178000, real nonlinear eye — Naka-Rushton transduction +
integer photon quantisation + the physical zero-photon floor): the prediction is
FALSIFIED on BOTH parts, and the measurement is load-bearing (all controls hold).

Pinned here at the grain the mechanism decides (measured values; able to fail on
a true floor):
  1. THE PRE-REGISTERED VERDICT is FALSIFIED (part1 immunity fails, part2 gain
     rises fails), controls hold.
  2. IMMUNITY BREAKS at k0-dominance — the CONTINUOUS clean-bin phase read is
     amplitude-immune while k0 is modest (raw err < 0.01 for A ≤ 96) but DRIFTS
     past the 0.05 bar once k0 dominates (A=192). Not immune in the real eye.
  3. THE GAIN DOES NOT RISE toward a large ceiling — it PEAKS at modest-high A
     then FALLS; the known-offset ceiling ITSELF falls at high A (clipping /
     transduction inject supra-fused-Nyquist harmonics neither eye resolves).
  4. THE 5b 19.7×-vs-683× GAP IS A REGISTRATION-PRECISION (rounding) ARTIFACT,
     not a k0-modesty artifact: on this seed the estimate is EXACT at modest A,
     so gain_est == gain_known (no gap to close).
  5. BYTE-IDENTITY / PROVENANCE — the Rung-5/5b estimator + fusion are imported
     unchanged; the number came from this tree's own (or source-identical shared)
     engine.
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
from scripts.two_eyes_k0dom_measure import (  # noqa: E402
    A_HI, A_LO, evaluate, run_sweep)

_SWEEP = run_sweep()
_CHECKS, _SUMMARY = evaluate(_SWEEP)
_BY_A = {p["A"]: p for p in _SWEEP}
_LO = _BY_A[A_LO]
_HI = _BY_A[A_HI]


# ── The pre-registered verdict: FALSIFIED, controls load-bearing ─────────────
def test_prediction_is_falsified():
    assert _SUMMARY["prediction"] == "FALSIFIED", _SUMMARY
    assert _SUMMARY["part1_immunity"] is False, _SUMMARY   # immunity fails
    assert _SUMMARY["part2_gain_rises"] is False, _SUMMARY  # gain-rises fails
    assert _SUMMARY["controls_hold"] is True, _CHECKS       # measurement valid


# ── Part 1 falsifier: immunity BREAKS at k0-dominance (a true measured floor) ─
def test_registration_is_not_immune_to_k0_amplitude():
    # While k0 is modest the CONTINUOUS clean-bin phase read is amplitude-immune.
    for p in _SWEEP:
        if p["A"] <= 96.0:
            assert p["reg_err_raw"] < 0.01, p               # immune here
    # ... but once k0 DOMINATES the read drifts past the H1 bar — not immune.
    assert _HI["reg_err"] > 0.05, _HI
    assert _HI["reg_err_raw"] > 0.05, _HI
    assert not _CHECKS["P1a_reg_err_bounded_all_A"]
    assert not _CHECKS["P1b_reg_err_no_growth"]


# ── Part 2 falsifier: the gain does NOT rise — it peaks then falls ───────────
def test_gain_does_not_rise_toward_ceiling():
    assert not _CHECKS["P2a_gain_rises_off_modest"], _SWEEP
    # gain_est at the dominant end is FAR below 3x the modest-A gain (pinned/fell).
    assert _HI["gain_est_over_single"] < 3.0 * _LO["gain_est_over_single"]
    # the known-offset CEILING itself is non-monotone: it falls from its peak to
    # the dominant end (clipping caps the achievable fused reconstruction).
    peak_ceiling = max(p["gain_known_over_single"] for p in _SWEEP)
    assert _HI["gain_known_over_single"] < peak_ceiling, _SWEEP


# ── The 5b gap is a registration-precision artifact, not a k0-modesty one ─────
def test_gap_is_a_registration_precision_artifact():
    # On this seed the estimate is EXACT at the modest 5b point (bt rounds to the
    # true offset), so the estimated gain EQUALS the known-offset ceiling — there
    # is no 19.7x-vs-683x gap to "close". The 5b gap came from that run's
    # delta_est=0.49 (err 0.01), a rounding penalty, not from k0 being modest.
    assert _LO["reg_err"] == 0.0, _LO
    assert _LO["gain_est_over_single"] == pytest.approx(
        _LO["gain_known_over_single"], rel=1e-6), _LO


# ── Controls hold at every A (the measurement is load-bearing) ───────────────
def test_controls_hold():
    # C_ceiling — estimated never exceeds the known-offset ceiling.
    assert _CHECKS["C_ceiling_est_not_above_known"], _SWEEP
    # C_perturb — a wrong offset still degrades at the dominant end.
    assert _CHECKS["C_perturb_degrades_at_hi"], _HI
    assert min(_HI["pert_hi_over_est"], _HI["pert_lo_over_est"]) >= 2.0, _HI
    # C_zero — two identical eyes give NO gain at EVERY A (Rung-5 falsifier).
    assert _CHECKS["C_zero_no_gain_all_A"], _SWEEP
    for p in _SWEEP:
        assert 0.8 <= p["zero"]["gain_est_over_single"] <= 1.25, p


# ── The invariant: the emitted offset observable is a finer-unit integer ─────
def test_offset_observable_is_a_finer_unit_integer():
    for p in _SWEEP:
        assert isinstance(p["bt_fine"], int)                # stepped observable
        assert p["delta_est"] == p["bt_fine"] / 100.0       # cross-frame map = bt/S
        assert p["reg_bins"] == [1, 3]                       # aliased bin 2 excluded


# ── Provenance ───────────────────────────────────────────────────────────────
def test_engine_provenance_is_own_or_shared():
    prov = engine_provenance()
    assert prov["source_match"] in ("own", "shared"), prov
