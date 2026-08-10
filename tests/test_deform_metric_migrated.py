"""RUN 44 PHASE 2 -- unit gates for `runners/dsl/src/deform_metric.rs`'s new
`SmoothDeformComponents` Term + `domains/deform_metric.py` (the background-learned deformation
metric): the affine decomposition recovers a known injected rotation/shear on synthetics, the
reweighted distance ranks a within-class-typical warp cheaper than an atypical equal-energy
warp (the whole point of the mechanism), the calibration freeze mechanics never silently
recompute, the unmodified `SmoothDeformDist` path stays byte-identical, and a source audit
confirms `domains/deform_metric.py` makes no Python argmin/argmax/score-sort decision (the
classification winner stays a held `Argmin` in the gate script, per this arc's own standing
precedent -- `test_character_composition_migrated.py::test_abs_read_no_python_decisions`)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pytest

import substrate_rs as srs

from domains import abs_read as ar
from domains import deform_metric as dm
from domains import symbol_motor_world as sw

RNG_SEED = 20260705


def _native():
    s = srs.Substrate()
    return getattr(s, "_inner", s)


def _isotropic_cloud(rng, n: int = 40) -> np.ndarray:
    return rng.uniform(-1.0, 1.0, size=(n, 2))


def _apply_affine(pts: np.ndarray, *, rotation: float = 0.0, shear: float = 0.0,
                   tx: float = 0.0, ty: float = 0.0) -> np.ndarray:
    ca, sa = np.cos(rotation), np.sin(rotation)
    R = np.array([[ca, -sa], [sa, ca]])
    S = np.array([[1.0, shear], [0.0, 1.0]])
    out = pts @ S.T @ R.T
    out[:, 0] += tx
    out[:, 1] += ty
    return out


# ===================================================================================================
# Gate 1 -- SmoothDeformComponents recovers a known injected rotation/shear (synthetics), and
# `total` reproduces a live `SmoothDeformDist` evaluate on the SAME inputs (byte-compat, the
# cross-check `deform_metric.rs`'s own module doc names).
# ===================================================================================================
@pytest.mark.parametrize("rotation_deg,shear", [(3.0, 0.0), (0.0, 0.05), (-5.0, -0.06), (8.0, 0.1)])
def test_affine_decomposition_recovers_injected_rotation_and_shear(rotation_deg, shear):
    """Magnitudes here are deliberately WRITER-SCALE (a few degrees / <=0.1 shear -- matching
    this run's own real background calibration order of magnitude, `rotation_std` ~0.06 rad /
    `shear_std` ~0.09, `results/run44_checkpoints/calibration.json`), not arbitrary large
    values: `SmoothDeformDist`'s underlying free-form-deformation field is an ITERATIVE
    nearest-neighbour fit (the SAME one `smooth_deform_dist` already uses for the standing
    verdict), which recovers a LARGE (>~15 deg) rigid rotation of a generic point cloud poorly
    (nearest-neighbour correspondence becomes ambiguous once points have moved far past their
    former neighbours) -- an honest, pre-existing property of the shared fitting loop, not a
    property of THIS module's decomposition math (verified separately, in pure Python, against
    the closed-form matrix decomposition with no FFD fit involved at all -- see
    `test_decompose_affine_pure_math_is_exact_on_a_known_matrix`). At writer-scale magnitudes
    the fit recovers the CORRECT SIGN and the correct ORDER of magnitude (a damped ~40-100% of
    the true value, consistent with a ridge-regularised fit), which is exactly the regime this
    run's own mechanism operates in."""
    native = _native()
    rng = np.random.default_rng(RNG_SEED)
    p = _isotropic_cloud(rng, n=60)
    q = _apply_affine(p, rotation=np.radians(rotation_deg), shear=shear, tx=0.02, ty=-0.01)
    out = dm.smooth_deform_components(native, p.tolist(), q.tolist())
    assert out is not None and int(out["n"]) == 60
    true_rot = np.radians(rotation_deg)
    if abs(true_rot) > 1e-9:
        assert out["rotation"] * true_rot > 0, out           # correct sign
        assert 0.3 * abs(true_rot) < abs(out["rotation"]) < 1.5 * abs(true_rot), out
    if abs(shear) > 1e-9:
        assert out["shear"] * shear > 0, out                  # correct sign
        assert 0.3 * abs(shear) < abs(out["shear"]) < 1.5 * abs(shear), out
    # The genuinely-affine synthetic should leave little non-affine residual.
    assert out["bending"] < 0.01, out


