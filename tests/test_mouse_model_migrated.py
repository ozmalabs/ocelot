"""tests/test_mouse_model_migrated.py — RUN 34 unit gates, run BEFORE the Gate-0 falsifier
script per the ops law ("this isn't handwriting. This is mousewriting" -- creator, 2026-07-05).

Covers: the FORWARD observation model (`mouse_model.quantize_to_grid` / `resample_event_rate`
/ `mouse_render`) is a fixed, deterministic numpy formula; the INVERSE model
(`mouse_model.denoise_path`) recovers a synthetic smooth curve pixel-quantized by the forward
model to well under the pre-registered 0.5px band, and NEVER drifts outside that band of any
observed sample (the invertibility contract); per-stroke grid-presence band-scaling behaves
correctly on a strongly-gridded vs a gridless synthetic stroke; every opt-in `denoise=` wiring
point this run added (`glyph_motor_world.to_trajectory[_strokes]`,
`omniglot_world.trajectory`, `ink_decode.ingest_ink`, `abs_read.stage_parse_char`) is
BYTE-IDENTICAL to its pre-existing behaviour when the flag is left at its default `False`; and
a source audit confirms `domains/mouse_model.py` makes no graph/Term/rule-engine calls at all
(a pure world-adapter-class numpy transform, CLAUDE.md's own class for
`domains/ink_dynamics.py`).

Seed-isolation fixture installed as standing project convention (mirrors
`tests/test_ink_dynamics_migrated.py`'s own rationale — most tests here never boot the
substrate at all, but `ingest_ink`/`stage_parse_char` byte-identity checks do touch a bare
`Substrate`, and the discipline is uniform across every migrated test file regardless)."""
from __future__ import annotations

import inspect
import re
from pathlib import Path

import numpy as np
import pytest

from domains import mouse_model as mm


@pytest.fixture(autouse=True)
def _isolate_seed_writes(tmp_path, monkeypatch):
    try:
        from domains.teach import teach as _real_teach
        from domains import stroke_codebook as sc
        monkeypatch.setattr(sc, "teach", lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_path}))
    except Exception:
        pass


def _write_motor_file(path: Path, strokes_xy: list) -> None:
    lines = ["START"]
    for i, st in enumerate(strokes_xy):
        for (x, y) in st:
            lines.append(f"{x},{y},{i * 1000}")
        if i < len(strokes_xy) - 1:
            lines.append("BREAK")
    path.write_text("\n".join(lines) + "\n")


# =============================================================================================
#  FORWARD MODEL — quantize_to_grid / resample_event_rate / mouse_render.
# =============================================================================================
def test_quantize_to_grid_rounds_to_nearest_multiple():
    pts = np.array([[0.2, 0.49], [0.51, 1.5], [-0.5, -1.49], [2.99, -0.01]])
    out = mm.quantize_to_grid(pts, grid=1.0)
    # numpy round-half-to-even: 0.5 -> 0.0, 1.5 -> 2.0, -0.5 -> -0.0, -1.49 -> -1.0
    expected = np.array([[0.0, 0.0], [1.0, 2.0], [-0.0, -1.0], [3.0, 0.0]])
    assert np.allclose(out, expected)


def test_quantize_to_grid_respects_grid_spacing():
    pts = np.array([[0.0, 0.0], [2.4, 4.9], [7.6, 0.0]])
    out = mm.quantize_to_grid(pts, grid=2.5)
    assert np.allclose(out, np.array([[0.0, 0.0], [2.5, 5.0], [7.5, 0.0]]))


def test_quantize_to_grid_nonpositive_grid_is_passthrough():
    pts = np.array([[0.234, 1.876], [3.001, -2.5]])
    out = mm.quantize_to_grid(pts, grid=0.0)
    assert np.allclose(out, pts)


def test_quantize_to_grid_preserves_extra_columns():
    pts = np.array([[0.2, 0.49, 10.0], [0.51, 1.5, 20.0]])
    out = mm.quantize_to_grid(pts, grid=1.0)
    assert out.shape == pts.shape
    assert np.allclose(out[:, 2], pts[:, 2])   # time column untouched


def test_resample_event_rate_produces_uniform_arclength_spacing():
    # A straight 100px line -> resampled at px_per_event=10 should yield ~11 evenly-spaced pts.
    pts = np.stack([np.linspace(0.0, 100.0, 500), np.zeros(500)], axis=1)
    out = mm.resample_event_rate(pts, px_per_event=10.0)
    assert out.shape[0] == 11
    d = np.sqrt(((np.diff(out, axis=0)) ** 2).sum(axis=1))
    assert np.allclose(d, 10.0)
    assert np.allclose(out[0], [0.0, 0.0]) and np.allclose(out[-1], [100.0, 0.0])


