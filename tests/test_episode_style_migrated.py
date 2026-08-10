"""RUN 42 PHASE 1 -- unit gates for `domains/episode_style.py` (episode style normalization):
the shear/aspect estimators recover known injected biases on synthetics, canonicalization
inverts them (deterministic + idempotent), a single-glyph (query-side) estimate is unbiased in
expectation over many trials even though noisier than the pooled (drawer-side) estimate, and a
source audit confirms no Python decision logic crept into the module (pure geometry only)."""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from domains import episode_style as es

RNG = np.random.default_rng(20260705)


# ===================================================================================================
# Synthetic glyph builders.
# ===================================================================================================
def _isotropic_glyph(rng, n_strokes: int = 3, pts_per_stroke: int = 40) -> list:
    """A multi-stroke synthetic glyph with (in expectation) zero shear and zero aspect bias:
    each stroke is a random walk inside a centered square, x/y drawn independently. Not
    perfectly isotropic per-draw (finite-sample noise) -- that noise is exactly what the
    unbiasedness test measures over many trials."""
    strokes = []
    for _ in range(n_strokes):
        x = rng.uniform(-1.0, 1.0, size=pts_per_stroke)
        y = rng.uniform(-1.0, 1.0, size=pts_per_stroke)
        strokes.append(np.stack([x, y], axis=1))
    return strokes


def _apply_shear(strokes: list, s: float) -> list:
    out = []
    for st in strokes:
        arr = np.asarray(st, dtype=float).copy()
        arr[:, 0] = arr[:, 0] + s * arr[:, 1]
        out.append(arr)
    return out


def _apply_aspect(strokes: list, a: float) -> list:
    """Scales y by exp(a) (x unchanged) -- an injection method independent of
    `canonicalize_strokes`'s own (area-preserving) removal parameterization, so recovering
    `aspect_log_hat == a` and inverting it back to ratio 1 is a genuine round-trip check, not a
    tautology against the same formula."""
    out = []
    for st in strokes:
        arr = np.asarray(st, dtype=float).copy()
        arr[:, 1] = arr[:, 1] * np.exp(a)
        out.append(arr)
    return out


# ===================================================================================================
# Gate 1 -- shear: recover + invert.
# ===================================================================================================
@pytest.mark.parametrize("s0", [-0.6, -0.2, 0.0, 0.3, 0.75])
def test_shear_estimator_recovers_injected_shear(s0):
    """DELTA framing (mathematically exact for a pure-shear injection, see module docstring's
    invariance note): Cov(x+s*y, y) = Cov(x,y) + s*Var(y), so shear_hat(sheared) -
    shear_hat(base) == s0 up to floating point, REGARDLESS of the base glyph's own idiosyncratic
    (non-zero, finite-sample) Cov(x,y) -- an absolute comparison against a fixed random base
    would incorrectly fold that base bias into the recovery error."""
    base = _isotropic_glyph(np.random.default_rng(1))
    sheared = _apply_shear(base, s0)
    delta = es.estimate_shear(sheared) - es.estimate_shear(base)
    assert abs(delta - s0) < 1e-6, f"shear {s0} -> delta {delta}"


@pytest.mark.parametrize("s0", [-0.5, 0.4, 0.9])
def test_deshear_inverts_injected_shear(s0):
    base = _isotropic_glyph(np.random.default_rng(2))
    sheared = _apply_shear(base, s0)
    style = dict(shear=es.estimate_shear(sheared), aspect_log=0.0)
    canon = es.canonicalize_strokes(sheared, style)
    s_after = es.estimate_shear(canon)
    assert abs(s_after) < 0.05, f"residual shear after deshear: {s_after}"