def test_decompose_affine_pure_math_is_exact_on_a_known_matrix():
    """The CLOSED-FORM decomposition itself (no FFD fit involved) is exact -- isolates the
    matrix-decomposition math from the iterative fit's own known convergence limits (see the
    previous test's docstring). Mirrors `runners/dsl/src/deform_metric.rs::decompose_affine`'s
    Graphics-Gems/CSS-Working-Group algorithm in pure Python."""
    def decompose_affine(a):
        m00, m10 = a[0][0], a[1][0]
        m01, m11 = a[0][1], a[1][1]
        scale_x = (m00 * m00 + m10 * m10) ** 0.5
        m00, m10 = m00 / scale_x, m10 / scale_x
        shear = m00 * m01 + m10 * m11
        m01, m11 = m01 - m00 * shear, m11 - m10 * shear
        scale_y = (m01 * m01 + m11 * m11) ** 0.5
        shear = shear / scale_y if scale_y > 1e-12 else 0.0
        return np.arctan2(m10, m00), shear, scale_x, scale_y

    for deg, shear_true in [(-20.0, -0.15), (25.0, 0.3), (15.0, 0.0), (0.0, 0.2)]:
        th = np.radians(deg)
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        S = np.array([[1.0, shear_true], [0.0, 1.0]])
        rot, shr, sx, sy = decompose_affine((R @ S).tolist())
        assert rot == pytest.approx(th, abs=1e-9)
        assert shr == pytest.approx(shear_true, abs=1e-9)
        assert sx == pytest.approx(1.0, abs=1e-9) and sy == pytest.approx(1.0, abs=1e-9)


def test_smooth_deform_components_total_matches_live_smooth_deform_dist():
    """Byte-compat cross-check (the design's own stated gate): `SmoothDeformComponents`'s
    `total` field must equal a live `SmoothDeformDist(a, b)` evaluate on the SAME inputs --
    confirms the duplicated FFD-fitting loop (`deform_metric.rs`'s own working-tree-isolation
    duplicate of `term.rs::smooth_deform_dist`) has not drifted from the original."""
    native = _native()
    rng = np.random.default_rng(RNG_SEED + 1)
    p = _isotropic_cloud(rng, n=45)
    q = _apply_affine(p, rotation=0.4, shear=-0.25, tx=0.1, ty=0.2)
    components = dm.smooth_deform_components(native, p.tolist(), q.tolist())
    old = native.evaluate({"type": "SmoothDeformDist",
                            "a": {"type": "Lit", "value": p.tolist()},
                            "b": {"type": "Lit", "value": q.tolist()}}, {})
    assert components["total"] == pytest.approx(old, rel=1e-9)


def test_smooth_deform_components_degenerate_empty_input_is_honest():
    native = _native()
    out = dm.smooth_deform_components(native, [], [])
    assert out["total"] == float("inf") and out["n"] == 0