def test_resample_event_rate_degenerate_passthrough():
    single = np.array([[1.0, 2.0]])
    assert np.allclose(mm.resample_event_rate(single), single)
    zero_len = np.array([[3.0, 3.0], [3.0, 3.0], [3.0, 3.0]])
    assert np.allclose(mm.resample_event_rate(zero_len, px_per_event=1.0), zero_len)


def test_resample_event_rate_is_deterministic_no_rng():
    pts = np.stack([np.linspace(0.0, 50.0, 37), np.sin(np.linspace(0.0, 6.0, 37)) * 5.0], axis=1)
    a = mm.resample_event_rate(pts, px_per_event=3.0)
    b = mm.resample_event_rate(pts, px_per_event=3.0)
    assert np.array_equal(a, b)


def test_mouse_render_composes_resample_then_quantize():
    pts = np.stack([np.linspace(0.0, 30.0, 200), np.zeros(200)], axis=1)
    out = mm.mouse_render(pts, grid=1.0, resample=True, px_per_event=5.0)
    manual = mm.quantize_to_grid(mm.resample_event_rate(pts, px_per_event=5.0), grid=1.0)
    assert np.allclose(out, manual)


def test_mouse_render_default_is_quantize_only():
    pts = np.array([[0.3, 0.7], [1.6, 2.2]])
    out = mm.mouse_render(pts)
    assert np.allclose(out, mm.quantize_to_grid(pts, grid=mm.DEFAULT_GRID_PX))


# =============================================================================================
#  GRID DIAGNOSTICS — integer_delta_fraction / exact_zero_turn_fraction / adaptive_tolerance.
# =============================================================================================
def test_integer_delta_fraction_all_integer_steps():
    pts = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [2.0, 1.0]])
    assert mm.integer_delta_fraction(pts) == pytest.approx(1.0)


def test_integer_delta_fraction_no_integer_steps():
    pts = np.array([[0.0, 0.0], [0.3, 0.15], [0.61, 0.42], [0.92, 0.71]])
    assert mm.integer_delta_fraction(pts) == pytest.approx(0.0)


def test_integer_delta_fraction_degenerate_stroke():
    assert mm.integer_delta_fraction(np.array([[1.0, 1.0]])) == 0.0
    assert mm.integer_delta_fraction(np.zeros((0, 2))) == 0.0


def test_exact_zero_turn_fraction_straight_staircase():
    # A pure horizontal-then-vertical staircase: every interior turn is either 0 (straight run)
    # or a right angle (the corner) -- construct one with a KNOWN fraction of exact zeros.
    xs = np.array([0.0, 1.0, 2.0, 3.0, 3.0, 3.0])
    ys = np.array([0.0, 0.0, 0.0, 0.0, 1.0, 2.0])
    pts = np.stack([xs, ys], axis=1)
    frac = mm.exact_zero_turn_fraction(pts)
    # interior points: idx 1,2,3,4 (4 of them) -- idx1,2 straight (0deg), idx3 the corner
    # (nonzero), idx4 straight again -> 3/4 exact zero.
    assert frac == pytest.approx(0.75)


def test_exact_zero_turn_fraction_smooth_curve_has_no_exact_zeros():
    th = np.linspace(0.0, np.pi, 40)
    pts = np.stack([np.cos(th), np.sin(th)], axis=1)
    assert mm.exact_zero_turn_fraction(pts) == pytest.approx(0.0)


def test_sample_dt_ms_drops_nonpositive_deltas():
    xyt = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 15.0], [2.0, 0.0, 14.0], [3.0, 0.0, 30.0]])
    dt = mm.sample_dt_ms(xyt)
    assert np.allclose(sorted(dt.tolist()), [15.0, 16.0])   # the 14<15 glitch step excluded


def test_adaptive_tolerance_full_grid_gets_full_band():
    pts = np.array([[float(i), 0.0] for i in range(10)])   # every delta is exactly 1.0
    tol = mm.adaptive_tolerance(pts, base_tol=0.5, min_band_frac=0.15)
    assert tol == pytest.approx(0.5)


def test_adaptive_tolerance_gridless_gets_scaled_down_band():
    rng = np.random.default_rng(0)
    pts = np.cumsum(rng.uniform(0.01, 0.09, size=(30, 2)), axis=0)   # never lands on an integer
    tol = mm.adaptive_tolerance(pts, base_tol=0.5, min_band_frac=0.15)
    assert tol == pytest.approx(0.5 * 0.15)


def test_adaptive_tolerance_never_zero():
    pts = np.array([[0.0123, 0.0], [0.0246, 0.01], [0.0369, 0.02]])
    assert mm.adaptive_tolerance(pts) > 0.0


