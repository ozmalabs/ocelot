"""tests/test_ink_dynamics_migrated.py — RUN 33 unit gates, run BEFORE the Gate-0 falsifier
script per the ops law ("are we missing something simple and stupid like the conservation of
momentum? YES, literally" -- the Omniglot motor files' third (time) column, silently dropped by
every loader/consumer across 32 prior runs of this arc).

Covers: `domains/omniglot_world.load_strokes_t` keeps time and matches the pre-existing
`load_strokes`'s xy byte-for-byte, with honest fallback counting on a non-monotone/missing-time
stroke; `domains/ink_dynamics.velocity_minima_knots` on a synthetic speed profile with a KNOWN
dip; `domains/ink_dynamics.two_thirds_fit`/`two_thirds_residual` on a synthetic trajectory BUILT
to satisfy speed ~ curvature^(-1/3) exactly (discretization-noise tolerances documented inline);
knot-candidate union correctness; cross-drawer agreement scoring; and a REUSE smoke test of
`domains/adaptive_bins.compute_quantile_edges` (RUN 32's zero-width-guard machinery) on a
dynamics-feature value list, confirming that machinery needs no modification for a new kind of
scalar.

None of these tests touch the substrate/graph or call `teach()` (this module and
`domains/omniglot_world.py`'s loader extension are pure-numpy world-adapter/feature-extraction
code, per CLAUDE.md — no agent decisions). The seed-isolation fixture is still installed
(project convention for every migrated test file, `tests/test_adaptive_bins_migrated.py`'s own
precedent) so this file stays hermetic even if a future test in it ever boots the substrate."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from domains import ink_dynamics as idyn
from domains import omniglot_world as ow


@pytest.fixture(autouse=True)
def _isolate_seed_writes(tmp_path, monkeypatch):
    """Mirrors tests/test_adaptive_bins_migrated.py's own fixture — defensive, since nothing in
    this file calls teach()/boots the substrate, but every migrated test file in this arc
    carries this guard as standing project convention."""
    try:
        from domains.teach import teach as _real_teach
        from domains import stroke_codebook as sc
        monkeypatch.setattr(sc, "teach", lambda *a, **k: _real_teach(*a, **{**k, "seeds_dir": tmp_path}))
    except Exception:
        pass


# =============================================================================================
#  LOADER: load_strokes_t keeps time, byte-identical xy, honest fallback counting.
# =============================================================================================
def _write_motor_file(path: Path, strokes_xyt: list) -> None:
    lines = ["START"]
    for i, st in enumerate(strokes_xyt):
        for (x, y, t) in st:
            lines.append(f"{x},{y},{t}")
        if i < len(strokes_xyt) - 1:
            lines.append("BREAK")
    path.write_text("\n".join(lines) + "\n")


def test_load_strokes_t_matches_old_loader_xy_byte_identical(tmp_path):
    f = tmp_path / "clean.txt"
    strokes = [
        [(0.0, 0.0, 0.0), (1.0, 0.0, 10.0), (2.0, 1.0, 25.0), (3.0, 1.0, 44.0)],
        [(5.0, 5.0, 60.0), (6.0, 6.0, 80.0)],
    ]
    _write_motor_file(f, strokes)

    old = ow.load_strokes(str(f))
    new, fallback = ow.load_strokes_t(str(f))
    assert len(old) == len(new) == 2
    assert fallback == [False, False]
    for o, n in zip(old, new):
        assert n.shape[1] == 3
        assert np.allclose(o, n[:, :2])
    assert np.allclose(new[0][:, 2], [0.0, 10.0, 25.0, 44.0])
    assert np.allclose(new[1][:, 2], [60.0, 80.0])


def test_load_strokes_t_falls_back_on_nonmonotone_time_and_counts_it(tmp_path):
    f = tmp_path / "glitch.txt"
    # Stroke 0 has a single decreasing sample (the real ~1% clock-glitch mode this arc's own
    # 200-file audit found); stroke 1 is clean.
    strokes = [
        [(0.0, 0.0, 0.0), (1.0, 0.0, 20.0), (2.0, 0.0, 15.0), (3.0, 0.0, 40.0)],
        [(0.0, 0.0, 0.0), (1.0, 1.0, 10.0)],
    ]
    _write_motor_file(f, strokes)

    strokes_xyt, fallback = ow.load_strokes_t(str(f))
    assert fallback == [True, False]
    # xy is untouched even on fallback -- only the time column is replaced.
    assert np.allclose(strokes_xyt[0][:, :2], [[0, 0], [1, 0], [2, 0], [3, 0]])
    # the fallback time is monotone and arc-length-proportional (constant-speed assumption).
    t0 = strokes_xyt[0][:, 2]
    assert np.all(np.diff(t0) >= 0.0)
    assert np.allclose(t0, [0.0, 1.0, 2.0, 3.0])   # unit steps -> arc length == index here


def test_load_strokes_t_falls_back_on_missing_time_column(tmp_path):
    f = tmp_path / "notime.txt"
    f.write_text("START\n0.0,0.0\n1.0,0.0\n2.0,1.0\n")
    strokes_xyt, fallback = ow.load_strokes_t(str(f))
    assert fallback == [True]
    assert strokes_xyt[0].shape == (3, 3)
    assert np.all(np.diff(strokes_xyt[0][:, 2]) >= 0.0)


def test_load_points_and_load_strokes_unchanged_by_the_extension(tmp_path):
    """The additive guard from the run-33 brief: old functions stay byte-identical."""
    f = tmp_path / "clean2.txt"
    strokes = [[(0.0, 0.0, 0.0), (1.0, 2.0, 5.0), (2.0, 4.0, 9.0)]]
    _write_motor_file(f, strokes)
    pts = ow.load_points(str(f))
    assert np.allclose(pts, [[0.0, 0.0], [1.0, 2.0], [2.0, 4.0]])
    old_strokes = ow.load_strokes(str(f))
    assert len(old_strokes) == 1
    assert np.allclose(old_strokes[0], [[0.0, 0.0], [1.0, 2.0], [2.0, 4.0]])


# =============================================================================================
#  VELOCITY MINIMA on a synthetic speed profile with a KNOWN dip.
# =============================================================================================
def _straight_line_with_dip(n=61, dip_center=0.5, dip_width=6, slow_factor=8.0):
    """A straight-line pen path (constant curvature=0, so no confound with the turning-angle
    detector) sampled at UNEQUAL time steps: dt is inflated by `slow_factor` near
    `dip_center` (a fraction of path length) -- a real ballistic slowdown look-alike. Returns
    (xyt, expected_dip_arclen_position)."""
    x = np.linspace(0.0, 10.0, n)
    y = np.zeros(n)
    dt = np.ones(n - 1)
    center_i = int(dip_center * (n - 1))
    lo, hi = max(0, center_i - dip_width // 2), min(n - 1, center_i + dip_width // 2)
    dt[lo:hi] *= slow_factor
    t = np.concatenate([[0.0], np.cumsum(dt)])
    xyt = np.stack([x, y, t], axis=1)
    return xyt, dip_center


def test_velocity_minima_detects_a_known_slowdown():
    xyt, expected_pos = _straight_line_with_dip()
    knots = idyn.velocity_minima_knots(xyt, smooth_ms=3.0, rel_threshold=0.6)
    assert knots[0] == pytest.approx(0.0)
    assert knots[-1] == pytest.approx(1.0)
    interior = idyn._interior(knots)
    assert interior.size >= 1, "the manufactured slowdown must produce at least one interior knot"
    assert np.min(np.abs(interior - expected_pos)) < 0.15


def test_velocity_minima_on_uniform_speed_has_no_spurious_interior_knots():
    n = 40
    x = np.linspace(0.0, 10.0, n)
    y = np.zeros(n)
    t = np.linspace(0.0, 100.0, n)          # perfectly uniform speed.
    xyt = np.stack([x, y, t], axis=1)
    knots = idyn.velocity_minima_knots(xyt)
    assert list(knots) == [0.0, 1.0] or idyn._interior(knots).size == 0


def test_arclength_corner_knots_always_include_endpoints_and_detect_a_right_angle():
    # An L-shaped path: a sharp 90-degree corner at its midpoint.
    xy = np.array([[float(i), 0.0] for i in range(10)] + [[9.0, float(i)] for i in range(1, 10)])
    knots = idyn.arclength_corner_knots(xy, n_knots=20, rel_threshold=0.3)
    assert knots[0] == pytest.approx(0.0)
    assert knots[-1] == pytest.approx(1.0)
    interior = idyn._interior(knots)
    assert interior.size >= 1
    assert np.min(np.abs(interior - 0.5)) < 0.15


# =============================================================================================
#  TWO-THIRDS POWER LAW recovery on a synthetic trajectory BUILT to satisfy it exactly.
# =============================================================================================
def _build_two_thirds_trajectory(n=400, L=10.0, kappa0=0.6, kappa1=0.4, K=1.0):
    """Construct a plane curve by specifying curvature as a function of ARC LENGTH,
    kappa(s) = kappa0 + kappa1*cos(2*pi*s/L) (always positive for kappa1 < kappa0), integrating
    heading theta(s) = integral kappa ds, then position via cumulative cos/sin -- the standard
    Frenet-frame construction for a plane curve of prescribed curvature. Speed is then DEFINED
    exactly as v(s) = K * kappa(s)**(-1/3) (the two-thirds law, by construction), and time is
    the cumulative integral of 1/v over arc length. Returns (xyt, kappa_analytic) sampled at N
    points evenly spaced in arc length."""
    s = np.linspace(0.0, L, n)
    ds = s[1] - s[0]
    kappa = kappa0 + kappa1 * np.cos(2 * np.pi * s / L)
    theta = np.concatenate([[0.0], np.cumsum((kappa[:-1] + kappa[1:]) / 2.0 * ds)])[:n]
    dx = np.cos(theta)
    dy = np.sin(theta)
    x = np.concatenate([[0.0], np.cumsum((dx[:-1] + dx[1:]) / 2.0 * ds)])[:n]
    y = np.concatenate([[0.0], np.cumsum((dy[:-1] + dy[1:]) / 2.0 * ds)])[:n]
    v = K * kappa ** (-1.0 / 3.0)
    inv_v = 1.0 / v
    t = np.concatenate([[0.0], np.cumsum((inv_v[:-1] + inv_v[1:]) / 2.0 * ds)])[:n]
    t = t * 1000.0                          # scale into millisecond-like units.
    xyt = np.stack([x, y, t], axis=1)
    return xyt, kappa


def test_two_thirds_fit_recovers_the_known_slope_and_high_r2():
    xyt, _ = _build_two_thirds_trajectory()
    fit = idyn.two_thirds_fit(xyt, smooth_ms=5.0)
    assert fit is not None
    # Discretization/finite-difference noise tolerance, documented: a clean recovery of the
    # -1/3 exponent within a factor of ~2, with a strong (not necessarily perfect) fit.
    assert -0.55 <= fit["slope"] <= -0.12, fit
    assert fit["r2"] > 0.55, fit


def test_two_thirds_residual_recovers_near_zero_spread_on_the_synthetic_law():
    xyt, _ = _build_two_thirds_trajectory()
    res = idyn.two_thirds_residual(xyt, smooth_ms=5.0)
    assert res is not None
    resid = np.asarray(res["residual"])
    assert resid.size == res["n"]
    assert abs(resid.mean()) < 1e-9              # mean-centred by construction.
    assert resid.std() < 0.2, "a curve BUILT to satisfy the -1/3 law should show tight spread"


def test_pooled_two_thirds_fit_matches_single_stroke_fit_quality():
    xyt, _ = _build_two_thirds_trajectory()
    single = idyn.two_thirds_fit(xyt, smooth_ms=5.0)
    pooled = idyn.pooled_two_thirds_fit([xyt, xyt], smooth_ms=5.0)     # two copies -> same fit
    assert pooled is not None
    assert pooled["n_strokes"] == 2
    assert pooled["slope"] == pytest.approx(single["slope"], abs=1e-9)
    assert pooled["r2"] == pytest.approx(single["r2"], abs=1e-9)


def test_pooled_two_thirds_fit_honest_none_on_insufficient_pooled_data():
    tiny = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 1.0]])
    assert idyn.pooled_two_thirds_fit([tiny, tiny]) is None


def test_two_thirds_fit_and_residual_are_honest_none_on_insufficient_data():
    xyt = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 1.0]])   # 2 points -- no curvature possible.
    assert idyn.two_thirds_fit(xyt) is None
    assert idyn.two_thirds_residual(xyt) is None


# =============================================================================================
#  KNOT-CANDIDATE UNION.
# =============================================================================================
def test_union_knots_dedupes_within_tolerance_and_keeps_distinct_points():
    a = np.array([0.0, 0.3, 1.0])
    b = np.array([0.29, 0.5, 1.0])
    u = idyn.union_knots(a, b, tol=0.05)
    # greedy left-to-right dedupe: 0.0 kept; 0.29 kept (0.29 clear of 0.0); 0.3 MERGES into
    # 0.29 (0.01 < tol); 0.5 kept; the exact-duplicate 1.0s collapse to one -> [0, 0.29, 0.5, 1].
    assert u[0] == pytest.approx(0.0)
    assert u[-1] == pytest.approx(1.0)
    assert len(u) == 4
    assert any(abs(v - 0.5) < 1e-9 for v in u)
    assert any(abs(v - 0.29) < 1e-9 for v in u)
    assert not any(abs(v - 0.3) < 1e-9 for v in u)     # 0.3 was absorbed into 0.29


def test_union_knots_keeps_all_when_tolerance_is_tight():
    a = np.array([0.0, 0.3, 1.0])
    b = np.array([0.29, 0.5, 1.0])
    u = idyn.union_knots(a, b, tol=0.001)
    assert len(u) == 5          # 0.0, 0.29, 0.3, 0.5, 1.0 -- only the exact-duplicate 1.0s merge


# =============================================================================================
#  CROSS-DRAWER AGREEMENT SCORING.
# =============================================================================================
def test_pairwise_agreement_perfect_match_scores_one():
    a = np.array([0.0, 0.3, 0.7, 1.0])
    b = np.array([0.0, 0.31, 0.69, 1.0])
    assert idyn.pairwise_agreement(a, b, tol=0.05) == pytest.approx(1.0)


def test_pairwise_agreement_no_match_scores_zero():
    a = np.array([0.0, 0.2, 1.0])
    b = np.array([0.0, 0.8, 1.0])
    assert idyn.pairwise_agreement(a, b, tol=0.05) == pytest.approx(0.0)


def test_pairwise_agreement_asymmetric_counts_scores_between_zero_and_one():
    a = np.array([0.0, 0.2, 0.4, 0.6, 1.0])   # 3 interior knots
    b = np.array([0.0, 0.21, 1.0])            # 1 interior knot, matches one of a's
    score = idyn.pairwise_agreement(a, b, tol=0.03)
    assert 0.0 < score < 1.0


def test_pairwise_agreement_both_empty_interior_is_none():
    a = np.array([0.0, 1.0])
    b = np.array([0.0, 1.0])
    assert idyn.pairwise_agreement(a, b) is None


def test_count_matched_null_agreement_rises_with_density_the_confound_it_corrects_for():
    """The exact regression this correction exists to catch: raw agreement rises with candidate
    COUNT alone, independent of alignment -- so the null baseline for a denser set must be
    higher than for a sparser one, at FIXED random (unaligned) positions."""
    rng = np.random.default_rng(1)
    sparse_sets = [np.concatenate([[0.0], np.sort(rng.uniform(0, 1, 3)), [1.0]]) for _ in range(15)]
    dense_sets = [np.concatenate([[0.0], np.sort(rng.uniform(0, 1, 12)), [1.0]]) for _ in range(15)]
    null_sparse = idyn.count_matched_null_agreement(sparse_sets, n_reps=40, rng=np.random.default_rng(2))
    null_dense = idyn.count_matched_null_agreement(dense_sets, n_reps=40, rng=np.random.default_rng(3))
    assert null_sparse is not None and null_dense is not None
    assert null_dense > null_sparse, "denser candidate sets must show a HIGHER chance floor"


def test_count_matched_null_agreement_detects_genuine_alignment_above_chance():
    """A knot set that is GENUINELY aligned (small jitter around one true position, on top of
    the shared 0/1 endpoints) must score its RAW agreement well above its own count-matched
    null -- the correction must not erase a real signal, only a density artifact."""
    rng = np.random.default_rng(4)
    true_pos = 0.4
    aligned_sets = [np.array([0.0, true_pos + rng.normal(0, 0.01), 1.0]) for _ in range(15)]
    raw = idyn.mean_pairwise_agreement(aligned_sets, tol=0.08)["mean"]
    null = idyn.count_matched_null_agreement(aligned_sets, n_reps=60, rng=np.random.default_rng(5))
    assert raw is not None and null is not None
    assert raw > null + 0.2


def test_count_matched_null_agreement_none_when_all_counts_zero():
    sets = [np.array([0.0, 1.0]) for _ in range(5)]
    assert idyn.count_matched_null_agreement(sets) is None


def test_mean_pairwise_agreement_over_several_drawers():
    sets = [np.array([0.0, 0.5, 1.0]), np.array([0.0, 0.52, 1.0]), np.array([0.0, 0.9, 1.0])]
    rep = idyn.mean_pairwise_agreement(sets, tol=0.05)
    assert rep["n_pairs"] == 3
    assert rep["mean"] is not None
    assert 0.0 <= rep["mean"] <= 1.0


# =============================================================================================
#  ADAPTIVE-EDGE REUSE (RUN 32's zero-width-guard machinery) ON A DYNAMICS DIMENSION -- a smoke
#  test that the EXISTING machinery needs no modification for a new kind of scalar, per the
#  run-33 brief's "REUSE domains/adaptive_bins.py".
# =============================================================================================
def test_adaptive_bins_reuse_on_dynamics_values_spreads_normally():
    from domains import adaptive_bins as ab
    rng = np.random.default_rng(0)
    values = rng.normal(0.0, 1.0, size=500).tolist()   # e.g. two-thirds residuals, duration shares
    edges = ab.compute_quantile_edges(values, n_bins=8, domain=(-5.0, 5.0))
    assert len(edges) == 9
    assert all(edges[i] < edges[i + 1] for i in range(len(edges) - 1))


def test_adaptive_bins_reuse_zero_width_guard_on_point_mass_dynamics_values():
    from domains import adaptive_bins as ab
    values = [0.5] * 500          # a degenerate point-mass dynamics feature (e.g. every
                                    # duration share identical under equal-arc-length data).
    edges = ab.compute_quantile_edges(values, n_bins=8, domain=(0.0, 1.0))
    # degenerate input falls back to UNIFORM edges over the domain (documented behaviour) --
    # still strictly increasing, never a crash or a zero-width bin.
    assert len(edges) == 9
    assert all(edges[i] < edges[i + 1] for i in range(len(edges) - 1))