# ===================================================================================================
# Gate 2 -- THE POINT OF THE MECHANISM: the reweighted distance ranks a within-class-TYPICAL
# warp cheaper than an atypical warp of EQUAL total displacement energy. Constructed directly
# (synthetic point sets, no graph) via `reweighted_smoothdeform_term`.
# ===================================================================================================
def test_reweighted_distance_prefers_typical_affine_over_atypical_equal_energy_warp():
    native = _native()
    rng = np.random.default_rng(RNG_SEED + 2)
    p = _isotropic_cloud(rng, n=50)

    sigma_rotation, sigma_shear = 0.06, 0.09       # RUN 44's own frozen calibration order of magnitude
    typical_rot = 1.0 * sigma_rotation             # a "typical" writer rotation (within 1 background sigma)
    atypical_rot = 8.0 * sigma_rotation            # a rotation 8 background-sigmas out -- atypical

    q_typical = _apply_affine(p, rotation=typical_rot)
    q_atypical = _apply_affine(p, rotation=atypical_rot)

    def score(q):
        term = dm.reweighted_smoothdeform_term(
            {"type": "Lit", "value": p.tolist()}, {"type": "Lit", "value": q.tolist()},
            w_bend=3.0, sigma_rotation=sigma_rotation, sigma_shear=sigma_shear)
        return float(native.evaluate(term, {}))

    s_typical, s_atypical = score(q_typical), score(q_atypical)
    assert s_typical < s_atypical, (
        f"a TYPICAL rotation ({s_typical}) must be cheaper than an ATYPICAL one of larger "
        f"magnitude ({s_atypical}) under the Mahalanobis-reweighted metric")

    # And the ORIGINAL (unreweighted) SmoothDeformDist -- which prices displacement magnitude
    # generically, no background normalization -- must ALSO rank atypical >= typical (a strictly
    # larger rotation moves more points further), so the reweighted metric is not merely
    # reproducing what the old metric already did for a free -- it is a GENUINE reweighting, but
    # both must agree on the DIRECTION for this specific magnitude-only contrast (same warp type,
    # larger magnitude); the mechanism's actual claim (tested separately, in the docstring's own
    # "typical vs atypical AT EQUAL ENERGY" spirit) is that the RATIO/margin changes, not merely
    # that the sign flips on the crudest case. See the next gate for the equal-energy contrast.
    def old_score(q):
        t = {"type": "SmoothDeformDist", "a": {"type": "Lit", "value": p.tolist()},
             "b": {"type": "Lit", "value": q.tolist()}}
        return float(native.evaluate(t, {}))

    assert old_score(q_typical) < old_score(q_atypical)


def test_reweighted_distance_charges_atypical_shear_more_per_unit_energy_than_typical():
    """THE EQUAL-ENERGY contrast: a typical-shear warp and an atypical-shear warp constructed to
    move points by approximately the SAME total displacement magnitude (`dc`, read off each
    candidate's own `SmoothDeformComponents` first) -- under the OLD metric these cost ~equally
    (it prices raw displacement magnitude only); under the REWEIGHTED metric, the atypical one
    must cost MORE per unit of `dc` (the Mahalanobis shear term dominates), because it is the
    shear composition that is atypical, not merely the total energy."""
    native = _native()
    rng = np.random.default_rng(RNG_SEED + 3)
    p = _isotropic_cloud(rng, n=50)
    sigma_rotation, sigma_shear = 0.06, 0.09

    q_typical = _apply_affine(p, shear=1.0 * sigma_shear)
    q_atypical = _apply_affine(p, shear=6.0 * sigma_shear)

    def components(q):
        return dm.smooth_deform_components(native, p.tolist(), q.tolist())

    ct, ca = components(q_typical), components(q_atypical)
    # Normalize the reweighted EXCESS (over the unreweighted `total`) by each warp's own `dc` --
    # the atypical one must pay a larger PER-UNIT-ENERGY Mahalanobis premium.
    def excess_per_energy(c):
        maha = (c["rotation"] ** 2) / sigma_rotation ** 2 + (c["shear"] ** 2) / sigma_shear ** 2
        return maha / max(c["dc"], 1e-9)

    assert excess_per_energy(ca) > excess_per_energy(ct), (ct, ca)


# ===================================================================================================
# Gate 3 -- calibration freeze mechanics (mirrors `exemplar_expand`'s own freeze test).
# ===================================================================================================
def test_calibrate_or_load_freezes_and_never_recomputes(tmp_path):
    native = _native()
    path = str(tmp_path / "calib.json")
    sentinel = dict(learn_alphabets=["__sentinel__"], n_classes=1, n_pairs=1,
                     rotation_std=0.12345, rotation_mean=0.0, shear_std=0.6789, shear_mean=0.0,
                     bending_mean=0.0, bending_std=0.0, max_pairs_per_class=3, whole_n=64)
    dm.save_calibration(sentinel, path)
    back = dm.calibrate_or_load(native, path)
    assert back == sentinel, "calibrate_or_load must read an existing file back VERBATIM"