# =============================================================================================
#  INVERSE MODEL — denoise_path: band containment (the invertibility CONTRACT) + recovery of a
#  synthetic smooth curve under the forward model (the invertibility CLAIM, pre-registered
#  bound: RMS well under 0.5px AND a real improvement over the raw quantized observation).
# =============================================================================================
def test_denoise_path_never_leaves_the_tolerance_band():
    rng = np.random.default_rng(1)
    th = np.linspace(0.0, 4 * np.pi, 120)
    true_curve = np.stack([20 * np.cos(th) + th * 3, 20 * np.sin(th)], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)
    denoised = mm.denoise_path(observed, tol=0.5, iters=25)
    assert np.max(np.abs(denoised - observed)) <= 0.5 + 1e-9


def test_denoise_path_short_stroke_passthrough():
    two_pt = np.array([[0.0, 0.0], [1.0, 1.0]])
    assert np.allclose(mm.denoise_path(two_pt), two_pt)
    one_pt = np.array([[3.0, 4.0]])
    assert np.allclose(mm.denoise_path(one_pt), one_pt)


def test_denoise_path_preserves_time_column():
    pts = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 15.0], [2.0, 1.0, 30.0], [3.0, 2.0, 45.0],
                     [4.0, 2.0, 60.0]])
    out = mm.denoise_path(pts, tol=0.5)
    assert out.shape == pts.shape
    assert np.allclose(out[:, 2], pts[:, 2])


# THE PRE-REGISTERED INVERTIBILITY BOUND (mirrors this run's Gate-0(ii) own pre-registration):
# a smooth curve, forward-quantized to an integer pixel grid, must be recovered by
# `denoise_path` (at its DEFAULT iteration count) to RMS well under the 0.5px band --
# pre-registered bound RMS < 0.35px -- AND the denoised RMS must be LOWER than the raw
# quantized-observation RMS (denoising must actually help, not merely stay inside a trivially-
# satisfied band). AMENDED (Gate 0(ii)'s own live run against a higher-curvature synthetic):
# the ORIGINAL default of 25 iterations FAILED this exact bound (RMS 0.5477px, worse than
# doing nothing) -- over-smoothing, diagnosed and fixed in `mouse_model.py`'s own docstring
# (`DEFAULT_DENOISE_ITERS` reduced 25 -> 2). This test now exercises the DEFAULT (not a
# hardcoded iteration count) so a future regression of that default is caught here first.
DENOISE_RMS_BOUND_PX = 0.35


def _rms(a, b):
    return float(np.sqrt(((a - b) ** 2).sum(axis=1).mean()))


def test_denoise_path_recovers_synthetic_smooth_curve_under_bound():
    th = np.linspace(0.0, 3 * np.pi, 150)
    true_curve = np.stack([30 * np.cos(th * 0.7) + 0.4 * th * 30,
                            30 * np.sin(th * 0.7) + 10 * np.sin(th * 0.15)], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)
    denoised = mm.denoise_path(observed, tol=0.5)   # DEFAULT iters -- the value under test.

    raw_rms = _rms(observed, true_curve)
    denoised_rms = _rms(denoised, true_curve)
    assert denoised_rms < DENOISE_RMS_BOUND_PX, (
        f"denoised RMS {denoised_rms:.4f}px exceeds the pre-registered "
        f"{DENOISE_RMS_BOUND_PX}px bound")
    assert denoised_rms < raw_rms, (
        f"denoising must improve on the raw quantized observation: "
        f"denoised={denoised_rms:.4f}px raw={raw_rms:.4f}px")


def test_denoise_path_recovers_higher_curvature_synthetic_under_bound():
    # THE GATE-0(ii) CURVE ITSELF (a 2x/3x-frequency Lissajous) -- the fixture that FALSIFIED
    # the original iters=25 default; kept here as a permanent regression gate on the corrected
    # default so it can never silently regress back to an over-smoothing value.
    th = np.linspace(0.0, 2 * np.pi, 220)
    true_curve = np.stack([40 * np.sin(3 * th + 0.4) + 0.15 * th * 40, 40 * np.sin(2 * th)], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)
    denoised = mm.denoise_path(observed, tol=0.5)
    raw_rms = _rms(observed, true_curve)
    denoised_rms = _rms(denoised, true_curve)
    assert denoised_rms < DENOISE_RMS_BOUND_PX
    assert denoised_rms < raw_rms