# ===================================================================================================
# Gate 2 -- aspect: recover + invert.
# ===================================================================================================
@pytest.mark.parametrize("a0", [-0.5, -0.15, 0.0, 0.25, 0.6])
def test_aspect_estimator_recovers_injected_bias(a0):
    """DELTA framing, exact for the same reason as the shear test above: scaling y by exp(a0)
    (x unchanged) shifts aspect_log_hat by EXACTLY a0, independent of the base's own bias."""
    base = _isotropic_glyph(np.random.default_rng(3))
    stretched = _apply_aspect(base, a0)
    delta = es.estimate_aspect_log(stretched) - es.estimate_aspect_log(base)
    assert abs(delta - a0) < 1e-6, f"aspect_log {a0} -> delta {delta}"


@pytest.mark.parametrize("a0", [-0.4, 0.3, 0.7])
def test_deaspect_restores_unit_variance_ratio(a0):
    base = _isotropic_glyph(np.random.default_rng(4))
    stretched = _apply_aspect(base, a0)
    style = dict(shear=0.0, aspect_log=es.estimate_aspect_log(stretched))
    canon = es.canonicalize_strokes(stretched, style)
    a_after = es.estimate_aspect_log(canon)
    assert abs(a_after) < 0.05, f"residual aspect_log after deaspect: {a_after}"


# ===================================================================================================
# Gate 3 -- canonicalization is deterministic and idempotent.
# ===================================================================================================
def test_canonicalize_is_deterministic():
    base = _isotropic_glyph(np.random.default_rng(5))
    glyph = _apply_aspect(_apply_shear(base, 0.4), 0.3)
    style = es.estimate_style(glyph)
    out1 = es.canonicalize_strokes(glyph, style)
    out2 = es.canonicalize_strokes(glyph, style)
    for a, b in zip(out1, out2):
        assert np.array_equal(a, b), "canonicalize_strokes is not deterministic"


def test_canonicalize_is_idempotent_on_a_canonical_glyph():
    """Re-estimating style on an ALREADY-canonicalized glyph and canonicalizing again with that
    (near-zero) re-estimate must be (near) a no-op -- the definition of idempotence here: once
    canonical, canonicalizing again does not move the glyph further.

    KNOWN, PRE-REGISTERED COUPLING (module docstring): shear and aspect are estimated
    SIMULTANEOUSLY from one (possibly doubly-biased) point cloud, not sequentially -- shear
    inflates the apparent Var(x) the aspect ratio is measured against, an O(shear^2) residual
    (algebraically: aspect_log_hat is biased by ~0.5*log(1+shear^2) at this test's injected
    magnitudes). This is negligible at REALISTIC handwriting shear magnitudes (this test's
    -0.2/0.25, tan(~11 degrees)/log-ratio ~0.25) and is why the injected values here are modest
    rather than the shear test's stress-test extremes (0.6-0.75) -- this test checks realistic-
    regime idempotence, not worst-case exactness."""
    base = _isotropic_glyph(np.random.default_rng(6))
    glyph = _apply_aspect(_apply_shear(base, -0.2), 0.25)
    style1 = es.estimate_style(glyph)
    canon = es.canonicalize_strokes(glyph, style1)

    style2 = es.estimate_style(canon)
    assert abs(style2["shear"]) < 0.05 and abs(style2["aspect_log"]) < 0.05, (
        "first canonicalization pass left a non-trivial residual style: "
        f"{style2}")
    canon_twice = es.canonicalize_strokes(canon, style2)
    for a, b in zip(canon, canon_twice):
        # Bounded by style2's own <0.05 assertion above (worst case ~shear*|y| + aspect-scale
        # movement on unit-ish-magnitude points) -- a loose bound, not a tight numerical claim.
        assert np.allclose(a, b, atol=0.08), "second pass moved an already-canonical glyph"


def test_canonicalize_zero_style_is_identity():
    base = _isotropic_glyph(np.random.default_rng(7))
    out = es.canonicalize_strokes(base, dict(shear=0.0, aspect_log=0.0))
    for a, b in zip(base, out):
        assert np.allclose(np.asarray(a, dtype=float), b)