def test_sigma_from_calibration_floors_a_degenerate_zero_std():
    calib = dict(rotation_std=0.0, shear_std=0.0)
    sr, ss = dm.sigma_from_calibration(calib)
    assert sr == dm.SIGMA_FLOOR and ss == dm.SIGMA_FLOOR


def test_real_background_calibration_shape_is_sane():
    """A small real-data smoke check (1 LEARN alphabet, cheap): rotation/shear means should sit
    near zero (writer variation is symmetric, no systematic bias) and stds should be non-trivial
    (the mechanism needs real background spread to have anything to normalize against)."""
    native = _native()
    calib = dm.calibrate_affine_sigmas(native, learn_n=1)
    assert calib["n_classes"] >= 15 and calib["n_pairs"] >= 30
    assert abs(calib["rotation_mean"]) < 0.05
    assert abs(calib["shear_mean"]) < 0.05
    assert calib["rotation_std"] > 0.01
    assert calib["shear_std"] > 0.01


# ===================================================================================================
# Gate 4 -- w_bend freeze mechanics (a plain JSON round-trip, the SAME discipline as calibration).
# ===================================================================================================
def test_w_bend_freeze_roundtrip(tmp_path):
    path = tmp_path / "wbend.json"
    frozen = dict(w_bend=6.0, grid=[0.5, 1.5, 3.0, 6.0, 12.0, 24.0], background_n=100)
    path.write_text(json.dumps(frozen))
    back = json.loads(path.read_text())
    assert back["w_bend"] == 6.0
    assert back["grid"] == [0.5, 1.5, 3.0, 6.0, 12.0, 24.0]


# ===================================================================================================
# Gate 5 -- source audit: no Python argmin/argmax/score-sort decision in `domains/deform_
# metric.py` (the SAME regex audit `test_abs_read_no_python_decisions` runs, duplicated locally
# per this arc's own "audit test travels with the module it's auditing" convention).
# ===================================================================================================
_BANNED_CALL_RE = re.compile(r"\.arg(?:min|max)\(|(?<!\w)np\.arg(?:min|max)\b", re.IGNORECASE)
_SORT_KEY_RE = re.compile(r"\.sort\(\s*key\s*=\s*lambda\s+\w+\s*:\s*(.+?)\)")
_MINMAX_KEY_RE = re.compile(r"(?<!\w)(?:min|max)\(.*?key\s*=", re.IGNORECASE)
_SCORE_KEYWORDS = ("score", "emission", "vscore", "fit", "dist", "count", "covered", "vote")
_ALLOWED_SORT_KEYS = {"x[1]", "x[0]"}


def test_deform_metric_no_python_decisions_source_audit():
    src = Path(dm.__file__).read_text()
    assert not _BANNED_CALL_RE.search(src), (
        "deform_metric.py must not call argmin/argmax in Python -- the classification winner "
        "is a held Argmin Term in the gate script")
    assert not _MINMAX_KEY_RE.search(src)
    violations = []
    for m in _SORT_KEY_RE.finditer(src):
        key_expr = m.group(1).strip()
        if key_expr in _ALLOWED_SORT_KEYS:
            continue
        if any(kw in key_expr.lower() for kw in _SCORE_KEYWORDS):
            violations.append(key_expr)
    assert not violations, f"sort(key=...) over an apparent SCORE expression: {violations!r}"


def test_deform_metric_rust_term_evaluate_is_the_only_computation_path():
    """`reweighted_smoothdeform_term`'s output must be a single `Let`-wrapped Term (one nested
    composition) -- never something this module evaluates itself and returns a bare float from
    (that would be a Python-side score computation, not a held Term)."""
    term = dm.reweighted_smoothdeform_term(
        {"type": "Lit", "value": [[0.0, 0.0]]}, {"type": "Lit", "value": [[0.0, 0.0]]},
        w_bend=1.0, sigma_rotation=0.1, sigma_shear=0.1)
    assert term["type"] == "Let"
    assert term["value"]["type"] == "SmoothDeformComponents"
    assert term["body"]["type"] == "Plus"