def test_denoise_path_more_iterations_can_oversmooth_high_curvature():
    # DOCUMENTS THE MECHANISM (not merely the symptom): iterating the box filter too many
    # times on a curve whose curvature scale is comparable to the sample spacing makes
    # reconstruction WORSE than the raw quantized observation -- the reason
    # `DEFAULT_DENOISE_ITERS` is small, not large. A future change that quietly raises the
    # default without re-checking this trade-off will fail the bound test above first, but
    # this test pins the DIRECTION of the effect explicitly.
    th = np.linspace(0.0, 2 * np.pi, 220)
    true_curve = np.stack([40 * np.sin(3 * th + 0.4) + 0.15 * th * 40, 40 * np.sin(2 * th)], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)
    raw_rms = _rms(observed, true_curve)
    rms_light = _rms(mm.denoise_path(observed, tol=0.5, iters=2), true_curve)
    rms_heavy = _rms(mm.denoise_path(observed, tol=0.5, iters=25), true_curve)
    assert rms_light < raw_rms
    assert rms_heavy > raw_rms
    assert rms_heavy > rms_light


# =============================================================================================
#  RUN 34b — GLOBAL CONSTRAINED SMOOTHER (`denoise_path_global`, `denoise_path(..., mode=
#  "global")`): the PRINCIPLED successor to the local iterated filter above, built because
#  34a's own Gate-0(iii) showed a local filter cannot see past an exactly-collinear Bresenham
#  run to the curvature underneath it. Covers: the pentadiagonal band derivation (a pinned
#  regression against hand-derived values); the HEADLINE tube-bowing property a local filter
#  structurally cannot have; straight-line fidelity (no hallucinated curvature); the same
#  invertibility contract (band containment) and determinism guarantees as the local method;
#  the `mode=` dispatch in `denoise_path` itself.
# =============================================================================================
def test_pentadiagonal_bands_match_hand_derivation():
    # Pinned against the hand-derived pentadiagonal stencil (a discrete-biharmonic operator,
    # [1,-4,6,-4,1] in its far-interior rows, tapering near each end) -- see
    # `_pentadiagonal_bands`'s own docstring for the derivation. m=3/4/5/6 cover every distinct
    # boundary shape (m=3: one row only; m=4: two boundary rows, no far-interior; m=5/6: the
    # first far-interior row appears).
    d0, d1, d2 = mm._pentadiagonal_bands(3)
    assert np.allclose(d0, [1.0, 4.0, 1.0])
    assert np.allclose(d1, [-2.0, -2.0, 0.0])
    assert np.allclose(d2, [1.0, 0.0, 0.0])

    d0, d1, d2 = mm._pentadiagonal_bands(4)
    assert np.allclose(d0, [1.0, 5.0, 5.0, 1.0])
    assert np.allclose(d1, [-2.0, -4.0, -2.0, 0.0])
    assert np.allclose(d2, [1.0, 1.0, 0.0, 0.0])

    d0, d1, d2 = mm._pentadiagonal_bands(6)
    assert np.allclose(d0, [1.0, 5.0, 6.0, 6.0, 5.0, 1.0])
    assert np.allclose(d1, [-2.0, -4.0, -4.0, -4.0, -2.0, 0.0])
    assert np.allclose(d2, [1.0, 1.0, 1.0, 1.0, 0.0, 0.0])


def test_denoise_path_global_never_leaves_the_tolerance_band():
    th = np.linspace(0.0, 4 * np.pi, 120)
    true_curve = np.stack([20 * np.cos(th) + th * 3, 20 * np.sin(th)], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)
    denoised = mm.denoise_path_global(observed, tol=0.5)
    assert np.max(np.abs(denoised - observed)) <= 0.5 + 1e-9


def test_denoise_path_global_short_stroke_passthrough():
    two_pt = np.array([[0.0, 0.0], [1.0, 1.0]])
    assert np.allclose(mm.denoise_path_global(two_pt), two_pt)
    one_pt = np.array([[3.0, 4.0]])
    assert np.allclose(mm.denoise_path_global(one_pt), one_pt)


def test_denoise_path_global_preserves_time_column():
    pts = np.array([[0.0, 0.0, 0.0], [1.0, 1.0, 15.0], [2.0, 1.0, 30.0], [3.0, 2.0, 45.0],
                     [4.0, 2.0, 60.0]])
    out = mm.denoise_path_global(pts, tol=0.5)
    assert out.shape == pts.shape
    assert np.allclose(out[:, 2], pts[:, 2])


def test_denoise_path_global_is_deterministic():
    th = np.linspace(0.0, 3 * np.pi, 90)
    curve = np.stack([25 * np.cos(th * 0.5), 25 * np.sin(th * 0.5)], axis=1)
    observed = mm.quantize_to_grid(curve, grid=1.0)
    a = mm.denoise_path_global(observed, tol=0.5)
    b = mm.denoise_path_global(observed, tol=0.5)
    assert np.array_equal(a, b)