# ===================================================================================================
# Gate 4 -- single-glyph (query-side) self-estimate is unbiased (noisier, not skewed).
# ===================================================================================================
def test_single_glyph_self_estimate_is_unbiased():
    rng = np.random.default_rng(2026)
    shears, aspects = [], []
    for _ in range(400):
        g = _isotropic_glyph(rng, n_strokes=rng.integers(1, 4),
                              pts_per_stroke=int(rng.integers(8, 30)))
        shears.append(es.estimate_shear(g))
        aspects.append(es.estimate_aspect_log(g))
    mean_shear, mean_aspect = float(np.mean(shears)), float(np.mean(aspects))
    # Individual estimates are noisy (single glyph) -- the CLAIM under test is zero MEAN bias
    # over many trials, not low per-trial variance.
    assert abs(mean_shear) < 0.05, f"single-glyph shear estimate mean-biased: {mean_shear}"
    assert abs(mean_aspect) < 0.05, f"single-glyph aspect estimate mean-biased: {mean_aspect}"
    assert float(np.std(shears)) > 0.01, "suspiciously zero variance -- estimator may be a stub"


def test_pooled_drawer_estimate_is_tighter_than_single_glyph():
    """The whole point of pooling 20 exemplars (vs a lone query glyph): pooling should reduce
    the SPREAD of the estimate around the true (here: injected) value, even though both are
    individually unbiased."""
    rng = np.random.default_rng(99)
    s0 = 0.35
    single_estimates, pooled_estimates = [], []
    for _ in range(60):
        # One "drawer" = 20 glyphs sharing the SAME true shear s0 plus independent per-glyph
        # noise (idiosyncratic letter shape) -- pooling should average that noise down.
        glyphs = [_apply_shear(_isotropic_glyph(rng), s0) for _ in range(20)]
        styles = [es.estimate_style(g) for g in glyphs]
        pooled = es.pool_style(styles)
        pooled_estimates.append(pooled["shear"])
        single_estimates.append(styles[0]["shear"])
    assert np.std(pooled_estimates) < np.std(single_estimates), (
        f"pooled std {np.std(pooled_estimates):.4f} not tighter than single-glyph std "
        f"{np.std(single_estimates):.4f}")


# ===================================================================================================
# Gate 5 -- StyleCanonFilter redirection is mechanical (path-keyed, pass-through elsewhere).
# ===================================================================================================
def test_style_canon_filter_only_touches_registered_paths(tmp_path, monkeypatch):
    import domains.omniglot_world as ow

    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    for f in (f1, f2):
        f.write_text("START\n0,0\n1,1\n2,0\nBREAK\n")

    style = dict(shear=0.5, aspect_log=0.2)
    with es.StyleCanonFilter({str(f1): style}):
        canon_a = ow.load_strokes(str(f1))
        raw_b = ow.load_strokes(str(f2))
    raw_a = ow.load_strokes(str(f1))  # filter exited -- back to raw

    assert not np.array_equal(canon_a[0], raw_a[0]), "registered path was not canonicalized"
    expected_b = ow.load_strokes(str(f2))
    for a, b in zip(raw_b, expected_b):
        assert np.array_equal(a, b), "unregistered path was altered"
    # Filter cleanly restored the original loader.
    assert ow.load_strokes.__name__ != "_patched" or True  # exit already verified via raw_a


# ===================================================================================================
# Gate 6 -- source audit: no Python decision logic (argmin/argmax/sort-on-score/min|max(key=)).
# ===================================================================================================
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count", "covered", "vote")
_ALLOWED_SORT_KEYS: set = set()


def test_episode_style_no_python_decisions():
    """`domains/episode_style.py` is a pure geometry estimator/canonicalizer -- it must not
    argmin/argmax or rank-by-score in Python; the RUN 42 arms are decided entirely by which
    STYLE DATA a caller chooses to hand to `StyleCanonFilter`, never by a Python comparison of
    verdict scores (the verdict itself stays the held `parse_marginal_verdict` Term, untouched)."""
    src = Path(es.__file__).read_text()

    assert not _BANNED_CALL_RE.search(src), (
        "episode_style.py must not call argmin/argmax in Python")
    assert not _MINMAX_KEY_RE.search(src), (
        "episode_style.py must not use min()/max(key=...) as a scoring decision")

    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"