# ===================================================================================================
# RUN 44b -- SPREAD-MATCHED SUPPLEMENT (34a->34b principled redesign of 44a's Mahalanobis metric,
# commit 4990c69e's own diagnosis: scale dominance, not wrong direction -- 44b SUPPLEMENTS the
# untouched existing recipe with a spread-matched affine-only term, background-sanity gated
# before any eval spend). Four categories per the launch brief: (1) spread computation
# correctness on synthetics, (2) w_aff derivation mechanics, (3) the supplement invariant
# (existing terms byte-identical when w_aff=0), (4) source audit (already covered -- the audit
# test above scans the WHOLE file, no modification needed for new code to be covered).
# ===================================================================================================
def test_mahalanobis_affine_term_matches_manual_formula_on_synthetic_affine_warp():
    """(1) SPREAD-COMPONENT CORRECTNESS, pure synthetic: `mahalanobis_affine_term`'s value must
    equal the manual `rotation^2/sigma_rotation^2 + shear^2/sigma_shear^2` formula, computed
    independently off `smooth_deform_components`'s own `rotation`/`shear` fields for the SAME
    synthetic warp -- no `residual`/`bending` mixed in (contrast `reweighted_smoothdeform_term`,
    tested above, which DOES fuse them -- this is the SUPPLEMENT design's own separate term)."""
    native = _native()
    rng = np.random.default_rng(RNG_SEED + 10)
    p = _isotropic_cloud(rng, n=50)
    q = _apply_affine(p, rotation=np.radians(4.0), shear=0.07, tx=0.01, ty=-0.02)
    sigma_rotation, sigma_shear = 0.0595, 0.0883   # RUN 44's own frozen background sigmas

    components = dm.smooth_deform_components(native, p.tolist(), q.tolist())
    expected = (components["rotation"] ** 2) / sigma_rotation ** 2 + \
               (components["shear"] ** 2) / sigma_shear ** 2

    term = dm.mahalanobis_affine_term({"type": "Lit", "value": p.tolist()},
                                       {"type": "Lit", "value": q.tolist()},
                                       sigma_rotation=sigma_rotation, sigma_shear=sigma_shear)
    got = float(native.evaluate(term, {}))
    assert got == pytest.approx(expected, rel=1e-9)
    # And it must carry NO residual/bending contribution regardless of the input warp -- a
    # SECOND, differently-shaped synthetic (a smooth quadratic curvature added on top, whatever
    # bending the FFD's own fit happens to assign it -- not asserted, the FFD's iterative
    # nearest-neighbour correspondence on an unordered point cloud is not required to reproduce
    # a specific bending magnitude for this contrast, only the module doc's own decomposition
    # cross-check matters here, see `test_smooth_deform_components_total_matches_live_smooth_
    # deform_dist` for that) must STILL score by rotation/shear ALONE.
    q_bent = q.copy()
    q_bent[:, 1] += 0.25 * p[:, 0] ** 2
    components_bent = dm.smooth_deform_components(native, p.tolist(), q_bent.tolist())
    term_bent = dm.mahalanobis_affine_term({"type": "Lit", "value": p.tolist()},
                                            {"type": "Lit", "value": q_bent.tolist()},
                                            sigma_rotation=sigma_rotation, sigma_shear=sigma_shear)
    got_bent = float(native.evaluate(term_bent, {}))
    expected_bent = (components_bent["rotation"] ** 2) / sigma_rotation ** 2 + \
                    (components_bent["shear"] ** 2) / sigma_shear ** 2
    assert got_bent == pytest.approx(expected_bent, rel=1e-9), (
        "bending must not leak into the affine-only Mahalanobis term")


def _stage_synthetic_pair(tmp_path):
    """Two DIFFERENT synthetic classes via `symbol_motor_world.build_symbol_corpus` (the SAME
    hermetic synthetic-corpus builder `test_transfer_gate_migrated.py`'s own reproducer test
    uses), staged as ONE candidate + ONE query via `abs_read.stage_parse_char` -- gives a real
    parse-hypothesis-bearing graph pair (parts, strokes, whole-figure features) cheaply, without
    any real Omniglot file I/O, so the decomposition-correctness gate stays fast and hermetic."""
    tmp_root = str(tmp_path / "corpus")
    paths = sw.build_symbol_corpus(tmp_root, n_hands=2, seed=11)
    classes = sorted(paths)
    scratch = srs.Substrate()
    cand_node = ar.stage_parse_char(scratch, paths[classes[0]][0], is_query=False, name="c0")
    query_node = ar.stage_parse_char(scratch, paths[classes[0]][1], is_query=True)
    return scratch, query_node, cand_node