def test_denoise_path_global_recovers_synthetic_curve_under_bound():
    # Same pre-registered bound class as the local method's own gate (DENOISE_RMS_BOUND_PX);
    # the global method must ALSO pass invertibility on the exact curve that falsified the
    # original (25-iteration) local default.
    th = np.linspace(0.0, 2 * np.pi, 220)
    true_curve = np.stack([40 * np.sin(3 * th + 0.4) + 0.15 * th * 40, 40 * np.sin(2 * th)], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)
    denoised = mm.denoise_path_global(observed, tol=0.5)
    raw_rms = _rms(observed, true_curve)
    denoised_rms = _rms(denoised, true_curve)
    assert denoised_rms < DENOISE_RMS_BOUND_PX
    assert denoised_rms < raw_rms


# THE PRE-REGISTERED STRAIGHT-LINE FIDELITY BOUND (Gate 0b(ii-b)'s own pre-registration,
# mirrored here as a permanent unit gate): a genuinely straight latent path, quantized then
# denoised, must come back straight -- a global curvature-minimizing objective must not
# hallucinate bowing where there is no real curvature to recover, only quantization noise.
STRAIGHT_LINE_RMS_BOUND_PX = 0.30


def test_denoise_path_global_straight_line_fidelity():
    n = 180
    t = np.linspace(0.0, 1.0, n)
    true_line = np.stack([t * 150.0, t * 90.0], axis=1)   # non-axis-aligned diagonal.
    observed = mm.quantize_to_grid(true_line, grid=1.0)
    denoised = mm.denoise_path_global(observed, tol=0.5)
    denoised_rms = _rms(denoised, true_line)
    assert denoised_rms < STRAIGHT_LINE_RMS_BOUND_PX, (
        f"global smoother hallucinated curvature on a true straight line: "
        f"RMS {denoised_rms:.4f}px exceeds {STRAIGHT_LINE_RMS_BOUND_PX}px")
    assert np.max(np.abs(denoised - observed)) <= 0.5 + 1e-9


def test_denoise_path_global_bows_through_collinear_run_local_cannot():
    # THE HEADLINE PROPERTY (34a's own named next lever): a Bresenham staircase run is locally
    # EXACTLY collinear over several consecutive samples -- a 3-tap local average of identical
    # deltas reproduces the same points exactly (nothing to average away), so `denoise_path`
    # (mode="local") is STRUCTURALLY unable to move a point in the interior of such a run. The
    # global method, solving the WHOLE stroke's curvature jointly, uses information from
    # OUTSIDE the run (its two ends connect to non-collinear samples) to bow the interior
    # points off the raw observation -- something no local filter can do by construction. A
    # shallow large-radius arc (R=500) reliably produces such a run under quantization.
    R = 500.0
    n = 60
    theta = np.linspace(0.0, 0.25, n)
    true_curve = np.stack([R * np.sin(theta), R * (1 - np.cos(theta))], axis=1)
    observed = mm.quantize_to_grid(true_curve, grid=1.0)

    d = np.diff(observed, axis=0)
    run_start = None
    for i in range(len(d) - 3):
        if np.allclose(d[i], d[i + 1]) and np.allclose(d[i + 1], d[i + 2]) and \
                np.allclose(d[i + 2], d[i + 3]):
            run_start = i
            break
    assert run_start is not None, "fixture must contain a >=4-sample exactly-collinear run"
    mid = run_start + 2   # an INTERIOR point of the collinear run.

    local = mm.denoise_path(observed, tol=0.5, mode="local")
    glob = mm.denoise_path(observed, tol=0.5, mode="global")

    assert np.allclose(local[mid], observed[mid]), (
        "local filter is expected to leave the interior of an exactly-collinear run untouched "
        "-- if this fails, the fixture no longer demonstrates the local method's own limit")
    assert not np.allclose(glob[mid], observed[mid]), (
        "global smoother should bow the interior of the collinear run using information from "
        "outside the run -- it did not move at all"
    )
    assert np.max(np.abs(glob - observed)) <= 0.5 + 1e-9   # still honours the band contract.

    raw_rms = _rms(observed, true_curve)
    local_rms = _rms(local, true_curve)
    global_rms = _rms(glob, true_curve)
    assert global_rms < local_rms < raw_rms, (
        f"expected raw({raw_rms:.4f}) > local({local_rms:.4f}) > global({global_rms:.4f})")


def test_denoise_path_mode_default_is_local_byte_identical():
    th = np.linspace(0.0, 3 * np.pi, 90)
    curve = np.stack([25 * np.cos(th * 0.5), 25 * np.sin(th * 0.5)], axis=1)
    observed = mm.quantize_to_grid(curve, grid=1.0)
    a = mm.denoise_path(observed, tol=0.5)
    b = mm.denoise_path(observed, tol=0.5, mode="local")
    assert np.array_equal(a, b)


