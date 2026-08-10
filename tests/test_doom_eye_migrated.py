"""GATE — the photon eye sees Doom (seed block 181000).

Pins, at the MECHANISM grain, the falsifiable facts of VISION_DOOM_EYE_PREREG.md,
each ABLE TO FAIL on a flat build / no cost-bend / a surviving scramble:

  1. BUILD      — on a held REAL Doom frame the held_surface reconstruction error
                  (held vs the true luminance field) drops toward an asymptote as
                  the graph rule EMA-integrates the noisy per-tick observation.
  2. STATELESS  — the raw single-tick observation stays FLAT above the denoised
                  asymptote; the held surface sits a clear factor below it (the
                  accumulation gap — fails if the held surface stops persisting).
  3. COST-BEND  — per-tick WORK (onset-event count) DRAINS to a low plateau on the
                  static hold and SPIKES on the REAL turning motion (compute ∝
                  surprise), then re-drains.
  4. SCRAMBLE   — a temporally-SCRAMBLED frame order KILLS the build (no drop) and
                  keeps compute high — the build needs real temporal coherence.
  5. STRUCTURE  — the held reconstruction's edges correlate with the true DEPTH
                  structure (oracle) above a spatial-shuffle null.

SELF-CONTAINED and VizDoom-free: it runs the SAME graph-native mechanism as the
live measure (scripts/doom_eye_measure.compute_criteria) on a COMMITTED fixture of
a handful of real E1M1 frames (downsampled luminance + depth), so CI needs no
VizDoom. The eye's perception is entirely graph rules under run_rules(); the
depth buffer is an ORACLE for scoring only, never fed to the eye. No agent
decision, no Rust, no Term, no new seed.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts import doom_eye_measure as dem                  # noqa: E402

FIXTURE = os.path.join(ROOT, "tests", "fixtures", "doom_eye", "frames.npz")

_CACHE = {}


def _results():
    if "r" not in _CACHE:
        assert os.path.exists(FIXTURE), f"missing committed fixture {FIXTURE}"
        d = np.load(FIXTURE)
        f0 = d["f0"].astype(float)
        motion = [m.astype(float) for m in d["motion"]]
        depth = d["depth"].astype(float)
        luma_seq = [f0] * dem.T1 + motion + [motion[-1]] * dem.T3
        _CACHE["r"] = dem.compute_criteria(luma_seq, motion, depth, seed=dem.SEED)
    return _CACHE["r"]


def test_fixture_is_real_doom_frames():
    d = np.load(FIXTURE)
    assert d["f0"].shape == (dem.N_EL, dem.N_AZ)
    assert d["motion"].shape[0] == dem.M
    # a real 8-bit luminance field spans a broad range (not a synthetic block)
    assert d["f0"].max() > 40 and d["f0"].min() < 30
    assert d["depth"].max() > d["depth"].min() + 10      # real depth structure


def test_build_curve_drops_on_a_real_held_doom_frame():
    r = _results()
    b = r["acc_EA"]; asymptote = r["asymptote"]
    assert asymptote < 0.12                       # denoised asymptote (fails flat)
    assert asymptote < 0.15 * b[0]                # >=~6x reduction: gist->reconstruction
    assert r["monotone_violations"] <= 3


def test_stateless_control_flat_and_accumulation_gap_is_real():
    r = _results()
    sl = r["stateless_EA"]; asymptote = r["asymptote"]
    assert np.std(sl) / max(np.mean(sl), 1e-9) < 0.20     # single-tick FLAT (no build)
    assert np.mean(sl) > 2.0 * asymptote                  # sits above the asymptote
    assert asymptote < 0.5 * np.mean(sl)                  # THE build (held beats stateless)


def test_cost_bends_low_on_static_high_on_real_motion():
    r = _results()
    assert r["plateau"] <= 0.15 * max(r["cost_start"], 1)  # work DRAINS on static hold
    assert r["motion_C_peak"] >= 20                        # a clear multi-cell real event
    assert r["motion_C_mean"] >= 3.0 * max(r["plateau"], 1.0)   # SPIKE (compute ∝ surprise)
    assert r["cost_static_vs_motion_ratio"] >= 3.0
    # re-drain once the motion stops (STATIC-B)
    assert r["plateau_B"] <= 0.5 * max(r["motion_C_peak"], 1e-9)


def test_scrambled_order_kills_the_build_and_keeps_cost_high():
    r = _results()
    # NO build: the scrambled accumulation gap collapses to <= half the ordered gap
    # (here it goes negative — the EMA actively lags a moving target).
    assert r["scramble_gap"] <= 0.5 * r["accumulation_gap"]
    # the scrambled held error does NOT converge like the ordered build
    assert r["scramble_asymptote"] > 2.0 * r["asymptote"]
    # compute stays HIGH (does not drain to the static plateau)
    assert r["scramble_C_mean"] >= 3.0 * max(r["plateau"], 1.0)


def test_recovers_real_depth_structure_above_null():
    r = _results()
    s = r["structure"]
    assert s, "depth oracle missing from fixture"
    assert s["depth_edge_corr"] > 0.15                     # held edges track depth structure
    assert s["depth_edge_corr"] > s["null_corr_abs_mean"]  # above the spatial-shuffle null


def test_all_prereg_criteria_pass():
    r = _results()
    failed = [k for k, v in r["criteria"].items() if not v]
    assert not failed, f"prereg criteria failed: {failed}"