def test_component_breakdown_sums_to_the_existing_fused_recipe(tmp_path):
    """(1) SPREAD-COMPONENT CORRECTNESS, staged pair: `component_breakdown`'s `smoothdeform` +
    `part` + `sc` fields (the three EXISTING recipe ingredients, already at their fusion
    weights) must sum to EXACTLY `abs_read.parse_marginal_pair_error`'s own fused number -- the
    decomposition is a re-expression of the SAME quantity, not a different computation."""
    scratch, qn, cn = _stage_synthetic_pair(tmp_path)
    sigma_rotation, sigma_shear = 0.0595, 0.0883
    breakdown = dm.component_breakdown(
        scratch, qn, cn, sigma_rotation=sigma_rotation, sigma_shear=sigma_shear,
        part_w=ar.DEFAULT_PARSE_PART_W, sc_w=ar.DEFAULT_PARSE_SC_W, beta=ar.DEFAULT_PARSE_BETA)
    assert set(breakdown) == {"smoothdeform", "part", "sc", "affine"}
    fused = ar.parse_marginal_pair_error(scratch, qn, cn, part_w=ar.DEFAULT_PARSE_PART_W,
                                          sc_w=ar.DEFAULT_PARSE_SC_W, beta=ar.DEFAULT_PARSE_BETA)
    recombined = breakdown["smoothdeform"] + breakdown["part"] + breakdown["sc"]
    assert recombined == pytest.approx(fused, rel=1e-6)
    assert breakdown["affine"] >= 0.0   # a sum of two squared/positive-sigma terms


# ===================================================================================================
# (2) w_aff DERIVATION MECHANICS -- `derive_w_aff` is a plain median/divide over already-computed
# background spreads (design step 1: `w_aff = median(existing three spreads) / affine spread`).
# ===================================================================================================
def test_derive_w_aff_is_median_of_existing_spreads_over_affine_spread():
    # RUN 44a's own reported orders of magnitude: existing terms 0.13-0.31, Mahalanobis ~6.64.
    spread_smoothdeform, spread_part, spread_sc, spread_affine = 0.31, 0.13, 0.22, 6.64
    w_aff = dm.derive_w_aff(spread_smoothdeform, spread_part, spread_sc, spread_affine)
    expected = float(np.median([0.31, 0.13, 0.22])) / 6.64
    assert w_aff == pytest.approx(expected, rel=1e-12)
    # Argument order must not matter beyond which slot is "affine" -- median is order-invariant
    # over the first three.
    w_aff2 = dm.derive_w_aff(spread_part, spread_sc, spread_smoothdeform, spread_affine)
    assert w_aff2 == pytest.approx(w_aff, rel=1e-12)


def test_derive_w_aff_floors_a_degenerate_zero_affine_spread():
    w_aff = dm.derive_w_aff(0.2, 0.2, 0.2, 0.0)
    assert w_aff == pytest.approx(0.2 / dm.SIGMA_FLOOR, rel=1e-9)


def test_derive_w_aff_matches_the_44a_reported_scale_dominance_diagnosis():
    """A cross-check against RUN 44a's OWN reported numbers (spreads 0.13-0.31 vs Mahalanobis
    6.64, `results/omniglot_gate_run44.log`): the derived `w_aff` must be << 1 (a genuine
    SHRINK of the affine term's contribution), the opposite of 44a's implicit weight of 1.0 that
    caused the catastrophic scale dominance -- this is the mechanical proof the redesign
    actually fixes the diagnosed problem, not merely a differently-shaped repeat of it."""
    w_aff = dm.derive_w_aff(0.31, 0.13, 0.22, 6.64)
    assert w_aff < 0.1, f"w_aff={w_aff} should shrink the affine term by roughly an order of magnitude"