def test_denoise_path_mode_global_dispatches_to_denoise_path_global():
    th = np.linspace(0.0, 3 * np.pi, 90)
    curve = np.stack([25 * np.cos(th * 0.5), 25 * np.sin(th * 0.5)], axis=1)
    observed = mm.quantize_to_grid(curve, grid=1.0)
    a = mm.denoise_path(observed, tol=0.5, mode="global")
    b = mm.denoise_path_global(observed, tol=0.5)
    assert np.array_equal(a, b)
    # and it genuinely differs from the local default (not a silent no-op dispatch).
    c = mm.denoise_path(observed, tol=0.5, mode="local")
    assert not np.array_equal(a, c)


def test_denoise_path_global_band_scaling_matches_local_adaptive_tolerance():
    # Same `adaptive_tolerance` machinery underlies both methods' auto-scaling -- a gridless
    # stroke gets the SAME scaled-down band under either mode.
    rng = np.random.default_rng(7)
    gridless = np.cumsum(rng.uniform(0.01, 0.09, size=(30, 2)), axis=0)
    denoised = mm.denoise_path_global(gridless, tol=None)
    expected_band = mm.adaptive_tolerance(gridless)
    assert np.max(np.abs(denoised - gridless)) <= expected_band + 1e-9
    assert expected_band < mm.DEFAULT_BAND_PX   # confirms the scaled-down (not full) band applied.


def test_denoise_strokes_maps_per_stroke_independently():
    s1 = np.array([[0.0, 0.0], [1.2, 0.1], [2.1, -0.2], [3.0, 0.05]])
    s2 = np.array([[10.0, 10.0], [11.3, 9.8], [12.0, 10.4], [13.1, 9.9]])
    out = mm.denoise_strokes([s1, s2], tol=0.5)
    assert len(out) == 2
    assert np.allclose(out[0], mm.denoise_path(s1, tol=0.5))
    assert np.allclose(out[1], mm.denoise_path(s2, tol=0.5))


# =============================================================================================
#  WIRING — every denoise= opt-in hook is byte-identical to pre-existing behaviour by default.
# =============================================================================================
def test_to_trajectory_default_byte_identical():
    from domains import glyph_motor_world as gmw
    rng = np.random.default_rng(2)
    pts = np.cumsum(rng.normal(0, 1, size=(40, 2)), axis=0)
    a = gmw.to_trajectory(pts)
    b = gmw.to_trajectory(pts, denoise=False)
    assert np.array_equal(a, b)


def test_to_trajectory_strokes_default_byte_identical():
    from domains import glyph_motor_world as gmw
    rng = np.random.default_rng(3)
    strokes = [np.cumsum(rng.normal(0, 1, size=(20, 2)), axis=0) for _ in range(3)]
    a = gmw.to_trajectory_strokes(strokes)
    b = gmw.to_trajectory_strokes(strokes, denoise=False)
    assert np.array_equal(a, b)


def test_to_trajectory_denoise_true_changes_output():
    from domains import glyph_motor_world as gmw
    th = np.linspace(0.0, 3 * np.pi, 60)
    curve = np.stack([15 * np.cos(th), 15 * np.sin(th)], axis=1)
    observed = mm.quantize_to_grid(curve, grid=1.0)
    plain = gmw.to_trajectory(observed)
    denoised = gmw.to_trajectory(observed, denoise=True)
    assert not np.array_equal(plain, denoised)


def test_omniglot_trajectory_default_byte_identical(tmp_path):
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)], [(10.0, 10.0), (12.0, 8.0)]])
    a = ow.trajectory(str(f), per_stroke=True)
    b = ow.trajectory(str(f), per_stroke=True, denoise=False)
    assert np.array_equal(a, b)
    c = ow.trajectory(str(f), per_stroke=False)
    d = ow.trajectory(str(f), per_stroke=False, denoise=False)
    assert np.array_equal(c, d)


def test_ingest_ink_default_byte_identical():
    pytest.importorskip("substrate_rs")
    import substrate_rs as srs
    from domains import ink_decode as ink
    rng = np.random.default_rng(4)
    pts = np.cumsum(rng.normal(0, 1, size=(30, 2)), axis=0).tolist()

    s1 = srs.Substrate()
    n1 = ink.ingest_ink(s1, pts, max_knots=24)
    s2 = srs.Substrate()
    n2 = ink.ingest_ink(s2, pts, max_knots=24, denoise=False)

    a1, a2 = s1.node(n1)["attrs"], s2.node(n2)["attrs"]
    assert a1["knots"] == a2["knots"]
    assert a1["points"] == a2["points"]


