"""RUN 43 PHASE 3 -- unit gates for `domains/exemplar_expand.py` (exemplar expansion under a
background-calibrated variation model) + the gate script's own held min-over-set/argmin
machinery (`scripts/jabberwock_omniglot_run43_expand.py`): the rotation/shear estimators
recover known injected deltas, variant rendering applies the intended calibrated delta, the
min-over-set score structurally never exceeds the original's own score, the calibration
freeze mechanics never silently recompute, everything is deterministic (no RNG anywhere in this
run's variant grid), and a source audit confirms `exemplar_expand.py` makes no Python
argmin/argmax/score-sort decision (that stays a held Term in the gate script, per
`episode_style.py`'s own precedent)."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

import substrate_rs as srs

from domains import exemplar_expand as ee

RNG_SEED = 20260705


def _isotropic_glyph(rng, n_strokes: int = 3, pts_per_stroke: int = 40) -> list:
    """A multi-stroke synthetic glyph with (in expectation) zero shear/rotation bias -- each
    stroke is a random walk inside a centered square, x/y independent. Mirrors `tests.
    test_episode_style_migrated._isotropic_glyph` exactly (same synthetic family, this run's
    own new estimators need the identical baseline property)."""
    strokes = []
    for _ in range(n_strokes):
        x = rng.uniform(-1.0, 1.0, size=pts_per_stroke)
        y = rng.uniform(-1.0, 1.0, size=pts_per_stroke)
        strokes.append(np.stack([x, y], axis=1))
    return strokes


def _rotate(strokes: list, angle: float) -> list:
    ca, sa = np.cos(angle), np.sin(angle)
    R = np.array([[ca, -sa], [sa, ca]])
    return [np.asarray(s, dtype=float) @ R.T for s in strokes]


def _apply_shear(strokes: list, s: float) -> list:
    out = []
    for st in strokes:
        arr = np.asarray(st, dtype=float).copy()
        arr[:, 0] = arr[:, 0] + s * arr[:, 1]
        out.append(arr)
    return out


# ===================================================================================================
# Gate 1 -- rotation estimator recovers an injected rotation (new estimator this module adds).
# ===================================================================================================
@pytest.mark.parametrize("deg", [-25.0, -8.0, 5.0, 20.0])
def test_rotation_estimator_recovers_injected_rotation(deg):
    base = _isotropic_glyph(np.random.default_rng(1))
    rotated = _rotate(base, np.radians(deg))
    a0 = ee.estimate_rotation_angle(base)
    a1 = ee.estimate_rotation_angle(rotated)
    delta = ee._wrap_half_pi(a1 - a0)
    assert abs(delta - np.radians(deg)) < 1e-4, f"deg={deg} -> delta={np.degrees(delta)}"


def test_pool_rotation_recovers_zero_spread_for_identical_angles():
    mean, resid = ee.pool_rotation([0.3, 0.3, 0.3])
    assert abs(ee._wrap_half_pi(mean - 0.3)) < 1e-9
    assert all(abs(r) < 1e-9 for r in resid)


def test_pool_rotation_empty_is_honest_zero():
    mean, resid = ee.pool_rotation([])
    assert mean == 0.0 and resid == []


# ===================================================================================================
# Gate 2 -- VARIANT RENDERING applies the intended calibrated dim delta: known shear in ->
# measured shear out (the launch brief's own explicitly required test).
# ===================================================================================================
@pytest.mark.parametrize("sign", [-1, 1])
def test_variant_rendering_shear_delta_matches_calibration(sign):
    base = _isotropic_glyph(np.random.default_rng(2))
    shear_std = 0.4
    calib = dict(shear_std=shear_std, rotation_std=0.0, pose_x_std=0.0, pose_y_std=0.0,
                 pose_o_std=0.0, pose_s_std=0.0)
    variant = ee.render_variant(base, "shear", sign, calib, quantize=False)
    from domains import episode_style as es
    delta = es.estimate_shear(variant) - es.estimate_shear(base)
    expected = sign * ee.Z_QUANTILE * shear_std
    assert abs(delta - expected) < 1e-6, f"sign={sign} -> delta={delta} expected={expected}"


@pytest.mark.parametrize("sign", [-1, 1])
def test_variant_rendering_rotation_delta_matches_calibration(sign):
    base = _isotropic_glyph(np.random.default_rng(3))
    rotation_std = 0.25
    calib = dict(shear_std=0.0, rotation_std=rotation_std, pose_x_std=0.0, pose_y_std=0.0,
                 pose_o_std=0.0, pose_s_std=0.0)
    variant = ee.render_variant(base, "rotation", sign, calib, quantize=False)
    a0 = ee.estimate_rotation_angle(base)
    a1 = ee.estimate_rotation_angle(variant)
    delta = ee._wrap_half_pi(a1 - a0)
    expected = ee._wrap_half_pi(sign * ee.Z_QUANTILE * rotation_std)
    assert abs(delta - expected) < 1e-4, f"sign={sign} -> delta={delta} expected={expected}"


def test_variant_rendering_zero_calibration_is_near_identity():
    """A ZERO calibration dict (a starved background -- see module docstring's engagement
    note) must render every variant as (numerically) the SAME shape as the original -- an
    honest no-op, never a fabricated perturbation."""
    base = _isotropic_glyph(np.random.default_rng(4))
    zero_calib = dict(shear_std=0.0, rotation_std=0.0, pose_x_std=0.0, pose_y_std=0.0,
                       pose_o_std=0.0, pose_s_std=0.0)
    for dim, sign in ee.VARIANT_GRID:
        variant = ee.render_variant(base, dim, sign, zero_calib, quantize=False)
        for s0, s1 in zip(base, variant):
            assert np.allclose(s0, s1, atol=1e-9), f"{dim}/{sign} moved a zero-calibration glyph"


def test_pose_jitter_alternates_sign_by_stroke_index():
    """Two identical parallel strokes (same shape, no shared points) under a pose_x-only
    calibration must be shifted in OPPOSITE x directions -- `_apply_pose_jitter`'s own
    documented `i % 2` alternation, the mechanism that makes 'jitter' look like independent
    per-stroke noise rather than a second rigid whole-figure transform."""
    stroke = np.array([[0.0, 0.0], [1.0, 0.0], [1.0, 1.0]])
    strokes = [stroke.copy(), stroke.copy()]
    calib = dict(shear_std=0.0, rotation_std=0.0, pose_x_std=0.5, pose_y_std=0.0,
                 pose_o_std=0.0, pose_s_std=0.0)
    variant = ee.render_variant(strokes, "pose_jitter", 1, calib, quantize=False)
    dx0 = (variant[0] - strokes[0])[:, 0].mean()
    dx1 = (variant[1] - strokes[1])[:, 0].mean()
    assert dx0 > 0.1 and dx1 < -0.1, f"expected opposite-sign x shift, got {dx0}, {dx1}"


def test_combined_dim_applies_all_three_sub_transforms():
    base = _isotropic_glyph(np.random.default_rng(5))
    calib = dict(shear_std=0.3, rotation_std=0.2, pose_x_std=0.1, pose_y_std=0.1,
                 pose_o_std=0.1, pose_s_std=0.1)
    combined = ee.render_variant(base, "combined", 1, calib, quantize=False)
    rotation_only = ee.render_variant(base, "rotation", 1, calib, quantize=False)
    shear_only = ee.render_variant(base, "shear", 1, calib, quantize=False)
    pose_only = ee.render_variant(base, "pose_jitter", 1, calib, quantize=False)
    for other in (rotation_only, shear_only, pose_only):
        assert any(not np.allclose(a, b) for a, b in zip(combined, other)), (
            "combined must differ from every isolated sub-transform")


def test_render_variant_rejects_unknown_dim():
    with pytest.raises(ValueError):
        ee.render_variant(_isotropic_glyph(np.random.default_rng(6)), "aspect", 1, {})


# ===================================================================================================
# Gate 3 -- determinism: no RNG anywhere in calibration or variant rendering.
# ===================================================================================================
def test_variant_generation_is_deterministic():
    base = _isotropic_glyph(np.random.default_rng(7))
    calib = dict(shear_std=0.2, rotation_std=0.15, pose_x_std=0.05, pose_y_std=0.05,
                 pose_o_std=0.05, pose_s_std=0.05)
    set1 = ee.render_variant_set(base, calib, quantize=False)
    set2 = ee.render_variant_set(base, calib, quantize=False)
    for a_list, b_list in zip(set1, set2):
        for a, b in zip(a_list, b_list):
            assert np.array_equal(a, b)


def test_calibrate_background_is_deterministic(tmp_path):
    c1 = ee.calibrate_background(learn_n=1)
    c2 = ee.calibrate_background(learn_n=1)
    for key in ("shear_std", "rotation_std", "log_scale_std", "pose_x_std", "pose_y_std",
                "pose_o_std", "pose_s_std"):
        assert c1[key] == c2[key], f"{key} differs across repeated calibration runs"
    assert c1["n_classes"] == c2["n_classes"] > 0


# ===================================================================================================
# Gate 4 -- background-calibration READ/FREEZE mechanics: once a calibration.json exists,
# `calibrate_or_load` must return it VERBATIM, never silently recompute.
# ===================================================================================================
def test_calibrate_or_load_freezes_an_existing_file(tmp_path):
    path = str(tmp_path / "calibration.json")
    sentinel = dict(learn_alphabets=["__sentinel__"], n_classes=-1, n_glyphs=-1,
                     shear_std=999.0, n_shear_samples=0, rotation_std=999.0,
                     n_rotation_samples=0, log_scale_std=999.0, n_scale_samples=0,
                     pose_x_std=999.0, pose_y_std=999.0, pose_o_std=999.0, pose_s_std=999.0,
                     n_pose_samples=0)
    ee.save_calibration(sentinel, path)
    loaded = ee.calibrate_or_load(path, learn_n=1)
    assert loaded == sentinel, "calibrate_or_load must return an existing file VERBATIM"


def test_calibrate_or_load_computes_only_when_absent(tmp_path):
    path = str(tmp_path / "calibration.json")
    assert not Path(path).exists()
    calib = ee.calibrate_or_load(path, learn_n=1)
    assert Path(path).exists()
    assert calib["n_classes"] > 0
    on_disk = ee.load_calibration(path)
    assert on_disk == calib


# ===================================================================================================
# Gate 5 -- VariantStrokesFilter: synthetic keys redirect, real paths pass through, restores on
# exit (mirrors `episode_style.StyleCanonFilter`'s own precedent test).
# ===================================================================================================
def test_variant_strokes_filter_redirects_only_registered_keys(tmp_path, monkeypatch):
    import domains.omniglot_world as ow

    real_path = "not_a_real_file.txt"
    monkeypatch.setattr(ow, "load_strokes",
                         lambda p, *a, **kw: [np.array([[1.0, 2.0]])] if p == real_path else
                         (_ for _ in ()).throw(FileNotFoundError(p)))
    fake_variant = [np.array([[9.0, 9.0]])]
    key = ee.variant_key(real_path, 0)
    with ee.VariantStrokesFilter({key: fake_variant}):
        assert ow.load_strokes(key) is fake_variant
        assert np.array_equal(ow.load_strokes(real_path)[0], np.array([[1.0, 2.0]]))
    # After exit, the synthetic key is no longer intercepted -- falls through to the (fake)
    # original loader, which raises for anything that isn't `real_path`.
    with pytest.raises(FileNotFoundError):
        ow.load_strokes(key)


def test_variant_key_never_collides_with_a_real_path():
    key = ee.variant_key("/some/real/path.txt", 3)
    assert "\x00" in key
    assert key != "/some/real/path.txt"


# ===================================================================================================
# Gate 6 -- min-over-set with the original ALWAYS included: the min score is structurally
# <= the original's own score (this is the gate script's own held-Term machinery, not a Python
# min() -- import it directly and evaluate the SAME MinOver Term the run's ARM X uses).
# ===================================================================================================
def test_min_over_set_never_exceeds_original_score():
    import scripts.jabberwock_omniglot_run43_expand as run43x

    native = getattr(srs.Substrate(), "_inner", None) or srs.Substrate()
    rng = np.random.default_rng(8)
    for _ in range(20):
        orig_score = float(rng.uniform(0.0, 5.0))
        variant_scores = [float(rng.uniform(0.0, 5.0)) for _ in range(8)]
        pairs = [(orig_score, 0)] + [(s, k + 1) for k, s in enumerate(variant_scores)]
        min_score = native.evaluate(run43x._min_score_term(pairs), {})
        assert min_score <= orig_score + 1e-9
        assert abs(min_score - min(orig_score, *variant_scores)) < 1e-9


def test_argmin_pairs_term_picks_the_true_minimum():
    import scripts.jabberwock_omniglot_run43_expand as run43x

    native = getattr(srs.Substrate(), "_inner", None) or srs.Substrate()
    pairs = [(3.0, 0), (1.5, 1), (4.2, 2), (1.5, 3)]
    winner = native.evaluate(run43x._argmin_pairs_term(pairs), {})
    assert winner[0] == 1.5
    assert winner[1] in (1, 3)


def test_min_over_set_structural_property_holds_for_variant_grid_size():
    """The SAME structural guarantee, but built the way the gate script actually builds it:
    tag 0 is always the original, tags 1..K are `ee.VARIANT_GRID`'s own K variants -- confirms
    `len(pairs) == len(ee.VARIANT_GRID) + 1` is the shape ARM X's own per-candidate set uses."""
    import scripts.jabberwock_omniglot_run43_expand as run43x

    native = getattr(srs.Substrate(), "_inner", None) or srs.Substrate()
    rng = np.random.default_rng(9)
    orig = float(rng.uniform(0, 5))
    pairs = [(orig, 0)] + [(float(rng.uniform(0, 5)), k + 1)
                            for k in range(len(ee.VARIANT_GRID))]
    assert len(pairs) == len(ee.VARIANT_GRID) + 1 == 9
    min_score = native.evaluate(run43x._min_score_term(pairs), {})
    assert min_score <= orig + 1e-9


# ===================================================================================================
# Gate 7 -- source audit: `exemplar_expand.py` makes no Python argmin/argmax/score-sort
# decision (mirrors `tests.test_episode_style_migrated.test_episode_style_no_python_decisions`
# verbatim -- the min-over-set/argmin DECISION stays a held Term in the gate script, never here).
# ===================================================================================================
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count", "covered", "vote")


def test_exemplar_expand_no_python_decisions():
    src = Path(ee.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src), (
        "exemplar_expand.py must not call argmin/argmax in Python")
    assert not _MINMAX_KEY_RE.search(src), (
        "exemplar_expand.py must not use min()/max(key=...) as a scoring decision")
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


def test_exemplar_expand_never_seeds_an_rng():
    """No RNG anywhere in this module -- the launch brief's own 'deterministic grid not RNG'
    choice; a `np.random`/`default_rng` call here would silently make the variant grid
    non-reproducible."""
    src = Path(ee.__file__).read_text()
    rng_calls = re.compile(r"np\.random\.|default_rng\(|RandomState\(", re.IGNORECASE)
    assert not rng_calls.search(src), "exemplar_expand.py must not call any RNG constructor"