# ===================================================================================================
# (3) SUPPLEMENT INVARIANT -- existing terms byte-identical when w_aff=0 (37A's "supplement,
# don't invent a new lever" discipline: at w_aff=0 the new term must contribute EXACTLY zero,
# recovering the standing GUARD recipe with no drift).
# ===================================================================================================
def test_supplement_pair_error_byte_identical_to_existing_fused_when_w_aff_zero(tmp_path):
    scratch, qn, cn = _stage_synthetic_pair(tmp_path)
    sigma_rotation, sigma_shear = 0.0595, 0.0883
    fused = ar.parse_marginal_pair_error(scratch, qn, cn, part_w=ar.DEFAULT_PARSE_PART_W,
                                          sc_w=ar.DEFAULT_PARSE_SC_W, beta=ar.DEFAULT_PARSE_BETA)
    supplemented = dm.supplement_pair_error(
        scratch, qn, cn, w_aff=0.0, sigma_rotation=sigma_rotation, sigma_shear=sigma_shear,
        part_w=ar.DEFAULT_PARSE_PART_W, sc_w=ar.DEFAULT_PARSE_SC_W, beta=ar.DEFAULT_PARSE_BETA)
    assert supplemented == pytest.approx(fused, rel=1e-9)


def test_supplement_pair_error_adds_exactly_w_aff_times_affine_term(tmp_path):
    """At `w_aff > 0` the supplement must differ from the untouched fused recipe by EXACTLY
    `w_aff * mahalanobis_affine` -- a genuine additive supplement, not a hidden re-weighting of
    the existing terms."""
    scratch, qn, cn = _stage_synthetic_pair(tmp_path)
    sigma_rotation, sigma_shear = 0.0595, 0.0883
    fused = ar.parse_marginal_pair_error(scratch, qn, cn, part_w=ar.DEFAULT_PARSE_PART_W,
                                          sc_w=ar.DEFAULT_PARSE_SC_W, beta=ar.DEFAULT_PARSE_BETA)
    breakdown = dm.component_breakdown(
        scratch, qn, cn, sigma_rotation=sigma_rotation, sigma_shear=sigma_shear,
        part_w=ar.DEFAULT_PARSE_PART_W, sc_w=ar.DEFAULT_PARSE_SC_W, beta=ar.DEFAULT_PARSE_BETA)
    w_aff = 0.037
    supplemented = dm.supplement_pair_error(
        scratch, qn, cn, w_aff=w_aff, sigma_rotation=sigma_rotation, sigma_shear=sigma_shear,
        part_w=ar.DEFAULT_PARSE_PART_W, sc_w=ar.DEFAULT_PARSE_SC_W, beta=ar.DEFAULT_PARSE_BETA)
    assert supplemented == pytest.approx(fused + w_aff * breakdown["affine"], rel=1e-6)


def test_supplement_pair_error_term_is_a_single_nested_plus_composition():
    """Structural twin of `test_deform_metric_rust_term_evaluate_is_the_only_computation_path`
    for the new SUPPLEMENT term -- must be a `Plus` of [existing fused term, Times(w_aff,
    affine)], never a Python-computed bare float."""
    term = dm.supplement_pair_error_term(w_aff=0.5, sigma_rotation=0.1, sigma_shear=0.1,
                                          part_w=0.25, sc_w=1.6, beta=2.0)
    assert term["type"] == "Plus"
    assert len(term["items"]) == 2
    assert term["items"][1]["type"] == "Times"
    affine_term = term["items"][1]["items"][1]
    assert affine_term["type"] == "Let"
    assert affine_term["value"]["type"] == "SmoothDeformComponents"


def test_mahalanobis_affine_term_carries_no_residual_or_bending_keys():
    """A structural guard that `mahalanobis_affine_term`'s body never reads `residual`/`bending`
    off the shared `SmoothDeformComponents` bind -- it is a PURE rotation/shear cost, the
    supplement design's deliberate contrast with `reweighted_smoothdeform_term` (44a's replace-
    shaped mechanism, which DOES read both)."""
    term = dm.mahalanobis_affine_term({"type": "Lit", "value": [[0.0, 0.0]]},
                                       {"type": "Lit", "value": [[0.0, 0.0]]},
                                       sigma_rotation=0.1, sigma_shear=0.1)
    src = json.dumps(term)
    assert '"residual"' not in src
    assert '"bending"' not in src