def test_ingest_ink_denoise_true_changes_knots():
    pytest.importorskip("substrate_rs")
    import substrate_rs as srs
    from domains import ink_decode as ink
    th = np.linspace(0.0, 3 * np.pi, 60)
    curve = np.stack([15 * np.cos(th), 15 * np.sin(th)], axis=1)
    observed = mm.quantize_to_grid(curve, grid=1.0).tolist()

    s1 = srs.Substrate()
    n1 = ink.ingest_ink(s1, observed, max_knots=24)
    s2 = srs.Substrate()
    n2 = ink.ingest_ink(s2, observed, max_knots=24, denoise=True)

    assert s1.node(n1)["attrs"]["knots"] != s2.node(n2)["attrs"]["knots"]


def test_stage_parse_char_default_byte_identical(tmp_path):
    pytest.importorskip("substrate_rs")
    import substrate_rs as srs
    from domains import abs_read as ar
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0), (0.0, 5.0)],
                          [(8.0, 8.0), (10.0, 6.0), (12.0, 8.0)]])

    from domains import recognition_graph as rg
    s1 = srs.Substrate()
    n1 = ar.stage_parse_char(s1, str(f), is_query=False, name="x")
    s2 = srs.Substrate()
    n2 = ar.stage_parse_char(s2, str(f), is_query=False, name="x", denoise=False)
    assert s1.node(n1)["attrs"][rg.WORD_FEAT_ATTR] == s2.node(n2)["attrs"][rg.WORD_FEAT_ATTR]


def test_stage_parse_char_denoise_true_changes_whole_feature(tmp_path):
    pytest.importorskip("substrate_rs")
    import substrate_rs as srs
    from domains import abs_read as ar
    from domains import recognition_graph as rg
    f = tmp_path / "char.txt"
    th = np.linspace(0.0, 2 * np.pi, 40)
    curve = np.stack([15 * np.cos(th), 15 * np.sin(th)], axis=1)
    observed = mm.quantize_to_grid(curve, grid=1.0)
    _write_motor_file(f, [observed.tolist()])

    s1 = srs.Substrate()
    n1 = ar.stage_parse_char(s1, str(f), is_query=False, name="x")
    s2 = srs.Substrate()
    n2 = ar.stage_parse_char(s2, str(f), is_query=False, name="x", denoise=True)
    whole1 = s1.node(n1)["attrs"][rg.WORD_FEAT_ATTR]
    whole2 = s2.node(n2)["attrs"][rg.WORD_FEAT_ATTR]
    assert whole1 != whole2


# =============================================================================================
#  SOURCE AUDIT — this module is a pure world-adapter-class numpy transform: no graph handle,
#  no Rust `evaluate`, no rule engine, no `teach()` — CLAUDE.md's own class for
#  `domains/ink_dynamics.py` (a FIXED FORMULA over already-collected numbers, never a decision
#  over graph state).
# =============================================================================================
def test_mouse_model_makes_no_graph_or_term_calls():
    # Strip docstrings first (the module docstring PROSE names the held Terms this run's
    # verdict layer uses, for context -- only ACTUAL calls in code are disqualifying).
    code_only = re.sub(r'""".*?"""', "", inspect.getsource(mm), flags=re.DOTALL)
    forbidden = ["substrate_rs", ".evaluate(", "run_rules(", "add_node(", "add_edge",
                 "teach(", "_inner", "ShapeDecode(", "TransformDecode("]
    hits = [tok for tok in forbidden if tok in code_only]
    assert not hits, f"mouse_model.py must stay pure-numpy (no graph/Term calls) -- found: {hits}"


def test_mouse_model_has_no_rng_in_default_forward_path():
    src = inspect.getsource(mm)
    # the forward model (quantize_to_grid / resample_event_rate / mouse_render) must be
    # reproducible -- no numpy RNG anywhere in this module (the denoiser is deterministic
    # too: iterated local averaging, no sampling).
    assert "np.random" not in src and "default_rng" not in src


# =============================================================================================
#  RUN 37C -- INGEST HYGIENE: `omniglot_world.load_strokes`/`load_strokes_t`/`trajectory`'s new
#  opt-in `drop_degenerate` param. Criterion (pre-registered, matches `_is_degenerate_stroke`'s
#  docstring): a stroke is DEGENERATE iff it is a single recorded sample, OR every recorded
#  sample sits at the exact same (x, y) (zero arc length across >=2 points). NOT a size filter
#  -- a short-but-real stroke (a dot/tick) that moves even a sub-pixel MUST survive.
# =============================================================================================
def test_load_strokes_drop_degenerate_removes_single_point_stroke(tmp_path):
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)], [(10.0, 10.0)]])
    default = ow.load_strokes(str(f))
    filtered = ow.load_strokes(str(f), drop_degenerate=True)
    assert len(default) == 2 and len(filtered) == 1
    assert filtered[0].shape[0] == 3


