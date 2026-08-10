"""tests/test_run72_migrated.py -- RUN 72 (THE MOTOR-PLANNING WRITER) unit gates, run FIRST
per the ops law. Covers: (1) sigma-lognormal fit+generate reconstructs a synthetic lognormal-
stroke trajectory; (2) generation is CONTINUOUS (no grid quantization); (3) the separation
metric computes correctly; (4) the motor plan is LOW-DIMENSIONAL; (5) generation goes through
the Rust Term (not re-implemented/duplicated in Python) -- a source audit; (6) the seed guard
(seeds/stroke_shapes.json) is untouched by any of this module's own calls.

Run:
  OZMA_SEED_PERSIST_DISABLED=1 PYTHONPATH=.:runners/dsl/python \\
    /home/matt/ozma/internal/research/.venv/bin/python3 -m pytest tests/test_run72_migrated.py -q
"""
from __future__ import annotations

import hashlib
import inspect
import math
import os
import re
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

import scripts.jabberwock_motorplan_run72 as mp72

STROKE_SHAPES_SEED = mp72.STROKE_SHAPES_SEED


def _md5(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


@pytest.fixture(scope="module")
def native():
    import substrate_rs as srs
    return srs.Substrate()._inner


# ===================================================================================== #
# GATE 0 -- seed guard: nothing in this module ever touches seeds/stroke_shapes.json.
# ===================================================================================== #
def test_seed_guard_untouched_by_fit_and_generate(native):
    before = _md5(STROKE_SHAPES_SEED)
    prims = [[0.0, 1.4, 0.35, 5.0, 0.2], [5.0, 1.2, 0.3, 3.0, 1.1]]
    gen = mp72.sigma_generate(native, prims, (0.0, 0.0), -1.0, 12.0, n_points=24)
    _ = mp72.fit_sigma_lognormal(gen.tolist())
    _ = mp72.learn_letter_form_sigma(native, gen.tolist())
    after = _md5(STROKE_SHAPES_SEED)
    assert before == after, "run72's fit/generate/learn_letter_form_sigma must not touch the seed"


# ===================================================================================== #
# GATE 1 -- fit+generate reconstructs a SYNTHETIC lognormal-stroke trajectory.
# ===================================================================================== #
def test_fit_reconstructs_synthetic_single_primitive(native):
    true_prims = [[0.0, 1.5, 0.35, 6.0, 0.4]]
    # Unit pseudo-time spacing (t_start=-1, t_end=16, n=18 -> dt=1), matching the FIT's own
    # per-sample-index convention (no real timestamps in the corpus this module targets).
    truth = mp72.sigma_generate(native, true_prims, (0.0, 0.0), -1.0, 16.0, n_points=18)

    fit_prims, t_start, t_end, start_xy = mp72.fit_sigma_lognormal(truth.tolist())
    assert len(fit_prims) >= 1
    recon = mp72.sigma_generate(native, fit_prims, start_xy, t_start, t_end, n_points=18)

    dtw = mp72.cc66.dtw(native, truth.tolist(), recon.tolist())
    arclen = mp72.cc66._arclen(truth)
    assert dtw / max(arclen, 1e-6) < 0.15, (
        f"fit+regenerate must reconstruct the synthetic single-primitive stroke closely: "
        f"dtw={dtw:.4f} arclen={arclen:.4f}")


def test_fit_reconstructs_synthetic_two_primitives(native):
    true_prims = [[0.0, 1.3, 0.3, 5.0, 0.1], [6.0, 1.2, 0.3, 4.0, 1.3]]
    truth = mp72.sigma_generate(native, true_prims, (0.0, 0.0), -1.0, 20.0, n_points=22)

    fit_prims, t_start, t_end, start_xy = mp72.fit_sigma_lognormal(truth.tolist())
    recon = mp72.sigma_generate(native, fit_prims, start_xy, t_start, t_end, n_points=22)

    dtw = mp72.cc66.dtw(native, truth.tolist(), recon.tolist())
    arclen = mp72.cc66._arclen(truth)
    assert dtw / max(arclen, 1e-6) < 0.20, (
        f"fit+regenerate must reconstruct a two-primitive synthetic stroke reasonably: "
        f"dtw={dtw:.4f} arclen={arclen:.4f}")


def test_fit_handles_degenerate_short_input():
    # <3 points -- must not raise, must return a well-formed plan.
    prims, t_start, t_end, start_xy = mp72.fit_sigma_lognormal([[0.0, 0.0], [1.0, 1.0]])
    assert len(prims) == 1 and len(prims[0]) == 5
    assert t_end > t_start
    assert start_xy == [0.0, 0.0]


# ===================================================================================== #
# GATE 2 -- generation is CONTINUOUS, not grid-quantized (the direct fix for run 71's
# StrokeQuantize floor: a discretized 12-segment/16-turn-bin codebook collapses onto a small
# alphabet of step vectors; this generator must not).
# ===================================================================================== #
def test_generation_is_continuous_not_grid_quantized(native):
    prims = [[0.0, 1.3, 0.3, 5.0, 0.1], [5.0, 1.1, 0.25, 3.5, 1.0], [10.0, 1.4, 0.35, 4.0, -0.6]]
    gen = mp72.sigma_generate(native, prims, (0.0, 0.0), -1.0, 18.0, n_points=90)
    deltas = np.round(np.diff(gen, axis=0) * 1e5).astype(np.int64)
    n_distinct = len({tuple(d) for d in deltas.tolist()})
    # StrokeQuantize's OWN alphabet is bounded by SEG=12 knot deltas total, regardless of how
    # many points it resamples to -- a small constant. This continuous generator's distinct-
    # step count must scale with resolution, not floor at a StrokeQuantize-sized constant.
    assert n_distinct > 4 * mp72.cc66.SEG, (
        f"expected far more than StrokeQuantize's own alphabet size ({mp72.cc66.SEG} segments); "
        f"got {n_distinct} distinct step vectors out of {len(deltas)}")


def test_generation_varies_smoothly_with_time_grid_density(native):
    """A CONTINUOUS generator's trajectory should converge as n_points increases (finer
    sampling of the SAME underlying curve), unlike a bin-quantized generator whose output is
    invariant to resolution above its own bin count."""
    prims = [[0.0, 1.3, 0.3, 5.0, 0.2]]
    coarse = mp72.sigma_generate(native, prims, (0.0, 0.0), -1.0, 10.0, n_points=12)
    fine = mp72.sigma_generate(native, prims, (0.0, 0.0), -1.0, 10.0, n_points=120)
    # Compare endpoints (both integrate the SAME velocity field over the SAME time window).
    assert np.linalg.norm(coarse[-1] - fine[-1]) < 0.05 * (np.linalg.norm(fine[-1]) + 1e-6)


# ===================================================================================== #
# GATE 3 -- the motor plan is LOW-DIMENSIONAL (Plamondon's own claim: a handful of primitives).
# ===================================================================================== #
def test_motor_plan_is_low_dimensional(native):
    # A moderately complex synthetic stroke with several velocity peaks.
    prims = [[0.0, 1.2, 0.3, 4.0, 0.0], [4.0, 1.1, 0.3, 3.0, 1.2],
             [8.0, 1.3, 0.3, 3.5, -1.0], [12.0, 1.2, 0.3, 3.0, 2.0]]
    gen = mp72.sigma_generate(native, prims, (0.0, 0.0), -1.0, 18.0, n_points=40)
    fit_prims, *_ = mp72.fit_sigma_lognormal(gen.tolist())
    assert len(fit_prims) <= mp72.MAX_PRIMITIVES
    for p in fit_prims:
        assert len(p) == 5, "each primitive is exactly (t0, mu, sigma, D, theta)"


def test_zero_primitives_is_degenerate_but_graceful(native):
    gen = mp72.sigma_generate(native, [], (2.0, -1.0), 0.0, 5.0, n_points=10)
    assert np.allclose(gen, np.array([2.0, -1.0]))


# ===================================================================================== #
# GATE 4 -- the separation metric (run 71's own formula) computes correctly.
# ===================================================================================== #
def test_separation_metric_computes():
    records = [
        {"true_class": 10, "genB_inv": [0.1] + [0.5] * 25, "genB_pose": [0.0] * 26},
        {"true_class": 11, "genB_inv": [0.5, 0.1] + [0.6] * 24, "genB_pose": [0.0] * 26},
    ]
    out = mp72.own_vs_wrong(records, "genB_inv", "genB_pose", lam=1.0)
    assert out["n"] == 2
    assert out["median_own"] == pytest.approx(0.1)
    assert out["median_wrong"] == pytest.approx(0.5)
    assert out["positive"] is True


def test_separation_metric_detects_negative_case():
    # Own-class score WORSE than nearest-wrong -- run 71's own finding, reproduced structurally.
    records = [
        {"true_class": 10, "genB_inv": [1.0] + [0.6] * 25, "genB_pose": [0.0] * 26},
        {"true_class": 12, "genB_inv": [0.6, 0.6, 1.0] + [0.7] * 23, "genB_pose": [0.0] * 26},
    ]
    out = mp72.own_vs_wrong(records, "genB_inv", "genB_pose", lam=1.0)
    assert out["median_own"] > out["median_wrong"]
    assert out["positive"] is False


# ===================================================================================== #
# GATE 5 -- source audit: generation goes through the Rust Term, never re-implemented; the
# FIT path never integrates a position trajectory itself (positions come EXCLUSIVELY from the
# Rust `SigmaLognormalGenerate` Term).
# ===================================================================================== #
def _code_only(fn) -> str:
    return re.sub(r'""".*?"""', "", inspect.getsource(fn), flags=re.DOTALL)


def test_sigma_generate_calls_the_rust_term():
    src = _code_only(mp72.sigma_generate)
    assert "SigmaLognormalGenerate" in src
    assert "native.evaluate" in src


def test_fit_never_integrates_a_position_trajectory_itself():
    """The FIT function may evaluate the VELOCITY-domain forward model (needed as the scipy
    least-squares objective -- ordinary closed-form curve fitting) but must never accumulate a
    position (no cumsum / running x,y state) and must never call the generator itself -- the
    Rust Term is the ONLY place a trajectory (as opposed to a velocity residual) is produced."""
    src = _code_only(mp72.fit_sigma_lognormal)
    assert "cumsum" not in src, "fit_sigma_lognormal must not integrate positions in Python"
    assert "SigmaLognormalGenerate" not in src, "fit_sigma_lognormal must not generate a trajectory itself"
    assert "sigma_generate(" not in src, "fit_sigma_lognormal must not call the generator"


def test_learn_letter_form_sigma_reuses_run66_geometry_not_reimplemented():
    src = _code_only(mp72.learn_letter_form_sigma)
    assert "cc66.invariant(" in src
    assert "cc66._arclen(" in src
    assert "cc66._heading(" in src
    assert "def invariant(" not in src and "def _arclen(" not in src and "def _heading(" not in src


def test_no_python_rule_engine_calls_anywhere_in_module():
    src = _code_only(mp72)
    for banned in ("gr.make_rule", "gr.run(", "gr._match", "gr._apply", ".run_rules("):
        assert banned not in src, f"run72 must not call the Python rule engine: found {banned!r}"


# ===================================================================================== #
# GATE 6 -- schema parity with cc66.learn_letter_form (so run 71's placement machinery
# applies UNCHANGED, per this run's own drop-in-replacement design).
# ===================================================================================== #
def test_learn_letter_form_sigma_schema_matches_run66(native):
    prims = [[0.0, 1.3, 0.3, 5.0, 0.3], [5.0, 1.2, 0.3, 3.0, -0.5]]
    gen = mp72.sigma_generate(native, prims, (1.0, 2.0), -1.0, 12.0, n_points=20)
    form = mp72.learn_letter_form_sigma(native, gen.tolist())
    for key in ("signature", "n_points", "theta", "arclen", "canon"):
        assert key in form
    assert len(form["canon"]) == mp72.CANON_N
    assert isinstance(form["theta"], float)
    assert isinstance(form["arclen"], float)

    # r71's gen_pose_from_form / gen_inv_from_form must accept this schema unchanged.
    pose = mp72.r71.gen_pose_from_form(form, k_scale=1.0, slant_deg=0.0)
    inv = mp72.r71.gen_inv_from_form(form)
    assert len(pose) == mp72.CANON_N
    assert inv is form["canon"]