def test_load_strokes_drop_degenerate_removes_zero_length_multisample_stroke(tmp_path):
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)],
                          [(3.0, 3.0), (3.0, 3.0), (3.0, 3.0), (3.0, 3.0)]])
    default = ow.load_strokes(str(f))
    filtered = ow.load_strokes(str(f), drop_degenerate=True)
    assert len(default) == 2 and default[1].shape[0] == 4   # the zero-length stroke IS present
    assert len(filtered) == 1                                # ...and IS dropped when filtered
    assert filtered[0].shape[0] == 3


def test_load_strokes_drop_degenerate_keeps_real_small_dot_stroke(tmp_path):
    """A dot/tick that moves even a sub-pixel is a genuine glyph element (some alphabets), not
    degenerate -- the criterion is motionlessness, never sample count or physical size."""
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)],
                          [(7.0, 7.0), (7.2, 7.1), (7.1, 7.3)]])
    filtered = ow.load_strokes(str(f), drop_degenerate=True)
    assert len(filtered) == 2
    assert filtered[1].shape[0] == 3


def test_load_strokes_drop_degenerate_default_false_is_byte_identical(tmp_path):
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)], [(10.0, 10.0)],
                          [(3.0, 3.0), (3.0, 3.0)]])
    a = ow.load_strokes(str(f))
    b = ow.load_strokes(str(f), drop_degenerate=False)
    assert len(a) == len(b) == 3
    assert all(np.array_equal(x, y) for x, y in zip(a, b))


def test_load_strokes_all_degenerate_file_returns_empty_not_a_crash(tmp_path):
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(5.0, 5.0)], [(9.0, 9.0), (9.0, 9.0)]])
    filtered = ow.load_strokes(str(f), drop_degenerate=True)
    assert filtered == []
    # downstream trajectory construction must not crash on a fully-filtered file.
    traj = ow.trajectory(str(f), per_stroke=True, drop_degenerate=True)
    assert traj.shape == (48, 2) or np.allclose(traj, 0.0)
    assert np.allclose(traj, 0.0)


def test_load_strokes_t_drop_degenerate_matches_load_strokes_and_keeps_flags_aligned(tmp_path):
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)], [(10.0, 10.0)],
                          [(3.0, 3.0), (3.0, 3.0), (3.0, 3.0)]])
    strokes_default, fb_default = ow.load_strokes_t(str(f))
    strokes_filtered, fb_filtered = ow.load_strokes_t(str(f), drop_degenerate=True)
    assert len(strokes_default) == len(fb_default) == 3
    assert len(strokes_filtered) == len(fb_filtered) == 1
    assert np.array_equal(strokes_filtered[0][:, :2],
                           ow.load_strokes(str(f), drop_degenerate=True)[0])


def test_load_strokes_t_drop_degenerate_default_false_is_byte_identical(tmp_path):
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)], [(10.0, 10.0)]])
    a, fa = ow.load_strokes_t(str(f))
    b, fb = ow.load_strokes_t(str(f), drop_degenerate=False)
    assert fa == fb
    assert all(np.array_equal(x, y) for x, y in zip(a, b))


def test_trajectory_drop_degenerate_default_false_is_byte_identical(tmp_path):
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0)], [(10.0, 10.0)],
                          [(3.0, 3.0), (3.0, 3.0)]])
    a = ow.trajectory(str(f), per_stroke=True)
    b = ow.trajectory(str(f), per_stroke=True, drop_degenerate=False)
    assert np.array_equal(a, b)
    # per_stroke=False reads raw points via load_points (no stroke boundaries) -- also untouched.
    c = ow.trajectory(str(f), per_stroke=False)
    d = ow.trajectory(str(f), per_stroke=False, drop_degenerate=False)
    assert np.array_equal(c, d)


def test_trajectory_drop_degenerate_true_changes_per_stroke_output_when_degenerate_present(
        tmp_path):
    # NOTE: `glyph_motor_world.to_trajectory_strokes` already drops SINGLE-POINT strokes on its
    # own (a pre-existing `shape[0] >= 2` filter, unrelated to this run) -- so this must use a
    # ZERO-LENGTH but multi-sample degenerate stroke (which that pre-existing filter does NOT
    # catch) to actually exercise the new `drop_degenerate` wiring at the trajectory level.
    from domains import omniglot_world as ow
    f = tmp_path / "char.txt"
    _write_motor_file(f, [[(0.0, 0.0), (5.0, 0.0), (5.0, 5.0), (0.0, 5.0)],
                          [(10.0, 10.0), (10.0, 10.0), (10.0, 10.0)]])
    plain = ow.trajectory(str(f), per_stroke=True)
    filtered = ow.trajectory(str(f), per_stroke=True, drop_degenerate=True)
    assert not np.array_equal(plain, filtered)
